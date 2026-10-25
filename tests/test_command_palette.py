"""The command palette, Ctrl+K (calc/tools/command_palette.py, issue #83, docs/ui/command-palette.md).

What is held: that Ctrl+K and the field of the top bar open it, Escape and the cross close it, and Tab and the arrows do nothing; that a category is chosen by a click or by its character typed first; that a click chooses -- the panel filled, no tab changed --, a double click opens and closes, Enter opens the first entry; that the panel keeps its width from before the first click; that the actions are the window's own, read off its menus and its PDF button, an action that cannot run not run; that the tabs are the ones the document shown can open, with their Ctrl+n; that a position opens in «Positions»; that the entries opened lately come first in an empty palette; that it is inert while a variable is chosen; and that its words are in three languages.

Built off-screen on a copy of the example project; the palette's reading waited for.
"""

import contextlib
import sys
import time

import conftest
from conftest import ROOT

import project

TOOLS = ROOT / "calc" / "tools"
_STATE = {}


def _qt():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _window():
    if "window" not in _STATE:
        app = _qt()
        conftest.exported("checks.json")
        here = conftest.project_copy("command_palette")
        import woodcore_gui
        with project.using(here):
            window = woodcore_gui.MainWindow()
        window.resize(1400, 900)
        window.show()
        app.processEvents()
        _STATE.update(window=window, here=here, app=app)
    return _STATE["window"], _STATE["here"], _STATE["app"]


@contextlib.contextmanager
def _palette():
    window, here, app = _window()
    with project.using(here):
        palette = window.open_palette()
        end = time.monotonic() + 60
        while palette.reader.isRunning() and time.monotonic() < end:
            app.processEvents()
            time.sleep(0.02)
        app.processEvents()
        try:
            yield palette, window, app
        finally:
            if palette.isVisible():
                palette.reject()
            app.processEvents()


def _rows(palette):
    return [palette.list.item(i).data(0x100) for i in range(palette.list.count()) if palette.list.item(i).data(0x100) is not None]


def _key(palette, key):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtCore import QEvent
    palette.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier))


def test_ctrl_k_and_the_field_open_it_escape_and_the_cross_close_it():
    window, here, app = _window()
    import command_palette
    assert window.palette_shortcut.key().toString() == "Ctrl+K" == command_palette.SHORTCUT
    with project.using(here):
        window.palette_shortcut.activated.emit()
        app.processEvents()
        assert window.palette.isVisible()
        window.palette.close_button.click()
        app.processEvents()
        assert not window.palette.isVisible()
        window.palette_button.click()
        app.processEvents()
        assert window.palette.isVisible()
        from PySide6.QtCore import Qt
        from PySide6.QtTest import QTest
        QTest.keyClick(window.palette, Qt.Key.Key_Escape)
        app.processEvents()
        assert not window.palette.isVisible()
        window.palette.reader.wait(60000)


def test_tab_and_the_arrows_choose_nothing_and_a_click_chooses_without_changing_the_tab():
    from PySide6.QtCore import Qt
    with _palette() as (palette, window, app):
        before = window.tab_widget.currentIndex()
        for key in (Qt.Key.Key_Tab, Qt.Key.Key_Down, Qt.Key.Key_Up):
            _key(palette, key)
        assert palette.chosen is None and not palette.list.selectedItems()
        assert palette.focusNextPrevChild(True) is False
        width = palette.panel.width()
        item = next(palette.list.item(i) for i in range(palette.list.count()) if palette.list.item(i).data(0x100) is not None)
        palette.on_click(item)
        app.processEvents()
        assert palette.chosen is item.data(0x100) and window.tab_widget.currentIndex() == before and palette.isVisible()
        assert palette.panel.width() == width, "the panel moved under the pointer at the first click"


def test_the_panel_holds_only_the_buttons_of_the_entry_chosen_last():
    from PySide6.QtCore import QCoreApplication, QEvent
    from PySide6.QtWidgets import QPushButton
    with _palette() as (palette, window, app):
        items = [palette.list.item(i) for i in range(palette.list.count()) if palette.list.item(i).data(0x100) is not None][:4]
        for item in items:
            palette.on_click(item)
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            app.processEvents()
        opened = [b for b in palette.panel.findChildren(QPushButton) if b.text() in (palette.t("cp_run"), palette.t("cp_open"))]
        assert len(opened) == 1, f"the buttons of the entries chosen before stayed on the panel: {[b.text() for b in opened]}"


def test_a_category_is_chosen_by_a_click_or_its_character():
    with _palette() as (palette, window, app):
        palette.search.setText("@T0")
        assert palette.category == "objects" and _rows(palette) and all(e.category == "objects" for e in _rows(palette))
        palette.search.setText("")
        palette.category_buttons["norms"].click()
        assert palette.search.text().startswith("§") and palette.category == "norms"
        assert all(e.kind == "norm" for e in _rows(palette))


def test_the_actions_are_the_window_s_menus_and_its_pdf_button_and_the_tabs_the_document_s():
    import woodcore_gui
    with _palette() as (palette, window, app):
        actions = {e.label for e in palette.entries if e.kind == "action"}
        menus = set()

        def walk(items):
            for action in items:
                if action.menu() is not None:
                    walk(action.menu().actions())
                elif not action.isSeparator() and action.text().strip() and action.isVisible():
                    menus.add(action.text().replace("&", ""))
        walk(window.menuBar().actions())
        assert menus <= actions, sorted(menus - actions)
        assert window.pdf_button.text() in actions
        tabs = [e for e in palette.entries if e.kind == "tab"]
        assert [e.data for e in tabs] == window.nav.order()
        assert tabs[0].extra["shortcut"] == "Ctrl+1" and tabs[0].key == "tab:tab_project"
        assert {e.data for e in palette.entries if e.kind == "language"} == {"fr", "de", "en"}


