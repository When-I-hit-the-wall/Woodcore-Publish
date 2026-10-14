"""The window's frame after the website's (calc/tools/chrome.py, woodcore_gui.py, home_page.py; v0.91, docs/ui/window.md §10quater).

The row of tabs gave way to a grouped side navigation -- the QTabWidget stays underneath, its bar hidden, so a module is still a tab -- the top bar names the project as the site names itself and shows a forced level or language as a chip, the language is the site's segmented switch, and the start page sets what there is to start with and the recent projects as cards.

What is held here: every module in one group and one row, the row and the tab kept in step both ways, the dot of unsaved changes on the row as on the tab, the navigation folded and unfolded and remembered, Ctrl+1 … Ctrl+9, the chip saying what the next PDF carries and nothing while it carries nothing forced, the language switch answering the combo box's interface it replaced, and the start page's three cards each doing what its button did.

⚠️ Built off-screen; nothing here opens a menu or a dialog, a modal off-screen never coming back.
"""

import os
import sys

import conftest
from conftest import ROOT

TOOLS = ROOT / "calc" / "tools"
_WINDOW = {}


def _qt():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _window():
    if "window" not in _WINDOW:
        _qt()
        conftest.exported("calculations.json")
        import woodcore_gui
        _WINDOW["window"] = woodcore_gui.MainWindow()
    return _WINDOW["window"]


def _clean(window):
    for tab in window.tabs:
        if hasattr(tab, "dirty"):
            tab.dirty = False
    window.update_tab_marks()


def test_every_module_is_in_one_group_and_every_group_has_its_words():
    _qt()
    import woodcore_gui
    keys = [key for key, _factory in woodcore_gui.TABS]
    grouped = [key for _title, members in woodcore_gui.NAV_GROUPS for key in members]
    assert sorted(grouped) == sorted(keys) and len(grouped) == len(set(grouped)), (keys, grouped)
    # «mets "Schémas" sous "Structure", visuellement en-dessous de "Modèles statiques"» (v0.94) -- an order between two rows and not a fixed position, so that a module added to the group later does not make it false. (The RFEM tab stood above the static models until it was retired in 0.117.)
    structure = dict(woodcore_gui.NAV_GROUPS)["nav_structure"]
    assert structure.index("tab_statics") + 1 == structure.index("tab_schema"), woodcore_gui.NAV_GROUPS
    for lang in ("fr", "de", "en"):
        titles = [woodcore_gui.STRINGS[lang][title] for title, _members in woodcore_gui.NAV_GROUPS]
        assert len(set(titles)) == len(titles) and all(titles), (lang, titles)
    import chrome
    assert set(keys) <= set(chrome.ICONS), "a module without its icon"


def test_the_navigation_and_the_tabs_move_together():
    window = _window()
    nav = window.nav
    assert not window.tab_widget.tabBar().isVisible() and window.tab_widget.tabBar().isHidden(), "the row of tabs is the navigation's now"
    order = nav.order()
    # the rows, and so Ctrl+1 … Ctrl+9, in the order NAV_GROUPS lists the modules: «Schémas» right under «Modèles statiques» (v0.94) -- the modules the document shown shows, which is every one but «Sections» for the report (MODE_TABS; this window is on it)
    import woodcore_gui
    by_key = {key: index for index, (key, _factory) in enumerate(woodcore_gui.TABS)}
    shown = woodcore_gui.mode_tabs(window.current_document())
    assert sorted(order) == sorted(by_key[key] for key in shown), order
    assert order == [by_key[key] for _title, keys in woodcore_gui.NAV_GROUPS for key in keys if key in by_key and key in shown], order
    for index in order:
        nav.list.setCurrentItem(nav.rows[index])
        assert window.tab_widget.currentIndex() == index, "a row chosen does not bring its module forward"
    for index in reversed(order):
        window.tab_widget.setCurrentIndex(index)
        assert nav.current() == index, "a module brought forward (setCurrentWidget, Ctrl+n) does not select its row"
    from PySide6.QtGui import QShortcut
    keys = sorted(s.key().toString() for s in window.centralWidget().findChildren(QShortcut) if s.key().toString().startswith("Ctrl+") and s.key().toString()[5:].isdigit())
    assert keys == [f"Ctrl+{n}" for n in range(1, min(9, len(order)) + 1)], keys


