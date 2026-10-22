"""The drawing surface of Woodcore's static models tab (docs/domain/static-models.md §3.3octies, docs/ui/window.md §10quater).

A QGraphicsView whose scene unit is the metre and whose axes are the model's own -- x to the right, **z down** -- so nothing is turned over between what the engineer types, what this shows and what the report prints. The figure itself is the very SVG the report sets, drawn over an exact rectangle and without its white ground, so the grid shows through it: `statics_svg.render()` is called on every change, and what the window shows and what the checker reads cannot drift apart.

Three things here are this tab's own rather than the position plan tab's. The **grid** follows the zoom -- 5 m, 1 m, 0.5 m, 0.1 m, with heavier lines every 10, 5, 5 and 1 -- and the snapping follows whatever it shows. The **tracking** works as AutoCAD's does: hovering a point acquires it, the cursor then locks to one of the eight polar directions, to the axis or the normal of a member meeting there, or to the line of a member extended, and Tab then takes a distance along that ray, which Enter puts down. All of its arithmetic is statics.py's, so this file only holds which state it is in. And a **click puts down what the tool draws**: a point, a member between two points, a support on a point -- which the pointer then turns, in steps of 45 degrees, until the next click sets it -- a release on the end of a member, a load on a point or on a member.

The wheel always zooms and the middle button always pans, whatever tool is chosen and whatever is half-drawn: a view one cannot move is a view one cannot draw in. The limits are absolute, in screen pixels to the metre, so they do not move with the model.

The only text it draws is the pointer's own coordinates and the axes beside them: every word is the tab's, in its three languages.
"""

import math

from PySide6.QtCore import QByteArray, QPoint, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QLineEdit,
)

import theme  # the ground of a distance that cannot be read (theme.py, v0.90)
from domains import statics as model
from domains import statics_geometry  # the geometry the canvas asks for, computed in the domain (D8)
from i18n import strings
from domains import statics_svg as drawing_svg
from canvas_items import SvgLayer, cosmetic as _cosmetic, saved_at  # the canvases' layer and pen, written once (D2)
from canvas_base import CanvasBase  # what the four canvases share, written once (D1)
_round = saved_at(3)   # a coordinate as it is saved: to the millimetre, far below what a click can place

# How near the pointer has to be, in screen pixels, to take hold of something.
PICK_PX = 9

# How far the view may be zoomed, in screen pixels to the metre. Absolute, so a model of one point and a model of thirty metres are held to the same range and the wheel never stops working where the engineer did not expect it to.
MIN_ZOOM = 0.5
MAX_ZOOM = 2000.0

# What a model with nothing in it, or next to nothing, is shown at: four metres across, so a first point lands on a grid one can read rather than on a millimetre.
MIN_VIEW_M = 4.0

# The grid steps in metres, coarsest first, each with the interval its heavier lines are drawn at, and the least a step may be apart on screen before the next coarser one is taken instead.
GRID_STEPS = model.GRID_STEPS
GRID_MIN_PX = 14.0
# However far the view is zoomed out, this many lines are never exceeded: a pathological zoom must not paint a hundred thousand of them.
GRID_MAX_LINES = 400

GRID_FINE = theme.colour("drawing-grid-fine")
GRID_HEAVY = theme.colour("drawing-grid-heavy")
GRID_AXIS = theme.colour("drawing-grid-axis")
SELECT_COLOUR = theme.colour("drawing-select")
TRACK_COLOUR = theme.colour("drawing-track")
SNAP_COLOUR = theme.colour("drawing-snap")
READOUT_COLOUR = theme.colour("drawing-readout")

# How long the pointer must rest on a point before it is acquired as a reference, in milliseconds.
ACQUIRE_MS = 220

# A support turns in steps of this many degrees while the pointer sets it; the panel takes any angle, to a tenth.
SUPPORT_STEP = 45.0

# What each tool draws. `geo` is how many clicks it takes: a point goes down on one, a member takes two, and the rest hang off what is already there. `on` says what a click must land on for the tool to draw at all.
TOOLS = {
    "select": {},
    "pan": {},
    "point": {"geo": "point", "on": "free"},
    "bar": {"geo": "member", "on": "free", "kind": "bar"},
    "cable": {"geo": "member", "on": "free", "kind": "cable"},
    "spring": {"geo": "member", "on": "free", "kind": "spring"},
    "support-fixed": {"geo": "attach", "on": "point", "type": "fixed"},
    "support-pinned": {"geo": "attach", "on": "point", "type": "pinned"},
    "support-roller": {"geo": "attach", "on": "point", "type": "roller"},
    # one tool per articulation rather than one tool and a combo: the engineer picks a symbol, not a setting
    "release-moment": {"geo": "attach", "on": "member-end", "dof": "moment", "spring": False},
    "release-shear": {"geo": "attach", "on": "member-end", "dof": "shear", "spring": False},
    "release-normal": {"geo": "attach", "on": "member-end", "dof": "normal", "spring": False},
    "release-spring-moment": {"geo": "attach", "on": "member-end", "dof": "moment", "spring": True},
    "point-load": {"geo": "attach", "on": "point"},
    "line-load": {"geo": "attach", "on": "member", "shape": "uniform"},
    "line-load-linear": {"geo": "attach", "on": "member", "shape": "linear"},
    # The dimensions, and the first tools here that take three clicks: the two ends of what is measured, then how far from them the dimension is drawn. The angle's two first clicks name members instead, there being no angle between two points.
    "dimension-horizontal": {"geo": "dimension", "on": "free", "kind": "horizontal"},
    "dimension-vertical": {"geo": "dimension", "on": "free", "kind": "vertical"},
    "dimension-parallel": {"geo": "dimension", "on": "free", "kind": "parallel"},
    "dimension-angle": {"geo": "dimension", "on": "member", "kind": "angle"},
    # a text, put down where the click falls (issue #43): one click, like a point, and written in the pane
    "text": {"geo": "text", "on": "free"},
}


