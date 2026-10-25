"""The member checks in Woodcore's window (spec docs/requirements/completed/2026-10-24-verifications-elements-v3.md, issue #112; calc/tools/check_tabs.py, check_member.py, check_results.py, check_display.py, material_menu.py; docs/ui/tab-member-checks.md).

What is held:

* **UI-001** -- the group «Sécurité structurale»: Traction, Compression, Flexion, Cisaillement, Torsion, Résistance au feu, in the report alone; «Flambage» and «Déversement» no tabs of their own; the placeholders saying they are to come in three languages;
* **UI-002** -- each of the four a class of parameters on the type «Calcul», its services the type's with the head «Élément», the check's «Résultats» and «Affichage»;
* **UI-003** -- each tab lists its own kinds (the compression its bucklings, the bending its lateral torsional bucklings), an id unique across them, a new check saved, exported and listed, «Supprimer» archiving, a project opened read-only writing nothing, the draft through a rebuild;
* **UI-004 / UI-005 / UI-006 / UI-015** -- the material following the position grey, written over orange and taken back; its menu searched by «OSB» and «panneau», its groups in order, OSB/3's values by loading in «Flexion», a material without resistance greyed; the row «Sollicitation» (OSB/3's bubbles as validated, C24's one bubble ticked and closed); the line «La vérification lit»; the factors of a member and of a panel;
* **UI-007** -- the state: T39's refusal of OSB/3 in compression across the grain, no message of the stability;
* **UI-010** -- «Cisaillement» in three figures, SC-01 76.0 %, a shear-off and a shear across the grain computed by their figure, no list;
* **UI-011** -- the verdict first, the rows in the order of the calculation, η last, the governing row framed;
* **UI-013** -- «Affichage»'s command `#include domain-file("check", id)`, an option written into the check's source;
* **REQ-011** -- the box «vérifier la stabilité» turning DR-02 into a buckling saved in `Timber-checks/Buckling/`.

⚠️ Built off-screen on a copy of the example project, message boxes stubbed; nothing here compiles Typst.
"""

import contextlib
import json
import os
import sys

import conftest
from conftest import ROOT, Skip

import project

TOOLS = ROOT / "calc" / "tools"
_STATE = {}


def _qt():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _window():
    """One window on one copy of the example project, the report in front, the checks exported."""
    if "window" not in _STATE:
        _qt()
        here = conftest.project_copy("member_check_tab")
        with project.using(here):
            from domains import member_check
            member_check.export(here)
            import woodcore_gui
            window = woodcore_gui.MainWindow()
            window.mode = "rs"
            window.apply_mode()
        _STATE.update(window=window, here=here)
    return _STATE["window"], _STATE["here"]


def _tab(window, name):
    import check_tabs
    cls = {"tension": check_tabs.TensionTab, "compression": check_tabs.CompressionTab, "bending": check_tabs.BendingTab, "shear": check_tabs.ShearTab}[name]
    return next(t for t in window.tabs if isinstance(t, cls))


@contextlib.contextmanager
def _boxes():
    from PySide6.QtWidgets import QMessageBox
    shown = []

    def ask(_parent, _title, text, *args, **kwargs):
        shown.append(text)
        return QMessageBox.StandardButton.Yes

    saved = {name: QMessageBox.__dict__[name] for name in ("question", "warning", "information")}
    QMessageBox.question = staticmethod(ask)
    QMessageBox.warning = staticmethod(ask)
    QMessageBox.information = staticmethod(ask)
    try:
        with conftest.notices_said(lambda notice: shown.append(notice.text)):
            yield shown
    finally:
        for name, original in saved.items():
            setattr(QMessageBox, name, original)


def _fresh(tab):
    """A tab of the base of before (MemberCheckTab: the fire's, the steel's) on a new draft, nothing unsaved, no page asked for -- read by tests/test_fire_check_tab.py."""
    tab.dirty = False
    tab.new()
    tab.dirty = False
    tab.live = False


def _select(combo, data):
    index = combo.findData(data)
    assert index >= 0, (data, [combo.itemData(i) for i in range(combo.count())])
    combo.setCurrentIndex(index)


def _open(tab, cid):
    tab.dirty = False
    tab.load(cid)
    return tab


def _field(tab, key):
    return tab.service("form").fields[key]


def _results(tab):
    return tab.service("modules").pane.modules["results"].body


# --- UI-001, UI-002 the tabs ------------------------------------------------------------------

