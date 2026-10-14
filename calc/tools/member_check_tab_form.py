"""MemberCheckTab's form and result -- the cards of the middle, the result on the right, the «Affichage» view, the draft read off the form and the form filled from it -- a mixin of methods moved verbatim out of calc/tools/member_check_tab.py (issue #30). MemberCheckTab names it among its bases.
"""

import copy
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QSplitter, QVBoxLayout, QWidget,
)
import build_reference as ref
import cards  # the form and what is read off it in cards, after the website (cards.py)
import display_view  # the «Affichage» view: the options, the call and the compiled page (display_view.py, v0.117)
import identity  # Nom · Description · ID (identity.py)
import richtext  # the call coloured as the site's code, «Copié ✓» once copied (richtext.py)
import theme  # the orange of a value written over (theme.py)
from domains import connector, member_check
from norms import sia265
import display_options  # the level -1 «Sélection manuelle» (issue #20)


KEEP = object()   # fill_positions: keep the position the combo has chosen


def _n(value):
    text = "%.3f" % value
    return text.rstrip("0").rstrip(".") if "." in text else text


def held_section(record):
    """The section a position gives a check -- `{"type": "rec", "b", "h"}` or `{"type": "cir", "d"}`, in mm -- or None where it has none a tension check can use (a plate, a CLT panel, a steel profile, no section at all)."""
    section = (record or {}).get("section") or {}
    if section.get("type") == "rec" and section.get("b") and section.get("h"):
        return {"type": "rec", "b": float(section["b"]), "h": float(section["h"])}
    if section.get("type") == "cir" and section.get("d"):
        return {"type": "cir", "d": float(section["d"])}
    return None


def section_text(section):
    """«100 × 200 mm» or «Ø 200 mm»."""
    if not section:
        return ""
    if section.get("type") == "cir":
        return "Ø %s mm" % _n(section["d"])
    return "%s × %s mm" % (_n(section["b"]), _n(section["h"]))


def _value_text(value):
    """A value of a result as a label writes it: a number to three decimals with a real minus sign, a word as it is."""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return _n(value).replace("-", "−")
    return str(value)


