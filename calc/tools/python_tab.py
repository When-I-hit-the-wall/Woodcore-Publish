"""Woodcore's «Python» tab (docs/domain/scripts.md §3.3sexdecies, docs/ui/window.md §10quater, v0.100): the engineer writes Python, runs it, and reads the values his variables took without going to a terminal.

The engineer: «Je souhaite avoir un onglet dans woodcore, où le user peut écrire du code python et le run. Idéalement, un volet à droite permettrait d'afficher les valeurs prises par les variables lors du run, afin de ne pas avoir à lire le terminal (intégré dans woodcore) à chaque fois» -- so the right pane carries three cards: the **results** the script declared, the **variables** its globals held when it ended, and the **output** it printed.

**What it is for** is solving an equation or a system of them, which is what he asked SciPy for and settled on numpy alone for (requirements.txt). A result reaches the report by being declared: `result("H_d", 2.2, "kN")`, exported into `data/scripts.json`, read with `#val("H_d", domain: ("script", "portique"))` -- the traceable route of the three he was offered, and the one he chose.

**A script is a Python file and its identity is in it**, as three `@` comment keys at the top -- `@name`, `@label`, `@group` (calc/domains/script.py). ⚠️ So this tab shows them **read-only** rather than offering a form for them, which is a deliberate departure from every other editor tab: the engineer edits the file in this very pane, and a form beside it would be a second place for one thing (section 2 rule 1) and a round-trip to keep right. The ID is the file's name, and *Renommer* renames the file.

**Every write goes through calc/domains/script.py**, as every other tab writes through its own domain module, and *Exécuter* saves, runs and exports in that order -- so what ran is what is on disk, which is what the export will run, and the report follows at once without the whole export being run again.

⚠️ **The run is in a process of its own** and cannot take the window with it, which is the whole reason the tab is thin: it edits text, spawns `woodcore-cli run-script`, and shows what came back.
"""

import source_editor  # Ctrl+S bound the one way (source_editor.save_shortcut)
import re

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QHeaderView, QInputDialog, QLabel, QLineEdit, QMessageBox,
    QPlainTextEdit, QPushButton, QSplitter, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

import build_reference as ref  # the one place a Typst call is spelled out (docs/typst/reference-workbook.md §10ter)
import cards  # the form in cards, after the website (cards.py, v0.93)
import autosave  # saving without a question, and what is never saved without the engineer (autosave.py, v0.117)
import grouped_list
import project
import richtext  # the calls coloured as the site's code, «Copié ✓» (richtext.py, v0.92)
import theme
from domains import script as model  # the one module that reads, runs and exports Woodcore-Datei/scripts/<id>.py

# What a new script starts from: the identity keys, what the API gives, and a solved system -- so that the first thing the engineer sees is a script that runs and declares something.
TEMPLATE = '''# @name {name}
# @label
# @group
"""What this script works out.

What it is given, and nothing else:
    result(name, value, unit="", symbol=None, label=None, descr=None, norm=None, norm_ref="")
        declares a value the report reads with #var(name, domain: ("script", "{id}"))
    value(domain, instance, name)
        a number out of the export: value("snow-load", "SL", "q_k11")
    PROJECT, DATA
        the project's folder and its export, as pathlib.Path -- to read, not to write

A script reads the project and writes nothing but the results it declares.
"""

import numpy as np
import notifications  # every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # what was a message box is a notice since v0.117 (notices_ui.tell)

# A x = b: two equations, two unknowns
A = np.array([[2.0, 1.0],
              [1.0, 3.0]])
b = np.array([8.0, 13.0])
x, y = np.linalg.solve(A, b)

result("x", x, "kN", label="First unknown")
result("y", y, "kN", label="Second unknown")
'''

# Python's own words, for the editor's colours. Not a parser: a highlighter, which is what a colour is.
KEYWORDS = (
    "and as assert async await break class continue def del elif else except finally for from global "
    "if import in is lambda nonlocal not or pass raise return try while with yield None True False"
).split()
# What the API puts into a script's own scope: coloured as a call, so it is visible that they are given and not imported.
GIVEN = ("result", "value", "PROJECT", "DATA")


