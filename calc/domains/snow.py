"""Snow load, transcribed from the `SL-*` sheets of the Belastungsannahmen workbooks.

Nothing is calculated here (docs/domain/loads.md §3.3bis, docs/decisions.md §13). An `SL-*` sheet *is* the snow calculation -- it owns the location, the correction from SIA 261 Annex D, the coefficients and the load model -- and Python's whole job is to read the cells Excel already computed and give them the traced var/step shape the report displays. There is deliberately no arithmetic below: every number comes out of a cell, and each formula is carried as a display string (docs/typst/report-engine.md §6bis) next to the value the sheet computed with it.

One sheet, one instance of the domain: `SL-Dach1` (a flat roof, one q_k) and `SL-Dach2` (a Sheddach, load model 2, three) are two cases of the same calculation, not two unrelated loads. Copying the sheet in Excel adds a case -- the prefix below is all that ties it to this module.

Cell addresses are pinned as constants: an SL sheet is a form, not a table, so a value moving to another row has to be followed here -- io_excel's CellReader turns an emptied or errored cell into a blocking export error rather than a silently empty load.

Two things a value read on its own cannot tell, both refused loudly rather than exported: a load the sheet computed in a cell nothing here reads (`_check_all_results_read`), and a Dachformbeiwert computed from another sheet's roof (`_check_mu_helper`).
"""

import re

import engine
import validation

DOMAIN = "snow-load"
LABEL = "Schneelast"
ENGINE = "excel"
SHEET_PREFIX = "SL"
ACTION = "variable"  # SIA 260: a variable action (Q), as opposed to a permanent one (G) -- docs/domain/calculation-domains.md §3.3
NORM = "SIA 261"

# Lookup tables on the workbook's own `Dropdowns` sheet -- read rather than restated here, so a report footnote can never disagree with the choices the engineer actually sees in Excel.
EXPOSURE_TABLE = ("Dropdowns", "B24:C26")     # Windexposition -> C_e
CORRECTION_TABLE = ("Dropdowns", "B30:C34")   # label -> Hoehenzuschlag [m]
LOAD_MODEL_LIST = ("Dropdowns", "I44:I48")    # Dachform / Lastmodell

FLAT_ROOF = "Flachdach"
HEIGHT_JUMP_VALUES = ("Ja", "Nein")
SLIDING_POSSIBLE = "möglich"
SLIDING_VALUES = (SLIDING_POSSIBLE, "behindert oder erschwert")

# Every cell an SL sheet can put a characteristic load in. Which of them carries a value is the sheet's own `IF(F21=...)` decision, so the load model never has to be named here: a cell that holds a number is one of this case's results. One that holds a number and is *not* read below is a design load the engineer entered and the report would never show -- refused by name rather than dropped (`_check_all_results_read`).
RESULT_CELLS = ("I37", "I38", "I39", "N37", "N38")

# The Dachformbeiwerte need not be computed on the SL sheet: as the workbook stands, `H26`/`H27` read them off a helper block on `Dropdowns`, and only that block's *formulas* say whose geometry went in ('SL-Dach1'!H23). That block is one block for the whole workbook, so a copied sheet keeps computing its shape coefficients from the original's Dachneigungen while displaying its own -- a wrong design load with nothing on the page to give it away, which is exactly what a value read on its own cannot catch.
#
# So a mu is read only once the cell holding it has been shown to be this sheet's: `_check_mu_helper` follows the sheet's own formula and, where it does reach into the shared block, requires the block to be anchored here. A sheet given its own mu formulas references no helper at all and is checked against nothing -- the guard is on the sharing, not on the arrangement.
MU_HELPER_SHEET = "Dropdowns"
MU_HELPER_FLAT = ("C57", "C58")      # L, B -> C59/C60 -> F61 -> mu_11
MU_11_CELL = "F64"                   # alpha_1 -> mu_11
MU_12_CELL = "F65"                   # alpha_2 -> mu_12
MU_2M_CELL = "F66"                   # alpha_1, alpha_2 -> mu_2m, the Sheddach accumulation

# A sheet reference in an Excel formula: quoted where the name needs it ('SL-Dach1'!H23), bare where it does not (Dropdowns!F61).
_SHEET_REF = re.compile(r"'([^']+)'!|([A-Za-z0-9_.]+)!")


def _require_one_of(cells, value, allowed, sheet, ref, what):
    if value not in allowed:
        allowed_text = ", ".join(repr(a) for a in allowed)
        raise validation.ValidationError(
            f"{cells.address(sheet, ref)}: {what} is {value!r} -- "
            f"expected one of: {allowed_text}"
        )


