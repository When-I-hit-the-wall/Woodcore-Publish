"""Woodcore's window (the Typst-Katalog until v0.83, the Katalog until v0.96): a window listing every value the report can quote -- the loads, split into permanent and variable actions, each with the workbook, sheet and cell it comes from -- and copying the exact Typst call that prints it (docs/ui/window.md §10quater). Its editor tabs are where a position plan, a static model, a detail schema, a connector and a polar-moment calculation are defined; its «Moments polaires» tab names a detail schema, the markers or points ticked on it, the rotation centre and the directions of N and V, with the fastener group's polar moment of inertia (section 3.3quinquies).

The loads come from data/calculations.json, the validated export Typst itself reads, so a call copied here is one that compiles. Every call is built by build_reference's call_* functions, the same ones behind docs/typst-reference.xlsx's example_call columns, so the window and the workbook cannot spell a call two ways. Nothing here computes or rewrites a load: the window only shows what the pipeline exported, and reruns that pipeline (calc/export_all.py) on request.

A project written as three documents -- the convention d'utilisation, the base de projet and the report, which is simply the third (the engineer's request of 30.09.2026) -- is shown one document at a time, chosen in a drop-down at the top of the navigation: each shows its own modules (MODE_TABS), its own journal, and «Exporter PDF» exports it -- «Exporter les trois» the three -- compiling only a document whose Typst changed since its PDF (calc/stamps.py). A project still laid out as one report is offered its migration as it opens (migrate_dialog.py).

A polar-moment calculation is saved as its source, connections/<id>.json, its id made from its name (connection.id_from_name) and naming no connector since v0.76, and exported at once by the same code export_all.py runs (calc/domains/connection.py) -- data/connections.json and the figures, without the load workbooks being read again.

Launched by Woodcore.bat beside the code, by Woodcore.exe once installed, or `python calc/tools/woodcore_gui.py [--project <file>.woodcore] [--home]` -- `catalog_gui.py` until v0.96 (its shim, for the launchers of 0.83 to 0.90, removed in v0.120). Started without a project it opens on the start page (home_page.py, v0.83); a project is opened in its own process, one project per window, and the *Fichier* menu opens another in a process of its own. A PySide6 (Qt) window since v0.30 -- standard-library tkinter before it -- carrying its own icon, woodcore.svg beside this file (typst-katalog.svg until v0.83), in its title bar and on the taskbar (docs/decisions.md §13).
"""

if __name__ == "__main__":
    # Run directly -- Woodcore.bat, Woodcore started again -- the start screen comes first, before this module's own imports take their seconds (woodcore_start.py, v0.117); it imports this module again, by its name, and calls main().
    import os as _os
    import sys as _sys
    _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    import woodcore_start as _start
    _start.main()
    raise SystemExit(0)

import atexit
import functools
import json
import math
import os
import shutil
import sys
import threading
import traceback
from datetime import datetime
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
# calc/ first: the tools below, and this window, find the project they work on through calc/project.py (v0.81) -- before the parts split out of this module (issue #30), whose words import home_page, which imports calc/doc_templates.py.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from woodcore_gui_words import STRINGS, _check_strings  # split out of this module (issue #30): every name it had is still importable from it
from polar_tab import (  # split out of this module (issue #30): every name it had is still importable from it
    DIGITS,
    MAX_MEMBERS,
    MIN_MEMBERS,
    POLAR_NEW_ROW,
    PolarTab,
    SUBSCRIPTS,
    angle_box,
    clean_number,
    default_source,
    fmt_value,
    form_layout,
    length_box,
    list_connections,
    members_from_schema,
    narrow_combo,
    next_free_name,
    plain_label,
)
from woodcore_gui_menus import MARK_PX, _QT_TRANSLATOR, config_stamp, data_file, install_qt_translation, mark_icon, one_line, read_settings, stale_workbooks, vscode_executable, write_settings, WindowMenusMixin  # split out of this module (issue #30): every name it had is still importable from it
from woodcore_gui_export import EXPORT_TIMEOUT_MS, LANGUAGES, cli_command, console_python, WindowExportMixin  # split out of this module (issue #30): every name it had is still importable from it

import project  # noqa: E402  -- where the program is, and where the project it works on is
import proc  # noqa: E402  -- every child process starts through it: no console window flashing open (calc/proc.py)
import documents  # noqa: E402  -- the three documents a project is written as, and the one spelling of a document's compile (30.09.2026)
import stamps  # noqa: E402  -- whether a document's Typst changed since its PDF: an unchanged one is neither compiled nor archived
import project_lock  # noqa: E402  -- the lock a window holds on its project (v0.83)
import shown_variables  # noqa: E402  -- what the level of detail -1 offers to tick (issue #20, v0.117)
import usersettings  # noqa: E402  -- Woodcore's own preferences, %APPDATA%\Woodcore (v0.83)
import busy  # noqa: E402  -- the card shown while the window works, its input held (v0.113)
import home_page  # noqa: E402  -- the start page, the project dialog, the File menu's words (v0.83)
import migrate_dialog  # noqa: E402  -- a project laid out as one report, offered its migration into three documents as it opens
import settings_dialog  # noqa: E402  -- *Fichier → Paramètres…*: the settings and the project templates (v0.94)
import typst_gui  # noqa: E402  -- Typst checked at every start from the sources, a newer one offered (v0.94)
import archive_export  # every successful compile lands a zip in the project's _Archiv/, called the same way woodcore-cli does (docs/conventions/build-and-release.md §12)
import build_reference as ref
import dependencies
import grouped_list  # the left pane of every editor tab: folders, drag and drop, Ctrl/Shift (grouped_list.py)
import source_archive  # «Supprimer» archives rather than deletes (source_archive.py)
import identity  # the Nom · Description · ID rows the editor tabs share (identity.py)
import chrome  # the window's frame after the website's: the language switch, the side navigation, the icons (chrome.py, v0.91)
import command_palette  # the command palette, Ctrl+K (issue #83)
import pdf_pane  # every Typst page of the window, zoomed by Ctrl+wheel and fitted back when its tab is left (issue #89)
import views  # the views of a tab and the switch in the top bar that chooses one (views.py, v0.117)
import autosave  # saving without a question when a tab, a view, a document or the window is left (autosave.py, v0.117)
import notifications  # noqa: E402  -- every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # noqa: E402  -- the red octagon and the orange triangle at the top right, and their panel (v0.117)
import list_order  # noqa: E402  -- the order of the window's lists and the «Formules» tab's folders, Woodcore-Datei/lists.json (issue #15)
import layout_store  # noqa: E402  -- the panes' sizes by tab, by view and by the screens plugged in (v0.117)
import variable_sources  # every variable of a project and where it comes from; instance_workbook (calc/variable_sources.py, v0.117)
import display_options  # the option panels of the «Affichage» views, one per command (display_options.py, v0.117)
import display_view  # the «Affichage» view a tab shows its commands in (display_view.py, v0.117)
import richtext  # symbols as mathematics, Typst calls coloured, «Copié ✓» (richtext.py, v0.92)
import cards  # forms in cards, after the website (cards.py, v0.93)
import nowheel  # the wheel scrolls and zooms, it never changes a value (nowheel.py)
import stallwatch  # where the window was when it stopped answering, written to %LOCALAPPDATA% (stallwatch.py)
import theme  # the website's look: one palette, one style sheet, light or dark (theme.py, v0.90)
import legal  # *Fichier → À propos de Woodcore…*: the copyright, the licence and the third-party notices

# calc/ itself, put on the path above, for the connection domain: the polar moments tab calculates and draws with the very functions export_all.py does, never a copy of them.
import engine  # noqa: E402
import validation  # noqa: E402
from domains import connection, connection_svg  # noqa: E402
from domains import connector as connector_model  # noqa: E402  -- the one reader of the exported positions (known_positions)
from domains import schema as schema_model  # noqa: E402  -- a connection is drawn on one
# The position plan tab, a module of its own beside this one (docs/domain/position-plans.md §3.3sexies): its texts join STRINGS below, its class TABS.
import plan_tab  # noqa: E402
import drawing_tab  # noqa: E402  -- the base the plan tabs share (v0.115): its writers are guarded with them (WRITERS, below)
import fire_tab  # noqa: E402  -- the fire protection plan tab (v0.115), the position plan's sibling on the same base: its texts join STRINGS below, its class TABS

