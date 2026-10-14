"""No console window flashes open when Woodcore starts a child process (calc/proc.py, docs/ui/window.md §10quater; the engineer's report of 01.10.2026: «je vois une fenêtre de terminal s'ouvrir une fraction de seconde, très souvent lors de la compilation Typst»).

Woodcore's window is a process with **no console** (`pythonw.exe`, or the frozen windowless `Woodcore.exe`). A console program it starts -- `typst.exe`, `python.exe`, `git`, `winget`, `woodcore-cli.exe` -- with nothing said gets a console of its own, and Windows opens a window for it that closes when the program ends. `CREATE_NO_WINDOW` is what prevents it, and it has to be on every start, so what is held here is two things:

⚠️ **The sources are read, and a start that does not go through `calc/proc.py` is refused**: `subprocess.run`, `Popen`, `call`, `check_call`, `check_output`, `os.system` and `os.popen` (and the rest of that family), `QProcess(...)` and `QProcess.startDetached`/`execute`, found by walking the syntax tree of every module of `calc/` -- a docstring that merely names one is not a start. A deliberate exception carries a `# console-ok: <why>` comment on its line or the line above it; there is none today. `packaging/` and `website/` are not read: their build scripts run in the engineer's terminal and write their progress to it, which is what hiding their console would take away (calc/proc.py says so).

⚠️ **The mechanism is run for real**, from a `pythonw.exe` that has no console, which is the one place the defect shows: a child of a plain `subprocess.run` has a console window (`GetConsoleWindow()` is a handle) and the child of `proc.run`, `proc.popen` and `proc.qprocess` has none. PySide6 6.11 does not expose `QProcess.setCreateProcessArgumentsModifier`, so a QProcess cannot be handed the flag; it needs none, Qt itself starting a child with `CREATE_NO_WINDOW` when its own process has no console -- and this is the check that says so, so that a Qt that stops doing it is caught here and not by the engineer.
"""

import ast
import json
import subprocess
import sys
import types
from pathlib import Path

import conftest
from conftest import CALC

import proc

# What starts a child process, by module. `os.startfile` is not here: it opens a document in its application, which is a window of its own (an installer, a PDF) and has no console to hide.
SUBPROCESS_STARTS = {"run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput"}
OS_STARTS = {"system", "popen"}
OS_PREFIXES = ("spawn", "exec")
QT_STARTS = {"startDetached", "execute"}
MARKER = "console-ok"


def _os_start(name):
    return name in OS_STARTS or name.startswith(OS_PREFIXES)


