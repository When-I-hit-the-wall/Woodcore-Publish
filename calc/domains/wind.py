"""Wind load, transcribed from the `WL-*` sheets of the Belastungsannahmen workbooks.

The same arrangement as snow.py, and for the same reason (docs/domain/loads.md §3.3quater, §3.3bis, docs/decisions.md §13): a `WL-*` sheet *is* the wind calculation -- it owns the reference wind pressure, the terrain category and the profile, the reduction and force coefficients, and the global wind forces they produce -- so what the sheet computes is read here, never recomputed. Every var comes out of a cell Excel already computed, and each formula is carried as a display string (section 6bis) beside the value the sheet computed with it.

The one piece of arithmetic below is the envelope of the local wind forces, and only because the sheet does not compute it. Its «Lokale Windkräfte» block combines the pressure coefficients for the single wind direction (G85) and opening (G86) the engineer has selected there; the report prints from level 2, for every surface and every opening case, the largest and the smallest value over all of the sheet's wind directions. That is the sheet's own formula, q_k = q_p · (c_pe - c_pi), applied to the sheet's own coefficient block -- and checked against the sheet's block wherever it shows a selection, so it cannot quietly turn into a second implementation of it.

One sheet, one instance -- `WL` in one workbook, `WL-Velo` and `WL-Pavillon` in another. Copying a sheet (`WL-Halle`) adds that case to the report with no edit here, exactly as for the snow and dead-load sheets.

What makes this domain different from snow is its *answer*: a global wind force is not one number but six -- a maximum and a minimum for each of the three reference areas (b*h, d*h, d*b), which are three different loads on three different faces and never alternatives to one another. So the formula is printed once in letters and its results as a table, the six result vars being the cells of that table (section 3.3, `value` columns).

Two things this module deliberately does not do, both spelled out in section 3.3quater: it does not read the force coefficients c_f the six forces are built from, and it does not correct `L70`, whose minimum the sheet computes from the reduction factor instead of the Staudruck -- `ENGINE` is `excel`, so what is printed is what the sheet computed.
"""

import math
import sys

import engine
import validation

DOMAIN = "wind-load"
LABEL = "Windlast"
ENGINE = "excel"
SHEET_PREFIX = "WL"
ACTION = "variable"  # SIA 260: a variable action (Q), as opposed to a permanent one (G) -- docs/domain/calculation-domains.md §3.3
NORM = "SIA 261"
# Where the one table computed here, rather than read, records that it was (docs/architecture/principles.md §2, rule 5): the domain's engine is Excel, the local-force envelope is not.
SOURCE = "python:domains/wind.py"

# The terrain categories, with the Gradientenhöhe and Bodenrauigkeit each one implies -- read off the workbook's own Dropdowns sheet rather than restated here, so a report footnote cannot disagree with the list the engineer picks from in Excel.
TERRAIN_TABLE = ("Dropdowns", {"kat": "B", "zg": "C", "ar": "D"}, 91, 94)

# The three reference areas the sheet computes a global wind force for, in its own column order (J/K/L), and the two rows it computes for each (row 69 = maximum, row 70 = minimum).
AREAS = (
    ("bh", "J", "b·h"),
    ("dh", "K", "d·h"),
    ("db", "L", "d·b"),
)
AREA_ROWS = (("max", 69, "Maximale"), ("min", 70, "Minimale"))

# The pressure coefficients of the figure chosen in F40 ("Druckbeiwerte"), which the sheet spills in from 'Wind Tabellen Werte': a header row, then one row per wind direction. Always four rows, but not always the same four directions -- most figures list 0°, 15°, 45° and 90°, figure 42 lists 180° instead of 45° -- so they are read from column B, never assumed.
FIGURE_CELL = "F40"
COEFFICIENT_HEADER_ROW = 77
DIRECTION_ROWS = (78, 79, 80, 81)
DIRECTION_COLUMN = "B"

# The surfaces an external pressure coefficient c_pe is given for, in the sheet's column order (C-J): the four walls, then the four roof zones -- named as the sheet's own «Lokale Windkräfte» block names them.
SURFACES = (
    ("Wand", "A", "C"), ("Wand", "B", "D"), ("Wand", "C", "E"), ("Wand", "D", "F"),
    ("Dach", "E", "G"), ("Dach", "F", "H"), ("Dach", "G", "I"), ("Dach", "H", "J"),
)

