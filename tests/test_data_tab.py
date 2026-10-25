"""The type «Données» (calc/tools/data_tab.py; spec docs/requirements/completed/2026-10-24-type-donnees.md, issue #106, REQ-001, REQ-006, REQ-007, REQ-009, ARCH-007, ARCH-008).

What is held, on invented tabs of parameters only and invented services: the services are found by `service(name)`, mounted in the order of `SERVICES` and run their phases in that order; a `NEEDS` the module lacks stops the tab, naming it, the service and the function; the type has no `dirty`, `save`, `current_id` nor `source`, and `confirm_leave` waits for a service that holds a thread, then says True; the banner shows what a browser says through the context -- a warning, a danger, nothing --, and a tab without one is told so by name; `EXPOSES` reads a method and an attribute of a service and writes on it, a name or a service missing being the error of its kind; the tab's splitter is its browser's, the type laying none; a browser built once with the state the window kept (`ctx.kept`) is filled once; and a service that writes, mounted by a data tab of the window, would be guarded.
"""

TIER = "fast"  # tests/run_tests.py --fast

import os
import sys

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


def _browser_class(log):
    """An invented browser: a whole service with its own splitter, a method and an attribute others call, a state, a thread to wait for, a count of its fillings."""
    import tab_frame
    from PySide6.QtWidgets import QLabel, QSplitter

    class Browser(tab_frame.Service):
        NAME = "browser"
        NEEDS = ("read",)

        def __init__(self):
            self.fills = 0
            self.search = "found"
            self.reader = None

        def mount(self, ctx):
            super().mount(ctx)
            log.append("mount browser")
            self.kept = ctx.kept(self.NAME)
            self.splitter = QSplitter()
            self.splitter.addWidget(QLabel("left"))
            self.splitter.addWidget(QLabel("right"))
            self.fill(self.kept.get("needle", ""))
            return self.splitter

        def fill(self, needle):
            self.fills += 1
            self.needle = needle

        def state(self):
            return {"needle": self.needle}

        def restore(self, state):
            log.append(("restore browser", dict(state)))   # what mount did with the same state, not done again

        def pick(self, value):
            return "picked %s" % value

        def shown(self):
            log.append("shown browser")
            self.ctx.say("stale", "warning")

        def mode_changed(self, mode):
            log.append(("mode browser", mode))

        def leave(self):
            log.append("leave browser")
            if self.reader is not None:
                self.reader.wait()
                log.append("waited")

    return Browser


class _Module:
    @staticmethod
    def read():
        return {}


def _tab(log, views=None):
    import data_tab
    Browser = _browser_class(log)

    class Fake(data_tab.DataTab):
        KEY = "tab_fake"
        MODULE = _Module
        SERVICES = data_tab.DataTab.SERVICES + (Browser,)
        EXPOSES = {"pick": "browser", "search": "browser", "missing": "browser", "elsewhere": "nowhere"}

    return Fake, Fake(_App(views))


def test_a_tab_of_parameters_finds_its_services_and_runs_their_phases_in_order():
    _qt()
    import data_tab
    log = []
    cls, tab = _tab(log)
    assert [s.NAME for s in tab.services] == ["banner", "browser"]
    assert isinstance(tab.service("banner"), data_tab.ExportBanner) and tab.service("browser").NAME == "browser"
    assert log[:1] == ["mount browser"]
    del log[:]
    tab.on_shown()
    tab.on_mode("cu")
    assert log == ["shown browser", ("mode browser", "cu")], log
    assert tab.confirm_leave() is True and log[-1] == "leave browser"
    try:
        tab.service("nothing")
    except KeyError as exc:
        assert "Fake" in str(exc) and "nothing" in str(exc)
    else:
        raise AssertionError("a service the tab has not is a KeyError naming it")
    # the tab names its parameters only (tests/test_tab_overrides.py holds it of every data tab of the window)
    assert {n for n in vars(cls) if not n.startswith("__")} - {"staticMetaObject"} == {"KEY", "MODULE", "SERVICES", "EXPOSES", "pick", "search", "missing", "elsewhere"}
    assert data_tab.DataTab.HOOKS == () and data_tab.DataTab.VIEWS == ()


def test_a_need_the_module_lacks_stops_the_tab_naming_it():
    _qt()
    import data_tab
    Browser = _browser_class([])

    class Lacking(data_tab.DataTab):
        KEY = "tab_lacking"
        MODULE = object()
        SERVICES = (Browser,)
    try:
        Lacking(_App())
    except TypeError as exc:
        assert "Lacking" in str(exc) and "Browser" in str(exc) and "read()" in str(exc), str(exc)
    else:
        raise AssertionError("a need the module lacks stops the tab")


