"""The left pane of the commands tab: the search and the commands by category (spec 2026-10-24-onglet-commandes-pages, UI-002, REQ-009, REQ-011, ARCH-007).

The categories go by task, in build_reference.CATEGORIES' order -- the website's too --, each with the number of its commands; under each, a command's name in the fixed font and its lead on a second line, cut by «…» (command_page.lead); «Internes» last and folded. The search reads the name and the lead in the window's language, nothing else (command_page.matches). Choosing a row emits `chosen("cmd|name")` or `chosen("cat|key")`: the tab hands it to the page and the right-hand pane, which this component knows nothing of.
"""

import build_reference as ref
import command_docs as docs
import command_page as page_model
import theme
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFontMetrics, QKeySequence, QShortcut
from PySide6.QtWidgets import QLineEdit, QStyledItemDelegate, QStyle, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

CATEGORY_ORDER = [key for key, _names in ref.CATEGORIES] + [ref.INTERNAL]
LEAD_ROLE = Qt.ItemDataRole.UserRole + 1


class TwoLineDelegate(QStyledItemDelegate):
    """A command's row on two lines: its name in the fixed font, its lead in grey under it, cut by «…» to the row's width."""

    def __init__(self, mono, parent=None):
        super().__init__(parent)
        self.mono = mono

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        if index.data(LEAD_ROLE):
            return QSize(size.width(), QFontMetrics(self.mono).height() + option.fontMetrics.height() + 8)
        return size

    def paint(self, painter, option, index):
        lead = index.data(LEAD_ROLE)
        if not lead:
            return super().paint(painter, option, index)
        style = option.widget.style() if option.widget else None
        if style is not None:
            opt = type(option)(option)
            self.initStyleOption(opt, index)
            opt.text = ""
            style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, option.widget)
        rect = option.rect.adjusted(4, 3, -4, -3)
        painter.save()
        painter.setFont(self.mono)
        painter.setPen(QColor(theme.colour("ink")))
        top = QFontMetrics(self.mono).height()
        painter.drawText(rect.left(), rect.top(), rect.width(), top, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, index.data(Qt.ItemDataRole.DisplayRole))
        painter.setFont(option.font)
        painter.setPen(QColor(theme.colour("muted")))
        elided = option.fontMetrics.elidedText(lead, Qt.TextElideMode.ElideRight, rect.width())
        painter.drawText(rect.left(), rect.top() + top, rect.width(), rect.height() - top, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, elided)
        painter.restore()


class CommandList(QWidget):
    """The search and the tree. `chosen` carries the row's id; `copy_requested` the Return or Ctrl+C on a command's row."""

    chosen = Signal(str)
    copy_requested = Signal(str)

    def __init__(self, ctx, state=None):
        super().__init__()
        self.ctx = ctx
        state = state or {}
        self.open_rows = set(state.get("open") or [])
        self.remembered = state.get("selection")
        self.first_fill = not state
        self.nodes = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.search = QLineEdit(state.get("search") or "")
        self.search.setPlaceholderText(ctx.word("search"))
        self.search.setClearButtonEnabled(True)
        layout.addWidget(self.search)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(1)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.tree.setItemDelegate(TwoLineDelegate(ctx.app.mono_font, self.tree))
        self.tree.itemSelectionChanged.connect(self._selected)
        for key in (QKeySequence(QKeySequence.StandardKey.Copy), QKeySequence("Return")):
            shortcut = QShortcut(key, self.tree)
            shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
            shortcut.activated.connect(lambda: self.selected_iid() and self.copy_requested.emit(self.selected_iid()))
        layout.addWidget(self.tree, 1)
        self.search.textChanged.connect(lambda _text: self.refill())

    def shown(self):
        pass

    def hidden(self):
        pass

    def refill(self):
        needle = self.search.text().strip()
        previously = self.current_open_rows()
        self.tree.blockSignals(True)
        self.tree.clear()
        self.nodes.clear()
        grey = QBrush(QColor(theme.colour("muted")))
        for key in CATEGORY_ORDER:
            group = [r for r in self.ctx.records if r["category"] == key and (key != ref.INTERNAL or not needle or needle.lower() in r["name"].lower())
                     and (key == ref.INTERNAL or page_model.matches(r, needle, self.ctx.lang))]
            if not group:
                continue
            label = docs.category_label(key, self.ctx.lang)
            parent = QTreeWidgetItem(self.tree, [f"{label}  ({len(group)})"])
            parent.setData(0, Qt.ItemDataRole.UserRole, f"cat|{key}")
            parent.setFont(0, self.ctx.app.bold_font)
            parent.setToolTip(0, docs.category_lead(key, self.ctx.lang) if key != ref.INTERNAL else self.ctx.t("ref_internal_note"))
            if key == ref.INTERNAL:
                parent.setForeground(0, grey)
            self.nodes[f"cat|{key}"] = parent
            if key == ref.INTERNAL:
                order = sorted(group, key=lambda r: r["name"])
            else:
                names = dict(ref.CATEGORIES)[key]
                order = sorted(group, key=lambda r: names.index(r["name"]))
            for record in order:
                node = QTreeWidgetItem(parent, [record["name"]])
                node.setData(0, Qt.ItemDataRole.UserRole, f"cmd|{record['name']}")
                if key != ref.INTERNAL:
                    node.setData(0, LEAD_ROLE, page_model.lead(record, self.ctx.lang))
                    node.setToolTip(0, page_model.lead(record, self.ctx.lang))
                else:
                    node.setFont(0, self.ctx.app.mono_font)
                self.nodes[f"cmd|{record['name']}"] = node
        for iid, node in self.nodes.items():
            if not node.childCount():
                continue
            if iid == f"cat|{ref.INTERNAL}" and not needle:
                node.setExpanded(iid in previously)
            else:
                node.setExpanded(self.first_fill or bool(needle) or iid in previously)
        self.first_fill = False
        self.tree.blockSignals(False)
        target = self.nodes.get(self.remembered)
        if target is not None:
            self.tree.setCurrentItem(target)
        else:
            self._selected()

    def current_open_rows(self):
        live = {iid for iid, node in self.nodes.items() if node.childCount() and node.isExpanded()}
        hidden = {iid for iid in self.open_rows if iid not in self.nodes}
        self.open_rows = live | hidden
        return self.open_rows

    def selected_iid(self):
        items = self.tree.selectedItems()
        return items[0].data(0, Qt.ItemDataRole.UserRole) if items else None

    def select(self, iid):
        node = self.nodes.get(iid)
        if node is not None:
            self.tree.setCurrentItem(node)

    def _selected(self):
        self.remembered = self.selected_iid() or self.remembered
        self.chosen.emit(self.selected_iid() or "")

    def state(self):
        return {"search": self.search.text(), "open": sorted(self.current_open_rows()), "selection": self.selected_iid() or self.remembered}

    def restore(self, state):
        self.search.setText(state.get("search") or "")
        self.open_rows = set(state.get("open") or [])
        self.remembered = state.get("selection")
        self.refill()
