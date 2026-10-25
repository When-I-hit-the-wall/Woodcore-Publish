"""Every tab of the window declared once, and guarded wherever its writers are defined (spec 2026-10-19-base-saine-nettoyage, ARCH-001, ARCH-RISK-101, ARCH-RISK-106; calc/tools/tab_registry.py, calc/tools/tab_guard.py).

A tab is one `TabSpec`: the lists the window reads are derived from it, so a tab can no longer be half added. What is held here is what the eight lists of before held by hand -- and that the read-only guard reaches a writer defined in a base class shared by several tabs, which the old guard, wrapping by name in a class and its mixins only, did not.
"""

TIER = "fast"  # tests/run_tests.py --fast

import sys

import conftest  # noqa: F401  -- calc/ on the path, Qt off-screen
from conftest import ROOT

if str(ROOT / "calc" / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "calc" / "tools"))

import chrome  # noqa: E402
import source_archive  # noqa: E402
import tab_guard  # noqa: E402
import tab_registry  # noqa: E402
import woodcore_gui  # noqa: E402


def test_every_list_the_window_reads_is_derived_from_the_specs():
    keys = [spec.key for spec in tab_registry.SPECS]
    assert len(keys) == len(set(keys)), "a key declared twice"
    assert woodcore_gui.TABS == tab_registry.TABS and [k for k, _f in woodcore_gui.TABS] == keys
    flattened = [key for _group, members in woodcore_gui.NAV_GROUPS for key in members]
    assert flattened == keys, "the navigation lists the tabs in their order, each group contiguous"
    assert len({g for g, _m in woodcore_gui.NAV_GROUPS}) == len(woodcore_gui.NAV_GROUPS), "a group cut in two"
    assert set(woodcore_gui.MODE_TABS["rs"]) == set(keys), "the report shows every tab"
    assert set(woodcore_gui.MODE_TABS["cu"]) <= set(woodcore_gui.MODE_TABS["bp"]) <= set(keys)
    assert woodcore_gui.MODE_BOUND == ("tab_structure", "tab_journal")


def test_every_tab_has_its_icon_and_its_title_in_three_languages():
    for spec in tab_registry.SPECS:
        assert spec.key in chrome.ICONS, f"{spec.key} has no icon in chrome.ICONS"
        for lang in ("fr", "de", "en"):
            assert woodcore_gui.STRINGS[lang].get(spec.key), f"{spec.key} has no title in {lang}"
        for words in (spec.group, spec.section):
            if words:
                assert all(woodcore_gui.STRINGS[lang].get(words) for lang in ("fr", "de", "en")), words


def test_every_tab_class_keeps_its_view_through_a_rebuild():
    """The window asks every tab its view_state() before it builds it again (woodcore_gui.rebuild, refresh_tab): a tab without one stopped every rebuild, a change of language, an export from the window (found by the verification of issue #71)."""
    import tab_host
    for spec in tab_registry.SPECS:
        if isinstance(spec.factory, type):
            assert callable(getattr(spec.factory, "view_state", None)), spec.key
            if issubclass(spec.factory, tab_host.TabHost):   # a tab built on a type answers what the window calls through its host (spec 2026-10-23-onglets-types-et-services, ARCH-009)
                for name in ("view_state", "restore", "set_view", "on_shown", "confirm_leave", "save", "update_list_marker", "lists_object", "open_object", "service"):
                    assert getattr(spec.factory, name) is getattr(tab_host.TabHost, name) or getattr(spec.factory, name).__qualname__.startswith(("TabHost.", "DisplayTab.")), (spec.key, name)
            import document_tab
            if issubclass(spec.factory, document_tab.DocumentTab):   # a tab of a document answers through its type and its frame (issue #107, REQ-005, REQ-007)
                for name in ("view_state", "restore", "set_view", "on_shown", "on_mode", "confirm_leave", "flush_pending", "save", "discard", "service", "on_properties_changed"):
                    assert getattr(spec.factory, name).__qualname__.startswith(("DocumentTab.", "TabFrame.")), (spec.key, name)


def test_no_tab_built_on_a_type_lacks_what_its_services_need():
    """REQ-006 of the spec 2026-10-23-onglets-types-et-services: a domain that lacks a function a service needs stops its tab as it is built -- and no tab of the window does."""
    import tab_frame
    import tab_host
    for spec in tab_registry.SPECS:
        if isinstance(spec.factory, type) and issubclass(spec.factory, tab_host.TabHost):
            assert not tab_host.missing_needs([cls() for cls in spec.factory.SERVICES], spec.factory.MODULE), spec.key
        if isinstance(spec.factory, type) and issubclass(spec.factory, tab_frame.TabFrame):   # a service asks its own module where it names one (issue #107, REQ-009)
            for cls in spec.factory.SERVICES:
                assert not tab_frame.missing_needs([cls()], cls.NEEDS_MODULE or spec.factory.MODULE), (spec.key, cls.__name__)


