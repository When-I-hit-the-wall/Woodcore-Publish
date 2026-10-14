"""The project's engine, looked at as the project opens (woodcore_gui.check_engine, v0.87; docs/ui/window.md §10quater, docs/conventions/build-and-release.md §12).

The engineer: «lors de l'ouverture d'un projet qui tourne sur un ancien moteur, un message demande si le user veut uploader le moteur à la dernière version». Until v0.87 the project's copy of the engine was compared with the program's only when an export ran (engine_consent). Now the window compares them once it is up, by project.engine_state: current, nothing; absent or another build of this version, copied without a word and said in the status bar; written by an older version, by none a VERSION names, or edited by hand, asked -- «Plus tard» writing nothing and asking again at the next opening; written by a newer Woodcore, said. A project opened read-only is asked nothing and written nothing. The question is the export's own box (engine_box), so the two cannot say different things.

Each check works on a copy of the example project (conftest.project_copy), whose engine starts absent. ⚠️ Built off-screen, and every modal replaced first: a modal off-screen never comes back.
"""

import json
import os
import sys

import conftest
from conftest import ROOT

import project
from test_project import _stamp

TOOLS = ROOT / "calc" / "tools"
_MISSING = object()


def _qt():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


_window = None


def _main_window():
    global _window
    if _window is None:
        conftest.exported("calculations.json")
        _qt()
        import woodcore_gui
        _window = woodcore_gui.MainWindow()
    return _window


class Answers:
    """Stands in for every box a check may show: a question (QMessageBox.exec) is answered by clicking the buttons named, in order, and recorded with its text and its buttons; an information or a warning is recorded; the differences' window (QDialog.exec) records the text it shows. A box nothing expected fails the check rather than waiting for a click that never comes."""

    def __init__(self, *clicks):
        self.clicks = list(clicks)
        self.questions, self.told, self.warned, self.diffs = [], [], [], []

    def __enter__(self):
        from PySide6.QtWidgets import QDialog, QMessageBox, QPlainTextEdit
        answers = self

        def question(box):
            answers.questions.append((box.text(), [b.text() for b in box.buttons()]))
            assert answers.clicks, f"a question nothing expected was asked: {box.text()!r}"
            wanted = answers.clicks.pop(0)
            button = next((b for b in box.buttons() if b.text() == wanted), None)
            assert button is not None, (wanted, [b.text() for b in box.buttons()])
            button.click()
            return 0

        def dialog(window):
            view = window.findChild(QPlainTextEdit)
            answers.diffs.append(view.toPlainText() if view is not None else "")
            return 0

        self.saved = [(cls, name, cls.__dict__.get(name, _MISSING)) for cls, name in
                      ((QMessageBox, "exec"), (QMessageBox, "information"), (QMessageBox, "warning"), (QMessageBox, "critical"), (QDialog, "exec"))]
        QMessageBox.exec = question
        QMessageBox.information = staticmethod(lambda *args, **kwargs: answers.told.append(args[2]))
        QMessageBox.warning = staticmethod(lambda *args, **kwargs: answers.warned.append(args[2]))
        QMessageBox.critical = staticmethod(lambda *args, **kwargs: answers.warned.append(args[2]))
        QDialog.exec = dialog
        # what was a box is a notice since v0.117: an information is told, an error or a warning warned
        import conftest
        self.said = conftest.notices_said(lambda notice: (answers.told if notice.severity == "info" else answers.warned).append(notice.text))
        self.said.__enter__()
        return self

    def __exit__(self, *exc):
        self.said.__exit__(None, None, None)
        for cls, name, value in self.saved:
            if value is _MISSING:
                delattr(cls, name)
            else:
                setattr(cls, name, value)
        return False


def _engine_files(here):
    """Every file of the project's generated folder but its export, by content: what a check that writes nothing must leave as it was."""
    root = here.generated_dir
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*")
            if p.is_file() and p.relative_to(root).parts[0] != "data"}


def _without_retired_keys(here):
    """The copy's project file without the keys of a retired feature (project.RETIRED_KEYS): the example keeps them on purpose (test_retired_features), and the window warns of each as the project opens -- a notice these checks, which ask that opening says nothing about the engine, are not about. The file is a test copy, so it is rewritten whole."""
    data = json.loads(here.file.read_text(encoding="utf-8"))
    for section, key in project.RETIRED_KEYS:
        data.get(section, {}).pop(key, None)
        here.data.get(section, {}).pop(key, None)
    here.file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert not here.retired_keys(), here.retired_keys()


def _copy(name, state):
    """A copy of the example project whose engine stands in `state`, built as test_project builds each one."""
    here = conftest.project_copy(name)
    _without_retired_keys(here)
    if state == "absent":
        return here
    project.sync_engine(here)
    if state == "stale":
        _stamp(here, project.VERSION, **{"lib/formula.typ": "// another build\n"})
    elif state == "older":
        _stamp(here, "0.70.0", **{"lib/formula.typ": "// an older version\n"})
    elif state == "newer":
        _stamp(here, "9.0.0")
    elif state == "unknown":
        (here.generated_dir / project.ENGINE_STAMP).unlink()
    elif state == "edited":
        copy = here.generated_dir / "lib" / "formula.typ"
        os.chmod(copy, 0o666)
        copy.write_text(copy.read_text(encoding="utf-8") + "// edited by hand\n", encoding="utf-8")
    assert project.engine_state(here)[0] == state, (state, project.engine_state(here))
    return here


