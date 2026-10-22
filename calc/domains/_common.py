"""The few helpers every domain module wrote for itself (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, G4).

The audit of 19.10.2026 found `_fail` in sixteen modules, `_number` in ten, in two meanings -- a test (is it a number) and a check (it must be one, refused naming the field otherwise) -- each copy free to word its refusal its own way. They are written once here; a module imports them under the names it always called them by (`from domains._common import fail as _fail`), so not one call changed. Qt-free and importing nothing of the domains, so any module of calc/ may read it.
"""

import math
from pathlib import Path

import validation
from number_text import exact as plain  # the one trimming of a number (calc/number_text.py, UI-003): six decimals, the load formulas' constants


def fail(where, message):
    """The refusal of a source or an export: `<where>: <message>`, `where` the file and the field (CLAUDE.md: a defect stops the export, naming both)."""
    raise validation.ValidationError(f"{where}: {message}")


def is_number(value):
    """Whether `value` is a number a calculation may take: an int or a float, a bool not being one."""
    return not isinstance(value, bool) and isinstance(value, (int, float))


def check_number(value, where, what, positive=False):
    """`value`, where it is a finite number (greater than 0 where `positive`) -- refused naming `what` otherwise."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        fail(where, f"{what} must be a number, got {value!r}")
    if positive and value <= 0:
        fail(where, f"{what} must be greater than 0, got {value!r}")
    return value


def source_paths(source_dir):
    """Every source of a folder, in file-name order without case -- the order they are listed in, exported in, and shown in the report (five domains had this function, word for word, until v0.120)."""
    source_dir = Path(source_dir)
    if not source_dir.is_dir():
        return []
    return sorted(source_dir.glob("*.json"), key=lambda p: p.name.lower())


def require_one_of(cells, value, allowed, sheet, ref, what):
    """`value`, a cell of a workbook's sheet, where it is one of `allowed` -- refused naming the cell and the values it may take otherwise (snow.py and wind.py had a copy each until v0.120)."""
    if value not in allowed:
        allowed_text = ", ".join(repr(a) for a in allowed)
        raise validation.ValidationError(f"{cells.address(sheet, ref)}: {what} is {value!r} -- expected one of: {allowed_text}")
    return value


# How far a value Excel computed may stand from Woodcore's before the export says so (spec 2026-10-21-restes-issue-69, D-07): relative, past the fifteen digits Excel keeps and well under the three a report prints
SHEET_TOLERANCE = 1e-6


def sheet_differences(cells, sheet, compared, vars_, notes):
    """A sheet of the workbook computes what Woodcore computes from its inputs (snow.py, wind.py): where a value the sheet shows -- `compared`, [(var name, cell)] -- stands apart from Woodcore's (`vars_`), the export says so, naming the cell and the two values (D-07). Woodcore's is the one printed. An empty cell, a cell Excel shows as an error and a var the calculation does not have are no difference."""
    import engine
    if notes is None:
        return
    for name, ref in compared:
        var = vars_.get(name)
        if var is None or not is_number(var.get("value")):
            continue
        try:
            shown = cells.value(sheet, ref, required=False)
        except validation.ValidationError:
            continue
        if not is_number(shown):
            continue
        mine = var["value"]
        if math.isclose(shown, mine, rel_tol=SHEET_TOLERANCE, abs_tol=1e-9):
            continue
        cell = cells.address(sheet, ref)
        notes.append(engine.Note(
            "sheet_value_differs",
            f"{cell}: the sheet gives {name} = {shown:.6g}, Woodcore computes {mine:.6g} from the sheet's inputs -- the report prints Woodcore's",
            cell=cell, name=name, excel=f"{shown:.6g}", woodcore=f"{mine:.6g}"))
