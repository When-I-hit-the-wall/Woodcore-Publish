"""The fire situation of SIA 265:2021 4.5.2 and the fire resistance VKF / AEAI 15-15 requires (issue #46, spec docs/requirements/active/2026-10-12-resistance-au-feu.md).

What is held here:

* **the norm files**: Tabelle 13 read for every (wood, family) pair, 4.5.2's d_red, 4.5.2.4's widths and (51)'s factor through `calc/norms/sia265.py`, and the column «Système porteur» of 15-15's tables 1 to 3 with its notes through `calc/norms/vkf.py` -- four cases of the spec (REQ-006) and every note;
* **one list written once**: the woods and the faces of `fire:` in lib/timber.typ are calc/norms/sia265.py's;
* **`#member(fire:)`**: the two reference workbooks reproduced where they follow the norm -- *«fire, bending» template* (C24 140/200, R60 on three faces: b_fi 30, h_fi 145, W_y,fi 105 125 mm³, sigma_m 57.6 N/mm², utilisation 2.27) and the geometry, the slenderness and k_c of *«fire, buckling» template* (D30 140/240, R30 on four faces: 96/196 mm, lambda 86.6, lambda_rel 1.408, k_c 0.4226), its resistance being k_fi · f_k where SIA 265 (51) writes 1.8 · R_d (D-04) --; k_h not applied and f_c,0,k, E_0,05 not scaled; eta_w kept in R_d (a moisture class 2 case);
* **the refusals**: 4.5.2.4's width, a duration over 90 minutes, a hardwood without its wood, a round section, a section the fire consumes.

⚠️ The Typst part is skipped where `typst` is not on the path.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import math
import re

import conftest
from conftest import ROOT, Skip

from norms import sia265, vkf




def close(a, b, rel=1e-9):
    return abs(a - b) <= rel * max(1.0, abs(b))


# --- the norm files ------------------------------------------------------------------

def test_tabelle_13_gives_a_rate_for_every_wood_and_family():
    assert sia265.charring_rate("C24")["beta_n"] == 0.8
    assert sia265.charring_rate("GL24h")["beta_n"] == 0.7
    assert sia265.charring_rate("D30", "oak")["beta_n"] == 0.5
    assert sia265.charring_rate("D30", "beech")["beta_n"] == 0.8
    assert sia265.charring_rate("C24", "cladding")["beta_n"] == 0.9
    clause = sia265.fire()
    assert clause["d_red"]["value"] == 7 and clause["d_red"]["max_duration"] == 90
    assert [(r["duration"], r["b"]) for r in clause["min_width"]["rows"]] == [(30, 80), (60, 140)]
    assert clause["resistance_factor"]["value"] == 1.8


def test_a_hardwood_names_its_wood():
    try:
        sia265.charring_rate("D30")
    except Exception as exc:
        assert "beech and oak" in str(exc)
    else:
        raise AssertionError("D30 without a wood was given a charring rate")


def test_the_woods_and_the_faces_are_written_once():
    schema = json.loads((ROOT / "schemas" / "member-check-source.schema.json").read_text(encoding="utf-8"))
    fire = schema["properties"]["fire"]["properties"]
    assert tuple(w for w in fire["wood"]["enum"] if w is not None) == sia265.FIRE_WOODS[1:]
    assert tuple(fire["sides"]["required"]) == sia265.FIRE_SIDES


def test_the_fire_s_domain_imports_no_qt():
    """ARCH-001: what computes the fire situation and the required duration is Qt-free; the tab shows and calls it."""
    for path in ("calc/domains/member_check.py", "calc/norms/sia265.py", "calc/norms/vkf.py"):
        text = (ROOT / path).read_text(encoding="utf-8")
        assert not re.search(r"^\s*(?:from|import)\s+(?:PySide6|PyQt|shiboken)", text, re.M), path


def test_no_value_of_the_fire_clauses_is_written_in_the_code():
    """ARCH-002: β_n, d_red, 90 minutes, 80/140 mm, 1.8 and VKF 15-15's minutes are read from calc/norms/ -- never written in the arithmetic that uses them."""
    import inspect
    literals = re.compile(r"(?<![\w.])(0\.8|0\.7|0\.5|0\.9|1\.8|7|90|80|140|30|60|120)(?![\w.])")
    sources = {name: inspect.getsource(getattr(member_check, name)) for name in ("_fire_block", "fire_duration", "_compute")}
    sources["vkf.required_resistance"] = inspect.getsource(vkf.required_resistance)
    for name, text in sources.items():
        code = "\n".join(line.split("#", 1)[0] for line in text.splitlines())
        code = re.sub(r"\"[^\"]*\"|'[^']*'", "\"\"", code)        # the words of a reason, not a value
        found = literals.findall(code)
        assert not found, f"{name} writes {found} -- a value of SIA 265 4.5 or VKF 15-15 belongs in calc/norms/"


