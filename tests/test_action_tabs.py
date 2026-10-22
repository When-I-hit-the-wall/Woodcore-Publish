"""The six empty tabs of «Actions» and its two sections (calc/tools/action_tabs.py, chrome.SideNav's «section» row, woodcore_gui.NAV_SECTIONS; v0.117, docs/ui/window.md §10quater).

The engineer's request of 08.10.2026: «dans "Actions", il faut deux sections différentes: (1) Actions permanentes, (2) Actions variables» -- the first holding the tabs «Poids propre» and «Surcharge», the second «Charge utile», «Neige», «Vent» and «Séisme», all «vides pour l'instant».

What is held: the two sections are sub-titles of the group «Actions», placed before their first tab, «Charges» and «Combinaisons de charges» staying under them after a thin line (decision D-005); NAV_GROUPS keeps the shape a dozen tests read; the six tabs exist in the report alone, each with its icon, its name and what it will hold in the three languages, and none is built to calculate; a sub-title is hidden with its last row and with its group where that is folded, and is no row a key press can reach.

⚠️ Built off-screen; nothing here opens a menu or a dialog.
"""

TIER = "fast"  # tests/run_tests.py --fast

import os
import sys
from types import SimpleNamespace

import conftest
from conftest import ROOT

TOOLS = ROOT / "calc" / "tools"
# «Poids propre» and «Surcharge» are one tab since issue #35 (D-08): «Poids propre et surcharge»
SIX = ("tab_ac_selfweight", "tab_ac_imposed", "tab_ac_snow", "tab_ac_wind", "tab_ac_seismic")


def _qt():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def test_the_group_actions_holds_the_six_tabs_then_the_combinations_and_two_sections_stand_before_them():
    _qt()
    import woodcore_gui
    actions = dict(woodcore_gui.NAV_GROUPS)["nav_actions"]
    # «Charges» was retired into «Variables» in v0.117 (issue 13): «Combinaisons» alone follows the six
    assert actions == SIX + ("tab_combinations",), actions
    assert [key for key, _factory in woodcore_gui.TABS if key in SIX] == list(SIX), "in the order the group lists them"
    # the group's own sub-titles -- the «Acier» group has its two (issue #50) and is held by test_steel_tab
    assert {k: v for k, v in woodcore_gui.NAV_SECTIONS.items() if k in actions} == {"tab_ac_selfweight": "nav_permanent", "tab_ac_imposed": "nav_variable", "tab_combinations": ""}
    # the permanent actions are the first, the variable ones the next four, «Combinaisons» after a thin line
    sections = [key for key in actions if key in woodcore_gui.NAV_SECTIONS]
    assert sections == ["tab_ac_selfweight", "tab_ac_imposed", "tab_combinations"]
    assert actions.index("tab_ac_imposed") == 1 and actions.index("tab_combinations") == 5
    # the six are in the report alone: the convention d'utilisation and the base de projet are written from other things
    assert all(key in woodcore_gui.MODE_TABS["rs"] for key in SIX)
    assert not any(key in woodcore_gui.MODE_TABS["cu"] or key in woodcore_gui.MODE_TABS["bp"] for key in SIX)


def test_the_words_the_six_tabs_and_the_two_sections_are_in_three_languages_and_the_norms_own():
    _qt()
    import woodcore_gui
    import action_tabs
    for lang in ("fr", "de", "en"):
        words = woodcore_gui.STRINGS[lang]
        for key in SIX + ("nav_permanent", "nav_variable") + tuple(action_tabs.SOON.values()):
            assert words.get(key, "").strip(), (lang, key)
        names = [words[key] for key in SIX]
        assert len(set(names)) == len(SIX), (lang, names)
    # SIA 260:2013's own words for the two sections, and the engineer's for the six tabs (docs/decisions.md: the German ones are SIA 261's)
    assert [woodcore_gui.STRINGS["fr"][k] for k in ("nav_permanent", "nav_variable")] == ["Actions permanentes", "Actions variables"]
    assert [woodcore_gui.STRINGS["de"][k] for k in ("nav_permanent", "nav_variable")] == ["Ständige Einwirkungen", "Veränderliche Einwirkungen"]
    assert [woodcore_gui.STRINGS["fr"][k] for k in SIX] == ["Poids propre et surcharge", "Charge utile", "Neige", "Vent", "Séisme"]
    assert [woodcore_gui.STRINGS["de"][k] for k in SIX] == ["Eigen- und Auflasten", "Nutzlast", "Schnee", "Wind", "Erdbeben"]
    assert "ß" not in " ".join(woodcore_gui.STRINGS["de"][k] for k in SIX + ("nav_permanent", "nav_variable")), "Swiss German writes ss"
    import chrome
    for key in SIX:
        assert key in chrome.ICONS, f"{key} has no icon"


