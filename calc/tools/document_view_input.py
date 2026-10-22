"""PageArea's mouse and keys -- the tool chosen, a press, a drag, a release, the wheel, a key -- a mixin of methods moved verbatim out of calc/tools/document_view.py (issue #30). PageArea names it among its bases.
"""

from PySide6.QtCore import QBuffer, QByteArray, QEvent, QIODevice, QObject, QPoint, QPointF, QRect, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import (QAbstractScrollArea, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QSplitter,
                               QToolButton, QToolTip, QVBoxLayout, QWidget)
import flowbar


# The view's tools (v0.116): «Sélection» -- the frames chosen, edited, opened, archived --, the default and what Échap comes back to; «Cadrer», a frame drawn; «Calibrer», two points.
TOOLS = ("select", "crop", "calibrate")


DEFAULT_TOOL = "select"


# A press that moves no further than this, in screen pixels, is a click.
CLICK_PX = 3


def _rounded(values):
    """Sheet coordinates to a thousandth of a unit: what a click can mean, with no float noise behind it."""
    return tuple(round(v, 3) + 0.0 for v in values)


class PageAreaInputMixin:
    """Methods of document_view.PageArea, moved verbatim (issue #30): the class names this mixin among its bases."""

    ZOOMS_ITSELF = True   # Ctrl+wheel zooms the pages, never the interface (nowheel.py, issue #85)

    def content_point(self, event):
        return event.position() + self.scroll()

    def clamped(self, page, point):
        rect = self.rects[page]
        return QPointF(min(max(point.x(), rect.left()), rect.right()), min(max(point.y(), rect.top()), rect.bottom()))

    def set_tool(self, tool):
        """«select», «crop» or «calibrate»; anything else -- None -- is the selection, the view's default (v0.116)."""
        tool = tool if tool in TOOLS else DEFAULT_TOOL
        changed = tool != self.tool
        self.tool = tool
        self.drag, self.calib = None, None
        if changed:
            self.toolChanged.emit(tool)
        self.viewport().setCursor(Qt.CursorShape.ArrowCursor if self.tool == "select" else Qt.CursorShape.CrossCursor)
        self.say_hint()
        self.viewport().update()

    def say_hint(self):
        if self.tool == "crop":
            self.hintChanged.emit(self.t("dv_hint_crop"))
        elif self.tool == "calibrate":
            self.hintChanged.emit(self.t("dv_hint_calibrate_second" if self.calib else "dv_hint_calibrate_first"))
        else:
            self.hintChanged.emit("")   # the selection says how it is used in its button's tooltip: a sentence in the bar would set the view's minimum width

    def mousePressEvent(self, event):
        point = self.content_point(event)
        if event.button() == Qt.MouseButton.MiddleButton:
            self.drag = ("pan", event.position(), self.scroll())
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        found = self.hit(point)
        if found is not None and found[0] in ("tick", "left", "right"):
            page = found[1]
            if found[0] == "tick":
                on = page not in self.used
                (self.used.add if on else self.used.discard)(page)
                self.viewport().update()
                self.pageToggled.emit(page, on)
            else:
                self.rotateRequested.emit(page, -90 if found[0] == "left" else 90)
            return
        if self.tool in ("select", "crop"):
            handle = self.frame_handle(point)
            if handle is not None:
                # an edge or a corner of a frame: dragged, it resizes that frame; clicked, it chooses it
                page, plan, edges, rect = handle
                self.drag = ("frame", page, plan, edges, QRectF(rect), point, QRectF(rect), False)
                return
        page = self.page_at(point)
        if self.tool == "crop" and page is not None:
            start = self.clamped(page, point)
            self.drag = ("crop", page, start, start)
            return
        if self.tool == "calibrate" and page is not None:
            here = self.to_sheet(page, self.clamped(page, point))
            if self.calib is not None and self.calib[0] == page:
                first = self.calib[1]
                self.calib = None
                self.calibrated.emit(page, [_rounded(first), _rounded(here)])
            else:
                self.calib = (page, here)
            self.say_hint()
            self.viewport().update()
            return
        if found is None:
            return
        self.choose(found, event.modifiers())

    def choose(self, found, modifiers):
        """A click of the selection on what `found` names: the page chosen, as before, and the frame clicked in -- the smallest holding the point -- chosen with it, Ctrl adding it to the frames chosen or taking it away; a click on a page outside every frame lets the frames go (v0.116)."""
        page = found[1]
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            self.selected = [p for p in self.selected if p != page] if page in self.selected else self.selected + [page]
        elif modifiers & Qt.KeyboardModifier.ShiftModifier and self.selected:
            order = [i.page for i in self.pages]
            a, b = sorted((order.index(self.selected[-1]), order.index(page)))
            self.selected = order[a:b + 1]
        else:
            self.selected = [page]
        self.viewport().update()
        self.pageSelected.emit(page)
        ctrl = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
        if found[0] == "crop":
            plan = found[2]
            if ctrl:
                self.set_frames([p for p in self.frames if p != plan] if plan in self.frames else self.frames + [plan])
            else:
                self.set_frames([plan])
        elif not ctrl:
            self.set_frames([])

    def mouseDoubleClickEvent(self, event):
        """A double click in a frame opens its plan (`planActivated`) -- what a single click did until v0.116, when a click came to choose the frame."""
        if event.button() != Qt.MouseButton.LeftButton or self.tool != "select":
            return super().mouseDoubleClickEvent(event)
        found = self.hit(self.content_point(event))
        if found is not None and found[0] == "crop":
            self.planActivated.emit(found[2])

    def resized(self, page, edges, rect, delta):
        """`rect` with its `edges` moved by `delta`, kept on its page and never turned inside out."""
        bounds = self.rects[page]
        r = QRectF(rect)
        if "l" in edges:
            r.setLeft(min(max(rect.left() + delta.x(), bounds.left()), rect.right() - 4))
        if "r" in edges:
            r.setRight(max(min(rect.right() + delta.x(), bounds.right()), rect.left() + 4))
        if "t" in edges:
            r.setTop(min(max(rect.top() + delta.y(), bounds.top()), rect.bottom() - 4))
        if "b" in edges:
            r.setBottom(max(min(rect.bottom() + delta.y(), bounds.bottom()), rect.top() + 4))
        return r

    def mouseMoveEvent(self, event):
        self.pointer = self.content_point(event)
        if self.drag is not None and self.drag[0] == "pan":
            _kind, start, scroll = self.drag
            delta = event.position() - start
            self.horizontalScrollBar().setValue(round(scroll.x() - delta.x()))
            self.verticalScrollBar().setValue(round(scroll.y() - delta.y()))
            return
        if self.drag is not None and self.drag[0] == "crop":
            _kind, page, start, _current = self.drag
            self.drag = ("crop", page, start, self.clamped(page, self.pointer))
        elif self.drag is not None and self.drag[0] == "frame":
            kind, page, plan, edges, rect, start, _current, moved = self.drag
            delta = self.pointer - start
            moved = moved or abs(delta.x()) > CLICK_PX or abs(delta.y()) > CLICK_PX
            self.drag = (kind, page, plan, edges, rect, start, self.resized(page, edges, rect, delta) if moved else QRectF(rect), moved)
        elif self.drag is None and self.tool in ("select", "crop"):
            handle = self.frame_handle(self.pointer)
            if handle is None:
                cursor = Qt.CursorShape.ArrowCursor if self.tool == "select" else Qt.CursorShape.CrossCursor
            else:
                edges = handle[2]
                if edges in ({"l", "t"}, {"r", "b"}):
                    cursor = Qt.CursorShape.SizeFDiagCursor
                elif len(edges) == 2:
                    cursor = Qt.CursorShape.SizeBDiagCursor
                elif edges & {"l", "r"}:
                    cursor = Qt.CursorShape.SizeHorCursor
                else:
                    cursor = Qt.CursorShape.SizeVerCursor
            self.viewport().setCursor(cursor)
        self.viewport().update()

    def mouseReleaseEvent(self, event):
        drag, self.drag = self.drag, None
        if drag is None:
            return
        if drag[0] == "crop" and event.button() == Qt.MouseButton.LeftButton:
            _kind, page, start, _current = drag
            end = self.clamped(page, self.content_point(event))
            box = QRectF(start, end).normalized()
            if box.width() >= 4 and box.height() >= 4:
                x0, y0 = self.to_sheet(page, box.topLeft())
                x1, y1 = self.to_sheet(page, box.bottomRight())
                self.cropDrawn.emit(page, _rounded((x0, y0, x1 - x0, y1 - y0)))
        elif drag[0] == "frame" and event.button() == Qt.MouseButton.LeftButton:
            _kind, page, plan, _edges, _rect, _start, box, moved = drag
            if moved:
                x0, y0 = self.to_sheet(page, box.topLeft())
                x1, y1 = self.to_sheet(page, box.bottomRight())
                self.set_frames([plan])
                self.frameEdited.emit(page, plan, _rounded((x0, y0, x1 - x0, y1 - y0)))
            else:
                self.choose(("crop", page, plan), event.modifiers())
        self.viewport().update()

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            steps = event.angleDelta().y() / 120.0
            if steps:
                self.set_zoom(self.zoom * 1.2 ** steps, event.position())
            event.accept()
            return
        super().wheelEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.drag is not None or self.calib is not None:
                self.drag, self.calib = None, None   # the gesture under way, first
                self.say_hint()
                self.viewport().update()
            elif self.tool != DEFAULT_TOOL:
                self.set_tool(DEFAULT_TOOL)          # then the tool itself, back to the selection
            elif self.frames:
                self.set_frames([])                  # then the frames chosen
            return
        if event.key() == Qt.Key.Key_Delete and self.frames and self.drag is None:
            self.framesDeleteRequested.emit(list(self.frames))
            return
        super().keyPressEvent(event)

    def leaveEvent(self, event):
        self.pointer = None
        self.viewport().update()
        super().leaveEvent(event)

    def viewportEvent(self, event):
        if event.type() == QEvent.Type.ToolTip:
            found = self.hit(event.position() + self.scroll()) if hasattr(event, "position") else self.hit(QPointF(event.pos()) + self.scroll())
            tips = {"tick": ("dv_in_plans", "dv_in_plans_use"), "left": ("dv_rotate_left", None), "right": ("dv_rotate_right", None)}
            if found is not None and found[0] in tips:
                name, usage = tips[found[0]]
                QToolTip.showText(event.globalPos(), flowbar.tip_text(self.t(name), self.t(usage) if usage else ""), self.viewport())
            else:
                QToolTip.hideText()
            return True
        return super().viewportEvent(event)
