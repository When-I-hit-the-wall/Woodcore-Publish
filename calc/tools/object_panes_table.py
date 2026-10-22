"""The editors of a table and of a live-load table in the right pane -- rows and columns, a cell's value written over, the live loads' categories -- split out of calc/tools/object_panes.py (issue #30), moved verbatim. object_panes.py imports every name back.
"""

from dataclasses import dataclass, field
from PySide6.QtCore import QEvent, QSize, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFileDialog, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton, QSpinBox, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)
import cards  # the cards a pane is made of (cards.py)
import richtext  # a symbol set as mathematics (richtext.py)
from i18n import strings as glossary  # the engine's words: a category of Tabelle 8 in the window's language
from typst_objects import AUTO, Content, Expr, ModelError
from object_panes_fields import (  # split out of this module (issue #30): every name it had is still importable from it
    CellField,
    DEBOUNCE_MS,
    ListBox,
    Pane,
    Switch,
    Text,
    _STRING,
    _VARIABLE,
    _between,
    _drop,
    _unescape,
    as_context,
    call_of,
    parse_number,
    plain,
    show_number,
    variable_of,
)


# The two values of a live-load row the category fills.
LOAD_VALUES = ("q_k", "Q_k")


# The kind of a column the two load tables know by its id, where its entry names none (calc/typst_objects.py KNOWN_COLUMNS; lib/document.typ).
KNOWN_KINDS = {"zone": "text", "storey": "text", "use": "wide", "category": "math", "q_k": "number", "Q_k": "number",
               "buildup": "wide", "load": "number"}


# The word of the glossary each known column is headed with by default.
KNOWN_TITLES = {"zone": "document.zone", "storey": "document.storey", "use": "document.use", "category": "document.category",
                "buildup": "document.buildup", "load": "document.superimposed"}


# What a column the command knows by its id and that is headed by its symbol is shown as.
KNOWN_SYMBOLS = {"q_k": "q_k", "Q_k": "Q_k"}


