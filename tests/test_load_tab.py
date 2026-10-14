"""The tabs of loads entered in Woodcore (calc/tools/load_tab.py, issues #35-#37, spec docs/requirements/completed/2026-10-10-issues-github-35-a-39.md).

What is held: «Poids propre et surcharge» is one tab (D-08) that lists its build-ups, edits the layers in a table -- each g_k or a_k, a library and a material, a thickness, battens at a spacing, a layer beside another --, shows at once the sums and the drawing, saves the source and exports calculations.json with the case under the domain dead-load (UI-001, UI-002, REQ-002); the project's library is edited in its own card and offered at once to the layers (D-07).

⚠️ Built off-screen; nothing here opens a dialog.
"""

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
        assert (here.data_dir / instance["figures"][0]["file"]).is_file()
        import display_view
        assert display_view.entry_call(tab.display_entries()[0]) == '#show-calc("dead-load", "%s")' % cid
        # the project's library, edited here and offered at once
        tab.add_project_material()
        tab.project_table.item(tab.project_table.rowCount() - 1, 1).setText("Hersteller OSB")
        assert tab.save_project_library()
        _select(cell(0, 1), "project")
        assert any(cell(0, 2).itemData(i)[0] == "M1" for i in range(cell(0, 2).count()))
        tab.dirty = False


def test_the_snow_tab_offers_the_roofs_of_figur_3_computes_at_once_and_saves():
    """UI-004 (issue #36): the site, the exposure, the roof form -- its fields shown for its form alone --, the sliding; the loads and the sketch at once; saved and exported under snow-load."""
    window, here = _window()
    with project.using(here):
        import load_tab
        from domains import snow_source
        tab = _tab(window, "tab_ac_snow")
        assert isinstance(tab, load_tab.SnowTab)
        tab.dirty = False
        tab.new()
        tab.h0_spin.setValue(638)
        _select(tab.roof_box, "curved")
        assert tab.roof_form.isRowVisible(tab.row_of(tab.alpha1_spin)) and not tab.roof_form.isRowVisible(tab.row_of(tab.alpha2_spin)) and not tab.roof_form.isRowVisible(tab.row_of(tab.length_spin))
        tab.alpha1_spin.setValue(10)
        assert tab.instance and tab.instance["results"] == ["q_k1", "q_k3", "q_k3h"], tab.reason
        # a gable roof: both pitches shown, model 1 on each slope and model 2's halves
        _select(tab.roof_box, "duo")
        assert tab.roof_form.isRowVisible(tab.row_of(tab.alpha1_spin)) and tab.roof_form.isRowVisible(tab.row_of(tab.alpha2_spin))
        tab.alpha1_spin.setValue(20)
        tab.alpha2_spin.setValue(40)
        v = tab.instance["vars"]
        assert tab.instance["results"] == ["q_k11", "q_k12", "q_k11h", "q_k12h"], tab.reason
        assert v["q_k11"]["value"] > v["q_k12"]["value"] > 0, "the steeper slope carries less (Figur 2)"
        _select(tab.roof_box, "flat")
        assert tab.roof_form.isRowVisible(tab.row_of(tab.length_spin)) and not tab.roof_form.isRowVisible(tab.row_of(tab.alpha1_spin))
        tab.length_spin.setValue(24)
        tab.width_spin.setValue(22)
        assert abs(tab.instance["vars"]["mu_1"]["value"] - 0.96) < 1e-12
        assert tab.save(), tab.reason
        cid = tab.current_id
        source = json.loads((here.sources_dir / snow_source.FOLDER / ("%s.json" % cid)).read_text(encoding="utf-8"))
        assert source["roof"] == "flat" and source["alpha_1"] is None and source["length"] == 24
        exported = json.loads((here.data_dir / "calculations.json").read_text(encoding="utf-8"))
        assert exported["domains"]["snow-load"]["instances"][cid]["source_file"] == "loads/snow/%s.json" % cid
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


def _choices(tab):
    entry = tab.display_entries()[0]
    assert entry.command == "show-calc" and not entry.call, "the command's panel, not a call written out"
    return [key for key, _words, _math in entry.context["shown"]]