# The positions tab (v0.94): the project's positions, Woodcore's own since v0.114 (calc/positions_store.py) -- its texts join STRINGS below, its class TABS.
import positions_tab
import reserved_tab  # the one class of a tab to come: the six reserved tabs (spec 2026-10-19-base-saine-nettoyage, ARCH-001)  # noqa: E402
import action_tabs  # the words of the six empty tabs of «Actions» (v0.117, docs/ui/window.md §10quater)  # noqa: E402
import load_tab  # the loads entered in Woodcore: «Poids propre et surcharge», «Neige», «Vent» (issues #35-#37, docs/domain/loads.md)  # noqa: E402
import fire_check_tab  # the «Résistance au feu» tab: the member checks in the design situation fire, SIA 265 4.5.2, and VKF 15-15 (issue #46)  # noqa: E402
import steel_tab  # the «Acier» tabs: the steel checks of SIA 263 (issues #50-#52, docs/ui/tab-steel.md)  # noqa: E402
import profile_tab  # the «Profilés» tab of «Acier»: the SZS C5 library and the free profiles (issue #50)  # noqa: E402
import member_check_tab  # the member checks of SIA 265 chapter 4 -- «Traction» and the placeholders of the two navigation groups «Sécurité structurale» and «Aptitude au service» (docs/domain/member-checks.md §3.3undecies, docs/ui/window.md §10quater)  # noqa: E402
import journal_tab  # the journal tab (v0.99): the report's revisions, written by hand (docs/domain/journal.md §3.3terdecies)  # noqa: E402
import annex_tab  # the annexes tab (v0.115): the documents the report draws on, and the excerpts it shows of them (docs/domain/annexes.md §3.3undevicies)  # noqa: E402
import structure_tab  # the «Structure du document» tab, the one tab a document is written in (the rework of 01.10.2026): its tree of chapters, sections and objects, the page of what is chosen, the options of its kind, and what is shared with the other documents (structure_tab.py)  # noqa: E402
import python_tab  # the Python tab (v0.100): the engineer writes Python, runs it and the report reads its named results (docs/domain/scripts.md §3.3sexdecies)  # noqa: E402
import formula_tab  # the «Formule» tab (v0.117): calculation domains written as blocks of var, eq, verify, val, one Formules/<id>.typ each (calc/domains/formula_domain.py)  # noqa: E402
import variables_tab  # the «Variables» tab: every value the report itself computes, read back out of a compiled report (calc/variables.py)  # noqa: E402

# The static models tab, a module of its own beside this one (docs/domain/static-models.md §3.3octies): its texts join STRINGS below, its class TABS.
import statics_tab  # noqa: E402

# The detail schemas tab, likewise (docs/domain/connections.md §3.3quinquies): the one place a connection detail is drawn.
import schema_tab  # noqa: E402

# The commands tab, a module of its own beside this one (docs/typst/command-docs.md §10sexies): its texts join STRINGS below, its class TABS.
import commands_tab
import connectors_tab  # noqa: E402

# The user's preferences are usersettings.py's: %APPDATA%\Woodcore\settings.json, or the file `WOODCORE_SETTINGS` names -- what the tests do, so that a test run never writes the engineer's own preferences (v0.75, v0.83).

# The window's icon, in its title bar and on its taskbar button: a drawing written as SVG text, so Qt renders it sharp at every size and Git shows what changed in it. Read from the program's own folder, which is the checkout or, once installed, the folder the executable unpacks it into.
# The icon, the taskbar's AppUserModelID and the claim of the icon for the taskbar are the start module's (woodcore_start.py, v0.117), which shows its screen before this module is imported.
from woodcore_start import APP_ID, ICON_FILE, claim_taskbar_icon  # noqa: E402,F401
import woodcore_start  # noqa: E402  -- the start screen: told which tab is being built


# An export document's words, prefixed bv_ (bundle_view.py, v0.117).
import bundle_view  # noqa: E402


_check_strings()


# --- Reading the export ---------------------------------------------------


def load_data(path=None):
    return json.loads(Path(path or data_file()).read_text(encoding="utf-8"))


# --- Settings (per user, outside the project) -------------------------------


# --- Connections (docs/domain/connections.md §3.3quinquies) ---------------------------




# Every tab, declared once in tab_registry.SPECS (spec 2026-10-19-base-saine-nettoyage, ARCH-001): the lists the window reads are derived from it, under the names it always read -- TABS, the side navigation's groups and sub-titles, which documents show which tab, the tabs bound to one document.
from tab_registry import DOCUMENT_TABS, GUARDED_TABS, MODE_BOUND, MODE_TABS, NAV_GROUPS, NAV_SECTIONS, SPECS, TABS  # noqa: E402,F401


def mode_tabs(mode):
    """The keys of TABS document `mode` shows, in TABS' order."""
    shown = MODE_TABS.get(mode, MODE_TABS["rs"])
    return [key for key, _factory in TABS if key in shown]


def mode_key(file):
    """The key a project's document is remembered under in the user's settings: its file, as the platform compares names."""
    return os.path.normcase(str(Path(file).resolve()))

# The read-only guard and the domains' files after a writer (tab_guard.py, spec 2026-10-19-base-saine-nettoyage, ARCH-RISK-101): applied by tab_registry to every tab class, where each writer is defined, once.
from tab_guard import WRITERS, own_classes, refused_when_read_only  # noqa: E402,F401


def note_text(note, lang):
    """A warning of a domain module in the window's language: the sentence of its code where it is an `engine.Note` (`"warn_" + code`), its values written in the window's language too where they are Notes themselves; else the sentence as the export printed it. A ValidationError is not one: it is a defect in a file, for whoever repairs the file, and stays English (periodic audit 260916, AUD-4-11)."""
    code = getattr(note, "code", None)
    table = STRINGS[lang if lang in STRINGS else "en"]
    if not code or "warn_" + code not in table:
        return str(note)
    args = {key: note_text(value, lang) if getattr(value, "code", None) else value for key, value in note.args.items()}
    return table["warn_" + code].format(**args)


