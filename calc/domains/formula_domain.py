"""A calculation domain written in the «Formules» tab: one `.typ` file of its own, its commands and the Typst written between them, what they compute, and how a report prints it (specs docs/requirements/completed/2026-10-08-onglet-formule-domaines.md and docs/requirements/completed/2026-10-08-onglet-formules-editeur-dossiers-include.md, issue #15).

The engineer, 08.10.2026: «écrire des calculs de manière simplifiée et que ça en fasse des commandes Typst … à chaque fois qu'il y ait des calculs, ils soient compris dans un domaine afin de pouvoir appeler ces domaines à d'autres endroits du rapport».

**One domain is one file**, `<Typst root>/Formules/<id>.typ` (D-11, `project.Project.formulas_dir`), and the file is the source of truth (docs/architecture/principles.md rule 15): the tab reads it, edits it through the model below and writes it back; the engineer may edit it in VS Code, and the tab reads what he wrote. It is Typst a report compiles as it stands:

    #import "/commands.typ": *

    // woodcore:object formula-domain domain
    #var-domain("poutre-p1", title: "Poutre P1")[
    La charge de la toiture :
      #var("q_d", 4.5, "kN/m")
      #var("l", 5, "m")
    $ M_d = q_d l^2 / 8 $
      #eq("M_d", `q_d * l^2 / 8`, unit: "kNm")
      #verify(`M_d <= M_Rd`)
    ]
    // woodcore:/object domain

**The id is the file's name** (issue #15, D-02, D-06): `#var-domain` is given it, so a value is read elsewhere with `#val(key, domain: "<id>")`, and the **name** the tab shows is the call's `title:`, which the report prints as a heading (D-10). A file whose `#var-domain` names another id than its own name -- copied, or renamed in the explorer -- is `hand_edited`, and written back under its own name.

**Between the commands, Typst of the engineer's own** (REQ-006): a title, a sentence, a formula in mathematics -- one `text` item each run of it, written flush left and read back as it was typed. It is printed and never computed; what Typst would compute and Python could not -- a `#var`, `#eq`, `#var-unit` or `#verify` inside it -- is refused, as is a line of tags, and the body is read back in memory before anything is written (ARCH-RISK-108).

**One tag** around the one `#var-domain` call, read by `structure.pair_tags` -- the one reader of tags -- and the call by `typst_objects`'s parser with positional arguments allowed (D-20). Its state has `typst_objects`'s three words: `canonical` (what this module writes reads back to the same bytes), `hand_edited` (it parses, in another form -- written back in Woodcore's only after the tab warns), `unreadable` (it does not parse: shown read only, corrected in VS Code, and an export stops on it naming the file).

**A report prints a domain** with `#include "/Formules/<id>.typ"` (issue #15, D-01), each command at its own `level:` or the report's. The index the export writes, `data/formulas.json`, lists the domains for the «Variables» tab and for the export's own checks (D-08); Typst no longer reads it.

**What a domain computes is computed here, at once** (D-10): `compute` evaluates every command with calc/units.py, the Python twin of lib/formula.typ's algebra, which tests/test_units.py holds equal to it. Nothing here imports Qt.
"""

import json
import re
import unicodedata
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path

import engine
import greek
import project
import structure
import typst_objects
import units
import validation
from tools import build_reference as ref

TAG_TYPE = "formula-domain"
TAG_ID = "domain"
EXPORT_FILE = "formulas.json"
EXPORT_SCHEMA_VERSION = "2.0"   # 2.0 (issue #15): keyed by the id, the file's name, and carrying the title -- 1.0 was keyed by the name v0.117's retired #show-formula read
# The commands a domain holds, in the order the palette offers them (D-04); `var-domain` is the domain itself
COMMANDS = ("var", "eq", "verify", "val", "var-unit")
# The item a run of the engineer's own Typst between two commands is (REQ-006): printed, never computed
TEXT = "text"
# What Typst would compute and Python could not, were it written inside a text: refused there (ARCH-RISK-108) -- `#val` only reads, and a sentence may print a value with it
COMPUTING = ("var", "eq", "verify", "var-unit")
DIGITS = 3   # the decimals the tab prints with -- the report's own default (calc-engine.typ's `number-digits`)
_IMPORT_LINE = '#import "/commands.typ": *'


class DomainError(ValueError):
    """A domain the tab cannot save as asked -- a name taken, a key used twice -- said in a sentence and a code the window translates (`code`, `args`)."""

    def __init__(self, code, message, **args):
        super().__init__(message)
        self.code = code
        self.values = args   # not `args`, which is the exception's own and what str() reads


# --- the model ---------------------------------------------------------------------------------

@dataclass
class Command:
    """One command of a domain. `key` is the registry key, `symbol` the printed symbol ("" where `key-symbol(key)` prints it), `value` a number -- or, for a variable taken from elsewhere (REQ-015), the Typst it is read with (`var-of(…)`) in `source` -- `unit` a variable's unit, an equation's output unit ("" = the table's) or `var-unit`'s new one, `formula` an equation's or a relation's Typst source, `options` every other named argument as `typst_objects` reads a literal. `raw` is the call as written, kept for one this module could not read into a model."""
    kind: str
    key: str = ""
    symbol: str = ""
    value: object = None
    unit: str = ""
    formula: str = ""
    options: dict = field(default_factory=dict)
    source: object = None   # None; ("var-of", "<the call>"); ("domain", "<name>" or (calc, instance))
    raw: str = ""

    @property
    def shown_symbol(self):
        return self.symbol or self.key

    @property
    def defines(self):
        """The registry key this command writes: a variable's, an equation's, a conversion's."""
        return self.key if self.kind in ("var", "eq", "var-unit") else None

    @property
    def is_text(self):
        """A run of the engineer's own Typst between two commands (REQ-006), held in `raw`."""
        return self.kind == TEXT


@dataclass
class Domain:
    """One domain: its id -- its file's name, what `#var-domain` and `#val(domain:)` are given --, its name (the `title:` the tab shows and the report prints), its items -- commands and runs of text --, and what reading its file found. `declared` is the name its `#var-domain` gave, the id where the file is Woodcore's own."""
    id: str
    name: str
    commands: list = field(default_factory=list)
    path: Path = None
    state: str = "canonical"
    problem: str = ""
    text: str = None   # the whole file as it was read, kept so a write changes the body and nothing else
    declared: str = ""
    index_problem: str = ""   # set by `save` alone: the file was written, but the index of the domains could not be (another file unreadable, two files of one id) -- said, never raised

    def keys(self):
        return [c.defines for c in self.commands if c.defines]


# --- keys from what the engineer types ----------------------------------------------------------

_KEY_RESERVED = ("dot", "pi") + units.FUNCTIONS


