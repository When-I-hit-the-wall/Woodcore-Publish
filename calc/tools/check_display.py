"""«Affichage» of a member check, a service (spec docs/requirements/completed/2026-10-24-verifications-elements-v3.md, UI-013, REQ-010, ARCH-005, ARCH-010; issue #112).

The type's «Affichage» (calc_display.DomainDisplay): the check's file compiled by Typst -- never a sketch (D-11) --, the command to copy, `#include domain-file("check", "<id>")`, the file as Woodcore writes it and its elements. What differs is **where an option is kept**: a check keeps the options of its «Affichage» in its **source** (`display`: the report's level 0 to 3 or auto, the member's line none or printed from a level, the verdict as a ratio or in percent, the description and the title printed) and nowhere else -- the file is written from it at every save (unfold.check_header, unfold_display.apply_check_display), so that an option is changed in one place (ARCH-010). Each choice here writes the source and saves the check (`write_check_display`, guarded); the domain's level of the type writes the same (`write_domain_level`).
"""

from PySide6.QtWidgets import QButtonGroup, QCheckBox, QComboBox, QHBoxLayout, QLabel, QPushButton

import domain_file_display
from calc_display import DomainDisplay
from domains import member_check_material as mm


class CheckSource(domain_file_display.CaseSource):
    """The check's file, as the type reads a case's, and the options of its source under the domain's level (`extra`)."""

    def extra(self, body, header):
        view = self.view
        service = view.tab
        t = service.t
        display = mm.display_of(service.ctx.source or {})
        for button in getattr(view, "level_buttons", {}).values():
            button.setVisible(False)   # the level is the source's: the row below, with its 0
        row = QHBoxLayout()
        row.addWidget(QLabel(t("vc_display_level")))
        group = QButtonGroup(view.card)
        view.check_level_buttons = {}
        for value in (None, 0, 1, 2, 3):
            button = QPushButton(t("ct_level_auto") if value is None else str(value))
            button.setCheckable(True)
            button.setChecked(display["level"] == value)
            button.setToolTip(t("vc_display_level_tip"))
            button.clicked.connect(lambda _c=False, v=value: service.write_check_display("level", v))
            group.addButton(button)
            row.addWidget(button)
            view.check_level_buttons[value] = button
        row.addStretch(1)
        body.addLayout(row)
        line = QHBoxLayout()
        line.addWidget(QLabel(t("vc_display_member_line")))
        combo = QComboBox()
        for value in (None, "none", 1, 2, 3):
            combo.addItem(t("vc_display_member_" + ("auto" if value is None else str(value))), value)
        combo.setCurrentIndex(max(combo.findData(display["member_line"]), 0))
        combo.currentIndexChanged.connect(lambda _i: service.write_check_display("member_line", combo.currentData()))
        line.addWidget(combo, 1)
        body.addLayout(line)
        view.member_line_combo = combo
        verdict = QHBoxLayout()
        verdict.addWidget(QLabel(t("vc_display_verdict")))
        choice = QComboBox()
        choice.addItem(t("vc_display_verdict_percent"), "percent")
        choice.addItem(t("vc_display_verdict_ratio"), "ratio")
        choice.setCurrentIndex(max(choice.findData(display["verdict"]), 0))
        choice.currentIndexChanged.connect(lambda _i: service.write_check_display("verdict", choice.currentData()))
        verdict.addWidget(choice, 1)
        body.addLayout(verdict)
        view.verdict_combo = choice
        for key in ("description", "title"):
            box = QCheckBox(t("vc_display_" + key))
            box.setChecked(bool(display[key]))
            box.toggled.connect(lambda on, k=key: service.write_check_display(k, bool(on)))
            body.addWidget(box)
            setattr(view, key + "_box", box)


class CheckDisplay(DomainDisplay):
    """«Affichage» of a member check -- see the module's docstring."""

    NAME = "display"
    WRITERS = ("write_line_display", "write_figure", "write_table", "write_domain_level", "write_check_display")

    def mount(self, ctx):
        self.ctx = ctx
        self.view = domain_file_display.DomainFileDisplay(self, ctx.key, parent=ctx.host, source=CheckSource)
        return None

    def write_check_display(self, name, value):
        """One option of «Affichage» written into the check's source -- the default taken out, so that a source without options stays as it was -- and the check saved: its file follows (REQ-010)."""
        ctx = self.ctx
        if ctx.loading or ctx.current_id is None:
            return False
        held = dict(ctx.source or {})
        display = dict(held.get("display") or {})
        if value == mm.DISPLAY_DEFAULT.get(name):
            display.pop(name, None)
        else:
            display[name] = value
        if display:
            held["display"] = display
        else:
            held.pop("display", None)
        ctx.source = held   # the draft is the source and the form's parts over it: the option goes with the next save, which follows at once
        ctx.dirty = True
        ok = ctx.save()
        self.view.rebuild()
        self.view.refresh()
        return ok

    def write_domain_level(self, level):
        """The domain's level of the type, kept in the source as every option of a check's «Affichage» (ARCH-010)."""
        return self.write_check_display("level", level)
