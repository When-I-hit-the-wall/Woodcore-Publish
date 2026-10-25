# -*- coding: utf-8 -*-
"""Woodcore's first second: a window of its own before anything heavy is imported, and what it says while the rest loads (spec docs/requirements/completed/2026-10-07-performance-erreurs-plans-legendes.md, REQ-002, REQ-003, REQ-004; docs/ui/window.md §10quater).

The engineer, 07.10.2026: «Le fait que le lancement de Woodcore puisse prendre un certain temps ne me dérange pas. Ce qui me dérange est que Windows donne actuellement l'impression que Woodcore est bloqué … Afficher immédiatement une image / un écran de démarrage Woodcore … apparaître avant les opérations lourdes … Woodcore doit également apparaître correctement dans la barre des tâches» · «Une progression réelle … avec une indication de ce qui est actuellement chargé» · «ne jamais afficher une application complètement figée avec uniquement le curseur Windows qui tourne».

Measured before (docs/architecture/performance.md, 08.10.2026): nothing on screen for 4-5 s after a double-click warm, 30 s at the first start of a day -- `import woodcore_gui` alone, before its card could appear. Hence this module, which imports only PySide6's three modules, the theme and the user's settings, and is what every way of starting the window goes through: `Woodcore.exe` (packaging/entry_gui.py), `Woodcore.bat`, `woodcore_gui.py` run directly (it hands over to `main()` here before its own imports), and Woodcore started again (`woodcore_gui.relaunch_command`).

**The order** (`main()`):

1. The taskbar's identity (APP_ID) and `QApplication`, the theme, then the screen (`StartScreen`): a normal top-level window -- never `Qt.Tool`, which has no button on the taskbar --, frameless, its icon claimed for the taskbar (`claim_taskbar_icon`).
2. The libraries and the calculation modules that touch no Qt -- openpyxl and numpy (4-5 s warm, 15 s cold), pypdf, the norms, the domains, the export --, imported **in a thread** while the screen turns on the main thread (`IMPORTS`). An import is the same object whichever thread made it: the main thread importing them again later only finds them done.
3. The window's own modules, which define Qt classes, imported **on the main thread** one after the other, the screen painted between two (`WINDOW_MODULES`).
4. `woodcore_gui.main(app)`, which opens the project and builds its window, its tabs one after the other with the screen saying which (`step`); the screen closes once the window is shown -- or the start page, where no project was named.

**The progress is real**: each step weighs what it took the last time, measured on this machine and kept in `%LOCALAPPDATA%\\Woodcore\\start-weights.json` (a cache: absent or unreadable, the default weights below); the bar moves by the weight of each step done and, inside a long step -- the tabs --, by the fraction its caller says.

Nothing here knows the project, the calculation or the window's glossary: it imports none of them before the screen is up.
"""

import importlib
import json
import os
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget

ICON_FILE = Path(__file__).with_name("woodcore.svg")
# The taskbar files a window under its process's AppUserModelID; without one of its own this window would be filed under pythonw.exe, and show Python's icon instead of ICON_FILE.
APP_ID = "Woodcore.App"

