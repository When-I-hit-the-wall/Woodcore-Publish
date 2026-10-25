"""The page of a command in the commands tab, condensed (spec 2026-10-24-onglet-commandes-pages, UI-003 to UI-009, D-20, ARCH-007, ARCH-008).

What it shows is command_page's data, turned into widgets and nothing more: the head (`#name`, the category, the lead), **the line of the command** in a read-only QTextBrowser -- each argument's name a link that opens its bubble, each default a link that opens the bubble of its values, the required in bold, the names underlined with dots --, the hint under it, «L'essentiel», the arguments as a table in groups, the names written by name, and the examples (command_examples). The bubbles are hover_bubble's: an argument's, 380 px, its status and its sentence; a value's, up to 860, the list of the values on the left and, for the one hovered, its call and its print cut out of its command's sheet on the right (examples/out/values/) -- never a compile (REQ-012). Every colour is theme.json's, every word reference.json's (command_docs.word) but the window's own chrome (commands_tab.STRINGS).
"""

import html

import build_examples as examples
import build_reference as ref
import command_docs as docs
import command_page as page_model
import command_pages as pages
import richtext
import theme
from command_examples import ExampleBox, ExampleRenderer, muted, plain_label
from hover_bubble import HoverController
from PySide6.QtCore import QPoint, QRect, Qt, QTimer
from PySide6.QtGui import QCursor, QPixmap, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QTextBrowser, QTextEdit, QVBoxLayout, QWidget)

ARG_WIDTH = 380
VALUE_WIDTH = 860
FLASH_MS = 1200
SECTION_GAP = 10


def rich(text, mono):
    """One sentence of a page as rich text: its code between backticks in the fixed font on the code ground, the rest escaped (command_docs.prose)."""
    return docs.prose(text, lambda code: f'<span style="font-family:\'{mono}\'; background-color:{theme.colour("bg-sunk")};">{html.escape(code)}</span>',
                      lambda words: html.escape(words, quote=False), r"<b>\1</b>", r"<i>\1</i>")


def rich_label(text, mono, wrap=True):
    label = QLabel(rich(text, mono))
    label.setTextFormat(Qt.TextFormat.RichText)
    label.setWordWrap(wrap)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return label


def line_html(lines, mono):
    """The line of the command as rich text, its links `arg:name` and `val:name` (command_page.line)."""
    out = []
    for row in lines:
        parts = []
        for segment in row:
            text = html.escape(segment["text"]).replace(" ", "&nbsp;")
            if segment["kind"] == "cmd":
                parts.append(f'<span style="color:{theme.colour("syn-call")};">{text}</span>')
            elif segment["kind"] == "arg":
                weight = "font-weight:bold; " if segment["required"] else ""
                colour = theme.colour("ink") if segment["required"] else theme.colour("syn-math")
                parts.append(f'<a href="arg:{html.escape(segment["arg"])}" style="{weight}color:{colour}; text-decoration:none;">{text}</a>')
            elif segment["kind"] == "value":
                parts.append(f'<a href="val:{html.escape(segment["arg"])}" style="color:{theme.colour("wood")}; background-color:{theme.colour("bg-sunk")}; text-decoration:none;">&nbsp;{text}&nbsp;<span style="color:{theme.colour("muted")};">▾</span></a>')
            else:
                parts.append(text)
        out.append("".join(parts))
    return f'<div style="font-family:\'{mono}\';">' + "<br/>".join(out) + "</div>"


class CommandLine(QTextBrowser):
    """The line of the command: read-only, its links the bubbles' triggers, the arguments' names underlined with dots (ARCH-RISK-001: Qt's rich text knows no dotted underline, so it is set on the document's characters after the HTML)."""

    def __init__(self, lines, mono_font):
        super().__init__()
        self.hover_trigger = True
        self.setObjectName("code")
        self.setOpenLinks(False)
        self.setFont(mono_font)
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHtml(line_html(lines, mono_font.family()))
        self.text_plain = page_model.line_text(lines)
        self._dot_the_names()
        self.lines = len(lines)
        self.fit()

    def _dot_the_names(self):
        document = self.document()
        cursor = QTextCursor(document)
        position = 0
        end = document.characterCount() - 1
        dotted = QTextCharFormat()
        dotted.setUnderlineStyle(QTextCharFormat.UnderlineStyle.DotLine)
        while position < end:
            cursor.setPosition(position)
            cursor.setPosition(position + 1, QTextCursor.MoveMode.KeepAnchor)
            if cursor.charFormat().anchorHref().startswith("arg:"):
                cursor.mergeCharFormat(dotted)
            position += 1

    def fit(self):
        height = self.document().size().height() + 2 * self.frameWidth() + 6
        bar = self.horizontalScrollBar()
        if bar.maximum() > 0:
            height += bar.sizeHint().height()
        self.setFixedHeight(round(height))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit()


