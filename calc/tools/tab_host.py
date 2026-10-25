"""A tab built on a type, from services written once (spec docs/requirements/completed/2026-10-23-onglets-types-et-services.md, issue #95, variant F; docs/ui/window.md «Construire un onglet»).

The engineer, 23.10.2026: «on ne copie plus des onglets». Until issue #95 (v0.125) a tab inherited a stack of classes and mixins, and a feature it needed was sometimes written a second time beside the first. A tab built on a type is **a thin class of parameters** -- its key, its domain, its id prefix, its words, and, where it differs from its type, the list of its services --, and the type (`calc_tab.CalcTab`, the first) says which services every tab of its kind has by default.

**A service** is one feature with a place on the screen, written once and tested alone (tests/test_tab_services.py): the list of the cases, the identity, the form, the right pane of modules, «Affichage»… It is a plain class -- no ABC, no common base with a QWidget, whose metaclass mixes with neither (ARCH-RISK-016) -- that says where it goes (`ZONE`: "left", "centre", "right", or None for one with no pane of its own), in which views it shows (`IN_VIEWS`), what it asks of the domain (`NEEDS`, checked when the tab is built: REQ-006), which of its methods write (`WRITERS`, guarded by tab_guard.guard_service: ARCH-004), and whose words live at the level of its module (`STRINGS`). `mount(ctx)` gives its widget.

**The context** (`TabContext`, one a tab) is all a service knows: the domain, the case as it is saved, the id open, whether the form is being filled (`loading`), the store of the cases (source_store.SourceStore), the linkable numbers (field_links.LinkSet), what the domain computed. **No service calls another** (D-06): what joins them goes through the context, in three ways only (ARCH-002) --
* the draft is assembled from **contributions**: a service of the centre says `fill(src)` and `collect(src)`, and `ctx.fill` / `ctx.draft` call them in the order of `SERVICES`, the links last;
* the sequences that must happen in order are **phases** the host runs, service after service in the order of `SERVICES`: `computed` (the domain has said what it says of the draft), `saved`, `before_display`, `hidden`; a service answers the phases it has;
* what needs no order is a **signal** of the context: a field and the results it goes into lit (`lit`), the elements whose keys an element hovered names lit and framed (`litKeys`, spec 2026-10-23-onglet-vent-briques, ARCH-004), a field to take to (`focusRequested`), an excerpt or a block pinned or taken out (`excerptPinned`, `excerptUnpinned`, `blockPinned`, `pinsChanged`).

**The host** (`TabHost`) stands on the frame every tab built from services shares (tab_frame.py, issue #107: `Service`, the phases, `service(name)`, the services built and mounted, moved there and re-exported here); it lays out the three panes, holds the save bar and the shortcut Ctrl+S, and answers once, for every tab of every type, what the window asks of a tab (`TAB_API`, ARCH-009): a tab on a type defines no method of its own but the hooks its type declares (`HOOKS`), which tests/test_tab_overrides.py holds (REQ-005).
"""

import copy

from PySide6.QtCore import QEvent, QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QSplitter, QStackedWidget, QVBoxLayout, QWidget

import autosave
import cards
import case_list_logic
import display_view
import draft_logic
import field_links
import project
import source_store
import validation
import views
from domains import dependencies
from domains.contracts import Message
from i18n import strings
from source_editor import save_shortcut
from tab_frame import FRAME_API, FrameContext, Service, TabFrame, missing_needs, run_phase, service_named  # noqa: F401 -- moved to tab_frame.py (issue #107), re-exported: a score of modules import them from here

OPTION_DELAY_MS = 150   # a pause in typing before «Affichage» compiles again

# What the window, the autosave and the palette call on a tab built on a type -- answered here once, never by the tab (ARCH-009, ARCH-RISK-004).
# What every tab on the frame answers is tab_frame.FRAME_API; what a tab of cases answers besides follows it (issue #107, REQ-005).
TAB_API = FRAME_API + ("set_view", "display", "dirty", "current_id", "source", "save", "update_list_marker", "reload_list", "lists_object", "open_object",
                       "GRAPH_KIND", "new", "refresh", "fill_form", "draft", "id_edit", "stop", "word")


