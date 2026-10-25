"""The right pane of a tab of calculation, a service: its modules (spec docs/requirements/completed/2026-10-23-onglets-types-et-services.md, ARCH-001; spec 2026-10-22-onglet-neige-type, REQ-008 to REQ-010; spec 2026-10-23-neige-correctifs-issues-96-99, UI-004).

`Modules` is one service that holds module_pane.ModulePane and gives it its modules, each described (`ModuleSpec`), never subclassed: «État du calcul» -- in red what stops the calculation, in orange what is only said, in green that every input is there and the calculation made --, «Résultats» -- what is computed, never an input, a row a value, then the instance's tables where it has them (a build-up's layers, the wind's forces) --, the domain's drawing and its interactive chart where it has them, and the excerpts of the norm pinned from a bubble and the blocks of the form pinned by their 📌 (spec 2026-10-23-onglet-vent-briques, ARCH-005), under «Résultats», each once. It reads what the domain said off the context (`messages`, `instance`, `drawing`, `chart`), refreshes in the phase `computed`, pins and takes out an excerpt when the context says so, and lights the results a field goes into. No word, no number and no rule of a domain here.
"""

import traceback

from PySide6.QtCore import QByteArray, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QGridLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

import module_pane
import norm_bubble
import richtext
import theme
from domains import contracts
from tab_host import Hover, Service, _n, excerpt_module_id, excerpt_of_module

# The prefix of the id of a block pinned, beside an excerpt's `x:` (tab_host.excerpt_module_id): what `Modules.restore` tells them apart by
BLOCK_PREFIX = "b:"

# The right pane's narrowest: a module's header and a drawing stay readable beside a wide form
MODULES_MIN_WIDTH = 340


class _StateBody(QWidget):
    """The module «État du calcul» (REQ-008): in red what stops the calculation, in orange what is only said, in green that every input is there and the calculation made -- a click on a message takes the engineer to its field, which flashes."""

    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.column = QVBoxLayout(self)
        self.column.setContentsMargins(0, 0, 0, 0)
        self.column.setSpacing(4)
        self.rows = []

    def refresh(self):
        for row in self.rows:
            row.setParent(None)
        self.rows = []
        messages = self.ctx.messages
        errors = [m for m in messages if m.severity == "error"]
        lines = [(m, "danger") for m in errors]
        if not errors and self.ctx.instance is not None:
            lines.append((next((m for m in messages if m.severity == "ok"), None), "ok"))   # the domain's own words where it says one (the permanent loads' «every layer has its weight»)
        lines += [(m, "warning") for m in messages if m.severity == "warning"]
        lines += [(m, "warning") for m in messages if m.severity == "info"]
        for message, callout in lines:
            text = ("✓ " + (self.ctx.t("ct_complete") if message is None else self.ctx.message_text(message))) if callout == "ok" else self.ctx.message_text(message)
            label = QLabel(richtext.subscripts(text))   # C_e as C<sub>e</sub> (UI-003)
            label.setWordWrap(True)
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setProperty("callout", callout if callout != "ok" else "info")
            if callout == "ok":
                label.setStyleSheet("color: %s;" % theme.colour("ok"))
            if message is not None and message.field:
                label.setCursor(Qt.CursorShape.PointingHandCursor)
                label.mousePressEvent = lambda _event, field=message.field: self.ctx.focus_field(field)
            self.column.addWidget(label)
            self.rows.append(label)


