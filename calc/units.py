"""The unit algebra of lib/formula.typ, in Python: what the «Formule» tab computes at once, without a compile (spec docs/requirements/completed/2026-10-08-onglet-formule-domaines.md, D-10, ARCH-002, ARCH-005).

The engineer chose an instant result over a compile per keystroke (Q-004, 08.10.2026), as he had for the member checks (docs/decisions.md, v0.117: «un calcul python instantané … pas de latence»). That makes this module **the second implementation** of what `#eq`, `#verify` and `#var` compute in the report, which is the price the decision accepted, and it is paid three ways:

* **the units themselves are written once**, in `lib/units.json`, which `lib/formula.typ` reads with `json("units.json")` and this module reads as a file -- the prefixes, the bases with their factor and dimensions, the superscript digits, the unit a result of each dimension is printed in, and the units the tab offers for a result of each dimension. Nothing of it is written here;
* **every rule is the Typst one, read off it function by function** -- `parse_unit` is `parse-unit` (the longest prefix-and-base match at each place), `natural_unit` is `natural-unit`, `present` is `present`, `evaluate` is `evaluate-formula` with its tokenizer and its recursive descent, `fmt_magnitude` is `fmt-magnitude`. Where Typst stops the compile (`panic`) this raises `FormulaError` with the same reason, so the tab refuses at the validation what the report would refuse at the compile: **Python is never laxer than Typst**;
* **`tests/test_units.py` holds the two equal**, value and unit, on a corpus of formulas compiled in one probe, refusals included.

No Qt here: the domain module (`domains/formula_domain.py`) and the tab both call it.
"""

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import validation

# lib/units.json: one file for the two implementations (ARCH-005)
UNITS_FILE = Path(__file__).resolve().parent.parent / "lib" / "units.json"


def _load():
    data = json.loads(UNITS_FILE.read_text(encoding="utf-8"))
    bases = {symbol: (float(spec["factor"]), dict(spec["dims"])) for symbol, spec in data["bases"].items()}
    return data, {p: float(f) for p, f in data["prefixes"].items()}, bases


DATA, PREFIXES, BASES = _load()
EXPONENTS = {c: int(n) for c, n in DATA["exponents"].items()}
SUPERSCRIPTS = dict(DATA["superscripts"])
DEFAULT_UNITS = dict(DATA["default_units"])
# The units the tab offers for a result, by the dimension `dims_text` writes -- the first is the one a result is printed in by default where DEFAULT_UNITS names none
OFFERED = {dims: list(units) for dims, units in DATA["offered"].items()}

# The functions a formula may call, and the short names it prints as the long ones (formula.typ's `formula-functions`, `formula-display-names`)
FUNCTIONS = ("sqrt", "abs", "max", "min", "sin", "cos", "tan", "arcsin", "arccos", "arctan", "asin", "acos", "atan", "ln", "log", "exp")
# The relations `#verify` reads, two characters first (formula.typ's `relation-ops`), what each is written as, and its negation
RELATION_OPS = ("==", "<=", ">=", "!=", "≤", "≥", "≠", "<", ">", "=")
RELATION_ALIASES = {"≤": "<=", "≥": ">=", "≠": "!=", "==": "="}
RELATION_NEGATION = {"<=": ">", ">=": "<", "<": ">=", ">": "<=", "=": "!=", "!=": "="}
TOLERANCE = 1e-9            # calc-engine.typ's `test-tolerance`
SCI_THRESHOLD = 99999       # formula.typ's `sci-threshold`
MINUS = chr(0x2212)         # the sign a negative number is printed with (calc-engine.typ's `minus-sign`)

_PH_OPEN, _PH_CLOSE = chr(1), chr(2)   # a placeholder for a substituted symbol, as formula.typ's `placeholder` writes one
_NAME_CHAR = re.compile(r"[A-Za-z0-9_]")


