"""The metadata an RFEM comment carries: `@position`, `@model`, `@be` and the rest, read into values the rest of the import can use.

An RFEM object -- a node, a member, a surface, a load -- carries a free `comment`, and that comment is where the engineer writes what RFEM itself has no field for: which Woodcore position a member realises, which structure a group of elements is, the influence width a load stands for. This module reads those lines and nothing else: it opens no model, knows no API, imports nothing of the pipeline but `engine`, and is the one place the convention is written down (docs/open-questions.md §14's `metadata_parser.py`).

**One sigil, `@`, and the key says what it is.** `@position` and `@load` *refer* to something that already exists -- a position of `Positionen.xlsx`, a load instance of `calculations.json`; `@model`, `@label`, `@descr`, `@be` and `@note` *state* something named or described here and nowhere else. Which of the two a key is, is declared once in `KEYS` and read by `validation.py`, so the sigil never has to carry it. The engineer chose one sigil over two knowing that the distinction is real: it is `KEYS` that records it, not the character typed.

⚠️ **`#` is unusable in an RFEM comment, and that is measured rather than assumed.** RFEM 6.15 reserves `#` for its own object tagging: it strips `#key` out of the comment, moves it to the end, **eats the newline that followed it and leaves the value orphaned on the line before**. Sent `@a 1 / &b 2 / $c 3 / >d 4 / !e 5 / +f 6 / :g 7 / ~h 8 / #i 9` on nine lines, RFEM stored all nine verbatim except the last, which came back as `~h 8 9 #i`. Every sigil survives; `#` does not. A first version of this convention used `#` for properties, and a comment written that way is destroyed before anything here ever sees it -- which is why a leftover `#key` is reported by name (`rfem_meta_hash`) rather than quietly ignored: it is the fingerprint of a metadata line RFEM ate.

**One entry per line.** Everything after the key is its value, so an unquoted value may carry spaces -- `@label Velo Unterstand` is one name -- and nothing has to be quoted that does not want to be. An optional `:` or `=` after the key is accepted, and several spaces anywhere, because a comment is typed by hand into a window with no completion. Newlines survive RFEM and survive the CSV export inside a quoted field, both verified on the engineer's own model.

**A line that does not open with a sigil is ordinary prose, and is kept.** It comes back as `Metadata.text`, since the comments an engineer has already written -- «Eigenschaften manuel geändert», on four of this project's sections and five of its materials -- must survive an import that reads the very same field.

**Nothing here refuses.** A key nobody knows, a sigil other than `@`, a length that is not a number: each is an `engine.Note` in `problems`, the value kept wherever it can be, and the import goes on. A typo has to be *reported* rather than stop the export of sixty members -- the exception the plans and the connectors already take (docs/architecture/data-contracts.md §3.6), applied to a seventh editor.

**What this module does not decide.** Whether `@position` sits on an object that may carry one -- only a member or a surface may (the engineer's rule: «une position ne peut être attribuée qu'à un élément barre ou panneau») -- whether the position it names exists, and whether a width of 1500 m is plausible: those need the model around the comment, and they belong to `validation.py`. The line is the usual one: syntax here, meaning there.
"""

import re

import engine

# The one sigil a metadata line opens with. Single, by the engineer's decision: the key itself says whether it refers or states, and after what RFEM does to `#` (above) a second sigil is one more thing that can go wrong in a comment typed by hand.
SIGIL = "@"

# The sigil RFEM takes for itself. Never valid here, and worth naming in a message when its remains turn up.
RFEM_TAG_SIGIL = "#"

# The metres in one of each unit a length may be written in (the engineer's request: mm, cm, m at least). A length is normalised to **metres**, which is what a static model's own influence width is given in (docs/domain/static-models.md §3.3octies), so that nothing downstream converts a second time.
LENGTH_UNITS = {"mm": 0.001, "cm": 0.01, "m": 1.0}

# A value written with no unit at all is read as metres. `@be 1.5` and `@be 1.5m` are therefore the same width, which is the reading an engineer expects of a structural drawing in metres -- and the reason `@be 1500` is a width of 1500 m rather than an error is that catching it needs a notion of what is plausible, which is validation's and not the parser's.
DEFAULT_LENGTH_UNIT = "m"

