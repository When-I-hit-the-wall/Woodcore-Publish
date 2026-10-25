"""The base every editor tab of sources is built on: a list of the sources on the left, in folders, the draft in the middle, its result on the right (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, ARCH-001, solution B).

Until v0.120 each editor tab wrote its own left pane -- the list, its folders, the dot of unsaved changes, a drop into a folder, a source chosen, a source loaded -- and the same hundred and fifty lines stood, word for word but for the keys of their words, in «Connecteurs», the three tabs of loads and the nine member checks, and with small differences in five more. They are written once here. A tab says what is its own:

* `KEY` -- the key its view, its folders and its list's order are kept under (tab_registry.SPECS names it);
* `LIST_KEY`, `EMPTY_KEY` -- its list's title and the line under an empty list; `WORDS` -- the prefix of its words for «Nouveau», «Dupliquer», «Supprimer», a draft's row and a drop into a folder (`<prefix>_new`, `_duplicate`, `_delete`, `_new_item`, `_moved`);
* `sources_dir()` -- where its sources lie; `saved_ids()` -- which of them it lists (by default every `*.json` there); `listed()` -- the rows it lists them by, `(id, text, group)` (by default the id in its own folder);
* `read_saved(path)` -- a source read to be edited (by default its domain's `read_source`, and a source the domain refuses opened as it is, so that it can be repaired here);
* and the draft's own: `fill_form`, `refresh`, `draft`, `new`, `duplicate`, `delete`, `save`, `export(done)`, `confirm_leave`.

**The list is the base's in every editor tab, the four canvases too** (spec 2026-10-21-restes-issue-69, UI-001, ARCH-001): «Schémas», «Statique», «Plan de positions» and «Plan feu», «Moment polaire» filled their list, chose a row and filed rows in a folder each their own way until v0.120 -- the static models and the plans moving a source without saving the draft first, and a file the disk refused raising out of the window. They say what differs through hooks, each a no-op or the common case here: `listed()`, `draft_text()`, `draft_group()` and `take_group(group)` (the folder of the draft, which a drop into a folder gives it), `list_selection(select)`, `show_empty_hint()`, `on_row_again(cid)` (the row of the source already open, chosen again), `after_row_loaded(cid)`, and `export_listed(text)`, the export a drop or an archive rebuilds, naming no source. None of them writes: `on_moved` is the writer, guarded once.

The writers it defines (`on_moved`) are guarded where they are defined, once (tab_guard.guard walks the whole hierarchy), and followed by the domains' files where the tab says `SYNC_DOMAIN`. Qt-free in its own body; it stands in a tab's bases before `QWidget`, as `display_view.DisplayTab` does, and is no abstract class -- a QWidget's metaclass does not mix with one (ARCH-RISK-103).
"""

import json

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

import autosave
import cards
import case_list_logic
import draft_logic
import grouped_list
import source_archive
import validation
from case_list_logic import NEW_ROW, next_free_id   # the list's rules, written once without Qt and called by the tabs built on a type too (spec 2026-10-23-onglets-types-et-services, ARCH-006); re-exported, the tabs import them from here

# The words a tab of sources names by its prefix (`WORDS`), `<prefix>_<suffix>`: what its list's buttons say, a draft's row, a drop into a folder, the question about unsaved changes and a failed export. tests/test_i18n.py counts them as named.
WORD_SUFFIXES = ("new", "duplicate", "delete", "new_item", "moved", "unsaved", "unsaved_title", "export_failed")

def save_shortcut(tab):
    """Ctrl+S saves the draft of `tab`, and of this tab alone: every tab is built when the window opens, and a shortcut of the whole window would be claimed by each of them at once. The one way an editor tab binds it (thirteen copies of these lines until v0.120)."""
    shortcut = QShortcut(QKeySequence(QKeySequence.StandardKey.Save), tab)
    shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
    shortcut.activated.connect(tab.save)
    return shortcut


