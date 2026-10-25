"""The table of the layers of a build-up, a service in place of the declared form (spec docs/requirements/completed/2026-10-23-onglets-types-et-services.md, REQ-003; redrawn by issue #111, spec docs/requirements/completed/2026-10-24-poids-propre-repense.md, UI-001, UI-002, T47 to T52, P08).

«Poids propre et surcharge» takes it on the type «Calcul» (`calc_tab.swap`). **One compact line a layer** (`ROW_HEIGHT`), its columns layer_cells.COLUMNS -- n°, Matériau, Ép., Entraxe, Largeur, g/a, kN/m² --: the material typed into its cell, the list proposing every material with a weight -- Woodcore's and the engineer's own, the «Matériaux» tab's -- the category the words name first (`materials_search.ranked`), each with its category, its weight and its origin; a name no material carries stays written, and the line says so in red. **The keyboard** (layer_cells.next_cell): Tab from the material to the thickness, the spacing, the width, g/a, then the kN/m², a cell that does not serve the line's pose greyed and skipped, after the last cell the material of the next line; g/a by ↑ ↓ or Space; Escape closes the line. The width a line fills between pieces is shown in italics, computed; the kN/m² shows the load computed, and a load typed there replaces it (orange). Under the table «+ Couche», «+ Charge saisie», «Retirer», «Monter», «Descendre», «Enregistrer comme modèle» and the sum; then the retained value, «auto» the tenth above the sum.

**A line open** -- clicked, or a cell of it given the focus -- shows its options in «Couche n» (layer_options.LayerOptions), a module this service gives the right pane (`ctx.pane_modules`); a message about a line, clicked, opens it (`focus`). «Lier à la ligne du dessous» on the last line makes the next one, the cursor in its material (T29). The tab creates no material: the link «Les matériaux se créent dans l'onglet Matériaux» opens that tab.

The layers are this service's model (`self.layers`, dead-load-source 2.0; a build-up of before is read as 2.0 and written at 2.0); each of a layer's four numbers may follow a variable of the export, its link the layer's own, carried by its cell (the context's linkable numbers, `store=False`); the retained value is linked like a field. It contributes the build-up to the draft (`fill`, `collect`). Its words are its tab's (`ld_`). What it shows of the calculation -- a load computed, a width filled, a formula -- is the domain's (`rows(src, here)`), read in the phase `computed`.
"""

import copy

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QDoubleSpinBox, QHBoxLayout, QHeaderView, QInputDialog, QLabel, QLineEdit, QPushButton,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

import cards
import layer_cells
import layer_options
import module_pane
import project
import richtext
import theme
import validation
from domains import dead_load_layers, dead_load_source, links, materials, materials_catalogue, materials_contract, materials_search, materials_user
from tab_host import Service, _n

# The words of a material's origin beside its name, the norms' own names written as they are
ORIGIN_TAGS = {"sia265": "SIA 265", "sia265-1": "SIA 265/1", "sia261": "SIA 261"}
LAYER_COLUMNS = layer_cells.COLUMNS
ROW_HEIGHT = 26            # a line, compact (T7, T47)
NUMBERS = {"thickness": ("mm", 100_000.0, 1), "spacing": ("mm", 100_000.0, 1), "width": ("mm", 100_000.0, 1), "load": ("kN/m²", 1000.0, 3)}


