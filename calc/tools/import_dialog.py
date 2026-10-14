"""The dialogs of the «Structure du document» tab (the engineer's rework of 01.10.2026, work package R2-D1): what a new section or chapter is called, **what to import from another document of the project**, and which version to keep in a conflict.

Each is a dialog of its own with the answer in a method (`values`, `chosen`), so that the tab asks it through one method (`ask_import`, `ask_choice`, `ask_section`, `ask_group`, `ask_template`) a test replaces: a modal off-screen never comes back. They read what they need from calc/doc_import.py and know nothing else of the project -- the tab hands over the words (`t`) and the project, and writes what the dialog says.

**«Importer depuis un autre document du projet»** (`ImportDialog`): a combo box of the other documents -- the convention d'utilisation, the base de projet and the report, as `doc_import.other_documents` offers them, chosen **dynamically**: the tree of its chapters, sections and objects under it is made again whenever another is chosen -- and a check box on every row. Ticking a chapter ticks everything under it, ticking a section its objects, and a section **ticked whole is imported whole** where one with only some of its objects ticked imports those objects alone (`values`): the rule calc/doc_import.py states, that a section and some of its objects together is the section. «Copie indépendante» is a box of its own, unticked: **what is imported stays linked** to its source (shared) unless it is ticked.

**«Partager avec…»** (`ShareDialog`): the other documents of the project, a check box on each -- one the section is shared with already is shown ticked and closed, saying so --, and what it answers is the modes ticked, for calc/sharing.py's `share`.

**«Enregistrer comme modèle…»** (`TemplateDialog`): the name of the document template in the language the document is written in, its description, and the place it is kept in -- the engineer's own templates, or the office's shared folder where the settings name one, the choice closed with its reason where they do not. What it answers -- `(name, description, place)` -- is what calc/doc_templates.py's `save_from_document` is called with.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QRadioButton, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout,
)

import cards  # the notes and the rows of a form, after the website (cards.py)
import doc_import  # what can be imported, and from which document (calc/doc_import.py)
import documents  # what each of the three documents is called (calc/documents.py)
import structure  # the languages a chapter's title is given in (calc/structure.py)

ITEM_ROLE = Qt.ItemDataRole.UserRole


class SectionDialog(QDialog):
    """The title and the id of a new section; the id follows the title -- `suggest(title)` -- until it has been typed into."""

    def __init__(self, parent, t, where, suggest, rs=False):
        super().__init__(parent)
        self.setWindowTitle(t("st_new_section"))
        self.suggest = suggest
        self.touched = False
        box = QVBoxLayout(self)
        box.addWidget(cards.note(where))
        form = cards.form()
        self.title = QLineEdit()
        self.id = QLineEdit()
        form.addRow(QLabel(t("st_title_label")), self.title)
        form.addRow(QLabel(t("st_id_label")), self.id)
        box.addLayout(form)
        box.addWidget(cards.note(t("st_id_note_rs" if rs else "st_id_note")))
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        box.addWidget(self.buttons)
        self.title.textChanged.connect(self.on_title)
        self.id.textEdited.connect(self.on_id)
        self.on_title("")

    def on_title(self, text):
        text = text.strip()
        if not self.touched:
            self.id.setText(self.suggest(text) if text else "")
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(bool(text))

    def on_id(self, _text):
        self.touched = True

    def values(self):
        """(id, title) as typed."""
        return self.id.text().strip(), self.title.text().strip()


class GroupDialog(QDialog):
    """The id and the three titles of a new chapter; the id follows the English title until it has been typed into."""

    def __init__(self, parent, t, where, suggest):
        super().__init__(parent)
        self.setWindowTitle(t("st_new_group"))
        self.suggest = suggest
        self.touched = False
        box = QVBoxLayout(self)
        box.addWidget(cards.note(where))
        form = cards.form()
        self.titles = {lang: QLineEdit() for lang in structure.LANGUAGES}
        for lang in structure.LANGUAGES:
            form.addRow(QLabel(t("st_title_" + lang)), self.titles[lang])
        self.id = QLineEdit()
        form.addRow(QLabel(t("st_id_label")), self.id)
        box.addLayout(form)
        box.addWidget(cards.note(t("st_group_note")))
        box.addWidget(cards.note(t("st_id_note")))
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        box.addWidget(self.buttons)
        for edit in self.titles.values():
            edit.textChanged.connect(self.on_title)
        self.id.textEdited.connect(self.on_id)
        self.on_title("")

    def on_title(self, _text):
        english = self.titles["en"].text().strip()
        if not self.touched:
            self.id.setText(self.suggest(english) if english else "")
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(all(edit.text().strip() for edit in self.titles.values()))

    def on_id(self, _text):
        self.touched = True

    def values(self):
        """(id, {fr, de, en}) as typed."""
        return self.id.text().strip(), {lang: edit.text().strip() for lang, edit in self.titles.items()}


class ImportDialog(QDialog):
    """Which sections and objects of another document to bring in, and whether they stay linked to it."""

    def __init__(self, parent, t, here, mode, lang):
        super().__init__(parent)
        self.t, self.here, self.mode, self.lang = t, here, mode, lang
        self.setWindowTitle(t("st_import_title"))
        self.setMinimumSize(520, 520)
        self.sources = list(doc_import.other_documents(here, mode))
        box = QVBoxLayout(self)
        box.addWidget(cards.note(t("st_import_intro")))
        row = QHBoxLayout()
        row.addWidget(QLabel(t("st_import_from")))
        self.combo = QComboBox()
        for source in self.sources:
            self.combo.addItem(documents.mode_name(source, lang), source)
        row.addWidget(self.combo, 1)
        box.addLayout(row)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(True)
        box.addWidget(self.tree, 1)
        self.note = cards.note("")
        box.addWidget(self.note)
        self.independent = QCheckBox(t("st_import_independent"))
        self.independent.setToolTip(t("st_import_independent_tip"))
        box.addWidget(self.independent)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        box.addWidget(self.buttons)
        self.combo.currentIndexChanged.connect(self.fill)
        self.tree.itemChanged.connect(self.update_ok)
        self.fill()

    # -- the tree of what the chosen document holds

    def source(self):
        """The document chosen, "" where the project has no other."""
        return self.combo.currentData() or ""

    def fill(self, _index=None):
        """The tree of document `source()` made again: its chapters, sections and objects, each with a box -- ticked or not as nothing was."""
        self.tree.blockSignals(True)
        try:
            self.tree.clear()
            source = self.source()
            items = []
            self.note.setText("")
            if source:
                try:
                    items = doc_import.importable(self.here, source)
                except Exception as exc:     # broad: a document that cannot be read says why, where the tree would be
                    self.note.setText(str(exc))
            for item in items:
                self.add(item, self.tree)
            if source and not items and not self.note.text():
                self.note.setText(self.t("st_import_empty"))
            self.tree.expandToDepth(1)
        finally:
            self.tree.blockSignals(False)
        self.update_ok()

    def add(self, item, parent):
        row = QTreeWidgetItem(parent)
        title = item.title or item.id
        if item.kind == doc_import.KIND_OBJECT:
            title = self.t("st_import_object", title=title, type=self.t("st_kind_" + item.object_type) if item.object_type else "")
        row.setText(0, title)
        row.setData(0, ITEM_ROLE, item)
        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable
        if item.children:
            flags |= Qt.ItemFlag.ItemIsAutoTristate
        row.setFlags(flags)
        row.setCheckState(0, Qt.CheckState.Unchecked)
        if item.kind == doc_import.KIND_GROUP:
            font = row.font(0)
            font.setBold(True)
            row.setFont(0, font)
        if item.problems:
            row.setToolTip(0, "\n".join(item.problems))
        for child in item.children:
            self.add(child, row)
        return row

    def update_ok(self, *_args):
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(bool(self.items()))

    # -- the answer

    @staticmethod
    def collect(row):
        """The items a row stands for: a chapter or a section ticked whole is itself, one ticked in part is what is ticked under it, an object ticked is itself."""
        state = row.checkState(0)
        if state == Qt.CheckState.Unchecked:
            return []
        item = row.data(0, ITEM_ROLE)
        if state == Qt.CheckState.Checked or item.kind == doc_import.KIND_OBJECT:
            return [item]
        found = []
        for index in range(row.childCount()):
            found += ImportDialog.collect(row.child(index))
        return found

    def items(self):
        """The `Item`s ticked, in document order -- what `doc_import.import_items` takes."""
        found = []
        for index in range(self.tree.topLevelItemCount()):
            found += self.collect(self.tree.topLevelItem(index))
        return found

    def values(self):
        """(source document, items, linked): `linked` is False where «copie indépendante» is ticked."""
        return self.source(), self.items(), not self.independent.isChecked()

    def tick(self, predicate, on=True):
        """Ticks (or clears) every row whose `Item` satisfies `predicate` -- how a test, and a caller that knows what it wants, chooses without a click."""
        self.tree.blockSignals(True)
        try:
            stack = [self.tree.topLevelItem(i) for i in range(self.tree.topLevelItemCount())]
            while stack:
                row = stack.pop()
                if predicate(row.data(0, ITEM_ROLE)):
                    row.setCheckState(0, Qt.CheckState.Checked if on else Qt.CheckState.Unchecked)
                stack += [row.child(i) for i in range(row.childCount())]
        finally:
            self.tree.blockSignals(False)
        self.update_ok()


class TemplateDialog(QDialog):
    """The name, the description and the place of a document template made of the document being worked on. `places` is a list of (place, words, enabled, reason): a place that cannot be chosen -- the office's, where no shared folder is set -- is shown closed, its reason as its tooltip and beside it, a choice disabled with nothing to say being one the engineer cannot account for."""

    def __init__(self, parent, t, document, language, places):
        super().__init__(parent)
        self.setWindowTitle(t("st_template_title"))
        self.setMinimumWidth(460)
        box = QVBoxLayout(self)
        box.addWidget(cards.note(t("st_template_intro", document=document, language=language)))
        form = cards.form()
        self.name = QLineEdit()
        self.name.setPlaceholderText(t("st_template_name_hint", language=language))
        self.description = QPlainTextEdit()
        self.description.setFixedHeight(72)
        form.addRow(QLabel(t("st_template_name")), self.name)
        form.addRow(QLabel(t("st_template_description")), self.description)
        box.addLayout(form)
        box.addWidget(QLabel(t("st_template_place")))
        self.radios = []
        for place, words, enabled, reason in places:
            radio = QRadioButton(words if enabled or not reason else f"{words} — {reason}")
            radio.setProperty("place", place)
            radio.setEnabled(bool(enabled))
            if not enabled and reason:
                radio.setToolTip(reason)
            self.radios.append(radio)
            box.addWidget(radio)
        first = next((radio for radio in self.radios if radio.isEnabled()), None)
        if first is not None:
            first.setChecked(True)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        box.addWidget(self.buttons)
        self.name.textChanged.connect(self.update_ok)
        self.update_ok()

    def update_ok(self, *_args):
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(bool(self.name.text().strip()) and any(radio.isChecked() for radio in self.radios))

    def values(self):
        """(name, description, place) as typed and ticked; the place is `user` or `office`."""
        place = next((radio.property("place") for radio in self.radios if radio.isChecked()), "user")
        return self.name.text().strip(), self.description.toPlainText().strip(), place


