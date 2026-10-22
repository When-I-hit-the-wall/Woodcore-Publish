"""The editors of options, a choice, a checklist, signatures, a list of norms and a field in the right pane -- split out of calc/tools/object_panes.py (issue #30), moved verbatim. object_panes.py imports every name back.
"""

from PySide6.QtCore import QEvent, QSize, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFileDialog, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton, QSpinBox, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)
import cards  # the cards a pane is made of (cards.py)
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


SIGNATURE_FIELDS = (("group", "op_sign_group"), ("role", "op_sign_role"), ("name", "op_sign_name"), ("place", "op_sign_place"), ("date", "op_sign_date"))


class NormListPane(Pane):
    """The norms a section names (`show-norm-list`): a check list of the documents of the catalogue -- designation and title in the window's language -- and of the project's own `references.bib`, and under it the free lines of the engineer's own."""
    KINDS = ("show-norm-list",)

    def build(self, layout):
        t = self.t
        card = cards.card(t("op_norms"))
        box = QVBoxLayout(card)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setMinimumHeight(self.fontMetrics().lineSpacing() * 14)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tree.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.tree.itemChanged.connect(self.on_ticked)
        box.addWidget(self.tree)
        layout.addWidget(card)

        card = cards.card(t("op_lines"))
        box = QVBoxLayout(card)
        self.line_list = self.make_list(3)
        self.line_list.currentRowChanged.connect(self.on_line_chosen)
        box.addWidget(self.line_list)
        self.line_add, self.line_remove, self.line_up, self.line_down, bar = self.list_buttons(self.add_line, self.remove_line, lambda: self.move_line(-1), lambda: self.move_line(1))
        box.addLayout(bar)
        form = cards.form()
        self.line_edit_widget = self.line_edit(self.line_edited)
        form.addRow(QLabel(t("op_line_text")), self.line_edit_widget)
        box.addLayout(form)
        layout.addWidget(card)

    # -- reading

    def keys(self):
        return self.model.keys

    def free_lines(self):
        """[(index in the model's keys, text)] of the lines that are the engineer's own words."""
        return [(i, plain(k)) for i, k in enumerate(self.keys()) if not isinstance(k, str)]

    def named_keys(self):
        """The catalogue key each string key of the list names (None where it names none)."""
        return {k: self.context.norm_key(k) for k in self.keys() if isinstance(k, str)}

    def refresh(self):
        self.refresh_tree()
        self.refresh_lines(select=self.line_list.currentRow() if self.line_list.count() else 0)

    def refresh_tree(self):
        groups = self.context.norm_groups()
        named = self.named_keys()
        ticked = {key for key in named.values() if key}
        self._loading += 1
        try:
            self.tree.clear()
            total = 0
            for kind, words in (("norm", "op_norm_norm"), ("literature", "op_norm_literature"), ("bib", "op_norm_bib")):
                entries = groups.get(kind) or []
                if not entries:
                    continue
                head = QTreeWidgetItem([self.t(words)])
                head.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.tree.addTopLevelItem(head)
                for entry in entries:
                    child = QTreeWidgetItem([entry["label"]])
                    child.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable)
                    child.setCheckState(0, Qt.CheckState.Checked if entry["key"] in ticked else Qt.CheckState.Unchecked)
                    child.setData(0, Qt.ItemDataRole.UserRole, entry["key"])
                    if entry.get("tip"):
                        child.setToolTip(0, entry["tip"])
                    head.addChild(child)
                    total += 1
                head.setExpanded(True)
            unknown = [k for k, found in named.items() if found is None]
            if unknown:
                head = QTreeWidgetItem([self.t("op_norm_other")])
                head.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.tree.addTopLevelItem(head)
                for key in unknown:
                    child = QTreeWidgetItem([key])
                    child.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable)
                    child.setCheckState(0, Qt.CheckState.Checked)
                    child.setData(0, Qt.ItemDataRole.UserRole, key)
                    head.addChild(child)
                head.setExpanded(True)
                total += len(unknown)
            if not total:
                self.tree.addTopLevelItem(QTreeWidgetItem([self.t("op_norm_none")]))
        finally:
            self._loading -= 1

    def on_ticked(self, item, _column):
        if self._loading or not self.ready():
            return
        key = item.data(0, Qt.ItemDataRole.UserRole)
        if key is None:
            return
        if item.checkState(0) == Qt.CheckState.Checked:
            self.do(self.model.select, key, True)
        else:
            # every string of the list that names this entry -- its key or an alias -- goes
            for cited, found in list(self.named_keys().items()):
                if found == key or (found is None and cited == key):
                    self.do(self.model.remove_key, cited)
        self.sync_ticks()

    def sync_ticks(self):
        """The ticks set from the model where they stand: the tree is not rebuilt from inside its own signal."""
        ticked = {found for found in self.named_keys().values() if found}
        strings = {k for k in self.keys() if isinstance(k, str)}
        self._loading += 1
        try:
            for top in range(self.tree.topLevelItemCount()):
                head = self.tree.topLevelItem(top)
                for child_at in range(head.childCount()):
                    child = head.child(child_at)
                    key = child.data(0, Qt.ItemDataRole.UserRole)
                    on = key in ticked or key in strings
                    child.setCheckState(0, Qt.CheckState.Checked if on else Qt.CheckState.Unchecked)
        finally:
            self._loading -= 1

    # -- the free lines

    def line_row(self):
        row = self.line_list.currentRow()
        return row if _between(range(len(self.free_lines())), row) else None

    def refresh_lines(self, select=0):
        self._loading += 1
        try:
            self.line_list.clear()
            for _index, shown in self.free_lines():
                self.line_list.addItem(QListWidgetItem(shown if shown is not None else self.t("op_expr")))
            if self.line_list.count():
                self.line_list.setCurrentRow(max(0, min(select, self.line_list.count() - 1)))
        finally:
            self._loading -= 1
        self.after_line_chosen()

    def after_line_chosen(self):
        row, count = self.line_row(), len(self.free_lines())
        self.line_remove.setEnabled(row is not None)
        self.line_up.setEnabled(row is not None and row > 0)
        self.line_down.setEnabled(row is not None and row < count - 1)
        lines = self.free_lines()
        self.set_edit(self.line_edit_widget, lines[row][1] if row is not None else None, self.t("op_expr"))
        if row is None:
            self.line_edit_widget.setEnabled(False)
            was = self.line_edit_widget.blockSignals(True)
            self.line_edit_widget.setText("")
            self.line_edit_widget.blockSignals(was)

    def on_line_chosen(self, _row):
        if self._loading or not self.ready():
            return
        self.after_line_chosen()

    def add_line(self):
        ok, _ = self.do(self.model.add_text, self.t("op_line_new"))
        if ok:
            self.refresh_lines(select=len(self.free_lines()) - 1)

    def remove_line(self):
        row = self.line_row()
        if row is None:
            return
        ok, _ = self.do(self.model.remove, self.free_lines()[row][0])
        if ok:
            self.refresh_lines(select=row)

    def move_line(self, delta):
        row = self.line_row()
        lines = self.free_lines()
        if row is None or not _between(lines, row + delta):
            return
        ok, _ = self.do(self.model.move, lines[row][0], lines[row + delta][0])
        if ok:
            self.refresh_lines(select=row + delta)

    def line_edited(self, typed):
        row = self.line_row()
        if row is None:
            return
        index = self.free_lines()[row][0]
        # a line is edited by being replaced where it stands
        before = self.model.keys[index]
        ok, _ = self.do(self.model.remove, index, immediate=False)
        if not ok:
            return
        ok, _ = self.do(self.model.add_text, typed if typed.strip() else "", index, immediate=False)
        if not ok:
            self.model.add_text(before, index)
            return
        item = self.line_list.item(row)
        if item is not None:
            was = self.line_list.blockSignals(True)
            item.setText(typed)
            self.line_list.blockSignals(was)

