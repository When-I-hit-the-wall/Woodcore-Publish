"""The material of a member check -- a class of SIA 265, a member of the engineer's own, a panel of SIA 265/1 (calc/domains/member_check_material.py, calc/domains/member_check.py; spec docs/requirements/completed/2026-10-24-verifications-elements-v3.md; issue #112). Without a window.

What is held:

* **REQ-001** -- the source 1.3: `material`, `loading`, `kled`, `accidental`, `display` written and read; 1.0 to 1.2 read as they are; `grade` with `material`, `loading` on a member, `impact` on a panel, a null, an unknown version refused naming the field; the JSON schema holds the three;
* **REQ-002** -- a member of one's own named by a check copied into the project at the save, and the check computed from the copy alone; an unknown id not calculable, naming it;
* **REQ-003** -- C24 and GL24h by `material` are the same rows and ratios as by `grade`; a complete member of one's own computes, each design value saying how it was had;
* **REQ-004 / REQ-007** -- OSB/3 in each loading and each range, 6, 10, 18, 25 mm on their limits, 5 and 26 mm out with the ranges; BI-04 77.2 %;
* **REQ-005** -- what each check reads; a panel in compression across the grain, in stability, in shear-off not calculable, a member of one's own without f_t,90,d or E_0,05 likewise -- naming material, loading and quantity;
* **REQ-006** -- the factors: a member's table value × η_w × η_t; a panel's b value at class 1, KLED medium, normal; η_mod · f_k / γ_M otherwise (OSB/3 class 2: 0.55); γ_M = 1.0 accidental; OSB/3 in class 3 refused; no k_h;
* **REQ-008** -- σ_90,d outside −f_c,90,d … f_t,90,d an orange note, the check computed;
* **REQ-009 / REQ-010 / REQ-011** -- the file names the panel and SIA 265/1; `display` written into the file of a check and taken off again; the kind changed by the stability, the file moved and the engineer's line kept;
* **REQ-013, REQ-014, REQ-015, REQ-016** -- following the position and writing over it said; the governing row marked; the export 1.7 carrying the material; the fire refusing a panel;
* **ARCH-002** -- no table of resistance in member_check*.py.
"""

TIER = "fast"  # tests/run_tests.py --fast

import copy
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import conftest
import project
import validation
from domains import materials_project, materials_user, member_check as mc, member_check_material as mm, unfold

POSITIONS = {
    "T001": {"strength_class": "C24", "moisture_class": 2, "section": {"type": "rec", "kind": "timber", "text": "100/200 mm", "b": 100, "h": 200}},
}


def _src(kind="bending", **change):
    src = mc.new_source("PR-01", kind)
    src.update(change)
    return mc.stamp_version(src)


def _panel(thickness=18, mode="plaque", direction="par", kind="bending", moisture=1, **change):
    src = mc.new_source("BI-04", kind)
    src.update(section={"type": "rec", "b": 1000, "h": thickness}, moisture_class=moisture, material="sia265-1:osb3", loading={"mode": mode, "direction": direction})
    if kind == "bending":
        src.update(M_y={"value": 0.4, "unit": "kNm"})
    src.update(change)
    return mc.stamp_version(src)


def _refused(src, *words):
    try:
        mc.check_source(src, "checks/probe.json")
    except validation.ValidationError as exc:
        for word in words:
            assert word in str(exc), (word, str(exc))
        return str(exc)
    raise AssertionError("accepted: %r" % src)


def _row(result, key):
    return next(r for r in result["rows"] if r["key"] == key)


# --- REQ-001 the source ------------------------------------------------------------------------

def test_a_source_of_1_3_is_written_read_and_checked():
    src = _panel()
    assert src["schema_version"] == "1.3" and "kled" not in src
    mc.check_source(src)
    validation.validate_structure(src, "member-check-source")
    # «Reprendre»: material taken off, the source goes back to the lowest version that holds it
    back = mc.stamp_version({k: v for k, v in src.items() if k not in ("material", "loading")})
    assert back["schema_version"] == "1.0" and "material" not in back
    # a class of SIA 265 written over the position
    stated = _src(material="sia265:GL24h")
    mc.check_source(stated)
    assert stated["schema_version"] == "1.3" and stated["grade"] is None
    # display alone is 1.3 too; its defaults are left out
    shown = _src(display={"level": 2, "verdict": "percent"})
    assert shown["display"] == {"level": 2} and shown["schema_version"] == "1.3"
    assert "display" not in _src(display={"verdict": "percent", "title": True})