def test_a_data_tab_keeps_nothing_and_waits_for_a_thread_before_it_is_left():
    """REQ-006: no draft, no save -- the window tells an editor by `dirty` --; `confirm_leave` waits for what a service holds running, then says True."""
    _qt()
    import data_tab
    for name in ("dirty", "save", "current_id", "source"):
        assert not hasattr(data_tab.DataTab, name), name
    log = []
    _cls, tab = _tab(log)

    class Thread:
        def wait(self):
            log.append("thread done")
    tab.service("browser").reader = Thread()
    assert tab.confirm_leave() is True
    assert log[-3:] == ["leave browser", "thread done", "waited"], log


def test_the_banner_shows_what_the_browser_says():
    """REQ-009: a warning, a danger, nothing -- text, look and visibility; the banner reads nothing itself."""
    _qt()
    log = []
    _cls, tab = _tab(log)
    banner = tab.service("banner").label
    assert banner.isHidden() and banner.text() == ""
    tab.ctx.say("the export is older", "warning")
    assert not banner.isHidden() and banner.text() == "the export is older" and banner.property("callout") == "warning"
    tab.ctx.say("a reading failed", "danger")
    assert banner.text() == "a reading failed" and banner.property("callout") == "danger"
    tab.ctx.say("")
    assert banner.isHidden() and banner.text() == ""
    tab.on_shown()
    assert banner.isVisibleTo(tab) and banner.text() == "stale"
    # a tab that mounts no banner is told so by name
    import data_tab

    class Bare(data_tab.DataTab):
        KEY = "tab_bare"
        SERVICES = ()
    bare = Bare(_App())
    try:
        bare.ctx.say("x")
    except LookupError as exc:
        assert "Bare" in str(exc), str(exc)
    else:
        raise AssertionError("say without a banner names the tab")
    assert bare.splitter is None


def test_exposes_reads_and_writes_on_the_service():
    """ARCH-007: a method and an attribute of the service read through the tab, an attribute written on the service; a name the service lacks is an AttributeError (so hasattr stays true), a service the tab lacks a KeyError."""
    _qt()
    import data_tab
    log = []
    cls, tab = _tab(log)
    assert isinstance(vars(cls)["pick"], data_tab.Exposed) and hasattr(cls, "pick") and hasattr(cls, "search")
    assert tab.pick(3) == "picked 3"
    assert tab.search == "found"
    tab.search = "other"
    assert tab.service("browser").search == "other"
    assert not hasattr(tab, "missing")
    assert getattr(tab, "missing", None) is None
    try:
        tab.elsewhere
    except KeyError as exc:
        assert "nowhere" in str(exc)
    else:
        raise AssertionError("a service the tab lacks is a KeyError")


def test_the_splitter_is_the_browser_s_and_a_rebuild_fills_it_once():
    """D-08 and ARCH-008: the type lays no splitter of its own; the browser filled once at its construction, with the state the window kept, the frame's `restore` doing nothing again; the splitter's sizes carried by the frame."""
    _qt()
    log = []
    _cls, tab = _tab(log)
    browser = tab.service("browser")
    assert tab.splitter is browser.splitter and tab.splitter.count() == 2
    assert browser.fills == 1 and browser.needle == ""
    browser.fill("beam")
    kept = tab.view_state()
    assert kept["services"]["browser"] == {"needle": "beam"} and "banner" in kept["services"]
    log2 = []
    _cls2, again = _tab(log2, views={"tab_fake": kept})
    browser = again.service("browser")
    assert browser.fills == 1 and browser.needle == "beam", (browser.fills, browser.needle)
    assert ("restore browser", {"needle": "beam"}) in log2


def test_a_service_of_a_data_tab_of_the_window_that_writes_is_guarded():
    """ARCH-005: the registry guards the services of every tab on the frame -- a data tab's among them --; none of the four browsers writes."""
    _qt()
    import data_tab
    import tab_frame
    import tab_guard
    import tab_registry
    data_tabs = [spec.factory for spec in tab_registry.SPECS if isinstance(spec.factory, type) and issubclass(spec.factory, data_tab.DataTab)]
    assert {cls.__name__ for cls in data_tabs} == {"VariablesTab", "MetreTab", "DependenciesTab", "CommandsTab"}, data_tabs
    for cls in data_tabs:
        assert all(service in tab_registry.GUARDED_SERVICES for service in cls.SERVICES), cls.__name__
        assert cls not in tab_registry.GUARDED_TABS, cls.__name__
        assert not [s for s in cls.SERVICES if s.WRITERS], cls.__name__

    assert all(issubclass(cls, tab_frame.TabFrame) for cls in data_tabs), "the registry's rule for GUARDED_SERVICES: every tab on the frame"

    class Writer(tab_frame.Service):
        NAME = "writer"
        WRITERS = ("write_note",)

        def write_note(self):
            return True
    tab_guard.guard_service(Writer)

    class Writes(data_tab.DataTab):
        KEY = "tab_writes"
        SERVICES = data_tab.DataTab.SERVICES + (Writer,)
    app = _App()
    refused = []
    app.refuse_read_only = lambda: refused.append(1)
    tab = Writes(app)
    assert tab.service("writer").write_note() is True
    app.read_only = True
    assert tab.service("writer").write_note() is False and refused == [1]
