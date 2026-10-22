"""A line of a calculation Python computed, written for `#eq` to compute again: its formula in the registry's keys, kept **only where that formula, computed as `#eq` computes it (calc/units.py), gives the line's own value** (spec docs/requirements/completed/2026-10-21-commandes-typst-refonte.md, REQ-017, ARCH-003).

A domain Woodcore writes out -- a member check, a steel check, the domains the next generators bring (calc/domains/unfold.py) -- prints each value it worked out as an `#eq` where this says the formula computes it, and as a literal checked by `domain:` where it does not: a branch, a value of a table written as a number, a formula that names something the file does not declare. Shared by every generator so that the rule is one. Qt-free.
"""

import re

import units

# The characters of a name in a formula: what may not stand on either side of a symbol replaced whole
NAME = r"[A-Za-z0-9_]"


def keys_of(formula, known):
    """`formula`, the math source a line is printed with, each symbol it names replaced by the registry's key of it (`known` {symbol: key}), the longest first and whole -- a name followed by `(` is a function and left. A name the registry does not hold stays as it is, and `computes` then says no."""
    out = formula
    for symbol in sorted(known, key=len, reverse=True):
        key = known[symbol]
        if symbol == key:
            continue
        out = re.sub(r"(?<!" + NAME + r")" + re.escape(symbol) + r"(?!" + NAME + r"|\()", key, out)
    return out


def computes(keys, values, key, value, unit):
    """Whether `keys`, computed as `#eq` computes it against `values` {key: (value, unit)}, gives `value` in `unit` to 1e-9 -- a dimension the unit cannot be reached from (a design value written as a bare number of its table) is no."""
    try:
        q, _operands = units.evaluate("eq", keys, values)
        got, _unit, warning = units.present("eq", key, q, units.written_unit(unit or "") or None)
    except (units.FormulaError, ValueError, TypeError, ZeroDivisionError, KeyError):
        return False
    if warning or not isinstance(got, (int, float)) or not isinstance(value, (int, float)):
        return False
    return abs(got - value) <= 1e-9 * max(1.0, abs(value))


def calc_lines(record):
    """The vars of a calculation record of the export -- `{vars, steps, …}`, a steel check's, a load's (engine.Calculation) -- in the order it worked them out, each `{key, symbol, value, unit, label, description, norm, norm_ref}` and `keys`, its step's formula in the registry's keys, where that formula computes the value as `#eq` computes it: what a file written out prints as an `#eq`; every other value is a literal checked by `domain:`. A step that names no value (`uses` empty, a formula of numbers) is a literal; a var without a value is left out."""
    steps = {step["result"]: step for step in record.get("steps", [])}
    known, values, out = {}, {}, []
    for key, var in record.get("vars", {}).items():
        if var.get("value") is None:
            continue
        line = dict(var, key=key)
        step = steps.get(key)
        numeric = isinstance(var["value"], (int, float)) and not isinstance(var["value"], bool)
        if numeric and step and step.get("uses") and " = " in step.get("formula", ""):
            # `\/` is a slash Typst's math sets as one (a connector's formulas write it so): a division to compute
            keys = keys_of(step["formula"].split(" = ", 1)[1].replace("\\/", "/"), known)
            if computes(keys, values, key, var["value"], var.get("unit")):
                line["keys"] = keys
        if numeric:
            known[var["symbol"]] = key
            values[key] = (var["value"], var.get("unit") or "")
        out.append(line)
    return out