# What a tab built on a type may say on its class -- its parameters, never a method (REQ-005, tests/test_tab_overrides.py): anything else it would write is a hook its type declares (`HOOKS`).
PARAMS = ("KEY", "MODULE", "ID_PREFIX", "LIST_KEY", "EMPTY_KEY", "WORDS", "PREFIX", "VIEWS", "SERVICES", "HOOKS", "GRAPH_KIND", "SYNC_DOMAIN", "SYNC_STORE",
          "DUPLICATE_FORGETS", "UNSAVED_WORDS", "STRETCH", "EXPOSES")


def _n(value):
    text = ("%.3f" % value).rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


def words_of(params):
    """A message's values as its words print them: a number short, the rest as it is."""
    return {k: _n(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v for k, v in params.items()}


def excerpt_module_id(norm, ids):
    """The id of the module of a pinned excerpt, `x:<norm file>:<id>+<id>` -- written here alone, and read back by `excerpt_of_module`."""
    return "x:" + norm + ":" + "+".join(ids)


def excerpt_of_module(module_id):
    """(norm file, ids) of a pinned excerpt's module id."""
    _x, norm, ids = module_id.split(":", 2)
    return norm, tuple(ids.split("+"))


class Hover(QObject):
    """The pointer entering and leaving a widget, told to `enter()` and `leave()`: what lights a field and the results it goes into (UI-004) -- shared by the form and the results, which never import each other."""

    def __init__(self, parent, enter, leave):
        super().__init__(parent)
        self.enter, self.leave = enter, leave

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Enter:
            self.enter()
        elif event.type() == QEvent.Type.Leave:
            self.leave()
        return False


class TabContext(FrameContext):
    """All a service knows of its tab -- see the module's docstring; the window, the tab and its words are the frame's (tab_frame.FrameContext)."""

    lit = Signal(object, object)          # (fields, result names) lit, both empty for none
    litKeys = Signal(object, object)      # (keys lit, keys framed) of an element hovered -- a cell, a row, a surface (ARCH-004); both empty for none
    focusRequested = Signal(str)          # a field a message was clicked for
    excerptPinned = Signal(str, object)   # (norm file, excerpt ids) to pin under «Résultats»
    excerptUnpinned = Signal(str, object)
    blockPinned = Signal(str)             # a block of the form to pin under «Résultats» as a module of its own (ARCH-005)
    viewChanged = Signal(str)             # a drawing's view turned, zoomed or set (`view_state`): its other bodies draw again
    pinsChanged = Signal()                # an excerpt pinned or taken out: the ⓘ say it again
    projectDataChanged = Signal()         # a file of the project the form reads was written (a library the layers choose from): what lists it, again
    overviewShown = Signal(bool)          # every case at a glance shown in the centre, or the case open again (spec 2026-10-24-poids-propre-repense, P06)

    def __init__(self, host, app):
        super().__init__(host, app)
        self.module = host.MODULE
        self.store = source_store.SourceStore(app, host.MODULE, sync_domain=host.SYNC_STORE)
        self.links = field_links.LinkSet(app, host.MODULE, app.t, self.touch, self.draft, lambda: (self.draft().get("id") or ""))
        self.source, self.current_id, self.dirty, self.loading = None, None, False, False
        self.ids = []
        self.layout = None            # layout_store's store: None the user's settings, a test's in memory
        self.bubbles = None           # the norm's bubbles, where the tab has them (norm_bubble.Bubbles)
        self.pinned = set()           # the ids of the excerpts' modules pinned (calc_modules.Modules)
        self.computed_source = {}
        self.view_states = {}         # a drawing's own view -- its rotation, its zoom, its direction --, by its key, shared by its bodies in the form, the pane and a window (ARCH-005, T87)
        self.pane_modules = []        # the modules a service gives the right pane (module_pane.ModuleSpec), given as it mounts, before the pane does: placed after «État du calcul» (spec 2026-10-24-poids-propre-repense, UI-002)
        self.overview = False         # whether the centre shows every case at a glance rather than the case open (P06)
        self.reset()

    def reset(self):
        """What the domain said of the draft forgotten: before it is computed again."""
        self.messages, self.instance, self.reason, self.drawing, self.chart, self.edges = [], None, "", None, None, {}
        self.blocks, self._links = {}, None   # the blocks' data (`blocks(src, instance)`), and the links of the elements' keys, read on the first hover (`key_links(src, instance)`)

    # --- words ---------------------------------------------------------------------

    def tl(self, text):
        return strings.translate(text, self.app.lang)

    def declaration(self):
        return self.module.declaration()

    def param(self, name, default=None):
        """A parameter of the tab -- its `KEY`, `LIST_KEY`, `WORDS`… -- as its class names it."""
        return getattr(type(self.host), name, default)

    def prefix(self):
        """The prefix of the domain's words in the tab's (`sn_`): the tab's `PREFIX`, else its declaration's (ARCH-RISK-007: a tab with no declared form names its own)."""
        return self.param("PREFIX") or self.declaration().prefix

    def word(self, suffix, **args):
        """A sentence of the tab's own that names its object, whole (D-12)."""
        return self.host.word(suffix, **args)

    def message_text(self, message):
        """A message in the window's words: the domain's `<prefix>msg_<code>`, the tab's for a source it could not compute."""
        if message.code == "invalid":
            return self.word("invalid", error=message.params.get("error", ""))
        params = message.params
        localise = getattr(self.module, "message_params", None)
        if localise is not None:
            params = localise(params, self.app.lang)   # what the domain names in the window's language (a material's name, a panel's loading: issue #112)
        return self.t(self.prefix() + "msg_" + message.code, **words_of(params))

    # --- what the tab does, for the services that ask it -----------------------------------

    def confirm_leave(self):
        return self.host.confirm_leave()

    def load(self, cid):
        self.host.load(cid)

    def current_label(self):
        return self.host.current_label()

    def after_archive(self):
        self.host.after_archive()

    def export_listed(self, text):
        self.host.export_listed(text)

    def reload_list(self, select=None):
        self.host.reload_list(select)

    def update_list_marker(self):
        self.host.update_list_marker()

    def new(self):
        """«Nouveau» of the list: the choice a service offers first where one does (`pick_new`: the permanent loads' templates, issue #111), else a new case."""
        chooser = next((s for s in self.host.services if hasattr(s, "pick_new")), None)
        if chooser is not None:
            chooser.pick_new()
        else:
            self.host.new()

    def new_from(self, source):
        """A new case from `source` -- a build-up made from a template."""
        self.host.new_from(source)

    def show_overview(self, on):
        """Every case at a glance in the centre (`on`), or the case open again: said to the host, which shows it, and to the services."""
        self.overview = bool(on)
        self.overviewShown.emit(self.overview)

    def duplicate(self):
        self.host.duplicate()

    def delete(self):
        self.host.delete()

    def save(self):
        return self.host.save()

    def refresh(self):
        """The draft computed again, with no change of the engineer's -- after a file of the project it reads was written."""
        self.host.refresh()

    def fail(self, message):
        """A refusal said in the tab's own words (autosave.refuse)."""
        return self.host.fail(message)

    def save_if_needed(self):
        """The case saved before «Affichage» shows its file -- what it shows is the file as the save writes it (REQ-005, D-4, D-7 of the spec 2026-10-23-neige-correctifs-issues-96-99): only a case changed, that the calculation can read, in a project not open read-only, where the guard would refuse it at every switch."""
        if self.dirty and not getattr(self.app, "read_only", False) and not self.blocked():
            self.save()

    # --- the draft: filled, assembled, touched ------------------------------------------

    def contributors(self):
        return [s for s in self.host.services if hasattr(s, "fill") or hasattr(s, "collect")]

    def fill(self, src):
        """The source `src` into the form: each contributor in the order of `SERVICES`, then the links; `loading` while it lasts, so that nothing it changes is a change of the engineer's."""
        self.loading = True
        try:
            self.links.forget_values()
            for service in self.contributors():
                if hasattr(service, "fill"):
                    service.fill(src)
            self.links.fill(src)
        finally:
            self.loading = False

    def draft(self):
        """The draft: the case as saved, each contributor's part over it, the links last (with the schema version that says whether any is left)."""
        s = copy.deepcopy(self.source or {})
        for service in self.contributors():
            if hasattr(service, "collect"):
                service.collect(s)
        self.links.collect(s)
        return s

    def touch(self, *_ignored):
        """A change of the engineer's -- never one the form makes as it is filled: tested here, by the one that says it, and not by each service (ARCH-RISK-003)."""
        if self.loading:
            return
        self.dirty = True
        self.host.refresh(preview=False)
        self.host.refresh_timer.start()

    # --- what the domain says of the draft -------------------------------------------

    def compute(self, source):
        """The draft computed (D-10 of v0.117): the domain's messages, its instance, the graph of what each result is computed from, its drawing and its chart -- never a calculation of the tab's. `computed_source` is the draft they were computed from, which the services read in the phase `computed` rather than assemble it again."""
        self.reset()
        self.computed_source = source
        module = self.module
        self.messages = list(module.messages(source)) if hasattr(module, "messages") else []
        if not any(m.severity == "error" for m in self.messages):
            try:
                module.check_source(source, "%s/%s.json" % (module.FOLDER, source.get("id") or "?"))
                self.instance = module.build_instance(source, project.current())
                extra = module.extra_dependencies(self.instance) if hasattr(module, "extra_dependencies") else None
                self.edges = dependencies.graph(self.instance, extra)
                if hasattr(module, "figure_svg"):
                    self.drawing = module.figure_svg(source, self.app.lang)
            except (validation.ValidationError, ValueError, KeyError, TypeError, ZeroDivisionError) as exc:
                self.reason = str(exc)
                self.messages.insert(0, Message("invalid", None, "error", {"error": str(exc)}))
        if hasattr(module, "chart"):
            try:
                self.chart = module.chart(source)
            except (KeyError, TypeError, ValueError):
                self.chart = None
        if hasattr(module, "blocks"):
            # the blocks' data even with no instance: a block may say what the source holds (the table of the norm chosen) while the calculation waits on another field
            try:
                self.blocks = module.blocks(source, self.instance) or {}
            except (validation.ValidationError, KeyError, TypeError, ValueError, ZeroDivisionError):
                self.blocks = {}

    def blocked(self):
        """Whether a message stops the calculation."""
        return any(m.severity == "error" for m in self.messages)

    # --- what joins the services: a highlight, a field to take to, an excerpt pinned ---------

    def field_vars(self):
        """{variable: field key} of the declared fields that name a variable of the export (`Field.var`)."""
        if not hasattr(self.module, "declaration"):
            return {}
        decl = self.declaration()
        return {f.var: f.key for f in decl.fields if f.var}

    def hover_result(self, name):
        """A row of «Résultats» hovered: the fields it is computed from, near or far, and the results between them lit; None, everything plain. Returns (fields, names)."""
        if name is None:
            return self.light(set(), set())
        used = dependencies.upstream(name, self.edges)
        by_var = self.field_vars()
        return self.light({by_var[v] for v in used if v in by_var}, used | {name})

    def hover_field(self, key):
        """A field hovered: itself and the results it goes into lit; None, everything plain."""
        if key is None:
            return self.light(set(), set())
        var = next((v for v, k in self.field_vars().items() if k == key), None)
        return self.light({key}, (dependencies.downstream(var, self.edges) | {var}) if var else set())

    def light(self, fields, names):
        self.lit.emit(fields, names)
        return fields, names

    def element_links(self):
        """{element id: {"lit": keys, "emphasis": keys}} the domain gives of what each element of its tab is read from (`key_links(src, instance)`), read once per calculation; {} for a domain with none."""
        if self._links is None:
            module = self.module
            self._links = (module.key_links(self.computed_source, self.instance) or {}) if hasattr(module, "key_links") and self.instance is not None else {}
        return self._links

    def hover_element(self, element_id):
        """An element hovered -- a cell, a row, a surface -- by its opaque id: itself and the keys the domain links it to lit, the keys it names framed (`litKeys`); None, everything plain. Returns (lit, emphasis). No key is read here (ARCH-004)."""
        if element_id is None:
            lit, emphasis = set(), set()
        else:
            entry = self.element_links().get(element_id) or {}
            lit, emphasis = set(entry.get("lit", ())) | {element_id}, set(entry.get("emphasis", ()))
        self.litKeys.emit(lit, emphasis)
        return lit, emphasis

    def pin_block(self, key):
        """A block's 📌: the block a module of the right pane (ARCH-005)."""
        self.blockPinned.emit(key)

    def view_state(self, key):
        """The view of the drawing `key` -- what its bodies in the form, the pane and a window turn and zoom together, each drawing its own (T87)."""
        return self.view_states.setdefault(key, {})

    def focus_field(self, key):
        """A message clicked (T49): the field it names taken to."""
        self.focusRequested.emit(key)

    def pin_excerpts(self, norm, ids):
        self.excerptPinned.emit(norm, tuple(ids))

    def unpin_excerpts(self, norm, ids):
        self.excerptUnpinned.emit(norm, tuple(ids))

    def is_pinned(self, norm, ids):
        """Whether the excerpts `ids` of `norm` are pinned -- what a bubble's click and its ⓘ ask."""
        return excerpt_module_id(norm, tuple(ids)) in self.pinned


class TabHost(display_view.DisplayTab, TabFrame):
    """The host of a tab built on a type -- see the module's docstring. A type is a subclass naming its `SERVICES` and its `HOOKS`; a tab is a subclass of its type naming its parameters. What does not speak of a case -- the services built and mounted, their phases, `service(name)`, the window's `on_mode` -- is its frame's (tab_frame.TabFrame, issue #107); the order a tab of cases is built in is the frame's three hooks: the store's new source (`frame_prepare`), the splitter, the centre and «Affichage» (`frame_body`), the timer and Ctrl+S (`frame_finish`)."""

    KEY = ""
    MODULE = None
    ID_PREFIX = ""
    LIST_KEY = ""
    EMPTY_KEY = ""
    WORDS = ""
    VIEWS = views.CALC_VIEWS
    SERVICES = ()
    HOOKS = ()
    CONTEXT = TabContext
    GRAPH_KIND = None
    SYNC_DOMAIN = False     # its «Enregistrer» and «Supprimer» refuse a project open read-only before they ask anything; the domains' files follow its store's and its services' writers, once (tab_guard)
    SYNC_STORE = True       # its cases are domains with a file of their own: the store's writers are followed by domain_file.sync (source_store.SourceStore `sync_domain`)
    PREFIX = None
    DUPLICATE_FORGETS = ("name",)
    UNSAVED_WORDS = None
    STRETCH = (2, 6, 4)

    def frame_prepare(self):
        self.live = False
        self.ctx.source = self.make_source()

    def frame_body(self, widgets):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self._zone("left", widgets))
        self.splitter.addWidget(self._centre(widgets))
        self.splitter.addWidget(self._zone("right", widgets))
        self.install_display(self.KEY)
        for index, stretch in enumerate(self.STRETCH):
            self.splitter.setStretchFactor(index, stretch)
        layout.addWidget(self.splitter, 1)

    def frame_finish(self):
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.setInterval(OPTION_DELAY_MS)
        self.refresh_timer.timeout.connect(self.request_preview)
        save_shortcut(self)

    # --- the zones ------------------------------------------------------------------

    def _zone(self, zone, widgets):
        """The widgets of the services of `zone`, one under the other; the zone's own widget where it has only one."""
        found = [w for s, w in widgets.items() if s.ZONE == zone and w is not None]
        if len(found) == 1:
            return found[0]
        holder = QWidget()
        column = QVBoxLayout(holder)
        column.setContentsMargins(0, 0, 0, 0)
        for widget in found:
            column.addWidget(widget, 1)
        return holder

    def _centre(self, widgets):
        """The centre: the services of the centre in a column that scrolls, then «Annuler les modifications» and «Enregistrer»."""
        panel = QWidget()
        column = QVBoxLayout(panel)
        column.setContentsMargins(0, 0, 0, 0)
        scroll, self.form = cards.column()
        column.addWidget(scroll, 1)
        for service, widget in widgets.items():
            if service.ZONE == "centre" and widget is not None:
                self.form.addWidget(widget)
        self.form.addStretch(1)
        actions = QHBoxLayout()
        revert = QPushButton(self.word("revert"))
        revert.clicked.connect(self.revert)
        save = QPushButton(self.word("save"))
        save.setDefault(True)
        save.clicked.connect(self.save)
        actions.addStretch(1)
        actions.addWidget(revert)
        actions.addWidget(save)
        column.addLayout(actions)
        # a service that shows every case at a glance (`overview_widget`, P06): the centre holds it beside the case open, the context saying which is shown
        overview = next((s for s in widgets if hasattr(s, "overview_widget")), None)
        if overview is None:
            return panel
        stack = QStackedWidget()
        stack.addWidget(panel)
        stack.addWidget(overview.overview_widget())
        self.ctx.overviewShown.connect(lambda on: stack.setCurrentIndex(1 if on else 0))
        return stack

    # --- the state the window reads, kept in the context ---------------------------------

    source = property(lambda self: self.ctx.source, lambda self, v: setattr(self.ctx, "source", v))
    current_id = property(lambda self: self.ctx.current_id, lambda self, v: setattr(self.ctx, "current_id", v))
    dirty = property(lambda self: self.ctx.dirty, lambda self, v: setattr(self.ctx, "dirty", v))
    loading = property(lambda self: self.ctx.loading, lambda self, v: setattr(self.ctx, "loading", v))
    ids = property(lambda self: self.ctx.ids, lambda self, v: setattr(self.ctx, "ids", v))
    instance = property(lambda self: self.ctx.instance)

    @property
    def id_edit(self):
        """The id field of the identity row, which the autosave asks before it saves (autosave.id_field)."""
        return self.service("identity").rows.id if self.has_service("identity") else None

    # --- the words ---------------------------------------------------------------------

    def word(self, suffix, **args):
        """A sentence that names the tab's object, whole (`<WORDS>_<suffix>`, D-12): the tab's, never composed."""
        return self.t(f"{self.WORDS}_{suffix}", **args)

    def tl(self, text):
        return self.ctx.tl(text)

    def fail(self, message):
        return autosave.refuse(self, self.t(self.KEY), message)

    def current_label(self):
        edit = self.id_edit
        return (edit.text().strip() if edit is not None else (self.source or {}).get("id", "")) or "?"

    # --- the cases (source_store, draft_logic, case_list_logic) ---------------------------

    def make_source(self):
        return self.ctx.store.new_source(self.ID_PREFIX)

    def after_new(self):
        """What a tab does to a source just made before it is shown."""

    def duplicate_id(self, source):
        return case_list_logic.next_free_id(self.ctx.store.all_ids(), self.ID_PREFIX)   # every id of the folder: tabs may share one (the member checks)

    def saved_ids(self):
        return self.ctx.store.ids()

    def sources_dir(self):
        return self.ctx.store.folder()

    def read_saved(self, path):
        return self.ctx.store.read(path)

    def graph_id(self, cid):
        own = getattr(self.MODULE, "graph_id", None)   # a domain naming its objects in the graph itself (a member check by its id alone, issue #112)
        return own(cid) if own is not None else f"{self.MODULE.DOMAIN}/{cid}"

    def lists_object(self, ident):
        return case_list_logic.lists_object(self, ident)

    def open_object(self, ident):
        case_list_logic.open_object(self, ident)

    def new(self):
        draft_logic.new(self)

    def new_from(self, source):
        draft_logic.new_from(self, source)

    def duplicate(self):
        draft_logic.duplicate(self)

    def revert(self):
        draft_logic.revert(self)

    def load(self, cid):
        draft_logic.load(self, cid)

    def blank(self):
        draft_logic.blank(self)

    def open_first(self):
        draft_logic.open_first(self)

    def after_archive(self):
        draft_logic.after_archive(self)

    def delete(self):
        """«Supprimer»: what is selected goes to «Archives» (source_archive.py) -- or, an archived entry selected, is deleted for good. A source never saved is simply discarded."""
        if self.has_service("cases") and self.service("cases").archive.delete():
            return
        self.dirty = False
        self.open_first()

    def confirm_leave(self):
        """Before the draft is left -- another case, tab, view or document, the window closed --: saved without a question where it can be, else the one question (autosave.py)."""
        title, message = self.UNSAVED_WORDS or (f"{self.WORDS}_unsaved_title", f"{self.WORDS}_unsaved")
        return autosave.confirm(self.app, self, self.t(title), self.t(message, id=self.current_label()))

    def reload_list(self, select=None):
        self.phase("reload_list", select)

    def update_list_marker(self):
        self.phase("update_marks")

    def export_listed(self, text):
        """The export rebuilt after the list changed cases without naming one -- a drop into a folder, an archive --, said in the status bar."""
        self.export(text)

    def export(self, done):
        error = self.ctx.store.export()
        self.app.set_status(self.word("export_failed", error=error) if error else done)

    # --- the form -----------------------------------------------------------------------

    def fill_form(self):
        self.ctx.fill(self.source)

    def draft(self):
        return self.ctx.draft()

    def touch(self, *_ignored):
        self.ctx.touch()

    def refresh(self, preview=True):
        """The draft computed at once, and every service told (`computed`): the messages, the results, the drawing, «Affichage»'s call, the dot."""
        self.ctx.compute(self.draft())
        self.phase("computed")
        self.update_list_marker()
        if preview:
            self.request_preview()

    def save(self):
        """«Enregistrer»: the case checked -- its id, its rename asked, its source --, written and exported by the store (one guarded writer, source_store.SourceStore.save), the list again."""
        source = self.draft()
        cid = source.get("id")
        refusal = self.ctx.store.id_refusal(source, self.current_id)
        if refusal:
            return self.fail(self.word(refusal[0], **refusal[1]))
        if source_store.is_rename(source, self.current_id):
            if not autosave.ask_rename(self, self.word("rename_title"), self.word("rename", old=self.current_id, new=cid)):
                return False
        refusal = self.ctx.store.check_refusal(source)
        if refusal:
            return self.fail(self.word(refusal[0], **refusal[1]))
        error = self.ctx.store.save(source, self.current_id)
        if error is False:      # refused: a project open read-only (tab_guard)
            return False
        self.source, self.current_id, self.dirty = source, cid, False
        self.app.set_status(self.word("export_failed", error=error) if error else self.word("saved", id=cid))
        self.reload_list(cid)
        self.phase("saved")
        return True

    # --- «Affichage» ---------------------------------------------------------------------

    def install_display(self, cache_key, centre=1, right=2):
        """«Affichage» is the display service's view, in the same panes as every tab's (display_view.ViewPanes)."""
        self.display = self.service("display").view
        self.panes = display_view.ViewPanes(self.splitter, self.display, centre, right)
        self.view = self.VIEWS[0]

    def display_entries(self):
        return self.service("display").entries()

    def prepare_display(self):
        """«Calcul» left for «Affichage»: the services told (`before_display`) -- the case saved where it can be, what «Affichage» shows being the file as the save writes it."""
        self.phase("before_display")

    def request_preview(self):
        if not self.live or self.view != "display":
            return
        try:
            if not self.display.active:
                self.display.activate(True)
            else:
                self.display.refresh()
        except Exception as exc:  # broad: a malformed case is said in the status bar, not raised into the event loop
            self.app.set_status(self.word("invalid", error=str(exc)))

    def stop(self):
        if getattr(self.display, "pane", None) is not None:
            self.display.pane.stop()

    # --- the window's calls ----------------------------------------------------------------

    def on_shown(self):
        draft_logic.shown(self)

    def view_state(self):
        return {"draft": copy.deepcopy(self.draft()), "current_id": self.current_id, "dirty": self.dirty, "splitter": self.splitter.sizes(),
                "services": {s.NAME: s.state() for s in self.services if s.NAME}}

    def restore(self, state):
        """The state `view_state` gave, after a rebuild of the window; none, the first case of the list or a new one."""
        if not state:
            self.reload_list()
            if self.ids:
                self.phase("select_row", self.ids[0])
                self.load(self.ids[0])
            else:
                self.fill_form()
                self.refresh()
            self.splitter.setSizes([s * 1000 for s in self.STRETCH])
            return
        self.source = state.get("draft") or self.source
        self.current_id = state.get("current_id")
        self.dirty = bool(state.get("dirty"))
        kept = state.get("services") or {}
        for service in self.services:
            if service.NAME in kept:
                service.restore(kept[service.NAME])
        self.reload_list(self.current_id)
        self.fill_form()
        if state.get("splitter"):
            self.splitter.setSizes(state["splitter"])
        self.refresh()
