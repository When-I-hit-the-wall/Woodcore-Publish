"""The member checks in Woodcore's window: the two navigation groups «Sécurité structurale» and «Aptitude au service», their nine modules, and the two that are built, «Traction» and «Compression» (calc/tools/member_check_tab.py; docs/domain/member-checks.md §3.3undecies, docs/ui/window.md §10quater).

What is held: the groups and their nine rows in the report and in no other document; each placeholder saying it is to come, in three languages, and naming what it will hold and the command that does the work meanwhile -- «Flexion» bending combined with a normal force, «Effort tranchant» the shear and the compression perpendicular to the grain --; the tension tab's three panes and cards; a check made, saved (its file written, the checks exported) and renamed (asked first); an ID taken refused, ignoring case; a value that follows its position saying so in its own field, written over in orange with «Reprendre» taking it back; the options of the command changing the call; the call saying it needs the check saved; the page asked for from the DRAFT, its values written into the call, nothing saved first; «Supprimer» archiving; a project opened read-only refusing; and the words in three languages.

«Compression» shares the tension tab's base: each tab lists the checks of its own kind and an ID is unique across both; its card «Appui» appears with an angle above 0, offers the five resistances f_c,90,d (the two bracketed ones closed for a grade with no bracketed value), and its contact width follows the section's.

⚠️ Built off-screen on a copy of the example project (conftest.project_copy), message boxes stubbed -- a modal off-screen never comes back -- and the page's pane replaced by a recorder: nothing here compiles Typst.
"""

import contextlib
import json
import os
import sys

import conftest
from conftest import ROOT, Skip

import project
from domains import unfold

TOOLS = ROOT / "calc" / "tools"
_STATE = {}


def _qt():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _window():
    """One window on one copy of the example project, for the whole file, the report in front (a window opens on the convention d'utilisation, which has none of these modules)."""
    if "window" not in _STATE:
        _qt()
        here = conftest.project_copy("member_check_tab")
        with project.using(here):
            import woodcore_gui
            window = woodcore_gui.MainWindow()
            window.mode = "rs"
            window.apply_mode()
        _STATE.update(window=window, here=here)
    return _STATE["window"], _STATE["here"]


def _tab(window):
    import member_check_tab
    return next(t for t in window.tabs if isinstance(t, member_check_tab.TensionTab))


def _ctab(window):
    import member_check_tab
    return next(t for t in window.tabs if isinstance(t, member_check_tab.CompressionTab))


@contextlib.contextmanager
def _boxes(question=None):
    """The message boxes answered without a window: `question(text)` gives the button, Yes where none is given; every text said is kept."""
    from PySide6.QtWidgets import QMessageBox
    shown = []

    def ask(_parent, _title, text, *args, **kwargs):
        shown.append(text)
        return question(text) if question else QMessageBox.StandardButton.Yes

    def warn(_parent, _title, text, *args, **kwargs):
        shown.append(text)
        return QMessageBox.StandardButton.Ok

    saved = {name: QMessageBox.__dict__[name] for name in ("question", "warning", "information")}
    QMessageBox.question = staticmethod(ask)
    QMessageBox.warning = staticmethod(warn)
    QMessageBox.information = staticmethod(warn)
    try:
        with conftest.notices_said(lambda notice: shown.append(notice.text)):   # what was a box is a notice since v0.117
            yield shown
    finally:
        for name, original in saved.items():
            setattr(QMessageBox, name, original)


def _fresh(tab):
    """The tab on a new draft, nothing unsaved, no page asked for."""
    tab.dirty = False
    tab.new()
    tab.dirty = False
    tab.live = False


def _select(combo, data):
    index = combo.findData(data)
    assert index >= 0, (data, [combo.itemData(i) for i in range(combo.count())])
    combo.setCurrentIndex(index)


def test_two_groups_and_nine_modules_in_the_report_alone():
    _qt()
    import woodcore_gui
    groups = dict(woodcore_gui.NAV_GROUPS)
    safety = ("tab_mc_tension", "tab_mc_compression", "tab_mc_bending", "tab_mc_shear", "tab_mc_torsion", "tab_mc_buckling", "tab_mc_ltb", "tab_mc_fire")   # issue #46: «Résistance au feu» last
    service = ("tab_sls_deformation", "tab_sls_vibration")
    assert groups["nav_safety"] == safety and groups["nav_service"] == service
    titles = [title for title, _members in woodcore_gui.NAV_GROUPS]
    # after the connections' group and before the reference, in that order
    assert titles.index("nav_connections") + 1 == titles.index("nav_safety") and titles.index("nav_safety") + 1 == titles.index("nav_service")
    # «Acier» (issues #50-#52) stands between the serviceability and the reference
    assert titles.index("nav_service") + 1 == titles.index("nav_steel") and titles.index("nav_steel") + 1 == titles.index("nav_reference"), titles
    for key in safety + service:
        assert key in woodcore_gui.mode_tabs("rs"), key
        assert key not in woodcore_gui.mode_tabs("cu") and key not in woodcore_gui.mode_tabs("bp"), key
    import chrome
    assert set(safety + service) <= set(chrome.ICONS), "a module without its icon"
    for lang in ("fr", "de", "en"):
        table = woodcore_gui.STRINGS[lang]
        words = [table[key] for key in safety + service + ("nav_safety", "nav_service")]
        assert all(words) and len(set(words)) == len(words), (lang, words)
    fr = woodcore_gui.STRINGS["fr"]
    assert (fr["nav_safety"], fr["nav_service"]) == ("Sécurité structurale", "Aptitude au service")
    assert [fr[k] for k in safety] == ["Traction", "Compression", "Flexion", "Effort tranchant", "Torsion", "Flambage", "Déversement", "Résistance au feu"]
    assert [fr[k] for k in service] == ["Déformations", "Vibrations"]


def test_the_navigation_shows_the_nine_rows_in_the_report():
    window, here = _window()
    import woodcore_gui
    with project.using(here):
        shown = woodcore_gui.mode_tabs(window.current_document())
    keys = [key for key, _factory in woodcore_gui.TABS]
    rows = [keys[index] for index in window.nav.order()]
    for key in ("tab_mc_tension", "tab_sls_vibration"):
        assert key in shown and key in rows, key
    assert rows.index("tab_mc_tension") < rows.index("tab_mc_ltb") < rows.index("tab_sls_deformation") < rows.index("tab_sls_vibration")
    assert keys.index("tab_mc_tension") == keys.index("tab_polar") + 1, "the group stands after the connections"


def test_the_placeholders_say_they_are_to_come_in_three_languages():
    window, here = _window()
    import member_check_tab
    import reserved_tab
    soon = [t for t in window.tabs if isinstance(t, reserved_tab.ReservedTab) and t.key in member_check_tab.SOON]
    assert len(soon) == 3, len(soon)      # Compression and Flexion are built since v0.117, Effort tranchant, Flambage and Déversement since issue #38
    assert not {"tab_mc_bending", "tab_mc_shear", "tab_mc_buckling", "tab_mc_ltb"} & set(member_check_tab.SOON)
    for tab in soon:
        assert tab.message.text() and tab.title.text() and tab.status.text()
    fr, de, en = (member_check_tab.STRINGS[lang] for lang in ("fr", "de", "en"))
    for key, (what, commands) in member_check_tab.SOON.items():
        for table, needle in ((fr, "à venir"), (de, "folgt"), (en, "is coming")):
            template = table["mc_soon" if commands else "mc_soon_none"]
            assert needle in template, (key, template)
            text = template.format(what=table[what], commands=", ".join(commands))
            assert table[what] in text and all(c in text for c in commands), text
    for what in ("mc_what_bending", "mc_what_shear", "mc_what_buckling", "mc_what_ltb"):
        assert all(what not in table for table in (fr, de, en)), "the placeholder's words went with it: " + what
    # «Effort tranchant» computes the shear-off and the shear across the grain since the spec 2026-10-21-commandes-typst-refonte (REQ-021); torsion is no check of Woodcore's, written in the report by hand since #verify-shear was retired (lot 19)
    for table in (fr, de, en):
        assert "#verify" in table["mc_shear_hint"] and "#verify-shear" not in table["mc_shear_hint"]
    # the two serviceability modules say that no command computes them yet
    assert not member_check_tab.SOON["tab_sls_deformation"][1] and not member_check_tab.SOON["tab_sls_vibration"][1]


