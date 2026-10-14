"""Woodcore's «Modèles statiques» tab (docs/domain/static-models.md §3.3octies, docs/ui/window.md §10quater): where a static system is drawn -- the members, where they are held, where they are hinged, and what acts on them -- and saved, and the Typst call that prints it is copied.

A model is saved as its source, statics/<id>.json beside calc/, and exported at once by calc/domains/statics.py, the module export_all.py runs: data/statics.json and the figure under data/statics/. So data/ is still only ever written by the pipeline's own code, and the report sees the model without the load workbooks being read again. What the canvas shows is statics_svg.py's drawing, the report's own; its geometry -- what is under the pointer, where it snaps, which direction the cursor is tracking along -- is statics.py's.

Everything can be entered two ways, which is what the engineer asked for: by clicking on the grid, whose step follows the zoom and which the pointer snaps to; or by typing into the four lists -- points, members, point loads, line loads -- which sit **under** the drawing, where they are as wide as it is. A point's list carries its support and that support's angle: a support belongs to a point, and that is where one looks for it. A release belongs to an end of a member, and is set in that member's panel.

A load's magnitude is either a number typed here or a **variable of the export** -- a domain, a sheet and a var of data/calculations.json -- so the figure follows the workbook by itself. Where the action is per square metre and the system carries per metre, the load takes an **influence width b_e**: the value is multiplied by it and one metre comes off the unit, and the figure says so.

The model carries three sliders -- the strokes, the symbols placed on a node, the texts -- and since v0.99 **one entry may carry a factor of its own over them** (`style_properties`, `calc/domains/figure_style.py`): only the factors it is actually drawn with, shown the way an overridden b/h is shown, orange with «Reprendre» beside it (`stylefactors.py`).

The tab lives in its own module rather than in woodcore_gui.py, which lists it in its TABS and merges STRINGS below into its own: the window's language, shortcuts and closing rules are woodcore_gui's, the tab's texts and behaviour are here.
"""

import copy
import json
from pathlib import Path

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QKeySequence, QPainter, QPixmap, QShortcut
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPlainTextEdit,
    QPushButton, QRadioButton, QSlider, QSplitter, QTabWidget, QTableWidget,
    QTableWidgetItem, QToolButton, QVBoxLayout, QWidget,
)

import build_reference as ref
import engine
import grouped_list
import source_archive  # «Supprimer» archives (source_archive.py)
import identity
import project  # where the project this tab works on is (calc/project.py)
import theme  # the colours this tab states itself (theme.py, v0.90)
import richtext  # the calls coloured as the site's code, «Copié ✓» (richtext.py, v0.92)
import cards  # the properties in cards, after the website (cards.py, v0.95)
import display_view  # the «Affichage» view: the command, its options, the call and the page (display_view.py, v0.117)
import views  # the views the top bar's switch chooses between (views.py, v0.117)
import autosave  # saving without a question, and what is never saved without the engineer (autosave.py, v0.117)
import stylefactors  # the factors one entry states over the drawing's three, as an overridden b/h is shown (stylefactors.py, v0.99)
import validation
from domains import figure_style  # which of the three each kind of entry may state (figure_style.py, v0.99)
from domains import statics as model
from domains import statics_svg
import flowbar
import notifications  # every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # what was a message box is a notice since v0.117 (notices_ui.tell)
from flowbar import (BAR_SPACING, TOOL_ICON_PX, FlowLayout, FlowWidget, ResizableColumns, ToolBarArea,
                     pixel_ratio, set_tip, size_tool, symbol_px, tool_group)
from statics_tab_words import HINTS, STRINGS, TIPS, hint_key, tip_key  # split out of this module (issue #30): every name it had is still importable from it
from statics_tab_build import (  # split out of this module (issue #30): every name it had is still importable from it
    GRID_CHOICES,
    ICON_PX,
    MEMBER_ICONS,
    RELEASES,
    SWATCH_FILL,
    SWATCH_INK,
    TOOL_GROUPS,
    _as_number,
    _canvas,
    _fix_direction,
    _fix_kind,
    _fix_shape,
    _member_icon,
    _set_along,
    _set_angle,
    _set_number,
    _set_stiffness,
    _set_unit,
    _set_width,
    _stiffness_text,
    _width_text,
    plain_label,
    svg_icon,
    StaticsBuildMixin,
)
from statics_tab_properties import StaticsPropertiesMixin  # split out of this module (issue #30): every name it had is still importable from it

