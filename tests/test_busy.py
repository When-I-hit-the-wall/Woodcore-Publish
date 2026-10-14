# -*- coding: utf-8 -*-
"""The card Woodcore shows while it works (calc/tools/busy.py, v0.113): the window held -- a click, a key, the wheel, a shortcut eaten -- while what only shows goes on, the pointer's hover among it; the card over the window and kept over content built after it; a hold inside a hold; work run in a thread with the event loop free; and the window's own long work -- a reload, a rebuild, an export, the opening of a project -- done under the card, its arc turned between two modules.

The engineer's request of 03.10.2026: «quand il y a des chargements, la fenêtre ne fait que de freeze … afficher quelque chose qui charge au milieu de l'écran … que si on passe sur des boutons, il y ait toujours le overlay du mouse over dessus, mais on ne peut pas interagir avec».
"""

import os
import sys
import time

import conftest


TOOLS = conftest.CALC / "tools"


def _qt():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    app = QApplication.instance() or QApplication([])
    import theme
    theme.ensure(app)
    return app


def _window():
    from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget
    window = QWidget()
    window.resize(600, 400)
    layout = QVBoxLayout(window)
    button = QPushButton("Exporter")
    layout.addWidget(button)
    window.show()
    return window, button


def test_a_held_window_takes_no_click_and_keeps_its_hover():
    app = _qt()
    import busy
    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QEnterEvent, QMouseEvent
    window, button = _window()
    clicks, entered = [], []
    button.clicked.connect(lambda: clicks.append(1))
    original = button.event

    def watch(event):
        if event.type() == QEvent.Type.Enter:
            entered.append(1)
        return original(event)
    button.event = watch
    try:
        card = busy.start(window, "Export en cours…")
        assert busy.held(window) and card.isVisible() and card.geometry() == window.rect()
        assert app.overrideCursor() is not None and app.overrideCursor().shape() == Qt.CursorShape.BusyCursor
        for kind in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
            app.sendEvent(button, QMouseEvent(kind, QPointF(5, 5), QPointF(5, 5), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))
        assert not clicks, "a click went through a held window"
        app.sendEvent(button, QEnterEvent(QPointF(5, 5), QPointF(5, 5), QPointF(5, 5)))
        assert entered, "the pointer's hover was held back with the clicks"
        busy.stop(window)
        assert not busy.held(window) and app.overrideCursor() is None
        for kind in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
            app.sendEvent(button, QMouseEvent(kind, QPointF(5, 5), QPointF(5, 5), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))
        assert clicks == [1], "the window let go takes its clicks again"
    finally:
        busy.stop_all()
        conftest.dispose(window)
def test_keys_and_shortcuts_are_held_back_and_another_window_is_not():
    app = _qt()
    import busy
    from PySide6.QtCore import QEvent, Qt
    from PySide6.QtGui import QKeyEvent, QKeySequence, QShortcut
    from PySide6.QtWidgets import QLineEdit
    window, _button = _window()
    field = QLineEdit(window)
    other = QLineEdit()
    other.show()
    fired = []
    QShortcut(QKeySequence("Ctrl+K"), window, activated=lambda: fired.append(1))
    try:
        with busy.hold(window, "Chargement…"):
            app.sendEvent(field, QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier, "a"))
            assert field.text() == "", "a key went through a held window"
            app.sendEvent(other, QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_B, Qt.KeyboardModifier.NoModifier, "b"))
            assert other.text() == "b", "a window not held -- a message box the work opens -- was held too"
        app.sendEvent(field, QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier, "a"))
        assert field.text() == "a"
    finally:
        busy.stop_all()
        conftest.dispose(window)
        other.close()


def test_a_hold_inside_a_hold_leaves_the_outer_one_standing():
    _qt()
    import busy
    window, _button = _window()
    try:
        busy.start(window, "Export en cours…")
        with busy.hold(window, "Chargement…"):
            assert busy._held[window].text == "Chargement…"
        assert busy.held(window), "the inner hold let go of the export's"
        busy.stop(window)
        assert not busy.held(window)
        busy.stop(window)   # twice is harmless
        busy.stop(None)
        assert busy.start(None, "rien") is None
    finally:
        busy.stop_all()
        conftest.dispose(window)
def test_the_guard_is_on_only_while_free_running_work_is_held():
    """The application-wide filter is a crossing into Python for every event of the process: about 8 s of the example window's 19 s build while it was installed for good (docs/architecture/performance.md, 08.10.2026). Main-thread work -- a window built, a reload -- is held without it, and it is taken off once no export, compilation or thread is held."""
    _qt()
    import busy
    window, _button = _window()
    try:
        with busy.hold(window, "Chargement…", guard=False):
            assert busy.held(window)
            assert busy._guard is None, "main-thread work installed the application's filter"
        busy.start(window, "Export en cours…")
        assert busy._guard is not None, "an export left the window unguarded"
        with busy.hold(window, "Chargement…", guard=False):
            assert busy._guard is not None, "a hold inside the export took its guard off"
        busy.stop(window)
        assert busy._guard is None, "the guard stayed on with nothing held"
    finally:
        busy.stop_all()
        conftest.dispose(window)
def test_the_card_stays_over_content_built_after_it():
    """A rebuild sets a new central widget under the card: added later, it would be stacked above it -- the card raises itself when a child is added, and again at every pump."""
    app = _qt()
    import busy
    from PySide6.QtWidgets import QLabel, QMainWindow
    window = QMainWindow()
    window.resize(600, 400)
    window.show()
    try:
        card = busy.start(window, "Chargement…")
        window.setCentralWidget(QLabel("contenu"))
        busy.pump(force=True)
        app.processEvents()
        siblings = [w for w in window.children() if hasattr(w, "isVisible") and w.isVisible()]
        assert siblings[-1] is card, [type(w).__name__ for w in siblings]
    finally:
        busy.stop_all()
        conftest.dispose(window)
