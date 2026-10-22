"""The base every drawing canvas of the window derives from -- the position plan's, the fire plan's, the schemas' and the static models' (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, D1).

Until v0.120 the schemas' and the static models' canvases each wrote the same fourteen methods -- the zoom about the pointer and its two limits, the grid, the cursor, the snap marker, the handles, the tracking's acquisition and its readout, a length dimension under way -- and the plan's two of them, word for word: a fix made to one was a fix the others waited for. They are written once here. What differs from one canvas to another is said by its class, not written again:

* `MODEL`, the domain module it draws (`domains.statics`, `domains.schema`): `entry_of`, `next_id`, `tracking_rays`, `dimension_ends`, `fmt_number`…;
* `TOOLS`, its tools by name; `ROUND`, how a coordinate is saved (canvas_items.saved_at);
* `MIN_ZOOM` and `MAX_ZOOM`, `GRID_STEPS` and `GRID_MIN_PX`, `SELECT_COLOUR`.

A canvas keeps for itself what it does its own way -- the plan's zoom, which re-renders its background, is the plan's -- and the undo is the tab's, not the canvas's (canvas_editor.CanvasEditorTab). Placed before QGraphicsView among a canvas's bases, so that `super()` here reaches Qt's own handler.
"""

import math

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QPainterPath
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem

import theme
from canvas_items import cosmetic