def key_from_symbol(symbol, taken=()):
    """The registry key a symbol typed by hand is computed with (REQ-008): letters, digits and `_` alone -- never a `-`, which a formula reads as a subtraction --, a Greek letter by its name, a subscript's parts joined by `_`, made unique against `taken` by `_2`, `_3`. `M_(y,d)` → `M_y_d`, `σ_(m,d)` → `sigma_m_d`, `gamma_M` → `gamma_M`."""
    text = str(symbol).replace('"', "")
    out = []
    for c in text:
        if c in greek.BY_LETTER:
            name = greek.BY_LETTER[c]
            if out and re.match(r"[A-Za-z0-9]", out[-1][-1]):
                out.append("_")
            out.append(name)
        elif re.match(r"[A-Za-z0-9_]", c):
            out.append(c)
        elif c.isalpha():
            plain = unicodedata.normalize("NFKD", c).encode("ascii", "ignore").decode()
            out.append(plain or "_")
        else:
            out.append("_")
    key = re.sub(r"_+", "_", "".join(out)).strip("_")
    if not key:
        key = "x"
    if key[0].isdigit():
        key = "v_" + key
    # A word a formula reads as an operation takes `_1`. A key that reads as a unit -- `m`, `l`, `N`, `t`, `s` -- is the engineer's as he typed it since v0.117 (issue #32): lib/formula.typ leaves a quoted unit alone, `(3 "m")` being three metres whatever variable `m` holds, where until then it substituted the variable inside the quotes and such a key had to take `_1` too.
    if key in _KEY_RESERVED:
        key += "_1"
    base, n = key, 1
    while key in taken:
        n += 1
        key = f"{base}_{n}"
    return key


def symbol_for(text, key):
    """The symbol a command writes: none where the text typed is the key itself, which `key-symbol` prints as typed; the text otherwise (ARCH-RISK-107: Python cannot know exactly what `key-symbol` would make of another spelling, so it never relies on it)."""
    text = (text or "").strip()
    return "" if text == key else text


# --- what the engineer types in a formula --------------------------------------------------------

_UNIT_CHARS = re.compile(r"[A-Za-zµμ°%⁰¹²³⁴⁵⁶⁷⁸⁹⁻^/·0-9]")
_NUMBER = re.compile(r"(?:[0-9]+(?:[.,][0-9]*)?|[.,][0-9]+)(?:[eE][+-]?[0-9]+)?")
_BOUNDARY = re.compile(r"[A-Za-z0-9_]")


def _unit_after(text, i):
    """The unit written right after a number at `i` (D-17): the longest run of unit characters that lib/units.json reads as a unit, spaces before it allowed, and what follows it no part of a name. (unit, end) or None."""
    j = i
    while j < len(text) and text[j] == " ":
        j += 1
    if j >= len(text) or not re.match(r"[A-Za-zµμ°%]", text[j]):
        return None
    k = j
    while k < len(text) and _UNIT_CHARS.match(text[k]):
        k += 1
    for end in range(k, j, -1):
        candidate = text[j:end]
        if candidate.endswith(("/", "^", "·")):
            continue
        if end < len(text) and _BOUNDARY.match(text[end]):
            continue
        if units.parse_unit(units.written_unit(candidate)) is not None:
            return units.written_unit(candidate), end
    return None


def _names(variables):
    """Every spelling a variable may be typed by -- its symbol, its key -- with the key it stands for, longest first."""
    out = {}
    for key, symbol in variables:
        for spelling in (symbol, key):
            if spelling and spelling not in out:
                out[spelling] = key
    return sorted(out.items(), key=lambda item: -len(item[0]))


def typst_formula(text, variables):
    """A formula as the engineer types it -- the symbols the tab shows, numbers, a unit after a number, `12 N / 3000 mm` -- as `#eq` and `#verify` read it: each symbol written as its key, each number with a unit in parentheses and its unit in quotes (`(12 "N") / (3000 "mm")`), a decimal comma as a point, `×` as `*`. `variables` is [(key, symbol)] of what the domain declares above."""
    names = _names(variables)
    out, i = [], 0
    while i < len(text):
        c = text[i]
        number = _NUMBER.match(text, i) if (c.isdigit() or c in ".,") and (i == 0 or not _BOUNDARY.match(text[i - 1])) else None
        if number and number.group().strip(".,"):
            written = number.group().replace(",", ".")
            i = number.end()
            unit = _unit_after(text, i)
            if unit:
                # in parentheses: math's `/` takes one atom on each side, and `12 "N" / 3000 "mm"` is set 12 · (N/3000) · mm in the letters line
                out.append(f'({written} "{unit[0]}")')
                i = unit[1]
            else:
                out.append(written)
            continue
        hit = None
        if i == 0 or not _BOUNDARY.match(text[i - 1]):
            for spelling, key in names:
                end = i + len(spelling)
                if text.startswith(spelling, i) and (end >= len(text) or not _BOUNDARY.match(text[end])):
                    hit = (key, end)
                    break
        if hit:
            out.append(hit[0])
            i = hit[1]
            continue
        out.append({"×": "*", "÷": "/", "−": "-"}.get(c, c))
        i += 1
    return re.sub(r"[ ]{2,}", " ", "".join(out)).strip()


def display_formula(formula, variables):
    """A formula's Typst source written back as the tab shows it to be edited: each key as its symbol, each quoted unit bare (`12 "N"` → `12 N`)."""
    symbols = {key: symbol for key, symbol in variables if symbol}
    text = re.sub(r'\(([0-9.eE+-]+)\s*"([^"]*)"\)', r"\1 \2", formula)
    text = re.sub(r'([0-9.])\s*"([^"]*)"', r"\1 \2", text)
    for key in sorted(symbols, key=len, reverse=True):
        text = units._replace_word(text, key, chr(1) + key + chr(2))
    for key, symbol in symbols.items():
        text = text.replace(chr(1) + key + chr(2), symbol)
    return text


# --- reading and writing a domain's file ---------------------------------------------------------

def _literal(value):
    """A value of the model as the call writes it."""
    if isinstance(value, typst_objects.Expr):
        return ref.Raw(value.source)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return ref.Raw(typst_objects.inline(value))


def _raw_text(value):
    """A formula as the model keeps it: the inside of a raw block `` `…` ``, or a string."""
    if isinstance(value, typst_objects.Expr):
        text = value.source.strip()
        if len(text) >= 2 and text[0] == "`" and text[-1] == "`":
            return text[1:-1]
        raise typst_objects.ParseError(f"a formula is written as a raw block, `…`, or a string -- not {text!r}")
    if isinstance(value, str):
        return value
    raise typst_objects.ParseError(f"a formula is written as a raw block, `…` -- not {value!r}")


