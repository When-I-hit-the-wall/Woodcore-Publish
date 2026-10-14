"""*Fichier → Paramètres…* (Ctrl+,): Woodcore's own settings, and the templates a new project is made from (docs/ui/window.md §10quater, v0.94; one templates page and one «Enregistrer» since v0.113; the layout and the content templates told apart since 06.10.2026).

The engineer found the dialog unclear, and decided its shape in one message (v0.113); on 06.10.2026 he asked that the two kinds of template be told apart everywhere -- «on parle beaucoup de templates sans comprendre si on parle d'un template de forme ou de fond», and «modèle» is the wrong word for one. A side list of four pages, each opening on one sentence saying what it is for:

* **Templates** -- a first switch, **Forme | Fond**. A **layout template** («template de forme», calc/forms.py) is the look of a project's three documents: fonts, sizes, margins, how the headings and sections are set, the title page -- no data. A **content template** («template de fond», calc/doc_templates.py) is the sections, objects and texts of one document; under «Fond» a second switch chooses the document -- *Convention d'utilisation*, *Base de projet*, *Rapport de statique*, the report having content templates of its own since 06.10.2026. The project templates of v0.94 are gone from the dialog: a project is now made from one layout template and three content templates. In each list the templates are grouped by place -- «Intégrés», «Partagés» (the office's shared folder), «Mes templates» -- and the one chosen is shown **read only**: its name and description in the window's language, its languages, its place and its folder. *Supprimer* moves a template of the engineer's or of the office's into its place's `archives/`, never deletes it (a builtin one is read only, the button closed with its reason); *Ouvrir le dossier*; *Importer un dossier…* copies one template folder into «Mes templates» (`forms.import_folder`, `doc_templates.import_folder`), a template of that folder's name replaced on the engineer's word and archived; and, for the layout templates, *Enregistrer la forme de ce projet comme template de forme…* (`forms.save_from_project`, closed with its reason where no project is open). The shared folder and the engineer's own folder are chosen and opened on the same page.
* **Valeurs par défaut** -- the company, author and checker a new project starts with, and the layout template *Nouveau projet* offers first (the setting `forms.default`);
* **Langues** -- the window's language, and the report language *Nouveau projet* offers;
* **Apparence et mises à jour** -- *Fichier → Apparence*'s three choices, applied through theme.set_appearance itself, and the update check of an installed Woodcore, the very `updates.enabled` setting update_gui.py reads.

**One «Enregistrer» for the whole dialog, beside «Fermer».** A setting changed is held pending, and «Enregistrer» writes them all into the settings the rest of the window reads (usersettings.py), hands the window that opened the dialog its settings afresh -- a window that wrote its own copy afterwards would take them back --, applies the appearance and the window's language, and closes the dialog. «Fermer», Escape and the title bar's × close without writing, asking first where something is pending. What acts on files -- importing, deleting, saving a project's layout as a template, opening a folder -- is not a setting, and happens at once. The template lists read the settings as they will be, a shared folder chosen and not yet saved included.
"""

import collections
import copy
import os
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QBrush, QColor, QDesktopServices, QFont
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QRadioButton, QStackedWidget, QToolButton,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

import cards
import doc_templates
import documents
import forms
import templates
import theme
import usersettings
import notifications  # every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # what was a message box is a notice since v0.117 (notices_ui.tell)

LANGUAGES = ("fr", "de", "en")
LANGUAGE_NAMES = {"fr": "Français", "de": "Deutsch", "en": "English"}
PAGES = ("templates", "defaults", "languages", "appearance")
# What a caller written before v0.113 may still ask for: the two template pages are one, and the paths are on it.
PAGE_ALIASES = {"documents": "templates", "paths": "templates"}
# The two kinds of template, the first switch of the templates page: the look of the documents, and what one document says.
KINDS = ("form", "content")
# The three documents of the content templates' switch, in the order a project holds them.
DOCUMENTS = ("cu", "bp", "rs")
# The places of a template, in the order the page groups them: the builtin ones, the office's, the engineer's own.
GROUPS = ("builtin", "shared", "user")
SHORTCUT = "Ctrl+,"

