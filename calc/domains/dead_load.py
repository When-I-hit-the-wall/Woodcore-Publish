"""Permanent loads (Eigenlast + Auflast), calculated here from the layer build-up entered on the `EL+AL-*` sheets of the Belastungsannahmen workbooks.

The opposite arrangement to snow.py, and deliberately so (docs/decisions.md §13). An `EL+AL-*` sheet is a *table*: one row per layer, carrying what the engineer chose -- material, thickness, width, spacing -- while the load column beside it is Excel arithmetic. So Excel here is the input form and Python is the calculation: every number below is computed from the raw entries, and not one value is read out of a formula cell.

Which side owns a calculation stays a per-domain decision, recorded in each var's `source`: snow says `excel:...`, everything here says `python:domains/dead_load.py`.

Two things follow from Python doing the arithmetic:

* The specific weight is looked up here, in the workbook's own material library, instead of being read from the sheet's XLOOKUP column. That also settles a real defect: `EL+AL-Dach2.ohnePV` was copied from another file and its lookups still point at a workbook that is not there (`[5]!Tabelle2`), so its cached weights cannot be trusted.
* The only cell read below the layer table is the *Gewählt* value, the rounded permanent load the engineer decided to design with. That is an entry, not a result -- so it is read, not recomputed, and it is what the report shows as the final result.

Per layer, reproducing the sheet's own K column exactly:

    load [kN/m2] = rho * Dicke * Breite / (Dist. * 100)

The `/100` is the workbook's kg -> kN conversion (g taken as 10 m/s2). A material given in kg/m2 rather than kg/m3 needs no special case: those rows carry Dicke = Breite = Dist. = 1, so the formula degenerates to rho/100 on its own.
"""

import math

import engine
import validation

DOMAIN = "dead-load"
LABEL = "Eigen- und Auflasten"
ENGINE = "python"
SHEET_PREFIX = "EL+AL"
ACTION = "permanent"  # SIA 260: a permanent action (G), as opposed to a variable one (Q) -- docs/domain/calculation-domains.md §3.3
NORM = "SIA 261"
NORM_REF = "Anhang A"

SOURCE = "python:domains/dead_load.py"

# The workbook's material library (its Excel table `Tabelle2` plus the project-specific rows the engineer adds above it -- both scanned, since the declared table range does not cover the latter).
MATERIAL_SHEET = "Material (hier ergänzen)"
MATERIAL_FIRST_ROW = 4
MATERIAL_COLUMNS = {"ebene": "A", "material": "B", "mass": "C", "unit": "D"}

# The layer table: header row, then one row per layer until the `Total` line. Neither the first nor the last row is pinned -- a facade has fewer layers than a roof, so `Total` moves. Both are found by their label.
HEADER_COLUMN, HEADER_TEXT = "C", "Ebene"
TOTAL_COLUMN, TOTAL_TEXT = "J", "Total"
CHOSEN_COLUMN, CHOSEN_TEXT = "D", "Ständige Lasten"
CHOSEN_VALUE_COLUMN = "J"

LAYER_COLUMNS = {
    "kind": "B",       # gk (Eigenlast) or ak (Auflast)
    "ebene": "D",      # layer role, e.g. Dachhaut
    "material": "E",   # keys the material library
    "dicke": "F",      # m
    "breite": "G",     # m
    "dist": "H",       # m
    "load": "K",       # kN/m² -- the sheet's own arithmetic, read only on a row that names no material (DIRECT_LOAD)
}

# What the table's material column says of a row whose load was typed straight into column K, naming no material: the Belastungsannahmen template 3.2 does it for «Installationen und Innenwände», 0.5 kN/m². The sheet counts such a row; until the periodic audit of 260916 this export skipped it, and a_k came out 0.5 kN/m² short with no word (AUD-2-2). A glossary term, so a French report says it in French.
DIRECT_LOAD = "Direkt eingegebene Last"

# The sheet's own specific-weight column: an XLOOKUP into the material library. Nothing here reads its value -- the weight is looked up against the library directly (see the module docstring) -- but its *formula* is read, to catch a cell whose lookup was typed over (`_check_weight_formula`).
WEIGHT_COLUMN = "I"

KIND_DEAD, KIND_IMPOSED = "gk", "ak"
KINDS = (KIND_DEAD, KIND_IMPOSED)

# kg -> kN, as the workbook does it
KG_TO_KN = 100.0