def test_the_group_holds_four_tabs_of_calculation_in_the_report_alone():
    _qt()
    import woodcore_gui
    groups = dict(woodcore_gui.NAV_GROUPS)
    assert groups["nav_safety"] == ("tab_mc_tension", "tab_mc_compression", "tab_mc_bending", "tab_mc_shear", "tab_mc_torsion", "tab_mc_fire")
    assert groups["nav_service"] == ("tab_sls_deformation", "tab_sls_vibration")
    for key in groups["nav_safety"] + groups["nav_service"]:
        assert key in woodcore_gui.mode_tabs("rs") and key not in woodcore_gui.mode_tabs("cu") and key not in woodcore_gui.mode_tabs("bp"), key
    words = {lang: [woodcore_gui.STRINGS[lang][k] for k in ("tab_mc_tension", "tab_mc_compression", "tab_mc_bending", "tab_mc_shear")] for lang in ("fr", "de", "en")}
    assert words["fr"] == ["Traction", "Compression", "Flexion", "Cisaillement"]
    assert words["de"][3] == "Schub" and words["en"][3] == "Shear"
    assert "tab_mc_buckling" not in woodcore_gui.STRINGS["fr"] and "tab_mc_ltb" not in woodcore_gui.STRINGS["fr"], "the tabs folded into their accordion leave no word"
    import variable_calc
    assert variable_calc.CHECK_TABS["check"]["buckling"] == "tab_mc_compression" and variable_calc.CHECK_TABS["check"]["lateral-torsional"] == "tab_mc_bending"


def test_the_placeholders_say_they_are_to_come_in_three_languages():
    window, _here = _window()
    import member_check_tab
    import reserved_tab
    soon = [t for t in window.tabs if isinstance(t, reserved_tab.ReservedTab) and t.key in member_check_tab.SOON]
    assert {t.key for t in soon} == set(member_check_tab.SOON)
    for lang in ("fr", "de", "en"):
        assert all(member_check_tab.STRINGS[lang].get(key) for key, _c in member_check_tab.SOON.values())


def test_each_tab_is_a_class_of_parameters_on_the_type():
    _qt()
    import calc_tab
    import check_tabs
    import tab_host
    for cls in (check_tabs.TensionTab, check_tabs.CompressionTab, check_tabs.BendingTab, check_tabs.ShearTab):
        assert issubclass(cls, calc_tab.CalcTab)
        assert set(k for k in vars(cls) if not k.startswith("__") and k != "staticMetaObject") <= set(tab_host.PARAMS), cls
        names = [s.__name__ for s in cls.SERVICES]
        assert names.index("CheckMember") < names.index("DeclaredForm") and "CheckResults" in names and "CheckDisplay" in names and "DomainDisplay" not in names


# --- UI-003 the list -------------------------------------------------------------------------

def test_each_tab_lists_its_own_kinds_and_an_id_is_unique_across_them():
    window, here = _window()
    with project.using(here):
        assert set(_tab(window, "tension").ids) == {"ZT-01", "ZT-02"}
        assert set(_tab(window, "compression").ids) == {"DR-01", "DR-02", "KN-01"}, "the bucklings in the compression tab (REQ-011)"
        assert set(_tab(window, "bending").ids) == {"BI-01", "BI-02", "BI-03", "KI-01", "KI-02"}
        assert set(_tab(window, "shear").ids) == {"SC-01"}
        tension = _tab(window, "tension")
        tension.dirty = False
        tension.new()
        tension.id_edit.setText("dr-01")
        with _boxes():
            assert tension.save() is False, "an id another tab's check holds, ignoring case"
        tension.dirty = False


def test_a_new_check_is_saved_exported_listed_and_archived():
    window, here = _window()
    import source_archive
    with project.using(here):
        tab = _tab(window, "tension")
        tab.dirty = False
        tab.new()
        tab.id_edit.setText("Z_new")
        _field(tab, "N").spin.setValue(40.0)
        member = tab.service("member")
        member.section_type.setCurrentIndex(member.section_type.findData("rec"))
        factors = tab.service("factors")
        factors.moisture.setCurrentIndex(factors.moisture.findData(1))
        with _boxes():
            assert tab.save() is True
        src = json.loads((here.checks_dir / "Z_new.json").read_text(encoding="utf-8"))
        assert src["kind"] == "tension" and src["N"] == {"value": 40.0, "unit": "kN"} and src["schema_version"] == "1.0" and "stability" not in src
        assert "Z_new" in tab.ids and json.loads((here.data_dir / "checks.json").read_text(encoding="utf-8"))["checks"]["Z_new"]["calculable"] is False, "no material: not calculable, said"
        with _boxes():
            tab.delete()
        assert not (here.checks_dir / "Z_new.json").exists() and "Z_new" not in tab.ids
        assert any(source_archive.folder(here.checks_dir).glob("*.json"))
        tab.dirty = False


