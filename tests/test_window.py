"""The window's mark of unsaved changes: a dot at the left, with its room kept whether it is drawn or not (docs/ui/window.md §10quater).

Until v0.61.3 the mark was a bullet appended to the row's text -- `SD_01-8mm — Velo Unterstand: … •` -- and the tabs carried none at all. It is an icon now, set at the left of the row and of the tab's title, and every row and every tab carries one: the dot where there are unsaved changes, a blank of the same size everywhere else.

What that last part buys is the whole reason the mark is an icon and not a character: a tab bar that widened as an editor is touched would move every tab after it, and a row whose text slid sideways as it is typed into would be as hard to follow. Nothing but this test holds it -- putting the bullet back into the text would look right in a screenshot and would still be wrong.

⚠️ Skipped where PySide6 is not installed or the export has never been run here: a machine that only builds the report is a legitimate machine. The window is built once, off-screen, and shared by the checks below; building it reads every plan's background.
"""

import os
import sys

import conftest
from conftest import ROOT, Skip

_window = None


def _main_window():
    """The window, built once, off-screen -- a test run must never open one."""
    global _window
    if _window is None:
        conftest.exported("calculations.json")  # a window with no export behind it has nothing to mark
        path = str(ROOT / "calc" / "tools")
        if path not in sys.path:
            sys.path.insert(0, path)
        try:
            from PySide6.QtWidgets import QApplication
        except ImportError as exc:
            raise Skip(f"PySide6 is not installed ({exc})")
        import woodcore_gui
        QApplication.instance() or QApplication([])
        _window = woodcore_gui.MainWindow()
    return _window


def _editors(win):
    """The tabs that have something to save in a list of their own: the plans, the static models, the polar moments… -- not the «Projet» tab, whose one draft is the title page and which lists nothing (issue #87)."""
    return [w for w in win.tabs if hasattr(w, "dirty") and hasattr(w, "list")]


def _rows(tab):
    """One (item, id) per row of an editor's list, whichever widget it keeps them in."""
    if hasattr(tab, "calc_items"):  # the polar moments, a tree
        return [(item, cid) for cid, item in tab.calc_items.items()]
    if hasattr(tab.list, "rows"):   # a GroupedList: a tree of folders and entries (v0.69, grouped_list.py)
        return tab.list.rows()
    from PySide6.QtCore import Qt
    return [(tab.list.item(i), tab.list.item(i).data(Qt.ItemDataRole.UserRole)) for i in range(tab.list.count())]


def _icon(item):
    return item.icon(0) if hasattr(item, "childCount") else item.icon()


def _text(item):
    return item.text(0) if hasattr(item, "childCount") else item.text()


def _painted(win, icon):
    """How many pixels the mark actually paints -- 0 for the blank, a disc for the dot."""
    image = icon.pixmap(win.mark_size).toImage()
    return sum(1 for y in range(image.height()) for x in range(image.width()) if image.pixelColor(x, y).alpha() > 0)


def _set_dirty(win, on):
    for tab in _editors(win):
        tab.dirty = on
        tab.update_list_marker()
    win.update_tab_marks()


def test_the_tab_bar_keeps_its_widths():
    """The dot must not resize a tab. This is the check the rest of the file exists for."""
    win = _main_window()
    bar = win.tab_widget.tabBar()
    _set_dirty(win, False)
    clean = [bar.tabSizeHint(i).width() for i in range(bar.count())]
    _set_dirty(win, True)
    dirty = [bar.tabSizeHint(i).width() for i in range(bar.count())]
    _set_dirty(win, False)
    assert clean == dirty, (
        f"a tab changes width when its dot appears:\n  clean {clean}\n  dirty {dirty}\n"
        f"The room for the mark must be kept on every tab -- a blank icon of the size of the dot."
    )


