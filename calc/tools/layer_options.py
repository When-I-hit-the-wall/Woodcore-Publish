"""«Couche n», the options of the line open in the table of layers (spec docs/requirements/completed/2026-10-24-poids-propre-repense.md, UI-002, T54, P08; issue #111): a module of the right pane, given by the table's service (layer_table.LayerTable) and written by it alone.

What it shows of the layer: its material's card -- its name, its category, its weight and where it is read --, its pose (continuous, spaced, per surface; a load typed is made by «+ Charge saisie»), «Remplir» on a line that shares its level with pieces, g_k | a_k, its role (dead_load_layers.ROLES, optional), «Lier à la ligne du dessous», its load and the formula it is computed by, «Remplacer» and «Rétablir». Each change is said by `changed(key, value)`; the table applies it to its layer and computes again. Nothing is weighed here: the formula is the domain's (`dead_load_layers.formula`, carried by the row). The thickness, the width and the spacing are typed in the table, each with its button of variable.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QCheckBox, QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

import richtext
import theme
import validation
from domains import dead_load_layers, materials_catalogue, materials_contract, materials_user
from tab_host import _n

# The poses the pane offers: a load typed is a line of its own, made by «+ Charge saisie» (T54)
POSES = ("continuous", "spaced", "surface")


def material_card(material_id, lang, t):
    """The words of a material's card: its name, its category, its weight and its source -- «—» where the id names none Woodcore or the engineer has."""
    found = materials_catalogue.find(material_id) if material_id else None
    if found is None and material_id:
        try:
            found = materials_user.find(material_id)
        except validation.ValidationError:   # a library that cannot be read is the «Matériaux» tab's to say
            found = None
    if found is None:
        return "—"
    weight = found.get("weight") or {}
    parts = [materials_contract.name(found, lang), t("mat_cat_" + found["category"]) if found.get("category") else ""]
    if weight:
        parts.append("%s %s" % (_n(weight["value"]), weight["unit"]))
    ref = (found.get("source") or {}).get("ref") or weight.get("ref") or ""
    return " · ".join(p for p in parts if p) + (("<br><span style='color:%s'>%s</span>" % (theme.colour("muted"), richtext.escape(ref))) if ref else "")