class CanvasBase:
    """What the four canvases share. Its class attributes are each canvas's to set (see the module's docstring)."""

    ZOOMS_ITSELF = True   # Ctrl+wheel zooms the drawing, never the interface (nowheel.py, issue #85)

    MODEL = None
    TOOLS = {}
    ROUND = staticmethod(round)
    MIN_ZOOM = 1.0
    MAX_ZOOM = 1.0
    GRID_STEPS = ()
    GRID_MIN_PX = 1.0
    SELECT_COLOUR = None

    # --- the zoom ---------------------------------------------------------------------

    def clamp_zoom(self):
        scale = self.scale_px()
        if scale < self.MIN_ZOOM:
            self.scale(self.MIN_ZOOM / scale, self.MIN_ZOOM / scale)
        elif scale > self.MAX_ZOOM:
            self.scale(self.MAX_ZOOM / scale, self.MAX_ZOOM / scale)

    def wheelEvent(self, event):
        """The wheel always zooms, about the pointer, between two absolute limits -- never against a limit that moves with the model."""
        steps = event.angleDelta().y() / 120.0
        if steps == 0:
            return
        self.zoom_at(event.position(), 1.15 ** steps)

    def zoom_at(self, position, factor):
        """Scales the view by `factor` about `position`, a point of the viewport: the point of the model under it stays under it. The two absolute limits are held here, so every way of zooming meets the same ones."""
        scale = self.scale_px()
        factor = max(self.MIN_ZOOM / scale, min(factor, self.MAX_ZOOM / scale))
        if abs(factor - 1.0) < 1e-12:
            return
        at = position.toPoint()
        anchor = self.mapToScene(at)
        self.grow_scene()
        self.scale(factor, factor)
        drift = self.mapFromScene(anchor) - at
        self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + drift.x())
        self.verticalScrollBar().setValue(self.verticalScrollBar().value() + drift.y())
        self.update_helpers()

    def grid_step(self):
        """The grid the view is showing: the step the engineer forced, or the finest that is still far enough apart on screen."""
        if self.grid_mode != "auto":
            step = float(self.grid_mode)
            for candidate, heavy in self.GRID_STEPS:
                if abs(candidate - step) < 1e-9:
                    return candidate, heavy
            return step, step * 5
        scale = self.scale_px()
        # finest first: the step taken is the smallest one whose lines are still far enough apart to be read
        for step, heavy in reversed(self.GRID_STEPS):
            if step * scale >= self.GRID_MIN_PX:
                return step, heavy
        return self.GRID_STEPS[0]

    # --- the pointer and the keys -----------------------------------------------------

    def restore_cursor(self):
        self._over_label = False
        if self.tool == "pan" or self.space_down:
            self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
        elif self.tool == "select":
            self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.viewport().setCursor(Qt.CursorShape.CrossCursor)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self.space_down = False
            self.restore_cursor()
            return
        super().keyReleaseEvent(event)

    def leaveEvent(self, event):
        self.cursor = None
        self.acquire_timer.stop()
        self.update_helpers()
        super().leaveEvent(event)

    # --- the selection and its handles ------------------------------------------------

    def selected(self):
        """The (collection, entry) selected, or (None, None)."""
        if not self.selection:
            return None, None
        collection, eid = self.selection
        return collection, self.MODEL.entry_of(self.source, collection, eid)

    def add_handle(self, at):
        handle = QGraphicsRectItem(-4, -4, 8, 8)
        handle.setPos(at)
        handle.setBrush(QBrush(theme.qcolor("paper")))
        handle.setPen(cosmetic(self.SELECT_COLOUR, 1.6))
        handle.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        handle.setZValue(21)
        self.scene().addItem(handle)
        self.handles.append(handle)

    def finish_turning(self):
        if self.turning is not None:
            self.turning = None
            self.end_change()
            self.selection_changed.emit()

    # --- the snap and the tracking ----------------------------------------------------

    def show_snap(self, point, kind):
        path = QPainterPath()
        if kind and kind != "shift":
            s = 6.0
            if kind == "point":
                path.addRect(-s, -s, 2 * s, 2 * s)
            elif kind == "midpoint":
                path.moveTo(0, -s)
                path.lineTo(s, s)
                path.lineTo(-s, s)
                path.closeSubpath()
            elif kind in ("crossing", "ray-crossing"):
                path.moveTo(-s, -s)
                path.lineTo(s, s)
                path.moveTo(-s, s)
                path.lineTo(s, -s)
            elif kind == "grid":
                path.addEllipse(QPointF(0, 0), s * 0.5, s * 0.5)
            else:
                path.addEllipse(QPointF(0, 0), s * 0.8, s * 0.8)
            self.snap_marker.setPos(self.qp(point))
        self.snap_marker.setPath(path)

    def acquire(self):
        if self._hover is None or self.drawing:
            return
        self.acquired = self._hover
        self.rays = self.MODEL.tracking_rays(self.source, self.acquired)
        self.update_helpers()

    def readout(self, result):
        """What the tab writes after the coordinates: what was locked to, and the angle along it."""
        fmt = self.MODEL.fmt_number
        if result["ray"] is not None:
            return f"{result['kind']}|{fmt(result['angle'])}|{fmt(result['distance'])}"
        if result["kind"] == "shift":
            return f"shift||{fmt(result['distance'])}"
        return result["kind"] or ""

    # --- a dimension under way --------------------------------------------------------

    def linear_entry(self, a, b, c=None):
        """The length dimension the clicks so far would make, or None where there is nothing to measure. `c` is the point its line is to run through; without one the line lies on the two ends, which is what the preview shows between the second click and the third. What is saved is not `c` but how far it lies from the middle of the two ends, measured at right angles to the line -- so the dimension follows the drawing when a point is moved."""
        model = self.MODEL
        entry = {
            "id": model.next_id(self.source, "dimensions"),
            "kind": self.TOOLS[self.tool]["kind"],
            "from": self.dimension_anchor(a),
            "to": self.dimension_anchor(b),
            "offset": 0.0,
        }
        ends = model.dimension_ends(self.source, entry)
        frame = model.dimension_direction(self.source, entry)
        if ends is None or frame is None or math.dist(ends[0], ends[1]) <= model.SAME_POINT:
            return None
        if c is not None:
            _u, n = frame
            middle = ((ends[0][0] + ends[1][0]) / 2.0, (ends[0][1] + ends[1][1]) / 2.0)
            entry["offset"] = self.ROUND((c[0] - middle[0]) * n[0] + (c[1] - middle[1]) * n[1])
        return entry
