"""The question a deletion of positions asks before anything is written (issue #9, spec docs/requirements/completed/2026-10-08-plan-positions-cotes-numerotation-sections.md, REQ-004, REQ-005, REQ-016, D-002, D-010, D-013).

What it shows is calc/renumbering.py's preview and never restated: the positions deleted, the numbers that move down (S111 → S110), and every occurrence of an id in a file it would rewrite, with its line, each of which may be unticked -- a steel grade «S355» in a prose page, when a position S355 exists. A position still cited is refused, unless its values are kept («Copier les valeurs»: S110-old, and a note in orange wherever it is called); one still drawn on a plan is refused, the element going first. What is written is no step of «Annuler»: the files are copied into the project's archives first, which is how it is undone, and the dialog says so. Another tab with unsaved changes is asked to save first, its draft holding numbers the renumbering would leave behind.

The words are this module's own, in the three languages of the window (calc/tools/migrate_dialog.py's pattern).
"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QMessageBox, QTreeWidget, QTreeWidgetItem, QVBoxLayout

import notices_ui  # what was a message box is a notice since v0.117
import notifications
import project
import renumbering
import sharing
import validation

STRINGS = {
    "fr": {
        "rn_title": "Supprimer et renuméroter",
        "rn_intro": "Supprimer {ids} — aucun plan ne {verb} dessine plus.",
        "rn_verb_one": "la",
        "rn_verb_many": "les",
        "rn_moves": "Renumérotées : {moves}.",
        "rn_moves_none": "Aucune autre position ne change de numéro.",
        "rn_archived": "Valeurs gardées sous : {names} (message orange partout où elles sont appelées).",
        "rn_files": "Remplacements dans les fichiers — décocher ceux qui ne citent pas une position :",
        "rn_col_file": "Fichier",
        "rn_col_line": "Ligne",
        "rn_col_change": "Remplacement",
        "rn_col_text": "Texte",
        "rn_not_undoable": "Ne s'annule pas avec « Annuler » : une copie des fichiers modifiés est gardée dans les archives du projet.",
        "rn_apply": "Supprimer et renuméroter",
        "rn_keep": "Garder la position",
        "rn_cited": "{ids} est encore citée — la suppression est refusée tant qu'elle l'est :\n{where}\n\n« Copier les valeurs » la supprime quand même : ses valeurs sont gardées sous {names}, les citations y renvoient et le rapport l'indique en orange.",
        "rn_copy": "Copier les valeurs",
        "rn_drawn": "{ids} est encore dessinée sur un plan ({plans}) : effacer d'abord l'élément.",
        "rn_dirty": "Un autre onglet a des modifications non enregistrées ({tabs}) : les enregistrer d'abord, la renumérotation réécrit leurs fichiers.",
        "rn_failed": "La renumérotation n'a rien écrit : {error}",
        "rn_read_only": "Le projet est ouvert en lecture seule : rien n'est supprimé.",
    },
    "de": {
        "rn_title": "Löschen und neu nummerieren",
        "rn_intro": "{ids} löschen — kein Plan zeichnet {verb} mehr.",
        "rn_verb_one": "sie",
        "rn_verb_many": "sie",
        "rn_moves": "Neu nummeriert: {moves}.",
        "rn_moves_none": "Keine andere Position ändert ihre Nummer.",
        "rn_archived": "Werte behalten unter: {names} (orange Meldung, wo immer sie aufgerufen werden).",
        "rn_files": "Ersetzungen in den Dateien — abwählen, was keine Position nennt:",
        "rn_col_file": "Datei",
        "rn_col_line": "Zeile",
        "rn_col_change": "Ersetzung",
        "rn_col_text": "Text",
        "rn_not_undoable": "Lässt sich nicht mit «Rückgängig» aufheben: eine Kopie der geänderten Dateien wird im Archiv des Projekts behalten.",
        "rn_apply": "Löschen und neu nummerieren",
        "rn_keep": "Position behalten",
        "rn_cited": "{ids} wird noch aufgerufen — das Löschen wird abgelehnt, solange das so ist:\n{where}\n\n«Werte kopieren» löscht sie trotzdem: ihre Werte werden unter {names} behalten, die Aufrufe verweisen darauf und der Bericht sagt es in Orange.",
        "rn_copy": "Werte kopieren",
        "rn_drawn": "{ids} ist noch auf einem Plan gezeichnet ({plans}): zuerst das Element löschen.",
        "rn_dirty": "Ein anderer Reiter hat ungespeicherte Änderungen ({tabs}): zuerst speichern, die Neunummerierung schreibt ihre Dateien neu.",
        "rn_failed": "Die Neunummerierung hat nichts geschrieben: {error}",
        "rn_read_only": "Das Projekt ist schreibgeschützt geöffnet: nichts wird gelöscht.",
    },
    "en": {
        "rn_title": "Delete and renumber",
        "rn_intro": "Delete {ids} — no plan draws {verb} any more.",
        "rn_verb_one": "it",
        "rn_verb_many": "them",
        "rn_moves": "Renumbered: {moves}.",
        "rn_moves_none": "No other position changes its number.",
        "rn_archived": "Values kept as: {names} (an orange note wherever they are called).",
        "rn_files": "Replacements in the files — untick those that do not name a position:",
        "rn_col_file": "File",
        "rn_col_line": "Line",
        "rn_col_change": "Replacement",
        "rn_col_text": "Text",
        "rn_not_undoable": "Not undone by «Undo»: a copy of the files changed is kept in the project's archives.",
        "rn_apply": "Delete and renumber",
        "rn_keep": "Keep the position",
        "rn_cited": "{ids} is still cited — the deletion is refused while it is:\n{where}\n\n«Copy the values» deletes it all the same: its values are kept as {names}, the citations point there and the report says so in orange.",
        "rn_copy": "Copy the values",
        "rn_drawn": "{ids} is still drawn on a plan ({plans}): delete the element first.",
        "rn_dirty": "Another tab has unsaved changes ({tabs}): save them first, the renumbering rewrites their files.",
        "rn_failed": "The renumbering wrote nothing: {error}",
        "rn_read_only": "The project is open read-only: nothing is deleted.",
    },
}


# A test's answers in place of the dialog and of the «Copier les valeurs» question: `CONFIRM(result)` → (accepted, unticked keys), `KEEP(result, names)` → bool.
CONFIRM = None
KEEP = None


def _t(lang):
    return STRINGS[lang if lang in STRINGS else "en"]


def _rel(here, path):
    try:
        return Path(path).resolve().relative_to(Path(here.root).resolve()).as_posix()
    except ValueError:
        return str(path)


def summary(t, result):
    """The dialog's text above the list: what is deleted, what moves, where the values are kept, and that it is no step of «Annuler»."""
    deleted = ", ".join(result.deleted)
    lines = [t["rn_intro"].format(ids=deleted, verb=t["rn_verb_one" if len(result.deleted) == 1 else "rn_verb_many"])]
    moves = ", ".join(f"{old} → {new}" for old, new in result.mapping.items())
    lines.append(t["rn_moves"].format(moves=moves) if moves else t["rn_moves_none"])
    if result.archived:
        lines.append(t["rn_archived"].format(names=", ".join(result.archived.values())))
    lines.append(t["rn_not_undoable"])
    return "\n".join(lines)


