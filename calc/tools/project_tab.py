"""The «Projet» tab: the project's basic data, its templates and its documents, the first row of the navigation (issues #87, #88, #90; docs/ui/tab-project.md).

The engineer, 21.10.2026: «lorsque l'on passe de la convention d'utilisation à la base de projet ou au rapport de statique, l'onglet qui doit s'ouvrir […] c'est l'onglet projet. De cette manière, il n'y a pas de compilation automatique de tout le rapport en TYPST». It is where the window opens, and where every change of document brings it back: its first view compiles nothing.

**Two views.** «Informations» (`details`) -- cards: the title page, which the engineer types (the `.woodcore`'s name and DETAILS, read by `Project.detail`, written by `project.update`, and reported at once into data/project.json, export_all.refresh_project_info); the project's language, chosen as the project was created and shown greyed (templates.project_language); the form in use, common to the three documents, and «Appliquer au projet…» (home_page.apply_form); each document's content template (`Project.content_template`: «inconnu» for a project made before 0.122, «introuvable» where it is not on this machine) -- or, for a document not made yet, its choice and «Créer le document…» (project_template.create_document); the Woodcore version pinned; the three documents' folders with «Ouvrir le dossier»; the last export (project.last_export); «Ouvrir dans VS Code». «Templates» (`templates`) -- on the left the document, the content template and the form to look at; in the centre that document compiled with them and nothing of the project but its basic data (calc/template_preview.py), built off the window's thread, the last request alone counting. Choosing in a list changes the preview and nothing else.

**Saving.** As every tab (autosave.py): the title page and the pinned version saved without a question when the tab is left, the document changed or the window left for another application, by Ctrl+S and by «Enregistrer»; «Annuler les modifications» reads the file again. Applying a form and creating a document are acts of their own, each confirmed. In a project opened read-only every field and button is off, and every writer is refused (tab_guard.WRITERS).

The tab's words, `pj_` (and `tpv_why_` for why a preview could not be made), in the window's three languages, are merged into woodcore_gui's STRINGS; it reuses the start page's `proj_` words for the title page's fields. It must not import woodcore_gui.
"""

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtWidgets import (QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QSplitter,
                               QStackedWidget, QVBoxLayout, QWidget)

import autosave
import busy
import cards
import doc_templates
import documents
import forms
import home_page
import notifications
import notices_ui
import pdf_pane
import project
import project_template
import settings_dialog
import source_editor
import template_preview
import templates
import usersettings

KEY = "tab_project"

