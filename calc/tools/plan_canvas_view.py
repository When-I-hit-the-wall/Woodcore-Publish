"""PlanCanvas's view -- the crop or the whole page, the background opened, rendered and kept, the superposed plan and «Aligner» -- a mixin of methods moved verbatim out of calc/tools/plan_canvas.py (issue #30). PlanCanvas names it among its bases.
"""

import json
import math
from pathlib import Path
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QObject, QPointF, QRect, QRectF, QSize, Qt, QTimer, Signal, qVersion
from PySide6.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPainterPath, QPen, QPixmap, QPixmapCache, QTransform
from PySide6.QtPdf import QPdfDocument, QPdfDocumentRenderOptions, QPdfPageRenderer
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsScene, QGraphicsSimpleTextItem, QGraphicsView, QLineEdit
import theme  # the desk around the sheet (theme.py, v0.90)
import plan_canvas_tools  # the circle a column is turned by, and the ruler (issue #9)
import usersettings  # where Woodcore keeps its caches (usersettings.py)
from domains import plan as model
from domains import plan_documents
from domains import plan_svg
from domains import plan_tracking as tracking
import plan_canvas_edit  # «Déplacer», «Copier» and «Ligne d'aide» (issue #18)
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


# A PDF page is rendered twice over, the part in view first. The part in view at the screen's own resolution, each time the view stops: the architect's lines are then as sharp as a PDF viewer shows them at every zoom, and no render is ever much larger than the screen. And the whole page, this many pixels along its longer side: what shows while the view moves, and wherever nothing sharper has come yet. The time a render takes grows faster than its pixels: an architect's sheet dense with hatching took 3.5 to 8 s at 2500 px, and takes about 1 s at 1200.
BASE_RENDER_PX = 1200


# Once the view has moved, the part in view is rendered with this much of the view's size beyond each edge, so that a short pan stays sharp -- within TILE_MAX_PX pixels, 64 MB. The first view of a plan just opened has no margin: it is the render waited for, and the smallest is the quickest.
TILE_MARGIN = 0.25


TILE_MAX_PX = 16_000_000


# The renders kept, so that a page seen before shows at once: in memory for the session, up to this many bytes; and on disk, the whole page and the first view of each page, in the user's local profile -- outside the project, which a cloud folder syncs.
MEMORY_CACHE_BYTES = 256 * 2**20


DISK_CACHE_BYTES = 300 * 2**20


DISK_CACHE_DIR = usersettings.cache_dir("renders")   # %LOCALAPPDATA%\Woodcore\renders, typst-katalog\renders until v0.83


# A section's storeys (v0.114): its lines are the overlay's (plan_svg), its boxes the canvas's own -- a translucent red over a dashed red outline, the storey written inside, as STE Compact 02 p. 12 marks the storey a floor plan is.
STOREY_COLOUR = theme.qcolor("plan-storey")


STOREY_FILL = theme.qcolor("plan-storey", 46)


# Around a plan shown as its crop alone, this much of the crop's longer side: the view's room to breathe.
CROP_MARGIN = 0.04


# The superposition (v0.116, the «Superposition» module): another plan of the same tab shown over this one, a drawing aid never printed. Its background is rendered once, its crop this many pixels along its longer side, and kept as every render is; it stands above this plan's own background and under this plan's own symbols (SUPERPOSE_Z), so what is drawn is drawn on top of it. «Aligner» is a tool of its own, two clicks: a point of the superposed plan, then the matching point of this one.
SUPERPOSE_RENDER_PX = 2000


RENDERS = RenderCache(MEMORY_CACHE_BYTES)


DISK = DiskCache(DISK_CACHE_DIR, DISK_CACHE_BYTES)


def _round(value):
    """A coordinate as it is saved: to a hundredth of a sheet unit, which is far below what a click can place."""
    value = round(float(value), 2) + 0.0
    return int(value) if value.is_integer() else value


