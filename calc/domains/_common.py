"""The few helpers every domain module wrote for itself (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, G4).

The audit of 19.10.2026 found `_fail` in sixteen modules, `_number` in ten, in two meanings -- a test (is it a number) and a check (it must be one, refused naming the field otherwise) -- each copy free to word its refusal its own way. They are written once here; a module imports them under the names it always called them by (`from domains._common import fail as _fail`), so not one call changed. Qt-free and importing nothing of the domains, so any module of calc/ may read it.
"""

import math
from pathlib import Path

import validation
from number_text import exact as plain  # the one trimming of a number (calc/number_text.py, UI-003): six decimals, the load formulas' constants

# The key of the result of a member check and of a steel check -- the utilisation η, the last `#eq` of every check's file (member_check, steel_check) -- written once here and read by the «Variables» tab, which marks it a result in each source that recalls the check (spec 2026-10-24-onglet-variables-groupes, REQ-004, ARCH-012): a check declares no `results` in checks.json or steel.json. tests/test_variable_calc.py holds it to the last `#eq` of every check file of the example.
RESULT_KEY = "eta"


def fail(where, message):
    """The refusal of a source or an export: `<where>: <message>`, `where` the file and the field (CLAUDE.md: a defect stops the export, naming both)."""
    raise validation.ValidationError(f"{where}: {message}")


def fail_first(problems, fail):
    """`fail(field, sentence)` on the first of a domain's `problems` [(field, code, params, sentence)], nothing where there is none: what a load's `check_fields` does with its `_problems` -- the snow's and the wind's (spec 2026-10-23-onglet-vent-briques, REQ-009), one rule written once."""
    for field, _code, _params, sentence in problems:
        fail(field, sentence)
        return


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
