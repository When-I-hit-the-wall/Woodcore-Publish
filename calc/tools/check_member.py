"""The head «Élément» of a member check, a service (spec docs/requirements/completed/2026-10-24-verifications-elements-v3.md, UI-004, UI-005, REQ-013; issue #112).

What the check is about, above the forces its domain declares: the position (a list), **the material** of the library -- a bubble whose click opens its menu under it (material_menu.MaterialMenu: the classes of SIA 265, the panels of SIA 265/1, the engineer's own, the materials without resistance greyed) -- and **the section**, each **following the position** (grey, «C24 — T001») or **written over** (orange, «Reprendre» taking it back). The rows «Sollicitation» and «Facteurs» are services of their own under it (load_row.LoadRow, factors_row.FactorsRow).

It contributes the draft's `position`, `material` (absent to follow), `grade` (a class of before kept until another is chosen) and `section` (`fill`, `collect`), and says again what the draft resolves to once the domain has computed it (phase `computed`). Every value and every rule is the domain's; the words are the tab's (`vc_`).
"""

from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

import cards
import richtext
import theme
from check_rows import decimal, material_of
from domains import member_check_material as mm
from material_menu import MaterialMenu
from tab_host import Service

FOLLOW = "__follow__"


class CheckMember(Service):
    """The head «Élément» -- see the module's docstring."""

    NAME = "member"
    ZONE = "centre"
    NEEDS = ("record",)

    def mount(self, ctx):
        super().mount(ctx)
        t = self.t
        self.tab = ctx.module.TAB
        self.material_id, self.grade = None, None
        self.record = {}
        self.box = cards.card(t("vc_box_member"))
        column = QVBoxLayout(self.box)
        column.setContentsMargins(10, 8, 10, 8)
        column.setSpacing(6)
        holder = QWidget()
        form = cards.form(holder)
        column.addWidget(holder)
        self.form = form
        # the position
        self.position = QComboBox()
        self.position.currentIndexChanged.connect(self._touched)
        form.addRow(t("vc_position"), self.position)
        # the material, its bubble and its menu
        row = QHBoxLayout()
        self.material_button = QPushButton("")
        self.material_button.setCheckable(True)
        self.material_button.setToolTip(t("vc_material_tip"))
        self.material_button.toggled.connect(self._toggle_menu)
        self.material_back = QPushButton(t("vc_take_back"))
        self.material_back.clicked.connect(lambda: self._choose(None))
        row.addWidget(self.material_button, 1)
        row.addWidget(self.material_back)
        material_line = QWidget()
        material_line.setLayout(row)
        form.addRow(t("vc_material"), material_line)
        self.menu = MaterialMenu(self._menu_entries, t("vc_menu_search"))
        self.menu.chosen.connect(self._choose)
        self.menu.setVisible(False)
        form.addRow(self.menu)
        # the section
        section_line = QWidget()
        srow = QHBoxLayout(section_line)
        srow.setContentsMargins(0, 0, 0, 0)
        self.section_type = QComboBox()
        self.section_type.addItem("", FOLLOW)
        self.section_type.addItem(t("vc_rec"), "rec")
        self.section_type.addItem(t("vc_cir"), "cir")
        self.section_type.currentIndexChanged.connect(self._section_changed)
        self.spins = {}
        srow.addWidget(self.section_type)
        for side in ("b", "h", "d"):
            spin = QDoubleSpinBox()
            spin.setRange(1.0, 100000.0)
            spin.setDecimals(1)
            spin.setSingleStep(10.0)
            spin.setSuffix(" mm")
            spin.setValue(100.0 if side != "h" else 200.0)
            spin.valueChanged.connect(self._touched)
            self.spins[side] = spin
            label = QLabel(side)
            srow.addWidget(label)
            srow.addWidget(ctx.links.linked(spin, "section." + side, "mm", side))
            spin.setProperty("side_label", label)
        self.section_back = QPushButton(t("vc_take_back"))
        self.section_back.clicked.connect(lambda: self.section_type.setCurrentIndex(0))
        srow.addWidget(self.section_back)
        srow.addStretch(1)
        form.addRow(t("vc_section"), section_line)
        return self.box

    def _touched(self, *_ignored):
        if not self.ctx.loading:
            self.ctx.touch()

    # --- the menu ---------------------------------------------------------------------------

    def _toggle_menu(self, on):
        self.menu.setVisible(on)
        if on:
            self.menu.refresh()
            self.menu.search.setFocus()

    def _menu_entries(self, query):
        from domains import materials_library
        lang = self.app.lang
        materials, _error = materials_library.entries()
        head = None
        pid = self.record.get("position")
        position_grade = self.ctx.module.position_grade(pid) if pid else None
        if position_grade:
            head = self.t("vc_menu_follow", material=position_grade, position=pid)
        groups = []
        for group, entries in mm.offered(self.tab, materials, query, lang):
            rows = []
            for e in entries:
                if e["lacks"]:
                    detail = self.t("vc_menu_lacks") if e["selectable"] else ""
                elif e["values"] and e["values"][0][0] is not None:
                    detail = " · ".join("%s %s" % (self.t("vc_abbr_%s_%s" % loading), decimal(value, lang)) for loading, value in e["values"] if value is not None)
                elif e["values"]:
                    detail = "%s %s" % (richtext.plain_math(self.t("vc_quantity_" + mm.TAB_QUANTITY[self.tab])), decimal(e["values"][0][1], lang))
                else:
                    detail = ""
                source = {"sia265": "SIA 265", "sia265-1": "SIA 265/1"}.get(e["source"], self.t("vc_src_user") if e["source"] == "user" else "")
                rows.append({"id": e["id"], "text": e["name"], "detail": detail, "source": source, "selectable": e["selectable"]})
            groups.append((self.t("vc_group_" + group), rows))
        return head, groups

    def _choose(self, material_id):
        """A material chosen in the menu, or «Reprendre» (None): the draft follows the position again."""
        self.material_button.setChecked(False)
        self.material_id = material_id
        self.grade = None   # a class of before, written as `grade`, gives way to the material chosen -- or to the position, «Reprendre»
        self._touched()

    # --- the section -----------------------------------------------------------------------

    def _section_changed(self, *_ignored):
        kind = self.section_type.currentData()
        for side, spin in self.spins.items():
            shown = (kind == "cir") == (side == "d") and kind != FOLLOW
            self.ctx.links.row_of(spin).setVisible(shown)
            spin.property("side_label").setVisible(shown)
        self.section_back.setVisible(kind != FOLLOW)
        self._touched()

    # --- the contribution to the draft -------------------------------------------------------

    def fill(self, src):
        self.material_id = src.get("material")
        self.grade = src.get("grade")
        self.position.blockSignals(True)
        self.position.clear()
        self.position.addItem(self.t("vc_no_position"), None)
        for pid, rec in sorted(self.ctx.module.positions().items()):
            self.position.addItem("%s · %s" % (pid, rec.get("type_label") or rec.get("strength_class") or ""), pid)
        pid = src.get("position")
        if pid and self.position.findData(pid) < 0:
            self.position.addItem(self.t("vc_position_gone", position=pid), pid)
        self.position.setCurrentIndex(max(self.position.findData(pid), 0))
        self.position.blockSignals(False)
        section = src.get("section")
        if section:
            for side in ("b", "h", "d"):
                if section.get(side):
                    self.spins[side].setValue(float(section[side]))
        self.section_type.setCurrentIndex(max(self.section_type.findData(section["type"] if section else FOLLOW), 0))
        self._section_changed()
        self.record = self.ctx.module.record(src) if src else {}
        self.show_record(src)

    def collect(self, src):
        src["position"] = self.position.currentData()
        if self.material_id:
            src["material"] = self.material_id
            src["grade"] = None
        else:
            src.pop("material", None)
            src["grade"] = self.grade
        kind = self.section_type.currentData()
        if kind == "rec":
            src["section"] = {"type": "rec", "b": self.spins["b"].value(), "h": self.spins["h"].value()}
        elif kind == "cir":
            src["section"] = {"type": "cir", "d": self.spins["d"].value()}
        else:
            src["section"] = None

    # --- the phase `computed`: what the draft resolves to ----------------------------------------

    def computed(self):
        src = self.ctx.computed_source
        self.record = self.ctx.module.record(src) if src else {}
        self.show_record(src)

    def show_record(self, src):
        """The bubbles grey where they follow the position, orange where written over (UI-004)."""
        t, lang, record = self.t, self.app.lang, self.record
        override, muted = theme.colour("override"), theme.colour("muted")
        material = material_of(src, record)
        pid = record.get("position")
        stated = bool(self.material_id or self.grade)
        name = mm.short_name(material, lang) if material else (record.get("grade") or t("vc_no_material"))
        loading = (src or {}).get("loading")
        if material and material.get("type") == "panel" and loading:
            name += " " + t("vc_load_%s_%s" % (loading["mode"], loading["direction"]))
        if stated:
            self.material_button.setText(name)
            self.material_button.setStyleSheet("color: %s; font-weight: 600;" % override)
        else:
            self.material_button.setText(cards.followed(name, pid) if pid and material else name)
            self.material_button.setStyleSheet("color: %s;" % muted)
        self.material_back.setVisible(stated)
        section = record.get("section")
        follow_text = cards.followed((section or {}).get("text", ""), pid) if pid else t("vc_section_none")
        self.section_type.setItemText(0, follow_text)
        self.section_type.setStyleSheet("" if self.section_type.currentData() == FOLLOW else "color: %s;" % override)