class MainWindow(WindowExportMixin, WindowMenusMixin, command_palette.PaletteWindowMixin, QMainWindow):
    # PyPI is asked in a thread of its own (check_dependencies), and Qt widgets may only be touched from the thread that made them -- so the answer comes back as a signal rather than as a call.
    updates_found = Signal(list)

    def __init__(self, read_only=False, holder=None, newer=None, migration_banner=False):
        super().__init__()
        theme.ensure()  # before anything reads the palette: a window built without main() -- a test's -- is dressed as the engineer sees it
        self.settings = read_settings()
        # The document shown, of the three a project is written as (the engineer's request of 30.09.2026): the one last shown in this project, as the user's settings keep it (`document_modes`), else the convention d'utilisation -- the first of the three a project is written in, and the one a new project is begun with -- and the report alone in a project laid out as one report. A property of the window and not of build(), so a rebuild keeps it.
        self.mode = self.remembered_mode()
        # A project laid out as one report whose migration the engineer put off, or which could not be migrated (open_project): a banner says so and offers «Migrer…».
        self.migration_banner = bool(migration_banner)
        self.shortcuts = []   # Ctrl+1 … Ctrl+9, made again whenever the modules shown change (apply_mode)
        # The documents the PDF button asked for and those still to compile, one after the other (compile_next): what is compiled, and with which flags, is fixed when the button is clicked.
        self.pdf_modes = None
        self.compile_queue = []
        self.compile_flags = []
        self.compile_messages = []
        self.compile_single = True
        self.compile_mode = None
        self.compile_deps = None
        self.last_pdf = None
        # Another window holds the project (project_lock.py) and the engineer chose to look without writing: every way the tabs write a source is refused (WRITERS, below), and neither the export nor the PDF runs (v0.83).
        self.read_only = bool(read_only)
        self.holder = holder or {}
        # The version of the newer Woodcore that wrote the project's engine, where that is why the window is read-only (open_project, v0.87); None where it is not.
        self.newer = newer
        # [(package, pinned, available), ...] once PyPI has answered; () until then, and () for good where there is no network. Read by the banner, which is rebuilt when the signal arrives.
        self.dependency_updates = ()
        self.lang = self.settings.get("lang") if self.settings.get("lang") in LANGUAGES else "fr"
        install_qt_translation(self.lang)
        self.views = {}  # each tab's view_state(), by title key, carried through a rebuild
        self.kept_views = {}  # the view each tab shows, by title key, carried through a rebuild (issue #86): never the user's settings
        self.picking = False  # a variable being chosen in «Variables» for the tab that asked: that tab keeps its view while it waits (issue #86)
        self.tab_index = 0
        self.process = None  # the export or the compilation running, if any -- never both, they run one after the other
        self.close_requested = False
        # What the next PDF will be compiled with, chosen in the export button's menu and read by pdf_input_args(). ("level", n) or ("uniform", n) forces one, (None, None) passes no --input at all, so the document's own base level governs (docs/typst/report-engine.md §4); the language likewise, None being the one the document declares (section 4bis). They live here rather than in build(), which is played again on every rebuild and takes its widgets with it, and they are deliberately not written to settings.json: a forced level remembered from another day is one nobody would look for.
        self.pdf_level = (None, None)
        self.pdf_lang = None
        self.pending_pdf = False  # the export running was asked for by the PDF button, so compile when it succeeds
        self.saving_quietly = False  # a tab saving without a question right now (autosave.py, v0.117)
        self.quiet_reasons = []
        self.quiet_export = False  # the export running was started by a save without a question: its warnings go to the status line
        self.light_export = False  # the export running was started by a position saved: the window is not built again after it, the tab in front is (refresh_lightly, v0.117)
        self.stale_tabs = set()    # the keys of the tabs that hold what an export has since replaced: each is built again when it is next shown (refresh_tab)
        self.stale_banner = None   # the banner of workbooks changed since the export, which a light refresh takes off
        self.autosave_pending = False  # a save put off while an export or a compilation ran, made when it ends
        # The window left for another application -- VS Code, Excel -- saves what can be saved (the engineer's answer of 07.10.2026); the application's state and not the window's, which a box of Woodcore's own would also take the focus from (review A03).
        QGuiApplication.instance().applicationStateChanged.connect(self.on_application_state)
        self.compiling = False  # which of the two the process is, for the one message that has to name it

        self.take_fonts()
        self.take_colours()

        # the project's name first, the way Word names its document: two windows on two projects are told apart on the taskbar (v0.82) -- and «•» before it while a tab holds unsaved changes (update_title, v0.83)
        self.setWindowTitle(f"{project.current().name} — Woodcore")
        self.setMinimumSize(900, 500)
        self.resize(self.remembered_size())

        self.status = plain_label("")
        self.status.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)  # a long call just copied must not widen the window
        self.statusBar().addWidget(self.status, 1)
        # «Zoom 120 %» while the interface is not at its size (issue #85): built once with the status bar, as the status line is, and said again by `rezoom`
        self.zoom_status = plain_label("")
        self.zoom_status.setObjectName("meta")
        self.statusBar().addPermanentWidget(self.zoom_status)
        self.show_zoom()

        self.take_over_folders()
        self.load()
        self.build()

    def t(self, key, **kwargs):
        text = STRINGS[self.lang][key]
        return text.format(**kwargs) if kwargs else text

    # -- the document shown (the engineer's request of 30.09.2026) --

    def remembered_mode(self):
        """The document last shown in the current project, as the user's settings keep it by project file. Where none is kept -- a project just made, or one never switched -- or the one kept is not one of the project's: the convention d'utilisation in a project written in three documents, which is where a project is begun (the engineer's request of 01.10.2026), and the report in a project laid out as one report, whose only document it is. A document once chosen, the report included, is kept."""
        here = project.current()
        kept = self.settings.get("document_modes")
        mode = kept.get(mode_key(here.file)) if isinstance(kept, dict) else None
        if mode in here.created_modes:
            return mode
        # the first document made, in the navigation's order -- the report for a project just made, which has none yet (issue #90)
        return next(iter(here.created_modes), "rs")

    def current_document(self):
        """The document the window works on -- `mode` where it is one of the current project's documents, else the report, which every project has. What a tab asks when it reads or writes one document's own files."""
        return self.mode if self.mode in project.current().modes else "rs"

    def document_name(self, mode=None):
        """What document `mode`, the one shown where none is named, is called in the window's language: «Base de projet»."""
        return documents.mode_name(mode or self.current_document(), self.lang)

    def remember_mode(self):
        settings = read_settings()
        kept = dict(settings.get("document_modes") or {})
        kept[mode_key(project.current().file)] = self.mode
        settings["document_modes"] = kept
        write_settings(settings)
        self.settings = settings

    def on_mode_changed(self, mode):
        """Another document chosen in the navigation's drop-down. What the modules bound to the document shown hold unsaved is asked about first, and an «Annuler» keeps the engineer on the document he was on; then the modules the document shows are shown, and each tab that reads one document's files is told (`on_mode`). The window is not built again: a rebuild carries each tab's view through it, and would carry a journal entry half written into another document's journal."""
        if mode == self.mode or mode not in project.current().modes:
            return
        self.autosave_all("tab")   # what can be saved is, without a question (v0.117); the modules bound to the document then ask where it could not
        for (key, _factory), tab in zip(TABS, self.tabs):
            confirm = getattr(tab, "confirm_leave", None)
            if key in MODE_BOUND and confirm is not None and not confirm():
                self.nav.set_mode(self.mode)
                return
        self.mode = mode
        self.remember_mode()
        with busy.hold(self, self.t("busy_switching"), guard=False):
            self.apply_mode()
            # every change of document brings the «Projet» tab forward, always -- even where the tab in front is one of both documents (the engineer, 21.10.2026, issue #87): nothing is compiled by the change itself
            self.tab_widget.setCurrentIndex(self.project_index())
            for tab in self.tabs:
                if hasattr(tab, "on_mode"):
                    tab.on_mode(mode)
                    busy.pump()
        self.update_pdf_tooltip()

    def apply_mode(self):
        """The modules the document shown shows (MODE_TABS), and nothing else: the navigation's rows, Ctrl+1 … Ctrl+9 for those it lists, and the module in front one of them."""
        by_key = {key: index for index, (key, _factory) in enumerate(TABS)}
        shown = [by_key[key] for key in mode_tabs(self.current_document())]
        self.nav.set_visible(shown)
        self.nav.set_unavailable([index for index in shown if not self.available(TABS[index][0])], self.t("pj_not_made_tip"))
        for button in (getattr(self, "pdf_button", None),):
            if button is not None:
                button.setEnabled(project.current().is_created(self.current_document()))   # no PDF of a document not made yet
        order = self.nav.order()
        if order and self.tab_widget.currentIndex() not in order:
            self.tab_widget.setCurrentIndex(order[0])
        self.bind_shortcuts()

    def project_index(self):
        """The index of the «Projet» tab, the first row of the navigation (issue #87)."""
        return next(index for index, (key, _factory) in enumerate(TABS) if key == "tab_project")

    def available(self, key):
        """Whether tab `key` can be opened in the document shown: every tab of a document that is made, and the «Projet» tab alone in one that is not yet (issue #90: «tout est grisé sauf l'onglet Projet»)."""
        return key == "tab_project" or project.current().is_created(self.current_document())

    def project_changed(self):
        """The project file rewritten by the «Projet» tab: its name where the window shows it -- the top bar, the title -- and what the tabs that show a compiled page read (issue #87: the name in the top bar was never refreshed)."""
        here = project.current()
        if getattr(self, "brand", None) is not None:
            self.brand.setText(here.name)
        self.update_title()

    def properties_written(self, look_changed):
        """The project's look changed (a form applied): every tab that shows a compiled page told, so that it is compiled again with it."""
        for tab in self.tabs:
            hook = getattr(tab, "on_properties_changed", None)
            if hook is not None:
                hook(look_changed)

    def document_created(self, mode):
        """Document `mode` made from the «Projet» tab (issue #90): the window built again -- every tab was built against a document that was not there -- and that document shown, the «Projet» tab in front."""
        if mode != self.mode and mode in project.current().modes:
            self.mode = mode
            self.remember_mode()
        self.rebuild()
        self.nav.set_mode(self.mode)
        self.apply_mode()
        self.tab_widget.setCurrentIndex(self.project_index())

    def bind_shortcuts(self):
        """Ctrl+1 … Ctrl+9: the modules in the order the navigation lists them, the ones it shows and no other -- made again, the old ones taken off the window, each time what it shows changes."""
        for shortcut in self.shortcuts:
            try:
                shortcut.setEnabled(False)
                shortcut.setParent(None)
                shortcut.deleteLater()
            except RuntimeError:
                pass   # taken with the content a rebuild replaced
        self.shortcuts = []
        parent = self.centralWidget()
        for n, index in enumerate(self.nav.order()[:9], 1):
            self.shortcuts.append(QShortcut(QKeySequence(f"Ctrl+{n}"), parent, activated=functools.partial(self.tab_widget.setCurrentIndex, index)))

    def note_text(self, note):
        """A domain module's warning in the window's language (`note_text`)."""
        return note_text(note, self.lang)

    def notice_context(self):
        """What a notice copied carries besides itself: Woodcore's version and the project it was met in."""
        try:
            here = project.current()
        except Exception:  # broad: the copy is made whether or not a project is open
            here = None
        return {"Woodcore": project.VERSION, "Project": str(here.file) if here is not None else ""}

    def label(self, key):
        """A field name followed by its colon, set the way each language sets it (`Recherche :`, `Suche:`)."""
        return self.t(key) + (" :" if self.lang == "fr" else ":")

    def remembered_size(self):
        """The size the window was last closed at, kept within the screen -- the tkinter window saved physical pixels, more than Qt's on a scaled display. Only the size is remembered, never the position: a window restored onto a screen that is no longer attached would open out of sight."""
        try:
            width, height = (int(n) for n in str(self.settings.get("size", "")).split("x"))
        except ValueError:
            width, height = 1400, 780
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry().size()
            width, height = min(width, available.width()), min(height, available.height())
        return QSize(width, height)

    def load(self):
        try:
            self.data = load_data()
            self.data_error = None
        except (OSError, ValueError) as exc:
            self.data, self.data_error = None, str(exc)

    def build(self):
        """The window's content, built anew on every language switch and reload; QMainWindow deletes the content it replaces."""
        main = QWidget()
        layout = QVBoxLayout(main)
        layout.setContentsMargins(8, 8, 8, 0)

        # The top bar, after the site's (v0.91): the project's name as the site sets its brand, what the export holds beside it in grey; at the right what a forced level or language will do to the next PDF, the language, and the three actions -- the PDF the primary one.
        top = QHBoxLayout()
        top.setSpacing(8)
        brand = QLabel(project.current().name)
        self.brand = brand   # named again when the «Projet» tab renames the project (project_changed)
        brand.setObjectName("brand")
        brand.setFont(theme.brand_font())   # its size the zoom's, and not the style sheet's (issue #85)
        brand.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        top.addWidget(brand)
        top.addSpacing(4)
        self.meta = plain_label(self.meta_text())
        self.meta.setObjectName("meta")
        top.addWidget(self.meta)
        top.addStretch(1)
        self.pdf_chip = QToolButton()
        self.pdf_chip.setProperty("chip", True)
        self.pdf_chip.setToolTip(self.t("pdf_chip_tip"))
        self.pdf_chip.clicked.connect(lambda: self.pdf_button.showMenu())
        self.pdf_chip.setVisible(False)
        top.addWidget(self.pdf_chip)
        # The view of the tab in front (the engineer's request of 07.10.2026, views.py): hidden for a tab that has no views.
        self.view_switch = chrome.SegmentedSwitch()
        self.view_switch.setObjectName("viewSwitch")
        self.view_switch.setToolTip(self.t("view_switch"))
        self.view_switch.changed.connect(self.on_view_chosen)
        top.addWidget(self.view_switch)
        top.addSpacing(4)
        # What runs in the background, then the critical notices and the warnings, right of the views and left of the languages (issue #11, 08.10.2026 -- they stood left of the views since 07.10.2026; notices_ui.py): the indicators are always there, quiet at zero.
        self.notice_bar = notices_ui.NoticeBar(self.t, self.lang, opener=open_in_editor, context=self.notice_context, mono_font=self.mono_font, status=lambda text: (self.set_status(text) or True) if hasattr(self, "status") else False)
        top.addWidget(self.notice_bar)
        top.addSpacing(4)
        self.language = chrome.LanguageSwitch(LANGUAGES, self.lang)
        self.language.setToolTip(self.t("language"))
        self.language.currentIndexChanged.connect(self.on_language)
        top.addWidget(self.language)
        self.bind_palette(top)   # «Rechercher… Ctrl K», and Ctrl+K (issue #83)
        top.addSpacing(8)
        reload_button = QPushButton(self.t("reload"))
        reload_button.clicked.connect(self.reload)
        top.addWidget(reload_button)
        self.export_button = self.import_button_widget()
        top.addWidget(self.export_button)
        self.pdf_button = self.pdf_button_widget()
        top.addWidget(self.pdf_button)
        layout.addLayout(top)

        if self.read_only:
            if self.newer:
                banner = plain_label(self.t("read_only_newer_banner", version=self.newer, ours=project.VERSION), wrap=True)
            else:
                banner = plain_label(self.t("read_only_banner", user=self.holder.get("user", "?"), host=self.holder.get("host", "?")), wrap=True)
            banner.setProperty("callout", "danger")  # the site's callouts, in the style sheet (theme.py, v0.90)
            layout.addWidget(banner)

        # A project laid out as one report, whose migration into three documents the engineer put off or which could not go through: said once, with the one button that asks again (migrate_dialog.py).
        if self.migration_banner and not self.read_only and not project.current().has_folders:
            row = QHBoxLayout()
            note = plain_label(self.t("mg_folders_banner" if project.current().has_modes else "mg_banner"), wrap=True)   # a project in three documents is offered the layout by folders (issue #64)
            note.setProperty("callout", "info")
            row.addWidget(note, 1)
            button = QPushButton(self.t("mg_banner_button"))
            button.setToolTip(self.t("mg_banner_tip"))
            button.clicked.connect(self.ask_migration)
            row.addWidget(button)
            layout.addLayout(row)

        stale = self.stale_text()
        self.stale_banner = None
        if stale:
            banner = plain_label(stale, wrap=True)
            banner.setProperty("callout", "warning")
            layout.addWidget(banner)
            self.stale_banner = banner

        # A newer version of a dependency is an offer and never a warning: the report was verified with the versions pinned in requirements.txt, and updating is a decision with a rebuild behind it. So it sits in a quieter blue than the stale-data banner above, and carries the button rather than a modal.
        if self.dependency_updates:
            detail = ", ".join(
                self.t("deps_update_one", name=name, pinned=pinned, available=available)
                for name, pinned, available in self.dependency_updates
            )
            row = QHBoxLayout()
            note = plain_label(self.t("deps_update", detail=detail), wrap=True)
            note.setProperty("callout", "info")
            row.addWidget(note, 1)
            install = QPushButton(self.t("deps_update_button"))
            install.clicked.connect(self.install_updates)
            row.addWidget(install)
            layout.addLayout(row)
        typst_gui.add_banner(self, layout)   # a newer Typst than the pin, offered in the same blue (typst_gui.py, v0.94)

        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("modules")
        self.tab_widget.setIconSize(self.mark_size)  # the room every title keeps for its mark, whether it carries the dot or the blank
        # The row of tabs gave way to the side navigation (v0.91), and stays -- hidden -- underneath it: every module is still a tab of this widget, so a tab brought forward, its title and its mark are what they were.
        self.tab_widget.tabBar().hide()
        self.tabs = []
        self.stale_tabs = set()   # every tab is built now
        for number, (key, factory) in enumerate(TABS):
            woodcore_start.step("tabs", self.t(key), number / len(TABS))   # the start screen says which tab, its bar moving (v0.117); nothing where none is up
            tab = factory(self)
            self.tab_widget.addTab(tab, self.t(key))
            self.tabs.append(tab)
            busy.pump()   # building the twelve modules holds the main thread for seconds: the card's arc moves and Windows is answered between two of them (busy.py, v0.113)
        self.nav = self.nav_widget()
        self.update_tab_marks()
        self.apply_views()
        self.bind_layouts()
        self.notice_bar.refresh(blink=False)   # an information reported before the status bar was up said now
        self.tab_widget.setCurrentIndex(min(self.tab_index, len(self.tabs) - 1))
        self.shown_index = self.tab_widget.currentIndex()
        self.nav.set_current(self.tab_widget.currentIndex())
        self.sync_view_switch()
        self.tab_widget.currentChanged.connect(self.nav.set_current)
        self.nav.chosen.connect(self.tab_widget.setCurrentIndex)
        self.nav.modeChanged.connect(self.on_mode_changed)
        # A tab brought to the front: the one left saved first, then the switch given the views of the one shown, then the one shown looks again at what another tab may have changed on disk -- a schema renamed or redrawn in «Schémas» is seen in «Connecteurs» and «Moments polaires» without «Recharger». One slot and not three, for the order (review A07).
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        body = QHBoxLayout()
        body.setContentsMargins(0, 4, 0, 0)
        body.setSpacing(10)
        body.addWidget(self.nav)
        body.addWidget(self.tab_widget, 1)
        layout.addLayout(body, 1)
        self.setCentralWidget(main)
        self.shortcuts = []   # the ones the content a rebuild replaced carried went with it
        # The modules the document shown shows, and Ctrl+1 … Ctrl+9 for those the navigation lists (apply_mode) -- once the new content is the window's, which the shortcuts are made on.
        self.apply_mode()
        self.build_menu()
        self.update_title()

    def nav_widget(self):
        """The modules, grouped as the site's sidebar groups its pages (NAV_GROUPS), each with its icon; folded to its icons where the engineer folded it, which the settings keep (`nav_collapsed`)."""
        by_key = {key: index for index, (key, _factory) in enumerate(TABS)}
        groups, placed = [], set()
        for title_key, keys in NAV_GROUPS:
            entries = []
            for key in keys:
                if key not in by_key:
                    continue
                if key in NAV_SECTIONS:
                    entries.append((None, self.t(NAV_SECTIONS[key]) if NAV_SECTIONS[key] else "", None))   # a sub-title row (chrome.SideNav)
                entries.append((by_key[key], self.t(key), key))
            placed.update(key for key in keys if key in by_key)
            groups.append((self.t(title_key), entries))
        rest = [(index, self.t(key), key) for key, index in by_key.items() if key not in placed]
        if rest:   # a module no group names still has its row, under the last group
            groups[-1][1].extend(rest)
        # the drop-down of the three documents at its top, in a project written as three (documents.mode_choices) -- none in a project laid out as one report, which has only the report
        here = project.current()
        modes = documents.mode_choices(self.lang) if here.has_modes else None
        # its width as dragged on these screens (layout_store, v0.117) and its groups folded by a click on their titles (`nav_folded`, every screen alike)
        folded = self.settings.get("nav_folded") if isinstance(self.settings.get("nav_folded"), list) else []
        nav = chrome.SideNav(groups, collapsed=bool(self.settings.get("nav_collapsed")), collapse_tip=(self.t("nav_collapse"), self.t("nav_expand")),
                             modes=modes, mode=self.current_document(), mode_tip=self.t("nav_document"),
                             width=layout_store.get_value("nav_width"), folded=[t for t in folded if isinstance(t, str)])
        nav.collapsedChanged.connect(lambda collapsed: self.store(nav_collapsed=collapsed))
        nav.widthChanged.connect(lambda width: layout_store.put_value("nav_width", width))
        nav.foldedChanged.connect(lambda titles: self.store(nav_folded=list(titles)))
        return nav

    def bind_layouts(self):
        """Every tab's panes kept as they were dragged, by tab, by view and by the screens plugged in (layout_store, REQ-023): its splitter of left, centre and right panes, bound once the tab is built. A tab changing its view puts back that view's sizes (`view_changed`)."""
        self.layout_bindings = {}
        for (key, _factory), tab in zip(TABS, self.tabs):
            self.bind_layout(key, tab)

    def bind_layout(self, key, tab):
        """One tab's panes bound to the screens' layouts (bind_layouts), made again for a tab built again alone (refresh_tab) -- and its own left pane, the second from the left, given the arrow that folds it away and the floor every tab shares (`fold_left_pane`, issue #10)."""
        from PySide6.QtWidgets import QSplitter
        splitter = getattr(tab, "splitter", None)
        if isinstance(splitter, QSplitter):
            pane = self.fold_left_pane(key, splitter)
            self.layout_bindings[key] = layout_store.bind(splitter, lambda key=key, tab=tab: (key, str(getattr(tab, "view", None) or "-"), "panes"))
            if pane is not None and key in self.folded_left_panes():
                pane.set_folded(True)   # after the layout is put back, so the width it unfolds to is the one dragged

    def folded_left_panes(self):
        """The keys of the tabs whose left pane the engineer left folded (the setting `left_folded`, every screen alike, as `nav_folded`)."""
        found = self.settings.get("left_folded")
        return [key for key in found if isinstance(key, str)] if isinstance(found, list) else []

    def fold_left_pane(self, key, splitter):
        """`splitter`'s first pane -- the tab's list or tree -- inside a chrome.FoldablePane, unless the tab built it so already (the plan tabs, drawing_tab.build_list); its arrow's clicks kept in the settings. None for a splitter of fewer than two panes, which has no left pane to fold."""
        if splitter.count() < 2:
            return None
        pane = splitter.widget(0)
        if not isinstance(pane, chrome.FoldablePane):
            sizes = splitter.sizes()
            wrapped = chrome.FoldablePane(pane, (self.t("pane_collapse"), self.t("pane_expand")))   # the pane leaves the splitter for the wrapper here, the centre pane becoming its first...
            splitter.insertWidget(0, wrapped)   # ...until the wrapper takes the first place back -- never `replaceWidget(0, …)`, which would then replace the centre pane
            splitter.setSizes(sizes)
            pane = wrapped
        pane.foldedChanged.connect(lambda folded, key=key: self.remember_left_fold(key, folded))
        return pane

    def remember_left_fold(self, key, folded):
        keys = [k for k in self.folded_left_panes() if k != key] + ([key] if folded else [])
        self.store(left_folded=keys)

    def meta_text(self):
        """What stands beside the project's name: its number, and what the export holds and when it was written."""
        number = project.current().detail("number")
        parts = [self.t("meta_number", number=number)] if number else []
        info = self.info_text()
        if info:
            parts.append(info)
        return " · ".join(parts)

    def on_tab_shown(self, index):
        tab = self.tabs[index] if 0 <= index < len(self.tabs) else None
        if tab is not None and hasattr(tab, "on_shown"):
            tab.on_shown()

    def on_tab_changed(self, index):
        """Another tab in front: the one left keeps nothing unsaved that can be saved (`leave_tab`, the engineer's rule of 07.10.2026), the view switch shows the views of the one now shown, and that one looks again at the disk (`on_tab_shown`) -- in this order, so a tab reads what the one left has just written (review A07)."""
        if 0 <= index < len(self.tabs) and not self.available(TABS[index][0]):
            # a door other than the navigation -- an object opened, the palette -- to a tab whose document is not made yet: the «Projet» tab instead (issue #90)
            self.tab_widget.setCurrentIndex(self.project_index())
            return
        previous = getattr(self, "shown_index", None)
        self.shown_index = index
        if previous is not None and previous != index and 0 <= previous < len(self.tabs):
            self.leave_tab(self.tabs[previous], "tab")
            self.reset_view(self.tabs[previous])
        self.refresh_if_stale(index)
        self.sync_view_switch()
        self.on_tab_shown(index)

    # -- after a position saved: what is looked at is built again, the rest when it is looked at (v0.117) --

    def refresh_if_stale(self, index):
        """The tab at `index` built again where an export has replaced what it holds since it was built (`stale_tabs`): before it is seen, so that it never shows what the export no longer says."""
        if 0 <= index < len(TABS) and TABS[index][0] in self.stale_tabs:
            with busy.hold(self, self.t("busy_loading"), guard=False):
                self.refresh_tab(TABS[index][0])

    def refresh_tab(self, key):
        """One tab built again in its place, with what it kept through a rebuild -- its `view_state()` and its display's options, the very ones `rebuild` carries -- and nothing else of the window touched: its row in the navigation, the others' state, the unsaved marks."""
        from PySide6.QtCore import QSignalBlocker
        index = next(i for i, (k, _factory) in enumerate(TABS) if k == key)
        factory = TABS[index][1]
        old = self.tabs[index]
        self.stale_tabs.discard(key)
        state = old.view_state()
        self.views[key] = state
        display = old.display.snapshot() if getattr(old, "display", None) is not None else None
        with QSignalBlocker(self.tab_widget):
            current = self.tab_widget.currentIndex()
            self.tab_widget.removeTab(index)
            new = factory(self)
            self.tab_widget.insertTab(index, new, self.t(key))
            self.tab_widget.setCurrentIndex(current)
        self.tabs[index] = new
        old.deleteLater()
        if display is not None and getattr(new, "display", None) is not None:
            new.display.restore(display)
        if views.declared(new):
            kept = getattr(old, "view", None)
            new.set_view(kept if kept in views.declared(new) else views.default(new), enter=False)
        self.bind_layout(key, new)
        self.update_tab_marks()
        self.sync_view_switch()
        return new

    def refresh_lightly(self):
        """A position saved and the export that follows it done (the engineer, 08.10.2026: after a save «rafraîchir que les onglets qui les lisent», 12 to 15 s on the example project, two thirds of them the window built again on its own thread): the window's data read again, what stands beside the project's name, the banner of workbooks changed since the export taken off, and **every tab marked stale** but the Positions tab -- which holds what it has just written --, the one in front built again at once and each other when it is next shown (`refresh_if_stale`). No list of the tabs that read positions to keep in step with the code: a tab that reads them, or anything an export wrote, is rebuilt before it is seen, as a full rebuild would have built it, and the ones nobody looks at cost nothing. A tab that holds unsaved work keeps it through `view_state`, as through a rebuild."""
        self.load()
        self.meta.setText(self.meta_text())
        if self.stale_banner is not None:
            text = self.stale_text()
            self.stale_banner.setText(text)
            self.stale_banner.setVisible(bool(text))
        self.stale_tabs = {key for key, _factory in TABS if key != "tab_positions"}
        self.refresh_if_stale(self.tab_widget.currentIndex())
        self.export_button.setEnabled(True)
        self.pdf_button.setEnabled(True)

    def autosave_all(self, reason):
        """Every tab saves what it holds unsaved without a question, where it can (autosave.leave): before an export, another document, or when the window is left for another application."""
        for tab in getattr(self, "tabs", ()):
            autosave.leave(self, tab, reason)

    def on_application_state(self, state):
        """Woodcore left for another application: what can be saved is saved, nothing is asked. Not while a box of Woodcore's own is open, nor while the window is held (busy), nor in a project opened read-only."""
        if state != Qt.ApplicationState.ApplicationInactive or self.read_only or busy.held(self):
            return
        try:
            self.autosave_all("focus")
        except RuntimeError:
            pass   # a window being deleted: its widgets are gone

    def flush_autosave(self):
        """The saves put off while an export or a compilation ran, made now it has ended."""
        if self.autosave_pending and self.process is None:
            self.autosave_pending = False
            self.autosave_all("tab")

    def leave_tab(self, tab, reason):
        """What `tab` holds unsaved, saved without a question where it can be (autosave.py): the tab left, the view changed, the window left for another application."""
        autosave.leave(self, tab, reason)

    # -- the views of a tab (views.py, the engineer's request of 07.10.2026) --

    def tab_key(self, tab):
        for (key, _factory), candidate in zip(TABS, self.tabs):
            if candidate is tab:
                return key
        return None

    def apply_views(self):
        """Each tab that has views put in its first, or in the one it showed before a rebuild (`kept_views`, issue #86) -- a state set and nothing compiled (review A10): what a view compiles waits for the tab to be shown."""
        for (key, _factory), tab in zip(TABS, self.tabs):
            if views.declared(tab):
                kept = self.kept_views.get(key)
                tab.set_view(kept if kept in views.declared(tab) else views.default(tab), enter=False)

    def reset_view(self, tab):
        """`tab`, being left, put back in its first view as a state, its panes in that view's sizes (issue #86: «lorsque l'on ouvre un onglet, on est toujours en mode calcul et pas en mode affichage»). Done as the tab is left and not as it arrives: Qt shows the page before it says the tab changed, and a view put back then would come after its compilation. Not while a variable is chosen for that tab (`picking`): it waits in the view it asked from."""
        if self.picking:
            return
        for page in tab.findChildren(pdf_pane.ZoomablePdfView):
            page.fit()   # a page zoomed by Ctrl+wheel back to its pane's width once its tab is left (issue #89)
        first = views.default(tab)
        if first is None or getattr(tab, "view", None) == first:
            return
        tab.set_view(first, enter=False)
        binding = getattr(self, "layout_bindings", {}).get(self.tab_key(tab))
        if binding is not None:
            binding.restore()   # the first view's own sizes (layout_store)

    def sync_view_switch(self):
        """The switch given the views of the tab in front, the one it shows pressed; hidden for a tab without views."""
        switch = getattr(self, "view_switch", None)
        if switch is None or not getattr(self, "tabs", None):
            return
        index = self.tab_widget.currentIndex()
        tab = self.tabs[index] if 0 <= index < len(self.tabs) else None
        buttons = views.items(tab, self.t) if tab is not None else []
        switch.set_items(buttons, getattr(tab, "view", None))
        switch.setVisible(bool(buttons))

    def on_view_chosen(self, key):
        """The engineer chose another view of the tab in front: what it holds unsaved is saved first, as a tab left is, then the tab shows the view, which holds until the tab is left (issue #86)."""
        index = self.tab_widget.currentIndex()
        tab = self.tabs[index] if 0 <= index < len(self.tabs) else None
        if tab is None or key not in views.declared(tab) or key == getattr(tab, "view", None):
            return
        self.leave_tab(tab, "view")
        tab.set_view(key)
        self.view_changed(tab)

    # -- an object of the graph of dependencies opened where it is edited (issue #71, spec 2026-10-21-graphe-dependances, UI-001) --

    def open_object(self, node, file=None):
        """`node` (`check:ZT-01`, `section:rs/Sections/004-einwirkungen.typ`) opened where it is edited: a section in the editor, any other object in the tab that lists it -- the one whose `GRAPH_KIND` is its kind and which `lists_object` it --, the draft there left as every change of source leaves it (`open_object`). False where no tab lists it: a case read from a workbook, a document."""
        kind, ident = node.split(":", 1)
        if kind == "section":
            return bool(file) and open_in_editor(project.current().root / file)
        for tab in self.tabs:
            if getattr(tab, "GRAPH_KIND", None) == kind and tab.lists_object(ident):
                self.tab_widget.setCurrentWidget(tab)
                tab.open_object(ident)
                return True
        return False

    # -- a variable chosen in «Variables» for the «Formule» tab (v0.117, spec 2026-10-08-onglet-formule-domaines REQ-015, UI-007) --

    def begin_variable_pick(self, on_done, title, accept=None):
        """The «Variables» tab brought forward in its choosing mode, every other module unavailable -- the side navigation and Ctrl+1 … Ctrl+9 off -- until a variable is chosen or the choice given up; `on_done` then receives (source, domain, variable, its export address or None), or None, and the tab that asked is brought back. Asked by «Importer…» of the «Formule» tab and, since issue #42, by the button beside every field that may follow a variable (spec 2026-10-11-variables-liees-champs-et-textes, UI-001), which hands over `accept(var, domain)`, what that field may take. False where the «Variables» tab has no choosing mode, the tab then saying so."""
        tab = next((t for t in self.tabs if isinstance(t, variables_tab.VariablesTab)), None)
        begin = getattr(tab, "begin_pick", None)
        if tab is None or begin is None:
            return False
        back = self.tab_widget.currentIndex()   # the tab that asked, in front as it asks

        def done(key):
            self.picking = False
            self.nav.setEnabled(True)
            for shortcut in self.shortcuts:
                shortcut.setEnabled(True)
            chosen = None
            if key is not None:
                var = tab.variable(key)
                if var is not None:
                    address = tab.address(key) if hasattr(tab, "address") else None
                    chosen = (key[0], key[1], var, address)
            # the choice handed over BEFORE the tab that asked comes back: a tab that rebuilds its form as it is shown (the connectors') rebuilds it from a draft that already holds it, where the other way round the choice reached a field already replaced
            on_done(chosen)
            self.tab_widget.setCurrentIndex(back)

        self.leave_tab(self.tabs[back], "leave")
        self.picking = True
        self.tab_widget.setCurrentWidget(tab)
        self.nav.setEnabled(False)
        for shortcut in self.shortcuts:
            shortcut.setEnabled(False)
        if accept is None:
            begin(done, title)   # the «Formule» tab's call, as it always was
        else:
            begin(done, title, accept)
        return True

    def view_changed(self, tab):
        """`tab` shows another view -- chosen in the switch, or reached from inside the tab (a frame of a document opening its plan): the panes take that view's sizes and the switch follows where the tab is in front. Nothing is written: the view holds while the tab stays in front (issue #86; the user's settings kept it from v0.117 to 0.121)."""
        key = self.tab_key(tab)
        view = getattr(tab, "view", None)
        if key is None or view is None:
            return
        binding = getattr(self, "layout_bindings", {}).get(key)
        if binding is not None:
            binding.restore()   # the view's own sizes, on these screens (layout_store)
        if self.tabs and self.tab_widget.currentWidget() is tab:
            self.view_switch.set_current(view)

    def new_position(self, symbol=None, floor=None):
        """A new position opened in the «Positions» tab, brought forward -- how another tab asks for one (a schema element's panel; the plan's alert where the project has no position of a tool's letter, until the plan tab wrote a blank one itself, v0.114), reaching that tab through the window rather than importing it (v0.94). True where the draft was opened."""
        for tab in self.tabs:
            if hasattr(tab, "new_position"):
                return tab.new_position(symbol=symbol, floor=floor)
        return False

    def info_text(self):
        if self.data is None:
            return ""
        count = sum(len(i["vars"]) for d in self.data["domains"].values() for i in d["instances"].values())
        date = datetime.fromtimestamp(data_file().stat().st_mtime).strftime("%d.%m.%Y %H:%M")
        return self.t("loaded", count=count, date=date)

    # --- The three packages outside the standard library (docs/architecture/layout.md §11) -------
    # requirements.txt states the versions this report was verified with; these check the machine against that file and offer to put it right. Nothing installs without a yes.


    def rebuild(self):
        """Builds the window's content again -- after a language switch or a reload -- keeping the tab, and each tab's state: the loads' search, open rows and selection, the connection being edited with its unsaved changes."""
        self.tab_index = self.tab_widget.currentIndex()
        self.views = {key: tab.view_state() for (key, _factory), tab in zip(TABS, self.tabs)}
        self.kept_views = {key: tab.view for (key, _factory), tab in zip(TABS, self.tabs) if getattr(tab, "view", None)}
        # the options chosen in each tab's «Affichage» view survive the rebuild every export ends in (v0.117, the engineer: they were lost at each save): kept in memory, never in a file
        displays = {key: tab.display.snapshot() for (key, _factory), tab in zip(TABS, self.tabs) if getattr(tab, "display", None) is not None}
        # Seconds of widgets built on the main thread (5 s for the example project, measured on 03.10.2026): the window held with the card over it rather than frozen (busy.py, v0.113)
        with busy.hold(self, self.t("busy_loading"), guard=False):
            self.build()
        self.kept_views = {}
        self.show_zoom()   # «Zoom 120 %» in the language the window now speaks
        for (key, _factory), tab in zip(TABS, self.tabs):
            if key in displays and getattr(tab, "display", None) is not None:
                tab.display.restore(displays[key])


    # -- the File menu (docs/ui/window.md §10quater, v0.83) --
    # One project per process: another project opens in a process of its own, and this window closes itself the way closing always does -- asking for what is unsaved. «Nouveau projet» and «Ouvrir dans une nouvelle fenêtre» leave it open, as Word leaves the document it has open.


    def switch_to(self, args):
        """This window closed -- asking for what is unsaved, as closing always does -- and Woodcore started again with `args`. Nothing is started where the engineer chose to stay."""
        if self.busy() or not self.close():
            return False
        relaunch(args)
        return True


    def open_in_new_window(self):
        file = self.ask_project_file()
        if file:
            relaunch(["--project", file])

    def new_project(self):
        file = home_page.create_project(self, self.lang, project.current().root.parent)
        if file:
            relaunch(["--project", str(file)])


    # -- the import, and the export of the PDF (docs/ui/window.md §10quater) --


    # -- the documents compiled, one after the other, each only where its Typst changed since its PDF --


    def closeEvent(self, event):
        if self.process is not None:
            # killing the export would stop it in the middle of writing data/: the window closes as soon as it has finished instead
            self.close_requested = True
            self.set_status(self.t("close_after_compile" if self.compiling else "close_after_export"))
            event.ignore()
            return
        # a connection with unsaved changes is saved, discarded or kept open, as the engineer answers
        for tab in self.tabs:
            confirm = getattr(tab, "confirm_leave", None)
            if confirm is not None and not confirm():
                event.ignore()
                return
        geometry = self.normalGeometry() if self.normalGeometry().isValid() else self.geometry()
        self.store(size=f"{geometry.width()}x{geometry.height()}", lang=self.lang)
        if not self.read_only:
            project_lock.release(project.current())  # the project is free the moment this window is gone, not only when the process ends
        event.accept()