# The internal pressure coefficient c_pi of each opening the sheet offers (K-P), headed exactly as its «Undicht auf der Seite» dropdown lists them. The figures that give a single value for uniformly distributed openings in some direction leave the second one blank, so that column alone may be empty.
OPENINGS = (
    ("glm. (+)", "K"), ("glm. (-)", "L"),
    ("A", "M"), ("B", "N"), ("C", "O"), ("D", "P"),
)
OPTIONAL_OPENINGS = {"glm. (-)"}

# The opening cases the report prints, and which of the sheet's c_pi each one envelopes. Uniformly distributed openings take both of the sheet's values, since either internal pressure can occur; a dominant opening in a wall takes that wall's own.
OPENING_CASES = (
    ("gleichmässig", ("glm. (+)", "glm. (-)")),
    ("Öffnung A", ("A",)),
    ("Öffnung B", ("B",)),
    ("Öffnung C", ("C",)),
    ("Öffnung D", ("D",)),
)

# The sheet's own «Lokale Windkräfte» block: the selection it combines the coefficients for, then one row per surface, the surface's letter in E and its q_k in F. "keine" (no opening) combines c_pe alone.
SELECTED_DIRECTION = "G85"
SELECTED_OPENING = "G86"
NO_OPENING = "keine"
SHEET_FORCE_ROWS = (90, 91, 92, 93, 95, 96, 97, 98)


def _require_one_of(cells, value, allowed, sheet, ref, what):
    if value not in allowed:
        allowed_text = ", ".join(repr(a) for a in allowed)
        raise validation.ValidationError(
            f"{cells.address(sheet, ref)}: {what} is {value!r} -- "
            f"expected one of: {allowed_text}"
        )


def _force_table(sheet):
    """The six global wind forces as the report prints them: the formula in letters once, and its results as a table of three reference areas by two rows.

    The cells of the three area columns are `value` cells -- they name the result vars rather than repeating their numbers, so the table cannot drift from the vars it shows (docs/architecture/principles.md §2, rule 1) and show-calc knows not to set those vars out on rows of their own as well. Shown from level 1, and *below* the values: unlike the dead load's build-up, which is the working behind its sums, this table is the answer.
    """
    return {
        "title": "Globale Windkräfte",
        "level": 1,
        "place": "below",
        "formula": 'q_k = c_"red" dot c_d dot c_f dot q_p',
        "norm": NORM,
        "norm_ref": "6.3",
        # A symbol in a note is written between dollars, as it is in a formula (docs/typst/language.md §4bis): the report sets what stands between them as real math, so c_red reads as a symbol where "cred" read as three letters. The reference areas b·h, d·h and d·b are left as words, being the names the table's own column headers carry.
        "note": "Bezugsflächen aus den Gebäudeabmessungen: b·h und d·h sind "
                "die Fassadenflächen quer bzw. längs zur Windrichtung, d·b "
                "die Dachfläche. $c_f$ ist der grösste bzw. kleinste globale "
                "Kraftbeiwert über alle Windrichtungen (Blatt " + sheet
                + ", Tabelle «Globale Kraftbeiwerte»); $c_\"red\"$ ist der "
                "Reduktionsfaktor der jeweiligen Bezugsfläche. Negative "
                "Werte sind Sog.",
        "columns": [
            {"label": "Globale Windkraft", "kind": "wide", "unit": "kN/m²"},
            {"label": "", "kind": "math"},
        ] + [
            {"label": label, "kind": "value", "group": "Bezugsfläche"}
            for _, _, label in AREAS
        ],
        "rows": [
            [f"{word.lower()} globale Windkraft", "q_k ="]
            + [f"qk_{kind}_{area}" for area, _, _ in AREAS]
            for kind, _, word in AREA_ROWS
        ],
    }


def _number(cells, sheet, ref, value, what, required=True):
    """`value` if it is a number, None if it is empty and may be; anything else stops the export naming the cell -- these values are computed with here, not merely printed."""
    if value is None and not required:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise validation.ValidationError(
            f"{cells.address(sheet, ref)}: {what} is {value!r} -- expected a number"
        )
    return value