class MaterialCombo(QComboBox):
    """The material of a layer, chosen in a list typed into: the words typed keep the materials they find, the category they name first (`materials_search.ranked`), the list shown under the field; leaving it puts back the name of the material chosen -- or keeps a name no material carries (`unknown`)."""

    def __init__(self, entries, wanted):
        super().__init__()
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.entries = list(entries)      # [(text, material)]
        self.unknown = None
        self._fill(self.entries, wanted)
        self.lineEdit().textEdited.connect(self.search)

    def _fill(self, entries, wanted):
        self.blockSignals(True)
        self.clear()
        self.materials = []
        for text, material in entries:
            self.addItem(text, (material["id"], ""))
            self.materials.append(material)
        index = self.index_of(wanted)
        if index < 0 and wanted:
            self.addItem("%s (?)" % wanted, (wanted, ""))      # a material no list holds any more is kept, and the result says why
            self.materials.append({"id": wanted, "names": {}})
            index = self.count() - 1
        self.setCurrentIndex(max(index, 0))
        self.blockSignals(False)

    def index_of(self, material_id):
        """The row of a material by its id, -1 for none."""
        return next((i for i, m in enumerate(self.materials) if m["id"] == material_id), -1)

    def current_id(self):
        return (self.currentData() or ("", ""))[0] or None

    def search(self, text):
        """The list kept to what the words find, the category they name first (T48)."""
        chosen = self.current_id()
        found = materials_search.ranked([m for _t, m in self.entries], text)
        by_id = {m["id"]: t for t, m in self.entries}
        self._fill([(by_id[m["id"]], m) for m in found] if text.strip() else self.entries, chosen)
        self.lineEdit().setText(text)
        if text.strip():
            self.showPopup()

    def settle(self):
        """The field left: the name of the material chosen put back -- or, where the words find none, the words kept (`unknown`, T48)."""
        text = self.lineEdit().text().strip()
        if text and text != self.itemText(self.currentIndex()) and not materials_search.ranked([m for _t, m in self.entries], text):
            self.unknown = text
            return
        self.unknown = None
        self.setEditText(self.itemText(self.currentIndex()))


def spin(minimum, maximum, decimals=1, step=1.0, suffix=""):
    box = QDoubleSpinBox()
    box.setRange(minimum, maximum)
    box.setDecimals(decimals)
    box.setSingleStep(step)
    box.setSuffix(suffix)
    box.setMinimumWidth(64)
    box.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
    return box


class _Keys(QObject):
    """The keyboard of the table (T50): Tab and Shift+Tab by `layer_cells.next_cell`, Space on g/a, Enter on the material, Escape closing the line; a cell given the focus opens its line."""

    def __init__(self, table):
        super().__init__()
        self.table = table

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            at = self.table.cell_of.get(obj)
            if at is not None:
                key = event.key()
                if key in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
                    self.table.tab_from(at, key == Qt.Key.Key_Tab and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier))
                    return True
                if key == Qt.Key.Key_Escape:
                    self.table.close_row()
                    return True
                if key == Qt.Key.Key_Space and at[1] == "kind":
                    combo = self.table.cell(at[0], "kind")
                    combo.setCurrentIndex(1 - combo.currentIndex())
                    return True
                if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and at[1] == "material":
                    self.table.tab_from(at, True)
                    return True
        elif event.type() == QEvent.Type.FocusIn:
            at = self.table.cell_of.get(obj)
            if at is not None and at[0] != self.table.open:
                self.table.open_row(at[0])
        return False


