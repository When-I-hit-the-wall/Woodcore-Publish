"""The right-hand pane of the commands tab: the lines to copy, the list of the examples, and the calls of the command in the project that is open (spec 2026-10-24-onglet-commandes-pages, UI-010, D-7, ARCH-007, ARCH-RISK-009).

The two lines to copy are command_docs.calls' -- the minimal call and the complete one, the website's too --, each with «Copier». The examples are listed by their first line; a click emits `example_chosen(index)`, which the tab hands to the page (it scrolls there and flashes the example). «Dans ce projet» lists the calls of the command in the open project, read-only, twelve at most and the number of the others (command_usage). No module of state: the commands are fixed (D-2).
"""

import command_docs as docs
import richtext
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget


def _label(text, meta=False, wrap=True, mono=None):
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(wrap)
    if meta:
        label.setObjectName("meta")
    if mono is not None:
        label.setFont(mono)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return label


class CommandSide(QScrollArea):
    """The three modules of the right-hand pane, filled by `set_command(record)`."""

    example_chosen = Signal(int)

    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.calls_shown = []      # the (word, call) offered, in order
        self.example_buttons = []
        self.usage_rows = []
        self.set_command(None)

    def shown(self):
        pass

    def hidden(self):
        pass

    def state(self):
        return {}

    def restore(self, _state):
        pass

    def _module(self, layout, title, count=None):
        box = QFrame()
        box.setObjectName("card")
        box.setFrameShape(QFrame.Shape.StyledPanel)
        column = QVBoxLayout(box)
        column.setContentsMargins(10, 8, 10, 10)
        column.setSpacing(4)
        head = _label(title + (f"  {count}" if count is not None else ""), wrap=False)
        head.setFont(self.ctx.app.bold_font)
        column.addWidget(head)
        layout.addWidget(box)
        return column

    def set_command(self, record):
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(4, 0, 4, 4)
        layout.setSpacing(8)
        self.calls_shown, self.example_buttons, self.usage_rows = [], [], []
        if record is not None and record.get("category") != "internal":
            column = self._module(layout, self.ctx.word("lines_to_copy"))
            for key, call in docs.calls(record, self.ctx.samples):
                self.calls_shown.append((key, call))
                column.addWidget(_label(self.ctx.word("copy_minimal" if key == "call_minimal" else "copy_complete"), meta=True))
                row = QHBoxLayout()
                row.addWidget(richtext.CodeField(" ".join(part.strip() for part in call.splitlines()), self.ctx.app.mono_font), 1)
                row.addWidget(richtext.copy_button(self.ctx.t("copy"), self.ctx.t("copied_short"), lambda c=call: self.ctx.app.copy(c)))
                column.addLayout(row)
            if record.get("examples"):
                column = self._module(layout, self.ctx.word("examples"))
                for index, example in enumerate(record["examples"]):
                    first = example["code"].strip().splitlines()[0] if example["code"].strip() else ""
                    button = QPushButton(f"{index + 1}   {first}")
                    button.setFlat(True)
                    button.setStyleSheet("text-align: left;")
                    button.setFont(self.ctx.app.mono_font)
                    button.setToolTip(example["code"])
                    button.clicked.connect(lambda _checked=False, i=index: self.example_chosen.emit(i))
                    self.example_buttons.append(button)
                    column.addWidget(button)
            hits, total = self.ctx.usage.calls(record["name"])
            column = self._module(layout, self.ctx.word("in_project"), total)
            if not hits:
                column.addWidget(_label(self.ctx.word("in_project_none"), meta=True))
            for file, line, text in hits:
                place = _label(f"{file}:{line}", meta=True, wrap=False)
                code = _label(text, wrap=False, mono=self.ctx.app.mono_font)
                code.setToolTip(text)
                column.addWidget(place)
                column.addWidget(code)
                self.usage_rows.append((file, line, text))
            if total > len(hits):
                column.addWidget(_label(self.ctx.word("in_project_more", n=total - len(hits)), meta=True))
        layout.addStretch(1)
        self.setWidget(body)
