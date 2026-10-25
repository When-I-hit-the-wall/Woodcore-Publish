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
from domains import wind_forces, wind_source
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
    per_m2 = ["qk_max_cf1", "qk_min_cf1", "qk_max_cf2", "qk_min_cf2", "qk_max_cf3", "qk_min_cf3"]
    assert inst["results"] == per_m2 + ["Q" + k[1:] for k in per_m2], "the loads per m² under their names of always, the forces in kN after them (REQ-002)"
    assert abs(v["Qk_max_cf2"] - v["qk_max_cf2"] * 0.96 * 12 * 8) < 1e-9 and inst["vars"]["Qk_max_cf2"]["unit"] == "kN"
    forces, local = inst["tables"]
    assert forces["columns"][3]["label"] == "0.96·d·h", "the area's factor in its header"
    assert forces["rows"][0][2:] == ["Qk_max_cf1", "Qk_max_cf2", "Qk_max_cf3"], "the forces in kN, read off their variables"
    # the local pressures of the openings chosen alone, transposed: a column a surface, a row max and a row min (REQ-014)
    assert [r[0] for r in local["rows"]] == ["max", "min"] and local["widths"] == "first-auto"
    surfaces = [c["label"] for c in local["columns"][1:]]
    assert surfaces[:8] == list("ABCDEFGH") and {"m", "n", "o"} <= set(surfaces) and {c["group"] for c in local["columns"][1:]} == {"Öffnungen gleichmässig verteilt"}
    k = surfaces.index("A") + 1
    a = [r["values"][0] for r in table["rows"]]
    reps = [r["values"][11] for r in table["rows"]]
    net = [qp * (e - p) for e, pr in zip(a, reps) for p in (pr if isinstance(pr, list) else [pr])]
    assert abs(local["rows"][0][k] - max(net)) < 1e-12 and abs(local["rows"][1][k] - min(net)) < 1e-12


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
    def values(cell):
        return [x for x, _side in wind_forces.values(cell)]
    by_row = [(cred_dh if r["label"] in ("0°", "90°") else cred_bh) * c * v["qp"] for r in table["rows"] for c in values(r["values"][i])]
    assert abs(v["qk_max_cf2"] - max(by_row)) < 1e-12 and abs(v["qk_min_cf2"] - min(by_row)) < 1e-12
    best = max(table["rows"], key=lambda r: max(values(r["values"][i])))
    assert best["label"] == "45°" and abs(v["qk_max_cf2"] - cred_bh * max(values(best["values"][i])) * v["qp"]) < 1e-12, "the 45° row governs, with the larger c_red"
    governing = next(f for f in wind_forces.analysis(src)["forces"] if f["name"] == "cf2")["max"]
    assert governing["phi"] == "45°" and governing["c_red_of"] == "max", "the analysis says which c_red the extreme took"


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
    inst = wind_source.build_instance(_src(q_p0=1.1, terrain="III", b=20, d=12, h=8, table="33", c_d=1.0, openings="A"))
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
    assert {c["group"] for c in local["columns"][1:]} == {"Dominante Öffnung in der Wand A"}, "the openings chosen, alone"
    compared = 0
    for k, column in enumerate(local["columns"]):
        if column["label"] in side_a:
            surface = side_a[column["label"]]
            assert abs(local["rows"][0][k] - max(surface)) < 1e-12 and abs(local["rows"][1][k] - min(surface)) < 1e-12, (column["label"], local["rows"][0][k], local["rows"][1][k])
            compared += 1
    assert compared == 8


def test_open_buildings_canopies_and_hemispheres_compute_and_a_direct_force_is_named_not_computed():
    for number in sia261_wind.NUMBERS:
        inst = wind_source.build_instance(_src(table=number))
        assert inst["tables"], number
    quai = wind_source.build_instance(_src(table="51"))
    assert "qk_max_cf1" not in quai["vars"] and "qk_max_cf2" in quai["vars"] and "qk_max_cfs1" in quai["vars"], "the «*» of c_f1 is computed directly (its note)"
    open_one = wind_source.build_instance(_src(table="46"))
    assert {c.get("group") for c in open_one["tables"][1]["columns"][1:]} == {"Innendruckbeiwert jeder Fläche"}, "an open building's surfaces with their own c_pi"


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
    data = registry.build_calculations(here, {})
    instance = data["domains"]["wind-load"]["instances"]["WI-01"]
    assert instance["source_file"] == "loads/wind/WI-01.json" and math.isfinite(instance["vars"]["qp"]["value"])
    validation.validate_structure(data, "calculations")
    validation.validate_calculations_business(data)


