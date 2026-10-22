"""SchemaTab's draft opened and shown in the form, the options of «Surfacique», and the lists of the elements, aids, fasteners and dimensions -- a mixin of methods moved verbatim out of calc/tools/schema_tab.py (issue #30). SchemaTab names it among its bases.
"""

import json
from PySide6.QtCore import QByteArray, QEvent, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QKeySequence, QPainter, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QSpinBox, QSplitter, QTabWidget,
    QTableWidget, QTableWidgetItem, QToolButton, QVBoxLayout, QWidget,
)
import grouped_list
import project  # where the project this tab works on is (calc/project.py)
import linkable_spin  # the export's values, which a text's variables print (issue #43)
import theme  # the colours this tab states itself (theme.py, v0.90)
import validation
from domains import connector as connector_model  # the one reader of the exported positions (known_positions)
from domains import figure_style  # which factors an entry of a schema may state over the drawing's (figure_style.py, v0.99)
from domains import schema as model


# The row that stands for the draft nobody has saved yet -- statics_tab's own sentinel, and for the same reason: ID_PATTERN allows no angle bracket, so it can collide with no id.
from source_editor import NEW_ROW  # the list's row of the draft, the one constant (spec 2026-10-20-indices-et-niveaux, ARCH-005)


def list_schemas():
    """(id, label, folder) for every saved schema, in file-name order -- read off the sources, never off data/, so a schema shows here the moment it is written."""
    out = []
    for path in model.source_paths(project.current().details_dir):
        try:
            source = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        out.append((path.stem, source.get("name") or source.get("label", ""), grouped_list.group_of(source)))
    return out


def next_free_id(taken):
    lower = {t.lower() for t in taken}
    n = 1
    while f"D{n:02d}".lower() in lower:
        n += 1
    return f"D{n:02d}"


def _as_number(text):
    try:
        return float(str(text).strip().replace(",", "."))
    except (TypeError, ValueError):
        return None


