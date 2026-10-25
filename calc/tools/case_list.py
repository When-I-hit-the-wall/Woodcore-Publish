"""The services of a case: the list of the cases on the left, and its identity at the head of the form (spec docs/requirements/completed/2026-10-23-onglets-types-et-services.md, ARCH-001; tab_host.py).

**The list** (`CaseList`) is the left pane every tab of cases has -- the cases in folders, «Archives», «Nouveau» · «Dupliquer» · «Supprimer», the dot of unsaved changes, a drop into a folder -- its rules case_list_logic's, the same functions `source_editor.SourceEditorTab` calls. Its writer, a drop into a folder (`move`), is guarded where it is defined (tab_guard.guard_service); its archive is source_archive.Actions, which reads the list, the id open and the dot off this service, as it reads them off an editor tab.

**The identity** (`Identity`) is the card «Nom · Description · ID» (identity.py), the first contributor to the draft.
"""

import sys

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

import cards
import case_list_logic
import grouped_list
import identity
import source_archive
from tab_host import Service


class CaseList(Service):
    """The list of the cases -- see the module's docstring. It is the host of case_list_logic's functions: the state it reads is the context's."""

    NAME = "cases"
    ZONE = "left"
    WRITERS = ("move",)
    KEEPS_ORDER = True   # the order the engineer drags kept in lists.json; a list ordered by its own rule keeps none (check_list.CheckList, issue #112)

    def mount(self, ctx):
        super().mount(ctx)
        self.KEY = ctx.key
        self.empty_folders = list(self.app.folder_settings(self.KEY))
        box = QWidget()
        column = QVBoxLayout(box)
        self.list = grouped_list.GroupedList(self.list_words(), lang=self.app.lang)
        self.archive = source_archive.Actions(self, ctx.store.folder, ctx.export_listed, lambda select: self.reload_list(select), ctx.after_archive)
        self.archive.connect()
        heading = QLabel(self.t(ctx.param("LIST_KEY")))
        heading.setFont(self.app.bold_font)
        column.addWidget(grouped_list.title_row(heading, self.list))
        self.list.setIconSize(self.app.mark_size)
        self.list.currentIdChanged.connect(self.on_list_change)
        self.list.moved.connect(self.move)
        self.list.foldersChanged.connect(lambda: case_list_logic.folders_changed(self))
        if self.KEEPS_ORDER:
            self.list.attach_order(self.KEY, self.app.list_store)   # the order the engineer gives the list by drag and drop, kept in Woodcore-Datei/lists.json (calc/list_order.py, issue #15)
        self.list.reordered.connect(lambda: self.reload_list(self.current_id))
        column.addWidget(self.list, 1)
        self.empty_hint = cards.note(self.t(ctx.param("EMPTY_KEY")))
        column.addWidget(self.empty_hint)
        row = QHBoxLayout()
        for suffix, slot in (("new", ctx.new), ("duplicate", ctx.duplicate), ("delete", ctx.delete)):
            button = QPushButton(ctx.word(suffix))
            button.clicked.connect(slot)
            row.addWidget(button)
        column.addLayout(row)
        return box

    def list_words(self):
        """The words of the list's own menus and dialogs (grouped_list.GroupedList): the tab module's `STRINGS` in the window's language, as an editor tab reads them."""
        words = sys.modules[type(self.ctx.host).__module__].STRINGS
        return words.get(self.app.lang, words["fr"])

    # --- the state the rules read: the context's -----------------------------------------

    source = property(lambda self: self.ctx.source)
    current_id = property(lambda self: self.ctx.current_id, lambda self, v: setattr(self.ctx, "current_id", v))
    dirty = property(lambda self: self.ctx.dirty, lambda self, v: setattr(self.ctx, "dirty", v))
    loading = property(lambda self: self.ctx.loading, lambda self, v: setattr(self.ctx, "loading", v))
    ids = property(lambda self: self.ctx.ids, lambda self, v: setattr(self.ctx, "ids", v))

    def word(self, suffix, **args):
        return self.ctx.word(suffix, **args)

    def sources_dir(self):
        return self.ctx.store.folder()

    def confirm_leave(self):
        return self.ctx.confirm_leave()

    def load(self, cid):
        self.ctx.load(cid)

    def export_listed(self, text):
        self.ctx.export_listed(text)

    def take_group(self, group):
        case_list_logic.set_group(self.ctx.source, group)

    def on_row_again(self, cid):
        """The row of the case already open chosen again: nothing to load."""

    def after_row_loaded(self, cid):
        """Nothing more once a row chosen is loaded."""

    # --- what the list shows -----------------------------------------------------------

    def listed(self):
        """The rows of the saved cases, `(id, text, group)`: the id, in the folder its source names."""
        return [(cid, cid, case_list_logic.group_of_file(self.ctx.store.path(cid))) for cid in self.ctx.store.ids()]

    def draft_text(self):
        """The row of the draft nobody has saved yet: the id it would be saved under, and «(nouveau)»."""
        return f"{self.ctx.current_label()} {self.word('new_item')}"

    def draft_group(self):
        return grouped_list.group_of(self.ctx.source or {})

    def list_selection(self, select):
        return case_list_logic.selection(select, self.current_id, self.ids)

    def archived_entries(self):
        base = source_archive.folder(self.ctx.store.folder())
        return [row for row in source_archive.entries(self.ctx.store.folder(), self.list._t)
                if self.ctx.store.owns_archived(base / row["id"][len(source_archive.KEY_PREFIX):])]   # a tab's own, where tabs share a folder (issue #112)

    def show_empty_hint(self):
        self.empty_hint.setVisible(not self.ids)

    def update_list_marker(self):
        case_list_logic.update_marks(self)

    # --- the phases and the signals ------------------------------------------------------

    def reload_list(self, select=None):
        case_list_logic.reload(self, select)

    def update_marks(self):
        case_list_logic.update_marks(self)

    def select_row(self, cid):
        self.list.select(cid)

    def on_list_change(self, cid):
        case_list_logic.row_changed(self, cid)

    def move(self, ids, group):
        """A drop wrote a folder: the draft saved first where it can be, the field written into each case, the cases exported, the list rebuilt (case_list_logic.move). Guarded: refused in a project open read-only."""
        case_list_logic.move(self, ids, group)

    def state(self):
        return {"empty_folders": list(self.empty_folders)}

    def restore(self, state):
        self.empty_folders = list((state or {}).get("empty_folders") or [])


class Identity(Service):
    """The card «Nom · Description · ID» at the head of the form (identity.py): the first contributor to the draft."""

    NAME = "identity"
    ZONE = "centre"

    def mount(self, ctx):
        super().mount(ctx)
        box = cards.card()
        form = cards.form(box)
        self.rows = identity.IdentityRows(form, self.t, ctx.touch)
        return box

    def fill(self, src):
        self.rows.fill(src.get("name", ""), src.get("label", ""), src.get("id", ""), saved=self.ctx.current_id is not None)

    def collect(self, src):
        name, description, sid = self.rows.values()
        src["id"], src["name"], src["label"] = sid, name, description
