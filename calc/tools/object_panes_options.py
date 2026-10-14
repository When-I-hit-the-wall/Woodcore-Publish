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
    OverrideField,
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
    make_combo,
    parse_number,
    plain,
    show_number,
    variable_of,
)


class OptionsPane(Pane):
    """What a choice and a list to tick share: the card of the label, the list of options with Add / Remove / ↑ / ↓ and the text of the one chosen."""

    def build(self, layout):
        t = self.t
        card = cards.card(t(self.CARD))
        self.label_form = cards.form()
        box = QVBoxLayout(card)
        box.addLayout(self.label_form)
        self.label_edit = self.line_edit(self.label_edited)
        self.label_form.addRow(QLabel(t(self.LABEL)), self.label_edit)
        self.label_rows(self.label_form)
        layout.addWidget(card)

        card = cards.card(t("op_options"))
        box = QVBoxLayout(card)
        self.option_list = self.make_list(5)
        self.option_list.itemChanged.connect(self.on_option_checked)
        self.option_list.currentRowChanged.connect(self.on_option_chosen)
        self.option_list.setToolTip(t(self.CHECK_TIP))
        box.addWidget(self.option_list)
        self.opt_add, self.opt_remove, self.opt_up, self.opt_down, bar = self.list_buttons(self.add_option, self.remove_option, lambda: self.move_option(-1), lambda: self.move_option(1))
        box.addLayout(bar)
        form = cards.form()
        self.option_edit = self.line_edit(self.option_label_edited)
        form.addRow(QLabel(t("op_opt_label")), self.option_edit)
        self.option_rows(form)
        box.addLayout(form)
        layout.addWidget(card)
        self.extra_cards(layout)

    def label_rows(self, form):
        """Rows under the label."""

    def option_rows(self, form):
        """Rows under the chosen option's text."""

    def extra_cards(self, layout):
        """Cards under the options'."""

    def refresh(self):
        self.set_edit(self.label_edit, self.model.get("label"), self.t("op_expr"))
        self.refresh_options(select=self.option_list.currentRow() if self.option_list.count() else 0)
        self.refresh_extra()

    def refresh_extra(self):
        pass

    def option_id(self):
        item = self.option_list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item is not None else None

    def refresh_options(self, select=0):
        self._loading += 1
        try:
            self.option_list.clear()
            for option in self.model.options:
                item = QListWidgetItem(plain(option.get("label")) or option["id"])
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked if self.is_ticked(option) else Qt.CheckState.Unchecked)
                item.setData(Qt.ItemDataRole.UserRole, option["id"])
                self.option_list.addItem(item)
            if isinstance(select, str):
                select = next((i for i in range(self.option_list.count()) if self.option_list.item(i).data(Qt.ItemDataRole.UserRole) == select), 0)
            if self.option_list.count():
                self.option_list.setCurrentRow(max(0, min(select or 0, self.option_list.count() - 1)))
        finally:
            self._loading -= 1
        self.after_option_chosen()

    def sync_ticks(self):
        """The ticks set from the model where they stand -- the list is not rebuilt from inside its own signal."""
        self._loading += 1
        try:
            by_id = {o["id"]: o for o in self.model.options}
            for i in range(self.option_list.count()):
                item = self.option_list.item(i)
                option = by_id.get(item.data(Qt.ItemDataRole.UserRole))
                if option is not None:
                    item.setCheckState(Qt.CheckState.Checked if self.is_ticked(option) else Qt.CheckState.Unchecked)
        finally:
            self._loading -= 1

    def is_ticked(self, option):
        return False

    def after_option_chosen(self):
        options = self.model.options
        at = next((i for i, o in enumerate(options) if o["id"] == self.option_id()), None)
        self.opt_remove.setEnabled(at is not None)
        self.opt_up.setEnabled(at is not None and at > 0)
        self.opt_down.setEnabled(at is not None and at < len(options) - 1)
        self.set_edit(self.option_edit, options[at].get("label") if at is not None else None, self.t("op_expr"))
        if at is None:
            self.option_edit.setEnabled(False)
        self.after_option_shown(options[at] if at is not None else None)

    def after_option_shown(self, option):
        pass

    def on_option_chosen(self, _row):
        if self._loading or not self.ready():
            return
        self.after_option_chosen()

    def on_option_checked(self, item):
        pass

    def label_edited(self, typed):
        self.do(self.model.set_label, typed if typed.strip() else None, immediate=False)

    def option_label_edited(self, typed):
        option_id = self.option_id()
        if option_id is None:
            return
        ok, _ = self.do(self.model.set_option_label, option_id, typed, immediate=False)
        if ok:
            item = self.option_list.currentItem()
            was = self.option_list.blockSignals(True)
            item.setText(typed or option_id)
            self.option_list.blockSignals(was)

    def new_option_id(self):
        taken = set(self.model.option_ids())
        n = 1
        while f"o{n}" in taken:
            n += 1
        return f"o{n}", n

    def add_option(self):
        option_id, n = self.new_option_id()
        ok, _ = self.do(self.model.add_option, option_id, self.t("op_opt_new", n=n))
        if ok:
            self.refresh_options(select=option_id)
            self.refresh_extra()

    def remove_option(self):
        option_id = self.option_id()
        if option_id is None:
            return
        at = self.option_list.currentRow()
        ok, _ = self.do(self.model.remove_option, option_id)
        if ok:
            self.refresh_options(select=at)
            self.refresh_extra()

    def move_option(self, delta):
        option_id = self.option_id()
        at = self.option_list.currentRow()
        if option_id is None or not _between(range(self.option_list.count()), at + delta):
            return
        ok, _ = self.do(self.model.move_option, option_id, at + delta)
        if ok:
            self.refresh_options(select=option_id)