def test_the_dot_and_the_blank_are_the_same_size():
    win = _main_window()
    dot, blank = win.dirty_mark(True), win.dirty_mark(False)
    assert not dot.isNull() and not blank.isNull(), "a null icon reserves no room at all"
    assert dot.pixmap(win.mark_size).size() == blank.pixmap(win.mark_size).size()
    assert _painted(win, blank) == 0, "the blank mark must paint nothing"
    assert _painted(win, dot) > 4, "the dot must be visible"


def test_every_tab_and_every_row_carries_a_mark():
    """The room is kept everywhere, not only where there is something to mark."""
    win = _main_window()
    _set_dirty(win, False)
    for i in range(win.tab_widget.count()):
        assert not win.tab_widget.tabIcon(i).isNull(), f"tab {win.tab_widget.tabText(i)!r} keeps no room for its mark"
    for tab in _editors(win):
        rows = _rows(tab)
        assert rows, f"{type(tab).__name__} lists nothing -- the check below would hold vacuously"
        for item, key in rows:
            assert not _icon(item).isNull(), f"{type(tab).__name__}: row {key!r} keeps no room for its mark"


def test_the_tabs_of_data_are_browsers_and_never_marked():
    """Issue #106 (REQ-006, UI-003 of the spec 2026-10-24-type-donnees): «Variables», «Métré», «Dépendances» and «Commandes», on the type «Données», have no `dirty` -- they are not among the editors -- and keep the blank even while every editor holds unsaved changes."""
    import data_tab
    win = _main_window()
    data = [i for i, tab in enumerate(win.tabs) if isinstance(tab, data_tab.DataTab)]
    assert len(data) == 4, data
    _set_dirty(win, True)
    try:
        win.update_tab_marks()
        for i in data:
            tab = win.tabs[i]
            assert tab not in _editors(win) and not hasattr(tab, "dirty") and not hasattr(tab, "update_list_marker"), type(tab).__name__
            assert win.tab_widget.tabIcon(i).cacheKey() == win.dirty_mark(False).cacheKey(), type(tab).__name__
    finally:
        _set_dirty(win, False)


def test_the_dot_marks_what_is_being_edited_and_its_tab():
    win = _main_window()
    _set_dirty(win, False)
    assert not [i for i in range(win.tab_widget.count()) if _painted(win, win.tab_widget.tabIcon(i))], \
        "a tab is dotted while nothing is unsaved"
    for tab in _editors(win):
        tab.dirty = True
        tab.update_list_marker()
        dotted = [key for item, key in _rows(tab) if _painted(win, _icon(item))]
        assert len(dotted) == 1, f"{type(tab).__name__}: {len(dotted)} rows dotted, expected the one being edited ({dotted})"
        index = win.tabs.index(tab)
        assert _painted(win, win.tab_widget.tabIcon(index)), \
            f"the row is marked but the tab {win.tab_widget.tabText(index)!r} is not"
        tab.dirty = False
        tab.update_list_marker()
        assert not [key for item, key in _rows(tab) if _painted(win, _icon(item))], \
            f"{type(tab).__name__}: a row stays dotted once saved"
        assert not _painted(win, win.tab_widget.tabIcon(index)), "a tab stays dotted once saved"


def test_the_mark_is_never_written_into_the_text():
    """The bullet this replaced sat at the right of the row's text; a text mark cannot keep its room."""
    win = _main_window()
    _set_dirty(win, True)
    try:
        titles = [win.tab_widget.tabText(i) for i in range(win.tab_widget.count())]
        assert not [t for t in titles if "•" in t], f"a tab's title carries a bullet: {titles}"
        for tab in _editors(win):
            marked = [_text(item) for item, _key in _rows(tab) if "•" in _text(item)]
            assert not marked, f"{type(tab).__name__}: a row carries a bullet in its text: {marked}"
    finally:
        _set_dirty(win, False)


