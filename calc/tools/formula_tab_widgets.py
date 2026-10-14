"""The widgets of the «Formules» tab -- a block of a calculation (var, eq, verify …) with its fields, the text of the domain with its commands as pills, the keys and clicks that move from one to the next -- split out of calc/tools/formula_tab.py (issue #30). formula_tab.py imports every name back.

**The middle pane is one text since issue #40** (`FormulaText`): the engineer's own Typst, and each command validated a **pill** in it -- a small rectangle with rounded corners, its shown variable, its value and its unit (`PillPainter`, a `QTextObjectInterface` drawing the object character U+FFFC) --, inline in its sentence where Typst prints the command inline, a line of its own where it prints it apart (calc/domains/formula_layout.py). A pill is dragged elsewhere in the text, and a double-click opens it as its row of fields (`Block`), on a line of its own, the text parted around it (D-04).
"""

import html
from PySide6.QtCore import QByteArray, QEvent, QMimeData, QObject, QPointF, QRectF, QSizeF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QDrag, QPainter, QPen, QPyTextObject, QTextCharFormat, QTextCursor, QTextDocument, QTextFormat
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QGridLayout, QHeaderView, QLabel, QLineEdit, QPlainTextEdit, QPushButton,
                               QScrollArea, QSplitter, QTextEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)
import typst_objects
import units
from domains import formula_domain as fd
import richtext
import theme


# What the middle of a block is filled with, by command: (field, the key of its label, the key of its tooltip)
# A `var` starts with what the engineer sees, its shown variable, the computation variable following it (issue #40, REQ-005): made from it as it is typed, Tab going into it to write another by hand
FIELDS = {
    "var": (("symbol", "fm_f_symbol", "fm_f_symbol_tip"), ("key", "fm_f_key", "fm_f_key_tip"), ("value", "fm_f_value", ""), ("unit", "fm_f_unit", "")),
    "eq": (("symbol", "fm_f_symbol", "fm_f_symbol_tip"), ("formula", "fm_f_formula", "fm_f_formula_tip")),
    "verify": (("formula", "fm_f_relation", "fm_f_relation_tip"),),
    "val": (("key", "fm_f_what", ""),),
    "var-unit": (("key", "fm_f_what", ""), ("unit", "fm_f_unit", "")),
}


FORMULA_FIELDS = ("formula",)


def math(source):
    """A symbol or a formula, Typst's math source, as the window's rich text sets it."""
    return richtext.math_html(source)


class _Keys(QObject):
    """Enter, Escape and the focus of a block's fields, told to the block -- a QLineEdit's own returnPressed knows nothing of Escape, and the focus is what says which formula a click on a variable writes into."""

    def __init__(self, block, parent):
        super().__init__(parent)     # the editor's content: the filter goes with the fields it watches, never outliving them
        self.block = block

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.block.validate()
                return True
            if event.key() == Qt.Key.Key_Escape:
                self.block.give_up()
                return True
        elif event.type() == QEvent.Type.FocusIn:
            self.block.focused.emit(obj)
        return False


