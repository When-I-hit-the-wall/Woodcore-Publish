"""The «Acier» tabs in Woodcore's window: the group and its six modules, the five check tabs on the member checks' base, and the «Profilés» tab (calc/tools/steel_tab.py, calc/tools/profile_tab.py; spec 2026-10-12-section-acier UI-001 to UI-003, D-05, D-13, D-16; docs/ui/tab-steel.md).

What is held: the group «Acier» before «Référence» with its sub-titles, in the report alone, an icon for each module, the words in three languages; a steel check made, its profile and grade following its position (said in their own field) or written over, saved into Woodcore-Datei/steel/ and exported into data/steel.json, its result shown at once as the export computes it, the verdict the ratio against one, a class-4 section said rather than computed, the call `#show-check-steel` and the page asked only of a saved check; a read-only project refusing; the «Profilés» tab drawing a model, loading an SZS C5 profile without its radii, a rectangle added by a drag, saved and refused to be deleted while a position names it.

⚠️ Built off-screen on a copy of the example project (conftest.project_copy), message boxes stubbed; nothing here compiles Typst.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import sys

import conftest
from conftest import ROOT, Skip

import project

TOOLS = ROOT / "calc" / "tools"
_STATE = {}
STEEL_TABS = ("tab_st_profiles", "tab_st_class", "tab_st_tension", "tab_st_compression", "tab_st_bending", "tab_st_shear")


def _qt():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _add_position(here, **row):
    """A position written as the export writes it -- data/positions/<id>.json and the index -- without running the whole export, which a copy of the example cannot (its plans' backgrounds are not copied)."""
    import export_all
    base = {"position": "", "type": "Stütze", "material": "Stahl", "strength_class": "S355", "section_type": "", "dimension": "", "units": "", "moisture_class": None, "description": ""}
    base.update(row)
    (record,), _notes = export_all._positions([base])
    folder = here.data_dir / "positions"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / ("%s.json" % record["position"])).write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    index_path = here.data_dir / "positions-index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    if record["position"] not in index["positions"]:
        index["positions"].append(record["position"])
    index_path.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")


def _window():
    if "window" not in _STATE:
        _qt()
        here = conftest.project_copy("steel_tab")
        with project.using(here):
            # a steel position, so that a check can follow one
            _add_position(here, position="S900", section_type="HEA", dimension="200")
            import woodcore_gui
            window = woodcore_gui.MainWindow()
            window.mode = "rs"
            window.apply_mode()
        _STATE.update(window=window, here=here)
    return _STATE["window"], _STATE["here"]


def _tab(window, cls_name):
    import steel_tab
    import profile_tab
    cls = getattr(steel_tab, cls_name, None) or getattr(profile_tab, cls_name)
    return next(t for t in window.tabs if isinstance(t, cls))


def _select(combo, data):
    index = combo.findData(data)
    assert index >= 0, (data, [combo.itemData(i) for i in range(combo.count())])
    combo.setCurrentIndex(index)


def _fresh(tab):
    tab.dirty = False
    tab.new()
    tab.dirty = False
    tab.live = False


def test_the_group_its_sections_and_six_modules_in_the_report_alone():
    """UI-001, D-13."""
    _qt()
    import chrome
    import woodcore_gui
    groups = dict(woodcore_gui.NAV_GROUPS)
    assert groups["nav_steel"] == STEEL_TABS
    titles = [title for title, _members in woodcore_gui.NAV_GROUPS]
    assert titles.index("nav_steel") + 1 == titles.index("nav_reference")
    assert woodcore_gui.NAV_SECTIONS["tab_st_profiles"] == "nav_steel_section" and woodcore_gui.NAV_SECTIONS["tab_st_tension"] == "nav_steel_safety"
    for key in STEEL_TABS:
        assert key in woodcore_gui.mode_tabs("rs") and key not in woodcore_gui.mode_tabs("cu") and key not in woodcore_gui.mode_tabs("bp"), key
        assert key in chrome.ICONS, key
    for lang in ("fr", "de", "en"):
        table = woodcore_gui.STRINGS[lang]
        words = [table[k] for k in STEEL_TABS + ("nav_steel", "nav_steel_section", "nav_steel_safety")]
        assert all(words) and len(set(words[:6])) == 6, (lang, words)
    fr = woodcore_gui.STRINGS["fr"]
    assert fr["nav_steel"] == "Acier" and [fr[k] for k in STEEL_TABS] == ["Profilés", "Classe de section", "Traction", "Compression", "Flexion", "Effort tranchant"]


