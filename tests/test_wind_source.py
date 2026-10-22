"""Wind loads entered in Woodcore (calc/domains/wind_source.py, calc/norms/sia261_wind.py, issue #37, spec docs/requirements/completed/2026-10-10-issues-github-35-a-39.md).

What is held:

* **REQ-006, D-06** -- every building table of SIA 261 Annexe C is transcribed (31 to 60b, 63, 64), each row as many values as its columns, and the transcription agrees with the Belastungsannahmen workbook's own tables (tests/fixtures/wind-tables-reference.json) wherever both carry a value -- the workbook's defects, confirmed on a render of the norm's pages, listed in DEFECTS and the norm's value kept (D-02);
* **REQ-005** -- c_h of (12) with its floors and category IV's switch, q_p of (11), c_red of Figur 9 read off the figure's own vectors and computed rather than read off a scroll bar, the global forces q_k = c_red · c_d · c_f · q_p per reference area and the local pressures, each worked out here by hand from the table;
* a coefficient the norm computes directly («*») named and not computed; a malformed source refused naming the field; the export beside a workbook's sheets.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import math

import conftest
import registry
import validation
from domains import wind_source
from norms import sia261_wind

ORACLE = conftest.ROOT / "tests" / "fixtures" / "wind-tables-reference.json"
# (table, the norm's row, the workbook's column): the workbook's value that is wrong, the norm's kept (D-02)
DEFECTS = {("35", "0°", "iD"), ("39", "90°", "C"), ("40", "90°", "F"), ("41", "180°", "iA"), ("42", "0°", "F")}
# the workbook's labels for the norm's directions, where they differ
RELABEL = {("40", "15°"): "45°", ("40", "45°"): "90°", ("40", "90°"): "180°", ("42", "15°"): "45°", ("43", "23°"): "22.5°", ("43", "15°"): "45°", ("41", "180"): "180°"}
NAMES = list("ABCDEFGH") + ["glm+", "glm-", "iA", "iB", "iC", "iD", "cf1", "cf2", "cf3"]


def _src(**change):
    src = wind_source.new_source("WI-01")
    src.update(change)
    return src


def test_every_building_table_of_annex_c_is_transcribed_and_checked():
    """D-06: the buildings of Annexe C -- 37 tables, from 31 to 64 without the bridges, the cylinders, the walls, the walkway and the sections -- each with its page, its columns and its rows."""
    assert len(sia261_wind.NUMBERS) == 37 and sia261_wind.NUMBERS[0] == "31" and sia261_wind.NUMBERS[-1] == "64"
    assert not {"61", "62", "65", "66", "67", "68", "69", "70", "71"} & set(sia261_wind.NUMBERS)
    for table in sia261_wind.tables():
        assert 82 <= table["page"] <= 105 and table["rows"] and table["columns"], table["number"]
        assert any(c["group"] in ("cpe", "cf") for c in table["columns"]), table["number"]
    t33 = sia261_wind.table("33")
    assert next(c for c in t33["columns"] if c["key"] == "cf2:d·h")["area_factor"] == 0.96, "the factor of c_f2's reference area, 0,96 d·h"
    assert sia261_wind.table("31")["rows"][0]["values"][11] == [0.15, -0.21], "rép. 0,15/−0,21"


def test_the_transcription_agrees_with_the_workbooks_tables():
    """A second reading by other hands: c_pe A-H, c_pi and c_f of tables 31-45, 59a, 59b, value for value, the workbook's known defects aside."""
    oracle = json.loads(ORACLE.read_text(encoding="utf-8"))["tables"]
    compared = 0
    for number, rows in oracle.items():
        table = sia261_wind.table(number)
        keys = [c["key"] for c in table["columns"]]
        for row in rows:
            label = RELABEL.get((number, row[0]), row[0]).replace(",", ".")
            mine = next(r for r in table["rows"] if r["label"] == label)
            v = dict(zip(keys, mine["values"]))
            rep = v["cpi:rep"]
            ours = [v["cpe:" + s] for s in "ABCDEFGH"] + ([rep[0], rep[1]] if isinstance(rep, list) else [rep, None])
            ours += [v["cpi:" + s] for s in "ABCD"] + [v[k] for k in keys if k.startswith("cf")][:3]
            for name, m, x in zip(NAMES, ours, row[1:]):
                if (number, label, name) in DEFECTS or (x is None and m is None):
                    continue
                if isinstance(m, list) and name not in ("glm+", "glm-"):
                    assert x is not None and abs(abs(x) - abs(m[0])) < 1e-9, (number, label, name, m, x)
                else:
                    assert x is not None and m is not None and abs(x - m) < 1e-9, (number, label, name, m, x)
                compared += 1
    assert compared > 1000, compared