class FormulaError(validation.ValidationError, ValueError):
    """What `#eq`, `#verify` or `#var` would stop the compile on -- a sum of two dimensions, the square root of an odd power, a name nobody declared, a unit that cannot be read -- said in the same words, so the tab refuses it before the report does. A ValidationError (v0.120, C7), so an export it stops says so as a defect of the input; still a ValueError for the callers that catch one."""


# --- units -------------------------------------------------------------------------------

def clean_dims(dims):
    return {d: e for d, e in dims.items() if e != 0}


def dims_equal(a, b):
    return clean_dims(a) == clean_dims(b)


def sup(n):
    """An integer as superscript digits: 2 → «²», -5 → «⁻⁵»."""
    return "".join(SUPERSCRIPTS[c] for c in str(n))


def dims_text(dims):
    """A dimension map as a unit an engineer recognises: {N: 1, m: -2} → «N/m²» -- sorted, so one dimension has one text (formula.typ's `dims-text`)."""
    d = clean_dims(dims)
    if not d:
        return "1"
    up = sorted((k, v) for k, v in d.items() if v > 0)
    down = sorted((k, v) for k, v in d.items() if v < 0)

    def part(pairs):
        return "·".join(k + ("" if abs(v) == 1 else sup(abs(v))) for k, v in pairs)

    top = "1" if not up else part(up)
    return top if not down else top + "/" + part(down)


def _read_factor(cl, i):
    """One factor of a unit product read off `cl` at `i`: (factor, dims, next) or None -- the longest prefix-and-base match wins, the first found where two are as long (formula.typ's `read-factor`)."""
    best = None
    for symbol, (factor, dims) in BASES.items():
        n = len(symbol)
        if cl[i:i + n] == symbol and (best is None or n > best[2]):
            best = (factor, dims, n)
        for prefix, scale in PREFIXES.items():
            m = len(prefix) + n
            if cl[i:i + m] == prefix + symbol and (best is None or m > best[2]):
                best = (factor * scale, dims, m)
    if best is None:
        return None
    factor, dims, used = best
    j = i + used
    power = 1
    if j < len(cl) and cl[j] in EXPONENTS:
        power = 0
        while j < len(cl) and cl[j] in EXPONENTS:
            power = power * 10 + EXPONENTS[cl[j]]
            j += 1
    else:
        k = j
        if k < len(cl) and cl[k] == "^":
            k += 1
        digits = ""
        while k < len(cl) and cl[k].isdigit() and cl[k].isascii():
            digits += cl[k]
            k += 1
        if digits:
            power = int(digits)
            j = k
    return factor ** power, {d: e * power for d, e in dims.items()}, j


def _read_product(text):
    cl = "".join(c for c in text.strip() if c not in (" ", "·", "*", "⋅"))
    factor, dims, i = 1.0, {}, 0
    while i < len(cl):
        got = _read_factor(cl, i)
        if got is None:
            return None
        factor *= got[0]
        for d, e in got[1].items():
            dims[d] = dims.get(d, 0) + e
        i = got[2]
    return factor, dims


def parse_unit(text):
    """A unit as (factor, dims) towards the base units, or None where it cannot be read: «kN» → (1000.0, {N: 1}), «kN/m²» → (1000.0, {N: 1, m: -2}), «» → dimensionless. Everything after the first `/` is a denominator (formula.typ's `parse-unit`)."""
    t = "" if text is None else text.strip()
    if t == "":
        return 1.0, {}
    factor, dims = 1.0, {}
    for i, part in enumerate(t.split("/")):
        if part.strip() == "":
            return None
        got = _read_product(part)
        if got is None:
            return None
        sign = 1 if i == 0 else -1
        factor = factor * got[0] if sign == 1 else factor / got[0]
        for d, e in got[1].items():
            dims[d] = dims.get(d, 0) + sign * e
    return factor, clean_dims(dims)


def written_unit(unit):
    """A unit written with a caret, spelt as the report prints it: «N/mm^2» → «N/mm²», and per mille written «%%» printed «‰» (formula.typ's `written-unit`)."""
    if not isinstance(unit, str):
        return unit
    unit = unit.replace("%%", "‰")
    if "^" not in unit:
        return unit
    return re.sub(r"\^([0-9]+)", lambda m: "".join(SUPERSCRIPTS[c] for c in m.group(1)), unit)