class Block(QFrame):
    """One command of the domain: being written -- a row of labelled fields -- or validated -- what matters of it, set as mathematics, a double-click opening it again (UI-005)."""

    focused = Signal(object)        # a field of the block took the focus
    validated = Signal(object, object)   # (block, the command it is now)
    abandoned = Signal(object)
    chosen = Signal(object)         # the block's fields or its line clicked: its options on the right

    def __init__(self, tab, command, result=None, editing=False):
        super().__init__()
        self.tab = tab
        self.t = tab.t
        self.command = command
        self.result = result
        self.fresh = editing and not (command.key or command.formula)   # added and never validated: Escape takes it away
        self.fields = {}
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setProperty("formulaBlock", True)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.content = None
        self.editing = False
        if editing:
            self.editing = True     # its fields built once it is in the window (FormulaDomainsMixin.open_at): a Tab order holds between fields of one window only
        else:
            self.show_view()

    def clear(self):
        """A new content for the block, the old one taken away **whole** (issue #15, REQ-001): the editor's fields lie in a grid, a layout and not a widget, and taking only the layout's widgets out left the grid's fields behind, visible over the line validated -- the «ghost» of the block."""
        old = self.content
        if old is not None:
            old.hide()
            old.setParent(None)
            old.deleteLater()
        self.content = QWidget(self)
        self.layout_ = QVBoxLayout(self.content)
        self.layout_.setContentsMargins(8, 6, 8, 6)
        self.layout_.setSpacing(4)
        self.layout().addWidget(self.content)
        self.fields = {}

    # -- validated: the line that matters

    def show_view(self):
        self.clear()
        self.editing = False
        label = QLabel(self.view_html())
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setWordWrap(True)
        label.setToolTip(self.t("fm_double_click"))
        self.layout_.addWidget(label)

    def view_html(self):
        """What the pill of the command shows, on one line (issue #40, REQ-001): its shown variable, `=`, its value and its unit -- an equation's answer alone, its letters and numbers left to a double-click and to «Affichage» (D-01) --; a relation, its two values and ✔ or ✘; a command the domain refuses, its shown variable and the reason."""
        c, r = self.command, self.result or fd.Result()
        muted = theme.colour("muted")
        if r.error:
            head = math(c.shown_symbol) + " = " if c.defines else ""
            return f"{head}<span style='color:{theme.colour('danger')}'>{html.escape(r.error[:80])}</span>"
        if c.kind in ("var", "var-unit", "val", "eq"):
            line = f"{math(c.shown_symbol)} = {html.escape(units.shown(r.value, r.unit))}"
            if c.kind == "var" and c.source:
                line += f" <span style='color:{muted}'>· {html.escape(self.t('fm_imported', source=fd.describe_source(c)))}</span>"
            if c.kind == "eq" and r.warning:
                line += f" <span style='color:{theme.colour('danger')}'>({html.escape(r.warning['wanted'])} → {html.escape(r.warning['natural'])})</span>"
            return line
        if r.value is None:     # not computed yet
            return math(fd.display_formula(c.formula, []) if c.formula else c.kind)
        (lv, lu), (rv, ru) = r.value
        sign = {"<=": "≤", ">=": "≥", "<": "&lt;", ">": "&gt;", "=": "=", "!=": "≠"}[r.op]
        colour = theme.colour("ok" if r.holds else "danger")
        mark = "✔" if r.holds else "✘"
        return (f"{math(r.letters)} : {html.escape(units.shown(lv, lu))} {sign} {html.escape(units.shown(rv, ru))} "
                f"<span style='color:{colour}'>{mark}</span>")

    def mouseDoubleClickEvent(self, event):
        if not self.editing:
            self.show_editor()
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        self.chosen.emit(self)
        super().mousePressEvent(event)

    # -- being written: the fields

    def show_editor(self):
        self.clear()
        self.editing = True
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(6)
        keys = _Keys(self, self.content)
        c = self.command
        values = {
            # an equation has no field for its key: its name is shown even where the symbol is the key itself, which the model keeps empty (REQ-002)
            "key": c.key, "symbol": c.shown_symbol if c.kind in ("eq", "var") else c.symbol, "unit": c.unit,
            "value": "" if c.value is None else units.fmt_decimals(c.value, 9) if isinstance(c.value, (int, float)) else str(c.value),
            "formula": fd.display_formula(c.formula, self.tab.variables_before(self)) if c.formula else "",
        }
        if c.kind == "val" and c.key:
            values["key"] = dict(self.tab.variables_before(self)).get(c.key) or c.key
        title = QLabel(f"<b>{html.escape(c.kind)}</b>")
        grid.addWidget(title, 0, 0)
        column = 1
        previous = None
        for name, label_key, tip_key in FIELDS[c.kind]:
            if c.kind == "eq" and name == "formula":
                grid.addWidget(QLabel("="), 1, column)
                column += 1
            caption = QLabel(self.t(label_key))
            caption.setStyleSheet(f"color: {theme.colour('muted')};")
            field = QLineEdit(values.get(name, ""))
            field.setToolTip(self.t(tip_key) if tip_key else "")
            field.setProperty("formulaField", name)
            field.installEventFilter(keys)
            if name in FORMULA_FIELDS:
                field.setMinimumWidth(220)
                grid.setColumnStretch(column, 3)
            else:
                grid.setColumnStretch(column, 1)
            grid.addWidget(caption, 0, column)
            grid.addWidget(field, 1, column)
            self.fields[name] = field
            if previous is not None:
                QWidget.setTabOrder(previous, field)
            previous = field
            column += 1
        self.key_by_hand = False
        if c.kind == "var":
            # the computation variable follows the shown one until the engineer writes his own (REQ-005): a key that is not the one the symbol makes was written by hand
            self.key_by_hand = bool(c.key) and c.key != self.made_key(values["symbol"])
            self.fields["symbol"].textEdited.connect(self.symbol_typed)
            self.fields["key"].textEdited.connect(self.key_typed)
        remove = QPushButton("✕")
        remove.setToolTip(self.t("fm_delete_block"))
        remove.setFixedWidth(28)
        remove.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        remove.clicked.connect(lambda: self.tab.remove_block(self))
        grid.addWidget(remove, 1, column)
        self.layout_.addLayout(grid)
        self.error = QLabel("")
        self.error.setWordWrap(True)
        self.error.setStyleSheet(f"color: {theme.colour('danger')};")
        self.error.setVisible(False)
        self.layout_.addWidget(self.error)
        hint = QLabel(self.t("fm_keys"))
        hint.setStyleSheet(f"color: {theme.colour('muted')}; font-size: 8pt;")
        self.layout_.addWidget(hint)
        first = next(iter(self.fields.values()))
        QTimer.singleShot(0, first, first.setFocus)   # the field as context: a block validated before the timer fires takes the call with it
        self.chosen.emit(self)

    def made_key(self, symbol):
        """The key the shown variable makes (formula_domain.key_from_symbol), unique against the domain's other keys -- what `command_from` makes of an empty key."""
        taken = {b.command.defines for b in self.tab.blocks if b is not self and b.command.defines and b.command.kind != "var-unit"}
        return fd.key_from_symbol(symbol, taken) if symbol.strip() else ""

    def symbol_typed(self, text):
        if not self.key_by_hand:
            self.fields["key"].setText(self.made_key(text))

    def key_typed(self, text):
        self.key_by_hand = bool(text.strip())   # emptied, the key follows the shown variable again
        if not self.key_by_hand:
            self.fields["key"].setText(self.made_key(self.text("symbol")))

    def text(self, name):
        field = self.fields.get(name)
        return field.text().strip() if field is not None else ""

    def say(self, message):
        if self.editing:
            self.error.setText(message)
            self.error.setVisible(bool(message))

    def validate(self):
        try:
            command = self.tab.command_from(self)
        except fd.DomainError as exc:
            self.say(str(exc))
            return
        self.validated.emit(self, command)

    def give_up(self):
        if self.fresh:
            self.abandoned.emit(self)
        else:
            self.tab.give_up_block(self)    # its pill again, as it was, the text closing round it (D-04)