def _tab_of(window, key):
    return next(t for t in window.tabs if getattr(t, "KEY", None) == key)


def test_the_buckling_lateral_and_shear_tabs_compute_at_once_what_the_export_holds():
    """UI-006 (issue #38): «Flambage», «Déversement» and «Effort tranchant» are member-check tabs -- each lists its own kind, loads the example's check, shows the instant result (η the export's record gives) and saves a new check that the export then carries calculable; the buckling lengths are one card for the two stability checks, shown in «Déversement» only with a compression (D-09)."""
    window, here = _window()
    with project.using(here):
        import member_check_tab
        from domains import member_check
        for key, cls, cid in (("tab_mc_buckling", member_check_tab.BucklingTab, "KN-01"), ("tab_mc_ltb", member_check_tab.LateralTab, "KI-02"),
                              ("tab_mc_shear", member_check_tab.ShearTab, "SC-01")):
            tab = _tab_of(window, key)
            assert isinstance(tab, cls) and cid in tab.ids, (key, tab.ids)
            assert all(i[:3] == cid[:3] for i in tab.ids), (key, tab.ids)
            tab.dirty = False
            tab.load(cid)
            assert tab.record and tab.record["calculable"], (key, tab.reason)
            exported = json.loads((here.data_dir / member_check.EXPORT_FILE).read_text(encoding="utf-8"))["checks"][cid]
            assert abs(member_check.compute(tab.record)["eta"] - member_check.compute(exported)["eta"]) < 1e-12
            assert "⩽" in tab.verdict_label.text() or "✔" in tab.verdict_label.text() or tab.results_label.text()
            assert not tab.effort_form.isRowVisible(tab.row_of(tab.alpha_spin)), "along the grain: no angle"
        lateral = _tab_of(window, "tab_mc_ltb")
        assert isinstance(lateral, member_check_tab.BucklingLengths) and isinstance(_tab_of(window, "tab_mc_buckling"), member_check_tab.BucklingLengths)
        lateral.load("KI-02")
        assert not lateral.lengths_card.isHidden(), "a compression shows the buckling lengths"
        lateral.n_spin.setValue(5.0)
        assert lateral.lengths_card.isHidden() and lateral.draft()["l_y"] == 4000, "a tension hides them and keeps them"
        _select(lateral.by_box, "crit")
        draft = lateral.draft()
        assert draft["a"] is None and draft["sigma_m_crit"] == lateral.crit_spin.value()
        lateral.dirty = False
        shear = _tab_of(window, "tab_mc_shear")
        shear.load("SC-01")
        assert not shear.effort_form.isRowVisible(shear.n_spin) and "N" not in shear.draft()
        shear.new()
        _select(shear.position_box, "T001")
        shear.pith_box.setChecked(True)
        assert shear.save(), "a new shear check is saved"
        saved = shear.current_id
        exported = json.loads((here.data_dir / member_check.EXPORT_FILE).read_text(encoding="utf-8"))["checks"][saved]
        assert exported["calculable"] and exported["pith"] is True and exported["N"] is None, exported
        (here.checks_dir / ("%s.json" % saved)).unlink()
        member_check.export(here)
        shear.dirty = False
        shear.load("SC-01")


def test_the_tension_tab_has_three_panes_and_its_cards():
    window, here = _window()
    with project.using(here):
        tab = _tab(window)
        assert tab.splitter.count() == 3
        from PySide6.QtWidgets import QGroupBox
        titles = {box.title() for box in tab.findChildren(QGroupBox)}
        for key in ("mc_box_position", "mc_box_material", "mc_box_section", "mc_box_effort", "mc_results", "ds_call"):
            assert tab.t(key) in titles, key
        # every kind is printed unfolded (spec 2026-10-15, UI-003; spec 2026-10-21-commandes-typst-refonte, REQ-017): its domain one click away, no option of its own
        assert tab.UNFOLDED and not tab.formulas_button.isHidden() and _ctab(window).UNFOLDED
        # two views since v0.117: «Calcul» -- the list, the form, the result -- and «Affichage» -- the list, the page, the options and the call
        assert tab.VIEWS == ("calc", "display")
        tab.set_view("calc")
        assert tab.panes.centre.currentIndex() == 0 and tab.panes.right.currentIndex() == 0, "«Calcul»: the form and the result"
        # the saved checks are listed, ZT-01 and ZT-02 of the example project
        assert {"ZT-01", "ZT-02"} <= set(tab.ids), tab.ids
        from PySide6.QtWidgets import QPushButton
        buttons = {button.text() for button in tab.findChildren(QPushButton)}
        assert {tab.t("mc_new"), tab.t("mc_duplicate"), tab.t("mc_delete"), tab.t("mc_revert"), tab.t("mc_save")} <= buttons, buttons


def test_a_value_that_follows_its_position_says_so_in_its_own_field():
    window, here = _window()
    with project.using(here):
        tab = _tab(window)
        tab.dirty = False
        tab.load("ZT-01")      # position T001, nothing stated: C24, 100 x 200 mm, class 2 -- all from the position
        assert tab.grade_box.currentData() is None and tab.section_box.currentData() is None and tab.moisture_box.currentData() is None
        assert tab.grade_box.itemText(0) == "C24 — T001", tab.grade_box.itemText(0)
        assert "repris de T001" in tab.grade_box.currentText() or "T001" in tab.grade_box.currentText()
        assert tab.moisture_box.itemText(0) == "2 — T001"
        assert "100" in tab.section_box.itemText(0) and "200" in tab.section_box.itemText(0) and "T001" in tab.section_box.itemText(0)
        # a value that follows is shown on the form, closed to typing, and no orange line is said
        assert (tab.b_spin.value(), tab.h_spin.value()) == (100.0, 200.0) and not tab.b_spin.isEnabled()
        assert not tab.grade_back.isVisibleTo(tab) and tab.grade_note.text() == ""
        draft = tab.draft()
        assert draft["grade"] is None and draft["section"] is None and draft["moisture_class"] is None and draft["position"] == "T001"
        assert not tab.dirty


