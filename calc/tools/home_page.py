# -*- coding: utf-8 -*-
"""Woodcore's start page, the dialog a project is created and described in, and the question a project someone else holds asks (docs/ui/window.md §10quater, v0.83).

Woodcore opens on this page when it is started without a project -- `Woodcore.bat`, `Woodcore.exe` from the Start menu -- the way Word opens on its own: the projects opened lately, the last first, each with its number, its folder, when it was last exported and by which version of the engine; *Ouvrir…* and *Nouveau projet…*; and a `.woodcore` dropped anywhere on it. A project no longer where it was -- moved, renamed, deleted, or not synced yet on this machine -- is taken off the list as the page is drawn (the engineer's decision of 03.10.2026, where it was greyed until then): opened again with *Ouvrir…*, it comes back. *Convertir un ancien dossier…*, which wrote a `.woodcore` into a folder laid out before v0.82, left the page the same day, every project being laid out the new way -- `woodcore-cli convert` keeps it.

One process works on one project (calc/project.py): this page opens a project in its own process, which has none yet, and hands over to the window. The window's *Fichier* menu opens another in a process of its own and closes itself, and *Fermer le projet* comes back here the same way.

Nothing here writes into a project but *Nouveau projet* and *Propriétés du projet*, each through calc/project_template.py or project.update, and the lock (calc/project_lock.py).
"""

import os
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QIcon, QKeySequence, QPalette, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMainWindow, QMenu, QMessageBox, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

import project
import busy
import project_template
import forms  # the layout templates, «templates de forme» (calc/forms.py, 06.10.2026)
import templates  # the people, the languages and the folders a new project starts with (calc/templates.py)
import settings_dialog  # *Paramètres…*, the start page's as the File menu's (v0.94)
import chrome  # the site's cards and its segmented language switch (chrome.py, v0.91)
import theme  # the site's look (theme.py, v0.90)
import legal  # the copyright line, the licence and the notices
import usersettings
import notifications  # every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # what was a message box is a notice since v0.117 (notices_ui.tell)

LANGUAGES = {"fr": "Français", "de": "Deutsch", "en": "English"}

