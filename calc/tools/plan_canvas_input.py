"""PlanCanvas's mouse and keys, and what only the editor shows -- the helpers, the tracking lines and the handles -- a mixin of methods moved verbatim out of calc/tools/plan_canvas.py (issue #30). PlanCanvas names it among its bases.
"""

import math
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QObject, QPointF, QRect, QRectF, QSize, Qt, QTimer, Signal, qVersion
from PySide6.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPainterPath, QPen, QPixmap, QPixmapCache, QTransform
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsScene, QGraphicsSimpleTextItem, QGraphicsView, QLineEdit
import theme  # the desk around the sheet (theme.py, v0.90)
import plan_canvas_tools  # the circle a column is turned by, and the ruler (issue #9)
from domains import plan as model
from domains import plan_svg
from domains import plan_tracking as tracking
import plan_canvas_edit  # «Déplacer», «Copier» and «Ligne d'aide» (issue #18)
import plan_canvas_outline  # the building's outline: taken by its edge, reshaped by its corners (issue #54)
from plan_canvas_render import (  # split out of this module (issue #30): every name it had is still importable from it
    BackgroundFallback,
    DiskCache,
    MultiplyPixmapItem,
    PIXMAP_CACHE_KB,
    PageTile,
    PdfPages,
    Render,
    RenderCache,
    RenderJob,
    SvgLayer,
    _SVG_PAINT,
    _WHITE,
    _cosmetic,
    _probe_pdf,
    clip_bias,
    covers,
    ensure_pixmap_cache,
    file_key,
    same_scale,
    tile_geometry,
    tint_image,
    tint_svg,
)
from plan_canvas_view import (  # split out of this module (issue #30): every name it had is still importable from it
    BASE_RENDER_PX,
    CROP_MARGIN,
    DISK,
    DISK_CACHE_BYTES,
    DISK_CACHE_DIR,
    MEMORY_CACHE_BYTES,
    RENDERS,
    STOREY_COLOUR,
    STOREY_FILL,
    SUPERPOSE_RENDER_PX,
    TILE_MARGIN,
    TILE_MAX_PX,
    _round,
    PlanCanvasViewMixin,
)
from plan_canvas_editing import AXIS_TOOLS, LEVEL_TOOL, PICK_PX, POINT_TOOLS, READOUT_KINDS, SELECTION_LISTS, TEXT_TOOL, PlanCanvasEditMixin, readout_kind  # split out of this module (issue #30): every name it had is still importable from it


# How far the wheel zooms in: this many screen pixels per sheet unit at most.
MAX_ZOOM = 60


SELECT_COLOUR = theme.qcolor("plan-select")


CROP_COLOUR = theme.qcolor("plan-crop")


# What the readout under the plan names of a snap: the kinds the tab has a word for. A track's own kinds are said by the dotted line itself.


ALIGN_TOOL = "superpose-align"


STOREY_TOOLS = ("storey-line", "storey-box")


SECTION_TOOLS = STOREY_TOOLS + (LEVEL_TOOL,)


_box_corners = tracking.box_corners   # the geometry lies in domains/plan_tracking.py, which the snapping index reads too


def hit_storey_line(source, point, tolerance):
    """The index of the storey line within `tolerance` of `point`, the nearest, or None."""
    best = None
    for i, line in enumerate(source.get("storey_lines") or []):
        points = line.get("points") or []
        if len(points) != 2:
            continue
        d, _q = model._point_segment(point, points[0], points[1])
        if d <= tolerance and (best is None or d < best[0]):
            best = (d, i)
    return best[1] if best else None


def hit_load_level(source, point, tolerance):
    """The index of the load transfer level within `tolerance` of `point`, the nearest, or None (v0.116)."""
    best = None
    for i, level in enumerate(source.get("load_levels") or []):
        points = level.get("points") or []
        if len(points) != 2:
            continue
        d, _q = model._point_segment(point, points[0], points[1])
        if d <= tolerance and (best is None or d < best[0]):
            best = (d, i)
    return best[1] if best else None


def hit_storey_box(source, point, tolerance):
    """The index of the storey box under `point` -- on its outline, within `tolerance`, before inside it; of two, the last drawn --, or None."""
    inside = None
    for i, box in reversed(list(enumerate(source.get("storey_boxes") or []))):
        try:
            corners = _box_corners(box)
        except (KeyError, TypeError, ValueError):
            continue
        if any(model._point_segment(point, corners[j], corners[(j + 1) % 4])[0] <= tolerance for j in range(4)):
            return i
        (x0, y0), (x1, y1) = corners[0], corners[2]
        if inside is None and min(x0, x1) <= point[0] <= max(x0, x1) and min(y0, y1) <= point[1] <= max(y0, y1):
            inside = i
    return inside