def test_c_h_q_p_and_c_red_follow_the_norm():
    c_h, z, profile = sia261_wind.c_h(8, "III")
    assert z == 8 and profile == "III" and abs(c_h - 1.6 * ((8 / 450) ** 0.23 + 0.375) ** 2) < 1e-12
    assert sia261_wind.c_h(3, "II")[1] == 5 and sia261_wind.c_h(7, "IV")[1] == 10, "the floors of 6.2.1.2"
    assert sia261_wind.c_h(40, "IV")[2] == "III", "category IV above 30 m reads category III's profile"
    assert abs(sia261_wind.c_red(5, 1) - 0.918) < 1e-12 and abs(sia261_wind.c_red(100, 0.1) - 0.826) < 1e-12
    between = sia261_wind.c_red(20, 1.5)
    assert sia261_wind.c_red(20, 2) < between < sia261_wind.c_red(20, 1), "between two curves, in log(beta)"
    assert sia261_wind.in_range(20, 1.5) and not sia261_wind.in_range(50, 20), "beta 20 at 50 m: Figur 9 draws no curve there"


def test_the_global_forces_and_the_local_pressures_of_a_closed_building():
    """REQ-005: Tableau 33 by hand -- q_p, c_red of the two facades, the six forces, a wall's local pressure with uniform openings."""
    src = _src(q_p0=1.1, terrain="III", b=20, d=12, h=8, table="33", c_d=1.0)
    wind_source.check_source(src)
    inst = wind_source.build_instance(src)
    v = {k: x["value"] for k, x in inst["vars"].items()}
    qp = 1.6 * ((8 / 450) ** 0.23 + 0.375) ** 2 * 1.1
    assert abs(v["qp"] - qp) < 1e-12
    cred_bh, cred_dh = sia261_wind.c_red(8, 20 / 8), sia261_wind.c_red(8, 12 / 8)
    assert abs(v["cred_bh"] - cred_bh) < 1e-12 and abs(v["cred_dh"] - cred_dh) < 1e-12
    table = sia261_wind.table("33")
    cf1 = [r["values"][16] for r in table["rows"]]
    assert abs(v["qk_max_cf1"] - cred_bh * max(cf1) * qp) < 1e-12 and abs(v["qk_min_cf1"] - cred_bh * min(cf1) * qp) < 1e-12
    cf3 = [r["values"][18] for r in table["rows"]]
    assert abs(v["qk_min_cf3"] - min(cf3) * qp) < 1e-12, "the roof's area takes c_red = 1.0 (6.3.2)"
    assert inst["results"] == ["qk_max_cf1", "qk_min_cf1", "qk_max_cf2", "qk_min_cf2", "qk_max_cf3", "qk_min_cf3"]
    forces, local = inst["tables"]
    assert forces["columns"][3]["label"] == "0.96·d·h", "the area's factor in its header"
    wall_a = next(r for r in local["rows"] if r[0] == "A")
    cases = [c.get("group") for c in local["columns"][1:]][::2]
    rep = cases.index("gleichmässig")
    a = [r["values"][0] for r in table["rows"]]
    reps = [r["values"][11] for r in table["rows"]]
    net = [qp * (e - p) for e, pr in zip(a, reps) for p in (pr if isinstance(pr, list) else [pr])]
    assert abs(wall_a[1 + 2 * rep] - max(net)) < 1e-12 and abs(wall_a[2 + 2 * rep] - min(net)) < 1e-12
    assert any(r[0] == "m (lokal)" for r in local["rows"]), "the local zones too"