class PlanCanvasViewMixin:
    """Methods of plan_canvas.PlanCanvas, moved verbatim (issue #30): the class names this mixin among its bases."""

    def clipped(self):
        """Whether only the crop is shown: always, but where the whole page is asked for (set_show_outside) or the crop tool is in use -- a crop is drawn on the page around it."""
        return not (self.show_outside or self.tool == "crop")

    def crop_rect(self):
        crop = model.crop_of(self.frame_source())
        return QRectF(crop["x"], crop["y"], crop["w"], crop["h"])

    def shown_rect(self):
        """The part of the sheet the plan shows: its crop where only the crop is shown, else the whole sheet."""
        sheet = self.sheet_rect()
        if not self.clipped():
            return sheet
        area = self.crop_rect().intersected(sheet)
        return area if not area.isEmpty() else self.crop_rect()

    def set_show_outside(self, show):
        """Shows the whole page, what lies outside the crop under a veil (True), or the crop alone (False, the default), and fits the view to the crop."""
        show = bool(show)
        if show == self.show_outside:
            return
        self.show_outside = show
        self.apply_view_mode()
        self.fit()

    def apply_view_mode(self):
        """Lays the scene out for what is shown: the drawing clipped to the crop and the scene no larger than the crop and a margin, no veil; or the whole sheet, the scene a third larger, the veils over what lies outside the crop."""
        sheet = self.sheet_rect()
        crop = self.crop_rect()
        clipped = self.clipped()
        if clipped:
            area = self.shown_rect()
            self.clip.setRect(area)
            margin = CROP_MARGIN * max(area.width(), area.height())
            scene_rect = area.adjusted(-margin, -margin, margin, margin)
        else:
            self.clip.setRect(sheet)
            margin = 0.35 * max(sheet.width(), sheet.height())
            scene_rect = sheet.adjusted(-margin, -margin, margin, margin)
        self.clip.setFlag(QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape, clipped)
        if scene_rect != self.sceneRect():
            self.setSceneRect(scene_rect)
        outer = self.sceneRect()
        self.dims[0].setRect(QRectF(outer.left(), outer.top(), outer.width(), crop.top() - outer.top()))
        self.dims[1].setRect(QRectF(outer.left(), crop.bottom(), outer.width(), outer.bottom() - crop.bottom()))
        self.dims[2].setRect(QRectF(outer.left(), crop.top(), crop.left() - outer.left(), crop.height()))
        self.dims[3].setRect(QRectF(crop.right(), crop.top(), outer.right() - crop.right(), crop.height()))
        for item in self.dims:
            item.setVisible(not clipped)

    def background_file(self):
        """(path, format, page) the background is rendered from, or None: for a plan drawn on a document, what plan_documents.render_source gives -- the document with its layers switched off and its pages turned, page numbers unchanged --, else the source's own file. A document that cannot be read or rendered falls back on the file, `background_problem` saying why."""
        self.background_problem = None
        try:
            return self.background_of(self.frame_source())
        except BackgroundFallback as fallback:
            self.background_problem = fallback.error
            return fallback.found

    def background_of(self, frame):
        """(path, format, page) the background of `frame` -- this plan's, or a superposed plan's (v0.116) -- is rendered from, or None; a document that cannot be rendered raises BackgroundFallback carrying why and the file to fall back on."""
        spec = frame.get("background")
        if not spec or self.project_root is None:
            return None
        page = int(spec.get("page", 1))
        docid = spec.get("document")
        problem = None
        if docid:
            try:
                here = self.document_place()
                doc = plan_documents.read(here, docid)
                path = Path(plan_documents.render_source(here, doc, page))
                return path, model.background_format(path), page if doc["kind"] == "pdf" else 1
            except Exception as error:  # broad: a layout ezdxf cannot draw is not a ValidationError: the plan is drawn on its file all the same, and the tab says why
                problem = error
        found = None
        file = spec.get("file")
        path = model.background_path(self.project_root, file) if file else None
        if path is not None and Path(path).is_file():
            found = (Path(path), model.background_format(path), page)
        if problem is not None:
            raise BackgroundFallback(problem, found)
        return found

    def document_place(self):
        """Where a document background is read from: the project the tab named, else the current one where it lies at project_root, else the project_root with the plans folder a project is laid out with by default."""
        if self.here is not None:
            return self.here
        import project
        root = Path(self.project_root).resolve()
        try:
            current = project.current()
            if Path(current.root).resolve() == root:
                return current
        except project.ProjectError:   # no project open: the plan's own folder
            pass
        return plan_documents.Place(root, root / project.DEFAULT_LAYOUT["sources"] / "plans")

    def load_background(self):
        """(Re)loads the source's background. A PDF page shows at once from a render kept of it, when there is one, and is otherwise rendered in QtPdf's thread, the part in view first and then the whole page; an image or an SVG shows at once. A file that cannot be found leaves the sheet empty -- the tab says why."""
        scene = self.scene()
        if self.background is not None:
            scene.removeItem(self.background)
        self.background = None
        self.background_renderer = None
        if self.pages is not None:
            # the previous plan's renders not yet on their way are not wanted any more; the one on its way is kept (on_rendered)
            self.pages.drop()
        self._sup_bg_key = None   # a superposition's render waiting on that PDF went with them: asked again (sync_superposition)
        self.pending = None
        self.pdf_file = None
        self.pdf_page = 0
        self.opening = False
        self.base_key = None
        self.tile_asked = None
        self.tile_scale = 0.0
        self.tile.hide()
        self.tile.set_pixmap(QPixmap(), QRectF())
        rect = self.sheet_rect()
        self.sheet_item.setRect(rect)
        self.apply_view_mode()
        found = self.background_file()
        if found is None:
            return
        path, fmt, page = found
        if fmt == "pdf":
            try:
                key = file_key(path)
            except OSError:
                return
            self.pdf_file = key
            self.pdf_page = page - 1
            self.opening = True
            self.use_pdf(path, key)
            self.request_base(ask=False)  # what is kept of it shows at once
            # what is rendered is asked for as soon as the tab has set the view (fit), without the pause that follows a move
            QTimer.singleShot(0, self, self.first_view)
        elif fmt in ("png", "jpg"):
            pixmap = QPixmap(str(path))
            if pixmap.isNull():
                return
            item = QGraphicsPixmapItem(pixmap)
            item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
            item.setTransform(QTransform.fromScale(rect.width() / pixmap.width(), rect.height() / pixmap.height()))
            self.background = item
        elif fmt == "svg":
            self.background_renderer = QSvgRenderer(str(path), self)
            self.background = SvgLayer(self.background_renderer, rect)
        if self.background is not None:
            self.background.setZValue(0)
            self.background.setParentItem(self.clip)

    def use_pdf(self, path, key):
        """Makes the PDF `key` the one the plan is rendered from: the one open already when it is the same file -- another page of a plan set, another plan drawn on it --, one left a moment ago and not closed yet, or a new one. A new one is loaded at once unless a render is on its way, which the load would wait for: it is then loaded when that render has come back (collect), the plan showing meanwhile whatever is kept of it."""
        if self.pages is not None and self.pages.key == key:
            self.pages_known.emit(self.pages.page_count())
            return
        revived = next((old for old in self.retired if old.key == key), None)
        if self.pages is not None:
            self.pages.drop()
            self.retired.append(self.pages)
            self.pages = None
        if revived is not None:
            self.retired.remove(revived)
            self.pages = revived
            self.pages_known.emit(self.pages.page_count())
        elif self.busy():
            self.pending = (path, key)
        else:
            self.collect()
            self.open_pdf(path, key)

    def open_pdf(self, path, key):
        self.pages = PdfPages(path, key, self)
        self.pages.rendered.connect(self.on_rendered)
        self.pages_known.emit(self.pages.page_count())

    def busy(self):
        """Whether a render is on its way, from any PDF this canvas has open."""
        return any(p.busy is not None for p in (self.pages, self.sup_pages, *self.retired) if p is not None)

    def collect(self):
        """Closes the PDFs of plans left and loads the one waiting -- only while nothing renders: a render on its way would hold up either (PdfPages)."""
        if self.busy():
            return
        for old in self.retired:
            old.close()
        self.retired = []
        if self.pending is not None:
            path, key = self.pending
            self.pending = None
            if key == self.pdf_file and self.pages is None:
                self.open_pdf(path, key)
                self.first_view()
        if self.sup_pending is not None:
            path, key = self.sup_pending
            self.sup_pending = None
            self.open_superposition_pdf(path, key)

    def first_view(self):
        """The renders of a plan just opened, asked for in the order QtPdf is to render them: the view, then the whole page."""
        self.sharpen()
        self.request_base()

    def page_count(self):
        """The pages of the plan's PDF, or None while it waits to be loaded (pages_known says when it is)."""
        if self.pages is not None and self.pages.key == self.pdf_file:
            return self.pages.page_count()
        return None

    def request_base(self, ask=True):
        """The whole PDF page, BASE_RENDER_PX along its longer side: shown at once when a render of it is kept, in memory or on disk, and otherwise asked for -- unless `ask` is false."""
        if self.pdf_file is None:
            return
        rect = self.sheet_rect()
        scale = BASE_RENDER_PX / max(rect.width(), rect.height())
        size = QSize(max(1, round(rect.width() * scale)), max(1, round(rect.height() * scale)))
        key = ("base", self.pdf_file, self.pdf_page, size.width(), size.height())
        if key == self.base_key:
            return
        kept = RENDERS.get(key)
        if kept is None:
            image = DISK.load(key, size)
            if image is not None:
                RENDERS.put(key, image, rect, scale)
                kept = RENDERS.get(key)
        if kept is not None:
            self.base_key = key
            self.show_base(kept.image)
        elif ask and self.pages is not None:
            self.pages.ask(RenderJob("base", key, size, QPdfDocumentRenderOptions(), rect, scale, disk=True))

    def on_rendered(self, job, image):
        """A render has come back: it is kept, and shown if it is of the page shown. One of a plan left in the meantime is kept all the same: going back to that plan shows it at once."""
        if job.kind == "superpose":
            self.on_superposition_rendered(job, image)
            if self.retired or self.pending or self.sup_pending:
                QTimer.singleShot(0, self, self.collect)
            return
        if job is self.tile_asked:
            self.tile_asked = None
        if not image.isNull():
            image = image.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
            RENDERS.put(job.key, image, job.rect, job.scale)
            if job.disk:
                DISK.save(job.key, image)
            if job.file == self.pdf_file and job.page == self.pdf_page:
                if job.kind == "tile":
                    self.show_tile(image, job.rect, job.scale)
                else:
                    self.base_key = job.key
                    self.show_base(image)
        if self.retired or self.pending or self.sup_pending:
            # not now: this runs inside the signal of a PDF that collect may close
            QTimer.singleShot(0, self, self.collect)

    def show_base(self, image):
        rect = self.sheet_rect()
        pixmap = QPixmap.fromImage(image)
        if isinstance(self.background, QGraphicsPixmapItem):
            self.background.setPixmap(pixmap)
        else:
            if self.background is not None:
                self.scene().removeItem(self.background)
            self.background = QGraphicsPixmapItem(pixmap)
            self.background.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
            self.background.setZValue(0)
            self.background.setParentItem(self.clip)
        self.background.setTransform(QTransform.fromScale(rect.width() / pixmap.width(), rect.height() / pixmap.height()))
        self.update_base_visibility()

    def show_tile(self, image, rect, scale):
        self.tile.set_pixmap(QPixmap.fromImage(image), rect)
        self.tile_scale = scale
        self.tile.show()
        self.update_base_visibility()

    def visible_rect(self):
        """The part of the scene the view shows."""
        return self.mapToScene(self.viewport().rect()).boundingRect()

    def sharpen(self):
        """Shows the part of the PDF page in view at the screen's own resolution, and a margin round it once the view has moved: from a render kept of it, in memory or on disk, when there is one at this scale, and otherwise asked for -- PdfPages sends one render at a time, and the newest view takes the place of one still waiting. Until it comes, a plan just opened shows the render kept nearest to it, a little soft. The first view of a plan just opened has no margin, and is kept on disk."""
        if self.pdf_file is None or not self.isVisible():
            return  # a hidden tab's view is not yet the one it will show (showEvent)
        sheet = self.sheet_rect()
        view = self.visible_rect()
        seen = view.intersected(self.shown_rect())  # where only the crop is shown, only the crop is rendered
        if seen.isEmpty():
            return
        scale = self.transform().m11() * self.viewport().devicePixelRatioF()  # screen pixels per sheet unit
        if self.tile.isVisible() and same_scale(self.tile_scale, scale) and covers(self.tile.rect, seen, scale):
            return
        asked = self.tile_asked
        if asked is not None and same_scale(asked.scale, scale) and covers(asked.rect, seen, scale):
            return  # on its way
        kept, exact = self.kept_tile(sheet, seen, scale)
        if exact:
            self.opening = False
            self.show_tile(*kept)
            return
        job = self.tile_job(sheet, view, seen, scale)
        if job is None:
            return  # a screen larger than TILE_MAX_PX: the whole page's render stays
        if kept is not None and not self.tile.isVisible():
            self.show_tile(*kept)  # meanwhile
        if self.pages is None:
            return  # the PDF waits for a render on its way to come back before it is loaded (collect)
        self.opening = False
        self.tile_asked = job
        self.pages.ask(job)

    def kept_tile(self, sheet, seen, scale):
        """((image, rect, scale), exact) of the render kept of this page, in memory or on disk, that best shows `seen`: one at this scale that covers it (exact), or else the one covering most of it at the scale nearest this one, within half and twice it; (None, False) when none does. Of two alike, the one in memory, which needs no reading."""
        candidates = [(key, kept.rect, kept.scale, kept) for key, kept in RENDERS.tiles(self.pdf_file, self.pdf_page)]
        candidates += [(key, *tile_geometry(key, sheet), path) for key, path in DISK.tiles(self.pdf_file, self.pdf_page) if key not in RENDERS.items]
        best, best_score = None, None
        for index, (key, rect, s, where) in enumerate(candidates):
            exact = same_scale(s, scale) and covers(rect, seen, scale)
            ratio = s / scale
            common = rect.intersected(seen)
            if not exact and (not 0.5 <= ratio <= 2 or common.isEmpty()):
                continue
            share = round(20 * common.width() * common.height() / max(seen.width() * seen.height(), 1e-9))
            score = (exact, share, -abs(math.log(ratio)), -index)
            if best_score is None or score > best_score:
                best, best_score = (key, rect, s, where), score
        if best is None:
            return None, False
        key, rect, s, where = best
        if isinstance(where, Path):
            image = DISK.load(key, QSize(key[7], key[8]), where)
            if image is None:
                return None, False
            RENDERS.put(key, image, rect, s)
        else:
            RENDERS.get(key)
            image = where.image
        return (image, rect, s), best_score[0]

    def tile_job(self, sheet, view, seen, scale):
        """The render of the part of the page in view: the whole page at `scale`, of which only that part is rendered -- with a margin round it, but for the first view of a plan just opened."""
        width, height = max(1, round(sheet.width() * scale)), max(1, round(sheet.height() * scale))
        sx, sy = width / sheet.width(), height / sheet.height()
        for margin in ((0.0,) if self.opening else (TILE_MARGIN, 0.0)):
            mx, my = view.width() * margin, view.height() * margin
            want = seen.adjusted(-mx, -my, mx, my).intersected(self.shown_rect())
            x0, y0 = max(0, math.floor(want.left() * sx)), max(0, math.floor(want.top() * sy))
            x1, y1 = min(width, math.ceil(want.right() * sx)), min(height, math.ceil(want.bottom() * sy))
            if 0 < (x1 - x0) * (y1 - y0) <= TILE_MAX_PX:
                break
        else:
            return None
        options = QPdfDocumentRenderOptions()
        options.setScaledSize(QSize(width, height))
        bias = clip_bias()
        options.setScaledClipRect(QRect(x0, y0, x1 - x0 + bias, y1 - y0 + bias))
        key = ("tile", self.pdf_file, self.pdf_page, width, height, x0, y0, x1 - x0, y1 - y0)
        rect = QRectF(x0 / sx, y0 / sy, (x1 - x0) / sx, (y1 - y0) / sy)
        return RenderJob("tile", key, QSize(x1 - x0, y1 - y0), options, rect, scale, disk=self.opening)

    def update_base_visibility(self):
        """The whole page's render is hidden while the sharp one covers the view: drawn under it, it would only cost time on every repaint."""
        if self.pdf_file is None or self.background is None:
            return
        seen = self.visible_rect().intersected(self.shown_rect())
        scale = self.transform().m11() * self.viewport().devicePixelRatioF()
        self.background.setVisible(not (self.tile.isVisible() and covers(self.tile.rect, seen, scale)))

    def view_moved(self, *_args):
        """After a zoom, a pan or a resize: the whole page shows where the sharp render no longer reaches, and a new one is asked for once the view stops."""
        self.update_base_visibility()
        self.sharpen_timer.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_if_pending()
        self.view_moved()

    def showEvent(self, event):
        super().showEvent(event)
        self.fit_if_pending()
        self.view_moved()

    def fit_if_pending(self):
        """A fit asked for while the view was hidden -- a plan opened behind the document view, or before the window was laid out -- done now that the view has its size: fitted then, the crop came out a postage stamp in the middle of the view."""
        if getattr(self, "fit_pending", False) and self.isVisible() and self.viewport().width() > 40 and self.viewport().height() > 40:
            self.fit_pending = False
            self.fit()

    def invalidate(self):
        """After any change to the source: the snapping targets and the numbers' places are gathered again and the symbols redrawn."""
        self._snap_index = None
        self._label_frames = None
        self.sync_superposition()   # the plan shown over this one, where the source asks for one (v0.116)
        self.redraw()

    def redraw(self):
        sheet = self.sheet_rect()
        window = {"x": 0.0, "y": 0.0, "w": sheet.width(), "h": sheet.height()}
        svg = plan_svg.render(self.drawn_source(), window, flagged=self.flagged, lang=self.language, values=self.values)
        self.overlay_renderer.load(QByteArray(svg.encode("utf-8")))
        self.overlay.set_rect(sheet)
        self.crop_item.setRect(self.crop_rect())
        self.apply_view_mode()  # the crop may have moved
        self.draw_storey_boxes()
        self.aid_item.setPath(plan_canvas_edit.aids_path(self.source, window))
        self.update_helpers()

    def draw_storey_boxes(self):
        """A section's storey boxes, whose outline the overlay does not draw (the report draws the one a sheet highlights): each a translucent red rectangle with a dashed red outline. Its STE designation, x1xx, is the overlay's, at its middle (plan_svg._storey_boxes, v0.116) -- no storey written in its corner any more."""
        scene = self.scene()
        for item in self.storey_items:
            scene.removeItem(item)
        self.storey_items = []
        for box in self.source.get("storey_boxes") or []:
            try:
                rect = QRectF(float(box["x"]), float(box["y"]), float(box["w"]), float(box["h"])).normalized()
            except (KeyError, TypeError, ValueError):
                continue
            item = QGraphicsRectItem(rect)
            item.setBrush(QBrush(STOREY_FILL))
            item.setPen(_cosmetic(STOREY_COLOUR, 1.4, [6, 3]))
            item.setZValue(9)  # under the overlay, which writes the designation over it
            item.setParentItem(self.clip)
            self.storey_items.append(item)

    def drawn_source(self):
        """The source as it is drawn: the element being dragged is already in it, since a drag edits in place -- and its dimensions left out where the view «Dessin» is set not to show them (issue #9, REQ-011), unless a dimension is being drawn or one is selected."""
        if self.show_dimensions or not self.source.get("dimensions") or plan_canvas_tools.is_dimension_tool(self.tool)                 or (self.selection and self.selection[0] == "dimension"):
            return self.source
        return {**self.source, "dimensions": []}

    def fit(self):
        """The crop in the view, and a margin round it -- or, while the crop tool shows the whole page, the whole page."""
        if not self.isVisible() or self.viewport().width() <= 40 or self.viewport().height() <= 40:
            self.fit_pending = True   # done again on the next show or resize, once the view has a size to fit into
        rect = self.sheet_rect() if self.tool == "crop" else self.crop_rect()
        margin = CROP_MARGIN * max(rect.width(), rect.height())
        self.fitInView(rect.adjusted(-margin, -margin, margin, margin), Qt.AspectRatioMode.KeepAspectRatio)
        self.view_moved()

    def sync_superposition(self):
        """The plan the source's `superposition` names, shown over this one as it states -- at its offset and scale (plan.superposition_transform), its opacity, its colour, with or without its elements -- or nothing, where it names none or one that is gone (`superposition_state` says which, the module reads it). Its background is rendered again only when its frame changed, its symbols only when they did: this runs at every change of the source."""
        spec = model.superposition_of(self.source)
        found = None
        if spec is not None and self.superposition_resolver is not None:
            try:
                found = self.superposition_resolver(spec["plan"])
            except Exception:   # broad: a file half written, a frame that cannot be read: nothing is shown, the plan open is not stopped for it
                found = None
        self.sup_points = []
        if spec is None or found is None:
            self.superposition_state = None if spec is None else {"plan": spec["plan"], "missing": True}
            self.sup_group.hide()
            self.superposition_changed.emit()
            return
        other, frame = found
        s, dx, dy = model.superposition_transform(spec, self.frame_source(), frame)
        _s, scaled = model.superposition_scale(self.frame_source(), frame)
        crop = model.crop_of(frame)
        self.sup_group.setRect(QRectF(crop["x"], crop["y"], crop["w"], crop["h"]))
        self.sup_group.setTransform(QTransform(s, 0, 0, s, dx, dy))
        self.sup_group.setOpacity(float(spec.get("opacity", 0.5)))
        self.sup_group.show()
        colour = spec.get("colour", "normal")
        background_key = json.dumps([frame.get("background"), frame.get("sheet"), crop], sort_keys=True, default=str)
        if background_key != self._sup_bg_key:
            self._sup_bg_key = background_key
            self._sup_colour = None
            self.load_superposition_background(frame)
        if colour != self._sup_colour:
            self._sup_colour = colour
            self.apply_superposition_image()
        if spec.get("elements", True):
            ink = model.SUPERPOSITION_INKS.get(colour) if spec.get("tint_elements") else None
            svg_key = json.dumps([other, frame, self.language, ink], sort_keys=True, default=str)
            if svg_key != self._sup_svg_key:
                self._sup_svg_key = svg_key
                svg = self.superposition_svg(other, frame)
                if ink:
                    svg = tint_svg(svg, ink)
                self.sup_renderer.load(QByteArray(svg.encode("utf-8")))
                sheet = frame.get("sheet") or model.BLANK_SHEET
                self.sup_elements.set_rect(QRectF(0, 0, float(sheet["width"]), float(sheet["height"])))
            self.sup_elements.show()
            x0, y0, x1, y1 = crop["x"], crop["y"], crop["x"] + crop["w"], crop["y"] + crop["h"]
            for qx, qy in self.superposition_points(other, frame):
                if x0 - 1e-6 <= qx <= x1 + 1e-6 and y0 - 1e-6 <= qy <= y1 + 1e-6:
                    self.sup_points.append((s * qx + dx, s * qy + dy))
        else:
            self.sup_elements.hide()
        self.superposition_state = {"plan": spec["plan"], "missing": False, "scaled": scaled, "scale": s, "offset": [dx, dy]}
        self.superposition_changed.emit()

    def superposition_svg(self, other, frame):
        """The superposed plan's symbols as an SVG over its whole sheet: plan_svg's, without the veil a background would have them drawn over. The fire-protection plan's canvas draws its own (FireCanvas)."""
        drawn = {key: value for key, value in other.items() if key != "background"}
        sheet = frame.get("sheet") or model.BLANK_SHEET
        window = {"x": 0.0, "y": 0.0, "w": float(sheet["width"]), "h": float(sheet["height"])}
        return plan_svg.render(drawn, window, lang=self.language)

    def superposition_points(self, other, frame):
        """The superposed plan's points, in its own sheet units: what a point drawn here may snap to and «Aligner» may take. A position plan's elements' corners; a fire-protection plan's entries' (FireCanvas)."""
        return [(float(p[0]), float(p[1])) for element in other.get("elements") or [] for p in element.get("points") or []]

    def superposition_snap_points(self):
        """The superposed plan's points as snap targets -- behind «Accrocher aux éléments», as this plan's own are, and never for «Aligner»'s second click, which takes a point of this plan."""
        if self._sup_snap_off or not self.snap_elements or not self.sup_group.isVisible():
            return []
        return list(self.sup_points)

    def load_level_points(self, exclude_storey=None):
        """The two ends of every load transfer level of a section, snap points as a storey line's are (v0.116) -- but those of the one being dragged, `exclude_storey` ("load-level", index)."""
        out = []
        for i, level in enumerate(self.source.get("load_levels") or []):
            if exclude_storey == ("load-level", i):
                continue
            for p in level.get("points") or []:
                try:
                    out.append((float(p[0]), float(p[1])))
                except (TypeError, ValueError, IndexError):
                    continue
        return out

    def load_superposition_background(self, frame):
        """The superposed plan's background, its crop rendered SUPERPOSE_RENDER_PX along its longer side: shown at once from a render kept of it, else asked of its PDF (PdfPages, one render at a time as every render here) -- an image or an SVG is read at once. A background that cannot be found shows nothing: the symbols are shown all the same."""
        self._sup_raw = None
        self._sup_job = None
        self.sup_background.set_pixmap(QPixmap(), QRectF())
        try:
            found = self.background_of(frame)
        except BackgroundFallback as fallback:
            found = fallback.found
        except Exception:   # broad: a frame that cannot be drawn shows no superposition, the plan open is not stopped for it
            found = None
        if found is None:
            return
        path, fmt, page = found
        crop = model.crop_of(frame)
        sheet = frame.get("sheet") or model.BLANK_SHEET
        sw, sh = float(sheet["width"]), float(sheet["height"])
        rect = QRectF(crop["x"], crop["y"], crop["w"], crop["h"]).intersected(QRectF(0, 0, sw, sh))
        if rect.isEmpty():
            return
        scale = SUPERPOSE_RENDER_PX / max(rect.width(), rect.height())
        if fmt == "pdf":
            try:
                key = file_key(path)
            except OSError:
                return
            width, height = max(1, round(sw * scale)), max(1, round(sh * scale))
            sx, sy = width / sw, height / sh
            x0, y0 = max(0, math.floor(rect.left() * sx)), max(0, math.floor(rect.top() * sy))
            x1, y1 = min(width, math.ceil(rect.right() * sx)), min(height, math.ceil(rect.bottom() * sy))
            if not 0 < (x1 - x0) * (y1 - y0) <= TILE_MAX_PX:
                return
            options = QPdfDocumentRenderOptions()
            options.setScaledSize(QSize(width, height))
            options.setScaledClipRect(QRect(x0, y0, x1 - x0 + clip_bias(), y1 - y0 + clip_bias()))
            job_key = ("tile", key, page - 1, width, height, x0, y0, x1 - x0, y1 - y0)
            job_rect = QRectF(x0 / sx, y0 / sy, (x1 - x0) / sx, (y1 - y0) / sy)
            kept = RENDERS.get(job_key)
            if kept is None:
                image = DISK.load(job_key, QSize(x1 - x0, y1 - y0))
                if image is not None:
                    RENDERS.put(job_key, image, job_rect, scale)
                    kept = RENDERS.get(job_key)
            if kept is not None:
                self._sup_raw = (kept.image, job_rect)
                return
            self._sup_job = RenderJob("superpose", job_key, QSize(x1 - x0, y1 - y0), options, job_rect, scale, disk=True)
            pages = self.superposition_pdf(path, key)
            if pages is not None:
                pages.ask(self._sup_job)
        elif fmt in ("png", "jpg"):
            image = QImage(str(path))
            if image.isNull():
                return
            ix, iy = image.width() / sw, image.height() / sh
            part = QRect(math.floor(rect.left() * ix), math.floor(rect.top() * iy), max(1, math.ceil(rect.width() * ix)), max(1, math.ceil(rect.height() * iy)))
            self._sup_raw = (image.copy(part), QRectF(part.x() / ix, part.y() / iy, part.width() / ix, part.height() / iy))
        elif fmt == "svg":
            renderer = QSvgRenderer(str(path))
            if not renderer.isValid():
                return
            image = QImage(max(1, round(rect.width() * scale)), max(1, round(rect.height() * scale)), QImage.Format.Format_ARGB32_Premultiplied)
            image.fill(QColor(0, 0, 0, 0))
            painter = QPainter(image)
            renderer.render(painter, QRectF(-rect.left() * scale, -rect.top() * scale, sw * scale, sh * scale))
            painter.end()
            self._sup_raw = (image, rect)

    def superposition_pdf(self, path, key):
        """The PdfPages the superposed plan's background is asked of: this plan's own where it is the same file, else one of its own -- loaded only while nothing renders (collect), as this plan's is."""
        if self.pages is not None and self.pages.key == key:
            return self.pages
        if self.sup_pages is not None and self.sup_pages.key == key:
            return self.sup_pages
        if self.sup_pages is not None:
            self.sup_pages.drop()
            self.retired.append(self.sup_pages)
            self.sup_pages = None
        revived = next((old for old in self.retired if old.key == key), None)
        if revived is not None:
            self.retired.remove(revived)
            self.sup_pages = revived
            return revived
        if self.busy():
            self.sup_pending = (path, key)
            return None
        self.open_superposition_pdf(path, key)
        return self.sup_pages

    def open_superposition_pdf(self, path, key):
        self.sup_pages = PdfPages(path, key, self)
        self.sup_pages.rendered.connect(self.on_rendered)
        if self._sup_job is not None and self._sup_job.file == key:
            self.sup_pages.ask(self._sup_job)

    def on_superposition_rendered(self, job, image):
        """The superposed plan's background has come back: kept as every render is, and shown where it is still the one asked for."""
        if image.isNull():
            return
        image = image.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
        RENDERS.put(job.key, image, job.rect, job.scale)
        if job.disk:
            DISK.save(job.key, image)
        if self._sup_job is not None and job.key == self._sup_job.key:
            self._sup_job = None
            self._sup_raw = (image, job.rect)
            self.apply_superposition_image()

    def apply_superposition_image(self):
        """The superposed plan's background in the colour the superposition is shown in: as it is, or grey or one of the five colours (tint_image), multiplied over this plan's (MultiplyPixmapItem)."""
        if self._sup_raw is None:
            self.sup_background.set_pixmap(QPixmap(), QRectF())
            return
        image, rect = self._sup_raw
        ink = model.SUPERPOSITION_INKS.get(self._sup_colour or "normal")
        self.sup_background.set_pixmap(QPixmap.fromImage(tint_image(image, ink)), rect)

    def align_point(self, raw):
        """(point, kind) a click of «Aligner» takes: on the superposed plan's points for the first, on this plan's own for the second."""
        if self.align_from is None:
            index = tracking.PlanSnapIndex({}, model.crop_of(self.frame_source()), axes=False, elements=False, extra_points=self.sup_points)
            return index.snap(raw, self.tolerance())
        self._sup_snap_off = True
        try:
            return self.snapped(raw)
        finally:
            self._sup_snap_off = False

    def align_click(self, raw):
        """A click of «Aligner»: the first takes a point of the superposed plan, the second the point of this plan it is to lie on -- and the superposition's offset moves by the difference, one step of «Annuler»."""
        state = self.superposition_state
        if not state or state.get("missing") or not isinstance(self.source.get("superposition"), dict):
            self.tool_done.emit()
            return
        p, _kind = self.align_point(raw)
        if self.align_from is None:
            self.align_from = (float(p[0]), float(p[1]))
            self.align_step.emit(2)
            self.update_align()
            return
        a, self.align_from = self.align_from, None
        dx, dy = state["offset"]
        self.begin_change()
        self.source["superposition"]["offset"] = [_round(dx + p[0] - a[0]), _round(dy + p[1] - a[1])]
        self.end_change()
        self.update_align()
        self.align_step.emit(0)
        self.tool_done.emit()

    def update_align(self):
        """«Aligner»'s line, from the point of the superposed plan taken to the pointer, and a ring on that point."""
        path = QPainterPath()
        if self.align_from is not None:
            unit = 1.0 / max(self.transform().m11(), 1e-9)
            a = QPointF(*self.align_from)
            path.addEllipse(a, 6.0 * unit, 6.0 * unit)
            if self.cursor is not None:
                path.moveTo(a)
                path.lineTo(QPointF(*self.cursor))
        self.align_item.setPath(path)