def dimension_of(unit):
    """The dimension a unit is of, as `dims_text` writes it -- the key of OFFERED and DEFAULT_UNITS -- or None for a unit that cannot be read."""
    parsed = parse_unit(unit)
    return None if parsed is None else dims_text(parsed[1])


def offered_units(dims):
    """The units the tab offers for a result of dimensions `dims`: lib/units.json's own list for that dimension, the default first; for one it names none, the default alone or the base units."""
    key = dims_text(dims)
    units = list(OFFERED.get(key, ()))
    default = DEFAULT_UNITS.get(key)
    if default and default not in units:
        units.insert(0, default)
    return units or ([] if key == "1" else [key])


# --- quantities -----------------------------------------------------------------------------

@dataclass
class Quantity:
    """A value in base units, its dimensions, and `nat`: the units the operands were written in, {unit: exponent} -- what lets a result be printed in Nmm where its declared unit cannot be reached (formula.typ's quantities)."""
    base: float
    dims: dict
    nat: dict = field(default_factory=dict)


def quantity(value, unit):
    parsed = parse_unit(unit)
    if parsed is None:
        return None
    written = "" if unit is None else unit.strip()
    return Quantity(value * parsed[0], parsed[1], {} if written == "" else {written: 1})


def _nat_mul(a, b, sign):
    out = dict(a)
    for u, e in b.items():
        out[u] = out.get(u, 0) + sign * e
    return {u: e for u, e in out.items() if e != 0}


def _nat_pow(a, n):
    out = {}
    for u, e in a.items():
        x = e * n
        if x != round(x):
            return {}
        if x != 0:
            out[u] = int(round(x))
    return out


def q_mul(a, b):
    dims = dict(a.dims)
    for d, e in b.dims.items():
        dims[d] = dims.get(d, 0) + e
    return Quantity(a.base * b.base, clean_dims(dims), _nat_mul(a.nat, b.nat, 1))


def q_div(a, b):
    if b.base == 0:
        raise FormulaError("eq: division by zero in the formula")
    dims = dict(a.dims)
    for d, e in b.dims.items():
        dims[d] = dims.get(d, 0) - e
    return Quantity(a.base / b.base, clean_dims(dims), _nat_mul(a.nat, b.nat, -1))


def q_add(a, b, sign):
    if not dims_equal(a.dims, b.dims):
        raise FormulaError(f"eq: cannot add {dims_text(a.dims)} and {dims_text(b.dims)} -- the two sides of a + or a - must have the same dimensions")
    return Quantity(a.base + sign * b.base, clean_dims(a.dims), a.nat if a.nat else b.nat)


def q_pow(a, n):
    # an exponent that comes out whole is an int, as Typst prints `str(2.0)` as «2»: a float would be written «2.0» and has no superscript
    dims = {d: int(e * n) if float(e * n).is_integer() else e * n for d, e in a.dims.items()}
    return Quantity(a.base ** n, clean_dims(dims), _nat_pow(a.nat, n))


def _nat_parsed(nat):
    factor, dims = 1.0, {}
    for u, e in nat.items():
        p = parse_unit(u)
        if p is None:
            return None
        factor *= p[0] ** e
        for d, x in p[1].items():
            dims[d] = dims.get(d, 0) + x * e
    return factor, clean_dims(dims)


def _compose_unit(nat, joiner):
    up = sorted((k, v) for k, v in nat.items() if v > 0)
    down = sorted((k, v) for k, v in nat.items() if v < 0)

    def part(pairs):
        return joiner.join(k + ("" if abs(v) == 1 else sup(abs(v))) for k, v in pairs)

    top = "1" if not up else part(up)
    return top if not down else top + "/" + part(down)


