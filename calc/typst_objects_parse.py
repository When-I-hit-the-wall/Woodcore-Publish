"""Typst values as Woodcore reads and writes them in a parametric object's call -- a length, content, an expression, a call and its arguments, parsed and serialised back -- and the signatures of the commands an object may be: split out of calc/typst_objects.py (issue #30), moved verbatim. typst_objects.py imports every name back.
"""

import copy
import math
import re
from dataclasses import dataclass, field
import typst_paths


# The parameters of the one command of lib/document.typ left -- the list of the norms; its parametric objects were written in raw Typst since the spec 2026-10-21-commandes-typst-refonte (REQ-019) -- as its signature writes them: the order is the canonical order of the arguments, and the default is what an argument left out means. tests/test_typst_objects.py holds this table equal to the file's own signatures.
SIGNATURES = {
    "show-norm-list": "keys: (), project: none, level: auto",
}


# The parameters of the six commands of lib/sheet.typ (v0.114), the objects of an export sheet (`Plans/<id>.typ`, calc/sheets.py) -- held equal to that file's signatures by tests/test_typst_objects.py, as the table above is to lib/document.typ's. `sheet-page` is the sheet's show rule, `sheet`, whose first parameter is the document it is handed (SHOW_RULES).
SHEET_SIGNATURES = {
    "sheet-page": 'format: "A3", landscape: true, margin: 10mm, kind: "position"',
    "sheet-text": 'x: 0mm, y: 0mm, body: none, size: 10pt, weight: "regular", width: auto',
    "sheet-viewport": "plan: none, x: 0mm, y: 0mm, scale: none, width: none, highlight: none, axes: true, dimensions: true, lengths: auto, centres: auto, scale-bar: false, caption: none, title: auto, level: auto",
    "sheet-section": "plan: none, storey: none, x: 0mm, y: 0mm, scale: none, width: none, title: auto",
    "sheet-legend": "plans: auto, x: 0mm, y: 0mm, width: 120mm, title: auto, level: auto",
    "sheet-fire-viewport": "plan: none, x: 0mm, y: 0mm, scale: none, width: none, legend: auto, scale-bar: false, caption: none, title: auto, level: auto",
    "sheet-fire-legend": "plans: auto, x: 0mm, y: 0mm, width: 120mm, title: auto, level: auto",
    # the list of the positions on a sheet (v0.116, lib/sheet.typ's sheet-position-list)
    "sheet-position-list": 'plans: auto, scope: "plans", storey: none, x: 0mm, y: 0mm, width: 180mm, title: auto, level: auto',
    # the quantities on a sheet (issue #9, lib/sheet.typ's sheet-quantities)
    "sheet-quantities": 'plans: auto, scope: "plans", positions: (), x: 0mm, y: 0mm, width: 150mm, title: auto, level: auto',
    "sheet-titleblock": "x: auto, y: auto, width: auto, logo: auto, object: auto, element: none, client: auto, architect: none, phase: none, project-number: auto, plan-number: none, index: auto, revision-date: auto, revision-author: auto, modification: auto, drawn-by: auto, date: auto, scale: auto, size: auto",
}


SIGNATURES.update(SHEET_SIGNATURES)


# An object written as a show rule rather than a call: `sheet-page` is `#show: sheet.with(format: "A3", ...)` in the file -- the one line that can set a page -- and a Call of type `sheet-page` here. `_as_call` and `serialize` turn the one into the other, so everything else of this module reads it as any call.
SHOW_RULES = {"sheet-page": "sheet"}


# The calls a `woodcore:object` tag may name, and the two objects that are markup and not a call: a heading and a paragraph. CALL_TYPES are a document's calls (lib/document.typ), SHEET_TYPES a sheet's (lib/sheet.typ, v0.114); DOCUMENT_TYPES what a document's section holds, the kinds the «Structure du document» tab edits. OBJECT_TYPES is structure.OBJECT_TYPES', in the same order.
CALL_TYPES = tuple(k for k in SIGNATURES if k not in SHEET_SIGNATURES)


