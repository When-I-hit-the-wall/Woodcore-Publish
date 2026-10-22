"""The rows of a steel check, in the shape `show-calc` prints (spec 2026-10-12-section-acier D-09, D-17, ARCH-RISK-202, ARCH-RISK-204; docs/domain/steel.md).

A steel check is computed once, in Python (D-09): each value it works out is a var `{value, unit, symbol, label, level, source, norm, norm_ref}` and each one worked out from others a step `{name, level, result, uses, norm, norm_ref, formula}` -- the connectors' arrangement (docs/domain/connectors.md), which `show-calc` in lib/calc-engine.typ prints with its levels, `shown:` at −1, the formula in letters then in numbers, and the citation. The export writes them as they are and Typst computes nothing (the decision of 12.10.2026, docs/decisions.md).

**Units.** The arithmetic is in N and mm; a var is written in the unit a page prints it in -- kN, kNm, N/mm², mm², mm³, mm⁴ -- `UNITS` converting. **Words.** A label and a step's name are written in German, the engine's source language, and are keys of calc/i18n/strings.json's `terms`, which `tl-str` turns into the report's language (docs/typst/language.md §4bis); tests/test_steel_check.py holds every one of them there. **Symbols** are Typst math with SIA 263's subscripts as letters apart, `N_(R d)`, `W_(p l,y)`, `gamma_(M 1)`.
"""

import engine

NORM = "SIA 263"

# The unit a value is printed in, and the factor from the N, mm the arithmetic is done in.
UNITS = {
    "kN": 1e-3, "kNm": 1e-6, "N/mm²": 1.0, "mm": 1.0, "mm²": 1.0, "mm³": 1.0, "mm⁴": 1.0, "": 1.0, "%": 1.0, "kg/m": 1.0,
}


class SteelCalculation(engine.Calculation):
    """The vars and steps of one check, in the order they are worked out -- an engine.Calculation, so every var and step is checked as every other domain's is: a citation, a level of 1 to 3 (spec 2026-10-19-base-saine-nettoyage, C1; `Calc` until v0.120).

    A value the engineer enters -- a force, a side of a profile he drew -- states no norm of its own: it cites the clause of the check it serves (Q-011, the engineer: «la norme où elle sert»), which the verdict knows and `cite_entered` writes in once it is reached.
    """

    def __init__(self, source):
        super().__init__()
        self.source = source   # "woodcore:steel/<id>.json"
        self.values = {}       # every value in N, mm -- what the next formula reads
        self.entered = []      # the keys of the values entered, cited where they serve (cite_entered)

    def given(self, key, value, unit, symbol, label, norm="", norm_ref="", source=None, group="input", description=None):
        """A value the check is given -- the source's, the position's, a table's -- printed, not worked out. One without a norm is a value entered (`entered`)."""
        self.values[key] = value
        if not norm:
            norm, norm_ref = NORM, ""
            self.entered.append(key)
        self.add_var(key, value=_out(value, unit), unit=unit, symbol=symbol, label=label,
                     source=source or self.source, norm=norm, norm_ref=norm_ref, group=group, description=description or None)
        return value

    def step(self, key, value, unit, symbol, label, formula, uses, norm_ref, description=None, bold=False):
        """A value worked out by `formula` (Typst math, letters on the left of `=`) from `uses`."""
        self.values[key] = value
        self.add_var(key, value=_out(value, unit), unit=unit, symbol=symbol, label=label,
                     source="python:domains/steel_resistance.py", norm=NORM, norm_ref=norm_ref)
        self.add_step(name=label, result=key, uses=uses, norm=NORM, norm_ref=norm_ref,
                      formula="%s = %s" % (symbol, formula), description=description, bold=True if bold else None, inline=True)
        return value

    def cite_entered(self, clause):
        """Every value entered cites `clause` of SIA 263, the clause of the verdict it serves (Q-011)."""
        for key in self.entered:
            if key in self.vars:
                self.vars[key]["norm_ref"] = clause

    def record(self):
        return {"vars": self.vars, "steps": self.steps}


def _out(value, unit):
    if value is None or isinstance(value, str):
        return value
    v = value * UNITS[unit]
    return round(v, 10) if abs(v) >= 1e-12 else 0.0
