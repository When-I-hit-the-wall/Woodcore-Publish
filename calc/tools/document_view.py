"""The view of one imported document in Woodcore's position plan tab (v0.114, docs/domain/position-plans.md §3.3sexies, docs/ui/window.md §10quater): every page of an architect's PDF -- or every layout of a CAD drawing, or the one page of an image or an SVG -- one after the other in a view that scrolls up and down, as a PDF reader shows them, and on each page what the plan tab needs of it.

**What it shows.** The pages laid out in rows, as many to a row as fit at the zoom: very close, one page across and scrolled; further out, two, three and more. Under each page its number, a box «dans les plans» -- ticked where at least one plan is drawn on the page --, and two buttons that turn the page by a quarter turn. On the page, the frame of every plan drawn on it -- its crop, or the page itself for a plan of the whole page --, dashed, with the plan's name; a frame chosen solid, the one in focus with its corners. The zoom is the bar's −, +, «largeur de page» and 100 %, or Ctrl + the wheel about the pointer; the wheel alone scrolls.

**Its tools (v0.116)**: «Sélection», the default and what Échap comes back to -- a click in a frame chooses it, the smallest holding the point, Ctrl adding one; a double click opens its plan; Suppr asks for the plans of the frames chosen to be archived; an edge or a corner dragged resizes the frame --; «Cadrer», a frame drawn on a page (an edge or a corner of a frame there resizes it too); «Calibrer», two points of one page. Several frames may stand on one page, each a plan: what a frame drawn means -- the crop of the page's whole-page plan, or a new plan -- is the caller's to decide.

**What it does not do: write.** The view emits what the engineer asked for -- a page ticked (`pageToggled`), a page to be turned (`rotateRequested`), a frame drawn (`cropDrawn`), a frame resized (`frameEdited`), two calibration points (`calibrated`), frames chosen (`frameSelected`), their plans to be archived (`framesDeleteRequested`), a plan's frame double-clicked (`planActivated`), a page chosen (`pageSelected`), the layers switched (`layersChanged`) -- and the caller writes the document and the plans and hands the view its document again with `set_document`. The one thing the view changes itself is its own copy of the document's layers, so that the preview follows a switch at once, before the caller has saved anything: the copy is an incremental update of the PDF (plan_documents.render_source, v0.116), the pages in view rendered first at the screen's resolution, what is shown staying until they come, and a configuration seen before taken from the renders kept without a render at all.

**What it renders** is calc/domains/plan_documents.py's `render_source`: a PDF as a cached copy with the layers switched off and every page turned, rendered by QtPdf; a CAD layout as an SVG, rendered by QtSvg; an image as it is. Only the pages in view are rendered, a coarse render of the whole page first (BASE_PX), then, once the view stops, a render at the screen's own resolution -- the whole page, or the part in view when the whole page would be too large. ⚠️ **QtPdf runs every call into PDFium under one lock** (plan_canvas.PdfPages, v0.48), so a render is asked for only when the one before it has come back, and a PDF is loaded or closed only while nothing renders. Renders are kept (`RENDERS`), so a page seen before shows at once.

**Its sheet units are the document's**: what plan_documents.page_size gives -- points for a PDF after rotation, pixels for an image, viewBox units for an SVG or a CAD layout -- and a page is laid out at its sheet size times `unit` display points per sheet unit (1, or a CAD drawing's hundredths of a millimetre in points), so a crop and a calibration come back in the page's own units, mapped exactly: a page starts on a whole pixel and nothing is rounded on the way.

No colour is written here: they are theme.py's tokens, read when the view paints.
"""

import copy
import functools
import json
import math
import threading
from dataclasses import dataclass, field
from pathlib import Path

import shiboken6
from PySide6.QtCore import QBuffer, QByteArray, QEvent, QIODevice, QObject, QPoint, QPointF, QRect, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen
from PySide6.QtPdf import QPdfDocument, QPdfDocumentRenderOptions, QPdfPageRenderer
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (QAbstractScrollArea, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QSplitter,
                               QToolButton, QToolTip, QVBoxLayout, QWidget)

import flowbar
import theme
from domains import cad
from domains import plan_documents
from plan_canvas import RenderCache, clip_bias, file_key
from document_view_render import BASE_PX, BOX_PX, BUTTON_PX, HANDLE_PX, ICONS, Job, RENDERS, SHARP_MAX_PX, STRIP_PX, Shown, TILE_MARGIN, _colour, _icon_for, _pixmap, PageAreaRenderMixin  # split out of this module (issue #30): every name it had is still importable from it
from document_view_input import CLICK_PX, DEFAULT_TOOL, TOOLS, _rounded, PageAreaInputMixin  # split out of this module (issue #30): every name it had is still importable from it

# --- measures -----------------------------------------------------------------------------------------------

# The white round the pages and between two of them, and the strip under a page that carries its number, its box and its two turning buttons, in screen pixels.
MARGIN_PX = 16
GAP_PX = 18
# A page is never laid out narrower than this, whatever the zoom: its strip has to hold its box, its number and its two buttons.
MIN_PAGE_PX = 84
# How far in the zoom goes: this many screen pixels per display point.
MAX_ZOOM = 24.0
# After a zoom, a scroll or a resize, the sharp renders are asked for once the view has stood still this long; a layer switched waits LAYER_DEBOUNCE_MS before the document is rendered again, so a run of switches is one render.
SETTLE_MS = 180
LAYER_DEBOUNCE_MS = 150
# Display points per sheet unit of a CAD layout: hundredths of a millimetre (calc/domains/cad.py's UNITS_PER_MM).
CAD_UNIT_PT = 72.0 / 25.4 / cad.UNITS_PER_MM


# --- words --------------------------------------------------------------------------------------------------

