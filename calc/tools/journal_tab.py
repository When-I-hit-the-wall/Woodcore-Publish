"""Woodcore's «Journal» tab (docs/domain/journal.md §3.3terdecies, docs/ui/window.md §10quater, v0.99): the report's revision journal -- one entry per revision, written by hand, and printed by `#show-journal` as a table, a list or a grid of cards.

The engineer: «avoir un module qui permet d'enregistrer dans un journal les modifications qui ont été faites (date, nom de la personne, nom court de l'entreprise (e.g. FLL), label, description courte, description longue)», and the three levels govern those last three texts alone.

**Every write goes through calc/journal.py**, the one module that reads and writes `Woodcore-Datei/journal.json`: the tab checks what that module would refuse before anything is written -- an index taken, a date that is not a day, an empty name or label -- in the window's language and under the field it concerns. A write is followed by an export of the journal alone (`journal.export`), so `data/journal.json` follows at once and the report sees the entry without the load workbooks being read again: the arrangement every editor tab has (docs/decisions.md §13).

**An entry is written by hand and never appended by anything else** (the engineer's decision): saving a drawing adds nothing here. `Nouvelle entrée` proposes the next index -- the largest plus one, never a number that has been used -- and prefills the name and the short form from the entry before it, which is a convenience and not a setting: a journal may carry entries by several offices.

The list is a flat one, in the journal's own order (newest first): a journal is chronological, so there is no `grouped_list` and no folder here -- and no `identity.py` either, an entry being named by its number and not by an id somebody types.

The tab lives in its own module, which woodcore_gui.py lists in its TABS and whose STRINGS it merges into its own: the keys carry a `jo_` prefix of their own.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox,
    QPlainTextEdit, QPushButton, QSpinBox, QSplitter, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

import build_reference as ref  # the one place a Typst call is spelled out (docs/typst/reference-workbook.md §10ter)
import cards  # the form in cards, after the website (cards.py, v0.93)
import display_view  # the «Affichage» view: the command, its options, the call and the page (display_view.py, v0.117)
import views  # the views the top bar's switch chooses between (views.py, v0.117)
import autosave  # saving without a question, and what is never saved without the engineer (autosave.py, v0.117)
import documents  # what each of the three documents is called (calc/documents.py)
import journal as model  # the one module that reads and writes Woodcore-Datei/journal.json
import project
import richtext  # the calls coloured as the site's code, «Copié ✓» (richtext.py, v0.92)
import theme
import validation

# The list's columns, each with its header's key. The two descriptions are searched and edited, not listed: a column of sentences would leave nothing for the ones that identify a revision.
COLUMNS = (
    ("index", "jo_col_index"), ("date", "jo_col_date"), ("name", "jo_col_name"),
    ("initials", "jo_col_initials"), ("label", "jo_col_label"),
)

# The row that stands for the entry nobody has written yet.
NEW_ROW = -1

STRINGS = {
    "fr": {
        "tab_journal": "Journal",
        "jo_list": "Révisions — {document}",
        "jo_search": "Rechercher…",
        "jo_col_index": "Rev.", "jo_col_date": "Date", "jo_col_name": "Nom",
        "jo_col_initials": "Sigle", "jo_col_label": "Désignation",
        "jo_new": "Nouvelle entrée", "jo_duplicate": "Dupliquer", "jo_delete": "Supprimer",
        "jo_new_item": "(nouvelle, non enregistrée)",
        "jo_form": "Révision",
        "jo_index": "Indice", "jo_date": "Date", "jo_name": "Nom", "jo_initials": "Sigle",
        "jo_label": "Désignation", "jo_summary": "Description courte", "jo_description": "Description longue",
        "jo_index_tip": "Le numéro de la révision, comme un cartouche de révision le numérote. Le plus grand plus un est proposé ; un trou n’est jamais comblé.",
        "jo_date_tip": "Le jour de la révision, aaaa-mm-jj. Il est saisi et non pris à l’horloge : une révision est datée du jour où elle a été décidée.",
        "jo_initials_tip": "Le sigle court du bureau ou de la personne, p. ex. FLL. Repris de l’entrée précédente.",
        "jo_levels": "Niveau de détail 1 : la désignation. 2 : la désignation et la description courte. 3 : tout.",
        "jo_index_taken": "Il y a déjà une révision n° {existing}.",
        "jo_index_low": "Un indice est un nombre entier de 1 ou plus.",
        "jo_date_bad": "Écrire un jour, p. ex. 2026-09-27 (ISO).",
        "jo_name_missing": "Une révision a besoin du nom de la personne qui l’a faite.",
        "jo_initials_missing": "Une révision a besoin du sigle court du bureau.",
        "jo_initials_long": "Un sigle court, au plus {max} caractères — pas le nom complet.",
        "jo_label_missing": "Une révision a besoin d’une désignation : c’est tout ce qu’imprime le niveau 1.",
        "jo_revert": "Annuler les modifications", "jo_save": "Enregistrer",
        "jo_unsaved_title": "Modifications non enregistrées",
        "jo_unsaved": "La révision n° {index} a des modifications non enregistrées.",
        "jo_delete_title": "Supprimer la révision",
        "jo_delete_ask": "Supprimer la révision n° {index} « {label} » du journal ?",
        "jo_saved": "Révision n° {index} enregistrée dans le journal.",
        "jo_deleted": "Révision n° {index} supprimée du journal.",
        "jo_unchanged": "Rien à écrire : la révision est telle que le journal la tient.",
        "jo_refused_title": "Le journal n’a pas été modifié",
        "jo_refused": "Woodcore ne peut pas écrire le journal : {error}",
        "jo_banner_unreadable": "Le journal ne peut pas être lu : {error}",
        "jo_banner_empty": "« {document} » n’a encore aucune révision. « Nouvelle entrée » en ajoute une.",
    },
    "de": {
        "tab_journal": "Journal",
        "jo_list": "Revisionen — {document}",
        "jo_search": "Suchen…",
        "jo_col_index": "Rev.", "jo_col_date": "Datum", "jo_col_name": "Name",
        "jo_col_initials": "Kürzel", "jo_col_label": "Bezeichnung",
        "jo_new": "Neuer Eintrag", "jo_duplicate": "Duplizieren", "jo_delete": "Löschen",
        "jo_new_item": "(neu, nicht gespeichert)",
        "jo_form": "Revision",
        "jo_index": "Index", "jo_date": "Datum", "jo_name": "Name", "jo_initials": "Kürzel",
        "jo_label": "Bezeichnung", "jo_summary": "Kurzbeschreibung", "jo_description": "Lange Beschreibung",
        "jo_index_tip": "Die Nummer der Revision, wie ein Revisionsstempel sie nummeriert. Vorgeschlagen wird die grösste plus eins; eine Lücke wird nie aufgefüllt.",
        "jo_date_tip": "Der Tag der Revision, jjjj-mm-tt. Er wird getippt und nicht der Uhr entnommen: eine Revision trägt den Tag, an dem sie beschlossen wurde.",
        "jo_initials_tip": "Das Kürzel des Büros oder der Person, z. B. FLL. Aus dem vorherigen Eintrag übernommen.",
        "jo_levels": "Detailstufe 1: die Bezeichnung. 2: die Bezeichnung und die Kurzbeschreibung. 3: alles.",
        "jo_index_taken": "Es gibt schon eine Revision Nr. {existing}.",
        "jo_index_low": "Ein Index ist eine ganze Zahl von 1 oder mehr.",
        "jo_date_bad": "Einen Tag schreiben, z. B. 2026-09-27 (ISO).",
        "jo_name_missing": "Eine Revision braucht den Namen der Person, die sie gemacht hat.",
        "jo_initials_missing": "Eine Revision braucht das Kürzel des Büros.",
        "jo_initials_long": "Ein kurzes Kürzel, höchstens {max} Zeichen – nicht der ganze Name.",
        "jo_label_missing": "Eine Revision braucht eine Bezeichnung: sie ist alles, was Stufe 1 druckt.",
        "jo_revert": "Änderungen verwerfen", "jo_save": "Speichern",
        "jo_unsaved_title": "Nicht gespeicherte Änderungen",
        "jo_unsaved": "Die Revision Nr. {index} hat nicht gespeicherte Änderungen.",
        "jo_delete_title": "Revision löschen",
        "jo_delete_ask": "Die Revision Nr. {index} «{label}» aus dem Journal löschen?",
        "jo_saved": "Revision Nr. {index} im Journal gespeichert.",
        "jo_deleted": "Revision Nr. {index} aus dem Journal gelöscht.",
        "jo_unchanged": "Nichts zu schreiben: die Revision steht so im Journal.",
        "jo_refused_title": "Das Journal wurde nicht geändert",
        "jo_refused": "Woodcore kann das Journal nicht schreiben: {error}",
        "jo_banner_unreadable": "Das Journal lässt sich nicht lesen: {error}",
        "jo_banner_empty": "«{document}» hat noch keine Revision. «Neuer Eintrag» fügt eine hinzu.",
    },
    "en": {
        "tab_journal": "Journal",
        "jo_list": "Revisions — {document}",
        "jo_search": "Search…",
        "jo_col_index": "Rev.", "jo_col_date": "Date", "jo_col_name": "Name",
        "jo_col_initials": "Initials", "jo_col_label": "Designation",
        "jo_new": "New entry", "jo_duplicate": "Duplicate", "jo_delete": "Delete",
        "jo_new_item": "(new, not saved)",
        "jo_form": "Revision",
        "jo_index": "Index", "jo_date": "Date", "jo_name": "Name", "jo_initials": "Initials",
        "jo_label": "Designation", "jo_summary": "Short description", "jo_description": "Long description",
        "jo_index_tip": "The revision's number, as a revision block numbers one. The largest plus one is proposed; a gap is never refilled.",
        "jo_date_tip": "The day of the revision, yyyy-mm-dd. It is typed and not taken from the clock: a revision is dated by the day it was decided.",
        "jo_initials_tip": "The short form of the office or of the person, e.g. FLL. Taken from the entry before it.",
        "jo_levels": "Level of detail 1: the designation. 2: the designation and the short description. 3: everything.",
        "jo_index_taken": "There is a revision no. {existing} already.",
        "jo_index_low": "An index is a whole number of 1 or more.",
        "jo_date_bad": "Write a day, e.g. 2026-09-27 (ISO).",
        "jo_name_missing": "A revision needs the name of whoever made it.",
        "jo_initials_missing": "A revision needs the office's short form.",
        "jo_initials_long": "A short form, at most {max} characters — not the whole name.",
        "jo_label_missing": "A revision needs a designation: it is all that level 1 prints.",
        "jo_revert": "Revert changes", "jo_save": "Save",
        "jo_unsaved_title": "Unsaved changes",
        "jo_unsaved": "Revision no. {index} has unsaved changes.",
        "jo_delete_title": "Delete the revision",
        "jo_delete_ask": "Delete revision no. {index} «{label}» from the journal?",
        "jo_saved": "Revision no. {index} saved in the journal.",
        "jo_deleted": "Revision no. {index} deleted from the journal.",
        "jo_unchanged": "Nothing to write: the revision is as the journal holds it.",
        "jo_refused_title": "The journal was not changed",
        "jo_refused": "Woodcore cannot write the journal: {error}",
        "jo_banner_unreadable": "The journal cannot be read: {error}",
        "jo_banner_empty": "«{document}» has no revision yet. «New entry» adds one.",
    },
}


def document_mode(app):
    """The document whose journal the tab edits: the window's (`current_document`, the one its navigation shows), the report where the window names none -- one built without a project in three documents, a test's."""
    current = getattr(app, "current_document", None)
    if callable(current):
        return current()
    mode = getattr(app, "mode", "rs")
    return mode if mode in project.current().modes else "rs"


def plain_label(text="", wrap=False):
    """A label that is never read as HTML -- a description is the engineer's text and may hold anything."""
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(wrap)
    return label


