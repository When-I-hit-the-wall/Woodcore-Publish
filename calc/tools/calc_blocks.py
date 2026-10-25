"""What a section of a calculation tab's form holds besides its fields, and what the right pane shows of it pinned (spec 2026-10-23-onglet-vent-briques, ARCH-003, ARCH-004, ARCH-006, ARCH-RISK-001).

A domain declares its blocks (calc/domains/contracts.py `Block`, `BLOCK_KINDS`) and gives their data through `blocks(src, instance)`, which the context keeps (`ctx.blocks`) as it keeps the drawing. This module is the blocks' widgets, written once: the declared form (calc_form.DeclaredForm) puts them in its sections and the pane of modules (calc_modules.Modules) makes a module of one pinned -- both call `make`, neither imports the other. It is no service.

* **text** -- `{"text": <a term of the glossary or a sentence the domain composed in German>}`, said in the window's language (`ctx.tl`), its symbols with their subscripts; or `{"word": <a word of the tab, after its prefix>, "params": {…}}`;
* **svg** -- `{"svg": <the drawing>}`, as wide as the section, its proportions kept;
* **formula** -- `{"formula": <Typst math>, "values": <the same, the numbers in>, "ref": <the clause>}`;
* **heat_table** -- a table of numbers coloured by their value (ARCH-006): `{"columns": [{"label", "key", "marked"}], "rows": [{"label", "cells": [{"value", "id", "keys"}]}], "legend": bool, "scale": the value of the strongest colour (None: the largest of the table)}` -- a value a number, a pair `[a, b]` (written ±a or a/b), "direct" (*) or None (–); the colours are `theme.json`'s `heat-*`, three of pressure, three of suction, one for nought;
* **row_select** -- a field of kind select on the line of a text (the openings beside «c_pi»): the form gives the field's widget, `{"text"}` or `{"word"}` the words before it;
* **excerpt** -- `{"norm": <the norm file>, "id": <the excerpt>}`: the excerpt in the window's language, its head, its words and its image cut out of the shipped PDF, as a bubble shows it (norm_bubble.ExcerptView);
* **views** -- several blocks shown one at a time (D-35): the block's `children`, each a button of a segmented bar over them named by the tab's word `<prefix>v_<child>`, a child the domain gives no data offered by no button, the bar hidden where one is left; `{}` its data (the children's are their own). The view chosen is the context's (`ctx.view_state(key)["view"]`), the same in the section, the right pane and a window;
* **model3d** -- a 3D model (calc/domains/model3d.py, spec version 3, ARCH-007, UI-008 to UI-018): `{"build": state -> model3d.Scene, "views": [(label, yaw, pitch)], "phi": True for a slider of the direction and "phi_label" its words, "directions": [labels] and "signs": [(key, label)] for a result's buttons, "max": the label of «every direction», "key_prefix": what a face's key is prefixed with as an element, "words": True where the labels are words of the tab, after its prefix}` -- the scene built only while the widget is shown, from the view the context holds by the block's key (`ctx.view_state`), drawn by a QPainter; dragged it turns, the wheel zooms about its centre, a face hovered asks `ctx.hover_element`, and what `litKeys` names is drawn through the model;

**Hovers by keys** (ARCH-004): a cell of a heat table carries its `id` and the keys of what it is read from; hovered, it asks `ctx.hover_element(id)`, and every widget lights what the context's `litKeys(lit, emphasis)` names -- `lit` on the theme's `hover` ground, `emphasis` framed in `heat-mark`. The keys are the domain's, opaque: nothing here knows what a cell of a table is of.
"""

from PySide6.QtCore import QByteArray, QEvent, QPointF, QSize, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QSlider, QToolButton, QVBoxLayout,
                               QWidget)

import richtext
import theme
from tab_host import Hover, _n, words_of

# The colours of a heat table, from the strongest suction to the strongest pressure (theme.json), and where a value turns from one to the next, as a fraction of the table's scale
HEAT = ("heat-s3", "heat-s2", "heat-s1", "heat-z0", "heat-p1", "heat-p2", "heat-p3")
HEAT_STEPS = (0.66, 0.33, 0.02)


def heat_token(value, scale):
    """The theme's token of a value in a heat table of scale `scale`: nought within 2 % of it, then a third, two thirds and beyond, each side."""
    x = value / scale if scale else 0.0
    for i, step in enumerate(HEAT_STEPS):
        if x > step:
            return HEAT[6 - i]
        if x < -step:
            return HEAT[i]
    return HEAT[3]


