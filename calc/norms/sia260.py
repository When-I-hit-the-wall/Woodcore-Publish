"""The values of SIA 260:2013 this project reads, out of the JSON files beside this module in `calc/norms/` (docs/architecture/layout.md §11).

`calc/norms/` is the one source of every value taken from a norm for a calculation made in Python: the numbers live in the JSON, once, and the code that needs them reads them through here. Every number was transcribed by hand from `ExternalFiles/000-Normes/SIA260-2013-DE.pdf`, and the file's `_source` says at which page (section 2 rule 13).

One file per table, named `<norm>-<year>-<table>-<designation>.json`:

    sia260-2013-tab02-reduktionsbeiwerte.json   Anhang A, Tabelle 2, the Reduktionsbeiwerte ψ0, ψ1 and ψ2 of buildings (p. 33) -- kept for the load combinations to come (section 3.5), which map a category of Tabelle 8 of SIA 261 to its row with `live_load_psi`. **No live-load table and no instance of the live-load domain carries them**: the engineer's rule of 01.10.2026 is that ψ is never shown for live loads

What a Reduktionsbeiwert is, in the norm's own words (1.2.4, p. 18; 3.2.3.2 to 3.2.3.4, p. 23): ψ0 scales a variable action to the *seltener Wert* it takes beside a leading variable action, ψ1 to its *häufiger Wert* and ψ2 to its *quasi-ständiger Wert*. They are the factors a load combination will pick (SIA 260 4.4.3, equations (16) to (23)) -- which is why they are read here, where the category they belong to is known, and not in the combination, where it is not (section 3.5).

⚠️ **Snow is a formula, not a number.** The norm prints «1 – 60/h0», «1 – 250/h0» and «1 – 1000/h0», and they are transcribed as printed and never evaluated here: a snow ψ depends on the site's Bezugshöhe h0, which is the snow-load calculation's own `h_ref`, and the day a combination wants the number it is that calculation's to give. The file keeps the formula's shape (`c`, the one constant that differs) beside the text the norm prints, so that a later evaluation reads a number and never parses a string.

The file is hand-written -- the one place in the pipeline where a number is transcribed rather than read -- so it is checked here before anything is built from it: a factor outside 0 to 1, a ψ that grows from ψ0 to ψ2 (the rare value is never the smaller), a category missing, a formula whose constant disagrees with the text beside it. A norm table that contradicts itself must stop the export naming the line, exactly as a defective workbook cell does.
"""

import json
import re
from pathlib import Path

import validation

HERE = Path(__file__).resolve().parent

TAB02 = "sia260-2013-tab02-reduktionsbeiwerte"
FILES = (TAB02,)

EDITION = "SIA 260:2013"

# The three factors of a row, in the order the norm prints them and the order of their indices.
PSI = ("psi_0", "psi_1", "psi_2")

# The eight categories of Nutzlasten and Verkehrslasten in Gebäuden, which are the rows a category of SIA 261 Tabelle 8 reaches, and the rows of every other action the table gives.
LIVE_LOAD_ROWS = ("A", "B", "C", "D", "E", "F", "G", "H")
OTHER_ROWS = ("snow", "wind", "temperature", "earth-pressure", "water-pressure")
# The one row whose cells are formulas (in h0); every other cell is a number.
FORMULA_ROWS = ("snow",)

# A category of SIA 261 Tabelle 8 is one letter of SIA 260 Tabelle 2, which Tabelle 8 subdivides: A1, A2 and A3 are category A, C1 to C3 category C (the engineer's reading, and the practice -- the norm states no other).
CATEGORY = re.compile(r"^([A-Z])\d*$")

_cache = {}


def _fail(name, what):
    raise validation.ValidationError("calc/norms/%s.json: %s" % (name, what))


