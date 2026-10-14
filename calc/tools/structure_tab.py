"""Woodcore's «Structure du document» tab -- **the one tab a document is written in**, in the convention d'utilisation, the base de projet and the report alike (the engineer's rework of 01.10.2026, work package R2-D1). It replaces both the structure tab of phase 2 and the «Sections» tab of phase 3, and **no Typst code is ever shown in it**: the engineer who wants to read or write code opens the file in VS Code, and this tab follows what he writes there.

* At the **left** the document's tree (calc/tools/structure_tree.py): **chapters › sections (files) › objects** -- the headings, paragraphs, tables, lists to tick, choices and signatures of each file --, with an icon for each kind, a box on every chapter and section to print it or not, extended selection (Ctrl and Shift) and **drag and drop**: a section or a chapter anywhere in the tree, an object within its file or into another, above or below another object. Above it the buttons that edit the structure -- add a section, a chapter or an object, remove, rename, import from another document, tag a file -- and, where the document shares anything with another, the three of the **synchronisation**.
* In the **middle** the preview of **the node chosen and nothing else** (calc/structure_preview.py): a chapter shows only its printed sections, a section only itself, an object only that object, and nothing chosen shows the whole document -- as a small Typst source compiled from standard input into the pane's page (calc/tools/pdf_pane.py, `request_snippet`), in about half a second, and not a live preview of the document.
* At the **right** the options of what is chosen (calc/tools/object_panes.py): the pane of a table, of a paragraph, of a chapter … by its kind. Several rows chosen show a sentence in its place. A section's pane carries its title, its file, whether it is printed and **its sharing**: the documents it is shared with, «Partager avec…» -- a small dialog of the project's other documents, then calc/sharing.py's `share` -- and «Arrêter le partage» (`stop_sharing`, asked first): the file then shows a **greyed link mark** in the tree for as long as the tab is open (`stopped`; the tags are gone from the file, so the files keep no memory of it). The `.typ` mark of a row is the report's alone -- in the other two documents every section is a file, and the mark and its legend are left out.

**The document is saved as a content template** («template de fond», the engineer's word of 06.10.2026, against the *layout* template, «template de forme», which the project's properties switch) with «Enregistrer comme template de fond…» -- in the three documents, the report included since 06.10.2026: a small dialog asks the name, the description and the place -- the engineer's own templates or the office's shared folder --, and calc/doc_templates.py's `save_from_document` writes it, a refusal said in the window's words (settings_dialog.doc_error_text), an existing template asked about before it is written over (`overwrite`, the old version going to archives/) and what is worth knowing about the template (`notes`: a file it names and does not carry, a file whose tags Woodcore cannot read) said in a box. It writes nothing into the project, so it is open to a project held read-only.

**The document switches its content template** with «Changer de template de fond…» (calc/tools/content_switch_dialog.py over calc/content_switch.py): the document and the template compared section by section in a tree, each section kept, taken or dropped, what is replaced or dropped archived -- never deleted. Rare, since a content template is chosen when the project is made, and possible in each of the three documents of a project laid out in three; refused, with its reason, to a project written as one report and to one held read-only.

**Every write goes through the modules that own it**: a section's state, title and place through calc/structure.py (`set_enabled`, `set_title`, `add_section`, `add_group`, `remove_section`, `rename_section`, `move_node`, `tag_section`), an object's body through calc/typst_objects.py (`write_object`, `insert_object`, `remove_object`: **only the bytes between the object's two tags change**), an object's place and what is imported through calc/doc_import.py (`move_object`, `import_items`), and what is shared with the other documents through calc/sync.py. The tab asks, says a refusal in the window's own words -- one `st_why_<code>` for each code of the five modules -- in a banner over the tree and never in a modal, and reads the tree again from what was written. An object **written by hand** in a form Woodcore does not write asks first, naming what will change, and then rewrites it; a file changed under a pane since the pane loaded refuses the write (`changed`) and reads it again.

**What is shared stays in step as the engineer decides** (calc/sync.py): a file or object shared with another document that the other copy changed is **orange**, one both changed **red**, one he chose to ignore grey; «Importer les modifications» takes the other version between the tags only -- asking which to keep where both changed -- «Ignorer» and «Réactiver» set the flag that is remembered, per document, until it is taken off. The tab's own right-pane edit of an object that stands in a shared block writes **this document's copy alone** and tells calc/sync.py (`record_local_edit`): the others then show it as incoming. `apply_sync_status(status)` is the one place the colours and the buttons follow a `sync.Status`.

**The files are the source of truth, and the engineer edits them elsewhere**: the tab watches the document's `Sections/` folder, its entry file and its structure.json (`QFileSystemWatcher`, **while it is shown**: a watch holds a directory on Windows) and reads the tree again, debounced, when what is on disk is not what it last read -- the pane of the object chosen included. The files it writes itself are not read again: what it read last is what it wrote.

**Nothing is computed or compiled before the tab is shown.** The window builds every tab when it opens, and a preview is a compile: the pane is given its document the first time the tab is shown (`showEvent`), and compiles of itself only where there is nothing to show yet. The tab reads the document the window shows (`current_document`) and is told when it changes (`on_mode`); it is one of MODE_BOUND, so an edit pending in a pane is written before another document is shown (`confirm_leave`). It has no `dirty`: it writes at once.
"""

