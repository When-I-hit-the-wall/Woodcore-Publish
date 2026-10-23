"""The snow and wind sheets of a load workbook read for their inputs and computed by Woodcore (spec 2026-10-21-restes-issue-69, REQ-001, REQ-002, UI-002, ARCH-002, D-07 to D-09; calc/domains/snow.py, wind.py).

The sheets are tests/fixtures/load-sheets-reference.json's: SL-*/WL-* sheets of the engineer's workbooks, their inputs and the values Excel computed, anonymous (D-09). What is held:

* **one calculation**: a sheet's instance is the one `snow_source`/`wind_source.build_instance` computes from the sheet's inputs -- the inputs cited by their cells (`excel:`), every value worked out `python:`; and the snow the sheets computed is Woodcore's to the digit;
* **inputs alone**: without a list of warnings, nothing but the cells the engineer enters (and the Dropdowns) is read -- no computed cell;
* **what the sheet computed is compared** (D-07): a value apart from Woodcore's is a warning naming its cell and the two values; a sheet in step with Woodcore gives none;
* **a defect stops, naming the cell**: an input the norm refuses, a table of Annexe C Woodcore does not hold, a load model it does not read;
* an empty second slope is 0°, as the sheet takes it, and said; a sheet named with an accent is read.
"""

import copy
import json

import conftest
from conftest import ROOT

import validation
from fixtures import workbook

REFERENCE = json.loads((ROOT / "tests" / "fixtures" / "load-sheets-reference.json").read_text(encoding="utf-8"))


def _reader(name, snow=(), wind=()):
    import io_excel
    path = conftest.tmpdir("load_sheets") / f"{name}.xlsx"
    workbook.build_loads(path, snow, wind)
    return io_excel.CellReader(path)


def _expect_refused(fn, *words):
    try:
        fn()
    except validation.ValidationError as exc:
        assert all(w in str(exc) for w in words), (words, str(exc))
    else:
        raise AssertionError("not refused: %s" % (words,))


def test_a_snow_sheet_is_the_source_computed_from_its_inputs():
    from domains import snow, snow_source
    cells = _reader("snow", snow=REFERENCE["snow"])
    for item in REFERENCE["snow"]:
        sheet = item["sheet"]
        notes = []
        instance = snow.read_instance(cells, sheet, notes)
        src, inputs = snow.read_source(cells, sheet)
        built = snow_source.build_instance(src, inputs=inputs)
        built.pop("_files"), built.pop("figures")   # a sheet's case carries no figure: the export draws the sources' alone (snow.read_instance)
        assert instance == {"sheet": sheet, **built}, sheet
        assert instance["vars"]["h_0"]["source"] == "excel:%s" % cells.address(sheet, "H10"), sheet
        assert instance["vars"]["s_k"]["source"] == snow_source.SOURCE, sheet
        # what the sheets computed is Woodcore's: nothing to say
        assert not [n for n in notes if n.code == "sheet_value_differs"], (sheet, notes)
        for name, cell in (("h_ref", "H12"), ("s_k", "H17")):
            if cell in item["excel"]:
                assert abs(instance["vars"][name]["value"] - item["excel"][cell]) < 1e-9, (sheet, name)
        first = instance["results"][0]
        if "I37" in item["excel"]:
            assert abs(instance["vars"][first]["value"] - item["excel"]["I37"]) < 1e-9, (sheet, first)
    flat = snow.read_instance(cells, "SL-2")
    assert flat["results"] == ["q_k1"] and "mu_1" in flat["vars"] and flat["vars"]["dachform"]["value"] == "Flachdach"
    duo = snow.read_instance(cells, "SL-3")
    assert duo["results"] == ["q_k11", "q_k12", "q_k11h", "q_k12h"], duo["results"]


def test_a_wind_sheet_is_the_source_computed_from_its_inputs_and_what_differs_is_said():
    from domains import wind, wind_source
    cells = _reader("wind", wind=REFERENCE["wind"])
    for item in REFERENCE["wind"]:
        sheet = item["sheet"]
        notes = []
        instance = wind.read_instance(cells, sheet, notes)
        src, inputs = wind.read_source(cells, sheet)
        assert instance == {"sheet": sheet, **wind_source.build_instance(src, inputs=inputs)}, sheet
        assert src["terrain"] == item["inputs"]["I11"].split()[0] and src["table"] == str(item["inputs"]["F40"]), src
        assert instance["vars"]["qp0"]["source"] == "excel:%s" % cells.address(sheet, "J6")
        assert instance["vars"]["qp"]["source"] == wind_source.SOURCE
        assert set(instance["results"]) == {"qk_%s_cf%d" % (k, i) for k in ("max", "min") for i in (1, 2, 3)}, instance["results"]
        # each difference names a cell of the sheet and its two values; the pressure coefficients are the norm's own
        differs = [n for n in notes if n.code == "sheet_value_differs"]
        for note in differs:
            assert note.args["cell"].startswith(cells.address(sheet) + "!") and note.args["excel"] != note.args["woodcore"], note
        assert not [n for n in differs if n.args["cell"][-3:-2] in "CDEFGHIJKLMNOP" and n.args["cell"][-2:] in ("78", "79", "80", "81")], differs
        # q_p is computed as the sheet does
        assert abs(instance["vars"]["qp"]["value"] - item["excel"]["J17"]) < 1e-9, sheet
        assert len(differs) <= 9, (sheet, differs)   # c_red and the six forces at most: no noise beyond what changed


