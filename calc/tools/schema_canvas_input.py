"""SchemaCanvas's mouse and keys, and what only the editor shows over the drawing -- the snap mark, a dimension's preview and readout, the helpers, the outline and the handles -- a mixin of methods moved verbatim out of calc/tools/schema_canvas.py (issue #30). SchemaCanvas names it among its bases.
"""

import math
from PySide6.QtCore import QByteArray, QLineF, QPoint, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QLineEdit,
)
import theme  # the ground of a distance that cannot be read (theme.py, v0.90)
from domains import schema as model
from domains import schema_svg as drawing_svg
from schema_canvas_place import ANGLE_STEP, CONNECTOR_TOOLS, TOOLS, _round, SchemaCanvasPlaceMixin  # split out of this module (issue #30): every name it had is still importable from it


# How far the view may be zoomed, in screen pixels to the millimetre. Absolute, so a 60 mm plate and a 3 m beam are held to the same range and the wheel never stops working where the engineer did not expect it to.
MIN_ZOOM = 0.002


MAX_ZOOM = 50.0


SELECT_COLOUR = theme.colour("drawing-select")


def _cosmetic(colour, width, dash=None):
    pen = QPen(QColor(colour), width)
    pen.setCosmetic(True)
    if dash:
        pen.setDashPattern(dash)
    return pen


