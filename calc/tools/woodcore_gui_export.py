"""MainWindow's import and export -- the «Import données» and «Exporter PDF» buttons, the engine's copy checked, the export run, then each document compiled where its Typst changed since its PDF -- a mixin of methods moved verbatim out of calc/tools/woodcore_gui.py (issue #30). MainWindow names it among its bases.
"""

import sys
from pathlib import Path
try:
    from PySide6.QtCore import QByteArray, QLibraryInfo, QLocale, QPoint, QProcess, QProcessEnvironment, QRectF, QRegularExpression, QSize, Qt, QTimer, QTranslator, QUrl, Signal
    from PySide6.QtGui import (
        QActionGroup, QColor, QDesktopServices, QFont, QGuiApplication, QIcon,
        QKeySequence, QPainter, QPixmap, QRegularExpressionValidator, QShortcut,
    )
    from PySide6.QtSvgWidgets import QSvgWidget
    from PySide6.QtWidgets import (
        QAbstractItemView, QApplication, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFileDialog, QFormLayout,
        QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow,
        QMenu, QMessageBox, QPlainTextEdit, QPushButton, QRadioButton, QScrollArea, QSizePolicy, QSpinBox, QSplitter, QTableWidget,
        QTableWidgetItem, QTabWidget, QToolButton, QVBoxLayout, QWidget,
    )
except ImportError as exc:
    if __name__ == "__main__" and sys.platform == "win32":
        # Started from Woodcore.bat there is no console to print this to, so it gets a window of its own -- Windows' own, Qt being what is missing.
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, f"PySide6 est introuvable · PySide6 fehlt · PySide6 is missing\n\n{sys.executable}\n{exc}\n\npython -m pip install PySide6", "Woodcore", 0x10)
    raise
from woodcore_gui_words import STRINGS, _check_strings  # split out of this module (issue #30): every name it had is still importable from it
import project  # noqa: E402  -- where the program is, and where the project it works on is
import proc  # noqa: E402  -- every child process starts through it: no console window flashing open (calc/proc.py)
import documents  # noqa: E402  -- the three documents a project is written as, and the one spelling of a document's compile (30.09.2026)
import stamps  # noqa: E402  -- whether a document's Typst changed since its PDF: an unchanged one is neither compiled nor archived
import busy  # noqa: E402  -- the card shown while the window works, its input held (v0.113)
import archive_export  # every successful compile lands a zip in the project's _Archiv/, called the same way woodcore-cli does (docs/conventions/build-and-release.md §12)
import notifications  # noqa: E402  -- every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # noqa: E402  -- the red octagon and the orange triangle at the top right, and their panel (v0.117)


# An export still running after ten minutes is stopped.
EXPORT_TIMEOUT_MS = 600_000


LANGUAGES = {"fr": "Français", "de": "Deutsch", "en": "English"}


def console_python():
    """The interpreter the export runs under: python.exe beside pythonw.exe when the window was started without a console, so the export's own output can be captured."""
    exe = Path(sys.executable)
    if exe.name.lower() == "pythonw.exe" and exe.with_name("python.exe").exists():
        return str(exe.with_name("python.exe"))
    return str(exe)


def cli_command(args):
    """woodcore-cli with `args`, as a program and its arguments: woodcore-cli.exe beside Woodcore.exe once installed, calc/cli.py under the console interpreter from the sources -- one route from the window to the export, the command line's (v0.83; the window ran export_all.py itself until then)."""
    if getattr(sys, "frozen", False):
        return str(Path(sys.executable).with_name("woodcore-cli.exe")), list(args)
    return console_python(), [str(project.CALC_DIR / "cli.py"), *args]


