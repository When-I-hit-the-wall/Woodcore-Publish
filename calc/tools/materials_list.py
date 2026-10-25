"""The list of the «Matériaux» tab, a service of the type «Bibliothèque» (spec docs/requirements/active/2026-10-24-onglet-materiaux.md, UI-003, REQ-006, REQ-007, REQ-011; issue #110).

The search -- every word, in three languages, the category and the type too (`materials_search`, the domain's, shared with the permanent loads) --, the filters of the origin (all, Woodcore's, the engineer's) and of the type, the number found; then the eleven categories, folded but where a search or a filter is on or where the material selected lies, each with its number; a row a material: the icon of its type, its name in the window's language, the label of its source on the right -- a click on it shows the source in the right pane (`ctx.reveal`). Under it «+ Nouveau» (a choice of the type first, in three cards), «Dupliquer» and «Supprimer», the last for the engineer's own alone. Nothing here decides what a material is: it lists what the context holds and asks the context.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QButtonGroup, QDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem,
                               QVBoxLayout, QWidget)

import theme
from domains import materials_contract, materials_library, materials_search
from material_marks import tag_text, type_icon
from tab_host import Service

ID_ROLE = Qt.ItemDataRole.UserRole
class TypeChoice(QDialog):
    """«+ Nouveau»: the type of the material first, three cards (T27)."""

    def __init__(self, parent, t):
        super().__init__(parent)
        self.setWindowTitle(t("mat_type_ask"))
        self.chosen = None
        column = QVBoxLayout(self)
        column.addWidget(QLabel(t("mat_type_ask")))
        row = QHBoxLayout()
        self.cards = {}
        for kind in materials_contract.TYPES:
            card = QPushButton("%s\n%s" % (t("mat_type_" + kind), t("mat_type_hint_" + kind)))
            card.setIcon(type_icon(kind))
            card.setMinimumSize(180, 90)
            card.clicked.connect(lambda _c=False, k=kind: self._choose(k))
            row.addWidget(card)
            self.cards[kind] = card
        column.addLayout(row)

    def _choose(self, kind):
        self.chosen = kind
        self.accept()


class MaterialList(Service):
    """The list of the materials -- see the module's docstring."""

    NAME = "list"
    ZONE = "left"
    IN_VIEWS = ()

    def mount(self, ctx):
        super().mount(ctx)
        self.origin, self.kind, self.opened = "all", None, set()
        holder = QWidget()
        column = QVBoxLayout(holder)
        column.setContentsMargins(0, 0, 0, 0)
        self.query = QLineEdit()
        self.query.setPlaceholderText(self.t("mat_search"))
        self.query.setClearButtonEnabled(True)
        self.query.textChanged.connect(lambda _t: self.listed())
        column.addWidget(self.query)
        self.origin_buttons = self._chips(column, (("all", "mat_all"), ("woodcore", "mat_woodcore"), ("user", "mat_user")), self._origin, exclusive=True)
        self.origin_buttons["all"].blockSignals(True)
        self.origin_buttons["all"].setChecked(True)      # «Toutes» down from the start, the list not built yet
        self.origin_buttons["all"].blockSignals(False)
        self.kind_buttons = self._chips(column, tuple((k, "mat_type_" + k) for k in materials_contract.TYPES), self._kind, exclusive=False)
        self.count = QLabel("")
        self.count.setStyleSheet("color: %s;" % theme.colour("muted"))
        column.addWidget(self.count)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderHidden(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setStretchLastSection(False)
        self.tree.itemClicked.connect(self._clicked)
        self.tree.itemExpanded.connect(lambda item: self.opened.add(item.data(0, ID_ROLE)))
        self.tree.itemCollapsed.connect(lambda item: self.opened.discard(item.data(0, ID_ROLE)))
        column.addWidget(self.tree, 1)
        row = QHBoxLayout()
        self.new_button = QPushButton(self.t("mat_new"))
        self.new_button.clicked.connect(self.new_material)
        self.duplicate_button = QPushButton(self.t("mat_duplicate"))
        self.duplicate_button.clicked.connect(self.duplicate_material)
        self.delete_button = QPushButton(self.t("mat_delete"))
        self.delete_button.clicked.connect(lambda: self.ctx.delete_entry())
        for button in (self.new_button, self.duplicate_button, self.delete_button):
            row.addWidget(button)
        column.addLayout(row)
        return holder

    def _chips(self, column, items, slot, exclusive):
        row = QHBoxLayout()
        group = QButtonGroup(row)
        group.setExclusive(exclusive)
        buttons = {}
        for key, word in items:
            button = QPushButton(self.t(word))
            button.setCheckable(True)
            button.setFlat(True)
            if key in materials_contract.TYPES:
                button.setIcon(type_icon(key))
            button.toggled.connect(lambda on, k=key: slot(k, on))
            group.addButton(button)
            row.addWidget(button)
            buttons[key] = button
        row.addStretch(1)
        column.addLayout(row)
        self._group = group
        return buttons

    def _origin(self, key, on):
        if on:
            self.origin = key
            self.listed()

    def _kind(self, key, on):
        if on:
            for other, button in self.kind_buttons.items():
                if other != key and button.isChecked():
                    button.blockSignals(True)
                    button.setChecked(False)
                    button.blockSignals(False)
            self.kind = key
        elif self.kind == key:
            self.kind = None
        self.listed()

    # --- the phases -----------------------------------------------------------------

    def found(self):
        return materials_search.search(self.ctx.entries, self.query.text(), self.origin, self.kind)

    def listed(self):
        """The entries listed again, by category, under the search and the filters."""
        found = self.found()
        self.count.setText(self.t("mat_count", n=len(found)))
        filtering = bool(self.query.text().strip()) or self.kind is not None or self.origin == "user"
        self.tree.blockSignals(True)
        self.tree.clear()
        lang = self.app.lang
        for category, items in materials_search.by_category(found).items():
            head = QTreeWidgetItem([self.t("mat_cat_" + category), str(len(items))])
            head.setData(0, ID_ROLE, category)
            font = head.font(0)
            font.setBold(True)
            head.setFont(0, font)
            self.tree.addTopLevelItem(head)
            for m in items:
                row = QTreeWidgetItem([materials_contract.name(m, lang) or self.t("mat_unnamed"), tag_text(self.t, m)])
                row.setIcon(0, type_icon(m["type"]))
                row.setData(0, ID_ROLE, m["id"])
                row.setToolTip(1, self.t("mat_src_tip"))
                row.setForeground(1, theme.qcolor("ok" if m.get("origin") in ("sia265", "sia265-1", "sia261") else ("warning" if m.get("origin") == "ext" else "primary")))
                head.addChild(row)
                if m["id"] == self.ctx.current_id:
                    self.tree.setCurrentItem(row)
            head.setExpanded(filtering or category in self.opened or any(m["id"] == self.ctx.current_id for m in items))
        self.tree.blockSignals(False)
        self._buttons()

    def selected(self):
        """The material selected: its row made current, its category opened."""
        self.tree.blockSignals(True)
        for i in range(self.tree.topLevelItemCount()):
            head = self.tree.topLevelItem(i)
            for j in range(head.childCount()):
                row = head.child(j)
                if row.data(0, ID_ROLE) == self.ctx.current_id:
                    head.setExpanded(True)
                    self.tree.setCurrentItem(row)
        self.tree.blockSignals(False)
        self._buttons()

    def drafted(self):
        """The draft changed: its row says its name as typed."""
        current = self.tree.currentItem()
        if current is not None and current.data(0, ID_ROLE) == self.ctx.current_id and self.ctx.draft is not None:
            current.setText(0, materials_contract.name(self.ctx.draft, self.app.lang) or self.t("mat_unnamed"))

    def _buttons(self):
        has = self.ctx.draft is not None
        self.duplicate_button.setEnabled(has)
        self.delete_button.setEnabled(has and self.ctx.editable())
        self.delete_button.setToolTip("" if self.delete_button.isEnabled() else self.t("mat_delete_why"))
        self.new_button.setEnabled(not self.ctx.error)

    # --- what the engineer does ------------------------------------------------------

    def _clicked(self, item, column):
        entry_id = item.data(0, ID_ROLE)
        if item.parent() is None:
            return
        if column == 1:
            self.ctx.reveal("source", entry_id)     # the label of the source: the material, then its source in the right pane (T38)
        elif not self.ctx.select(entry_id):
            self.selected()

    def new_material(self, kind=None):
        """«+ Nouveau»: the type chosen in three cards, then a material of the engineer's own, selected, its name ready to be typed (T27)."""
        if kind is None:
            dialog = TypeChoice(self.ctx.tab, self.t)
            if not dialog.exec() or dialog.chosen is None:
                return False
            kind = dialog.chosen
        return self.ctx.start(materials_library.new(kind))

    def duplicate_material(self):
        """«Dupliquer», and «Dupliquer dans ma bibliothèque» on a shipped one: a material of the engineer's own of the same values (REQ-006)."""
        if self.ctx.draft is None:
            return False
        return self.ctx.start(materials_library.duplicate(self.ctx.draft))

    def state(self):
        return {"query": self.query.text(), "origin": self.origin, "kind": self.kind, "opened": sorted(self.opened)}

    def restore(self, state):
        self.opened = set(state.get("opened") or ())
        if state.get("origin") in self.origin_buttons:
            self.origin_buttons[state["origin"]].setChecked(True)
        if state.get("kind") in self.kind_buttons:
            self.kind_buttons[state["kind"]].setChecked(True)
        self.query.setText(state.get("query") or "")
