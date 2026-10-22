"""The level of detail each line of a calculation is printed from, read out of `lib/line-levels.json` for Python (spec docs/requirements/completed/2026-10-20-indices-et-niveaux.md, UI-002, ARCH-002, D-13).

Typst reads the same file when it prints (lib/calc-engine-core.typ, `line-level`; lib/timber.typ, `timber-at`): **the level of a line is written there and nowhere else** -- until v0.120 each domain wrote it as a literal into its export (`level=1`, `level=3` …), a second place to set it, which the audit of 19.10.2026 named. Nothing of the table is written here, as calc/units.py writes nothing of lib/units.json.

`level(domain, key, role="var", kind=None, own=None)` follows the rule docs/typst/report-engine.md §4 states, the same as Typst's: the table's level for the line (its kind's, else the domain's, else a pattern's), else what the line carries in the export (`own`: an export written before v0.120, a domain written by hand), else the domain's `*`; None where nothing gives one. tests/test_line_levels.py holds the two readers equal.
"""

import functools
import json
import re
from pathlib import Path

TABLE_FILE = Path(__file__).resolve().parent.parent / "lib" / "line-levels.json"
ROLES = ("var", "step", "check")


@functools.lru_cache(maxsize=1)
def table():
    """The table's `domains`, read once."""
    return json.loads(TABLE_FILE.read_text(encoding="utf-8"))["domains"]


def domains():
    """The domains the table holds, in its order."""
    return list(table())


def _entry(domain, key, kind):
    d = table().get(domain)
    if d is None:
        return None
    if kind is not None and key in (d.get("kinds") or {}).get(kind, {}):
        return d["kinds"][kind][key]
    if key in (d.get("lines") or {}):
        return d["lines"][key]
    for pattern, level in (d.get("patterns") or {}).items():
        if re.search(pattern, key):
            return level
    return None


def level(domain, key, role="var", kind=None, own=None):
    """The level `key` of `domain` is printed from, as `role` (a var, the step producing it, a check): the table's, else `own`, else the domain's `*`, else None."""
    if role not in ROLES:
        raise ValueError("role is one of %s -- got %r" % (", ".join(ROLES), role))
    entry = _entry(domain, key, kind)
    if isinstance(entry, dict):
        entry = entry.get(role)   # a role it does not name falls through to the line's own
    if entry is not None:
        return entry
    if own is not None:
        return own
    return (table().get(domain) or {}).get("*")


def keys(domain):
    """Every key the table names for `domain`, its kinds' included -- not the patterns'."""
    d = table().get(domain) or {}
    out = list(d.get("lines") or {})
    for lines in (d.get("kinds") or {}).values():
        out += [k for k in lines if k not in out]
    return out
