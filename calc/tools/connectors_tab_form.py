"""ConnectorsTab's form -- the type bar and the fields, the shape of a row and its read-only cells, the pattern and the section drawn, the material and the dowel boxes, the figures, results and calls on the right -- a mixin of methods moved verbatim out of calc/tools/connectors_tab.py (issue #30). ConnectorsTab names it among its bases.
"""

from PySide6.QtCore import QByteArray, QEvent, Qt, QTimer
from PySide6.QtGui import QCursor, QIcon, QKeySequence, QShortcut
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QAbstractItemView, QAbstractSpinBox, QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QSizePolicy, QSpinBox, QSplitter, QTableWidget, QTableWidgetItem, QToolButton,
    QVBoxLayout, QWidget,
)
import identity
import traceback
import project  # where the project this tab works on is (calc/project.py)
import theme  # the colours this tab states itself: the orange of a value written over, a lit result (theme.py, v0.90)
import cards  # the form and what is read off it in cards, after the website (cards.py)
import linkable_spin  # the button beside a number that may follow a variable (spec 2026-10-11-variables-liees-champs-et-textes)
from shiboken6 import isValid
from domains import connector, connector_svg, dowel, links
from i18n import strings
from norms import sia263, sia265, sn_en_14592
import svg_icons


ICON_PX = 30


TOOL_HEIGHT = 62


TOOL_MIN_WIDTH = 92


# One row of the form is `sentence | symbol [entry] unit`. The three widths keep the symbols and the
# units in columns of their own, so that a form read down the page lines up rather than wandering.
SYMBOL_WIDTH = 42


UNIT_WIDTH = 52


LABEL_WIDTH = 250


# Inside a member column the same sentence stands twice, so it is given a narrower measure.
COLUMN_LABEL_WIDTH = 170


# The bar of kinds, in the order the engineer named them. `None` for a kind with no calculation module:
# the button is there and disabled, so that what is not implemented is visible rather than absent.
TOOL_TYPES = (
    ("Nagel", "cn_type_nail", "Nagel"),
    ("Stabdübel", "cn_type_dowel", "Stabdübel"),
    ("Vollgewindeschraube", "cn_type_screw", "Vollgewindeschraube"),
    ("Bolzen", "cn_type_bolt", "Bolzen"),
    ("Dübel besonderer Bauart", "cn_type_ring", "Dübel besonderer Bauart"),
    ("Blatt", "cn_type_lap", "Blatt"),
    ("Versatz", "cn_type_notch", "Versatz"),
    ("Schwalbenschwanz", "cn_type_dovetail", "Schwalbenschwanz"),
)


def svg_icon(kind, size=ICON_PX, ink=None, ground=None):
    """One kind's swatch as an icon, in the palette's ink so that it reads on a dark theme too (svg_icons.recolour)."""
    try:
        svg = connector_svg.swatch(kind)
    except KeyError:
        return QIcon()
    return svg_icons.svg_icon(svg_icons.recolour(svg, connector_svg.SWATCH_INK, connector_svg.SWATCH_FILL, ink, ground), size)


def _n(value):
    text = "%.3f" % value
    return text.rstrip("0").rstrip(".") if "." in text else text


