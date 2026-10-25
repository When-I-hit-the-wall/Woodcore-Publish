"""The command palette, Ctrl+K (issue #83; docs/ui/command-palette.md): a tab, an action, an object of the project, a variable, a norm, a Typst command or a warning found in a few letters, without going through the navigation.

The engineer, 21.10.2026: «juste sous la barre de recherche il y a des catégories que l'on peut sélectionner […] On ne va pas naviguer avec les flèches, on va naviguer en scrollant avec la souris […] Lorsque l'on clique une fois dessus, ça doit simplement l'activer. Et lorsqu'on double-clique dessus, ça doit l'ouvrir. La touche échappe doit permettre de sortir de ce panneau […] il doit également y avoir en haut à droite une croix […] Tab ne doit pas faire quoi que ce soit […] ce panneau [de droite] devrait tout le temps être ouvert dès que l'on sélectionne quelque chose à gauche».

**What it shows.** The search field and its cross; under it the categories (calc/palette_index.CATEGORIES -- typing a category's first character chooses it); on the left the entries, grouped by kind, the letters found underlined, a check's η coloured by theme's `ok` and `danger`, an action's or a tab's keys beside it; on the right, always in its place so that nothing moves under the pointer, the detail of the entry chosen and what can be done with it. Empty, it shows the entries opened lately in this session and the actions.

**How it is used.** The wheel scrolls without choosing; one click chooses; a double click opens -- the tab brought forward, the action run, the object opened in its tab (MainWindow.open_object) -- and closes the palette; Enter, while typing, opens the first entry. Escape and the cross close it. Tab and the arrows do nothing.

**Where it reads.** Everything but the window's own entries -- its tabs, actions, views and languages, which the window hands in (MainWindow.palette_entries) -- is read by calc/palette_index.py, off the window's thread, each time the palette opens: nothing is kept between two openings but the entries opened lately.

The words, `cp_`, in the window's three languages, are merged into woodcore_gui's STRINGS. It must not import woodcore_gui.
"""

import html

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtGui import QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMenu, QPushButton, QSizePolicy, QToolButton,
                               QVBoxLayout, QWidget)

import palette_index
import project
import theme

SHORTCUT = "Ctrl+K"
SHOWN = 300            # the entries the list holds at most: a query of one letter over a big project narrows as it is typed
RECENT_KEPT = 8        # the entries opened lately, shown first in an empty palette (this session only)

