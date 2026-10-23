"""The norm under a datum: the ⓘ beside each field, the bubble it opens, the excerpt it shows (spec 2026-10-22-onglet-neige-type, UI-003, UI-004, UI-005, REQ-001 to REQ-004; the engineer's decisions of 21-22.10.2026).

**Hover** a ⓘ for about `DELAY_MS`: a bubble shows, for each excerpt the field cites, the norm, its edition, the clause and the page, then **the norm's words first and the image of the excerpt under them** (D-4), cut out of the shipped PDF (excerpt_image) -- no tabs. A tile's bubble shows the image alone (T28: `bare`). The bubble stays while the pointer is on the ⓘ or on it; it opens under the ⓘ, above it where there is no room under, and scrolls inside where neither holds it -- it never covers what it explains (`place`, a pure function a test holds). **Click** the ⓘ or the bubble: its excerpts are pinned as modules of the right pane (`pinned`). **Ctrl+click**: the edition is opened in Woodcore's reader at the clause, framed -- or, for an excerpt with a map, the map's site (`opened`). The language is the window's, German where the norm has no edition in it (excerpts.excerpt).

Nothing here knows the snow: the tab hands each ⓘ the norm file and the excerpt ids its declaration names (contracts.Field.excerpts). The bubble is a tool window that never takes the focus, hidden when its tab is hidden, its window deactivated or its view changed (ARCH-RISK-W11).
"""

from PySide6.QtCore import QEvent, QObject, QPoint, QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QCursor, QGuiApplication, QPixmap
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

import excerpt_image
import theme
from norms import excerpts as norm_excerpts

# How long the pointer rests on a ⓘ before its bubble opens, and how long it may leave both before the bubble closes
DELAY_MS = 350
LEAVE_MS = 250
# The bubble's widest, and the gap between it and its ⓘ
WIDTH = 460
GAP = 6


def place(trigger, size, screen):
    """Where the bubble goes (UI-003): `trigger` the ⓘ's rectangle and `screen` the screen's available one, both global, `size` the bubble's natural size. Under the ⓘ where it fits; above it where it does not and fits there; else on the side with more room, as high as that room, scrolling inside -- never over the ⓘ. Returns (QRect, whether it must scroll)."""
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


class FitImage(QLabel):
    """An excerpt's image as wide as the room it is given, never wider than itself, its height following: what lets a pinned excerpt sit in a narrow pane without widening it."""

    def __init__(self, image, parent=None):
        super().__init__(parent)
        self.original = QPixmap.fromImage(image)
        self.setMinimumWidth(60)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._fit(min(self.original.width(), WIDTH - 24))

    def _fit(self, width):
        width = max(1, min(width, self.original.width()))
        self.setPixmap(self.original.scaledToWidth(width, Qt.TransformationMode.SmoothTransformation))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        width = min(width, self.original.width())
        return round(self.original.height() * width / max(self.original.width(), 1))

    def sizeHint(self):
        width = min(self.original.width(), WIDTH - 24)
        return QSize(width, self.heightForWidth(width))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if abs(self.pixmap().width() - min(self.width(), self.original.width())) > 1:
            self._fit(self.width())


class ExcerptView(QWidget):
    """The excerpts of one ⓘ, one under the other: for each its head -- the norm, the clause as its edition names it, the page --, its words, then its image (D-4); `bare` the image alone. What the bubble shows and a pinned module keeps."""

    def __init__(self, items, t, bare=False, parent=None):
        super().__init__(parent)
        self.items = list(items)
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(10)
        for e in self.items:
            if not bare:
                head = QLabel(t("ct_bubble_head", norm=e.edition, ref=e.ref, page=e.page))
                head.setStyleSheet("font-weight: 600;")
                column.addWidget(head)
                words = QLabel(e.text.replace("μ_", "μ").replace("_", ""))
                words.setWordWrap(True)
                words.setTextFormat(Qt.TextFormat.PlainText)
                words.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                column.addWidget(words)
            image = excerpt_image.image(e)
            if image is not None:
                column.addWidget(FitImage(image))
            else:
                missing = QLabel(t("ct_no_pdf", file=e.file))
                missing.setWordWrap(True)
                missing.setStyleSheet("color: %s;" % theme.colour("muted"))
                column.addWidget(missing)


class NormBubble(QFrame):
    """The bubble itself: a tool window without a frame that never takes the focus, its excerpts in a scroll area of its own."""

    clicked = Signal(object)   # the QMouseEvent's modifiers

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setObjectName("normBubble")
        self.setStyleSheet("#normBubble { background: %s; border: 1px solid %s; border-radius: 6px; }" % (theme.colour("card"), theme.colour("line")))
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        column = QVBoxLayout(self)
        column.setContentsMargins(10, 10, 10, 10)
        column.addWidget(self.scroll)
        self.scrolling = False

    def show_for(self, view, trigger_rect, screen_rect):
        view.setMaximumWidth(WIDTH - 24)
        self.scroll.setWidget(view)
        natural = QSize(WIDTH, view.sizeHint().height() + 24)
        rect, self.scrolling = place(trigger_rect, natural, screen_rect)
        self.setGeometry(rect)
        self.show()
        self.raise_()

    def mousePressEvent(self, event):
        self.clicked.emit(event.modifiers())
        event.accept()


