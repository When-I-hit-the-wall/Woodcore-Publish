"""What a plan's background is rendered with -- the render jobs and their caches in memory and on disk, a PDF's pages, the tiles, the SVG layers, the tinting of a superposed plan -- split out of calc/tools/plan_canvas.py (issue #30), moved verbatim. plan_canvas.py imports every name back, so plan_canvas.RENDERS and plan_canvas.ensure_pixmap_cache are still read where they always were.
"""

import collections
import dataclasses
import functools
import hashlib
import os
import re
import threading
import time
from pathlib import Path
import shiboken6
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QObject, QPointF, QRect, QRectF, QSize, Qt, QTimer, Signal, qVersion
from PySide6.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPainterPath, QPen, QPixmap, QPixmapCache, QTransform
from PySide6.QtPdf import QPdfDocument, QPdfDocumentRenderOptions, QPdfPageRenderer
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsScene, QGraphicsSimpleTextItem, QGraphicsView, QLineEdit
import theme  # the desk around the sheet (theme.py, v0.90)


def _probe_pdf():
    """A PDF of one 100 × 100 pt page with a vertical line at x = 99 pt, written here: the one page whose render clip_bias() can read a position off."""
    content = b"0 0 0 RG 0.4 w 99 0 m 99 100 l S"
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] /Contents 4 0 R >>",
               b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream"]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    for offset in offsets:
        out += b"%010d 00000 n \n" % offset
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref)
    return bytes(out)


@functools.cache
def clip_bias():
    """How much wider and taller than the image its clip rectangle must be asked for, for a clipped render to keep the scale asked for. QtPdf (6.11) scales a clipped render by the rectangle's right() - left(), which QRect puts a pixel short of its width, so a render 1000 pixels wide came out 999/1000 of its scale, two pixels off the whole page's render at its far side; the pixels it draws are the image's, whatever the rectangle's size, so a rectangle one pixel larger puts it right. Measured once, on a line of known position, rather than assumed -- a Qt that reads the width would be put a pixel wrong the other way."""
    buffer = QBuffer()
    buffer.setData(QByteArray(_probe_pdf()))
    buffer.open(QIODevice.OpenModeFlag.ReadOnly)
    document = QPdfDocument()
    document.load(buffer)
    options = QPdfDocumentRenderOptions()
    options.setScaledSize(QSize(1000, 1000))
    options.setScaledClipRect(QRect(0, 0, 1001, 11))
    image = document.render(0, QSize(1000, 10), options)
    weights = [(x, image.pixelColor(x, 5).alpha()) for x in range(970, 1000)]
    total = sum(a for _x, a in weights)
    if image.isNull() or total == 0:
        return 1
    # the line's middle: pixel 989.5 at the scale asked for; 990.5 if this Qt reads the width, the larger rectangle then scaling it up
    centre = sum(x * a for x, a in weights) / total
    return 1 if abs(centre - 989.5) <= abs(centre - 990.5) else 0


def file_key(path):
    """What the renders of a file are kept under: the file, its size and the time it was last written. A plan set the architect replaced by their next version is then another file, and is rendered afresh."""
    path = Path(path).resolve()
    stat = path.stat()
    return (str(path), stat.st_size, stat.st_mtime_ns)


def same_scale(a, b):
    return b > 0 and abs(a / b - 1) < 1e-3


def covers(outer, inner, scale):
    """Whether the rectangle `outer` covers `inner`, to a screen pixel at `scale` screen pixels per sheet unit."""
    pixel = 1.0 / max(scale, 1e-9)
    return outer.adjusted(-pixel, -pixel, pixel, pixel).contains(inner)


def tile_geometry(key, sheet):
    """The part of the sheet a tile kept under `key` shows, and its pixels per sheet unit."""
    _kind, _file, _page, width, height, x, y, w, h = key
    sx, sy = width / sheet.width(), height / sheet.height()
    return QRectF(x / sx, y / sy, w / sx, h / sy), sx