def _read_coefficients(cells, sheet):
    """The sheet's pressure coefficients as [(direction, c_pe by surface, c_pi by opening), ...], one entry per direction row, in the sheet's order.

    The header row is checked against the columns read, so a reorganised block stops the export by name instead of feeding the envelope another surface's coefficients. A list rather than a dict keyed by direction: two rows carrying the same label would otherwise silently merge, and the envelope lose one of them.
    """
    headers = [(column, surface) for _, surface, column in SURFACES]
    headers += [(column, opening) for opening, column in OPENINGS]
    for column, expected in headers:
        found = cells.at(sheet, column, COEFFICIENT_HEADER_ROW)
        if found != expected:
            raise validation.ValidationError(
                f"{cells.address(sheet, f'{column}{COEFFICIENT_HEADER_ROW}')} is "
                f"headed {found!r} where {expected!r} was expected -- the "
                f"pressure-coefficient block moved, follow it in domains/wind.py"
            )

    def coefficient(column, row, required=True):
        ref = f"{column}{row}"
        return _number(cells, sheet, ref, cells.value(sheet, ref, required=required),
                       "pressure coefficient", required=required)

    return [
        (
            cells.at(sheet, DIRECTION_COLUMN, row),
            {surface: coefficient(column, row) for _, surface, column in SURFACES},
            {opening: coefficient(column, row, opening not in OPTIONAL_OPENINGS)
             for opening, column in OPENINGS},
        )
        for row in DIRECTION_ROWS
    ]


def _local_force(qp, c_pe, c_pi):
    """The sheet's own combination of external and internal pressure, `q_k = q_p · (c_pe - c_pi)` (its cell E88), in the one place both the envelope and the check against the sheet compute it."""
    return qp * (c_pe - c_pi)


def _envelope(qp, coefficients, surface, openings):
    """(largest, smallest) q_k on one surface, over every direction the sheet lists and every c_pi the opening case takes -- a blank c_pi being a combination the figure does not give."""
    values = [
        _local_force(qp, cpe[surface], cpi[opening])
        for _, cpe, cpi in coefficients
        for opening in openings
        if cpi[opening] is not None
    ]
    return max(values), min(values)


def _check_against_sheet(cells, sheet, qp, coefficients):
    """The sheet's own «Lokale Windkräfte» block combines the coefficients for one selected direction and opening. Where it shows numbers, each has to be what `_local_force` gives for that selection -- which is what makes the envelope the sheet's formula applied to the sheet's coefficients, rather than a second implementation that could drift from it.

    Nothing selected is nothing to compare, and passes. A selection the sheet shows as an Excel error (a direction the chosen figure does not list, say) cannot be compared either; it is reported and the check skipped, since those cells are not printed -- only a disagreement between two numbers stops the export.
    """
    direction = cells.value(sheet, SELECTED_DIRECTION, required=False)
    opening = cells.value(sheet, SELECTED_OPENING, required=False)
    if direction is None or opening is None:
        return
    # Excel's MATCH takes the first row carrying the direction; so does this.
    chosen = next(((cpe, cpi) for d, cpe, cpi in coefficients if d == direction), None)
    # How many of the eight surfaces could actually be compared. A surface the sheet shows nothing for is skipped rather than ending the check: until v0.59 the first such row returned, and the seven after it went unchecked behind a single warning that did not say so.
    checked = []
    skipped = []
    for row in SHEET_FORCE_ROWS:
        surface = cells.at(sheet, "E", row)
        ref = f"F{row}"
        try:
            shown = cells.value(sheet, ref, required=False)
        except validation.ValidationError:
            shown = None  # an Excel error: the selection does not resolve on this sheet
        expected = None
        if chosen is not None and surface in chosen[0]:
            c_pi = 0 if opening == NO_OPENING else chosen[1].get(opening)
            if c_pi is not None:
                expected = _local_force(qp, chosen[0][surface], c_pi)
        if isinstance(shown, bool) or not isinstance(shown, (int, float)) or expected is None:
            skipped.append(str(surface))
            continue
        if not math.isclose(shown, expected, rel_tol=1e-9, abs_tol=1e-12):
            raise validation.ValidationError(
                f"{cells.address(sheet, ref)}: the sheet gives q_k = {shown:.6g} "
                f"kN/m² on surface {surface} for {direction} / {opening}, but "
                f"q_p · (c_pe - c_pi) from its own coefficients gives "
                f"{expected:.6g} -- either the workbook was saved without "
                f"recalculating (recalculate in Excel and save), or the sheet's "
                f"formula or its coefficient block changed (follow it in "
                f"domains/wind.py)"
            )
        checked.append(str(surface))

    # Said with the count either way, so a check that covered two surfaces out of eight cannot be read as a check that passed.
    if skipped:
        print(
            f"wind: WARNING {cells.address(sheet)} shows no local wind force for "
            f"the selection {direction} / {opening} on "
            f"{len(skipped)} of {len(SHEET_FORCE_ROWS)} surfaces "
            f"({', '.join(skipped)}) -- the envelope was checked against the "
            f"sheet's own block on the other {len(checked)} "
            f"({', '.join(checked) if checked else 'none'})",
            file=sys.stderr,
        )