# The view's texts in the window's three languages, every key prefixed `dv_` -- merged by the plan tab into the window's STRINGS.
STRINGS = {
    "fr": {
        "dv_zoom_out": "Zoom arrière",
        "dv_zoom_in": "Zoom avant",
        "dv_fit_width": "Largeur de page",
        "dv_actual_size": "Taille réelle",
        "dv_zoom_use": "Ctrl + molette zoome autour du pointeur ; la molette seule fait défiler les pages.",
        "dv_select": "Sélection",
        "dv_select_use": "Un clic dans un cadre le choisit (Ctrl en ajoute un) ; nommez le plan et donnez-lui un étage dans le volet de droite. Double-clic : ouvre le plan. Suppr : archive les plans des cadres choisis.",
        "dv_crop": "Cadrer",
        "dv_crop_use": "Tirez un rectangle sur une page : le premier cadre recadre le plan de toute la page, chaque cadre suivant crée un nouveau plan sur la page. Tirer le bord ou le coin d'un cadre le redimensionne. Échap revient à la sélection.",
        "dv_calibrate": "Calibrer",
        "dv_calibrate_use": "Cliquez deux points d'une même page dont vous connaissez la distance réelle. Échap annule.",
        "dv_rotate_left": "Tourner à gauche (−90°)",
        "dv_rotate_right": "Tourner à droite (+90°)",
        "dv_rotate_use": "Tourne les pages sélectionnées d'un quart de tour ; ce qui est dessiné sur ces pages tourne avec elles.",
        "dv_layers": "Calques",
        "dv_layers_use": "Affiche ou masque les calques du document ; l'aperçu suit aussitôt.",
        "dv_layers_none": "Ce document n'a pas de calques.",
        "dv_layers_filter": "Filtrer les calques…",
        "dv_layers_all": "Tout",
        "dv_layers_nothing": "Aucun",
        "dv_layers_count": "{on} calque(s) affiché(s) sur {n}",
        "dv_in_plans": "Dans les plans",
        "dv_in_plans_use": "Cochée : au moins un plan est dessiné sur cette page. Cochez pour en faire un plan de toute la page, décochez pour archiver tous ses plans.",
        "dv_page": "Page {n}",
        "dv_busy": "Mise à jour de l'aperçu…",
        "dv_load_failed": "Le document ne peut pas être affiché.",
        "dv_empty": "Aucun document ouvert.",
        "dv_hint_crop": "Tirez un cadre sur une page, ou le bord d'un cadre pour le redimensionner.",
        "dv_hint_calibrate_first": "Cliquez le premier point.",
        "dv_hint_calibrate_second": "Cliquez le second point, sur la même page.",
    },
    "de": {
        "dv_zoom_out": "Verkleinern",
        "dv_zoom_in": "Vergrössern",
        "dv_fit_width": "Seitenbreite",
        "dv_actual_size": "Originalgrösse",
        "dv_zoom_use": "Ctrl + Mausrad zoomt um den Zeiger; das Mausrad allein blättert durch die Seiten.",
        "dv_select": "Auswahl",
        "dv_select_use": "Ein Klick in einen Rahmen wählt ihn (Ctrl fügt einen hinzu); den Plan im rechten Bereich benennen und ihm ein Geschoss geben. Doppelklick: öffnet den Plan. Entf: archiviert die Pläne der gewählten Rahmen.",
        "dv_crop": "Zuschneiden",
        "dv_crop_use": "Ziehen Sie ein Rechteck auf einer Seite: Der erste Rahmen schneidet den Plan der ganzen Seite zu, jeder weitere Rahmen erzeugt einen neuen Plan auf der Seite. Den Rand oder die Ecke eines Rahmens ziehen ändert seine Grösse. Esc kehrt zur Auswahl zurück.",
        "dv_calibrate": "Kalibrieren",
        "dv_calibrate_use": "Klicken Sie zwei Punkte derselben Seite, deren wirklichen Abstand Sie kennen. Esc bricht ab.",
        "dv_rotate_left": "Nach links drehen (−90°)",
        "dv_rotate_right": "Nach rechts drehen (+90°)",
        "dv_rotate_use": "Dreht die gewählten Seiten um eine Vierteldrehung; was auf ihnen gezeichnet ist, dreht mit.",
        "dv_layers": "Ebenen",
        "dv_layers_use": "Blendet die Ebenen des Dokuments ein oder aus; die Vorschau folgt sofort.",
        "dv_layers_none": "Dieses Dokument hat keine Ebenen.",
        "dv_layers_filter": "Ebenen filtern…",
        "dv_layers_all": "Alle",
        "dv_layers_nothing": "Keine",
        "dv_layers_count": "{on} von {n} Ebenen sichtbar",
        "dv_in_plans": "In den Plänen",
        "dv_in_plans_use": "Angekreuzt: Auf dieser Seite ist mindestens ein Plan gezeichnet. Ankreuzen macht einen Plan der ganzen Seite daraus, abwählen archiviert alle ihre Pläne.",
        "dv_page": "Seite {n}",
        "dv_busy": "Vorschau wird aktualisiert…",
        "dv_load_failed": "Das Dokument kann nicht angezeigt werden.",
        "dv_empty": "Kein Dokument geöffnet.",
        "dv_hint_crop": "Ziehen Sie einen Rahmen auf einer Seite, oder den Rand eines Rahmens, um seine Grösse zu ändern.",
        "dv_hint_calibrate_first": "Klicken Sie den ersten Punkt.",
        "dv_hint_calibrate_second": "Klicken Sie den zweiten Punkt, auf derselben Seite.",
    },
    "en": {
        "dv_zoom_out": "Zoom out",
        "dv_zoom_in": "Zoom in",
        "dv_fit_width": "Page width",
        "dv_actual_size": "Actual size",
        "dv_zoom_use": "Ctrl + wheel zooms about the pointer; the wheel alone scrolls the pages.",
        "dv_select": "Selection",
        "dv_select_use": "A click in a frame chooses it (Ctrl adds one); name the plan and give it a storey in the right pane. Double-click: opens the plan. Del: archives the plans of the frames chosen.",
        "dv_crop": "Crop",
        "dv_crop_use": "Drag a rectangle on a page: the first frame crops the plan of the whole page, every further frame makes a new plan on the page. Dragging a frame's edge or corner resizes it. Esc goes back to the selection.",
        "dv_calibrate": "Calibrate",
        "dv_calibrate_use": "Click two points of one page whose real distance you know. Esc cancels.",
        "dv_rotate_left": "Turn left (−90°)",
        "dv_rotate_right": "Turn right (+90°)",
        "dv_rotate_use": "Turns the selected pages by a quarter turn; what is drawn on them turns with them.",
        "dv_layers": "Layers",
        "dv_layers_use": "Shows or hides the document's layers; the preview follows at once.",
        "dv_layers_none": "This document has no layers.",
        "dv_layers_filter": "Filter the layers…",
        "dv_layers_all": "All",
        "dv_layers_nothing": "None",
        "dv_layers_count": "{on} of {n} layers shown",
        "dv_in_plans": "In the plans",
        "dv_in_plans_use": "Ticked: at least one plan is drawn on this page. Tick it to make a plan of the whole page, untick it to archive all its plans.",
        "dv_page": "Page {n}",
        "dv_busy": "Updating the preview…",
        "dv_load_failed": "The document cannot be shown.",
        "dv_empty": "No document open.",
        "dv_hint_crop": "Drag a frame on a page, or a frame's edge to resize it.",
        "dv_hint_calibrate_first": "Click the first point.",
        "dv_hint_calibrate_second": "Click the second point, on the same page.",
    },
}