def test_the_window_holds_no_banner_of_load_workbooks():
    """Issue #109 (UI-003): no workbook is read, so none can be stale -- the banner «… a été modifié après le dernier export» went with them, its word too."""
    _main_window()
    import woodcore_gui
    import woodcore_gui_words
    assert not hasattr(woodcore_gui, "stale_workbooks") and not hasattr(woodcore_gui.MainWindow, "stale_text")
    assert all("stale" not in words for words in woodcore_gui_words.STRINGS.values())


def test_a_missing_page_is_compiled_in_the_language_of_the_pages_beside_it():
    """A German window shows the committed pages, all German (build_examples.LANG): one missing or stale among them is compiled in German, never in another language (periodic audit 260916, AUD-7-411, where a French window showed that one example in French among German ones). A French or English window shows every page in its own language since v0.94, through command_preview.render_localised -- the committed pages being German, there is no language to mix."""
    import time
    from types import SimpleNamespace
    from PySide6.QtWidgets import QApplication
    win = _main_window()
    import build_examples
    import command_preview
    tab = next(t for t in win.tabs if type(t).__name__ == "CommandsTab").service("browser").page.renderer   # the examples' renderer, the page's own since issue #115, mounted by the tab's browser since issue #106
    seen = []

    def render(kind):
        def fake(code, level, lang, *_args, **_kwargs):
            seen.append((kind, lang))
            return None, "error: stubbed"
        return fake

    shown = {}
    box = SimpleNamespace(code="#val(1.5)", level=2, command="val", index=0,
                          show_note=lambda *a, **k: None, show_png=lambda *a, **k: shown.setdefault("png", a), show_error=lambda *a, **k: shown.setdefault("error", a))
    saved = (command_preview.render_blocking, command_preview.render_localised, command_preview.cached_png, command_preview.have_typst, tab.lang)
    command_preview.render_blocking, command_preview.render_localised = render("blocking"), render("localised")
    command_preview.cached_png, command_preview.have_typst = (lambda _key: None), (lambda: True)
    tab.page_for = lambda _box: (None, "missing")
    try:
        for lang in (build_examples.LANG, "fr"):
            tab.lang = lang
            tab.show_page(box)
            deadline = time.time() + 10
            while (tab.job is not None or tab.queue) and time.time() < deadline:
                QApplication.processEvents()
                time.sleep(0.01)
    finally:
        (command_preview.render_blocking, command_preview.render_localised, command_preview.cached_png, command_preview.have_typst, tab.lang) = saved
        del tab.page_for
    assert seen == [("blocking", build_examples.LANG), ("localised", "fr")], seen
    assert "error" in shown, "a compile that failed with no German page to fall back on says why"


def test_a_disabled_button_says_why():
    """A button shown disabled with no tooltip cannot be told from a broken one: every disabled element says why (v0.47's rule, prompt-audit phase 5). «Calibrer…», «Longueurs des murs», «Annuler les modifications» (plans, polar moments) and «Ouvrir le classeur» said nothing (periodic audit 260916, AUD-5-6)."""
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        from PySide6.QtWidgets import QAbstractButton, QApplication, QTabBar
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    app = QApplication.instance() or QApplication([])
    import woodcore_gui
    window = woodcore_gui.MainWindow()
    window.show()
    bare = set()
    for tab in window.tabs:
        window.tab_widget.setCurrentWidget(tab)
        for opened in (False, True):
            if opened and hasattr(tab, "load_first"):
                tab.dirty = False
                tab.load_first()
            app.processEvents()
            for button in tab.findChildren(QAbstractButton):
                if isinstance(button.parent(), QTabBar) or not button.isVisibleTo(tab) or button.isEnabled():
                    continue
                if not button.toolTip():
                    bare.add(f"{type(tab).__name__}: {button.text() or button.objectName()}")
        tab.dirty = False
    conftest.dispose(window)
    assert not bare, "disabled with nothing to say why: " + "; ".join(sorted(bare))