@dataclasses.dataclass(eq=False)
class RenderJob:
    """One render asked of a PDF: the whole page (`base`) or the part of it in view (`tile`). `key` is what it is kept under -- (kind, file_key, page, width, height), and for a tile the part rendered, (x, y, w, h), all in pixels --, `rect` the part of the sheet it shows, `scale` its pixels per sheet unit, `disk` whether it is kept on disk as well."""

    kind: str
    key: tuple
    size: QSize
    options: QPdfDocumentRenderOptions
    rect: QRectF
    scale: float
    disk: bool = False

    @property
    def file(self):
        return self.key[1]

    @property
    def page(self):
        return self.key[2]


Render = collections.namedtuple("Render", "image rect scale")


class RenderCache:
    """The renders made in this session, the most recently used last, up to `limit` bytes -- the oldest go first. Kept as images rather than pixmaps: the cache outlives any one window, and a pixmap may not outlive the application."""

    def __init__(self, limit):
        self.limit = limit
        self.items = collections.OrderedDict()
        self.size = 0

    def get(self, key):
        entry = self.items.get(key)
        if entry is not None:
            self.items.move_to_end(key)
        return entry

    def put(self, key, image, rect, scale):
        old = self.items.pop(key, None)
        if old is not None:
            self.size -= old.image.sizeInBytes()
        self.items[key] = Render(image, QRectF(rect), scale)
        self.size += image.sizeInBytes()
        while self.size > self.limit and len(self.items) > 1:
            _key, dropped = self.items.popitem(last=False)
            self.size -= dropped.image.sizeInBytes()

    def tiles(self, file, page):
        """(key, render) of the parts of a page rendered for a view, the most recent first."""
        return [(key, entry) for key, entry in reversed(self.items.items()) if key[0] == "tile" and key[1] == file and key[2] == page]


class DiskCache:
    """The renders kept from one session to the next -- the whole page and the first view of each page opened -- as PNG files. A file's name is a hash of the page it shows (the file, its size and time, the page, the Qt that rendered it) followed by the render's size and the part of it rendered, so that the views kept of a page can be listed and one at another scale stand in for a moment. They are written in a thread of their own (QImage.save lets go of Python's lock), and beyond `limit` bytes the least recently used are removed. A file that cannot be read or written is simply not used: the page is rendered as if it had never been."""

    NAME = re.compile(r"[0-9a-f]+-tile-(\d+)x(\d+)-(\d+)-(\d+)-(\d+)x(\d+)")

    def __init__(self, folder, limit):
        self.folder = Path(folder)
        self.limit = limit
        self.lock = threading.Lock()

    def prefix(self, file, page):
        """What the renders of one page are named by: a hash of the file, its size and time, the page and the Qt that renders it."""
        return hashlib.sha1(repr((file, page, qVersion(), clip_bias())).encode("utf-8")).hexdigest()[:24]

    def path(self, key):
        kind, file, page, width, height, *part = key
        x, y, w, h = part or (0, 0, width, height)
        return self.folder / f"{self.prefix(file, page)}-{kind}-{width}x{height}-{x}-{y}-{w}x{h}.png"

    def tiles(self, file, page):
        """(key, path) of the parts of a page kept for a view."""
        out = []
        if not self.folder.is_dir():
            return out
        for path in self.folder.glob(f"{self.prefix(file, page)}-tile-*.png"):
            match = self.NAME.fullmatch(path.stem)
            if match:
                width, height, x, y, w, h = map(int, match.groups())
                out.append((("tile", file, page, width, height, x, y, w, h), path))
        return out

    def load(self, key, size, path=None):
        """The render kept under `key`, of `size` pixels, or None."""
        path = path or self.path(key)
        if not path.is_file():
            return None
        image = QImage(str(path))
        if image.isNull() or image.size() != size:
            return None
        try:
            os.utime(path)  # used: the last to be removed
        except OSError:
            pass
        return image.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)

    def save(self, key, image):
        threading.Thread(target=self._write, args=(self.path(key), image), daemon=True).start()

    def _write(self, path, image):
        try:
            self.folder.mkdir(parents=True, exist_ok=True)
            partial = path.with_name(f"{path.stem}.{os.getpid()}.{threading.get_ident()}.part")
            if image.save(str(partial), "PNG"):
                os.replace(partial, path)
            else:
                partial.unlink(missing_ok=True)
            self._trim()
        except OSError:
            pass

    def _trim(self):
        with self.lock:
            files = []
            for path in self.folder.iterdir():
                try:
                    stat = path.stat()
                    if path.suffix == ".part" and time.time() - stat.st_mtime > 3600:
                        path.unlink()  # a write cut short by the window closing
                    elif path.suffix == ".png":
                        files.append((stat.st_mtime, stat.st_size, path))
                except OSError:
                    continue
            total = sum(size for _mtime, size, _path in files)
            for _mtime, size, path in sorted(files):
                if total <= self.limit:
                    break
                try:
                    path.unlink()
                    total -= size
                except OSError:
                    pass


