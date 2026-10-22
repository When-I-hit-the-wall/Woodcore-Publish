"""The position plan's right pane for a drawing tool, and the *Section* of a position -- the rows plan_tab.py builds besides an element's own (issue #9, spec docs/requirements/completed/2026-10-08-plan-positions-cotes-numerotation-sections.md, REQ-006, REQ-007, REQ-008, REQ-015, UI-002, D-011, D-014).

The engineer, 08.10.2026: «À l'activation d'un outil de dessin, afficher tout de suite dans le volet de droite les options de l'objet, comme si un objet déjà dessiné du même type était sélectionné» -- and «Ajouter dans le volet de droite, au-dessus de la position, un champ *Section*. On y choisit le numéro d'une autre position, dont la section est alors reprise … par copie uniquement, sans lien», or the section defined in fields of its type.

Two targets, one set of rows: an **element** selected, whose changes are steps of «Annuler» (`tab.edit`), and a **tool**'s defaults, the canvas's `tool_defaults[type]`, which the next element drawn takes (`plan.apply_defaults`) and which are no step of anything. While a drawing tool is chosen the pane follows the tool; with «Sélection» it follows the selection (D-014). A section chosen for a position the plan draws is kept in the draft (`plan_tab.PENDING`) and written with the plan by «Enregistrer» (D-011).

Its words are plan_tab.py's own STRINGS, which woodcore_gui already reads.
"""

from PySide6.QtWidgets import QCheckBox, QComboBox, QDoubleSpinBox, QLabel, QLineEdit

import plan_centres_card  # a bracing wall's «Mode de construction» (issue #54)
import positions_store
import section_fields
from domains import plan as model
from domains import plan_centres
from domains import section


def section_rows(tab, form, current, on_change, exclude=""):
    """The *Section* rows: «Reprendre de» (another position's section, copied), the section type, its fields and its units -- `current` the section shown ({section_type, dimension, units}), `on_change(new)` called with the whole section whenever the engineer changes it."""
    current = dict(current or {})
    copy = QComboBox()
    copy.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)   # a position's summary does not set the pane's width
    copy.setMinimumContentsLength(12)
    copy.addItem(tab.t("plan_section_copy_none"), "")
    for row in tab.positions:
        found = positions_store.section_of(row)
        if row["position"] != exclude and found and found.get("section_type"):
            copy.addItem(f"{row['position']} — {section.display(row) or found.get('dimension', '')}", row["position"])
    copy.setToolTip(tab.t("plan_section_copy_tip"))
    form.addRow(tab.t("plan_section_copy"), copy)
    kind = QComboBox()
    section_fields.fill_types(kind, tab.app.lang)
    kind.setCurrentIndex(max(0, kind.findData(current.get("section_type", ""))))
    form.addRow(tab.t("plan_section_type"), kind)
    fields = section_fields.DimensionFields(tab.app.lang)
    line = QLineEdit(current.get("dimension", ""))
    form.addRow(fields)
    form.addRow(tab.t("plan_section_dimension"), line)
    units = QComboBox()
    units.setEditable(True)
    for unit in ("mm", "cm", "m"):
        units.addItem(unit)
    units.setCurrentText(current.get("units", "") or "mm")
    form.addRow(tab.t("plan_section_units"), units)

    def show():
        by_fields = fields.set_code(kind.currentData() or "", line.text())
        form.setRowVisible(line, not by_fields)

    def emit():
        on_change({"section_type": kind.currentData() or "", "dimension": line.text().strip(), "units": units.currentText().strip()})

    def typed_in_fields():
        line.setText(fields.text())
        emit()

    def chose_copy(_index):
        pid = copy.currentData()
        row = next((r for r in tab.positions if r["position"] == pid), None)
        found = positions_store.section_of(row) if row else None
        if not found:
            return
        kind.blockSignals(True)
        kind.setCurrentIndex(max(0, kind.findData(found.get("section_type", ""))))
        kind.blockSignals(False)
        line.setText(found.get("dimension", ""))
        units.setCurrentText(found.get("units", "") or "mm")
        show()
        on_change(dict(found))       # a copy, never a link (issue #9)

    def chose_kind(_index):
        # the dimension typed stays as it is: shown in the new type's fields where it reads as one of its forms, on its line otherwise
        show()
        emit()

    copy.activated.connect(chose_copy)
    kind.activated.connect(chose_kind)
    fields.edited.connect(typed_in_fields)
    line.editingFinished.connect(lambda: (show(), emit()))
    units.activated.connect(lambda _i: emit())
    show()
    return copy, kind, fields, line, units


