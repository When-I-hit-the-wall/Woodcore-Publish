"""What the drawing canvases share to draw -- an SVG over an exact rectangle of the scene, a pen one pixel wide on the screen whatever the zoom, a coordinate rounded as it is saved (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, D2).

The position plan, the fire plan, the static models and the schemas each had their own `SvgLayer`, `_cosmetic` and `_round` -- three bodies of the same class, two caches. Written once here; each canvas imports them under the names it always used, and `plan_canvas.SvgLayer` stays importable from where it was.
"""

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmapCache
from PySide6.QtWidgets import QGraphicsItem

# Qt keeps an item's cached picture in QPixmapCache, 10 MB by default -- less than one picture of a full-screen view (1920 x 1080 at 150 %: 19 MB). Past it the cache keeps nothing, and the SVG of the symbols was drawn again, vector by vector, at every frame of a pan or a zoom (measured, docs/architecture/performance.md, v0.117).
PIXMAP_CACHE_KB = 256 * 1024


def ensure_pixmap_cache():
    """QPixmapCache made large enough for a cached layer of a full-screen view -- never smaller than it is."""
    if QPixmapCache.cacheLimit() < PIXMAP_CACHE_KB:
        QPixmapCache.setCacheLimit(PIXMAP_CACHE_KB)


class SvgLayer(QGraphicsItem):
    """An SVG drawn over an exact rectangle of the scene. QGraphicsSvgItem would size itself by the SVG's whole-pixel default size, and an A3 page of 1190.55 points would come out 0.45 points short at its far edge -- enough to set a symbol beside what it marks.

    Two ways of keeping what was rendered, the one class:

    * by default, Qt's DeviceCoordinateCache in a QPixmapCache made large enough (`ensure_pixmap_cache`): a pan blits what was drawn -- the plans', the fire plans' and the static models' layer;
    * `per_view=True`, **rendered once per view, not once per paint**: an image the size of the view, rendered again only when the SVG, the transform, the view's size or its pixel ratio change, and blitted otherwise -- the schemas' layer. Every movement of the mouse there repaints the whole viewport (the snap marker, the tracking ray, the preview all move), and `QSvgRenderer.render` costs what the figure's text costs to set: measured at a device pixel ratio of 2 on a 1900 x 1000 view, about 300 ms a paint, the freeze the engineer met (v0.77). A pan renders again, which on a figure of a schema's size is not felt.
    """

    def __init__(self, renderer, rect, per_view=False):
        super().__init__()
        self.renderer = renderer
        self.rect = QRectF(rect)
        self.per_view = per_view
        self.generation = 0      # bumped whenever the rectangle changes, which a per-view image is keyed by
        self._image = None
        self._key = None
        if not per_view:
            ensure_pixmap_cache()   # or the cached picture is thrown away as soon as made (PIXMAP_CACHE_KB)
            self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)

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
        if not self.per_view or widget is None or device is None:
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


def cosmetic(colour, width=1.5, dash=None):
    """A pen `width` pixels wide on the screen whatever the zoom, in `colour` (a QColor or its name), dashed by `dash` where given."""
    pen = QPen(QColor(colour), width)
    pen.setCosmetic(True)
    if dash:
        pen.setDashPattern(dash)
    return pen


def saved_at(default):
    """The rounding of a coordinate as a canvas saves it, at `default` decimals -- far below what a click can place -- and an int where it is whole, so a source reads `120` and not `120.0`: 2 for a plan (a hundredth of a sheet unit) and a schema (a hundredth of a millimetre), 3 for a static model (a millimetre, in metres). An angle or a whole millimetre says its own `digits`."""
    def _round(value, digits=default):
        value = round(float(value), digits) + 0.0
        return int(value) if value.is_integer() else value
    return _round