class WindowExportMixin:
    """Methods of woodcore_gui.MainWindow, moved verbatim (issue #30): the class names this mixin among its bases."""

    def import_button_widget(self):
        """«Import données»: a split button whose own click runs the export, and whose arrow opens a menu holding that same single action, named by what it takes in.

        It was «Import données» until the RFEM import (v0.98, retired in 0.117), and the rename is the engineer's: the one action reads everything entered and drawn in Woodcore -- the load workbooks and `Positionen.xlsx` too until issue #109 and v0.114 --, so a name that says «Excel» says less than the button does. ⚠️ There is still **one** way to import, which is why the menu still holds one entry: a second entry per source would suggest that a source can be imported on its own, and the export is one pass over all of them -- a plan's labels are checked against the positions the same pass read.
        """
        button = QToolButton()
        button.setText(self.t("reexport"))
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        button.clicked.connect(lambda: self.reexport())
        button.setEnabled(self.process is None)
        menu = QMenu(button)
        action = menu.addAction(f'{self.t("reexport")} — {self.t("reexport_what")}')
        action.triggered.connect(lambda: self.reexport())
        button.setMenu(menu)
        return button

    def pdf_button_widget(self):
        """«Exporter PDF»: a split button whose own click compiles the document shown with whatever its menu has checked, and whose arrow opens that menu. The entries are checks and never actions -- choosing one says what the next compilation will carry, and nothing runs until the button itself is clicked -- but one: in a project written as three documents, «Exporter les trois», which compiles the three, each that changed since its PDF (compile_next)."""
        button = QToolButton()
        button.setText(self.t("export_pdf"))
        button.setProperty("primary", True)  # the window's one primary action, in the site's teal (theme.py, v0.90)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        button.clicked.connect(lambda: self.export_pdf())
        button.setEnabled(self.process is None)

        menu = QMenu(button)
        # One exclusive group over all seven, across the two submenus: -Level and -Uniform are mutually exclusive, which woodcore-cli can only say by refusing when it is given both. Here the interface cannot ask for both at all.
        levels = QActionGroup(menu)
        levels.setExclusive(True)
        self.add_pdf_choice(menu, levels, self.t("pdf_as_written"), (None, None), self.pdf_level, self.set_pdf_level)
        base = menu.addMenu(self.t("pdf_base_level"))
        for n in (1, 2, 3):
            self.add_pdf_choice(base, levels, self.t("pdf_level_n", n=n), ("level", n), self.pdf_level, self.set_pdf_level)
        uniform = menu.addMenu(self.t("pdf_uniform_level"))
        for n in (1, 2, 3):
            self.add_pdf_choice(uniform, levels, self.t("pdf_uniform_n", n=n), ("uniform", n), self.pdf_level, self.set_pdf_level)

        menu.addSeparator()
        languages = QActionGroup(menu)
        languages.setExclusive(True)
        self.add_pdf_choice(menu, languages, self.t("pdf_doc_language"), None, self.pdf_lang, self.set_pdf_lang)
        for code, name in LANGUAGES.items():
            self.add_pdf_choice(menu, languages, name, code, self.pdf_lang, self.set_pdf_lang)

        here = project.current()
        if len(here.created_modes) > 1:
            menu.addSeparator()
            every = menu.addAction(self.t("pdf_all"))
            every.triggered.connect(lambda _checked=False: self.export_pdf(modes=project.current().created_modes))

        button.setMenu(menu)
        self.update_pdf_tooltip(button)
        return button

    def add_pdf_choice(self, menu, group, text, value, current, chosen):
        """One checkable entry of the PDF menu. Its value travels on the action itself rather than being read back from its label: the labels are translated and the values are not."""
        action = menu.addAction(text)
        action.setCheckable(True)
        action.setChecked(value == current)
        group.addAction(action)
        action.triggered.connect(lambda _checked=False, value=value: chosen(value))
        return action

    def set_pdf_level(self, value):
        self.pdf_level = value
        self.update_pdf_tooltip()

    def set_pdf_lang(self, value):
        self.pdf_lang = value
        self.update_pdf_tooltip()

    def update_pdf_tooltip(self, button=None):
        """What the next compilation will be of and will carry, on the PDF button's tooltip: the document it exports, and under it a forced level or a forced language -- the two a reader would otherwise have to open the menu to find -- and nothing more while both are the document's own."""
        button = self.pdf_button if button is None else button
        kind, n = self.pdf_level
        detail = []
        if kind == "level":
            detail.append(self.t("pdf_level_n", n=n))
        elif kind == "uniform":
            detail.append(self.t("pdf_uniform_n", n=n))
        if self.pdf_lang:
            detail.append(LANGUAGES[self.pdf_lang])
        lines = [self.t("pdf_document", document=self.document_name())]
        if detail:
            lines.append(self.t("pdf_settings", detail=" · ".join(detail)))
        button.setToolTip("\n".join(lines))
        # and in the top bar, where it is seen without hovering anything (v0.91): «Uniforme 2 · Français»; clicked, it opens the PDF menu
        chip = getattr(self, "pdf_chip", None)
        if chip is not None:
            chip.setText(" · ".join(detail))
            chip.setVisible(bool(detail))

    def pdf_input_args(self):
        """The --input flags the menu asks for, built by calc/cli.py's input_args from the same two choices woodcore-cli takes. None at all where the document's own base level and language govern, which is what makes the report come out «as written» (docs/typst/report-engine.md §4, docs/typst/language.md §4bis)."""
        import cli  # the one spelling of the three flags, the command line's too (calc/cli.py, v0.82)
        kind, n = self.pdf_level
        return cli.input_args(kind, n, self.pdf_lang)

    def export_pdf(self, modes=None):
        """The PDF of the document shown -- of each of `modes` where they are named, which «Exporter les trois» does -- built as woodcore-cli builds it: the export first, then the compilation, and the compilation only if the export exits 0 -- Typst is never compiled against unvalidated data (docs/conventions/build-and-release.md §12). So this starts the export and leaves export_done to carry on; the flags ticked now are what every document is compiled with."""
        if self.process is not None:
            return
        if self.read_only:
            self.refuse_read_only()
            return
        here = project.current()
        self.pdf_modes = [mode for mode in (modes or [self.current_document()]) if mode in here.created_modes]
        self.compile_flags = self.pdf_input_args()
        self.reexport(chain_pdf=True)

    def engine_consent(self, quiet=False):
        """Whether the export may go ahead, and with which extra argument: the project's copy of the engine is replaced without a word when it is this version's, and only on the engineer's say when another version wrote it or it was edited by hand -- the report may print otherwise, or the edit would be lost (calc/project.py engine_state, v0.82). One a newer program wrote is never replaced. Returns None to stop, else the arguments to add."""
        here = project.current()
        state, detail = project.engine_state(here)
        if quiet and (state == "newer" or state in project.ASKED):
            self.set_status(self.t("autosave_engine"))   # a save without a question asks nothing: «Import données» will
            return None
        if state == "newer":
            notices_ui.tell(self.t("engine_newer", version=detail, ours=project.VERSION), notifications.CRITICAL, key="engine_newer", args=dict(version=detail, ours=project.VERSION), title_key="engine_title", source="woodcore_gui")
            return None
        if state not in project.ASKED:
            return []
        return ["--update-engine"] if self.ask_engine(state, detail, opening=False) else None

    def engine_box(self, state, detail, *, opening):
        """The question the project's copy of the engine asks before it is replaced -- one box for the two places it is asked, an export (engine_consent) and the opening of the project (check_engine, v0.87), so the two cannot come to say different things. The sentence says what the copy is -- written by an older Woodcore, by none a VERSION names, or edited by hand -- and which version would replace it; «Voir les différences…» shows the copy against the program's; the other two buttons say what happens next: «Mettre à jour et exporter» (or «Écraser et exporter») and «Annuler» at an export, «Mettre à jour» (or «Écraser») and «Plus tard» at the opening. Returns (the box, the button that replaces the copy, the button that shows the differences)."""
        text = {"older": lambda: self.t("engine_older", version=detail, ours=project.VERSION),
                "unknown": lambda: self.t("engine_unknown", files=detail, ours=project.VERSION),
                "edited": lambda: self.t("engine_edited", files=detail, ours=project.VERSION)}[state]()
        box = QMessageBox(QMessageBox.Icon.Warning, self.t("engine_title"), text, parent=self)  # dialog-ok: the engine replaced or not, a decision that waits for its answer
        if state == "edited":
            key = "engine_overwrite_now" if opening else "engine_overwrite"
        else:
            key = "engine_update_now" if opening else "engine_update"
        go = box.addButton(self.t(key), QMessageBox.ButtonRole.AcceptRole)
        diff = box.addButton(self.t("engine_diff"), QMessageBox.ButtonRole.ActionRole)
        if opening:
            later = box.addButton(self.t("engine_later"), QMessageBox.ButtonRole.RejectRole)
        else:
            later = box.addButton(QMessageBox.StandardButton.Cancel)
        box.setDefaultButton(go)
        box.setEscapeButton(later)
        return box, go, diff

    def ask_engine(self, state, detail, *, opening):
        """Whether the engineer agrees to replace the project's copy of the engine (engine_box). «Voir les différences…» shows them and asks the same question again, so looking at the differences answers nothing; closing the box is «Annuler» or «Plus tard»."""
        box, go, diff = self.engine_box(state, detail, opening=opening)
        while True:
            box.exec()
            if box.clickedButton() is not diff:
                return box.clickedButton() is go
            self.show_engine_diff()

    def show_engine_diff(self):
        """«Voir les différences…»: the project's copy of the engine against the program's, as a unified diff in the fixed font (project.engine_diff), in a window of its own the question waits behind. Until v0.87 the diff was the message box's own «Afficher les détails», for an edited copy alone; an older copy shows what the update will change as well."""
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            text = project.engine_diff(project.current())
        finally:
            QApplication.restoreOverrideCursor()
        dialog = QDialog(self)
        dialog.setWindowTitle(self.t("engine_diff_title", ours=project.VERSION))
        layout = QVBoxLayout(dialog)
        view = QPlainTextEdit(text or self.t("engine_diff_none"))
        view.setReadOnly(True)
        view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        view.setFont(self.mono_font)
        layout.addWidget(view)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.resize(1000, 650)
        dialog.exec()

    def check_engine(self):
        """Run once, just after the window is up (v0.87), queued by open_project beside check_dependencies: the project's copy of the engine against this program's, the comparison an export makes (engine_consent) made as the project opens -- the engineer: «lors de l'ouverture d'un projet qui tourne sur un ancien moteur, un message demande si le user veut uploader le moteur à la dernière version». By engine_state: the program's own or current, nothing; absent, or another build of this same version (stale -- the sources edited since), copied without a word as an export would, and said in the status bar; written by an older version, by none a VERSION names (unknown) or edited by hand, asked (engine_box) -- «Plus tard» writes nothing, and the question comes back at the next opening; written by a newer Woodcore, said, this window then refusing to export into it (engine_consent) -- a case open_project no longer lets reach here, opening such a project read-only (v0.87). A project opened read-only, which another window holds or a newer Woodcore wrote, is asked nothing and written nothing."""
        if self.read_only:
            return
        here = project.current()
        state, detail = project.engine_state(here)
        if state in ("own", "current"):
            return
        if state == "newer":
            notices_ui.tell(self.t("engine_newer_open", version=detail, ours=project.VERSION), notifications.INFO, key="engine_newer_open", args=dict(version=detail, ours=project.VERSION), title_key="engine_title", source="woodcore_gui")
            return
        asked = state in project.ASKED
        if asked and not self.ask_engine(state, detail, opening=True):
            return
        self.sync_engine_copy(here, update=asked)

    def sync_engine_copy(self, here, update):
        """The program's engine copied into project `here` (project.sync_engine), and the status bar saying so; a copy that cannot be written -- a file held open, a folder not synced yet -- is said in a box rather than lost. `update` is the engineer's yes to replacing another version's copy or an edited one. Returns whether it was written."""
        try:
            project.sync_engine(here, update=update)
        except (OSError, project.ProjectError) as exc:
            notices_ui.tell(self.t("engine_sync_failed", error=exc), notifications.CRITICAL, exc=exc, key="engine_sync_failed", args=dict(error=exc), title_key="engine_title", source="woodcore_gui")
            return False
        self.set_status(self.t("engine_synced", ours=project.VERSION))
        return True

    def reexport(self, *, chain_pdf=False, light=False):
        """Runs calc/export_all.py exactly as woodcore-cli does, in its own process: its exit code decides, and a failed export leaves data/ as it was (export_all never writes half an export). Qt starts it without a console window when this one has none, as when it is opened from the .bat. With chain_pdf the PDF is compiled after it, which is the export button's own doing; the keyword is keyword-only so that a `clicked` signal's own argument can never become one."""
        quiet = self.saving_quietly   # started by a save without a question (a position saved imports): nothing asked, its warnings in the status line
        if not quiet and self.process is None and not self.read_only:
            # what the tabs hold unsaved is saved first, so the export reads it (review A05); a position saved imports by itself, and the PDF then follows that import
            self.autosave_all("export")
            if self.process is not None:
                self.pending_pdf = self.pending_pdf or chain_pdf
                return
        if self.process is not None:
            return
        if self.read_only:
            self.refuse_read_only()
            return
        # one writer of data/ at a time (ARCH-003, v0.117): the export of a layer switched, which a plan tab runs in a thread of its own, finished before the export is started -- never the two writing the plans' files at once
        for tab in self.tabs:
            finish = getattr(tab, "finish_layer_export", None)
            if finish is not None:
                finish()
        extra = self.engine_consent(quiet=quiet)
        if extra is None:
            return
        self.quiet_export = quiet
        self.light_export = bool(light) and not chain_pdf   # a PDF asked for is compiled after a full rebuild, as before
        self.pending_pdf = chain_pdf
        self.export_button.setEnabled(False)
        self.pdf_button.setEnabled(False)
        self.set_status(self.t("exporting"))
        # Held for as long as it runs, the card saying what is done (the engineer's choice of 03.10.2026: the window held with the card rather than left free while an export or a compilation runs)
        busy.start(self, self.t("exporting"))
        process = self.process = proc.qprocess(self)
        environment = QProcessEnvironment.systemEnvironment()
        environment.insert("PYTHONUTF8", "1")
        environment.insert("PYTHONIOENCODING", "utf-8")
        environment.insert(notifications.STRUCTURED_ENV, "1")   # its warnings as structured lines, each a notice in the window's words (notifications.read_output, v0.117)
        process.setProcessEnvironment(environment)
        process.setWorkingDirectory(str(project.APP_ROOT))
        process.finished.connect(self.export_finished)
        process.errorOccurred.connect(self.export_error)
        timeout = QTimer(process)  # dies with the process, so it can never stop a later export
        timeout.setSingleShot(True)
        timeout.timeout.connect(process.kill)
        timeout.start(EXPORT_TIMEOUT_MS)
        program, arguments = cli_command(["export", "--data-only", "--project", str(project.current().file), *extra])
        process.start(program, arguments)

    def export_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:  # the one error no `finished` follows
            self.export_done(-1, "", self.process.errorString())

    def export_finished(self, code, status):
        process = self.process
        stdout = bytes(process.readAllStandardOutput()).decode("utf-8", "replace")
        stderr = bytes(process.readAllStandardError()).decode("utf-8", "replace")
        if status != QProcess.ExitStatus.NormalExit:  # stopped at the timeout, or crashed
            code, stderr = -1, f"{stderr}\n{process.errorString()}".strip()
        self.export_done(code, stdout, stderr)

    def export_done(self, code, stdout, stderr):
        self.process.deleteLater()
        self.process = None
        compile_next, self.pending_pdf = self.pending_pdf, False  # consumed here however it ends, so a failed export can never compile
        quiet, self.quiet_export = self.quiet_export, False
        light, self.light_export = self.light_export, False
        QTimer.singleShot(0, self.flush_autosave)   # a save put off while it ran (autosave.py)
        if code != 0:
            busy.stop(self)
            self.export_button.setEnabled(True)
            self.pdf_button.setEnabled(True)
            output = "\n".join((stderr or stdout).strip().splitlines()[-30:])
            self.set_status(self.t("export_failed_title"))
            # what it warned of before it stopped, each a notice; then the failure itself, critical, its whole output the technical text
            notifications.read_output("\n".join(line for line in stderr.splitlines() if line.startswith(notifications.STRUCTURED_PREFIX)), source="export")
            notifications.report("export_failed", self.t("export_failed", code=code, output=output), notifications.CRITICAL, key="export_failed", args=dict(code=code, output=output),
                           title_key="export_failed_title", technical=(stderr or stdout).strip(), source="export")
        elif not self.close_requested:
            if light and not compile_next:
                try:
                    self.refresh_lightly()   # a position saved: the tab in front is built again, the others when they are shown
                except Exception:   # broad: whatever goes wrong here, a full rebuild is what it was before and is never wrong
                    self.reload()
            else:
                self.reload()   # still held: the card says «Chargement…» while the modules are built again
            busy.stop(self)
            self.set_status(self.t("export_ok"))
            if stderr.strip():
                # its warnings, each a notice of its own in the window's words (ARCH-008); an export run without a question says the first in the status line as well
                found = notifications.read_output(stderr, source="export")
                if quiet and not compile_next and found:
                    self.set_status(self.t("autosave_warnings", first=notifications.message(found[0], self.lang)))
            if compile_next:
                self.start_compiles()
        if self.close_requested:
            busy.stop(self)
            self.close()

    def start_compiles(self):
        """The documents the PDF button asked for, compiled one after the other (compile_next). Reached only through export_done, so data/ has just been written and validated."""
        here = project.current()
        self.compile_queue = [mode for mode in (self.pdf_modes or [self.current_document()]) if mode in here.created_modes]
        self.compile_single = len(self.compile_queue) == 1
        self.compile_messages = []
        self.last_pdf = None
        self.pdf_modes = None
        self.export_button.setEnabled(False)  # the reload that precedes this built both buttons anew, and enabled
        self.pdf_button.setEnabled(False)
        self.compile_next()

    def compile_command(self, here, mode, flags):
        """(program, arguments, deps file) of document `mode`'s compile -- documents.compile_args, the one spelling of a document's command line, which states the Typst root and asks Typst what it read (`--deps`, stamps.deps_file) -- and `typst` found as woodcore-cli finds it (project.typst_executable)."""
        deps = stamps.deps_file(here, mode)
        return project.typst_executable(), documents.compile_args(here, mode, flags, deps=deps), deps

    def compile_next(self):
        """The next document of the queue: passed over where its Typst did not change since its PDF (stamps.changed) -- said in the status line, neither compiled nor archived, the engineer's rule -- else compiled. When the queue is empty, what became of each is said, and the PDF of a single document opened."""
        here = project.current()
        while self.compile_queue:
            mode = self.compile_queue.pop(0)
            try:
                changed, why = stamps.changed(here, mode, self.compile_flags)
            except (OSError, project.ProjectError):
                changed, why = True, None   # a stamp that cannot be read is a document compiled: slow, never wrong
            if not changed:
                self.compile_messages.append(self.stamp_text(why, mode))
                self.last_pdf = here.document_pdf(mode)
                continue
            self.compile_document(here, mode)
            return
        self.compiles_finished()

    def stamp_text(self, note, mode):
        """What a stamp said of document `mode`, in the window's language by the code its engine.Note carries (`doc_<code>`), the document named as the window names it; the English sentence where the window has none for that code."""
        key = "doc_" + getattr(note, "code", "")
        if key in STRINGS[self.lang]:
            return self.t(key, document=self.document_name(mode))
        return f"{self.document_name(mode)}: {note}"

    def compile_document(self, here, mode):
        """Compiles document `mode`: the same input and the same output as woodcore-cli -- every build route names each document's one deliverable (docs/conventions/build-and-release.md §12). A compilation that fails leaves the PDF that was there where it was."""
        self.compiling = True
        self.compile_mode = mode
        self.set_status(self.t("compiling", document=self.document_name(mode)))
        busy.start(self, self.t("compiling", document=self.document_name(mode)))   # held until the last document is done (compiles_finished)
        program, arguments, self.compile_deps = self.compile_command(here, mode, self.compile_flags)
        process = self.process = proc.qprocess(self)
        process.setWorkingDirectory(str(here.typst_root))
        process.finished.connect(self.compile_finished)
        process.errorOccurred.connect(self.compile_error)
        timeout = QTimer(process)  # dies with the process, so it can never stop a later compilation
        timeout.setSingleShot(True)
        timeout.timeout.connect(process.kill)
        timeout.start(EXPORT_TIMEOUT_MS)
        process.start(program, arguments)

    def compile_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:  # the one error no `finished` follows -- a typst that is not on PATH arrives here, and Qt's message names it
            self.compile_done(-1, "", self.process.errorString())

    def compile_finished(self, code, status):
        process = self.process
        stdout = bytes(process.readAllStandardOutput()).decode("utf-8", "replace")
        stderr = bytes(process.readAllStandardError()).decode("utf-8", "replace")
        if status != QProcess.ExitStatus.NormalExit:  # stopped at the timeout, or crashed
            code, stderr = -1, f"{stderr}\n{process.errorString()}".strip()
        self.compile_done(code, stdout, stderr)

    def compile_done(self, code, stdout, stderr):
        """One document compiled, or not. A failure stops the queue and says so with Typst's own message; a success is stamped (stamps.record -- so the next export passes it over while nothing it read changes) and archived (archive_export, the document's own zip), and the next document follows."""
        if self.process is not None:
            self.process.deleteLater()
        self.process = None
        self.compiling = False
        QTimer.singleShot(0, self.flush_autosave)   # a save put off while it ran (autosave.py)
        mode, here = self.compile_mode, project.current()
        if code != 0:
            busy.stop(self)
            self.compile_queue = []
            self.export_button.setEnabled(True)
            self.pdf_button.setEnabled(True)
            output = "\n".join((stderr or stdout).strip().splitlines()[-30:])
            self.set_status(self.t("compile_failed_title"))
            # Typst's diagnostics, each a notice at its file, line and column, to be opened there; output with none -- a crash, a timeout -- one notice with the whole of it
            notifications.report_typst(stderr or stdout, source=f"compile {self.document_name(mode)}", root=here.typst_root)
            if self.close_requested:
                self.close()
            return
        pdf = here.document_pdf(mode)
        try:
            stamps.record(here, mode, self.compile_flags, self.compile_deps, pdf)
        except OSError:
            pass   # a document not stamped is one compiled again next time: slow, never wrong
        self.last_pdf = pdf
        self.compile_messages.append(self.t("pdf_ready", document=self.document_name(mode), name=pdf.name))
        try:
            archive_export.run("gui", " ".join(self.compile_flags), mode=mode)
        except Exception as exc:  # broad: a convenience, never worth a modal: the PDF is written regardless, the reason said
            self.compile_messages.append(self.t("archive_failed", reason=str(exc)))
        if self.close_requested:
            self.compile_queue = []
            busy.stop(self)
            self.close()
            return
        self.compile_next()

    def compiles_finished(self):
        """The queue done: the window let go, the buttons back, what became of each document in the status line, and -- for one document asked for, and only then -- its PDF opened, compiled now or unchanged since it was."""
        busy.stop(self)
        self.export_button.setEnabled(True)
        self.pdf_button.setEnabled(True)
        self.set_status(" · ".join(self.compile_messages))
        if self.compile_single and self.last_pdf is not None and Path(self.last_pdf).is_file() and not self.close_requested:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_pdf)))
        if self.close_requested:
            self.close()
