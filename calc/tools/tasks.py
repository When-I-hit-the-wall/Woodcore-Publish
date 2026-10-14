# -*- coding: utf-8 -*-
"""Long work, off the window's thread and said while it runs (spec docs/requirements/completed/2026-10-07-performance-erreurs-plans-legendes.md, REQ-006, REQ-007, ARCH-002, ARCH-003).

The engineer, 07.10.2026: «Si l'utilisateur peut continuer à utiliser Woodcore pendant le chargement, ne pas afficher de popup au centre. Dans ce cas, afficher simplement un indicateur de chargement discret» · «Si une opération empêche réellement l'utilisateur d'interagir avec l'interface, afficher une fenêtre / overlay de chargement au centre» · «ne pas déplacer arbitrairement une opération dans un thread si cela peut créer des problèmes de concurrence ou de cohérence des données».

One way to run a piece of work that touches no widget (`run`), whatever it is -- a layer exported, a document read, a render prepared:

* **In the background** (the default): the work runs in a thread of the pool, the activity chip at the top right says «Chargement…» while it runs (notices_ui.ActivityChip, through `TaskRunner.changed`), the window stays free.
* **Blocking** (`blocking=True`): the same, with busy.py's card over the window and its input held -- busy's own guard, the loop free the whole time.
* **What it gives back** reaches `done(result)` on the window's thread, never in the thread: a widget is only touched by the thread that made it. An exception reaches `failed(exc)`, or, where there is none, the notices as a critical one (calc/notifications.py) -- never lost, never a box.
* **A result that came too late is not used**: a task given a `key` is the latest of that key; one started again under the same key -- another plan opened, the project changed -- makes the earlier one's result stale, and its `done` is not called (its generation, ARCH-003).
* **One writer at a time** (`writes=True`): work that writes into the project -- a layer's drawings exported into data/ -- runs in a pool of one thread, so two never write at once; the export, a process of its own, waits for none of them and is waited for by none: the window starts it only once the writers it started are done (`writers_idle`). Saving a source stays on the window's thread (autosave.py), where the engineer's own edits are.

Nothing here knows what the work is: its caller names it in the window's language (`label`).
"""

import itertools
import threading
import traceback

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal, Slot

import notifications

_tokens = itertools.count(1)


class Activity(QObject):
    """What runs in the background now, whatever runs it -- a TaskRunner's task, the export of a layer switched in its own thread, a preview compiled by Typst, a sheet rendered: each says it begins (`begin(key)`, a key of the window's words, `activity_<…>`) and ends (`end(token)`), from any thread, and the activity chip at the top right says it (notices_ui.ActivityChip, REQ-007). One for the process (`activity()`)."""

    changed = Signal()
    _poke = Signal()

    def __init__(self):
        super().__init__()
        self._lock = threading.Lock()
        self._running = {}
        self._poke.connect(self.changed, Qt.ConnectionType.QueuedConnection)

    def begin(self, key):
        token = next(_tokens)
        with self._lock:
            self._running[token] = key
        self._poke.emit()
        return token

    def end(self, token):
        with self._lock:
            found = self._running.pop(token, None) is not None
        if found:
            self._poke.emit()

    def keys(self):
        with self._lock:
            return list(self._running.values())


_activity = []


def activity():
    """The process's Activity, made the first time it is asked for (a QObject: after QApplication)."""
    if not _activity:
        _activity.append(Activity())
    return _activity[0]


class _Relay(QObject):
    """Carries a result from the pool's thread to the window's: its signals, emitted in the thread, are delivered in the thread this object lives in."""

    finished = Signal(int, object, object)   # token, result, exception


class _Job(QRunnable):
    def __init__(self, token, work, relay):
        super().__init__()
        self.token, self.work, self.relay = token, work, relay
        self.setAutoDelete(True)

    def run(self):
        try:
            result, error = self.work(), None
        except BaseException as exc:   # broad: handed to the window's thread, which says it
            result, error = None, exc
            error.__traceback_text__ = traceback.format_exc()
        self.relay.finished.emit(self.token, result, error)


class Task:
    """A piece of work under way: its `label`, whether it holds the window, its `key` and its token."""

    def __init__(self, token, label, key, blocking, done, failed, window):
        self.token, self.label, self.key, self.blocking = token, label, key, blocking
        self.done, self.failed, self.window = done, failed, window
        self.stale = False


class TaskRunner(QObject):
    """The window's tasks (one runner per window): what runs, said by `changed` and `labels()`."""

    changed = Signal()

    def __init__(self, parent=None, pool=None):
        super().__init__(parent)
        self.pool = pool or QThreadPool.globalInstance()
        self.writer = QThreadPool(self)
        self.writer.setMaxThreadCount(1)
        self.relay = _Relay(self)
        self.relay.finished.connect(self._finished)
        self.tasks = {}
        self.latest = {}
        self._lock = threading.Lock()

    def run(self, label, work, done=None, failed=None, *, blocking=False, window=None, key=None, writes=False):
        """`work()` -- touching no widget -- run in a thread; `done(result)` or `failed(exc)` called on the window's thread once it is over (module docstring). Returns the Task."""
        token = next(_tokens)
        task = Task(token, label, key, blocking, done, failed, window)
        with self._lock:
            if key is not None:
                earlier = self.latest.get(key)
                if earlier is not None and earlier in self.tasks:
                    self.tasks[earlier].stale = True
                self.latest[key] = token
            self.tasks[token] = task
        if blocking and window is not None:
            import busy
            busy.start(window, label)
        else:
            task.activity = activity().begin(label)
        (self.writer if writes else self.pool).start(_Job(token, work, self.relay))
        self.changed.emit()
        return task

    @Slot(int, object, object)
    def _finished(self, token, result, error):
        with self._lock:
            task = self.tasks.pop(token, None)
            if task is not None and task.key is not None and self.latest.get(task.key) == token:
                del self.latest[task.key]
        if task is None:
            return
        if task.blocking and task.window is not None:
            import busy
            busy.stop(task.window)
        if getattr(task, "activity", None) is not None:
            activity().end(task.activity)
        self.changed.emit()
        if task.stale:
            return   # a later task of the same key has the say
        if error is not None:
            if task.failed is not None:
                task.failed(error)
            else:
                notifications.report_exception(error, source=task.label)
            return
        if task.done is not None:
            task.done(result)

    def labels(self):
        """What runs in the background now, each named -- what the activity chip says; a blocking task has the card instead."""
        with self._lock:
            return [t.label for t in self.tasks.values() if not t.blocking and not t.stale]

    def busy(self):
        with self._lock:
            return bool(self.tasks)

    def writers_idle(self):
        """Whether no task that writes into the project is running."""
        return self.writer.activeThreadCount() == 0

    def wait(self, msecs=-1):
        """Every task's thread finished (a window closing, a test): the results still to be delivered are delivered at the next turn of the loop."""
        self.writer.waitForDone(msecs)
        return self.pool.waitForDone(msecs) if self.pool is not QThreadPool.globalInstance() else True