def cell_numbers(value):
    """The numbers a cell stands for: a pair both, a number itself, an empty or a direct cell none."""
    if value is None or value == "direct":
        return []
    return list(value) if isinstance(value, (list, tuple)) else [value]


def cell_text(value):
    """A cell as the norm writes it: ±0,1 a pair of opposite values, a/b another pair, * a coefficient computed directly, – none."""
    if value is None:
        return "–"
    if value == "direct":
        return "*"
    if isinstance(value, (list, tuple)):
        a, b = value
        return ("±" + _n(abs(a))) if a == -b and a != 0 else (_n(a) + "/" + _n(b)).replace("-", "−")
    return _n(value).replace("-", "−")


def words(ctx, data):
    """What a text or a row_select says: a word of the tab (`word`, after the tab's prefix, with its `params`), else a sentence of the glossary (`text`)."""
    if data.get("word"):
        # a value given per edition ({"fr": …, "de": …}: a table's title, D-35) said in the window's language, English reading German
        params = {k: (v.get(ctx.app.lang) or v.get("de", "")) if isinstance(v, dict) else v for k, v in data.get("params", {}).items()}
        return ctx.t(ctx.prefix() + data["word"], **words_of(params))
    return ctx.tl(data.get("text") or "")


def _alive(call, widget=None):
    """`call()` unless the widget it draws on is gone -- a body whose module was taken out, still connected to the context's signals. Returns whether it was alive."""
    try:
        if widget is not None:
            widget.objectName()
        call()
        return True
    except RuntimeError:
        return False


class _Base(QWidget):
    """A block's widget: its data read off the context at each `refresh()` -- `ctx.blocks[key]`, {} where the domain gives none."""

    def __init__(self, block, ctx):
        super().__init__()
        self.block, self.ctx = block, ctx
        self.column = QVBoxLayout(self)
        self.column.setContentsMargins(0, 0, 0, 0)
        self.column.setSpacing(2)

    def data(self):
        return (self.ctx.blocks or {}).get(self.block.key) or {}


class TextBlock(_Base):
    def __init__(self, block, ctx):
        super().__init__(block, ctx)
        self.label = QLabel("")
        self.label.setTextFormat(Qt.TextFormat.RichText)
        self.label.setWordWrap(True)
        self.column.addWidget(self.label)

    def refresh(self):
        data = self.data()
        self.label.setText(richtext.subscripts(words(self.ctx, data)) if data else "")
        self.setVisible(bool(data))


class SvgBlock(_Base):
    def __init__(self, block, ctx):
        super().__init__(block, ctx)
        self.svg = QSvgWidget()
        self.svg.setMinimumHeight(120)
        self.svg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.column.addWidget(self.svg)

    def refresh(self):
        drawing = self.data().get("svg")
        self.setVisible(bool(drawing))
        if drawing:
            self.svg.load(QByteArray(drawing.encode("utf-8")))
            self.svg.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)


class FormulaBlock(_Base):
    def __init__(self, block, ctx):
        super().__init__(block, ctx)
        self.label = QLabel("")
        self.label.setTextFormat(Qt.TextFormat.RichText)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.column.addWidget(self.label)

    def refresh(self):
        data = self.data()
        parts = [richtext.math_html(data[k]) for k in ("formula", "values") if data.get(k)]
        ref = (" <span style='color:%s'>%s</span>" % (theme.colour("muted"), richtext.escape(data["ref"]))) if data.get("ref") else ""
        self.label.setText(" = ".join(parts) + ref if parts else "")
        self.setVisible(bool(parts))


