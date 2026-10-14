"""What the plan canvases do besides drawing elements: the circle a selected column is turned by, and the ruler (issue #9, spec docs/requirements/completed/2026-10-08-plan-positions-cotes-numerotation-sections.md, REQ-002, REQ-009, D-005, D-012, D-015).

Kept apart from plan_canvas.py, which is long enough, and called from it at four places -- a click, a move, a release, the helpers drawn over the selection. Nothing here is a source's: the ruler is a measure that is shown and kept nowhere (D-005: not in the plan, not in «Annuler», not in the export), and the turn writes the element's `angle` through `plan.set_element_angle`, the one rule the angle field and the source's check read, in one step of «Annuler».

The engineer, 08.10.2026: «Permettre de tourner les poteaux avec le cercle qui apparaît à la sélection, et non plus seulement par l'angle saisi en texte» -- and «Ajouter un outil règle».
"""

import math

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem, QGraphicsPathItem, QGraphicsSimpleTextItem

import theme  # the ink of a dimension and the paper of its handles (theme.py, issue #29)
from domains import dimension
from domains import plan as model
from domains import plan_svg

# The rotation circle stands this far beyond the selection ring, on the screen, whatever the zoom; it is picked within PICK px.
ROTATE_PX = 26
PICK = 8
RULER = "ruler"
INK = theme.colour("plan-dimension")


def _zoom(canvas):
    return max(canvas.transform().m11(), 1e-9)


def _pen(colour, width):
    pen = QPen(QColor(colour))
    pen.setWidthF(width)
    pen.setCosmetic(True)
    return pen


# --- turning a column ---------------------------------------------------------------------

def rotation_point(canvas, element):
    """Where the circle of a turnable element stands -- above it at 0°, turned with it --, or None for an element that does not turn."""
    if element is None or not model.is_rotatable(element) or not element.get("points"):
        return None
    cx, cy = element["points"][0]
    ring = 18 * plan_svg.base_unit(model.crop_of(canvas.frame_source()))
    r = ring + ROTATE_PX / _zoom(canvas)
    a = math.radians(float(element.get("angle", 0) or 0))
    return (cx + r * math.sin(a), cy - r * math.cos(a))


def add_rotation_handle(canvas, element):
    """The circle drawn over a selected column, with the thin line that ties it to the column's centre -- of a fixed size on the screen."""
    at = rotation_point(canvas, element)
    if at is None:
        return
    path = QPainterPath(QPointF(*element["points"][0]))
    path.lineTo(QPointF(*at))
    tie = QGraphicsPathItem(path)
    tie.setPen(_pen(INK, 1.0))
    tie.setZValue(20)
    canvas.scene().addItem(tie)
    canvas.handles.append(tie)
    circle = QGraphicsEllipseItem(-5, -5, 10, 10)
    circle.setPos(QPointF(*at))
    circle.setBrush(QBrush(theme.qcolor("paper")))
    circle.setPen(_pen(INK, 1.6))
    circle.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
    circle.setZValue(22)
    canvas.scene().addItem(circle)
    canvas.handles.append(circle)


def press_rotation(canvas, raw):
    """A press on the selected column's circle starts a turn (True); anything else is not this module's (False)."""
    element = canvas.selected_element()
    at = rotation_point(canvas, element)
    if at is None or math.dist(raw, at) > PICK / _zoom(canvas):
        return False
    canvas.drag = {"kind": "rotate", "index": canvas.selection[1], "moved": False, "start": raw}
    return True


def angle_at(centre, raw, shift):
    """The angle the pointer at `raw` gives an element turned about `centre`: clockwise on the drawing, 0° above it (plan_svg._square's), by steps of plan.ANGLE_STEP with Shift."""
    degrees = math.degrees(math.atan2(raw[0] - centre[0], -(raw[1] - centre[1])))
    return model.snap_angle(degrees) if shift else round(model.normalize_angle(degrees), 1)