class TablePane(Pane):
    """A table of the document (`doc-table`) or the dead loads (`dead-load-table`): the list of its rows with Add / Remove / ↑ / ↓, the fields of the chosen row -- one for each column printed --, the list of its columns with a check box each (printed or hidden), a title for the chosen one, a caption, the notes."""
    KINDS = ("doc-table", "dead-load-table")
    SUMMARY_SKIP = ()

    def init_state(self):
        self.cell_fields = {}
        self.notes_were_a_list = False

    # -- reading

    def visible_columns(self):
        return [c for c in self.model.columns if not c.hidden]

    def listed_columns(self):
        return list(self.model.columns)

    def column_title(self, column):
        """The heading a column carries: its title as written, else the command's own word for a column it knows by its id."""
        written = plain(column.title) if column.title is not None else None
        if column.title is not None and written:
            return written
        if column.known and column.id in KNOWN_SYMBOLS:
            return KNOWN_SYMBOLS[column.id]
        if column.known and column.id in KNOWN_TITLES:
            return glossary.text(KNOWN_TITLES[column.id], self.lang)
        return column.id

    def column_kind(self, column):
        return column.kind or (KNOWN_KINDS.get(column.id, "text") if column.known else "text")

    def cell_summary(self, value):
        found = variable_of(value)
        if found is not None:
            return found[0]
        if value is None or value is AUTO:
            return ""
        if isinstance(value, Expr):
            return "…"
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return show_number(value)
        shown = plain(value)
        return " ".join((shown or "").split())

    def row_summary(self, index):
        parts = []
        for column in self.visible_columns():
            if column.id in self.SUMMARY_SKIP:
                continue
            shown = self.cell_summary(self.model.cell(index, column.id))
            if shown:
                parts.append(shown)
        return f"{index + 1}. " + (" · ".join(parts) if parts else self.t("op_row_empty"))

    def row_index(self):
        row = self.row_list.currentRow()
        return row if _between(range(self.model.row_count), row) else None

    def column_id(self):
        item = self.column_list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item is not None else None

    # -- building

    def build(self, layout):
        t = self.t
        card = cards.card(t("op_rows"))
        box = QVBoxLayout(card)
        self.row_list = self.make_list(6)
        self.row_list.currentRowChanged.connect(self.on_row_chosen)
        box.addWidget(self.row_list)
        self.row_add, self.row_remove, self.row_up, self.row_down, bar = self.list_buttons(self.add_row, self.remove_row, lambda: self.move_row(-1), lambda: self.move_row(1))
        box.addLayout(bar)
        layout.addWidget(card)

        self.fields_card = cards.card(t("op_row_fields"))
        self.fields_layout = QVBoxLayout(self.fields_card)
        self.fields_body = None
        layout.addWidget(self.fields_card)

        card = cards.card(t("op_columns"))
        box = QVBoxLayout(card)
        self.column_list = self.make_list(7)      # the live loads table has six columns: all of them show, a longer table's scroll
        self.column_list.itemChanged.connect(self.on_column_checked)
        self.column_list.currentRowChanged.connect(self.on_column_chosen)
        box.addWidget(self.column_list)
        self.col_add, self.col_remove, self.col_up, self.col_down, bar = self.list_buttons(self.add_column, self.remove_column, lambda: self.move_column(-1), lambda: self.move_column(1), "op_col_add_tip")
        box.addLayout(bar)
        form = cards.form()
        self.column_title_edit = self.line_edit(self.column_title_edited)
        form.addRow(QLabel(t("op_col_title")), self.column_title_edit)
        box.addLayout(form)
        layout.addWidget(card)

        card = cards.card(t("op_caption_notes"))
        form = cards.form(card)
        self.caption_edit = self.line_edit(self.caption_edited)
        form.addRow(QLabel(t("op_caption")), self.caption_edit)
        self.notes_edit = Text(3)
        self.notes_edit.setToolTip(t("op_notes_tip"))
        self.notes_edit.textChanged.connect(self.notes_edited)
        form.addRow(QLabel(t("op_notes")), self.notes_edit)
        self.header_check = Switch(t("op_header"))
        self.header_check.toggled.connect(self.header_toggled)
        form.addRow(self.header_check)
        layout.addWidget(card)

    # -- filling

    def refresh(self):
        self.refresh_rows(select=self.row_list.currentRow() if self.row_list.count() else 0)
        self.refresh_columns(select=0)
        self.set_edit(self.caption_edit, self.model.get("caption"), self.t("op_expr"))
        notes = self.model.get("notes")
        items = notes if isinstance(notes, (list, tuple)) else [notes]
        shown = [plain(n) for n in items if n is not None]
        was = self.notes_edit.blockSignals(True)
        self.notes_edit.setPlainText("\n".join("" if s is None else s for s in shown))
        self.notes_edit.setEnabled(all(s is not None and "\n" not in s for s in shown))
        self.notes_edit.blockSignals(was)
        self.notes_were_a_list = isinstance(notes, (list, tuple))
        is_doc_table = self.model.type == "doc-table"
        self.header_check.setVisible(is_doc_table)
        if is_doc_table:
            self.header_check.set(self.model.get("header"))

    def refresh_rows(self, select=0):
        self._loading += 1
        try:
            self.row_list.clear()
            for index in range(self.model.row_count):
                self.row_list.addItem(QListWidgetItem(self.row_summary(index)))
            if self.row_list.count():
                self.row_list.setCurrentRow(max(0, min(select if select is not None else 0, self.row_list.count() - 1)))
        finally:
            self._loading -= 1
        self.after_row_chosen()

    def refresh_columns(self, select=0):
        self._loading += 1
        try:
            self.column_list.clear()
            for column in self.listed_columns():
                item = QListWidgetItem(self.column_title(column))
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked if column.hidden else Qt.CheckState.Checked)
                item.setData(Qt.ItemDataRole.UserRole, column.id)
                item.setToolTip(self.t("op_col_shown_tip"))
                self.column_list.addItem(item)
            if isinstance(select, str):
                select = next((i for i in range(self.column_list.count()) if self.column_list.item(i).data(Qt.ItemDataRole.UserRole) == select), 0)
            if self.column_list.count():
                self.column_list.setCurrentRow(max(0, min(select or 0, self.column_list.count() - 1)))
        finally:
            self._loading -= 1
        self.after_column_chosen()

    def after_row_chosen(self):
        row, count = self.row_index(), self.model.row_count
        self.row_remove.setEnabled(row is not None)
        self.row_up.setEnabled(row is not None and row > 0)
        self.row_down.setEnabled(row is not None and row < count - 1)
        self.fill_fields()

    def after_column_chosen(self):
        column_id = self.column_id()
        listed = self.listed_columns()
        at = next((i for i, c in enumerate(listed) if c.id == column_id), None)
        column = listed[at] if at is not None else None
        self.col_remove.setEnabled(column is not None and not column.known)
        self.col_remove.setToolTip(self.t("op_col_known_tip") if column is not None and column.known else "")
        self.col_up.setEnabled(at is not None and at > 0)
        self.col_down.setEnabled(at is not None and at < len(listed) - 1)
        self.column_title_edit.setEnabled(column is not None)
        was = self.column_title_edit.blockSignals(True)
        self.column_title_edit.setText("" if column is None or column.title is None else (plain(column.title) or ""))
        self.column_title_edit.setPlaceholderText(self.t("op_col_title_default") if column is not None and column.known else "")
        self.column_title_edit.blockSignals(was)

    def fill_fields(self):
        """One editor for each column printed, for the row chosen."""
        body = self.fresh(self.fields_layout, "fields_body")
        self.cell_fields = {}
        form = cards.form(body)
        form.setContentsMargins(0, 0, 0, 0)
        row = self.row_index()
        if row is None:
            form.addRow(cards.note(self.t("op_no_row")))
            return
        for column in self.visible_columns():
            field = self.make_cell_field(row, column)
            self.cell_fields[column.id] = field
            form.addRow(self.field_label_widget(column), field)

    def field_label_widget(self, column):
        """The label of a field: the column's heading, a symbol -- q_k -- set as mathematics."""
        label = QLabel()
        if column.known and column.id in KNOWN_SYMBOLS and column.title is None:
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setText(richtext.math_html(KNOWN_SYMBOLS[column.id]))
        else:
            label.setText(self.field_label(column))
        return label

    def field_label(self, column):
        return self.column_title(column)

    def make_cell_field(self, row, column):
        """The editor of one cell: the text as written, or the variable it holds."""
        field = CellField(self, self.model.cell(row, column.id))
        field.edited.connect(lambda value, c=column.id: self.cell_edited(c, value))
        field.cleared.connect(lambda c=column.id: self.cell_edited(c, "", immediate=True))
        return field

    # -- the rows

    def on_row_chosen(self, _row):
        if self._loading or not self.ready():
            return
        self.after_row_chosen()

    def add_row(self):
        at = self.row_index()
        ok, new = self.do(self.model.add_row, None if at is None else at + 1)
        if ok:
            self.refresh_rows(select=new)

    def remove_row(self):
        at = self.row_index()
        if at is None:
            return
        ok, _ = self.do(self.model.remove_row, at)
        if ok:
            self.refresh_rows(select=at)

    def move_row(self, delta):
        at = self.row_index()
        if at is None or not _between(range(self.model.row_count), at + delta):
            return
        ok, _ = self.do(self.model.move_row, at, at + delta)
        if ok:
            self.refresh_rows(select=at + delta)

    def update_row_item(self, row):
        item = self.row_list.item(row)
        if item is not None:
            item.setText(self.row_summary(row))

    # -- the cells

    def parse_text(self, column, typed):
        """What a text typed in a cell is written as: a number in a number column where it reads as one, markup otherwise; '' empties the cell (a number column's key is taken off the row)."""
        if self.column_kind(column) == "number":
            if not typed.strip():
                return None
            number = parse_number(typed)
            if number is not None:
                return number
        return typed

    def cell_edited(self, column_id, value, immediate=None):
        """A cell written: a text typed (emitted after the debounce), a variable chosen or taken out (a button's edit: at once)."""
        if self._loading:
            return
        row = self.row_index()
        if row is None:
            return
        column = self.model.column(column_id)
        if isinstance(value, str):
            value = self.parse_text(column, value)
        at_once = isinstance(value, (Content, Expr)) if immediate is None else immediate
        if value is None:
            ok, _ = self.do(self.model.clear_cell, row, column_id, immediate=at_once)
        else:
            ok, _ = self.do(self.model.set_cell, row, column_id, value, immediate=at_once)
        if ok:
            self.update_row_item(row)

    # -- the columns

    def on_column_chosen(self, _row):
        if self._loading or not self.ready():
            return
        self.after_column_chosen()

    def on_column_checked(self, item):
        if self._loading or not self.ready():
            return
        column_id = item.data(Qt.ItemDataRole.UserRole)
        hidden = item.checkState() != Qt.CheckState.Checked
        ok, _ = self.do(self.model.set_hidden, column_id, hidden)
        if ok:
            self.refresh_rows(select=self.row_list.currentRow())
        else:
            self._loading += 1
            item.setCheckState(Qt.CheckState.Unchecked if self.model.is_hidden(column_id) else Qt.CheckState.Checked)
            self._loading -= 1

    def column_title_edited(self, typed):
        column_id = self.column_id()
        if column_id is None:
            return
        column = self.model.column(column_id)
        title = typed if typed.strip() else (None if column.known else "")
        ok, _ = self.do(self.model.set_column, column_id, title=title, immediate=False)
        if ok:
            item = self.column_list.currentItem()
            was = self.column_list.blockSignals(True)
            item.setText(self.column_title(self.model.column(column_id)))
            self.column_list.blockSignals(was)
            self.fill_fields()

    def add_column(self):
        taken = set(self.model.column_ids())
        n = 1
        while f"col{n}" in taken:
            n += 1
        ok, _ = self.do(self.model.add_column, f"col{n}", title=self.t("op_col_new", n=n))
        if ok:
            self.refresh_columns(select=f"col{n}")
            self.refresh_rows(select=self.row_list.currentRow())

    def remove_column(self):
        column_id = self.column_id()
        if column_id is None:
            return
        column = self.model.column(column_id)
        if column.known:
            return
        ok, _ = self.do(self.model.remove_column, column_id)
        if ok:
            at = self.column_list.currentRow()
            self.refresh_columns(select=at)
            self.refresh_rows(select=self.row_list.currentRow())

    def move_column(self, delta):
        listed = self.listed_columns()
        at = next((i for i, c in enumerate(listed) if c.id == self.column_id()), None)
        if at is None or not _between(listed, at + delta):
            return
        ids = self.model.column_ids()
        moved = listed[at].id
        ok, _ = self.do(self.model.move_column, moved, ids.index(listed[at + delta].id))
        if ok:
            self.refresh_columns(select=moved)
            self.fill_fields()

    # -- the caption and the notes

    def caption_edited(self, typed):
        ok, _ = self.do(self.model.set_caption, typed if typed.strip() else None, immediate=False)

    def notes_edited(self):
        if self._loading:
            return
        lines = [line for line in self.notes_edit.toPlainText().split("\n") if line.strip()]
        if not lines:
            notes = None
        elif len(lines) > 1 or self.notes_were_a_list:
            notes = lines
        else:
            notes = lines[0]
        self.do(self.model.set_notes, notes, immediate=False)

    def header_toggled(self, on):
        self.do(self.model.set_header, bool(on))