def _check_mu_helper(cells, sheet, mu_ref, refs):
    """Checks that `sheet`'s `mu_ref` cell reports `sheet`'s own geometry.

    Does nothing unless that cell actually reaches into the shared helper block: a sheet carrying its own mu formulas has nothing to verify. Where it does, the helper cells `refs` behind it are read as *formulas*, since the value of a cell shared by every sheet says nothing about whose geometry produced it. Anything else would export a Dachformbeiwert belonging to another roof, printed next to this roof's Dachneigungen.
    """
    if MU_HELPER_SHEET not in str(cells.formula(sheet, mu_ref) or ""):
        return
    for ref in refs:
        formula = cells.formula(MU_HELPER_SHEET, ref)
        for quoted, bare in _SHEET_REF.findall(str(formula or "")):
            named = quoted or bare
            if named.startswith(SHEET_PREFIX) and named != sheet:
                raise validation.ValidationError(
                    f"{cells.address(sheet, mu_ref)} reads its "
                    f"Dachformbeiwert from {MU_HELPER_SHEET}!{ref}, which "
                    f"takes its geometry from '{named}', not from '{sheet}' "
                    f"-- one helper block serves the whole workbook, so "
                    f"'{sheet}' shows its own Dachneigungen (H23/H24) while "
                    f"{mu_ref} reports the ones entered on '{named}'. Give "
                    f"this sheet its own mu formula, reading its own H23/H24, "
                    f"then save the workbook and export again"
                )


def _check_all_results_read(cells, sheet, load_model, read):
    """No result cell may hold a load this exporter did not read."""
    for ref in RESULT_CELLS:
        if ref in read:
            continue
        if cells.value(sheet, ref, required=False) is not None:
            raise validation.ValidationError(
                f"{cells.address(sheet, ref)}: load model "
                f"{load_model!r} also computes a characteristic load here, "
                f"which this exporter does not read yet -- extend "
                f"calc/domains/snow.py before using it"
            )