def test_the_three_load_tabs_offer_the_manual_selection_of_show_calc():
    """Issues #56, #57 (spec 2026-10-14-neige-vent-affichage-altitude, REQ-001, ARCH-002, D-05): «Affichage» of the three load tabs is show-calc's panel -- its level, -1 «Sélection manuelle» among them -- with every var, table and drawing of the case as the export holds it; nothing before the first save; the snow offers no drawing (D-02). The call with `level: -1, shown:` is written as the other tabs write it."""
    window, here = _window()
    with project.using(here):
        import display_options
        import display_view
        assert display_options.SPECS["show-calc"].options[0].kind == "detail"
        for key, domain in (("tab_ac_selfweight", "dead-load"), ("tab_ac_snow", "snow-load"), ("tab_ac_wind", "wind-load")):
            tab = _tab(window, key)
            tab.dirty = False
            tab.new()
            if key == "tab_ac_wind":
                _select(tab.table_box, "45")
                tab.h_spin.setValue(9)
            assert _choices(tab) == [], "a case not exported has nothing to tick yet"
            assert tab.save(), tab.reason
            cid = tab.current_id
            exported = json.loads((here.data_dir / "calculations.json").read_text(encoding="utf-8"))["domains"][domain]["instances"][cid]
            keys = _choices(tab)
            assert keys[:len(exported["vars"])] == list(exported["vars"]), (key, keys)
            assert ("figure-1" in keys) == (key == "tab_ac_selfweight"), (key, keys)
            entry = tab.display_entries()[0]
            assert entry.positional == (domain, cid)
            call = display_view.entry_call(entry, {"level": -1, "shown": {keys[0]: 2}})
            assert call.startswith('#show-calc("%s", "%s"' % (domain, cid)) and "level: -1" in call and "shown:" in call, call
            tab.dirty = False


def test_the_snow_tab_warns_above_the_limit_and_keeps_its_sketch():
    """Issue #56 (REQ-003, REQ-004, UI-001, D-03, D-04): a site above 5.1.4's limit is computed and said in the tab's callout -- the limit read from the norm file --, a site below it says nothing; the sketch stays in «Calcul» and no svg of the snow is written by the export."""
    window, here = _window()
    with project.using(here):
        from norms import sia261_snow
        tab = _tab(window, "tab_ac_snow")
        tab.dirty = False
        tab.new()
        tab.h0_spin.setValue(1900)
        assert tab.instance and not tab.warning and not tab.message.isVisibleTo(tab), tab.reason
        tab.h0_spin.setValue(2100)
        assert tab.instance and tab.instance["vars"]["h_0"]["value"] == 2100, tab.reason
        limit = sia261_snow.clause()["max_altitude"]
        assert tab.warning == tab.t("ld_warn_above_limit", h_0="2100", limit="%g" % limit["value"], ref=limit["norm_ref"])
        assert tab.message.isVisibleTo(tab) and "2100" in tab.message.text()
        assert tab.figure_card.isVisibleTo(tab) and "<svg" in tab.drawing
        assert tab.save(), tab.reason
        assert not list((here.data_dir / "calculations").glob("snow-load-*.svg"))
        exported = json.loads((here.data_dir / "calculations.json").read_text(encoding="utf-8"))
        instance = exported["domains"]["snow-load"]["instances"][tab.current_id]
        assert "figures" not in instance and "5.1.4" not in json.dumps(instance, ensure_ascii=False)
        tab.dirty = False


def test_the_load_tab_words_exist_in_the_three_languages():
    """ARCH-RISK-004 of spec 2026-10-14-neige-vent-affichage-altitude: tests/test_i18n.py does not read load_tab.STRINGS, so the three languages are held equal here."""
    _qt()
    import load_tab
    assert set(load_tab.STRINGS["fr"]) == set(load_tab.STRINGS["de"]) == set(load_tab.STRINGS["en"])
    for lang in ("fr", "de", "en"):
        text = load_tab.STRINGS[lang]["ld_warn_above_limit"]
        assert "{h_0}" in text and "{limit}" in text and "{ref}" in text and "2000" not in text
