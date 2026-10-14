# -*- coding: utf-8 -*-
"""The export sheets' list of the tabs of plans (v0.116, docs/ui/window.md §10quater): the sheets, and the PDF bundles that look like folders.

A **PDF bundle** (calc/sheets.py, Plans/bundles.json) gathers sheets into one extra multi-page PDF, the pages in the order the sheets stand in it. It is shown as a folder of the list -- the wood-coloured icon, semibold, a click opening and shutting it, the very look WP-A gave grouped_list.GroupedList -- and its sheets stand beneath it, in the bundle's order. A sheet in no bundle stands at the root. The widget *is* a GroupedList: a bundle is a «folder», a sheet an «entry», and what is a field there (a folder is a `group` string) is written to bundles.json here.

What differs from the plans' list:

- **A folder is a bundle, and it is persisted by the tab**: making, renaming and removing one are signals (`bundleCreateRequested`, `bundleRenameRequested`, `bundleDeleteRequested`) the tab answers with calc/sheets.py's create/rename/delete, never GroupedList's own «empty folder» bookkeeping, which the project file keeps for the plans.
- **A drop says where in the bundle**: `sheetsMoved(moves, target, before)` -- `moves` the (sheet, bundle it came from) of every sheet dragged, `target` the bundle dropped into ("" for the root), `before` the sheet they were dropped above (None at the end) -- since a bundle's order is its pages' order. A multiple selection is dragged whole, as in every list.
- **No «Archives» row**: a sheet deleted goes to Plans/archives and is not restored from here.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QAbstractItemView

from grouped_list import ARCHIVE_KINDS, GROUP_ROLE, ID_ROLE, KIND_ROLE, ROOT_GROUP, GroupedList


class SheetList(GroupedList):
    """The export sheets, the PDF bundles as folders (module docstring)."""

    sheetsMoved = Signal(object, str, object)       # ([(sheet, from bundle)], target bundle or "", before sheet or None)
    bundleCreateRequested = Signal(str)
    bundleRenameRequested = Signal(str, str)
    bundleDeleteRequested = Signal(str)

    def __init__(self, strings=None, parent=None, lang=None):
        super().__init__(strings, parent, lang)
        self.setAcceptDrops(True)

    # --- contents -------------------------------------------------------------

    def set_sheets(self, sheet_ids, bundles, select=None):
        """`sheet_ids` every sheet of the tab's kind, `bundles` {name, sheets} in the file's order: the bundles as folders holding their sheets in order, the sheets in no bundle at the root. A bundle the file no longer names disappears even when it is empty."""
        names = [b["name"] for b in bundles]
        known = set(sheet_ids)
        entries, held = [], set()
        for bundle in bundles:
            for sid in bundle["sheets"]:
                if sid in known:
                    entries.append({"id": sid, "text": sid, "group": bundle["name"]})
                    held.add(sid)
        entries.extend({"id": sid, "text": sid, "group": ROOT_GROUP} for sid in sheet_ids if sid not in held)
        previous = {e.get("group") or ROOT_GROUP for e in self._entries} | set(self._empty)
        self._dropped = previous - set(names) - {ROOT_GROUP}     # set_entries keeps a folder the previous contents used: here the file decides
        self.set_entries(entries, empty_folders=names, select=None)
        for index in range(self.topLevelItemCount() - 1, -1, -1):  # no «Archives» row
            if self.topLevelItem(index).data(0, KIND_ROLE) == "archives":
                self.takeTopLevelItem(index)
        tip = self._t("se_bundle_tip", "")
        for item in self._items(("folder",)):
            if tip:
                item.setToolTip(0, tip.format(name=item.data(0, GROUP_ROLE)))
        if select:
            self.select(select)

    def select_folder(self, name):
        """The bundle `name`'s folder made the current item -- after a write rebuilt the list. False where there is none."""
        for item in self._items(("folder",)):
            if item.data(0, GROUP_ROLE) == name:
                self.setCurrentItem(item)
                return True
        return False

    def bundle_names(self):
        return [item.data(0, GROUP_ROLE) for item in self._items(("folder",))]

    def bundle_sheets(self, name):
        """The sheets under bundle `name`, in the order shown."""
        for item in self._items(("folder",)):
            if item.data(0, GROUP_ROLE) == name:
                return [item.child(i).data(0, ID_ROLE) for i in range(item.childCount())]
        return []

    def root_sheets(self):
        return [item.data(0, ID_ROLE) for item in self._items(("leaf",)) if not item.data(0, GROUP_ROLE)]

    def chosen_bundle(self):
        """The bundle chosen: the folder current, or the one the current sheet stands in; None at the root."""
        item = self.currentItem()
        if item is None:
            return None
        if item.data(0, KIND_ROLE) == "folder":
            return item.data(0, GROUP_ROLE)
        return item.data(0, GROUP_ROLE) or None

    # --- the drop: where in the bundle -----------------------------------------

    def dropEvent(self, event):
        """Where the drop landed, said as `sheetsMoved`; the tree itself is left alone, the tab rebuilds it from bundles.json."""
        point = event.position().toPoint() if hasattr(event, "position") else event.pos()
        target = self.itemAt(point)
        below = self.dropIndicatorPosition() == QAbstractItemView.DropIndicatorPosition.BelowItem
        event.setDropAction(Qt.DropAction.IgnoreAction)
        event.accept()
        self.drop_on(target, below)

    def drop_on(self, target, below=False):
        """The selected sheets dropped on `target` (a row, or None for the empty part of the list): at the end of a bundle dropped on, above a sheet of a bundle -- below it where `below` -- and at the root otherwise."""
        chosen = {id(i) for i in self.selectedItems()}
        moves = [(i.data(0, ID_ROLE), i.data(0, GROUP_ROLE) or ROOT_GROUP) for i in self._items(("leaf",)) if id(i) in chosen]
        if not moves:
            return
        kind = target.data(0, KIND_ROLE) if target is not None else None
        if kind in ARCHIVE_KINDS:
            return
        before = None
        if target is None:
            group = ROOT_GROUP
        elif kind == "folder":
            group = target.data(0, GROUP_ROLE)
        else:
            group = target.data(0, GROUP_ROLE) or ROOT_GROUP
            if group:
                before = self.insertion(target, below, {sid for sid, _src in moves})   # the kernel's own, which every ordered list reads (issue #15)
        self.sheetsMoved.emit(moves, group, before)

    # --- the bundles are the folders: what the menu and the button at the title's end ask -----------

    def _new_folder(self):
        name = self._ask(self._t("grp_new_prompt", ""))
        if name:
            self.bundleCreateRequested.emit(name)

    def _rename_folder(self, item):
        old = item.data(0, GROUP_ROLE)
        name = self._ask(self._t("grp_rename_prompt", ""), old)
        if name and name != old:
            self.bundleRenameRequested.emit(old, name)

    def _remove_folder(self, item):
        self.bundleDeleteRequested.emit(item.data(0, GROUP_ROLE))

    def _menu(self, point):
        """The right-button menu: new bundle; on one, rename and delete."""
        from PySide6.QtWidgets import QMenu
        item = self.itemAt(point)
        menu = QMenu(self)
        menu.addAction(self._t("grp_new", ""), self._new_folder)
        if item is not None and item.data(0, KIND_ROLE) == "folder":
            menu.addAction(self._t("grp_rename", ""), lambda: self._rename_folder(item))
            menu.addAction(self._t("grp_remove", ""), lambda: self._remove_folder(item))
        menu.exec(self.viewport().mapToGlobal(point))


def bundle_strings(words):
    """GroupedList's words for the list of sheets, from sheet_editor.bundle_words: a «folder» is a PDF bundle."""
    return {
        "grp_folder": words["se_bundle"], "grp_new": words["se_bundle_new"], "grp_new_prompt": words["se_bundle_name_prompt"],
        "grp_rename": words["se_bundle_rename"], "grp_rename_prompt": words["se_bundle_rename_prompt"], "grp_remove": words["se_bundle_delete"],
        "se_bundle_tip": words["se_bundle_tip"],
    }