def words(lang="fr"):
    """A `t(key, **values)` reading STRINGS in `lang` -- what the view uses where its caller hands it none."""
    table = STRINGS.get(lang, STRINGS["fr"])

    def t(key, **values):
        text = table[key]
        return text.format(**values) if values else text
    return t


# --- the symbols of the bar ------------------------------------------------------------------------------------


def icon(name, size):
    """One of the view's icons (ICONS) in the ink of the scheme: what another view of pages puts on its own buttons (annex_tab.py, issue #16)."""
    return _icon(name, size)


def _icon(name, size):
    return _icon_for(name, size, theme.colour("ink"))


# --- the pages ------------------------------------------------------------------------------------------------

@dataclass
class PageInfo:
    """One page as the view lays it out: its number, its size in sheet units after rotation, and the display points one sheet unit takes."""

    page: int
    width: float
    height: float
    unit: float = 1.0


class _PdfSource(QObject):
    """One PDF open for the view, rendered one page at a time -- QtPdf's lock (plan_canvas.PdfPages)."""

    rendered = Signal(object, QImage)

    def __init__(self, path, parent, data=None):
        super().__init__(parent)
        self.path = Path(path)
        # loaded from memory, never from the file: a PDF QtPdf holds open is a file Windows will not let the next export, NextCloud or the architect's next version replace
        self.buffer = QBuffer(self)
        self.buffer.setData(QByteArray(data if data is not None else self.path.read_bytes()))
        self.buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        self.document = QPdfDocument(self)
        self.document.load(self.buffer)
        self.renderer = QPdfPageRenderer(self)
        self.renderer.setRenderMode(QPdfPageRenderer.RenderMode.MultiThreaded)
        self.renderer.setDocument(self.document)
        self.renderer.pageRendered.connect(self.on_page_rendered)
        self.busy = None   # (request id, job)

    def send(self, job):
        options = QPdfDocumentRenderOptions()
        if job.clip is not None:
            bias = clip_bias()
            options.setScaledSize(job.full)
            options.setScaledClipRect(QRect(job.clip.x(), job.clip.y(), job.clip.width() + bias, job.clip.height() + bias))
        request = self.renderer.requestPage(job.page - 1, job.size, options)
        if request:
            self.busy = (request, job)
            return True
        return False

    def on_page_rendered(self, _page, _size, image, _options, request):
        if self.busy is None or request != self.busy[0]:
            return
        job = self.busy[1]
        self.busy = None
        self.rendered.emit(job, image)

    def close(self):
        """Closes the document at once -- only while nothing renders (see the module's docstring)."""
        shiboken6.delete(self.renderer)
        shiboken6.delete(self.document)
        self.buffer.close()
        shiboken6.delete(self)