def test_a_double_click_opens_and_closes_enter_opens_the_first_and_an_action_that_cannot_run_does_not():
    import palette_index
    with _palette() as (palette, window, app):
        palette.search.setText("posit")
        target = next(e for e in _rows(palette) if e.kind == "tab" and e.key == "tab:tab_positions")
        palette.on_double_click(next(palette.list.item(i) for i in range(palette.list.count()) if palette.list.item(i).data(0x100) is target))
        app.processEvents()
        import woodcore_gui
        assert woodcore_gui.TABS[window.tab_widget.currentIndex()][0] == "tab_positions" and not palette.isVisible()
    with _palette() as (palette, window, app):
        palette.search.setText("@T001")
        app.processEvents()
        palette.open_first()
        app.processEvents()
        assert woodcore_gui.TABS[window.tab_widget.currentIndex()][0] == "tab_positions"
        tab = window.tabs[window.tab_widget.currentIndex()]
        assert tab.current_id == "T001", "the position was not opened in its tab"
    ran = []

    class Off:
        def text(self):
            return "Off"

        def trigger(self):
            ran.append(True)

        def isEnabled(self):
            return False
    with _palette() as (palette, window, app):
        palette.open_entry(palette_index.Entry("action", "action:off", "Off", data=Off(), extra={"enabled": False}))
        assert not ran and palette.isVisible()


def test_the_entries_opened_lately_come_first_in_an_empty_palette():
    import command_palette
    with _palette() as (palette, window, app):
        palette.search.setText("posit")
        target = next(e for e in _rows(palette) if e.key == "tab:tab_positions")
        palette.open_entry(target)
    assert command_palette.RECENT[0] == "tab:tab_positions"
    with _palette() as (palette, window, app):
        assert palette.list.item(0).text() == window.t("cp_recent").upper() and _rows(palette)[0].key == "tab:tab_positions"


def test_it_is_inert_while_a_variable_is_chosen_and_its_words_are_in_three_languages():
    import command_palette
    import woodcore_gui
    window, here, app = _window()
    window.picking = True
    try:
        assert window.open_palette() is None
    finally:
        window.picking = False
    for lang in ("fr", "de", "en"):
        assert set(command_palette.STRINGS[lang]) == set(command_palette.STRINGS["fr"]), lang
        assert all(key in woodcore_gui.STRINGS[lang] for key in command_palette.STRINGS[lang])
        assert all(f"cp_kind_{kind}" in command_palette.STRINGS[lang] for kind in __import__("palette_index").GENRES)
        assert all(f"cp_cat_{key}" in command_palette.STRINGS[lang] for key, _p in __import__("palette_index").CATEGORIES)


def test_enter_opens_the_first_entry_and_a_tab_s_keys_and_settings_ctrl_comma_are_beside_them():
    _window()
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    import woodcore_gui
    with _palette() as (palette, window, app):
        settings = next(e for e in palette.entries if e.kind == "action" and (e.extra or {}).get("shortcut") == "Ctrl+,")
        assert settings is not None
        palette.search.setText("posit")
        app.processEvents()
        first = _rows(palette)[0]
        assert first.kind == "tab", first.key
        QTest.keyClick(palette.search, Qt.Key.Key_Return)   # the key itself, in the field
        app.processEvents()
        assert "tab:" + woodcore_gui.TABS[window.tab_widget.currentIndex()][0] == first.key and not palette.isVisible()


def test_the_search_field_stands_right_of_what_the_export_holds():
    """Issue #99 (UI-001 of the spec 2026-10-23-neige-correctifs-issues-96-99): «Rechercher… Ctrl K» is at the top left, just right of the grey «N valeurs · export du …», before the bar's stretch -- the views, the languages and the actions after it."""
    window, here, app = _window()
    bar = window.meta.parentWidget().layout()
    top = next(bar.itemAt(i).layout() for i in range(bar.count()) if bar.itemAt(i).layout() is not None and bar.itemAt(i).layout().indexOf(window.meta) >= 0)
    meta, field, language = top.indexOf(window.meta), top.indexOf(window.palette_button), top.indexOf(window.language)
    stretch = next(i for i in range(top.count()) if top.itemAt(i).spacerItem() is not None and top.stretch(i) > 0)
    assert meta < field < stretch < language, (meta, field, stretch, language)


def test_a_variable_of_the_palette_is_searched_in_the_variables_tab():
    """Issue #114 (REQ-007): «Variables» opened from the palette, the variable's name arrives in the tab's `search` -- the `QLineEdit` of its bar of tags -- and is searched in the filter already set."""
    import palette_index
    import variables_tab
    from PySide6.QtWidgets import QLineEdit
    with _palette() as (palette, window, app):
        palette.open_entry(palette_index.Entry("variable", "variable:q_k1", "q_k1", extra={"key": "q_k1"}))
        app.processEvents()
        tab = window.tabs[window.tab_widget.currentIndex()]
        assert isinstance(tab, variables_tab.VariablesTab)
        assert isinstance(tab.search, QLineEdit) and tab.search is tab.service("browser").search_bar.edit and tab.search.text() == "q_k1"
        shown = tab.service("browser").list.shown()
        assert shown and all(key[2] == "q_k1" or "q_k1" in tab.service("browser").catalogue.haystack(tab.variable(key), tab.service("browser").domains[key[:2]]) for key in shown)
        tab.search.setText("")
