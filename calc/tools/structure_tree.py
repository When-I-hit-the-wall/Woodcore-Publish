"""The tree of a document, as a widget (the «Structure du document» tab -- the engineer's rework of 01.10.2026, work package R2-D1: **chapters › sections › objects**, several of them chosen at once, and moved by drag and drop).

`StructureTree` shows what calc/structure.py's `tree` gives -- a list of `Node`s -- and **nothing else**: it reads no file, writes none and knows no document. What a tick means, what a drop means, what a tooltip says are the tab's; the widget draws the rows and says what the user did (`toggled`, `selectionIdsChanged`, `dropped`), so that it can be tried without a project.

**A row** is a node's title with an icon for what it is -- a chapter (a group), a section (a file) and, under a section that carries object tags, **each of its objects**: a heading, a paragraph, a table, a list to tick, a choice, the signatures, the norms … (`KIND_ICONS`) -- a `.typ` mark where the node is a file of its own **and the document is the report** (`typ_mark`: in a convention d'utilisation and a base de projet every section is a file, so the mark would stand on every row and say nothing; in the report it tells which headings open a file of their own, and the column is hidden where the mark is not shown), a link mark where that file is shared with another document -- **greyed where the engineer stopped sharing it** (`set_stopped`: the tab keeps the ids for the session) --, and a **sync mark** where the file or the object is shared and another document changed it (calc/sync.py). The objects of a file are flat under it, in the order of the file, **indented by their level** (`Node.level`: the heading's, a paragraph's one more than the heading it follows): drawn so by the delegate and not by the tree, which is what lets a drop between two of them mean «between these two», whatever their level.

**A file** and a **group** carry a box, ticked while the section is enabled -- a group being a chapter, which a disabled one switches off with everything under it. An object, and a heading inside a file that carries no tags, has none: it has no state of its own, its file's being its state (`Node.enabled`). A row that is not printed (`Node.active`) is greyed, its box keeping its own state; a row whose file has something wrong with it (`Node.problems`) is set in the warning colour and its tooltip says what.

**The sync colours** come from the tab's `sync` function (`set_nodes(…, sync=…)`, `set_sync`): a row where another document's copy changed is the override's **orange** (`incoming`), one where both changed the danger **red** (`conflict`), one the engineer chose to ignore the muted **grey** (`ignored`), one whose copy cannot be compared the warning colour (`problem`); `local` -- only this copy changed -- is no alarm and gets none. The mark column says it in a character as well, so that a colour is never all there is. **A row chosen keeps its colour** (`_Delegate`): the style sheet gives a selected item the ink of the scheme, which would turn an orange or red row dark at the very moment the engineer looks at it, so a selected row is painted by the delegate -- the selection's ground, then the row in its own ink.

**Selection** is extended -- Ctrl and Shift, as an explorer has it -- and `selectionIdsChanged` says the ids chosen, in document order, whenever they change by the user's hand. **Drag and drop** is Qt's own gesture and **never Qt's own move**: a drop emits `dropped(ids, target id, where)` -- `where` being `above`, `below`, `on` or `end` -- and is ignored, the tab asking the model to move what was dragged and filling the tree again with what the files then say.

**Expanding to a level** is by the level a node is printed at (`Node.level`, absolute): «to 2» shows every row of level 2 and leaves the rows of level 2 themselves closed. The tree is opened to level 2 the first time it is filled, and keeps what the engineer opened and selected when it is filled again.

**The whole document** is a row of its own at the top (`WHOLE_ID`, the words the tab gives as `whole_label`): choosing it chooses nothing else, so the page shows the document entire -- the engineer's request of 06.10.2026, «tout en haut de cette arborescence, pouvoir cliquer sur tout afficher». It is a sibling of the first chapter and not their parent, so nothing under it is indented one step further for one row; it carries no box, a document that is not printed making no sense; it is never dragged, and a drop above it is a drop above the first row. It is chosen whenever nothing else is.

**An object taken out of the document** (calc/removed_objects.py) is a row of kind `removed` at the place it stood among its file's objects: greyed and struck through, with no box, never dragged, and chosen like any other row -- what the right button offers on it is the tab's («Réintégrer dans le document»).

No colour is written here: the ink of a greyed row, of a warning and of a sync state are the scheme's (theme.py), read when the rows are built, and the window is built again when the scheme changes.
"""