def test_each_defect_of_1_3_is_refused_naming_the_field():
    _refused(dict(_src(material="sia265:C24"), grade="C24"), "grade", "material")
    _refused(dict(_src(), schema_version="1.3", loading={"mode": "plaque", "direction": "par"}), "loading")
    _refused(dict(_src(material="sia265:C24"), loading={"mode": "plaque", "direction": "par"}), "loading", "class of SIA 265")
    _refused(dict(_panel(), impact=True), "impact")
    _refused(dict(_panel(), loading={"mode": "beam", "direction": "par"}), "loading")
    _refused(dict(_panel(), kled="eternal"), "kled")
    _refused(dict(_panel(), accidental="yes"), "accidental")
    _refused(dict(_panel(), material=None), "material is null")
    _refused(dict(_src(material="sia265:C99")), "C99")
    _refused(dict(_src(material="ext:12")), "material")
    _refused(dict(_src(display={"level": 5})), "display.level")
    _refused(dict(_src(display={"colour": "red"})), "display.colour")
    _refused(dict(_panel(), schema_version="1.2"), "schema_version", "1.3")
    _refused(dict(_panel(), schema_version="1.4"), "schema_version")


def test_the_example_s_sources_are_read_as_they_are():
    for path in sorted((conftest.EXAMPLE / project.WOODCORE_FOLDER / "sources" / "checks").glob("*.json")) if hasattr(conftest, "EXAMPLE") else []:
        before = path.read_bytes()
        src = mc.read_source(path)
        assert src["schema_version"] in ("1.0", "1.1", "1.2") and path.read_bytes() == before
    here = conftest.project_copy("mcm_sources")
    for path in mc.source_paths(here):
        src = mc.read_source(path)
        assert src["schema_version"] in ("1.0", "1.1", "1.2"), path.name
        assert mc.stamp_version(copy.deepcopy(src))["schema_version"] == src["schema_version"], "a source of before is saved at its own version"


# --- REQ-003 a class of SIA 265 by material, a member of one's own ---------------------------------------

def test_a_class_by_material_is_the_class_by_grade():
    for grade, kind, change in (("C24", "bending", {"M_z": {"value": 0.3, "unit": "kNm"}}), ("GL24h", "tension", {}), ("C24", "shear", {}), ("GL24h", "buckling", {})):
        base = dict(change, section={"type": "rec", "b": 100, "h": 200}, moisture_class=2)
        by_grade = mc.resolve(_src(kind, grade=grade, **base), {})
        by_material = mc.resolve(_src(kind, material="sia265:" + grade, **base), {})
        assert by_material["grade"] == grade and by_material["grade_from"] == "stated"
        assert mc.compute(by_grade)["rows"] == mc.compute(by_material)["rows"] and mc.compute(by_grade)["eta"] == mc.compute(by_material)["eta"], (grade, kind)


def _mine(values, family="softwood", mid="u-0000a0b1"):
    return {"id": mid, "type": "member", "family": family, "values": values, "names": {"fr": "Mon épicéa", "de": "Meine Fichte", "en": "My spruce"},
            "category": "wood", "source": {"kind": "url", "url": "https://example.org/fiche", "ref": "Fiche produit"}}


def test_a_member_of_one_s_own_computes_saying_how_each_value_was_had():
    mine = _mine({"f_m_k": 24, "f_t_0_d": 9.0, "f_c_0_k": 21})
    src = _src("tension", material=mine["id"], section={"type": "rec", "b": 100, "h": 200}, moisture_class=2)
    rec = mc.resolve(src, {}, library={mine["id"]: mine})
    assert rec["calculable"], rec["reason"]
    assert rec["resistance"]["type"] == "member" and rec["resistance"]["values"]["f_t_0"] == {"value": 9.0, "how": "typed", "clause": ""}
    result = mc.compute(rec)
    f = _row(result, "f_t_0_d")
    assert abs(f["value"] - 0.8 * 9.0) < 1e-12 and f["label"] == "eingegeben" and f["table"]["value"] == 9.0
    # deduced and set values cite their clause
    bend = mc.resolve(_src("bending", material=mine["id"], section={"type": "rec", "b": 100, "h": 200}, moisture_class=1), {}, library={mine["id"]: mine})
    f_m = _row(mc.compute(bend), "f_m_y_d")
    assert f_m["value"] == 14.1, "f_m,k 24 / 1.7 = 14.1, rounded as the norm prints"
    shear = mc.resolve(_src("shear", material=mine["id"], section={"type": "rec", "b": 100, "h": 200}, moisture_class=1), {}, library={mine["id"]: mine})
    f_v = _row(mc.compute(shear), "f_v_d")
    assert f_v["label"] == "von der Norm festgelegt" and f_v["clause"] == "3.3.2.2"