def test_a_value_typed_over_its_position_is_orange_with_reprendre_which_takes_it_back():
    window, here = _window()
    import theme
    with project.using(here):
        tab = _tab(window)
        tab.dirty = False
        tab.load("ZT-01")
        # the strength class written over
        _select(tab.grade_box, "GL24h")
        assert tab.dirty and tab.draft()["grade"] == "GL24h"
        assert "T001" in tab.grade_note.text() and "C24" in tab.grade_note.text(), tab.grade_note.text()
        assert theme.colour("override") in tab.grade_note.styleSheet()
        assert tab.grade_back.isVisibleTo(tab) and tab.grade_note.isVisibleTo(tab)
        tab.grade_back.click()
        assert tab.grade_box.currentData() is None and tab.draft()["grade"] is None and tab.grade_note.text() == ""
        # the moisture class, and the section, likewise
        _select(tab.moisture_box, 3)
        assert tab.draft()["moisture_class"] == 3 and "T001" in tab.moisture_note.text()
        tab.moisture_back.click()
        assert tab.draft()["moisture_class"] is None
        _select(tab.section_box, "cir")
        assert tab.draft()["section"]["type"] == "cir" and tab.d_spin.isEnabled()
        assert tab.section_form.isRowVisible(tab.row_of(tab.d_spin)) and not tab.section_form.isRowVisible(tab.row_of(tab.b_spin))   # a row holds the field with its variable button
        assert "T001" in tab.section_note.text()
        tab.section_back.click()
        assert tab.draft()["section"] is None and not tab.d_spin.isEnabled()
        tab.dirty = False


def test_without_a_position_the_values_are_typed_and_a_position_gone_is_said():
    window, here = _window()
    with project.using(here):
        tab = _tab(window)
        tab.dirty = False
        tab.load("ZT-02")     # no position: GL24h, 120 x 240, class 1, alpha 10
        assert tab.grade_box.currentData() == "GL24h" and tab.section_box.currentData() == "rec"
        assert (tab.b_spin.value(), tab.h_spin.value()) == (120.0, 240.0) and tab.b_spin.isEnabled()
        assert tab.moisture_box.currentData() == 1 and tab.alpha_spin.value() == 10.0 and tab.n_spin.value() == 20.0
        assert tab.grade_note.text() == "" and tab.grade_box.itemText(0) == tab.t("mc_none")
        # a position the export does not list: kept, marked, said in orange
        source = tab.draft()
        source["position"] = "T009"
        tab.source = source
        tab.fill_form()
        assert tab.position_box.currentData() == "T009" and "(?)" in tab.position_box.currentText()
        assert "T009" in tab.position_note.text()
        assert tab.draft()["position"] == "T009"
        tab.dirty = False


def test_a_new_check_is_saved_exported_and_listed():
    window, here = _window()
    with project.using(here):
        tab = _tab(window)
        _fresh(tab)
        assert tab.current_id is None and tab.draft()["id"].startswith("Z_")
        tab.identity.name.setText("Zugstab Süd")
        assert tab.identity.id.text() == "Zugstab_Sud", "the ID follows the name"
        tab.identity.description.setText("Zug im Stab")
        _select(tab.position_box, "S001")
        tab.n_spin.setValue(40.0)
        assert tab.dirty
        with _boxes():
            assert tab.save() is True
        path = here.checks_dir / "Zugstab_Sud.json"
        assert path.is_file()
        written = json.loads(path.read_text(encoding="utf-8"))
        assert written["position"] == "S001" and written["name"] == "Zugstab Süd" and written["label"] == "Zug im Stab"
        assert written["grade"] is None and written["section"] is None and written["N"] == {"value": 40.0, "unit": "kN"}
        assert not tab.dirty and tab.current_id == "Zugstab_Sud" and "Zugstab_Sud" in tab.ids
        exported = json.loads((here.data_dir / "checks.json").read_text(encoding="utf-8"))
        assert "Zugstab_Sud" in exported["checks"], list(exported["checks"])
        assert exported["checks"]["Zugstab_Sud"]["calculable"] is True


def test_an_id_taken_is_refused_ignoring_case_and_a_rename_is_asked_first():
    window, here = _window()
    with project.using(here):
        tab = _tab(window)
        _fresh(tab)
        tab.identity.id.setText("zt-01")        # ZT-01 exists: the file system does not tell the two apart
        with _boxes() as shown:
            assert tab.save() is False
        assert shown and "zt-01" in shown[0], shown
        assert [p.name for p in here.checks_dir.glob("*.json") if p.stem.lower() == "zt-01"] == ["ZT-01.json"]
        # a rename of a saved check is asked about, and a «no» writes nothing
        tab.dirty = False
        tab.load("ZT-02")
        tab.identity.id.setText("ZT-02b")
        from PySide6.QtWidgets import QMessageBox
        with _boxes(lambda text: QMessageBox.StandardButton.No) as shown:
            assert tab.save() is False
        assert shown and "ZT-02" in shown[0] and "ZT-02b" in shown[0]
        assert (here.checks_dir / "ZT-02.json").is_file() and not (here.checks_dir / "ZT-02b.json").exists()
        with _boxes():
            assert tab.save() is True
        assert (here.checks_dir / "ZT-02b.json").is_file() and not (here.checks_dir / "ZT-02.json").exists()
        # put back
        tab.identity.id.setText("ZT-02")
        with _boxes():
            assert tab.save() is True
        assert (here.checks_dir / "ZT-02.json").is_file()
        tab.dirty = False


def test_the_page_is_asked_for_from_the_draft_with_its_values_written_into_the_call():
    window, here = _window()
    with project.using(here):
        tab = _tab(window)
        tab.dirty = False
        tab.load("ZT-02")
        asked = []
        tab.pane.request_snippet = lambda here_, mode, source, key: asked.append((here_, mode, source, key))
        tab.live = False
        tab.set_view("display")      # the page compiles only in «Affichage» (v0.117)
        tab.refresh()
        assert asked == [], "nothing is compiled before the tab has been shown"
        tab.on_shown()
        assert asked, "shown, the tab asks for its page"
        _here, mode, source, key = asked[-1]
        assert mode == window.current_document() and key
        assert source.startswith("#import") and '"/000-Typst-Config/commands.typ"' in source
        # a tension's page is its domain unfolded (spec 2026-10-15, UI-003): its values written as literals, no domain: a draft is in no export
        assert '#domain("ZT-02"' in source and "#verify(" in source and "GL24h" in source and "120/240" in source and '20, "kN"' in source, source
        assert 'domain: ("check"' not in source and "gen:" not in source
        assert tab.command_text() == '#include domain-file("check", "ZT-02")'   # no path written by hand (ARCH-008)
        # an edit in the form -- not saved -- is in the next page, newest request first
        tab.n_spin.setValue(55.0)
        tab.refresh()
        assert '55, "kN"' in asked[-1][2] and tab.dirty
        # a check that cannot be calculated asks for no page and says why in the pane
        tab.n_spin.setValue(0.0)
        count = len(asked)
        tab.refresh()
        assert len(asked) == count
        assert tab.record["calculable"] is False and not tab.message.isHidden() and tab.message.text()
        assert tab.display.note.text() == tab.reason, "the reason is said in place of the page"
        tab.set_view("calc")
        tab.dirty = False
        tab.live = False


def test_delete_archives_and_the_id_is_free_again():
    window, here = _window()
    import source_archive
    with project.using(here):
        tab = _tab(window)
        _fresh(tab)
        tab.identity.id.setText("Z_arch")
        with _boxes():
            assert tab.save() is True
            assert (here.checks_dir / "Z_arch.json").is_file()
            tab.delete()
        assert not (here.checks_dir / "Z_arch.json").exists(), "archived: out of the folder the export reads"
        archived = list(source_archive.folder(here.checks_dir).glob("*.json"))
        assert archived and all("id" not in json.loads(p.read_text(encoding="utf-8")) for p in archived)
        assert "Z_arch" not in tab.ids
        exported = json.loads((here.data_dir / "checks.json").read_text(encoding="utf-8"))
        assert "Z_arch" not in exported["checks"]
        tab.dirty = False


