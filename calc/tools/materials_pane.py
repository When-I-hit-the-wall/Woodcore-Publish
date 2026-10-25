"""The right pane of the «Matériaux» tab, a service of the type «Bibliothèque» (spec docs/requirements/active/2026-10-24-onglet-materiaux.md, UI-007, UI-008, REQ-009, REQ-010, REQ-012; issue #110).

Four modules of a `module_pane.ModulePane`, in this order: **État** -- what the domain says of the draft (`materials_derive.status`): green complete, orange what keeps it from a use, red a name another material carries, the rest only said --; **La source** -- the excerpt of the norm, cut from the edition shipped in norm-library/ (`norm_bubble.ExcerptView`), the PDF imported (`pdf_pane.ZoomablePdfView`), the website with «ouvrir dans le navigateur», or, for a material of the engineer's own with none, a place to drop a PDF or import one --, its ⤢ opening it large over the window (`BigView`: Échap or × closes it); **Disponible dans** -- the tabs it is offered in and what it lacks for the others (`materials_derive.available_in`) --; **Où il est enregistré** -- the file, its PDF, and the copies the projects that use it keep. A label of a source asks the context to show this pane's «La source» (`revealRequested`): it unfolds, scrolls into sight and flashes (`ModulePane.reveal`).
"""

from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QEvent, QIODevice, QUrl, Qt
from PySide6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PySide6.QtPdf import QPdfDocument
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QToolButton, QVBoxLayout, QWidget

import theme
from domains import materials_derive as derive, materials_library, materials_user
from module_pane import ModulePane, ModuleSpec
from norms import excerpts as norm_excerpts
from tab_host import Service

LEVEL_COLOUR = {"ok": "ok", "warn": "warning", "error": "danger", "info": "muted"}
USE_ORDER = ("tab_ac_selfweight", "tab_mc", "tab_connections", "tab_plates")


class _Body(QWidget):
    """A module's body, drawn again by `refresh()` from the context. Its height is the one its wrapped lines need at its width, set by itself (`_fit`): a layout's cache of a height for a width would keep, inside the pane's scroll area, the height a body had before it was drawn anew."""

    def __init__(self, draw):
        super().__init__()
        self.draw = draw
        self.column = QVBoxLayout(self)
        self.column.setContentsMargins(0, 0, 0, 0)
        self.refresh()

    def refresh(self):
        while self.column.count():
            widget = self.column.takeAt(0).widget()
            if widget is not None:
                for document in widget.findChildren(QPdfDocument):
                    document.close()       # the PDF let go at once: Windows refuses to delete a file a view still holds
                widget.setParent(None)     # gone from the pane at once, not when Qt gets round to deleting it
                widget.deleteLater()
        self.draw(self.column)
        self.column.addStretch(1)     # what the height set leaves over, under the lines and not between them
        self._fit()

    def hasHeightForWidth(self):
        return False

    def _fit(self):
        width = self.width() if self.width() > 50 else 300
        self.setMinimumHeight(self.column.heightForWidth(width) if self.column.hasHeightForWidth() else self.column.sizeHint().height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if event.size().width() != event.oldSize().width():
            self._fit()


class BigView(QFrame):
    """The source large, over the window: a frame on the window's whole size, its title and ×, the source under them; Échap or × closes it (T40)."""

    def __init__(self, window, title, body, t):
        super().__init__(window)
        self.window_ = window
        self.setObjectName("bigView")
        self.setStyleSheet("QFrame#bigView { background: %s; border: 1px solid %s; }" % (theme.colour("bg"), theme.colour("line-strong")))
        column = QVBoxLayout(self)
        head = QHBoxLayout()
        label = QLabel(title)
        label.setStyleSheet("font-weight: 600;")
        head.addWidget(label, 1)
        self.close_button = QToolButton()
        self.close_button.setText("×")
        self.close_button.setToolTip(t("mat_close"))
        self.close_button.clicked.connect(self.close)
        head.addWidget(self.close_button)
        column.addLayout(head)
        column.addWidget(body, 1)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self.close)   # Échap closes it, as ×
        window.installEventFilter(self)
        self._fit()
        self.show()
        self.raise_()
        self.setFocus()

    def _fit(self):
        self.setGeometry(self.window_.rect().adjusted(24, 24, -24, -24))

    def eventFilter(self, obj, event):
        if obj is self.window_ and event.type() == QEvent.Type.Resize:
            self._fit()
        return False

    def closeEvent(self, event):
        self.window_.removeEventFilter(self)
        self.deleteLater()
        super().closeEvent(event)