class PythonHighlighter(QSyntaxHighlighter):
    """Python coloured with the site's own syntax tokens (theme.json's `syn-*`), the ones `richtext.TypstHighlighter` colours Typst with -- so code reads the same in both panes of the window.

    Line by line, as that one is: a triple-quoted string spanning lines is coloured on its first line only, which is what a `QSyntaxHighlighter` without state does and is enough for a colour.
    """

    def __init__(self, document):
        super().__init__(document)
        self.rules = []
        for token, pattern in (
            ("syn-number", r"\b\d+\.?\d*([eE][-+]?\d+)?\b"),
            ("syn-call", r"\b(" + "|".join(GIVEN) + r")\b"),
            ("syn-keyword", r"\b(" + "|".join(KEYWORDS) + r")\b"),
            ("syn-string", r"('''.*?'''|\"\"\".*?\"\"\"|'[^'\n]*'|\"[^\"\n]*\")"),
            ("syn-comment", r"#[^\n]*"),
        ):
            shape = QTextCharFormat()
            shape.setForeground(QColor(theme.colour(token)))
            if token == "syn-keyword":
                shape.setFontWeight(QFont.Weight.Bold)
            if token == "syn-comment":
                shape.setFontItalic(True)
            self.rules.append((re.compile(pattern), shape))

    def highlightBlock(self, text):
        for pattern, shape in self.rules:      # later rules win: a keyword inside a comment is a comment
            for found in pattern.finditer(text):
                self.setFormat(found.start(), found.end() - found.start(), shape)


