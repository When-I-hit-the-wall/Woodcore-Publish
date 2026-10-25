"""«Coupe | Contributions», a service of the tabs that draw layers (spec docs/requirements/completed/2026-10-24-poids-propre-repense.md, UI-002, UI-003, REQ-008, REQ-009, ARCH-002, P09; issue #111): a module of the right pane, given as the service mounts (`ctx.pane_modules`), in the place of the domain's drawing.

**La coupe** is the domain's section of the layers (`section_svg(model, width)`) drawn again at the width the module has -- the legend mode under 560 units, the domain's rule --, the model asked of the domain (`layers(src, here)`, contracts.Layer, D-14); a click on a layer opens its line (`ctx.focus_field("layers[i]")`, `section_boxes`). **Les contributions** are three lists -- g_k alone, a_k alone, the two --, each layer's load and its part (`contributions(src, here)`). Its ⤢ opens a window whose body takes the window's size and follows it (module_pane.FillingWindow). No word, no number and no rule of the domain here: the words are the tab's (`<prefix>sec_*`).
"""

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget

import module_pane
import project
import richtext
import theme
import validation
from tab_host import Service, _n


class _Section(QSvgWidget):
    """The section drawn at the widget's width; a click opens the layer under it."""

    def __init__(self, body):
        super().__init__()
        self.body = body
        self.drawn_at = None
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumHeight(80)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.drawn_at != self.width():
            self.body.draw()

    def heightForWidth(self, width):
        size = self.renderer().defaultSize()
        return round(size.height() * width / size.width()) if size.width() > 0 else 80

    def hasHeightForWidth(self):
        return True

    def sizeHint(self):
        return QSize(max(self.width(), 300), self.heightForWidth(max(self.width(), 300)))

    def mousePressEvent(self, event):
        size = self.renderer().defaultSize()
        if size.width() <= 0:
            return
        scale = size.width() / max(self.width(), 1)
        x, y = event.position().x() * scale, event.position().y() * scale
        for number, bx, by, bw, bh in self.body.boxes:
            if bx <= x <= bx + bw and by <= y <= by + bh:
                self.body.ctx.focus_field("layers[%d]" % (number - 1))
                return


class _Body(QWidget):
    """The module's body: «Coupe» and «Contributions» one at a time under a segmented button."""

    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.model, self.boxes = [], []
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        self.which = QButtonGroup(self)
        for i, word in enumerate((ctx.t(ctx.prefix() + "sec_section"), ctx.t(ctx.prefix() + "sec_contributions"))):
            button = QPushButton(word)
            button.setCheckable(True)
            button.setChecked(i == 0)
            self.which.addButton(button, i)
            row.addWidget(button)
        row.addStretch(1)
        column.addLayout(row)
        self.stack = QStackedWidget()
        self.section = _Section(self)
        self.lists = QLabel()
        self.lists.setTextFormat(Qt.TextFormat.RichText)
        self.lists.setWordWrap(True)
        self.lists.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.stack.addWidget(self.section)
        self.stack.addWidget(self.lists)
        self.which.idClicked.connect(self.stack.setCurrentIndex)
        column.addWidget(self.stack, 1)

    def refresh(self):
        source = self.ctx.computed_source or {}
        try:
            self.model = self.ctx.module.layers(source, project.current()) if source.get("layers") else []
        except validation.ValidationError:
            self.model = []
        self.draw()
        self.show_lists(source)

    def draw(self):
        width = max(self.section.width(), 240)
        self.section.drawn_at = self.section.width()
        if not self.model:
            self.section.load(QByteArray(b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 1" width="10" height="1"/>'))
            self.boxes = []
            return
        svg = self.ctx.module.section_svg(self.model, width)
        self.boxes = self.ctx.module.section_boxes(self.model, width)
        self.section.load(QByteArray(svg.encode("utf-8")))
        self.section.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.section.setFixedHeight(self.section.heightForWidth(self.section.width() or width))

    def show_lists(self, source):
        """The three lists (REQ-008): each layer's number, its name, its load and its part."""
        t = self.ctx.t
        heads = {"gk": t(self.ctx.prefix() + "sec_gk"), "ak": t(self.ctx.prefix() + "sec_ak"), "all": t(self.ctx.prefix() + "sec_all")}
        try:
            lists, totals = self.ctx.module.contributions(source, project.current()) if source.get("layers") else ({}, {})
        except validation.ValidationError:
            lists, totals = {}, {}
        if not lists:
            self.lists.setText("<i>%s</i>" % richtext.escape(t(self.ctx.prefix() + "sec_none")))
            return
        muted = theme.colour("muted")
        parts = []
        for key in ("gk", "ak", "all"):
            rows = "".join("<tr><td>%d</td><td>%s</td><td align='right'>%s</td><td align='right' style='color:%s'>%s %%</td></tr>"
                           % (c["number"], richtext.escape(c["label"]), _n(round(c["load"], 3)), muted, _n(round(100 * c["share"], 1))) for c in lists[key])
            parts.append("<p><b>%s</b> = %s kN/m²</p><table cellspacing='4'>%s</table>" % (richtext.escape(heads[key]), _n(round(totals[key], 3)), rows))
        self.lists.setText("".join(parts))


class LayerSection(Service):
    """«Coupe | Contributions» -- see the module's docstring."""

    NAME = "section"
    NEEDS = ("layers", "section_svg", "section_boxes", "contributions")

    def mount(self, ctx):
        super().mount(ctx)
        ctx.pane_modules.append(module_pane.ModuleSpec("drawing", self.t(ctx.prefix() + "module_drawing"), lambda: _Body(ctx), kind="drawing", fills_window=True))
        return None
