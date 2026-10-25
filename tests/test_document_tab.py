"""The type «Document» (calc/tools/document_tab.py; spec docs/requirements/completed/2026-10-24-type-document.md, issue #107).

What is held, on invented services and on the services of «Projet» and «Structure du document»: a tab of parameters alone finds its services (REQ-001) and the type names none by default (D-07); `confirm_leave` is the type's -- a service with a draft asks the tab's one question when it is changed and skips it when not, a service that writes at once writes what it holds pending and asks nothing (REQ-004); `save` runs in the order of the services and stops at the first refusal; the context offers a service's method to the others and refuses a name offered by none or by two (ARCH-002); the pages follow `VIEWS` and `set_view` (REQ-005); the type carries none of the names that would make the window take it for an editor of cases (ARCH-007); a service that lacks what it needs stops the tab naming it (REQ-009); a writer of «Projet» and one of «Structure» are refused in a project open read-only (REQ-006); and the preview of «Templates» is delivered in the window's thread, a stale one ignored (ARCH-009).
"""

TIER = "fast"  # tests/run_tests.py --fast

import os
import sys
import threading
import types

import conftest
from conftest import ROOT

TOOLS = ROOT / "calc" / "tools"


def _qt():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


class _App:
    def __init__(self, read_only=False, views=None):
        self.read_only = read_only
        self.views = views or {}
        self.marks = 0
        self.refused = 0

    def t(self, key, **values):
        return key

    def update_tab_marks(self):
        self.marks += 1

    def refuse_read_only(self):
        self.refused += 1


def _services(log):
    """A service with a draft (a title page) and one that writes at once (a tree), on pages of two views."""
    import tab_frame
    from PySide6.QtWidgets import QLabel

    class Draft(tab_frame.Service):
        NAME = "draft"
        ZONE = "page"
        IN_VIEWS = ("one",)
        PROVIDES = ("answer",)
        refuse = False

        def mount(self, ctx):
            super().mount(ctx)
            return QLabel("draft")

        def loaded(self):
            log.append("loaded draft")

        def lock(self):
            log.append("lock draft")

        def save(self):
            log.append("save draft")
            if self.refuse:
                return False
            self.ctx.dirty = False
            return True

        def discard(self):
            log.append("discard draft")
            self.ctx.reload()

        def answer(self):
            return 42

        def view_set(self, key, enter):
            log.append(("view", key, enter))

    class AtOnce(tab_frame.Service):
        NAME = "at_once"
        ZONE = "page"
        IN_VIEWS = ("two",)

        def mount(self, ctx):
            super().mount(ctx)
            self.pending = ["an edit"]
            self.written = []
            return QLabel("at once")

        def flush(self):
            self.written += self.pending
            self.pending = []

        def leave(self):
            self.flush()

        def save(self):
            log.append("save at_once")
            return True

    return Draft, AtOnce


def _tab(log, app=None, services=None):
    import document_tab
    draft, at_once = _services(log)

    class Paper(document_tab.DocumentTab):
        KEY = "tab_paper"
        VIEWS = ("one", "two")
        SERVICES = services or (draft, at_once)
        UNSAVED_WORDS = ("paper_title", "paper_unsaved")
    return Paper(app or _App())


def test_a_tab_of_parameters_alone_finds_its_services_and_the_type_names_none():
    _qt()
    import document_tab
    log = []
    tab = _tab(log)
    assert document_tab.DocumentTab.SERVICES == () and document_tab.DocumentTab.HOOKS == () and document_tab.DocumentTab.VIEWS == ()
    assert tab.service("draft").NAME == "draft" and tab.service("at_once").NAME == "at_once"
    assert log == ["loaded draft", "lock draft"], "the files are read once as the tab is built, then what may be written enabled"
    assert not tab.dirty and tab.view == "one"


def test_confirm_leave_asks_for_a_draft_changed_and_writes_what_is_pending_at_once():
    _qt()
    import autosave
    asked = []
    saved = autosave.confirm
    autosave.confirm = lambda app, tab, title, text, discard=None, save=None: asked.append((title, text, discard)) or True
    try:
        log = []
        tab = _tab(log)
        at_once = tab.service("at_once")
        assert tab.confirm_leave() is True and asked == [], "nothing changed: no question"
        assert at_once.written == ["an edit"] and not at_once.pending, "what a service writing at once held was written"
        tab.service("draft").ctx.touch()
        tab.service("draft").ctx.touch()
        assert tab.dirty and tab.app.marks == 1, "one flag a tab, the marks once"
        at_once.pending = ["another"]
        assert tab.confirm_leave() is True
        assert len(asked) == 1 and asked[0][:2] == ("paper_title", "paper_unsaved") and asked[0][2] == tab.discard
        assert at_once.written == ["an edit", "another"]
        tab.flush_pending()
        tab.discard()
        assert not tab.dirty and "discard draft" in log
    finally:
        autosave.confirm = saved


def test_save_runs_in_the_order_of_the_services_and_stops_at_the_first_refusal():
    _qt()
    log = []
    tab = _tab(log)
    log.clear()
    tab.dirty = True
    assert tab.save() is True and log == ["save draft", "save at_once"] and not tab.dirty
    log.clear()
    tab.service("draft").refuse = True
    assert tab.save() is False and log == ["save draft"]