class MaterialLibrary:
    """The workbook's material list, looked up the way a layer row is actually keyed.

    The library lists a material once per `Ebene` it can appear under, and those repeats do not always agree: `Gartenplatten` weighs 2200 kg/m3 as a *Beschichtung* and 2000 as a *Beschwerung*. Excel's own XLOOKUP keys on the material name alone and silently takes the first hit, which is a coin toss between the two.

    A layer row names both its Ebene and its material, so the exact pair is used first and the name alone only as a fallback -- and that fallback refuses to guess when the name really is ambiguous. Rows of the library nobody uses are never resolved, so an inconsistency the project does not touch cannot block an export.

    One library per workbook, holding that workbook's reader: a build-up is weighed against the library of the file it was entered in, never against another load workbook's, whose list may differ.
    """

    def __init__(self, cells, by_pair, by_name):
        self._cells = cells
        self._by_pair = by_pair
        self._by_name = by_name

    def lookup(self, ebene, material, sheet, row):
        exact = self._by_pair.get((ebene, material))
        if exact is not None and len(exact) == 1:
            return next(iter(exact))

        where = self._cells.address(sheet, f"E{row}")
        entries = self._by_name.get(material)
        if not entries:
            raise validation.ValidationError(
                f"{where}: material "
                f"{material!r} is not in the '{MATERIAL_SHEET}' library -- "
                f"add it there, or correct the layer"
            )
        if len(entries) > 1:
            listed = ", ".join(f"{m:g} {u}" for m, u in sorted(entries))
            raise validation.ValidationError(
                f"{where}: material "
                f"{material!r} under Ebene {ebene!r} is listed in the "
                f"'{MATERIAL_SHEET}' library with several different weights "
                f"({listed}) and none of them under that Ebene -- Excel's "
                f"lookup would take one at random, so fix the library or the "
                f"layer's Ebene"
            )
        return next(iter(entries))


def read_materials(cells):
    """Reads the material library into a MaterialLibrary."""
    by_pair, by_name = {}, {}
    rows = cells.rows(
        MATERIAL_SHEET, MATERIAL_COLUMNS,
        MATERIAL_FIRST_ROW, cells.max_row(MATERIAL_SHEET),
    )
    for _, r in rows:
        name, mass, unit = r["material"], r["mass"], r["unit"]
        # the library repeats its own header row; a row without a numeric weight carries no material either way
        if not name or not isinstance(mass, (int, float)):
            continue
        entry = (float(mass), str(unit or "").strip())
        by_pair.setdefault((str(r["ebene"] or ""), name), set()).add(entry)
        by_name.setdefault(name, set()).add(entry)
    return MaterialLibrary(cells, by_pair, by_name)


def _number(cells, value, sheet, ref, what):
    if not isinstance(value, (int, float)):
        raise validation.ValidationError(
            f"{cells.address(sheet, ref)}: {what} is {value!r} -- "
            f"expected a number"
        )
    return float(value)


def _check_weight_formula(cells, sheet, row, material, mass):
    """Refuses a layer whose specific weight was typed over the sheet's own lookup.

    Column I is an XLOOKUP into the material library, and this module deliberately does not read it: the weight is looked up here instead, keyed on (Ebene, Material), because a copied sheet's lookups cannot be trusted (see the module docstring). That makes one thing invisible, though -- a cell whose formula has been *replaced by a number*. The material named in column E then says one thing and the number beside it another, and since Python follows the name, the report prints a load the sheet does not show.

    It is not hypothetical: on `EL+AL-Dach ohne Wasser` (v0.59) both `I9` and `K9` had been typed over with 100 and 1, to get a dry Dachbegrünung, while `E9` went on naming the wet one at 160 kg/m². The build-up in the report came to 2.412 kN/m², the sheet showed 1.812, and nothing said why.

    The fix is always in Excel and always the same: give the library a row for the material actually meant, name *that* row in column E, and restore the formula in column I. What is refused here is the shortcut, not the value.
    """
    formula = cells.formula(sheet, f"{WEIGHT_COLUMN}{row}")
    # A real lookup is a formula; anything else is a literal somebody typed.
    if isinstance(formula, str) and formula.lstrip().startswith("="):
        return
    if formula is None or not isinstance(formula, (int, float)) or isinstance(formula, bool):
        return
    if math.isclose(float(formula), mass, rel_tol=1e-9, abs_tol=1e-9):
        return
    raise validation.ValidationError(
        f"{cells.address(sheet, f'{WEIGHT_COLUMN}{row}')}: holds the number "
        f"{formula:g} instead of its lookup, while column E names "
        f"{material!r}, which the '{MATERIAL_SHEET}' library lists at {mass:g}. "
        f"The name and the number say different things, and this export follows "
        f"the name -- so the report would print a load the sheet does not show. "
        f"Add the material actually meant to the library, name it in "
        f"{cells.address(sheet, f'E{row}')}, and put the lookup formula back"
    )