# a table written in raw Typst too (spec 2026-10-21-commandes-typst-refonte, ARCH-004): its body is the `#table(…)` as written, read by calc/typst_raw_table.py and rewritten by span
MARKUP_TYPES = ("heading", "text", "table")


SHEET_TYPES = tuple(SHEET_SIGNATURES)


# What a line of the canonical form may hold before an array of plain values is written one element per line.
LINE_WIDTH = 100


# The arguments whose elements are entries read one by one -- a column, a row, an option, a document named, a line of the small print -- written one element per line whatever their length, so that an entry added or taken out is a line of the diff. Any other array -- the ids of `hidden`, the positions of `highlight` -- is written inline where its line fits in LINE_WIDTH.
LIST_ARGUMENTS = ("columns", "rows", "options", "keys", "notes")


# The mark a text still to be written carries, «[…]» (lib/document.typ's doc-placeholder), as the markup of a content block.
PLACEHOLDER = "[" + chr(0x2026) + "]"


class _Auto:
    """Typst's `auto`: one value, compared by identity."""
    _one = None

    def __new__(cls):
        if cls._one is None:
            cls._one = super().__new__(cls)
        return cls._one

    def __repr__(self):
        return "AUTO"

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

    def __reduce__(self):
        return (_Auto, ())


AUTO = _Auto()


UNITS = ("pt", "mm", "cm", "in", "em", "fr", "deg", "rad", "%")


def _normalise(text):
    """`text` with every line ending made `\\n`: what the canonical form is compared in and written from."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


@dataclass(frozen=True)
class Length:
    """A length, a ratio, a fraction or an angle as Typst writes it: a number and its unit, `80%`, `12pt`, `1.5cm`, `2fr`, `90deg`. `value` keeps whether the number was written as an integer or a float, `12pt` and `12.0pt` being two spellings."""
    value: object
    unit: str

    def __post_init__(self):
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
            raise ValueError(f"a length's value is a number -- got {self.value!r}")
        if isinstance(self.value, float) and not math.isfinite(self.value):
            raise ValueError(f"a length's value is a finite number -- got {self.value!r}")
        if self.unit not in UNITS:
            raise ValueError(f"{self.unit!r} is not a unit of Typst -- expected one of {', '.join(UNITS)}")


@dataclass(frozen=True)
class Content:
    """Content, `[...]`: the markup between the brackets, kept as it is written and never looked into. Checked on creation: the markup must close where it ends -- its brackets balanced, no comment or escape swallowing the closing one -- or the call it is written into would not end where it should. Line endings are normalised to `\\n`."""
    markup: str

    def __post_init__(self):
        if not isinstance(self.markup, str):
            raise ValueError(f"content is markup, a string -- got {self.markup!r}")
        markup = _normalise(self.markup)
        object.__setattr__(self, "markup", markup)
        text = "[" + markup + "]"
        try:
            end = _Parser(text).content_end(0)
        except ParseError as exc:
            raise ValueError(f"[{markup}] is not one content block: {exc.reason}") from None
        if end != len(text):
            raise ValueError(f"[{markup}] is not one content block: it closes after {text[:end]!r}")


@dataclass(frozen=True)
class Expr:
    """An argument written as code that is none of the literals -- `50% + 1cm`, `my-rows`, `calc.round(x)` -- kept verbatim and written back as it is. Woodcore's editors do not look into it."""
    source: str

    def __post_init__(self):
        source = _normalise(self.source).strip()
        object.__setattr__(self, "source", source)
        if not source:
            raise ValueError("an expression is not empty")
        parser = _Parser(source)
        end = parser.expr_end(0)
        if parser.ws(end) != len(source):
            raise ValueError(f"{source!r} is not one expression -- it goes on after {source[:end]!r}")