# Every key the convention knows, and what its value is: `text` is kept as written, `length` is read as a number and converted to metres. Exported so that a message can list the valid keys rather than say «unknown key» and stop there.
KEYS = {
    "position": "text",   # the Positionen.xlsx position a member or a surface realises
    "load": "text",       # the Woodcore load instance a load case's value came from, «snow-load/SL-Dach1»
    "model": "text",      # the id of the structure this object's group is
    "label": "text",      # that structure's name
    "descr": "text",      # that structure's description
    "be": "length",       # an influence width, in metres once read
    "note": "text",       # free text about this object
}

# The keys that name something which must already exist elsewhere. `validation.py` resolves these and reports what it cannot find; the parser only records which they are, since one sigil no longer distinguishes them.
REFERENCES = frozenset({"position", "load"})

# The keys that may be written on an object whose kind the engineer restricted. Only a member or a surface realises a position -- a node, a support or a load never does -- and `validation.py` enforces it, knowing the object's kind, which this module does not.
MEMBER_OR_SURFACE_ONLY = frozenset({"position"})

# `@key value`, `@key: value`, `@ key = value` -- the sigil, the key, an optional colon or equals, and the rest of the line as the value. A sigil other than `@` is matched too, so that a line written with one is read and reported rather than silently taken for prose; the key is matched loosely so a typo reaches the unknown-key warning by its own name.
_ENTRY = re.compile(r"^\s*([@&$>!+:~])\s*([A-Za-z_][A-Za-z0-9_\-]*)\s*[:=]?\s*(.*)$")

# What RFEM leaves behind when it has eaten a `#` line: the tag, moved to the end of the comment.
_RFEM_TAG = re.compile(r"(?<![A-Za-z0-9_])#([A-Za-z_][A-Za-z0-9_\-]*)")

# A number and an optional unit: `1.5m`, `1500 mm`, `1,5m`. A comma is accepted as the decimal separator because the keyboard this is typed on is Swiss and the report's own numbers are written with a point (docs/typst/language.md §4bis) -- accepting both here costs one character and saves a value silently read as text.
_LENGTH = re.compile(r"^([+-]?\d+(?:[.,]\d+)?)\s*([A-Za-z]*)$")

_QUOTES = ('"', '“', "'", "«")
_CLOSING = {'"': '"', '“': '”', "'": "'", "«": "»"}


class Metadata:
    """What one comment held: `values` by key, the ordinary prose as `text`, and every `problems` entry an `engine.Note`.

    It reads as a mapping -- `md["be"]`, `"be" in md`, `md.get("model")` -- so a caller that only wants the values never mentions `.values`, and it unpacks as `values, text, problems` for a caller that wants all three. `bool(md)` is true when the comment held any metadata at all, whatever its problems.
    """

    __slots__ = ("values", "text", "problems")

    def __init__(self, values=None, text="", problems=None):
        self.values = dict(values or {})
        self.text = text
        self.problems = list(problems or [])

    def __getitem__(self, key):
        return self.values[key]

    def __contains__(self, key):
        return key in self.values

    def __iter__(self):
        return iter((self.values, self.text, self.problems))

    def __len__(self):
        return len(self.values)

    def get(self, key, default=None):
        return self.values.get(key, default)

    def __bool__(self):
        return bool(self.values)

    def __eq__(self, other):
        if isinstance(other, Metadata):
            return (self.values, self.text, [str(p) for p in self.problems]) == (other.values, other.text, [str(p) for p in other.problems])
        return self.values == other if isinstance(other, dict) else NotImplemented

    def __repr__(self):
        parts = [f"values={self.values!r}"]
        if self.text:
            parts.append(f"text={self.text!r}")
        if self.problems:
            parts.append(f"problems={[str(p) for p in self.problems]!r}")
        return f"Metadata({', '.join(parts)})"


def _unquote(raw):
    """The text inside a pair of quotes, or None where the quotes do not close. Returns `(text, quoted)`; an unquoted value comes back as it was written."""
    if len(raw) >= 2 and raw[0] in _QUOTES:
        closing = _CLOSING[raw[0]]
        if raw.endswith(closing):
            return raw[1:-1], True
        return None, True
    return raw, False