def read_instance(cells, sheet):
    """Reads one SL-* sheet into one instance of the snow-load domain (docs/domain/calculation-domains.md §3.3): the {sheet, results, vars, steps, checks} shape every calculation instance has.
    """
    calc = engine.Calculation()

    def add(name, ref, symbol, unit, label, level, norm_ref,
            description=None, choices=None, group=None, group_label=None,
            required=True, from_sheet=None):
        """One cell -> one traced var. Returns the value as read, or None for an optional cell this load model leaves empty. `from_sheet` reads the cell off another sheet -- where mu_2m is left off the SL sheet it is read on the helper block instead -- and `source` then records where it was actually read.
        """
        held_on = from_sheet or sheet
        value = cells.value(held_on, ref, required=required)
        if value is None:
            return None
        calc.add_var(
            name=name, value=value, unit=unit, symbol=symbol, label=label,
            level=level, source=f"excel:{cells.address(held_on, ref)}", norm=NORM,
            norm_ref=norm_ref, description=description, choices=choices,
            group=group, group_label=group_label,
        )
        return value

    # The vars are added in the order the *report* prints them, not in cell order: show-calc walks a calculation var by var, rendering one that a step produces as that step (docs/typst/api-conventions.md §10bis), so this order is the level-3 layout. Their levels are what splits the three reports (section 3.7): the q_k step alone at level 1; h_ref and s_k joining it as plain values at level 2; and at level 3 every coefficient, every choice, and the formulas behind h_ref and s_k. A var and the step that produces it are levelled separately on purpose -- h_ref is worth showing from level 2, the working behind it only to a checker.

    # F21 decides how H23/H24 are read, so the load model is read here and added further down, at the place the report shows it.
    load_models = cells.column(*LOAD_MODEL_LIST)
    load_model = cells.value(sheet, "F21")
    _require_one_of(cells, load_model, load_models, sheet, "F21",
                    "Dachform / Lastmodell")

    # Whether this case has a Schneeanhäufung is asked of the result cell, not of the load model's name: the sheet's own IF decides which loads it computes, and a name checked here would be one more thing to keep in step with the dropdown. The answer is needed before the coefficients, because mu_2m is printed with the other Dachformbeiwerte.
    has_2m = cells.value(sheet, "I39", required=False) is not None

    # --- Standort und Bezugshöhe (SIA 261, Anhang D) ----------------------
    # H11 holds the dropdown's label ("+200"), H12 the height it resolves to; the labels are the allowed values, their metres the explanation.
    correction_choices = [
        {"value": label, "desc": "± 0 m" if offset == 0 else f"{offset:+g} m"}
        for label, offset in cells.pairs(*CORRECTION_TABLE)
    ]
    add("h_0", "H10", "h_0", "m", "Höhe ü. NN", 3, "5.2.6",
        description="Höhe des Standorts über Meer.")
    add("korrektur", "H11", "Delta h", "m", "Korrektur Wert", 3, "Anhang D",
        description="Höhenzuschlag auf die Höhe ü. NN nach SIA 261, Anhang D.",
        choices=correction_choices)
    add("h_ref", "H12", 'h_"ref"', "m", "Bezugshöhe", 2, "5.2.6")
    calc.add_step(
        name="Bezugshöhe", level=3, result="h_ref", uses=["h_0", "korrektur"],
        formula='h_"ref" = h_0 + Delta h', norm=NORM, norm_ref="Anhang D",
    )

    # --- Beiwerte ----------------------------------------------------------
    exposure = cells.value(sheet, "E14")
    exposure_choices = [
        {"value": value, "desc": label}
        for label, value in cells.pairs(*EXPOSURE_TABLE)
    ]
    add("ce", "H14", "C_e", "", "Expositionsbeiwert", 3, "5.2.4",
        description=f"Gewählte Windexposition: {exposure}.",
        choices=exposure_choices, group="beiwerte")
    add("ct", "H15", "C_T", "", "Thermischer Beiwert", 3, "5.2.5",
        description="Thermischer Beiwert nach SIA 261, Ziffer 5.2.",
        group="beiwerte")

    # --- Gebäudegeometrie --------------------------------------------------
    # H23/H24 are the building's plan dimensions for a flat roof and the two roof pitches for every other load model -- the sheet swaps its own labels and unit in place (its G23/I23 formulas), so this does too. The two cases are added at different places because the report shows them in different places: the geometry here, the pitches below the load model that gives them their meaning.
    if load_model == FLAT_ROOF:
        add("L", "H23", "L", "m", "Gebäudelänge", 3, "5.3", group="geometrie",
            group_label="Gebäude Geometrie")
        add("B", "H24", "B", "m", "Gebäudebreite", 3, "5.3", group="geometrie")

    # --- Dachform und Dachformbeiwerte -------------------------------------
    height_jumps = add(
        "hoehenspruenge", "F19", '"Grosse Höhensprünge"', "",
        "Grosse Höhensprünge", 3, "5.3.6",
        description="Bei 'Ja' ist die Schneeanhäufung nach SIA 261, Figur 5 "
                    "zusätzlich zu berücksichtigen.",
    )
    _require_one_of(cells, height_jumps, HEIGHT_JUMP_VALUES, sheet, "F19",
                    "Grosse Höhensprünge")

    sliding = add(
        "abgleiten", "F29", '"Abgleiten des Schnees"', "",
        "Abgleiten des Schnees", 3, "5.3.4",
        description="Ist das Abgleiten behindert oder erschwert, wird der "
                    "Dachformbeiwert mit mindestens 0.8 angesetzt "
                    "(SIA 261, Ziffer 5.3.4).",
    )
    _require_one_of(cells, sliding, SLIDING_VALUES, sheet, "F29",
                    "Abgleiten des Schnees")
    slides = sliding == SLIDING_POSSIBLE

    add("lastmodell", "F21", '"Lastmodell"', "", "Dachform / Lastmodell", 3, "5.3",
        description="Im Blatt " + sheet + " wählbare Lastmodelle: "
                    + ", ".join(load_models) + ".")

    if load_model == FLAT_ROOF:
        _check_mu_helper(cells, sheet, "H26", MU_HELPER_FLAT)
    else:
        add("alpha_1", "H23", "alpha_1", "°", "Dachneigung 1", 3, "5.3",
            group="dachneigung")
        add("alpha_2", "H24", "alpha_2", "°", "Dachneigung 2", 3, "5.3",
            group="dachneigung", required=False)
        _check_mu_helper(cells, sheet, "H26", (MU_11_CELL,))
        _check_mu_helper(cells, sheet, "H27", (MU_12_CELL,))

    add("mu_11", "H26", "mu_11", "", "Dachformbeiwert", 3, "5.3",
        group="dachformbeiwerte")
    mu_12 = add("mu_12", "H27", "mu_12", "", "Dachformbeiwert 2", 3, "5.3",
                group="dachformbeiwerte", required=False)
    if has_2m:
        mu_2m_args = dict(
            symbol="mu_(2m)", unit="", label="Dachformbeiwert der Schneeanhäufung",
            level=3, norm_ref="5.3", group="dachformbeiwerte",
            description="Dachformbeiwert für die Schneeanhäufung in der Kehle "
                        "eines Sheddachs (SIA 261, Figur 2 und Figur 3).",
        )
        # The sheet labels this coefficient (I35) but its template leaves the value cell blank, so where the sheet does not state it, it is read where I39 reads it -- off the shared helper block, which must then be this sheet's.
        if add("mu_2m", "K35", required=False, **mu_2m_args) is None:
            _check_mu_helper(cells, sheet, "I39", (MU_2M_CELL,))
            add("mu_2m", MU_2M_CELL, from_sheet=MU_HELPER_SHEET, **mu_2m_args)

    # --- Charakteristischer Wert am Boden ----------------------------------
    add("s_k", "H17", "s_k", "kN/m²",
        "Charakteristischer Wert der Schneelast auf horizontalem Gelände",
        2, "5.2.6")
    calc.add_step(
        name="Charakteristischer Wert auf horizontalem Gelände", level=3,
        result="s_k", uses=["h_ref"],
        # `thin` -- Typst math ignores source spaces, so the unit would otherwise be set flush against the 0.9. The `>=` is also what stops show-calc closing this formula with "= 1.729 kN/m²": a bound is not an equality, so the step prints the compact "mit h_ref = ..." note and its result on a row of its own.
        formula='s_k = (1 + (h_"ref" / 350)^2) dot 0.4 >= 0.9 thin "kN/m"^2',
        norm=NORM, norm_ref="5.2.6",
    )

    # --- Charakteristische Schneelast(en) ----------------------------------
    # The printed formulas follow the sheet's own I37/I38, which branch on F29: with the sliding hindered, I37 raises mu_11 to at least 0.8 and I38 drops mu_12 for a flat 0.8 (SIA 261, 5.3.4). Printing the unconditional product in that case would show a formula that does not produce the number standing next to it. I39, the Sheddach accumulation, has no such branch -- it is the plain product, exactly as the sheet computes it.
    results = []
    read = set()

    def result(name, ref, symbol, label, formula, uses, required=True):
        """One result cell -> one level-1 var and the step that produced it. Returns False for a cell this load model leaves empty, so the caller reads them all and the sheet decides which ones exist.
        """
        if add(name, ref, symbol, "kN/m²", label, 1, "5.2.2",
               required=required) is None:
            return False
        read.add(ref)
        results.append(name)
        calc.add_step(name=label, level=1, result=name, uses=uses,
                      formula=formula, norm=NORM, norm_ref="5.2.2")
        return True

    result("q_k11", "I37", "q_(k,11)", "Charakteristische Schneelast",
           formula=(
               "q_(k,11) = mu_11 dot C_e dot C_T dot s_k" if slides
               else "q_(k,11) = max(mu_11, 0.8) dot C_e dot C_T dot s_k"
           ),
           uses=["mu_11", "ce", "ct", "s_k", "abgleiten"])

    if mu_12 is not None:
        result("q_k12", "I38", "q_(k,12)",
               "Charakteristische Schneelast, Lastmodell 2",
               formula=(
                   "q_(k,12) = mu_12 dot C_e dot C_T dot s_k" if slides
                   else "q_(k,12) = 0.8 dot C_e dot C_T dot s_k"
               ),
               uses=(["mu_12", "ce", "ct", "s_k", "abgleiten"] if slides
                     else ["ce", "ct", "s_k", "abgleiten"]),
               required=False)

    if has_2m:
        result("q_k2m", "I39", "q_(k,2m)",
               "Charakteristische Schneelast der Schneeanhäufung",
               formula="q_(k,2m) = mu_(2m) dot C_e dot C_T dot s_k",
               uses=["mu_2m", "ce", "ct", "s_k"])

    # A result cell this module does not read is a design load the engineer entered and the report would never show, so it is refused by name -- the treatment the Sheddach accumulation used to get, now applied to every cell the sheet can compute a load in rather than to the one that happened to be known about.
    _check_all_results_read(cells, sheet, load_model, read)

    return {"sheet": sheet, "results": results, **calc.to_dict()}


def read_instances(cells, sheets):
    """Every SL-* sheet of one workbook, in tab order, keyed by sheet name."""
    return {sheet: read_instance(cells, sheet) for sheet in sheets}
