"""PlanTab's building and drawing of a position plan -- the centre and the right pane, the plan's scale, storey, type and section, its dimensions and lengths, its calibration and background -- a mixin of methods moved verbatim out of calc/tools/plan_tab.py (issue #30). PlanTab names it among its bases.
"""

from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPlainTextEdit, QPushButton, QSizePolicy, QSpinBox, QVBoxLayout, QWidget,
)
import identity
import positions_store  # the project's positions, Woodcore's own file (calc/positions_store.py, v0.114)
import dimension_icons  # the dimension tools' symbols, the static models' and the schemas' own (issue #9)
import project  # where the project this tab works on is (calc/project.py)
import theme  # the colours this tab states itself (theme.py, v0.90)
import cards  # the properties in cards, after the website (cards.py)
import usersettings  # the engineer's own settings: what a view shows (issue #9)
from domains import plan as model
from domains import plan_svg
from domains import figure_text  # the Text tool's symbol (issue #43)
from plan_canvas_editing import TEXT_TOOL
from flowbar import FlowLayout, FlowWidget
from plan_canvas import PlanCanvas
import plan_canvas_edit  # «Déplacer», «Copier» and «Ligne d'aide» (issue #18)
import drawing_tab  # what every tab of plans drawn on imported documents shares (v0.115)
from drawing_tab import (  # noqa: F401 -- names the tab's own code uses, and names other modules and the tests read here
    Blank, CurrentStack, DrawingTab, HISTORY, KINDS, NEW_ROW, document_text, next_free_id, number_text, plain_label, plan_text, svg_icon,
)


# The tools of the first row, by name, and the STE tools of the second, by type letter; a section's two of its own (v0.114).
# The crop and the calibration are no tools of the bar since v0.116: they are reached from the right pane alone, «Dessiner le cadre» in «Cadrage» and «Calibrer…» in «Échelle» (PANE_TOOLS) -- the canvas's modes are the same.
TOOLS = ("select", "pan", "ruler", "axis-v", "axis-h", "axis-o")


STOREY_TOOLS = ("storey-line", "storey-box")


# A section's third tool (v0.116): the load transfer level, «Niveau de reprise des charges» (STE Compact 02 p. 14).
LEVEL_TOOL = "load-level"


SECTION_TOOLS = STOREY_TOOLS + (LEVEL_TOOL,)


SUBTYPE_TOOLS = {t for t in model.TYPES if model.TYPES[t].get("subtypes")}


# The engineer's setting of the view «Dessin»: the plans' dimensions shown or not (issue #9, REQ-011).
DRAW_DIMENSIONS = "plan_draw_dimensions"


# A box drawn dashed: the storey box tool's symbol.
STOREY_BOX_ICON = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 26 18"><rect x="3" y="3" width="20" height="12" '
                   'fill="{mark}" fill-opacity="0.25" stroke="{mark}" stroke-width="1.4" stroke-dasharray="3 2"/></svg>').format(mark=theme.colour("plan-storey-mark"))


UNITS = {"pdf": "pt", "png": "px", "jpg": "px", "svg": "", None: "pt"}


def list_plans(folder=None):
    """(id, source, folder) of every saved plan, in file-name order -- the source read from its file, or None for one that cannot be read, which is listed by its name. The folder is the source's own `group` field (grouped_list.py)."""
    return drawing_tab.list_sources(model, folder or project.current().plans_dir)