from PySide6.QtCore import QItemSelectionModel, QSize, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QHeaderView, QStyle, QStyledItemDelegate, QStyleOptionViewItem, QTreeWidget, QTreeWidgetItem,
)

import chrome
import structure
import theme

# The columns: the title, the `.typ` mark, the link mark and the sync mark.
TITLE, TYP, LINK, SYNC = 0, 1, 2, 3
# Where a row keeps its node's id, and how far its title is indented under its file.
ID_ROLE = Qt.ItemDataRole.UserRole
INDENT_ROLE = Qt.ItemDataRole.UserRole + 1
# The level the tree is opened to the first time it is filled.
DEFAULT_LEVEL = 2
# What the `.typ` mark reads.
TYP_MARK = ".typ"
# The size of the icons, in logical pixels, and how far one level of a file's objects is indented.
LINK_PX = 14
KIND_PX = 14
INDENT_PX = 14
# The character each state of a shared file or object is marked with, and the one a row with none leaves blank.
SYNC_MARKS = {"incoming": "↓", "conflict": "!", "ignored": "–", "problem": "?", "local": "↑"}
# The states a row is coloured by, and the theme token of each (`local` is no alarm; `in_sync` is nothing to say).
SYNC_TOKENS = {"incoming": "override", "conflict": "danger", "ignored": "muted", "problem": "warning"}
# The icon of each kind of row: a group, a file, and an object by its type.
KIND_ICONS = {
    "group": "kind_group", "file": "kind_file", "heading": "kind_heading", "text": "kind_text",
    "table": "kind_table", "show-norm-list": "kind_norms",
}
# What a row can be dragged as: the families a drop treats alike. A heading of a file that carries no tags is no object and goes with its file; an object taken out of the document (`removed`) goes nowhere until it is put back.
DRAGGABLE = ("group", "file", "object")
# The id of the «Document entier» row: no node of a document can have it, a node's id never starting with «@».
WHOLE_ID = "@document"


def display_title(node):
    """What a row reads: a group's title as structure.json has it, a file's or a heading's as the words Typst prints (`structure.plain_title` -- the markup source of the heading taken to its words), an object's short label, the node's id (an object's own) where there is nothing to read."""
    if node.kind == "group":
        return node.title or node.id
    words = structure.plain_title(node.title or "").strip()
    if words:
        return words
    return node.object_id or node.id if node.kind in ("object", "removed") else node.id


def icon_key(node):
    """The key of `chrome.ICONS` for a node: its object type where it is one -- or was one, for an object taken out of the document --, else its kind."""
    if node.kind in ("object", "removed"):
        return KIND_ICONS.get(node.object_type, "kind_text")
    return KIND_ICONS.get(node.kind, "kind_file")


class _Delegate(QStyledItemDelegate):
    """Draws an object's title indented by its level under its file -- the rows are flat in the tree, so the indent is the row's own -- and **a row chosen in its own ink**: the style sheet gives a selected item the ink of the scheme whatever the row's foreground, so the delegate fills the cell with the selection's ground itself and draws the item as one that is not selected, which keeps the orange of a row another document changed, the red of a conflict and the grey of a row not printed readable while it is chosen. The ground is the whole cell, the indent included."""

    def paint(self, painter, option, index):
        shift = index.data(INDENT_ROLE) if index.column() == TITLE else 0
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        if not shift and not selected:
            super().paint(painter, option, index)
            return
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        if selected:
            painter.save()
            painter.fillRect(option.rect, QColor(theme.colour("accent-soft")))
            painter.restore()
            opt.state &= ~(QStyle.StateFlag.State_Selected | QStyle.StateFlag.State_MouseOver)
        if shift:
            opt.rect = opt.rect.adjusted(int(shift) * INDENT_PX, 0, 0, 0)
        widget = opt.widget
        style = widget.style() if widget is not None else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, widget)


