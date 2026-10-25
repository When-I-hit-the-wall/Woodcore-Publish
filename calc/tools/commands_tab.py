"""Woodcore's commands tab: every command of the report, one condensed page each (docs/ui/tab-commands.md; spec 2026-10-24-onglet-commandes-pages, issue #115; docs/typst/command-docs.md §10sexies).

**One view, three panes** (UI-001, D-2): on the left the search and the commands by category (command_list), in the centre the page of the command (command_page_view), on the right the lines to copy, the list of the examples and the calls of the command in the open project (command_side). No view to switch, no module of state, no bubble of a norm: the commands are fixed.

**The page is the website's** (ARCH-008, D-13): what it says is command_page's data -- the lead, the line of the command and its bubbles, the key points, the table of the arguments --, read from calc/i18n/command-pages.json, written by hand in French, German and English, and from the signature of lib/; the bubble of a value shows the call and the print build_examples compiled once (examples/out/values/), never a compile when a page opens (REQ-012). The examples are the `///` blocks' fences and their committed pages (command_examples).

**A thin tab** (ARCH-007): three components, each built on the same small context and each with `state()`, `restore()`, `shown()` and `hidden()`, speaking through signals -- a row chosen, an example chosen. Since issue #106 the tab is a class of parameters on the type «Données» (data_tab.DataTab, spec 2026-10-24-type-donnees), without the type's banner -- it reads lib/, not the export --, and the three components are mounted by one whole service, `CommandsBrowser` (`tab.service("browser")`), which holds the context, the splitter and the wiring; the command palette's `search` is exposed on the tab (`EXPOSES`). This module holds them, and the words of the window's own chrome (STRINGS); every word of the page is calc/i18n/reference.json's (command_docs.word), the site's too.

⚠️ It must not import woodcore_gui -- woodcore_gui imports this module to fill TABS, so the two would be circular.
"""

from types import SimpleNamespace

import build_reference as ref
import command_docs as docs  # the reference's words (command_docs.py)
import command_examples
import command_list
import command_usage
import project  # the project whose ids fill the calls to copy, and whose files «Dans ce projet» reads (calc/project.py)
from command_list import CommandList
from command_page_view import CommandPage
from command_side import CommandSide
from data_tab import DataTab
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget
from tab_frame import Service

# The tab's texts, in the window's three languages -- merged into woodcore_gui.STRINGS. The prefix is `ref_`. What is NOT here: the categories' names and every word the page says, calc/i18n/reference.json's and the website's too (command_docs.category_label, command_docs.word); nor the pages themselves, calc/i18n/command-pages.json's. What is left is the chrome the site has no use for: what the tab says of an internal, of a page it could not show and of an example's level.
STRINGS = {
    "fr": {
        "tab_commands": docs.word("commands", "fr"),
        "ref_internal_note": "Auxiliaire du moteur. Le caractère générique de commands.typ l'exporte comme les autres, donc ce nom atteint chaque fichier de Sections/ — mais ce n'est pas une commande du rapport : ni documentée, ni stable. Ne pas l'appeler.",
        "ref_hint": "Choisir une commande à gauche.",
        "ref_level_fixed": "fixé à {level} par l'appel lui-même, qui l'emporte sur celui du rapport",
        "ref_missing": "Aucune image enregistrée pour cet exemple — lancer calc/tools/build_examples.py.",
        "ref_stale": "L'exemple a changé depuis l'image enregistrée — relancer calc/tools/build_examples.py.",
        "ref_rendering": "Compilation…",
        "ref_render_failed": "L'exemple ne compile pas :",
        "ref_no_typst": "typst est introuvable sur le PATH.",
        "ref_german_page": "Page en allemand : cet exemple n'a pas pu être compilé en français — {reason}",
        "ref_no_examples": "Cette commande n'a pas encore d'exemple.",
        "ref_pages_error": "Les pages des commandes ne se lisent pas : {error}",
    },
    "de": {
        "tab_commands": docs.word("commands", "de"),
        "ref_internal_note": "Hilfsfunktion der Engine. Der Platzhalter in commands.typ exportiert sie wie alles andere, der Name erreicht also jede Datei in Sections/ — ein Befehl des Berichts ist sie aber nicht: weder dokumentiert noch stabil. Nicht aufrufen.",
        "ref_hint": "Links einen Befehl wählen.",
        "ref_level_fixed": "vom Aufruf selbst auf {level} gesetzt, was die Stufe des Berichts übergeht",
        "ref_missing": "Für dieses Beispiel ist kein Bild abgelegt — calc/tools/build_examples.py ausführen.",
        "ref_stale": "Das Beispiel hat sich seit dem abgelegten Bild geändert — calc/tools/build_examples.py erneut ausführen.",
        "ref_rendering": "Wird kompiliert…",
        "ref_render_failed": "Das Beispiel kompiliert nicht:",
        "ref_no_typst": "typst ist im PATH nicht zu finden.",
        "ref_german_page": "Deutsche Seite: dieses Beispiel liess sich nicht in der Sprache des Fensters kompilieren — {reason}",
        "ref_no_examples": "Für diesen Befehl gibt es noch kein Beispiel.",
        "ref_pages_error": "Die Seiten der Befehle lassen sich nicht lesen: {error}",
    },
    "en": {
        "tab_commands": docs.word("commands", "en"),
        "ref_internal_note": "An engine helper. commands.typ's wildcard exports it like everything else, so the name does reach every file of Sections/ — but it is not a command of the report: neither documented nor stable. Do not call it.",
        "ref_hint": "Choose a command on the left.",
        "ref_level_fixed": "fixed at {level} by the call itself, which outranks the report's own",
        "ref_missing": "No committed page for this example — run calc/tools/build_examples.py.",
        "ref_stale": "The example has changed since its committed page — run calc/tools/build_examples.py again.",
        "ref_rendering": "Compiling…",
        "ref_render_failed": "The example does not compile:",
        "ref_no_typst": "typst is not on the PATH.",
        "ref_german_page": "German page: this example could not be compiled in English — {reason}",
        "ref_no_examples": "This command has no example yet.",
        "ref_pages_error": "The commands' pages cannot be read: {error}",
    },
}

