"""One row of the «Domaines» tab's «Formulaire»: a line of the domain's file as fields (issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, UI-005, UI-006, UI-007, UI-009, UI-011, UI-013, D-10, D-16).

A row is an item of the domain (calc/domains/formula_rows.py): the grip ⋮⋮ it is dragged by, its line in the file, the label of its command, then what the line is --

* `var`: its symbol as Typst sets it, `=`, its value, its unit, the ⓘ of its clause, its label; a variable linked from elsewhere its symbol, its value, «↗ Neige · SL» and the label its source gives (REQ-010);
* `eq`: its symbol, `=`, **the calculation typed with the symbols** (REQ-002), its unit (auto, or one of its dimension), `=`, its result, the ⓘ;
* `verify`: the relation in symbols, its two sides and ✔ or ✘;
* a text: the engineer's Typst, printed as written; a line of text that holds commands (D-16) its text pieces, each its own field, and its commands as small blocks that are not typed in -- a click chooses the command, whose fields and arguments open on the right.

**Chosen**, a row shows under it the computation variable (its key), the label, the norm, the clause (`norm-section:`) and the description (UI-006). **A × on its right** deletes it (UI-007). Its **stripe** on the left is red at a fault, orange at a warning, grey for a line that only inherits a fault above it, the colour of its state for a line of an unfolded check (UI-009, REQ-015), and its message is under it.

Nothing is computed here: the row shows what the view gives it -- the command, its result, its state -- and tells the view what is typed (`FormView`, calc/tools/formula_form.py), which writes. The fields are found again by (row, field) and never kept across a rebuild (UI-011, ARCH-RISK-008).
"""

import html

from PySide6.QtCore import QMimeData, QPoint, Qt, Signal
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QSizePolicy,
                               QToolButton, QVBoxLayout, QWidget)

import richtext
import theme
import units
from domains import formula_args, formula_defaults, formula_infer
from norm_bubble import InfoMark

MIME = "application/x-woodcore-form-rows"
COMMAND_COLOURS = {"var": "syn-call", "eq": "accent", "verify": "warning", "text": "muted"}


def math(source):
    """A symbol or a relation as Typst's mathematics, for a QLabel (richtext.math_html)."""
    return richtext.math_html(source) if source else ""


class FormulaEdit(QLineEdit):
    """A field of a calculation: it tells the view it has the cursor (UI-011), and keeps where its cursor was when it lost it."""

    focused = Signal(object)

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.kept = len(text)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.focused.emit(self)

    def focusOutEvent(self, event):
        self.kept = self.cursorPosition()
        super().focusOutEvent(event)


class TextEdit(QPlainTextEdit):
    """A text of the engineer's, as tall as its lines: written when it is left."""

    left = Signal()

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.document().contentsChanged.connect(self._fit)
        self._fit()

    def _fit(self):
        lines = max(1, self.document().blockCount())
        self.setFixedHeight(lines * self.fontMetrics().lineSpacing() + 10)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.left.emit()


class Grip(QLabel):
    """⋮⋮: what a row is dragged by (UI-013) -- never a key (D-10)."""

    def __init__(self, row):
        super().__init__("⋮⋮")
        self.row = row
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setStyleSheet("color: %s; padding: 0 2px;" % theme.colour("muted"))
        self._press = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press = event.position().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._press is None or (event.position().toPoint() - self._press).manhattanLength() < QApplication.startDragDistance():
            return
        self._press = None
        rows = self.row.view.dragged_rows(self.row)
        drag = QDrag(self)
        data = QMimeData()
        data.setData(MIME, ",".join(str(r) for r in rows).encode("ascii"))
        drag.setMimeData(data)
        drag.setPixmap(self.row.grab())
        drag.exec(Qt.DropAction.MoveAction)

    def mouseReleaseEvent(self, event):
        self._press = None
        super().mouseReleaseEvent(event)


class InsertBar(QFrame):
    """The + between two rows (UI-008): shown under the pointer, it offers var, eq, verify, texte, lier une variable."""

    def __init__(self, view, at):
        super().__init__()
        self.view, self.at = view, at
        self.setFixedHeight(10)
        row = QHBoxLayout(self)
        row.setContentsMargins(28, 0, 0, 0)
        self.button = QToolButton()
        self.button.setText("+")
        self.button.setAutoRaise(True)
        self.button.setFixedHeight(10)
        self.button.setToolTip(view.t("fm_row_add"))
        self.button.setStyleSheet("QToolButton { color: %s; font-weight: 600; border: none; padding: 0 4px; }" % theme.colour("accent"))
        self.button.clicked.connect(lambda: view.insert_menu(self))
        self.button.setVisible(False)
        row.addWidget(self.button)
        row.addStretch(1)

    def enterEvent(self, event):
        self.button.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.button.setVisible(False)
        super().leaveEvent(event)


