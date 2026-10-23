"""Snow load of the `SL-*` sheets of the Belastungsannahmen workbooks: their inputs read, the load computed by Woodcore (spec 2026-10-21-restes-issue-69, REQ-001, ARCH-002; docs/domain/loads.md §3.3bis).

Until v0.120 an `SL-*` sheet *was* the snow calculation, and this module read the cells Excel had computed -- h_ref, s_k, the Dachformbeiwerte, the loads. The engineer, 21.10.2026: the workbook gives the inputs only. A sheet is now read for what the engineer enters on it -- the altitude (H10), the correction of Anhang D (H11), the exposure (E14), C_T (H15), the roof (F21), its plan dimensions or its slopes (H23, H24), a height step (F19), the sliding (F29) -- and the load is computed by `snow_source.build_instance`, the code a snow load entered in Woodcore is computed by: one calculation of the snow, its values out of calc/norms/. Each input keeps the cell it was read from as its provenance (`excel:<workbook>!<sheet>!<cell>`), each value worked out `python:`.

**What the sheet computed is compared, never printed** (D-07): where the sheet shows h_ref, s_k, a Dachformbeiwert or a load that stands apart from Woodcore's, the export says so -- the cell and the two values (`_common.sheet_differences`). A sheet whose shared helper block on `Dropdowns` computed its Dachformbeiwerte from another roof (the defect `_check_mu_helper` refused until v0.120) is caught there too: its value differs.

**The workbook's words.** The dropdowns of `Dropdowns` are read for their labels -- the correction's «+200», the exposure's «normale Windexposition» --, each number one SIA 261 gives or the import stops naming the table (`_held`). The roof is the load model's first word: «Flachdach», «Giebeldach» (a duo-pitch roof, both load models computed), «Sheddach». A duo-pitch or shed roof whose second slope H24 is left empty takes 0°, as the sheet's own helper block does, and the export says so.

One sheet, one instance of the domain, named by the sheet. The names of its values are the source's -- q_k1 and mu_1 of a flat roof, `dachform` where the sheet said `lastmodell` --, which the sections, the scripts and the sources of a project are migrated to when it is opened (domains/loads_names.py, CON-002).
"""

import validation
from domains import snow_source
from domains._common import require_one_of, sheet_differences
from domains.loads_names import SNOW_COMPARED
from norms import sia261_snow

DOMAIN = snow_source.DOMAIN
LABEL = "Schneelast"
ENGINE = "python"   # computed by Woodcore since v0.120, from the sheet's inputs (REQ-001)
SHEET_PREFIX = "SL"
ACTION = "variable"  # SIA 260: a variable action (Q), as opposed to a permanent one (G) -- docs/domain/calculation-domains.md §3.3
NORM = "SIA 261"

# Lookup tables on the workbook's own `Dropdowns` sheet -- their labels read rather than restated here, each number one SIA 261 gives (`_held`), so a report footnote can never disagree with the choices the engineer actually sees in Excel.
EXPOSURE_TABLE = ("Dropdowns", "B24:C26")     # Windexposition -> C_e
CORRECTION_TABLE = ("Dropdowns", "B30:C34")   # label -> Hoehenzuschlag [m]
LOAD_MODEL_LIST = ("Dropdowns", "I44:I48")    # Dachform / Lastmodell

# The roof a load model of F21 names, by its first word: the load model itself is gone, Woodcore computing both models of Figur 3 for a pitched roof (snow_source)
ROOF_OF = {"Flachdach": "flat", "Giebeldach": "duo", "Sheddach": "shed"}
HEIGHT_JUMP_VALUES = ("Ja", "Nein")
SLIDING_VALUES = tuple(snow_source.SLIDING_WORDS[key] for key in snow_source.SLIDING)   # the sheet's words are the report's (snow_source.SLIDING_WORDS)

# Where each field of a source is read on a sheet: what a refusal names, and each input's provenance
CELLS = {"h_0": "H10", "correction": "H11", "exposure": "E14", "c_t": "H15", "roof": "F21",
         "length": "H23", "width": "H24", "alpha_1": "H23", "alpha_2": "H24", "height_step": "F19", "sliding": "F29"}


def _held(pairs, values, table, norm_ref):
    """The workbook's (label, number) pairs, each number one SIA 261 gives (`values`, read from calc/norms/): the norm's number is what is taken, and a number of the workbook's own stops the import, naming the table."""
    out = []
    for label, number in pairs:
        held = next((v for v in values if isinstance(number, (int, float)) and abs(v - number) < 1e-9), None)
        if held is None:
            raise validation.ValidationError(
                f"{table[0]}!{table[1]}: {label!r} gives {number!r} -- SIA 261 {norm_ref} gives {', '.join(f'{v:g}' for v in values)} (calc/norms/{sia261_snow.SNOW}.json)")
        out.append((label, held))
    return out


