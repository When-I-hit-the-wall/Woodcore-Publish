"""Woodcore's commands tab: every command this project defines, what its arguments are, and what it prints (docs/typst/command-docs.md §10sexies).

`commands.typ` re-exports all three files of lib/ with a bare wildcard, so every top-level name of lib/ -- 237 at v0.86 -- reaches every Sections/*.typ, and nothing at the point of use says which of them are the 64 an engineer calls. This tab says it: the categories of commands, and everything else folded into one row marked as the engine's own.

Every word of a command's documentation is read out of the `///` blocks of lib/ -- the same text Tinymist shows on hover and docs/typst-reference.xlsx carries -- so there is no second description of a command to keep in step (section 2 rule 1). The examples are the ```typ fences of those blocks, and held by tests/test_commands.py.

**One set of data for the window and the website (v0.94).** The engineer: «la liste des commandes, leur description et exemples dans le katalog ou le site internet doivent partager un même set de données». So the order of the categories is build_reference.CATEGORIES' -- calculating in the report first --, a category's name and the line that introduces it, and every word the reference says beside a command («Arguments», «Appel minimal», «Exemple 1», «Niveau», «Défini dans»), are calc/i18n/reference.json's, read through command_docs as website/build.py reads them; a command's signature, its arguments' rows, the calls it offers and the levels each example is shown at are command_docs' too (`signature`, `arguments`, `calls`, `example_levels`). The tab's STRINGS carry only the words of its own chrome that the site has no use for. The detail pane is laid out as the site's command page: the category, the name, the signature coloured, the paragraphs, the arguments as a table, what it returns, the minimal and the complete call, the examples with their code and their page -- the 1 · 2 · 3 levels where example_levels gives three --, and where it is defined.

**In a French or German window the documentation is shown in that language (v0.86).** Its translation is kept in calc/i18n/commands.json, one unit per paragraph and per argument, each carrying the English it translates (command_docs.py): a unit whose English has changed since is shown in English and the pane says how many, until tests/test_commands.py -- which names it -- sees it translated again. The English stays the source, and what Tinymist and the workbook show.

**And so are the examples (v0.94).** A German window shows the committed pages (examples/out, build_examples.py), a load and not a run of Typst. A French or English one shows the page a report of its language prints, compiled on demand by command_preview.render_localised -- the very document the website compiles its pages from -- in a thread of its own, «Compilation…» standing where the page will be, and kept in the cache (%LOCALAPPDATA%\\Woodcore\\examples), so the second look is a load. Where Typst is absent or the compile fails, the German page is shown with one line saying why. The window shows every example: the website's masking of the norm tables (website/site.json) is the site's alone.

The prose is set as the `///` blocks write it: `code` between backticks in the window's fixed font, **bold** and *italic* as such, rather than as the asterisks and backticks they are typed with.

The tab lives in its own module rather than in woodcore_gui.py, which lists it in its TABS and merges STRINGS below into its own: the window's language, shortcuts and closing rules are woodcore_gui's, the tab's texts and behaviour are here. ⚠️ It must not import woodcore_gui -- woodcore_gui imports this module to fill TABS, so the two would be circular; the handful of helpers it would borrow are small and restated here instead.
"""

import html
import threading

import build_examples as examples
import build_reference as ref
import command_docs as docs  # the reference's words, the French and German of the documentation, and the site's decisions (command_docs.py)
import command_preview as preview
import project  # the project whose ids fill the calls to copy (calc/project.py)
import richtext  # the calls and the examples coloured as the site's code, «Copié ✓» (richtext.py, v0.92)
import theme
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QImage, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QButtonGroup, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMenu, QPlainTextEdit, QScrollArea, QSplitter, QToolButton,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)
from shiboken6 import isValid