def test_the_context_offers_one_service_s_method_and_refuses_none_or_two():
    _qt()
    import tab_frame
    log = []
    tab = _tab(log)
    assert tab.ctx.provide("answer")() == 42
    for name in ("nothing",):
        try:
            tab.ctx.provide(name)
        except LookupError as exc:
            assert "Paper" in str(exc) and name in str(exc)
        else:
            raise AssertionError("a name no service offers was found")
    draft, at_once = _services(log)

    class Twice(tab_frame.Service):
        NAME = "twice"
        PROVIDES = ("answer",)

        def answer(self):
            return 0
    tab = _tab(log, services=(draft, Twice))
    try:
        tab.ctx.provide("answer")
    except LookupError as exc:
        assert "2 services" in str(exc)
    else:
        raise AssertionError("a name two services offer was found")


def test_the_pages_follow_the_views_and_set_view_tells_the_services():
    _qt()
    log = []
    tab = _tab(log)
    assert tab.pages.count() == 2 and tab.pages.currentIndex() == 0
    tab.set_view("two", enter=False)
    assert tab.view == "two" and tab.pages.currentIndex() == 1 and ("view", "two", False) in log
    tab.set_view("three")
    assert tab.view == "two", "a view the tab has not is ignored"
    assert tab.splitter is None, "no service gives a splitter"


def test_the_type_carries_no_name_of_an_editor_of_cases():
    """ARCH-007: `dirty` and `save` for the draft, never `current_id`, `current`, `id_edit` nor `list` -- the window would take the tab for an editor of cases, and the autosave its draft for one saved once."""
    _qt()
    import document_tab
    import tab_frame
    for name in ("current_id", "current", "id_edit", "list", "display", "STRETCH"):
        assert not hasattr(document_tab.DocumentTab, name), name
        assert not hasattr(tab_frame.TabFrame, name), name
    for name in ("dirty", "save", "discard", "flush_pending", "confirm_leave", "set_view", "on_mode", "on_shown", "view_state", "restore", "service"):
        assert hasattr(document_tab.DocumentTab, name), name
    assert isinstance(document_tab.DocumentTab.dirty, property)


def test_a_service_of_a_document_that_lacks_what_it_needs_stops_the_tab():
    _qt()
    import document_tab
    import project_services
    import structure_tab
    lacking = types.ModuleType("structure")

    class Lacks(structure_tab.DocumentStructure):
        NEEDS_MODULE = lacking

    class Paper(document_tab.DocumentTab):
        KEY = "tab_paper"
        SERVICES = (Lacks,)
    try:
        Paper(_App())
    except TypeError as exc:
        assert str(exc).startswith("Paper: Lacks needs tree() of structure"), str(exc)
    else:
        raise AssertionError("a service whose module lacks a function was mounted")
    assert project_services.ProjectActions.NEEDS_MODULE.__name__ == "project_template"


def test_a_writer_of_projet_and_one_of_structure_are_refused_read_only():
    """REQ-006, ARCH-008: guarded where they are defined -- «Appliquer au projet…» on its service, a write of the structure on the widget the service wraps."""
    _qt()
    import tab_guard
    import woodcore_gui  # noqa: F401 -- the registry guards the writers as the window imports it
    import project_services
    import structure_tab
    app = _App(read_only=True)
    actions = project_services.ProjectActions()
    actions.ctx = types.SimpleNamespace(app=app, dirty=False)
    for name in project_services.ProjectActions.WRITERS:
        assert getattr(vars(project_services.ProjectActions)[name], tab_guard._MARK, False), name
    assert actions.write_apply_form("builtin:bfh") is False and actions.write_create_document("cu", "x") is False and app.refused == 2
    owner = next(k for k in tab_guard.own_classes(structure_tab.StructureView) if "write_enabled" in vars(k))
    assert getattr(vars(owner)["write_enabled"], tab_guard._MARK, False), owner.__name__
    view = types.SimpleNamespace(app=app)
    assert structure_tab.StructureView.write_enabled(view, "a", True) is False and app.refused == 3, "a section switched in a project open read-only"
    assert "write_apply_form" not in tab_guard.WRITERS and "write_create_document" not in tab_guard.WRITERS


def test_the_preview_of_templates_is_delivered_in_the_window_s_thread_and_a_stale_one_ignored():
    """ARCH-009: the thread's `done` reaches a QObject of the window's thread, not a plain service's method."""
    qt = _qt()
    import time
    import project_services
    import template_preview
    from PySide6.QtWidgets import QWidget
    seen = []
    page = QWidget()
    receiver = project_services._Receiver(page, lambda *a: seen.append(("done", threading.current_thread() is threading.main_thread())),
                                          lambda *a: seen.append(("failed", threading.current_thread() is threading.main_thread())))
    saved = template_preview.prepare
    worker_thread = []
    template_preview.prepare = lambda *a: worker_thread.append(threading.current_thread() is threading.main_thread()) or "shown"
    try:
        worker = project_services._Preview(1, None, "cu", None, None)
        worker.done.connect(receiver.done)
        worker.failed.connect(receiver.failed)
        worker.start()
        worker.wait(10000)
        end = time.monotonic() + 5
        while not seen and time.monotonic() < end:
            qt.processEvents()
    finally:
        template_preview.prepare = saved
    assert worker_thread == [False], "the preview was not built off the window's thread"
    assert seen == [("done", True)], seen
    stale = types.SimpleNamespace(generation=2)   # no pane, no banner: a stale preview touches nothing
    assert project_services.ProjectTemplates.on_preview_done(stale, 1, "shown", "cu") is None
    assert project_services.ProjectTemplates.on_preview_failed(stale, 1, "build_failed", "x") is None
    page.deleteLater()
