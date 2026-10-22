"""Woodcore's «Schémas» tab (docs/domain/detail-schemas.md §3.3decies): where a connection detail is drawn -- the pieces, the fastener markers, the construction aids and the dimensions -- saved, and the Typst call that prints it copied.

A schema is saved as its source, `details/<id>.json` beside calc/, and exported at once by `calc/domains/schema.py`, the module export_all.py runs: `data/schemas.json` and the figures under `data/schemas/`. So data/ is still only ever written by the pipeline's own code, and the report sees the schema without the load workbooks being read again. What the canvas shows is `schema_svg.py`'s drawing, the report's own; its geometry -- what is under the pointer, where it snaps, which direction the cursor is tracking along -- is `schema.py`'s.

statics_tab.py's own arrangement, ported: the list on the left with its folders, the tool bar / canvas / lists as three panes the engineer drags in the middle, the properties on the right, and everything enterable twice over -- by clicking on the grid or by typing into a list.

The tab lives in its own module rather than in woodcore_gui.py, which lists it in its TABS and merges STRINGS below into its own: the window's language, shortcuts and closing rules are woodcore_gui's, the tab's texts and behaviour are here.

⚠️ The source folder is `details/`, not `schemas/` -- `000-Python/schemas/` holds the *.schema.json contracts (schema.py's own module docstring says why).
"""

import copy
import json
import math
from pathlib import Path

from PySide6.QtCore import QEvent, QSize, Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QSpinBox, QSplitter, QTabWidget,
    QTableWidget, QTableWidgetItem, QToolButton, QVBoxLayout, QWidget,
)

import build_reference as ref
from check_cell import CentredCheck  # a tick centred in its cell (v0.77)
import engine
import grouped_list
import source_archive  # «Supprimer» archives (source_archive.py)
import identity
import project  # where the project this tab works on is (calc/project.py)
import stylefactors  # the three factors of a drawing and of one entry of it, typed the way every tab types them (stylefactors.py, v0.99)
import theme  # the colours this tab states itself (theme.py, v0.90)
import dimension_icons  # the dimension tools' symbols, the same in the three tabs (issue #9)
import richtext  # the calls coloured as the site's code, «Copié ✓» (richtext.py, v0.92)
import cards  # the properties in cards, after the website (cards.py, v0.95)
import text_pane  # a text's pane, the four drawing engines' one (issue #43)
import display_view  # the «Affichage» view: the command, its options, the call and the page (display_view.py, v0.117)
import views  # the views the top bar's switch chooses between (views.py, v0.117)
import autosave  # saving without a question, and what is never saved without the engineer (autosave.py, v0.117)
import validation
from domains import connector as connector_model  # the one reader of the exported positions (known_positions)
from domains import figure_style  # which factors an entry of a schema may state over the drawing's (figure_style.py, v0.99)
from domains import schema as model
from domains import schema_svg
import flowbar
from flowbar import (BAR_SPACING, TOOL_ICON_PX, FlowLayout, FlowWidget, ResizableColumns, ToolBarArea,
                     set_tip, size_tool, symbol_px, tool_group)
from schema_canvas import AREA_MODES, CONNECTOR_TOOLS, TOOLS, SchemaCanvas
from schema_tab_words import STRINGS, TIPS, tip_key  # split out of this module (issue #30): every name it had is still importable from it
from schema_tab_build import AREA_MODE_SVG, GRID_CHOICES, ICON_PX, TOOL_GROUPS, icon_from_svg, on_ground, plain_label, swatch_kind, tool_icon, SchemaBuildMixin  # split out of this module (issue #30): every name it had is still importable from it
from schema_tab_draft import NEW_ROW, _as_number, list_schemas, next_free_id, SchemaDraftMixin  # split out of this module (issue #30): every name it had is still importable from it

# Every path is the current project's, asked of project.current() when it is needed (v0.81, docs/architecture/layout.md §11): the schemas' sources are its `details_dir`, and the two kinds of calculation drawn on a schema, which name it by its id and into which a rename here is carried (section 3.3decies), its `connectors_dir` and `connections_dir`.


# How many steps «Annuler» can go back.
from canvas_editor import CanvasEditorTab  # «Annuler» and «Rétablir», once for every tab with a canvas (spec 2026-10-19-base-saine-nettoyage, ARCH-001)


# A cell that cannot be read takes theme.colour("danger-soft"); a side of an element's section written over its position's, theme.colour("override") -- the orange the connectors' tab already uses for exactly that (v0.75), the scheme's since v0.90.


