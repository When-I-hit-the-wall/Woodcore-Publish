"""The annexes tab's pages: the PDF read, the source's pages shown and the frames found, split out of annex_tab.py (issue #30): every name is still importable from annex_tab.
"""

import threading
from pathlib import Path
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QObject, QRectF, QSize, QSizeF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QKeySequence, QPainter, QPen, QShortcut
from PySide6.QtPdf import QPdfDocument
from PySide6.QtWidgets import (
    QAbstractItemView, QAbstractScrollArea, QButtonGroup, QComboBox, QFileDialog, QHBoxLayout, QHeaderView, QInputDialog, QLabel, QMessageBox,
    QPushButton, QRadioButton, QSpinBox, QSplitter, QToolButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)
import document_view  # the plans' view of a document's pages, a source's pages here (issue #16)
import theme
from domains import annex as model  # the one module that reads and writes Woodcore-Datei/annexes/


# The anchor band and the frame, drawn over the page: the report's own frame colour (lib/calc-engine.typ, annex-frame-colour), and the yellow of a highlight for the title found.
FRAME_COLOUR = theme.colour("annex-frame")


TITLE_COLOUR = theme.colour("annex-title")


class Pdf:
    """One source's PDF, read once while it is unchanged: its bytes, pypdf's reader and outline for the geometry -- the same functions the export runs -- and QtPdf for the pictures, loaded from the bytes so that nothing holds the file open."""

    def __init__(self, path):
        self.path = Path(path)
        self.data = self.path.read_bytes()
        self.sha = model.file_hash(self.path)
        self.reader = model.reader(self.path)
        self.marks = model.outline(self.reader)
        self.text = model.has_text(self.reader)
        self.sizes = []
        for page in self.reader.pages:
            left, bottom, right, top = model.page_box(page)
            self.sizes.append((right - left, top - bottom))
        self._bytes = QByteArray(self.data)
        self._buffer = QBuffer()
        self._buffer.setData(self._bytes)
        self._buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        self.document = QPdfDocument()
        self.document.load(self._buffer)
        self._cache = {}

    def pages(self):
        return len(self.sizes)

    def render(self, page, width_px):
        """Page `page` (1-based) as a picture `width_px` wide."""
        key = (page, int(width_px))
        if key not in self._cache:
            w, h = self.sizes[page - 1]
            size = QSize(max(1, int(width_px)), max(1, int(width_px * h / w)))
            self._cache = {k: v for k, v in list(self._cache.items())[-6:]}
            # a page that draws no ground of its own is rendered transparent, and read dark on the dark scheme: a page is paper, white in both schemes
            rendered = self.document.render(page - 1, size)
            paper = QImage(rendered.size(), QImage.Format.Format_ARGB32_Premultiplied)
            paper.fill(QColor("white"))
            if not rendered.isNull():
                painter = QPainter(paper)
                painter.drawImage(0, 0, rendered)
                painter.end()
            self._cache[key] = paper
        return self._cache[key]

    def close(self):
        self.document.close()
        self._buffer.close()


