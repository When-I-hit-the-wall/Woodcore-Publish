"""Writing a member's checks in keyword lines, and turning them into Typst (docs/domain/member-checks.md §3.3septdecies, v0.100).

The engineer asked for «un onglet où le user peut écrire des formules de manières simples, non formatées en typst», and his own example reads:

    Position: S001
    Fais la vérification à: la compression
    Fais la vérification à la stabilité: compression
    Fais la vérification à la flexion avec compression

He was offered an AI for it and refused («n'implémente pas l'IA»), and agreed that **a deterministic parser suffices** — so this is a grammar of a dozen words and not a model. What that buys, and it is the whole argument for it: the same lines always give the same Typst, a line outside the grammar is **refused naming the line and listing what is understood**, there is no network, no key, no cost, and it cannot invent a command that does not exist. What it gives up is tolerance: «vérifie le flambement de S001» written a new way each day is a refusal until the grammar learns the word.

**The shape is `mot-clé: valeur`, one per line.** A blank line and a `#` comment are skipped; a `position:` line opens a block and everything after it belongs to that member until the next one. Every keyword has its French, German and English word, as an RFEM comment's `@key` does (section 3.3duodecies), and a word is matched without its accents and its case so that «humidite» and «Humidité» are one word.

⚠️ **It emits Typst and never runs anything.** What it writes is `#member` and the `verify-*` commands of section 3.3undecies, with the arguments each of them takes and no other: the grammar knows that `verify-shear` takes no `l-k-y`, so a length written in a block that only shears is carried to the checks that use it and quietly not to the ones that do not. The engineer reads the Typst, and sees the page it compiles to, before any of it reaches a section of his report.
"""

import re
import unicodedata

# --- the words -----------------------------------------------------------------------

def fold(word):
    """A keyword without its accents, its case or its surrounding space: «Humidité» and «humidite» are one word."""
    stripped = unicodedata.normalize("NFKD", str(word).strip().lower())
    return "".join(ch for ch in stripped if not unicodedata.combining(ch))


# What opens a block, and what a block may then state. Each canonical key with the words that reach it, in French, German and English -- and the older spellings of the engineer's own example, so that what he wrote by hand keeps working.
KEYWORDS = {
    "position": ("position", "element", "member", "bauteil", "poste"),
    "grade": ("classe", "classe de resistance", "festigkeitsklasse", "grade", "strength class"),
    "moisture": ("humidite", "classe d'humidite", "feuchteklasse", "moisture", "moisture class"),
    "b": ("b", "largeur", "breite", "width"),
    "h": ("h", "hauteur", "hohe", "height"),
    "d": ("d", "diametre", "durchmesser", "diameter"),
    "N": ("n", "effort normal", "normalkraft", "normal force"),
    "V": ("v", "effort tranchant", "querkraft", "shear force"),
    "V_y": ("v_y", "vy"),
    "M_y": ("m_y", "my", "moment", "moment y", "biegemoment"),
    "M_z": ("m_z", "mz", "moment z"),
    "T": ("t", "torsion", "moment de torsion", "torsionsmoment"),
    "F": ("f", "force", "charge concentree", "einzellast", "concentrated load"),
    "tau": ("tau", "contrainte de cisaillement", "schubspannung"),
    "sigma_90": ("sigma_90", "contrainte transversale", "querspannung"),
    "l": ("l", "longueur", "lange", "length"),
    "w": ("w", "largeur d'appui", "auflagerbreite", "bearing width"),
    "l_k": ("l_k", "lk", "longueur de flambement", "knicklange", "buckling length"),
    "l_k_y": ("l_k_y", "lky"),
    "l_k_z": ("l_k_z", "lkz"),
    "a": ("a", "distance des appuis lateraux", "kipplange", "lateral support distance"),
    "alpha": ("alpha", "angle", "winkel"),
    "level": ("niveau", "level", "stufe"),
    "verify": ("verifier", "verification", "fais la verification a", "fais la verification a la stabilite",
               "nachweis", "nachweisen", "verify", "check"),
}
# The canonical key of every word, built once: two keys claiming one word is a defect in the table above and is refused at import.
WORDS = {}
for _key, _words in KEYWORDS.items():
    for _word in _words:
        assert fold(_word) not in WORDS, f"the keyword {_word!r} is claimed by {WORDS.get(fold(_word))!r} and by {_key!r}"
        WORDS[fold(_word)] = _key

