"""The sheet of a material, in folds, a service of the type «Bibliothèque» (spec docs/requirements/active/2026-10-24-onglet-materiaux.md, UI-004 to UI-006, REQ-004, REQ-006 to REQ-008, REQ-012; issue #110).

A shipped material shows a band -- read only, «Dupliquer dans ma bibliothèque» -- and every field off; the engineer's own every field on and «Annuler» / «Enregistrer» under the folds. The header: the name in the window's language and the label of its source, which shows the source in the right pane (`ctx.reveal`). Then the folds, each saying while folded what it holds (`module_pane.Fold`): **Identité** -- the type (a change of it builds the sheet again), the category, the names in the two other languages --; **Poids** -- per volume or per area, its value with its weight in kg (g = 10 m/s², `materials.KG_TO_KN`), its reference, «for the loads» --; **Résistances** -- a member's family, its six strengths, characteristic and design side by side, its stiffness and ρ_k; a panel's product, its thickness, ρ_k «for the strengths and the connections» and the grid of SIA 265/1 Tableau 19a, a column per range of thickness, characteristic | design --; **Commentaire**; **Source** -- a website or a PDF, copied into the library («Importer un PDF…»), a norm's reference for a shipped one.

A design value left empty is shown deduced or set by the norm (`materials_derive`), **in italics**, its rule and its numbers in its tooltip; a cell counted as missing is on the theme's `missing` ground. Every value the sheet shows is the domain's: it computes nothing. Every change writes the draft (`ctx.draft`) and is said (`ctx.touch`).
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QFont
from PySide6.QtWidgets import (QAbstractButton, QButtonGroup, QComboBox, QFileDialog, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPlainTextEdit,
                               QPushButton, QScrollArea, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

import cards
import theme
from chrome import SegmentedSwitch
from domains import materials, materials_contract as contract, materials_derive as derive, materials_library, materials_user
from material_marks import tag_text, type_icon
from module_pane import Fold
from norms import sia265, sia265_1
from tab_host import Service, _n

SYMBOL = {"m": "f_m", "t_0": "f_t,0", "c_0": "f_c,0", "t_90": "f_t,90", "c_90": "f_c,90", "v": "f_v"}
STIFF_SYMBOL = {"E_0_mean": "E_0,mean", "E_90_mean": "E_90,mean", "G_mean": "G_mean", "rho_k": "ρ_k"}
STIFF_UNIT = {"E_0_mean": "N/mm²", "E_90_mean": "N/mm²", "G_mean": "N/mm²", "rho_k": "kg/m³"}
ROW_SYMBOL = {"f_m": "f_m", "f_c_90": "f_c,90", "f_v": "f_v", "E_m_mean": "E_m,mean", "G_mean": "G_mean", "f_t": "f_t", "f_c": "f_c", "E_tc_mean": "E_t/c,mean"}


def number(text):
    """A number typed -- a comma as a point --, None for nothing; a text that is no number is None too, the cell staying empty."""
    text = (text or "").strip().replace(",", ".").replace("'", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def field(text, placeholder=""):
    edit = QLineEdit(text or "")
    edit.setPlaceholderText(placeholder)
    return edit


def range_label(t, column, first):
    lo, hi = column.get("t_min"), column.get("t_max")
    if lo is None:
        return "≤ %s" % _n(hi)
    if hi is None:
        return "> %s" % _n(lo)
    return "%s %s – %s" % ("≥" if column.get("from_inclusive") or first else ">", _n(lo), _n(hi))


class MaterialSheet(Service):
    """The sheet of the material selected -- see the module's docstring."""

    NAME = "sheet"
    ZONE = "centre"
    IN_VIEWS = ()

    def mount(self, ctx):
        super().mount(ctx)
        self.mode = "k"
        self.folded = {}
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.inner = None
        return self.scroll

    # --- the phases -----------------------------------------------------------------

    def selected(self):
        """The sheet built again for the draft."""
        self.grid = None
        self.inner = QWidget()
        self.inner.setObjectName("cardGround")
        self.column = QVBoxLayout(self.inner)
        self.column.setContentsMargins(0, 0, 8, 0)
        self.folds = {}
        m = self.ctx.draft
        if m is not None:
            self.editable = self.ctx.editable()
            if not self.editable:
                self._readonly_band()
            self._header(m)
            self._fold("ident", self.t("mat_ident"), self._ident(m))
            self._fold("weight", self.t("mat_weight"), self._weight(m))
            if m["type"] == "member":
                self._fold("strength", self.t("mat_strength"), self._member(m))
            if m["type"] == "panel":
                self._fold("strength", self.t("mat_strength"), self._panel(m))
            self._fold("comment", self.t("mat_comment"), self._comment(m))
            self._fold("source", self.t("mat_source"), self._source(m))
            if self.editable:
                self._buttons()
            else:
                for button in self.inner.findChildren(QAbstractButton):
                    if not button.isEnabled() and not button.toolTip():
                        button.setToolTip(self.t("mat_readonly"))   # a disabled button says why
            self.summaries()
        self.column.addStretch(1)
        self.scroll.setWidget(self.inner)

    def drafted(self):
        self.summaries()
        if getattr(self, "grid", None) is not None and self.ctx.draft is not None:
            self._fill_grid()

    # --- the parts ------------------------------------------------------------------

    def _readonly_band(self):
        band = QFrame()
        band.setStyleSheet("background: %s; border-radius: 6px;" % theme.colour("accent-soft"))
        row = QHBoxLayout(band)
        label = QLabel("🔒 " + self.t("mat_readonly"))
        label.setWordWrap(True)
        row.addWidget(label, 1)
        self.dup_mine = QPushButton(self.t("mat_dup_mine"))
        self.dup_mine.clicked.connect(lambda: self.ctx.start(materials_library.duplicate(self.ctx.draft)))
        row.addWidget(self.dup_mine)
        self.column.addWidget(band)

    def _header(self, m):
        row = QHBoxLayout()
        lang = self.app.lang
        self.name_edit = field(contract.name(m, lang) if not self.editable else (m.get("names") or {}).get(lang, ""), self.t("mat_name"))
        self.name_edit.setReadOnly(not self.editable)
        font = self.name_edit.font()
        font.setPointSizeF(font.pointSizeF() * 1.25)
        self.name_edit.setFont(font)
        self.name_edit.textEdited.connect(lambda text: self._set_name(lang, text))
        row.addWidget(self.name_edit, 1)
        self.tag = QPushButton(tag_text(self.t, m))
        self.tag.setFlat(True)
        self.tag.setToolTip(self.t("mat_src_tip"))
        self.tag.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tag.clicked.connect(lambda: self.ctx.reveal("source"))
        row.addWidget(self.tag)
        self.column.addLayout(row)

    def _fold(self, key, title, body):
        fold = Fold(self.inner, title, self.t)
        fold.set_body(body)
        fold.set_folded(self.folded.get(key, False))
        fold.fold_button.clicked.connect(lambda _c=False, k=key, f=fold: self.folded.__setitem__(k, f.folded))
        self.folds[key] = fold
        self.column.addWidget(fold)

    def summaries(self):
        """What each fold says while folded."""
        m = self.ctx.draft
        if m is None or not getattr(self, "folds", None):
            return
        self.folds["ident"].set_summary("%s · %s" % (self.t("mat_type_" + m["type"]), self.t("mat_cat_" + m["category"])))
        w = m.get("weight")
        self.folds["weight"].set_summary("%s %s" % (_n(w["value"]), w["unit"]) if w and w.get("value") is not None else "—")
        if "strength" in self.folds:
            n = derive.missing(m)
            self.folds["strength"].set_summary(('<span style="color:%s">%d ✕</span>' % (theme.colour("warning"), n)) if n else "✓")
        self.folds["comment"].set_summary((m.get("comment") or "")[:40])
        source = m.get("source") or {}
        self.folds["source"].set_summary(source.get("ref") or source.get("url") or source.get("file") or self.t("mat_no_source"))

    def _set_name(self, lang, text):
        self.ctx.draft.setdefault("names", {})[lang] = text
        self.ctx.touch()

    def _set(self, key, value):
        if value is None:
            self.ctx.draft.pop(key, None)
        else:
            self.ctx.draft[key] = value
        self.ctx.touch()

    # --- Identité -------------------------------------------------------------------

    def _ident(self, m):
        body = QWidget()
        form = cards.form(body)
        self.type_switch = SegmentedSwitch([(k, self.t("mat_type_" + k), self.t("mat_type_hint_" + k)) for k in contract.TYPES], m["type"])
        for k in contract.TYPES:
            self.type_switch.button(k).setIcon(type_icon(k))
            self.type_switch.button(k).setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.type_switch.setEnabled(self.editable)
        self.type_switch.changed.connect(self._set_type)
        form.addRow(self.t("mat_type"), self.type_switch)
        self.category = QComboBox()
        for c in contract.CATEGORIES:
            self.category.addItem(self.t("mat_cat_" + c), c)
        self.category.setCurrentIndex(max(self.category.findData(m["category"]), 0))
        self.category.setEnabled(self.editable)
        self.category.currentIndexChanged.connect(lambda _i: self._set("category", self.category.currentData()))
        form.addRow(self.t("mat_category"), self.category)
        self.more = QPushButton(self.t("mat_names_more"))
        self.more.setFlat(True)
        form.addRow("", self.more)
        self.other_names = {}
        for lang in contract.LANGS:
            if lang == self.app.lang:
                continue
            edit = field((m.get("names") or {}).get(lang, ""))
            edit.setReadOnly(not self.editable)
            edit.textEdited.connect(lambda text, l=lang: self._set_name(l, text))
            form.addRow(self.t("mat_name_" + lang), edit)
            edit.setVisible(False)
            form.labelForField(edit).setVisible(False)
            self.other_names[lang] = edit
        self.more.clicked.connect(lambda: [(e.setVisible(not e.isVisible()), form.labelForField(e).setVisible(e.isVisible())) for e in self.other_names.values()])
        return body

    def _set_type(self, kind):
        """A change of type: what the old one carried taken away, the new one's fields given, the sheet built again."""
        m = self.ctx.draft
        if kind == m["type"]:
            return
        for key in ("family", "values", "product", "isotropic", "columns", "thickness", "rho_k", "grid"):
            m.pop(key, None)
        blank = materials_user.blank(kind)
        for key in ("family", "values", "product", "isotropic", "columns", "thickness", "rho_k", "grid"):
            if key in blank:
                m[key] = blank[key]
        m["type"] = kind
        self.ctx.dirty = True
        self.ctx.rebuild()

    # --- Poids ----------------------------------------------------------------------

    def _weight(self, m):
        body = QWidget()
        form = cards.form(body)
        w = m.get("weight") or {}
        unit = w.get("unit") if w else None
        self.weight_switch = SegmentedSwitch([("kN/m³", self.t("mat_weight_vol"), "kN/m³"), ("kN/m²", self.t("mat_weight_surf"), "kN/m²"), ("", self.t("mat_weight_none"), "")],
                                             unit if w else "")
        self.weight_switch.setEnabled(self.editable)
        self.weight_switch.changed.connect(self._weight_unit)
        form.addRow(self.t("mat_weight"), self.weight_switch)
        row = QHBoxLayout()
        self.weight_value = field(_n(w["value"]) if w.get("value") is not None else "")
        self.weight_value.setReadOnly(not self.editable)
        self.weight_value.setMaximumWidth(110)
        self.weight_value.textEdited.connect(self._weight_value)
        self.weight_unit = QLabel(unit or "")
        self.weight_kg = QLabel("")
        self.weight_kg.setStyleSheet("color: %s;" % theme.colour("muted"))
        row.addWidget(self.weight_value)
        row.addWidget(self.weight_unit)
        row.addWidget(self.weight_kg, 1)
        holder = QWidget()
        holder.setLayout(row)
        form.addRow("", holder)
        self.weight_ref = field(w.get("ref", ""), self.t("mat_weight_ref"))
        self.weight_ref.setReadOnly(not self.editable)
        self.weight_ref.textEdited.connect(self._weight_ref)
        form.addRow(self.t("mat_weight_ref"), self.weight_ref)
        role = QLabel(self.t("mat_weight_role"))
        role.setStyleSheet("color: %s;" % theme.colour("muted"))
        form.addRow("", role)
        self._weight_shown()
        return body

    def _weight_shown(self):
        w = self.ctx.draft.get("weight") or {}
        self.weight_value.setEnabled(bool(w) or not self.editable)
        self.weight_unit.setText(w.get("unit", "") if w else "")
        value = w.get("value") if w else None
        self.weight_kg.setText("= %s %s" % (_n(value * materials.KG_TO_KN), "kg/m³" if w.get("unit") == "kN/m³" else "kg/m²") if value is not None else "")

    def _weight_unit(self, unit):
        m = self.ctx.draft
        if not unit:
            m.pop("weight", None)
        else:
            m["weight"] = dict(m.get("weight") or {"value": number(self.weight_value.text()), "ref": self.weight_ref.text()}, unit=unit)
        self._weight_shown()
        self.ctx.touch()

    def _weight_value(self, text):
        m = self.ctx.draft
        if not m.get("weight"):
            m["weight"] = {"unit": "kN/m³", "ref": self.weight_ref.text()}
            self.weight_switch.set_current("kN/m³")
        m["weight"]["value"] = number(text)
        self._weight_shown()
        self.ctx.touch()

    def _weight_ref(self, text):
        if self.ctx.draft.get("weight"):
            self.ctx.draft["weight"]["ref"] = text
            self.ctx.touch()

    # --- Résistances: a member --------------------------------------------------------

    def _member(self, m):
        body = QWidget()
        column = QVBoxLayout(body)
        column.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        row.addWidget(QLabel(self.t("mat_family")))
        self.family = QComboBox()
        for f in contract.FAMILIES:
            self.family.addItem(self.t("mat_fam_" + f), f)
        self.family.setCurrentIndex(max(self.family.findData(m.get("family")), 0))
        self.family.setEnabled(self.editable)
        self.family.currentIndexChanged.connect(lambda _i: self._set("family", self.family.currentData()))
        row.addWidget(self.family)
        self.gamma = QLabel("")
        self.gamma.setStyleSheet("color: %s;" % theme.colour("muted"))
        row.addWidget(self.gamma, 1)
        column.addLayout(row)
        self.grid = QTableWidget(len(contract.MEMBER_STRENGTHS) + len(contract.MEMBER_STIFFNESS), 3)
        self.grid.setHorizontalHeaderLabels([self.t("mat_col_strength"), self.t("mat_col_k"), self.t("mat_col_d")])
        self.grid.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.grid.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.grid.verticalHeader().setVisible(False)
        self.grid.itemChanged.connect(self._member_cell)
        column.addWidget(self.grid)
        note = QLabel(self.t("mat_ded_note"))
        note.setWordWrap(True)
        note.setStyleSheet("color: %s;" % theme.colour("muted"))
        column.addWidget(note)
        self._fill_grid()
        return body

    def _cell(self, text, editable, key, italic=False, tip="", missing=False):
        item = QTableWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, key)
        flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        if editable and key:
            flags |= Qt.ItemFlag.ItemIsEditable
        item.setFlags(flags)
        if italic:
            font = QFont(item.font())
            font.setItalic(True)
            item.setFont(font)
            item.setForeground(QBrush(theme.qcolor("muted")))
        if tip:
            item.setToolTip(tip)
        if missing:
            item.setBackground(QBrush(theme.qcolor("missing")))
        return item

    def _rule(self, design):
        if design is None or design.how == "typed":
            return self.t("mat_rule_typed") if design is not None else ""
        params = {k: (_n(v) if isinstance(v, (int, float)) else v) for k, v in design.params.items()}
        return self.t("mat_rule_" + design.rule, **params)

    def _fill_grid(self):
        m = self.ctx.draft
        self.grid.blockSignals(True)
        try:
            if m["type"] == "member":
                self._fill_member(m)
            else:
                self._fill_panel(m)
        finally:
            self.grid.blockSignals(False)

    def _fill_member(self, m):
        try:
            self.gamma.setText(self.t("mat_gamma", g=_n(sia265.family_gamma_m(m.get("family", "softwood")))))
        except Exception:  # broad: a family the norm does not know says nothing here; the save refuses it
            self.gamma.setText("")
        values = m.get("values") or {}
        for r, s in enumerate(contract.MEMBER_STRENGTHS):
            design = derive.member_design(m, s)
            k = values.get("f_%s_k" % s)
            lacking = k is None and design is None
            self.grid.setItem(r, 0, self._cell("%s  %s [N/mm²]" % (self.t("mat_s_" + s), SYMBOL[s]), False, ""))
            self.grid.setItem(r, 1, self._cell(_n(k) if k is not None else "", self.editable, "f_%s_k" % s, missing=lacking))
            shown = _n(design.value) if design is not None else ""
            self.grid.setItem(r, 2, self._cell(shown, self.editable, "f_%s_d" % s, italic=design is not None and design.how != "typed", tip=self._rule(design), missing=lacking))
        for i, key in enumerate(contract.MEMBER_STIFFNESS):
            r = len(contract.MEMBER_STRENGTHS) + i
            value = values.get(key)
            self.grid.setItem(r, 0, self._cell("%s [%s]" % (STIFF_SYMBOL[key], STIFF_UNIT[key]), False, ""))
            self.grid.setItem(r, 1, self._cell(_n(value) if value is not None else "", self.editable, key, missing=value is None))
            self.grid.setItem(r, 2, self._cell("", False, ""))

    def _member_cell(self, item):
        key = item.data(Qt.ItemDataRole.UserRole)
        if not key:
            return
        values = self.ctx.draft.setdefault("values", {})
        value = number(item.text())
        if key.endswith("_d") and value is not None and item.font().italic():
            design = derive.member_design(self.ctx.draft, key[2:-2])
            if design is not None and abs(design.value - value) < 1e-9:
                value = None     # the italic value left as it was: still deduced
        if value is None:
            values.pop(key, None)
        else:
            values[key] = value
        self.ctx.touch()

    # --- Résistances: a panel ---------------------------------------------------------

    def _panel(self, m):
        body = QWidget()
        column = QVBoxLayout(body)
        column.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        row.addWidget(QLabel(self.t("mat_product")))
        self.product = QComboBox()
        self.product.addItem("—", None)
        for pid in sia265_1.products():
            self.product.addItem(self.t("mat_prod_" + pid), pid)
        self.product.setCurrentIndex(max(self.product.findData(m.get("product")), 0))
        self.product.setEnabled(self.editable)
        self.product.currentIndexChanged.connect(lambda _i: self._set("product", self.product.currentData()))
        row.addWidget(self.product)
        self.gamma = QLabel("")
        self.gamma.setStyleSheet("color: %s;" % theme.colour("muted"))
        row.addWidget(self.gamma, 1)
        column.addLayout(row)
        if not m.get("columns"):
            row = QHBoxLayout()
            row.addWidget(QLabel(self.t("mat_thickness")))
            self.thickness = field(_n(m["thickness"]) if m.get("thickness") is not None else "", self.t("mat_thickness_hint"))
            self.thickness.setReadOnly(not self.editable)
            self.thickness.setMaximumWidth(90)
            self.thickness.textEdited.connect(lambda text: self._set("thickness", number(text)))
            row.addWidget(self.thickness)
            row.addWidget(QLabel("mm"))
            hint = QLabel(self.t("mat_thickness_hint"))
            hint.setStyleSheet("color: %s;" % theme.colour("muted"))
            row.addWidget(hint, 1)
            column.addLayout(row)
        self.mode_switch = SegmentedSwitch([("k", self.t("mat_vals_k"), ""), ("d", self.t("mat_vals_d"), "")], self.mode)
        self.mode_switch.changed.connect(self._mode)
        column.addWidget(self.mode_switch, 0, Qt.AlignmentFlag.AlignLeft)
        self.grid = QTableWidget(0, 0)
        self.grid.verticalHeader().setVisible(False)
        self.grid.itemChanged.connect(self._panel_cell)
        column.addWidget(self.grid)
        note = QLabel(self.t("mat_ded_note"))
        note.setWordWrap(True)
        note.setStyleSheet("color: %s;" % theme.colour("muted"))
        column.addWidget(note)
        self._fill_grid()
        return body

    def _mode(self, mode):
        self.mode = mode
        self._fill_grid()

    def _panel_rows(self, m):
        """The grid's rows in the mode shown: ρ_k, then per loading its heading and its rows -- a strength by its `_k` or `_d`, a modulus in the characteristic grid alone -- one per direction."""
        rows = [("rho", None, None, None)]
        for loading, keys in contract.PANEL_GRID.items():
            rows.append(("head", loading, None, None))
            for key in keys:
                if self.mode == "d" and not contract.is_strength(key):
                    continue
                for direction in contract.directions(m):
                    rows.append(("value", loading, key, direction))
        return rows

    def _fill_panel(self, m):
        factors = derive.panel_factors(m)
        self.gamma.setText(self.t("mat_factors", g=_n(factors[0]), e=_n(factors[1])) if factors else "")
        columns = m.get("columns") or []
        n = contract.column_count(m)
        labels = [range_label(self.t, c, i == 0) for i, c in enumerate(columns)] or [(_n(m["thickness"]) + " mm") if m.get("thickness") is not None else self.t("mat_col_any")]
        rows = self._panel_rows(m)
        self.grid.clear()
        self.grid.setColumnCount(2 + n)
        self.grid.setRowCount(len(rows))
        self.grid.setHorizontalHeaderLabels(["", self.t("mat_col_t")] + labels)
        self.grid.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.grid.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.grid.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.panel_rows = rows
        for r, (kind, loading, key, direction) in enumerate(rows):
            if kind == "rho":
                self.grid.setItem(r, 0, self._cell("ρ_k [kg/m³] — %s" % self.t("mat_rho_role"), False, ""))
                self.grid.setItem(r, 1, self._cell("", False, ""))
                rho = m.get("rho_k") or [None] * n
                for c in range(n):
                    value = rho[c] if c < len(rho) else None
                    self.grid.setItem(r, 2 + c, self._cell((("≥ " if m.get("rho_k_is_minimum") else "") + _n(value)) if value is not None else "", self.editable, "rho:%d" % c, missing=value is None))
                continue
            if kind == "head":
                self.grid.setItem(r, 0, self._cell(self.t("mat_load_" + loading), False, ""))
                font = QFont(self.grid.item(r, 0).font())
                font.setBold(True)
                self.grid.item(r, 0).setFont(font)
                self.grid.setSpan(r, 0, 1, 2 + n)
                continue
            suffix = "_k" if contract.is_strength(key) and self.mode == "k" else ("_d" if contract.is_strength(key) else "")
            unit = "N/mm²"
            self.grid.setItem(r, 0, self._cell("%s  %s%s [%s]" % (self.t("mat_row_" + key), ROW_SYMBOL[key], {"_k": ",k", "_d": ",d", "": ""}[suffix], unit), False, ""))
            self.grid.setItem(r, 1, self._cell(self.t("mat_dir_" + direction), False, ""))
            self.grid.item(r, 1).setToolTip(self.t("mat_dir_tip"))
            not_given = derive.unavailable(m, loading, key)
            for c in range(n):
                cell_key = "grid:%s:%s:%s:%d" % (loading, key + suffix, direction, c)
                if not_given:
                    self.grid.setItem(r, 2 + c, self._cell("—", False, "", tip=self.t("mat_not_given")))
                    continue
                if suffix == "_d":
                    design = derive.panel_design(m, loading, key, direction, c)
                    k = derive.cell(m, loading, key + "_k", direction, c)
                    shown = _n(design.value) if design is not None else ""
                    self.grid.setItem(r, 2 + c, self._cell(shown, self.editable, cell_key, italic=design is not None and design.how != "typed", tip=self._rule(design),
                                                           missing=design is None and k is None))
                else:
                    value = derive.cell(m, loading, key + suffix, direction, c)
                    lacking = value is None and (not contract.is_strength(key) or derive.panel_design(m, loading, key, direction, c) is None)
                    self.grid.setItem(r, 2 + c, self._cell(_n(value) if value is not None else "", self.editable, cell_key, missing=lacking))

    def _panel_cell(self, item):
        key = item.data(Qt.ItemDataRole.UserRole)
        if not key:
            return
        m = self.ctx.draft
        n = contract.column_count(m)
        value = number(item.text())
        if key.startswith("rho:"):
            rho = list(m.get("rho_k") or [None] * n)
            rho += [None] * (n - len(rho))
            rho[int(key[4:])] = value
            m["rho_k"] = rho
        else:
            _g, loading, full, direction, column = key.split(":")
            column = int(column)
            if full.endswith("_d") and value is not None and item.font().italic():
                design = derive.panel_design(m, loading, full[:-2], direction, column)
                if design is not None and abs(design.value - value) < 1e-9:
                    value = None
            cells = m.setdefault("grid", {}).setdefault(loading, {}).setdefault(full, {})
            values = list(cells.get(direction) or [None] * n)
            values += [None] * (n - len(values))
            values[column] = value
            cells[direction] = values
            if all(v is None for v in values):
                cells.pop(direction)
            if not cells:
                m["grid"][loading].pop(full)
        self.ctx.touch()

    # --- Commentaire, Source --------------------------------------------------------

    def _comment(self, m):
        self.comment = QPlainTextEdit(m.get("comment") or "")
        self.comment.setReadOnly(not self.editable)
        self.comment.setMaximumHeight(80)
        self.comment.textChanged.connect(lambda: self._set("comment", self.comment.toPlainText()))
        return self.comment

    def _source(self, m):
        body = QWidget()
        form = cards.form(body)
        source = m.get("source") or {"kind": "none"}
        if not self.editable:
            ref = QLabel(source.get("ref") or source.get("url") or "")
            ref.setWordWrap(True)
            form.addRow(self.t("mat_src_norm" if source.get("kind") == "norm" else "mat_source"), ref)
            return body
        kinds = [("none", self.t("mat_src_none"), ""), ("url", self.t("mat_src_url"), ""), ("pdf", self.t("mat_src_pdf"), "")]
        if source.get("kind") == "book":
            kinds.append(("book", self.t("mat_source"), ""))
        self.source_switch = SegmentedSwitch(kinds, source.get("kind", "none"))
        self.source_switch.changed.connect(self._source_kind)
        form.addRow(self.t("mat_source"), self.source_switch)
        self.url = field(source.get("url", ""), "https://")
        self.url.textEdited.connect(self._source_url)
        form.addRow(self.t("mat_src_url"), self.url)
        row = QHBoxLayout()
        self.pdf_name = QLabel(source.get("file") or self.t("mat_no_pdf"))
        self.import_button = QPushButton(self.t("mat_import_pdf"))
        self.import_button.clicked.connect(lambda: self.import_pdf())
        row.addWidget(self.pdf_name, 1)
        row.addWidget(self.import_button)
        holder = QWidget()
        holder.setLayout(row)
        form.addRow(self.t("mat_src_pdf"), holder)
        if source.get("kind") == "book":
            ref = field(source.get("ref", ""))
            ref.textEdited.connect(lambda text: (self.ctx.draft["source"].__setitem__("ref", text), self.ctx.touch()))
            form.addRow(self.t("mat_weight_ref"), ref)
        return body

    def _source_kind(self, kind):
        source = dict(self.ctx.draft.get("source") or {}, kind=kind)
        self.ctx.draft["source"] = source
        self.ctx.touch()

    def _source_url(self, text):
        self.ctx.draft["source"] = dict(self.ctx.draft.get("source") or {}, kind="url", url=text.strip())
        self.source_switch.set_current("url")
        self.ctx.touch()

    def import_pdf(self, path=None):
        """«Importer un PDF…»: chosen in the system's file window -- or given, a PDF dropped --, **copied** into the library's sources, the source naming the copy (REQ-012)."""
        if path is None:
            path, _filter = QFileDialog.getOpenFileName(self.ctx.tab, self.t("mat_import_pdf"), "", self.t("mat_pdf_filter"))
            if not path:
                return False
        rel = materials_user.import_pdf(path)
        self.ctx.draft["source"] = {"kind": "pdf", "file": rel}
        if hasattr(self, "pdf_name"):
            self.pdf_name.setText(rel)
            self.source_switch.set_current("pdf")
        self.ctx.touch()
        return rel

    # --- Annuler / Enregistrer ---------------------------------------------------------

    def _buttons(self):
        row = QHBoxLayout()
        row.addStretch(1)
        self.cancel_button = QPushButton(self.t("mat_cancel"))
        self.cancel_button.clicked.connect(lambda: self.ctx.cancel())
        self.save_button = QPushButton(self.t("mat_save"))
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(lambda: self.ctx.save_entry())
        row.addWidget(self.cancel_button)
        row.addWidget(self.save_button)
        self.column.addLayout(row)

    def state(self):
        return {"mode": self.mode, "folded": dict(self.folded)}

    def restore(self, state):
        self.mode = state.get("mode") or "k"
        self.folded = dict(state.get("folded") or {})
