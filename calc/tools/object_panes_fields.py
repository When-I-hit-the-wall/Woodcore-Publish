"""The fields an object editor is built of -- a text, a list, a switch, a value written over, a table cell -- and Pane, the base every editor of the right pane derives from: split out of calc/tools/object_panes.py (issue #30), moved verbatim. object_panes.py imports every name back.
"""

import re
from PySide6.QtCore import QEvent, QSize, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFileDialog, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton, QSpinBox, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)
import cards  # the cards a pane is made of (cards.py)
import richtext  # a symbol set as mathematics (richtext.py)
import theme  # the orange of a value written over
import typst_objects as objects  # the models the panes edit (calc/typst_objects.py)
from typst_objects import AUTO, Content, Expr, ModelError
from object_panes_words import ERROR_WORDS, NNBSP, REASON_WORDS, STRINGS, _DE, _EN, _FR, _french, text  # split out of this module (issue #30): every name it had is still importable from it
from object_panes_context import Category, ExcerptInfo, FirePlanInfo, LANGUAGES, PaneContext, PlanInfo, VariableChoice, VariableDialog, _BIB_ENTRY, _BIB_TITLE, bib_entries, fmt_value  # split out of this module (issue #30): every name it had is still importable from it


# How long a typed edit waits for the next before it is emitted: a paragraph typed is one write.
DEBOUNCE_MS = 400


_STRING = r'"((?:[^"\\]|\\.)*)"'


_VARIABLE = re.compile(r"^\s*#(?:doc-value|val)\(\s*" + _STRING + r"(?:\s*,\s*domain:\s*(?:" + _STRING + r"|\(\s*" + _STRING + r"\s*,\s*" + _STRING + r"\s*\)))?\s*\)\s*$")


def _unescape(raw):
    return re.sub(r"\\(.)", lambda m: {"n": "\n", "r": "\r", "t": "\t"}.get(m.group(1), m.group(1)), raw)


def variable_of(value):
    """The variable a cell holds -- `(name, domain)`, the domain None, a string or a pair -- where it is `variable_cell(...)`'s content, else None: what the pane shows as the variable it is and not as the call that writes it."""
    if not isinstance(value, Content):
        return None
    found = _VARIABLE.match(value.markup)
    if found is None:
        return None
    name, string, first, second = (None if g is None else _unescape(g) for g in found.groups())
    if string is not None:
        return name, string
    if first is not None:
        return name, (first, second)
    return name, None


def parse_number(typed):
    """The number a text is -- `3`, `1.5`, `1,5` -- or None."""
    shown = str(typed).strip().replace(",", ".")
    if not re.fullmatch(r"[+-]?(?:\d+(?:\.\d+)?|\.\d+)", shown):
        return None
    return float(shown) if "." in shown else int(shown)