class SourcePages(document_view.PageArea):
    """A source's pages, all of them (issue #16: «défiler ses pages et zoomer / dézoomer ; dézoomé suffisamment, 2, 3 pages ou plus côte à côte»): the plans' own view of a document's pages (document_view.PageArea) -- laid out in rows by the zoom, rendered as they come into view, Ctrl and the wheel to zoom about the pointer, the middle button to pan --, with no strip under its pages (`strip_px`), and over them what an excerpt is: the title found (`band`), the frame (`frame`) on the page in focus (`page`), the source's other excerpts dashed (`others`), and in the mode «Cadre trouvé» the frames the page's drawing holds (`found`), the one under the pointer filled.

    It says what the tab did with the one page of v0.115: a click (`clicked`) and a drag (`dragged`), in points below and right of the top-left corner of the page they were made on -- which becomes `page` first --, the measure calc/domains/annex.py works in; `modifiers` the keys held. `doc` is the source shown (the tab's Pdf), `pdf` the view's renderer; the PDF it renders is the tab's own bytes (Pdf.data), never its file."""

    clicked = Signal(float, float)
    dragged = Signal(float, float, float, float)
    pageChosen = Signal(int)
    climbed = Signal()

    strip_px = 0

    def __init__(self, t=None):
        super().__init__(t=t)
        self.doc = None       # the source shown (Pdf) -- `pdf` is the plans' view's own renderer (document_view.PageArea)
        self.page = 1
        self.band = None      # the height of the title found, in points below the top of `page`
        self.frame = None     # [x, y, w, h] in points, on `page`
        self.others = []      # [(page, [x, y, w, h])] the source's other excerpts
        self.found = {}       # {page: [[x, y, w, h], …]} the frames the page's drawing holds, the smallest first (annex.find_rects)
        self.finding = False  # the mode «Cadre trouvé»: the frames under the pointer offered
        self.hover = None     # (page, [rects under the pointer, the smallest first]) in that mode
        self.level = 0        # which of them: 0 the smallest, Alt and the wheel or a right click climb (D-013)
        self.press = None     # (page, content point) of a left press
        self.rubber = None    # (page, start, current) content points of a frame being drawn
        self.modifiers = Qt.KeyboardModifier.NoModifier

    def update(self):
        self.viewport().update()

    def show_page(self, pdf, page):
        """`pdf`'s pages laid out -- afresh where it is another PDF, or another version of the same --, and `page` brought into view."""
        if pdf is not self.doc:
            self.doc = pdf
            self.found, self.hover, self.level = {}, None, 0
            self.drop_pdf()
            self.base.clear()
            self.sharp.clear()
            if pdf is None:
                self.clear()
            else:
                infos = [document_view.PageInfo(i + 1, w, h, 1.0) for i, (w, h) in enumerate(pdf.sizes)]
                self.set_pages(infos, "pdf", {0: pdf.path}, keep_view=False, data=pdf.data)
                self.set_zoom(self.fit_width_zoom())
        self.page = max(1, min(page, len(pdf.sizes))) if pdf is not None else 1
        self.bring(self.page)
        self.update()

    def bring(self, page):
        """`page` scrolled into view where it is not."""
        rect = self.rects.get(page)
        if rect is None:
            return
        view = QRectF(self.scroll(), QSizeF(self.viewport().size()))
        if not view.intersects(rect):
            self.verticalScrollBar().setValue(int(rect.top()) - document_view.MARGIN_PX)

    def fit_width(self):
        self.set_zoom(self.fit_width_zoom())

    def hovered_rect(self):
        if not self.hover or not self.hover[1]:
            return None
        return self.hover[1][min(self.level, len(self.hover[1]) - 1)]

    def climb(self, steps=1):
        """The frame round the one offered (D-013): a print report's cell, then its table, then the block round it; back down the other way, the smallest again past the largest."""
        if self.hover and self.hover[1]:
            self.level = (self.level + steps) % len(self.hover[1])
            self.update()
            self.climbed.emit()

    def box(self, page, rect):
        x, y, w, h = rect
        return QRectF(self.to_content(page, x, y), self.to_content(page, x + w, y + h)).normalized()

    def paint_overlay(self, painter, page, rect):
        frame = QColor(FRAME_COLOUR)
        for where, other in self.others:
            if where == page:
                painter.setPen(QPen(frame, 1, Qt.PenStyle.DashLine))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(self.box(page, other))
        if page == self.page and self.band is not None:
            y = self.to_content(page, 0, self.band).y()
            painter.fillRect(QRectF(rect.left(), y - 2, rect.width(), 4), QColor(TITLE_COLOUR))
        if page == self.page and self.frame is not None:
            painter.setPen(QPen(frame, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.box(page, self.frame))
        if self.finding:
            offered = self.hovered_rect() if self.hover and self.hover[0] == page else None
            for found in self.found.get(page, []):
                painter.setPen(QPen(QColor(theme.colour("muted")), 1, Qt.PenStyle.DotLine))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(self.box(page, found))
            if offered is not None:
                ink = QColor(theme.colour("primary"))
                fill = QColor(ink)
                fill.setAlpha(40)
                painter.setPen(QPen(ink, 2))
                painter.setBrush(fill)
                painter.drawRect(self.box(page, offered))
        if self.rubber is not None and self.rubber[0] == page:
            painter.setPen(QPen(frame, 1, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRectF(self.rubber[1], self.rubber[2]).normalized())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            return super().mousePressEvent(event)   # the pan
        point = self.content_point(event)
        page = self.page_at(point)
        if page is None:
            return
        if event.button() == Qt.MouseButton.RightButton and self.finding:
            self.climb()
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if page != self.page:
            self.page = page
            self.pageChosen.emit(page)
        self.modifiers = event.modifiers()
        start = self.clamped(page, point)
        self.press = (page, start)
        self.rubber = None

    def mouseMoveEvent(self, event):
        if self.drag is not None and self.drag[0] == "pan":
            return super().mouseMoveEvent(event)
        point = self.content_point(event)
        if self.press is not None:
            page, start = self.press
            self.rubber = (page, start, self.clamped(page, point))
            self.update()
            return
        if self.finding:
            page = self.page_at(point)
            under = model.rects_at(self.found.get(page, []), *self.to_sheet(page, point)) if page is not None else []
            hover = (page, under) if under else None
            if hover != self.hover:
                if not hover or not self.hover or hover[0] != self.hover[0] or hover[1][:1] != self.hover[1][:1]:
                    self.level = 0
                self.hover = hover
                self.update()

    def mouseReleaseEvent(self, event):
        if self.drag is not None and self.drag[0] == "pan":
            return super().mouseReleaseEvent(event)
        if self.press is None or event.button() != Qt.MouseButton.LeftButton:
            return
        page, start = self.press
        end = self.clamped(page, self.content_point(event))
        self.press, self.rubber = None, None
        self.page = page
        x0, y0 = self.to_sheet(page, start)
        x1, y1 = self.to_sheet(page, end)
        if abs(end.x() - start.x()) < 6 and abs(end.y() - start.y()) < 6:
            self.clicked.emit(x1, y1)
        else:
            self.dragged.emit(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
        self.update()

    def wheelEvent(self, event):
        if self.finding and event.modifiers() & Qt.KeyboardModifier.AltModifier:
            delta = event.angleDelta().y() or event.angleDelta().x()   # Alt turns a wheel sideways on some systems
            if delta:
                self.climb(1 if delta > 0 else -1)
            event.accept()
            return
        super().wheelEvent(event)

    def viewportEvent(self, event):
        if event.type() == event.Type.ToolTip:
            return True   # the plans' tooltips are of their strip, which these pages have not
        return QAbstractScrollArea.viewportEvent(self, event)


class _Finder(QObject):
    """The frames of one page of a source, found off the window's thread (annex.find_rects_in): a dense page of a print report takes a moment, and the window stays live meanwhile. `found` carries (source's sha, page, rects)."""

    found = Signal(str, int, object)

    def ask(self, data, sha, page):
        def run():
            try:
                rects = model.find_rects_in(data, page)
            except Exception:   # broad: a page that cannot be read offers no frame, and stops nothing
                rects = []
            self.found.emit(sha, page, rects)
        threading.Thread(target=run, daemon=True).start()
