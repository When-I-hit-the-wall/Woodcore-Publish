"""A search bar that carries a filter as tags before the text typed (spec docs/requirements/completed/2026-10-24-onglet-variables-groupes.md, UI-004, ARCH-002).

The engineer's prototype: «Actions › Actions variables ×», «source : export ×», «Charge utile · A1 [export] ×»,
then what he types, which is searched **in** that filter. The × of a tag takes it off; ⌫ in an empty bar takes
off the last one.

⚠️ **A brick that knows nothing of variables** (ARCH-002): the caller gives the tags -- (kind, text) -- and their
words, and hears which kind was taken off (`removed`); the bar owns no word of its own, so another tab may take
it. Its look is the style sheet's (`tagbar`, `tag`, theme.py), its colours theme.json's.
"""

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QSizePolicy, QToolButton


class TagSearchBar(QFrame):
    """The bar: its tags, then `edit`, the QLineEdit the text is typed in -- what a caller reads and what the command palette fills (`search`)."""

    removed = Signal(str)       # the kind of the tag taken off, by its × or by ⌫ in an empty bar

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("tagbar", True)
        self.row = QHBoxLayout(self)
        self.row.setContentsMargins(4, 2, 4, 2)
        self.row.setSpacing(4)
        self.edit = QLineEdit()
        self.edit.setClearButtonEnabled(True)
        self.edit.installEventFilter(self)
        self.edit.setMinimumWidth(160)
        self.row.addWidget(self.edit, 1)
        self.tags = []          # [(kind, text, its widget)], in the order shown
        self.placeholders = ("", "")

    def set_placeholders(self, empty, filtered):
        """The bar's hint with no tag, and with tags («Chercher dans ce filtre…»)."""
        self.placeholders = (empty, filtered)
        self._hint()

    def _hint(self):
        self.edit.setPlaceholderText(self.placeholders[1] if self.tags else self.placeholders[0])

    def set_tags(self, tags, close_tip=""):
        """The tags [(kind, text)], in the order shown; `close_tip` the × button's tooltip, in the caller's words."""
        for _kind, _text, widget in self.tags:
            self.row.removeWidget(widget)
            widget.hide()
            widget.deleteLater()
        self.tags = []
        for index, (kind, text) in enumerate(tags):
            widget = QFrame()
            widget.setProperty("tag", True)
            widget.setObjectName(f"tag_{kind}")
            widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)   # as wide as its words: the text typed keeps the rest
            box = QHBoxLayout(widget)
            box.setContentsMargins(8, 0, 2, 0)
            box.setSpacing(2)
            label = QLabel(text)
            label.setTextFormat(Qt.TextFormat.PlainText)
            box.addWidget(label)
            close = QToolButton()
            close.setText("×")
            close.setToolTip(close_tip)
            close.setCursor(Qt.CursorShape.PointingHandCursor)
            close.clicked.connect(lambda _c=False, kind=kind: self.removed.emit(kind))
            box.addWidget(close)
            self.row.insertWidget(index, widget)
            self.tags.append((kind, text, widget))
        self._hint()

    def kinds(self):
        return [kind for kind, _text, _widget in self.tags]

    def texts(self):
        return [text for _kind, text, _widget in self.tags]

    def close_button(self, kind):
        """The × of the tag `kind` (a test clicks it)."""
        for k, _text, widget in self.tags:
            if k == kind:
                return widget.findChild(QToolButton)
        return None

    def eventFilter(self, obj, event):
        if obj is self.edit and event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Backspace \
                and not self.edit.text() and self.tags:
            self.removed.emit(self.tags[-1][0])
            return True
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        self.edit.setFocus()   # a click beside the tags is a click in the bar
        super().mousePressEvent(event)
