"""Woodcore's «Annexes» tab (docs/domain/annexes.md §3.3undevicies, docs/ui/window.md §10quater, v0.115): the documents the report draws on from outside -- a FEM program's print report first -- and the excerpts it shows of them.

The engineer: «à l'intérieur du dossier il doit y avoir 2 dossiers. Le premier se nomme ''Source'' et si on rentre dans celui-ci on peut ajouter un pdf. Et le second s'appelle ''Aperçu'' [«Extraits» since]». The list is a tree of those two fixed folders, in the tab's own list pane -- «dans le deuxième volet», beside the side navigation and not in it.

**Adding a source copies the PDF into the project** (the engineer's answer B3), `Woodcore-Datei/annexes/sources/<id>.pdf`, and «Remplacer le PDF…» writes a new version over it (B4): every excerpt then follows it, and the source's card says, excerpt by excerpt, whether it was found again.

**An excerpt is made in three steps, on the page itself.** Its source; then its title, clicked on the page or chosen among the source's bookmarks -- a print report's headings are drawn as vector paths and carry no text, so the title is found by its **bookmark** and not by selecting its words (measured on the engineer's own RFEM export, calc/domains/annex.py); then its frame, dragged over the page. A title used several times («Charges de barre» under each load case) is told apart by the path of titles above it, and the card says how many there are and which this one is. A source with no bookmark -- a PDF printed through a PDF printer -- is framed on its page directly, and such an excerpt must be confirmed again after every new version of its source.

**Every write goes through calc/domains/annex.py and is followed by an export of the annexes alone** (`annex.export`), so `data/annexes.json` and the cropped pages follow at once and the report sees them without the load workbooks being read again -- the arrangement every editor tab has.

The PDF is rendered by QtPdf **from its bytes**, never from its file: a document QtPdf holds open is one Windows refuses to let «Remplacer» write over.

The tab lives in its own module, which woodcore_gui.py lists in its TABS and whose STRINGS it merges into its own: the keys carry an `ax_` prefix of their own, and the warnings of calc/domains/annex.py a `warn_annex_` one, which `woodcore_gui.note_text` reads.
"""

