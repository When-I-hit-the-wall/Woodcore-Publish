"""The position plan's card «Centres S et M» -- the stiffness centre and the mass centre -- and the «Mode de construction» of a bracing wall (issue #54, docs/ui/tab-plans.md §10quater; spec docs/requirements/completed/2026-10-13-plan-positions-centre-rigidite-centre-masse.md, UI-001, UI-003).

The engineer, 12.10.2026: «une case à cocher sur le plan, enregistrée avec lui, décide s'ils apparaissent aussi sur le plan imprimé dans le rapport» -- and, of the CLT, «c'est l'ingénieur qui choisit entre 1,5 et 2 dans Woodcore», answered «sur le plan» on 13.10.2026.

⚠️ Its title and its switch are short on purpose -- «Centres S et M», «Imprimer dans le rapport», what the three are being said in the switch's tip and in the card's own lines: a card's title does not wrap, and written out in full («Centre de rigidité et centre de masse») it made this card the widest of the pane and set the pane's minimum width, 599 px for 495 measured in French (UI-003; tests/test_panes.py).

The card stands among the plan's own modules, shown while nothing is selected (drawing_tab's `when="plan"`), and holds three things: the switch that prints S, M and the outline (`print_centres`); the power of a CLT wall's length (`clt_power`), shown only on a plan whose bracing walls are CLT -- a field with nothing to show for it is no field --; and what the plan's two centres stand on, or why one is not there. It **computes nothing**: what it says is `plan_centres.state`'s, the very sentences the warnings under the plan and the export say (`engine.Note`, written in the window's language by `note_text`), so the card and a warning cannot come to explain one plan two ways.

An elevation section has no stiffness centre: the card is not shown there (`PlanTab.update_modules`). The fire-protection plan has none of this (docs/domain/fire-plans.md §3.3vicies): bracing walls are the position plan's.
"""

from PySide6.QtWidgets import QCheckBox, QComboBox

import cards
from domains import plan_centres
from drawing_tab import number_text


def mode_text(tab, mode):
    """A construction mode in the window's language: the word the warnings name it by (`warn_plan_construction_<mode>`), said once."""
    return tab.app.note_text(plan_centres.mode_note(mode))


def construction_combo(tab, current, chosen):
    """The list «Mode de construction» of a bracing wall or of its tool: «non défini» -- there is no default, and the stiffness centre waits for every wall's --, then the three modes. `chosen(mode)` is called with the mode picked, None for «non défini»."""
    combo = QComboBox()
    combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)   # its longest word does not set the card's width
    combo.setMinimumContentsLength(10)
    combo.addItem(tab.t("plan_construction_none"), None)
    for mode in plan_centres.MODES:
        combo.addItem(mode_text(tab, mode), mode)
    combo.setCurrentIndex(max(0, combo.findData(current)))
    combo.setToolTip(tab.t("plan_construction_tip"))
    combo.activated.connect(lambda _index: chosen(combo.currentData()))
    return combo


class CentresCard:
    """The card, built once with the tab's right pane; `refresh()` after every change of the plan."""

    def __init__(self, tab):
        self.tab = tab
        self.card = cards.card(tab.t("plan_group_centres"))
        self.form = cards.form(self.card)
        self.print_box = QCheckBox(tab.t("plan_print_centres"))
        self.print_box.setToolTip(tab.t("plan_print_centres_tip"))
        self.print_box.toggled.connect(self.on_print)
        self.form.addRow(self.print_box)
        self.power = QComboBox()
        self.power.addItem(tab.t("plan_clt_power_none"), None)
        for power in plan_centres.POWERS["clt"]:
            self.power.addItem(number_text(power), power)
        self.power.setToolTip(tab.t("plan_clt_power_tip"))
        self.power.activated.connect(self.on_power)
        self.form.addRow(tab.t("plan_clt_power"), self.power)
        self.stiffness = tab.note("")
        self.mass = tab.note("")
        self.form.addRow(self.stiffness)
        self.form.addRow(self.mass)

    def on_print(self, checked):
        """The switch: written where it is on and taken out where it is off -- a plan that prints none is the file it was."""
        def apply():
            if checked:
                self.tab.source["print_centres"] = True
            else:
                self.tab.source.pop("print_centres", None)
        self.tab.edit(apply)

    def on_power(self, _index):
        power = self.power.currentData()

        def apply():
            if power is None:
                self.tab.source.pop("clt_power", None)
            else:
                self.tab.source["clt_power"] = power
        self.tab.edit(apply)

    def refresh(self):
        """The card as the plan now stands: the switch, the power where the walls are CLT, and what S and M stand on or why they are not there."""
        tab, source = self.tab, self.tab.source
        was, tab.loading = tab.loading, True
        try:
            self.print_box.setChecked(bool(source.get("print_centres")))
            self.power.setCurrentIndex(max(0, self.power.findData(source.get("clt_power"))))
        finally:
            tab.loading = was
        clt = any(wall["construction"] == "clt" for wall in plan_centres.walls(source))
        self.form.setRowVisible(self.power, clt or "clt_power" in source)
        found = plan_centres.state(source)
        s = found["stiffness"]
        if s is not None:
            lines = [tab.t("plan_centres_stiffness", walls=s["walls"], mode=mode_text(tab, s["construction"]), power=number_text(s["power"]))]
            lines += [tab.app.note_text(note) for note in found["remarks"]]
        else:
            lines = [tab.app.note_text(found["stiffness_note"])] if found["stiffness_note"] is not None else []
        self.stiffness.setText("\n".join(lines))
        self.mass.setText(tab.t("plan_centres_mass") if found["mass"] is not None else (tab.app.note_text(found["mass_note"]) if found["mass_note"] is not None else ""))
