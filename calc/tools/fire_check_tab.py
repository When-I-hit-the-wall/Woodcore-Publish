# -*- coding: utf-8 -*-
"""The «Résistance au feu» tab: member checks in the design situation fire of SIA 265 4.5.2, and the fire resistance VKF / AEAI 15-15 requires of the building's load-bearing structure (issue #46, spec docs/requirements/active/2026-10-12-resistance-au-feu.md; docs/ui/tab-fire-resistance.md).

**One tab, five kinds** (the engineer's D-01 and D-09): bending, shear, buckling, and the section in compression or in tension -- the checks of the other tabs of «Sécurité structurale», each in the fire situation. A check here is a source of `Woodcore-Datei/checks/` like theirs, of their kinds, carrying `fire` (D-06): this tab lists the sources that carry it, every other tab those that do not (`MemberCheckTab.owns`). The kind is chosen in a combo, **closed once the check is saved** -- a saved check keeps its kind, the fields of one kind meaning nothing to another (ARCH-RISK-101); the effort's rows of every kind are built once and shown or hidden by the kind, nothing rebuilt.

**The duration follows the building unless it is written over** -- the pattern of the contact width of a compression: the field shows what VKF 15-15 requires, «60 min — AEAI 15-15, tableau 2», and a value typed stays written over, an orange line naming what the directive requires with «Reprendre» beside it. The building is the project's, once (D-10): the card «Bâtiment (AEAI 15-15)» holds its height category, use, concept and storeys, written to `Woodcore-Datei/building.json` by «Enregistrer le bâtiment» or with the check (Ctrl+S); every check that follows it is exported again then. Nothing of the directive is decided here: the duration is `vkf.required_resistance`'s, the residual section and the result `member_check`'s.

⚠️ The forces are E_d,fi, typed as the fire situation gives them (D-08): no 0.6 · E_d and no combination here.
"""

import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QPushButton, QWidget

import cards
import project
import theme
import validation
from domains import member_check
from norms import sia265, vkf
from member_check_tab import BucklingLengths, MemberCheckTab
from member_check_tab_actions import next_free_id
from member_check_tab_form import _n
from fire_check_tab_words import STRINGS  # noqa: F401  -- merged into the window's STRINGS by woodcore_gui_words

# The kinds of the tab, in the order the combo lists them, with the key of each one's words. Literals on purpose: tests/test_i18n.py finds a key by the code that names it.
KINDS = (
    ("bending", "mc_fire_kind_bending"),
    ("shear", "mc_fire_kind_shear"),
    ("buckling", "mc_fire_kind_buckling"),
    ("compression", "mc_fire_kind_compression"),
    ("tension", "mc_fire_kind_tension"),
)
SIDE_WORDS = {"bottom": "mc_fire_side_bottom", "top": "mc_fire_side_top", "left": "mc_fire_side_left", "right": "mc_fire_side_right"}
WOODS = ((None, "mc_fire_wood_auto"), ("beech", "mc_fire_wood_beech"), ("oak", "mc_fire_wood_oak"), ("cladding", "mc_fire_wood_cladding"))
# The words of VKF 15-15's lists, by the ids of calc/norms/vkf-2015-15-15-tab01-03-tragwerk.json -- tests/test_fire_check_tab.py holds that every id has its word
AEAI_WORDS = {
    "height": {"low": "mc_aeai_height_low", "medium": "mc_aeai_height_medium", "high": "mc_aeai_height_high"},
    "use": {"housing": "mc_aeai_use_housing", "office": "mc_aeai_use_office", "school": "mc_aeai_use_school", "retail": "mc_aeai_use_retail",
            "parking": "mc_aeai_use_parking", "industry_low": "mc_aeai_use_industry_low", "agriculture": "mc_aeai_use_agriculture",
            "industry_high": "mc_aeai_use_industry_high", "lodging_a": "mc_aeai_use_lodging_a", "lodging_b": "mc_aeai_use_lodging_b",
            "lodging_c": "mc_aeai_use_lodging_c", "assembly": "mc_aeai_use_assembly", "department_store": "mc_aeai_use_department_store",
            "single_family": "mc_aeai_use_single_family", "small_building": "mc_aeai_use_small_building"},
    "concept": {"construction": "mc_aeai_concept_construction", "extinction": "mc_aeai_concept_extinction"},
    "storeys": {"single": "mc_aeai_storeys_single", "two_small": "mc_aeai_storeys_two_small", "several": "mc_aeai_storeys_several"},
}
BUILDING_LABELS = {"height": "mc_building_height", "use": "mc_building_use", "concept": "mc_building_concept", "storeys": "mc_building_storeys"}
# The fields of the source each kind holds beyond N -- what draft_effort writes and takes out
KIND_FIELDS = ("M_y", "M_z", "V_z", "V_y", "pith", "l_y", "l_z", "beta_y", "beta_z")