STRINGS = {
    "fr": {
        "cp_search": "Rechercher…",
        "cp_search_button": "Rechercher…   Ctrl K",
        "cp_search_tip": "La palette de commandes : un onglet, une action, un objet, une variable, une norme ou un avertissement en quelques lettres (Ctrl+K)",
        "cp_close": "Fermer (Échap)",
        "cp_cat_all": "Tout",
        "cp_cat_actions": "Actions",
        "cp_cat_objects": "Objets du projet",
        "cp_cat_variables": "Variables",
        "cp_cat_norms": "Normes",
        "cp_cat_warnings": "Avertissements",
        "cp_kind_tab": "Onglets",
        "cp_kind_action": "Actions",
        "cp_kind_view": "Vues de l'onglet",
        "cp_kind_language": "Langue de la fenêtre",
        "cp_kind_position": "Positions",
        "cp_kind_check": "Vérifications",
        "cp_kind_object": "Objets",
        "cp_kind_norm": "Normes",
        "cp_kind_variable": "Variables",
        "cp_kind_command": "Commandes Typst",
        "cp_kind_warning": "Avertissements",
        "cp_recent": "Récents",
        "cp_reading": "Lecture du projet…",
        "cp_nothing": "Rien ne correspond.",
        "cp_choose": "Cliquez sur un élément pour voir son détail et ses actions.",
        "cp_open": "Ouvrir",
        "cp_run": "Exécuter",
        "cp_copy_call": "Copier l'appel Typst",
        "cp_copied": "Copié : {call}",
        "cp_show_plan": "Montrer sur le plan {plan}",
        "cp_new_check": "Nouvelle vérification…",
        "cp_used_by": "Utilisé par",
        "cp_summary": "{checks} vérification(s), η max {eta}",
        "cp_summary_none": "Utilisé par {count} objet(s)",
        "cp_no_graph": "Le graphe des dépendances n'est pas encore écrit : « utilisé par » apparaît après le prochain export.",
        "cp_no_tab": "{what} n'a pas d'onglet où l'ouvrir.",
        "cp_disabled": "Cette action n'est pas disponible maintenant.",
        "cp_unreadable": "Fichier illisible",
        "cp_missing": "Pas encore exporté",
    },
    "de": {
        "cp_search": "Suchen…",
        "cp_search_button": "Suchen…   Ctrl K",
        "cp_search_tip": "Die Befehlspalette: ein Register, eine Aktion, ein Objekt, eine Variable, eine Norm oder eine Warnung in wenigen Buchstaben (Ctrl+K)",
        "cp_close": "Schliessen (Esc)",
        "cp_cat_all": "Alles",
        "cp_cat_actions": "Aktionen",
        "cp_cat_objects": "Projektobjekte",
        "cp_cat_variables": "Variablen",
        "cp_cat_norms": "Normen",
        "cp_cat_warnings": "Warnungen",
        "cp_kind_tab": "Register",
        "cp_kind_action": "Aktionen",
        "cp_kind_view": "Ansichten des Registers",
        "cp_kind_language": "Sprache des Fensters",
        "cp_kind_position": "Positionen",
        "cp_kind_check": "Nachweise",
        "cp_kind_object": "Objekte",
        "cp_kind_norm": "Normen",
        "cp_kind_variable": "Variablen",
        "cp_kind_command": "Typst-Befehle",
        "cp_kind_warning": "Warnungen",
        "cp_recent": "Zuletzt",
        "cp_reading": "Projekt wird gelesen…",
        "cp_nothing": "Nichts passt.",
        "cp_choose": "Ein Element anklicken, um seine Einzelheiten und Aktionen zu sehen.",
        "cp_open": "Öffnen",
        "cp_run": "Ausführen",
        "cp_copy_call": "Typst-Aufruf kopieren",
        "cp_copied": "Kopiert: {call}",
        "cp_show_plan": "Auf dem Plan {plan} zeigen",
        "cp_new_check": "Neuer Nachweis…",
        "cp_used_by": "Verwendet von",
        "cp_summary": "{checks} Nachweis(e), η max {eta}",
        "cp_summary_none": "Von {count} Objekt(en) verwendet",
        "cp_no_graph": "Der Abhängigkeitsgraph ist noch nicht geschrieben: «verwendet von» erscheint nach dem nächsten Export.",
        "cp_no_tab": "{what} hat kein Register, in dem es sich öffnen lässt.",
        "cp_disabled": "Diese Aktion ist jetzt nicht verfügbar.",
        "cp_unreadable": "Datei unlesbar",
        "cp_missing": "Noch nicht exportiert",
    },
    "en": {
        "cp_search": "Search…",
        "cp_search_button": "Search…   Ctrl K",
        "cp_search_tip": "The command palette: a tab, an action, an object, a variable, a norm or a warning in a few letters (Ctrl+K)",
        "cp_close": "Close (Esc)",
        "cp_cat_all": "All",
        "cp_cat_actions": "Actions",
        "cp_cat_objects": "Project objects",
        "cp_cat_variables": "Variables",
        "cp_cat_norms": "Norms",
        "cp_cat_warnings": "Warnings",
        "cp_kind_tab": "Tabs",
        "cp_kind_action": "Actions",
        "cp_kind_view": "Views of the tab",
        "cp_kind_language": "Window language",
        "cp_kind_position": "Positions",
        "cp_kind_check": "Checks",
        "cp_kind_object": "Objects",
        "cp_kind_norm": "Norms",
        "cp_kind_variable": "Variables",
        "cp_kind_command": "Typst commands",
        "cp_kind_warning": "Warnings",
        "cp_recent": "Recent",
        "cp_reading": "Reading the project…",
        "cp_nothing": "Nothing matches.",
        "cp_choose": "Click an entry to see its detail and its actions.",
        "cp_open": "Open",
        "cp_run": "Run",
        "cp_copy_call": "Copy the Typst call",
        "cp_copied": "Copied: {call}",
        "cp_show_plan": "Show on plan {plan}",
        "cp_new_check": "New check…",
        "cp_used_by": "Used by",
        "cp_summary": "{checks} check(s), η max {eta}",
        "cp_summary_none": "Used by {count} object(s)",
        "cp_no_graph": "The graph of dependencies is not written yet: «used by» shows after the next export.",
        "cp_no_tab": "{what} has no tab to open it in.",
        "cp_disabled": "This action is not available now.",
        "cp_unreadable": "File not readable",
        "cp_missing": "Not exported yet",
    },
}