def test_a_drop_in_a_folder_writes_the_group_field():
    window, here = _window()
    with project.using(here):
        tab = _tab(window)
        tab.dirty = False
        with _boxes():
            tab.on_moved(["ZT-02"], "Zugglieder")
        assert json.loads((here.checks_dir / "ZT-02.json").read_text(encoding="utf-8"))["group"] == "Zugglieder"
        with _boxes():
            tab.on_moved(["ZT-02"], "")
        assert not json.loads((here.checks_dir / "ZT-02.json").read_text(encoding="utf-8")).get("group")
        tab.dirty = False


def test_a_project_opened_read_only_writes_nothing():
    window, here = _window()
    with project.using(here):
        tab = _tab(window)
        tab.dirty = False
        tab.load("ZT-02")
        before = (here.checks_dir / "ZT-02.json").read_bytes()
        window.read_only = True
        refused = []
        window.refuse_read_only = lambda *a, **k: refused.append(True)
        try:
            tab.n_spin.setValue(77.0)
            assert tab.save() is False and tab.delete() is False
        finally:
            window.read_only = False
        assert len(refused) == 2, refused
        assert (here.checks_dir / "ZT-02.json").read_bytes() == before
        tab.dirty = False
        tab.load("ZT-02")


def test_the_draft_travels_through_a_rebuild():
    window, here = _window()
    with project.using(here):
        tab = _ctab(window)
        tab.dirty = False
        tab.load("DR-02")
        tab.n_spin.setValue(33.0)
        state = tab.view_state()
        assert state["dirty"] and state["draft"]["N"]["value"] == 33.0 and state["current_id"] == "DR-02"
        import member_check_tab
        window.views["tab_mc_compression"] = state
        other = member_check_tab.CompressionTab(window)
        try:
            assert other.dirty and other.current_id == "DR-02" and other.n_spin.value() == 33.0
            assert other.command_text() == '#include domain-file("check", "DR-02")'
        finally:
            window.views.pop("tab_mc_compression", None)
            other.dirty = False
            other.deleteLater()
        tab.dirty = False
        tab.load("DR-02")


def test_the_words_are_in_three_languages_with_no_sharp_s_and_a_space_before_a_french_colon():
    _qt()
    import re
    import member_check_tab
    reference = set(member_check_tab.STRINGS["fr"])
    for lang, table in member_check_tab.STRINGS.items():
        assert set(table) == reference, f"{lang}: {sorted(set(table) ^ reference)}"
        assert all(text for text in table.values()), lang
    assert not any("ß" in text for text in member_check_tab.STRINGS["de"].values()), "Swiss German never has an ß"
    glued = [text for text in member_check_tab.STRINGS["fr"].values()
             if re.search(r"[^\s  \d][;:](\s|$)", re.sub(r"\{[^}]*\}", "", text))]
    assert not glued, glued
    # the sentences of the engine's warnings, which `note_text` reads as "warn_" + the Note's code
    for code in ("check_position_missing", "check_not_calculable"):
        assert all("warn_" + code in member_check_tab.STRINGS[lang] for lang in ("fr", "de", "en"))

def test_the_engines_warnings_are_said_in_the_window_s_language():
    window, here = _window()
    from domains import member_check
    notes = member_check.resolve(member_check.new_source("Z_x"), {})["warnings"]
    notes += member_check.resolve(member_check.new_source("Z_y") | {"position": "T999"}, {})["warnings"]
    assert {note.code for note in notes} >= {"check_not_calculable", "check_position_missing"}, [n.code for n in notes]
    for note in notes:
        said = window.note_text(note)
        assert said != str(note) and note.args["check"] in said, (str(note), said)



# --- Compression ---------------------------------------------------------------------

def test_the_compression_tab_is_built_in_the_report_alone_and_the_two_tabs_share_a_base():
    window, here = _window()
    import member_check_tab
    import woodcore_gui
    with project.using(here):
        tab = _ctab(window)
        assert isinstance(tab, member_check_tab.MemberCheckTab) and not isinstance(tab, member_check_tab.TensionTab)
        assert isinstance(_tab(window), member_check_tab.MemberCheckTab)
        assert (tab.KEY, tab.KIND, tab.ID_PREFIX) == ("tab_mc_compression", "compression", "DR-")
        assert "tab_mc_compression" in woodcore_gui.mode_tabs("rs")
        assert "tab_mc_compression" not in woodcore_gui.mode_tabs("cu") and "tab_mc_compression" not in woodcore_gui.mode_tabs("bp")
        assert tab.splitter.count() == 3
        from PySide6.QtWidgets import QGroupBox
        titles = {box.title() for box in tab.findChildren(QGroupBox)}
        for key in ("mc_box_position", "mc_box_material", "mc_box_section", "mc_box_effort", "mc_box_support", "mc_results", "ds_call"):
            assert tab.t(key) in titles, key
    # the read-only guard sits on the base, so on both tabs, and the subclasses override no writer
    assert "save" in {k: v for c in reversed(woodcore_gui.own_classes(member_check_tab.MemberCheckTab)) for k, v in vars(c).items()} and "save" not in vars(member_check_tab.CompressionTab)
    assert hasattr(member_check_tab.MemberCheckTab.save, "__wrapped__") and hasattr(member_check_tab.MemberCheckTab.delete, "__wrapped__"), "the read-only guard wraps the base"


def test_each_tab_lists_its_own_kind_and_an_id_is_unique_across_both():
    window, here = _window()
    with project.using(here):
        t, c = _tab(window), _ctab(window)
        t.reload_list()
        c.reload_list()
        assert {"ZT-01", "ZT-02"} <= set(t.ids) and not any(i.startswith("DR-") for i in t.ids), t.ids
        assert {"DR-01", "DR-02"} <= set(c.ids) and not any(i.startswith("ZT-") for i in c.ids), c.ids
        # a new compression takes the first free DR-nn, a new tension the first free Z_nn
        _fresh(c)
        assert c.draft()["id"].startswith("DR-") and c.draft()["kind"] == "compression"
        _fresh(t)
        assert t.draft()["id"].startswith("Z_") and t.draft()["kind"] == "tension"
        # an ID of the other kind is taken, whatever its case
        _fresh(c)
        c.identity.id.setText("zt-01")
        with _boxes() as shown:
            assert c.save() is False
        assert shown and "zt-01" in shown[0], shown
        _fresh(t)
        t.identity.id.setText("dr-01")
        with _boxes() as shown:
            assert t.save() is False
        assert shown and "dr-01" in shown[0], shown
        assert sorted(p.name for p in here.checks_dir.glob("*.json") if p.stem.lower() in ("zt-01", "dr-01")) == ["DR-01.json", "ZT-01.json"]
        _fresh(c)
        _fresh(t)