STRINGS = {
    "fr": {
        "tab_project": "Projet",
        "pj_title_card": "Page de titre",
        "pj_title_note": "Imprimé sur la page de titre et dans les métadonnées du PDF : reporté tout de suite pour le prochain PDF.",
        "pj_language_card": "Langue du projet",
        "pj_language_note": "Choisie à la création du projet ; elle ne se change plus.",
        "pj_form_card": "Template de forme",
        "pj_form_apply": "Appliquer au projet…",
        "pj_documents_card": "Documents",
        "pj_content": "Template de fond",
        "pj_unknown": "inconnu",
        "pj_missing": "introuvable sur ce poste ({ref})",
        "pj_not_made": "pas encore créé",
        "pj_create": "Créer le document…",
        "pj_create_ask": "Créer « {document} » à partir du template de fond « {template} » ?\n\nLe document est créé dans le dossier {folder}. Son template de fond ne se change plus ensuite.",
        "pj_create_failed": "Le document n'a pas pu être créé :\n\n{error}",
        "pj_busy_creating": "Création du document…",
        "pj_open_folder": "Ouvrir le dossier",
        "pj_version_card": "Version de Woodcore",
        "pj_export_card": "Dernier export",
        "pj_export_none": "Le projet n'a pas encore été exporté.",
        "pj_export_at": "Le {date}, moteur {engine}",
        "pj_vscode": "Ouvrir dans VS Code",
        "pj_save": "Enregistrer",
        "pj_discard": "Annuler les modifications",
        "pj_report_failed": "Enregistré, mais la page de titre n'a pas pu être reportée dans data/project.json : {error}",
        "pj_preview_document": "Document",
        "pj_preview_note": "L'aperçu montre le document choisi avec ces deux templates et les seules données de base du projet : rien n'est écrit dans le projet.",
        "pj_preview_building": "Préparation de l'aperçu…",
        "pj_preview_failed": "L'aperçu n'a pas pu être préparé : {error}",
        "pj_not_made_tip": "Ce document n'est pas encore créé : choisissez son template de fond dans l'onglet Projet.",
        "tpv_why_no_language": "le projet n'a pas de langue",
        "tpv_why_bad_mode": "ce document n'existe pas",
        "tpv_why_template_unusable": "ce template de fond n'existe pas dans la langue du projet",
        "tpv_why_build_failed": "le document n'a pas pu être construit",
    },
    "de": {
        "tab_project": "Projekt",
        "pj_title_card": "Titelseite",
        "pj_title_note": "Auf der Titelseite und in den Metadaten des PDF gedruckt: sofort für das nächste PDF übernommen.",
        "pj_language_card": "Sprache des Projekts",
        "pj_language_note": "Beim Erstellen des Projekts gewählt; sie lässt sich nicht mehr ändern.",
        "pj_form_card": "Formvorlage",
        "pj_form_apply": "Auf das Projekt anwenden…",
        "pj_documents_card": "Dokumente",
        "pj_content": "Inhaltsvorlage",
        "pj_unknown": "unbekannt",
        "pj_missing": "auf diesem Rechner nicht vorhanden ({ref})",
        "pj_not_made": "noch nicht erstellt",
        "pj_create": "Dokument erstellen…",
        "pj_create_ask": "«{document}» aus der Inhaltsvorlage «{template}» erstellen?\n\nDas Dokument wird im Ordner {folder} erstellt. Seine Inhaltsvorlage lässt sich danach nicht mehr ändern.",
        "pj_create_failed": "Das Dokument konnte nicht erstellt werden:\n\n{error}",
        "pj_busy_creating": "Dokument wird erstellt…",
        "pj_open_folder": "Ordner öffnen",
        "pj_version_card": "Woodcore-Version",
        "pj_export_card": "Letzter Export",
        "pj_export_none": "Das Projekt wurde noch nicht exportiert.",
        "pj_export_at": "Am {date}, Engine {engine}",
        "pj_vscode": "In VS Code öffnen",
        "pj_save": "Speichern",
        "pj_discard": "Änderungen verwerfen",
        "pj_report_failed": "Gespeichert, aber die Titelseite konnte nicht in data/project.json übernommen werden: {error}",
        "pj_preview_document": "Dokument",
        "pj_preview_note": "Die Vorschau zeigt das gewählte Dokument mit diesen beiden Vorlagen und nur den Grunddaten des Projekts: nichts wird ins Projekt geschrieben.",
        "pj_preview_building": "Vorschau wird vorbereitet…",
        "pj_preview_failed": "Die Vorschau konnte nicht vorbereitet werden: {error}",
        "pj_not_made_tip": "Dieses Dokument ist noch nicht erstellt: seine Inhaltsvorlage wird im Register Projekt gewählt.",
        "tpv_why_no_language": "das Projekt hat keine Sprache",
        "tpv_why_bad_mode": "dieses Dokument gibt es nicht",
        "tpv_why_template_unusable": "diese Inhaltsvorlage gibt es in der Sprache des Projekts nicht",
        "tpv_why_build_failed": "das Dokument konnte nicht aufgebaut werden",
    },
    "en": {
        "tab_project": "Project",
        "pj_title_card": "Title page",
        "pj_title_note": "Printed on the title page and in the PDF's metadata: carried over at once for the next PDF.",
        "pj_language_card": "Project language",
        "pj_language_note": "Chosen when the project was created; it no longer changes.",
        "pj_form_card": "Layout template",
        "pj_form_apply": "Apply to the project…",
        "pj_documents_card": "Documents",
        "pj_content": "Content template",
        "pj_unknown": "unknown",
        "pj_missing": "not on this machine ({ref})",
        "pj_not_made": "not created yet",
        "pj_create": "Create the document…",
        "pj_create_ask": "Create «{document}» from the content template «{template}»?\n\nThe document is created in the folder {folder}. Its content template cannot be changed afterwards.",
        "pj_create_failed": "The document could not be created:\n\n{error}",
        "pj_busy_creating": "Creating the document…",
        "pj_open_folder": "Open the folder",
        "pj_version_card": "Woodcore version",
        "pj_export_card": "Last export",
        "pj_export_none": "The project has not been exported yet.",
        "pj_export_at": "On {date}, engine {engine}",
        "pj_vscode": "Open in VS Code",
        "pj_save": "Save",
        "pj_discard": "Discard the changes",
        "pj_report_failed": "Saved, but the title page could not be carried into data/project.json: {error}",
        "pj_preview_document": "Document",
        "pj_preview_note": "The preview shows the chosen document with these two templates and the project's basic data alone: nothing is written into the project.",
        "pj_preview_building": "Preparing the preview…",
        "pj_preview_failed": "The preview could not be prepared: {error}",
        "pj_not_made_tip": "This document is not created yet: choose its content template in the Project tab.",
        "tpv_why_no_language": "the project has no language",
        "tpv_why_bad_mode": "this document does not exist",
        "tpv_why_template_unusable": "this content template does not exist in the project's language",
        "tpv_why_build_failed": "the document could not be built",
    },
}


