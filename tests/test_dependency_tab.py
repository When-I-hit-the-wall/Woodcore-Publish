"""The «Dépendances» tab (spec docs/requirements/completed/2026-10-21-graphe-dependances.md, UI-001; calc/tools/dependencies_tab.py), off-screen on a copy of the example project exported with its graph.

What is held: a position chosen shows what depends on it -- its checks, its plans --, a check what it depends on; an object opened from the tab is opened in its own tab, the source chosen there; a graph not exported yet is said; the tab writes nothing -- it defines no writer of tab_guard.WRITERS -- and speaks the window's three languages.
"""

import json

import conftest

import project
from test_autosave import _boxes, _qt
from test_dependency_graph import _copy, _export

_STATE = {}


def _window():
    if "window" not in _STATE:
        app = _qt()
        here = _copy("dependency_tab")
        _export(here)
        # the plans' documents the export read: gone before the window opens, whose renderer would hold them open (conftest.project_copy)
        import shutil
        for folder in here.root.iterdir():
            if folder.is_dir() and folder.name.startswith("01_"):
                shutil.rmtree(folder, ignore_errors=True)
        with project.using(here), _boxes():
            import woodcore_gui
            window = woodcore_gui.MainWindow()
            window.reexport = lambda **_k: None
        _STATE.update(app=app, window=window, here=here)
    return _STATE["window"], _STATE["here"]


def _tab(window):
    """The tab's browser (issue #106: the tab is a class of parameters on the type «Données», its content one whole service)."""
    import woodcore_gui
    index = [k for k, _f in woodcore_gui.TABS].index("tab_dependencies")
    window.tab_widget.setCurrentIndex(index)
    return window.tabs[index].service("browser")


def _texts(widget):
    return [widget.item(i).text() for i in range(widget.count())]


def test_a_position_shows_what_depends_on_it_and_a_check_what_it_depends_on():
    window, here = _window()
    with project.using(here):
        tab = _tab(window)
        tab.reload()
        graph = json.loads((here.data_dir / "dependencies.json").read_text(encoding="utf-8"))
        edge = next(e for e in graph["edges"] if e["from"].startswith("check:") and e["to"].startswith("position:"))
        assert tab.select(edge["to"]), edge
        used = _texts(tab.used_by)
        assert any(edge["from"].split(":", 1)[1] in text for text in used), used
        assert tab.select(edge["from"])
        assert any(edge["to"].split(":", 1)[1] in text for text in _texts(tab.depends_on)), _texts(tab.depends_on)
        # a position read by a check, a schema and a plan lists the three kinds
        position = next(n for n in graph["nodes"] if n.startswith("position:") and {e["from"].split(":")[0] for e in graph["edges"] if e["to"] == n} >= {"check", "schema", "plan"})
        assert tab.select(position)
        used = " ".join(_texts(tab.used_by))
        assert all(window.t("warn_dep_kind_" + kind) in used for kind in ("check", "schema", "plan")), used
        # the tab survives a rebuild of itself, the object chosen kept (view_state, restore)
        new = window.refresh_tab("tab_dependencies")
        assert new.service("browser").current_node() == position
        # and the filter (issue #106, REQ-007: the browser's state given back by the frame)
        kind, ident = position.split(":", 1)
        new.service("browser").filter.setText(ident)
        again = window.refresh_tab("tab_dependencies").service("browser")
        assert again.filter.text() == ident and again.current_node() == position
        again.filter.setText("")


def test_an_object_opened_from_the_tab_opens_in_its_own_tab():
    import member_check_tab
    window, here = _window()
    with project.using(here):
        tab = _tab(window)
        tab.reload()
        graph = json.loads((here.data_dir / "dependencies.json").read_text(encoding="utf-8"))
        node = next(n for n in graph["nodes"] if n.startswith("check:"))
        with _boxes():
            assert tab.open(node), node
        shown = window.tab_widget.currentWidget()
        import check_tabs
        assert isinstance(shown, (member_check_tab.MemberCheckTab, check_tabs.TensionTab, check_tabs.CompressionTab, check_tabs.BendingTab, check_tabs.ShearTab)) and shown.current_id == node.split(":", 1)[1], (type(shown).__name__, getattr(shown, "current_id", None))
        # a case read from no source of Woodcore has no tab: said, nothing opened
        assert window.open_object("load:snow-load/no-such-case") is False


def test_a_graph_not_exported_yet_is_said_and_the_tab_writes_nothing():
    window, here = _window()
    import dependencies_tab   # calc/tools on the path once the window is built
    import tab_guard
    with project.using(here):
        tab = _tab(window)
        path = here.data_dir / "dependencies.json"
        kept = path.read_bytes()
        path.unlink()
        try:
            tab.reload()
            banner = tab.ctx.host.service("banner").label   # the type's banner, which the browser tells (data_tab.ExportBanner)
            assert banner.text() == window.t("dg_not_exported") and tab.objects.topLevelItemCount() == 0
        finally:
            path.write_bytes(kept)
        tab.reload()
    assert not [name for name in tab_guard.WRITERS if name in dir(dependencies_tab.DependenciesTab)], "a browser defines no writer"
    assert not hasattr(dependencies_tab.DependenciesTab, "dirty")
    for lang in ("fr", "de", "en"):
        assert set(dependencies_tab.STRINGS[lang]) == set(dependencies_tab.STRINGS["fr"]), lang
