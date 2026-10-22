# -*- coding: utf-8 -*-
"""The left pane of every editor tab: a list that can be sorted into folders (docs/ui/window.md §10quater).

A project grows a plan per building, a static model per beam and a connector per node, and a flat list of forty of them is a list nobody reads. The engineer asked for folders, drag and drop, and the multiple selection of the Windows explorer -- Ctrl and Shift.

**A folder is a field, not a directory.** Each source carries a `group` string ("" at the root), which is exactly the «Groupe» the engineer's own «Identité» box already names. Nothing moves on disk, so the rule that decides everything downstream -- *the id is the file name*, section 3.3quinquies -- is untouched, no `show-*` call changes, and a folder renamed cannot break a report. The alternative, real subdirectories, would have made `connectors/Halle/SD_01.json` an id of `Halle/SD_01` or a name that no longer says where its file is; neither is worth a tidier `ls`.

**A folder that holds nothing exists only in the window.** Folders are *derived* from the `group` values in use, so an empty one has nowhere to live in the project -- and it should not: it is not a fact about the structure. The set of empty folders is kept per tab in the project file, `gui.empty_folders` (project.py, v0.83; in the user's settings from v0.75 to v0.82), a folder being a property of the sources it files.

**A leaf may have children.** The polar moments tab lists calculations under their connector, so an entry may carry `children`; the folder then holds the connector and the connector holds its calculations. The three flat tabs simply pass none.

⚠️ **The drop is not Qt's own move.** `dropEvent` is intercepted: the widget works out which group was dropped into, emits `moved`, and leaves the tree alone. The tab writes the field, exports, and rebuilds -- so what is on screen is always what is in the files, and a drop that the tab refuses (an export that fails) leaves nothing half-moved.

**Four things the engineer asked for at the end of v0.77**, all of them here and none in the tabs:

- **Ctrl and Shift select several entries** and the selection survives the list being rebuilt. It did not: a click loads the entry, loading rebuilds the list, and `clear()` took the selection with it -- so Ctrl+click only ever held the last entry clicked. `set_entries` puts back what was selected, and `select` moves the current entry without clearing the others.
- **«Archives», always the last row.** A deleted file is archived (source_archive.py) and listed under it; dropping an entry on it archives, dropping an archived entry anywhere else restores it, and its menu deletes it for good. The folder is not a `group`: it is neither renamed nor removed, and no drop files anything into it as a field.
- **A folder stays when its last entry leaves.** Folders are derived from the `group` values in use, so moving the last file out of one made it vanish; `set_entries` now keeps every folder the previous contents used, unless it was removed or renamed here.
- **Which file is in which folder is drawn**: a vertical line under a folder, left of what it holds, and a short horizontal one to each entry (`drawBranches`), as a file tree draws them.

**A folder and a file no longer look alike (v0.116, the engineer's complaint of 06.10.2026).** A folder is a wood-coloured folder icon, open or closed, set in semibold; it has no expand arrow, the icon says whether it is open and a click on its row toggles it. A file has no icon but the dot of unsaved changes the tab puts in its slot, and plain weight. And the tree has **no decoration column at the root**: a file that is in no folder stands at the very left, exactly where a folder's icon does, so only a file that is really inside a folder is indented -- and carries the tree's lines. Before, every top-level row had an arrow column to its left, empty for a file, so root files read as if they were inside the folder above.

**The order is the engineer's, where a tab asks for it (issue #15).** A tab that calls `attach_order(key, store)` -- a `list_order.Store`, the file `Woodcore-Datei/lists.json` -- shows its entries in the order kept there, those it does not name last by id, and a drop says *where*: above the entry dropped on, below it, or at the end of the folder. The order is written by the kernel itself through the store, which refuses in a project opened read only; then `moved(ids, group)` goes out **only for the entries whose folder changes** (its signature unchanged, so every tab's `on_moved` writes their field as before), and `reordered()` where none does -- an order alone rewrites no source and exports nothing. A tab whose sources have no field for a folder (`groups=True`, the «Formules» tab, whose domains are `.typ` files) has its folders kept in the same file, and the kernel writes them there too: a drop, a folder renamed or removed. A tab that attaches nothing -- `SheetList`, whose order is its bundle's -- behaves exactly as before. Folders stay in alphabetical order, and the root's entries after them.

**A multiple selection is dragged whole.** Pressing on an entry of a Ctrl/Shift selection changed the current entry, a tab loaded it and rebuilt the list, and the drag that was starting was lost with the rebuilt rows -- so only one file could be dragged. A press on an already-selected entry now leaves the selection and the current entry alone until it is known whether it is a drag (it then carries every selected entry in one drop, one `moved`) or a click (it then selects that entry alone, as the explorer does).
"""