STRINGS = {
    "fr": {
        "home_recent": "Projets récents",
        "home_col_name": "Projet",
        "home_col_number": "N°",
        "home_col_folder": "Dossier",
        "home_col_exported": "Dernier export",
        "home_col_engine": "Moteur",
        "home_open": "Ouvrir…",
        "home_new": "Nouveau projet…",
        "home_open_selected": "Ouvrir le projet",
        "home_drop_hint": "Glissez un fichier .woodcore sur cette fenêtre pour l'ouvrir, ou double-cliquez un projet de la liste.",
        "home_empty": "Aucun projet récent : « Ouvrir… » en choisit un, « Nouveau projet… » en crée un.",
        "home_forget": "Retirer de la liste",
        "home_show_folder": "Ouvrir le dossier",
        "home_never": "jamais",
        "home_missing_gone": "« {path} » est introuvable — déplacé, renommé ou supprimé : il a été retiré de la liste. Ouvert à nouveau avec « Ouvrir… », il y revient.",
        "home_beside": "Le projet à côté des sources du programme.",
        "home_version": "Version {version}",
        "home_start": "Commencer",
        "home_new_text": "Un dossier vide devient un projet : ses trois documents et leurs sections, et le classeur des positions.",
        "home_open_text": "Un fichier .woodcore, où qu'il soit.",
        "home_engine": "moteur {version}",
        "home_failed": "Ce projet n'a pas pu être ouvert :\n\n{error}",
        "home_language": "Langue :",
        "proj_new_title": "Nouveau projet",
        "proj_location": "Emplacement",
        "proj_choose": "Choisir…",
        "proj_folder": "Dossier du projet",
        "proj_name": "Nom",
        "proj_number": "Numéro",
        "proj_client": "Maître d'ouvrage",
        "proj_address": "Adresse",
        "proj_company": "Bureau",
        "proj_author": "Auteur",
        "proj_checker": "Vérificateur",
        "proj_form_hint": "La mise en page des trois documents : polices, tailles, marges, titres, page de titre — aucune donnée.",
        "proj_form_ask": "Le projet s'imprimera avec le template de forme « {form} » : son dossier Template/ et son title.typ seront remplacés, les anciens archivés dans _Archiv. Vos réglages dans config.typ sont gardés.\n\nChanger de template de forme ?",
        "proj_form_ask_old": "Le projet s'imprimera avec le template de forme « {form} » : son config.typ, d'une version précédente, sera remplacé par un config.typ qui ne garde que la langue et vos réglages à venir, et archivé dans _Archiv avec son title.typ. Ce qui a été modifié à la main dans l'ancien config.typ ne passe pas dans le nouveau.\n\nChanger de template de forme ?",
        "proj_form_failed": "Le template de forme n'a pas pu être appliqué :\n\n{error}",
        "proj_language": "Langue du rapport",
        "proj_language_hint": "Règle d'un coup la langue du document (config.typ : la césure, «Abbildung»/«Fig.», le titre du sommaire) et celle du moteur (#set-report-language : les libellés des calculs, les titres des tableaux, les légendes des figures).",
        "proj_version_latest": "La plus récente installée",
        "proj_hint_new": "Crée le dossier du projet dans la langue choisie, qui ne se change plus. La page de titre, le template de forme et le template de fond de chaque document se choisissent ensuite dans l'onglet Projet, où Woodcore s'ouvre.",
        "proj_name_needed": "Le projet a besoin d'un nom.",
        "proj_failed": "Le projet n'a pas pu être écrit :\n\n{error}",
        "busy_creating": "Création du projet…",
        "lock_title": "Projet déjà ouvert",
        "lock_text": "« {name} » est ouvert par {user} sur le poste {host} depuis le {since}.\n\nDeux fenêtres qui enregistrent le même projet perdent le travail de la première. Ouvrir en lecture seule ?",
        "lock_read_only": "Lecture seule",
        "lock_force": "Ouvrir quand même",
        "read_only_banner": "Lecture seule : ce projet est ouvert par {user} sur le poste {host}. Rien ne peut être enregistré ni exporté depuis cette fenêtre.",
        "read_only_refused": "Ce projet est ouvert en lecture seule : rien n'y est enregistré ni exporté.",
        "read_only_newer_banner": "Lecture seule : le moteur de ce projet a été écrit par Woodcore {version}, plus récent que ce programme ({ours}). Rien ne peut être enregistré ni exporté depuis cette fenêtre : ouvrez le projet avec Woodcore {version} ou une version plus récente.",
        "read_only_suffix": "lecture seule",
        "file_menu": "&Fichier",
        "file_new": "&Nouveau projet…",
        "file_open": "&Ouvrir…",
        "file_recent": "Projets &récents",
        "file_recent_empty": "(aucun)",
        "file_open_window": "Ouvrir dans une nouvelle &fenêtre…",
        "file_close": "&Fermer le projet",
        "file_properties": "&Propriétés du projet…",
        "file_show_folder": "Ouvrir le &dossier du projet",
        "file_open_pdf": "Ouvrir le P&DF",
        "file_open_vscode": "Ouvrir dans &VS Code",
        "file_dev": "Ouvrir les fichiers .woodcore avec ces sources (développement)",
        "file_dev_tip": "Un double-clic sur un fichier .woodcore lancera Woodcore depuis ces sources plutôt que la version installée.",
        "view_menu": "&Affichage",
        "zoom_in": "Zoom &avant",
        "zoom_out": "Zoom a&rrière",
        "zoom_reset": "&Taille réelle",
        "zoom_status": "Zoom {percent} %",
        "file_appearance": "&Apparence",
        "file_appearance_system": "Comme &Windows",
        "file_appearance_light": "&Clair",
        "file_appearance_dark": "&Sombre",
        "file_quit": "&Quitter",
        "file_busy": "Un export est en cours : attendez qu'il se termine avant de changer de projet.",
        "file_no_pdf": "Le PDF n'existe pas encore : « Exporter PDF » l'écrit.",
        "file_no_vscode": "VS Code est introuvable : la commande « code » n'est pas sur le PATH.",
    },
    "de": {
        "home_recent": "Zuletzt geöffnete Projekte",
        "home_col_name": "Projekt",
        "home_col_number": "Nr.",
        "home_col_folder": "Ordner",
        "home_col_exported": "Letzter Export",
        "home_col_engine": "Engine",
        "home_open": "Öffnen…",
        "home_new": "Neues Projekt…",
        "home_open_selected": "Projekt öffnen",
        "home_drop_hint": "Eine .woodcore-Datei auf dieses Fenster ziehen, um sie zu öffnen, oder ein Projekt der Liste doppelklicken.",
        "home_empty": "Noch kein Projekt geöffnet: «Öffnen…» wählt eines, «Neues Projekt…» legt eines an.",
        "home_forget": "Aus der Liste entfernen",
        "home_show_folder": "Ordner öffnen",
        "home_never": "nie",
        "home_missing_gone": "«{path}» ist nicht zu finden — verschoben, umbenannt oder gelöscht: Es wurde aus der Liste entfernt. Mit «Öffnen…» wieder geöffnet, kommt es zurück.",
        "home_beside": "Das Projekt neben den Quellen des Programms.",
        "home_version": "Version {version}",
        "home_start": "Loslegen",
        "home_new_text": "Ein leerer Ordner wird ein Projekt: seine drei Dokumente mit ihren Abschnitten und die Positionsliste.",
        "home_open_text": "Eine .woodcore-Datei, wo sie auch liegt.",
        "home_engine": "Engine {version}",
        "home_failed": "Dieses Projekt konnte nicht geöffnet werden:\n\n{error}",
        "home_language": "Sprache:",
        "proj_new_title": "Neues Projekt",
        "proj_location": "Speicherort",
        "proj_choose": "Wählen…",
        "proj_folder": "Projektordner",
        "proj_name": "Name",
        "proj_number": "Nummer",
        "proj_client": "Bauherrschaft",
        "proj_address": "Adresse",
        "proj_company": "Büro",
        "proj_author": "Verfasser",
        "proj_checker": "Prüfer",
        "proj_form_hint": "Das Layout der drei Dokumente: Schriften, Grössen, Ränder, Titel, Titelseite — keine Daten.",
        "proj_form_ask": "Das Projekt wird mit der Formvorlage «{form}» gedruckt: sein Ordner Template/ und seine title.typ werden ersetzt, die alten in _Archiv archiviert. Die eigenen Einstellungen in config.typ bleiben.\n\nDie Formvorlage wechseln?",
        "proj_form_ask_old": "Das Projekt wird mit der Formvorlage «{form}» gedruckt: seine config.typ einer früheren Version wird durch eine config.typ ersetzt, die nur die Sprache und künftige eigene Einstellungen behält, und mit seiner title.typ in _Archiv archiviert. Was in der alten config.typ von Hand geändert wurde, geht nicht in die neue über.\n\nDie Formvorlage wechseln?",
        "proj_form_failed": "Die Formvorlage konnte nicht angewendet werden:\n\n{error}",
        "proj_language": "Sprache des Berichts",
        "proj_language_hint": "Setzt zugleich die Sprache des Dokuments (config.typ: die Silbentrennung, «Abbildung»/«Fig.», der Titel des Inhaltsverzeichnisses) und die der Engine (#set-report-language: die Bezeichnungen der Berechnungen, die Titel der Tabellen, die Legenden der Abbildungen).",
        "proj_version_latest": "Die neueste installierte",
        "proj_hint_new": "Erstellt den Projektordner in der gewählten Sprache, die sich nicht mehr ändern lässt. Titelseite, Formvorlage und die Inhaltsvorlage jedes Dokuments werden danach im Register Projekt gewählt, in dem Woodcore sich öffnet.",
        "proj_name_needed": "Das Projekt braucht einen Namen.",
        "proj_failed": "Das Projekt konnte nicht geschrieben werden:\n\n{error}",
        "busy_creating": "Projekt wird erstellt…",
        "lock_title": "Projekt bereits geöffnet",
        "lock_text": "«{name}» ist seit {since} von {user} auf dem Rechner {host} geöffnet.\n\nZwei Fenster, die dasselbe Projekt speichern, verlieren die Arbeit des ersten. Schreibgeschützt öffnen?",
        "lock_read_only": "Schreibgeschützt",
        "lock_force": "Trotzdem öffnen",
        "read_only_banner": "Schreibgeschützt: dieses Projekt ist von {user} auf dem Rechner {host} geöffnet. In diesem Fenster kann nichts gespeichert oder exportiert werden.",
        "read_only_refused": "Dieses Projekt ist schreibgeschützt geöffnet: nichts wird gespeichert oder exportiert.",
        "read_only_newer_banner": "Schreibgeschützt: die Engine dieses Projekts wurde von Woodcore {version} geschrieben, neuer als dieses Programm ({ours}). In diesem Fenster kann nichts gespeichert oder exportiert werden: öffnen Sie das Projekt mit Woodcore {version} oder einer neueren Version.",
        "read_only_suffix": "schreibgeschützt",
        "file_menu": "&Datei",
        "file_new": "&Neues Projekt…",
        "file_open": "Ö&ffnen…",
        "file_recent": "&Zuletzt geöffnet",
        "file_recent_empty": "(keine)",
        "file_open_window": "In neuem &Fenster öffnen…",
        "file_close": "Projekt &schliessen",
        "file_properties": "Projekt&eigenschaften…",
        "file_show_folder": "Projekt&ordner öffnen",
        "file_open_pdf": "P&DF öffnen",
        "file_open_vscode": "In &VS Code öffnen",
        "file_dev": ".woodcore-Dateien mit diesen Quellen öffnen (Entwicklung)",
        "file_dev_tip": "Ein Doppelklick auf eine .woodcore-Datei startet Woodcore aus diesen Quellen statt der installierten Version.",
        "view_menu": "&Ansicht",
        "zoom_in": "Ver&grössern",
        "zoom_out": "Ver&kleinern",
        "zoom_reset": "&Originalgrösse",
        "zoom_status": "Zoom {percent} %",
        "file_appearance": "&Darstellung",
        "file_appearance_system": "Wie &Windows",
        "file_appearance_light": "&Hell",
        "file_appearance_dark": "&Dunkel",
        "file_quit": "&Beenden",
        "file_busy": "Ein Export läuft: warten, bis er fertig ist, bevor das Projekt gewechselt wird.",
        "file_no_pdf": "Das PDF gibt es noch nicht: «PDF exportieren» schreibt es.",
        "file_no_vscode": "VS Code ist nicht zu finden: der Befehl «code» steht nicht im PATH.",
    },
    "en": {
        "home_recent": "Recent projects",
        "home_col_name": "Project",
        "home_col_number": "No.",
        "home_col_folder": "Folder",
        "home_col_exported": "Last export",
        "home_col_engine": "Engine",
        "home_open": "Open…",
        "home_new": "New project…",
        "home_open_selected": "Open project",
        "home_drop_hint": "Drop a .woodcore file on this window to open it, or double-click a project of the list.",
        "home_empty": "No recent project: “Open…” chooses one, “New project…” creates one.",
        "home_forget": "Remove from the list",
        "home_show_folder": "Open the folder",
        "home_never": "never",
        "home_missing_gone": "“{path}” cannot be found — moved, renamed or deleted: it was taken off the list. Opened again with “Open…”, it comes back.",
        "home_beside": "The project beside the program's sources.",
        "home_version": "Version {version}",
        "home_start": "Start",
        "home_new_text": "An empty folder becomes a project: its three documents and their sections, and the positions workbook.",
        "home_open_text": "A .woodcore file, wherever it is.",
        "home_engine": "engine {version}",
        "home_failed": "This project could not be opened:\n\n{error}",
        "home_language": "Language:",
        "proj_new_title": "New project",
        "proj_location": "Location",
        "proj_choose": "Choose…",
        "proj_folder": "Project folder",
        "proj_name": "Name",
        "proj_number": "Number",
        "proj_client": "Client",
        "proj_address": "Address",
        "proj_company": "Office",
        "proj_author": "Author",
        "proj_checker": "Checker",
        "proj_form_hint": "How the three documents look: fonts, sizes, margins, headings, title page — no data.",
        "proj_form_ask": "The project will be printed with the layout template «{form}»: its Template/ folder and its title.typ will be replaced, the old ones archived in _Archiv. Your adjustments in config.typ are kept.\n\nSwitch the layout template?",
        "proj_form_ask_old": "The project will be printed with the layout template «{form}»: its config.typ, of an earlier version, will be replaced by a config.typ that keeps only the language and your adjustments to come, and archived in _Archiv with its title.typ. What was edited by hand in the old config.typ does not pass into the new one.\n\nSwitch the layout template?",
        "proj_form_failed": "The layout template could not be applied:\n\n{error}",
        "proj_language": "Report language",
        "proj_language_hint": "Sets at once the document's language (config.typ: the hyphenation, «Abbildung»/«Fig.», the outline's title) and the engine's (#set-report-language: the calculations' labels, the tables' titles, the figures' legends).",
        "proj_version_latest": "The newest installed",
        "proj_hint_new": "Creates the project's folder in the language chosen, which no longer changes. The title page, the layout template and each document's content template are chosen afterwards in the Project tab, where Woodcore opens.",
        "proj_name_needed": "The project needs a name.",
        "proj_failed": "The project could not be written:\n\n{error}",
        "busy_creating": "Creating the project…",
        "lock_title": "Project already open",
        "lock_text": "“{name}” has been open by {user} on the machine {host} since {since}.\n\nTwo windows saving the same project lose the first one's work. Open it read-only?",
        "lock_read_only": "Read-only",
        "lock_force": "Open anyway",
        "read_only_banner": "Read-only: this project is open by {user} on the machine {host}. Nothing can be saved or exported from this window.",
        "read_only_refused": "This project is open read-only: nothing is saved or exported.",
        "read_only_newer_banner": "Read-only: this project's engine was written by Woodcore {version}, newer than this program ({ours}). Nothing can be saved or exported from this window: open the project with Woodcore {version} or a newer version.",
        "read_only_suffix": "read-only",
        "file_menu": "&File",
        "file_new": "&New project…",
        "file_open": "&Open…",
        "file_recent": "&Recent projects",
        "file_recent_empty": "(none)",
        "file_open_window": "Open in a new &window…",
        "file_close": "&Close the project",
        "file_properties": "Project &properties…",
        "file_show_folder": "Open the project's &folder",
        "file_open_pdf": "Open the P&DF",
        "file_open_vscode": "Open in &VS Code",
        "file_dev": "Open .woodcore files with these sources (development)",
        "file_dev_tip": "A double-click on a .woodcore file will start Woodcore from these sources rather than the installed version.",
        "view_menu": "&View",
        "zoom_in": "Zoom &in",
        "zoom_out": "Zoom &out",
        "zoom_reset": "&Actual size",
        "zoom_status": "Zoom {percent}%",
        "file_appearance": "&Appearance",
        "file_appearance_system": "Like &Windows",
        "file_appearance_light": "&Light",
        "file_appearance_dark": "&Dark",
        "file_quit": "&Quit",
        "file_busy": "An export is running: wait for it to finish before changing project.",
        "file_no_pdf": "The PDF does not exist yet: “Export PDF” writes it.",
        "file_no_vscode": "VS Code cannot be found: the command “code” is not on the PATH.",
    },
}