# The tab's texts, in the window's three languages -- merged into woodcore_gui.STRINGS, which checks that every language carries every key. The prefix is `ref_`: `cmd_` is the loads tab's, and a key defined twice would be silently overwritten by whichever module merged last.
#
# What is NOT here (v0.94): the categories' names and every word the reference says about a command, which are calc/i18n/reference.json's and the website's too (command_docs.category_label, command_docs.word); nor the documentation itself, the /// blocks' English and calc/i18n/commands.json's French and German. The tab's own title is reference.json's word, under the key woodcore_gui names the tab by. What is left is the chrome the site has no use for: the tree's count and its summary column, the arguments table's column names, and what the tab says about a page it could not show.
STRINGS = {
    "fr": {
        "tab_commands": docs.word("commands", "fr"),
        "ref_internal_note": "Auxiliaire du moteur. Le caractère générique de commands.typ l'exporte comme les autres, donc ce nom atteint chaque fichier de Sections/ — mais ce n'est pas une commande du rapport : ni documentée, ni stable. Ne pas l'appeler.",
        "ref_col_summary": "Description",
        "ref_col_name": "Nom",
        "ref_col_type": "Type",
        "ref_col_default": "Défaut",
        "ref_count": "{shown} sur {total} commandes · {internal} internes",
        "ref_hint": "Choisir une commande à gauche.",
        "ref_level_fixed": "fixé à {level} par l'appel lui-même, qui l'emporte sur celui du rapport",
        "ref_missing": "Aucune image enregistrée pour cet exemple — lancer calc/tools/build_examples.py.",
        "ref_stale": "L'exemple a changé depuis l'image enregistrée — relancer calc/tools/build_examples.py.",
        "ref_rendering": "Compilation…",
        "ref_render_failed": "L'exemple ne compile pas :",
        "ref_no_typst": "typst est introuvable sur le PATH.",
        "ref_german_page": "Page en allemand : cet exemple n'a pas pu être compilé en français — {reason}",
        "ref_no_examples": "Cette commande n'a pas encore d'exemple.",
        "ref_no_doc": "Cette commande n'a pas encore de bloc /// dans lib/.",
    },
    "de": {
        "tab_commands": docs.word("commands", "de"),
        "ref_internal_note": "Hilfsfunktion der Engine. Der Platzhalter in commands.typ exportiert sie wie alles andere, der Name erreicht also jede Datei in Sections/ — ein Befehl des Berichts ist sie aber nicht: weder dokumentiert noch stabil. Nicht aufrufen.",
        "ref_col_summary": "Beschreibung",
        "ref_col_name": "Name",
        "ref_col_type": "Typ",
        "ref_col_default": "Vorgabe",
        "ref_count": "{shown} von {total} Befehlen · {internal} interne",
        "ref_hint": "Links einen Befehl wählen.",
        "ref_level_fixed": "vom Aufruf selbst auf {level} gesetzt, was die Stufe des Berichts übergeht",
        "ref_missing": "Für dieses Beispiel ist kein Bild abgelegt — calc/tools/build_examples.py ausführen.",
        "ref_stale": "Das Beispiel hat sich seit dem abgelegten Bild geändert — calc/tools/build_examples.py erneut ausführen.",
        "ref_rendering": "Wird kompiliert…",
        "ref_render_failed": "Das Beispiel kompiliert nicht:",
        "ref_no_typst": "typst ist im PATH nicht zu finden.",
        "ref_german_page": "Deutsche Seite: dieses Beispiel liess sich nicht in der Sprache des Fensters kompilieren — {reason}",
        "ref_no_examples": "Für diesen Befehl gibt es noch kein Beispiel.",
        "ref_no_doc": "Dieser Befehl hat in lib/ noch keinen ///-Block.",
    },
    "en": {
        "tab_commands": docs.word("commands", "en"),
        "ref_internal_note": "An engine helper. commands.typ's wildcard exports it like everything else, so the name does reach every file of Sections/ — but it is not a command of the report: neither documented nor stable. Do not call it.",
        "ref_col_summary": "Summary",
        "ref_col_name": "Name",
        "ref_col_type": "Type",
        "ref_col_default": "Default",
        "ref_count": "{shown} of {total} commands · {internal} internals",
        "ref_hint": "Choose a command on the left.",
        "ref_level_fixed": "fixed at {level} by the call itself, which outranks the report's own",
        "ref_missing": "No committed page for this example — run calc/tools/build_examples.py.",
        "ref_stale": "The example has changed since its committed page — run calc/tools/build_examples.py again.",
        "ref_rendering": "Compiling…",
        "ref_render_failed": "The example does not compile:",
        "ref_no_typst": "typst is not on the PATH.",
        "ref_german_page": "German page: this example could not be compiled in English — {reason}",
        "ref_no_examples": "This command has no example yet.",
        "ref_no_doc": "This command has no /// block in lib/ yet.",
    },
}

CATEGORY_ORDER = [key for key, _names in ref.CATEGORIES] + [ref.INTERNAL]   # build_reference.CATEGORIES' order, the site's; Internes last
POLL_MS = 60   # how often the window looks whether the example compiling in its thread is done
SECTION_GAP = 8   # the room above the arguments, the calls and the examples: the site's h2, in a pane


def plain_label(text, wrap=False):
    """A label showing `text` exactly as it is -- given a text that looks like HTML, QLabel would render it as HTML."""
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(wrap)
    return label


def muted(label):
    """The site's secondary text: the theme's grey (QLabel#meta in theme.py), never a colour written here."""
    label.setObjectName("meta")
    return label


def pinned_level(code):
    """The level the rule beside an example names: the last one its calls write that prints something. A `level: 0` declares a variable and prints nothing (docs/typst/formulas.md §10quinquies), so «fixed at 0» would name the wrong line -- `#member(…, level: 0)` before `#verify-compression(…, level: 3)` is fixed at 3; with nothing but zeros the rule is not said. command_preview.FIXES_LEVEL reads no 0, the one place that says so (v0.94)."""
    printed = preview.FIXES_LEVEL.findall(code)
    return printed[-1] if printed else None


