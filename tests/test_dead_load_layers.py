"""The layers of a build-up of permanent loads computed, and the build-ups of before read as 2.0 (calc/domains/dead_load_layers.py, dead_load_migrate.py; spec docs/requirements/completed/2026-10-24-poids-propre-repense.md, issue #111).

What is held:

* **REQ-003** -- each pose's load: continuous γ·t, spaced γ·t·b/e, per surface γ, typed the value; the formula the pane writes, «5 kN/m³ × 0.2 m × 60/625 = 0.096 kN/m²»;
* **REQ-004, D-07** -- two lines linked share a level, never three; the line that fills takes 1000·(1 − b/e) mm (100/500 leaves 800, 60/625 leaves 904: a wool of 0.076 kN/m² at full width weighs 0.069), or the width written; two spaced lines, or two that fill, on one level refused;
* **REQ-005** -- the retained value, the tenth above or equal to the sum: 0.909 → 1.0, 0.900 → 0.9, 0.901 → 1.0;
* **REQ-006, ARCH-006** -- a load written replaces the calculation of its layer in the sum;
* **REQ-002, ARCH-007, CON-001** -- a 1.x source read as 2.0 in memory, `beside` become `link` on the line above, the pose deduced, the libraries' names become ids, the same sum; three layers beside each other, or two spaced ones, refused naming the layer; nothing rewritten on reading.
"""

TIER = "fast"  # tests/run_tests.py --fast

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import conftest
import validation
from domains import dead_load_layers as dl, dead_load_migrate, dead_load_source

TIMBER = "sia261:holz_nadelhoelzer_allgemein"   # 5 kN/m³, SIA 261 Tabelle 28
WOOL = "ext:46"                                  # Flumroc Typ 1, 38 kg/m³


def _layer(**change):
    return dict(dead_load_source.new_layer(), **change)


def _src(layers, chosen=None, cid="AU-01"):
    return {"schema_version": "2.0", "id": cid, "name": "", "label": "", "group": "", "chosen": chosen, "layers": layers}


def _refused(call, *words):
    try:
        call()
    except validation.ValidationError as exc:
        for word in words:
            assert word in str(exc), (word, str(exc))
    else:
        raise AssertionError("passed: %s" % (words,))


def test_the_retained_value_is_the_tenth_above_or_equal_to_the_sum():
    """REQ-005 (T36): 0.909 → 1.0, 0.900 → 0.9 -- a float read back on a tenth stays on it --, 0.901 → 1.0."""
    for total, tenth in ((0.909, 1.0), (0.900, 0.9), (0.901, 1.0), (0.1 + 0.2, 0.3), (2.0000000001, 2.0), (1.21, 1.3), (0.0, 0.0)):
        assert dl.retained(total) == tenth, (total, dl.retained(total), tenth)


def test_each_pose_weighs_as_it_says_and_writes_its_formula():
    """REQ-003 (T39): γ·t, γ·t·b/e, γ alone, the value typed; the formula of T54."""
    assert dl.computed_load({"pose": "continuous", "thickness": 27}, 5, "kN/m³") == (5 * 0.027, {"gamma": 5.0, "t": 27, "w": dl.STRIP})
    load, numbers = dl.computed_load({"pose": "spaced", "thickness": 200, "width": 60, "spacing": 625}, 5, "kN/m³")
    assert abs(load - 0.096) < 1e-12 and dl.formula(numbers, load) == "5 kN/m³ × 0.2 m × 60/625 = 0.096 kN/m²"
    assert dl.computed_load({"pose": "surface", "thickness": 10}, 47, "kg/m²")[0] == 0.47, "a weight per m², its thickness drawn only"
    assert dl.computed_load({"pose": "continuous", "thickness": 10}, 0.47, "kN/m²")[0] == 0.47, "a weight per m² on a continuous line: per m² still"
    assert dl.computed_load({"pose": "typed", "load": 0.5}, None, None) == (0.5, {})
    assert dl.computed_load({"pose": "continuous", "thickness": None}, 5, "kN/m³")[0] is None, "a thickness missing: no load"
    assert dl.computed_load({"pose": "spaced", "thickness": 200, "width": None, "spacing": 625}, 5, "kN/m³")[0] is None
    # T40: a weight per m² makes the line «surface», one per m³ on a «surface» line makes it continuous again
    assert dl.pose_for("kN/m²", {"pose": "continuous"}) == "surface" and dl.pose_for("kN/m³", {"pose": "surface"}) == "continuous"
    assert dl.pose_for("kN/m³", {"pose": "spaced"}) == "spaced"