def test_alpha_zero_is_a_normal_force_and_above_zero_a_force_on_a_bearing_with_its_card():
    window, here = _window()
    with project.using(here):
        tab = _ctab(window)
        tab.dirty = False
        tab.load("DR-02")        # alpha 0
        assert tab.alpha_spin.value() == 0
        assert not tab.support_card.isVisibleTo(tab)
        assert tab.n_label.text() == tab.t("mc_N_compression")
        tab.alpha_spin.setValue(90.0)
        assert tab.support_card.isVisibleTo(tab) and tab.n_label.text() == tab.t("mc_F_support")
        assert tab.t("mc_F_support")[:1] == "F" and tab.t("mc_N_compression")[:1] == "N"
        assert tab.dirty and tab.draft()["alpha"] == 90.0
        tab.alpha_spin.setValue(30.0)
        assert tab.support_card.isVisibleTo(tab) and tab.n_label.text() == tab.t("mc_F_support")
        tab.alpha_spin.setValue(0.0)
        assert not tab.support_card.isVisibleTo(tab) and tab.n_label.text() == tab.t("mc_N_compression")
        # what the card held stays in the source while it is hidden
        tab.alpha_spin.setValue(45.0)
        _select(tab.support_box, "vorholz")
        tab.l_spin.setValue(150.0)
        tab.alpha_spin.setValue(0.0)
        draft = tab.draft()
        assert (draft["case"], draft["larger"], draft["l"]) == ("mit_vorholz", False, 150.0), draft
        tab.dirty = False
        # a saved check opened at 90 degrees shows the card at once, one at 0 hides it again
        tab.load("DR-01")
        assert tab.alpha_spin.value() == 90 and tab.support_card.isVisibleTo(tab) and tab.n_label.text() == tab.t("mc_F_support")
        tab.load("DR-02")
        assert not tab.support_card.isVisibleTo(tab)
        tab.dirty = False


def test_the_five_resistances_map_to_case_and_larger_and_back():
    window, here = _window()
    import member_check_tab
    with project.using(here):
        tab = _ctab(window)
        tab.dirty = False
        tab.load("DR-01")
        expected = (("general", "generell", False), ("vorholz", "mit_vorholz", False), ("vorholz+", "mit_vorholz", True),
                    ("end", "endauflagerung", False), ("end+", "endauflagerung", True))
        assert tuple((d, c, l) for d, c, l, _k in member_check_tab.SUPPORT_CHOICES) == expected
        assert [tab.support_box.itemData(i) for i in range(tab.support_box.count())] == [e[0] for e in expected]
        assert [tab.support_box.itemText(i) for i in range(5)] == [tab.t(k) for _d, _c, _l, k in member_check_tab.SUPPORT_CHOICES]
        for data, case, larger in expected:
            _select(tab.support_box, data)
            draft = tab.draft()
            assert (draft["case"], draft["larger"]) == (case, larger), data
            tab.source = dict(draft)
            tab.fill_form()
            assert tab.support_box.currentData() == data, data
        tab.dirty = False
        tab.load("DR-01")
        assert tab.support_box.currentData() == "end"
        tab.load("DR-02")      # case null: generell
        assert tab.support_box.currentData() == "general"
        tab.dirty = False


def test_a_grade_without_a_bracketed_value_closes_the_two_bracketed_resistances():
    window, here = _window()
    import theme
    with project.using(here):
        tab = _ctab(window)
        tab.dirty = False
        tab.load("DR-02")        # GL24h, written over
        tab.alpha_spin.setValue(90.0)
        model = tab.support_box.model()
        assert [model.item(i).isEnabled() for i in range(5)] == [True] * 5
        _select(tab.grade_box, "D30")
        assert [model.item(i).isEnabled() for i in range(5)] == [True, True, False, True, False]
        from PySide6.QtCore import Qt
        assert "D30" in tab.support_box.itemData(2, Qt.ItemDataRole.ToolTipRole) and "D30" in tab.support_box.itemData(4, Qt.ItemDataRole.ToolTipRole), "the tooltip says why"
        assert not tab.support_note.isVisibleTo(tab)
        _select(tab.support_box, "end+")
        _select(tab.grade_box, "GL24h")
        assert model.item(4).isEnabled() and not tab.support_note.isVisibleTo(tab)
        _select(tab.grade_box, "D30")      # chosen, then closed by the grade: said in orange, never changed silently
        assert tab.support_note.isVisibleTo(tab) and "D30" in tab.support_note.text() and theme.colour("override") in tab.support_note.styleSheet()
        assert tab.support_box.currentData() == "end+"
        # the grade that follows the position counts too: T001 is C24, which has a bracketed value
        tab.dirty = False
        tab.load("DR-01")
        assert all(model.item(i).isEnabled() for i in range(5))
        tab.dirty = False


def test_the_contact_width_follows_the_section_and_is_written_over_in_orange():
    window, here = _window()
    import theme
    with project.using(here):
        tab = _ctab(window)
        tab.dirty = False
        tab.load("DR-01")      # T001, 100 x 200 mm: nothing stated, w null
        assert tab.draft()["w"] is None and not tab.w_stated
        assert tab.w_spin.value() == 100.0 and tab.w_spin.suffix() == tab.t("mc_w_followed")
        assert not tab.w_back.isVisibleTo(tab) and tab.w_note.text() == ""
        tab.w_spin.setValue(80.0)
        assert tab.w_stated and tab.draft()["w"] == 80.0 and tab.dirty
        assert "100" in tab.w_note.text() and theme.colour("override") in tab.w_note.styleSheet()
        assert tab.w_back.isVisibleTo(tab) and tab.w_spin.suffix() == " mm"
        tab.w_back.click()
        assert tab.draft()["w"] is None and tab.w_spin.value() == 100.0 and not tab.w_back.isVisibleTo(tab)
        # a section written over changes the width it follows
        _select(tab.section_box, "rec")
        tab.b_spin.setValue(140.0)
        assert tab.w_spin.value() == 140.0 and tab.draft()["w"] is None
        # a round section gives its diameter
        _select(tab.section_box, "cir")
        tab.d_spin.setValue(180.0)
        assert tab.w_spin.value() == 180.0
        tab.dirty = False
        tab.load("DR-01")
        # a stated width is read back as stated
        source = tab.draft()
        source["w"] = 90.0
        tab.source = source
        tab.fill_form()
        assert tab.w_stated and tab.w_spin.value() == 90.0 and tab.draft()["w"] == 90.0
        tab.dirty = False


def test_a_compression_is_saved_with_its_kind_and_its_bearing():
    window, here = _window()
    from domains import member_check
    with project.using(here):
        tab = _ctab(window)
        _fresh(tab)
        assert tab.current_id is None
        tab.identity.id.setText("DR-new")
        _select(tab.position_box, "T001")
        tab.alpha_spin.setValue(90.0)
        tab.n_spin.setValue(25.0)
        _select(tab.support_box, "vorholz+")
        tab.l_spin.setValue(120.0)
        with _boxes():
            assert tab.save() is True
        path = here.checks_dir / "DR-new.json"
        written = json.loads(path.read_text(encoding="utf-8"))
        assert written["kind"] == "compression" and written["alpha"] == 90.0 and written["N"] == {"value": 25.0, "unit": "kN"}
        assert (written["case"], written["larger"], written["l"], written["w"]) == ("mit_vorholz", True, 120.0, None)
        member_check.read_source(path)         # the source the engine reads
        exported = json.loads((here.data_dir / "checks.json").read_text(encoding="utf-8"))["checks"]["DR-new"]
        assert exported["kind"] == "compression" and exported["w"] == 100 and exported["w_from"] == "section", exported
        assert "DR-new" in tab.ids and "DR-new" not in _tab(window).ids
        # an angle with no bearing length is a source the engine refuses, said in the pane
        tab.l_spin.setValue(0.0)
        assert tab.draft()["l"] is None
        tab.refresh()
        assert tab.message.isVisibleTo(tab) and tab.reason
        # the call and the page are the check's own
        tab.l_spin.setValue(120.0)
        asked = []
        tab.pane.request_snippet = lambda here_, mode, source, key: asked.append(source)
        tab.set_view("display")
        tab.on_shown()
        # the page is the domain the export would write (spec 2026-10-15, UI-003): across the grain f_c,90,d, along it f_c,0,d
        assert asked and "#domain(" in asked[-1] and '"f_c_90_d"' in asked[-1], asked[-1:]
        tab.alpha_spin.setValue(0.0)
        tab.refresh()
        assert '"f_c_0_d"' in asked[-1] and '"f_c_90_d"' not in asked[-1], asked[-1:]
        tab.set_view("calc")
        tab.live = False
        tab.dirty = False