class LayerOptions(QWidget):
    """The options of one layer -- see the module's docstring. `show_layer(None)` says that no line is open."""

    changed = Signal(str, object)     # (key of the layer, its new value): pose, fill, kind, role, link, load
    openMaterials = Signal()

    def __init__(self, t, lang):
        super().__init__()
        self.t, self.lang = t, lang
        self.filling = False
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(6)
        self.heading = QLabel()
        self.heading.setTextFormat(Qt.TextFormat.RichText)
        column.addWidget(self.heading)
        self.card = QLabel()
        self.card.setTextFormat(Qt.TextFormat.RichText)
        self.card.setWordWrap(True)
        column.addWidget(self.card)
        link = QLabel("<a href='#'>%s</a>" % richtext.escape(t("ld_materials_link")))
        link.linkActivated.connect(lambda _href: self.openMaterials.emit())
        column.addWidget(link)
        row = QHBoxLayout()
        self.poses = QButtonGroup(self)
        for i, pose in enumerate(POSES):
            button = QPushButton(t("ld_pose_" + pose))
            button.setCheckable(True)
            self.poses.addButton(button, i)
            row.addWidget(button)
        self.poses.idClicked.connect(lambda i: self._say("pose", POSES[i]))
        column.addLayout(row)
        self.fill = QCheckBox(t("ld_opt_fill"))
        self.fill.setToolTip(t("ld_opt_fill_tip"))
        self.fill.toggled.connect(lambda on: self._say("fill", on))
        column.addWidget(self.fill)
        row = QHBoxLayout()
        self.kinds = QButtonGroup(self)
        for i, kind in enumerate(("gk", "ak")):
            button = QPushButton(t("ld_kind_" + kind))
            button.setCheckable(True)
            self.kinds.addButton(button, i)
            row.addWidget(button)
        self.kinds.idClicked.connect(lambda i: self._say("kind", ("gk", "ak")[i]))
        column.addLayout(row)
        row = QHBoxLayout()
        row.addWidget(QLabel(t("ld_opt_role")))
        self.role = QComboBox()
        self.role.addItem(t("ld_role_none"), None)
        for role in dead_load_layers.ROLES:
            self.role.addItem(t("ld_role_" + role), role)
        self.role.currentIndexChanged.connect(lambda _i: self._say("role", self.role.currentData()))
        row.addWidget(self.role, 1)
        column.addLayout(row)
        self.link = QCheckBox(t("ld_opt_link"))
        self.link.toggled.connect(lambda on: self._say("link", on))
        column.addWidget(self.link)
        self.load = QLabel()
        self.load.setTextFormat(Qt.TextFormat.RichText)
        self.load.setWordWrap(True)
        column.addWidget(self.load)
        row = QHBoxLayout()
        self.replace = QPushButton(t("ld_opt_replace"))
        self.replace.clicked.connect(lambda: self._say("load", self.computed))
        self.restore = QPushButton(t("ld_opt_restore"))
        self.restore.clicked.connect(lambda: self._say("load", None))
        row.addWidget(self.replace)
        row.addWidget(self.restore)
        row.addStretch(1)
        column.addLayout(row)
        column.addStretch(1)
        self.computed = None
        self.show_layer(None)

    def _say(self, key, value):
        if not self.filling:
            self.changed.emit(key, value)

    def show_layer(self, number, layer=None, row=None, beside_pieces=False):
        """The options of the layer `layer`, line `number` (from 1), `row` its line of the domain (its formula, its load computed); None: no line open."""
        self.filling = True
        try:
            open_ = layer is not None
            for widget in (self.card, self.fill, self.role, self.link, self.load, self.replace, self.restore) + tuple(self.poses.buttons()) + tuple(self.kinds.buttons()):
                widget.setVisible(open_)
            if not open_:
                self.heading.setText("<i>%s</i>" % richtext.escape(self.t("ld_opt_none")))
                return
            self.heading.setText("<b>%s</b>" % richtext.escape(self.t("ld_module_layer_n", n=number)))
            typed = layer.get("pose") == "typed"
            self.card.setText(richtext.escape(layer.get("label") or "") if typed else material_card(layer.get("material"), self.lang, self.t))
            for i, pose in enumerate(POSES):
                self.poses.button(i).setChecked(layer.get("pose") == pose)
                self.poses.button(i).setVisible(not typed)
            self.kinds.button(0).setChecked(layer.get("kind") == "gk")
            self.kinds.button(1).setChecked(layer.get("kind") == "ak")
            self.fill.setVisible(beside_pieces and layer.get("pose") != "spaced" and not typed)
            self.fill.setChecked(layer.get("fill", True))
            self.role.setCurrentIndex(max(self.role.findData(layer.get("role")), 0))
            self.link.setChecked(bool(layer.get("link")))
            self.computed = round(row["computed"], 3) if row and row.get("computed") is not None else None
            formula = (row or {}).get("formula") or ""
            replaced = layer.get("load") is not None and not typed
            words = [self.t("ld_opt_load", value=_n(layer["load"]) if layer.get("load") is not None else (_n(self.computed) if self.computed is not None else "—"))]
            if formula:
                words.append("<span style='color:%s'>%s</span>" % (theme.colour("muted"), richtext.escape(formula)))
            if replaced:
                words.insert(0, "<span style='color:%s'>%s</span>" % (theme.colour("warning"), richtext.escape(self.t("ld_opt_replaced"))))
            self.load.setText("<br>".join(words))
            self.replace.setVisible(not typed and not replaced and self.computed is not None)
            self.restore.setVisible(replaced)
        finally:
            self.filling = False