def natural_unit(nat):
    """The unit the operands were written in -- an N times a mm gives «Nmm» -- or None where it composes into nothing writable (formula.typ's `natural-unit`)."""
    if not nat:
        return None
    want = _nat_parsed(nat)
    if want is None:
        return None

    def fits(text):
        p = parse_unit(text)
        return p is not None and dims_equal(p[1], want[1]) and abs(p[0] - want[0]) <= 1e-9 * max(1.0, abs(want[0]))

    for joiner in ("", "·"):
        text = _compose_unit(nat, joiner)
        if fits(text):
            return text
    return None


def pick_unit(dims, table=None):
    return (table or DEFAULT_UNITS).get(dims_text(clean_dims(dims)))


def present(fn, symbol, parsed, want=None, table=None):
    """A quantity as the value and unit a report prints: `want` the declared unit, None to let the table choose. Where the declared unit cannot be reached the result is given in the operands' own unit with a `warning` (wanted, natural), never a stop; an unreadable unit is one (formula.typ's `present`)."""
    table = table or DEFAULT_UNITS
    want = written_unit(want)   # as formula.typ's `present` is handed it: «%%» is per mille, «‰»

    def natural():
        nat = natural_unit(parsed.nat)
        if nat is not None:
            return parsed.base / parse_unit(nat)[0], nat
        u = pick_unit(parsed.dims, table)
        if u is not None:
            return parsed.base / parse_unit(u)[0], u
        return parsed.base, dims_text(parsed.dims)

    if want is None:
        if not clean_dims(parsed.dims):
            return parsed.base, "", None
        u = pick_unit(parsed.dims, table)
        if u is None:
            return parsed.base, dims_text(parsed.dims), None
        return parsed.base / parse_unit(u)[0], u, None
    p = parse_unit(want)
    if p is None:
        raise FormulaError(f"{fn}: cannot read the unit {want!r} of {symbol} -- write it as the report writes one, `kN`, `N/mm²`, `kNm`")
    if dims_equal(parsed.dims, p[1]):
        return parsed.base / p[0], want, None
    value, unit = natural()
    return value, unit, {"wanted": want, "natural": unit}


# --- the formula ---------------------------------------------------------------------------

def _skip_quoted(src, i):
    """Where the quoted span opening at `i` ends, past its closing quote -- an escaped quote does not close it (formula.typ's `skip-quoted`)."""
    j = i + 1
    while j < len(src) and src[j] != '"':
        j += 2 if src[j] == "\\" else 1
    return min(j + 1, len(src))


def _blank_quoted(src):
    """`src` with every quoted span blanked (formula.typ's `blank-quoted`)."""
    out, i = [], 0
    while i < len(src):
        if src[i] == '"':
            i = _skip_quoted(src, i)
            out.append(" ")
        else:
            out.append(src[i])
            i += 1
    return "".join(out)


def _replace_word(src, key, with_):
    """`src` with every whole-word occurrence of `key` replaced, quoted spans left alone (formula.typ's `replace-word`; issue #32: a variable `m` rewrote the "m" of `(3 "m")`)."""
    out, i, n = [], 0, len(key)
    while i < len(src):
        if src[i] == '"':
            j = _skip_quoted(src, i)
            out.append(src[i:j])
            i = j
            continue
        fits = src[i:i + n] == key
        free_before = i == 0 or not _NAME_CHAR.match(src[i - 1])
        free_after = i + n >= len(src) or not _NAME_CHAR.match(src[i + n])
        if fits and free_before and free_after:
            out.append(with_)
            i += n
        else:
            out.append(src[i])
            i += 1
    return "".join(out)


def star_as_dot(src):
    """A `*` read as `dot`, as `#eq` and `#verify` read it -- left alone inside quotes, after a backslash and as an attachment (formula.typ's `star-as-dot`)."""
    if "*" not in src:
        return src
    out, i = [], 0
    while i < len(src):
        c = src[i]
        if c == '"':
            j = i + 1
            while j < len(src) and src[j] != '"':
                j += 2 if src[j] == "\\" else 1
            j = min(j + 1, len(src))
        elif c == "\\":
            j = min(i + 2, len(src))
        else:
            j = i + 1
        attached = i > 0 and src[i - 1] in ("^", "_")
        out.append(" dot " if c == "*" and not attached else src[i:j])
        i = j
    return "".join(out)