def test_a_project_opened_read_only_writes_nothing():
    window, here = _window()
    with project.using(here):
        tab = _open(_tab(window, "tension"), "ZT-02")
        before = (here.checks_dir / "ZT-02.json").read_bytes()
        window.read_only = True
        refused = []
        window.refuse_read_only = lambda *a, **k: refused.append(True)
        try:
            _field(tab, "N").spin.setValue(77.0)
            assert tab.save() is False
        finally:
            window.read_only = False
        assert refused and (here.checks_dir / "ZT-02.json").read_bytes() == before
        _open(tab, "ZT-02")


def test_the_draft_travels_through_a_rebuild():
    window, here = _window()
    import check_tabs
    with project.using(here):
        tab = _open(_tab(window, "compression"), "DR-02")
        _field(tab, "N").spin.setValue(33.0)
        state = tab.view_state()
        assert state["dirty"] and state["draft"]["N"]["value"] == 33.0 and state["current_id"] == "DR-02"
        window.views["tab_mc_compression"] = state
        other = check_tabs.CompressionTab(window)
        try:
            assert other.dirty and other.current_id == "DR-02" and _field(other, "N").spin.value() == 33.0
        finally:
            window.views.pop("tab_mc_compression", None)
            other.dirty = False
            other.deleteLater()
        _open(tab, "DR-02")


# --- UI-004 to UI-006, UI-015 the head «Élément» ------------------------------------------------------

def test_the_material_follows_its_position_grey_written_over_orange_and_taken_back():
    window, here = _window()
    with project.using(here):
        tab = _open(_tab(window, "compression"), "DR-01")
        member = tab.service("member")
        assert member.material_button.text() == "C24 — T001" and not member.material_back.isVisibleTo(member.box)
        member.material_button.setChecked(True)
        assert member.menu.isVisibleTo(member.box)
        assert member.menu.choose("sia265:GL24h")
        assert member.material_button.text() == "GL24h" and member.material_back.isVisibleTo(member.box)
        assert tab.draft()["material"] == "sia265:GL24h" and tab.draft()["schema_version"] == "1.3"
        said = [tab.ctx.message_text(m) for m in tab.ctx.messages]
        assert any("GL24h" in s and "T001" in s and "C24" in s for s in said), said
        member.material_back.click()
        assert "material" not in tab.draft() and tab.draft()["schema_version"] == "1.0"
        _open(tab, "DR-01")


def test_the_menu_searches_the_library_in_its_groups():
    window, here = _window()
    with project.using(here):
        tab = _open(_tab(window, "bending"), "BI-01")
        member = tab.service("member")
        member.material_button.setChecked(True)
        items = member.menu.items()
        titles = [text for text, mid, _on in items if mid is None]
        assert titles[:3] == [tab.t("vc_group_solid"), tab.t("vc_group_glulam"), tab.t("vc_group_panel")] and titles[-1] == tab.t("vc_group_other")
        assert items[0][0].startswith("C24") and "T001" in items[0][0], "the position's material first"
        osb = next(text for text, mid, _on in items if mid == "sia265-1:osb3")
        said = " · ".join("%s %s" % (tab.t("vc_abbr_" + l), v) for l, v in (("plaque_par", "10.5"), ("plaque_perp", "5.3"), ("voile_par", "5.8"), ("voile_perp", "4.2")))
        assert said in osb or said.replace(".", ",") in osb, osb
        assert any(mid and str(mid).startswith("sia261:") and not on for _t, mid, on in items), "a material without resistance greyed"
        member.menu.search.setText("OSB")
        assert {mid for _t, mid, on in member.menu.items() if on and mid not in (None, "__head__")} >= {"sia265-1:osb3"}
        for word in ("panneau", "Platte", "panel"):
            member.menu.search.setText(word)
            assert any(str(mid).startswith("sia265-1:") for _t, mid, on in member.menu.items() if on), word
        member.menu.search.setText("")
        member.material_button.setChecked(False)
        _open(tab, "BI-01")