def _local_table(cells, sheet, qp, coefficients):
    """The local wind forces as the report prints them: for every surface, and for every opening case, the largest and the smallest q_k over all of the sheet's wind directions. From level 2, and below the values -- the engineer's report shows them beside the global forces, set after them the way the sheet sets its «Lokale Windkräfte» after its «Globale Windkräfte».

    The cells are plain numbers, not vars: eighty values nobody quotes one at a time, which the table is the one place of. The table's `source` says they were computed here rather than read.
    """
    figure = cells.value(sheet, FIGURE_CELL)
    directions = ", ".join(str(d) for d, _, _ in coefficients)
    return {
        "title": "Lokale Windkräfte",
        "level": 2,
        "place": "below",
        "formula": 'q_k = q_p dot (c_"pe" - c_"pi")',
        "norm": NORM,
        "norm_ref": "6.3",
        "source": SOURCE,
        "note": f"Grösster (max) und kleinster (min) Wert je Fläche über die "
                f"Windrichtungen {directions}, mit den Aussen- und "
                f"Innendruckbeiwerten $c_\"pe\"$ und $c_\"pi\"$ des Blatts {sheet} "
                f"(Druckbeiwerte {figure}). gleichmässig: gleichmässig "
                f"verteilte Öffnungen, beide Innendruckbeiwerte des Blatts "
                f"(glm. (+) und glm. (-)) berücksichtigt; Öffnung A–D: "
                f"dominante Öffnung in der Wand A, B, C bzw. D. Negative "
                f"Werte sind Sog.",
        "columns": [
            {"label": "Lokale Windkraft", "kind": "wide", "unit": "kN/m²"},
        ] + [
            {"label": bound, "kind": "number", "group": case}
            for case, _ in OPENING_CASES
            for bound in ("max", "min")
        ],
        "rows": [
            [f"{part} {surface}"] + [
                value
                for _, openings in OPENING_CASES
                for value in _envelope(qp, coefficients, surface, openings)
            ]
            for part, surface, _ in SURFACES
        ],
    }


