"""FireTab's building -- the tree of its entries, its combos, the centre of the drawing view and the cards of its right pane -- a mixin of methods moved verbatim out of calc/tools/fire_tab.py (issue #30). FireTab names it among its bases.
"""

from PySide6.QtCore import QItemSelectionModel, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPlainTextEdit, QPushButton,
    QSizePolicy, QSpinBox, QTabWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)
import cards  # the properties in cards, after the website (cards.py)
import identity
import plan_canvas_edit  # Ctrl+C's and Ctrl+V's states (issue #61)
import stylefactors  # the entries' own size factors, shown as an overridden b/h is (stylefactors.py)
import theme  # the colours this tab states itself (theme.py)
from drawing_tab import DrawingTab, number_text, plain_label
from domains import fire
from fire_canvas import FireCanvas
from flowbar import FlowLayout, FlowWidget, tool_group
from i18n import strings  # the German name of a fire resistance or of a kind of surface, in the window's language
from norms import vkf  # the fire resistances, the escape routes and the doors of the VKF sheet of symbols, and their colours


# The tools, in the order of the bar, and the key of each one's name and of its hint. The calibration acts on the plan's own frame, which a plan that follows a position plan has none of; the crop acts on it too, and on the crop such a plan may state for itself. Neither is a tool of the bar since v0.116 (PANE_TOOLS): «Dessiner le cadre» in «Cadrage» and «Calibrer…» in «Échelle» start them, as in the position plan's tab.
TOOLS = ("select", "pan", "ruler", "move", "copy", "polygon", "wall", "door", "route", "exit", "width", "text")   # «Déplacer» and «Copier» since issue #18 (plan_canvas_edit.py, the position plan's own); «Texte» since issue #43, the four drawing engines' one


NAMES = {"select": "plan_tool_select", "pan": "plan_tool_pan", "ruler": "plan_tool_ruler", "move": "plan_tool_move", "copy": "plan_tool_copy", "polygon": "fp_tool_polygon", "wall": "fp_tool_wall", "door": "fp_tool_door",
         "route": "fp_tool_route", "exit": "fp_tool_exit", "width": "fp_tool_width", "text": "plan_tool_text", "crop": "plan_tool_crop", "calibrate": "plan_tool_calibrate"}


HINTS = {"select": "fp_hint_select", "pan": "fp_hint_pan", "ruler": "plan_hint_ruler", "move": "plan_hint_move", "copy": "plan_hint_copy", "polygon": "fp_hint_polygon", "wall": "fp_hint_wall", "door": "fp_hint_door",
         "route": "fp_hint_route", "exit": "fp_hint_exit", "width": "fp_hint_width", "crop": "plan_hint_crop", "calibrate": "plan_hint_calibrate", "text": "plan_tip_text",
         plan_canvas_edit.CLIP_BASE: "plan_hint_clip_base", plan_canvas_edit.PASTE: "plan_hint_paste"}   # Ctrl+C's base point and Ctrl+V's paste, no button of their own (issue #61)


# What the next entry of each tool is drawn as until the engineer chooses another (the canvas's own defaults are the same).
DEFAULT_WALL_CLASS = "EI 30"


DEFAULT_SURFACE_KIND = "horizontal"


DEFAULT_DOOR_KIND = "swing"


DEFAULT_DOOR_CLASS = "EI 30"