import functools
import time
from pathlib import Path

import shiboken6
from PySide6.QtCore import QFileSystemWatcher, QTimer, Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QInputDialog, QLabel, QMenu, QMessageBox, QPushButton, QSplitter, QVBoxLayout, QWidget

import cards  # the card the pane host sits in (cards.py)
import autosave  # saving without a question, and what is never saved without the engineer (autosave.py, v0.117)
import doc_import  # what is imported from another document, and an object's move (calc/doc_import.py)
import sharing  # a section shared with another document, and no longer (calc/sharing.py)
import doc_templates  # the document saved as a template (calc/doc_templates.py)
import documents  # what each of the three documents is called (calc/documents.py)
import flowbar  # the rows of buttons that wrap rather than set the tab's width (flowbar.py)
import import_dialog  # the questions the tab asks (import_dialog.py)
import object_panes  # the right pane (calc/tools/object_panes.py)
import pdf_pane  # the page, and its compile in the background (calc/tools/pdf_pane.py)
import project
import removed_objects  # the objects taken out of the document, kept where they stood (calc/removed_objects.py)
import settings_dialog  # the words of a template's refusal and of its place (settings_dialog.py)
import structure  # the tree, and everything that writes the structure (calc/structure.py)
import structure_preview  # the Typst source of what is chosen (calc/structure_preview.py)
import structure_tree  # the tree widget (structure_tree.py)
import structure_words  # the words (structure_words.py)
import sync  # what the documents share, and where each stands (calc/sync.py)
import typst_objects  # the objects of a file, and the writing of one (calc/typst_objects.py)
import typst_paths
import validation
import notifications  # every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # what was a message box is a notice since v0.117 (notices_ui.tell)
from structure_tab_view import STRINGS, StructureTabViewMixin  # split out of this module (issue #30): every name it had is still importable from it
from structure_tab_write import WHY, _Safe, _lines, shared_block_text, StructureTabWriteMixin  # split out of this module (issue #30): every name it had is still importable from it
from structure_tab_share import SYNC_RANK, StructureTabShareMixin  # split out of this module (issue #30): every name it had is still importable from it

# The objects a menu offers to add, in the order a document is written in.
OBJECT_KINDS = tuple(kind for kind in typst_objects.DOCUMENT_TYPES if "st_kind_" + kind in STRINGS["en"])
# The words of the buttons whose key is not "st_" + the button's own: the window merges every tab's words into one table, the later tab winning a key, and the static models' tab (statics_tab.py) writes `st_remove`, `st_rename` and `st_moved` of its own -- «Id…» read «Renommer « {old} » en « {new} » ?» in the window. tests/test_structure_tab.py holds this module's keys apart from every other tab's.
BUTTON_WORDS = {"remove": "st_remove_button", "rename": "st_rename_button"}
# The levels the buttons above the tree open it to; None is «all».
LEVELS = (1, 2, 3, None)
# How long a change on disk waits for the next before the tree is read again: an editor saves in a burst.
WATCH_DEBOUNCE_MS = 500
# How long after a write the state of what is shared is worked out again.
SYNC_DEBOUNCE_MS = 120
# The share of its width each pane takes when the tab is first shown: the tree, the page, the options. The page has the most: the preview is what the engineer reads, and its text is as large as the pane is wide.
SHARES = (0.27, 0.43, 0.30)