def _read(name, check):
    """One file, read once and checked once."""
    if name in _cache:
        return _cache[name]
    path = HERE / (name + ".json")
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        _fail(name, "not found at %s -- the values of SIA 260 live in calc/norms/" % path)
    except json.JSONDecodeError as exc:
        _fail(name, "is not valid JSON: %s" % exc)
    if data.get("edition") != EDITION:
        _fail(name, "edition is %r -- expected %r" % (data.get("edition"), EDITION))
    check(name, data)
    _cache[name] = data
    return data


# --- Tabelle 2, the Reduktionsbeiwerte --------------------------------------------

def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _check_formula_cell(name, where, cell, symbol):
    for key in ("printed", "formula"):
        if not isinstance(cell.get(key), str) or not cell[key].strip():
            _fail(name, "%s: the formula cell has no '%s' -- the text the norm prints, and the same in plain text" % (where, key))
    constant = cell.get("c")
    if not _is_number(constant) or constant <= 0:
        _fail(name, "%s: the formula's constant 'c' is %r -- expected a positive number" % (where, constant))
    # the text and the constant say one thing or the transcription contradicts itself: «1 - 60 / h_0» is c = 60
    expected = "1 - %g / %s" % (constant, symbol)
    if cell["formula"] != expected:
        _fail(name, "%s: the formula is %r but its constant says %r" % (where, cell["formula"], expected))
    if str(int(constant) if float(constant).is_integer() else constant) not in cell["printed"]:
        _fail(name, "%s: the printed text %r does not carry the constant %s" % (where, cell["printed"], constant))


def _check_table_2(name, data):
    table = data.get("table_2")
    if not isinstance(table, dict):
        _fail(name, "no 'table_2'")
    for key in ("number", "title", "norm", "norm_ref", "annex", "symbols", "rows"):
        if not table.get(key):
            _fail(name, "table_2 has no '%s'" % key)

    symbols = table["symbols"]
    if tuple(symbols) != PSI:
        _fail(name, "table_2 names the symbols %s -- expected %s, in that order" % (list(symbols), ", ".join(PSI)))
    for symbol, entry in symbols.items():
        if not isinstance(entry.get("label"), str) or not entry["label"].strip():
            _fail(name, "%s has no label -- the norm's own words for it (1.2.4)" % symbol)
        defined = entry.get("defined_in")
        if not isinstance(defined, list) or not defined or any(not isinstance(c, str) or not c.strip() for c in defined):
            _fail(name, "%s: 'defined_in' must list the clauses that define it" % symbol)

    seen = set()
    for index, row in enumerate(table["rows"], start=1):
        where = "row %d (%s)" % (index, row.get("id"))
        row_id = row.get("id")
        if not isinstance(row_id, str) or not row_id.strip():
            _fail(name, "%s: no id" % where)
        if row_id in seen:
            _fail(name, "%s: the id is listed twice -- one row per action" % where)
        seen.add(row_id)
        if not isinstance(row.get("name"), str) or not row["name"].strip():
            _fail(name, "%s: no name" % where)
        if "group" not in row or (row["group"] is not None and not isinstance(row["group"], str)):
            _fail(name, "%s: 'group' must be the heading the row stands under, or null" % where)

        is_formula = "variable" in row
        if is_formula != (row_id in FORMULA_ROWS):
            _fail(name, "%s: %s -- the norm prints a formula in the row %s and a number everywhere else"
                  % (where, "carries a formula" if is_formula else "carries numbers", ", ".join(FORMULA_ROWS)))
        if is_formula:
            variable = row["variable"]
            for key in ("symbol", "name", "unit", "norm", "norm_ref"):
                if not isinstance(variable.get(key), str) or not variable[key].strip():
                    _fail(name, "%s: the variable has no '%s'" % (where, key))
            constants = []
            for psi in PSI:
                cell = row.get(psi)
                if not isinstance(cell, dict):
                    _fail(name, "%s: %s is %r -- expected the formula the norm prints" % (where, psi, cell))
                _check_formula_cell(name, "%s %s" % (where, psi), cell, variable["symbol"])
                constants.append(cell["c"])
            # ψ0 >= ψ1 >= ψ2 for every h0: the constants must grow
            if not constants[0] < constants[1] < constants[2]:
                _fail(name, "%s: the constants %s do not grow from ψ0 to ψ2 -- the rare value would be the smaller" % (where, constants))
        else:
            values = []
            for psi in PSI:
                value = row.get(psi)
                if not _is_number(value):
                    _fail(name, "%s: %s is %r -- expected a number" % (where, psi, value))
                if not 0 <= value <= 1:
                    _fail(name, "%s: %s is %s -- a Reduktionsbeiwert lies between 0 and 1" % (where, psi, value))
                values.append(value)
            if not values[0] >= values[1] >= values[2]:
                _fail(name, "%s: ψ0, ψ1, ψ2 = %s -- the rare value is never the smaller of the three" % (where, values))

    missing = [r for r in LIVE_LOAD_ROWS + OTHER_ROWS if r not in seen]
    if missing:
        _fail(name, "table_2 lacks the rows %s" % ", ".join(missing))