class SchemaCanvasInputMixin:
    """Methods of schema_canvas.SchemaCanvas, moved verbatim (issue #30): the class names this mixin among its bases."""

    def start_pan(self, event):
        self.panning = event.position()
        self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)

    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == Qt.MouseButton.MiddleButton or (
            event.button() == Qt.MouseButton.LeftButton and (self.tool == "pan" or self.space_down)
        ):
            self.start_pan(event)
            return
        if event.button() == Qt.MouseButton.RightButton:
            if self.turning is not None:
                self.finish_turning()
            elif self.drawing or self.dim_elements:
                self.drawing = []
                self.dim_elements = []
                self.dim_hover = None
                self.cursor = None
            elif self.acquired is not None:
                self.acquired = None
                self.ray = None
            else:
                self.select(None)
            self.hide_distance()
            self.update_helpers()
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        raw = self.scene_point(event)
        shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        if self.turning is not None:
            self.finish_turning()
            return
        if self.tool == "select":
            self.press_select(raw, add=bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier))
            self.update_helpers()
            return
        if TOOLS[self.tool].get("drag") == "crop":
            start, _kind = model.snap(self.source, raw, self.tolerance(), self.snap_step(), geometry=self.snap_geometry())
            self.drag = {"kind": "crop", "start": start, "now": start, "moved": False}
            self.update_helpers()
            return
        geo = TOOLS[self.tool].get("geo")
        if geo == "dimension" and TOOLS[self.tool]["on"] == "element" and len(self.dim_elements) < 2:
            eid = model.hit_element(self.source, raw, self.tolerance() * 2)
            if eid is None:
                self.refused.emit("element")
                return
            if eid in self.dim_elements:
                self.refused.emit("dimension-same-element")
                return
            self.dim_elements.append(eid)
            self.update_helpers()
            return
        self.hide_distance()
        self.place(self.track(raw, shift)["point"])

    def press_select(self, raw, add=False):
        tol = self.tolerance()
        if add:
            # Ctrl: the thing under the pointer joins the selection or leaves it, and nothing is dragged --
            # a drag started on a Ctrl+click would move one entry out of a set the engineer was still building.
            for hit, owner in ((model.hit_connector(self.source, raw, tol), "connectors"),
                               (model.hit_aid_point(self.source, raw, tol), "aids"),
                               (model.hit_element(self.source, raw, tol), "elements"),
                               # a construction line last: it runs across the whole detail (v0.75, what «Trancher» needs selected)
                               (model.hit_aid_line(self.source, raw, tol), "aids")):
                if hit is not None:
                    self.select((owner, hit), add=True)
                    return
            return
        collection, entry = self.selected()
        if entry is not None and collection == "connectors":
            if math.dist(raw, (entry["x"], entry["z"])) <= tol:
                self.drag = {"kind": "connector", "id": entry["id"], "moved": False}
                return
        frames = self.label_frames()
        owner = drawing_svg.hit_label(self.source, raw, tol, frames)
        if owner is not None:
            self.select(owner)
            offset = (model.entry_of(self.source, *owner) or {}).get("label_offset") or [0, 0]
            self.drag = {"kind": "label", "owner": owner, "start": raw,
                         "offset": (float(offset[0]), float(offset[1])), "moved": False}
            return
        cid = model.hit_connector(self.source, raw, tol)
        if cid is not None:
            self.select(("connectors", cid))
            self.drag = {"kind": "connector", "id": cid, "moved": False}
            return
        aid = model.hit_aid_point(self.source, raw, tol)
        if aid is not None:
            self.select(("aids", aid))
            self.drag = {"kind": "aid", "id": aid, "moved": False}
            return
        eid = model.hit_element(self.source, raw, tol)
        if eid is not None:
            self.select(("elements", eid))
            return
        line = model.hit_aid_line(self.source, raw, tol)
        if line is not None:
            self.select(("aids", line))
            return
        self.select(None)

    def mouseMoveEvent(self, event):
        if self.panning is not None:
            delta = event.position() - self.panning
            self.panning = event.position()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - round(delta.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - round(delta.y()))
            return
        raw = self.scene_point(event)
        shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        self.pointer.emit(raw[0], raw[1], "")
        if self.turning is not None:
            self.turn(raw)
            return
        drag = self.drag
        if drag is not None and drag["kind"] == "crop" and event.buttons() & Qt.MouseButton.LeftButton:
            now, kind = model.snap(self.source, raw, self.tolerance(), self.snap_step(), geometry=self.snap_geometry())
            drag["now"], drag["moved"] = now, True
            self.show_snap(now, kind)
            self.pointer.emit(now[0], now[1], kind or "")
            self.update_helpers()
            return
        if drag is not None and event.buttons() & Qt.MouseButton.LeftButton:
            if not drag["moved"]:
                drag["moved"] = True
                self.begin_change()
            if drag["kind"] in ("connector", "aid"):
                collection = "connectors" if drag["kind"] == "connector" else "aids"
                entry = model.entry_of(self.source, collection, drag["id"])
                p, kind = model.snap(self.source, raw, self.tolerance(), self.snap_step(), positions=self.positions)
                entry["x"], entry["z"] = _round(p[0]), _round(p[1])
                self.show_snap(p, kind)
                self.pointer.emit(p[0], p[1], kind or "")
            else:
                entry = model.entry_of(self.source, *drag["owner"])
                dx, dz = raw[0] - drag["start"][0], raw[1] - drag["start"][1]
                if shift:
                    moved = model.constrain(drag["start"], raw)
                    dx, dz = moved[0] - drag["start"][0], moved[1] - drag["start"][1]
                ox, oz = drag["offset"][0] + dx, drag["offset"][1] + dz
                if math.hypot(ox, oz) <= self.tolerance():
                    entry.pop("label_offset", None)
                else:
                    entry["label_offset"] = [_round(ox), _round(oz)]
            self._drawing_cache = None
            self.redraw_timer.start()
            return

        if self.typing:
            return
        if TOOLS[self.tool].get("geo") is not None:
            result = self.track(raw, shift)
            self.cursor = result["point"]
            self.ray = result["ray"]
            self.show_snap(result["point"], result["kind"])
            want_element = (TOOLS[self.tool].get("geo") == "dimension"
                            and TOOLS[self.tool].get("on") == "element" and len(self.dim_elements) < 2)
            self.dim_hover = model.hit_element(self.source, raw, self.tolerance() * 2) if want_element else None
            measured = self.dimension_readout()
            self.pointer.emit(result["point"][0], result["point"][1], measured or self.readout(result))
            hover = model.hit_aid_point(self.source, raw, self.tolerance())
            at = None if hover is None else model.named_point(self.source, hover)
            if at is None:
                cid = model.hit_connector(self.source, raw, self.tolerance())
                marker = model.entry_of(self.source, "connectors", cid) if cid else None
                at = (float(marker["x"]), float(marker["z"])) if marker else None
            if at != self._hover:
                self._hover = at
                self.acquire_timer.stop()
                if at is not None and not self.drawing:
                    self.acquire_timer.start()
            self.update_helpers()
            return
        self.show_snap(raw, None)
        if self.tool == "select" and drag is None and not self.space_down:
            over = drawing_svg.hit_label(self.source, raw, self.tolerance(), self.label_frames()) is not None
            if over != self._over_label:
                self._over_label = over
                self.viewport().setCursor(Qt.CursorShape.SizeAllCursor if over else Qt.CursorShape.ArrowCursor)

    def readout(self, result):
        if result["ray"] is not None:
            return f"{result['kind']}|{model.fmt_number(result['angle'])}|{model.fmt_number(result['distance'])}"
        if result["kind"] == "shift":
            return f"shift||{model.fmt_number(result['distance'])}"
        return result["kind"] or ""

    def mouseReleaseEvent(self, event):
        if self.panning is not None:
            self.panning = None
            self.restore_cursor()
            return
        drag, self.drag = self.drag, None
        self.show_snap((0, 0), None)
        if drag is not None and drag["kind"] == "crop":
            (x0, z0), (x1, z1) = drag["start"], drag["now"]
            if self.set_crop((x0, z0, x1 - x0, z1 - z0)):
                self.tool_done.emit()
            self.update_helpers()
            return
        if drag is not None and drag.get("moved"):
            self.end_change()

    def wheelEvent(self, event):
        """The wheel always zooms, about the pointer, between two absolute limits -- nowheel.py leaves this canvas alone for exactly this reason (docs/ui/window.md §10quater)."""
        steps = event.angleDelta().y() / 120.0
        if steps == 0:
            return
        self.zoom_at(event.position(), 1.15 ** steps)

    def zoom_at(self, position, factor):
        scale = self.scale_px()
        factor = max(MIN_ZOOM / scale, min(factor, MAX_ZOOM / scale))
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

    def focusNextPrevChild(self, _next):
        """Tab is the tracking's, not the focus chain's -- statics_canvas's own rule."""
        return False

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Space and not event.isAutoRepeat():
            self.space_down = True
            self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
            return
        if key == Qt.Key.Key_Tab and (self.ray is not None or self.rotation_waiting()) and not self.typing:
            self.show_distance()
            return
        if key == Qt.Key.Key_Escape:
            if self.typing:
                self.hide_distance()
            elif self.turning is not None:
                self.finish_turning()
            elif self.drawing or self.dim_elements:
                self.drawing = []
                self.dim_elements = []
                self.dim_hover = None
                self.cursor = None
            elif self.acquired is not None:
                self.acquired = None
                self.ray = None
            elif self.tool != "select":
                self.tool_done.emit()
            else:
                self.select(None)
            self.update_helpers()
            return
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not self.typing:
            if self.turning is not None:
                self.finish_turning()
            elif self.cursor is not None:
                self.place(self.cursor)
            return
        if key == Qt.Key.Key_Backspace and (self.drawing or self.dim_elements):
            (self.drawing or self.dim_elements).pop()
            self.update_helpers()
            return
        if key == Qt.Key.Key_Delete and self.selection_ids() and not self.drawing:
            self.delete_selection()
            return
        super().keyPressEvent(event)

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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_helpers()

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

    def dimension_preview(self):
        """What the dimension being drawn would look like, built from the same geometry the figure is drawn from -- statics_canvas's own preview, so what the pointer promises is what the last click delivers."""
        if TOOLS[self.tool].get("geo") != "dimension" or self.cursor is None:
            return None
        path = QPainterPath()
        if TOOLS[self.tool]["kind"] == "angle":
            if len(self.dim_elements) != 2:
                return None
            entry = self.angle_entry(self.cursor)
            if entry is None:
                return None
            turn = model.dimension_angle(self.source, entry)
            if turn is None:
                return None
            centre, sweep, start = turn
            radius = abs(float(entry["offset"]))
            steps = max(8, int(abs(sweep) / 4.0) + 1)
            for i in range(steps + 1):
                a = math.radians(start + sweep * i / steps)
                q = self.qp((centre[0] + radius * math.cos(a), centre[1] + radius * math.sin(a)))
                path.moveTo(q) if i == 0 else path.lineTo(q)
            for end in (start, start + sweep):
                a = math.radians(end)
                path.moveTo(self.qp(centre))
                path.lineTo(self.qp((centre[0] + radius * math.cos(a), centre[1] + radius * math.sin(a))))
            return path
        if not self.drawing:
            return None
        a = self.drawing[0]
        b = self.drawing[1] if len(self.drawing) > 1 else self.cursor
        entry = self.linear_entry(a, b, self.cursor if len(self.drawing) > 1 else None)
        if entry is None:
            return None
        ends = model.dimension_ends(self.source, entry)
        line = model.dimension_line(self.source, entry)
        if ends is None or line is None:
            return None
        path.moveTo(self.qp(line[0]))
        path.lineTo(self.qp(line[1]))
        for end, foot in zip(ends, line):
            if math.dist(end, foot) > model.SAME_POINT:
                path.moveTo(self.qp(end))
                path.lineTo(self.qp(foot))
        return path

    def dimension_readout(self):
        """What the dimension being drawn measures so far -- «140 mm» as the far end is moved, «90°» as the sector is chosen."""
        if TOOLS[self.tool].get("geo") != "dimension" or self.cursor is None:
            return ""
        entry = None
        if TOOLS[self.tool]["kind"] == "angle":
            if len(self.dim_elements) == 2:
                entry = self.angle_entry(self.cursor)
        elif self.drawing:
            b = self.drawing[1] if len(self.drawing) > 1 else self.cursor
            entry = self.linear_entry(self.drawing[0], b, self.cursor if len(self.drawing) > 1 else None)
        if entry is None:
            return ""
        value, unit = model.dimension_value(self.source, entry)
        return "" if value is None else f"{model.fmt_number(value)} {unit}".strip()

    def update_helpers(self):
        scene = self.scene()
        for handle in self.handles:
            scene.removeItem(handle)
        self.handles = []

        path = QPainterPath()
        chosen = self.selection_ids()
        frames = self.label_frames() if (chosen or self.hover) else []
        for collection, entry in self.selected_entries():
            # Handles are the focused entry's alone: they are what a drag grabs, and a set of them on
            # every entry of a six-entry selection would be a field of dots with no one meaning.
            handles = (collection, entry["id"]) == self.selection
            self.outline(path, collection, entry, handles)
        if chosen:
            for owner, frame in frames:
                if owner in chosen:
                    self.outline_label(path, frame)
        self.select_item.setPath(path)

        # the row of the lists the pointer is over (v0.75), in a colour of its own: hovering selects nothing
        hovered = QPainterPath()
        if self.hover is not None:
            entry = model.entry_of(self.source, *self.hover)
            if entry is not None:
                self.outline(hovered, self.hover[0], entry, False)
                for owner, frame in frames:
                    if owner == self.hover:
                        self.outline_label(hovered, frame)
        self.hover_item.setPath(hovered)

        # «Cadrage»: the crop drawn, or being dragged out, and a veil over what the report will not show
        crop_rect = None
        if self.drag is not None and self.drag.get("kind") == "crop":
            (x0, z0), (x1, z1) = self.drag["start"], self.drag["now"]
            crop_rect = QRectF(QPointF(min(x0, x1), min(z0, z1)), QPointF(max(x0, x1), max(z0, z1)))
        elif isinstance(self.source.get("crop"), dict):
            c = self.source["crop"]
            crop_rect = QRectF(float(c["x"]), float(c["z"]), float(c["w"]), float(c["h"]))
        veil = QPainterPath()
        if crop_rect is not None:
            self.crop_item.setRect(crop_rect)
            self.crop_item.show()
            veil.addRect(self.sceneRect())
            inner = QPainterPath()
            inner.addRect(crop_rect)
            veil = veil.subtracted(inner)
        else:
            self.crop_item.hide()
        self.crop_veil.setPath(veil)

        preview = QPainterPath()
        marked = list(self.dim_elements)
        if self.dim_hover is not None and self.dim_hover not in marked:
            marked.append(self.dim_hover)
        for eid in marked:
            element = model.entry_of(self.source, "elements", eid)
            points = [tuple(q) for q in (element or {}).get("points", [])]
            if len(points) >= 2:
                preview.moveTo(self.qp(points[0]))
                for q in points[1:]:
                    preview.lineTo(self.qp(q))
        dim = self.dimension_preview()
        if dim is not None:
            preview.addPath(dim)
        elif TOOLS[self.tool].get("geo") == "area":
            corners = self.area_points(self.drawing, self.cursor)
            if corners is not None:
                preview.moveTo(self.qp(corners[0]))
                for q in corners[1:]:
                    preview.lineTo(self.qp(q))
                preview.closeSubpath()
        elif TOOLS[self.tool].get("geo") is not None:
            points = list(self.drawing) + ([self.cursor] if self.cursor is not None else [])
            if len(points) >= 2:
                preview.moveTo(self.qp(points[0]))
                for q in points[1:]:
                    preview.lineTo(self.qp(q))
            elif points and TOOLS[self.tool].get("geo") in ("connector", "aid-point", "aid-fixed", "aid-turn"):
                r = 5.0 / self.scale_px()
                preview.addEllipse(self.qp(points[0]), r, r)
        self.preview.setPen(_cosmetic(SELECT_COLOUR, 2, [5, 4]))
        self.preview.setPath(preview)

        track = QPainterPath()
        anchor = self.anchor()
        if anchor is not None and self.ray is not None:
            rect = self.mapToScene(self.viewport().rect()).boundingRect()
            reach = 2 * max(rect.width(), rect.height())
            u = self.ray["unit"]
            track.moveTo(self.qp((anchor[0] - u[0] * reach, anchor[1] - u[1] * reach)))
            track.lineTo(self.qp((anchor[0] + u[0] * reach, anchor[1] + u[1] * reach)))
        if anchor is not None:
            r = 7.0 / self.scale_px()
            track.addEllipse(self.qp(anchor), r, r)
        self.track_item.setPath(track)

    def outline(self, path, collection, entry, handles=False):
        """One entry's outline, added to `path` -- what the selection draws, and a hovered row (v0.75); `handles` puts the grab squares on it too."""
        if collection == "connectors":
            p = self.qp((entry["x"], entry["z"]))
            r = 9.0 / self.scale_px()
            path.addEllipse(p, r, r)
            if handles:
                self.add_handle(p)
        elif collection == "aids":
            at = model.aid_point(entry)
            if at is not None:
                p = self.qp(at)
                r = 9.0 / self.scale_px()
                path.addEllipse(p, r, r)
                if handles:
                    self.add_handle(p)
            else:
                line = model.aid_line(entry)
                if line is not None:
                    (ax, az), (ux, uz) = line
                    reach = max(self.sceneRect().width(), self.sceneRect().height())
                    path.moveTo(QPointF(ax - ux * reach, az - uz * reach))
                    path.lineTo(QPointF(ax + ux * reach, az + uz * reach))
        elif collection == "elements":
            points = [tuple(q) for q in entry.get("points", [])]
            if len(points) >= 2:
                path.moveTo(self.qp(points[0]))
                for q in points[1:]:
                    path.lineTo(self.qp(q))
                if model.element_kind(entry) == "area":
                    path.closeSubpath()
                if handles:
                    for q in points:
                        self.add_handle(self.qp(q))
        elif collection == "dimensions":
            ends = model.dimension_ends(self.source, entry)
            line = model.dimension_line(self.source, entry) if entry.get("kind") != "angle" else None
            if line is not None:
                path.moveTo(self.qp(line[0]))
                path.lineTo(self.qp(line[1]))
            elif ends is not None:
                path.moveTo(self.qp(ends[0]))
                path.lineTo(self.qp(ends[1]))

    @staticmethod
    def outline_label(path, frame):
        corners = [QPointF(c[0], c[1]) for c in drawing_svg.label_corners(frame)]
        path.moveTo(corners[0])
        for c in corners[1:]:
            path.lineTo(c)
        path.closeSubpath()

    def add_handle(self, at):
        handle = QGraphicsRectItem(-4, -4, 8, 8)
        handle.setPos(at)
        handle.setBrush(QBrush(theme.qcolor("paper")))
        handle.setPen(_cosmetic(SELECT_COLOUR, 1.6))
        handle.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        handle.setZValue(21)
        self.scene().addItem(handle)
        self.handles.append(handle)