class RenumberDialog(QDialog):
    """The preview shown, every occurrence ticked; `unchecked()` the keys of those the engineer unticked."""

    def __init__(self, parent, lang, here, result):
        super().__init__(parent)
        t = _t(lang)
        self.setWindowTitle(t["rn_title"])
        self.resize(820, 520)
        layout = QVBoxLayout(self)
        intro = QLabel(summary(t, result))
        intro.setWordWrap(True)
        layout.addWidget(intro)
        if result.occurrences:
            layout.addWidget(QLabel(t["rn_files"]))
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([t["rn_col_file"], t["rn_col_line"], t["rn_col_change"], t["rn_col_text"]])
        self.items = []
        for occurrence in sorted(result.occurrences, key=lambda o: (str(o.path), o.start)):
            item = QTreeWidgetItem([_rel(here, occurrence.path), str(occurrence.line), f"{occurrence.old} → {occurrence.new}", occurrence.text.strip()])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(0, Qt.CheckState.Checked)
            self.tree.addTopLevelItem(item)
            self.items.append((item, occurrence.key))
        for column in range(3):
            self.tree.resizeColumnToContents(column)
        self.tree.setVisible(bool(result.occurrences))
        layout.addWidget(self.tree, 1)
        buttons = QDialogButtonBox()
        buttons.addButton(t["rn_apply"], QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton(t["rn_keep"], QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def unchecked(self):
        return [key for item, key in self.items if item.checkState(0) != Qt.CheckState.Checked]


def _keep_values(parent, t, result, archived_names):
    """The question a position still cited asks: «Copier les valeurs» or keep it."""
    where = "\n".join(f"• {Path(o.path).name}:{o.line}  {o.text.strip()}" for found in result.cited.values() for o in found)
    box = QMessageBox(QMessageBox.Icon.Warning, t["rn_title"],  # dialog-ok: a decision -- delete with the values kept, or keep the position -- that waits for its answer
                      t["rn_cited"].format(ids=", ".join(pid for pid, found in result.cited.items() if found), where=where, names=", ".join(archived_names)), parent=parent)
    copy = box.addButton(t["rn_copy"], QMessageBox.ButtonRole.AcceptRole)
    box.addButton(t["rn_keep"], QMessageBox.ButtonRole.RejectRole)
    box.exec()
    return box.clickedButton() is copy


def _confirm(parent, lang, here, result):
    """The engineer's yes: a plain question where no file is rewritten -- nothing to untick --, the dialog with its list otherwise."""
    if CONFIRM is not None:
        return CONFIRM(result)
    if not result.occurrences:
        t = _t(lang)
        return QMessageBox.question(parent, t["rn_title"], summary(t, result)) == QMessageBox.StandardButton.Yes, []
    dialog = RenumberDialog(parent, lang, here, result)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return False, []
    return True, dialog.unchecked()


def dirty_tabs(app, but=None):
    """The window's other tabs that hold unsaved changes -- a draft whose numbers a renumbering would leave behind."""
    return [tab for tab in getattr(app, "tabs", []) if tab is not but and getattr(tab, "dirty", False)]


def ask(parent, app, deleted, here=None, keep_values=None, confirm=None, tell=None):
    """Deletes the positions `deleted` and numbers the ones after them again everywhere -- once the engineer has seen what it does and agreed. Returns the folder the files were copied into, or None where nothing was written. `keep_values(result, names)`, `confirm(result)` → (accepted, unticked keys) and `tell(text)` are the questions and the message boxes, given by a test in their place."""
    here = here or project.current()
    t = _t(getattr(app, "lang", "fr"))
    tell = tell or (lambda text: notices_ui.tell(text, notifications.WARNING, source="renumber_dialog"))
    if getattr(app, "read_only", False):
        tell(t["rn_read_only"])
        return None
    others = dirty_tabs(app, but=parent)
    if others:
        tell(t["rn_dirty"].format(tabs=", ".join(getattr(tab, "TITLE", type(tab).__name__) for tab in others)))
        return None
    try:
        result = renumbering.preview(here, deleted)
        drawn = {pid: plans for pid, plans in result.drawn.items() if plans}
        if drawn:
            tell(t["rn_drawn"].format(ids=", ".join(drawn), plans=", ".join(sorted({Path(p).stem for plans in drawn.values() for p in plans}))))
            return None
        if result.refused:
            kept = renumbering.preview(here, deleted, keep_values=True)
            if not (keep_values or KEEP or (lambda r, names: _keep_values(parent, t, r, names)))(result, list(kept.archived.values())):
                return None
            result = kept
        accepted, unticked = (confirm or (lambda r: _confirm(parent, getattr(app, "lang", "fr"), here, r)))(result)
        if not accepted:
            return None
        return renumbering.apply(here, result, unticked)
    except (renumbering.RenumberError, sharing.SharingError, validation.ValidationError, OSError) as exc:
        tell(t["rn_failed"].format(error=exc))
        return None