class PdfPages(QObject):
    """One PDF open for the canvas, and the renders asked of it, one at a time.

    QtPdf runs every call into PDFium under a single lock, the renders in its own thread included: loading or closing a document, or asking for a page's size, while a page renders waits for that render to end -- 8 seconds on a sheet of the architect's --, and a render once asked for cannot be taken back. So a render is asked for only when the one before it has come back, the part in view before the whole page, and a newer request takes the place of the one of its kind still waiting; the canvas loads and closes a document only while nothing renders (PlanCanvas.collect)."""

    rendered = Signal(object, QImage)  # the job, and its image

    def __init__(self, path, key, parent):
        super().__init__(parent)
        self.key = key
        self.document = QPdfDocument(self)
        self.document.load(str(path))
        self.renderer = QPdfPageRenderer(self)
        self.renderer.setRenderMode(QPdfPageRenderer.RenderMode.MultiThreaded)
        self.renderer.setDocument(self.document)
        self.renderer.pageRendered.connect(self.on_page_rendered)
        self.busy = None  # (request id, job) of the render on its way
        self.waiting = {}  # kind -> the job waiting for it

    def page_count(self):
        """The document's pages, read when it was loaded: asking takes no lock."""
        return self.document.pageCount()

    def ask(self, job):
        self.waiting[job.kind] = job
        self.send()

    def drop(self):
        """Forgets the renders not yet on their way: another plan is shown."""
        self.waiting.clear()

    def send(self):
        if self.busy is not None or not self.waiting:
            return
        # the view first, then the whole page, then anything else -- another plan shown over this one (v0.116)
        kind = "tile" if "tile" in self.waiting else "base" if "base" in self.waiting else next(iter(self.waiting))
        job = self.waiting.pop(kind)
        request = self.renderer.requestPage(job.page, job.size, job.options)
        if request:
            self.busy = (request, job)
        else:
            self.waiting.clear()  # a document that could not be read: nothing will come

    def on_page_rendered(self, _page, _size, image, _options, request):
        if self.busy is None or request != self.busy[0]:
            return
        job = self.busy[1]
        self.busy = None
        self.rendered.emit(job, image)
        self.send()

    def close(self):
        """Closes the document at once -- called only while nothing renders, when that takes no time; left to deleteLater, it could run while the next render holds the lock."""
        self.waiting.clear()
        shiboken6.delete(self.renderer)
        shiboken6.delete(self.document)
        shiboken6.delete(self)


# Qt keeps an item's cached picture in QPixmapCache, 10 MB by default -- less than one picture of a full-screen view (1920 x 1080 at 150 %: 19 MB). Past it the cache keeps nothing, and the SVG of the symbols was drawn again, vector by vector, at every frame of a pan or a zoom (measured, docs/architecture/performance.md, v0.117).
PIXMAP_CACHE_KB = 256 * 1024


def ensure_pixmap_cache():
    """QPixmapCache made large enough for a cached layer of a full-screen view -- never smaller than it is."""
    if QPixmapCache.cacheLimit() < PIXMAP_CACHE_KB:
        QPixmapCache.setCacheLimit(PIXMAP_CACHE_KB)


class SvgLayer(QGraphicsItem):
    """An SVG drawn over an exact rectangle of the scene. QGraphicsSvgItem would size itself by the SVG's whole-pixel default size, and an A3 page of 1190.55 points would come out 0.45 points short at its far edge -- enough to set a symbol beside what it marks."""

    def __init__(self, renderer, rect):
        super().__init__()
        self.renderer = renderer
        self.rect = QRectF(rect)
        ensure_pixmap_cache()   # or the cached picture is thrown away as soon as made (PIXMAP_CACHE_KB)
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)

    def set_rect(self, rect):
        self.prepareGeometryChange()
        self.rect = QRectF(rect)
        self.update()

    def boundingRect(self):
        return self.rect

    def paint(self, painter, _option, _widget=None):
        if self.renderer.isValid():
            self.renderer.render(painter, self.rect)