class _DropZone(QFrame):
    """A place to drop a PDF, for a material of the engineer's own without a source."""

    def __init__(self, t, dropped, chosen):
        super().__init__()
        self.dropped = dropped
        self.setAcceptDrops(True)
        self.setObjectName("dropZone")
        self.setStyleSheet("QFrame#dropZone { border: 1px dashed %s; border-radius: 6px; }" % theme.colour("line-strong"))
        column = QVBoxLayout(self)
        label = QLabel(t("mat_drop"))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        column.addWidget(label)
        button = QPushButton(t("mat_import_pdf"))
        button.clicked.connect(chosen)
        column.addWidget(button, 0, Qt.AlignmentFlag.AlignCenter)

    def dragEnterEvent(self, event):
        urls = event.mimeData().urls()
        if urls and urls[0].toLocalFile().lower().endswith(".pdf"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.dropped(event.mimeData().urls()[0].toLocalFile())
        event.acceptProposedAction()


class MaterialModules(Service):
    """The right pane of the materials -- see the module's docstring."""

    NAME = "modules"
    ZONE = "right"
    IN_VIEWS = ()

    def mount(self, ctx):
        super().mount(ctx)
        self.pane = ModulePane(self.t, ctx.tab.KEY)
        self.bodies = {}
        for mid, title, draw in (("state", "mat_m_state", self._state), ("source", "mat_m_source", self._source), ("available", "mat_m_available", self._available),
                                 ("where", "mat_m_where", self._where)):
            self.pane.add(ModuleSpec(mid, self.t(title), lambda d=draw, m=mid: self.bodies.setdefault(m, _Body(d)), kind=mid))
        ctx.revealRequested.connect(self.pane.reveal)
        return self.pane

    def selected(self):
        self.refresh()

    def drafted(self):
        for mid in ("state", "available", "where"):
            self.pane.refresh(mid)

    def listed(self):
        self.refresh()

    def refresh(self):
        self.pane.refresh()

    # --- the modules ----------------------------------------------------------------

    def _label(self, column, text, colour=None, rich=False):
        label = QLabel(text)
        label.setWordWrap(True)
        label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        label.setTextFormat(Qt.TextFormat.RichText if rich else Qt.TextFormat.PlainText)
        if colour:
            label.setStyleSheet("color: %s;" % theme.colour(colour))
        column.addWidget(label)
        return label

    def _state(self, column):
        m = self.ctx.draft
        if self.ctx.error:
            self._label(column, "● " + self.t("mat_st_unreadable", error=self.ctx.error), "danger")
        if m is None:
            return
        others = [e for e in self.ctx.entries if e["id"] != m["id"]]
        for s in derive.status(m, others, self.app.lang):
            self._label(column, "● " + self.t("mat_st_" + s.code, **s.params), LEVEL_COLOUR[s.level])

    def _source(self, column):
        m = self.ctx.draft
        if m is None:
            return
        view = self.source_view(m)
        if view is not None:
            column.addWidget(view)
            big = QPushButton("⤢ " + self.t("mat_big"))
            big.setFlat(True)
            big.clicked.connect(self.open_big)
            column.addWidget(big, 0, Qt.AlignmentFlag.AlignRight)

    def source_view(self, m, large=False):
        """The widget of a material's source: an excerpt of the norm, the PDF, the website, or a place to drop a PDF -- None where a shipped material names none."""
        if m.get("excerpt"):
            norm, eid = m["excerpt"]
            return self._excerpt(norm, eid)
        source = m.get("source") or {}
        if source.get("kind") == "pdf" and source.get("file"):
            return self._pdf(materials_user.source_path(m), large)
        if source.get("kind") == "url" and source.get("url"):
            holder = QWidget()
            column = QVBoxLayout(holder)
            column.setContentsMargins(0, 0, 0, 0)
            self._label(column, '<a href="%s">%s</a>' % (source["url"], source["url"]), rich=True).setOpenExternalLinks(True)
            button = QPushButton(self.t("mat_open_web"))
            button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(source["url"])))
            column.addWidget(button, 0, Qt.AlignmentFlag.AlignLeft)
            return holder
        if source.get("kind") == "book" and source.get("ref"):
            label = QLabel(source["ref"])
            label.setWordWrap(True)
            return label
        if materials_library.editable(m) and self.ctx.editable():
            return _DropZone(self.t, self._dropped, lambda: self._sheet_import())
        label = QLabel(self.t("mat_no_source"))
        label.setStyleSheet("color: %s;" % theme.colour("muted"))
        return label

    def _excerpt(self, norm, eid):
        from norm_bubble import ExcerptView
        return ExcerptView([norm_excerpts.excerpt(norm, eid, self.app.lang)], self.t)

    def _pdf(self, path, large):
        if path is None or not Path(path).is_file():
            label = QLabel(self.t("mat_pdf_missing", file=str(path)))
            label.setWordWrap(True)
            return label
        from pdf_pane import ZoomablePdfView
        view = ZoomablePdfView(lang=self.app.lang)
        document = QPdfDocument(view)      # the view's: closed and deleted with it
        # read from its bytes and not from its path: QPdfDocument.load(path) keeps the file open on Windows even closed and deleted, and a material deleted could not take its PDF with it
        buffer = QBuffer(view)
        buffer.setData(QByteArray(Path(path).read_bytes()))
        buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        document.load(buffer)
        view.setDocument(document)
        view.setMinimumHeight(560 if large else 320)
        return view

    def _dropped(self, path):
        """A PDF dropped on the source: copied into the library and named by the draft, as «Importer un PDF…» does."""
        rel = materials_user.import_pdf(path)
        self.ctx.draft["source"] = {"kind": "pdf", "file": rel}
        self.ctx.rebuild()

    def _sheet_import(self):
        from PySide6.QtWidgets import QFileDialog
        path, _filter = QFileDialog.getOpenFileName(self.ctx.tab, self.t("mat_import_pdf"), "", self.t("mat_pdf_filter"))
        if path:
            self._dropped(path)

    def open_big(self):
        """⤢: the source large, over the window."""
        m = self.ctx.draft
        if m is None:
            return None
        view = self.source_view(m, large=True)
        if view is None:
            return None
        self.big = BigView(self.ctx.tab.window(), "%s · %s" % (self.t("mat_m_source"), materials_library.name(m, self.app.lang)), view, self.t)
        return self.big

    def _available(self, column):
        m = self.ctx.draft
        if m is None:
            return
        for use in derive.available_in(m):
            mark = {"yes": "✓", "no": "✗", "soon": "…"}[use.status]
            colour = {"yes": "ok", "no": "warning", "soon": "muted"}[use.status]
            text = "%s %s" % (mark, self.t("mat_use_" + use.tab))
            if use.status == "soon":
                text += " — " + self.t("mat_use_soon")
            if use.need:
                text += " — " + self.t("mat_need_" + use.need)
            self._label(column, text, colour)

    def _where(self, column):
        m = self.ctx.draft
        if m is None:
            return
        self._label(column, materials_library.stored(m))
        pdf = materials_user.source_path(m) if materials_library.editable(m) else None
        if pdf is not None:
            self._label(column, self.t("mat_where_pdf", file=str(pdf)))
        if materials_library.editable(m):
            self._label(column, self.t("mat_where_copies"), "muted")
