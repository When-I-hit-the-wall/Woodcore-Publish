"""The wheel scrolls and zooms; it never changes a value -- `calc/tools/nowheel.py` (docs/ui/window.md §10quater).

Qt changes a spin box, a combo box and a slider on a wheel whether or not they have the focus, so in a window that is mostly forms inside scroll areas a wheel meant to scroll silently retyped whichever field was under the pointer. The engineer asked for it to stop everywhere, and "everywhere" is what this file is about: the guard is one application-level event filter, so what has to be held is not a list of widgets but the three rules it follows.

👉 The defect this keeps: a wheel over the angle field of a static model's load, while scrolling the properties panel, moved the load by five degrees and said nothing.

⚠️ Skipped where PySide6 is not installed: a machine that only builds the report is a legitimate machine. Everything here is built off-screen; a test run must never open a window.
"""

import os
import sys

import conftest
from conftest import ROOT, Skip

_qt = None


def _widgets():
    """One of each guarded kind inside a scroll area that has somewhere to scroll, plus the guard installed."""
    global _qt
    if _qt is None:
        path = str(ROOT / "calc" / "tools")
        if path not in sys.path:
            sys.path.insert(0, path)
        try:
            from PySide6.QtWidgets import QApplication
        except ImportError as exc:
            raise Skip(f"PySide6 is not installed ({exc})")
        import nowheel
        app = QApplication.instance() or QApplication([])
        nowheel.install(app)
        _qt = _build(app)
    return _qt


def _build(app):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QComboBox, QDoubleSpinBox, QScrollArea, QSlider, QSpinBox, QVBoxLayout, QWidget,
    )
    inner = QWidget()
    layout = QVBoxLayout(inner)
    spin = QDoubleSpinBox()
    spin.setRange(0, 1000)
    spin.setValue(30.0)
    count = QSpinBox()
    count.setRange(0, 1000)
    count.setValue(4)
    combo = QComboBox()
    combo.addItems(["C24", "GL24h", "GL28h", "D30"])
    combo.setCurrentIndex(1)
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(0, 300)
    slider.setValue(100)
    for widget in (spin, count, combo, slider):
        layout.addWidget(widget)
    spacer = QWidget()
    spacer.setMinimumHeight(2000)          # so the area has somewhere to scroll to
    layout.addWidget(spacer)

    area = QScrollArea()
    area.setWidget(inner)
    area.setWidgetResizable(True)
    area.resize(300, 200)
    area.show()
    app.processEvents()
    return {"app": app, "area": area, "spin": spin, "count": count, "combo": combo, "slider": slider}


def _wheel(widget, notches=-1):
    """Send one wheel notch to `widget`, the way the mouse does, through the application's own notify()."""
    from PySide6.QtCore import QPoint, QPointF, Qt
    from PySide6.QtGui import QWheelEvent
    from PySide6.QtWidgets import QApplication
    centre = QPointF(widget.rect().center())
    event = QWheelEvent(
        centre,
        QPointF(widget.mapToGlobal(widget.rect().center())),
        QPoint(0, 0),
        QPoint(0, 120 * notches),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    QApplication.sendEvent(widget, event)
    QApplication.instance().processEvents()


# --- the three rules ----------------------------------------------------------

def test_the_wheel_does_not_change_a_value():
    """A spin box, a combo box and a slider all keep what they held. This is the whole point of the module."""
    w = _widgets()
    before = (w["spin"].value(), w["count"].value(), w["combo"].currentIndex(), w["slider"].value())
    for key in ("spin", "count", "combo", "slider"):
        _wheel(w[key])
        _wheel(w[key], notches=+1)
    after = (w["spin"].value(), w["count"].value(), w["combo"].currentIndex(), w["slider"].value())
    assert before == after, "the wheel retyped a field: %r -> %r" % (before, after)


def test_the_wheel_still_scrolls_the_panel_behind_the_field():
    """Eating the wheel alone would be worse than the defect -- the panel could not be scrolled by pointing at the middle of it.

    So the event is re-sent to the viewport of the enclosing scroll area, and what the pointer meant still happens.
    """
    w = _widgets()
    bar = w["area"].verticalScrollBar()
    bar.setValue(0)
    _wheel(w["spin"])
    assert bar.value() > 0, "the wheel was eaten and nothing scrolled (scroll bar still at %d)" % bar.value()


def test_a_scroll_bar_is_not_guarded():
    """A QScrollBar IS a QAbstractSlider, so the naive rule would eat the wheel on the scroll bar itself -- which would stop the very scrolling the guard exists to protect."""
    import nowheel
    w = _widgets()
    bar = w["area"].verticalScrollBar()
    assert not nowheel.guarded(bar), "a scroll bar must not be guarded"
    assert nowheel.guarded(w["spin"]) and nowheel.guarded(w["combo"]) and nowheel.guarded(w["slider"])
    bar.setValue(0)
    _wheel(bar)
    assert bar.value() > 0, "the scroll bar stopped responding to its own wheel"


def test_a_field_with_nothing_behind_it_still_refuses_the_wheel():
    """A guarded widget outside any scroll area has nothing to forward to. It must still not change -- the guard eats the event either way."""
    from PySide6.QtWidgets import QDoubleSpinBox
    _widgets()                       # the application and the guard
    loose = QDoubleSpinBox()
    loose.setRange(0, 100)
    loose.setValue(12.5)
    _wheel(loose)
    assert loose.value() == 12.5, "a field with no scroll area behind it was retyped"


def test_the_guard_is_installed_by_main():
    """The one line that arms it. Read out of woodcore_gui.py rather than run, since running main() opens a window."""
    source = conftest.module_source(ROOT / "calc" / "tools" / "woodcore_gui.py")   # with the parts split out of it (issue #30)
    assert "import nowheel" in source, "woodcore_gui.py no longer imports nowheel"
    assert "nowheel.install(app)" in source, "main() no longer installs the wheel guard"
