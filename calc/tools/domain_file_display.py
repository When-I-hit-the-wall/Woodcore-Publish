"""«Affichage» of a calculation tab: the case's file, compiled, and every line of it set (spec 2026-10-22-onglet-neige-type, REQ-011 to REQ-015, UI-011, UI-012, D-7, D-8, D-17, D-23, D-28, D-29, D-30).

**In the centre** the file the export writes for the case (`Variable-loads/Snow/<id>.typ`), compiled as the report prints it -- the domain's title, the figure, then its `#var` and `#eq` -- and **every element the report hides shown all the same, pale and marked «masquée»** (`show-masked`, lib/calc-engine-core.typ; a masked figure, its line commented out, drawn here pale): the preview is no button and has no blue frame (D-8), Ctrl+wheel zooms it and the page follows the pane's width (`ZoomablePdfView`); it is a real page's height, so a note is set at its foot as in the PDF.

**On the right, one card** (D-7): the file, the command a section prints it by -- `#include domain-file("snow-load", "SN-01")`, which «Copier» copies --, the domain's **level of detail**, auto (the report's), 1, 2 or 3, written `#domain(…, level: n)` (D-30); then the section **«Éléments du fichier»**: every element with its command, its symbol and its label, and for a line its levels **0 1 2 3** -- the one it follows dotted, a click sets the line's own `level:`, a second click gives it back to the domain. A click on a line opens its arguments under it -- for `#var`, `#eq` and `#verify` those of its display (calc/line_display.py, read from lib/display-presets.json, the values lib/formula.typ takes), for an `#eq` its formula, units, label and description too, for the figure its width, caption, label and whether it is shown --, the line as the file writes it, and «Voir le fichier entier» (D-28: what Woodcore writes, read only). Every change is written into the file at once (calc/domains/unfold_display.py), and an export keeps it (D-17).

A subclass of display_view.DisplayView: the page, its banner and its compile are DisplayView's (`PdfPane.request_snippet`), the right pane is this module's. Every write goes through the tab's guarded writers (`write_line_display`, `write_figure`, `write_domain_level`: tab_guard.WRITERS), refused in a project open read-only. No word of a domain here.
"""

import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QComboBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
                               QPushButton, QToolButton, QVBoxLayout, QWidget)

import cards
import display_view
import line_display
import project
import richtext
import structure_preview
import theme
from domains import unfold, unfold_display
from plan_command_builder import CommandField

LEVELS = (0, 1, 2, 3)
WIDTHS = ("100%", "80%", "60%", "50%", "40%")
# The page the preview is set on: as tall as an A4, so that a note goes to its foot as in the PDF (UI-011)
PAGE_HEIGHT = "#set page(height: 29.7cm)"


class _LevelButtons(QWidget):
    """0 1 2 3 of a line: the one it follows dotted, its own filled."""

    def __init__(self, element, followed, choose):
        super().__init__()
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(2)
        own = element.get("level")
        self.buttons = {}
        for level in LEVELS:
            button = QToolButton()
            button.setText(str(level))
            button.setCheckable(True)
            button.setChecked(own == level)
            dotted = own is None and followed == level
            accent = theme.colour("accent")
            button.setStyleSheet("QToolButton { border: 1px %s %s; border-radius: 3px; padding: 0 5px; } QToolButton:checked { background: %s; color: %s; }"
                                 % ("dashed" if dotted else "solid", accent if dotted else theme.colour("line"), accent, theme.colour("on-primary")))
            button.setProperty("dotted", dotted)
            button.clicked.connect(lambda _c=False, n=level: choose(None if own == n else n))
            row.addWidget(button)
            self.buttons[level] = button