def _read_layers(cells, sheet, materials):
    """Every layer row that carries a material or a load of its own, as [{kind, ebene, material, dicke, breite, dist, mass, unit, load}, ...].

    A row with an empty material column is skipped, exactly as the sheet's own `IF(E="", "", ...)` does -- those are the placeholder lines the form leaves in place for layers this build-up does not use -- **unless a number was typed into its load column K**, which the sheet then counts and so does this export (DIRECT_LOAD): its load is the one typed, and it has no thickness, width, spacing or weight.
    """
    header = cells.find_row(sheet, HEADER_COLUMN, HEADER_TEXT)
    total = cells.find_row(sheet, TOTAL_COLUMN, TOTAL_TEXT, first=header + 1)

    layers = []
    for row, r in cells.rows(sheet, LAYER_COLUMNS, header + 1, total - 1):
        if not r["material"]:
            typed = r.get("load")
            if not isinstance(typed, (int, float)) or isinstance(typed, bool):
                continue
            kind = str(r["kind"] or "").strip()
            if kind not in KINDS:
                raise validation.ValidationError(
                    f"{cells.address(sheet, f'B{row}')}: layer type is "
                    f"{kind!r} -- expected 'gk' (Eigenlast) or 'ak' (Auflast); "
                    f"the row names no material and carries a load typed in K{row}"
                )
            layers.append({
                "row": row, "kind": kind, "ebene": str(r["ebene"] or ""),
                "material": DIRECT_LOAD, "dicke": None, "breite": None,
                "dist": None, "mass": None, "unit": "", "load": float(typed),
            })
            continue
        material = str(r["material"])
        ebene = str(r["ebene"] or "")
        mass, unit = materials.lookup(ebene, material, sheet, row)
        _check_weight_formula(cells, sheet, row, material, mass)
        kind = str(r["kind"] or "").strip()
        if kind not in KINDS:
            raise validation.ValidationError(
                f"{cells.address(sheet, f'B{row}')}: layer type is "
                f"{kind!r} -- expected 'gk' (Eigenlast) or 'ak' (Auflast)"
            )
        dicke = _number(cells, r["dicke"], sheet, f"F{row}", "Dicke")
        breite = _number(cells, r["breite"], sheet, f"G{row}", "Breite")
        dist = _number(cells, r["dist"], sheet, f"H{row}", "Dist.")
        if dist == 0:
            raise validation.ValidationError(
                f"{cells.address(sheet, f'H{row}')}: Dist. is 0 for "
                f"layer {material!r} -- it divides the layer's load"
            )
        layers.append({
            "row": row, "kind": kind, "ebene": ebene,
            "material": material, "dicke": dicke, "breite": breite,
            "dist": dist, "mass": mass, "unit": unit,
            "load": mass * dicke * breite / (dist * KG_TO_KN),
        })

    if not layers:
        raise validation.ValidationError(
            f"{cells.address(sheet)}: no layer row carries a "
            f"material or a load -- nothing to build a permanent load from"
        )
    return layers


# The symbol each layer counts towards, printed in the table's first column as real math rather than as the sheet's own "gk"/"ak" shorthand.
KIND_SYMBOLS = {KIND_DEAD: "g_k", KIND_IMPOSED: "a_k"}

# The workbook writes a specific weight's unit flat ("kg/m3"), which reads as a factor of three next to a column of decimals. Only the exponent differs between the two units the library uses, so it is lifted here rather than parsed.
UNIT_SUPERSCRIPTS = {"2": "²", "3": "³"}


def _weight_text(mass, unit):
    """A layer's specific weight as the table prints it: 500 kg/m3 -> 500 kg/m³."""
    text = str(unit or "").strip()
    if text and text[-1] in UNIT_SUPERSCRIPTS:
        text = text[:-1] + UNIT_SUPERSCRIPTS[text[-1]]
    return f"{mass:g} {text}".strip()