def test_an_oblique_row_takes_the_larger_c_red():
    """Spec 2026-10-12-audit-issues-47-48-49, REQ-001 (D-03, D-18): SIA 261 6.3.3 (p. 33) -- c_red,b/h and c_red,d/h hold for directions less than 15° off a reference direction, the more unfavourable of the two for every other. Tableau 37, b 12, d 20, h 8 m: its largest c_f2 stands in the 45° row, which takes max(c_red,b/h, c_red,d/h) = c_red,b/h (beta 1.5) and not the d·h area's own c_red,d/h (beta 2.5); 0° and 90° keep the column's own; 15° is not «less than 15°»."""
    assert [sia261_wind.oblique(label) for label in ("0°", "15°", "22.5°", "45°", "90°", "135°", "180°", "−30°", "φ = 90°")] == [False, True, True, True, False, True, False, True, False]
    src = _src(q_p0=1.1, terrain="III", b=12, d=20, h=8, table="37", c_d=1.0)
    inst = wind_source.build_instance(src)
    v = {k: x["value"] for k, x in inst["vars"].items()}
    table = sia261_wind.table("37")
    i = next(n for n, c in enumerate(table["columns"]) if c["group"] == "cf" and c["area"] == "d·h")
    cred_bh, cred_dh = sia261_wind.c_red(8, 12 / 8), sia261_wind.c_red(8, 20 / 8)
    assert cred_bh > cred_dh and abs(v["cred_max"] - cred_bh) < 1e-12
    by_row = [(cred_dh if r["label"] in ("0°", "90°") else cred_bh) * c * v["qp"] for r in table["rows"] for c in wind_source._values(r["values"][i])]
    assert abs(v["qk_max_cf2"] - max(by_row)) < 1e-12 and abs(v["qk_min_cf2"] - min(by_row)) < 1e-12
    best = max(table["rows"], key=lambda r: max(wind_source._values(r["values"][i])))
    assert best["label"] == "45°" and abs(v["qk_max_cf2"] - cred_bh * max(wind_source._values(best["values"][i])) * v["qp"]) < 1e-12, "the 45° row governs, with the larger c_red"
    assert "6.3.3" in inst["tables"][0]["note"]


def test_every_row_of_every_table_has_its_direction_read():
    """D-18: the direction of a row is read off its label -- every label of the 37 tables is a direction in degrees, except Tableau 64's, which name a roof and an angle φ and keep their area's own c_red (none of them is a facade's b·h or d·h)."""
    for number in sia261_wind.NUMBERS:
        table = sia261_wind.table(number)
        facades = any(c["area"] in ("b·h", "d·h") for c in table["columns"] if c["group"] in ("cf", "cf_snow"))
        for row in table["rows"]:
            angle = sia261_wind.direction(row["label"])
            assert angle is not None or (number == "64" and not facades), (number, row["label"])


def test_the_forces_and_the_local_pressures_are_the_workbooks():
    """REQ-005: the sheet «Wind» of «load workbook» template recalculated by Excel on 11.10.2026 (a copy of the template) -- q_p0 1.1, b 20, d 12, h 8 m, «III Ortschaften, freies Feld», figure 33, its c_red,b/h and c_red,d/h typed as Woodcore computes them (the workbook reads them off a scroll bar), «Undicht auf der Seite» A: J17, J69:L70, and F90:F98 for each of the four directions, enveloped as Woodcore's table does. The workbook takes one c_red per area in every direction, where 6.3.3 gives an oblique row the larger of the two (D-18): the comparison holds because Tableau 33's extreme force coefficients stand in its 0° and 90° rows, which keep their own."""
    inst = wind_source.build_instance(_src(q_p0=1.1, terrain="III", b=20, d=12, h=8, table="33", c_d=1.0))
    v = {k: x["value"] for k, x in inst["vars"].items()}
    assert abs(v["qp"] - 1.04566362720076) < 1e-12
    excel = {"qk_max_cf1": 0.791606745727926, "qk_max_cf2": 0.95993868810021, "qk_max_cf3": -0.679681357680496,
             "qk_min_cf1": 0, "qk_min_cf2": 0, "qk_min_cf3": -0.763334447856557}
    for key, value in excel.items():
        assert abs(v[key] - value) < 1e-12, (key, v[key], value)
    # F90:F98 by direction 0°, 15°, 45°, 90°, the openings on side A
    side_a = {"A": (0, 0.0522831813600381, -0.0522831813600381, 0), "B": (-1.0979468085608, -0.993380445840725, -0.941097264480687, 0),
              "C": (-1.56849544080114, -1.0979468085608, -0.0522831813600381, 1.56849544080114), "D": (-1.56849544080114, -1.15022998992084, -0.941097264480687, 0.470548632240343),
              "E": (-1.88219452896137, -1.67306180352122, -1.56849544080114, -0.313699088160229), "F": (-1.88219452896137, -1.51621225944111, -1.0979468085608, 0.365982269520267),
              "G": (-1.20251317128088, -0.941097264480687, -1.0979468085608, -0.313699088160229), "H": (-1.20251317128088, -0.993380445840725, -0.83653090176061, 0.365982269520267)}
    local = inst["tables"][1]
    at = [i for i, c in enumerate(local["columns"]) if c.get("group") == "Öffnung A"]
    for row in local["rows"]:
        if row[0] in side_a:
            assert abs(row[at[0]] - max(side_a[row[0]])) < 1e-12 and abs(row[at[1]] - min(side_a[row[0]])) < 1e-12, (row[0], row[at[0]], row[at[1]])


