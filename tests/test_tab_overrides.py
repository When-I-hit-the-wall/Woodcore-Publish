"""The editor tabs redefine the list's methods of their base only where they differ from it, each saying why (spec 2026-10-20-indices-et-niveaux, ARCH-005, a leftover of the base saine's ARCH-001).

`SourceEditorTab` (calc/tools/source_editor.py) holds the list of an editor tab -- the question about unsaved changes, the dot beside the draft, the list filled, a row chosen, rows dropped into a folder. Until v0.120 four tabs carried a copy of `update_list_marker` the same as the base's but for a name, and three a copy of `confirm_leave` differing only by their words and their «discard»; those are gone (`UNSAVED_WORDS`, `DISCARD_OPENS_FIRST`). Since the restes of issue #69 (spec 2026-10-21-restes-issue-69, ARCH-001) the four canvases -- «Schémas», «Statique», the plans, «Moment polaire» -- fill their list, choose a row and file rows in a folder through the base too, saying what differs by its hooks (`listed`, `list_selection`, `on_row_again`, `take_group`, `export_listed`…): none of them redefines a list method but the plans' `confirm_leave`. What remains redefined is redefined for a reason this table states, and a check fails on a redefinition the table does not name, on an entry no tab needs any more, and on a redefinition whose body is the base's once the names are set aside -- a copy, which `tests/test_no_duplicates.py` cannot see when its variables are renamed.
"""

import ast
import inspect
import sys
import textwrap

import conftest  # noqa: F401  -- calc/ on the path, Qt off-screen
from conftest import ROOT

if str(ROOT / "calc" / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "calc" / "tools"))

import woodcore_gui  # noqa: E402,F401  -- every tab module imported, as the window imports them

METHODS = ("confirm_leave", "update_list_marker", "reload_list", "on_list_change", "on_moved", "on_folders_changed")

# (class, method): why it is not the base's
PERMITTED = {
    ("LibraryTab", "confirm_leave"): "a library's entry is the engineer's file for every project (issue #110): asked -- saved, discarded or stayed on --, never saved without a question; the type has no `save`, so the autosave never writes a half-typed one",
    ("DrawingTab", "confirm_leave"): "finishes the export of a layer switched, then saves without asking where it can (autosave ask=True): a plan's draft is saved, not discarded",
    ("PythonTab", "confirm_leave"): "a script is saved without a question, never discarded: the question is only asked where it cannot be saved",
    ("PythonTab", "update_list_marker"): "the dot is an icon on a row of a QListWidget, the scripts' list",
    ("PythonTab", "reload_list"): "the scripts' list filters by the search field",
    ("FormulaTab", "confirm_leave"): "the domain's timers are flushed and the file handed back (autosave.leave) before the question",
    ("FormulaTab", "update_list_marker"): "a domain's list has no draft row: only the dirty state is shown",
    ("FormulaDomainsMixin", "on_folders_changed"): "a domain's folder is written by the list itself (attach_order's `groups`): the empty folders are kept and the tree filled again, no source list to rebuild",
    ("JournalTab", "confirm_leave"): "an entry is named by its index in the journal, not by an id",
    ("JournalTab", "update_list_marker"): "the dot is an icon on a row of the journal's tree",
    ("JournalTab", "on_list_change"): "a row is an item of a tree; a refusal fills the list again",
    ("AnnexTab", "update_list_marker"): "a row of the annexes' tree is keyed by a (source, excerpt) pair",
    ("AnnexTab", "on_list_change"): "a row is an item of a tree; a refusal fills the list again",
    ("PositionsTab", "update_list_marker"): "the dot is an icon on a row of the positions' tree",
    ("PositionsTab", "on_list_change"): "a row is an item of a tree; a refusal fills the list again",
    ("ProfileTab", "update_list_marker"): "the profiles' list is a QListWidget walked row by row",
    ("ProfileTab", "reload_list"): "the profiles' list is a QListWidget, filled from the catalogue and the project's own",
    ("ProfileTab", "on_list_change"): "a row is chosen by its text in a QListWidget",
}