def test_what_a_member_of_one_s_own_lacks_is_said():
    mine = _mine({"f_m_k": 24}, mid="u-0000a0b2")
    # no f_t,0 (neither typed nor deduced): the tension refused, naming it
    rec = mc.resolve(_src("tension", material=mine["id"], section={"type": "rec", "b": 100, "h": 200}, moisture_class=1), {}, library={mine["id"]: mine})
    assert not rec["calculable"] and rec["reason_code"] == "material_lacks" and "f_t,0,d" in rec["reason_params"]["missing"]
    # no E_0,05 in the library: no stability of one's own (REQ-005)
    full = _mine({"f_m_k": 24, "f_c_0_k": 21, "f_t_0_k": 14}, mid="u-0000a0b3")
    rec = mc.resolve(_src("buckling", material=full["id"], section={"type": "rec", "b": 100, "h": 200}, moisture_class=1), {}, library={full["id"]: full})
    assert not rec["calculable"] and "E_0,05" in rec["reason_params"]["missing"]
    # f_t,90,d is set by the norm for softwood -- the shear across the grain computes
    perp = mc.resolve(_src("shear", material=full["id"], variant="shear-perp", sigma_90=-1.0, section={"type": "rec", "b": 100, "h": 200}, moisture_class=1), {}, library={full["id"]: full})
    assert not perp["calculable"] and "f_c,90,d" in perp["reason_params"]["missing"], "no f_c,90 typed nor deduced"


def test_an_unknown_material_is_not_calculable_naming_it():
    rec = mc.resolve(_src("tension", material="u-deadbeef", section={"type": "rec", "b": 100, "h": 200}, moisture_class=1), {}, library={})
    assert not rec["calculable"] and rec["reason_code"] == "unknown_material" and "u-deadbeef" in rec["reason"]


def test_a_member_of_one_s_own_is_copied_into_the_project_and_computed_from_the_copy():
    here = conftest.project_copy("mcm_copy")
    mine = _mine({"f_m_k": 24, "f_t_0_k": 14, "f_c_0_k": 21}, mid="u-0000a0c1")
    materials_user.save(mine)
    src = _src("tension", material=mine["id"], section={"type": "rec", "b": 100, "h": 200}, moisture_class=1, N={"value": 20, "unit": "kN"})
    src["id"] = "ZT-77"
    with project.using(here):
        mc.write_source(here, src)
        assert mine["id"] in materials_project.used_ids(here)
        data = mc.export(here)
        assert data["checks"]["ZT-77"]["calculable"], data["checks"]["ZT-77"]["reason"]
        assert materials_project.find(mine["id"], here) is not None, "the copy is in Woodcore-Datei/materials.json"
        materials_user.delete(mine["id"])
        again = mc.export(here)
    assert again["checks"]["ZT-77"]["calculable"] and mc.compute(again["checks"]["ZT-77"])["eta"] == mc.compute(data["checks"]["ZT-77"])["eta"], "the library gone, the copy computes"
    assert again["schema_version"] == mc.LIBRARY_EXPORT_VERSION


# --- REQ-004 / REQ-007 a panel -----------------------------------------------------------------------

def test_osb3_in_each_loading_and_each_range():
    expected = {6: (10.5, 5.3, 5.8, 4.2), 8: (10.5, 5.3, 5.8, 4.2), 10: (10.5, 5.3, 5.8, 4.2), 12: (9.6, 4.8, 5.5, 4.1), 18: (9.6, 4.8, 5.5, 4.1), 22: (8.6, 4.3, 5.3, 4.0), 25: (8.6, 4.3, 5.3, 4.0)}
    for thickness, values in expected.items():
        got = []
        for mode, direction in mm.TAB_LOADINGS["bending"]:
            src = _panel(thickness, mode, direction)
            rec = mc.resolve(src, {})
            assert rec["calculable"], (thickness, mode, rec["reason"])
            got.append(_row(mc.compute(rec), "f_m_y_d")["value"])
        assert tuple(got) == values, (thickness, got)


