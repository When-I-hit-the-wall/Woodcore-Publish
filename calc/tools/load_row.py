"""The row «Sollicitation» of a member check, a service (spec docs/requirements/completed/2026-10-24-verifications-elements-v3.md, UI-006, UI-012, CON-005; issue #112).

Always there under the head «Élément» (check_member.CheckMember): a panel's bubbles as the engineer validated them for OSB/3 (T35) -- each its value of the b table at the draft's thickness, greyed without one --, a member's one bubble ticked and closed; beside them the ⓘ of the material's table (Tableaux 19a et 19b for an OSB/3, Tableau 8 for a class of SIA 265: the material's `excerpt`), pinned under «Résultats» by a click; under them the line **«La vérification lit …»**, read off the row of the clause `compute` writes (never composed again), in red the refusal of a thickness out of the ranges.

It contributes the draft's `loading` -- a panel's, the first of the tab where none was chosen; none for a member (`collect`) -- and redraws itself once the domain has computed the draft (phase `computed`), the material being the draft's (`check_rows.material_of`): the services never read each other.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

import cards
import richtext
import theme
from check_rows import decimal, material_of, material_value
from domains import member_check_material as mm
from norm_bubble import InfoMark
from tab_host import Service


class LoadRow(Service):
    """The row «Sollicitation» -- see the module's docstring."""

    NAME = "load"
    ZONE = "centre"
    NEEDS = ("record",)

    def mount(self, ctx):
        super().mount(ctx)
        t = self.t
        self.tab = ctx.module.TAB
        self.loading = None
        self.record = {}
        self.box = cards.card("")
        column = QVBoxLayout(self.box)
        column.setContentsMargins(10, 6, 10, 6)
        column.setSpacing(4)
        holder = QWidget()
        form = cards.form(holder)
        column.addWidget(holder)
        line = QWidget()
        row = QHBoxLayout(line)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)
        self.loading_holder = QWidget()
        self.loading_row = QHBoxLayout(self.loading_holder)
        self.loading_row.setContentsMargins(0, 0, 0, 0)
        self.loading_row.setSpacing(4)
        self.loading_buttons = {}
        row.addWidget(self.loading_holder)
        self.mark = InfoMark(t("vc_material_excerpt_tip"))
        self.mark.setVisible(False)
        self.excerpt = None
        row.addWidget(self.mark)
        row.addStretch(1)
        form.addRow(t("vc_loading"), line)
        self.reads = QLabel("")
        self.reads.setWordWrap(True)
        self.reads.setTextFormat(Qt.TextFormat.RichText)
        form.addRow("", self.reads)
        self.box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)   # a row, as high as what it says
        return self.box

    def _chose_loading(self, loading):
        self.loading = {"mode": loading[0], "direction": loading[1]}
        if not self.ctx.loading:
            self.ctx.touch()

    # --- the contribution to the draft -------------------------------------------------------

    def fill(self, src):
        self.loading = dict(src["loading"]) if src.get("loading") else None
        self.record = self.ctx.module.record(src) if src else {}
        self.show(src)

    def collect(self, src):
        src.pop("loading", None)
        material = material_of(src, None)
        if material and material.get("type") == "panel":
            if self.loading is None:
                first = mm.TAB_LOADINGS[self.tab][0]
                self.loading = {"mode": first[0], "direction": first[1]}
            src["loading"] = dict(self.loading)

    def computed(self):
        src = self.ctx.computed_source
        self.record = self.ctx.module.record(src) if src else {}
        self.show(src)

    # --- what the row says -------------------------------------------------------------------

    def show(self, src):
        material = material_of(src, self.record)
        self._buttons(material)
        self._excerpt(material)
        self._reads(material)

    def _buttons(self, material):
        """A panel's bubbles, each its value of the b table at the draft's thickness, greyed without one; a member's one bubble, ticked and closed (UI-006)."""
        while self.loading_row.count():
            item = self.loading_row.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self.loading_buttons = {}
        lang = self.app.lang
        quantity = mm.TAB_QUANTITY[self.tab]
        if material and material.get("type") == "panel":
            section = self.record.get("section") or {}
            thickness = min(section["b"], section["h"]) if section.get("type") == "rec" else None
            for loading in mm.TAB_LOADINGS[self.tab]:
                value = mm.loading_value(material, quantity, {"mode": loading[0], "direction": loading[1]}, thickness)
                button = QPushButton(("%s %s" % (self.t("vc_load_%s_%s" % loading), decimal(value, lang))) if value is not None else self.t("vc_load_%s_%s" % loading))
                button.setCheckable(True)
                button.setChecked(bool(self.loading) and (self.loading["mode"], self.loading["direction"]) == loading)
                button.setEnabled(value is not None)
                if value is None:
                    button.setToolTip(self.t("vc_load_none_tip"))
                button.setProperty("choice", True)
                button.clicked.connect(lambda _c=False, l=loading: self._chose_loading(l))
                self.loading_row.addWidget(button)
                self.loading_buttons[loading] = button
        else:
            value = material_value(material, self.tab)
            button = QPushButton("%s %s = %s" % (self.t("vc_load_member_" + self.tab), richtext.plain_math(self.t("vc_quantity_" + quantity)), decimal(value, lang)))
            button.setCheckable(True)
            button.setChecked(True)
            button.setEnabled(False)
            button.setToolTip(self.t("vc_load_member_tip"))
            self.loading_row.addWidget(button)
            self.loading_buttons["member"] = button

    def _excerpt(self, material):
        """The ⓘ of the material's table (UI-012): Tableaux 19a et 19b for an OSB/3, the table of a class of SIA 265 -- the material's `excerpt` --, hidden for the engineer's own."""
        excerpt = tuple((material or {}).get("excerpt") or ())
        bubbles = self.ctx.bubbles
        if len(excerpt) == 2 and bubbles is not None:
            self.excerpt = (excerpt[0], (excerpt[1],))
            bubbles.attach(self.mark, *self.excerpt)
            self.mark.setVisible(True)
        else:
            self.excerpt = None
            self.mark.setVisible(False)

    def _reads(self, material):
        """«La vérification lit …» (UI-006): the row of the design value `compute` writes -- its symbol, value, norm, clause and label --, the panel's thickness and range, the factors; in red the refusal of a thickness out of the ranges."""
        record, lang = self.record, self.app.lang
        if record.get("reason_code") == "thickness_out":
            p = record.get("reason_params") or {}
            self.reads.setText("<span style='color:%s'>%s</span>" % (theme.colour("danger"), richtext.escape(self.t("vc_reads_out", thickness=p.get("thickness", ""), ranges=p.get("ranges", "")))))
            return
        instance = self.ctx.instance
        if not instance:
            self.reads.setText("")
            return
        rows = instance["result"]["rows"]
        wanted = {"f_m": ("f_m_y_d", "f_m_z_d"), "f_t_0": ("f_t_0_d",), "f_c_0": ("f_c_0_d",), "f_v": ("f_v_d",)}[mm.TAB_QUANTITY[self.tab]]
        row = next((r for r in rows if r["key"] in wanted), None) or next((r for r in rows if r["key"].startswith("f_") and r["key"].endswith("_d")), None)
        if row is None:
            self.reads.setText("")
            return
        table = row.get("table") or {}
        res = record.get("resistance") or {}
        if table:
            # a member's design value, the table's (or the material's) value the factors multiply -- the row of its clause
            value, source = table["value"], " ".join(p for p in (row.get("norm") or "", table.get("clause") or "") if p)
        elif row.get("clause"):
            # a panel's: the b table's value at class 1, KLED medium, normal, or η_mod · f_k / γ_M
            value, source = row["value"], " ".join(p for p in (row.get("norm") or "", row["clause"]) if p)
        else:
            # a bending's f_m,y,d, written with the table's value in its formula: the value of the material and its source, the catalogue's
            value = material_value(material, self.tab)
            source = ((material or {}).get("source") or {}).get("ref") or ""
        symbol = row["symbol"].replace(",y,", ",").replace(",z,", ",") if row["key"] in ("f_m_y_d", "f_m_z_d") else row["symbol"]
        parts = [self.t("vc_reads", symbol=richtext.math_html(symbol), value=decimal(value, lang), unit=row.get("unit") or "N/mm²")]
        if source:
            parts.append(richtext.escape(source + ((", " + row["label"]) if row.get("label") and row["label"] not in ("eingegeben", "abgeleitet", "von der Norm festgelegt") else "")))
        if res.get("type") == "panel":
            parts.append(richtext.subscripts(self.t("vc_reads_thickness", thickness=decimal(res["thickness"], lang))))
            if res.get("eta_mod") is not None:
                parts.append(richtext.subscripts(self.t("vc_reads_panel", eta=decimal(res["eta_mod"], lang, 2), gamma=decimal(res["gamma_m"], lang, 1))))
        else:
            factors = {r["key"]: r["value"] for r in rows if r["key"] in ("eta_w", "eta_t")}
            if factors:
                parts.append(richtext.subscripts(self.t("vc_reads_member", eta_w=decimal(factors.get("eta_w"), lang, 1), eta_t=decimal(factors.get("eta_t"), lang, 1))))
        if res.get("type") == "member" and row.get("label") == "abgeleitet" or (table and table.get("clause") == "2.2.2"):
            parts.append(richtext.escape(self.t("vc_deduced")))
        self.reads.setText(" · ".join(parts))
