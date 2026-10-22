"""FireTab's selection and lists -- what is selected, its rows, its area, its size, its opacity, its class or kind and where its text stands -- a mixin of methods moved verbatim out of calc/tools/fire_tab.py (issue #30). FireTab names it among its bases.
"""

from PySide6.QtCore import QItemSelectionModel, Qt
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPlainTextEdit, QPushButton,
    QSizePolicy, QSpinBox, QTabWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)
import theme  # the colours this tab states itself (theme.py)
import text_pane  # a text's pane, the four drawing engines' one (issue #43)
from drawing_tab import DrawingTab, number_text, plain_label
from domains import figure_style  # which of the factors each kind of entry may state
from domains import fire
from domains import plan_clip  # Ctrl+C and Ctrl+V between fire-protection plans (issue #61)
from i18n import strings  # the German name of a fire resistance or of a kind of surface, in the window's language
from norms import vkf  # the fire resistances, the escape routes and the doors of the VKF sheet of symbols, and their colours


# The order a mixed selection is told in: the order of the plan's own drawing, surfaces first.
COLLECTION_ORDER = ("zones", "walls", "doors", "routes", "exits", "widths")


class FireTabSelectionMixin:
    """Methods of fire_tab.FireTab, moved verbatim (issue #30): the class names this mixin among its bases."""

    def selected_of(self, collection):
        """The entries of `collection` the canvas has selected, in the order they were selected, as the source's own dictionaries."""
        entries = {entry["id"]: entry for entry in self.source.get(collection, [])}
        return [entries[eid] for eid in self.canvas.selected if eid in entries]

    def selected_zones(self):
        return self.selected_of("zones")

    def selection(self):
        return {collection: self.selected_of(collection) for collection in fire.COLLECTIONS}

    def area_text(self, zone, per_m):
        area = fire.area_m2(zone, per_m)
        return None if area is None else number_text(area, 1)

    def length_text(self, entry, per_m):
        return number_text(fire.line_length(entry["points"]) / per_m, 1) if per_m else None

    def metres_text(self, metres):
        return None if metres is None else number_text(metres, 2)

    def surface_kind_text(self, zone):
        kind = zone.get("kind")
        return strings.term(vkf.escape(kind)["label"], self.app.lang) if kind in fire.SURFACES else "—"

    def door_kind_text(self, door):
        return self.t(f"fp_door_{door['kind']}") if door.get("kind") in fire.DOOR_KINDS else "—"

    def door_class_text(self, door):
        return door["class"] if door.get("class") else self.t("fp_door_plain")

    def refresh_lists(self):
        """The four lists from the source: surfaces with their kind and area, walls with their fire resistance and length, doors with theirs and their width, the escape routes' three marks with their value and text -- «—» where the plan has no scale."""
        per_m = fire.per_m(self.frame())
        right = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        previous, self.syncing = self.syncing, True

        def add(tree, eid, texts, aligned=(), icons=()):
            item = QTreeWidgetItem(texts)
            item.setData(0, Qt.ItemDataRole.UserRole, eid)
            for column in aligned:
                item.setTextAlignment(column, right)
            for column, rgb in icons:
                item.setIcon(column, self.swatch(rgb))
            tree.addTopLevelItem(item)

        try:
            for tree in self.tree_list:
                tree.clear()
            for zone in self.source.get("zones", []):
                area = self.area_text(zone, per_m)
                icons = [(1, vkf.escape(zone["kind"])["rgb"])] if zone.get("kind") in fire.SURFACES else []
                add(self.zone_tree, zone["id"], [zone["id"], self.surface_kind_text(zone), zone.get("label", ""), area if area is not None else "—"], (3,), icons)
            for wall in self.source.get("walls", []):
                length = self.length_text(wall, per_m)
                icons = [(1, vkf.resistance(wall["class"])["rgb"])] if wall["class"] in vkf.resistance_keys() else []
                add(self.wall_tree, wall["id"], [wall["id"], wall["class"], length if length is not None else "—"], (2,), icons)
            for door in self.source.get("doors", []):
                width = self.metres_text(fire.door_width_m(door, per_m))
                icons = [(2, vkf.door(door["kind"], door["class"])["rgb"])] if door.get("class") in vkf.door_classes() and door.get("kind") in fire.DOOR_KINDS else []
                add(self.door_tree, door["id"], [door["id"], self.door_kind_text(door), self.door_class_text(door), width if width is not None else "—"], (3,), icons)
            for route in self.source.get("routes", []):
                length = self.length_text(route, per_m)
                add(self.escape_tree, route["id"], [route["id"], self.t("fp_symbol_length"), length if length is not None else "—", route.get("text", "")], (2,))
            for entry in self.source.get("exits", []):
                add(self.escape_tree, entry["id"], [entry["id"], self.t("fp_symbol_exit"), "", ""], (2,))
            for entry in self.source.get("widths", []):
                width = self.metres_text(fire.width_m(entry, per_m))
                add(self.escape_tree, entry["id"], [entry["id"], self.t("fp_symbol_width"), width if width is not None else "—", entry.get("text", "")], (2,))
        finally:
            self.syncing = previous
        self.sync_rows()

    def sync_rows(self, front=False, keep=None):
        """The rows of every list are what the canvas has selected, the last one current. With `front`, the list of the entry in focus is brought to the front; `keep` is the list the engineer is working in, which is not touched."""
        previous, self.syncing = self.syncing, True
        try:
            selected = list(self.canvas.selected)
            focused = selected[-1] if selected else None
            for tree in self.tree_list:
                if tree is keep:
                    continue
                tree.clearSelection()
                tree.setCurrentItem(None)
                for index in range(tree.topLevelItemCount()):
                    item = tree.topLevelItem(index)
                    eid = item.data(0, Qt.ItemDataRole.UserRole)
                    if eid == focused:
                        tree.setCurrentItem(item, 0, QItemSelectionModel.SelectionFlag.NoUpdate)
                    item.setSelected(eid in selected)
            found = fire.entry_of(self.source, focused) if focused is not None else None
            if front and found is not None and found[0] in self.trees:   # a text (issue #43) is in no list
                self.entry_tabs.setCurrentWidget(self.trees[found[0]])
        finally:
            self.syncing = previous

    def on_rows(self, tree):
        """A row clicked in a list selects its entry on the canvas, the current row last -- and the plan's drawing is brought forward where a document or a sheet was shown."""
        if self.syncing:
            return
        if self.view_kind != "plan":
            self.show_plan_view()
        ids = [item.data(0, Qt.ItemDataRole.UserRole) for item in tree.selectedItems()]
        order = [tree.topLevelItem(i).data(0, Qt.ItemDataRole.UserRole) for i in range(tree.topLevelItemCount())]
        ids.sort(key=order.index)
        current = tree.currentItem()
        if current is not None and current.data(0, Qt.ItemDataRole.UserRole) in ids:
            focused = current.data(0, Qt.ItemDataRole.UserRole)
            ids = [i for i in ids if i != focused] + [focused]
        self.syncing = True
        try:
            self.canvas.select_ids(ids)
            self.sync_rows(keep=tree)
        finally:
            self.syncing = False

    # -- Ctrl+C and Ctrl+V (issue #61, drawing_tab_clip.py): what is the fire-protection plan's own --

    def make_clip(self, point):
        """The entries selected, taken at `point`."""
        return plan_clip.clip_fire(self.source, list(self.canvas.selected), point, self.canvas.per_m(), self.clip_root())

    def paste_clip(self, clip, point):
        """The clip put down at `point`, inside the change the caller opened, each entry with an id of its own. Returns (the ids pasted, what is said)."""
        result = plan_clip.paste_fire(self.source, clip, point, self.canvas.per_m())
        said = [self.t("plan_paste_done", n=len(result["added"]))]
        if plan_clip.ratio(clip, self.canvas.per_m()) != 1.0:
            said.append(self.t("plan_paste_scaled"))
        return result["added"], said

    def select_pasted(self, ids):
        self.canvas.select_ids(ids)

    def on_selection(self):
        if not self.syncing:
            self.sync_rows(front=True)
        self.refresh_selection()
        self.update_object_buttons()

    def show_choice(self, combo, values):
        """The combo of a card shows the choice the entries selected share, and none where they differ."""
        values = set(values)
        value = next(iter(values)) if len(values) == 1 else None
        combo.setCurrentIndex(combo.findData(value) if value is not None else -1)

    def refresh_selection(self):
        """The selection's card: a hint where nothing is selected; the kind of surfaces, and the name and area of one; the fire resistance and the length of walls; the kind, the fire resistance and the width of doors, and their two flips; the length and the text of one escape route, the width and the text of one width; and for anything else the count."""
        picked = self.selection()
        zones, walls, doors, routes, widths = (picked[collection] for collection in ("zones", "walls", "doors", "routes", "widths"))
        texts = self.selected_of("texts")
        total = sum(len(entries) for entries in picked.values()) + len(texts)
        zones_only = bool(zones) and total == len(zones)
        walls_only = bool(walls) and total == len(walls)
        doors_only = bool(doors) and total == len(doors)
        single = total == 1
        self.label_typing = False
        self.nothing_label.setVisible(total == 0)
        self.zone_box.setVisible(zones_only)
        self.single_box.setVisible(single and bool(zones))
        self.wall_box.setVisible(walls_only)
        self.door_box.setVisible(doors_only)
        self.route_box.setVisible(single and bool(routes))
        self.width_box.setVisible(single and bool(widths))
        self.several_label.setVisible(total >= 1 and not (walls_only or doors_only or (single and bool(zones or routes or widths or texts))))
        self.fill_text(texts[0] if single and texts else None)
        # a disabled button says why (v0.47's rule): none selected is none to delete
        for button in (self.delete_selection_button, self.delete_button):
            button.setEnabled(total >= 1)
            button.setToolTip(self.t("fp_delete_selection") if total >= 1 else self.t("fp_nothing_selected"))
        loading, self.loading = self.loading, True
        try:
            if zones_only:
                self.show_choice(self.zone_kind_combo, [zone.get("kind") for zone in zones])
            if single and zones:
                self.zone_label.setText(zones[0].get("label", ""))
            if walls_only:
                self.show_choice(self.class_combo, [wall["class"] for wall in walls])
            if doors_only:
                self.show_choice(self.door_kind_card_combo, [door.get("kind") for door in doors])
                self.show_choice(self.door_class_card_combo, [door.get("class", "") for door in doors])
            if single and routes:
                self.route_text_edit.setText(routes[0].get("text", ""))
            if single and widths:
                self.width_text_edit.setText(widths[0].get("text", ""))
        finally:
            self.loading = loading
        self.update_area()
        self.refresh_own()
        self.update_modules()

    def fill_text(self, entry):
        """A text's pane (issue #43, UI-004): text_pane's, the four engines' one -- built for the one text selected, taken down otherwise."""
        while self.text_layout.count():
            widget = self.text_layout.takeAt(0).widget()
            if widget is not None:
                widget.deleteLater()
        self.text_pane = None
        self.text_holder.setVisible(entry is not None)
        if entry is not None:
            self.text_pane = text_pane.TextPane(entry, lambda: self.app, self.app.lang, self.edit, self.refresh_selection, self.text_values(),
                                                bool(getattr(self.app, "read_only", False)))
            self.text_layout.addWidget(self.text_pane)

    def has_selection(self):
        """Something selected on the plan open, of any collection: the right pane then shows the selection's card and «Taille des symboles», and the plan's own modules no more (v0.116). The legend, dragged by its body, is no entry and selects nothing."""
        return bool(self.selected_entries())

    def update_area(self):
        """What the selection measures, in square metres or metres -- «—» and a word where the plan has no scale."""
        picked = self.selection()
        zones, walls, doors, routes, widths = (picked[collection] for collection in ("zones", "walls", "doors", "routes", "widths"))
        total = sum(len(entries) for entries in picked.values())
        per_m = fire.per_m(self.frame())
        unscaled = f"— ({self.t('fp_no_scale_short')})"
        if len(zones) == 1 and total == 1:
            area = self.area_text(zones[0], per_m)
            self.area_label.setText(self.t("fp_area_value", area=area) if area is not None else unscaled)
        elif walls and total == len(walls):
            if not per_m:
                self.wall_length_label.setText(unscaled if len(walls) == 1 else self.t("fp_several_walls_no_scale", count=len(walls)))
            elif len(walls) == 1:
                self.wall_length_label.setText(self.t("fp_length_value", length=self.length_text(walls[0], per_m)))
            else:
                everything = number_text(sum(fire.line_length(wall["points"]) for wall in walls) / per_m, 1)
                self.wall_length_label.setText(self.t("fp_several_walls", count=len(walls), length=everything))
        elif doors and total == len(doors):
            if len(doors) > 1:
                self.door_width_label.setText("—")
            else:
                width = self.metres_text(fire.door_width_m(doors[0], per_m))
                self.door_width_label.setText(self.t("fp_width_value", width=width) if width is not None else unscaled)
        elif len(routes) == 1 and total == 1:
            length = self.length_text(routes[0], per_m)
            self.route_length_label.setText(self.t("fp_length_value", length=length) if length is not None else unscaled)
            self.route_text_edit.setPlaceholderText(fire.route_text({"points": routes[0]["points"]}, per_m))
        elif len(widths) == 1 and total == 1:
            width = self.metres_text(fire.width_m(widths[0], per_m))
            self.width_label.setText(self.t("fp_width_value", width=width) if width is not None else unscaled)
            self.width_text_edit.setPlaceholderText(fire.width_text({"points": widths[0]["points"]}, per_m))
        elif total > 1 and len(zones) == total:
            if per_m:
                everything = sum(fire.area_m2(zone, per_m) for zone in zones)
                self.several_label.setText(self.t("fp_several", count=len(zones), area=number_text(everything, 1)))
            else:
                self.several_label.setText(self.t("fp_several_no_scale", count=len(zones)))
        elif total >= 1:
            detail = ", ".join(self.t(f"fp_kind_{collection}", n=len(picked[collection])) for collection in COLLECTION_ORDER if picked[collection])
            self.several_label.setText(self.t("fp_mixed", count=total, detail=detail))

    def selected_entries(self):
        """(collection, entry) of everything the canvas has selected, in the order it was selected."""
        out = []
        for eid in self.canvas.selected:
            found = fire.entry_of(self.source, eid)
            if found is not None:
                out.append((found[0], self.source[found[0]][found[1]]))
        return out

    def refresh_own(self):
        """The card of the selection's own size and opacity put in step with the selection -- without being built again, which would delete the very slider under the pointer while one is dragged."""
        chosen = self.selected_entries()
        if not chosen:
            self.own_card.setVisible(False)
            return
        collections = {collection for collection, _entry in chosen}
        may = [key for key in figure_style.KEYS if all(key in figure_style.allowed(fire.STYLE_KIND, collection) for collection in collections)]
        stated = {}
        for key in may:
            for _collection, entry in chosen:
                own = figure_style.stated(entry)
                if key in own:
                    stated[key] = own[key]
                    break
        self.entry_style.fill({"style": stated} if stated else {}, may)
        opaque = all(collection in fire.OPACITY for collection in collections)
        row = self.entry_opacity
        row["name"].setVisible(opaque)
        row["field"].setVisible(opaque)
        if opaque:
            states = [entry for _collection, entry in chosen if entry.get("opacity") is not None]
            value = float(states[0]["opacity"]) if states else fire.opacity_of(*chosen[0])
            self.own_filling = True
            try:
                row["slider"].setValue(int(round(100 * value)))
                row["readout"].setText(f"{row['slider'].value()} %")
            finally:
                self.own_filling = False
            orange = theme.colour("override")
            for widget in (row["name"], row["readout"]):
                widget.setStyleSheet(f"color: {orange};" if states else "")
            row["back"].setVisible(bool(states))
        single = len(chosen) == 1 and chosen[0][0] in fire.TEXT_COLLECTIONS
        self.text_place.setVisible(single)
        if single:
            moved = "label_offset" in chosen[0][1]
            self.text_reset_button.setVisible(moved)
            self.text_home.setVisible(not moved)
        self.own_card.setVisible(bool(may) or opaque or single)

    def set_entry_style(self, key, factor):
        """A factor the entries selected state over the plan's own: all of them, one step of «Annuler» per drag. It stays stated at 100 % -- «Reprendre» is the one way back (the b/h rule of v0.75)."""
        entries = [entry for _collection, entry in self.selected_entries()]
        if entries:
            self.edit(lambda: [entry.setdefault("style", {}).__setitem__(key, round(factor, 2)) for entry in entries])

    def take_back_entry_style(self, key):
        """«Reprendre»: that factor follows the plan's own again, on every entry selected that states it."""
        entries = [entry for _collection, entry in self.selected_entries() if key in figure_style.stated(entry)]
        if not entries:
            return

        def apply():
            for entry in entries:
                entry["style"].pop(key, None)
                if not entry["style"]:
                    entry.pop("style")
        self.edit(apply)

    def on_entry_opacity(self, value):
        if self.own_filling or self.loading:
            return
        entries = [entry for collection, entry in self.selected_entries() if collection in fire.OPACITY]
        if entries:
            self.edit(lambda: [entry.__setitem__("opacity", round(value / 100, 2)) for entry in entries])

    def take_back_opacity(self):
        entries = [entry for _collection, entry in self.selected_entries() if "opacity" in entry]
        if entries:
            self.edit(lambda: [entry.pop("opacity") for entry in entries])

    def reset_text(self):
        """The text of the one entry selected put back in its own place -- one step of «Annuler»."""
        chosen = self.selected_entries()
        if len(chosen) == 1 and "label_offset" in chosen[0][1]:
            entry = chosen[0][1]
            self.edit(lambda: entry.pop("label_offset"))

    def on_wall_class(self, _index=None):
        if self.loading:
            return
        cls = self.class_combo.currentData()
        walls = self.selected_of("walls")
        if cls is None or not walls:
            return

        def apply():
            for wall in walls:
                wall["class"] = cls
        self.edit(apply)

    def on_zone_kind(self, _index=None):
        if self.loading:
            return
        kind = self.zone_kind_combo.currentData()
        zones = self.selected_zones()
        if kind is None or not zones:
            return

        def apply():
            for zone in zones:
                zone["kind"] = kind
        self.edit(apply)

    def on_door_kind(self, _index=None):
        if self.loading:
            return
        kind = self.door_kind_card_combo.currentData()
        doors = self.selected_of("doors")
        if kind is None or not doors:
            return

        def apply():
            for door in doors:
                door["kind"] = kind
        self.edit(apply)

    def on_door_class(self, _index=None):
        if self.loading or self.door_class_card_combo.currentIndex() < 0:
            return
        cls = self.door_class_card_combo.currentData() or None
        doors = self.selected_of("doors")
        if not doors:
            return

        def apply():
            for door in doors:
                if cls is None:
                    door.pop("class", None)
                else:
                    door["class"] = cls
        self.edit(apply)

    def flip_doors(self, what):
        """The doors selected opened the other way -- "hinge" or "side" --, all of them in one step of the history, each door's own dictionary changed in place."""
        doors = self.selected_of("doors")
        if not doors:
            return

        def apply():
            for door in doors:
                flipped = fire.door_flipped(door, what)
                door.clear()
                door.update(flipped)
        self.edit(apply)

    def on_route_text(self, _text=None):
        self.type_text("routes", self.route_text_edit)

    def on_width_text(self, _text=None):
        self.type_text("widths", self.width_text_edit)

    def type_text(self, collection, field):
        if self.loading:
            return
        entries = self.selected_of(collection)
        if len(entries) != 1:
            return
        entry = entries[0]
        text = field.text().strip()

        def apply():
            if text:
                entry["text"] = text
            else:
                entry.pop("text", None)
        self.edit(apply, history=not self.label_typing)
        self.label_typing = True

    def on_zone_label(self, _text=None):
        if self.loading:
            return
        zones = self.selected_zones()
        if len(zones) != 1:
            return
        zone = zones[0]
        text = self.zone_label.text().strip()

        def apply():
            if text:
                zone["label"] = text
            else:
                zone.pop("label", None)
        self.edit(apply, history=not self.label_typing)
        self.label_typing = True

    def on_zone_label_done(self):
        self.label_typing = False