def show_number(value):
    """A number as a field shows it: no trailing `.0`."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return repr(value) if isinstance(value, float) else str(value)


def plain(value):
    """What a text value of a model -- None, a string, Content, an Expr -- is shown as in a field: its markup as written. (`None` for an expression, which has no text.)"""
    if value is None:
        return ""
    if isinstance(value, Content):
        return value.markup
    if isinstance(value, str):
        return value
    if isinstance(value, Expr):
        return None
    return str(value)


def as_context(value):
    """A PaneContext: the one given, or one made of a dictionary of its arguments, or an empty one."""
    if isinstance(value, PaneContext):
        return value
    return PaneContext(**value) if isinstance(value, dict) else PaneContext()


def call_of(subject):
    """The `Call` a subject is: a model, a call, an object of a file, or the text of one call."""
    if isinstance(subject, objects.Model):
        return subject.to_call()
    if isinstance(subject, objects.Call):
        return subject
    if isinstance(subject, objects.Object):
        return subject.replacement()
    if isinstance(subject, str):
        return objects.parse_call(subject)
    raise TypeError(f"a pane shows a model, a call or an object -- got {subject!r}")


def _drop(widget):
    """A widget taken out of the screen without a window of its own flashing open, and deleted when Qt next has a turn: hidden, detached, then deleted (docs/ui/window.md §10quater, the rebuilt rows)."""
    widget.hide()
    widget.setParent(None)
    widget.deleteLater()


class Text(QPlainTextEdit):
    """A few lines of the document's own words: plain, in the window's font, wrapped to its width, Tab moving on to the next field. `lines` is its height; with `grow` it is **its least height and the box grows with the text** -- one line for a short cell, and as many as the text takes once it wraps or holds a line break, up to `max_lines`, from where it scrolls. The height is worked out again whenever the font or the style changes (the style sheet's font arrives when the widget is polished, after it was made) and when the box is shown."""

    def __init__(self, lines=2, parent=None, grow=False, max_lines=8):
        super().__init__(parent)
        self.setTabChangesFocus(True)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.min_lines, self.max_lines, self.grow = lines, max(lines, max_lines), grow
        self.shown_lines = lines
        if grow:
            # a box that grows with its text shows no scroll bar until it has stopped growing: one beside a single line would take a fifth of its width
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.document().documentLayout().documentSizeChanged.connect(self.fit)
            self.textChanged.connect(self.fit)
        self.fit()

    def height_for(self, lines):
        return int(self.fontMetrics().lineSpacing() * lines + 2 * self.document().documentMargin() + 2 * self.frameWidth() + 4)

    def text_lines(self):
        """The lines the text takes at the width it has: a plain text's layout counts one for each line it is wrapped to."""
        return max(1, int(self.document().size().height() + 0.999))

    def fit(self, *_args):
        """The height made to the text -- between `min_lines` and `max_lines` where the box grows, `min_lines` where it does not."""
        wanted = self.text_lines() if self.grow else self.min_lines
        lines = max(self.min_lines, min(self.max_lines, wanted))
        self.shown_lines = lines
        height = self.height_for(lines)
        if self.minimumHeight() != height or self.maximumHeight() != height:
            self.setFixedHeight(height)
        if self.grow:
            scrolls = Qt.ScrollBarPolicy.ScrollBarAsNeeded if wanted > self.max_lines else Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            if self.verticalScrollBarPolicy() != scrolls:
                self.setVerticalScrollBarPolicy(scrolls)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit()

    def showEvent(self, event):
        super().showEvent(event)
        self.fit()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QEvent.Type.FontChange, QEvent.Type.StyleChange):
            self.fit()


class ListBox(QListWidget):
    """A list that asks for the height of `rows` rows and no more -- Qt's own list asks for about twelve whatever it holds, which left a list of three lines in a card of white."""

    def __init__(self, rows=5, parent=None):
        super().__init__(parent)
        self.rows = rows
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def row_height(self):
        found = self.sizeHintForRow(0) if self.count() else -1
        return found if found > 0 else self.fontMetrics().lineSpacing() + 8

    def sizeHint(self):
        base = super().sizeHint()
        return QSize(base.width(), self.row_height() * self.rows + 2 * self.frameWidth() + 4)

    def minimumSizeHint(self):
        base = super().minimumSizeHint()
        return QSize(base.width(), min(self.sizeHint().height(), self.row_height() * 3 + 2 * self.frameWidth() + 4))


class Switch(QCheckBox):
    """A check box that says what it does to the object: set from the model without a signal, read by the pane."""

    def set(self, on):
        was = self.blockSignals(True)
        self.setChecked(bool(on))
        self.blockSignals(was)