def test_osb3_s_loading_bubbles_and_what_the_check_reads():
    window, here = _window()
    with project.using(here):
        tab = _open(_tab(window, "bending"), "BI-01")
        member, load, factors = tab.service("member"), tab.service("load"), tab.service("factors")
        assert type(load).__module__ == "load_row" and type(factors).__module__ == "factors_row", "the rows «Sollicitation» and «Facteurs» are services of their own"
        member.section_type.setCurrentIndex(member.section_type.findData("rec"))
        member.spins["b"].setValue(1000.0)
        member.spins["h"].setValue(18.0)
        factors.moisture.setCurrentIndex(factors.moisture.findData(1))
        member.material_button.setChecked(True)
        member.menu.choose("sia265-1:osb3")
        factors.moisture.setCurrentIndex(factors.moisture.findData(1))
        texts = [b.text() for b in load.loading_buttons.values()]
        assert [t.rsplit(" ", 1)[0] for t in texts] == [tab.t("vc_load_plaque_par"), tab.t("vc_load_plaque_perp"), tab.t("vc_load_voile_par"), tab.t("vc_load_voile_perp")]
        assert [t.rsplit(" ", 1)[1].replace(",", ".") for t in texts] == ["9.6", "4.8", "5.5", "4.1"]
        draft = tab.draft()
        assert draft["loading"] == {"mode": "plaque", "direction": "par"} and draft["impact"] is False
        assert "alpha" not in tab.MODULE.visible_fields(draft), "a panel's direction replaces the angle"
        reads = load.reads.text()
        assert "9" in reads and "SIA 265/1" in reads and "Tableau 19b" in reads and "18" in reads, reads
        # the material's table, pinnable (UI-012): Tableaux 19a et 19b
        assert load.mark.isVisibleTo(load.box) and load.excerpt == ("sia265-1-2018-materials-excerpts", ("tab19",))
        module = tab.service("modules").pin(*load.excerpt)
        assert "Tableaux 19a et 19b" in module.spec.title and tab.ctx.is_pinned(*load.excerpt), module.spec.title
        tab.ctx.unpin_excerpts(*load.excerpt)
        # the factors of a panel: its classes, five KLED and the situation
        assert [factors.moisture.itemData(i) for i in range(factors.moisture.count())][1:] == [1, 2]
        assert factors.kled.count() == 5 and factors.kled.isVisibleTo(factors.box) and not factors.action.isVisibleTo(factors.box)
        factors.kled.setCurrentIndex(factors.kled.findData("short"))
        assert tab.draft()["kled"] == "short"
        factors.situation.setCurrentIndex(1)
        assert tab.draft()["accidental"] is True
        tab.dirty = False
        _open(tab, "BI-01")
        # C24: one bubble, ticked and closed; the factors of a member
        bubble = list(load.loading_buttons.values())[0]
        assert len(load.loading_buttons) == 1 and bubble.isChecked() and not bubble.isEnabled() and "14" in bubble.text()
        assert [factors.moisture.itemData(i) for i in range(factors.moisture.count())] == [None, 1, 2, 3] and factors.action.count() == 2
        assert "1,7" in factors.gamma.text() or "1.7" in factors.gamma.text()


# --- UI-007 the state -----------------------------------------------------------------------

def test_a_panel_in_compression_across_the_grain_says_why_and_no_stability_is_asked():
    window, here = _window()
    with project.using(here):
        tab = _open(_tab(window, "compression"), "DR-01")
        assert not any("stabil" in tab.ctx.message_text(m).lower() for m in tab.ctx.messages)
        member = tab.service("member")
        member.material_button.setChecked(True)
        member.menu.choose("sia265-1:osb3")
        errors = [m for m in tab.ctx.messages if m.severity == "error"]
        assert errors and errors[0].code in ("material_lacks", "thickness_out"), errors
        member.section_type.setCurrentIndex(member.section_type.findData("rec"))
        member.spins["b"].setValue(18.0)
        member.spins["h"].setValue(200.0)
        errors = [m for m in tab.ctx.messages if m.severity == "error"]
        text = tab.ctx.message_text(errors[0])
        assert errors[0].code == "material_lacks" and "compression" in text and "f_c,90,d" in text and tab.ctx.instance is None, text
        tab.dirty = False
        _open(tab, "DR-01")