class InfoMark(QLabel):
    """The ⓘ beside a datum (T24): what the bubble opens over, a click pins, a Ctrl+click opens."""

    def __init__(self, tip="", parent=None):
        super().__init__("ⓘ", parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("")
        self.setAccessibleDescription(tip)
        self.setStyleSheet("color: %s; padding: 0 3px;" % theme.colour("accent"))


class BubbleController(QObject):
    """The bubbles of one tab: `attach(widget, norm, ids, bare)` makes `widget` -- a ⓘ, a tile -- open the bubble of the excerpts `ids` of the norm file `norm`. `pinned(norm, ids)` is emitted at a click, `opened(norm, id)` at a Ctrl+click: the tab pins (module_pane) and opens (norm_reader). `lang()` gives the window's language, `t` its words."""

    pinned = Signal(str, tuple)
    opened = Signal(str, str)

    def __init__(self, t, lang, parent=None):
        super().__init__(parent)
        self.t, self.lang = t, lang
        self.bubble = None
        self.targets = {}         # id(widget) -> (norm, ids, bare)
        self.current = None       # the widget whose bubble is open
        self.waiting = None       # the widget the pointer rests on
        self.show_timer = QTimer(self)
        self.show_timer.setSingleShot(True)
        self.show_timer.setInterval(DELAY_MS)
        self.show_timer.timeout.connect(self._show)
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.setInterval(LEAVE_MS)
        self.hide_timer.timeout.connect(self._maybe_hide)

    def attach(self, widget, norm, ids, bare=False):
        self.targets[id(widget)] = (norm, tuple(ids), bare)
        widget.installEventFilter(self)
        widget.setMouseTracking(True)

    def excerpts(self, norm, ids):
        return [norm_excerpts.excerpt(norm, eid, self.lang()) for eid in ids]

    def eventFilter(self, obj, event):
        target = self.targets.get(id(obj))
        if target is None:
            return False
        kind = event.type()
        try:
            if kind == QEvent.Type.Enter:
                self.waiting = obj
                self.hide_timer.stop()
                if self.current is obj and self.bubble is not None and self.bubble.isVisible():
                    return False
                self.show_timer.start()
            elif kind == QEvent.Type.Leave:
                self.show_timer.stop()
                self.hide_timer.start()
            elif kind == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self.show_timer.stop()
                self._act(target, event.modifiers())
                return not hasattr(obj, "isCheckable") or not obj.isCheckable()   # a tile is still chosen by its click
            elif kind in (QEvent.Type.Hide, QEvent.Type.Wheel):
                self.hide()
        except RuntimeError:   # the widget was deleted with a window rebuilt (ARCH-RISK-W11)
            self.hide()
        return False

    def _act(self, target, modifiers):
        norm, ids, _bare = target
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            self.opened.emit(norm, ids[0])
        else:
            self.pinned.emit(norm, ids)
        self.hide()

    def _show(self):
        obj = self.waiting
        if obj is None:
            return
        try:
            if not obj.isVisible():
                return
            norm, ids, bare = self.targets[id(obj)]
            rect = QRect(obj.mapToGlobal(QPoint(0, 0)), obj.size())
        except (RuntimeError, KeyError):
            return
        if self.bubble is None:
            self.bubble = NormBubble()
            self.bubble.installEventFilter(_BubbleHover(self, self.bubble))
            self.bubble.clicked.connect(lambda modifiers: self.current is not None and self._act(self.targets[id(self.current)], modifiers))
        screen = QGuiApplication.screenAt(rect.center()) or QGuiApplication.primaryScreen()
        self.bubble.show_for(ExcerptView(self.excerpts(norm, ids), self.t, bare), rect, screen.availableGeometry())
        self.current = obj

    def _maybe_hide(self):
        if self.bubble is not None and self.bubble.isVisible() and self.bubble.geometry().contains(QCursor.pos()):
            return
        self.hide()

    def hide(self):
        self.show_timer.stop()
        self.hide_timer.stop()
        if self.bubble is not None:
            self.bubble.hide()
        self.current = None


class _BubbleHover(QObject):
    """The pointer on the bubble keeps it open; leaving it closes it after the same delay as leaving the ⓘ."""

    def __init__(self, controller, parent):
        super().__init__(parent)
        self.controller = controller

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Enter:
            self.controller.hide_timer.stop()
        elif event.type() == QEvent.Type.Leave:
            self.controller.hide_timer.start()
        return False
