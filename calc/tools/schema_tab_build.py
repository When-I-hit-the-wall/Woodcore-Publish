"""SchemaTab's building -- the list, the tool bar and its buttons, the canvas, the tables and the right pane's properties -- a mixin of methods moved verbatim out of calc/tools/schema_tab.py (issue #30). SchemaTab names it among its bases.
"""

from PySide6.QtCore import QEvent, QSize, Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QSpinBox, QSplitter, QTabWidget,
    QTableWidget, QTableWidgetItem, QToolButton, QVBoxLayout, QWidget,
)
from check_cell import CentredCheck  # a tick centred in its cell (v0.77)
import grouped_list
import source_archive  # «Supprimer» archives (source_archive.py)
import identity
import project  # where the project this tab works on is (calc/project.py)
import stylefactors  # the three factors of a drawing and of one entry of it, typed the way every tab types them (stylefactors.py, v0.99)
import theme  # the colours this tab states itself (theme.py, v0.90)
import dimension_icons  # the dimension tools' symbols, the same in the three tabs (issue #9)
import cards  # the properties in cards, after the website (cards.py, v0.95)
from domains import schema as model
from domains import schema_svg
import flowbar
from flowbar import (BAR_SPACING, TOOL_ICON_PX, FlowLayout, FlowWidget, ResizableColumns, ToolBarArea,
                     set_tip, size_tool, symbol_px, tool_group)
from schema_canvas import AREA_MODES, CONNECTOR_TOOLS, TOOLS, SchemaCanvas
from schema_tab_words import STRINGS, TIPS, tip_key  # split out of this module (issue #30): every name it had is still importable from it
import svg_icons


# The grid steps the engineer may force, beside «auto» -- millimetres, a detail's own unit.
GRID_CHOICES = ("auto", 1000.0, 100.0, 10.0, 1.0)


# The bar's own measures (flowbar.py): a tool's symbol drawn at the size it is shown (flowbar.symbol_px), every control flowbar.tool_height() tall -- a tool of the position plan's bar, measured (v0.94) -- and ICON_PX where no button gives a symbol its size.
ICON_PX = TOOL_ICON_PX


# The tool bar, in the groups the plan names, after the navigation and the history. Every tool its symbol alone since v0.94 -- the engineer: «Les icônes sont suffisamment compréhensibles pour qu'il ne faille pas de nom» --, its name and how it is used being its tooltip (TIPS), and the groups parted by a thin line with no title (flowbar.tool_group). Until then the pieces and the verbs carried their names under their symbols, and the six construction lines had shown their symbols alone since v0.75, their names under them having made the group 950 px wide on its own.
TOOL_GROUPS = (
    ("sc_group_elements", (("linear", "sc_tool_linear"), ("area", "sc_tool_area"))),
    ("sc_group_connectors", tuple(
        (f"connector:{kind}", key) for kind, key in zip(
            CONNECTOR_TOOLS,
            ("sc_tool_nail", "sc_tool_dowel", "sc_tool_screw", "sc_tool_bolt", "sc_tool_ring"),
        )
    )),
    ("sc_group_aids", (("aid-centre", "sc_tool_centre"), ("aid-point", "sc_tool_point"),
                       ("aid-vertical", "sc_tool_vertical"),
                       ("aid-horizontal", "sc_tool_horizontal"),
                       ("aid-point-angle", "sc_tool_point_angle"),
                       ("aid-perpendicular", "sc_tool_perpendicular"),
                       ("aid-parallel", "sc_tool_parallel"),
                       ("aid-two-points", "sc_tool_two_points"))),
    ("sc_group_modify", (("move", "sc_tool_move"), ("duplicate", "sc_tool_duplicate"),
                         ("rotate", "sc_tool_rotate"), ("mirror", "sc_tool_mirror"))),
    ("sc_group_dimensions", (("dimension-horizontal", "sc_tool_dim_horizontal"),
                             ("dimension-vertical", "sc_tool_dim_vertical"),
                             ("dimension-parallel", "sc_tool_dim_parallel"),
                             ("dimension-angle", "sc_tool_dim_angle"))),
    ("sc_group_texts", (("text", "sc_tool_text"),)),
)