STRINGS = {
    "fr": {
        "prefs_menu": "&Paramètres…",
        "prefs_title": "Paramètres",
        "prefs_page_templates": "Templates",
        "prefs_page_defaults": "Valeurs par défaut",
        "prefs_page_languages": "Langues",
        "prefs_page_appearance": "Apparence et mises à jour",
        "prefs_save": "Enregistrer",
        "prefs_save_tip": "Écrit tous les réglages modifiés et ferme la fenêtre.",
        "prefs_close": "Fermer",
        "prefs_unsaved_ask": "Enregistrer les modifications des paramètres ?",
        "prefs_templates_note": "Un projet est fait d'un template de forme — sa mise en page — et, pour chacun de ses trois documents, d'un template de fond — ce qu'il dit. Choisissez en haut le type de template.",
        "prefs_actions_note": "Importer, supprimer ou enregistrer un template agit tout de suite sur ses fichiers ; le dossier partagé, comme tout réglage, n'est écrit qu'à « Enregistrer ».",
        "prefs_kind_label": "Type de template",
        "prefs_kind_form": "Template de forme",
        "prefs_kind_content": "Template de fond",
        "prefs_kind_form_note": "Un template de forme règle la mise en page : polices, tailles, marges, titres, page de titre — aucune donnée. Dans un projet, il vit dans le dossier Template/ et son title.typ ; le config.typ ne garde que la langue et vos propres réglages.",
        "prefs_kind_content_note": "Un template de fond porte les sections, objets et textes d'un document : une convention d'utilisation longue ou courte, une base de projet pour le béton ou le bois, un rapport pour des plans de position ou un prédimensionnement…",
        "prefs_document_label": "Document",
        "prefs_place_builtin": "Intégrés",
        "prefs_place_user": "Mes templates",
        "prefs_place_shared": "Partagés",
        "prefs_place_missing": "{place} — dossier introuvable",
        "prefs_place_unset": "Aucun dossier partagé n'est choisi.",
        "prefs_place_empty": "Aucun template.",
        "prefs_col_name": "Nom",
        "prefs_col_languages": "Langues",
        "prefs_lang_any": "toutes",
        "prefs_default_mark": "{name}  (par défaut)",
        "prefs_card_details": "Template choisi",
        "prefs_detail_name": "Nom",
        "prefs_detail_description": "Description",
        "prefs_detail_languages": "Langues",
        "prefs_detail_place": "Emplacement",
        "prefs_detail_folder": "Dossier",
        "prefs_detail_broken": "Ce template ne peut pas servir : {error}",
        "prefs_pick": "Choisissez un template dans la liste.",
        "prefs_read_only": "Template intégré, en lecture seule : il ne peut pas être supprimé.",
        "prefs_delete": "Supprimer",
        "prefs_delete_ask": "Supprimer le template « {name} » ?\n\nIl est déplacé dans le dossier archives de son emplacement, jamais effacé.\n\n{folder}",
        "prefs_archived": "« {name} » a été déplacé dans les archives : {folder}",
        "prefs_open_folder": "Ouvrir le dossier",
        "prefs_import": "Importer un dossier…",
        "prefs_import_tip_form": "Copie dans « Mes templates » le dossier d'un template de forme, celui qui porte son form.json — par exemple l'un de ceux du dossier partagé.",
        "prefs_import_tip_content": "Copie dans « Mes templates » le dossier d'un template de fond du document choisi, celui qui porte son template.json — par exemple l'un de ceux du dossier partagé.",
        "prefs_import_title": "Dossier du template à importer",
        "prefs_import_replace_ask": "« Mes templates » contient déjà un template « {folder} ». Le remplacer ?\n\nL'ancien est déplacé dans les archives, jamais effacé.",
        "prefs_import_done": "« {name} » a été importé dans « Mes templates ».",
        "prefs_import_failed": "Le dossier n'a pas pu être importé :\n\n{error}",
        "prefs_save_form": "Enregistrer la forme de ce projet comme template de forme…",
        "prefs_save_form_tip": "Le dossier Template/ et le title.typ du projet ouvert deviennent un template de forme : sa mise en page, sans aucune donnée.",
        "prefs_no_project": "Aucun projet n'est ouvert.",
        "prefs_name_title": "Nom du template",
        "prefs_name_label": "Nom :",
        "prefs_place_label": "Enregistrer dans :",
        "prefs_saved_form": "« {name} » a été enregistré comme template de forme.",
        "prefs_failed": "Le template n'a pas pu être écrit ni déplacé :\n\n{error}",
        "prefs_card_folders": "Dossiers des templates",
        "prefs_shared_folder": "Dossier partagé du bureau",
        "prefs_shared_note": "Un dossier que le bureau partage — sur NextCloud, un lecteur réseau : ses templates de forme dans forms/, ses templates de fond dans documents/.",
        "prefs_choose_shared": "Choisir le dossier partagé…",
        "prefs_clear": "Effacer",
        "prefs_user_folder": "Mes templates",
        "prefs_defaults_page_note": "Ce qu'un nouveau projet reçoit : le bureau, l'auteur et le vérificateur de ses rapports, et le template de forme proposé en premier.",
        "prefs_card_people": "Personnes",
        "prefs_company": "Bureau",
        "prefs_author": "Auteur",
        "prefs_checker": "Vérificateur",
        "prefs_default_form": "Template de forme proposé en premier",
        "prefs_default_form_note": "La mise en page qu'un nouveau projet reçoit si on ne lui en choisit pas d'autre.",
        "prefs_languages_page_note": "La langue de cette fenêtre, et celle du rapport que « Nouveau projet » propose. La fenêtre change de langue à l'enregistrement.",
        "prefs_card_window": "Fenêtre",
        "prefs_window_language": "Langue de la fenêtre",
        "prefs_card_new_projects": "Nouveaux projets",
        "prefs_new_report_language": "Langue du rapport des nouveaux projets",
        "prefs_new_report_language_tip": "Celle que « Nouveau projet » choisit d'abord : les templates de fond proposés sont ceux qui existent dans cette langue.",
        "prefs_appearance_page_note": "L'aspect de Woodcore — clair, sombre ou comme Windows — et la recherche de ses nouvelles versions.",
        "prefs_appearance": "Apparence",
        "prefs_updates_title": "Mises à jour",
        "prefs_updates": "Chercher au démarrage si une nouvelle version de Woodcore est publiée",
        "prefs_updates_note": "Seul un Woodcore installé la cherche ; lancé depuis ses sources, il ne demande rien.",
        "prefs_form_err_bad_place": "« {place} » n'est pas un emplacement de templates de forme : intégrés, mes templates ou partagés.",
        "prefs_form_err_no_shared_folder": "Aucun dossier de templates partagés n'est défini (Paramètres → Templates).",
        "prefs_form_err_read_only": "Un template de forme intégré est en lecture seule : il ne peut être ni remplacé ni supprimé.",
        "prefs_form_err_no_such_form": "Aucun template de forme ne s'appelle « {ref} ».",
        "prefs_form_err_form_unusable": "Le template de forme {ref} ne peut pas servir : {error}",
        "prefs_form_err_no_project_form": "Ce projet n'a pas de dossier Template/ ni de title.typ : sa mise en page est le config.typ d'une version précédente, qui n'est pas un template de forme. Choisissez d'abord un template de forme dans ses propriétés.",
        "prefs_form_err_no_name": "Un template de forme a besoin d'un nom.",
        "prefs_form_err_name_is_builtin": "« {name} » est le nom d'un template de forme intégré : choisissez-en un autre.",
        "prefs_form_err_not_a_folder": "{folder} n'est pas un dossier.",
        "prefs_form_err_no_form": "Le dossier {folder} ne porte pas de form.json : ce n'est pas un template de forme. Choisissez le dossier du template lui-même.",
        "prefs_form_err_invalid": "Le template de forme n'est pas valable : {error}",
        "prefs_form_err_already_mine": "Ce dossier est déjà parmi vos templates de forme.",
        "prefs_form_err_exists": "« Mes templates » contient déjà un template de forme « {folder} ».",
        "prefs_form_err_write_failed": "Le template de forme n'a pas pu être écrit ni déplacé : {error}",
        "prefs_doc_err_bad_mode": "« {mode} » n'est pas un document dont on fait un template de fond : la convention d'utilisation (cu), la base de projet (bp) ou le rapport de statique (rs).",
        "prefs_doc_err_bad_language": "« {language} » n'est pas une langue de Woodcore : fr, de ou en.",
        "prefs_doc_err_bad_place": "« {place} » n'est pas un emplacement de templates : intégrés, mes templates ou partagés.",
        "prefs_doc_err_bad_folder": "« {folder} » ne peut pas nommer le dossier d'un template : un seul dossier, sans rien de ce que Windows refuse dans un nom.",
        "prefs_doc_err_read_only": "Un template de fond intégré est en lecture seule : il ne peut être ni remplacé ni supprimé. Enregistrez-en un parmi vos templates ou ceux du bureau.",
        "prefs_doc_err_no_folder": "Aucun dossier de templates partagés n'est défini (Paramètres → Templates).",
        "prefs_doc_err_place_taken": "Ce dossier est celui d'un template de projet d'une version précédente : des templates de fond ne peuvent pas y être rangés.",
        "prefs_doc_err_no_such_document": "Le projet n'a pas ce document : seul un projet organisé en trois documents en a trois.",
        "prefs_doc_err_no_entry": "Le fichier d'entrée de ce document n'existe pas.",
        "prefs_doc_err_structure_unreadable": "La structure de ce document (structure.json) ne peut pas être lue.",
        "prefs_doc_err_section_missing": "La structure nomme des fichiers de sections qui n'existent pas : {files}.",
        "prefs_doc_err_entry_unreadable": "Le fichier d'entrée {file} doit porter exactement un bloc woodcore:structure sans balise défectueuse.",
        "prefs_doc_err_no_name": "Un template de fond a besoin d'un nom, dans la langue du document.",
        "prefs_doc_err_name_is_builtin": "« {name} » est le nom d'un template de fond intégré : choisissez-en un autre.",
        "prefs_doc_err_name_taken": "{ref} porte déjà ce nom : un nom doit désigner un seul template.",
        "prefs_doc_err_exists": "{ref} existe déjà : l'enregistrer par-dessus doit être confirmé.",
        "prefs_doc_err_not_a_template": "Le dossier {folder} n'est pas un template de fond : il n'est pas écrasé.",
        "prefs_doc_err_mode_mismatch": "Ce template de fond est celui d'un autre document.",
        "prefs_doc_err_no_such_template": "Aucun template de fond n'est nommé « {name} ».",
        "prefs_doc_err_template_unusable": "Le template de fond {ref} ne peut pas servir : il est défectueux.",
        "prefs_doc_err_language_missing": "{ref} existe en {languages} et pas en {language}.",
        "prefs_doc_err_invalid": "Le template de fond n'est pas valable : {error}",
        "prefs_doc_err_write_failed": "Le template de fond n'a pas pu être écrit ni déplacé : {error}",
        "prefs_doc_err_not_a_folder": "{folder} n'est pas un dossier.",
        "prefs_doc_err_no_template": "Le dossier {folder} ne porte pas de template.json : ce n'est pas un template de fond. Choisissez le dossier du template lui-même.",
        "prefs_doc_err_project_template": "Le dossier {folder} est un template de projet d'une version précédente : ce n'est ni un template de forme ni un template de fond.",
        "prefs_doc_err_already_mine": "Ce dossier est déjà parmi vos templates.",
    },
    "de": {
        "prefs_menu": "&Einstellungen…",
        "prefs_title": "Einstellungen",
        "prefs_page_templates": "Vorlagen",
        "prefs_page_defaults": "Standardwerte",
        "prefs_page_languages": "Sprachen",
        "prefs_page_appearance": "Darstellung und Updates",
        "prefs_save": "Speichern",
        "prefs_save_tip": "Schreibt alle geänderten Einstellungen und schliesst das Fenster.",
        "prefs_close": "Schliessen",
        "prefs_unsaved_ask": "Die Änderungen an den Einstellungen speichern?",
        "prefs_templates_note": "Ein Projekt wird aus einer Formvorlage gemacht — seinem Layout — und, für jedes seiner drei Dokumente, aus einer Inhaltsvorlage — dem, was es sagt. Oben den Vorlagentyp wählen.",
        "prefs_actions_note": "Eine Vorlage importieren, löschen oder speichern wirkt sofort auf ihre Dateien; der geteilte Ordner wird, wie jede Einstellung, erst mit «Speichern» geschrieben.",
        "prefs_kind_label": "Vorlagentyp",
        "prefs_kind_form": "Formvorlage",
        "prefs_kind_content": "Inhaltsvorlage",
        "prefs_kind_form_note": "Eine Formvorlage regelt das Layout: Schriften, Grössen, Ränder, Titel, Titelseite — keine Daten. In einem Projekt lebt sie im Ordner Template/ und ihrer title.typ; die config.typ behält nur die Sprache und die eigenen Einstellungen.",
        "prefs_kind_content_note": "Eine Inhaltsvorlage trägt die Abschnitte, Objekte und Texte eines Dokuments: eine lange oder kurze Nutzungsvereinbarung, eine Projektbasis für Beton oder Holz, einen Bericht für Positionspläne oder eine Vorbemessung…",
        "prefs_document_label": "Dokument",
        "prefs_place_builtin": "Integriert",
        "prefs_place_user": "Meine Vorlagen",
        "prefs_place_shared": "Geteilt",
        "prefs_place_missing": "{place} — Ordner nicht gefunden",
        "prefs_place_unset": "Es ist kein geteilter Ordner gewählt.",
        "prefs_place_empty": "Keine Vorlage.",
        "prefs_col_name": "Name",
        "prefs_col_languages": "Sprachen",
        "prefs_lang_any": "alle",
        "prefs_default_mark": "{name}  (Standard)",
        "prefs_card_details": "Gewählte Vorlage",
        "prefs_detail_name": "Name",
        "prefs_detail_description": "Beschreibung",
        "prefs_detail_languages": "Sprachen",
        "prefs_detail_place": "Ort",
        "prefs_detail_folder": "Ordner",
        "prefs_detail_broken": "Diese Vorlage ist unbrauchbar: {error}",
        "prefs_pick": "Eine Vorlage in der Liste wählen.",
        "prefs_read_only": "Integrierte Vorlage, schreibgeschützt: sie kann nicht gelöscht werden.",
        "prefs_delete": "Löschen",
        "prefs_delete_ask": "Die Vorlage «{name}» löschen?\n\nSie wird in den Ordner archives ihres Orts verschoben, nie gelöscht.\n\n{folder}",
        "prefs_archived": "«{name}» wurde ins Archiv verschoben: {folder}",
        "prefs_open_folder": "Ordner öffnen",
        "prefs_import": "Ordner importieren…",
        "prefs_import_tip_form": "Kopiert den Ordner einer Formvorlage, den mit ihrer form.json, in «Meine Vorlagen» — zum Beispiel einen aus dem geteilten Ordner.",
        "prefs_import_tip_content": "Kopiert den Ordner einer Inhaltsvorlage des gewählten Dokuments, den mit ihrer template.json, in «Meine Vorlagen» — zum Beispiel einen aus dem geteilten Ordner.",
        "prefs_import_title": "Ordner der zu importierenden Vorlage",
        "prefs_import_replace_ask": "«Meine Vorlagen» enthält schon eine Vorlage «{folder}». Sie ersetzen?\n\nDie alte wird ins Archiv verschoben, nie gelöscht.",
        "prefs_import_done": "«{name}» wurde in «Meine Vorlagen» importiert.",
        "prefs_import_failed": "Der Ordner konnte nicht importiert werden:\n\n{error}",
        "prefs_save_form": "Das Layout dieses Projekts als Formvorlage speichern…",
        "prefs_save_form_tip": "Der Ordner Template/ und die title.typ des offenen Projekts werden eine Formvorlage: sein Layout, ohne jede Daten.",
        "prefs_no_project": "Es ist kein Projekt geöffnet.",
        "prefs_name_title": "Name der Vorlage",
        "prefs_name_label": "Name:",
        "prefs_place_label": "Speichern in:",
        "prefs_saved_form": "«{name}» wurde als Formvorlage gespeichert.",
        "prefs_failed": "Die Vorlage konnte weder geschrieben noch verschoben werden:\n\n{error}",
        "prefs_card_folders": "Ordner der Vorlagen",
        "prefs_shared_folder": "Geteilter Ordner des Büros",
        "prefs_shared_note": "Ein Ordner, den das Büro teilt — auf NextCloud, einem Netzlaufwerk: seine Formvorlagen in forms/, seine Inhaltsvorlagen in documents/.",
        "prefs_choose_shared": "Geteilten Ordner wählen…",
        "prefs_clear": "Leeren",
        "prefs_user_folder": "Meine Vorlagen",
        "prefs_defaults_page_note": "Was ein neues Projekt erhält: das Büro, der Verfasser und der Prüfer seiner Berichte, und die zuerst angebotene Formvorlage.",
        "prefs_card_people": "Personen",
        "prefs_company": "Büro",
        "prefs_author": "Verfasser",
        "prefs_checker": "Prüfer",
        "prefs_default_form": "Zuerst angebotene Formvorlage",
        "prefs_default_form_note": "Das Layout, das ein neues Projekt erhält, wenn ihm kein anderes gewählt wird.",
        "prefs_languages_page_note": "Die Sprache dieses Fensters, und die des Berichts, die «Neues Projekt» anbietet. Das Fenster wechselt die Sprache beim Speichern.",
        "prefs_card_window": "Fenster",
        "prefs_window_language": "Sprache des Fensters",
        "prefs_card_new_projects": "Neue Projekte",
        "prefs_new_report_language": "Berichtssprache neuer Projekte",
        "prefs_new_report_language_tip": "Die, die «Neues Projekt» zuerst wählt: angeboten werden die Inhaltsvorlagen, die es in dieser Sprache gibt.",
        "prefs_appearance_page_note": "Das Aussehen von Woodcore — hell, dunkel oder wie Windows — und die Suche nach seinen neuen Versionen.",
        "prefs_appearance": "Darstellung",
        "prefs_updates_title": "Aktualisierungen",
        "prefs_updates": "Beim Start prüfen, ob eine neue Version von Woodcore veröffentlicht ist",
        "prefs_updates_note": "Nur ein installiertes Woodcore prüft das; aus seinen Quellen gestartet, fragt es nichts.",
        "prefs_form_err_bad_place": "«{place}» ist kein Ort für Formvorlagen: integriert, meine Vorlagen oder geteilt.",
        "prefs_form_err_no_shared_folder": "Es ist kein Ordner geteilter Vorlagen festgelegt (Einstellungen → Vorlagen).",
        "prefs_form_err_read_only": "Eine integrierte Formvorlage ist schreibgeschützt: sie kann weder ersetzt noch gelöscht werden.",
        "prefs_form_err_no_such_form": "Keine Formvorlage heisst «{ref}».",
        "prefs_form_err_form_unusable": "Die Formvorlage {ref} ist unbrauchbar: {error}",
        "prefs_form_err_no_project_form": "Dieses Projekt hat keinen Ordner Template/ und keine title.typ: sein Layout ist die config.typ einer früheren Version, die keine Formvorlage ist. Zuerst in seinen Eigenschaften eine Formvorlage wählen.",
        "prefs_form_err_no_name": "Eine Formvorlage braucht einen Namen.",
        "prefs_form_err_name_is_builtin": "«{name}» ist der Name einer integrierten Formvorlage: einen anderen wählen.",
        "prefs_form_err_not_a_folder": "{folder} ist kein Ordner.",
        "prefs_form_err_no_form": "Der Ordner {folder} trägt keine form.json: er ist keine Formvorlage. Den Ordner der Vorlage selbst wählen.",
        "prefs_form_err_invalid": "Die Formvorlage ist ungültig: {error}",
        "prefs_form_err_already_mine": "Dieser Ordner ist schon unter den eigenen Formvorlagen.",
        "prefs_form_err_exists": "«Meine Vorlagen» enthält schon eine Formvorlage «{folder}».",
        "prefs_form_err_write_failed": "Die Formvorlage konnte weder geschrieben noch verschoben werden: {error}",
        "prefs_doc_err_bad_mode": "«{mode}» ist kein Dokument, aus dem man eine Inhaltsvorlage macht: die Nutzungsvereinbarung (cu), die Projektbasis (bp) oder der statische Bericht (rs).",
        "prefs_doc_err_bad_language": "«{language}» ist keine Sprache von Woodcore: fr, de oder en.",
        "prefs_doc_err_bad_place": "«{place}» ist kein Ort für Vorlagen: integriert, meine Vorlagen oder geteilt.",
        "prefs_doc_err_bad_folder": "«{folder}» kann den Ordner einer Vorlage nicht benennen: ein einziger Ordner, ohne etwas, das Windows in einem Namen verweigert.",
        "prefs_doc_err_read_only": "Eine integrierte Inhaltsvorlage ist schreibgeschützt: sie kann weder ersetzt noch gelöscht werden. Eine unter den eigenen oder den Vorlagen des Büros speichern.",
        "prefs_doc_err_no_folder": "Es ist kein Ordner geteilter Vorlagen festgelegt (Einstellungen → Vorlagen).",
        "prefs_doc_err_place_taken": "Dieser Ordner ist der einer Projektvorlage einer früheren Version: Inhaltsvorlagen können dort nicht abgelegt werden.",
        "prefs_doc_err_no_such_document": "Das Projekt hat dieses Dokument nicht: nur ein in drei Dokumente gegliedertes Projekt hat drei.",
        "prefs_doc_err_no_entry": "Die Einstiegsdatei dieses Dokuments gibt es nicht.",
        "prefs_doc_err_structure_unreadable": "Die Struktur dieses Dokuments (structure.json) kann nicht gelesen werden.",
        "prefs_doc_err_section_missing": "Die Struktur nennt Abschnittsdateien, die es nicht gibt: {files}.",
        "prefs_doc_err_entry_unreadable": "Die Einstiegsdatei {file} muss genau einen woodcore:structure-Block ohne defekte Marke tragen.",
        "prefs_doc_err_no_name": "Eine Inhaltsvorlage braucht einen Namen in der Sprache des Dokuments.",
        "prefs_doc_err_name_is_builtin": "«{name}» ist der Name einer integrierten Inhaltsvorlage: einen anderen wählen.",
        "prefs_doc_err_name_taken": "{ref} heisst schon so: ein Name muss genau eine Vorlage bezeichnen.",
        "prefs_doc_err_exists": "{ref} gibt es schon: sie zu überschreiben muss bestätigt werden.",
        "prefs_doc_err_not_a_template": "Der Ordner {folder} ist keine Inhaltsvorlage: er wird nicht überschrieben.",
        "prefs_doc_err_mode_mismatch": "Diese Inhaltsvorlage gehört zu einem anderen Dokument.",
        "prefs_doc_err_no_such_template": "Keine Inhaltsvorlage heisst «{name}».",
        "prefs_doc_err_template_unusable": "Die Inhaltsvorlage {ref} ist unbrauchbar: sie ist defekt.",
        "prefs_doc_err_language_missing": "{ref} gibt es auf {languages} und nicht auf {language}.",
        "prefs_doc_err_invalid": "Die Inhaltsvorlage ist ungültig: {error}",
        "prefs_doc_err_write_failed": "Die Inhaltsvorlage konnte nicht geschrieben oder verschoben werden: {error}",
        "prefs_doc_err_not_a_folder": "{folder} ist kein Ordner.",
        "prefs_doc_err_no_template": "Der Ordner {folder} trägt keine template.json: er ist keine Inhaltsvorlage. Den Ordner der Vorlage selbst wählen.",
        "prefs_doc_err_project_template": "Der Ordner {folder} ist eine Projektvorlage einer früheren Version: weder eine Formvorlage noch eine Inhaltsvorlage.",
        "prefs_doc_err_already_mine": "Dieser Ordner ist schon unter den eigenen Vorlagen.",
    },
    "en": {
        "prefs_menu": "&Settings…",
        "prefs_title": "Settings",
        "prefs_page_templates": "Templates",
        "prefs_page_defaults": "Defaults",
        "prefs_page_languages": "Languages",
        "prefs_page_appearance": "Appearance and updates",
        "prefs_save": "Save",
        "prefs_save_tip": "Writes every setting changed and closes the window.",
        "prefs_close": "Close",
        "prefs_unsaved_ask": "Save the changes to the settings?",
        "prefs_templates_note": "A project is made of a layout template — how it looks — and, for each of its three documents, a content template — what it says. Choose the kind of template at the top.",
        "prefs_actions_note": "Importing, deleting or saving a template acts on its files at once; the shared folder, like every setting, is written only by “Save”.",
        "prefs_kind_label": "Kind of template",
        "prefs_kind_form": "Layout template",
        "prefs_kind_content": "Content template",
        "prefs_kind_form_note": "A layout template sets how the documents look: fonts, sizes, margins, headings, title page — no data. In a project it lives in the folder Template/ and its title.typ; config.typ keeps only the language and your own adjustments.",
        "prefs_kind_content_note": "A content template holds the sections, objects and texts of one document: a long or a short service criteria agreement, a basis of design for concrete or timber, a report for position plans or a preliminary design…",
        "prefs_document_label": "Document",
        "prefs_place_builtin": "Built-in",
        "prefs_place_user": "My templates",
        "prefs_place_shared": "Shared",
        "prefs_place_missing": "{place} — folder not found",
        "prefs_place_unset": "No shared folder is chosen.",
        "prefs_place_empty": "No template.",
        "prefs_col_name": "Name",
        "prefs_col_languages": "Languages",
        "prefs_lang_any": "any",
        "prefs_default_mark": "{name}  (default)",
        "prefs_card_details": "Chosen template",
        "prefs_detail_name": "Name",
        "prefs_detail_description": "Description",
        "prefs_detail_languages": "Languages",
        "prefs_detail_place": "Place",
        "prefs_detail_folder": "Folder",
        "prefs_detail_broken": "This template cannot be used: {error}",
        "prefs_pick": "Choose a template in the list.",
        "prefs_read_only": "Built-in template, read-only: it cannot be deleted.",
        "prefs_delete": "Delete",
        "prefs_delete_ask": "Delete the template “{name}”?\n\nIt is moved into the archives folder of its place, never erased.\n\n{folder}",
        "prefs_archived": "“{name}” was moved into the archives: {folder}",
        "prefs_open_folder": "Open the folder",
        "prefs_import": "Import a folder…",
        "prefs_import_tip_form": "Copies a layout template's folder, the one holding its form.json, into “My templates” — one of the shared folder's, for instance.",
        "prefs_import_tip_content": "Copies the folder of a content template of the document chosen, the one holding its template.json, into “My templates” — one of the shared folder's, for instance.",
        "prefs_import_title": "Folder of the template to import",
        "prefs_import_replace_ask": "“My templates” holds a template “{folder}” already. Replace it?\n\nThe old one is moved into the archives, never erased.",
        "prefs_import_done": "“{name}” was imported into “My templates”.",
        "prefs_import_failed": "The folder could not be imported:\n\n{error}",
        "prefs_save_form": "Save this project's layout as a layout template…",
        "prefs_save_form_tip": "The open project's Template/ folder and title.typ become a layout template: its look, with no data at all.",
        "prefs_no_project": "No project is open.",
        "prefs_name_title": "Template name",
        "prefs_name_label": "Name:",
        "prefs_place_label": "Save in:",
        "prefs_saved_form": "“{name}” was saved as a layout template.",
        "prefs_failed": "The template could not be written or moved:\n\n{error}",
        "prefs_card_folders": "Template folders",
        "prefs_shared_folder": "The office's shared folder",
        "prefs_shared_note": "A folder the office shares — on NextCloud, a network drive: its layout templates in forms/, its content templates in documents/.",
        "prefs_choose_shared": "Choose the shared folder…",
        "prefs_clear": "Clear",
        "prefs_user_folder": "My templates",
        "prefs_defaults_page_note": "What a new project is given: the office, the author and the checker of its reports, and the layout template offered first.",
        "prefs_card_people": "People",
        "prefs_company": "Office",
        "prefs_author": "Author",
        "prefs_checker": "Checker",
        "prefs_default_form": "Layout template offered first",
        "prefs_default_form_note": "The look a new project is given where no other is chosen for it.",
        "prefs_languages_page_note": "The language of this window, and the report language “New project” offers. The window changes its language when the settings are saved.",
        "prefs_card_window": "Window",
        "prefs_window_language": "Window language",
        "prefs_card_new_projects": "New projects",
        "prefs_new_report_language": "Report language of new projects",
        "prefs_new_report_language_tip": "The one “New project” chooses first: the content templates offered are those that exist in that language.",
        "prefs_appearance_page_note": "How Woodcore looks — light, dark or as Windows does — and the search for its new versions.",
        "prefs_appearance": "Appearance",
        "prefs_updates_title": "Updates",
        "prefs_updates": "Look at start whether a new version of Woodcore is published",
        "prefs_updates_note": "Only an installed Woodcore looks; started from its sources, it asks nothing.",
        "prefs_form_err_bad_place": "“{place}” is not a place of layout templates: built-in, my templates or shared.",
        "prefs_form_err_no_shared_folder": "No folder of shared templates is set (Settings → Templates).",
        "prefs_form_err_read_only": "A built-in layout template is read-only: it can be neither replaced nor deleted.",
        "prefs_form_err_no_such_form": "No layout template is called “{ref}”.",
        "prefs_form_err_form_unusable": "The layout template {ref} cannot be used: {error}",
        "prefs_form_err_no_project_form": "This project has no Template/ folder and no title.typ: its look is the config.typ of an earlier version, which is no layout template. Choose a layout template in its properties first.",
        "prefs_form_err_no_name": "A layout template needs a name.",
        "prefs_form_err_name_is_builtin": "“{name}” is the name of a built-in layout template: choose another.",
        "prefs_form_err_not_a_folder": "{folder} is not a folder.",
        "prefs_form_err_no_form": "The folder {folder} holds no form.json: it is no layout template. Choose the template's own folder.",
        "prefs_form_err_invalid": "The layout template is not valid: {error}",
        "prefs_form_err_already_mine": "That folder is among your layout templates already.",
        "prefs_form_err_exists": "“My templates” holds a layout template “{folder}” already.",
        "prefs_form_err_write_failed": "The layout template could not be written or moved: {error}",
        "prefs_doc_err_bad_mode": "“{mode}” is not a document a content template is made of: the service criteria agreement (cu), the basis of design (bp) or the statical report (rs).",
        "prefs_doc_err_bad_language": "“{language}” is not a language of Woodcore: fr, de or en.",
        "prefs_doc_err_bad_place": "“{place}” is not a place of templates: built-in, my templates or shared.",
        "prefs_doc_err_bad_folder": "“{folder}” cannot name a template's folder: one folder, with nothing Windows refuses in a name.",
        "prefs_doc_err_read_only": "A built-in content template is read-only: it can be neither replaced nor deleted. Save one among your own or the office's.",
        "prefs_doc_err_no_folder": "No folder of shared templates is set (Settings → Templates).",
        "prefs_doc_err_place_taken": "That folder is a project template's of an earlier version: content templates cannot be kept there.",
        "prefs_doc_err_no_such_document": "The project has no such document: only a project laid out in three documents has three.",
        "prefs_doc_err_no_entry": "The entry file of that document is not there.",
        "prefs_doc_err_structure_unreadable": "The structure of that document (structure.json) cannot be read.",
        "prefs_doc_err_section_missing": "The structure names section files that are not there: {files}.",
        "prefs_doc_err_entry_unreadable": "The entry file {file} must carry exactly one woodcore:structure block with no faulty tag.",
        "prefs_doc_err_no_name": "A content template needs a name, in the document's language.",
        "prefs_doc_err_name_is_builtin": "“{name}” is the name of a built-in content template: choose another.",
        "prefs_doc_err_name_taken": "{ref} is called that already: a name must mean one template.",
        "prefs_doc_err_exists": "{ref} is there already: saving over it has to be confirmed.",
        "prefs_doc_err_not_a_template": "The folder {folder} is no content template: it is not written over.",
        "prefs_doc_err_mode_mismatch": "That content template belongs to another document.",
        "prefs_doc_err_no_such_template": "No content template is called “{name}”.",
        "prefs_doc_err_template_unusable": "The content template {ref} cannot be used: it is faulty.",
        "prefs_doc_err_language_missing": "{ref} exists in {languages} and not in {language}.",
        "prefs_doc_err_invalid": "The content template is not valid: {error}",
        "prefs_doc_err_write_failed": "The content template could not be written or moved: {error}",
        "prefs_doc_err_not_a_folder": "{folder} is not a folder.",
        "prefs_doc_err_no_template": "The folder {folder} holds no template.json: it is no content template. Choose the template's own folder.",
        "prefs_doc_err_project_template": "The folder {folder} is a project template of an earlier version: neither a layout template nor a content template.",
        "prefs_doc_err_already_mine": "That folder is among your templates already.",
    },
}

