"""The compiled page of a document, beside what it is written from: the centre pane of the «Structure document» tab and the preview of the «Sections» tab (the engineer's request of 30.09.2026, phase 2 of the three documents).

A `PdfPane` shows one document's PDF, every page one under the other and fitted to its width, and compiles that document again in the background when it is asked to -- at every save, which is the tab's to say (`request`). It holds no knowledge of a document's structure: it gives the PDF's own outline as a flat list (`bookmarks`), and scrolls to a page and a height on it when told to (`jump`) -- which heading is which section is calc/structure.py's to work out.

**The PDF is read into memory and never opened as a file.** `QPdfDocument.load(path)` keeps a Windows handle on the file for as long as the document is open, and the next compile, which writes that same file, then fails on Windows' own sharing error -- the handle the plan tab's renderer keeps is why `conftest.project_copy` copies no plan background. Here the bytes are read in one call and handed to the document through a `QBuffer`, which PDFium reads from for as long as the document is open: the file itself is closed the moment it is read, and a compile, NextCloud or the engineer may replace it at any time.

**A preview is compiled beside the deliverable and never over it**: into Woodcore's cache (`usersettings.cache_dir("preview")`, `<project key>-<document>.pdf`), outside the project that NextCloud syncs, with `documents.compile_args` -- the one spelling of a document's command line -- and `stamps.deps_file(..., preview=True)`, and stamped with `stamps.record(..., preview=True)`, so a preview never says anything of the PDF the export writes, nor the export of the preview.

**One compile at a time, and only the latest request.** A request waits `DEBOUNCE_MS` for the next (three saves in a row are one compile); one made while a compile runs waits for it to end, and a later one replaces it -- nobody wants to see the page of a save that was saved over. What a compile read is stamped off the main thread (`stamps.record` hashes every input: a quarter of a second), and so is the question whether what is shown is current (`stamps.changed`, a fifth of one), so the pane never holds the window while a section is typed.

**What it says**, in the window's language (STRINGS, keys `pp_`): «Modifications non compilées» where what is shown is not what the document's sources would give now (`stamps.changed(here, mode, [], ignore_flags=True, preview=True)`), a thin busy bar while Typst runs, and where a compile fails, Typst's own message in a banner -- never a modal: a section half typed does not compile, and a window that stopped the engineer at every save for it would be unusable. What was shown before stays shown. The banners are the style sheet's callouts (`callout` warning and danger): no colour is written here.

Until a preview has been compiled, the document's own PDF is shown where there is one, and the banner then says whether *that* PDF is current (its own stamp, `preview=False`): what is on screen is what the banner is about.

**A pane of snippets only never shows the document** (`snippets_only`, issue #21, v0.117): the «Affichage» view of a tab (display_view.DisplayView) and the plans' command builder show nothing but the snippet asked for, and the document's own PDF -- whose first page is the report's title page -- loaded while the first snippet compiled was the «Statischer Bericht» seen for half a second at every entry into «Affichage». Such a pane shows the placeholder until its first snippet is compiled, keeps the last snippet when the tab leaves the view, and asks no question of staleness: the Structure tab's pane, which shows the document, is built without the flag.

**A snippet is a page of its own, compiled from standard input** (`request_snippet`, the engineer's rework of 01.10.2026): the «Structure du document» tab shows the node chosen -- a chapter, a section, one object -- and not the document, so what it asks for is a small Typst source (calc/structure_preview.py) compiled against the project's folder as the Typst root, into the cache beside the previews (`snippet_file`) and shown in the same view. It runs through the one process this pane has, so **one compile at a time and only the latest request**: a snippet asked for while the document's compile runs ends that compile (the document is asked for again when the engineer chooses nothing), one asked for while a snippet runs waits for it, and a later one takes its place; `show_document()` brings the document's own page back and drops a snippet still on its way. A snippet says nothing of staleness -- it is compiled from the sources as they are at the moment it is asked for -- and writes no stamp: a failing one says Typst's own message in the banner, as the document's does, and leaves the page shown. A snippet is compiled **in a moment** (`SNIPPET_DEBOUNCE_MS`), the document in a longer one.
"""

