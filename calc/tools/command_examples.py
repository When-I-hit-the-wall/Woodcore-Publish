"""The worked examples of a command's page: their code, their levels and the page each prints (spec 2026-10-24-onglet-commandes-pages, UI-009, REQ-008, ARCH-007; docs/typst/command-docs.md §10sexies).

Moved out of commands_tab.py with the condensed pages, unchanged in what they do since v0.94. **A German window shows the committed pages** (examples/out, build_examples.py), a load and not a run of Typst. **A French or English one shows the page a report of its language prints**, compiled on demand by command_preview.render_localised -- the very document the website compiles its pages from -- in a thread of its own, «Compilation…» standing where the page will be, and kept in the cache (%LOCALAPPDATA%\\Woodcore\\examples), so the second look is a load. Where Typst is absent or the compile fails, the German page is shown with one line saying why.

**The levels** (REQ-008): the 1 · 2 · 3 buttons where command_docs.example_levels gives three; one page and «Les trois niveaux impriment la même page.» where build_examples measured the three alike, the buttons and the note where two are (command_page.shown_levels, levels_note).

The renderer owns the queue and its timer; the page that holds it stops it when it is hidden (ARCH-007).
"""

import threading

import build_examples as examples
import command_docs as docs
import command_page as page_model
import command_preview as preview
import richtext
from PySide6.QtCore import QObject, Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QLabel, QPlainTextEdit, QToolButton, QVBoxLayout, QWidget
from shiboken6 import isValid

POLL_MS = 60   # how often the window looks whether the example compiling in its thread is done


def plain_label(text, wrap=False):
    """A label showing `text` exactly as it is -- given a text that looks like HTML, QLabel would render it as HTML."""
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(wrap)
    return label


def muted(label):
    """The site's secondary text: the theme's grey (QLabel#meta in theme.py), never a colour written here."""
    label.setObjectName("meta")
    return label


def pinned_level(code):
    """The level the rule beside an example names: the last one its calls write that prints something. A `level: 0` declares a variable and prints nothing (docs/typst/formulas.md §10quinquies), so «fixed at 0» would name the wrong line; command_preview.FIXES_LEVEL reads no 0 (v0.94)."""
    printed = preview.FIXES_LEVEL.findall(code)
    return printed[-1] if printed else None


def first_line(text):
    """The first line that says something -- «error: unknown variable: foo» of a Typst message."""
    for line in (text or "").splitlines():
        if line.strip():
            return line.strip()
    return ""


class PreviewLabel(QLabel):
    """The page one example compiles to, drawn at whatever width the panel gives it, through the device pixel ratio rather than resampled."""

    def __init__(self):
        super().__init__()
        self._image = None
        self.path = None   # the file shown, which says where the page came from: examples/out or the cache
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

    def set_image(self, image, path=None):
        self._image = image if image is not None and not image.isNull() else None
        self.path = path if self._image is not None else None
        self.apply()

    def forget(self):
        self._image, self.path = None, None
        self.clear()

    def apply(self):
        if self._image is None:
            return
        natural = self._image.width() * 96 / preview.PPI  # what 16 cm is at 100 %
        width = min(natural, max(self.width(), 80))
        scale = self._image.width() / width
        pixmap = QPixmap.fromImage(self._image)
        pixmap.setDevicePixelRatio(scale)
        self.setPixmap(pixmap)
        self.setFixedHeight(round(self._image.height() / scale))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.apply()


class CodeBlock(QPlainTextEdit):
    """An example's code as the site sets it: on the code ground (QPlainTextEdit#code in theme.py), selectable, its lines kept, exactly as tall as its lines."""

    def __init__(self, code, font):
        super().__init__(code)
        self.setObjectName("code")
        self.setReadOnly(True)
        self.setFont(font)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.lines = max(len(code.splitlines()), 1)
        self.fit()

    def fit(self):
        bar = self.horizontalScrollBar()
        extra = bar.sizeHint().height() if bar.maximum() > 0 else 0
        margins = self.contentsMargins()
        height = self.lines * self.fontMetrics().lineSpacing() + 2 * self.document().documentMargin() + margins.top() + margins.bottom() + 6 + extra
        if self.height() != round(height):
            self.setFixedHeight(round(height))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit()