# The object a pill is: Qt's object character U+FFFC, of this object type, its block named by an integer in this property
PILL = int(QTextFormat.ObjectTypes.UserObject) + 40
PILL_UID = int(QTextFormat.Property.UserProperty) + 40
OBJECT = "\ufffc"
PILL_MIME = "application/x-woodcore-formula-pill"


class PillPainter(QPyTextObject):
    """Draws a command validated as a pill (issue #40, UI-001): its block's line (`Block.view_html`) set as rich text in a rectangle with rounded corners, the ground and the line the scheme's (`accent-soft`, `line-strong`; `danger-soft`, `danger` for a command refused), the line `accent` where it is the block chosen. Python keeps the handler alive: the text holds it (`FormulaText.painter`)."""

    PAD_X, PAD_Y, RADIUS = 6, 1, 6

    def __init__(self, text):
        super().__init__(text)
        self.text = text

    def document_of(self, block):
        doc = QTextDocument()
        doc.setDocumentMargin(0)
        doc.setDefaultFont(self.text.font())
        doc.setHtml(f"<span style='white-space:nowrap'>{block.view_html()}</span>")
        return doc

    def intrinsicSize(self, _doc, _pos, fmt):
        block = self.text.tab.pill_block(fmt.property(PILL_UID))
        if block is None:
            return QSizeF(8, self.text.fontMetrics().height())
        doc = self.document_of(block)
        return QSizeF(doc.idealWidth() + 2 * self.PAD_X, max(doc.size().height(), self.text.fontMetrics().height()) + 2 * self.PAD_Y)

    def drawObject(self, painter, rect, _doc, _pos, fmt):
        block = self.text.tab.pill_block(fmt.property(PILL_UID))
        if block is None:
            return
        refused = bool((block.result or fd.Result()).error)
        chosen = block is self.text.tab.chosen_block
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(theme.colour("danger-soft" if refused else "accent-soft")))
        painter.setPen(QPen(QColor(theme.colour("accent" if chosen else "danger" if refused else "line-strong")), 2 if chosen else 1))
        painter.drawRoundedRect(QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5), self.RADIUS, self.RADIUS)
        doc = self.document_of(block)
        painter.translate(rect.x() + self.PAD_X, rect.y() + (rect.height() - doc.size().height()) / 2)
        doc.drawContents(painter)
        painter.restore()