class SchemaDraftMixin:
    """Methods of schema_tab.SchemaTab, moved verbatim (issue #30): the class names this mixin among its bases."""

    def open_source(self, source, current_id, dirty):
        self.loading = True
        model.upgrade_source(source)   # a 1.0 file's `width` becomes the side its view shows (v0.75)
        self.positions = connector_model.known_positions(project.current().data_dir)
        self.canvas.positions = self.positions
        # the export's values, which a text's variables print (issue #43): read as the schema opens, as a linked field's are
        self.values = linkable_spin.current_values()
        self.canvas.values = self.values
        self.fill_positions()
        self.source = source
        self.current_id = current_id
        self.dirty = dirty
        self.init_history()
        self.canvas.set_source(self.source)
        self.fill_form()
        self.fill_tables()
        self.loading = False
        self.update_calls()
        self.update_warnings()
        self.update_list_marker()
        self.on_selection()

    def load(self, sid):
        try:
            source = json.loads((project.current().details_dir / f"{sid}.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            # a sentence and the file's name, as the other editors say it (periodic audit 260916, AUD-4-6)
            self.app.set_status(self.t("sc_unreadable", name=f"{sid}.json", error=exc))
            return
        # a 1.0 file is opened as 1.1 (open_source upgrades it), and so is not dirty: its drawing is unchanged
        self.open_source(source, sid, False)

    def load_first(self):
        saved = list_schemas()
        if saved:
            self.load(saved[0][0])
            self.reload_list(select=saved[0][0])
        else:
            self.open_source(model.new_source(next_free_id([])), None, False)
            self.reload_list()

    def fill_form(self):
        self.identity.fill(self.source.get("name", ""), self.source.get("label", ""), self.source.get("id", ""),
                           saved=self.current_id is not None)
        own = self.source.get("style") or {}
        for key, slider in self.style_sliders.items():
            slider.setValue(int(round(100 * float(own.get(key, 1.0)))))
        self.update_crop_text()

    def on_style(self, key, value):
        """One of the drawing's own three factors moved. A drag is one step of «Annuler» -- the slider's `sliderPressed` pushed the state before it -- and a change with no press of its own (an arrow key) pushes its own."""
        if self.loading:
            return
        factor = round(value / 100.0, 2)
        if float((self.source.get("style") or {}).get(key, 1.0)) == factor:
            return
        if not self.style_sliders[key].isSliderDown():
            self.remember()
        self.source.setdefault("style", {})[key] = factor
        self.after_style()

    def on_entry_style(self, key, factor):
        """A factor stated on the entry selected: a factor multiplying the drawing's, written on the entry, as one step of «Annuler». It stays written over until «Reprendre» -- setting the slider back to 100 % states 1 and is still an override, which is the b/h rule of v0.75."""
        collection, entry = self.canvas.selected()
        if self.loading or entry is None:
            return
        if float((entry.get("style") or {}).get(key, 0.0)) == round(factor, 2) and key in (entry.get("style") or {}):
            return
        if not self.entry_style.rows[key]["slider"].isSliderDown():
            self.remember()
        entry.setdefault("style", {})[key] = round(factor, 2)
        self.after_style(entry)

    def take_back_style(self, key):
        """«Reprendre»: the entry follows the drawing for that factor again, and carries no `style` at all once it states none."""
        collection, entry = self.canvas.selected()
        if entry is None or key not in (entry.get("style") or {}):
            return
        self.remember()
        entry["style"].pop(key, None)
        if not entry["style"]:
            entry.pop("style")
        self.after_style(entry)

    def after_style(self, entry=None):
        """What a factor changed asks for: the figure redrawn, the dot of unsaved changes, and the rows shown again where an override has just appeared or gone."""
        self.canvas.invalidate()
        self.mark_dirty()
        if entry is not None:
            self.fill_entry_style(entry)

    def fill_entry_style(self, entry):
        """The factors of one entry -- only those it is drawn with (figure_style.ENTRY_KEYS), orange with «Reprendre» where it states one."""
        collection, _entry = self.canvas.selected()
        may = figure_style.allowed("schema", collection or "")
        self.entry_style_box.setVisible(bool(entry is not None and may))
        if entry is not None:
            self.entry_style.fill(entry, may)

    def form_row(self, label, widget):
        """One row of the selection's form, kept so that it can be shown and hidden with what is selected: (label, widget)."""
        caption = QLabel(label)
        self.selection_form.addRow(caption, widget)
        return caption, widget

    def on_area_combo(self, _index=None):
        """The tool bar's drawing mode chosen: the canvas draws by it, and the option in the right pane shows the same one."""
        mode = self.area_combo.currentData()
        self.canvas.set_area_mode(mode)
        combo = getattr(self, "tool_mode_combo", None)
        if combo is not None and combo.currentData() != mode:
            combo.blockSignals(True)
            combo.setCurrentIndex(max(combo.findData(mode), 0))
            combo.blockSignals(False)

    def on_tool_mode(self, _index=None):
        """The drawing mode chosen in the right pane: it is the tool bar's -- one value behind the two controls."""
        mode = self.tool_mode_combo.currentData()
        if self.area_combo.currentData() != mode:
            self.area_combo.setCurrentIndex(max(self.area_combo.findData(mode), 0))   # on_area_combo tells the canvas

    def on_tool_changed(self, tool):
        """The options of «Surfacique» are in the right pane while it is the tool, and only then."""
        on = tool == "area"
        self.tool_box.setVisible(on)
        if on:
            self.fill_tool_positions()
            self.update_area_fixed()

    def fill_tool_positions(self):
        """The position the next element is of, offered from the very list the selection's combo offers (fill_positions): the one summary line of a position is written once."""
        combo = self.tool_position_combo
        combo.blockSignals(True)
        combo.clear()
        for i in range(self.position_combo.count()):
            combo.addItem(self.position_combo.itemText(i), self.position_combo.itemData(i))
        combo.setCurrentIndex(max(combo.findData(self.canvas.element_position or ""), 0))
        combo.blockSignals(False)

    def on_tool_position(self, _index=None):
        self.canvas.element_position = self.tool_position_combo.currentData() or ""   # the one the next element drawn is given, as the selection's combo sets it
        self.update_area_fixed()

    def update_area_fixed(self, _index=None):
        """What the position chosen fixes of an area element (schema.area_fixed): which dimension is drawn -- chosen here for a rectangular section, a section with one dimension fixing that one --, and the words saying which is the position's. Nothing is recomputed here: the canvas is given (the dimension drawn, the fixed length) and draws by it."""
        pid = self.canvas.element_position or ""
        record = self.positions.get(pid) if pid else None
        fixed = model.area_fixed(record, self.tool_draw_combo.currentData() or "b") if record else None
        self.canvas.area_fixed = (fixed["draw"], fixed["length"]) if fixed else None
        two = fixed is not None and fixed["fixed"] in ("b", "h")
        self.tool_draw_caption.setVisible(two)
        self.tool_draw_combo.setVisible(two)
        if not pid:
            words = self.t("sc_fixed_free")
        elif fixed is None:
            words = self.t("sc_fixed_none")
        else:
            words = self.t(f"sc_fixed_{fixed['fixed']}", length=model.fmt_number(fixed["length"]))
        self.tool_fixed_note.setText(words)
        self.canvas.update_helpers()

    def fill_positions(self):
        """The position combo: «(aucune)», then every exported position with what it is -- «T001 — Träger C24 100/200 mm» -- the list the plan asked a piece's number to be chosen from."""
        self.position_combo.blockSignals(True)
        self.position_combo.clear()
        self.position_combo.addItem(self.t("sc_position_none"), "")
        for pid, record in self.positions.items():
            summary = " ".join(part for part in (record.get("type", ""), record.get("material", ""), record.get("strength_class", ""),
                                                 connector_model.position_dimension(record)) if part)
            self.position_combo.addItem(f"{pid} — {summary}" if summary else pid, pid)
        self.position_combo.blockSignals(False)
        if hasattr(self, "tool_position_combo"):
            self.fill_tool_positions()          # the options of «Surfacique» offer the same list
            self.update_area_fixed()            # and a position whose dimension changed fixes the new one

    def update_crop_text(self):
        crop = self.source.get("crop")
        if isinstance(crop, dict):
            self.crop_text.setText(self.t("sc_crop_text", w=model.fmt_number(crop["w"]), h=model.fmt_number(crop["h"]),
                                          x=model.fmt_number(crop["x"]), z=model.fmt_number(crop["z"])))
        else:
            self.crop_text.setText(self.t("sc_crop_none"))

    def on_identity(self):
        """Nom, Description or ID typed: one step of «Annuler» per change, as every field of this tab. The description is the source's `label`, which is what the report's caption prints."""
        if self.loading:
            return
        name, description, sid = self.identity.values()
        if (name, description, sid) == (self.source.get("name", ""), self.source.get("label", ""), self.source.get("id", "")):
            return
        self.remember()
        if name:
            self.source["name"] = name
        else:
            self.source.pop("name", None)
        self.source["label"] = description
        self.source["id"] = sid
        self.mark_dirty()
        self.update_calls()

    def set_field(self, key, value):
        """One field of the schema itself. An empty `group` is removed rather than written as "": absent and empty both read as the root, and a file says so with the field gone (grouped_list.py)."""
        if self.loading:
            return
        self.remember()
        if key == "group" and not value:
            self.source.pop(key, None)
        else:
            self.source[key] = value
        self.mark_dirty()
        self.update_calls()

    def mark_dirty(self):
        self.dirty = True
        self.update_list_marker()

    def rows_of(self, which):
        source = self.source
        if which == "linear":
            return [e for e in source["elements"] if e.get("kind") == "linear"]
        if which == "area":
            return [e for e in source["elements"] if e.get("kind") == "area"]
        if which == "connectors":
            return list(source["connectors"])
        if which == "points":
            return [a for a in source["aids"] if a.get("kind") == "point"]
        if which == "aids":
            return [a for a in source["aids"] if a.get("kind") != "point"]
        return list(source["dimensions"])

    def collection_of(self, which):
        return {"linear": "elements", "area": "elements", "connectors": "connectors",
                "points": "aids", "aids": "aids", "dims": "dimensions"}[which]

    def fill_tables(self):
        self.loading = True
        for which, _key, _columns in self.TABLE_SPECS:
            table = self.table_widgets[which]
            rows = self.rows_of(which)
            table.setRowCount(len(rows))
            for r, entry in enumerate(rows):
                section = model.element_section(entry, self.positions) if which in self.SIDE_COLUMNS else None
                for c, text in enumerate(self.cells_of(which, entry)):
                    item = QTableWidgetItem(text)
                    if c in self.READ_ONLY.get(which, ()):
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    side = self.SIDE_COLUMNS.get(which, {}).get(c)
                    if side is not None and section[f"{side}_from"] == "stated":
                        item.setForeground(QColor(theme.colour("override")))
                    key = self.CHECK_COLUMNS.get((which, c))
                    if key is not None:
                        # «visible» is a check box since v0.75, where it was a «1»/«0» typed into a cell; «connecteur» since v0.77
                        item.setFlags((item.flags() | Qt.ItemFlag.ItemIsUserCheckable) & ~Qt.ItemFlag.ItemIsEditable)
                        default = entry.get("kind") in model.AID_POINT_KINDS if key == "shown" else False
                        item.setCheckState(Qt.CheckState.Checked if entry.get(key, default) else Qt.CheckState.Unchecked)
                    if (which, c) == self.SHOW_COLUMN:
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        table.setCellWidget(r, c, self.show_combo(entry))
                    table.setItem(r, c, item)
            self.table_columns[which].fit()
        self.loading = False

    def show_combo(self, entry):
        """What a dimension writes beside itself, as a combo of the four -- in its list's cell and in the panel alike."""
        combo = QComboBox()
        for value, key in zip(model.LABEL_MODES, self.SHOW_KEYS):
            combo.addItem(self.t(key), value)
        combo.setCurrentIndex(max(combo.findData(model.dimension_show(entry)), 0))
        combo.currentIndexChanged.connect(lambda _i, c=combo, eid=entry["id"]: self.set_dimension_show(eid, c.currentData()))
        return combo

    def set_dimension_show(self, eid, mode):
        """A dimension's `show` chosen, from its list or its panel: one step of «Annuler». Written whatever it is, the choice being made -- a dimension stating none reads as it was drawn before it could be chosen (schema.dimension_show)."""
        if self.loading:
            return
        entry = model.entry_of(self.source, "dimensions", eid)
        if entry is None or entry.get("show") == mode:
            return
        self.remember()
        entry["show"] = mode
        self.mark_dirty()
        self.canvas.invalidate()
        self.fill_tables()
        self.update_calls()
        self.update_warnings()
        self.on_selection()

    def cells_of(self, which, entry):
        if which in ("linear", "area"):
            points = " ; ".join(f"{model.fmt_number(p[0])}/{model.fmt_number(p[1])}"
                                for p in entry.get("points", []))
            section = model.element_section(entry, self.positions)
            sides = ["" if section[side] is None else model.fmt_number(section[side]) for side in model.ELEMENT_SIDES]
            if which == "linear":
                return [entry["id"], entry.get("position", ""), entry.get("view", "h"), *sides, points]
            return [entry["id"], entry.get("position", ""), *sides, points]
        if which == "connectors":
            diameter = (entry.get("diameter") or {}).get("value")
            return [entry["id"], entry.get("kind", ""), model.fmt_number(entry.get("x", 0)),
                    model.fmt_number(entry.get("z", 0)),
                    "" if diameter is None else model.fmt_number(diameter)]
        if which == "points":
            return [entry["id"], model.fmt_number(entry.get("x", 0)), model.fmt_number(entry.get("z", 0)), "", "",
                    entry.get("label", "")]
        if which == "aids":
            at = model.aid_point(entry)
            return [entry["id"], entry.get("kind", ""),
                    model.fmt_number(entry.get("x", at[0] if at else 0)),
                    model.fmt_number(entry.get("z", at[1] if at else 0)),
                    "" if "angle" not in entry else model.fmt_number(entry["angle"], 1),
                    ""]   # the check box is the cell's state, not its text (fill_tables)
        value, unit = model.dimension_value(self.source, entry)
        return [entry["id"], entry.get("kind", ""), model.fmt_number(entry.get("offset", 0)),
                "?" if value is None else f"{model.fmt_number(value)} {unit}".strip(),
                entry.get("label", ""),
                ""]   # the combo is the cell's widget, not its text (fill_tables)

    def on_cell(self, which, item):
        """A cell typed into: the value is read, and a cell that cannot be read keeps its old one and says so (statics_tab's own rule)."""
        if self.loading:
            return
        rows = self.rows_of(which)
        if item.row() >= len(rows):
            return
        entry = rows[item.row()]
        text = item.text().strip()
        column = item.column()
        ok = True
        self.remember()
        if column == 0:
            try:
                model.rename(self.source, self.collection_of(which), entry["id"], text)
            except validation.ValidationError as exc:
                self.app.set_status(str(exc))
                ok = False
        elif which == "linear" and column == 1 or which == "area" and column == 1:
            entry["position"] = text
        elif which == "linear" and column == 2:
            ok = text in model.ELEMENT_VIEWS
            if ok:
                entry["view"] = text
        elif column in self.SIDE_COLUMNS.get(which, {}):
            side = self.SIDE_COLUMNS[which][column]
            if not text:
                entry.pop(side, None)     # emptied: the side follows its position again
            else:
                value = _as_number(text)
                ok = value is not None and value > 0
                if ok:
                    entry[side] = value
        elif which == "connectors" and column in (2, 3):
            value = _as_number(text)
            ok = value is not None
            if ok:
                entry["x" if column == 2 else "z"] = value
        elif which == "connectors" and column == 4:
            if not text:
                entry.pop("diameter", None)
            else:
                value = _as_number(text)
                ok = value is not None and value > 0
                if ok:
                    entry["diameter"] = {"value": value, "unit": "mm"}
        elif which == "points" and column in (1, 2):
            value = _as_number(text)
            ok = value is not None
            if ok:
                entry["x" if column == 1 else "z"] = value
        elif which == "points" and column == 5:
            # the name printed beside the point, draggable like any label (section 3.3decies; periodic audit 260916, AUD-7-310)
            if text:
                entry["label"] = text
            else:
                entry.pop("label", None)
                entry.pop("label_offset", None)
        elif (which, column) in self.CHECK_COLUMNS:
            entry[self.CHECK_COLUMNS[(which, column)]] = item.checkState() == Qt.CheckState.Checked
        elif which == "aids" and column in (2, 3):
            value = _as_number(text)
            ok = value is not None
            if ok:
                entry["x" if column == 2 else "z"] = value
        elif which == "aids" and column == 4:
            value = _as_number(text)
            ok = value is not None and "angle" in entry
            if ok:
                entry["angle"] = value
        elif which == "dims" and column == 2:
            value = _as_number(text)
            ok = value is not None
            if ok:
                entry["offset"] = value
        elif which == "dims" and column == 4:
            entry["label"] = text
        item.setBackground(QColor(theme.colour("danger-soft")) if not ok else QColor(0, 0, 0, 0))
        if not ok:
            # the step remember() took changes nothing: take it back, so «Annuler» does not undo a refusal
            if self.undo_stack:
                self.undo_stack.pop()
            return
        self.mark_dirty()
        self.canvas.invalidate()
        self.fill_tables()
        self.update_calls()
        self.update_warnings()
        self.on_selection()

    def on_table_selection(self, which):
        table = self.table_widgets[which]
        rows = self.rows_of(which)
        if self.loading:
            return
        collection = self.collection_of(which)
        picked = []
        current = table.currentRow()
        for index in sorted({i.row() for i in table.selectedIndexes()}):
            if 0 <= index < len(rows):
                pair = (collection, rows[index]["id"])
                # The row the engineer last clicked is the focused one, so it leads.
                picked.insert(0, pair) if index == current else picked.append(pair)
        if not picked:
            return
        from PySide6.QtWidgets import QApplication
        if QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier:
            # Ctrl in a list keeps what the OTHER lists hold selected: a table holds one collection, and «Trancher»
            # needs an element and a construction line together (v0.75)
            picked += [pair for pair in self.canvas.selection_ids() if pair[0] != collection and pair not in picked]
        self.from_table = True
        self.canvas.select_many(picked)
        self.from_table = False