def test_a_thickness_out_of_the_ranges_is_refused_with_the_ranges():
    for thickness in (5, 26):
        rec = mc.resolve(_panel(thickness), {})
        assert not rec["calculable"] and rec["reason_code"] == "thickness_out"
        assert rec["reason_params"]["ranges"] == "6–10 mm, 10–18 mm, 18–25 mm" and "6–10 mm, 10–18 mm, 18–25 mm" in rec["reason"]


def test_bi_04_is_77_2_percent_the_b_table_s_value():
    rec = mc.resolve(_panel(), {})
    result = mc.compute(rec)
    assert abs(result["eta"] - 7.407407407407407 / 9.6) < 1e-12 and round(result["eta"] * 100, 1) == 77.2
    f = _row(result, "f_m_y_d")
    assert (f["value"], f["clause"], f["norm"], f["label"]) == (9.6, "Tableau 19b", "SIA 265/1", "10–18 mm")
    assert rec["resistance"]["range"] == "10–18 mm" and rec["resistance"]["table"] == "19" and rec["resistance"]["page"] == 42
    assert not any(r["key"].startswith("k_h") for r in result["rows"]), "no k_h for a panel"


def test_a_panel_s_thickness_not_the_side_its_loading_supposes_is_said():
    rec = mc.resolve(_panel(18, "voile"), {})
    assert rec["calculable"] and any(n["code"] == "panel_side" for n in rec["notes"])
    assert not any(n["code"] == "panel_side" for n in mc.resolve(_panel(18, "plaque"), {}).get("notes", []))


# --- REQ-005 what a check reads -----------------------------------------------------------------------

def test_what_each_check_reads():
    assert mm.needs("tension") == ["f_t_0"] and mm.needs("tension", 30) == ["f_t_0", "f_t_90"]
    assert mm.needs("compression", 90) == ["f_c_90"] and mm.needs("bending", normal=-5) == ["f_m", "f_c_0"]
    assert mm.needs("shear", variant="shear-off") == ["f_v", "k_a"] and mm.needs("shear", variant="shear-perp") == ["f_v", "f_t_90", "f_c_90"]
    assert mm.needs("buckling") == ["f_c_0", "f_c_0_k", "E_0_05", "beta_c"]


def test_a_panel_refuses_what_it_does_not_give():
    across = mc.resolve(_panel(kind="compression", alpha=90, l=100, N={"value": 5, "unit": "kN"}, mode="tc"), {})
    assert not across["calculable"] and across["reason_code"] == "material_lacks" and across["reason_params"]["missing"] == "f_c,90,d"
    assert across["reason_params"]["loading"] == "tc-par" and across["reason_params"]["kind"] == "compression"
    buckling = mc.resolve(_panel(kind="buckling", N={"value": 5, "unit": "kN"}, mode="tc"), {})
    assert not buckling["calculable"] and "E_0,05" in buckling["reason_params"]["missing"]
    off = mc.resolve(_panel(kind="shear", variant="shear-off", F={"value": 5, "unit": "kN"}, l=200), {})
    assert not off["calculable"] and "k_a" in off["reason_params"]["missing"]
    # what it gives, it computes: shear as a plate and as a diaphragm, tension and compression in its plane
    assert mc.resolve(_panel(kind="shear", V_z={"value": 2, "unit": "kN"}), {})["calculable"]
    assert mc.resolve(_panel(kind="shear", mode="voile", V_z={"value": 2, "unit": "kN"}), {})["calculable"]
    t = mc.resolve(_panel(kind="tension", mode="tc", direction="perp", N={"value": 20, "unit": "kN"}), {})
    assert t["calculable"] and _row(mc.compute(t), "f_t_0_d")["value"] == 4.1


# --- REQ-006 the factors -----------------------------------------------------------------------------

