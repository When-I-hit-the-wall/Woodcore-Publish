"""What marks a material wherever the window shows one (issue #110): the icon of its type -- a bar, a panel in perspective, a layer, the prototype's -- in the theme's colours, and the words of the label of its source. Read by the «Matériaux» tab's list and sheet, which do not import each other (D-06).
"""

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

import theme
from domains import materials_library

TYPE_SHAPES = {   # the prototype's icons of the three types: a bar, a panel in perspective, a layer
    "member": '<rect x="1" y="4" width="14" height="4" rx="1" fill="{wood}" stroke="{ink}" stroke-width=".7"/>',
    "panel": '<path d="M1 9 L5 3 H15 L11 9 Z" fill="{board}" stroke="{ink}" stroke-width=".7"/>',
    "other": '<rect x="1" y="3" width="14" height="6" fill="{other}" stroke="{ink}" stroke-width=".7"/>',
}


def type_icon(kind):
    """The icon of a type of material, drawn in the theme's colours."""
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 12" width="16" height="12">%s</svg>' % TYPE_SHAPES[kind].format(
        wood=theme.colour("wood"), board=theme.colour("wood-soft"), other=theme.colour("bg-sunk"), ink=theme.colour("ink-soft"))
    pixmap = QPixmap(QSize(32, 24))
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    QSvgRenderer(QByteArray(svg.encode("utf-8"))).render(painter)
    painter.end()
    return QIcon(pixmap)


def tag_text(t, m):
    tag = materials_library.tag(m)
    return t("mat_src_" + tag) if tag in ("ext", "user") else tag
