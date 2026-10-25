"""The tabs built on a type and their services (spec docs/requirements/completed/2026-10-23-onglets-types-et-services.md, issue #95; calc/tools/tab_host.py, case_list_logic.py, draft_logic.py, source_store.py, field_links.py and the services of calc_tab.CalcTab).

What is held:

* **the rules have no Qt** (ARCH-005): the list's, the draft's and the store's modules import no PySide6, and their rules run here without a QApplication, on hosts made of plain attributes;
* **no service knows another** (ARCH-002): no module of a service imports another's, and a tab's services hold no other service -- what joins them is the context;
* **a writer is guarded where it is defined** (ARCH-004, ARCH-RISK-001): a store and a list refuse to write in a project open read-only, the guard finding the window through the context, and the domains' files follow a save once;
* **a service asks its domain** (REQ-006): a domain that lacks a function a service needs stops the tab as it is built, naming the tab, the service and the function;
* **the host answers the window** (ARCH-009): every name of `TAB_API`; and, on the invented domain, a case made, typed into, saved, left for another, counts one computation a change and never a dot while the form is filled (ARCH-RISK-003).
"""

TIER = "fast"  # tests/run_tests.py --fast

import ast
import os
import sys
import types

import conftest
import project
from conftest import ROOT

TOOLS = ROOT / "calc" / "tools"
LOGIC = ("case_list_logic.py", "draft_logic.py", "source_store.py")
SERVICES = ("case_list.py", "calc_form.py", "calc_modules.py", "calc_bubbles.py", "calc_display.py")
_STATE = {}


def _path():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))


def _qt():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    _path()
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _imports(name):
    tree = ast.parse((TOOLS / name).read_text(encoding="utf-8"))
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".")[0])
    return found


# --- the rules, without Qt ------------------------------------------------------------------

def test_the_rules_of_the_list_the_draft_and_the_store_import_no_qt():
    for name in LOGIC:
        assert "PySide6" not in _imports(name), name


def test_the_list_rules_run_on_a_plain_host():
    _path()
    import case_list_logic as logic
    assert logic.next_free_id(["SN-01", "sn-02"], "SN-") == "SN-03"
    assert logic.selection(None, None, ["A"]) == logic.NEW_ROW and logic.selection(None, "A", ["A"]) == "A" and logic.selection("B", "A", ["A"]) is None
    assert logic.is_mine(logic.NEW_ROW, None) and not logic.is_mine(logic.NEW_ROW, "A") and logic.is_mine("A", "A")
    rows = logic.entries([("A", "A", "")], None, lambda: "? (new)", lambda: "Roof")
    assert rows[-1] == {"id": logic.NEW_ROW, "text": "? (new)", "group": "Roof"} and len(logic.entries([("A", "A", "")], "A", None, None)) == 1
    source = {"id": "A"}
    logic.set_group(source, "Roof")
    assert source["group"] == "Roof"
    logic.set_group(source, None)
    assert "group" not in source

    calls = []

    class Host:
        loading, current_id, ids, dirty = False, "A", ["A", "B"], False

        class list:
            @staticmethod
            def ids():
                return ["A", "B"]

        def on_row_again(self, cid):
            calls.append(("again", cid))

        def confirm_leave(self):
            return True

        def load(self, cid):
            calls.append(("load", cid))

        def after_row_loaded(self, cid):
            calls.append(("after", cid))

        def reload_list(self, select=None):
            calls.append(("reload", select))
    host = Host()
    logic.row_changed(host, "A")
    logic.row_changed(host, "B")
    logic.row_changed(host, "Z")
    assert calls == [("again", "A"), ("load", "B"), ("after", "B")]
    host.loading = True
    logic.row_changed(host, "B")
    assert len(calls) == 3, "a row chosen while the form is filled is the form's, never the engineer's"