class FormRow(QFrame):
    """One row -- see the module's docstring. `index` is its place among the rows, `row` its formula_rows.Row."""

    def __init__(self, view, index, row):
        super().__init__()
        self.view, self.index, self.row = view, index, row
        self.setObjectName("formRow")
        self.fields = {}         # (item index, field name) -> widget
        self.chosen = False
        self.grouped = False
        self.state = None        # error | warning | blocked | one of the unfolded check's
        self.lit = None          # self | uses | used
        self.setMouseTracking(True)
        column = QVBoxLayout(self)
        column.setContentsMargins(6, 3, 4, 3)
        column.setSpacing(2)
        self.line = QHBoxLayout()
        self.line.setSpacing(6)
        column.addLayout(self.line)
        self.message = QLabel("")
        self.message.setWordWrap(True)
        self.message.setVisible(False)
        self.message.setTextFormat(Qt.TextFormat.RichText)
        column.addWidget(self.message)
        self.detail = QWidget()
        self.detail_form = QFormLayout(self.detail)
        self.detail_form.setContentsMargins(60, 2, 4, 4)
        self.detail.setVisible(False)
        column.addWidget(self.detail)
        self.build()
        self.paint()

    # --- what it shows ---------------------------------------------------------------------------

    @property
    def domain(self):
        return self.view.domain

    def result(self, i):
        results = self.view.results
        return results[i] if i < len(results) else None

    def build(self):
        t = self.view.t
        line = self.line
        self.grip = Grip(self)
        self.grip.setToolTip(t("fm_row_grip"))
        line.addWidget(self.grip)
        number = QLabel(str(self.row.line))
        number.setMinimumWidth(22)
        number.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        number.setStyleSheet("color: %s;" % theme.colour("muted"))
        self.number = number
        line.addWidget(number)
        kind = self.row.kind
        badge = QLabel(t("fm_kind_text") if kind == "text" else kind)
        badge.setStyleSheet("color: %s; border: 1px solid %s; border-radius: 3px; padding: 0 4px;" % (theme.colour(COMMAND_COLOURS[kind]), theme.colour("line")))
        badge.setFont(self.view.tab.app.mono_font)
        self.badge = badge
        line.addWidget(badge)
        if kind == "text":
            self.build_text()
        else:
            i = self.row.first
            getattr(self, "build_" + kind)(i, self.domain.commands[i])
        delete = QToolButton()
        delete.setText("×")
        delete.setAutoRaise(True)
        delete.setToolTip(t("fm_row_delete"))
        delete.clicked.connect(lambda: self.view.delete_rows([self.index]))
        self.delete_button = delete
        line.addWidget(delete)

    def _label(self, text, rich=False, tip=""):
        label = QLabel(text)
        if rich:
            label.setTextFormat(Qt.TextFormat.RichText)
        if tip:
            label.setToolTip(tip)
        return label

    def _field(self, i, name, text, formula=False, width=None, placeholder=""):
        field = FormulaEdit(text) if formula else QLineEdit(text)
        if placeholder:
            field.setPlaceholderText(placeholder)
        if width:
            field.setMaximumWidth(width)
        field.editingFinished.connect(lambda: self.view.field_done(self, i, name, field.text()))
        tip = {"symbol": "fm_f_symbol_tip", "key": "fm_f_key_tip", "formula": "fm_f_relation_tip" if self.row.kind == "verify" else "fm_f_formula_tip"}.get(name)
        if tip:
            notes = []
            if name == "formula":
                for key in self.view.symbol_table(i).shadowed:
                    other = next((c for c in self.domain.commands if c.key == key), None)
                    notes.append(self.view.t("fm_shadowed", symbol=other.symbol if other is not None else key, var=key))
            field.setToolTip("\n".join([self.view.t(tip)] + notes))
        if formula:
            field.focused.connect(lambda f: self.view.formula_focused(self, i, name, f))
            self.view.attach_completion(field, i)
        self.fields[(i, name)] = field
        return field

    def _info(self, c):
        norm, section = c.options.get("norm"), c.options.get("norm-section")
        if not norm:
            return None
        found = self.view.excerpt_for(str(norm), str(section or ""))
        if found is None:
            return self._label(html.escape(f"{norm} {section or ''}".strip()), tip=self.view.t("fm_f_sect"))
        mark = InfoMark(f"{norm} {section}")
        self.view.attach_bubble(mark, found)
        return mark

    def build_var(self, i, c):
        r = self.result(i)
        symbol = c.symbol or (r.symbol if r is not None else "") or c.key
        self.symbol = self._label(math(symbol), rich=True)
        self.line.addWidget(self.symbol)
        self.line.addWidget(QLabel("="))
        if c.source and c.source[0] == "domain":
            self.value = self._label("")
            self.line.addWidget(self.value)
            origin = self.view.origin_text(r.origin if r is not None else None, c)
            self.line.addWidget(self._label(html.escape(origin)))
            self.line.addWidget(self._label(html.escape(r.label if r is not None else "")), 1)
            self.update_result()
            return
        self.line.addWidget(self._field(i, "value", "" if c.value is None or c.source else str(c.value), width=90))
        self.line.addWidget(self._field(i, "unit", c.unit, width=70, placeholder=self.view.t("fm_f_unit")))
        mark = self._info(c)
        if mark is not None:
            self.line.addWidget(mark)
        self.line.addWidget(self._field(i, "label", str(c.options.get("label") or ""), placeholder=self.view.t("fm_f_label")), 1)

    def build_eq(self, i, c):
        self.symbol = self._label(math(c.symbol or c.key), rich=True)
        self.line.addWidget(self.symbol)
        self.line.addWidget(QLabel("="))
        table = self.view.symbol_table(i)
        self.line.addWidget(self._field(i, "formula", formula_infer.to_symbols(c.formula, table), formula=True), 1)
        unit = QComboBox()
        unit.setToolTip(self.view.t("fm_f_unit"))
        self.unit_box = unit
        self.fill_units(i, c)
        unit.activated.connect(lambda _x: self.view.field_done(self, i, "unit", unit.currentData() or ""))
        self.fields[(i, "unit")] = unit
        self.line.addWidget(unit)
        self.line.addWidget(QLabel("="))
        self.value = self._label("")
        self.line.addWidget(self.value)
        mark = self._info(c)
        if mark is not None:
            self.line.addWidget(mark)
        self.update_result()

    def fill_units(self, i, c):
        unit = self.unit_box
        unit.blockSignals(True)
        unit.clear()
        unit.addItem(self.view.t("fm_a_auto"), "")
        for one in formula_args.units_of(self.result(i)):
            unit.addItem(one, one)
        if c.unit and unit.findData(c.unit) < 0:
            unit.addItem(c.unit, c.unit)
        unit.setCurrentIndex(max(0, unit.findData(c.unit)))
        unit.blockSignals(False)

    def build_verify(self, i, c):
        table = self.view.symbol_table(i)
        self.line.addWidget(self._field(i, "formula", formula_infer.to_symbols(c.formula, table), formula=True), 1)
        self.value = self._label("")
        self.line.addWidget(self.value)
        mark = self._info(c)
        if mark is not None:
            self.line.addWidget(mark)
        self.update_result()

    def build_text(self):
        commands = self.row.commands(self.domain)
        if not commands:
            c = self.domain.commands[self.row.first]
            if formula_defaults.find(self.domain) is not None and formula_defaults.find(self.domain).index == self.row.first and c.raw.strip().count("\n") == 0:
                note = self._label(html.escape(self.view.t("fm_row_defaults")))
                note.setStyleSheet("color: %s;" % theme.colour("muted"))
                self.line.addWidget(note)
                code = self._label(html.escape(c.raw.strip()))
                code.setStyleSheet("color: %s;" % theme.colour("syn-call"))
                code.setFont(self.view.tab.app.mono_font)
                self.line.addWidget(code, 1)
                return
            edit = TextEdit(c.raw.strip("\n"))
            edit.setToolTip(self.view.t("fm_text_tip"))
            edit.setPlaceholderText(self.view.t("fm_text_placeholder"))
            edit.left.connect(lambda: self.view.text_done(self, self.row.first, edit.toPlainText()))
            self.fields[(self.row.first, "text")] = edit
            self.line.addWidget(edit, 1)
            return
        # a line of text that holds its commands (D-16): each text a field, each command a block
        for i in self.row.items:
            c = self.domain.commands[i]
            if c.is_text:
                edit = QLineEdit(c.raw) if "\n" not in c.raw else TextEdit(c.raw)
                if isinstance(edit, QLineEdit):
                    edit.editingFinished.connect(lambda i=i, e=edit: self.view.text_done(self, i, e.text()))
                else:
                    edit.left.connect(lambda i=i, e=edit: self.view.text_done(self, i, e.toPlainText()))
                self.fields[(i, "text")] = edit
                self.line.addWidget(edit)
            else:
                block = QToolButton()
                block.setAutoRaise(False)
                block.setToolTip(self.view.t("fm_row_inline"))
                block.clicked.connect(lambda _c=False, i=i: self.view.choose_item(self, i))
                self.fields[(i, "block")] = block
                self.line.addWidget(block)
        self.line.addStretch(1)
        self.update_result()

    def update_result(self):
        """What the line computes, shown again -- in place, nothing rebuilt (ARCH-RISK-008)."""
        kind = self.row.kind
        if kind == "text":
            for i in self.row.items:
                block = self.fields.get((i, "block"))
                if block is not None:
                    c, r = self.domain.commands[i], self.result(i)
                    block.setText(self.view.plain_line(c, r))
            return
        i = self.row.first
        c, r = self.domain.commands[i], self.result(i)
        if r is None:
            return
        if kind == "verify":
            if r.error:
                self.value.setText('<span style="color:%s">✘</span>' % theme.colour("danger"))
            else:
                (lv, lu), (rv, ru) = r.value
                colour = theme.colour("ok" if r.holds else "warning")
                self.value.setText('%s %s %s <b style="color:%s">%s</b>' % (html.escape(units.shown(lv, lu)), html.escape(r.op), html.escape(units.shown(rv, ru)), colour, "✔" if r.holds else "✘"))
            self.value.setTextFormat(Qt.TextFormat.RichText)
        elif kind == "eq" or (kind == "var" and c.source and c.source[0] == "domain"):
            self.value.setText("<b>%s</b>" % html.escape(units.shown(r.value, r.unit)) if not r.error and r.value is not None else "—")
            self.value.setTextFormat(Qt.TextFormat.RichText)
            if kind == "eq" and hasattr(self, "unit_box"):
                self.fill_units(i, c)

    def set_state(self, state, message=""):
        self.state = state
        self.message.setText(message)
        self.message.setVisible(bool(message))
        if message:
            token = {"error": "danger", "warning": "warning"}.get(state, "muted")
            self.message.setStyleSheet("color: %s; padding-left: 60px;" % theme.colour(token))
        self.paint()

    def set_chosen(self, chosen):
        self.chosen = chosen
        if chosen and not self.detail_form.rowCount():
            self.fill_detail()
        self.detail.setVisible(chosen and self.row.kind != "text")
        self.paint()

    def fill_detail(self):
        """Under a row chosen (UI-006): the key, the label, the norm, the clause, the description -- and for a var its symbol."""
        if self.row.kind == "text":
            return
        t = self.view.t
        i = self.row.first
        c = self.domain.commands[i]
        rows = [("symbol", "fm_f_symbol"), ("key", "fm_f_key"), ("label", "fm_f_label"), ("norm", "fm_f_norm"), ("norm-section", "fm_f_sect"), ("descr", "fm_f_descr")]
        if c.kind == "verify":
            rows = rows[2:]
        if c.source and c.source[0] == "domain":
            rows = [r for r in rows if r[0] != "symbol"]
        for name, word in rows:
            if name == "label" and c.kind == "var" and (i, "label") in self.fields:
                continue
            field = self._field(i, name, formula_args.value_of(c, name))
            self.detail_form.addRow(t(word), field)

    def set_grouped(self, grouped):
        self.grouped = grouped
        self.paint()

    def set_lit(self, lit):
        if lit != self.lit:
            self.lit = lit
            self.paint()

    def paint(self):
        """The stripe of its state, the ground of the hover, the dashed frame of the group (UI-009, UI-013, UI-018) -- the colours theme.json's."""
        from domains import formula_state
        stripe = formula_state.COLOURS.get(self.state)
        ground = {"self": "lit", "uses": "link-uses", "used": "link-used"}.get(self.lit) or ("accent-soft" if self.chosen else None)
        border = "3px solid %s" % theme.colour(stripe) if stripe else "3px solid transparent"
        frame = "border: 1px dashed %s;" % theme.colour("link-uses-line") if self.grouped else "border: 1px solid transparent;"
        self.setStyleSheet("#formRow { %s border-left: %s; %s border-radius: 4px; }" % (frame, border, ("background: %s;" % theme.colour(ground)) if ground else ""))

    # --- what the pointer does -------------------------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.view.row_clicked(self, event.modifiers())
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self.view.row_hovered(self, True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.view.row_hovered(self, False)
        super().leaveEvent(event)

    def field(self, item, name):
        """The field `name` of item `item` as it is now -- what a click on a variable writes into (UI-011)."""
        return self.fields.get((item, name))