CATEGORY_ORDER = command_list.CATEGORY_ORDER   # build_reference.CATEGORIES' order, the site's; Internes last
pinned_level = command_examples.pinned_level
CODE_SPAN, BOLD, ITALIC = docs.PROSE_CODE_SPAN, docs.BOLD, docs.ITALIC


def prose_html(text, mono_family):
    """One sentence as rich text: the code between backticks in the fixed font, **bold** and *italic* as such, everything else escaped (command_docs.prose)."""
    import html
    return docs.prose(text, lambda code: f'<span style="font-family: \'{mono_family}\', monospace;">{html.escape(code)}</span>',
                      lambda words: html.escape(words, quote=False), r"<b>\1</b>", r"<i>\1</i>")


def prose_plain(text):
    """The same sentence as plain text: the markers dropped, the words kept."""
    return docs.prose(text, lambda code: code, lambda words: words, r"\1", r"\1")


def read_records():
    """Every binding of the lib files, with its doc block read and its category decided: the records the three panes share. The block is kept as `english`, where command_docs.example_levels reads it."""
    records = []
    for binding in ref.lib_bindings(ref.ROOT):
        block = ref.parse_doc_block(binding["doc_lines"])
        record = dict(binding)
        record.update(block)
        record["english"] = block
        record["category"] = ref.category_of(binding["name"])
        records.append(record)
    return records


def context(app):
    """What every pane is built on: the window's words and fonts, its language, the records, the calls' samples and the open project's files."""
    lang = getattr(app, "lang", "en")
    current = project.current()
    try:
        root = current.typst_root
    except Exception:   # broad: a project whose layout cannot say its root -- «Dans ce projet» then lists nothing
        root = None
    return SimpleNamespace(app=app, t=app.t, lang=lang, records=read_records(), samples=ref.sample_arguments(current.data_dir),
                           usage=command_usage.UsageIndex(root), word=lambda key, **values: docs.word(key, lang, **values))


class CommandsBrowser(Service):
    """The three panes, side by side -- the list, the page, the right-hand pane --, one whole service (D-03 of the spec 2026-10-24-type-donnees). Filled once as it is mounted, with the state the window kept (`ctx.kept`, ARCH-008): the open rows, the search, the row chosen, the examples' levels."""

    NAME = "browser"
    ZONE = "body"

    def mount(self, ctx):
        super().mount(ctx)
        self.t = ctx.t
        self.panes = context(ctx.app)    # the small context the three panes are built on (not the tab's: no pane knows the type)
        self.lang = self.panes.lang
        self.records = self.panes.records
        self.samples = self.panes.samples
        state = ctx.kept(self.NAME)
        self.widget = QWidget()
        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(6, 6, 6, 6)
        self.list = CommandList(self.panes, state)
        self.page = CommandPage(self.panes, state)
        self.side = CommandSide(self.panes)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        for pane in (self.list, self.page, self.side):
            self.splitter.addWidget(pane)
        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 6)
        self.splitter.setStretchFactor(2, 3)
        self.splitter.setSizes([2500, 6000, 3500])   # the sizes kept through a rebuild are the frame's, given back after
        layout.addWidget(self.splitter, 1)
        self.list.chosen.connect(self.on_chosen)
        self.list.copy_requested.connect(self.copy_main)
        self.side.example_chosen.connect(self.page.flash_example)
        self.list.refill()
        return self.widget

    # what the window and the command palette reach by name (the palette's `search` exposed on the tab)
    @property
    def search(self):
        return self.list.search

    @property
    def tree(self):
        return self.list.tree

    @property
    def nodes(self):
        return self.list.nodes

    @property
    def boxes(self):
        return self.page.boxes

    def record(self, name):
        return next((r for r in self.records if r["name"] == name), None)

    def on_chosen(self, iid):
        record = self.record(iid[4:]) if iid.startswith("cmd|") else None
        self.page.set_selection(iid, record)
        self.side.set_command(record)

    def copy_main(self, iid):
        record = self.record(iid[4:]) if iid.startswith("cmd|") else None
        calls = docs.calls(record, self.samples) if record is not None and record["category"] != ref.INTERNAL else []
        if calls:
            self.app.copy(calls[0][1])

    # the life of the panes: the tab shown on the screen, hidden (the frame's phases `revealed` and `hidden`, its showEvent and hideEvent)
    def revealed(self):
        for pane in (self.list, self.page, self.side):
            pane.shown()

    def hidden(self):
        for pane in (self.list, self.page, self.side):
            pane.hidden()

    def state(self):
        """The union of the panes' states (the splitter's sizes are the frame's)."""
        return {**self.list.state(), **self.page.state(), **self.side.state()}

    def restore(self, state):
        """Nothing: the state the frame gives back after the mount is the one `mount` was built with (`ctx.kept`), and filling the tree again would fill it twice (ARCH-008)."""


class CommandsTab(DataTab):
    """The tab: the browser of the commands, without the type's banner. Parameters only (tests/test_tab_overrides.py)."""

    KEY = "tab_commands"
    SERVICES = (CommandsBrowser,)
    EXPOSES = {"search": "browser"}   # the command palette writes a command's name in it (command_palette._palette_show_in)