class SourceEditorTab:
    KEY = ""
    LIST_KEY = ""
    EMPTY_KEY = ""
    WORDS = ""
    DOMAIN = None
    ID_PREFIX = ""
    DUPLICATE_FORGETS = ("name",)   # what a copy does not keep of the source it was made from: its name, so that two sources are not named alike
    # The question about unsaved changes (confirm_leave): its two words, WORDS' own unless a tab names others -- the canvases, which have no WORDS -- and whether discarding a draft never saved opens the first source in its place, as the canvases and the polar moments do (spec 2026-10-20-indices-et-niveaux, ARCH-005: their three copies of confirm_leave, written once)
    UNSAVED_WORDS = None
    DISCARD_OPENS_FIRST = False
    LIST_MARGINS = None   # the left pane's margins (left, top, right, bottom), where a tab keeps a gap before its splitter -- the canvases'
    GRAPH_KIND = None     # the kind of node of the graph of dependencies its sources are (dependency_graph.KINDS): what «Dépendances» opens in it (issue #71)

    # --- the draft's life: new, a copy, back to what is saved, deleted, exported ------------------

    def make_source(self):
        return self.DOMAIN.new_source(next_free_id(self.saved_ids(), self.ID_PREFIX))

    def after_new(self):
        """What a tab does to a source just made before it is shown (connectors: the schema's markers adopted)."""

    def duplicate_id(self, source):
        return next_free_id(self.saved_ids(), self.ID_PREFIX)

    def new(self):
        draft_logic.new(self)

    def duplicate(self):
        draft_logic.duplicate(self)

    def revert(self):
        draft_logic.revert(self)

    def delete(self):
        """«Supprimer»: what is selected goes to «Archives», its id removed (source_archive.py, v0.77) -- or, an archived entry selected, is deleted for good. A source never saved is simply discarded."""
        if self.archive.delete():
            return
        self.dirty = False
        self.open_first()

    def open_first(self):
        """What the form shows once the source it showed is gone (draft_logic.open_first)."""
        draft_logic.open_first(self)

    def blank(self):
        """The form once its source is gone and nothing is left to open, with no dot (draft_logic.blank, issue #97)."""
        draft_logic.blank(self)

    def _after_archive(self):
        draft_logic.after_archive(self)

    def fail_title(self):
        return self.t(self.KEY)

    def fail(self, message):
        return autosave.refuse(self, self.fail_title(), message)

    def export_sources(self):
        """The tab's export written (data/…json) -- the tab's own exporter."""
        raise NotImplementedError(f"{type(self).__name__} names its exporter")

    def export_listed(self, text):
        """The export rebuilt after the list changed sources without naming one -- rows dropped into a folder, a source archived or put back: the tab's `export(done)`, a canvas's own export with no id."""
        return self.export(text)

    def export(self, done):
        """The export rebuilt with what was saved: a failure is said in the status bar, the source stays saved."""
        try:
            self.export_sources()
        except Exception as exc:  # broad: the exporter's own message is what helps, said in the status bar
            self.app.set_status(self.word("export_failed", error=str(exc)))
            return
        self.app.set_status(done)

    # --- what a tab says of its own sources ------------------------------------------------

    def sources_dir(self):
        raise NotImplementedError(f"{type(self).__name__} names where its sources lie")

    def saved_ids(self):
        folder = self.sources_dir()
        return sorted(p.stem for p in folder.glob("*.json")) if folder.is_dir() else []

    def archived_entries(self):
        return source_archive.entries(self.sources_dir(), self.list._t)

    def read_saved(self, path):
        try:
            return self.DOMAIN.read_source(path)
        except validation.ValidationError:
            return json.loads(path.read_text(encoding="utf-8"))   # a source the checks refuse is still opened, so that it can be repaired here

    def word(self, suffix, **args):
        return self.t(f"{self.WORDS}_{suffix}", **args)

    def current_label(self):
        """What the question about unsaved changes names the draft by: the id typed in its identity row («Nom · Description · ID», identity.py) or in its own id field, «?» while it is empty."""
        field = getattr(getattr(self, "identity", None), "id", None) or getattr(self, "id_edit", None)
        return (field.text().strip() if field is not None else (self.source or {}).get("id", "")) or "?"

    def confirm_leave(self):
        """Before the draft is left -- another source chosen, another tab, view or document, the window closed --: saved without a question where it can be, else the one question (autosave.py, v0.117)."""
        title, message = self.UNSAVED_WORDS or (f"{self.WORDS}_unsaved_title", f"{self.WORDS}_unsaved")
        more = {"discard": self.discard_draft} if self.DISCARD_OPENS_FIRST else {}
        return autosave.confirm(self.app, self, self.t(title), self.t(message, id=self.current_label()), **more)

    def discard_draft(self):
        """What «Abandonner» does where DISCARD_OPENS_FIRST: the draft forgotten, and a draft never saved gives its place to the first source of the list."""
        draft_logic.discard(self)

    # --- the left pane ----------------------------------------------------------------------

    def heading(self, text):
        label = QLabel(text)
        label.setFont(self.app.bold_font)
        return label

    def build_list(self):
        box = QWidget()
        column = QVBoxLayout(box)
        if self.LIST_MARGINS:
            column.setContentsMargins(*self.LIST_MARGINS)
        self.list = grouped_list.GroupedList(self.list_words(), lang=self.app.lang)
        # an archive gives the form to the first source where a draft discarded does (DISCARD_OPENS_FIRST), else to a new one
        self.archive = source_archive.Actions(self, self.sources_dir, self.export_listed, lambda select: self.reload_list(select),
                                              self.load_first if self.DISCARD_OPENS_FIRST else self._after_archive)
        self.archive.connect()
        column.addWidget(grouped_list.title_row(self.heading(self.t(self.LIST_KEY)), self.list))
        self.list.setIconSize(self.app.mark_size)
        self.list.currentIdChanged.connect(self.on_list_change)
        self.list.moved.connect(self.on_moved)
        self.list.foldersChanged.connect(self.on_folders_changed)
        self.list.attach_order(self.KEY, self.app.list_store)   # the order the engineer gives the list by drag and drop, kept in Woodcore-Datei/lists.json (calc/list_order.py, issue #15)
        self.list.reordered.connect(lambda: self.reload_list(self.current_id))
        column.addWidget(self.list, 1)
        self.empty_hint = cards.note(self.t(self.EMPTY_KEY))
        column.addWidget(self.empty_hint)
        row = QHBoxLayout()
        for suffix, slot in (("new", self.new), ("duplicate", self.duplicate), ("delete", self.delete)):
            button = QPushButton(self.word(suffix))
            button.clicked.connect(slot)
            row.addWidget(button)
        column.addLayout(row)
        return box

    def list_words(self):
        """The words of the list's own menus and dialogs (grouped_list.GroupedList): the tab module's `STRINGS` in the window's language."""
        import sys
        strings = sys.modules[type(self).__module__].STRINGS
        return strings.get(self.app.lang, strings["fr"])

    def _group_of(self, cid):
        """The folder a source is filed in, read off its own `group` -- the field, never a directory (grouped_list.py)."""
        return case_list_logic.group_of_file(self.sources_dir() / ("%s.json" % cid))

    def install_save_shortcut(self):
        return save_shortcut(self)

    def listed(self):
        """The rows of the saved sources, in order, `(id, text, group)`: the id, in the folder its source names."""
        return [(cid, cid, self._group_of(cid)) for cid in self.saved_ids()]

    def draft_text(self):
        """The row of the draft nobody has saved yet: the id it would be saved under, and «(nouveau)»."""
        return f"{self.current_label()} {self.word('new_item')}"

    def draft_group(self):
        """The folder the draft's row stands in: its own `group`, the root until a drop gives it one."""
        return grouped_list.group_of(self.source or {})

    def take_group(self, group):
        """The draft takes the folder `group` (None: the root): what it is saved with, so that its next save does not put it back where it was."""
        case_list_logic.set_group(self.source, group)

    def list_selection(self, select):
        """The row the list chooses once filled: `select`, else the source open -- the draft's row where it is unsaved."""
        return case_list_logic.selection(select, self.current_id, self.ids)

    def show_empty_hint(self):
        """The line under an empty list."""
        self.empty_hint.setVisible(not self.ids)

    def on_row_again(self, cid):
        """The row of the source already open chosen again (or the draft's row while the draft is open): nothing to load."""

    def after_row_loaded(self, cid):
        """What a tab does once a row chosen is loaded."""

    def reload_list(self, select=None):
        case_list_logic.reload(self, select)

    def on_folders_changed(self):
        """A folder made, renamed or removed in the list: what the widget now holds is what the tab keeps (case_list_logic.folders_changed)."""
        case_list_logic.folders_changed(self)

    def update_list_marker(self):
        """A dot beside the source being edited while it has unsaved changes (case_list_logic.update_marks)."""
        case_list_logic.update_marks(self)

    def on_list_change(self, cid):
        case_list_logic.row_changed(self, cid)

    def on_moved(self, ids, group):
        """A drop wrote a folder (UI-001): the draft saved first where it can be, the field written into each source, the sources written exported, the list rebuilt (case_list_logic.move)."""
        case_list_logic.move(self, ids, group)

    def graph_id(self, cid):
        """The id a source of this tab has in the graph of dependencies: its own, by default."""
        return cid

    def lists_object(self, ident):
        """Whether the object `ident` of the graph is one of this tab's sources (MainWindow.open_object). Not `owns`, which a member check tab asks of a source."""
        return case_list_logic.lists_object(self, ident)

    def open_object(self, ident):
        """The source the graph names `ident` opened here, the draft open left as choosing another row leaves it (`confirm_leave`)."""
        case_list_logic.open_object(self, ident)

    def load(self, cid):
        draft_logic.load(self, cid)