class FireCheckTab(BucklingLengths, MemberCheckTab):
    """Résistance au feu: the member checks of SIA 265 4.2 in the design situation fire (4.5.2) -- see the module's docstring."""

    KEY = "tab_mc_fire"
    KIND = "bending"          # the kind a new check starts as
    ID_PREFIX = "FE-"
    LIST_KEY = "mc_list_fire"
    EMPTY_KEY = "mc_empty_fire"
    N_KEY = "mc_N_fire"
    N_MIN = -1_000_000.0       # a bending's N is signed; the other kinds' a magnitude, the field's minimum following the kind
    duration_stated = False    # the duration is written over (else it follows VKF 15-15)
    building_dirty = False     # the building's card changed and is not saved

    def __init__(self, app):
        self.building_data = None
        super().__init__(app)

    # --- what this tab lists and makes ----------------------------------------------

    def owns(self, source):
        return source.get("fire") is not None

    def current_kind(self):
        box = getattr(self, "kind_box", None)
        return (box.currentData() if box is not None else None) or self.source.get("kind") or self.KIND

    def make_source(self):
        kind = getattr(self, "kind_box", None).currentData() if getattr(self, "kind_box", None) is not None else self.KIND
        return member_check.new_source(next_free_id(self._taken(), self.ID_PREFIX), kind or self.KIND, fire=True)

    def resolve_draft(self, source):
        return member_check.resolve(source, self.positions(), building=self.building())

    # --- the cards ---------------------------------------------------------------------

    def build_effort(self):
        # the fire: the kind, the duration, the faces, the wood, the top storey
        box = cards.card(self.t("mc_box_fire"))
        form = cards.form(box)
        self.fire_form = form
        self.kind_box = QComboBox()
        for kind, words in KINDS:
            self.kind_box.addItem(self.t(words), kind)
        self.kind_box.currentIndexChanged.connect(self.on_kind)
        form.addRow(self.t("mc_fire_kind"), self.kind_box)
        self.kind_note = cards.note(self.t("mc_fire_kind_locked"))
        form.addRow("", self.kind_note)
        self.duration_spin = self.spin(0.0, 240.0, 0, 30.0, " min")
        self.duration_spin.valueChanged.connect(self.on_duration)
        form.addRow(self.t("mc_fire_duration"), self.duration_spin)
        self.duration_note = self.orange_note()
        self.duration_back = self.take_back_button(self.take_back_duration)
        self.duration_line = self.row_with_back(form, self.duration_note, self.duration_back)
        sides = QWidget()
        row = QHBoxLayout(sides)
        row.setContentsMargins(0, 0, 0, 0)
        self.side_boxes = {}
        for side in sia265.FIRE_SIDES:
            check = QCheckBox(self.t(SIDE_WORDS[side]))
            check.toggled.connect(self.touch)
            row.addWidget(check)
            self.side_boxes[side] = check
        row.addStretch(1)
        form.addRow(self.t("mc_fire_sides"), sides)
        self.wood_box = QComboBox()
        for wood, words in WOODS:
            self.wood_box.addItem(self.t(words), wood)
        self.wood_box.currentIndexChanged.connect(self.touch)
        form.addRow(self.t("mc_fire_wood"), self.wood_box)
        self.top_box = QCheckBox(self.t("mc_fire_top"))
        self.top_box.toggled.connect(self.on_duration_source)
        form.addRow("", self.top_box)
        form.addRow("", cards.note(self.t("mc_fire_hint")))
        self.form.addWidget(box)

        # the effort: every kind's rows, built once and shown by the kind
        self.effort_card(self.N_KEY)
        effort = self.effort_form
        effort.setRowVisible(self.row_of(self.alpha_spin), False)     # along the grain: alpha is 0
        self.extra_spins = {}
        for key, words, unit in (("M_y", "mc_My_fire", "kNm"), ("M_z", "mc_Mz_fire", "kNm"), ("V_z", "mc_Vz_fire", "kN"), ("V_y", "mc_Vy_fire", "kN")):
            spin = self.spin(0.0, 1_000_000.0, 2, 0.5, " " + unit)
            spin.valueChanged.connect(self.touch)
            effort.addRow(self.t(words), self.linked(spin, key, unit, key))
            self.extra_spins[key] = spin
        self.build_lengths()

        # the building, the project's (D-10)
        box = cards.card(self.t("mc_box_building"))
        building = cards.form(box)
        self.building_form = building
        self.building_boxes = {}
        for key in vkf.BUILDING_KEYS:
            combo = QComboBox()
            combo.addItem(self.t("mc_building_none"), None)
            for value in vkf.building_ids(key):
                combo.addItem(self.t(AEAI_WORDS[key][value]), value)
            combo.currentIndexChanged.connect(self.on_building)
            building.addRow(self.t(BUILDING_LABELS[key]), combo)
            self.building_boxes[key] = combo
        self.building_line = cards.note("")
        building.addRow("", self.building_line)
        building.addRow("", cards.note(self.t("mc_building_hint")))
        save = QPushButton(self.t("mc_building_save"))
        save.clicked.connect(self.save_building)
        building.addRow("", save)
        self.form.addWidget(box)
        self.fill_building()

    # --- the building ----------------------------------------------------------------------

    def fill_building(self):
        """The card filled from Woodcore-Datei/building.json -- left empty where the file is absent or cannot be read (a defect the export says, naming the field)."""
        try:
            self.building_data = member_check.read_building(project.current())
        except (validation.ValidationError, OSError, ValueError):
            self.building_data = None
        for key, combo in self.building_boxes.items():
            combo.blockSignals(True)
            combo.setCurrentIndex(max(combo.findData((self.building_data or {}).get(key)), 0))
            combo.blockSignals(False)
        self.building_dirty = False

    def building(self):
        """The building as the card holds it -- None until its four fields are chosen."""
        values = {key: combo.currentData() for key, combo in getattr(self, "building_boxes", {}).items()}
        if not values or any(value is None for value in values.values()):
            return None
        return values

    def on_building(self, *_args):
        self.building_dirty = True
        self.on_duration_source()

    def save_building(self):
        """«Enregistrer le bâtiment»: the card into Woodcore-Datei/building.json, then the checks exported again -- every check that follows VKF 15-15 takes the new duration."""
        building = self.building()
        if building is None:
            return self.fail(self.t("mc_building_incomplete"))
        try:
            self.building_data = member_check.write_building(building, project.current())
        except (validation.ValidationError, OSError) as exc:
            return self.fail(self.t("mc_invalid", error=str(exc)))
        self.building_dirty = False
        self.export(self.t("mc_building_saved"))
        self.app.update_tab_marks()
        return True

    def save(self):
        """Ctrl+S: the building where its card changed, then the check."""
        if self.building_dirty and self.building() is not None and not self.save_building():
            return False
        done = super().save()
        self.update_effort_view()      # saved: the kind is closed
        return done

    # --- the duration -------------------------------------------------------------------

    def requirement(self):
        """What VKF 15-15 requires of the check being edited: `vkf.required_resistance` for the card's building and the check's top storey, None without a building."""
        building = self.building()
        return vkf.required_resistance(building, self.top_box.isChecked()) if building else None

    def notes_text(self, requirement):
        if requirement and requirement.get("exemption"):
            return ", " + requirement["exemption"]
        return self.t("mc_fire_notes", notes=", ".join("[%s]" % n for n in requirement["notes"])) if requirement and requirement["notes"] else ""

    def on_duration(self, *_args):
        """The duration typed: it is written over now."""
        if self.loading:
            return
        self.duration_stated = True
        self.fill_notes()
        self.touch()

    def take_back_duration(self):
        self.duration_stated = False
        self.fill_notes()
        self.touch()

    def on_duration_source(self, *_args):
        """The building or the top storey changed: a duration that follows takes what is now required."""
        if self.loading:
            return
        self.fill_notes()
        self.touch()

    def fill_effort_notes(self):
        """The duration's field and line, and the building's line: what VKF 15-15 requires, followed or written over."""
        requirement = self.requirement()
        override = theme.colour("override")
        minutes = requirement["minutes"] if requirement else None
        if self.duration_stated:
            self.duration_spin.setSuffix(" min")
            self.duration_spin.setSpecialValueText("")
        elif minutes:
            self.duration_spin.setValue(minutes)
            self.duration_spin.setSuffix(self.t("mc_fire_follows", table=requirement["table"]))
            self.duration_spin.setSpecialValueText("")
        else:
            self.duration_spin.setValue(0)
            self.duration_spin.setSpecialValueText(self.t("mc_none"))
        text, back = "", False
        if self.duration_stated and minutes:
            text, back = self.t("mc_fire_overridden", minutes=minutes, table=requirement["table"], row=requirement["row"], notes=self.notes_text(requirement)), True
        elif not self.duration_stated and requirement is None:
            text = self.t("mc_fire_no_building")
        elif not self.duration_stated and minutes == 0:
            text = self.t("mc_fire_no_requirement", table=requirement["table"], notes=self.notes_text(requirement))
        elif not self.duration_stated and minutes is None:
            text = self.tl(requirement["reason"] or "")
        self.duration_note.setText(text)
        self.duration_note.setStyleSheet("color: %s;" % override)
        self.duration_back.setVisible(back)
        self.fire_form.setRowVisible(self.duration_line, bool(text))
        self.building_line.setText(self.t("mc_building_requirement", minutes=minutes, table=requirement["table"], row=requirement["row"])
                                   if requirement and minutes is not None else "")
        self.update_effort_view()

    # --- the kind ---------------------------------------------------------------------------

    def on_kind(self, *_args):
        if self.loading:
            return
        self.update_effort_view()
        self.touch()

    def update_effort_view(self, *_args):
        """The rows of the kind chosen, the others hidden and kept; the force signed for a bending alone; the kind closed once the check is saved."""
        kind = self.current_kind()
        effort = self.effort_form
        effort.setRowVisible(self.row_of(self.n_spin), kind != "shear")
        self.n_spin.setMinimum(self.N_MIN if kind == "bending" else 0.0)
        for key, spin in self.extra_spins.items():
            effort.setRowVisible(self.row_of(spin), (kind == "bending" and key in ("M_y", "M_z")) or (kind == "shear" and key in ("V_z", "V_y")))
        self.lengths_card.setVisible(kind == "buckling")
        saved = self.current_id is not None
        self.kind_box.setEnabled(not saved)
        self.fire_form.setRowVisible(self.kind_note, saved)

    # --- the draft <-> the form -------------------------------------------------------------

    def fill_effort(self, s):
        self.kind_box.setCurrentIndex(max(self.kind_box.findData(s.get("kind") or self.KIND), 0))
        super().fill_effort(s)
        self.alpha_spin.setValue(0.0)
        for key, spin in self.extra_spins.items():
            spin.setValue(abs(float((s.get(key) or {}).get("value") or 0)))
        self.fill_lengths(s)
        fire = s.get("fire") or member_check.FIRE_DEFAULT
        self.duration_stated = fire.get("duration") is not None
        if self.duration_stated:
            self.duration_spin.setValue(float(fire["duration"]))
        for side, check in self.side_boxes.items():
            check.setChecked(bool((fire.get("sides") or {}).get(side)))
        self.wood_box.setCurrentIndex(max(self.wood_box.findData(fire.get("wood")), 0))
        self.top_box.setChecked(bool(fire.get("top_level")))
        self.update_effort_view()

    def draft_effort(self, s):
        kind = self.current_kind()
        s["alpha"] = 0
        for key in KIND_FIELDS:
            s.pop(key, None)
        if kind == "shear":
            s.pop("N", None)
            for key in ("V_z", "V_y"):
                value = self.extra_spins[key].value()
                s[key] = {"value": value, "unit": "kN"} if value else None
            s["pith"] = False
        else:
            s["N"] = {"value": self.n_spin.value(), "unit": "kN"}
        if kind == "bending":
            for key in ("M_y", "M_z"):
                value = self.extra_spins[key].value()
                s[key] = {"value": value, "unit": "kNm"} if value else None
        if kind == "buckling":
            self.draft_lengths(s)
        duration = int(round(self.duration_spin.value()))
        s["fire"] = {"duration": duration if self.duration_stated and duration > 0 else None,
                     "sides": {side: check.isChecked() for side, check in self.side_boxes.items()},
                     "wood": self.wood_box.currentData(),
                     "top_level": self.top_box.isChecked()}

    def view_state(self):
        state = super().view_state()
        state["building"] = self.building() if self.building_dirty else None
        return state

    def restore(self, state):
        super().restore(state)
        building = (state or {}).get("building")
        if building:
            for key, combo in self.building_boxes.items():
                combo.setCurrentIndex(max(combo.findData(building.get(key)), 0))
            self.building_dirty = True
            self.fill_notes()
            self.refresh()
