"""The four member checks' tabs as their type reads them, without a window (calc/domains/member_check_view.py; spec docs/requirements/completed/2026-10-24-verifications-elements-v3.md, UI-002, UI-007, UI-009, UI-010, UI-012, REQ-011; issue #112).

What is held: each tab's domain lists its kinds; the box «vérifier la stabilité» turns the kind in the draft and never reaches the file; the rows a draft shows (no angle for a panel, the contact at an angle, the shear's figure); the messages -- a refusal by its code, the orange notes, none of the stability --; the rows in the order of `compute`, η last; the scheme of a bending black and white, without a word, its edge values `compute`'s; the charts' points `compute`'s; the module imports no Qt.
"""

TIER = "fast"  # tests/run_tests.py --fast

import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import conftest
import project
from domains import member_check as mc, member_check_view as view


def test_each_tab_lists_its_kinds_and_the_stability_box_turns_the_kind():
    assert view.DOMAINS["compression"].KINDS == ("compression", "buckling") and view.DOMAINS["bending"].KINDS == ("bending", "lateral-torsional")
    assert view.domain_of_kind("buckling") is view.DOMAINS["compression"]
    d = view.DOMAINS["compression"]
    src = d.new_source("DR-77")
    assert src["stability"] is False and d.owns(src) and not view.DOMAINS["tension"].owns(src)
    src["stability"] = True
    d.stamp_version(src)
    assert src["kind"] == "buckling" and src["l_y"] == 3000 and src["stability"] is True
    assert "stability" not in d.to_file(src)
    d.check_source(src, "checks/DR-77.json")
    src["stability"] = False
    d.stamp_version(src)
    assert src["kind"] == "compression" and "l_y" not in src
    fire = mc.new_source("FE-77", "bending", fire=True)
    assert not view.DOMAINS["bending"].owns(fire), "a check in the fire situation is the fire tab's"


def test_the_rows_a_draft_shows():
    t = view.DOMAINS["tension"]
    src = t.new_source("Z_9")
    assert "alpha" in t.visible_fields(src)
    assert "alpha" not in t.visible_fields(dict(src, material="sia265-1:osb3")), "a panel's direction replaces the angle"
    c = view.DOMAINS["compression"]
    s = c.new_source("DR-9")
    assert "l" not in c.visible_fields(s) and "l" in c.visible_fields(dict(s, alpha=90)) and "support" in c.visible_fields(dict(s, alpha=90))
    sh = view.DOMAINS["shear"]
    s = sh.new_source("SC-9")
    assert set(sh.visible_fields(dict(s, variant="shear-off"))) == {"variant", "F", "l", "w"}
    assert set(sh.visible_fields(dict(s, variant="shear-perp"))) == {"variant", "V_z", "sigma_90"}


def test_the_five_cards_of_f_c_90_d_are_the_table_s_and_written_as_case_and_larger():
    """UI-008: five cards -- generell, mit Vorholz with and without consequence, Endauflagerung with and without --, their values SIA 265 Tabelle 8's for the draft's class, D30's bracketed ones absent (greyed); a card is the file's `case` and `larger`, never held itself."""
    from norms import sia265
    c = view.DOMAINS["compression"]
    src = c.new_source("DR-9")
    assert src["support"] == "generell" and "support" not in c.to_file(src)
    src.update(alpha=90, l=160, grade="C24", section={"type": "rec", "b": 100, "h": 200})
    cards = c.choice_values(src)["support"]
    assert list(cards) == list(view.SUPPORTS) and len(cards) == 5
    table = sia265.grade("C24")["f_c_90_d"]
    for support, said in cards.items():
        case, larger = (support[:-len("-larger")], True) if support.endswith("-larger") else (support, False)
        cell = table[case]
        expected = (cell.get("groessere_eindrueckungen") if larger else cell.get("value")) if isinstance(cell, dict) else (None if larger else cell)
        assert said["value"] == expected and said["enabled"] == (expected is not None), (support, said)
    d30 = c.choice_values(dict(src, grade="D30"))["support"]
    assert d30["mit_vorholz-larger"]["value"] is None and not d30["mit_vorholz-larger"]["enabled"] and d30["mit_vorholz"]["enabled"]
    src["support"] = "endauflagerung-larger"
    out = c.to_file(src)
    assert (out["case"], out["larger"]) == ("endauflagerung", True) and "support" not in out
    c.stamp_version(src)
    assert (src["case"], src["larger"], src["support"]) == ("endauflagerung", True, "endauflagerung-larger")
    src["support"] = "generell"
    c.stamp_version(src)
    assert (src["case"], src["larger"]) == ("generell", False)
    c.check_source(src, "checks/DR-9.json")
    assert c.choice_values(dict(src, grade=None, material="sia265-1:osb3")) == {} and view.DOMAINS["tension"].choice_values(src) == {}


def test_messages_rows_the_scheme_and_the_charts_are_compute_s():
    here = conftest.project_copy("member_check_view")
    with project.using(here):
        mc.export(here)
        b = view.DOMAINS["bending"]
        src = b.read_source(here.checks_dir / "BI-02.json")
        assert not any("stabil" in m.code for m in b.messages(src))
        instance = b.build_instance(src, here)
        assert b.results(instance)[-1] == "eta" and b.results(instance) == [r["key"] for r in instance["result"]["rows"]]
        svg = b.figure_svg(src)
        result = mc.compute(b.record(src))
        top, bottom = view.edge_stresses(result)
        rows = {r["key"]: r["value"] for r in result["rows"]}
        assert abs((bottom - top) / 2 - rows["sigma_m_y_d"]) < 1e-9
        for value in (top, bottom):
            assert ">%s<" % mc._fmt(round(value, 2)) in svg, value
        colours = set(re.findall(r"#[0-9a-fA-F]{3,6}\b", svg))
        assert colours <= {"#000"}, colours
        words = re.findall(r">([^<>]+)<", re.sub(r"<style>.*?</style>", "", svg))
        assert all(not re.search(r"[A-Za-zÀ-ÿ]{4,}", w) for w in words), words
        kn = view.DOMAINS["compression"]
        k = kn.read_source(here.checks_dir / "KN-01.json")
        chart = kn.chart(k)
        rows = {r["key"]: r["value"] for r in mc.compute(kn.record(k))["rows"]}
        assert [round(m["x"], 9) for m in chart["marks"]] == [round(rows["lambda_rel_y"], 9), round(rows["lambda_rel_z"], 9)]
        sh = view.DOMAINS["shear"]
        s = sh.new_source("SC-9")
        s.update(position="T001", variant="shear-perp", sigma_90=5.0)
        said = sh.messages(s)
        assert [m.code for m in said] == ["sigma_90_outside"] and said[0].severity == "info"
        s = dict(s, material="sia265-1:osb3", loading={"mode": "plaque", "direction": "par"}, variant="shear-off", F={"value": 5, "unit": "kN"}, l=200)
        s = sh.stamp_version(s)
        codes = [m.code for m in sh.messages(s) if m.severity == "error"]
        assert codes == ["thickness_out"] or codes == ["material_lacks"], codes
        text = sh.message_params({"material": "sia265:GL24h", "loading": "plaque-par", "kind": "compression"}, "fr")
        assert text["material"] == "GL24h" and text["loading"] == "en plaque ∥" and text["kind"] == "compression"


def test_the_module_imports_no_qt():
    tree = ast.parse((conftest.ROOT / "calc" / "domains" / "member_check_view.py").read_text(encoding="utf-8"))
    names = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    names |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert "PySide6" not in names
