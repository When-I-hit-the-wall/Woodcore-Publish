# -*- coding: utf-8 -*-
"""The wheel scrolls and zooms; it never changes a value (docs/ui/window.md §10quater).

Qt turns the wheel into a value change on a spin box, a combo box and a slider, and it does so whether or not the widget has the focus. In a window that is mostly forms inside scroll areas -- which is what every editor tab of Woodcore's window is -- that means a wheel meant to scroll a panel silently retypes whichever field happened to be under the pointer. An angle becomes 5 degrees more, a strength class becomes the next one down, and nothing says so. The engineer asked for it to stop everywhere.

**One filter, on the application, rather than a subclass per widget.** There are 28 spin boxes, 25 combo boxes and the style sliders across `woodcore_gui.py`, `connectors_tab.py`, `plan_tab.py` and `statics_tab.py`, and subclassing would have to reach every one of them -- including the ones a delegate builds on the fly for a table cell, which are not written down anywhere, and every one added later. An application-level event filter sees them all, and a widget written next year is covered without anybody remembering this file exists.

**The event is eaten and then re-sent to the nearest scrolling ancestor.** Eating it alone would be worse than the defect: the wheel would do nothing at all over a field, so a panel could not be scrolled by pointing at the middle of it. Re-sending it to the viewport of the enclosing `QAbstractScrollArea` is what makes the wheel mean one thing everywhere -- scroll what is under the pointer.

⚠️ **A `QScrollBar` is a `QAbstractSlider`** and must not be caught: it is the scroll bar itself, and eating its wheel would stop the very scrolling this exists to protect. It is the one exclusion, and `tests/test_wheel.py` holds it.

👉 The canvases are untouched: `plan_canvas` and `statics_canvas` handle the wheel themselves, to zoom about the pointer, and neither is a guarded type.
"""

from PySide6.QtCore import QEvent, QObject, QPointF
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QAbstractSlider,
    QAbstractSpinBox,
    QApplication,
    QComboBox,
    QScrollBar,
)

# What Qt lets the wheel retype. A QScrollBar is a QAbstractSlider and is excluded below.
GUARDED = (QAbstractSpinBox, QComboBox, QAbstractSlider)


def guarded(widget):
    """True where the wheel would change this widget's value rather than scroll something."""
    return isinstance(widget, GUARDED) and not isinstance(widget, QScrollBar)


def scrolling_ancestor(widget):
    """The nearest ancestor that scrolls, so a wheel taken from a field still does what the pointer meant."""
    parent = widget.parentWidget()
    while parent is not None:
        if isinstance(parent, QAbstractScrollArea):
            return parent
        parent = parent.parentWidget()
    return None


def _forward(event, area):
    """Re-send the wheel to a scroll area's viewport, in the viewport's own coordinates."""
    viewport = area.viewport()
    local = QPointF(viewport.mapFromGlobal(event.globalPosition().toPoint()))
    QApplication.sendEvent(viewport, QWheelEvent(
        local,
        event.globalPosition(),
        event.pixelDelta(),
        event.angleDelta(),
        event.buttons(),
        event.modifiers(),
        event.phase(),
        event.inverted(),
    ))


class WheelGuard(QObject):
    """Installed on the application: every wheel over a spin box, a combo box or a slider is scrolling, never typing."""

    def eventFilter(self, obj, event):
        if event.type() != QEvent.Type.Wheel or not guarded(obj):
            return False
        area = scrolling_ancestor(obj)
        if area is not None:
            _forward(event, area)
        return True      # eaten either way: a field with nothing to scroll behind it still must not change


def install(app):
    """Put the guard on the application and keep it alive there. Returns it, which is what a test reads."""
    guard = WheelGuard(app)
    app.installEventFilter(guard)
    return guard