def console_starts(source):
    """[(line, what), ...]: every child-process start `source` makes outside `calc/proc.py`, except where a `# console-ok:` comment on the line or the one above says it is deliberate."""
    tree = ast.parse(source)
    lines = source.splitlines()
    subprocess_names, os_names = {"subprocess"}, {"os"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "subprocess":
                    subprocess_names.add(alias.asname or alias.name)
                elif alias.name == "os":
                    os_names.add(alias.asname or alias.name)
    found = []
    for node in ast.walk(tree):
        what = None
        if isinstance(node, ast.ImportFrom):
            names = [alias.name for alias in node.names]
            if node.module == "subprocess":
                what = next((f"from subprocess import {n}" for n in names if n in SUBPROCESS_STARTS), None)
            elif node.module == "os":
                what = next((f"from os import {n}" for n in names if _os_start(n)), None)
            elif node.module == "asyncio":
                what = next((f"from asyncio import {n}" for n in names if n.startswith("create_subprocess")), None)
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            base, attr = node.value.id, node.attr
            if base in subprocess_names and attr in SUBPROCESS_STARTS:
                what = f"subprocess.{attr}"
            elif base in os_names and _os_start(attr):
                what = f"os.{attr}"
            elif base == "QProcess" and attr in QT_STARTS:
                what = f"QProcess.{attr}"
            elif base == "asyncio" and attr.startswith("create_subprocess"):
                what = f"asyncio.{attr}"
        elif isinstance(node, ast.Call):
            func = node.func
            if (isinstance(func, ast.Name) and func.id == "QProcess") or (isinstance(func, ast.Attribute) and func.attr == "QProcess"):
                what = "QProcess(...)"
        if what is not None:
            nearby = lines[max(node.lineno - 2, 0):node.lineno]
            if not any(MARKER in line for line in nearby):
                found.append((node.lineno, what))
    return sorted(set(found))


def _modules():
    return sorted(p for p in CALC.rglob("*.py") if "__pycache__" not in p.parts and p != CALC / "proc.py")


def test_every_child_process_of_calc_is_started_through_proc():
    """No module of calc/ starts a child process of its own: each goes through `proc.run`, `proc.popen`, `proc.qprocess` or `proc.start_detached`, which is where `CREATE_NO_WINDOW` is added."""
    assert _modules(), "no module of calc/ was found"
    bad = []
    for path in _modules():
        for line, what in console_starts(path.read_text(encoding="utf-8")):
            bad.append(f"{path.relative_to(CALC.parent).as_posix()}:{line}  {what}")
    assert not bad, "a child process started without going through calc/proc.py (a console window flashes open under pythonw.exe):\n  " + "\n  ".join(bad)


def test_the_scan_catches_what_it_is_there_to_catch():
    """The check above would pass if the walk saw nothing, so each shape of start is planted and must be found -- and what is not a start must not be."""
    planted = {
        "import subprocess\nsubprocess.run(['typst'])\n": ["subprocess.run"],
        "import subprocess\nsubprocess.Popen(['typst'])\n": ["subprocess.Popen"],
        "import subprocess\ndef installed(run=subprocess.run):\n    pass\n": ["subprocess.run"],      # a reference is the start waiting to happen
        "import subprocess as sp\nsp.check_output(['git'])\n": ["subprocess.check_output"],
        "from subprocess import run\n": ["from subprocess import run"],
        "import os\nos.system('typst')\n": ["os.system"],
        "import os\nos.popen('typst')\n": ["os.popen"],
        "from PySide6.QtCore import QProcess\nprocess = QProcess(self)\n": ["QProcess(...)"],
        "from PySide6.QtCore import QProcess\nQProcess.startDetached('code', [])\n": ["QProcess.startDetached"],
        "import PySide6.QtCore as QtCore\nprocess = QtCore.QProcess()\n": ["QProcess(...)"],
    }
    for source, expected in planted.items():
        assert [what for _line, what in console_starts(source)] == expected, source
    quiet = [
        "import subprocess\nsubprocess.TimeoutExpired\nsubprocess.SubprocessError\nsubprocess.list2cmdline(['a'])\n",
        "import proc\nproc.run(['typst'])\nproc.qprocess(self)\nproc.start_detached('code', [])\n",
        "from PySide6.QtCore import QProcess\nif error == QProcess.ProcessError.FailedToStart:\n    pass\nQProcess.ExitStatus.NormalExit\n",
        'def f():\n    """Runs `subprocess.run` and `QProcess(self)` in a thread."""\n    # os.system is not called here\n',
        "import os\nos.startfile('a.pdf')\nos.path.exists('a')\nos.environ.get('A')\n",
    ]
    for source in quiet:
        assert console_starts(source) == [], source
    # a deliberate exception says so, on its own line or the one above, and only there
    assert console_starts("import subprocess\nsubprocess.run(['a'])  # console-ok: the user watches this one\n") == []
    assert console_starts("import subprocess\n# console-ok: the user watches this one\nsubprocess.run(['a'])\n") == []
    assert console_starts("import subprocess\n# console-ok\n\n\nsubprocess.run(['a'])\n") == [(5, "subprocess.run")]


def test_a_child_gets_no_console_window_flag_on_windows_and_none_elsewhere():
    assert proc.NO_WINDOW == 0x08000000 == getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    assert proc.creation_flags(platform="win32") == proc.NO_WINDOW
    assert proc.creation_flags(0x200, platform="win32") == proc.NO_WINDOW | 0x200, "what the caller asked for is kept"
    assert proc.creation_flags(platform="linux") == 0 and proc.creation_flags(0x200, platform="darwin") == 0, "the flag means nothing off Windows, and subprocess refuses a nonzero one there"
    assert proc.creation_flags() == (proc.NO_WINDOW if sys.platform == "win32" else 0)


def test_run_and_popen_add_the_flag_to_the_call_and_leave_the_rest_alone():
    """`proc.run` and `proc.popen` are `subprocess.run` and `subprocess.Popen` and nothing else: every argument arrives as given, and `creationflags` gains the flag on Windows."""
    seen = []
    saved = subprocess.run, subprocess.Popen
    subprocess.run = lambda *args, **kwargs: seen.append(("run", args, kwargs)) or types.SimpleNamespace(returncode=0)
    subprocess.Popen = lambda *args, **kwargs: seen.append(("popen", args, kwargs)) or types.SimpleNamespace(returncode=0)
    try:
        proc.run(["typst", "--version"], capture_output=True, text=True, timeout=30)
        proc.run(["typst"], creationflags=0x200)
        proc.popen(["installer.exe"], close_fds=True)
    finally:
        subprocess.run, subprocess.Popen = saved
    on_windows = sys.platform == "win32"
    (kind, args, kwargs), (_kind2, _args2, flagged), (kind3, args3, kwargs3) = seen
    already = dict(kwargs)
    flags, flags3 = kwargs.pop("creationflags", 0), kwargs3.pop("creationflags", 0)
    assert kind == "run" and args == (["typst", "--version"],)
    assert flags == (proc.NO_WINDOW if on_windows else 0)
    assert kwargs == {"capture_output": True, "text": True, "timeout": 30}, "no argument is touched but creationflags"
    assert flagged.get("creationflags", 0) == ((proc.NO_WINDOW | 0x200) if on_windows else 0), "a flag the caller gave is kept"
    assert kind3 == "popen" and args3 == (["installer.exe"],) and flags3 == (proc.NO_WINDOW if on_windows else 0)
    assert kwargs3 == {"close_fds": True}
    if not on_windows:
        assert "creationflags" not in flagged and "creationflags" not in already, "off Windows the argument is not passed at all"


def test_proc_runs_a_real_child_and_gives_its_output_back():
    """The wrapper is a working `subprocess.run`: a child's output is read through the pipes, as the export and the compile read Typst's."""
    done = proc.run([sys.executable, "-c", "import sys; print('out'); print('err', file=sys.stderr); sys.exit(3)"], capture_output=True, text=True, timeout=60)
    assert done.returncode == 3 and done.stdout.strip() == "out" and done.stderr.strip() == "err"
    child = proc.popen([sys.executable, "-c", "print('piped')"], stdout=subprocess.PIPE, text=True)
    out, _ = child.communicate(timeout=60)
    assert out.strip() == "piped" and child.returncode == 0


PROBE = r'''
import ctypes, json, subprocess, sys, traceback
from pathlib import Path

calc, python, target = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, calc)
code = "import ctypes; print(ctypes.windll.kernel32.GetConsoleWindow())"
result = {}
try:
    import proc
    from PySide6.QtCore import QCoreApplication
    app = QCoreApplication([])
    result["own"] = int(ctypes.windll.kernel32.GetConsoleWindow() or 0)
    result["plain"] = int(subprocess.run([python, "-c", code], capture_output=True, text=True, timeout=60).stdout)
    result["run"] = int(proc.run([python, "-c", code], capture_output=True, text=True, timeout=60).stdout)
    child = proc.popen([python, "-c", code], stdout=subprocess.PIPE, text=True)
    result["popen"] = int(child.communicate(timeout=60)[0])
    process = proc.qprocess()
    process.start(python, ["-c", code])
    process.waitForFinished(60000)
    result["qprocess"] = int(bytes(process.readAllStandardOutput()).decode().strip())
except BaseException:
    result["error"] = traceback.format_exc()
Path(target).write_text(json.dumps(result), encoding="utf-8")
'''


def test_a_child_of_a_windowless_gui_has_no_console_window():
    """The defect itself, from the one process it shows in: a `pythonw.exe`, which has no console. Its child console program (`python.exe` asking for its own console window) gets a window through a plain `subprocess.run` -- and none through `proc.run`, `proc.popen` or `proc.qprocess`."""
    if sys.platform != "win32":
        raise conftest.OtherSystem("a console window is a Windows matter")
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    python = Path(sys.executable).with_name("python.exe")
    if not pythonw.is_file() or not python.is_file():
        raise conftest.Skip(f"no pythonw.exe and python.exe beside {sys.executable}")
    try:
        import PySide6  # noqa: F401
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    folder = conftest.tmpdir("no_console")
    script, result_file = folder / "probe.py", folder / "result.json"
    script.write_text(PROBE, encoding="utf-8")
    subprocess.run([str(pythonw), str(script), str(CALC), str(python), str(result_file)], timeout=180)   # pythonw, not proc: the test is the GUI's stand-in
    assert result_file.is_file(), "the probe wrote nothing"
    result = json.loads(result_file.read_text(encoding="utf-8"))
    assert "error" not in result, result.get("error")
    assert result["own"] == 0, f"pythonw.exe has a console of its own ({result}): the probe would say nothing"
    if result["plain"] == 0:
        raise conftest.Skip(f"this machine gives a child of a windowless process no console window even without the flag ({result}): the probe cannot tell the two apart")
    assert result["run"] == 0, f"proc.run: the child has a console window ({result})"
    assert result["popen"] == 0, f"proc.popen: the child has a console window ({result})"
    assert result["qprocess"] == 0, f"proc.qprocess: the child has a console window -- Qt no longer starts it with CREATE_NO_WINDOW ({result})"


DRIVE = r"""
import os, sys
sys.path[:0] = [sys.argv[1], os.path.dirname(sys.argv[1])]
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
app = QApplication([])
import theme; theme.apply(app)
import woodcore_gui
window = woodcore_gui.open_project(app, os.environ["WOODCORE_PROJECT"], quiet=True)
QTimer.singleShot(300, window.export_pdf)
def check():
    if window.process is None and not window.compile_queue and not window.compiling:
        app.quit()
watch = QTimer(app)
watch.timeout.connect(check)
QTimer.singleShot(2000, lambda: watch.start(300))
QTimer.singleShot(240000, app.quit)
app.exec()
"""


def _visible_consoles():
    """The console windows on screen now: their handle and the process that owns them."""
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    found = []

    def each(hwnd, _param):
        name = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, name, 256)
        if name.value in ("ConsoleWindowClass", "CASCADIA_HOSTING_WINDOW_CLASS") and user32.IsWindowVisible(hwnd):
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            found.append((hwnd, pid.value))
        return True
    user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)(each), 0)
    return found


