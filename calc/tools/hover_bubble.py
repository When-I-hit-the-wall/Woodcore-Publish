"""A bubble that opens at the hover, stays open while the pointer is in it, is pinned by a click and closed by Escape, a click elsewhere or a scroll (spec 2026-10-24-onglet-commandes-pages, ARCH-002, UI-008).

`QToolTip` closes the moment the pointer enters it and holds no image one can hover, and the bubble of a command's values must be entered -- its values are hovered one by one, each showing its call and its print. So the bubble is a frameless tool window that never takes the focus (as norm_bubble's), and its controller owns its life: `open(key, widget, trigger, width)` shows a widget under the trigger rectangle (above it where there is no room, never off the screen: `place`), `leave()` closes it LEAVE_MS later unless the pointer reaches the bubble, `pin()` keeps it until Escape, a click outside or the scroll of the page it explains (`watch_scroll`). Nothing here knows what it shows: the commands tab hands it its widgets, and the domains and variables tabs may hand it theirs (#113, #114).

`place` and `GAP` were norm_bubble's; norm_bubble imports them from here.
"""

from PySide6.QtCore import QEvent, QObject, QRect, Qt, QTimer, Signal
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import QApplication, QFrame, QScrollArea, QVBoxLayout

import theme

LEAVE_MS = 300   # the prototype's: the pointer may cross the gap to the bubble
GAP = 6


def place(trigger, size, screen):
    """Where the bubble goes: `trigger` the rectangle it explains and `screen` the screen's available one, both global, `size` the bubble's natural size. Under the trigger where it fits; above it where it does not and fits there; else on the side with more room, as high as that room, scrolling inside -- never over the trigger. Returns (QRect, whether it must scroll)."""
    width = min(size.width(), screen.width())
    x = max(screen.left(), min(trigger.left(), screen.right() - width + 1))
    below = screen.bottom() - (trigger.bottom() + GAP)
    above = (trigger.top() - GAP) - screen.top()
    height = size.height()
    if height <= below:
        return QRect(x, trigger.bottom() + GAP + 1, width, height), False
    if height <= above:
        return QRect(x, trigger.top() - GAP - height, width, height), False
    if below >= above:
        return QRect(x, trigger.bottom() + GAP + 1, width, max(below, 1)), True
    return QRect(x, screen.top(), width, max(above, 1)), True


class HoverBubble(QFrame):
    """The bubble: a frameless tool window that never takes the focus, its content in a scroll area of its own."""

    entered = Signal()
    left = Signal()
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setObjectName("hoverBubble")
        self.setStyleSheet("#hoverBubble { background: %s; border: 1px solid %s; border-radius: 8px; }" % (theme.colour("card"), theme.colour("line-strong")))
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        column = QVBoxLayout(self)
        column.setContentsMargins(10, 8, 10, 8)
        column.addWidget(self.scroll)
        self.scrolling = False

    def show_for(self, widget, trigger, width):
        """Shows `widget`, at most `width` wide, under the global rectangle `trigger` (place)."""
        widget.setMaximumWidth(width - 22)
        self.scroll.setWidget(widget)
        self.trigger, self.width_max = trigger, width
        self.refit()

    def refit(self):
        """Places the bubble again for what it shows now -- a value's print taller than the one before it."""
        widget, trigger, width = self.scroll.widget(), self.trigger, self.width_max
        if widget is None:
            return
        widget.adjustSize()
        hint = widget.sizeHint()
        natural = hint.expandedTo(widget.minimumSizeHint()).expandedTo(widget.minimumSize())
        inner = min(natural.width(), width - 22)
        layout = widget.layout()
        if layout is not None and layout.hasHeightForWidth():
            natural.setHeight(max(layout.totalHeightForWidth(inner), natural.height() if natural.width() <= inner else 0))
        natural.setWidth(inner)
        size = natural.grownBy(self.layout().contentsMargins())
        size.setWidth(min(max(size.width(), 120), width))
        size.setHeight(size.height() + 4)
        screen = QGuiApplication.screenAt(trigger.center()) or QGuiApplication.primaryScreen()
        rect, self.scrolling = place(trigger, size, screen.availableGeometry())
        self.setGeometry(rect)
        self.show()
        self.raise_()

    def enterEvent(self, event):
        self.entered.emit()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.left.emit()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.clicked.emit()
        event.accept()


class HoverController(QObject):
    """The life of one bubble (UI-008): open at a hover, kept while the pointer is in it, closed LEAVE_MS after it leaves both, pinned by a click; Escape, a click outside it or a scroll of what it explains closes it, pinned or not. `closed` is emitted when it closes."""

    closed = Signal()

    def __init__(self, parent=None, leave_ms=LEAVE_MS):
        super().__init__(parent)
        self.bubble = HoverBubble()
        self.bubble.entered.connect(self.keep)
        self.bubble.left.connect(self._bubble_left)
        self.bubble.clicked.connect(self.pin)
        self.key = None
        self.pinned = False
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(leave_ms)
        self.timer.timeout.connect(self._maybe_close)
        self._filtering = False

    # -- what the trigger says --

    def open(self, key, widget, trigger, width, pin=False):
        """Shows `widget` for `key` under the global rectangle `trigger`; a bubble pinned on another key is replaced only by a click (`pin`)."""
        if self.pinned and not pin and key != self.key:
            return
        self.timer.stop()
        self.key = key
        self.pinned = pin or (self.pinned and key == self.key)
        self.bubble.show_for(widget, trigger, width)
        if not self._filtering:
            QApplication.instance().installEventFilter(self)
            self._filtering = True

    def leave(self):
        """The pointer left the trigger: the bubble closes LEAVE_MS later, unless the pointer is in it by then or it is pinned."""
        if self.is_open() and not self.pinned:
            self.timer.start()

    def keep(self):
        self.timer.stop()

    def pin(self):
        if self.is_open():
            self.pinned = True
            self.timer.stop()

    def is_open(self):
        return self.bubble.isVisible()

    def close(self):
        self.timer.stop()
        was = self.is_open()
        self.bubble.hide()
        self.key, self.pinned = None, False
        if self._filtering:
            QApplication.instance().removeEventFilter(self)
            self._filtering = False
        if was:
            self.closed.emit()

    def watch_scroll(self, scrollbar):
        """A scroll of the page the bubble explains closes it: what it pointed at has moved."""
        scrollbar.valueChanged.connect(lambda _value: self.close())

    # -- inside --

    def _bubble_left(self):
        if not self.pinned:
            self.timer.start()

    def _maybe_close(self):
        if self.bubble.isVisible() and self.bubble.geometry().contains(QCursor.pos()):
            return
        if not self.pinned:
            self.close()

    def eventFilter(self, obj, event):
        kind = event.type()
        if kind == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape and self.is_open():
            self.close()
            return True
        if kind == QEvent.Type.MouseButtonPress and self.is_open():
            inside = self.bubble.geometry().contains(event.globalPosition().toPoint()) if hasattr(event, "globalPosition") else False
            if not inside and obj is not self.bubble and not self._is_trigger(obj):
                self.close()
        return False

    def _is_trigger(self, obj):
        """A press on what opened the bubble is the trigger's to decide (its click pins it)."""
        return getattr(obj, "hover_trigger", False) or getattr(getattr(obj, "parent", lambda: None)(), "hover_trigger", False)