PROJECT_FILTER = {"fr": "Projets Woodcore (*.woodcore)", "de": "Woodcore-Projekte (*.woodcore)", "en": "Woodcore projects (*.woodcore)"}

# Where installed versions of Woodcore live, one folder each: what the launcher starts from, and what «Version de Woodcore» offers (packaging/woodcore.iss).
INSTALL_ROOT = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "Programs" / "Woodcore"


def installed_versions(root=None):
    """The versions installed under INSTALL_ROOT, newest first: a folder named after its version holding Woodcore.exe."""
    root = Path(root or INSTALL_ROOT)
    found = []
    if root.is_dir():
        for folder in root.iterdir():
            if folder.is_dir() and (folder / "Woodcore.exe").is_file() and folder.name[:1].isdigit():
                found.append(folder.name)
    return sorted(found, key=project._version_tuple, reverse=True)


def summary(file):
    """What the start page shows of a project file: its name, number and folder, when it was last exported and by which version of the engine -- read from the file and the export beside it, nothing written. `missing` where the file is not there, `error` where it cannot be read."""
    file = Path(file)
    row = {"file": str(file), "name": file.stem, "number": "", "folder": str(file.parent), "exported": None, "engine": "", "missing": not file.is_file(), "error": ""}
    if row["missing"]:
        return row
    try:
        here = project.Project.load(file)
    except project.ProjectError as exc:
        row["error"] = str(exc)
        return row
    row["name"], row["number"] = here.name, here.detail("number")
    # the time of the last export, not of data/project.json, which the «Projet» tab rewrites as a title page's field is saved (project.last_export, issue #87)
    row["exported"], row["engine"] = project.last_export(here)
    return row