def move_rotation(canvas, drag, raw, shift):
    """The turn followed: the element's angle as the pointer gives it, the change begun at the first move that changes it, so a click alone is no step of «Annuler»."""
    element = canvas.source["elements"][drag["index"]]
    value = angle_at(element["points"][0], raw, shift)
    if not model.set_element_angle(dict(element), value):
        return
    if not drag["moved"]:
        drag["moved"] = True
        canvas.begin_change()
    model.set_element_angle(element, value)
    canvas.redraw()
    canvas.update_helpers()
    canvas.angle_dragged.emit(float(element.get("angle", 0) or 0))


# --- the ruler -----------------------------------------------------------------------------

def ruler_text(canvas, a, b):
    """The distance between two points as the ruler says it: in metres where the plan has a scale (plan.distance_m), else in the sheet's own units, named as such."""
    per_m = canvas.per_m()
    if per_m:
        return model.metres_text(model.distance_m(a, b, per_m))
    return f"{math.dist(a, b):.1f} {canvas.unit_word()}".strip()


def clear_ruler(canvas):
    for item in getattr(canvas, "ruler_items", []):
        if item.scene() is not None:
            canvas.scene().removeItem(item)
    canvas.ruler_items = []
    canvas.ruler = []


def _draw(canvas, a, b):
    for item in getattr(canvas, "ruler_items", []):
        if item.scene() is not None:
            canvas.scene().removeItem(item)
    path = QPainterPath(QPointF(*a))
    path.lineTo(QPointF(*b))
    line = QGraphicsPathItem(path)
    line.setPen(_pen(INK, 1.4))
    line.setZValue(23)
    text = QGraphicsSimpleTextItem(ruler_text(canvas, a, b))
    text.setBrush(QBrush(QColor(INK)))
    text.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
    text.setPos(QPointF((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))
    text.setZValue(24)
    canvas.scene().addItem(line)
    canvas.scene().addItem(text)
    canvas.ruler_items = [line, text]
    canvas.ruler_shown = ruler_text(canvas, a, b)


def ruler_click(canvas, raw, shift):
    """A click with the ruler: the first point, then the second -- the distance shown and kept until the next click starts another or Escape takes it away. Snapped as the calibration is; nothing written."""
    anchor = canvas.ruler[0] if len(canvas.ruler) == 1 else None
    p, _kind = canvas.snapped(raw, anchor, shift)
    if len(canvas.ruler) != 1:
        clear_ruler(canvas)
        canvas.ruler = [p]
        return
    canvas.ruler.append(p)
    _draw(canvas, canvas.ruler[0], p)


def ruler_move(canvas, raw, shift):
    """The distance followed from the first point to the pointer."""
    if len(getattr(canvas, "ruler", [])) != 1:
        return
    p, kind = canvas.snapped(raw, canvas.ruler[0], shift)
    canvas.show_snap(p, kind)
    _draw(canvas, canvas.ruler[0], p)


# --- dimensions (issue #9, REQ-010) ---------------------------------------------------------------
# The five tools, by the kind they draw -- named as the static models' and the schemas' tools, so a tool shows the same symbol in the three tabs (dimension_icons).
DIMENSION_TOOLS = {"dimension-horizontal": "horizontal", "dimension-vertical": "vertical", "dimension-parallel": "parallel",
                   "dimension-chain": "chain", "dimension-angle": "angle"}


def is_dimension_tool(tool):
    return tool in DIMENSION_TOOLS


def _rounded(points):
    return [[round(x, 2), round(y, 2)] for x, y in points]


def chain_axis(points):
    """The line a chain is measured along: horizontal where its ends lie further apart across than up, vertical otherwise."""
    (x0, y0), (x1, y1) = points[0], points[-1]
    return "horizontal" if abs(x1 - x0) >= abs(y1 - y0) else "vertical"


def offset_at(axis, a, b, raw):
    """The offset a click at `raw` gives a dimension from `a` to `b`: its distance from their middle along the offset direction (domains/dimension.py)."""
    frame = dimension.direction(axis, a, b, model.SAME_POINT)
    if frame is None:
        return 0.0
    n = frame[1]
    base = dimension.midpoint(a, b)
    return (raw[0] - base[0]) * n[0] + (raw[1] - base[1]) * n[1]


def clear_dimension_draft(canvas):
    for item in getattr(canvas, "dim_items", []):
        if item.scene() is not None:
            canvas.scene().removeItem(item)
    canvas.dim_items = []
    canvas.dim_points = []
    canvas.dim_offset_next = False


def _draw_lines(canvas, lines, store, dashed=False, width=1.2, z=23):
    """`lines` drawn over the plan in the tools' blue, kept in the canvas's list `store` so they are taken away with it."""
    for line in lines:
        if len(line) < 2:
            continue
        path = QPainterPath(QPointF(*line[0]))
        for p in line[1:]:
            path.lineTo(QPointF(*p))
        item = QGraphicsPathItem(path)
        pen = _pen(INK, width)
        if dashed:
            pen.setStyle(Qt.PenStyle.DashLine)
        item.setPen(pen)
        item.setZValue(z)
        canvas.scene().addItem(item)
        getattr(canvas, store).append(item)


def _draft(canvas, raw):
    """The dimension the clicks so far and the pointer would make, or None while its points are not all there."""
    kind = DIMENSION_TOOLS[canvas.tool]
    pts = canvas.dim_points
    if not canvas.dim_offset_next:
        return None
    axis = chain_axis(pts) if kind == "chain" else kind
    dim = {"kind": kind, "points": _rounded(pts), "offset": offset_at(axis, pts[0], pts[-1], raw)}
    if kind == "chain":
        dim["axis"] = axis
    return dim


def draw_dimension_preview(canvas, raw):
    """While a dimension is drawn: the points clicked joined to the pointer, dashed -- and, once its points are all there, the dimension itself where the next click will put it."""
    for item in canvas.dim_items:
        if item.scene() is not None:
            canvas.scene().removeItem(item)
    canvas.dim_items = []
    pts = canvas.dim_points
    if not pts:
        return
    dim = _draft(canvas, raw)
    if dim is None:
        _draw_lines(canvas, [list(pts) + [raw]], "dim_items", dashed=True)
        return
    parts = model.dimension_parts(canvas.source, dim)
    lines = [[part["ends"][k], part["line"][k]] for part in parts for k in (0, 1)] + [list(part["line"]) for part in parts]
    _draw_lines(canvas, lines or [list(pts)], "dim_items")


def _add(canvas, dim):
    """The dimension drawn written into the plan, in one step of «Annuler», and selected."""
    clear_dimension_draft(canvas)
    canvas.begin_change()
    canvas.source.setdefault("dimensions", []).append(dim)
    canvas.selection = ("dimension", len(canvas.source["dimensions"]) - 1)
    canvas.end_change()
    canvas.selection_changed.emit()


def dimension_click(canvas, raw, shift):
    """A click with a dimension tool: a linear one's two ends, then where its line goes; a chain's points, Enter or a double-click, then where its line goes; an angle's corner and a point on each side. Snapped as everything drawn is."""
    kind = DIMENSION_TOOLS[canvas.tool]
    pts = canvas.dim_points
    if canvas.dim_offset_next:
        dim = _draft(canvas, raw)
        dim["offset"] = round(dim["offset"], 2)
        _add(canvas, dim)
        return
    p, _kind = canvas.snapped(raw, pts[-1] if pts else None, shift)
    if pts and math.dist(p, pts[-1]) <= canvas.tolerance() * 0.5:
        return   # one point clicked twice
    pts.append(p)
    if kind == "angle" and len(pts) == 3:
        _add(canvas, {"kind": "angle", "points": _rounded(pts)})
        return
    if kind in dimension.LINEAR and len(pts) == 2:
        canvas.dim_offset_next = True
    draw_dimension_preview(canvas, raw)


def finish_chain(canvas):
    """Enter or a double-click with the chain tool: its points are all there, the next click places its line. True where it did."""
    if canvas.tool == "dimension-chain" and len(canvas.dim_points) >= 3 and not canvas.dim_offset_next:
        canvas.dim_offset_next = True
        return True
    return False


def dimension_move(canvas, raw, shift):
    if canvas.dim_points:
        draw_dimension_preview(canvas, raw)


def _near_segment(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length2 = dx * dx + dy * dy
    t = 0.0 if length2 < 1e-18 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / length2))
    return math.dist(p, (a[0] + t * dx, a[1] + t * dy))