from PySide6.QtCore import QItemSelectionModel, QLineF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPalette, QPen
import list_order  # the order of the lists and the «Formules» tab's folders (calc/list_order.py, issue #15)
import notifications  # every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # what was a message box is a notice since v0.117 (notices_ui.tell)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QInputDialog,
    QMenu,
    QMessageBox,
    QStyledItemDelegate,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
)
import svg_icons

# What an item carries, beside its text.
ID_ROLE = Qt.ItemDataRole.UserRole          # a leaf's id; a folder carries None
GROUP_ROLE = Qt.ItemDataRole.UserRole + 1   # the folder name a row belongs to ("" at the root)
KIND_ROLE = Qt.ItemDataRole.UserRole + 2    # "folder", "leaf", "child", "archives" (the folder) or "archived" (an entry in it)
ARCHIVE_KINDS = ("archives", "archived")

ROOT_GROUP = ""

FOLDER_PX = 16                              # a folder's icon, whatever the tab's icon size (which is the dot's)

# A folder shut and open, line icons on a 24-unit square (SVG Tiny: paths only), drawn in one ink.
FOLDER_SVG = {
    False: '<path d="M3 6.5h6l2 2h10v11H3z"/>',
    True: '<path d="M3 6.5h6l2 2h8v3"/><path d="M3 19.5l2.5-8h16l-2.5 8z"/>',
}


def folder_icon(opened, colour):
    """The icon of a folder, open or shut, in `colour` (svg_icons.svg_icon)."""
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="%s" '
           'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">%s</svg>' % (colour, FOLDER_SVG[bool(opened)]))
    return svg_icons.svg_icon(svg, FOLDER_PX)


def _ink(name):
    """A token of the scheme in force. Until v0.117 a colour of its own stood in where the theme could not be loaded -- a copy of theme.json's value that would have aged without saying so (issue #29); theme.json is read by every test."""
    import theme
    return theme.colour(name)


class _Delegate(QStyledItemDelegate):
    """Draws a folder's icon at its own size, which is not the size of the dot a file's slot keeps."""

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        if index.data(KIND_ROLE) in ("folder", "archives"):
            option.decorationSize = QSize(FOLDER_PX, FOLDER_PX)


def group_of(source):
    """The folder a source belongs to. Absent, empty or not a string all read as the root, so a file written before this existed needs no migration."""
    value = source.get("group") if isinstance(source, dict) else None
    return value.strip() if isinstance(value, str) else ROOT_GROUP


def folders_in(sources):
    """Every folder actually in use, in the order a reader expects: alphabetical, the root apart."""
    return sorted({group_of(s) for s in sources} - {ROOT_GROUP}, key=lambda name: name.lower())


