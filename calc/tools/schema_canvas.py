"""The drawing surface of Woodcore's «Schémas» tab (docs/domain/detail-schemas.md §3.3decies).

A QGraphicsView whose scene unit is the **millimetre** and whose axes are the schema's own -- x to the right, z down -- so nothing is turned over between what the engineer draws, what this shows and what the report prints. The figure itself is the very SVG the report sets, drawn over an exact rectangle and without its white ground, so the grid shows through it: `schema_svg.render()` is called on every change, and what the window shows and what the checker reads cannot drift apart.

statics_canvas.py's own file, ported: its grid that follows the zoom, its AutoCAD-style tracking (hover to acquire a point, lock to a ray, Tab a distance along it, Enter to place), its snapping, its draggable labels and its select/pan behaviour are all here, reading `schema.py` where that one reads `statics.py`. What is this tab's own is what a click puts down -- a piece, a fastener marker, a construction aid, a dimension -- and the three ways an area element may be drawn.

⚠️ The scene is millimetres, not metres, so the zoom limits are millimetre limits: a detail is read at 0.5 to 50 screen pixels to the millimetre, where a static model is read at 0.5 to 2000 to the metre. Everything else the two share.
"""

import math

from PySide6.QtCore import QByteArray, QLineF, QPoint, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPainterPath, QPen
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
from domains import schema as model
from domains import schema_svg as drawing_svg
from schema_canvas_place import ANGLE_STEP, CONNECTOR_TOOLS, TOOLS, _round, SchemaCanvasPlaceMixin  # split out of this module (issue #30): every name it had is still importable from it
from schema_canvas_input import MAX_ZOOM, MIN_ZOOM, SELECT_COLOUR, _cosmetic, SchemaCanvasInputMixin  # split out of this module (issue #30): every name it had is still importable from it

# How near the pointer has to be, in screen pixels, to take hold of something.
PICK_PX = 9


# What a schema with nothing in it is shown at: 400 mm across, so a first click lands on a grid one can read.
MIN_VIEW_MM = 400.0

GRID_STEPS = model.GRID_STEPS
GRID_MIN_PX = 14.0
GRID_MAX_LINES = 400

GRID_FINE = theme.colour("drawing-grid-fine")
GRID_HEAVY = theme.colour("drawing-grid-heavy")
GRID_AXIS = theme.colour("drawing-grid-axis")
# What a row of the lists under the drawing lights while the pointer is over it (v0.75) -- not the selection's blue, since hovering selects nothing.
HOVER_COLOUR = theme.colour("drawing-hover")
# «Cadrage»: the crop's own frame, and the veil over what the report will not show.
CROP_COLOUR = theme.colour("drawing-crop")
CROP_VEIL = theme.qcolor("drawing-crop-veil", 60)
TRACK_COLOUR = theme.colour("drawing-track")
SNAP_COLOUR = theme.colour("drawing-snap")
READOUT_COLOUR = theme.colour("drawing-readout")

ACQUIRE_MS = 220


# The three ways an area element may be drawn (the plan's own "sélecteur du mode"): two diagonal corners; an edge and a third click off it; an edge and a typed width. The last two are one construction -- schema.rectangle_from_edge -- and differ only in where the width comes from.
AREA_MODES = ("diagonal", "edge", "typed")


# What each of the four takes, in words the hint can use: two points, the second read as a place to
# land on (move, duplicate), as a direction from the first (rotate), or as the far end of an axis (mirror).
MODIFY_VERBS = ("move", "duplicate", "rotate", "mirror")

TOOL_ORDER = (
    ("elements", ("linear", "area")),
    ("connectors", tuple(f"connector:{k}" for k in CONNECTOR_TOOLS)),
    ("aids", ("aid-centre", "aid-point", "aid-vertical", "aid-horizontal",
              "aid-point-angle", "aid-perpendicular", "aid-parallel", "aid-two-points")),
    ("dimensions", ("dimension-horizontal", "dimension-vertical",
                    "dimension-parallel", "dimension-angle")),
    ("modify", MODIFY_VERBS),
)


# Half the arm of a named point's green cross, in screen pixels (v0.77).
POINT_CROSS_PX = 8.0


