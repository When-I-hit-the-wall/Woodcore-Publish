"""SVG text rendered as a pixmap or an icon, sharp at the screen's pixel ratio -- the one way the window does it (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, D3).

Seven modules each rendered SVG text into a pixmap their own way: at a ratio of 1, of 2 or of the screen, into the whole square or fitted to the drawing's box, smoothed or not, and two of them recoloured a swatch by the same two string replacements. Written once here; a leaf of the window that imports nothing of it, so `flowbar`, `chrome` and the tabs all may read it.
"""

from PySide6.QtCore import QByteArray, QRectF, QSize, Qt
from PySide6.QtGui import QGuiApplication, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer


def pixel_ratio():
    """The screen's device pixel ratio, what a symbol is rendered at so it stays sharp on a scaled display rather than being drawn at 20 px and blown up."""
    app = QGuiApplication.instance()
    return max(1.0, app.devicePixelRatio()) if app is not None else 1.0


def svg_pixmap(svg, size, fit=False):
    """`svg` rendered `size` logical pixels (a number for a square, or a QSize) at the screen's pixel ratio, on a clear ground, smoothed. `fit`: the drawing's own box scaled into the square and centred, its proportions kept -- else stretched to it, as a 24×24 symbol is drawn."""
    size = size if isinstance(size, QSize) else QSize(round(size), round(size))
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    ratio = pixel_ratio()
    pixmap = QPixmap(round(size.width() * ratio), round(size.height() * ratio))
    pixmap.setDevicePixelRatio(ratio)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    target = QRectF(0, 0, size.width(), size.height())
    if fit:
        box = renderer.viewBoxF()
        if box.width() > 0 and box.height() > 0:
            scale = min(size.width() / box.width(), size.height() / box.height())
            w, h = box.width() * scale, box.height() * scale
            target = QRectF((size.width() - w) / 2, (size.height() - h) / 2, w, h)
    renderer.render(painter, target)
    painter.end()
    return pixmap


def svg_icon(svg, size, fit=False):
    """An icon of `svg_pixmap`."""
    return QIcon(svg_pixmap(svg, size, fit))


def recolour(svg, ink_default, ground_default, ink=None, ground=None):
    """A swatch drawn in its own two colours, given `ink` and `ground` instead where they are said -- through two placeholders, so that a new ink equal to the old ground is not recoloured twice."""
    if ink is None and ground is None:
        return svg
    svg = svg.replace(ink_default, "#000001").replace(ground_default, "#000002")
    return svg.replace("#000001", ink or ink_default).replace("#000002", ground or ground_default)
