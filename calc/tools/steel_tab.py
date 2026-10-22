# -*- coding: utf-8 -*-
"""The «Acier» tabs of Woodcore's window: the steel checks of SIA 263:2013 -- section class, tension, compression, bending, shear (issues #50, #51; spec 2026-10-12-section-acier UI-001, UI-003, D-05, D-13; docs/ui/tab-steel.md).

**One base, the member checks'.** Each tab is a `member_check_tab.MemberCheckTab` -- the list in folders, the form in cards, the instant result, the «Calcul» and «Affichage» views, the fields that follow a variable -- told which domain it writes (`DOMAIN = steel_check`, its sources in Woodcore-Datei/steel/) and overriding only what steel does differently: the card «Profilé et acier» in the place of the material and section cards (`build_material`, `fill_material`, `fill_material_notes`, `draft_material`), the forces of its kind (`build_effort`), the result read off the export's rows (`window_result`), and the call `#show-check-steel` (lib/steel.typ). Nothing is computed here: `steel_check.resolve` and `compute` are what the export runs, run on the draft (D-09).

**What follows the position** (D-05): the profile -- an SZS C5 designation or a free profile, the position's section -- and the steel grade -- its strength class --, each shown in its own field, «IPE 360 — S010», and each written over by choosing another, with an orange line and «Reprendre» (the timber tabs' rule, v0.70/v0.77).

**«Affichage»** prints the check as the last export computed it: a draft is not exported, so the page asks for it to be saved first (`st_save_first`) -- the export being the one place a steel check is computed.
"""

import re

from PySide6.QtWidgets import QComboBox, QLabel

import build_reference as ref
import cards
import display_view
import project
import structure_preview
import theme
from domains import profile as free_profile, section as position_section, steel_check
from norms import sia263, szs_c5
from member_check_tab import MemberCheckTab
from member_check_tab_form import _n
from steel_tab_words import STRINGS  # noqa: F401  -- merged into the window's STRINGS by woodcore_gui_words

USER = position_section.USER_CODE


