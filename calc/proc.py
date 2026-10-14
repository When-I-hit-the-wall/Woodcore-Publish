"""Child processes started from Woodcore, without a console window flashing open (docs/ui/window.md §10quater).

Woodcore's window runs under `pythonw.exe`, or is the frozen, windowless `Woodcore.exe`: a process with **no console**. A console program -- `typst.exe`, `python.exe`, `git`, `winget`, `woodcore-cli.exe` -- that such a process starts with nothing said gets a console of its own, and Windows opens a window for it (a Windows Terminal tab, where that is the default terminal) which closes again when the program ends: a terminal that opens for a fraction of a second, very often when Typst compiles. Measured from a `pythonw.exe` here, the child of a plain `subprocess.run` has a console window (`GetConsoleWindow()` is a handle), and the child of the same call with `CREATE_NO_WINDOW` has none (0).

**Every child of the program is started through this module**, and `tests/test_no_console.py` refuses one that is not -- by reading the sources, so a start added next month cannot bring the flash back:

* `run` and `popen` are `subprocess.run` and `subprocess.Popen` with `CREATE_NO_WINDOW` added to the creation flags on Windows, and the call untouched elsewhere. The std handles are not affected: a child whose output is read through pipes still writes to them.
* `qprocess` and `start_detached` are Qt's. ⚠️ **PySide6 6.11 does not expose `QProcess.setCreateProcessArgumentsModifier`**, the Windows-only hook that would add the flag (checked: the attribute is not on `QProcess` in 6.11.2), so a QProcess cannot be given it. It does not need it where it matters: Qt itself starts a child with `CREATE_NO_WINDOW` when its own process has no console -- `GetConsoleWindow() ? 0 : CREATE_NO_WINDOW` in `QProcessPrivate::startProcess` -- which is what the window is, and the test runs a QProcess from a real `pythonw.exe` to say so. The two functions are there so that one place knows every start: the day a binding offers the modifier, or Qt's rule changes, this is the only file that moves.

⚠️ **What is deliberately not here**: a child the engineer is meant to watch -- the build scripts of `packaging/` and `website/build.py`, run from a terminal and writing their progress to it -- and a child that is a window of its own (`os.startfile` opening a PDF or the installer, `QDesktopServices`). Hiding the console of the first would hide the output it exists to show; the second has no console to hide.

Imports nothing of Qt at the top, like every module the pipeline reaches: `qprocess` imports it when it is called.
"""

import subprocess
import sys

# Win32 `CREATE_NO_WINDOW`: the child is a console program run without a console window. `subprocess.CREATE_NO_WINDOW` carries the same value on Windows, and does not exist elsewhere.
NO_WINDOW = 0x08000000


def creation_flags(extra=0, platform=None):
    """The `creationflags` a child is started with: `extra` -- what the caller wants of its own -- and, on Windows, `CREATE_NO_WINDOW`. `platform` is `sys.platform` unless a test says otherwise; 0 elsewhere, where the flag means nothing and `subprocess` refuses a nonzero one."""
    on_windows = (sys.platform if platform is None else platform) == "win32"
    return (int(extra) | NO_WINDOW) if on_windows else 0


def _quiet(kwargs):
    """The keyword arguments of a `subprocess` call, `creationflags` made quiet -- and left out altogether where the flags come to nothing."""
    flags = creation_flags(kwargs.pop("creationflags", 0))
    if flags:
        kwargs["creationflags"] = flags
    return kwargs


def run(*args, **kwargs):
    """`subprocess.run`, without a console window on Windows. A `creationflags` the caller gives is kept and gains the flag."""
    return subprocess.run(*args, **_quiet(kwargs))


def popen(*args, **kwargs):
    """`subprocess.Popen`, without a console window on Windows. A `creationflags` the caller gives is kept and gains the flag."""
    return subprocess.Popen(*args, **_quiet(kwargs))


def qprocess(parent=None):
    """A `QProcess` for a console program, as `QProcess(parent)`: the one place a window makes one (see the module's note on what Qt does by itself and what PySide6 6.11 does not offer)."""
    from PySide6.QtCore import QProcess
    return QProcess(parent)


def start_detached(program, arguments, working_directory=""):
    """`QProcess.startDetached(program, arguments, working_directory)`: a program started in a process of its own that outlives this one -- a window, here: VS Code, or Woodcore itself started again. Returns whether it started."""
    from PySide6.QtCore import QProcess
    started = QProcess.startDetached(program, list(arguments), str(working_directory))
    return bool(started[0] if isinstance(started, tuple) else started)   # PySide6 hands back (started, pid)
