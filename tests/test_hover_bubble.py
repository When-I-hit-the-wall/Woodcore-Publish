"""The bubble that stays open under the pointer (calc/tools/hover_bubble.py; spec 2026-10-24-onglet-commandes-pages, ARCH-002, UI-008): opened at a hover, kept while the pointer is in it, closed 300 ms after it leaves, pinned by a click, closed by Escape, a click elsewhere or a scroll, placed above its trigger where there is no room under it -- and used here without anything of the commands tab, as the domains and variables tabs will use it."""

import sys
import time

from conftest import ROOT, Skip

sys.path.insert(0, str(ROOT / "calc" / "tools"))

TIER = "fast"


def _app():
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _wait(ms):
    app = _app()
    end = time.time() + ms / 1000
    while time.time() < end:
        app.processEvents()
        time.sleep(0.01)


def _controller():
    from PySide6.QtCore import QRect
    from PySide6.QtWidgets import QLabel
    import hover_bubble
    _app()
    controller = hover_bubble.HoverController(leave_ms=80)
    controller.open("a", QLabel("une phrase"), QRect(100, 100, 40, 16), 380)
    return controller, hover_bubble


def test_the_brick_knows_nothing_of_the_commands():
    """ARCH-002: the module imports nothing of the commands tab, nor of the norms."""
    source = (ROOT / "calc" / "tools" / "hover_bubble.py").read_text(encoding="utf-8")
    assert "commands_tab" not in source and "command_page" not in source and "norms" not in source


def test_it_closes_after_the_pointer_leaves_and_stays_while_it_is_in():
    controller, _hb = _controller()
    assert controller.is_open()
    controller.leave()
    controller.keep()   # the pointer reached the bubble
    _wait(200)
    assert controller.is_open(), "entering the bubble cancels the closing"
    controller.leave()
    _wait(250)
    assert not controller.is_open(), "it closes once the pointer left both"


def test_a_click_pins_it_and_escape_closes_it():
    from PySide6.QtCore import QEvent, Qt
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtWidgets import QApplication
    controller, _hb = _controller()
    controller.pin()
    controller.leave()
    _wait(200)
    assert controller.is_open() and controller.pinned, "a pinned bubble does not close when the pointer leaves"
    QApplication.sendEvent(controller.bubble, QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier))
    assert not controller.is_open(), "Escape closes it"


def test_a_scroll_closes_it_pinned_or_not():
    from PySide6.QtWidgets import QScrollBar
    controller, _hb = _controller()
    controller.pin()
    bar = QScrollBar()
    bar.setRange(0, 100)
    controller.watch_scroll(bar)
    bar.setValue(30)
    assert not controller.is_open()


def test_it_opens_above_where_there_is_no_room_under():
    from PySide6.QtCore import QRect, QSize
    _controller()
    import hover_bubble
    screen = QRect(0, 0, 1000, 800)
    under, scroll = hover_bubble.place(QRect(100, 100, 40, 16), QSize(380, 200), screen)
    assert under.top() > 116 and not scroll
    above, scroll = hover_bubble.place(QRect(100, 700, 40, 16), QSize(380, 200), screen)
    assert above.bottom() < 700 and not scroll
    right, _ = hover_bubble.place(QRect(900, 100, 40, 16), QSize(380, 200), screen)
    assert right.right() <= screen.right(), "never off the screen"


def test_norm_bubble_reads_the_same_placement():
    _app()
    import hover_bubble
    import norm_bubble
    assert norm_bubble.place is hover_bubble.place and norm_bubble.GAP == hover_bubble.GAP