def test_archiving_a_compression_leaves_the_tension_tab_alone():
    window, here = _window()
    with project.using(here):
        c, t = _ctab(window), _tab(window)
        _fresh(c)
        c.identity.id.setText("DR-arch")
        with _boxes():
            assert c.save() is True
            c.delete()
        assert not (here.checks_dir / "DR-arch.json").exists()
        c.reload_list()
        t.reload_list()
        mine = {row["id"] for row in c._archived_of_kind()}
        theirs = {row["id"] for row in t._archived_of_kind()}
        assert mine and not (mine & theirs), (mine, theirs)
        c.dirty = False
        t.dirty = False


def test_the_compression_words_are_in_three_languages():
    _qt()
    import member_check_tab
    for lang in ("fr", "de", "en"):
        table = member_check_tab.STRINGS[lang]
        for key in ("mc_sup_general", "mc_sup_vorholz", "mc_sup_vorholz_larger", "mc_sup_end", "mc_sup_end_larger", "mc_N_compression", "mc_F_support", "mc_w_followed"):
            assert table[key], (lang, key)
    fr = member_check_tab.STRINGS["fr"]
    assert fr["mc_F_support"] == "F — force sur la surface d’appui" and fr["mc_N_compression"] == "N — effort normal (compression)"
    assert fr["mc_sup_vorholz"].startswith("Avec avant-bois (≥ 100 mm des deux côtés)")
    assert "Vorholz" in member_check_tab.STRINGS["de"]["mc_sup_vorholz"] and "Endauflagerung" in member_check_tab.STRINGS["de"]["mc_sup_end"]
    assert "end support" in member_check_tab.STRINGS["en"]["mc_sup_end"].lower() and "end distance" in member_check_tab.STRINGS["en"]["mc_sup_vorholz"]


# --- Flexion (SIA 265 4.2.3, 4.2.4) -------------------------------------------------------

def _btab(window):
    import member_check_tab
    return next(t for t in window.tabs if isinstance(t, member_check_tab.BendingTab))


def test_the_bending_tab_is_built_on_the_base_and_lists_its_own_kind():
    window, here = _window()
    import member_check_tab
    with project.using(here):
        tab = _btab(window)
        assert isinstance(tab, member_check_tab.MemberCheckTab) and (tab.KEY, tab.KIND, tab.ID_PREFIX) == ("tab_mc_bending", "bending", "BI-")
        assert tab.splitter.count() == 3
        tab.reload_list()
        assert {"BI-01", "BI-02", "BI-03"} <= set(tab.ids) and not any(i.startswith(("ZT-", "DR-")) for i in tab.ids), tab.ids
        assert not any(i.startswith("BI-") for i in _tab(window).ids + _ctab(window).ids)
        _fresh(tab)
        draft = tab.draft()
        assert draft["id"].startswith("BI-") and draft["kind"] == "bending" and draft["N"] == {"value": 0.0, "unit": "kN"}
        assert draft["M_y"] == {"value": 10.0, "unit": "kNm"} and draft["M_z"] is None
        assert tab.n_spin.minimum() < 0 and _tab(window).n_spin.minimum() == 0, "a bending's normal force is signed, a tension's is not"
        tab.dirty = False
    assert "save" not in vars(member_check_tab.BendingTab), "the read-only guard sits on the base"


def test_at_an_angle_m_z_is_closed_and_zero_and_n_stays_open():
    window, here = _window()
    with project.using(here):
        tab = _btab(window)
        _fresh(tab)
        tab.mz_spin.setValue(1.5)
        tab.n_spin.setValue(-20.0)
        assert tab.mz_spin.isEnabled() and not tab.mz_note.isVisibleTo(tab)
        assert tab.draft()["M_z"] == {"value": 1.5, "unit": "kNm"} and tab.draft()["N"]["value"] == -20.0
        tab.alpha_spin.setValue(30.0)
        assert not tab.mz_spin.isEnabled() and tab.mz_spin.value() == 0 and tab.mz_note.isVisibleTo(tab)
        assert tab.n_spin.isEnabled()
        draft = tab.draft()
        assert draft["M_z"] is None and draft["N"]["value"] == -20.0 and draft["alpha"] == 30.0
        tab.alpha_spin.setValue(0.0)
        assert tab.mz_spin.isEnabled() and not tab.mz_note.isVisibleTo(tab)
        tab.dirty = False


def test_a_bending_is_saved_exported_and_computed_at_once():
    window, here = _window()
    from domains import member_check
    with project.using(here):
        tab = _btab(window)
        _fresh(tab)
        tab.identity.id.setText("BI-new")
        _select(tab.position_box, "T001")
        tab.my_spin.setValue(4.0)
        tab.mz_spin.setValue(0.5)
        tab.n_spin.setValue(-30.0)
        tab.refresh()
        # the result is compute()'s, the verdict the ratio against 1 (issue #12), with no compile
        assert "4.2.4.2" in tab.results_label.text() and "⩽ 1" in tab.verdict_label.text(), tab.results_label.text()
        with _boxes():
            assert tab.save() is True
        path = here.checks_dir / "BI-new.json"
        written = json.loads(path.read_text(encoding="utf-8"))
        assert written["kind"] == "bending" and written["N"] == {"value": -30.0, "unit": "kN"}
        assert written["M_y"] == {"value": 4.0, "unit": "kNm"} and written["M_z"] == {"value": 0.5, "unit": "kNm"}
        member_check.read_source(path)
        exported = json.loads((here.data_dir / "checks.json").read_text(encoding="utf-8"))["checks"]["BI-new"]
        assert exported["calculable"] and exported["M_y"] == {"value": 4.0, "unit": "kNm"}, exported
        # the page is the domain the export would write: with N its compression, without N the bending alone
        asked = []
        tab.pane.request_snippet = lambda here_, mode, source, key: asked.append(source)
        tab.set_view("display")
        tab.on_shown()
        assert asked and "#domain(" in asked[-1] and '"N_c_d"' in asked[-1], asked[-1:]
        tab.n_spin.setValue(0.0)
        tab.refresh()
        assert '"N_c_d"' not in asked[-1], asked[-1:]
        # no moment at all: not calculable, said in the results
        tab.my_spin.setValue(0.0)
        tab.mz_spin.setValue(0.0)
        tab.refresh()
        assert "no moment" in tab.reason, tab.reason
        tab.set_view("calc")
        tab.live = False
        tab.dirty = False


