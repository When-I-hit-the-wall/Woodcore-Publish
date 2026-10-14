# -*- coding: utf-8 -*-
"""Where Woodcore's window was when it stopped answering -- and whether the whole computer stopped with it (docs/ui/window.md §10quater).

The engineer met the «Schémas» tab freezing for two or three seconds, now and then, the whole computer with it. One cause was found and measured -- the schema's SVG rendered again on every paint, about 300 ms a paint at a device pixel ratio of 2 (schema_canvas.SvgLayer) -- but a freeze that comes «sometimes» on another machine is exactly the kind a session cannot be sure it has seen the whole of. So the window keeps a watch on itself, and appends what it sees to `%LOCALAPPDATA%\\Woodcore\\stalls.log` (`typst-katalog` until v0.83):

- **the window stopped** -- a timer on the event loop beats four times a second, and one watch thread notices when the beat is more than STALL_S old. It then writes the Python stack of every thread (`faulthandler.dump_traceback`), once per stall: the frame the window was in (a canvas's paint, an export, a file read), or `app.exec()` alone for a stall inside Qt's own C++.
- **the whole computer stopped** -- the watch thread sleeps a quarter of a second at a time, so when it wakes up more than HITCH_S late, nothing on the machine was being scheduled, the window included. That is written as a line of its own, with the process's memory at that moment, which is what tells a freeze of the window from a freeze of the computer the window merely sits on.

⚠️ **One thread for the life of the window** (v0.77). The first version re-armed `faulthandler.dump_traceback_later` four times a second, and CPython implements every re-arm by joining the old watchdog thread and starting a new one: 14 000 operating-system threads an hour, for a window standing idle. It was measured, it was found while the engineer reported a freeze every ~50 s, and it is gone whether or not it was that freeze's cause.

Outside the project, beside the plans' render cache, so nothing of it is synced or versioned.
"""

import ctypes
import faulthandler
import os
import threading
import time
from pathlib import Path

from PySide6.QtCore import QTimer

import usersettings  # where Woodcore keeps its caches and its log (usersettings.py)

LOG = usersettings.cache_dir("stalls.log")   # %LOCALAPPDATA%\Woodcore\stalls.log, typst-katalog\stalls.log until v0.83
TICK_MS = 250
STALL_S = 1.5
HITCH_S = 0.75           # a watch thread that wakes this late found the whole machine unscheduled
LOG_LIMIT = 512 * 1024   # a log grown past this is started afresh: it is a diagnosis, not an archive


def _memory():
    """The process's working set and private bytes in MB, or "" where Windows is not there to ask."""
    try:
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                        ("PrivateUsage", ctypes.c_size_t)]
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        process = ctypes.windll.kernel32.GetCurrentProcess()
        if not ctypes.windll.psapi.GetProcessMemoryInfo(process, ctypes.byref(counters), counters.cb):
            return ""
        return "working set %d MB, private %d MB" % (counters.WorkingSetSize // 2**20, counters.PrivateUsage // 2**20)
    except Exception:  # broad: a diagnosis must never be what breaks the window
        return ""


def install(app, log=LOG, stall_s=None):
    """Arms the watch for the life of `app`. Returns the log's path, or None where it cannot be opened (a read-only profile) -- the window runs the same without it."""
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        if log.exists() and log.stat().st_size > LOG_LIMIT:
            log.unlink()
        handle = open(log, "a", encoding="utf-8")
        handle.write(f"\n--- Woodcore started {time.strftime('%Y-%m-%d %H:%M:%S')}; below, a stack dump is the window stopped for more than {STALL_S} s, and a one-line entry the whole computer stopped for more than {HITCH_S} s\n")
        handle.flush()
    except OSError:
        return None

    state = {"beat": time.monotonic()}
    lock = threading.Lock()

    def beat():
        state["beat"] = time.monotonic()

    def write(text, stacks=False):
        with lock:
            if handle.closed:
                return False
            handle.write(text)
            handle.flush()
            if stacks:
                faulthandler.dump_traceback(file=handle, all_threads=True)
            return True

    stall_s = STALL_S if stall_s is None else float(stall_s)   # v0.117: a threshold of the caller's -- a measurement of the start at a quarter of a second

    def watch():
        dumped = False
        tick = min(TICK_MS / 1000.0, stall_s / 2)
        last = time.monotonic()
        while not handle.closed:
            time.sleep(tick)
            now = time.monotonic()
            try:
                late = now - last - tick
                if late > HITCH_S:
                    write("%s System hitch: the watch thread woke %.0f ms late -- the whole computer, not only Woodcore, was stopped (%s)\n"
                          % (time.strftime("%H:%M:%S"), late * 1000, _memory()))
                last = now
                silent = now - state["beat"]
                if silent > stall_s and not dumped:
                    write("%s Timeout: the window has not answered for %.1f s (%s)\n"
                          % (time.strftime("%H:%M:%S"), silent, _memory()), stacks=True)
                    dumped = True
                elif silent <= stall_s:
                    dumped = False
            except (ValueError, OSError):
                return      # the log was closed under us: the window is going

    timer = QTimer(app)
    timer.setInterval(min(TICK_MS, int(stall_s * 500)))
    timer.timeout.connect(beat)
    timer.start()
    threading.Thread(target=watch, name="woodcore-stallwatch", daemon=True).start()

    def stop():
        timer.stop()
        with lock:
            handle.close()

    app.aboutToQuit.connect(stop)
    app._stallwatch = (timer, handle)   # kept alive with the application
    return log