import shutil
import threading
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QObject, QRectF, QSize, QSizeF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QKeySequence, QPainter, QPen, QShortcut
from PySide6.QtPdf import QPdfDocument
from PySide6.QtWidgets import (
    QAbstractItemView, QAbstractScrollArea, QButtonGroup, QComboBox, QFileDialog, QHBoxLayout, QHeaderView, QInputDialog, QLabel, QMessageBox,
    QPushButton, QRadioButton, QSpinBox, QSplitter, QToolButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

import build_reference as ref  # the one place a Typst call is spelled out (docs/typst/reference-workbook.md §10ter)
import cards
import document_view  # the plans' view of a document's pages, a source's pages here (issue #16)
import autosave  # saving without a question, and what is never saved without the engineer (autosave.py, v0.117)
import identity  # Nom · Description · ID, and the ID composed of the name (identity.py)
import project
import richtext
import theme
import validation
import notifications  # every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # what was a message box is a notice since v0.117 (notices_ui.tell)
from domains import annex as model  # the one module that reads and writes Woodcore-Datei/annexes/
from annex_tab_words import STRINGS  # split out of this module (issue #30): every name it had is still importable from it
from annex_tab_pages import FRAME_COLOUR, Pdf, SourcePages, TITLE_COLOUR, _Finder  # split out of this module (issue #30): every name it had is still importable from it

SOURCES, EXCERPTS = "source", "excerpt"


def plain_label(text="", wrap=False):
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(wrap)
    return label


class AnnexList(QTreeWidget):
    """The two fixed folders, «Sources» and «Extraits», and what each holds. `rows()` is every entry, never a folder -- what the window's marks and tests read."""

    ROLE = Qt.ItemDataRole.UserRole

    def rows(self):
        found = []
        for i in range(self.topLevelItemCount()):
            folder = self.topLevelItem(i)
            for j in range(folder.childCount()):
                item = folder.child(j)
                found.append((item, item.data(0, self.ROLE)))
        return found

    def item_of(self, key):
        return next((item for item, k in self.rows() if k == key), None)


class AnnexTab(QWidget):
    """Lists the annexes' sources and excerpts, edits one at a time, and writes them through calc/domains/annex.py."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.t = app.t
        self.loading = False
        self.dirty = False
        self.kind = None        # SOURCES or EXCERPTS: what the form holds
        self.current = None     # its id; None for an excerpt not written yet
        self.draft = None       # what the form holds, as the file would hold it
        self.original = None
        self.sources, self.excerpts = {}, {}
        self.pdfs = {}          # {source id: Pdf}
        self.mode = "frame"     # how a gesture on the pages extracts (issue #16): "frame", "pages" or "found"
        self.finder = _Finder(self)   # the frames of a page, found off the window's thread
        self.finder.found.connect(self.on_found)
        self.asked = set()      # (sha, page) asked of the finder and not yet found
        self.error = None
        self.last_export = {}   # data/annexes.json as the last export wrote it

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.build_list())
        self.splitter.addWidget(self.build_viewer())
        self.splitter.addWidget(self.build_form())
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(2, 0)
        self.sized = False      # the panes' widths are set the first time the tab is shown, when the splitter knows its own
        layout.addWidget(self.splitter, 1)
        shortcut = QShortcut(QKeySequence(QKeySequence.StandardKey.Save), self)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.activated.connect(self.save)
        self.restore(app.views.get("tab_annexes"))

    # -- building ---------------------------------------------------------------------

    def build_list(self):
        panel = QWidget()
        box = QVBoxLayout(panel)
        box.setContentsMargins(0, 0, 6, 0)
        title = plain_label(self.t("ax_list"))
        title.setFont(self.app.bold_font)
        box.addWidget(title)
        self.list = AnnexList()
        self.list.setHeaderHidden(True)
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list.setIconSize(self.app.mark_size)
        self.list.currentItemChanged.connect(self.on_list_change)
        box.addWidget(self.list, 1)
        row = QHBoxLayout()
        for key, slot in (("ax_add_source", self.add_annex_source), ("ax_new_excerpt", self.new), ("ax_delete", self.delete)):
            button = QPushButton(self.t(key))
            button.clicked.connect(slot)
            row.addWidget(button)
        row.addStretch(1)
        box.addLayout(row)
        box.addWidget(self.build_extract())
        return panel

    def build_extract(self):
        """The section «Extraire» under the list (issue #16): three ways of making excerpts, one at a time -- «Cadre», each frame drawn an excerpt; «Pages», each page of a range an excerpt; «Cadre trouvé», a frame the page's drawing holds, clicked."""
        section = QWidget()
        v = QVBoxLayout(section)
        v.setContentsMargins(0, 8, 0, 0)
        title = plain_label(self.t("ax_extract"))
        title.setFont(self.app.bold_font)
        v.addWidget(title)
        self.mode_group = QButtonGroup(self)
        self.mode_buttons = {}
        for mode in ("frame", "pages", "found"):
            button = QRadioButton(self.t("ax_mode_" + mode))
            button.setToolTip(self.t("ax_mode_%s_tip" % mode))
            self.mode_group.addButton(button)
            self.mode_buttons[mode] = button
            v.addWidget(button)
            button.toggled.connect(lambda on, mode=mode: on and self.set_mode(mode))
            if mode == "pages":
                pages = QWidget()
                row = QHBoxLayout(pages)
                row.setContentsMargins(18, 0, 0, 0)
                row.setSpacing(4)   # «de [1] à [1]» within the pane's floor (issue #10), the number boxes squeezed by cards.loosen
                row.addWidget(plain_label(self.t("ax_from")))
                self.from_spin = QSpinBox()
                self.from_spin.setRange(1, 1)
                row.addWidget(self.from_spin)
                row.addWidget(plain_label(self.t("ax_to")))
                self.to_spin = QSpinBox()
                self.to_spin.setRange(1, 1)
                row.addWidget(self.to_spin)
                row.addStretch(1)
                v.addWidget(pages)
                self.pages_row = pages
                self.extract_pages_button = QPushButton(self.t("ax_extract_pages"))
                self.extract_pages_button.clicked.connect(self.extract_annex_pages)
                v.addWidget(self.extract_pages_button)
        self.mode_buttons["frame"].setChecked(True)
        self.set_mode("frame")
        return section

    def set_mode(self, mode):
        """How a gesture on the pages extracts; the range shown with «Pages» alone, the frames found looked for with «Cadre trouvé» alone."""
        self.mode = mode
        for widget in (getattr(self, "pages_row", None), getattr(self, "extract_pages_button", None)):
            if widget is not None:
                widget.setEnabled(mode == "pages")
                widget.setToolTip("" if mode == "pages" else self.t("ax_extract_pages_off"))   # a disabled control says why (tests/test_window.py)
        view = getattr(self, "view", None)
        if view is None:
            return
        view.finding = mode == "found"
        view.hover, view.level = None, 0
        if view.finding:
            self.find_frames(view.page)
            self.hint.setText(self.t("ax_found_pick"))
        view.update()

    def build_viewer(self):
        panel = QWidget()
        box = QVBoxLayout(panel)
        box.setContentsMargins(6, 0, 6, 0)
        self.hint = plain_label("", wrap=True)
        box.addWidget(self.hint)
        self.viewer_split = QSplitter(Qt.Orientation.Horizontal)
        self.viewer_split.setChildrenCollapsible(False)
        marks = QWidget()
        mbox = QVBoxLayout(marks)
        mbox.setContentsMargins(0, 0, 0, 0)
        mbox.addWidget(plain_label(self.t("ax_bookmark_list")))
        self.marks = QTreeWidget()
        self.marks.setHeaderHidden(True)
        self.marks.itemClicked.connect(self.on_mark_clicked)
        mbox.addWidget(self.marks, 1)
        self.viewer_split.addWidget(marks)
        pages = QWidget()
        pbox = QVBoxLayout(pages)
        pbox.setContentsMargins(0, 0, 0, 0)
        nav = QHBoxLayout()
        nav.addWidget(plain_label(self.t("ax_page")))
        self.page_spin = QSpinBox()
        self.page_spin.setRange(1, 1)
        self.page_spin.valueChanged.connect(self.go_to)
        nav.addWidget(self.page_spin)
        self.page_total = plain_label("")
        nav.addWidget(self.page_total)
        nav.addStretch(1)
        # zoomed out, two, three pages and more side by side; in, one page wider than the pane (issue #16) -- the plans' view's own buttons and words (document_view)
        zoom_words = document_view.words(self.app.lang)
        self.view = SourcePages(t=zoom_words)
        for key, icon, slot in (("dv_zoom_out", "zoom-out", lambda: self.view.set_zoom(self.view.zoom / 1.25)),
                                ("dv_zoom_in", "zoom-in", lambda: self.view.set_zoom(self.view.zoom * 1.25)),
                                ("dv_fit_width", "fit-width", self.view.fit_width)):
            button = QToolButton()
            button.setAutoRaise(True)
            button.setToolTip(zoom_words(key))
            button.setIcon(document_view.icon(icon, 18))
            button.clicked.connect(slot)
            nav.addWidget(button)
        pbox.addLayout(nav)
        self.view.clicked.connect(self.on_page_click)
        self.view.dragged.connect(self.on_page_drag)
        self.view.pageChosen.connect(self.on_page_chosen)
        self.view.verticalScrollBar().valueChanged.connect(lambda _v: self.find_frames(self.view_page_in_middle()) if self.mode == "found" else None)
        pbox.addWidget(self.view, 1)
        self.viewer_split.addWidget(pages)
        self.viewer_split.setStretchFactor(1, 4)
        box.addWidget(self.viewer_split, 1)
        return panel

    def build_form(self):
        outer = QWidget()
        shell = QVBoxLayout(outer)
        shell.setContentsMargins(6, 0, 0, 0)
        area, box = cards.column()
        self.banner = plain_label("", wrap=True)
        self.banner.setVisible(False)
        box.addWidget(self.banner)

        # the source's card
        self.source_card = cards.card(self.t("ax_source_card"))
        form = cards.form(self.source_card)
        self.source_identity = identity.IdentityRows(form, self.t, self.changed)
        self.file_label = plain_label("", wrap=True)
        form.addRow(self.t("ax_file"), self.file_label)
        self.pages_label = plain_label("")
        form.addRow(self.t("ax_pages"), self.pages_label)
        self.bookmarks_label = plain_label("")
        form.addRow(self.t("ax_bookmarks"), self.bookmarks_label)
        self.text_label = plain_label("")
        form.addRow(self.t("ax_text"), self.text_label)
        self.no_bookmark = cards.note(self.t("ax_no_bookmark_note"))
        form.addRow(self.no_bookmark)
        self.mode_combo = QComboBox()
        for mode in model.MODES:
            self.mode_combo.addItem(self.t("ax_mode_" + mode), mode)
        self.mode_combo.currentIndexChanged.connect(self.changed)
        form.addRow(self.t("ax_mode"), self.mode_combo)
        self.replace_button = QPushButton(self.t("ax_replace"))
        self.replace_button.clicked.connect(self.replace_annex_source)
        form.addRow(self.replace_button)
        box.addWidget(self.source_card)
        self.status_card = cards.card(self.t("ax_status"))
        self.status_layout = QVBoxLayout(self.status_card)
        box.addWidget(self.status_card)

        # the excerpt's card
        self.excerpt_card = cards.card(self.t("ax_excerpt_card"))
        form = cards.form(self.excerpt_card)
        self.excerpt_identity = identity.IdentityRows(form, self.t, self.changed)
        self.source_label = plain_label("")
        form.addRow(self.t("ax_source"), self.source_label)
        self.title_label = plain_label("", wrap=True)
        form.addRow(self.t("ax_title"), self.title_label)
        self.occurrence_label = cards.note("")
        form.addRow(self.occurrence_label)
        self.frame_label = plain_label("", wrap=True)
        form.addRow(self.t("ax_frame"), self.frame_label)
        self.state_label = plain_label("", wrap=True)
        form.addRow(self.t("ax_state"), self.state_label)
        self.confirm_button = QPushButton(self.t("ax_confirm"))
        self.confirm_button.setToolTip(self.t("ax_confirm_tip"))
        self.confirm_button.clicked.connect(self.confirm)
        form.addRow(self.confirm_button)
        box.addWidget(self.excerpt_card)
        self.preview_card = cards.card(self.t("ax_preview"))
        pv = QVBoxLayout(self.preview_card)
        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pv.addWidget(self.preview)
        box.addWidget(self.preview_card)
        self.calls_card = cards.card(self.t("ax_commands"))
        self.calls_layout = QVBoxLayout(self.calls_card)
        box.addWidget(self.calls_card)
        box.addStretch(1)
        shell.addWidget(area, 1)

        actions = QHBoxLayout()
        actions.addStretch(1)
        revert = QPushButton(self.t("ax_revert"))
        revert.clicked.connect(self.revert)
        actions.addWidget(revert)
        save = QPushButton(self.t("ax_save"))
        save.setDefault(True)
        save.clicked.connect(self.save)
        actions.addWidget(save)
        shell.addLayout(actions)
        return outer

    # -- reading ----------------------------------------------------------------------

    def here(self):
        return project.current()

    def read_all(self):
        """The sources and excerpts read afresh, and the banner saying what cannot be done with them. Never raises."""
        self.error = None
        try:
            self.sources = model.list_sources(self.here())
            self.excerpts = model.list_excerpts(self.here())
        except validation.ValidationError as exc:
            self.sources, self.excerpts, self.error = {}, {}, exc
        self.last_export = model.previous_export(self.here().data_dir)
        self.update_banner()

    def update_banner(self):
        kind, text = None, ""
        if self.error is not None:
            kind, text = "danger", self.t("ax_banner_unreadable", error=self.error)
        elif not self.sources:
            kind, text = "info", self.t("ax_banner_empty")
        self.banner.setText(text)
        self.banner.setProperty("callout", kind or "info")
        self.banner.style().unpolish(self.banner)
        self.banner.style().polish(self.banner)
        self.banner.setVisible(bool(text))

    def pdf_of(self, sid):
        """The source's PDF, read once while unchanged; None where its file is missing or cannot be read."""
        path = model.pdf_path(self.here(), sid)
        known = self.pdfs.get(sid)
        try:
            if known is not None and known.path == path and path.is_file() and model.file_hash(path) == known.sha:
                return known
            if known is not None:
                known.close()
            if not path.is_file():
                self.pdfs.pop(sid, None)
                return None
            self.pdfs[sid] = Pdf(path)
        except (OSError, validation.ValidationError):
            self.pdfs.pop(sid, None)
            return None
        return self.pdfs[sid]

    # -- the list -----------------------------------------------------------------------

    def fill_list(self, select=None):
        loading, self.loading = self.loading, True
        self.list.clear()
        folders = {}
        for kind, key in ((SOURCES, "ax_sources"), (EXCERPTS, "ax_excerpts")):
            folder = QTreeWidgetItem([self.t(key)])
            folder.setFlags(Qt.ItemFlag.ItemIsEnabled)
            folder.setFont(0, self.app.bold_font)
            folder.setData(0, AnnexList.ROLE, None)
            self.list.addTopLevelItem(folder)
            folders[kind] = folder
        for sid, source in self.sources.items():
            item = QTreeWidgetItem([source.get("name") or sid])
            item.setToolTip(0, sid)
            item.setData(0, AnnexList.ROLE, (SOURCES, sid))
            item.setIcon(0, self.app.dirty_mark(False))
            folders[SOURCES].addChild(item)
        for eid, excerpt in self.excerpts.items():
            item = QTreeWidgetItem([excerpt.get("name") or eid])
            record = self.last_export.get("excerpts", {}).get(eid, {})
            item.setToolTip(0, eid if record.get("resolved", True) else record.get("reason", eid))
            if record and not record.get("resolved", True):
                item.setForeground(0, QColor(theme.colour("danger")))
            item.setData(0, AnnexList.ROLE, (EXCERPTS, eid))
            item.setIcon(0, self.app.dirty_mark(False))
            folders[EXCERPTS].addChild(item)
        if self.kind == EXCERPTS and self.current is None and self.draft is not None:
            item = QTreeWidgetItem([self.t("ax_new_item")])
            item.setData(0, AnnexList.ROLE, (EXCERPTS, None))
            item.setIcon(0, self.app.dirty_mark(False))
            folders[EXCERPTS].addChild(item)
        self.list.expandAll()
        target = select if select is not None else (self.kind, self.current)
        item = self.list.item_of(target)
        if item is not None:
            self.list.setCurrentItem(item)
        self.loading = loading
        self.update_list_marker()

    def update_list_marker(self):
        for item, key in self.list.rows():
            mine = key == (self.kind, self.current)
            item.setIcon(0, self.app.dirty_mark(mine and self.dirty))
        self.app.update_tab_marks()

    def on_list_change(self, item, _previous=None):
        if self.loading or item is None:
            return
        key = item.data(0, AnnexList.ROLE)
        if not key or key == (self.kind, self.current):
            return
        if not self.confirm_leave():
            self.fill_list()
            return
        self.load(*key)

    # -- loading one ----------------------------------------------------------------------

    def load(self, kind, key):
        if kind == SOURCES and key in self.sources:
            self.kind, self.current = SOURCES, key
            self.draft, self.original = model.snapshot(self.sources[key]), model.snapshot(self.sources[key])
        elif kind == EXCERPTS and key in self.excerpts:
            self.kind, self.current = EXCERPTS, key
            self.draft, self.original = model.snapshot(self.excerpts[key]), model.snapshot(self.excerpts[key])
        else:
            self.load_first()
            return
        self.dirty = False
        self.fill_form()
        self.fill_list()

    def load_first(self):
        if self.excerpts:
            self.load(EXCERPTS, next(iter(self.excerpts)))
        elif self.sources:
            self.load(SOURCES, next(iter(self.sources)))
        else:
            self.kind, self.current, self.draft, self.original = None, None, None, None
            self.dirty = False
            self.fill_form()
            self.fill_list()

    # -- the form -------------------------------------------------------------------------

    def changed(self, *_args):
        if self.loading or self.draft is None:
            return
        self.read_form()
        self.dirty = True
        self.update_list_marker()
        self.fill_commands()

    def read_form(self):
        """The identity rows and the mode combo into the draft."""
        if self.kind == SOURCES:
            name, description, sid = self.source_identity.values()
            self.draft.update(name=name, label=description, id=sid, mode=self.mode_combo.currentData() or model.DEFAULT_MODE)
        elif self.kind == EXCERPTS:
            name, description, eid = self.excerpt_identity.values()
            self.draft.update(name=name, label=description, id=eid)

    def fill_form(self):
        self.loading = True
        self.source_card.setVisible(self.kind == SOURCES)
        self.status_card.setVisible(self.kind == SOURCES)
        for card in (self.excerpt_card, self.preview_card):
            card.setVisible(self.kind == EXCERPTS)
        self.calls_card.setVisible(self.kind is not None)
        if self.kind == SOURCES:
            d = self.draft
            self.source_identity.fill(d.get("name", ""), d.get("label", ""), d.get("id", ""), saved=self.current is not None)
            self.mode_combo.setCurrentIndex(max(0, self.mode_combo.findData(d.get("mode", model.DEFAULT_MODE))))
            pdf = self.pdf_of(self.current)
            self.file_label.setText(d.get("original") or model.pdf_path(self.here(), self.current).name)
            self.pages_label.setText(str(pdf.pages()) if pdf else "—")
            self.bookmarks_label.setText(str(len(pdf.marks)) if pdf else "—")
            self.text_label.setText((self.t("ax_yes") if pdf.text else self.t("ax_no")) if pdf else "—")
            self.no_bookmark.setVisible(bool(pdf) and not pdf.marks)
            self.fill_status()
            self.view.band, self.view.frame, self.view.others = None, None, []
            self.hint.setText("")
            self.show_source(self.current, 1)
        elif self.kind == EXCERPTS:
            d = self.draft
            self.excerpt_identity.fill(d.get("name", ""), d.get("label", ""), d.get("id", ""), saved=self.current is not None)
            source = self.sources.get(d["source"], {})
            self.source_label.setText(source.get("name") or d["source"])
            self.show_excerpt()
        else:
            self.view.band, self.view.frame, self.view.others = None, None, []
            self.hint.setText("")
            self.show_source(None, 1)
        self.fill_commands()
        self.loading = False

    def fill_status(self):
        """Each excerpt of the source, found again or not -- what «Remplacer le PDF…» has to say, and the source's card keeps saying."""
        while self.status_layout.count():
            widget = self.status_layout.takeAt(0).widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        pdf = self.pdf_of(self.current) if self.current else None
        mine = {eid: e for eid, e in self.excerpts.items() if e["source"] == self.current}
        for eid, excerpt in mine.items():
            where = model.resolve(excerpt, pdf.reader, pdf.sha, pdf.marks) if pdf else None
            if where is not None and where["ok"]:
                text = (self.t("ax_found", id=eid, page=where["page"], title=where["title"]) if where["title"]
                        else self.t("ax_found_page", id=eid, page=where["page"]))
                colour = None
            else:
                text = self.app.note_text(where["note"]) if where else self.t("warn_annex_pdf_missing", source=self.current)
                colour = theme.colour("danger")
            label = plain_label(text, wrap=True)
            if colour:
                label.setStyleSheet(f"color: {colour};")
            self.status_layout.addWidget(label)
        self.status_card.setVisible(bool(mine))

    def excerpt_state(self):
        """(ok, text, page, down) of the draft against its source's current version."""
        d = self.draft
        pdf = self.pdf_of(d["source"])
        if pdf is None:
            return False, self.t("warn_annex_pdf_missing", source=d["source"]), 1, None
        if not d.get("anchor"):
            return False, self.t("ax_missing_anchor"), self.view.page if self.view.doc is pdf else 1, None
        down = self.anchor_down(pdf)
        if d.get("frame") is None:
            page = d["anchor"].get("page") or (self.anchor_mark(pdf) or {}).get("page", 1)
            return False, self.t("ax_missing_frame"), page, down
        where = model.resolve(dict(d, id=d.get("id") or "?"), pdf.reader, pdf.sha, pdf.marks)
        if where["ok"]:
            return True, self.t("ax_state_ok", page=where["page"]), where["page"], where["down"]
        return False, self.app.note_text(where["note"]), where["page"] or 1, down

    def anchor_mark(self, pdf):
        anchor = (self.draft or {}).get("anchor") or {}
        if anchor.get("kind") != "bookmark":
            return None
        same = model.candidates(pdf.marks, [model.title_key(t) for t in anchor["path"]])
        occurrence = anchor.get("occurrence", 1)
        return same[occurrence - 1] if 0 < occurrence <= len(same) else None

    def anchor_down(self, pdf):
        anchor = (self.draft or {}).get("anchor") or {}
        if anchor.get("kind") == "page":
            return 0.0
        mark = self.anchor_mark(pdf)
        return None if mark is None else mark["top"]

    def show_excerpt(self):
        d = self.draft
        pdf = self.pdf_of(d["source"])
        anchor = d.get("anchor") or {}
        if anchor.get("kind") == "bookmark":
            self.title_label.setText(anchor["path"][-1])
            same = model.candidates(pdf.marks, [model.title_key(t) for t in anchor["path"]]) if pdf else []
            multiple = len([m for m in (pdf.marks if pdf else []) if m["key"] == model.title_key(anchor["path"][-1])]) > 1
            self.occurrence_label.setText(self.t("ax_occurrence", count=max(len(same), 1), occurrence=anchor.get("occurrence", 1)) if multiple else "")
            self.occurrence_label.setVisible(multiple)
        elif anchor.get("kind") == "page":
            self.title_label.setText(self.t("ax_title_page", page=anchor["page"]))
            self.occurrence_label.setVisible(False)
        else:
            self.title_label.setText(self.t("ax_title_none"))
            self.occurrence_label.setVisible(False)
        frame = d.get("frame")
        self.frame_label.setText(self.t("ax_frame_value", w=round(frame["w"]), h=round(frame["h"]), x=round(frame["x"])) if frame else self.t("ax_frame_none"))
        ok, text, page, down = self.excerpt_state()
        self.state_label.setText(text)
        self.state_label.setStyleSheet("" if ok else f"color: {theme.colour('danger')};")
        self.confirm_button.setVisible(anchor.get("kind") == "page" and pdf is not None and d.get("confirmed") != pdf.sha)
        if pdf is not None and (pdf is not self.view.doc or self.view.page != page):
            self.show_source(d["source"], page)
        self.view.band = down if anchor.get("kind") == "bookmark" else None
        self.view.frame = None
        if frame is not None and down is not None:
            self.view.frame = [frame["x"], down + frame["y"], frame["w"], frame["h"]]
        self.view.others = self.other_frames(pdf)
        self.view.update()
        self.select_mark(pdf)
        if pdf is None or not pdf.marks:
            self.hint.setText(self.t("ax_step_page"))
        elif not anchor:
            self.hint.setText(self.t("ax_step_title"))
        elif not frame:
            self.hint.setText(self.t("ax_step_frame"))
        else:
            self.hint.setText(self.t("ax_step_done"))
        self.update_preview(ok, page)

    def other_frames(self, pdf):
        """The frames of the source's other excerpts on the page shown, dashed, so a new one is drawn beside them."""
        if pdf is None or self.draft is None:
            return []
        found = []
        for eid, excerpt in self.excerpts.items():
            if eid == self.current or excerpt["source"] != self.draft["source"]:
                continue
            where = model.resolve(excerpt, pdf.reader, pdf.sha, pdf.marks)
            if where["ok"]:
                found.append((where["page"], where["rect"]))   # on every page, all of them in view at once since issue #16
        return found

    def update_preview(self, ok, page):
        """The region the report will print, cut out of the page as the export crops it."""
        rect = self.view.frame
        pdf = self.pdf_of(self.draft["source"]) if self.draft else None
        if not ok or rect is None or pdf is None:
            self.preview.clear()
            return
        w_pt, _h = pdf.sizes[page - 1]
        width = 1200
        s = width / w_pt
        image = pdf.render(page, width)
        x, y, w, h = rect
        cut = image.copy(int(x * s), int(y * s), max(1, int(w * s)), max(1, int(h * s)))
        from PySide6.QtGui import QPixmap
        ratio = self.devicePixelRatioF()
        pix = QPixmap.fromImage(cut.scaledToWidth(round(360 * ratio), Qt.TransformationMode.SmoothTransformation))
        pix.setDevicePixelRatio(ratio)
        self.preview.setPixmap(pix)

    def fill_commands(self):
        while self.calls_layout.count():
            item = self.calls_layout.takeAt(0)
            if item.layout() is not None:
                while item.layout().count():
                    widget = item.layout().takeAt(0).widget()
                    if widget is not None:
                        widget.hide()
                        widget.setParent(None)
                        widget.deleteLater()
            elif item.widget() is not None:
                item.widget().hide()
                item.widget().setParent(None)
                item.widget().deleteLater()
        calls = []
        if self.kind == EXCERPTS and self.draft and self.draft.get("id"):
            calls += [ref.call_show_extract(self.draft["id"]), ref.call_show_extract(self.draft["id"], width="60%")]
        calls += [ref.call_extract_loop(), ref.call_show_annexes(), ref.import_line()]
        for text in calls:
            row = QHBoxLayout()
            row.addWidget(richtext.CodeField(text, self.app.mono_font), 1)
            row.addWidget(richtext.copy_button(self.app.t("copy"), self.app.t("copied_short"), lambda t=text: self.app.copy(t)))
            self.calls_layout.addLayout(row)

    # -- the page ------------------------------------------------------------------------

    def show_source(self, sid, page):
        pdf = self.pdf_of(sid) if sid else None
        self.marks.clear()
        if pdf is None:
            self.view.show_page(None, 1)
            self.page_spin.setRange(1, 1)
            self.page_total.setText("")
            return
        self.fill_marks(pdf)
        loading, self.loading = self.loading, True
        self.page_spin.setRange(1, pdf.pages())
        self.page_spin.setValue(max(1, min(page, pdf.pages())))
        for spin in (self.from_spin, self.to_spin):
            spin.setRange(1, pdf.pages())
        self.loading = loading
        self.page_total.setText(f"/ {pdf.pages()}")
        self.view.show_page(pdf, self.page_spin.value())
        if self.mode == "found":
            self.find_frames(self.view.page)

    def fill_marks(self, pdf):
        """The source's bookmarks as its own program's navigator shows them."""
        parents = {}
        for mark in pdf.marks:
            depth = len(mark["path"]) - 1
            item = QTreeWidgetItem([mark["title"]])
            item.setData(0, Qt.ItemDataRole.UserRole, pdf.marks.index(mark))
            item.setToolTip(0, f"{self.t('ax_page')} {mark['page']}")
            parent = parents.get(depth - 1)
            if parent is None:
                self.marks.addTopLevelItem(item)
            else:
                parent.addChild(item)
            parents[depth] = item
            for deeper in [k for k in parents if k > depth]:
                del parents[deeper]
        self.marks.expandAll()

    def select_mark(self, pdf):
        """The excerpt's own bookmark selected in the list, and brought into view."""
        mark = self.anchor_mark(pdf) if pdf is not None else None
        if mark is None:
            self.marks.clearSelection()
            return
        wanted = pdf.marks.index(mark)
        found = [item for item in self._mark_items() if item.data(0, Qt.ItemDataRole.UserRole) == wanted]
        if found:
            self.marks.setCurrentItem(found[0])
            self.marks.scrollToItem(found[0])

    def _mark_items(self):
        stack = [self.marks.topLevelItem(i) for i in range(self.marks.topLevelItemCount())]
        while stack:
            item = stack.pop()
            yield item
            stack.extend(item.child(i) for i in range(item.childCount()))

    def go_to(self, page):
        if self.loading or self.view.doc is None:
            return
        self.view.show_page(self.view.doc, page)
        if self.kind == EXCERPTS and self.draft is not None:
            pdf = self.view.doc
            self.view.others = self.other_frames(pdf)
            anchor = self.draft.get("anchor") or {}
            shown = anchor.get("kind") == "page" and anchor.get("page") == page
            mark = self.anchor_mark(pdf)
            if mark is not None and mark["page"] != page:
                self.view.band, self.view.frame = None, None
            elif anchor.get("kind") == "page" and not shown:
                self.view.frame = None
            self.view.update()

    def on_mark_clicked(self, item, _column=0):
        if self.kind != EXCERPTS or self.draft is None:
            pdf = self.view.doc
            if pdf is not None:
                mark = pdf.marks[item.data(0, Qt.ItemDataRole.UserRole)]
                self.page_spin.setValue(mark["page"])
            return
        pdf = self.pdf_of(self.draft["source"])
        mark = pdf.marks[item.data(0, Qt.ItemDataRole.UserRole)]
        self.take_mark(pdf, mark)

    def take_mark(self, pdf, mark):
        """A title chosen: the excerpt anchored on its bookmark. A frame already drawn keeps its place on the page, re-measured from the new title."""
        old_down = self.anchor_down(pdf)
        frame = self.draft.get("frame")
        anchor = model.anchor_for(pdf.marks, mark)
        if frame is not None and old_down is not None and self.anchor_mark(pdf) is not None and self.anchor_mark(pdf)["page"] == mark["page"]:
            frame = dict(frame, y=round(old_down + frame["y"] - mark["top"], 2))
        elif frame is not None:
            frame = None
        self.draft["anchor"] = anchor
        self.draft["frame"] = frame
        self.draft.pop("confirmed", None)
        self.touched()

    def on_page_chosen(self, page):
        """A press on another page than the one in focus: the page number follows it, and the frames found are looked for there."""
        loading, self.loading = self.loading, True
        self.page_spin.setValue(page)
        self.loading = loading
        if self.mode == "found":
            self.find_frames(page)

    def view_page_in_middle(self):
        anchor = self.view.anchor()
        return anchor[0] if anchor else self.view.page

    def shown_source(self):
        """The source whose pages are shown: the excerpt's, or the source selected."""
        if self.kind == EXCERPTS and self.draft is not None:
            return self.draft.get("source")
        if self.kind == SOURCES:
            return self.current
        return None

    def find_frames(self, page):
        """The frames of `page` and of the pages beside it looked for, once each per version of the source (annex.find_rects, off the window's thread)."""
        pdf = self.view.doc
        if pdf is None or self.mode != "found":
            return
        for p in (page, page - 1, page + 1):
            if 1 <= p <= pdf.pages() and p not in self.view.found and (pdf.sha, p) not in self.asked:
                self.asked.add((pdf.sha, p))
                self.finder.ask(pdf.data, pdf.sha, p)
                if p == page:
                    self.hint.setText(self.t("ax_found_searching", page=page))

    def on_found(self, sha, page, rects):
        self.asked.discard((sha, page))
        pdf = self.view.doc
        if pdf is None or pdf.sha != sha:
            return
        self.view.found[page] = rects
        if page == self.view.page and self.mode == "found":
            self.hint.setText(self.t("ax_found_pick") if rects else self.t("ax_found_none"))
        self.view.update()

    def on_page_click(self, x, down):
        if self.mode == "found":
            rect = self.view.hovered_rect() if self.view.hover and self.view.hover[0] == self.view.page else None
            if rect is not None:
                self.extract_annex_rects([(self.view.page, rect)])
            return
        if self.mode == "pages":
            for spin in (self.from_spin, self.to_spin):
                spin.setValue(self.view.page)   # a click on a page starts the range there
            return
        if self.kind != EXCERPTS or self.draft is None:
            return
        pdf = self.pdf_of(self.draft["source"])
        if pdf is None or not pdf.marks:
            return
        mark = model.bookmark_at(pdf.marks, self.view.page, down)
        if mark is None:
            self.app.set_status(self.t("ax_click_no_title"))
            return
        self.take_mark(pdf, mark)

    def on_page_drag(self, x, down, w, h):
        if self.mode != "frame":
            return
        if w < model.MIN_FRAME or h < model.MIN_FRAME:
            self.app.set_status(self.t("ax_frame_small", min=int(model.MIN_FRAME)))
            return
        # «Cadre» (D-012): every frame drawn is an excerpt of its own -- unless the excerpt being made by «Nouvel extrait…» waits for its frame, or Shift redraws the frame of the excerpt selected
        reframe = self.kind == EXCERPTS and self.draft is not None and (self.current is None or self.view.modifiers & Qt.KeyboardModifier.ShiftModifier)
        if not reframe:
            self.extract_annex_rects([(self.view.page, [x, down, w, h])])
            return
        pdf = self.pdf_of(self.draft["source"])
        if pdf is None:
            return
        if pdf.marks:
            mark = self.anchor_mark(pdf)
            if mark is None or mark["page"] != self.view.page:
                # a frame drawn before any title, or on another page than its title: the title of this page closest above the frame is taken
                mark = model.bookmark_at(pdf.marks, self.view.page, down + 1.0)
                if mark is None:
                    self.app.set_status(self.t("ax_click_no_title"))
                    return
                self.draft["anchor"] = model.anchor_for(pdf.marks, mark)
            anchor_down = mark["top"]
        else:
            self.draft["anchor"] = {"kind": "page", "page": self.view.page}
            self.draft["confirmed"] = pdf.sha
            anchor_down = 0.0
        self.draft["frame"] = {"x": round(x, 2), "y": round(down - anchor_down, 2), "w": round(w, 2), "h": round(h, 2)}
        self.touched()

    def extract_annex_pages(self):
        """«Extraire les pages» (issue #16): every page of the range an excerpt of its own, the page whole, anchored on its page."""
        sid = self.shown_source()
        pdf = self.pdf_of(sid) if sid else None
        if pdf is None:
            return False
        first, last = sorted((self.from_spin.value(), self.to_spin.value()))
        return self.write_extracted(sid, [model.page_excerpt(pdf.reader, page, pdf.sha) for page in range(first, last + 1)])

    def extract_annex_rects(self, rects):
        """Excerpts of `rects`, [(page, [x, down, w, h])], each anchored on the title above it, or on its page (annex.frame_excerpt)."""
        sid = self.shown_source()
        pdf = self.pdf_of(sid) if sid else None
        if pdf is None:
            return False
        return self.write_extracted(sid, [model.frame_excerpt(pdf.marks, page, rect, pdf.sha) for page, rect in rects])

    def write_extracted(self, sid, parts):
        """`parts` -- each an anchor, a frame, and where it needs one the version it was confirmed on -- written as excerpts of the source `sid`, named after their title or their page, with ids no other excerpt has, the batch's own included. Every one is checked before any is written, and the annexes exported once (review ARCH-RISK-007): a range of thirty pages is one export, never thirty."""
        if not parts or not self.confirm_leave():
            return False
        pdf = self.pdf_of(sid)
        here = self.here()
        taken, made = set(self.excerpts), []
        try:
            for part in parts:
                name = model.excerpt_name(pdf.marks, part, self.t("ax_page_short"))
                eid = model.free_id(f"{sid}-{name}", taken)
                taken.add(eid)
                excerpt = dict({"schema_version": model.EXCERPT_SCHEMA_VERSION, "id": eid, "name": name, "label": "", "source": sid}, **part)
                model.check_excerpt(excerpt, f"{eid}.json")
                made.append(excerpt)
            for excerpt in made:
                model.write_excerpt(here, excerpt)
            self.export()
        except (OSError, validation.ValidationError) as exc:
            return self.fail(self.t("ax_refused", error=exc))
        self.dirty = False
        self.load(EXCERPTS, made[-1]["id"])
        ids = ", ".join(e["id"] for e in made)
        self.app.set_status(self.t("ax_extracted", count=len(made), ids=ids))
        return True

    def confirm(self):
        """A page anchor confirmed on its source's current version."""
        if self.kind != EXCERPTS or self.draft is None:
            return
        pdf = self.pdf_of(self.draft["source"])
        if pdf is not None:
            self.draft["confirmed"] = pdf.sha
            self.touched()

    def touched(self):
        self.dirty = True
        loading, self.loading = self.loading, True
        self.show_excerpt()
        self.loading = loading
        self.update_list_marker()

    # -- the actions -----------------------------------------------------------------------

    def confirm_leave(self):
        return autosave.confirm(self.app, self, self.t("ax_unsaved_title"), self.t("ax_unsaved", id=(self.draft or {}).get("id") or self.t("ax_new_item")))   # saved without a question where it can be, else the one question (autosave.py, v0.117)

    def fail(self, message):
        return autosave.refuse(self, self.t("ax_refused_title"), message)

    def export(self):
        """The annexes exported alone, as export_all.py exports them -- so the report sees the change without the workbooks being read again. The warnings go to the status line in the window's language."""
        notes = model.export(self.here())
        self.read_all()
        if notes:
            self.app.set_status(" · ".join(self.app.note_text(n) for n in notes))
        return notes

    def unique(self, stem, taken):
        base = identity.slug_id(stem) or "Annexe"
        sid, n = base, 2
        while sid.lower() in {t.lower() for t in taken}:
            sid, n = f"{base}-{n}", n + 1
        return sid

    def add_annex_source(self):
        """«Ajouter un PDF…»: the file copied into the project as a new source, named after it, and exported at once."""
        if not self.confirm_leave():
            return False
        chosen, _filter = QFileDialog.getOpenFileName(self, self.t("ax_pick_pdf"), str(self.here().root), self.t("ax_pdf_filter"))
        if not chosen:
            return False
        path = Path(chosen)
        sid = self.unique(path.stem, self.sources)
        target = model.pdf_path(self.here(), sid)
        try:
            model.reader(path)   # refused here, before anything is copied, where it is not a PDF
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            source = model.new_source(sid, path.stem, "", path.name)
            source["sha256"] = model.file_hash(target)
            model.write_source(self.here(), source)
            self.export()
        except (OSError, validation.ValidationError) as exc:
            return self.fail(self.t("ax_refused", error=exc))
        self.dirty = False
        self.load(SOURCES, sid)
        self.app.set_status(self.t("ax_saved", id=sid))
        return True

    def replace_annex_source(self):
        """«Remplacer le PDF…»: a new version written over the source, after a yes, and every excerpt looked for in it."""
        if self.kind != SOURCES or self.current is None:
            return False
        chosen, _filter = QFileDialog.getOpenFileName(self, self.t("ax_pick_pdf"), str(self.here().root), self.t("ax_pdf_filter"))
        if not chosen:
            return False
        return self.replace_with(Path(chosen))

    def replace_with(self, path, ask=True):
        sid = self.current
        mine = [e for e in self.excerpts.values() if e["source"] == sid]
        name = self.sources[sid].get("name") or sid
        if ask and QMessageBox.question(self, self.t("ax_replace_title"),
                                        self.t("ax_replace_ask", file=path.name, name=name, count=len(mine))) != QMessageBox.StandardButton.Yes:
            return False
        target = model.pdf_path(self.here(), sid)
        try:
            model.reader(path)
            known = self.pdfs.pop(sid, None)
            if known is not None:
                known.close()
            shutil.copyfile(path, target)
            source = dict(self.sources[sid], sha256=model.file_hash(target), original=path.name)
            model.write_source(self.here(), source)
            self.export()
        except (OSError, validation.ValidationError) as exc:
            return self.fail(self.t("ax_refused", error=exc))
        found = sum(1 for e in mine if self.last_export.get("excerpts", {}).get(e["id"], {}).get("resolved"))
        self.dirty = False
        self.load(SOURCES, sid)
        self.app.set_status(self.t("ax_replaced", name=name, found=found, count=len(mine)))
        return True

    def new(self):
        """«Nouvel extrait…»: its source chosen, then its title and its frame on the page."""
        if not self.confirm_leave():
            return False
        if not self.sources:
            notices_ui.tell(self.t("ax_no_source"), notifications.INFO, key="ax_no_source", title_key="ax_pick_source_title", source="annex_tab")
            return False
        ids = list(self.sources)
        if self.kind == SOURCES and self.current in ids:
            sid = self.current
        elif len(ids) == 1:
            sid = ids[0]
        else:
            names = [f"{self.sources[i].get('name') or i} ({i})" for i in ids]
            chosen, ok = QInputDialog.getItem(self, self.t("ax_pick_source_title"), self.t("ax_pick_source"), names, 0, False)
            if not ok:
                return False
            sid = ids[names.index(chosen)]
        self.kind, self.current = EXCERPTS, None
        self.draft = {"schema_version": model.EXCERPT_SCHEMA_VERSION, "id": "", "name": "", "label": "",
                      "source": sid, "anchor": None, "frame": None}
        self.original = None
        self.dirty = True
        self.fill_form()
        self.fill_list()
        return True

    def duplicate(self):
        """An excerpt copied, its frame and title kept -- the start of the next diagram of the same kind."""
        if self.kind != EXCERPTS or self.draft is None or not self.confirm_leave():
            return False
        copy = model.snapshot(self.draft)
        copy.update(id="", name=(copy.get("name") or "") + " 2")
        self.kind, self.current, self.draft, self.original = EXCERPTS, None, copy, None
        self.dirty = True
        self.fill_form()
        self.fill_list()
        return True

    def revert(self):
        if self.current is None:
            self.dirty = False
            self.load_first()
        else:
            self.load(self.kind, self.current)

    def blocking(self):
        """The first reason the form cannot be written, before anything is."""
        d = self.draft
        taken = self.sources if self.kind == SOURCES else self.excerpts
        new_id = d.get("id", "")
        if not model.ID_PATTERN.match(new_id or ""):
            return self.t("ax_id_bad")
        if new_id.lower() != (self.current or "").lower() and new_id.lower() in {k.lower() for k in taken}:
            return self.t("ax_id_taken", id=new_id)
        if self.kind == EXCERPTS:
            if not d.get("anchor"):
                return self.t("ax_missing_anchor")
            if not d.get("frame"):
                return self.t("ax_missing_frame")
        return None

    def save(self):
        """Writes the form -- a source's name, description, ID and mode, or an excerpt -- then exports the annexes. True when written, or when there was nothing to write."""
        if self.kind is None or self.draft is None:
            return True
        self.read_form()
        problem = self.blocking()
        if problem:
            return self.fail(problem)
        if self.current is not None and self.draft == self.original:
            self.dirty = False
            self.update_list_marker()
            return True
        here = self.here()
        new_id = self.draft["id"]
        # a source renamed takes its PDF with it, an excerpt renamed leaves its old file: never without the engineer's own «Enregistrer» (review A02)
        if self.current is not None and new_id != self.current and not autosave.ask_rename(self, self.t("ax_refused_title"), "", ask=False):
            return False
        try:
            if self.kind == SOURCES:
                model.check_source(self.draft, f"{new_id}.json")
                if new_id != self.current:
                    self.rename_source(self.current, new_id)
                model.write_source(here, self.draft)
            else:
                excerpt = {k: v for k, v in self.draft.items() if v is not None}
                model.check_excerpt(excerpt, f"{new_id}.json")
                model.write_excerpt(here, excerpt)
                if self.current is not None and new_id != self.current:
                    (model.excerpts_dir(here) / f"{self.current}.json").unlink(missing_ok=True)
            self.export()
        except (OSError, validation.ValidationError) as exc:
            return self.fail(self.t("ax_refused", error=exc))
        self.dirty = False
        self.load(self.kind, new_id)
        self.app.set_status(self.t("ax_saved", id=new_id))
        return True

    def rename_source(self, old, new):
        """A source renamed: its PDF follows, and so does every excerpt that names it."""
        here = self.here()
        known = self.pdfs.pop(old, None)
        if known is not None:
            known.close()
        model.pdf_path(here, old).rename(model.pdf_path(here, new))
        (model.sources_dir(here) / f"{old}.json").unlink(missing_ok=True)
        for excerpt in self.excerpts.values():
            if excerpt["source"] == old:
                model.write_excerpt(here, dict(excerpt, source=new))

    def delete(self):
        """«Supprimer»: the selected source and its PDF, or the selected excerpt, after a yes. An excerpt never written is simply discarded."""
        if self.kind is None:
            return False
        if self.current is None:
            self.dirty = False
            self.load_first()
            return True
        here = self.here()
        if self.kind == SOURCES:
            source = self.sources.get(self.current, {})
            count = sum(1 for e in self.excerpts.values() if e["source"] == self.current)
            question = self.t("ax_delete_source", name=source.get("name") or self.current, count=count)
        else:
            excerpt = self.excerpts.get(self.current, {})
            question = self.t("ax_delete_excerpt", name=excerpt.get("name") or self.current)
        if QMessageBox.question(self, self.t("ax_delete_title"), question) != QMessageBox.StandardButton.Yes:
            return False
        gone = self.current
        try:
            if self.kind == SOURCES:
                known = self.pdfs.pop(gone, None)
                if known is not None:
                    known.close()
                model.pdf_path(here, gone).unlink(missing_ok=True)
                (model.sources_dir(here) / f"{gone}.json").unlink(missing_ok=True)
            else:
                (model.excerpts_dir(here) / f"{gone}.json").unlink(missing_ok=True)
            self.export()
        except (OSError, validation.ValidationError) as exc:
            return self.fail(self.t("ax_refused", error=exc))
        self.dirty = False
        self.load_first()
        self.app.set_status(self.t("ax_deleted", id=gone))
        return True

    def on_shown(self):
        """Brought to the front: the annexes read again, the form kept where it holds unsaved changes."""
        self.read_all()
        if self.dirty:
            self.fill_list()
        elif self.kind is not None and self.current is not None:
            self.load(self.kind, self.current)
        else:
            self.load_first()

    # -- surviving a rebuild ---------------------------------------------------------------

    def view_state(self):
        return {
            "kind": self.kind, "current": self.current, "dirty": self.dirty,
            "draft": self.draft if self.dirty else None, "page": self.view.page,
            "splitter": self.splitter.sizes(), "viewer": self.viewer_split.sizes(),
        }

    def restore(self, state):
        self.read_all()
        if state and state.get("kind"):
            kind, current, draft = state["kind"], state.get("current"), state.get("draft")
            if current is not None:
                self.load(kind, current)
            else:
                self.load_first()
            if state.get("dirty") and draft:
                self.kind, self.current, self.draft = kind, current, draft
                self.dirty = True
                self.fill_form()
                self.fill_list()
            if state.get("splitter"):
                self.splitter.setSizes(state["splitter"])
                self.sized = True
            if state.get("viewer"):
                self.viewer_split.setSizes(state["viewer"])
        else:
            self.load_first()

    def showEvent(self, event):
        """The first time the tab is shown, the page takes the width: the list as narrow as its folders need, the cards as wide as a form, the rest the page's -- sizes given before the splitter is laid out are rescaled to its minimums, which left the page a fifth of the window."""
        super().showEvent(event)
        if not self.sized and self.splitter.width() > 600:
            self.sized = True
            total = self.splitter.width()
            side, form = 240, max(380, int(total * 0.3))
            self.splitter.setSizes([side, max(300, total - side - form), form])
            inner = self.viewer_split.width() or (total - side - form)
            self.viewer_split.setSizes([int(inner * 0.3), int(inner * 0.7)])
