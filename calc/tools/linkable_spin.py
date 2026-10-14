"""A number field that may follow a variable of the export: the button beside it, what it shows once linked, and the way back (spec docs/requirements/completed/2026-10-11-variables-liees-champs-et-textes.md, UI-001, UI-002, ARCH-002).

`LinkableSpin` wraps the QDoubleSpinBox a form has always built, and changes none of it: the tab goes on reading `value()`, writing `setValue()` and listening to `valueChanged` on its spin, and asks the wrapper only for the link (`link()`, `set_link()`) when it reads or writes its source. That is what lets every form of the perimeter take the button without its `fill_*` and `draft_*` being rewritten (ARCH-RISK-006).

* **The button** (UI-001) brings the «Variables» tab forward in its choosing mode, every other module unavailable, listing only what the field may take -- a number of the export or of a «Formule» domain, of the field's dimension, of a source this consumer may name (`variable_sources.linkable`) -- and gives the choice back to the tab that asked.
* **Linked** (UI-002), the spin is read-only and shows the variable's value now, converted into the field's unit; under it, the variable's symbol and domain, the factor and the offset it is taken with, and «Délier». A variable that can no longer be read keeps the field's last value, in the theme's warning colour, with «Introuvable : …» (D-06).
* **The values** a link is resolved against are the export's, read when the form is filled (`variable_sources.known_values`): the window shows what the report will print, and the last value is written into the source when the tab saves (D-14).

The calculation is `calc/domains/links.py`'s; nothing is computed here.
"""

import html

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDoubleSpinBox, QHBoxLayout, QLabel, QToolButton, QVBoxLayout, QWidget

import theme
import variable_sources
from domains import links

STRINGS = {
    "fr": {
        "lk_link_tip": "Lier à une variable",
        "lk_pick_title": "Choisir une variable pour {field} [{unit}]",
        "lk_pick_title_no_unit": "Choisir une variable pour {field} (sans unité)",
        "lk_from": "↳ {symbol} — {domain}",
        "lk_factor": "×",
        "lk_offset": "+",
        "lk_factor_tip": "Facteur : la valeur vaut facteur × variable + décalage",
        "lk_offset_tip": "Décalage, dans l’unité de la variable",
        "lk_unlink": "Délier",
        "lk_unlink_tip": "Ne plus suivre la variable : le champ garde sa valeur et redevient modifiable",
        "lk_missing": "Introuvable : {ref} — dernière valeur gardée",
        "lk_unavailable": "L’onglet « Variables » n’est pas disponible.",
    },
    "de": {
        "lk_link_tip": "Mit einer Variablen verknüpfen",
        "lk_pick_title": "Variable für {field} [{unit}] wählen",
        "lk_pick_title_no_unit": "Variable für {field} (ohne Einheit) wählen",
        "lk_from": "↳ {symbol} — {domain}",
        "lk_factor": "×",
        "lk_offset": "+",
        "lk_factor_tip": "Faktor: Der Wert ist Faktor × Variable + Verschiebung",
        "lk_offset_tip": "Verschiebung, in der Einheit der Variablen",
        "lk_unlink": "Lösen",
        "lk_unlink_tip": "Der Variablen nicht mehr folgen: Das Feld behält seinen Wert und ist wieder bearbeitbar",
        "lk_missing": "Nicht gefunden: {ref} – letzter Wert beibehalten",
        "lk_unavailable": "Der Reiter «Variablen» ist nicht verfügbar.",
    },
    "en": {
        "lk_link_tip": "Link to a variable",
        "lk_pick_title": "Choose a variable for {field} [{unit}]",
        "lk_pick_title_no_unit": "Choose a variable for {field} (no unit)",
        "lk_from": "↳ {symbol} — {domain}",
        "lk_factor": "×",
        "lk_offset": "+",
        "lk_factor_tip": "Factor: the value is factor × variable + offset",
        "lk_offset_tip": "Offset, in the variable's unit",
        "lk_unlink": "Unlink",
        "lk_unlink_tip": "Stop following the variable: the field keeps its value and can be edited again",
        "lk_missing": "Not found: {ref} — last value kept",
        "lk_unavailable": "The «Variables» tab is not available.",
    },
}

