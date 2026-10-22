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
    for spec in tab_registry.SPECS:
        if isinstance(spec.factory, type):
            assert callable(getattr(spec.factory, "view_state", None)), spec.key


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


def test_the_tabs_that_make_domains_say_so_on_their_class():
    makes = {spec.key for spec in tab_registry.SPECS if isinstance(spec.factory, type) and getattr(spec.factory, "SYNC_DOMAIN", False)}
    assert {"tab_ac_selfweight", "tab_ac_snow", "tab_ac_wind", "tab_connections", "tab_polar", "tab_mc_tension", "tab_mc_fire",
            "tab_st_tension", "tab_python"} <= makes, makes
    assert not makes & {"tab_structure", "tab_plan", "tab_journal", "tab_variables", "tab_commands"}, makes


def test_every_editor_tab_has_the_one_structure_of_its_kind():
    """Solution B (spec 2026-10-19-base-saine-nettoyage, D-11): a tab that edits sources is a `SourceEditorTab` -- its list, its draft's actions, Ctrl+S, the question about unsaved changes, its export --, a tab that edits a drawing is a `CanvasEditorTab` -- the same, and «Annuler» --, a tab to come is a `ReservedTab`. Only the four tabs that edit no source of their own stand apart: the document's structure, and the references, «Variables», «Commandes» and «Dépendances»."""
    import canvas_editor
    import reserved_tab
    import source_editor
    # «Métré» reads the export and edits no source (spec 2026-10-21-commandes-typst-refonte, UI-003): a browser too
    browsers = {"tab_structure", "tab_variables", "tab_commands", "tab_dependencies", "tab_metre"}
    # «Projet» edits the project file itself -- its title page, its form, its documents (issues #87, #88, #90) --, no list of sources: a form of its own, guarded by its writers
    browsers.add("tab_project")
    canvases = {"tab_plan", "tab_fire", "tab_statics", "tab_schema"}
    for spec in tab_registry.SPECS:
        if not isinstance(spec.factory, type):
            continue
        if spec.key in browsers:
            assert not issubclass(spec.factory, source_editor.SourceEditorTab), spec.key
        elif spec.key in canvases:
            assert issubclass(spec.factory, canvas_editor.CanvasEditorTab), f"{spec.key} edits a drawing: a CanvasEditorTab"
        else:
            assert issubclass(spec.factory, source_editor.SourceEditorTab), f"{spec.key} edits sources: a SourceEditorTab"
    reserved = [spec.key for spec in tab_registry.SPECS if not isinstance(spec.factory, type)]
    assert reserved == ["tab_ac_imposed", "tab_ac_seismic", "tab_combinations", "tab_mc_torsion", "tab_sls_deformation", "tab_sls_vibration"], reserved
    assert reserved_tab.ReservedTab and all(name not in dir(reserved_tab.ReservedTab) for name in ("save", "delete"))