class RenderJob:
    """One example compiled off the window's thread: in the window's language by command_preview.render_localised, or -- for a German page missing or stale among the committed ones -- in German by render_blocking. The thread touches no widget: it fills `png` and `error` and sets `finished`."""

    def __init__(self, box, lang, localised, note=None, fallback=None):
        self.box, self.code, self.level, self.lang = box, box.code, box.level, lang
        self.localised = localised
        self.note = note
        self.fallback = fallback
        self.png = self.error = None
        self.finished = threading.Event()

    def key(self, token):
        return preview.cache_key(self.code, self.level, self.lang, token, document_language=self.localised)

    def run(self):
        try:
            render = preview.render_localised if self.localised else preview.render_blocking
            self.png, self.error = render(self.code, self.level, self.lang)
        except Exception as exc:  # broad: a thread's exception would otherwise be lost, and the box left saying «Compilation…» for ever
            self.png, self.error = None, f"{type(exc).__name__}: {exc}"
        self.finished.set()


class ExampleRenderer(QObject):
    """The pages of the examples shown: a committed file where there is one to show, else a compile in a thread of its own, one at a time, in the order they stand on the page."""

    def __init__(self, t, lang, parent=None):
        super().__init__(parent)
        self.t, self.lang = t, lang
        self.manifest = examples.index()   # the committed pages, read once
        self.queue = []
        self.job = None
        self.token = None
        self.timer = QTimer(self)
        self.timer.setInterval(POLL_MS)
        self.timer.timeout.connect(self.poll)

    def new_page(self):
        """A page is shown: the waiting renders go with the page that asked for them; the one compiling finishes into the cache."""
        self.queue = []
        self.token = preview.generation()

    def stop(self):
        """The page is hidden: nothing more is started (ARCH-007)."""
        self.queue = []
        self.timer.stop()

    def page_for(self, box):
        """The committed German page for one example, and whether it can be trusted (build_examples.page)."""
        return examples.page(box.command, box.index, box.level, box.code, self.manifest)

    def show_page(self, box):
        """Puts one example's page in its box -- at once where there is a file to show, else through a compile in a thread of its own."""
        german, state = self.page_for(box)
        if self.lang == examples.LANG:
            if state == "fresh":
                box.show_png(german)
                return
            job = RenderJob(box, self.lang, localised=False, note=self.t("ref_stale" if state == "stale" else "ref_missing"), fallback=german)
        else:
            job = RenderJob(box, self.lang, localised=True, fallback=german)
        hit = preview.cached_png(job.key(self.token or preview.generation()))
        if hit is not None:
            box.show_png(hit, note=job.note)
            return
        if not preview.have_typst():
            self.settle(job)
            return
        box.show_note(" ".join(part for part in (job.note, self.t("ref_rendering")) if part))
        self.queue = [waiting for waiting in self.queue if waiting.box is not box]
        self.queue.append(job)
        self.pump()

    def pump(self):
        if self.job is not None or not self.queue:
            return
        self.job = self.queue.pop(0)
        threading.Thread(target=self.job.run, name="example-render", daemon=True).start()
        self.timer.start()

    def poll(self):
        job = self.job
        if job is None:
            self.timer.stop()
            return
        if not job.finished.is_set():
            return
        self.job = None
        self.settle(job)
        if not self.queue:
            self.timer.stop()
        self.pump()

    def settle(self, job):
        """Puts a compiled page where it belongs -- or, where there is none, the German page with one line saying why, or the error."""
        box = job.box
        if not isValid(box) or box.level != job.level:
            return
        if job.png is not None:
            box.show_png(job.png, note=job.note)
            return
        reason = first_line(job.error) or self.t("ref_no_typst")
        if job.fallback is not None and job.localised:
            box.show_png(job.fallback, note=self.t("ref_german_page", reason=reason))
        elif job.fallback is not None:
            box.show_png(job.fallback, note=f"{job.note} {reason}")
        else:
            box.show_error(job.error or self.t("ref_no_typst"))