def test_the_draft_rules_run_on_a_plain_host():
    _path()
    import draft_logic
    done = []

    class Host:
        DUPLICATE_FORGETS = ("name",)
        source, current_id, dirty, ids = {"id": "A", "name": "a"}, "A", False, []

        def confirm_leave(self):
            return True

        def make_source(self):
            return {"id": "N"}

        def after_new(self):
            done.append("after_new")

        def duplicate_id(self, source):
            return "C"

        def draft(self):
            return dict(self.source)

        def fill_form(self):
            done.append("fill")

        def refresh(self):
            done.append("refresh")

        def reload_list(self, select=None):
            done.append("reload")
    host = Host()
    draft_logic.duplicate(host)
    assert host.source == {"id": "C"} and host.current_id is None and host.dirty, "a copy forgets its name and carries the dot"
    draft_logic.new(host)
    assert host.source == {"id": "N"} and host.dirty
    draft_logic.blank(host)
    assert not host.dirty, "the form once its case is gone carries no dot (issue #97)"
    assert done.count("fill") == 3 and done[-1] == "reload"


def test_the_store_refuses_an_id_taken_or_a_source_its_domain_refuses_and_writes_the_rename(tmp_path=None):
    _path()
    import re
    import tempfile
    import pathlib
    import source_store
    import validation

    def check(src, where):
        if src.get("bad"):
            raise validation.ValidationError("%s: bad" % where)
    module = types.SimpleNamespace(ID_PATTERN=re.compile(r"^[A-Za-z][\w-]*$"), FOLDER="loads/x", check_source=check)
    assert source_store.id_refusal(module, ["A-01"], {"id": "a-01"}, None) == ("taken", {"id": "a-01"}), "compared without case"
    assert source_store.id_refusal(module, ["A-01"], {"id": "A-01"}, "A-01") is None, "its own id is not taken"
    assert source_store.id_refusal(module, [], {"id": "1x"}, None)[0] == "taken"
    assert source_store.check_refusal(module, {"id": "A", "bad": True})[0] == "invalid"
    folder = pathlib.Path(tempfile.mkdtemp()) / "x"
    source_store.write(folder, {"id": "A"}, None)
    source_store.write(folder, {"id": "B"}, "A")
    assert source_store.saved_ids(folder) == ["B"], "a rename takes the old file away"


# --- the guard -----------------------------------------------------------------------------

class _ReadOnlyApp:
    read_only = True

    def __init__(self):
        self.refused = 0

    def refuse_read_only(self):
        self.refused += 1


def test_a_store_and_a_list_refuse_to_write_read_only_and_the_guard_finds_their_window():
    _qt()
    import tab_registry  # noqa: F401 -- guards every tab and service
    import case_list
    import source_store
    import tab_guard
    app = _ReadOnlyApp()
    store = source_store.SourceStore(app, types.SimpleNamespace(FOLDER="loads/never", DOMAIN="never"))
    assert getattr(source_store.SourceStore.save, tab_guard._MARK, False), "the store's save is guarded"
    assert store.save({"id": "A"}, None) is False and app.refused == 1
    cases = case_list.CaseList()
    cases.ctx = types.SimpleNamespace(app=app, store=store)
    assert tab_guard._app_of(cases) is app, "a service's window is found through its context (ARCH-RISK-001)"
    assert cases.move(["A"], "Roof") is False and app.refused == 2
    assert tab_guard._makes_domains(store) and not tab_guard._makes_domains(types.SimpleNamespace(sync_domain=False))
    for cls in tab_registry.GUARDED_SERVICES:
        for name in getattr(cls, "WRITERS", ()):
            assert any(getattr(vars(k).get(name), tab_guard._MARK, False) for k in tab_guard.own_classes(cls)), (cls.__name__, name)


# --- the services -----------------------------------------------------------------------------

def test_no_service_imports_another():
    modules = {name[:-3] for name in SERVICES}
    for name in SERVICES:
        others = (_imports(name) & modules) - {name[:-3]}
        assert not others, (name, others)