def test_a_line_that_fills_takes_what_the_pieces_leave():
    """REQ-004 (T41): 100/500 leaves 800 mm; 60/625 leaves 904 mm, and the wool between the rafters goes from 0.076 to 0.069 kN/m² -- AU-01's 0.916 becoming 0.909, retained 1.0 still."""
    battens = [_layer(pose="spaced", thickness=100, width=100, spacing=500, link=True), _layer(pose="continuous", material=WOOL, thickness=100)]
    assert dl.fill_width(battens, 1) == (800.0, True)
    au01 = [_layer(pose="spaced", thickness=200, width=60, spacing=625, link=True), _layer(pose="continuous", material=WOOL, thickness=200)]
    assert dl.fill_width(au01, 1) == (904.0, True) and dl.levels(au01) == [[0, 1]]
    rows = dead_load_source.layer_rows(_src(au01))
    assert round(rows[1]["load"], 3) == 0.069 and round(rows[1]["fill_width"]) == 904 and rows[1]["breite"] == 0.904 and rows[1]["dist"] == 1.0
    full = dead_load_source.layer_rows(_src([au01[0], dict(au01[1], fill=False)]))
    assert round(full[1]["load"], 3) == 0.076 and full[1]["fill_width"] == 1000, "fill false, no width: the full metre"
    assert round(full[1]["load"] - rows[1]["load"], 3) == 0.007, "0.916 → 0.909"
    half = dead_load_source.layer_rows(_src([au01[0], dict(au01[1], fill=False, width=500)]))
    assert abs(half[1]["load"] - full[1]["load"] / 2) < 1e-12, "the width written"
    # the order of the two lines does not matter: the wool above the rafters fills as well
    flipped = dead_load_source.layer_rows(_src([dict(au01[1], link=True), dict(au01[0], link=False)]))
    assert abs(flipped[0]["load"] - rows[1]["load"]) < 1e-12
    # the air above a filling line thinner than its pieces (T18)
    thin = [au01[0], dict(au01[1], thickness=160)]
    assert dl.air(thin, 1) == 40 and dl.air(thin, 0) == 0
    # b/e ≥ 1 fills nothing
    assert dl.fill_width([_layer(pose="spaced", thickness=100, width=700, spacing=625, link=True), au01[1]], 1)[0] == 0.0


def test_a_level_holds_two_lines_one_spaced_and_one_that_fills():
    """REQ-004, D-07 (Q-001, 24.10.2026): a third line on a level, two spaced or two filling lines on one, a link on the last line -- each refused naming the layer."""
    spaced = _layer(pose="spaced", thickness=200, width=60, spacing=625)
    wool = _layer(pose="continuous", material=WOOL, thickness=200)
    for layers, at, words in (([dict(spaced, link=True), dict(wool, link=True), wool], "layers[1]", "third layer"),
                              ([dict(spaced, link=True), spaced], "layers[1]", "two spaced"),
                              ([dict(wool, link=True), wool], "layers[1]", "neither spaced"),
                              ([spaced, dict(wool, link=True)], "layers[1]", "last layer")):
        _refused(lambda: dead_load_source.check_source(_src(layers), "loads/dead/probe.json"), "probe.json", at, words)
    dead_load_source.check_source(_src([dict(spaced, link=True), wool]))


def test_each_defect_of_a_layer_at_2_0_is_refused_naming_the_field():
    """REQ-001: the pose, the role, a spacing on a line not spaced, a load typed without its value or with a material, a load of 0."""
    for change, word in ((dict(pose="laid"), "pose"), (dict(role="roof"), "role"), (dict(spacing=625), "spacing"),
                         (dict(pose="typed", load=0.5), "material"),
                         (dict(load=0), "load"), (dict(kind="qk"), "kind"), (dict(thickness=-1), "thickness")):
        _refused(lambda: dead_load_source.check_source(_src([_layer(**change)]), "loads/dead/probe.json"), word, "probe.json", "layers[0]")
    dead_load_source.check_source(_src([_layer(role="structure"), _layer(pose="typed", material=None, label="Installationen", load=0.5)]))


def test_a_load_written_replaces_the_calculation_of_its_layer():
    """REQ-006, ARCH-006: `load` on a layer of any pose replaces its calculation in the sum -- 0.2 in place of c changes the sum by (0.2 − c); the formula still says c."""
    layers = [_layer(thickness=27), _layer(pose="spaced", thickness=200, width=60, spacing=625)]
    before = dead_load_source.layer_rows(_src(layers))
    after = dead_load_source.layer_rows(_src([layers[0], dict(layers[1], load=0.2)]))
    assert after[1]["load"] == 0.2 and after[1]["replaced"] and abs(after[1]["computed"] - before[1]["load"]) < 1e-12
    assert after[1]["formula"] == before[1]["formula"]
    sums = [dead_load_source.build_instance(_src(x), conftest.PROJECT)["vars"]["gk_ak"]["value"] for x in (layers, [layers[0], dict(layers[1], load=0.2)])]
    assert abs((sums[1] - sums[0]) - (0.2 - before[1]["load"])) < 1e-12


def test_the_retained_value_is_always_in_the_instance():
    """REQ-005, P01: no value written, the tenth above the sum, its source the domain's; a value written is the engineer's entry."""
    instance = dead_load_source.build_instance(_src([_layer(thickness=27)]), conftest.PROJECT)
    v = instance["vars"]
    assert abs(v["gk_ak"]["value"] - 0.135) < 1e-12 and v["gk_ak_gew"]["value"] == 0.2 and instance["results"] == ["gk_ak_gew"]
    assert v["gk_ak_gew"]["source"].endswith("retained")
    written = dead_load_source.build_instance(_src([_layer(thickness=27)], chosen=0.5), conftest.PROJECT)["vars"]["gk_ak_gew"]
    assert written["value"] == 0.5 and written["source"].startswith("entered:")