class ValueRow(QLabel):
    """One value in the bubble of the values: hovered, it shows its call and its print beside the list."""

    def __init__(self, html_text, on_hover):
        super().__init__(html_text)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setWordWrap(True)
        self.on_hover = on_hover
        self.setMouseTracking(True)

    def enterEvent(self, event):
        self.on_hover()
        super().enterEvent(event)


class CommandPage(QWidget):
    """The centre of the tab: one command's page, a category's head, or the hint. The examples' renderer and the bubbles are its own (ARCH-007)."""

    def __init__(self, ctx, state=None):
        super().__init__()
        self.ctx = ctx
        self.app, self.lang, self.t = ctx.app, ctx.lang, ctx.t
        state = state or {}
        self.levels = dict(state.get("levels") or {})
        self.renderer = ExampleRenderer(ctx.t, ctx.lang, self)
        self.bubble = HoverController(self)
        self.sheets = {}
        self.parts = []
        self.boxes = []
        self.record = None
        self.line = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(self.scroll)
        self.bubble.watch_scroll(self.scroll.verticalScrollBar())
        self.body = QWidget()
        self.scroll.setWidget(self.body)

    # -- what the examples ask of their host --

    def word(self, key, **values):
        return docs.word(key, self.lang, **values)

    def copy_button(self, text):
        return richtext.copy_button(self.t("copy"), self.t("copied_short"), lambda: self.app.copy(text))

    def level_of(self, command, index):
        return self.levels.get(f"{command}|{index}", 2)

    def remember_level(self, command, index, level):
        self.levels[f"{command}|{index}"] = level

    # -- the life of the component --

    def shown(self):
        pass

    def hidden(self):
        self.renderer.stop()
        self.bubble.close()

    def state(self):
        return {"levels": {k: v for k, v in self.levels.items() if v != 2}}

    def restore(self, state):
        self.levels = dict((state or {}).get("levels") or {})

    # -- the page --

    def add(self, layout, name, widget):
        self.parts.append((name, widget))
        layout.addWidget(widget)
        return widget

    def heading(self, text):
        label = plain_label(text)
        label.setFont(self.app.bold_font)
        return label

    def title_font(self, mono=True):
        from PySide6.QtGui import QFont
        font = QFont(self.app.mono_font if mono else self.app.bold_font)
        if self.app.title_font.pointSizeF() > 0:
            font.setPointSizeF(self.app.title_font.pointSizeF())
        font.setBold(True)
        return font

    def set_selection(self, iid, record):
        self.bubble.close()
        self.parts, self.boxes = [], []
        self.record = record
        self.line = None
        self.renderer.new_page()
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(14, 8, 8, 12)
        layout.setSpacing(6)
        try:
            has_page = record is not None and record["category"] != ref.INTERNAL and pages.entry(record["name"]) is not None
        except pages.PagesError as exc:   # a malformed command-pages.json stops the page, naming the file and the field, and not the window
            self.add(layout, "error", plain_label(self.t("ref_pages_error", error=str(exc)), wrap=True))
            layout.addStretch(1)
            self.scroll.setWidget(body)
            self.body = body
            return
        if has_page:
            self.fill_page(layout, record)
        elif record is not None:
            self.fill_internal(layout, record)
        elif iid.startswith("cat|"):
            self.fill_category(layout, iid[4:])
        else:
            self.add(layout, "hint", plain_label(self.t("ref_hint"), wrap=True))
        layout.addStretch(1)
        self.scroll.setWidget(body)
        self.body = body

    def fill_category(self, layout, key):
        self.add(layout, "title", plain_label(docs.category_label(key, self.lang))).setFont(self.title_font(mono=False))
        lead = docs.category_lead(key, self.lang) if key != ref.INTERNAL else self.t("ref_internal_note")
        self.add(layout, "lead", rich_label(lead, self.app.mono_font.family()))
        self.add(layout, "hint", muted(plain_label(self.t("ref_hint"), wrap=True)))

    def fill_internal(self, layout, record):
        self.add(layout, "title", plain_label(record["name"])).setFont(self.title_font())
        self.add(layout, "signature", muted(plain_label(record.get("signature") or "", wrap=True))).setFont(self.app.mono_font)
        self.add(layout, "note", muted(plain_label(self.t("ref_internal_note"), wrap=True)))
        self.add(layout, "defined", muted(plain_label(f"{self.word('defined_in')} lib/{record['file']}:{record['line']}")))

    def fill_page(self, layout, record):
        mono = self.app.mono_font.family()
        view = page_model.view(record, self.lang)
        head = QWidget()
        row = QHBoxLayout(head)
        row.setContentsMargins(0, 0, 0, 0)
        title = plain_label(f"#{record['name']}")
        title.setFont(self.title_font())
        row.addWidget(title)
        chip = plain_label(view["category_label"])
        chip.setStyleSheet(f"color:{theme.colour('accent-strong')}; background:{theme.colour('accent-soft')}; border-radius:8px; padding:1px 8px;")
        row.addWidget(chip, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addStretch(1)
        self.add(layout, "head", head)
        self.add(layout, "lead", rich_label(view["lead"], mono))

        self.line = self.add(layout, "line", CommandLine(view["line"], self.app.mono_font))
        self.line.highlighted.connect(lambda url: self.on_line_hover(url.toString()))
        self.line.anchorClicked.connect(lambda url: self.open_bubble(url.toString(), self.cursor_rect(), pin=True))
        self.add(layout, "hint", muted(plain_label(view["hint"], wrap=True)))

        cards = QWidget()
        grid = QGridLayout(cards)
        grid.setContentsMargins(0, 4, 0, 0)
        grid.setSpacing(8)
        for i, key in enumerate(view["keys"]):
            card = QFrame()
            card.setStyleSheet(f"QFrame#keycard {{ background:{theme.colour('card')}; border:1px solid {theme.colour('line')}; border-left:3px solid {theme.colour('accent')}; border-radius:6px; }}")
            card.setObjectName("keycard")
            column = QVBoxLayout(card)
            column.setContentsMargins(10, 6, 10, 8)
            column.setSpacing(2)
            name = rich_label(key["title"], mono)
            name.setFont(self.app.bold_font)
            column.addWidget(name)
            column.addWidget(rich_label(key["text"], mono))
            grid.addWidget(card, i // 2, i % 2)
        layout.addSpacing(SECTION_GAP)
        self.add(layout, "essentials", self.heading(self.word("essentials")))
        self.add(layout, "keys", cards)

        layout.addSpacing(SECTION_GAP)
        if view["groups"]:
            self.add(layout, "arguments", self.heading(self.word("arguments")))
            self.add(layout, "argument_table", self.argument_table(view))
        if view["note"]:
            self.add(layout, "note", muted(rich_label(view["note"], mono)))

        layout.addSpacing(SECTION_GAP)
        if record["examples"]:
            self.add(layout, "examples", self.heading(self.word("examples")))
        else:
            self.add(layout, "no_examples", plain_label(self.t("ref_no_examples"), wrap=True))
        for index, example in enumerate(record["examples"]):
            box = ExampleBox(self, record, index, example)
            self.boxes.append(box)
            self.add(layout, "example", box)
        self.add(layout, "defined", muted(plain_label(f"{self.word('defined_in')} lib/{record['file']}:{record['line']}")))

    def argument_table(self, view):
        """The arguments in groups (UI-005): Argument · Status · what it does and its examples; a default in its box opens the bubble of the values; the names written by name last."""
        mono = self.app.mono_font.family()
        table = QWidget()
        grid = QGridLayout(table)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(6)
        grid.setColumnStretch(2, 1)
        for column, text in enumerate(view["columns"]):
            header = muted(plain_label(text))
            header.setFont(self.app.bold_font)
            grid.addWidget(header, 0, column)
        row = 1
        top = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        self.table_rows = []
        for group in view["groups"]:
            band = plain_label(group["label"])
            band.setFont(self.app.bold_font)
            band.setStyleSheet(f"background:{theme.colour('bg-sunk')}; color:{theme.colour('ink-soft')}; padding:3px 6px;")
            grid.addWidget(band, row, 0, 1, 3)
            row += 1
            for arg in group["rows"]:
                weight = "font-weight:bold; " if arg["required"] else ""
                name = self.link_label(f'<a href="arg:{html.escape(arg["name"])}" style="{weight}color:{theme.colour("ink") if arg["required"] else theme.colour("syn-math")}; text-decoration:none; font-family:\'{mono}\';">{html.escape(arg["name"])}</a>')
                grid.addWidget(name, row, 0, top)
                if arg["required"]:
                    status = f'<span style="color:{theme.colour("danger")}; background:{theme.colour("danger-soft")};">&nbsp;{html.escape(arg["status"])}&nbsp;</span>'
                else:
                    status = f'<span style="color:{theme.colour("ink-soft")};">{html.escape(arg["status"])}</span>'
                    if arg["default"] is not None:
                        status += (f' <a href="val:{html.escape(arg["name"])}" style="color:{theme.colour("wood")}; background-color:{theme.colour("bg-sunk")}; text-decoration:none; font-family:\'{mono}\';">'
                                   f'&nbsp;{html.escape(str(arg["default"]))}&nbsp;▾</a>')
                grid.addWidget(self.link_label(status), row, 1, top)
                cell = QWidget()
                column = QVBoxLayout(cell)
                column.setContentsMargins(0, 0, 0, 0)
                column.setSpacing(2)
                column.addWidget(rich_label(arg["text"], mono))
                for example in arg["examples"]:
                    shows = f' <span style="color:{theme.colour("muted")};">{rich(example["shows"], mono)}</span>' if example["shows"] else ""
                    line = QLabel(f'<span style="font-family:\'{mono}\'; background-color:{theme.colour("code-bg")};">{html.escape(example["code"])}</span>{shows}')
                    line.setTextFormat(Qt.TextFormat.RichText)
                    line.setWordWrap(True)
                    line.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                    column.addWidget(line)
                grid.addWidget(cell, row, 2)
                self.table_rows.append(arg["name"])
                row += 1
        if view["named"]:
            band = plain_label(view["named"]["label"])
            band.setFont(self.app.bold_font)
            band.setStyleSheet(f"background:{theme.colour('bg-sunk')}; color:{theme.colour('ink-soft')}; padding:3px 6px;")
            grid.addWidget(band, row, 0, 1, 3)
            row += 1
            grid.addWidget(rich_label(view["named"]["text"], mono), row, 0, 1, 3)
            self.named_row = view["named"]["members"]
        return table

    def link_label(self, html_text):
        label = QLabel(html_text)
        label.hover_trigger = True
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse | Qt.TextInteractionFlag.LinksAccessibleByKeyboard)
        label.linkHovered.connect(lambda href, l=label: self.on_label_hover(href, l))
        label.linkActivated.connect(lambda href, l=label: self.open_bubble(href, self.widget_rect(l), pin=True))
        return label

    # -- the bubbles --

    def cursor_rect(self):
        return QRect(QCursor.pos() - QPoint(8, 10), QCursor.pos() + QPoint(8, 10))

    def widget_rect(self, widget):
        return QRect(widget.mapToGlobal(QPoint(0, 0)), widget.size())

    def on_line_hover(self, href):
        if href:
            self.open_bubble(href, self.cursor_rect())
        else:
            self.bubble.leave()

    def on_label_hover(self, href, label):
        if href:
            self.open_bubble(href, self.widget_rect(label))
        else:
            self.bubble.leave()

    def open_bubble(self, href, trigger, pin=False):
        if self.record is None or ":" not in href:
            return
        kind, name = href.split(":", 1)
        if kind == "arg":
            widget, width = self.argument_widget(name), ARG_WIDTH
        elif kind == "val":
            widget, width = self.values_widget(name), VALUE_WIDTH
        else:
            return
        widget.setMinimumWidth(width - 60 if kind == "val" and self.last_bubble[1]["free"] is None else min(width, ARG_WIDTH) - 40)
        self.bubble.open(href, widget, trigger, width, pin=pin)

    def head_html(self, name, status):
        mono = self.app.mono_font.family()
        return (f'<span style="font-family:\'{mono}\'; font-weight:bold; background-color:{theme.colour("bg-sunk")};">&nbsp;{html.escape(name)}&nbsp;</span>'
                f'&nbsp;&nbsp;<span style="color:{theme.colour("muted")}; font-size:small;">{html.escape(status)}</span>')

    def argument_widget(self, name):
        data = page_model.argument_bubble(self.record, name, self.lang)
        widget = QWidget()
        column = QVBoxLayout(widget)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(4)
        head = QLabel(self.head_html(data["name"], data["status"]))
        head.setTextFormat(Qt.TextFormat.RichText)
        column.addWidget(head)
        column.addWidget(rich_label(data["text"], self.app.mono_font.family()))
        self.last_bubble = ("arg", data)
        return widget

    def values_widget(self, name):
        data = page_model.value_bubble(self.record, name, self.lang)
        mono = self.app.mono_font.family()
        widget = QWidget()
        column = QVBoxLayout(widget)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(6)
        head = QLabel(self.head_html(data["name"], data["status"]))
        head.setTextFormat(Qt.TextFormat.RichText)
        column.addWidget(head)
        self.last_bubble = ("val", data)
        if data["free"] is not None:
            free = data["free"]
            current = f'<span style="font-family:\'{mono}\';">{html.escape(str(free["default"]))}</span>' if free["default"] is not None else ""
            text = QLabel(f'{current}<br/>{html.escape(free["text"])} <span style="font-family:\'{mono}\';">{html.escape(free["example"])}</span>')
            text.setTextFormat(Qt.TextFormat.RichText)
            text.setWordWrap(True)
            column.addWidget(text)
            return widget
        body = QWidget()
        row = QHBoxLayout(body)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)
        listing = QWidget()
        listing.setMaximumWidth(320)
        items = QVBoxLayout(listing)
        items.setContentsMargins(0, 0, 0, 0)
        items.setSpacing(1)
        preview = QWidget()
        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(10, 0, 0, 0)
        rows = []

        def show(value):
            for r, v in rows:
                r.setStyleSheet(f"background:{theme.colour('accent-soft')}; border-radius:4px;" if v is value else "")
            while preview_layout.count():
                item = preview_layout.takeAt(0)
                if item.widget() is not None:
                    item.widget().deleteLater()
            self.fill_preview(preview_layout, value["preview"])
            self.shown_value = value["value"]
            if self.bubble.is_open():
                QTimer.singleShot(0, self.bubble.bubble.refit)

        for value in data["values"]:
            text = (f'<span style="font-family:\'{mono}\';">{html.escape(value["value"])}</span>&nbsp;&nbsp;'
                    f'<span style="color:{theme.colour("ink-soft")};">{rich(value["text"], mono)}</span>')
            label = ValueRow(text, lambda v=value: show(v))
            rows.append((label, value))
            items.addWidget(label)
        hint = muted(plain_label(data["hover"], wrap=True))
        items.addWidget(hint)
        items.addStretch(1)
        row.addWidget(listing)
        row.addWidget(preview, 1)
        column.addWidget(body)
        column.addWidget(muted(plain_label(data["foot"], wrap=True)))
        current = next((v for v in data["values"] if v["value"] == data["current"]), data["values"][0])
        show(current)
        return widget

    def fill_preview(self, layout, preview):
        """One value's call and its print (UI-007): the set-up lines in grey, the call, «Ce qu'il imprime», then the print cut out of its sheet -- or what is said in its place."""
        mono = self.app.mono_font
        if preview["state"] == "unrendered":
            if preview["note"]:
                layout.addWidget(muted(plain_label(preview["note"], wrap=True)))
            layout.addStretch(1)
            return
        if preview["setup"]:
            setup = muted(plain_label(preview["setup"], wrap=True))
            setup.setFont(mono)
            layout.addWidget(setup)
        call = plain_label(preview["call"], wrap=True)
        call.setFont(mono)
        call.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(call)
        label = muted(plain_label(self.word("prints")))
        label.setFont(self.app.bold_font)
        layout.addWidget(label)
        if preview["state"] == "missing":
            layout.addWidget(muted(plain_label(self.word("render_missing"), wrap=True)))
        elif preview["blank"]:
            layout.addWidget(muted(plain_label(self.word("blank"), wrap=True)))
        elif preview["rect"]:
            image = QLabel()
            image.setStyleSheet(f"background:{theme.colour('paper')}; border:1px solid {theme.colour('line')}; padding:4px;")
            image.setPixmap(self.cut(preview["file"], preview["rect"]))
            image.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            layout.addWidget(image)
            self.shown_print = (preview["file"], tuple(preview["rect"]))
        if preview["state"] == "stale":
            layout.addWidget(muted(plain_label(self.word("render_stale"), wrap=True)))
        if preview["note"]:
            layout.addWidget(muted(rich_label(preview["note"], mono.family())))
        layout.addStretch(1)

    def cut(self, file, rect):
        """A value's print, cut out of its sheet and drawn at the bubble's scale through the device pixel ratio (ARCH-009)."""
        if file not in self.sheets:
            self.sheets[file] = QPixmap(str(examples.VALUES / file))
        top, width, height = rect
        piece = self.sheets[file].copy(0, top, width, height)
        piece.setDevicePixelRatio(1 / examples.VALUE_SCALE)
        return piece

    # -- the examples --

    def flash_example(self, index):
        """The example chosen in the right-hand pane: scrolled to, and lit for a moment (UI-010)."""
        if not 0 <= index < len(self.boxes):
            return
        box = self.boxes[index]
        self.scroll.ensureWidgetVisible(box, 0, 40)
        box.setStyleSheet(f"ExampleBox {{ background:{theme.colour('wood-soft')}; }}")
        box.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        QTimer.singleShot(FLASH_MS, lambda: box.setStyleSheet("") if box is not None else None)
        self.flashed = index