def _tab_classes():
    """The classes of the editor tabs up to `SourceEditorTab`; a tab built on a type stops at its type, which the next tests hold, and at the frame every type stands on (tab_frame.TabFrame, issue #107)."""
    import source_editor
    import tab_frame
    import tab_host
    import tab_registry
    seen = []
    for spec in tab_registry.SPECS:
        factory = getattr(spec.factory, "func", spec.factory)   # a partial names its class
        if not inspect.isclass(factory):
            continue   # a reserved tab's factory: a function, no list of its own
        for cls in factory.__mro__:
            if cls is source_editor.SourceEditorTab or cls is object or cls in _types() or cls is tab_host.TabHost or cls is tab_frame.TabFrame:
                break
            if cls not in seen:
                seen.append(cls)
    return seen


def _types():
    """The types a tab is built on (spec 2026-10-23-onglets-types-et-services, ARCH-003): the thin bases of the host, and of the frame (issue #107: «Document»; issue #106: «Données»)."""
    import calc_tab
    import data_tab
    import document_tab
    return (calc_tab.CalcTab, data_tab.DataTab, document_tab.DocumentTab)


def _unauthorised(cls):
    """What a tab built on a type writes on its class beyond its parameters and its type's hooks -- a method, or any other name: none is allowed (REQ-005). A name a data tab declares in `EXPOSES` is allowed where the type set it, an `Exposed` (issue #106, ARCH-007), and refused where anything else stands under it."""
    import data_tab
    import tab_host
    kind = next(t for t in cls.__mro__ if t in _types())
    allowed = set(tab_host.PARAMS) | set(kind.HOOKS) | {"staticMetaObject"}
    found = []
    for klass in cls.__mro__:
        if klass is kind:
            break
        exposed = {name for name in vars(klass).get("EXPOSES", {}) if isinstance(vars(klass).get(name), data_tab.Exposed)}
        found += ["%s.%s" % (klass.__name__, name) for name in vars(klass) if not (name.startswith("__") and name.endswith("__")) and name not in allowed | exposed]
    return found


def test_a_tab_built_on_a_type_writes_only_its_parameters():
    """REQ-005 of the spec 2026-10-23-onglets-types-et-services: a tab on a type defines no method -- not `confirm_leave`, not a `lambda` assigned -- but the hooks its type declares (none for «Calcul»)."""
    import calc_tab
    import tab_registry
    built = [spec.factory for spec in tab_registry.SPECS if inspect.isclass(spec.factory) and issubclass(spec.factory, _types())]
    assert {cls.__name__ for cls in built} >= {"SnowTab", "DeadLoadTab", "ProjectTab", "StructureTab"}, built
    for cls in built:
        assert not _unauthorised(cls), _unauthorised(cls)
    assert calc_tab.CalcTab.HOOKS == ()

    class Redefines(calc_tab.CalcTab):
        KEY = "tab_x"

        def confirm_leave(self):
            return True

    class Assigns(calc_tab.CalcTab):
        refresh = lambda self, preview=True: None   # noqa: E731
    assert _unauthorised(Redefines) == ["Redefines.confirm_leave"]
    assert _unauthorised(Assigns) == ["Assigns.refresh"]


def test_a_tab_of_a_document_writes_only_its_parameters():
    """REQ-008 of the spec 2026-10-24-type-document (issue #107): «Projet» and «Structure du document» name their parameters only -- their `confirm_leave` of before is the type's --, and a tab of the type that redefines one or assigns a `lambda` is refused."""
    import document_tab
    import project_tab
    import structure_tab
    assert document_tab.DocumentTab.HOOKS == ()
    for cls in (project_tab.ProjectTab, structure_tab.StructureTab):
        assert issubclass(cls, document_tab.DocumentTab) and not _unauthorised(cls), _unauthorised(cls)
        assert "confirm_leave" not in vars(cls) and cls.confirm_leave is document_tab.DocumentTab.confirm_leave

    class Redefines(document_tab.DocumentTab):
        KEY = "tab_x"

        def confirm_leave(self):
            return True

    class Assigns(document_tab.DocumentTab):
        on_mode = lambda self, mode=None: None   # noqa: E731
    assert _unauthorised(Redefines) == ["Redefines.confirm_leave"]
    assert _unauthorised(Assigns) == ["Assigns.on_mode"]