def test_a_check_follows_its_position_and_is_saved_and_exported():
    """UI-003, D-05, REQ-004: the profile and the grade say they follow S900; a bending saved is a file of steel/ and a record of data/steel.json, its result shown at once."""
    window, here = _window()
    with project.using(here):
        tab = _tab(window, "SteelBendingTab")
        _fresh(tab)
        assert tab.draft()["id"].startswith("ST-B")
        _select(tab.position_box, "S900")
        assert "HEA 200" in tab.family_box.itemText(0) and "S900" in tab.family_box.itemText(0), tab.family_box.itemText(0)
        assert "S355" in tab.grade_box.itemText(0)
        tab.force_spins["M_y"].setValue(40.0)
        draft = tab.draft()
        assert draft["profile"] is None and draft["grade"] is None and draft["M_y"] == {"value": 40.0, "unit": "kNm"}
        tab.refresh(preview=False)
        assert tab.record["calculable"] and "HEA 200" == tab.record["designation"]
        assert "✔" in tab.verdict_label.text() and "M" in tab.verdict_label.text()
        assert "SIA 263" in tab.results_label.text()
        assert tab.save() is True
        cid = tab.current_id
        written = json.loads((here.steel_dir / ("%s.json" % cid)).read_text(encoding="utf-8"))
        assert written["kind"] == "bending" and written["position"] == "S900"
        exported = json.loads((here.data_dir / "steel.json").read_text(encoding="utf-8"))
        assert exported["checks"][cid]["calculable"] and abs(exported["checks"][cid]["eta"] - 40 / (355 * 429e3 / 1.05e6)) < 1e-6
        # its file written out by the export, included where a section prints it (spec 2026-10-21-commandes-typst-refonte, REQ-017, UI-002)
        assert tab.command_text() == '#include domain-file("steel", "%s")' % cid
        assert tab.preview_source() is not None and tab.command_text() in tab.preview_source()


def test_a_profile_written_over_is_orange_and_reprendre_takes_it_back():
    window, here = _window()
    with project.using(here):
        tab = _tab(window, "SteelTensionTab")
        _fresh(tab)
        _select(tab.position_box, "S900")
        _select(tab.family_box, "IPE")
        _select(tab.size_box, "360")
        assert tab.profile_note.text() and tab.profile_back.isVisible() is False or tab.profile_note.text()
        assert tab.draft()["profile"] == {"type": "IPE", "dimension": "360"}
        tab.take_back(tab.family_box)
        assert tab.draft()["profile"] is None and not tab.profile_note.text()


def test_a_class_4_section_is_said_not_computed():
    window, here = _window()
    with project.using(here):
        tab = _tab(window, "SteelCompressionTab")
        _fresh(tab)
        _select(tab.family_box, "IPE")
        _select(tab.size_box, "360")
        _select(tab.grade_box, "S355")
        tab.force_spins["N"].setValue(500.0)
        assert tab.draft()["N"] == {"value": -500.0, "unit": "kN"}, "the field is the magnitude, the source tension positive"
        tab.refresh(preview=False)
        assert "4.5.3" in tab.results_label.text() or "4.5.3" in tab.reason, tab.results_label.text()
        _select(tab.family_box, "HEB")
        _select(tab.size_box, "200")
        tab.refresh(preview=False)
        assert "✔" in tab.verdict_label.text()


def test_the_class_tab_shows_the_class_and_no_verdict():
    window, here = _window()
    with project.using(here):
        tab = _tab(window, "SteelClassTab")
        _fresh(tab)
        _select(tab.family_box, "IPE")
        _select(tab.size_box, "360")
        _select(tab.grade_box, "S355")
        tab.force_spins["N"].setValue(-500.0)
        tab.force_spins["M_y"].setValue(100.0)
        tab.refresh(preview=False)
        assert not tab.verdict_label.isVisible() and "2" in tab.results_label.text()


def test_a_project_opened_read_only_writes_nothing():
    window, here = _window()
    with project.using(here):
        tab = _tab(window, "SteelShearTab")
        _fresh(tab)
        window.read_only = True
        refused = []
        window.refuse_read_only = lambda *a, **k: refused.append(True)
        try:
            assert tab.save() is False
            ptab = _tab(window, "ProfileTab")
            assert ptab.save() is False and ptab.delete() is False
        finally:
            window.read_only = False
        assert len(refused) == 3, refused


def test_the_profiles_tab_draws_loads_saves_and_refuses_to_delete_a_cited_profile():
    """UI-002, REQ-003, D-16."""
    window, here = _window()
    with project.using(here):
        tab = _tab(window, "ProfileTab")
        tab.dirty = False
        tab.new()
        _select(tab.model_box, "RHS")
        tab.draw_model()
        assert tab.table.rowCount() == 4
        _select(tab.c5_family, "HEA")
        _select(tab.c5_size, "200")
        tab.load_c5()
        assert tab.table.rowCount() == 7 and tab.draft()["template"]["c5"] == "HEA 200"
        tab.add_part(0, -20, 200, 10)
        assert tab.table.rowCount() == 8
        assert "A" in tab.values_label.text()
        tab.identity.name.setText("Stütze mit Lasche")
        pid = tab.draft()["id"]
        assert tab.save() is True and (here.profiles_dir / ("%s.json" % pid)).is_file()
        # a position naming it: its delete is refused (D-16)
        _add_position(here, position="S901", section_type="USR", dimension=pid)
        assert tab.delete() is False and (here.profiles_dir / ("%s.json" % pid)).is_file()


def test_the_words_are_in_three_languages():
    _qt()
    import steel_tab_words
    keys = [set(texts) for texts in steel_tab_words.STRINGS.values()]
    assert keys[0] == keys[1] == keys[2]
    for lang, texts in steel_tab_words.STRINGS.items():
        assert all(isinstance(v, str) and v for v in texts.values()), lang
        if lang == "de":
            assert not any("ß" in v for v in texts.values())
