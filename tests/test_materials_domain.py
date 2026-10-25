"""What a material's values give (calc/domains/materials_derive.py, materials_search.py, spec docs/requirements/active/2026-10-24-onglet-materiaux.md, REQ-008 to REQ-011, ARCH-001; issue #110).

What is held:

* **REQ-008** -- the design values: typed wins; f_v,d and f_t,90,d set by 3.3.2.2 / 3.4.2.2 (and equal to Tabellen 8 and 9's); f_k / (γ_M/η_M) otherwise -- C24 24 → 14.1, 21 → 12.4, GL24h 24 → 16.0 --; the limit of T36, f_c,90,k 2.5 → 1.5 and not Tabelle 8's 1.8; a panel η_mod · f_k / γ_M -- OSB/3 18 → 10.5, 10 → 5.8, 1.0 → 0.6 --; rounding half up;
* **REQ-009** -- the state: the prototype's member typed by f_m,k alone lacks 3 values and has 3 written in italics; C24 complete; two of the engineer's materials of one name in red; a panel without thickness said; MDF's «non disponibles» said apart;
* **REQ-010** -- «Disponible dans»: a weight for the permanent loads; a class of SIA 265 in the checks and the connectors; since issue #112 (REQ-012) a member of one's own complete and a panel giving a resistance in the member checks, a member of one's own «soon» in the connectors;
* **REQ-011** -- every word found, in three languages, without accents; the filters;
* **ARCH-001** -- the domain imports no Qt.
"""

TIER = "fast"  # tests/run_tests.py --fast

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import conftest
from domains import materials_catalogue as catalogue, materials_derive as derive, materials_search as search
from norms import sia265


def _member(values, family="softwood", **more):
    return dict({"id": "u-0000000a", "type": "member", "family": family, "values": values, "names": {"fr": "Mon bois"}, "category": "wood",
                 "source": {"kind": "url", "url": "https://example.org"}, "weight": {"value": 5, "unit": "kN/m³"}}, **more)


def test_a_design_value_typed_set_or_deduced():
    c24 = _member({"f_m_k": 24, "f_c_0_k": 21, "f_c_90_k": 2.5, "f_t_0_d": 9.9})
    assert derive.member_design(c24, "m") == derive.Design(14.1, "deduced", "general", {"k": 24, "gamma": 1.7})
    assert derive.member_design(c24, "c_0").value == 12.4
    assert derive.member_design(c24, "c_90").value == 1.5          # T36: the norm's rule, not Tabelle 8's 1.8
    assert derive.member_design(c24, "t_0") == derive.Design(9.9, "typed")
    assert derive.member_design(c24, "v") == derive.Design(1.5, "set", "set", {"clause": "3.3.2.2"})
    assert derive.member_design(c24, "t_90").value == 0.1
    assert derive.member_design(_member({}, "hardwood"), "v").value == 1.8 and derive.member_design(_member({}, "hardwood"), "t_90").value == 0.2
    assert derive.member_design(_member({}, "glulam"), "t_90") == derive.Design(0.15, "set", "set", {"clause": "3.4.2.2"})
    assert derive.member_design(_member({"f_m_k": 24}, "glulam"), "m").value == 16.0
    assert derive.member_design(_member({}), "m") is None


def test_the_set_values_are_tabelle_8_and_9s():
    for gid, grade in sia265.grades().items():
        family = "glulam" if grade["family"] == "Brettschichtholz" else ("hardwood" if grade["species"] == "Laubholz" else "softwood")
        for key in sia265.SET_DESIGN_VALUES:
            assert sia265.set_design_value(family, key)[0] == grade[key], (gid, key)


def test_a_panels_design_value_is_eta_mod_times_f_k_over_gamma_m():
    osb = catalogue.find("sia265-1:osb3")
    mine = {"id": "u-0000000b", "type": "panel", "product": "osb3", "isotropic": False, "columns": [], "rho_k": [550], "names": {"fr": "x"}, "category": "board",
            "grid": {"plate": {"f_m_k": {"par": [18.0], "perp": [None]}, "f_c_90_k": {"par": [10.0], "perp": [10.0]}, "f_v_k": {"par": [1.0], "perp": [1.0]}}}}
    assert derive.panel_design(mine, "plate", "f_m", "par", 0) == derive.Design(10.5, "deduced", "panel", {"k": 18.0, "gamma": 1.2, "eta": 0.7})
    assert derive.panel_design(mine, "plate", "f_c_90", "par", 0).value == 5.8
    assert derive.panel_design(mine, "plate", "f_v", "perp", 0).value == 0.6
    assert derive.panel_design(mine, "plate", "f_m", "perp", 0) is None
    assert derive.panel_design(osb, "plate", "f_m", "par", 2) == derive.Design(8.6, "typed")   # the norm's b table, read


def test_each_type_is_checked_and_a_member_carries_no_panel_grid():
    """REQ-004: a material of each type passes the contract; a member with a panel's grid, a panel with a member's values, an «other» with either is refused, naming the field."""
    from domains import materials_contract as contract, materials_user
    from norms import sia265_1
    products = set(sia265_1.products())
    for kind in contract.TYPES:
        m = materials_user.blank(kind)
        m["names"]["fr"] = "Essai " + kind
        if kind == "panel":
            m["product"] = "osb3"
        contract.check_material(m, "test", products)
    for kind, extra, said in (("member", {"grid": {}}, "no panel grid"), ("panel", {"family": "softwood"}, "no family"), ("other", {"values": {}}, "no family"), ("other", {"product": "osb3"}, "no panel grid")):
        m = dict(materials_user.blank(kind), **extra)
        m["names"] = {"fr": "x"}
        if kind == "panel":
            m["product"] = "osb3"
        try:
            contract.check_material(m, "test", products)
        except Exception as exc:
            assert said in str(exc), (kind, extra, exc)
        else:
            raise AssertionError((kind, extra))