class JournalList(QTreeWidget):
    """The revisions, one flat row each, newest first -- the entry not written yet as a row of its own. Flat and not grouped: a journal is chronological, so there is no folder to file one in (grouped_list.py is for the editors whose sources are named objects)."""

    INDEX_ROLE = Qt.ItemDataRole.UserRole

    def rows(self):
        return [(self.topLevelItem(i), self.topLevelItem(i).data(0, self.INDEX_ROLE)) for i in range(self.topLevelItemCount())]

    def indices(self):
        return [index for _item, index in self.rows()]

    def item_of(self, index):
        return next((item for item, key in self.rows() if key == index), None)


class JournalTab(display_view.DisplayTab, QWidget):
    """Lists the report's revisions, edits one at a time, and writes the journal back through calc/journal.py."""

    VIEWS = views.ENTRY_VIEWS   # «Saisie» and «Affichage» (views.py, v0.117)

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.t = app.t
        self.loading = False    # set while the form is filled, so filling it is not taken for an edit
        self.dirty = False
        self.current = None     # the index of the revision the form holds; None for one not written yet
        self.original = None    # that entry as the journal held it, what a save compares with
        self.source = model.blank()
        self.error = None       # why the journal could not be read, where it could not

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.build_list())
        self.splitter.addWidget(self.build_form())
        self.install_display("tab_journal", centre=1, right=None)   # «Affichage»: show-journal's options, the call and the page of the document's journal (v0.117)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        layout.addWidget(self.splitter, 1)
        shortcut = QShortcut(QKeySequence(QKeySequence.StandardKey.Save), self)   # Ctrl+S, as in every editor tab
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.activated.connect(self.save)
        self.restore(app.views.get("tab_journal"))

    # -- building ---------------------------------------------------------------------

    def heading(self, text):
        label = plain_label(text)
        label.setFont(self.app.bold_font)
        return label

    def note(self):
        """A line under a field, saying why it cannot be written: empty and hidden until then."""
        label = plain_label("", wrap=True)
        label.setVisible(False)
        return label

    def build_list(self):
        panel = QWidget()
        box = QVBoxLayout(panel)
        box.setContentsMargins(0, 0, 6, 0)
        self.title = self.heading(self.t("jo_list", document=self.document_name()))   # the document whose journal this is, which changes with the navigation's drop-down (on_mode)
        box.addWidget(self.title)
        self.search = QLineEdit()
        self.search.setPlaceholderText(self.t("jo_search"))
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.apply_search)
        box.addWidget(self.search)
        self.list = JournalList()
        self.list.setColumnCount(len(COLUMNS))
        self.list.setHeaderLabels([self.t(key) for _field, key in COLUMNS])
        self.list.setRootIsDecorated(False)
        self.list.setUniformRowHeights(True)
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list.setIconSize(self.app.mark_size)
        self.list.header().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.list.header().setStretchLastSection(True)
        self.list.currentItemChanged.connect(self.on_list_change)
        box.addWidget(self.list, 1)
        row = QHBoxLayout()
        for key, slot in (("jo_new", self.new), ("jo_duplicate", self.duplicate), ("jo_delete", self.delete)):
            button = QPushButton(self.t(key))
            button.clicked.connect(slot)
            row.addWidget(button)
        row.addStretch(1)
        box.addLayout(row)
        return panel

    def build_form(self):
        outer = QWidget()
        shell = QVBoxLayout(outer)
        shell.setContentsMargins(6, 0, 0, 0)
        area, box = cards.column()
        self.banner = plain_label("", wrap=True)
        self.banner.setVisible(False)
        box.addWidget(self.banner)

        group = cards.card(self.t("jo_form"))
        form = cards.form(group)
        self.captions = {}
        self.index_edit = QSpinBox()
        self.index_edit.setRange(1, 9999)
        self.index_edit.setToolTip(self.t("jo_index_tip"))
        self.index_edit.valueChanged.connect(self.changed)
        self.index_note = self.note()
        self.add_row(form, "jo_index", self.index_edit, self.index_note)
        self.date_edit = QLineEdit()
        self.date_edit.setPlaceholderText("2026-09-27")
        self.date_edit.setToolTip(self.t("jo_date_tip"))
        self.date_edit.textEdited.connect(self.changed)
        self.date_note = self.note()
        self.add_row(form, "jo_date", self.date_edit, self.date_note)
        self.name_edit = QLineEdit()
        self.name_edit.textEdited.connect(self.changed)
        self.name_note = self.note()
        self.add_row(form, "jo_name", self.name_edit, self.name_note)
        self.initials_edit = QLineEdit()
        self.initials_edit.setMaxLength(model.INITIALS_MAX)
        self.initials_edit.setToolTip(self.t("jo_initials_tip"))
        self.initials_edit.textEdited.connect(self.changed)
        self.initials_note = self.note()
        self.add_row(form, "jo_initials", self.initials_edit, self.initials_note)
        self.label_edit = QLineEdit()
        self.label_edit.textEdited.connect(self.changed)
        self.label_note = self.note()
        self.add_row(form, "jo_label", self.label_edit, self.label_note)
        self.summary_edit = self.text_box(3)
        self.add_row(form, "jo_summary", self.summary_edit)
        self.description_edit = self.text_box(6)
        self.add_row(form, "jo_description", self.description_edit)
        group_note = cards.note(self.t("jo_levels"))
        form.addRow(group_note)
        box.addWidget(group)

        box.addStretch(1)
        shell.addWidget(area, 1)

        actions = QHBoxLayout()
        actions.addStretch(1)
        revert = QPushButton(self.t("jo_revert"))
        revert.clicked.connect(self.revert)
        actions.addWidget(revert)
        save = QPushButton(self.t("jo_save"))
        save.setDefault(True)
        save.clicked.connect(self.save)
        actions.addWidget(save)
        shell.addLayout(actions)
        return outer

    def text_box(self, lines):
        box = QPlainTextEdit()
        box.setTabChangesFocus(True)
        box.setMinimumHeight(2 * self.fontMetrics().height() + 12)
        box.setMaximumHeight(lines * self.fontMetrics().height() + 12)
        box.textChanged.connect(self.changed)
        return box

    def add_row(self, form, key, widget, note=None):
        caption = QLabel(self.t(key))
        if note is None:
            form.addRow(caption, widget)
        else:
            cell = QWidget()
            column = QVBoxLayout(cell)
            column.setContentsMargins(0, 0, 0, 0)
            column.setSpacing(2)
            column.addWidget(widget)
            column.addWidget(note)
            form.addRow(caption, cell)
        self.captions[key] = caption

    def display_entries(self):
        """What prints the journal of the document shown (v0.117, «Affichage»): `show-journal` -- its form, its level, its title -- compiled as that document, and the entries read into a variable for a section that sets them its own way, which prints nothing; `document:` the window's own document, which the call copied did not say until v0.117. A journal takes no id: there is one per document."""
        return [
            display_view.Entry("journal", "show-journal", "show-journal"),
            display_view.Entry("entries", "journal-entries", "journal-entries", preset={"document": self.mode()},
                               call_fn=lambda o: ref.call_journal_entries(o.get("document")), note="ds_note_prints_nothing"),
        ]

    # -- the journal ---------------------------------------------------------------------

    def mode(self):
        return document_mode(self.app)

    def document_name(self):
        return documents.mode_name(self.mode(), getattr(self.app, "lang", documents.DEFAULT_LANGUAGE))

    def file(self):
        """The journal of the document shown: each of the three documents prints its own «Historique des versions» (the engineer's decision), the report's being `journal.json` as it has been since v0.99 (`Project.journal_file_for`)."""
        return project.current().journal_file_for(self.mode())

    def on_mode(self, _mode):
        """Another document shown in the window: its own journal read and listed, its name in the heading. What the form held unsaved was asked about before (the window's `on_mode_changed`, this tab being one of MODE_BOUND), so nothing here is lost."""
        self.title.setText(self.t("jo_list", document=self.document_name()))
        self.dirty = False
        self.current = None
        self.read_journal()
        self.load_first()
        self.update_display()   # «Affichage» compiles the journal of the document now shown

    def read_journal(self):
        """The journal read afresh, and the banner saying what cannot be done with it. Never raises: one that cannot be read is said, and lists nothing."""
        self.error = None
        try:
            self.source = model.read(self.file())
        except validation.ValidationError as exc:
            self.source, self.error = model.blank(), exc
        self.update_banner()

    def update_banner(self):
        kind, text = None, ""
        if self.error is not None:
            kind, text = "danger", self.t("jo_banner_unreadable", error=self.error)
        elif not self.source["entries"]:
            kind, text = "info", self.t("jo_banner_empty", document=self.document_name())
        self.banner.setText(text)
        self.banner.setProperty("callout", kind or "info")
        self.banner.style().unpolish(self.banner)
        self.banner.style().polish(self.banner)
        self.banner.setVisible(bool(text))

    def entries(self):
        """The journal's entries, newest first -- the order the report prints them in and the order the list shows."""
        return model.entries(self.source)

    def entry_of(self, index):
        return next((e for e in self.source["entries"] if e.get("index") == index), None)

    def indices(self):
        return [e["index"] for e in self.source["entries"]]

    # -- the list ------------------------------------------------------------------------

    def fill_list(self, select=None):
        loading, self.loading = self.loading, True
        self.list.clear()
        for entry in self.entries():
            values = self.entry_values(entry)
            item = QTreeWidgetItem([str(values[field]) for field, _key in COLUMNS])
            item.setData(0, JournalList.INDEX_ROLE, entry["index"])
            item.setToolTip(0, values["summary"] or values["description"])
            item.setIcon(0, self.app.dirty_mark(False))   # its mark's room, whether it carries the dot or the blank
            self.list.addTopLevelItem(item)
        if self.current is None:    # the entry not written yet, where it can be seen
            item = QTreeWidgetItem([self.t("jo_new_item")] + [""] * (len(COLUMNS) - 1))
            item.setData(0, JournalList.INDEX_ROLE, NEW_ROW)
            item.setIcon(0, self.app.dirty_mark(False))
            self.list.addTopLevelItem(item)
            item.setFirstColumnSpanned(True)
        for column in range(len(COLUMNS) - 1):
            self.list.resizeColumnToContents(column)
        target = select if select is not None else (self.current if self.current is not None else NEW_ROW)
        item = self.list.item_of(target)
        if item is not None:
            self.list.setCurrentItem(item)
        self.apply_search()
        self.loading = loading
        self.update_list_marker()

    def apply_search(self, _text=None):
        words = self.search.text().strip().lower().split()
        for item, index in self.list.rows():
            entry = self.entry_of(index) if index != NEW_ROW else None
            text = " ".join(str(v) for v in entry.values()).lower() if entry else ""
            item.setHidden(bool(words) and index != NEW_ROW and not all(word in text for word in words))

    def update_list_marker(self):
        """A dot at the left of the row being edited while it has unsaved changes, and the tab's own; every row carries a mark, dot or blank, so none moves sideways."""
        for item, index in self.list.rows():
            mine = index == self.current or (self.current is None and index == NEW_ROW)
            item.setIcon(0, self.app.dirty_mark(mine and self.dirty))
        self.app.update_tab_marks()

    def on_list_change(self, item, _previous=None):
        if self.loading or item is None:
            return
        index = item.data(0, JournalList.INDEX_ROLE)
        if index == NEW_ROW or index == self.current:
            return
        if not self.confirm_leave():
            self.fill_list()
            return
        self.load(index)

    # -- the form ------------------------------------------------------------------------

    @staticmethod
    def entry_values(entry):
        """One entry as the form holds it: every text a string, the index a number."""
        return {
            "index": entry.get("index", 1),
            "date": str(entry.get("date", "")).strip(),
            "name": str(entry.get("name", "")).strip(),
            "initials": str(entry.get("initials", "")).strip(),
            "label": str(entry.get("label", "")).strip(),
            "summary": str(entry.get("summary", "")).strip(),
            "description": str(entry.get("description", "")).strip(),
        }

    def form_values(self):
        return {
            "index": self.index_edit.value(),
            "date": self.date_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "initials": self.initials_edit.text().strip(),
            "label": self.label_edit.text().strip(),
            "summary": self.summary_edit.toPlainText().strip(),
            "description": self.description_edit.toPlainText().strip(),
        }

    def fill_form(self, values):
        self.loading = True
        self.index_edit.setValue(values.get("index", 1))
        self.date_edit.setText(values.get("date", ""))
        self.name_edit.setText(values.get("name", ""))
        self.initials_edit.setText(values.get("initials", ""))
        self.label_edit.setText(values.get("label", ""))
        self.summary_edit.setPlainText(values.get("summary", ""))
        self.description_edit.setPlainText(values.get("description", ""))
        self.loading = False
        self.update_notes()

    def changed(self, *_args):
        if self.loading:
            return
        self.dirty = True
        self.update_notes()
        self.update_list_marker()

    def update_notes(self):
        values = self.form_values()
        for note, problem in (
            (self.index_note, self.index_problem(values)),
            (self.date_note, self.date_problem(values)),
            (self.name_note, self.t("jo_name_missing") if not values["name"] else ""),
            (self.initials_note, self.initials_problem(values)),
            (self.label_note, self.t("jo_label_missing") if not values["label"] else ""),
        ):
            note.setText(problem)
            note.setStyleSheet("color: %s;" % theme.colour("danger"))
            note.setVisible(bool(problem))

    def index_problem(self, values):
        index = values["index"]
        if index < 1:
            return self.t("jo_index_low")
        for other in self.indices():
            if other == index and other != self.current:
                return self.t("jo_index_taken", existing=other)
        return ""

    def date_problem(self, values):
        return "" if model.parse_date(values["date"]) is not None else self.t("jo_date_bad")

    def initials_problem(self, values):
        if not values["initials"]:
            return self.t("jo_initials_missing")
        if len(values["initials"]) > model.INITIALS_MAX:
            return self.t("jo_initials_long", max=model.INITIALS_MAX)
        return ""

    def blocking(self, values):
        """The first reason the form cannot be written, checked before anything is -- what journal.check_source would refuse, in the window's language and under its own field."""
        for problem in (self.index_problem(values), self.date_problem(values),
                        self.t("jo_name_missing") if not values["name"] else "",
                        self.initials_problem(values),
                        self.t("jo_label_missing") if not values["label"] else ""):
            if problem:
                return problem
        return None

    # -- the revisions -------------------------------------------------------------------

    def load(self, index):
        """The entry of `index` into the form; the newest where the journal no longer has it."""
        entry = self.entry_of(index)
        if entry is None:
            self.load_first()
            return
        self.current, self.original = index, self.entry_values(entry)
        self.dirty = False
        self.fill_form(self.original)
        self.fill_list(select=index)

    def load_first(self):
        listed = self.entries()
        if listed:
            self.load(listed[0]["index"])
        else:
            self.open_draft(dirty=False)

    def open_draft(self, values=None, dirty=True):
        """A revision not written yet in the form: its index the next free one, its name and short form those of the entry before it -- a convenience, not a setting (the engineer's decision 6.4)."""
        self.current, self.original = None, None
        previous = self.entries()
        blank = {
            "index": model.next_index(self.source),
            "date": "",
            # the first revision of a project has nobody before it: the report's own author, as the project file states him
            "name": previous[0]["name"] if previous else project.current().detail("author"),
            "initials": previous[0]["initials"] if previous else "",
            "label": "", "summary": "", "description": "",
        }
        blank.update(values or {})
        self.fill_form(blank)
        self.dirty = dirty
        self.update_notes()
        self.fill_list(select=NEW_ROW)

    def confirm_leave(self):
        """True when the form may be replaced: nothing unsaved, or the engineer saved or discarded it."""
        return autosave.confirm(self.app, self, self.t("jo_unsaved_title"), self.t("jo_unsaved", index=self.index_edit.value()))   # saved without a question where it can be, else the one question (autosave.py, v0.117)

    def new(self):
        if not self.confirm_leave():
            return False
        self.open_draft()
        self.date_edit.setFocus()
        return True

    def duplicate(self):
        """A new revision holding what the form holds, its index proposed afresh."""
        if not self.confirm_leave():
            return
        values = self.form_values()
        values["index"] = model.next_index(self.source)
        self.open_draft(values)

    def revert(self):
        if self.current is None:
            self.dirty = False
            self.load_first()
        else:
            self.load(self.current)

    def on_shown(self):
        """Brought to the front: the journal read again -- it may have been edited elsewhere since -- the form kept where it holds unsaved changes."""
        self.read_journal()
        if self.dirty:
            self.fill_list()
        elif self.current is not None:
            self.load(self.current)
        else:
            self.fill_list()

    # -- writing -------------------------------------------------------------------------

    def fail(self, message):
        return autosave.refuse(self, self.t("jo_refused_title"), message)

    def write(self, entries):
        """The journal written and exported at once, by the very functions export_all.py runs -- so data/journal.json follows and the report sees the entry without the workbooks being read again. Returns False, and says why, where nothing was written."""
        source = dict(self.source, entries=entries)
        try:
            model.check_source(source, self.file().name)
        except validation.ValidationError as exc:
            return self.fail(self.t("jo_refused", error=exc))
        try:
            model.write_source(self.file(), source)
            model.export(self.file(), project.current().data_dir, self.mode())   # into the document's own data/journal[-cu|-bp].json
        except (validation.ValidationError, OSError) as exc:
            return self.fail(self.t("jo_refused", error=exc))
        self.read_journal()
        return True

    def save(self):
        """Writes the form into the journal -- a new revision, or the one being edited. True when written (or when there was nothing to write)."""
        values = self.form_values()
        problem = self.blocking(values)
        if problem:
            return self.fail(problem)
        new = self.current is None
        if not new and values == self.original:
            self.dirty = False
            self.update_list_marker()
            self.app.set_status(self.t("jo_unchanged"))
            return True
        entries = [e for e in self.source["entries"] if e.get("index") != self.current]
        entries.append(model.record(values))
        if not self.write(entries):
            return False
        self.dirty = False
        self.load(values["index"])
        self.app.set_status(self.t("jo_saved", index=values["index"]))
        return True

    def delete(self):
        """«Supprimer»: the revision selected taken out of the journal, after a yes. A revision never written is simply discarded."""
        if self.current is None:
            self.dirty = False
            self.load_first()
            return True
        index = self.current
        entry = self.entry_of(index) or {}
        if QMessageBox.question(self, self.t("jo_delete_title"),
                                self.t("jo_delete_ask", index=index, label=entry.get("label", ""))) != QMessageBox.StandardButton.Yes:
            return False
        listed = [e["index"] for e in self.entries()]
        position = listed.index(index) if index in listed else 0
        if not self.write([e for e in self.source["entries"] if e.get("index") != index]):
            return False
        self.dirty = False
        rest = [e["index"] for e in self.entries()]
        if rest:
            self.load(rest[min(position, len(rest) - 1)])
        else:
            self.open_draft(dirty=False)
        self.app.set_status(self.t("jo_deleted", index=index))
        return True

    # -- surviving a rebuild -------------------------------------------------------------

    def view_state(self):
        return {
            "current": self.current,
            "dirty": self.dirty,
            "draft": self.form_values() if self.dirty or self.current is None else None,
            "search": self.search.text(),
            "splitter": self.splitter.sizes(),
            "columns": [self.list.columnWidth(i) for i in range(len(COLUMNS))],
        }

    def restore(self, state):
        self.read_journal()
        if state:
            self.loading = True
            self.search.setText(state.get("search", ""))
            self.loading = False
            if state.get("columns"):
                for i, width in enumerate(state["columns"]):
                    self.list.setColumnWidth(i, width)
            current, draft = state.get("current"), state.get("draft")
            if current is not None and self.entry_of(current) is not None:
                self.load(current)
                if state.get("dirty") and draft:
                    self.fill_form(draft)
                    self.dirty = True
                    self.update_list_marker()
            elif current is None and draft:
                self.open_draft(draft, dirty=state.get("dirty", False))
            else:
                self.load_first()
            if state.get("splitter"):
                self.splitter.setSizes(state["splitter"])
        else:
            self.splitter.setSizes([6000, 4000])
            self.load_first()