import hashlib
from collections import namedtuple
from pathlib import Path

import shiboken6

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QModelIndex, QPointF, QProcess, QThread, QTimer, Qt, Signal
from PySide6.QtPdf import QPdfBookmarkModel, QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QProgressBar, QStackedLayout, QVBoxLayout, QWidget

import documents
import proc
import project
import stamps
import usersettings
import tasks  # what runs in the background, said by the chip at the top right (tasks.activity, v0.117)

# How long a request waits for the next before the compile starts: three saves in a row are one compile.
DEBOUNCE_MS = 800
# The same for a snippet, which compiles in half a second and is asked for at every click of the tree.
SNIPPET_DEBOUNCE_MS = 250
# A preview still compiling after this long is stopped: Typst caught in a loop must not leave the pane busy for ever.
COMPILE_TIMEOUT_MS = 5 * 60 * 1000
# The folder of Woodcore's caches the previews are compiled into (usersettings.cache_dir).
PREVIEW_CACHE = "preview"
# How many lines of Typst's message the failure banner shows: its first, where Typst says what is wrong and where.
MESSAGE_LINES = 20

# One entry of a PDF's outline: the heading's level as Typst counts it (1 for a top-level heading), its title, the page it is on (0 for the first) and how far down that page it stands, in points from the page's top edge -- what `jump` takes.
Bookmark = namedtuple("Bookmark", "level title page y")

STRINGS = {
    "fr": {
        "pp_stale": "Modifications non compilées",
        "pp_compiling": "Compilation de l'aperçu…",
        "pp_failed": "La compilation de l'aperçu a échoué :",
        "pp_more": "… et {n} lignes de plus",
        "pp_timeout": "Arrêtée après {minutes} min sans réponse de Typst.",
        "pp_empty": "Pas encore d'aperçu",
    },
    "de": {
        "pp_stale": "Nicht kompilierte Änderungen",
        "pp_compiling": "Vorschau wird kompiliert…",
        "pp_failed": "Die Kompilierung der Vorschau ist fehlgeschlagen:",
        "pp_more": "… und {n} weitere Zeilen",
        "pp_timeout": "Nach {minutes} min ohne Antwort von Typst abgebrochen.",
        "pp_empty": "Noch keine Vorschau",
    },
    "en": {
        "pp_stale": "Uncompiled changes",
        "pp_compiling": "Compiling the preview…",
        "pp_failed": "The preview failed to compile:",
        "pp_more": "… and {n} more lines",
        "pp_timeout": "Stopped after {minutes} min without an answer from Typst.",
        "pp_empty": "No preview yet",
    },
}


def text(key, lang, **values):
    """One of STRINGS in `lang` -- English where the window's language is none of the three -- its holes filled."""
    table = STRINGS[lang if lang in STRINGS else "en"]
    return table[key].format(**values) if values else table[key]


def project_key(here):
    """What one project's previews are named after in the cache: its project file's own path, hashed -- the rule calc/variables.py names its cached readings by, so two projects never share one and a project moved is simply compiled again."""
    return hashlib.sha256(str(Path(here.file).resolve()).encode("utf-8")).hexdigest()[:16]


def snippet_file(here, mode, folder=None):
    """Where document `mode`'s snippet is compiled to: `<cache>/preview/<project key>-<mode>-snippet.pdf` -- one page per document, written over at every compile. Not made, nor its folder."""
    folder = Path(folder) if folder is not None else usersettings.cache_dir(PREVIEW_CACHE)
    return folder / f"{project_key(here)}-{mode}-snippet.pdf"


def preview_file(here, mode, folder=None):
    """Where document `mode`'s preview is compiled to: `<cache>/preview/<project key>-<mode>.pdf`, or in `folder` where one is named (a test's). Not made, nor its folder."""
    folder = Path(folder) if folder is not None else usersettings.cache_dir(PREVIEW_CACHE)
    return folder / f"{project_key(here)}-{mode}.pdf"


