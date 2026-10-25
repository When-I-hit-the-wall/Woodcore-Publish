"""The services of the «Projet» tab (project_tab.ProjectTab, a tab of the type «Document»: document_tab.py; spec docs/requirements/completed/2026-10-24-type-document.md, issue #107, REQ-002, ARCH-006; docs/ui/tab-project.md).

What the tab did as one class until issue #107, cut by what it shows and what it writes:

* **«Informations»** (`ProjectDetails`, the view `details`): the cards -- the title page the engineer types and its «Enregistrer» / «Annuler les modifications», the project's language greyed, the form in use and «Appliquer au projet…», each document's content template or its choice and «Créer le document…», the Woodcore version pinned, the documents' folders, the last export, «Ouvrir dans VS Code». The title page and the version are the tab's one draft: a change sets the context's flag (`touch`), `save` writes what changed;
* **«Templates»** (`ProjectTemplates`, the view `templates`): the document, the content template and the form to look at, and that document compiled with them off the window's thread, the last request alone counting -- its splitter is the tab's;
* **the acts** (`ProjectActions`, no pane): applying a form to the project and creating a document -- the two writers both pages trigger --, opening a document's folder, and what both pages list -- the forms found, a document's content templates, a content template's name --, read once and offered through the context (`PROVIDES`, `DocumentContext.provide`): no service holds another (ARCH-002).

A box asked takes the tab for its parent (`ctx.host`): a service is no widget (ARCH-RISK-009). The words are the tab's (`pj_`, `tpv_why_`, project_tab.STRINGS) and the start page's (`proj_`): no service has words of its own (`WORDS_MODULE` None, ARCH-003).
"""

from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot
from PySide6.QtWidgets import QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QSplitter, QVBoxLayout, QWidget

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
import template_preview
import templates
import usersettings
from tab_frame import Service


def form_combo(found_forms, lang):
    """A list of the forms found, each named in `lang` and, where it is not built in, by its place; its description as its tooltip -- what both pages offer."""
    combo = QComboBox()
    for found in found_forms:
        name = found.name(lang)
        combo.addItem(name if found.place == "builtin" else f"{name} — {settings_dialog.place_label(lang, found.place)}", found.ref)
        combo.setItemData(combo.count() - 1, found.description(lang), Qt.ItemDataRole.ToolTipRole)
    return combo


def select_form(combo, current, default_ref, lang):
    """The form in use chosen in `combo` -- added where it is not among the forms found --, else the default, without a signal."""
    combo.blockSignals(True)
    if current is not None and combo.findData(current.ref) < 0:
        combo.addItem(current.name(lang), current.ref)
    combo.setCurrentIndex(max(0, combo.findData(current.ref if current is not None else default_ref)))
    combo.blockSignals(False)