def test_the_services_of_a_document_import_no_other_service_and_hold_none():
    """ARCH-002, ARCH-006 of the spec 2026-10-24-type-document (issue #107): the services of «Projet» and «Structure du document» import none of each other's modules, and in the tabs the window builds no service holds another -- what joins them is the type's context."""
    _qt()
    documents = ("project_services.py", "structure_tab.py")
    for name in documents:
        others = (_imports(name) & {n[:-3] for n in documents + SERVICES}) - {name[:-3]}
        assert not others, (name, others)
    import tab_frame
    import woodcore_gui
    with project.using(conftest.project_copy("tab_services_documents")):
        window = woodcore_gui.MainWindow()
        try:
            for tab in window.tabs[:2]:
                assert type(tab).__name__ in ("ProjectTab", "StructureTab"), tab
                for service in tab.services:
                    held = [k for k, v in vars(service).items() if isinstance(v, tab_frame.Service)]
                    assert not held, (type(service).__name__, held)
            # the tabs of data (issue #106, ARCH-002 of the spec 2026-10-24-type-donnees): the banner and the browser never hold each other -- the browser tells the banner through the context
            import data_tab
            data = [tab for tab in window.tabs if isinstance(tab, data_tab.DataTab)]
            assert {type(tab).__name__ for tab in data} == {"VariablesTab", "MetreTab", "DependenciesTab", "CommandsTab"}, data
            for tab in data:
                for service in tab.services:
                    held = [k for k, v in vars(service).items() if isinstance(v, tab_frame.Service)]
                    assert not held, (type(tab).__name__, type(service).__name__, held)
        finally:
            for tab in window.tabs:
                if hasattr(tab, "dirty"):
                    tab.dirty = False
            conftest.dispose(window)


def _tab():
    if "tab" not in _STATE:
        _qt()
        import fake_domain
        import calc_tab
        import load_words
        import layout_store
        import woodcore_gui
        import woodcore_gui_words
        for lang, words in fake_domain.WORDS.items():
            woodcore_gui_words.STRINGS[lang].update(words)
        here = conftest.project_copy("tab_services")
        memory = {}
        with project.using(here):
            window = woodcore_gui.MainWindow()

            class Beam(calc_tab.CalcTab):
                KEY = "tab_beam"
                MODULE = fake_domain
                ID_PREFIX = "BM-"
                LIST_KEY = "fk_list"
                EMPTY_KEY = "fk_empty"
            Beam.__module__ = "fake_domain"
            fake_domain.STRINGS = load_words.STRINGS
            original = layout_store.Store
            layout_store.Store = lambda *a, **k: original(read=lambda: dict(memory), write=lambda s: memory.update(s))
            try:
                tab = Beam(window)
            finally:
                layout_store.Store = original
        _STATE.update(tab=tab, here=here, window=window)
    return _STATE["tab"]


def test_a_domain_that_lacks_what_a_service_needs_stops_the_tab_naming_all_three():
    tab = _tab()
    import calc_tab
    import fake_domain
    lacking = types.ModuleType("lacking")
    for name in dir(fake_domain):
        if name != "results":
            setattr(lacking, name, getattr(fake_domain, name))

    class Lacking(calc_tab.CalcTab):
        KEY = "tab_lacking"
        MODULE = lacking
    try:
        with project.using(_STATE["here"]):
            Lacking(_STATE["window"])
    except TypeError as exc:
        said = str(exc)
        assert "Lacking" in said and "Modules" in said and "results" in said, said
    else:
        raise AssertionError("a domain without results() was mounted")
    assert tab.services, "the tab built on the whole domain stands"


def test_the_services_hold_no_other_service_and_the_host_answers_the_window():
    tab = _tab()
    import tab_host
    for service in tab.services:
        held = [k for k, v in vars(service).items() if isinstance(v, tab_host.Service)]
        assert not held, (type(service).__name__, held)
    for name in tab_host.TAB_API:
        assert hasattr(tab, name), name
    assert tab.service("form").NAME == "form" and tab.id_edit is tab.service("identity").rows.id


