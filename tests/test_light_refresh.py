"""After a position is saved, the window is not built again (calc/tools/woodcore_gui.py `refresh_lightly`, `refresh_tab`, `refresh_if_stale`; v0.117, docs/ui/window.md §10quater and docs/decisions.md).

The engineer, 08.10.2026, on the 12 to 15 seconds a position took to save, two thirds of them the window building its 32 tabs again on its own thread: «rafraîchir que les onglets qui les lisent». What is held: a position saved imports **lightly** (`reexport(light=True)`) -- a PDF asked for, «Import données» and a reload being full rebuilds as ever --; after it **no tab is built again but the one in front** and none at all while it is the Positions tab, which holds what it has just written; every other tab is marked **stale** and built again, with the state it kept through a rebuild (`view_state`, its display's options), **when it is next shown** and before it is seen -- so there is no list of the tabs that read positions to keep in step with the code, and none shows what an export no longer says; the window's data, what stands beside the project's name and the banner of workbooks changed since the export are brought up to date at once; a light refresh that goes wrong is a full rebuild.

⚠️ Built off-screen on a copy of the example project; every tab's constructor is counted.
"""

import os
import sys

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
    """One window for the file, on a copy of the example project, whose tabs' constructors are counted."""
    if "window" not in _STATE:
        _qt()
        conftest.exported("calculations.json")
        here = conftest.project_copy("light_refresh")
        import woodcore_gui
        calls = {}

        def counted(key, factory):
            def build(app):
                calls[key] = calls.get(key, 0) + 1
                return factory(app)
            return build

        real = woodcore_gui.TABS
        woodcore_gui.TABS = tuple((key, counted(key, factory)) for key, factory in real)
        try:
            with project.using(here):
                window = woodcore_gui.MainWindow()
        finally:
            pass
        _STATE.update(window=window, here=here, calls=calls, real=real)
    return _STATE["window"], _STATE["here"], _STATE["calls"]


def _index(key):
    import woodcore_gui
    return [k for k, _f in woodcore_gui.TABS].index(key)


def test_a_position_saved_imports_lightly_and_a_pdf_a_reload_and_the_import_button_do_not():
    import inspect
    import woodcore_gui
    import positions_tab
    assert "light=True" in inspect.getsource(positions_tab.PositionsTab.reimport), "a position saved asks for the light refresh"
    assert inspect.signature(woodcore_gui.MainWindow.reexport).parameters["light"].default is False, "everything else is a full rebuild, as before"
    source = inspect.getsource(woodcore_gui.MainWindow.reexport)
    assert "self.light_export = bool(light) and not chain_pdf" in source, "a PDF asked for is compiled after a full rebuild"
    assert "if light and not compile_next" in inspect.getsource(woodcore_gui.MainWindow.export_done)


def test_after_a_position_saved_no_tab_is_built_again_while_the_positions_tab_is_in_front():
    window, here, calls = _window()
    with project.using(here):
        window.tab_widget.setCurrentIndex(_index("tab_positions"))
        before = list(window.tabs)
        calls.clear()
        window.refresh_lightly()
        assert calls == {}, f"tabs were built again: {calls}"
        assert window.tabs == before, "the tabs are the very ones that were there"
        import woodcore_gui
        assert window.stale_tabs == {key for key, _f in woodcore_gui.TABS} - {"tab_positions"}
        assert window.export_button.isEnabled() and window.pdf_button.isEnabled(), "the buttons the export held are given back"


def test_a_stale_tab_is_built_again_when_it_is_shown_and_before_it_is_seen_with_what_it_kept():
    window, here, calls = _window()
    with project.using(here):
        schema = _index("tab_schema")
        window.tab_widget.setCurrentIndex(_index("tab_positions"))
        window.refresh_lightly()
        old = window.tabs[schema]
        old_id = id(old)
        calls.clear()
        window.tab_widget.setCurrentIndex(schema)
        assert calls == {"tab_schema": 1}, f"only the tab shown is built: {calls}"
        assert id(window.tabs[schema]) != old_id and window.tab_widget.widget(schema) is window.tabs[schema]
        assert "tab_schema" not in window.stale_tabs and "tab_plan" in window.stale_tabs, "the others wait to be shown"
        assert window.tab_widget.currentIndex() == schema, "the tab in front is still the one chosen"
        # a tab that is not stale is not built again when it is shown
        calls.clear()
        window.tab_widget.setCurrentIndex(_index("tab_positions"))
        window.tab_widget.setCurrentIndex(schema)
        assert calls == {}, calls