class PageTile(QGraphicsItem):
    """A part of a PDF page rendered for the view, over the rectangle of the sheet it shows. While the view is at the scale it was rendered for, it is drawn pixel for pixel: smoothing an image drawn at its own size would only blur it, by the half pixel a scroll position may fall between. Once the view has zoomed away from it, it is smoothed like any image, until the next render replaces it."""

    def __init__(self):
        super().__init__()
        self.pixmap = QPixmap()
        self.rect = QRectF()

    def set_pixmap(self, pixmap, rect):
        self.prepareGeometryChange()
        self.pixmap = pixmap
        self.rect = QRectF(rect)
        self.update()

    def boundingRect(self):
        return self.rect

    def paint(self, painter, _option, _widget=None):
        if self.pixmap.isNull() or self.rect.isEmpty():
            return
        # screen pixels per pixel of the render: 1 while the view has not zoomed since -- to the half pixel a whole page's width in pixels is rounded to
        ratio = painter.deviceTransform().m11() * self.rect.width() / self.pixmap.width()
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, abs(ratio - 1) > 2e-3)
        painter.drawPixmap(self.rect, self.pixmap, QRectF(self.pixmap.rect()))


class MultiplyPixmapItem(QGraphicsItem):
    """The superposed plan's background (v0.116), drawn with QPainter's Multiply over what lies under it: its white paper takes nothing away from the plan open, only its lines darken it -- in their own colours, or in the one colour the superposition is shown in. Over the rectangle `rect` of the superposed plan's own sheet, smoothed."""

    def __init__(self):
        super().__init__()
        self.pixmap = QPixmap()
        self.rect = QRectF()

    def set_pixmap(self, pixmap, rect):
        self.prepareGeometryChange()
        self.pixmap = pixmap
        self.rect = QRectF(rect)
        self.update()

    def boundingRect(self):
        return self.rect

    def paint(self, painter, _option, _widget=None):
        if self.pixmap.isNull() or self.rect.isEmpty():
            return
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.drawPixmap(self.rect, self.pixmap, QRectF(self.pixmap.rect()))


def tint_image(image, ink=None):
    """`image` laid on white paper, and where `ink` is given its lines in that colour: made grey, then Screen-blended with the ink, so black becomes the ink and white stays white (the superposition's colours, v0.116)."""
    paper = QImage(image.size(), QImage.Format.Format_ARGB32_Premultiplied)
    paper.fill(theme.qcolor("paper"))
    painter = QPainter(paper)
    painter.drawImage(0, 0, image)
    painter.end()
    if ink is None:
        return paper
    grey = paper.convertToFormat(QImage.Format.Format_Grayscale8).convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
    painter = QPainter(grey)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Screen)
    painter.fillRect(grey.rect(), QColor(ink))
    painter.end()
    return grey


_SVG_PAINT = re.compile(r'\b(fill|stroke)="([^"]*)"')


_WHITE = {"#fff", "#ffffff", "white", "none", "transparent"}


def tint_svg(svg, ink):
    """An SVG of symbols with every colour but white and none made `ink` -- the superposed plan's elements in the superposition's one colour (v0.116). The texts that state no fill take the ink from the root."""
    svg = _SVG_PAINT.sub(lambda m: m.group(0) if m.group(2).strip().lower() in _WHITE else f'{m.group(1)}="{ink}"', svg)
    return svg.replace("<svg ", f'<svg fill="{ink}" ', 1)


def _cosmetic(colour, width=1.5, dash=None):
    pen = QPen(colour, width)
    pen.setCosmetic(True)
    if dash:
        pen.setDashPattern(dash)
    return pen


class BackgroundFallback(Exception):
    """A document background that could not be rendered: `error` says why, `found` is the (path, format, page) of the file to draw on instead, or None."""

    def __init__(self, error, found):
        super().__init__(str(error))
        self.error = error
        self.found = found