def from_call(call):
    """One call of a domain's body as a Command. Raises typst_objects.ParseError for one this module cannot hold."""
    kind, pos, named = call.type, list(call.positional), dict(call.args)
    if kind not in COMMANDS:
        raise typst_objects.ParseError(f"#{kind} is none of the commands a domain holds -- {', '.join(COMMANDS)}")
    if kind != "verify" and (not pos or not isinstance(pos[0], str)):
        raise typst_objects.ParseError(f"#{kind} starts with what it names, a string")
    if kind == "var":
        key, rest = pos[0], pos[1:]
        symbol = rest.pop(0) if rest and isinstance(rest[0], str) else ""
        command = Command("var", key=key, symbol=symbol)
        if "domain" in named:
            if rest:
                raise typst_objects.ParseError(f"#var({key!r}) reads its value from domain: and states one besides")
            where = named.pop("domain")
            command.source = ("domain", where if isinstance(where, str) else tuple(where) if isinstance(where, list) else _literal(where))
        elif rest and isinstance(rest[0], typst_objects.Expr):
            command.source = ("var-of", rest[0].source)
            if len(rest) > 1:
                command.unit = rest[1] if isinstance(rest[1], str) else ""
        elif rest and isinstance(rest[0], (int, float)) and not isinstance(rest[0], bool):
            command.value = rest[0]
            if len(rest) > 1:
                if not isinstance(rest[1], str):
                    raise typst_objects.ParseError(f"#var({key!r}): its unit is a string")
                command.unit = rest[1]
            if len(rest) > 2:
                raise typst_objects.ParseError(f"#var({key!r}) has more than a symbol, a value and a unit")
        else:
            raise typst_objects.ParseError(f"#var({key!r}) has no value")
    elif kind == "eq":
        if len(pos) not in (2, 3):
            raise typst_objects.ParseError(f"#eq({pos[0]!r}) is written #eq(key, formula) or #eq(key, symbol, formula)")
        command = Command("eq", key=pos[0], symbol=pos[1] if len(pos) == 3 else "", formula=_raw_text(pos[-1]))
        unit = named.pop("unit", "")
        command.unit = "" if unit in (None, "") or isinstance(unit, typst_objects._Auto) else str(unit)
    elif kind == "verify":
        if len(pos) != 1:
            raise typst_objects.ParseError("#verify takes one relation")
        command = Command("verify", formula=_raw_text(pos[0]))
    elif kind == "val":
        if len(pos) != 1:
            raise typst_objects.ParseError("#val takes one name")
        command = Command("val", key=pos[0])
        if "domain" in named:
            where = named.pop("domain")
            command.source = ("domain", where if isinstance(where, str) else tuple(where) if isinstance(where, list) else _literal(where))
    else:
        if len(pos) != 2 or not isinstance(pos[1], str):
            raise typst_objects.ParseError("#var-unit takes a name and a unit")
        command = Command("var-unit", key=pos[0], unit=pos[1])
    command.options = named
    return command


def to_call(command):
    """The command's call, as a domain's file writes it: only what differs from the signature's defaults (build_reference.call_command, ARCH-003). A text is its own Typst, as typed."""
    c = command
    if c.raw and c.kind not in COMMANDS:
        return c.raw
    options = {name.replace("-", "_"): _literal(value) for name, value in c.options.items()}
    if c.kind == "eq" and c.unit:
        options = {"unit": c.unit, **options}
    if c.kind == "var":
        head = [c.key] + ([c.symbol] if c.symbol else [])
        if c.source and c.source[0] == "domain":
            where = c.source[1]
            options["domain"] = list(where) if isinstance(where, tuple) else where
            return ref.call_command("var", *head, **options)
        if c.source and c.source[0] == "var-of":
            return ref.call_command("var", *head, ref.Raw(c.source[1]), *([c.unit] if c.unit else []), **options)
        return ref.call_command("var", *head, c.value, *([c.unit] if c.unit else []), **options)
    if c.kind == "eq":
        return ref.call_command("eq", c.key, *([c.symbol] if c.symbol else []), ref.Raw("`" + c.formula + "`"), **options)
    if c.kind == "verify":
        return ref.call_command("verify", ref.Raw("`" + c.formula + "`"), **options)
    if c.kind == "val":
        if c.source and c.source[0] == "domain":
            where = c.source[1]
            options["domain"] = list(where) if isinstance(where, tuple) else where
        return ref.call_command("val", c.key, **options)
    return ref.call_command("var-unit", c.key, c.unit, **options)


def header_of(domain):
    """`#var-domain("<id>", title: "<name>")[` -- the line a domain's body opens with (D-06, D-10)."""
    title = f", title: {ref.typst_str(domain.name)}" if domain.name else ""
    return "#var-domain(" + ref.typst_str(domain.id) + title + ")["


def body_of(domain):
    """The `#var-domain(…)[…]` call as the file writes it: one command a line, two spaces in; a text flush left, as it was typed (REQ-006) -- indenting it would change a raw block or a string it holds."""
    lines = [header_of(domain)]
    for c in domain.commands:
        lines.append(c.raw if c.is_text else "  " + to_call(c))
    lines.append("]")
    return "\n".join(lines)


def file_text(domain):
    """A new domain's whole file."""
    return "\n".join([_IMPORT_LINE, "", f"// woodcore:object {TAG_TYPE} {TAG_ID}", body_of(domain), f"// woodcore:/object {TAG_ID}", ""])


def _body_span(text):
    """(first line, line after the last) of the body between the domain's two tags, the lines as structure splits them, or a reason the tags cannot be read."""
    blocks, problems = structure.pair_tags(text, object_types=(TAG_TYPE,))
    if problems:
        return None, "; ".join(str(p) for p in problems)
    found = [b for b in blocks if b.kind == "object" and b.type == TAG_TYPE]
    if len(found) != 1:
        return None, f"a domain's file holds one `// woodcore:object {TAG_TYPE} {TAG_ID}` block -- this one holds {len(found)}"
    return (found[0].start + 1, found[0].end), ""


def parse_body(body):
    """(declared name, title, items) of a `#var-domain("…", title: "…")[…]` body -- the commands and, between them, the runs of the engineer's own Typst (`text` items). Raises typst_objects.ParseError."""
    text = typst_objects._normalise(body)
    parser = typst_objects._Parser(text)
    start = parser.ws(0)
    if start >= parser.n:
        parser.fail("the domain holds no #var-domain call", start)
    call, end = parser.call(start, positional=True)
    if parser.ws(end) < parser.n:
        parser.fail("a domain's block holds its #var-domain call and nothing after it", parser.ws(end))
    title = call.args.get("title", "") if call.type == "var-domain" else None
    if (call.type != "var-domain" or len(call.positional) != 1 or not isinstance(call.positional[0], str)
            or set(call.args) - {"title"} or not isinstance(title, str)):
        parser.fail('a domain is written #var-domain("its id", title: "its name")[…]', start)
    if call.body is None:
        parser.fail("#var-domain has no content block", end)
    return call.positional[0], title, split_items(call.body.markup)


# A line that opens with one of the domain's commands: a command, where it stands alone on its line at the top of the body
_COMMAND_LINE = re.compile(r"[ \t]*#(" + "|".join(sorted((re.escape(c) for c in COMMANDS), key=len, reverse=True)) + r")\(")