def test_a_saved_bending_is_loaded_back_into_its_fields():
    """UI-001: a bending of the example project read back into the form -- α, the signed N, the moments -- and its result the one the report prints (BI-02: (22), η 0.44; BI-03: (21) at 10°, η 0.698, M_z closed)."""
    window, here = _window()
    with project.using(here):
        tab = _btab(window)
        tab.dirty = False
        tab.load("BI-02")
        assert (tab.alpha_spin.value(), tab.n_spin.value(), tab.my_spin.value(), tab.mz_spin.value()) == (0.0, -40.0, 3.0, 0.0)
        assert tab.mz_spin.isEnabled() and not tab.dirty
        tab.refresh()
        assert "4.2.4.2" in tab.results_label.text() and "0.44" in tab.verdict_label.text(), tab.verdict_label.text()
        tab.load("BI-03")
        assert (tab.alpha_spin.value(), tab.n_spin.value(), tab.my_spin.value()) == (10.0, 25.0, 3.0)
        assert not tab.mz_spin.isEnabled() and tab.mz_note.isVisibleTo(tab) and not tab.dirty
        tab.refresh()
        assert "4.2.4.1" in tab.results_label.text() and "0.698" in tab.verdict_label.text(), tab.verdict_label.text()
        tab.load("BI-01")
        assert (tab.my_spin.value(), tab.mz_spin.value(), tab.n_spin.value()) == (4.5, 0.3, 0.0)
        tab.dirty = False


def test_the_bending_words_are_in_three_languages():
    _qt()
    import member_check_tab
    for lang in ("fr", "de", "en"):
        table = member_check_tab.STRINGS[lang]
        for key in ("mc_list_bending", "mc_empty_bending", "mc_alpha_bending", "mc_My", "mc_Mz", "mc_Mz_angle", "mc_N_bending"):
            assert table[key], (lang, key)
    fr = member_check_tab.STRINGS["fr"]
    assert fr["mc_N_bending"] == "Effort normal N (traction +, compression −)" and "(17) à (20)" in fr["mc_Mz_angle"]
    assert "Zug +" in member_check_tab.STRINGS["de"]["mc_N_bending"] and "tension +" in member_check_tab.STRINGS["en"]["mc_N_bending"]


# --- The results: Python's, instant -----------------------------------------------------

@contextlib.contextmanager
def _compute(ok=True, eta=0.42, relation=None):
    """`member_check.compute` replaced by a stub of the contract's shape -- {kind, equation, clause, rows, eta, ok, relation} --, counting its calls: what is held here is the tab's reading of it, not the arithmetic (the engine's own tests hold that)."""
    from domains import member_check
    calls = []

    def stub(record):
        calls.append(record["N"]["value"])
        return {"kind": record["kind"], "equation": "sigma_(t,0,d) <= f_(t,0,d)", "clause": "SIA 265 4.2.1",
                "rows": [{"key": "sigma", "symbol": "sigma_(t,0,d)", "value": record["N"]["value"] / 10, "unit": "N/mm²", "label": "Zugspannung"},
                         {"key": "f", "symbol": "f_(t,0,d)", "value": 9.5, "unit": "N/mm²", "formula": "eta_w dot f_(t,0,k)"}],
                "eta": eta, "ok": ok, "relation": relation or ("<=" if ok else ">"), "ratio": "sigma_(t,0,d) / f_(t,0,d)"}

    saved = getattr(member_check, "compute", None)
    member_check.compute = stub
    try:
        yield calls
    finally:
        if saved is None:
            del member_check.compute
        else:
            member_check.compute = saved


def test_the_results_follow_every_edit_at_once_and_ask_for_no_page():
    for pick in (_tab, _ctab):
        window, here = _window()
        with project.using(here):
            tab = pick(window)
            tab.dirty = False
            tab.load("ZT-01" if pick is _tab else "DR-02")
            tab.set_view("calc")
            asked = []
            tab.pane.request_snippet = lambda here_, mode, source, key: asked.append(source)
            tab.live = True
            with _compute() as calls:
                tab.refresh()
                first = tab.results_label.text()
                assert "SIA 265 4.2.1" in first and "f<sub>t,0,d</sub>" in first and "N/mm²" in first and "Zugspannung" in first, first
                before = len(calls)
                tab.n_spin.setValue(30.0)         # no timer, no wait: the label is already the new one
                assert len(calls) > before and calls[-1] == 30.0
                assert "3" in tab.results_label.text() and tab.results_label.text() != first
                verdict = tab.verdict_label.text()
                assert tab.verdict_label.isVisibleTo(tab) and "0.42" in verdict and "⩽ 1" in verdict and "η" not in verdict and "σ" in verdict and "/" in verdict, verdict
            assert asked == [], "in «Calcul» no page is asked for, whatever is edited"
            tab.dirty = False
            tab.live = False


def test_the_verdict_of_the_real_calculation_is_the_ratio_against_one():
    """Against the engine's own compute(), not a stub: its `relation` is the whole relation in registry keys («sigma_c_90_d <= f_c_90_d»), and the verdict printed it raw -- «η = 0.926 sigma_c_90_d <= f_c_90_d 1 ✔» (v0.117, found on a screenshot). Since issue #12 the verdict is the ratio of the action to the resistance, `σ/f = 0.41 ⩽ 1`, as the report prints it, and never η."""
    window, here = _window()
    with project.using(here):
        for pick, cid in ((_tab, "ZT-01"), (_ctab, "DR-01")):
            tab = pick(window)
            tab.dirty = False
            tab.load(cid)
            tab.refresh()
            text = tab.verdict_label.text()
            assert "⩽ 1" in text and "sigma" not in text and "_" not in text and "η" not in text and "σ" in text and "/" in text, text
            tab.dirty = False


def test_the_verdict_has_its_own_colour_for_ok_and_not_ok():
    window, here = _window()
    import theme
    with project.using(here):
        tab = _tab(window)
        tab.dirty = False
        tab.load("ZT-01")
        ok_colour, danger_colour = theme.colour("ok"), theme.colour("danger")
        assert ok_colour != danger_colour
        with _compute(ok=True, eta=0.42):
            tab.refresh()
            text = tab.verdict_label.text()
            assert ok_colour in text and "✔" in text and danger_colour not in text, text
        with _compute(ok=False, eta=1.3):
            tab.refresh()
            text = tab.verdict_label.text()
            assert danger_colour in text and "✘" in text and ok_colour not in text and ">" in text.replace("&nbsp;", "") and "1.3" in text, text
        tab.dirty = False


def test_a_check_that_cannot_be_calculated_says_why_in_the_results():
    window, here = _window()
    with project.using(here):
        tab = _tab(window)
        tab.dirty = False
        tab.load("ZT-02")
        with _compute() as calls:
            tab.n_spin.setValue(0.0)           # a tension of 0 kN: the record gives its reason
            assert not calls or calls[-1] != 0.0, "nothing is computed for a record that is not calculable"
            assert not tab.verdict_label.isVisibleTo(tab) and tab.reason and tab.reason[:20] in tab.results_label.text().replace("&amp;", "&")
        tab.dirty = False
        tab.load("ZT-02")