class HeatTable(_Base):
    """A table of numbers coloured by their value (ARCH-006): a marked column framed, a legend under it, each cell hovered asking the context what it lights, and lit or framed by the keys the context names."""

    def __init__(self, block, ctx):
        super().__init__(block, ctx)
        self.grid_holder = QWidget()
        self.grid = QGridLayout(self.grid_holder)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(1)
        self.grid.setVerticalSpacing(1)
        self.column.addWidget(self.grid_holder)
        self.legend = QWidget()
        self.column.addWidget(self.legend)
        self.cells = {}        # id -> (label, keys, base style)
        self.lit, self.emphasis = set(), set()
        ctx.litKeys.connect(self.set_keys)
        self._legend()

    def _legend(self):
        row = QHBoxLayout(self.legend)
        row.setContentsMargins(0, 2, 0, 0)
        row.setSpacing(2)
        row.addWidget(QLabel(self.ctx.t("ct_suction")))
        for token in HEAT:
            swatch = QLabel("")
            swatch.setFixedSize(16, 10)
            swatch.setStyleSheet("background: %s; border: 1px solid %s;" % (theme.colour(token), theme.colour("line")))
            row.addWidget(swatch)
        row.addWidget(QLabel(self.ctx.t("ct_pressure")))
        row.addStretch(1)

    def refresh(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget() is not None:
                item.widget().hide()   # gone at once, not at the next turn of the event loop
                item.widget().deleteLater()
        self.cells = {}
        data = self.data()
        self.setVisible(bool(data))
        self.legend.setVisible(bool(data.get("legend")))
        if not data:
            return
        columns = data.get("columns") or []
        scale = data.get("scale") or max((abs(v) for row in data.get("rows", ()) for c in row["cells"] for v in cell_numbers(c.get("value"))), default=0)
        marked = theme.colour("heat-mark")
        for c, column in enumerate(columns, 1):
            head = QLabel(richtext.subscripts(self.ctx.tl(column.get("label") or "")))
            head.setTextFormat(Qt.TextFormat.RichText)
            head.setAlignment(Qt.AlignmentFlag.AlignCenter)
            head.setStyleSheet("font-weight: 600; padding: 0 3px;" + (" border-bottom: 2px solid %s;" % marked if column.get("marked") else ""))
            self.grid.addWidget(head, 0, c)
        for r, row in enumerate(data.get("rows") or (), 1):
            label = QLabel(richtext.subscripts(self.ctx.tl(row.get("label") or "")))
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setStyleSheet("padding: 0 4px; color: %s;" % theme.colour("ink-soft"))
            self.grid.addWidget(label, r, 0)
            for c, (column, cell) in enumerate(zip(columns, row["cells"]), 1):
                value = cell.get("value")
                numbers = cell_numbers(value)
                strongest = max(numbers, key=abs) if numbers else None
                ground = theme.colour(heat_token(strongest, scale)) if strongest is not None and data.get("colour", True) else "transparent"
                base = "padding: 1px 4px; color: %s; background: %s;" % (theme.colour("heat-ink") if strongest is not None else theme.colour("muted"), ground)
                if column.get("marked"):
                    base += " border-left: 2px solid %s; border-right: 2px solid %s;" % (marked, marked)
                text = QLabel(cell.get("text") or cell_text(value))
                text.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                text.setStyleSheet(base)
                eid = cell.get("id")
                if eid:
                    text.installEventFilter(Hover(text, lambda e=eid: self.ctx.hover_element(e), lambda: self.ctx.hover_element(None)))
                    self.cells[eid] = (text, set(cell.get("keys") or ()) | {eid}, base)
                self.grid.addWidget(text, r, c)
        self.grid.setColumnStretch(len(columns) + 1, 1)
        self.set_keys(self.lit, self.emphasis)

    def set_keys(self, lit, emphasis):
        """The cells whose keys `lit` names on the theme's `hover` ground, those `emphasis` names framed in `heat-mark` (UI-021: «cadre orange»)."""
        self.lit, self.emphasis = set(lit or ()), set(emphasis or ())
        if not _alive(lambda: None, self):
            return
        for _eid, (label, keys, base) in self.cells.items():
            style = base
            if keys & self.lit:
                style += " background: %s; color: %s;" % (theme.colour("hover"), theme.colour("hover-ink"))
            if keys & self.emphasis:
                style += " border: 2px solid %s;" % theme.colour("heat-mark")
            label.setStyleSheet(style)

    def lit_ids(self):
        """The ids of the cells lit -- what a test reads."""
        return {eid for eid, (_l, keys, _b) in self.cells.items() if keys & self.lit}

    def framed_ids(self):
        return {eid for eid, (_l, keys, _b) in self.cells.items() if keys & self.emphasis}


class ExcerptBlock(_Base):
    """An excerpt of a norm in a section (the figure of the wind's building, UI-005): built again when its excerpt changes."""

    def __init__(self, block, ctx):
        super().__init__(block, ctx)
        self.shown, self.view = None, None

    def refresh(self):
        import norm_bubble
        from norms import excerpts
        data = self.data()
        self.setVisible(bool(data))
        wanted = (data.get("norm"), data.get("id"), self.ctx.app.lang) if data else None
        if wanted == self.shown:
            return
        if self.view is not None:
            self.view.setParent(None)
            self.view = None
        self.shown = wanted
        if data:
            self.view = norm_bubble.ExcerptView([excerpts.excerpt(data["norm"], data["id"], self.ctx.app.lang)], self.ctx.t, bare=True)
            self.column.addWidget(self.view)


class ViewsBlock(_Base):
    """Several blocks one at a time under a segmented bar (D-35): the wind's figure of the norm and its model in 3D."""

    def __init__(self, block, ctx, pinned=False):
        super().__init__(block, ctx)
        self.bar = QWidget()
        row = QHBoxLayout(self.bar)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        self.view_buttons = {}
        self.children = {}
        for key in block.children:
            button = QPushButton(ctx.t(ctx.prefix() + "v_" + key))
            button.setCheckable(True)
            button.setProperty("choice", True)
            button.clicked.connect(lambda _c=False, k=key: self.choose(k))
            row.addWidget(button)
            self.view_buttons[key] = button
        row.addStretch(1)
        self.column.addWidget(self.bar)
        for key in block.children:
            child = make(ctx.declaration().block(key), ctx, pinned=pinned)
            self.column.addWidget(child)
            self.children[key] = child
        ctx.viewChanged.connect(self._view_changed)

    def offered(self):
        """The children the domain gives data, in their order."""
        return [k for k in self.block.children if (self.ctx.blocks or {}).get(k)]

    def current(self):
        offered = self.offered()
        chosen = self.ctx.view_state(self.block.key).get("view")
        return chosen if chosen in offered else (offered[0] if offered else None)

    def choose(self, key):
        self.ctx.view_state(self.block.key)["view"] = key
        self.ctx.viewChanged.emit(self.block.key)

    def _view_changed(self, key):
        if key == self.block.key:
            _alive(self._show, self)

    def refresh(self):
        for child in self.children.values():
            child.refresh()
        self._show()

    def _show(self):
        offered, current = self.offered(), self.current()
        self.setVisible(bool(offered))
        self.bar.setVisible(len(offered) > 1)
        for key, button in self.view_buttons.items():
            button.setVisible(key in offered)
            button.setChecked(key == current)
        for key, child in self.children.items():
            child.setVisible(key == current)


class RowSelect(_Base):
    """A field of kind select on the line of its words (ARCH-RISK-014): the form gives its widget, which stays its own -- filled and collected with the form's fields."""

    def __init__(self, block, ctx, field_widget=None):
        super().__init__(block, ctx)
        line = QWidget()
        row = QHBoxLayout(line)
        row.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel("")
        self.label.setTextFormat(Qt.TextFormat.RichText)
        row.addWidget(self.label)
        if field_widget is not None:
            row.addWidget(field_widget)
        row.addStretch(1)
        self.column.addWidget(line)

    def refresh(self):
        self.label.setText(richtext.subscripts(words(self.ctx, self.data())))


class _Canvas(QWidget):
    """Where a 3D model is painted: the items `model3d.render` gives, at the widget's size -- turned by a drag, zoomed by the wheel, a face under the pointer hovered. No text is selected by a drag (UI-008): it is a plain widget."""

    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.setMouseTracking(True)
        self.setMinimumSize(260, 200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.items, self._drag, self._hovered = [], None, None

    def heightForWidth(self, width):
        return int(width * 0.75)

    def hasHeightForWidth(self):
        return True

    def paintEvent(self, event):
        from domains import model3d
        self.items = self.owner.render(self.width(), self.height())
        colours = model3d.palette()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(colours["halo"]))
        hatch = QBrush(QColor(colours["ink"]), Qt.BrushStyle.BDiagPattern)
        for it in self.items:
            if it["kind"] == "polygon":
                poly = QPolygonF([QPointF(x, y) for x, y in it["points"]])
                colour = QColor(colours[it["role"]])
                colour.setAlphaF(it["opacity"])
                p.setPen(QPen(QColor(colours[it["outline"]]), it["width"]))
                p.setBrush(colour)
                p.drawPolygon(poly)
                if it["hatch"]:
                    p.setBrush(hatch)
                    p.drawPolygon(poly)
            elif it["kind"] in ("line", "arrow"):
                pen = QPen(QColor(colours[it["role"]]), it["width"])
                if it.get("dash"):
                    pen.setStyle(Qt.PenStyle.DashLine)
                p.setOpacity(it.get("opacity", 1.0))
                p.setPen(pen)
                p.drawLine(QPointF(*it["a"]), QPointF(*it["b"]))
                if it["kind"] == "arrow":
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(QColor(colours[it["role"]]))
                    p.drawPolygon(QPolygonF([QPointF(x, y) for x, y in it["head"]]))
                p.setOpacity(1.0)
            elif it["kind"] == "text":
                font = QFont(self.font())
                font.setPixelSize(max(int(it["size"]), 8))
                font.setItalic(it["italic"])
                font.setBold(it["bold"])
                path = QPainterPath()
                width = len(it["text"]) * it["size"] * 0.58
                x = it["x"] - width / 2 if it["anchor"] == "middle" else it["x"] - width if it["anchor"] == "end" else it["x"]
                path.addText(QPointF(x, it["y"]), font, it["text"])
                p.setPen(QPen(QColor(colours["halo"]), 3))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawPath(path)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(colours[it["role"]]))
                p.drawPath(path)
        p.end()

    def mousePressEvent(self, event):
        self._drag = event.position()

    def mouseReleaseEvent(self, event):
        self._drag = None

    def mouseMoveEvent(self, event):
        if self._drag is not None and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.position() - self._drag
            self._drag = event.position()
            self.owner.turn(delta.x() * 0.5, -delta.y() * 0.4)
            return
        from domains import model3d
        key = model3d.pick(self.items, event.position().x(), event.position().y())
        if key != self._hovered:
            self._hovered = key
            self.owner.hovered(key)

    def leaveEvent(self, event):
        if self._hovered is not None:
            self._hovered = None
            self.owner.hovered(None)

    def wheelEvent(self, event):
        self.owner.zoom_by(1.15 if event.angleDelta().y() > 0 else 1 / 1.15)
        event.accept()