class RawTablePane(TablePane):
    """A table written in raw Typst, `#table(…)` (spec 2026-10-21-commandes-typst-refonte, ARCH-004, REQ-019): the same cards as a `doc-table`'s -- its rows, the fields of the chosen one, its columns printed or hidden and their titles, the caption of the figure it stands in, its header -- and the alignment of the chosen column (Q-012); no notes, which a raw table has none of. The model is calc/typst_raw_table.py's, `current()` the body to write: a cell rewritten in its brackets alone, the table's arguments once its shape changed. A table out of the subset Woodcore edits is shown read only and never rewritten."""
    KINDS = ("table",)
    ALIGNS = ((None, "op_align_auto"), ("left", "op_align_left"), ("center", "op_align_center"), ("right", "op_align_right"))

    def subject_in(self, subject):
        from typst_objects import Object, model_for_body
        if isinstance(subject, str):
            body = subject
        elif isinstance(subject, Object):
            body = subject.written
        else:
            body = subject.to_body()
        self.model = model_for_body("table", body)

    def current(self):
        return None if self.model is None else self.model.to_body()

    def build(self, layout):
        super().build(layout)
        card = cards.card(self.t("op_col_align"))
        form = cards.form(card)
        self.align_box = QComboBox()
        for align, key in self.ALIGNS:
            self.align_box.addItem(self.t(key), align)
        self.align_box.currentIndexChanged.connect(self.align_chosen)
        form.addRow(QLabel(self.t("op_col_align")), self.align_box)
        layout.addWidget(card)

    def refresh(self):
        super().refresh()
        self.notes_edit.setVisible(False)
        self.header_check.setVisible(True)
        self.header_check.set(self.model.get("header"))
        self.caption_edit.setEnabled(self.model.caption_span is not None)

    def after_column_chosen(self):
        super().after_column_chosen()
        box = getattr(self, "align_box", None)
        if box is None:
            return
        column_id = self.column_id()
        align = self.model.column(column_id).align if column_id is not None else None
        was = box.blockSignals(True)
        box.setCurrentIndex(max(box.findData(align), 0))
        box.setEnabled(column_id is not None and not self.model.is_hidden(column_id))
        box.blockSignals(was)

    def align_chosen(self, _index):
        if self._loading or not self.ready():
            return
        column_id = self.column_id()
        if column_id is not None:
            self.do(self.model.set_align, column_id, self.align_box.currentData())