def _layer_table(layers, gk, ak):
    """The build-up as a table for the report, shown at level 3 *above* the sums it explains (docs/domain/loads.md §3.3ter). Values stay numbers; Typst rounds and formats them.

    Each column says what it holds -- `math` (Typst math source, evaluated like any other symbol), `wide` (the one column that should take the leftover width), `text`, `number` -- and the display layer turns that into a width and a rendering. A column's content is a property of the calculation; how wide it ends up is not, which is why only the former is stated here.

    The two `totals` rows are what replaced the sums' formulas: `g_k` and `a_k` are the totals of the rows carrying that symbol, which the table can simply show, instead of a Sigma formula above it restating in letters what the rows already list.
    """
    # A column's unit is a field of its own, never typed into its label: the header then sets as "Dicke" over "[m]" instead of on one line, which is what lets a column of two-decimal numbers be as narrow as its own name (docs/domain/calculation-domains.md §3.3). Same rule as every var's `unit` -- the unit is data, its brackets are display.
    def column(label, kind, unit=""):
        return {"label": label, "kind": kind, "unit": unit}

    return {
        "title": "Schichtaufbau",
        "source": SOURCE,
        "note": "Last je Schicht = spez. Gewicht · Dicke · Breite / "
                "(Dist. · 100); der Faktor 100 rechnet kg in kN um. "
                "Flächenbezogene Materialien (kg/m²) sind mit "
                "Dicke = Breite = Dist. = 1 erfasst.",
        "columns": [
            column("Type", "math"),
            column("Ebene", "text"),
            column("Material", "wide"),
            column("Dicke", "number", unit="m"),
            column("Breite", "number", unit="m"),
            column("Dist.", "number", unit="m"),
            column("Gewicht", "number"),
            column("Last", "number", unit="kN/m²"),
        ],
        "rows": [
            [
                KIND_SYMBOLS[layer["kind"]], layer["ebene"], layer["material"],
                *(("", "", "", "") if layer["mass"] is None else (
                    layer["dicke"], layer["breite"], layer["dist"], _weight_text(layer["mass"], layer["unit"]))),
                layer["load"],
            ]
            for layer in layers
        ],
        "totals": [
            [KIND_SYMBOLS[KIND_DEAD], "Total", "Eigengewicht", "", "", "", "", gk],
            [KIND_SYMBOLS[KIND_IMPOSED], "Total", "Auflast", "", "", "", "", ak],
        ],
    }


# How far below the computed sum a chosen value may sit before it is refused. Not zero: the engineer rounds, and a build-up that sums to 1.2004 may legitimately be designed with 1.2. A tenth of a percent covers the rounding and nothing else -- a layer left in the table by mistake is out by whole percents, as `EL+AL-Dach ohne Wasser` was (2.412 summed, 1.900 chosen, v0.59).
CHOSEN_TOLERANCE = 1e-3


def _check_chosen(cells, sheet, ref, chosen, computed):
    """The *Gewählt* value is the permanent load the design is carried out with, and the report prints the Schichtaufbau table above it: the table has to lead to the number.

    It is an entry and not a result -- the engineer rounds the computed sum up, on the safe side -- so it is read rather than recomputed. What cannot happen is a chosen value *below* the sum of the layers it is chosen from: the level-3 table then adds up to one number and the bold line under it states another, and a checker cannot follow the one to the other. That is the defect a copied sheet produces -- a layer of the original build-up left in place, compensated by hand in this cell instead of being removed from the table -- and it is the same class as the Dachformbeiwert a copied SL sheet reports (domains/snow.py's _check_mu_helper, docs/domain/loads.md §3.3bis): a value that is wrong in a way nothing on the page gives away.

    Rounding up is the normal case and passes; equal passes; below by more than the rounding stops the export naming the cell and both numbers.
    """
    if computed <= 0 or chosen >= computed * (1 - CHOSEN_TOLERANCE):
        return
    raise validation.ValidationError(
        f"{cells.address(sheet, ref)}: the chosen permanent load is "
        f"{chosen:.3f} kN/m², below the {computed:.3f} kN/m² its own layers add "
        f"up to ({(1 - chosen / computed) * 100:.1f}% less) -- the report prints "
        f"that build-up above this value, so the table would not lead to the "
        f"number. Either a layer of the table does not belong to this build-up "
        f"(a sheet copied from another and not edited: remove or correct the "
        f"layer in column E), or the chosen value is too low. Round up, never down"
    )


