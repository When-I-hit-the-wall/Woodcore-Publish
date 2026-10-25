"""The menu of a material of the library, a brick written once (spec docs/requirements/completed/2026-10-24-verifications-elements-v3.md, UI-005, ARCH-004, ARCH-RISK-009; issue #112).

A field «search» -- what the engineer types finds a material by its names in the three languages, its group and its source (domains/materials_search.py) -- above a list in groups: an entry at its head (the material the position gives, «suit T001»), then each group's title and its materials, each with what its caller says beside its name (the resistance the tab reads, a panel's values by loading) and its source; an entry that cannot be chosen (a material without resistance) is greyed. A click chooses (`chosen(id)`), the head's id being None. What the groups hold and what each line says are its caller's: a member check gives `member_check_material.offered`, a layer of the permanent loads may give its own (#111). No domain's word or rule here.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

import theme

ID_ROLE = Qt.ItemDataRole.UserRole
HEAD = "__head__"


class MaterialMenu(QWidget):
    """The menu -- see the module's docstring. `fill(query)` gives the list for what is typed: (head, [(title, [entry])]) -- `head` (text) or None, each entry {id, text, detail, source, selectable}."""

    chosen = Signal(object)   # the id chosen, None for the head (follow the position)

    def __init__(self, fill, placeholder, parent=None):
        super().__init__(parent)
        self.fill = fill
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 4, 0, 4)
        column.setSpacing(4)
        self.search = QLineEdit()
        self.search.setPlaceholderText(placeholder)
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh)
        column.addWidget(self.search)
        self.list = QListWidget()
        self.list.setMinimumHeight(220)
        self.list.itemClicked.connect(self._clicked)
        self.list.itemActivated.connect(self._clicked)
        column.addWidget(self.list)
        self.setObjectName("materialMenu")

    def refresh(self, *_ignored):
        """The list again for what the search field holds."""
        head, groups = self.fill(self.search.text())
        self.list.setCurrentItem(None)
        while self.list.count():
            self.list.takeItem(self.list.count() - 1)   # taken one by one and dropped by Python: a `clear()` under a list just shown crashed off-screen
        muted = QBrush(QColor(theme.colour("muted")))
        if head:
            item = QListWidgetItem(head)
            item.setData(ID_ROLE, HEAD)
            font = item.font()
            font.setItalic(True)
            item.setFont(font)
            self.list.addItem(item)
        for title, entries in groups:
            header = QListWidgetItem(title)
            header.setFlags(Qt.ItemFlag.NoItemFlags)
            font = header.font()
            font.setBold(True)
            header.setFont(font)
            self.list.addItem(header)
            for entry in entries:
                text = entry["text"] + ("    " + entry["detail"] if entry.get("detail") else "") + ("    · " + entry["source"] if entry.get("source") else "")
                item = QListWidgetItem("   " + text)
                item.setData(ID_ROLE, entry["id"])
                item.setToolTip(text)
                if not entry.get("selectable", True):
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                    item.setForeground(muted)
                self.list.addItem(item)

    def items(self):
        """[(text, id, selectable)] of the list -- what a test reads."""
        out = []
        for i in range(self.list.count()):
            item = self.list.item(i)
            out.append((item.text().strip(), item.data(ID_ROLE), bool(item.flags() & Qt.ItemFlag.ItemIsEnabled)))
        return out

    def choose(self, material_id):
        """The entry of `material_id` clicked (None: the head) -- what a test does."""
        for i in range(self.list.count()):
            item = self.list.item(i)
            if item.data(ID_ROLE) == (HEAD if material_id is None else material_id) and item.flags() & Qt.ItemFlag.ItemIsEnabled:
                self._clicked(item)
                return True
        return False

    def _clicked(self, item):
        mid = item.data(ID_ROLE)
        if mid is None or not item.flags() & Qt.ItemFlag.ItemIsEnabled:
            return
        self.chosen.emit(None if mid == HEAD else mid)