class DomainFileDisplay(display_view.DisplayView):
    """The «Affichage» view of a calculation tab -- see the module's docstring. `tab` is the tab (its words, its writers, its case)."""

    def __init__(self, tab, cache_key):
        super().__init__(tab.t, mono_font=tab.app.mono_font, copy=tab.app.copy, cache_key=cache_key, import_line=False, lang=tab.app.lang,
                         parent=tab, import_fn=lambda: tab.app.reexport(), import_text=tab.t("reexport"))
        self.tab = tab
        self.entry = None
        self.opened = None          # the element whose arguments are open
        self.whole = False
        self.elements = []
        # DisplayView's own right pane, with its drop-down of the commands, kept alive and out of sight: the window and its tests read `chooser`, which lists the one command this view prints
        self.command_pane = self.right
        self.right = QWidget()
        column = QVBoxLayout(self.right)
        column.setContentsMargins(0, 0, 0, 0)
        scroll, self.column = cards.column()
        column.addWidget(scroll)
        self.card = cards.card(tab.t("ct_file"))
        self.body = QVBoxLayout(self.card)
        self.column.addWidget(self.card)
        self.column.addStretch(1)

    # -- what the tab says --

    def set_entries(self, entries):
        self.entry = entries[0] if entries else None
        self.filling = True
        try:
            self.chooser.clear()
            if self.entry is not None:
                self.chooser.addItem(self.entry.title, self.entry.key)
        finally:
            self.filling = False
        self.rebuild()
        self.refresh()

    def current(self):
        return self.entry

    def command(self):
        return self.entry.call if self.entry is not None else ""

    def path(self):
        """The case's file, or None where it is not written yet."""
        if self.here is None or not self.tab.current_id:
            return None
        found = unfold.domain_path(self.here, self.tab.current_id, kind=self.tab.MODULE.DOMAIN)
        return found if found.is_file() else None

    def source(self):
        """The page compiled: the snippet's header on a page an A4 high, `show-masked` set, then the case's file -- its masked figure drawn pale and marked."""
        path = self.path()
        if path is None or self.here is None:
            return None
        lines = structure_preview.header(self.here, self.mode) + [PAGE_HEIGHT, "#show-masked.update(true)", ""]
        mark = self.t("ct_masked")
        for line in path.read_text(encoding="utf-8").split("\n"):
            if line.lstrip().startswith("#import"):
                continue
            parts = unfold_display.figure_parts(line)
            if parts and parts["masked"]:
                body = line.lstrip()[2:].lstrip()
                body = body[:body.rfind(" <")] if body.endswith(">") else body
                line = "#block[#set text(fill: luma(150))\n%s\n#align(center, text(size: 0.75em, style: \"italic\")[(%s)])]" % (body, mark)
            lines.append(line)
        return "\n".join(lines) + "\n"

    def refresh(self):
        entry = self.entry
        if entry is not None and self.path() is None and not entry.note_text:
            entry.note_text = self.t("ct_not_written")
        super().refresh()

    # -- the right pane --

    def rebuild(self):
        """The card again: the file, the command, the domain's level, the elements -- read from the file as it stands."""
        while self.body.count():
            item = self.body.takeAt(0)
            if item.widget() is not None:
                item.widget().setParent(None)
        path = self.path()
        here = self.here
        name = QLabel(here.from_root(path) if path is not None and here is not None else self.t("ct_not_written"))
        name.setWordWrap(True)
        name.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.body.addWidget(name)
        self.body.addWidget(QLabel(self.t("ct_command")))
        field = CommandField("", self.tab.app.mono_font if hasattr(self.tab.app, "mono_font") else None)
        field.set_code(self.command())
        self.field = field
        row = QHBoxLayout()
        row.addWidget(field, 1)
        self.copy_button = richtext.copy_button(self.t("ds_copy"), self.t("ds_copied"), lambda: self.copy_text(self.command()))
        row.addWidget(self.copy_button)
        self.body.addLayout(row)
        self.elements = []
        if path is None or here is None:
            return
        try:
            with project.using(here):
                self.elements = unfold_display.elements(here, self.tab.current_id, self.tab.MODULE.DOMAIN)
        except unfold.UnfoldError as exc:
            self.body.addWidget(QLabel(str(exc)))
            return
        try:
            with project.using(here):
                matches = unfold.status(here, self.tab.current_id, kind=self.tab.MODULE.DOMAIN).matches
        except unfold.UnfoldError:
            matches = True
        if not matches:
            # a file of an earlier form (D-18): said, and written again only on the engineer's word
            said = QLabel(self.t("ct_form_changed"))
            said.setWordWrap(True)
            said.setProperty("callout", "warning")
            self.body.addWidget(said)
            self.regenerate_button = QPushButton(self.t("ct_regenerate"))
            self.regenerate_button.clicked.connect(lambda: self.tab.write_unfold_regenerate())
            self.body.addWidget(self.regenerate_button)
        header = self.elements[0]
        level_row = QHBoxLayout()
        level_row.addWidget(QLabel(self.t("ct_level")))
        self.level_group = QButtonGroup(self.card)
        self.level_buttons = {}
        for value in (None, 1, 2, 3):
            button = QPushButton(self.t("ct_level_auto") if value is None else str(value))
            button.setCheckable(True)
            button.setChecked(header["level"] == value)
            button.setToolTip(self.t("ct_level_tip"))
            button.clicked.connect(lambda _c=False, v=value: self.tab.write_domain_level(v))
            self.level_group.addButton(button)
            level_row.addWidget(button)
            self.level_buttons[value] = button
        level_row.addStretch(1)
        self.body.addLayout(level_row)
        title = QLabel(self.t("ct_elements"))
        title.setStyleSheet("font-weight: 600; margin-top: 8px;")
        title.setToolTip(self.t("ct_elements_tip"))
        self.body.addWidget(title)
        followed = header["level"] if header["level"] is not None else structure_preview.LEVEL
        self.rows = {}
        for element in self.elements[1:]:
            self.body.addWidget(self._row(element, followed))
            if element["id"] == self.opened:
                self.body.addWidget(self._arguments(element))

    def _row(self, element, followed):
        row = QFrame()
        row.setObjectName("elementRow")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(2, 2, 2, 2)
        command = QLabel("#figure" if element["kind"] == "figure" else "#" + element["kind"])
        command.setStyleSheet("color: %s; font-family: monospace;" % theme.colour("syn-call"))
        layout.addWidget(command)
        if element["kind"] == "figure":
            symbol = QLabel(element.get("caption") or element.get("label") or "")
        else:
            symbol = QLabel(richtext.math_html(element["symbol"]))
            symbol.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(symbol)
        label = QLabel(element.get("label", "") if element["kind"] != "figure" else "")
        label.setStyleSheet("color: %s;" % theme.colour("muted"))
        layout.addWidget(label, 1)
        masked = element.get("masked") or element.get("level") == 0 or (element.get("level") is None and followed == 0)
        if masked:
            mark = QLabel(self.t("ct_masked"))
            mark.setStyleSheet("color: %s; font-style: italic;" % theme.colour("muted"))
            layout.addWidget(mark)
        if element["kind"] != "figure":
            layout.addWidget(_LevelButtons(element, followed, lambda level, lid=element["id"]: self.tab.write_line_display(lid, {"level": level})))
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        row.mousePressEvent = lambda _event, lid=element["id"]: self.open(lid)
        if element["id"] == self.opened:
            row.setStyleSheet("#elementRow { background: %s; border-radius: 4px; }" % theme.colour("accent-soft"))
        self.rows[element["id"]] = row
        return row

    def open(self, line_id):
        """A line clicked (T61): its arguments opened under it -- a second click closes them."""
        self.opened = None if self.opened == line_id else line_id
        self.rebuild()

    def _arguments(self, element):
        box = QFrame()
        box.setObjectName("elementArguments")
        column = QVBoxLayout(box)
        column.setContentsMargins(12, 4, 4, 8)
        form = QFormLayout()
        lid = element["id"]
        if element["kind"] == "figure":
            show = QCheckBox(self.t("ct_show_figure"))
            show.setChecked(not element["masked"])
            show.toggled.connect(lambda on: self.tab.write_figure(lid, shown=on))
            form.addRow("", show)
            width = QComboBox()
            width.setEditable(True)
            width.addItems(WIDTHS)
            width.setCurrentText(element["width"])
            width.lineEdit().editingFinished.connect(lambda: self.tab.write_figure(lid, width=width.currentText().strip()))
            width.activated.connect(lambda _i: self.tab.write_figure(lid, width=width.currentText().strip()))
            form.addRow(self.t("ct_width"), width)
            for key, words in (("caption", "ct_caption"), ("label", "ct_label")):
                line = QLineEdit(element[key])
                line.editingFinished.connect(lambda k=key, l=line: self.tab.write_figure(lid, **{k: l.text()}))
                form.addRow(self.t(words), line)
        else:
            values = line_display.fine_values()
            for name in line_display.display_args(element["kind"]):
                if name == "level":
                    continue
                combo = QComboBox()
                combo.addItem(self.t("ct_level_auto"), None)
                for value in values.get(name, ()):
                    combo.addItem(value, value)
                combo.setCurrentIndex(max(combo.findData(element["options"].get(name)), 0))
                combo.activated.connect(lambda _i, n=name, c=combo: self.tab.write_line_display(lid, {n: c.currentData()}))
                form.addRow(name, combo)
            for name in unfold_display.WRITABLE.get(element["kind"], ()):
                line = QLineEdit()
                line.setPlaceholderText(self.t("ct_level_auto"))
                line.editingFinished.connect(lambda n=name, l=line: self.tab.write_line_display(lid, {n: l.text().strip() or None}))
                form.addRow(name, line)
        column.addLayout(form)
        column.addWidget(QLabel(self.t("ct_written")))
        written = QPlainTextEdit(element["line"])
        written.setReadOnly(True)
        written.setMaximumHeight(70)
        written.setFont(self.field.font())
        column.addWidget(written)
        whole = QPushButton(self.t("ct_whole_file"))
        whole.setCheckable(True)
        whole.setChecked(self.whole)
        column.addWidget(whole)
        text = QPlainTextEdit(self.path().read_text(encoding="utf-8") if self.path() is not None else "")
        text.setReadOnly(True)
        text.setMinimumHeight(260)
        text.setVisible(self.whole)
        whole.toggled.connect(lambda on: (setattr(self, "whole", on), text.setVisible(on)))
        column.addWidget(text)
        return box