def read_instance(cells, sheet):
    """Reads one WL-* sheet into one instance of the wind-load domain (docs/domain/calculation-domains.md §3.3): the {sheet, results, tables, vars, steps, checks} shape every calculation instance has.
    """
    calc = engine.Calculation()

    def add(name, ref, symbol, unit, label, level, norm_ref,
            description=None, choices=None, group=None, group_label=None):
        """One cell -> one traced var. `group_label` is what puts the sheet's own row label in front of the value ("Gradientenhöhe: z_g = 450 m"): a var row otherwise prints the symbol alone, which for a profile coefficient says too little.
        """
        value = cells.value(sheet, ref)
        calc.add_var(
            name=name, value=value, unit=unit, symbol=symbol, label=label,
            level=level, source=f"excel:{cells.address(sheet, ref)}", norm=NORM,
            norm_ref=norm_ref, description=description, choices=choices,
            group=group, group_label=group_label,
        )
        return value

    # The vars are added in the order the report prints them, not in cell order (docs/typst/api-conventions.md §10bis), and their levels are what splits the three reports (section 3.7): level 1 is the terrain category and the global wind forces, level 2 adds the local wind forces (a table, its level set in _local_table), level 3 the whole sheet.

    # --- Referenzwert des Staudrucks und Gebäudegeometrie ------------------
    add("qp0", "J6", "q_(p 0)", "kN/m²", "Referenzwert des Staudrucks",
        3, "Anhang E",
        description="Referenzwert des Staudrucks am Standort nach SIA 261.")
    add("b", "J7", "b", "m", "Gebäudelänge", 3, "6.3", group="geometrie",
        group_label="Gebäude Geometrie")
    add("d", "J8", "d", "m", "Gebäudebreite", 3, "6.3", group="geometrie")
    add("h", "J9", "h", "m", "Gebäudehöhe", 3, "6.3", group="geometrie")

    # --- Geländekategorie und Windprofil -----------------------------------
    # The category is the one entry the rest of the profile follows from: the sheet looks its Gradientenhöhe and Bodenrauigkeit up from the same Dropdowns table the choices below are read from.
    terrain = cells.rows(*TERRAIN_TABLE)
    # The two symbols are written between dollars, as in the notes above: the report sets what stands between them as real math (docs/typst/language.md §4bis). The category itself -- "IV grossflächige Stadtgebiete" -- is the German the workbook's own list carries, and the glossary translates it where it is printed, the norm naming these four categories in its Tabelle 4.
    terrain_choices = [
        {"value": r["kat"],
         "desc": f"$z_g$ = {r['zg']:g} m, $alpha_r$ = {r['ar']:g}"}
        for _, r in terrain
    ]
    kategorie = add(
        "gelaendekategorie", "I11", '"Geländekategorie"', "",
        "Geländekategorie", 1, "6.2", choices=terrain_choices,
        description="Die Geländekategorie bestimmt die Gradientenhöhe und die "
                    "Bodenrauigkeit des Windprofils.",
    )
    _require_one_of(cells, kategorie, [r["kat"] for _, r in terrain], sheet,
                    "I11", "Geländekategorie")

    add("zg", "J12", "z_g", "m", "Gradientenhöhe", 3, "6.2",
        group_label="Gradientenhöhe")
    add("alpha_r", "J13", "alpha_r", "", "Bodenrauigkeit", 3, "6.2",
        group_label="Bodenrauigkeit")
    add("z", "J14", "z", "m", "Höhe über Boden", 3, "6.2",
        group_label="Höhe über Boden",
        description="Höhe über Boden, für die der Staudruck bestimmt wird; "
                    "die Norm setzt sie mindestens zu 5 m an (10 m in "
                    "Geländekategorie IV).")
    add("ch", "J15", "c_h", "", "Windprofilbeiwert", 3, "6.2 (11)",
        group_label="Windprofilbeiwert")

    # --- Reduktionsfaktoren und dynamischer Faktor -------------------------
    add("cred_bh", "J19", 'c_("red", "b/h")', "", "Reduktionsfaktor b", 3,
        "6.3", group_label="Reduktionsfaktor b",
        description="Reduktionsfaktor für die Bezugsfläche b·h, aus dem "
                    "Verhältnis Länge (b) zu Höhe (h).")
    add("cred_dh", "J20", 'c_("red", "d/h")', "", "Reduktionsfaktor d", 3,
        "6.3", group_label="Reduktionsfaktor d",
        description="Reduktionsfaktor für die Bezugsfläche d·h, aus dem "
                    "Verhältnis Breite (d) zu Höhe (h).")
    add("cd", "J60", "c_d", "", "Dynamischer Faktor", 3, "6.3",
        group_label="dynamischer Faktor")

    # --- Staudruck ---------------------------------------------------------
    # The Staudruck is the value every global wind force is built from, and the sheet sets it apart accordingly (it restates it in its own «Globale Windkräfte» block, J62). `bold` says so here: it is an answer of its own, even though the calculation's results are the six forces below.
    qp = _number(cells, sheet, "J17",
                 add("qp", "J17", "q_p", "kN/m²", "Staudruck", 3, "6.2 (12)"),
                 "Staudruck")
    calc.add_step(
        name="Staudruck", level=3, result="qp", uses=["ch", "qp0"],
        formula="q_p = c_h dot q_(p 0)", bold=True,
        norm=NORM, norm_ref="6.2 (12)",
    )

    # --- Globale Windkräfte ------------------------------------------------
    # Six results, not one: a maximum and a minimum per reference area. They are the cells of the instance's force table (`value` columns), which is where the report prints them -- so they carry no step, the formula in letters being carried by the table itself.
    results = []
    for area, column, area_label in AREAS:
        for kind, row, word in AREA_ROWS:
            name = f"qk_{kind}_{area}"
            add(name, f"{column}{row}", f'q_(k,"{kind}","{area_label}")',
                "kN/m²", f"{word} globale Windkraft, Bezugsfläche {area_label}",
                1, "6.3")
            results.append(name)

    # --- Lokale Windkräfte -------------------------------------------------
    # The combination of external and internal pressure per surface, enveloped over the sheet's wind directions -- a table of its own after the global forces, from level 2. Checked against the sheet's own block first, so a formula that changed there stops the export instead of printing numbers the sheet would not give.
    coefficients = _read_coefficients(cells, sheet)
    _check_against_sheet(cells, sheet, qp, coefficients)

    return {
        "sheet": sheet,
        "results": results,
        "tables": [
            _force_table(sheet),
            _local_table(cells, sheet, qp, coefficients),
        ],
        **calc.to_dict(),
    }


def read_instances(cells, sheets):
    """Every WL-* sheet of one workbook, in tab order, keyed by sheet name."""
    return {sheet: read_instance(cells, sheet) for sheet in sheets}