# --- spec 2026-10-23-onglet-vent-briques, V1: domains/wind_forces.py, the arithmetic kept with its provenance

GOLDEN = conftest.ROOT / "tests" / "fixtures" / "wind-prototype-golden.json"


def _golden_src(case):
    i = case["input"]
    return _src(q_p0=i["qp0"], terrain=i["terrain"], b=i["b"], d=i["d"], h=i["h"], z=None if i["zIsH"] else i["z"], c_d=i["cd"], table=i["table"], openings=i["opening"])


def _near(x, y):
    return x == y or (x is not None and y is not None and abs(x - y) < 2e-6)


def test_the_analysis_gives_the_prototypes_numbers():
    """CON-001, REQ-001 to REQ-004: the prototype's compute() run on eight buildings (tests/fixtures/wind-prototype-golden.json) -- q_p, z, the profile, c_red, the openings' case, every force's A_ref, extremes and their φ, Q_k in kN, every surface's extremes with their φ, c_pe and c_pi."""
    from domains import wind_forces
    for case in json.loads(GOLDEN.read_text(encoding="utf-8"))["cases"]:
        a = wind_forces.analysis(_golden_src(case))
        n = case["input"]["table"]
        assert _near(a["q_p"], case["qp"]) and a["z_used"] == case["z_used"] and a["profile"] == case["profile"] and a["opening"] == case["opening"], n
        assert _near(a["cred"]["bh"], case["cred"]["bh"]) and _near(a["cred"]["dh"], case["cred"]["dh"]), n
        assert [f["name"][1:] for f in a["forces"]] == [g["name"] for g in case["global"]], n
        for f, g in zip(a["forces"], case["global"]):
            assert _near(f["area"], g["A"]), (n, f["name"])
            assert _near(f["max"]["q"], g["max"]) and f["max"]["phi"] == g["max_phi"] and _near(f["min"]["q"], g["min"]) and f["min"]["phi"] == g["min_phi"], (n, f["name"])
            assert f["area"] is None or (_near(f["max"]["Q"], g["Qmax"]) and _near(f["min"]["Q"], g["Qmin"])), (n, f["name"])
        assert [s["surface"] for s in a["local"]] == [g["surface"] for g in case["local"]], n
        for s, g in zip(a["local"], case["local"]):
            mx, mn = s["max"], s["min"]
            assert _near(mx["q"], g["max"]) and mx["phi"] == g["max_phi"] and mx["c_pe"] == g["max_cpe"] and mx["c_pi"] == g["max_cpi"] and mx["c_pi_key"] == g["max_cpi_key"], (n, s["surface"])
            assert _near(mn["q"], g["min"]) and mn["phi"] == g["min_phi"] and mn["c_pe"] == g["min_cpe"] and mn["c_pi"] == g["min_cpi"], (n, s["surface"])


def test_the_local_pressures_take_c_d_and_both_values_of_a_pair_never_c_red():
    """REQ-003: q_k = q_p · (c_d · c_pe − c_pi) by hand on Tableau 36's wall A at c_d 1.2, the same as before at c_d 1.0; ±0,1 of the uniform openings counts both its signs; no c_red in a local pressure; an extreme recomputed from its own c_pe and c_pi is itself (REQ-004)."""
    from domains import wind_forces
    one, more = (wind_forces.analysis(_src(q_p0=1.1, terrain="III", b=24, d=12, h=6, table="36", c_d=c_d, openings="rep")) for c_d in (1.0, 1.2))
    table = sia261_wind.table("36")
    i, j = (next(k for k, c in enumerate(table["columns"]) if c["key"] == key) for key in ("cpe:A", "cpi:rep"))
    by_hand = [more["q_p"] * (1.2 * e - p) for row in table["rows"] for e, _s in wind_forces.values(row["values"][i]) for p, _t in wind_forces.values(row["values"][j])]
    wall = next(s for s in more["local"] if s["surface"] == "A")
    assert abs(wall["max"]["q"] - max(by_hand)) < 1e-12 and abs(wall["min"]["q"] - min(by_hand)) < 1e-12
    assert all("c_red" not in v for r in wall["rows"] for v in r["values"])
    plain = next(s for s in one["local"] if s["surface"] == "A")
    before = [one["q_p"] * (e - p) for row in table["rows"] for e, _s in wind_forces.values(row["values"][i]) for p, _t in wind_forces.values(row["values"][j])]
    assert abs(plain["max"]["q"] - max(before)) < 1e-12 and abs(plain["min"]["q"] - min(before)) < 1e-12, "c_d = 1.0: q_p · (c_pe − c_pi), what Woodcore wrote before"
    assert {0.1, -0.1} <= {v["c_pi"] for r in wall["rows"] for v in r["values"]}, "±0,1: both signs"
    for s in more["local"]:
        for x in (s["max"], s["min"]):
            assert abs(more["q_p"] * (1.2 * x["c_pe"] - x["c_pi"]) - x["q"]) < 1e-12, s["surface"]


