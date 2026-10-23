"""The tabs of loads entered in Woodcore (calc/tools/load_tab.py, issues #35-#37, spec docs/requirements/completed/2026-10-10-issues-github-35-a-39.md).

What is held: «Poids propre et surcharge» is one tab (D-08) that lists its build-ups, edits the layers in a table -- each g_k or a_k, a library and a material, a thickness, battens at a spacing, a layer beside another --, shows at once the sums and the drawing, saves the source and exports calculations.json with the case under the domain dead-load (UI-001, UI-002, REQ-002); the project's library is edited in its own card and offered at once to the layers (D-07).

⚠️ Built off-screen; nothing here opens a dialog.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import os
import sys

import conftest
from conftest import ROOT

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
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _window():
    if "window" not in _STATE:
        _qt()
        here = conftest.project_copy("load_tab")
        with project.using(here):
            import woodcore_gui
            window = woodcore_gui.MainWindow()
            window.mode = "rs"
            window.apply_mode()
        _STATE.update(window=window, here=here)
    return _STATE["window"], _STATE["here"]


def _tab(window, key):
    return next(t for t in window.tabs if getattr(t, "KEY", None) == key)


def _select(combo, data):
    index = combo.findData(data)
    assert index >= 0, (data, [combo.itemData(i) for i in range(combo.count())])
    combo.setCurrentIndex(index)


def test_the_dead_load_tab_edits_layers_shows_the_sums_and_the_drawing_and_saves_and_exports():
    window, here = _window()
    with project.using(here):
        import load_tab
        from domains import dead_load_source
        tab = _tab(window, "tab_ac_selfweight")
        assert isinstance(tab, load_tab.DeadLoadTab)
        tab.dirty = False
        tab.new()
        tab.identity.name.setText("Flachdach Test")
        assert tab.table.rowCount() == 1
        tab.add_layer()
        tab.add_layer()
        assert tab.table.rowCount() == 3
        # layer 2: rafters 60/200 at 625, layer 3: insulation beside them, from the workbook's library
        cell = lambda r, c: tab.table.cellWidget(r, c)
        cell(1, 3).setValue(200)
        cell(1, 4).setValue(60)
        cell(1, 5).setValue(625)
        _select(cell(2, 1), "belastungsannahmen")
        combo = cell(2, 2)
        combo.setCurrentIndex(next(i for i in range(combo.count()) if combo.itemData(i) == ("Flumroc Typ 1", "Dämmung")))
        cell(2, 3).setValue(200)
        cell(2, 6).setChecked(True)
        assert tab.instance is not None, tab.reason
        sums = tab.instance["vars"]
        gk_before, ak_before = sums["gk"]["value"], sums["ak"]["value"]
        assert gk_before > 0 and ak_before == 0
        assert tab.figure_card.isVisibleTo(tab) and "60" in tab.instance["_files"][next(iter(tab.instance["_files"]))]
        # REQ-002: the insulation moved to a_k
        _select(cell(2, 0), "ak")
        assert tab.instance["vars"]["ak"]["value"] > 0 and tab.instance["vars"]["gk"]["value"] < gk_before
        assert "g_k" in tab.results_label.text() or "g" in tab.results_label.text()
        assert tab.save(), tab.reason
        cid = tab.current_id
        source = json.loads((here.sources_dir / dead_load_source.FOLDER / ("%s.json" % cid)).read_text(encoding="utf-8"))
        assert [l["kind"] for l in source["layers"]] == ["gk", "gk", "ak"] and source["layers"][2]["beside"] is True
        assert source["layers"][1]["spacing"] == 625 and source["name"] == "Flachdach Test"
        exported = json.loads((here.data_dir / "calculations.json").read_text(encoding="utf-8"))
        instance = exported["domains"]["dead-load"]["instances"][cid]
        assert instance["source_file"] == "loads/dead/%s.json" % cid and instance["figures"]
        assert conftest.figure(here, instance["figures"][0]["file"]).is_file()
        import display_view
        assert display_view.entry_call(tab.display_entries()[0]) == '#include domain-file("dead-load", "%s")' % cid
        # the project's library, edited here and offered at once
        tab.add_project_material()
        tab.project_table.item(tab.project_table.rowCount() - 1, 1).setText("Hersteller OSB")
        assert tab.save_project_library()
        _select(cell(0, 1), "project")
        assert any(cell(0, 2).itemData(i)[0] == "M1" for i in range(cell(0, 2).count()))
        tab.dirty = False


def test_the_snow_tab_is_drawn_from_its_declaration_computes_at_once_and_saves():
    """UI-004 (issue #36), rebuilt on the calculation tabs' base (spec 2026-10-22-onglet-neige-type, ARCH-002, REQ-005, REQ-007): the building first and always, the site, the roof among five tiles -- its slopes shown for its form alone --, the sliding; the loads at once; saved and exported under snow-load, the building's length and width kept whatever the roof."""
    window, here = _window()
    with project.using(here):
        import calc_tab
        import snow_tab
        from domains import snow_source
        tab = _tab(window, "tab_ac_snow")
        assert isinstance(tab, snow_tab.SnowTab) and isinstance(tab, calc_tab.DeclaredTabMixin)
        tab.dirty = False
        tab.new()
        f = tab.fields

        def shown(key):
            form, widget = tab.rows[key]
            return form.isRowVisible(widget)
        f["h_0"].spin.setValue(638)
        f["roof"].buttons["curved"].click()
        assert shown("alpha_1") and not shown("alpha_2") and shown("length") and shown("width"), "the building is always entered (T37)"
        f["alpha_1"].spin.setValue(10)
        assert tab.instance and tab.instance["results"] == ["q_k1", "q_k3", "q_k3h"], tab.messages_
        # a gable roof: both pitches shown, model 1 on each slope and model 2's halves
        f["roof"].buttons["duo"].click()
        assert shown("alpha_1") and shown("alpha_2")
        f["alpha_1"].spin.setValue(20)
        f["alpha_2"].spin.setValue(40)
        v = tab.instance["vars"]
        assert tab.instance["results"] == ["q_k11", "q_k12", "q_k11h", "q_k12h"], tab.messages_
        assert v["q_k11"]["value"] > v["q_k12"]["value"] > 0, "the steeper slope carries less (Figur 2)"
        f["roof"].buttons["flat"].click()
        assert not shown("alpha_1") and shown("length")
        f["length"].spin.setValue(24)
        f["width"].spin.setValue(22)
        assert abs(tab.instance["vars"]["mu_1"]["value"] - 0.96) < 1e-12
        assert [m.code for m in tab.messages_] == ["large_flat"], tab.messages_
        assert tab.save(), tab.messages_
        cid = tab.current_id
        source = json.loads((here.sources_dir / snow_source.FOLDER / ("%s.json" % cid)).read_text(encoding="utf-8"))
        assert source["roof"] == "flat" and source["length"] == 24 and source["width"] == 22 and source["schema_version"] == "1.0"
        exported = json.loads((here.data_dir / "calculations.json").read_text(encoding="utf-8"))
        instance = exported["domains"]["snow-load"]["instances"][cid]
        assert instance["source_file"] == "loads/snow/%s.json" % cid and instance["figures"][0]["file"].endswith("%s-fig3.svg" % cid)
        tab.dirty = False


def test_a_free_c_e_is_written_at_1_3_and_said_by_no_message():
    """REQ-006, REQ-021, D-10: the three buttons of C_e say what they are worth, and a value typed beside them is the case's C_e -- no message, the source written at 1.3."""
    window, here = _window()
    with project.using(here):
        from domains import snow_source
        tab = _tab(window, "tab_ac_snow")
        tab.dirty = False
        tab.new()
        exposure = tab.fields["exposure"]
        assert [b.text() for b in exposure.buttons.values()] == [tab.t("sn_c_exposure_" + w) + " " + n for w, n in (("sheltered", "1.2"), ("normal", "1"), ("exposed", "0.8"))]   # «abrité 1.2» (T38)
        exposure.free.setValue(0.95)
        assert tab.draft()["exposure"] == "custom" and tab.draft()["c_e"] == 0.95
        assert tab.instance["vars"]["ce"]["value"] == 0.95 and not [m for m in tab.messages_ if m.field in ("exposure", "c_e")]
        assert tab.save()
        source = json.loads((here.sources_dir / snow_source.FOLDER / ("%s.json" % tab.current_id)).read_text(encoding="utf-8"))
        assert source["schema_version"] == "1.3" and source["c_e"] == 0.95
        exposure.buttons["sheltered"].click()
        assert tab.draft()["exposure"] == "sheltered" and "c_e" not in tab.draft()
        tab.dirty = False


def test_the_wind_tab_offers_every_building_table_computes_at_once_and_saves():
    """UI-005 (issue #37): q_p0, the terrain, b, d, h, z, the table of Annexe C -- all 37 buildings offered (D-06) --, c_d; q_p and the forces at once, their tables shown; saved and exported under wind-load."""
    window, here = _window()
    with project.using(here):
        import load_tab
        from domains import wind_source
        from norms import sia261_wind
        tab = _tab(window, "tab_ac_wind")
        assert isinstance(tab, load_tab.WindTab)
        assert [tab.table_box.itemData(i) for i in range(tab.table_box.count())] == list(sia261_wind.NUMBERS)
        tab.dirty = False
        tab.new()
        _select(tab.table_box, "45")
        tab.h_spin.setValue(9)
        assert tab.instance and tab.instance["vars"]["qp"]["value"] > 0, tab.reason
        assert "qk_max_cf1" in tab.instance["vars"] and "<table" in tab.results_label.text()
        assert tab.save(), tab.reason
        cid = tab.current_id
        source = json.loads((here.sources_dir / wind_source.FOLDER / ("%s.json" % cid)).read_text(encoding="utf-8"))
        assert source["table"] == "45" and source["h"] == 9 and source["z"] is None
        exported = json.loads((here.data_dir / "calculations.json").read_text(encoding="utf-8"))
        assert exported["domains"]["wind-load"]["instances"][cid]["source_file"] == "loads/wind/%s.json" % cid
        tab.dirty = False


def test_the_snow_tabs_state_says_red_orange_and_green_and_a_click_takes_to_the_field():
    """REQ-008 (D-19): above 2000 m an orange message, the calculation made -- its words without «calculé quand même» --; above 800 m the cornice; a C_T of 0 a red one naming its field, no result; every input there, the green line. A click on a message gives its field the focus and makes it flash."""
    window, here = _window()
    with project.using(here):
        from norms import sia261_snow
        tab = _tab(window, "tab_ac_snow")
        tab.dirty = False
        tab.new()
        state = tab.pane.modules["state"].body
        tab.fields["h_0"].spin.setValue(700)
        assert tab.instance and [r.text() for r in state.rows] == ["✓ " + tab.t("ct_complete")]
        tab.fields["h_0"].spin.setValue(2100)
        assert tab.instance and tab.instance["vars"]["h_0"]["value"] == 2100
        limit = sia261_snow.clause()["max_altitude"]
        said = tab.t("sn_msg_above_limit", h_0="2100", limit="%g" % limit["value"], ref=limit["norm_ref"])
        assert [r.text() for r in state.rows] == ["✓ " + tab.t("ct_complete"), said] and state.rows[1].property("callout") == "warning"
        tab.fields["h_0"].spin.setValue(850)
        assert "5.3.7" in state.rows[1].text()
        tab.fields["c_t"].spin.setValue(0)
        assert tab.instance is None and state.rows[0].property("callout") == "danger" and [m.field for m in tab.messages_ if m.severity == "error"] == ["c_t"]
        state.rows[0].mousePressEvent(None)
        assert tab.fields["c_t"].blinking
        assert "<svg" in (tab.drawing or "<svg"), "the drawing of a case that cannot be computed is the last one's or none"
        tab.fields["c_t"].spin.setValue(1)
        assert tab.instance and "<svg" in tab.drawing
        tab.dirty = False


def test_supprimer_archives_the_case_and_leaves_no_draft_that_saves_itself():
    """Issue #97: a snow case deleted is listed under «Archives», and what the form shows next is a draft nobody asked for -- no dot, never saved by itself: the draft «Nouveau» opened with its dot was saved without a word as soon as the engineer looked elsewhere (`SN-01.json`, empty), and «Supprimer» on it opened another one, so the tab could never be emptied."""
    window, here = _window()
    from PySide6.QtWidgets import QMessageBox
    import autosave
    original = QMessageBox.__dict__["question"]
    QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
    try:
        with project.using(here):
            from domains import snow_source
            tab = _tab(window, "tab_ac_snow")
            folder = here.sources_dir / snow_source.FOLDER
            tab.dirty = False
            tab.new()
            tab.identity.id.setText("Neige_97")
            assert tab.save(), tab.messages_
            before = sorted(p.name for p in folder.glob("*.json"))
            tab.list.select("Neige_97")
            tab.delete()
            assert not (folder / "Neige_97.json").exists()
            archived = [e for e in tab.list.archived_ids() if e.endswith("-Neige_97.json")]
            assert archived, ("the case deleted is not listed under «Archives»", tab.list.archived_ids())
            assert tab.current_id is None and not tab.dirty, "the form after «Supprimer» holds a draft marked unsaved"
            assert autosave.leave(window, tab, "replace") and autosave.leave(window, tab, "close")
            assert sorted(p.name for p in folder.glob("*.json")) == [n for n in before if n != "Neige_97.json"], "a draft nobody asked for was saved"
            tab.delete()    # «Supprimer» on that draft: nothing saved, nothing archived, still no dot
            assert not tab.dirty and sorted(p.name for p in folder.glob("*.json")) == [n for n in before if n != "Neige_97.json"]
    finally:
        QMessageBox.question = original
        tab.dirty = False


def test_the_load_tab_words_exist_in_the_three_languages():
    """ARCH-RISK-004 of spec 2026-10-14-neige-vent-affichage-altitude: tests/test_i18n.py does not read load_tab.STRINGS, so the three languages are held equal here -- the snow's own since the spec 2026-10-22-onglet-neige-type (snow_tab_words, calc_tab_words), the 2000 m read from the norm file and said without «calculé quand même» (T50)."""
    _qt()
    import calc_tab_words
    import load_tab
    import snow_tab_words
    for module in (load_tab, calc_tab_words, snow_tab_words):
        assert set(module.STRINGS["fr"]) == set(module.STRINGS["de"]) == set(module.STRINGS["en"]), module.__name__
    for lang in ("fr", "de", "en"):
        text = snow_tab_words.STRINGS[lang]["sn_msg_above_limit"]
        assert "{h_0}" in text and "{limit}" in text and "{ref}" in text and "2000" not in text
        assert "quand même" not in text and "trotzdem" not in text and "all the same" not in text
