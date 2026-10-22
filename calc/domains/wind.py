"""Wind load of the `WL-*` sheets of the Belastungsannahmen workbooks: their inputs read, the load computed by Woodcore (spec 2026-10-21-restes-issue-69, REQ-002, ARCH-002; docs/domain/loads.md §3.3quater).

Until v0.120 a `WL-*` sheet *was* the wind calculation, and this module read the cells Excel had computed -- the profile, q_p, the reduction factors off the sheet's scroll bars, the six global forces --, enveloping the local forces from the sheet's own block of pressure coefficients. The engineer, 21.10.2026: the workbook gives the inputs only. A sheet is now read for what the engineer enters on it -- q_p0 (J6), the building's b, d, h (J7 to J9), the terrain category (I11), the table of Annexe C (F40), c_d (J60) -- and the load is computed by `wind_source.build_instance`, the code a wind load entered in Woodcore is computed by: c_red from Figur 9 and the rule of 6.3.3 (D-08), every coefficient from calc/norms/. Each input keeps the cell it was read from as its provenance.

**What the sheet computed is compared, never printed** (D-07): z_g, alpha_r, z, c_h, q_p, the two c_red and the global forces under their new names (`loads_names.wind_compared`), and the sheet's block of pressure coefficients row by row, where its wind direction is one of the table's -- a value apart from Woodcore's is said by the export, naming the cell and the two values. A direction the table does not list is said too: nothing of that row is compared.

**The workbook's words.** The terrain category is the first word of the label I11 shows («IV grossflächige Stadtgebiete» -> IV), the Dropdowns' table of z_g and alpha_r held to SIA 261 Tableau 4 (`_terrain`). The names of the values are the source's -- `qk_max_cf1` where the sheet said `qk_max_bh` --, which a project's sections, scripts and sources are migrated to when it is opened (domains/loads_names.py, CON-002).
"""

import math

import engine
import validation
from domains import wind_source
from domains._common import SHEET_TOLERANCE, is_number, require_one_of, sheet_differences
from domains.loads_names import wind_compared
from norms import sia261_wind

DOMAIN = wind_source.DOMAIN
LABEL = "Windlast"
ENGINE = "python"   # computed by Woodcore since v0.120, from the sheet's inputs (REQ-002)
SHEET_PREFIX = "WL"
ACTION = "variable"  # SIA 260: a variable action (Q), as opposed to a permanent one (G) -- docs/domain/calculation-domains.md §3.3
NORM = "SIA 261"

# The terrain categories of the workbook's own Dropdowns sheet, with the Gradientenhöhe and Bodenrauigkeit each one implies: read for the labels the engineer picks from in Excel, their numbers held to the norm (`_terrain`).
TERRAIN_TABLE = ("Dropdowns", {"kat": "B", "zg": "C", "ar": "D"}, 91, 94)

# Where each field of a source is read on a sheet: what a refusal names, and each input's provenance
CELLS = {"q_p0": "J6", "b": "J7", "d": "J8", "h": "J9", "terrain": "I11", "table": "F40", "c_d": "J60"}

# The sheet's block of pressure coefficients (spilled in from 'Wind Tabellen Werte'): a header row, then one row per wind direction, the direction in column B -- compared with the table of Annexe C row by row (D-07)
COEFFICIENT_HEADER_ROW = 77
DIRECTION_ROWS = (78, 79, 80, 81)
DIRECTION_COLUMN = "B"
# The sheet's column of each coefficient, and the table's column key: the four walls and the four roof zones (c_pe), the openings (c_pi)
COEFFICIENT_COLUMNS = (("C", "cpe:A"), ("D", "cpe:B"), ("E", "cpe:C"), ("F", "cpe:D"), ("G", "cpe:E"), ("H", "cpe:F"), ("I", "cpe:G"), ("J", "cpe:H"),
                       ("M", "cpi:A"), ("N", "cpi:B"), ("O", "cpi:C"), ("P", "cpi:D"))
# glm. (+) and glm. (-): the pair the table writes as one cell of uniformly distributed openings
UNIFORM_COLUMNS = (("K", 0), ("L", 1))


def _terrain(rows):
    """The workbook's terrain categories, its own labels («IV grossflächige Stadtgebiete»), each with z_g and alpha_r as SIA 261 Tableau 4 gives them (calc/norms/, REQ-003): the category is the label's first word, and a row of the workbook giving another number than the norm stops the import, naming the cell."""
    out = []
    for row, r in rows:
        if r["kat"] in (None, ""):
            continue
        norm = sia261_wind.terrain(str(r["kat"]).split()[0])
        for key, held in (("zg", norm["z_g"]), ("ar", norm["alpha_r"])):
            if not isinstance(r[key], (int, float)) or abs(r[key] - held) > 1e-9:
                raise validation.ValidationError(
                    f"{TERRAIN_TABLE[0]}!{TERRAIN_TABLE[1][key]}{row}: {r['kat']!r} gives {r[key]!r} -- SIA 261 Tableau 4 gives {held:g} (calc/norms/)")
        out.append((row, {"kat": r["kat"], "zg": norm["z_g"], "ar": norm["alpha_r"]}))
    return out