# The steps, in order: their key, and their weight where nothing was measured yet (seconds, warm, the example project, 08.10.2026).
STEPS = (
    ("config", 0.2),       # the settings, the theme
    ("libraries", 4.0),    # openpyxl, numpy, pypdf -- in a thread
    ("calc", 2.0),         # the norms, the domains, the export -- in a thread
    ("typst", 0.5),        # Typst's check and the engine's
    ("window", 2.5),       # the window's own modules -- on the main thread
    ("project", 0.8),      # the project opened: its lock, its migrations, its data
    ("tabs", 8.0),         # the window built, tab after tab
)
# What the thread imports: no Qt, nothing that creates a window. Each a module name as calc/ and calc/tools/ are on the path.
IMPORTS = {
    "libraries": ("numpy", "openpyxl", "openpyxl.workbook", "openpyxl.writer.excel", "openpyxl.packaging.extended", "pypdf"),   # packaging.extended: what saving a workbook imports, as the «Projet» tab's preview makes a project (issue #88)
    "calc": ("project", "engine", "validation", "norms", "registry", "positions_store", "export_all", "build_reference",
             "domains.plan", "domains.plan_svg", "domains.fire", "domains.statics", "domains.schema", "domains.connector",
             "domains.member_check", "notifications", "typst_diagnostics"),
    "typst": ("typst_check", "updates"),
}
# The window's own modules, imported on the main thread in this order -- the heaviest first, woodcore_gui last, which then finds them done.
WINDOW_MODULES = ("cards", "chrome", "busy", "grouped_list", "plan_canvas", "document_view", "sheet_editor", "drawing_tab", "plan_tab", "fire_tab",
                  "connectors_tab", "schema_tab", "statics_tab", "member_check_tab", "positions_tab", "structure_tab", "display_view",
                  "home_page", "woodcore_gui")
WEIGHTS_FILE = "start-weights.json"
WEIGHTS_SCHEMA = "1.0"
FRAME_MS = 16
SCREEN_SIZE = QSize(520, 312)

STRINGS = {
    "fr": {"start_title": "Chargement de Woodcore…", "start_config": "Configuration", "start_libraries": "Bibliothèques",
           "start_calc": "Modules de calcul", "start_typst": "Moteur Typst", "start_window": "Interface",
           "start_project": "Chargement du projet", "start_tabs": "Construction des onglets", "start_home": "Page d'accueil"},
    "de": {"start_title": "Woodcore wird geladen…", "start_config": "Konfiguration", "start_libraries": "Bibliotheken",
           "start_calc": "Berechnungsmodule", "start_typst": "Typst-Engine", "start_window": "Oberfläche",
           "start_project": "Projekt wird geladen", "start_tabs": "Register werden aufgebaut", "start_home": "Startseite"},
    "en": {"start_title": "Loading Woodcore…", "start_config": "Configuration", "start_libraries": "Libraries",
           "start_calc": "Calculation modules", "start_typst": "Typst engine", "start_window": "Interface",
           "start_project": "Loading the project", "start_tabs": "Building the tabs", "start_home": "Start page"},
}

_screen = []   # the screen up, if any: what `step()` and `done()` speak to


def set_app_id():
    """The process's AppUserModelID, before any window exists: its windows filed under Woodcore on the taskbar, with ICON_FILE."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except (AttributeError, OSError):
        pass  # the window still opens, filed under Python on the taskbar


def claim_taskbar_icon(window):
    """Hands the window's icons to its window class as well, before it is shown -- the class's icon being Windows' generic one otherwise, as Qt leaves it. The AppUserModelID alone is not enough: launched in turn with and without this, the taskbar button came up generic every time without it and with ICON_FILE every time with it -- the taskbar asks the window for its icon as the button appears, the window is still busy laying itself out right then, and past a short wait the taskbar takes the class's icon instead."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.WinDLL("user32")  # an instance of our own, so the signatures set here touch no one else's
        user32.SendMessageW.restype = ctypes.c_ssize_t
        user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.SetClassLongPtrW.restype = ctypes.c_size_t
        user32.SetClassLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
        hwnd = int(window.winId())  # creates the native window, Qt giving it the application's icons on the way
        for which, slot in ((1, -14), (0, -34)):  # WM_GETICON's ICON_BIG and ICON_SMALL into GCLP_HICON and GCLP_HICONSM
            icon = user32.SendMessageW(hwnd, 0x7F, which, 0)
            if icon:
                user32.SetClassLongPtrW(hwnd, slot, icon)
    except (AttributeError, OSError):
        pass  # the title bar keeps its icon either way


def _weights_path():
    import usersettings
    return usersettings.cache_dir(WEIGHTS_FILE)