def test_open_buildings_canopies_and_hemispheres_compute_and_a_direct_force_is_named_not_computed():
    for number in sia261_wind.NUMBERS:
        inst = wind_source.build_instance(_src(table=number))
        assert inst["tables"], number
    quai = wind_source.build_instance(_src(table="51"))
    assert "qk_max_cf1" not in quai["vars"] and "qk_max_cf2" in quai["vars"] and "qk_max_cfs1" in quai["vars"], "the «*» of c_f1 is computed directly (its note)"
    open_one = wind_source.build_instance(_src(table="46"))
    assert "netto" in [c.get("group") for c in open_one["tables"][1]["columns"]], "an open building's surfaces with their own c_pi"


def test_each_defect_is_refused_naming_the_field():
    for change, word in (({"q_p0": 0}, "q_p0"), ({"terrain": "V"}, "terrain"), ({"h": -1}, "h is"), ({"h": 250}, "6.1.2"), ({"z": 0}, "z is"),
                         ({"table": "61"}, "Annexe C"), ({"c_d": 0}, "c_d")):
        try:
            wind_source.check_source(_src(**change), "loads/wind/probe.json")
        except validation.ValidationError as exc:
            assert word in str(exc), (change, str(exc))
        else:
            raise AssertionError(change)


def test_the_export_carries_a_wind_source():
    here = conftest.project_copy("wind_source_export")
    folder = here.sources_dir / wind_source.FOLDER
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "WI-01.json").write_text(json.dumps(_src()), encoding="utf-8")
    data = registry.build_calculations([], here, {})
    instance = data["domains"]["wind-load"]["instances"]["WI-01"]
    assert instance["source_file"] == "loads/wind/WI-01.json" and math.isfinite(instance["vars"]["qp"]["value"])
    validation.validate_structure(data, "calculations")
    validation.validate_calculations_business(data)


def test_the_workbook_path_takes_the_terrain_from_the_norm_and_stops_on_a_table_that_disagrees():
    """REQ-003 (spec 2026-10-19-base-saine-nettoyage, lot 8): wind.py reads the workbook's own words for a terrain category and SIA 261 Tableau 4's z_g and alpha_r from calc/norms/; a workbook row that says another number stops the import, naming its cell."""
    from domains import wind
    rows = [(91, {"kat": "II Seeufer", "zg": 300, "ar": 0.16}), (92, {"kat": "IV grossflächige Stadtgebiete", "zg": 526, "ar": 0.3}), (93, {"kat": None, "zg": None, "ar": None})]
    held = wind._terrain(rows)
    assert [r["kat"] for _, r in held] == ["II Seeufer", "IV grossflächige Stadtgebiete"]
    assert held[1][1]["zg"] == sia261_wind.terrain("IV")["z_g"] and held[1][1]["ar"] == sia261_wind.terrain("IV")["alpha_r"]
    try:
        wind._terrain([(92, {"kat": "IV grossflächige Stadtgebiete", "zg": 500, "ar": 0.3})])
    except validation.ValidationError as exc:
        assert "Dropdowns!C92" in str(exc) and "526" in str(exc), exc
    else:
        raise AssertionError("a workbook's z_g other than the norm's was read")