class FireTabBuildMixin:
    """Methods of fire_tab.FireTab, moved verbatim (issue #30): the class names this mixin among its bases."""

    def entry_tree(self, headers):
        """A list of one kind of entry: one row each, the entry's id kept in the first column's user data."""
        tree = QTreeWidget()
        tree.setColumnCount(len(headers))
        tree.setHeaderLabels([self.t(key) for key in headers])
        tree.setRootIsDecorated(False)
        tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        tree.itemSelectionChanged.connect(lambda tree=tree: self.on_rows(tree))
        return tree

    def swatch(self, rgb):
        """A small square in a fire resistance's own colour, as the sheet of symbols draws its band."""
        key = tuple(rgb)
        if key not in self.class_icons:
            pixmap = QPixmap(14, 14)
            pixmap.fill(QColor(*key))
            painter = QPainter(pixmap)
            painter.setPen(QColor(theme.colour("muted")))
            painter.drawRect(0, 0, 13, 13)
            painter.end()
            self.class_icons[key] = QIcon(pixmap)
        return self.class_icons[key]

    def fit_combo(self, combo, characters=12):
        """A combo whose longest choice does not set the width of the bar or the card it stands in."""
        combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        combo.setMinimumContentsLength(characters)
        return combo

    def make_class_combo(self):
        """The fire resistances of the VKF sheet, in the sheet's order: the text is the class's name in the window's language, the data its key, the icon its colour."""
        combo = QComboBox()
        for row in vkf.resistances():
            combo.addItem(self.swatch(row["rgb"]), strings.translate(row["label"], self.app.lang), row["key"])
        return self.fit_combo(combo)

    def make_surface_combo(self):
        """The three kinds of surface the sheet draws, in `fire.SURFACES`' order."""
        combo = QComboBox()
        for kind in fire.SURFACES:
            entry = vkf.escape(kind)
            combo.addItem(self.swatch(entry["rgb"]), strings.term(entry["label"], self.app.lang), kind)
        return self.fit_combo(combo, 16)

    def make_door_kind_combo(self):
        """How a door opens: a leaf turning on a hinge, or sliding along the wall."""
        combo = QComboBox()
        for kind in fire.DOOR_KINDS:
            combo.addItem(self.t(f"fp_door_{kind}"), kind)
        combo.setToolTip(self.t("fp_door_kind_tip"))
        return self.fit_combo(combo, 10)

    def make_door_class_combo(self):
        """The fire resistances the sheet gives a door, with a last choice for a door without one -- an empty string, which a door states by having no `class` at all."""
        combo = QComboBox()
        for cls in vkf.door_classes():
            entry = vkf.door("swing", cls)
            combo.addItem(self.swatch(entry["rgb"]), cls, cls)
            combo.setItemData(combo.count() - 1, strings.term(entry["label"], self.app.lang), Qt.ItemDataRole.ToolTipRole)
        combo.addItem(self.swatch((255, 255, 255)), self.t("fp_door_plain"), "")
        combo.setToolTip(self.t("fp_door_class_tip"))
        return self.fit_combo(combo, 10)

    def build_fire_center(self):
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(6, 0, 6, 0)
        # two rows that wrap, as the position plan's bar is (flowbar.py): the tools, then what acts on the plan
        self.tool_rows = []
        for _ in range(2):
            holder = FlowWidget()
            FlowLayout(holder, spacing=2)
            self.tool_rows.append(holder)
            v.addWidget(holder)
        top, actions = (holder.layout() for holder in self.tool_rows)
        self.tool_group = QButtonGroup(self)
        self.tool_group.setExclusive(True)
        self.tool_buttons = {}
        for tool in TOOLS:
            button = self.tool_button(self.t(NAMES[tool]), tip=self.t(HINTS[tool]))
            button.clicked.connect(lambda _checked=False, tool=tool: self.choose_tool(tool))
            self.tool_group.addButton(button)
            self.tool_buttons[tool] = button
        self.surface_combo = self.make_surface_combo()
        self.surface_combo.setToolTip(self.t("fp_surface_kind_tip"))
        self.wall_combo = self.make_class_combo()
        self.wall_combo.setToolTip(self.t("fp_wall_class_tip"))
        self.door_kind_combo = self.make_door_kind_combo()
        self.door_class_combo = self.make_door_class_combo()
        buttons = self.tool_buttons
        for widget in (buttons["select"], buttons["pan"], buttons["move"], buttons["copy"]):
            top.addWidget(widget)
        top.addWidget(tool_group([buttons["polygon"], self.surface_combo], self.t("fp_zones")))
        top.addWidget(tool_group([buttons["wall"], self.wall_combo], self.t("fp_walls")))
        top.addWidget(tool_group([buttons["door"], self.door_kind_combo, self.door_class_combo], self.t("fp_doors")))
        top.addWidget(tool_group([buttons["route"], buttons["exit"], buttons["width"]], self.t("fp_group_escape")))
        self.delete_button = self.tool_button(self.t("fp_delete_selection"), checkable=False)
        self.delete_button.clicked.connect(lambda: self.canvas.delete_selection())
        actions.addWidget(self.delete_button)
        for key, slot in (("plan_undo", self.undo), ("plan_redo", self.redo), ("plan_fit", lambda: self.canvas.fit())):
            button = self.tool_button(self.t(key), checkable=False)
            button.clicked.connect(slot)
            actions.addWidget(button)

        self.canvas = FireCanvas()
        self.canvas.lang = self.app.lang   # the legend is written in the window's language
        self.canvas.about_to_change.connect(self.push_history)
        self.canvas.changed.connect(self.on_changed)
        self.canvas.selection_changed.connect(self.on_selection)
        self.canvas.pointer.connect(self.on_pointer)
        self.canvas.unit_word = self.unit   # a ruler on a plan with no scale says its sheet's unit (issue #9)
        self.canvas.calibrated.connect(self.on_calibrated)
        self.canvas.tool_done.connect(lambda: self.choose_tool("select"))
        self.canvas.edit_refused.connect(lambda _tool: self.hint.setText(self.t("plan_edit_nothing")))
        # the combos are connected once the canvas exists: filling one would otherwise tell it a choice made before it could hear
        for combo, default, attribute, slot in (
                (self.surface_combo, DEFAULT_SURFACE_KIND, "zone_kind", self.on_surface_tool_kind),
                (self.wall_combo, DEFAULT_WALL_CLASS, "wall_class", self.on_wall_tool_class),
                (self.door_kind_combo, DEFAULT_DOOR_KIND, "door_kind", self.on_door_tool_kind),
                (self.door_class_combo, DEFAULT_DOOR_CLASS, "door_class", self.on_door_tool_class)):
            combo.setCurrentIndex(max(combo.findData(default), 0))
            setattr(self.canvas, attribute, combo.currentData() or None)
            combo.currentIndexChanged.connect(slot)
        v.addWidget(self.canvas, 1)
        # Everything under the plan keeps its height whatever it says: the plan would otherwise grow and shrink as a message comes and goes.
        line = self.fontMetrics().height()
        self.pointer_line = plain_label("")
        self.pointer_line.setFont(self.app.mono_font)
        self.pointer_line.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.pointer_line.setFixedHeight(line + 4)
        v.addWidget(self.pointer_line)
        self.hint = self.note("")
        self.hint.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.hint.setFixedHeight(3 * line + 4)
        self.hint.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        v.addWidget(self.hint)
        self.message = QPlainTextEdit()
        self.message.setReadOnly(True)
        self.message.setFrameShape(QPlainTextEdit.Shape.NoFrame)
        self.message.setStyleSheet(f"color: {theme.colour('warning')}; background: transparent;")
        self.message.setFixedHeight(3 * line + 8)
        v.addWidget(self.message)
        return box

    def own(self, widget):
        """Registers a control of the plan's own frame: it is greyed, and says why, while the plan follows a position plan's."""
        self.own_widgets.append((widget, widget.toolTip()))
        return widget

    def build_fire_properties(self):
        outer = QWidget()
        ov = QVBoxLayout(outer)
        ov.setContentsMargins(6, 0, 0, 0)
        scroll, v = cards.column()
        ov.addWidget(scroll, 1)

        # The right pane follows the selection (v0.116), as the position plan's does: the selection's card -- its own sizes and opacity inside it -- and «Taille des symboles» while something is selected, the plan's own modules while nothing is (drawing_tab.add_module, update_modules).
        self.add_module(v, self.build_selection_card(), "selection")

        group = cards.card(self.t("plan_group_plan"))
        form = cards.form(group)
        # Nom · Description · ID, the identity of every tab of the window (identity.py)
        self.identity = identity.IdentityRows(form, self.t, self.on_meta)
        self.name_edit, self.label_edit, self.id_edit = self.identity.name, self.identity.description, self.identity.id
        self.plan_form = form
        self.plan_group = self.add_module(v, group)

        # «Fond de plan»: what the plan follows -- a position plan, or its own frame on a page of a document --, the page turned, and what is shown of it
        group = cards.card(self.t("fp_group_frame"))
        gv = QVBoxLayout(group)
        self.follow_combo = QComboBox()
        self.follow_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.follow_combo.setMinimumContentsLength(12)
        self.follow_combo.currentIndexChanged.connect(self.on_follow)
        gv.addWidget(self.follow_combo)
        self.follow_note = self.note(self.t("fp_follow_note"))
        gv.addWidget(self.follow_note)
        self.follow_info = plain_label("", wrap=True)
        gv.addWidget(self.follow_info)
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
        row.addWidget(self.background_import_button)
        row.addStretch(1)
        gv.addLayout(row)
        self.show_outside_box = QCheckBox(self.t("plan_show_outside"))
        self.show_outside_box.setToolTip(self.t("plan_show_outside_tip"))
        self.show_outside_box.toggled.connect(self.on_show_outside)
        gv.addWidget(self.show_outside_box)
        form = cards.form()
        self.opacity = self.own(self.slider(0, 100, self.on_opacity))
        form.addRow(self.t("plan_opacity"), self.opacity)
        gv.addLayout(form)
        self.background_group = self.add_module(v, group)

        group = cards.card(self.t("plan_group_scale"))
        gv = QVBoxLayout(group)
        self.scale_mode = self.own(QComboBox())
        for key in ("plan_scale_none", "plan_scale_ratio", "plan_scale_calibration"):
            self.scale_mode.addItem(self.t(key))
        self.scale_mode.currentIndexChanged.connect(self.on_scale_mode)
        self.scale_mode.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.scale_mode.setMinimumContentsLength(12)
        gv.addWidget(self.scale_mode)
        row = QHBoxLayout()
        row.addWidget(QLabel("1 :"))
        self.ratio_spin = QSpinBox()
        self.ratio_spin.setRange(1, 100000)
        self.ratio_spin.setValue(100)
        self.ratio_spin.valueChanged.connect(self.on_ratio)
        row.addWidget(self.ratio_spin, 1)
        # «Calibrer…»: the canvas's calibration for two clicks, then the length asked -- the one way to it since it left the tool bar (v0.116); greyed, and saying why, while the plan follows a position plan's scale
        self.calibrate_button = QPushButton(self.t("plan_calibrate"))
        self.calibrate_button.clicked.connect(lambda: self.choose_tool("calibrate"))
        self.calibrate_button.setToolTip(self.t("plan_calibrate_tip"))  # a disabled element says why (v0.47's rule)
        row.addWidget(self.calibrate_button)
        gv.addLayout(row)
        self.scale_text = self.note("")
        gv.addWidget(self.scale_text)
        self.scale_group = group

        # «Taille des symboles»: the plan's own two factors, for its strokes and for its texts -- the position plan's sliders, without the one for the symbols placed on a point, which nothing here draws
        group = cards.card(self.t("plan_group_style"))
        form = cards.form(group)
        self.style_sliders = {}
        for key in fire.STYLE_KEYS:
            box = self.slider(int(fire.STYLE_RANGE[0] * 100), int(fire.STYLE_RANGE[1] * 100), lambda value, key=key: self.on_style(key, value))
            self.style_sliders[key] = box.slider
            form.addRow(self.t(f"plan_style_{key}"), box)
        self.style_group = group

        # «Cadrage»: a plan with a frame of its own draws it or takes the whole sheet back; one that follows a position plan shows that plan's crop until it states one of its own, and takes the position plan's again with «Reprendre»
        self.crop_group = cards.card(self.t("plan_group_crop"))
        gv = QVBoxLayout(self.crop_group)
        self.crop_text = self.note("")
        gv.addWidget(self.crop_text)
        self.crop_state = self.note("")
        gv.addWidget(self.crop_state)
        row = QHBoxLayout()
        self.crop_draw_button = QPushButton(self.t("plan_crop_draw"))
        self.crop_draw_button.clicked.connect(lambda: self.choose_tool("crop"))
        self.reset_crop_button = QPushButton(self.t("plan_crop_reset"))
        self.reset_crop_button.clicked.connect(self.reset_crop)
        self.crop_take_back_button = QPushButton(self.t("plan_style_take_back"))
        self.crop_take_back_button.clicked.connect(self.take_back_crop)
        for button in (self.crop_draw_button, self.reset_crop_button, self.crop_take_back_button):
            row.addWidget(button)
        row.addStretch(1)
        gv.addLayout(row)
        # «Cadrage» above «Échelle», then «Taille des symboles» (v0.116, the engineer's order)
        self.add_module(v, self.crop_group)
        self.add_module(v, self.scale_group)
        self.add_snap_module(v)   # «Magnétisme», as in the position plan (drawing_tab.add_snap_module, v0.117)
        self.add_module(v, self.style_group, "always")
        # ⚑ «Superposition» (another plan shown over this one, v0.116 WP-F) takes its place right here: insert_module(card, after=self.style_group)

        # the legend: a box listing what the plan draws, placed on the plan -- on or off here, dragged on the plan with the selection tool, and of a size of its own
        group = cards.card(self.t("fp_group_legend"))
        gv = QVBoxLayout(group)
        self.legend_check = QCheckBox(self.t("fp_legend_show"))
        self.legend_check.toggled.connect(self.on_legend)
        gv.addWidget(self.legend_check)
        form = cards.form()
        box, self.legend_slider, _readout = stylefactors.percent(*fire.LEGEND_SCALE_RANGE)
        self.legend_slider.valueChanged.connect(self.on_legend_size)
        self.legend_slider.sliderPressed.connect(self.on_slider_pressed)
        self.legend_slider.sliderReleased.connect(self.on_slider_released)
        self.legend_size = box
        form.addRow(self.t("fp_legend_size"), box)
        gv.addLayout(form)
        gv.addWidget(self.note(self.t("fp_legend_note")))
        self.legend_group = self.add_module(v, group)
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

    def build_selection_card(self):
        self.selection_group = cards.card(self.t("fp_group_selection"))
        sv = QVBoxLayout(self.selection_group)
        self.nothing_label = self.note(self.t("fp_nothing_selected"))
        sv.addWidget(self.nothing_label)
        # surfaces, one or several and nothing else: their kind, changed for all of them at once
        self.zone_box = QWidget()
        form = cards.form(self.zone_box)
        form.setContentsMargins(0, 0, 0, 0)
        self.zone_kind_combo = self.make_surface_combo()
        self.zone_kind_combo.currentIndexChanged.connect(self.on_zone_kind)
        form.addRow(self.t("fp_col_kind"), self.zone_kind_combo)
        sv.addWidget(self.zone_box)
        # one surface: its name and its area
        self.single_box = QWidget()
        form = cards.form(self.single_box)
        form.setContentsMargins(0, 0, 0, 0)
        self.zone_label = QLineEdit()
        self.zone_label.textEdited.connect(self.on_zone_label)
        self.zone_label.editingFinished.connect(self.on_zone_label_done)
        form.addRow(self.t("fp_zone_name"), self.zone_label)
        self.area_label = plain_label("")
        form.addRow(self.t("fp_zone_area"), self.area_label)
        sv.addWidget(self.single_box)
        # walls: their fire resistance, changed for all of them at once, and their length
        self.wall_box = QWidget()
        form = cards.form(self.wall_box)
        form.setContentsMargins(0, 0, 0, 0)
        self.class_combo = self.make_class_combo()
        self.class_combo.currentIndexChanged.connect(self.on_wall_class)
        form.addRow(self.t("fp_wall_class"), self.class_combo)
        self.wall_length_label = plain_label("", wrap=True)
        form.addRow(self.t("fp_length"), self.wall_length_label)
        sv.addWidget(self.wall_box)
        # doors: the way they open and their fire resistance, changed for all of them at once, the width, and the two flips
        self.door_box = QWidget()
        column = QVBoxLayout(self.door_box)
        column.setContentsMargins(0, 0, 0, 0)
        holder = QWidget()
        form = cards.form(holder)
        form.setContentsMargins(0, 0, 0, 0)
        self.door_kind_card_combo = self.make_door_kind_combo()
        self.door_kind_card_combo.currentIndexChanged.connect(self.on_door_kind)
        form.addRow(self.t("fp_col_kind"), self.door_kind_card_combo)
        self.door_class_card_combo = self.make_door_class_combo()
        self.door_class_card_combo.currentIndexChanged.connect(self.on_door_class)
        form.addRow(self.t("fp_wall_class"), self.door_class_card_combo)
        self.door_width_label = plain_label("", wrap=True)
        form.addRow(self.t("fp_width"), self.door_width_label)
        column.addWidget(holder)
        self.flip_hinge_button = QPushButton(self.t("fp_flip_hinge"))
        self.flip_hinge_button.setToolTip(self.t("fp_flip_hinge_tip"))
        self.flip_hinge_button.clicked.connect(lambda: self.flip_doors("hinge"))
        self.flip_side_button = QPushButton(self.t("fp_flip_side"))
        self.flip_side_button.setToolTip(self.t("fp_flip_side_tip"))
        self.flip_side_button.clicked.connect(lambda: self.flip_doors("side"))
        column.addWidget(self.flip_hinge_button)
        column.addWidget(self.flip_side_button)
        sv.addWidget(self.door_box)
        # one escape route's length: measured, and the text written along it instead
        self.route_box = QWidget()
        form = cards.form(self.route_box)
        form.setContentsMargins(0, 0, 0, 0)
        self.route_length_label = plain_label("")
        form.addRow(self.t("fp_length"), self.route_length_label)
        self.route_text_edit = QLineEdit()
        self.route_text_edit.textEdited.connect(self.on_route_text)
        self.route_text_edit.editingFinished.connect(self.on_zone_label_done)
        form.addRow(self.t("fp_col_text"), self.route_text_edit)
        sv.addWidget(self.route_box)
        # one escape route's width: measured, and the text written on it instead
        self.width_box = QWidget()
        form = cards.form(self.width_box)
        form.setContentsMargins(0, 0, 0, 0)
        self.width_label = plain_label("")
        form.addRow(self.t("fp_width"), self.width_label)
        self.width_text_edit = QLineEdit()
        self.width_text_edit.textEdited.connect(self.on_width_text)
        self.width_text_edit.editingFinished.connect(self.on_zone_label_done)
        form.addRow(self.t("fp_col_text"), self.width_text_edit)
        sv.addWidget(self.width_box)
        # one text placed with the Text tool (issue #43): text_pane's, built for the text selected
        self.text_holder = QWidget()
        self.text_layout = QVBoxLayout(self.text_holder)
        self.text_layout.setContentsMargins(0, 0, 0, 0)
        self.text_pane = None
        sv.addWidget(self.text_holder)
        self.several_label = plain_label("", wrap=True)
        sv.addWidget(self.several_label)
        sv.addWidget(self.build_own_card())
        row = QHBoxLayout()
        self.delete_selection_button = QPushButton(self.t("fp_delete_selection"))
        self.delete_selection_button.clicked.connect(lambda: self.canvas.delete_selection())
        row.addWidget(self.delete_selection_button)
        row.addStretch(1)
        sv.addLayout(row)
        return self.selection_group

    def build_own_card(self):
        """The size and the opacity the selection is drawn at, and where its text stands: a card inside the selection's card, as the position plan's «Taille propre» is -- built once and put in step with the selection at every change (refresh_own). «Taille propre» is `stylefactors.EntryRows`: one row per factor EVERY entry selected may state, at 100 % while none states it and orange with «Reprendre» once any does; the opacity is a row of its own, which is not a factor."""
        self.own_card = cards.card(self.t("fp_group_own"))
        ov = QVBoxLayout(self.own_card)
        ov.addWidget(self.note(self.t("fp_style_own_note")))
        form = cards.form()
        ov.addLayout(form)
        self.entry_style = stylefactors.EntryRows(form, self.t, "plan", self.set_entry_style, self.take_back_entry_style,
                                                  pressed=self.on_slider_pressed, released=self.on_slider_released)
        box, slider, readout = stylefactors.percent(*fire.OPACITY_RANGE)
        back = QPushButton(self.t("plan_style_take_back"))
        box.layout().addWidget(back)
        name = QLabel(self.t("fp_opacity"))
        form.addRow(name, box)
        slider.valueChanged.connect(self.on_entry_opacity)
        slider.sliderPressed.connect(self.on_slider_pressed)
        slider.sliderReleased.connect(self.on_slider_released)
        back.clicked.connect(self.take_back_opacity)
        self.entry_opacity = {"name": name, "field": box, "slider": slider, "readout": readout, "back": back}
        self.text_place = QWidget()
        tv = QVBoxLayout(self.text_place)
        tv.setContentsMargins(0, 0, 0, 0)
        tv.addWidget(QLabel(self.t("fp_text_where")))
        self.text_home = self.note(self.t("fp_text_home"))
        tv.addWidget(self.text_home)
        row = QHBoxLayout()
        self.text_reset_button = QPushButton(self.t("fp_text_reset"))
        self.text_reset_button.clicked.connect(self.reset_text)
        row.addWidget(self.text_reset_button)
        row.addStretch(1)
        tv.addLayout(row)
        ov.addWidget(self.text_place)
        self.own_card.setVisible(False)
        return self.own_card