def test_rounding_is_half_up():
    assert derive.round_tenth(12.35) == 12.4 and derive.round_tenth(0.05) == 0.1 and derive.round_tenth(5.833) == 5.8


def test_the_state_of_a_material():
    proto = _member({"f_m_k": 24, "E_0_mean": 11000, "E_90_mean": 370, "G_mean": 690, "rho_k": 350})
    states = {s.code: s for s in derive.status(proto)}
    assert states["missing"].params == {"n": 3} and states["missing"].level == "warn"     # f_t,0, f_c,0, f_c,90
    assert states["deduced"].params == {"n": 3} and states["deduced"].level == "info"     # f_m,d, f_v,d, f_t,90,d
    assert "ok" not in states
    assert [s.code for s in derive.status(catalogue.find("sia265:C24"))] == ["ok"]
    twin = dict(proto, id="u-0000000c")
    assert "same_name" in {s.code for s in derive.status(proto, [twin])}
    assert "same_name" not in {s.code for s in derive.status(catalogue.find("sia265:C24"), [dict(catalogue.find("sia265:C24"), id="u-1")])}
    bare = {"id": "u-0000000d", "type": "other", "names": {"fr": "Rien"}, "category": "ins", "source": {"kind": "none"}}
    assert {s.code for s in derive.status(bare)} == {"no_weight", "no_source"}
    assert {s.code for s in derive.status(dict(bare, example=True))} >= {"example"}
    panel = {"id": "u-0000000e", "type": "panel", "product": "osb3", "columns": [], "thickness": None, "rho_k": [None], "grid": {}, "names": {"fr": "p"}, "category": "board"}
    assert "no_thickness" in {s.code for s in derive.status(panel)}
    mdf = {s.code: s for s in derive.status(catalogue.find("sia265-1:mdf-la"))}
    assert mdf["not_given"].params == {"n": 16} and "missing" not in mdf


def test_where_a_material_is_offered():
    use = {u.tab: u for u in derive.available_in(catalogue.find("sia265:C24"))}
    assert (use["tab_ac_selfweight"].status, use["tab_mc"].status, use["tab_connections"].status) == ("yes", "yes", "yes")
    # issue #112, REQ-012: the member checks read a member of one's own complete in what they read, and a panel giving one of their resistances
    mine = {u.tab: u for u in derive.available_in(_member({"f_m_k": 24}))}
    assert mine["tab_mc"] == derive.Use("tab_mc", "no", "design") and mine["tab_connections"] == derive.Use("tab_connections", "soon", "rho")
    complete = {u.tab: u for u in derive.available_in(_member({"f_m_k": 24, "f_t_0_k": 14, "f_c_0_k": 21}))}
    assert complete["tab_mc"] == derive.Use("tab_mc", "yes")
    nothing = {u.tab: u for u in derive.available_in({"type": "other"})}
    assert nothing["tab_ac_selfweight"] == derive.Use("tab_ac_selfweight", "no", "weight") and "tab_mc" not in nothing
    osb3 = {u.tab: u for u in derive.available_in(catalogue.find("sia265-1:osb3"))}
    assert set(osb3) == {"tab_ac_selfweight", "tab_mc", "tab_plates", "tab_connections"} and osb3["tab_mc"] == derive.Use("tab_mc", "yes")


def test_every_word_is_found_in_three_languages():
    all_ = catalogue.catalogue()
    insulation = {m["id"] for m in all_ if m["category"] == "ins"}
    for word in ("isolation", "Dämmung", "insulation", "DAEMMUNG"):
        assert insulation <= {m["id"] for m in search.search(all_, word)}, word
    assert "sia265-1:osb3" in {m["id"] for m in search.search(all_, "panneau osb")}
    assert {m["id"] for m in search.search(all_, "panneau osb")} <= {m["id"] for m in all_ if "osb" in search.fold(" ".join(m["names"].values()))}
    assert search.search(all_, "beton") == search.search(all_, "béton")
    assert all(m["type"] == "panel" for m in search.search(all_, "", kind="panel"))
    assert search.search(all_, "", origin="user") == []
    mine = {"id": "u-1", "type": "other", "names": {"de": "Schaumglas"}, "category": "ins"}
    assert search.search(all_ + [mine], "schaumglas", origin="user") == [mine]
    assert list(search.by_category(all_))[0] == "wood"


def test_the_domain_imports_no_qt():
    code = ("import sys; sys.path.insert(0, %r); from domains import materials_user, materials_catalogue, materials_derive, materials_search, materials_contract; "
            "from norms import sia265_1; materials_catalogue.catalogue(); assert not [m for m in sys.modules if m.startswith('PySide6')]") % str(conftest.CALC)
    subprocess.run([sys.executable, "-c", code], check=True, env=dict(__import__("os").environ, WOODCORE_SETTINGS=str(conftest.SETTINGS)))