# What the button shows: a variable, as the report's own `var` is a name standing for a value
BUTTON_TEXT = "𝑥"


def current_values():
    """The values a link is resolved against in the window: the export's, read now (`variable_sources.known_values`)."""
    return variable_sources.known_values()


class LinkableSpin(QWidget):
    """`spin` and the button beside it, and once linked the variable it follows (see the module's docstring).

    `unit` is what the field is written in («kN», «mm», «°», "" for none); `field` names it in the choosing bar's title; `app()` returns the window, whose `begin_variable_pick` the button calls; `consumer` is the source this field's links may name (`links.ANY`, or `links.LOADS` for a load's own field, D-11). `changed` is emitted when the link is set, changed or taken off -- what the tab marks itself modified on.
    """

    changed = Signal()

    def __init__(self, spin, unit, field, app, lang="fr", consumer=links.ANY, parent=None, refuse=None):
        super().__init__(parent)
        self.refuse = refuse   # refuse(link) -> a sentence where the tab will not take that link (a load closing a circle, REQ-007), else None
        self.spin = spin
        self.unit = unit or ""
        self.field = field
        self.app = app
        self.lang = lang if lang in STRINGS else "en"
        self.consumer = consumer
        self._link = None
        self.refused = None      # the last refusal said, for a test to read
        self._editable = True
        self._loading = False

        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(2)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(spin, 1)
        self.button = QToolButton()
        self.button.setText(BUTTON_TEXT)
        self.button.setToolTip(self.t("lk_link_tip"))
        self.button.setAutoRaise(True)
        self.button.clicked.connect(self.pick)
        row.addWidget(self.button)
        column.addLayout(row)

        self.linked_row = QWidget()
        line = QHBoxLayout(self.linked_row)
        line.setContentsMargins(0, 0, 0, 0)
        self.chip = QLabel("")
        self.chip.setWordWrap(True)
        line.addWidget(self.chip, 1)
        self.factor = self._small_spin(self.t("lk_factor_tip"), -1e9, 1e9, 1.0)
        self.offset = self._small_spin(self.t("lk_offset_tip"), -1e12, 1e12, 0.0)
        line.addWidget(QLabel(self.t("lk_factor")))
        line.addWidget(self.factor)
        line.addWidget(QLabel(self.t("lk_offset")))
        line.addWidget(self.offset)
        self.unlink_button = QToolButton()
        self.unlink_button.setText(self.t("lk_unlink"))
        self.unlink_button.setToolTip(self.t("lk_unlink_tip"))
        self.unlink_button.clicked.connect(self.unlink)
        line.addWidget(self.unlink_button)
        column.addWidget(self.linked_row)
        self.linked_row.setVisible(False)
        self.set_editable(True)   # closed at once in a project opened read-only (ARCH-RISK-009)

    # a drop-in for the spin it wraps (ARCH-RISK-006): what reads or writes the number may hold the wrapper
    def value(self):
        return self.spin.value()

    def setValue(self, value):
        self.spin.setValue(value)

    @property
    def valueChanged(self):
        return self.spin.valueChanged

    def t(self, key, **kwargs):
        text = STRINGS[self.lang][key]
        return text.format(**kwargs) if kwargs else text

    def _small_spin(self, tip, low, high, value):
        box = QDoubleSpinBox()
        box.setRange(low, high)
        box.setDecimals(4)
        box.setValue(value)
        box.setToolTip(tip)
        box.setMaximumWidth(90)
        box.valueChanged.connect(self._on_factor)
        return box

    # -- the link ---------------------------------------------------------------------

    def link(self):
        """The link this field follows, as the source saves it, or None."""
        if self._link is None:
            return None
        return links.make(self._link["domain"], self._link["instance"], self._link["var"],
                          self.factor.value(), self.offset.value(), self._link.get("origin"))

    def set_link(self, link, values=None):
        """Shows `link` (None: a typed field), resolved against `values` (the export's, read now where None). Emits nothing: what a form fills is not an edit."""
        self._loading = True
        try:
            self._link = dict(link) if link else None
            self.factor.setValue(float((link or {}).get("factor", 1.0)))
            self.offset.setValue(float((link or {}).get("offset", 0.0)))
        finally:
            self._loading = False
        self.show_state(values)

    def read_only(self):
        """Whether the window has the project open read-only: a link is a change to its sources, refused there as every other (woodcore_gui.WRITERS)."""
        return bool(getattr(self.app() if self.app is not None else None, "read_only", False))

    def set_editable(self, editable):
        """Read-only projects and kinds that close a field: the button follows the spin, and stays closed in a project opened read-only."""
        editable = editable and not self.read_only()
        self._editable = editable
        self.button.setEnabled(editable)
        self.unlink_button.setEnabled(editable)
        self.factor.setEnabled(editable)
        self.offset.setEnabled(editable)

    def show_state(self, values=None):
        """The field's three states (UI-002): typed; linked, the spin showing the value now; linked to what cannot be read, the last value in the warning colour."""
        self.linked_row.setVisible(self._link is not None)
        self.spin.setReadOnly(self._link is not None)
        if self._link is None:
            self.spin.setStyleSheet("")
            self.chip.setText("")
            return
        link = self.link()
        values = current_values() if values is None else values
        found = links.resolve(link, values, self.unit, self.spin.value(), self.consumer)
        if found["stale"]:
            self.chip.setText(html.escape(self.t("lk_missing", ref=found["from"])))
            colour = theme.colour("warning")
            self.chip.setStyleSheet(f"color: {colour};")
            self.spin.setStyleSheet(f"color: {colour};")
            return
        self.chip.setStyleSheet("")
        self.spin.setStyleSheet("")
        record = links.lookup(link, values) or {}
        domain = link["instance"] if link.get("origin") == links.FORMULAS else f"{link['domain']} · {link['instance']}"
        self.chip.setText(self.t("lk_from", symbol=record.get("symbol") or link["var"], domain=domain))
        if abs(self.spin.value() - found["value"]) > 1e-12:
            self.spin.setValue(found["value"])

    # -- the button, «Délier», the factor ---------------------------------------------------

    def pick(self):
        """The «Variables» tab in its choosing mode, showing only what this field may take (UI-001, UI-003)."""
        if self.read_only():
            return
        begin = getattr(self.app(), "begin_variable_pick", None) if self.app is not None else None
        title = self.t("lk_pick_title", field=self.field, unit=self.unit) if self.unit else self.t("lk_pick_title_no_unit", field=self.field)

        def accept(var, domain):
            return variable_sources.linkable(var, domain, self.unit, self.consumer)

        if begin is None or not begin(self.on_picked, title, accept):
            setter = getattr(self.app(), "set_status", None) if self.app is not None else None
            if setter is not None:
                setter(self.t("lk_unavailable"))

    def on_picked(self, chosen):
        """What the «Variables» tab gave back: (source, domain, variable, its export address or None), or None where the choice was given up."""
        if chosen is None:
            return
        origin, domain_name, var, address = chosen
        link = links.from_choice(origin, domain_name, var.key, address)
        if link is None:
            return
        refused = self.refuse(link) if self.refuse is not None else None
        if refused:
            setter = getattr(self.app(), "set_status", None) if self.app is not None else None
            if setter is not None:
                setter(refused)
            self.refused = refused
            return
        self._link = link
        self._loading = True
        try:
            self.factor.setValue(1.0)
            self.offset.setValue(0.0)
        finally:
            self._loading = False
        # the value at once, from the variable chosen: the export read again would give the same number, later
        if var.is_number and links.compatible(var.unit, self.unit):
            self.spin.setValue(links.convert(links.apply(link, var.value), var.unit, self.unit))
        self.show_state()
        self.changed.emit()

    def unlink(self):
        """«Délier» (REQ-008): the field keeps the value it shows and is typed again."""
        self._link = None
        self.show_state()
        self.changed.emit()

    def _on_factor(self, *_args):
        if self._loading or self._link is None:
            return
        self.show_state()
        self.changed.emit()