STRINGS = {
    "fr": {
        "tab_python": "Python",
        "py_list": "Scripts",
        "py_search": "Chercher un script…",
        "py_new": "Nouveau", "py_duplicate": "Dupliquer", "py_rename": "Renommer", "py_delete": "Supprimer",
        "py_identity": "Identité",
        "py_identity_note": "Le nom, la description et le groupe se lisent dans le fichier, en lignes «# @name», "
                            "«# @label» et «# @group» au début : le script est la source, et un formulaire à côté "
                            "en serait une seconde. L’ID est le nom du fichier ; «Renommer» le change.",
        "py_code": "Code",
        "py_run": "Exécuter", "py_run_hint": "Enregistre le script, l’exécute dans un processus à part, puis exporte "
                                             "ses résultats — le rapport les voit aussitôt. Exécute aussi les autres "
                                             "scripts du projet, l’export les recalculant tous.",
        "py_save": "Enregistrer", "py_revert": "Annuler les modifications",
        "py_results": "Résultats", "py_variables": "Variables", "py_output": "Sortie", "py_commands": "Commandes Typst",
        "py_col_name": "Nom", "py_col_value": "Valeur", "py_col_unit": "Unité", "py_col_label": "Désignation",
        "py_col_type": "Type", "py_col_repr": "Valeur",
        "py_no_results": "Ce script n’a déclaré aucun résultat. Appelez result(\"nom\", valeur, \"unité\") "
                         "pour chaque valeur que le rapport doit lire.",
        "py_no_variables": "Exécutez le script pour voir les valeurs prises par ses variables.",
        "py_never_run": "Pas encore exécuté.",
        "py_ran": "Exécuté en {seconds} s : {results} résultat(s).",
        "py_failed": "L’exécution n’a rien produit : {reason}",
        "py_none": "Aucun script. «Nouveau» en crée un.",
        "py_new_name": "Nom du fichier du nouveau script (sans .py) :",
        "py_rename_name": "Nouveau nom du fichier (sans .py) :",
        "py_taken": "Il y a déjà un script nommé {id}.",
        "py_bad_name": "Un nom de script se limite aux lettres, aux chiffres et à _ . + - — {id} n’en est pas un.",
        "py_delete_ask": "Supprimer le script {id} ? Les appels du rapport qui le nomment cesseront de compiler.",
        "py_leave": "Le script {id} a des modifications non enregistrées. Les enregistrer ?",
        "py_saved": "Script {id} enregistré.",
        "py_export_failed": "Le script est enregistré, mais l’export a échoué : {error}",
    },
    "de": {
        "tab_python": "Python",
        "py_list": "Skripte",
        "py_search": "Skript suchen…",
        "py_new": "Neu", "py_duplicate": "Duplizieren", "py_rename": "Umbenennen", "py_delete": "Löschen",
        "py_identity": "Identität",
        "py_identity_note": "Name, Beschreibung und Gruppe stehen in der Datei selbst, als Zeilen «# @name», "
                            "«# @label» und «# @group» am Anfang: das Skript ist die Quelle, ein Formular daneben "
                            "wäre eine zweite. Die ID ist der Dateiname; «Umbenennen» ändert ihn.",
        "py_code": "Code",
        "py_run": "Ausführen", "py_run_hint": "Speichert das Skript, führt es in einem eigenen Prozess aus und "
                                              "exportiert seine Ergebnisse — der Bericht sieht sie sofort. Führt auch "
                                              "die anderen Skripte des Projekts aus, da der Export alle neu berechnet.",
        "py_save": "Speichern", "py_revert": "Änderungen verwerfen",
        "py_results": "Ergebnisse", "py_variables": "Variablen", "py_output": "Ausgabe", "py_commands": "Typst-Befehle",
        "py_col_name": "Name", "py_col_value": "Wert", "py_col_unit": "Einheit", "py_col_label": "Bezeichnung",
        "py_col_type": "Typ", "py_col_repr": "Wert",
        "py_no_results": "Dieses Skript hat kein Ergebnis angegeben. Rufen Sie result(\"Name\", Wert, \"Einheit\") "
                         "für jeden Wert auf, den der Bericht lesen soll.",
        "py_no_variables": "Führen Sie das Skript aus, um die Werte seiner Variablen zu sehen.",
        "py_never_run": "Noch nicht ausgeführt.",
        "py_ran": "In {seconds} s ausgeführt: {results} Ergebnis(se).",
        "py_failed": "Die Ausführung hat nichts ergeben: {reason}",
        "py_none": "Kein Skript. «Neu» legt eines an.",
        "py_new_name": "Dateiname des neuen Skripts (ohne .py):",
        "py_rename_name": "Neuer Dateiname (ohne .py):",
        "py_taken": "Es gibt bereits ein Skript namens {id}.",
        "py_bad_name": "Ein Skriptname besteht aus Buchstaben, Zahlen und _ . + - — {id} ist keiner.",
        "py_delete_ask": "Das Skript {id} löschen? Aufrufe des Berichts, die es nennen, lassen sich dann nicht mehr kompilieren.",
        "py_leave": "Das Skript {id} hat nicht gespeicherte Änderungen. Speichern?",
        "py_saved": "Skript {id} gespeichert.",
        "py_export_failed": "Das Skript ist gespeichert, aber der Export ist gescheitert: {error}",
    },
    "en": {
        "tab_python": "Python",
        "py_list": "Scripts",
        "py_search": "Find a script…",
        "py_new": "New", "py_duplicate": "Duplicate", "py_rename": "Rename", "py_delete": "Delete",
        "py_identity": "Identity",
        "py_identity_note": "The name, the description and the group are read from the file itself, as «# @name», "
                            "«# @label» and «# @group» lines at its top: the script is the source, and a form beside "
                            "it would be a second one. The ID is the file's name; «Rename» changes it.",
        "py_code": "Code",
        "py_run": "Run", "py_run_hint": "Saves the script, runs it in a process of its own, then exports its results "
                                        "— the report sees them at once. It runs the project's other scripts too, the "
                                        "export recalculating all of them.",
        "py_save": "Save", "py_revert": "Discard changes",
        "py_results": "Results", "py_variables": "Variables", "py_output": "Output", "py_commands": "Typst commands",
        "py_col_name": "Name", "py_col_value": "Value", "py_col_unit": "Unit", "py_col_label": "Label",
        "py_col_type": "Type", "py_col_repr": "Value",
        "py_no_results": "This script declared no result. Call result(\"name\", value, \"unit\") for every value "
                         "the report is to read.",
        "py_no_variables": "Run the script to see the values its variables took.",
        "py_never_run": "Not run yet.",
        "py_ran": "Ran in {seconds} s: {results} result(s).",
        "py_failed": "The run produced nothing: {reason}",
        "py_none": "No script. «New» makes one.",
        "py_new_name": "The new script's file name (without .py):",
        "py_rename_name": "The new file name (without .py):",
        "py_taken": "There is already a script called {id}.",
        "py_bad_name": "A script's name is letters, digits and _ . + - — {id} is not one.",
        "py_delete_ask": "Delete the script {id}? The report's calls naming it will stop compiling.",
        "py_leave": "The script {id} has unsaved changes. Save them?",
        "py_saved": "Script {id} saved.",
        "py_export_failed": "The script is saved, but the export failed: {error}",
    },
}