for _lang in LANGUAGES[1:]:
    assert set(STRINGS[_lang]) == set(STRINGS["fr"]), f"settings_dialog.STRINGS[{_lang!r}] does not carry the same keys as French"

# The appearance words are *Fichier → Apparence*'s own, which home_page.py carries: read from there rather than written a second time.
APPEARANCE_KEYS = {"system": "file_appearance_system", "light": "file_appearance_light", "dark": "file_appearance_dark"}


def t(lang, key, **values):
    text = STRINGS[lang if lang in STRINGS else "fr"][key]
    return text.format(**values) if values else text


def _plain(text):
    """A menu's words without the & of their shortcut."""
    return text.replace("&", "")


def place_label(lang, place):
    """The words for a template's place -- builtin, user, or the office's -- in `lang`: the office's place is `office` for a content template (calc/doc_templates.py) and `shared` for a layout template (calc/forms.py), and both read «Partagés»."""
    return t(lang, f"prefs_place_{'shared' if place in ('office', 'shared') else place}")


def default_form_ref(settings):
    """The layout template «Nouveau projet» offers first: calc/forms.py's own `default_ref` where it has one, else the settings' `forms.default`, else builtin neutral."""
    own = getattr(forms, "default_ref", None)
    if own is not None:
        return own(settings)
    prefs = settings.get("forms") if isinstance(settings, dict) else None
    ref = prefs.get("default") if isinstance(prefs, dict) else None
    return ref if isinstance(ref, str) and ref.strip() else f"builtin:{forms.NEUTRAL}"