def first_line(text):
    """The first line that says something -- «error: unknown variable: foo» of a Typst message."""
    for line in (text or "").splitlines():
        if line.strip():
            return line.strip()
    return ""


CODE_SPAN, BOLD, ITALIC = docs.PROSE_CODE_SPAN, docs.BOLD, docs.ITALIC   # read by command_docs.prose (v0.89)


def prose_html(text, mono_family):
    """One paragraph of a /// block as rich text: the code between backticks in the fixed font, **bold** and *italic* as such, everything else escaped -- a `<` in a formula is not a tag.

    The code spans are taken out first and put back last, so nothing inside one is ever read as emphasis -- `#var("R_k", 7, "kN")` and `2 * 3` stay what they are -- while an emphasis may still run across one: `**`unit:` is display only**` is bold, code and all.
    """
    return _prose(text, lambda code: f'<span style="font-family: \'{mono_family}\', monospace;">{html.escape(code)}</span>',
                  lambda words: html.escape(words, quote=False), r"<b>\1</b>", r"<i>\1</i>")


def prose_plain(text):
    """The same paragraph as plain text, for the tree's one-line summary: the markers dropped, the words kept."""
    return _prose(text, lambda code: code, lambda words: words, r"\1", r"\1")


# prose_html's and prose_plain's one reading lives in command_docs (v0.89), which imports no Qt: the website's build (website/build.py) sets the same paragraphs the same way.
_prose = docs.prose


def prose_label(text, mono_family):
    """A wrapped, selectable label setting one paragraph of documentation (prose_html)."""
    label = QLabel(prose_html(text, mono_family))
    label.setTextFormat(Qt.TextFormat.RichText)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return label


def types_html(types, mono_family):
    """An argument's types as the site sets them, one small badge each on the accent's soft ground (site.css's `.params .type`), the colours the scheme's."""
    style = (f"background-color:{theme.colour('accent-soft')}; color:{theme.colour('accent-strong')}; "
             f"font-family:'{mono_family}', monospace;")
    return " ".join(f'<span style="{style}">&nbsp;{html.escape(kind)}&nbsp;</span>' for kind in types)


class PreviewLabel(QLabel):
    """The page one example compiles to.

    The image is rendered once, at a fixed resolution, and drawn at whatever width the panel gives it: rendering at the widget's width instead would put the window's size in the cache key, and every drag of the splitter would be a run of Typst. Below its natural size it is drawn through the device pixel ratio rather than resampled, so it stays as sharp as the panel allows.
    """

    def __init__(self):
        super().__init__()
        self._image = None
        self.path = None   # the file shown, which says where the page came from: examples/out or the cache
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

    def set_image(self, image, path=None):
        self._image = image if image is not None and not image.isNull() else None
        self.path = path if self._image is not None else None
        self.apply()

    def forget(self):
        self._image, self.path = None, None
        self.clear()

    def apply(self):
        if self._image is None:
            return
        natural = self._image.width() * 96 / preview.PPI  # what 16 cm is at 100 %
        width = min(natural, max(self.width(), 80))
        scale = self._image.width() / width
        pixmap = QPixmap.fromImage(self._image)
        pixmap.setDevicePixelRatio(scale)
        self.setPixmap(pixmap)
        self.setFixedHeight(round(self._image.height() / scale))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.apply()


class CodeBlock(QPlainTextEdit):
    """An example's code as the site sets it: on the code ground (QPlainTextEdit#code in theme.py), selectable, its lines kept, and exactly as tall as its lines -- with the room of the scroll bar a line wider than the pane brings, which hid the last line until v0.94."""

    def __init__(self, code, font):
        super().__init__(code)
        self.setObjectName("code")
        self.setReadOnly(True)
        self.setFont(font)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.lines = max(len(code.splitlines()), 1)
        self.fit()

    def fit(self):
        bar = self.horizontalScrollBar()
        extra = bar.sizeHint().height() if bar.maximum() > 0 else 0
        margins = self.contentsMargins()
        height = self.lines * self.fontMetrics().lineSpacing() + 2 * self.document().documentMargin() + margins.top() + margins.bottom() + 6 + extra
        if self.height() != round(height):
            self.setFixedHeight(round(height))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit()


class RenderJob:
    """One example compiled off the window's thread: in the window's language by command_preview.render_localised, or -- for a German page missing or stale among the committed ones -- in German by render_blocking, against the frozen data like the committed pages (a fallback reading the live export would disagree with every page beside it).

    The thread touches no widget: it fills `png` and `error` and sets `finished`, and the tab, which looks every POLL_MS on the window's own thread, puts the page where it belongs -- if that box is still shown and still asks for that level.
    """

    def __init__(self, box, lang, localised, note=None, fallback=None):
        self.box, self.code, self.level, self.lang = box, box.code, box.level, lang
        self.localised = localised   # the window's language, where the committed pages are German
        self.note = note             # why a German page had to be compiled: missing or stale
        self.fallback = fallback     # the committed German page to show where the compile fails, or None
        self.png = self.error = None
        self.finished = threading.Event()

    def key(self, token):
        return preview.cache_key(self.code, self.level, self.lang, token, document_language=self.localised)

    def run(self):
        try:
            render = preview.render_localised if self.localised else preview.render_blocking
            self.png, self.error = render(self.code, self.level, self.lang)
        except Exception as exc:  # broad: a thread's exception would otherwise be lost, and the box left saying «Compilation…» for ever
            self.png, self.error = None, f"{type(exc).__name__}: {exc}"
        self.finished.set()


