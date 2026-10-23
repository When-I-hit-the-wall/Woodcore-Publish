"""The arguments a line of a domain's file is displayed by -- what the engineer sets in «Affichage» and Woodcore's writing keeps (spec 2026-10-22-onglet-neige-type, D-17, ARCH-012, ARCH-RISK-F03).

A line Woodcore writes into a domain's file (`#var`, `#eq`, `#verify`) carries what the export says -- its key, its value, its unit, its formula, its label, its citation -- and how it is printed. **How it is printed is the engineer's**: the fine arguments of its command (`fine-keys`), its `style`, its `role` and its `level`. The base of a domain's lines (calc/domains/unfold.py) compares a line without them and writes a line of the export with the file's own, so that a line set in «Affichage» keeps its setting through every export and only its value is refreshed. The list is read from lib/display-presets.json, where lib/formula.typ reads it too: one list for the two (`fine-values`, `fine-keys`). What the export writes itself -- an `#eq`'s formula, unit, label, description -- is not in it: changed by hand, such a line becomes the engineer's (`local`) and is never refreshed in silence.
"""

import json
from pathlib import Path

PRESETS = Path(__file__).resolve().parent.parent / "lib" / "display-presets.json"
# Beside the fine arguments: the line's emphasis, its role and its level. `#verify` has no `style:` (lib/formula.typ: its double rule says whether the relation holds).
EXTRA = {"var": ("style", "role", "level"), "eq": ("style", "role", "level"), "verify": ("role", "level")}

_cache = {}


def _read():
    if "data" not in _cache:
        _cache["data"] = json.loads(PRESETS.read_text(encoding="utf-8"))
    return _cache["data"]


def fine_values():
    """{argument: the values it takes} -- lib/display-presets.json `fine-values`."""
    return {name: tuple(values) for name, values in _read()["fine-values"].items()}


def display_args(command):
    """The arguments a line of `command` (var, eq, verify) is displayed by, in the order «Affichage» offers them: its fine arguments, then style, role and level. () for a command that has none."""
    keys = _read()["fine-keys"].get(command)
    if keys is None or command not in EXTRA:
        return ()
    return tuple(keys) + EXTRA[command]
