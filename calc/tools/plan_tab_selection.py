"""PlanTab's tools, its new elements and their positions, the messages, the selection and the properties of what is selected -- elements, axes, storeys -- a mixin of methods moved verbatim out of calc/tools/plan_tab.py (issue #30). PlanTab names it among its bases.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPlainTextEdit, QPushButton, QSizePolicy, QSpinBox, QVBoxLayout, QWidget,
)
import positions_store  # the project's positions, Woodcore's own file (calc/positions_store.py, v0.114)
import plan_properties  # the pane of a drawing tool, and the *Section* of a position (issue #9)
import plan_canvas_tools  # the dimension tools (issue #9)
import plan_canvas_outline  # the building's outline (issue #54)
import plan_centres_card  # the stiffness and mass centres' card, and a bracing wall's «Mode de construction» (issue #54)
import project  # where the project this tab works on is (calc/project.py)
import theme  # the colours this tab states itself (theme.py, v0.90)
import cards  # the properties in cards, after the website (cards.py)
import validation
from domains import connector  # position_dimension: a position's dimension and unit, or nothing where it states none
from domains import plan as model
from domains import plan_clip  # Ctrl+C and Ctrl+V between plans (issue #61)
from domains import plan_centres  # which walls brace, and whether a plan has a stiffness centre at all (issue #54)
from domains import plan_svg
from drawing_tab import (  # noqa: F401 -- names the tab's own code uses, and names other modules and the tests read here
    Blank, CurrentStack, DrawingTab, HISTORY, KINDS, NEW_ROW, document_text, next_free_id, number_text, plain_label, plan_text, svg_icon,
)
import notifications  # every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # what was a message box is a notice since v0.117 (notices_ui.tell)
import plan_canvas_edit  # «Déplacer», «Copier» and «Ligne d'aide» (issue #18)
from plan_tab_build import DRAW_DIMENSIONS, LEVEL_TOOL, SECTION_TOOLS, STOREY_BOX_ICON, STOREY_TOOLS, SUBTYPE_TOOLS, TOOLS, UNITS, list_plans, PlanBuildMixin  # split out of this module (issue #30): every name it had is still importable from it


PANE_TOOLS = ("crop", "calibrate")


# The draft's own key for the positions it draws and the project has not got yet -- their section chosen, written by «Enregistrer» (issue #9); taken off before the plan is checked or written, never in a plan's file.
PENDING = "_pending_positions"


class PlanSelectionMixin:
    """Methods of plan_tab.PlanTab, moved verbatim (issue #30): the class names this mixin among its bases."""

    def choose_tool(self, tool):
        if not self.tool_shown(tool):
            tool = "select"  # a tool the plan's type does not carry -- its letter typed on a section, say
        self.canvas.set_tool(tool)
        self.mark_tool(tool)
        self.loading = True
        self.subtype_combo.clear()
        if tool in SUBTYPE_TOOLS:
            for subtype in model.TYPES[tool]["subtypes"]:
                self.subtype_combo.addItem(self.t(f"plan_sub_{subtype}"), subtype)
            current = self.canvas.subtypes.get(tool)
            self.subtype_combo.setCurrentIndex(max(0, self.subtype_combo.findData(current)))
        self.subtype_combo.setVisible(tool in SUBTYPE_TOOLS)
        self.loading = False
        kind = self.canvas.tool_kind()
        hint = {"line": "plan_hint_line", "poly": "plan_hint_poly", "point": "plan_hint_point"}.get(kind)
        if kind == "line" and model.point_count(tool) == 2:
            hint = "plan_hint_segment"
        if tool in ("axis-v", "axis-h"):
            hint = "plan_hint_axis"
        elif tool == "axis-o":
            hint = "plan_hint_axis_o"
        elif tool in ("select", "pan", "ruler") + PANE_TOOLS:
            hint = f"plan_hint_{tool}"
        elif tool in SECTION_TOOLS:
            hint = {"storey-line": "plan_hint_storey_line", "storey-box": "plan_hint_storey_box", LEVEL_TOOL: "plan_hint_load_level"}[tool]
        elif plan_canvas_tools.is_dimension_tool(tool):
            hint = {"dimension-chain": "plan_hint_dimension_chain", "dimension-angle": "plan_hint_dimension_angle"}.get(tool, "plan_hint_dimension")
        elif plan_canvas_edit.handles(tool):
            hint = "plan_hint_" + tool.replace("-", "_")
        elif tool == plan_canvas_outline.TOOL:
            hint = "plan_hint_outline"   # an area as every other, and one a plan (issue #54)
        text = self.t(hint) if hint else ""
        self.hint.setText(text)
        if hasattr(self, "selection_layout"):
            self.refresh_selection()   # the pane follows a drawing tool from its first moment (issue #9)
        self.canvas.setFocus()

    def on_edit_refused(self, tool):
        """«Déplacer» or «Copier» with nothing selected, a parallel aid clicked off any line, or the building's outline asked to be copied -- a plan has one (issue #54): said where the tool's hint is."""
        self.hint.setText(self.t({"aid-par": "plan_aid_no_line", plan_canvas_outline.KIND: "plan_outline_single"}.get(tool, "plan_edit_nothing")))

    def ask_aid_distance(self):
        """A parallel aid's distance, asked in metres where the plan has a scale and in the sheet's units otherwise: in sheet units, or None where the question is cancelled."""
        per_m = model.units_per_m(self.source)
        unit = "m" if per_m else self.unit()
        value, ok = QInputDialog.getDouble(self, self.t("plan_aid_distance_title"), self.t("plan_aid_distance", unit=unit), 1.0 if per_m else 100.0, 0.0, 1e6, 3)
        if not ok or value <= 0:
            return None
        return value * per_m if per_m else value

    def on_tool_subtype(self, _index):
        if self.loading:
            return
        tool = self.canvas.tool
        subtype = self.subtype_combo.currentData()
        if tool in SUBTYPE_TOOLS and subtype:
            self.canvas.subtypes[tool] = subtype

    def propose_label(self, type_, create=False):
        """The number a new element of this type is given (issue #9, the engineer: «chaque nouvel objet dessiné augmente le numéro de 1 … le compteur est propre à chaque préfixe et à chaque étage»): the next of its letter on the plan's storey, over the project's positions and the numbers this plan draws and has not saved yet -- S101, S102 …, S201 on the second floor (positions_store.propose_id). Nothing is written: the plan's «Enregistrer» makes the positions (`save`), so drawing, undoing and drawing again leaves no gap. `create` is the canvas's asking as it draws, kept for its callers; it writes nothing either."""
        if model.is_load(type_):
            return model.next_load_label(self.source, type_)  # a load is numbered by the plan, one after another, and is no position (v0.116)
        if not model.labelled(type_):
            return ""
        taken = list(self.position_ids) + model.plan_labels(self.source)
        return positions_store.propose_id(taken, type_, self.source.get("floor") or "0")

    def pending_positions(self):
        """The positions this plan draws and the project has not got yet, {number: {type, section_type, dimension, units}} in the order drawn -- kept in the draft under PENDING (so «Annuler» takes a section chosen back with the rest) and written by `save`."""
        return self.source.get(PENDING, {})

    def on_new_element(self, element):
        """A new element, inside the step of «Annuler» that draws it: what its tool was set to in the right pane (plan.apply_defaults, REQ-015), and for a position it makes, which the project has not got, the section the tool states, else the section of the last of its type (issue #9: «par défaut, la section proposée est celle du dernier objet du même type dessiné»), held until the plan is saved."""
        model.apply_defaults(element, self.canvas.tool_defaults.get(element["type"]))
        label = element.get("label")
        if not label or model.is_load(element["type"]) or not model.labelled(element["type"]) or label in self.position_ids:
            return
        pending = self.source.setdefault(PENDING, {})
        if label in pending:
            return
        type_name = positions_store.type_for(element["type"])
        stated = self.canvas.tool_defaults.get(element["type"], {}).get("section")
        pending[label] = {"type": type_name, **(stated or positions_store.last_section_of_type(list(self.positions) + self.pending_rows(), type_name) or {})}

    def pending_rows(self):
        """The positions drawn and not saved yet, as rows -- after the project's, in the order drawn."""
        return [{"position": number, **row} for number, row in self.pending_positions().items()]

    def on_pointer(self, x, y, kind):
        text = self.t("plan_pointer", x=number_text(x, 1), y=number_text(y, 1), unit=self.unit())
        per_m = model.units_per_m(self.source)
        if per_m:
            crop = model.crop_of(self.source)
            text += self.t("plan_pointer_m", x=number_text((x - crop["x"]) / per_m, 2), y=number_text((y - crop["y"]) / per_m, 2))
        if kind:
            text += self.t("plan_snapped", kind=self.t(f"plan_snap_kind_{kind}"))
        self.pointer_line.setText(text)

    def flagged(self):
        """The numbers outlined in red on the canvas: those the project's positions do not have. A number drawn several times is not one -- identical elements share it."""
        known = set(self.position_ids)
        return {label for label in model.plan_labels(self.source) if label not in known}

    def on_changed(self):
        if not self.loading:
            self.dirty = True
        flagged = self.flagged()
        if flagged != self.canvas.flagged:
            self.canvas.flagged = flagged
            self.canvas.redraw()
        self.update_crop_text()
        self.update_scale_widgets()
        self.refresh_elements()
        self.refresh_messages()
        self.refresh_selection()
        self.centres_card.refresh()   # S and M follow the drawing: what they stand on, or why one is not there (issue #54)
        self.revert_button.setEnabled(self.dirty)
        self.update_list_marker()

    def refresh_messages(self):
        messages = []
        try:
            # checked at the version «Enregistrer» will write it at (plan.version_of), not at the one it was read at: a text, an outline or a wall's mode put on a plan read as 1.6 is no defect of the draft
            model.check_source({**self.source, "schema_version": model.version_of(self.source)}, f"{self.source.get('id') or '?'}.json")
        except validation.ValidationError as exc:
            messages.append(str(exc))
        background = self.source.get("background")
        if background:
            path = model.background_path(project.current().root, background["file"])
            if path is None or not path.is_file():
                messages.append(self.t("plan_background_missing", file=background["file"]))
        problem = getattr(self.canvas, "background_problem", None)
        if problem is not None:
            messages.append(self.document_error_text(problem))
        # with the positions' section types, and those chosen in the pane and not saved yet over them: a bracing wall's mode is held against its position's section (issue #54)
        messages += [self.app.note_text(n) for n in model.warnings(self.source, self.position_ids, sections=self.section_types())]
        text = "\n".join(messages)
        if text != self.message.toPlainText():
            self.message.setPlainText(text)
        missing = sorted({label for label in model.plan_labels(self.source) if label not in set(self.position_ids)})
        self.missing.setText(self.t("plan_missing", labels=", ".join(missing)) if missing else "")
        self.missing.setVisible(bool(missing))
        self.missing_button.setVisible(bool(missing))

    def section_types(self):
        """{position: section type} as the plan's warnings and its export read it (positions_store.section_types): the project's positions, and over them the sections chosen in the pane for this plan's and not saved yet (pending_positions)."""
        return positions_store.section_types(list(self.positions) + self.pending_rows())

    def add_missing_positions(self):
        """«Ajouter aux positions»: every number the plan shows that the project has no position of, written as a blank position of its element's type (positions_store.create_blank) -- a position renamed or taken away since it was drawn, brought back to be completed in the Positions tab."""
        if getattr(self.app, "read_only", False):
            self.app.refuse_read_only()
            return []
        known = set(self.position_ids)
        added = []
        for element in self.source.get("elements", []):
            label = element.get("label", "")
            if label and label not in known and label not in added and not model.is_load(element["type"]):  # a load is numbered by the plan, and is no position (v0.116)
                try:
                    positions_store.create_blank(project.current(), label, positions_store.type_for(element["type"]))
                except (validation.ValidationError, OSError) as exc:
                    notices_ui.tell(str(exc), notifications.CRITICAL, exc=exc, source="plan_tab")
                    break
                added.append(label)
        if added:
            self.reread_positions()
            self.created_positions = True
            self.on_changed_quietly()
            self.app.set_status(self.t("plan_missing_added", labels=", ".join(added)))
        return added

    def refresh_elements(self):
        self.element_list.blockSignals(True)
        try:
            self.element_list.clear()
            flagged = self.canvas.flagged
            for i, element in enumerate(self.source.get("elements", [])):
                label = element.get("label", "")
                name = model.type_name(element["type"], element.get("subtype"))
                text = f"{label or '—'} · {name}" + (" ⚠" if label in flagged else "")
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, ("element", i))
                self.element_list.addItem(item)
            # the axes in the order of their names, whatever order they were drawn in
            for i, axis in sorted(enumerate(self.source.get("axes", [])), key=lambda pair: model.axis_sort_key(pair[1])):
                item = QListWidgetItem(self.t("plan_axis_item", label=axis["label"]))
                item.setData(Qt.ItemDataRole.UserRole, ("axis", i))
                self.element_list.addItem(item)
            self.select_row(self.canvas.selection)
        finally:
            self.element_list.blockSignals(False)

    def select_row(self, selection):
        # an item's data may come back from Qt as a list where a tuple went in
        wanted = tuple(selection) if selection else None
        for i in range(self.element_list.count()):
            data = self.element_list.item(i).data(Qt.ItemDataRole.UserRole)
            if wanted is not None and tuple(data) == wanted:
                self.element_list.setCurrentRow(i)
                return
        self.element_list.setCurrentRow(-1)

    def on_element_row(self, current, _previous):
        if current is None:
            return
        if self.view_kind != "plan":
            self.show_plan_view()
        selection = tuple(current.data(Qt.ItemDataRole.UserRole))
        if selection != self.canvas.selection:
            self.canvas.select(selection)

    def on_selection(self):
        self.element_list.blockSignals(True)
        self.select_row(self.canvas.selection)
        self.element_list.blockSignals(False)
        self.refresh_selection()
        self.update_object_buttons()

    def clear_selection_panel(self):
        while self.selection_layout.count():
            item = self.selection_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self.clear_layout(item.layout())

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
            elif item.layout() is not None:
                self.clear_layout(item.layout())

    def refresh_selection(self):
        """The selection's properties, built anew -- an element's type, variant and position number (and a slab's span), an axis's name, angle, bubbles and distance to its neighbour -- and, under them, the size it is drawn at (build_entry_style).

        Its rows are a card's (`cards.form`), so a long label goes above its field rather than setting the card's width as the sum of the two -- the rule the plan's own properties took in v0.95.
        """
        if self.slider_down:
            return
        self.clear_selection_panel()
        self.entry_style = None      # the rows just deleted with the card: nothing may touch them again
        if self.drawing_tool():
            # a drawing tool chosen: the pane is its next element's, as if one of its type were selected (issue #9, REQ-015, D-014)
            form = cards.form()
            self.selection_layout.addLayout(form)
            plan_properties.tool_rows(self, form, self.canvas.tool)
            self.update_modules()
            return
        element = self.canvas.selected_element()
        axis = self.canvas.selected_axis()
        storey_line = self.canvas.selected_storey_line()
        storey_box = self.canvas.selected_storey_box()
        load_level = self.canvas.selected_load_level()
        dimension_selected = self.canvas._selected_of("dimension")
        aid_selected = self.canvas._selected_of("aid")
        text_selected = self.canvas._selected_of("text")
        if text_selected is not None:
            self.text_properties(text_selected)
            self.selection_layout.addWidget(self.build_entry_style())   # its own `text` factor (figure_style, `texts`)
            delete = QPushButton(self.t("plan_delete_selection"))
            delete.clicked.connect(self.canvas.delete_selection)
            self.selection_layout.addWidget(delete)
            self.update_modules()
            return
        if self.canvas._selected_of(plan_canvas_outline.KIND) is not None:
            # the building's outline (issue #54): what it is and how it is reshaped -- it has no property to set, its place being its points
            self.selection_layout.addWidget(self.note(self.t("plan_outline_selected")))
            delete = QPushButton(self.t("plan_delete_selection"))
            delete.clicked.connect(self.canvas.delete_selection)
            self.selection_layout.addWidget(delete)
            self.update_modules()
            return
        if aid_selected is not None:
            self.selection_layout.addWidget(self.note(self.t("plan_aid_selected", kind=self.t("plan_aid_kind_" + aid_selected.get("kind", "two-points")))))
            delete = QPushButton(self.t("plan_delete_selection"))
            delete.clicked.connect(self.canvas.delete_selection)
            self.selection_layout.addWidget(delete)
            self.update_modules()
            return
        if dimension_selected is not None:
            form = cards.form()
            self.selection_layout.addLayout(form)
            plan_properties.dimension_rows(self, form, dimension_selected)
            delete = QPushButton(self.t("plan_delete_selection"))
            delete.clicked.connect(self.canvas.delete_selection)
            self.selection_layout.addWidget(delete)
            self.update_modules()
            return
        if element is None and axis is None and storey_line is None and storey_box is None and load_level is None:
            # the card is hidden then, the plan's own modules shown in its place (update_modules); its note stays for a reader of the card alone
            self.selection_layout.addWidget(self.note(self.t("plan_nothing_selected")))
            self.update_modules()
            return
        form = cards.form()
        self.selection_layout.addLayout(form)
        if element is not None:
            self.element_properties(form, element)
        elif axis is not None:
            self.axis_properties(form, axis)
        elif load_level is not None:
            self.storey_properties(form, None, None, load_level)
        else:
            self.storey_properties(form, storey_line, storey_box)
        if element is not None or axis is not None:
            self.selection_layout.addWidget(self.build_entry_style())
        delete = QPushButton(self.t("plan_delete_selection"))
        delete.clicked.connect(self.canvas.delete_selection)
        self.selection_layout.addWidget(delete)
        self.update_modules()

    def has_selection(self):
        """Something selected on the plan open -- an element, an axis, or on a section a storey line or a storey box: the right pane then shows the selection's card and «Taille des symboles», and the plan's own modules no more (v0.116)."""
        canvas = self.canvas
        if self.drawing_tool():
            return True
        return any(found is not None for found in (canvas.selected_element(), canvas.selected_axis(), canvas.selected_storey_line(), canvas.selected_storey_box(), canvas.selected_load_level(), canvas._selected_of("dimension"), canvas._selected_of("aid"), canvas._selected_of("text"), canvas._selected_of(plan_canvas_outline.KIND)))

    def update_modules(self):
        """The right pane's cards for what is selected (drawing_tab) -- and the card of the stiffness and mass centres never on an elevation section, which has neither (issue #54)."""
        super().update_modules()
        card = getattr(self, "centres_group", None)
        if card is not None and not plan_centres.applies(self.source):
            card.hide()

    def drawing_tool(self):
        """Whether the tool chosen draws an element -- a position's symbol or a load --, whose options the pane then shows."""
        return self.canvas.tool in model.TYPES

    def storey_properties(self, form, line, box, level=None):
        """A storey line, a storey box or a load transfer level selected on a section: what it is and the storey it draws -- and for a box and a level the numbering character its designation x1xx is made of, which may be written over (v0.116)."""
        tool = "storey-line" if line is not None else ("storey-box" if box is not None else LEVEL_TOOL)
        entry = line if line is not None else (box if box is not None else level)
        form.addRow(self.t("plan_type"), plain_label(self.t(f"plan_tool_{tool.replace('-', '_')}"), wrap=True))
        form.addRow(self.t("plan_storey"), plain_label(entry.get("storey", "") or "—", wrap=True))
        if line is None:
            floor = QLineEdit(str(entry.get("floor") or ""))
            floor.setMaxLength(1)
            floor.setMaximumWidth(40)
            floor.setPlaceholderText(model.storey_floor(entry.get("storey", ""), self.other_floors()))
            floor.setToolTip(self.t("plan_floor_tip"))
            floor.editingFinished.connect(lambda floor=floor, entry=entry: self.set_entry_floor(entry, floor.text().strip()))
            form.addRow(self.t("plan_floor"), floor)

    def set_entry_floor(self, entry, floor):
        """A storey box's or a load level's numbering character written over (empty: proposed from its storey again)."""
        if floor == str(entry.get("floor") or ""):
            return

        def apply():
            if floor:
                entry["floor"] = floor
            else:
                entry.pop("floor", None)
        self.edit(apply)

    def selected_entry(self):
        """The entry whose own size factors the panel shows, and the collection it belongs to: `(element, "elements")`, `(axis, "axes")`, or `(None, None)` with nothing selected. Which collection it is decides which of the three factors it may state (`figure_style.ENTRY_KEYS`)."""
        element = self.canvas.selected_element()
        if element is not None:
            return element, "elements"
        axis = self.canvas.selected_axis()
        if axis is not None:
            return axis, "axes"
        text = self.canvas._selected_of("text")
        if text is not None:
            return text, "texts"   # issue #43
        return None, None

    def element_properties(self, form, element):
        type_ = element["type"]
        form.addRow(self.t("plan_type"), plain_label(self.t(f"plan_type_{type_}"), wrap=True))
        subtypes = model.TYPES[type_].get("subtypes")
        if subtypes:
            combo = QComboBox()
            for subtype in subtypes:
                combo.addItem(self.t(f"plan_sub_{subtype}"), subtype)
            combo.setCurrentIndex(max(0, combo.findData(element.get("subtype"))))
            combo.currentIndexChanged.connect(lambda _i, combo=combo: self.set_subtype(combo.currentData()))
            form.addRow(self.t("plan_subtype"), combo)
        if model.is_load(type_):
            # a load's number is the plan's own, free text (Pxxx, Lxxx), and no position (v0.116)
            number = QLineEdit(element.get("label", ""))
            number.setToolTip(self.t("plan_load_number_tip"))
            number.editingFinished.connect(lambda number=number: self.set_load_label(number.text().strip()))
            form.addRow(self.t("plan_load_number"), number)
            if type_ == "PL" and element.get("subtype") in ("horiz", "vh"):
                angle = QDoubleSpinBox()
                angle.setRange(-180, 180)
                angle.setDecimals(1)
                angle.setSuffix("°")
                angle.setValue(float(element.get("angle", 0) or 0))
                angle.editingFinished.connect(lambda angle=angle: self.set_element_field("angle", round(angle.value(), 2)))
                form.addRow(self.t("plan_load_angle"), angle)
        elif model.labelled(type_):
            label = element.get("label", "")
            plan_properties.element_section_rows(self, form, element)   # above the position (issue #9, UI-002)
            # a list to pick from, not a field to type in: an element carries a position of the project and nothing else
            combo = QComboBox()
            # as narrow as its pane allows rather than as wide as its longest position: the column of cards asks for its widest field (cards.Column)
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            combo.setMinimumContentsLength(10)
            for position in self.positions:
                if position["position"].startswith(type_):
                    # the type in the window's language -- the stored key is German (positions_store.type_label); the material as the engineer wrote it, a word of his and not of the norm (D10 of spec 2026-10-07-performance-erreurs-plans-legendes)
                    details = ", ".join(part for part in (positions_store.type_label(position.get("type", ""), self.app.lang), position.get("material", ""),
                                                          connector.position_dimension(position)) if part)
                    combo.addItem(f"{position['position']} — {details}" if details else position["position"], position["position"])
            if combo.findData(label) < 0:
                # a number the project no longer has, or none: shown for what it is until one of its positions is chosen
                combo.insertItem(0, f"{label} (?)" if label else self.t("plan_number_none"), label)
            combo.setCurrentIndex(max(0, combo.findData(label)))
            combo.activated.connect(lambda _i, combo=combo: self.set_label(combo.currentData()))
            form.addRow(self.t("plan_number"), combo)
            if label and label not in set(self.position_ids):
                warning = plain_label(self.t("plan_number_unknown", label=label), wrap=True)
                warning.setStyleSheet(f"color: {theme.colour('warning')};")
                form.addRow(warning)
            if label:
                # a number is moved on the plan itself; here it is only put back
                if element.get("label_offset"):
                    reset = QPushButton(self.t("plan_label_reset"))
                    reset.clicked.connect(self.reset_label)
                    form.addRow(self.t("plan_label_where"), reset)
                else:
                    form.addRow(self.t("plan_label_where"), self.note(self.t("plan_label_home")))
        if model.is_rotatable(element):
            # a column turned (source 1.4, the engineer: «un carré comme aujourd'hui, qu'il est possible de tourner (e.g. 30°)»)
            row = QHBoxLayout()
            angle = QDoubleSpinBox()
            angle.setRange(-180, 180)
            angle.setDecimals(1)
            angle.setSuffix("°")
            angle.setValue(float(element.get("angle", 0) or 0))
            angle.setToolTip(self.t("plan_element_angle_tip"))
            angle.editingFinished.connect(lambda angle=angle: self.set_angle(angle.value()))
            self.angle_spin = angle   # follows the circle while it is dragged (on_angle_dragged)
            turn = QPushButton(self.t("plan_turn_90"))
            turn.setToolTip(self.t("plan_turn_90_tip"))
            turn.clicked.connect(self.turn_quarter)
            row.addWidget(angle, 1)
            row.addWidget(turn)
            form.addRow(self.t("plan_element_angle"), row)
        if type_ in model.LENGTH_TYPES:
            # this element's length shown or hidden whatever the plan says, or as the plan says (source 1.4)
            length = QComboBox()
            for text, value in ((self.t("plan_length_follow"), None), (self.t("plan_length_on"), True), (self.t("plan_length_off"), False)):
                length.addItem(text, value)
            length.setCurrentIndex(max(0, length.findData(element.get("show_length"))))
            length.setEnabled(bool(model.units_per_m(self.source)))
            length.setToolTip(self.t("plan_lengths_tip"))
            length.activated.connect(lambda _i, length=length: self.set_show_length(length.currentData()))
            form.addRow(self.t("plan_element_length"), length)
        if type_ in plan_centres.WALL_TYPES:
            # how a bracing wall is built (issue #54): what its stiffness for the stiffness centre is taken from -- «non défini» until the engineer says, there being no default
            form.addRow(self.t("plan_construction"), plan_centres_card.construction_combo(self, element.get("construction"), self.set_construction))
        if type_ == "D":
            row = QHBoxLayout()
            span = QDoubleSpinBox()
            span.setRange(-180, 180)
            span.setDecimals(1)
            span.setSuffix("°")
            auto = QCheckBox(self.t("plan_span_auto"))
            auto.setChecked("span" not in element)
            span.setValue(float(element.get("span", model.default_span(element["points"]))))
            span.setEnabled("span" in element)
            auto.toggled.connect(lambda checked, span=span: self.set_span(None if checked else span.value()))
            span.editingFinished.connect(lambda span=span, auto=auto: None if auto.isChecked() else self.set_span(span.value()))
            row.addWidget(span)
            row.addWidget(auto)
            form.addRow(self.t("plan_span"), row)
            if element.get("subtype") == "normal":
                diagonal = QCheckBox(self.t("plan_diagonal"))
                diagonal.setChecked(bool(element.get("diagonal", 0)))
                diagonal.toggled.connect(lambda checked: self.set_element_field("diagonal", 1 if checked else 0))
                form.addRow("", diagonal)

    def axis_properties(self, form, axis):
        name = QLineEdit(axis["label"])
        name.editingFinished.connect(lambda name=name: self.set_axis_field("label", name.text().strip() or axis["label"]))
        form.addRow(self.t("plan_axis_label"), name)
        angle = QDoubleSpinBox()
        angle.setRange(-180, 180)
        angle.setDecimals(2)
        angle.setSuffix("°")
        angle.setValue(float(axis["angle"]))
        angle.editingFinished.connect(lambda angle=angle: self.set_axis_field("angle", round(angle.value(), 4)))
        form.addRow(self.t("plan_axis_angle"), angle)
        bubbles = QComboBox()
        for key in model.BUBBLES:
            bubbles.addItem(self.t(f"plan_bubbles_{key}"), key)
        bubbles.setCurrentIndex(max(0, bubbles.findData(axis.get("bubbles", "both"))))
        bubbles.currentIndexChanged.connect(lambda _i, bubbles=bubbles: self.set_axis_field("bubbles", bubbles.currentData()))
        form.addRow(self.t("plan_axis_bubbles"), bubbles)
        per_m = model.units_per_m(self.source)
        if per_m:
            previous = self.previous_parallel(axis, per_m)
            if previous is not None:
                other, distance = previous
                spin = QDoubleSpinBox()
                spin.setRange(0.001, 10000)
                spin.setDecimals(3)
                spin.setSuffix(" m")
                spin.setValue(distance)
                spin.editingFinished.connect(lambda spin=spin, other=other: self.set_axis_distance(other, spin.value(), per_m))
                form.addRow(self.t("plan_axis_distance", other=other["label"]), spin)
            row = QHBoxLayout()
            parallel = QDoubleSpinBox()
            parallel.setRange(-10000, 10000)
            parallel.setDecimals(3)
            parallel.setSuffix(" m")
            parallel.setValue(1.0)
            add = QPushButton(self.t("plan_axis_parallel_add"))
            add.clicked.connect(lambda _c=False, parallel=parallel: self.add_parallel(parallel.value(), per_m))
            row.addWidget(parallel, 1)
            row.addWidget(add)
            form.addRow(self.t("plan_axis_parallel"), row)

    def previous_parallel(self, axis, per_m):
        """The nearest axis parallel to `axis` on its negative side -- left of a vertical axis, above a horizontal one -- and its distance, in m."""
        best = None
        for other in self.source["axes"]:
            if other is axis:
                continue
            d = model.axis_distance(other, axis, per_m)
            if d is not None and d > 1e-9 and (best is None or d < best[1]):
                best = (other, d)
        return best

    def set_axis_distance(self, other, distance, per_m):
        axis = self.canvas.selected_axis()
        if axis is None:
            return

        def apply():
            moved = model.parallel_axis(other, distance, per_m, axis["label"])
            axis["point"] = moved["point"]
        self.edit(apply)

    def add_parallel(self, distance, per_m):
        """A new axis parallel to the one selected, named by where it lies, as one drawn on the plan is."""
        axis = self.canvas.selected_axis()
        if axis is None or distance == 0:
            return
        renames = []

        def apply():
            renames.extend(model.insert_axis(self.source["axes"], model.parallel_axis(axis, distance, per_m, ""), model.crop_of(self.source)))
        self.edit(apply)
        self.canvas.select(("axis", len(self.source["axes"]) - 1))
        if renames:
            self.on_axes_renamed(renames)

    # -- Ctrl+C and Ctrl+V (issue #61, drawing_tab_clip.py): what is the position plan's own --

    def make_clip(self, point):
        """The objects selected, taken at `point`, with the type and section of every position they show -- read now, from the project's positions or the ones this plan drew and has not saved yet, which are gone once it is (REQ-006)."""
        chosen = self.canvas.selected_entries()
        rows = {row["position"]: row for row in self.positions}
        pending = self.pending_positions()
        sections = {}
        for kind, index in chosen:
            label = self.source["elements"][index].get("label") if kind == "element" else None
            row = rows.get(label) or (pending.get(label) and {"position": label, **pending[label]})
            if label and row:
                sections[label] = {"type": row.get("type", ""), **(positions_store.section_of(row) or {})}
        return plan_clip.clip_plan(self.source, chosen, point, self.canvas.per_m(), sections, self.clip_root())

    def paste_clip(self, clip, point):
        """The clip put down at `point`, inside the change the caller opened: every element numbered on this plan's storey (`propose_label`), the positions it makes kept among the pending ones as one drawn is (`on_new_element`). Returns (the objects pasted, what is said)."""
        result = plan_clip.paste_plan(self.source, clip, point, self.canvas.per_m(), model.crop_of(self.canvas.frame_source()), self.propose_label)
        pending = self.source.setdefault(PENDING, {})
        made = plan_clip.new_positions(clip, result["relabelled"])
        for kind, index in result["added"]:
            label = self.source["elements"][index].get("label") if kind == "element" else None
            if label and label not in self.position_ids and label not in pending and not model.is_load(self.source["elements"][index]["type"]):
                pending[label] = made.get(label) or {"type": positions_store.type_for(self.source["elements"][index]["type"])}
        if not pending:
            self.source.pop(PENDING, None)
        said = [self.t("plan_paste_done", n=len(result["added"]))]
        left = sum(result["left_out"].values())
        if left:
            said.append(self.t("plan_paste_left_out", n=left))
        if result["outline_replaced"]:
            said.append(self.t("plan_paste_outline_replaced"))
        if not plan_clip.ratio(clip, self.canvas.per_m()) == 1.0:
            said.append(self.t("plan_paste_scaled"))
        if result["axes_renamed"]:
            self.on_axes_renamed(result["axes_renamed"])
        return result["added"], said

    def select_pasted(self, selection):
        self.canvas.set_selected(selection)

    def on_axes_renamed(self, renames):
        """Says which axes a new one moved up -- a name the engineer may have quoted in a calc-block's axes."""
        axis = self.canvas.selected_axis()
        names = ", ".join(f"{old} → {new}" for old, new in renames)
        self.app.set_status(self.t("plan_axes_renamed", label=axis["label"] if axis else "?", names=names))

    def set_subtype(self, subtype):
        element = self.canvas.selected_element()
        if element is None or subtype == element.get("subtype"):
            return

        def apply():
            element["subtype"] = subtype
            kind_before = "point" if len(element["points"]) == 1 else "line"
            if element["type"] == "L":
                # a point load and a line load are not drawn with the same points: keep the first, and give a line a second one beside it
                if subtype == "punkt" and kind_before == "line":
                    element["points"] = element["points"][:1]
                elif subtype == "linie" and kind_before == "point":
                    x, y = element["points"][0]
                    step = 40 * plan_svg.base_unit(model.crop_of(self.source))
                    element["points"] = [[x, y], [round(x + step, 2), y]]
            if element["type"] == "D" and subtype == "scheibe":
                element.pop("diagonal", None)
        self.edit(apply)

    def set_label(self, text):
        """Renumbers the element selected -- to a position of the project, which is all the list offers: another number is not taken. The tool goes on drawing new numbers (issue #9: a number is one object)."""
        element = self.canvas.selected_element()
        label = (text or "").split(" — ")[0].strip()
        if element is None or label == element.get("label", ""):
            return
        if label not in self.position_ids:
            if label:
                self.app.set_status(self.t("plan_number_unknown", label=label))
            return
        self.edit(lambda: element.__setitem__("label", label))

    def set_load_label(self, label):
        """A load symbol's number written over: free text, the plan's own (v0.116). An empty one is not taken."""
        element = self.canvas.selected_element()
        if element is None or not model.is_load(element.get("type")) or not label or label == element.get("label", ""):
            return
        self.edit(lambda: element.__setitem__("label", label))

    def reset_label(self):
        """The selected element's number put back in its own place, where it follows its element again."""
        element = self.canvas.selected_element()
        if element is not None and "label_offset" in element:
            self.edit(lambda: element.pop("label_offset", None))

    def set_span(self, value):
        element = self.canvas.selected_element()
        if element is None:
            return
        if value is None:
            self.edit(lambda: element.pop("span", None))
        else:
            self.edit(lambda: element.__setitem__("span", round(value, 2)))

    def set_angle(self, degrees):
        """The column selected turned to `degrees`, 0 written as no angle at all (a 1.3 plan stays as it was)."""
        element = self.canvas.selected_element()
        if element is None or not model.set_element_angle(dict(element), degrees):
            return
        self.edit(lambda: model.set_element_angle(element, degrees))

    def on_angle_dragged(self, degrees):
        """The circle of the column selected being dragged: its angle field follows, without the pane being built again."""
        spin = getattr(self, "angle_spin", None)
        try:
            if spin is not None:
                spin.blockSignals(True)
                spin.setValue(degrees)
                spin.blockSignals(False)
        except RuntimeError:
            self.angle_spin = None   # the pane was built again since: its field is gone

    def turn_quarter(self):
        element = self.canvas.selected_element()
        if element is not None and model.is_rotatable(element):
            self.set_angle(float(element.get("angle", 0) or 0) + 90.0)
            self.refresh_selection()

    def set_show_length(self, value):
        """The selected element's length shown (True), hidden (False) or as the plan says (None, the field taken out)."""
        element = self.canvas.selected_element()
        if element is None or element.get("show_length") == value and (value is not None or "show_length" not in element):
            return

        def apply():
            if value is None:
                element.pop("show_length", None)
            else:
                element["show_length"] = bool(value)
        self.edit(apply)

    def set_construction(self, mode):
        """The selected bracing wall's construction mode, or none (the field taken out): one step of «Annuler». The tool's own mode, the next wall's, is set in the tool's pane and is not touched (D-021)."""
        element = self.canvas.selected_element()
        if element is None or element.get("construction") == mode:
            return

        def apply():
            if mode is None:
                element.pop("construction", None)
            else:
                element["construction"] = mode
        self.edit(apply)

    def set_element_field(self, key, value):
        element = self.canvas.selected_element()
        if element is not None and element.get(key) != value:
            self.edit(lambda: element.__setitem__(key, value))

    def set_axis_field(self, key, value):
        axis = self.canvas.selected_axis()
        if axis is not None and axis.get(key) != value:
            self.edit(lambda: axis.__setitem__(key, value))