def _top_level_lines(markup):
    """The offsets of the lines of `markup` that begin in its own markup -- not inside a raw block, a comment, a string, an equation or a call --, read with typst_paths' lexer, the one that walks Typst's modes (ARCH-RISK-108: never a regex on `#var(`). Also every `#name` the lexer met, with its offset: what `check_text` refuses."""
    import typst_paths
    starts = [0] + [i + 1 for i, c in enumerate(markup) if c == "\n"]
    top, hashes = set(), []
    lexer = typst_paths._Lexer(markup)
    original = lexer._hash

    def hashed(j):
        found = typst_paths._IDENT.match(markup, j + 1)
        if found is not None:
            hashes.append((j, found.group()))
        original(j)
    lexer._hash = hashed
    k = 0
    while lexer.i < lexer.n:
        at = lexer.i
        frame = lexer.stack[-1]
        plain = len(lexer.stack) == 1 and frame[0] == "markup" and frame[2] == 0
        if plain:
            special = typst_paths._MARKUP_SPECIAL.search(markup, at)
            stop = special.start() if special else lexer.n
            while k < len(starts) and starts[k] < at:
                k += 1
            j = k
            while j < len(starts) and starts[j] <= stop:
                top.add(starts[j])
                j += 1
        getattr(lexer, "_" + frame[0])(frame)
        if lexer.i == at and lexer.stack[-1] is frame:
            lexer.i += 1   # a lexer that does not move would loop: never seen, guarded
    return top, hashes


def plain_spans(markup):
    """The offsets of the lines of `markup` that begin in its own markup -- not inside a raw block, a comment, a string, an equation or a call -- read with typst_paths' lexer (ARCH-RISK-108), as a sorted list: where a command may stand on a line of its own without changing what the text around it means. The public face of `_top_level_lines` (issue #40, ARCH-004), which formula_layout reads to refuse a drop."""
    top, _hashes = _top_level_lines(typst_objects._normalise(markup))
    return sorted(top)


def tidy_items(items):
    """The items as a domain's body keeps them (issue #40, D-05, D-07): a **blank line beside a command is a paragraph** -- Typst's own rule, two line breaks a new paragraph (docs/typst/formulas.md) -- and is kept, **one at most**, at the head of a text that follows a command and at the tail of one a command follows; one between two commands is an empty text (`raw == ""`). Blank lines at the very start or end of the body are no paragraph and go, as does an empty text that does not stand between two commands; two texts in a row are one. What a text holds between its first and last written lines is kept as typed."""
    out = []
    for c in items:
        if c.is_text and out and out[-1].is_text:
            joined = out[-1].raw + "\n" + c.raw if out[-1].raw and c.raw else out[-1].raw or c.raw
            out[-1] = Command(TEXT, raw=joined)
        else:
            out.append(c)
    tidy = []
    for i, c in enumerate(out):
        if not c.is_text:
            tidy.append(c)
            continue
        lines = typst_objects._normalise(c.raw).split("\n")
        head = bool(lines) and not lines[0].strip()
        while lines and not lines[0].strip():
            lines.pop(0)
        tail = bool(lines) and not lines[-1].strip()
        while lines and not lines[-1].strip():
            lines.pop()
        before, after = i > 0, i < len(out) - 1   # a command on that side: the text stands between the two
        if not lines:
            if before and after:
                tidy.append(Command(TEXT, raw=""))
            continue
        tidy.append(Command(TEXT, raw="\n".join(([""] if head and before else []) + lines + ([""] if tail and after else []))))
    return tidy


def split_items(markup):
    """The items of a domain's body: each command that stands alone on its line(s) at the top of the body, and each run of lines between two of them as one `text` item, kept as typed -- one blank line beside a command kept as the paragraph it is, an empty text between two commands (`tidy_items`, issue #40, D-05: until then every blank line beside a command was left out, and two paragraphs ran into one). Raises typst_objects.ParseError where a command cannot be read."""
    markup = typst_objects._normalise(markup)
    top, _hashes = _top_level_lines(markup)
    sub = typst_objects._Parser(markup)
    items, pending, i = [], [], 0
    n = len(markup)

    def flush():
        if pending:   # no line at all between two commands is no text; blank lines are a paragraph (tidy_items)
            items.append(Command(TEXT, raw="\n".join(pending)))
        pending.clear()
    while i < n:
        eol = markup.find("\n", i)
        eol = n if eol < 0 else eol
        line = markup[i:eol]
        found = _COMMAND_LINE.match(line) if i in top else None
        if found:
            at = i + len(line) - len(line.lstrip(" \t"))
            call, end = sub.call(at, positional=True)
            after = markup.find("\n", end)
            after = n if after < 0 else after
            rest = markup[end:after].strip()
            if not rest or rest.startswith("//"):
                if call.body is not None:
                    sub.fail(f"#{call.type} takes no content block", end)
                flush()
                items.append(from_call(call))
                if rest:   # a comment after a call, written by hand: kept, on a line of its own (the file is then hand_edited)
                    pending.append(rest)
                i = after + 1
                continue
        pending.append(line)
        i = eol + 1
    flush()
    return tidy_items(items)


def check_text(raw):
    """Refuses what a text between two commands may not hold (ARCH-RISK-108), with its reason: a command Typst would compute and Python would not (`#var`, `#eq`, `#var-unit`, `#verify`), a line of Woodcore's tags, which the file's own reader would take for its own. Raises DomainError `text`."""
    for line in typst_objects._normalise(raw).split("\n"):
        if line.strip().startswith("// woodcore:"):
            raise DomainError("text_tag", f"a text of the domain holds a line of Woodcore's tags: {line.strip()!r}", line=line.strip())
    text = typst_objects._normalise(raw)
    _top, hashes = _top_level_lines(text)
    for j, name in hashes:
        if name in COMPUTING:
            start = text.rfind("\n", 0, j) + 1
            eol = text.find("\n", j)
            eol = len(text) if eol < 0 else eol
            line = text[start:eol].strip()
            trailing = _after_call(text, j, eol) if not text[start:j].strip() else ""
            if trailing:
                # the commonest case: `#var(...) ;` -- the call alone on its line but for what follows it, which makes the line a text
                hint = f'#{name}(..., sep: "{trailing}")' if name in SEPARATED and _PUNCTUATION.fullmatch(trailing) else f"#{name}(...) alone on its line"
                raise DomainError("text_trailing", f"{line!r}: {trailing!r} after #{name}(...) on the same line is refused -- it makes the line a text, which Woodcore does not compute. Write {hint}, without {trailing!r} after the call; several values written one line after the other print on one line (inline is the default, note: \"line\" sets one on a line of its own)", command=name, line=line, rest=trailing, hint=hint)
            raise DomainError("text_command", f"a text of the domain holds #{name} ({line!r}): write it as a block of its own, which Woodcore computes -- in a text the report would compute it and Woodcore would not", command=name, line=line)


# The commands that take `sep:` (lib/formula.typ, spec 2026-10-11-argument-sep-var), and what a separator typed after one of them looks like: what the refusal proposes to write as `sep:` instead
SEPARATED = ("var", "eq", "var-unit")
_PUNCTUATION = re.compile(r"[;,:/|–—-]")