def read_weights():
    """The weight of each step, as measured at the last start on this machine, else STEPS' own; a cache, so anything wrong with it is no cache."""
    weights = dict(STEPS)
    try:
        data = json.loads(_weights_path().read_text(encoding="utf-8"))
        if str(data.get("schema_version", "")).split(".")[0] == WEIGHTS_SCHEMA.split(".")[0]:
            for key, value in data.get("seconds", {}).items():
                if key in weights and isinstance(value, (int, float)) and 0 < value < 600:
                    weights[key] = float(value)
    except (OSError, ValueError, AttributeError):
        pass
    return weights


def write_weights(seconds):
    try:
        path = _weights_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"schema_version": WEIGHTS_SCHEMA, "seconds": {k: round(v, 3) for k, v in seconds.items()}}, indent=1), encoding="utf-8", newline="\n")
    except OSError:
        pass


def _language():
    try:
        import usersettings
        lang = usersettings.read().get("lang")
    except Exception:  # broad: settings unreadable are the window's to say; the screen speaks French
        lang = None
    return lang if lang in STRINGS else "fr"


class StartScreen(QWidget):
    """The start screen: Woodcore's mark and name, a bar from 0 to 100 % and the list of the steps -- ✓ done, → under way, ○ to come -- with what the step under way is doing. Painted, never laid out: nothing in it costs a style sheet's polish. A normal top-level window, frameless, on the taskbar."""

    def __init__(self, lang):
        super().__init__(None, Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle("Woodcore")
        self.setWindowIcon(QIcon(str(ICON_FILE)))
        self.lang = lang
        self.words = STRINGS[lang]
        self.weights = read_weights()
        self.total = sum(self.weights.values())
        self.current = None
        self.done_steps = []
        self.fraction = 0.0      # inside the step under way
        self.detail = ""
        self.version = ""
        self.started = time.monotonic()
        self.step_started = self.started
        self.seconds = {}
        self.icon = QIcon(str(ICON_FILE))
        self.resize(SCREEN_SIZE)
        screen = QApplication.primaryScreen()
        if screen is not None:
            area = screen.availableGeometry()
            self.move(area.center().x() - self.width() // 2, area.center().y() - self.height() // 2)
        self.timer = QTimer(self)
        self.timer.setInterval(FRAME_MS)
        self.timer.timeout.connect(self._frame)
        self.timer.start()
        self.last_frame = time.monotonic()
        self.longest = 0.0   # the longest the screen went without a frame: what «never frozen» is measured by (WOODCORE_START_TRACE)
        self.longest_at = ""

    def _frame(self):
        now = time.monotonic()
        said = f"{self.current}: {self.detail}" if self.detail else str(self.current)
        if now - self.last_frame > self.longest:   # and between which two things the screen said it happened: what a measurement needs to find its cause
            self.longest, self.longest_at = now - self.last_frame, f"{getattr(self, 'said', '')} -> {said}"
        self.said = said
        self.last_frame = now
        self.update()

    # -- progress --

    def step(self, key, detail="", fraction=None):
        """`key` under way -- the steps before it done --, saying `detail`; `fraction` how far inside it."""
        now = time.monotonic()
        if key != self.current:
            if self.current is not None:
                self.seconds[self.current] = self.seconds.get(self.current, 0.0) + now - self.step_started
                if self.current not in self.done_steps:
                    self.done_steps.append(self.current)
            self.current = key
            self.step_started = now
            self.fraction = 0.0
        self.detail = detail or ""
        if fraction is not None:
            self.fraction = max(0.0, min(1.0, float(fraction)))
        self.update()

    def progress(self):
        """How far the start is, 0 to 1: the weights of the steps done, and the fraction of the one under way."""
        if not self.total:
            return 0.0
        done = sum(self.weights.get(k, 0.0) for k in self.done_steps)
        if self.current is not None and self.current not in self.done_steps:
            done += self.weights.get(self.current, 0.0) * self.fraction
        return min(1.0, done / self.total)

    def finish(self):
        """The last step done, the measured seconds kept as the next start's weights."""
        if self.current is not None:
            self.seconds[self.current] = self.seconds.get(self.current, 0.0) + time.monotonic() - self.step_started
        measured = dict(self.weights)
        measured.update(self.seconds)
        write_weights(measured)
        self.timer.stop()

    # -- painting --

    def paintEvent(self, _event):
        import theme
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        card = QRectF(self.rect()).adjusted(6, 6, -6, -6)
        painter.setPen(QPen(QColor(theme.colour("line-strong")), 1))
        painter.setBrush(QColor(theme.colour("card")))
        painter.drawRoundedRect(card, 12, 12)
        # the mark and the name
        self.icon.paint(painter, int(card.left() + 26), int(card.top() + 24), 52, 52)
        title = QFont(self.font())
        title.setPointSizeF(max(title.pointSizeF(), 9) * 1.9)
        title.setWeight(QFont.Weight.DemiBold)
        painter.setFont(title)
        painter.setPen(QColor(theme.colour("ink")))
        painter.drawText(QRectF(card.left() + 92, card.top() + 22, card.width() - 110, 34), Qt.AlignmentFlag.AlignVCenter, "Woodcore")
        small = QFont(self.font())
        painter.setFont(small)
        painter.setPen(QColor(theme.colour("muted")))
        painter.drawText(QRectF(card.left() + 92, card.top() + 54, card.width() - 110, 20), Qt.AlignmentFlag.AlignVCenter,
                         self.words["start_title"] + (f"   v{self.version}" if self.version else ""))
        # the bar: the progress, with a light running over it so it moves even inside a long step
        bar = QRectF(card.left() + 26, card.top() + 96, card.width() - 52, 6)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(theme.colour("line")))
        painter.drawRoundedRect(bar, 3, 3)
        filled = QRectF(bar.left(), bar.top(), max(6.0, bar.width() * self.progress()), bar.height())
        painter.setBrush(QColor(theme.colour("accent")))
        painter.drawRoundedRect(filled, 3, 3)
        phase = ((time.monotonic() - self.started) % 1.4) / 1.4
        glow = QRectF(filled.left() + (filled.width() - 40) * phase, bar.top(), 40, bar.height())
        painter.setBrush(theme.qcolor("paper", 90))
        painter.drawRoundedRect(glow.intersected(filled), 3, 3)
        painter.setPen(QColor(theme.colour("muted")))
        painter.drawText(QRectF(bar.left(), bar.bottom() + 4, bar.width(), 18), Qt.AlignmentFlag.AlignRight, f"{round(self.progress() * 100)} %")
        # the steps
        metrics = QFontMetrics(small)
        y = bar.bottom() + 26
        for key, _weight in STEPS:
            if key in self.done_steps:
                mark, colour = "✓", theme.colour("ok")
            elif key == self.current:
                mark, colour = "→", theme.colour("accent")
            else:
                mark, colour = "○", theme.colour("muted")
            painter.setPen(QColor(colour))
            painter.drawText(QRectF(bar.left(), y, 18, metrics.height()), Qt.AlignmentFlag.AlignLeft, mark)
            painter.setPen(QColor(theme.colour("ink") if key == self.current else theme.colour("ink-soft") if key in self.done_steps else theme.colour("muted")))
            text = self.words[f"start_{key}"]
            if key == self.current and self.detail:
                text += " — " + self.detail
            painter.drawText(QRectF(bar.left() + 20, y, bar.width() - 20, metrics.height()), Qt.AlignmentFlag.AlignLeft,
                             metrics.elidedText(text, Qt.TextElideMode.ElideRight, int(bar.width() - 20)))
            y += metrics.height() + 4
        painter.end()


# --- what the window's start says to the screen -----------------------------------------------------

def current():
    """The start screen up, or None (a window opened from the start page, a test)."""
    return _screen[0] if _screen else None


def step(key, detail="", fraction=None):
    """The start screen told what is under way -- nothing where there is none -- and painted at once, the event loop turned without the user's input (busy.pump's own rule)."""
    screen = current()
    if screen is None:
        return
    screen.step(key, detail, fraction)
    _pump()


def done():
    """The start over: the weights kept, the screen closed."""
    screen = current()
    if screen is None:
        return
    _screen.clear()
    screen.finish()
    if os.environ.get("WOODCORE_START_TRACE"):
        print(f"woodcore_start: longest without a frame {screen.longest:.3f} s ({screen.longest_at}); steps {', '.join(f'{k} {v:.2f} s' for k, v in screen.seconds.items())}", file=sys.stderr, flush=True)
    screen.close()
    screen.deleteLater()


_last_pump = [0.0]


def pump():
    """Inside a long piece of building on the main thread, between two of its parts: the start screen painted, where one is up -- nothing otherwise, and never the user's input."""
    if _screen:
        _pump()


def _pump(force=False):
    from PySide6.QtCore import QEventLoop
    now = time.monotonic()
    if not force and now - _last_pump[0] < 0.02:
        return
    _last_pump[0] = now
    app = QApplication.instance()
    if app is not None:
        app.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)