class OverrideField(QWidget):
    """A value the norm gives and the engineer may write over: `[ 3 ] norme` while it follows the norm, `[ 3.5 ] [Reprendre]` in orange the moment it is written over -- b/h's rule of v0.75, «typing the very value the norm holds still writes it over», and «Reprendre» is the one way back."""
    overridden = Signal(object)
    reverted = Signal()

    def __init__(self, lang, parent=None):
        super().__init__(parent)
        self.lang = lang
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        self.edit = QLineEdit()
        self.edit.textEdited.connect(self.typed)
        self.edit.editingFinished.connect(self.finished)
        self.note = QLabel(text("op_norm_value", lang))
        self.note.setEnabled(False)
        self.back = QPushButton(text("op_override_back", lang))
        self.back.setToolTip(text("op_override_tip", lang))
        self.back.clicked.connect(self.revert)
        row.addWidget(self.edit, 1)
        row.addWidget(self.note)
        row.addWidget(self.back)
        self.auto = None
        self.stated = None
        self.set_state(None, None)

    def set_state(self, auto, stated, enabled=True):
        """`auto` the norm's value (None where it gives none), `stated` the engineer's own number or None."""
        self.auto, self.stated = auto, stated
        was = self.edit.blockSignals(True)
        shown = stated if stated is not None else auto
        self.edit.setText("" if shown is None else show_number(shown))
        self.edit.setPlaceholderText(text("op_project_specific", self.lang) if auto is None and stated is None else "")
        self.edit.blockSignals(was)
        written = stated is not None
        self.edit.setStyleSheet(f"color: {theme.colour('override')};" if written else "")
        self.edit.setEnabled(enabled)
        self.back.setVisible(written)
        self.note.setVisible(not written)

    def typed(self, shown):
        number = parse_number(shown)
        if number is None:
            return
        self.stated = number
        self.edit.setStyleSheet(f"color: {theme.colour('override')};")
        self.back.setVisible(True)
        self.note.setVisible(False)
        self.overridden.emit(number)

    def finished(self):
        """The field left: an emptied field goes back to the norm; a text that is no number is put back as it was."""
        shown = self.edit.text().strip()
        if not shown and self.stated is not None:
            self.revert()
        elif not shown or parse_number(shown) is None:
            self.set_state(self.auto, self.stated)

    def revert(self):
        self.set_state(self.auto, None)
        self.reverted.emit()


class CellField(QWidget):
    """One cell of the chosen row as the right pane edits it: the text as written; or, where it holds a variable of the calculation, that variable -- `g_k = 1.9 kN/m²`, never the call -- with the button that takes it out; or, where it was written as an expression, a line saying so. `edited` carries the text typed (a string) or, for a variable, its content; an emptied cell carries ''."""
    edited = Signal(object)
    cleared = Signal()

    def __init__(self, pane, value, lines=1, parent=None):
        super().__init__(parent)
        self.pane = pane
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        self.text = Text(lines, grow=True)
        self.text.textChanged.connect(self.typed)
        self.chip = QLabel()
        self.chip.setTextFormat(Qt.TextFormat.RichText)
        self.chip.setWordWrap(True)
        self.clear = QPushButton(pane.t("op_var_clear"))
        self.clear.clicked.connect(self.remove_variable)
        self.pick = QPushButton(pane.t("op_cell_var"))
        self.pick.setToolTip(pane.t("op_cell_var_tip"))
        self.pick.clicked.connect(self.choose)
        row.addWidget(self.text, 1)
        row.addWidget(self.chip, 1)
        row.addWidget(self.clear)
        row.addWidget(self.pick, 0, Qt.AlignmentFlag.AlignTop)
        self.variable = None
        self.set_value(value)

    def set_value(self, value):
        """The cell shown as `value` holds it -- without a signal."""
        self.variable = variable_of(value)
        was = self.text.blockSignals(True)
        if self.variable is not None:
            self.text.setPlainText("")
            self.chip.setText(self.chip_html(*self.variable))
        elif isinstance(value, Expr):
            self.text.setPlainText("")
            self.text.setPlaceholderText(self.pane.t("op_expr"))
        else:
            self.text.setPlainText(self.shown_text(value))
            self.text.setPlaceholderText("")
        self.text.blockSignals(was)
        self.expression = isinstance(value, Expr)
        in_variable = self.variable is not None
        self.text.setVisible(not in_variable)
        self.text.setEnabled(not self.expression)
        self.chip.setVisible(in_variable)
        self.clear.setVisible(in_variable)
        self.pick.setVisible(not in_variable and not self.expression)

    @staticmethod
    def shown_text(value):
        if value is None or value is AUTO:
            return ""
        if isinstance(value, bool):
            return str(value)
        if isinstance(value, (int, float)):
            return show_number(value)
        found = plain(value)
        return "" if found is None else found

    def chip_html(self, name, domain):
        """The variable a cell names: its symbol as mathematics and its value, else its name; the domain, quiet, after it."""
        info = self.pane.context.variable_info(name, domain)
        if info is not None:
            symbol = richtext.math_html(info.symbol) if info.symbol else richtext.escape(name)
            value = richtext.escape((info.value_text + " " + info.unit).strip())
            shown = f"{symbol} = {value}" if value else symbol
        else:
            shown = richtext.escape(name)
        where = VariableChoice(name, domain).domain_text
        return shown + (f' <span style="color: {theme.colour("muted")}">({richtext.escape(where)})</span>' if where else "")

    def typed(self):
        self.edited.emit(self.text.toPlainText())

    def choose(self):
        choice = self.pane.context.pick_variable(self)
        if choice is None:
            return
        value = choice.cell()
        self.set_value(value)
        self.edited.emit(value)

    def remove_variable(self):
        self.set_value("")
        self.cleared.emit()