class PageArea(PageAreaInputMixin, PageAreaRenderMixin, QAbstractScrollArea):
    """The pages themselves: laid out in rows by the zoom, painted, rendered as they come into view, and clicked. Everything it is told and everything it says goes through DocumentView, which carries the same signals."""

    pageToggled = Signal(int, bool)
    rotateRequested = Signal(int, int)
    cropDrawn = Signal(int, object)
    calibrated = Signal(int, object)
    planActivated = Signal(str)
    pageSelected = Signal(int)
    zoomChanged = Signal(float)
    hintChanged = Signal(str)
    toolChanged = Signal(str)
    frameSelected = Signal(list)            # the plans whose frames are chosen, the one in focus last; [] for none
    framesDeleteRequested = Signal(list)    # Suppr on the frames chosen
    frameEdited = Signal(int, str, object)  # page, plan, its frame (x, y, w, h) in the page's sheet units, an edge or a corner dragged

    # The strip under each page -- the box «dans les plans», the number, the turning buttons -- and its height: the plans' view's own. A view of pages that has none of them (the annexes' sources, annex_tab.SourcePages, issue #16) sets it to 0, and the pages are laid out with no room under them and painted with no strip.
    strip_px = STRIP_PX

    def __init__(self, parent=None, t=None):
        super().__init__(parent)
        self.t = t or words()
        self.pages = []          # [PageInfo]
        self.rects = {}          # page -> QRectF of the page, in content coordinates
        self.rows = []
        self.content = QSize(0, 0)
        self.zoom = 1.0
        self.kind = None
        self.sources = {}        # page -> (path, file_key); a PDF's under 0
        self.images = {}         # page -> QImage, an image document's own
        self.base = {}           # page -> Shown
        self.sharp = {}          # page -> Shown
        self.queue = []
        self.svg_running = False
        self.svg_renderers = {}
        self.pdf = None
        self.retired = []
        self.pending_pdf = None
        self.used = set()
        self.other_used = set()   # pages carrying a plan of the other kind: a hollow marker beside the tick
        self.crops = {}
        self.selected = []
        self.frames = []          # the plans whose frames are chosen, the one in focus last (v0.116)
        self.tool = DEFAULT_TOOL
        self.sent = 0             # renders asked of QtPdf or QtSvg since the view was made -- what a test counts to say a render was served from the cache
        self.drag = None          # ("crop", page, start content point, current) | ("pan", start pos, start scroll) | ("frame", page, plan, edges, rect, start, current, moved)
        self.calib = None         # (page, (x, y)) the first point
        self.pointer = None
        self.settle = QTimer(self)
        self.settle.setSingleShot(True)
        self.settle.setInterval(SETTLE_MS)
        self.settle.timeout.connect(lambda: self.schedule(settled=True))
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.horizontalScrollBar().valueChanged.connect(self.on_scrolled)
        self.verticalScrollBar().valueChanged.connect(self.on_scrolled)
        self.horizontalScrollBar().setSingleStep(40)
        self.verticalScrollBar().setSingleStep(40)

    # -- the pages and their sources --

    def set_pages(self, infos, kind, sources, keep_view=True, data=None):
        """Lays out `infos` (PageInfo) rendered from `sources` ({page: path}, a PDF's under 0, its bytes `data` where the loader read them already). A page whose size changed loses its renders; every other one keeps what it shows until the new source's render comes, so a layer switched never flashes a blank page."""
        old = {info.page: (info.width, info.height) for info in self.pages}
        anchor = self.anchor() if keep_view and self.pages else None
        for info in infos:
            if old.get(info.page) != (info.width, info.height):
                self.base.pop(info.page, None)
                self.sharp.pop(info.page, None)
        valid = {info.page for info in infos}
        for table in (self.base, self.sharp):
            for page in [p for p in table if p not in valid]:
                del table[page]
        self.selected = [p for p in self.selected if p in valid]
        self.pages = list(infos)
        self.kind = kind
        self.sources = {page: (Path(path), file_key(path)) for page, path in sources.items()}
        self.queue = []
        if kind == "pdf":
            self.use_pdf(Path(sources[0]), data)
        else:
            self.drop_pdf()
        # an image shown as it is, unturned, is painted from the file itself; turned, it is an SVG and rendered like one
        self.images = {page: QImage(str(path)) for page, path in sources.items() if kind == "image" and Path(path).suffix.lower() in (".png", ".jpg", ".jpeg")}
        live = {str(path) for path, _key in self.sources.values()}
        self.svg_renderers = {k: v for k, v in self.svg_renderers.items() if k in live}
        if not keep_view or anchor is None:
            self.zoom = self.clamp(self.fit_page_zoom())
            self.layout()
            self.horizontalScrollBar().setValue(0)
            self.verticalScrollBar().setValue(0)
        else:
            self.layout()
            self.restore(anchor)
        self.zoomChanged.emit(self.zoom)
        if keep_view and anchor is not None:
            # the same document again, a layer switched or a page turned, the view where it was: the pages in view at the screen's resolution first, and at once -- nothing moved, there is nothing to wait for -- and the coarse renders after them (v0.116)
            self.settle.stop()
            self.schedule(settled=True, sharp_first=True)
        else:
            self.schedule(settled=False)
            self.settle.start()
        self.viewport().update()

    def clear(self):
        self.pages, self.rects, self.rows = [], {}, []
        self.base, self.sharp, self.images, self.sources, self.queue = {}, {}, {}, {}, []
        self.frames = []
        self.drop_pdf()
        self.content = QSize(0, 0)
        self.update_bars()
        self.viewport().update()

    def use_pdf(self, path, data=None):
        if self.pdf is not None and self.pdf.path == path:
            return
        if self.pdf is not None:
            self.retired.append(self.pdf)
            self.pdf = None
        if self.busy():
            self.pending_pdf = (path, data)
        else:
            self.collect()
            self.open_pdf(path, data)

    def open_pdf(self, path, data=None):
        self.pdf = _PdfSource(path, self, data)
        self.pdf.rendered.connect(self.on_rendered)

    def drop_pdf(self):
        if self.pdf is not None:
            self.retired.append(self.pdf)
            self.pdf = None
        self.pending_pdf = None
        self.collect()

    def busy(self):
        return any(p.busy is not None for p in (self.pdf, *self.retired) if p is not None)

    def collect(self):
        """Closes the PDFs left and opens the one waiting -- only while nothing renders."""
        if self.busy():
            return
        for old in self.retired:
            old.close()
        self.retired = []
        if self.pending_pdf is not None and self.kind == "pdf":
            (path, data), self.pending_pdf = self.pending_pdf, None
            self.open_pdf(path, data)
            self.schedule(settled=not self.settle.isActive())
        self.kick()

    def rendering(self):
        """Whether anything is still to be rendered or on its way."""
        return bool(self.queue) or self.busy() or self.svg_running or self.pending_pdf is not None

    # -- the layout --

    def info(self, page):
        return next((i for i in self.pages if i.page == page), None)

    def display_size(self, info, zoom=None):
        z = self.zoom if zoom is None else zoom
        return info.width * info.unit * z, info.height * info.unit * z

    def min_zoom(self):
        if not self.pages:
            return 0.01
        narrowest = min(i.width * i.unit for i in self.pages)
        return MIN_PAGE_PX / max(narrowest, 1e-9)

    def clamp(self, zoom):
        return max(self.min_zoom(), min(MAX_ZOOM, zoom))

    def fit_width_zoom(self):
        if not self.pages:
            return 1.0
        widest = max(i.width * i.unit for i in self.pages)
        return max(self.viewport().width() - 2 * MARGIN_PX, 1) / max(widest, 1e-9)

    def fit_page_zoom(self):
        """The zoom that shows the largest page whole: as wide as the view and as tall."""
        if not self.pages:
            return 1.0
        tallest = max(i.height * i.unit for i in self.pages)
        tall = max(self.viewport().height() - 2 * MARGIN_PX - self.strip_px, 1) / max(tallest, 1e-9)
        return min(self.fit_width_zoom(), tall)

    def actual_zoom(self):
        """100 %: a point of the page is a point of the screen."""
        return self.logicalDpiX() / 72.0

    def layout(self):
        """The pages in rows: as many to a row as fit the view's width at the zoom, each row centred, every page starting on a whole pixel."""
        width = self.viewport().width()
        avail = max(width - 2 * MARGIN_PX, 1)
        rows, row, used = [], [], 0.0
        for info in self.pages:
            w, _h = self.display_size(info)
            if row and used + GAP_PX + w > avail:
                rows.append(row)
                row, used = [], 0.0
            used = w if not row else used + GAP_PX + w
            row.append(info)
        if row:
            rows.append(row)
        widths = [sum(self.display_size(i)[0] for i in r) + GAP_PX * (len(r) - 1) for r in rows]
        content_w = max(widths, default=0) + 2 * MARGIN_PX
        total_w = max(width, content_w)
        self.rects, y = {}, float(MARGIN_PX)
        for r, rw in zip(rows, widths):
            x = (total_w - rw) / 2
            height = 0.0
            for info in r:
                w, h = self.display_size(info)
                self.rects[info.page] = QRectF(round(x), round(y), w, h)
                x += w + GAP_PX
                height = max(height, h)
            y += height + self.strip_px + GAP_PX
        self.rows = [[i.page for i in r] for r in rows]
        content_h = (y - GAP_PX + MARGIN_PX) if rows else 0
        self.content = QSize(math.ceil(content_w), math.ceil(content_h))
        self.update_bars()

    def update_bars(self):
        view = self.viewport().size()
        for bar, content, page in ((self.horizontalScrollBar(), self.content.width(), view.width()),
                                   (self.verticalScrollBar(), self.content.height(), view.height())):
            bar.setPageStep(max(page, 1))
            bar.setRange(0, max(0, content - page))

    def scroll(self):
        return QPointF(self.horizontalScrollBar().value(), self.verticalScrollBar().value())

    def pages_per_row(self):
        return max((len(r) for r in self.rows), default=0)

    def anchor(self, at=None):
        """(page, u, v, at): the page under the viewport point `at` (its middle by default) or the nearest one, and where on it that point is, as fractions of the page -- what a zoom keeps under the pointer."""
        at = QPointF(at) if at is not None else QPointF(self.viewport().width() / 2, self.viewport().height() / 2)
        point = at + self.scroll()
        page = self.page_at(point, nearest=True)
        if page is None:
            return None
        rect = self.rects[page]
        return page, (point.x() - rect.left()) / rect.width(), (point.y() - rect.top()) / rect.height(), at

    def restore(self, anchor):
        if anchor is None or anchor[0] not in self.rects:
            return
        page, u, v, at = anchor
        rect = self.rects[page]
        self.horizontalScrollBar().setValue(round(rect.left() + u * rect.width() - at.x()))
        self.verticalScrollBar().setValue(round(rect.top() + v * rect.height() - at.y()))

    def set_zoom(self, zoom, at=None):
        """Zooms to `zoom` screen pixels per display point, keeping the point of the page under the viewport point `at` (the view's middle by default) where it is."""
        zoom = self.clamp(zoom)
        anchor = self.anchor(at)
        self.zoom = zoom
        self.layout()
        self.restore(anchor)
        self.zoomChanged.emit(self.zoom)
        self.view_moved()

    def resizeEvent(self, event):
        anchor = self.anchor() if self.pages else None
        super().resizeEvent(event)
        if self.pages:
            self.zoom = self.clamp(self.zoom)
            self.layout()
            self.restore(anchor)
            self.view_moved()

    def scrollContentsBy(self, _dx, _dy):
        self.viewport().update()

    def on_scrolled(self, *_args):
        self.view_moved()

    def view_moved(self):
        self.viewport().update()
        self.schedule(settled=False)
        self.settle.start()

    # -- where things are --


    # -- rendering --


    # -- painting --


    # -- the mouse and the keys --