class SvgLayer(QGraphicsItem):
    """An SVG drawn over an exact rectangle of the scene -- statics_canvas's and plan_canvas's own: QGraphicsSvgItem sizes itself by the SVG's whole-pixel default size, which lands a symbol visibly beside what it marks.

    ⚠️ **Rendered once per view, not once per paint.** Every movement of the mouse repaints the whole viewport (the snap marker, the tracking ray, the preview all move), and `QSvgRenderer.render` costs what the figure's text costs to set: measured at a device pixel ratio of 2 on a 1900 x 1000 view, **about 300 ms a paint** -- Qt's DeviceCoordinateCache was not reused between paints -- so the tab stalled for seconds under a moving pointer, which is the freeze the engineer met. The figure is rendered into an image the size of the view and blitted; it is rendered again only when the SVG, the transform, the view's size or its pixel ratio change.
    """

    def __init__(self, renderer, rect):
        super().__init__()
        self.renderer = renderer
        self.rect = QRectF(rect)
        self.generation = 0      # bumped whenever the renderer is given a new SVG
        self._image = None
        self._key = None

    def set_rect(self, rect):
        self.prepareGeometryChange()
        self.rect = QRectF(rect)
        self.generation += 1
        self.update()

    def boundingRect(self):
        return self.rect

    def paint(self, painter, _option, widget=None):
        if not self.renderer.isValid():
            return
        device = painter.device()
        if widget is None or device is None:
            self.renderer.render(painter, self.rect)
            return
        ratio = device.devicePixelRatioF() or 1.0
        width, height = widget.width(), widget.height()
        xf = painter.worldTransform()
        key = (self.generation, xf.m11(), xf.m12(), xf.m21(), xf.m22(), round(xf.dx(), 4), round(xf.dy(), 4), width, height, ratio)
        if key != self._key:
            image = QImage(max(1, math.ceil(width * ratio)), max(1, math.ceil(height * ratio)), QImage.Format.Format_ARGB32_Premultiplied)
            image.setDevicePixelRatio(ratio)
            image.fill(Qt.GlobalColor.transparent)
            inner = QPainter(image)
            inner.setRenderHints(painter.renderHints())
            inner.setTransform(xf)
            self.renderer.render(inner, self.rect)
            inner.end()
            self._image, self._key = image, key
        painter.save()
        painter.resetTransform()
        painter.drawImage(QPointF(0, 0), self._image)
        painter.restore()


