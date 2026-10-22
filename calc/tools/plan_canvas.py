"""The drawing surface of Woodcore's position plan tab (docs/domain/position-plans.md §3.3sexies, docs/ui/window.md §10quater): the background -- a page of a PDF rendered by QtPdf, an image or an SVG --, over it the plan's symbols exactly as plan_svg.py draws them for the report, and over those what only an editor shows: the element selected, its corners and its number's box, the line being drawn, the point the pointer snaps to, and the frame the report will show.

What is drawn is the report's own drawing, so the plan the engineer sees is the plan the checker will read. The geometry -- what lies under the pointer, where it snaps, Shift's 0°/45°/90° -- is calc/domains/plan.py's, which has no Qt in it; this module turns the mouse and the keys into calls to it and into edits of the source it is given. It has no text of its own: the tab (plan_tab.py) says what is what, in the window's language.
"""

import collections
import dataclasses
import functools
import hashlib
import json
import math
import os
import re
import threading
import time
from pathlib import Path

import shiboken6
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QObject, QPointF, QRect, QRectF, QSize, Qt, QTimer, Signal, qVersion
from PySide6.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPainterPath, QPen, QPixmap, QPixmapCache, QTransform
from PySide6.QtPdf import QPdfDocument, QPdfDocumentRenderOptions, QPdfPageRenderer
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsScene, QGraphicsSimpleTextItem, QGraphicsView, QLineEdit

import theme  # the desk around the sheet (theme.py, v0.90)
import plan_canvas_tools  # the circle a column is turned by, and the ruler (issue #9)
import plan_canvas_edit  # «Déplacer», «Copier» and «Ligne d'aide» (issue #18)
import usersettings  # where Woodcore keeps its caches (usersettings.py)
from domains import lines  # a parallel aid's line, through an element's side (issue #18)
from domains import plan as model
from domains import plan_documents
from domains import plan_svg
from domains import plan_tracking as tracking
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
from plan_canvas_editing import AXIS_TOOLS, LEVEL_TOOL, PICK_PX, POINT_TOOLS, SELECTION_LISTS, TEXT_TOOL, PlanCanvasEditMixin  # split out of this module (issue #30): every name it had is still importable from it
from plan_canvas_input import (  # split out of this module (issue #30): every name it had is still importable from it
    ALIGN_TOOL,
    CROP_COLOUR,
    MAX_ZOOM,
    READOUT_KINDS,
    SECTION_TOOLS,
    SELECT_COLOUR,
    STOREY_TOOLS,
    _box_corners,
    hit_load_level,
    hit_storey_box,
    hit_storey_line,
    readout_kind,
    PlanCanvasInputMixin,
)
from canvas_base import CanvasBase  # what the four canvases share, written once (D1)

SNAP_COLOUR = theme.qcolor("plan-snap")
# The tracking (v0.116, domains/plan_tracking.py): how long the pointer must rest on a point of the plan before it is acquired as a reference, in milliseconds, and the colour of the dotted lines the cursor locks to.
ACQUIRE_MS = 350
TRACK_COLOUR = theme.qcolor("plan-track")
SUPERPOSE_Z = 5
ALIGN_COLOUR = theme.qcolor("plan-align")