def test_each_of_the_six_tabs_opens_empty_with_its_name_and_what_it_will_hold():
    _qt()
    import woodcore_gui
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QLabel
    factories = dict(woodcore_gui.TABS)
    for lang in ("fr", "de", "en"):
        app = SimpleNamespace(t=lambda key, **v: woodcore_gui.STRINGS[lang][key].format(**v) if v else woodcore_gui.STRINGS[lang][key],
                              title_font=QFont(), bold_font=QFont())
        import action_tabs
        for key in [k for k in SIX if k in action_tabs.SOON]:     # the tabs still empty; the loads entered in Woodcore have their own tests (test_load_tab.py)
            tab = factories[key](app)
            texts = [label.text() for label in tab.findChildren(QLabel)]
            assert texts[0] == woodcore_gui.STRINGS[lang][key], (lang, key, texts)
            assert woodcore_gui.STRINGS[lang]["future"] in texts, (lang, key, "it says it is not built")
            assert any("Variables" in t or "Variablen" in t or "module" in t.lower() or "Modul" in t for t in texts[2:]), (lang, key, texts)
            assert not any("« Charges »" in t or "«Lasten»" in t or "«Loads»" in t for t in texts), (lang, key, "a tab retired in v0.117")
            assert tab.view_state() == {}, "nothing to keep"
            assert not hasattr(tab, "display") and not hasattr(tab, "save"), "no calculation is wired here"


def test_a_sub_title_stands_in_its_group_and_goes_with_its_last_row_and_its_group():
    _qt()
    import chrome
    from PySide6.QtCore import Qt
    groups = [("Actions", [(None, "Permanentes", None), (0, "Poids propre", "tab_statics"), (1, "Surcharge", "tab_statics"),
                           (None, "Variables", None), (2, "Neige", "tab_statics"),
                           (None, "", None), (3, "Combinaisons", "tab_combinations")]),
              ("Structure", [(4, "Modèles statiques", "tab_statics")])]
    nav = chrome.SideNav(groups)
    kinds = [nav.list.item(i).data(chrome.KIND) for i in range(nav.list.count())]
    assert kinds == ["group", "section", "entry", "entry", "section", "entry", "section", "entry", "group", "entry"], kinds
    assert nav.order() == [0, 1, 2, 3, 4], "a sub-title is no row: the keys count the tabs"
    sections = [nav.list.item(i) for i in range(nav.list.count()) if nav.list.item(i).data(chrome.KIND) == "section"]
    assert [s.text() for s in sections] == ["Permanentes", "Variables", ""]
    assert all(not (s.flags() & Qt.ItemFlag.ItemIsSelectable) for s in sections), "a sub-title is not chosen"
    # the document shows only the tab 2: the other sub-titles go with the rows they stood before
    nav.set_visible({2, 4})
    assert [s.isHidden() for s in sections] == [True, False, True]
    nav.set_visible({0, 2, 3, 4})
    assert [s.isHidden() for s in sections] == [False, False, False]
    # the group folded: its rows and its sub-titles are hidden together
    nav.toggle_group("Actions")
    assert all(s.isHidden() for s in sections)
    nav.toggle_group("Actions")
    assert not any(s.isHidden() for s in sections)
    # the navigation folded to its icons keeps the lines, and a sub-title with words is a thin line there too
    nav.set_collapsed(True)
    assert nav.delegate.sizeHint(None, nav.list.indexFromItem(sections[0])).height() == chrome.SECTION_LINE
    nav.set_collapsed(False)
    assert nav.delegate.sizeHint(None, nav.list.indexFromItem(sections[0])).height() == chrome.SECTION_HEIGHT
    assert nav.delegate.sizeHint(None, nav.list.indexFromItem(sections[2])).height() == chrome.SECTION_LINE, "no words, only a line"