def test_the_list_groups_by_position_colours_the_rates_and_sorts_by_rate():
    """UI-003: DR-01 under its position, its rate green; sorted by rate, one list the highest first; a check that cannot be calculated has no rate and says why."""
    window, here = _window()
    import theme
    from domains import member_check as mc
    with project.using(here):
        tab = _open(_tab(window, "compression"), "DR-01")
        cases = tab.service("cases")
        assert type(cases).__name__ == "CheckList" and cases.sort == "position"
        # what the rows say, read at once: the items go with the next rebuild of the list
        said = {cid: (item.text(0), item.parent().text(0) if item.parent() is not None else None, item.foreground(0).color().name().lower(), item.toolTip(0))
                for item, cid in cases.list.rows()}
        assert (said["DR-01"][1] or "").startswith("T001"), "DR-01 under its position"
        assert said["DR-02"][1] == tab.t("vc_list_no_position")
        data = json.loads((here.data_dir / "checks.json").read_text(encoding="utf-8"))
        eta = mc.utilisations(data)["DR-01"]["eta"]
        text = said["DR-01"][0]
        assert ("%.1f" % (eta * 100)).replace(".", ",") in text or ("%.1f" % (eta * 100)) in text, text
        assert said["DR-01"][2] == theme.colour("ok" if eta <= 1 else "danger").lower()
        cases.sort_buttons["rate"].click()
        rates = mc.utilisations(data)
        listed = [cid for cid, _text, _group in cases.listed()]
        assert listed == sorted(listed, key=lambda c: (c not in rates, -(rates.get(c, {}).get("eta") or 0), c)) and all(g == "" for _c, _t, g in cases.listed())
        cases.rows["DR-02"] = dict(cases.rows["DR-02"], eta=None, ok=None, reason="no material")
        cases._paint()
        assert "no material" in next(i.toolTip(0) for i, cid in cases.list.rows() if cid == "DR-02")
        cases.set_sort("position")
        _open(tab, "DR-01")


def test_the_five_cards_of_f_c_90_d_show_the_table_and_d30_s_bracketed_values_greyed():
    """UI-008: the support's five cards, each its value of SIA 265 Tabelle 8 for the draft's class; D30's bracketed cards greyed, saying why; a card clicked is the draft's `case` and `larger`."""
    window, here = _window()
    with project.using(here):
        tab = _open(_tab(window, "compression"), "DR-02")
        _field(tab, "alpha").spin.setValue(90.0)
        cards = _field(tab, "support").buttons
        assert list(cards) == ["generell", "mit_vorholz", "mit_vorholz-larger", "endauflagerung", "endauflagerung-larger"]
        assert all(b.isEnabled() and "\n" in b.text() and "N/mm²" in b.text() for b in cards.values()), [b.text() for b in cards.values()]
        cards["endauflagerung-larger"].click()
        draft = tab.draft()
        assert (draft["case"], draft["larger"]) == ("endauflagerung", True)
        member = tab.service("member")
        member.material_button.setChecked(True)
        member.menu.choose("sia265:D30")
        assert not cards["mit_vorholz-larger"].isEnabled() and "D30" in cards["mit_vorholz-larger"].toolTip() and cards["mit_vorholz-larger"].text().endswith("—")
        assert cards["mit_vorholz"].isEnabled() and cards["generell"].isEnabled()
        tab.dirty = False
        _open(tab, "DR-02")


# --- UI-010, UI-011 the shear and the results -------------------------------------------------------

def test_the_shear_is_three_figures_and_the_results_are_in_the_order_of_the_calculation():
    window, here = _window()
    with project.using(here):
        tab = _open(_tab(window, "shear"), "SC-01")
        from PySide6.QtWidgets import QComboBox
        assert not [c for c in tab.service("form").fields["variant"].widget.findChildren(QComboBox)], "no list"
        figures = _field(tab, "variant").buttons
        assert list(figures) == ["shear", "shear-off", "shear-perp"] and figures["shear-off"].text() == tab.t("vc_t_shear_off")
        body = _results(tab)
        assert "76,0" in body.verdict.text() or "76.0" in body.verdict.text()
        assert body.order()[-1] == "eta"
        figures["shear-perp"].click()
        _field(tab, "sigma_90").spin.setValue(-1.0)
        assert tab.ctx.instance is not None and tab.ctx.instance["record"].get("variant") == "shear-perp"
        figures["shear-off"].click()
        _field(tab, "F").spin.setValue(25.0)
        _field(tab, "l").spin.setValue(200.0)
        assert tab.ctx.instance is not None and tab.ctx.instance["result"]["equation"] == "(26)"
        tab.dirty = False
        _open(tab, "SC-01")
        kn = _open(_tab(window, "compression"), "KN-01")
        body = _results(kn)
        assert body.order()[-1] == "eta" and len(body.framed()) == 1, body.framed()