class MemberCheckFormMixin:
    """Methods of member_check_tab.MemberCheckTab, moved verbatim (issue #30): the class names this mixin among its bases."""

    def build_form(self):
        panel = QWidget()
        column = QVBoxLayout(panel)
        column.setContentsMargins(0, 0, 0, 0)
        scroll, self.form = cards.column()
        column.addWidget(scroll, 1)

        # Nom · Description · ID, as every editor tab names its objects
        box = cards.card()
        form = cards.form(box)
        self.identity = identity.IdentityRows(form, self.t, self.touch)
        self.form.addWidget(box)

        # the position it concerns, if any
        box = cards.card(self.t("mc_box_position"))
        form = cards.form(box)
        self.position_box = QComboBox()
        self.position_box.currentIndexChanged.connect(self.on_position)
        form.addRow(self.t("mc_position"), self.position_box)
        self.position_form = form
        self.position_note = self.orange_note()
        form.addRow("", self.position_note)
        form.addRow("", cards.note(self.t(self.POSITION_HINT_KEY)))
        self.form.addWidget(box)

        self.build_material()

        # the effort -- what a kind holds: the angle between the force and the grain, the force, and for a compression the bearing
        self.build_effort()
        self.form.addStretch(1)

        actions = QHBoxLayout()
        revert = QPushButton(self.t("mc_revert"))
        revert.clicked.connect(self.revert)
        save = QPushButton(self.t("mc_save"))
        save.setDefault(True)
        save.clicked.connect(self.save)
        actions.addStretch(1)
        actions.addWidget(revert)
        actions.addWidget(save)
        column.addLayout(actions)
        return panel

    def build_material(self):
        """The cards of what the check is made of -- for a member check its material and its section, each following the position or written over; a steel tab has its own (steel_tab.py)."""
        # the material: the strength class and the moisture class follow the position, and the impact factor is the engineer's
        box = cards.card(self.t("mc_box_material"))
        self.material_form = cards.form(box)
        self.grade_box = QComboBox()
        self.grade_box.addItem("", None)       # the first entry follows the position (fill_notes names it)
        for grade in sia265.grades():
            self.grade_box.addItem(grade, grade)
        self.grade_box.currentIndexChanged.connect(self.on_field)
        self.material_form.addRow(self.t("mc_grade"), self.grade_box)
        self.grade_note = self.orange_note()
        self.grade_back = self.take_back_button(lambda: self.take_back(self.grade_box))
        self.grade_line = self.row_with_back(self.material_form, self.grade_note, self.grade_back)
        self.moisture_box = QComboBox()
        self.moisture_box.addItem("", None)
        for number in sia265.moisture_class_ids():
            self.moisture_box.addItem(str(number), number)
        self.moisture_box.currentIndexChanged.connect(self.on_field)
        self.material_form.addRow(self.t("mc_moisture"), self.moisture_box)
        self.moisture_note = self.orange_note()
        self.moisture_back = self.take_back_button(lambda: self.take_back(self.moisture_box))
        self.moisture_line = self.row_with_back(self.material_form, self.moisture_note, self.moisture_back)
        self.impact_box = QCheckBox(self.t("mc_impact", eta_t=self.decimal(sia265.eta_t(True))))   # η_t is SIA 265's, read from calc/norms/ and never typed into a label
        self.impact_box.toggled.connect(self.touch)
        self.material_form.addRow("", self.impact_box)
        self.form.addWidget(box)

        # the section: b and h of a rectangle or d of a circle, mm
        box = cards.card(self.t("mc_box_section"))
        self.section_form = cards.form(box)
        self.section_box = QComboBox()
        self.section_box.addItem("", None)
        self.section_box.addItem(self.t("mc_rec"), "rec")
        self.section_box.addItem(self.t("mc_cir"), "cir")
        self.section_box.currentIndexChanged.connect(self.on_field)
        self.section_form.addRow(self.t("mc_section_type"), self.section_box)
        self.b_spin = self.spin(1.0, 10000.0, 1, 10.0, " mm")
        self.h_spin = self.spin(1.0, 10000.0, 1, 10.0, " mm")
        self.d_spin = self.spin(1.0, 10000.0, 1, 10.0, " mm")
        for spin, value in ((self.b_spin, 100.0), (self.h_spin, 200.0), (self.d_spin, 200.0)):
            spin.setValue(value)      # what a section chosen starts from where no position gave one: a size in plain view, not a 1 mm minimum nobody meant
        for label_key, widget, key in (("mc_b", self.b_spin, "section.b"), ("mc_h", self.h_spin, "section.h"), ("mc_d", self.d_spin, "section.d")):
            widget.valueChanged.connect(self.on_size)
            self.section_form.addRow(self.t(label_key), self.linked(widget, key, "mm", key[-1]))
        self.section_note = self.orange_note()
        self.section_back = self.take_back_button(lambda: self.take_back(self.section_box))
        self.section_line = self.row_with_back(self.section_form, self.section_note, self.section_back)
        self.form.addWidget(box)

    def effort_card(self, label_key):
        """The card «Effort» every kind starts with: the angle between the force and the grain and the force, kN -- from `N_MIN`, 0 for a magnitude. The force's label is returned beside the card, for a kind whose label changes."""
        box = cards.card(self.t("mc_box_effort"))
        form = cards.form(box)
        self.alpha_spin = self.spin(0.0, 90.0, 1, 5.0, " °")
        self.alpha_spin.valueChanged.connect(self.on_alpha)
        form.addRow(self.t(self.ALPHA_KEY), self.linked(self.alpha_spin, "alpha", "°", "α"))
        self.effort_form = form
        self.n_spin = self.spin(self.N_MIN, 1_000_000.0, 2, 1.0, " kN")
        self.n_spin.valueChanged.connect(self.touch)
        self.n_label = QLabel(self.t(label_key))
        self.n_label.setWordWrap(True)
        form.addRow(self.n_label, self.linked(self.n_spin, "N", "kN", "N"))
        self.form.addWidget(box)
        return box

    def build_effort(self):
        """A kind's card (or cards) of the effort, added to `self.form`."""
        self.effort_card(self.N_KEY)

    def fill_effort(self, s):
        """The effort of the source `s` in the form."""
        self.alpha_spin.setValue(float(s.get("alpha") or 0))
        self.n_spin.setValue(float((s.get("N") or {}).get("value") or 0))

    def draft_effort(self, s):
        """The effort in the draft `s`."""
        s["alpha"] = self.alpha_spin.value()
        s["N"] = {"value": self.n_spin.value(), "unit": "kN"}

    def fill_effort_notes(self):
        """Called by `fill_notes`, the form being loading: what in the effort depends on the position or on the other cards."""

    def on_alpha(self, *_args):
        self.touch()

    def on_size(self, *_args):
        self.touch()

    def build_result(self):
        """The right pane, in the order of the engineer's decision of 07.10.2026: the results (Python, instant), the call to copy, then the options and the Typst preview, both closed until opened."""
        scroll, details = cards.column(margins=(0, 10, 4, 0), hold=False)
        self.message = QLabel("")
        self.message.setTextFormat(Qt.TextFormat.RichText)
        self.message.setWordWrap(True)
        self.message.setProperty("callout", "warning")   # the site's warning callout, inside the pane and never a pop-up
        self.message.setVisible(False)
        details.addWidget(self.message)

        results = cards.card(self.t("mc_results"))
        box = QVBoxLayout(results)
        self.results_label = QLabel("")
        self.results_label.setTextFormat(Qt.TextFormat.RichText)
        self.results_label.setWordWrap(True)
        self.results_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        box.addWidget(self.results_label)
        self.verdict_label = QLabel("")
        self.verdict_label.setTextFormat(Qt.TextFormat.RichText)
        self.verdict_label.setVisible(False)
        box.addWidget(self.verdict_label)
        details.addWidget(results)

        details.addStretch(1)
        return scroll

    def build_display(self):
        """The «Affichage» view: the check's own options -- they also say the unit of the verdict in «Calcul», and the options of the draft the page compiles, which no declaration can (display_view.OwnPanel) -- the call to copy, and the page of the draft, saved or not."""
        body = QWidget()
        form = cards.form(body)
        form.setContentsMargins(0, 0, 0, 0)
        self.options_form = form   # a tab whose command takes fewer options hides their rows (steel_tab.py)
        # the level, and -1 «Sélection manuelle» with a box and a level for every variable the check prints (issue #20): the control every panel of a declaration draws (display_view.LevelControl, rule 16), its variables the check's own (member_check.shown_keys)
        self.level_box = display_view.LevelControl(("auto", "0", "1", "2", "3", display_options.SELECTION), self.t)
        form.addRow(self.t("mc_opt_level"), self.level_box)
        self.member_box = QComboBox()
        self.member_box.addItem(self.t("mc_member_none"), "none")
        for level in (0, 1, 2, 3):
            self.member_box.addItem(str(level), level)
        form.addRow(self.t("mc_opt_member"), self.member_box)
        self.member_box.setCurrentIndex(self.member_box.findData(1))     # the line `#member` prints at level 1, the command's own default
        self.description_box = QCheckBox(self.t("mc_opt_description"))
        form.addRow("", self.description_box)
        self.title_box = QComboBox()
        self.title_box.addItem(self.t("mc_title_auto"), "auto")
        self.title_box.addItem(self.t("mc_title_none"), "none")
        self.title_box.addItem(self.t("mc_title_text"), "text")
        form.addRow(self.t("mc_opt_title"), self.title_box)
        self.title_text = QLineEdit()
        self.title_text.setEnabled(False)
        form.addRow("", self.title_text)
        self.unit_box = QComboBox()
        self.unit_box.addItem(self.t("mc_unit_ratio"), None)
        self.unit_box.addItem(self.t("mc_unit_percent"), "%")
        form.addRow(self.t("mc_opt_unit"), self.unit_box)
        for widget in (self.member_box, self.title_box, self.unit_box):
            widget.currentIndexChanged.connect(self.on_option)
        self.level_box.changed.connect(self.on_option)
        self.description_box.toggled.connect(self.on_option)
        self.title_text.textChanged.connect(self.on_option)
        card = cards.card(self.t("mc_options"))
        QVBoxLayout(card).addWidget(body)
        self.options_panel = display_view.OwnPanel(card)
        self.display = display_view.DisplayView(self.t, mono_font=self.app.mono_font, copy=self.app.copy, cache_key=self.KEY, lang=self.app.lang,
                                                import_fn=lambda: self.app.reexport(), import_text=self.t("reexport"), parent=self)
        self.command_field = self.display.field
        self.copy_button = self.display.copy_button

    @property
    def pane(self):
        """The compiled page of the draft: the «Affichage» view's, made when it is first needed."""
        return self.display.pane

    def display_entries(self):
        """What «Affichage» offers for the check chosen: its own `#show-check-member`, compiled from the draft -- saved or not --, and the loop over every check, which the PDF shows."""
        unsaved = self.current_id is None or self.dirty
        reason = "" if self.record is not None and self.record.get("calculable") else (self.reason or self.t("mc_preview_none"))
        return [
            display_view.Entry("member", "show-check-member", panel=self.options_panel, call_fn=lambda _v: self.command_text(),
                               snippet_fn=lambda _v: self.preview_source(), note_text=reason,
                               banner=self.t("mc_save_first") if unsaved else ""),
            display_view.Entry("loop", self.t("ds_loop", command="show-check-member"), call=ref.call_check_member_loop(), note="ds_note_loop"),
        ]

    def set_view(self, key, enter=True):
        """«Calcul» or «Affichage» (views.py): the list stays, the centre and the right pane change. The page is compiled only in «Affichage», and only once the tab is shown."""
        if key not in self.VIEWS:
            return
        self.view = key
        self.panes.show(key == "display", enter and self.live)
        if key == "display":
            self.fill_command()

    def muted_html(self, text):
        return "<span style='color:%s'>%s</span>" % (theme.colour("muted"), richtext.prose_html(text))

    def fill_results(self):
        """The card «Résultats»: every value of the check as `member_check.compute` gives it -- the symbol as mathematics, the value, its unit, the equation and the clause --, and the verdict with its mark in the `ok` or the `danger` colour. Where the check cannot be calculated, the reason instead."""
        record = self.record
        compute = self.window_result
        self.verdict_label.setVisible(False)
        if record is None or not record.get("calculable") or compute is None:
            self.results_label.setText(self.muted_html(self.reason or self.t("mc_preview_none")))
            return
        try:
            result = compute(record)
        except Exception as exc:  # broad: a result the engine cannot work out is said, never raised through a slot
            self.results_label.setText(richtext.prose_html(self.t("mc_invalid", error=str(exc))))
            return
        if not result:
            self.results_label.setText(self.muted_html(self.reason or self.t("mc_preview_none")))
            return
        muted = theme.colour("muted")
        lines = []
        head = [richtext.escape((self.NORM_PREFIX if str(result["clause"])[:1].isdigit() else "") + str(result["clause"]))] if result.get("clause") else []   # the engine gives the clause alone, «4.2.2.1»
        if result.get("equation"):
            head.append(richtext.math_html(result["equation"]))
        if head:
            lines.append("<p style='color:%s;margin:0 0 4px 0'>%s</p>" % (muted, " — ".join(head)))
        body = []
        for row in result.get("rows") or []:
            unit = (" " + richtext.escape(row["unit"])) if row.get("unit") else ""
            label = ("<td style='padding-left:10px;color:%s'>%s</td>" % (muted, richtext.escape(self.tl(row["label"])))) if row.get("label") else "<td></td>"
            body.append("<tr><td style='padding-right:8px'>%s</td><td style='padding-right:6px'>=</td><td align='right'>%s%s</td>%s</tr>"
                        % (richtext.math_html(row.get("symbol", "")), richtext.escape(_value_text(row.get("value"))), unit, label))
            if row.get("formula"):
                body.append("<tr><td></td><td></td><td colspan='2' style='color:%s'>%s</td></tr>" % (muted, richtext.math_html(row["formula"])))
        lines.append('<table cellspacing="0" cellpadding="1">' + "".join(body) + "</table>")
        self.results_label.setText("".join(lines))
        eta = result.get("eta")
        if eta is not None:
            ok = bool(result.get("ok"))
            colour = theme.colour("ok" if ok else "danger")
            percent = self.unit_box.currentData() == "%"
            # the ratio of the action to the resistance, as the report's verdict prints it (lib/timber.typ timber-verdict, issue #12): `σ/f = 0.41 ⩽ 1 ✔`, in percent `σ/f = 41 % ✔` without «⩽ 100 %» -- never η, which stays the value underneath
            ratio = (richtext.math_html(result["ratio"]) + " = ") if result.get("ratio") else ""   # a result without its ratio's formula shows the value alone, never η
            if percent:
                shown = "%s%s %%" % (ratio, richtext.escape(_n(eta * 100)))
            else:
                shown = "%s%s %s 1" % (ratio, richtext.escape(_n(eta)), "⩽" if ok else ">")   # the sign that holds, as #verify prints it
            self.verdict_label.setText("<span style='color:%s;font-weight:600'>%s &nbsp;%s</span>" % (colour, shown, "✔" if ok else "✘"))
            self.verdict_label.setVisible(True)

    def window_result(self, record):
        """The instant result the card «Résultats» shows -- {clause, equation, rows, eta, ok, ratio} -- or None: member_check.compute for a member check."""
        return member_check.compute(record)

    def fill_positions(self, wanted=KEEP):
        """The positions the export holds, in the combo; a position the export no longer lists is kept and marked `T009 (?)` rather than silently replaced by whichever entry is first -- the plan tab's rule, and it matters here because the replacement would change a check without anyone asking."""
        positions = self.positions()
        wanted = self.position_box.currentData() if wanted is KEEP else wanted
        self.position_box.blockSignals(True)
        self.position_box.clear()
        self.position_box.addItem(self.t("mc_no_position"), None)
        for pid, record in positions.items():
            parts = [self.tl(record.get("type") or ""), record.get("strength_class") or "", connector.position_dimension(record)]
            self.position_box.addItem(" — ".join([pid, " ".join(p for p in parts if p)]) if any(parts) else pid, pid)
        if wanted and wanted not in positions:
            self.position_box.addItem("%s (?)" % wanted, wanted)
        index = self.position_box.findData(wanted)
        self.position_box.setCurrentIndex(index if index >= 0 else 0)
        self.position_box.blockSignals(False)

    def fill_form(self):
        self.loading = True
        s = self.source
        self.identity.fill(s.get("name", ""), s.get("label", ""), s.get("id", ""), saved=self.current_id is not None)
        self.fill_positions(s.get("position"))
        self.fill_material(s)
        self.fill_effort(s)
        self.fill_links(s)
        self.loading = False
        self.fill_notes()

    def fill_material(self, s):
        """The material and the section cards from the source `s`."""
        grade = s.get("grade")
        if grade and self.grade_box.findData(grade) < 0:
            self.grade_box.addItem(grade, grade)     # a class the norm tables do not carry is kept, so the source is not silently changed
        self.grade_box.setCurrentIndex(max(self.grade_box.findData(grade), 0))
        self.moisture_box.setCurrentIndex(max(self.moisture_box.findData(s.get("moisture_class")), 0))
        self.impact_box.setChecked(bool(s.get("impact")))
        section = s.get("section") or {}
        self.section_box.setCurrentIndex(max(self.section_box.findData(section.get("type")), 0))
        for spin, value in ((self.b_spin, section.get("b")), (self.h_spin, section.get("h")), (self.d_spin, section.get("d"))):
            if value:
                spin.setValue(float(value))

    def held(self):
        """What the position chosen holds: (pid, its record) -- (None, None) where none is chosen or the export no longer lists it."""
        pid = self.position_box.currentData()
        record = self.positions().get(pid) if pid else None
        return (pid, record) if record is not None else (None, None)

    def fill_notes(self):
        """Where each value comes from, said the engineer's way: **a value that follows its position says so in its own field** -- «C24 — T001» -- and a line under it appears only where it is written over (orange, with «Reprendre») or its position gone (orange). The spin boxes of a section that follows show the position's and are closed to typing."""
        wanted = self.position_box.currentData()
        pid, record = self.held()
        was_loading, self.loading = self.loading, True
        override = theme.colour("override")

        gone = bool(wanted) and pid is None
        self.position_note.setText(self.t("mc_position_gone", pid=wanted) if gone else "")
        self.position_note.setStyleSheet("color: %s;" % override)
        self.position_form.setRowVisible(self.position_note, gone)
        self.fill_material_notes(pid, record)
        self.fill_effort_notes()
        self.loading = was_loading

    def fill_material_notes(self, pid, record):
        """What the material and section cards say of the position chosen: the first entry of each combo, the orange lines."""
        override = theme.colour("override")
        # the strength class
        held_grade = (record or {}).get("strength_class") or ""
        self._note_for(self.grade_box, self.grade_note, self.grade_back, self.grade_line, self.material_form, pid, held_grade, held_grade,
                       "mc_no_grade", lambda value: value)
        # the moisture class
        held_moisture = (record or {}).get("moisture_class")
        self._note_for(self.moisture_box, self.moisture_note, self.moisture_back, self.moisture_line, self.material_form, pid,
                       "" if held_moisture is None else str(held_moisture), held_moisture, None, lambda value: str(value))
        # the section
        held = held_section(record) if record else None
        following = self.section_box.currentData() is None
        shown = (held or {}).get("type") if following else self.section_box.currentData()
        self.section_box.setItemText(0, cards.followed(section_text(held), pid) if (pid and held) else self.t("mc_none"))
        if following and held:
            for spin, key in ((self.b_spin, "b"), (self.h_spin, "h"), (self.d_spin, "d")):
                if key in held:
                    spin.setValue(held[key])
        for spin in (self.b_spin, self.h_spin, self.d_spin):
            spin.setEnabled(not following)
            self.row_of(spin).set_editable(not following)   # a section that follows its position takes no variable: state it first
        self.section_form.setRowVisible(self.row_of(self.b_spin), shown == "rec")
        self.section_form.setRowVisible(self.row_of(self.h_spin), shown == "rec")
        self.section_form.setRowVisible(self.row_of(self.d_spin), shown == "cir")
        note, back = "", False
        if pid and following and not held:
            note = self.t("mc_no_section", pid=pid)
        elif pid and not following and held:
            note, back = self.t("mc_overridden", pid=pid, value=section_text(held)), True
        self.section_note.setText(note)
        self.section_note.setStyleSheet("color: %s;" % override)
        self.section_back.setVisible(back)
        self.section_form.setRowVisible(self.section_line, bool(note))

    def _note_for(self, box, note_label, back, line, form, pid, held_text, held_value, missing_key, show):
        """One combo whose first entry follows the position: that entry's text, and the line under it."""
        stated = box.currentData()
        box.setItemText(0, cards.followed(held_text, pid) if (pid and held_text) else self.t("mc_none"))
        text, button = "", False
        if pid and stated is None and not held_text and missing_key:
            text = self.t(missing_key, pid=pid)
        elif pid and stated is not None and held_text:
            text, button = self.t("mc_overridden", pid=pid, value=show(held_value)), True
        note_label.setText(text)
        note_label.setStyleSheet("color: %s;" % theme.colour("override"))
        back.setVisible(button)
        form.setRowVisible(line, bool(text))

    def take_back(self, combo):
        """«Reprendre»: the value follows its position again."""
        combo.setCurrentIndex(0)

    def on_position(self, _index=0):
        if self.loading:
            return
        self.fill_notes()
        self.touch()

    def on_field(self, _index=0):
        if self.loading:
            return
        self.fill_notes()
        self.touch()

    def draft(self):
        """The source as the form has it: a value that follows its position is `None`, one that is written over is stated."""
        s = copy.deepcopy(self.source)
        name, description, sid = self.identity.values()
        s["id"], s["name"], s["label"], s["kind"] = sid, name, description, self.current_kind()
        s["position"] = self.position_box.currentData()
        self.draft_material(s)
        self.draft_effort(s)
        self.draft_links(s)
        return s

    def draft_material(self, s):
        """The material and the section into the draft `s`: a value that follows its position is None."""
        s["grade"] = self.grade_box.currentData()
        s["moisture_class"] = self.moisture_box.currentData()
        s["impact"] = self.impact_box.isChecked()
        kind = self.section_box.currentData()
        if kind == "rec":
            s["section"] = {"type": "rec", "b": self.b_spin.value(), "h": self.h_spin.value()}
        elif kind == "cir":
            s["section"] = {"type": "cir", "d": self.d_spin.value()}
        else:
            s["section"] = None