def content(markup):
    """`markup` as a Content, checked -- the engineer's words, Typst markup. None stays None and a Content or an Expr is given back."""
    if markup is None or isinstance(markup, (Content, Expr)):
        return markup
    if not isinstance(markup, str):
        raise ValueError(f"a text is Typst markup, a string -- got {markup!r}")
    return Content(markup)


def length(value):
    """A Length from its text, `"60%"`, `"12cm"`, or given back where it is one already."""
    if isinstance(value, Length):
        return value
    if not isinstance(value, str):
        raise ValueError(f"a length is written as text, \"60%\" -- got {value!r}")
    found = parse_value(value)
    if not isinstance(found, Length):
        raise ValueError(f"{value!r} is not a length, a ratio or an angle -- write it as \"60%\" or \"12cm\"")
    return found


def variable_cell(name, domain=None):
    """The cell Woodcore writes for a value of the Variables tab: `[#doc-value("g_k", domain: ("dead-load", "D1"))]` -- content printed as the value it names, so the table follows the calculation (the coordinator's decision for phase 4: a cell carries no footnote). `domain` is a var-domain of the report (a string), a calculation and its instance (a pair) or None."""
    if not isinstance(name, str) or not name:
        raise ValueError(f"a variable is named by a string -- got {name!r}")
    call = "#doc-value(" + _string(name)
    if domain is not None:
        if isinstance(domain, str):
            call += ", domain: " + _string(domain)
        elif isinstance(domain, (list, tuple)) and len(domain) == 2 and all(isinstance(d, str) for d in domain):
            call += ", domain: (" + _string(domain[0]) + ", " + _string(domain[1]) + ")"
        else:
            raise ValueError(f"a domain is a string or a pair of strings -- got {domain!r}")
    return Content(call + ")")


def same(a, b):
    """Whether two values are the same value **as Woodcore would write them**: a list and a tuple are both an array, but an integer is not a float, `true` is not `1`, and a dictionary's order counts."""
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return list(a) == list(b) and all(same(a[k], b[k]) for k in a)
    if isinstance(a, float):
        return repr(a) == repr(b)
    if isinstance(a, Length):
        return a.unit == b.unit and same(a.value, b.value)
    return a == b


class ParseError(ValueError):
    """A call or a value that cannot be read: where (`offset` into the text read, `line` and `column` 1-based) and why (`reason`)."""

    def __init__(self, reason, offset=0, text=""):
        self.reason = reason
        self.offset = offset
        self.line = text.count("\n", 0, offset) + 1
        self.column = offset - (text.rfind("\n", 0, offset) + 1) + 1
        super().__init__(f"line {self.line}, column {self.column}: {reason}")


_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*")


_NUMBER = re.compile(r"[+-]?(?:0x[0-9A-Fa-f]+|0o[0-7]+|0b[01]+|(?:\d+\.\d+|\.\d+|\d+)(?:[eE][+-]?\d+)?)(?P<unit>pt|mm|cm|in|em|fr|deg|rad|%)?")


_WORD_CHAR = re.compile(r"[\w-]")


_KEYWORDS = {"none": None, "auto": AUTO, "true": True, "false": False}


# The words a dictionary key cannot be written bare as: `(none: 1)` is not a dictionary to Typst.
RESERVED = frozenset({"none", "auto", "true", "false", "not", "and", "or", "let", "set", "show", "context", "if", "else",
                      "for", "in", "while", "break", "continue", "return", "import", "include", "as"})


_ESCAPES = {"\\": "\\", '"': '"', "n": "\n", "r": "\r", "t": "\t"}


_NOT = object()   # what `literal` gives where the text is no literal