def test_every_number_carries_the_cells_it_was_read_off():
    """REQ-004, REQ-005: the detail holds a value for every (surface, φ) of the table; an extreme names its c_pe cell and its c_pi cell -- the side of a pair too -- as opaque keys of the cells of the norm's table (ARCH-004)."""
    from domains import wind_forces
    a = wind_forces.analysis(_src(q_p0=1.1, terrain="III", b=24, d=12, h=6, table="36", c_d=1.0, openings="rep"))
    table = a["table"]
    rep_at = [c["key"] for c in table["columns"]].index("cpi:rep")
    for s in a["local"]:
        assert [r["phi"] for r in s["rows"]] == [r["label"] for r in table["rows"]] and all(r["values"] for r in s["rows"]), s["surface"]
        x = s["max"]
        row = table["rows"][x["row"]]
        assert x["phi"] == row["label"] and x["keys"][0].startswith(wind_forces.cell(s["key"], x["row"]))
        rep = row["values"][rep_at]
        side = rep.index(x["c_pi"]) if isinstance(rep, list) else None
        assert x["keys"][1] == wind_forces.cell("cpi:rep", x["row"], side), "the openings' cell it took, and which value of a pair"
    f = a["forces"][0]
    assert f["max"]["keys"] == [wind_forces.cell(f["key"], f["max"]["row"])]


def test_the_global_forces_take_the_c_red_of_their_row():
    """REQ-002: Tableau 36's forces -- c_red of b·h in the 0° row, the larger of the two in the 45° row (6.3.3), 1.0 for the roof's d·b (6.3.2); Q_k = q_k · A_ref with the header's factor."""
    from domains import wind_forces
    a = wind_forces.analysis(_src(q_p0=1.1, terrain="III", b=24, d=12, h=6, table="36", c_d=1.0))
    f1, f2, f3 = a["forces"]
    by_phi = {r["phi"]: r for r in f1["rows"]}
    assert by_phi["0°"]["c_red"] == a["cred"]["bh"] and by_phi["45°"]["c_red"] == a["cred"]["max"] == max(a["cred"]["bh"], a["cred"]["dh"])
    assert all(r["c_red"] == 1.0 for r in f3["rows"]), "the roof"
    assert abs(f1["area"] - 24 * 6) < 1e-12 and abs(f2["area"] - (f2["column"].get("area_factor") or 1) * 12 * 6) < 1e-12 and abs(f3["area"] - 12 * 24) < 1e-12
    assert abs(f1["max"]["Q"] - f1["max"]["q"] * f1["area"]) < 1e-12


def test_a_reference_area_the_building_does_not_give_is_per_square_metre_only():
    """REQ-002 (ARCH-RISK-008): a header naming h1, d1 or hs has no A_ref -- its q_k per m², no Q_k; the closed table of the norm file, never the label evaluated."""
    from domains import wind_forces
    areas = sia261_wind.clause()["forces"]["areas"]
    for number in sia261_wind.NUMBERS:
        for f in wind_forces.analysis(_src(table=number))["forces"]:
            assert (f["area"] is not None) == (f["column"]["area"] in areas), (number, f["column"]["area"])
            assert f["area"] is not None or all(v["Q"] is None for r in f["rows"] for v in r["values"])
    assert abs(sia261_wind.area({"area": "π·d²/8"}, 1, 4, 1) - math.pi * 2) < 1e-12 and abs(sia261_wind.area({"area": "d·(b+d)/2"}, 3, 2, 1) - 5) < 1e-12


