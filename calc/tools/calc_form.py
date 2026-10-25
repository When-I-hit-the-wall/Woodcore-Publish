"""The declared form of a tab of calculation, a service (spec docs/requirements/completed/2026-10-23-onglets-types-et-services.md, ARCH-001; spec 2026-10-22-onglet-neige-type, ARCH-003; spec 2026-10-23-neige-correctifs-issues-96-99, UI-004, UI-005).

The domain declares its sections and its fields (calc/domains/contracts.py `Declaration`); this service draws them: each section a card of the accordion, numbered, its header saying what its fields hold and a dot green, orange or red after their messages, folded on its own and kept per tab on this machine (layout_store `sections`); each field a calc_fields.FieldWidget with its ⓘ, several fields on one line where the section groups them (b · d · h), and the blocks it declares between them -- a text, a drawing, a coloured table, a formula, a field set on the line of a text -- each a widget of calc_blocks, refreshed in the phase `computed` (spec 2026-10-23-onglet-vent-briques, ARCH-003, ARCH-RISK-014). It contributes the form's part of the draft (`fill`, `collect`), shows again the rows the source shows (`visible_fields`) once the domain has spoken (phase `computed`), lights a field and the results it goes into when the pointer is on it, and takes the engineer to a field a message names (the context's `focusRequested`). No word, no number and no rule of a domain here (tests/test_calc_tab_base.py).
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QToolButton, QVBoxLayout, QWidget

import cards
import layout_store
import richtext
import theme
from tab_host import Hover, Service


class _SectionHeader(QFrame):
    """A section's header: a click anywhere on it folds or unfolds the section."""

    def __init__(self, section):
        super().__init__()
        self.section = section
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        self.section.set_folded(not self.section.folded)
        event.accept()


class Section:
    """One section of the form as an accordion (UI-005 of the spec 2026-10-23-neige-correctifs-issues-96-99, the wind prototype's): a card whose header says its number, its title, what its fields hold, a dot green, orange or red after its fields' messages, and ▾/▸; folded, its rows hide and the header stays. `owner` gives the words (`t`) and keeps the folding (`save_sections`)."""

    def __init__(self, owner, sid, number, title):
        self.owner, self.id = owner, sid
        self.box = cards.card()
        self.box.setObjectName("calcSection")
        column = QVBoxLayout(self.box)
        column.setContentsMargins(10, 8, 10, 8)
        column.setSpacing(6)
        self.header = _SectionHeader(self)
        row = QHBoxLayout(self.header)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        self.number = QLabel(str(number))
        self.number.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.number.setFixedSize(22, 22)
        self.number.setStyleSheet("background: %s; color: %s; border-radius: 6px; font-weight: 700;" % (theme.colour("bg-sunk"), theme.colour("ink-soft")))
        self.title = QLabel(title)
        self.title.setStyleSheet("font-weight: 600;")
        self.summary = QLabel("")
        self.summary.setTextFormat(Qt.TextFormat.RichText)
        self.summary.setStyleSheet("color: %s;" % theme.colour("muted"))
        self.summary.setMinimumWidth(0)
        self.summary.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.dot = QLabel("●")
        self.fold_button = QToolButton()
        self.fold_button.setAutoRaise(True)
        self.fold_button.clicked.connect(lambda: self.set_folded(not self.folded))
        row.addWidget(self.number)
        row.addWidget(self.title)
        row.addWidget(self.summary, 1)
        row.addWidget(self.dot)
        row.addWidget(self.fold_button)
        column.addWidget(self.header)
        self.body = QWidget()
        column.addWidget(self.body)
        self.form = cards.form(self.body)
        self.form.setContentsMargins(0, 0, 0, 0)
        self.folded = False
        self.severity = "ok"
        self.set_folded(False, save=False)

    def set_folded(self, folded, save=True):
        self.folded = bool(folded)
        self.body.setVisible(not self.folded)
        self.fold_button.setText("▸" if self.folded else "▾")
        self.fold_button.setToolTip(self.owner.t("ct_unfold" if self.folded else "ct_fold"))
        if save:
            self.owner.save_sections()

    def set_state(self, summary, severity):
        """Its header's words and dot: `severity` "error" red, "info" orange, else green."""
        self.summary.setText(summary)
        self.summary.setToolTip(summary)
        self.severity = severity
        colour = {"error": "danger", "info": "warning"}.get(severity, "ok")
        self.dot.setStyleSheet("color: %s;" % theme.colour(colour))


