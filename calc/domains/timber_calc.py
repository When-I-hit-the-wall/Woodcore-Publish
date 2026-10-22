"""The lines of a timber member check, built by the engine (spec 2026-10-21-restes-issue-69, REQ-003; docs/domain/member-checks.md).

A member check's `compute` (calc/domains/member_check.py) works its result out line by line: each line is a value with its unit and its symbol, the formula it is worked out by, and the clause of SIA 265 it cites. Since v0.120 a line is an `engine.var` -- checked the moment it is written, as every var of every other domain is (a norm, always; a clause or none) -- and a line worked out by a formula is also an `engine.step`, its `uses` the values its formula in keys names. `TimberCalculation` holds them in the order the report prints them, and `rows()` gives them back in the shape the window, `unfold`, `published_vars` and the parity with `#show-check-member` read: `{key, symbol, value, unit, formula?, label?, keys?, clause?, norm?, table?}` -- the shape `compute` has always returned, so that nothing that reads it changes (CON-001). It is the steel check's arrangement (calc/domains/steel_calc.py), the projection living here, in the domain, and not in a tab.

**Two formulas.** A line may carry `formula`, the math the window sets with symbols (`N_(t,d) / A`), and `keys`, the same formula in the registry's keys as `#eq` computes it (`N_t_d / A`). The two are written apart because the window and the unfolded file print different things; the step keeps `formula`, the calculation `keys`.

**A table's value.** A design value is computed from a value of SIA 265 Tabelle 8 or 9 (`table`): a var of its own, `<key>_tab`, which `rows()` gives back inside the line it serves and never as a line of its own.
"""

import re
from typing import NamedTuple

import engine

# The norm a line cites where it states none of its own (spec 2026-10-19-base-saine-nettoyage, ARCH-RISK-203)
NORM = "SIA 265"
# Where a member check's values come from: written into checks.json by `published_vars`, unchanged since the unfolded checks (CON-001)
SOURCE = "python:domains/member_check.py"

_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class Line(NamedTuple):
    """One line of a check, as `line()` built it: its var (checked by `engine.var`), the formula the window sets, the formula in keys, and the table value it is computed from."""
    key: str
    symbol: str
    var: dict
    formula: str | None
    keys: str | None
    table: "Line | None"


def line(key, symbol, value, unit, formula=None, label=None, keys=None, clause=None, table=None, norm=NORM):
    """A line of a check's results: `value` in `unit`, set as `symbol`; `formula` the math the window sets, `keys` the same in the registry's keys (spec 2026-10-15, ARCH-008), `clause` the clause of `norm` it cites, `label` a note printed beside it («Feuchteklasse 1»), `table` the Line of the value of SIA 265 Tabelle 8/9 a design value is computed from. Checked now, by `engine.var`: a line without a norm, or with a clause that is no string, stops here (C1, v0.120)."""
    var = engine.var(value=value, unit=unit, symbol=symbol, label=label, source=SOURCE, norm=norm, norm_ref=clause or "")
    return Line(key, symbol, var, formula or None, keys or None, table)


class TimberCalculation(engine.Calculation):
    """The lines of one check, in the order the report prints them: a var each (and a var for each table value), a step for each line worked out by a formula. `take` writes them once; `rows` is the projection `compute` returns."""

    def __init__(self):
        super().__init__()
        self.order = []    # the keys of the lines, in the order they print
        self.keys = {}     # key -> the formula in the registry's keys
        self.tables = {}   # key -> the key of its table value's var

    def add_var(self, name, **kwargs):
        if name in self.vars:
            raise engine.EngineError(f"member check: line '{name}' is written twice")
        return super().add_var(name, **kwargs)

    def take(self, lines):
        """Writes `lines` in their order: every var first, then a step for each line with a formula, its `uses` the values its formula in keys names that the check holds."""
        for item in lines:
            self.add_var(item.key, **item.var)
            self.order.append(item.key)
            if item.keys:
                self.keys[item.key] = item.keys
            if item.table:
                self.add_var(item.table.key, **item.table.var)
                self.tables[item.key] = item.table.key
        for item in lines:
            if item.formula:
                names = _IDENTIFIER.findall(item.keys or "")
                uses = [name for name in dict.fromkeys(names) if name in self.vars and name != item.key]
                var = self.vars[item.key]
                self.add_step(name=item.key, result=item.key, uses=uses, norm=var["norm"], norm_ref=var["norm_ref"],
                              formula="%s = %s" % (item.symbol, item.formula))
        return self

    def rows(self):
        """The lines as `compute` has always returned them: `{key, symbol, value, unit, formula?, label?, keys?, clause?, norm?, table?}`, only what a line carries."""
        formulas = {s["result"]: s["formula"] for s in self.steps}
        out = []
        for key in self.order:
            var = self.vars[key]
            row = {"key": key, "symbol": var["symbol"], "value": var["value"], "unit": var["unit"]}
            if key in formulas:
                row["formula"] = formulas[key].removeprefix(var["symbol"] + " = ")
            if var["label"]:
                row["label"] = var["label"]
            if key in self.keys:
                row["keys"] = self.keys[key]
            if var["norm_ref"]:
                row["clause"] = var["norm_ref"]
                row["norm"] = var["norm"]
            if key in self.tables:
                table = self.vars[self.tables[key]]
                row["table"] = {"key": self.tables[key], "symbol": table["symbol"], "value": table["value"], "unit": table["unit"], "clause": table["norm_ref"]}
            out.append(row)
        return out
