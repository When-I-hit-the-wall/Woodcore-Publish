"""What a call at the level of detail −1 may name in `shown:`, read once for the window (issue #20, v0.117; docs/typst/report-engine.md §4).

`level: -1, shown: (A: 2, W_y: 1)` prints the variables it names, each at its own level, and nothing else of them -- the title always (spec 2026-10-10-issues-github-19-20-21, D-09), a check's verdict where `shown:` names the key of its utilisation, `eta`, `eta_s`… (issue #58). **Which keys a command may name is written once**, in `lib/shown-variables.json`, which lib/calc-engine.typ reads with `json("shown-variables.json")` to refuse a key the command does not print, and which this module reads as a file to give the window its boxes -- the engineer never types a name (T7). Nothing of it is written here, as calc/units.py writes nothing of lib/units.json.

Two commands take their keys from elsewhere: `show-calc` and `show-connector-resistance` print what the export carries, so their keys are the instance's own variables and tables (`export_keys`), and `show-check-member` prints `member` and then the check of its kind, so its keys are those two lists together (`check_member_keys`, D-11: a key both print is the check's).

No Qt here: calc/tools/display_view.py and the tabs read it, and so do the tests.
"""

import json
import re
from pathlib import Path

import greek

SHOWN_FILE = Path(__file__).resolve().parent.parent / "lib" / "shown-variables.json"
# The level that lists what is printed: a level of one call, never of a document (REQ-006)
SELECTION_LEVEL = -1
# The key a table of an export is named by: its place among the instance's tables, from 1 -- a table has a title and no name
TABLE_KEY = "table-%d"
# ... and a drawing of an instance, by its place among the instance's figures (schema 1.5, issues #35-#37)
FIGURE_KEY = "figure-%d"

_loaded = None


def _commands():
    global _loaded
    if _loaded is None:
        _loaded = json.loads(SHOWN_FILE.read_text(encoding="utf-8"))["commands"]
    return _loaded


def commands():
    """The commands lib/shown-variables.json lists, in its order."""
    return list(_commands())


def keys(command):
    """Every key `command` may name in `shown:`, in the order it prints them -- a superset: a key the call does not print is accepted and ignored (D-15)."""
    return list(_commands()[command]["keys"])


def parts(command):
    """{heading: [keys]}: the headings `command` prints from level 2 only, and the keys under each -- printed at -1 where one of them is chosen (D-09)."""
    return {name: list(names) for name, names in _commands()[command]["parts"].items()}


def check_command(record):
    """The verify-* command `show-check-member` calls for a check saved in Woodcore (lib/timber.typ, `show-check-member`): its kind, and for a compression its angle, for a bending and a lateral torsional buckling its normal force. The one place Python decides it -- calc/domains/member_check.py's `draft_typst` and the tests call it (issue #38, ARCH-RISK-101); lib/timber.typ decides it once more, from the same record, and tests/test_member_check.py holds the two equal."""
    kind = record["kind"]
    if kind == "tension":
        return "verify-tension"
    if kind == "shear":
        return "verify-shear"
    if kind in ("bending", "lateral-torsional"):
        n = (record.get("N") or {}).get("value", 0)
        return "verify-bending" if not n else "verify-bending-normal"
    if kind == "buckling":
        return "verify-compression"
    return "verify-compression" if not record.get("alpha") else "verify-compression-perp"


def check_member_keys(record=None, command=None):
    """The keys `show-check-member` may name: `member`'s, then those of the check of its kind, a key both print being the check's (D-11). `record` a check as the export carries it, or `command` the verify-* named."""
    command = command or check_command(record)
    own = keys(command)
    return [key for key in keys("member") if key not in own] + own


def split_check_member(shown, command):
    """`shown` of a `show-check-member` call split as lib/timber.typ splits it: ({member's}, {the check's})."""
    own = set(keys(command))
    return ({k: n for k, n in shown.items() if k not in own}, {k: n for k, n in shown.items() if k in own})


def export_keys(entry):
    """The keys `show-calc` may name for one instance of the export: its variables in the order the data states them, then its tables (`table-1`, …). `entry` the instance's record -- `vars`, `tables`."""
    out = list((entry.get("vars") or {}).keys())
    out += [TABLE_KEY % (i + 1) for i in range(len(entry.get("tables") or ()))]
    figures = entry.get("figures")
    out += [FIGURE_KEY % (i + 1) for i in range(len(figures))] if isinstance(figures, list) else []   # a connector's own `figures` is a dictionary, shown by show-connector
    return out


_SUB = re.compile(r"^([A-Za-z]+)(?:_(.+))?$")


def key_math(key):
    """The math source a key is shown with in the window, beside its box: the base and its subscripts, each Greek name a letter -- `sigma_t_0_d` as `sigma_(t,0,d)`, `lambda_rel_y` as `lambda_("rel",y)`. What the box names, not what the page prints: the page sets the command's own symbol."""
    match = _SUB.match(key)
    if match is None or match.group(2) is None:
        return key
    base, rest = match.group(1), match.group(2).split("_")
    subs = [part if len(part) <= 1 or part.isdigit() or part in greek.LETTERS else '"%s"' % part for part in rest]
    return "%s_(%s)" % (base, ",".join(subs)) if len(subs) > 1 else "%s_%s" % (base, subs[0])


# The files of the export a show-calc instance is read from, by domain (lib/calc-engine.typ, `resolve-source`): a connector's and a connection's calculation are their own files, every load's is calculations.json
_EXPORT_FILES = {"connector": ("connectors.json", "connectors"), "connection": ("connections.json", "connections")}


def export_entry(data_dir, domain, instance):
    """The record of one instance of the export, as show-calc reads it -- None where the export does not hold it (not exported yet, or not readable)."""
    name, key = _EXPORT_FILES.get(domain, ("calculations.json", None))
    try:
        data = json.loads((Path(data_dir) / name).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    holder = data.get(key) if key else (data.get("domains") or {}).get(domain, {}).get("instances")
    entry = (holder or {}).get(instance)
    return entry if isinstance(entry, dict) else None


def export_choices(data_dir, domain, instance):
    """The boxes the window offers for a show-calc or a show-connector-resistance of one instance: [(key, words, math)] -- a var by its own symbol, a table by its title -- or [] where the export does not hold it."""
    entry = export_entry(data_dir, domain, instance)
    if entry is None:
        return []
    out = [(key, None, (var or {}).get("symbol") or key_math(key)) for key, var in (entry.get("vars") or {}).items()]
    out += [(TABLE_KEY % (i + 1), table.get("title") or TABLE_KEY % (i + 1), None) for i, table in enumerate(entry.get("tables") or ())]
    figures = entry.get("figures")
    out += [(FIGURE_KEY % (i + 1), figure.get("title") or FIGURE_KEY % (i + 1), None) for i, figure in enumerate(figures)] if isinstance(figures, list) else []
    return out
