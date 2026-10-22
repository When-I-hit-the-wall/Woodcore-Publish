"""The lock a window holds on the project it has open, so two machines do not edit one project at once (docs/ui/window.md §10quater, v0.83).

A project lives in NextCloud and is opened from more than one machine. Two windows saving the same sources, one after the other, lose the first one's work without a word -- NextCloud keeps the later file and a conflicted copy nobody opens. So a window opening a project writes a small file beside its `.woodcore`, naming who holds it, and a second window finding one asks: open it read-only, open it anyway, or not at all.

**The file is `<name>.woodcore.lock`, and not `~$<name>.woodcore`** as Word names its own. NextCloud's default exclusion list carries `~$*` -- Office's lock files -- so a lock named like Word's is never synced, and the other machine would never see it. Nothing in that list matches `*.lock`.

**A lock is advice, not a guarantee.** It reaches the other machine when NextCloud has synced it, a few seconds later, and a window that crashed leaves its lock behind. So a lock this machine left for a process that no longer runs is taken over without asking, and one another machine left is shown with its time, for the engineer to judge.
"""

import getpass
import json
import os
import socket
import sys
from datetime import datetime
from pathlib import Path

SUFFIX = ".lock"


def lock_path(here):
    """`Musterprojekt.woodcore.lock` beside `Musterprojekt.woodcore`."""
    file = Path(here.file if hasattr(here, "file") else here)
    return file.with_name(file.name + SUFFIX)


def whoami():
    """Who this window is: the user, the machine, the process, and since when."""
    try:
        user = getpass.getuser()
    except (OSError, KeyError, ImportError):   # getuser raises where no variable names the user
        user = os.environ.get("USERNAME") or "?"
    return {"user": user, "host": socket.gethostname(), "pid": os.getpid(),
            "since": datetime.now().isoformat(timespec="seconds")}


def _alive(pid):
    """Whether process `pid` runs on this machine."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.OpenProcess(0x1000, False, pid)   # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return ctypes.get_last_error() == 5   # ERROR_ACCESS_DENIED: it runs, under someone else
        try:
            code = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return True
            return code.value == 259   # STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def read(here):
    """The lock beside the project as it stands, or None."""
    try:
        data = json.loads(lock_path(here).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _ours(lock, me):
    return lock.get("host") == me["host"] and str(lock.get("pid")) == str(me["pid"])


def holder(here, me=None):
    """Who else holds the project, or None: a lock of this very process is no one else's, and one this machine left for a process that no longer runs is stale."""
    me = me or whoami()
    lock = read(here)
    if lock is None or _ours(lock, me):
        return None
    if lock.get("host") == me["host"] and not _alive(lock.get("pid")):
        return None
    return lock


def acquire(here, force=False, me=None):
    """Writes this window's lock beside the project. Returns None where it holds it now, else the lock of whoever does -- nothing written. `force` takes a lock someone else holds, which is «Ouvrir quand même»."""
    me = me or whoami()
    other = holder(here, me)
    if other is not None and not force:
        return other
    try:
        lock_path(here).write_text(json.dumps(me, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    except OSError:
        pass   # a folder that cannot be written to is one nobody else can save into either
    return None


def release(here, me=None):
    """Removes the lock beside the project, if it is this process's -- never another window's."""
    me = me or whoami()
    lock = read(here)
    if lock is not None and _ours(lock, me):
        try:
            lock_path(here).unlink()
        except OSError:
            pass