# The row that stands for the draft nobody has saved yet. Not an id anything can be filed under, so it
# cannot collide with a model's own: ID_PATTERN allows no angle bracket.
NEW_ROW = "<new>"
from statics_canvas import TOOLS, StaticsCanvas

# Every path is the current project's, asked of project.current() when it is needed (v0.81, docs/architecture/layout.md §11): the models' sources -- one file per model, written by this tab and nothing else (section 3.3octies) -- are its `statics_dir`, and the values a load may name are read from its export.

# How many steps «Annuler» can go back.
HISTORY = 200


# A cell whose content cannot be read keeps its old value and says so rather than destroying it, on theme.colour("danger-soft") (v0.90).


# The words `stylefactors.EntryRows` builds an entry's own factor rows from: it composes them out of this tab's
# prefix rather than being handed them, so they are named here, where they are defined, and checked at import --
# `app.t` raises on a key it does not have, and a word missing from one language would otherwise raise in front of
# the engineer, the moment he selected something. woodcore_gui._check_strings' own rule, for keys no literal names.
STYLE_ROW_KEYS = tuple(f"st_style_{key}" for key in figure_style.KEYS) + ("st_style_take_back",)
for _lang, _said in STRINGS.items():
    _missing = [key for key in STYLE_ROW_KEYS if key not in _said]
    if _missing:
        raise KeyError(f"statics_tab.STRINGS[{_lang!r}] is missing {_missing} -- stylefactors.EntryRows asks for them")


def list_models():
    """Every saved model, in file-name order, as (id, label, folder). The folder is the source's own `group` field (grouped_list.py)."""
    out = []
    for path in model.source_paths(project.current().statics_dir):
        try:
            source = json.loads(path.read_text(encoding="utf-8"))
            label = (source.get("name") or source.get("label", "")) if isinstance(source, dict) else ""
            out.append((path.stem, label, grouped_list.group_of(source)))
        except (OSError, ValueError):
            out.append((path.stem, "", grouped_list.ROOT_GROUP))
    return out


def next_free_id(taken):
    n = 1
    while f"S{n:02d}" in taken:
        n += 1
    return f"S{n:02d}"