def test_the_factors_of_a_member_and_of_a_panel_follow_the_norm():
    impact = mc.resolve(_src("tension", grade="C24", impact=True, section={"type": "rec", "b": 100, "h": 200}, moisture_class=3), {})
    f = _row(mc.compute(impact), "f_t_0_d")
    assert abs(f["value"] - 0.6 * 1.4 * 8.5) < 1e-12
    class2 = mc.compute(mc.resolve(_panel(moisture=2), {}))
    assert _row(class2, "eta_mod")["value"] == 0.55 and _row(class2, "gamma_M")["value"] == 1.2
    assert abs(_row(class2, "f_m_y_d")["value"] - 0.55 * 16.4 / 1.2) < 1e-12, "unrounded, D-23"
    short = mc.compute(mc.resolve(_panel(kled="short"), {}))
    assert abs(_row(short, "f_m_y_d")["value"] - 0.9 * 16.4 / 1.2) < 1e-12
    accidental = mc.compute(mc.resolve(_panel(accidental=True), {}))
    assert _row(accidental, "gamma_M")["value"] == 1.0 and abs(_row(accidental, "f_m_y_d")["value"] - 0.7 * 16.4 / 1.0) < 1e-12
    refused = mc.resolve(_panel(moisture=3), {})
    assert not refused["calculable"] and refused["reason_code"] == "class_not_admitted" and refused["reason_params"]["classes"] == "1, 2"
    assert _row(class2, "eta_mod")["norm"] == "SIA 265/1" and _row(class2, "eta_mod")["clause"] == "Tableau 9"


# --- REQ-008 σ_90 outside ------------------------------------------------------------------------------

def test_sigma_90_outside_the_interval_is_said_and_computed():
    out = mc.compute(mc.resolve(_src("shear", grade="C24", variant="shear-perp", sigma_90=5, section={"type": "rec", "b": 100, "h": 200}, moisture_class=1), {}))
    assert out["eta"] > 0 and out["notes"][0]["code"] == "sigma_90_outside" and out["notes"][0]["field"] == "sigma_90"
    inside = mc.compute(mc.resolve(_src("shear", grade="C24", variant="shear-perp", sigma_90=-1, section={"type": "rec", "b": 100, "h": 200}, moisture_class=1), {}))
    assert "notes" not in inside


# --- REQ-013, REQ-014, REQ-015, REQ-016 -------------------------------------------------------------------

def test_a_material_written_over_the_position_is_said():
    follows = mc.resolve(_src("tension", position="T001"), POSITIONS)
    assert follows["grade"] == "C24" and follows["grade_from"] == "position" and "material" not in follows
    over = mc.resolve(_src("tension", position="T001", material="sia265:GL24h"), POSITIONS)
    assert over["grade"] == "GL24h" and over["material"]["from"] == "stated"
    assert over["notes"][0] == {"code": "material_overrides", "params": {"material": "sia265:GL24h", "position": "T001", "held": "C24"}}


def test_the_governing_row_is_marked_and_eta_is_last():
    data = conftest.exported(mc.EXPORT_FILE)
    for cid in ("BI-01", "KN-01", "DR-01"):
        result = mc.compute(data["checks"][cid])
        assert result["rows"][-1]["key"] == "eta"
    assert mc.compute(data["checks"]["BI-01"])["governing"] == [], "η of (14) is a sum, no maximum"
    kn = mc.compute(data["checks"]["KN-01"])
    assert len(kn["governing"]) == 1 and _row(kn, kn["governing"][0])["value"] == max(r["value"] for r in kn["rows"] if r["key"] in mc.GOVERNING_KEYS)


def test_the_export_of_a_panel_is_1_7_and_says_its_material():
    here = conftest.project_copy("mcm_export")
    src = _panel()
    with project.using(here):
        mc.write_source(here, src)
        data = mc.export(here)
    rec = data["checks"]["BI-04"]
    assert data["schema_version"] == "1.7" and rec["material"]["id"] == "sia265-1:osb3" and rec["loading"] == {"mode": "plaque", "direction": "par"}
    assert rec["kled"] == "medium" and rec["accidental"] is False and rec["grade"] is None
    validation.validate_structure(data, "checks")
    validation.validate_checks_business(data)
    assert all(data["checks"][cid]["calculable"] for cid in ("ZT-01", "DR-01", "BI-01"))


def test_the_fire_reads_a_class_of_sia_265_only():
    data = conftest.exported(mc.EXPORT_FILE)
    assert data["checks"]["FE-01"]["calculable"]
    src = mc.new_source("FE-09", "bending", fire=True)
    src.update(section={"type": "rec", "b": 1000, "h": 18}, moisture_class=1, material="sia265-1:osb3", loading={"mode": "plaque", "direction": "par"})
    src["fire"]["duration"] = 30
    src = mc.stamp_version(src)
    mc.check_source(src)
    rec = mc.resolve(src, {})
    assert not rec["calculable"] and rec["reason_code"] == "fire_material"


