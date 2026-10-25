"""The type «Données»: a tab that browses what the project holds and edits none of it, built from services on the frame (spec docs/requirements/completed/2026-10-24-type-donnees.md, issue #106; docs/ui/building-a-tab.md).

The fifth type of the decision D-05 of the spec 2026-10-23-onglets-types-et-services. It holds «Variables» (variables_tab), «Métré» (metre_tab), «Dépendances» (dependencies_tab) and «Commandes» (commands_tab): browsers, which keep no draft and save nothing, so it stands on the frame without cases (tab_frame.TabFrame, issue #107), as «Document» does.

**What a tab of the type is**: a class of parameters -- `KEY`, `MODULE` where its browser asks something of a domain, `SERVICES`, `EXPOSES` -- and nothing else (tests/test_tab_overrides.py, REQ-011); `HOOKS` is empty. Its browser is **one whole service** (D-03), which builds its own widgets, its own splitter (D-08: the type lays none, the window binds and folds the browser's, `splitter`) and keeps its state through a rebuild by `state()` / `restore()`.

**Its context** (`DataContext`) is all a browser knows of its tab, never another service (ARCH-002):
* `say(text, kind)`: the banner told what the browser read -- the export missing or older than its sources, a reading that failed -- (`provide("say")`, the frame's); the browser reads, the banner only shows (REQ-009);
* `kept(name)`: the state the window kept for the service `name` through a rebuild, so that a browser filled once at its construction is filled with it at once (ARCH-008); the frame gives it again to `restore` afterwards.

**Its default service** is the banner of the state of the export (`ExportBanner`, D-07): a warning label in the zone «top» above the browser, in the `callout` look every banner of the window has. A tab without one -- «Commandes», which reads lib/ and not the export -- names its `SERVICES` without it. No table of the export and no «Affichage» are written: no data tab asks for one (Q-002 A).

**`EXPOSES`** (D-06, ARCH-007): what other modules call on a tab by name -- the window's choice of a variable, the command palette's search -- lives in its browser. The tab declares those names, `EXPOSES = {name: service}`, and the type sets on its class, for each, an `Exposed` descriptor that reads (a bound method or an attribute) and writes on the service. No caller changes; a name the service lacks is an `AttributeError`, so `hasattr` and `getattr(tab, name, None)` stay true to it.

**The type answers once** what the window calls on any tab -- the frame's `on_shown`, `on_mode`, `view_state`, `restore`, `confirm_leave` (the phase `leave`, a reading in a thread waited for, then always True) -- and defines neither `dirty`, `save`, `current_id` nor `source`: the window tells an editor by `dirty` (update_tab_marks, the autosave), and a browser is none (REQ-006).
"""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from tab_frame import FrameContext, Service, TabFrame


class DataContext(FrameContext):
    """All a service of a data tab knows of its tab -- see the module's docstring."""

    def say(self, text, kind=None):
        """The banner told `text` -- of the kind `kind`, «warning» by default, «danger» for what failed --; an empty text takes it away. A LookupError naming the tab where it mounts no banner."""
        self.provide("say")(text, kind)

    def kept(self, name):
        """The state the window kept through a rebuild for the service `name` ({} where none), read as the service is mounted."""
        state = (getattr(self.app, "views", None) or {}).get(self.key) or {}
        return dict((state.get("services") or {}).get(name) or {})


class ExportBanner(Service):
    """The type's default service: one warning line above the browser, which the browser says through the context (`ctx.say`). It reads nothing and decides nothing (REQ-009): what it says is the browser's own words."""

    NAME = "banner"
    ZONE = "top"
    PROVIDES = ("say",)

    def mount(self, ctx):
        super().mount(ctx)
        self.widget = QWidget()
        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(6, 6, 6, 0)
        self.label = QLabel("")
        self.label.setWordWrap(True)
        self.label.setProperty("callout", "warning")
        layout.addWidget(self.label)
        self.label.setVisible(False)
        self.widget.setVisible(False)
        return self.widget

    def say(self, text, kind=None):
        """`text` shown in the look of `kind` (the theme's `callout` property, polished again so the new look takes), the line hidden where `text` is empty."""
        self.label.setText(text or "")
        self.label.setProperty("callout", kind or "warning")
        self.label.style().unpolish(self.label)
        self.label.style().polish(self.label)
        self.label.setVisible(bool(text))
        self.widget.setVisible(bool(text))


class Exposed:
    """A name of a data tab that is its service's (`EXPOSES`, ARCH-007): read on the service -- a bound method, or an attribute's value --, written on it. On the class it is the descriptor itself, so `hasattr(TabClass, name)` holds."""

    def __init__(self, name, service):
        self.name, self.service = name, service

    def __get__(self, tab, owner=None):
        if tab is None:
            return self
        return getattr(tab.service(self.service), self.name)

    def __set__(self, tab, value):
        setattr(tab.service(self.service), self.name, value)

    def __repr__(self):
        return "Exposed(%r of the service %r)" % (self.name, self.service)


class DataTab(TabFrame):
    """The type «Données» -- see the module's docstring."""

    CONTEXT = DataContext
    SERVICES = (ExportBanner,)
    VIEWS = ()
    HOOKS = ()
    EXPOSES = {}

    def __init_subclass__(cls, **kwargs):
        """The names a tab declares in `EXPOSES`, each set on its class as an `Exposed` -- read and written on the service named."""
        super().__init_subclass__(**kwargs)
        for name, service in vars(cls).get("EXPOSES", {}).items():
            setattr(cls, name, Exposed(name, service))

    def frame_body(self, widgets):
        """Two zones in a column: «top» (the banner) above the body (the browser, which stretches); the tab's splitter the first a service gives -- the type lays none (D-08)."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        for top in (True, False):
            for service, widget in widgets.items():
                if widget is not None and (service.ZONE == "top") == top:
                    layout.addWidget(widget, 0 if top else 1)
        self.splitter = next((s.splitter for s in self.services if getattr(s, "splitter", None) is not None), None)