class StaticsCanvas(CanvasBase, QGraphicsView):
    """Draws a static model and lets it be drawn. Everything it computes is statics.py's; what it holds is the tool, what is half-drawn, and where the tracking has got to."""

    # what CanvasBase reads of this canvas (D1)
    MODEL = model
    TOOLS = TOOLS
    ROUND = staticmethod(_round)
    MIN_ZOOM = MIN_ZOOM
    MAX_ZOOM = MAX_ZOOM
    GRID_STEPS = GRID_STEPS
    GRID_MIN_PX = GRID_MIN_PX
    SELECT_COLOUR = SELECT_COLOUR

    about_to_change = Signal()
    changed = Signal()
    selection_changed = Signal()
    pointer = Signal(float, float, str)
    tool_done = Signal()
    # why a click put nothing down: "point", "member", "member-end", "support-taken" or "release-taken". The tab turns it into a sentence, in its own three languages.
    refused = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
            | QPainter.RenderHint.TextAntialiasing
        )
        # The wheel zooms about the pointer, which zoom_at() does itself: Qt's AnchorUnderMouse anchors on the last point its own mouseMoveEvent saw, and this view handles its moves without calling it.
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setBackgroundBrush(QBrush(theme.qcolor("paper")))
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # The language the figure is drawn in -- the window's own, set by the tab -- so the preview reads
        # like the report that language would set.
        self.lang = strings.SOURCE_LANGUAGE
        self.source = model.new_source("S01")
        self.values = {}
        self.tool = "select"
        self.release_dof = "moment"
        self.release_spring = False
        self.line_shape = "uniform"
        self.snap_on = True
        self.grid_mode = "auto"
        self.selection = None
        self.hint = ""
        self.axis_names = ("x", "z")

        self.drawing = []  # the points of the member being drawn
        self.dim_members = []  # the members an angle dimension has been given so far
        self.dim_hover = None  # the member under the pointer while an angle dimension is being picked
        self.cursor = None
        self.drag = None
        self.panning = None
        self.space_down = False
        self.acquired = None
        self.rays = []
        self.ray = None
        self.typing = False
        self.turning = None  # the support the pointer is turning
        self.pending = None  # the point load waiting for the member it is measured from
        self._drawing_cache = None
        self._over_label = False
        self._readout = ""

        self.renderer = QSvgRenderer()
        self.overlay = SvgLayer(self.renderer, QRectF(0, 0, 1, 1))
        self.overlay.setZValue(10)
        self.scene().addItem(self.overlay)
        self.select_item = QGraphicsPathItem()
        self.select_item.setPen(_cosmetic(SELECT_COLOUR, 2.2))
        self.select_item.setZValue(20)
        self.scene().addItem(self.select_item)
        self.preview = QGraphicsPathItem()
        self.preview.setZValue(22)
        self.scene().addItem(self.preview)
        self.snap_marker = QGraphicsPathItem()
        self.snap_marker.setPen(_cosmetic(SNAP_COLOUR, 2))
        self.snap_marker.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        self.snap_marker.setZValue(24)
        self.scene().addItem(self.snap_marker)
        self.track_item = QGraphicsPathItem()
        self.track_item.setPen(_cosmetic(TRACK_COLOUR, 1.2, [6, 5]))
        self.track_item.setZValue(23)
        self.scene().addItem(self.track_item)
        self.handles = []

        self.distance = QLineEdit(self.viewport())
        self.distance.hide()
        self.distance.setFixedWidth(120)
        self.distance.textEdited.connect(self.on_typed)
        self.distance.returnPressed.connect(self.commit_typed)

        self.acquire_timer = QTimer(self)
        self.acquire_timer.setSingleShot(True)
        self.acquire_timer.setInterval(ACQUIRE_MS)
        self.acquire_timer.timeout.connect(self.acquire)
        self._hover = None

        self.redraw_timer = QTimer(self)
        self.redraw_timer.setSingleShot(True)
        self.redraw_timer.setInterval(30)
        self.redraw_timer.timeout.connect(self.redraw)

    # -- the model --------------------------------------------------------------

    def set_source(self, source, values=None):
        self.source = source
        if values is not None:
            self.values = values
        self.selection = None
        self.drawing = []
        self.acquired = None
        self.ray = None
        self.turning = None
        self.pending = None
        self.hide_distance()
        self.invalidate()
        self.fit()

    def invalidate(self):
        """The model changed: whatever was worked out about it is stale."""
        self._drawing_cache = None
        self.redraw()

    def drawing_of(self):
        """The placed drawing, worked out once per state of the model -- what the canvas hit-tests against."""
        if self._drawing_cache is None:
            self._drawing_cache = drawing_svg.layout(self.source, self.values, self.lang)
        return self._drawing_cache

    def redraw(self):
        d = self.drawing_of()
        # no white ground under it: the grid is what says where things are while they are being drawn. The nodes are this window's own: a dot on a point the figure has no symbol of says where one may click, which the report has no use for and must not claim is an articulation.
        svg = drawing_svg.render(d, self.highlight(), background=False, nodes=True)
        self.renderer.load(QByteArray(svg.encode("utf-8")))
        k = d["k"] or 1.0
        view = d["view"]
        self.overlay.set_rect(QRectF(view["x"] / k, view["y"] / k, view["w"] / k, view["h"] / k))
        self.grow_scene()
        self.update_helpers()

    def grow_scene(self):
        """Room to pan in, and it only ever grows: a scene rect that shrank with the model would jerk the view every time something was drawn."""
        rect = QRectF(self.overlay.boundingRect())
        if rect.width() <= 0 or rect.height() <= 0:
            rect = QRectF(-MIN_VIEW_M, -MIN_VIEW_M, 2 * MIN_VIEW_M, 2 * MIN_VIEW_M)
        margin = max(5.0 * max(rect.width(), rect.height()), 50.0)
        wanted = rect.adjusted(-margin, -margin, margin, margin)
        self.setSceneRect(wanted.united(self.sceneRect()) if not self.sceneRect().isNull() else wanted)

    def highlight(self):
        return [self.selection[1]] if self.selection else None

    def fit(self):
        """Zoom to everything -- the whole figure, and the four-metre grid only for a model that has nothing to fit: none at all, or one point, which alone would open magnified beyond use.

        A model that has been drawn is fitted to what it is, however small. Holding every model to four metres made a 0.5 m beam a twenty-fifth of the view: the floor is a square, and a square letterboxed into a drawing area far wider than it is tall blows the width out to twelve metres. What guards the top end is MAX_ZOOM, which is absolute and does it without a floor on the model.
        """
        rect = QRectF(self.overlay.boundingRect())
        box = model.bbox(self.source)
        span = 0.0 if box is None else max(box[2] - box[0], box[3] - box[1])
        if rect.width() <= 0 or rect.height() <= 0:
            rect = QRectF(-MIN_VIEW_M / 2, -MIN_VIEW_M / 2, MIN_VIEW_M, MIN_VIEW_M)
        elif span <= 0:
            centre = rect.center()
            rect = QRectF(centre.x() - MIN_VIEW_M / 2, centre.y() - MIN_VIEW_M / 2, MIN_VIEW_M, MIN_VIEW_M)
        margin = 0.06 * max(rect.width(), rect.height())
        self.grow_scene()
        self.fitInView(rect.adjusted(-margin, -margin, margin, margin), Qt.AspectRatioMode.KeepAspectRatio)
        self.clamp_zoom()
        self.update_helpers()

    # -- the grid ---------------------------------------------------------------

    def scale_px(self):
        return max(self.transform().m11(), 1e-9)

    def snap_step(self):
        return self.grid_step()[0] if self.snap_on else None

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        step, heavy = self.grid_step()
        if step <= 0:
            return
        if rect.width() / step > GRID_MAX_LINES or rect.height() / step > GRID_MAX_LINES:
            return
        fine, heavy_pen, axis = _cosmetic(GRID_FINE, 1), _cosmetic(GRID_HEAVY, 1), _cosmetic(GRID_AXIS, 1.4)
        x0 = math.floor(rect.left() / step) * step
        y0 = math.floor(rect.top() / step) * step
        for pen, want in ((fine, False), (heavy_pen, True)):
            painter.setPen(pen)
            x = x0
            while x <= rect.right():
                on_heavy = abs(x / heavy - round(x / heavy)) < 1e-6
                if on_heavy == want and abs(x) > 1e-9:
                    painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
                x += step
            y = y0
            while y <= rect.bottom():
                on_heavy = abs(y / heavy - round(y / heavy)) < 1e-6
                if on_heavy == want and abs(y) > 1e-9:
                    painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
                y += step
        painter.setPen(axis)
        painter.drawLine(QPointF(0, rect.top()), QPointF(0, rect.bottom()))
        painter.drawLine(QPointF(rect.left(), 0), QPointF(rect.right(), 0))

    # -- what is written over the drawing ----------------------------------------

    def paintEvent(self, event):
        """The tool's hint at the top left and the pointer's coordinates with the axes at the bottom left -- inside the drawing, where the eye already is, rather than under it."""
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont(self.font())
        painter.setFont(font)
        metrics = painter.fontMetrics()
        pad = 8
        if self.hint:
            painter.setPen(QColor(READOUT_COLOUR))
            painter.drawText(QPoint(pad, pad + metrics.ascent()), self.hint)
        bottom = self.viewport().height() - pad
        if self._readout:
            painter.setPen(QColor(READOUT_COLOUR))
            painter.drawText(QPoint(pad, bottom - metrics.descent()), self._readout)
        # the axes: x to the right, z down, drawn as they are in the model
        origin = QPoint(pad + 6, bottom - metrics.height() - 30)
        reach = 22
        painter.setPen(_cosmetic(READOUT_COLOUR, 1.4))
        painter.drawLine(origin, origin + QPoint(reach, 0))
        painter.drawLine(origin, origin + QPoint(0, reach))
        painter.setBrush(QBrush(QColor(READOUT_COLOUR)))
        for tip, back in (
            (origin + QPoint(reach, 0), (QPoint(reach - 5, -3), QPoint(reach - 5, 3))),
            (origin + QPoint(0, reach), (QPoint(-3, reach - 5), QPoint(3, reach - 5))),
        ):
            path = QPainterPath()
            path.moveTo(QPointF(tip))
            path.lineTo(QPointF(origin + back[0]))
            path.lineTo(QPointF(origin + back[1]))
            path.closeSubpath()
            painter.drawPath(path)
        painter.setPen(QColor(READOUT_COLOUR))
        painter.drawText(origin + QPoint(reach + 4, 4), self.axis_names[0])
        painter.drawText(origin + QPoint(4, reach + metrics.ascent() - 2), self.axis_names[1])
        painter.end()

    def set_hint(self, text):
        self.hint = text
        self.viewport().update()

    def set_readout(self, text):
        self._readout = text
        self.viewport().update()

    # -- tools and picking ------------------------------------------------------

    def set_tool(self, tool):
        self.tool = tool
        self.drawing = []
        self.dim_members = []
        self.dim_hover = None
        self.cursor = None
        self.drag = None
        self.acquired = None
        self.ray = None
        self.finish_turning()
        if self.pending is not None:
            self.set_reference((1e12, 1e12))
        self.hide_distance()
        self.snap_marker.setPath(QPainterPath())
        self.restore_cursor()
        self.update_helpers()

    def tolerance(self):
        return PICK_PX / self.scale_px()

    def scene_point(self, event):
        """A point of the viewport in the model's frame. The scene is the model: x right, z down, one unit to the metre."""
        p = self.mapToScene(event.position().toPoint())
        return (p.x(), p.y())

    def qp(self, p):
        """A model point as a scene point -- the same thing, said in Qt."""
        return QPointF(p[0], p[1])

    def select(self, selection):
        if selection != self.selection:
            self.selection = selection
            self.redraw()
            self.selection_changed.emit()

    def begin_change(self):
        self.about_to_change.emit()

    def end_change(self):
        self.invalidate()
        self.changed.emit()

    def delete_selection(self):
        if not self.selection:
            return
        collection, eid = self.selection
        self.begin_change()
        model.remove(self.source, collection, eid)
        self.selection = None
        self.end_change()
        self.selection_changed.emit()

    # -- what a click puts down --------------------------------------------------

    def add_point(self, p):
        entry = {"id": model.next_id(self.source, "points"), "x": _round(p[0]), "z": _round(p[1])}
        self.source["points"].append(entry)
        return entry["id"]

    def point_or_new(self, p):
        """The point under `p`, or a new one there -- what a member's end is drawn onto."""
        hit = model.hit_point(self.source, p, self.tolerance())
        return hit if hit is not None else self.add_point(p)

    def add_member(self, a, b):
        kind = TOOLS[self.tool].get("kind", "bar")
        self.begin_change()
        p1 = self.point_or_new(a)
        p2 = self.point_or_new(b)
        if p1 == p2:
            self.end_change()
            return
        entry = {"id": model.next_id(self.source, "members"), "kind": kind, "p1": p1, "p2": p2}
        if kind == "spring":
            entry["stiffness"] = {"value": 1000.0, "unit": model.MEMBER_STIFFNESS_UNIT}
        self.source["members"].append(entry)
        self.selection = ("members", entry["id"])
        self.end_change()
        self.selection_changed.emit()

    def dimension_anchor(self, p):
        """One end of a dimension, from a click: the point of the model under it, which the dimension then follows as that point is moved, or a place of its own. The `label_offset` philosophy of a plan's numbers (docs/domain/position-plans.md §3.3sexies)."""
        pid = model.hit_point(self.source, p, self.tolerance())
        return {"point": pid} if pid is not None else {"x": _round(p[0]), "z": _round(p[1])}

    def add_dimension(self, a, b, c):
        """A length, from its three clicks: the two ends, then the point the dimension line is to run through."""
        entry = self.linear_entry(a, b, c)
        if entry is None:
            self.refused.emit("dimension-ends")
            return
        self.begin_change()
        self.source["dimensions"].append(entry)
        self.selection = ("dimensions", entry["id"])
        self.end_change()
        self.selection_changed.emit()

    def angle_entry(self, p):
        """The angle dimension a third click at `p` would make, or None where the two members do not cross. The click gives the arc its radius and, as a `bearing` from the corner, **which of the four sectors** is meant: the engineer measures the angle he pointed at (statics.angle_rays)."""
        entry = {
            "id": model.next_id(self.source, "dimensions"),
            "kind": "angle",
            "from": {"member": self.dim_members[0]},
            "to": {"member": self.dim_members[1]},
            "offset": 0.0,
        }
        corner = model.dimension_corner(self.source, entry)
        if corner is None:
            return None
        reached = statics_geometry.angle_reach(corner[0], p)
        if reached is None:
            return None
        radius, bearing = reached
        entry["offset"] = _round(radius)
        entry["bearing"] = _round(bearing, 1)
        return entry

    def add_angle_dimension(self, p):
        """The angle between the two members already picked, its arc drawn through the third click."""
        entry = self.angle_entry(p)
        if entry is None:
            self.refused.emit("dimension-parallel")
            return
        self.dim_members = []
        self.dim_hover = None
        self.begin_change()
        self.source["dimensions"].append(entry)
        self.selection = ("dimensions", entry["id"])
        self.end_change()
        self.selection_changed.emit()

    def add_text(self, p):
        """A text put down at `p` (issue #43): empty, selected, written in the pane -- one step of «Annuler»."""
        entry = {"id": model.next_id(self.source, model.figure_text.COLLECTION), "x": _round(p[0]), "z": _round(p[1]), "text": ""}
        self.begin_change()
        self.source.setdefault(model.figure_text.COLLECTION, []).append(entry)
        self.selection = (model.figure_text.COLLECTION, entry["id"])
        self.end_change()
        self.selection_changed.emit()
        self.tool_done.emit()

    def attach(self, raw):
        """A support, a release or a load, put on what lies under the pointer. Where there is nothing of the kind the tool needs, it says so rather than drawing into thin air."""
        tool = TOOLS[self.tool]
        tol = self.tolerance()
        if tool["on"] == "point":
            pid = model.hit_point(self.source, raw, tol * 2)
            if pid is None:
                self.refused.emit("point")
                return
            self.begin_change()
            if self.tool == "point-load":
                entry = {
                    "id": model.next_id(self.source, "point_loads"), "point": pid,
                    "direction": "vertical", "magnitude": {"value": 1.0, "unit": "kN"},
                    "label": "", "show": "value",
                }
                self.source["point_loads"].append(entry)
                self.selection = ("point_loads", entry["id"])
                self.end_change()
                self.selection_changed.emit()
                # the next click names the member it is measured from and drawn along; anywhere else ends the step
                self.pending = entry["id"]
                self.begin_change()
                return
            if any(s["point"] == pid for s in self.source["supports"]):
                self.end_change()
                self.refused.emit("support-taken")
                return
            entry = {"id": model.next_id(self.source, "supports"), "point": pid,
                     "type": tool["type"], "angle": 0.0}
            self.source["supports"].append(entry)
            self.selection = ("supports", entry["id"])
            self.end_change()
            self.selection_changed.emit()
            # the pointer now turns it, in steps of 45 degrees, until the next click sets it
            self.turning = {"id": entry["id"], "at": model.point_at(self.source, pid)}
            self.begin_change()
            return

        mid = model.hit_member(self.source, raw, tol * 2)
        if mid is None:
            self.refused.emit("member-end" if tool["on"] == "member-end" else "member")
            return
        if tool.get("shape"):
            shape = tool["shape"]
            entry = {
                "id": model.next_id(self.source, "line_loads"), "member": mid,
                "shape": shape, "direction": "vertical",
                "magnitude": {"value": 1.0, "unit": "kN/m"}, "label": "", "show": "value",
            }
            if shape == "linear":
                entry["magnitude_end"] = {"value": 0.0, "unit": "kN/m"}
            self.begin_change()
            self.source["line_loads"].append(entry)
            self.selection = ("line_loads", entry["id"])
            self.end_change()
            self.selection_changed.emit()
            return

        ends = model.member_points(self.source, mid)
        end = "start" if math.dist(raw, ends[0]) <= math.dist(raw, ends[1]) else "end"
        dof = tool.get("dof", "moment")
        if any(r["member"] == mid and r["end"] == end and r["dof"] == dof
               for r in self.source["releases"]):
            self.refused.emit("release-taken")
            return
        entry = {"id": model.next_id(self.source, "releases"), "member": mid, "end": end, "dof": dof}
        if tool.get("spring") and dof in model.SPRING_UNITS:
            entry["stiffness"] = {"value": 1000.0, "unit": model.SPRING_UNITS[dof]}
        self.begin_change()
        self.source["releases"].append(entry)
        self.selection = ("releases", entry["id"])
        self.end_change()
        self.selection_changed.emit()

    def set_reference(self, raw):
        """The second click of a point load: the member it is measured from, which is also the one `along` is counted on. A click on nothing simply ends the step -- a load needs no reference member unless its angle is taken from one."""
        entry = model.entry_of(self.source, "point_loads", self.pending)
        mid = model.hit_member(self.source, raw, self.tolerance() * 2)
        if entry is not None and mid is not None:
            entry["reference"] = mid
        self.pending = None
        self.end_change()
        self.selection_changed.emit()

    def turn(self, raw):
        """A support just put down, turned to face where the pointer is -- in steps of 45 degrees, so an upright support, one against a wall and one on a slope each come out square."""
        entry = model.entry_of(self.source, "supports", self.turning["id"])
        at = self.turning["at"]
        if entry is None or at is None:
            return
        dx, dz = raw[0] - at[0], raw[1] - at[1]
        if math.hypot(dx, dz) < 1e-9:
            return
        length = math.hypot(dx, dz)
        g = (dx / length, dz / length)
        angle = drawing_svg.support_angle(g)
        entry["angle"] = _round(round(angle / SUPPORT_STEP) * SUPPORT_STEP, 1)
        self._drawing_cache = None
        self.redraw_timer.start()

    # -- tracking ---------------------------------------------------------------

    def anchor(self):
        """Where the cursor is tracking from: the last point of the member being drawn, else the point the pointer rested on."""
        return self.drawing[-1] if self.drawing else self.acquired

    def track(self, raw, shift=False):
        """Where a click at `raw` would land, and what it locked to."""
        anchor = self.anchor()
        if anchor is not None and shift:
            return {"point": model.constrain(anchor, raw), "ray": None, "kind": "shift",
                    "distance": math.dist(anchor, raw), "angle": None}
        if anchor is None:
            p, kind = model.snap(self.source, raw, self.tolerance(), self.snap_step())
            return {"point": p, "ray": None, "kind": kind, "distance": None, "angle": None}
        return model.track(self.source, anchor, raw, self.tolerance(), self.snap_step())

    def show_distance(self):
        if self.ray is None or self.anchor() is None:
            return
        self.typing = True
        p = self.mapFromScene(self.qp(self.cursor or self.anchor()))
        self.distance.move(min(max(p.x() + 14, 0), max(self.viewport().width() - 130, 0)), max(p.y() - 12, 0))
        self.distance.setText(model.fmt_number(math.dist(self.anchor(), self.cursor or self.anchor())))
        self.distance.selectAll()
        self.distance.show()
        self.distance.setFocus()

    def hide_distance(self):
        self.typing = False
        self.distance.hide()
        self.distance.setStyleSheet("")
        self.setFocus()

    def on_typed(self, text):
        p = model.typed_point(self.anchor(), self.ray, text) if self.ray else None
        self.distance.setStyleSheet("" if p is not None or not text.strip() else f"background:{theme.colour('danger-soft')};")
        if p is not None:
            self.cursor = p
            self.update_helpers()

    def commit_typed(self):
        p = model.typed_point(self.anchor(), self.ray, self.distance.text()) if self.ray else None
        if p is None:
            return
        self.hide_distance()
        self.place(p)

    def place(self, p):
        """Puts a point down where the tool is drawing."""
        geo = TOOLS[self.tool].get("geo")
        if geo == "point":
            self.begin_change()
            pid = self.add_point(p)
            self.selection = ("points", pid)
            self.end_change()
            self.selection_changed.emit()
        elif geo == "text":
            self.add_text(p)
        elif geo == "dimension":
            if TOOLS[self.tool]["kind"] == "angle":
                # the two members are already picked: this click is the arc's radius
                if len(self.dim_members) == 2:
                    self.cursor = None
                    self.add_angle_dimension(p)
            else:
                self.drawing.append(p)
                if len(self.drawing) == 3:
                    a, b, c = self.drawing
                    self.drawing = []
                    self.cursor = None
                    self.add_dimension(a, b, c)
        elif geo == "member":
            self.drawing.append(p)
            if len(self.drawing) == 2:
                a, b = self.drawing
                self.drawing = []
                self.cursor = None
                self.add_member(a, b)
                # AutoCAD's chain: the end just put down is where the next one starts from
                self.acquired = b
                self.rays = model.tracking_rays(self.source, b)
        self.update_helpers()

    # -- the mouse and the keys --------------------------------------------------

    def start_pan(self, event):
        self.panning = event.position()
        self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)

    def mousePressEvent(self, event):
        self.setFocus()
        # the middle button always pans, whatever tool is chosen and whatever is half-drawn
        if event.button() == Qt.MouseButton.MiddleButton or (
            event.button() == Qt.MouseButton.LeftButton and (self.tool == "pan" or self.space_down)
        ):
            self.start_pan(event)
            return
        if event.button() == Qt.MouseButton.RightButton:
            if self.pending is not None:
                self.set_reference((1e12, 1e12))
            elif self.turning is not None:
                self.finish_turning()
            elif self.drawing or self.dim_members:
                self.drawing = []
                self.dim_members = []
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
        if self.pending is not None:
            self.set_reference(raw)
            return
        if self.tool == "select":
            self.press_select(raw)
            self.update_helpers()
            return
        geo = TOOLS[self.tool].get("geo")
        if geo == "attach":
            self.attach(raw)
            return
        if geo == "dimension" and TOOLS[self.tool]["on"] == "member" and len(self.dim_members) < 2:
            mid = model.hit_member(self.source, raw, self.tolerance() * 2)
            if mid is None:
                self.refused.emit("member")
                return
            if mid in self.dim_members:
                self.refused.emit("dimension-same-member")
                return
            self.dim_members.append(mid)
            self.update_helpers()
            return
        self.hide_distance()
        self.place(self.track(raw, shift)["point"])

    def press_select(self, raw):
        tol = self.tolerance()
        collection, entry = self.selected()
        if entry is not None and collection == "points":
            if math.dist(raw, (entry["x"], entry["z"])) <= tol:
                self.drag = {"kind": "point", "id": entry["id"], "moved": False}
                return
        d = self.drawing_of()
        frames = drawing_svg.label_frames(self.source, self.values, d)
        owner = drawing_svg.hit_label(self.source, raw, tol, frames, d["k"])
        if owner[0] == model.figure_text.COLLECTION:
            # a text is moved itself, its x and z, not set off from a place of its own: it has no other (issue #43)
            self.select(owner)
            entry = model.entry_of(self.source, *owner)
            self.drag = {"kind": "text", "owner": owner, "start": raw, "at": (float(entry["x"]), float(entry["z"])), "moved": False}
            return
        if owner[0] is not None:
            self.select(owner)
            offset = (model.entry_of(self.source, *owner) or {}).get("label_offset") or [0, 0]
            self.drag = {"kind": "label", "owner": owner, "start": raw,
                         "offset": (float(offset[0]), float(offset[1])), "moved": False}
            return
        pid = model.hit_point(self.source, raw, tol)
        if pid is not None:
            self.select(("points", pid))
            self.drag = {"kind": "point", "id": pid, "moved": False}
            return
        hit = drawing_svg.hit_load(self.source, raw, tol, d)
        if hit[0] is not None:
            self.select(hit)
            return
        mid = model.hit_member(self.source, raw, tol)
        if mid is not None:
            self.select(("members", mid))
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
        if drag is not None and event.buttons() & Qt.MouseButton.LeftButton:
            if not drag["moved"]:
                drag["moved"] = True
                self.begin_change()
            if drag["kind"] == "point":
                entry = model.entry_of(self.source, "points", drag["id"])
                p, kind = model.snap(self.source, raw, self.tolerance(), self.snap_step())
                entry["x"], entry["z"] = _round(p[0]), _round(p[1])
                self.show_snap(p, kind)
                self.pointer.emit(p[0], p[1], kind or "")
            elif drag["kind"] == "text":
                entry = model.entry_of(self.source, *drag["owner"])
                moved = model.constrain(drag["start"], raw) if shift else raw
                entry["x"] = _round(drag["at"][0] + moved[0] - drag["start"][0])
                entry["z"] = _round(drag["at"][1] + moved[1] - drag["start"][1])
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
        if TOOLS[self.tool].get("geo") in ("point", "member", "dimension"):
            result = self.track(raw, shift)
            self.cursor = result["point"]
            self.ray = result["ray"]
            self.show_snap(result["point"], result["kind"])
            # the member under the pointer, while an angle dimension is still choosing its two
            want_member = (TOOLS[self.tool].get("geo") == "dimension"
                           and TOOLS[self.tool]["on"] == "member" and len(self.dim_members) < 2)
            self.dim_hover = model.hit_member(self.source, raw, self.tolerance() * 2) if want_member else None
            # what the dimension measures so far comes first: it is what the engineer is watching
            measured = self.dimension_readout()
            self.pointer.emit(result["point"][0], result["point"][1],
                              measured or self.readout(result))
            # hovering a point acquires it, as long as nothing is half-drawn
            hover = model.hit_point(self.source, raw, self.tolerance())
            at = None if hover is None else model.point_at(self.source, hover)
            if at != self._hover:
                self._hover = at
                self.acquire_timer.stop()
                if at is not None and not self.drawing:
                    self.acquire_timer.start()
            self.update_helpers()
            return
        self.show_snap(raw, None)
        if self.tool == "select" and drag is None and not self.space_down:
            d = self.drawing_of()
            over = drawing_svg.hit_label(self.source, raw, self.tolerance(),
                                         drawing_svg.label_frames(self.source, self.values, d), d["k"])[0] is not None
            if over != self._over_label:
                self._over_label = over
                self.viewport().setCursor(Qt.CursorShape.SizeAllCursor if over else Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event):
        if self.panning is not None:
            self.panning = None
            self.restore_cursor()
            return
        drag, self.drag = self.drag, None
        self.show_snap((0, 0), None)
        if drag is not None and drag.get("moved"):
            self.end_change()

    def focusNextPrevChild(self, _next):
        """Tab is the tracking's, not the focus chain's: without this it would leave the canvas the moment a direction is locked."""
        return False

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Space and not event.isAutoRepeat():
            self.space_down = True
            self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
            return
        if key == Qt.Key.Key_Tab and self.ray is not None and not self.typing:
            self.show_distance()
            return
        if key == Qt.Key.Key_Escape:
            if self.typing:
                self.hide_distance()
            elif self.pending is not None:
                self.set_reference((1e12, 1e12))
            elif self.turning is not None:
                self.finish_turning()
            elif self.drawing or self.dim_members:
                self.drawing = []
                self.dim_members = []
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
        if key == Qt.Key.Key_Backspace and (self.drawing or self.dim_members):
            (self.drawing or self.dim_members).pop()
            self.update_helpers()
            return
        if key == Qt.Key.Key_Delete and self.selection is not None and not self.drawing:
            self.delete_selection()
            return
        super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_helpers()

    # -- what only the editor shows ---------------------------------------------

    def dimension_preview(self):
        """What the dimension being drawn would look like, as a path in scene metres, or None where there is nothing to show yet.

        It is built from the **same geometry the figure is drawn from** (`model.dimension_line`, `model.dimension_angle`) rather than sketched by hand here, so what the pointer promises is what the third click delivers. From the first click on: with one end down, the far end follows the pointer and the length is already read out; with both down, the line follows the pointer to where it will be drawn. For an angle, the arc appears as soon as the second member is picked, in the sector the pointer is in.
        """
        if TOOLS[self.tool].get("geo") != "dimension" or self.cursor is None:
            return None
        path = QPainterPath()
        if TOOLS[self.tool]["kind"] == "angle":
            if len(self.dim_members) != 2:
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
        """What the dimension being drawn measures so far, for the line under the pointer -- «2.5 m» as the far end is moved, «90°» as the sector is chosen. Empty where there is nothing to measure yet."""
        if TOOLS[self.tool].get("geo") != "dimension" or self.cursor is None:
            return ""
        entry = None
        if TOOLS[self.tool]["kind"] == "angle":
            if len(self.dim_members) == 2:
                entry = self.angle_entry(self.cursor)
        elif self.drawing:
            b = self.drawing[1] if len(self.drawing) > 1 else self.cursor
            entry = self.linear_entry(self.drawing[0], b,
                                      self.cursor if len(self.drawing) > 1 else None)
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
        collection, entry = self.selected()
        if entry is not None:
            if collection == "points":
                p = self.qp((entry["x"], entry["z"]))
                r = 9.0 / self.scale_px()
                path.addEllipse(p, r, r)
                self.add_handle(p)
            elif collection == "members":
                ends = model.member_points(self.source, entry["id"])
                if ends:
                    path.moveTo(self.qp(ends[0]))
                    path.lineTo(self.qp(ends[1]))
                    for q in ends:
                        self.add_handle(self.qp(q))
            d = self.drawing_of()
            for owner_collection, owner, frame in drawing_svg.label_frames(self.source, self.values, d):
                if (owner_collection, owner) == self.selection:
                    corners = [QPointF(c[0] / d["k"], c[1] / d["k"])
                               for c in drawing_svg.label_corners(frame)]
                    path.moveTo(corners[0])
                    for c in corners[1:]:
                        path.lineTo(c)
                    path.closeSubpath()
        self.select_item.setPath(path)

        preview = QPainterPath()
        # a member an angle dimension has been given already, so the second click is made knowing the first,
        # and the one under the pointer, so the engineer sees what he is about to pick rather than guessing
        marked = list(self.dim_members)
        if self.dim_hover is not None and self.dim_hover not in marked:
            marked.append(self.dim_hover)
        for mid in marked:
            ends = model.member_points(self.source, mid)
            if ends:
                preview.moveTo(self.qp(ends[0]))
                preview.lineTo(self.qp(ends[1]))
        dim = self.dimension_preview()
        if dim is not None:
            preview.addPath(dim)
        elif TOOLS[self.tool].get("geo") != "dimension":
            points = list(self.drawing) + ([self.cursor] if self.cursor is not None else [])
            if len(points) >= 2:
                preview.moveTo(self.qp(points[0]))
                for q in points[1:]:
                    preview.lineTo(self.qp(q))
            elif points and TOOLS[self.tool].get("geo") == "point":
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
