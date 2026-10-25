"""The card at the right of the «Variables» tab (spec docs/requirements/completed/2026-10-24-onglet-variables-groupes.md, UI-011, UI-012, REQ-008, REQ-009; docs/ui/tab-variables.md).

It shows what `variable_card` composed -- the head (symbol = **value** unit, the value framed for a result,
«Résultat du calcul»), the label, the path, «Ouvrir l'onglet … ↗», the box of a field being linked («… suivra
q_k de A1 · Importer», REQ-008), the command to copy and what to include before it, the fields, «Vient de», and
«Le même calcul ailleurs» with a button per other source -- and asks the tab for the rest through its signals:
open the tab, copy, go to a sibling, import («Ouvrir le classeur» went with the load workbooks, issue #109). It decides nothing: no call is spelled here
(variable_card does it), no tab is opened here (the window does it, `MainWindow.show_tab`).
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFormLayout, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

import cards
import richtext
import theme
import variables as model


def _label(text="", wrap=True, rich=False):
    label = QLabel(text)
    label.setWordWrap(wrap)
    label.setTextFormat(Qt.TextFormat.RichText if rich else Qt.TextFormat.PlainText)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return label


def result_style(result):
    """The value of a card's head: in a thin frame of the theme's accent, in the accent and in bold, where it is a result (UI-008, D-6); in bold otherwise."""
    if result:
        return f"QLabel {{ border: 1.5px solid {theme.colour('accent')}; border-radius: 4px; color: {theme.colour('accent-strong')}; font-weight: 700; padding: 0 4px; }}"
    return "QLabel { font-weight: 700; }"


class Head(QWidget):
    """The head of a card: symbol = value unit (the symbol as the report prints it), or a domain's case and source."""

    def __init__(self, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        self.text = _label(wrap=False, rich=True)
        self.value = _label(wrap=False)
        self.unit = _label(wrap=False)
        for label in (self.text, self.value, self.unit):
            font = label.font()
            font.setPointSizeF(font.pointSizeF() * 1.4)
            label.setFont(font)
            row.addWidget(label)
        row.addStretch(1)

    def set_variable(self, symbol, value, unit, result):
        self.text.setText(f"{richtext.math_html(symbol)} =")
        self.value.setText(model.fmt_value(value))
        self.value.setStyleSheet(result_style(result))
        self.value.setVisible(True)
        self.unit.setText(unit)
        self.unit.setVisible(bool(unit))

    def set_html(self, text):
        self.text.setText(text)
        self.value.setVisible(False)
        self.unit.setVisible(False)


class VariablesDetail(QWidget):
    """The right pane. `t` the window's words, `mono` the font of the calls."""

    open_tab = Signal()
    copy = Signal(str)
    go = Signal(object)          # a sibling's key, (origin, domain, name or None)
    import_ = Signal()

    def __init__(self, t, mono, parent=None):
        super().__init__(parent)
        self.t = t
        self.mono = mono
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.scroll, column = cards.column(hold=False)
        outer.addWidget(self.scroll)
        self.body = cards.card("")
        box = QVBoxLayout(self.body)
        box.setSpacing(8)
        self.hint = _label(t("vr_no_selection"))
        self.hint.setStyleSheet(f"color: {theme.colour('muted')};")
        box.addWidget(self.hint)

        self.head = Head()
        box.addWidget(self.head)
        self.result_tag = _label(t("vr_result"))
        self.result_tag.setStyleSheet(f"color: {theme.colour('accent-strong')}; font-weight: 600;")
        box.addWidget(self.result_tag)
        self.title = _label()
        self.title.setStyleSheet("font-weight: 600;")
        box.addWidget(self.title)
        self.path = _label()
        self.path.setStyleSheet(f"color: {theme.colour('muted')};")
        box.addWidget(self.path)

        self.open_button = QPushButton(t("vr_open_none"))
        self.open_button.clicked.connect(self.open_tab.emit)
        row = QHBoxLayout()
        row.addWidget(self.open_button)
        row.addStretch(1)
        box.addLayout(row)

        # the box of a field being linked (REQ-008): «<champ> de <vérification>», what it will follow or why it may not, «Importer»
        self.pick_box = QFrame()
        self.pick_box.setStyleSheet(f"QFrame {{ border: 1.5px solid {theme.colour('accent')}; background: {theme.colour('accent-soft')}; border-radius: 8px; }}"
                                    " QLabel { border: none; background: transparent; }")
        pick = QVBoxLayout(self.pick_box)
        pick.setContentsMargins(10, 8, 10, 8)
        self.pick_title = _label()
        self.pick_title.setStyleSheet("font-weight: 600;")
        pick.addWidget(self.pick_title)
        self.pick_text = _label(rich=True)
        pick.addWidget(self.pick_text)
        self.pick_import = QPushButton(t("vr_pick_import"))
        self.pick_import.clicked.connect(self.import_.emit)
        prow = QHBoxLayout()
        prow.addStretch(1)
        prow.addWidget(self.pick_import)
        pick.addLayout(prow)
        box.addWidget(self.pick_box)

        self.command_title = _label(t("vr_command"))
        self.command_title.setStyleSheet(f"color: {theme.colour('muted')}; font-weight: 600;")
        box.addWidget(self.command_title)
        self.command_row = QHBoxLayout()
        self.command_field = None
        self.copy_button = richtext.copy_button(t("vr_copy"), t("vr_copy_done"), lambda: self.copy.emit(self.command_field.text() if self.command_field else ""))
        self.command_row.addWidget(self.copy_button)
        box.addLayout(self.command_row)
        self.command_note = _label()
        self.command_note.setStyleSheet(f"color: {theme.colour('muted')};")
        box.addWidget(self.command_note)

        self.form = QFormLayout()
        self.form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.rows = {}
        for key in ("vr_key", "vr_description", "vr_citation", "vr_formula", "vr_choices", "vr_level", "vr_came_from", "vr_its_variables"):
            caption = _label(t(key), wrap=False)
            caption.setStyleSheet(f"color: {theme.colour('muted')};")
            cell = _label(rich=key in ("vr_choices",))
            if key in ("vr_key", "vr_formula"):
                cell.setFont(mono)
            self.form.addRow(caption, cell)
            self.rows[key] = (caption, cell)
        box.addLayout(self.form)
        self.untraced = cards.note(t("vr_untraced"))
        box.addWidget(self.untraced)

        self.same_title = _label(t("vr_same_elsewhere"))
        self.same_title.setStyleSheet(f"color: {theme.colour('muted')}; font-weight: 600;")
        box.addWidget(self.same_title)
        self.computed = _label()
        box.addWidget(self.computed)
        self.siblings_box = QVBoxLayout()
        self.siblings_box.setSpacing(4)
        box.addLayout(self.siblings_box)
        self.sibling_buttons = []
        column.addWidget(self.body)
        column.addStretch(1)
        self.show_none()

    # -- the parts --

    def _set_command(self, command, note_text):
        if self.command_field is not None:
            self.command_row.removeWidget(self.command_field)
            self.command_field.hide()   # out of the layout, and hidden at once: deleteLater waits for the event loop
            self.command_field.deleteLater()
            self.command_field = None
        shown = command is not None and bool(command.call)
        if shown:
            self.command_field = richtext.CodeField(command.call, self.mono)
            self.command_row.insertWidget(0, self.command_field, 1)
        self.copy_button.setVisible(shown)
        self.command_title.setVisible(shown or bool(note_text))
        self.command_note.setText(note_text)
        self.command_note.setVisible(bool(note_text))

    def _set_rows(self, values):
        for key, (caption, cell) in self.rows.items():
            text = values.get(key, "")
            cell.setText(text)
            caption.setVisible(bool(text))
            cell.setVisible(bool(text))

    def _set_siblings(self, computed_text, siblings):
        for button in self.sibling_buttons:
            self.siblings_box.removeWidget(button)
            button.hide()
            button.deleteLater()
        self.sibling_buttons = []
        for text, key, tip in siblings:
            button = QPushButton(text)
            button.setToolTip(tip)
            button.setStyleSheet("text-align: left; padding: 3px 8px;")
            button.clicked.connect(lambda _c=False, key=key: self.go.emit(key))
            self.siblings_box.addWidget(button)
            self.sibling_buttons.append(button)
        shown = bool(siblings)
        self.same_title.setVisible(shown)
        self.computed.setText(computed_text)
        self.computed.setVisible(shown and bool(computed_text))

    def set_open(self, text, enabled, tip):
        self.open_button.setText(text)
        self.open_button.setEnabled(enabled)
        self.open_button.setToolTip(tip)

    def set_pick(self, title, text, can_import):
        """The box of a field being linked, hidden where `title` is None."""
        self.pick_box.setVisible(title is not None)
        if title is not None:
            self.pick_title.setText(title)
            self.pick_text.setText(text)
            self.pick_import.setEnabled(can_import)
            self.pick_import.setToolTip("" if can_import else text)

    # -- what it shows --

    def show_none(self):
        for widget in (self.head, self.result_tag, self.title, self.path, self.open_button, self.pick_box, self.command_title, self.copy_button, self.command_note,
                       self.untraced, self.same_title, self.computed):
            widget.setVisible(False)
        self._set_command(None, "")
        self._set_rows({})
        self._set_siblings("", [])
        self.hint.setVisible(True)

    def show_variable(self, head, result, title, path, command, note_text, rows, untraced, computed_text, siblings):
        """A variable's card: `head` (symbol, value, unit), `rows` {caption key: text}, `siblings` [(text, key, tip)]."""
        self.hint.setVisible(False)
        self.head.set_variable(*head, result)
        self.head.setVisible(True)
        self.result_tag.setVisible(result)
        self.title.setText(title or "—")
        self.title.setVisible(True)
        self.path.setText(path)
        self.path.setVisible(True)
        self.open_button.setVisible(True)
        self.command_title.setText(self.t("vr_command"))
        self._set_command(command, note_text)
        self._set_rows(rows)
        self.untraced.setVisible(untraced)
        self._set_siblings(computed_text, siblings)

    def show_domain(self, head, title, path, command, note_text, counts, siblings):
        """A domain chosen alone (UI-012): its name and source, its path, the whole domain to copy, its variables and results -- no «Valeur», no «Désignation»."""
        self.hint.setVisible(False)
        self.head.set_html(head)
        self.head.setVisible(True)
        self.result_tag.setVisible(False)
        self.title.setText(title)
        self.title.setVisible(bool(title))
        self.path.setText(path)
        self.path.setVisible(True)
        self.open_button.setVisible(True)
        self.pick_box.setVisible(False)
        self.command_title.setText(self.t("vr_whole"))
        self._set_command(command, note_text)
        self._set_rows({"vr_its_variables": counts})
        self.untraced.setVisible(False)
        self._set_siblings("", siblings)
