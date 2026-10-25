"""A text editor with two margins: the line numbers on the left, coloured by what a provider says of each line, and a note at the right of each line (issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, UI-019, ARCH-016).

Generic: it knows no domain. The «Domaines» tab's «Code» (calc/tools/formula_code.py) gives it its margins -- a line's number red at a fault, orange at a warning; «= 4.238 kN/m» or «✔ 9.967 ≤ 11.28 N/mm²» at the right of a line that computes, a fault's words at its line -- and colours its text with richtext.TypstHighlighter. Everything drawn comes from `margins(line)`, a callable (line from 1) -> (theme token of the number or None, the note or ""); `replace_lines` writes a range of lines in **one** edit of the buffer, the cursor and the scroll staying where they were (an argument set from the module beside it).
"""

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QTextCursor, QTextFormat
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget

import theme

NOTE_GAP = 24      # between the end of a line's text and its note
NOTE_MIN = 120     # the least room left for the notes: a line longer than the editor less this has its note at the editor's right edge


class _Gutter(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.gutter_width(), 0)

    def paintEvent(self, event):
        self.editor.paint_gutter(event)


class CodeEditor(QPlainTextEdit):
    """See the module's docstring. `margins(line)` -> (token, note); `refresh_margins()` after the provider changed."""

    hovered = Signal(int)   # the line under the pointer, from 1 -- 0 where it left

    def __init__(self, font=None, parent=None):
        super().__init__(parent)
        self.margins = lambda _line: (None, "")
        self.setMouseTracking(True)
        self._hovered = 0
        self.lit_lines = {}
        if font is not None:
            self.setFont(font)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.gutter = _Gutter(self)
        self.blockCountChanged.connect(lambda _n: self._fit_gutter())
        self.updateRequest.connect(self._update_gutter)
        self._fit_gutter()

    # -- the left margin --

    def gutter_width(self):
        digits = max(2, len(str(max(1, self.blockCount()))))
        return 12 + self.fontMetrics().horizontalAdvance("9") * digits

    def _fit_gutter(self):
        self.setViewportMargins(self.gutter_width(), 0, 0, 0)

    def _update_gutter(self, rect, dy):
        if dy:
            self.gutter.scroll(0, dy)
        else:
            self.gutter.update(0, rect.y(), self.gutter.width(), rect.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        r = self.contentsRect()
        self.gutter.setGeometry(QRect(r.left(), r.top(), self.gutter_width(), r.height()))

    def paint_gutter(self, event):
        painter = QPainter(self.gutter)
        painter.fillRect(event.rect(), QColor(theme.colour("card")))
        block = self.firstVisibleBlock()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        height = self.fontMetrics().height()
        while block.isValid() and top <= event.rect().bottom():
            number = block.blockNumber() + 1
            token, _note = self.margins(number)
            font = QFont(self.font())
            font.setBold(token is not None)
            painter.setFont(font)
            painter.setPen(QColor(theme.colour(token) if token else theme.colour("muted")))
            painter.drawText(0, top, self.gutter.width() - 6, height, Qt.AlignmentFlag.AlignRight, str(number))
            block = block.next()
            top += round(self.blockBoundingRect(block).height()) if block.isValid() else height

    # -- the right margin: each line's note --

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        metrics = self.fontMetrics()
        block = self.firstVisibleBlock()
        offset = self.contentOffset()
        width = self.viewport().width()
        while block.isValid():
            geometry = self.blockBoundingGeometry(block).translated(offset)
            if geometry.top() > event.rect().bottom():
                break
            token, note = self.margins(block.blockNumber() + 1)
            if note:
                x = max(metrics.horizontalAdvance(block.text()) + NOTE_GAP + int(offset.x()), width - max(NOTE_MIN, metrics.horizontalAdvance(note) + 8))
                painter.fillRect(QRect(x - 4, int(geometry.top()), max(0, width - x + 4), int(geometry.height())), QColor(theme.colour("card")))   # over a line longer than the room: the note stays legible
                painter.setPen(QColor(theme.colour(token) if token else theme.colour("muted")))
                painter.drawText(QRect(x, int(geometry.top()), max(0, width - x - 4), int(geometry.height())), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, note)
            block = block.next()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        line = self.cursorForPosition(event.position().toPoint()).blockNumber() + 1
        if line != self._hovered:
            self._hovered = line
            self.hovered.emit(line)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._hovered = 0
        self.hovered.emit(0)

    def light_lines(self, grounds):
        """{line (from 1): colour}: those lines' grounds, the others' as they are -- the linked hovers (UI-018)."""
        selections = []
        for line, colour in grounds.items():
            block = self.document().findBlockByNumber(line - 1)
            if not block.isValid():
                continue
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor(colour))
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = QTextCursor(block)
            selections.append(selection)
        self.setExtraSelections(selections)
        self.lit_lines = dict(grounds)

    def refresh_margins(self):
        self.gutter.update()
        self.viewport().update()

    # -- what the module beside it writes --

    def current_line(self):
        """The line of the cursor, from 1."""
        return self.textCursor().blockNumber() + 1

    def select_line(self, line):
        """Line `line` (from 1) selected, scrolled to -- what a message of the state leads to (UI-015)."""
        block = self.document().findBlockByNumber(max(0, line - 1))
        if not block.isValid():
            return
        cursor = QTextCursor(block)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        self.setTextCursor(cursor)
        self.centerCursor()

    def replace_lines(self, first, last, text):
        """Lines `first` to `last` (from 1) replaced by `text` in one edit -- one step of the editor's own undo --, the cursor and the scroll kept (ARCH-016)."""
        doc = self.document()
        start, end = doc.findBlockByNumber(first - 1), doc.findBlockByNumber(last - 1)
        if not start.isValid() or not end.isValid():
            return False
        keep = self.textCursor()
        anchor, position = keep.anchor(), keep.position()
        bar = self.verticalScrollBar().value(), self.horizontalScrollBar().value()
        cursor = QTextCursor(doc)
        cursor.beginEditBlock()
        cursor.setPosition(start.position())
        cursor.setPosition(end.position() + end.length() - 1, QTextCursor.MoveMode.KeepAnchor)
        cursor.insertText(text)
        cursor.endEditBlock()
        back = QTextCursor(doc)
        size = doc.characterCount() - 1
        back.setPosition(min(anchor, size))
        back.setPosition(min(position, size), QTextCursor.MoveMode.KeepAnchor)
        self.setTextCursor(back)
        self.verticalScrollBar().setValue(bar[0])
        self.horizontalScrollBar().setValue(bar[1])
        return True