# --- the layers -----------------------------------------------------------------------------------------------

class LayersPanel(QWidget):
    """The document's layers, each with a box: a filter, «Tout» and «Aucun» (over the layers the filter shows), and every switch said at once (`toggled`) -- there is no OK button, the preview follows."""

    toggled = Signal(list, bool)   # the layers' names, and whether they are now shown

    def __init__(self, parent=None, t=None):
        super().__init__(parent)
        self.t = t or words()
        self.filling = False
        v = QVBoxLayout(self)
        v.setContentsMargins(6, 0, 0, 0)
        self.title = QLabel()
        self.title.setObjectName("cardTitle")
        v.addWidget(self.title)
        self.filter = QLineEdit()
        self.filter.setClearButtonEnabled(True)
        self.filter.textChanged.connect(self.apply_filter)
        v.addWidget(self.filter)
        row = QHBoxLayout()
        self.all_button = QPushButton()
        self.none_button = QPushButton()
        self.all_button.clicked.connect(lambda: self.set_all(True))
        self.none_button.clicked.connect(lambda: self.set_all(False))
        row.addWidget(self.all_button)
        row.addWidget(self.none_button)
        row.addStretch(1)
        v.addLayout(row)
        self.list = QListWidget()
        self.list.itemChanged.connect(self.on_item_changed)
        v.addWidget(self.list, 1)
        self.count = QLabel()
        self.count.setObjectName("cardNote")
        v.addWidget(self.count)
        self.retranslate(self.t)

    def retranslate(self, t):
        self.t = t
        self.title.setText(t("dv_layers"))
        self.filter.setPlaceholderText(t("dv_layers_filter"))
        self.all_button.setText(t("dv_layers_all"))
        self.none_button.setText(t("dv_layers_nothing"))
        self.update_count()

    def set_layers(self, layers):
        """Shows `layers` ([{"name", "on"}]), keeping the filter."""
        self.filling = True
        self.list.clear()
        for layer in layers:
            item = QListWidgetItem(layer["name"])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if layer["on"] else Qt.CheckState.Unchecked)
            self.list.addItem(item)
        self.filling = False
        self.apply_filter(self.filter.text())
        self.update_count()

    def layers(self):
        return [{"name": self.list.item(i).text(), "on": self.list.item(i).checkState() == Qt.CheckState.Checked} for i in range(self.list.count())]

    def apply_filter(self, text):
        words_ = text.casefold().split()
        for i in range(self.list.count()):
            item = self.list.item(i)
            item.setHidden(not all(w in item.text().casefold() for w in words_))

    def set_all(self, on):
        state = Qt.CheckState.Checked if on else Qt.CheckState.Unchecked
        names = []
        self.filling = True
        for i in range(self.list.count()):
            item = self.list.item(i)
            if not item.isHidden() and item.checkState() != state:
                item.setCheckState(state)
                names.append(item.text())
        self.filling = False
        self.update_count()
        if names:
            self.toggled.emit(names, on)

    def on_item_changed(self, item):
        if self.filling:
            return
        self.update_count()
        self.toggled.emit([item.text()], item.checkState() == Qt.CheckState.Checked)

    def update_count(self):
        layers = self.layers()
        self.count.setText(self.t("dv_layers_count", on=sum(1 for l in layers if l["on"]), n=len(layers)) if layers else self.t("dv_layers_none"))