class PlanCanvas(PlanCanvasInputMixin, PlanCanvasEditMixin, PlanCanvasViewMixin, CanvasBase, QGraphicsView):
    """The plan being edited, and the tools that edit it. It edits the `source` dictionary it is given in place -- the tab's draft -- and says so: `about_to_change` just before an edit (the tab keeps the state for its undo history), `changed` once it is made. `selection_changed` when another element or axis is selected, `pointer` as the pointer moves (its sheet coordinates and what it snaps to), `calibrated` with the two points of a calibration, `tool_done` when a one-shot tool (the crop, the calibration) has been used, `axes_renamed` with the (old, new) names of the axes a new axis moved up (plan.insert_axis), `refused` with the type of a tool that was used with no position number to give what it would draw -- an element carries a position of Positionen.xlsx, and `propose_label` found none of that type --, and `pages_known` with the page count of the plan's PDF once it is loaded, which may be a moment after the plan is shown (use_pdf).

    Since v0.114 a plan is shown as its **crop alone** -- nothing outside the crop is drawn, the background, the symbols and the sheet clipped to it, and the view no larger than the crop and a margin -- unless `set_show_outside(True)` asks for the whole page under a veil, as before; the crop tool shows the whole page while it is used, there being nothing to crop otherwise. Its background may be a document's (`background.document`, calc/domains/plan_documents.py): the window then renders `plan_documents.render_source`, the document with its layers switched off and its pages turned. On a section the two storey tools draw into `storey_lines` and `storey_boxes` with the storey the tab has chosen (`set_storey_choice`), through the same `about_to_change`/`changed` as every other edit, and say so: `storeyLineDrawn` with the line's two points, `storeyBoxDrawn` with the box, `storeyMissing` with the tool when no storey is chosen and nothing was drawn."""

    about_to_change = Signal()
    changed = Signal()
    selection_changed = Signal()
    pointer = Signal(float, float, str)
    calibrated = Signal(list)
    tool_done = Signal()
    axes_renamed = Signal(list)
    refused = Signal(str)
    angle_dragged = Signal(float)  # a column turned by its circle, while it is dragged: the angle field follows (issue #9)
    pages_known = Signal(int)
    storeyLineDrawn = Signal(list)
    storeyBoxDrawn = Signal(dict)
    storeyMissing = Signal(str)
    clip_point = Signal(str, float, float)   # Ctrl+C's base point or Ctrl+V's point clicked (issue #61): the tab takes the clip or puts it down
    edit_refused = Signal(str)   # «Déplacer», «Copier» or a parallel aid with nothing to act on (issue #18): the tab says what to do first
    # the superposition (v0.116): shown again as the source now states it -- the module reads `superposition_state` --, and the step «Aligner» is at (1: a point of the superposed plan, 2: the matching point of this one, 0: done)
    superposition_changed = Signal()
    align_step = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.values = {}   # the export's, which a text's variables print (issue #43): the tab's, set as a drawing opens
        self.setScene(QGraphicsScene(self))
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform | QPainter.RenderHint.TextAntialiasing)
        # The wheel zooms about the pointer, which zoom_at() does itself: Qt's AnchorUnderMouse anchors on the last point its own mouseMoveEvent saw, and this view handles its moves without it -- Qt would zoom about the sheet's corner.
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        # Shown always: appearing once a plan is fitted, they made the view smaller than the one fitted -- and a plan opened twice got two scales, and found none of its renders kept.
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setBackgroundBrush(QBrush(QColor(theme.colour("desk"))))  # the desk the sheet lies on, darker in the dark scheme; the sheet itself stays paper
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.source = model.new_source("?")
        self.project_root = None
        self.here = None  # the project a document background is read from (a Project, or plan_documents.Place); None: project.current(), where it is the project at project_root
        self.background_problem = None  # why a document background could not be rendered, the plan then drawn on its file; the tab may say it
        self.show_outside = False  # the whole page under a veil, rather than the crop alone
        self.storey_choice = ""  # the storey a section's tools draw, chosen in the tab
        self.floor_of = lambda storey: model.storey_floor(storey)  # the numbering character of a storey, which its designation x1xx is made of -- the tab gives one that knows the project's other plans (v0.116)
        self.language = "de"  # the language of the engine's words the drawing carries -- a load transfer level's (v0.116); the tab sets the project's
        self.tool = "select"
        self.subtypes = {t: model.default_subtype(t) for t in model.TYPES if model.default_subtype(t)}
        self.tool_defaults = {}  # type -> what its tool's next element takes, set in the right pane while the tool is chosen (issue #9; plan.apply_defaults)
        self.snap_axes = True
        self.snap_elements = True
        self.flagged = set()
        self.selection = None  # ("element", index) or ("axis", index)
        self.drawing = []  # the points of the element or axis being drawn
        self.cursor = None  # the pointer, snapped, while drawing
        self.drag = None
        self.panning = None
        self.space_down = False
        self.propose_label = lambda type_: ""  # set by the tab: the number a new element gets
        self.ruler, self.ruler_items, self.ruler_shown = [], [], ""   # the ruler's points and what it draws: shown, kept nowhere (issue #9, D-005)
        self.unit_word = lambda: ""  # set by the tab: the sheet's unit, said by a ruler on a plan with no scale
        self.dim_points, self.dim_items, self.dim_offset_next = [], [], False   # a dimension being drawn (issue #9)
        self.show_dimensions = True   # the view «Dessin»'s own: the plan's dimensions shown, or not (the engineer's setting, plan_tab)
        self.new_element = lambda element: None  # set by the tab: what a new element takes besides its type and points -- its tool's defaults, its position's section (issue #9) -- inside the same step of «Annuler»
        self._snap_index = None
        self._label_frames = None  # where the numbers are drawn, gathered once per state of the plan
        self._over_label = False  # the pointer is over a number, and shows that it can move it
        # The tracking (v0.116): the points the pointer rested on, the newest first; the rays the cursor is locked to; the point the pointer rests on while its dwell runs; a distance being typed; a point put down by a typed distance rather than by the pointer.
        self.acquired = []
        self.locked = []
        self._hover = None
        self.typing = False
        self.typing_ray = None
        self._forced = None

        scene = self.scene()
        # What the plan draws -- the sheet, the background, the symbols, a section's storey boxes -- is the child of one invisible rectangle that clips it to the crop when the plan is shown as its crop alone (apply_view_mode); what only the editor draws over it stays outside, so a handle at the crop's edge is drawn whole.
        self.clip = QGraphicsRectItem()
        self.clip.setPen(QPen(Qt.PenStyle.NoPen))
        self.clip.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.clip.setZValue(0)
        scene.addItem(self.clip)
        self.sheet_item = QGraphicsRectItem()
        self.sheet_item.setBrush(QBrush(theme.qcolor("paper")))
        self.sheet_item.setPen(_cosmetic(theme.qcolor("plan-sheet-edge"), 1))
        self.sheet_item.setZValue(-1)
        self.sheet_item.setParentItem(self.clip)
        self.storey_items = []  # a section's storey boxes, drawn by the canvas (draw_storey_boxes)
        self.background = None
        self.background_renderer = None
        self.pages = None  # the plan's PDF, open (PdfPages)
        self.retired = []  # the PDFs of plans left, closed once nothing renders (collect)
        self.pending = None  # (path, key) of the plan's PDF, while it waits for a render on its way to come back before it is loaded
        self.pdf_file = None  # the file_key of the plan's PDF; None when its background is not a PDF
        self.pdf_page = 0
        self.opening = False  # the plan has just been opened: its first view is rendered without a margin, and kept on disk
        self.base_key = None  # the key of the whole page's render shown
        self.tile_asked = None  # the latest render of the view asked for, until it comes back
        self.tile_scale = 0.0
        self.tile = PageTile()
        self.tile.setZValue(0.5)
        self.tile.hide()
        self.tile.setParentItem(self.clip)
        self.overlay_renderer = QSvgRenderer(self)
        self.overlay = SvgLayer(self.overlay_renderer, QRectF())
        self.overlay.setZValue(10)
        self.overlay.setParentItem(self.clip)
        self.dims = []
        for _ in range(4):
            item = QGraphicsRectItem()
            item.setBrush(QBrush(theme.qcolor("plan-shade", 38)))
            item.setPen(QPen(Qt.PenStyle.NoPen))
            item.setZValue(15)
            scene.addItem(item)
            self.dims.append(item)
        self.crop_item = QGraphicsRectItem()
        self.crop_item.setPen(_cosmetic(CROP_COLOUR, 1.2, [6, 4]))
        self.crop_item.setZValue(16)
        scene.addItem(self.crop_item)
        self.select_item = QGraphicsPathItem()
        self.select_item.setPen(_cosmetic(SELECT_COLOUR, 2.2, [5, 3]))
        self.select_item.setZValue(20)
        scene.addItem(self.select_item)
        self.handles = []
        self.preview = QGraphicsPathItem()
        self.preview.setZValue(22)
        scene.addItem(self.preview)
        # the construction aids (issue #18): thin, dashed, across the whole sheet, under the symbols -- what only the editor shows
        self.aid_item = QGraphicsPathItem()
        self.aid_item.setPen(_cosmetic(plan_canvas_edit.AID_COLOUR, 1.0, [6, 4]))
        self.aid_item.setZValue(9.5)
        scene.addItem(self.aid_item)
        self.aid_pending = None    # a parallel aid's (angle, distance), between its line and its side
        self.ask_distance = None   # the tab's question for a parallel aid's distance, in sheet units: () -> float or None
        self.snap_marker = QGraphicsPathItem()
        self.snap_marker.setPen(_cosmetic(SNAP_COLOUR, 2))
        self.snap_marker.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        self.snap_marker.setZValue(23)
        scene.addItem(self.snap_marker)
        self.track_item = QGraphicsPathItem()
        self.track_item.setPen(_cosmetic(TRACK_COLOUR, 1.1, [2, 4]))
        self.track_item.setZValue(21.5)
        scene.addItem(self.track_item)
        # The superposition (v0.116): another plan of the tab shown over this one, in the other plan's own sheet units under a transform -- its background multiplied over this plan's, its symbols over that, the whole clipped to the other plan's crop and as opaque as the module says. It is no part of the plan: nothing in it is hit, selected or exported.
        self.superposition_resolver = None   # set by the module: plan id -> (source, frame), or None for a plan that is gone
        self.superposition_state = None      # None: none asked for; else {"plan", "missing", "scaled", "scale", "offset"}
        self.sup_group = QGraphicsRectItem()
        self.sup_group.setPen(QPen(Qt.PenStyle.NoPen))
        self.sup_group.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.sup_group.setFlag(QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape, True)
        self.sup_group.setZValue(SUPERPOSE_Z)
        self.sup_group.setParentItem(self.clip)
        self.sup_group.hide()
        self.sup_background = MultiplyPixmapItem()
        self.sup_background.setParentItem(self.sup_group)
        self.sup_renderer = QSvgRenderer(self)
        self.sup_elements = SvgLayer(self.sup_renderer, QRectF())
        self.sup_elements.setZValue(1)
        self.sup_elements.setParentItem(self.sup_group)
        self.sup_points = []          # the superposed plan's points, on this plan: snap targets behind «Accrocher aux éléments»
        self.sup_pages = None         # the superposed plan's PDF, where it is not this plan's
        self.sup_pending = None       # (path, key) of that PDF, waiting for a render on its way before it is loaded
        self._sup_job = None          # the render of its background asked for
        self._sup_raw = None          # (image, rect) of its background as rendered
        self._sup_bg_key = None
        self._sup_svg_key = None
        self._sup_colour = None
        self._sup_snap_off = False    # set for «Aligner»'s second click, which snaps to this plan alone
        self.align_from = None        # «Aligner»'s first click, on the superposed plan
        self.align_item = QGraphicsPathItem()
        self.align_item.setPen(_cosmetic(ALIGN_COLOUR, 1.6, [5, 3]))
        self.align_item.setZValue(22.5)
        scene.addItem(self.align_item)
        self.distance = QLineEdit(self.viewport())
        self.distance.hide()
        self.distance.setFixedWidth(110)
        self.distance.textEdited.connect(self.on_typed)
        self.distance.returnPressed.connect(self.commit_typed)
        self.acquire_timer = QTimer(self)
        self.acquire_timer.setSingleShot(True)
        self.acquire_timer.setInterval(ACQUIRE_MS)
        self.acquire_timer.timeout.connect(self.acquire)

        # the symbols are redrawn at most every few hundredths of a second while something is dragged
        self.redraw_timer = QTimer(self)
        self.redraw_timer.setSingleShot(True)
        self.redraw_timer.setInterval(30)
        self.redraw_timer.timeout.connect(self.redraw)
        # the part of the PDF in view is rendered sharp once the view stops moving
        self.sharpen_timer = QTimer(self)
        self.sharpen_timer.setSingleShot(True)
        self.sharpen_timer.setInterval(150)
        self.sharpen_timer.timeout.connect(self.sharpen)
        self.horizontalScrollBar().valueChanged.connect(self.view_moved)
        self.verticalScrollBar().valueChanged.connect(self.view_moved)
        clip_bias()  # measured now, before any render: measuring renders, and would wait for a render on its way

    # -- the plan shown --

    def frame_source(self):
        """The source the frame a plan is drawn over -- its sheet, background, crop and scale -- is read from: the plan's own. A drawing that follows another's frame (a fire plan following a position plan) answers with the frame it follows, and the canvas reads its sheet, crop and background from it all the same."""
        return self.source

    def sheet_rect(self):
        sheet = self.frame_source().get("sheet") or model.BLANK_SHEET
        return QRectF(0, 0, float(sheet["width"]), float(sheet["height"]))

    def set_source(self, source, project_root, here=None):
        """Shows `source`, its background included -- a new plan, or one read from its file. `here` is the project a document background is read from (a Project, or a plan_documents.Place); left out, the current project where it is the one at `project_root`."""
        self.source = source
        self.project_root = project_root
        if here is not None:
            self.here = here
        self.selection = None
        if self.scene() is not None:
            plan_canvas_tools.clear_ruler(self)
            plan_canvas_tools.clear_dimension_draft(self)
        self.drawing = []
        self.cursor = None
        self.reset_tracking()
        self.load_background()
        self.invalidate()
        self.fit()

    def reload_background(self, fit=True):
        """The background loaded again from the source as it stands: after the engineer switched a layer of its document off or on, or turned its page -- the source then carrying the turned sheet (plan.rotate_source), which the scene is laid out on again. `fit` fits the view to the crop, which a turned page has moved."""
        self.load_background()
        self.invalidate()
        if fit:
            self.fit()

    # -- what is shown: the crop alone, or the whole page --


    # -- the PDF: open, rendered, kept --


    # -- the superposition: another plan shown over this one (v0.116) --


    # -- «Aligner»: a point of the superposed plan on the matching point of this one --


    # -- tools --


    # -- tracking (v0.116) --


    # -- editing --


    # -- the mouse and the keys --


    # -- what only the editor shows --