def test_the_navigation_s_documents_and_the_rows_it_shows():
    """The navigation of a project written as three documents (30.09.2026): a drop-down at its top whose choice is said once (`modeChanged`) and which the window may take back without a word (`set_mode`); rows hidden with `set_visible`, a group's title with its last row, and `order` -- what Ctrl+1 … Ctrl+9 count by -- listing only the rows shown. Given no `modes` it has no drop-down, a project laid out as one report having only its report. The window's own use of it is tests/test_modes_window.py's."""
    _qt()
    import chrome
    groups = [("A", [(0, "Eins", "tab_plan"), (1, "Zwei", "tab_positions")]), ("B", [(2, "Drei", "tab_statics")])]
    modes = [("cu", "Nutzungsvereinbarung"), ("bp", "Projektbasis"), ("rs", "Statischer Bericht")]
    nav = chrome.SideNav(groups, modes=modes, mode="bp")
    said = []
    nav.modeChanged.connect(said.append)
    assert nav.mode() == "bp" and nav.mode_select.currentData() == "bp" and nav.mode_select.objectName() == "modeSelect"
    assert nav.mode_button.text() == "2"
    nav.mode_select.setCurrentIndex(nav.mode_select.findData("rs"))
    assert said == ["rs"] and nav.mode() == "rs" and nav.mode_button.text() == "3"
    nav.set_mode("cu")
    assert said == ["rs"], "set_mode said something"
    assert nav.mode() == "cu" and nav.mode_select.currentData() == "cu"
    assert [a.data() for a in nav.mode_actions.actions() if a.isChecked()] == ["cu"]
    assert nav.order() == [0, 1, 2]
    nav.set_visible([0, 1])
    assert nav.order() == [0, 1] and not nav.visible(2)
    heads = {head.text(): head for head, _members in nav.groups}
    assert heads["B"].isHidden() and not heads["A"].isHidden(), "a group of hidden rows keeps its title"
    nav.set_visible([2])
    assert nav.order() == [2] and heads["A"].isHidden() and not heads["B"].isHidden()
    nav.set_visible([0, 1, 2])
    assert nav.order() == [0, 1, 2]
    plain = chrome.SideNav(groups)
    assert plain.mode_select is None and plain.mode_button is None and plain.mode() is None


def test_a_module_holding_unsaved_changes_is_dotted_in_the_navigation():
    window = _window()
    _clean(window)
    editor = next(tab for tab in window.tabs if hasattr(tab, "dirty"))
    index = window.tabs.index(editor)
    assert not window.nav.dirty(index)
    editor.dirty = True
    window.update_tab_marks()
    try:
        assert window.nav.dirty(index), "the row carries no mark while its tab does"
        assert [i for i in range(window.tab_widget.count()) if window.nav.dirty(i)] == [index]
    finally:
        _clean(window)
    assert not window.nav.dirty(index)


def test_the_navigation_folds_to_its_icons_and_is_remembered():
    window = _window()
    import chrome
    import usersettings
    nav = window.nav
    assert not nav.collapsed and nav.width() == chrome.EXPANDED_WIDTH
    nav.set_collapsed(True)
    try:
        assert nav.collapsed and nav.maximumWidth() == chrome.COLLAPSED_WIDTH
        assert usersettings.read().get("nav_collapsed") is True, "the fold is not remembered"
        window.rebuild()
        assert window.nav.collapsed, "a window built again unfolds what the engineer folded"
    finally:
        window.nav.set_collapsed(False)
    assert usersettings.read().get("nav_collapsed") is False and window.nav.maximumWidth() == chrome.EXPANDED_WIDTH