class Model3D(_Base):
    """A 3D model of the domain's (ARCH-007): its canvas, the zoom −, its share, +, «Ajuster», the views the domain names, the direction's slider where it has one, a result's directions and signs -- the view the context's by the block's key, shared by its bodies in the form, the pane and a window, each block its own (T87)."""

    ZOOMS_ITSELF = True   # nowheel.py leaves its wheel to it

    def __init__(self, block, ctx):
        super().__init__(block, ctx)
        self.canvas = _Canvas(self)
        self.column.addWidget(self.canvas, 1)
        self.controls = QWidget()
        self.row = _FlowRow(self.controls)
        self.column.addWidget(self.controls)
        self.lit = set()
        self._built = None
        ctx.litKeys.connect(self.set_keys)
        ctx.viewChanged.connect(self._view_changed)

    def _view_changed(self, key):
        """Another body of the same drawing turned or zoomed: this one draws again -- a body gone with its module (a pin taken out) says nothing."""
        if key == self.block.key:
            _alive(self.canvas.update)

    def state(self):
        view = self.ctx.view_state(self.block.key)
        view.setdefault("yaw", -131.0)
        view.setdefault("pitch", 28.0)
        view.setdefault("zoom", 1.0)
        view.setdefault("phi", 0.0)
        return view

    def refresh(self):
        data = self.data()
        self.setVisible(bool(data))
        self._built = None
        self._controls(data)
        self.canvas.update()

    def _word(self, label):
        """A label of the domain's data: a word of the tab where the data say so (`words`), else as it is (a direction, «0°»)."""
        return self.ctx.t(self.ctx.prefix() + label) if self.data().get("words") else label

    def _button(self, text, action, checked=None):
        button = QPushButton(text)
        if checked is not None:
            button.setCheckable(True)
            button.setChecked(checked)
        button.clicked.connect(action)
        self.row.add(button)
        return button

    def _controls(self, data):
        self.row.clear()
        state = self.state()
        self.zoom_label = QLabel("")
        self._button("−", lambda: self.zoom_by(1 / 1.15)).setToolTip(self.ctx.t("ct_zoom_out"))
        self.row.add(self.zoom_label)
        self._button("+", lambda: self.zoom_by(1.15)).setToolTip(self.ctx.t("ct_zoom_in"))
        self._button(self.ctx.t("ct_fit"), lambda: self.set_view(zoom=1.0))
        self.view_buttons = {}
        for label, yaw, pitch in data.get("views", ()):
            self.view_buttons[label] = self._button(self._word(label), lambda _c=False, y=yaw, p=pitch: self.set_view(yaw=y, pitch=p))
        self.slider = None
        if data.get("phi"):
            self.slider = QSlider(Qt.Orientation.Horizontal)
            self.slider.setRange(0, 360)
            self.slider.setValue(int(state["phi"]))
            self.slider.setMinimumWidth(140)
            self.slider.valueChanged.connect(lambda v: self.set_view(phi=float(v)))
            self.row.add(QLabel(self._word(data["phi_label"]) if data.get("phi_label") else ""))
            self.row.add(self.slider)
        self.direction_buttons = {}
        directions = list(data.get("directions", ()))
        if directions:
            chosen = state.get("direction") or data.get("max")
            for label in directions + ([data["max"]] if data.get("max") else []):
                text = self._word(label) if label == data.get("max") else label
                self.direction_buttons[label] = self._button(text, lambda _c=False, l=label: self.set_view(direction=None if l == data.get("max") else l), checked=label == chosen)
        self.sign_buttons = {}
        for key, label in data.get("signs", ()):
            self.sign_buttons[key] = self._button(self._word(label), lambda _c=False, k=key: self.set_view(sign=k), checked=key == state.get("sign", "+"))
        self._say_zoom()

    def _say_zoom(self):
        self.zoom_label.setText("%d %%" % round(self.state()["zoom"] * 100))

    def render(self, width, height):
        """The items of the model at the canvas's size -- the scene built here, while the widget is shown, from the view the context holds (ARCH-007: none for a widget hidden)."""
        from domains import model3d
        data = self.data()
        if not data or not self.isVisible():
            return []
        state = self.state()
        if self._built is None or self._built[0] != repr(sorted(state.items())):
            self._built = (repr(sorted(state.items())), data["build"](dict(state)))
        scene = self._built[1]
        view = model3d.View(yaw=state["yaw"], pitch=state["pitch"], zoom=state["zoom"], width=max(width, 10), height=max(height, 10))
        state["zoom"] = model3d.projector(scene, view).zoom
        prefix = data.get("key_prefix", "")
        lit = {k[len(prefix):] for k in self.lit if isinstance(k, str) and k.startswith(prefix)}
        return model3d.render(scene, view, lit)

    def turn(self, dyaw, dpitch):
        state = self.state()
        self.set_view(yaw=state["yaw"] + dyaw, pitch=max(-5.0, min(90.0, state["pitch"] + dpitch)))

    def zoom_by(self, factor):
        self.set_view(zoom=self.state()["zoom"] * factor)

    def set_view(self, **changes):
        state = self.state()
        state.update(changes)
        if "phi" in changes:
            state["phi"] = changes["phi"] % 360
        if "direction" in changes or "sign" in changes:
            chosen = state.get("direction") or self.data().get("max")
            for label, button in getattr(self, "direction_buttons", {}).items():
                button.setChecked(label == chosen)
            for key, button in getattr(self, "sign_buttons", {}).items():
                button.setChecked(key == state.get("sign", "+"))
        self.canvas.update()
        self._say_zoom()
        self.ctx.viewChanged.emit(self.block.key)

    def hovered(self, key):
        self.ctx.hover_element(None if key is None else self.data().get("key_prefix", "") + key)

    def set_keys(self, lit, _emphasis):
        self.lit = set(lit or ())
        _alive(self.canvas.update)


