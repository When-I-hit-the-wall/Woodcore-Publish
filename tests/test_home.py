"""Woodcore's start page, its File menu, its title and a project opened read-only (calc/tools/home_page.py, woodcore_gui.py, usersettings.py; v0.83, docs/ui/window.md §10quater).

The start page lists the projects opened lately, greys one that is no longer where it was, and opens what is chosen or dropped on it. The window names its project first, «•» before it while a tab holds unsaved changes; its File menu opens another project in a process of its own; a project another window holds is opened read-only and saves nothing. The settings the window kept before v0.83, when it was the Typst-Katalog, are taken over once, and the tests never write the engineer's own. «Nouveau projet» and the properties of a project -- the layout and the content templates -- are tests/test_project_dialog.py's.

⚠️ Built off-screen, and every message box a check would meet is replaced first: a modal off-screen never comes back.
"""

import os
import subprocess
import sys

import conftest
from conftest import ROOT

import project

TOOLS = ROOT / "calc" / "tools"


def _qt():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


# --- the user's settings -------------------------------------------------------------------

def test_the_recent_projects_are_the_last_first_once_each_and_a_dozen_at_most():
    _qt()
    import usersettings
    root = conftest.tmpdir("recent").resolve()
    first = str(root / "A" / "A.woodcore")
    settings = {"last_project": first}
    assert usersettings.recent_projects(settings) == [first], "v0.82's last_project is the first recent project"
    for n in range(20):
        usersettings.remember(settings, root / f"P{n}" / f"P{n}.woodcore")
    p3 = str(root / "P3" / "P3.woodcore")
    same = lambda p: os.path.normcase(p) == os.path.normcase(p3)
    # Windows' file names know no case: the same project written otherwise is still one
    usersettings.remember(settings, p3.upper() if os.name == "nt" else p3)
    recent = usersettings.recent_projects(settings)
    assert len(recent) == usersettings.RECENT_MAX and "last_project" not in settings
    assert same(recent[0]) and sum(same(p) for p in recent) == 1
    usersettings.forget(settings, p3)
    assert not any(same(p) for p in usersettings.recent_projects(settings))


def test_the_settings_of_before_v0_83_are_taken_over_once():
    _qt()
    import usersettings
    base = conftest.tmpdir("migrate")
    saved = {k: os.environ.get(k) for k in ("APPDATA", "LOCALAPPDATA", usersettings.ENV)}
    try:
        os.environ["APPDATA"], os.environ["LOCALAPPDATA"] = str(base / "Roaming"), str(base / "Local")
        os.environ.pop(usersettings.ENV)
        old = base / "Roaming" / "typst-katalog" / "settings.json"
        old.parent.mkdir(parents=True)
        old.write_text('{"lang": "de", "size": "1000x700"}', encoding="utf-8")
        renders = base / "Local" / "typst-katalog" / "renders"
        renders.mkdir(parents=True)
        (renders / "page.png").write_bytes(b"png")
        moved = usersettings.migrate()
        assert usersettings.settings_file() == base / "Roaming" / "Woodcore" / "settings.json"
        assert usersettings.read() == {"lang": "de", "size": "1000x700"}, moved
        assert (base / "Local" / "Woodcore" / "renders" / "page.png").is_file() and not renders.exists()
        assert old.is_file(), "the old settings are left where they were"
        usersettings.write({"lang": "fr"})
        old.write_text('{"lang": "en"}', encoding="utf-8")
        usersettings.migrate()
        assert usersettings.read() == {"lang": "fr"}, "the old settings were taken over a second time"
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    assert usersettings.settings_file() == conftest.SETTINGS


# --- the start page ------------------------------------------------------------------------