def plain_label(text="", wrap=False):
    """A label that is never read as HTML -- a title is the engineer's text and may hold anything."""
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(wrap)
    return label


def document_mode(app):
    """The document whose structure the tab shows: the window's (`current_document`, the one its navigation shows), the report where the window names none -- a window built without a project in three documents, a test's."""
    current = getattr(app, "current_document", None)
    if callable(current):
        return current()
    mode = getattr(app, "mode", "rs")
    return mode if mode in project.current().modes else "rs"


class StructureTab(StructureTabShareMixin, StructureTabWriteMixin, StructureTabViewMixin, QWidget):
    """A document's tree, the page of what is chosen in it, and the options of what is chosen -- and the one place that writes a document's structure and the objects of its sections."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.t = app.t
        self.nodes = []             # what structure.tree gave, as last read
        self.error = None           # why the structure could not be read, where it could not
        self.failure = None         # why the last write was refused or failed, said in the banner until the next is tried
        self.subject = None         # what the right pane shows and what its edits are written to: {"id", "kind", ...}
        self.pane_loaded = False    # whether the page has been given its document -- the first time the tab is shown
        self.resume = False         # a compile that was asked for and lost to a rebuild of the window: asked again when the page is given its document
        self.sized = False          # whether the panes have the widths they will keep
        self.sync_status = None     # the last sync.Status of the document, None before any
        self.signature = None       # what the files said when the tree was last read: a change on disk is a signature that differs
        self.forced = set()         # the objects the engineer said yes to rewriting, for as long as they are the object chosen
        self.loading = False        # set while a pane is filled, so that filling is not taken for an edit
        self.watcher = None         # the QFileSystemWatcher, made when the tab is shown
        self._in_tree_signal = False
        self.drops = []             # what a test of the drag and drop keeps: (ids, target, where)
        self.stopped = {}           # for each document, the ids of the files whose sharing was stopped while the tab was open: they show a greyed link mark
        self.form_seen = None       # the layout template's files as last seen (form_signature): a switch in the properties is a signature that differs

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.build_tree_panel())
        self.splitter.addWidget(self.build_pane_panel())
        self.splitter.addWidget(self.build_options_panel())
        for index, stretch in enumerate((3, 4, 3)):
            self.splitter.setStretchFactor(index, stretch)
        layout.addWidget(self.splitter, 1)

        self.external_timer = QTimer(self)
        self.external_timer.setSingleShot(True)
        self.external_timer.setInterval(WATCH_DEBOUNCE_MS)
        self.external_timer.timeout.connect(self.reload_external)
        self.sync_timer = QTimer(self)
        self.sync_timer.setSingleShot(True)
        self.sync_timer.setInterval(SYNC_DEBOUNCE_MS)
        self.sync_timer.timeout.connect(self.refresh_sync)
        self.restore(app.views.get("tab_structure"))

    # -- building ---------------------------------------------------------------------

    def bar(self, buttons):
        """A row of buttons that wraps onto another line rather than set the tab's width: (key, slot) pairs, the button of each kept in `self.buttons`."""
        holder = flowbar.FlowWidget()
        row = flowbar.FlowLayout(holder, spacing=4)
        for key, slot in buttons:
            button = QPushButton(self.t(BUTTON_WORDS.get(key, "st_" + key)))
            button.setToolTip(self.t("st_" + key + "_tip"))
            button.clicked.connect(functools.partial(self.run_action, slot))
            row.addWidget(button)
            self.buttons[key] = button
        return holder

    def run_action(self, slot, _checked=False):
        slot()

    def build_tree_panel(self):
        panel = QWidget()   # no minimum of its own since issue #10: the floor is every tab's (cards.PANE_FLOOR, chrome.FoldablePane)
        box = QVBoxLayout(panel)
        box.setContentsMargins(0, 0, 6, 0)
        self.title = plain_label(self.t("st_heading", document=self.document_name()))
        self.title.setFont(self.app.bold_font)   # the document whose structure this is, which changes with the navigation's drop-down (on_mode)
        box.addWidget(self.title)
        row = QHBoxLayout()
        row.setSpacing(4)
        caption = plain_label(self.t("st_levels"))
        caption.setToolTip(self.t("st_levels_tip"))
        row.addWidget(caption)
        self.level_buttons = {}
        for level in LEVELS:
            button = QPushButton(self.t("st_level_all") if level is None else str(level))
            if level is not None:
                button.setProperty("compact", True)
                button.setMinimumWidth(28)      # «1 2 3» a hair wide each, not the three slivers a compact button is
            button.setToolTip(self.t("st_levels_tip"))
            button.clicked.connect(functools.partial(self.expand_to, level))
            row.addWidget(button)
            self.level_buttons[level] = button
        row.addStretch(1)
        box.addLayout(row)
        self.buttons = {}
        box.addWidget(self.bar([
            ("add_section", self.on_add_section), ("add_group", self.on_add_group), ("add_object", self.on_add_object),
            ("remove", self.on_remove), ("rename", self.on_rename), ("import", self.on_import), ("tag", self.on_tag),
            ("save_template", self.on_save_template), ("switch_template", self.on_switch_template),
        ]))
        # The «+ Objet» button opens the menu of the kinds an object can be.
        self.object_menu = QMenu(self)
        for kind in OBJECT_KINDS:
            action = self.object_menu.addAction(self.t("st_kind_" + kind))
            action.triggered.connect(functools.partial(self.on_add_kind, kind))
        self.buttons["add_object"].setMenu(self.object_menu)
        # Where the synchronisation's buttons go: a row of its own, shown where the document shares anything with another.
        self.sync_box = QWidget()
        sync_layout = QVBoxLayout(self.sync_box)
        sync_layout.setContentsMargins(0, 0, 0, 0)
        sync_layout.setSpacing(2)
        self.sync_bar = self.bar([("sync_import", self.on_sync_import), ("sync_ignore", self.on_sync_ignore), ("sync_reactivate", self.on_sync_reactivate)])
        sync_layout.addWidget(self.sync_bar)
        self.sync_label = plain_label("", wrap=True)
        self.sync_label.setObjectName("meta")
        sync_layout.addWidget(self.sync_label)
        self.sync_box.setVisible(False)
        box.addWidget(self.sync_box)
        self.banner = plain_label("", wrap=True)
        self.banner.setProperty("callout", "danger")
        self.banner.setVisible(False)
        box.addWidget(self.banner)
        # A convention or a base laid out before v0.113, its headings at offsets and its chapters in its entry: said once, with the button that converts it -- nothing rewritten without the engineer's yes (structure.make_absolute, 06.10.2026)
        self.levels_box = QWidget()
        levels_layout = QVBoxLayout(self.levels_box)
        levels_layout.setContentsMargins(0, 0, 0, 0)
        levels_layout.setSpacing(4)
        levels_note = plain_label(self.t("st_levels_relative"), wrap=True)
        levels_note.setProperty("callout", "info")
        levels_layout.addWidget(levels_note)
        self.levels_button = QPushButton(self.t("st_levels_convert"))
        self.levels_button.setToolTip(self.t("st_levels_convert_tip"))
        self.levels_button.clicked.connect(lambda _checked=False: self.on_make_absolute())
        levels_layout.addWidget(self.levels_button, 0, Qt.AlignmentFlag.AlignLeft)
        self.levels_box.setVisible(False)
        box.addWidget(self.levels_box)
        self.tree = structure_tree.StructureTree()
        self.tree.toggled.connect(self.on_toggled)
        self.tree.selectionIdsChanged.connect(self.on_selection_changed)
        self.tree.dropped.connect(self.on_dropped)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.on_context_menu)
        box.addWidget(self.tree, 1)
        self.legend = plain_label(self.t(self.legend_key()), wrap=True)
        self.legend.setObjectName("meta")
        box.addWidget(self.legend)
        return panel

    def legend_key(self):
        """The words under the tree: the report's legend names the `.typ` mark, which only the report shows."""
        return "st_legend" if self.mode() == "rs" else "st_legend_documents"

    def build_pane_panel(self):
        panel = QWidget()
        panel.setMinimumWidth(200)
        box = QVBoxLayout(panel)
        box.setContentsMargins(6, 0, 6, 0)
        row = QHBoxLayout()
        self.preview_label = plain_label(self.t("st_preview", what=self.t("st_preview_document")))
        self.preview_label.setFont(self.app.bold_font)
        row.addWidget(self.preview_label, 1)
        self.compile_button = QPushButton(self.t("st_compile"))
        self.compile_button.setToolTip(self.t("st_compile_tip", document=self.document_name()))
        self.compile_button.clicked.connect(self.compile_now)
        if self.read_only():    # a compile of the whole document writes its record into the project's generated folder: not in a project another window holds
            self.compile_button.setEnabled(False)
            self.compile_button.setToolTip(self.t("st_read_only"))
        row.addWidget(self.compile_button)
        box.addLayout(row)
        self.pane = pdf_pane.PdfPane(self, lang=self.app.lang)
        self.pane.failed.connect(self.on_failed)
        self.pane.staleChanged.connect(self.on_stale_changed)
        box.addWidget(self.pane, 1)
        return panel

    def build_options_panel(self):
        panel = QWidget()
        panel.setMinimumWidth(240)
        box = QVBoxLayout(panel)
        box.setContentsMargins(6, 0, 0, 0)
        self.context = object_panes.PaneContext.from_project(project.current(), self.app.lang)
        self.host = object_panes.ObjectPaneHost(self.context)
        self.host.changed.connect(self.on_pane_changed)
        self.host.tagRequested.connect(self.on_tag)
        self.host.shareRequested.connect(self.on_share)
        self.host.stopShareRequested.connect(self.on_stop_share)
        if self.read_only():    # the forms stay readable, and writing nothing is what the window's guard is for
            self.host.setEnabled(False)
        box.addWidget(self.host, 1)
        return panel

    # -- the document ----------------------------------------------------------------------

    def mode(self):
        return document_mode(self.app)

    def read_only(self):
        """Whether the window holds the project read-only -- another window has it (project_lock.py)."""
        return bool(getattr(self.app, "read_only", False))

    def document_name(self):
        return documents.mode_name(self.mode(), getattr(self.app, "lang", documents.DEFAULT_LANGUAGE))

    def doc_dir(self):
        return Path(project.current().document_dir(self.mode()))

    def say(self, text):
        status = getattr(self.app, "set_status", None)
        if status is not None:
            status(text)

    def on_mode(self, _mode=None):
        """Another document shown in the window: its structure read and its page shown, its name in the heading. What a pane held unsaved was written before (the window's `on_mode_changed` asks `confirm_leave`, this tab being one of MODE_BOUND)."""
        self.failure = None
        self.forced = set()
        self.title.setText(self.t("st_heading", document=self.document_name()))
        self.legend.setText(self.t(self.legend_key()))
        if not self.read_only():
            self.compile_button.setToolTip(self.t("st_compile_tip", document=self.document_name()))
        self.sync_status = None
        self.stop_watching()
        self.reload(reset=True)
        if self.pane_loaded:
            self.load_pane(auto=self.isVisible())
        if self.isVisible():
            self.start_watching()

    def on_shown(self):
        """Brought to the front: what the files say read again where it is not what was read last -- a section may have been written, or a file edited, elsewhere since -- the state of what is shared worked out again, and the document's own PDF shown where the page had nothing and an export has written one since."""
        self.context.reset()
        if not self.reload_external(quiet=True):
            self.refresh_sync()
        if self.pane_loaded and not self.pane.showing:
            own = project.current().document_pdf(self.mode())
            if own.is_file():
                self.pane.load(own)
        if self.pane_loaded:
            self.pane.check_stale()

    def showEvent(self, event):
        super().showEvent(event)
        if not self.sized:
            QTimer.singleShot(0, self.share_out)
        if not self.pane_loaded:
            self.load_pane(auto=True)
        self.start_watching()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.stop_watching()

    def share_out(self):
        """The widths of the three panes when the tab is first shown and the engineer has none of his own: a share of the width it has."""
        if self.sized or not shiboken6.isValid(self):
            return
        total = self.splitter.width()
        if self.isVisible() and total > 600:
            self.splitter.setSizes([round(total * share) for share in SHARES])
            self.sized = True

    def on_properties_changed(self, style_changed):
        """The project's properties were edited (*Fichier → Propriétés du projet*): where they replaced the config.typ the three documents share, or switched the layout template («template de forme»: `Template/` and `title.typ`, calc/forms.py, which may leave a config.typ of the new format as it is), what the page shows is compiled again with it, the window asking and not the tab, which does not watch a file it did not write."""
        form = self.form_signature()
        changed = style_changed or (self.form_seen is not None and form != self.form_seen)
        self.form_seen = form
        if changed and self.pane_loaded:
            self.request_preview(force=True)

    def form_signature(self):
        """What says the project's layout template was switched: the size and the time written of its `Template/form.json`, `Template/template.typ` and `title.typ` -- None for each that is not there."""
        try:
            here = project.current()
            root = Path(here.typst_root)
            paths = (root / "Template" / "form.json", root / "Template" / "template.typ", Path(here.title_typ))
        except (project.ProjectError, AttributeError):
            return None
        out = []
        for path in paths:
            try:
                found = path.stat()
                out.append((found.st_size, found.st_mtime_ns))
            except OSError:
                out.append(None)
        return tuple(out)

    def set_language(self, lang):
        """The panes' words in `lang`. The tab's own are the window's (`app.t`), which a language switch builds again."""
        self.pane.set_language(lang)
        self.host.set_language(lang)

    # -- the files ----------------------------------------------------------------------------


    # -- the tree ------------------------------------------------------------------------------


    # -- the selection ---------------------------------------------------------------------


    # -- the right pane ---------------------------------------------------------------------


    # -- the page -----------------------------------------------------------------------------


    # -- why a write was refused ------------------------------------------------------------------


    CAUGHT = (validation.ValidationError, project.ProjectError, OSError, typst_objects.ObjectError, ValueError)

    # -- writing: a section's state, title and place --------------------------------------------------


    # -- writing: the objects of a section ----------------------------------------------------------------


    # -- writing: tagging, importing, moving -----------------------------------------------------------------


    # -- sharing the section chosen -----------------------------------------------------------------------------------


    # -- switching the document's content template ------------------------------------------------------------


    # -- saving the document as a template ---------------------------------------------------------------------


    # -- what is shared ----------------------------------------------------------------------------------------


    # -- the buttons -------------------------------------------------------------------------------------------

    def writable(self):
        """Whether the project may be written; the window says it may not, once, where it may not."""
        if self.read_only():
            self.app.refuse_read_only()
            return False
        return True

    def set_button(self, key, enabled, reason=None):
        """A button enabled, or disabled with its reason as its tooltip -- a disabled control with nothing to say is one the engineer cannot account for."""
        button = self.buttons[key]
        button.setEnabled(bool(enabled))
        button.setToolTip(self.t("st_" + key + "_tip") if enabled or not reason else reason)

    def update_buttons(self):
        """The buttons enabled where they can act on what is chosen, each saying why where it cannot."""
        chosen = self.selection()
        node = chosen[0] if len(chosen) == 1 else None
        read_only = self.read_only()
        none = self.t("st_off_none")
        self.set_button("add_section", not read_only, self.t("st_read_only"))
        self.set_button("add_group", not read_only and self.mode() != "rs", self.t("st_read_only") if read_only else self.t("st_why_rs_no_groups"))
        holds = node is not None and node.kind != "group"
        self.set_button("add_object", not read_only and holds, self.t("st_read_only") if read_only else none)
        removable = bool(chosen) and all(item.kind in ("file", "group", "object") for item in chosen)
        self.set_button("remove", not read_only and removable, self.t("st_read_only") if read_only else none)
        self.set_button("rename", not read_only and node is not None and node.kind in ("file", "group"), self.t("st_read_only") if read_only else none)
        others = bool(doc_import.other_documents(project.current(), self.mode())) if self.mode() in project.current().modes else False
        self.set_button("import", not read_only and others, self.t("st_read_only") if read_only else self.t("st_import_empty"))
        tag_ok = False
        if node is not None and node.kind in ("file", "object", "heading"):
            tag_ok = self.has_untagged(self.read_text(node))
        self.set_button("tag", not read_only and tag_ok, self.t("st_read_only") if read_only else (none if node is None else self.t("st_off_tag")))
        self.set_button("save_template", True)     # it writes nothing into the project: open to a project held read-only
        self.set_button("switch_template", not read_only and self.switchable(), self.t("st_read_only") if read_only else self.t("st_off_switch_single"))
        status = self.sync_status
        shared = status is not None and bool(status.blocks)
        self.sync_box.setVisible(shared)
        if shared:
            counts = {"incoming": len(status.incoming), "conflicts": len(status.conflicts), "ignored": len(status.ignored)}
            self.sync_label.setText(self.t("st_sync_counts", **counts) if any(counts.values()) else self.t("st_sync_nothing"))
            keys = self.sync_keys(chosen) if chosen else None
            pool = keys if keys is not None else list(status.incoming) + list(status.conflicts)
            incoming = [key for key in pool if status.state_of(key) in ("incoming", "conflict")]
            ignored = [key for key in (keys or []) if status.state_of(key) == "ignored"]
            self.set_button("sync_import", not read_only and bool(incoming), self.t("st_read_only") if read_only else self.t("st_sync_off_incoming"))
            self.set_button("sync_ignore", not read_only and bool(keys), self.t("st_read_only") if read_only else self.t("st_sync_off_selection"))
            self.set_button("sync_reactivate", not read_only and bool(ignored), self.t("st_read_only") if read_only else self.t("st_sync_off_ignored"))

    def on_context_menu(self, pos):
        """The actions of the buttons on the right button of a row -- the row under the pointer chosen first, as a click would; the action run once the menu has closed, the tree being filled again by it."""
        row = self.tree.itemAt(pos)
        if row is not None and not row.isSelected():
            self.tree.select(row.data(0, structure_tree.ID_ROLE))
            self.on_selection_changed()
        menu = QMenu(self)
        chosen = {}
        removed = [node.id for node in self.selection() if node.kind == "removed"]
        if removed:
            # an object taken out of the document: put it back, or take it off the list
            chosen[menu.addAction(self.t("st_restore"))] = lambda: [self.write_restore(row_id) for row_id in removed]
            chosen[menu.addAction(self.t("st_forget_removed"))] = lambda: [self.write_forget_removed(row_id) for row_id in removed]
            picked = menu.exec(self.tree.viewport().mapToGlobal(pos))
            if picked is not None and picked in chosen:
                QTimer.singleShot(0, functools.partial(self.deferred, chosen[picked]))
            return
        for key, slot in (("add_section", self.on_add_section), ("add_group", self.on_add_group), ("rename", self.on_rename), ("remove", self.on_remove),
                          ("import", self.on_import), ("tag", self.on_tag), ("sync_import", self.on_sync_import),
                          ("sync_ignore", self.on_sync_ignore), ("sync_reactivate", self.on_sync_reactivate)):
            if key.startswith("sync") and not self.sync_box.isVisibleTo(self):
                continue
            action = menu.addAction(self.buttons[key].text())
            action.setEnabled(self.buttons[key].isEnabled())
            action.setToolTip(self.buttons[key].toolTip())
            chosen[action] = slot
        add = menu.addMenu(self.buttons["add_object"].text())
        add.setEnabled(self.buttons["add_object"].isEnabled())
        for kind in OBJECT_KINDS:
            chosen[add.addAction(self.t("st_kind_" + kind))] = functools.partial(self.on_add_kind, kind)
        menu.setToolTipsVisible(True)
        picked = menu.exec(self.tree.viewport().mapToGlobal(pos))
        if picked is not None and picked in chosen:
            QTimer.singleShot(0, functools.partial(self.deferred, chosen[picked]))

    # -- the questions -----------------------------------------------------------------------------------------------
    # Each one a method of its own, so that a test answers it without a dialog: a modal off-screen never comes back.

    def ask_section(self, where):
        """(id, title) of a new section, or None."""
        mode = self.mode()
        dialog = import_dialog.SectionDialog(self, self.t, where, lambda title: structure.suggest_id(project.current(), mode, title), rs=mode == "rs")
        return dialog.values() if dialog.exec() == QDialog.DialogCode.Accepted else None

    def ask_group(self, where):
        """(id, {fr, de, en}) of a new chapter, or None."""
        mode = self.mode()
        dialog = import_dialog.GroupDialog(self, self.t, where, lambda title: structure.suggest_id(project.current(), mode, title))
        return dialog.values() if dialog.exec() == QDialog.DialogCode.Accepted else None

    def ask_rename(self, node_id, title):
        """The new id of a section, or None."""
        new, ok = QInputDialog.getText(self, self.t("tab_structure"), self.t("st_rename_ask", title=title, id=node_id), text=node_id)
        return new.strip() if ok and new.strip() else None

    def ask_import(self):
        """(source document, items, linked) the engineer chose to import, or None."""
        lang = getattr(self.app, "lang", documents.DEFAULT_LANGUAGE)
        dialog = import_dialog.ImportDialog(self, self.t, project.current(), self.mode(), lang)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        source, items, linked = dialog.values()
        return (source, items, linked) if source and items else None

    def ask_share(self, node):
        """The modes of the other documents the engineer chose to share section `node` with, or None."""
        lang = getattr(self.app, "lang", documents.DEFAULT_LANGUAGE)
        try:
            others = doc_import.other_documents(project.current(), self.mode())
        except (validation.ValidationError, project.ProjectError):
            others = ()
        listed = [(mode, documents.mode_name(mode, lang), mode in node.shared_with) for mode in others]
        dialog = import_dialog.ShareDialog(self, self.t, structure_tree.display_title(node), listed)
        return dialog.values() if dialog.exec() == QDialog.DialogCode.Accepted else None

    def ask_template(self):
        """(name, description, place) of the template to save the document as, or None."""
        dialog = import_dialog.TemplateDialog(self, self.t, self.document_name(), self.template_language(), self.template_places())
        return dialog.values() if dialog.exec() == QDialog.DialogCode.Accepted else None

    def ask_confirm(self, text):
        return QMessageBox.question(self, self.t("tab_structure"), text) == QMessageBox.StandardButton.Yes

    def tell(self, title, text):
        """Something worth knowing, said in the status line (an information notice, v0.117) rather than in a box the engineer closes."""
        notices_ui.tell(text, notifications.INFO, source="structure_tab")

    def flush_pending(self):
        """What a pane holds pending written now -- the tab left, the window left for VS Code (autosave.py, v0.117): the files are the source of truth, and VS Code must find the edit in them."""
        self.host.flush()

    def confirm_leave(self):
        """True: what a pane holds pending is written before another document is shown -- this tab being one of MODE_BOUND -- and nothing in it can be kept unsaved, every change being written as it is made."""
        self._in_tree_signal = False
        self.host.flush()
        return True

    # -- surviving a rebuild --------------------------------------------------------------------------------------------

    def view_state(self):
        """What the window carries through a rebuild -- which is the only time it asks: it replaces this tab, so what a pane held is written, the page's compile is stopped (a new page would compile over the same file) and asked for again by the new tab where one was running, and the watch is let go of."""
        self.host.flush()
        pending = self.pane.is_pending()
        self.pane.stop()
        self.stop_watching()
        return {"splitter": self.splitter.sizes() if self.sized else None, "tree": self.tree.state(), "pending": pending,
                "stopped": {mode: sorted(ids) for mode, ids in self.stopped.items() if ids}}

    def restore(self, state):
        state = state or {}
        self.resume = bool(state.get("pending"))
        self.stopped = {mode: set(ids) for mode, ids in (state.get("stopped") or {}).items()}      # the greyed link marks of the files whose sharing was stopped
        self.reload(reset=not state.get("tree"), state=state.get("tree") or None)
        sizes = state.get("splitter")
        self.sized = bool(sizes)
        if sizes:
            self.splitter.setSizes(sizes)