def plain_label(text="", wrap=False):
    """A label that never reads its text as HTML -- a script's own words, and a traceback, carry «<» and «&»."""
    label = QLabel()
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setText(text)
    label.setWordWrap(wrap)
    return label


class PythonTab(source_editor.SourceEditorTab, QWidget):
    """Lists the project's scripts, edits one, runs it in a process of its own, and shows what it produced."""
    SYNC_DOMAIN = True   # its sources are domains with a file of their own: every writer is followed by domain_file.sync (tab_guard.py, spec 2026-10-19-base-saine-nettoyage)

    SAVE_ON_FOCUS = False   # a script half typed would run at the next export: saved when the tab or the script is left, not when the window is (autosave.py, review A16)

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.t = app.t
        self.loading = False
        self.dirty = False
        self.current = None      # the id of the script the editor holds
        self.original = ""       # its code as the file has it, what a save compares with
        self.report = None       # the last run's report, for the three panes

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.build_list())
        self.splitter.addWidget(self.build_editor())
        self.splitter.addWidget(self.build_panes())
        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 5)
        self.splitter.setStretchFactor(2, 3)
        layout.addWidget(self.splitter, 1)
        source_editor.save_shortcut(self)   # Ctrl+S
        self.reload_list()
        self.restore(app.views.get("tab_python"))

    # -- building ---------------------------------------------------------------------

    def heading(self, text):
        label = plain_label(text)
        label.setFont(self.app.bold_font)
        return label

    def build_list(self):
        panel = QWidget()
        box = QVBoxLayout(panel)
        box.setContentsMargins(0, 0, 6, 0)
        self.list = grouped_list.GroupedList(STRINGS.get(self.app.lang, STRINGS["fr"]), lang=self.app.lang)
        box.addWidget(grouped_list.title_row(self.heading(self.t("py_list")), self.list))
        self.search = QLineEdit()
        self.search.setPlaceholderText(self.t("py_search"))
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda _text: self.reload_list())
        box.addWidget(self.search)
        # ⚠️ `moved` is deliberately not connected: a script's group is a line of its own code, so a drop would have to
        # rewrite the file. The folders are shown and take no drop, which is what «Moments polaires» did from v0.69 to v0.74.
        self.list.currentIdChanged.connect(self.on_pick)
        self.list.attach_order("tab_python", self.app.list_store, regroup=False)   # the order the engineer gives the list by drag and drop, kept in Woodcore-Datei/lists.json (calc/list_order.py, issue #15) -- the order alone: a script's folder is a line of its code
        self.list.reordered.connect(lambda: self.reload_list())
        box.addWidget(self.list, 1)
        row = QHBoxLayout()
        for key, slot in (("py_new", self.new), ("py_duplicate", self.duplicate),
                          ("py_rename", self.rename), ("py_delete", self.delete)):
            button = QPushButton(self.t(key))
            button.clicked.connect(slot)
            row.addWidget(button)
        row.addStretch(1)
        box.addLayout(row)
        return panel

    def build_editor(self):
        panel = QWidget()
        box = QVBoxLayout(panel)
        box.setContentsMargins(6, 0, 6, 0)
        identity = cards.card(self.t("py_identity"))
        form = cards.form(identity)
        self.identity = {}
        for key in ("name", "label", "group", "id"):
            self.identity[key] = plain_label("", wrap=(key == "label"))
            form.addRow(plain_label(self.t("py_col_name") if key == "name" else
                                    self.t("py_col_label") if key == "label" else
                                    "Groupe" if key == "group" else "ID"), self.identity[key])
        box.addWidget(identity)
        box.addWidget(cards.note(self.t("py_identity_note")))
        box.addWidget(self.heading(self.t("py_code")))
        self.editor = QPlainTextEdit()
        self.editor.setObjectName("code")
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.editor.setTabStopDistance(4 * self.editor.fontMetrics().horizontalAdvance(" "))
        self.highlighter = PythonHighlighter(self.editor.document())
        self.editor.textChanged.connect(self.on_edit)
        box.addWidget(self.editor, 1)
        self.status = plain_label("", wrap=True)
        box.addWidget(self.status)
        row = QHBoxLayout()
        self.run_button = QPushButton(self.t("py_run"))
        self.run_button.setProperty("primary", True)
        self.run_button.setToolTip(self.t("py_run_hint"))
        self.run_button.clicked.connect(self.run)
        row.addWidget(self.run_button)
        row.addStretch(1)
        for key, slot in (("py_revert", self.revert), ("py_save", self.save)):
            button = QPushButton(self.t(key))
            button.clicked.connect(slot)
            row.addWidget(button)
        box.addLayout(row)
        return panel

    def build_panes(self):
        area, box = cards.column(hold=False)
        results = cards.card(self.t("py_results"))
        inner = QVBoxLayout(results)
        self.results = QTreeWidget()
        self.results.setColumnCount(4)
        self.results.setHeaderLabels([self.t(k) for k in ("py_col_name", "py_col_value", "py_col_unit", "py_col_label")])
        self.results.setRootIsDecorated(False)
        self.results.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.results.header().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.results.header().setStretchLastSection(True)
        inner.addWidget(self.results)
        self.results_note = cards.note("")
        inner.addWidget(self.results_note)
        box.addWidget(results)

        variables = cards.card(self.t("py_variables"))
        inner = QVBoxLayout(variables)
        self.variables = QTreeWidget()
        self.variables.setColumnCount(3)
        self.variables.setHeaderLabels([self.t(k) for k in ("py_col_name", "py_col_type", "py_col_repr")])
        self.variables.setRootIsDecorated(False)
        self.variables.header().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.variables.header().setStretchLastSection(True)
        inner.addWidget(self.variables)
        self.variables_note = cards.note(self.t("py_no_variables"))
        inner.addWidget(self.variables_note)
        box.addWidget(variables)

        output = cards.card(self.t("py_output"))
        inner = QVBoxLayout(output)
        self.output = QPlainTextEdit()
        self.output.setObjectName("code")
        self.output.setReadOnly(True)
        inner.addWidget(self.output)
        box.addWidget(output)

        commands = cards.card(self.t("py_commands"))
        self.commands = QVBoxLayout(commands)
        box.addWidget(commands)
        box.addStretch(1)
        return area

    # -- the project's scripts --------------------------------------------------------

    def sources(self):
        """Every script of the project: {id, name, label, group} each, read from the files themselves."""
        out = []
        for path in model.source_paths():
            try:
                out.append(model.read_source(path))
            except OSError:
                continue
        return out

    def reload_list(self, select=None):
        wanted = select or self.current
        needle = self.search.text().strip().lower()
        entries = []
        for source in self.sources():
            if needle and needle not in " ".join(
                    (source["id"], source["name"], source["label"], source["group"])).lower():
                continue
            entries.append({"id": source["id"], "text": source["name"] or source["id"], "group": source["group"]})
        self.list.set_entries(entries, select=wanted)
        if not entries and not needle:
            self.status.setText(self.t("py_none"))

    def path_of(self, script_id):
        return model.sources_dir() / (script_id + model.SUFFIX)

    def taken(self):
        return {source["id"].lower() for source in self.sources()}

    # -- loading and editing ----------------------------------------------------------

    def on_pick(self, script_id):
        if self.loading or not script_id or script_id == self.current:
            return
        if not self.confirm_leave():
            self.loading = True
            self.list.select(self.current)
            self.loading = False
            return
        self.load(script_id)

    def load(self, script_id):
        path = self.path_of(script_id)
        if not path.is_file():
            self.reload_list()
            return
        self.loading = True
        self.current = script_id
        self.original = path.read_text(encoding="utf-8")
        self.editor.setPlainText(self.original)
        self.report = None
        self.loading = False
        self.dirty = False
        self.refresh_identity()
        self.fill_results()
        self.fill_variables()
        self.output.setPlainText("")
        self.status.setText(self.t("py_never_run"))
        self.fill_commands()
        self.update_list_marker()

    def refresh_identity(self):
        found = model.read_source_text(self.editor.toPlainText(), self.current or "")
        self.identity["name"].setText(found["name"] or found["id"])
        self.identity["label"].setText(found["label"])
        self.identity["group"].setText(found["group"])
        self.identity["id"].setText(found["id"])

    def on_edit(self):
        if self.loading:
            return
        self.dirty = self.editor.toPlainText() != self.original
        self.refresh_identity()
        self.update_list_marker()

    def revert(self):
        if self.current is None:
            return
        self.loading = True
        self.editor.setPlainText(self.original)
        self.loading = False
        self.dirty = False
        self.refresh_identity()
        self.update_list_marker()

    # -- the three panes --------------------------------------------------------------

    def fill_results(self):
        self.results.clear()
        rows = (self.report or {}).get("results", [])
        for item in rows:
            value = item["value"]
            QTreeWidgetItem(self.results, [item["name"], f"{value:g}", item.get("unit", ""), item.get("label", "")])
        self.results_note.setText("" if rows else self.t("py_no_results"))
        self.results_note.setVisible(not rows)

    def fill_variables(self):
        self.variables.clear()
        rows = (self.report or {}).get("variables", [])
        for item in rows:
            QTreeWidgetItem(self.variables, [item["name"], item["type"], item["repr"]])
        self.variables_note.setVisible(not rows)

    def fill_commands(self):
        while self.commands.count():
            item = self.commands.takeAt(0)
            if item.widget() is not None:
                # hidden and detached before it is deleted: a widget detached while shown is a top-level window, and Qt shows it as one on that same turn (the white windows of v0.77)
                item.widget().hide()
                item.widget().setParent(None)
                item.widget().deleteLater()
            elif item.layout() is not None:
                while item.layout().count():
                    inner = item.layout().takeAt(0)
                    if inner.widget() is not None:
                        inner.widget().hide()
                        inner.widget().setParent(None)
                        inner.widget().deleteLater()
                item.layout().deleteLater()
        if self.current is None:
            return
        names = [item["name"] for item in (self.report or {}).get("results", [])] or ["x"]
        # its values read by `#var`, and its file written out by the export (spec 2026-10-21-commandes-typst-refonte, REQ-009, REQ-017, UI-002)
        calls = [ref.call_var_domain(model.DOMAIN, self.current, name) for name in names[:6]]
        calls.append(ref.call_include_domain(model.DOMAIN, self.current))
        calls.append(ref.import_line())
        for call in calls:
            row = QHBoxLayout()
            row.addWidget(richtext.CodeField(call, self.app.mono_font), 1)
            row.addWidget(richtext.copy_button(self.app.t("copy"), self.app.t("copied_short"),
                                               lambda text=call: self.app.copy(text)))
            self.commands.addLayout(row)

    # -- running ----------------------------------------------------------------------

    def run(self):
        """Saves, runs in a process of its own, shows what came back, and exports -- so the report reads the results at once."""
        if self.current is None:
            return
        if not self.save(quiet=True):
            return
        self.run_button.setEnabled(False)
        self.status.setText("…")
        QTimer.singleShot(0, self.run_now)

    def run_now(self):
        try:
            self.report = model.run(self.path_of(self.current))
        finally:
            self.run_button.setEnabled(True)
        self.fill_results()
        self.fill_variables()
        self.output.setPlainText(self.report.get("output", ""))
        if self.report.get("ok") and self.report.get("results"):
            self.status.setText(self.t("py_ran", seconds=self.report.get("seconds", 0), results=len(self.report["results"])))
        else:
            reason = self.report.get("reason") or self.t("py_no_results")
            self.status.setText(self.t("py_failed", reason=reason))
        self.fill_commands()
        self.export()

    def export(self):
        """Writes data/scripts.json, so the report sees what the scripts produced without the whole export being run again."""
        try:
            model.export()
        except Exception as exc:                       # broad: an export refused says so; the file is written either way
            self.status.setText(self.t("py_export_failed", error=exc))

    # -- writing ----------------------------------------------------------------------

    def save(self, quiet=False):
        if self.current is None:
            return False
        path = self.path_of(self.current)
        path.parent.mkdir(parents=True, exist_ok=True)
        text = self.editor.toPlainText()
        path.write_text(text, encoding="utf-8", newline="\n")
        self.original = text
        self.dirty = False
        self.refresh_identity()
        self.reload_list(select=self.current)
        self.update_list_marker()
        if not quiet:
            self.app.set_status(self.t("py_saved", id=self.current))
            self.export()
        return True

    def ask_name(self, key, suggested=""):
        name, ok = QInputDialog.getText(self, self.t("tab_python"), self.t(key), text=suggested)
        if not ok:
            return None
        name = name.strip()
        if not name:
            return None
        if not model.ID_PATTERN.match(name):
            notices_ui.tell(self.t("py_bad_name", id=name), notifications.WARNING, key="py_bad_name", args=dict(id=name), title_key="tab_python", source="python_tab")
            return None
        if name.lower() in self.taken():
            notices_ui.tell(self.t("py_taken", id=name), notifications.WARNING, key="py_taken", args=dict(id=name), title_key="tab_python", source="python_tab")
            return None
        return name

    def new(self):
        if not self.confirm_leave():
            return
        name = self.ask_name("py_new_name", "calcul")
        if name is None:
            return
        path = self.path_of(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(TEMPLATE.format(name=name, id=name), encoding="utf-8", newline="\n")
        self.reload_list(select=name)
        self.load(name)

    def duplicate(self):
        if self.current is None or not self.confirm_leave():
            return
        name = self.ask_name("py_new_name", self.current + "-2")
        if name is None:
            return
        self.path_of(name).write_text(self.editor.toPlainText(), encoding="utf-8", newline="\n")
        self.reload_list(select=name)
        self.load(name)

    def rename(self):
        if self.current is None:
            return
        name = self.ask_name("py_rename_name", self.current)
        if name is None:
            return
        if self.dirty:
            self.save(quiet=True)
        self.path_of(self.current).rename(self.path_of(name))
        self.current = name
        self.reload_list(select=name)
        self.load(name)
        self.export()

    def delete(self):
        if self.current is None:
            return
        if QMessageBox.question(self, self.t("tab_python"), self.t("py_delete_ask", id=self.current)) \
                != QMessageBox.StandardButton.Yes:
            return
        self.path_of(self.current).unlink(missing_ok=True)
        self.current, self.original, self.report = None, "", None
        self.loading = True
        self.editor.setPlainText("")
        self.loading = False
        self.dirty = False
        self.refresh_identity()
        self.fill_results()
        self.fill_variables()
        self.reload_list()
        self.app.update_tab_marks()
        self.export()

    # -- the window's contract --------------------------------------------------------

    def update_list_marker(self):
        """A dot at the left of the row being edited while it has unsaved changes, and the tab's own; every row carries a mark, dot or blank, so none moves sideways.

        ⚠️ What makes this owed rather than optional: `tests/test_window.py`'s `_editors` is every tab that has a `dirty`, and it calls this on each -- so in this window `dirty` does not merely hold a flag, it **declares the tab an editor**, and an editor owes the window its row marks. A tab that only browses carries no `dirty` at all (VariablesTab, CommandsTab), which `MainWindow.update_tab_marks` reads with a `getattr` default for exactly that reason.
        """
        for item, script_id in self.list.rows():
            item.setIcon(0, self.app.dirty_mark(script_id == self.current and self.dirty))
        self.app.update_tab_marks()

    def confirm_leave(self):
        """Asked before another script is opened, or the window closes: saved without a question where it can be (v0.117), else save, discard, or stay."""
        if not self.dirty or self.current is None:
            return True
        return autosave.confirm(self.app, self, self.t("tab_python"), self.t("py_leave", id=self.current), save=lambda: self.save(quiet=True))   # saved without a question where it can be, else the one question (autosave.py, v0.117)

    def on_shown(self):
        """The scripts are read again when the tab is brought to the front, as every other editor tab reads its sources."""
        self.reload_list()

    def view_state(self):
        return {"current": self.current, "code": self.editor.toPlainText() if self.dirty else None,
                "sizes": self.splitter.sizes(), "search": self.search.text()}

    def restore(self, state):
        if not state:
            if self.current is None:
                first = self.sources()
                if first:
                    self.load(first[0]["id"])
            return
        if state.get("sizes"):
            self.splitter.setSizes(state["sizes"])
        self.search.setText(state.get("search", ""))
        if state.get("current"):
            self.reload_list(select=state["current"])
            self.load(state["current"])
            if state.get("code") is not None:
                self.loading = True
                self.editor.setPlainText(state["code"])
                self.loading = False
                self.dirty = True
                self.refresh_identity()
                self.app.update_tab_marks()