# --- REQ-011 the stability, UI-013 «Affichage» -------------------------------------------------------

def test_the_stability_box_turns_a_compression_into_a_buckling_and_moves_its_file():
    window, here = _window()
    from domains import unfold
    with project.using(here):
        tab = _open(_tab(window, "compression"), "DR-02")
        assert "l_y" not in tab.MODULE.visible_fields(tab.draft())
        _field(tab, "stability").check.setChecked(True)
        assert tab.draft()["kind"] == "buckling" and "l_y" in tab.MODULE.visible_fields(tab.draft())
        assert tab.ctx.instance is not None and tab.ctx.instance["result"]["kind"] == "buckling"
        with _boxes():
            assert tab.save() is True
        assert json.loads((here.checks_dir / "DR-02.json").read_text(encoding="utf-8"))["kind"] == "buckling"
        assert (here.domain_dir("check", "buckling") / "DR-02.typ").is_file() and not (here.domain_dir("check", "compression") / "DR-02.typ").exists()
        assert "DR-02" in tab.ids
        _field(tab, "stability").check.setChecked(False)
        with _boxes():
            assert tab.save() is True
        assert (here.domain_dir("check", "compression") / "DR-02.typ").is_file()
        assert unfold.domain_path(here, "DR-02", kind="check").parent.name == "Compression"


def test_affichage_copies_the_include_and_keeps_its_options_in_the_source():
    window, here = _window()
    with project.using(here):
        tab = _open(_tab(window, "bending"), "BI-02")
        display = tab.service("display")
        assert display.entries()[0].call == '#include domain-file("check", "BI-02")', display.entries()[0].call
        with _boxes():
            assert display.write_check_display("verdict", "ratio")
        assert json.loads((here.checks_dir / "BI-02.json").read_text(encoding="utf-8"))["display"] == {"verdict": "ratio"}
        with _boxes():
            display.write_domain_level(2)
            display.write_check_display("verdict", "percent")
        src = json.loads((here.checks_dir / "BI-02.json").read_text(encoding="utf-8"))
        assert src["display"] == {"level": 2} and src["schema_version"] == "1.3"
        text = (here.domain_dir("check", "bending") / "BI-02.typ").read_text(encoding="utf-8")
        assert "level: 2)[" in text
        with _boxes():
            display.write_domain_level(None)
        assert "display" not in json.loads((here.checks_dir / "BI-02.json").read_text(encoding="utf-8"))


def test_the_verdict_is_red_above_100_percent_and_a_thickness_out_of_the_ranges_is_said_in_red():
    window, here = _window()
    import theme
    with project.using(here):
        tab = _open(_tab(window, "tension"), "ZT-01")
        body = _results(tab)
        assert theme.colour("ok") in body.verdict.text()
        _field(tab, "N").spin.setValue(500.0)
        assert theme.colour("danger") in body.verdict.text() and "✘" in body.verdict.text()
        tab.dirty = False
        bending = _open(_tab(window, "bending"), "BI-01")
        member = bending.service("member")
        member.section_type.setCurrentIndex(member.section_type.findData("rec"))
        member.spins["b"].setValue(1000.0)
        member.spins["h"].setValue(5.0)
        member.material_button.setChecked(True)
        member.menu.choose("sia265-1:osb3")
        errors = [m for m in bending.ctx.messages if m.severity == "error"]
        assert errors and errors[0].code == "thickness_out", errors
        said = bending.ctx.message_text(errors[0])
        assert "6–10 mm, 10–18 mm, 18–25 mm" in said and "5" in said
        reads = bending.service("load").reads.text()
        assert theme.colour("danger") in reads and "6–10 mm" in reads
        bending.dirty = False
        _open(bending, "BI-01")


def test_t39_is_said_in_three_languages():
    window, _here = _window()
    import member_check_tab_words
    from domains import member_check_view
    params = {"material": "OSB/3", "loading": "plaque-par", "kind": "compression", "missing": "f_c,90,d"}
    for lang, start in (("fr", "OSB/3 en plaque ∥ ne donne pas toutes les résistances de cette vérification (compression)"),
                        ("de", "OSB/3 Plattenbeanspruchung ∥ liefert nicht alle Festigkeiten"), ("en", "OSB/3 as a plate ∥ does not give every resistance")):
        words = member_check_view.DOMAINS["compression"].message_params(params, lang)
        text = member_check_tab_words.STRINGS[lang]["vc_msg_material_lacks"].format(**words)
        assert text.startswith(start) and "f_c,90,d" in text, (lang, text)