class SchemaCanvas(SchemaCanvasInputMixin, SchemaCanvasPlaceMixin, QGraphicsView):
    """Draws a detail schema and lets it be drawn. Everything it computes is schema.py's; what it holds is the tool, what is half-drawn, and where the tracking has got to."""

    about_to_change = Signal()
    changed = Signal()
    selection_changed = Signal()
    pointer = Signal(float, float, str)
    tool_done = Signal()
    tool_changed = Signal(str)   # the tool chosen (v0.117): the tab shows the options of «Surfacique» in its right pane while it is the one
    # why a click put nothing down: "element", "reference", "dimension-ends", "dimension-parallel",
    # "dimension-same-element". The tab turns it into a sentence, in its own three languages.
    refused = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
            | QPainter.RenderHint.TextAntialiasing
        )
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setBackgroundBrush(QBrush(theme.qcolor("paper")))
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.source = model.new_source("D01")
        self.tool = "select"
        self.area_mode = "diagonal"
        # The position records an element's section and label resolve against (v0.75), set by the tab from the export; and the position a new element is given -- the one last chosen in the panel.
        self.positions = {}
        self.values = {}   # the export's, which a text's variables print (issue #43): the tab's, set as a schema opens
        self.element_position = ""
        # What the position given fixes of an area element (schema.area_fixed): (the dimension that stays free -- "b", "h" or "" --, the fixed length in mm), or None for an area drawn freely; set by the tab's options for the tool (v0.117)
        self.area_fixed = None
        self.hover = None        # the (collection, id) a row of the lists lights while the pointer is over it
        self.typing_angle = False  # Tab after a rotation's centre takes an angle, not a distance
        self.snap_on = True
        self.grid_mode = "auto"
        self.selection = None    # the focused entry, (collection, id)
        self.extra = []          # everything else selected with it, same shape (v0.73)
        self.hint = ""
        self.axis_names = ("x", "z")

        self.drawing = []       # the clicks put down so far by the tool in hand
        self.dim_elements = []  # the elements an angle dimension has been given so far
        self.dim_hover = None   # the element under the pointer while an angle dimension is being picked
        self.cursor = None
        self.drag = None
        self.panning = None
        self.space_down = False
        self.acquired = None
        self.rays = []
        self.ray = None
        self.typing = False
        self.turning = None     # the aid line the pointer is turning
        self._drawing_cache = None
        self._snap_cache = None  # (the drawing it was worked out for, schema.snap_geometry's result)
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
        self.hover_item = QGraphicsPathItem()
        self.hover_item.setPen(_cosmetic(HOVER_COLOUR, 2.6, [4, 3]))
        self.hover_item.setZValue(19)
        self.scene().addItem(self.hover_item)
        # the crop: a veil over what lies outside it, and its own dashed frame
        self.crop_veil = QGraphicsPathItem()
        self.crop_veil.setPen(QPen(Qt.PenStyle.NoPen))
        self.crop_veil.setBrush(QBrush(CROP_VEIL))
        self.crop_veil.setZValue(15)
        self.scene().addItem(self.crop_veil)
        self.crop_item = QGraphicsRectItem()
        self.crop_item.setPen(_cosmetic(CROP_COLOUR, 1.4, [6, 4]))
        self.crop_item.setZValue(16)
        self.scene().addItem(self.crop_item)
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

    # -- the schema --------------------------------------------------------------

    def set_positions(self, positions):
        """The position records, {id: record}, an element's b, h and label are resolved against -- the export's, read by the tab (`connector.known_positions`)."""
        self.positions = dict(positions or {})
        self.invalidate()

    def set_source(self, source):
        self.source = source
        self.selection = None
        self.extra = []
        self.hover = None
        self.drawing = []
        self.dim_elements = []
        self.acquired = None
        self.ray = None
        self.turning = None
        self.hide_distance()
        self.invalidate()
        self.fit()

    def invalidate(self):
        self._drawing_cache = None
        self.redraw()

    def drawing_of(self):
        """The placed drawing, worked out once per state of the schema -- what the canvas hit-tests against."""
        if self._drawing_cache is None:
            # `editing`: the construction aids the report leaves out are drawn here, light, and the crop is marked over the whole detail rather than cutting it (v0.75)
            self._drawing_cache = drawing_svg.layout(self.source, positions=self.positions, editing=True, values=self.values)
        return self._drawing_cache

    def snap_geometry(self):
        """What a click may be pulled onto -- the corners and edges of every band, the crossings of pieces and construction lines -- worked out once per state of the schema and kept beside the drawing it belongs to. While something is being dragged the drawing is stale by design (`_drawing_cache` is None until the next redraw), and the geometry is then worked out afresh."""
        if self._drawing_cache is None:
            return model.snap_geometry(self.source, self.positions)
        if self._snap_cache is None or self._snap_cache[0] is not self._drawing_cache:
            self._snap_cache = (self._drawing_cache, model.snap_geometry(self.source, self.positions))
        return self._snap_cache[1]

    def label_frames(self):
        """The labels as this canvas draws them -- with the positions' own captions, which is what sizes their boxes (v0.75). `schema_svg.label_frames(source)` alone lays the schema out again without them, and a label then hit-tests at a size it is not drawn at."""
        return drawing_svg.label_frames(self.source, self.drawing_of())

    def redraw(self):
        d = self.drawing_of()
        # no white ground under it: the grid is what says where things are while they are being drawn
        # nor its construction lines nor its points: drawForeground draws them across the whole view, over everything -- the points last, over the lines (v0.77)
        svg = drawing_svg.render(d, self.selection, background=False, aid_lines=False, aid_points=False)
        self.renderer.load(QByteArray(svg.encode("utf-8")))
        x0, y0, x1, y1 = d["bbox"]
        self.overlay.set_rect(QRectF(x0, y0, x1 - x0, y1 - y0))
        self.grow_scene()
        self.update_helpers()

    def grow_scene(self):
        """Room to pan in, and it only ever grows: a scene rect that shrank with the schema would jerk the view every time something was drawn."""
        rect = QRectF(self.overlay.boundingRect())
        if rect.width() <= 0 or rect.height() <= 0:
            rect = QRectF(-MIN_VIEW_MM, -MIN_VIEW_MM, 2 * MIN_VIEW_MM, 2 * MIN_VIEW_MM)
        margin = max(5.0 * max(rect.width(), rect.height()), 5000.0)
        wanted = rect.adjusted(-margin, -margin, margin, margin)
        self.setSceneRect(wanted.united(self.sceneRect()) if not self.sceneRect().isNull() else wanted)

    def fit(self):
        """Zoom to everything -- the whole figure, and the 400 mm grid only for a schema that has nothing to fit (statics_canvas.fit's own rule, in millimetres)."""
        rect = QRectF(self.overlay.boundingRect())
        box = model.bbox(self.source)
        span = 0.0 if box is None else max(box[2] - box[0], box[3] - box[1])
        if rect.width() <= 0 or rect.height() <= 0:
            rect = QRectF(-MIN_VIEW_MM / 2, -MIN_VIEW_MM / 2, MIN_VIEW_MM, MIN_VIEW_MM)
        elif span <= 0:
            centre = rect.center()
            rect = QRectF(centre.x() - MIN_VIEW_MM / 2, centre.y() - MIN_VIEW_MM / 2, MIN_VIEW_MM, MIN_VIEW_MM)
        margin = 0.06 * max(rect.width(), rect.height())
        self.grow_scene()
        self.fitInView(rect.adjusted(-margin, -margin, margin, margin), Qt.AspectRatioMode.KeepAspectRatio)
        self.clamp_zoom()
        self.update_helpers()

    def clamp_zoom(self):
        scale = self.scale_px()
        if scale < MIN_ZOOM:
            self.scale(MIN_ZOOM / scale, MIN_ZOOM / scale)
        elif scale > MAX_ZOOM:
            self.scale(MAX_ZOOM / scale, MAX_ZOOM / scale)

    # -- the grid ---------------------------------------------------------------

    def scale_px(self):
        return max(self.transform().m11(), 1e-9)

    def grid_step(self):
        if self.grid_mode != "auto":
            step = float(self.grid_mode)
            for candidate, heavy in GRID_STEPS:
                if abs(candidate - step) < 1e-9:
                    return candidate, heavy
            return step, step * 5
        scale = self.scale_px()
        for step, heavy in reversed(GRID_STEPS):
            if step * scale >= GRID_MIN_PX:
                return step, heavy
        return GRID_STEPS[0]

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
        # Axis-parallel lines need no antialiasing, and one drawLines call per pen rather than one drawLine per line: the grid is repainted on every movement of the mouse, and drawn line by line with antialiasing it was most of what a paint cost once the figure itself was cached.
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        for pen, want in ((fine, False), (heavy_pen, True)):
            lines = []
            x = x0
            while x <= rect.right():
                on_heavy = abs(x / heavy - round(x / heavy)) < 1e-6
                if on_heavy == want and abs(x) > 1e-9:
                    lines.append(QLineF(x, rect.top(), x, rect.bottom()))
                x += step
            y = y0
            while y <= rect.bottom():
                on_heavy = abs(y / heavy - round(y / heavy)) < 1e-6
                if on_heavy == want and abs(y) > 1e-9:
                    lines.append(QLineF(rect.left(), y, rect.right(), y))
                y += step
            if lines:
                painter.setPen(pen)
                painter.drawLines(lines)
        painter.setPen(axis)
        painter.drawLine(QPointF(0, rect.top()), QPointF(0, rect.bottom()))
        painter.drawLine(QPointF(rect.left(), 0), QPointF(rect.right(), 0))
        painter.restore()

    def drawForeground(self, painter, rect):
        """The construction lines, **over everything and to the edges of the view** -- the engineer's rule: a construction line is infinite, and it is what the rest is read against. They are drawn here and not in the SVG, where a line has to stop somewhere: until now it stopped a share of the detail's size either side of its own point, a few centimetres on a large detail.

        Every line is shown in this tab, whatever its `shown` says; one the report will print (`shown`) is drawn heavier and darker than one it leaves out. The pens are cosmetic -- a width in screen pixels -- so a line reads the same at every zoom.
        """
        super().drawForeground(painter, rect)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        for ends, shown in self.aid_line_segments(rect):
            if shown:
                painter.setPen(_cosmetic(drawing_svg.AID_SHOWN_COLOUR, 1.8, [7, 4]))
            else:
                painter.setPen(_cosmetic(drawing_svg.AID_COLOUR, 1.0, [5, 4]))
            painter.drawLine(QPointF(*ends[0]), QPointF(*ends[1]))
        # The named points, green crosses in front of everything, the lines included, so a point is always seen (v0.77). A fixed size on screen: a point is found at every zoom.
        scale = abs(self.transform().m11()) or 1.0
        half = POINT_CROSS_PX / scale
        for (x, z), shown in self.aid_point_marks(rect):
            painter.setPen(_cosmetic(drawing_svg.POINT_COLOUR, 2.4 if shown else 1.5))
            painter.drawLine(QPointF(x - half, z), QPointF(x + half, z))
            painter.drawLine(QPointF(x, z - half), QPointF(x, z + half))
        painter.restore()

    def aid_point_marks(self, rect):
        """Every named point (an aid of kind `point`) inside `rect` (a QRectF of the scene, grown by the cross's own reach), with whether the report prints it: [((x, z), shown)]. What drawForeground draws over the lines, kept apart so it can be read without a painter."""
        scale = abs(self.transform().m11()) or 1.0
        reach = POINT_CROSS_PX / scale
        grown = rect.adjusted(-reach, -reach, reach, reach)
        out = []
        for aid in self.source.get("aids", []):
            if aid.get("kind") != "point":
                continue
            at = model.aid_point(aid)
            if at is None or not grown.contains(QPointF(at[0], at[1])):
                continue
            out.append(((at[0], at[1]), bool(aid.get("shown", True))))
        return out

    def aid_line_segments(self, rect):
        """Every construction line as the parts of it inside `rect` (a QRectF of the scene) that no label's box covers, with whether the report prints it: [((a, b), shown)]. What drawForeground draws, kept apart so it can be read without a painter.

        ⚠️ **Cut at the labels' boxes, as the exported figure cuts them** (v0.99, `schema_svg.cut_at_labels`): the lines are drawn here and not in the SVG, so a cut made only in the export would show the engineer one detail and the checker another -- and the whole reason the lines are drawn here is that the window and the report must not drift apart (this module's own docstring). One line may therefore come back as several segments.

        A line the report leaves out is cut too. What the cut is for is that the text is read, and a faint line crossing a number is as hard to read past as a heavy one; drawn across the whole view rather than across the figure's frame, a line here crosses far more labels than the exported one does.
        """
        box = (rect.left(), rect.top(), rect.right(), rect.bottom())
        frames = [frame for _key, frame in self.label_frames()]
        out = []
        for aid in self.source.get("aids", []):
            line = model.aid_line(aid)
            if line is None:
                continue
            ends = drawing_svg.clip_line(line[0], line[1], box)
            if ends is None:
                continue
            shown = bool(aid.get("shown", aid.get("kind") in model.AID_POINT_KINDS))
            for piece in drawing_svg.cut_at_labels(ends[0], ends[1], frames):
                out.append((piece, shown))
        return out

    # -- what is written over the drawing ----------------------------------------

    def paintEvent(self, event):
        """The tool's hint at the top left and the pointer's coordinates with the axes at the bottom left -- statics_canvas's own arrangement, inside the drawing where the eye already is."""
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(QFont(self.font()))
        metrics = painter.fontMetrics()
        pad = 8
        if self.hint:
            painter.setPen(QColor(READOUT_COLOUR))
            painter.drawText(QPoint(pad, pad + metrics.ascent()), self.hint)
        bottom = self.viewport().height() - pad
        if self._readout:
            painter.setPen(QColor(READOUT_COLOUR))
            painter.drawText(QPoint(pad, bottom - metrics.descent()), self._readout)
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
        changed = tool != self.tool
        self.tool = tool
        self.drawing = []
        self.dim_elements = []
        self.dim_hover = None
        self.cursor = None
        self.drag = None
        self.acquired = None
        self.ray = None
        self.finish_turning()
        self.hide_distance()
        self.snap_marker.setPath(QPainterPath())
        self.restore_cursor()
        self.update_helpers()
        if changed:
            self.tool_changed.emit(tool)

    def set_area_mode(self, mode):
        if mode in AREA_MODES:
            self.area_mode = mode
            self.drawing = []
            self.cursor = None
            self.update_helpers()

    def restore_cursor(self):
        self._over_label = False
        if self.tool == "pan" or self.space_down:
            self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
        elif self.tool == "select":
            self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.viewport().setCursor(Qt.CursorShape.CrossCursor)

    def tolerance(self):
        return PICK_PX / self.scale_px()

    def scene_point(self, event):
        p = self.mapToScene(event.position().toPoint())
        return (p.x(), p.y())

    def qp(self, p):
        return QPointF(p[0], p[1])

    def select(self, selection, add=False):
        """Selects one entry, or -- with `add` -- toggles it into the selection beside what is already there.

        ⚠️ The selection is **a focused entry and the rest**, not a flat list, and deliberately so: the properties panel, the table that scrolls itself into view and a drag all act on one entry, the way the focused item of a Windows explorer selection does. `self.selection` is that one; `self.extra` is everything else selected with it.
        """
        if add and selection is not None:
            current = self.selection_ids()
            if selection in current:
                current.remove(selection)
                self.selection = current[0] if current else None
                self.extra = current[1:]
            else:
                # The one just clicked takes the focus, and what was focused joins the rest.
                self.extra = current
                self.selection = selection
            self.redraw()
            self.selection_changed.emit()
            return
        if selection != self.selection or self.extra:
            self.selection = selection
            self.extra = []
            self.redraw()
            self.selection_changed.emit()

    def select_many(self, selections):
        """Sets the whole selection at once -- what a table hands over when several of its rows are picked."""
        selections = list(selections)
        if selections == self.selection_ids():
            return
        self.selection = selections[0] if selections else None
        self.extra = selections[1:]
        self.redraw()
        self.selection_changed.emit()

    def selection_ids(self):
        """Every (collection, id) selected, the focused one first."""
        return ([self.selection] if self.selection else []) + list(self.extra)

    def selected_entries(self):
        """The (collection, entry) pairs selected, skipping any a reload has since emptied."""
        out = []
        for collection, eid in self.selection_ids():
            entry = model.entry_of(self.source, collection, eid)
            if entry is not None:
                out.append((collection, entry))
        return out

    def selected(self):
        """The (collection, entry) focused, or (None, None)."""
        if not self.selection:
            return None, None
        collection, eid = self.selection
        return collection, model.entry_of(self.source, collection, eid)

    def begin_change(self):
        self.about_to_change.emit()

    def end_change(self):
        self.invalidate()
        self.changed.emit()

    def delete_selection(self):
        """Deletes everything selected, in **one** step of «Annuler» -- a multiple selection deleted in six steps would be undone in six."""
        chosen = self.selection_ids()
        if not chosen:
            return
        self.begin_change()
        for collection, eid in chosen:
            model.remove(self.source, collection, eid)
        self.selection = None
        self.extra = []
        self.end_change()
        self.selection_changed.emit()

    def clear_aid_lines(self):
        """*Supprimer toutes les lignes d'aide*: every construction line goes, the named points (centre, point) stay -- they are what a dimension and a connector may be anchored to."""
        lines = [a["id"] for a in self.source.get("aids", [])
                 if a.get("kind") not in model.AID_POINT_KINDS]
        if not lines:
            return
        self.begin_change()
        for eid in lines:
            model.remove(self.source, "aids", eid)
        if self.selection and self.selection[0] == "aids" and self.selection[1] in lines:
            self.selection = None
        self.end_change()
        self.selection_changed.emit()

    # -- what a click puts down --------------------------------------------------


    # -- tracking ---------------------------------------------------------------


    # -- modification ------------------------------------------------------------


    # -- the mouse and the keys --------------------------------------------------


    # -- what only the editor shows ---------------------------------------------


