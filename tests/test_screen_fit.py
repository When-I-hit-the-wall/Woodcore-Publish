"""A window of Woodcore's own opened inside its screen, its title bar on it (calc/tools/screen_fit.py; spec 2026-10-23-neige-correctifs-issues-96-99, UI-006, ARCH-002): the engineer, 23.10.2026, «la barre tout en haut du PDF apparaît en dehors de l'écran».

Held here: the norm's reader, which asks 820 × 1000, on a laptop's 1920 × 1032 available area keeps its title bar on the screen and shrinks to it; a second screen whose origin is not (0, 0); a window already standing partly off a screen moved in, one inside left where it is; the reader and a module's window opened through `place`, on the screen of the window they belong to.
"""

TIER = "fast"  # tests/run_tests.py --fast

import os
import sys

import conftest
from conftest import ROOT

TOOLS = ROOT / "calc" / "tools"


def _qt():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def test_the_reader_s_window_keeps_its_title_bar_on_a_laptop_screen():
    _qt()
    import screen_fit
    from PySide6.QtCore import QMargins, QRect
    frame = QMargins(8, 38, 8, 8)
    screen = QRect(0, 0, 1920, 1032)
    rect = screen_fit.fitted(QRect(0, 0, 820, 1000), frame, screen, centre=True)
    assert rect.top() - frame.top() >= screen.top(), "the title bar on the screen"
    assert rect.bottom() + frame.bottom() <= screen.bottom() and rect.height() < 1000, "shrunk to the screen"
    assert rect.width() == 820 and abs((rect.left() - screen.left()) - (screen.right() - rect.right())) <= 2, "centred"
    # a second screen right of the first and lower
    second = QRect(1920, 200, 1280, 700)
    rect = screen_fit.fitted(QRect(0, 0, 820, 1000), frame, second, centre=True)
    assert second.contains(rect.adjusted(-frame.left(), -frame.top(), frame.right(), frame.bottom()))
    # a window standing above the screen's top is moved down; one inside stays
    rect = screen_fit.fitted(QRect(100, -20, 600, 400), frame, screen)
    assert rect.top() == screen.top() + frame.top() and rect.left() == 100
    assert screen_fit.fitted(QRect(300, 200, 600, 400), frame, screen) == QRect(300, 200, 600, 400)


def test_the_reader_and_a_module_s_window_open_through_place():
    """Both windows are placed inside their screen: the reader before it shows and once shown, a module's window as it opens."""
    _qt()
    import inspect
    import module_pane
    import norm_reader
    import screen_fit
    from PySide6.QtWidgets import QWidget
    assert "screen_fit.place" in inspect.getsource(norm_reader.NormReader._show_placed)
    assert "screen_fit.place" in inspect.getsource(module_pane.ModulePane.open_window)
    window = QWidget()
    window.resize(5000, 5000)
    rect = screen_fit.place(window)
    available = window.screen().availableGeometry()
    assert rect.width() <= available.width() and rect.height() <= available.height() and rect.top() >= available.top()