def edition():
    """The edition every value read here belongs to, "SIA 260:2013" -- cited in the report and recorded in each var's `source` (docs/project/purpose.md §1bis)."""
    return _read(TAB02, _check_table_2)["edition"]


def table_2():
    """Tabelle 2 as the file states it: its title, its citation, the symbols and one row per action."""
    return _read(TAB02, _check_table_2)["table_2"]


def symbols():
    """ψ0, ψ1 and ψ2 with the norm's own words for each and the clauses that define it: {"psi_0": {label, defined_in}, ...}."""
    return table_2()["symbols"]


def rows():
    """Every row of Tabelle 2, in the norm's own order."""
    return table_2()["rows"]


def row(row_id):
    """The row `row_id` of Tabelle 2 -- a category "A" to "H", or "snow", "wind", "temperature", "earth-pressure", "water-pressure"; KeyError naming the ids there are where it has none."""
    for line in rows():
        if line["id"] == row_id:
            return line
    raise KeyError("SIA 260 Tabelle 2 has no row %r -- it has %s" % (row_id, ", ".join(l["id"] for l in rows())))


def psi(row_id):
    """The three factors of a row of numbers, as {"psi_0": ..., "psi_1": ..., "psi_2": ...}.

    Snow is a formula in h0 and has no number to give: asking for it is refused, saying so, rather than returning something the norm does not state (see the module's docstring).
    """
    line = row(row_id)
    if "variable" in line:
        raise ValueError("SIA 260 Tabelle 2 gives %r as a formula in %s, not a number -- read it with sia260.snow()"
                         % (row_id, line["variable"]["symbol"]))
    return {key: line[key] for key in PSI}


def snow():
    """The snow row as the norm prints it: the variable h0, and for each ψ the printed text, the plain-text formula and its constant -- nothing evaluated."""
    return row("snow")


def live_load_row(category):
    """The row of Tabelle 2 a category of SIA 261 Tabelle 8 belongs to: A1, A2 and A3 to "A", C1 to C3 to "C", and B, D, E, F, G and H to themselves. KeyError naming the rows there are where the category matches none."""
    match = CATEGORY.match(category) if isinstance(category, str) else None
    if match is None or match.group(1) not in LIVE_LOAD_ROWS:
        raise KeyError("%r is no category of SIA 261 Tabelle 8 that SIA 260 Tabelle 2 has a row for -- it has %s"
                       % (category, ", ".join(LIVE_LOAD_ROWS)))
    return match.group(1)


def live_load_psi(category):
    """The three factors of a category of SIA 261 Tabelle 8 (A1, B, C2, H, ...), as {"psi_0": ..., "psi_1": ..., "psi_2": ...}."""
    return psi(live_load_row(category))


def check_all():
    """Read and check every file, for a test or for an export that wants to fail early rather than at the first lookup."""
    table_2()
    return edition()