class _Parser:
    """A small reader of Typst's code for the literals of the canonical grammar, over one text. Content and formulas are handed to the lexer of calc/typst_paths.py, which knows where each of them stops; everything else is read here."""

    def __init__(self, text):
        self.text = text
        self.n = len(text)
        self._lexer = typst_paths._Lexer(text)
        self.spans = []   # the arguments of the last call read, where they stand (`call`)

    def fail(self, reason, at):
        raise ParseError(reason, at, self.text)

    # -- white space, comments, and the blocks the lexer reads

    def ws(self, i):
        """Past white space and comments from `i`."""
        text, n = self.text, self.n
        while i < n:
            c = text[i]
            if c in " \t\n\r":
                i += 1
            elif text.startswith("//", i):
                j = text.find("\n", i)
                i = n if j < 0 else j
            elif text.startswith("/*", i):
                i = self._lexer._block_comment(i)
            else:
                break
        return i

    def _frame_end(self, i, kind, closer, what, at):
        """Where the frame the lexer is put in at `i` closes: a content block (`markup`, closed by `]`) or a formula (`math`, closed by `$`)."""
        lexer = self._lexer
        lexer.i = i
        lexer.stack = [["markup", None, 0], [kind, closer, 0]]
        lexer.hist, lexer.found = [], []
        while lexer.i < lexer.n and len(lexer.stack) > 1:
            frame = lexer.stack[-1]
            getattr(lexer, "_" + frame[0])(frame)
        if len(lexer.stack) > 1:
            self.fail(f"the {what} opened here is never closed", at)
        return lexer.i

    def content_end(self, i):
        """The index after the content block whose `[` is at `i`."""
        return self._frame_end(i + 1, "markup", "]", "content block", i)

    def string_end(self, i):
        """The index after the string whose `"` is at `i`."""
        text, n, j = self.text, self.n, i + 1
        while j < n:
            if text[j] == "\\":
                j += 2
            elif text[j] == '"':
                return j + 1
            else:
                j += 1
        self.fail("the string opened here is never closed", i)

    def string(self, i):
        """The string whose `"` is at `i`, its escapes resolved as Typst resolves them -- an escape Typst does not know is kept as it is written, backslash and all -- and the index after it."""
        end = self.string_end(i)
        raw, out, k = self.text[i + 1:end - 1], [], 0
        while k < len(raw):
            c = raw[k]
            if c != "\\" or k + 1 >= len(raw):
                out.append(c)
                k += 1
                continue
            nxt = raw[k + 1]
            if nxt == "u" and raw.startswith("{", k + 2):
                close = raw.find("}", k + 3)
                code = raw[k + 3:close] if close > 0 else ""
                if close < 0 or not re.fullmatch(r"[0-9A-Fa-f]{1,6}", code):
                    self.fail("a \\u{...} escape holds a hexadecimal code", i + 1 + k)
                out.append(chr(int(code, 16)))
                k = close + 1
            elif nxt in _ESCAPES:
                out.append(_ESCAPES[nxt])
                k += 2
            else:
                out.append(c + nxt)
                k += 2
        return "".join(out), end

    # -- an expression that is none of the literals

    def expr_end(self, i):
        """The end of the expression that starts at `i`: the end of its last token before a `,` or a closing `)` at its own depth, or the end of the text. Strings, content, formulas, raw blocks and comments are passed over whole."""
        text, n = self.text, self.n
        depth, j, last = 0, i, i
        while j < n:
            c = text[j]
            if c in " \t\n\r":
                j += 1
                continue
            if text.startswith("//", j) or text.startswith("/*", j):
                j = self.ws(j)
                continue
            if c == '"':
                j = last = self.string_end(j)
                continue
            if c == "`":
                j = last = self._lexer._raw(j)
                continue
            if c == "$":
                j = last = self._frame_end(j + 1, "math", None, "formula", j)
                continue
            if c == "[":
                j = last = self.content_end(j)
                continue
            if c in "({":
                depth += 1
            elif c in ")}":
                if depth == 0:
                    if c == "}":
                        self.fail("a `}` closes nothing here", j)
                    break
                depth -= 1
            elif c == "]":
                self.fail("a `]` closes nothing here", j)
            elif c == "," and depth == 0:
                break
            j += 1
            last = j
        if depth:
            self.fail("a bracket opened in this expression is never closed", i)
        return last

    # -- values

    def value(self, i):
        """The value that starts at `i` (white space before it passed over) and the index after it: a literal where the text is one and a `,` or a `)` follows it, else the expression the text is (Expr)."""
        i = self.ws(i)
        if i >= self.n or self.text[i] in ",)":
            self.fail("a value is expected here", i)
        found, end = self.literal(i)
        if found is not _NOT:
            k = self.ws(end)
            if k >= self.n or self.text[k] in ",)":
                return found, end
        end = self.expr_end(i)
        return Expr(self.text[i:end]), end

    def literal(self, i):
        """The literal that starts at `i` and the index after it, or `(_NOT, i)` where the text there is no literal."""
        text = self.text
        c = text[i]
        if c == '"':
            return self.string(i)
        if c == "[":
            end = self.content_end(i)
            return Content(text[i + 1:end - 1]), end
        if c == "(":
            return self.group(i)
        number = _NUMBER.match(text, i)
        if number and not (number.end() < self.n and _WORD_CHAR.match(text, number.end())):
            written = number.group()
            unit = number.group("unit") or ""
            digits = written[:len(written) - len(unit)]
            if re.match(r"[+-]?0[xob]", digits):
                if unit:
                    return _NOT, i
                sign = -1 if digits.startswith("-") else 1
                value = sign * int(digits.lstrip("+-"), 0)
            elif "." in digits or "e" in digits or "E" in digits:
                value = float(digits)
            else:
                value = int(digits)
            if unit:
                if isinstance(value, float) and not math.isfinite(value):
                    return _NOT, i
                return Length(value, unit), number.end()
            if isinstance(value, float) and not math.isfinite(value):
                return _NOT, i
            return value, number.end()
        word = _IDENT.match(text, i)
        if word and word.group() in _KEYWORDS:
            return _KEYWORDS[word.group()], word.end()
        return _NOT, i

    def _key(self, i):
        """A dictionary key at `i` -- an identifier or a string followed by `:` -- as (key, index after the colon), or None where the item is not a named one."""
        text = self.text
        if text[i] == '"':
            try:
                key, end = self.string(i)
            except ParseError:
                return None
        else:
            word = _IDENT.match(text, i)
            if not word:
                return None
            key, end = word.group(), word.end()
        k = self.ws(end)
        if k < self.n and text[k] == ":":
            return key, k + 1
        return None

    def group(self, i):
        """What a `(` at `i` opens: an array, a dictionary, or a value in parentheses; `(_NOT, i)` where it is an expression (a spread, a parenthesised expression)."""
        text, n = self.text, self.n
        j = self.ws(i + 1)
        if j < n and text[j] == ")":
            return [], j + 1
        if j < n and text[j] == ":":
            k = self.ws(j + 1)
            if k < n and text[k] == ")":
                return {}, k + 1
            self.fail("an empty dictionary is written (:)", j)
        items, named, positional, comma = {}, False, False, False
        array = []
        while True:
            j = self.ws(j)
            if j >= n:
                self.fail("the parenthesis opened here is never closed", i)
            if text[j] == ")":
                break
            if text.startswith("..", j):
                return _NOT, i
            key = self._key(j)
            if key is not None:
                if positional:
                    self.fail("an array and a dictionary at once: every item is named or none is", j)
                named = True
                name, after = key
                if name in items:
                    self.fail(f"the key {name!r} is given twice", j)
                value, end = self.value(after)
                items[name] = value
            else:
                if named:
                    self.fail("an array and a dictionary at once: every item is named or none is", j)
                positional = True
                value, end = self.value(j)
                array.append(value)
            j = self.ws(end)
            if j >= n:
                self.fail("the parenthesis opened here is never closed", i)
            if text[j] == ",":
                comma = True
                j += 1
                continue
            if text[j] == ")":
                break
            self.fail("a `,` or a `)` is expected here", j)
        end = j + 1
        if named:
            return items, end
        if len(array) == 1 and not comma:
            # a value in parentheses: `(5)` is 5, and `(a + b)` is the expression it is
            return (array[0], end) if not isinstance(array[0], Expr) else (_NOT, i)
        return array, end

    # -- a call

    def call(self, i, positional=False):
        """The call `#<type>(<name>: <value>, ...)` that starts at `i`, as (Call, the index after its `)`). Only named arguments: a positional one, a spread, an argument given twice and a content block after the parenthesis are refused -- unless `positional`, which a calculation domain's file is read with (domains/formula_domain.py, v0.117): `#var("F", 12, "kN")`, `#eq("M", `F * l`)`, and `#var-domain("…")[…]`, whose content block is its body. The ten commands of a document take named arguments only, and are read without it."""
        text, n = self.text, self.n
        if not text.startswith("#", i):
            self.fail("a parametric object is one call, `#<command>(...)`", i)
        word = _IDENT.match(text, i + 1)
        if not word:
            self.fail("a command's name is expected after the `#`", i + 1)
        kind, j = word.group(), word.end()
        if j >= n or text[j] != "(":
            self.fail(f"`#{kind}` is not called: a `(` is expected right after its name", j)
        args, pos, j = {}, [], j + 1
        # where each argument stands in the text (spec 2026-10-15, ARCH-003): (its index or its name, where the argument starts, where its value starts and ends) -- what lets a domain's file change one argument and keep every other byte
        self.spans = []
        while True:
            j = self.ws(j)
            if j >= n:
                self.fail(f"the call of {kind} is never closed", i)
            if text[j] == ")":
                j += 1
                break
            if text.startswith("..", j):
                self.fail("a spread argument is none Woodcore can write back", j)
            word = _IDENT.match(text, j)
            k = self.ws(word.end()) if word else j
            if not word or k >= n or text[k] != ":":
                if not positional:
                    self.fail(f"{kind} takes named arguments only, `name: value`", j)
                if args:
                    self.fail("a positional argument comes before the named ones", j)
                value, end = self.value(j)
                self.spans.append((len(pos), j, self.ws(j), end))
                pos.append(value)
                j = self.ws(end)
                if j < n and text[j] == ",":
                    j += 1
                    continue
                if j < n and text[j] == ")":
                    j += 1
                    break
                self.fail("a `,` or a `)` is expected here", j)
            name = word.group()
            if name in args:
                self.fail(f"the argument {name!r} is given twice", j)
            value, end = self.value(k + 1)
            self.spans.append((name, j, self.ws(k + 1), end))
            args[name] = value
            j = self.ws(end)
            if j < n and text[j] == ",":
                j += 1
                continue
            if j < n and text[j] == ")":
                j += 1
                break
            self.fail("a `,` or a `)` is expected here", j)
        body = None
        if j < n and text[j] == "[":
            if not positional:
                self.fail("a content block after the call is a positional argument, which the command does not take", j)
            end = self.content_end(j)
            body, j = Content(text[j + 1:end - 1]), end
        return Call(kind, args, pos, body), j


