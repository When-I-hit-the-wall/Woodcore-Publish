# -*- coding: utf-8 -*-
"""What Woodcore shows while it works: a card in the middle of the window with a turning arc and a line saying what is being done, the window's input held back meanwhile and its hover left alone (the engineer's request of 03.10.2026: «quand il y a des chargements, la fenêtre ne fait que de freeze, et on a presque l'impression que le programme va crash … afficher quelque chose qui charge au milieu de l'écran, de design également, et que la fenêtre ne soit pas en train de freeze. Que si on passe sur des boutons, il y ait toujours le overlay du mouse over dessus, mais on ne peut pas interagir avec»).

Three things, each answering one half of that sentence:

* **The card** (`Spinner`): a child of the window it covers, centred and following its size, painted in the theme's own tokens -- the `card` ground, a `line` border, the `accent` arc on a `line` track, the text in `ink` and `muted` -- so it reads the same in the light and the dark scheme (theme.py) and states no colour of its own. It is transparent to the mouse, so the widgets under it go on taking their hover. Opened where no window is up yet -- a project double-clicked, whose window is being built -- it is a small window of its own (`Splash`), the same card.
* **The guard** (`_Guard`): one event filter on the application, installed while a window is held over work that leaves the event loop free -- an export, a compilation, `run_in_thread` -- and taken off as soon as no such hold is left (v0.117). It eats what would act on a held window -- a click, a double-click, the wheel, a key, a shortcut, a context menu, a drop -- and lets through what only shows: the pointer moving over a button, its entering and leaving, paints, resizes. A message box or a dialog the work opens is a window of its own and is never held. The pointer shows Qt's busy cursor, the arrow with its small wheel: the window is there to be looked at, and waits. Work done on the main thread is held **without** the guard (`guard=False`): its loop only turns in `pump()`, which leaves input queued until the work is done, so the guard would have nothing to hold back -- and an application-wide filter is a crossing into Python for every event of every widget, which while a window is built is every polish and style change of every child: 127 505 calls and about 8 s of the example project's 19 s (docs/architecture/performance.md, measured on 08.10.2026). Installed once and never taken off, as it was until v0.117, it taxed every paint, scroll and zoom of the session as well.
* **Keeping the arc turning.** Work Woodcore hands to another process -- an export, a compilation -- leaves the event loop free, and the arc turns by itself. Work done on the main thread does not, and most of it cannot leave it: building a window's twelve modules is Qt widgets, which only the thread that made them may touch (8.6 s for the example project's window, 5.2 s for a reload, measured on 03.10.2026). So a long piece of such work calls `pump()` between its steps -- MainWindow.build does, once per module -- which paints the arc where it now is and lets Windows see a window that answers, so it never greys it out as «Ne répond pas»; input is not processed there (`ExcludeUserInputEvents`), and the guard holds it back anyway. Work that touches no widget -- a project created from its template, pip -- runs in a thread of its own instead (`run_in_thread`), the loop free the whole time.

Nothing here knows what is being done: a caller says it in its own words, in the window's language.
"""

import math
import threading
import time

from PySide6.QtCore import QEvent, QEventLoop, QObject, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget

import theme

# How long one turn of the arc takes, and how often it is painted while the loop is free.
TURN_S = 1.1
FRAME_MS = 16
# How often a long piece of main-thread work lets the card be painted and Windows be answered (`pump`): often enough for the arc to move, seldom enough to cost nothing measurable.
PUMP_S = 0.03
# The card: its width and the arc's size and stroke, in device-independent pixels.
CARD_WIDTH = 300
ARC_SIZE = 34
ARC_STROKE = 4
# The site's radius (theme.json's `radius`, 10px), which every card of the window takes (cards.py).
CARD_RADIUS = 10.0
# After this long the card says how long it has been (v0.117: «une estimation si celle-ci est fiable» -- the time gone is what is certain).
ELAPSED_AFTER_S = 2.0

