"""MainWindow's packages and settings -- the three packages outside the standard library checked and updated, the colours and the language taken, the folders' settings, the title and the marks -- and its File menu: a mixin of methods moved verbatim out of calc/tools/woodcore_gui.py (issue #30). MainWindow names it among its bases.
"""

import functools
import os
import shutil
import sys
import threading
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
import project  # noqa: E402  -- where the program is, and where the project it works on is
import proc  # noqa: E402  -- every child process starts through it: no console window flashing open (calc/proc.py)
import usersettings  # noqa: E402  -- Woodcore's own preferences, %APPDATA%\Woodcore (v0.83)
import busy  # noqa: E402  -- the card shown while the window works, its input held (v0.113)
import home_page  # noqa: E402  -- the start page, the project dialog, the File menu's words (v0.83)
import settings_dialog  # noqa: E402  -- *Fichier → Paramètres…*: the settings and the project templates (v0.94)
import dependencies
import notifications  # noqa: E402  -- every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # noqa: E402  -- the red octagon and the orange triangle at the top right, and their panel (v0.117)
import list_order  # noqa: E402  -- the order of the window's lists and the «Formules» tab's folders, Woodcore-Datei/lists.json (issue #15)
import variable_sources  # every variable of a project and where it comes from; instance_workbook (calc/variable_sources.py, v0.117)
import chrome  # noqa: E402  -- the zoom's three actions, the same in the menu and on the start page (issue #85)
import theme  # the website's look: one palette, one style sheet, light or dark (theme.py, v0.90)
import legal  # *Fichier → À propos de Woodcore…*: the copyright, the licence and the third-party notices


def data_file():
    """The current project's data/calculations.json, the validated export this window lists."""
    return project.current().data_dir / "calculations.json"


def stale_workbooks(data, data_file=None):
    """The workbooks the data was read from that were saved after it was exported -- their values may no longer be what the window shows."""
    here = project.current()
    data_file = data_file or here.data_dir / "calculations.json"
    exported = data_file.stat().st_mtime
    names = {
        variable_sources.instance_workbook(domain, instance)
        for domain in data["domains"].values()
        for instance in domain["instances"].values()
    }
    stale = []
    for name in sorted(n for n in names if n):
        path = here.root / name
        if path.exists() and path.stat().st_mtime > exported:
            stale.append(name)
    return stale


def one_line(text):
    return " ".join(part.strip() for part in text.splitlines())


def read_settings():
    return usersettings.read()


def write_settings(settings):
    usersettings.write(settings)  # a preference that cannot be saved is not worth interrupting anyone for


# The mark of unsaved changes: a dot at the left of a tab's title and of the row being edited (docs/ui/window.md §10quater).
MARK_PX = 10


def mark_icon(colour):
    """A filled dot in `colour`, or the empty square of the same size when `colour` is None.

    The mark is an icon rather than a character in the text because an icon takes the same room whether anything is drawn in it or not, and every tab and every row carries one: a tab bar that widened as an editor is touched would move every tab after it, and a row whose text slid sideways as it is typed into would be as hard to follow.
    """
    screen = QGuiApplication.primaryScreen()
    ratio = screen.devicePixelRatio() if screen is not None else 1.0
    pixmap = QPixmap(round(MARK_PX * ratio), round(MARK_PX * ratio))
    pixmap.setDevicePixelRatio(ratio)  # the painter then works in the window's own logical pixels, and the dot is drawn at the screen's resolution
    pixmap.fill(Qt.GlobalColor.transparent)
    if colour is not None:
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(colour)
        painter.drawEllipse(QRectF(MARK_PX * 0.25, MARK_PX * 0.25, MARK_PX * 0.5, MARK_PX * 0.5))
        painter.end()
    return QIcon(pixmap)


def config_stamp(here):
    """What says the project's config.typ -- the file its three documents are styled by -- was replaced: its size and the time it was written, or None where it is not there."""
    try:
        found = Path(here.config_typ).stat()
    except OSError:
        return None
    return (found.st_size, found.st_mtime_ns)


_QT_TRANSLATOR = None