def hit_dimension(canvas, raw, tol):
    """The index of the dimension under `raw` -- its line, its arc, or where it cannot be drawn its points --, the last drawn first; None."""
    for i in range(len(canvas.source.get("dimensions") or []) - 1, -1, -1):
        dim = canvas.source["dimensions"][i]
        parts = model.dimension_parts(canvas.source, dim)
        for part in parts:
            if "radius" in part:
                if abs(math.dist(raw, part["centre"]) - part["radius"]) <= tol:
                    return i
            elif _near_segment(raw, *part["line"]) <= tol:
                return i
        if not parts:
            points = dim["points"]
            if any(_near_segment(raw, points[j - 1], points[j]) <= tol for j in range(1, len(points))):
                return i
    return None


def press_dimension(canvas, raw, tol):
    """A press on a dimension selects it and starts moving its line -- an angle's arc --: True; False where there is none."""
    i = hit_dimension(canvas, raw, tol)
    if i is None:
        return False
    canvas.select(("dimension", i))
    dim = canvas.source["dimensions"][i]
    canvas.drag = {"kind": "dimension", "index": i, "start": raw, "offset": float(dim.get("offset", 0.0)), "moved": False}
    return True


def move_dimension(canvas, drag, raw):
    """A selected dimension's line dragged: its offset follows the pointer -- an angle's radius --, in one step of «Annuler»."""
    dim = canvas.source["dimensions"][drag["index"]]
    points = dim["points"]
    if dim["kind"] == "angle":
        value = math.dist(raw, points[0]) * (-1 if drag["offset"] < 0 else 1)
    else:
        axis = dim.get("axis", "parallel") if dim["kind"] == "chain" else dim["kind"]
        value = drag["offset"] + offset_at(axis, points[0], points[-1], raw) - offset_at(axis, points[0], points[-1], drag["start"])
    if not drag["moved"]:
        if math.dist(raw, drag["start"]) < canvas.tolerance() * 0.5:
            return
        drag["moved"] = True
        canvas.begin_change()
    dim["offset"] = round(value, 2)
    canvas.redraw()
    canvas.update_helpers()


def add_dimension_highlight(canvas):
    """The selected dimension outlined and its points marked: what Delete takes away, what a drag moves."""
    if not canvas.selection or canvas.selection[0] != "dimension":
        return
    dims = canvas.source.get("dimensions") or []
    if canvas.selection[1] >= len(dims):
        return
    dim = dims[canvas.selection[1]]
    lines = []
    for part in model.dimension_parts(canvas.source, dim):
        if "radius" in part:
            (cx, cy), r = part["centre"], part["radius"]
            a, s = math.radians(part["start"]), math.radians(part["sweep"])
            lines.append([(cx + r * math.cos(a + s * k / 16), cy + r * math.sin(a + s * k / 16)) for k in range(17)])
        else:
            lines.append(list(part["line"]))
    _draw_lines(canvas, lines or [dim["points"]], "handles", width=3.0, z=19)
    for p in dim["points"]:
        canvas._add_handle(QPointF(*p))