def ask_lock(parent, lang, here, holder):
    """The question a project someone else holds asks: «read_only», «force», or None to stay away."""
    t = STRINGS[lang]
    since = str(holder.get("since", "?"))
    try:
        since = datetime.fromisoformat(since).strftime("%d.%m.%Y %H:%M")
    except ValueError:
        pass
    box = QMessageBox(QMessageBox.Icon.Warning, t["lock_title"],  # dialog-ok: a decision -- open read-only, take the project over, or not -- that waits for its answer
                      t["lock_text"].format(name=here.name, user=holder.get("user", "?"), host=holder.get("host", "?"), since=since), parent=parent)
    read_only = box.addButton(t["lock_read_only"], QMessageBox.ButtonRole.AcceptRole)
    force = box.addButton(t["lock_force"], QMessageBox.ButtonRole.DestructiveRole)
    box.addButton(QMessageBox.StandardButton.Cancel)
    box.setDefaultButton(read_only)
    box.exec()
    clicked = box.clickedButton()
    return "read_only" if clicked is read_only else "force" if clicked is force else None


class ProjectDialog(QDialog):
    """«Nouveau projet»: the project's name -- which names its folder too --, where that folder goes, and the project's language, nothing else (issue #90, the engineer, 21.10.2026: «La fenêtre qui s'ouvre pour créer le nouveau projet doit uniquement demander le nom du projet, qui sera le nom du dossier créé, ainsi que l'endroit où ce dossier doit être créé»; and 22.10.2026: «le choix de la langue se fait lors de la création du projet»). The folder is shown before it is made. Everything else -- the title page, the form, each document's content template, the version pinned -- is the «Projet» tab's (project_tab.py), where the window opens on the new project.

    The language is the project's for good: the document's and the engine's both (docs/typst/language.md §4bis), the settings' report language at first."""

    def __init__(self, parent, lang, location=None):
        super().__init__(parent)
        self.t = STRINGS[lang]
        self.lang = lang
        self.setWindowTitle(self.t["proj_new_title"])
        self.setMinimumWidth(520)
        layout = QVBoxLayout(self)
        hint = QLabel(self.t["proj_hint_new"])
        hint.setWordWrap(True)
        layout.addWidget(hint)
        form = QFormLayout()
        self.settings = usersettings.read()
        self.name = QLineEdit()
        form.addRow(self.t["proj_name"], self.name)
        row = QHBoxLayout()
        self.location = QLineEdit(str(location or Path.home()))
        choose = QPushButton(self.t["proj_choose"])
        choose.clicked.connect(self.choose_location)
        row.addWidget(self.location, 1)
        row.addWidget(choose)
        form.addRow(self.t["proj_location"], row)
        self.language = QComboBox()
        for code in templates.LANGUAGES:
            self.language.addItem(settings_dialog.LANGUAGE_NAMES[code], code)
        own = templates.defaults(self.settings)
        self.language.setCurrentIndex(max(0, self.language.findData(own["report_language"] or templates.DEFAULT_LANGUAGE)))
        self.language.setToolTip(self.t["proj_language_hint"])
        form.addRow(self.t["proj_language"], self.language)
        self.folder = QLabel()
        self.folder.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        form.addRow(self.t["proj_folder"], self.folder)
        self.name.textChanged.connect(self.update_folder)
        self.location.textChanged.connect(self.update_folder)
        self.update_folder()
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def choose_location(self):
        folder = QFileDialog.getExistingDirectory(self, self.t["proj_location"], self.location.text())
        if folder:
            self.location.setText(folder)

    def target(self):
        """The new project's folder: the location and, inside it, a folder named after the project."""
        name = self.name.text().strip()
        return Path(self.location.text().strip()) / Path(project_template.file_name(name or "Projekt")).stem

    def update_folder(self):
        self.folder.setText(str(self.target()))

    def values(self):
        """What the dialog says: the name and the language."""
        return {"name": self.name.text().strip(), "language": self.language.currentData()}

    def accept(self):
        if not self.name.text().strip():
            notices_ui.inline_error(self, self.t["proj_name_needed"])
            return
        super().accept()