def test_z_floor_category_iv_and_the_localised_surfaces():
    """REQ-001, REQ-007, REQ-008: z below 6.2.1.2's floor is raised to it, category IV above 30 m reads category III's profile; m, n, o are «loc», never walls nor roofs; ĉ_pe · q_p; a table with no openings' column takes the surface's own c_pi, or none."""
    from domains import wind_forces
    assert wind_forces.analysis(_src(terrain="III", h=3))["z_used"] == 5, "6.2.1.2: z at least 5 m"
    low = wind_forces.analysis(_src(terrain="IV", h=6))
    assert low["z"] == 6 and low["z_used"] == 10 and low["profile"] == "IV"
    tall = wind_forces.analysis(_src(terrain="IV", h=40, z=35))
    assert tall["z_used"] == 35 and tall["profile"] == "III"
    a = wind_forces.analysis(_src(table="36"))
    assert {s["surface"] for s in a["local"] if s["group"] == "loc"} == {"m", "n", "o"}
    assert {s["group"] for s in a["local"] if s["surface"] in "ABCD"} == {"wall"} and {s["group"] for s in a["local"] if s["surface"] in "EFGH"} == {"roof"}
    assert a["cpe_peak"] == -2.0 and abs(a["q_peak"] - -2.0 * a["q_p"]) < 1e-12
    open_one = wind_forces.analysis(_src(table="46"))
    assert open_one["opening"] is None and all(s["own_c_pi"] for s in open_one["local"] if s["c_pi_key"])
    assert wind_forces.analysis(_src(table="57a"))["local"][0]["c_pi_key"] is None


def test_the_openings_case_is_the_sources_and_older_sources_are_read():
    """REQ-006, CON-002, D-24: a new source is 1.2 and holds its openings' case; another case takes another c_pi column and other pressures; a source of 1.0 or 1.1 holds none and is read with «rep»; openings at 1.0 or 1.1, or a case the norm does not name, are refused naming the field; a case kept from another table is not."""
    from domains import wind_forces
    src = wind_source.new_source("WI-01")
    assert src["schema_version"] == "1.2" and src["openings"] == "rep"
    wind_source.check_source(src)
    a, b = (wind_forces.analysis(dict(src, openings=case)) for case in ("rep", "B"))
    assert a["opening_key"] == "cpi:rep" and b["opening_key"] == "cpi:B" and a["local"][0]["max"]["q"] != b["local"][0]["max"]["q"]
    old = {k: v for k, v in src.items() if k != "openings"}
    for version in ("1.0", "1.1"):
        if version == "1.1":
            old["links"] = {"b": {"domain": "wind-load", "instance": "WI-00", "var": "b"}}
        old["schema_version"] = version
        wind_source.check_source(old)
        assert wind_forces.analysis(old)["opening"] == "rep"
    assert wind_source.stamp_version(dict(old))["schema_version"] == "1.1" and wind_source.stamp_version(dict(old, openings="A"))["schema_version"] == "1.2"
    wind_source.check_source(dict(src, links=old["links"]))
    wind_source.check_source(dict(src, table="46", openings="D"))
    for bad, word in ((dict(old, openings="A"), "openings"), (dict(src, openings="E"), "openings")):
        try:
            wind_source.check_source(bad)
        except validation.ValidationError as exc:
            assert word in str(exc), str(exc)
        else:
            raise AssertionError(bad)


# the prototype's field of each message, for the golden cases (its form's ids: f_h, f_z, f_terrain, f_cd, f_b, acc3 the table's section)
PROTOTYPE_FIELD = {"h": "f_h", "z": "f_z", "terrain": "f_terrain", "c_d": "f_cd", "b": "f_b", "table": "acc3"}


