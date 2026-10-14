"""The rows of a steel check, in the shape `show-calc` prints (spec 2026-10-12-section-acier D-09, D-17, ARCH-RISK-202, ARCH-RISK-204; docs/domain/steel.md).

A steel check is computed once, in Python (D-09): each value it works out is a var `{value, unit, symbol, label, level, source, norm, norm_ref}` and each one worked out from others a step `{name, level, result, uses, norm, norm_ref, formula}` -- the connectors' arrangement (docs/domain/connectors.md), which `show-calc` in lib/calc-engine.typ prints with its levels, `shown:` at −1, the formula in letters then in numbers, and the citation. The export writes them as they are and Typst computes nothing (the decision of 12.10.2026, docs/decisions.md).

**Units.** The arithmetic is in N and mm; a var is written in the unit a page prints it in -- kN, kNm, N/mm², mm², mm³, mm⁴ -- `UNITS` converting. **Words.** A label and a step's name are written in German, the engine's source language, and are keys of calc/i18n/strings.json's `terms`, which `tl-str` turns into the report's language (docs/typst/language.md §4bis); tests/test_steel_check.py holds every one of them there. **Symbols** are Typst math with SIA 263's subscripts as letters apart, `N_(R d)`, `W_(p l,y)`, `gamma_(M 1)`.
"""

NORM = "SIA 263"

# The unit a value is printed in, and the factor from the N, mm the arithmetic is done in.
UNITS = {
    "kN": 1e-3, "kNm": 1e-6, "N/mm²": 1.0, "mm": 1.0, "mm²": 1.0, "mm³": 1.0, "mm⁴": 1.0, "": 1.0, "%": 1.0, "kg/m": 1.0,
}


class Calc:
    """The vars and steps of one check, in the order they are worked out."""

    def __init__(self, source):
        self.source = source   # "woodcore:steel/<id>.json"
        self.vars = {}
        self.steps = []
        self.values = {}       # every value in N, mm -- what the next formula reads

    def given(self, key, value, unit, symbol, label, level=2, norm="", norm_ref="", source=None, group="input", description=None):
        """A value the check is given -- the source's, the position's, a table's -- printed, not worked out."""
        self.values[key] = value
        var = {"value": _out(value, unit), "unit": unit, "symbol": symbol, "label": label, "level": level,
               "source": source or self.source, "norm": norm, "norm_ref": norm_ref, "group": group}
        if description:
            var["description"] = description
        self.vars[key] = var
        return value

    def step(self, key, value, unit, symbol, label, formula, uses, norm_ref, level=2, description=None, bold=False):
        """A value worked out by `formula` (Typst math, letters on the left of `=`) from `uses`."""
        self.values[key] = value
        self.vars[key] = {"value": _out(value, unit), "unit": unit, "symbol": symbol, "label": label, "level": level,
                          "source": "python:domains/steel_resistance.py", "norm": NORM, "norm_ref": norm_ref}
        step = {"name": label, "level": level, "result": key, "uses": list(uses), "norm": NORM, "norm_ref": norm_ref,
                "formula": "%s = %s" % (symbol, formula), "inline": True}
        if description:
            step["description"] = description
        if bold:
            step["bold"] = True
        self.steps.append(step)
        return value

    def record(self):
        return {"vars": self.vars, "steps": self.steps}


def _out(value, unit):
    if value is None or isinstance(value, str):
        return value
    v = value * UNITS[unit]
    return round(v, 10) if abs(v) >= 1e-12 else 0.0
