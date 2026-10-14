"""The window's watch on itself (calc/tools/stallwatch.py): a pause of the event loop longer than STALL_S writes where the window was, and a window that answers writes nothing.

Held against a planted stall -- a function that sleeps, named so its frame can be found in the log -- because a watch that has never been seen to fire is a watch nobody has tested. Skipped where PySide6 is not installed.

⚠️ **The two planted scenarios run in a process of their own.** Under the full suite the stall test failed and alone it passed: its log found the main thread in `loop.exec()` rather than in the planted frame. The cause, found on 17.09.2026 in a sandbox by bisecting the files that run before it: the windows the earlier tests build and rebuild leave a backlog of posted events -- deferred deletions of the widgets a rebuild replaces -- which Qt only processes when an event loop next runs, and that is this test's `loop.exec()`. Draining them took 1.56 s after the 22 files up to `test_pdf_button.py`, longer than STALL_S, so the watch fired on the backlog, and the planted stall that followed it without a beat in between was never dumped. With the backlog drained first the test passed in that same process. A watch whose subject is a pause of the event loop is measured where nothing else has left the loop work to do.
"""

import os
import sys
import time
from pathlib import Path

from conftest import ROOT, OtherSystem, Skip, tmpdir


def _app():
    path = str(ROOT / "calc" / "tools")
    if path not in sys.path:
        sys.path.insert(0, path)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _scenario(log, busy_seconds):
    """The planted scenario itself, run by `python tests/test_stallwatch.py <log> <seconds>` in a process of its own: a fresh application, the watch installed, a stall of `busy_seconds` planted, the log written."""
    app = _app()
    _run(app, busy_seconds, log)


def _in_own_process(busy_seconds):
    """The log of the planted scenario, run in a fresh interpreter -- see the module docstring for why."""
    import subprocess
    log = tmpdir("stallwatch-%s" % str(busy_seconds).replace(".", "_")) / "stalls.log"      # busy_seconds, or "hitch"
    try:
        from PySide6.QtWidgets import QApplication  # noqa: F401 -- a Skip here rather than a failure in the child
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    env = dict(os.environ, QT_QPA_PLATFORM=os.environ.get("QT_QPA_PLATFORM", "offscreen"))
    run = subprocess.run([sys.executable, "-u", str(Path(__file__).resolve()), str(log), str(busy_seconds)],
                         capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=120)
    assert run.returncode == 0, "the scenario's own process failed:\n" + run.stdout[-1500:] + run.stderr[-1500:]
    return log.read_text(encoding="utf-8")


def _run(app, busy_seconds, log=None):
    import faulthandler
    import stallwatch
    from PySide6.QtCore import QEventLoop, QTimer
    log = log if log is not None else tmpdir("stallwatch") / "stalls.log"
    assert stallwatch.install(app, log) == log

    def a_frame_the_log_must_name():
        time.sleep(busy_seconds)

    loop = QEventLoop()
    QTimer.singleShot(100, a_frame_the_log_must_name)
    QTimer.singleShot(int(1000 * (busy_seconds + stallwatch.STALL_S)) + 400, loop.quit)
    try:
        loop.exec()
    finally:
        faulthandler.cancel_dump_traceback_later()
        _stop(app)
    return log.read_text(encoding="utf-8")


def _stop(app):
    timer, handle = app._stallwatch
    timer.stop()
    handle.close()
    time.sleep(0.4)     # the watch thread sees the log closed at its next tick and ends


def test_a_stall_writes_where_the_window_was():
    text = _in_own_process(2.2)
    assert "Timeout" in text and "a_frame_the_log_must_name" in text, text[-800:]


def test_a_window_that_answers_writes_nothing_but_its_start():
    text = _in_own_process(0.2)
    assert "Timeout" not in text, text[-800:]