def read_bookmarks(document):
    """The outline of a loaded `QPdfDocument`, flattened in document order, as [Bookmark] -- what `PdfPane.bookmarks` gives."""
    model = QPdfBookmarkModel()
    model.setDocument(document)
    found = []

    def walk(parent):
        for row in range(model.rowCount(parent)):
            index = model.index(row, 0, parent)
            location = model.data(index, QPdfBookmarkModel.Role.Location)
            found.append(Bookmark(
                level=int(model.data(index, QPdfBookmarkModel.Role.Level) or 0) + 1,
                title=str(model.data(index, QPdfBookmarkModel.Role.Title) or ""),
                page=int(model.data(index, QPdfBookmarkModel.Role.Page) or 0),
                y=float(location.y()) if isinstance(location, QPointF) else 0.0,
            ))
            walk(index)

    walk(QModelIndex())
    return found


class _Job(QThread):
    """One call of calc/stamps.py off the main thread: `done` carries what it returned, or the exception it raised. Unparented and held in _RUNNING until it has finished, so a pane deleted meanwhile never destroys a thread that still runs -- its answer is then simply delivered to nobody."""

    done = Signal(object, object)   # the result, the exception

    def __init__(self, work):
        super().__init__()
        self.work = work

    def run(self):
        try:
            result = self.work()
        except Exception as exc:        # broad: an answer, whatever happens -- handed to the pane, which says it; never leave it waiting for ever
            self.done.emit(None, exc)
        else:
            self.done.emit(result, None)


_RUNNING = set()


def _start_job(work, pane, receiver):
    """`work` run off the main thread, and `receiver(result, exception)` called on the main thread with what it gave -- unless `pane` has been deleted meanwhile, which a slot that is not one of its own methods is never told of."""
    job = _Job(work)
    _RUNNING.add(job)
    job.done.connect(lambda result, error: receiver(result, error) if shiboken6.isValid(pane) else None)
    job.finished.connect(lambda: (_RUNNING.discard(job), job.deleteLater()))
    job.start()
    return job


def _same(a, b):
    """Whether two (project, document) pairs name one document: the same project file, the same mode."""
    if a is None or b is None or a[0] is None or b[0] is None:
        return False
    return Path(a[0].file) == Path(b[0].file) and a[1] == b[1]