class _FlowRow:
    """Buttons that wrap to the next line where the widget narrows (UI-018): a grid filled again at each resize."""

    def __init__(self, holder):
        self.holder = holder
        self.layout = QHBoxLayout(holder)
        self.layout.setContentsMargins(0, 2, 0, 0)
        self.layout.setSpacing(4)
        self.widgets = []
        self.lines = QVBoxLayout()
        self.layout.addLayout(self.lines)
        self.layout.addStretch(1)
        holder.resizeEvent = lambda event: self.arrange()

    def add(self, widget):
        self.widgets.append(widget)
        self.arrange()

    def clear(self):
        for widget in self.widgets:
            widget.setParent(None)
        self.widgets = []
        self.arrange()

    def arrange(self):
        while self.lines.count():
            item = self.lines.takeAt(0)
            if item.layout() is not None:
                while item.layout().count():
                    item.layout().takeAt(0)
        width = max(self.holder.width(), 200)
        line, used = QHBoxLayout(), 0
        line.setSpacing(4)
        for widget in self.widgets:
            need = widget.sizeHint().width() + 4
            if used and used + need > width:
                line.addStretch(1)
                self.lines.addLayout(line)
                line, used = QHBoxLayout(), 0
                line.setSpacing(4)
            line.addWidget(widget)
            used += need
        line.addStretch(1)
        self.lines.addLayout(line)

    def rows(self):
        return self.lines.count()