# Each check the engineer may ask for: the command it becomes, and **the arguments that command takes** (docs/domain/member-checks.md §3.3undecies). A value a block states is passed to the checks that take it and to no other, so a length written for a buckling check is not handed to a shear check that would refuse it.
CHECKS = {
    "tension": ("verify-tension", ("N", "alpha")),
    "compression": ("verify-compression", ("N", "l_k_y", "l_k_z")),
    "compression-perp": ("verify-compression-perp", ("F", "l", "w", "alpha")),
    "bending": ("verify-bending", ("M_y", "M_z", "a", "alpha")),
    "bending-normal": ("verify-bending-normal", ("N", "M_y", "M_z", "l_k_y", "l_k_z", "a")),
    "shear": ("verify-shear", ("V", "V_y", "T")),
    "shear-off": ("verify-shear-off", ("F", "l", "w")),
    "shear-perp": ("verify-shear-perp", ("V", "tau", "sigma_90")),
}
# What the engineer writes for each, in the three languages. «stabilité: compression» is his own wording and reaches the same check as «compression»: the command prints Tragsicherheit and Stabilität as two parts of one page, so there is one check and not two (section 3.3undecies).
CHECK_WORDS = {
    "tension": ("traction", "zug", "tension"),
    "compression": ("compression", "la compression", "stabilite compression", "compression stabilite",
                    "druck", "knicken", "compression stability", "buckling"),
    "compression-perp": ("compression transversale", "querdruck", "compression perpendicular",
                         "transverse compression"),
    "bending": ("flexion", "la flexion", "biegung", "bending", "kippen", "deversement"),
    "bending-normal": ("flexion avec compression", "flexion composee", "flexion avec traction",
                       "biegung mit druck", "biegung mit normalkraft", "bending with compression",
                       "bending with normal force"),
    "shear": ("cisaillement", "schub", "shear"),
    "shear-off": ("cisaillement decale", "schub versetzt", "shear off", "notch"),
    "shear-perp": ("cisaillement transversal", "querzug", "shear perpendicular", "transverse tension"),
}
CHECK_OF = {}
for _key, _words in CHECK_WORDS.items():
    for _word in _words:
        assert fold(_word) not in CHECK_OF, f"the check {_word!r} is claimed twice"
        CHECK_OF[fold(_word)] = _key

# `M_y` is written `M-y:` in a Typst call, and `l_k_y` `l-k-y:`.
ARGUMENT = {"N": "N", "V": "V", "V_y": "V-y", "M_y": "M-y", "M_z": "M-z", "T": "T", "F": "F",
            "tau": "tau", "sigma_90": "sigma-90", "l": "l", "w": "w", "l_k_y": "l-k-y", "l_k_z": "l-k-z",
            "a": "a", "alpha": "alpha"}
# What `#member` itself takes, rather than a check.
MEMBER_ARGUMENT = {"grade": "grade", "moisture": "moisture-class", "b": "b", "h": "h", "d": "d"}

_LINE = re.compile(r"^\s*(?P<key>[^:]+?)\s*:\s*(?P<value>.*?)\s*$")


class Problem:
    """One line that was not understood: its number, what it said, and what it could have said. A refusal names the line rather than guessing, which is what makes the parser worth having over a model."""

    def __init__(self, line, text, message):
        self.line, self.text, self.message = line, text, message

    def __str__(self):
        return f"line {self.line}: {self.message}"

    def __repr__(self):
        return f"Problem({self.line}, {self.text!r}, {self.message!r})"


class Block:
    """One member and what is asked of it: the values stated for it and the checks to make, in the order they were written."""

    def __init__(self, position, line):
        self.position, self.line = position, line
        self.values = {}          # canonical key -> what was written, as text
        self.checks = []          # (check key, the line it was asked on)
        self.level = None

    def __repr__(self):
        return f"Block({self.position!r}, values={self.values!r}, checks={[c for c, _l in self.checks]!r})"