class ChoicePane(OptionsPane):
    """One choice among several (`doc-choice`): the question, whether the answer alone is printed, the options -- the one ticked is the answer, only one -- and an answer of the engineer's own where none fits."""
    KINDS = ("doc-choice",)
    CARD = "op_choice"
    LABEL = "op_question"
    CHECK_TIP = "op_selected_tip"

    def label_rows(self, form):
        self.only_check = Switch(self.t("op_only_selected"))
        self.only_check.toggled.connect(lambda on: self.do(self.model.set_only_selected, bool(on)))
        form.addRow(self.only_check)

    def extra_cards(self, layout):
        card = cards.card(self.t("op_other"))
        box = QVBoxLayout(card)
        box.addWidget(cards.note(self.t("op_other_tip")))
        self.other_edit = self.line_edit(self.other_edited)
        box.addWidget(self.other_edit)
        layout.addWidget(card)

    def is_ticked(self, option):
        return option["id"] == self.model.selected

    def refresh_extra(self):
        self.set_edit(self.other_edit, self.model.other, self.t("op_expr"))
        self.only_check.set(self.model.only_selected)

    def on_option_checked(self, item):
        if self._loading or not self.ready():
            return
        option_id = item.data(Qt.ItemDataRole.UserRole)
        ticked = item.checkState() == Qt.CheckState.Checked
        self.do(self.model.select, option_id if ticked else None)
        self.sync_ticks()
        self.refresh_extra()

    def other_edited(self, typed):
        ok, _ = self.do(self.model.set_other, typed if typed.strip() else None, immediate=False)
        if ok and typed.strip():
            self.sync_ticks()


class ChecklistPane(OptionsPane):
    """A list to tick (`doc-checklist`): the label, whether only the ticked options are printed, the options -- each ticked or not -- and the paragraph printed under the ticked one chosen."""
    KINDS = ("doc-checklist",)
    CARD = "op_checklist"
    LABEL = "op_label"
    CHECK_TIP = "op_check_tip"

    def label_rows(self, form):
        self.only_check = Switch(self.t("op_only_checked"))
        self.only_check.toggled.connect(lambda on: self.do(self.model.set_only_checked, bool(on)))
        form.addRow(self.only_check)

    def option_rows(self, form):
        self.text_edit = Text(3)
        self.text_edit.textChanged.connect(self.option_text_edited)
        form.addRow(QLabel(self.t("op_check_text")), self.text_edit)

    def is_ticked(self, option):
        return bool(option.get("checked", False))

    def refresh_extra(self):
        self.only_check.set(self.model.only_checked)

    def after_option_shown(self, option):
        was = self.text_edit.blockSignals(True)
        shown = plain(option.get("text")) if option is not None else None
        self.text_edit.setPlainText(shown or "")
        self.text_edit.setEnabled(option is not None and shown is not None)
        self.text_edit.blockSignals(was)

    def on_option_checked(self, item):
        if self._loading or not self.ready():
            return
        option_id = item.data(Qt.ItemDataRole.UserRole)
        ok, _ = self.do(self.model.set_checked, option_id, item.checkState() == Qt.CheckState.Checked)
        if not ok:
            self.sync_ticks()

    def option_text_edited(self):
        if self._loading:
            return
        option_id = self.option_id()
        if option_id is None:
            return
        typed = self.text_edit.toPlainText()
        self.do(self.model.set_option_text, option_id, typed if typed.strip() else None, immediate=False)


SIGNATURE_FIELDS = (("group", "op_sign_group"), ("role", "op_sign_role"), ("name", "op_sign_name"), ("place", "op_sign_place"), ("date", "op_sign_date"))