def test_the_start_page_lists_the_recent_projects_and_drops_one_gone():
    """A recent project whose file is gone is taken off the list as the page is drawn, and written so (the engineer's decision of 03.10.2026, where it was greyed and offered to be forgotten until then); one that goes while the page is open is taken off when it is chosen, and said."""
    _qt()
    import home_page
    import usersettings
    from PySide6.QtGui import QPalette
    from PySide6.QtWidgets import QMessageBox
    gone = conftest.tmpdir("home_gone") / "Weg.woodcore"
    saved = usersettings.read()
    usersettings.write({"lang": "en", "recent_projects": [str(conftest.PROJECT.file), str(gone)]})
    import notifications
    opened = []
    notifications.STORE.clear()
    try:
        page = home_page.HomeWindow(lambda file: opened.append(file) or False)
        rows = [page.list.topLevelItem(i) for i in range(page.list.topLevelItemCount())]
        assert [r.text(0) for r in rows] == ["Exemple"], [r.text(0) for r in rows]
        assert usersettings.recent_projects(usersettings.read()) == [str(conftest.PROJECT.file)], "the project gone was not written off the list"
        assert rows[0].text(4) == project.VERSION, "the engine the export was written with"
        muted = page.palette().color(QPalette.ColorRole.PlaceholderText)
        assert rows[0].foreground(0).color() != muted
        page.open_item(rows[0])
        assert opened == [str(conftest.PROJECT.file)]
        # one that goes while the page is open
        gone.write_bytes(conftest.PROJECT.file.read_bytes())
        usersettings.write({"lang": "en", "recent_projects": [str(gone), str(conftest.PROJECT.file)]})
        page.settings = usersettings.read()
        page.fill()
        assert page.list.topLevelItemCount() == 2
        gone.unlink()
        page.open_item(page.list.topLevelItem(0))
        told = [n for n in notifications.STORE.items() if n.key == "home_missing_gone"]   # said under the start page's triangle since v0.117, no box
        assert told and opened == [str(conftest.PROJECT.file)], "a project gone was opened"
        assert usersettings.recent_projects(usersettings.read()) == [str(conftest.PROJECT.file)]
        assert page.list.topLevelItemCount() == 1
        page.close()
    finally:
        notifications.STORE.clear()
        usersettings.write(saved)


def _patched(obj, **values):
    import contextlib

    @contextlib.contextmanager
    def patch():
        saved = {name: getattr(obj, name) for name in values}
        for name, value in values.items():
            setattr(obj, name, value)
        try:
            yield
        finally:
            for name, value in saved.items():
                setattr(obj, name, value)
    return patch()


def test_a_woodcore_file_dropped_is_recognised_and_nothing_else():
    _qt()
    import home_page
    from PySide6.QtCore import QMimeData, QUrl
    mime = QMimeData()
    folder = conftest.tmpdir("dropped")
    mime.setUrls([QUrl.fromLocalFile(str(folder / "notes.txt")), QUrl.fromLocalFile(str(folder / "Halle.woodcore"))])
    assert [os.path.basename(f) for f in home_page.woodcore_files(mime)] == ["Halle.woodcore"]
    empty = QMimeData()
    empty.setText("Halle.woodcore")
    assert home_page.woodcore_files(empty) == []


def test_the_installed_versions_are_listed_newest_first():
    _qt()
    import home_page
    root = conftest.tmpdir("installed")
    for version in ("0.83.0", "0.9.1", "0.83.2", "notes"):
        (root / version).mkdir()
        (root / version / "Woodcore.exe").write_bytes(b"")
    (root / "launcher").mkdir()
    assert home_page.installed_versions(root) == ["0.83.2", "0.83.0", "0.9.1"]


# --- the window -----------------------------------------------------------------------------

_window = None


def _main_window():
    global _window
    if _window is None:
        conftest.exported("calculations.json")
        _qt()
        import woodcore_gui
        _window = woodcore_gui.MainWindow()
    return _window


def test_the_window_names_its_project_and_marks_what_is_unsaved():
    window = _main_window()
    assert window.windowTitle() == "Exemple — Woodcore", window.windowTitle()
    tab = next(t for t in window.tabs if hasattr(t, "dirty"))
    tab.dirty = True
    try:
        window.update_tab_marks()
        assert window.windowTitle() == "• Exemple — Woodcore", window.windowTitle()
    finally:
        tab.dirty = False
        window.update_tab_marks()
    assert window.windowTitle() == "Exemple — Woodcore"


def test_the_file_menu_holds_what_a_project_is_opened_and_closed_with():
    window = _main_window()
    menu = window.menuBar().actions()[0].menu()
    texts = [a.text() for a in menu.actions() if not a.isSeparator()]
    for key in ("file_new", "file_open", "file_recent", "file_open_window", "file_close", "file_properties", "file_show_folder", "file_open_pdf", "file_open_vscode", "file_quit"):
        assert window.t(key) in texts, (key, texts)
    if not getattr(sys, "frozen", False):
        assert window.t("file_dev") in texts, "the choice of the sources for a double-click is offered from the sources"