class Pane(QWidget):
    """One object's editor, as a column of cards. See the module's docstring for the contract: `load`, `changed`, `flush`, `current`, `set_language`."""
    changed = Signal(object)
    KINDS = ()

    def __init__(self, context=None, parent=None):
        super().__init__(parent)
        theme.ensure()
        self.context = as_context(context)
        self.lang = self.context.lang
        self.init_state()
        self.model = None
        self.broken = False
        self._loading = 0
        self._dirty = False
        self.page = None
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(DEBOUNCE_MS)
        self.timer.timeout.connect(self.flush)
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(0, 0, 0, 0)
        self.root.setSpacing(10)
        self._notice_key = None
        self.notice = QLabel()
        self.notice.setProperty("callout", "warning")
        self.notice.setWordWrap(True)
        self.notice.setVisible(False)
        self.root.addWidget(self.notice)
        self.message = QLabel()
        self.message.setProperty("callout", "danger")
        self.message.setWordWrap(True)
        self.message.setVisible(False)
        self.root.addWidget(self.message)
        self.rebuild()

    def init_state(self):
        """What a pane holds besides its model, made before its first page is built."""

    # -- the words

    def t(self, key, **values):
        return text(key, self.lang, **values)

    def set_language(self, lang):
        """The pane's words in `lang` -- the window's language switched: the pane is built again over what it holds."""
        self.lang = lang if lang in LANGUAGES else "en"
        self.context.lang = self.lang
        self.show_notice()
        self.rebuild()

    # -- loading, and what is edited

    def load(self, subject, context=None):
        """Shows `subject`. What the previous one had pending is emitted first; loading says nothing."""
        self.flush()
        if context is not None:
            self.context = as_context(context)
            self.lang = self.context.lang
        self.say(None)
        self.broken = False
        self.warn(subject)
        try:
            self.subject_in(subject)
        except (ModelError, objects.ParseError, ValueError) as exc:
            self.model = None
            self.broken = True
            self.subject_failed = exc
        self.rebuild()

    def subject_in(self, subject):
        """Takes `subject` as the pane's model; a ModelError (or a ParseError) means the object is written in a form that cannot be edited here."""
        call = call_of(subject)
        if call.type not in self.KINDS:
            raise ModelError("wrong_type", f"{type(self).__name__} edits {', '.join(self.KINDS)} -- got {call.type!r}")
        self.model = objects.model_for(call.copy())

    def ready(self):
        return self.model is not None and not self.broken

    def rebuild(self):
        """The page of cards made again from what the pane holds. The old one is dropped hidden and deleted when Qt next has a turn -- a button that asked for the rebuild is on it."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        old, self.page = self.page, page
        if old is not None:
            _drop(old)
        self.root.addWidget(page)
        self._loading += 1
        try:
            if self.broken:
                card = cards.card(self.t("op_empty_title"))
                box = QVBoxLayout(card)
                box.addWidget(cards.note(self.t("op_not_editable")))
                layout.addWidget(card)
            elif self.ready() or not self.KINDS:
                self.build(layout)
                self.refresh()
            else:
                layout.addWidget(cards.note(self.t("op_empty")))
        finally:
            self._loading -= 1

    def build(self, layout):
        """The cards of the pane, added to `layout`."""

    def refresh(self):
        """Fills the widgets from the model, under `_loading`."""

    def reload_view(self):
        self._loading += 1
        try:
            self.refresh()
        finally:
            self._loading -= 1

    def warn(self, subject):
        """What the engineer is told before he edits an object of a file that Woodcore did not write in its own form: written by hand, it is rewritten in Woodcore's; unreadable, it is replaced (typst_objects.Object.state)."""
        state = getattr(subject, "state", None) if isinstance(subject, objects.Object) else None
        unreadable = "op_unreadable_markup" if getattr(subject, "markup", False) else "op_unreadable"
        self._notice_key = {"hand_edited": "op_hand_edited", "unreadable": unreadable}.get(state)
        self.show_notice()

    def show_notice(self):
        self.notice.setText(self.t(self._notice_key) if self._notice_key else "")
        self.notice.setVisible(bool(self._notice_key))

    def say(self, words):
        """The banner: a sentence, or nothing."""
        self.message.setText(words or "")
        self.message.setVisible(bool(words))

    def error_words(self, error):
        reason = (getattr(error, "values", None) or {}).get("reason")
        key = REASON_WORDS.get(reason) or ERROR_WORDS.get(getattr(error, "code", ""), "op_err_generic")
        return self.t(key)

    def do(self, action, *args, immediate=True, **kwargs):
        """One edit of the model, refused or made: `(True, result)`, or `(False, None)` after a sentence in the banner -- the model is left as it was. A button's edit is emitted at once, a typed one after the debounce."""
        if self._loading:
            return False, None
        try:
            result = action(*args, **kwargs)
        except ModelError as exc:
            self.say(self.error_words(exc))
            return False, None
        self.say(None)
        self.touch(immediate)
        return True, result

    def touch(self, immediate=True):
        self._dirty = True
        if immediate:
            self.flush()
        else:
            self.timer.start()

    def flush(self):
        """What is pending is emitted now."""
        self.timer.stop()
        if self._dirty:
            self._dirty = False
            if self.ready():
                self.changed.emit(self.current())

    def current(self):
        """A snapshot of what the pane holds: a model of its own that `to_call()` serialises -- None while nothing is loaded."""
        return None if self.model is None else objects.model_for(self.model.to_call().copy())

    # -- widgets the panes share

    def button(self, key, slot, tip_key=None, compact=False):
        button = QPushButton(self.t(key))
        if tip_key:
            button.setToolTip(self.t(tip_key))
        if compact:
            button.setProperty("compact", True)
        button.clicked.connect(lambda *_: slot())
        return button

    def list_buttons(self, add, remove, up, down, tip_add=None):
        """Add / Remove / ↑ / ↓ in a row: returns the four buttons and the row."""
        row = QHBoxLayout()
        row.setSpacing(6)
        buttons = (self.button("op_add", add, tip_add), self.button("op_remove", remove),
                   self.button("op_up", up, "op_up_tip", compact=True), self.button("op_down", down, "op_down_tip", compact=True))
        for one in buttons:
            row.addWidget(one)
        row.addStretch(1)
        return (*buttons, row)

    def make_list(self, rows=5):
        return ListBox(rows)

    def fresh(self, layout, attribute):
        """A new empty body widget in `layout` in place of the one `attribute` names -- dropped, not deleted on the spot: a button on it may be what asked."""
        old = getattr(self, attribute, None)
        if old is not None:
            _drop(old)
        body = QWidget()
        setattr(self, attribute, body)
        layout.addWidget(body)
        return body

    def line_edit(self, slot, placeholder=""):
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.textEdited.connect(lambda value: slot(value))
        return edit

    @staticmethod
    def set_edit(edit, value, expression_words=None):
        """A line edit shown as `value` -- None, a string, Content, an Expr -- without a signal; an expression makes it read only and says so."""
        found = plain(value)
        was = edit.blockSignals(True)
        edit.setText("" if found is None else found)
        edit.setPlaceholderText(expression_words if found is None else edit.placeholderText())
        edit.setEnabled(found is not None)
        edit.blockSignals(was)


def make_combo():
    """A drop-down that never asks for the width of its longest item -- the category «Park- und Verkehrsflächen für Fahrzeuge von 3.5 t bis 16 t» would set the width of the whole column."""
    combo = QComboBox()
    combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
    combo.setMinimumContentsLength(12)
    return combo


def _between(items, index):
    return 0 <= index < len(items)