def _check(window, here, *clicks):
    """The window's check run on `here`, the status bar emptied first; returns the Answers it met."""
    window.set_status("")
    with project.using(here), Answers(*clicks) as answers:
        window.check_engine()
    assert not answers.clicks, f"questions expected and not asked: {answers.clicks}"
    return answers


def test_a_current_engine_is_left_alone_and_nothing_is_said():
    window = _main_window()
    here = _copy("engine_open_current", "current")
    before = _engine_files(here)
    answers = _check(window, here)
    assert not (answers.questions or answers.told or answers.warned), (answers.questions, answers.told, answers.warned)
    assert window.status.text() == "" and _engine_files(here) == before


def test_an_absent_or_stale_engine_is_copied_without_a_word_and_said_in_the_status_bar():
    window = _main_window()
    for state in ("absent", "stale"):
        here = _copy(f"engine_open_{state}", state)
        answers = _check(window, here)
        assert not (answers.questions or answers.told or answers.warned), (state, answers.questions, answers.told)
        assert project.engine_state(here)[0] == "current", state
        assert window.status.text() == window.t("engine_synced", ours=project.VERSION), (state, window.status.text())


def test_an_older_engine_is_asked_about_and_later_writes_nothing_and_asks_again():
    window = _main_window()
    here = _copy("engine_open_older", "older")
    before = _engine_files(here)
    answers = _check(window, here, window.t("engine_later"))
    text, buttons = answers.questions[0]
    assert text == window.t("engine_older", version="0.70.0", ours=project.VERSION), text
    assert sorted(buttons) == sorted([window.t("engine_update_now"), window.t("engine_diff"), window.t("engine_later")]), buttons
    assert _engine_files(here) == before and project.engine_state(here)[0] == "older", "«Plus tard» wrote into the project"
    assert window.status.text() == ""
    # the next opening asks again; the differences are shown and the same question comes back
    answers = _check(window, here, window.t("engine_diff"), window.t("engine_later"))
    assert len(answers.questions) == 2 and len(answers.diffs) == 1, (answers.questions, len(answers.diffs))
    assert "-// an older version" in answers.diffs[0], answers.diffs[0][:300]
    assert _engine_files(here) == before
    # and a yes replaces it
    _check(window, here, window.t("engine_update_now"))
    assert project.engine_state(here)[0] == "current"
    assert window.status.text() == window.t("engine_synced", ours=project.VERSION)


def test_an_engine_no_version_names_is_asked_about_like_an_older_one():
    window = _main_window()
    here = _copy("engine_open_unknown", "unknown")
    detail = project.engine_state(here)[1]
    answers = _check(window, here, window.t("engine_update_now"))
    assert answers.questions[0][0] == window.t("engine_unknown", files=detail, ours=project.VERSION), answers.questions
    assert project.engine_state(here)[0] == "current"


def test_an_edited_engine_is_asked_with_the_edited_wording_and_overwritten_only_on_a_yes():
    window = _main_window()
    here = _copy("engine_open_edited", "edited")
    copy = here.generated_dir / "lib" / "formula.typ"
    answers = _check(window, here, window.t("engine_later"))
    text, buttons = answers.questions[0]
    assert text == window.t("engine_edited", files="lib/formula.typ", ours=project.VERSION), text
    assert sorted(buttons) == sorted([window.t("engine_overwrite_now"), window.t("engine_diff"), window.t("engine_later")]), buttons
    assert copy.read_text(encoding="utf-8").endswith("// edited by hand\n"), "an engine edited by hand was overwritten on «Plus tard»"
    _check(window, here, window.t("engine_overwrite_now"))
    assert "edited by hand" not in copy.read_text(encoding="utf-8") and project.engine_state(here)[0] == "current"


def test_a_newer_engine_is_said_and_never_replaced():
    window = _main_window()
    here = _copy("engine_open_newer", "newer")
    before = _engine_files(here)
    answers = _check(window, here)
    assert answers.told == [window.t("engine_newer_open", version="9.0.0", ours=project.VERSION)], answers.told
    assert not answers.questions and _engine_files(here) == before


def test_the_export_asks_the_same_question_with_its_own_buttons():
    """engine_consent and check_engine share engine_box: the same sentence, the export's buttons."""
    window = _main_window()
    here = _copy("engine_export_older", "older")
    with project.using(here), Answers(window.t("engine_update")) as answers:
        assert window.engine_consent() == ["--update-engine"]
    text, buttons = answers.questions[0]
    assert text == window.t("engine_older", version="0.70.0", ours=project.VERSION)
    assert len(buttons) == 3 and window.t("engine_update") in buttons and window.t("engine_diff") in buttons and window.t("engine_later") not in buttons, buttons
    cancel = next(b for b in buttons if b not in (window.t("engine_update"), window.t("engine_diff")))  # Qt's own «Cancel», in the window's language
    with project.using(here), Answers(window.t("engine_diff"), cancel) as answers:
        assert window.engine_consent() is None, "the export went ahead on «Annuler»"
    assert len(answers.diffs) == 1 and project.engine_state(here)[0] == "older", "the export's own question wrote into the project"


