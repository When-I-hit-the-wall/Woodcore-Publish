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

**`#domain` since the spec 2026-10-21-commandes-typst-refonte** (REQ-008, ARCH-005): the tab writes a domain `#domain("<id>", label: "<name>")[…]`, its `label:` the `title:` of the `#var-domain` it replaces; a file written with `#var-domain` is read as it always was and kept to its bytes while its header is not changed, and a `#var` with no value prints a variable again (REQ-002). The commands keep every fine argument they are written with -- `display`, `role`, the positions, `id` -- as options, read and written back unchanged.

**The id is the file's name** (issue #15, D-02, D-06): `#var-domain` is given it, so a value is read elsewhere with `#val(key, domain: "<id>")`, and the **name** the tab shows is the call's `title:`, which the report prints as a heading (D-10). A file whose `#var-domain` names another id than its own name -- copied, or renamed in the explorer -- is `misnamed`, and written back under its own name.

**Between the commands, Typst of the engineer's own** (REQ-006): a title, a sentence, a formula in mathematics -- one `text` item each run of it, written flush left and read back as it was typed. It is printed and never computed; what Typst would compute and Python could not -- a `#var`, `#eq`, `#var-unit` or `#verify` inside it -- is refused, as is a line of tags, and the body is read back in memory before anything is written (ARCH-RISK-108).