# --- the loader -----------------------------------------------------------------------------------------------

class _Loader(QObject):
    """Reads a document's pages, sizes and layers and makes its render sources (plan_documents.render_source) in a thread of its own: writing a PDF's copy with its layers stated takes the better part of a second on an architect's plan set, and a CAD layout is drawn by ezdxf -- the window must not stop for either."""

    done = Signal(int, object, object)   # generation, result, error

    def start(self, generation, place, doc, with_layers):
        thread = threading.Thread(target=self.run, args=(generation, place, doc, with_layers), daemon=True)
        thread.start()
        return thread

    def run(self, generation, place, doc, with_layers):
        try:
            result = load(place, doc, with_layers)
        except Exception as exc:  # broad: a DocumentError, a CadError, or a file that will not be read -- handed to the window, which says it
            self.done.emit(generation, None, exc)
            return
        self.done.emit(generation, result, None)


def load(place, doc, with_layers=True):
    """What the view needs of `doc`, Qt-free: {"infos": [PageInfo], "kind", "sources": {page: path} (a PDF's whole copy under 0), "data": the PDF's bytes or None, "layers": [...] or None}."""
    count = plan_documents.page_count(place, doc)
    unit = CAD_UNIT_PT if doc["kind"] == "cad" else 1.0
    infos = [PageInfo(p, *plan_documents.page_size(place, doc, p), unit) for p in range(1, count + 1)]
    data = None
    if doc["kind"] == "pdf":
        sources = {0: plan_documents.render_source(place, doc)}
        data = Path(sources[0]).read_bytes()
    else:
        sources = {p: plan_documents.render_source(place, doc, p) for p in range(1, count + 1)}
    layers = plan_documents.layers(place, doc) if with_layers else None
    return {"infos": infos, "kind": doc["kind"], "sources": sources, "layers": layers, "data": data}


def document_key(doc):
    """What the view's rendering depends on: the file, its hash, every page's rotation and the layers switched off."""
    if doc is None:
        return None
    return json.dumps([doc.get("id"), doc.get("file"), doc.get("sha256"), [int(p.get("rotation", 0)) for p in doc.get("pages", [])],
                       sorted(set(doc.get("layers_off", [])))], ensure_ascii=False)


def place_of(here):
    """The (root, plans folder) a plan_documents call is given, read once here so the loader's thread asks nothing of a Project."""
    if isinstance(here, plan_documents.Place):
        return here
    if here is None:
        import project
        here = project.current()
    return plan_documents.Place(Path(here.root), Path(here.plans_dir))


# --- the view -------------------------------------------------------------------------------------------------