def test_pump_does_nothing_while_nothing_is_held():
    _qt()
    import busy
    from PySide6.QtCore import QTimer
    fired = []
    QTimer.singleShot(0, lambda: fired.append(1))
    busy.pump(force=True)
    assert not fired, "pump turned the loop with nothing held"
    window, _button = _window()
    try:
        busy.start(window, "x")
        busy.pump(force=True)
        assert fired, "pump did not turn the loop while held"
    finally:
        busy.stop_all()
        conftest.dispose(window)
def test_work_in_a_thread_leaves_the_loop_free_and_gives_back_its_answer_or_its_error():
    _qt()
    import busy
    from PySide6.QtCore import QTimer
    window, _button = _window()
    ticks = []
    timer = QTimer()
    timer.setInterval(10)
    timer.timeout.connect(lambda: ticks.append(1))
    timer.start()
    try:
        answer = busy.run_in_thread(window, "Création du projet…", lambda: time.sleep(0.4) or 42)
        assert answer == 42
        # the loop turned while the thread slept: ~40 ticks alone, fewer after the windows earlier tests leave behind have their own events processed in the same loop -- what is held is that it turned at all
        assert ticks, "the event loop stood still while the thread worked"
        assert not busy.held(window)

        def fails():
            raise ValueError("refusé")
        try:
            busy.run_in_thread(window, "x", fails)
        except ValueError as exc:
            assert str(exc) == "refusé"
        else:
            raise AssertionError("the thread's error was swallowed")
        assert not busy.held(window), "a work that failed left the window held"
    finally:
        timer.stop()
        busy.stop_all()
        conftest.dispose(window)
def test_the_splash_is_a_card_of_its_own():
    _qt()
    import busy
    splash = busy.Splash("Ouverture de « Exemple »…")
    try:
        assert splash.isVisible() and busy.held(splash) and splash.spinner.text.startswith("Ouverture")
    finally:
        busy.stop(splash)
        splash.close()


def test_the_card_states_no_colour_of_its_own():
    text = (conftest.ROOT / "calc" / "tools" / "busy.py").read_text(encoding="utf-8")
    import re
    assert not re.search(r"#[0-9a-fA-F]{6}\b", text), "busy.py states a colour: it reads the theme's tokens"
    for token in ("card", "line", "accent", "ink", "muted"):
        assert f'theme.colour("{token}")' in text


def test_the_window_builds_its_modules_under_the_card():
    """A reload and a rebuild hold the window and turn the arc between two modules; a switch of document likewise; the words the card says are the window's, in three languages."""
    _qt()
    import busy
    import project
    import woodcore_gui
    here = conftest.project_copy("busy_build")
    with project.using(here):
        window = woodcore_gui.MainWindow()
        window.show()
        pumps = []
        real = busy.pump
        busy.pump = lambda force=False: pumps.append(busy.held(window)) or real(force)
        try:
            window.reload()
            assert len(pumps) >= len(woodcore_gui.TABS) and all(pumps), "the modules were not built under the card"
            assert not busy.held(window), "a reload left the window held"
            pumps.clear()
            other = next(mode for mode in here.modes if mode != window.mode)
            window.on_mode_changed(other)
            assert pumps and all(pumps) and not busy.held(window)
        finally:
            busy.pump = real
            busy.stop_all()
            conftest.dispose(window)
    for lang in ("fr", "de", "en"):
        for key in ("busy_loading", "busy_opening", "busy_installing", "busy_switching"):
            assert woodcore_gui.STRINGS[lang][key]


def test_an_export_holds_the_window_until_it_is_done():
    """«Import données» and «Exporter PDF» hold the window for as long as the export and the compilations run (the engineer's choice of 03.10.2026), and let it go when it fails as when it succeeds."""
    _qt()
    import busy
    import project
    import woodcore_gui
    from PySide6.QtWidgets import QMessageBox
    with project.using(conftest.project_copy("busy_export")):
        window = woodcore_gui.MainWindow()
        window.show()
        critical = QMessageBox.critical
        QMessageBox.critical = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok)
        try:
            window.engine_consent = lambda: []
            window.process = None
            busy.start(window, window.t("exporting"))   # what reexport does before it starts the process
            window.process = type("P", (), {"deleteLater": lambda self: None})()
            window.export_done(1, "", "boom")
            assert not busy.held(window), "a failed export left the window held"
            busy.start(window, window.t("exporting"))
            window.process = type("P", (), {"deleteLater": lambda self: None})()
            window.export_done(0, "", "")
            assert not busy.held(window), "a finished export left the window held"
        finally:
            QMessageBox.critical = critical
            busy.stop_all()
            conftest.dispose(window)
def test_the_card_says_the_time_gone_and_how_far_the_work_is_where_it_is_known():
    """REQ-006 (v0.117): «une estimation si celle-ci est fiable» -- the time gone is what is certain, said once it passes ELAPSED_AFTER_S; a progress where the work knows it, as a thin bar."""
    _qt()
    import busy
    window, _button = _window()
    try:
        card = busy.start(window, "Compilation du document Typst", "rapport")
        assert card.detail_line() == "rapport"
        card.started -= busy.ELAPSED_AFTER_S + 1
        assert card.detail_line().startswith("rapport · ") and card.detail_line().endswith(" s")
        tall = card.card_rect().height()
        busy.set_progress(window, 0.4)
        assert card.fraction == 0.4 and card.card_rect().height() > tall
        busy.set_progress(window, None)
        assert card.fraction is None
        card.grab()   # painted with its bar and its time, without an error
    finally:
        busy.stop_all()
        conftest.dispose(window)