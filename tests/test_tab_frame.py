"""The frame every tab built from services stands on (calc/tools/tab_frame.py; spec docs/requirements/completed/2026-10-24-type-document.md, issue #107, ARCH-001, ARCH-005).

What is held, on a bare frame and invented services: the services are built, mounted and run in the order of `SERVICES`; `service(name)` finds them and names the tab where it has none; what a service needs of its module is checked as the tab is built, the error naming the tab, the service and the function; `view_state` and `restore` carry each service's state through a rebuild; the frame lays nothing out and carries none of the names by which the window tells an editor (ARCH-007); and what was moved out of tab_host.py is the very object it re-exports, never a copy.
"""

TIER = "fast"  # tests/run_tests.py --fast

import os
import sys
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
    def __init__(self, views=None):
        self.views = views or {}
        self.read_only = False

    def t(self, key, **values):
        return key


def _frame(log, views=None):
    """A bare frame on two invented services, the first with a widget, both with a state, each saying the phases it sees into `log`."""
    import tab_frame
    from PySide6.QtWidgets import QLabel

    class Kept(tab_frame.Service):
        NAME = "kept"

        def __init__(self):
            self.value = None

        def mount(self, ctx):
            super().mount(ctx)
            log.append("mount kept")
            return QLabel("kept")

        def state(self):
            return {"value": self.value}

        def restore(self, state):
            log.append(("restore kept", dict(state)))
            self.value = state.get("value")

        def shown(self):
            log.append("shown kept")

        def mode_changed(self, mode):
            log.append(("mode kept", mode))

        def leave(self):
            log.append("leave kept")

    class Quiet(tab_frame.Service):
        NAME = "quiet"

        def mount(self, ctx):
            super().mount(ctx)
            log.append("mount quiet")
            return None

        def shown(self):
            log.append("shown quiet")

    class Frame(tab_frame.TabFrame):
        KEY = "tab_x"
        SERVICES = (Kept, Quiet)

        def frame_prepare(self):
            log.append("prepare")

        def frame_body(self, widgets):
            log.append(("body", [type(s).__name__ for s in widgets]))
            self.widgets = widgets

        def frame_finish(self):
            log.append("finish")

    return Frame(_App(views))


def test_the_services_are_built_mounted_and_run_in_their_order():
    _qt()
    log = []
    frame = _frame(log)
    assert log == ["prepare", "mount kept", "mount quiet", ("body", ["Kept", "Quiet"]), "finish", ("restore kept", {})], log
    assert frame.service("kept") is frame.services[0] and frame.has_service("quiet") and not frame.has_service("display")
    try:
        frame.service("display")
    except KeyError as exc:
        assert "Frame" in str(exc) and "display" in str(exc)
    else:
        raise AssertionError("a service the tab has not was found")
    log.clear()
    frame.on_shown()
    frame.on_mode("cu")
    assert frame.confirm_leave() is True
    assert log == ["shown kept", "shown quiet", ("mode kept", "cu"), "leave kept"], log
    assert frame.services[0].ctx is frame.ctx and frame.ctx.host is frame and frame.ctx.key == "tab_x"


def test_a_frame_keeps_each_service_s_state_through_a_rebuild():
    _qt()
    log = []
    frame = _frame(log)
    frame.service("kept").value = 7
    state = frame.view_state()
    assert state == {"splitter": None, "services": {"kept": {"value": 7}, "quiet": {}}}, state
    again = _frame([], views={"tab_x": state})
    assert again.service("kept").value == 7


def test_the_frame_lays_nothing_out_and_names_nothing_of_an_editor():
    """ARCH-005: a bare frame has no layout, no splitter; ARCH-007: it carries none of the names by which the window and the autosave tell an editor's draft."""
    _qt()
    import tab_frame
    frame = _frame([])
    assert frame.layout() is None and frame.splitter is None and frame.view is None
    for name in ("dirty", "save", "current_id", "current", "id_edit", "list", "flush_pending", "STRETCH", "display"):
        assert not hasattr(tab_frame.TabFrame, name), name
    for name in tab_frame.FRAME_API:
        assert hasattr(frame, name), name


def test_a_service_that_lacks_what_it_needs_stops_the_tab_naming_tab_service_and_function():
    _qt()
    import tab_frame
    module = types.ModuleType("writer_module")
    module.write = lambda: None

    class Asks(tab_frame.Service):
        NAME = "asks"
        NEEDS = ("write", "rename")
        NEEDS_MODULE = module

    class Frame(tab_frame.TabFrame):
        KEY = "tab_x"
        SERVICES = (Asks,)
    try:
        Frame(_App())
    except TypeError as exc:
        assert str(exc) == "Frame: Asks needs rename() of writer_module", str(exc)
    else:
        raise AssertionError("a service that lacks a function of its module was built")


def test_what_moved_out_of_the_host_is_the_object_it_re_exports():
    _qt()
    import tab_frame
    import tab_host
    for name in ("Service", "service_named", "run_phase", "missing_needs", "FRAME_API"):
        assert getattr(tab_host, name) is getattr(tab_frame, name), name
    assert issubclass(tab_host.TabHost, tab_frame.TabFrame) and issubclass(tab_host.TabContext, tab_frame.FrameContext)
    assert tab_host.TAB_API[:len(tab_frame.FRAME_API)] == tab_frame.FRAME_API and len(set(tab_host.TAB_API)) == len(tab_host.TAB_API)
    source = (TOOLS / "tab_host.py").read_text(encoding="utf-8")
    for name in ("class Service", "def service_named", "def run_phase", "def missing_needs", "def service(self", "def phase(self"):
        assert name not in source, f"{name} is written in tab_host.py again"