def tool_rows(tab, form, tool):
    """The rows of a drawing tool, as an element of its type has them -- what the next element drawn with it takes (REQ-015): its type, the number it will get, its section, its variant, its angle, its length shown, a bracing wall's construction mode, a slab's span and diagonal. A field that only an element has -- its number moved, a warning, «Supprimer» -- is not here."""
    defaults = tab.canvas.tool_defaults.setdefault(tool, {})
    form.addRow(tab.t("plan_type"), QLabel(tab.t(f"plan_type_{tool}")))
    form.addRow(tab.note(tab.t("plan_tool_defaults_note")))
    if model.is_load(tool) or model.labelled(tool):
        form.addRow(tab.t("plan_next_number"), QLabel(tab.propose_label(tool) or "—"))
    if model.labelled(tool) and not model.is_load(tool):
        type_name = positions_store.type_for(tool)
        proposed = defaults.get("section") or positions_store.last_section_of_type(list(tab.positions) + tab.pending_rows(), type_name) or {}
        section_rows(tab, form, proposed, lambda new: defaults.__setitem__("section", new))
    subtypes = model.TYPES[tool].get("subtypes")
    if subtypes:
        combo = QComboBox()
        for subtype in subtypes:
            combo.addItem(tab.t(f"plan_sub_{subtype}"), subtype)
        combo.setCurrentIndex(max(0, combo.findData(tab.canvas.subtypes.get(tool) or defaults.get("subtype"))))

        def chose(_i, combo=combo):
            defaults["subtype"] = combo.currentData()
            tab.canvas.subtypes[tool] = combo.currentData()
            tab.subtype_combo.setCurrentIndex(max(0, tab.subtype_combo.findData(combo.currentData())))
        combo.activated.connect(chose)
        form.addRow(tab.t("plan_subtype"), combo)
    if tool in model.ROTATABLE or tool == "PL":
        angle = QDoubleSpinBox()
        angle.setRange(-180, 180)
        angle.setDecimals(1)
        angle.setSuffix("°")
        angle.setValue(float(defaults.get("angle", 0) or 0))
        angle.editingFinished.connect(lambda angle=angle: defaults.__setitem__("angle", round(angle.value(), 2)))
        form.addRow(tab.t("plan_element_angle"), angle)
    if tool in model.LENGTH_TYPES:
        length = QComboBox()
        for text, value in ((tab.t("plan_length_follow"), None), (tab.t("plan_length_on"), True), (tab.t("plan_length_off"), False)):
            length.addItem(text, value)
        length.setCurrentIndex(max(0, length.findData(defaults.get("show_length"))))
        length.activated.connect(lambda _i, length=length: defaults.__setitem__("show_length", length.currentData()) if length.currentData() is not None else defaults.pop("show_length", None))
        form.addRow(tab.t("plan_element_length"), length)
    if tool in plan_centres.WALL_TYPES:
        # the mode the next bracing wall takes (issue #54): «non défini» until one is chosen -- no default --, kept for the walls after it while the session lasts
        form.addRow(tab.t("plan_construction"), plan_centres_card.construction_combo(
            tab, defaults.get("construction"), lambda mode: defaults.__setitem__("construction", mode) if mode is not None else defaults.pop("construction", None)))
    if tool == "D":
        diagonal = QCheckBox(tab.t("plan_diagonal"))
        diagonal.setChecked(bool(defaults.get("diagonal", 0)))
        diagonal.toggled.connect(lambda checked: defaults.__setitem__("diagonal", 1 if checked else 0))
        form.addRow("", diagonal)


def element_section_rows(tab, form, element):
    """The *Section* of the position an element carries, above its number (UI-002): its section as the project holds it, or as chosen since and not yet saved -- a change kept in the draft, a step of «Annuler», written with the plan (D-011)."""
    label = element.get("label", "")
    if not label or model.is_load(element["type"]) or not model.labelled(element["type"]):
        return
    pending = tab.pending_positions().get(label)
    row = tab.position_by_id.get(label)
    current = {key: value for key, value in (pending or {}).items() if key in positions_store.SECTION_KEYS} or positions_store.section_of(row) or {}

    def change(new):
        def apply():
            entry = tab.source.setdefault(tab.PENDING_KEY, {}).setdefault(label, {"type": positions_store.type_for(element["type"])})
            entry.update(new)
        tab.edit(apply)
    section_rows(tab, form, current, change, exclude=label)


def dimension_rows(tab, form, dim):
    """A dimension selected: its kind and what it measures -- computed from its points and the plan's scale, never typed --, or why it is not drawn. Its line is moved on the plan itself, by dragging it."""
    form.addRow(tab.t("plan_dim_kind"), QLabel(tab.t(f"plan_dim_kind_{dim['kind']}")))
    parts = model.dimension_parts(tab.source, dim)
    if parts:
        form.addRow(tab.t("plan_dim_values"), QLabel(" + ".join(model.dimension_value_text(part) for part in parts)))
    else:
        form.addRow(tab.note(tab.t("plan_dim_no_scale")))