class SteelCheckTab(MemberCheckTab):
    GRAPH_KIND = "steel"   # a steel check of the graph of dependencies (issue #71)
    """A tab of steel checks of one kind -- see the module's docstring."""

    DOMAIN = steel_check
    NORM_PREFIX = "SIA 263 "
    POSITION_HINT_KEY = "st_position_hint"
    EMPTY_KEY = "st_empty"
    FIELDS = ()          # the forces the kind's card holds: (key, label key, unit, minimum)

    def sources_dir(self):
        return project.current().steel_dir

    def owns(self, source):
        return source.get("kind") == self.KIND

    def resolve_draft(self, source):
        return steel_check.resolve(source, self.positions())

    # --- the profile and the steel -----------------------------------------------------

    def build_material(self):
        box = cards.card(self.t("st_box_profile"))
        form = cards.form(box)
        self.material_form = form
        self.family_box = QComboBox()
        self.family_box.addItem("", None)   # the first entry follows the position
        for code in szs_c5.tabulated():
            self.family_box.addItem(code, code)
        self.family_box.addItem(self.t("st_free"), USER)
        self.family_box.currentIndexChanged.connect(self.on_family)
        form.addRow(self.t("st_family"), self.family_box)
        self.size_box = QComboBox()
        self.size_box.currentIndexChanged.connect(self.on_field)
        form.addRow(self.t("st_size"), self.size_box)
        self.profile_note = self.orange_note()
        self.profile_back = self.take_back_button(lambda: self.take_back(self.family_box))
        self.profile_line = self.row_with_back(form, self.profile_note, self.profile_back)
        self.grade_box = QComboBox()
        self.grade_box.addItem("", None)
        for grade in sia263.grades():
            self.grade_box.addItem(grade, grade)
        self.grade_box.currentIndexChanged.connect(self.on_field)
        form.addRow(self.t("st_grade"), self.grade_box)
        self.grade_note = self.orange_note()
        self.grade_back = self.take_back_button(lambda: self.take_back(self.grade_box))
        self.grade_line = self.row_with_back(form, self.grade_note, self.grade_back)
        self.form.addWidget(box)

    def fill_sizes(self, code, wanted=None):
        """The sizes of a family -- its table's, or the project's free profiles for USR -- with `wanted` kept where the list lacks it."""
        self.size_box.blockSignals(True)
        self.size_box.clear()
        if code == USER:
            sizes = [p["id"] for p in free_profile.list_sources()]
        elif code:
            sizes = list(szs_c5.sizes(code))
        else:
            sizes = []
        for size in sizes:
            self.size_box.addItem(size.replace("x", "×"), size)
        if wanted and wanted not in sizes:
            self.size_box.addItem("%s (?)" % wanted, wanted)
        self.size_box.setCurrentIndex(max(self.size_box.findData(wanted), 0) if wanted else 0)
        self.size_box.setEnabled(bool(code))
        self.size_box.blockSignals(False)

    def on_family(self, _index=0):
        if self.loading:
            return
        self.fill_sizes(self.family_box.currentData())
        self.on_field()

    def fill_material(self, s):
        prof = s.get("profile") or {}
        code = position_section.code_of(prof.get("type")) if prof else None
        if code and self.family_box.findData(code) < 0:
            self.family_box.addItem(code, code)
        self.family_box.setCurrentIndex(max(self.family_box.findData(code), 0))
        size = None
        if prof:
            values = position_section.split_dimension(code, prof.get("dimension"))
            size = (values[0] if code == USER else szs_c5.key_of(code, values)) if values else prof.get("dimension")
        self.fill_sizes(code, size)
        grade = s.get("grade")
        if grade and self.grade_box.findData(grade) < 0:
            self.grade_box.addItem(grade, grade)
        self.grade_box.setCurrentIndex(max(self.grade_box.findData(grade), 0))

    def fill_material_notes(self, pid, record):
        """The first entry of each combo says what the position holds, «IPE 360 — S010»; a line under it where it is written over or missing."""
        section = (record or {}).get("section") or {}
        held = section.get("text", "") if section.get("kind") in ("steel", "user") else ""
        following = self.family_box.currentData() is None
        self.family_box.setItemText(0, cards.followed(held, pid) if (pid and held) else self.t("mc_none"))
        if following:
            self.size_box.blockSignals(True)
            self.size_box.clear()
            self.size_box.setEnabled(False)
            self.size_box.blockSignals(False)
        text, back = "", False
        if pid and following and not held:
            text = self.t("st_no_profile", pid=pid)
        elif pid and not following and held:
            text, back = self.t("mc_overridden", pid=pid, value=held), True
        self.profile_note.setText(text)
        self.profile_note.setStyleSheet("color: %s;" % theme.colour("override"))
        self.profile_back.setVisible(back)
        self.material_form.setRowVisible(self.profile_line, bool(text))
        held_grade = (record or {}).get("strength_class") or ""
        self._note_for(self.grade_box, self.grade_note, self.grade_back, self.grade_line, self.material_form, pid, held_grade, held_grade,
                       "st_no_grade", lambda value: value)

    def draft_material(self, s):
        code = self.family_box.currentData()
        size = self.size_box.currentData()
        s["profile"] = {"type": code, "dimension": size} if code and size else None
        s["grade"] = self.grade_box.currentData()

    # --- the forces ------------------------------------------------------------------------

    def build_effort(self):
        box = cards.card(self.t("st_box_forces"))
        form = cards.form(box)
        self.effort_form = form
        self.force_spins = {}
        for key, label_key, unit, minimum in self.FIELDS:
            spin = self.spin(minimum, 1_000_000.0, 2 if unit != "mm²" else 0, 1.0 if unit != "mm²" else 100.0, " " + unit)
            if key == "A_net":
                spin.setSpecialValueText(self.t("st_A_net_none"))   # 0 is «not stated»: the gross section alone
            spin.valueChanged.connect(self.touch)
            self.force_spins[key] = spin
            form.addRow(self.t(label_key), self.linked(spin, key, unit, key))
        note = self.effort_note()
        if note:
            form.addRow("", cards.note(note))
        self.form.addWidget(box)

    def effort_note(self):
        return ""

    def fill_effort(self, s):
        for key, _label, unit, _minimum in self.FIELDS:
            if key == "A_net":
                self.force_spins[key].setValue(float(s.get("A_net") or 0))
                continue
            value = float((s.get(key) or {}).get("value") or 0)
            self.force_spins[key].setValue(self.shown_value(key, value))

    def shown_value(self, key, value):
        """A source's value as the field shows it -- a compression's N its magnitude."""
        return value

    def stored_value(self, key, value):
        return value

    def draft_effort(self, s):
        for key, _label, unit, _minimum in self.FIELDS:
            value = self.force_spins[key].value()
            if key == "A_net":
                s["A_net"] = value or None
            else:
                s[key] = {"value": self.stored_value(key, value), "unit": unit} if value or key == "N" else None

    # --- the result -----------------------------------------------------------------------

    def _computed(self, record):
        if record is None or not record.get("calculable"):
            return None
        key = id(record)
        if getattr(self, "_computed_key", None) != key:
            try:
                self._computed_value = steel_check.compute(record)
            except Exception:  # broad: the result card says what failed, never a slot
                self._computed_value = None
            self._computed_key = key
        return self._computed_value

    def window_result(self, record):
        """The export's rows as the card «Résultats» lists them: each value with its symbol, its unit, its label and the formula it was worked out by; the verdict's ratio in the vars' symbols. A record the norm offers no way through (class 4 ...) gives its reason."""
        result = self._computed(record)
        if not result:
            return None
        if "reason" in result:
            self.reason = self.t("mc_no_calc", reason=result["reason"])
            return None
        calc = result["calc"]
        formulas = {st["result"]: st["formula"].split(" = ", 1)[1] for st in calc["steps"]}
        rows = [{"key": key, "symbol": v["symbol"], "value": v["value"], "unit": v["unit"], "label": v["label"], "formula": formulas.get(key)}
                for key, v in calc["vars"].items()]
        symbols = {key: v["symbol"] for key, v in calc["vars"].items()}
        ratio = result.get("ratio")
        if ratio:
            ratio = re.sub(r"[A-Za-z][A-Za-z0-9_]*", lambda m: symbols.get(m.group(0), m.group(0)), ratio)
        clause = result.get("clause") or ""
        out = {"clause": clause, "rows": rows, "eta": result["eta"], "ok": result["ok"], "ratio": ratio}
        if result.get("classification") and result["eta"] is None:
            out["rows"].append({"key": "class", "symbol": "\"QK\"", "value": result["classification"]["class"], "unit": "", "label": self.t("st_class_result", cls=result["classification"]["class"])})
        return out

    # --- the call and the page --------------------------------------------------------------

    def command_text(self):
        """Its domain written out by the export, where a section prints it: `#include domain-file("steel", id)` (spec 2026-10-21-commandes-typst-refonte, REQ-017, UI-002)."""
        return ref.call_include_domain("steel", self.draft()["id"])

    def preview_source(self):
        """The page of the check as the last export computed it -- a draft has no page: it is saved first, the export being where a steel check is computed."""
        if self.current_id is None or self.dirty or self.record is None or not self.record.get("calculable"):
            return None
        here = project.current()
        return "\n".join(structure_preview.header(here, self.app.current_document())) + "\n\n" + self.command_text() + "\n"

    def display_entries(self):
        unsaved = self.current_id is None or self.dirty
        reason = "" if self.record is not None and self.record.get("calculable") else (self.reason or self.t("mc_preview_none"))
        if unsaved and not reason:
            reason = self.t("st_save_first")
        return [display_view.Entry("steel", "domain-file", call_fn=lambda _v: self.command_text(), snippet_fn=lambda _v: self.preview_source(),
                                   note_text=reason, banner=self.t("mc_save_first") if unsaved else "")]