def create_project(parent, lang, location=None):
    """«Nouveau projet»: asks the name, the place and the language, makes the project -- Standard laid out in three documents, in that language, with the settings' default form and its title page's people from the settings' defaults, and **no document yet** (project_template.create_skeleton, issue #90) -- and returns its file; None where the engineer cancelled or it failed (and was told). Each document is made later from the «Projet» tab."""
    dialog = ProjectDialog(parent, lang, location=location)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    values = dialog.values()
    settings = usersettings.read()
    people = {key: value for key, value in templates.defaults(settings).items() if key in templates.PEOPLE and value}
    try:
        # Copying the skeleton touches no widget: it runs in a thread of its own, the page held with the card over it meanwhile (busy.py, v0.113)
        here = busy.run_in_thread(parent, STRINGS[lang]["busy_creating"], lambda: project_template.create_skeleton(
            dialog.target(), values["name"], values["language"], form=forms.default_ref(settings), **people))
    except forms.FormError as exc:
        notices_ui.tell(STRINGS[lang]["proj_failed"].format(error=settings_dialog.form_error_text(lang, exc)), notifications.CRITICAL, exc=exc, source="home_page")
        return None
    except (project.ProjectError, OSError) as exc:
        notices_ui.tell(STRINGS[lang]["proj_failed"].format(error=exc), notifications.CRITICAL, exc=exc, source="home_page")
        return None
    return here.file