def roof_of(load_model):
    """The source's roof a load model of the workbook names («GiebeldachLM2» -> duo), None where it names none."""
    return next((roof for word, roof in ROOF_OF.items() if str(load_model).startswith(word)), None)


def read_source(cells, sheet, notes=None):
    """The sheet's inputs as a snow-load source, and where each was read, `(src, {field: "excel:<cell>"})` -- every field checked by the source's own rules, a refusal naming the cell (snow_source.check_fields)."""
    norm = sia261_snow.clause()

    def at(field, required=True):
        return cells.value(sheet, CELLS[field], required=required)

    load_model = require_one_of(cells, at("roof"), cells.column(*LOAD_MODEL_LIST), sheet, CELLS["roof"], "Dachform / Lastmodell")
    roof = roof_of(load_model)
    if roof is None:
        raise validation.ValidationError(f"{cells.address(sheet, CELLS['roof'])}: Dachform / Lastmodell is {load_model!r} -- Woodcore reads {', '.join(ROOF_OF)}")
    corrections = dict(_held(cells.pairs(*CORRECTION_TABLE), norm["corrections"]["values"], CORRECTION_TABLE, "Anhang D"))
    correction = require_one_of(cells, at("correction"), list(corrections), sheet, CELLS["correction"], "Korrektur Wert")
    exposures = dict(_held(cells.pairs(*EXPOSURE_TABLE), [c["value"] for c in norm["exposure"]["choices"]], EXPOSURE_TABLE, "5.2.4"))
    exposure = require_one_of(cells, at("exposure"), list(exposures), sheet, CELLS["exposure"], "Windexposition")
    height = require_one_of(cells, at("height_step"), HEIGHT_JUMP_VALUES, sheet, CELLS["height_step"], "Grosse Höhensprünge")
    sliding = require_one_of(cells, at("sliding"), SLIDING_VALUES, sheet, CELLS["sliding"], "Abgleiten des Schnees")
    src = {"schema_version": snow_source.SOURCE_SCHEMA_VERSION, "id": sheet,
           "h_0": at("h_0"), "correction": corrections[correction],
           "exposure": next(c["id"] for c in norm["exposure"]["choices"] if abs(c["value"] - exposures[exposure]) < 1e-9),
           "c_t": at("c_t"), "roof": roof,
           "sliding": next(key for key, word in snow_source.SLIDING_WORDS.items() if word == sliding)}
    fields = ["h_0", "correction", "exposure", "c_t", "roof", "sliding"]
    if height == "Ja":
        src["height_step"] = True
        fields.append("height_step")
    if roof == "flat":
        src["length"], src["width"] = at("length"), at("width")
        fields += ["length", "width"]
    else:
        src["alpha_1"], src["alpha_2"] = at("alpha_1"), at("alpha_2", required=False)
        fields.append("alpha_1")
        if src["alpha_2"] is None:
            # the sheet's helper block reads an empty H24 as 0° (Dropdowns!F65): computed as it does, and said
            src["alpha_2"] = 0
            if notes is not None:
                import engine
                cell = cells.address(sheet, CELLS["alpha_2"])
                notes.append(engine.Note("sheet_slope_empty", f"{cell}: the second roof slope is empty -- computed at 0°, as the sheet does",
                                         cell=cell))
        else:
            fields.append("alpha_2")

    def fail(field, message):
        raise validation.ValidationError(f"{cells.address(sheet, CELLS.get(field, ''))}: {message}")
    snow_source.check_fields(src, fail)
    return src, {field: "excel:%s" % cells.address(sheet, CELLS[field]) for field in fields}


def read_instance(cells, sheet, notes=None):
    """One SL-* sheet, one instance of the snow-load domain (docs/domain/calculation-domains.md §3.3): its inputs read (`read_source`), computed by `snow_source.build_instance`, compared with what the sheet computed (D-07)."""
    src, inputs = read_source(cells, sheet, notes)
    instance = snow_source.build_instance(src, inputs=inputs)
    # a sheet's case is printed without the figure a case entered in Woodcore carries: the export writes the drawings of the sources alone (registry._build_source), as for a permanent load's sheet
    instance.pop("_files", None)
    instance.pop("figures", None)
    sheet_differences(cells, sheet, SNOW_COMPARED.get(src["roof"], ()), instance["vars"], notes)
    if notes is not None:
        notes.extend(snow_source.notes_of(src, cells.address(sheet, CELLS["h_0"])))
    return {"sheet": sheet, **instance}


def read_instances(cells, sheets, notes=None):   # `notes`: what is worth saying, registry's one signature for the three (C4)
    """Every SL-* sheet of one workbook, in tab order, keyed by sheet name."""
    return {sheet: read_instance(cells, sheet, notes) for sheet in sheets}
