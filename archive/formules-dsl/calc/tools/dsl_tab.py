"""Woodcore's «Formules» tab (docs/domain/member-checks.md §3.3septdecies, docs/ui/window.md §10quater, v0.100): the engineer writes a member's checks in keyword lines, reads the Typst they come to, sees the page it compiles to, and puts it into a section of his report.

The engineer: «est-il possible d'avoir un onglet où le user peut écrire des formules de manières simples, non formatées en typst». He was offered an AI for it and refused (`n'implémente pas l'IA`), and agreed a **deterministic parser** suffices — so what stands behind this tab is `calc/dsl.py`, a grammar of a dozen words: the same lines always give the same Typst, and a line outside the grammar is refused **naming the line** and listing what is understood.

**Three panes, left to right**: what he writes, the Typst it becomes, and the page that Typst compiles to. The third is his own requirement — «il doit être possible de voir la compilation typst et pas uniquement le code typst» — so nothing reaches a section of the report before he has seen what it prints.

**Nothing is written into the report until he asks**, and then he sees the diff first (his answer E14): *Insérer dans une section…* names the section, shows what will be added, and appends only on a yes.

⚠️ The page is compiled from **standard input against the project's own report folder** as the Typst root, so `#member("T001")` reads the project's real positions and nothing is written into the project to render it — the arrangement the commands tab has used since v0.81.
"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QMessageBox, QPlainTextEdit,
    QPushButton, QScrollArea, QSplitter, QVBoxLayout, QWidget,
)

import cards
import command_preview
import dsl
import proc
import project
import richtext
import notifications  # every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # what was a message box is a notice since v0.117 (notices_ui.tell)

LEVELS = (1, 2, 3)
DEFAULT_LEVEL = 2
# What a new tab starts from: the engineer's own example, in his own words, so the grammar is read by being read.
SAMPLE = """# Une ligne «mot-clé: valeur». Un «#» est un commentaire.
position: T001
M_y: 26.9 kNm
a: 6000 mm
vérifier: flexion
V: 24 kN
vérifier: cisaillement
"""

STRINGS = {
    "fr": {
        "tab_dsl": "Formules",
        "dsl_written": "Ce que vous écrivez",
        "dsl_typst": "Le Typst obtenu",
        "dsl_page": "La page compilée",
        "dsl_translate": "Traduire et compiler",
        "dsl_copy": "Copier le Typst",
        "dsl_insert": "Insérer dans une section…",
        "dsl_level": "Niveau",
        "dsl_problems": "Lignes non comprises",
        "dsl_ok": "{blocks} élément(s), {checks} vérification(s).",
        "dsl_nothing": "Rien à traduire : commencez par une ligne «position: T001».",
        "dsl_no_typst": "Typst n’est pas installé, donc la page ne peut pas être compilée. Le Typst obtenu reste juste.",
        "dsl_failed": "La compilation a échoué : {error}",
        "dsl_grammar": "Mots-clés : {keywords}.\nVérifications : {checks}.",
        "dsl_insert_title": "Insérer dans une section",
        "dsl_insert_which": "Section",
        "dsl_insert_preview": "Ce qui sera ajouté à la fin de la section :",
        "dsl_inserted": "Ajouté à {section}.",
        "dsl_no_sections": "Ce projet n’a pas de dossier Sections.",
    },
    "de": {
        "tab_dsl": "Formeln",
        "dsl_written": "Was Sie schreiben",
        "dsl_typst": "Das erzeugte Typst",
        "dsl_page": "Die kompilierte Seite",
        "dsl_translate": "Übersetzen und kompilieren",
        "dsl_copy": "Typst kopieren",
        "dsl_insert": "In einen Abschnitt einfügen…",
        "dsl_level": "Stufe",
        "dsl_problems": "Nicht verstandene Zeilen",
        "dsl_ok": "{blocks} Bauteil(e), {checks} Nachweis(e).",
        "dsl_nothing": "Nichts zu übersetzen: beginnen Sie mit einer Zeile «position: T001».",
        "dsl_no_typst": "Typst ist nicht installiert, die Seite kann daher nicht kompiliert werden. Das erzeugte Typst bleibt richtig.",
        "dsl_failed": "Die Kompilierung ist gescheitert: {error}",
        "dsl_grammar": "Schlüsselwörter: {keywords}.\nNachweise: {checks}.",
        "dsl_insert_title": "In einen Abschnitt einfügen",
        "dsl_insert_which": "Abschnitt",
        "dsl_insert_preview": "Was am Ende des Abschnitts angefügt wird:",
        "dsl_inserted": "An {section} angefügt.",
        "dsl_no_sections": "Dieses Projekt hat keinen Sections-Ordner.",
    },
    "en": {
        "tab_dsl": "Formulas",
        "dsl_written": "What you write",
        "dsl_typst": "The Typst it comes to",
        "dsl_page": "The compiled page",
        "dsl_translate": "Translate and compile",
        "dsl_copy": "Copy the Typst",
        "dsl_insert": "Insert into a section…",
        "dsl_level": "Level",
        "dsl_problems": "Lines not understood",
        "dsl_ok": "{blocks} member(s), {checks} check(s).",
        "dsl_nothing": "Nothing to translate: start with a «position: T001» line.",
        "dsl_no_typst": "Typst is not installed, so the page cannot be compiled. The Typst it comes to is still right.",
        "dsl_failed": "The compilation failed: {error}",
        "dsl_grammar": "Keywords: {keywords}.\nChecks: {checks}.",
        "dsl_insert_title": "Insert into a section",
        "dsl_insert_which": "Section",
        "dsl_insert_preview": "What will be added at the end of the section:",
        "dsl_inserted": "Added to {section}.",
        "dsl_no_sections": "This project has no Sections folder.",
    },
}


def plain_label(text="", wrap=False):
    label = QLabel()
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setText(text)
    label.setWordWrap(wrap)
    return label


def render(code, level, lang, root):
    """The page `code` compiles to, against the project's own report folder as the Typst root: `(png, error)`.

    On standard input, so nothing is written into the engineer's project to render a preview -- the commands tab's own arrangement since v0.81. The preamble is `command_preview`'s, so a page here and a page there are set on the same measure and with the same digits.
    """
    if not command_preview.have_typst():
        return None, "no-typst"
    png = command_preview.CACHE_DIR / f"dsl-{abs(hash((code, level, lang, str(root))))}.png"
    png.parent.mkdir(parents=True, exist_ok=True)
    document = command_preview.document(code, level, lang)
    done = proc.run(
        [str(project.typst_executable()), "compile", "--root", str(root), "--format", "png",
         "--ppi", str(command_preview.PPI), "-", str(png)],
        input=document, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if done.returncode != 0:
        return None, (done.stderr or done.stdout).strip()
    return png, None


class InsertDialog(QDialog):
    """Which section the Typst goes into, and what will be added -- shown before anything is written (the engineer's answer E14)."""

    def __init__(self, parent, t, sections, code):
        super().__init__(parent)
        self.t = t
        self.setWindowTitle(t("dsl_insert_title"))
        self.setMinimumWidth(620)
        box = QVBoxLayout(self)
        self.section = QComboBox()
        for path in sections:
            self.section.addItem(path.name, str(path))
        row = QHBoxLayout()
        row.addWidget(plain_label(t("dsl_insert_which")))
        row.addWidget(self.section, 1)
        box.addLayout(row)
        box.addWidget(plain_label(t("dsl_insert_preview"), wrap=True))
        shown = QPlainTextEdit(code)
        shown.setObjectName("code")
        shown.setReadOnly(True)
        richtext.TypstHighlighter(shown.document())
        box.addWidget(shown, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        box.addWidget(buttons)

    def chosen(self):
        return Path(self.section.currentData())


class DslTab(QWidget):
    """Keyword lines in, Typst and its compiled page out, and into a section of the report on a yes."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.t = app.t
        self.code = ""
        # ⚠️ No `dirty`, deliberately: in this window a `dirty` **declares a tab an editor** (tests/test_window.py's
        # `_editors`), and an editor owes a list of saved sources each of which can carry a dot. This tab saves nothing
        # of its own -- its keyword lines are carried through a rebuild by `view_state` and belong to no file -- so a dot
        # would come on at the first keystroke and never clear. It browses and translates; what it writes, it writes
        # into a section on a yes, and that is the engineer's own act.

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.build_written())
        self.splitter.addWidget(self.build_typst())
        self.splitter.addWidget(self.build_page())
        for index, weight in enumerate((3, 3, 4)):
            self.splitter.setStretchFactor(index, weight)
        layout.addWidget(self.splitter, 1)
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.activated.connect(self.translate)
        self.restore(app.views.get("tab_dsl"))

    def heading(self, text):
        label = plain_label(text)
        label.setFont(self.app.bold_font)
        return label

    def build_written(self):
        panel = QWidget()
        box = QVBoxLayout(panel)
        box.setContentsMargins(0, 0, 6, 0)
        box.addWidget(self.heading(self.t("dsl_written")))
        self.written = QPlainTextEdit(SAMPLE)
        self.written.setObjectName("code")
        box.addWidget(self.written, 1)
        box.addWidget(cards.note(self.t("dsl_grammar", keywords=", ".join(sorted(dsl.KEYWORDS)),
                                        checks=", ".join(sorted(dsl.CHECK_WORDS)))))
        row = QHBoxLayout()
        self.level = QComboBox()
        for level in LEVELS:
            self.level.addItem(str(level), level)
        self.level.setCurrentIndex(LEVELS.index(DEFAULT_LEVEL))
        self.level.currentIndexChanged.connect(lambda _index: self.translate())
        row.addWidget(plain_label(self.t("dsl_level")))
        row.addWidget(self.level)
        translate = QPushButton(self.t("dsl_translate"))
        translate.setProperty("primary", True)
        translate.clicked.connect(self.translate)
        row.addWidget(translate, 1)
        box.addLayout(row)
        return panel

    def build_typst(self):
        panel = QWidget()
        box = QVBoxLayout(panel)
        box.setContentsMargins(6, 0, 6, 0)
        box.addWidget(self.heading(self.t("dsl_typst")))
        self.typst = QPlainTextEdit()
        self.typst.setObjectName("code")
        self.typst.setReadOnly(True)
        richtext.TypstHighlighter(self.typst.document())
        box.addWidget(self.typst, 3)
        self.status = plain_label("", wrap=True)
        box.addWidget(self.status)
        box.addWidget(self.heading(self.t("dsl_problems")))
        self.problems = QPlainTextEdit()
        self.problems.setReadOnly(True)
        box.addWidget(self.problems, 2)
        row = QHBoxLayout()
        copy = QPushButton(self.t("dsl_copy"))
        copy.clicked.connect(lambda: self.app.copy(self.code))
        row.addWidget(copy)
        insert = QPushButton(self.t("dsl_insert"))
        insert.clicked.connect(self.insert)
        row.addWidget(insert)
        row.addStretch(1)
        box.addLayout(row)
        return panel

    def build_page(self):
        panel = QWidget()
        box = QVBoxLayout(panel)
        box.setContentsMargins(6, 0, 0, 0)
        box.addWidget(self.heading(self.t("dsl_page")))
        self.page = QLabel()
        self.page.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setWidget(self.page)
        box.addWidget(area, 1)
        return panel

    # -- what it does -----------------------------------------------------------------

    def translate(self):
        """Reads the lines, writes the Typst, and compiles the page it prints."""
        blocks, problems = dsl.parse(self.written.toPlainText())
        level = self.level.currentData()
        self.code = dsl.to_typst(blocks, level=level)
        self.typst.setPlainText(self.code)
        lines = [str(problem) for problem in problems] + dsl.missing(blocks)
        self.problems.setPlainText("\n".join(lines))
        if not blocks:
            self.status.setText(self.t("dsl_nothing"))
            self.page.setPixmap(QPixmap())
            return
        self.status.setText(self.t("dsl_ok", blocks=len(blocks), checks=sum(len(b.checks) for b in blocks)))
        png, error = render(self.code, level, self.app.lang, project.current().typst_root)
        if error == "no-typst":
            self.status.setText(self.t("dsl_no_typst"))
            self.page.setPixmap(QPixmap())
        elif error:
            self.status.setText(self.t("dsl_failed", error=error.splitlines()[0] if error else ""))
            self.problems.setPlainText("\n".join(lines + ["", error]))
            self.page.setPixmap(QPixmap())
        else:
            self.page.setPixmap(QPixmap(str(png)))

    def sections(self):
        """The sections of the document the window shows, in their order: the report's numbered ones in a project laid out as one report, and in three documents those of the document's own folder (`Project.document_dir`) -- the Typst root being the whole project there, its `Sections/` is no document's."""
        here = project.current()
        current = getattr(self.app, "current_document", None)
        mode = current() if callable(current) else "rs"
        folder = here.document_dir(mode if mode in here.modes else "rs") / "Sections"
        return sorted(folder.glob("*.typ")) if folder.is_dir() else []

    def insert(self):
        """Appends the Typst to a section of the report -- after the engineer has seen which section and what will be added (his answer E14)."""
        if not self.code.strip():
            self.translate()
        if not self.code.strip():
            return
        sections = self.sections()
        if not sections:
            notices_ui.tell(self.t("dsl_no_sections"), notifications.WARNING, key="dsl_no_sections", title_key="tab_dsl", source="dsl_tab")
            return
        dialog = InsertDialog(self, self.t, sections, self.code)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        path = dialog.chosen()
        text = path.read_text(encoding="utf-8")
        if not text.endswith("\n"):
            text += "\n"
        path.write_text(text + "\n" + self.code, encoding="utf-8")
        self.app.set_status(self.t("dsl_inserted", section=path.name))

    # -- the window's contract --------------------------------------------------------

    def on_shown(self):
        pass

    def view_state(self):
        return {"written": self.written.toPlainText(), "level": self.level.currentData(),
                "sizes": self.splitter.sizes()}

    def restore(self, state):
        if not state:
            return
        if state.get("sizes"):
            self.splitter.setSizes(state["sizes"])
        if state.get("written"):
            self.written.setPlainText(state["written"])
        if state.get("level") in LEVELS:
            self.level.setCurrentIndex(LEVELS.index(state["level"]))