def _length(raw, where, key, problems):
    """A length in metres, or None with a `Note` naming what could not be read."""
    match = _LENGTH.match(raw)
    if not match:
        problems.append(engine.Note(
            "rfem_meta_number",
            f"{where}: {SIGIL}{key} is not a length -- «{raw}»; write a number and a unit, as «1.5m», «150cm» or «1500mm»",
            where=where, key=key, value=raw,
        ))
        return None
    number, unit = match.group(1).replace(",", "."), match.group(2) or DEFAULT_LENGTH_UNIT
    if unit not in LENGTH_UNITS:
        problems.append(engine.Note(
            "rfem_meta_unit",
            f"{where}: {SIGIL}{key} is given in «{unit}», which is not a length unit -- write {', '.join(sorted(LENGTH_UNITS))}",
            where=where, key=key, unit=unit, units=", ".join(sorted(LENGTH_UNITS)),
        ))
        return None
    return float(number) * LENGTH_UNITS[unit]


def _report_rfem_tags(comment, where, problems):
    """Names every `#tag` left in the comment: RFEM moved it there out of a line it destroyed, so the metadata that line carried is gone and cannot be recovered here."""
    for name in dict.fromkeys(_RFEM_TAG.findall(comment)):
        known = " -- that line's value is lost" if name in KEYS else ""
        problems.append(engine.Note(
            "rfem_meta_hash",
            f"{where}: RFEM reserves «{RFEM_TAG_SIGIL}» for its own tags and moved «{RFEM_TAG_SIGIL}{name}» to the end of this comment{known}; write «{SIGIL}{name}» in RFEM instead",
            where=where, key=name, sigil=RFEM_TAG_SIGIL, wanted=SIGIL,
        ))


def parse_metadata(comment, where=""):
    """The metadata one RFEM comment holds, as a `Metadata`.

    `comment` is the object's `comment` field as RFEM gives it -- `None` and `""` are a comment with nothing in it, which every object has until the engineer writes one. `where` names the object in the problems it produces («Member 24», «Node 15»), so that a message says which comment to go and fix; it is the caller's to give, this module knowing nothing of the model.

    Every line is read on its own: one opening with `@` is an entry, any other is prose. A key the convention does not know, and a line opened with another sigil, are kept -- the intent being plain -- and reported.
    """
    problems = []
    if not comment:
        return Metadata(problems=problems)

    comment = str(comment)
    _report_rfem_tags(comment, where, problems)

    values, prose = {}, []
    for raw_line in comment.splitlines():
        match = _ENTRY.match(raw_line)
        if not match:
            if raw_line.strip():
                prose.append(raw_line.strip())
            continue

        sigil, key, raw_value = match.group(1), match.group(2).lower(), match.group(3).strip()

        if key not in KEYS:
            problems.append(engine.Note(
                "rfem_meta_unknown_key",
                f"{where}: «{sigil}{key}» is not a metadata key -- the keys are {', '.join(sorted(KEYS))}",
                where=where, key=key, sigil=sigil, keys=", ".join(sorted(KEYS)),
            ))
        elif sigil != SIGIL:
            problems.append(engine.Note(
                "rfem_meta_sigil",
                f"{where}: metadata is written with «{SIGIL}» -- read «{sigil}{key}» as «{SIGIL}{key}»",
                where=where, key=key, sigil=sigil, wanted=SIGIL,
            ))

        if key in values:
            problems.append(engine.Note(
                "rfem_meta_duplicate",
                f"{where}: «{key}» is given more than once -- the first value is kept",
                where=where, key=key,
            ))
            continue

        text, quoted = _unquote(raw_value)
        if text is None:
            problems.append(engine.Note(
                "rfem_meta_quote",
                f"{where}: the quotes around «{key}»'s value do not close -- {raw_value}",
                where=where, key=key, value=raw_value,
            ))
            continue

        if not text and not quoted:
            problems.append(engine.Note(
                "rfem_meta_empty",
                f"{where}: «{sigil}{key}» has no value",
                where=where, key=key, sigil=sigil,
            ))
            continue

        if KEYS.get(key) == "length":
            value = _length(text, where, key, problems)
            if value is None:
                continue
        else:
            value = text

        values[key] = value

    return Metadata(values, "\n".join(prose), problems)
