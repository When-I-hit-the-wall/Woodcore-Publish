"""The dimension tools' symbols, the same in the three tabs that dimension a figure -- the static models, the schemas and the position plans (issue #9, UI-004; the engineer: «utiliser les mêmes logos d'outils pour les 3»).

The four kinds the static models had are drawn as statics_tab draws them -- the very symbol its figure draws (statics_svg.swatch) -- and the plan's fifth, the chain, which only the plan has, is drawn here in the same ink, as three dimensions end to end.
"""

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

import statics_tab

# The plan's own: a chain of three lengths on one line, with the swatches' ink.
CHAIN_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 18">'
             '<g stroke="{ink}" stroke-width="1.6" fill="none" stroke-linecap="butt">'
             '<path d="M2 12 H38"/><path d="M2 4 V15 M14 4 V15 M26 4 V15 M38 4 V15"/>'
             '<path d="M0 14 L4 10 M12 14 L16 10 M24 14 L28 10 M36 14 L40 10"/></g></svg>')

TOOLS = ("dimension-horizontal", "dimension-vertical", "dimension-parallel", "dimension-chain", "dimension-angle")


def icon(tool, size, ink=None, ground=None):
    """The symbol of a dimension tool at `size` pixels: statics_tab.svg_icon's for its four kinds, the chain's own for the fifth."""
    if tool != "dimension-chain":
        return statics_tab.svg_icon(tool, size, ink, ground)
    svg = CHAIN_SVG.format(ink=ink or statics_tab.SWATCH_INK)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    box = renderer.viewBoxF()
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    scale = min(size / box.width(), size / box.height())
    w, h = box.width() * scale, box.height() * scale
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF((size - w) / 2, (size - h) / 2, w, h))
    painter.end()
    return QIcon(pix)