class ExampleBox(QWidget):
    """One example of one command, as the site sets it: «Exemple n», its code, the 1 · 2 · 3 levels where command_docs.example_levels gives three, and the page it prints."""

    def __init__(self, tab, record, index, example):
        super().__init__()
        self.tab = tab
        self.command = record["name"]
        self.index = index
        self.code = example["code"]
        self.renderable = example["render"]
        # the site's decision, read where the site and build_examples.py read it: all three levels for a command taking a `level:`, one for an example that pins its own or a command that takes none, none for a ```typ-dry fence
        self.levels = docs.example_levels(record, record["english"], example)
        remembered = tab.level_of(self.command, index)
        if remembered in self.levels:
            self.level = remembered
        elif preview.DEFAULT_LEVEL in self.levels or not self.levels:
            self.level = preview.DEFAULT_LEVEL
        else:
            self.level = self.levels[0]
        self.group = None
        self.fixed_note = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 6)
        layout.setSpacing(5)

        self.heading = plain_label(tab.word("example", n=index + 1))
        self.heading.setFont(tab.app.bold_font)
        layout.addWidget(self.heading)

        source = CodeBlock(self.code, tab.app.mono_font)
        self.highlighter = richtext.TypstHighlighter(source.document())   # coloured as the site colours an example (v0.92)
        self.source = source
        row = QHBoxLayout()
        row.addWidget(source, 1)
        row.addWidget(tab.copy_button(self.code), 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(row)

        if len(self.levels) > 1:
            levels = QHBoxLayout()
            levels.setSpacing(0)
            levels.addWidget(muted(plain_label(tab.word_label("level") + " ")))
            self.group = QButtonGroup(self)
            for position, value in enumerate(self.levels):
                button = QToolButton()
                button.setText(str(value))
                button.setCheckable(True)
                # the site's level buttons, the one chosen in ink: the segmented look of the window's language switch (theme.py's QToolButton[segment])
                button.setProperty("segment", "first" if position == 0 else "last" if position == len(self.levels) - 1 else "middle")
                button.setChecked(value == self.level)
                self.group.addButton(button, value)
                levels.addWidget(button)
            self.group.idClicked.connect(self.on_level)
            levels.addStretch(1)
            layout.addLayout(levels)
        elif self.renderable and docs.takes_level(record, record["english"]):
            # the command takes a level and this example writes its own, which outranks the report's (docs/typst/report-engine.md §4): no buttons, as on the site, and the rule said -- the override is what the example demonstrates
            fixed = pinned_level(self.code)
            if fixed is not None:
                self.fixed_note = muted(plain_label(f"{tab.word_label('level')} {tab.t('ref_level_fixed', level=fixed)}", wrap=True))
                layout.addWidget(self.fixed_note)

        self.status = muted(plain_label("", wrap=True))
        self.status.hide()
        layout.addWidget(self.status)

        self.error = QPlainTextEdit()
        self.error.setReadOnly(True)
        self.error.setFont(tab.app.mono_font)
        self.error.hide()
        layout.addWidget(self.error)

        self.preview = PreviewLabel()
        layout.addWidget(self.preview)
        self.start()

    def on_level(self, level):
        if level == self.level:
            return
        self.level = level
        self.tab.remember_level(self.command, self.index, level)
        self.start()

    def start(self):
        """Shows the page: a committed file in a German window, a page from the cache or compiled on demand in a French or English one (CommandsTab.show_page)."""
        if not self.renderable:
            self.show_note(self.tab.word("not_rendered"))
            return
        self.tab.show_page(self)

    def show_note(self, text):
        self.status.setText(text)
        self.status.show()
        self.error.hide()
        self.preview.forget()

    def show_error(self, text):
        self.status.hide()
        lines = text.strip().splitlines()[-14:]
        self.error.setPlainText(self.tab.t("ref_render_failed") + "\n" + "\n".join(lines))
        self.error.setFixedHeight(18 + 16 * (len(lines) + 1))
        self.error.show()
        self.preview.forget()
        self.preview.setFixedHeight(0)

    def show_png(self, path, note=None):
        """The page. With a note where it is not the page asked for as it was asked: compiled because the committed one was missing or stale, or the German one because the window's language could not be compiled."""
        self.error.hide()
        if note:
            self.status.setText(note)
            self.status.show()
        else:
            self.status.hide()
        self.preview.set_image(QImage(str(path)), path)


class CommandsTab(QWidget):
    """Lists every command of lib/, in categories, and shows one as the website's command page shows it."""

    COLUMNS = ("command", "arguments", "summary")
    WIDTHS = {"command": 240, "arguments": 240, "summary": 420}
    SUMMARY = 2

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.t = app.t
        self.lang = getattr(app, "lang", "en")  # the documentation's and the examples' language is read once, as every tab reads its texts: a switch rebuilds the tab
        self.translations = docs.load()
        self.records = self.read_records()
        self.manifest = examples.index()  # the committed pages, read once
        self.samples = ref.sample_arguments(project.current().data_dir)
        self.nodes = {}
        self.boxes = []
        self.parts = []   # the detail pane's parts, in the order the site's page sets them: (name, widget)
        self.queue = []   # the examples waiting to be compiled, one at a time
        self.job = None   # the one compiling
        self.token = None  # command_preview.generation(), read once per page shown
        self.timer = QTimer(self)
        self.timer.setInterval(POLL_MS)
        self.timer.timeout.connect(self.poll)

        state = app.views.get("tab_commands") or {}
        self.open_rows = set(state.get("open") or [])
        self.levels = dict(state.get("levels") or {})
        self.remembered = state.get("selection")
        self.first_fill = not state

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        bar = QHBoxLayout()
        bar.addWidget(plain_label(app.label("search")))
        self.search = QLineEdit(state.get("search") or "")
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumWidth(260)
        bar.addWidget(self.search)
        bar.addStretch(1)
        self.count = muted(plain_label(""))
        bar.addWidget(self.count)
        layout.addLayout(bar)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.tree = self.build_tree()
        self.splitter.addWidget(self.tree)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.detail = QWidget()
        self.scroll.setWidget(self.detail)
        self.splitter.addWidget(self.scroll)
        self.splitter.setStretchFactor(0, 5)
        self.splitter.setStretchFactor(1, 4)
        self.splitter.setSizes(state.get("splitter") or [5200, 4800])
        layout.addWidget(self.splitter, 1)

        self.search.textChanged.connect(lambda _text: self.refill())
        self.refill()

    # -- the reference's words ---------------------------------------------------

    def word(self, key, **values):
        """One of calc/i18n/reference.json's words in the window's language -- the site's, said once (command_docs.word)."""
        return docs.word(key, self.lang, **values)

    def word_label(self, key):
        """The same word with its colon, set as each language sets one (woodcore_gui's `label`)."""
        return self.word(key) + (" :" if self.lang == "fr" else ":")

    def category(self, key):
        return docs.category_label(key, self.lang)

    # -- the records -------------------------------------------------------------

    def read_records(self):
        """Every binding of the lib files, with its doc block read -- in the window's language where it is translated -- and its category decided.

        The English is kept beside the translation (`english`), so a search finds a command by the words of either, and the site's decisions read the block they read (command_docs.example_levels).
        """
        records = []
        for binding in ref.lib_bindings(ref.ROOT):
            block = ref.parse_doc_block(binding["doc_lines"])
            record = dict(binding)
            record["english"] = block
            record["category"] = ref.category_of(binding["name"])
            if record["category"] != ref.INTERNAL and binding["doc_lines"]:
                block, record["untranslated"] = docs.localise(binding["name"], block, self.lang, self.translations)
            else:
                record["untranslated"] = 0
            record.update(block)
            records.append(record)
        return records

    def record(self, name):
        for record in self.records:
            if record["name"] == name:
                return record
        return None

    # -- the tree ----------------------------------------------------------------

    def build_tree(self):
        tree = QTreeWidget()
        tree.setColumnCount(len(self.COLUMNS))
        tree.setHeaderLabels([self.word("command"), self.word("arguments"), self.t("ref_col_summary")])
        tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        tree.setEditTriggers(QTreeWidget.EditTrigger.NoEditTriggers)
        tree.setUniformRowHeights(True)
        tree.setAlternatingRowColors(True)
        tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header = tree.header()
        header.setStretchLastSection(False)
        for index, column in enumerate(self.COLUMNS):
            tree.setColumnWidth(index, self.WIDTHS[column])
        header.setSectionResizeMode(self.SUMMARY, QHeaderView.ResizeMode.Stretch)
        tree.itemSelectionChanged.connect(self.show_selection)
        tree.customContextMenuRequested.connect(self.on_context_menu)
        for key in (QKeySequence(QKeySequence.StandardKey.Copy), QKeySequence("Return")):
            shortcut = QShortcut(key, tree)
            shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
            shortcut.activated.connect(self.copy_main)
        return tree

    def matches(self, record, needle):
        if not needle:
            return True
        fields = [record["name"], record["signature"], record["summary"], record["english"]["summary"]]
        fields += [f"{b[0]} {b[2]}" for b in record["bullets"] + record["english"]["bullets"]]
        return any(needle in field.lower() for field in fields)

    def refill(self):
        needle = self.search.text().strip().lower()
        previously = self.current_open_rows()
        self.tree.blockSignals(True)
        self.tree.clear()
        self.nodes.clear()
        shown = 0
        grey = QBrush(QColor(theme.colour("muted")))
        for key in CATEGORY_ORDER:
            group = [r for r in self.records if r["category"] == key and self.matches(r, needle)]
            if not group:
                continue
            # the category's name and, for a category of commands, the line that introduces it: reference.json's, as the site's reference sets them
            lead = docs.category_lead(key, self.lang) if key != ref.INTERNAL else self.t("ref_internal_note")
            parent = QTreeWidgetItem(self.tree, [f"{self.category(key)}  ({len(group)})", "", lead if key != ref.INTERNAL else ""])
            parent.setData(0, Qt.ItemDataRole.UserRole, f"cat|{key}")
            parent.setFont(0, self.app.bold_font)
            parent.setForeground(self.SUMMARY, grey)
            for column in range(len(self.COLUMNS)):
                parent.setToolTip(column, lead)
            self.nodes[f"cat|{key}"] = parent
            if key == ref.INTERNAL:
                order = sorted(group, key=lambda r: r["name"])
            else:
                names = dict(ref.CATEGORIES)[key]
                order = sorted(group, key=lambda r: names.index(r["name"]))
            for record in order:
                summary = prose_plain(record["summary"]) if key != ref.INTERNAL else f"{record['file']}:{record['line']}"
                node = QTreeWidgetItem(parent, [record["name"], record["params"] or "", summary])
                node.setData(0, Qt.ItemDataRole.UserRole, f"cmd|{record['name']}")
                node.setFont(0, self.app.mono_font)
                self.nodes[f"cmd|{record['name']}"] = node
                shown += key != ref.INTERNAL  # the count is of commands: a helper is not one (it read «236 sur 236 commandes» for 64)
        for iid, node in self.nodes.items():
            if not node.childCount():
                continue
            if iid == f"cat|{ref.INTERNAL}" and not needle:
                node.setExpanded(iid in previously)  # folded unless it was left open: it is the long one
            else:
                node.setExpanded(self.first_fill or bool(needle) or iid in previously)
        self.first_fill = False
        public = [r for r in self.records if r["category"] != ref.INTERNAL]
        self.count.setText(self.t("ref_count", shown=shown, total=len(public), internal=len(self.records) - len(public)))
        self.tree.blockSignals(False)
        target = self.nodes.get(self.remembered)
        if target is not None:
            self.tree.setCurrentItem(target)
        else:
            self.show_selection()

    def current_open_rows(self):
        live = {iid for iid, node in self.nodes.items() if node.childCount() and node.isExpanded()}
        hidden = {iid for iid in self.open_rows if iid not in self.nodes}
        self.open_rows = live | hidden
        return self.open_rows

    def selected_iid(self):
        items = self.tree.selectedItems()
        return items[0].data(0, Qt.ItemDataRole.UserRole) if items else None

    def selected_record(self):
        iid = self.selected_iid()
        return self.record(iid[4:]) if iid and iid.startswith("cmd|") else None

    # -- small widgets -----------------------------------------------------------

    def heading(self, text):
        label = plain_label(text)
        label.setFont(self.app.bold_font)
        return label

    def title_font(self, mono=True):
        font = QFont(self.app.mono_font if mono else self.app.bold_font)
        if self.app.title_font.pointSizeF() > 0:
            font.setPointSizeF(self.app.title_font.pointSizeF())
        font.setBold(True)
        return font

    def code_field(self, text):
        # a call written over several lines is shown on one, as it is pasted; coloured as the site sets a code block (v0.92)
        return richtext.CodeField(" ".join(part.strip() for part in text.splitlines()), self.app.mono_font)

    def signature_label(self, text):
        """The signature the page opens with, as the site's `.signature` block: the code ground, coloured, selectable, and wrapped at its commas rather than clipped -- a call field clips, and a signature is read whole."""
        label = QLabel(richtext.typst_html(" ".join(part.strip() for part in text.splitlines())))
        label.setObjectName("code")
        label.setFont(self.app.mono_font)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        return label

    def copy_button(self, text):
        return richtext.copy_button(self.t("copy"), self.t("copied_short"), lambda: self.app.copy(text))

    # -- the detail pane ---------------------------------------------------------

    def show_selection(self):
        record = self.selected_record()
        self.remembered = self.selected_iid() or self.remembered
        self.boxes = []
        self.parts = []
        self.queue = []  # the waiting renders go with the page that asked for them; the one compiling finishes into the cache
        self.token = preview.generation()
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(10, 4, 4, 8)
        layout.setSpacing(6)
        iid = self.selected_iid() or ""
        if record is not None:
            self.fill_detail(layout, record)
        elif iid.startswith("cat|"):
            self.fill_category(layout, iid[4:])
        else:
            layout.addWidget(plain_label(self.t("ref_hint"), wrap=True))
        layout.addStretch(1)
        self.scroll.setWidget(box)  # the QScrollArea takes ownership and deletes the one it replaces
        self.detail = box

    def add(self, layout, name, widget):
        """One part of the page, kept in `parts` by the name the site's page gives it -- what tests/test_commands.py reads the layout by."""
        self.parts.append((name, widget))
        layout.addWidget(widget)
        return widget

    def fill_category(self, layout, key):
        """A category row chosen: its name and the line that introduces it, as the site's reference sets them above its commands."""
        title = self.add(layout, "title", plain_label(self.category(key)))
        title.setFont(self.title_font(mono=False))
        lead = docs.category_lead(key, self.lang) if key != ref.INTERNAL else self.t("ref_internal_note")
        self.add(layout, "lead", prose_label(lead, self.app.mono_font.family()))
        self.add(layout, "hint", muted(plain_label(self.t("ref_hint"), wrap=True)))

    def fill_detail(self, layout, record):
        """One command, as the site's command page sets it (website/build.py's page_command): the category, the name, the signature, the paragraphs, the arguments, what it returns, the calls, the examples, and where it is defined."""
        mono = self.app.mono_font.family()
        self.add(layout, "eyebrow", plain_label(f"{self.word('commands')} › {self.category(record['category'])}")).setObjectName("eyebrow")
        self.add(layout, "title", plain_label(record["name"])).setFont(self.title_font())
        self.add(layout, "signature", self.signature_label(docs.signature(record, record)))

        internal = record["category"] == ref.INTERNAL
        if internal or not record["doc_lines"]:
            self.add(layout, "note", muted(plain_label(self.t("ref_internal_note" if internal else "ref_no_doc"), wrap=True)))
            self.add_defined(layout, record)
            return

        for paragraph in record["paragraphs"]:
            self.add(layout, "paragraph", prose_label(paragraph, mono))
        if record.get("untranslated"):
            note = plain_label(self.word("untranslated", n=record["untranslated"]), wrap=True)
            note.setProperty("callout", "info")   # the site's `callout note` (theme.py's QLabel[callout])
            self.add(layout, "untranslated", note)

        rows = docs.arguments(record, record)
        if rows:
            layout.addSpacing(SECTION_GAP)
            self.add(layout, "arguments", self.heading(self.word("arguments")))
            self.add(layout, "argument_table", self.argument_table(rows))

        if record["returns"]:
            self.add(layout, "returns", muted(plain_label(f"{self.word('returns')} {record['returns']}")))

        calls = self.calls_for(record)
        if calls:
            layout.addSpacing(SECTION_GAP)
        for key, call in calls:
            self.add(layout, key, muted(plain_label(self.word(key), wrap=True)))
            row = QWidget()
            line = QHBoxLayout(row)
            line.setContentsMargins(0, 0, 0, 0)
            line.addWidget(self.code_field(call), 1)
            line.addWidget(self.copy_button(call))
            self.add(layout, key + "_code", row)

        layout.addSpacing(SECTION_GAP)
        if not record["examples"]:
            self.add(layout, "no_examples", plain_label(self.t("ref_no_examples"), wrap=True))
        for index, example in enumerate(record["examples"]):
            box = ExampleBox(self, record, index, example)
            self.boxes.append(box)
            self.add(layout, "example", box)

        row = QWidget()
        line = QHBoxLayout(row)
        line.setContentsMargins(0, 8, 0, 0)
        line.addWidget(plain_label(self.t("import_label")))  # the text carries its own colon: label() added a second one («… section : :»)
        line.addWidget(self.code_field(ref.import_line()), 1)
        line.addWidget(self.copy_button(ref.import_line()))
        self.add(layout, "import", row)
        self.add_defined(layout, record)

    def add_defined(self, layout, record):
        self.add(layout, "defined", muted(plain_label(f"{self.word('defined_in')} lib/{record['file']}:{record['line']}")))

    def argument_table(self, rows):
        """The arguments as a table -- name, type, default, what it does --, the site's list of arguments set in the columns a window reads it in: a required argument has no default and shows «—»."""
        mono = self.app.mono_font.family()
        table = QWidget()
        grid = QGridLayout(table)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(6)
        grid.setColumnStretch(3, 1)
        for column, key in enumerate(("ref_col_name", "ref_col_type", "ref_col_default", "ref_col_summary")):
            header = muted(plain_label(self.t(key)))
            header.setFont(self.app.bold_font)
            grid.addWidget(header, 0, column)
        rule = QFrame()
        rule.setFrameShape(QFrame.Shape.HLine)
        rule.setFrameShadow(QFrame.Shadow.Plain)
        grid.addWidget(rule, 1, 0, 1, 4)
        top = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        bold_mono = QFont(self.app.mono_font)
        bold_mono.setBold(True)
        for row, arg in enumerate(rows, start=2):
            name = plain_label(arg["name"])
            name.setFont(bold_mono)
            name.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            grid.addWidget(name, row, 0, top)
            kinds = QLabel(types_html(arg["types"], mono))
            kinds.setTextFormat(Qt.TextFormat.RichText)
            grid.addWidget(kinds, row, 1, top)
            default = muted(plain_label(arg["default"] if arg["default"] is not None else "—"))
            default.setFont(self.app.mono_font)
            default.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            grid.addWidget(default, row, 2, top)
            grid.addWidget(prose_label(arg["text"], mono), row, 3)
        return table

    # -- copying -----------------------------------------------------------------

    def calls_for(self, record):
        """The calls one command offers to copy, in the site's order -- the minimal one, then the complete one where it says more (command_docs.calls)."""
        if record is None or record["category"] == ref.INTERNAL:
            return []
        return docs.calls(record, self.samples)

    def copy_main(self):
        calls = self.calls_for(self.selected_record())
        if calls:
            self.app.copy(calls[0][1])

    def on_context_menu(self, position):
        node = self.tree.itemAt(position)
        if node is None:
            return
        self.tree.setCurrentItem(node)
        calls = self.calls_for(self.selected_record())
        if not calls:
            return
        menu = QMenu(self)
        for key, call in calls:
            # a single & would be read as a keyboard accelerator; the call goes in the right-hand column
            action = menu.addAction(self.word(key).replace("&", "&&") + "\t" + call.replace("\n", " "))
            action.triggered.connect(lambda _checked=False, c=call: self.app.copy(c))
        menu.exec(self.tree.viewport().mapToGlobal(position))

    # -- the pages ---------------------------------------------------------------

    def level_of(self, command, index):
        return self.levels.get(f"{command}|{index}", preview.DEFAULT_LEVEL)

    def remember_level(self, command, index, level):
        self.levels[f"{command}|{index}"] = level

    def page_for(self, box):
        """The committed German page for one example, and whether it can be trusted (build_examples.page)."""
        return examples.page(box.command, box.index, box.level, box.code, self.manifest)

    def show_page(self, box):
        """Puts one example's page in its box -- at once where there is a file to show, else through a compile in a thread of its own.

        A German window shows the committed page, and compiles only where it is missing or was rendered from an older version of the fence -- saying which, rather than having it quietly recompiled under the reader (docs/typst/command-docs.md §10sexies). A French or English window shows the page in its own language, from the cache or compiled on demand by command_preview.render_localised; the committed German page is what it falls back to.
        """
        german, state = self.page_for(box)
        if self.lang == examples.LANG:
            if state == "fresh":
                box.show_png(german)
                return
            job = RenderJob(box, self.lang, localised=False, note=self.t("ref_stale" if state == "stale" else "ref_missing"), fallback=german)
        else:
            job = RenderJob(box, self.lang, localised=True, fallback=german)
        hit = preview.cached_png(job.key(self.token or preview.generation()))
        if hit is not None:
            box.show_png(hit, note=job.note)
            return
        if not preview.have_typst():
            self.settle(job)   # nothing to compile with: the German page, or the error, said at once
            return
        box.show_note(" ".join(part for part in (job.note, self.t("ref_rendering")) if part))
        self.queue = [waiting for waiting in self.queue if waiting.box is not box]  # a box asking again replaces its own waiting request
        self.queue.append(job)
        self.pump()

    def pump(self):
        """Starts the next compile. One at a time: a reader going through a command's examples must not start five Typsts at once, and the pages come in the order they stand on the page."""
        if self.job is not None or not self.queue:
            return
        self.job = self.queue.pop(0)
        threading.Thread(target=self.job.run, name="example-render", daemon=True).start()
        self.timer.start()

    def poll(self):
        job = self.job
        if job is None:
            self.timer.stop()
            return
        if not job.finished.is_set():
            return
        self.job = None
        self.settle(job)
        if not self.queue:
            self.timer.stop()
        self.pump()

    def settle(self, job):
        """Puts a compiled page where it belongs -- or, where there is none, the German page with one line saying why, or the error."""
        box = job.box
        if not isValid(box) or box.level != job.level:
            return   # its page went with the pane, or it asks for another level since: the page is in the cache for the next look
        if job.png is not None:
            box.show_png(job.png, note=job.note)
            return
        reason = first_line(job.error) or self.t("ref_no_typst")
        if job.fallback is not None and job.localised:
            box.show_png(job.fallback, note=self.t("ref_german_page", reason=reason))
        elif job.fallback is not None:
            box.show_png(job.fallback, note=f"{job.note} {reason}")   # the stale committed page, said stale
        else:
            box.show_error(job.error or self.t("ref_no_typst"))

    # -- state -------------------------------------------------------------------

    def view_state(self):
        return {
            "search": self.search.text(),
            "open": sorted(self.current_open_rows()),
            "selection": self.selected_iid() or self.remembered,
            "levels": {k: v for k, v in self.levels.items() if v != preview.DEFAULT_LEVEL},
            "splitter": self.splitter.sizes(),
        }