def test_a_project_opened_read_only_is_asked_nothing_and_written_nothing():
    window = _main_window()
    here = _copy("engine_open_read_only", "older")
    before = _engine_files(here)
    window.read_only = True
    try:
        answers = _check(window, here)
    finally:
        window.read_only = False
    assert not (answers.questions or answers.told or answers.warned) and _engine_files(here) == before


def _later_in_the_window_s_language():
    """«Plus tard» as the window about to open will say it -- its language is the user's settings', which the tests seed in English."""
    import woodcore_gui
    settings = woodcore_gui.read_settings()
    lang = settings.get("lang") if settings.get("lang") in woodcore_gui.LANGUAGES else "fr"
    return woodcore_gui.STRINGS[lang]["engine_later"]


def _open(here, *clicks, lock_answer=None):
    """open_project on `here`, as the start page, the File menu and a double-click do, and the queued checks run: returns (the window, the Answers met). What opening a project installs in the process for good -- the stall watch, the error box's excepthook -- is kept out, the dependencies' check, which asks PyPI, is stood down, and so is the offer of a migration into three documents, which a project laid out as one report -- the example -- is asked before its window is built (migrate_dialog.py; tests/test_modes_window.py holds it)."""
    app = _qt()
    import woodcore_gui
    import home_page
    import migrate_dialog
    saved = (sys.excepthook, list(woodcore_gui._WATCHING), woodcore_gui.MainWindow.__dict__.get("check_dependencies"), home_page.ask_lock, migrate_dialog.offer)
    woodcore_gui._WATCHING.append(True)
    woodcore_gui.MainWindow.check_dependencies = lambda self: None
    home_page.ask_lock = lambda *args, **kwargs: lock_answer
    migrate_dialog.offer = lambda *args, **kwargs: "postponed"
    try:
        with Answers(*clicks) as answers:
            window = woodcore_gui.open_project(app, here.file)
            assert window is not None
            asked_before = list(answers.questions)
            app.processEvents()
        assert not asked_before, "the engine was asked about before the window was up"
    finally:
        sys.excepthook = saved[0]
        woodcore_gui._WATCHING[:] = saved[1]
        woodcore_gui.MainWindow.check_dependencies = saved[2]
        home_page.ask_lock = saved[3]
        migrate_dialog.offer = saved[4]
    return window, answers


def _close(window):
    import woodcore_gui
    conftest.dispose(window)
    if window in woodcore_gui._WINDOWS:
        woodcore_gui._WINDOWS.remove(window)


def test_opening_a_project_asks_about_its_engine_once_the_window_is_up():
    _qt()
    import project_lock
    here = _copy("engine_open_project", "older")
    before = _engine_files(here)
    with project.using(here):
        window, answers = _open(here, _later_in_the_window_s_language())
        try:
            assert len(answers.questions) == 1, answers.questions
            assert answers.questions[0][0] == window.t("engine_older", version="0.70.0", ours=project.VERSION)
            assert _engine_files(here) == before
        finally:
            _close(window)
    assert project_lock.read(here) is None, "the window left its lock behind"


def test_opening_a_project_read_only_asks_nothing_about_its_engine():
    _qt()
    import json
    import project_lock
    here = _copy("engine_open_project_ro", "older")
    project_lock.lock_path(here).write_text(json.dumps({"user": "kollege", "host": "ANDERER-PC", "pid": 4242, "since": "2026-09-22T08:00:00"}), encoding="utf-8")
    before = _engine_files(here)
    with project.using(here):
        window, answers = _open(here, lock_answer="read_only")
        try:
            assert window.read_only and not (answers.questions or answers.told or answers.warned), (answers.questions, answers.told)
            assert _engine_files(here) == before
        finally:
            _close(window)
    assert project_lock.read(here)["host"] == "ANDERER-PC", "a window opened read-only touched the other window's lock"


def test_opening_a_project_a_newer_woodcore_wrote_opens_it_read_only():
    """The engineer, v0.87: yes to opening read-only a project whose engine a newer Woodcore wrote. Until then only its export was refused, and a drawing saved from one of its tabs re-exported its part of data/ with this older code. The window says why in its banner, asks nothing, writes nothing, and holds no lock."""
    _qt()
    import project_lock
    here = _copy("engine_open_project_newer", "newer")
    before = _engine_files(here)
    with project.using(here):
        window, answers = _open(here)
        try:
            assert window.read_only and window.newer == "9.0.0", (window.read_only, window.newer)
            assert not (answers.questions or answers.told or answers.warned), (answers.questions, answers.told)
            assert project_lock.read(here) is None, "a window that writes nothing held the project's lock"
            assert _engine_files(here) == before
            assert window.t("read_only_newer_banner", version="9.0.0", ours=project.VERSION)
        finally:
            _close(window)