def test_without_warnings_only_the_inputs_are_read():
    """REQ-001, REQ-002: «classeur = entrées seulement» -- with no list of warnings, no cell Excel computed is read."""
    from domains import snow, wind
    import io_excel
    cells = _reader("spy", snow=REFERENCE["snow"], wind=REFERENCE["wind"])
    read = []
    real = io_excel.CellReader.value

    def spy(self, sheet, ref, required=True):
        if sheet != "Dropdowns":
            read.append(ref)
        return real(self, sheet, ref, required)
    io_excel.CellReader.value = spy
    try:
        for item in REFERENCE["snow"]:
            snow.read_instance(cells, item["sheet"])
        for item in REFERENCE["wind"]:
            wind.read_instance(cells, item["sheet"])
    finally:
        io_excel.CellReader.value = real
    assert set(read) <= set(snow.CELLS.values()) | set(wind.CELLS.values()), sorted(set(read) - set(snow.CELLS.values()) - set(wind.CELLS.values()))


def test_a_value_the_sheet_computed_apart_from_woodcore_s_is_said_with_its_cell():
    from domains import snow
    item = copy.deepcopy(REFERENCE["snow"][1])
    item["excel"]["I37"] = 1.5
    cells = _reader("differs", snow=[item])
    notes = []
    snow.read_instance(cells, item["sheet"], notes)
    differs = [n for n in notes if n.code == "sheet_value_differs"]
    assert len(differs) == 1 and differs[0].args["cell"].endswith("!I37") and differs[0].args["name"] == "q_k1" and differs[0].args["excel"] == "1.5", differs


def test_a_wind_force_the_sheet_computed_apart_from_woodcore_s_is_said_with_its_cell():
    from domains import wind
    item = copy.deepcopy(REFERENCE["wind"][0])
    item["excel"] = {"J69": 9.99}
    cells = _reader("differs_wind", wind=[item])
    notes = []
    instance = wind.read_instance(cells, item["sheet"], notes)
    differs = [n for n in notes if n.code == "sheet_value_differs" and not n.args["cell"].endswith(("!J19", "!J20"))]   # the sheet's c_red, a scroll bar's, differ too
    assert len(differs) == 1 and differs[0].args["cell"].endswith("!J69") and differs[0].args["name"] == "qk_max_cf1", differs
    assert differs[0].args["excel"] == "9.99" and differs[0].args["woodcore"] == "%.6g" % instance["vars"]["qk_max_cf1"]["value"], differs


def test_a_defect_of_an_input_stops_naming_its_cell():
    from domains import snow, wind
    for cell, value, words in (("H15", 2, ("!H15", "c_t")), ("F21", "Pultdach", ("!F21", "Dachform")), ("H11", "+300", ("!H11",)), ("F29", "rutscht", ("!F29",))):
        item = copy.deepcopy(REFERENCE["snow"][1])
        item["inputs"][cell] = value
        cells = _reader("bad_snow_" + cell, snow=[item])
        _expect_refused(lambda: snow.read_instance(cells, item["sheet"]), *words)
    for cell, value, words in (("F40", 99, ("!F40", "Tableaux")), ("J9", 0, ("!J9",)), ("I11", "V Wüste", ("!I11",))):
        item = copy.deepcopy(REFERENCE["wind"][0])
        item["inputs"][cell] = value
        cells = _reader("bad_wind_" + cell, wind=[item])
        _expect_refused(lambda: wind.read_instance(cells, item["sheet"]), *words)


def test_an_empty_second_slope_is_zero_and_said_and_a_sheet_may_carry_an_accent():
    from domains import snow, wind
    item = copy.deepcopy(REFERENCE["snow"][2])
    item["sheet"] = "SL-Gebäude"
    del item["inputs"]["H24"]
    item["excel"].pop("H27", None)
    cells = _reader("slope", snow=[item])
    notes = []
    instance = snow.read_instance(cells, "SL-Gebäude", notes)
    assert instance["vars"]["alpha_2"]["value"] == 0 and [n.code for n in notes if n.code == "sheet_slope_empty"] == ["sheet_slope_empty"], notes
    windy = copy.deepcopy(REFERENCE["wind"][0])
    windy["sheet"] = "WL-Fluchttreppe+Geräte"
    cells = _reader("accent", wind=[windy])
    assert wind.read_instance(cells, "WL-Fluchttreppe+Geräte")["sheet"] == "WL-Fluchttreppe+Geräte"


def test_a_c_red_figure_9_does_not_draw_and_a_site_above_the_limit_are_said():
    """ARCH-RISK-811: two warnings the export never gave -- c_red read off the end of Figur 9, a site above SIA 261 5.1.4's 2000 m."""
    from domains import snow, wind
    item = copy.deepcopy(REFERENCE["snow"][1])
    item["inputs"]["H10"] = 2100
    item["excel"] = {}
    cells = _reader("high", snow=[item])
    notes = []
    snow.read_instance(cells, item["sheet"], notes)
    assert [n.code for n in notes] == ["snow_above_limit"], notes
    windy = copy.deepcopy(REFERENCE["wind"][0])
    windy["inputs"]["J7"] = 400.0   # beta = b/h far beyond Figur 9's last curve
    windy["excel"] = {}
    cells = _reader("long", wind=[windy])
    notes = []
    wind.read_instance(cells, windy["sheet"], notes)
    assert "wind_c_red_outside" in [n.code for n in notes], notes