@dataclass
class Call:
    """One call: the command's name (`type`, `doc-table`) and its named arguments, in the order they were written -- and, read with `positional` (a calculation domain's file), its positional arguments and the content block after it."""
    type: str
    args: dict = field(default_factory=dict)
    positional: list = field(default_factory=list)
    body: object = None

    def copy(self):
        return Call(self.type, copy.deepcopy(self.args), copy.deepcopy(self.positional), self.body)

    def unknown(self):
        """The arguments the command does not take, which the canonical form leaves out."""
        order = ORDER.get(self.type)
        return [] if order is None else [name for name in self.args if name not in order]

    def same_as(self, other):
        return isinstance(other, Call) and self.type == other.type and same(self.args, other.args) and same(self.positional, other.positional) and self.body == other.body


def parse_value(text):
    """One value written as Typst code, `"(a: 1)"`, `"60%"`, `"[Büro]"`: a literal, or an Expr where the text is none."""
    text = _normalise(text)
    parser = _Parser(text)
    value, end = parser.value(0)
    rest = parser.ws(end)
    if rest < parser.n:
        parser.fail("the value ends before this", rest)
    return value


def parse_call_at(text, start):
    """The call that starts at `start` in `text` (at its `#`), as (Call, the index after it). What follows the call is not looked at."""
    return _Parser(text).call(start)


