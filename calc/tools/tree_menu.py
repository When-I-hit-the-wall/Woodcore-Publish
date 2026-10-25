"""A button that opens a tree of entries in a popup, each with a number, an entry at zero greyed (spec docs/requirements/completed/2026-10-24-onglet-variables-groupes.md, UI-002, ARCH-002).

The engineer's prototype: «Tous les onglets ▾», and under it the navigation of Woodcore -- groups, sections,
tabs --, all of it seen at once with the number of each entry. **A tree in a popup** (`Qt.Popup`, as the
notices' panel is) and not a QMenu of submenus, which hides the numbers behind a hover (ARCH-007 of the review);
placed under the button by `hover_bubble.place`, where it fits; Escape or a click elsewhere closes it.

⚠️ **A brick that knows nothing of variables** (ARCH-002): the caller gives the entries -- id, words, number,
depth, whether it can be chosen -- and hears the id chosen (`chosen`). It owns no word.
"""

from dataclasses import dataclass

from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QAbstractItemView, QFrame, QHeaderView, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout

from hover_bubble import place   # where a popup goes under its trigger (issue #115)

ID = Qt.ItemDataRole.UserRole


@dataclass
class Entry:
    """One entry: its id, its words, its number as shown («—» or "" for none), its depth (0 a root), whether it can be chosen, and its tooltip -- the reason where it cannot."""

    id: str
    text: str
    count: str = ""
    depth: int = 0
    enabled: bool = True
    tip: str = ""
    bold: bool = False


class TreePopup(QFrame):
    """The popup: a tree of every entry, open."""

    def __init__(self, owner):
        super().__init__(owner.window(), Qt.WindowType.Popup)
        self.owner = owner
        self.setObjectName("treeMenu")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        box = QVBoxLayout(self)
        box.setContentsMargins(4, 4, 4, 4)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(False)
        self.tree.setItemsExpandable(False)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.setFrameShape(QFrame.Shape.NoFrame)
        self.tree.setStyleSheet("QTreeView::branch { image: none; border-image: none; }")   # all of it open, always: no arrow to fold it
        header = self.tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.itemClicked.connect(self._clicked)
        self.tree.itemActivated.connect(self._clicked)
        box.addWidget(self.tree)

    def _clicked(self, item, _column=0):
        if item is None or not (item.flags() & Qt.ItemFlag.ItemIsEnabled):
            return
        self.hide()
        self.owner.chosen.emit(item.data(0, ID))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            event.accept()
            return
        super().keyPressEvent(event)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.owner.closed.emit()


class TreeMenu(QPushButton):
    """The button, its text what is chosen with «▾» after it, and its popup."""

    chosen = Signal(str)
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.popup = TreePopup(self)
        self.entries = []
        self.current = None
        self.clicked.connect(self.open)

    def set_label(self, text):
        self.setText(f"{text}  ▾")

    def set_entries(self, entries, current=None):
        """The entries, in order, each under the last entry of a depth one less: a tree all open."""
        self.entries = list(entries)
        self.current = current
        tree = self.popup.tree
        tree.clear()
        parents = []
        for entry in self.entries:
            parents = parents[:entry.depth]
            parent = parents[-1] if parents else None
            item = QTreeWidgetItem(parent if parent is not None else tree, [entry.text, entry.count])
            item.setData(0, ID, entry.id)
            item.setTextAlignment(1, int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter))
            item.setToolTip(0, entry.tip or entry.text)
            item.setToolTip(1, entry.tip or entry.text)
            if entry.bold:
                font = item.font(0)
                font.setBold(True)
                item.setFont(0, font)
            if not entry.enabled:
                item.setFlags(Qt.ItemFlag.NoItemFlags)   # greyed, and never chosen
            parents.append(item)
            if entry.id == current:
                tree.setCurrentItem(item)
        tree.expandAll()

    def item(self, entry_id):
        """The tree's row of `entry_id`, None where there is none."""
        tree = self.popup.tree
        for item in _items(tree):
            if item.data(0, ID) == entry_id:
                return item
        return None

    def choose(self, entry_id):
        """`entry_id` chosen as a click would choose it: nothing where it is greyed or absent."""
        item = self.item(entry_id)
        if item is not None:
            self.popup._clicked(item)

    def open(self):
        """The popup under the button, as wide as its content needs, as high as the screen allows (hover_bubble.place)."""
        popup = self.popup
        tree = popup.tree
        rows = sum(1 for _ in _items(tree))
        height = min(rows * (tree.sizeHintForRow(0) if rows else 20) + 12, 2000)
        width = max(self.width(), tree.sizeHintForColumn(0) + tree.sizeHintForColumn(1) + 48)
        trigger = QRect(self.mapToGlobal(QPoint(0, 0)), self.size())
        screen = (self.screen() or QGuiApplication.primaryScreen()).availableGeometry()
        rect, _scrolls = place(trigger, QSize(width, height), screen)
        popup.setGeometry(rect)
        popup.show()
        tree.setFocus()

    def is_open(self):
        return self.popup.isVisible()


def _items(tree):
    out = []

    def walk(item):
        out.append(item)
        for i in range(item.childCount()):
            walk(item.child(i))
    for i in range(tree.topLevelItemCount()):
        walk(tree.topLevelItem(i))
    return out