class _Preview(QThread):
    """A preview built off the window's thread (template_preview.prepare): `done(generation, project, mode)` or `failed(generation, code, message)`."""

    done = Signal(int, object, str)
    failed = Signal(int, str, str)

    def __init__(self, generation, here, mode, content, form):
        super().__init__()
        self.args = (generation, here, mode, content, form)

    def run(self):
        generation, here, mode, content, form = self.args
        try:
            shown = template_preview.prepare(here, mode, content, form)
        except template_preview.TemplatePreviewError as exc:
            self.failed.emit(generation, exc.code, str(exc))
            return
        except Exception as exc:  # broad: a thread's failure is said in the pane, never lost
            self.failed.emit(generation, "build_failed", str(exc))
            return
        self.done.emit(generation, shown, mode)


class ProjectTab(QWidget):
    """The project's basic data, its templates and its documents (issues #87, #88, #90)."""

    KEY = KEY
    VIEWS = ("details", "templates")

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.t = app.t
        self.lang = app.lang
        self.dirty = False
        self.view = self.VIEWS[0]
        self.generation = 0
        self.workers = []
        self.settings = usersettings.read()
        self.forms_found = [found for found in forms.list_forms(self.settings) if not found.error]
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)
        self.stack.addWidget(self._details_page())
        self.stack.addWidget(self._templates_page())
        source_editor.save_shortcut(self)
        self.load()
        state = getattr(app, "views", {}).get(KEY)
        if state:
            self.restore(state)

    # --- «Informations» ------------------------------------------------------------------

    def _details_page(self):
        scroll, column = cards.column()
        here = project.current()
        # the title page
        box = cards.card(self.t("pj_title_card"))
        rows = QVBoxLayout(box)
        rows.addWidget(cards.note(self.t("pj_title_note")))
        form = cards.form()
        self.fields = {}
        for key in ("name", *project.DETAILS):
            field = QLineEdit()
            field.textEdited.connect(self.mark_dirty)
            form.addRow(self.t("proj_" + key), field)
            self.fields[key] = field
        rows.addLayout(form)
        buttons = QHBoxLayout()
        self.save_button = QPushButton(self.t("pj_save"))
        self.save_button.clicked.connect(self.save)
        self.discard_button = QPushButton(self.t("pj_discard"))
        self.discard_button.clicked.connect(self.discard)
        buttons.addStretch(1)
        buttons.addWidget(self.discard_button)
        buttons.addWidget(self.save_button)
        rows.addLayout(buttons)
        column.addWidget(box)
        # the language: chosen as the project was created, shown greyed
        box = cards.card(self.t("pj_language_card"))
        rows = QVBoxLayout(box)
        self.language = QComboBox()
        for code in templates.LANGUAGES:
            self.language.addItem(settings_dialog.LANGUAGE_NAMES[code], code)
        self.language.setEnabled(False)
        rows.addWidget(self.language)
        rows.addWidget(cards.note(self.t("pj_language_note")))
        column.addWidget(box)
        # the form, common to the three documents
        box = cards.card(self.t("pj_form_card"))
        rows = QVBoxLayout(box)
        row = QHBoxLayout()
        self.form_combo = self._form_combo()
        self.form_apply = QPushButton(self.t("pj_form_apply"))
        self.form_apply.clicked.connect(lambda: self.write_apply_form(self.form_combo.currentData()))
        row.addWidget(self.form_combo, 1)
        row.addWidget(self.form_apply)
        rows.addLayout(row)
        rows.addWidget(cards.note(self.t("proj_form_hint")))
        column.addWidget(box)
        # the documents: each its content template and its folder -- or, not made yet, its choice and «Créer le document…»
        box = cards.card(self.t("pj_documents_card"))
        self.documents_form = QFormLayout(box)
        self.document_rows = {}
        for mode in here.modes:
            cell = QWidget()
            line = QVBoxLayout(cell)
            line.setContentsMargins(0, 0, 0, 0)
            template = QLabel()
            template.setWordWrap(True)
            choose = QHBoxLayout()
            combo = QComboBox()
            create = QPushButton(self.t("pj_create"))
            create.clicked.connect(lambda _c=False, mode=mode: self.write_create_document(mode, self.document_rows[mode]["combo"].currentData()))
            choose.addWidget(combo, 1)
            choose.addWidget(create)
            folder_row = QHBoxLayout()
            folder = QLabel()
            folder.setObjectName("meta")
            folder.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            opener = QPushButton(self.t("pj_open_folder"))
            opener.clicked.connect(lambda _c=False, mode=mode: self.open_folder(mode))
            folder_row.addWidget(folder, 1)
            folder_row.addWidget(opener)
            line.addWidget(template)
            line.addLayout(choose)
            line.addLayout(folder_row)
            self.documents_form.addRow(documents.mode_name(mode, self.lang), cell)
            self.document_rows[mode] = {"template": template, "combo": combo, "create": create, "folder": folder, "open": opener}
        column.addWidget(box)
        # the version pinned
        box = cards.card(self.t("pj_version_card"))
        rows = QVBoxLayout(box)
        self.version = QComboBox()
        self.version.currentIndexChanged.connect(lambda _i: self.mark_dirty())
        rows.addWidget(self.version)
        column.addWidget(box)
        # the last export, and VS Code
        box = cards.card(self.t("pj_export_card"))
        rows = QVBoxLayout(box)
        self.export_label = QLabel()
        rows.addWidget(self.export_label)
        vscode = QPushButton(self.t("pj_vscode"))
        vscode.clicked.connect(self.app.open_vscode)
        rows.addWidget(vscode, 0, Qt.AlignmentFlag.AlignLeft)
        column.addWidget(box)
        column.addStretch(1)
        return scroll

    def _form_combo(self):
        combo = QComboBox()
        for found in self.forms_found:
            name = found.name(self.lang)
            combo.addItem(name if found.place == "builtin" else f"{name} — {settings_dialog.place_label(self.lang, found.place)}", found.ref)
            combo.setItemData(combo.count() - 1, found.description(self.lang), Qt.ItemDataRole.ToolTipRole)
        return combo

    # --- «Templates» ---------------------------------------------------------------------

    def _templates_page(self):
        here = project.current()
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)   # a pane dragged to nothing would have no arrow to come back by (chrome.FoldablePane)
        scroll, column = cards.column()
        # each list under its caption, one under the other: a left pane as narrow as every tab's (cards.PANE_FLOOR), a long name cut rather than holding it wider
        self.preview_document = QComboBox()
        for mode in here.modes:
            self.preview_document.addItem(documents.mode_name(mode, self.lang), mode)
        self.preview_document.currentIndexChanged.connect(self.on_preview_document)
        self.preview_content = QComboBox()
        self.preview_content.currentIndexChanged.connect(lambda _i: self.request_preview())
        self.preview_form = self._form_combo()
        self.preview_form.currentIndexChanged.connect(lambda _i: self.request_preview())
        for caption, combo in (("pj_preview_document", self.preview_document), ("pj_content", self.preview_content), ("pj_form_card", self.preview_form)):
            label = QLabel(self.t(caption))
            label.setWordWrap(True)
            column.addWidget(label)
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            combo.setMinimumContentsLength(6)
            column.addWidget(combo)
        self.preview_apply = QPushButton(self.t("pj_form_apply"))
        self.preview_apply.clicked.connect(lambda: self.write_apply_form(self.preview_form.currentData()))
        self.preview_create = QPushButton(self.t("pj_create"))
        self.preview_create.clicked.connect(lambda: self.write_create_document(self.preview_document.currentData(), self.preview_content.currentData()))
        column.addWidget(self.preview_apply)
        column.addWidget(self.preview_create)
        column.addWidget(cards.note(self.t("pj_preview_note")))
        column.addStretch(1)
        self.splitter.addWidget(scroll)
        centre = QWidget()
        rows = QVBoxLayout(centre)
        rows.setContentsMargins(0, 0, 0, 0)
        self.preview_banner = QLabel()
        self.preview_banner.setWordWrap(True)
        self.preview_banner.setProperty("callout", "warning")
        self.preview_banner.hide()
        rows.addWidget(self.preview_banner)
        self.pane = pdf_pane.PdfPane(centre, lang=self.lang)
        rows.addWidget(self.pane, 1)
        self.splitter.addWidget(centre)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 3)
        return self.splitter

    # --- reading -------------------------------------------------------------------------

    def load(self):
        """Every card filled from the project as its files state it now; nothing unsaved any more."""
        here = project.current()
        for key, field in self.fields.items():
            field.setText(here.name if key == "name" else here.detail(key))
        language = templates.project_language(here, fallback=templates.DEFAULT_LANGUAGE)
        self.language.setCurrentIndex(max(0, self.language.findData(language)))
        current = forms.current(here)
        for combo in (self.form_combo, self.preview_form):
            combo.blockSignals(True)
            if current is not None and combo.findData(current.ref) < 0:
                combo.addItem(current.name(self.lang), current.ref)
            combo.setCurrentIndex(max(0, combo.findData(current.ref if current is not None else forms.default_ref(self.settings))))
            combo.blockSignals(False)
        for mode, row in self.document_rows.items():
            self._fill_document(here, mode, row, language)
        self.version.blockSignals(True)
        self.version.clear()
        self.version.addItem(self.t("proj_version_latest"), "")
        pinned = str(here.data.get(project.PIN_KEY, "") or "")
        for version in dict.fromkeys([*home_page.installed_versions(), *([pinned] if pinned else [])]):
            self.version.addItem(version, version)
        self.version.setCurrentIndex(max(0, self.version.findData(pinned)))
        self.version.blockSignals(False)
        when, engine = project.last_export(here)
        self.export_label.setText(self.t("pj_export_at", date=when.strftime("%d.%m.%Y %H:%M"), engine=engine or "?") if when else self.t("pj_export_none"))
        self.on_preview_document()
        self.dirty = False
        self.lock()

    def _content_name(self, mode, ref):
        """A content template as the tab names it: its name in the window's language, «inconnu» for none kept, «introuvable» for one not on this machine."""
        if not ref:
            return self.t("pj_unknown")
        try:
            found = doc_templates.find(ref, mode)
        except doc_templates.DocTemplateError:
            return self.t("pj_missing", ref=ref)
        return found.name(self.lang) if not found.error else self.t("pj_missing", ref=ref)

    def _templates_for(self, mode, language):
        try:
            return doc_templates.list_templates(mode, language=language, settings=self.settings)
        except doc_templates.DocTemplateError:
            return []

    def _fill_document(self, here, mode, row, language):
        made = here.is_created(mode)
        row["template"].setText(f"{self.t('pj_content')} : {self._content_name(mode, here.content_template(mode))}" if made else self.t("pj_not_made"))
        row["folder"].setText(here.rel(here.document_dir(mode)))
        row["combo"].clear()
        for found in self._templates_for(mode, language):
            row["combo"].addItem(found.name(self.lang), found.ref)
        row["combo"].setCurrentIndex(max(0, row["combo"].findData(doc_templates.default_ref(mode))))
        for key in ("combo", "create"):
            row[key].setVisible(not made and here.has_modes)
        row["open"].setEnabled(here.document_dir(mode).is_dir())

    def lock(self):
        """Every field and button that writes off in a project opened read-only."""
        writable = not getattr(self.app, "read_only", False)
        for widget in (*self.fields.values(), self.save_button, self.discard_button, self.form_apply, self.version, self.preview_apply):
            widget.setEnabled(writable)
        here = project.current()
        for mode, row in self.document_rows.items():
            row["create"].setEnabled(writable and not here.is_created(mode))
        mode = self.preview_document.currentData()
        self.preview_create.setEnabled(writable and here.has_modes and mode is not None and not here.is_created(mode))

    def mark_dirty(self, *_args):
        if not self.dirty:
            self.dirty = True
            self.app.update_tab_marks()

    # --- the tab's life in the window ----------------------------------------------------

    def set_view(self, key, enter=True):
        """«Informations» or «Templates»: the second builds its preview as it is shown, never while the window is built (`enter` False)."""
        if key not in self.VIEWS:
            return
        self.view = key
        self.stack.setCurrentIndex(self.VIEWS.index(key))
        if key == "templates" and enter and self.isVisible():
            self.request_preview()

    def showEvent(self, event):
        super().showEvent(event)
        if self.view == "templates":
            self.request_preview()

    def on_shown(self):
        """Read again as it is shown, where nothing is unsaved: a document made, a form applied elsewhere."""
        if not self.dirty:
            self.load()

    def on_mode(self, _mode):
        if not self.dirty:
            self.load()

    def view_state(self):
        """What the tab keeps through a rebuilt window: the title page typed and not saved, and the document looked at."""
        return {"draft": {key: field.text() for key, field in self.fields.items()} if self.dirty else None,
                "version": self.version.currentData() if self.dirty else None,
                "document": self.preview_document.currentData(), "splitter": self.splitter.sizes()}

    def restore(self, state):
        draft = state.get("draft")
        if draft:
            for key, value in draft.items():
                if key in self.fields:
                    self.fields[key].setText(value)
            if state.get("version") is not None:
                self.version.setCurrentIndex(max(0, self.version.findData(state["version"])))
            self.dirty = True
        if state.get("document") is not None:
            self.preview_document.setCurrentIndex(max(0, self.preview_document.findData(state["document"])))
        sizes = state.get("splitter")
        if sizes and len(sizes) == self.splitter.count():
            self.splitter.setSizes(sizes)

    def confirm_leave(self):
        return autosave.confirm(self.app, self, self.t("tab_project"), self.t("pj_title_card"), discard=self.discard)

    # --- writing ------------------------------------------------------------------------

    def save(self):
        """The title page and the pinned version written into the project file -- only what changed, a name never empty -- and the title page reported at once into data/project.json (export_all.refresh_project_info: no export, no stamp). Returns whether it was saved."""
        here = project.current()
        values = {key: field.text().strip() for key, field in self.fields.items()}
        if not values["name"]:
            return autosave.refuse(self, self.t("tab_project"), self.t("proj_name_needed"))
        changes = {key: value for key, value in values.items() if value != (here.name if key == "name" else here.detail(key))}
        pinned = self.version.currentData() or ""
        if pinned != str(here.data.get(project.PIN_KEY, "") or ""):
            changes[project.PIN_KEY] = pinned
        if changes:
            try:
                here = project.update(here.file, **changes)
            except (project.ProjectError, OSError) as exc:
                return autosave.refuse(self, self.t("tab_project"), self.t("proj_failed", error=exc))
            try:
                import export_all
                export_all.refresh_project_info(here)
            except Exception as exc:  # broad: the project file is written; the export says the rest at its next run
                autosave.warn(self, self.t("tab_project"), self.t("pj_report_failed", error=exc))
            self.app.project_changed()
        self.dirty = False
        self.app.update_tab_marks()
        return True

    def discard(self):
        self.load()
        self.app.update_tab_marks()

    def write_apply_form(self, ref):
        """The form `ref` applied to the three documents, once the engineer agrees (home_page.apply_form: Template/ and title.typ replaced, the old ones archived)."""
        found = next((form for form in self.forms_found if form.ref == ref), None)
        current = forms.current(project.current())
        if found is None or (current is not None and current.ref == found.ref):
            return False
        if self.dirty and not self.save():
            return False
        applied = home_page.apply_form(self, self.lang, project.current(), found, current)
        if applied:
            self.app.properties_written(True)
            self.load()
        return applied

    def write_create_document(self, mode, ref):
        """Document `mode` made from content template `ref`, once the engineer agrees -- in its folder, its content template then fixed (project_template.create_document) -- and the window built again for it."""
        here = project.current()
        if mode is None or here.is_created(mode) or not here.has_modes:
            return False
        found = next((t for t in self._templates_for(mode, templates.project_language(here, fallback="")) if t.ref == ref), None)
        if found is None:
            return False
        question = self.t("pj_create_ask", document=documents.mode_name(mode, self.lang), template=found.name(self.lang), folder=here.rel(here.document_dir(mode)))
        if QMessageBox.question(self, self.t("tab_project"), question, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return False
        try:
            busy.run_in_thread(self.app, self.t("pj_busy_creating"), lambda: project_template.create_document(here, mode, found))
        except (project.ProjectError, OSError) as exc:
            notices_ui.tell(self.t("pj_create_failed", error=exc), notifications.CRITICAL, exc=exc, source="project_tab")
            return False
        project.use(here.file)
        self.app.document_created(mode)
        return True

    def open_folder(self, mode):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(project.current().document_dir(mode))))

    # --- the preview -------------------------------------------------------------------

    def on_preview_document(self, _index=None):
        """Another document looked at: its content templates in the project's language, its own chosen where it was made from one."""
        here = project.current()
        mode = self.preview_document.currentData()
        self.preview_content.blockSignals(True)
        self.preview_content.clear()
        if mode is not None:
            for found in self._templates_for(mode, templates.project_language(here, fallback="")):
                self.preview_content.addItem(found.name(self.lang), found.ref)
            own = here.content_template(mode) or doc_templates.default_ref(mode)
            self.preview_content.setCurrentIndex(max(0, self.preview_content.findData(own)))
            made = here.is_created(mode)
            self.preview_content.setEnabled(not made)   # a document made keeps its content template; its look may still be previewed with another form
        self.preview_content.blockSignals(False)
        self.lock()
        self.request_preview()

    def request_preview(self):
        """The preview built again for what the three lists say -- off the window's thread, the last request alone counting -- while the «Templates» view is shown."""
        if self.view != "templates" or not self.isVisible():
            return
        mode = self.preview_document.currentData()
        if mode is None:
            return
        self.generation += 1
        self.preview_banner.setText(self.t("pj_preview_building"))
        self.preview_banner.show()
        worker = _Preview(self.generation, project.current(), mode, self.preview_content.currentData(), self.preview_form.currentData())
        worker.done.connect(self.on_preview_done)
        worker.failed.connect(self.on_preview_failed)
        worker.finished.connect(lambda worker=worker: self.workers.remove(worker) if worker in self.workers else None)
        self.workers.append(worker)
        worker.start()

    def on_preview_done(self, generation, shown, mode):
        if generation != self.generation:
            return
        self.preview_banner.hide()
        self.pane.set_document(shown, mode)
        self.pane.request(shown, mode)
        template_preview.clean(project.current(), keep=shown)

    def on_preview_failed(self, generation, code, message):
        if generation != self.generation:
            return
        why = self.t("tpv_why_" + code) if code in template_preview.CODES else message
        self.preview_banner.setText(self.t("pj_preview_failed", error=why))
        self.preview_banner.setToolTip(message)
        self.preview_banner.show()