# The refusals the canvas emits, and the sentence each becomes.
REFUSALS = {
    "element": "sc_refused_element",
    "reference": "sc_refused_reference",
    "dimension-ends": "sc_refused_dimension_ends",
    "dimension-parallel": "sc_refused_dimension_parallel",
    "dimension-same-element": "sc_refused_dimension_same_element",
    # v0.73. A reason may arrive as «code|detail» -- the detail is what the model's own refusal named
    # (the two position numbers that would not merge, the number of times a line crossed an area) and
    # it goes into the string's {detail} hole. on_refused splits it.
    "modify-nothing": "sc_refused_modify_nothing",
    "modify-axis": "sc_refused_modify_axis",
    "split-no-element": "sc_refused_split_no_element",
    "split-no-line": "sc_refused_split_no_line",
    "split-many-lines": "sc_refused_split_many_lines",
    "split-missed": "sc_refused_split_missed",
    "split-crossings": "sc_refused_split_crossings",
    "split-aid-point": "sc_refused_split_aid_point",
    "split-no-aid": "sc_refused_split_no_line",
    "merge-too-few": "sc_refused_merge_too_few",
    "merge-kinds": "sc_refused_merge_kinds",
    "merge-positions": "sc_refused_merge_positions",
    "merge-apart": "sc_refused_merge_apart",
    "merge-no-edge": "sc_refused_merge_no_edge",
    "crop-empty": "sc_refused_crop_empty",
}


def grid_points(columns, rows, column_spacing, row_spacing, x0, z0, angle):
    """A rectangular group of connector markers: `columns` along the direction `angle` (degrees from x towards z), `rows` across it, centred on (x0, z0), in millimetres. Numbered row by row, from the top row down (z growing) and along each row -- the way a course sheet numbers a 3 × 5 dowel group.

    ⚠️ It lived in the window's own module (`woodcore_gui.py` since v0.96) until v0.74, filling the polar-moment tab's own coordinate table. The
    markers are the schema's now, so it lives where they are placed: a second tab writing `details/<id>.json`
    could overwrite an unsaved draft of that very schema in the tab that owns it, which is the one failure
    this project treats as worst (docs/decisions.md §13).
    """
    u = (math.cos(math.radians(angle)), math.sin(math.radians(angle)))
    v = (-u[1], u[0])  # a quarter from the columns towards z
    points = []
    for r in range(rows):
        across = (r - (rows - 1) / 2) * row_spacing
        for c in range(columns):
            along = (c - (columns - 1) / 2) * column_spacing
            points.append((model.round_place(x0 + along * u[0] + across * v[0]),
                           model.round_place(z0 + along * u[1] + across * v[1])))
    return points


class GridDialog(QDialog):
    """Sets out a rectangular group of connector markers: so many columns along a direction, so many rows across it, their spacings and the group's centre. `changed` is emitted on every edit of a field, typing included, so the tab can draw the group while it is being set out. `values` are the fields to start from -- the last grid accepted -- else a 3 × 2 group at 60 mm whose columns run along x."""

    changed = Signal()

    def __init__(self, parent, t, values=None):
        super().__init__(parent)
        values = values or {}
        self.setWindowTitle(t("sc_grid_title"))
        form = QFormLayout(self)
        self.columns = QSpinBox()
        self.columns.setRange(1, 60)
        self.columns.setValue(values.get("columns", 3))
        self.rows = QSpinBox()
        self.rows.setRange(1, 60)
        self.rows.setValue(values.get("rows", 2))

        def length(default):
            box = QDoubleSpinBox()
            box.setRange(-100000.0, 100000.0)
            box.setDecimals(1)
            box.setSuffix(" mm")
            box.setValue(default)
            return box

        self.column_spacing = length(values.get("column_spacing", 60))
        self.row_spacing = length(values.get("row_spacing", 60))
        self.x0 = length(values.get("x0", 0))
        self.z0 = length(values.get("z0", 0))
        self.angle = QDoubleSpinBox()
        self.angle.setRange(-360.0, 360.0)
        self.angle.setDecimals(1)
        self.angle.setSuffix(" °")
        self.angle.setValue(values.get("angle", 0))
        self.replace = QCheckBox(t("sc_grid_replace"))
        self.replace.setChecked(values.get("replace", True))
        for box in (self.columns, self.rows, self.column_spacing, self.row_spacing, self.x0, self.z0, self.angle):
            box.valueChanged.connect(lambda _value: self.changed.emit())
        self.replace.toggled.connect(lambda _checked: self.changed.emit())
        for key, widget in (("sc_grid_columns", self.columns), ("sc_grid_rows", self.rows),
                            ("sc_grid_col_spacing", self.column_spacing),
                            ("sc_grid_row_spacing", self.row_spacing),
                            ("sc_grid_center_x", self.x0), ("sc_grid_center_z", self.z0),
                            ("sc_grid_angle", self.angle)):
            form.addRow(t(key), widget)
        form.addRow(self.replace)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def points(self):
        return grid_points(self.columns.value(), self.rows.value(),
                           self.column_spacing.value(), self.row_spacing.value(),
                           self.x0.value(), self.z0.value(), self.angle.value())

    def values(self):
        """The fields as they stand, for the next grid to start from."""
        return {
            "columns": self.columns.value(), "rows": self.rows.value(),
            "column_spacing": self.column_spacing.value(), "row_spacing": self.row_spacing.value(),
            "x0": self.x0.value(), "z0": self.z0.value(), "angle": self.angle.value(),
            "replace": self.replace.isChecked(),
        }