def test_a_case_made_typed_and_left_for_another_computes_once_a_change_and_no_dot_while_filled():
    """ARCH-RISK-003: the invented domain has no folder for its cases' files, so its cases are written as the store writes them, not saved through the export."""
    tab = _tab()
    import fake_domain
    import source_store
    with project.using(_STATE["here"]):
        computed = []
        original = tab.ctx.compute
        tab.ctx.compute = lambda source: (computed.append(source.get("id")), original(source))[1]
        cases = tab.service("cases")
        tab.new()
        assert tab.dirty and tab.current_id is None
        computed.clear()
        tab.service("form").fields["span"].spin.setValue(6)
        assert len(computed) == 1, computed
        for cid, span in (("BM-71", 6.0), ("BM-72", 3.0)):
            source = fake_domain.new_source(cid)
            source["span"] = span
            source_store.write(tab.ctx.store.folder(), source, None)
        tab.dirty = False
        tab.reload_list()
        assert {"BM-71", "BM-72"} <= set(tab.ids)
        marks = []
        real = cases.update_list_marker

        def marked():
            marks.append(tab.ctx.loading)
            real()
        cases.update_list_marker = marked
        computed.clear()
        cases.on_list_change("BM-71")
        assert tab.current_id == "BM-71" and not tab.dirty and tab.service("form").fields["span"].spin.value() == 6
        assert len(computed) == 1, "one computation for the case loaded"
        cases.on_list_change("BM-72")
        assert tab.current_id == "BM-72" and tab.service("form").fields["span"].spin.value() == 3 and len(computed) == 2
        assert True not in marks, "the dot is never put while the form is filled"
        cases.update_list_marker = real
        tab.ctx.compute = original


# --- each service alone, on a context of its own ----------------------------------------------

class _Stub:
    """What a service may ask of a capability it does not own -- the bubbles of the norm, for a form mounted without them."""

    def __init__(self):
        self.attached = []

    def attach(self, widget, norm, ids, bare=False):
        self.attached.append((norm, tuple(ids)))

    def refresh_marks(self):
        pass


def _alone(service_cls):
    """`service_cls` mounted alone on a context of its own -- a host that holds that service and nothing else, on the invented domain (ARCH-001)."""
    _tab()
    import fake_domain
    import tab_host
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QWidget

    class Lone(QWidget):
        MODULE, KEY, WORDS, SYNC_STORE, PREFIX = fake_domain, "tab_lone", "ld", True, None
        LIST_KEY, EMPTY_KEY = "fk_list", "fk_empty"

        def __init__(self, app):
            super().__init__()
            self.app, self.refreshed = app, 0
            self.refresh_timer = QTimer(self)
            self.services = []

        def word(self, suffix, **args):
            return self.app.t("ld_" + suffix, **args)

        def refresh(self, preview=True):
            self.refreshed += 1

        def current_label(self):
            return "?"

    Lone.__module__ = "fake_domain"
    host = Lone(_STATE["window"])
    ctx = tab_host.TabContext(host, _STATE["window"])
    ctx.bubbles = _Stub()
    ctx.source = fake_domain.new_source("BM-90")
    service = service_cls()
    host.services = [service]
    widget = service.mount(ctx)
    return service, ctx, widget