# The three ways «Surfacique» draws a rectangle, each shown by its symbol in the bar (flowbar.SymbolCombo, v0.94) and by its words in the list it opens: two opposite corners; an edge and a third click off it; an edge and a width typed. SVG text on a 24 px square, `{c}` the scheme's ink.
AREA_MODE_SVG = {
    "diagonal": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
                '<rect x="4" y="6" width="16" height="12" fill="none" stroke="{c}" stroke-width="1.3"/>'
                '<path d="M4 18 L20 6" fill="none" stroke="{c}" stroke-width="1.2" stroke-dasharray="2.4,1.8"/>'
                '<circle cx="4" cy="18" r="2.3" fill="{c}"/><circle cx="20" cy="6" r="2.3" fill="{c}"/></svg>',
    "edge": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
            '<rect x="4" y="6" width="16" height="12" fill="none" stroke="{c}" stroke-width="1.1"/>'
            '<path d="M4 18 H20" fill="none" stroke="{c}" stroke-width="2.8"/>'
            '<circle cx="4" cy="18" r="2.3" fill="{c}"/><circle cx="20" cy="18" r="2.3" fill="{c}"/>'
            '<circle cx="12" cy="6" r="2.3" fill="{c}"/></svg>',
    "typed": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
             '<rect x="3" y="6" width="14" height="12" fill="none" stroke="{c}" stroke-width="1.1"/>'
             '<path d="M3 18 H17" fill="none" stroke="{c}" stroke-width="2.8"/>'
             '<circle cx="3" cy="18" r="2.3" fill="{c}"/><circle cx="17" cy="18" r="2.3" fill="{c}"/>'
             '<path d="M21.5 8 V16" fill="none" stroke="{c}" stroke-width="1.2"/>'
             '<polygon points="21.5,5 19.5,8.6 23.5,8.6" fill="{c}"/><polygon points="21.5,19 19.5,15.4 23.5,15.4" fill="{c}"/></svg>',
}


def plain_label(text, wrap=False):
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(wrap)
    return label


def icon_from_svg(text, size=ICON_PX):
    """An icon from SVG text, `size` logical pixels square (svg_icons.svg_icon)."""
    return svg_icons.svg_icon(text, size)


def swatch_kind(tool):
    """Which swatch a tool shows, by name, or None for one that shows none (Sélection, Vue).

    ⚠️ Three name collisions live here, which is why this is a function and not a mapping written out twice. An aid line and a dimension share `horizontal`, `vertical` and `parallel`, so a dimension asks for its own by the name `schema_svg.DIMENSION_SWATCHES` gives it -- without which the four cotation buttons would all draw a dashed construction line. And a **modification verb** names no kind at all: it draws nothing, so its swatch is keyed by the verb.

    👉 `tests/test_schema_tab.py` asks *this* rather than restating it. It restated it until v0.73, and the restatement is what broke the moment a tool arrived whose spec has a `verb` and no `kind` -- a guard failing because the thing it guards grew correctly.
    """
    spec = TOOLS.get(tool, {})
    geo = spec.get("geo")
    if geo in ("linear", "area"):
        return geo
    if geo == "dimension":
        return schema_svg.DIMENSION_SWATCHES[spec["kind"]]
    if geo == "modify":
        return spec["verb"]
    if geo == "text":
        return "text"   # figure_text's T (issue #43)
    return spec.get("kind")


def on_ground(svg):
    """A swatch with the figure's black ink and white fill put into the scheme's ink and ground (theme.py, v0.90), the way statics_tab and connectors_tab recolour theirs: the four cotation tools and the fasteners were drawn black on the dark scheme's buttons, and all but invisible. The colours that say which symbol it is -- the wood, the construction grey, a point's green -- stay the figure's. Through svg_icons.recolour."""
    from domains import connector_svg
    svg = svg.replace(schema_svg.DIMENSION, connector_svg.SWATCH_INK)
    return svg_icons.recolour(svg, connector_svg.SWATCH_INK, connector_svg.SWATCH_FILL, theme.colour("ink"), theme.colour("bg"))