class ProjectActions(Service):
    """The tab's acts and what both its pages list -- see the module's docstring."""

    NAME = "actions"
    NEEDS = ("create_document",)
    NEEDS_MODULE = project_template
    WRITERS = ("write_apply_form", "write_create_document")
    PROVIDES = ("write_apply_form", "write_create_document", "open_folder", "forms", "default_form", "templates_for", "content_name")

    def mount(self, ctx):
        super().mount(ctx)
        self.lang = self.app.lang
        self.settings = usersettings.read()
        self.forms_found = [found for found in forms.list_forms(self.settings) if not found.error]
        return None

    def forms(self):
        return self.forms_found

    def default_form(self):
        return forms.default_ref(self.settings)

    def templates_for(self, mode, language):
        """The content templates of document `mode` in `language`, none where they cannot be listed."""
        try:
            return doc_templates.list_templates(mode, language=language, settings=self.settings)
        except doc_templates.DocTemplateError:
            return []

    def content_name(self, mode, ref):
        """A content template as the tab names it: its name in the window's language, «inconnu» for none kept, «introuvable» for one not on this machine."""
        if not ref:
            return self.t("pj_unknown")
        try:
            found = doc_templates.find(ref, mode)
        except doc_templates.DocTemplateError:
            return self.t("pj_missing", ref=ref)
        return found.name(self.lang) if not found.error else self.t("pj_missing", ref=ref)

    def write_apply_form(self, ref):
        """The form `ref` applied to the three documents, once the engineer agrees (home_page.apply_form: Template/ and title.typ replaced, the old ones archived) -- the title page saved first where it is unsaved."""
        found = next((form for form in self.forms_found if form.ref == ref), None)
        current = forms.current(project.current())
        if found is None or (current is not None and current.ref == found.ref):
            return False
        if self.ctx.dirty and not self.ctx.host.save():
            return False
        applied = home_page.apply_form(self.ctx.host, self.lang, project.current(), found, current)
        if applied:
            self.app.properties_written(True)
            self.ctx.reload()
        return applied

    def write_create_document(self, mode, ref):
        """Document `mode` made from content template `ref`, once the engineer agrees -- in its folder, its content template then fixed (project_template.create_document) -- and the window built again for it."""
        here = project.current()
        if mode is None or here.is_created(mode) or not here.has_modes:
            return False
        found = next((t for t in self.templates_for(mode, templates.project_language(here, fallback="")) if t.ref == ref), None)
        if found is None:
            return False
        question = self.t("pj_create_ask", document=documents.mode_name(mode, self.lang), template=found.name(self.lang), folder=here.rel(here.document_dir(mode)))
        if QMessageBox.question(self.ctx.host, self.t("tab_project"), question, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
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


class ProjectDetails(Service):
    """«Informations»: the cards of the project's basic data, and its one draft -- see the module's docstring."""

    NAME = "details"
    ZONE = "page"
    IN_VIEWS = ("details",)
    WRITERS = ("save",)

    def mount(self, ctx):
        super().mount(ctx)
        self.lang = self.app.lang
        provide = ctx.provide
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
        self.save_button.clicked.connect(lambda _checked=False: ctx.host.save())
        self.discard_button = QPushButton(self.t("pj_discard"))
        self.discard_button.clicked.connect(lambda _checked=False: ctx.host.discard())
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
        self.form_combo = form_combo(provide("forms")(), self.lang)
        self.form_apply = QPushButton(self.t("pj_form_apply"))
        self.form_apply.clicked.connect(lambda: provide("write_apply_form")(self.form_combo.currentData()))
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
            create.clicked.connect(lambda _c=False, mode=mode: provide("write_create_document")(mode, self.document_rows[mode]["combo"].currentData()))
            choose.addWidget(combo, 1)
            choose.addWidget(create)
            folder_row = QHBoxLayout()
            folder = QLabel()
            folder.setObjectName("meta")
            folder.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            opener = QPushButton(self.t("pj_open_folder"))
            opener.clicked.connect(lambda _c=False, mode=mode: provide("open_folder")(mode))
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

    # --- the phases ----------------------------------------------------------------------

    def loaded(self):
        """Every card filled from the project as its files state it now."""
        here = project.current()
        provide = self.ctx.provide
        for key, field in self.fields.items():
            field.setText(here.name if key == "name" else here.detail(key))
        language = templates.project_language(here, fallback=templates.DEFAULT_LANGUAGE)
        self.language.setCurrentIndex(max(0, self.language.findData(language)))
        select_form(self.form_combo, forms.current(here), provide("default_form")(), self.lang)
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

    def _fill_document(self, here, mode, row, language):
        made = here.is_created(mode)
        row["template"].setText(f"{self.t('pj_content')} : {self.ctx.provide('content_name')(mode, here.content_template(mode))}" if made else self.t("pj_not_made"))
        row["folder"].setText(here.rel(here.document_dir(mode)))
        row["combo"].clear()
        for found in self.ctx.provide("templates_for")(mode, language):
            row["combo"].addItem(found.name(self.lang), found.ref)
        row["combo"].setCurrentIndex(max(0, row["combo"].findData(doc_templates.default_ref(mode))))
        for key in ("combo", "create"):
            row[key].setVisible(not made and here.has_modes)
        row["open"].setEnabled(here.document_dir(mode).is_dir())

    def lock(self):
        """Every field and button that writes off in a project opened read-only."""
        writable = not self.ctx.read_only()
        for widget in (*self.fields.values(), self.save_button, self.discard_button, self.form_apply, self.version):
            widget.setEnabled(writable)
        here = project.current()
        for mode, row in self.document_rows.items():
            row["create"].setEnabled(writable and not here.is_created(mode))

    def shown(self):
        """Read again as it is shown, where nothing is unsaved: a document made, a form applied elsewhere."""
        if not self.ctx.dirty:
            self.ctx.reload()

    def mode_changed(self, _mode):
        if not self.ctx.dirty:
            self.ctx.reload()

    def discard(self):
        """The title page and the version read again from the project file."""
        self.ctx.reload()
        self.app.update_tab_marks()

    def mark_dirty(self, *_args):
        self.ctx.touch()

    # --- the draft ------------------------------------------------------------------------

    def save(self):
        """The title page and the pinned version written into the project file -- only what changed, a name never empty -- and the title page reported at once into data/project.json (export_all.refresh_project_info: no export, no stamp). Returns whether it was saved."""
        host = self.ctx.host
        here = project.current()
        values = {key: field.text().strip() for key, field in self.fields.items()}
        if not values["name"]:
            return autosave.refuse(host, self.t("tab_project"), self.t("proj_name_needed"))
        changes = {key: value for key, value in values.items() if value != (here.name if key == "name" else here.detail(key))}
        pinned = self.version.currentData() or ""
        if pinned != str(here.data.get(project.PIN_KEY, "") or ""):
            changes[project.PIN_KEY] = pinned
        if changes:
            try:
                here = project.update(here.file, **changes)
            except (project.ProjectError, OSError) as exc:
                return autosave.refuse(host, self.t("tab_project"), self.t("proj_failed", error=exc))
            try:
                import export_all
                export_all.refresh_project_info(here)
            except Exception as exc:  # broad: the project file is written; the export says the rest at its next run
                autosave.warn(host, self.t("tab_project"), self.t("pj_report_failed", error=exc))
            self.app.project_changed()
        self.ctx.dirty = False
        self.app.update_tab_marks()
        return True

    def state(self):
        """The title page typed and not saved, and the version, through a rebuilt window."""
        dirty = self.ctx.dirty
        return {"draft": {key: field.text() for key, field in self.fields.items()} if dirty else None,
                "version": self.version.currentData() if dirty else None}

    def restore(self, state):
        draft = state.get("draft")
        if draft:
            for key, value in draft.items():
                if key in self.fields:
                    self.fields[key].setText(value)
            if state.get("version") is not None:
                self.version.setCurrentIndex(max(0, self.version.findData(state["version"])))
            self.ctx.dirty = True


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


class _Receiver(QObject):
    """Where a preview's thread says it is done: a QObject of the window's thread, owned by the page, so that its slots run there -- a service is a plain object, and a signal tied to its method would not say in which thread it runs (ARCH-009)."""

    def __init__(self, parent, done, failed):
        super().__init__(parent)
        self._done, self._failed = done, failed

    @Slot(int, object, str)
    def done(self, generation, shown, mode):
        self._done(generation, shown, mode)

    @Slot(int, str, str)
    def failed(self, generation, code, message):
        self._failed(generation, code, message)


class ProjectTemplates(Service):
    """«Templates»: a document previewed with a content template and a form -- see the module's docstring."""

    NAME = "templates"
    ZONE = "page"
    IN_VIEWS = ("templates",)

    def mount(self, ctx):
        super().mount(ctx)
        self.lang = self.app.lang
        self.generation = 0
        self.workers = []
        provide = ctx.provide
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
        self.preview_form = form_combo(provide("forms")(), self.lang)
        self.preview_form.currentIndexChanged.connect(lambda _i: self.request_preview())
        for caption, combo in (("pj_preview_document", self.preview_document), ("pj_content", self.preview_content), ("pj_form_card", self.preview_form)):
            label = QLabel(self.t(caption))
            label.setWordWrap(True)
            column.addWidget(label)
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            combo.setMinimumContentsLength(6)
            column.addWidget(combo)
        self.preview_apply = QPushButton(self.t("pj_form_apply"))
        self.preview_apply.clicked.connect(lambda: provide("write_apply_form")(self.preview_form.currentData()))
        self.preview_create = QPushButton(self.t("pj_create"))
        self.preview_create.clicked.connect(lambda: provide("write_create_document")(self.preview_document.currentData(), self.preview_content.currentData()))
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
        self.receiver = _Receiver(self.splitter, self.on_preview_done, self.on_preview_failed)
        return self.splitter

    # --- the phases ----------------------------------------------------------------------

    def loaded(self):
        """The form in use chosen, and the document looked at listed again."""
        select_form(self.preview_form, forms.current(project.current()), self.ctx.provide("default_form")(), self.lang)
        self.on_preview_document()

    def lock(self):
        """«Appliquer au projet…» and «Créer le document…» off in a project opened read-only -- the second also for a document made."""
        here = project.current()
        writable = not self.ctx.read_only()
        self.preview_apply.setEnabled(writable)
        mode = self.preview_document.currentData()
        self.preview_create.setEnabled(writable and here.has_modes and mode is not None and not here.is_created(mode))

    def view_set(self, key, enter):
        """The view chosen: the preview built as it is shown, never while the window is built (`enter` False)."""
        if key == "templates" and enter and self.ctx.host.isVisible():
            self.request_preview()

    def revealed(self):
        if self.ctx.host.view == "templates":
            self.request_preview()

    def state(self):
        """The document looked at, through a rebuilt window."""
        return {"document": self.preview_document.currentData()}

    def restore(self, state):
        if state.get("document") is not None:
            self.preview_document.setCurrentIndex(max(0, self.preview_document.findData(state["document"])))

    # --- the preview -------------------------------------------------------------------

    def on_preview_document(self, _index=None):
        """Another document looked at: its content templates in the project's language, its own chosen where it was made from one."""
        here = project.current()
        mode = self.preview_document.currentData()
        self.preview_content.blockSignals(True)
        self.preview_content.clear()
        if mode is not None:
            for found in self.ctx.provide("templates_for")(mode, templates.project_language(here, fallback="")):
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
        host = self.ctx.host
        if host.view != "templates" or not host.isVisible():
            return
        mode = self.preview_document.currentData()
        if mode is None:
            return
        self.generation += 1
        self.preview_banner.setText(self.t("pj_preview_building"))
        self.preview_banner.show()
        worker = _Preview(self.generation, project.current(), mode, self.preview_content.currentData(), self.preview_form.currentData())
        worker.done.connect(self.receiver.done)
        worker.failed.connect(self.receiver.failed)
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
