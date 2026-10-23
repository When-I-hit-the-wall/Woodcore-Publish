"""The right pane of a calculation tab, made of modules (spec 2026-10-22-onglet-neige-type, UI-006, UI-007, UI-008, REQ-003, REQ-010, ARCH-005, D-6, D-26, D-27).

Each block of the pane is a **module**: a header -- its title, the summary it says while folded («✓ complet · 1 info», «q_k,11 = 2.21 kN/m²»), ▾/▸, ⧉ and, for a pinned excerpt, × -- over its body. They are **reordered by drag and drop** on their header, easier folded, and never by arrows (D-6); **▾/▸** folds one to its header; **×** unpins an excerpt, the others fold but never close; **⧉** opens a minimal Woodcore window of the module, zoomed by Ctrl+wheel, the module staying in the pane too. The **order and the folding** are kept per tab on this machine (layout_store.get_state/put_state, D-26) -- the fixed modules' alone: the pinned excerpts are the session's, kept through a window rebuilt (`state`, D-27), put under «Résultats» in the order they were pinned, one excerpt never twice (REQ-003).

A module is described, never subclassed (`ModuleSpec`): its id, its title, a factory of its body -- called again for the ⧉ window, the two bodies refreshed together (`refresh`) -- and whether it closes. Nothing here knows a domain (ARCH-005): the snow tab adds its modules through calc/tools/calc_tab.py.
"""

from dataclasses import dataclass

from PySide6.QtCore import QMimeData, QPoint, Qt, Signal
from PySide6.QtGui import QDrag, QPainter
from PySide6.QtWidgets import (QApplication, QFrame, QGraphicsScene, QGraphicsView, QHBoxLayout, QLabel, QScrollArea, QSizePolicy,
                               QToolButton, QVBoxLayout, QWidget)

import layout_store
import theme

MIME = "application/x-woodcore-module"
ZOOM_STEP = 1.15


@dataclass
class ModuleSpec:
    """One module: `id` unique in its pane, `title`, `factory()` -> a new body (a widget; its `refresh()`, where it has one, is called by `ModulePane.refresh`), `closable` (a pinned excerpt), `kind` (state, results, excerpt, drawing, chart: what it is, for a test and the pane's order)."""
    id: str
    title: str
    factory: object
    closable: bool = False
    kind: str = ""


class _Header(QFrame):
    """A module's header: what is dragged to reorder it."""

    def __init__(self, module):
        super().__init__(module)
        self.module = module
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._press = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._press is None or (event.position().toPoint() - self._press).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        data = QMimeData()
        data.setData(MIME, self.module.spec.id.encode("utf-8"))
        drag.setMimeData(data)
        drag.setPixmap(self.grab())
        self._press = None
        drag.exec(Qt.DropAction.MoveAction)

    def mouseReleaseEvent(self, event):
        self._press = None
        super().mouseReleaseEvent(event)