def translate_notice(key, lang):
    """A notice's word in `lang` from the window's glossary, or None -- what calc/notifications.py is configured with."""
    return STRINGS.get(lang if lang in STRINGS else "en", {}).get(key)


def open_in_editor(path, line=None, column=None):
    """`path` opened at `line` and `column` in VS Code -- its own Code.exe, never `code.cmd`, which would flash a console (vscode_executable) -- returning False where VS Code is not there, the caller then opening it with its own program."""
    code = vscode_executable()
    if code is None:
        return False
    where = ":".join(str(part) for part in (path, line, column) if part)
    return proc.start_detached(code, ["-g", where], str(Path(path).parent))


# --- Starting, and starting again (docs/ui/window.md §10quater, v0.83) --------------------

def relaunch_command(args):
    """Woodcore with `args`, as a program and its arguments: the installed Woodcore.exe, or woodcore_gui.py under the windowless interpreter from the sources."""
    if getattr(sys, "frozen", False):
        return sys.executable, list(args)
    exe = Path(sys.executable)
    windowless = exe.with_name("pythonw.exe")
    return str(windowless if windowless.is_file() else exe), [str(Path(__file__).resolve()), *args]


def relaunch(args):
    """Woodcore started again, in a process of its own, with `args` -- another project, or the start page."""
    program, arguments = relaunch_command(args)
    proc.start_detached(program, arguments, str(project.APP_ROOT))


