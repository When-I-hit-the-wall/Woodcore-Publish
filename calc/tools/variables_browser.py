"""The content of the «Variables» tab: three panes, one view (spec docs/requirements/completed/2026-10-24-onglet-variables-groupes.md, UI-001 to UI-012, REQ-007 to REQ-009, ARCH-004, ARCH-009; docs/ui/tab-variables.md).

The engineer's prototype, version 2 (24.10.2026, issue #114): on the left the menu of Woodcore's tabs, the
source and the domains of the filter under the title of their tab; in the centre the search bar that carries
the filter as tags, the unit, «Résultats seulement», the count, the bar of the choice and the list always
grouped by domain; on the right the card, which opens the tab where the value was computed, gives the command to
copy and says where the same calculation is elsewhere. The tab serves to find a value the project computed, to
print it elsewhere in the report or to have a field of another tab follow it (issue #42).

**It holds no arithmetic and decides nothing** (ARCH-001): what a domain is, its tab, its siblings, whether it is
printed (variable_calc); the menu, the filter, the groups, the counts (variable_query); the choice
(variable_select); the card and the command (variable_card) -- all Qt-free under calc/. This shows them.

⚠️ **A service** (ARCH-004, ARCH-009, D-17 of issue #114; issue #106): a `tab_frame.Service` -- `NAME`,
`mount(ctx)` giving its widget, `state()` / `restore()`, the phases `shown`, `mode_changed`, `leave` --, no Qt
base, no other service called, no `app.tabs` read. What it needs of the window goes through its public methods
(`current_document`, `t`, `set_status`, `busy`, `process`, `copy`, `can_open_tab`, `show_tab`), found on its
context's `app`; what failed or is out of date is said to the type's banner (`ctx.say`, data_tab.ExportBanner).
`variables_tab.VariablesTab` is a class of parameters on the type «Données» that mounts it and exposes what the
window and the other tabs call on it (`EXPOSES`). Mounted without a context -- built alone, as a test does --, it
says nothing.

⚠️ **The documents are read once** (the measurement of v0.110 that the tab's module said, kept): the first showing
reads them in a thread (`variables_tab.Read`), then the cache answers until a document, the engine or the export
moved under it; a banner says so, and «Relire les documents» is the one thing that reads again. The export's
files, some tens of kilobytes, are read again at every showing.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QSplitter, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

import cards
import chrome
import documents
import project
import theme
import variable_calc as calc
import variable_card as card
import variable_query as query
import variable_sources as sources
import variables as model
from tab_frame import Service
from tag_search_bar import TagSearchBar
from tree_menu import Entry, TreeMenu
from variable_select import Selection
from variables_detail import VariablesDetail
from variables_list import VariablesList

EXPORT = sources.EXPORT
FORMULAS = sources.formula_domain.ORIGIN

# A document's letters, the same in every language (the engineer, 30.09.2026), its whole name in the tooltip.
DOCUMENT_CODES = {"cu": "CU", "bp": "BP", "rs": "RS"}

# The left pane's width at the start, wide enough for the names of the cases (UI-003), and the card's; dragged at the splitter's handle afterwards.
LEFT_WIDTH = 260
RIGHT_WIDTH = 400

DOMAIN_ROLE = Qt.ItemDataRole.UserRole
BADGE_TOKENS = {calc.SOURCE_EXPORT: "wood", calc.SOURCE_FILE: "accent-strong", calc.SOURCE_DOCUMENT: "ok"}


class VariablesBrowser(Service):
    """The content of the tab, its one whole service. Mounted on the tab's context (`mount(ctx)`), or built on `app`, the window, and mounted alone (`mount()`)."""

    NAME = "browser"
    ZONE = "body"
    app = None                    # the window: its context's, or the one it was built on -- the frame's property shadowed, so a browser built alone has one

    def __init__(self, app=None):
        self.app = app
        self.ctx = None
        self.readings = {}            # document -> the last read, from the cache or from a read of our own
        self.errors = {}              # document -> why its last read did not happen
        self.reader = None            # the thread while one runs
        self.opened = False           # whether `shown` has already decided about the first read
        self.export = sources.read_export()   # the export's files, read now and at every showing (D-014)
        self.domains = {}             # (origin, name) -> variable_sources.Domain, every domain listed
        self.assembly = None
        self.catalogue = None
        self.filter = query.Filter()
        self.selection = Selection()
        self.pick_done = None         # while a field's value is chosen: what receives it (MainWindow.begin_variable_pick)
        self.pick_accept = None       # and what the field may take (variable_sources.linkable, REQ-008)
        self.pick_title = ""
        self.widget = None

    # -- the service's shape --

    def mount(self, ctx=None):
        """The widget: the bar, the field's bar, and the three panes -- the banner is the type's, above them."""
        if self.widget is not None:
            return self.widget
        if ctx is not None:
            self.ctx, self.app = ctx, ctx.app
        self.t = self.app.t
        self.widget = QWidget()
        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addLayout(self._build_bar())
        layout.addWidget(self._build_pick_bar())
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self._build_left())
        self.splitter.addWidget(self._build_centre())
        self.detail = VariablesDetail(self.t, self.app.mono_font)
        self.detail.open_tab.connect(self.open_tab)
        self.detail.copy.connect(self.copy)
        self.detail.go.connect(self.go)
        self.detail.import_.connect(self.pick_chosen)
        self.splitter.addWidget(self.detail)
        for index, stretch in enumerate((0, 3, 2)):
            self.splitter.setStretchFactor(index, stretch)
        self.splitter.setSizes([LEFT_WIDTH, 700, RIGHT_WIDTH])
        self.sized = False            # the panes given their widths of the start once the splitter has one (`_first_width`)
        self.splitter.installEventFilter(self.widget_filter())
        layout.addWidget(self.splitter, 1)
        escape = QShortcut(QKeySequence(Qt.Key.Key_Escape), self.widget)
        escape.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        escape.activated.connect(lambda: self.end_pick(None) if self.pick_done is not None else None)

        here = project.current()
        for mode in here.created_modes:
            found = model.cached(here, mode)
            if found is not None:
                self.readings[mode] = found
        self.refresh()
        return self.widget

    def widget_filter(self):
        """The splitter's first real width: the left pane at LEFT_WIDTH and the card at RIGHT_WIDTH, the list the rest (UI-003) -- sizes set before the splitter had a width are squeezed to its panes' minimums. Not where a kept state gave them."""
        from PySide6.QtCore import QEvent, QObject

        browser = self

        class First(QObject):
            def eventFilter(self, obj, event):
                if event.type() == QEvent.Type.Resize and not browser.sized and event.size().width() >= 2 * (LEFT_WIDTH + RIGHT_WIDTH):
                    browser.sized = True
                    total = event.size().width() - (obj.count() - 1) * obj.handleWidth()
                    obj.setSizes([LEFT_WIDTH, total - LEFT_WIDTH - RIGHT_WIDTH, RIGHT_WIDTH])
                return False

        self._first = First(self.widget)
        return self._first

    def state(self):
        """What the window keeps through a rebuild (`view_state`): the splitter, the filter -- `menu`, `origin_filter`, `tags` (the domain chosen), the words, the unit, «Résultats seulement» --, the widths of the columns, the choice (`selection`) and the last one clicked under the names `select_key` reads (`source`, `domain`, `name`). ⚠️ No name of before with another meaning (UI-007): `source` is the origin of what is chosen, as it always was, and the segment of the source is `origin_filter`."""
        origin, domain, name = self.selected_key() or (None, None, None)
        return {
            "splitter": self.splitter.sizes(),
            "search": self.search.text(),
            "unit": self.filter.unit,
            "results_only": self.filter.results_only,
            "origin_filter": self.filter.source,
            "menu": self.filter.menu,
            "tags": {"domain": list(self.filter.domain) if self.filter.domain else None},
            "widths": self.list.widths(),
            "selection": [list(key) for key in self.selection.chosen],
            "source": origin,
            "domain": domain,
            "name": name,
            "opened": self.opened,
        }

    def restore(self, state):
        """A view kept through a rebuilt window. A state of before (v0.117: `provenance`, `all_domains`, a `source` that is an origin such as `rs`) is read without harm: it sets no source filter -- there is no `origin_filter` in it -- and chooses its domain and its variable again; its splitter's sizes are applied only where they are as many as the panes."""
        if not state:
            return
        sizes = state.get("splitter")
        if sizes and len(sizes) == self.splitter.count():
            self.splitter.setSizes(sizes)
            self.sized = True
        self.opened = bool(state.get("opened"))
        f = self.filter
        f.results_only = bool(state.get("results_only"))
        f.source = state.get("origin_filter") if state.get("origin_filter") in query.SOURCE_FILTERS else query.ALL_SOURCES
        menu = state.get("menu")
        f.menu = menu if isinstance(menu, str) and self.catalogue is not None and menu in self.catalogue.nodes else query.ALL
        tags = state.get("tags") if isinstance(state.get("tags"), dict) else {}
        domain = tags.get("domain")
        f.domain = tuple(domain) if isinstance(domain, (list, tuple)) and len(domain) == 2 and tuple(domain) in self.domains else None
        unit = state.get("unit")
        f.unit = unit if self.catalogue is not None and unit in self.catalogue.units() else query.ANY_UNIT
        self.list.set_widths(state.get("widths"))
        self.selection.chosen = {tuple(k): True for k in state.get("selection") or () if isinstance(k, (list, tuple)) and len(k) == 3 and self.variable(tuple(k)) is not None}
        self._set_controls()
        self.search.blockSignals(True)
        self.search.setText(state.get("search") or "")
        self.search.blockSignals(False)
        f.text = self.search.text()
        source, domain_name, name = state.get("source"), state.get("domain"), state.get("name")
        if source is not None and domain_name is not None:
            if "tags" in state:
                key = (source, domain_name, name)
                if name is not None and self.variable(key) is not None:
                    self.selection.focus = self.selection.anchor = key
            else:
                self.select_key((source, domain_name, name))   # a state of before: its domain chosen, as on the left then
                return
        self.fill()

    def shown(self):
        """Brought to the front. The export's files are read again every time -- a polar moment saved on another tab must be here when one comes back (D-014). The **first** time, the documents are read where no current reading is cached; every time after that, only where it is **free** (their PDF exported since, v0.110)."""
        first = not self.opened
        self.opened = True
        self.export = sources.read_export()
        if model.auto_enabled():
            wanted = self.unread(free_only=not first)
            if wanted:
                self.reload(automatic=True, modes=wanted)
                return
        self.refresh()

    def say(self, text, kind=None):
        """The type's banner told `text` (data_tab.DataContext.say); nothing where the browser was mounted alone."""
        if self.ctx is not None:
            self.ctx.say(text, kind)

    def mode_changed(self, _mode):
        """Another document shown: the documents' entries of the menu and «Ouvrir l'onglet» follow it."""
        self.refresh()

    def leave(self):
        """The window is closing: a reading is a `subprocess.run` in a thread and cannot be cut short, so it is waited for. Always True: nothing is lost here."""
        if self.reader is not None:
            self.reader.wait(model.TIMEOUT_S * 1000 * max(1, len(self.reader.modes)))
        return True

    # -- building --

    def _build_bar(self):
        bar = QHBoxLayout()
        self.state_label = QLabel("")
        self.state_label.setStyleSheet(f"color: {theme.colour('muted')};")
        bar.addWidget(self.state_label)
        bar.addStretch(1)
        self.reload_button = QPushButton(self.t("vr_reload"))
        self.reload_button.clicked.connect(lambda _c=False: self.reload())
        bar.addWidget(self.reload_button)
        self.set_reading(False)
        return bar

    def _build_pick_bar(self):
        """The line that says a field is waiting for a value -- its title, «Annuler» --, hidden but while choosing; Escape gives up too."""
        bar = QFrame()
        bar.setProperty("callout", "info")
        bar.setStyleSheet(f"QFrame {{ background: {theme.colour('accent-soft')}; border-left: 3px solid {theme.colour('accent')}; border-radius: 4px; }}"
                          " QLabel { background: transparent; border: none; }")
        row = QHBoxLayout(bar)
        row.setContentsMargins(8, 4, 8, 4)
        self.pick_label = QLabel("")
        self.pick_label.setWordWrap(True)
        row.addWidget(self.pick_label, 1)
        self.pick_cancel = QPushButton(self.t("vr_pick_cancel"))
        self.pick_cancel.clicked.connect(lambda: self.end_pick(None))
        row.addWidget(self.pick_cancel)
        bar.setVisible(False)
        self.pick_bar = bar
        return bar

    def _heading(self, key):
        label = QLabel(self.t(key))
        label.setFont(self.app.bold_font)
        return label

    def _build_left(self):
        """The left pane: the menu of the tabs, the source, the domains of the filter under their tab, the legend."""
        pane = QWidget()
        box = QVBoxLayout(pane)
        box.setContentsMargins(0, 0, 6, 0)
        box.addWidget(self._heading("vr_domains"))
        self.menu = TreeMenu()
        self.menu.setToolTip(self.t("vr_menu_tip"))
        self.menu.chosen.connect(self.choose_menu)
        box.addWidget(self.menu)
        self.source_switch = chrome.SegmentedSwitch([(key, self.t("vr_source_" + key), self.t("vr_source_tip")) for key in query.SOURCE_FILTERS], query.ALL_SOURCES, soft=True)
        self.source_switch.changed.connect(self.choose_source)
        for button in self.source_switch.group.buttons():
            button.setMinimumWidth(cards.ELIDE_LEAST // 2)   # the pane may be dragged to its floor (cards.PANE_FLOOR, issue #10): the segment gives way, its words in its tooltip
        box.addWidget(self.source_switch)
        self.domain_list = QTreeWidget()
        self.domain_list.setColumnCount(3)
        self.domain_list.setHeaderHidden(True)
        self.domain_list.setRootIsDecorated(False)
        self.domain_list.setIndentation(0)
        self.domain_list.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        header = self.domain_list.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, header.ResizeMode.Stretch)
        header.setSectionResizeMode(1, header.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, header.ResizeMode.ResizeToContents)
        self.domain_list.itemClicked.connect(lambda item, _c: self.click_domain(item.data(0, DOMAIN_ROLE)))
        box.addWidget(self.domain_list, 1)
        self.legend = QLabel("")
        self.legend.setTextFormat(Qt.TextFormat.RichText)
        self.legend.setWordWrap(True)
        box.addWidget(self.legend)
        return pane

    def _build_centre(self):
        """The centre pane: the search bar with its tags, the unit, «Résultats seulement» and the count, the bar of the choice, the list."""
        pane = QWidget()
        box = QVBoxLayout(pane)
        box.setContentsMargins(0, 0, 6, 0)
        self.search_bar = TagSearchBar()
        self.search_bar.set_placeholders(self.t("vr_search"), self.t("vr_search_filtered"))
        self.search_bar.removed.connect(self.remove_tag)
        self.search = self.search_bar.edit
        self.search.textChanged.connect(self.on_text)
        box.addWidget(self.search_bar)
        filters = QHBoxLayout()
        self.unit_box = QComboBox()
        self.unit_box.currentIndexChanged.connect(self.on_unit)
        filters.addWidget(self.unit_box)
        self.results_box = QCheckBox(self.t("vr_results_only"))
        self.results_box.setToolTip(self.t("vr_results_only_hint"))
        self.results_box.toggled.connect(self.on_results)
        filters.addWidget(self.results_box)
        self.count_label = QLabel("")
        self.count_label.setStyleSheet(f"color: {theme.colour('muted')};")
        filters.addWidget(self.count_label)
        filters.addStretch(1)
        box.addLayout(filters)

        self.choice_bar = QWidget()
        row = QHBoxLayout(self.choice_bar)
        row.setContentsMargins(0, 0, 0, 0)
        self.choice_label = QLabel("")
        row.addWidget(self.choice_label)
        self.copy_button = QPushButton("")
        self.copy_button.clicked.connect(self.copy_chosen)
        row.addWidget(self.copy_button)
        self.clear_button = QPushButton(self.t("vr_clear"))
        self.clear_button.clicked.connect(self.clear_choice)
        row.addWidget(self.clear_button)
        self.choice_hint = QLabel(self.t("vr_select_hint"))
        self.choice_hint.setStyleSheet(f"color: {theme.colour('muted')};")
        row.addWidget(self.choice_hint)
        row.addStretch(1)
        box.addWidget(self.choice_bar)

        self.list = VariablesList(self.t, selection=self.selection)
        self.list.changed.connect(self.on_choice)
        box.addWidget(self.list, 1)
        self.empty = QLabel("")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setWordWrap(True)
        self.empty.setStyleSheet(f"color: {theme.colour('muted')};")
        box.addWidget(self.empty, 1)
        return pane

    # -- the documents --

    def modes(self):
        """The documents of the current project, the one the window shows first."""
        here = project.current()
        current = getattr(self.app, "current_document", None)
        first = current() if callable(current) else "rs"
        return sorted(here.created_modes, key=lambda mode: (mode != first, here.created_modes.index(mode)))

    def document_name(self, mode):
        return documents.mode_name(mode, getattr(self.app, "lang", documents.DEFAULT_LANGUAGE))

    def all_domains(self):
        """[Domain]: the export's (its files' last), then every document's read, the one shown first -- the order the list keeps within a tab."""
        found = list(self.export.domains)
        for mode in self.modes():
            found += sources.registry_domains(mode, self.readings.get(mode))
        return found

    def stale(self):
        here = project.current()
        return [mode for mode, found in self.readings.items() if mode in here.created_modes and not model.is_current(found, here, mode)]

    def unread(self, free_only=False):
        """The documents whose reading does not answer for them -- and, `free_only`, only those whose own PDF is current, a read then costing the half-second of opening it rather than a compile (variables.pdf_is_current, v0.110)."""
        here = project.current()
        out = []
        for mode in here.created_modes:
            if model.is_current(self.readings.get(mode), here, mode):
                continue
            if free_only and not model.pdf_is_current(here, mode):
                continue
            out.append(mode)
        return out

    # -- reading --

    def set_reading(self, reading, reason=None):
        """Whether a reading runs: the button and its tooltip set together, so a button shown disabled says why (v0.47's rule) and an enabled one what it costs."""
        self.reload_button.setEnabled(not reading)
        self.reload_button.setToolTip(self.t(reason or ("vr_reading" if reading else "vr_reload_hint")))

    def reload(self, automatic=False, modes=None):
        """Reads the documents again -- `modes`, else every one -- in a thread. Refused while an export or a compilation runs: `data/` is in what a reading reads. ⚠️ A click is answered with `app.busy()`, the first automatic read with a line in the bar -- a modal put up by a tab merely opened is worse than a tab that fills a moment later."""
        if self.reader is not None:
            return
        if automatic:
            if self.app.process is not None:
                self.state_label.setText(self.t("vr_busy"))
                return
        elif self.app.busy():
            return
        import variables_tab   # the thread lives with the tab's shell (variables_tab.Read), the one module that names it
        here = project.current()
        modes = [mode for mode in (modes or self.modes()) if mode in here.created_modes]
        for mode in modes:
            self.errors.pop(mode, None)
        self.set_reading(True)
        self.state_label.setText(self.t("vr_reading"))
        self.say("")
        self.reader = variables_tab.Read(self.widget, here, modes)
        self.reader.done.connect(self.read_done)
        self.reader.failed.connect(self.read_failed)
        self.reader.finished.connect(self.read_finished)
        self.reader.start()

    def read_done(self, mode, registry):
        self.readings[mode] = registry
        self.errors.pop(mode, None)

    def read_failed(self, mode, error):
        self.errors[mode] = error

    def read_finished(self):
        reader, self.reader = self.reader, None
        if reader is not None:
            reader.deleteLater()
        self.set_reading(False)
        self.export = sources.read_export()   # an export the reading waited on has written data/ since
        self.refresh()
        if self.errors:
            mode, error = next(iter(self.errors.items()))
            self.app.set_status(self.failure(mode, error))

    def reason(self, error):
        """A failure in the window's language, from the code the module gave it -- never by parsing its English sentence."""
        try:
            return self.t(f"vr_err_{error.code}", **error.detail)
        except (KeyError, IndexError):
            return str(error)

    def failure(self, mode, error):
        return self.t("vr_failed", document=self.document_name(mode), reason=self.reason(error))

    # -- filling --

    def refresh(self):
        """Everything again from what the last reads left: the domains assembled (variable_calc), the menu (variable_query, from tab_registry's navigation), the bar, the banner, the panes."""
        import tab_registry   # the navigation, read when the menu is made (ARCH-005); imported here, tab_registry importing this tab
        listed = self.all_domains()
        here = project.current()
        self.assembly = calc.assemble(listed, self.export.index, documents_read=any(mode in self.readings for mode in here.created_modes))
        self.domains = {(domain.origin, domain.name): domain for domain in listed}
        roots = query.navigation(tab_registry.NAV_GROUPS, tab_registry.NAV_SECTIONS, self.t,
                                 documents=[(mode, self.document_name(mode)) for mode in here.created_modes], none_title=self.t("vr_menu_none"))
        self.catalogue = query.Catalogue(self.assembly, roots)
        if self.filter.menu and self.filter.menu not in self.catalogue.nodes:
            self.filter.menu = query.ALL
        if self.filter.domain is not None and tuple(self.filter.domain) not in self.domains:
            self.filter.domain = None
        self.selection.chosen = {k: True for k in self.selection.chosen if self.variable(k) is not None}
        if self.selection.focus is not None and self.variable(self.selection.focus) is None:
            self.selection.focus = None
        if self.reader is None:
            # The bar says what is on screen, the banner what went wrong: a failed reading keeps the values of the last good one listed below.
            count = sum(len(domain.variables) for domain in listed)
            if self.readings or (count and not self.errors):
                text = self.t("vr_count", count=count, domains=len(listed))
                if not self.readings and not self.errors:
                    text += " · " + self.t("vr_never")
                self.state_label.setText(text)
            elif self.errors:
                self.state_label.setText(self.failure(*next(iter(self.errors.items()))))
            else:
                self.state_label.setText(self.t("vr_never"))
        stale = self.stale()
        failures = []
        if self.reader is None:
            for mode, error in self.errors.items():
                failures.append(self.failure(mode, error))
                output = (error.detail.get("output") or "").strip()
                if output:
                    failures.append(output)
        failures += [self.reason(error) for error in self.export.errors]
        if failures:
            self.say("\n\n".join(failures), "danger")
        else:
            self.say(self.t("vr_stale") if stale and self.reader is None else "", "warning")
        self.fill_units()
        self._set_controls()
        self.fill()

    def _set_controls(self):
        """The unit, «Résultats seulement» and the source's segment set from the filter, without their signals."""
        self.results_box.blockSignals(True)
        self.results_box.setChecked(self.filter.results_only)
        self.results_box.blockSignals(False)
        index = self.unit_box.findData(self.filter.unit)
        self.unit_box.blockSignals(True)
        self.unit_box.setCurrentIndex(index if index >= 0 else 0)
        self.unit_box.blockSignals(False)
        self.source_switch.blockSignals(True)
        self.source_switch.set_current(self.filter.source)
        self.source_switch.blockSignals(False)

    def fill_units(self):
        """The units of the project, the commonest first (UI-005) -- those the field takes while one is linked."""
        units = self.catalogue.units(self.pick_accept)
        if self.filter.unit is not query.ANY_UNIT and self.filter.unit not in units:
            self.filter.unit = query.ANY_UNIT
        self.unit_box.blockSignals(True)
        try:
            self.unit_box.clear()
            self.unit_box.addItem(self.t("vr_any_unit"), query.ANY_UNIT)
            for unit in units:
                self.unit_box.addItem(unit if unit else self.t("vr_no_unit"), unit)
        finally:
            self.unit_box.blockSignals(False)

    def fill(self):
        """The panes from the filter: the menu, the domains on the left, the tags, the list, the bar of the choice, the card."""
        self.fill_menu()
        self.fill_side()
        self.fill_list()

    def badge(self, domain):
        """A domain's source as its tag says it: «export», «fichier», or a document's letters."""
        source = calc.source_of(domain)
        if source == calc.SOURCE_DOCUMENT:
            return DOCUMENT_CODES.get(domain.origin, domain.origin.upper())
        return self.t("vr_badge_export" if source == calc.SOURCE_EXPORT else "vr_badge_file")

    def fill_menu(self):
        """The menu's entries, each with its number in the source chosen (UI-002); one at zero greyed."""
        entries = [Entry(query.ALL, self.t("vr_menu_all_entry"), str(self.catalogue.count(query.ALL, self.filter.source, self.pick_accept)), 0, bold=True)]
        for node, n in self.catalogue.menu_rows(self.filter.source, self.pick_accept):
            entries.append(Entry(node.id, node.title, str(n) if n else "—", node.depth,
                                 enabled=n > 0, tip="" if n else self.t("vr_menu_zero"), bold=node.kind == "group"))
        self.menu.set_entries(entries, self.filter.menu)
        node = self.catalogue.nodes.get(self.filter.menu)
        self.menu.set_label(" › ".join(node.path) if node is not None else self.t("vr_menu_all"))

    def fill_side(self):
        """The domains of the filter under the title of their tab (UI-003): the case, its source, its number; in grey where no document prints it."""
        lst = self.domain_list
        lst.blockSignals(True)
        try:
            lst.clear()
            current = None
            muted = theme.colour("muted")
            for title, rows in self.catalogue.side(self.filter, self.pick_accept):
                head = QTreeWidgetItem(lst, [title or self.t("vr_menu_none"), "", ""])
                head.setFlags(Qt.ItemFlag.NoItemFlags)
                font = head.font(0)
                font.setBold(True)
                head.setFont(0, font)
                head.setForeground(0, _brush(muted))
                head.setFirstColumnSpanned(True)
                for domain, n in rows:
                    item = QTreeWidgetItem(lst, ["   " + calc.case_of(domain), self.badge(domain), str(n)])
                    item.setData(0, DOMAIN_ROLE, (domain.origin, domain.name))
                    item.setForeground(1, _brush(theme.colour(BADGE_TOKENS[calc.source_of(domain)])))
                    item.setTextAlignment(2, int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter))
                    tip = f"{calc.case_of(domain)} · {self.badge(domain)}" + (f" — {domain.label}" if domain.label else "")
                    if self.assembly.printed(domain) is False:
                        item.setForeground(0, _brush(muted))
                        tip += " · " + self.t("vr_not_printed_tip")
                    if calc.source_of(domain) == calc.SOURCE_DOCUMENT:
                        tip += f" ({self.document_name(domain.origin)})"
                    for column in range(3):
                        item.setToolTip(column, tip)
                    if self.filter.domain is not None and (domain.origin, domain.name) == tuple(self.filter.domain):
                        current = item
            lst.setCurrentItem(current) if current is not None else lst.clearSelection()
        finally:
            lst.blockSignals(False)
        colours = {key: theme.colour(token) for key, token in BADGE_TOKENS.items()}
        self.legend.setText(f'<span style="color:{colours[calc.SOURCE_EXPORT]}">{self.t("vr_badge_export")}</span> · '
                            f'<span style="color:{colours[calc.SOURCE_FILE]}">{self.t("vr_badge_file")}</span> · '
                            f'<span style="color:{colours[calc.SOURCE_DOCUMENT]}">{" / ".join(DOCUMENT_CODES[m] for m in project.current().created_modes)}</span> · '
                            f'<span style="color:{muted}">{self.t("vr_legend")}</span>')

    def describe(self, domain, count):
        """A title line of the list (UI-006): its case, its source, its tab, its label, «pas imprimé» where so, its number."""
        rest = [self.catalogue.tab_title(domain) or self.t("vr_menu_none")]
        if domain.label:
            rest.append(domain.label)
        if self.assembly.printed(domain) is False:
            rest.append(self.t("vr_not_printed"))
        return {"case": calc.case_of(domain), "badge": self.badge(domain), "kind": calc.source_of(domain), "rest": " · ".join(rest), "count": count,
                "tip": self.t("vr_not_printed_tip") if self.assembly.printed(domain) is False else ""}

    def fill_list(self):
        """The list, grouped by domain, the tags, the count, the bar of the choice and the card."""
        self.search_bar.set_tags(self.catalogue.tags(self.filter, self.t, self.badge), self.t("vr_tag_remove"))
        self.list.list_model.accept = self.pick_accept
        groups = self.catalogue.groups(self.filter, self.pick_accept)
        self.list.set_groups(groups, self.describe)
        count, domains = self.catalogue.totals(groups)
        self.count_label.setText(self.t("vr_list_count", count=count, domains=domains))
        self.list.setVisible(bool(groups))
        self.empty.setVisible(not groups)
        if not groups:
            self.empty.setText(self.empty_text())
        self.fill_choice()
        self.show_card()

    def empty_text(self):
        if not any(domain.variables for domain in self.domains.values()):
            text = self.t("vr_empty")
            if len(self.export.missing) == len(sources.FILE_SOURCES):
                text = self.t("vr_no_export") + "\n\n" + text
            return text
        return self.t("vr_filtered")

    def fill_choice(self):
        """The bar of the choice (UI-010): «3 choisie(s) · Copier les 3 commandes · Tout désélectionner», hidden at none and while a field is linked."""
        n = len(self.selection)
        hidden = self.selection.hidden(self.list.shown())
        self.choice_bar.setVisible(n > 0 and self.pick_done is None)
        self.choice_label.setText(self.t("vr_selected_hidden", count=n, hidden=hidden) if hidden else self.t("vr_selected", count=n))
        self.copy_button.setText(self.t("vr_copy_many", count=n) if n > 1 else self.t("vr_copy_one"))

    # -- the gestures --

    def choose_menu(self, node_id):
        """An entry of the menu chosen: its tabs kept, the domain chosen let go where it is no longer among them."""
        self.filter.menu = node_id
        self._drop_domain_out_of_scope()
        self.fill()

    def choose_source(self, source):
        """A source of the segment chosen."""
        self.filter.source = source
        self._drop_domain_out_of_scope()
        self._set_controls()
        self.fill()

    def _drop_domain_out_of_scope(self):
        domain = self.domains.get(tuple(self.filter.domain)) if self.filter.domain is not None else None
        if domain is not None and not self.catalogue.in_scope(domain, self.filter):
            self.filter.domain = None

    def click_domain(self, key):
        """A domain on the left: chosen -- the search emptied, its card shown -- or, chosen already, let go (UI-003)."""
        if key is None:
            return
        key = tuple(key)
        if self.filter.domain is not None and tuple(self.filter.domain) == key:
            self.filter.domain = None
        else:
            self.filter.domain = key
            self.search.blockSignals(True)
            self.search.setText("")
            self.search.blockSignals(False)
            self.filter.text = ""
            self.selection.focus = None
        self.fill()

    def remove_tag(self, kind):
        """A tag's × or ⌫ in an empty bar (UI-004): the domain let go on the left too, the source back to «Toutes», the menu back to «Tous les onglets»."""
        query.without(self.filter, kind)
        if kind == "source":
            self._set_controls()
        self.fill()
        self.search.setFocus()

    def on_text(self, text):
        self.filter.text = text
        self.fill_list()

    def on_unit(self, _index):
        self.filter.unit = self.unit_box.currentData()
        self.fill_list()

    def on_results(self, on):
        self.filter.results_only = bool(on)
        self.fill_list()

    def on_choice(self):
        self.fill_choice()
        self.show_card()

    def clear_choice(self):
        self.selection.clear()
        self.list.refresh()
        self.fill_choice()

    def copy_chosen(self):
        """«Copier les n commandes»: a `#var` line a variable, the ones shown in the order of the list, then the ones the filter hides (UI-009, UI-010)."""
        keys = self.selection.copy_order(self.list.shown(), self.catalogue.all_keys())
        lines = card.copy_lines(keys, self.domains, self.assembly)
        if lines:
            self.copy("\n".join(lines))

    def copy(self, text):
        copier = getattr(self.app, "copy", None)
        if callable(copier):
            copier(text)
        else:
            from PySide6.QtGui import QGuiApplication
            QGuiApplication.clipboard().setText(text)

    def go(self, key):
        """A sibling's button: the same variable chosen in the other source, the filter opened to it where it hid it."""
        self.select_key(key)

    # -- the card --

    def show_card(self):
        key = self.selected_key()
        domain = self.domain_of(key)
        var = self.variable(key)
        if domain is None:
            self.detail.show_none()
            return
        path = self.catalogue.menu_path(domain)
        path_text = " › ".join(path + (calc.case_of(domain),)) + f" [{self.badge(domain)}]"
        siblings = []
        if var is not None:
            found = card.variable_card(var, domain, self.assembly, path, document_name=self.document_name)
            for sib in found.siblings:
                role = self.t("vr_computes" if sib.computes else "vr_recalls")
                text = f"[{self.badge(sib.domain)}] {calc.case_of(sib.domain)}" + (f" · {sib.value}" if sib.key else "") + f" · {role}"
                siblings.append((text, (sib.domain.origin, sib.domain.name, sib.key), self.document_name(sib.domain.origin) if calc.source_of(sib.domain) == calc.SOURCE_DOCUMENT else ""))
            computed = ""
            if found.computed_in is not None:
                key_, values = found.computed_in
                computed = self.t(key_, **({"source": self.badge(values["source"])} if "source" in values else {}))
            note = self.t(found.command.note, **found.command.values) if found.command is not None else ""
            from_key, from_values = found.came_from
            rows = {k: v for k, v in found.fields}
            rows["vr_choices"] = " · ".join(("▶ " if taken else "") + text for text, taken in card.choices(var))
            rows["vr_came_from"] = self.t(from_key, **from_values)
            self.detail.show_variable((var.symbol, var.value, var.unit), found.result, var.label, path_text,
                                      found.command, note, rows, calc.source_of(domain) == calc.SOURCE_DOCUMENT, computed, siblings)
        else:
            found = card.domain_card(domain, self.assembly, path)
            for sib in found.siblings:
                role = self.t("vr_computes" if sib.computes else "vr_recalls")
                siblings.append((f"[{self.badge(sib.domain)}] {calc.case_of(sib.domain)} · {role}", (sib.domain.origin, sib.domain.name, None), ""))
            note = self.t(found.command.note) if found.command is not None else self.t("vr_whole_none")
            head = f'<b>{_esc(calc.case_of(domain))}</b> &nbsp;<span style="color:{theme.colour(BADGE_TOKENS[calc.source_of(domain)])}">{_esc(self.badge(domain))}</span>'
            self.detail.show_domain(head, domain.label, path_text, found.command, note,
                                    self.t("vr_domain_counts", count=found.variables, results=found.results), siblings)
        self._set_open(found.tab, found.node, domain)
        self._set_pick_box(var, domain)

    def _set_open(self, tab, node, domain):
        """«Ouvrir l'onglet … ↗» (REQ-009): the computing source's tab, greyed with its reason where the window refuses it (`can_open_tab`) or where no tab computes the domain."""
        self.open_target = (tab, node)
        if not tab:
            self.detail.set_open(self.t("vr_open_none"), False, self.t("vr_open_none_tip"))
            return
        title = self.t(tab)
        can = getattr(self.app, "can_open_tab", None)
        ok, reason = can(tab) if callable(can) else (True, None)
        if not ok:
            document = self.document_name(self.app.current_document()) if callable(getattr(self.app, "current_document", None)) else ""
            self.detail.set_open(self.t("vr_open_tab", tab=title), False, self.t(reason, tab=title, document=document))
            return
        self.detail.set_open(self.t("vr_open_tab", tab=title), True, self.t("vr_open_tab_tip", tab=title, case=calc.case_of(self.assembly.computing(domain))))

    def open_tab(self):
        tab, node = getattr(self, "open_target", (None, None))
        show = getattr(self.app, "show_tab", None)
        if tab and callable(show):
            show(tab, node)

    def _set_pick_box(self, var, domain):
        """The box of the field being linked (REQ-008): what it will follow, or why it may not."""
        if self.pick_done is None or var is None:
            self.detail.set_pick(None, "", False)
            return
        accepted = self.pick_accept is None or self.pick_accept(var, domain)
        from richtext import math_html
        text = self.t("vr_pick_follows", var=math_html(var.symbol), case=_esc(calc.case_of(domain))) if accepted else _esc(self.t("vr_pick_refused"))
        self.detail.set_pick(self.pick_title, text, accepted)

    # -- the choosing mode: a value for a field of another tab (spec 2026-10-11-variables-liees-champs-et-textes; REQ-008) --

    def begin_pick(self, on_done, title, accept=None):
        """`on_done(key)` is called with the (origin, domain, name) chosen, or None where the choice is given up; `accept(var, domain)` is what the field may take -- the menu, the source, the domains, the numbers and the list offer nothing else, so never a document's value. One value: no box, no bar of the choice; the choice of before is kept aside and comes back."""
        self.pick_done = on_done
        self.pick_accept = accept
        self.pick_title = title
        self.pick_label.setText(title)
        self.pick_bar.setVisible(True)
        self.selection.begin_single()
        if self.selection.focus is not None and accept is not None and not self._accepted(self.selection.focus):
            self.selection.focus_on(None)
        self.fill_units()
        self._set_controls()
        self.fill()

    def _accepted(self, key):
        var, domain = self.variable(key), self.domain_of(key)
        return var is not None and (self.pick_accept is None or self.pick_accept(var, domain))

    def pick_chosen(self):
        """«Importer»: the variable chosen handed over, if the field takes it; else the bar says what to do."""
        key = self.selected_key()
        if key is None or key[2] is None or self.variable(key) is None or not self._accepted(key):
            self.pick_label.setText(self.t("vr_pick_none"))
            return
        self.end_pick(key)

    def end_pick(self, key):
        done, self.pick_done = self.pick_done, None
        self.pick_accept = None
        self.pick_bar.setVisible(False)
        self.selection.end_single()
        self.fill_units()
        self._set_controls()
        self.fill()
        if done is not None:
            done(key)

    # -- the contract another tab builds on (REQ-007) --

    def selected_key(self):
        """(origin, domain, name) of the last variable clicked, else of the domain chosen on the left with name None, else None."""
        focus = self.selection.focus
        if focus is not None and self.variable(focus) is not None:
            return tuple(focus)
        if self.filter.domain is not None and tuple(self.filter.domain) in self.domains:
            return (*self.filter.domain, None)
        return None

    def selected_keys(self):
        """Every variable chosen, in the order the list shows them, those the filter hides after them."""
        return self.selection.keys(self.list.shown())

    def select_key(self, key):
        """Chooses (origin, domain, name) again: its domain on the left, the filter opened to it where it hid it, and the variable alone where one is named."""
        if not key:
            return
        origin, name, var_key = tuple(key)
        domain = self.domains.get((origin, name))
        if domain is None:
            return
        if not self.catalogue.in_scope(domain, self.filter):
            self.filter.menu, self.filter.source = query.ALL, query.ALL_SOURCES
            self._set_controls()
        self.filter.domain = (origin, name)
        if var_key is not None and domain.variable(var_key) is not None:
            self.selection.focus_on((origin, name, var_key))
            if not self.catalogue.matches(domain.variable(var_key), domain, self.filter, self.pick_accept):
                self.search.blockSignals(True)
                self.search.setText("")
                self.search.blockSignals(False)
                self.filter.text, self.filter.unit, self.filter.results_only = "", query.ANY_UNIT, False
                self._set_controls()
        else:
            self.selection.focus = None
        self.fill()
        if var_key is not None:
            self.list.scroll_to((origin, name, var_key))

    def domain_of(self, key):
        return self.domains.get((key[0], key[1])) if key else None

    def variable(self, key):
        """The `variables.Variable` a key names, None for a domain's own key or one no longer listed."""
        domain = self.domain_of(key)
        if domain is None or key[2] is None:
            return None
        return domain.variable(key[2])

    def address(self, key):
        """(calculation, instance) an export's domain is called by, None for any other."""
        domain = self.domain_of(key)
        return domain.address if domain is not None and domain.origin == EXPORT else None


def _brush(colour):
    from PySide6.QtGui import QBrush, QColor
    return QBrush(QColor(colour))


def _esc(text):
    import html
    return html.escape(str(text or ""), quote=False)