class ExampleBox(QWidget):
    """One example of one command, as the site sets it: «Exemple n», its code, its levels -- the buttons, or the note that says its levels print alike --, and the page it prints. `host` gives the words, the fonts, the copy button, the levels remembered and the renderer."""

    def __init__(self, host, record, index, example):
        super().__init__()
        self.host = host
        self.command = record["name"]
        self.index = index
        self.code = example["code"]
        self.renderable = example["render"]
        all_levels = docs.example_levels(record, record["english"], example)
        self.levels = page_model.shown_levels(self.command, index, all_levels, host.renderer.manifest)
        self.levels_note = page_model.levels_note(self.command, index, host.lang, host.renderer.manifest) if len(all_levels) > 1 else None
        remembered = host.level_of(self.command, index)
        if remembered in self.levels:
            self.level = remembered
        elif preview.DEFAULT_LEVEL in self.levels or not self.levels:
            self.level = preview.DEFAULT_LEVEL
        else:
            self.level = self.levels[0]
        self.group = None
        self.fixed_note = None
        self.note_label = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 6)
        layout.setSpacing(5)
        self.heading = plain_label(host.word("example", n=index + 1))
        self.heading.setFont(host.app.bold_font)
        layout.addWidget(self.heading)

        source = CodeBlock(self.code, host.app.mono_font)
        self.highlighter = richtext.TypstHighlighter(source.document())
        self.source = source
        row = QHBoxLayout()
        row.addWidget(source, 1)
        row.addWidget(host.copy_button(self.code), 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(row)

        if len(self.levels) > 1:
            levels = QHBoxLayout()
            levels.setSpacing(0)
            levels.addWidget(muted(plain_label(host.word("level") + (" : " if host.lang == "fr" else ": "))))
            self.group = QButtonGroup(self)
            for position, value in enumerate(self.levels):
                button = QToolButton()
                button.setText(str(value))
                button.setCheckable(True)
                button.setProperty("segment", "first" if position == 0 else "last" if position == len(self.levels) - 1 else "middle")
                button.setChecked(value == self.level)
                self.group.addButton(button, value)
                levels.addWidget(button)
            self.group.idClicked.connect(self.on_level)
            levels.addSpacing(10)
            if self.levels_note:
                self.note_label = muted(plain_label(self.levels_note))
                levels.addWidget(self.note_label)
            levels.addStretch(1)
            layout.addLayout(levels)
        elif self.levels_note:
            self.note_label = muted(plain_label(self.levels_note, wrap=True))
            layout.addWidget(self.note_label)
        elif self.renderable and docs.takes_level(record, record["english"]):
            fixed = pinned_level(self.code)
            if fixed is not None:
                self.fixed_note = muted(plain_label(f"{host.word('level')}{' : ' if host.lang == 'fr' else ': '}{host.t('ref_level_fixed', level=fixed)}", wrap=True))
                layout.addWidget(self.fixed_note)

        self.status = muted(plain_label("", wrap=True))
        self.status.hide()
        layout.addWidget(self.status)
        self.error = QPlainTextEdit()
        self.error.setReadOnly(True)
        self.error.setFont(host.app.mono_font)
        self.error.hide()
        layout.addWidget(self.error)
        self.preview = PreviewLabel()
        layout.addWidget(self.preview)
        self.start()

    def on_level(self, level):
        if level == self.level:
            return
        self.level = level
        self.host.remember_level(self.command, self.index, level)
        self.start()

    def start(self):
        if not self.renderable:
            self.show_note(self.host.word("not_rendered"))
            return
        self.host.renderer.show_page(self)

    def show_note(self, text):
        self.status.setText(text)
        self.status.show()
        self.error.hide()
        self.preview.forget()

    def show_error(self, text):
        self.status.hide()
        lines = text.strip().splitlines()[-14:]
        self.error.setPlainText(self.host.t("ref_render_failed") + "\n" + "\n".join(lines))
        self.error.setFixedHeight(18 + 16 * (len(lines) + 1))
        self.error.show()
        self.preview.forget()
        self.preview.setFixedHeight(0)

    def show_png(self, path, note=None):
        self.error.hide()
        if note:
            self.status.setText(note)
            self.status.show()
        else:
            self.status.hide()
        self.preview.set_image(QImage(str(path)), path)