# The windows this process shows, kept alive; and whether the stall watch is on, which one process installs once.
_WINDOWS = []
_WATCHING = []


def open_project(app, file, parent=None, quiet=False, migrate=False):
    """Opens project `file` in this process, which has none open yet: names it, asks when another window holds it (project_lock.py), offers a project laid out as one report its migration into three documents (migrate_dialog.py) -- `migrate`, the banner's «Migrer…», offers it again where the engineer had put it off -- builds the window and shows it. Returns the window, or None where the project could not be opened or the engineer chose not to. `quiet` -- `--self-test` -- asks nothing and says why on standard error: a check run with no one in front of it must not wait on a dialog."""
    settings = read_settings()
    lang = settings.get("lang") if settings.get("lang") in LANGUAGES else "fr"

    def fail(text):
        if quiet:
            print(text, file=sys.stderr)
        else:
            notices_ui.tell(text, notifications.CRITICAL, source="woodcore_gui")
        return None

    try:
        here = project.use(file)
    except project.ProjectError as exc:
        return fail(STRINGS[lang]["home_failed"].format(error=exc))
    holder = project_lock.acquire(here)
    read_only = False
    if holder is not None:
        if quiet:
            return fail(f"{here.file}: held by {holder.get('user')} on {holder.get('host')}")
        answer = home_page.ask_lock(parent, lang, here, holder)
        if answer is None:
            return None
        if answer == "force":
            project_lock.acquire(here, force=True)
        else:
            read_only = True
    newer = None
    if not read_only:
        # A project whose engine a newer Woodcore wrote is opened read-only (v0.87, the engineer's yes): this program would refuse to export into it, and a drawing saved from one of its tabs would still re-export its part of data/ with older code, beside an engine that reads it newer. Its lock is let go, a window that writes nothing holding nothing; the banner names the version that wrote it.
        state, detail = project.engine_state(here)
        if state == "newer":
            newer, read_only = detail, True
            project_lock.release(here)
    migration_banner = False
    if not read_only and not quiet and not here.has_folders:
        # A project laid out as one report, offered its migration into three documents (the engineer's request of 30.09.2026) -- after the lock, which the migration runs under (its `--lock-owner` is this process), and before anything is seeded, which the migration would move. «Plus tard» opens it as it is, the banner offering it again; a migration that went through is the project read again, in three documents.
        try:
            outcome = migrate_dialog.offer(parent, lang, here, forced=migrate)
        except Exception:  # broad: an offer that fails keeps no project from opening: it opens as it is, the banner offering it again
            traceback.print_exc()
            outcome = "failed"
        if outcome == "migrated":
            try:
                here = project.use(here.file)
            except project.ProjectError as exc:
                project_lock.release(here)
                return fail(STRINGS[lang]["home_failed"].format(error=exc))
        else:
            migration_banner = True
    positions_note = None
    if not read_only:
        # A project made before v0.114 kept its positions in Positionen.xlsx: they are imported once into Woodcore's own positions.json, and the workbook moved into the project's archives, never deleted (calc/positions_store.py) -- before the seed, which would otherwise write an index of no position. A workbook that cannot be read keeps no project from opening: the export says why, and the next opening tries again.
        try:
            import positions_store
            positions_note = positions_store.migrate(here)
        except Exception:  # broad: the export migrates too, and says what is wrong
            traceback.print_exc()
    if not read_only:
        # The report commands renamed in v0.120 -- the thirteen `*-ids` now `ids(kind)`, the eight `get-*` now `get(v, field)`, `show-line-load-summary` now `show-load-summary(unit:)` -- rewritten in the project's sections once, each file saved first into the archives (calc/domains/commands_migrate.py, spec 2026-10-19-base-saine-nettoyage, D-13).
        try:
            from domains import commands_migrate
            for change in commands_migrate.migrate(here):
                print(f"woodcore: {here.rel(change.path)} migrated: " + "; ".join(change.notes))
            # what was taken away is never rewritten: said here, at its file and line, and refused by the export (spec 2026-10-21-commandes-typst-refonte, REQ-020)
            import notices_ui
            notices_ui.tell_removed_commands(commands_migrate.removals(here), here)
            notices_ui.tell_unscoped_units(commands_migrate.unit_scope_notes(here), here)   # a #unit written before its scope: existed (CON-007)
        except Exception:  # broad: a file the migration could not rewrite is left as it was, and the export names it
            traceback.print_exc()
        # The values of the snow and wind sheets renamed in v0.120, the sheets being computed by Woodcore -- `q_k11` of a flat roof now `q_k1`, `qk_max_bh` now `qk_max_cf1` -- rewritten in the project's sections, scripts and sources once, each file saved first into the archives (calc/domains/loads_migrate.py, spec 2026-10-21-restes-issue-69, D-06). What cannot be rewritten safely is left, and the export names it.
        try:
            from domains import loads_migrate
            for change in loads_migrate.migrate(here):
                print(f"woodcore: {here.rel(change.path)} migrated: " + "; ".join(change.notes))
        except Exception:  # broad: a file the migration could not rewrite is left as it was, and the export names it
            traceback.print_exc()
    if not read_only:
        # A project whose data/ lacks a file its report reads -- one «Nouveau projet» made before v0.86.1 wrote them -- gets it, empty, so its report compiles in Tinymist before its first export (export_all.seed); a file already there is never touched, and a failure here keeps no project from opening.
        try:
            import export_all
            export_all.seed(here)
        except Exception:  # broad: a convenience: the export writes the same files, and says what is wrong
            traceback.print_exc()
    write_settings(usersettings.remember(read_settings(), here.file))   # what the start page and «Récents» list, the last first
    # Building the window holds the main thread for seconds (8.6 s for the example project, measured on 03.10.2026): the start page held with the card over it -- or, a project double-clicked, a card of its own -- its arc turned between two modules (busy.py, v0.113)
    splash = None
    opening = STRINGS[lang]["busy_opening"].format(name=here.name)
    if parent is not None:
        busy.start(parent, opening, guard=False)   # the window built on the main thread: input waits in the queue (busy.py)
    elif woodcore_start.current() is not None:
        woodcore_start.step("project", here.name)   # the start screen is up: it says what is opened, no second card
    else:
        splash = busy.Splash(opening)
    try:
        window = MainWindow(read_only=read_only, holder=holder if read_only else None, newer=newer, migration_banner=migration_banner)
    except Exception:  # broad: started from the .bat there is no console, so a crash must say so in a window of its own
        busy.stop(splash or parent)
        if splash is not None:
            splash.close()
        if not read_only:
            project_lock.release(here)
        return fail(STRINGS[lang]["startup_error"].format(error=traceback.format_exc()))
    busy.stop(splash or parent)
    if splash is not None:
        splash.close()
        splash.deleteLater()
    if not read_only:
        atexit.register(project_lock.release, here)   # a window killed rather than closed still frees its project
    claim_taskbar_icon(window)
    window.show()
    woodcore_start.done()   # the window up: the start screen goes, its steps' times kept as the next start's weights
    if positions_note is not None:
        window.set_status(note_text(positions_note, lang))   # the positions taken over from Positionen.xlsx, said once
    # A key of the project file that names a feature Woodcore no longer has (the RFEM import, retired in 0.117): a warning among the notices as the project opens, as at every export -- the file is the engineer's and is not rewritten (project.RETIRED_KEYS)
    for note in here.retired_keys():
        notifications.report_note(note, source="project")
    _WINDOWS.append(window)
    # Once the window is up, so building it is not taken for a stall: from here a pause of the event loop longer than stallwatch.STALL_S writes where it was to %LOCALAPPDATA%\Woodcore\stalls.log.
    if not _WATCHING:
        stallwatch.install(app)
        _WATCHING.append(True)
    # After show(), so the window is on screen before anything is asked of the network or of pip -- and never before, since a modal owned by a window that is not up yet has nowhere to sit. The project's engine first (v0.87): it is about the project just opened, the packages about the machine. A project opened read-only is asked nothing about its engine (check_engine says so itself).
    if not quiet:
        QTimer.singleShot(0, window.check_engine)
        QTimer.singleShot(0, window.check_dependencies)
        QTimer.singleShot(0, functools.partial(typst_gui.check_at_start, window))   # the Typst found against the pin, then GitHub in a thread -- from the sources only (typst_gui.py, v0.94)
    return window


