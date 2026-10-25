"""The frame every tab built from services stands on (spec docs/requirements/completed/2026-10-24-type-document.md, issue #107, Q-001 A, D-04, ARCH-005; docs/ui/building-a-tab.md).

Until issue #107 the one host of services was `tab_host.TabHost`, built around a domain of cases saved in the project: a store of the cases, a list, «Affichage», the bar «Annuler / Enregistrer» of a case. A document has none of them, nor has a browser of the export. What every tab built from services shares, whatever it shows, was extracted from it here, **moved and not copied**:

* **a service** (`Service`): one feature with a place on the screen, written once and tested alone -- a plain class, no QWidget, that says where it goes (`ZONE`), in which views it shows (`IN_VIEWS`), what it asks of a module (`NEEDS`, checked as the tab is built), which of its methods write (`WRITERS`, guarded by tab_guard.guard_service), which names it offers to the others through the context (`PROVIDES`, `FrameContext.provide`) and which widget class it wraps whole, whose own writers the registry guards (`WIDGET`);
* **the context** (`FrameContext`, one a tab): all a service knows of its tab -- the window, the tab, the words. Each type has its own, a subclass (`tab_host.TabContext`, `document_tab.DocumentContext`); no service calls another (D-06 of the spec 2026-10-23-onglets-types-et-services);
* **the frame** (`TabFrame`): the services built in the order of `SERVICES`, what they need checked, each mounted on the context, the **phases** run service after service in that order (`shown`, `mode_changed`, `revealed`, `hidden`, `flush`, `leave`), `service(name)`, and what the window calls on any tab without speaking of a case (`FRAME_API`): `on_shown`, `on_mode`, `view_state` and `restore` through a rebuild, `confirm_leave`.

**The frame lays nothing out** (ARCH-005, ARCH-RISK-002): each type places the widgets its services mounted in `frame_body(widgets)` -- `TabHost` its splitter of three panes, its column that scrolls, its bar and «Affichage»; `DocumentTab` its pages; `DataTab` (issue #106) a top zone above the body, the splitter its browser's own. Its two other hooks are `frame_prepare` (before the services are mounted) and `frame_finish` (after the body). It defines none of the names by which the window and the autosave tell an editor from another tab -- not `dirty`, `save`, `current_id`, `current`, `id_edit` nor `list` (ARCH-007): a type that has a draft says so itself.
"""

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget

# What the window calls on any tab built on the frame, answered here once (ARCH-009 of the spec 2026-10-23-onglets-types-et-services; `tab_host.TAB_API` goes on with what a tab of cases answers).
FRAME_API = ("view", "VIEWS", "view_state", "restore", "splitter", "service", "on_shown", "on_mode", "confirm_leave")

# The phases the frame itself runs: a service answers those it has, by a method of the same name.
FRAME_PHASES = ("shown", "mode_changed", "revealed", "hidden", "flush", "leave")


class Service:
    """What every service says, its defaults: no pane, the work view, nothing asked, nothing written, nothing offered. `NAME` is how `tab.service(name)` finds it."""

    NAME = ""
    ZONE = None
    WORDS_MODULE = None     # the module whose `STRINGS` holds the service's generic words, listed in woodcore_gui_words.SERVICE_WORDS (ARCH-008); None for a service whose words are its tab's
    IN_VIEWS = ("calc",)
    NEEDS = ()
    NEEDS_MODULE = None     # the module `NEEDS` are asked of: None for its tab's `MODULE` (a domain of calculation), else the module the service writes through (a document's: issue #107, REQ-009)
    WRITERS = ()
    PROVIDES = ()           # the names of its methods the other services reach through the context (document_tab.DocumentContext.provide), never by holding it
    WIDGET = None           # the widget class it wraps whole, whose own writers (tab_guard.WRITERS) the registry guards where they are defined (tab_registry.GUARDED_WIDGETS, ARCH-008)

    def mount(self, ctx):
        """The service's widget for its zone, built on the context `ctx` (None for a service with no pane)."""
        self.ctx = ctx
        return None

    @property
    def app(self):
        return self.ctx.app

    def t(self, key, **args):
        return self.ctx.t(key, **args)

    def state(self):
        """What the service keeps across a rebuild of the window (`view_state`), {} for nothing."""
        return {}

    def restore(self, state):
        """The state `state()` gave, after a rebuild."""


def service_named(tab, name):
    """The service of `tab` named `name`, a KeyError naming the tab where it has none -- what a tab of any type answers to `service(name)` (TabFrame, library_tab.LibraryTab)."""
    found = next((s for s in tab.services if s.NAME == name), None)
    if found is None:
        raise KeyError("%s has no service %r" % (type(tab).__name__, name))
    return found


def run_phase(services, name, *args):
    """The phase `name` run by every service of `services` that has it, in their order."""
    for service in services:
        method = getattr(service, name, None)
        if method is not None:
            method(*args)