# What a held window is spared: everything that acts. Moving the pointer, entering and leaving a widget and the hover they draw are not among them -- the engineer wants the hover kept.
BLOCKED = frozenset({
    QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease, QEvent.Type.MouseButtonDblClick, QEvent.Type.Wheel,
    QEvent.Type.KeyPress, QEvent.Type.KeyRelease, QEvent.Type.ShortcutOverride, QEvent.Type.ContextMenu,
    QEvent.Type.DragEnter, QEvent.Type.DragMove, QEvent.Type.Drop, QEvent.Type.TabletPress, QEvent.Type.TouchBegin,
})

# The windows held, each with its card: {window: Spinner}; and those held over work that leaves the loop free, which the guard watches over.
_held = {}
_guarded = set()
_guard = None
_last_pump = [0.0]


class Spinner(QWidget):
    """The card: a turning arc and a line -- what is being done -- with a second, quieter one where the caller gives a detail. A child of `host`, covering it whole (it is transparent to the mouse, so what lies under it keeps its hover) and painting only its card, in the middle."""

    def __init__(self, host, text="", detail=""):
        super().__init__(host)
        self.text = text
        self.detail = detail
        self.fraction = None   # how far the work is, 0 to 1, where its caller knows (set_progress); None: the arc alone
        self.started = time.monotonic()
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.timer = QTimer(self)
        self.timer.setInterval(FRAME_MS)
        self.timer.timeout.connect(self.update)
        self.timer.start()
        host.installEventFilter(self)
        self.cover()
        self.show()
        self.raise_()

    def cover(self):
        host = self.parentWidget()
        if host is not None:
            self.setGeometry(host.rect())

    def eventFilter(self, obj, event):
        if obj is self.parentWidget() and event.type() in (QEvent.Type.Resize, QEvent.Type.Show, QEvent.Type.ChildAdded, QEvent.Type.LayoutRequest):
            # a child added later -- a window's content built again under the card -- would be stacked above it
            self.cover()
            self.raise_()
        return False

    def set_text(self, text, detail=""):
        self.text = text
        self.detail = detail
        self.update()

    def angle(self):
        """Where the arc stands now: from the time held, so that a frame painted late -- a pump that came late -- puts it where it belongs rather than one step on."""
        return (time.monotonic() - self.started) / TURN_S * 360.0

    def card_rect(self):
        """The card's rectangle, centred: as wide as CARD_WIDTH or the window allows, as tall as the arc and the lines it holds."""
        metrics = QFontMetrics(self.text_font())
        lines = 1 + (1 if self.detail_line() else 0)
        height = 22 + ARC_SIZE + 14 + lines * (metrics.height() + 2) + 18 + (10 if self.fraction is not None else 0)
        width = min(CARD_WIDTH, max(160, self.width() - 32))
        return QRectF((self.width() - width) / 2, (self.height() - height) / 2, width, height)

    def detail_line(self):
        """The quieter line: the caller's detail, and the time gone once it is more than ELAPSED_AFTER_S."""
        gone = time.monotonic() - self.started
        elapsed = f"{int(gone)} s" if gone >= ELAPSED_AFTER_S else ""
        return " · ".join(part for part in (self.detail, elapsed) if part)

    def text_font(self):
        font = QFont(self.font())
        font.setWeight(QFont.Weight.DemiBold)
        return font

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        card = self.card_rect()
        radius = CARD_RADIUS
        painter.setPen(QPen(QColor(theme.colour("line")), 1))
        painter.setBrush(QColor(theme.colour("card")))
        painter.drawRoundedRect(card.adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)
        # the arc: a full track, and three quarters of it turning
        box = QRectF(card.center().x() - ARC_SIZE / 2, card.top() + 22, ARC_SIZE, ARC_SIZE)
        track = QPen(QColor(theme.colour("line")), ARC_STROKE)
        track.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(track)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(box)
        arc = QPen(QColor(theme.colour("accent")), ARC_STROKE)
        arc.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(arc)
        start = -self.angle()
        # the arc breathes between a quarter and three quarters of a turn, which reads as work rather than as a wheel
        span = 90 + 180 * (0.5 + 0.5 * math.sin(math.radians(self.angle() * 0.6)))
        painter.drawArc(box, int(start * 16), int(-span * 16))
        # the line, and the detail under it
        y = box.bottom() + 14
        width = card.width() - 28
        painter.setFont(self.text_font())
        painter.setPen(QColor(theme.colour("ink")))
        metrics = QFontMetrics(self.text_font())
        painter.drawText(QRectF(card.left() + 14, y, width, metrics.height()), Qt.AlignmentFlag.AlignHCenter,
                         metrics.elidedText(self.text, Qt.TextElideMode.ElideMiddle, int(width)))
        detail = self.detail_line()
        if detail:
            y += metrics.height() + 2
            painter.setFont(self.font())
            painter.setPen(QColor(theme.colour("muted")))
            small = QFontMetrics(self.font())
            painter.drawText(QRectF(card.left() + 14, y, width, small.height()), Qt.AlignmentFlag.AlignHCenter,
                             small.elidedText(detail, Qt.TextElideMode.ElideMiddle, int(width)))
        if self.fraction is not None:   # the progress, where it is known: a thin bar at the card's foot
            bar = QRectF(card.left() + 24, card.bottom() - 14, card.width() - 48, 4)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(theme.colour("line")))
            painter.drawRoundedRect(bar, 2, 2)
            painter.setBrush(QColor(theme.colour("accent")))
            painter.drawRoundedRect(QRectF(bar.left(), bar.top(), max(4.0, bar.width() * self.fraction), bar.height()), 2, 2)
        painter.end()