def _values(lang, exc):
    """The values a refusal states, as its sentence writes them: a list as its items, a document's code as its name in `lang`, a value it has none of left empty, `error` the English sentence where it states no other."""
    values = collections.defaultdict(str, error=str(exc))
    for name, value in (getattr(exc, "values", None) or {}).items():
        if isinstance(value, (list, tuple)):
            value = ", ".join(map(str, value))
        elif name == "document" and value in documents.MODE_NAMES["en"]:
            value = documents.mode_name(value, lang)
        values[name] = value
    return values


def _coded(lang, exc, key):
    """The sentence `key` of a refusal, with the values it states -- the English sentence where the exception states no code or the table has no such key."""
    if not getattr(exc, "code", "") or key not in STRINGS["fr"]:
        return str(exc)
    return t(lang, key).format_map(_values(lang, exc))


def doc_error_text(lang, exc):
    """A DocTemplateError's refusal in `lang`, by the `code` it states (doc_templates.CODES) with the `values` it is about -- a list written as its items, a value the refusal has none of left empty, `error` the English sentence where it states no other. The English sentence itself where the exception states no code, or one this table does not know: a window never says nothing."""
    return _coded(lang, exc, f"prefs_doc_err_{getattr(exc, 'code', '')}")


def form_error_text(lang, exc):
    """A FormError's refusal in `lang`, by the `code` it states (forms.CODES), as `doc_error_text` says a content template's."""
    return _coded(lang, exc, f"prefs_form_err_{getattr(exc, 'code', '')}")