class StaticsTab(StaticsPropertiesMixin, StaticsBuildMixin, display_view.DisplayTab, QWidget):
    """Draws a static model, saves it as its source, exports it, and copies the call that prints it."""

    VIEWS = views.DRAW_VIEWS   # «Dessin» and «Affichage» (views.py, v0.117)

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.t = app.t
        self.loading = False  # set while the form is being filled, so filling it is not taken for an edit
        self.dirty = False
        self.current_id = None  # the saved model the tab holds; None for one not saved yet
        self.source = model.new_source("S01")
        self.undo_stack, self.redo_stack = [], []
        self.values = model.known_values(project.current().data_dir)
        # the variable a load named before it was given a typed value, per load id -- so that changing one's mind twice does not lose it. The window's, not the source's: it is a convenience, not data.
        self.last_reference = {}
        # and the other way round: the value typed before a variable was tried, per load id (periodic audit 260916, AUD-5-9)
        self.last_literal = {}
        self.empty_folders = list(app.folder_settings("tab_statics"))   # folders holding nothing: a view preference, kept in settings.json by the window (grouped_list.py, v0.75)
        self.slider_down = False
        # the selected entry's own style rows and the factors it may state: built afresh at every selection (`style_properties`), and read back to turn a row orange without rebuilding the panel
        self.style_rows, self.style_may = None, ()
        self.from_table = False  # a selection that came from a list must not have its own cell taken back

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.build_list())
        self.splitter.addWidget(self.build_center())
        self.splitter.addWidget(self.build_properties())
        self.install_display("tab_statics")   # «Affichage»: show-static-model's options, its call and its page (v0.117)
        for index, stretch in enumerate((2, 7, 3)):
            self.splitter.setStretchFactor(index, stretch)
        layout.addWidget(self.splitter, 1)

        for sequence, slot in (
            (QKeySequence.StandardKey.Save, self.save),
            (QKeySequence.StandardKey.Undo, self.undo),
            (QKeySequence.StandardKey.Redo, self.redo),
            (QKeySequence("Ctrl+Y"), self.redo),
        ):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(slot)
        fit = QShortcut(QKeySequence("F"), self.canvas)
        fit.setContext(Qt.ShortcutContext.WidgetShortcut)
        fit.activated.connect(self.canvas.fit)

        self.restore(app.views.get("tab_statics"))

    # -- building ----------------------------------------------------------------


    # -- the form ----------------------------------------------------------------

    def width_form(self, layout, owner, use_key, on_toggle):
        """The influence width of a model or of one load: whether it applies, how wide it is, what it is called, what it is, and whether the figure says so. One form serves both, since both carry the same thing -- a load's own being the exception that overrides the model's."""
        self.clear_layout(layout)
        width = owner.get("width")
        use = QCheckBox(self.t(use_key))
        use.setChecked(width is not None)
        use.toggled.connect(on_toggle)
        layout.addWidget(use)
        if width is None:
            return
        form = cards.form()
        value = QDoubleSpinBox()
        value.setRange(0.001, 1000.0)
        value.setDecimals(3)
        value.setValue(float(width["value"]))
        value.valueChanged.connect(lambda v, w=width: self.edit(lambda: w.update(value=float(v))))
        form.addRow(self.app.label("st_width_value"), self.linked_field(value, owner, "width", model.WIDTH_UNIT, "b_e"))
        name = QLineEdit(width.get("label", model.DEFAULT_WIDTH_LABEL))
        name.editingFinished.connect(
            lambda w=width, n=name: self.edit(lambda: w.update(label=n.text().strip() or model.DEFAULT_WIDTH_LABEL))
        )
        form.addRow(self.app.label("st_width_label"), name)
        description = QLineEdit(width.get("description", ""))
        description.editingFinished.connect(lambda w=width, d=description: self.edit(lambda: w.update(description=d.text())))
        form.addRow(self.app.label("st_width_desc"), description)
        show = QCheckBox(self.t("st_width_show"))
        show.setChecked(bool(width.get("show", True)))
        show.toggled.connect(lambda on, w=width: self.edit(lambda: w.update(show=bool(on))))
        form.addRow(show)
        holder = QWidget()
        holder.setLayout(form)
        layout.addWidget(holder)

    def set_model_width(self, on):
        def apply():
            if on:
                self.source["width"] = {"value": 1.0, "unit": model.WIDTH_UNIT,
                                        "label": model.DEFAULT_WIDTH_LABEL, "description": "", "show": True}
            else:
                self.source.pop("width", None)
        self.edit(apply)
        self.fill_model_width()

    def fill_model_width(self):
        self.width_form(self.model_width_layout, self.source, "st_model_width_use", self.set_model_width)

    def fill(self):
        self.loading = True
        self.fill_model_width()
        self.identity.fill(self.source.get("name", ""), self.source.get("label", ""), self.source.get("id", ""),
                           saved=self.current_id is not None)
        for key, widget in self.style_sliders.items():
            widget.setValue(int(round(100 * float(self.source.get("style", {}).get(key, 1.0)))))
        snap = self.source.get("grid", {}).get("snap", "auto")
        index = self.grid_combo.findData(snap)
        self.grid_combo.setCurrentIndex(index if index >= 0 else 0)
        self.loading = False

    def edit(self, apply):
        """One change to the model: pushed onto the history, applied, redrawn. A change that changes nothing -- «Ajouter» with nothing to hang the entry on -- leaves no step and marks nothing (periodic audit 260916). True when something changed."""
        if self.loading:
            return False
        before = copy.deepcopy(self.source)
        self.push_history()
        apply()
        if self.source == before:
            self.undo_stack.pop()
            return False
        self.canvas.invalidate()
        self.on_changed()
        return True

    def on_identity(self):
        """Nom, Description or ID left after typing: one step of «Annuler». The description is the source's `label`, which is what the report's caption prints."""
        name, description, sid = self.identity.values()
        if self.loading or (name, description, sid) == (self.source.get("name", ""), self.source.get("label", ""), self.source.get("id", "")):
            return

        def apply():
            self.source.update(label=description, id=sid)
            if name:
                self.source["name"] = name
            else:
                self.source.pop("name", None)
        self.edit(apply)

    def on_style(self, key, value):
        if self.loading:
            return
        factor = value / 100.0
        if self.slider_down:
            self.source.setdefault("style", {})[key] = factor
            self.canvas.invalidate()
            self.dirty = True
            self.update_list_marker()
        else:
            self.edit(lambda: self.source.setdefault("style", {}).update({key: factor}))

    def on_grid(self, _index):
        choice = self.grid_combo.currentData()
        self.canvas.grid_mode = choice
        self.canvas.viewport().update()
        if not self.loading:
            self.source.setdefault("grid", {})["snap"] = choice
            self.dirty = True
            self.update_list_marker()

    def on_snap(self, checked):
        self.canvas.snap_on = checked

    def choose_tool(self, tool):
        button = self.tool_buttons.get(tool)
        if button is not None:
            button.setChecked(True)
        self.canvas.set_tool(tool)
        self.canvas.set_hint(self.t(hint_key(tool)))

    def on_refused(self, reason):
        """A click that put nothing down, said in words. The canvas knows why; the sentence is the tab's."""
        key = {
            "point": "st_refused_point",
            "member": "st_refused_member",
            "member-end": "st_refused_member_end",
            "support-taken": "st_refused_support",
            "release-taken": "st_refused_member_end",
            "dimension-ends": "st_refused_dim_ends",
            "dimension-parallel": "st_refused_dim_parallel",
            "dimension-same-member": "st_refused_dim_same_member",
        }.get(reason, "st_refused_point")
        self.app.set_status(self.t(key))
        self.message.setPlainText(self.t(key))

    def on_pointer(self, x, z, kind):
        text = self.t("st_pointer", x=model.fmt_number(x), z=model.fmt_number(z))
        if kind:
            parts = kind.split("|")
            key = "st_snap_" + parts[0].replace("-", "_")
            name = self.t(key) if key in STRINGS["fr"] else parts[0]
            if len(parts) == 3 and parts[1]:
                text += "   " + self.t("st_lock", angle=parts[1], distance=parts[2])
            text += f"   [{name}]"
        self.canvas.set_readout(text)

    # -- the four lists -----------------------------------------------------------

    def set_tables(self):
        self.loading = True
        for collection, spec in self.table_specs.items():
            table = self.table_widgets[collection]
            entries = self.source.get(collection, [])
            table.setRowCount(len(entries))
            for row, entry in enumerate(entries):
                for col, column in enumerate(spec["columns"]):
                    live = column["enabled"](entry) if "enabled" in column else True
                    if column["kind"] in ("choice", "ref"):
                        combo = QComboBox()
                        if column["kind"] == "choice":
                            for value, key in zip(column["values"], column["labels"]):
                                combo.addItem(self.t(key), value)
                            current = column["get_value"](entry) if "get_value" in column else entry.get(column["field"])
                        else:
                            combo.addItem("", "")
                            for other in self.source.get(column["of"], []):
                                combo.addItem(other["id"], other["id"])
                            current = entry.get(column["field"], "")
                        combo.setCurrentIndex(max(combo.findData(current), 0))
                        combo.setEnabled(bool(live))
                        if live is not True and isinstance(live, str):
                            combo.setToolTip(self.t(live))
                        combo.currentIndexChanged.connect(
                            lambda _i, c=collection, r=row, k=column: self.on_combo(c, r, k)
                        )
                        table.setCellWidget(row, col, combo)
                    else:
                        text = entry["id"] if column["kind"] == "id" else column["get"](entry)
                        item = QTableWidgetItem(text if live else "")
                        if column.get("readonly"):
                            # what the model measured: shown where it is read, and changed only by changing the model
                            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        if not live:
                            # a cell a row has no use for -- a uniform load's far value -- is closed rather than left to be typed into
                            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        table.setItem(row, col, item)
            self.table_columns[collection].fit()
        self.loading = False

    def on_combo(self, collection, row, column):
        if self.loading:
            return
        combo = self.table_widgets[collection].cellWidget(row, self.table_specs[collection]["columns"].index(column))
        value = combo.currentData()
        entries = self.source.get(collection, [])
        if row >= len(entries):
            return

        def apply():
            if "set_value" in column:
                column["set_value"](entries[row], value)
                return
            entries[row][column["field"]] = value
            if column.get("after"):
                column["after"](entries[row])
        self.edit(apply)
        self.set_tables()

    def read_table(self, collection):
        """Every cell of one list, read back into the source. A cell that cannot be read keeps its old value and is painted, so a half-typed number never destroys what was there."""
        if self.loading:
            return
        spec = self.table_specs[collection]
        table = self.table_widgets[collection]
        entries = self.source.get(collection, [])
        before = copy.deepcopy(self.source)
        bad = []
        for row in range(min(table.rowCount(), len(entries))):
            entry = entries[row]
            for col, column in enumerate(spec["columns"]):
                if column["kind"] in ("choice", "ref") or column.get("readonly"):
                    continue
                if "enabled" in column and not column["enabled"](entry):
                    continue
                item = table.item(row, col)
                if item is None:
                    continue
                text = item.text().strip()
                if column["kind"] == "id":
                    if text == entry["id"]:
                        continue
                    try:
                        model.rename(self.source, collection, entry["id"], text)
                    except validation.ValidationError:
                        bad.append((row, col))
                elif not column["set"](entry, text):
                    bad.append((row, col))
        self.loading = True
        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item is not None:
                    item.setBackground(QColor(theme.colour("danger-soft")) if (row, col) in bad else QColor(0, 0, 0, 0))
        self.loading = False
        if before != self.source:
            self.push_history()
            self.canvas.invalidate()
            self.on_changed(tables=False)

    def add_row(self, collection):
        """A new entry of that list. One typed here is exactly one drawn on the canvas -- a point at the origin, a member between the first two points, a load on the first point or member."""
        def apply():
            entries = self.source.setdefault(collection, [])
            eid = model.next_id(self.source, collection)
            if collection == "points":
                entries.append({"id": eid, "x": 0.0, "z": 0.0})
            elif collection == "members":
                points = [p["id"] for p in self.source["points"]]
                if len(points) < 2:
                    return
                entries.append({"id": eid, "kind": "bar", "p1": points[0], "p2": points[1]})
            elif collection == "point_loads":
                if not self.source["points"]:
                    return
                entries.append({"id": eid, "point": self.source["points"][0]["id"], "direction": "vertical",
                                "magnitude": {"value": 1.0, "unit": "kN"}, "label": "", "show": "value"})
            elif collection == "dimensions":
                points = [q["id"] for q in self.source["points"]]
                if len(points) < 2:
                    return
                entries.append({"id": eid, "kind": "horizontal", "from": {"point": points[0]},
                                "to": {"point": points[1]}, "offset": 1.0, "label": ""})
            else:
                if not self.source["members"]:
                    return
                entries.append({"id": eid, "member": self.source["members"][0]["id"], "shape": "uniform",
                                "direction": "vertical", "magnitude": {"value": 1.0, "unit": "kN/m"},
                                "label": "", "show": "value"})
        self.edit(apply)
        self.set_tables()

    def remove_row(self, collection):
        table = self.table_widgets[collection]
        row = table.currentRow()
        entries = self.source.get(collection, [])
        if row < 0 or row >= len(entries):
            return
        eid = entries[row]["id"]
        rest = model.used_by(self.source, collection, eid)
        if rest and QMessageBox.question(
            self, self.t("st_delete_title"),
            self.t("st_cascade", id=eid, rest=", ".join(r[1] for r in rest)),
        ) != QMessageBox.StandardButton.Yes:
            return
        self.edit(lambda: model.remove(self.source, collection, eid))
        self.set_tables()

    def on_table_selection(self, collection):
        """A row clicked in a list selects its entry on the drawing -- and the cell the engineer actually clicked keeps the focus, rather than being taken back to the first column."""
        if self.loading:
            return
        table = self.table_widgets[collection]
        row = table.currentRow()
        entries = self.source.get(collection, [])
        if 0 <= row < len(entries):
            self.from_table = True
            self.canvas.select((collection, entries[row]["id"]))
            self.from_table = False

    # -- history ------------------------------------------------------------------

    def push_history(self):
        self.undo_stack.append(copy.deepcopy(self.source))
        del self.undo_stack[:-HISTORY]
        self.redo_stack.clear()

    def replace_source(self, state):
        self.source.clear()
        self.source.update(state)
        self.canvas.selection = None
        self.canvas.invalidate()
        self.fill()
        self.on_changed()
        self.on_selection()

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(copy.deepcopy(self.source))
            self.replace_source(self.undo_stack.pop())

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(copy.deepcopy(self.source))
            self.replace_source(self.redo_stack.pop())

    # -- after every change --------------------------------------------------------

    def on_changed(self, tables=True):
        self.dirty = True
        if tables:
            self.set_tables()
        self.refresh_messages()
        self.fill_commands()
        self.update_list_marker()

    def refresh_messages(self):
        try:
            notes = [self.app.note_text(n) for n in model.warnings(self.source, self.values)]
        except Exception as exc:  # broad: a draft may be half-built -- its message is the warning shown; a warning must never stop the window
            notes = [str(exc)]
        self.message.setPlainText("\n".join(notes))

    def on_selection(self):
        self.refresh_selection()
        self.fill_commands()
        collection, entry = self.canvas.selected()
        if entry is None or collection not in self.table_widgets or self.from_table:
            return
        self.loading = True
        table = self.table_widgets[collection]
        for row in range(table.rowCount()):
            item = table.item(row, 0)
            if item is not None and item.text() == entry["id"]:
                table.selectRow(row)
                self.tables.setCurrentIndex(list(self.table_specs).index(collection))
                break
        self.loading = False

    # -- the selection's properties -------------------------------------------------


    # -- the calls ------------------------------------------------------------------

    def fill_commands(self):
        """The «Affichage» view told the model as it stands (display_view.DisplayTab): the calls to copy left the right pane in v0.117."""
        self.update_display()

    def display_entries(self):
        """`#show-static-model` of the model open -- the parts it may highlight are the model's own ids -- and the loop over every model."""
        sid = self.source.get("id") or "?"
        here = project.current()
        if self.current_id is None or self.dirty:
            banner = self.t("st_unsaved_hint")
        else:
            exported = sid in ref.load_statics(here.data_dir).get("models", {})
            banner = display_view.export_state(self.t, sid, exported, here.statics_dir / f"{sid}.json", here.data_dir / "statics.json")
        return [
            display_view.Entry("model", "show-static-model", "show-static-model", positional=(sid,), banner=banner,
                               context={"highlight": sorted(model.all_ids(self.source))},
                               preset={"highlight": [entry["id"]] if (entry := self.canvas.selected()[1]) is not None else []}),   # what is selected on the drawing, ticked: the call that lights it, as the card of calls led with until v0.117
            self.loop_entry("show-static-model", ref.call_static_model_loop()),
        ]

    # -- the models -----------------------------------------------------------------

    def reload_list(self, select=None):
        self.loading = True
        self.saved_ids = []
        entries = []
        for sid, label, group in list_models():
            self.saved_ids.append(sid)
            entries.append({"id": sid, "text": f"{sid} — {label}" if label else sid, "group": group})
        if self.current_id is None:      # the draft nobody has saved yet, at the root where it can be seen
            entries.append({"id": NEW_ROW, "text": self.t("st_new_item"), "group": grouped_list.ROOT_GROUP})
        target = select if select is not None else self.current_id
        if target not in self.saved_ids:
            target = NEW_ROW if self.current_id is None else None
        self.list.set_entries(entries, self.empty_folders, target, archived=source_archive.entries(project.current().statics_dir, self.list._t))
        self.empty_folders = self.list.empty_folders()
        self.app.save_folder_settings("tab_statics", self.empty_folders)
        self.empty_hint.setVisible(not self.saved_ids)
        self.loading = False
        self.update_list_marker()

    def on_folders_changed(self):
        """A folder made, renamed or removed in the list: what the widget now holds is what the tab keeps. ⚠️ Connecting `foldersChanged` straight to `reload_list` rebuilt the list from the tab's own copy of the empty folders, taken BEFORE the new one was added -- so a folder just made vanished the moment it was made."""
        self.empty_folders = self.list.empty_folders()
        self.reload_list(select=self.current_id)

    def on_moved(self, ids, group):
        """A drag wrote a folder: the field goes into each source, the models are exported, the list is rebuilt from the files."""
        moved = 0
        for sid in ids:
            if sid == NEW_ROW:
                continue                  # a draft has no file to write the field into
            path = project.current().statics_dir / ("%s.json" % sid)
            try:
                source = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if group:
                source["group"] = group
            else:
                source.pop("group", None)
            path.write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            moved += 1
        if moved:
            self.export_models(self.t("st_moved", count=moved, group=group or "—"))
        self.reload_list(self.current_id)

    def update_list_marker(self):
        """A dot at the left of the model being edited while it has unsaved changes, and the tab's own. Every row carries a mark, dot or blank, so none of them moves sideways as the model is drawn on."""
        for sid in self.list.ids():
            mine = sid == self.current_id or (self.current_id is None and sid == NEW_ROW)
            self.list.set_mark(sid, self.app.dirty_mark(mine and self.dirty))
        self.app.update_tab_marks()

    def on_list_change(self, sid):
        if self.loading or not sid or sid not in self.saved_ids:
            return
        if sid == self.current_id:
            return
        if not self.confirm_leave():
            self.reload_list(select=self.current_id)
            return
        self.load(sid)

    def open_source(self, source, current_id, dirty):
        self.source = source
        self.current_id = current_id
        self.dirty = dirty
        self.undo_stack, self.redo_stack = [], []
        self.canvas.set_source(self.source, self.values)
        self.fill()
        self.loading = True
        self.on_changed()
        self.loading = False
        self.dirty = dirty
        self.on_selection()

    def load(self, sid):
        path = project.current().statics_dir / f"{sid}.json"
        try:
            source = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(source, dict):
                raise ValueError("not a JSON object")
            for key, value in model.new_source(sid).items():
                source.setdefault(key, copy.deepcopy(value))
            # a release's translational stiffness is dropped as the export drops it; the model opens modified, so the change is seen and saved (AUD-7-424)
            dropped = model.drop_release_stiffness(source, f"model {sid}")
            # the export's values read again, and every linked field given the value its variable has now: the drawing on screen is the one the report will print (spec 2026-10-11-variables-liees-champs-et-textes, D-14)
            self.values = model.known_values(project.current().data_dir)
            model.refresh_links(source, self.values)
        except (OSError, ValueError) as exc:
            notices_ui.tell(self.t("st_unreadable", name=path.name, error=exc), notifications.CRITICAL, exc=exc, key="st_unreadable", args=dict(name=path.name, error=exc), source="statics_tab")
            source, dropped = model.new_source(sid), []
        self.open_source(source, sid, bool(dropped))
        self.reload_list(select=sid)

    def load_first(self):
        models = list_models()
        if models:
            self.load(models[0][0])
        else:
            self.open_source(model.new_source(next_free_id([])), None, False)
            self.reload_list()

    def confirm_leave(self):
        """True when the model may be replaced: nothing unsaved, or the engineer saved or discarded it."""
        return autosave.confirm(self.app, self, self.t("st_unsaved_title"), self.t("st_unsaved", id=self.id_edit.text().strip() or "?"), discard=lambda: (setattr(self, "dirty", False), self.current_id is None and self.load_first()))   # saved without a question where it can be, else the one question (autosave.py, v0.117)

    def taken_ids(self):
        # (id, label, folder) since v0.69: unpacked as two, «Nouveau» and «Dupliquer» raised a ValueError, silent under pythonw until v0.77 showed it
        return [sid for sid, _label, _group in list_models()]

    def new(self):
        if not self.confirm_leave():
            return
        self.open_source(model.new_source(next_free_id(self.taken_ids())), None, True)
        self.reload_list()
        self.choose_tool("point")

    def duplicate(self):
        if not self.confirm_leave():
            return
        source = copy.deepcopy(self.source)
        source["id"] = next_free_id(self.taken_ids())
        self.open_source(source, None, True)
        self.reload_list()

    def revert(self):
        if self.current_id is None:
            self.load_first()
        else:
            self.load(self.current_id)

    def delete(self):
        """«Supprimer»: what is selected goes to «Archives», its ID removed (source_archive.py, v0.77) -- or, an archived entry selected, is deleted for good. A model never saved is simply discarded."""
        if self.archive.delete():
            return
        self.dirty = False
        self.load_first()

    # -- saving ----------------------------------------------------------------------

    def fail(self, message):
        return autosave.refuse(self, self.t("st_save_failed_title"), message)

    def save(self):
        """Writes statics/<id>.json and exports the models -- the draft checked first by the same rules export_all.py applies, so a model that saves is one the report can build. True when saved."""
        # each linked field given the value it has now, its last value, and the version that says so (D-14) -- in the model itself, whose entries the panes and the canvas hold
        model.stamp_version(self.source, self.values)
        source = copy.deepcopy(self.source)
        sid = source.get("id", "")
        if not model.ID_PATTERN.match(sid or ""):
            return self.fail(self.t("st_id_invalid", id=sid))
        old = self.current_id
        renaming = old is not None and sid != old
        # the file system ignores case, the report does not: S01 and s01 are one file, and two ids
        clash = any(t.lower() == sid.lower() for t in self.taken_ids()) and (old is None or sid.lower() != old.lower())
        if clash:
            return self.fail(self.t("st_id_exists", id=sid))
        if renaming and not autosave.ask_rename(self, self.t("st_save_failed_title"), self.t("st_rename", old=old, new=sid)):
            return False
        try:
            model.check_source(source, f"{sid}.json")
        except validation.ValidationError as exc:
            return self.fail(str(exc))
        try:
            project.current().statics_dir.mkdir(parents=True, exist_ok=True)
            if renaming:
                (project.current().statics_dir / f"{old}.json").unlink(missing_ok=True)
            (project.current().statics_dir / f"{sid}.json").write_text(
                json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
        except OSError as exc:
            return self.fail(str(exc))
        self.current_id = sid
        self.dirty = False
        self.export(sid, self.t("st_saved", id=sid))
        self.reload_list(select=sid)
        return True

    def export_models(self, done_text):
        """Export the models without naming one: what a drop needs, which changes a field and no drawing."""
        try:
            model.export(project.current().statics_dir, project.current().data_dir, self.values)
        except Exception as exc:  # broad: the exporter's own message is what helps
            self.app.set_status(self.t("st_move_failed", error=str(exc)))
            return
        self.app.set_status(done_text)

    def export(self, sid, done_text):
        """The models' part of the export, run here and now: data/statics.json and data/statics/, from every saved source. A failure leaves data/ as it was and says why."""
        try:
            notes = model.export(project.current().statics_dir, project.current().data_dir, self.values)
        except (validation.ValidationError, engine.EngineError, OSError) as exc:
            autosave.warn(self, "Woodcore", self.t("st_export_failed", id=sid, error=exc))
            return False
        mine = [n for n in notes if n.startswith(f"model {sid}:")]
        self.app.set_status(self.t("st_saved_warnings", id=sid, n=len(mine)) if mine else done_text)
        return True

    # -- surviving a rebuild ------------------------------------------------------------

    def view_state(self):
        return {
            "draft": copy.deepcopy(self.source),
            "current_id": self.current_id,
            "dirty": self.dirty,
            "tool": self.canvas.tool,
            "grid": self.grid_combo.currentIndex(),
            "snap": self.snap_button.isChecked(),
            "list_tab": self.tables.currentIndex(),
            "splitter": self.splitter.sizes(),
            "center": self.center_split.sizes(),
            "columns": {collection: columns.state() for collection, columns in self.table_columns.items()},
            "empty_folders": list(self.empty_folders),
        }

    def restore(self, state):
        if state:
            self.grid_combo.setCurrentIndex(state.get("grid", 0))
            self.snap_button.setChecked(state.get("snap", True))
            self.tables.setCurrentIndex(state.get("list_tab", 0))
            self.empty_folders = list(state.get("empty_folders") or [])
            # the widths the engineer dragged the lists' columns to, before the lists are filled with them
            for collection, widths in (state.get("columns") or {}).items():
                if collection in self.table_columns:
                    self.table_columns[collection].restore(widths)
            self.open_source(state["draft"], state.get("current_id"), state.get("dirty", False))
            self.reload_list(select=self.current_id)
            if state.get("splitter"):
                self.splitter.setSizes(state["splitter"])
            # the three heights the engineer set, through a language switch and a reload like everything else here -- and the bar's pane left as he set it rather than made snug again
            if state.get("center"):
                self.center_split.setSizes(state["center"])
                self.bar_area.snug_on_show = False
            self.choose_tool(state.get("tool", "select"))
        else:
            self.splitter.setSizes([1800, 7000, 4600])
            self.load_first()
            self.choose_tool("select")
