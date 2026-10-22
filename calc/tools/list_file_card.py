"""The card of a list Woodcore writes once in raw Typst -- the journal, the list of the positions, the quantities (calc/domains/list_files.py; spec 2026-10-21-commandes-typst-refonte, REQ-017, UI-003, Q-008): where its file is, «Écrire le fichier» where it has none, «Ajouter» the rows of the export it does not hold yet, «Copier l'inclusion» the `#include` a section prints it with. The file is the engineer's once written: nothing here rewrites a row of it."""

from PySide6.QtWidgets import QApplication, QHBoxLayout, QPushButton, QVBoxLayout

import cards
import notices_ui
import project
from domains import list_files

STRINGS = {
    "fr": {
        "lf_title": "Fichier de la liste",
        "lf_none": "Pas encore de fichier : « Écrire le fichier » l’écrit une fois, chaque cellule tenue à jour par #sync. Il est ensuite à vous.",
        "lf_file": "Fichier : {file} — à vous ; l’export signale une cellule qui ne dit plus la donnée.",
        "lf_missing": "{n} ligne(s) de l’export ne sont pas dans le fichier : {ids}.",
        "lf_complete": "Le fichier tient toutes les lignes de l’export.",
        "lf_write": "Écrire le fichier",
        "lf_add": "Ajouter",
        "lf_copy": "Copier l’inclusion",
        "lf_written": "{file} écrit.",
        "lf_added": "{n} ligne(s) ajoutée(s) à {file}.",
        "lf_refused": "{error}",
        "lf_add_why": "Le fichier tient déjà toutes les lignes de l’export.",
        "lf_copy_why": "Pas encore de fichier à inclure : écrivez-le d’abord.",
    },
    "de": {
        "lf_title": "Datei der Liste",
        "lf_none": "Noch keine Datei: «Datei schreiben» schreibt sie einmal, jede Zelle durch #sync nachgeführt. Danach gehört sie Ihnen.",
        "lf_file": "Datei: {file} — gehört Ihnen; der Export meldet eine Zelle, die nicht mehr die Daten sagt.",
        "lf_missing": "{n} Zeile(n) des Exports fehlen in der Datei: {ids}.",
        "lf_complete": "Die Datei enthält alle Zeilen des Exports.",
        "lf_write": "Datei schreiben",
        "lf_add": "Hinzufügen",
        "lf_copy": "Einbindung kopieren",
        "lf_written": "{file} geschrieben.",
        "lf_added": "{n} Zeile(n) zu {file} hinzugefügt.",
        "lf_refused": "{error}",
        "lf_add_why": "Die Datei enthält schon alle Zeilen des Exports.",
        "lf_copy_why": "Noch keine Datei zum Einbinden: schreiben Sie sie zuerst.",
    },
    "en": {
        "lf_title": "The list's file",
        "lf_none": "No file yet: «Write the file» writes it once, each cell kept in step by #sync. It is yours afterwards.",
        "lf_file": "File: {file} — yours; the export says a cell that no longer says its data.",
        "lf_missing": "{n} row(s) of the export are not in the file: {ids}.",
        "lf_complete": "The file holds every row of the export.",
        "lf_write": "Write the file",
        "lf_add": "Add",
        "lf_copy": "Copy the include",
        "lf_written": "{file} written.",
        "lf_added": "{n} row(s) added to {file}.",
        "lf_refused": "{error}",
        "lf_add_why": "The file holds every row of the export already.",
        "lf_copy_why": "No file to include yet: write it first.",
    },
}


class ListFileCard:
    """The card, built into a tab's layout: `kind` one of list_files.KINDS, `document` a function giving the document whose journal it is ("rs" for the other two)."""

    def __init__(self, app, kind, document=lambda: "rs"):
        self.app, self.kind, self.document = app, kind, document
        self.t = app.t
        self.card = cards.card(self.t("lf_title"))
        column = QVBoxLayout(self.card)
        self.state = cards.note("")
        column.addWidget(self.state)
        row = QHBoxLayout()
        self.write_button = QPushButton(self.t("lf_write"))
        self.write_button.clicked.connect(self.write)
        self.add_button = QPushButton(self.t("lf_add"))
        self.add_button.clicked.connect(self.add)
        self.copy_button = QPushButton(self.t("lf_copy"))
        self.copy_button.clicked.connect(self.copy)
        for button in (self.write_button, self.add_button, self.copy_button):
            row.addWidget(button)
        row.addStretch(1)
        column.addLayout(row)

    def path(self):
        try:
            return list_files.path(project.current(), self.kind, self.document())
        except project.ProjectError:
            return None

    def refresh(self):
        """What the card says of the file now: none yet, or the rows of the export it misses."""
        path = self.path()
        if path is None:
            self.card.setVisible(False)
            return
        self.card.setVisible(True)
        here = project.current()
        exists = path.is_file()
        missing = list_files.missing(here, self.kind, self.document()) if exists else []
        lines = [self.t("lf_file", file=here.rel(path)) if exists else self.t("lf_none")]
        if exists:
            lines.append(self.t("lf_missing", n=len(missing), ids=", ".join(missing[:8]) + (" …" if len(missing) > 8 else "")) if missing else self.t("lf_complete"))
        self.state.setText("\n".join(lines))
        self.write_button.setVisible(not exists)
        self.add_button.setVisible(exists)
        self.add_button.setEnabled(bool(missing))
        self.add_button.setToolTip("" if missing else self.t("lf_add_why"))
        self.copy_button.setEnabled(exists)
        self.copy_button.setToolTip("" if exists else self.t("lf_copy_why"))

    def write(self):
        here = project.current()
        try:
            path = list_files.write(here, self.kind, self.document())
        except list_files.ListError as exc:
            notices_ui.tell(self.t("lf_refused", error=exc), notices_ui.notifications.WARNING, exc=exc, code="list_file_refused", key="lf_refused", args={"error": str(exc)}, source="lists")
        else:
            self.app.set_status(self.t("lf_written", file=here.rel(path)))
        self.refresh()

    def add(self):
        here = project.current()
        try:
            added = list_files.add(here, self.kind, self.document())
        except list_files.ListError as exc:
            notices_ui.tell(self.t("lf_refused", error=exc), notices_ui.notifications.WARNING, exc=exc, code="list_file_refused", key="lf_refused", args={"error": str(exc)}, source="lists")
        else:
            self.app.set_status(self.t("lf_added", n=len(added), file=here.rel(self.path())))
        self.refresh()

    def include(self):
        path = self.path()
        return None if path is None else f'#include "{project.current().from_root(path)}"'

    def copy(self):
        call = self.include()
        if call:
            QApplication.clipboard().setText(call)
