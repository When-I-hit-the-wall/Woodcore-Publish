"""The notices in the window: the indicators at the top right and their panel (calc/tools/notices_ui.py; spec docs/requirements/completed/2026-10-07-performance-erreurs-plans-legendes.md, UI-001 to UI-005).

The engineer, 07.10.2026: «[ 🔴 ] [ 🟠 ] Français | Deutsch | English» · «Le symbole doit être coloré uniquement lorsqu'au moins une erreur critique existe» · «clignoter pendant environ 3 secondes» · «un grand panneau déroulant directement sous les indicateurs … ne doit pas dépasser en dehors de la fenêtre … scrollable» · «Chaque erreur doit pouvoir être copiée» · «supprimer une erreur individuellement ; supprimer toutes les erreurs». The window is built once, off-screen, on the session's project; the process's store is emptied around each test.
"""

import contextlib
import os
import sys
import time

import conftest
from conftest import ROOT, Skip

import notifications
import project

_STATE = {}


def _qt():
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        from PySide6.QtWidgets import QApplication
        import PySide6.QtPdf  # noqa: F401
    except ImportError as exc:
        raise Skip(f"PySide6 or its QtPdf is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _window():
    if "window" not in _STATE:
        app = _qt()
        here = conftest.project_copy("notice_bar")
        with project.using(here):
            import woodcore_gui
            notifications.configure(translate=woodcore_gui.translate_notice)
            window = woodcore_gui.MainWindow()
        window.resize(1300, 760)
        window.show()
        _STATE.update(app=app, window=window, here=here)
    return _STATE["window"], _STATE["here"]


def _pump(seconds):
    app = _STATE["app"]
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        app.processEvents()
        time.sleep(0.01)


@contextlib.contextmanager
def _clean():
    notifications.STORE.clear()
    try:
        yield
    finally:
        bar = _STATE["window"].notice_bar if "window" in _STATE else None
        if bar is not None and bar.panel is not None:
            bar.panel.close()
        notifications.STORE.clear()
        _pump(0.2)


def test_the_indicators_stand_between_the_views_and_the_languages():
    """Issue #11: right of the views' switch -- the «modes» of the issue (D-005) --, left of the languages; until then left of both (07.10.2026)."""
    window, _here = _window()
    layout = window.centralWidget().layout().itemAt(0).layout()
    widgets = [layout.itemAt(i).widget() for i in range(layout.count())]
    assert widgets.index(window.view_switch) < widgets.index(window.notice_bar) < widgets.index(window.language)
    bar = window.notice_bar
    order = [bar.layout().itemAt(i).widget() for i in range(bar.layout().count())]
    assert order == [bar.activity, bar.indicators["critical"], bar.indicators["warning"]], "loading, then 🛑, then ⚠"
    assert not bar.activity.isVisible() and bar.activity.sizePolicy().retainSizeWhenHidden(), "the chip keeps its room: the bar never moves"


def test_an_indicator_is_quiet_at_zero_blinks_three_seconds_and_stays_coloured():
    window, _here = _window()
    with _clean():
        bar = window.notice_bar
        critical = bar.indicators["critical"]
        _pump(0.3)
        assert critical.count == 0 and not critical.lit() and not critical.blinking()
        notifications.report("calc_failed", "the calculation failed", notifications.CRITICAL, source="test")
        _pump(0.3)
        assert critical.count == 1 and critical.blinking(), "a new error blinks"
        assert bar.indicators["warning"].count == 0, "the other indicator is untouched"
        assert "1" in critical.toolTip()
        _pump(3.0)
        assert not critical.blinking() and critical.lit(), "after about 3 s it stops blinking and stays coloured"
        notifications.report("calc_failed", "the calculation failed", notifications.CRITICAL, source="test")
        _pump(0.3)
        assert critical.count == 1 and critical.blinking(), "the same error again: still one, blinking again"
        notifications.report("calc_failed", "another calculation failed", notifications.CRITICAL, source="test")
        _pump(0.3)
        assert critical.count == 2 and critical.toolTip() == bar.t("notice_critical_tip", n=2), critical.toolTip()
        notifications.STORE.clear()
        _pump(0.3)
        assert critical.count == 0 and not critical.lit(), "all deleted: quiet again"


def test_the_panel_opens_under_the_indicators_inside_the_window_and_scrolls():
    window, _here = _window()
    with _clean():
        for i in range(50):
            notifications.report(f"w{i}", f"warning number {i} " + "very long words " * 12, notifications.WARNING, source="test")
        notifications.report("c", "one error", notifications.CRITICAL)
        _pump(0.3)
        bar = window.notice_bar
        bar.indicators["warning"].click()
        _pump(0.3)
        panel = bar.panel
        assert panel is not None and panel.isVisible() and panel.filter == "warning"
        frame = window.frameGeometry()
        inside = window.geometry()
        geometry = panel.geometry()
        assert inside.contains(geometry.topLeft()) and inside.contains(geometry.bottomRight()), (geometry, inside, frame)
        anchor = bar.mapToGlobal(bar.rect().bottomLeft())
        assert geometry.top() >= anchor.y(), "under the indicators"
        assert geometry.height() <= window.height() * 0.7 + 1
        assert panel.scroll.verticalScrollBar().maximum() > 0, "fifty notices scroll"
        rows = [panel.rows.itemAt(i).widget() for i in range(panel.rows.count()) if panel.rows.itemAt(i).widget() is not None]
        assert sum(type(r).__name__ == "NoticeRow" for r in rows) == 50, "the warnings alone, as the triangle was clicked"
        panel.set_filter("all")
        rows = [panel.rows.itemAt(i).widget() for i in range(panel.rows.count()) if type(panel.rows.itemAt(i).widget()).__name__ == "NoticeRow"]
        assert len(rows) == 51


def test_a_row_opens_copies_deletes_and_offers_its_file_only_where_it_exists():
    from PySide6.QtGui import QGuiApplication
    window, here = _window()
    with _clean():
        real = here.root / "report-under-test.typ"
        real.write_text("#foo\n", encoding="utf-8")
        long_path = os.path.join(os.path.abspath(os.sep), *["un-dossier-au-nom-tres-long"] * 10, "rapport.typ")
        notifications.report_typst(f"error: unknown variable: foo\n  ┌─ {real}:1:2\n", source="compile")
        notifications.report("typst_error", "Typst failed", notifications.CRITICAL, file=long_path, line=183, column=14, technical="error: x", args={"message": "x"})
        _pump(0.3)
        bar = window.notice_bar
        bar.show_panel("critical")
        _pump(0.2)
        panel = bar.panel
        rows = [panel.rows.itemAt(i).widget() for i in range(panel.rows.count()) if type(panel.rows.itemAt(i).widget()).__name__ == "NoticeRow"]
        by_file = {row.notice.file: row for row in rows}
        missing, present = by_file[long_path], by_file[str(real)]
        missing.toggle()
        assert missing.open and missing.details.isVisibleTo(panel)
        assert missing.open_button is not None and not missing.open_button.isEnabled() and long_path in missing.open_button.toolTip()
        assert present.open_button is not None and present.open_button.isEnabled()
        from PySide6.QtWidgets import QLabel
        shown = missing.findChild(QLabel, "noticeFile")
        assert shown is not None and "…" in shown.text() and shown.toolTip().startswith(long_path), "a long path is cut in its middle, whole in its tooltip"
        missing.copy()
        copied = QGuiApplication.clipboard().text()
        for part in ("[critical]", f"{long_path}:183:14", "error: x", "Woodcore:"):
            assert part in copied, (part, copied)
        panel.delete(missing.notice.id)
        _pump(0.3)
        assert notifications.STORE.get(missing.notice.id) is None and bar.indicators["critical"].count == 1
        panel.clear()
        _pump(0.3)
        assert bar.indicators["critical"].count == 0
        real.unlink()


def test_the_words_follow_the_window_s_language_and_the_bar_survives_a_rebuild():
    window, _here = _window()
    language = window.lang
    with _clean():
        notifications.report_typst("error: unknown variable: foo\n  ┌─ report.typ:3:1\n", source="compile")
        (notice,) = notifications.STORE.items()
        try:
            for lang, title in (("fr", "Compilation Typst impossible"), ("de", "Typst-Kompilierung unmöglich"), ("en", "Typst compilation failed")):
                assert notifications.title(notice, lang) == title, lang
            window.lang = "de"
            window.rebuild()
            _pump(0.3)
            assert window.notice_bar.indicators["critical"].count == 1, "the store outlives the bar made again"
            window.notice_bar.show_panel("critical")
            _pump(0.2)
            panel = window.notice_bar.panel
            row = next(panel.rows.itemAt(i).widget() for i in range(panel.rows.count()) if type(panel.rows.itemAt(i).widget()).__name__ == "NoticeRow")
            from PySide6.QtWidgets import QLabel
            texts = [label.text() for label in row.findChildren(QLabel)]   # the title is a plain label, the message under it an ElidedLabel (issue #11)
            assert "Typst-Kompilierung unmöglich" in texts, texts
            assert "unknown variable: foo" in notice.technical, "the technical text is Typst's own"
        finally:
            window.lang = language
            window.rebuild()


def test_an_exception_nobody_caught_is_a_critical_notice_not_a_box():
    import notices_ui
    import threading
    window, _here = _window()
    saved = (sys.excepthook, threading.excepthook, list(notices_ui._installed))
    notices_ui._installed.clear()
    try:
        with _clean():
            notices_ui.install_hooks()
            try:
                raise ValueError("boom in a slot")
            except ValueError:
                sys.excepthook(*sys.exc_info())
            thread = threading.Thread(target=lambda: 1 / 0, name="worker")
            thread.start()
            thread.join()
            _pump(0.3)
            texts = [n.text for n in notifications.STORE.items(notifications.CRITICAL)]
            assert any("boom in a slot" in t for t in texts) and any("ZeroDivisionError" in t for t in texts), texts
            assert window.notice_bar.indicators["critical"].count == 2
    finally:
        sys.excepthook, threading.excepthook = saved[0], saved[1]
        notices_ui._installed[:] = saved[2]


def test_a_closed_row_shows_much_of_its_message_and_all_of_it_opened():
    """Issue #11: «seuls les deux premiers mots du message sont visibles» -- the summary was one line, cut at the width the row had before the panel had its own. Closed it shows up to three lines at the row's width; opened, the whole."""
    window, _here = _window()
    words = " ".join(f"mot{i}" for i in range(40))
    with _clean():
        notifications.report("typst_error", words, notifications.CRITICAL, args={"message": words})
        _pump(0.3)
        bar = window.notice_bar
        bar.show_panel("critical")
        _pump(0.3)
        panel = bar.panel
        row = next(panel.rows.itemAt(i).widget() for i in range(panel.rows.count()) if type(panel.rows.itemAt(i).widget()).__name__ == "NoticeRow")
        assert row.summary.width() > 300, f"the summary laid out at {row.summary.width()} px in a {panel.width()} px panel"
        # how many words three lines hold is the font's (the offscreen platform's is wide); what is kept is the row's whole width filled on three lines, where the defect showed two words on one
        lines = row.summary.text().splitlines()
        metrics = row.summary.fontMetrics()
        assert len(lines) == 3 and lines[-1].endswith("…"), f"closed, three lines and an ellipsis: {row.summary.text()!r}"
        for line in lines[:2]:
            assert metrics.horizontalAdvance(line) >= 0.75 * row.summary.contentsRect().width(), f"a line laid out narrower than the row: {line!r} in {row.summary.contentsRect().width()} px"
        shown = [w for w in row.summary.text().replace("…", " ").split() if w.startswith("mot")]
        assert len(shown) >= 10, f"closed, the row shows {len(shown)} of 40 words: {row.summary.text()!r}"
        row.toggle()
        _pump(0.1)
        from PySide6.QtWidgets import QLabel
        whole = [label.text() for label in row.details.findChildren(QLabel)]
        assert any(words in text for text in whole), "opened, the whole message"


def test_a_notice_is_copied_by_its_menu_by_ctrl_c_and_all_of_them_at_once():
    """Issue #11: «permettre de copier-coller les erreurs» -- without opening the row: Ctrl+C on it, its menu's «Copier», and «Tout copier» for every notice shown."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtTest import QTest
    window, _here = _window()
    with _clean():
        notifications.report("typst_error", "first", notifications.CRITICAL, args={"message": "premier message"})
        notifications.report("typst_error", "second", notifications.CRITICAL, args={"message": "second message"}, file="C:/x/autre.typ")
        _pump(0.3)
        bar = window.notice_bar
        bar.show_panel("critical")
        _pump(0.3)
        panel = bar.panel
        rows = [panel.rows.itemAt(i).widget() for i in range(panel.rows.count()) if type(panel.rows.itemAt(i).widget()).__name__ == "NoticeRow"]
        assert len(rows) == 2
        QGuiApplication.clipboard().setText("")
        QTest.keyClick(rows[0], Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
        copied = QGuiApplication.clipboard().text()
        assert "[critical]" in copied and rows[0].notice.code in copied and not rows[0].open, copied
        assert panel.copy_all_button.isEnabled()
        panel.copy_all_button.click()
        both = QGuiApplication.clipboard().text()
        assert "premier message" in both and "second message" in both and both.count("[critical]") == 2, both
        assert rows[0].summary.textInteractionFlags() & Qt.TextInteractionFlag.TextSelectableByMouse, "the summary can be selected with the mouse"


def test_copy_all_joins_the_notices_and_names_the_context_once():
    """notifications.copy_all, without Qt."""
    a = notifications.Notice("typst_error", notifications.CRITICAL, "a")
    b = notifications.Notice("typst_error", notifications.CRITICAL, "b")
    text = notifications.copy_all([a, b], "fr", {"Woodcore": "0.117"})
    assert text.count("Woodcore: 0.117") == 1 and text.count("[critical]") == 2, text