def tool_icon(tool, size=ICON_PX):
    """A tool's own symbol, drawn by the module that draws the figure -- the bar shows what it draws (statics_tab's and connectors_tab's own rule) -- in the scheme's ink (on_ground). A dimension tool's is the one the static models and the position plans show (dimension_icons, issue #9)."""
    if tool in dimension_icons.TOOLS:
        return dimension_icons.icon(tool, size if isinstance(size, int) else size.height())
    kind = swatch_kind(tool)
    if kind is None:
        return None
    return icon_from_svg(on_ground(schema_svg.swatch(kind)), size)


class SchemaBuildMixin:
    """Methods of schema_tab.SchemaTab, moved verbatim (issue #30): the class names this mixin among its bases."""

    def heading(self, text):
        label = plain_label(text)
        label.setFont(self.app.bold_font)
        return label

    def note(self, text):
        """An explanation, muted and wrapping, as a card's note is (cards.note)."""
        return cards.note(text)

    def bar_tip(self, widget, name_key, tip_key):
        """Names a control of the bar and says how it is used (flowbar.set_tip), and keeps the two keys it said it with in `bar_tips` -- what tests/test_toolbar.py reads each language's words back by."""
        set_tip(widget, self.t(name_key), self.t(tip_key))
        self.bar_tips.append((widget, name_key, tip_key))
        return widget

    def bar_button(self, icon, name_key, tip_key, checkable=False):
        """A control of the tool bar: its symbol alone in a square button as tall as a tool of the position plan's bar (flowbar.size_tool), and its name in bold with how it is used in the tooltip the pointer shows after half a second (flowbar.set_tip, v0.94)."""
        button = QToolButton()
        button.setCheckable(checkable)
        button.setAutoRaise(True)
        if icon is not None and not icon.isNull():
            button.setIcon(icon)
        else:
            button.setText(self.t(name_key))     # nothing draws a symbol for it: its word, kept compact
        self.bar_tip(button, name_key, tip_key)
        size_tool(button)
        return button

    def tool_button(self, tool, key):
        """One tool, its symbol alone -- the very symbol the figure draws, in the scheme's ink (on_ground), or the bar's own for the navigation (flowbar.ICONS) -- since the engineer judged the symbols clear enough to need no name (v0.94)."""
        px = symbol_px(self.font())
        icon = tool_icon(tool, px)
        if icon is None and tool in flowbar.ICONS:
            icon = flowbar.icon(tool, px, theme.colour("ink"))
        button = self.bar_button(icon, key, tip_key(tool), checkable=True)
        button.clicked.connect(lambda _checked=False, name=tool: self.choose_tool(name))
        self.tool_buttons[tool] = button
        self.tool_group.addButton(button)
        return button

    def action_button(self, icon, key, tip, slot):
        """A button that acts rather than a tool the canvas holds -- «Ajuster», «Grille…», «Effacer les lignes», «Trancher», «Fusionner» -- its symbol alone like every tool (v0.94)."""
        button = self.bar_button(icon, key, tip)
        button.clicked.connect(slot)
        return button

    def group_box(self, key, widgets):
        """One group of the bar: its controls side by side, a thin line before them and no title (flowbar.tool_group, v0.94), its name the group's accessible name."""
        return tool_group(widgets, self.t(key))

    def build_bar(self):
        """The navigation, the history and the groups the plan names, laid out in a FlowLayout so a bar too wide for its pane takes another line rather than losing a tool (flowbar.py, v0.67's own rule) -- since v0.94 after the position plan's bar: every control its symbol alone and as tall as the plan's tools, the groups parted by a thin line and named by no title."""
        self.tool_buttons = {}
        self.bar_tips = []      # (control, name key, use key), every control of the bar
        self.action_buttons = {}
        self.tool_group = QButtonGroup(self)
        self.tool_group.setExclusive(True)
        bar = FlowWidget()
        flow = FlowLayout(bar, spacing=BAR_SPACING)
        px = symbol_px(self.font())
        ink = theme.colour("ink")

        navigation = []
        for tool, key in (("select", "sc_tool_select"), ("pan", "sc_tool_pan"), ("crop", "sc_tool_frame")):
            navigation.append(self.tool_button(tool, key))
        navigation.append(self.action_button(flowbar.icon("fit", px, ink), "sc_tool_fit", "sc_tip_fit", self.canvas.fit))
        # the grid's step and the snapping are settings rather than tools: a combo as tall as a button, and a toggle drawn as a magnet
        self.grid_combo = QComboBox()
        for choice in GRID_CHOICES:
            self.grid_combo.addItem("auto" if choice == "auto" else f"{choice:g} mm", choice)
        flowbar.size_combo(self.grid_combo)
        self.bar_tip(self.grid_combo, "sc_grid_step", "sc_tip_grid_step")
        self.grid_combo.currentIndexChanged.connect(self.on_grid)
        self.snap_button = self.bar_button(flowbar.icon("snap", px, ink), "sc_snap", "sc_tip_snap", checkable=True)
        self.snap_button.setChecked(True)
        self.snap_button.toggled.connect(self.on_snap)
        navigation += [self.grid_combo, self.snap_button]
        flow.addWidget(self.group_box("sc_group_navigation", navigation))

        history = []
        for name, key, tip, slot in (("undo", "sc_undo", "sc_tip_undo", self.undo), ("redo", "sc_redo", "sc_tip_redo", self.redo)):
            history.append(self.action_button(flowbar.icon(name, px, ink), key, tip, slot))
        self.undo_button, self.redo_button = history
        flow.addWidget(self.group_box("sc_group_history", history))

        for group_key, tools in TOOL_GROUPS:
            widgets = [self.tool_button(tool, key) for tool, key in tools]
            if group_key == "sc_group_elements":
                self.area_combo = flowbar.SymbolCombo()
                self.area_combo.setIconSize(QSize(px, px))
                for mode, key in zip(AREA_MODES, ("sc_area_diagonal", "sc_area_edge", "sc_area_typed")):
                    self.area_combo.addItem(flowbar.svg_text_icon(AREA_MODE_SVG[mode].format(c=ink), px), self.t(key), mode)
                self.bar_tip(self.area_combo, "sc_area_mode", "sc_tip_area_mode")
                self.area_combo.currentIndexChanged.connect(self.on_area_combo)
                widgets.append(self.area_combo)
            if group_key == "sc_group_connectors":
                # «Grille…» is a **button and not a tool**: it places a whole group at once and has
                # nothing on the grid to point at, exactly as «Trancher» and «Fusionner» do.
                grid = self.action_button(flowbar.icon("marker-grid", px, ink), "sc_grid", "sc_grid_tip", self.place_grid)
                self.action_buttons["grid"] = grid
                widgets.append(grid)
            if group_key == "sc_group_aids":
                widgets.append(self.action_button(flowbar.icon("clear-lines", px, ink), "sc_clear_aids", "sc_clear_aids_tip",
                                                  self.canvas.clear_aid_lines))
            if group_key == "sc_group_modify":
                # «Trancher» and «fusionner» are **actions, not tools**: they act on what is already
                # selected, so there is nothing on the grid for them to point at and nothing for the
                # exclusive tool group to hold checked. Hence plain buttons beside the four verbs.
                for verb, key, tip, slot in (
                    ("split", "sc_split", "sc_split_tip", self.canvas.split_selection),
                    ("merge", "sc_merge", "sc_merge_tip", self.canvas.merge_selection),
                ):
                    button = self.action_button(icon_from_svg(on_ground(schema_svg.swatch(verb)), px), key, tip, slot)
                    self.action_buttons[verb] = button
                    widgets.append(button)
            flow.addWidget(self.group_box(group_key, widgets))

        # ⚠️ Never a vertical scroll (v0.75): what the height does not hold goes to the right and the bar
        # scrolls sideways -- the static models' own ToolBarArea, shared. A bare QScrollArea with its
        # vertical bar hidden, which this was until v0.75, still clipped a row and scrolled it under the wheel.
        self.bar_area = ToolBarArea(bar)
        return self.bar_area

    def build_center(self):
        """The three panes the engineer drags: the tool bar, the drawing, the lists (v0.66's own arrangement)."""
        self.canvas = SchemaCanvas()
        self.canvas.about_to_change.connect(self.remember)
        self.canvas.changed.connect(self.on_canvas_change)
        self.canvas.selection_changed.connect(self.on_selection)
        self.canvas.tool_changed.connect(self.on_tool_changed)
        self.canvas.pointer.connect(self.on_pointer)
        self.canvas.tool_done.connect(lambda: self.choose_tool("select"))
        self.canvas.refused.connect(self.on_refused)

        panel = QWidget()
        box = QVBoxLayout(panel)
        box.setContentsMargins(0, 0, 0, 0)
        self.center_split = QSplitter(Qt.Orientation.Vertical)
        self.center_split.setChildrenCollapsible(False)
        self.center_split.addWidget(self.build_bar())
        self.center_split.addWidget(self.canvas)
        self.center_split.addWidget(self.build_tables())
        # the drawing is what the height is wanted for (statics_tab's own stretch factors, v0.66)
        for index, stretch in ((0, 0), (1, 5), (2, 3)):
            self.center_split.setStretchFactor(index, stretch)
        box.addWidget(self.center_split, 1)
        self.warnings = self.note("")
        self.warnings.setFixedHeight(34)
        box.addWidget(self.warnings)
        return panel

    def build_tables(self):
        self.tables = QTabWidget()
        self.table_widgets = {}
        self.table_columns = {}
        for name, key, columns in self.TABLE_SPECS:
            table = QTableWidget(0, len(columns))
            table.setHorizontalHeaderLabels([self.t(c) for c in columns])
            # the columns are the engineer's to widen by dragging the header's dividers, each starting at the width of what it holds (flowbar.ResizableColumns) -- stretched over the list until then, which no divider can be dragged in
            self.table_columns[name] = ResizableColumns(table)
            table.verticalHeader().setVisible(False)
            table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            # Ctrl and Shift, the way the left pane's folders take them (v0.69) and the way an
            # explorer does. ⚠️ A table holds one collection, so a selection spanning two of them
            # shows in each tab as its own share of it; the canvas is what holds the whole.
            table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
            table.itemChanged.connect(lambda item, which=name: self.on_cell(which, item))
            table.itemSelectionChanged.connect(lambda which=name: self.on_table_selection(which))
            # the row under the pointer lights its entry on the drawing (v0.75) -- the plan's «le survol d'une ligne met l'objet en évidence»
            table.setMouseTracking(True)
            table.cellEntered.connect(lambda row, _column, which=name: self.on_row_hover(which, row))
            table.viewport().installEventFilter(self)
            # a column that holds a tick and nothing else has it in its middle, under its centred header (v0.77, check_cell.py)
            for (which, column) in self.CHECK_COLUMNS:
                if which == name:
                    table.setItemDelegateForColumn(column, CentredCheck(table))
            self.table_widgets[name] = table
            page = QWidget()
            box = QVBoxLayout(page)
            box.setContentsMargins(4, 4, 4, 4)
            box.addWidget(table, 1)
            row = QHBoxLayout()
            add = QPushButton(self.t("sc_add"))
            add.clicked.connect(lambda _checked=False, which=name: self.add_row(which))
            remove = QPushButton(self.t("sc_remove"))
            remove.clicked.connect(self.canvas.delete_selection)
            row.addWidget(add)
            row.addStretch(1)
            row.addWidget(remove)
            box.addLayout(row)
            table.setMinimumHeight(2 * self.fontMetrics().height())
            self.tables.addTab(page, self.t(key))
        # A table's own minimum is its header and several rows, which would stop the splitter long before the drawing had gained anything (statics_tab's own floor, v0.66).
        self.tables.setMinimumHeight(5 * self.fontMetrics().height() + 52)
        return self.tables

    def build_properties(self):
        panel = QWidget()
        shell = QVBoxLayout(panel)
        shell.setContentsMargins(6, 0, 0, 0)
        # the properties in cards on the soft ground, after the website: a column that scrolls up and down only and is never narrower than its cards (cards.py)
        area, outer = cards.column()
        shell.addWidget(area, 1)

        # The options of the tool chosen, first in the pane and only while «Surfacique» is the tool (v0.117, the engineer: «lorsque je sélectionne l'outil "Surfacique", dans le volet de droite, je dois déjà voir les options pour cet outil»): the drawing mode -- the tool bar's, one value behind the two --, the position the element is of, and which of its dimensions is drawn; the other is the position's, fixed.
        self.tool_box = cards.card(self.t("sc_tool_options"))
        tool_form = cards.form(self.tool_box)
        self.tool_mode_combo = QComboBox()
        for mode, key in zip(AREA_MODES, ("sc_area_diagonal", "sc_area_edge", "sc_area_typed")):
            self.tool_mode_combo.addItem(self.t(key), mode)
        self.tool_mode_combo.currentIndexChanged.connect(self.on_tool_mode)
        tool_form.addRow(self.t("sc_area_mode"), self.tool_mode_combo)
        self.tool_position_combo = QComboBox()
        self.tool_position_combo.currentIndexChanged.connect(self.on_tool_position)
        tool_form.addRow(self.t("sc_position"), self.tool_position_combo)
        self.tool_draw_caption = QLabel(self.t("sc_tool_draw"))
        self.tool_draw_combo = QComboBox()
        self.tool_draw_combo.addItem(self.t("sc_tool_draw_b"), "b")
        self.tool_draw_combo.addItem(self.t("sc_tool_draw_h"), "h")
        self.tool_draw_combo.currentIndexChanged.connect(self.update_area_fixed)
        tool_form.addRow(self.tool_draw_caption, self.tool_draw_combo)
        self.tool_fixed_note = self.note("")
        tool_form.addRow(self.tool_fixed_note)
        outer.addWidget(self.tool_box)
        self.tool_box.setVisible(False)

        # Nom · Description · ID, the identity of every tab of the window (identity.py). The folder is not a field: it is set by dragging the schema in the left pane.
        identity_box = cards.card(self.t("sc_identity"))
        form = cards.form(identity_box)
        self.identity = identity.IdentityRows(form, self.t, self.on_identity)
        self.name_edit, self.label_edit, self.id_edit = self.identity.name, self.identity.description, self.identity.id
        outer.addWidget(identity_box)

        # The drawing's own three factors (v0.99): the plans' and the static models' three sliders, with the same names, the same range and the same meaning -- `line` on the strokes, `point` on the symbols placed on a point, `text` on the texts (figure_style). A schema had none at all until now, so a schema that states none is drawn exactly as it was.
        style_box = cards.card(self.t("sc_group_style"))
        style_form = cards.form(style_box)
        self.style_sliders = {}
        for key in model.STYLE_KEYS:
            widget, slider, _readout = stylefactors.percent()
            slider.sliderPressed.connect(self.remember)   # one drag is one step of «Annuler»: the state before it is pushed once, here
            slider.valueChanged.connect(lambda value, which=key: self.on_style(which, value))
            self.style_sliders[key] = slider
            style_form.addRow(self.t(f"sc_style_{key}"), widget)
        outer.addWidget(style_box)

        self.selection_box = cards.card(self.t("sc_selection"))
        self.selection_form = cards.form(self.selection_box)
        self.selection_note = self.note(self.t("sc_none_selected"))
        self.selection_form.addRow(self.selection_note)
        # v0.75: what an element IS -- its position, the side its view shows, its section b and h, each following
        # the position unless written over (orange, with «Reprendre»), and the label written on it.
        self.element_rows = []
        self.position_combo = QComboBox()
        self.position_combo.currentIndexChanged.connect(self.on_position)
        # beside it, a position the sheet does not have yet, opened in the «Positions» tab through the window (MainWindow.new_position, v0.94)
        self.new_position_button = QToolButton()
        self.new_position_button.setText("+")
        self.new_position_button.setToolTip(self.t("po_new_position_tip"))
        self.new_position_button.clicked.connect(lambda _checked=False: self.app.new_position())
        position_cell = QWidget()
        position_row = QHBoxLayout(position_cell)
        position_row.setContentsMargins(0, 0, 0, 0)
        position_row.addWidget(self.position_combo, 1)
        position_row.addWidget(self.new_position_button)
        self.element_rows.append(self.form_row(self.t("sc_position"), position_cell))
        self.view_combo = QComboBox()
        for view in model.ELEMENT_VIEWS:
            self.view_combo.addItem(self.t(f"sc_view_{view}"), view)
        self.view_combo.currentIndexChanged.connect(self.on_view)
        self.view_row = self.form_row(self.t("sc_view"), self.view_combo)
        self.element_rows.append(self.view_row)
        self.side_fields = {}
        for side in model.ELEMENT_SIDES:
            spin = QDoubleSpinBox()
            spin.setRange(0.1, 100000.0)
            spin.setDecimals(1)
            spin.setSuffix(" mm")
            spin.setKeyboardTracking(False)
            spin.valueChanged.connect(lambda value, which=side: self.on_side(which, value))
            note = QLabel("")
            note.setWordWrap(True)
            back = QPushButton(self.t("sc_take_back"))
            back.clicked.connect(lambda _checked=False, which=side: self.take_back(which))
            line = QWidget()
            row = QHBoxLayout(line)
            row.setContentsMargins(0, 0, 0, 0)
            row.addWidget(note, 1)
            row.addWidget(back)
            self.side_fields[side] = {"spin": spin, "note": note, "back": back, "line": line}
            self.element_rows.append(self.form_row(side, spin))
            # the line under a side is shown only when there is something orange to say (fill_element): kept out of element_rows, whose rows the selection shows whole
            self.side_fields[side]["row"] = self.form_row("", line)
        self.element_label_edit = QLineEdit()
        self.element_label_edit.textEdited.connect(self.on_element_label)
        self.element_rows.append(self.form_row(self.t("sc_element_label"), self.element_label_edit))
        # What a dimension writes beside itself -- a static model's own four, `show` -- and its name, the `label` that choice may print: the list's two columns, in the panel.
        self.dim_show_combo = QComboBox()
        for value, key in zip(model.LABEL_MODES, self.SHOW_KEYS):
            self.dim_show_combo.addItem(self.t(key), value)
        self.dim_show_combo.currentIndexChanged.connect(self.on_dim_show)
        self.dim_name_edit = QLineEdit()
        self.dim_name_edit.editingFinished.connect(self.on_dim_name)
        self.dim_rows = [self.form_row(self.t("sc_dim_show"), self.dim_show_combo),
                         self.form_row(self.t("sc_dim_name"), self.dim_name_edit)]
        # A text's pane (issue #43): text_pane's, built for the text selected and taken down with the selection
        self.text_holder = QWidget()
        self.text_layout = QVBoxLayout(self.text_holder)
        self.text_layout.setContentsMargins(0, 0, 0, 0)
        self.text_pane = None
        self.selection_form.addRow(self.text_holder)
        # The factors this entry states over the drawing's (v0.99): a card inside the selection's card, as a titled «Pièce» is inside a connector's (v0.95), so the selection stays readable when it grows three more rows. Only the factors the entry is drawn with are shown, and one it states is orange with «Reprendre» -- an overridden b/h's own way of saying it (v0.75).
        self.entry_style_box = cards.card(self.t("sc_style_own"))
        entry_style = cards.form(self.entry_style_box)
        entry_style.addRow(self.note(self.t("sc_style_own_note")))
        self.entry_style = stylefactors.EntryRows(entry_style, self.t, "sc", self.on_entry_style, self.take_back_style)
        self.selection_form.addRow(self.entry_style_box)
        outer.addWidget(self.selection_box)

        crop = cards.card(self.t("sc_crop_box"))
        crop_box = QVBoxLayout(crop)
        self.crop_text = self.note(self.t("sc_crop_none"))
        crop_box.addWidget(self.crop_text)
        crop_row = QHBoxLayout()
        draw = QPushButton(self.t("sc_crop_draw"))
        draw.clicked.connect(lambda: self.choose_tool("crop"))
        reset = QPushButton(self.t("sc_crop_reset"))
        reset.clicked.connect(lambda: self.canvas.set_crop(None))
        crop_row.addWidget(draw)
        crop_row.addWidget(reset)
        crop_box.addLayout(crop_row)
        outer.addWidget(crop)

        outer.addStretch(1)

        row = QHBoxLayout()
        revert = QPushButton(self.t("sc_revert"))
        revert.clicked.connect(self.revert)
        save = QPushButton(self.t("sc_save"))
        save.setDefault(True)
        save.clicked.connect(self.save)
        row.addWidget(revert)
        row.addWidget(save)
        shell.addLayout(row)
        return panel