def result_rows(ctx):
    """[(name, [(html, alignment)])] of «Résultats»: the symbol, «=», the value and its unit, a load in bold -- or (None, the word «aucun») where nothing is computed. The domain names the results (`results(instance)`); a domain that names none shows every value of its instance."""
    left, right = Qt.AlignmentFlag.AlignLeft, Qt.AlignmentFlag.AlignRight
    instance = ctx.instance
    if instance is None:
        return [(None, [("<span style='color:%s'>%s</span>" % (theme.colour("muted"), richtext.escape(ctx.t("ct_none"))), left)])]
    loads = set(instance.get("results") or ())
    rows = []
    for name in ctx.module.results(instance):
        var = instance["vars"][name]
        value = var.get("value")
        text = _n(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else ctx.tl(str(value))
        unit = (" " + richtext.escape(var["unit"])) if var.get("unit") else ""
        bold = (lambda html: "<b>%s</b>" % html) if name in loads else (lambda html: html)
        rows.append((name, [(bold(richtext.math_html(var.get("symbol") or name)), left), ("=", left), (bold(richtext.escape(text) + unit), right)]))
    return rows


def tables_html(ctx):
    """The instance's tables after its values -- a build-up's layers, the wind's global and local forces --, a value cell naming its variable: one rendering, written once, for every domain that has tables (ARCH-RISK-007). "" where it has none."""
    instance = ctx.instance or {}
    vars_ = instance.get("vars") or {}
    muted = theme.colour("muted")
    html = ""
    for table in instance.get("tables") or ():
        groups = [c.get("group") for c in table["columns"]]
        spans = []   # a group over the columns it heads, once (the wind's openings over its surfaces)
        for g in groups:
            if spans and spans[-1][0] == g:
                spans[-1][1] += 1
            else:
                spans.append([g, 1])
        group_row = ("<tr>%s</tr>" % "".join("<th colspan='%d' style='padding:0 6px;color:%s'>%s</th>" % (n, muted, richtext.escape(ctx.tl(g or ""))) for g, n in spans)) if any(groups) else ""
        head = "".join("<th style='padding:0 6px'>%s</th>" % richtext.escape(ctx.tl(c.get("label") or "")) for c in table["columns"])
        rows = []
        for row in table["rows"]:
            cells = []
            for column, value in zip(table["columns"], row):
                value = contracts.table_cell(value, column, vars_)
                text = _n(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else ctx.tl(str(value or ""))
                cells.append("<td align='right' style='padding:0 6px'>%s</td>" % richtext.escape(text))
            rows.append("<tr>%s</tr>" % "".join(cells))
        html += "<p style='margin:8px 0 2px 0;font-weight:600'>%s</p><table cellspacing='0' cellpadding='1'>%s<tr>%s</tr>%s</table>" % (
            richtext.escape(ctx.tl(table.get("title") or "")), group_row, head, "".join(rows))
    return html


class _ResultsBody(QWidget):
    """The module «Résultats» (REQ-009): what is computed, never an input, compact -- a row a value, each its widgets, so that a row hovered lights the data it is computed from and a datum hovered the rows it goes into (UI-004 of the spec 2026-10-23-neige-correctifs-issues-96-99) --, then the instance's tables, or the blocks the domain declares there in their place (`Declaration.modules` «results», D-34: the wind's walls, roof and local areas at their φ)."""

    def __init__(self, ctx, blocks=()):
        super().__init__()
        self.ctx = ctx
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(4)
        grid_holder = QWidget()
        self.grid = QGridLayout(grid_holder)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(6)
        self.grid.setVerticalSpacing(1)
        column.addWidget(grid_holder)
        self.tables = QLabel("")
        self.tables.setTextFormat(Qt.TextFormat.RichText)
        self.tables.setWordWrap(True)
        self.tables.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.tables.setVisible(False)
        column.addWidget(self.tables)
        self.blocks = [_block(block, ctx) for block in blocks]
        for widget in self.blocks:
            column.addWidget(widget)
        self.rows = {}          # name -> its labels
        self.lit = set()
        self.keyed = set()      # the names lit by the keys of an element hovered (`var:<name>`, ARCH-004)
        ctx.litKeys.connect(self.set_keys)

    def refresh(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget() is not None:
                item.widget().hide()   # gone at once, not at the next turn of the event loop
                item.widget().deleteLater()
        self.rows = {}
        for r, (name, cells) in enumerate(result_rows(self.ctx)):
            labels = []
            for c, (text, align) in enumerate(cells):
                label = QLabel(text)
                label.setTextFormat(Qt.TextFormat.RichText)
                label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                label.setAlignment(align | Qt.AlignmentFlag.AlignVCenter)
                if name is not None:
                    label.installEventFilter(Hover(label, lambda n=name: self._enter(n), lambda: self._enter(None)))
                self.grid.addWidget(label, r, c)
                labels.append(label)
            if name is not None:
                self.rows[name] = labels
        self.grid.setColumnStretch(3, 1)
        tables = "" if self.blocks else tables_html(self.ctx)
        self.tables.setText(tables)
        self.tables.setVisible(bool(tables))
        for widget in self.blocks:
            widget.refresh()
        self.set_lit(self.lit)

    def _enter(self, name):
        """A row hovered: the data it is computed from lit (UI-004), and what the domain links it to by its key `var:<name>` (ARCH-004); None, everything plain."""
        self.ctx.hover_result(name)
        self.ctx.hover_element(None if name is None else "var:" + name)

    def set_keys(self, lit, _emphasis):
        """The rows whose `var:<name>` an element hovered lights (a column of the global forces lights its Q_k, UI-021)."""
        self.keyed = {key[4:] for key in (lit or ()) if isinstance(key, str) and key.startswith("var:")}
        self.set_lit(self.lit)

    def set_lit(self, names):
        """The rows of `names`, and those an element's keys light, on the theme's `hover` ground, the others plain."""
        self.lit = set(names)
        lit = "background: %s; color: %s;" % (theme.colour("hover"), theme.colour("hover-ink"))
        for name, labels in self.rows.items():
            for label in labels:
                label.setStyleSheet(lit if name in self.lit or name in self.keyed else "")

    def text(self):
        """The rows' words, one after the other, then the tables' -- what a test reads."""
        cells = " ".join(self.grid.itemAt(i).widget().text() for i in range(self.grid.count()))
        return (cells + " " + self.tables.text()).strip()


class _DrawingBody(QWidget):
    """The domain's drawing of the case (the snow's column of Figur 3, a build-up's layers), as the export writes it, its words the window's."""

    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        self.svg = QSvgWidget()
        self.svg.setMinimumHeight(200)
        self.svg.setMinimumWidth(60)
        self.svg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        column.addWidget(self.svg)

    def refresh(self):
        drawing = self.ctx.drawing
        self.svg.setVisible(bool(drawing))
        if drawing:
            try:
                self.svg.load(QByteArray(drawing.encode("utf-8")))
                self.svg.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
                size = self.svg.renderer().defaultSize()
                if size.width() > 0:
                    self.svg.setMinimumHeight(min(620, round(size.height() * min(max(self.width(), 260), size.width()) / size.width())))
            except Exception:  # broad: a drawing that fails must not empty the form -- but it is said (G5)
                traceback.print_exc()


def _unit(axis):
    """An axis's unit after a number: a degree against it, any other after a space, none where it has none."""
    unit = axis.get("unit") or ""
    return unit if unit in ("", "°") else " " + unit


class ChartWidget(QWidget):
    """An interactive chart of a domain's data (UI-010: Figur 2): its series as polylines, the case's marks, and under the pointer the value of every series there. It knows the labels the domain gives (`chart`: x, y, series, marks), never what they mean."""

    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.setMouseTracking(True)
        self.setMinimumSize(320, 220)
        self.pointer = None
        self.data = None

    def refresh(self):
        self.data = self.ctx.chart
        self.update()

    def _frame(self):
        return QRectF(40, 12, max(self.width() - 56, 10), max(self.height() - 44, 10))

    def _to(self, x, y):
        d, f = self.data, self._frame()
        sx = (x - d["x"]["min"]) / ((d["x"]["max"] - d["x"]["min"]) or 1)
        sy = (y - d["y"]["min"]) / ((d["y"]["max"] - d["y"]["min"]) or 1)
        return QPointF(f.left() + sx * f.width(), f.bottom() - sy * f.height())

    @staticmethod
    def value_at(points, x):
        """The series' value at `x`: straight between its points, constant beyond them."""
        if x <= points[0][0]:
            return points[0][1]
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            if x <= x1:
                return y0 + (y1 - y0) * (x - x0) / ((x1 - x0) or 1)
        return points[-1][1]

    def probe(self, x):
        """[(series name, value)] at `x` -- what the pointer reads."""
        return [(s["name"], self.value_at(s["points"], x)) for s in (self.data or {}).get("series", ())]

    def mouseMoveEvent(self, event):
        self.pointer = event.position()
        self.update()

    def leaveEvent(self, event):
        self.pointer = None
        self.update()

    def paintEvent(self, event):
        if not self.data:
            return
        d, f = self.data, self._frame()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        ink, muted, line = QColor(theme.colour("ink")), QColor(theme.colour("muted")), QColor(theme.colour("line"))
        p.setPen(QPen(line, 1, Qt.PenStyle.DashLine))
        x = d["x"]["min"]
        while x <= d["x"]["max"] + 1e-9:
            a = self._to(x, d["y"]["min"])
            p.drawLine(a, self._to(x, d["y"]["max"]))
            p.setPen(QPen(muted))
            p.drawText(QRectF(a.x() - 20, f.bottom() + 2, 40, 14), Qt.AlignmentFlag.AlignHCenter, _n(x))
            p.setPen(QPen(line, 1, Qt.PenStyle.DashLine))
            x += d["x"]["step"]
        y = d["y"]["min"]
        while y <= d["y"]["max"] + 1e-9:
            a = self._to(d["x"]["min"], y)
            p.drawLine(a, self._to(d["x"]["max"], y))
            p.setPen(QPen(muted))
            p.drawText(QRectF(0, a.y() - 7, 36, 14), Qt.AlignmentFlag.AlignRight, _n(y))
            p.setPen(QPen(line, 1, Qt.PenStyle.DashLine))
            y += d["y"]["step"]
        p.setPen(QPen(ink, 1))
        p.drawRect(f)
        p.drawText(QRectF(f.right() - 60, f.bottom() + 16, 60, 14), Qt.AlignmentFlag.AlignRight, "%s [%s]" % (d["x"]["label"], d["x"]["unit"]) if d["x"]["unit"] else d["x"]["label"])
        p.drawText(QRectF(2, 0, 36, 12), Qt.AlignmentFlag.AlignLeft, d["y"]["label"])
        for s in d["series"]:
            p.setPen(QPen(ink, 1.6))
            points = [self._to(px, py) for px, py in s["points"]]
            for a, b in zip(points, points[1:]):
                p.drawLine(a, b)
            last = points[-1]
            p.drawText(QRectF(last.x() - 36, last.y() - 16, 34, 14), Qt.AlignmentFlag.AlignRight, richtext.plain_math(s["name"]))
        accent = QColor(theme.colour("accent"))
        for m in d["marks"]:
            at = self._to(m["x"], m["y"])
            p.setPen(QPen(accent, 1, Qt.PenStyle.DashLine))
            p.drawLine(self._to(m["x"], d["y"]["min"]), at)
            p.setPen(QPen(accent, 1))
            p.setBrush(accent)
            p.drawEllipse(at, 4, 4)
            p.setBrush(Qt.BrushStyle.NoBrush)
            bold = QFont(p.font())
            bold.setBold(True)
            p.setFont(bold)
            p.drawText(QPointF(at.x() + 6, at.y() - 6), "%s = %s%s → %s = %s" % (richtext.plain_math(m["label"]), _n(m["x"]), _unit(d["x"]), richtext.plain_math(m["series"]), "%.2f" % m["y"]))
            p.setFont(QFont(self.font()))
        if self.pointer is not None and f.contains(self.pointer):
            sx = (self.pointer.x() - f.left()) / f.width()
            x = d["x"]["min"] + sx * (d["x"]["max"] - d["x"]["min"])
            p.setPen(QPen(muted, 1))
            p.drawLine(QPointF(self.pointer.x(), f.top()), QPointF(self.pointer.x(), f.bottom()))
            said = "%s = %s%s   " % (d["x"]["label"], _n(round(x)), _unit(d["x"])) + "   ".join("%s = %.2f" % (richtext.plain_math(name), value) for name, value in self.probe(x))
            p.setPen(QPen(ink))
            p.drawText(QRectF(f.left() + 4, f.top() + 2, f.width() - 8, 14), Qt.AlignmentFlag.AlignLeft, said)
        p.end()


def _block(block, ctx):
    import calc_blocks
    return calc_blocks.make(block, ctx, pinned=True)


class _BlocksBody(QWidget):
    """A module of the blocks the domain declares for it (`Declaration.modules`, D-34): the wind's «Bâtiment», its figure or its model and the table's facts."""

    def __init__(self, ctx, blocks):
        super().__init__()
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(4)
        self.blocks = [_block(block, ctx) for block in blocks]
        for widget in self.blocks:
            column.addWidget(widget)

    def refresh(self):
        for widget in self.blocks:
            widget.refresh()


def declared_modules(ctx):
    """{id: (Block, …)} of the modules the domain's declaration names (D-34), {} for a tab with no declared form."""
    declaration = getattr(ctx.module, "declaration", None)
    if declaration is None:
        return {}
    decl = declaration()
    return {mid: tuple(decl.block(k) for k in keys) for mid, keys in decl.modules}


class Modules(Service):
    """The right pane of modules -- see the module's docstring."""

    NAME = "modules"
    WORDS_MODULE = "calc_tab_words"
    ZONE = "right"
    NEEDS = ("messages", "results")

    def mount(self, ctx):
        super().mount(ctx)
        self.pane = module_pane.ModulePane(self.t, ctx.key, ctx.layout)
        self.pane.setMinimumWidth(MODULES_MIN_WIDTH)
        self.pane.removed.connect(self._removed)
        self.pane.add(module_pane.ModuleSpec("state", self.t("ct_module_state"), lambda: _StateBody(ctx), kind="state"))
        # the modules the tab's services give the pane (the permanent loads' «Couche n» and «Coupe | Contributions», UI-002), after the state; one named «drawing» takes the place of the domain's drawing
        given = list(ctx.pane_modules)
        for spec in given:
            self.pane.add(spec)
        declared = declared_modules(ctx)
        # one named «results» takes the place of the type's (a member check's verdict and its rows in the order of the calculation, issue #112)
        if not any(spec.id == "results" for spec in given):
            self.pane.add(module_pane.ModuleSpec("results", self.t("ct_module_results"), lambda: _ResultsBody(ctx, declared.get("results", ())), kind="results"))
        for mid, blocks in declared.items():
            if mid != "results":
                self.pane.add(module_pane.ModuleSpec(mid, self.t(ctx.prefix() + "m_" + mid), lambda b=blocks: _BlocksBody(ctx, b), kind="declared",
                                                     fills_window=any(b.kind in ("model3d", "views") for b in blocks)))
        if hasattr(ctx.module, "figure_svg") and not any(spec.id == "drawing" for spec in given):
            self.pane.add(module_pane.ModuleSpec("drawing", self.t(ctx.prefix() + "module_drawing"), lambda: _DrawingBody(ctx), kind="drawing"))
        if hasattr(ctx.module, "chart"):
            self.pane.add(module_pane.ModuleSpec("chart", self.t(ctx.prefix() + "module_chart"), lambda: ChartWidget(ctx), kind="chart"))
        ctx.excerptPinned.connect(self.pin)
        ctx.excerptUnpinned.connect(self.unpin)
        ctx.blockPinned.connect(self.pin_block)
        ctx.lit.connect(lambda _fields, names: self.pane.modules["results"].body.set_lit(names))
        return self.pane

    # --- the phase `computed` -------------------------------------------------------------

    def computed(self):
        self.pane.refresh()
        self.update_summaries()

    def update_summaries(self):
        """What a folded module says in its header (T45): the state's count, the first load, the chart's marks."""
        ctx = self.ctx
        errors = [m for m in ctx.messages if m.severity == "error"]
        infos = [m for m in ctx.messages if m.severity in ("warning", "info")]
        if errors:
            state = self.t("ct_summary_errors", count=len(errors))
        else:
            state = self.t("ct_summary_complete") + ((" · " + self.t("ct_summary_infos", count=len(infos))) if infos else "")
        self.pane.summary("state", richtext.escape(state))
        first = next(iter((ctx.instance or {}).get("results") or ()), None)
        if first:
            var = ctx.instance["vars"][first]
            self.pane.summary("results", "%s = %s %s" % (richtext.math_html(var.get("symbol") or first), _n(var["value"]), richtext.escape(var.get("unit") or "")))
        else:
            self.pane.summary("results", richtext.escape(self.t("ct_none")))
        marks = (ctx.chart or {}).get("marks") or ()
        self.pane.summary("chart", " · ".join("%s → %s = %.2f" % (richtext.math_html(m["label"]), richtext.math_html(m["series"]), m["y"]) for m in marks))

    # --- the excerpts of the norm, pinned under «Résultats» --------------------------------

    def pin(self, norm, ids):
        """A bubble clicked (REQ-003): its excerpts a module under «Résultats», once; their ⓘ filled. Returns the module."""
        ids = tuple(ids)
        prefix = self.ctx.prefix()
        module = norm_bubble.pin_excerpts(self.pane, norm, ids, self.app.lang, self.t, lambda items: " + ".join("%s %s" % (e.ref, self.t(prefix + "x_" + e.id)) for e in items))
        mid = excerpt_module_id(norm, ids)
        self.ctx.pinned.add(mid)
        self.ctx.pinsChanged.emit()
        return module

    def pin_block(self, key):
        """A block's 📌 (ARCH-005): the block a module under «Résultats», once, its title the tab's word `<prefix>b_<key>`; its body a new widget of calc_blocks, refreshed with the others, its window laid out at the window's size for a drawing that draws itself (the 3D model). Returns the module."""
        import calc_blocks
        block = self.ctx.declaration().block(key)
        mid = BLOCK_PREFIX + key
        spec = module_pane.ModuleSpec(mid, self.t(self.ctx.prefix() + "b_" + key), lambda: calc_blocks.make(block, self.ctx, pinned=True), closable=True, kind="block",
                                      fills_window=block.kind == "model3d")
        module = self.pane.pin(spec)
        module.body.refresh()
        self.ctx.pinned.add(mid)
        self.ctx.pinsChanged.emit()
        return module

    def unpin(self, norm, ids):
        """A bubble clicked again, its excerpts pinned (issue #96): taken out of the pane as by their ×."""
        self.pane.remove(excerpt_module_id(norm, tuple(ids)))

    def _removed(self, module_id):
        """× or a second click: the excerpt is no longer pinned, its ⓘ hollow again (issue #96)."""
        self.ctx.pinned.discard(module_id)
        self.ctx.pinsChanged.emit()

    # --- state across a rebuild (D-27) ------------------------------------------------------

    def state(self):
        return {"pins": self.pane.state()}

    def restore(self, state):
        pins = (state or {}).get("pins") or {}
        for module_id in pins.get("pins", ()):
            if module_id.startswith(BLOCK_PREFIX):
                module = self.pin_block(module_id[len(BLOCK_PREFIX):])
            else:
                norm, ids = excerpt_of_module(module_id)
                module = self.pin(norm, ids)
            if module_id in pins.get("folded", ()):
                module.set_folded(True, save=False)