class GroupedList(QTreeWidget):
    """A tree of folders and entries. `set_entries` is the only way its contents are set; everything else reads."""

    currentIdChanged = Signal(str)          # "" where nothing is selected; never an archived entry's key
    moved = Signal(object, str)             # (ids dropped, target folder) -- the tab writes the field
    foldersChanged = Signal()               # an empty folder was made, renamed or removed: the tab persists
    archiveRequested = Signal(object)       # ids dropped on «Archives» -- the tab archives them (source_archive.Actions)
    restoreRequested = Signal(object, str)  # (archived keys, target folder) -- dropped out of «Archives», or «Restaurer»
    purgeRequested = Signal(object)         # archived keys to delete for good
    reordered = Signal()                    # a drop changed the order kept and no folder (attach_order): the tab rebuilds its list

    def __init__(self, strings=None, parent=None, lang=None):
        super().__init__(parent)
        self._strings = strings or {}
        self._lang = lang
        self._entries = []
        self._archived = []
        self._empty = []                    # folders holding nothing, kept by the window alone
        self._dropped = set()               # folders removed or renamed here: not kept when they empty
        self._expanded = None               # None until the first fill, which opens what it finds
        self._seen = set()
        self._filling = False
        self._deferred = None               # (item, point) -- a press on a selected entry of a multiple selection, not yet a click or a drag
        self._pressed_folder = None         # the folder a left press landed on, toggled by its release
        self._order = None                  # (tab key, list_order.Store, folders kept there, a drop may change a folder) -- attach_order
        self.setHeaderHidden(True)
        self.setRootIsDecorated(False)      # no arrow column at the root: a file in no folder stands where a folder's icon does
        self.setExpandsOnDoubleClick(False) # a click on the row toggles it (mouseReleaseEvent)
        self.setIndentation(20)
        self.setItemDelegate(_Delegate(self))
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)   # Ctrl and Shift, as the explorer does
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu)
        self.currentItemChanged.connect(self._on_current)
        self.itemExpanded.connect(self._remember_expanded)
        self.itemCollapsed.connect(self._remember_expanded)

    # --- words ----------------------------------------------------------------


    def _t(self, key, fallback):
        """A word of this widget. The tabs hand over their own STRINGS, which do not carry the `grp_` words -- woodcore_gui merges those into its own table only -- so they are looked up here by language: until v0.77 the folder menu said French in a German window."""
        if key in self._strings:
            return self._strings[key]
        return STRINGS.get(self._lang or "", {}).get(key, fallback)

    def archives_name(self):
        return self._t("grp_archives", "Archives")

    # --- contents -------------------------------------------------------------

    def attach_order(self, key, store, groups=False, regroup=True):
        """The entries shown in the order the engineer gave them, kept by `store` (a list_order.Store) under the tab's `key` (module docstring). `groups`: the folders are kept there too, the tab's sources having no field for one. `regroup` False: a drop never changes an entry's folder (the «Python» tab, whose folder is a line of the script) -- one into another folder does nothing."""
        self._order = (key, store, groups, regroup)

    def set_entries(self, entries, empty_folders=(), select=None, archived=()):
        """`entries` is a list of {id, text, group, children?, colour?, tooltip?, fixed?} -- a child {id, text, italic?}; `fixed` keeps an entry in the `group` it is given, whatever folder the kept order files it in (the «Domaines» tab's group of a specialised tab's domain, issue #64); `empty_folders` the ones the project cannot record; `archived` the archived sources as source_archive.entries() lists them, set under «Archives», the last row. `colour` paints a row's text and `tooltip` says why.

        What was selected is selected again, and a folder the previous contents used stays when nothing is left in it -- unless it was removed or renamed here.
        """
        chosen = set(self.selected_ids()) | set(self.selected_archives())
        previous = {e.get("group") or ROOT_GROUP for e in self._entries} - {ROOT_GROUP}
        if self._order is not None:
            key, store, groups, _regroup = self._order
            order, kept = store.tab(key)
            entries = list_order.ordered(list(entries), order)
            if groups:
                entries = [e if e.get("fixed") else dict(e, group=kept.get(e["id"], ROOT_GROUP)) for e in entries]
        self._entries = list(entries)
        self._archived = list(archived)
        used = {e.get("group") or ROOT_GROUP for e in self._entries}
        kept = [name for name in empty_folders if name] + sorted(previous - used)
        self._empty = [name for i, name in enumerate(kept) if name not in kept[:i] and name not in self._dropped]
        self._dropped = set()
        self._filling = True
        self.clear()
        names = sorted(used - {ROOT_GROUP} | set(self._empty), key=lambda n: n.lower())
        folders = {}
        for name in names:
            item = QTreeWidgetItem([name])
            item.setData(0, KIND_ROLE, "folder")
            item.setData(0, GROUP_ROLE, name)
            item.setFlags((item.flags() | Qt.ItemFlag.ItemIsDropEnabled) & ~Qt.ItemFlag.ItemIsDragEnabled)
            font = item.font(0)
            font.setWeight(QFont.Weight.DemiBold)      # a folder is set in semibold, a file in plain weight
            item.setFont(0, font)
            self.addTopLevelItem(item)
            folders[name] = item
        for entry in self._entries:
            group = entry.get("group") or ROOT_GROUP
            leaf = QTreeWidgetItem([entry.get("text") or entry["id"]])
            leaf.setData(0, ID_ROLE, entry["id"])
            leaf.setData(0, GROUP_ROLE, group)
            leaf.setData(0, KIND_ROLE, "leaf")
            leaf.setFlags((leaf.flags() | Qt.ItemFlag.ItemIsDragEnabled) & ~Qt.ItemFlag.ItemIsDropEnabled)
            if entry.get("colour"):
                leaf.setForeground(0, QColor(entry["colour"]))
            if entry.get("tooltip"):
                leaf.setToolTip(0, entry["tooltip"])
            if group in folders:
                folders[group].addChild(leaf)
            else:
                self.addTopLevelItem(leaf)
            for child in entry.get("children") or ():
                row = QTreeWidgetItem([child.get("text") or child["id"]])
                row.setData(0, ID_ROLE, child["id"])
                row.setData(0, GROUP_ROLE, group)
                row.setData(0, KIND_ROLE, "child")
                row.setFlags(row.flags() & ~(Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsDropEnabled))
                if child.get("italic"):
                    # a child that is no thing of its own -- the «Formules» tab's `val`, a variable shown again and not made (issue #19)
                    font = row.font(0)
                    font.setItalic(True)
                    row.setFont(0, font)
                leaf.addChild(row)
        # «Archives», after everything else, the root's own entries included
        shelf = QTreeWidgetItem([self.archives_name()])
        shelf.setData(0, KIND_ROLE, "archives")
        shelf.setData(0, GROUP_ROLE, None)
        shelf.setFlags((shelf.flags() | Qt.ItemFlag.ItemIsDropEnabled) & ~Qt.ItemFlag.ItemIsDragEnabled)
        font = shelf.font(0)
        font.setItalic(True)
        shelf.setFont(0, font)
        shelf.setToolTip(0, self._t("grp_archives_tip", "Les fichiers supprimés. Glisser un fichier hors d'ici le restaure ; clic droit pour le supprimer définitivement."))
        self.addTopLevelItem(shelf)
        muted = self.palette().color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text)
        for entry in self._archived:
            row = QTreeWidgetItem([entry.get("text") or entry["id"]])
            row.setData(0, ID_ROLE, entry["id"])
            row.setData(0, GROUP_ROLE, None)
            row.setData(0, KIND_ROLE, "archived")
            row.setFlags((row.flags() | Qt.ItemFlag.ItemIsDragEnabled) & ~Qt.ItemFlag.ItemIsDropEnabled)
            row.setForeground(0, muted)
            if entry.get("tooltip"):
                row.setToolTip(0, entry["tooltip"])
            shelf.addChild(row)
        if self._expanded is None:          # first fill: a folder nobody has closed yet is open
            self._expanded = set(names) | {ARCHIVES_KEY}   # «Archives» open too, so a file just deleted is seen where it went
        self._expanded |= {n for n in names if n not in self._seen}
        self._seen |= set(names)            # a folder seen for the first time opens; one closed stays closed
        for name, item in folders.items():
            item.setExpanded(name in self._expanded)
            self._set_folder_icon(item)
        shelf.setExpanded(ARCHIVES_KEY in self._expanded)
        self._set_folder_icon(shelf)
        for item in self._items(("leaf",)):
            if item.childCount():
                item.setExpanded(True)     # a file holding children has no arrow to open it with
        for item in self._items(("leaf", "child", "archived")):
            if item.data(0, ID_ROLE) in chosen:
                item.setSelected(True)
        self._filling = False
        if select:
            self.select(select)

    def _set_folder_icon(self, item):
        """The folder's icon follows its state: open or shut, wood-coloured -- «Archives» muted."""
        shelf = item.data(0, KIND_ROLE) == "archives"
        item.setIcon(0, folder_icon(item.isExpanded(), _ink("muted" if shelf else "wood")))

    def _remember_expanded(self, item):
        if item.data(0, KIND_ROLE) in ("folder", "archives"):
            self._set_folder_icon(item)
        if self._filling or item.data(0, KIND_ROLE) not in ("folder", "archives"):
            return
        name = ARCHIVES_KEY if item.data(0, KIND_ROLE) == "archives" else item.data(0, GROUP_ROLE)
        self._expanded.add(name) if item.isExpanded() else self._expanded.discard(name)

    # --- reading --------------------------------------------------------------

    def _items(self, kinds=("leaf",)):
        out = []
        stack = [self.topLevelItem(i) for i in range(self.topLevelItemCount())]
        while stack:
            item = stack.pop(0)
            if item.data(0, KIND_ROLE) in kinds:
                out.append(item)
            stack.extend(item.child(i) for i in range(item.childCount()))
        return out

    def _item_for(self, entry_id, kinds=("leaf", "child")):
        for item in self._items(kinds):
            if item.data(0, ID_ROLE) == entry_id:
                return item
        return None

    def current_id(self):
        """The id selected, leaf or child, or None -- never an archived entry, which no tab can open."""
        item = self.currentItem()
        if item is None or item.data(0, KIND_ROLE) in ARCHIVE_KINDS:
            return None
        return item.data(0, ID_ROLE)

    def selected_ids(self):
        """Every leaf selected, in the tree's own order -- what a drag carries."""
        chosen = {id(i) for i in self.selectedItems()}
        return [i.data(0, ID_ROLE) for i in self._items() if id(i) in chosen]

    def selected_archives(self):
        """Every archived entry selected, by its key (source_archive.KEY_PREFIX)."""
        chosen = {id(i) for i in self.selectedItems()}
        return [i.data(0, ID_ROLE) for i in self._items(("archived",)) if id(i) in chosen]

    def ids(self):
        return [i.data(0, ID_ROLE) for i in self._items()]

    def archived_ids(self):
        return [i.data(0, ID_ROLE) for i in self._items(("archived",))]

    def rows(self):
        """One (item, id) per entry, folders and archives excluded -- what a caller walks to mark every row, and what `tests/test_window.py` reads."""
        return [(item, item.data(0, ID_ROLE)) for item in self._items(("leaf", "child"))]

    def empty_folders(self):
        """The folders the project cannot record, for the tab to keep in its settings."""
        used = {e.get("group") or ROOT_GROUP for e in self._entries}
        return [name for name in self._empty if name not in used]

    def select(self, entry_id):
        """Makes `entry_id` the current entry. One already among several selected stays among them: moving the current entry must not undo a Ctrl or Shift selection."""
        item = self._item_for(entry_id)
        if item is None:
            return False
        self._filling = True
        parent = item.parent()
        while parent is not None:
            parent.setExpanded(True)
            parent = parent.parent()
        if item.isSelected():
            self.setCurrentItem(item, 0, QItemSelectionModel.SelectionFlag.NoUpdate)
        else:
            # the entry alone, said and not left to Qt: without flags it reads the keyboard's modifiers, and a Ctrl the application last saw held -- a key or a click sent by a test, or still down in the window -- kept the previous entry selected beside it (v0.116, WP-K)
            self.setCurrentItem(item, 0, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        self._filling = False
        return True

    def set_mark(self, entry_id, icon):
        item = self._item_for(entry_id)
        if item is not None:
            item.setIcon(0, icon if icon is not None else QIcon())


    def _on_current(self, current, _previous):
        if self._filling:
            return
        if current is not None and current.data(0, KIND_ROLE) in ARCHIVE_KINDS:
            return                          # an archived file is not opened: it is restored by a drop, or deleted
        self.currentIdChanged.emit((current.data(0, ID_ROLE) if current is not None else None) or "")

    # --- the lines of the tree ------------------------------------------------

    def drawBranches(self, painter, rect, index):
        """Qt's own branch (a folder's arrow), then the lines of a file tree: under a folder, a vertical line left of what it holds, stopping at its last entry, and a short horizontal one to each entry."""
        super().drawBranches(painter, rect, index)
        item = self.itemFromIndex(index)
        if item is None or item.parent() is None:
            return
        indent = self.indentation()
        colour = QColor(self.palette().color(QPalette.ColorRole.Text))
        colour.setAlphaF(0.45)
        painter.save()
        painter.setPen(QPen(colour, 1.0))
        chain, node = [], item
        while node.parent() is not None:
            chain.append(node)
            node = node.parent()
        depth = len(chain)
        left, top, bottom, middle = rect.left(), rect.top(), rect.bottom() + 1, rect.center().y() + 0.5

        def column(level):
            # the centre of the arrow column of the item `level` deep (0 for a top-level item)
            return left + level * indent + indent / 2.0

        def last(child):
            parent = child.parent()
            return parent.indexOfChild(child) == parent.childCount() - 1

        x = column(depth - 1)
        painter.drawLine(QLineF(x, top, x, middle if last(item) else bottom))
        painter.drawLine(QLineF(x, middle, rect.right() - 1, middle))
        for level, ancestor in enumerate(reversed(chain[1:]), start=1):
            # an ancestor folder with more below it carries its line past this row
            if not last(ancestor):
                ax = column(level - 1)
                painter.drawLine(QLineF(ax, top, ax, bottom))
        painter.restore()

    # --- the press: a multiple selection is dragged whole -----------------------------

    def mousePressEvent(self, event):
        """A press on an entry that is already one of several selected does nothing yet: making it the current entry would have the tab load it and rebuild the list, and the drag it may be the start of would die with the rebuilt rows. `mouseMoveEvent` starts the drag with the whole selection, `mouseReleaseEvent` turns a click into the entry alone."""
        self._deferred = None
        self._pressed_folder = None
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.position().toPoint())
            plain = not (event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier))
            if plain and item is not None:
                if item.data(0, KIND_ROLE) == "leaf" and item.isSelected() and len(self.selected_ids()) > 1:
                    self._deferred = (item, event.position().toPoint())
                    event.accept()
                    return
                if item.data(0, KIND_ROLE) in ("folder", "archives"):
                    self._pressed_folder = item
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._deferred is not None:
            if event.buttons() & Qt.MouseButton.LeftButton and \
                    (event.position().toPoint() - self._deferred[1]).manhattanLength() >= QApplication.startDragDistance():
                self._deferred = None
                self.startDrag(Qt.DropAction.MoveAction)          # carries every selected entry
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        deferred, self._deferred = self._deferred, None
        folder, self._pressed_folder = self._pressed_folder, None
        if deferred is not None:
            if event.button() == Qt.MouseButton.LeftButton and self.itemAt(event.position().toPoint()) is deferred[0]:
                self.setCurrentItem(deferred[0], 0, QItemSelectionModel.SelectionFlag.ClearAndSelect)   # a click, not a drag: the entry alone, as the explorer does
            event.accept()
            return
        super().mouseReleaseEvent(event)
        if folder is not None and event.button() == Qt.MouseButton.LeftButton and self.itemAt(event.position().toPoint()) is folder:
            folder.setExpanded(not folder.isExpanded())          # no arrow: a click on the row opens and shuts it

    # --- the drop -------------------------------------------------------------

    def dropEvent(self, event):
        """Work out where the drop landed, say so, and leave the tree alone: the tab rebuilds it from the files. Onto «Archives» or an entry in it, the entries dropped are archived; an archived entry dropped anywhere else is restored there."""
        ids = self.selected_ids()
        keys = self.selected_archives()
        target = self.itemAt(event.position().toPoint()) if hasattr(event, "position") else self.itemAt(event.pos())
        kind = target.data(0, KIND_ROLE) if target is not None else None
        if target is None:
            group = ROOT_GROUP
        elif kind == "folder":
            group = target.data(0, GROUP_ROLE)
        else:
            group = target.data(0, GROUP_ROLE) or ROOT_GROUP
        below = self.dropIndicatorPosition() == QAbstractItemView.DropIndicatorPosition.BelowItem
        event.setDropAction(Qt.DropAction.IgnoreAction)
        event.accept()
        if kind in ARCHIVE_KINDS:
            if ids:
                self.archiveRequested.emit(ids)
            return
        if keys:
            self.restoreRequested.emit(keys, group)
        if ids:
            if self._order is None:
                self.moved.emit(ids, group)
            else:
                self.drop_ids(ids, target, group, below)

    def insertion(self, target, below, moving):
        """The entry a drop on the row `target` lands just above: `target` itself, the one after it where `below` -- the first of them not among `moving` --, or None at the end of its folder. SheetList's bundles and the order of every list read it."""
        parent = target.parent()
        siblings = [parent.child(i) for i in range(parent.childCount())] if parent is not None else [self.topLevelItem(i) for i in range(self.topLevelItemCount())]
        siblings = [s for s in siblings if s.data(0, KIND_ROLE) == "leaf"]
        index = siblings.index(target) + (1 if below else 0) if target in siblings else len(siblings)
        return next((s.data(0, ID_ROLE) for s in siblings[index:] if s.data(0, ID_ROLE) not in moving), None)

    def drop_ids(self, ids, target, group, below=False):
        """`ids` dropped on `target` (None: the empty part of the list) into `group`, where an order is attached: the order written through the store -- nothing at all where it refuses --, then `moved` for the entries that change folder, or `reordered`. Where the folders are kept by the store, it writes them too and `reordered` alone goes out."""
        key, store, groups, regroup = self._order
        kind = target.data(0, KIND_ROLE) if target is not None else None
        if kind == "child":
            target, kind = target.parent(), "leaf"
        current = {e["id"]: (e.get("group") or ROOT_GROUP) for e in self._entries}
        changing = [i for i in ids if current.get(i, ROOT_GROUP) != group]
        if changing and not regroup:
            return                          # an entry's folder is not the list's to change here
        before = self.insertion(target, below, set(ids)) if kind == "leaf" else None
        order, kept = store.tab(key)
        new = list_order.place(order, [e["id"] for e in self._entries], ids, lambda i: current.get(i, ROOT_GROUP), group, before)
        if groups:
            for i in ids:
                if group:
                    kept[i] = group
                else:
                    kept.pop(i, None)
            if store.save(key, new, kept):
                self.reordered.emit()
            return
        if not store.save(key, new):
            return
        if changing:
            self.moved.emit(changing, group)
        else:
            self.reordered.emit()

    # --- the folders ----------------------------------------------------------

    def _menu(self, point):
        item = self.itemAt(point)
        kind = item.data(0, KIND_ROLE) if item is not None else None
        menu = QMenu(self)
        if kind == "archived":
            keys = self.selected_archives() if item.isSelected() else [item.data(0, ID_ROLE)]
            menu.addAction(self._t("grp_restore", "Restaurer"), lambda: self.restoreRequested.emit(keys, ROOT_GROUP))
            menu.addAction(self._t("grp_purge", "Supprimer définitivement…"), lambda: self.purgeRequested.emit(keys))
            menu.exec(self.viewport().mapToGlobal(point))
            return
        menu.addAction(self._t("grp_new", "Nouveau dossier…"), self._new_folder)
        if kind == "folder":
            menu.addAction(self._t("grp_rename", "Renommer le dossier…"), lambda: self._rename_folder(item))
            menu.addAction(self._t("grp_remove", "Supprimer le dossier"), lambda: self._remove_folder(item))
        menu.exec(self.viewport().mapToGlobal(point))

    def _ask(self, title, value=""):
        name, ok = QInputDialog.getText(self, self._t("grp_folder", "Dossier"), title, text=value)
        return name.strip() if ok else None

    def new_folder(self):
        """«Nouveau dossier» -- the button at the right of the pane's title, and the right-button menu's first entry."""
        self._new_folder()

    def _new_folder(self):
        name = self._ask(self._t("grp_new_prompt", "Nom du dossier :"))
        if not name:
            return
        if name in self._existing():
            notices_ui.tell(self._t("grp_taken", "Ce dossier existe déjà."), notifications.WARNING, key="grp_taken", title_key="grp_folder", source="grouped_list")
            return
        self._empty.append(name)
        self._dropped.discard(name)
        self._expanded.add(name)
        self.foldersChanged.emit()

    def _rename_folder(self, item):
        old = item.data(0, GROUP_ROLE)
        name = self._ask(self._t("grp_rename_prompt", "Nouveau nom :"), old)
        if not name or name == old:
            return
        if name in self._existing():
            notices_ui.tell(self._t("grp_taken", "Ce dossier existe déjà."), notifications.WARNING, key="grp_taken", title_key="grp_folder", source="grouped_list")
            return
        self._empty = [name if n == old else n for n in self._empty]
        self._dropped.add(old)
        self._dropped.discard(name)
        self._expanded.discard(old)
        self._expanded.add(name)
        held = [e["id"] for e in self._entries if (e.get("group") or ROOT_GROUP) == old]
        if held:
            if name not in self._empty:
                self._empty.append(name)     # kept by the next fill, in use or not
            if self._folders_kept():
                self._order[1].set_group(self._order[0], held, name)
                self.foldersChanged.emit()
            else:
                self.moved.emit(held, name)     # the tab writes the field and rebuilds
        else:
            self.foldersChanged.emit()

    def _remove_folder(self, item):
        """Removing a folder never removes what is in it: its entries go back to the root."""
        name = item.data(0, GROUP_ROLE)
        held = [e["id"] for e in self._entries if (e.get("group") or ROOT_GROUP) == name]
        self._empty = [n for n in self._empty if n != name]
        self._dropped.add(name)
        self._expanded.discard(name)
        if held and self._folders_kept():
            self._order[1].set_group(self._order[0], held, ROOT_GROUP)
            self.foldersChanged.emit()
        elif held:
            self.moved.emit(held, ROOT_GROUP)
        else:
            self.foldersChanged.emit()

    def _folders_kept(self):
        """Whether the folders are kept by the store of the order rather than in the tab's sources (attach_order's `groups`)."""
        return self._order is not None and self._order[2]

    def _existing(self):
        """The folder names taken -- «Archives» among them, so no folder of the project is mistaken for the shelf."""
        return {e.get("group") or ROOT_GROUP for e in self._entries} | set(self._empty) | {self.archives_name()}