class PlanBuildMixin:
    """Methods of plan_tab.PlanTab, moved verbatim (issue #30): the class names this mixin among its bases."""

    def build_plan_center(self):
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(6, 0, 6, 0)
        # The bar is two rows that wrap -- the navigation tools, then the STE tools (v0.67, flowbar.py). In one grid it demanded the width of its widest row, which became the centre pane's minimum width and left the splitter no play to be dragged in; and the two rows sharing the grid's columns is what elided their labels.
        self.tool_rows = []
        for _ in range(2):
            holder = FlowWidget()
            FlowLayout(holder, spacing=2)
            self.tool_rows.append(holder)
            v.addWidget(holder)
        top, tools = (holder.layout() for holder in self.tool_rows)
        self.tool_group = QButtonGroup(self)
        self.tool_group.setExclusive(True)
        self.tool_buttons = {}
        axis_icon = svg_icon(plan_svg.swatch("Achse"))
        for tool in TOOLS:
            text = self.t(f"plan_tool_{tool.replace('-', '_')}")
            button = self.tool_button(text, icon=axis_icon if tool.startswith("axis") else None)
            button.clicked.connect(lambda _checked=False, tool=tool: self.choose_tool(tool))
            self.tool_group.addButton(button)
            self.tool_buttons[tool] = button
            top.addWidget(button)
        # «Déplacer» and «Copier», then the construction aids (issue #18, plan_canvas_edit.py) -- the aids the position plan's alone (D-015)
        for tool in plan_canvas_edit.EDIT_TOOLS + tuple(plan_canvas_edit.AID_TOOLS):
            key = tool.replace('-', '_')
            button = self.tool_button(self.t(f"plan_tool_{key}"), self.t(f"plan_tip_{key}") if tool in plan_canvas_edit.AID_TOOLS else None)
            button.clicked.connect(lambda _checked=False, tool=tool: self.choose_tool(tool))
            self.tool_group.addButton(button)
            self.tool_buttons[tool] = button
            top.addWidget(button)
        # the Text tool (issue #43), the four drawing engines' one: text_pane's T
        button = self.tool_button(self.t("plan_tool_text"), self.t("plan_tip_text"), svg_icon(figure_text.icon_svg(theme.colour("ink"))))
        button.clicked.connect(lambda _checked=False: self.choose_tool(TEXT_TOOL))
        self.tool_group.addButton(button)
        self.tool_buttons[TEXT_TOOL] = button
        top.addWidget(button)
        # the STE tools, then the load-path plan's two load tools (v0.116), shown on a load-path plan alone (apply_plan_type)
        for type_ in model.TYPE_ORDER + model.LOAD_TYPES:
            text = model.TYPES[type_]["prefix"] if model.is_load(type_) else type_
            button = self.tool_button(text, self.t(f"plan_type_{type_}"), svg_icon(plan_svg.swatch(type_, model.default_subtype(type_))))
            button.clicked.connect(lambda _checked=False, tool=type_: self.choose_tool(tool))
            self.tool_group.addButton(button)
            self.tool_buttons[type_] = button
            tools.addWidget(button)
        for tool in dimension_icons.TOOLS:
            button = self.tool_button("", self.t(f"plan_tool_{tool.replace('-', '_')}"), dimension_icons.icon(tool, 20))
            button.clicked.connect(lambda _checked=False, tool=tool: self.choose_tool(tool))
            self.tool_group.addButton(button)
            self.tool_buttons[tool] = button
            tools.addWidget(button)
            if model.is_load(type_):
                button.hide()
        self.subtype_combo = QComboBox()
        self.subtype_combo.currentIndexChanged.connect(self.on_tool_subtype)
        tools.addWidget(self.subtype_combo)
        for key, slot in (("plan_undo", self.undo), ("plan_redo", self.redo), ("plan_fit", lambda: self.canvas.fit())):
            button = self.tool_button(self.t(key), checkable=False)
            button.clicked.connect(slot)
            tools.addWidget(button)
        # A section's own row, shown on a section alone (v0.114): its storey line and storey box, and the storey they draw.
        self.section_row = FlowWidget()
        FlowLayout(self.section_row, spacing=2)
        icons = {"storey-line": axis_icon, "storey-box": svg_icon(STOREY_BOX_ICON), LEVEL_TOOL: svg_icon(plan_svg.swatch("Lastniveau"))}
        for tool in SECTION_TOOLS:
            button = self.tool_button(self.t(f"plan_tool_{tool.replace('-', '_')}"), icon=icons[tool])
            button.clicked.connect(lambda _checked=False, tool=tool: self.choose_tool(tool))
            self.tool_group.addButton(button)
            self.tool_buttons[tool] = button
            self.section_row.layout().addWidget(button)
        self.section_row.layout().addWidget(plain_label(self.t("plan_storey_choice")))
        self.storey_choice = QComboBox()
        self.storey_choice.setEditable(True)
        self.storey_choice.setMinimumContentsLength(8)
        self.storey_choice.currentTextChanged.connect(self.on_storey_choice)
        self.section_row.layout().addWidget(self.storey_choice)
        # «← P01»: back to the floor plan «Coupe…» came from (v0.117), shown while the section it opened is open
        self.section_back = QPushButton()
        self.section_back.clicked.connect(self.back_to_section_origin)
        self.section_back.hide()
        self.section_origin = None
        self.section_row.layout().addWidget(self.section_back)
        self.section_row.hide()
        v.addWidget(self.section_row)

        self.canvas = PlanCanvas()
        self.canvas.propose_label = lambda type_: self.propose_label(type_, create=True)
        self.canvas.new_element = self.on_new_element
        self.canvas.unit_word = self.unit
        self.canvas.angle_dragged.connect(self.on_angle_dragged)
        self.canvas.about_to_change.connect(self.push_history)
        self.canvas.changed.connect(self.on_changed)
        self.canvas.selection_changed.connect(self.on_selection)
        self.canvas.pointer.connect(self.on_pointer)
        self.canvas.calibrated.connect(self.on_calibrated)
        self.canvas.tool_done.connect(lambda: self.choose_tool("select"))
        self.canvas.edit_refused.connect(self.on_edit_refused)
        self.canvas.ask_distance = self.ask_aid_distance
        self.canvas.axes_renamed.connect(self.on_axes_renamed)
        self.canvas.floor_of = lambda storey: model.storey_floor(storey, self.other_floors())  # a storey box's and a load level's designation, x1xx (v0.116)
        self.canvas.language = positions_store.project_language(fallback=self.app.lang)  # the words a load level writes on the plan, in the project's language
        if hasattr(self.canvas, "storeyMissing"):
            self.canvas.storeyMissing.connect(lambda _tool: self.hint.setText(self.t("plan_hint_storey_missing")))
        v.addWidget(self.canvas, 1)
        # Everything under the plan keeps its height whatever it says: the plan would otherwise grow and shrink as a message comes and goes, and slide under the pointer while it draws.
        line = self.fontMetrics().height()
        self.pointer_line = plain_label("")
        self.pointer_line.setFont(self.app.mono_font)
        self.pointer_line.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.pointer_line.setFixedHeight(line + 4)
        v.addWidget(self.pointer_line)
        self.hint = self.note("")
        self.hint.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.hint.setFixedHeight(2 * line + 4)
        self.hint.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        v.addWidget(self.hint)
        self.message = QPlainTextEdit()
        self.message.setReadOnly(True)
        self.message.setFrameShape(QPlainTextEdit.Shape.NoFrame)
        self.message.setStyleSheet(f"color: {theme.colour('warning')}; background: transparent;")
        self.message.setFixedHeight(4 * line + 8)
        v.addWidget(self.message)
        return box

    def build_plan_properties(self):
        outer = QWidget()
        ov = QVBoxLayout(outer)
        ov.setContentsMargins(6, 0, 0, 0)
        # the properties in cards on the soft ground, after the website: a column that scrolls up and down only and is never narrower than its cards (cards.py)
        scroll, v = cards.column()
        ov.addWidget(scroll, 1)

        # The right pane follows the selection (v0.116): the selection's card -- its own sizes inside it -- and «Taille des symboles» while something is selected on the plan, the plan's own modules while nothing is (drawing_tab.add_module, update_modules). The selection's card stands first, so that what was clicked is what is read first.
        self.selection_group = cards.card(self.t("plan_group_selection"))
        self.selection_layout = QVBoxLayout(self.selection_group)
        self.add_module(v, self.selection_group, "selection")

        group = cards.card(self.t("plan_group_plan"))
        form = cards.form(group)
        # Nom · Description · ID, the identity of every tab of the window (identity.py), then the storey and the character the numbering reads (v0.114)
        self.identity = identity.IdentityRows(form, self.t, self.on_meta)
        self.name_edit, self.label_edit, self.id_edit = self.identity.name, self.identity.description, self.identity.id
        # the row right under the ID: where the plan's type stands («Type de plan»: a floor plan, an elevation section, a load-path plan) -- inserted there with plan_form.insertRow(plan_type_row, …)
        self.plan_form = form
        self.plan_type_row = form.rowCount()
        # «Type de plan» (v0.116): a floor plan, an elevation section, a load-path plan -- in place of v0.114's «Ce plan est une coupe»
        self.plan_type_combo = QComboBox()
        for kind in model.PLAN_TYPES:
            self.plan_type_combo.addItem(self.t(f"plan_kind_{kind}"), kind)
        self.plan_type_combo.setToolTip(self.t("plan_kind_tip"))
        self.plan_type_combo.currentIndexChanged.connect(self.on_plan_type)
        self.storey_combo = QComboBox()
        self.storey_combo.setEditable(True)
        self.storey_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.storey_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.storey_combo.setMinimumContentsLength(8)
        self.storey_combo.addItems(model.STOREYS.get(self.app.lang, model.STOREYS["en"]))
        self.storey_combo.setToolTip(self.t("plan_storey_tip"))
        self.storey_combo.currentTextChanged.connect(self.on_storey)
        form.addRow(self.t("plan_storey"), self.storey_combo)
        self.floor_edit = QLineEdit()
        self.floor_edit.setMaxLength(1)
        self.floor_edit.setMaximumWidth(40)
        self.floor_edit.setToolTip(self.t("plan_floor_tip"))
        self.floor_edit.textEdited.connect(self.on_floor_typed)
        form.addRow(self.t("plan_floor"), self.floor_edit)
        form.insertRow(self.plan_type_row, self.t("plan_plan_type"), self.plan_type_combo)
        row = QHBoxLayout()
        self.section_button = QPushButton(self.t("plan_section_button"))
        self.section_button.clicked.connect(lambda: self.choose_section())
        self.section_button.setToolTip(self.t("plan_section_choose_ask"))
        self.section_text = self.note("")
        row.addWidget(self.section_button)
        row.addWidget(self.section_text, 1)
        self.section_row_widget = QWidget()  # a row of its own, hidden on a section (apply_plan_type)
        self.section_row_widget.setLayout(row)
        row.setContentsMargins(0, 0, 0, 0)
        form.addRow("", self.section_row_widget)
        self.plan_group = self.add_module(v, group)

        group = cards.card(self.t("plan_group_background"))
        gv = QVBoxLayout(group)
        self.background_text = plain_label("", wrap=True)
        gv.addWidget(self.background_text)
        row = QHBoxLayout()
        self.rotate_left_button = QPushButton("⟲")
        self.rotate_left_button.setToolTip(self.t("plan_doc_rotate_left"))
        self.rotate_left_button.clicked.connect(lambda: self.rotate_current_page(-90))
        self.rotate_right_button = QPushButton("⟳")
        self.rotate_right_button.setToolTip(self.t("plan_doc_rotate_right"))
        self.rotate_right_button.clicked.connect(lambda: self.rotate_current_page(90))
        for button in (self.rotate_left_button, self.rotate_right_button):
            button.setProperty("compact", True)
            row.addWidget(button)
        self.background_import_button = QPushButton(self.t("plan_doc_import"))
        self.background_import_button.clicked.connect(lambda: self.import_document())
        self.remove_background_button = QPushButton(self.t("plan_remove_background"))
        self.remove_background_button.clicked.connect(self.remove_background)
        self.remove_background_button.setToolTip(self.t("plan_no_background"))
        row.addWidget(self.background_import_button)
        row.addWidget(self.remove_background_button)
        row.addStretch(1)
        gv.addLayout(row)
        self.show_outside_box = QCheckBox(self.t("plan_show_outside"))
        self.show_outside_box.setToolTip(self.t("plan_show_outside_tip"))
        self.show_outside_box.toggled.connect(self.on_show_outside)
        gv.addWidget(self.show_outside_box)
        form = cards.form()
        self.opacity = self.slider(0, 100, self.on_opacity)
        form.addRow(self.t("plan_opacity"), self.opacity)
        gv.addLayout(form)
        self.background_group = self.add_module(v, group)

        group = cards.card(self.t("plan_group_crop"))
        gv = QVBoxLayout(group)
        self.crop_text = self.note("")
        gv.addWidget(self.crop_text)
        row = QHBoxLayout()
        # «Dessiner le cadre»: the canvas's crop for one drag, then «Sélection» again (tool_done) -- the one way to it since it left the tool bar (v0.116)
        self.crop_draw_button = QPushButton(self.t("plan_crop_draw"))
        self.crop_draw_button.clicked.connect(lambda: self.choose_tool("crop"))
        self.reset_crop_button = QPushButton(self.t("plan_crop_reset"))
        self.reset_crop_button.clicked.connect(self.reset_crop)
        row.addWidget(self.crop_draw_button)
        row.addWidget(self.reset_crop_button)
        row.addStretch(1)
        gv.addLayout(row)
        self.crop_group = self.add_module(v, group)

        group = cards.card(self.t("plan_group_scale"))
        gv = QVBoxLayout(group)
        self.scale_mode = QComboBox()
        for key in ("plan_scale_none", "plan_scale_ratio", "plan_scale_calibration"):
            self.scale_mode.addItem(self.t(key))
        self.scale_mode.currentIndexChanged.connect(self.on_scale_mode)
        self.scale_mode.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)   # its longest choice does not set the card's width
        self.scale_mode.setMinimumContentsLength(12)
        gv.addWidget(self.scale_mode)
        row = QHBoxLayout()
        row.addWidget(QLabel("1 :"))
        self.ratio_spin = QSpinBox()
        self.ratio_spin.setRange(1, 100000)
        self.ratio_spin.setValue(100)
        self.ratio_spin.valueChanged.connect(self.on_ratio)
        row.addWidget(self.ratio_spin, 1)
        # «Calibrer…»: the canvas's calibration for two clicks, then the length asked (on_calibrated) -- the one way to it since it left the tool bar (v0.116), whatever the scale's mode, which the calibration then sets
        self.calibrate_button = QPushButton(self.t("plan_calibrate"))
        self.calibrate_button.clicked.connect(lambda: self.choose_tool("calibrate"))
        self.calibrate_button.setToolTip(self.t("plan_calibrate_tip"))
        row.addWidget(self.calibrate_button)
        gv.addLayout(row)
        self.scale_text = self.note("")
        gv.addWidget(self.scale_text)
        self.lengths_box = QCheckBox(self.t("plan_show_lengths"))
        self.lengths_box.setToolTip(self.t("plan_lengths_tip"))
        self.lengths_box.toggled.connect(self.on_lengths)
        gv.addWidget(self.lengths_box)
        # the dimensions shown in this view, or not: the engineer's setting, not the plan's -- each view has its own (issue #9, REQ-011: «Affichage» and «Export» say it in their command, `dimensions:`)
        self.dimensions_box = QCheckBox(self.t("plan_show_dimensions"))
        self.dimensions_box.setToolTip(self.t("plan_show_dimensions_tip"))
        self.dimensions_box.setChecked(bool(usersettings.read().get(DRAW_DIMENSIONS, True)))
        self.canvas.show_dimensions = self.dimensions_box.isChecked()
        self.dimensions_box.toggled.connect(self.on_show_dimensions)
        gv.addWidget(self.dimensions_box)
        self.scale_group = self.add_module(v, group)
        self.add_snap_module(v)   # «Magnétisme», in the right pane since v0.117 (drawing_tab.add_snap_module)

        group = cards.card(self.t("plan_group_style"))
        form = cards.form(group)
        self.style_sliders = {}
        for key in model.STYLE_KEYS:
            slider = self.slider(int(model.STYLE_RANGE[0] * 100), int(model.STYLE_RANGE[1] * 100), lambda value, key=key: self.on_style(key, value))
            self.style_sliders[key] = slider
            form.addRow(self.t(f"plan_style_{key}"), slider)
        self.style_group = self.add_module(v, group, "always")
        # ⚑ «Superposition» (another plan shown over this one, v0.116 WP-F) takes its place right here: insert_module(card, after=self.style_group)

        v.addStretch(1)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self.revert_button = QPushButton(self.t("plan_revert"))
        self.revert_button.setToolTip(self.t("plan_revert_tip"))
        self.revert_button.clicked.connect(self.revert)
        self.save_button = QPushButton(self.t("plan_save"))
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(lambda: self.save())
        actions.addWidget(self.revert_button)
        actions.addWidget(self.save_button)
        ov.addLayout(actions)
        return outer

    def unit(self):
        background = self.source.get("background")
        if not background:
            return UNITS[None]
        if Path(background["file"]).suffix.lower() in model.CAD_SUFFIXES:
            return ""  # a drawing's layout: hundredths of a millimetre of its page (calc/domains/cad.py)
        return UNITS.get(model.background_format(background["file"]), "")

    def fill(self):
        """The form from the source -- a plan loaded, restored or undone."""
        self.loading = True
        try:
            self.identity.fill(self.source.get("name", ""), self.source.get("label", ""), self.source.get("id", ""),
                               saved=self.current_id is not None)
            self.floor_edit.setText(self.source.get("floor", ""))
            self.storey_combo.setEditText(self.source.get("storey", "") or "")
            self.plan_type_combo.setCurrentIndex(max(0, self.plan_type_combo.findData(model.plan_type(self.source))))
            section = self.source.get("section_plan")
            self.section_text.setText(self.t("plan_section_text", id=section) if section else self.t("plan_section_none"))
            background = self.source.get("background")
            doc = self.document(background.get("document")) if background and background.get("document") else None
            if background:
                page = int(background.get("page", 1))
                if doc is not None:
                    self.background_text.setText(self.t("plan_background_document", doc=document_text(doc), page=page))
                else:
                    path = model.background_path(project.current().root, background["file"])
                    exists = path is not None and path.is_file()
                    self.background_text.setText(self.t("plan_background_file", file=background["file"], page=page) if exists
                                                 else self.t("plan_background_missing", file=background["file"]))
                self.opacity.slider.setValue(round(100 * float(background.get("opacity", model.DEFAULT_OPACITY))))
            else:
                self.background_text.setText(self.t("plan_no_background"))
                self.opacity.slider.setValue(round(100 * model.DEFAULT_OPACITY))
            self.opacity.setEnabled(bool(background))
            self.remove_background_button.setEnabled(bool(background))
            for button in (self.rotate_left_button, self.rotate_right_button):
                button.setEnabled(doc is not None)
            self.background_import_button.setVisible(doc is None)
            scale = self.source.get("scale")
            self.scale_mode.setCurrentIndex(0 if not scale else (1 if scale.get("mode") == "ratio" else 2))
            if scale and scale.get("mode") == "ratio":
                self.ratio_spin.setValue(int(scale.get("ratio", 100)))
            self.lengths_box.setChecked(bool(self.source.get("show_lengths")))
            for key, box in self.style_sliders.items():
                box.slider.setValue(round(100 * float(self.source.get("style", {}).get(key, 1.0))))
        finally:
            self.loading = False
        self.apply_plan_type()
        self.update_scale_widgets()
        self.update_crop_text()

    def update_scale_widgets(self):
        background = self.source.get("background")
        is_pdf = bool(background) and model.background_format(background["file"]) == "pdf"
        mode = self.scale_mode.currentIndex()
        self.ratio_spin.setEnabled(mode == 1 and is_pdf)
        per_m = model.units_per_m(self.source)
        scale = self.source.get("scale") or {}
        if mode == 1 and not is_pdf:
            self.scale_text.setText(self.t("plan_ratio_pdf_only"))
        elif mode == 2 and scale.get("mode") == "calibration" and per_m:
            self.scale_text.setText(self.t("plan_calibration_text", k=number_text(per_m, 3), length=number_text(scale["length_m"], 3)))
        else:
            self.scale_text.setText("")
        self.lengths_box.setEnabled(bool(per_m))

    def update_crop_text(self):
        crop = model.crop_of(self.source)
        self.crop_text.setText(self.t("plan_crop_text", w=number_text(crop["w"], 1), h=number_text(crop["h"], 1), unit=self.unit()))

    def on_meta(self, _text=None):
        if self.loading:
            return
        name, self.source["label"], self.source["id"] = self.identity.values()
        if name:
            self.source["name"] = name
        else:
            self.source.pop("name", None)
        self.set_floor(self.floor_edit.text().strip())
        self.on_changed()

    def set_floor(self, floor):
        self.source["floor"] = floor

    def on_floor_typed(self, _text):
        """The numbering character typed by the engineer: from now on a storey chosen proposes none (v0.114)."""
        if self.loading:
            return
        self.floor_typed = True
        self.on_meta()

    def other_floors(self):
        """The numbering characters of the project's other plans: what the attic's is proposed above (plan.storey_floor)."""
        return [source.get("floor", "") for pid, source, _group in list_plans() if source and pid != self.current_id]

    def on_storey(self, text):
        """The storey chosen in the list or typed (free text, any length): written into the plan, and the numbering character proposed from it while the engineer has not typed one himself (plan.storey_floor)."""
        if self.loading:
            return
        storey = text.strip()
        if storey:
            self.source["storey"] = storey
        else:
            self.source["storey"] = ""
        if not self.floor_typed:
            proposed = model.storey_floor(storey, self.other_floors())
            if proposed:
                self.loading = True
                self.floor_edit.setText(proposed)
                self.loading = False
                self.set_floor(proposed)
        self.on_changed()

    def on_plan_type(self, _index):
        """«Type de plan» (v0.116): the plan's type and its role with it -- a section's role is section --, and what the new type does not carry taken out in the same step of «Annuler»: a section's storey lines, storey boxes and load levels on any other plan, the load symbols on any plan but a load-path plan. The status line says how many went."""
        if self.loading:
            return
        kind = self.plan_type_combo.currentData()
        dropped = []

        def apply():
            self.source["plan_type"] = kind
            self.source["role"] = "section" if kind == "section" else "plan"
            if kind != "section":
                for key in ("storey_lines", "storey_boxes", "load_levels"):
                    dropped.extend(self.source.pop(key, None) or [])
            if kind != "loadpath":
                loads = [e for e in self.source.get("elements", []) if model.is_load(e.get("type"))]
                if loads:
                    dropped.extend(loads)
                    self.source["elements"] = [e for e in self.source["elements"] if not model.is_load(e.get("type"))]
        self.canvas.select(None)
        self.edit(apply)
        if dropped:
            self.app.set_status(self.t("plan_kind_dropped", n=len(dropped)))
        self.apply_plan_type()

    def tool_shown(self, tool):
        """Whether a tool belongs to the open plan's type: a section's own three on a section alone, the STE tools on a floor plan and a load-path plan, the load tools on a load-path plan alone; the navigation and the axes on every plan."""
        kind = model.plan_type(self.source)
        if tool in SECTION_TOOLS:
            return kind == "section"
        if tool in model.TYPES:
            if model.is_load(tool):
                return kind == "loadpath"
            return kind != "section"
        return True

    def apply_plan_type(self):
        """The tools and the plan's rows of the plan's type (v0.116): a section's own row of tools on a section alone, the load tools on a load-path plan alone, no STE tool on a section; the storey, the numbering character and «Coupe…» on a floor plan and a load-path plan, hidden on a section. A tool the type does not carry, chosen, goes back to «Sélection»."""
        kind = model.plan_type(self.source)
        section = kind == "section"
        self.section_row.setVisible(section)
        for tool, button in self.tool_buttons.items():
            if tool in model.TYPES:
                button.setVisible(self.tool_shown(tool))
        self.section_button.setEnabled(not section)
        for widget in (self.storey_combo, self.floor_edit, self.section_row_widget):
            self.plan_form.setRowVisible(widget, not section)
        if section:
            self.fill_storey_choice()
        if not self.tool_shown(self.canvas.tool):
            self.choose_tool("select")
        elif self.canvas.tool in SUBTYPE_TOOLS:
            self.subtype_combo.setVisible(True)
        else:
            self.subtype_combo.setVisible(False)

    def entry_text(self, pid, source):
        """A plan as the left pane lists it -- «P01 – Hauptgebäude – EG» -- and, for a section or a load-path plan, its type after it, so that it is told from a floor plan at a glance (v0.116)."""
        text = drawing_tab.plan_text(pid, source)
        kind = model.plan_type(source or {})
        return f"{text} · {self.t(f'plan_kind_short_{kind}')}" if kind != "floor" else text

    def storeys_used(self):
        """The storeys of the window's language's list, then those the project's plans name that it does not."""
        names = list(model.STOREYS.get(self.app.lang, model.STOREYS["en"]))
        for _pid, source, _group in list_plans():
            storey = (source or {}).get("storey") or ""
            if storey and storey not in names:
                names.append(storey)
        return names

    def fill_storey_choice(self):
        text = self.storey_choice.currentText()
        self.storey_choice.blockSignals(True)
        self.storey_choice.clear()
        self.storey_choice.addItems(self.storeys_used())
        self.storey_choice.setEditText(text)
        self.storey_choice.blockSignals(False)
        self.canvas.set_storey_choice(text)

    def on_storey_choice(self, text):
        self.canvas.set_storey_choice(text)

    def choose_section(self):
        """«Coupe…»: the section plan this floor plan's storey is marked on, chosen among the project's plans -- the sections first."""
        plans = [(pid, source) for pid, source, _group in list_plans() if source and pid != self.current_id]
        plans.sort(key=lambda pair: pair[1].get("role", "plan") != "section")
        choices = [self.t("plan_section_none")] + [plan_text(pid, source) for pid, source in plans]
        current = self.source.get("section_plan")
        index = next((i + 1 for i, (pid, _s) in enumerate(plans) if pid == current), 0)
        picked = self.ask_choice(self.t("plan_section_choose_title"), self.t("plan_section_choose_ask"), choices, index)
        if picked is None:
            return
        chosen = plans[picked - 1][0] if picked > 0 else None

        def apply():
            if chosen:
                self.source["section_plan"] = chosen
            else:
                self.source.pop("section_plan", None)
        self.edit(apply)
        self.section_text.setText(self.t("plan_section_text", id=chosen) if chosen else self.t("plan_section_none"))
        if chosen:
            self.draw_storey_on(chosen)

    def draw_storey_on(self, section):
        """The section just linked opened, ready for this plan's storey to be drawn on it (the engineer, 07.10.2026: «ouvre le plan sélectionné dans le menu déroulant et permet de dessiner la ligne d'étage ou le rectangle d'étage directement avec le bon étage écrit»): the storey chosen is this plan's, the tool the storey line -- or the storey box, the line drawn already --, or, both drawn, the line selected. The plan left is saved as any plan left is (autosave.py); «← P01» in the section's row brings it back."""
        origin, storey = self.current_id, str(self.source.get("storey") or "").strip()
        self.open_plan(section)
        if self.current_id != section:
            return   # the plan could not be left (a save refused): nothing opened
        self.section_origin = origin
        self.section_back.setText(self.t("plan_section_back", id=origin))
        self.section_back.setToolTip(self.t("plan_section_back_tip", id=origin))
        self.section_back.show()
        if storey:
            self.storey_choice.setCurrentText(storey)
        same = lambda other: model.storey_index(other) == model.storey_index(storey) if model.storey_index(storey) is not None else str(other).strip().casefold() == storey.casefold()
        lines = [i for i, line in enumerate(self.source.get("storey_lines", [])) if same(line.get("storey", ""))]
        boxes = [i for i, box in enumerate(self.source.get("storey_boxes", [])) if same(box.get("storey", ""))]
        if lines and boxes:
            self.choose_tool("select")
            self.canvas.select(("storey-line", lines[0]))
            self.app.set_status(self.t("plan_section_found", section=section, storey=storey, plan=origin))
        else:
            self.choose_tool("storey-box" if lines else "storey-line")
            self.app.set_status(self.t("plan_section_opened", section=section, storey=storey or "?", plan=origin))

    def back_to_section_origin(self):
        origin, self.section_origin = self.section_origin, None
        self.section_back.hide()
        if origin:
            self.open_plan(origin)

    def on_show_dimensions(self, checked):
        """The view «Dessin» shows the plan's dimensions or not -- kept in the engineer's settings, nothing written into the plan."""
        settings = usersettings.read()
        settings[DRAW_DIMENSIONS] = bool(checked)
        usersettings.write(settings)
        self.canvas.show_dimensions = bool(checked)
        self.canvas.redraw()

    def on_lengths(self, checked):
        self.edit(lambda: self.source.__setitem__("show_lengths", bool(checked)))

    def on_scale_mode(self, index):
        if self.loading:
            return

        def apply():
            if index == 0:
                self.source.pop("scale", None)
            elif index == 1:
                self.source["scale"] = {"mode": "ratio", "ratio": self.ratio_spin.value()}
            else:
                scale = self.source.get("scale") or {}
                if scale.get("mode") != "calibration":
                    self.source.pop("scale", None)  # until the two points are clicked
        self.edit(apply)
        self.update_scale_widgets()
        if index == 2 and not (self.source.get("scale") or {}).get("mode") == "calibration":
            self.choose_tool("calibrate")

    def on_ratio(self, value):
        if self.scale_mode.currentIndex() == 1:
            self.edit(lambda: self.source.__setitem__("scale", {"mode": "ratio", "ratio": value}))
            self.update_scale_widgets()

    def on_calibrated(self, points):
        length = self.ask_length()
        if length is None:
            return
        self.edit(lambda: self.source.__setitem__("scale", {"mode": "calibration", "points": [[round(x, 2), round(y, 2)] for x, y in points], "length_m": length}))
        self.loading = True
        self.scale_mode.setCurrentIndex(2)
        self.loading = False
        self.update_scale_widgets()

    def remove_background(self):
        def apply():
            self.source.pop("background", None)
            if (self.source.get("scale") or {}).get("mode") == "ratio":
                self.source.pop("scale", None)
        self.edit(apply)
        self.canvas.load_background()
        self.canvas.invalidate()
        self.fill()