def missing_needs(services, module):
    """[(service, function)] of what the services ask of the domain `module` and it does not give."""
    return [(type(s).__name__, need) for s in services for need in getattr(s, "NEEDS", ()) if not hasattr(module, need)]


class FrameContext(QObject):
    """All a service knows of its tab: the window (`app`), the tab (`host`), its key and its words. A type's context is a subclass, built the same way, `(host, app)`."""

    def __init__(self, host, app):
        super().__init__(host)
        self.host, self.app = host, app
        self.key = host.KEY

    def t(self, key, **args):
        return self.app.t(key, **args)

    def provide(self, name):
        """The method `name` of the one service that offers it (`PROVIDES`) -- what joins two services that never hold each other: «Projet»'s acts (document_tab), a data tab's banner (data_tab, issue #106). A name offered by none or by two is an error naming the tab."""
        found = [s for s in self.host.services if name in getattr(s, "PROVIDES", ())]
        if len(found) != 1:
            raise LookupError("%s: %d services offer %r" % (type(self.host).__name__, len(found), name))
        return getattr(found[0], name)


class TabFrame(QWidget):
    """The frame -- see the module's docstring. A type is a subclass that sets `CONTEXT` and lays its body out (`frame_body`); a tab is a subclass of its type naming its parameters."""

    KEY = ""
    MODULE = None
    VIEWS = ()
    SERVICES = ()
    HOOKS = ()
    CONTEXT = FrameContext

    def __init__(self, app):
        super().__init__()
        self.app, self.t = app, app.t
        self.view = self.VIEWS[0] if self.VIEWS else None
        self.splitter = None
        self.ctx = self.CONTEXT(self, app)
        self.services = [cls() for cls in self.SERVICES]
        self.check_needs()
        self.frame_prepare()
        widgets = {s: s.mount(self.ctx) for s in self.services}
        self.frame_body(widgets)
        self.frame_finish()
        self.restore(getattr(app, "views", {}).get(self.KEY))

    def check_needs(self):
        """What the services ask of their module, given -- else the tab stops as it is built, naming itself, the service and the function (REQ-006 of the spec 2026-10-23-onglets-types-et-services, REQ-009 of issue #107)."""
        missing = []
        for service in self.services:
            module = service.NEEDS_MODULE or self.MODULE
            missing += [(name, need, module) for name, need in missing_needs([service], module)]
        if missing:
            raise TypeError("%s: %s" % (type(self).__name__, ", ".join("%s needs %s() of %s" % (s, need, getattr(module, "__name__", module)) for s, need, module in missing)))

    # --- the type's hooks ---------------------------------------------------------------

    def frame_prepare(self):
        """What the type sets before the services are mounted."""

    def frame_body(self, widgets):
        """The widgets the services mounted ({service: widget or None}, in the order of `SERVICES`) laid out on the tab: the type's, the frame lays nothing out."""

    def frame_finish(self):
        """What the type sets once its body stands, before the state kept through a rebuild is given back."""

    # --- the services -------------------------------------------------------------------

    def service(self, name):
        """The service of this tab named `name` -- the one way a test or the host reaches a widget (REQ-001, ARCH-RISK-005 of the spec 2026-10-23-onglets-types-et-services)."""
        return service_named(self, name)

    def has_service(self, name):
        return any(s.NAME == name for s in self.services)

    def phase(self, name, *args):
        """The phase `name` run by every service that has it, in the order of `SERVICES` (ARCH-002)."""
        run_phase(self.services, name, *args)

    # --- the window's calls ---------------------------------------------------------------

    def on_shown(self):
        """Brought to the front (the window's `on_tab_shown`)."""
        self.phase("shown")

    def on_mode(self, mode=None):
        """Another document shown in the window (`on_mode_changed`)."""
        self.phase("mode_changed", mode)

    def confirm_leave(self):
        """Before the tab is left -- another tab, document, the window closed --: what the services hold pending, said (`leave`); nothing is asked."""
        self.phase("leave")
        return True

    def view_state(self):
        """What the window carries through a rebuild: the splitter's sizes where the tab has one, and each named service's state."""
        return {"splitter": self.splitter.sizes() if self.splitter is not None else None,
                "services": {s.NAME: s.state() for s in self.services if s.NAME}}

    def restore(self, state):
        """The state `view_state` gave, after a rebuild -- each service its own, {} where none was kept, then the splitter's sizes --; none, each service from nothing."""
        state = state or {}
        kept = state.get("services") or {}
        for service in self.services:
            service.restore(kept.get(service.NAME) or {})
        sizes = state.get("splitter")
        if sizes and any(sizes) and self.splitter is not None and len(sizes) == self.splitter.count():   # the sizes of a splitter never laid out say nothing
            self.splitter.setSizes(sizes)

    def showEvent(self, event):
        super().showEvent(event)
        self.phase("revealed")

    def hideEvent(self, event):
        self.phase("hidden")
        super().hideEvent(event)