class PlanCanvasInputMixin:
    """Methods of plan_canvas.PlanCanvas, moved verbatim (issue #30): the class names this mixin among its bases."""

    def scene_point(self, event):
        p = self.mapToScene(event.position().toPoint())
        return (p.x(), p.y())

    def start_pan(self, event):
        self.panning = event.position()
        self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)

    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == Qt.MouseButton.MiddleButton or (event.button() == Qt.MouseButton.LeftButton and (self.tool == "pan" or self.space_down)):
            self.start_pan(event)
            return
        if event.button() == Qt.MouseButton.RightButton:
            if self.typing:
                self.hide_distance()
            elif self.drawing:
                self.drawing = []
                self.cursor = None
                self.update_helpers()
            elif self.acquired:
                self.reset_tracking()   # as in the static models' tab: the next right click lets go of what was acquired
                self.update_helpers()
            else:
                self.select(None)
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        raw = self.scene_point(event)
        shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        self.hide_distance()
        if self.tool == "select" and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.press_toggle(raw)   # Ctrl+click: added to the selection or taken out of it, nothing dragged (issue #61)
            return
        self._left_click(raw, shift)

    def _left_click(self, raw, shift):
        """What a left click at `raw` does with the current tool -- a click of the mouse, or a point put down by a typed distance (`place`)."""
        kind = self.tool_kind()
        if kind in ("point", "line", "poly") and not self.drawing and self.tool in model.TYPES and model.labelled(self.tool) and not self.propose_label(self.tool):
            # nothing is put down that would carry no position: Positionen.xlsx has none of this type to give it
            self.refused.emit(self.tool)
            return

        if self.tool == "select":
            self.press_select(raw)
        elif self.tool == plan_canvas_tools.RULER:
            plan_canvas_tools.ruler_click(self, raw, shift)
        elif plan_canvas_tools.is_dimension_tool(self.tool):
            plan_canvas_tools.dimension_click(self, raw, shift)
        elif self.tool == "crop":
            self.drag = {"kind": "crop", "start": raw, "now": raw}
        elif self.tool == "calibrate":
            p, _kind = self.snapped(raw, self.drawing[-1] if self.drawing else None, shift)
            self.drawing.append(p)
            if len(self.drawing) == 2:
                points = [list(q) for q in self.drawing]
                self.drawing = []
                self.update_helpers()
                self.calibrated.emit(points)
                self.tool_done.emit()
                return
        elif self.tool == ALIGN_TOOL:
            self.align_click(raw)
            return
        elif self.tool == TEXT_TOOL:
            self.add_text(raw)   # a text placed with the Text tool (issue #43)
            return
        elif plan_canvas_edit.handles(self.tool):
            plan_canvas_edit.click(self, raw, shift)
            return
        elif self.tool in SECTION_TOOLS:
            if not self.storey_choice:
                self.storeyMissing.emit(self.tool)  # nothing is drawn that would name no storey: the tab says to choose one
                return
            p, _kind = self.storey_point(raw, shift)
            if not self.drawing:
                self.drawing = [p]
            else:
                a = self.drawing[0]
                self.drawing = []
                self.cursor = None
                tol = self.tolerance()
                if self.tool == "storey-line":
                    if math.dist(a, p) > tol:
                        self.add_storey_line(a, p)
                elif self.tool == LEVEL_TOOL:
                    if math.dist(a, p) > tol:
                        self.add_load_level(a, p)
                elif abs(p[0] - a[0]) > tol and abs(p[1] - a[1]) > tol:
                    self.add_storey_box(a, p)
        elif kind == "point":
            p, _kind = self.snapped(raw)
            self.add_element(self.tool, [p])
        elif kind == "axis":
            angle = AXIS_TOOLS[self.tool]
            p, _kind = self.snapped(raw, self.drawing[-1] if self.drawing else None, shift)
            if angle is not None:
                self.add_axis(p, angle)
            elif self.drawing:
                a = self.drawing[0]
                if math.dist(a, p) > self.tolerance():
                    angle = math.degrees(math.atan2(p[1] - a[1], p[0] - a[0]))
                    if angle <= -90:
                        angle += 180
                    elif angle > 90:
                        angle -= 180
                    self.drawing = []
                    self.add_axis(a, angle)
            else:
                self.drawing = [p]
        elif kind in ("line", "poly"):
            p, _kind = self.snapped(raw, self.drawing[-1] if self.drawing else None, shift)
            tol = self.tolerance()
            count = model.point_count(self.tool) if self.tool in model.TYPES else None   # the building's outline is no element type, and an area of any number of corners
            if self.drawing and math.dist(p, self.drawing[-1]) <= tol * 0.75:
                if count is None:
                    self.finish_drawing()  # a click on the last point ends it
                return  # a beam's second end is not its first: the click is let go, and the line waits for its other end
            if kind == "poly" and len(self.drawing) >= 3 and math.dist(p, self.drawing[0]) <= tol:
                self.finish_drawing()  # a click on the first point closes it
                return
            self.drawing.append(p)
            if len(self.drawing) == count:
                self.finish_drawing()  # a beam and a bracing member are one straight line: its second end ends it
                return
        self.update_helpers()

    def entry_at(self, raw):
        """What a click of the selection tool at `raw` would select, (kind, index) or None, and nothing else done: `press_select` asked with no object in focus -- so no handle is taken -- and its selection caught rather than made, its drag let go (ARCH-004)."""
        focus, extra, drag = self.selection, list(self.extra), self.drag
        caught = []
        self.__dict__["_focus"] = None
        self.select = lambda selection, add=False: caught.append(selection)
        try:
            self.press_select(raw)
        finally:
            del self.select
            self.__dict__["_focus"], self.__dict__["extra"], self.drag = focus, extra, drag
        return caught[-1] if caught else None

    def press_toggle(self, raw):
        """Ctrl+click with the selection tool (issue #61): the object under the pointer added to the selection, or taken out of it."""
        found = self.entry_at(raw)
        if found is not None:
            self.select(tuple(found), add=True)

    def press_select(self, raw):
        tol = self.tolerance()
        if self.clipped() and not self.shown_rect().adjusted(-tol, -tol, tol, tol).contains(QPointF(*raw)):
            self.select(None)  # nothing outside the crop is shown, and nothing there is taken
            return
        line = self.selected_storey_line()
        if line is not None:
            ends = [j for j, q in enumerate(line["points"]) if math.dist(raw, q) <= tol]
            if ends:
                self.drag = {"kind": "storey-line-end", "index": self.selection[1], "vertex": ends[0], "moved": False}
                return
        level = self.selected_load_level()
        if level is not None:
            ends = [j for j, q in enumerate(level["points"]) if math.dist(raw, q) <= tol]
            if ends:
                self.drag = {"kind": "load-level-end", "index": self.selection[1], "vertex": ends[0], "moved": False}
                return
        # a load level's words, drawn over the section, are taken by a click on them -- to move them clear (label_offset)
        for i, frame in reversed(self.load_level_frames()):
            if plan_svg.on_number(frame, raw, 0.5 * tol):
                self.select(("load-level", i))
                offset = self.source["load_levels"][i].get("label_offset") or [0, 0]
                self.drag = {"kind": "load-level-label", "index": i, "start": raw, "offset": (float(offset[0]), float(offset[1])), "moved": False}
                return
        box = self.selected_storey_box()
        if box is not None:
            corners = [j for j, q in enumerate(_box_corners(box)) if math.dist(raw, q) <= tol]
            if corners:
                self.drag = {"kind": "storey-box-corner", "index": self.selection[1], "opposite": _box_corners(box)[(corners[0] + 2) % 4], "moved": False}
                return
        element = self.selected_element()
        if element is not None and plan_canvas_tools.press_rotation(self, raw):
            return   # the circle a column is turned by, before its own handle (issue #9)
        if element is not None:
            vertex = model.nearest_vertex(element, raw, tol)
            if vertex is not None:
                self.drag = {"kind": "vertex", "index": self.selection[1], "vertex": vertex, "moved": False}
                return
        if plan_canvas_outline.press_vertex(self, raw, tol):
            return   # a corner of the building's outline, selected: dragged as a wall's corner is (issue #54)
        # a number is drawn over every symbol, so a click on it takes the number -- to move it clear of what it hides -- and selects its element
        text = plan_svg.hit_text(self.source, raw, tol, self.values)
        if text is not None:
            # a text is drawn over everything (issue #43): a click on it takes it, and a drag moves it
            self.select(("text", text))
            self.drag = {"kind": "text", "index": text, "start": raw, "points": [list(p) for p in self.source["texts"][text]["points"]], "moved": False}
            return
        label = self.label_under(raw)
        if label is not None:
            self.select(("element", label))
            offset = self.source["elements"][label].get("label_offset") or [0, 0]
            self.drag = {"kind": "label", "index": label, "start": raw, "offset": (float(offset[0]), float(offset[1])), "moved": False}
            return
        hit = model.hit_element(self.source, raw, tol)
        if hit is not None:
            self.select(("element", hit))
            self.drag = {"kind": "element", "index": hit, "start": raw, "points": [list(p) for p in self.source["elements"][hit]["points"]], "moved": False}
            return
        if plan_canvas_outline.press_edge(self, raw, tol):
            return   # the building's outline, after every element: a wall drawn along it is the wall, and its inside is never the outline (issue #54)
        level = hit_load_level(self.source, raw, tol)
        if level is not None:
            self.select(("load-level", level))
            self.drag = {"kind": "load-level", "index": level, "start": raw, "points": [list(q) for q in self.source["load_levels"][level]["points"]], "moved": False}
            return
        line = hit_storey_line(self.source, raw, tol)
        if line is not None:
            self.select(("storey-line", line))
            self.drag = {"kind": "storey-line", "index": line, "start": raw, "points": [list(q) for q in self.source["storey_lines"][line]["points"]], "moved": False}
            return
        crop = model.crop_of(self.frame_source())
        axis = model.hit_axis(self.source, raw, tol, crop)
        if axis is not None:
            self.select(("axis", axis))
            self.drag = {"kind": "axis", "index": axis, "start": raw, "point": list(self.source["axes"][axis]["point"]), "moved": False}
            return
        aid = model.hit_aid(self.source, raw, tol, crop)
        if aid is not None:
            self.select(("aid", aid))   # a construction aid: selected, deleted, moved (issue #18)
            self.drag = {"kind": "aid", "index": aid, "start": raw, "point": list(self.source["aids"][aid]["point"]), "moved": False}
            return
        box = hit_storey_box(self.source, raw, tol)
        if box is not None:
            self.select(("storey-box", box))
            entry = self.source["storey_boxes"][box]
            self.drag = {"kind": "storey-box", "index": box, "start": raw, "corner": (float(entry["x"]), float(entry["y"])), "moved": False}
            return
        if plan_canvas_tools.press_dimension(self, raw, tol):
            return   # a dimension's line: selected, and its line dragged (issue #9)
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
        drag = self.drag
        if drag is not None and event.buttons() & Qt.MouseButton.LeftButton:
            if drag["kind"] == "crop":
                drag["now"] = raw
                self.update_helpers()
                self.pointer.emit(raw[0], raw[1], "")
                return
            if drag["kind"] == "rotate":
                plan_canvas_tools.move_rotation(self, drag, raw, shift)
                return
            if drag["kind"] == "dimension":
                plan_canvas_tools.move_dimension(self, drag, raw)
                return
            if not drag["moved"]:
                if drag["kind"] not in ("vertex", "storey-line-end", "storey-box-corner", "load-level-end", plan_canvas_outline.DRAG_VERTEX) and math.dist(raw, drag["start"]) < self.tolerance() * 0.5:
                    return
                drag["moved"] = True
                self.begin_change()
            if plan_canvas_outline.follow(self, drag, raw, shift):
                pass   # the building's outline, whole or by one corner (issue #54)
            elif drag["kind"] == "vertex":
                element = self.source["elements"][drag["index"]]
                points = element["points"]
                j = drag["vertex"]
                anchor = points[j - 1] if j > 0 else (points[1] if len(points) > 1 else None)
                p, kind = self.snapped(raw, anchor, shift, exclude=drag["index"])
                points[j] = [_round(p[0]), _round(p[1])]
                self.show_snap(p, kind)
                self.note_hover(p, kind)
                self.pointer.emit(p[0], p[1], readout_kind(kind))
            elif drag["kind"] == "element":
                dx, dy = raw[0] - drag["start"][0], raw[1] - drag["start"][1]
                if shift:
                    moved = model.constrain(drag["start"], raw)
                    dx, dy = moved[0] - drag["start"][0], moved[1] - drag["start"][1]
                self.source["elements"][drag["index"]]["points"] = model.shifted(drag["points"], dx, dy)   # the translation «Déplacer» writes (issue #18)
                self.pointer.emit(raw[0], raw[1], "")
            elif drag["kind"] == "text":
                self.source["texts"][drag["index"]]["points"] = model.shifted(drag["points"], raw[0] - drag["start"][0], raw[1] - drag["start"][1])
                self.pointer.emit(raw[0], raw[1], "")
            elif drag["kind"] == "aid":
                self.source["aids"][drag["index"]]["point"] = model.shifted([drag["point"]], raw[0] - drag["start"][0], raw[1] - drag["start"][1])[0]
                self.pointer.emit(raw[0], raw[1], "")
            elif drag["kind"] == "label":
                dx, dy = raw[0] - drag["start"][0], raw[1] - drag["start"][1]
                if shift:
                    moved = model.constrain(drag["start"], raw)
                    dx, dy = moved[0] - drag["start"][0], moved[1] - drag["start"][1]
                ox, oy = drag["offset"][0] + dx, drag["offset"][1] + dy
                element = self.source["elements"][drag["index"]]
                if math.hypot(ox, oy) <= self.tolerance():
                    element.pop("label_offset", None)  # brought back to its own place, it goes back to following it
                else:
                    element["label_offset"] = [_round(ox), _round(oy)]
                self.pointer.emit(raw[0], raw[1], "")
            elif drag["kind"] == "axis":
                axis = self.source["axes"][drag["index"]]
                nx, ny = model.axis_normal(axis)
                d = (raw[0] - drag["start"][0]) * nx + (raw[1] - drag["start"][1]) * ny
                axis["point"] = [_round(drag["point"][0] + d * nx), _round(drag["point"][1] + d * ny)]
                self.pointer.emit(raw[0], raw[1], "")
            elif drag["kind"] == "storey-line":
                dx, dy = raw[0] - drag["start"][0], raw[1] - drag["start"][1]
                if shift:
                    moved = model.constrain(drag["start"], raw)
                    dx, dy = moved[0] - drag["start"][0], moved[1] - drag["start"][1]
                self.source["storey_lines"][drag["index"]]["points"] = model.shifted(drag["points"], dx, dy)
                self.pointer.emit(raw[0], raw[1], "")
            elif drag["kind"] == "storey-line-end":
                points = self.source["storey_lines"][drag["index"]]["points"]
                j = drag["vertex"]
                other = points[1 - j]
                excluded = ("storey-line", drag["index"])
                if shift:
                    p, kind = self.snapped((raw[0], other[1]), exclude_storey=excluded)
                    p = (p[0], other[1])
                else:
                    p, kind = self.snapped(raw, other, exclude_storey=excluded)
                points[j] = [_round(p[0]), _round(p[1])]
                self.show_snap(p, kind)
                self.note_hover(p, kind)
                self.pointer.emit(p[0], p[1], readout_kind(kind))
            elif drag["kind"] == "load-level":
                dx, dy = raw[0] - drag["start"][0], raw[1] - drag["start"][1]
                if shift:
                    moved = model.constrain(drag["start"], raw)
                    dx, dy = moved[0] - drag["start"][0], moved[1] - drag["start"][1]
                self.source["load_levels"][drag["index"]]["points"] = model.shifted(drag["points"], dx, dy)
                self.pointer.emit(raw[0], raw[1], "")
            elif drag["kind"] == "load-level-end":
                points = self.source["load_levels"][drag["index"]]["points"]
                j = drag["vertex"]
                other = points[1 - j]
                excluded = ("load-level", drag["index"])   # its own ends are no target of its own (load_level_points)
                if shift:
                    p, kind = self.snapped((raw[0], other[1]), exclude_storey=excluded)
                    p = (p[0], other[1])
                else:
                    p, kind = self.snapped(raw, other, exclude_storey=excluded)
                points[j] = [_round(p[0]), _round(p[1])]
                self.show_snap(p, kind)
                self.note_hover(p, kind)
                self.pointer.emit(p[0], p[1], readout_kind(kind))
            elif drag["kind"] == "load-level-label":
                dx, dy = raw[0] - drag["start"][0], raw[1] - drag["start"][1]
                ox, oy = drag["offset"][0] + dx, drag["offset"][1] + dy
                level = self.source["load_levels"][drag["index"]]
                if math.hypot(ox, oy) <= self.tolerance():
                    level.pop("label_offset", None)  # brought back to its own place
                else:
                    level["label_offset"] = [_round(ox), _round(oy)]
                self.pointer.emit(raw[0], raw[1], "")
            elif drag["kind"] == "storey-box":
                dx, dy = raw[0] - drag["start"][0], raw[1] - drag["start"][1]
                if shift:
                    moved = model.constrain(drag["start"], raw)
                    dx, dy = moved[0] - drag["start"][0], moved[1] - drag["start"][1]
                box = self.source["storey_boxes"][drag["index"]]
                box["x"], box["y"] = _round(drag["corner"][0] + dx), _round(drag["corner"][1] + dy)
                self.pointer.emit(raw[0], raw[1], "")
            elif drag["kind"] == "storey-box-corner":
                p, kind = self.snapped(raw, exclude_storey=("storey-box", drag["index"]))
                ox, oy = drag["opposite"]
                box = self.source["storey_boxes"][drag["index"]]
                x0, x1 = sorted((ox, p[0]))
                y0, y1 = sorted((oy, p[1]))
                box.update({"x": _round(x0), "y": _round(y0), "w": _round(x1 - x0), "h": _round(y1 - y0)})
                self.show_snap(p, kind)
                self.note_hover(p, kind)
                self.pointer.emit(p[0], p[1], readout_kind(kind))
            self._snap_index = None
            self._label_frames = None
            self.redraw_timer.start()
            return

        if self.typing:
            return   # a distance is being typed: the cursor stays where Tab found it
        if self.tool == plan_canvas_tools.RULER:
            plan_canvas_tools.ruler_move(self, raw, shift)
            return
        if plan_canvas_tools.is_dimension_tool(self.tool):
            plan_canvas_tools.dimension_move(self, raw, shift)
            return
        if self.tool == ALIGN_TOOL:
            p, snap = self.align_point(raw)
            self.cursor = p
            self.show_snap(p, snap)
            self.pointer.emit(p[0], p[1], readout_kind(snap))
            self.update_align()
            return
        if plan_canvas_edit.handles(self.tool):
            plan_canvas_edit.move(self, raw, shift)
            return
        kind = self.tool_kind()
        if self.tool in SECTION_TOOLS:
            p, snap = self.storey_point(raw, shift)
            self.cursor = p
            self.show_snap(p, snap)
            self.note_hover(p, snap)
            self.pointer.emit(p[0], p[1], readout_kind(snap))
            self.update_helpers()
        elif kind in ("line", "poly", "axis", "point") or self.tool == "calibrate":
            anchor = self.drawing[-1] if self.drawing else None
            p, snap = self.snapped(raw, anchor, shift)
            self.cursor = p
            self.show_snap(p, snap)
            self.note_hover(p, snap)
            self.pointer.emit(p[0], p[1], readout_kind(snap))
            self.update_helpers()
        else:
            self.show_snap(raw, None)
            self.pointer.emit(raw[0], raw[1], "")
            if self.tool == "select" and not self.space_down and drag is None:
                # over a number, the pointer says that it can be moved
                over = self.label_under(raw) is not None
                if over != self._over_label:
                    self._over_label = over
                    self.viewport().setCursor(Qt.CursorShape.SizeAllCursor if over else Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event):
        if self.panning is not None:
            self.panning = None
            self.restore_cursor()
            return
        drag, self.drag = self.drag, None
        if drag is None:
            return
        if drag["kind"] == "crop":
            (x0, y0), (x1, y1) = drag["start"], drag["now"]
            sheet = self.sheet_rect()
            x0, x1 = sorted((max(0.0, min(x0, sheet.width())), max(0.0, min(x1, sheet.width()))))
            y0, y1 = sorted((max(0.0, min(y0, sheet.height())), max(0.0, min(y1, sheet.height()))))
            if x1 - x0 > 0.01 * sheet.width() and y1 - y0 > 0.01 * sheet.height():
                self.begin_change()
                self.source["crop"] = {"x": _round(x0), "y": _round(y0), "w": _round(x1 - x0), "h": _round(y1 - y0)}
                self.end_change()
            self.update_helpers()
            self.tool_done.emit()
            return
        self.show_snap((0, 0), None)
        if drag.get("moved"):
            self.end_change()

    def mouseDoubleClickEvent(self, event):
        if plan_canvas_tools.finish_chain(self):
            return
        if self.tool_kind() in ("line", "poly") and self.drawing:
            self.finish_drawing()
            return
        super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event):
        steps = event.angleDelta().y() / 120.0
        if steps == 0:
            return
        factor = 1.15 ** steps
        scale = self.transform().m11() * factor
        rect = self.shown_rect()
        fit = min(self.viewport().width() / max(rect.width(), 1e-9), self.viewport().height() / max(rect.height(), 1e-9))
        if (factor < 1 and scale < fit * 0.2) or (factor > 1 and scale > MAX_ZOOM):
            return
        self.zoom_at(event.position(), factor)

    def zoom_at(self, position, factor):
        """Scales the view by `factor` about `position`, a point of the viewport: the point of the plan under it stays under it."""
        at = position.toPoint()
        anchor = self.mapToScene(at)
        self.scale(factor, factor)
        drift = self.mapFromScene(anchor) - at
        self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + drift.x())
        self.verticalScrollBar().setValue(self.verticalScrollBar().value() + drift.y())
        self.view_moved()
        self.update_track()   # the dotted lines are drawn as far as the view reaches
        self.update_helpers()   # a column's circle stands at a distance on the screen, whatever the zoom

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Space and not event.isAutoRepeat():
            self.space_down = True
            self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
            return
        if key == Qt.Key.Key_Tab and self.locked and not self.typing:
            self.show_distance()
            return
        if key == Qt.Key.Key_Escape:
            if self.ruler:
                plan_canvas_tools.clear_ruler(self)   # the ruler's measure taken away; the tool stays
            elif self.dim_points:
                plan_canvas_tools.clear_dimension_draft(self)   # the dimension being drawn given up; the tool stays
            elif self.typing:
                self.hide_distance()
                self.update_helpers()
            elif self.drawing:
                self.drawing = []
                self.cursor = None
                self.update_helpers()
            elif self.acquired:
                self.reset_tracking()   # as in the static models' tab: Escape lets go of what was acquired before it leaves the tool
                self.update_helpers()
            elif self.tool != "select":
                self.tool_done.emit()
            else:
                self.select(None)
            return
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if plan_canvas_tools.finish_chain(self):
                return
            self.finish_drawing()
            return
        if key == Qt.Key.Key_Backspace and self.drawing:
            self.drawing.pop()
            self.update_helpers()
            return
        if key == Qt.Key.Key_Delete and self.selection is not None and not self.drawing:
            self.delete_selection()
            return
        super().keyPressEvent(event)

    def focusNextPrevChild(self, forward):
        """Tab is the tracking's, not the focus chain's, while the cursor is locked to a ray: without this it would leave the canvas the moment a direction is locked."""
        if self.locked and not self.typing:
            return False
        return super().focusNextPrevChild(forward)

    def leaveEvent(self, event):
        self.cursor = None
        self.locked = []
        self._hover = None
        self.acquire_timer.stop()
        self.update_helpers()
        super().leaveEvent(event)

    def update_helpers(self):
        scene = self.scene()
        for handle in self.handles:
            scene.removeItem(handle)
        self.handles = []
        path = QPainterPath()
        element = self.selected_element()
        axis = self.selected_axis()
        if element is not None and element.get("points"):
            points = [QPointF(x, y) for x, y in element["points"]]
            kind = model.element_kind(element)
            if kind == "point":
                r = 18 * plan_svg.base_unit(model.crop_of(self.frame_source()))
                path.addEllipse(points[0], r, r)
            else:
                path.moveTo(points[0])
                for q in points[1:]:
                    path.lineTo(q)
                if kind == "poly":
                    path.closeSubpath()
            # its number's box, which can be dragged clear of what it hides
            frame = plan_svg.number_frame(element, plan_svg.sizes_of(self.source))
            if frame is not None:
                corners = [QPointF(*c) for c in plan_svg.number_corners(frame, 2.5 / max(self.transform().m11(), 1e-9))]
                path.moveTo(corners[0])
                for c in corners[1:]:
                    path.lineTo(c)
                path.closeSubpath()
            for q in points:
                self._add_handle(q)
            plan_canvas_tools.add_rotation_handle(self, element)
        elif self.selection and self.selection[0] == "dimension":
            plan_canvas_tools.add_dimension_highlight(self)
        elif plan_canvas_outline.highlight(self, path):
            pass   # the building's outline selected: its corners joined, a handle on each (issue #54)
        elif axis is not None or (self.selection and self.selection[0] == "aid" and self.has_selection()):
            line = axis if axis is not None else self.source["aids"][self.selection[1]]
            segment = model.axis_segment(line, model.crop_of(self.frame_source()))
            if segment:
                path.moveTo(QPointF(*segment[0]))
                path.lineTo(QPointF(*segment[1]))
        else:
            line, box = self.selected_storey_line(), self.selected_storey_box()
            level = self.selected_load_level()
            if level is not None and len(level.get("points") or []) == 2:
                ends = [QPointF(*q) for q in level["points"]]
                path.moveTo(ends[0])
                path.lineTo(ends[1])
                frame = dict(self.load_level_frames()).get(self.selection[1])
                if frame is not None:
                    corners = [QPointF(*c) for c in plan_svg.number_corners(frame, 2.5 / max(self.transform().m11(), 1e-9))]
                    path.moveTo(corners[0])
                    for c in corners[1:]:
                        path.lineTo(c)
                    path.closeSubpath()
                for q in ends:
                    self._add_handle(q)
            elif line is not None and len(line.get("points") or []) == 2:
                ends = [QPointF(*q) for q in line["points"]]
                path.moveTo(ends[0])
                path.lineTo(ends[1])
                for q in ends:
                    self._add_handle(q)
            elif box is not None:
                corners = [QPointF(*q) for q in _box_corners(box)]
                path.moveTo(corners[0])
                for q in corners[1:]:
                    path.lineTo(q)
                path.closeSubpath()
                for q in corners:
                    self._add_handle(q)
        for kind, index in self.selected_entries()[:-1]:
            path.addPath(self.entry_outline(kind, self.source[SELECTION_LISTS[kind]][index]))   # the others selected beside the one in focus, without handles (issue #61)
        self.select_item.setPath(path)

        preview = QPainterPath()
        colour = QColor(plan_svg.COLOURS.get(self.tool, plan_svg.AXIS_COLOUR))
        if self.drag is not None and self.drag["kind"] == "crop":
            (x0, y0), (x1, y1) = self.drag["start"], self.drag["now"]
            preview.addRect(QRectF(QPointF(x0, y0), QPointF(x1, y1)).normalized())
            colour = CROP_COLOUR
        elif self.tool in SECTION_TOOLS:
            colour = STOREY_COLOUR
            if self.drawing and self.cursor is not None:
                a, b = QPointF(*self.drawing[0]), QPointF(*self.cursor)
                if self.tool in ("storey-line", LEVEL_TOOL):
                    preview.moveTo(a)
                    preview.lineTo(b)
                else:
                    preview.addRect(QRectF(a, b).normalized())
        elif plan_canvas_edit.handles(self.tool):
            preview, colour = plan_canvas_edit.preview(self)
        elif self.drawing or (self.cursor is not None and self.tool_kind() == "axis"):
            points = list(self.drawing) + ([self.cursor] if self.cursor is not None else [])
            if self.tool_kind() == "axis" and points:
                # an axis is a whole line: show it across the frame as it will be drawn
                crop = model.crop_of(self.frame_source())
                if AXIS_TOOLS[self.tool] is not None:
                    angle = AXIS_TOOLS[self.tool]
                    a = points[-1]
                elif len(points) >= 2:
                    a, b = points[0], points[-1]
                    angle = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) if math.dist(a, b) > 1e-9 else None
                else:
                    a, angle = points[0], None
                segment = model.axis_segment({"point": list(a), "angle": angle}, crop) if angle is not None else None
                if segment:
                    preview.moveTo(QPointF(*segment[0]))
                    preview.lineTo(QPointF(*segment[1]))
                colour = QColor(plan_svg.AXIS_COLOUR)
            elif points:
                preview.moveTo(QPointF(*points[0]))
                for q in points[1:]:
                    preview.lineTo(QPointF(*q))
                if self.tool_kind() == "poly" and len(points) > 2:
                    preview.lineTo(QPointF(*points[0]))
                for q in self.drawing:
                    preview.addEllipse(QPointF(*q), 2.5 / max(self.transform().m11(), 1e-9), 2.5 / max(self.transform().m11(), 1e-9))
        self.preview.setPen(_cosmetic(colour, 2, [4, 3]))
        self.preview.setPath(preview)
        self.update_track()

    def update_track(self):
        """The dotted lines the cursor is locked to, across the view, and a small cross on every acquired point (the one being acquired, a ring) -- what only the editor shows, never printed."""
        path = QPainterPath()
        unit = 1.0 / max(self.transform().m11(), 1e-9)
        rect = self.mapToScene(self.viewport().rect()).boundingRect()
        reach = 2.0 * max(rect.width(), rect.height(), 1.0)
        for ray in self.locked:
            a, u = ray["anchor"], ray["unit"]
            path.moveTo(QPointF(a[0] - u[0] * reach, a[1] - u[1] * reach))
            path.lineTo(QPointF(a[0] + u[0] * reach, a[1] + u[1] * reach))
        for q in self.acquired:
            s = 5.0 * unit
            path.moveTo(QPointF(q[0] - s, q[1]))
            path.lineTo(QPointF(q[0] + s, q[1]))
            path.moveTo(QPointF(q[0], q[1] - s))
            path.lineTo(QPointF(q[0], q[1] + s))
        if self._hover is not None:
            path.addEllipse(QPointF(*self._hover), 7.0 * unit, 7.0 * unit)
        self.track_item.setPath(path)

    def _add_handle(self, point):
        """A square handle at `point`, of a fixed size on the screen: a corner to drag."""
        handle = QGraphicsRectItem(-4, -4, 8, 8)
        handle.setPos(point)
        handle.setBrush(QBrush(theme.qcolor("paper")))
        handle.setPen(_cosmetic(SELECT_COLOUR, 1.6))
        handle.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        handle.setZValue(21)
        self.scene().addItem(handle)
        self.handles.append(handle)