class PdfPane(QWidget):
    """One document's compiled PDF, every page one under the other fitted to the pane's width, compiled again in the background on request.

    `set_document(here, mode)` names the document shown -- its preview, or its own PDF until a preview has been compiled; `request()` asks for a compile of it; `bookmarks()` and `jump()` let a tab tie its sections to the pages. `stop()` ends what runs, which the window's quitting does by itself.
    """

    compiled = Signal(str)          # a document whose preview was compiled and is shown
    failed = Signal(str, str)       # a document, and Typst's own message
    started = Signal(str)           # a document whose compile has started
    loaded = Signal(int)            # a PDF shown: its page count -- the outline may have changed with it
    staleChanged = Signal(bool)     # whether what is shown is not what the document's sources would give now
    busyChanged = Signal(bool)      # whether Typst runs, or its record is being written
    snippetCompiled = Signal(str)   # a snippet that was compiled and is shown: its key

    def __init__(self, parent=None, lang="en", snippets_only=False):
        super().__init__(parent)
        self.lang = lang
        self.snippets_only = snippets_only   # a pane that shows snippets and never the document's own PDF (issue #21)
        self.here = None                # the document shown: its project...
        self.mode = None                # ...and which of its documents
        self.showing = False            # whether a PDF is on screen
        self.shown = None               # its path, None where it came as bytes (load_bytes)
        self.shown_preview = False      # whether that PDF is the document's preview, or its own
        self.preview_folder = None      # where previews are compiled to: Woodcore's cache unless a test names another
        self.stale = None               # what the last check said: True, False, or None before any
        self.stale_reason = None        # the engine.Note of that check (its `code` says why)
        self.last_error = None          # Typst's message of the last compile that failed, until one succeeds
        self.wanted = None              # the latest request not yet started: (project, mode)
        self.process = None             # the compile that runs
        self.running = None             # what it compiles: (project, mode, target, deps)
        self.recording = None           # the record of a compile being written, which the next compile waits for
        self.timed_out = False
        self.snippet_wanted = None      # the latest snippet request not yet started: (project, mode, source, key)
        self.snippet_running = None     # the snippet being compiled: (project, mode, target, key, epoch)
        self.shown_snippet = None       # the key of the snippet on screen, None where the page is the document's
        self.killed = False             # the compile that runs was ended on purpose, for a snippet: it is not a failure
        self._snippet_epoch = 0         # moved on whenever what a snippet on its way would show is no longer wanted
        self._check_generation = 0      # only the latest check of staleness is believed
        self._epoch = 0                 # moved on by stop(): what a thread answers about a compile before it is dropped
        self._buffer = None

        self.document = QPdfDocument(self)
        self.view = QPdfView(self)
        self.view.setPageMode(QPdfView.PageMode.MultiPage)
        self.view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        # the vertical bar is always there: fitted to the width, a page just taller than the pane brings the bar, which narrows the view, which shrinks the page to fit again, which takes the bar away -- and the page, rendered at each width in turn, showed blank
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.view.setDocument(self.document)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(DEBOUNCE_MS)
        self.timer.timeout.connect(self._start_wanted)
        self.snippet_timer = QTimer(self)
        self.snippet_timer.setSingleShot(True)
        self.snippet_timer.setInterval(SNIPPET_DEBOUNCE_MS)
        self.snippet_timer.timeout.connect(self._start_wanted)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.stale_banner = QLabel(self)
        self.stale_banner.setProperty("callout", "warning")
        self.stale_banner.setWordWrap(True)
        self.stale_banner.setHidden(True)
        layout.addWidget(self.stale_banner)

        self.error_banner = QLabel(self)
        self.error_banner.setProperty("callout", "danger")
        self.error_banner.setTextFormat(Qt.TextFormat.PlainText)   # Typst's message is text, and may carry a «<» of its own
        self.error_banner.setWordWrap(True)
        self.error_banner.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.error_banner.setHidden(True)
        try:
            import theme
            self.error_banner.setFont(theme.mono_font(self.font().pointSizeF()))
        except (ImportError, OSError, ValueError):   # theme.json unreadable
            pass    # the message in the text's own font: less legible, never wrong
        layout.addWidget(self.error_banner)

        self.busy_row = QWidget(self)
        busy = QHBoxLayout(self.busy_row)
        busy.setContentsMargins(0, 0, 0, 0)
        self.busy_bar = QProgressBar(self.busy_row)
        self.busy_bar.setRange(0, 0)     # no end known: the bar runs
        self.busy_bar.setTextVisible(False)
        self.busy_bar.setFixedSize(64, 6)
        self.busy_label = QLabel(self.busy_row)
        self.busy_label.setObjectName("meta")
        busy.addWidget(self.busy_bar)
        busy.addWidget(self.busy_label)
        busy.addStretch(1)
        self.busy_row.setHidden(True)
        layout.addWidget(self.busy_row)

        self.stack = QStackedLayout()
        self.placeholder = QLabel(self)
        self.placeholder.setObjectName("meta")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stack.addWidget(self.placeholder)
        self.stack.addWidget(self.view)
        layout.addLayout(self.stack, 1)

        self.set_language(lang)
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.stop)

    # --- the words ---------------------------------------------------------------------

    def t(self, key, **values):
        return text(key, self.lang, **values)

    def set_language(self, lang):
        """The pane's words in `lang` -- the window's language switched."""
        self.lang = lang
        self.stale_banner.setText(self.t("pp_stale"))
        self.busy_label.setText(self.t("pp_compiling"))
        self.placeholder.setText(self.t("pp_empty"))
        self._show_error()

    # --- what is shown -------------------------------------------------------------------

    def set_document(self, here, mode):
        """Shows document `mode` of project `here`: its preview where one has been compiled, else the document's own PDF, else nothing yet -- and asks whether it is current. A document the project does not have is a ProjectError, as everywhere else."""
        here.document_typ(mode)
        if _same((here, mode), (self.here, self.mode)):
            return
        self.here, self.mode = here, mode
        self.last_error = None
        self._show_error()
        self.snippet_wanted = None
        self._snippet_epoch += 1
        self._show_own(here, mode)

    def _show_own(self, here, mode):
        """The document's preview shown where one has been compiled, else its own PDF, else nothing -- and the question whether it is current asked. A pane of snippets only shows the placeholder -- another document's snippet is not this one's, and the document's own PDF is never shown (issue #21)."""
        if self.snippets_only:
            self.clear()
            return
        self.shown_snippet = None
        preview = preview_file(here, mode, self.preview_folder)
        own = here.document_pdf(mode)
        if preview.is_file() and self.load(preview):
            self.shown_preview = True
        elif own.is_file() and self.load(own):
            self.shown_preview = False
        else:
            self.clear()
        self.check_stale()

    def show_document(self):
        """Back to the document: a snippet on screen, or on its way, is given up, and the document's preview -- or its own PDF -- is shown in its place. What the tab calls when the engineer chooses nothing."""
        self._snippet_epoch += 1
        self.snippet_wanted = None
        self.snippet_timer.stop()
        if self.here is not None and self.shown_snippet is not None and not self.snippets_only:
            self.last_error = None
            self._show_error()
            self._show_own(self.here, self.mode)

    def load(self, path, keep_place=None):
        """Shows the PDF at `path`, read into memory at once, and gives back whether it could be read. Shown again -- the same file, or `keep_place` -- it keeps the place it was scrolled to, where the new PDF still has that page; a PDF that lost pages goes to its last. A file that is not a PDF leaves the pane empty."""
        path = Path(path)
        try:
            data = path.read_bytes()
        except OSError:
            self.clear()
            return False
        if keep_place is None:
            keep_place = self.shown is not None and Path(self.shown) == path
        return self._load_bytes(data, path, keep_place=keep_place and self.showing)

    def load_bytes(self, data):
        """Shows the PDF `data` holds, as `load` would a file."""
        return self._load_bytes(bytes(data), None, keep_place=False)

    def _load_bytes(self, data, path, keep_place):
        navigator = self.view.pageNavigator()
        page, value = navigator.currentPage(), self.view.verticalScrollBar().value()
        buffer = QBuffer(self)
        buffer.setData(QByteArray(data))
        buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        self.document.load(buffer)      # closes the document it replaces, then reads from the new buffer for as long as it is open
        old, self._buffer = self._buffer, buffer
        if old is not None:
            old.close()
            old.deleteLater()
        if self.document.status() != QPdfDocument.Status.Ready or self.document.pageCount() == 0:
            self.clear()
            return False
        self.showing, self.shown = True, path
        self.stack.setCurrentWidget(self.view)
        count = self.document.pageCount()
        if keep_place:
            if page < count:
                self.view.verticalScrollBar().setValue(value)
            else:
                self.jump(count - 1)
        else:
            self.view.verticalScrollBar().setValue(0)
        self.loaded.emit(count)
        return True

    def clear(self):
        """Nothing shown: the placeholder in place of the pages."""
        self.document.close()
        if self._buffer is not None:
            self._buffer.close()
            self._buffer.deleteLater()
            self._buffer = None
        self.showing, self.shown = False, None
        self.shown_preview = False
        self.shown_snippet = None
        self.stack.setCurrentWidget(self.placeholder)
        self._show_stale()

    def page_count(self):
        return self.document.pageCount() if self.showing else 0

    def current_page(self):
        """The page at the top of the view, 0 for the first."""
        return self.view.pageNavigator().currentPage()

    def bookmarks(self):
        """The shown PDF's outline -- Typst writes one entry per heading it outlines -- flattened in document order, as [Bookmark(level, title, page, y)]: the level as Typst counts a heading's (1 at the top), the page from 0, and y in points from that page's top edge, which is what `jump` takes. Empty where nothing is shown."""
        return read_bookmarks(self.document) if self.showing else []

    def jump(self, page, y=0):
        """Scrolls the view to `page` (from 0, held to the pages there are), `y` points down it."""
        count = self.page_count()
        if count == 0:
            return
        page = max(0, min(int(page), count - 1))
        self.view.pageNavigator().jump(page, QPointF(0, float(y)), 0)

    # --- whether what is shown is current ------------------------------------------------

    def check_stale(self):
        """Asks, off the main thread, whether what is shown is what the document's sources would give now -- the preview's stamp, or the document's own where its own PDF is shown; the banner follows when the answer comes back (`staleChanged`). Nothing is compiled to find out."""
        if self.here is None or self.shown_snippet is not None:
            return      # a snippet is compiled from the sources as they are: it is never out of date
        self._check_generation += 1
        generation, here, mode, preview = self._check_generation, self.here, self.mode, self.shown_preview or not self.showing
        _start_job(lambda: stamps.changed(here, mode, [], ignore_flags=True, preview=preview), self,
                   lambda result, error: self._checked(generation, (here, mode), result, error))

    def _checked(self, generation, document, result, error):
        if generation != self._check_generation or not _same(document, (self.here, self.mode)):
            return      # a later check was asked for, or another document is shown: this answer is about what is gone
        stale, why = (True, None) if error is not None or result is None else result
        before, self.stale, self.stale_reason = self.stale, bool(stale), why
        self._show_stale()
        if before != self.stale:
            self.staleChanged.emit(self.stale)

    def _show_stale(self):
        """The banner says the page is not current only where a page is shown: without one, the placeholder says it."""
        self.stale_banner.setHidden(not (self.stale and self.showing and self.shown_snippet is None))

    def _show_error(self):
        if not self.last_error:
            self.error_banner.setHidden(True)
            return
        lines = self.last_error.splitlines()
        shown = lines[:MESSAGE_LINES]
        if len(lines) > MESSAGE_LINES:
            shown.append(self.t("pp_more", n=len(lines) - MESSAGE_LINES))
        self.error_banner.setText(self.t("pp_failed") + "\n" + "\n".join(shown))
        self.error_banner.setHidden(False)

    # --- compiling -------------------------------------------------------------------------

    def request(self, here=None, mode=None):
        """Asks for a compile of document `mode` of project `here` -- the one shown where neither is named, and shown from now on where another is --, `DEBOUNCE_MS` from now unless another request follows sooner. One made while a compile runs is started when it ends; a later one takes its place."""
        if here is None or mode is None:
            if self.here is None:
                raise ValueError("no document is shown, and none was named")
            here, mode = here or self.here, mode or self.mode
        self.set_document(here, mode)
        self.snippet_wanted = None
        self.snippet_timer.stop()
        self.wanted = (here, mode)
        self.timer.start()      # started again: the debounce counts from the last request
        self.check_stale()
        self._show_busy()

    def request_snippet(self, here, mode, source, key):
        """Asks for a snippet -- the Typst `source` of a part of document `mode`, named `key` -- compiled from standard input and shown in place of the page, `SNIPPET_DEBOUNCE_MS` from now unless another request follows sooner. A request for the document's own compile that was not started is forgotten, and a compile of the document that runs is ended: the snippet is what the engineer asked for last, and Typst runs once at a time."""
        self.set_document(here, mode)
        self._snippet_epoch += 1
        self.wanted = None
        self.timer.stop()
        self.snippet_wanted = (here, mode, source, key)
        self.snippet_timer.start()
        if self.process is not None and self.snippet_running is None and not self.killed:
            self.killed = True
            self.process.kill()
        self._show_busy()

    def compile_now(self):
        """Starts the compile requested at once, without waiting for the next request -- or as soon as the one running has ended."""
        self.timer.stop()
        self.snippet_timer.stop()
        self._start_wanted()

    def is_busy(self):
        """Whether Typst runs for this pane, or the record of what it compiled is being written."""
        return self.process is not None or self.recording is not None

    def is_pending(self):
        """Whether a compile is asked for and not finished: waiting for the next request, for the one that runs, or running."""
        return self.is_busy() or self.wanted is not None or self.snippet_wanted is not None

    def _start_wanted(self):
        if self.is_busy():
            return      # the one that runs starts it when it has ended
        if self.snippet_wanted is not None:
            self._start_snippet()
            return
        if self.wanted is None:
            return
        here, mode = self.wanted
        self.wanted = None
        target = preview_file(here, mode, self.preview_folder)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            deps = stamps.deps_file(here, mode, preview=True)
        except OSError as exc:
            self._failed(mode, str(exc))
            return
        arguments = documents.compile_args(here, mode, flags=[], target=target, deps=deps)
        process = proc.qprocess(self)
        process.setWorkingDirectory(str(here.typst_root))
        process.finished.connect(self._process_finished)
        process.errorOccurred.connect(self._process_error)
        timeout = QTimer(process)       # dies with the process, so it can never stop a later compile
        timeout.setSingleShot(True)
        timeout.timeout.connect(self._timeout)
        timeout.start(COMPILE_TIMEOUT_MS)
        self.process, self.running, self.timed_out = process, (here, mode, target, deps), False
        self._show_busy()
        self.busyChanged.emit(True)
        self.started.emit(mode)
        self._activity = tasks.activity().begin("activity_preview")   # said by the chip at the top right while Typst runs (REQ-007)
        process.start(project.typst_executable(), arguments)

    def _start_snippet(self):
        here, mode, source, key = self.snippet_wanted
        self.snippet_wanted = None
        target = snippet_file(here, mode, self.preview_folder)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self._snippet_failed(mode, str(exc), self._snippet_epoch)
            return
        process = proc.qprocess(self)
        process.setWorkingDirectory(str(here.typst_root))
        process.finished.connect(self._process_finished)
        process.errorOccurred.connect(self._process_error)
        process.started.connect(lambda: self._feed(process, source))
        timeout = QTimer(process)
        timeout.setSingleShot(True)
        timeout.timeout.connect(self._timeout)
        timeout.start(COMPILE_TIMEOUT_MS)
        self.process, self.running, self.timed_out = process, None, False
        self.snippet_running = (here, mode, target, key, self._snippet_epoch)
        self._show_busy()
        self.busyChanged.emit(True)
        self.started.emit(mode)
        process.start(project.typst_executable(), ["compile", "--root", str(here.typst_root), "-", str(target)])

    @staticmethod
    def _feed(process, source):
        """The snippet handed to Typst on its standard input, which is then closed: Typst reads to the end before it compiles."""
        if shiboken6.isValid(process):
            process.write(source.encode("utf-8"))
            process.closeWriteChannel()

    def _timeout(self):
        if self.process is not None:
            self.timed_out = True
            self.process.kill()

    def _process_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:     # the one error no `finished` follows: a Typst that is not there
            self._process_done(-1, "", self.process.errorString() if self.process is not None else "")

    def _process_finished(self, code, status):
        process = self.process
        if process is None:
            return
        stdout = bytes(process.readAllStandardOutput()).decode("utf-8", "replace")
        stderr = bytes(process.readAllStandardError()).decode("utf-8", "replace")
        if status != QProcess.ExitStatus.NormalExit:       # stopped at the timeout, or crashed
            code, stderr = -1, f"{stderr}\n{process.errorString()}".strip()
        self._process_done(code, stdout, stderr)

    def _process_done(self, code, stdout, stderr):
        if self.process is not None:
            self.process.deleteLater()
        self.process = None
        self._end_activity()
        if self.killed:         # ended on purpose, for a snippet: neither a result nor a failure
            self.killed = False
            self.running = self.snippet_running = None
            self._show_busy()
            self.busyChanged.emit(self.is_busy())
            self._start_wanted()
            return
        if self.snippet_running is not None:
            here, mode, target, key, epoch = self.snippet_running
            self.snippet_running = None
            if code != 0:
                message = (stderr or stdout).strip()
                if self.timed_out:
                    message = self.t("pp_timeout", minutes=COMPILE_TIMEOUT_MS // 60000) + ("\n" + message if message else "")
                self._snippet_failed(mode, message, epoch)
            else:
                self._snippet_shown(here, mode, target, key, epoch)
            return
        here, mode, target, deps = self.running
        self.running = None
        if code != 0:
            message = (stderr or stdout).strip()
            if self.timed_out:
                message = self.t("pp_timeout", minutes=COMPILE_TIMEOUT_MS // 60000) + ("\n" + message if message else "")
            self._failed(mode, message)
            return

        def record():
            try:
                stamps.record(here, mode, [], deps, target, preview=True)
            except OSError:
                pass    # a preview not stamped is one said to be stale, and compiled again: slow, never wrong
            return stamps.changed(here, mode, [], ignore_flags=True, preview=True)

        self._check_generation += 1
        generation, epoch = self._check_generation, self._epoch
        self.recording = _start_job(record, self, lambda result, error: self._recorded(epoch, generation, (here, mode), target, result, error))

    def _snippet_shown(self, here, mode, target, key, epoch):
        """A snippet compiled: shown from the top where it is still the one wanted and the document it belongs to is still the one shown; dropped otherwise."""
        if epoch == self._snippet_epoch and _same((here, mode), (self.here, self.mode)):
            self.last_error = None
            self._show_error()
            if self.load(target, keep_place=False):
                self.shown_snippet, self.shown_preview = key, False
                self._show_stale()
                self.snippetCompiled.emit(key)
        self._show_busy()
        self.busyChanged.emit(self.is_busy())
        self._start_wanted()

    def _snippet_failed(self, mode, message, epoch):
        """A snippet that did not give a page: Typst's message in the banner, what was shown left shown, the next request started."""
        if epoch == self._snippet_epoch and self.here is not None and mode == self.mode:
            self.last_error = message or "?"
            self._show_error()
        self._show_busy()
        self.busyChanged.emit(self.is_busy())
        self.failed.emit(mode, message)
        self._start_wanted()

    def _recorded(self, epoch, generation, document, target, result, error):
        if epoch != self._epoch:
            return      # stopped meanwhile: nobody waits for this compile any more
        self.recording = None
        here, mode = document
        if _same(document, (self.here, self.mode)):
            self.last_error = None
            self._show_error()
            if self.load(target, keep_place=True):     # the same document, its own PDF or its last preview: the place is kept
                self.shown_preview = True
                self.shown_snippet = None
            self._checked(generation, document, result, error)
        self._show_busy()
        self.busyChanged.emit(self.is_busy())
        self.compiled.emit(mode)
        self._start_wanted()

    def _failed(self, mode, message):
        """A compile that did not give a PDF: Typst's message in the banner, what was shown left shown, and the next request started."""
        if self.here is not None and mode == self.mode:
            self.last_error = message or "?"
            self._show_error()
        self._show_busy()
        self.busyChanged.emit(self.is_busy())
        self.failed.emit(mode, message)
        self._start_wanted()

    def _end_activity(self):
        """The chip at the top right told the compile is over -- by its end, and by `stop`, whose kill no `finished` follows (else the chip said «Aperçu Typst» for the rest of the session)."""
        if getattr(self, "_activity", None) is not None:
            tasks.activity().end(self._activity)
            self._activity = None

    def _show_busy(self):
        self.busy_row.setHidden(not self.is_busy())

    def stop(self):
        """Ends what runs: the compile is killed, a request forgotten, and the stamps being written waited for -- what the window's quitting does, and a test's end."""
        self.timer.stop()
        self.snippet_timer.stop()
        self.wanted = None
        self.snippet_wanted = None
        self._snippet_epoch += 1
        self._epoch += 1
        self._check_generation += 1
        process = self.process
        if process is not None:
            process.finished.disconnect(self._process_finished)
            process.errorOccurred.disconnect(self._process_error)
            process.kill()
            process.waitForFinished(5000)
            process.deleteLater()
            self.process, self.running, self.snippet_running, self.killed = None, None, None, False
        self._end_activity()
        for job in list(_RUNNING):
            job.wait(10000)
        self.recording = None
        self._show_busy()