class Splash(QWidget):
    """The card in a small window of its own, frameless and on top -- for work done before any window of Woodcore's is up: a project double-clicked, whose window is being built. It is held like any other window, so a click on it does nothing."""

    def __init__(self, text="", detail=""):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle("Woodcore")
        self.resize(QSize(CARD_WIDTH + 24, 150))
        screen = QApplication.primaryScreen()
        if screen is not None:
            area = screen.availableGeometry()
            self.move(area.center().x() - self.width() // 2, area.center().y() - self.height() // 2)
        self.show()
        self.spinner = start(self, text, detail, guard=False)   # a window being built on the main thread: nothing to guard, and a guard would double the wait


class _Guard(QObject):
    """The application's event filter: what would act on a held window eaten, what only shows let through (BLOCKED). A shortcut is eaten wherever it would fire while anything is held: a QShortcut is not a widget, and the one it belongs to cannot always be told."""

    def eventFilter(self, obj, event):
        if not _guarded:
            return False
        kind = event.type()
        if kind == QEvent.Type.Shortcut:
            return True
        if kind in BLOCKED and isinstance(obj, QWidget):
            window = obj.window()
            return window in _guarded
        return False


def _install_guard():
    global _guard
    app = QApplication.instance()
    if _guard is None and app is not None:
        _guard = _Guard(app)
        app.installEventFilter(_guard)


def _remove_guard():
    """The guard taken off once no window is held over free-running work: an event filter left on the application costs every event of the session."""
    global _guard
    if _guard is None:
        return
    app = QApplication.instance()
    if app is not None:
        app.removeEventFilter(_guard)
    _guard.deleteLater()
    _guard = None


def held(window=None):
    """Whether `window` -- any window, where none is named -- is held."""
    if window is None:
        return bool(_held)
    return window.window() in _held


def start(window, text="", detail="", guard=True):
    """Holds `window` (any widget: its window is held) and shows the card over it with `text`; already held, the text is changed. Returns the card -- None where there is no window to hold, the work then simply done. `guard` -- the default -- for work that leaves the event loop free (a process, a thread): its input is eaten while it runs. False for work done on the main thread, which only `pump()` interrupts and whose input therefore waits in the queue anyway (module docstring)."""
    if window is None:
        return None
    window = window.window()
    if guard:
        _guarded.add(window)
        _install_guard()
    spinner = _held.get(window)
    if spinner is not None:
        spinner.set_text(text, detail)
        return spinner
    if not _held:
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
    spinner = _held[window] = Spinner(window, text, detail)
    pump(force=True)
    return spinner


def set_progress(window, fraction):
    """How far the work holding `window` is, 0 to 1 -- None takes the bar away; nothing where the window is not held."""
    if window is None:
        return
    spinner = _held.get(window.window())
    if spinner is not None:
        spinner.fraction = None if fraction is None else max(0.0, min(1.0, float(fraction)))
        spinner.update()


def set_text(window, text, detail=""):
    if window is None:
        return
    spinner = _held.get(window.window())
    if spinner is not None:
        spinner.set_text(text, detail)


def stop(window):
    """Lets `window` go: the card taken away and its input given back -- the pointer's own shape too once nothing is held. Safe to call on a window not held, and on one Qt has deleted."""
    try:
        window = window.window() if window is not None else None
    except RuntimeError:
        window = None
    spinner = _held.pop(window, None) if window is not None else None
    _guarded.discard(window)
    if spinner is None:
        for key in [key for key in _held if not _alive(key)]:
            spinner = _held.pop(key)
            _guarded.discard(key)
    if not _guarded:
        _remove_guard()
    if spinner is not None and _alive(spinner):
        spinner.timer.stop()
        spinner.hide()
        spinner.deleteLater()
    if not _held and QApplication.overrideCursor() is not None:
        QApplication.restoreOverrideCursor()


def stop_all():
    for window in list(_held):
        stop(window)


def _alive(widget):
    try:
        widget.objectName()
        return True
    except RuntimeError:
        return False


class hold:
    """`with busy.hold(window, text):` -- the window held for the length of the block, and let go however it ends. `guard=False` for a block of main-thread work (start())."""

    def __init__(self, window, text="", detail="", guard=True):
        self.window, self.text, self.detail, self.guard = window, text, detail, guard
        self.was_held = False

    def __enter__(self):
        self.was_held = self.window is not None and held(self.window)
        start(self.window, self.text, self.detail, guard=self.guard)
        return self

    def __exit__(self, *exc):
        if not self.was_held:   # a hold inside a hold leaves the outer one standing
            stop(self.window)
        return False


def pump(force=False):
    """Inside a long piece of main-thread work, between two of its steps: the card painted where its arc now stands, and Windows answered -- at most every PUMP_S, and only while something is held. Input is not processed here (and the guard would hold it back anyway), so nothing the engineer does runs in the middle of the work."""
    if not _held:
        return
    now = time.monotonic()
    if not force and now - _last_pump[0] < PUMP_S:
        return
    _last_pump[0] = now
    for spinner in list(_held.values()):
        if _alive(spinner):
            spinner.raise_()
    app = QApplication.instance()
    if app is not None:
        app.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)


def run_in_thread(window, text, work, detail=""):
    """`work()` -- which must touch no widget -- run in a thread of its own while `window` is held, the event loop turning the arc the whole time. Returns what it returned, or raises what it raised, on the main thread, once it is done."""
    box = {}

    def target():
        try:
            box["value"] = work()
        except BaseException as exc:   # broad: handed back to the main thread, which raises it
            box["error"] = exc

    with hold(window, text, detail):
        thread = threading.Thread(target=target, name="woodcore-busy", daemon=True)
        thread.start()
        loop = QEventLoop()
        timer = QTimer()
        timer.setInterval(FRAME_MS)
        timer.timeout.connect(lambda: thread.is_alive() or loop.quit())
        timer.start()
        if thread.is_alive():
            loop.exec()
        timer.stop()
        thread.join()
    if "error" in box:
        raise box["error"]
    return box.get("value")