FACTORIES = {"text": TextBlock, "svg": SvgBlock, "formula": FormulaBlock, "heat_table": HeatTable, "row_select": RowSelect, "model3d": Model3D, "excerpt": ExcerptBlock, "views": ViewsBlock}


def make(block, ctx, field_widget=None, pinned=False):
    """The widget of `block` -- in a section of the form, or pinned in the right pane (`pinned`: no pin of its own). A block `pinnable` carries a 📌 that asks the context to pin it (`ctx.pin_block`); a block `wide` scrolls sideways below its `min_width`."""
    factory = FACTORIES.get(block.kind)
    if factory is None:
        raise TypeError("calc_blocks: no widget for a block of kind %r (%s) -- contracts.BLOCK_KINDS names %s" % (block.kind, block.key, ", ".join(FACTORIES)))
    body = factory(block, ctx, field_widget) if block.kind == "row_select" else factory(block, ctx, pinned=pinned) if block.kind == "views" else factory(block, ctx)
    if block.wide:
        body.setMinimumWidth(block.min_width)
        scroll = _WideScroll()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; }")   # the card's ground, never the palette's base
        scroll.viewport().setAutoFillBackground(False)
        scroll.setWidget(body)
        outer = _Wrapper(body, scroll)
        outer.scroll = scroll
    else:
        outer = _Wrapper(body, body)
    if block.pinnable and not pinned:
        outer.add_pin(lambda: ctx.pin_block(block.key), ctx.t("ct_pin"))
    return outer