def import_error_text(lang, exc):
    """A refusal of `forms.import_folder` (a FormError) or of `doc_templates.import_folder` (a DocTemplateError) in `lang`, by its code; the English sentence where it states none this table knows."""
    if isinstance(exc, forms.FormError):
        return form_error_text(lang, exc)
    return doc_error_text(lang, exc)


def apply_setting(settings, section, key, value):
    """`settings` with one setting written -- `section` a dict of the settings (`defaults`, `templates`, `forms`, `updates`), or None for a key at the top -- a value None or "" taken out, and a section left empty taken out with it. Returns `settings`, changed in place."""
    if section is None:
        target = settings
    else:
        target = dict(settings.get(section)) if isinstance(settings.get(section), dict) else {}
    if value is None or value == "":
        target.pop(key, None)
    else:
        target[key] = value
    if section is not None:
        if target:
            settings[section] = target
        else:
            settings.pop(section, None)
    return settings


def setting_of(settings, section, key):
    """One setting as `settings` hold it, None where they hold none."""
    holder = settings if section is None else settings.get(section)
    return holder.get(key) if isinstance(holder, dict) else None


def store(parent, section, key, value):
    """One setting written at once as the settings stand on disk, and the window `parent` handed the settings afresh, so a window writing its own copy later does not take this back -- what an action on files changes in the settings (a default template archived), which waits for no «Enregistrer»."""
    settings = apply_setting(usersettings.read(), section, key, value)
    usersettings.write(settings)
    if parent is not None and hasattr(parent, "settings"):
        parent.settings = usersettings.read()
    return settings


class NameDialog(QDialog):
    """A template's name, and -- where the office shares a folder of templates -- the place it goes into."""

    def __init__(self, parent, lang, name, places):
        super().__init__(parent)
        self.setWindowTitle(t(lang, "prefs_name_title"))
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name = QLineEdit(name)
        self.name.selectAll()
        form.addRow(t(lang, "prefs_name_label"), self.name)
        self.place = QComboBox()
        for place in places:
            self.place.addItem(place_label(lang, place), place)
        if len(places) > 1:
            form.addRow(t(lang, "prefs_place_label"), self.place)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setMinimumWidth(420)

    def values(self):
        return self.name.text().strip(), self.place.currentData() or "user"


def _segments(labels, chosen, on_click):
    """A row of the site's segmented control (theme.py): one checkable QToolButton per (key, text) of `labels`, `chosen` checked, `on_click(key)` on a click. Returns (layout, group, {key: button})."""
    row = QHBoxLayout()
    row.setSpacing(0)
    group = QButtonGroup()
    group.setExclusive(True)
    buttons = {}
    keys = [key for key, _text in labels]
    for index, (key, text) in enumerate(labels):
        button = QToolButton()
        button.setText(text)
        button.setCheckable(True)
        button.setProperty("segment", "first" if index == 0 else "last" if index == len(labels) - 1 else "middle")
        button.setChecked(key == chosen)
        group.addButton(button, index)
        buttons[key] = button
        row.addWidget(button)
    row.addStretch(1)
    group.idClicked.connect(lambda index: on_click(keys[index]))
    return row, group, buttons