def _os_thread_ids():
    """Every operating-system thread id of this process -- Windows only, where the churn was measured."""
    import ctypes
    from ctypes import wintypes
    if os.name != "nt":
        raise OtherSystem("the thread census uses the Windows tool-help API")

    class Entry(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ThreadID", wintypes.DWORD),
                    ("th32OwnerProcessID", wintypes.DWORD), ("tpBasePri", wintypes.LONG),
                    ("tpDeltaPri", wintypes.LONG), ("dwFlags", wintypes.DWORD)]
    kernel32 = ctypes.windll.kernel32
    snap = kernel32.CreateToolhelp32Snapshot(0x4, 0)
    entry = Entry()
    entry.dwSize = ctypes.sizeof(entry)
    ids, ok = set(), kernel32.Thread32First(snap, ctypes.byref(entry))
    while ok:
        if entry.th32OwnerProcessID == os.getpid():
            ids.add(entry.th32ThreadID)
        ok = kernel32.Thread32Next(snap, ctypes.byref(entry))
    kernel32.CloseHandle(snap)
    return ids


def test_the_watch_starts_no_thread_while_the_window_answers():
    """v0.77: the first version re-armed faulthandler.dump_traceback_later four times a second, and CPython starts a NEW operating-system thread at every re-arm -- 14 000 an hour for an idle window, found while the engineer reported a freeze every ~50 s. One watch thread for the life of the window now."""
    app = _app()          # first: it puts calc/tools on the path
    import stallwatch
    from PySide6.QtCore import QEventLoop, QTimer
    log = tmpdir("stallwatch-threads") / "stalls.log"
    assert stallwatch.install(app, log) == log
    loop = QEventLoop()
    QTimer.singleShot(300, loop.quit)
    loop.exec()
    before = _os_thread_ids()
    loop = QEventLoop()
    QTimer.singleShot(2000, loop.quit)
    loop.exec()
    born = _os_thread_ids() - before
    _stop(app)
    assert not born, "%d thread(s) started in two idle seconds" % len(born)


def _hitch(log):
    """The whole-computer scenario, run by `python tests/test_stallwatch.py <log> hitch` in a process of its own: the watch thread suspended by the operating system for 1.2 s while the window keeps answering."""
    import ctypes
    import threading
    app = _app()          # first: it puts calc/tools on the path
    import stallwatch
    from PySide6.QtCore import QEventLoop, QTimer
    assert stallwatch.install(app, log) == log
    watch = [t for t in threading.enumerate() if t.name == "woodcore-stallwatch" and t.is_alive()][-1]
    kernel32 = ctypes.windll.kernel32
    thread = kernel32.OpenThread(0x0002, False, watch.native_id)     # THREAD_SUSPEND_RESUME
    assert thread, "could not open the watch thread"

    def freeze():
        kernel32.SuspendThread(thread)
        time.sleep(1.2)
        kernel32.ResumeThread(thread)

    loop = QEventLoop()
    QTimer.singleShot(200, lambda: threading.Thread(target=freeze, daemon=True).start())
    QTimer.singleShot(2200, loop.quit)
    loop.exec()
    kernel32.CloseHandle(thread)
    _stop(app)


def test_a_stop_of_the_whole_computer_is_told_from_a_stall_of_the_window():
    """The watch thread is suspended by the operating system for 1.2 s -- exactly what a whole-computer freeze does to it -- while the window keeps answering: the log says «System hitch» and dumps no stack.

    ⚠️ In a process of its own, like the planted stall and for the same reason: under the whole suite the posted events the earlier tests' windows left behind held this test's own loop past 1.5 s, and the log carried a «Timeout» stack beside the hitch (full run of 17.09.2026)."""
    if os.name != "nt":
        raise OtherSystem("suspending a thread uses the Windows API")
    text = _in_own_process("hitch")
    assert "System hitch" in text and "Timeout" not in text, text[-800:]


if __name__ == "__main__":
    # the planted scenario's own process (_in_own_process): the tests folder on the path for conftest, the log and the stall's length as arguments
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    if sys.argv[2] == "hitch":
        _hitch(Path(sys.argv[1]))
    else:
        _scenario(Path(sys.argv[1]), float(sys.argv[2]))
    # os._exit runs no atexit handler, so this process's copy of the example project is removed here or never (conftest.WORK, v0.81)
    import conftest
    conftest._wipe(conftest.WORK)
    os._exit(0)