def _after_call(text, at, eol):
    """What follows the call that starts at `at` on its own line, stripped -- "" where the call cannot be read or nothing follows it."""
    try:
        _call, end = typst_objects._Parser(text).call(at, positional=True)
    except typst_objects.ParseError:
        return ""
    if end > eol:
        after = text.find("\n", end)
        eol = len(text) if after < 0 else after
    rest = text[end:eol].strip()
    return "" if rest.startswith("//") else rest


def read(path):
    """The domain one file holds. A file that cannot be read is a Domain all the same, `unreadable`, its reason in `problem` -- the tab shows it read only."""
    path = Path(path)
    with open(path, encoding="utf-8", newline="") as file:
        text = file.read()   # the text as it is, its line endings with it: a write keeps them
    domain = Domain(id=path.stem, name="", path=path, text=text)
    span, why = _body_span(text)
    if span is None:
        domain.state, domain.problem = "unreadable", why
        return domain
    lines = structure._split(text)
    body = "".join(lines[span[0]:span[1]])
    try:
        domain.declared, domain.name, domain.commands = parse_body(body)
        for c in domain.commands:
            if c.is_text:
                check_text(c.raw)
    except typst_objects.ParseError as exc:
        domain.state, domain.problem = "unreadable", str(exc)
        return domain
    except DomainError as exc:   # a computing command inside a text: Typst and Python would disagree on what it gives
        domain.state, domain.problem = "unreadable", str(exc)
        return domain
    if domain.declared != domain.id or typst_objects._normalise(body).strip() != body_of(domain).strip():
        domain.state = "hand_edited"   # another id than its file's name -- copied, renamed outside -- is written back under its own
    return domain


def check_body(domain):
    """The body as it would be written, refused where it does not read back to the same items (ARCH-RISK-108): a text with a `]` too many would close `#var-domain` early, one with a computing command or a tag line would be taken for another thing. Raises DomainError `text`; nothing is written."""
    items = tidy_items(domain.commands)
    for c in items:
        if c.is_text:
            check_text(c.raw)
    body = body_of(replace(domain, commands=items))
    try:
        _declared, _title, back = parse_body(body)
    except typst_objects.ParseError as exc:
        raise DomainError("text_unbalanced", f"the domain would not read back once written -- a text's brackets do not balance? ({exc})", reason=str(exc))
    if [(c.kind, c.raw if c.is_text else to_call(c)) for c in back] != [(c.kind, c.raw if c.is_text else to_call(c)) for c in items]:
        raise DomainError("text_unbalanced", "the domain would not read back once written as it is now -- a text holds what reads as a command, or the brackets of a text do not balance")
    return items


def write_text(domain):
    """The file's text with the domain's body written in Woodcore's form between its two tags and **nothing else changed** (every byte outside the body kept, the file's own line endings) -- or a new file's whole text."""
    domain = replace(domain, commands=check_body(domain))
    if domain.text is None:
        return file_text(domain)
    span, why = _body_span(domain.text)
    if span is None:
        raise DomainError("unreadable", f"{domain.path.name if domain.path else domain.id}: its tags cannot be read ({why}) -- correct it in VS Code", file=domain.id, reason=why)
    lines = structure._split(domain.text)
    newline = "\r\n" if lines and lines[0].endswith("\r\n") else "\n"
    body = body_of(domain).replace("\n", newline) + newline
    return "".join(lines[:span[0]]) + body + "".join(lines[span[1]:])


# --- the project's domains ----------------------------------------------------------------------

def list_domains(here=None):
    """Every domain of the project, by file name: `<Typst root>/Formules/*.typ`."""
    here = here or project.current()
    folder = here.formulas_dir
    return [read(path) for path in sorted(folder.glob("*.typ"))] if folder.is_dir() else []


def slug(name):
    """A file id for a domain named `name`: lower case, digits and hyphens (structure.ID_PATTERN's alphabet), accents dropped."""
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    out = re.sub(r"[^a-z0-9]+", "-", plain).strip("-")
    return out if out and out[0].isalpha() else ("d-" + out if out else "domaine")


def free_id(here, base, taken=()):
    """`base`, or `base-2`, `base-3`…, the first no domain and no file of Formules/ bears."""
    fid, n = base, 1
    while fid in taken or (here.formulas_dir / f"{fid}.typ").exists():
        n += 1
        fid = f"{base}-{n}"
    return fid


def new_domain(here, name, domains=None):
    """A domain not yet written, its id made from its name and free in the folder -- made again from the name at its first write, until the engineer types an id of his own (REQ-004)."""
    domains = list_domains(here) if domains is None else domains
    check_name(name)
    fid = free_id(here, slug(name), {d.id for d in domains})
    return Domain(id=fid, name=name, path=here.formulas_dir / f"{fid}.typ")


def check_name(name):
    """A domain's name is its title, free text on one line -- two domains may bear the same, the id telling them apart (D-06)."""
    if not name or not name.strip():
        raise DomainError("name_empty", "a domain needs a name")
    if "\n" in name or "\r" in name:
        raise DomainError("name_line", "a domain's name is one line", name=name)


def check_id(fid, domains, own=None, here=None):
    """An id a domain may take: lower-case letters, digits and hyphens (structure.ID_PATTERN, the file's name), and no other domain's -- nor another file's of Formules/. Raises DomainError `id_invalid` or `id_taken`."""
    if not fid or not structure.ID_PATTERN.match(fid):
        raise DomainError("id_invalid", f"{fid!r} is no id: lower-case letters, digits and hyphens, starting with a letter", id=fid)
    taken = {d.id for d in domains if d.id != own}
    if fid in taken or (here is not None and fid != own and (here.formulas_dir / f"{fid}.typ").exists()):
        raise DomainError("id_taken", f"the id {fid!r} is another domain's", id=fid)


def check_keys(domain):
    """A key defined twice in a domain, said -- `#var-unit` excepted, which converts one already there."""
    seen = set()
    for c in domain.commands:
        if c.kind in ("var", "eq"):
            if c.key in seen:
                raise DomainError("key_taken", f"{c.key!r} is defined twice in {domain.name!r}", key=c.key, domain=domain.name)
            seen.add(c.key)


def cited_by(here, fid):
    """[(file relative to the Typst root, line number, line)] of the project's Typst that cite the domain `fid` -- `#include "/Formules/<id>.typ"` or `domain: "<id>"` --: what an id changed leaves to correct, said and never rewritten (D-11). The generated folder and the archives are not read."""
    root = here.typst_root
    generated = here.generated_dir.resolve()
    patterns = (f'"/{project.FORMULAS_FOLDER}/{fid}.typ"', f'domain: "{fid}"', f'domain:"{fid}"')
    found = []
    for path in sorted(root.rglob("*.typ")):
        resolved = path.resolve()
        if resolved.is_relative_to(generated) or "archives" in path.relative_to(root).parts:
            continue
        if path.parent.resolve() == here.formulas_dir.resolve() and path.stem == fid:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for number, line in enumerate(lines, 1):
            if any(p in line for p in patterns):
                found.append((path.relative_to(root).as_posix(), number, line.strip()))
    return found


