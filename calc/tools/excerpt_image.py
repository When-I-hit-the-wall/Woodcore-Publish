"""The image of an excerpt of a norm, cut out of the edition's page (spec 2026-10-22-onglet-neige-type, ARCH-013, D-20, REQ-004).

The page is rendered by QtPdf -- the engine the window's PDF panes already use -- at `DPI`, and the excerpt's box (PDF points from the page's top-left corner, calc/norms/excerpts.py) cut out of it; an excerpt without a box is its whole page. Each image is kept on this machine, in Woodcore's cache (usersettings.cache_dir), named by the edition's file, its page, its box and the resolution, so the bubble shows it at once the second time; never in a project, never in the repository. An edition that is not there gives None: the bubble shows the clause and its words without an image, and says so.
"""

from PySide6.QtCore import QSize
from PySide6.QtGui import QImage
from PySide6.QtPdf import QPdfDocument

import usersettings

DPI = 144
_memory = {}


def _key(excerpt):
    box = "-".join("%g" % v for v in excerpt.box) if excerpt.box else "page"
    return "%s_p%d_%s_%d" % (excerpt.file.rsplit(".", 1)[0], excerpt.page, box, DPI)


def image(excerpt):
    """The excerpt's image (a QImage), or None where its edition is not shipped or its page cannot be rendered."""
    key = _key(excerpt)
    if key in _memory:
        return _memory[key]
    cache = usersettings.cache_dir("excerpts") / (key + ".png")
    if cache.is_file():
        found = QImage(str(cache))
        if not found.isNull():
            _memory[key] = found
            return found
    pdf = excerpt.pdf()
    if pdf is None:
        return None
    document = QPdfDocument()
    if document.load(str(pdf)) != QPdfDocument.Error.None_ or not 0 < excerpt.page <= document.pageCount():
        return None
    points = document.pagePointSize(excerpt.page - 1)
    scale = DPI / 72.0
    page = document.render(excerpt.page - 1, QSize(round(points.width() * scale), round(points.height() * scale)))
    document.close()
    if page.isNull():
        return None
    if excerpt.box:
        x0, y0, x1, y1 = excerpt.box
        page = page.copy(round(x0 * scale), round(y0 * scale), round((x1 - x0) * scale), round((y1 - y0) * scale))
    cache.parent.mkdir(parents=True, exist_ok=True)
    page.save(str(cache), "PNG")
    _memory[key] = page
    return page