def _building(height, use, concept="construction", storeys="several"):
    return {"height": height, "use": use, "concept": concept, "storeys": storeys}


def test_vkf_15_15_gives_the_spec_s_four_cases():
    assert vkf.required_resistance(_building("low", "housing"))["minutes"] == 30
    assert vkf.required_resistance(_building("medium", "housing"))["minutes"] == 60
    assert vkf.required_resistance(_building("high", "housing"))["minutes"] == 90
    assert vkf.required_resistance(_building("medium", "industry_high", "extinction"))["minutes"] == 60


def test_vkf_15_15_applies_its_notes_as_the_file_states_them():
    # [1]: the top storey of tables 1 and 2 carries no requirement
    got = vkf.required_resistance(_building("medium", "office"), top_level=True)
    assert (got["minutes"], got["notes"]) == (0, ["1"])
    # [5]: two storeys, 2400 m² at most -- 30 minutes less where table 1 marks it, and not on a row it does not mark
    assert vkf.required_resistance(_building("low", "industry_high", storeys="two_small"))["minutes"] == 30
    assert vkf.required_resistance(_building("low", "lodging_a", storeys="two_small"))["minutes"] == 60
    assert vkf.required_resistance(_building("low", "lodging_c", "extinction", "two_small"))["minutes"] == 0
    # [8]: the top storey of a high building, 30 minutes less; [9]: a one-storey high building, none
    assert vkf.required_resistance(_building("high", "office"), top_level=True)["minutes"] == 60
    assert vkf.required_resistance(_building("high", "office", storeys="single"))["minutes"] == 0
    # 3.2.3 al. 2 c, d: a single-family house, a building of reduced size -- none, whatever the height
    got = vkf.required_resistance(_building("high", "single_family"))
    assert (got["minutes"], got["exemption"]) == (0, "3.2.3 al. 2 d")
    assert vkf.required_resistance(_building("medium", "small_building"))["exemption"] == "3.2.3 al. 2 c"
    # table 3 has no row for agriculture: no value, and a reason
    got = vkf.required_resistance(_building("high", "agriculture"))
    assert got["minutes"] is None and "no row" in got["reason"]


def test_a_building_s_data_is_checked_field_by_field():
    try:
        vkf.check_building({"height": "low", "use": "castle", "concept": "construction", "storeys": "several"}, "Woodcore-Datei/building.json")
    except Exception as exc:
        assert "building.json" in str(exc) and "use" in str(exc)
    else:
        raise AssertionError("an unknown use was accepted")


# --- a member in the fire situation, computed by the export (calc/domains/member_check.py) ------------------------
# Held against lib/timber.typ's #member(fire:) until the spec 2026-10-21-commandes-typst-refonte retired it (lot 19): the computation is member_check's alone, and the workbooks are held against it here.

def _computed(kind, grade, section, moisture_class, fire=None, **fields):
    """{key: value} of the rows member_check computes for a check written here, `fire` the fire situation's source fields or None."""
    src = member_check.new_source("FX-99", kind, fire=fire is not None)
    src.update(position=None, grade=grade, section=section, moisture_class=moisture_class, **fields)
    if fire is not None:
        src["fire"].update(fire)
    rec = member_check.resolve(member_check.stamp_version(src), {})
    assert rec["calculable"], rec["reason"]
    return {row["key"]: row["value"] for row in member_check.compute(rec)["rows"]}