_SHOW_RULE = re.compile(r"#show[ \t]*:[ \t]*([A-Za-z_][A-Za-z0-9_-]*)\.with\(")


def _as_call(text):
    """`text` with a show rule of SHOW_RULES at its start -- `#show: sheet.with(` -- written as the call it stands for, `#sheet-page(`, at the same place: what the parser reads. Anything else is returned as it is."""
    found = _SHOW_RULE.search(text)
    if found is None or text[:found.start()].strip():
        return text
    kinds = {fn: kind for kind, fn in SHOW_RULES.items()}
    if found.group(1) not in kinds:
        return text
    return text[:found.start()] + "#" + kinds[found.group(1)] + "(" + text[found.end():]


def parse_call(body):
    """The one call `body` is -- white space and comments around it allowed, nothing else -- as a Call. Line endings are normalised first, so a content block reads the same in a CRLF file. A show rule of SHOW_RULES is read as its call. Raises ParseError."""
    text = _as_call(_normalise(body))
    parser = _Parser(text)
    start = parser.ws(0)
    if start >= parser.n:
        parser.fail("the object holds no call", start)
    found, end = parser.call(start)
    rest = parser.ws(end)
    if rest < parser.n:
        parser.fail("the object holds one call and nothing after it", rest)
    return found


def _parameters(text, what):
    """The named parameters of a signature's parameter list -- `columns: (), hidden: ()` -- as {name: default}, in order."""
    return parse_call(f"#{what}({text})").args