class Module(QFrame):
    """One module in its pane (see the module's docstring)."""

    def __init__(self, pane, spec):
        super().__init__(pane)
        self.pane, self.spec = pane, spec
        self.setObjectName("calcModule")
        self.setProperty("card", True)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        column = QVBoxLayout(self)
        column.setContentsMargins(8, 6, 8, 8)
        column.setSpacing(4)
        self.header = _Header(self)
        row = QHBoxLayout(self.header)
        row.setContentsMargins(0, 0, 0, 0)
        t = pane.t
        self.fold_button = QToolButton()
        self.fold_button.setAutoRaise(True)
        self.fold_button.clicked.connect(lambda: self.set_folded(not self.folded))
        self.title = QLabel(spec.title)
        self.title.setStyleSheet("font-weight: 600;")
        self.title.setToolTip(t("ct_drag"))
        self.summary = QLabel("")
        self.summary.setStyleSheet("color: %s;" % theme.colour("muted"))
        self.summary.setTextFormat(Qt.TextFormat.RichText)
        self.window_button = QToolButton()
        self.window_button.setText("⧉")
        self.window_button.setAutoRaise(True)
        self.window_button.setToolTip(t("ct_window"))
        self.window_button.clicked.connect(lambda: pane.open_window(spec.id))
        row.addWidget(self.fold_button)
        row.addWidget(self.title)
        row.addWidget(self.summary, 1)
        row.addWidget(self.window_button)
        self.close_button = None
        if spec.closable:
            self.close_button = QToolButton()
            self.close_button.setText("×")
            self.close_button.setAutoRaise(True)
            self.close_button.setToolTip(t("ct_unpin"))
            self.close_button.clicked.connect(lambda: pane.remove(spec.id))
            row.addWidget(self.close_button)
        column.addWidget(self.header)
        self.body = spec.factory()
        column.addWidget(self.body)
        self.folded = False
        self.set_folded(False, save=False)

    def set_folded(self, folded, save=True):
        self.folded = bool(folded)
        self.body.setVisible(not self.folded)
        self.summary.setVisible(self.folded)
        self.fold_button.setText("▸" if self.folded else "▾")
        self.fold_button.setToolTip(self.pane.t("ct_unfold" if self.folded else "ct_fold"))
        if save:
            self.pane.save_state()

    def set_summary(self, text):
        self.summary.setText(text)


