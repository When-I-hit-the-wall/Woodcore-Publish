"""PageArea's geometry, rendering and painting -- where a page, a frame and a handle stand, what is rendered and kept, how a page is painted -- a mixin of methods moved verbatim out of calc/tools/document_view.py (issue #30). PageArea names it among its bases.
"""

import functools
import math
from dataclasses import dataclass, field
from pathlib import Path
from PySide6.QtCore import QBuffer, QByteArray, QEvent, QIODevice, QObject, QPoint, QPointF, QRect, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen
from PySide6.QtSvg import QSvgRenderer
import flowbar
import theme
from plan_canvas import RenderCache, clip_bias, file_key


STRIP_PX = 24


BOX_PX = 14


BUTTON_PX = 18


# The coarse render of a whole page, this many pixels along its longer side: what shows at once and while the view moves.
BASE_PX = 480


# A render at the screen's resolution is of the whole page up to this many pixels, and of the part in view beyond (with TILE_MARGIN of the view round it).
SHARP_MAX_PX = 12_000_000


TILE_MARGIN = 0.25


# The renders kept in this session, shared by every view.
RENDERS = RenderCache(192 * 2**20)


# How near a frame's edge, in screen pixels, a press takes that edge (or that corner) to resize the frame rather than to choose it or to draw another.
HANDLE_PX = 5


ICONS = {
    "zoom-in": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
               '<circle cx="10" cy="10" r="6.5" fill="none" stroke="{c}" stroke-width="1.8"/>'
               '<path d="M15 15 L21 21 M7 10 H13 M10 7 V13" fill="none" stroke="{c}" stroke-width="1.8"/></svg>',
    "zoom-out": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
                '<circle cx="10" cy="10" r="6.5" fill="none" stroke="{c}" stroke-width="1.8"/>'
                '<path d="M15 15 L21 21 M7 10 H13" fill="none" stroke="{c}" stroke-width="1.8"/></svg>',
    "fit-width": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
                 '<path d="M3 4 V20 M21 4 V20 M6.5 12 H17.5" fill="none" stroke="{c}" stroke-width="1.8"/>'
                 '<polygon points="5.5,12 9,9 9,15" fill="{c}"/><polygon points="18.5,12 15,9 15,15" fill="{c}"/></svg>',
    "actual": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
              '<path d="M4.5 8.5 L7.5 6 V18 M16.5 8.5 L19.5 6 V18" fill="none" stroke="{c}" stroke-width="2" stroke-linejoin="round"/>'
              '<circle cx="12" cy="9.5" r="1.4" fill="{c}"/><circle cx="12" cy="15" r="1.4" fill="{c}"/></svg>',
    "calibrate": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
                 '<path d="M3 15 L15 3 L21 9 L9 21 Z" fill="none" stroke="{c}" stroke-width="1.6" stroke-linejoin="round"/>'
                 '<path d="M6.5 11.5 L9 14 M9.5 8.5 L11 10 M12.5 5.5 L15 8" fill="none" stroke="{c}" stroke-width="1.4"/></svg>',
    "layers": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
              '<path d="M12 3 L21 8 L12 13 L3 8 Z" fill="none" stroke="{c}" stroke-width="1.6" stroke-linejoin="round"/>'
              '<path d="M3 12 L12 17 L21 12 M3 16 L12 21 L21 16" fill="none" stroke="{c}" stroke-width="1.6" stroke-linejoin="round"/></svg>',
}


@functools.lru_cache(maxsize=64)
def _icon_for(name, size, ink):
    if name in ICONS:
        return flowbar.svg_text_icon(ICONS[name].format(c=ink), size)
    return flowbar.icon(name, size, ink)


@functools.lru_cache(maxsize=64)
def _pixmap(name, size, ink):
    return _icon_for(name, size, ink).pixmap(QSize(size, size))


def _colour(name, alpha=None):
    colour = QColor(theme.colour(name))
    if alpha is not None:
        colour.setAlpha(alpha)
    return colour