class ShareDialog(QDialog):
    """Which of the other documents of the project a section is shared with. `documents` is a list of (mode, words, shared): a document the section is shared with already is shown ticked and closed, with its reason, and is not part of what the dialog answers. Where there is nobody to share with, the dialog says so and cannot be accepted; where exactly one document can be chosen, it is ticked."""

    def __init__(self, parent, t, title, documents):
        super().__init__(parent)
        self.setWindowTitle(t("st_share_title"))
        self.setMinimumWidth(440)
        box = QVBoxLayout(self)
        box.addWidget(cards.note(t("st_share_intro", title=title)))
        self.boxes = []
        for mode, words, shared in documents:
            check = QCheckBox(t("st_share_already", document=words) if shared else words)
            check.setProperty("mode", mode)
            if shared:
                check.setChecked(True)
                check.setEnabled(False)
            check.toggled.connect(self.update_ok)
            self.boxes.append(check)
            box.addWidget(check)
        open_boxes = [check for check in self.boxes if check.isEnabled()]
        if not open_boxes:
            box.addWidget(cards.note(t("st_share_nobody")))
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        box.addWidget(self.buttons)
        if len(open_boxes) == 1:
            open_boxes[0].setChecked(True)
        self.update_ok()

    def update_ok(self, *_args):
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(bool(self.values()))

    def values(self):
        """The modes ticked, in the order they are listed -- a document the section is shared with already is not among them."""
        return [check.property("mode") for check in self.boxes if check.isEnabled() and check.isChecked()]


class ChoiceDialog(QDialog):
    """Which version of a shared block or object to keep where this document and another changed it: this document's, the newest of the others, or one document's. `options` is a list of (value, words) -- `mine`, `theirs` or a document's code -- and `chosen()` the value of the one ticked."""

    def __init__(self, parent, t, item_label, others, options):
        super().__init__(parent)
        self.setWindowTitle(t("st_choice_title"))
        box = QVBoxLayout(self)
        box.addWidget(cards.note(t("st_choice_ask", item=item_label, others=others)))
        self.radios = []
        for value, words in options:
            radio = QRadioButton(words)
            radio.setProperty("choice", value)
            self.radios.append(radio)
            box.addWidget(radio)
        if self.radios:
            self.radios[0].setChecked(True)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        box.addWidget(buttons)

    def chosen(self):
        return next((radio.property("choice") for radio in self.radios if radio.isChecked()), None)