class DocumentView(QWidget):
    """One imported document, every page in a view that scrolls, and the bar and the layers beside it (the module's docstring).

    Signals: `pageToggled(page, on)`, `rotateRequested(page, delta_degrees)`, `cropDrawn(page, (x, y, w, h))` and `calibrated(page, [(x1, y1), (x2, y2)])` in the page's sheet units, `planActivated(plan_id)` (a double click in a frame), `pageSelected(page)`, `frameSelected([plan ids])` (the frames chosen with «Sélection», the one in focus last), `framesDeleteRequested([plan ids])` (Suppr), `frameEdited(page, plan_id, (x, y, w, h))` (an edge or a corner of a frame dragged), `layersChanged(layers_off)`, `loaded()` once a document's pages are laid out, `failed(exception)` where it cannot be read."""

    pageToggled = Signal(int, bool)
    rotateRequested = Signal(int, int)
    cropDrawn = Signal(int, object)
    calibrated = Signal(int, object)
    planActivated = Signal(str)
    pageSelected = Signal(int)
    frameSelected = Signal(list)
    framesDeleteRequested = Signal(list)
    frameEdited = Signal(int, str, object)
    layersChanged = Signal(list)
    loaded = Signal()
    failed = Signal(object)

    def __init__(self, parent=None, t=None, lang="fr"):
        super().__init__(parent)
        self.t = t or words(lang)
        self.here = None
        self.doc = None
        self.key = None
        self.generation = 0
        self.loading = None        # the generation being loaded
        self.reload_wanted = False
        self._fresh = False
        self._with_layers = False
        self.layers = []
        self.describe_error = lambda exc: self.t("dv_load_failed")
        self.loader = _Loader(self)
        self.loader.done.connect(self.on_loaded)
        self.layer_timer = QTimer(self)
        self.layer_timer.setSingleShot(True)
        self.layer_timer.setInterval(LAYER_DEBOUNCE_MS)
        self.layer_timer.timeout.connect(lambda: self.start_load(with_layers=False))

        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(2)
        self.bar = flowbar.FlowWidget()
        flowbar.FlowLayout(self.bar, spacing=flowbar.BAR_SPACING)
        v.addWidget(self.bar)
        self.banner = QLabel()
        self.banner.setProperty("callout", "danger")
        self.banner.setWordWrap(True)
        self.banner.hide()
        v.addWidget(self.banner)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.area = PageArea(t=self.t)
        self.panel = LayersPanel(t=self.t)
        self.panel.toggled.connect(self.on_layers_toggled)
        self.panel.hide()
        self.splitter.addWidget(self.area)
        self.splitter.addWidget(self.panel)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setChildrenCollapsible(False)
        v.addWidget(self.splitter, 1)
        for name in ("pageToggled", "rotateRequested", "cropDrawn", "calibrated", "planActivated", "pageSelected", "frameSelected", "framesDeleteRequested", "frameEdited"):
            getattr(self.area, name).connect(getattr(self, name))
        self.area.pageSelected.connect(lambda _page: self.update_buttons())
        self.area.zoomChanged.connect(self.show_zoom)
        self.area.hintChanged.connect(self.show_hint)
        self.area.toolChanged.connect(self.on_tool_changed)
        self.build_bar()
        self.retranslate(self.t)
        self.update_buttons()

    # -- the bar --

    def tool(self, icon, checkable=False):
        button = QToolButton()
        button.setIcon(_icon(icon, flowbar.symbol_px()))
        button.setCheckable(checkable)
        button.setAutoRaise(True)
        flowbar.size_tool(button)
        return button

    def build_bar(self):
        self.zoom_out_button = self.tool("zoom-out")
        self.zoom_in_button = self.tool("zoom-in")
        self.fit_button = self.tool("fit-width")
        self.actual_button = self.tool("actual")
        self.zoom_label = QLabel()
        self.zoom_label.setMinimumWidth(self.fontMetrics().horizontalAdvance("8888 %") + 6)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.fit_button.clicked.connect(self.fit_width)
        self.actual_button.clicked.connect(self.actual_size)
        self.select_button = self.tool("select", checkable=True)
        self.select_button.setChecked(True)
        self.crop_button = self.tool("crop", checkable=True)
        self.calibrate_button = self.tool("calibrate", checkable=True)
        self.select_button.clicked.connect(lambda _on: self.set_tool(DEFAULT_TOOL))
        self.crop_button.clicked.connect(lambda on: self.set_tool("crop" if on else None))
        self.calibrate_button.clicked.connect(lambda on: self.set_tool("calibrate" if on else None))
        self.left_button = self.tool("undo")
        self.right_button = self.tool("redo")
        self.left_button.clicked.connect(lambda: self.rotate_selected(-90))
        self.right_button.clicked.connect(lambda: self.rotate_selected(90))
        self.layers_button = self.tool("layers", checkable=True)
        self.layers_button.toggled.connect(self.show_layers)
        self.busy_label = QLabel()
        self.busy_label.setObjectName("cardNote")
        self.busy_label.hide()
        self.hint_label = QLabel()
        self.hint_label.setObjectName("cardNote")
        layout = self.bar.layout()
        layout.addWidget(flowbar.tool_group([self.zoom_out_button, self.zoom_label, self.zoom_in_button, self.fit_button, self.actual_button], "zoom"))
        layout.addWidget(flowbar.tool_group([self.select_button, self.crop_button, self.calibrate_button], "tools"))
        layout.addWidget(flowbar.tool_group([self.left_button, self.right_button], "rotate"))
        layout.addWidget(flowbar.tool_group([self.layers_button], "layers"))
        layout.addWidget(self.busy_label)
        layout.addWidget(self.hint_label)

    def retranslate(self, t):
        """Says everything again in the language of `t`."""
        self.t = t
        self.area.t = t
        self.panel.retranslate(t)
        zoom_use = t("dv_zoom_use")
        flowbar.set_tip(self.zoom_out_button, t("dv_zoom_out"), zoom_use)
        flowbar.set_tip(self.zoom_in_button, t("dv_zoom_in"), zoom_use)
        flowbar.set_tip(self.fit_button, t("dv_fit_width"), zoom_use)
        flowbar.set_tip(self.actual_button, t("dv_actual_size"), zoom_use)
        flowbar.set_tip(self.select_button, t("dv_select"), t("dv_select_use"))
        flowbar.set_tip(self.crop_button, t("dv_crop"), t("dv_crop_use"))
        flowbar.set_tip(self.calibrate_button, t("dv_calibrate"), t("dv_calibrate_use"))
        flowbar.set_tip(self.left_button, t("dv_rotate_left"), t("dv_rotate_use"))
        flowbar.set_tip(self.right_button, t("dv_rotate_right"), t("dv_rotate_use"))
        flowbar.set_tip(self.layers_button, t("dv_layers"), t("dv_layers_use") if self.layers else t("dv_layers_none"))
        self.busy_label.setText(t("dv_busy"))
        self.area.say_hint()
        self.area.viewport().update()

    def update_buttons(self):
        has = bool(self.area.pages)
        for button in (self.zoom_out_button, self.zoom_in_button, self.fit_button, self.actual_button, self.select_button, self.crop_button, self.calibrate_button):
            button.setEnabled(has)
        for button in (self.left_button, self.right_button):
            button.setEnabled(bool(self.area.selected))
        self.layers_button.setEnabled(bool(self.layers))
        if not self.layers and self.layers_button.isChecked():
            self.layers_button.setChecked(False)

    def show_zoom(self, zoom):
        self.zoom_label.setText(f"{round(100 * zoom / self.area.actual_zoom())} %")

    def show_hint(self, text):
        self.hint_label.setText(text)

    # -- the document --

    def set_document(self, here, doc):
        """Shows `doc` (a plan document, calc/domains/plan_documents.py) of the project `here` -- a Project or a plan_documents.Place. The same document again, nothing in it changed that the rendering depends on, is left as it is; a page turned or a layer switched is rendered again, what was shown staying until its new render comes; another document starts afresh. `None` clears the view."""
        if doc is None:
            self.clear()
            return
        key = document_key(doc)
        place = place_of(here)
        same_file = self.doc is not None and self.doc.get("id") == doc.get("id") and self.doc.get("file") == doc.get("file") and self.here == place
        self.doc = copy.deepcopy(doc)
        if same_file and key == self.key:
            return
        self.here = place
        self.key = key
        if not same_file:
            self.area.selected = []
            self.area.used = set()
            self.area.crops = {}
            self.area.set_frames([])
            self.area.set_tool(DEFAULT_TOOL)
            self.on_tool_changed(DEFAULT_TOOL)
        self.start_load(with_layers=not same_file, fresh=not same_file)

    def document(self):
        """A copy of the document as the view holds it -- its layers as the panel last switched them."""
        return copy.deepcopy(self.doc)

    def clear(self):
        self.doc, self.key, self.here, self.layers = None, None, None, []
        self.generation += 1
        self._fresh = self._with_layers = False
        self.busy_label.hide()
        self.layer_timer.stop()
        self.area.clear()
        self.panel.set_layers([])
        self.banner.hide()
        self.update_buttons()

    def start_load(self, with_layers=True, fresh=False):
        """Loads the document in the loader's thread -- one load at a time; asked again while one runs, it runs once more when that one is done."""
        self.generation += 1
        self._fresh = self._fresh or fresh
        self._with_layers = self._with_layers or with_layers
        if self.loading is not None:
            self.reload_wanted = True
            return
        self.loading = self.generation
        self.busy_label.show()
        self.loader.start(self.generation, self.here, copy.deepcopy(self.doc), self._with_layers)

    def on_loaded(self, generation, result, error):
        self.loading = None
        if self.reload_wanted:
            self.reload_wanted = False
            if self.doc is not None:
                self.start_load()   # the document changed while it was read: read it again, as it is now
                return
        if generation != self.generation or self.doc is None:
            self.busy_label.setVisible(self.loading is not None)
            return
        self.busy_label.hide()
        fresh, self._fresh, self._with_layers = self._fresh, False, False
        if error is not None:
            self.banner.setText(self.describe_error(error))
            self.banner.show()
            self.failed.emit(error)
            return
        self.banner.hide()
        if result["layers"] is not None:
            off = set(self.doc.get("layers_off", []))
            self.layers = [{"name": layer["name"], "on": layer["name"] not in off} for layer in result["layers"]]
            self.panel.set_layers(self.layers)
        self.area.set_pages(result["infos"], result["kind"], result["sources"], keep_view=not fresh, data=result.get("data"))
        flowbar.set_tip(self.layers_button, self.t("dv_layers"), self.t("dv_layers_use") if self.layers else self.t("dv_layers_none"))
        self.update_buttons()
        self.loaded.emit()

    def is_busy(self):
        """Whether the document is being read, or a page is still to be rendered."""
        return self.loading is not None or self.layer_timer.isActive() or self.area.settle.isActive() or self.area.rendering()

    # -- what the caller tells the view --

    def set_used_pages(self, pages):
        """Ticks «dans les plans» on `pages` and on no other."""
        self.area.used = set(pages)
        self.area.viewport().update()

    def used_pages(self):
        return sorted(self.area.used)

    def set_other_pages(self, pages):
        """Paints a small hollow marker beside the tick of `pages`, the pages that carry a plan of the other kind (a fire plan, seen from the position plans' tab, and the other way round). Nothing changes where it is not called."""
        self.area.other_used = set(pages)
        self.area.viewport().update()

    def other_pages(self):
        return sorted(self.area.other_used)

    def set_crops(self, crops):
        """{page: [{"plan": id, "rect": (x, y, w, h) in the page's sheet units, "label": "P01 – Name – EG"}]}: the crop of every plan, drawn on its page. A crop may carry `"other": True` -- a plan of the other kind, shown for reference -- and then `"kind"`, the word its label is prefixed with: it is painted muted and dotted and is never hit."""
        self.area.crops = {int(page): list(items) for page, items in (crops or {}).items()}
        drawn = {item.get("plan") for items in self.area.crops.values() for item in items if not item.get("other")}
        self.area.set_frames([p for p in self.area.frames if p in drawn])
        self.area.viewport().update()

    def set_tool(self, tool):
        """"select" (also None, the default), "crop" or "calibrate"."""
        self.area.set_tool(tool)
        self.on_tool_changed(self.area.tool)
        self.area.setFocus()

    def on_tool_changed(self, tool):
        self.select_button.setChecked(tool == "select")
        self.crop_button.setChecked(tool == "crop")
        self.calibrate_button.setChecked(tool == "calibrate")

    def current_tool(self):
        return self.area.tool

    def selected_pages(self):
        return list(self.area.selected)

    def selected_frames(self):
        """The plans whose frames are chosen, the one in focus last."""
        return list(self.area.frames)

    def select_frames(self, plans, emit=False):
        """The frames of `plans` chosen -- those drawn --, said (`frameSelected`) only where `emit`."""
        drawn = {item.get("plan") for items in self.area.crops.values() for item in items if not item.get("other")}
        self.area.set_frames([p for p in plans if p in drawn], emit=emit)

    def select_pages(self, pages):
        self.area.selected = [p for p in pages if p in self.area.rects]
        self.area.viewport().update()
        self.update_buttons()

    def rotate_selected(self, delta):
        for page in self.area.selected:
            self.rotateRequested.emit(page, delta)

    # -- the zoom --

    def zoom(self):
        return self.area.zoom

    def set_zoom(self, zoom, at=None):
        self.area.set_zoom(zoom, at)

    def zoom_in(self):
        self.area.set_zoom(self.area.zoom * 1.25)

    def zoom_out(self):
        self.area.set_zoom(self.area.zoom / 1.25)

    def fit_width(self):
        self.area.set_zoom(self.area.fit_width_zoom(), QPointF(self.area.viewport().width() / 2, 0))

    def actual_size(self):
        self.area.set_zoom(self.area.actual_zoom())

    def pages_per_row(self):
        return self.area.pages_per_row()

    # -- the layers --

    def show_layers(self, on):
        opening = bool(on) and bool(self.layers) and not self.panel.isVisible()
        self.panel.setVisible(bool(on) and bool(self.layers))
        if opening:
            total = sum(self.splitter.sizes()) or self.width()
            side = min(260, max(total // 3, 160))
            self.splitter.setSizes([max(total - side, 1), side])
        if self.layers_button.isChecked() != bool(on):
            self.layers_button.setChecked(bool(on))

    def on_layers_toggled(self, names, on):
        if self.doc is None:
            return
        for name in names:
            plan_documents.set_layer(self.doc, name, on)
        self.layers = self.panel.layers()
        self.key = document_key(self.doc)
        self.layersChanged.emit(list(self.doc.get("layers_off", [])))
        self.busy_label.show()
        self.layer_timer.start()

    # -- where things are, for the caller and the tests --

    def page_rect(self, page):
        """The rectangle of `page` in the page area's viewport."""
        return self.area.rects[page].translated(-self.area.scroll())

    def viewport_point(self, page, x, y):
        """The point of the page area's viewport over the sheet point (x, y) of `page`."""
        return self.area.to_content(page, x, y) - self.area.scroll()

    def sheet_point(self, position):
        """(page, x, y) under the viewport point `position`, or None between the pages."""
        point = QPointF(position) + self.area.scroll()
        page = self.area.page_at(point)
        if page is None:
            return None
        return (page, *self.area.to_sheet(page, point))