def test_the_knicken_workbook_s_geometry_and_k_c_are_reproduced():
    """«fire, buckling» template, «4 seitiger Abbrand»: D30 (Eiche) 140/240, l 2.4 m, R30, N_d,fi 185 kN. Its resistance is k_fi · f_k (EN 1995-1-2); Woodcore's is 1.8 · k_c · f_c,0,d (SIA 265 (51), D-04)."""
    got = _computed("buckling", "D30", {"type": "rec", "b": 140, "h": 240}, 1, N={"value": 185, "unit": "kN"}, l_y=2400, l_z=2400,
                    fire={"duration": 30, "wood": "oak", "sides": {"bottom": True, "top": True, "left": True, "right": True}})
    assert close(got["lambda_z"], 86.60254037844386)
    assert close(got["lambda_rel_z"], 1.4079669684714229, 1e-9)
    assert close(got["k_c_z"], 0.42262472792804556, 1e-9)
    assert close(got["sigma_c_0_d"], 185000 / (96 * 196))
    # f_c,0,k and E_0,05 are the norm's, unscaled; f_c,0,d is 1.8 times the table's
    assert (got["f_c_0_k"], got["E_0_05"]) == (24, 9200)
    assert close(got["f_c_0_d"], 1.8 * 14.1)
    assert close(got["eta"], got["sigma_c_0_d"] / (got["k_c_z"] * 1.8 * 14.1))


def test_glulam_takes_no_k_h_and_eta_w_stays_in_the_fire():
    got = _computed("bending", "GL24h", {"type": "rec", "b": 160, "h": 320}, 2, M_y={"value": 10, "unit": "kNm"},
                    fire={"duration": 30, "sides": {"bottom": True, "top": False, "left": False, "right": False}})
    assert "k_h_y" not in got
    assert close(got["f_m_y_d"], 1.8 * sia265.eta_w(2) * 16.0)


def test_a_member_without_fire_is_what_it_was():
    got = _computed("bending", "GL24h", {"type": "rec", "b": 160, "h": 320}, 1, M_y={"value": 10, "unit": "kNm"})
    rule = sia265.k_h()
    k_h = min((rule["reference_height"] / 320) ** rule["exponent"], rule["maximum"])   # SIA 265 (5), read off the norm file
    assert k_h > 1 and close(got["f_m_y_d"], k_h * 16.0), (k_h, got["f_m_y_d"])


# --- a check in the fire situation, saved in Woodcore (calc/domains/member_check.py) ---------------

from domains import member_check   # noqa: E402

POSITIONS = {"T001": {"strength_class": "C24", "moisture_class": 2, "section": {"type": "rec", "kind": "timber", "text": "100/200 mm", "b": 100, "h": 200}},
             "R001": {"strength_class": "GL24h", "moisture_class": 1, "section": {"type": "cir", "kind": "timber", "text": "Ø 200 mm", "d": 200}},
             "E001": {"strength_class": "D30", "moisture_class": 1, "section": {"type": "rec", "kind": "timber", "text": "140/240 mm", "b": 140, "h": 240}}}


def _fire_src(kind="bending", **change):
    src = member_check.new_source("FE-99", kind, fire=True)
    src.update(position="T001")
    fire = change.pop("fire", {})
    src.update(change)
    src["fire"].update(fire)
    return member_check.stamp_version(src)


def _refused(src, words):
    try:
        member_check.check_source(src, "checks/FE-99.json")
    except validation.ValidationError as exc:
        assert words in str(exc), str(exc)
        assert "FE-99" in str(exc)
    else:
        raise AssertionError("accepted: %r" % (src,))


import validation   # noqa: E402


def test_a_fire_check_is_saved_at_1_2_and_a_cold_one_as_it_was():
    src = _fire_src()
    assert src["schema_version"] == "1.2" and src["fire"] == member_check.FIRE_DEFAULT
    member_check.check_source(src)
    cold = member_check.new_source("BI-99", "bending")
    assert cold["schema_version"] == "1.0" and "fire" not in cold
    assert "fire" not in member_check.stamp_version(dict(cold, fire=None))


def test_a_malformed_fire_stops_naming_the_field():
    _refused(dict(_fire_src(), schema_version="1.1"), "schema_version")
    _refused(_fire_src(kind="bending", alpha=30), "along the grain")
    src = _fire_src()
    src["kind"] = "lateral-torsional"
    _refused(src, "fire on a lateral-torsional")
    _refused(_fire_src(fire={"duration": 0}), "fire.duration")
    _refused(_fire_src(fire={"sides": {"bottom": True}}), "fire.sides")
    _refused(_fire_src(fire={"wood": "pine"}), "fire.wood")
    src = _fire_src()
    src["fire"]["colour"] = "red"
    _refused(src, "fire.colour")