def test_a_tab_class_that_names_its_key_names_the_one_it_is_declared_under():
    for spec in tab_registry.SPECS:
        key = getattr(spec.factory, "KEY", None) if isinstance(spec.factory, type) else None
        if isinstance(key, str) and key.startswith("tab_"):
            assert key == spec.key, f"{spec.factory.__name__}.KEY is {key}, declared as {spec.key}"


def test_every_writer_a_tab_reaches_is_guarded_where_it_is_defined_and_once():
    for cls in tab_registry.GUARDED_TABS:
        for owner in tab_guard.own_classes(cls):
            for name in tab_guard.WRITERS:
                method = vars(owner).get(name)
                if method is not None and callable(method):
                    assert getattr(method, "_woodcore_tab_guard", False), f"{owner.__name__}.{name} is not guarded"
                    assert not getattr(getattr(method, "__wrapped__", None), "_woodcore_tab_guard", False), f"{owner.__name__}.{name} is guarded twice"
    for name in ("archive", "restore", "purge"):
        assert getattr(vars(source_archive.Actions)[name], "_woodcore_tab_guard", False), name
    # the card of a list written once, built by «Métrés», «Journal» and «Positions» (issue #106, REQ-010): guarded where it is defined, once
    import list_file_card
    for name in list_file_card.ListFileCard.WRITERS:
        method = vars(list_file_card.ListFileCard)[name]
        assert getattr(method, "_woodcore_tab_guard", False) and not getattr(getattr(method, "__wrapped__", None), "_woodcore_tab_guard", False), name
    # the tabs built on a type: their writers are their services' and their store's, each guarded by the WRITERS it declares (spec 2026-10-23-onglets-types-et-services, ARCH-004)
    for cls in tab_registry.GUARDED_SERVICES:
        for name in cls.WRITERS:
            owner = next(k for k in tab_guard.own_classes(cls) if name in vars(k))
            method = vars(owner)[name]
            assert getattr(method, "_woodcore_tab_guard", False), f"{owner.__name__}.{name} is not guarded"
            assert not getattr(getattr(method, "__wrapped__", None), "_woodcore_tab_guard", False), f"{owner.__name__}.{name} is guarded twice"
    # a widget a service wraps whole (`Service.WIDGET`, issue #107, ARCH-008): its writers guarded by name where they are defined, once -- and a service that names one is mounted by a tab of the window
    for cls in tab_registry.GUARDED_WIDGETS:
        found = 0
        for owner in tab_guard.own_classes(cls):
            for name in tab_guard.WRITERS:
                method = vars(owner).get(name)
                if method is not None and callable(method):
                    found += 1
                    assert getattr(method, "_woodcore_tab_guard", False), f"{owner.__name__}.{name} is not guarded"
                    assert not getattr(getattr(method, "__wrapped__", None), "_woodcore_tab_guard", False), f"{owner.__name__}.{name} is guarded twice"
        assert found, f"{cls.__name__} is a widget guarded for no writer"
    assert all(service.WIDGET in tab_registry.GUARDED_WIDGETS for service in tab_registry.GUARDED_SERVICES if getattr(service, "WIDGET", None) is not None)
    # every name of the list is defined somewhere a tab, a service or a widget reaches: none is kept for nothing
    reached = [k for cls in tab_registry.GUARDED_TABS + tab_registry.GUARDED_WIDGETS + tab_registry.GUARDED_SERVICES for k in tab_guard.own_classes(cls)]
    unused = [name for name in tab_guard.WRITERS if not any(name in vars(k) for k in reached)]
    assert not unused, f"tab_guard.WRITERS names writers no tab, service or widget defines: {unused}"


def test_a_tab_built_on_a_type_answers_what_the_window_asks():
    """ARCH-009 of the spec 2026-10-23-onglets-types-et-services: the host answers once what the window, the autosave and the palette call on a tab (`TAB_API`)."""
    import tab_host
    built = [spec.factory for spec in tab_registry.SPECS if isinstance(spec.factory, type) and issubclass(spec.factory, tab_host.TabHost)]
    assert built
    for cls in built:
        assert all(hasattr(cls, name) or name in ("splitter", "display", "dirty", "current_id", "source", "view") for name in tab_host.TAB_API), cls.__name__
        for name in ("dirty", "current_id", "source"):
            assert isinstance(getattr(tab_host.TabHost, name), property), name
    # the tabs of a document (issue #107, REQ-005): every name of the frame's part, and the type's own -- `dirty` and `save`, but no `current_id`, `id_edit` nor `list` (ARCH-007)
    import document_tab
    import tab_frame
    documents = [spec.factory for spec in tab_registry.SPECS if isinstance(spec.factory, type) and issubclass(spec.factory, document_tab.DocumentTab)]
    assert {cls.__name__ for cls in documents} == {"ProjectTab", "StructureTab"}, documents
    for cls in documents:
        assert all(hasattr(cls, name) or name in ("splitter", "view") for name in tab_frame.FRAME_API), cls.__name__
        assert all(hasattr(cls, name) for name in ("dirty", "save", "set_view", "flush_pending", "discard")), cls.__name__
        assert not any(hasattr(cls, name) for name in ("current_id", "current", "id_edit", "list")), cls.__name__
    # the tabs of data (issue #106, REQ-006, REQ-007): every name of the frame's part answered by the type, none by which the window tells an editor; none guarded as a tab, none writing
    import data_tab
    data = [spec.factory for spec in tab_registry.SPECS if isinstance(spec.factory, type) and issubclass(spec.factory, data_tab.DataTab)]
    assert {cls.__name__ for cls in data} == {"VariablesTab", "MetreTab", "DependenciesTab", "CommandsTab"}, data
    for cls in data:
        assert all(hasattr(cls, name) or name in ("splitter", "view") for name in tab_frame.FRAME_API), cls.__name__
        assert not any(hasattr(cls, name) for name in ("dirty", "save", "current_id", "source", "current", "id_edit", "list")), cls.__name__
        assert cls not in tab_registry.GUARDED_TABS and cls.VIEWS == (), cls.__name__