class SteelClassTab(SteelCheckTab):
    """Classe de section: SIA 263 Tabelle 5a, 5b under the forces given."""

    KEY = "tab_st_class"
    KIND = "class"
    ID_PREFIX = "QK-"
    LIST_KEY = "st_list_class"
    FIELDS = (("N", "st_N_signed", "kN", -1_000_000.0), ("M_y", "st_M_y", "kNm", 0.0), ("M_z", "st_M_z", "kNm", 0.0))

    def effort_note(self):
        return self.t("st_class_note")


class SteelTensionTab(SteelCheckTab):
    """Traction: SIA 263 5.1.2, (38) and (39)."""

    KEY = "tab_st_tension"
    KIND = "tension"
    ID_PREFIX = "ST-Z"
    LIST_KEY = "st_list_tension"
    FIELDS = (("N", "st_N_tension", "kN", 0.0), ("A_net", "st_A_net", "mm²", 0.0))


class SteelCompressionTab(SteelCheckTab):
    """Compression: SIA 263 5.1.2, the section alone. The field is the force's magnitude; the source holds it negative (tension positive)."""

    KEY = "tab_st_compression"
    KIND = "compression"
    ID_PREFIX = "ST-D"
    LIST_KEY = "st_list_compression"
    FIELDS = (("N", "st_N_compression", "kN", 0.0),)

    def effort_note(self):
        return self.t("st_compression_note")

    def shown_value(self, key, value):
        return abs(value)

    def stored_value(self, key, value):
        return -abs(value)


class SteelBendingTab(SteelCheckTab):
    """Flexion: SIA 263 5.1.3, 5.1.6, 5.2.3, 5.2.6."""

    KEY = "tab_st_bending"
    KIND = "bending"
    ID_PREFIX = "ST-B"
    LIST_KEY = "st_list_bending"
    FIELDS = (("N", "st_N_signed", "kN", -1_000_000.0), ("M_y", "st_M_y", "kNm", 0.0), ("M_z", "st_M_z", "kNm", 0.0))


class SteelShearTab(SteelCheckTab):
    """Effort tranchant: SIA 263 5.1.4, 5.1.5, 5.2.4, 5.2.5 -- and the bending it reduces."""

    KEY = "tab_st_shear"
    KIND = "shear"
    ID_PREFIX = "ST-Q"
    LIST_KEY = "st_list_shear"
    FIELDS = (("V_z", "st_V_z", "kN", 0.0), ("V_y", "st_V_y", "kN", 0.0), ("M_y", "st_M_y", "kNm", 0.0))
