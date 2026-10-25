"""The row «Facteurs» of a member check, a service (spec docs/requirements/completed/2026-10-24-verifications-elements-v3.md, REQ-006, UI-015; issue #112).

Under the row «Sollicitation» (load_row.LoadRow): a member's moisture class (η_w beside each, SIA 265 Tabelle 4) and action (η_t, 2.2.6), its γ_M/η_M shown, never chosen (Tabelle 1); a panel's moisture class (those its product is admitted in, SIA 265/1 Tableau 9), load-duration class (Tableau 8 in its tooltip) and situation, its η_mod and γ_M shown (Tableaux 9 and 6). The first moisture class follows the position.

It contributes the draft's `moisture_class`, `impact`, and a panel's `kled` and `accidental` (`collect`), and redraws itself once the domain has computed the draft (phase `computed`), the material being the draft's (`check_rows.material_of`).
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

import cards
import richtext
from check_rows import decimal, material_of
from domains import member_check_material as mm
from norms import sia265, sia265_1
from tab_host import Service


class FactorsRow(Service):
    """The row «Facteurs» -- see the module's docstring."""

    NAME = "factors"
    ZONE = "centre"
    NEEDS = ("record", "position_moisture")

    def mount(self, ctx):
        super().mount(ctx)
        t = self.t
        self.record = {}
        self.material = None
        self.box = cards.card("")
        column = QVBoxLayout(self.box)
        column.setContentsMargins(10, 6, 10, 6)
        holder = QWidget()
        form = cards.form(holder)
        column.addWidget(holder)
        line = QWidget()
        frow = QHBoxLayout(line)
        frow.setContentsMargins(0, 0, 0, 0)
        frow.setSpacing(6)
        self.moisture = QComboBox()
        self.moisture.currentIndexChanged.connect(self._touched)
        self.action = QComboBox()
        self.action.addItem(t("vc_action_normal", eta=decimal(sia265.eta_t(False), self.app.lang, 1)), False)
        self.action.addItem(t("vc_action_impact", eta=decimal(sia265.eta_t(True), self.app.lang, 1)), True)
        self.action.currentIndexChanged.connect(self._touched)
        self.kled = QComboBox()
        for c in sia265_1.kled_classes():
            self.kled.addItem(t("vc_kled_" + c["id"]), c["id"])
        self.kled.setToolTip(self._kled_tip())
        self.kled.currentIndexChanged.connect(self._touched)
        self.situation = QComboBox()
        self.situation.addItem(t("vc_situation_normal"), False)
        self.situation.addItem(t("vc_situation_accidental"), True)
        self.situation.currentIndexChanged.connect(self._touched)
        self.gamma = QLabel("")
        self.gamma.setTextFormat(Qt.TextFormat.RichText)
        self.labels = {}
        for key, widget in (("moisture", self.moisture), ("action", self.action), ("kled", self.kled), ("situation", self.situation)):
            label = QLabel(t("vc_factor_" + key))
            self.labels[key] = label
            frow.addWidget(label)
            frow.addWidget(widget)
        frow.addWidget(self.gamma)
        frow.addStretch(1)
        form.addRow(t("vc_factors"), line)
        self.box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)   # a row, as high as what it says
        return self.box

    def _touched(self, *_ignored):
        if not self.ctx.loading:
            self.ctx.touch()

    def _kled_tip(self):
        """Tableau 8 beside the choice of a KLED: each action of SIA 261 and its class (SIA 265/1 6.2.1.3)."""
        lines = ["%s — %s" % (r["action"], self.t("vc_kled_" + r["kled"])) for r in sia265_1.kled_actions()]
        return self.t("vc_kled_tip") + "\n" + "\n".join(lines)

    def _panel(self):
        return (self.material or {}).get("type") == "panel"

    # --- the contribution to the draft -------------------------------------------------------

    def fill(self, src):
        self.record = self.ctx.module.record(src) if src else {}
        self.material = material_of(src, self.record)
        for combo, index in ((self.action, 1 if src.get("impact") else 0),
                             (self.kled, max(self.kled.findData(src.get("kled") or mm.DEFAULT_KLED), 0)),
                             (self.situation, 1 if src.get("accidental") else 0)):
            combo.blockSignals(True)
            combo.setCurrentIndex(index)
            combo.blockSignals(False)
        self._moisture_items(src.get("moisture_class"))
        self.show()

    def collect(self, src):
        for key in ("kled", "accidental"):
            src.pop(key, None)
        material = material_of(src, None)
        if material and material.get("type") == "panel":
            if self.kled.currentData() != mm.DEFAULT_KLED:
                src["kled"] = self.kled.currentData()
            if self.situation.currentData():
                src["accidental"] = True
            src["impact"] = False
        else:
            src["impact"] = bool(self.action.currentData())
        src["moisture_class"] = self.moisture.currentData()

    def computed(self):
        src = self.ctx.computed_source
        self.record = self.ctx.module.record(src) if src else {}
        self.material = material_of(src, self.record)
        self._moisture_items(self.moisture.currentData())
        self.show()

    # --- what the row says -------------------------------------------------------------------

    def _moisture_items(self, chosen):
        """The moisture classes offered: a member's three (η_w beside each, SIA 265 Tabelle 4), a panel's those its product is admitted in (Tableau 9); the first follows the position."""
        lang = self.app.lang
        material = self.material or {}
        self.moisture.blockSignals(True)
        self.moisture.clear()
        pid = self.record.get("position")
        held = self.ctx.module.position_moisture(pid) if pid else None
        self.moisture.addItem(cards.followed(held, pid) if held is not None and pid else self.t("vc_moisture_none"), None)
        if material.get("type") == "panel" and material.get("product") in sia265_1.products():
            for c in sia265_1.admitted_classes(material["product"]):
                self.moisture.addItem(self.t("vc_moisture_panel", n=c), c)
        else:
            for c in sia265.moisture_class_ids():
                self.moisture.addItem(self.t("vc_moisture_member", n=c, eta=decimal(sia265.eta_w(c), lang, 1)), c)
        self.moisture.setCurrentIndex(max(self.moisture.findData(chosen), 0) if chosen is not None else 0)
        self.moisture.blockSignals(False)

    def show(self):
        """A member's action and γ_M/η_M, a panel's KLED, situation, η_mod and γ_M (UI-015)."""
        lang = self.app.lang
        material = self.material
        panel = self._panel()
        for key, widget in (("action", self.action), ("kled", self.kled), ("situation", self.situation)):
            shown = (key == "action") != panel
            widget.setVisible(shown)
            self.labels[key].setVisible(shown)
        res = self.record.get("resistance") or {}
        self.gamma.setToolTip("")
        if panel:
            if res.get("eta_mod") is not None:
                self.gamma.setText("η<sub>mod</sub> = %s · γ<sub>M</sub> = %s" % (decimal(res["eta_mod"], lang, 2), decimal(res["gamma_m"], lang, 1)))
            else:
                self.gamma.setText("")
        elif material and material.get("type") == "member":
            family = material.get("family")
            ratio = sia265.family_gamma_m(family) if family in sia265.FAMILY_GAMMA else None
            self.gamma.setText(richtext.subscripts(self.t("vc_gamma_member", gamma=decimal(ratio, lang, 1))) if ratio else "")
            self.gamma.setToolTip(self.t("vc_gamma_member_tip"))
        else:
            self.gamma.setText("")
