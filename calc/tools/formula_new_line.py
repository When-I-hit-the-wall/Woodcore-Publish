"""A new line of the «Domaines» tab's «Formulaire»: what is typed, the command it is inferred to be, and its fields (issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, UI-008, UI-010, REQ-001, D-4, D-11).

At the foot of the form, and where the + between two rows opens one: a line where «h = 240 mm», «M_d = q_d * l^2 / 8» or «sigma_(m,d) <= f_(m,d)» is typed. **On its left a pill** says what it infers -- «var auto», «eq auto», «verify auto» (calc/domains/formula_infer.py) --; a click opens auto · var · eq · verify · texte, and a choice fixes it, «auto» gone. **Under it the fields of the command**, filled from what is typed and changed by hand: var -- symbol, value, unit, label; eq -- symbol, calculation, unit, label; verify -- relation, label; text -- the text. **Enter** or ✓ writes the line, **Escape** or × gives it up. The pill and the fields are the same for the line the + opens, whose pill comes fixed on the command chosen.

Nothing is decided here: `infer_line` reads the text, the view writes the command (`FormView.commit_line`).
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QMenu, QToolButton, QVBoxLayout, QWidget

import theme
from domains import formula_infer
from formula_row import COMMAND_COLOURS, FormulaEdit

# The fields of a new line, by command, in order (UI-010)
FIELDS = {"var": ("symbol", "value", "unit", "label"), "eq": ("symbol", "formula", "unit", "label"), "verify": ("relation", "label"), "text": ("text",)}
WORDS = {"symbol": "fm_f_symbol", "value": "fm_f_value", "unit": "fm_f_unit", "label": "fm_f_label", "formula": "fm_f_formula", "relation": "fm_f_relation", "text": "fm_f_text"}
# What the line of the foot shows before anything is typed: a formula, the same in every language
PLACEHOLDER = "M_d = q_d * l^2 / 8"


class NewLine(QFrame):
    """See the module's docstring. `at` is the item it is written before (None: the end); `kind` a command fixed (the + chose it)."""

    committed = Signal(object)
    cancelled = Signal()

    def __init__(self, view, at=None, kind=None, foot=False):
        super().__init__()
        self.view, self.at, self.kind, self.foot = view, at, kind, foot
        self.overrides = {}
        self.setObjectName("newLine")
        self.setStyleSheet("#newLine { border: 1px dashed %s; border-radius: 4px; }" % theme.colour("line"))
        t = view.t
        column = QVBoxLayout(self)
        column.setContentsMargins(6, 4, 6, 4)
        row = QHBoxLayout()
        column.addLayout(row)
        plus = QLabel("+")
        plus.setStyleSheet("color: %s; font-weight: 600;" % theme.colour("accent"))
        row.addWidget(plus)
        self.pill = QToolButton()
        self.pill.setToolTip(t("fm_nl_pick"))
        self.pill.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.pill.setFont(view.tab.app.mono_font)
        menu = QMenu(self.pill)
        for choice in (None,) + formula_infer.KINDS:
            action = QAction(t("fm_nl_auto") if choice is None else (t("fm_kind_text") if choice == "text" else choice), menu)
            action.triggered.connect(lambda _c=False, k=choice: self.choose(k))
            menu.addAction(action)
        self.pill.setMenu(menu)
        row.addWidget(self.pill)
        self.text = FormulaEdit("")
        self.text.setPlaceholderText(PLACEHOLDER)
        self.text.textEdited.connect(lambda _t: self.refresh())
        self.text.returnPressed.connect(self.commit)
        self.text.focused.connect(lambda f: view.formula_focused(None, self.at, "new", f))
        view.attach_completion(self.text, self.at)
        row.addWidget(self.text, 1)
        ok = QToolButton()
        ok.setText("✓")
        ok.setToolTip(t("fm_nl_ok"))
        ok.clicked.connect(self.commit)
        row.addWidget(ok)
        no = QToolButton()
        no.setText("×")
        no.setToolTip(t("fm_nl_no"))
        no.clicked.connect(self.cancel)
        row.addWidget(no)
        self.no_button = no
        self.boxes = QWidget()
        self.boxes_row = QHBoxLayout(self.boxes)
        self.boxes_row.setContentsMargins(24, 0, 0, 0)
        column.addWidget(self.boxes)
        self.message = QLabel("")
        self.message.setStyleSheet("color: %s;" % theme.colour("danger"))
        self.message.setVisible(False)
        column.addWidget(self.message)
        if foot:
            hint = QLabel(t("fm_nl_hint"))
            hint.setWordWrap(True)
            hint.setStyleSheet("color: %s;" % theme.colour("muted"))
            column.addWidget(hint)
        self.fields = {}
        self.refresh()

    # --- what it infers ---------------------------------------------------------------------------

    def inferred(self):
        """The line as typed, its fields changed by hand over it; None where nothing is typed."""
        line = formula_infer.infer_line(self.text.text(), self.view.taken_keys(), self.kind)
        if line is None:
            return None
        for name, value in self.overrides.items():
            if name in FIELDS.get(line.kind, ()):
                line.fields[name] = value
        if line.kind in ("var", "eq") and "symbol" in self.overrides:
            line.fields["key"] = ""
        return line

    def shown_kind(self):
        line = self.inferred()
        return self.kind or (line.kind if line is not None else None)

    def pill_text(self):
        """«var auto», or «var» once chosen -- «…» before anything is typed."""
        kind = self.shown_kind()
        t = self.view.t
        name = (t("fm_kind_text") if kind == "text" else kind) if kind else "…"
        return name if self.kind else f"{name} {t('fm_nl_auto')}"

    def choose(self, kind):
        """A command chosen on the pill -- None for auto."""
        self.kind = kind
        self.refresh()

    def refresh(self):
        kind = self.shown_kind()
        self.pill.setText(self.pill_text() + " ▾")
        self.pill.setStyleSheet("QToolButton { color: %s; border: 1px %s %s; border-radius: 3px; padding: 0 6px; }"
                                % (theme.colour(COMMAND_COLOURS.get(kind or "text", "muted")), "solid" if self.kind else "dashed", theme.colour("line")))
        self.no_button.setVisible(not self.foot or bool(self.text.text()) or self.kind is not None)
        line = self.inferred()
        while self.boxes_row.count():
            item = self.boxes_row.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self.fields = {}
        if line is None or kind is None:
            self.boxes.setVisible(False)
            return
        self.boxes.setVisible(True)
        for name in FIELDS[kind]:
            label = QLabel(self.view.t(WORDS[name] if not (kind == "verify" and name == "relation") else "fm_f_relation"))
            label.setStyleSheet("color: %s;" % theme.colour("muted"))
            self.boxes_row.addWidget(label)
            field = QLineEdit(str(line.fields.get(name, "")))
            field.textEdited.connect(lambda text, n=name: self.overrides.__setitem__(n, text))
            field.returnPressed.connect(self.commit)
            self.fields[name] = field
            self.boxes_row.addWidget(field, 2 if name in ("formula", "relation", "text", "label") else 1)

    # --- written, or given up ---------------------------------------------------------------------

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.cancel()
            return
        super().keyPressEvent(event)

    def commit(self):
        line = self.inferred()
        if line is None:
            self.say(self.view.t("fm_nl_hint"))
            return
        self.committed.emit(line)

    def say(self, text):
        self.message.setText(text)
        self.message.setVisible(bool(text))

    def cancel(self):
        self.text.clear()
        self.overrides = {}
        if self.foot:
            self.kind = None
        self.say("")
        self.refresh()
        self.cancelled.emit()
