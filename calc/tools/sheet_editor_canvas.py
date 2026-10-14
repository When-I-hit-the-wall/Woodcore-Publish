"""The page of an export sheet as the editor shows it, its objects drawn over the compiled page to be chosen, moved and resized -- split out of calc/tools/sheet_editor.py (issue #30), moved verbatim. sheet_editor.py imports every name back.
"""

from PySide6.QtCore import QBuffer, QByteArray, QFileSystemWatcher, QIODevice, QObject, QPointF, QRect, QRectF, QSize, QThread, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtPdf import QPdfDocument, QPdfDocumentRenderOptions, QPdfPageRenderer
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QMessageBox,
                               QPlainTextEdit, QPushButton, QScrollArea, QToolButton, QVBoxLayout, QWidget)
import flowbar
import theme
from sheet_editor_words import BUNDLE_KEYS, STRINGS, bundle_words, words  # split out of this module (issue #30): every name it had is still importable from it
from sheet_editor_render import (  # split out of this module (issue #30): every name it had is still importable from it
    BOX_LABEL,
    BOX_QUERY,
    Box,
    COMPILE_TIMEOUT_S,
    Compiler,
    DEBOUNCE_MS,
    DRAWING_KINDS,
    LEGEND_KINDS,
    RESIZABLE_KINDS,
    SNAP_MM,
    TITLE_MM,
    _Job,
    _RUNNING,
    _count_positions,
    _objects,
    _position,
    cache_target,
    drawing_width,
    estimate_boxes,
    file_signature,
    markup_of,
    match_boxes,
    parse_boxes,
    parse_scale,
    query_args,
    read_fire_plans,
    read_plans,
    render,
    scale_for,
    snap,
    units_per_m,
)


# How far apart the pixels of the zoom steps are, and its bounds, in pixels per millimetre.
ZOOM_STEP = 1.25


ZOOM_MIN, ZOOM_MAX = 0.3, 25.0


# The white round the page in the canvas, in pixels.
PAD = 16


# The side of a resize handle, in pixels.
HANDLE = 9