class SchemaTab(SchemaDraftMixin, SchemaBuildMixin, CanvasEditorTab, display_view.DisplayTab, QWidget):
    """Draws a detail schema, saves it as its source, exports it, and copies the call that prints it."""
    KEY = "tab_schema"
    GRAPH_KIND = "schema"   # issue #71
    LIST_KEY = "sc_list"
    EMPTY_KEY = "sc_empty"
    WORDS = "sc"
    UNSAVED_WORDS = ("sc_unsaved_title", "sc_unsaved")   # the question before the draft is left (SourceEditorTab.confirm_leave)
    DISCARD_OPENS_FIRST = True

    VIEWS = views.DRAW_VIEWS   # «Dessin» and «Affichage» (views.py, v0.117)

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.t = app.t
        self.loading = False
        self.dirty = False
        self.current_id = None
        self.source = model.new_source("D01")
        self.init_history()
        self.grid_values = None  # the last marker grid accepted, for the next one to start from
        self.empty_folders = list(app.folder_settings(self.KEY))
        self.ids = []
        self.from_table = False
        self.positions = connector_model.known_positions(project.current().data_dir)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.build_list())
        self.splitter.addWidget(self.build_center())
        self.splitter.addWidget(self.build_properties())
        self.install_display("tab_schema")   # «Affichage»: schema()'s options, the figure it is copied in and its page (v0.117)
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

        self.restore(app.views.get("tab_schema"))

    # -- building ----------------------------------------------------------------


    # v0.75: an element's section is two columns, b and h, each the value in force -- typed, it is written over; emptied, it follows the position again.
    TABLE_SPECS = (
        ("linear", "sc_tab_linear", ("sc_col_id", "sc_col_position", "sc_col_view", "sc_col_b", "sc_col_h", "sc_col_points")),
        ("area", "sc_tab_area", ("sc_col_id", "sc_col_position", "sc_col_b", "sc_col_h", "sc_col_points")),
        ("connectors", "sc_tab_connectors", ("sc_col_id", "sc_col_kind", "sc_col_x", "sc_col_z", "sc_col_diameter")),
        # v0.77: the named points have a list of their own, right of the markers, and a «connecteur» tick -- a point
        # ticked is a fastener every module may take, «Connecteurs» and «Moments polaires» alike (schema.fastener_places). They are still aids of kind
        # `point` in the source: the tab is a view, the collection unchanged.
        ("points", "sc_tab_points", ("sc_col_id", "sc_col_x", "sc_col_z", "sc_col_shown", "sc_col_connector", "sc_col_label")),
        ("aids", "sc_tab_aids", ("sc_col_id", "sc_col_kind", "sc_col_x", "sc_col_z", "sc_col_angle", "sc_col_shown")),
        # the dimension's name (its `label`) and what the figure writes beside it, a static model's own four -- a combo, the one cell of these lists that is not typed into (SHOW_COLUMN)
        ("dims", "sc_tab_dims", ("sc_col_id", "sc_col_kind", "sc_col_offset", "sc_col_value", "sc_col_label", "sc_col_show")),
    )


    # -- the draft ------------------------------------------------------------------


    # -- the options of «Surfacique» (v0.117) ----------------------------------------------


    # -- the lists -------------------------------------------------------------------


    # Which columns are read only: the points of an element (drawn, not typed), a dimension's kind
    # and the value it measured -- a measurement is the drawing's answer, never a cell to type into
    # (statics_tab's own rule for its «valeur» column, section 3.3octies).
    READ_ONLY = {"linear": (5,), "area": (4,), "connectors": (1,), "points": (), "aids": (1,), "dims": (1, 3)}

    # The check boxes of the lists, (list, column) -> the entry's key: a tick is the cell's state, not its text.
    CHECK_COLUMNS = {("points", 3): "shown", ("points", 4): "connector", ("aids", 5): "shown"}

    # The b and h columns of the two element lists, whose cell turns orange where a side is written over (v0.75).
    SIDE_COLUMNS = {"linear": {3: "b", 4: "h"}, "area": {2: "b", 3: "h"}}

    # The column of a dimension's `show`: a combo of a static model's own four, set into its cell rather than typed.
    SHOW_COLUMN = ("dims", 5)
    SHOW_KEYS = ("sc_show_none", "sc_show_name", "sc_show_value", "sc_show_both")


    # -- reacting --------------------------------------------------------------------

    def remember(self):
        """One step of «Annuler», taken before a change rather than after it."""
        if self.loading:
            return
        self.push_history()

    def snapshot(self, state):
        return model.snapshot(state)   # the schema's own copy, which keeps its drawing's caches out

    def replace_source(self, state):
        """A step of «Annuler» or «Rétablir»: the source is the state put back, the canvas drawn from it."""
        self.source = state
        self.canvas.set_source(self.source)
        self.after_change()

    def after_change(self):
        self.loading = True
        self.fill_form()
        self.loading = False
        self.on_selection()
        self.fill_tables()
        self.mark_dirty()
        self.update_calls()
        self.update_warnings()

    def on_canvas_change(self):
        self.fill_tables()
        self.mark_dirty()
        self.update_calls()
        self.update_warnings()
        self.update_crop_text()

    def on_selection(self):
        collection, entry = self.canvas.selected()
        self.selection_note.setText(
            self.t("sc_none_selected") if entry is None else f"{collection} · {entry['id']}"
        )
        element = entry is not None and collection == "elements"
        for caption, widget in self.element_rows:
            caption.setVisible(element)
            widget.setVisible(element)
        if element:
            self.fill_element(entry)
        else:
            for fields in self.side_fields.values():
                for widget in fields["row"]:
                    widget.setVisible(False)
        self.fill_entry_style(entry)
        self.fill_text(collection, entry)
        dimension = entry is not None and collection == "dimensions"
        for caption, widget in self.dim_rows:
            caption.setVisible(dimension)
            widget.setVisible(dimension)
        if dimension:
            loading, self.loading = self.loading, True
            self.dim_show_combo.setCurrentIndex(max(self.dim_show_combo.findData(model.dimension_show(entry)), 0))
            self.dim_name_edit.setText(entry.get("label", ""))
            self.loading = loading
        if not self.from_table:
            self.sync_tables()
        self.update_calls()

    def fill_text(self, collection, entry):
        """A text's pane (issue #43, UI-004), text_pane's: built for the text selected, taken down otherwise."""
        while self.text_layout.count():
            widget = self.text_layout.takeAt(0).widget()
            if widget is not None:
                widget.deleteLater()
        self.text_pane = None
        if entry is None or collection != "texts":
            self.text_holder.setVisible(False)
            return
        self.text_pane = text_pane.TextPane(entry, lambda: self.app, self.app.lang, self.edit_text, self.on_selection, self.values,
                                            bool(getattr(self.app, "read_only", False)))
        self.text_layout.addWidget(self.text_pane)
        self.text_holder.setVisible(True)

    def edit_text(self, apply):
        """One change to a text, from its pane: one step of «Annuler», redrawn."""
        if self.loading:
            return
        self.remember()
        apply()
        self.mark_dirty()
        self.canvas.invalidate()
        self.fill_tables()
        self.update_warnings()

    def fill_element(self, entry):
        """The panel of one element: its position, its view, each side of its section with where it comes from, and its label."""
        self.loading = True
        section = model.element_section(entry, self.positions)
        pid = entry.get("position") or ""
        index = self.position_combo.findData(pid)
        if index < 0:
            # a number the export no longer lists is kept and marked, never replaced by whatever comes first (the plan tab's own rule)
            self.position_combo.addItem(f"{pid} (?)", pid)
            index = self.position_combo.count() - 1
        self.position_combo.setCurrentIndex(index)
        linear = entry.get("kind") == "linear"
        for widget in self.view_row:
            widget.setVisible(linear)
        self.view_combo.setCurrentIndex(max(0, self.view_combo.findData(entry.get("view", "h"))))
        for side, fields in self.side_fields.items():
            value = section[side]
            fields["spin"].setValue(value if value is not None else model.ELEMENT_DEFAULT_WIDTH)
            held = section[f"position_{side}"]
            stated = section[f"{side}_from"] == "stated"
            # A side that follows its position says so IN ITS FIELD -- «200.0 mm — T001» -- and the line under it appears only when there is something orange to say: the side written over (with «Reprendre»), the position gone, or a position with no b/h to follow.
            following = section[f"{side}_from"] == "position"
            fields["spin"].blockSignals(True)
            fields["spin"].setSuffix(" " + cards.followed("mm", pid) if following else " mm")   # «200.0 mm — T001» (v0.117)
            fields["spin"].blockSignals(False)
            note, back = "", False
            if pid and not section["resolved"]:
                note, back = self.t("sc_lost_position", pid=pid), stated
            elif stated and pid and held is not None:
                note, back = self.t("sc_overridden", pid=pid, value=model.fmt_number(held)), True
            elif pid and held is None:
                note, back = self.t("sc_no_section", pid=pid, dimension=section["dimension"] or "—"), stated
            fields["note"].setText(note)
            fields["note"].setStyleSheet(f"color: {theme.colour('override')};")
            fields["back"].setVisible(back and bool(pid))
            for widget in fields["row"]:
                widget.setVisible(bool(note) or (back and bool(pid)))
            fields["spin"].setStyleSheet(f"color: {theme.colour('override')};" if stated else "")
        self.element_label_edit.setText(entry.get("label", ""))
        self.element_label_edit.setPlaceholderText(model.element_caption({**entry, "label": ""}, self.positions))
        self.loading = False

    def edit_element(self, change):
        """One change to the focused element, as one step of «Annuler»: `change(entry)` makes it."""
        if self.loading:
            return
        collection, entry = self.canvas.selected()
        if entry is None or collection != "elements":
            return
        self.remember()
        change(entry)
        self.mark_dirty()
        self.canvas.invalidate()
        self.fill_tables()
        self.fill_element(entry)
        self.update_calls()
        self.update_warnings()

    def on_position(self, _index):
        pid = self.position_combo.currentData() or ""
        if self.loading:
            return
        collection, entry = self.canvas.selected()
        if entry is None or collection != "elements":
            return
        # the position chosen is the one the next piece drawn is given
        self.canvas.element_position = pid
        self.fill_tool_positions()
        self.update_area_fixed()

        def change(element):
            if pid:
                element["position"] = pid
            else:
                element.pop("position", None)
        self.edit_element(change)

    def on_view(self, _index):
        view = self.view_combo.currentData() or "h"
        self.edit_element(lambda element: element.__setitem__("view", view) if element.get("kind") == "linear" else None)

    def on_side(self, side, value):
        """A side typed: written over, and it stays written over (v0.75). Typing the very value the position holds still writes it over -- «Reprendre» is what follows the position again."""
        self.edit_element(lambda element: element.__setitem__(side, round(float(value), 2)))

    def take_back(self, side):
        """«Reprendre»: the side follows its position again."""
        self.edit_element(lambda element: element.pop(side, None))

    def on_element_label(self, text):
        def change(element):
            if text.strip():
                element["label"] = text
            else:
                element.pop("label", None)
        self.edit_element(change)

    def on_dim_show(self, _index):
        collection, entry = self.canvas.selected()
        if self.loading or entry is None or collection != "dimensions":
            return
        self.set_dimension_show(entry["id"], self.dim_show_combo.currentData())

    def on_dim_name(self):
        """A dimension's name typed in the panel: one step of «Annuler», as the list's own cell is."""
        collection, entry = self.canvas.selected()
        text = self.dim_name_edit.text().strip()
        if self.loading or entry is None or collection != "dimensions" or text == (entry.get("label") or ""):
            return
        self.remember()
        entry["label"] = text
        self.mark_dirty()
        self.canvas.invalidate()
        self.fill_tables()
        self.update_calls()
        self.update_warnings()

    def add_row(self, which):
        """«Ajouter» under a list: one entry put down in the middle of the view, selected, and one step of «Annuler» (v0.75)."""
        self.canvas.add_default(which)
        self.tables.setCurrentIndex([spec[0] for spec in self.TABLE_SPECS].index(which))

    def on_row_hover(self, which, row):
        rows = self.rows_of(which)
        self.canvas.set_hover((self.collection_of(which), rows[row]["id"]) if 0 <= row < len(rows) else None)

    def eventFilter(self, obj, event):
        # the pointer leaving a list takes its light off the drawing
        if event.type() == QEvent.Type.Leave and any(obj is t.viewport() for t in self.table_widgets.values()):
            self.canvas.set_hover(None)
        return super().eventFilter(obj, event)

    def sync_tables(self):
        """Shows the canvas's selection in the lists: every table marks its own share of it, and the tab holding the focused entry comes to the front.

        ⚠️ Each table holds one collection, so a selection of an element **and** the construction line it is to be cut on cannot be shown in one list at all. That is the tabbed layout's own limit, not a state the two got into: what holds the whole selection is the canvas, and the lists are a view of it.
        """
        chosen = set(self.canvas.selection_ids())
        self.loading = True
        front = None
        for which, _key, _columns in self.TABLE_SPECS:
            table = self.table_widgets[which]
            collection = self.collection_of(which)
            table.clearSelection()
            for r, row in enumerate(self.rows_of(which)):
                if (collection, row["id"]) in chosen:
                    table.selectRow(r)
                    if self.canvas.selection == (collection, row["id"]):
                        front = which
                        table.setCurrentCell(r, 0)
        if front is not None:
            self.tables.setCurrentIndex([s[0] for s in self.TABLE_SPECS].index(front))
        self.loading = False

    def on_pointer(self, x, z, kind):
        """The readout under the drawing: where the pointer is, and what it snapped to in the window's language -- a tracking ray with its angle and distance. It showed the kinds raw, `[midpoint]`, `[ray|45|25]` (periodic audit 260916, AUD-4-1). The coordinates stay an f-string: as a key, they would be the same text in the three languages."""
        text = f"x = {model.fmt_number(x)} mm    z = {model.fmt_number(z)} mm"
        if kind:
            parts = kind.split("|")
            key = "sc_snap_" + parts[0].replace("-", "_")
            name = self.t(key) if key in STRINGS["fr"] else parts[0]   # a kind no key names passes as it is
            if len(parts) == 3 and parts[1]:
                text += "    " + self.t("sc_lock", angle=parts[1], distance=parts[2])
            text += f"    [{name}]"
        self.canvas.set_readout(text)

    def on_refused(self, reason):
        """Says why, in the window's language. A reason is a code, or «code|detail» where the model's own refusal named something -- the two position numbers, a crossing count -- which goes into the string's {detail} hole (section 4bis: the chrome follows the window, the sentence a test asserts stays English in the model)."""
        code, _, detail = str(reason).partition("|")
        key = REFUSALS.get(code)
        if key:
            self.app.set_status(self.t(key, detail=detail) if detail else self.t(key))
        elif detail or code:
            # A code with no words yet: the model's own sentence says more than silence would.
            self.app.set_status(reason)

    def on_grid(self, _index):
        choice = self.grid_combo.currentData()
        self.canvas.grid_mode = choice
        self.canvas.viewport().update()

    def on_snap(self, checked):
        self.canvas.snap_on = checked

    MODIFY_HINTS = {"move": "sc_hint_move", "duplicate": "sc_hint_duplicate",
                    "rotate": "sc_hint_rotate", "mirror": "sc_hint_mirror"}

    def place_grid(self):
        """Sets out a rectangular group of connector markers, drawn as it is set out: every change in the dialog goes into the drawing at once. OK keeps the group; Cancel puts the markers back as they were.

        ⚠️ The kind is the connector tool in force, else the first of `connector.TYPES`: a grid places
        markers, and what kind they are is the same choice the five buttons beside it make.
        """
        before = copy.deepcopy(self.canvas.source.get("connectors", []))
        kind = TOOLS.get(self.canvas.tool, {}).get("kind")
        dialog = GridDialog(self, self.t, self.grid_values)

        def preview():
            self.canvas.place_markers(dialog.points(), kind=kind, replace=dialog.replace.isChecked())

        dialog.changed.connect(preview)
        preview()
        accepted = dialog.exec() == QDialog.DialogCode.Accepted
        if accepted:
            self.grid_values = dialog.values()
        else:
            # every preview was one step of «Annuler»; putting the markers back is one more, and the
            # engineer who cancelled sees the drawing they had.
            self.canvas.begin_change()
            self.canvas.source["connectors"] = before
            self.canvas.selection = None
            self.canvas.end_change()
            self.canvas.selection_changed.emit()

    def choose_tool(self, tool):
        self.canvas.set_tool(tool)
        button = self.tool_buttons.get(tool)
        if button is not None:
            button.setChecked(True)
        if tool in self.MODIFY_HINTS:
            # A modification verb says what its two clicks mean: what «déplacer» takes is not what
            # «tourner» takes, and one shared «cliquez» would say nothing about either.
            hint = self.t(self.MODIFY_HINTS[tool])
        elif tool == "crop":
            hint = self.t("sc_hint_crop")
        else:
            hint = self.t("sc_hint_select" if tool in ("select", "pan") else "sc_hint_draw")
        self.canvas.set_hint(hint)

    # -- the list ----------------------------------------------------------------------

    def sources_dir(self):
        return project.current().details_dir

    def listed(self):
        """The schemas, «id — label», in the folder each names (list_schemas)."""
        return [(sid, f"{sid} — {label}" if label else sid, group) for sid, label, group in list_schemas()]

    def export_listed(self, text):
        """The schemas exported without naming one -- what a drop into a folder or an archive needs; a failure said in the status bar."""
        try:
            model.export(project.current().details_dir, project.current().data_dir, self.known_positions(), self.values)
        except Exception as exc:  # broad: the exporter's own message is what helps
            self.app.set_status(self.t("sc_move_failed", error=str(exc)))
            return
        self.app.set_status(text)

    # -- the calls -----------------------------------------------------------------

    def update_calls(self):
        """The «Affichage» view told the schema as it stands (display_view.DisplayTab): the block of calls left the right pane in v0.117."""
        self.update_display()

    def display_entries(self):
        """`#figure(schema(…))` of the schema open -- the parts it may highlight are the schema's own ids, the one selected ticked -- and the loop over every schema."""
        sid = self.source.get("id", "") or "?"
        here = project.current()
        if self.current_id is None or self.dirty:
            banner = self.t("sc_unsaved_hint")
        else:
            exported = sid in ref.load_schemas(here.data_dir).get("schemas", {})
            banner = display_view.export_state(self.t, sid, exported, here.details_dir / f"{sid}.json", here.data_dir / "schemas.json")
        # «Copier» copies a figure of the report's own (spec 2026-10-15, UI-001, D-16): the drawing in it, the schema's label its caption and a label to cite it by
        caption = self.source.get("label") or sid
        return [
            display_view.Entry("schema", "image-schema", "image-schema", positional=(sid,), banner=banner,
                               context={"highlight": sorted(model.all_ids(self.source)), "detail-figure": ref.image_vocabulary()["image-schema"]["detail-figure"]},
                               preset={"highlight": [entry["id"]] if (entry := self.canvas.selected()[1]) is not None else []},   # what is selected on the drawing, ticked: the call that lights it, as the block of calls led with until v0.117
                               call_fn=lambda values: ref.figure_of_panel("image-schema", sid, values, caption)),   # the drawing as an image (spec 2026-10-21-commandes-typst-refonte, REQ-014, ARCH-012)
            self.loop_entry("image-schema", ref.call_figure_loop("image-schema", "schema")),
        ]

    def update_warnings(self):
        notes = [self.app.note_text(n) for n in model.warnings(self.source, self.positions)]
        self.warnings.setText(" · ".join(notes))

    def known_positions(self):
        """The position records the export wrote -- an element's b, h and label are read off them (v0.75)."""
        return connector_model.known_positions(project.current().data_dir)

    # -- new, duplicate, delete, save ------------------------------------------------

    def taken_ids(self):
        return [sid for sid, _label, _group in list_schemas()]

    def new(self):
        if not self.confirm_leave():
            return
        self.open_source(model.new_source(next_free_id(self.taken_ids())), None, True)
        self.reload_list()
        self.choose_tool("linear")

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

    def fail(self, message):
        return autosave.refuse(self, self.t("sc_save_failed_title"), message)

    def save(self):
        """Writes details/<id>.json and exports the schemas -- the draft checked first by the same rules export_all.py applies, so a schema that saves is one the report can build. True when saved."""
        model.stamp_version(self.source, self.values)   # a text's last values (D-14), and 1.2 where it holds one
        source = copy.deepcopy(self.source)
        sid = source.get("id", "")
        if not model.ID_PATTERN.match(sid or ""):
            return self.fail(self.t("sc_id_invalid", id=sid))
        old = self.current_id
        renaming = old is not None and sid != old
        clash = any(t.lower() == sid.lower() for t in self.taken_ids()) and (old is None or sid.lower() != old.lower())
        if clash:
            return self.fail(self.t("sc_id_exists", id=sid))
        if renaming and not autosave.ask_rename(self, self.t("sc_save_failed_title"), self.t("sc_rename", old=old, new=sid)):
            return False
        try:
            model.check_source(source, f"{sid}.json")
        except validation.ValidationError as exc:
            return self.fail(str(exc))
        try:
            project.current().details_dir.mkdir(parents=True, exist_ok=True)
            if renaming:
                (project.current().details_dir / f"{old}.json").unlink(missing_ok=True)
            engine.write_json(project.current().details_dir / f"{sid}.json", source)
        except OSError as exc:
            return self.fail(str(exc))
        self.current_id = sid
        self.dirty = False
        self.export(sid, self.t("sc_saved", id=sid))
        if renaming:
            self.rename_references(old, sid)
            self.app.list_store.rename("tab_schema", old, sid)   # the schema keeps its place in the list (calc/list_order.py, issue #15)
        self.reload_list(select=sid)
        self.update_list_marker()
        return True

    def rename_references(self, old, new):
        """A schema saved under a new id: every connector and every polar-moment calculation naming the old one is rewritten to name the new one, then exported, and the two tabs' drafts follow.

        Until now a rename left them naming a schema that no longer existed -- «Le schéma … n'existe plus», every marker «(?)» -- and nothing but editing each of them again brought the drawing back. A schema is referred to by its id and by nothing else, so the rename is exact: only a `schema` field equal to the old id changes.
        """
        changed = {}
        for folder in (project.current().connectors_dir, project.current().connections_dir):
            for path in sorted(folder.glob("*.json")):
                try:
                    source = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    continue
                if isinstance(source, dict) and source.get("schema") == old:
                    source["schema"] = new
                    try:
                        engine.write_json(path, source)
                    except OSError as exc:
                        self.app.set_status(self.t("sc_move_failed", error=str(exc)))
                        continue
                    changed.setdefault(folder, []).append(path.stem)
        try:
            from domains import connection as connection_model   # only here, the one place this tab exports a calculation
            if project.current().connectors_dir in changed:
                connector_model.export(project.current().connectors_dir, project.current().data_dir)
            if project.current().connections_dir in changed:
                connection_model.export(project.current().connections_dir, project.current().data_dir)
        except Exception as exc:  # broad: the files are renamed; the export's own message says what else is wrong
            self.app.set_status(self.t("sc_move_failed", error=str(exc)))
        for tab in getattr(self.app, "tabs", []):
            if tab is not self and hasattr(tab, "schema_renamed"):
                tab.schema_renamed(old, new)
        names = [stem for stems in changed.values() for stem in stems]
        if names:
            self.app.set_status(self.t("sc_renamed_references", old=old, new=new, names=", ".join(names)))
        return names

    def export(self, sid, done_text):
        """The schemas' part of the export, run here and now: data/schemas.json and data/schemas/, from every saved source."""
        try:
            notes = model.export(project.current().details_dir, project.current().data_dir, self.known_positions(), self.values)
        except (validation.ValidationError, engine.EngineError, OSError) as exc:
            autosave.warn(self, "Woodcore", self.t("sc_export_failed", id=sid, error=exc))
            return False
        mine = [n for n in notes if n.startswith(f"schema {sid}:")]
        self.app.set_status(self.t("sc_saved_warnings", id=sid, n=len(mine)) if mine else done_text)
        return True

    # -- surviving a rebuild -----------------------------------------------------------

    def view_state(self):
        return {
            "draft": copy.deepcopy(self.source),
            "current_id": self.current_id,
            "dirty": self.dirty,
            "tool": self.canvas.tool,
            "area_mode": self.canvas.area_mode,
            "grid": self.grid_combo.currentIndex(),
            "snap": self.snap_button.isChecked(),
            "list_tab": self.tables.currentIndex(),
            "splitter": self.splitter.sizes(),
            "center": self.center_split.sizes(),
            "columns": {which: columns.state() for which, columns in self.table_columns.items()},
            "empty_folders": list(self.empty_folders),
        }

    def restore(self, state):
        if state:
            self.grid_combo.setCurrentIndex(state.get("grid", 0))
            self.snap_button.setChecked(state.get("snap", True))
            self.tables.setCurrentIndex(state.get("list_tab", 0))
            self.empty_folders = list(state.get("empty_folders") or [])
            # the widths the engineer dragged the lists' columns to, before the lists are filled with them
            for which, widths in (state.get("columns") or {}).items():
                if which in self.table_columns:
                    self.table_columns[which].restore(widths)
            mode = state.get("area_mode", "diagonal")
            if mode in AREA_MODES:
                self.area_combo.setCurrentIndex(AREA_MODES.index(mode))
            self.open_source(state["draft"], state.get("current_id"), state.get("dirty", False))
            self.reload_list(select=self.current_id)
            if state.get("splitter"):
                self.splitter.setSizes(state["splitter"])
            if state.get("center"):
                self.center_split.setSizes(state["center"])
                # the heights the engineer set, the bar's pane left as he set it rather than made snug again
                self.bar_area.snug_on_show = False
            self.choose_tool(state.get("tool", "select"))
        else:
            self.splitter.setSizes([1800, 7000, 4600])
            self.load_first()
            self.choose_tool("select")
