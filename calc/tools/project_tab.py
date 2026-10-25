"""The «Projet» tab: the project's basic data, its templates and its documents, the first row of the navigation (issues #87, #88, #90; docs/ui/tab-project.md).

The engineer, 21.10.2026: «lorsque l'on passe de la convention d'utilisation à la base de projet ou au rapport de statique, l'onglet qui doit s'ouvrir […] c'est l'onglet projet. De cette manière, il n'y a pas de compilation automatique de tout le rapport en TYPST». It is where the window opens, and where every change of document brings it back: its first view compiles nothing.

**Two views.** «Informations» (`details`) -- cards: the title page, which the engineer types (the `.woodcore`'s name and DETAILS, read by `Project.detail`, written by `project.update`, and reported at once into data/project.json, export_all.refresh_project_info); the project's language, chosen as the project was created and shown greyed (templates.project_language); the form in use, common to the three documents, and «Appliquer au projet…» (home_page.apply_form); each document's content template (`Project.content_template`: «inconnu» for a project made before 0.122, «introuvable» where it is not on this machine) -- or, for a document not made yet, its choice and «Créer le document…» (project_template.create_document); the Woodcore version pinned; the three documents' folders with «Ouvrir le dossier»; the last export (project.last_export); «Ouvrir dans VS Code». «Templates» (`templates`) -- on the left the document, the content template and the form to look at; in the centre that document compiled with them and nothing of the project but its basic data (calc/template_preview.py), built off the window's thread, the last request alone counting. Choosing in a list changes the preview and nothing else.

**Built on the type «Document»** (document_tab.DocumentTab, issue #107): the class names its parameters only; what it shows and writes is three services (project_services.py) -- «Informations» (`ProjectDetails`), «Templates» (`ProjectTemplates`) and the acts both trigger (`ProjectActions`) --, joined by the type's context alone.

**Saving.** As every tab (autosave.py): the title page and the pinned version saved without a question when the tab is left, the document changed or the window left for another application, by Ctrl+S and by «Enregistrer»; «Annuler les modifications» reads the file again. Applying a form and creating a document are acts of their own, each confirmed. In a project opened read-only every field and button is off, and every writer is refused (the services' `WRITERS`, tab_guard.guard_service).

The tab's words, `pj_` (and `tpv_why_` for why a preview could not be made), in the window's three languages, are merged into woodcore_gui's STRINGS; it reuses the start page's `proj_` words for the title page's fields. It must not import woodcore_gui.
"""

from document_tab import DocumentTab
from project_services import ProjectActions, ProjectDetails, ProjectTemplates

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


class ProjectTab(DocumentTab):
    """The project's basic data, its templates and its documents (issues #87, #88, #90): a tab of the type «Document», its parameters only (issue #107)."""

    KEY = KEY
    VIEWS = ("details", "templates")
    SERVICES = (ProjectActions, ProjectDetails, ProjectTemplates)
    UNSAVED_WORDS = ("tab_project", "pj_title_card")