ENTRY = Qt.ItemDataRole.UserRole
RECENT = []   # the keys of the entries opened lately, newest first: this session's, never written


class _Read(QThread):
    """palette_index.build off the window's thread: the variables alone take a second on a project of some size."""

    done = Signal(object, object)

    def __init__(self, here, lang, entries):
        super().__init__()
        self.args = (here, lang, entries)

    def run(self):
        here, lang, entries = self.args
        try:
            found, graph = palette_index.build(here, lang, entries)
        except Exception as exc:  # broad: what could not be read is said in the palette, never lost
            found, graph = list(entries) + [palette_index.Entry("warning", "unreadable:palette", "palette", detail=str(exc), extra={"source": "unreadable"})], None
        self.done.emit(found, graph)


def marked(text, positions):
    """`text` as rich text, the letters at `positions` underlined -- what the query found."""
    chosen = set(positions or ())
    return "".join(f"<u>{html.escape(ch)}</u>" if i in chosen else html.escape(ch) for i, ch in enumerate(text))


def _empty(layout):
    """`layout` emptied, the widgets of its nested layouts deleted too: a nested layout taken out leaves its buttons on the panel, drawn over the next entry's."""
    while layout.count():
        item = layout.takeAt(0)
        if item.widget() is not None:
            item.widget().deleteLater()
        elif item.layout() is not None:
            _empty(item.layout())
            item.layout().deleteLater()


