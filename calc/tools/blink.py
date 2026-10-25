"""A widget that flashes to be found, written once (spec docs/requirements/active/2026-10-24-onglet-materiaux.md, review U05; issue #110).

A field a message names flashes three times in the theme's `lit` colour (calc_fields, T49 of the snow's spec); a module of a right pane its source label points at flashes the same way (module_pane.ModulePane.reveal, the «Matériaux» tab's «La source»). One timer a widget, stopped where it ends: the widget's style sheet put back as it was.
"""

from PySide6.QtCore import QObject, QTimer

import theme

BLINKS = 6          # how many times the colour changes (three flashes)
BLINK_MS = 180


class Blinker(QObject):
    """Flashes `widget` -- its background in `lit`, then as it was -- `BLINKS` times, `BLINK_MS` apart."""

    def __init__(self, widget, selector=""):
        super().__init__(widget)
        self.widget = widget
        self.selector = selector     # «#calcModule» to colour the frame alone and not each child
        self.left = 0
        self.timer = QTimer(self)
        self.timer.setInterval(BLINK_MS)
        self.timer.timeout.connect(self._step)
        self.kept = None

    def start(self):
        if not self.timer.isActive():
            self.kept = self.widget.styleSheet()
        self.left = BLINKS
        self.timer.start()
        self._step()

    def active(self):
        return self.timer.isActive()

    def _step(self):
        on = self.left % 2 == 0 and self.left > 0
        rule = "background: %s;" % theme.colour("lit")
        self.widget.setStyleSheet((self.kept or "") + ((" %s { %s }" % (self.selector, rule)) if self.selector else rule) if on else (self.kept or ""))
        self.left -= 1
        if self.left <= 0:
            self.timer.stop()
            self.widget.setStyleSheet(self.kept or "")