def test_the_messages_are_the_prototypes_each_on_its_field():
    """REQ-009: the oranges of the eight golden buildings are the prototype's, field for field -- z raised to its floor and two facades Figur 9 does not draw (Tableau 40, h 4 m), c_d = 1.0 above 15 m (59a), category IV above 30 m (59b), a reference area per m² only (57a)."""
    for case in json.loads(GOLDEN.read_text(encoding="utf-8"))["cases"]:
        said = wind_source.messages(_golden_src(case))
        assert all(m.severity == "info" for m in said), case["input"]["table"]
        assert sorted(PROTOTYPE_FIELD[m.field] for m in said) == sorted(case["infos"]), (case["input"]["table"], said)


def test_each_message_names_its_field_and_a_red_one_stops_the_calculation():
    """REQ-009 (ARCH-RISK-015): one probe per message -- the input that causes it, its colour, its field; a red one is said by `messages` and refused by `check_fields` with the same field, and no orange is computed beside it; with every input valid, nothing is said (the tab's green «complete» is the brick's)."""
    reds = (({"q_p0": 0}, "q_p0", "q_p0"), ({"q_p0": None}, "q_p0", "q_p0"), ({"terrain": "V"}, "terrain", "terrain"), ({"d": -1}, "dimension", "d"), ({"h": 250}, "too_high", "h"),
            ({"z": 0}, "z", "z"), ({"table": None}, "table", "table"), ({"c_d": 0}, "c_d", "c_d"))
    for change, code, field in reds:
        said = wind_source.messages(_src(**change))
        assert [(m.code, m.field, m.severity) for m in said] == [(code, field, "error")], (change, said)
        stopped = []
        wind_source.check_fields(_src(**change), lambda f, message: stopped.append(f))
        assert stopped == [field], change
    oranges = (({"terrain": "IV", "h": 6}, "z_min", "h"), ({"terrain": "IV", "h": 6, "z": 4}, "z_min", "z"), ({"terrain": "IV", "h": 40, "b": 40, "d": 40}, "iv_as_iii", "terrain"),
               ({"h": 20, "b": 30, "d": 20}, "c_d_default", "c_d"), ({"h": 2}, "c_red_outside", "h"), ({"table": "36", "b": 12, "d": 12, "h": 6}, "ratio", "b"),
               ({"table": "51"}, "direct", "table"), ({"table": "57a"}, "no_area", "table"))
    for change, code, field in oranges:
        said = wind_source.messages(_src(**change))
        assert (code, field, "info") in [(m.code, m.field, m.severity) for m in said], (change, said)
    assert [m.code for m in wind_source.messages(_src(table="36", b=24, d=12, h=6))] == [], "every input valid: nothing said"
    old = {k: v for k, v in _src(table="36", b=24, d=12, h=6).items() if k != "openings"}
    assert [(m.code, m.field) for m in wind_source.messages(old)] == [("openings_default", "openings")], "D-24"
    assert wind_source.messages({k: v for k, v in _src(table="46", b=15, d=9, h=6).items() if k != "openings"}) == [], "a table with no openings' column asks for none"
    assert [c for c, _p in wind_source.warnings(_src(h=2))] == ["c_red_outside", "c_red_outside"], "the export says only what it said before"


def test_the_results_in_3d_at_every_direction_are_the_extremes():
    """UI-014 (V3): «Max, toutes directions» -- `loads_at` and `forces_at` with MAX -- gives each surface's largest pressure and suction and each force's Q_k max and min, those of «Résultats» (REQ-002, REQ-004); one direction its own row's; a surface whose extreme is of the other sign left out."""
    from domains import wind_forces
    a = wind_forces.analysis(_src(table="36", b=24, d=12, h=6))
    up, down = wind_forces.loads_at(a), wind_forces.loads_at(a, sign="-")
    for s in a["local"]:
        assert up.get(s["surface"], None) == (s["max"]["q"] if s["max"]["q"] > 0 else None), s["surface"]
        assert down.get(s["surface"], None) == (s["min"]["q"] if s["min"]["q"] < 0 else None), s["surface"]
    forces = {f["name"]: f for f in a["forces"]}
    assert wind_forces.forces_at(a) == {"f%s" % n[2:]: forces[n]["max"]["Q"] for n in forces}
    assert wind_forces.forces_at(a, sign="-") == {"f%s" % n[2:]: forces[n]["min"]["Q"] for n in forces}
    at_zero = wind_forces.forces_at(a, "0°")
    assert at_zero["f1"] == max(v["Q"] for r in forces["cf1"]["rows"] if r["phi"] == "0°" for v in r["values"])