def test_opening_another_project_waits_for_an_export_and_starts_a_process_of_its_own():
    _qt()
    import woodcore_gui
    from PySide6.QtWidgets import QMessageBox
    window = _main_window()
    import notifications
    said = []
    status = window.set_status
    window.set_status = lambda text: said.append(text)   # an information is a line of the status bar since v0.117, no box
    started = []
    relaunch = woodcore_gui.relaunch
    woodcore_gui.relaunch = lambda args: started.append(args)
    window.process = object()
    try:
        assert window.switch_to(["--home"]) is False
        window.notice_bar.refresh()
        assert window.t("file_busy") in said and not started, "a project was changed under a running export"
    finally:
        window.process = None
        window.set_status = status
        notifications.STORE.clear()
        woodcore_gui.relaunch = relaunch
    program, arguments = woodcore_gui.relaunch_command(["--project", "X.woodcore"])
    assert arguments[-2:] == ["--project", "X.woodcore"] and arguments[0].endswith("woodcore_gui.py"), arguments
    program, arguments = woodcore_gui.cli_command(["export", "--data-only"])
    assert arguments[0].endswith("cli.py") and arguments[1:] == ["export", "--data-only"], arguments


def test_a_project_opened_read_only_saves_nothing_and_exports_nothing():
    _qt()
    import woodcore_gui
    window = woodcore_gui.MainWindow(read_only=True, holder={"user": "kollege", "host": "ANDERER-PC"})
    refused = []
    window.refuse_read_only = lambda: refused.append(True)
    try:
        assert window.windowTitle().endswith(f"({window.t('read_only_suffix')})"), window.windowTitle()
        before = {p: p.read_bytes() for p in project.current().sources_dir.rglob("*.json")}
        before_file = project.current().file.read_bytes()
        for tab in window.tabs:
            if hasattr(tab, "save") and hasattr(tab, "dirty"):
                tab.dirty = True
                assert tab.save() is False, type(tab).__name__
                tab.dirty = False
        window.reexport()
        window.export_pdf()
        assert window.process is None, "an export ran in a project opened read-only"
        window.save_folder_settings("tab_plan", ["Leer"])
        assert project.current().file.read_bytes() == before_file, "a window opened read-only wrote into the project file"
        assert {p: p.read_bytes() for p in project.current().sources_dir.rglob("*.json")} == before
        assert len(refused) >= 5, refused
    finally:
        for tab in window.tabs:
            if hasattr(tab, "dirty"):
                tab.dirty = False
        conftest.dispose(window)
    assert not project.current().file.with_name(project.current().file.name + ".lock").exists(), "a window opened read-only wrote or kept a lock"


def test_woodcore_opens_a_project_and_quits_when_it_is_only_checked():
    """`--self-test` is what the build checks an installed Woodcore with: 0 where the project opened, 1 where it did not."""
    _qt()
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONUTF8="1")
    run = subprocess.run([sys.executable, str(TOOLS / "woodcore_gui.py"), "--project", str(project.current().file), "--self-test"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=180)
    assert run.returncode == 0, run.stdout + run.stderr
    assert not project.current().file.with_name(project.current().file.name + ".lock").exists(), "the window left its lock behind"
    missing = conftest.tmpdir("self_test") / "Nichts.woodcore"
    run = subprocess.run([sys.executable, str(TOOLS / "woodcore_gui.py"), "--project", str(missing), "--self-test"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=180)
    assert run.returncode == 1, run.stdout + run.stderr


def test_every_writer_an_editor_tab_reaches_is_guarded_wherever_it_is_defined():
    """The read-only guard wraps by name the writers of each editor tab (woodcore_gui.WRITERS). Cut into mixins (issue #30), a tab defines many of them in a mixin: `vars(tab)` alone would have left `write_title`, `rename_id`, `delete_document` and a member check's `save` unguarded, a project held read-only then written. Every writer a tab reaches outside Qt is the guarded one."""
    _qt()
    import woodcore_gui
    unguarded = []
    for tab in woodcore_gui.GUARDED_TABS:
        for name in woodcore_gui.WRITERS:
            method = getattr(tab, name, None)
            if method is None or not callable(method):
                continue
            owner = next(k for k in tab.__mro__ if name in vars(k))
            if owner.__module__.startswith(("PySide6", "shiboken6")):
                continue
            if not hasattr(method, "__wrapped__"):
                unguarded.append(f"{tab.__name__}.{name} (defined in {owner.__name__})")
    assert not unguarded, unguarded
