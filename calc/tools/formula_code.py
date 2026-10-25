"""«Code» of the «Domaines» tab: the domain's `.typ` file itself, coloured, with its two margins (issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, UI-019, UI-012, REQ-007, REQ-012, ARCH-016, D-13).

The buffer is the source while «Code» is open (ARCH-016): it is read as the file would be (`formula_domain.parse_text`) once the typing pauses, and **written to the disk only where it reads** -- a parenthesis forgotten breaks the line until it is corrected, the state says where as Typst would (calc/domains/formula_errors.py), and the file of before stays as it was. The number of a line is red at a fault, orange at a warning; at its right the line's result, «= 4.238 kN/m», «✔ 9.967 ≤ 11.28 N/mm²», or its fault (calc/tools/code_editor.py, the margins the tab gives). **The command of the cursor** is recognised at once (`formula_args.command_at`) and fills the module «Arguments de la ligne»; a value set there replaces its line in the buffer by one edit, the cursor and the scroll staying.
"""

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

import richtext
from code_editor import CodeEditor

PAUSE_MS = 600


class CodeView(QWidget):
    """See the module's docstring. `cursorLine(int)` at every move of the cursor, `paused(str)` once the typing pauses."""

    cursorLine = Signal(int)
    paused = Signal(str)

    def __init__(self, tab):
        super().__init__()
        self.tab = tab
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        self.editor = CodeEditor(tab.app.mono_font)
        self.highlighter = richtext.TypstHighlighter(self.editor.document())
        column.addWidget(self.editor, 1)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(PAUSE_MS)
        self.timer.timeout.connect(lambda: self.paused.emit(self.editor.toPlainText()))
        self.editor.textChanged.connect(self._typed)
        self.editor.cursorPositionChanged.connect(lambda: self.cursorLine.emit(self.editor.current_line()))
        self.filling = False

    def _typed(self):
        if not self.filling:
            self.timer.start()

    def set_text(self, text):
        """The file's text in the buffer, where it differs -- the cursor kept on its line."""
        text = text or ""
        if self.editor.toPlainText() == text.replace("\r\n", "\n"):
            return
        line = self.editor.current_line()
        self.filling = True
        try:
            self.editor.setPlainText(text.replace("\r\n", "\n"))
        finally:
            self.filling = False
        block = self.editor.document().findBlockByNumber(max(0, line - 1))
        if block.isValid():
            cursor = self.editor.textCursor()
            cursor.setPosition(block.position())
            self.editor.setTextCursor(cursor)

    def text(self):
        return self.editor.toPlainText()

    def flush(self):
        """What is typed and not yet read, read now (another mode, another domain)."""
        if self.timer.isActive():
            self.timer.stop()
            self.paused.emit(self.editor.toPlainText())

    def replace_lines(self, first, last, text):
        self.filling = True
        try:
            return self.editor.replace_lines(first, last, text)
        finally:
            self.filling = False
