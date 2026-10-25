"""The fields of a calculation tab's form, drawn from its domain's declaration (spec 2026-10-22-onglet-neige-type, UI-002, ARCH-002; calc/domains/contracts.py `Field`).

One widget per kind of field, each with its words and its ⓘ beside it (T24), what it reads from a source (`fill`) and writes into a draft (`draft`), and how it is shown to the engineer a message names it (`blink`):

* **number** -- a number with its unit; one the domain may link to a variable of the export carries the button of issue #42 (`LoadTab.linked`, linkable_spin); one with a `special_word` a check box beside it that writes null in its place («z = h», spec 2026-10-23-onglet-vent-briques, ARCH-RISK-014);
* **buttons** -- buttons that say what they are worth («abrité 1.2»), and where the field takes one a value of the engineer's own beside them (`free_id`, `free_key`: C_e's), taken as it is (D-10);
* **tiles** -- one drawn tile a choice (the five roofs, T39), each with the bubble of its own excerpts and no words (T28);
* **checkbox**, and **select**, a drop-down list (the wind's tables of Annexe C, when the wind is built on this base).

A form that is not declared -- the layers of a permanent load -- is no kind of field: its tab takes a service of its own in place of the declared form (calc_tab.swap, spec 2026-10-23-onglets-types-et-services).

The words: the field's `<prefix>f_<key>`, a choice's glossary term (`tab.tl`), its number and unit. Colours are the theme's (the accent of a tile chosen, `lit` for the blink). No word of a domain here.
"""

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox, QHBoxLayout, QLabel, QPushButton, QToolButton,
                               QVBoxLayout, QWidget)

import richtext
import theme
from norm_bubble import InfoMark

from blink import BLINK_MS, BLINKS, Blinker  # noqa: E402,F401  -- a field named by a message flashes as a module of a pane does, one helper (issue #110)
TILE = QSize(98, 64)


def _n(value):
    text = ("%.3f" % value).rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


def choice_text(tab, field, choice):
    """What a button says: its word and the number it is worth («windgeschützt 1.2» in the window's language), or its number and the field's unit alone («± 0 m», «+200 m» where the choices run either side of 0)."""
    signed = any(isinstance(c.value, (int, float)) and c.value < 0 for c in field.choices)
    number = ""
    if isinstance(choice.value, (int, float)):
        number = ("± 0" if choice.value == 0 else "%+g" % choice.value) if signed else _n(choice.value)
        number += (" " + field.unit) if field.unit else ""
    if choice.word:
        prefix = tab.declaration().prefix
        word = tab.t(choice.word) if choice.word.startswith(prefix) else tab.tl(choice.word)   # a word of the tab's, else a term of the glossary
        return (word + (" " + number if number else "")).strip()
    return number or str(choice.id)