class LayerTable(Service):
    """The layers of a build-up and its retained value -- see the module's docstring."""

    NAME = "layers"
    ZONE = "centre"
    NEEDS = ("rows", "save_template")

    def mount(self, ctx):
        super().mount(ctx)
        self.layers, self.shown, self.open, self.bodies = [], [], None, []
        self.cell_of, self.widgets = {}, []
        self.keys = _Keys(self)
        holder = QWidget()
        outer = QVBoxLayout(holder)
        outer.setContentsMargins(0, 0, 0, 0)
        box = cards.card(self.t("ld_box_layers"))
        column = QVBoxLayout(box)
        self.table = QTableWidget(0, len(LAYER_COLUMNS))
        self.table.setHorizontalHeaderLabels([self.t("ld_col_" + c) for c in LAYER_COLUMNS])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(LAYER_COLUMNS.index("material"), QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setMinimumHeight(180)
        self.table.cellClicked.connect(self.clicked)
        column.addWidget(self.table)
        row = QHBoxLayout()
        for key, slot in (("ld_add_layer", self.add_layer), ("ld_add_typed", self.add_typed), ("ld_remove", self.remove_layer),
                          ("ld_up", lambda: self.move_layer(-1)), ("ld_down", lambda: self.move_layer(1))):
            button = QPushButton(self.t(key))
            button.clicked.connect(slot)
            row.addWidget(button)
        row.addStretch(1)
        self.sum = QLabel()
        self.sum.setTextFormat(Qt.TextFormat.RichText)
        row.addWidget(self.sum)
        column.addLayout(row)
        row = QHBoxLayout()
        link = QLabel("<a href='#'>%s</a>" % richtext.escape(self.t("ld_materials_link")))
        link.linkActivated.connect(lambda _href: self.open_materials())
        row.addWidget(link)
        row.addStretch(1)
        save = QPushButton(self.t("ld_save_template"))
        save.clicked.connect(self.ask_template)
        row.addWidget(save)
        column.addLayout(row)
        column.addWidget(cards.note(self.t("ld_layers_hint")))
        outer.addWidget(box)
        box = cards.card(self.t("ld_box_chosen"))
        form = cards.form(box)
        self.chosen_spin = spin(0.0, 1000.0, 3, 0.05, " kN/m²")
        self.chosen_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
        self.chosen_spin.setSpecialValueText(self.t("ld_chosen_sum"))
        self.chosen_spin.valueChanged.connect(ctx.touch)
        form.addRow(self.t("ld_chosen"), ctx.links.linked(self.chosen_spin, "chosen", "kN/m²", "g_k+a_k"))
        outer.addWidget(box)
        ctx.focusRequested.connect(self.focus)
        # «Couche n», the options of the line open (UI-002): a module of the right pane, given before the pane mounts
        ctx.pane_modules.append(module_pane.ModuleSpec("layer", self.t("ld_module_layer"), self.options_body, kind="layer"))
        return holder

    # --- the contribution to the draft ----------------------------------------------------

    def fill(self, src):
        try:
            src = dead_load_source.upgraded(src)          # a build-up of before shown as 2.0, written at 2.0 by the next save
        except validation.ValidationError:
            src = dict(src, layers=[])                    # a level the rule of two refuses: the check says it in red
        self.layers = copy.deepcopy(src.get("layers") or [])
        self.open = None
        self.rebuild()
        self.chosen_spin.setValue(float(src.get("chosen") or 0))

    def collect(self, src):
        src["layers"] = self.current_layers()
        src["chosen"] = self.chosen_spin.value() or None

    def current_layers(self):
        """The layers as the table holds them, each one's links read off its cells."""
        out = []
        for row, layer in enumerate(self.layers):
            layer = {k: v for k, v in layer.items() if k != links.LINKS}
            found = {}
            for key in NUMBERS:
                cell = self.cell(row, key) if row < len(self.widgets) else None
                if cell is not None and hasattr(cell, "link") and cell.link() is not None:
                    found[key] = cell.link()
            if found:
                layer[links.LINKS] = found
            out.append(layer)
        return out

    # --- the lines --------------------------------------------------------------------

    def cell(self, row, column):
        return self.widgets[row].get(column)

    def rebuild(self):
        """Every line made again from the layers: what a change of the build-up's shape does (a line added, moved, its pose or its link changed)."""
        was, self.ctx.loading = self.ctx.loading, True
        try:
            self.cell_of = {}
            self.widgets = []
            self.table.setRowCount(len(self.layers))
            for row, layer in enumerate(self.layers):
                self.widgets.append(self._make_row(row, layer))
        finally:
            self.ctx.loading = was
        self.show_computed()

    def _make_row(self, row, layer):
        cells = {}
        number = QTableWidgetItem(str(row + 1))
        number.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        number.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 0, number)
        if layer.get("pose") == "typed":
            material = QLineEdit(layer.get("label") or "")
            material.setPlaceholderText(self.t("ld_typed_placeholder"))
            material.textEdited.connect(lambda text, r=row: self._set(r, "label", text))
            focusable = material
        else:
            material = MaterialCombo(self._weighed(), layer.get("material") or "")
            if layer.get("material") is None and layer.get("label"):
                material.setEditText(layer["label"])
            material.setMinimumContentsLength(16)
            material.view().setMinimumWidth(460)
            material.currentIndexChanged.connect(lambda _i, r=row, c=material: self._material_chosen(r, c))
            material.lineEdit().editingFinished.connect(lambda r=row, c=material: self._material_left(r, c))
            focusable = material.lineEdit()
        cells["material"] = material
        self._watch(material, row, "material", focusable)
        found = links.links_of(layer)
        for key, (unit, maximum, decimals) in NUMBERS.items():
            box = spin(0.0, maximum, decimals)
            box.setSpecialValueText(" ")
            value = layer.get(key)
            if key == "width" and layer.get("pose") != "spaced" and layer.get("fill", True):
                value = None
            box.setValue(float(value or 0))
            box.valueChanged.connect(lambda v, r=row, k=key: self._number(r, k, v))
            linked = self.ctx.links.linked(box, key, unit, self.t("ld_col_" + key), store=False)
            linked.set_link(found.get(key), self.ctx.links.values() if found else {})
            cells[key] = linked
            self._watch(linked, row, key, box, box.lineEdit())
        kind = QComboBox()
        for k in ("gk", "ak"):
            kind.addItem(self.t("ld_kind_" + k), k)
        kind.setCurrentIndex(max(kind.findData(layer.get("kind")), 0))
        kind.currentIndexChanged.connect(lambda _i, r=row, c=kind: self._set(r, "kind", c.currentData()))
        cells["kind"] = kind
        self._watch(kind, row, "kind")
        for column, name in enumerate(LAYER_COLUMNS):
            if name in cells:
                self.table.setCellWidget(row, column, cells[name])
                cells[name].setEnabled(layer_cells.used(self.layers, row, name))
        return cells

    def _watch(self, widget, row, column, *focusables):
        for w in (widget,) + focusables:
            if w is None:
                continue
            self.cell_of[w] = (row, column)
            w.installEventFilter(self.keys)

    def _set(self, row, key, value, rebuild=False):
        if self.ctx.loading or row >= len(self.layers):
            return
        self.layers[row][key] = value
        if rebuild:
            self.rebuild()
        self.ctx.touch()

    def _number(self, row, key, value):
        if self.ctx.loading:
            return
        self._set(row, key, value or None)

    def _material_chosen(self, row, combo):
        """A material chosen: its id written, its pose following its unit (T40) -- per m² makes the line «surface», per m³ on a «surface» line makes it continuous again."""
        if self.ctx.loading:
            return
        layer = self.layers[row]
        layer["material"], layer["label"] = combo.current_id(), ""
        try:
            unit = materials.weight_of(layer["material"], None)[1] if layer["material"] else None
        except validation.ValidationError:
            unit = None
        pose = dead_load_layers.pose_for(unit, layer) if unit else layer.get("pose")
        if pose != layer.get("pose"):
            layer["pose"] = pose
            if pose != "spaced":
                layer["spacing"] = None
            self.rebuild()
            self.focus_cell(row, "material")
        self.ctx.touch()

    def _material_left(self, row, combo):
        combo.settle()
        if combo.unknown is not None and row < len(self.layers):
            self.layers[row]["material"], self.layers[row]["label"] = None, combo.unknown   # a name no material carries, kept; the line says it in red (T48)
            self.ctx.touch()

    # --- the keyboard and the line open -------------------------------------------------

    def tab_from(self, at, forward):
        """Tab (`forward`) or Shift+Tab from the cell `at` = (row, column) (T50)."""
        target = layer_cells.next_cell(self.layers, at[0], at[1], forward)
        if target is not None:
            self.focus_cell(*target)

    def focus_cell(self, row, column):
        cell = self.cell(row, column)
        if cell is None:
            return
        self.open_row(row)
        self.table.setCurrentCell(row, LAYER_COLUMNS.index(column))
        inner = getattr(cell, "spin", cell)
        inner.setFocus(Qt.FocusReason.TabFocusReason)
        edit = inner if isinstance(inner, QLineEdit) else (inner.lineEdit() if hasattr(inner, "lineEdit") else None)
        if edit is not None:
            edit.selectAll()

    def clicked(self, row, _column):
        """A click on a line's number: the line opened, the material's name selected (T26, T49) -- a second click closes it."""
        if row == self.open:
            self.close_row()
            return
        self.focus_cell(row, "material")

    def open_row(self, row):
        self.open = row
        self.table.selectRow(row)
        self.show_options()

    def close_row(self):
        """Escape, or a second click: the line closed, the composition kept (T23)."""
        self.open = None
        self.table.clearSelection()
        self.table.setFocus()
        self.show_options()

    def focus(self, field):
        """A message clicked (UI-002): the line it names (`layers[i]`) opened, or the retained value given the focus."""
        if field == "chosen":
            self.chosen_spin.setFocus()
            return
        if field and field.startswith("layers[") and field.endswith("]"):
            row = int(field[len("layers["):-1])
            if 0 <= row < len(self.layers):
                self.focus_cell(row, "material")

    # --- «Couche n» -------------------------------------------------------------------

    def options_body(self):
        body = layer_options.LayerOptions(self.t, self.app.lang)
        body.changed.connect(self.option_changed)
        body.openMaterials.connect(self.open_materials)
        body.refresh = lambda b=body: self._show_in(b)
        self.bodies.append(body)
        self._show_in(body)
        return body

    def show_options(self):
        for body in list(self.bodies):
            try:
                self._show_in(body)
            except RuntimeError:         # a body whose window was closed
                self.bodies.remove(body)

    def _show_in(self, body):
        row = self.open
        if row is None or row >= len(self.layers):
            body.show_layer(None)
            return
        shown = self.shown[row] if row < len(self.shown) else None
        body.show_layer(row + 1, self.layers[row], shown, layer_cells.beside_pieces(self.layers, row))

    def option_changed(self, key, value):
        """A change made in «Couche n»: written into the layer open; a pose or a link reshapes the lines; «Lier» on the last line makes the next one, the cursor in its material (T29)."""
        row = self.open
        if row is None or row >= len(self.layers):
            return
        self.layers = self.current_layers()
        layer = self.layers[row]
        layer[key] = value
        if key == "pose" and value != "spaced":
            layer["spacing"] = None
        if key == "fill" and value:
            layer["width"] = None
        made = None
        if key == "link" and value and row == len(self.layers) - 1:
            self.layers.append(dict(dead_load_source.new_layer(), material=None, thickness=None, kind=layer.get("kind", "gk")))
            made = row + 1
        self.rebuild()
        self.ctx.touch()
        if made is not None:
            self.focus_cell(made, "material")
        else:
            self.open_row(row)

    # --- what the domain computed, shown beside the lines -------------------------------

    def computed(self):
        try:
            self.shown = self.ctx.module.rows(self.ctx.computed_source, project.current()) if self.ctx.computed_source else []
        except validation.ValidationError:
            self.shown = []
        self.show_computed()
        self.show_options()

    def show_computed(self):
        """The width a line fills (italic, computed), the load computed in the kN/m² of a line whose load is not typed -- a load typed there orange --, the sum and the retained value."""
        italic = QFont()
        italic.setItalic(True)
        warn = theme.colour("warning")
        for row, layer in enumerate(self.layers):
            if row >= len(self.widgets):
                break
            shown = self.shown[row] if row < len(self.shown) else {}
            width = getattr(self.cell(row, "width"), "spin", self.cell(row, "width"))
            filled = shown.get("fill_width") if layer.get("pose") != "spaced" and layer_cells.fills(self.layers, row) else None
            width.setSpecialValueText(_n(filled) if filled is not None else " ")
            width.setFont(italic if filled is not None else QFont())
            load = getattr(self.cell(row, "load"), "spin", self.cell(row, "load"))
            computed = shown.get("computed")
            load.setSpecialValueText(_n(round(computed, 3)) if computed is not None else " ")
            replaced = layer.get("load") is not None and layer.get("pose") != "typed"
            load.setStyleSheet("color: %s;" % warn if replaced else "")
        loads = [r.get("load") for r in self.shown]
        if self.shown and all(v is not None for v in loads):
            total = sum(loads)
            retained = self.chosen_spin.value() or dead_load_layers.retained(total)
            self.sum.setText(self.t("ld_sum", total=_n(round(total, 3)), retained=_n(retained)))
        else:
            self.sum.setText("")

    # --- the materials a line may name ----------------------------------------------------

    def _weighed(self):
        """Every material a layer may name -- Woodcore's and the engineer's own that have a weight -- as (text, material): its name in the window's language, its category, its weight, its origin (T48)."""
        try:
            mine = [m for m in materials_user.materials() if m.get("weight")]
        except validation.ValidationError:
            mine = []   # a library that cannot be read is the «Matériaux» tab's to say
        out = []
        for m in [m for m in materials_catalogue.catalogue() if m.get("weight")] + mine:
            w = m["weight"]
            tag = ORIGIN_TAGS.get(m.get("origin")) or self.t("ld_src_ext" if m.get("origin") == "ext" else "ld_src_user")
            category = self.t("mat_cat_" + m["category"]) if m.get("category") else ""
            out.append(("%s — %s · %s %s · %s" % (materials_contract.name(m, self.app.lang), category, _n(w["value"]), w["unit"], tag), m))
        return out

    def open_materials(self):
        """The «Matériaux» tab brought forward: materials are made there, never here (T52)."""
        for tab in getattr(self.app, "tabs", ()):
            if getattr(tab, "KEY", "") == "tab_materials" and hasattr(self.app, "tab_widget"):
                self.app.tab_widget.setCurrentWidget(tab)
                return

    # --- the lines added, removed, moved; the build-up kept as a template -----------------

    def add_layer(self):
        self.layers = self.current_layers() + [dict(dead_load_source.new_layer(), material=None, thickness=None)]
        self.rebuild()
        self.ctx.touch()
        self.focus_cell(len(self.layers) - 1, "material")

    def add_typed(self):
        self.layers = self.current_layers() + [{"kind": "ak", "pose": "typed", "material": None, "label": "", "thickness": None, "width": None,
                                                "spacing": None, "link": False, "fill": True, "role": None, "load": None}]
        self.rebuild()
        self.ctx.touch()
        self.focus_cell(len(self.layers) - 1, "material")

    def remove_layer(self):
        row = self.open if self.open is not None else self.table.currentRow()
        if 0 <= row < len(self.layers):
            self.layers = self.current_layers()
            del self.layers[row]
            self.open = None
            self.rebuild()
            self.ctx.touch()

    def move_layer(self, step):
        row = self.open if self.open is not None else self.table.currentRow()
        target = row + step
        if 0 <= row < len(self.layers) and 0 <= target < len(self.layers):
            self.layers = self.current_layers()
            self.layers[row], self.layers[target] = self.layers[target], self.layers[row]
            self.rebuild()
            self.ctx.touch()
            self.open_row(target)

    def ask_template(self):
        words, ok = QInputDialog.getText(self.table, self.t("ld_save_template"), self.t("ld_template_name"), text=self.ctx.draft().get("name") or "")
        if ok:
            self.save_as_template(words)

    def save_as_template(self, words):
        """«Enregistrer comme modèle» (REQ-010, D-08): the build-up kept in the engineer's own templates, on this computer. Returns the template, None where it is refused (said by the tab)."""
        try:
            template = self.ctx.module.save_template(self.ctx.draft(), words, self.app.lang)
        except validation.ValidationError as exc:
            self.ctx.fail(str(exc))
            return None
        status = getattr(self.app, "statusBar", None)
        if callable(status):
            status().showMessage(self.t("ld_template_saved", name=words or template["id"]), 5000)
        return template