class StructureTree(QTreeWidget):
    """A document's chapters, sections and objects as a tree: collapsible, a box on every section, an icon for each kind of row, marks for a file of its own, a file shared and a change another document made, several rows chosen at once, and a drop that says what it means and moves nothing."""

    toggled = Signal(str, bool)                 # a section's box ticked or cleared by the user: its node id, and whether it is now enabled
    selectionIdsChanged = Signal(list)          # the rows chosen, by the user's hand: their node ids in document order ([] where none)
    dropped = Signal(list, str, str)            # what was dragged and where it was dropped: the node ids, the id of the row under the pointer ("" over none) and `above`, `below`, `on` or `end`

    def __init__(self, parent=None):
        super().__init__(parent)
        theme.ensure()
        self.setColumnCount(4)
        self.setHeaderHidden(True)
        self.setUniformRowHeights(True)
        self.setIndentation(16)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setExpandsOnDoubleClick(True)
        self.setIconSize(QSize(KIND_PX, KIND_PX))
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setItemDelegate(_Delegate(self))
        head = self.header()
        head.setStretchLastSection(False)
        head.setSectionResizeMode(TITLE, QHeaderView.ResizeMode.Stretch)
        for column in (TYP, LINK, SYNC):
            head.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        self.nodes = {}                 # node id -> node, as last given
        self.items = {}                 # node id -> row
        self.order = []                 # node ids in document order
        self.sync = None                # node -> state or None, the tab's
        self.sync_tips = None           # node -> the tooltip of its sync mark
        self.typ_mark = True            # whether the `.typ` column is shown
        self.stopped = set()            # the ids of the files whose sharing the engineer stopped, which show a greyed link mark
        self.stopped_tip = ""           # what that greyed mark says
        self.whole = None               # the «Document entier» row, at the top
        self._building = False
        self.itemChanged.connect(self._changed)
        self.itemSelectionChanged.connect(self._selection_changed)

    # -- filling -------------------------------------------------------------------------

    def set_nodes(self, nodes, tips=None, state=None, level=DEFAULT_LEVEL, sync=None, sync_tips=None, typ_mark=True, stopped=None, stopped_tip=None, whole_label=None, whole_tip=None):
        """The tree shows `nodes` (what structure.tree gives). `tips(node)` -- the tab's -- gives the three tooltips of a row as (title, `.typ` mark, link mark), empty strings for none. `sync(node)` is a node's state against the other documents (calc/sync.py's: `incoming`, `conflict`, `ignored`, `local`, `problem` -- None for none) and `sync_tips(node)` what its mark says. `typ_mark` says whether the `.typ` column is shown (the report's, not a convention's or a base's: see the module's docstring). `stopped` and `stopped_tip` are what `set_stopped` takes, given with the rows they apply to. `whole_label` -- the window's words for the whole document -- puts the row that stands for it at the top, `whole_tip` its tooltip. `state` is what `state()` gave before: the rows opened then are opened again and the rows selected are selected again, where they are still there; without one the tree is opened to `level` (None for every row), which is also what a state that names no row still here gets. Nothing is said while it is filled: a row selected by it was not chosen by anyone."""
        state = state or {}
        self._building = True
        self.blockSignals(True)
        try:
            self.clear()
            self.nodes, self.items, self.order = {}, {}, []
            self.whole = None
            if whole_label:
                # the whole document: a sibling of the first chapter and not their parent, no box, never dragged
                self.whole = QTreeWidgetItem(self)
                self.whole.setText(TITLE, whole_label)
                self.whole.setData(TITLE, ID_ROLE, WHOLE_ID)
                self.whole.setIcon(TITLE, chrome.icon("kind_group", QColor(theme.colour("accent-strong")).name(), KIND_PX))
                self.whole.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                font = QFont(self.whole.font(TITLE))
                font.setItalic(True)
                self.whole.setFont(TITLE, font)
                if whole_tip:
                    self.whole.setToolTip(TITLE, whole_tip)
            self.sync, self.sync_tips = sync, sync_tips
            self.typ_mark = bool(typ_mark)
            if stopped is not None:
                self.stopped, self.stopped_tip = set(stopped), stopped_tip or ""
            self.setColumnHidden(TYP, not self.typ_mark)
            muted = QBrush(QColor(theme.colour("muted")))
            ink = QColor(theme.colour("ink-soft")).name()

            def add(node, parent, file_level):
                row = QTreeWidgetItem(parent) if parent is not None else QTreeWidgetItem(self)
                row.setText(TITLE, display_title(node))
                row.setData(TITLE, ID_ROLE, node.id)
                row.setIcon(TITLE, chrome.icon(icon_key(node), ink, KIND_PX))
                # A row is enabled and selectable, may be dragged where it is a chapter, a section or an object, and be dropped on; only a section carries a box.
                flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsDropEnabled
                if node.kind in DRAGGABLE:
                    flags |= Qt.ItemFlag.ItemIsDragEnabled
                if node.kind in ("file", "group"):
                    row.setFlags(flags | Qt.ItemFlag.ItemIsUserCheckable)
                    row.setCheckState(TITLE, Qt.CheckState.Checked if node.enabled else Qt.CheckState.Unchecked)
                else:
                    row.setFlags(flags)
                if node.kind == "group":
                    font = QFont(row.font(TITLE))
                    font.setBold(True)
                    row.setFont(TITLE, font)
                if node.kind in ("object", "removed") and file_level is not None and node.level is not None:
                    row.setData(TITLE, INDENT_ROLE, max(0, min(4, node.level - file_level)))
                if node.kind == "removed":
                    # taken out of the document: struck through, and greyed by apply_sync, the node not being printed
                    font = QFont(row.font(TITLE))
                    font.setStrikeOut(True)
                    row.setFont(TITLE, font)
                    row.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                if node.separate_file and self.typ_mark:
                    row.setText(TYP, TYP_MARK)
                    row.setTextAlignment(TYP, Qt.AlignmentFlag.AlignCenter)
                if node.shared_with:
                    row.setIcon(LINK, chrome.icon("badge_link", theme.colour("accent-strong"), LINK_PX))
                elif node.id in self.stopped:
                    row.setIcon(LINK, chrome.icon("badge_link", theme.colour("muted"), LINK_PX))
                if tips is not None:
                    for column, text in zip((TITLE, TYP, LINK), tips(node)):
                        if text:
                            row.setToolTip(column, text)
                if node.id in self.stopped and not node.shared_with and self.stopped_tip:
                    row.setToolTip(LINK, self.stopped_tip)
                self.nodes[node.id] = node
                self.items[node.id] = row
                self.order.append(node.id)
                for child in node.children:
                    add(child, row, node.level if node.kind == "file" else file_level)

            for node in nodes:
                add(node, None, node.level if node.kind == "file" else None)
            self.apply_sync(muted)
            opened = state.get("expanded")
            if opened is None or not set(opened) & set(self.items):
                self.expand_to(level)
            else:
                wanted = set(opened)
                for node_id, row in self.items.items():
                    row.setExpanded(node_id in wanted)
            chosen = [node_id for node_id in state.get("selection") or [] if node_id in self.items]
            current = state.get("selected")
            if not chosen and current in self.items:
                chosen = [current]
            self._select(chosen, current if current in self.items else None)
        finally:
            self.blockSignals(False)
            self._building = False

    def update_nodes(self, nodes, tips=None):
        """The rows' words, indents and ink brought up to date with `nodes` **without rebuilding the tree** -- where they are the same nodes in the same order, which is what an edit of one object's body leaves. The rows themselves, what is open and what is chosen stay: it is how a tree is refreshed from inside one of its own signals, where clearing it would crash. False, and nothing touched, where the ids differ: the caller then fills the tree again."""
        flat = structure.flatten(nodes)
        if [node.id for node in flat] != self.order:
            return False
        self._building = True
        try:
            file_level = {}
            for node in flat:
                row = self.items[node.id]
                self.nodes[node.id] = node
                row.setText(TITLE, display_title(node))
                if node.kind == "file":
                    file_level[node.id] = node.level
                level = file_level.get(node.parent)
                if node.kind in ("object", "removed") and level is not None and node.level is not None:
                    row.setData(TITLE, INDENT_ROLE, max(0, min(4, node.level - level)))
                if tips is not None:
                    for column, text in zip((TITLE, TYP, LINK), tips(node)):
                        row.setToolTip(column, text or "")
            self.apply_sync()
        finally:
            self._building = False
        return True


    def set_sync(self, sync, sync_tips=None):
        """The rows coloured and marked again by another `sync` function -- the state against the other documents changed, the rows did not. Nothing is said."""
        self.sync, self.sync_tips = sync, sync_tips
        self._building = True
        try:
            self.apply_sync()
        finally:
            self._building = False

    def apply_sync(self, muted=None):
        """The ink of every row: the warning colour for a file with something wrong, then the sync state's, then the grey of a section not printed -- the order in which they matter."""
        muted = muted or QBrush(QColor(theme.colour("muted")))
        warning = QBrush(QColor(theme.colour("warning")))
        for node_id, row in self.items.items():
            node = self.nodes[node_id]
            state = self.sync(node) if self.sync is not None else None
            token = SYNC_TOKENS.get(state)
            if node.problems:
                ink = warning
            elif token is not None:
                ink = QBrush(QColor(theme.colour(token)))
            elif not node.active:
                ink = muted
            else:
                ink = None
            for column in (TITLE, TYP):
                row.setForeground(column, ink if ink is not None else QBrush())
            if ink is not None and not node.active and not node.problems and token is None:
                row.setForeground(TYP, muted)
            mark = SYNC_MARKS.get(state, "") if state not in (None, "in_sync") else ""
            row.setText(SYNC, mark)
            row.setTextAlignment(SYNC, Qt.AlignmentFlag.AlignCenter)
            if mark and token is not None:
                row.setForeground(SYNC, QBrush(QColor(theme.colour(token))))
            elif mark:
                row.setForeground(SYNC, muted)
            tip = self.sync_tips(node) if self.sync_tips is not None and mark else ""
            row.setToolTip(SYNC, tip or "")

    def expand_to(self, level):
        """The rows printed at a level below `level` opened, every other closed: «2» shows the rows of levels 1 and 2. None opens the whole tree."""
        if level is None:
            self.expandAll()
            return
        for node_id, row in self.items.items():
            node = self.nodes[node_id]
            row.setExpanded(row.childCount() > 0 and node.level is not None and node.level < level)

    def reveal(self, node_id):
        """Every row above `node_id` opened and the row scrolled into view; False where there is none."""
        row = self.items.get(node_id)
        if row is None:
            return False
        parent = row.parent()
        while parent is not None:
            parent.setExpanded(True)
            parent = parent.parent()
        self.scrollToItem(row)
        return True

    # -- what it holds ---------------------------------------------------------------------

    def node(self, node_id):
        return self.nodes.get(node_id)

    def row(self, node_id):
        return self.items.get(node_id)

    def ids(self):
        """The node ids in document order."""
        return list(self.order)

    def selected_ids(self):
        """The ids of the rows chosen, in document order."""
        chosen = {row.data(TITLE, ID_ROLE) for row in self.selectedItems()}
        return [node_id for node_id in self.order if node_id in chosen]

    def selected_id(self):
        """The row that is current -- the one last clicked -- or "" where there is none, or it is the whole document."""
        row = self.currentItem()
        node_id = row.data(TITLE, ID_ROLE) if row is not None and row.isSelected() else ""
        return "" if node_id == WHOLE_ID else node_id

    def _select(self, ids, current=None):
        blocked = self.blockSignals(True)
        try:
            self.clearSelection()
            first = None
            for node_id in ids:
                row = self.items.get(node_id)
                if row is not None:
                    row.setSelected(True)
                    first = first or row
            target = self.items.get(current) if current is not None else first
            if target is not None:
                self.setCurrentItem(target, 0, QItemSelectionModel.SelectionFlag.NoUpdate)
            elif self.whole is not None:
                # nothing chosen is the whole document, and its row says so
                self.whole.setSelected(True)
                self.setCurrentItem(self.whole, 0, QItemSelectionModel.SelectionFlag.NoUpdate)
            else:
                self.setCurrentItem(None)
        finally:
            self.blockSignals(blocked)

    def select(self, node_id):
        """Makes `node_id` the one row chosen without saying so -- a programmatic move is nobody's choice. False where there is no such row."""
        if node_id not in self.items:
            return False
        self._select([node_id], node_id)
        return True

    def select_ids(self, ids, current=None):
        """The rows `ids` chosen without saying so; the ones there are, and False where none is."""
        found = [node_id for node_id in ids if node_id in self.items]
        self._select(found, current if current in found else None)
        return bool(found)

    def state(self):
        """What the engineer has done to the tree, to give back to `set_nodes`: the ids of the rows he has open, the one current and the rows chosen."""
        return {"expanded": [node_id for node_id, row in self.items.items() if row.isExpanded()], "selected": self.selected_id(), "selection": self.selected_ids()}

    # -- what the user does -----------------------------------------------------------------

    def _changed(self, row, column):
        if self._building or column != TITLE:
            return
        node_id = row.data(TITLE, ID_ROLE)
        node = self.nodes.get(node_id)
        if node is None or not (row.flags() & Qt.ItemFlag.ItemIsUserCheckable):
            return
        enabled = row.checkState(TITLE) == Qt.CheckState.Checked
        if enabled != node.enabled:     # the tab writes it, and fills the tree again with what the file then says
            self.toggled.emit(node_id, enabled)

    def _selection_changed(self):
        if self._building:
            return
        if self.whole is not None and self.whole.isSelected() and len(self.selectedItems()) > 1:
            # the whole document chosen with other rows means those rows: the whole row lets go
            blocked = self.blockSignals(True)
            self.whole.setSelected(False)
            self.blockSignals(blocked)
        self.selectionIdsChanged.emit(self.selected_ids())

    def dragMoveEvent(self, event):
        if event.source() is self:
            super().dragMoveEvent(event)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """A drop says where it fell and changes nothing: the rows are never moved by Qt, the tab moves what the model moves and fills the tree again. What was dragged is what was chosen."""
        if event.source() is not self:
            event.ignore()
            return
        row = self.itemAt(event.position().toPoint())
        indicator = self.dropIndicatorPosition()
        if row is not None and row is self.whole:
            # above the whole document's row is above the first row of the document
            row = self.items.get(self.order[0]) if self.order else None
            indicator = QAbstractItemView.DropIndicatorPosition.AboveItem
        where = {
            QAbstractItemView.DropIndicatorPosition.AboveItem: "above",
            QAbstractItemView.DropIndicatorPosition.BelowItem: "below",
            QAbstractItemView.DropIndicatorPosition.OnItem: "on",
        }.get(indicator, "end")
        ids = self.selected_ids()
        event.setDropAction(Qt.DropAction.IgnoreAction)
        event.ignore()
        self.setState(QAbstractItemView.State.NoState)      # what the view's own dropEvent does once it has dropped
        self.viewport().update()
        if ids:
            self.dropped.emit(ids, row.data(TITLE, ID_ROLE) if row is not None else "", where)