def svg_icon(svg, size=TILE):
    """A drawing as an icon of `size`."""
    pixmap = QPixmap(size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    QSvgRenderer(QByteArray(svg.encode("utf-8"))).render(painter)
    painter.end()
    return QIcon(pixmap)


class FieldWidget:
    """One field of the form: `label` (its words and ⓘ) and `widget` (what the form's row holds), `fill(src)`, `draft(src)`, `focus()`, `blink()`."""

    def __init__(self, tab, field, declaration):
        self.tab, self.field, self.declaration = tab, field, declaration
        t = tab.t
        self.label = QWidget()
        row = QHBoxLayout(self.label)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(2)
        # its symbols with their subscripts, C<sub>e</sub> and not «C_e» (UI-003 of the spec 2026-10-23-neige-correctifs-issues-96-99)
        self.words = QLabel(richtext.subscripts(t(declaration.prefix + "f_" + field.key)))
        self.words.setTextFormat(Qt.TextFormat.RichText)
        row.addWidget(self.words)
        self.info = InfoMark(t("ct_info_tip"))
        if field.excerpts:
            row.addWidget(self.info)
            tab.bubbles.attach(self.info, declaration.norm, field.excerpts)
        row.addStretch(1)
        self.focus_target = None
        self.free_active = False
        self.special = None
        builder = getattr(self, "_build_" + field.kind)
        self.widget = builder()
        self._blinker = Blinker(self.widget)

    # -- the kinds --

    def _build_number(self):
        f = self.field
        spin = QDoubleSpinBox()
        spin.setRange(f.minimum, f.maximum)
        spin.setDecimals(f.decimals)
        spin.setSingleStep(f.step)
        if f.unit:
            spin.setSuffix(" " + f.unit)
        spin.setMinimumWidth(90)
        spin.valueChanged.connect(self.tab.touch)
        self.spin = spin
        self.focus_target = spin
        shown = self.tab.linked(spin, f.key, f.unit, f.key) if f.linkable else spin
        if not f.special_word:
            return shown
        holder = QWidget()
        row = QHBoxLayout(holder)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        self.special = QCheckBox(richtext.plain_math(self.tab.t(self.declaration.prefix + f.special_word)))
        self.special.toggled.connect(self._special_toggled)
        row.addWidget(self.special)
        row.addWidget(shown)
        row.addStretch(1)
        return holder

    def _special_toggled(self, on):
        """The special value chosen -- «z = h» --: the number put aside, null written in its place."""
        self.spin.setEnabled(not on)
        self.tab.touch()

    def _build_buttons(self):
        f = self.field
        holder = QWidget()
        row = QHBoxLayout(holder)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)
        self.group = QButtonGroup(holder)
        self.group.setExclusive(True)
        self.buttons = {}
        for choice in f.choices:
            button = QPushButton(choice_text(self.tab, f, choice))
            button.setCheckable(True)
            button.setProperty("choice", True)
            self.group.addButton(button)
            self.buttons[choice.id] = button
            button.clicked.connect(lambda _checked=False, c=choice.id: self._chosen(c))
            row.addWidget(button)
        if f.free_id is not None:
            self.free_label = QLabel(self.tab.t("ct_free"))
            self.free = QDoubleSpinBox()
            self.free.setRange(f.minimum, f.maximum)
            self.free.setDecimals(f.decimals)
            self.free.setSingleStep(f.step)
            self.free.setToolTip(self.tab.t("ct_free_tip"))
            self.free.setMinimumWidth(70)
            if f.unit:
                self.free.setSuffix(" " + f.unit)   # a free Δh says its metres, as the buttons beside it do
            self.free.valueChanged.connect(self._free_typed)
            row.addWidget(self.free_label)
            # a free value may follow a variable of the export, as every number of a load does (issue #42), where the domain says so
            linkable = f.free_key in next(iter(getattr(self.tab.MODULE, "LINKABLE", {}).values()), {})
            row.addWidget(self.tab.linked(self.free, f.free_key, f.unit, f.free_key) if linkable else self.free)
        row.addStretch(1)
        self.focus_target = next(iter(self.buttons.values()), None)
        return holder

    def _build_tiles(self):
        f = self.field
        holder = QWidget()
        row = QHBoxLayout(holder)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        self.group = QButtonGroup(holder)
        self.group.setExclusive(True)
        self.buttons = {}
        draw = getattr(self.tab.MODULE, "tile_svg", None)
        for choice in f.choices:
            cell = QWidget()
            column = QVBoxLayout(cell)
            column.setContentsMargins(0, 0, 0, 0)
            column.setSpacing(0)
            tile = QToolButton()
            tile.setCheckable(True)
            tile.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            tile.setText(choice_text(self.tab, f, choice))
            if draw is not None:
                tile.setIcon(svg_icon(draw(choice.id)))
                tile.setIconSize(TILE)
            tile.setStyleSheet("QToolButton:checked { border: 2px solid %s; border-radius: 6px; }" % theme.colour("accent"))
            self.group.addButton(tile)
            self.buttons[choice.id] = tile
            tile.clicked.connect(lambda _checked=False, c=choice.id: self._chosen(c))
            column.addWidget(tile)
            if choice.excerpts:
                mark = InfoMark(self.tab.t("ct_info_tip"))
                mark.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                self.tab.bubbles.attach(mark, self.declaration.norm, choice.excerpts, bare=True)   # a roof's bubble shows its excerpt alone (T28)
                column.addWidget(mark)
            row.addWidget(cell)
        row.addStretch(1)
        self.focus_target = next(iter(self.buttons.values()), None)
        return holder

    def _build_checkbox(self):
        self.check = QCheckBox()
        self.check.toggled.connect(self.tab.touch)
        self.focus_target = self.check
        return self.check

    def _build_select(self):
        self.combo = QComboBox()
        for choice in self.field.choices:
            self.combo.addItem(choice_text(self.tab, self.field, choice), choice.id)
        self.combo.currentIndexChanged.connect(lambda _i: self.tab.field_changed(self.field.key) if not self.tab.loading else None)   # a choice may show other rows (the wind's openings, spec 2026-10-23-onglet-vent-briques)
        self.focus_target = self.combo
        return self.combo

    # -- what the engineer does --

    def _chosen(self, choice_id):
        self.free_active = False
        self._mark_free()
        self.tab.field_changed(self.field.key)

    def _free_typed(self, _value):
        if self.tab.loading:
            return
        self.free_active = True
        self.group.setExclusive(False)
        for button in self.buttons.values():
            button.setChecked(False)
        self.group.setExclusive(True)
        self._mark_free()
        self.tab.field_changed(self.field.key)

    def _mark_free(self):
        if getattr(self, "free", None) is not None:
            self.free.setStyleSheet("QDoubleSpinBox { border: 2px solid %s; }" % theme.colour("accent") if self.free_active else "")

    # -- the source --

    def _number_of(self, value):
        """A number field's value as the source holds it: a {value, unit} block's value (`Field.block`), its magnitude where the field takes no negative (a member check's moment, whose sign says nothing a section check reads)."""
        f = self.field
        if f.block and isinstance(value, dict):
            value = value.get("value")
            if isinstance(value, (int, float)) and f.minimum >= 0:
                value = abs(value)
        return value

    def fill(self, src):
        f = self.field
        value = src.get(f.key)
        if f.kind == "number":
            value = self._number_of(value)
            if self.special is not None:
                self.special.setChecked(value is None)
                self.spin.setEnabled(value is not None)
            if isinstance(value, (int, float)) or self.special is None:
                self.spin.setValue(float(value) if isinstance(value, (int, float)) else 0.0)
        elif f.kind in ("buttons", "tiles"):
            self.free_active = f.free_id is not None and value == f.free_id
            self.group.setExclusive(False)
            for cid, button in self.buttons.items():
                button.setChecked(cid == value and not self.free_active)
            self.group.setExclusive(True)
            if getattr(self, "free", None) is not None:
                free = src.get(f.free_key)
                # not free: the value of the choice made, a start for a value of one's own (Δh +200 → 150), else the first choice's
                chosen = next((c.value for c in f.choices if c.id == value and isinstance(c.value, (int, float))), None)
                self.free.setValue(float(free) if isinstance(free, (int, float)) else float(chosen) if chosen is not None else next((float(c.value) for c in f.choices if isinstance(c.value, (int, float))), 0.0))
            self._mark_free()
        elif f.kind == "checkbox":
            self.check.setChecked(bool(value))
        elif f.kind == "select":
            self.combo.setCurrentIndex(max(self.combo.findData(value), 0))

    def draft(self, src):
        f = self.field
        if f.kind == "number":
            value = None if self.special is not None and self.special.isChecked() else self.spin.value()
            if value is not None and f.zero_none and value == 0:
                value = None
            src[f.key] = {"value": value, "unit": f.unit} if f.block and value is not None else value
        elif f.kind in ("buttons", "tiles"):
            if self.free_active:
                src[f.key] = f.free_id
                src[f.free_key] = self.free.value()
            else:
                chosen = next((cid for cid, button in self.buttons.items() if button.isChecked()), src.get(f.key))
                src[f.key] = chosen
                if f.free_key:
                    src.pop(f.free_key, None)
        elif f.kind == "checkbox":
            src[f.key] = self.check.isChecked()
        elif f.kind == "select":
            src[f.key] = self.combo.currentData()

    def set_choice_values(self, values):
        """What each choice of a field of buttons is worth for the draft, under its words (a member check's five cards of f_c,90,d, issue #112, UI-008): `values` {choice id: {value, unit, enabled, tip}} as the domain's `choice_values` gives them -- a value under the words, «—» where there is none, a choice without one greyed with the domain's word saying why. {} gives every button back its words alone."""
        if self.field.kind != "buttons":
            return
        for choice in self.field.choices:
            button = self.buttons[choice.id]
            said = values.get(choice.id)
            text = choice_text(self.tab, self.field, choice)
            if said is None:
                button.setText(text)
                button.setEnabled(True)
                button.setToolTip("")
                continue
            value = said.get("value")
            button.setText(text + "\n" + ((_n(value) + (" " + said["unit"] if said.get("unit") else "")) if isinstance(value, (int, float)) else "—"))
            button.setEnabled(bool(said.get("enabled", True)))
            tip = said.get("tip")
            button.setToolTip(self.tab.t(tip[0], **tip[1]) if tip and not said.get("enabled", True) else "")

    # -- a message names it --

    def focus(self):
        target = (self.free if self.free_active else self.focus_target) if getattr(self, "free", None) is not None else self.focus_target
        if target is not None:
            target.setFocus(Qt.FocusReason.OtherFocusReason)

    def blink(self):
        """The field flashes three times in the theme's `lit` colour (T49: «un clic sur un message mène au champ, qui clignote»)."""
        self._blinker.start()

    def summary(self, src):
        """What the field says in its section's header (UI-005): its value and unit, the choice made, a check box's words where it is ticked -- "" where it says nothing (a box not ticked)."""
        f = self.field
        value = src.get(f.key)
        if f.kind == "number":
            value = self._number_of(value)
            if value is None and self.special is not None:
                return richtext.plain_math(self.tab.t(self.declaration.prefix + f.special_word))
            return (_n(value) + (" " + f.unit if f.unit and f.unit != "°" else f.unit)) if isinstance(value, (int, float)) else ""
        if f.kind in ("buttons", "tiles", "select"):
            if f.free_id is not None and value == f.free_id:
                free = src.get(f.free_key)
                return (_n(free) + (" " + f.unit if f.unit else "")) if isinstance(free, (int, float)) else ""
            choice = next((c for c in f.choices if c.id == value), None)
            return choice_text(self.tab, f, choice) if choice is not None else ""
        if f.kind == "checkbox":
            return self.words.text() if value else ""
        return ""

    def set_lit(self, lit):
        """Lit up with the results it goes into, or with the result hovered that is computed from it (UI-004): its words on the theme's `hover` ground."""
        self.words.setStyleSheet("background: %s; color: %s; border-radius: 4px; padding: 0 3px;" % (theme.colour("hover"), theme.colour("hover-ink")) if lit else "")
        self.lit = bool(lit)

    @property
    def blinking(self):
        return self._blinker.active()
