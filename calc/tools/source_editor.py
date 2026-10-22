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
import engine
import grouped_list
import source_archive
import validation

# The words a tab of sources names by its prefix (`WORDS`), `<prefix>_<suffix>`: what its list's buttons say, a draft's row, a drop into a folder, the question about unsaved changes and a failed export. tests/test_i18n.py counts them as named.
WORD_SUFFIXES = ("new", "duplicate", "delete", "new_item", "moved", "unsaved", "unsaved_title", "export_failed")

NEW_ROW = "<new>"   # the list's row of the draft nobody has saved yet -- the one constant, which the tabs import (six copies until v0.120)


def next_free_id(taken, prefix):
    """The first id `prefix` + two digits that no source of `taken` holds -- compared without case, a file system that does not tell `s01` from `S01` being the engineer's own (five copies of this until v0.120, each with its own format)."""
    lowered = {t.lower() for t in taken}
    index = 1
    while f"{prefix}{index:02d}".lower() in lowered:
        index += 1
    return f"{prefix}{index:02d}"


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
        if not self.confirm_leave():
            return
        self.source = self.make_source()
        self.current_id = None
        self.dirty = True
        self.after_new()
        self.fill_form()
        self.refresh()
        self.reload_list()

    def duplicate(self):
        if not self.confirm_leave():
            return
        source = self.draft()
        source["id"] = self.duplicate_id(source)
        for key in self.DUPLICATE_FORGETS:
            source.pop(key, None)
        self.source = source
        self.current_id = None
        self.dirty = True
        self.fill_form()
        self.refresh()
        self.reload_list()

    def revert(self):
        if self.current_id:
            self.load(self.current_id)
        else:
            self.new()

    def delete(self):
        """«Supprimer»: what is selected goes to «Archives», its id removed (source_archive.py, v0.77) -- or, an archived entry selected, is deleted for good. A source never saved is simply discarded."""
        if self.archive.delete():
            return
        self.dirty = False
        self.open_first()

    def open_first(self):
        """What the form shows once the source it showed is gone: the first source of the list, else a new one. A tab that keeps its own way of opening the first (`load_first`) says so."""
        if hasattr(self, "load_first"):
            self.load_first()
            return
        self.reload_list()
        if self.ids:
            self.load(self.ids[0])
            self.reload_list(self.ids[0])
        else:
            self.new()

    def _after_archive(self):
        """The source the form showed was archived: a new one opens, as deleting always did."""
        self.reload_list()
        self.new()

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
        self.dirty = False
        if self.current_id is None:
            self.load_first()

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
        try:
            source = json.loads((self.sources_dir() / ("%s.json" % cid)).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return grouped_list.ROOT_GROUP
        return grouped_list.group_of(source)

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
        if self.source is None:
            return
        if group:
            self.source["group"] = group
        else:
            self.source.pop("group", None)

    def list_selection(self, select):
        """The row the list chooses once filled: `select`, else the source open -- the draft's row where it is unsaved."""
        if select is None:
            select = self.current_id
        if select in self.ids:
            return select
        return NEW_ROW if self.current_id is None else None

    def show_empty_hint(self):
        """The line under an empty list."""
        self.empty_hint.setVisible(not self.ids)

    def on_row_again(self, cid):
        """The row of the source already open chosen again (or the draft's row while the draft is open): nothing to load."""

    def after_row_loaded(self, cid):
        """What a tab does once a row chosen is loaded."""

    def reload_list(self, select=None):
        was_loading = self.loading
        self.loading = True
        rows = self.listed()
        self.ids = [cid for cid, _text, _group in rows]
        entries = [{"id": cid, "text": text, "group": group} for cid, text, group in rows]
        if self.current_id is None:      # the draft nobody has saved yet, where it can be seen
            entries.append({"id": NEW_ROW, "text": self.draft_text(), "group": self.draft_group()})
        self.list.set_entries(entries, self.empty_folders, self.list_selection(select), archived=self.archived_entries())
        self.empty_folders = self.list.empty_folders()
        self.app.save_folder_settings(self.KEY, self.empty_folders)
        self.show_empty_hint()
        self.loading = was_loading   # a list rebuilt while the form is being filled leaves it being filled
        self.update_list_marker()

    def on_folders_changed(self):
        """A folder made, renamed or removed in the list: what the widget now holds is what the tab keeps. ⚠️ Connecting `foldersChanged` straight to `reload_list` rebuilt the list from the tab's own copy of the empty folders, taken BEFORE the new one was added -- so a folder just made vanished the moment it was made."""
        self.empty_folders = self.list.empty_folders()
        self.reload_list(select=self.current_id)

    def update_list_marker(self):
        """A dot beside the source being edited while it has unsaved changes. Every row carries a mark, dot or blank, so none of them moves sideways as the form is typed into."""
        for cid in self.list.ids():
            mine = cid == self.current_id or (self.current_id is None and cid == NEW_ROW)
            self.list.set_mark(cid, self.app.dirty_mark(mine and self.dirty))
        self.app.update_tab_marks()

    def on_list_change(self, cid):
        if self.loading or not cid:
            return
        if cid == self.current_id or (cid == NEW_ROW and self.current_id is None):
            self.on_row_again(cid)
            return
        if cid not in self.ids:
            return
        if not self.confirm_leave():
            self.reload_list(self.current_id)   # the row of the source kept chosen again
            return
        self.load(cid)
        self.after_row_loaded(cid)
        if NEW_ROW in self.list.ids():
            self.reload_list(cid)         # the draft given up leaves the list

    def on_moved(self, ids, group):
        """A drop wrote a folder (UI-001): the draft is saved first where it can be (`confirm_leave`, the question asked only where it cannot), then the field goes into each source, the sources written are exported, and the list is rebuilt from the files. The draft takes the folder too -- the source open, or the draft never saved, whose row was dropped -- or its next save would put it back where it was. A file the disk refuses (OneDrive holding it) stops the move there: what was written before is exported, and the status bar says which file failed, last."""
        if not self.confirm_leave():
            self.reload_list(self.current_id)
            return
        targets = [cid for cid in ids if cid != NEW_ROW]
        if NEW_ROW in ids:
            if self.current_id is None:
                self.take_group(group)    # a draft has no file to write the field into: it carries the folder until it is saved
            elif self.current_id not in targets:
                targets.append(self.current_id)   # saved just now by confirm_leave: its file takes the folder
        written, failure = [], None
        for cid in targets:
            path = self.sources_dir() / ("%s.json" % cid)
            try:
                source = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if group:
                source["group"] = group
            else:
                source.pop("group", None)
            try:
                engine.write_json(path, source)
            except OSError as exc:
                failure = self.t("list_write_failed", id=cid, error=str(exc))
                break
            written.append(cid)
            if cid == self.current_id:
                self.take_group(group)
        if written:
            self.export_listed(self.word("moved", count=len(written), group=group or "—"))
        self.reload_list(self.current_id)
        if failure:
            self.app.set_status(failure)

    def graph_id(self, cid):
        """The id a source of this tab has in the graph of dependencies: its own, by default."""
        return cid

    def lists_object(self, ident):
        """Whether the object `ident` of the graph is one of this tab's sources (MainWindow.open_object). Not `owns`, which a member check tab asks of a source."""
        return any(self.graph_id(cid) == ident for cid in self.saved_ids())

    def open_object(self, ident):
        """The source the graph names `ident` opened here, the draft open left as choosing another row leaves it (`confirm_leave`)."""
        cid = next((c for c in self.saved_ids() if self.graph_id(c) == ident), None)
        if cid is None or cid == self.current_id or not self.confirm_leave():
            return
        self.load(cid)
        self.reload_list(cid)

    def load(self, cid):
        self.source = self.read_saved(self.sources_dir() / ("%s.json" % cid))
        self.current_id = cid
        self.dirty = False
        self.fill_form()
        self.refresh()