def show_home(app):
    """The start page (home_page.py): a project chosen there opens in this process, and the page closes."""
    page = home_page.HomeWindow(lambda file: open_project(app, file, parent=page) is not None, icon=str(ICON_FILE))
    claim_taskbar_icon(page)
    page.show()
    woodcore_start.done()
    _WINDOWS.append(page)
    return page


def main(app=None, argv=None, watching=False):
    """`--project <file>` opens that project; `--home` the start page whatever else names a project; without either, `WOODCORE_PROJECT`'s project where it names one, else the start page. `--migrate` offers a project laid out as one report its migration into three documents even where the engineer had put it off -- what the window's banner starts Woodcore again with. `--self-test` opens what it is asked to and quits after a second and a half, 1 where the project did not open -- what the build checks an installed Woodcore with (packaging/build.py)."""
    argv = list(sys.argv if argv is None else argv)
    usersettings.migrate()   # the settings and caches of the Typst-Katalog, as the window was named until v0.83, taken over once
    # Every notice in the window's words, and in %LOCALAPPDATA%\Woodcore\woodcore.log -- configured here and never at import, so a test writes no log; an exception nobody caught becomes a critical notice from now on, not a message box (notices_ui.install_hooks, v0.117).
    notifications.configure(translate=translate_notice, log=None if watching else usersettings.cache_dir("woodcore.log"))   # started by woodcore_start: the log is open since its screen
    notices_ui.install_hooks()
    woodcore_start.set_app_id()   # before any window exists (APP_ID); done already where woodcore_start.main came first
    try:
        named, rest = project.take_argument(argv[1:])
    except project.ProjectError:
        named, rest = None, argv[1:]
    home = "--home" in rest
    self_test = "--self-test" in rest
    migrate = "--migrate" in rest
    rest = [arg for arg in rest if arg not in ("--home", "--self-test", "--migrate")]
    if app is None:
        app = QApplication([argv[0], *rest])
        theme.apply(app)  # before any window too, the lock's question included: the site's look, light or dark (theme.py, v0.90)
    app.setApplicationName("Woodcore")
    app.setWindowIcon(QIcon(str(ICON_FILE)))  # every window of the process: this one and its message boxes
    nowheel.install(app)  # before any window: the wheel scrolls and zooms, it never retypes a field (nowheel.py)
    if watching:
        _WATCHING.append(True)   # the stall watch was installed with the start screen (woodcore_start.py)
    target = named or (None if home else os.environ.get(project.ENV))
    window = open_project(app, target, quiet=self_test, migrate=migrate) if target else None
    if window is None:
        if self_test and target:
            sys.exit(1)
        show_home(app)
    if self_test:
        QTimer.singleShot(1500, app.quit)
    else:
        # An installed Woodcore asks its website whether a newer version is published, in a thread, once the first window is up; a window says so once per version (update_gui.py, v0.89). A checkout and a test run ask nothing (updates.enabled).
        import update_gui
        update_gui.schedule(app)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