# --- REQ-009 / REQ-010 / REQ-011 the file ---------------------------------------------------------------

def test_the_file_of_a_panel_names_it_and_its_norm():
    here = conftest.project_copy("mcm_file")
    with project.using(here):
        mc.write_source(here, _panel())
        mc.export(here)
        text = unfold.domain_path(here, "BI-04", kind="check").read_text(encoding="utf-8")
        published = json.loads((here.data_dir / mc.EXPORT_FILE).read_text(encoding="utf-8"))["checks"]["BI-04"]["vars"]
    assert "OSB/3" in text and "Plattenbeanspruchung" in text
    assert published["f_m_y_d"]["norm"] == "SIA 265/1" and published["f_m_y_d"]["norm_ref"] == "Tableau 19b"


def test_the_options_of_affichage_are_kept_in_the_source_and_written_into_the_file():
    here = conftest.project_copy("mcm_display")
    with project.using(here):
        mc.export(here)
        path = unfold.domain_path(here, "BI-01", kind="check")
        before = path.read_text(encoding="utf-8")
        src = mc.read_source(here.checks_dir / "BI-01.json")
        src["display"] = {"level": 2, "member_line": "none", "description": True, "title": False, "verdict": "ratio"}
        mc.write_source(here, mc.stamp_version(src))
        mc.export(here)
        text = path.read_text(encoding="utf-8")
        assert re.search(r'#domain\("BI-01", label: "[^"]+", descr: "[^"]+", label-position: "none", level: 2\)\[', text), text[:400]
        assert "// *T001*" in text and '#eq("eta", `sigma_m_y_d / f_m_y_d + sigma_m_z_d / f_m_z_d`, id: "eta")' in text
        # taken off again: the file as before
        src.pop("display")
        mc.write_source(here, mc.stamp_version(src))
        src2 = mc.read_source(here.checks_dir / "BI-01.json")
        src2["display"] = {"verdict": "percent"}
        mc.write_source(here, mc.stamp_version(src2))
        mc.export(here)
        assert path.read_text(encoding="utf-8").split("\n")[2] == before.split("\n")[2], "the header as it was"


def test_the_stability_changes_the_kind_and_moves_the_file():
    here = conftest.project_copy("mcm_move")
    with project.using(here):
        mc.export(here)
        old = unfold.domain_path(here, "DR-02", kind="check")
        src = mc.read_source(here.checks_dir / "DR-02.json")
        assert src["kind"] == "compression"
        text = old.read_text(encoding="utf-8")
        old.write_text(text.replace('  #eq("A"', 'Mon commentaire.\n  #eq("A"', 1), encoding="utf-8", newline="\n")
        new_src = mc.change_kind(src, True)
        assert new_src["kind"] == "buckling" and new_src["alpha"] == 0 and new_src["l_y"] == 3000 and new_src["id"] == "DR-02"
        mc.write_source(here, mc.stamp_version(new_src))
        moved = mc.save_kind_change(here, "DR-02", "compression", "buckling")
        data = mc.export(here, moved=moved)
        new = here.domain_dir("check", "buckling") / "DR-02.typ"
        moved_text = new.read_text(encoding="utf-8")
        assert not old.exists() and new.is_file() and "Mon commentaire." in moved_text, moved_text[:600]
        assert "Stabilität – DR-02" in moved_text and '"l_k_y"' in moved_text, "the new form written, its title with it"
        assert data["checks"]["DR-02"]["kind"] == "buckling"
        back = mc.change_kind(new_src, False)
        assert back["kind"] == "compression" and "l_y" not in back


# --- ARCH-002 no table of resistance written in the module -----------------------------------------------

def test_no_resistance_is_written_in_the_check_s_modules():
    for name in ("member_check.py", "member_check_material.py"):
        text = (conftest.ROOT / "calc" / "domains" / name).read_text(encoding="utf-8")
        for value in ("14.1", "9.6", "16.4", "0.55", "1.2,", "10.5"):
            assert not re.search(r"(?<![\d.])%s(?![\d])" % re.escape(value), text), (name, value)