def read_instance(cells, sheet, materials):
    """Reads one EL+AL-* sheet into one instance of the dead-load domain (docs/domain/calculation-domains.md §3.3): the {sheet, results, tables, vars, steps, checks} shape every calculation instance has.
    """
    layers = _read_layers(cells, sheet, materials)
    gk = sum(l["load"] for l in layers if l["kind"] == KIND_DEAD)
    ak = sum(l["load"] for l in layers if l["kind"] == KIND_IMPOSED)

    chosen_row = cells.find_row(sheet, CHOSEN_COLUMN, CHOSEN_TEXT)
    chosen_ref = f"{CHOSEN_VALUE_COLUMN}{chosen_row}"
    chosen = _number(
        cells, cells.value(sheet, chosen_ref), sheet, chosen_ref,
        "gewählte ständige Last",
    )
    _check_chosen(cells, sheet, chosen_ref, chosen, gk + ak)
    instance = instance_from_layers(layers, chosen, f"excel:{cells.address(sheet, chosen_ref)}",
                                    "Auf der sicheren Seite gerundeter Bemessungswert der ständigen Lasten, im Blatt " + sheet + " gewählt.")
    return {"sheet": sheet, **instance}


def instance_from_layers(layers, chosen, chosen_source, chosen_description, source=SOURCE, note=None):
    """One instance of the domain from its layers -- [{kind, ebene, material, dicke, breite, dist, mass, unit, load}], lengths in m, load in kN/m² -- and the chosen value: g_k, a_k, their sum and the chosen value as vars, the build-up as the table above them. The one place the sums are made, for a sheet of the workbook (`read_instance`) and for a build-up entered in Woodcore (domains/dead_load_source.py, issue #35): two readers, one arithmetic. `chosen` None takes the sum itself, read as the result."""
    gk = sum(l["load"] for l in layers if l["kind"] == KIND_DEAD)
    ak = sum(l["load"] for l in layers if l["kind"] == KIND_IMPOSED)
    calc = engine.Calculation()

    def add(name, value, symbol, label, level, source, description=None):
        calc.add_var(
            name=name, value=value, unit="kN/m²", symbol=symbol, label=label,
            level=level, source=source, norm=NORM, norm_ref=NORM_REF,
            description=description,
        )

    # The level split, decided here rather than in the display code (docs/typst/api-conventions.md §10bis): every level from 2 up prints g_k, a_k, g_k + a_k and the gewählt value as four plain lines -- the four numbers an engineer reads off an Aufbau -- and level 3 adds the Schichtaufbau table above them.
    #
    # Neither sum carries a formula. A Sigma over the layers would state in letters exactly what the table below it lists row by row, and the table now carries the two sums itself as its `totals` rows, where each stands directly under the column it adds up. The steps stay, formula or not: they are what records that these vars are calculated (their norm, their source) rather than entered.
    add("gk", gk, "g_k", "Eigengewicht (Flächenlast)", 2, source)
    calc.add_step(
        name="Eigengewicht", level=2, result="gk", uses=[],
        norm=NORM, norm_ref=NORM_REF,
    )

    add("ak", ak, "a_k", "Auflast (Flächenlast)", 2, source)
    calc.add_step(
        name="Auflast", level=2, result="ak", uses=[],
        norm=NORM, norm_ref=NORM_REF,
    )

    # No formula: the sum of two symbols that are printed right above it would only restate them as `g_k + a_k = g_k + a_k`.
    add("gk_ak", gk + ak, "g_k + a_k", "Summe (berechnet)", 2, source)
    calc.add_step(
        name="Summe", level=2, result="gk_ak", uses=["gk", "ak"],
        norm=NORM, norm_ref=NORM_REF,
    )

    if chosen is not None:
        # An entry, not a result: the engineer rounds the computed sum up to the value the design is actually carried out with, so it is read as entered and shown as this instance's final result.
        calc.add_var(
            name="gk_ak_gew", value=chosen, unit="kN/m²",
            symbol='(g_k + a_k)_"gew"', label="Ständige Lasten, gewählt",
            level=1, source=chosen_source,
            norm=NORM, norm_ref="2.1",
            description=chosen_description,
        )
        calc.add_step(
            name="Ständige Lasten", level=1, result="gk_ak_gew", uses=["gk_ak"],
            norm=NORM, norm_ref="2.1",
        )
    table = _layer_table(layers, gk, ak)
    if note is not None:
        table["note"] = note
    table["source"] = source
    return {
        "results": ["gk_ak_gew" if chosen is not None else "gk_ak"],
        "tables": [table],
        **calc.to_dict(),
    }


def read_instances(cells, sheets):
    """Every EL+AL-* sheet of one workbook, in tab order, keyed by sheet name. The material library is read once and shared -- it is one table for the whole workbook, not per build-up, and registry.py calls this once per workbook, so each workbook's build-ups use that workbook's own library.
    """
    materials = read_materials(cells)
    return {sheet: read_instance(cells, sheet, materials) for sheet in sheets}