class SettingsDialog(QDialog):
    """The dialog: the side list of PAGES and a page each, «Enregistrer» and «Fermer» under them. `here` is the project the window has open -- what «Enregistrer la forme de ce projet» takes -- None from the start page. `kind` is the kind of template the templates page opens on (`form` or `content`), `document` the document its content templates are of."""

    def __init__(self, parent=None, lang="fr", here=None, page="templates", document="cu", kind=None):
        super().__init__(parent)
        theme.ensure()
        self.window_ = parent
        self.lang = lang if lang in LANGUAGES else "fr"
        self.here = here
        self.document = document if document in DOCUMENTS else DOCUMENTS[0]
        self.kind = kind if kind in KINDS else "form"
        self.pending = {}                 # {(section, key): value} -- the settings changed and not yet written
        self.pending_lang = None          # the window's language chosen, applied through the window's own switch on «Enregistrer»
        self.pending_appearance = None    # *Fichier → Apparence*'s choice, applied through theme.set_appearance on «Enregistrer»
        self.found = {}                   # ref -> the template listed, of the kind (and document) shown
        self.resize(1040, 680)
        self.setWindowTitle(self.t("prefs_title"))
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)
        body = QWidget()
        row = QHBoxLayout(body)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        self.nav = QListWidget()
        self.nav.setObjectName("nav")   # the window's side navigation's ground (theme.py)
        self.nav.setFixedWidth(210)
        self.nav.setSpacing(2)
        self.pages = QStackedWidget()
        builders = {"templates": self.templates_page, "defaults": self.defaults_page, "languages": self.languages_page, "appearance": self.appearance_page}
        for key in PAGES:
            QListWidgetItem(self.t(f"prefs_page_{key}"), self.nav)
            self.pages.addWidget(builders[key]())
        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)
        page = PAGE_ALIASES.get(page, page)
        self.nav.setCurrentRow(PAGES.index(page) if page in PAGES else 0)
        row.addWidget(self.nav)
        row.addWidget(self.pages, 1)
        outer.addWidget(body, 1)
        # «Enregistrer» left of «Fermer», as the engineer asked -- laid out by hand rather than by a QDialogButtonBox, which orders its buttons after the platform
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.save_button = QPushButton(self.t("prefs_save"))
        self.save_button.setProperty("primary", True)
        self.save_button.setToolTip(self.t("prefs_save_tip"))
        self.save_button.clicked.connect(lambda: self.save())
        self.close_button = QPushButton(self.t("prefs_close"))
        self.close_button.clicked.connect(self.reject)
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.close_button)
        outer.addLayout(buttons)
        self.set_kind(self.kind)

    def t(self, key, **values):
        return t(self.lang, key, **values)

    # --- the frame, and what is pending --------------------------------------------------------------

    def page(self):
        return PAGES[self.nav.currentRow()]

    def show_page(self, key):
        self.nav.setCurrentRow(PAGES.index(PAGE_ALIASES.get(key, key)))

    def saved(self):
        """The settings as they stand on disk."""
        return usersettings.read()

    def settings(self):
        """The settings as they will be once saved: those on disk, with what is pending written over them -- what the template lists are read against."""
        merged = copy.deepcopy(self.saved())
        for (section, key), value in self.pending.items():
            apply_setting(merged, section, key, value)
        return merged

    def set_pending(self, section, key, value):
        """One setting changed and held until «Enregistrer»: taken out of what is pending again where it comes back to what the settings hold."""
        value = None if value in (None, "") else value
        if value == setting_of(self.saved(), section, key):
            self.pending.pop((section, key), None)
        else:
            self.pending[(section, key)] = value

    def dirty(self):
        """Whether anything is held that «Enregistrer» would write."""
        return bool(self.pending) or self.pending_lang is not None or self.pending_appearance is not None

    def save(self):
        """«Enregistrer»: every pending setting written at once into the settings file, the window that opened the dialog handed them afresh, the appearance applied through theme.set_appearance, the window's language through the window's own switch -- the window then writes it, installs Qt's translation and builds itself again --, and the dialog closed. Returns True."""
        settings = self.saved()
        for (section, key), value in self.pending.items():
            apply_setting(settings, section, key, value)
        lang, appearance = self.pending_lang, self.pending_appearance
        switch, index = getattr(self.window_, "language", None), None
        if lang is not None and switch is not None and hasattr(switch, "itemData"):
            index = next((i for i in range(switch.count()) if switch.itemData(i) == lang), None)
        if lang is not None and index is None:
            settings["lang"] = lang
        usersettings.write(settings)
        if self.window_ is not None and hasattr(self.window_, "settings"):
            self.window_.settings = usersettings.read()
        self.pending, self.pending_lang, self.pending_appearance = {}, None, None
        self.accept()
        if appearance is not None:
            theme.set_appearance(appearance)
        if index is not None:
            switch.setCurrentIndex(index)
        return True

    def reject(self):
        """«Fermer», Escape or the title bar's ×: closed without writing -- asked first where something is pending: Enregistrer, Ne pas enregistrer, Annuler."""
        if self.dirty():
            buttons = QMessageBox.StandardButton
            answer = QMessageBox.question(self, self.t("prefs_title"), self.t("prefs_unsaved_ask"), buttons.Save | buttons.Discard | buttons.Cancel, buttons.Save)
            if answer == buttons.Save:
                self.save()
                return
            if answer != buttons.Discard:
                return
        super().reject()

    def page_widget(self, note_key):
        """A page: a column of cards on the soft ground, scrolling up and down and never sideways (cards.column, v0.93), opening on one sentence saying what it is for."""
        scroll, layout = cards.column(margins=(10, 8, 10, 8), spacing=8)
        layout.addWidget(cards.note(self.t(note_key)))
        return scroll, layout

    # --- Templates ------------------------------------------------------------------------------------

    def templates_page(self):
        """The switch between the two kinds of template, and under «Fond» the switch between the three documents; the templates of what is chosen, grouped by place, with what can be done to them; the one chosen read only beside them; and the two folders of templates under them."""
        scroll, layout = self.page_widget("prefs_templates_note")
        layout.addWidget(cards.note(self.t("prefs_actions_note")))

        kind_row = QHBoxLayout()
        kind_row.addWidget(QLabel(self.t("prefs_kind_label")))
        kind_row.addSpacing(8)
        segments, self.kind_group, self.kind_buttons = _segments([(kind, self.t(f"prefs_kind_{kind}")) for kind in KINDS], self.kind, self.set_kind)
        self.kind_group.setParent(self)
        kind_row.addLayout(segments, 1)
        layout.addLayout(kind_row)
        self.kind_note = cards.note("")
        layout.addWidget(self.kind_note)

        self.document_box = QWidget()   # the documents' switch: the content templates' alone
        document_row = QHBoxLayout(self.document_box)
        document_row.setContentsMargins(0, 0, 0, 0)
        document_row.addWidget(QLabel(self.t("prefs_document_label")))
        document_row.addSpacing(8)
        segments, self.document_group, self.document_buttons = _segments([(mode, documents.mode_name(mode, self.lang)) for mode in DOCUMENTS], self.document, self.set_document)
        self.document_group.setParent(self)
        document_row.addLayout(segments, 1)
        layout.addWidget(self.document_box)

        row = QHBoxLayout()
        row.setSpacing(8)
        listing = cards.card(self.t("prefs_page_templates"))
        lv = QVBoxLayout(listing)
        lv.setSpacing(4)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels([self.t("prefs_col_name"), self.t("prefs_col_languages")])
        self.tree.setRootIsDecorated(False)
        self.tree.setUniformRowHeights(True)
        self.tree.setMinimumHeight(260)
        header = self.tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)       # the name takes what is left, never elided while there is room
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.currentItemChanged.connect(lambda _current, _previous: self.on_chosen())
        lv.addWidget(self.tree, 1)
        buttons = QHBoxLayout()
        buttons.setSpacing(4)
        self.delete_button = QPushButton(self.t("prefs_delete"))
        self.delete_button.clicked.connect(lambda: self.delete_template())
        self.folder_button = QPushButton(self.t("prefs_open_folder"))
        self.folder_button.clicked.connect(self.open_template_folder)
        buttons.addWidget(self.delete_button)
        buttons.addWidget(self.folder_button)
        buttons.addStretch(1)
        lv.addLayout(buttons)
        actions = QHBoxLayout()
        actions.setSpacing(4)
        self.import_button = QPushButton(self.t("prefs_import"))
        self.import_button.clicked.connect(lambda: self.import_template())
        self.save_form_button = QPushButton(self.t("prefs_save_form"))
        self.save_form_button.setToolTip(self.t("prefs_save_form_tip") if self.here is not None else self.t("prefs_no_project"))
        self.save_form_button.setEnabled(self.here is not None)
        self.save_form_button.clicked.connect(lambda: self.save_form())
        actions.addWidget(self.import_button)
        actions.addWidget(self.save_form_button)
        actions.addStretch(1)
        lv.addLayout(actions)
        self.status = cards.note("")
        lv.addWidget(self.status)
        row.addWidget(listing, 3)

        details = cards.card(self.t("prefs_card_details"))
        dv = QVBoxLayout(details)
        self.detail_pick = cards.note(self.t("prefs_pick"))
        dv.addWidget(self.detail_pick)
        self.details_box = QWidget()   # hidden while nothing is chosen, rather than showing its rows empty
        form = cards.form(self.details_box)
        form.setContentsMargins(0, 0, 0, 0)
        self.details = {}
        for key in ("name", "description", "languages", "place", "folder"):
            if key == "folder":
                value = QLineEdit()   # a path has no space to wrap at: read only, scrolled rather than broken after «C:»
                value.setReadOnly(True)
            else:
                value = QLabel()
                value.setWordWrap(True)
                value.setTextFormat(Qt.TextFormat.PlainText)
                value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.details[key] = value
            form.addRow(self.t(f"prefs_detail_{key}"), value)
        dv.addWidget(self.details_box)
        self.detail_error = QLabel()
        self.detail_error.setWordWrap(True)
        self.detail_error.setTextFormat(Qt.TextFormat.PlainText)
        self.detail_error.setProperty("callout", "warning")
        dv.addWidget(self.detail_error)
        dv.addStretch(1)
        row.addWidget(details, 2)
        layout.addLayout(row)

        folders = cards.card(self.t("prefs_card_folders"))
        fv = QVBoxLayout(folders)
        fv.addWidget(QLabel(self.t("prefs_shared_folder")))
        fv.addWidget(cards.note(self.t("prefs_shared_note")))
        shared_row = QHBoxLayout()
        shared = templates.shared_folder(self.saved())
        self.shared_field = QLineEdit(str(shared) if shared else "")
        self.shared_field.editingFinished.connect(lambda: self.set_shared(self.shared_field.text()))
        shared_row.addWidget(self.shared_field, 1)
        self.choose_shared_button = QPushButton(self.t("prefs_choose_shared"))
        self.choose_shared_button.clicked.connect(lambda: self.choose_shared())
        shared_row.addWidget(self.choose_shared_button)
        self.clear_shared_button = QPushButton(self.t("prefs_clear"))
        self.clear_shared_button.clicked.connect(lambda: self.set_shared(""))
        shared_row.addWidget(self.clear_shared_button)
        fv.addLayout(shared_row)
        fv.addWidget(QLabel(self.t("prefs_user_folder")))
        own_row = QHBoxLayout()
        own_path = QLineEdit(str(templates.place_dir("user")))
        own_path.setReadOnly(True)
        own_row.addWidget(own_path, 1)
        open_own = QPushButton(self.t("prefs_open_folder"))
        open_own.clicked.connect(self.open_user_folder)
        own_row.addWidget(open_own)
        fv.addLayout(own_row)
        layout.addWidget(folders)
        layout.addStretch(1)
        return scroll

    def set_kind(self, kind):
        """The kind of template the page lists: «Forme» the layout templates, «Fond» the content templates of the document chosen -- each kind said in one sentence under the switch."""
        if kind not in KINDS:
            return
        self.kind = kind
        self.kind_buttons[kind].setChecked(True)
        self.kind_note.setText(self.t(f"prefs_kind_{kind}_note"))
        self.document_box.setVisible(kind == "content")
        self.save_form_button.setVisible(kind == "form")
        self.import_button.setToolTip(self.t(f"prefs_import_tip_{kind}"))
        self.status.setText("")
        self.fill_tree()

    def set_document(self, mode):
        """The document whose content templates the page lists -- the convention, the base or the report."""
        if mode not in DOCUMENTS:
            return
        self.document = mode
        self.document_buttons[mode].setChecked(True)
        if self.kind != "content":
            self.set_kind("content")
            return
        self.status.setText("")
        self.fill_tree()

    def listed(self, settings):
        """(templates, {group: folder or None}) of what the page shows, read against `settings`: the layout templates, or the content templates of the document chosen -- every place's, the broken ones with their reason."""
        if self.kind == "form":
            found = forms.list_forms(settings)
            roots = {"builtin": forms.place_dir("builtin"), "shared": forms.place_dir("shared", settings), "user": forms.place_dir("user", settings)}
            return found, roots
        shared = templates.shared_folder(settings)
        found = doc_templates.list_templates(self.document, settings=settings)
        roots = {"builtin": doc_templates.place_dir("builtin") / self.document,
                 "shared": (shared / "documents" / self.document) if shared is not None else None,
                 "user": doc_templates.place_dir("user", settings) / self.document}
        return found, roots

    def group_of(self, template):
        return "shared" if template.place in ("office", "shared") else template.place

    def name_of(self, template):
        return template.name(self.lang)

    def languages_of(self, template):
        """The languages a template is offered in: a content template's own; a layout template is the same in every language («toutes»)."""
        if self.kind == "form":
            return self.t("prefs_lang_any")
        return ", ".join(template.languages) if template.languages else "—"

    def fill_tree(self, select=None):
        """The templates of what is shown, grouped by place -- Intégrés, Partagés, Mes templates --, the default layout template marked, one that cannot be used greyed with its reason as its tooltip, a place with nothing in it or no folder saying so. `select` a ref to choose afterwards, else the one chosen."""
        if not hasattr(self, "tree"):
            return
        select = select or self.current_ref()
        settings = self.settings()
        found, roots = self.listed(settings)
        self.found = {template.ref: template for template in found}
        default = default_form_ref(settings) if self.kind == "form" else None
        muted = QBrush(QColor(theme.colour("muted")))
        self.tree.blockSignals(True)
        self.tree.clear()
        chosen = None
        for group in GROUPS:
            heading = place_label(self.lang, group)
            root = roots[group]
            if group == "shared" and root is not None and not Path(templates.shared_folder(settings)).is_dir():
                heading = self.t("prefs_place_missing", place=heading)
            item = QTreeWidgetItem([heading, ""])
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            font = QFont(item.font(0))
            font.setBold(True)
            item.setFont(0, font)
            self.tree.addTopLevelItem(item)
            members = [template for template in found if self.group_of(template) == group]
            for template in members:
                name = self.name_of(template)
                label = self.t("prefs_default_mark", name=name) if template.ref == default else name
                child = QTreeWidgetItem([label, self.languages_of(template)])
                child.setData(0, Qt.ItemDataRole.UserRole, template.ref)
                tip = template.error or f"{template.description(self.lang)}\n{template.folder}".strip()
                for column in range(2):
                    child.setToolTip(column, tip)
                    if template.error:
                        child.setForeground(column, muted)
                item.addChild(child)
                if template.ref == select:
                    chosen = child
            if not members:
                empty = QTreeWidgetItem([self.t("prefs_place_unset") if group == "shared" and root is None else self.t("prefs_place_empty"), ""])
                empty.setFlags(Qt.ItemFlag.NoItemFlags)
                empty.setForeground(0, muted)
                item.addChild(empty)
            item.setExpanded(True)
        if chosen is not None:
            self.tree.setCurrentItem(chosen)
        self.tree.blockSignals(False)
        self.on_chosen()

    def groups(self):
        """{group heading: [row names]} of the list as shown -- what a reader of the page sees, for the tests."""
        out = {}
        for g in range(self.tree.topLevelItemCount()):
            group = self.tree.topLevelItem(g)
            out[group.text(0)] = [group.child(c).text(0) for c in range(group.childCount()) if group.child(c).data(0, Qt.ItemDataRole.UserRole)]
        return out

    def current_ref(self):
        tree = getattr(self, "tree", None)
        item = tree.currentItem() if tree is not None else None
        return item.data(0, Qt.ItemDataRole.UserRole) if item is not None else None

    def chosen(self):
        """The template chosen in the list, None where none is."""
        return self.found.get(self.current_ref())

    def choose(self, ref):
        """The template `ref` chosen in the list. Returns whether it is listed."""
        for g in range(self.tree.topLevelItemCount()):
            group = self.tree.topLevelItem(g)
            for c in range(group.childCount()):
                if group.child(c).data(0, Qt.ItemDataRole.UserRole) == ref:
                    self.tree.setCurrentItem(group.child(c))
                    return True
        return False

    def on_chosen(self):
        """The template chosen shown read only, and the buttons that act on it opened or closed -- *Supprimer* closed with its reason as its tooltip where nothing is chosen and where the template is a builtin one."""
        template = self.chosen()
        self.detail_pick.setVisible(template is None)
        self.details_box.setVisible(template is not None)
        for key, label in self.details.items():
            label.setText("" if template is None else {
                "name": self.name_of(template),
                "description": template.description(self.lang) or "—",
                "languages": self.languages_of(template),
                "place": place_label(self.lang, template.place),
                "folder": str(template.folder),
            }[key])
        error = template.error if template is not None else ""
        self.detail_error.setText(self.t("prefs_detail_broken", error=error) if error else "")
        self.detail_error.setVisible(bool(error))
        self.folder_button.setEnabled(template is not None)
        self.delete_button.setEnabled(template is not None and not template.read_only)
        self.delete_button.setToolTip(self.t("prefs_pick") if template is None else self.t("prefs_read_only") if template.read_only else "")

    def delete_template(self, ref=None, confirm=True):
        """«Supprimer»: the template chosen -- or `ref` -- moved into the archives folder of its place, once asked (forms.archive, doc_templates.delete: never deleted), the list filled again. A layout template that was the default leaves builtin neutral the default, written at once, the template being gone at once. Returns where it went, or None where the engineer declined, the template is a builtin one or the move was refused -- said in the window's language."""
        template = self.found.get(ref or self.current_ref())
        if template is None or template.read_only:
            return None
        name = self.name_of(template)
        if confirm and QMessageBox.question(self, self.t("prefs_title"), self.t("prefs_delete_ask", name=name, folder=template.folder)) != QMessageBox.StandardButton.Yes:
            return None
        try:
            if self.kind == "form":
                target = forms.archive(template)
            else:
                target = doc_templates.delete(template, settings=self.settings())
        except forms.FormError as exc:
            notices_ui.inline_error(self, self.t("prefs_failed", error=form_error_text(self.lang, exc)))   # in the dialog, which is modal: the panel behind it cannot be reached
            return None
        except doc_templates.DocTemplateError as exc:
            notices_ui.inline_error(self, self.t("prefs_failed", error=doc_error_text(self.lang, exc)))   # in the dialog, which is modal: the panel behind it cannot be reached
            return None
        except OSError as exc:
            notices_ui.inline_error(self, self.t("prefs_failed", error=exc))   # in the dialog, which is modal: the panel behind it cannot be reached
            return None
        if self.kind == "form" and setting_of(self.saved(), "forms", "default") == template.ref:
            store(self.window_, "forms", "default", None)
            self.pending.pop(("forms", "default"), None)
        self.fill_tree()
        self.fill_default_combo()
        self.status.setText(self.t("prefs_archived", name=name, folder=target))
        return target

    def import_template(self, source=None, replace=None):
        """«Importer un dossier…»: one template folder chosen -- `source` given asks nothing (tests) -- and copied into «Mes templates» as a template of the kind shown (forms.import_folder for a layout template, doc_templates.import_folder for a content template of the document shown). A template of that folder's name there already is replaced only on the engineer's word -- `replace` given asks nothing --, the old one archived. A refusal is said in the window's language. Returns the template imported, or None."""
        if source is None:
            start = str(templates.shared_folder(self.settings()) or Path.home())
            source = QFileDialog.getExistingDirectory(self, self.t("prefs_import_title"), start)
            if not source:
                return None
        settings = self.settings()

        def bring(again):
            if self.kind == "form":
                return forms.import_folder(source, replace=again, settings=settings)
            return doc_templates.import_folder(source, self.document, replace=again, settings=settings)

        try:
            try:
                made = bring(bool(replace))
            except (forms.FormError, doc_templates.DocTemplateError) as exc:
                if getattr(exc, "code", "") != "exists" or replace is not None:
                    raise
                folder = exc.values.get("folder") or Path(source).name
                if QMessageBox.question(self, self.t("prefs_title"), self.t("prefs_import_replace_ask", folder=folder)) != QMessageBox.StandardButton.Yes:
                    return None
                made = bring(True)
        except (forms.FormError, doc_templates.DocTemplateError) as exc:
            notices_ui.inline_error(self, self.t("prefs_import_failed", error=import_error_text(self.lang, exc)))   # in the dialog, which is modal: the panel behind it cannot be reached
            return None
        except OSError as exc:
            notices_ui.inline_error(self, self.t("prefs_import_failed", error=exc))   # in the dialog, which is modal: the panel behind it cannot be reached
            return None
        self.fill_tree(made.ref)
        self.fill_default_combo()
        self.status.setText(self.t("prefs_import_done", name=self.name_of(made)))
        return made

    def ask_name(self, default):
        """(name, place) asked in a NameDialog, or None where cancelled."""
        places = ["user"] + (["shared"] if templates.shared_folder(self.settings()) is not None else [])
        dialog = NameDialog(self, self.lang, default, places)
        if dialog.exec() != QDialog.DialogCode.Accepted or not dialog.values()[0]:
            return None
        return dialog.values()

    def save_form(self, name=None, place="user"):
        """«Enregistrer la forme de ce projet comme template de forme…»: the open project's `Template/` and title.typ made a layout template (forms.save_from_project) -- not by hand, from what the project is --, chosen in the list of the layout templates. `name` given asks nothing (tests). A refusal -- a project whose look is still an old config.typ -- is said in the window's language. Returns the template, or None."""
        if self.here is None:
            return None
        if name is None:
            answer = self.ask_name(self.here.name)
            if answer is None:
                return None
            name, place = answer
        try:
            made = forms.save_from_project(self.here, name, place, settings=self.settings())
        except forms.FormError as exc:
            notices_ui.inline_error(self, self.t("prefs_failed", error=form_error_text(self.lang, exc)))   # in the dialog, which is modal: the panel behind it cannot be reached
            return None
        except OSError as exc:
            notices_ui.inline_error(self, self.t("prefs_failed", error=exc))   # in the dialog, which is modal: the panel behind it cannot be reached
            return None
        if self.kind != "form":
            self.set_kind("form")
        self.fill_tree(made.ref)
        self.fill_default_combo()
        self.status.setText(self.t("prefs_saved_form", name=made.name(self.lang)))
        return made

    def open_template_folder(self):
        template = self.chosen()
        if template is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(template.folder)))

    def choose_shared(self):
        folder = QFileDialog.getExistingDirectory(self, self.t("prefs_shared_folder"), self.shared_field.text() or str(Path.home()))
        if folder:
            self.set_shared(folder)

    def set_shared(self, folder):
        """The office's shared folder of templates chosen -- or taken out, "" --, held until «Enregistrer», and the templates listed again as they will be."""
        folder = os.path.normpath(folder.strip()) if folder and folder.strip() else ""
        self.shared_field.setText(folder)
        self.set_pending("templates", "shared_folder", folder)
        self.fill_tree()
        self.fill_default_combo()

    def open_user_folder(self):
        folder = templates.place_dir("user")
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    # --- Valeurs par défaut ----------------------------------------------------------------------------

    def defaults_page(self):
        """The company, author and checker a new project starts with, and the layout template «Nouveau projet» offers first -- a card each."""
        scroll, layout = self.page_widget("prefs_defaults_page_note")
        people = cards.card(self.t("prefs_card_people"))
        form = cards.form(people)
        own = templates.defaults(self.saved())
        self.default_fields = {}
        for key in templates.PEOPLE:
            field = QLineEdit(own[key])
            field.textChanged.connect(lambda text, key=key: self.set_pending("defaults", key, text.strip()))
            self.default_fields[key] = field
            form.addRow(self.t(f"prefs_{key}"), field)
        layout.addWidget(people)
        default = cards.card(self.t("prefs_default_form"))
        dv = QVBoxLayout(default)
        dv.addWidget(cards.note(self.t("prefs_default_form_note")))
        self.default_combo = QComboBox()
        self.default_combo.currentIndexChanged.connect(self.on_default_form)
        dv.addWidget(self.default_combo)
        layout.addWidget(default)
        layout.addStretch(1)
        self.fill_default_combo()
        return scroll

    def fill_default_combo(self):
        """The layout templates there are, as the settings will be -- the one the settings name, or will, chosen; each with its description as its tooltip."""
        combo = getattr(self, "default_combo", None)
        if combo is None:
            return
        settings = self.settings()
        combo.blockSignals(True)
        combo.clear()
        for form in forms.list_forms(settings):
            if not form.error:
                name = form.name(self.lang)
                combo.addItem(name if form.place == "builtin" else f"{name} — {place_label(self.lang, form.place)}", form.ref)
                combo.setItemData(combo.count() - 1, form.description(self.lang), Qt.ItemDataRole.ToolTipRole)
        combo.setCurrentIndex(max(0, combo.findData(default_form_ref(settings))))
        combo.blockSignals(False)

    def on_default_form(self, index):
        ref = self.default_combo.itemData(index)
        self.set_pending("forms", "default", None if ref == f"builtin:{forms.NEUTRAL}" else ref)
        if self.kind == "form" and hasattr(self, "tree"):
            self.fill_tree()

    # --- Langues -------------------------------------------------------------------------------------------

    def languages_page(self):
        """The window's language, and the report language «Nouveau projet» offers -- a card each."""
        scroll, layout = self.page_widget("prefs_languages_page_note")
        window = cards.card(self.t("prefs_card_window"))
        form = cards.form(window)
        self.window_language = QComboBox()
        for code in LANGUAGES:
            self.window_language.addItem(LANGUAGE_NAMES[code], code)
        self.window_language.setCurrentIndex(LANGUAGES.index(self.lang))
        self.window_language.currentIndexChanged.connect(lambda index: self.set_language(self.window_language.itemData(index)))
        form.addRow(self.t("prefs_window_language"), self.window_language)
        layout.addWidget(window)
        new = cards.card(self.t("prefs_card_new_projects"))
        nv = QVBoxLayout(new)
        nv.addWidget(cards.note(self.t("prefs_new_report_language_tip")))
        form = cards.form()
        self.report_language = QComboBox()
        for code in templates.LANGUAGES:
            self.report_language.addItem(LANGUAGE_NAMES[code], code)
        self.report_language.setCurrentIndex(max(0, self.report_language.findData(templates.defaults(self.saved())["report_language"] or templates.DEFAULT_LANGUAGE)))
        self.report_language.currentIndexChanged.connect(lambda index: self.set_pending("defaults", "report_language", self.report_language.itemData(index)))
        form.addRow(self.t("prefs_new_report_language"), self.report_language)
        nv.addLayout(form)
        layout.addWidget(new)
        layout.addStretch(1)
        return scroll

    def set_language(self, lang):
        """The window's language chosen, held until «Enregistrer» -- which moves the window's own language switch where it has one, else writes it into the settings."""
        if lang not in LANGUAGES:
            return
        self.pending_lang = None if lang == self.lang else lang

    # --- Apparence et mises à jour ---------------------------------------------------------------------

    def appearance_page(self):
        """*Fichier → Apparence*'s three choices, applied through theme.set_appearance itself on «Enregistrer», and the update check of an installed Woodcore -- a card each."""
        import home_page   # the appearance's words are the File menu's (home_page.STRINGS), imported here: home_page opens this dialog
        scroll, layout = self.page_widget("prefs_appearance_page_note")
        box = cards.card(self.t("prefs_appearance"))
        bv = QVBoxLayout(box)
        self.appearance = QButtonGroup(box)
        chosen = theme.appearance()
        for index, value in enumerate(theme.APPEARANCES):
            button = QRadioButton(_plain(home_page.STRINGS[self.lang][APPEARANCE_KEYS[value]]))
            button.setChecked(value == chosen)
            self.appearance.addButton(button, index)
            bv.addWidget(button)
        self.appearance.idClicked.connect(self.on_appearance)
        layout.addWidget(box)
        updates = cards.card(self.t("prefs_updates_title"))
        uv = QVBoxLayout(updates)
        self.updates_box = QCheckBox(self.t("prefs_updates"))
        prefs = self.saved().get("updates")
        self.updates_box.setChecked(not (isinstance(prefs, dict) and prefs.get("enabled") is False))
        self.updates_box.toggled.connect(lambda on: self.set_pending("updates", "enabled", None if on else False))
        uv.addWidget(self.updates_box)
        uv.addWidget(cards.note(self.t("prefs_updates_note")))
        layout.addWidget(updates)
        layout.addStretch(1)
        return scroll

    def on_appearance(self, index):
        value = theme.APPEARANCES[index]
        self.pending_appearance = None if value == theme.appearance() else value


def menu_text(lang):
    """The File menu's entry, «&Paramètres…», in `lang`."""
    return t(lang, "prefs_menu")


def open_dialog(parent, lang, here=None, page="templates", document="cu", kind=None):
    """*Paramètres…* from the window or the start page: the dialog shown until closed -- its templates page on the layout templates, or on the content templates of `document` (`cu`, `bp` or `rs`) where `kind` is `content`. Returns it."""
    dialog = SettingsDialog(parent, lang, here=here, page=page, document=document, kind=kind)
    dialog.exec()
    return dialog