def rename(here, domain, new_id, domains=None):
    """The domain's id changed (REQ-004, ARCH-RISK-105): checked first, the file moved -- the one step that cannot be half done --, then written with its new `#var-domain` and the index written again. Returns (the domain read back, what still cites the old id). A file another program holds is said, nothing changed."""
    import os
    domains = list_domains(here) if domains is None else domains
    old = domain.id
    if new_id == old:
        return domain, []
    check_id(new_id, domains, own=old, here=here)
    check_unchanged(domain)   # before the move: a file changed meanwhile is read again, not renamed and then written over
    target = here.formulas_dir / f"{new_id}.typ"
    if domain.path is not None and domain.path.is_file():
        try:
            os.replace(domain.path, target)
        except OSError as exc:
            raise DomainError("rename_failed", f"{domain.path.name} cannot be renamed -- is it open in another program? ({exc})", file=domain.path.name)
        domain.text = target.read_text(encoding="utf-8", newline="") if domain.text is not None else None
    domain.id, domain.path = new_id, target
    saved = save(here, domain)
    return saved, cited_by(here, old)


def duplicate(here, domain, name, domains=None):
    """A copy of the domain under a new name and a free id, written at once: its items as they are (REQ-009)."""
    domains = list_domains(here) if domains is None else domains
    check_name(name)
    fid = free_id(here, slug(name), {d.id for d in domains})
    copy = Domain(id=fid, name=name, path=here.formulas_dir / f"{fid}.typ",
                  commands=[replace(c, options=dict(c.options)) for c in domain.commands])
    return save(here, copy)


def check_unchanged(domain, path=None):
    """Refuses to write over a file that changed on the disk since the domain was read from it -- VS Code, another Woodcore, an engine synced (ARCH-RISK-108's twin for the whole file): the domain the tab holds is then older than the file, and writing it would silently drop every line written since. A domain never written (`text` None) may not take the place of a file that appeared meanwhile. Raises DomainError `changed_on_disk`; nothing is written."""
    path = path or domain.path
    if path is None or not path.is_file():
        return
    try:
        with open(path, encoding="utf-8", newline="") as file:
            on_disk = file.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise DomainError("changed_on_disk", f"{path.name} cannot be read back before it is written ({exc})", file=path.name)
    if domain.text is None or on_disk != domain.text:
        raise DomainError("changed_on_disk", f"{path.name} changed on the disk since Woodcore read it -- it is read again, and nothing was written over it", file=path.name)