def test_calcul_compiles_nothing_and_affichage_compiles_the_draft_at_every_edit():
    """v0.117, the engineer's two views: in «Calcul» the result is Python's, instant, and no page is asked for; in «Affichage» the page of the draft -- saved or not -- is asked for at once and again at every edit. Until then the options and the page were folded sections of one pane, the page compiled only while open."""
    for pick in (_tab, _ctab):
        window, here = _window()
        with project.using(here):
            tab = pick(window)
            tab.dirty = False
            tab.load("ZT-02" if pick is _tab else "DR-02")
            asked = []
            tab.pane.request_snippet = lambda here_, mode, source, key: asked.append(source)
            tab.live = True
            tab.set_view("calc")
            tab.refresh()
            tab.n_spin.setValue(41.0)
            tab.refresh_timer.stop()
            tab.request_preview()
            assert asked == [], "«Calcul»: no request at all"
            tab.set_view("display")                     # «Affichage» compiles the draft
            tab.request_preview()
            assert asked and ("41 kN" in asked[-1] or '41, "kN"' in asked[-1]), asked[-1]   # the unfolded tension writes its literal (spec 2026-10-15)
            count = len(asked)
            tab.n_spin.setValue(42.0)                   # an edit asks again, a moment later
            tab.refresh_timer.stop()
            tab.request_preview()
            assert len(asked) > count and ("42 kN" in asked[-1] or '42, "kN"' in asked[-1])
            tab.set_view("calc")
            count = len(asked)
            tab.n_spin.setValue(43.0)
            tab.refresh_timer.stop()
            tab.request_preview()
            assert len(asked) == count, "back in «Calcul», nothing more is asked for"
            tab.pane.request_snippet = lambda *a, **k: None
            tab.dirty = False
            tab.live = False
            tab.load("ZT-02" if pick is _tab else "DR-02")


def test_calcul_shows_the_result_and_affichage_the_command_and_the_call():
    window, here = _window()
    from PySide6.QtWidgets import QGroupBox
    with project.using(here):
        tab = _ctab(window)
        work = [b.title() for b in tab.panes.right.widget(0).findChildren(QGroupBox) if b.property("card")]
        assert tab.t("mc_results") in work and tab.t("ds_call") not in work, work
        shown = [b.title() for b in tab.display.right.findChildren(QGroupBox) if b.property("card") and b.title()]
        order = [title for title in shown if title in (tab.t("ds_command"), tab.t("ds_call"))]
        assert order == [tab.t("ds_command"), tab.t("ds_call")], order


def test_a_tension_saved_is_unfolded_shows_a_value_imported_from_its_file_and_opens_in_formulas():
    """UI-003 (spec 2026-10-15): saving a tension writes its source through `member_check.write_source` and its domain Formules/<id>.typ; N changed to 30 kN in that file and imported in the «Formules» tab is what the «Traction» tab then shows; «Ouvrir dans Formules» brings that tab forward on the check's domain."""
    window, here = _window()   # calc/tools is on the path once the window is built: a tab's module is imported after it
    import formula_tab
    from domains import unfold
    with project.using(here):
        tab = _tab(window)
        tab.dirty = False
        tab.load("ZT-01")
        tab.save()
        path = unfold.domain_path(here, "ZT-01")   # Timber-checks/Tension/ laid out by folders (issue #64)
        try:
            assert path.is_file()
            path.write_text(path.read_text(encoding="utf-8").replace('"N_(t,d)", 25, "kN"', '"N_(t,d)", 30, "kN"'), encoding="utf-8")
            assert unfold.import_lines(here, "ZT-01", ["var:N_t_d"], lang="de")["imported"] == ["var:N_t_d"]
            tab.dirty = False
            tab.load("ZT-01")
            assert tab.n_spin.value() == 30.0
            assert tab.open_in_formulas() is True
            ftab = next(t for t in window.tabs if isinstance(t, formula_tab.FormulaTab))
            assert window.tab_widget.currentWidget() is ftab and ftab.current_id == "ZT-01"
        finally:
            src = json.loads((here.checks_dir / "ZT-01.json").read_text(encoding="utf-8"))
            src["N"] = {"value": 25, "unit": "kN"}
            (here.checks_dir / "ZT-01.json").write_text(json.dumps(src, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            path.unlink(missing_ok=True)
            base = unfold.read_base(here)
            base["domains"].pop("ZT-01", None)
            unfold.write_base(here, base)
            tab.dirty = False
            tab.load("ZT-01")


def test_a_domain_whose_form_no_longer_matches_its_check_says_so_in_red_in_the_formulas_tab():
    """Spec 2026-10-21-commandes-typst-refonte, UI-004 (REQ-012): after a regeneration that cannot apply -- the form a check's domain was written from no longer the check's -- the domain's tab says so at its head, in the theme's red, as the report prints it."""
    window, here = _window()   # calc/tools is on the path once the window is built: a tab's module is imported after it
    import formula_tab
    import theme
    from domains import unfold
    with project.using(here):
        tab = _tab(window)
        tab.dirty = False
        tab.load("ZT-01")
        tab.save()
        path = unfold.domain_path(here, "ZT-01")
        base = unfold.read_base(here)
        try:
            assert path.is_file() and "ZT-01" in base["domains"]
            base["domains"]["ZT-01"]["gen"] = dict(base["domains"]["ZT-01"]["gen"], form="(8)/(9)")   # written from another form: a regeneration that cannot apply
            unfold.write_base(here, base)
            assert tab.open_in_formulas() is True
            ftab = next(t for t in window.tabs if isinstance(t, formula_tab.FormulaTab))
            ftab.refresh_unfold()
            assert ftab.unfold_card.isVisibleTo(ftab), "the card of a domain Woodcore wrote out"
            head = ftab.unfold_head.text()
            assert ftab.t("fm_unfold_no_match") in head and theme.colour("danger") in head, head
        finally:
            path.unlink(missing_ok=True)
            base = unfold.read_base(here)
            base["domains"].pop("ZT-01", None)
            unfold.write_base(here, base)
            tab.dirty = False
            tab.load("ZT-01")


def test_the_shear_tab_offers_its_three_checks_in_a_list():
    """Spec 2026-10-21-commandes-typst-refonte, UI-005, REQ-021, Q-010: «Effort tranchant» chooses in a list what it checks -- the shear of 4.2.5.1, the shear-off of 4.2.6, the shear with a stress perpendicular to the grain of 4.2.7.1 --, each showing its own fields; a shear-off saved is exported calculable, its variant and its fields kept, and computed by Python."""
    window, here = _window()
    with project.using(here):
        from domains import member_check
        shear = _tab_of(window, "tab_mc_shear")
        assert [shear.variant_box.itemData(i) for i in range(shear.variant_box.count())] == list(member_check.SHEAR_VARIANTS)
        shear.new()
        _select(shear.position_box, "T001")
        shear.variant_box.setCurrentIndex(shear.variant_box.findData("shear-off"))
        assert shear.effort_form.isRowVisible(shear.f_off) and not shear.effort_form.isRowVisible(shear.pith_box) and not shear.effort_form.isRowVisible(shear.s90)
        shear.f_off.setValue(20.0)
        shear.l_off.setValue(200.0)
        draft = shear.draft()
        assert draft["variant"] == "shear-off" and draft["F"] == {"value": 20.0, "unit": "kN"} and draft["l"] == 200.0 and draft["w"] is None and draft["V_z"] is None, draft
        assert shear.save(), "a shear-off is saved"
        saved = shear.current_id
        exported = json.loads((here.data_dir / member_check.EXPORT_FILE).read_text(encoding="utf-8"))["checks"][saved]
        assert exported["calculable"] and exported["variant"] == "shear-off" and member_check.compute(exported)["equation"] in ("(26)", "(27)"), exported
        shear.variant_box.setCurrentIndex(shear.variant_box.findData("shear-perp"))
        assert shear.effort_form.isRowVisible(shear.s90) and not shear.effort_form.isRowVisible(shear.f_off)
        shear.dirty = False
        (here.checks_dir / ("%s.json" % saved)).unlink()
        member_check.export(here)