def install_qt_translation(lang):
    """Qt's own words -- Save, Discard, Cancel, Yes, No, the context menu of a field -- in the window's language. PySide6 ships `qtbase_<lang>.qm`; without it every «unsaved changes» question read Save / Discard / Cancel in a French or German window (periodic audit 260916, AUD-4-2). Where the file cannot be loaded, Qt keeps its English and nothing else changes."""
    global _QT_TRANSLATOR
    app = QApplication.instance()
    if app is None:
        return
    if _QT_TRANSLATOR is not None:
        app.removeTranslator(_QT_TRANSLATOR)
    _QT_TRANSLATOR = QTranslator(app)
    if _QT_TRANSLATOR.load(QLocale(lang), "qtbase", "_", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
        app.installTranslator(_QT_TRANSLATOR)


def vscode_executable():
    """VS Code's own Code.exe -- `code` on the PATH is a .cmd, which a process cannot be started on without a console window -- or None."""
    found = shutil.which("code")
    candidates = []
    if found:
        path = Path(found)
        candidates.append(path.parent.parent / "Code.exe" if path.suffix.lower() in (".cmd", ".bat") else path)
    for base in (os.environ.get("LOCALAPPDATA"), os.environ.get("ProgramFiles")):
        if base:
            candidates.append(Path(base) / ("Programs" if base == os.environ.get("LOCALAPPDATA") else "") / "Microsoft VS Code" / "Code.exe")
    return next((str(c) for c in candidates if c.is_file()), None)


class WindowMenusMixin:
    """Methods of woodcore_gui.MainWindow, moved verbatim (issue #30): the class names this mixin among its bases."""

    def check_dependencies(self):
        """Run once, just after the window is up.

        Two questions, and only the first can stop anything. *Is what the project asks for installed?* is read out of this interpreter -- instant, offline, and a mismatch is worth a modal, because a workbook read by another openpyxl is not the workbook this version was verified against. *Is there anything newer?* needs PyPI, so it goes to a thread and comes back as a banner, or never comes back at all.

        Neither is asked of an installed Woodcore (v0.83): its packages are the ones it was built with, frozen inside it, and pip has nothing to install them into.
        """
        if getattr(sys, "frozen", False):
            return
        mismatch = dependencies.check()
        if mismatch:
            detail = "\n".join(
                self.t("deps_line_missing", name=name, wanted=wanted) if found is None
                else self.t("deps_line_other", name=name, wanted=wanted, found=found)
                for name, wanted, found in mismatch
            )
            if QMessageBox.question(self, self.t("deps_title"), self.t("deps_mismatch", detail=detail)) == QMessageBox.StandardButton.Yes:
                self.run_pip(None)

        def ask_pypi():
            try:
                found = dependencies.updates()
            except Exception:  # broad: an answer nobody asked for must never be able to bring the window down
                found = []  # an answer nobody asked for must never be able to bring the window down
            self.updates_found.emit(found)

        self.updates_found.connect(self.on_updates)
        threading.Thread(target=ask_pypi, daemon=True).start()

    def on_updates(self, found):
        """PyPI has answered. Rebuild so the banner appears; say nothing when there is nothing to say."""
        if not found or tuple(map(tuple, found)) == tuple(self.dependency_updates):
            return
        self.dependency_updates = tuple(map(tuple, found))
        self.rebuild()

    def install_updates(self):
        """The banner's button: install the newer versions and pin them, on a yes."""
        packages = [(name, available) for name, _pinned, available in self.dependency_updates]
        detail = ", ".join(
            self.t("deps_update_one", name=name, pinned=pinned, available=available)
            for name, pinned, available in self.dependency_updates
        )
        if QMessageBox.question(self, self.t("deps_title"), self.t("deps_update_ask", detail=detail)) != QMessageBox.StandardButton.Yes:
            return
        if self.run_pip(packages):
            # The file and the machine must go on saying the same thing: installing without pinning would produce, from the other side, exactly the disagreement check() reports.
            dependencies.pin(packages)
            self.dependency_updates = ()
            self.rebuild()

    def run_pip(self, packages):
        """Runs pip with the wait cursor on, and reports the outcome. Returns whether it worked."""
        ok, output = busy.run_in_thread(self, self.t("busy_installing"), lambda: dependencies.install(packages))
        if ok:
            notices_ui.tell(self.t("deps_ok"), notifications.INFO, key="deps_ok", title_key="deps_title", source="woodcore_gui")
        else:
            notices_ui.tell(self.t("deps_failed", output=output[-1500:]), notifications.WARNING, key="deps_failed", args=dict(output=output[-1500:]), title_key="deps_title", source="woodcore_gui")
        return ok

    def stale_text(self):
        if self.data is None:
            return ""
        try:
            stale = stale_workbooks(self.data)
        except OSError:
            return ""
        return self.t("stale", files=", ".join(stale)) if stale else ""

    def take_colours(self):
        """The colours the window states itself, read from the scheme in force (theme.py): the grey of secondary text, and the two marks of section 10quater read by dirty_mark() -- the dot in the text's own ink, white in the dark scheme, and the blank that keeps its room."""
        self.muted = theme.colour("muted")
        self.marks = (mark_icon(None), mark_icon(QColor(theme.colour("ink"))))

    def take_fonts(self):
        """The fonts the window states itself, taken from the application's -- whose size is the zoom's (theme.set_zoom) -- when the window is built and again after a zoom: the bold, the titles' a quarter larger, the code's, and the room of a tab's mark (issue #85)."""
        base = QApplication.font()
        self.bold_font = QFont(base)
        self.bold_font.setBold(True)
        self.title_font = QFont(self.bold_font)
        self.title_size = "large"
        if base.pointSizeF() > 0:
            self.title_font.setPointSizeF(base.pointSizeF() * 1.25)
            self.title_size = f"{self.title_font.pointSizeF():g}pt"
        # The site's code font, Cascadia Mono on Windows (theme.py, v0.90) -- Consolas until then, where Qt's own fixed font, Courier New, was thin beside the text around it
        self.mono_font = theme.mono_font(base.pointSizeF())
        self.mark_size = QSize(theme.scaled(MARK_PX), theme.scaled(MARK_PX))

    def show_zoom(self):
        """«Zoom 120 %» in the status bar while the interface is not at its size, nothing at 100 %."""
        percent = theme.zoom()
        self.zoom_status.setText(self.t("zoom_status", percent=percent) if percent != theme.ZOOM_DEFAULT else "")
        self.zoom_status.setVisible(percent != theme.ZOOM_DEFAULT)

    def rezoom(self):
        """The interface's zoom changed (theme.set_zoom): the fonts the window copied taken again and the window built again, as a change of scheme builds it -- the application's font, which most widgets inherit, has already changed."""
        self.take_fonts()
        self.show_zoom()
        self.rebuild()

    def retheme(self):
        """The scheme changed (*Fichier → Apparence*, or Windows while the appearance follows it): the palette and the style sheet are the application's and changed with it, but a widget that stated a colour of its own when it was built -- the orange of a value written over -- is built again, the way a language switch builds the window again."""
        self.take_colours()
        self.rebuild()

    def folder_settings(self, key):
        """The folders tab `key` holds nothing in, as the project file keeps them (`gui.empty_folders`, v0.83; `katalog.empty_folders` in a file written before v0.96, still read). They lived in settings.json from v0.75 to v0.82, where one project's empty folders showed in every other; take_over_folders hands those to the first project opened after."""
        return project.current().empty_folders(key)

    @property
    def list_store(self):
        """The order of the window's lists and the «Formules» tab's folders (calc/list_order.py, issue #15), one store for the window: the project read at every call, a drop refused while the project is read only -- the way `save_folder_settings` refuses -- and a file that cannot be read said once, as a warning, the lists then following the ids."""
        store = getattr(self, "_list_store", None)
        if store is None:
            store = self._list_store = list_order.Store(
                project.current, lambda: bool(getattr(self, "read_only", False)),
                warn=lambda message: notices_ui.tell(message, notifications.WARNING, source="list_order"))
        return store

    def save_folder_settings(self, key, names):
        """Writes tab `key`'s empty folders into the project file at once, and only when they changed -- so a folder made and the window then killed is not lost, and rebuilding a list writes nothing. Not in a project opened read-only, whose folders live for the session."""
        if self.read_only:
            return
        try:
            project.set_empty_folders(project.current(), key, names)
        except (project.ProjectError, OSError):
            pass  # a folder that cannot be kept is not worth interrupting anyone for

    def take_over_folders(self):
        """The empty folders settings.json kept until v0.83, written into this project once -- where it keeps none of its own -- and taken out of the settings, so a second project does not inherit them."""
        settings = read_settings()
        folders = settings.get("folders")
        if not isinstance(folders, dict) or self.read_only:
            return
        here = project.current()
        if not here.gui():
            try:
                for key, names in folders.items():
                    if isinstance(names, list):
                        here = project.set_empty_folders(here, key, names)
            except (project.ProjectError, OSError):
                return
        settings.pop("folders", None)
        write_settings(settings)
        self.settings = settings

    def store(self, **values):
        """Writes `values` into the settings as they stand on disk -- another window, or the start page, may have written since this one read them (the recent projects)."""
        settings = read_settings()
        settings.update(values)
        write_settings(settings)
        self.settings = settings

    def on_language(self, index):
        chosen = self.language.itemData(index)
        if chosen != self.lang:
            self.lang = chosen
            self.store(lang=chosen)
            install_qt_translation(chosen)
            self.rebuild()

    def reload(self):
        with busy.hold(self, self.t("busy_loading"), guard=False):
            self.load()
            self.rebuild()

    def set_status(self, text):
        self.status.setText(text)

    def dirty_mark(self, dirty):
        """The dot that marks unsaved changes, or the blank of the same size -- an editor sets one on every row of its list, so the room is there either way."""
        return self.marks[bool(dirty)]

    def update_tab_marks(self):
        """The dot before the title of every tab holding unsaved changes. Called by the editors themselves, each time they refresh the mark on their own list; a browser and a reserved tab have nothing to save and keep the blank."""
        for index in range(self.tab_widget.count()):
            dirty = getattr(self.tab_widget.widget(index), "dirty", False)
            self.tab_widget.setTabIcon(index, self.dirty_mark(dirty))
            if getattr(self, "nav", None) is not None:
                self.nav.set_dirty(index, dirty)
        self.update_title()

    def update_title(self):
        """«Musterprojekt — Woodcore», with «•» before it while a tab holds unsaved changes, as an editor marks a document not saved -- and «(lecture seule)» after it in a project another window holds (v0.83)."""
        dirty = any(getattr(tab, "dirty", False) for tab in getattr(self, "tabs", ()))
        title = f"{'• ' if dirty else ''}{project.current().name} — Woodcore"
        if self.read_only:
            title += f" ({self.t('read_only_suffix')})"
        self.setWindowTitle(title)

    def build_menu(self):
        bar = self.menuBar()
        bar.clear()
        menu = bar.addMenu(self.t("file_menu"))
        menu.setToolTipsVisible(True)
        menu.addAction(self.t("file_new"), self.new_project)
        action = menu.addAction(self.t("file_open"), self.open_other)
        action.setShortcut(QKeySequence(QKeySequence.StandardKey.Open))
        recent = menu.addMenu(self.t("file_recent"))
        here = project.current().file
        files = [f for f in usersettings.recent_projects(read_settings()) if Path(f).resolve() != here]
        for file in files:
            entry = recent.addAction(f"{Path(file).stem}   —   {Path(file).parent}", lambda file=file: self.open_file(file))
            entry.setEnabled(Path(file).is_file())
        if not files:
            recent.addAction(self.t("file_recent_empty")).setEnabled(False)
        menu.addAction(self.t("file_open_window"), self.open_in_new_window)
        menu.addAction(self.t("file_close"), self.close_project)
        menu.addSeparator()
        menu.addAction(self.t("file_properties"), self.edit_properties)
        menu.addAction(self.t("file_show_folder"), lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(project.current().root))))
        menu.addAction(self.t("file_open_pdf"), self.open_pdf)
        menu.addAction(self.t("file_open_vscode"), self.open_vscode)
        if not getattr(sys, "frozen", False):
            menu.addSeparator()
            dev = menu.addAction(self.t("file_dev"))
            dev.setCheckable(True)
            dev.setChecked(self.dev_launcher())
            dev.setToolTip(self.t("file_dev_tip"))
            dev.toggled.connect(self.set_dev_launcher)
        menu.addSeparator()
        action = menu.addAction(settings_dialog.menu_text(self.lang), self.open_settings)
        action.setShortcut(QKeySequence(settings_dialog.SHORTCUT))
        legal.add_about_action(menu, self, self.lang)   # © 2026 Florian Lamprecht, the licence and the third-party notices (legal.py)
        menu.addSeparator()
        action = menu.addAction(self.t("file_quit"), self.close)
        action.setShortcut(QKeySequence(QKeySequence.StandardKey.Quit))
        # «Affichage» (issue #85): the interface's zoom and its keys, and «Apparence», which stood in «Fichier» until 0.121
        view = bar.addMenu(self.t("view_menu"))
        for action in chrome.zoom_actions(view, self.t):
            view.addAction(action)
        view.addSeparator()
        self.add_appearance_menu(view)

    def add_appearance_menu(self, menu):
        """*Apparence*: Comme Windows, Clair, Sombre -- one exclusive group of checks, the engineer's per user (theme.py, v0.90). Read-only or not, it writes only the user's own settings."""
        sub = menu.addMenu(self.t("file_appearance"))
        group = QActionGroup(sub)
        group.setExclusive(True)
        chosen = theme.appearance()
        for value in theme.APPEARANCES:
            action = sub.addAction(self.t(f"file_appearance_{value}"))
            action.setCheckable(True)
            action.setChecked(value == chosen)
            action.setData(value)
            group.addAction(action)
        # once the menu has closed: set_appearance builds the window again, this menu with it, and a menu is not taken apart from inside its own signal
        group.triggered.connect(lambda action: QTimer.singleShot(0, functools.partial(theme.set_appearance, action.data())))
        return sub

    def refuse_read_only(self):
        notices_ui.tell(self.t("read_only_refused"), notifications.INFO, key="read_only_refused", source="woodcore_gui")

    def busy(self):
        """Whether an export or a compilation runs -- a project is never changed under one."""
        if self.process is None:
            return False
        notices_ui.tell(self.t("file_busy"), notifications.INFO, key="file_busy", source="woodcore_gui")
        return True

    def ask_project_file(self):
        file, _filter = QFileDialog.getOpenFileName(self, self.t("open_project_title"), str(project.current().root.parent), self.t("open_project_filter"))
        return file or None

    def open_file(self, file):
        if file and Path(file).resolve() != project.current().file:
            self.switch_to(["--project", str(file)])

    def open_other(self):
        self.open_file(self.ask_project_file())

    def close_project(self):
        self.switch_to(["--home"])

    def edit_properties(self):
        """*Fichier → Propriétés du projet*: the «Projet» tab brought forward, where the title page, the form, the documents and the version pinned are (issue #87) -- what every tab holds unsaved saved first. A project opened read-only shows it too, nothing in it writable."""
        self.autosave_all("tab")
        self.tab_widget.setCurrentIndex(self.project_index())

    def open_settings(self):
        """*Fichier → Paramètres…* (Ctrl+,): the settings and the templates a new project is made from (settings_dialog.py, v0.94), «Enregistrer ce projet comme modèle» taking this project's report. It writes the user's settings and templates, never the project, so a project opened read-only offers it too."""
        settings_dialog.open_dialog(self, self.lang, here=project.current())

    def open_pdf(self):
        """The PDF of the document shown -- the report's in a project laid out as one report."""
        pdf = project.current().document_pdf(self.current_document())
        if not pdf.is_file():
            notices_ui.tell(self.t("file_no_pdf"), notifications.INFO, key="file_no_pdf", source="woodcore_gui")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf)))

    def open_vscode(self):
        """The project's folder in VS Code, the entry file of the document shown open in it -- the one to pin Tinymist to (docs/conventions/build-and-release.md §12). The project's folder is Tinymist's workspace, which is the Typst root of a project in three documents: the root-absolute `/commands.typ` its sections import then resolves as the command line resolves it."""
        code = vscode_executable()
        if code is None:
            notices_ui.tell(self.t("file_no_vscode"), notifications.INFO, key="file_no_vscode", source="woodcore_gui")
            return
        here = project.current()
        entry = here.document_typ(self.current_document())
        # a document not made yet (issue #90) is no file to open: the project's folder alone
        proc.start_detached(code, [str(here.root)] + ([str(entry)] if entry.is_file() else []), str(here.root))

    def ask_migration(self):
        """The banner's «Migrer…»: this window closed -- asking for what is unsaved, as closing always does -- and the project opened again in a process of its own, which asks its migration first (`--migrate`, migrate_dialog.offer). A project is never migrated under a window that has it open: its folders are renamed, and a file this window holds would stop the rename half-way."""
        self.switch_to(["--project", str(project.current().file), "--migrate"])

    def dev_launcher(self):
        """Whether a .woodcore double-clicked starts Woodcore from these sources (the launcher reads it, packaging/launcher.py)."""
        launcher = read_settings().get("launcher")
        chosen = launcher.get("dev_checkout") if isinstance(launcher, dict) else None
        return bool(chosen) and Path(chosen).resolve() == project.APP_ROOT.resolve()

    def set_dev_launcher(self, on):
        settings = read_settings()
        launcher = dict(settings.get("launcher") or {})
        if on:
            launcher["dev_checkout"] = str(project.APP_ROOT)
        else:
            launcher.pop("dev_checkout", None)
        if launcher:
            settings["launcher"] = launcher
        else:
            settings.pop("launcher", None)
        write_settings(settings)
        self.settings = settings

    def copy(self, text):
        QGuiApplication.clipboard().setText(text)  # Qt hands it over to Windows on exit, so it outlives the window
        self.set_status(self.t("copied", text=one_line(text)))