def _import_in_thread(names):
    """`names` imported in a thread of their own while the screen turns; the main thread waits for it in an event loop, so Windows sees a window that answers. An import that fails is left for the main thread to meet again, where it says why."""
    from PySide6.QtCore import QEventLoop
    finished = threading.Event()

    def work():
        for name in names:
            try:
                importlib.import_module(name)
            except Exception:  # broad: met again on the main thread, which says why
                pass
        finished.set()

    threading.Thread(target=work, name="woodcore-start-imports", daemon=True).start()
    app = QApplication.instance()
    while not finished.wait(0.015):
        app.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)


def main(argv=None):
    """Woodcore started: the screen first, then everything else (the module's docstring), then `woodcore_gui.main`."""
    started = time.perf_counter()
    for path in (str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parent.parent)):
        if path not in sys.path:
            sys.path.insert(0, path)
    set_app_id()
    argv = list(sys.argv if argv is None else argv)
    app = QApplication.instance() or QApplication([argv[0], *[a for a in argv[1:] if a.startswith("-") and a not in ("--project", "--home", "--self-test", "--migrate")]])
    app.setApplicationName("Woodcore")
    app.setWindowIcon(QIcon(str(ICON_FILE)))
    import theme
    theme.apply(app)
    screen = StartScreen(_language())
    claim_taskbar_icon(screen)
    screen.show()
    _screen[:] = [screen]
    screen.step("config")
    _pump(force=True)
    if os.environ.get("WOODCORE_START_TRACE"):
        print(f"woodcore_start: screen shown {time.perf_counter() - started:.3f} s after main()", file=sys.stderr, flush=True)
    # an exception nobody caught is a critical notice from the screen on, and the log written from here -- under pythonw one raised while the start imports would otherwise say nothing (verification of 08.10.2026); the window's bar shows what was kept
    import notifications
    import notices_ui
    import usersettings
    notifications.configure(log=usersettings.cache_dir("woodcore.log"))
    notices_ui.install_hooks()
    import stallwatch
    stall = os.environ.get("WOODCORE_STALL_S")   # a measurement's own threshold (docs/architecture/performance.md); 1.5 s otherwise
    stallwatch.install(app, stall_s=float(stall) if stall else None)   # from the screen on, so a stall of the start is written down too (it was installed once the window was up)
    for key in ("libraries", "calc", "typst"):
        screen.step(key)
        _import_in_thread(IMPORTS[key])
    import project
    screen.version = project.VERSION
    screen.step("window")
    for number, name in enumerate(WINDOW_MODULES):
        step("window", name, number / len(WINDOW_MODULES))
        importlib.import_module(name)
    import woodcore_gui
    woodcore_gui.main(app=app, argv=argv, watching=True)
