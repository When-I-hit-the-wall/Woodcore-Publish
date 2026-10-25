"""Every case of a tab at a glance, a service (spec docs/requirements/completed/2026-10-24-poids-propre-repense.md, REQ-011, UI-004, P06; issue #111): «⊞ Vue d'ensemble» at the head of the list, and, in the centre in place of the case open, a table of every case -- a small section, its id and its name, its number of layers, g_k, a_k, their sum, the retained value (bold, orange where it was written), its state, «complète» or the number of red messages to correct -- with, on its right, the red messages of all of them, each with its case's id.

What it shows is the domain's (`overview(here)`: dead_load_overview), drawn here; a line clicked opens its case, which takes the centre back (`fill`). The centre's two pages are the host's (`overview_widget`, `ctx.show_overview`). Its words are the tab's (`<prefix>ov_*`).
"""

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QAbstractItemView, QHBoxLayout, QHeaderView, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

import project
import richtext
import theme
import validation
from tab_host import Service, _n

COLUMNS = ("section", "id", "name", "layers", "gk", "ak", "total", "retained", "state")
THUMB = 150     # the small section's width


class Overview(Service):
    """«⊞ Vue d'ensemble» -- see the module's docstring."""

    NAME = "overview"
    ZONE = "left"
    NEEDS = ("overview", "section_svg")

    def mount(self, ctx):
        super().mount(ctx)
        self.lines = []
        self.button = QPushButton("⊞ " + self.t(ctx.prefix() + "ov_title"))
        self.button.setCheckable(True)
        self.button.clicked.connect(lambda on: self.show(on))
        ctx.overviewShown.connect(self.button.setChecked)
        return self.button

    def overview_widget(self):
        page = QWidget()
        row = QHBoxLayout(page)
        row.setContentsMargins(0, 0, 0, 0)
        left = QVBoxLayout()
        heading = QLabel("<b>%s</b>" % richtext.escape(self.t(self.ctx.prefix() + "ov_title")))
        left.addWidget(heading)
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels([self.t(w) for w in (self.ctx.prefix() + "ov_section", self.ctx.prefix() + "ov_id", self.ctx.prefix() + "ov_name", self.ctx.prefix() + "ov_layers", self.ctx.prefix() + "ov_gk", self.ctx.prefix() + "ov_ak",
                                                                self.ctx.prefix() + "ov_total", self.ctx.prefix() + "ov_retained", self.ctx.prefix() + "ov_state")])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(COLUMNS.index("name"), QHeaderView.ResizeMode.Stretch)
        self.table.cellClicked.connect(self.open_line)
        left.addWidget(self.table, 1)
        row.addLayout(left, 3)
        self.problems = QLabel()
        self.problems.setTextFormat(Qt.TextFormat.RichText)
        self.problems.setWordWrap(True)
        self.problems.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.problems.setMinimumWidth(220)
        row.addWidget(self.problems, 1)
        return page

    def show(self, on=True):
        """The overview shown (computed again from the project's files) or the case open shown again."""
        if on:
            self.refresh_overview()
        self.ctx.show_overview(on)

    def fill(self, src):
        """A case filled into the form -- opened, made, reverted --: the centre is the case again."""
        if self.ctx.overview:
            self.ctx.show_overview(False)

    def refresh_overview(self):
        try:
            self.lines = self.ctx.module.overview(project.current())
        except validation.ValidationError as exc:
            self.lines = []
            self.problems.setText("<span style='color:%s'>%s</span>" % (theme.colour("danger"), richtext.escape(str(exc))))
            return
        danger = theme.colour("danger")
        self.table.setRowCount(len(self.lines))
        said = []
        for r, line in enumerate(self.lines):
            if line["model"]:
                thumb = QSvgWidget()
                svg = self.ctx.module.section_svg(line["model"], THUMB * 3, False)
                thumb.load(QByteArray(svg.encode("utf-8")))
                thumb.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
                thumb.setFixedSize(THUMB, 54)
                self.table.setCellWidget(r, 0, thumb)
                self.table.setRowHeight(r, 58)
            values = {"id": line["id"], "name": line["name"], "layers": str(line["layers"]),
                      "gk": _n(round(line["gk"], 3)) if line["gk"] is not None else "—", "ak": _n(round(line["ak"], 3)) if line["ak"] is not None else "—",
                      "total": _n(round(line["total"], 3)) if line["total"] is not None else "—",
                      "retained": _n(line["retained"]) if line["retained"] is not None else "—",
                      "state": self.t(self.ctx.prefix() + "ov_complete") if line["state"] == "complete" else self.t(self.ctx.prefix() + "ov_to_fix", count=line["to_fix"])}
            for c, key in enumerate(COLUMNS[1:], 1):
                item = QTableWidgetItem(values[key])
                if key == "retained":
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                    if line["replaced"]:
                        item.setForeground(theme.qcolor("warning"))
                if key == "state" and line["state"] != "complete":
                    item.setForeground(theme.qcolor("danger"))
                self.table.setItem(r, c, item)
            for m in line["problems"]:
                said.append("<b>%s</b> %s" % (richtext.escape(line["id"]), richtext.escape(self.ctx.message_text(m))))
            if line["malformed"]:
                said.append("<b>%s</b> %s" % (richtext.escape(line["id"]), richtext.escape(line["malformed"])))
        self.problems.setText(("<span style='color:%s'>" % danger) + "<br>".join(said) + "</span>" if said else
                              "<i>%s</i>" % richtext.escape(self.t(self.ctx.prefix() + "ov_no_problem")))

    def open_line(self, row, _column):
        """A line clicked: its case opened, the centre its form again."""
        if 0 <= row < len(self.lines):
            self.ctx.load(self.lines[row]["id"])
            self.ctx.show_overview(False)