def operands_of(src, values):
    """The keys of `values` the formula names, longest first, so that a key which begins another cannot eat it (formula.typ's `formula-operands`)."""
    named = [key for key in values if _replace_word(src, key, chr(3)) != src]
    return sorted(named, key=lambda k: -len(k))


def unknown_names(src, operands):
    rest = _blank_quoted(src)
    for key in operands:
        rest = _replace_word(rest, key, " ")
    words = []
    for m in re.finditer(r"[A-Za-z_][A-Za-z0-9_]*", rest):
        w = m.group()
        if w not in ("dot", "pi") and w not in FUNCTIONS and w not in words:
            words.append(w)
    return words


def _tokenize(src):
    tokens, i, n = [], 0, len(src)
    singles = {"+": "+", "-": "-", "*": "*", "/": "/", "^": "^", "⋅": "*", "·": "*"}
    while i < n:
        c = src[i]
        if c in (" ", "\n", "\t"):
            i += 1
        elif c in singles:
            tokens.append(("op", singles[c]))
            i += 1
        elif c == "(":
            tokens.append(("lpar",))
            i += 1
        elif c == ")":
            tokens.append(("rpar",))
            i += 1
        elif c == ",":
            tokens.append(("comma",))
            i += 1
        elif c == _PH_OPEN:
            j = i + 1
            while j < n and src[j] != _PH_CLOSE:
                j += 1
            if j >= n:
                return None
            tokens.append(("sym", int(src[i + 1:j])))
            i = j + 1
        elif c.isascii() and (c.isdigit() or c == "."):
            j = i
            while j < n and src[j].isascii() and (src[j].isdigit() or src[j] == "."):
                j += 1
            digits = src[i:j]
            expo, k = "", j
            if k < n and src[k] in "eE":
                t, m = src[k], k + 1
                if m < n and src[m] in "+-":
                    t += src[m]
                    m += 1
                e = ""
                while m < n and src[m].isascii() and src[m].isdigit():
                    e += src[m]
                    m += 1
                if e:
                    expo, k = t + e, m
            unit, past = "", k
            m = k
            while m < n and src[m] == " ":
                m += 1
            if m < n and src[m] == '"':
                q = m + 1
                while q < n and src[q] != '"':
                    q += 1
                if q < n:
                    unit, past = src[m + 1:q], q + 1
            try:
                value = float(digits + expo)
            except ValueError:
                raise FormulaError(f"eq: {digits + expo!r} is not a number")
            qty = quantity(value, unit)
            if qty is None:
                return None
            tokens.append(("qty", qty))
            i = past
        elif c.isascii() and c.isalpha():
            j = i
            while j < n and src[j].isascii() and src[j].isalpha():
                j += 1
            word = src[i:j]
            if word == "dot":
                tokens.append(("op", "*"))
            elif word == "pi":
                tokens.append(("qty", Quantity(math.pi, {}, {})))
            elif word in FUNCTIONS:
                tokens.append(("func", word))
            else:
                return None
            i = j
        elif c == "\\" and i + 1 < n and src[i + 1] == "/":
            tokens.append(("op", "/"))
            i += 2
        else:
            return None
    return tokens