def test_the_tab_in_front_is_built_again_at_once_where_it_is_not_the_positions_tab_and_keeps_its_state():
    window, here, calls = _window()
    with project.using(here):
        positions = window.tabs[_index("tab_positions")]
        window.tab_widget.setCurrentIndex(_index("tab_positions"))
        ids = positions.ids()
        assert len(ids) >= 2
        positions.load(ids[1])
        # the state a tab keeps goes through refresh_tab as it goes through a rebuild: here the position chosen in the list
        calls.clear()
        new = window.refresh_tab("tab_positions")
        assert calls == {"tab_positions": 1} and new is window.tabs[_index("tab_positions")] and new is not positions
        assert new.current_id == ids[1], "the position being looked at is still the one"
        # in front, and not the positions tab: built again at once, and the others stale
        window.tab_widget.setCurrentIndex(_index("tab_schema"))
        calls.clear()
        window.refresh_lightly()
        assert calls == {"tab_schema": 1}, calls
        assert "tab_schema" not in window.stale_tabs and "tab_positions" not in window.stale_tabs and "tab_plan" in window.stale_tabs


def test_a_full_rebuild_builds_everything_and_leaves_nothing_stale_and_a_failed_light_refresh_is_one():
    window, here, calls = _window()
    with project.using(here):
        import woodcore_gui
        window.refresh_lightly()
        assert window.stale_tabs
        calls.clear()
        window.rebuild()
        assert len(calls) == len(woodcore_gui.TABS) and set(calls.values()) == {1}, calls
        assert window.stale_tabs == set(), "every tab is new"
        # the export that ended well, started by a position saved: the light refresh, and no rebuild
        window.refresh_lightly()
        calls.clear()

        class Process:
            def deleteLater(self):
                pass

        window.process, window.light_export, window.pending_pdf, window.quiet_export = Process(), True, False, True
        window.export_done(0, "", "")
        assert calls == {} or set(calls) <= {woodcore_gui.TABS[window.tab_widget.currentIndex()][0]}, f"a full rebuild ran: {calls}"
        assert window.process is None and window.light_export is False, "the flag is consumed"
        # a light refresh that goes wrong is a full rebuild
        rebuilt = []
        real_light, real_reload = window.refresh_lightly, window.reload
        window.refresh_lightly = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
        window.reload = lambda: rebuilt.append(True)
        try:
            window.process, window.light_export, window.quiet_export = Process(), True, True
            window.export_done(0, "", "")
        finally:
            window.refresh_lightly, window.reload = real_light, real_reload
        assert rebuilt == [True]
        # and an export that asked for a PDF is a full rebuild, the compile following it
        rebuilt.clear()
        window.reload = lambda: rebuilt.append(True)
        window.start_compiles = lambda: None
        try:
            window.process, window.light_export, window.pending_pdf, window.quiet_export = Process(), True, True, True
            window.export_done(0, "", "")
        finally:
            window.reload = real_reload
        assert rebuilt == [True]


def test_the_banner_and_the_line_beside_the_name_follow_a_light_refresh():
    window, here, calls = _window()
    with project.using(here):
        window.meta.setText("old")
        window.refresh_lightly()
        assert window.meta.text() == window.meta_text() and window.meta.text() != "old"
        from PySide6.QtWidgets import QLabel
        window.stale_banner = QLabel("workbooks changed since the export")
        window.stale_banner.setVisible(True)
        window.stale_text = lambda: ""
        try:
            window.refresh_lightly()
        finally:
            del window.stale_text
        assert window.stale_banner.isHidden() and window.stale_banner.text() == "", "a banner of the old export is taken off"