def parse(text):
    """Reads the keyword lines and gives back `(blocks, problems)`.

    Nothing raises: every line that is not understood becomes a Problem, so the tab shows the whole of what was written with the refusals against the lines they belong to -- and what *was* understood still compiles, which is what lets the engineer correct one line at a time.
    """
    blocks, problems, current = [], [], None
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        found = _LINE.match(line)
        if found is None:
            problems.append(Problem(number, line, f"a line is «keyword: value» and this one carries no colon -- "
                                                  f"the keywords are {', '.join(sorted(KEYWORDS))}"))
            continue
        key, value = WORDS.get(fold(found["key"])), found["value"].strip()
        if key is None:
            problems.append(Problem(number, line, f"{found['key'].strip()!r} is not a keyword -- "
                                                  f"the keywords are {', '.join(sorted(KEYWORDS))}"))
            continue
        if key == "position":
            if not value:
                problems.append(Problem(number, line, "a position needs a name: «position: S001»"))
                continue
            current = Block(value, number)
            blocks.append(current)
            continue
        if current is None:
            problems.append(Problem(number, line, f"{found['key'].strip()!r} states something about a member, so a "
                                                  f"«position: …» line comes before it"))
            continue
        if key == "verify":
            check = CHECK_OF.get(fold(value))
            if check is None:
                problems.append(Problem(number, line, f"{value!r} is not a check this engine makes -- "
                                                      f"the checks are {', '.join(sorted(CHECK_WORDS))}"))
                continue
            current.checks.append((check, number))
            continue
        if key == "level":
            if value not in ("0", "1", "2", "3"):
                problems.append(Problem(number, line, f"a level is 0, 1, 2 or 3, and {value!r} is not"))
                continue
            current.level = int(value)
            continue
        if not value:
            problems.append(Problem(number, line, f"{found['key'].strip()!r} states a value and this line gives none"))
            continue
        current.values[key] = value
    return blocks, problems


def _typst_value(text):
    """What is written for an action, as a Typst argument: a bare number as a number, and anything else -- «−40 kN», a variable's name -- as a string, which is what `#member` and the checks read (section 3.3undecies)."""
    cleaned = text.replace("−", "-").strip()
    try:
        float(cleaned)
    except ValueError:
        return '"' + text.strip().replace('"', '\\"') + '"'
    return cleaned


def to_typst(blocks, level=None):
    """The Typst the blocks come to: `#member` for each, then its checks, each with the arguments that command takes and no other.

    ⚠️ A `l_k` stated once is handed to both axes, which is what an engineer means by one buckling length; `l_k_y` and `l_k_z` state them apart.
    """
    out = []
    for block in blocks:
        if out:
            out.append("")
        member = [f'#member("{block.position}"']
        for key, argument in MEMBER_ARGUMENT.items():
            if key in block.values:
                member.append(f"{argument}: {_typst_value(block.values[key])}")
        shown = block.level if block.level is not None else level
        if shown is not None:
            member.append(f"level: {shown}")
        out.append(", ".join(member) + ")")
        values = dict(block.values)
        if "l_k" in values:                     # one buckling length means both axes
            values.setdefault("l_k_y", values["l_k"])
            values.setdefault("l_k_z", values["l_k"])
        for check, _line in block.checks:
            command, takes = CHECKS[check]
            call = [f'#{command}("{block.position}"']
            for key in takes:
                if key in values:
                    call.append(f"{ARGUMENT[key]}: {_typst_value(values[key])}")
            if shown is not None:
                call.append(f"level: {shown}")
            out.append(", ".join(call) + ")")
    return "\n".join(out) + ("\n" if out else "")


def missing(blocks):
    """What a check needs and its block does not state, as a list of sentences -- a warning and never a refusal: the engineer may mean to write the value in the report by hand, and `#member` and the checks say for themselves what they cannot compute."""
    wanted = {
        "tension": ("N",), "compression": ("N",), "compression-perp": ("F",),
        "bending": ("M_y",), "bending-normal": ("N",), "shear": ("V",),
        "shear-off": ("F",), "shear-perp": ("V",),
    }
    out = []
    for block in blocks:
        values = set(block.values)
        if "l_k" in values:
            values |= {"l_k_y", "l_k_z"}
        for check, line in block.checks:
            for key in wanted.get(check, ()):
                if key not in values:
                    out.append(f"line {line}: {block.position} is checked in {check} and states no {key}")
            if check == "compression" and not {"l_k_y", "l_k_z"} & values:
                out.append(f"line {line}: {block.position} is checked in compression and states no buckling length, "
                           f"so only its Tragsicherheit is checked")
    return out
