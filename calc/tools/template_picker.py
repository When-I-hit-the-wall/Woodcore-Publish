"""«Nouveau…» with templates, a service (spec docs/requirements/completed/2026-10-24-poids-propre-repense.md, REQ-010, UI-004, T46, T58, P07; issue #111): the list's «Nouveau» asks first what to start from -- «Modèles Lignum», «Mes modèles» (this computer's), or «Composition vide».

Each template is a card: its small section, its number of layers, its sum in kN/m² and kg/m², its reference, what it supposes, the book's weight where the book gives one -- and «Créer depuis ce modèle», which copies it into a new case of the project (`from_template`); one of the engineer's own may be deleted. What it shows is the domain's (`templates()`, `template_summary`, `section_svg`); the dialog only draws it. `choose(template)` is the choice made, without the dialog -- what a test calls. Its words are the tab's (`<prefix>tpl_*`).
"""

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QTabWidget, QVBoxLayout, QWidget)

import project
import richtext
import theme
import validation
from tab_host import Service, _n

CARD_SECTION = 360      # the card's section, its width in the drawing's units


class _Dialog(QDialog):
    """The choice of what a new case starts from -- see the module's docstring. `chosen` is the template chosen, None for an empty case; the dialog accepted either way."""

    def __init__(self, picker, parent):
        super().__init__(parent)
        self.picker, self.ctx, self.chosen = picker, picker.ctx, None
        t = self.ctx.t
        self.setWindowTitle(t(self.ctx.prefix() + "tpl_title"))
        self.resize(900, 640)
        column = QVBoxLayout(self)
        tabs = QTabWidget()
        shipped, mine, problems = self.ctx.module.templates()
        tabs.addTab(self._page(shipped, False), t(self.ctx.prefix() + "tpl_lignum"))
        tabs.addTab(self._page(mine, True, problems), t(self.ctx.prefix() + "tpl_mine"))
        column.addWidget(tabs, 1)
        row = QHBoxLayout()
        empty = QPushButton(t(self.ctx.prefix() + "tpl_empty"))
        empty.clicked.connect(lambda: self._take(None))
        cancel = QPushButton(t(self.ctx.prefix() + "tpl_cancel"))
        cancel.clicked.connect(self.reject)
        row.addWidget(empty)
        row.addStretch(1)
        row.addWidget(cancel)
        column.addLayout(row)

    def _take(self, template):
        self.chosen = template
        self.accept()

    def _page(self, templates, mine, problems=()):
        t = self.ctx.t
        inner = QWidget()
        column = QVBoxLayout(inner)
        if not templates:
            column.addWidget(QLabel("<i>%s</i>" % richtext.escape((t(self.ctx.prefix() + "tpl_mine_none") if mine else t(self.ctx.prefix() + "tpl_none")))))
        for problem in problems:
            note = QLabel(richtext.escape(problem))
            note.setStyleSheet("color: %s;" % theme.colour("danger"))
            note.setWordWrap(True)
            column.addWidget(note)
        for template in templates:
            column.addWidget(self._card(template, mine))
        column.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner)
        return scroll

    def _card(self, template, mine):
        ctx, t, lang = self.ctx, self.ctx.t, self.ctx.app.lang
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        row = QHBoxLayout(card)
        summary = ctx.module.template_summary(template, project.current())
        if summary["model"]:
            section = QSvgWidget()
            section.load(QByteArray(ctx.module.section_svg(summary["model"], CARD_SECTION, True).encode("utf-8")))
            section.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
            section.setFixedSize(220, 160)
            row.addWidget(section)
        words = QVBoxLayout()
        lines = ["<b>%s</b>" % richtext.escape(ctx.module.template_name(template, lang))]
        weight = (t(self.ctx.prefix() + "tpl_sum", layers=summary["layers"], total=_n(round(summary["total"], 3)), kg=_n(round(summary["total_kg"])))
                  if summary["total"] is not None else t(self.ctx.prefix() + "tpl_layers", layers=summary["layers"]))
        lines.append(richtext.escape(weight))
        reference = template.get("reference")
        if reference:
            lines.append(richtext.escape(t(self.ctx.prefix() + "tpl_reference", book=reference["book"], where=reference["where"], page=reference["page"])))
        book = template.get("book_weight")
        if book:
            lines.append(richtext.escape(t(self.ctx.prefix() + "tpl_book", value=_n(book["value"]), unit=book["unit"])))
        assumptions = (template.get("assumptions") or {})
        said = assumptions.get(lang) or next(iter(assumptions.values()), "")
        if said:
            lines.append("<span style='color:%s'>%s</span>" % (theme.colour("muted"), richtext.escape(said)))
        for m in summary["problems"]:
            lines.append("<span style='color:%s'>%s</span>" % (theme.colour("danger"), richtext.escape(ctx.message_text(m))))
        text = QLabel("<br>".join(lines))
        text.setTextFormat(Qt.TextFormat.RichText)
        text.setWordWrap(True)
        words.addWidget(text)
        buttons = QHBoxLayout()
        create = QPushButton(t(self.ctx.prefix() + "tpl_create"))
        create.clicked.connect(lambda: self._take(template))
        buttons.addWidget(create)
        if mine:
            delete = QPushButton(t(self.ctx.prefix() + "tpl_delete"))
            delete.clicked.connect(lambda: self._delete(template, card))
            buttons.addWidget(delete)
        buttons.addStretch(1)
        words.addLayout(buttons)
        row.addLayout(words, 1)
        return card

    def _delete(self, template, card):
        try:
            self.ctx.module.delete_template(template["id"])
        except validation.ValidationError as exc:
            self.ctx.fail(str(exc))
            return
        card.setParent(None)
        card.deleteLater()


class TemplatePicker(Service):
    """«Nouveau…» with templates -- see the module's docstring."""

    NAME = "templates"
    NEEDS = ("templates", "template_summary", "from_template", "delete_template", "template_name", "section_svg")

    def pick_new(self):
        """«Nouveau» of the list: the choice asked, then the case made from it, the draft left first (draft_logic.new_from) -- nothing where the dialog is closed."""
        dialog = _Dialog(self, self.ctx.host)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.choose(dialog.chosen)

    def choose(self, template):
        """A new case from `template` -- an empty one where it is None (REQ-010: «Créer depuis ce modèle» copies the template into the project, at the save)."""
        if template is None:
            self.ctx.new_from(None)
            return
        cid = self.ctx.host.make_source()["id"]
        self.ctx.new_from(self.ctx.module.from_template(template, cid, self.app.lang))