def read_source(cells, sheet):
    """The sheet's inputs as a wind-load source, and where each was read, `(src, {field: "excel:<cell>"})` -- every field checked by the source's own rules, a refusal naming the cell (wind_source.check_fields)."""
    def at(field):
        return cells.value(sheet, CELLS[field])

    labels = [r["kat"] for _, r in _terrain(cells.rows(*TERRAIN_TABLE))]
    terrain = require_one_of(cells, at("terrain"), labels, sheet, CELLS["terrain"], "Geländekategorie")
    table = at("table")
    src = {"schema_version": wind_source.SOURCE_SCHEMA_VERSION, "id": sheet,
           "q_p0": at("q_p0"), "terrain": str(terrain).split()[0], "b": at("b"), "d": at("d"), "h": at("h"), "z": None,
           "table": ("%d" % table) if is_number(table) and table == int(table) else str(table), "c_d": at("c_d")}

    def fail(field, message):
        raise validation.ValidationError(f"{cells.address(sheet, CELLS.get(field, ''))}: {message}")
    wind_source.check_fields(src, fail)
    return src, {field: "excel:%s" % cells.address(sheet, ref) for field, ref in CELLS.items()}


def _coefficient_differences(cells, sheet, table, notes):
    """The sheet's pressure coefficients against the table of Annexe C, row by row where the sheet's wind direction is one the table lists (D-07): a coefficient apart is said with its cell, a direction the table does not list once. Nothing is printed from the sheet."""
    columns = {c["key"]: i for i, c in enumerate(table["columns"])}
    rows = {str(row["label"]): row for row in table["rows"]}
    for r in DIRECTION_ROWS:
        direction = cells.at(sheet, DIRECTION_COLUMN, r, required=False)
        if direction in (None, ""):
            continue
        row = rows.get(str(direction))
        if row is None:
            cell = cells.address(sheet, f"{DIRECTION_COLUMN}{r}")
            notes.append(engine.Note("sheet_direction_unknown", f"{cell}: the wind direction {direction!r} is not one of Tableau {table['number']} -- its coefficients are not compared",
                                     cell=cell, direction=str(direction), table=table["number"]))
            continue
        pairs = [(column, row["values"][columns[key]]) for column, key in COEFFICIENT_COLUMNS if key in columns]
        uniform = row["values"][columns["cpi:rep"]] if "cpi:rep" in columns else None
        for column, index in UNIFORM_COLUMNS:
            held = uniform[index] if isinstance(uniform, list) and len(uniform) > index else (uniform if index == 0 else None)
            pairs.append((column, held))
        for column, held in pairs:
            if not is_number(held):
                continue
            try:
                shown = cells.value(sheet, f"{column}{r}", required=False)
            except validation.ValidationError:
                continue
            if not is_number(shown) or math.isclose(shown, held, rel_tol=SHEET_TOLERANCE, abs_tol=1e-9):
                continue
            cell = cells.address(sheet, f"{column}{r}")
            name = "%s (%s)" % (cells.at(sheet, column, COEFFICIENT_HEADER_ROW, required=False), direction)
            notes.append(engine.Note("sheet_value_differs", f"{cell}: the sheet gives {name} = {shown:.6g}, SIA 261 Tableau {table['number']} gives {held:.6g} -- the report prints the norm's",
                                     cell=cell, name=name, excel=f"{shown:.6g}", woodcore=f"{held:.6g}"))


def read_instance(cells, sheet, notes=None):
    """One WL-* sheet, one instance of the wind-load domain (docs/domain/calculation-domains.md §3.3): its inputs read (`read_source`), computed by `wind_source.build_instance`, compared with what the sheet computed (D-07)."""
    src, inputs = read_source(cells, sheet)
    instance = wind_source.build_instance(src, inputs=inputs)
    if notes is not None:
        sheet_differences(cells, sheet, wind_compared(src["table"]), instance["vars"], notes)
        _coefficient_differences(cells, sheet, sia261_wind.table(src["table"]), notes)
        notes.extend(wind_source.notes_of(src, cells.address(sheet)))
    return {"sheet": sheet, **instance}


def read_instances(cells, sheets, notes=None):
    """Every WL-* sheet of one workbook, in tab order, keyed by sheet name; what is worth saying about one goes into `notes` (engine.Note)."""
    return {sheet: read_instance(cells, sheet, notes) for sheet in sheets}
