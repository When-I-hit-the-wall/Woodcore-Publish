"""Long work off the window's thread, said while it runs (calc/tools/tasks.py; spec docs/requirements/completed/2026-10-07-performance-erreurs-plans-legendes.md, REQ-006, REQ-007, ARCH-002, ARCH-003).

What is held here: a task's result reaches the window's thread and only there; the loop keeps turning while it runs; an exception becomes a critical notice, not a box and not silence; a result made stale by a later task of the same key is not used; two tasks that write into the project never run at once; a blocking task holds the window with the card and lets it go.
"""

import os
import sys
import threading
import time

from conftest import ROOT, Skip

import notifications


def _qt():
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _until(app, condition, timeout=10.0):
    end = time.monotonic() + timeout
    while not condition():
        if time.monotonic() > end:
            raise AssertionError("timed out")
        app.processEvents()
        time.sleep(0.005)


def test_a_background_task_answers_on_the_window_s_thread_and_the_loop_turns_meanwhile():
    app = _qt()
    import tasks
    from PySide6.QtCore import QTimer
    runner = tasks.TaskRunner()
    main = threading.get_ident()
    seen, ticks, labels = {}, [], []
    runner.changed.connect(lambda: labels.append(runner.labels()))
    timer = QTimer()
    timer.setInterval(20)
    timer.timeout.connect(lambda: ticks.append(1))
    timer.start()

    def work():
        seen["thread"] = threading.get_ident()
        time.sleep(0.6)
        return 42
    runner.run("Rendu du plan", work, done=lambda result: seen.update(result=result, done_in=threading.get_ident()))
    assert runner.labels() == ["Rendu du plan"], "what runs is named for the activity chip"
    _until(app, lambda: "result" in seen)
    timer.stop()
    assert seen["result"] == 42 and seen["thread"] != main and seen["done_in"] == main
    assert len(ticks) >= 10, f"the loop stood still while the work ran ({len(ticks)} ticks in 0.6 s)"
    assert runner.labels() == [] and labels[0] == ["Rendu du plan"] and labels[-1] == []


def test_an_exception_is_a_critical_notice_unless_the_caller_takes_it():
    app = _qt()
    import tasks
    runner = tasks.TaskRunner()
    notifications.STORE.clear()
    runner.run("Export des calques", lambda: {}["h"])
    _until(app, lambda: not runner.busy())
    app.processEvents()
    (notice,) = notifications.STORE.items(notifications.CRITICAL)
    assert "KeyError" in notice.text and notice.source == "Export des calques" and "Traceback" in notice.technical
    notifications.STORE.clear()
    caught = []
    runner.run("Lecture", lambda: 1 / 0, failed=caught.append)
    _until(app, lambda: caught)
    assert isinstance(caught[0], ZeroDivisionError) and not notifications.STORE.items()


def test_a_later_task_of_the_same_key_makes_the_earlier_one_s_result_stale():
    app = _qt()
    import tasks
    runner = tasks.TaskRunner()
    results = []
    runner.run("Rendu", lambda: time.sleep(0.4) or "P01", done=results.append, key="render")
    runner.run("Rendu", lambda: time.sleep(0.05) or "P02", done=results.append, key="render")
    _until(app, lambda: not runner.busy())
    app.processEvents()
    assert results == ["P02"], results


def test_two_writers_never_run_at_once():
    app = _qt()
    import tasks
    runner = tasks.TaskRunner()
    inside, most = [0], [0]
    lock = threading.Lock()

    def write():
        with lock:
            inside[0] += 1
            most[0] = max(most[0], inside[0])
        time.sleep(0.15)
        with lock:
            inside[0] -= 1
    for _ in range(3):
        runner.run("Écriture", write, writes=True)
    assert not runner.writers_idle()
    _until(app, lambda: not runner.busy())
    assert most[0] == 1 and runner.writers_idle()


def test_a_blocking_task_holds_the_window_with_the_card_and_lets_it_go():
    app = _qt()
    import busy
    import tasks
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QWidget
    window = QWidget()
    window.resize(400, 300)
    window.show()
    runner = tasks.TaskRunner()
    ticks = []
    timer = QTimer()
    timer.setInterval(100)
    timer.timeout.connect(lambda: ticks.append(time.monotonic()))
    try:
        timer.start()
        runner.run("Compilation du document Typst", lambda: time.sleep(3.0), window=window, blocking=True)   # REQ-006's criterion: three seconds of work
        assert busy.held(window) and busy._held[window].text == "Compilation du document Typst"
        assert busy._held[window].isVisible(), "the card is up over the window"
        assert runner.labels() == [], "a blocking task has the card, not the chip"
        _until(app, lambda: not runner.busy())
        assert len(ticks) >= 20, f"the loop turned {len(ticks)} times in three seconds: it was held, not alive"
        assert not busy.held(window)
    finally:
        timer.stop()
        busy.stop_all()
        window.close()


def test_what_runs_anywhere_is_said_by_the_chip_in_the_window_s_words():
    """REQ-007: a preview compiled, a sheet rendered, a layer exported in its own thread -- each says it begins and ends (tasks.activity), and the chip at the top right says it, its name in the window's language, gone when it is done."""
    app = _qt()
    import notices_ui
    import tasks
    bar = notices_ui.NoticeBar(notices_ui.words("fr"), "fr")
    bar.show()
    tokens = []
    thread = threading.Thread(target=lambda: tokens.append(tasks.activity().begin("activity_preview")))
    thread.start()
    thread.join()
    _until(app, lambda: bar.activity.isVisible())
    assert bar.activity.toolTip() == "Aperçu Typst" and bar.activity.text() == "Chargement…"
    second = tasks.activity().begin("activity_sheet")
    _until(app, lambda: len(bar.activity.labels) == 2)
    assert bar.activity.text() == "2 tâches…"
    assert bar.activity.toolTip() == "Aperçu Typst\nRendu de la feuille", "the tip names both, in the window's words"
    from PySide6.QtWidgets import QApplication
    assert QApplication.activeModalWidget() is None, "work in the background opens no modal"
    tasks.activity().end(tokens[0])
    tasks.activity().end(second)
    _until(app, lambda: not bar.activity.isVisible())
    bar.close()