def test_each_service_mounts_alone_on_a_context_of_its_own():
    """ARCH-001: a service is written once and tested alone -- mounted on a context whose host holds it and nothing else, it builds its widget where it has a pane, and does its part."""
    import calc_bubbles
    import calc_display
    import calc_form
    import calc_modules
    import case_list
    import fake_domain
    _tab()
    with project.using(_STATE["here"]):
        identity, ctx, widget = _alone(case_list.Identity)
        assert widget is not None
        identity.fill({"id": "BM-90", "name": "Poutre", "label": "Toit"})
        out = {}
        identity.collect(out)
        assert out == {"id": "BM-90", "name": "Poutre", "label": "Toit"}

        form, ctx, widget = _alone(calc_form.DeclaredForm)
        assert widget is not None and set(form.fields) == {"span", "kind", "shape", "braced", "grade", "width", "depth", "height", "side"} and ctx.bubbles.attached, "its ⓘ attached to the context's bubbles"
        source = fake_domain.new_source("BM-90")
        source["span"] = 7.0
        ctx.fill(source)
        assert ctx.draft()["span"] == 7.0 and not ctx.dirty, "filled, never touched"
        form.fields["span"].spin.setValue(8.0)
        assert ctx.dirty and ctx.host.refreshed == 1, "the engineer's change touches the context, once"

        modules, ctx, widget = _alone(calc_modules.Modules)
        ctx.compute(source)
        modules.computed()
        assert widget is modules.pane and modules.pane.ids()[:2] == ["state", "results"] and "M<sub>d</sub>" in modules.pane.modules["results"].body.text()
        module = modules.pin(fake_domain.NORM, ("5.3.4",))
        assert ctx.is_pinned(fake_domain.NORM, ("5.3.4",)) and module.spec.closable
        modules.unpin(fake_domain.NORM, ("5.3.4",))
        assert not ctx.is_pinned(fake_domain.NORM, ("5.3.4",))

        bubbles, ctx, widget = _alone(calc_bubbles.Bubbles)
        assert widget is None and ctx.bubbles is bubbles.controller, "no pane: the bubbles offered to the context"

        display, ctx, widget = _alone(calc_display.DomainDisplay)
        assert widget is None and display.view is not None
        entry = display.entries()[0]
        assert 'domain-file("fake-load", "BM-90")' in entry.call and entry.banner, "a case not saved says «Enregistrez d'abord»"

        import layer_table
        import material_copies
        from domains import dead_load_source
        _STATE["window"].views.pop("tab_lone", None)
        layers, ctx, widget = _alone(layer_table.LayerTable)
        build_up = dead_load_source.new_source("AU-90")
        build_up["chosen"] = 1.5
        ctx.fill(build_up)
        out = {}
        layers.collect(out)
        assert widget is not None and layers.table.rowCount() == 1 and out["chosen"] == 1.5 and out["layers"][0]["thickness"] == 27, out
        layers.add_layer()
        assert ctx.dirty and layers.table.rowCount() == 2, "a layer added is a change of the engineer's"
        copies, ctx, widget = _alone(material_copies.MaterialCopies)
        assert widget is not None and set(material_copies.MaterialCopies.WRITERS) == {"take_material", "keep_material"}, "its writers into the project guarded (issue #110)"

        cases, ctx, widget = _alone(case_list.CaseList)
        cases.reload_list()
        assert widget is not None and set(ctx.ids) == set(ctx.store.ids()) and "<new>" in cases.list.ids(), "the cases, and the draft's row"


def test_every_service_names_its_words_module_and_the_window_merges_it():
    """ARCH-008: a service's generic words live at the level of its module, which woodcore_gui_words merges from its registry of the services' words."""
    _qt()
    import tab_registry
    import woodcore_gui_words
    registry = {m.__name__ for m in woodcore_gui_words.SERVICE_WORDS}
    services = {s for spec in tab_registry.SPECS if isinstance(spec.factory, type) and hasattr(spec.factory, "SERVICES") for s in spec.factory.SERVICES}
    named = {s.WORDS_MODULE for s in services if s.WORDS_MODULE}
    assert named and named <= registry, (named, registry)
    for name in registry:
        module = __import__(name)
        for lang in ("fr", "de", "en"):
            assert set(module.STRINGS[lang]) <= set(woodcore_gui_words.STRINGS[lang]), (name, lang)


def test_the_file_affichage_shows_is_found_without_qt():
    """ARCH-005: the rules of «Affichage» -- the case's file, its lines, their levels -- are calc/domains/unfold_display.py's, which imports no Qt; a project laid out before v0.119 has no case's file and says so, never raises."""
    _path()
    sys.path.insert(0, str(ROOT / "calc"))
    assert "PySide6" not in {n.split(".")[0] for n in ast.parse((ROOT / "calc" / "domains" / "unfold_display.py").read_text(encoding="utf-8")).body for n in ([a.name for a in n.names] if isinstance(n, ast.Import) else [n.module or ""] if isinstance(n, ast.ImportFrom) else [])}
    from domains import unfold_display
    old = types.SimpleNamespace(domain_dir=lambda kind: None)
    assert unfold_display.case_file(old, "SN-01", "snow-load") is None
    assert unfold_display.case_file(None, "SN-01", "snow-load") is None and unfold_display.case_file(old, None, "snow-load") is None


def test_the_store_of_a_tab_on_a_type_says_its_domains_follow():
    """ARCH-004: whether the domains' files follow a save is the store's parameter (`sync_domain`), which the tab's `SYNC_STORE` gives."""
    tab = _tab()
    import tab_guard
    assert tab.ctx.store.sync_domain is type(tab).SYNC_STORE is True
    assert tab_guard._makes_domains(tab.ctx.store) and not tab_guard._makes_domains(tab), "the tab's own writers sync nothing: its store's do, once"