def apply_form(parent, lang, here, form, current=None):
    """Project `here` switched to layout template `form` (a forms.Form) once the engineer agrees -- its `Template/` and title.typ replaced, the old ones archived in _Archiv, the engineer's adjustments in a config.typ of the new format kept, an old monolithic config.typ replaced and archived (forms.apply) -- so the next compile of each of the three documents prints with it. `current` is the form in use, None for an old config.typ. What the «Projet» tab's «Appliquer au projet…» does (issue #88). Returns whether it was applied; a refusal is said in the window's words."""
    question = STRINGS[lang]["proj_form_ask" if current is not None else "proj_form_ask_old"].format(form=form.name(lang))
    asked = QMessageBox.question(parent, form.name(lang), question,
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
    if asked != QMessageBox.StandardButton.Yes:
        return False
    try:
        forms.apply(here, form)
    except forms.FormError as exc:
        notices_ui.tell(STRINGS[lang]["proj_form_failed"].format(error=settings_dialog.form_error_text(lang, exc)), notifications.CRITICAL, exc=exc, source="home_page")
        return False
    except OSError as exc:
        notices_ui.tell(STRINGS[lang]["proj_form_failed"].format(error=exc), notifications.CRITICAL, exc=exc, source="home_page")
        return False
    return True


def choose_project_file(parent, lang, start=None):
    file, _filter = QFileDialog.getOpenFileName(parent, STRINGS[lang]["home_open"].rstrip("…"), str(start or Path.home()), PROJECT_FILTER[lang])
    return file or None


class RecentList(QTreeWidget):
    """The recent projects, one row each; a .woodcore dropped on it is opened, as it is anywhere on the page."""

    dropped = Signal(str)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setRootIsDecorated(False)
        self.setUniformRowHeights(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def dragEnterEvent(self, event):
        if woodcore_files(event.mimeData()):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if woodcore_files(event.mimeData()):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        files = woodcore_files(event.mimeData())
        if files:
            event.acceptProposedAction()
            self.dropped.emit(files[0])
        else:
            super().dropEvent(event)


def woodcore_files(mime):
    return [url.toLocalFile() for url in mime.urls() if url.isLocalFile() and url.toLocalFile().lower().endswith(project.EXTENSION)] if mime.hasUrls() else []


class HomeWindow(QMainWindow):
    """The start page. `open_project(file)` is the window's own opening -- the lock asked, the window built -- and returns whether the project opened, in which case this page closes."""

    def __init__(self, open_project, icon=None):
        super().__init__()
        theme.ensure()  # the site's look, where no main() applied it first (theme.py, v0.90)
        self.open_project = open_project
        self.settings = usersettings.read()
        self.lang = self.settings.get("lang") if self.settings.get("lang") in LANGUAGES else "fr"
        self.icon = icon
        self.setAcceptDrops(True)
        self.setWindowTitle("Woodcore")
        self.resize(980, 560)
        self.build()

    def t(self, key, **values):
        text = STRINGS[self.lang][key]
        return text.format(**values) if values else text

    def build(self):
        """The page, after the site's (v0.91): the brand and the language at the top; at the left what there is to start with, as the site sets its features -- a new project, a project opened -- and at the right the recent projects as cards, the last first, the one to open with Enter selected."""
        main = QWidget()
        layout = QVBoxLayout(main)
        layout.setContentsMargins(20, 16, 20, 14)
        layout.setSpacing(12)
        top = QHBoxLayout()
        top.setSpacing(12)
        if self.icon is not None:
            mark = QLabel()
            mark.setPixmap(QIcon(self.icon).pixmap(40, 40))
            top.addWidget(mark)
        brand = QLabel("Woodcore")
        brand.setObjectName("brand")
        brand.setFont(theme.brand_font())   # following the zoom (issue #85)
        top.addWidget(brand)
        version = QLabel(self.t("home_version", version=project.VERSION))
        version.setObjectName("meta")
        top.addWidget(version)
        top.addStretch(1)
        # the notices, as in the window: what failed to open or to be made is said here, under the octagon and the triangle (notices_ui.py, v0.117)
        self.notice_bar = notices_ui.NoticeBar(notices_ui.words(self.lang), self.lang)
        top.addWidget(self.notice_bar)
        top.addSpacing(4)
        self.language = chrome.LanguageSwitch(LANGUAGES, self.lang)
        self.language.setToolTip(self.t("home_language").rstrip(" :"))
        self.language.currentIndexChanged.connect(self.on_language)
        top.addWidget(self.language)
        # *Paramètres…* (Ctrl+,), as in the window's File menu: the templates a new project is made from, and the defaults (settings_dialog.py, v0.94)
        self.settings_button = QPushButton(settings_dialog.menu_text(self.lang).replace("&", ""))
        self.settings_button.clicked.connect(self.open_settings)
        top.addWidget(self.settings_button)
        QShortcut(QKeySequence(settings_dialog.SHORTCUT), main, activated=self.open_settings)
        for action in chrome.zoom_actions(main, self.t):   # Ctrl+ / Ctrl− / Ctrl+0, as in the window's «Affichage» menu (issue #85)
            main.addAction(action)
        layout.addLayout(top)

        columns = QHBoxLayout()
        columns.setSpacing(24)
        start = QVBoxLayout()
        start.setSpacing(10)
        eyebrow = QLabel(self.t("home_start").upper())
        eyebrow.setObjectName("eyebrow")
        start.addWidget(eyebrow)
        self.cards = {}
        for key, text, slot in (("home_new", "home_new_text", self.new), ("home_open", "home_open_text", self.choose)):
            card = chrome.ActionCard(key, self.t(key).rstrip("…"), self.t(text))
            card.clicked.connect(slot)
            start.addWidget(card)
            self.cards[key] = card
        start.addStretch(1)
        left = QWidget()
        left.setLayout(start)
        left.setFixedWidth(320)
        columns.addWidget(left)

        recent = QVBoxLayout()
        recent.setSpacing(6)
        heading = QLabel(self.t("home_recent").upper())
        heading.setObjectName("eyebrow")
        recent.addWidget(heading)
        self.list = RecentList()
        self.list.setObjectName("recent")
        self.list.setHeaderLabels([self.t("home_col_name"), self.t("home_col_number"), self.t("home_col_folder"), self.t("home_col_exported"), self.t("home_col_engine")])
        # One card per project across the row: the first column is painted over the whole of it, the other four keep their data for the card to read (chrome.RecentCardDelegate)
        self.list.setHeaderHidden(True)
        for column in range(1, 5):
            self.list.setColumnHidden(column, True)
        self.list.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.list.setUniformRowHeights(True)
        self.list.setMouseTracking(True)
        self.list.setItemDelegate(chrome.RecentCardDelegate(self.list, {
            "number": self.t("home_col_number"), "exported": self.t("home_col_exported"),
            "engine": self.t("home_engine"), "current": project.VERSION}))
        self.list.itemActivated.connect(lambda item, _column: self.open_item(item))
        self.list.customContextMenuRequested.connect(self.context_menu)
        self.list.dropped.connect(self.open_file)
        recent.addWidget(self.list, 1)
        self.empty = QLabel(self.t("home_empty"))
        self.empty.setWordWrap(True)
        recent.addWidget(self.empty)
        hint = QLabel(self.t("home_drop_hint"))
        hint.setObjectName("meta")
        hint.setWordWrap(True)
        recent.addWidget(hint)
        columns.addLayout(recent, 1)
        layout.addLayout(columns, 1)

        buttons = QHBoxLayout()
        buttons.addWidget(legal.copyright_label(main))   # © 2026 Florian Lamprecht · woodcore@pineo.ch (legal.py)
        buttons.addStretch(1)
        self.open_button = QPushButton(self.t("home_open_selected"))
        self.open_button.setProperty("primary", True)  # the page's one primary action, in the site's teal
        self.open_button.setDefault(True)
        self.open_button.clicked.connect(lambda: self.open_item(self.list.currentItem()))
        buttons.addWidget(self.open_button)
        layout.addLayout(buttons)
        self.setCentralWidget(main)
        self.fill()

    def retheme(self):
        """The scheme changed while the page is open (theme.set_appearance, Windows switching): built again, for the one colour it states itself."""
        self.build()

    def rows(self):
        """The recent projects, and -- where the list holds nothing yet -- the project beside the program's sources. A project whose file is no longer there -- moved, renamed, deleted, or not synced yet on this machine -- is taken off the list here and written so (the engineer's decision of 03.10.2026: «ce projet-là doit disparaître»): opened again with «Ouvrir…», it comes back. One that is there and cannot be read stays, greyed, its error as its tooltip."""
        files = usersettings.recent_projects(self.settings)
        kept = [f for f in files if Path(f).is_file()]
        if len(kept) != len(files):
            for gone in files:
                if gone not in kept:
                    self.settings = usersettings.forget(self.settings, gone)
            usersettings.write(self.settings)
            files = usersettings.recent_projects(self.settings)
        beside = project.checkout_project()
        suggested = beside is not None and not files
        if suggested:
            files = [str(beside)]
        return [dict(summary(f), suggested=suggested) for f in files]

    def fill(self):
        self.list.clear()
        muted = self.palette().color(QPalette.ColorRole.PlaceholderText)
        rows = self.rows()
        for row in rows:
            exported = row["exported"].strftime("%d.%m.%Y %H:%M") if row["exported"] else self.t("home_never")
            item = QTreeWidgetItem([row["name"], row["number"], row["folder"], exported, row["engine"]])
            item.setData(0, Qt.ItemDataRole.UserRole, row["file"])
            item.setData(1, Qt.ItemDataRole.UserRole, bool(row["error"]))
            tip = row["error"] or (self.t("home_beside") if row["suggested"] else row["file"])
            for column in range(5):
                item.setToolTip(column, tip)
                if row["error"]:
                    item.setForeground(column, muted)
            self.list.addTopLevelItem(item)
        for column in (0, 1, 3, 4):
            self.list.resizeColumnToContents(column)
        self.empty.setVisible(not rows)
        if rows:
            self.list.setCurrentItem(self.list.topLevelItem(0))
            self.list.setFocus()   # Enter opens the last project, as the window opened it straight away until v0.83
        self.open_button.setEnabled(bool(rows))

    def on_language(self, index):
        self.lang = self.language.itemData(index)
        self.settings["lang"] = self.lang
        usersettings.write(self.settings)
        self.build()

    def open_settings(self):
        """*Paramètres…* from the start page: no project is open here, so «Enregistrer la forme de ce projet comme template de forme» is closed, its reason in its tooltip."""
        settings_dialog.open_dialog(self, self.lang)
        self.settings = usersettings.read()

    def open_item(self, item):
        if item is None:
            return
        file = item.data(0, Qt.ItemDataRole.UserRole)
        if not Path(file).is_file():
            # gone since the page was drawn: taken off the list, and said
            self.forget(file)
            notices_ui.tell(self.t("home_missing_gone", path=file), notifications.WARNING, key="home_missing_gone", args=dict(path=file), source="home_page")
            return
        self.open_file(file)

    def open_file(self, file):
        if file and self.open_project(file):
            self.close()

    def forget(self, file):
        self.settings = usersettings.forget(usersettings.read(), file)
        usersettings.write(self.settings)
        self.fill()

    def context_menu(self, point):
        item = self.list.itemAt(point)
        if item is None:
            return
        file = item.data(0, Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        menu.addAction(self.t("home_open_selected"), lambda: self.open_item(item))
        folder = menu.addAction(self.t("home_show_folder"), lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(file).parent))))
        folder.setEnabled(Path(file).parent.is_dir())
        menu.addAction(self.t("home_forget"), lambda: self.forget(file))
        menu.exec(self.list.viewport().mapToGlobal(point))

    def start_folder(self):
        """Where a file dialog opens: beside the last project, else the user's own folder."""
        recent = usersettings.recent_projects(self.settings)
        for file in recent:
            if Path(file).parent.is_dir():
                return Path(file).parent.parent
        beside = project.checkout_project()
        return beside.parent.parent if beside else Path.home()

    def choose(self):
        self.open_file(choose_project_file(self, self.lang, self.start_folder()))

    def new(self):
        self.open_file(create_project(self, self.lang, self.start_folder()))

    def dragEnterEvent(self, event):
        if woodcore_files(event.mimeData()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        files = woodcore_files(event.mimeData())
        if files:
            event.acceptProposedAction()
            self.open_file(files[0])