def test_the_top_bar_names_the_project_and_what_the_next_pdf_carries():
    window = _window()
    import project
    from PySide6.QtWidgets import QLabel
    brand = window.centralWidget().findChild(QLabel, "brand")
    assert brand is not None and brand.text() == project.current().name
    assert window.meta.text() == window.meta_text()
    chip = window.pdf_chip
    try:
        window.set_pdf_level((None, None))
        window.set_pdf_lang(None)
        assert chip.isHidden(), "the chip shows while the report is compiled as written"
        window.set_pdf_level(("uniform", 2))
        window.set_pdf_lang("fr")
        assert not chip.isHidden() and chip.text() == f"{window.t('pdf_uniform_n', n=2)} · Français", chip.text()
        assert chip.property("chip") is True
    finally:
        window.set_pdf_level((None, None))
        window.set_pdf_lang(None)
    assert chip.isHidden()


def test_the_language_switch_answers_as_the_combo_it_replaced():
    window = _window()
    import woodcore_gui
    switch = window.language
    assert switch.count() == len(woodcore_gui.LANGUAGES)
    assert [switch.itemData(i) for i in range(switch.count())] == list(woodcore_gui.LANGUAGES)
    before = window.lang
    try:
        window.language.setCurrentIndex(list(woodcore_gui.LANGUAGES).index("de"))
        # the first row of the navigation is the title of its first group -- «Document», since the «Structure document» tab joined it (work package 2.3), «Projet» before
        assert window.lang == "de" and window.nav.list.item(0).text() == woodcore_gui.STRINGS["de"][woodcore_gui.NAV_GROUPS[0][0]]
        assert window.language.currentIndex() == list(woodcore_gui.LANGUAGES).index("de"), "the window built again shows another language"
    finally:
        window.language.setCurrentIndex(list(woodcore_gui.LANGUAGES).index(before))
    assert window.lang == before


def test_every_property_of_the_frame_has_its_rule():
    import theme
    for rule in ('QToolButton[segment="first"]', 'QToolButton[segment="last"]', 'QToolButton[chip="true"]', "QListWidget#nav", "QFrame#card",
                 "QLabel#brand", "QLabel#meta", "QLabel#eyebrow", "QTabWidget#modules::pane", "QTreeWidget#recent"):
        assert rule in theme.STYLE, rule


def test_the_start_page_s_cards_do_what_its_buttons_did():
    _qt()
    import home_page
    from PySide6.QtCore import Qt
    calls = []
    saved = {name: getattr(home_page.HomeWindow, name) for name in ("new", "choose")}
    for name in saved:
        setattr(home_page.HomeWindow, name, lambda self, name=name: calls.append(name))
    try:
        page = home_page.HomeWindow(lambda _file: False)
        assert list(page.cards) == ["home_new", "home_open"], "«Convertir un ancien dossier» left the page in v0.113"
        for key, card in page.cards.items():
            assert card.title.text() and card.text.text() and card.objectName() == "card"
            card.clicked.emit()
        assert calls == ["new", "choose"], calls
        from PySide6.QtGui import QKeyEvent
        from PySide6.QtCore import QEvent
        page.cards["home_open"].keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier))
        assert calls[-1] == "choose", "Enter on a card with the focus does nothing"
        # the recent projects: one card per project across the row, the data kept in its five columns
        assert page.list.isHeaderHidden() and all(page.list.isColumnHidden(c) for c in range(1, 5)) and not page.list.isColumnHidden(0)
        if page.list.topLevelItemCount():
            item = page.list.topLevelItem(0)
            assert item.text(0) and page.list.visualItemRect(item).height() >= 50, "a recent project is not set as a card"
        page.close()
    finally:
        for name, method in saved.items():
            setattr(home_page.HomeWindow, name, method)