# The key «Archives» keeps its open or closed state under, which no folder name can be.
ARCHIVES_KEY = "\x00archives"


# A folder with a plus: the new-folder button's own symbol, in the palette's ink so it reads on Windows' dark theme as well as on its light one.
FOLDER_PLUS_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
    '<path d="M2.5 6.5 h7 l2 2 h10 v11.5 h-19 z" fill="none" stroke="{ink}" stroke-width="1.6" stroke-linejoin="round"/>'
    '<path d="M12 11 v7 M8.5 14.5 h7" stroke="{ink}" stroke-width="1.8" stroke-linecap="round"/></svg>'
)


def title_row(heading, grouped, size=20):
    """The pane's title with the «new folder» button at its far right -- where the engineer asked for it: the right-button menu alone was a way to make a folder nobody found.

    `heading` is the tab's own title label, `grouped` the GroupedList the button makes a folder in.
    """
    row = QWidget()
    line = QHBoxLayout(row)
    line.setContentsMargins(0, 0, 0, 0)
    line.addWidget(heading, 1)
    button = QToolButton()
    button.setAutoRaise(True)
    ink = grouped.palette().windowText().color().name()
    button.setIcon(svg_icons.svg_icon(FOLDER_PLUS_SVG.replace("{ink}", ink), size))
    button.setIconSize(QSize(size, size))
    button.setToolTip(grouped._t("grp_new", "Nouveau dossier…"))
    button.clicked.connect(grouped.new_folder)
    line.addWidget(button)
    row.new_folder_button = button
    return row