class ModulePane(QScrollArea):
    """A tab's right pane of modules. `tab_key` names its state on this machine; `store` is layout_store's (a test's own)."""

    orderChanged = Signal(list)
    removed = Signal(str)

    def __init__(self, t, tab_key, store=None, parent=None):
        super().__init__(parent)
        self.t = t
        self.tab_key = tab_key
        self.store = store
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)   # a module is as wide as the pane: a drawing or an excerpt scales to it
        self.inner = QWidget()
        self.inner.setObjectName("cardGround")
        self.column = QVBoxLayout(self.inner)
        self.column.setContentsMargins(0, 8, 4, 0)
        self.column.setSpacing(8)
        self.column.addStretch(1)
        self.setWidget(self.inner)
        self.setAcceptDrops(True)
        self.modules = {}       # id -> Module
        self.order = []         # ids, top to bottom
        self.pins = []          # the excerpts pinned, in the order they were
        self.windows = {}       # id -> [ModuleWindow]
        self.kept = layout_store.get_state(tab_key, self.store)

    # -- what the tab adds --

    def add(self, spec):
        """A fixed module, placed where this machine last had it (D-26) -- after the others where it has no place kept."""
        module = Module(self, spec)
        self.modules[spec.id] = module
        self.order.append(spec.id)
        if spec.id in self.kept.get("folded", ()):
            module.set_folded(True, save=False)
        self._arrange(self._kept_order())
        return module

    def pin(self, spec, after="results"):
        """A pinned excerpt (REQ-003): under the module `after` and the excerpts pinned before it, once -- pinned again, it is only unfolded. Returns its module."""
        if spec.id in self.modules:
            self.modules[spec.id].set_folded(False)
            return self.modules[spec.id]
        module = Module(self, spec)
        self.modules[spec.id] = module
        self.pins.append(spec.id)
        order = [i for i in self.order if i not in self.pins]
        at = order.index(after) + 1 if after in order else len(order)
        order[at:at] = self.pins
        self._arrange(order)
        return module

    def remove(self, module_id):
        """An excerpt unpinned (×): the fixed modules fold, they never close."""
        module = self.modules.get(module_id)
        if module is None or not module.spec.closable:
            return
        for window in self.windows.pop(module_id, []):
            window.close()
        self.modules.pop(module_id)
        self.pins.remove(module_id)
        self.order.remove(module_id)
        module.setParent(None)
        module.deleteLater()
        self.removed.emit(module_id)
        self.save_state()

    def refresh(self, module_id=None):
        """The bodies of a module -- in the pane and in its windows -- told to show the tab's state again (`refresh()`); every module where none is named."""
        for mid in ([module_id] if module_id else list(self.modules)):
            bodies = [self.modules[mid].body] if mid in self.modules else []
            bodies += [w.body for w in self.windows.get(mid, []) if w.isVisible()]
            for body in bodies:
                if hasattr(body, "refresh"):
                    body.refresh()

    def summary(self, module_id, text):
        if module_id in self.modules:
            self.modules[module_id].set_summary(text)

    def ids(self):
        return list(self.order)

    # -- the order --

    def _kept_order(self):
        kept = [i for i in self.kept.get("order", ()) if i in self.modules and i not in self.pins]
        rest = [i for i in self.order if i not in kept]
        return kept + rest

    def _arrange(self, order):
        self.order = list(order)
        while self.column.count() > 1:
            self.column.takeAt(0)
        for at, mid in enumerate(self.order):
            self.column.insertWidget(at, self.modules[mid])
        self.orderChanged.emit(list(self.order))

    def move(self, module_id, index):
        """`module_id` put at `index` of the order -- what a drop does (D-6)."""
        if module_id not in self.order:
            return
        order = [i for i in self.order if i != module_id]
        order.insert(max(0, min(index, len(order))), module_id)
        self._arrange(order)
        self.save_state()

    def save_state(self):
        """The fixed modules' order and folding kept for this tab on this machine (D-26) -- the pins are the session's (D-27)."""
        fixed = [i for i in self.order if i not in self.pins]
        state = {"order": fixed, "folded": [i for i in fixed if self.modules[i].folded]}
        self.kept = state
        layout_store.put_state(self.tab_key, state, self.store)

    def state(self):
        """What a window rebuilt gives back (`restore_pins`): the excerpts pinned and which are folded."""
        return {"pins": list(self.pins), "folded": [i for i in self.pins if self.modules[i].folded]}

    # -- drag and drop --

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(MIME):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(MIME):
            event.acceptProposedAction()

    def dropEvent(self, event):
        if not event.mimeData().hasFormat(MIME):
            return
        module_id = bytes(event.mimeData().data(MIME)).decode("utf-8")
        y = self.inner.mapFrom(self, event.position().toPoint()).y()
        index = 0
        for mid in self.order:
            if mid == module_id:
                continue
            widget = self.modules[mid]
            if y > widget.y() + widget.height() / 2:
                index += 1
        self.move(module_id, index)
        event.acceptProposedAction()

    # -- the ⧉ window --

    def open_window(self, module_id):
        spec = self.modules[module_id].spec
        window = ModuleWindow(spec, self)
        self.windows.setdefault(module_id, []).append(window)
        window.show()
        return window


class ModuleWindow(QGraphicsView):
    """A module in a minimal Woodcore window (UI-007): a new body of it in a scene, zoomed by Ctrl+wheel -- the module stays in its pane, the two refreshed together."""

    ZOOMS_ITSELF = True   # nowheel.py leaves its Ctrl+wheel to it

    def __init__(self, spec, pane):
        super().__init__(None)
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.setWindowTitle(spec.title)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform | QPainter.RenderHint.TextAntialiasing)
        self.body = spec.factory()
        if hasattr(self.body, "refresh"):
            self.body.refresh()
        self.scene_ = QGraphicsScene(self)
        self.proxy = self.scene_.addWidget(self.body)
        self.setScene(self.scene_)
        self.resize(max(420, self.body.sizeHint().width() + 40), max(300, self.body.sizeHint().height() + 40))
        self.zoom = 1.0

    def zoom_by(self, factor):
        self.zoom = max(0.25, min(8.0, self.zoom * factor))
        self.resetTransform()
        self.scale(self.zoom, self.zoom)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.zoom_by(ZOOM_STEP if event.angleDelta().y() > 0 else 1 / ZOOM_STEP)
            event.accept()
            return
        super().wheelEvent(event)