class FormulaText(QTextEdit):
    """The domain as a text (issue #40, ARCH-001): the engineer's own Typst -- coloured as Typst is (richtext.TypstHighlighter), printed as typed, never computed -- and each command validated a pill in it (`PillPainter`), the paragraphs calc/domains/formula_layout.py lays out. As high as what it holds: the middle pane scrolls, not the text. A click on a pill chooses it, a double-click opens it, a drag moves it -- a drop refused where formula_layout says why; Enter beside a pill is a new paragraph (D-05). What is copied or pasted is text alone: a pill is a command, never duplicated by a paste."""

    entered = Signal(object)
    left = Signal(object)
    edited = Signal(object)

    def __init__(self, tab, paragraphs=()):
        super().__init__()
        self.tab = tab
        self.press = None          # (uid, where) of a press on a pill, which a move far enough turns into a drag
        self.setAcceptRichText(False)
        self.setTabChangesFocus(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.setToolTip(tab.t("fm_text_tip"))
        self.setProperty("formulaText", True)
        self.painter = PillPainter(self)
        self.document().documentLayout().registerHandler(PILL, self.painter)
        self.highlighter = richtext.TypstHighlighter(self.document())
        self.set_paragraphs(paragraphs)
        self.document().contentsChanged.connect(self.fit)
        self.textChanged.connect(lambda: self.edited.emit(self))
        self.fit()

    # -- the content

    def set_paragraphs(self, paragraphs):
        """The text of `paragraphs` -- [[("text", str) | ("cmd", uid)]] --, its history of undoing emptied: a domain shown again is not undone into another."""
        self.blockSignals(True)
        doc = self.document()
        doc.setUndoRedoEnabled(False)
        doc.clear()
        cursor = QTextCursor(doc)
        for i, paragraph in enumerate(paragraphs):
            if i:
                cursor.insertBlock()
            for kind, value in paragraph:
                if kind == "text":
                    cursor.insertText(value, QTextCharFormat())
                else:
                    cursor.insertText(OBJECT, self.pill_format(value))
        doc.setUndoRedoEnabled(True)
        self.blockSignals(False)
        self.fit()

    @staticmethod
    def pill_format(uid):
        fmt = QTextCharFormat()
        fmt.setObjectType(PILL)
        fmt.setProperty(PILL_UID, int(uid))
        fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignMiddle)
        fmt.setToolTip("")
        return fmt

    def paragraphs(self):
        """The text as paragraphs, a pill by its uid: [[("text", str) | ("cmd", uid)]]. An empty text is no paragraph at all."""
        doc = self.document()
        if doc.isEmpty():
            return []
        out = []
        block = doc.begin()
        while block.isValid():
            runs = []
            it = block.begin()
            while not it.atEnd():
                fragment = it.fragment()
                text = fragment.text()
                fmt = fragment.charFormat()
                if fmt.objectType() == PILL:
                    runs.extend(("cmd", int(fmt.property(PILL_UID))) for _ch in text if _ch == OBJECT)
                else:
                    text = text.replace(OBJECT, "").replace("\u2028", " ")
                    if runs and runs[-1][0] == "text":
                        runs[-1] = ("text", runs[-1][1] + text)
                    elif text:
                        runs.append(("text", text))
                it += 1
            out.append(runs)
            block = block.next()
        return out

    def place_of(self, position):
        """(paragraph, run, character in the run) of a position of the text -- where formula_layout.drop_refusal reads a drop and a command added cuts the sentence --, the character None where the position is just before a pill, the run past the last at the paragraph's end."""
        block = self.document().findBlock(position)
        offset = position - block.position()
        paragraphs = self.paragraphs()
        runs = paragraphs[block.blockNumber()] if block.blockNumber() < len(paragraphs) else []
        at = 0
        for r, (kind, value) in enumerate(runs):
            if kind == "text":
                if offset <= at + len(value):
                    return (block.blockNumber(), r, offset - at)
                at += len(value)
            else:
                if offset == at:
                    return (block.blockNumber(), r, None)
                at += 1
        return (block.blockNumber(), len(runs), None)

    def pill_position(self, uid):
        """Where the pill of `uid` stands in the text, or None."""
        doc = self.document()
        for i in range(doc.characterCount()):
            if doc.characterAt(i) == OBJECT:
                cursor = QTextCursor(doc)
                cursor.setPosition(i + 1)
                fmt = cursor.charFormat()
                if fmt.objectType() == PILL and int(fmt.property(PILL_UID)) == uid:
                    return i
        return None

    def pill_at(self, point):
        """The uid of the pill under `point` (the viewport's coordinates), or None."""
        doc = self.document()
        position = doc.documentLayout().hitTest(QPointF(point), Qt.HitTestAccuracy.ExactHit)
        for i in (position, position - 1):
            if 0 <= i < doc.characterCount() and doc.characterAt(i) == OBJECT:
                cursor = QTextCursor(doc)
                cursor.setPosition(i + 1)
                fmt = cursor.charFormat()
                if fmt.objectType() != PILL:
                    continue
                left = self.cursorRect(self._cursor(i))
                right = self.cursorRect(self._cursor(i + 1))
                if left.top() == right.top() and left.x() <= point.x() <= right.x() and left.top() - 4 <= point.y() <= left.bottom() + 4:
                    return int(fmt.property(PILL_UID))
        return None

    def _cursor(self, position):
        cursor = QTextCursor(self.document())
        cursor.setPosition(position)
        return cursor

    def pill_rect(self, uid):
        """The rectangle of the pill of `uid` in the text's coordinates, or None."""
        i = self.pill_position(uid)
        if i is None:
            return None
        left, right = self.cursorRect(self._cursor(i)), self.cursorRect(self._cursor(i + 1))
        return left.united(right)

    def repaint_pills(self):
        """The pills drawn again -- a result changed, another block chosen --, their widths measured again."""
        doc = self.document()
        doc.markContentsDirty(0, doc.characterCount())
        self.viewport().update()
        self.fit()

    def fit(self):
        """As high as what it holds, one line at least: the gap reads as a gap while it is empty."""
        height = self.document().documentLayout().documentSize().height()
        line = self.fontMetrics().lineSpacing() + 2 * self.document().documentMargin()
        margins = self.contentsMargins()
        self.setFixedHeight(int(max(height, line) + margins.top() + margins.bottom() + 2))

    # -- the keys, the mouse, a drag

    def event(self, event):
        """A pill says how it is opened (UI-001, `fm_double_click`); the text, what it holds (`fm_text_tip`)."""
        if event.type() == QEvent.Type.ToolTip:
            point = self.viewport().mapFromGlobal(event.globalPos())
            self.setToolTip(self.tab.t("fm_double_click") if self.pill_at(point) is not None else self.tab.t("fm_text_tip"))
        return super().event(event)


    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.textCursor().insertBlock()   # a new paragraph, never Qt's line separator, which the file has no word for
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        uid = self.pill_at(event.position())
        self.press = (uid, event.position()) if uid is not None else None
        if uid is not None:
            self.tab.pill_clicked(self, uid)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.press is not None and event.buttons() & Qt.MouseButton.LeftButton:
            uid, start = self.press
            if (event.position() - start).manhattanLength() >= QApplication.startDragDistance() and self.tab.may_drag(self):
                self.press = None
                drag = QDrag(self)
                mime = QMimeData()
                mime.setData(PILL_MIME, QByteArray(str(uid).encode()))
                drag.setMimeData(mime)
                drag.exec(Qt.DropAction.MoveAction)
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.press is not None:
            self.press = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        uid = self.pill_at(event.position())
        if uid is not None:
            self.tab.pill_opened(self, uid)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def drop_position(self, point):
        return self.cursorForPosition(point.toPoint()).position()

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(PILL_MIME):
            event.acceptProposedAction()
        elif event.source() is self:
            event.ignore()      # a selection dragged inside the text would carry a pill away as text: moved by its own drag only
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(PILL_MIME):
            position = self.drop_position(event.position())
            if self.tab.drop_refusal(self, position) is None:
                self.setTextCursor(self._cursor(position))
                event.acceptProposedAction()
            else:
                event.ignore()
            return
        if event.source() is self:
            event.ignore()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat(PILL_MIME):
            uid = int(bytes(event.mimeData().data(PILL_MIME)).decode())
            event.acceptProposedAction()
            self.tab.pill_dropped(self, uid, self.drop_position(event.position()))
            return
        if event.source() is self:
            event.ignore()
            return
        super().dropEvent(event)

    def move_pill(self, uid, position):
        """The pill of `uid` taken from its place and set at `position` (the text's position before it was taken). Returns False where it is not in this text."""
        old = self.pill_position(uid)
        if old is None:
            return False
        cursor = self._cursor(old)
        cursor.beginEditBlock()
        cursor.setPosition(old + 1, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        cursor.setPosition(position - 1 if position > old else position)
        cursor.insertText(OBJECT, self.pill_format(uid))
        cursor.endEditBlock()
        return True

    def createMimeDataFromSelection(self):
        mime = QMimeData()
        mime.setText(self.textCursor().selectedText().replace(OBJECT, "").replace("\u2029", "\n").replace("\u2028", "\n"))
        return mime

    def insertFromMimeData(self, source):
        if source.hasText():
            self.textCursor().insertText(source.text().replace(OBJECT, ""), QTextCharFormat())

    # -- the focus

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.setPlaceholderText(self.tab.t("fm_text_placeholder"))
        self.entered.emit(self)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.setPlaceholderText("")
        self.left.emit(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit()


class _ClickOutside(QObject):
    """A press anywhere in the application, told to the tab, which validates a block being written when the press lands in the middle pane outside it (REQ-007, ARCH-RISK-110). Parented to the tab: Qt takes the filter away with it."""

    def __init__(self, tab):
        super().__init__(tab)
        self.tab = tab

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress and isinstance(obj, QWidget):
            self.tab.pressed_on(obj)
        return False