def save(here, domain):
    """Writes the domain's file and the export's index of the domains (`data/formulas.json`), so that the «Variables» tab lists a domain the moment it is saved (REQ-010). Returns the domain as read back. A file changed on the disk since the domain was read is never written over (`check_unchanged`)."""
    check_keys(domain)
    text = write_text(domain)
    path = domain.path or (here.formulas_dir / f"{domain.id}.typ")
    check_unchanged(domain, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")
    saved = read(path)
    try:
        export(here)
    except validation.ValidationError as exc:
        # the file is written: what stops the index is another file of Formules/ (unreadable, or of the same id) -- said by the tab, never an unexpected error
        saved.index_problem = str(exc)
    return saved


ARCHIVES = "archives"


def remove(here, domain):
    """Takes a domain's file out of the folder into `Formules/archives/<stamp>-<id>.typ` -- never deleted, as a removed object is archived (docs/domain/documents.md §3.3octodecies), a second removal in the same second numbered rather than written over (ARCH-RISK-206) -- and writes the index again."""
    if domain.path is None or not domain.path.is_file():
        return None
    folder = domain.path.parent / ARCHIVES
    folder.mkdir(parents=True, exist_ok=True)
    stem = f"{datetime.now().strftime('%y%m%d-%H%M%S')}-{domain.path.stem}"
    target, n = folder / f"{stem}.typ", 1
    while target.exists():
        n += 1
        target = folder / f"{stem}-{n}.typ"
    domain.path.replace(target)
    export(here)
    return target


def archived(here):
    """[(the archive's key -- its file name --, the domain it holds)] of Formules/archives/, newest first: what «Archives» lists."""
    folder = here.formulas_dir / ARCHIVES
    if not folder.is_dir():
        return []
    return [(path.name, read(path)) for path in sorted(folder.glob("*.typ"), reverse=True)]


def restore(here, key, domains=None):
    """An archived domain back into Formules/ under its own id, or a free one made from it where the id was taken since -- its `#var-domain` written with that id --, and the index written again. Returns the domain read back."""
    domains = list_domains(here) if domains is None else domains
    path = here.formulas_dir / ARCHIVES / key
    if not path.is_file():
        raise DomainError("archive_missing", f"{key} is no longer in {project.FORMULAS_FOLDER}/{ARCHIVES}/", key=key)
    domain = read(path)
    if domain.state == "unreadable":
        raise DomainError("unreadable", f"{key}: {domain.problem}", file=key, reason=domain.problem)
    base = domain.declared if domain.declared and structure.ID_PATTERN.match(domain.declared) else slug(domain.name or "domaine")
    fid = free_id(here, base, {d.id for d in domains})
    target = here.formulas_dir / f"{fid}.typ"
    path.replace(target)
    domain.id, domain.path = fid, target
    return save(here, domain)


def purge(here, key):
    """An archived domain deleted for good -- what «Archives»' own menu does, asked first by the window."""
    path = here.formulas_dir / ARCHIVES / key
    if path.is_file():
        path.unlink()


# --- the export: data/formulas.json, the index the «Variables» tab and the export's checks read ---------

def empty():
    return {"schema_version": EXPORT_SCHEMA_VERSION, "domains": {}}


def prepare(here=None):
    """(data, warnings): every domain's id, title and file, sorted by id. A file that cannot be read **stops** the export, naming it (a malformed file stops); two files whose `#var-domain` gives one name too, since `#val(domain:)` could read either. A file written by hand is exported as it stands, and said."""
    here = here or project.current()
    data, notes, files = empty(), [], {}
    for domain in list_domains(here):
        rel = f"{project.FORMULAS_FOLDER}/{domain.path.name}"
        if domain.state == "unreadable":
            raise validation.ValidationError(f"{rel}: the calculation domain cannot be read -- {domain.problem}. Correct it in VS Code or in Woodcore's «Formules» tab")
        if domain.declared in files:
            raise validation.ValidationError(f"{rel} and {files[domain.declared]} both declare #var-domain({domain.declared!r}) -- give one of the two its own id")
        files[domain.declared] = rel
        if domain.state == "hand_edited":
            notes.append(engine.Note("formula_hand_edited", f"{rel}: the domain {domain.id!r} is written by hand in another form than Woodcore's -- it is exported as it stands, and the «Formules» tab rewrites it in its own", file=rel, domain=domain.id))
        data["domains"][domain.id] = {"title": domain.name, "file": rel}
    data["domains"] = dict(sorted(data["domains"].items()))
    validation.validate_structure(data, "formulas")
    return data, notes


def write(data, data_dir):
    engine.write_json(Path(data_dir) / EXPORT_FILE, data)


def export(here=None):
    """prepare + write: what a save runs, so the report reads a new domain without a whole export."""
    here = here or project.current()
    data, notes = prepare(here)
    here.data_dir.mkdir(parents=True, exist_ok=True)
    write(data, here.data_dir)
    return notes


# --- what a domain computes ---------------------------------------------------------------------

@dataclass
class Result:
    """What one command gives: its value and unit; the formula in letters and in numbers (math source the tab sets with richtext.math_html); a relation's truth; and, where it gives nothing, why."""
    value: object = None
    unit: str = ""
    letters: str = ""
    numbers: str = ""
    holds: object = None
    op: str = ""
    error: str = ""
    warning: dict = None


def _symbol_of(key, symbols):
    return symbols.get(key) or key


def _letters(formula, symbols):
    src = units.star_as_dot(formula)
    keys = sorted(symbols, key=len, reverse=True)
    for i, key in enumerate(keys):
        src = units._replace_word(src, key, f"{chr(1)}{i}{chr(2)}")
    for i, key in enumerate(keys):
        src = src.replace(f"{chr(1)}{i}{chr(2)}", "(" + _symbol_of(key, symbols) + ")" if " " in _symbol_of(key, symbols) else _symbol_of(key, symbols))
    return re.sub(r"\s+", " ", src).strip()


def _numbers(formula, values, digits=DIGITS):
    src = units.star_as_dot(formula)
    keys = sorted(values, key=len, reverse=True)
    for i, key in enumerate(keys):
        src = units._replace_word(src, key, f"{chr(1)}{i}{chr(2)}")
    for i, key in enumerate(keys):
        value, unit = values[key]
        text = units.signed(units.fmt_magnitude(value, digits)) if isinstance(value, (int, float)) else str(value)
        written = f'"{text}{"" if unit == "°" else " "}{unit}"' if unit else (f"({text})" if text.startswith(units.MINUS) else text)
        src = src.replace(f"{chr(1)}{i}{chr(2)}", written)
    return re.sub(r"\s+", " ", src).strip()


def compute(domain, resolve=None, digits=DIGITS):
    """What every command of `domain` gives, in order: [Result]. A command the report would refuse is a Result with its `error` -- the reason the compile would stop on -- and the commands after it go on, a name it would have defined being then unknown to them. `resolve(command)` gives a variable taken from elsewhere its (value, unit), or None where it cannot be found (REQ-015)."""
    values, symbols, out = {}, {}, []
    for c in domain.commands:
        r = Result()
        if c.is_text:      # printed, never computed: an empty result keeps every list aligned with the items (ARCH-RISK-108)
            out.append(r)
            continue
        try:
            if c.kind == "var":
                if c.source:
                    got = resolve(c) if resolve else None
                    if got is None:
                        raise units.FormulaError(f"var: {c.key!r} is taken from {describe_source(c)}, which gives no value here")
                    value, unit = got
                    unit = c.unit or unit
                else:
                    value, unit = c.value, units.written_unit(c.unit or "")
                if isinstance(value, (int, float)) and units.parse_unit(unit) is None:
                    raise units.FormulaError(f"var: cannot read the unit {unit!r} of {c.key!r} -- write it as the report writes one, `kN`, `N/mm²`, `kNm`")
                values[c.key] = (value, unit)
                symbols[c.key] = c.symbol
                r.value, r.unit = value, unit
            elif c.kind == "eq":
                q, operands = units.evaluate("eq", c.formula, values)
                symbol = c.symbol or c.key
                value, unit, warning = units.present("eq", symbol, q, units.written_unit(c.unit) or None)
                r.value, r.unit, r.warning = value, unit, warning
                r.letters = _letters(c.formula, {k: symbols.get(k, "") for k in operands})
                r.numbers = _numbers(c.formula, {k: values[k] for k in operands}, digits)
                values[c.key] = (value, unit)
                symbols[c.key] = c.symbol
            elif c.kind == "verify":
                left, op, right = units.split_relation(units.star_as_dot(c.formula))
                sides = []
                for side in (left, right):
                    q, operands = units.evaluate("verify", side.strip(), values)
                    one = operands[0] if len(operands) == 1 and operands[0] == side.strip() else None
                    sides.append((q, operands, one))
                (lq, lops, lone), (rq, rops, rone) = sides
                if not units.dims_equal(lq.dims, rq.dims):
                    raise units.FormulaError(f"verify: comparing {units.dims_text(lq.dims)} with {units.dims_text(rq.dims)} -- the two sides of a relation must have the same dimensions")
                r.holds = units.holds(op, lq.base, rq.base)
                r.op = op if r.holds else units.RELATION_NEGATION[op]
                shown = []
                for q, operands, one in sides:
                    if one is not None:
                        shown.append(values[one])
                    else:
                        v, u, _w = units.present("verify", "", q)
                        shown.append((v, u))
                r.value = (shown[0], shown[1])
                r.letters = _letters(left.strip(), {k: symbols.get(k, "") for k in lops}) + f" {op} " + _letters(right.strip(), {k: symbols.get(k, "") for k in rops})
            elif c.kind == "val":
                if c.source:
                    got = resolve(c) if resolve else None
                    if got is None:
                        raise units.FormulaError(f"val: {c.key!r} is read from {describe_source(c)}, which gives no value here")
                    r.value, r.unit = got
                elif c.key not in values:
                    raise units.FormulaError(f"val: no variable named {c.key!r} here -- declared here: {', '.join(values) or 'none'}")
                else:
                    r.value, r.unit = values[c.key]
            else:  # var-unit
                if c.key not in values:
                    raise units.FormulaError(f"var-unit: no variable named {c.key!r} here -- declared here: {', '.join(values) or 'none'}")
                value, unit = values[c.key]
                q = units.quantity(float(value), unit)
                new = units.written_unit(c.unit)
                p = units.parse_unit(new)
                if p is None:
                    raise units.FormulaError(f"var-unit: cannot read the unit {c.unit!r}")
                if q is None or not units.dims_equal(q.dims, p[1]):
                    raise units.FormulaError(f"var-unit: {c.key!r} is in {unit}, which is not of the dimension of {new}")
                values[c.key] = (q.base / p[0], new)
                r.value, r.unit = values[c.key]
        except units.FormulaError as exc:
            r.error = str(exc)
        out.append(r)
    return out


def variables_of(domain, results=None):
    """[(key, symbol, value, unit)] of what the domain defines, in order -- the list at the top of the tab's right pane (T23); a key redefined by a conversion keeps its place."""
    results = results if results is not None else compute(domain)
    out, index = [], {}
    for c, r in zip(domain.commands, results):
        if c.defines and not r.error:
            row = (c.key, c.symbol, r.value, r.unit)
            if c.key in index:
                out[index[c.key]] = row
            else:
                index[c.key] = len(out)
                out.append(row)
    return out


# --- variables taken from elsewhere (REQ-015) ------------------------------------------------------

CIRCLE = "the domains take their values from each other in a circle"
_VAR_OF = re.compile(r'^\s*var-of\(\s*"([^"]*)"\s*,\s*"([^"]*)"\s*,\s*"([^"]*)"\s*\)\s*$')


def describe_source(command):
    kind, where = command.source
    if kind == "var-of":
        found = _VAR_OF.match(where)
        return f"{found.group(1)} / {found.group(2)}" if found else where
    return " / ".join(where) if isinstance(where, tuple) else str(where)


def resolve_import(here, command, domains=(), _stack=(), calculations=None):
    """The (value, unit) a variable taken from elsewhere has now, or None where it cannot be read here: a value of the export (`var-of(calc, instance, name)`, or `domain:` a pair), read off `data/calculations.json`; a variable of another of the project's domains (`domain:` a name), computed now -- a cycle between domains is refused, naming it. A domain of a document's own sections is compiled, never computed here: it gives None, and the tab says the value is read when the document is."""
    kind, where = command.source
    name = command.key
    pair = None
    if kind == "var-of":
        found = _VAR_OF.match(where)
        if found:
            pair, name = (found.group(1), found.group(2)), found.group(3)
    elif isinstance(where, tuple) and len(where) == 2:
        pair = where
    if pair is not None:
        try:
            # the export being built where one is handed over (export_all: the values a linked field follows, spec 2026-10-11-variables-liees-champs-et-textes ARCH-RISK-003), else the last one written
            calcs = calculations if calculations is not None else json.loads((here.data_dir / "calculations.json").read_text(encoding="utf-8"))
            var = calcs["domains"][pair[0]]["instances"][pair[1]]["vars"][name]
        except (OSError, ValueError, KeyError, TypeError):
            return None
        return var.get("value"), var.get("unit", "") or ""
    if isinstance(where, str):
        other = next((d for d in domains if d.id == where), None)    # a domain of the tab is named by its id (D-06)
        if other is None:
            return None
        if other.id in _stack:
            raise units.FormulaError(f"var: {CIRCLE} -- " + " → ".join(list(_stack) + [other.id]))
        results = compute(other, lambda c: resolve_import(here, c, domains, _stack + (other.id,), calculations))
        for c, r in reversed(list(zip(other.commands, results))):
            if c.defines == name:
                if CIRCLE in r.error:
                    raise units.FormulaError(r.error)   # said where it was asked for, not lost as «gives no value»
                return None if r.error else (r.value, r.unit)
    return None


# --- the «Variables» tab's source (spec 2026-10-08-onglet-variables-trois-colonnes, its FILE_SOURCES) ---------------

# The origin the «Variables» tab gives a domain of the «Formules» tab: neither the export -- it has no (calculation, instance) a call names it by -- nor a document's registry, which holds it only where a document prints it. A call names it by its id, `#val(key, domain: "<id>")` (D-06), its name shown beside it.
ORIGIN = "formulas"


def variable_domains(data, here=None, calculations=None):
    """The domains data/formulas.json names, as the «Variables» tab lists them (variable_sources.FILE_SOURCES's reader): each under its id with its name as label (D-06), computed now, its variables with their values, their source the domain's own file (`woodcore:Formules/<id>.typ`). A file that cannot be read is left out -- the export names it and stops."""
    import variable_sources
    import variables as model
    here = here or project.current()
    domains = list_domains(here)
    out = []
    for fid in (data or {}).get("domains", {}):
        domain = next((d for d in domains if d.id == fid), None)
        if domain is None or domain.state == "unreadable":
            continue
        results = compute(domain, lambda c: resolve_import(here, c, domains, calculations=calculations))
        source = f"woodcore:{project.FORMULAS_FOLDER}/{domain.id}.typ"
        labels = {c.key: str(c.options.get("label") or "") for c in domain.commands if c.defines}
        variables = [model.Variable(key=key, domain=fid, value=value, unit=unit, symbol=symbol or key, label=labels.get(key, ""), source=source)
                     for key, symbol, value, unit in variables_of(domain, results)]
        out.append(variable_sources.Domain(name=fid, origin=ORIGIN, variables=variables, kind="named", label=domain.name))
    return out


# --- the Typst a report prints a domain with ---------------------------------------------------

def include_call(domain):
    """`#include "/Formules/<id>.typ"` -- what a section pastes to print the domain where it stands (issue #15, D-01): from the Typst root, where Formules/ lies."""
    return f'#include "/{project.FORMULAS_FOLDER}/{domain.id}.typ"'


# --- «Archives» in the tab's list: source_archive.Actions' backend for a domain ---------------------

class ArchiveBackend:
    """What `source_archive.Actions` archives, restores and purges with in the «Formules» tab (issue #15, ARCH-RISK-206): a domain is a `.typ`, moved as it is into Formules/archives/ and back under a free id, its `#var-domain` written with it -- and its place in the list and its folder, kept by `store` (a list_order.Store) under `key`, forgotten or given back with it. `here()` is the project. Qt-free, as the rest of this module."""

    PREFIX = "archive:"   # source_archive.KEY_PREFIX: the list's id of an archived entry

    def __init__(self, here, store=None, key="tab_formula"):
        self.here = here
        self.store = store
        self.key = key

    def present(self, _folder):
        return {d.id for d in list_domains(self.here())}

    def archive(self, _folder, fid):
        here = self.here()
        domain = next((d for d in list_domains(here) if d.id == fid), None)
        target = remove(here, domain) if domain is not None else None
        if self.store is not None:
            self.store.forget(self.key, [fid])
        return self.PREFIX + target.name if target is not None else None

    def restore(self, _folder, key, group=""):
        domain = restore(self.here(), key[len(self.PREFIX):] if key.startswith(self.PREFIX) else key)
        if self.store is not None and group:
            self.store.set_group(self.key, [domain.id], group)
        return domain.id

    def purge(self, _folder, key):
        purge(self.here(), key[len(self.PREFIX):] if key.startswith(self.PREFIX) else key)

    def entries(self, _folder, text=None):
        """The archived domains as the list shows them, newest first: {id, text, tooltip} -- the name, and in the tooltip the id it had and when it was archived."""
        rows = []
        for key, domain in archived(self.here()):
            stamp = re.match(r"(\d\d)(\d\d)(\d\d)-(\d\d)(\d\d)\d\d-", key)
            at = f"20{stamp.group(1)}-{stamp.group(2)}-{stamp.group(3)} {stamp.group(4)}:{stamp.group(5)}" if stamp else ""
            old = domain.declared or domain.id
            tooltip = (text("grp_archived_tip", "Ancien identifiant : {id} · archivé le {at}.\nGlisser dans un dossier pour le restaurer.") if text else "{id} {at}").format(id=old, at=at)
            rows.append({"id": self.PREFIX + key, "text": domain.name or old, "tooltip": tooltip})
        return rows