class _Page(QWidget):
    """The paper, drawn at the canvas's zoom: the compiled page, and over it a frame round every object -- the one chosen in the accent with its resize handle."""

    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

    # millimetres <-> pixels
    def to_px(self, x, y):
        s = self.canvas.ppm
        return PAD + x * s, PAD + y * s

    def to_mm(self, point):
        s = self.canvas.ppm
        return (point.x() - PAD) / s, (point.y() - PAD) / s

    def rect_of(self, box, dx=0.0, dy=0.0, factor=1.0):
        x, y = self.to_px(box.x + dx, box.y + dy)
        s = self.canvas.ppm
        return QRectF(x, y, box.w * factor * s, box.h * factor * s)

    def paintEvent(self, _event):
        c = self.canvas
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(theme.colour("desk")))
        w, h = c.page_mm
        page = QRectF(PAD, PAD, w * c.ppm, h * c.ppm)
        painter.fillRect(page, QColor(theme.colour("paper")))
        image, norm = c.page_render()
        if image is not None:   # stretched over the part of the page it shows, at whatever zoom it was rendered
            painter.drawImage(QRectF(page.left() + norm.x() * page.width(), page.top() + norm.y() * page.height(),
                                     norm.width() * page.width(), norm.height() * page.height()), image)
        painter.setPen(QPen(QColor(theme.colour("line-strong")), 1))
        painter.drawRect(page)
        accent = QColor(theme.colour("accent"))
        faint = QColor(theme.colour("muted"))
        for box in c.boxes:
            chosen = box.id == c.selected
            dx = dy = 0.0
            factor = 1.0
            if chosen and c.drag is not None:
                dx, dy, factor = c.drag["dx"], c.drag["dy"], c.drag["factor"]
            rect = self.rect_of(box, dx, dy, factor)
            if chosen:
                fill = QColor(accent)
                fill.setAlpha(28)
                painter.fillRect(rect, fill)
                painter.setPen(QPen(accent, 1.6))
                painter.drawRect(rect)
                if box.resizable:
                    painter.fillRect(self.handle_rect(rect), accent)
                label = c.drag.get("label") if c.drag else None
                if label:
                    painter.setPen(QPen(accent, 1))
                    painter.drawText(rect.bottomRight() + QPointF(HANDLE, -2), label)
            elif box.id == c.hovered:
                painter.setPen(QPen(accent, 1, Qt.PenStyle.DashLine))
                painter.drawRect(rect)
            else:
                pen = QPen(faint, 1, Qt.PenStyle.DotLine)
                painter.setPen(pen)
                painter.drawRect(rect)
        painter.end()

    @staticmethod
    def handle_rect(rect):
        return QRectF(rect.right() - HANDLE / 2, rect.bottom() - HANDLE / 2, HANDLE, HANDLE)

    def box_at(self, point):
        """The object under `point`: its handle first where the chosen one has one, then the smallest box holding the point -- a text inside a plan's frame is reached."""
        c = self.canvas
        chosen = c.box(c.selected)
        if chosen is not None and chosen.resizable and self.handle_rect(self.rect_of(chosen)).adjusted(-3, -3, 3, 3).contains(point):
            return chosen, "resize"
        x, y = self.to_mm(point)
        under = [b for b in c.boxes if b.contains(x, y)]
        if not under:
            return None, None
        return min(under, key=lambda b: max(b.w * b.h, 0.01)), "move"

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        box, what = self.box_at(event.position())
        c = self.canvas
        c.select(box.id if box else "")
        if box is not None:
            c.drag = {"id": box.id, "what": what, "start": event.position(), "dx": 0.0, "dy": 0.0, "factor": 1.0, "label": "", "moved": False}
        self.update()

    def mouseMoveEvent(self, event):
        c = self.canvas
        if c.drag is None:
            box, what = self.box_at(event.position())
            hovered = box.id if box else ""
            self.setCursor(Qt.CursorShape.SizeFDiagCursor if what == "resize" else Qt.CursorShape.SizeAllCursor if box else Qt.CursorShape.ArrowCursor)
            if hovered != c.hovered:
                c.hovered = hovered
                self.update()
            return
        box = c.box(c.drag["id"])
        if box is None:
            return
        delta = event.position() - c.drag["start"]
        if abs(delta.x()) + abs(delta.y()) > 2:
            c.drag["moved"] = True
        if c.drag["what"] == "move":
            c.drag["dx"], c.drag["dy"] = delta.x() / c.ppm, delta.y() / c.ppm
        else:
            new_w = max(box.w * 0.05, box.w + delta.x() / c.ppm)
            c.drag["factor"] = new_w / box.w if box.w > 0 else 1.0
            c.drag["label"] = c.resize_label(box, c.drag["factor"])
        self.update()

    def mouseReleaseEvent(self, event):
        c = self.canvas
        drag, c.drag = c.drag, None
        self.update()
        if drag is None or not drag["moved"]:
            return
        box = c.box(drag["id"])
        if box is None:
            return
        if drag["what"] == "move":
            c.moveRequested.emit(box.id, snap(box.x + drag["dx"]), snap(box.y + drag["dy"]))
        elif abs(drag["factor"] - 1.0) > 1e-6:
            c.resizeRequested.emit(box.id, drag["factor"])

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.canvas.zoom_by(ZOOM_STEP if event.angleDelta().y() > 0 else 1 / ZOOM_STEP, event.position())
            event.accept()
        else:
            event.ignore()


# The page's render (SheetCanvas): asked for once the zoom stands still this long; the whole page up to this many pixels, the part in view (and this much of the view round it) beyond.
RENDER_SETTLE_MS = 120


RENDER_MAX_PX = 12_000_000


RENDER_MARGIN = 0.25