ORDER = {kind: tuple(_parameters(text, kind)) for kind, text in SIGNATURES.items()}


def signatures_in(text):
    """The signatures of the commands as a .typ file writes them -- `#let doc-table(columns: (), ...) = ...` -- as {command: {name: default}}, read with this module's own parser: what tests hold SIGNATURES against lib/document.typ and lib/sheet.typ with. A show rule (SHOW_RULES) is found by its function's name, its first parameter -- the document -- left out."""
    found = {}
    for kind in SIGNATURES:
        name = SHOW_RULES.get(kind, kind)
        at = text.find(f"#let {name}(")
        if at < 0:
            continue
        rest = text[at + len(f"#let {name}("):]
        if kind in SHOW_RULES:
            rest = re.sub(r"^\s*doc\s*,", "", rest)
        call, _ = parse_call_at(f"#{kind}(" + rest, 0)
        found[kind] = call.args
    return found


def _string(value):
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r") + '"'


def _float(value):
    if not math.isfinite(value):
        raise ValueError(f"{value!r} cannot be written as a Typst number")
    text = repr(value)
    if "e" in text:
        mantissa, exponent = text.split("e")
        text = f"{mantissa}e{int(exponent)}"
    return text


def _number(value):
    return _float(value) if isinstance(value, float) else str(value)


def _dict_key(key):
    if not isinstance(key, str):
        raise ValueError(f"a dictionary key is a string -- got {key!r}")
    if _IDENT.fullmatch(key) and key not in RESERVED:
        return key
    return _string(key)


def inline(value):
    """`value` written on one line, as Typst code: what a row, a column, an option or any element of an array is written as."""
    if value is None:
        return "none"
    if value is AUTO:
        return "auto"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return _number(value)
    if isinstance(value, str):
        return _string(value)
    if isinstance(value, Length):
        return _number(value.value) + value.unit
    if isinstance(value, Content):
        return "[" + value.markup + "]"
    if isinstance(value, Expr):
        return value.source
    if isinstance(value, (list, tuple)):
        if not value:
            return "()"
        return "(" + ", ".join(inline(v) for v in value) + ("," if len(value) == 1 else "") + ")"
    if isinstance(value, dict):
        if not value:
            return "(:)"
        return "(" + ", ".join(f"{_dict_key(k)}: {inline(v)}" for k, v in value.items()) + ")"
    raise ValueError(f"{value!r} is none of the values Woodcore writes")