class _WideScroll(QScrollArea):
    """A scroll area as high as its block, the horizontal bar under it where it scrolls: a scroll area takes no height of its own, and a height fixed once is wrong while the section is folded."""

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def _height(self):
        body = self.widget()
        if body is None or body.isHidden():
            return 0   # a block with nothing to show leaves no gap
        return body.sizeHint().height() + self.horizontalScrollBar().sizeHint().height() + 2

    def sizeHint(self):
        return QSize(super().sizeHint().width(), self._height())

    def minimumSizeHint(self):
        return QSize(super().minimumSizeHint().width(), self._height())

    def eventFilter(self, watched, event):
        # its block laid out again (a table rebuilt): its height asked again
        if watched is self.widget() and event.type() == QEvent.Type.LayoutRequest:
            self.updateGeometry()
        return super().eventFilter(watched, event)

    def showEvent(self, event):
        # a hidden widget's updateGeometry is lost: the height asked again when its section opens
        super().showEvent(event)
        self.updateGeometry()


class _Wrapper(QWidget):
    """A block's body in its place: `body` the block's widget (what refreshes), `shown` what the layout holds (the body, or a scroll around it), a 📌 over it where it may be pinned."""

    def __init__(self, body, shown):
        super().__init__()
        self.body = body
        self.column = QVBoxLayout(self)
        self.column.setContentsMargins(0, 0, 0, 0)
        self.column.setSpacing(0)
        self.pin = None
        self.scroll = None
        self.column.addWidget(shown)

    def add_pin(self, pin, tip):
        self.pin = QToolButton()
        self.pin.setText("📌")
        self.pin.setAutoRaise(True)
        self.pin.setToolTip(tip)
        self.pin.clicked.connect(pin)
        bar = QHBoxLayout()
        bar.addStretch(1)
        bar.addWidget(self.pin)
        self.column.insertLayout(0, bar)

    def refresh(self):
        self.body.refresh()
        if self.scroll is not None:
            self.scroll.updateGeometry()   # its height is its block's (_WideScroll)
