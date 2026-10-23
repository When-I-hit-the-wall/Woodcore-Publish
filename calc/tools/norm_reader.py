"""Woodcore's reader of a norm: the chapter an excerpt belongs to, scrolled to its page, the clause framed (spec 2026-10-22-onglet-neige-type, REQ-001, D-5, ARCH-RISK-W10).

Ctrl+click on a ⓘ opens it: the whole chapter of the edition the window reads -- SIA 261's chapter 5, pp. 26-29 in French and 25-28 in German (`editions.<lang>.chapter`, calc/norms/excerpts.py) --, cut out of the shipped PDF once with pypdf and kept in Woodcore's cache, so that it scrolls from the chapter's first page to its last and no further. The view is at the excerpt's page, its box framed in the accent colour. An excerpt with a map opens the map's site instead (Anhang D: 261.sia.ch), which the tab does.

It is a window of its own, one for the whole window (`reader(app)`), its pages a `ZoomablePdfView` -- the one every page of Woodcore is shown in, Ctrl+wheel and «Ajuster à la largeur» with it -- under a `FramedPdfView` that paints the frame. Never a `PdfPane`, which compiles Typst (ARCH-RISK-W10). Where the frame goes is a pure function of the view's layout (`page_rect_in_view`), as QPdfView lays its pages out in its multi-page mode -- a test holds the frame to it.
"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtPdf import QPdfDocument
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

import theme
import usersettings
from pdf_pane import ZoomablePdfView

_readers = {}


def page_rect_in_view(page, rect, sizes, pixels, spacing, margins, viewport_width, scroll):
    """The rectangle `rect` (x0, y0, x1, y1 in PDF points from the top-left of `page`, 0-based) where the view draws it: `sizes` every page's (width, height) in points, `pixels` the pixels a point takes now, `spacing` the gap between two pages, `margins` the document's (left, top, right, bottom), `viewport_width` the viewport's width, `scroll` the scroll bars' (x, y). As QPdfView's multi-page mode: the pages one under the other from the top margin, each centred on the widest, the whole centred in a viewport wider than it."""
    left, top, right, _bottom = margins
    widest = max(w for w, _h in sizes) * pixels
    document_width = widest + left + right
    offset = max(0.0, (viewport_width - document_width) / 2.0)
    y = top + sum(h * pixels + spacing for _w, h in sizes[:page])
    page_width = sizes[page][0] * pixels
    x = offset + left + (widest - page_width) / 2.0
    x0, y0, x1, y1 = rect
    return QRectF(x + x0 * pixels - scroll[0], y + y0 * pixels - scroll[1], (x1 - x0) * pixels, (y1 - y0) * pixels)


class FramedPdfView(ZoomablePdfView):
    """A `ZoomablePdfView` that frames one rectangle of one page (`frame`)."""

    def __init__(self, parent=None, lang="en"):
        super().__init__(parent, lang)
        self.framed = None   # (page, (x0, y0, x1, y1)) or None

    def frame(self, page, rect):
        """Frames `rect` (PDF points from the top-left) of `page` (0-based) and scrolls to it; None takes the frame away."""
        self.framed = (page, tuple(rect)) if rect else None
        self.pageNavigator().jump(page, QPointF(0, max(0.0, (rect[1] if rect else 0) - 24)), 0)   # the clause a little under the top of the view
        self.viewport().update()

    def frame_rect(self):
        """Where the frame is drawn now, in the viewport -- None without one."""
        document = self.document()
        if self.framed is None or document is None or document.pageCount() == 0:
            return None
        page, rect = self.framed
        sizes = [(document.pagePointSize(p).width(), document.pagePointSize(p).height()) for p in range(document.pageCount())]
        m = self.documentMargins()
        pixels = self.scale() * self.logicalDpiX() / 72.0
        return page_rect_in_view(page, rect, sizes, pixels, self.pageSpacing(), (m.left(), m.top(), m.right(), m.bottom()),
                                 self.viewport().width(), (self.horizontalScrollBar().value(), self.verticalScrollBar().value()))

    def paintEvent(self, event):
        super().paintEvent(event)
        found = self.frame_rect()
        if found is None:
            return
        painter = QPainter(self.viewport())
        colour = QColor(theme.colour("accent"))
        painter.setPen(QPen(colour, 2.5))
        painter.drawRect(found.adjusted(-3, -3, 3, 3))
        painter.end()


def chapter_pdf(pdf, first, last):
    """The chapter's pages of `pdf`, written once into Woodcore's cache: its path, or None where the edition cannot be read."""
    target = usersettings.cache_dir("chapters") / ("%s_%d-%d.pdf" % (pdf.stem, first, last))
    if target.is_file() and target.stat().st_mtime >= pdf.stat().st_mtime:
        return target
    try:
        from pypdf import PdfReader, PdfWriter
        reader = PdfReader(str(pdf))
        writer = PdfWriter()
        for index in range(first - 1, min(last, len(reader.pages))):
            writer.add_page(reader.pages[index])
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "wb") as out:
            writer.write(out)
    except Exception:  # broad: an edition pypdf cannot cut is said by the reader, never raised into the event loop
        return None
    return target


class NormReader(QWidget):
    """The reader's window: the chapter, scrolled to the excerpt's page, the clause framed."""

    def __init__(self, t, lang):
        super().__init__(None, Qt.WindowType.Window)
        self.t = t
        self.resize(820, 1000)
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        self.missing = QLabel()
        self.missing.setWordWrap(True)
        self.missing.setProperty("callout", "warning")
        self.missing.hide()
        column.addWidget(self.missing)
        self.document = QPdfDocument(self)
        self.view = FramedPdfView(self, lang)
        self.view.setDocument(self.document)
        column.addWidget(self.view, 1)
        self.loaded = None

    def show_excerpt(self, excerpt):
        """The chapter of `excerpt`'s edition, at its page, its box framed. Returns False where the edition is not there (said in the window)."""
        pdf = excerpt.pdf()
        first, last = excerpt.chapter
        chapter = chapter_pdf(pdf, first, last) if pdf is not None else None
        if chapter is None:
            self.missing.setText(self.t("ct_reader_missing", file=excerpt.file))
            self.missing.show()
            self.show()
            return False
        self.missing.hide()
        if self.loaded != chapter:
            self.document.load(str(chapter))
            self.loaded = chapter
        self.setWindowTitle(self.t("ct_reader_title", edition=excerpt.edition, first=first, last=last))
        page = excerpt.page - first
        if not 0 <= page < self.document.pageCount():
            page = 0
        box = excerpt.box or (0, 0, self.document.pagePointSize(page).width(), self.document.pagePointSize(page).height())
        self.show()
        self.raise_()
        self.activateWindow()
        self.view.frame(page, box)
        return True


def reader(app, key="norm"):
    """The window's one reader, made the first time it is asked for."""
    found = _readers.get(key)
    try:
        if found is not None:
            found.isVisible()
            return found
    except RuntimeError:
        pass
    found = _readers[key] = NormReader(app.t, app.lang)
    return found