@dataclass(eq=False)
class Job:
    """One render asked for: the coarse whole page (`base`) or one at the screen's resolution (`sharp`), of `page` of the source `source` (its file_key), `full` the whole page's size in pixels at that render's scale and `clip` the part of it rendered (pixels), None for the whole page."""

    kind: str
    page: int
    source: tuple
    path: Path
    full: QSize
    clip: QRect = None
    key: tuple = field(default=())

    @property
    def size(self):
        return self.clip.size() if self.clip is not None else self.full

    @property
    def norm(self):
        """The part of the page the render shows, as fractions of the page."""
        if self.clip is None:
            return QRectF(0, 0, 1, 1)
        w, h = self.full.width(), self.full.height()
        return QRectF(self.clip.x() / w, self.clip.y() / h, self.clip.width() / w, self.clip.height() / h)


@dataclass
class Shown:
    """A render shown on a page: its image, the part of the page it covers (fractions), its pixels per sheet unit and the source it was made of."""

    image: QImage
    norm: QRectF
    scale: float
    source: tuple


class PageAreaRenderMixin:
    """Methods of document_view.PageArea, moved verbatim (issue #30): the class names this mixin among its bases."""

    def page_at(self, point, nearest=False):
        """The page whose rectangle holds the content point `point`; with `nearest`, the nearest page where none holds it."""
        for page, rect in self.rects.items():
            if rect.contains(point):
                return page
        if not nearest or not self.rects:
            return None

        def distance(rect):
            dx = max(rect.left() - point.x(), 0, point.x() - rect.right())
            dy = max(rect.top() - point.y(), 0, point.y() - rect.bottom())
            return dx * dx + dy * dy
        return min(self.rects, key=lambda p: distance(self.rects[p]))

    def per_unit(self, page):
        """Screen pixels per sheet unit of `page` at the zoom."""
        return self.info(page).unit * self.zoom

    def to_sheet(self, page, point):
        """The sheet point (x, y) of `page` under the content point `point`."""
        rect, k = self.rects[page], self.per_unit(page)
        return ((point.x() - rect.left()) / k, (point.y() - rect.top()) / k)

    def to_content(self, page, x, y):
        rect, k = self.rects[page], self.per_unit(page)
        return QPointF(rect.left() + x * k, rect.top() + y * k)

    def strip(self, page):
        """(box, number, left button, right button) of the strip under `page`, in content coordinates."""
        rect = self.rects[page]
        top = rect.bottom() + (STRIP_PX - BUTTON_PX) / 2
        box = QRectF(rect.left(), rect.bottom() + (STRIP_PX - BOX_PX) / 2, BOX_PX, BOX_PX)
        right = QRectF(rect.right() - BUTTON_PX, top, BUTTON_PX, BUTTON_PX)
        left = QRectF(right.left() - BUTTON_PX - 2, top, BUTTON_PX, BUTTON_PX)
        number = QRectF(box.right() + 4, rect.bottom(), max(left.left() - box.right() - 8, 0), STRIP_PX)
        return box, number, left, right

    def crop_rects(self, page):
        """[(plan, content rect, label)] of the crops drawn on `page` -- the plans of the kind the view is for; a crop that carries "other" (a plan of the other kind, shown for reference) is not among them, so it is never hit."""
        out = []
        for crop in self.crops.get(page, []):
            if crop.get("other"):
                continue
            x, y, w, h = crop["rect"]
            a, b = self.to_content(page, x, y), self.to_content(page, x + w, y + h)
            out.append((crop.get("plan", ""), QRectF(a, b).normalized(), crop.get("label", crop.get("plan", ""))))
        return out

    def other_crop_rects(self, page):
        """[(content rect, label)] of the crops of the other kind of plan drawn on `page`, the label prefixed by the kind the crop's dict names (`"kind"`): shown muted, and never hit."""
        out = []
        for crop in self.crops.get(page, []):
            if not crop.get("other"):
                continue
            x, y, w, h = crop["rect"]
            a, b = self.to_content(page, x, y), self.to_content(page, x + w, y + h)
            label = crop.get("label", crop.get("plan", ""))
            kind = crop.get("kind", "")
            out.append((QRectF(a, b).normalized(), f"{kind} {label}".strip() if kind else label))
        return out

    def frame_handle(self, point):
        """(page, plan, edges, content rect) of the frame whose edge or corner lies within HANDLE_PX of the content point `point` -- `edges` a set of "l", "r", "t", "b", two of them at a corner --, or None. Of several, a frame chosen first, then the smallest (v0.116)."""
        found = []
        for page, rect in self.rects.items():
            if not rect.adjusted(-HANDLE_PX, -HANDLE_PX, HANDLE_PX, HANDLE_PX).contains(point):
                continue
            for plan, r, _label in self.crop_rects(page):
                if not r.adjusted(-HANDLE_PX, -HANDLE_PX, HANDLE_PX, HANDLE_PX).contains(point):
                    continue
                edges = set()
                dl, dr = abs(point.x() - r.left()), abs(point.x() - r.right())
                dt, db = abs(point.y() - r.top()), abs(point.y() - r.bottom())
                if min(dl, dr) <= HANDLE_PX:
                    edges.add("l" if dl <= dr else "r")
                if min(dt, db) <= HANDLE_PX:
                    edges.add("t" if dt <= db else "b")
                if edges:
                    found.append((plan not in self.frames, r.width() * r.height(), page, plan, frozenset(edges), r))
        if not found:
            return None
        best = min(found, key=lambda item: item[:2])
        return best[2], best[3], set(best[4]), best[5]


    def set_frames(self, plans, emit=True):
        """The frames of `plans` chosen -- the last in focus -- and said (`frameSelected`) where that changed."""
        plans = [p for p in dict.fromkeys(plans) if p]
        if plans == self.frames:
            return
        self.frames = plans
        self.viewport().update()
        if emit:
            self.frameSelected.emit(list(plans))

    def hit(self, point):
        """What lies under the content point `point`: ("tick" | "left" | "right" | "number", page), ("crop", page, plan), ("page", page) or None."""
        for page, rect in self.rects.items():
            box, number, left, right = self.strip(page)
            if box.adjusted(-3, -3, 3, 3).contains(point):
                return ("tick", page)
            if left.contains(point):
                return ("left", page)
            if right.contains(point):
                return ("right", page)
            if rect.contains(point):
                inside = [(r.width() * r.height(), plan) for plan, r, _label in self.crop_rects(page) if r.contains(point)]
                if inside:
                    return ("crop", page, min(inside)[1])
                return ("page", page)
            if number.contains(point):
                return ("number", page)
        return None

    def source(self, page):
        return self.sources.get(0 if self.kind == "pdf" else page)

    def visible_pages(self, margin=0.0):
        view = QRectF(self.scroll(), self.viewport().size())
        if margin:
            view = view.adjusted(0, -view.height() * margin, 0, view.height() * margin)
        return [info.page for info in self.pages if info.page in self.rects and self.rects[info.page].intersects(view)]

    def schedule(self, settled=False, sharp_first=False):
        """The renders the view needs, in the order they are to come: the coarse page for every page in view (and a little beyond), then, once the view has stood still, the page at the screen's resolution for every page in view -- or those first, with `sharp_first`, where the view did not move and what it shows is to be replaced (a layer switched): the page the engineer is looking at is the one that has to change at once. Any render kept is shown at once and not asked for; what was waiting and is no longer in view is forgotten."""
        if self.kind is None or not self.pages:
            self.queue = []
            return
        ratio = self.viewport().devicePixelRatioF()
        near, seen = self.visible_pages(margin=1.0), self.visible_pages()
        bases, sharps = [], []
        for page in near:
            src = self.source(page)
            if src is None or page in self.images:
                continue
            path, key = src
            info = self.info(page)
            scale = BASE_PX / max(info.width, info.height)
            full = QSize(max(1, round(info.width * scale)), max(1, round(info.height * scale)))
            shown = self.base.get(page)
            if shown is not None and shown.source == key and shown.image.size() == full:
                continue
            job = Job("base", page, key, path, full)
            job.key = ("dv", "base", key, page, full.width(), full.height())
            if not self.from_cache(job):
                bases.append(job)
        if settled:
            view = QRectF(self.scroll(), self.viewport().size())
            for page in (p for p in seen if p not in self.images):
                job = self.sharp_job(page, view, ratio)
                if job is not None and not self.from_cache(job):
                    sharps.append(job)
            for page in [p for p in self.sharp if p not in seen]:
                del self.sharp[page]
        # The pages in view first -- their coarse render where they have none yet, then their render at the screen's resolution --, the coarse renders of the pages round them last: one render of an architect's page holds QtPdf's lock 0.2 to 0.5 s whatever its size (measured, docs/architecture/performance.md, v0.117), so ten pages round the view rendered coarse before the one looked at kept it blurred for seconds.
        in_view = [job for job in bases if job.page in seen]
        around = [job for job in bases if job.page not in seen]
        self.queue = (sharps + in_view + around) if sharp_first else (in_view + sharps + around)
        self.kick()

    def sharp_job(self, page, view, ratio):
        src = self.source(page)
        if src is None:
            return None
        path, key = src
        info = self.info(page)
        scale = self.per_unit(page) * ratio
        width, height = max(1, round(info.width * scale)), max(1, round(info.height * scale))
        if max(width, height) <= BASE_PX * 1.02:
            self.sharp.pop(page, None)
            return None   # the coarse render is already this sharp
        rect = self.rects[page]
        seen = rect.intersected(view)
        full = QSize(width, height)
        clip = None
        if width * height > SHARP_MAX_PX:
            mx, my = view.width() * TILE_MARGIN, view.height() * TILE_MARGIN
            want = seen.adjusted(-mx, -my, mx, my).intersected(rect)
            sx, sy = width / rect.width(), height / rect.height()
            x0, y0 = max(0, math.floor((want.left() - rect.left()) * sx)), max(0, math.floor((want.top() - rect.top()) * sy))
            x1, y1 = min(width, math.ceil((want.right() - rect.left()) * sx)), min(height, math.ceil((want.bottom() - rect.top()) * sy))
            if (x1 - x0) * (y1 - y0) <= 0:
                return None
            clip = QRect(x0, y0, x1 - x0, y1 - y0)
        job = Job("sharp", page, key, path, full, clip)
        job.key = ("dv", "sharp", key, page, width, height) + ((clip.x(), clip.y(), clip.width(), clip.height()) if clip else ())
        shown = self.sharp.get(page)
        if shown is not None and shown.source == key and abs(shown.scale / (width / info.width) - 1) < 1e-3:
            need = QRectF((seen.left() - rect.left()) / rect.width(), (seen.top() - rect.top()) / rect.height(),
                          seen.width() / rect.width(), seen.height() / rect.height())
            pixel = 1.0 / max(width, height)
            if shown.norm.adjusted(-pixel, -pixel, pixel, pixel).contains(need):
                return None   # what is shown already covers what is seen
        return job

    def from_cache(self, job):
        kept = RENDERS.get(job.key)
        if kept is None:
            return False
        self.show(job, kept.image)
        return True

    def show(self, job, image):
        info = self.info(job.page)
        if info is None:
            return
        current = self.source(job.page)
        if current is None or current[1] != job.source:
            return
        shown = Shown(image, job.norm, job.full.width() / info.width, job.source)
        if job.kind == "base":
            self.base[job.page] = shown
            old = self.sharp.get(job.page)
            if old is not None and old.source != job.source:
                del self.sharp[job.page]
        else:
            self.sharp[job.page] = shown
        self.viewport().update()

    def kick(self):
        """Sends the next render: to QtPdf when nothing is on its way, or to QtSvg at the next turn of the event loop."""
        if not self.queue:
            return
        if self.kind == "pdf":
            if self.pdf is None or self.busy():
                return
            while self.queue:
                job = self.queue.pop(0)
                if self.pdf.send(job):
                    self.sent += 1
                    return
        elif not self.svg_running:
            self.svg_running = True
            QTimer.singleShot(0, self, self.run_svg)

    def run_svg(self):
        self.svg_running = False
        if not self.queue:
            return
        job = self.queue.pop(0)
        self.sent += 1
        renderer = self.svg_renderers.get(str(job.path))
        if renderer is None:
            renderer = QSvgRenderer(str(job.path))
            self.svg_renderers[str(job.path)] = renderer
        image = QImage(job.size, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(theme.qcolor("paper"))
        if renderer.isValid():
            painter = QPainter(image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            if job.clip is not None:
                painter.translate(-job.clip.x(), -job.clip.y())
            renderer.render(painter, QRectF(0, 0, job.full.width(), job.full.height()))
            painter.end()
        RENDERS.put(job.key, image, job.norm, job.full.width())
        self.show(job, image)
        self.kick()

    def on_rendered(self, job, image):
        if not image.isNull():
            image = image.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
            RENDERS.put(job.key, image, job.norm, job.full.width())
            self.show(job, image)
        if self.retired or self.pending_pdf is not None:
            QTimer.singleShot(0, self, self.collect)   # not inside the signal of a PDF collect may close
        else:
            self.kick()

    def paintEvent(self, _event):
        painter = QPainter(self.viewport())
        painter.fillRect(self.viewport().rect(), _colour("desk"))
        if not self.pages:
            painter.setPen(_colour("muted"))
            painter.drawText(self.viewport().rect(), Qt.AlignmentFlag.AlignCenter, self.t("dv_empty"))
            return
        painter.translate(-self.scroll())
        view = QRectF(self.scroll(), self.viewport().size())
        font = QFont(self.font())
        small = QFont(font)
        if font.pointSizeF() > 0:
            small.setPointSizeF(max(font.pointSizeF() - 1, 6))
        for info in self.pages:
            rect = self.rects.get(info.page)
            if rect is None or not rect.adjusted(0, 0, 0, self.strip_px).intersects(view):
                continue
            self.paint_page(painter, info.page, rect, small)
            self.paint_overlay(painter, info.page, rect)
        self.paint_gesture(painter)

    def paint_overlay(self, painter, page, rect):
        """What a view of its own draws over `page`, laid at `rect` (content coordinates) -- nothing here; the annexes' excerpts and the frames found in a page (annex_tab.SourcePages, issue #16)."""

    def paint_page(self, painter, page, rect, small):
        painter.fillRect(rect, _colour("paper"))
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        image = self.images.get(page)
        if image is not None and not image.isNull():
            painter.drawImage(rect, image)
        else:
            for shown in (self.base.get(page), self.sharp.get(page)):
                if shown is not None:
                    n = shown.norm
                    target = QRectF(rect.left() + n.x() * rect.width(), rect.top() + n.y() * rect.height(), n.width() * rect.width(), n.height() * rect.height())
                    painter.drawImage(target, shown.image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        selected = page in self.selected
        painter.setPen(QPen(_colour("primary" if selected else "line-strong"), 2.5 if selected else 1.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)
        # the frames of the plans drawn on the page -- a plan of the whole page framed by the page itself -- dashed; a frame chosen solid and tinted, the one in focus with its handles (v0.116)
        pen = QPen(_colour("accent-strong"), 1.6, Qt.PenStyle.DashLine)
        chosen_pen = QPen(_colour("primary"), 2.4)
        painter.setFont(small)
        metrics = painter.fontMetrics()
        focus = self.frames[-1] if self.frames else None
        for plan, crop, label in self.crop_rects(page):
            chosen = plan in self.frames
            shown = crop.adjusted(1, 1, -1, -1) if crop.contains(rect.adjusted(1, 1, -1, -1)) else crop   # a frame the size of the page drawn just inside its edge
            if chosen:
                painter.fillRect(shown, _colour("primary", 28))
            painter.setPen(chosen_pen if chosen else pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(shown)
            if label:
                text = metrics.elidedText(label, Qt.TextElideMode.ElideRight, max(int(shown.width()) - 8, 24))
                box = QRectF(shown.left() + 2, shown.top() + 2, metrics.horizontalAdvance(text) + 8, metrics.height() + 2)
                painter.fillRect(box, _colour("card", 225))
                painter.setPen(_colour("primary" if chosen else "accent-strong"))
                painter.drawText(box, Qt.AlignmentFlag.AlignCenter, text)
            if plan == focus:
                painter.setPen(QPen(_colour("primary"), 1.0))
                painter.setBrush(_colour("paper"))
                for corner in (shown.topLeft(), shown.topRight(), shown.bottomLeft(), shown.bottomRight()):
                    painter.drawRect(QRectF(corner.x() - 3, corner.y() - 3, 6, 6))
                painter.setBrush(Qt.BrushStyle.NoBrush)
        # the crops of the other kind of plan, for reference: muted, dotted, never clicked
        other_pen = QPen(_colour("muted"), 1.2, Qt.PenStyle.DotLine)
        for crop, label in self.other_crop_rects(page):
            painter.setPen(other_pen)
            painter.drawRect(crop)
            if label:
                text = metrics.elidedText(label, Qt.TextElideMode.ElideRight, max(int(crop.width()) - 8, 24))
                painter.setPen(_colour("muted"))
                painter.drawText(QRectF(crop.left() + 4, crop.bottom() - metrics.height() - 3, max(crop.width() - 8, 1), metrics.height() + 2), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)
        # the strip: the box «dans les plans», the number, the two turning buttons -- none in a view that has no strip (`strip_px`)
        if not self.strip_px:
            return
        box, number, left, right = self.strip(page)
        used = page in self.used
        painter.setPen(QPen(_colour("ink-soft"), 1.2))
        painter.setBrush(_colour("primary") if used else _colour("paper"))
        painter.drawRoundedRect(box, 2.5, 2.5)
        if page in self.other_used:
            painter.setPen(QPen(_colour("ink-soft"), 1.2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(box.right() + 7, box.center().y()), 3.5, 3.5)
        if used:
            painter.setPen(QPen(_colour("on-primary"), 1.8))
            painter.drawPolyline([QPointF(box.left() + 3, box.center().y()), QPointF(box.left() + 6, box.bottom() - 3.5), QPointF(box.right() - 3, box.top() + 3.5)])
        painter.setPen(_colour("ink" if selected else "ink-soft"))
        text = self.t("dv_page", n=page)
        if metrics.horizontalAdvance(text) > number.width():
            text = str(page)
        painter.drawText(number, Qt.AlignmentFlag.AlignCenter, text)
        size = BUTTON_PX - 2
        for name, where in (("undo", left), ("redo", right)):
            if self.pointer is not None and where.contains(self.pointer):
                painter.fillRect(where, _colour("accent-soft"))
            painter.drawPixmap(where.adjusted(1, 1, -1, -1).toRect(), _pixmap(name, size, theme.colour("ink")))

    def paint_gesture(self, painter):
        if self.drag is not None and self.drag[0] == "crop":
            _kind, page, start, current = self.drag
            painter.setPen(QPen(_colour("override"), 1.6, Qt.PenStyle.DashLine))
            painter.setBrush(_colour("override", 30))
            painter.drawRect(QRectF(start, current).normalized())
        if self.drag is not None and self.drag[0] == "frame" and self.drag[7]:
            painter.setPen(QPen(_colour("override"), 1.8))
            painter.setBrush(_colour("override", 30))
            painter.drawRect(self.drag[6])
        if self.calib is not None and self.calib[0] in self.rects:
            page, (x, y) = self.calib
            first = self.to_content(page, x, y)
            painter.setPen(QPen(_colour("override"), 1.6))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(first, 4, 4)
            if self.pointer is not None:
                painter.drawLine(first, self.clamped(page, self.pointer))