**One tag** around the one `#var-domain` call, read by `structure.pair_tags` -- the one reader of tags -- and the call by `typst_objects`'s parser with positional arguments allowed (D-20). Its state: `canonical` (it reads; since v0.119 a form of the engineer's own -- a call over two lines, a comment -- is no state, the tab writing back only the arguments it changed, ARCH-003), `misnamed` (it reads and declares another id than its file's name -- written back under its own after the tab says so), `unreadable` (it does not parse: shown read only, corrected in VS Code, and an export stops on it naming the file).

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
import build_reference as ref

TAG_TYPE = "formula-domain"
TAG_ID = "domain"
EXPORT_FILE = "formulas.json"
EXPORT_SCHEMA_VERSION = "2.0"   # 2.0 (issue #15): keyed by the id, the file's name, and carrying the title -- 1.0 was keyed by the name v0.117's retired #show-formula read
# The commands a domain holds, in the order the palette offers them (D-04); `domain` is the domain itself. `#val` and `#var-unit` were merged into `#var` (spec 2026-10-21-commandes-typst-refonte, REQ-009): a line that still writes one is the engineer's own text, which the export says (commands_migrate)
COMMANDS = ("var", "eq", "verify")
# The item a run of the engineer's own Typst between two commands is (REQ-006): printed, never computed
TEXT = "text"
# What Typst would compute and Python could not, were it written inside a text: refused there (ARCH-RISK-108)
COMPUTING = ("var", "eq", "verify")
DIGITS = 3   # the decimals the tab prints with -- the report's own default (calc-engine.typ's `number-digits`)
# A domain's first line is the engine imported from the Typst root, `/000-Typst-Config/commands.typ` in a project laid out by folders (calc/documents.py `root_import_line`, issue #64): the current project's, else the form every project laid out before writes (`_import_line`).

# What a domain's file is in, read (spec 2026-10-15, ARCH-006): it reads, it reads and declares another id than its file's name, it does not read. A form of the engineer's own is none of them -- the tab writes back only what it changed (ARCH-003)
STATES = ("canonical", "misnamed", "unreadable")


# Every code a DomainError is raised with -- here and in the modules beside this one (formula_infer, formula_args, formula_defaults) --, each a word of the window (calc/tools/formula_tab_words.py REFUSALS, issue #113 REQ-005)
CODES = ("archive_missing", "changed_on_disk", "defaults_option", "defaults_value", "formula", "id_invalid", "id_taken", "key_invalid", "key_taken", "missing",
         "name_empty", "name_line", "rename_failed", "text_command", "text_tag", "text_unbalanced", "unreadable", "value")


class DomainError(validation.ValidationError, ValueError):
    """A domain the tab cannot save as asked -- a name taken, a key used twice -- said in a sentence and a code the window translates (`code`, `args`). A ValidationError (v0.120, C7), so an export it stops says so as a defect of the input; still a ValueError for the callers that catch one."""

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
    # A command the engineer wrote inside a line (spec 2026-10-14-commandes-en-ligne-domaine, D-02): `glued_before`, it begins on the line the item before it ends on (`- $0°$: #var(…)`); `glued_after`, the item after it begins on its line (`#var(…) --- Auflast`). A write keeps it there. A text carries no flag of its own: the pane rebuilds texts from strings, a command keeps its identity
    glued_before: bool = False
    glued_after: bool = False
    # What the file held for this command when it was read (spec 2026-10-15, ARCH-006, D-17): its lines exactly as written -- arguments over several lines, a comment after the call --, and the call Woodcore would write for it then. A command the tab did not change is written back as `written`, byte for byte; only one it changed is written in Woodcore's form.
    written: str = ""
    read_call: str = ""

    @property
    def shown_symbol(self):
        return self.symbol or self.key

    @property
    def defines(self):
        """The registry key this command writes: a variable's, an equation's, a conversion's."""
        return self.key if self.kind in ("var", "eq") else None

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
    # `gen:` of an unfolded check (spec 2026-10-15, REQ-003): the form it was written from, (kind, form, version), or None for a domain written by hand
    gen: object = None
    # What the file held when it was read (ARCH-006): the `#var-domain(...)[` header as written and the one Woodcore would write, and the body's items as they were -- what lets a write leave everything it did not change as it stands
    header_written: str = ""
    header_call: str = ""
    read_items: tuple = ()
    body_read: str = ""
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


_SUBSCRIPT = re.compile(r"_\(([^()]*)\)")


def _tight(text):
    """A subscript's commas without the spaces after them (issue #113, REQ-002): `sigma_(m, d)` is typed for `sigma_(m,d)`."""
    return _SUBSCRIPT.sub(lambda m: "_(" + re.sub(r"\s*,\s*", ",", m.group(1)) + ")", text)


def _names(variables):
    """Every spelling a variable may be typed by -- its symbol, its key -- with the key it stands for, longest first."""
    out = {}
    for key, symbol in variables:
        for spelling in (_tight(symbol or ""), key):
            if spelling and spelling not in out:
                out[spelling] = key
    return sorted(out.items(), key=lambda item: -len(item[0]))


def typst_formula(text, variables):
    """A formula as the engineer types it -- the symbols the tab shows, numbers, a unit after a number, `12 N / 3000 mm` -- as `#eq` and `#verify` read it: each symbol written as its key, each number with a unit in parentheses and its unit in quotes (`(12 "N") / (3000 "mm")`), a decimal comma as a point, `×` as `*`. `variables` is [(key, symbol)] of what the domain declares above."""
    names = _names(variables)
    text = _tight(text)
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
            where = named.pop("domain")
            command.source = ("domain", where if isinstance(where, str) else tuple(where) if isinstance(where, list) else _literal(where))
            # a value written beside domain: is a literal checked by it (lib/formula.typ, spec 2026-10-15 REQ-001): the value is the one computed with
            if rest:
                if not isinstance(rest[0], (int, float)) or isinstance(rest[0], bool):
                    raise typst_objects.ParseError(f"#var({key!r}): beside domain: the value is a number")
                command.value = rest[0]
                if len(rest) > 1:
                    if not isinstance(rest[1], str):
                        raise typst_objects.ParseError(f"#var({key!r}): its unit is a string")
                    command.unit = rest[1]
                if len(rest) > 2:
                    raise typst_objects.ParseError(f"#var({key!r}) has more than a symbol, a value and a unit")
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
        elif not rest:
            # no value and no domain: the line prints a variable declared above it again (spec 2026-10-21-commandes-typst-refonte, REQ-002) -- `unit:`, if given, for that line alone
            command.source = ("again", None)
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
    else:
        raise typst_objects.ParseError(f"#{kind} is no command of a domain -- {', '.join(COMMANDS)}")
    # «Article» is `norm-section:` (issue #113, REQ-008): a file of before written with `norm-ref:` is read into it, and written so at the next write of the line -- never the two at once
    if "norm-ref" in named and "norm-section" not in named:
        named = {("norm-section" if name == "norm-ref" else name): value for name, value in named.items()}
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
            # the literal checked by domain: before the named arguments, where the value goes (REQ-001)
            literal = [c.value] + ([c.unit] if c.unit else []) if c.value is not None else []
            return ref.call_command("var", *head, *literal, **{"domain": list(where) if isinstance(where, tuple) else where, **options})
        if c.source and c.source[0] == "var-of":
            return ref.call_command("var", *head, ref.Raw(c.source[1]), *([c.unit] if c.unit else []), **options)
        if c.source and c.source[0] == "again":
            return ref.call_command("var", c.key, **options)
        return ref.call_command("var", *head, c.value, *([c.unit] if c.unit else []), **options)
    if c.kind == "eq":
        return ref.call_command("eq", c.key, *([c.symbol] if c.symbol else []), ref.Raw("`" + c.formula + "`"), **options)
    return ref.call_command("verify", ref.Raw("`" + c.formula + "`"), **options)


def header_of(domain):
    """`#domain("<id>", label: "<name>")[` -- the line a domain's body opens with (D-06, D-10; spec 2026-10-21-commandes-typst-refonte, REQ-008, ARCH-005: `#domain` replaces `#var-domain`, whose `title:` is its `label:`). A file that writes `#var-domain` keeps its header while the tab changes none of it (`body_of`), and an unfolded check's -- which carries its `gen:` (REQ-003) until its generator writes `#domain` (lot 8) -- is still written so."""
    label = f", label: {ref.typst_str(domain.name)}" if domain.name else ""
    return "#domain(" + ref.typst_str(domain.id) + label + ")["


def _signature(items):
    """What tells one list of items from another for a write: each item's kind, the text Woodcore would write for it, and for a command what it is glued to (D-02)."""
    return tuple(item_key(c) for c in items)


def body_of(domain):
    """The `#var-domain(…)[…]` call as the file writes it: one command a line, two spaces in; a text flush left, as it was typed (REQ-006) -- indenting it would change a raw block or a string it holds. A command glued to what is beside it (spec 2026-10-14-commandes-en-ligne-domaine, D-02) is written on that line, in Woodcore's form.

    **Only what changed is written in Woodcore's form** (spec 2026-10-15, ARCH-006, D-17, reversing the canonical rewrite of issue #15): a domain whose items and header are what the file held is its body as read, byte for byte; otherwise every command the tab did not change is written as it was written -- its arguments over several lines, a comment after it --, every text as typed, and the header as written unless it changed."""
    if domain.body_read and _signature(domain.commands) == domain.read_items and header_of(domain) == domain.header_call:
        return domain.body_read
    return "".join(("" if glued else "\n") + text for _index, text, glued in body_pieces(domain))[1:]


def body_pieces(domain):
    """The body as `body_of` writes it, piece by piece: (index of the item or None for the header and the closing `]`, its text, whether it is written on the line before it) -- what `formula_rows.item_lines` counts the lines of the file with (issue #113, ARCH-011), never guessed."""
    header = domain.header_written if domain.header_written and header_of(domain) == domain.header_call else header_of(domain)
    out = [(None, header, False)]
    prev = None
    for index, c in enumerate(domain.commands):
        if prev is not None and same_line(prev, c):
            out.append((index, c.raw if c.is_text else to_call(c), True))
        elif c.is_text:
            out.append((index, c.raw, False))
        elif c.written and to_call(c) == c.read_call:
            out.append((index, c.written, False))
        elif c.written:
            out.append((index, patched(c.written, c.read_call, to_call(c)), False))
        else:
            out.append((index, "  " + to_call(c), False))
        prev = c
    out.append((None, "]", False))
    return out


def same_line(prev, item):
    """Whether `item` is written on the line `prev` ends on (D-02): a command glued to what precedes it, or what follows a command glued to it."""
    return (not prev.is_text and prev.glued_after) or (not item.is_text and item.glued_before)


def _arguments(text, at):
    """{index or name: (where the argument starts, where its value starts, where it ends, its value's source)} of the call at `at` of `text`, and the index after its `)`."""
    parser = typst_objects._Parser(text)
    _call, end = parser.call(at, positional=True)
    return {key: (start, value, stop, text[value:stop]) for key, start, value, stop in parser.spans}, end


def _taken_away(written, mine, key):
    """The edits that take the named argument `key` out of the call as written: its line where it stands alone on one, else the argument with the comma after it, else -- the last one -- with the comma before it; a comment beside it stays. None where none of these holds."""
    start, _value, stop, _source = mine[key]
    j = stop
    while j < len(written) and written[j] in " \t":
        j += 1
    comma_after = j < len(written) and written[j] == ","
    end = j + 1 if comma_after else stop
    line_start = written.rfind("\n", 0, start) + 1
    line_end = written.find("\n", end)
    if not written[line_start:start].strip() and line_end >= 0 and not written[end:line_end].strip():
        return [(line_start, line_end + 1, "")]   # alone on its line: the line goes
    if comma_after:
        while end < len(written) and written[end] in " \t":
            end += 1
        return [(start, end, "")]
    previous = max((span[2] for span in mine.values() if span[2] <= start), default=None)
    comma = -1 if previous is None else written.find(",", previous, start)
    if comma < 0:
        return None
    if written[comma + 1:start].strip():
        return [(comma, comma + 1, ""), (start, stop, "")]   # a comment between the comma and the argument stays
    return [(comma, stop, "")]


def patched(written, was, now):
    """A command the tab changed, written over its lines as the engineer wrote them (spec 2026-10-15, ARCH-003): **only the arguments whose value changed are replaced**, an argument added written after the last one, one taken away removed with the comma before it -- every other byte kept, arguments over several lines and a comment after the call included. `was` is the call Woodcore would have written for the command as read, `now` the one it writes for it as it is. Where the number of positional arguments changes, or the result would not read back as `now`, the call alone is written in Woodcore's form, what stood before and after it on its lines kept."""
    at = written.index("#")
    try:
        before, _ = _arguments(was, 0)
        after, _ = _arguments(now, 0)
        mine, close = _arguments(written, at)
    except (typst_objects.ParseError, ValueError):
        return written
    whole = written[:at] + now + written[close:]
    positional = lambda args: sorted(k for k in args if isinstance(k, int))
    if positional(before) != positional(after) or positional(mine) != positional(after):
        return whole
    edits = []   # (start, end, new text), never overlapping: one per argument
    for key in after:
        value = after[key][3]
        if key in mine:
            if (before.get(key) or (0, 0, 0, None))[3] != value:
                edits.append((mine[key][1], mine[key][2], value))
        else:
            last = max(span[2] for span in mine.values())
            edits.append((last, last, f", {key}: {value}"))
    for key in before:
        if key not in after and key in mine and not isinstance(key, int):
            taken = _taken_away(written, mine, key)
            if taken is None:
                return whole
            edits.extend(taken)
    text = written
    for start, end, new in sorted(edits, key=lambda edit: (edit[0], edit[1]), reverse=True):
        text = text[:start] + new + text[end:]
    try:
        call, _ = typst_objects._Parser(text).call(at, positional=True)
        same = to_call(from_call(call)) == to_call(from_call(typst_objects._Parser(now).call(0, positional=True)[0]))
    except (typst_objects.ParseError, DomainError):
        same = False
    return text if same else whole


def file_text(domain, here=None):
    """A new domain's whole file: the import line -- project `here`'s, else the current project's (`_import_line`) -- and the `#var-domain` call -- no tag, the call being what Woodcore finds the domain by (ARCH-006)."""
    return "\n".join([_import_line(here), "", body_of(domain), ""])


def _import_line(here=None):
    """The engine imported from the Typst root, as project `here` -- else the current one, else none -- spells it (documents.root_import_line)."""
    import documents
    if here is None:
        try:
            here = project.current()
        except project.ProjectError:
            here = None
    return documents.root_import_line(here)


def _body_span(text):
    """(first line, line after the last) of the domain's `#var-domain(...)[...]` call, the lines as structure splits them, or a reason it cannot be found.

    **Found by the call, not by a tag** (spec 2026-10-15, ARCH-006, REQ-005): the one `#var-domain(` that stands at the top of the file's markup, read with typst_paths' lexer, to the `]` that closes it. The tag `// woodcore:object formula-domain domain` around it, which every domain carried until then, is neither needed nor in the way -- a file that still has it, or has lost one of its two lines, is read all the same, and the migration takes it away (calc/domains/unfold.py)."""
    norm = typst_objects._normalise(text)
    _top, hashes = _top_level_lines(norm)
    found = [j for j, name, _at_top in hashes if name in ("var-domain", "domain")]
    if len(found) != 1:
        return None, f"a domain's file holds one #var-domain(...)[...] call at its top level -- this one holds {len(found)}"
    j = found[0]
    if norm[norm.rfind("\n", 0, j) + 1:j].strip():
        return None, "#var-domain(...) stands at the start of its line"
    try:
        call, end = typst_objects._Parser(norm).call(j, positional=True)
    except typst_objects.ParseError as exc:
        return None, f"#var-domain(...) cannot be read: {exc}"
    eol = norm.find("\n", end)
    eol = len(norm) if eol < 0 else eol
    rest = norm[end:eol].strip()
    if rest and not rest.startswith("//"):
        return None, f"#var-domain(...)[...] is followed on its last line by {rest!r}"
    return (norm.count("\n", 0, j), norm.count("\n", 0, end) + 1), ""


def parse_body(body):
    """(declared name, title, items) of a `#var-domain("…", title: "…")[…]` body -- the commands and, between them, the runs of the engineer's own Typst (`text` items). Raises typst_objects.ParseError."""
    declared, title, items, _gen, _header = parse_domain(body)
    return declared, title, items


def parse_domain(body):
    """`parse_body`, and the `gen:` of an unfolded check (None for a domain written by hand) and the header as it is written, `#var-domain(...)[` to its bracket."""
    text = typst_objects._normalise(body)
    parser = typst_objects._Parser(text)
    start = parser.ws(0)
    if start >= parser.n:
        parser.fail("the domain holds no #var-domain call", start)
    call, end = parser.call(start, positional=True)
    if parser.ws(end) < parser.n:
        parser.fail("a domain's block holds its #var-domain call and nothing after it", parser.ws(end))
    # `#domain(id, label:, …)` since the spec 2026-10-21-commandes-typst-refonte (REQ-008), `#var-domain(id, title:, gen:)` before it: both read, the label the domain's name
    allowed = {"var-domain": {"title", "gen"}, "domain": {"label", "label-position", "descr", "descr-position", "norm", "norm-section", "norm-position", "level"}}
    title = call.args.get("title" if call.type == "var-domain" else "label", "") if call.type in allowed else None
    if (call.type not in allowed or len(call.positional) != 1 or not isinstance(call.positional[0], str)
            or set(call.args) - allowed[call.type] or not isinstance(title, str)):
        parser.fail('a domain is written #domain("its id", label: "its name")[…]', start)
    if call.body is None:
        parser.fail("#var-domain has no content block", end)
    gen = call.args.get("gen")
    if gen is not None and not (isinstance(gen, dict) and set(gen) == {"kind", "form", "version"}
                                and isinstance(gen["kind"], str) and isinstance(gen["form"], str) and isinstance(gen["version"], int)):
        parser.fail('gen: is (kind: "tension", form: "(6)", version: 1), written by Woodcore when it unfolds a check', start)
    # the header as written: the text before the content block's own markup and its `[`
    closing = text.rstrip()
    header = closing[start:len(closing) - 1 - len(call.body.markup) - 1] + "["
    return call.positional[0], title, split_items(call.body.markup), gen, header


# A line that opens with one of the domain's commands: a command, where it stands alone on its line at the top of the body
_COMMAND_LINE = re.compile(r"[ \t]*#(" + "|".join(sorted((re.escape(c) for c in COMMANDS), key=len, reverse=True)) + r")\(")


def _top_level_lines(markup):
    """The offsets of the lines of `markup` that begin in its own markup -- not inside a raw block, a comment, a string, an equation or a call --, read with typst_paths' lexer, the one that walks Typst's modes (ARCH-RISK-108: never a regex on `#var(`). Also every `#name` the lexer met, as (offset, name, top): `top` where it stands in the body's own markup, outside any content block, call or equation -- where `split_items` may cut a command out of a line (D-02) --, every one of them what `check_text` refuses."""
    import typst_paths
    starts = [0] + [i + 1 for i, c in enumerate(markup) if c == "\n"]
    top, hashes = set(), []
    lexer = typst_paths._Lexer(markup)
    original = lexer._hash

    def hashed(j):
        found = typst_paths._IDENT.match(markup, j + 1)
        if found is not None:
            frame = lexer.stack[-1]
            hashes.append((j, found.group(), len(lexer.stack) == 1 and frame[0] == "markup" and frame[2] == 0))
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
    """The offsets of the lines of `markup` that begin in its own markup -- not inside a raw block, a comment, a string, an equation or a call -- read with typst_paths' lexer (ARCH-RISK-108), as a sorted list: where a command may stand on a line of its own without changing what the text around it means. The public face of `_top_level_lines` (issue #40, ARCH-004), which the pills' layout read to refuse a drop until issue #113 took the pills away."""
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
        # a side glued to a command (D-02) is part of the command's line: kept as typed -- a space between two commands with it
        glued_head = i > 0 and out[i - 1].glued_after
        glued_tail = i < len(out) - 1 and out[i + 1].glued_before
        if (glued_head or glued_tail) and c.raw == "":
            continue   # nothing between a command and what it is glued to
        head = not glued_head and bool(lines) and not lines[0].strip()
        while not glued_head and len(lines) > glued_tail and not lines[0].strip():
            lines.pop(0)
        tail = not glued_tail and bool(lines) and not lines[-1].strip()
        while not glued_tail and len(lines) > glued_head and not lines[-1].strip():
            lines.pop()
        before, after = i > 0, i < len(out) - 1   # a command on that side: the text stands between the two
        if not lines:
            if before and after:
                tidy.append(Command(TEXT, raw=""))
            continue
        tidy.append(Command(TEXT, raw="\n".join(([""] if head and before else []) + lines + ([""] if tail and after else []))))
    return _settle_glue(tidy)


def _settle_glue(items):
    """The items with the flags of their glued commands (D-02) saying what the file will hold once written, so that it reads back to the same items: a run of blanks on one line beside a command is a space only between two commands glued to it, and goes otherwise, with the glue; a command is glued to no text that begins (ends) with a line break, nor to the edge of the body; two commands glued on either side share their line. The flags are changed in place -- the tab knows a command by its identity."""
    out = []
    for k, c in enumerate(items):
        prev = items[k - 1] if k > 0 else None
        nxt = items[k + 1] if k + 1 < len(items) else None
        glued = (prev is not None and not prev.is_text and prev.glued_after) or (nxt is not None and not nxt.is_text and nxt.glued_before)
        if c.is_text and glued and "\n" not in c.raw and not c.raw.strip():
            if not (prev is not None and prev.glued_after and nxt is not None and nxt.glued_before):
                if prev is not None:
                    prev.glued_after = False
                if nxt is not None:
                    nxt.glued_before = False
                continue
        out.append(c)
    for k, c in enumerate(out):
        if c.is_text:
            continue
        prev = out[k - 1] if k > 0 else None
        nxt = out[k + 1] if k + 1 < len(out) else None
        if prev is None or (prev.is_text and "\n" in prev.raw and not prev.raw.split("\n")[-1].strip()):
            c.glued_before = False
        if nxt is None or (nxt.is_text and "\n" in nxt.raw and not nxt.raw.split("\n")[0].strip()):
            c.glued_after = False
        if nxt is not None and not nxt.is_text and (c.glued_after or nxt.glued_before):
            c.glued_after = nxt.glued_before = True
    return out


def split_items(markup):
    """The items of a domain's body: each command that stands alone on its line(s) at the top of the body, each computing command written inside a line of the body's own markup -- `- $0°$: #var(…)`, `#var(…) --- Auflast`, glued to what is beside it (spec 2026-10-14-commandes-en-ligne-domaine, D-02; until then refused, `text_trailing`) --, and each run of text between two of them as one `text` item, kept as typed -- one blank line beside a command kept as the paragraph it is, an empty text between two commands (`tidy_items`, issue #40, D-05: until then every blank line beside a command was left out, and two paragraphs ran into one). Raises typst_objects.ParseError where a command cannot be read."""
    markup = typst_objects._normalise(markup)
    top, hashes = _top_level_lines(markup)
    inline = [j for j, name, at_top in hashes if at_top and name in COMPUTING]
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
                command = from_call(call)
                # its lines as written, a comment after the call included, kept with it (ARCH-006): what it is written back as while the tab does not change it
                command.written = markup[i:after]
                command.read_call = to_call(command)
                items.append(command)
                i = after + 1
                continue
        i = _split_line(markup, i, eol, [j for j in inline if i <= j < eol], sub, items, pending, flush)
    flush()
    return tidy_items(items)


def _split_line(markup, i, eol, cuts, sub, items, pending, flush):
    """The line that begins at `i` read into `items` and `pending`: each computing command whose `#` is in `cuts` a command glued to what is beside it on the line (D-02), the rest text as typed. A call Typst carries on into what follows it (`#var(…)[…]`, `#var(…).x`, `#var(…)(…)`) is left in the text, which `check_text` refuses. Returns where the next line begins -- after the line a call written over several lines ends on."""
    n, pos, cut = len(markup), i, False
    for j in cuts:
        if j < pos:
            continue
        call, end = sub.call(j, positional=True)
        if call.body is not None or markup[end:end + 1] in ("(", "[") or re.match(r"\.[A-Za-z_]", markup[end:end + 2]):
            continue
        before = markup[pos:j]
        if before.strip() or (cut and before):   # the indentation before a command that opens its line is no text, as for one alone on it
            pending.append(before)
        flush()
        command = from_call(call)
        command.glued_before = bool(markup[i:j].strip())
        items.append(command)
        if end > eol:
            eol = markup.find("\n", end)
            eol = n if eol < 0 else eol
        rest = markup[end:eol].strip()
        if not rest or rest.startswith("//"):
            if rest:   # a comment after it: on a line of its own, as after a call alone on its line
                pending.append(rest)
            return eol + 1
        command.glued_after = True
        pos, cut = end, True
    pending.append(markup[pos:eol])
    return eol + 1


def check_text(raw):
    """Refuses what a text between two commands may not hold (ARCH-RISK-108), with its reason: a command Typst would compute and Python would not (`#var`, `#eq`, `#var-unit`, `#verify`), a line of Woodcore's tags, which the file's own reader would take for its own. Raises DomainError `text`."""
    for line in typst_objects._normalise(raw).split("\n"):
        if line.strip().startswith("// woodcore:"):
            raise DomainError("text_tag", f"a text of the domain holds a line of Woodcore's tags: {line.strip()!r}", line=line.strip())
    text = typst_objects._normalise(raw)
    _top, hashes = _top_level_lines(text)
    for j, name, _at_top in hashes:
        if name in COMPUTING:
            # since spec 2026-10-14-commandes-en-ligne-domaine a computing command in the body's own markup is a command wherever it stands on its line (`text_trailing` retired): what reaches here sits in a content block, a call, an equation, or carries on into what follows it
            start = text.rfind("\n", 0, j) + 1
            eol = text.find("\n", j)
            eol = len(text) if eol < 0 else eol
            line = text[start:eol].strip()
            raise DomainError("text_command", f"a text of the domain holds #{name} ({line!r}): write it as a block of its own, which Woodcore computes -- in a text the report would compute it and Woodcore would not", command=name, line=line)


def read(path):
    """The domain one file holds. A file that cannot be read is a Domain all the same, `unreadable`, its reason in `problem` -- the tab shows it read only."""
    path = Path(path)
    with open(path, encoding="utf-8", newline="") as file:
        text = file.read()   # the text as it is, its line endings with it: a write keeps them
    return parse_text(text, path)


def parse_text(text, path):
    """`read` on a text rather than a file (issue #113, ARCH-016): what the «Code» mode reads its buffer with before anything is written -- the domain of `path` as `text` would make it."""
    path = Path(path)
    domain = Domain(id=path.stem, name="", path=path, text=text)
    span, why = _body_span(text)
    if span is None:
        domain.state, domain.problem = "unreadable", why
        return domain
    lines = structure._split(text)
    body = "".join(lines[span[0]:span[1]])
    try:
        domain.declared, domain.name, domain.commands, domain.gen, domain.header_written = parse_domain(body)
        for c in domain.commands:
            if c.is_text:
                check_text(c.raw)
    except typst_objects.ParseError as exc:
        domain.state, domain.problem = "unreadable", str(exc)
        return domain
    except DomainError as exc:   # a computing command inside a text: Typst and Python would disagree on what it gives
        domain.state, domain.problem = "unreadable", str(exc)
        return domain
    # what was read, so that a write changes what the tab changed and nothing else (ARCH-006, D-17): a form of the engineer's own -- arguments over several lines, a comment, a blank line -- is no longer a state to rewrite
    domain.read_items = _signature(domain.commands)
    domain.header_call = header_of(replace(domain, id=domain.declared))
    domain.body_read = typst_objects._normalise(body).rstrip("\n")
    if domain.declared != domain.id:
        domain.state = "misnamed"   # another id than its file's name -- copied, renamed outside -- is written back under its own
    return domain


def item_key(c):
    """What an item is, to compare two lists of them: its kind, its text or its call, and for a command what it is glued to (D-02)."""
    return (c.kind, c.raw) if c.is_text else (c.kind, to_call(c), c.glued_before, c.glued_after)


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
    if [item_key(c) for c in back] != [item_key(c) for c in items]:
        raise DomainError("text_unbalanced", "the domain would not read back once written as it is now -- a text holds what reads as a command, or the brackets of a text do not balance")
    return items


def write_text(domain):
    """The file's text with the domain's body written in Woodcore's form between its two tags and **nothing else changed** (every byte outside the body kept, the file's own line endings) -- or a new file's whole text."""
    domain = replace(domain, commands=check_body(domain))
    if domain.text is None:
        return file_text(domain)
    span, why = _body_span(domain.text)
    if span is None:
        raise DomainError("unreadable", f"{domain.path.name if domain.path else domain.id}: its #var-domain call cannot be found ({why}) -- correct it in VS Code", file=domain.id, reason=why)
    lines = structure._split(domain.text)
    newline = "\r\n" if lines and lines[0].endswith("\r\n") else "\n"
    body = body_of(domain).replace("\n", newline) + newline
    return "".join(lines[:span[0]]) + body + "".join(lines[span[1]:])


# --- the project's domains ----------------------------------------------------------------------

def list_domains(here=None):
    """Every domain of the project, by file name: the engineer's own, `<Typst root>/Domains/*.typ` (`Formules/` in a project laid out before), and in a project laid out by folders every domain a specialised tab's folder holds written out whole -- a member check unfolded, `Timber-checks/Tension/<id>.typ` (issue #64, REQ-016). A stub there (domains/domain_file.py), which prints its domain by one call and holds no `#var-domain`, is no domain of this tab and is not read (spec 2026-10-15 ARCH-RISK-B02)."""
    here = here or project.current()
    folder = here.formulas_dir
    found = [read(path) for path in sorted(folder.glob("*.typ"))] if folder.is_dir() else []
    for path in specialised_files(here):
        if any(call in path.read_text(encoding="utf-8", errors="replace") for call in _VAR_DOMAIN):
            found.append(read(path))
    return found


# What a file written out whole holds and a stub does not: a domain's `#var-domain` call.
_VAR_DOMAIN = ("#var-domain(", "#domain(")


def specialised_files(here):
    """Every `.typ` at the top of a specialised tab's domain folder -- a stub or a domain written out whole -- in a project laid out by folders, archives aside; [] before."""
    out = []
    for kind in project.DOMAIN_FOLDERS:
        for sub in (list(project.KIND_FOLDERS.get(kind, {})) or [None]):
            folder = here.domain_dir(kind, sub)
            if folder is not None and folder.is_dir():
                out += sorted(folder.glob("*.typ"))
    return out


def group_of(here, domain):
    """The group the «Domaines» tab shows `domain` in (REQ-016): None for the engineer's own -- Domains/ --, else (kind, sub) of the folder of the specialised tab it lies in: ("check", "tension") for `Timber-checks/Tension/<id>.typ`."""
    if domain.path is None or domain.path.parent.resolve() == here.formulas_dir.resolve():
        return None
    for kind in project.DOMAIN_FOLDERS:
        for sub in (list(project.KIND_FOLDERS.get(kind, {})) or [None]):
            folder = here.domain_dir(kind, sub)
            if folder is not None and domain.path.parent.resolve() == folder.resolve():
                return (kind, sub)
    return None


def _taken(here, fid):
    """Whether a file of a domain bears `fid` already: in Domains/ or, laid out by folders, in a specialised tab's folder -- a domain's id is its `#var-domain`'s and `#val(domain:)`'s, one for the whole project (spec 2026-10-15 ARCH-RISK-B04)."""
    if (here.formulas_dir / f"{fid}.typ").exists():
        return True
    return any(path.stem == fid for path in specialised_files(here))


def slug(name):
    """A file id for a domain named `name`: lower case, digits and hyphens (structure.ID_PATTERN's alphabet), accents dropped."""
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    out = re.sub(r"[^a-z0-9]+", "-", plain).strip("-")
    return out if out and out[0].isalpha() else ("d-" + out if out else "domaine")


def free_id(here, base, taken=()):
    """`base`, or `base-2`, `base-3`…, the first no domain and no file of a domain bears (`_taken`)."""
    fid, n = base, 1
    while fid in taken or _taken(here, fid):
        n += 1
        fid = f"{base}-{n}"
    return fid


def new_domain(here, name, domains=None, defaults=True):
    """A domain not yet written, its id made from its name and free in the folder -- made again from the name at its first write, until the engineer types an id of his own (REQ-004). With `defaults`, it opens on `#calc-defaults(presets: "block", scope: "domain")` (issue #113, REQ-004, D-3: printed one line a value); a domain already written keeps what it has."""
    domains = list_domains(here) if domains is None else domains
    check_name(name)
    fid = free_id(here, slug(name), {d.id for d in domains})
    from domains import formula_defaults
    commands = [Command(TEXT, raw=formula_defaults.NEW_LINE)] if defaults else []
    return Domain(id=fid, name=name, path=here.formulas_dir / f"{fid}.typ", commands=commands)


def check_name(name):
    """A domain's name is its title, free text on one line -- two domains may bear the same, the id telling them apart (D-06)."""
    if not name or not name.strip():
        raise DomainError("name_empty", "a domain needs a name")
    if "\n" in name or "\r" in name:
        raise DomainError("name_line", "a domain's name is one line", name=name)


# The id of a member check (calc/domains/member_check.py), which an unfolded check's domain keeps as it is (spec 2026-10-15, D-14): `ZT-01` names the check, its file and its `#var-domain` alike
CHECK_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$")


def check_id(fid, domains, own=None, here=None, unfolded=False):
    """An id a domain may take: lower-case letters, digits and hyphens (structure.ID_PATTERN, the file's name) -- or, for an unfolded check (`unfolded`), its check's id as it is (D-14) --, and no other domain's -- nor another file's of Formules/. Raises DomainError `id_invalid` or `id_taken`."""
    if not fid or not (CHECK_ID if unfolded else structure.ID_PATTERN).match(fid):
        raise DomainError("id_invalid", f"{fid!r} is no id: lower-case letters, digits and hyphens, starting with a letter", id=fid)
    taken = {d.id for d in domains if d.id != own}
    if fid in taken or (here is not None and fid != own and _taken(here, fid)):
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
    patterns = (f'"{here.from_root(here.formulas_dir / f"{fid}.typ")}"', f'domain: "{fid}"', f'domain:"{fid}"')
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
    target = (domain.path.parent if domain.path is not None else here.formulas_dir) / f"{new_id}.typ"   # in its own folder: Domains/, or a specialised tab's for a domain written there
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
        raise DomainError("archive_missing", f"{key} is no longer in {here.rel(here.formulas_dir / ARCHIVES)}/", key=key)
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
        rel = here.rel(domain.path)
        if domain.state == "unreadable":
            raise validation.ValidationError(f"{rel}: the calculation domain cannot be read -- {domain.problem}. Correct it in VS Code or in Woodcore's «Domaines» tab")
        if domain.declared in files:
            raise validation.ValidationError(f"{rel} and {files[domain.declared]} both declare #var-domain({domain.declared!r}) -- give one of the two its own id")
        files[domain.declared] = rel
        if domain.state == "misnamed":
            notes.append(engine.Note("formula_misnamed", f"{rel}: the domain declares #var-domain({domain.declared!r}) and its file is named {domain.id!r} -- it is exported as it stands, and the «Domaines» tab writes its own id back at the next save", file=rel, domain=domain.id))
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
    # issue #113 (ARCH-012): the refusal's code and values (units.CODES), the keys the line reads (`uses`, what the linked hovers light), the index of the line whose fault this one only inherits (`blocked_by`: said once, REQ-006 -- `error` stays, so every reader still sees a line that gives nothing), and for a variable linked from elsewhere its symbol, label and origin (REQ-010)
    code: str = ""
    values: dict = field(default_factory=dict)
    uses: tuple = ()
    blocked_by: object = None
    symbol: str = ""
    label: str = ""
    origin: object = None


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


def compute(domain, resolve=None, digits=DIGITS, describe=None):
    """What every command of `domain` gives, in order: [Result]. A command the report would refuse is a Result with its `error` -- the reason the compile would stop on -- and the commands after it go on, a name it would have defined being then unknown to them: such a line, whose only unknown names are keys a line above failed to define, is `blocked_by` that line (issue #113, REQ-006: a fault said once). `resolve(command)` gives a variable taken from elsewhere its (value, unit), or None where it cannot be found (REQ-015); `describe(command)`, where given, its {symbol, label, origin} (formula_links.linked_info, REQ-010)."""
    values, symbols, out = {}, {}, []
    broken = {}   # key -> the index of the line at the root of its failure
    for index, c in enumerate(domain.commands):
        r = Result()
        if c.is_text:      # printed, never computed: an empty result keeps every list aligned with the items (ARCH-RISK-108)
            out.append(r)
            continue
        if c.kind == "var":
            r.uses = (c.key,) if c.source and c.source[0] == "again" else ()
        else:
            src = units.star_as_dot(c.formula)
            known = units.operands_of(src, values)
            r.uses = tuple(known) + tuple(n for n in units.unknown_names(src, known) if n in broken)
        if c.kind == "var" and c.source and c.source[0] == "domain" and describe is not None:
            info = describe(c) or {}
            r.symbol, r.label, r.origin = info.get("symbol", ""), info.get("label", ""), info.get("origin")
        try:
            if c.kind == "var" and c.source and c.source[0] == "again":
                # a variable printed again (REQ-002): the value it holds, shown in `unit:` for this line alone -- the registry keeps its own (Q-011)
                if c.key not in values:
                    raise units.FormulaError(f"var: no variable named {c.key!r} here -- declared here: {', '.join(values) or 'none'}", "again", key=c.key, declared=tuple(values))
                value, unit = values[c.key]
                shown_unit = c.options.get("unit")
                if isinstance(shown_unit, str) and shown_unit:
                    q = units.quantity(float(value), unit)
                    new = units.written_unit(shown_unit)
                    parsed = units.parse_unit(new)
                    if parsed is None or q is None or not units.dims_equal(q.dims, parsed[1]):
                        raise units.FormulaError(f"var: {c.key!r} is in {unit}, which cannot be shown in {shown_unit}", "shown_unit", key=c.key, unit=unit, wanted=shown_unit)
                    value, unit = q.base / parsed[0], new
                r.value, r.unit = value, unit
            elif c.kind == "var":
                if c.source and c.value is not None:
                    # a literal checked by domain: is computed with as written, as Typst does (REQ-001); whether it is stale is Typst's to say (unfold.query_state)
                    value, unit = c.value, units.written_unit(c.unit or "")
                elif c.source:
                    got = resolve(c) if resolve else None
                    if got is None:
                        raise units.FormulaError(f"var: {c.key!r} is taken from {describe_source(c)}, which gives no value here", "no_value", key=c.key, source=describe_source(c))
                    value, unit = got
                    unit = c.unit or unit
                else:
                    value, unit = c.value, units.written_unit(c.unit or "")
                if isinstance(value, (int, float)) and units.parse_unit(unit) is None:
                    raise units.FormulaError(f"var: cannot read the unit {unit!r} of {c.key!r} -- write it as the report writes one, `kN`, `N/mm²`, `kNm`", "unit_read", unit=unit, symbol=c.key)
                values[c.key] = (value, unit)
                symbols[c.key] = c.symbol or r.symbol
                r.value, r.unit = value, unit
            elif c.kind == "eq":
                q, operands = units.evaluate("eq", c.formula, values)
                symbol = c.symbol or c.key
                value, unit, warning = units.present("eq", symbol, q, units.written_unit(c.unit) or None)
                as_unit = c.options.get("as-unit")
                if isinstance(as_unit, str) and as_unit:
                    # the answer given another unit without converting it (spec 2026-10-21-commandes-typst-refonte, REQ-003): its number kept, and said in the window and not in the report (Q-004)
                    warning = {"as_unit": True, "wanted": units.written_unit(as_unit), "natural": unit}
                    unit = units.written_unit(as_unit)
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
                    raise units.FormulaError(f"verify: comparing {units.dims_text(lq.dims)} with {units.dims_text(rq.dims)} -- the two sides of a relation must have the same dimensions", "vdims", a=units.dims_text(lq.dims), b=units.dims_text(rq.dims))
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
        except units.FormulaError as exc:
            r.error, r.code, r.values = str(exc), exc.code, dict(exc.values)
            names = exc.values.get("names") or ((c.key,) if exc.code == "again" else ())
            if exc.code in ("unknown", "again") and names and all(n in broken for n in names):
                r.blocked_by = broken[names[0]]
            if c.defines:
                broken[c.key] = r.blocked_by if r.blocked_by is not None else index
        else:
            if c.defines:
                broken.pop(c.key, None)   # defined again: no longer broken below
        out.append(r)
    return out


def variables_of(domain, results=None):
    """[(key, symbol, value, unit)] of what the domain defines, in order -- the list at the top of the tab's right pane (T23); a key redefined by a conversion keeps its place."""
    results = results if results is not None else compute(domain)
    out, index = [], {}
    for c, r in zip(domain.commands, results):
        if c.defines and not r.error:
            row = (c.key, c.symbol or r.symbol, r.value, r.unit)
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


def reference(command):
    """What a command takes from elsewhere, (domain, instance, name): a value of the export -- `var-of("snow-load", "SL", "s_k")`, `domain:` a pair -- or, `instance` None, a variable of another domain of the project named by its id; None where the command takes nothing, or names it in a way that is not read here. The one reading of a command's source, for `resolve_import` and for the graph of dependencies (spec 2026-10-21-graphe-dependances, ARCH-RISK-1103)."""
    if not command.source:
        return None
    kind, where = command.source
    if kind == "var-of":
        found = _VAR_OF.match(where)
        return (found.group(1), found.group(2), found.group(3)) if found else None
    if isinstance(where, tuple) and len(where) == 2:
        return where[0], where[1], command.key
    if isinstance(where, str):
        return where, None, command.key
    return None


def resolve_import(here, command, domains=(), _stack=(), calculations=None):
    """The (value, unit) a variable taken from elsewhere has now, or None where it cannot be read here: a value of the export (`var-of(calc, instance, name)`, or `domain:` a pair), read off `data/calculations.json`; a variable of another of the project's domains (`domain:` a name), computed now -- a cycle between domains is refused, naming it. A domain of a document's own sections is compiled, never computed here: it gives None, and the tab says the value is read when the document is."""
    found = reference(command)
    if found is None:
        return None
    pair = (found[0], found[1]) if found[1] is not None else None
    name = found[2]
    where = found[0]
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
            raise units.FormulaError(f"var: {CIRCLE} -- " + " → ".join(list(_stack) + [other.id]), "circle", path=" → ".join(list(_stack) + [other.id]))
        results = compute(other, lambda c: resolve_import(here, c, domains, _stack + (other.id,), calculations))
        for c, r in reversed(list(zip(other.commands, results))):
            if c.defines == name:
                if CIRCLE in r.error:
                    raise units.FormulaError(r.error, r.code or "formula", **r.values)   # said where it was asked for, not lost as «gives no value»
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

def include_call(domain, here=None):
    """`#include "/Domains/<id>.typ"` -- what a section pastes to print the domain where it stands (issue #15, D-01): its file from the Typst root, wherever it lies -- Domains/, a specialised tab's folder for a domain written there (issue #64), Formules/ in a project laid out before. `here` is the project, the current one where none is given."""
    here = here or project.current()
    path = domain.path if domain.path is not None else here.formulas_dir / f"{domain.id}.typ"
    return f'#include "{here.from_root(path)}"'


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