class SignaturesPane(Pane):
    """The signatures (`doc-signatures`): the list of signatories, the five fields of the one chosen -- group, role, name, place, date, each left empty to be written by hand -- and whether the place and the date are printed."""
    KINDS = ("doc-signatures",)

    def build(self, layout):
        t = self.t
        card = cards.card(t("op_signatures"))
        box = QVBoxLayout(card)
        self.row_list = self.make_list(5)
        self.row_list.currentRowChanged.connect(self.on_row_chosen)
        box.addWidget(self.row_list)
        self.row_add, self.row_remove, self.row_up, self.row_down, bar = self.list_buttons(self.add_row, self.remove_row, lambda: self.move_row(-1), lambda: self.move_row(1))
        box.addLayout(bar)
        layout.addWidget(card)

        card = cards.card(t("op_sign_fields"))
        form = cards.form(card)
        self.field_edits = {}
        for key, words in SIGNATURE_FIELDS:
            edit = self.line_edit(lambda typed, k=key: self.field_edited(k, typed))
            self.field_edits[key] = edit
            form.addRow(QLabel(t(words)), edit)
        self.fields_card = card
        layout.addWidget(card)

        card = cards.card(t("op_signatures"))
        box = QVBoxLayout(card)
        self.place_date_check = Switch(t("op_sign_place_date"))
        self.place_date_check.toggled.connect(lambda on: self.do(self.model.set_place_date, bool(on)))
        box.addWidget(self.place_date_check)
        layout.addWidget(card)

    def row_summary(self, index):
        row = self.model.rows[index]
        parts = [plain(row[key]) for key, _w in SIGNATURE_FIELDS if row.get(key) is not None and plain(row[key])]
        return f"{index + 1}. " + (" — ".join(parts) if parts else self.t("op_sign_empty"))

    def refresh(self):
        self.refresh_rows(select=self.row_list.currentRow() if self.row_list.count() else 0)
        self.place_date_check.set(self.model.place_date)

    def row_index(self):
        row = self.row_list.currentRow()
        return row if _between(range(len(self.model.rows)), row) else None

    def refresh_rows(self, select=0):
        self._loading += 1
        try:
            self.row_list.clear()
            for index in range(len(self.model.rows)):
                self.row_list.addItem(QListWidgetItem(self.row_summary(index)))
            if self.row_list.count():
                self.row_list.setCurrentRow(max(0, min(select, self.row_list.count() - 1)))
        finally:
            self._loading -= 1
        self.after_row_chosen()

    def after_row_chosen(self):
        row, count = self.row_index(), len(self.model.rows)
        self.row_remove.setEnabled(row is not None)
        self.row_up.setEnabled(row is not None and row > 0)
        self.row_down.setEnabled(row is not None and row < count - 1)
        entry = self.model.rows[row] if row is not None else {}
        for key, _words in SIGNATURE_FIELDS:
            edit = self.field_edits[key]
            self.set_edit(edit, entry.get(key), self.t("op_expr"))
            if row is None:
                edit.setEnabled(False)

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
        if at is None or not _between(range(len(self.model.rows)), at + delta):
            return
        ok, _ = self.do(self.model.move_row, at, at + delta)
        if ok:
            self.refresh_rows(select=at + delta)

    def field_edited(self, key, typed):
        row = self.row_index()
        if row is None:
            return
        ok, _ = self.do(self.model.set_field, row, key, typed if typed.strip() else None, immediate=False)
        if ok:
            item = self.row_list.item(row)
            if item is not None:
                item.setText(self.row_summary(row))


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


class FieldPane(Pane):
    """A labelled value of the document (`doc-field`): its label, its value -- a number or text, or a variable of the calculation -- and its unit."""
    KINDS = ("doc-field",)

    def build(self, layout):
        t = self.t
        card = cards.card(t("op_field"))
        form = cards.form(card)
        self.label_edit = self.line_edit(lambda typed: self.do(self.model.set_label, typed if typed.strip() else None, immediate=False))
        form.addRow(QLabel(t("op_label")), self.label_edit)
        self.value_field = CellField(self, None)
        self.value_field.edited.connect(self.value_edited)
        self.value_field.cleared.connect(lambda: self.do(self.model.set_value, None))
        form.addRow(QLabel(t("op_field_value")), self.value_field)
        self.unit_edit = self.line_edit(lambda typed: self.do(self.model.set_unit, typed if typed.strip() else None, immediate=False))
        form.addRow(QLabel(t("op_field_unit")), self.unit_edit)
        layout.addWidget(card)

    def refresh(self):
        self.set_edit(self.label_edit, self.model.get("label"), self.t("op_expr"))
        self.value_field.set_value(self.model.get("value"))
        self.set_edit(self.unit_edit, self.model.get("unit"))

    def value_edited(self, value):
        if isinstance(value, str):
            if not value.strip():
                value = None
            else:
                number = parse_number(value)
                value = number if number is not None else value
        self.do(self.model.set_value, value, immediate=not isinstance(value, str))