def _parse(tokens, values):
    """expr := term (("+"|"-") term)*; term := unary (("*"|"/") unary)*; unary := "-" unary | power; power := atom ("^" number)?; atom := number | symbol | "(" expr ")" | func "(" expr ("," expr)* ")". Each returns (value, next) or None (formula.typ's `parse-expr`)."""

    def atom(i):
        if i >= len(tokens):
            return None
        t = tokens[i]
        if t[0] == "qty":
            return t[1], i + 1
        if t[0] == "sym":
            return (values[t[1]], i + 1) if t[1] < len(values) else None
        if t[0] == "lpar":
            got = expr(i + 1)
            if got is None or got[1] >= len(tokens) or tokens[got[1]][0] != "rpar":
                return None
            return got[0], got[1] + 1
        if t[0] == "func":
            if i + 1 >= len(tokens) or tokens[i + 1][0] != "lpar":
                return None
            args, j = [], i + 2
            while True:
                got = expr(j)
                if got is None:
                    return None
                args.append(got[0])
                j = got[1]
                if j < len(tokens) and tokens[j][0] == "comma":
                    j += 1
                else:
                    break
            if j >= len(tokens) or tokens[j][0] != "rpar":
                return None
            return _call(t[1], args), j + 1
        return None

    def power(i):
        got = atom(i)
        if got is None:
            return None
        value, j = got
        if j + 1 < len(tokens) and tokens[j] == ("op", "^") and tokens[j + 1][0] == "qty" and not clean_dims(tokens[j + 1][1].dims):
            n = tokens[j + 1][1].base
            if any((e * n) % 1 != 0 for e in clean_dims(value.dims).values()):
                raise FormulaError(f"eq: {dims_text(value.dims)} raised to {n:g} has no unit -- a formula that holds only in given units (SIA 265 (87): d in mm) is written with its answer and its unit, value: and unit:, or with its operands as plain numbers")
            return q_pow(value, n), j + 2
        return value, j

    def unary(i):
        if i < len(tokens) and tokens[i] == ("op", "-"):
            got = unary(i + 1)
            if got is None:
                return None
            return Quantity(-got[0].base, got[0].dims, got[0].nat), got[1]
        return power(i)

    def term(i):
        got = unary(i)
        if got is None:
            return None
        value, j = got
        while j < len(tokens) and tokens[j][0] == "op" and tokens[j][1] in ("*", "/"):
            op = tokens[j][1]
            nxt = unary(j + 1)
            if nxt is None:
                return None
            value = q_mul(value, nxt[0]) if op == "*" else q_div(value, nxt[0])
            j = nxt[1]
        return value, j

    def expr(i):
        got = term(i)
        if got is None:
            return None
        value, j = got
        while j < len(tokens) and tokens[j][0] == "op" and tokens[j][1] in ("+", "-"):
            sign = 1 if tokens[j][1] == "+" else -1
            nxt = term(j + 1)
            if nxt is None:
                return None
            value = q_add(value, nxt[0], sign)
            j = nxt[1]
        return value, j

    return expr(0)


def _call(name, args):
    a = args[0]
    if name == "sqrt":
        dims = {}
        for d, e in a.dims.items():
            if e % 2 != 0:
                raise FormulaError(f"eq: sqrt of {dims_text(a.dims)}, whose dimensions are not even")
            dims[d] = e // 2
        return Quantity(math.sqrt(a.base), clean_dims(dims), _nat_pow(a.nat, 0.5))
    if name == "abs":
        return Quantity(abs(a.base), a.dims, a.nat)
    if name in ("max", "min"):
        for other in args[1:]:
            if not dims_equal(a.dims, other.dims):
                raise FormulaError(f"eq: {name} compares {dims_text(a.dims)} with {dims_text(other.dims)}")
        bases = [q.base for q in args]
        return Quantity(max(bases) if name == "max" else min(bases), a.dims, a.nat)
    d = clean_dims(a.dims)
    if d and d != {"deg": 1}:
        raise FormulaError(f"eq: {name} takes a number, got {dims_text(a.dims)}")
    x = a.base * math.pi / 180 if d == {"deg": 1} else a.base
    fn = {"sin": math.sin, "cos": math.cos, "tan": math.tan, "asin": math.asin, "arcsin": math.asin, "acos": math.acos, "arccos": math.acos,
          "atan": math.atan, "arctan": math.atan, "ln": math.log, "log": math.log10, "exp": math.exp}[name]
    return Quantity(fn(x), {}, {})