class ConnectorsFormMixin:
    """Methods of connectors_tab.ConnectorsTab, moved verbatim (issue #30): the class names this mixin among its bases."""

    def build_form(self):
        panel = QWidget()
        column = QVBoxLayout(panel)
        column.setContentsMargins(0, 0, 0, 0)

        self.type_box = cards.card(self.t("cn_types"))
        bar = QHBoxLayout(self.type_box)
        bar.setContentsMargins(6, 4, 6, 4)
        ink = self.palette().windowText().color().name()
        ground = self.palette().base().color().name()
        self.type_buttons = {}
        for kind, key, swatch_key in TOOL_TYPES:
            button = QToolButton()
            button.setText(self.t(key))
            button.setIcon(svg_icon(swatch_key, ICON_PX, ink, ground))
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            button.setCheckable(True)
            button.setMinimumHeight(TOOL_HEIGHT)
            button.setMinimumWidth(TOOL_MIN_WIDTH)
            if kind in connector.MODULES:
                button.clicked.connect(lambda _c, k=kind: self.choose_type(k))
            else:
                button.setEnabled(False)
                button.setToolTip(self.t("cn_not_yet", type=self.t(key)))
            self.type_buttons[kind] = button
            bar.addWidget(button)
        bar.addStretch(1)
        column.addWidget(self.type_box)

        self.expand_button = QPushButton(self.t("cn_expand"))
        self.expand_button.clicked.connect(self.expand_types)
        self.expand_button.setVisible(False)
        column.addWidget(self.expand_button)

        # the boxes in cards on the soft ground, after the website: a column that scrolls up and down only and is never narrower than its cards (cards.py)
        scroll, self.form = cards.column()
        column.addWidget(scroll, 1)

        self.build_fields()
        return panel

    def _spin(self, minimum, maximum, decimals=1, step=1.0):
        box = QDoubleSpinBox()
        box.setRange(minimum, maximum)
        box.setDecimals(decimals)
        box.setSingleStep(step)
        box.valueChanged.connect(self.touch)
        return box

    def build_fields(self):
        """The form, in the boxes the engineer listed and in the classeur's own order.

        Identité · Assemblage · Géométrie et matériau · Stabdübel · Disposition des broches · Conditions.
        The middle two are rebuilt whenever the assembly changes, because what they hold depends on it: a
        Holz-Holz joint enters two timber members side by side, a Stahl-Holz joint one member and its plates.
        """
        self.computed = {}          # name -> the read-only QLabel a calculated cell is written into
        self.box_results = {}       # a QGroupBox -> the result names it produces, for the hover
        self.member_boxes = {}      # a «Pièce» QGroupBox -> the index of the member it is
        self.hover_element = ""     # the element of the member whose box the pointer is in
        self.hover_member = None    # and its 1-based index, which the section rings its piece(s) by
        self.hot_box = None

        # --- Identité: Schéma · Nom · Description · ID, in that order and nothing else (the engineer's list).
        # The folder is set by dragging the connector in the left pane; the variant, the separate
        # designation, the members joined and the length went with it -- none of them enters the
        # calculation. The members joined are read off the schema instead (draft), so the report's
        # descriptive line «(Bauteile: T001, S001)» stays true without being typed.
        identity_box = cards.card(self.t("cn_identity"))
        form = QFormLayout(identity_box)
        # The detail this connector is drawn on, FIRST: it says which joint this is, and the elements and
        # the markers below are read off it (docs/domain/detail-schemas.md §3.3decies).
        self.schema_box = QComboBox()
        self.schema_box.currentIndexChanged.connect(self.on_schema)
        form.addRow(self.app.label("cn_schema"), self.schema_box)
        self.schema_note = QLabel("")
        self.schema_note.setWordWrap(True)
        self.schema_note.setStyleSheet("color: %s;" % self.app.muted)
        form.addRow("", self.schema_note)
        self.identity = identity.IdentityRows(form, self.t, self.touch)
        self.name_edit, self.description_edit, self.id_edit = (
            self.identity.name, self.identity.description, self.identity.id)
        self.form.addWidget(identity_box)

        # --- Assemblage: the one choice, and nothing else. It commands everything below it.
        self.assembly_group = cards.card(self.t("cn_box_assembly"))
        form = QFormLayout(self.assembly_group)
        self.assembly_box = QComboBox()
        for name in dowel.ASSEMBLIES:
            self.assembly_box.addItem(self.tl(name), name)
        for name, reason in dowel.UNCOVERED_ASSEMBLIES.items():
            self.assembly_box.addItem(self.tl(name), name)
            index = self.assembly_box.count() - 1
            self.assembly_box.model().item(index).setEnabled(False)
            self.assembly_box.setItemData(index, "%s SIA 265 6.1.1.11." % self.tl(reason), Qt.ItemDataRole.ToolTipRole)
        self.assembly_box.currentIndexChanged.connect(self.on_assembly)
        form.addRow(self.app.label("cn_assembly"), self.assembly_box)
        self.form.addWidget(self.assembly_group)
        self._watch(self.assembly_group, ["p"])

        # --- Géométrie et matériau, rebuilt per assembly
        self.material_group = cards.card(self.t("cn_box_material"))
        self.material_layout = QVBoxLayout(self.material_group)
        self.form.addWidget(self.material_group)

        # --- Stabdübel, rebuilt too: n, n_quer and a_1 are per member, as the classeur has them.
        # ⚠️ It is built here and **added to the form after «Disposition des broches»** (the engineer,
        # v0.84): the pattern is drawn first and n_tot is read off it, so the box that settles the count
        # stands before the box that spends it.
        self.dowel_group = cards.card(self.t("cn_box_dowel"))
        self.dowel_layout = QVBoxLayout(self.dowel_group)

        # --- Disposition des broches
        self.layout_group = cards.card(self.t("cn_box_layout"))
        column = QVBoxLayout(self.layout_group)
        column.addWidget(self.note(self.t("cn_markers_note")))
        # Since v0.74 the coordinates are not typed here: they are the schema's, and this is the list of
        # its connector markers with a tick against the ones this connector carries. A cell that could be
        # typed into would be a second place for a number the schema already holds (section 2, rule 1).
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            "", self.t("cn_marker"), "x [mm]", "z [mm]"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.itemChanged.connect(self.on_marker_toggled)
        self.table.itemSelectionChanged.connect(self.on_marker_selected)
        self.table.setMouseTracking(True)
        self.table.cellEntered.connect(self.on_marker_hover)
        self.table.viewport().installEventFilter(self)
        self.hover_marker = None
        self.table.setMinimumHeight(150)
        self.table.setColumnWidth(0, 28)
        column.addWidget(self.table)
        self.markers_note = QLabel("")
        self.markers_note.setWordWrap(True)
        self.markers_note.setStyleSheet("color: %s;" % theme.colour("override"))
        self.markers_note.setVisible(False)
        column.addWidget(self.markers_note)
        row = QHBoxLayout()
        # «Reprendre du dessin» reads n and a_1 off the ticked pattern (derive_rows); its button had been lost
        # from the row though the method, its words and the reference docs all still named it.
        for key, slot in (("cn_tick_all", self.tick_all), ("cn_tick_none", self.tick_none), ("cn_derive", self.derive_rows)):
            button = QPushButton(self.t(key))
            button.clicked.connect(slot)
            row.addWidget(button)
        row.addStretch(1)
        column.addLayout(row)
        self.form.addWidget(self.layout_group)
        self._watch(self.layout_group, ["n_tot"])
        self.form.addWidget(self.dowel_group)

        # --- Conditions. Not in the engineer's own list of boxes, and kept: eta_t and the truss factor
        # have nowhere else to be said, and dropping the box would drop them silently.
        conditions = cards.card(self.t("cn_conditions"))
        column = QVBoxLayout(conditions)
        # the two factors are SIA 265's, read from calc/norms/ and never written into a label (docs/architecture/layout.md §11; periodic audit 260916)
        self.seismic_box = QCheckBox(self.t("cn_seismic", eta_t=self.decimal(sia265.eta_t(True))))
        self.seismic_box.toggled.connect(self.touch)
        self.truss_box = QCheckBox(self.t("cn_truss", factor=self.decimal(sia265.constant("truss_reduction"))))
        self.truss_box.toggled.connect(self.touch)
        # 5.3.6.2.2's condition under the box: the one sentence the report prints under R_d,Fachwerk, read from calc/norms/ and translated by the glossary (D-08)
        self.truss_note = QLabel(strings.translate(sia265.clause("truss_reduction")["condition"], self.app.lang))
        self.truss_note.setWordWrap(True)
        self.truss_note.setStyleSheet("color: %s;" % self.app.muted)
        column.addWidget(self.seismic_box)
        column.addWidget(self.truss_box)
        column.addWidget(self.truss_note)
        self.form.addWidget(conditions)
        self._watch(conditions, ["eta_t"])
        self.form.addStretch(1)

    def _field(self, form, label_key, symbol, widget, unit="", label_text=None, width=None, link=None):
        """One row: the classeur's own sentence, then the symbol, the entry, and the unit.

        The symbol sits **immediately left of the entry**, which is what the engineer asked for and what
        «Moments polaires» already does with b and h: a symbol written after the sentence is read as part
        of the sentence, and the eye cannot find it while typing.

        Every row carries a unit, «–» where the quantity genuinely has none, so that a missing unit is a
        decision somebody took and not one nobody noticed. They are set in a column of their own rather
        than as a spin box's suffix, so that they line up down the form and a read-only cell can have one too.
        """
        cell = QWidget()
        row = QHBoxLayout(cell)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        mark = QLabel(symbol)
        mark.setStyleSheet("font-style: italic;")
        mark.setMinimumWidth(SYMBOL_WIDTH)
        mark.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(mark)
        if link is not None:
            # the button beside a number that may follow a variable (spec 2026-10-11-variables-liees-champs-et-textes, UI-001): `link` is (where, key) -- "self" or a member's slot, and the field's key in the source
            wrapper = linkable_spin.LinkableSpin(widget, unit, symbol or label_key, lambda: self.app, self.app.lang, links.JOINTS)
            wrapper.changed.connect(self.touch)
            if not hasattr(self, "link_fields"):
                self.link_fields = {}
            self.link_fields[link] = wrapper
            row.addWidget(wrapper, 1)
        else:
            row.addWidget(widget, 1)
        widget.row_cell = cell   # the row's own widget, which setRowVisible names -- a linked field's parent is its wrapper
        tail = QLabel(unit or self.t("cn_no_unit"))
        tail.setMinimumWidth(UNIT_WIDTH)
        tail.setStyleSheet("color: %s;" % self.app.muted)
        row.addWidget(tail)
        caption = QLabel(label_text if label_text is not None else self.app.label(label_key))
        caption.setWordWrap(True)
        # ⚠️ FIXED, not maximum: a wrapped label in a QFormLayout is laid out at its one-line height
        # unless its width is settled, and the rows then draw on top of one another.
        caption.setFixedWidth(width or LABEL_WIDTH)
        caption.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        form.addRow(caption, cell)
        return widget

    def _readonly(self, form, name, label_key, symbol, unit="", label_text=None, width=None):
        """A cell the calculation fills: the formula cells of the classeur, which are read and never typed into."""
        view = QLabel("—")
        view.setFont(self.app.mono_font)
        view.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        view.setStyleSheet("color: %s;" % self.app.muted)
        self.computed[name] = view
        return self._field(form, label_key, symbol, view, unit, label_text, width)

    def _watch(self, box, results, member=None):
        """Which results a box produces -- read off the classeur's structure, where a formula cell closes a run of entries. The hover lights the box and those results together (the engineer's own request). `member` is the index of the member a «Pièce» box is, whose piece the pattern lights while the pointer is in it."""
        first = box not in self.box_results
        self.box_results[box] = list(results)
        if member is not None:
            self.member_boxes[box] = member
        if first:
            box.installEventFilter(self)   # once per box: the two rebuilt ones pass here on every rebuild

    def update_hot(self):
        """Lights the INNERMOST watched box under the pointer. Boxes nest -- «Pièce 1» inside «Géométrie et matériau» -- and Qt sends a parent no Leave when the pointer moves into a child, nor an Enter when it comes back, so which box is hot is asked of the pointer's position rather than inferred from the event."""
        widget = QApplication.widgetAt(QCursor.pos())
        while widget is not None and widget not in self.box_results:
            widget = widget.parentWidget()
        self.set_hot(widget)

    def eventFilter(self, obj, event):
        if obj in self.box_results and event.type() in (QEvent.Type.Enter, QEvent.Type.Leave):
            self.update_hot()
        try:
            viewport = self.table.viewport() if getattr(self, "table", None) is not None else None
        except RuntimeError:     # the window torn down: its table is gone before the filter is
            return False
        if obj is viewport and event.type() == QEvent.Type.Leave:
            self.on_marker_hover(-1)
        return super().eventFilter(obj, event)

    def on_marker_hover(self, row, _column=0):
        """The marker of the row under the pointer, lit on the pattern beside the form (v0.75: the plan's «le survol d'une ligne met le point en évidence sur la figure 1»); -1 is the pointer gone."""
        item = self.table.item(row, 0) if row >= 0 else None
        marker = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        if marker == getattr(self, "hover_marker", None):
            return
        self.hover_marker = marker
        self.refresh_pattern()

    def refresh_pattern(self):
        """The two drawings, redrawn -- what a hover changes, without the calculation behind the form being run again.

        Both, since v0.84: hovering a «Pièce» box lights that member's element on the pattern **and its
        piece or pieces on the section** (the engineer). Which piece that is is `connector_svg`'s own
        answer -- the outer two of a zweischnittig joint for member 1, the middle one for member 2.
        """
        try:
            self.pattern_svg.load(QByteArray(connector_svg.pattern_of(
                self.draft(), self.detail(), lang=self.app.lang, highlight=self.marked(),
                positions=connector.known_positions(project.current().data_dir)).encode("utf-8")))
            self.pattern_svg.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        except Exception:  # broad: a drawing that fails must not empty the form -- but it is said, never silent (spec 2026-10-19-base-saine-nettoyage, G5)
            traceback.print_exc()
        self.refresh_section()

    def refresh_section(self):
        """The section alone, with the hovered member's piece(s) ringed."""
        try:
            self.section_svg.load(QByteArray(connector_svg.section_of(
                self.draft(), note=self.section_note(),
                highlight=getattr(self, "hover_member", None)).encode("utf-8")))
            self.section_svg.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        except Exception:  # broad: a drawing that fails must not empty the form -- but it is said, never silent (spec 2026-10-19-base-saine-nettoyage, G5)
            traceback.print_exc()

    def section_note(self):
        """What the section says where the diameter could not be drawn to scale, in the window's language."""
        return {state: strings.text("connector.section_" + state, self.app.lang)
                for state in ("enlarged", "reduced")}

    def set_hot(self, box):
        if box is self.hot_box:
            return
        for candidate in list(self.box_results):
            if not isValid(candidate):
                self.box_results.pop(candidate, None)
                self.member_boxes.pop(candidate, None)
                continue
            on = candidate is box
            if bool(candidate.property("hot")) != on:
                candidate.setProperty("hot", on)
                candidate.style().unpolish(candidate)
                candidate.style().polish(candidate)
                candidate.update()
        self.hot_box = box
        # A member's box lights that member's piece on the pattern beside the form and on the section
        # under it, the two drawings and the form all saying the same thing.
        index = self.member_boxes.get(box)
        element = ""
        if index is not None and index < len(getattr(self, "member_fields", [])):
            element = self.member_fields[index]["element"].currentData() or ""
        member = None if index is None else index + 1
        if element != self.hover_element or member != getattr(self, "hover_member", None):
            self.hover_element, self.hover_member = element, member
            self.refresh_pattern()
        self.fill_results()

    def member_material(self, index, two):
        """One timber member's material fields. `two` says whether it shares the box with a second one."""
        widgets = {}
        box = QGroupBox(self.t("cn_member", n=index + 1) if two else "")
        box.setFlat(not two)
        box.setProperty("card", two)   # a titled «Pièce» is a card inside its card; an untitled one stays a flat box, a card's room for a title being empty then
        form = QFormLayout(box)
        narrow = COLUMN_LABEL_WIDTH if two else LABEL_WIDTH
        widgets["alpha"] = self._field(form, "cn_alpha_long", "α", self._spin(0.0, 90.0, 1, 5.0), "°", width=narrow, link=(index, "alpha"))
        # The piece this member is: an ELEMENT of the schema since v0.74, and it is through that element
        # that the member reaches its position, and so its strength class and its moisture class. The
        # combo is filled from the schema in force (`fill_elements`), and choosing one lights that piece
        # on the drawing beside the form.
        widgets["element"] = QComboBox()
        widgets["element"].currentIndexChanged.connect(self.on_element)
        self._field(form, "cn_element", "", widgets["element"], "", width=narrow)
        widgets["grade"] = QComboBox()
        # The item's DATA is the grade and its text what is shown: a grade that follows its position reads «C24 — T001» in the field itself, so the combo's text is never what the code compares.
        for grade in sia265.grades():
            widgets["grade"].addItem(grade, grade)
        widgets["grade"].currentIndexChanged.connect(self.touch)
        self._field(form, "cn_grade", "", widgets["grade"], "", width=narrow)
        # The line under the grade, and only while it is WRITTEN OVER (orange, with «Reprendre») or its position is gone (orange): a grade that follows says so in the field itself.
        note = QWidget()
        line = QHBoxLayout(note)
        line.setContentsMargins(0, 0, 0, 0)
        widgets["grade_note"] = QLabel("")
        widgets["grade_note"].setWordWrap(True)
        widgets["grade_note"].setStyleSheet("color: %s;" % theme.colour("override"))
        widgets["grade_back"] = QPushButton(self.t("cn_take_back"))
        widgets["grade_back"].setVisible(False)
        widgets["grade_back"].clicked.connect(lambda _c, i=index: self.take_back(i))
        line.addWidget(widgets["grade_note"], 1)
        line.addWidget(widgets["grade_back"])
        form.addRow("", note)
        widgets["note_row"] = note
        widgets["form"] = form
        # What the member IS, whether or not the calculation runs: its position's material (Positionen.xlsx) and the characteristic density of its grade, SIA 265 Tabelle 8/9's 5 % fractile -- fill_member_values() fills both. ⚠️ No mean unit weight (SIA 261 Tabelle 28): nothing calculates with it, the engineer's own word (v0.77).
        self._readonly(form, "species_%d" % (index + 1), "cn_species", "", "", width=narrow)
        self._readonly(form, "rho_k_%d" % (index + 1), "cn_rho", "ρ_k", "kg/m³", width=narrow)
        # a Stahl-Holz joint's member 1 has its thickness in the steel half's own b, which is where its link is (below)
        widgets["t"] = self._field(form, "cn_thickness", "t", self._spin(1.0, 2000.0, 1, 10.0), "mm", width=narrow, link=(index, "t") if two else None)
        # ⚠️ A Stahl-Holz joint's timber thickness is the steel half's own b (Bauteildicke), which is what draft()
        # saves: a t shown here beside it would be a field typed into and never read (v0.75, the audit's finding).
        form.setRowVisible(widgets["t"].row_cell, two)
        widgets["predrilled"] = QCheckBox()
        widgets["predrilled"].toggled.connect(self.touch)
        self._field(form, "cn_predrilled", "", widgets["predrilled"], "", width=narrow)
        self._watch(box, ["f_h_%d" % (index + 1)], member=index)
        return box, widgets

    def build_material(self, assembly, spec, timber):
        """«Géométrie et matériau», in one of four shapes -- exactly the engineer's own list."""
        head = QWidget()
        form = QFormLayout(head)
        form.setContentsMargins(0, 0, 0, 0)
        self.diameter_box = self._field(form, "cn_diameter", "d", self._spin(1.0, 60.0, 1, 1.0), "mm", link=("self", "diameter"))
        self.diameter_box.valueChanged.connect(self.on_diameter)
        self.moisture_box = QComboBox()
        self.moisture_box.addItem("—", None)                # follow the members' positions
        for value in sia265.moisture_class_ids():
            self.moisture_box.addItem(str(value), value)
        self.moisture_box.currentIndexChanged.connect(self.touch)
        self._field(form, "cn_moisture", "", self.moisture_box, "")
        self.moisture_note = QLabel("")
        self.moisture_note.setWordWrap(True)
        self.moisture_note.setStyleSheet("color: %s;" % theme.colour("override"))
        # «Reprendre» on the moisture class's own line too (v0.75), as the plan set it for every value taken from a position
        self.moisture_back = QPushButton(self.t("cn_take_back"))
        self.moisture_back.setVisible(False)
        self.moisture_back.clicked.connect(self.take_back_moisture)
        moisture_line = QWidget()
        line = QHBoxLayout(moisture_line)
        line.setContentsMargins(0, 0, 0, 0)
        line.addWidget(self.moisture_note, 1)
        line.addWidget(self.moisture_back)
        form.addRow("", moisture_line)
        self.moisture_form, self.moisture_line = form, moisture_line
        self.material_layout.addWidget(head)

        two = spec["family"] == "timber-timber"
        self.member_fields = []
        holder = cards.Reflow()   # side by side where the column has the room, one under the other where it does not (cards.py)
        for index in range(spec["members"] if two else 1):
            box, widgets = self.member_material(index, two)
            holder.addWidget(box)
            self.member_fields.append(widgets)
        self.material_layout.addWidget(holder)

        # --- the steel half, for a Stahl-Holz joint: the classeur's own b, t, n and the cells they feed
        self.plate_fields = {}
        if not two:
            plates = QWidget()
            form = QFormLayout(plates)
            form.setContentsMargins(0, 0, 0, 0)
            self.plate_fields["b"] = self._field(form, "cn_b", "b", self._spin(1.0, 2000.0, 1, 10.0), "mm", link=(0, "t"))
            self.plate_fields["slot"] = self._field(form, "cn_slot", "t", self._spin(0.0, 60.0, 1, 1.0), "mm", link=(0, "plates.slot"))
            self.plate_fields["count"] = QSpinBox()
            self.plate_fields["count"].setRange(1, 8)
            self.plate_fields["count"].valueChanged.connect(self.touch)
            self._field(form, "cn_plates_n", "n", self.plate_fields["count"], "")
            self._readonly(form, "t_1", "cn_t1", "t₁", "mm")
            self._readonly(form, "t_2", "cn_t2", "t₂", "mm")
            self.plate_fields["ratio"] = self._field(
                form, "cn_ratio", "t₁/t₂", self._spin(0.05, 5.0, 2, 0.05), "", link=(0, "plates.ratio"))
            self._readonly(form, "k_beta", "cn_kbeta", "k_β", "")
            self._readonly(form, "k_beta_2", "cn_kbeta2", "k_β,₂", "")
            self._readonly(form, "p_k_beta", "cn_pkbeta", "p·k_β", "")
            if assembly == "Stahl-Holz, Bleche aussen":
                # The engineer's own list for outer plates is d · Feuchteklasse · Festigkeitsklasse · α · b · t₁ · k_β
                # (v0.75): equation (128) reads the timber between the plates whole, so no slot, no plate count, no
                # t₂ and no second k_β enter it -- dowel.py reads none of them for this assembly.
                for hidden in (self.plate_fields["slot"], self.plate_fields["count"], self.computed["t_2"],
                               self.plate_fields["ratio"], self.computed["k_beta_2"], self.computed["p_k_beta"]):
                    form.setRowVisible(getattr(hidden, "row_cell", None) or hidden.parentWidget(), False)
            self.material_layout.addWidget(plates)
        else:
            self._readonly(QFormLayout(self._loose()), "k_beta", "cn_kbeta", "k_β", "")

        results = ["f_h_%d" % (i + 1) for i in range(len(self.member_fields))]
        results += ["t_1", "t_2", "k_beta", "k_beta_2", "p_k_beta"]
        self._watch(self.material_group, results)

    def _loose(self):
        """A holder for a read-only cell that belongs to «Géométrie et matériau» but to none of its columns."""
        holder = QWidget()
        self.material_layout.addWidget(holder)
        return holder

    def build_dowel(self, spec):
        """«Stabdübel»: n_tot, p, and -- one column per timber member, as the classeur has them -- n, n_quer and a_1, then f_u,k and M_u,k."""
        head = QWidget()
        form = QFormLayout(head)
        form.setContentsMargins(0, 0, 0, 0)
        self.n_tot_box = QSpinBox()
        self.n_tot_box.setRange(1, 400)
        self.n_tot_box.valueChanged.connect(self.touch)
        self._field(form, "cn_n_tot_long", 'n_tot', self.n_tot_box, "")
        self.n_tot_override = QCheckBox(self.t("cn_n_tot_override"))
        self.n_tot_override.toggled.connect(self.touch)
        self.n_tot_override.toggled.connect(self.sync_n_tot)
        form.addRow("", self.n_tot_override)
        self._readonly(form, "p", "cn_p", "p", "")
        self.dowel_layout.addWidget(head)

        holder = cards.Reflow()   # as in «Géométrie et matériau»
        count = spec["members"] if spec["family"] == "timber-timber" else 1
        for index in range(count):
            box = QGroupBox(self.t("cn_member", n=index + 1) if count > 1 else "")
            box.setFlat(count == 1)
            box.setProperty("card", count > 1)   # as in member_material
            form = QFormLayout(box)
            narrow = COLUMN_LABEL_WIDTH if count > 1 else LABEL_WIDTH
            widgets = self.member_fields[index] if index < len(self.member_fields) else {}
            widgets["n"] = QSpinBox()
            widgets["n"].setRange(1, 60)
            widgets["n"].valueChanged.connect(self.touch)
            self._field(form, "cn_n_long", "n", widgets["n"], "", width=narrow)
            self._readonly(form, "n_quer_%d" % (index + 1), "cn_nquer", "n_quer", "", width=narrow)
            widgets["a_1"] = self._field(form, "cn_a1_long", "a₁", self._spin(0.0, 2000.0, 1, 10.0), "mm", width=narrow, link=(index, "a_1"))
            self._watch(box, ["n_quer_%d" % (index + 1)], member=index)
            holder.addWidget(box)
        self.dowel_layout.addWidget(holder)

        tail = QWidget()
        form = QFormLayout(tail)
        form.setContentsMargins(0, 0, 0, 0)
        # The PLATE's steel, SIA 263 Tabelle 1 -- for a Stahl-Holz joint only: a Holz-Holz joint has no plate
        # (the engineer, v0.77). The dowel's own steel is not asked for: SIA 265 reads its f_u,k and nothing else.
        self.steel_box = QComboBox()
        self.steel_box.addItem("—", "")
        for name in sia263.plate_grades():
            self.steel_box.addItem(name, name)
        self.steel_box.currentIndexChanged.connect(self.touch)
        self._field(form, "cn_steel_plate", "", self.steel_box, "")
        form.setRowVisible(self.steel_box.row_cell, spec["family"] == "steel-timber")
        # The plate's bearing on the dowels, SIA 263 Tabelle 16 (76) and 6.2.5 (spec 2026-10-12-audit-issues-47-48-49, D-14): its thickness, its smallest end distance along the force, its edge distance across it and the hole -- 0 while not stated, which the export says; p1 and p2 are read off the drawing
        self.plate_boxes = {}
        for key, words, symbol in (("t", "cn_plate_t", "t_pl"), ("e1", "cn_plate_e1", "e₁"), ("e2", "cn_plate_e2", "e₂"), ("d0", "cn_plate_d0", "d₀")):
            box = self._field(form, words, symbol, self._spin(0.0, 500.0, 1, 1.0), "mm", link=("self", "plate." + key))
            form.setRowVisible(box.row_cell, spec["family"] == "steel-timber")
            self.plate_boxes[key] = box
        # The DOWEL's steel (spec 2026-10-12-audit-issues-47-48-49, D-06): a grade of SIA 263 Tabelle 1 whose f_y meets SN EN 14592 Tabelle G.9 -- it fills f_u,k, which stays writable; a value typed over it sets the grade back to «—»
        self.dowel_steel_box = QComboBox()
        self.dowel_steel_box.addItem("—", "")
        for name in sn_en_14592.dowel_grades():
            self.dowel_steel_box.addItem(name, name)
        self._field(form, "cn_dowel_steel", "", self.dowel_steel_box, "")
        self.f_u_k_box = self._field(form, "cn_f_u_k", "f_u,k", self._spin(100.0, 1500.0, 0, 10.0), "N/mm²", link=("self", "dowel.f_u_k"))
        self.dowel_steel_box.currentIndexChanged.connect(self.on_dowel_steel)
        self.f_u_k_box.valueChanged.connect(self.on_f_u_k)
        # Where f_u,k comes from, said under it: SIA 263 Tabelle 1 for the grade, SN EN 14592 asking only f_y >= 235 N/mm².
        requirement = sn_en_14592.requirement()
        self.f_u_k_note = QLabel(self.t("cn_f_u_k_note", min_yield=_n(requirement["min_yield"]), norm=requirement["norm"] + " " + requirement["norm_ref"]))
        self.f_u_k_note.setWordWrap(True)
        self.f_u_k_note.setStyleSheet("color: %s;" % self.app.muted)
        form.addRow("", self.f_u_k_note)
        self._readonly(form, "M_u_k", "cn_mu_k", "M_u,k", "Nmm")
        self.dowel_layout.addWidget(tail)
        self._watch(self.dowel_group, ["k_red", "M_u_k"])

    def build_preview(self):
        panel = QWidget()
        column = QVBoxLayout(panel)
        column.setContentsMargins(0, 0, 0, 0)

        figures = cards.card(self.t("cn_figures"))   # the two drawings on their paper, in a card (cards.py)
        fv = QVBoxLayout(figures)
        self.pattern_svg = QSvgWidget()
        self.pattern_svg.setMinimumHeight(180)
        self.pattern_svg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        fv.addWidget(self.pattern_svg, 3)
        self.section_svg = QSvgWidget()
        self.section_svg.setMinimumHeight(120)
        self.section_svg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        fv.addWidget(self.section_svg, 2)
        column.addWidget(figures, 5)

        # what is read off them, in cards on the soft ground; read, not typed, so the pane may be narrower than it (hold=False)
        scroll, details = cards.column(margins=(0, 10, 4, 0), hold=False)

        results = cards.card(self.t("cn_results"))
        rv = QVBoxLayout(results)
        self.results = QLabel("")
        self.results.setTextFormat(Qt.TextFormat.RichText)
        self.results.setFont(self.app.mono_font)
        self.results.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.results.setWordWrap(True)
        rv.addWidget(self.results)
        details.addWidget(results)

        details.addStretch(1)
        column.addWidget(scroll, 3)

        self.message = QLabel("")
        self.message.setTextFormat(Qt.TextFormat.RichText)  # a warning's symbols are set with their subscripts (_prose_html)
        self.message.setWordWrap(True)
        self.message.setProperty("callout", "warning")  # «in yellow inside the pane», the site's warning callout since v0.90
        self.message.setVisible(False)
        column.addWidget(self.message)

        actions = QHBoxLayout()
        revert = QPushButton(self.t("cn_revert"))
        revert.clicked.connect(self.revert)
        save = QPushButton(self.t("cn_save"))
        save.setDefault(True)
        save.clicked.connect(self.save)
        actions.addStretch(1)
        actions.addWidget(revert)
        actions.addWidget(save)
        column.addLayout(actions)
        return panel
