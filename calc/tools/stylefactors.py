# -*- coding: utf-8 -*-
"""The three factors a figure is set with, in the window: the drawing's own three sliders, and the factors one entry may state over them (v0.99, docs/ui/window.md §10quater).

`calc/domains/figure_style.py` is what the factors *are* -- their names, their range, which of them each kind of entry may state, and the arithmetic; this is how they are typed. Both the plans, the static models and the detail schemas read them from here rather than each growing a copy, for the reason the three tabs already share `identity.IdentityRows`: a slider means the same thing in every tab, so it is built once.

⚠️ **An entry's factor is shown the way an overridden b/h is shown** (v0.75, `schema_tab.fill_element`): while the entry states none, the slider stands at 100 % and says «follows the drawing»; the moment it states one, the row's name and its readout are written in `theme.colour("override")` -- the orange the connectors' tab has written an overridden value in since v0.70 -- and **«Reprendre»** appears beside it, which takes the factor off the entry again. Setting the slider back to 100 % by hand does **not** take it off: that is the b/h rule stated in v0.75, «typing the very value the position holds still writes it over», and it is what keeps an engineer from thinking he has undone something he has not.

The words are each tab's own, in its own `STRINGS`, in the three languages -- `<prefix>_style_line`, `_point`, `_text`, `_style_own`, `_style_own_note`, `_style_take_back` -- so that a tab says «Traits» where it already says «Traits» and the window's words stay where the house keeps them.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSlider, QWidget

import theme
from domains import figure_style


def percent(minimum=None, maximum=None):
    """A slider in per cent over `figure_style.RANGE`, with its value beside it: `(widget, slider, readout)`. What the three tabs set a drawing's own factor with."""
    lo = int(round(100 * (figure_style.RANGE[0] if minimum is None else minimum)))
    hi = int(round(100 * (figure_style.RANGE[1] if maximum is None else maximum)))
    box = QWidget()
    row = QHBoxLayout(box)
    row.setContentsMargins(0, 0, 0, 0)
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(lo, hi)
    slider.setValue(100)
    readout = QLabel("100 %")
    readout.setMinimumWidth(42)
    slider.valueChanged.connect(lambda value: readout.setText(f"{value} %"))
    row.addWidget(slider, 1)
    row.addWidget(readout)
    return box, slider, readout


class EntryRows:
    """One row per factor an entry may state, added to a `QFormLayout`: `name | [slider] 130 % [Reprendre]`.

    `t` is the tab's own translator and `prefix` its own key prefix (`sc`, `st`, `plan`). `on_set(key, factor)` is called when a slider is moved -- the entry then **states** that factor -- and `on_take_back(key)` when «Reprendre» is clicked. `pressed`/`released` are given where the tab drags a slider live and pushes one step of «Annuler» per drag, as the static models' own sliders do.
    """

    def __init__(self, form, t, prefix, on_set, on_take_back, pressed=None, released=None):
        self.t, self.prefix = t, prefix
        self.on_set, self.on_take_back = on_set, on_take_back
        self.rows = {}
        for key in figure_style.KEYS:
            box, slider, readout = percent()
            back = QPushButton(t(f"{prefix}_style_take_back"))
            back.clicked.connect(lambda _checked=False, which=key: self.on_take_back(which))
            box.layout().addWidget(back)
            slider.valueChanged.connect(lambda value, which=key: self._moved(which, value))
            if pressed is not None:
                slider.sliderPressed.connect(pressed)
            if released is not None:
                slider.sliderReleased.connect(released)
            name = QLabel(t(f"{prefix}_style_{key}"))
            form.addRow(name, box)
            self.rows[key] = {"name": name, "field": box, "slider": slider, "readout": readout, "back": back}
        self.loading = False

    def _moved(self, key, value):
        if self.loading:
            return
        self.on_set(key, value / 100.0)

    def widgets(self):
        """Every widget of every row -- what a tab hides when nothing is selected."""
        return [widget for row in self.rows.values() for widget in (row["name"], row["field"])]

    def fill(self, entry, may):
        """The rows of one entry: those of `may` shown, the others hidden altogether -- a factor the entry is not drawn with is not a field it could be typed into (`figure_style.ENTRY_KEYS`). A factor the entry states is orange, with «Reprendre»; one it does not stands at 100 % and follows the drawing."""
        own = figure_style.stated(entry or {})
        orange = theme.colour("override")
        self.loading = True
        for key, row in self.rows.items():
            shown = key in may
            row["name"].setVisible(shown)
            row["field"].setVisible(shown)
            if not shown:
                continue
            stated = key in own
            row["slider"].setValue(int(round(100 * own.get(key, figure_style.DEFAULT))))
            row["readout"].setText(f"{row['slider'].value()} %")
            for widget in (row["name"], row["readout"]):
                widget.setStyleSheet(f"color: {orange};" if stated else "")
            row["back"].setVisible(stated)
        self.loading = False