def _old(**change):
    layer = {"kind": "gk", "library": "sia261", "material": "holz_nadelhoelzer_allgemein", "ebene": "", "thickness": 27, "width": None, "spacing": None, "beside": False, "load": None}
    layer.update(change)
    return layer


def test_a_source_of_before_is_read_as_2_0_with_the_same_sum():
    """REQ-002, ARCH-007, CON-001 (T32, T66): `beside` on layer i becomes `link` on layer i − 1, the line that is not spaced keeping the full width it was summed with; the pose from the weight's unit; the libraries' names become ids; a typed load at a spacing keeps its share; the same sum; the source itself untouched."""
    old = {"schema_version": "1.0", "id": "DA-01", "name": "", "label": "", "group": "", "chosen": None, "layers": [
        _old(kind="ak", library="belastungsannahmen", ebene="Abdichtung", material="Dachpappe", thickness=10),
        _old(),
        _old(thickness=200, width=60, spacing=625),
        _old(kind="ak", library="belastungsannahmen", ebene="Dämmung", material="Flumroc Typ 1", thickness=200, beside=True),
        _old(kind="ak", library="direct", material="Installationen", load=0.5, thickness=None, width=100, spacing=500)]}
    kept = copy.deepcopy(old)
    new = dead_load_migrate.upgrade(old)
    assert old == kept, "read in memory, never changed"
    assert new["schema_version"] == "2.0"
    assert [l["pose"] for l in new["layers"]] == ["surface", "continuous", "spaced", "continuous", "typed"]
    assert [l["material"] for l in new["layers"]] == ["ext:163", TIMBER, TIMBER, WOOL, None]
    assert [l["link"] for l in new["layers"]] == [False, False, True, False, False]
    assert [l["role"] for l in new["layers"]] == ["waterproofing", None, None, "insulation", None], "the workbook's Ebene said what the layer is for"
    assert new["layers"][3]["fill"] is False and new["layers"][3]["width"] == 1000
    assert new["layers"][4]["label"] == "Installationen" and abs(new["layers"][4]["load"] - 0.1) < 1e-12
    assert all("library" not in l and "beside" not in l and "ebene" not in l for l in new["layers"])
    dead_load_source.check_source(new)
    validation.validate_structure(new, dead_load_source.SOURCE_SCHEMA)
    total = lambda rows: sum(r["load"] for r in rows)
    weigh = lambda layer: dead_load_source.materials.weight(layer)
    expected = 0.0
    for layer in old["layers"]:
        share = layer["width"] / layer["spacing"] if layer.get("spacing") else 1.0
        if layer["library"] == "direct":
            expected += layer["load"] * share
            continue
        value, unit = weigh(layer)[:2]
        per = (layer["thickness"] / 1000.0) if unit.endswith("³") else 1.0
        expected += dead_load_source.materials.to_kn(value, unit) * per * share
    assert abs(total(dead_load_source.layer_rows(old)) - expected) < 1e-12 and abs(total(dead_load_source.layer_rows(new)) - expected) < 1e-12
    assert dead_load_migrate.upgrade(new) is new, "2.0 is read as it is"


def test_two_layers_of_before_the_rule_of_two_refuses_are_refused_naming_the_layer():
    """ARCH-007 (P03): two spaced layers beside each other, or three layers on one band, cannot be read as 2.0 -- refused naming the file and the layer; two continuous layers beside each other become two levels, the same sum."""
    def src(*layers):
        return {"schema_version": "1.0", "id": "DA-02", "name": "", "label": "", "group": "", "chosen": None, "layers": list(layers)}
    rafters = _old(thickness=200, width=60, spacing=625)
    _refused(lambda: dead_load_source.check_source(src(rafters, dict(rafters, beside=True)), "loads/dead/DA-02.json"), "DA-02.json", "layers[1]", "two spaced")
    _refused(lambda: dead_load_source.check_source(src(rafters, _old(beside=True), _old(beside=True)), "loads/dead/DA-02.json"), "layers[2]", "third")
    two = dead_load_migrate.upgrade(src(_old(), _old(beside=True)))
    assert [l["link"] for l in two["layers"]] == [False, False]
    dead_load_source.check_source(two)


def test_a_source_is_written_at_2_0_and_its_schema_reads_every_version():
    """ARCH-004: what the window writes is 2.0, by `stamp_version`; the schema pins 1.0 to 2.0."""
    src = dead_load_source.new_source("AU-09")
    assert src["schema_version"] == "2.0" and dead_load_source.stamp_version(dict(src, schema_version="1.2"))["schema_version"] == "2.0"
    validation.validate_structure(src, dead_load_source.SOURCE_SCHEMA)
    schema = json.loads((conftest.ROOT / "schemas" / "dead-load-source.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["schema_version"]["enum"] == ["1.0", "1.1", "1.2", "2.0"]
    assert set(schema["properties"]["layers"]["items"]["properties"]["pose"]["enum"]) == set(dl.POSES)