def _argument(name, value):
    """One argument of the canonical form: `  name: value,` -- an array one element per line where it is one of LIST_ARGUMENTS, where it holds a dictionary or an array, or where its line would pass LINE_WIDTH."""
    head = f"  {name}: "
    if isinstance(value, (list, tuple)) and value:
        compound = name in LIST_ARGUMENTS or any(isinstance(v, (dict, list, tuple)) for v in value)
        one = head + inline(value) + ","
        if not compound and len(one) <= LINE_WIDTH:
            return one
        return "\n".join([head + "("] + [f"    {inline(v)}," for v in value] + ["  ),"])
    return head + inline(value) + ","


def arguments_of(call):
    """The arguments the canonical form writes, in its order: ORDER's for one of the ten commands -- an argument the command does not take being left out -- and the call's own for another."""
    order = ORDER.get(call.type)
    if order is None:
        return [name for name in call.args]
    return [name for name in order if name in call.args]


def serialize(call):
    """The canonical form of `call`, with `\\n` line endings and no final one: `#type(` on a line, one argument per line, `)`. A call with no argument is `#type()`."""
    if not _IDENT.fullmatch(call.type or ""):
        raise ValueError(f"{call.type!r} is not a command's name")
    names = arguments_of(call)
    head = f"#show: {SHOW_RULES[call.type]}.with(" if call.type in SHOW_RULES else f"#{call.type}("
    if not names:
        return head + ")"
    for name in names:
        if not _IDENT.fullmatch(name):
            raise ValueError(f"{name!r} is not an argument's name")
    return "\n".join([head] + [_argument(name, call.args[name]) for name in names] + [")"])


def default_call(kind):
    """The call Woodcore writes for a new object of `kind`, and in place of one it cannot read: every command's payload empty but for a text's placeholder, so that it compiles and says what is still to be written."""
    if kind not in SIGNATURES:
        raise ObjectError("bad_type", f"{kind!r} is not a call of lib/document.typ or lib/sheet.typ -- expected one of {', '.join(CALL_TYPES + SHEET_TYPES)}" + (" (a heading and a paragraph are markup: `default_body`)" if kind in MARKUP_TYPES else ""), type=kind)
    blank = Content(PLACEHOLDER)
    calls = {
        "show-norm-list": {"keys": []},
        # a sheet's objects (lib/sheet.typ): placed in the frame's top-left quarter, where the window then moves them
        "sheet-page": {"format": "A3", "landscape": True, "margin": Length(10, "mm")},
        "sheet-text": {"x": Length(20, "mm"), "y": Length(20, "mm"), "body": blank},
        "sheet-viewport": {"plan": None, "x": Length(20, "mm"), "y": Length(40, "mm")},
        "sheet-section": {"plan": None, "x": Length(20, "mm"), "y": Length(40, "mm")},
        "sheet-legend": {"x": Length(20, "mm"), "y": Length(40, "mm")},
        "sheet-fire-viewport": {"plan": None, "x": Length(20, "mm"), "y": Length(40, "mm")},
        "sheet-fire-legend": {"x": Length(20, "mm"), "y": Length(40, "mm")},
        "sheet-position-list": {"x": Length(20, "mm"), "y": Length(40, "mm")},
        "sheet-quantities": {"x": Length(20, "mm"), "y": Length(40, "mm")},
        "sheet-titleblock": {},
    }
    return Call(kind, calls[kind])


class ObjectError(ValueError):
    """A refusal of the functions that write objects: a `code` (CODES), an English sentence, and what it concerns -- `object` where there is one."""

    def __init__(self, code, message, object=None, **values):
        self.code = code
        self.object = object
        self.values = values
        super().__init__(message)