class DeclaredForm(Service):
    """The form a domain declares -- see the module's docstring. It is the holder calc_fields.FieldWidget reads its tab's words, bubbles and linkable numbers off."""

    NAME = "form"
    WORDS_MODULE = "calc_tab_words"
    ZONE = "centre"
    NEEDS = ("declaration", "visible_fields")

    def mount(self, ctx):
        super().mount(ctx)
        decl = ctx.declaration()
        self.fields, self.rows, self.sections, self.blocks = {}, {}, {}, {}
        holder = QWidget()
        column = QVBoxLayout(holder)
        column.setContentsMargins(0, 0, 0, 0)
        folded = set(layout_store.get_state(ctx.key, ctx.layout).get("sections", ()))
        for number, (section, keys) in enumerate(decl.sections, 1):
            part = Section(self, section, number, self.t(decl.prefix + "s_" + section))
            self.sections[section] = part
            for entry in keys:
                if isinstance(entry, tuple):
                    self._line(part, entry, decl)
                elif decl.block(entry) is not None:
                    self._block(part, decl.block(entry), decl)
                else:
                    field = self._field(entry, decl)
                    part.form.addRow(field.label, field.widget)
                    self.rows[entry] = (part.form, field.widget)
            part.set_folded(section in folded, save=False)
            column.addWidget(part.box)
        ctx.lit.connect(self.set_lit)
        ctx.focusRequested.connect(self.focus_field)
        return holder

    def _field(self, key, decl):
        """The widget of the field `key`, hovered as a field (UI-004)."""
        import calc_fields
        field = calc_fields.FieldWidget(self, decl.field(key), decl)
        self.fields[key] = field
        for widget in (field.label, field.widget):
            widget.installEventFilter(Hover(widget, lambda k=key: self.ctx.hover_field(k), lambda: self.ctx.hover_field(None)))
        return field

    def _line(self, part, keys, decl):
        """Several fields on one row of the section (b · d · h, ARCH-RISK-014): each its words, its ⓘ and its widget, side by side; the row shown while one of them is."""
        line = QWidget()
        row = QHBoxLayout(line)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        for i, key in enumerate(keys):
            field = self._field(key, decl)
            if i:
                row.addWidget(QLabel("·"))
            row.addWidget(field.label)
            row.addWidget(field.widget)
        row.addStretch(1)
        part.form.addRow(line)
        for key in keys:
            self.rows[key] = (part.form, line)

    def _block(self, part, block, decl):
        """A block of the section (ARCH-003): its widget from calc_blocks, a row_select holding the widget of its field, which the form fills and collects as any other."""
        import calc_blocks
        field_widget = None
        if block.kind == "row_select":
            field = self._field(block.field, decl)
            field_widget = field.widget
        widget = calc_blocks.make(block, self.ctx, field_widget)
        part.form.addRow(widget)
        self.blocks[block.key] = widget
        if block.kind == "row_select":
            self.rows[block.field] = (part.form, widget)

    # --- what calc_fields.FieldWidget reads off its holder --------------------------------

    MODULE = property(lambda self: self.ctx.module)
    loading = property(lambda self: self.ctx.loading)
    bubbles = property(lambda self: self.ctx.bubbles)

    def tl(self, text):
        return self.ctx.tl(text)

    def declaration(self):
        return self.ctx.declaration()

    def touch(self, *_ignored):
        self.ctx.touch()

    def linked(self, spin, key, unit, label, store=True):
        return self.ctx.links.linked(spin, key, unit, label, store)

    def field_changed(self, key):
        """A choice made -- a button, a tile -- the rows the source shows again (a roof's slopes), then the draft computed."""
        self.update_rows(self.ctx.draft())
        self.ctx.touch()

    # --- the contribution to the draft ----------------------------------------------------

    def fill(self, src):
        for field in self.fields.values():
            field.fill(src)
        self.update_rows(src)
        self.update_choices(src)

    def update_choices(self, src):
        """What the choices of the form are worth for the draft, where the domain says it (`choice_values`, optional: a member check's cards of f_c,90,d, issue #112) -- every field of buttons it names, the others given back their words alone."""
        say = getattr(self.ctx.module, "choice_values", None)
        if say is None or not src:
            return
        values = say(src)
        for key, field in self.fields.items():
            field.set_choice_values(values.get(key) or {})

    def collect(self, src):
        for field in self.fields.values():
            field.draft(src)

    # --- the phase `computed`: the domain has spoken --------------------------------------

    def computed(self):
        # the rows follow the draft at every computation: a choice of another service may show some (a member check's material: a panel shows no angle, issue #112)
        if self.ctx.computed_source:
            self.update_rows(self.ctx.computed_source)
            self.update_choices(self.ctx.computed_source)
        self.update_sections(self.ctx.computed_source)
        for widget in self.blocks.values():
            widget.refresh()

    def update_rows(self, src):
        visible = set(self.ctx.module.visible_fields(src))
        shown = {}
        for key, (form, widget) in self.rows.items():
            shown[widget] = (form, shown.get(widget, (form, False))[1] or key in visible)   # a line of fields shown while one of them is
        for widget, (form, on) in shown.items():
            form.setRowVisible(widget, on)
        # a section none of whose fields the source shows, and that holds no block, is hidden whole (a buckling's contact, issue #112)
        decl = self.ctx.declaration()
        for sid, keys in decl.sections:
            entries = decl.section_keys(keys)
            if any(decl.block(k) is not None for k in entries):
                continue
            self.sections[sid].box.setVisible(any(k in visible for k in entries))

    def field_of(self, key):
        """The field of the form a message names: its own key, or the free value a field writes (C_e's `c_e`, Δh's `delta_h`)."""
        if key in self.fields:
            return key
        return next((k for k, f in self.fields.items() if f.field.free_key and f.field.free_key == key), None)

    def section_of(self, key):
        """The section a field is in: among its entries, on a line of them, or set by a row_select."""
        decl = self.ctx.declaration()

        def holds(keys):
            entries = decl.section_keys(keys)
            return key in entries or any(decl.block(k) is not None and decl.block(k).field == key for k in entries)
        return next((sid for sid, keys in decl.sections if holds(keys)), None)

    def focus_field(self, key):
        """A message clicked (T49): its section opened (UI-005), its field shown, given the focus, flashed."""
        key = self.field_of(key)
        field = self.fields.get(key)
        if field is None:
            return
        section = self.sections.get(self.section_of(key))
        if section is not None and section.folded:
            section.set_folded(False)
        field.focus()
        field.blink()

    def update_sections(self, src):
        """Each section's header: what its fields shown hold, its short words before each value where the tab has them (`<prefix>fs_<key>`), and its dot after its fields' messages."""
        decl = self.ctx.declaration()
        visible = set(self.ctx.module.visible_fields(src))
        worst = {}
        for m in self.ctx.messages:
            key = self.field_of(m.field) if m.field else None
            sid = self.section_of(key) if key else None
            if sid is not None and worst.get(sid) != "error":
                worst[sid] = "error" if m.severity == "error" else "info"
        for sid, keys in decl.sections:
            parts = []
            for key in decl.section_keys(keys):
                if key not in self.fields or key not in visible:
                    continue
                said = self.fields[key].summary(src)
                if not said:
                    continue
                try:
                    short = self.t(decl.prefix + "fs_" + key)
                except KeyError:
                    short = ""
                parts.append(richtext.subscripts(short) + " " + richtext.escape(said) if short else richtext.escape(said))
            self.sections[sid].set_state(" · ".join(parts), worst.get(sid, "ok"))

    def save_sections(self):
        """The sections folded, kept for this tab on this machine beside its modules' order (layout_store)."""
        layout_store.put_state(self.ctx.key, {"sections": [sid for sid, s in self.sections.items() if s.folded]}, self.ctx.layout)

    def set_lit(self, fields, _names):
        for key, field in self.fields.items():
            field.set_lit(key in fields)