def evaluate(fn, src, values):
    """One formula, as `#eq` and `#verify` read it, against `values` {key: (value, unit)}: (Quantity, the keys it named). Raises FormulaError where the report's compile would stop -- an unknown name, a sum of two dimensions -- and where the formula cannot be read at all, which `#eq` without `value:` refuses too (formula.typ's `evaluate-formula`)."""
    src = star_as_dot(src)
    operands = operands_of(src, values)
    unknown = unknown_names(src, operands)
    if unknown:
        raise FormulaError(f"{fn}: no variable named {', '.join(repr(w) for w in unknown)} here -- "
                           + ("declared here: " + ", ".join(values) if values else "no variable is declared yet"))
    coded, qs = src, []
    for i, key in enumerate(operands):
        coded = _replace_word(coded, key, f"{_PH_OPEN}{i}{_PH_CLOSE}")
        value, unit = values[key]
        if not isinstance(value, (int, float)):
            raise FormulaError(f"{fn}: `{key}` is {value!r}, not a number")
        q = quantity(float(value), unit)
        if q is None:
            raise FormulaError(f"{fn}: cannot read the unit {unit!r} of `{key}`")
        qs.append(q)
    tokens = _tokenize(coded)
    got = None if tokens is None else _parse(tokens, qs)
    if got is None or got[1] != len(tokens):
        raise FormulaError(f"{fn}: {src.strip()!r} cannot be computed -- write it with + - * / ^, parentheses, numbers (a unit in quotes after one, 12 \"kN\") and the functions {', '.join(FUNCTIONS[:6])} …")
    return got[0], operands


def split_relation(src):
    """A relation as (left, operator, right), the operator as `#verify` reads it -- or a FormulaError naming the operators where there is none."""
    for op in RELATION_OPS:
        at = src.find(op)
        if at >= 0:
            return src[:at], RELATION_ALIASES.get(op, op), src[at + len(op):]
    raise FormulaError(f"verify: no relation in {src!r} -- write one of {', '.join(RELATION_OPS)}")


def holds(op, a, b):
    slack = TOLERANCE * max(1, abs(a), abs(b))
    return {"<=": a <= b + slack, ">=": a >= b - slack, "<": a < b - slack, ">": a > b + slack,
            "=": abs(a - b) <= slack, "!=": abs(a - b) > slack}[op]


# --- printing a number ---------------------------------------------------------------------

def fmt_decimals(x, digits=3):
    """A number at `digits` decimals, its trailing zeros and a bare point dropped, «-0» never written (calc-engine.typ's `fmt-decimals`): half rounds away from zero, as Typst's `calc.round`."""
    if isinstance(x, str):
        return x
    scaled = int(math.floor(abs(x) * 10 ** digits + 0.5))
    s = str(scaled).rjust(digits + 1, "0")
    cut = len(s) - digits
    frac = s[cut:].rstrip("0")
    out = s[:cut] if frac == "" else s[:cut] + "." + frac
    return "-" + out if x < 0 and scaled != 0 else out


def fmt_magnitude(x, digits=3):
    """A number at `digits` decimals, as a mantissa and a power of ten past 99 999: 1234567 → «1.235 · 10⁶» (formula.typ's `fmt-magnitude`)."""
    if not isinstance(x, (int, float)) or abs(x) <= SCI_THRESHOLD:
        return fmt_decimals(x, digits)
    e = int(math.floor(math.log10(abs(x))))
    if abs(float(fmt_decimals(x / 10.0 ** e, digits))) >= 10:
        e += 1
    return fmt_decimals(x / 10.0 ** e, digits) + " · 10" + sup(e)


def signed(text):
    """A number as it is printed: its sign the typographic minus (calc-engine.typ's `signed-text`)."""
    return MINUS + text[1:] if isinstance(text, str) and text.startswith("-") else text


def shown(value, unit, digits=3):
    """«4.969 kN» -- a value and its unit as a line of the tab prints them."""
    text = signed(fmt_magnitude(value, digits)) if isinstance(value, (int, float)) else str(value)
    return text if not unit else text + ("" if unit == "°" else " ") + unit