def test_a_data_tab_writes_only_its_parameters():
    """REQ-011 of the spec 2026-10-24-type-donnees (issue #106): «Variables», «Métré», «Dépendances» and «Commandes» name their parameters only -- the names others call on «Variables» are `EXPOSES`, set by the type --, `confirm_leave` is the frame's; a tab of the type that redefines one, assigns a `lambda`, or puts one under a name it exposes is refused."""
    import data_tab
    import tab_frame
    import tab_registry
    assert data_tab.DataTab.HOOKS == ()
    built = [spec.factory for spec in tab_registry.SPECS if inspect.isclass(spec.factory) and issubclass(spec.factory, data_tab.DataTab)]
    assert {cls.__name__ for cls in built} == {"VariablesTab", "MetreTab", "DependenciesTab", "CommandsTab"}, built
    for cls in built:
        assert not _unauthorised(cls), _unauthorised(cls)
        assert "confirm_leave" not in vars(cls) and cls.confirm_leave is tab_frame.TabFrame.confirm_leave, cls.__name__

    class Redefines(data_tab.DataTab):
        KEY = "tab_x"

        def on_shown(self):
            pass

    class Assigns(data_tab.DataTab):
        on_mode = lambda self, mode=None: None   # noqa: E731

    class Hides(data_tab.DataTab):
        EXPOSES = {"pick": "browser"}
    Hides.pick = lambda self: None   # noqa: E731  -- a lambda put where the type had set the redirection
    assert _unauthorised(Redefines) == ["Redefines.on_shown"]
    assert _unauthorised(Assigns) == ["Assigns.on_mode"]
    assert _unauthorised(Hides) == ["Hides.pick"]


def _redefined():
    """{(class name, method): the class} for every list method a tab class (or a mixin of it) defines."""
    out = {}
    for cls in _tab_classes():
        for name in METHODS:
            if name in vars(cls):
                out[(cls.__name__, name)] = cls
    return out


def _shape(fn):
    """A function's body with its docstring left out and its names set aside: what a copy shares with what it copies."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
    node = tree.body[0]
    body = [s for s in node.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and isinstance(s.value.value, str))]
    for sub in ast.walk(ast.Module(body=body, type_ignores=[])):
        if isinstance(sub, ast.Name):
            sub.id = "_"
        elif isinstance(sub, ast.arg):
            sub.arg = "_"
    return ast.dump(ast.Module(body=body, type_ignores=[]))


def test_every_redefinition_of_a_list_method_says_why():
    found = _redefined()
    unnamed = sorted(set(found) - set(PERMITTED))
    stale = sorted(set(PERMITTED) - set(found))
    assert not unnamed, "a tab redefines a list method of SourceEditorTab and PERMITTED does not say why: %s" % unnamed
    assert not stale, "PERMITTED names a redefinition no tab has any more: %s" % stale
    assert all(reason.strip() for reason in PERMITTED.values())


def test_no_redefinition_is_the_base_s_own_body():
    import source_editor
    copies = [key for key, cls in _redefined().items() if _shape(getattr(cls, key[1])) == _shape(getattr(source_editor.SourceEditorTab, key[1]))]
    assert not copies, "the base's own body, under other names: %s -- remove the redefinition" % copies


def test_the_canvases_ask_their_own_question_through_the_base():
    """ARCH-005: the schemas, the static models and the polar moments ask the question about unsaved changes with their own words through `SourceEditorTab.confirm_leave`, discarding a draft never saved opening the first source."""
    import polar_tab
    import schema_tab
    import source_editor
    import statics_tab
    for cls, words in ((schema_tab.SchemaTab, "sc"), (statics_tab.StaticsTab, "st"), (polar_tab.PolarTab, "polar")):
        assert "confirm_leave" not in vars(cls), cls.__name__
        assert cls.confirm_leave is source_editor.SourceEditorTab.confirm_leave
        assert cls.UNSAVED_WORDS == (f"{words}_unsaved_title", f"{words}_unsaved") and cls.DISCARD_OPENS_FIRST, cls.__name__