def _makes_domains(cls):
    """Whether a tab's cases are domains with a file of their own: its class says so, or -- a tab built on a type -- its store."""
    import tab_host
    if issubclass(cls, tab_host.TabHost):
        return cls.SYNC_STORE
    return getattr(cls, "SYNC_DOMAIN", False)


def test_the_tabs_that_make_domains_say_so_on_their_class():
    makes = {spec.key for spec in tab_registry.SPECS if isinstance(spec.factory, type) and _makes_domains(spec.factory)}
    assert {"tab_ac_selfweight", "tab_ac_snow", "tab_ac_wind", "tab_connections", "tab_polar", "tab_mc_tension", "tab_mc_fire",
            "tab_st_tension", "tab_python"} <= makes, makes
    assert not makes & {"tab_structure", "tab_plan", "tab_journal", "tab_variables", "tab_commands"}, makes


def test_every_editor_tab_has_the_one_structure_of_its_kind():
    """Solution B (spec 2026-10-19-base-saine-nettoyage, D-11): a tab that edits sources is a `SourceEditorTab` -- its list, its draft's actions, Ctrl+S, the question about unsaved changes, its export --, a tab that edits a drawing is a `CanvasEditorTab` -- the same, and «Annuler» --, a tab to come is a `ReservedTab`. Only the four tabs that edit no source of their own stand apart: the document's structure, and the references, «Variables», «Commandes» and «Dépendances»."""
    import calc_tab
    import canvas_editor
    import reserved_tab
    import source_editor
    # «Métré» reads the export and edits no source (spec 2026-10-21-commandes-typst-refonte, UI-003): a browser too
    browsers = {"tab_structure", "tab_variables", "tab_commands", "tab_dependencies", "tab_metre"}
    # «Projet» edits the project file itself -- its title page, its form, its documents (issues #87, #88, #90) --, no list of sources: a form of its own, guarded by its writers
    browsers.add("tab_project")
    canvases = {"tab_plan", "tab_fire", "tab_statics", "tab_schema"}
    # the tabs built on the type «Calcul» (spec 2026-10-23-onglets-types-et-services, ARCH-010, replacing D-25): the structure of their kind is their type's
    calculations = {"tab_ac_snow", "tab_ac_selfweight", "tab_ac_wind", "tab_mc_tension", "tab_mc_compression", "tab_mc_bending", "tab_mc_shear"}   # the wind since spec 2026-10-23-onglet-vent-briques (issue #100), the four member checks since issue #112
    # the type «Bibliothèque» (issue #110, ARCH-006): the engineer's own files, no source of the project -- apart from SourceEditorTab and TabHost
    import library_tab
    libraries = {"tab_materials"}
    for spec in tab_registry.SPECS:
        if not isinstance(spec.factory, type):
            continue
        if spec.key in browsers:
            assert not issubclass(spec.factory, source_editor.SourceEditorTab), spec.key
        elif spec.key in libraries:
            assert issubclass(spec.factory, library_tab.LibraryTab) and not issubclass(spec.factory, source_editor.SourceEditorTab), f"{spec.key} is a library: a LibraryTab"
        elif spec.key in calculations:
            assert issubclass(spec.factory, calc_tab.CalcTab) and not issubclass(spec.factory, source_editor.SourceEditorTab), f"{spec.key} is a tab of calculation: a CalcTab"
        elif spec.key in canvases:
            assert issubclass(spec.factory, canvas_editor.CanvasEditorTab), f"{spec.key} edits a drawing: a CanvasEditorTab"
        else:
            assert issubclass(spec.factory, source_editor.SourceEditorTab), f"{spec.key} edits sources: a SourceEditorTab"
    reserved = [spec.key for spec in tab_registry.SPECS if not isinstance(spec.factory, type)]
    assert reserved == ["tab_ac_imposed", "tab_ac_seismic", "tab_combinations", "tab_mc_torsion", "tab_sls_deformation", "tab_sls_vibration"], reserved
    assert reserved_tab.ReservedTab and all(name not in dir(reserved_tab.ReservedTab) for name in ("save", "delete"))