class CommandPalette(QDialog):
    """The palette, over the window: the search field, the categories, the list and the panel. `window` is the MainWindow: it hands in its own entries (`palette_entries`) and does what an entry asks (`palette_open`, `palette_action`)."""

    def __init__(self, window):
        super().__init__(window, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.window_ = window
        self.t = window.t
        self.setObjectName("palette")
        self.setModal(False)
        self.entries = window.palette_entries()
        self.graph = None
        self.chosen = None
        self.reader = None
        self.category = "all"
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        frame = QFrame()
        frame.setObjectName("card")
        outer.addWidget(frame)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 12)
        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(self.t("cp_search"))
        self.search.textChanged.connect(self.on_text)
        self.search.returnPressed.connect(self.open_first)
        top.addWidget(self.search, 1)
        close = QToolButton()
        close.setText("✕")
        close.setToolTip(self.t("cp_close"))
        close.setAutoRaise(True)
        close.clicked.connect(self.reject)
        self.close_button = close
        top.addWidget(close)
        layout.addLayout(top)
        cats = QHBoxLayout()
        cats.setSpacing(0)
        self.category_buttons = {}
        for n, (key, prefix) in enumerate(palette_index.CATEGORIES):
            button = QToolButton()
            button.setText(self.t("cp_cat_" + key) + (f"  {prefix}" if prefix else ""))
            button.setCheckable(True)
            button.setProperty("segment", "first" if n == 0 else "last" if n == len(palette_index.CATEGORIES) - 1 else "middle")
            button.setProperty("soft", True)
            button.clicked.connect(lambda _checked=False, key=key: self.choose_category(key))
            cats.addWidget(button)
            self.category_buttons[key] = button
        cats.addStretch(1)
        layout.addLayout(cats)
        body = QHBoxLayout()
        self.list = QListWidget()
        self.list.setObjectName("paletteList")
        self.list.setFocusPolicy(Qt.FocusPolicy.NoFocus)   # the arrows do not move through it: the wheel scrolls, a click chooses (the engineer, 21.10.2026)
        self.list.setMouseTracking(True)
        self.list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.list.itemClicked.connect(self.on_click)
        self.list.itemDoubleClicked.connect(self.on_double_click)
        body.addWidget(self.list, 3)
        self.panel = QFrame()
        self.panel.setObjectName("palettePanel")
        self.panel_layout = QVBoxLayout(self.panel)
        self.panel_layout.setContentsMargins(10, 4, 4, 4)
        # always there, the same width before and after the first click (UI-001): the two share the width by their stretch alone, never by what they hold
        for widget in (self.list, self.panel):
            widget.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        body.addWidget(self.panel, 2)
        layout.addLayout(body, 1)
        self.status = QLabel()
        self.status.setObjectName("meta")
        layout.addWidget(self.status)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, activated=self.reject)
        self.choose_category("all", refill=False)
        self.show_panel(None)
        self.fill()
        self.read()

    # --- the keyboard: Escape closes, Tab and the arrows do nothing -------------------------

    def focusNextPrevChild(self, _next):
        return False   # Tab does nothing (the engineer, 21.10.2026)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab, Qt.Key.Key_Up, Qt.Key.Key_Down):
            event.accept()
            return
        super().keyPressEvent(event)

    def place(self):
        """Over the window's top, wide: two thirds of it, never narrower than a list and its panel side by side."""
        window = self.window_
        width = max(720, int(window.width() * 0.66))
        height = max(420, int(window.height() * 0.62))
        self.setFixedSize(min(width, window.width() - 40), min(height, window.height() - 80))   # fixed: what the panel shows never widens the palette under the pointer
        corner = window.mapToGlobal(window.rect().topLeft())
        self.move(corner.x() + (window.width() - self.width()) // 2, corner.y() + 60)

    # --- reading -----------------------------------------------------------------------------

    def read(self):
        """The project's entries read off the window's thread; the window's own are there at once."""
        self.status.setText(self.t("cp_reading"))
        self.reader = _Read(project.current(), self.window_.lang, self.entries)
        self.reader.done.connect(self.on_read)
        self.reader.start()

    def on_read(self, entries, graph):
        self.entries, self.graph = entries, graph
        self.status.setText("" if graph is not None else self.t("cp_no_graph"))
        self.fill()

    def done(self, result):
        if self.reader is not None and self.reader.isRunning():
            self.reader.wait(10000)
        super().done(result)

    # --- the list ---------------------------------------------------------------------------

    def choose_category(self, key, refill=True):
        """A category clicked: what the field holds kept, its first character the category's."""
        self.category = key
        for other, button in self.category_buttons.items():
            button.setChecked(other == key)
        if refill:
            _category, text = palette_index.parse(self.search.text())
            prefix = dict(palette_index.CATEGORIES)[key]
            self.search.blockSignals(True)
            self.search.setText(prefix + text)
            self.search.blockSignals(False)
            self.fill()
        self.search.setFocus()

    def on_text(self, text):
        category, _rest = palette_index.parse(text)
        if text[:1] in palette_index.PREFIXES or category != self.category:
            self.choose_category(category, refill=False)
        elif self.category != "all" and not text[:1] in palette_index.PREFIXES:
            self.choose_category("all", refill=False)
        self.fill()

    def query(self):
        return self.search.text()

    def found(self):
        """The entries the field finds, with their letters; an empty «all» palette its recent entries first."""
        query = self.query()
        hits = palette_index.search(self.entries, query)
        if not palette_index.parse(query)[1] and self.category == "all":
            by_key = {entry.key: entry for entry in self.entries}
            recent = [(by_key[key], []) for key in RECENT if key in by_key]
            actions = [(entry, positions) for entry, positions in hits if entry.kind in ("tab", "action")]
            return recent, actions
        return [], hits

    def fill(self):
        """The list filled again: the groups by kind, each entry a row of rich text."""
        self.list.clear()
        recent, hits = self.found()
        rows = 0
        if recent:
            self._head(self.t("cp_recent"))
            for entry, positions in recent:
                self._row(entry, positions)
        kind = None
        for entry, positions in hits[:SHOWN]:
            if entry.kind != kind:
                kind = entry.kind
                self._head(self.t("cp_kind_" + kind))
            self._row(entry, positions)
            rows += 1
        if not rows and not recent:
            self._head(self.t("cp_nothing"))
        if self.chosen is not None and not any(self.list.item(i).data(ENTRY) is self.chosen for i in range(self.list.count())):
            self.show_panel(None)

    def _head(self, text):
        item = QListWidgetItem(text.upper())
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        item.setForeground(theme.qcolor("muted"))
        self.list.addItem(item)

    def _row(self, entry, positions):
        item = QListWidgetItem()
        item.setData(ENTRY, entry)
        self.list.addItem(item)
        row = QWidget()
        line = QHBoxLayout(row)
        line.setContentsMargins(6, 2, 6, 2)
        text = entry.label
        name = QLabel(marked(text, [p for p in positions if p < len(text)]) + (f"  <span style='color:{theme.colour('muted')}'>{html.escape(entry.ident)}</span>" if entry.ident and entry.ident != entry.label else ""))
        name.setTextFormat(Qt.TextFormat.RichText)
        line.addWidget(name, 1)
        if entry.eta is not None:
            eta = QLabel(f"η {entry.eta:.2f}")
            eta.setStyleSheet(f"color: {theme.colour('ok' if entry.ok else 'danger')}; font-weight: 600;")
            line.addWidget(eta)
        keys = (entry.extra or {}).get("shortcut")
        if keys:
            hint = QLabel(keys)
            hint.setObjectName("meta")
            line.addWidget(hint)
        if (entry.extra or {}).get("enabled") is False:
            name.setEnabled(False)
        item.setSizeHint(row.sizeHint())
        self.list.setItemWidget(item, row)

    # --- choosing and opening -------------------------------------------------------------------

    def entry_of(self, item):
        return item.data(ENTRY) if item is not None else None

    def on_click(self, item):
        entry = self.entry_of(item)
        if entry is not None:
            self.show_panel(entry)

    def on_double_click(self, item):
        entry = self.entry_of(item)
        if entry is not None:
            self.open_entry(entry)

    def open_first(self):
        """Enter while typing: the first entry found opened."""
        recent, hits = self.found()
        first = (recent or hits or [(None, [])])[0][0]
        if first is not None:
            self.open_entry(first)

    def open_entry(self, entry):
        """`entry` opened -- the tab brought forward, the action run, the object opened in its tab -- and the palette closed first: an action may build the window again."""
        if (entry.extra or {}).get("enabled") is False:
            self.status.setText(self.t("cp_disabled"))
            return
        if entry.key in RECENT:
            RECENT.remove(entry.key)
        RECENT.insert(0, entry.key)
        del RECENT[RECENT_KEPT:]
        self.accept()
        self.window_.palette_open(entry)

    # --- the panel ------------------------------------------------------------------------------

    def show_panel(self, entry):
        """The panel on the right: the entry chosen, its detail and what can be done with it -- or the line saying to click one. Never hidden: nothing moves under the pointer at the first click."""
        self.chosen = entry
        _empty(self.panel_layout)
        if entry is None:
            hint = QLabel(self.t("cp_choose"))
            hint.setWordWrap(True)
            hint.setObjectName("meta")
            self.panel_layout.addWidget(hint)
            self.panel_layout.addStretch(1)
            return
        title = QLabel(f"<b>{html.escape(entry.label)}</b>" + (f"  {html.escape(entry.ident)}" if entry.ident and entry.ident != entry.label else ""))
        title.setWordWrap(True)
        self.panel_layout.addWidget(title)
        source = (entry.extra or {}).get("source")
        kind = QLabel(self.t({"missing": "cp_missing", "unreadable": "cp_unreadable"}.get(source, "cp_kind_" + entry.kind)))
        kind.setObjectName("meta")
        self.panel_layout.addWidget(kind)
        if entry.detail:
            detail = QLabel(entry.detail)
            detail.setWordWrap(True)
            detail.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.panel_layout.addWidget(detail)
        if entry.eta is not None:
            eta = QLabel(f"η = {entry.eta:.2f}")
            eta.setStyleSheet(f"color: {theme.colour('ok' if entry.ok else 'danger')}; font-weight: 600;")
            self.panel_layout.addWidget(eta)
        if entry.node and entry.kind in ("position", "check", "object"):
            self._uses(entry)
        self._actions(entry)
        self.panel_layout.addStretch(1)

    def _uses(self, entry):
        if self.graph is None:
            note = QLabel(self.t("cp_no_graph"))
            note.setWordWrap(True)
            note.setObjectName("meta")
            self.panel_layout.addWidget(note)
            return
        etas = {e.node.split(":", 1)[1]: (e.eta, e.ok) for e in self.entries if e.kind == "check" and e.eta is not None}
        found = palette_index.summary(self.graph, entry.node, etas)
        checks = found["count"].get("check", 0) + found["count"].get("steel", 0)
        line = self.t("cp_summary", checks=checks, eta=f"{found['eta_max']:.2f}") if found["eta_max"] is not None else self.t("cp_summary_none", count=len(found["used_by"]))
        summary = QLabel(line)
        summary.setWordWrap(True)
        self.panel_layout.addWidget(summary)
        if found["used_by"]:
            self.panel_layout.addWidget(QLabel(f"<b>{html.escape(self.t('cp_used_by'))}</b>"))
            uses = QListWidget()
            uses.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            for node in found["used_by"]:
                item = QListWidgetItem(node.replace(":", " · ", 1))
                item.setData(ENTRY, node)
                uses.addItem(item)
            uses.itemDoubleClicked.connect(lambda item: (self.accept(), self.window_.palette_open(palette_index.Entry("object", item.data(ENTRY), item.text(), node=item.data(ENTRY)))))
            uses.setMaximumHeight(140)
            self.panel_layout.addWidget(uses)
        self.entry_plans = [node for node in found["used_by"] if node.startswith("plan:")]

    def _actions(self, entry):
        """What can be done with the entry: open it, and for an object copy its Typst call, show it on a plan, start a check of a position."""
        buttons = QVBoxLayout()
        opener = QPushButton(self.t("cp_run" if entry.kind in ("action", "view", "language") else "cp_open"))
        opener.setProperty("primary", True)
        opener.clicked.connect(lambda: self.open_entry(entry))
        buttons.addWidget(opener)
        if entry.node:
            call = palette_index.typst_call(entry.node)
            if call:
                copy = QPushButton(self.t("cp_copy_call"))
                copy.setToolTip(call)
                copy.clicked.connect(lambda _c=False, call=call: self.copy(call))
                buttons.addWidget(copy)
        for plan in getattr(self, "entry_plans", [])[:3] if entry.kind == "position" else []:
            show = QPushButton(self.t("cp_show_plan", plan=plan.split(":", 1)[1]))
            show.clicked.connect(lambda _c=False, plan=plan: self.open_entry(palette_index.Entry("object", plan, plan, node=plan)))
            buttons.addWidget(show)
        if entry.kind == "position":
            tabs = self.window_.palette_check_tabs()
            if tabs:
                new = QPushButton(self.t("cp_new_check"))
                menu = QMenu(new)
                for key, title in tabs:
                    menu.addAction(title, lambda key=key, pid=entry.node.split(":", 1)[1]: (self.accept(), self.window_.palette_new_check(key, pid)))
                new.setMenu(menu)
                buttons.addWidget(new)
        self.entry_plans = []
        self.panel_layout.addLayout(buttons)

    def copy(self, call):
        QGuiApplication.clipboard().setText(call)
        self.status.setText(self.t("cp_copied", call=call))


class PdfAction:
    """The PDF button's own click, offered as an action of the palette: its words, what it does and whether it can, in the part of QAction's interface the palette reads."""

    def __init__(self, button):
        self.button = button

    def text(self):
        return self.button.text()

    def trigger(self):
        self.button.click()

    def isEnabled(self):
        return self.button.isEnabled()

    def isCheckable(self):
        return False

    def isChecked(self):
        return False

    def shortcut(self):
        return QKeySequence()


class PaletteWindowMixin:
    """What the window does for its palette (MainWindow names this mixin among its bases): Ctrl+K and the field of the top bar open it; it hands in its own entries -- the tabs of the document shown, the actions of its menus and of the PDF button, the views of the tab in front, the languages --, read off the window itself and copied nowhere (Q-002, Q-006); and it does what an entry asks."""

    def bind_palette(self, top):
        """The field «Rechercher… Ctrl K» in the top bar, and Ctrl+K on the window."""
        button = QPushButton(self.t("cp_search_button"))
        button.setObjectName("paletteField")
        button.setToolTip(self.t("cp_search_tip"))
        button.clicked.connect(self.open_palette)
        top.addWidget(button)
        self.palette_button = button
        if getattr(self, "palette_shortcut", None) is None:
            self.palette_shortcut = QShortcut(QKeySequence(SHORTCUT), self, activated=self.open_palette)

    def open_palette(self):
        """The palette over the window -- not while a variable is being chosen for a tab (begin_variable_pick), every other module being unavailable then."""
        if getattr(self, "picking", False):
            return None
        palette = CommandPalette(self)
        palette.place()
        palette.show()
        palette.search.setFocus()
        self.palette = palette
        return palette

    def palette_entries(self):
        """The window's own entries: the tabs the navigation shows and can open, each with its Ctrl+n; every action of the menus and of the PDF button, with its path, its keys and whether it can run; the views of the tab in front; the window's languages."""
        from tab_registry import NAV_GROUPS, TABS
        import views
        entries = []
        group_of = {key: group for group, members in NAV_GROUPS for key in members}
        for n, index in enumerate(self.nav.order()):
            key = TABS[index][0]
            entries.append(palette_index.Entry("tab", f"tab:{key}", self.t(key), detail=self.t(group_of[key]) if key in group_of else "", data=index,
                                               extra={"shortcut": f"Ctrl+{n + 1}" if n < 9 else ""}))
        for path, action in self.palette_actions():
            text = action.text().replace("&", "")
            entries.append(palette_index.Entry("action", "action:" + " › ".join(path + [text]), text, detail=" › ".join(path), data=action,
                                               extra={"shortcut": action.shortcut().toString(QKeySequence.SequenceFormat.NativeText), "enabled": action.isEnabled(),
                                                      "checked": action.isChecked() if action.isCheckable() else None}))
        tab = self.tab_widget.currentWidget()
        if tab is not None:
            for key, name, tip in views.items(tab, self.t):
                entries.append(palette_index.Entry("view", f"view:{key}", name, detail=tip, data=key, extra={"checked": getattr(tab, "view", None) == key}))
        for code in self.language.codes:
            entries.append(palette_index.Entry("language", f"language:{code}", self.language.names[code], ident=code.upper(), data=code, extra={"checked": code == self.lang}))
        return entries

    def palette_actions(self):
        """[(menu path, action)] of every action the window offers: its menu bar's, walked into every submenu, and the PDF button's -- its click and its menu --, separators, actions without words and submenus themselves left out. Read now: the menus are built again with the window."""
        found = []

        def walk(actions, path):
            for action in actions:
                if action.isSeparator() or not action.isVisible():
                    continue
                menu = action.menu()
                if menu is not None:
                    walk(menu.actions(), path + [action.text().replace("&", "")])
                elif action.text().strip():
                    found.append((path, action))

        walk(self.menuBar().actions(), [])
        pdf = getattr(self, "pdf_button", None)
        if pdf is not None:
            found.append(([], PdfAction(pdf)))
            if pdf.menu() is not None:
                walk(pdf.menu().actions(), [pdf.text().replace("&", "")])
        return found

    def palette_check_tabs(self):
        """[(tab key, title)] of the tabs where a check is made -- those whose `GRAPH_KIND` is a check's, read off the tabs themselves -- that the document shown can open."""
        from tab_registry import TABS
        return [(key, self.t(key)) for (key, _factory), tab in zip(TABS, self.tabs)
                if getattr(tab, "GRAPH_KIND", None) in ("check", "steel") and hasattr(tab, "new") and self.available(key)]

    def palette_new_check(self, key, position):
        """A new check of position `position` opened in tab `key`: the tab brought forward, a new draft made (its own «Nouveau»), its position set."""
        from tab_registry import TABS
        index = next(i for i, (k, _f) in enumerate(TABS) if k == key)
        tab = self.tabs[index]
        self.tab_widget.setCurrentIndex(index)
        tab.new()
        source = getattr(tab, "source", None)
        if isinstance(source, dict) and "position" in source:
            source["position"] = position
            tab.fill_form()
            if hasattr(tab, "refresh"):
                tab.refresh()

    def palette_open(self, entry):
        """What a double click on `entry` does: a tab brought forward, an action run, a view or a language chosen, an object opened in its tab (open_object), a warning's object or file opened, a variable or a command shown in its tab."""
        kind = entry.kind
        if kind == "tab":
            self.tab_widget.setCurrentIndex(entry.data)
        elif kind == "action":
            entry.data.trigger()
        elif kind == "view":
            self.on_view_chosen(entry.data)
        elif kind == "language":
            self.language.setCurrentIndex(self.language.codes.index(entry.data))
        elif entry.node:
            if not self.open_object(entry.node):
                self.set_status(self.t("cp_no_tab", what=entry.node.replace(":", " · ", 1)))
        elif kind == "warning" and (entry.extra or {}).get("file"):
            path = project.current().root / entry.extra["file"]
            if path.is_file():
                import sys
                sys.modules[type(self).__module__].open_in_editor(path, (entry.extra or {}).get("line"))
        elif kind == "variable":
            self._palette_show_in("tab_variables", (entry.extra or {}).get("key", entry.label))
        elif kind == "command":
            self._palette_show_in("tab_commands", (entry.extra or {}).get("name", entry.label))
        elif kind == "norm" and (entry.extra or {}).get("checks"):
            first = entry.extra["checks"][0]
            self.open_object(f"check:{first}") or self.open_object(f"steel:{first}")

    def _palette_show_in(self, key, text):
        """Tab `key` brought forward, its search field holding `text` where it has one."""
        from tab_registry import TABS
        index = next((i for i, (k, _f) in enumerate(TABS) if k == key), None)
        if index is None:
            return
        self.tab_widget.setCurrentIndex(index)
        search = getattr(self.tabs[index], "search", None)
        if isinstance(search, QLineEdit):
            search.setText(text)
