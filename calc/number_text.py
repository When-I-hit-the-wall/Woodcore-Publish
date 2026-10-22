"""How Woodcore writes a number: the one display rule, and the rounding it is built on -- lib/number.typ's Python twin (named `number_text` and not `numbers`, which is a module of the standard library that `fractions` and `decimal` import: calc/ being first on the path, the name would have hidden it) (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, UI-002, UI-003, Q-005, D-22).

* `trimmed(value, digits)` -- at most `digits` decimals, trailing zeros and point dropped, never «-0». What a value **transported** is written with: a literal Typst evaluates again (6 decimals, `exact`), a coordinate of a figure (svg_draw.number_at), a constant composed into a formula. The domains had it four times over until v0.120 (`_fmt` of member_check, dowel and the two load sources, `_common.plain`), at two precisions.
* `display(value)` -- a number as the report prints it, lib/number.typ's `display-number`: at most three decimals, a minus sign, and a mantissa and a power of ten past 99 999 or where three decimals would lose the value's first three significant digits (0.00234 → 2.34 · 10⁻³, an exact 0.05 staying 0.05). tests/test_number_text.py holds the two equal, case by case, against Typst itself.

Qt-free and importing nothing of the domains: any module of calc/ may read it.
"""

import json
import math
from pathlib import Path

# lib/units.json's superscript digits, the ones lib/number.typ writes an exponent with
_SUPERSCRIPTS = json.loads((Path(__file__).resolve().parent.parent / "lib" / "units.json").read_text(encoding="utf-8"))["superscripts"]

DISPLAY_LIMIT = 99999       # past this, a mantissa and a power of ten (D-08)
DISPLAY_DECIMALS = 3        # never more decimals than this, trailing zeros dropped (UI-003)
MINUS = "−"            # the sign a printed number carries (v0.87)
EXACT_DIGITS = 6            # what a transported value keeps: unfold's tolerance is 1e-6 (ARCH-RISK-401)


def trimmed(value, digits):
    """`value` with at most `digits` decimals, its trailing zeros and point taken off, never «-0»: 1.250 → «1.25», -0.0004 → «0» at three. A hyphen for a sign: the string is also math source."""
    text = f"{value:.{digits}f}"
    # the zeros of the decimals only: at no decimal a whole number keeps its own (1200 stays «1200»; ARCH-RISK-702)
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def plain(value, digits):
    """A number as a figure writes it -- `trimmed` at `digits` (at least 1) -- and anything that is not one as its text: the schemas' and the static models' `fmt_number`, written once (spec 2026-10-20-indices-et-niveaux, ARCH-004)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return str(value)
    return trimmed(value, digits)


def exact(value):
    """A value as it is transported, at six decimals (`trimmed`, D-22)."""
    return trimmed(float(value), EXACT_DIGITS)


def display_parts(value):
    """(mantissa, exponent) as the rule writes `value`: the mantissa a `trimmed` string (a hyphen for a sign), the exponent an int or None."""
    fixed = trimmed(value, DISPLAY_DECIMALS)
    a = abs(value)
    if a == 0:
        return "0", None
    lossy = abs(float(fixed) - value) > 1e-12 * max(1.0, a)
    # below 0.1, three decimals hold fewer than three significant digits: a value they do not write whole is written in powers of ten
    if a <= DISPLAY_LIMIT and not (lossy and a < 0.1):
        return fixed, None
    e = math.floor(math.log10(a))
    # a mantissa the rounding carries over: 999999.9 is 10.000 · 10⁵, which is 1 · 10⁶
    if abs(float(trimmed(value / 10.0 ** e, DISPLAY_DECIMALS))) >= 10:
        e += 1
    return trimmed(value / 10.0 ** e, DISPLAY_DECIMALS), e


def superscript(n):
    """An integer as superscript digits: 2 → «²», -5 → «⁻⁵»."""
    return "".join(_SUPERSCRIPTS[c] for c in str(n))


def display(value):
    """A number as the report prints it (lib/number.typ, `display-number`); a string passes through."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return value
    mantissa, e = display_parts(value)
    if mantissa.startswith("-"):
        mantissa = MINUS + mantissa[1:]
    return mantissa if e is None else f"{mantissa} · 10{superscript(e)}"