def test_a_fire_check_follows_vkf_15_15_or_its_own_duration():
    building = {"height": "medium", "use": "housing", "concept": "construction", "storeys": "several"}
    src = _fire_src(grade="C24", section={"type": "rec", "b": 140, "h": 200})
    rec = member_check.resolve(src, POSITIONS, building=building)
    assert rec["calculable"], rec["reason"]
    assert (rec["fire"]["duration"], rec["fire"]["duration_from"]) == (60, "vkf")
    assert rec["fire"]["requirement"]["table"] == "2"
    assert close(rec["fire"]["b"], 30) and close(rec["fire"]["h"], 145)
    # the top storey: note [1], no requirement, and the check says so
    top = member_check.resolve(_fire_src(grade="C24", section={"type": "rec", "b": 140, "h": 200}, fire={"top_level": True}), POSITIONS, building=building)
    assert not top["calculable"] and "requires no fire resistance" in top["reason"] and "[1]" in top["reason"]
    # written over: stays, whatever the building says
    own = member_check.resolve(_fire_src(grade="C24", section={"type": "rec", "b": 140, "h": 200}, fire={"duration": 30}), POSITIONS, building=building)
    assert (own["fire"]["duration"], own["fire"]["duration_from"]) == (30, "stated")
    # no building and no duration: a gap of the project, never a stop
    none = member_check.resolve(_fire_src(), POSITIONS)
    assert not none["calculable"] and "no fire resistance" in none["reason"]


def test_what_the_project_lacks_makes_a_fire_check_not_calculable():
    def reason(**change):
        rec = member_check.resolve(_fire_src(**change), POSITIONS)
        assert not rec["calculable"]
        return rec["reason"]
    assert "4.5.2.4" in reason(section={"type": "rec", "b": 120, "h": 200}, fire={"duration": 60})
    assert "90 minutes" in reason(fire={"duration": 120})
    assert "choose the wood" in reason(position="E001", fire={"duration": 30})
    assert "round section" in reason(position="R001", fire={"duration": 30})
    assert "no face" in reason(fire={"duration": 30, "sides": {"bottom": False, "top": False, "left": False, "right": False}})
    assert "leaves no section" in reason(section={"type": "rec", "b": 140, "h": 50}, fire={"duration": 60, "sides": {"bottom": True, "top": False, "left": False, "right": False}})
    # oak named: calculable
    assert member_check.resolve(_fire_src(position="E001", fire={"duration": 30, "wood": "oak"}), POSITIONS)["calculable"]


def test_the_window_s_result_is_the_biegung_workbook():
    src = _fire_src(grade="C24", section={"type": "rec", "b": 140, "h": 200}, moisture_class=1, M_y={"value": 1.9375 * 25 / 8, "unit": "kNm"}, fire={"duration": 60})
    result = member_check.compute(member_check.resolve(src, POSITIONS))
    assert close(result["eta"], 2.2693114598647526, 1e-9)
    rows = {row["key"]: row for row in result["rows"]}
    assert close(rows["W_y"]["value"], 105125) and rows["k_fi"]["value"] == 1.8 and rows["f_m_y_d"]["formula"].startswith("k_(fi) dot")
    assert "k_h_y" not in rows


def test_the_building_file_is_checked_and_written(tmp=None):
    class Here:
        pass
    here = Here()
    here.rel = lambda path: path.name   # what a message names the file by, as Project.rel does
    d = conftest.probe_dir("fire_building")
    here.building_file = d / "building.json"
    assert member_check.read_building(here) is None
    member_check.write_building({"height": "low", "use": "office", "concept": "extinction", "storeys": "two_small"}, here)
    assert member_check.read_building(here)["schema_version"] == "1.0"
    here.building_file.write_text(json.dumps({"schema_version": "1.0", "height": "tall", "use": "office", "concept": "extinction", "storeys": "several"}), encoding="utf-8")
    try:
        member_check.read_building(here)
    except validation.ValidationError as exc:
        assert "building.json" in str(exc) and "height" in str(exc)
    else:
        raise AssertionError("a malformed building was read")