def test_an_export_and_a_compilation_of_a_windowless_woodcore_open_no_console_window():
    """REQ-008 measured whole (spec docs/requirements/completed/2026-10-07-performance-erreurs-plans-legendes.md): the window as the launcher, Woodcore.pyw and Woodcore.exe start it -- no console of its own --, an export and the compilation of the documents asked for, and every console window that appears on screen meanwhile, looked for every 10 ms: none. Every console program it starts (python for the export, typst, git) has a console host, hidden; none has a window."""
    if sys.platform != "win32":
        raise conftest.OtherSystem("a console window is a Windows matter")
    if not conftest.have_typst():
        raise conftest.Skip("typst is not on the path")
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    if not pythonw.is_file():
        raise conftest.Skip(f"no pythonw.exe beside {sys.executable}")
    import shutil
    import time
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import perf_startup
    work, file = perf_startup._copy_project()
    env = perf_startup._environment(work, file)
    env.pop("QT_QPA_PLATFORM", None)   # a real window, as the engineer's
    script = work / "drive.py"
    script.write_text(DRIVE, encoding="utf-8")
    try:
        before = {hwnd for hwnd, _pid in _visible_consoles()}
        child = subprocess.Popen([str(pythonw), str(script), str(CALC / "tools")], env=env)
        appeared = set()
        while child.poll() is None:
            appeared |= {(hwnd, pid) for hwnd, pid in _visible_consoles() if hwnd not in before}
            time.sleep(0.01)
        assert child.returncode == 0, f"the window's run ended with {child.returncode}"
        assert not appeared, f"console windows appeared: {sorted(appeared)}"
    finally:
        shutil.rmtree(work, ignore_errors=True)
