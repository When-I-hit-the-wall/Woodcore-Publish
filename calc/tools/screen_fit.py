"""A window of Woodcore's own opened inside the screen it belongs to, its title bar included (spec 2026-10-23-neige-correctifs-issues-96-99, UI-006, ARCH-002): the engineer, 23.10.2026, «la barre tout en haut du PDF apparaît en dehors de l'écran et c'est compliqué de la ramener vers le bas».

`fitted` is the arithmetic, a pure function a test holds: the client rectangle a window asks for, shrunk to what the screen's available area holds once its frame -- the title bar above, the borders around -- is counted, and moved inside it. `place` applies it to a window: the screen of the window it belongs to (`anchor`, Woodcore's main window), never the primary one, its frame read once the window is shown, estimated from the style's title bar before. The norm's reader (norm_reader.py) and a module's window (module_pane.ModuleWindow) open through it. The start screen and the splash centre a small window on the primary screen before any window of Woodcore's exists, and the main window remembers its size alone (woodcore_gui.remembered_size): neither places a window by its frame, which is this module's one job.
"""

from PySide6.QtCore import QMargins, QRect
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QStyle

# The borders a frame adds left, right and below where it cannot be read yet: what Windows 11 draws, a few pixels
BORDER = 8


def fitted(rect, frame, available, centre=False):
    """The client rectangle of a window that asks for `rect` -- centred where `centre`, else at its position, moved in where it does not fit -- inside `available` once `frame` (QMargins: the title bar on top, the borders) is counted: never larger than the area, its frame -- the title bar first -- always on the screen."""
    room_w = max(1, available.width() - frame.left() - frame.right())
    room_h = max(1, available.height() - frame.top() - frame.bottom())
    width, height = min(rect.width(), room_w), min(rect.height(), room_h)
    if centre:
        x = available.left() + frame.left() + (room_w - width) // 2
        y = available.top() + frame.top() + (room_h - height) // 2
    else:
        x, y = rect.x(), rect.y()
    x = min(max(x, available.left() + frame.left()), available.left() + frame.left() + room_w - width)
    y = min(max(y, available.top() + frame.top()), available.top() + frame.top() + room_h - height)
    return QRect(x, y, width, height)


def frame_of(window):
    """The margins `window`'s frame adds to its client area: read where the window is shown, estimated from the style's title bar where not."""
    outer, inner = window.frameGeometry(), window.geometry()
    if window.isVisible() and outer != inner:
        return QMargins(inner.left() - outer.left(), inner.top() - outer.top(), outer.right() - inner.right(), outer.bottom() - inner.bottom())
    title = window.style().pixelMetric(QStyle.PixelMetric.PM_TitleBarHeight) + BORDER
    return QMargins(BORDER, title, BORDER, BORDER)


def place(window, anchor=None, keep=False):
    """`window` resized and moved inside the available area of `anchor`'s screen (its own where none is given): centred, or where it stands if `keep` and that fits."""
    screen = None
    for widget in (anchor, window):
        try:
            screen = widget.screen() if widget is not None else None
        except RuntimeError:
            screen = None
        if screen is not None:
            break
    screen = screen or QGuiApplication.primaryScreen()
    if screen is None:
        return window.geometry()
    kept = keep and window.isVisible()
    rect = fitted(QRect(window.geometry()), frame_of(window), screen.availableGeometry(), centre=not kept)
    window.setGeometry(rect)
    return rect