# The five words the widget says for itself, merged into each tab's STRINGS under the `grp_` prefix
# (`cn_`, `plan_`, `st_`, `ref_` and `cmd_` are taken, and a key defined twice is silently taken by
# whichever module merges last -- which `_check_strings` cannot see).
STRINGS = {
    "fr": {
        "grp_folder": "Dossier",
        "grp_new": "Nouveau dossier…",
        "grp_new_prompt": "Nom du dossier :",
        "grp_rename": "Renommer le dossier…",
        "grp_rename_prompt": "Nouveau nom :",
        "grp_remove": "Supprimer le dossier",
        "grp_taken": "Ce dossier existe déjà.",
        "grp_archives": "Archives",
        "grp_archives_tip": "Les fichiers supprimés. Glisser un fichier hors d'ici le restaure ; clic droit pour le supprimer définitivement.",
        "grp_archived_tip": "Ancien identifiant : {id} · archivé le {at}.\nGlisser dans un dossier pour le restaurer.",
        "grp_archive_confirm": "« {ids} » ira dans « Archives » : son identifiant est retiré, et les appels Typst qui l'utilisent ne fonctionneront plus. Continuer ?",
        "grp_archived_status": "{count} fichier(s) déplacé(s) dans « Archives ».",
        "grp_restored_status": "Restauré sous « {ids} ».",
        "grp_restore": "Restaurer",
        "grp_purge": "Supprimer définitivement…",
        "grp_purge_confirm": "Supprimer définitivement {count} fichier(s) archivé(s) ? Cette action est irréversible.",
    },
    "de": {
        "grp_folder": "Ordner",
        "grp_new": "Neuer Ordner…",
        "grp_new_prompt": "Name des Ordners:",
        "grp_rename": "Ordner umbenennen…",
        "grp_rename_prompt": "Neuer Name:",
        "grp_remove": "Ordner löschen",
        "grp_taken": "Dieser Ordner besteht bereits.",
        "grp_archives": "Archiv",
        "grp_archives_tip": "Die gelöschten Dateien. Eine Datei hier herausziehen stellt sie wieder her; Rechtsklick löscht sie endgültig.",
        "grp_archived_tip": "Frühere ID: {id} · archiviert am {at}.\nIn einen Ordner ziehen, um sie wiederherzustellen.",
        "grp_archive_confirm": "«{ids}» kommt ins «Archiv»: die ID wird entfernt, und Typst-Aufrufe, die sie verwenden, funktionieren nicht mehr. Fortfahren?",
        "grp_archived_status": "{count} Datei(en) ins «Archiv» verschoben.",
        "grp_restored_status": "Wiederhergestellt als «{ids}».",
        "grp_restore": "Wiederherstellen",
        "grp_purge": "Endgültig löschen…",
        "grp_purge_confirm": "{count} archivierte Datei(en) endgültig löschen? Dies kann nicht rückgängig gemacht werden.",
    },
    "en": {
        "grp_folder": "Folder",
        "grp_new": "New folder…",
        "grp_new_prompt": "Folder name:",
        "grp_rename": "Rename folder…",
        "grp_rename_prompt": "New name:",
        "grp_remove": "Remove folder",
        "grp_taken": "That folder already exists.",
        "grp_archives": "Archives",
        "grp_archives_tip": "The deleted files. Dragging a file out of here restores it; right-click to delete it for good.",
        "grp_archived_tip": "Former ID: {id} · archived on {at}.\nDrag into a folder to restore it.",
        "grp_archive_confirm": "“{ids}” will go to “Archives”: its ID is removed, and the Typst calls using it will stop working. Continue?",
        "grp_archived_status": "{count} file(s) moved to “Archives”.",
        "grp_restored_status": "Restored as “{ids}”.",
        "grp_restore": "Restore",
        "grp_purge": "Delete for good…",
        "grp_purge_confirm": "Delete {count} archived file(s) for good? This cannot be undone.",
    },
}
