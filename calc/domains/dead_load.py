"""Permanent loads (Eigenlast + Auflast): the arithmetic of a build-up of layers -- the sums g_k and a_k, their sum, the retained value and the table of the layers (docs/domain/loads.md §3.3ter).

A build-up is entered in Woodcore's «Poids propre» tab, one source each (domains/dead_load_source.py, issue #35, redesigned by issue #111), and summed here: `instance_from_layers` is the one place the sums are made. Until issue #109 the `EL+AL-*` sheets of the Belastungsannahmen workbooks were read here too, their layers looked up in the workbook's material library; they are read no more (decision D-33), and only what a build-up entered in Woodcore needs stays.

Per layer, as the workbook did it:

    load [kN/m2] = rho * thickness * width / spacing

with kg turned into kN at g = 10 m/s2 (`KG_TO_KN`).
"""

import engine

DOMAIN = "dead-load"
LABEL = "Eigen- und Auflasten"
ENGINE = "python"
ACTION = "permanent"  # SIA 260: a permanent action (G), as opposed to a variable one (Q) -- docs/domain/calculation-domains.md §3.3
NORM = "SIA 261"
NORM_REF = "Anhang A"

SOURCE = "python:domains/dead_load.py"

# What the table's material column says of a layer whose load was typed, naming no material (the workbook's «Installationen und Innenwände», 0.5 kN/m², periodic audit 260916, AUD-2-2). A glossary term, so a French report says it in French.
DIRECT_LOAD = "Direkt eingegebene Last"

KIND_DEAD, KIND_IMPOSED = "gk", "ak"
KINDS = (KIND_DEAD, KIND_IMPOSED)

# kg -> kN, as the workbook does it
KG_TO_KN = 100.0


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


# How far below the computed sum a chosen value may sit before it is refused (dead_load_messages). Not zero: the engineer rounds, and a build-up that sums to 1.2004 may legitimately be designed with 1.2. A tenth of a percent covers the rounding and nothing else -- a layer left in the table by mistake is out by whole percents, as a workbook's `EL+AL-Dach ohne Wasser` was (2.412 summed, 1.900 chosen, v0.59).
CHOSEN_TOLERANCE = 1e-3


def instance_from_layers(layers, chosen, chosen_source, chosen_description, source=SOURCE, note=None):
    """One instance of the domain from its layers -- [{kind, ebene, material, dicke, breite, dist, mass, unit, load}], lengths in m, load in kN/m² -- and the chosen value: g_k, a_k, their sum and the chosen value as vars, the build-up as the table above them. The one place the sums are made, for a build-up entered in Woodcore (domains/dead_load_source.py, issue #35). `chosen` None takes the sum itself, read as the result."""
    gk = sum(l["load"] for l in layers if l["kind"] == KIND_DEAD)
    ak = sum(l["load"] for l in layers if l["kind"] == KIND_IMPOSED)
    calc = engine.Calculation()

    def add(name, value, symbol, label, source, description=None):
        calc.add_var(
            name=name, value=value, unit="kN/m²", symbol=symbol, label=label,
            source=source, norm=NORM, norm_ref=NORM_REF,
            description=description,
        )

    # The level split, decided here rather than in the display code (docs/typst/api-conventions.md §10bis): every level from 2 up prints g_k, a_k, g_k + a_k and the gewählt value as four plain lines -- the four numbers an engineer reads off an Aufbau -- and level 3 adds the Schichtaufbau table above them.
    #
    # Neither sum carries a formula. A Sigma over the layers would state in letters exactly what the table below it lists row by row, and the table now carries the two sums itself as its `totals` rows, where each stands directly under the column it adds up. The steps stay, formula or not: they are what records that these vars are calculated (their norm, their source) rather than entered.
    add("gk", gk, "g_k", "Eigengewicht (Flächenlast)", source)
    calc.add_step(
        name="Eigengewicht", result="gk", uses=[],
        norm=NORM, norm_ref=NORM_REF,
    )

    add("ak", ak, "a_k", "Auflast (Flächenlast)", source)
    calc.add_step(
        name="Auflast", result="ak", uses=[],
        norm=NORM, norm_ref=NORM_REF,
    )

    # No formula: the sum of two symbols that are printed right above it would only restate them as `g_k + a_k = g_k + a_k`.
    add("gk_ak", gk + ak, "g_k + a_k", "Summe (berechnet)", source)
    calc.add_step(
        name="Summe", result="gk_ak", uses=["gk", "ak"],
        norm=NORM, norm_ref=NORM_REF,
    )

    if chosen is not None:
        # An entry, not a result: the engineer rounds the computed sum up to the value the design is actually carried out with, so it is read as entered and shown as this instance's final result.
        calc.add_var(
            name="gk_ak_gew", value=chosen, unit="kN/m²",
            symbol='(g_k + a_k)_"gew"', label="Ständige Lasten, gewählt",
            source=chosen_source,
            norm=NORM, norm_ref="2.1",
            description=chosen_description,
        )
        calc.add_step(
            name="Ständige Lasten", result="gk_ak_gew", uses=["gk_ak"],
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