class SheetCanvas(QWidget):
    """The centre of the sheet editor: the compiled page at a zoom -- fit by default, `zoom_in`, `zoom_out`, `fit` and Ctrl + wheel --, a frame round every object, a banner where the sheet does not compile. It writes nothing: a frame dragged is `moveRequested(id, x, y)` in millimetres, a frame resized `resizeRequested(id, factor)`, a frame chosen `selectionChanged(id)` ("" for none)."""

    selectionChanged = Signal(str)
    moveRequested = Signal(str, float, float)
    resizeRequested = Signal(str, float)

    def __init__(self, parent=None, lang="en"):
        super().__init__(parent)
        self.lang = lang
        self.page_mm = (420.0, 297.0)
        self.boxes = []
        self.selected = ""
        self.hovered = ""
        self.drag = None
        self.ppm = 1.0
        self.fitting = True
        self.scale_label = None     # callable(box, factor) -> str, the scale a frame dragged larger would print at
        self.document = QPdfDocument(self)
        self._buffer = None
        self._image = None
        self._image_key = None
        self._image_norm = QRectF(0, 0, 1, 1)
        self.generation = 0
        # The page is rendered by QtPdf's own thread, never in a paint (v0.117): until then each zoom rendered the whole page at once on the window's thread -- an A1 at the deepest zoom, 300 megapixels. The last image is drawn stretched meanwhile; a render is asked for once the zoom stands still (RENDER_SETTLE_MS), one at a time -- QtPdf runs every call under one lock (plan_canvas.PdfPages) -- and beyond RENDER_MAX_PX only the part in view is rendered, with RENDER_MARGIN of the view round it.
        self.renderer = QPdfPageRenderer(self)
        self.renderer.setRenderMode(QPdfPageRenderer.RenderMode.MultiThreaded)
        self.renderer.setDocument(self.document)
        self.renderer.pageRendered.connect(self._on_rendered)
        self._pending = None        # (request id, key, norm) of the render under way
        self._wanted = None         # (key, size, clip, norm) asked for while one ran
        self._retired = []          # documents replaced while a render ran: closed once it is back
        self._settle = QTimer(self)
        self._settle.setSingleShot(True)
        self._settle.setInterval(RENDER_SETTLE_MS)
        self._settle.timeout.connect(self._request)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        bar = QHBoxLayout()
        bar.setContentsMargins(6, 4, 6, 0)
        self.zoom_out_button = QToolButton()
        self.zoom_out_button.setText("−")
        self.fit_button = QToolButton()
        self.zoom_in_button = QToolButton()
        self.zoom_in_button.setText("+")
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.fit_button.clicked.connect(self.fit)
        for button in (self.zoom_out_button, self.fit_button, self.zoom_in_button):
            bar.addWidget(button)
        bar.addStretch(1)
        layout.addLayout(bar)
        self.banner = QLabel()
        self.banner.setWordWrap(True)
        self.banner.setTextFormat(Qt.TextFormat.PlainText)
        self.banner.hide()
        layout.addWidget(self.banner)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(False)
        self.surface = _Page(self)
        self.scroll.setWidget(self.surface)
        layout.addWidget(self.scroll, 1)
        self.set_language(lang)
        self._resize_surface()

    def t(self, key, **values):
        return words(self.lang, key, **values)

    def set_language(self, lang):
        self.lang = lang
        self.fit_button.setText(self.t("se_fit"))
        flowbar.set_tip(self.zoom_out_button, self.t("se_zoom_out"), self.t("se_zoom_usage"))
        flowbar.set_tip(self.zoom_in_button, self.t("se_zoom_in"), self.t("se_zoom_usage"))
        flowbar.set_tip(self.fit_button, self.t("se_fit"), self.t("se_fit_usage"))

    # -- what is shown ----------------------------------------------------------------------

    def set_page_size(self, width_mm, height_mm):
        if (width_mm, height_mm) != self.page_mm:
            self.page_mm = (float(width_mm), float(height_mm))
            self._relayout()

    def load_pdf(self, data):
        """Shows the PDF `data` holds -- read from a buffer, never a file. False where it is no PDF, the page shown before staying shown."""
        buffer = QBuffer(self)
        buffer.setData(QByteArray(bytes(data)))
        buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        document = QPdfDocument(self)
        document.load(buffer)
        if document.status() != QPdfDocument.Status.Ready or document.pageCount() == 0:
            document.deleteLater()
            buffer.close()
            buffer.deleteLater()
            return False
        old_document, old_buffer = self.document, self._buffer
        self.document, self._buffer = document, buffer
        if self._pending is not None:
            self._retired.append((old_document, old_buffer))   # closed once the render under way is back (QtPdf's one lock)
        else:
            self._close(old_document, old_buffer)
        self.renderer.setDocument(document)
        size = document.pagePointSize(0)
        self.generation += 1
        self._image = None
        self.set_page_size(round(size.width() * 25.4 / 72, 2), round(size.height() * 25.4 / 72, 2))
        self.surface.update()
        return True

    def clear_page(self):
        """No page shown: the paper is drawn blank until the next compile."""
        self.document.close()
        self.generation += 1
        self._image = self._image_key = None
        self.surface.update()

    def has_page(self):
        return self.document.status() == QPdfDocument.Status.Ready and self.document.pageCount() > 0

    def page_image(self):
        """The page as last rendered -- at the zoom shown, or, while a render at it is on its way, at the one before, drawn stretched -- and the render the zoom and the view call for asked for once they stand still. None before the first render is back."""
        if not self.has_page():
            return None
        wish = self._wish()
        if wish is not None and wish[0] != self._image_key and (self._pending is None or self._pending[1] != wish[0]):
            self._wanted = wish
            if not self._settle.isActive():
                self._settle.start()
        return self._image

    def page_render(self):
        """(image, the part of the page it shows as fractions of it) -- what the surface paints."""
        return self.page_image(), self._image_norm

    def _wish(self):
        """(key, size, clip, norm) of the render the zoom shown and the part in view call for."""
        ratio = self.devicePixelRatioF() or 1.0
        w, h = self.page_mm
        full = QSize(max(1, round(w * self.ppm * ratio)), max(1, round(h * self.ppm * ratio)))
        if full.width() * full.height() <= RENDER_MAX_PX:
            return (self.generation, full.width(), full.height()), full, None, QRectF(0, 0, 1, 1)
        # the part in view, and a margin round it, in the page's pixels
        bar_x, bar_y = self.scroll.horizontalScrollBar().value(), self.scroll.verticalScrollBar().value()
        view = self.scroll.viewport().size()
        mx, my = view.width() * RENDER_MARGIN, view.height() * RENDER_MARGIN
        left = max(0.0, (bar_x - mx - PAD) * ratio)
        top = max(0.0, (bar_y - my - PAD) * ratio)
        right = min(float(full.width()), (bar_x + view.width() + mx - PAD) * ratio)
        bottom = min(float(full.height()), (bar_y + view.height() + my - PAD) * ratio)
        if right - left < 1 or bottom - top < 1:
            return None
        # snapped to a grid of 256 pixels, so a scroll of a few pixels asks for nothing new
        step = 256
        x0, y0 = int(left // step * step), int(top // step * step)
        x1, y1 = min(full.width(), int(-(-right // step) * step)), min(full.height(), int(-(-bottom // step) * step))
        clip = QRect(x0, y0, x1 - x0, y1 - y0)
        norm = QRectF(x0 / full.width(), y0 / full.height(), (x1 - x0) / full.width(), (y1 - y0) / full.height())
        return (self.generation, full.width(), full.height(), x0, y0, x1, y1), full, clip, norm

    def _request(self):
        if self._pending is not None or self._wanted is None or not self.has_page():
            return
        key, full, clip, norm = self._wanted
        self._wanted = None
        if key[0] != self.generation:
            return
        options = QPdfDocumentRenderOptions()
        size = full
        if clip is not None:
            from plan_canvas import clip_bias
            bias = clip_bias()
            options.setScaledSize(full)
            options.setScaledClipRect(QRect(clip.x(), clip.y(), clip.width() + bias, clip.height() + bias))
            size = clip.size()
        request = self.renderer.requestPage(0, size, options)
        if request:
            self._pending = (request, key, norm)

    def _on_rendered(self, _page, _size, image, _options, request):
        if self._pending is None or request != self._pending[0]:
            return
        _request_id, key, norm = self._pending
        self._pending = None
        for document, buffer in self._retired:
            self._close(document, buffer)
        self._retired = []
        if not image.isNull() and key[0] == self.generation:
            image.setDevicePixelRatio(self.devicePixelRatioF() or 1.0)
            self._image, self._image_key, self._image_norm = image, key, norm
            self.surface.update()
        if self._wanted is not None:
            self._request()
        else:
            self.surface.update()   # the view may have moved on while it rendered: page_image() asks again

    @staticmethod
    def _close(document, buffer):
        document.close()
        document.deleteLater()
        if buffer is not None:
            buffer.close()
            buffer.deleteLater()

    def wait_rendered(self, timeout_ms=10000):
        """The page rendered at the zoom shown (a test, a sheet exported to an image): the loop turned until it is."""
        import time
        from PySide6.QtWidgets import QApplication
        end = time.monotonic() + timeout_ms / 1000
        while time.monotonic() < end:
            wish = self._wish() if self.has_page() else None
            if wish is None or (self._image_key == wish[0] and self._pending is None):
                return self._image
            self.page_image()
            QApplication.processEvents()
            time.sleep(0.005)
        return self._image

    def set_boxes(self, boxes):
        self.boxes = list(boxes)
        if self.selected and self.box(self.selected) is None:
            self.selected = ""
            self.selectionChanged.emit("")
        self.surface.update()

    def box(self, object_id):
        return next((b for b in self.boxes if b.id == object_id), None)

    def select(self, object_id):
        object_id = object_id or ""
        if object_id != self.selected:
            self.selected = object_id
            self.surface.update()
            self.selectionChanged.emit(object_id)

    def say(self, message, kind="danger"):
        """A sentence in the banner over the page -- Typst's own words where the sheet does not compile; "" hides it."""
        self.banner.setText(message)
        self.banner.setProperty("callout", kind)
        self.banner.style().unpolish(self.banner)
        self.banner.style().polish(self.banner)
        self.banner.setVisible(bool(message))

    def resize_label(self, box, factor):
        if self.scale_label is None:
            return ""
        return self.scale_label(box, factor) or ""

    # -- the zoom ---------------------------------------------------------------------------

    def fit(self):
        self.fitting = True
        self._relayout()

    def zoom_in(self):
        self.zoom_by(ZOOM_STEP)

    def zoom_out(self):
        self.zoom_by(1 / ZOOM_STEP)

    def zoom_by(self, factor, anchor=None):
        """The zoom multiplied by `factor`, between ZOOM_MIN and ZOOM_MAX -- about `anchor` (a point of the page's surface, the pointer under Ctrl + wheel), which stays under the pointer."""
        old = self.ppm
        self.fitting = False
        self.ppm = min(ZOOM_MAX, max(ZOOM_MIN, self.ppm * factor))
        bars = self.scroll.horizontalScrollBar(), self.scroll.verticalScrollBar()
        view = None if anchor is None else (anchor.x() - bars[0].value(), anchor.y() - bars[1].value())
        self._resize_surface()
        if anchor is not None and old > 0:
            k = self.ppm / old
            bars[0].setValue(round(PAD + (anchor.x() - PAD) * k - view[0]))
            bars[1].setValue(round(PAD + (anchor.y() - PAD) * k - view[1]))

    def _relayout(self):
        if self.fitting:
            view = self.scroll.viewport().size()
            w, h = self.page_mm
            if view.width() > 2 * PAD and view.height() > 2 * PAD and w > 0 and h > 0:
                self.ppm = min(ZOOM_MAX, max(ZOOM_MIN, min((view.width() - 2 * PAD) / w, (view.height() - 2 * PAD) / h)))
        self._resize_surface()

    def _resize_surface(self):
        w, h = self.page_mm
        self.surface.setFixedSize(round(w * self.ppm + 2 * PAD), round(h * self.ppm + 2 * PAD))
        self.surface.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.fitting:
            self._relayout()

    def showEvent(self, event):
        super().showEvent(event)
        if self.fitting:
            self._relayout()
