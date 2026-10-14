"""Saving without a question (v0.117, calc/tools/autosave.py; spec docs/requirements/active/2026-10-07-vues-onglets-slider-et-volets.md, REQ-001, REQ-002, ARCH-004).

The engineer, 07.10.2026: «Lorsqu'on change de fenêtre, d'onglet, de mode, il doit y avoir un enregistrement automatique sans demander la confirmation». The plan tabs did since v0.114; every editor does since v0.117, from one module. Held here, on a copy of the example project with every box counted: an edit saved when the tab is left, with no box and the dot gone; what is refused not written, the dot kept and the reason in the status line; a rename never made without the engineer; a new draft never touched not written; nothing written in a project opened read-only; a save put off while an export runs and made when it ends; and the window left for another application saving what can be.
"""

import contextlib
import json
import os
import sys

import conftest
from conftest import ROOT, Skip

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


@contextlib.contextmanager
def _boxes():
    """Every box counted, and none can block: a question says Discard where it has three buttons, Yes where it has two."""
    from PySide6.QtWidgets import QMessageBox
    shown = []
    names = ("warning", "critical", "information", "question")
    originals = {name: QMessageBox.__dict__[name] for name in names}
    for name in names:
        def stub(*a, name=name, **k):
            shown.append(name)
            if name == "question":
                return QMessageBox.StandardButton.Discard if len(a) >= 4 else QMessageBox.StandardButton.Yes
            return QMessageBox.StandardButton.Ok
        setattr(QMessageBox, name, staticmethod(stub))
    try:
        yield shown
    finally:
        for name, original in originals.items():
            setattr(QMessageBox, name, original)


def _window():
    if "window" not in _STATE:
        app = _qt()
        here = conftest.project_copy("autosave_v0118")
        with project.using(here), _boxes():
            import woodcore_gui
            window = woodcore_gui.MainWindow()
            window.reexport = lambda **_k: None     # a position saved imports the project: not in this run
        _STATE.update(app=app, window=window, here=here)
    return _STATE["window"], _STATE["here"]


def _show(window, key):
    import woodcore_gui
    index = [k for k, _f in woodcore_gui.TABS].index(key)
    window.tab_widget.setCurrentIndex(index)
    return window.tabs[index]


def _leave(window):
    """Another tab brought to the front: the variables, a browser with nothing to save."""
    _show(window, "tab_variables")


# Each editor: the tab, how an edit is made in it, and the file the edit lands in.
def _edit_identity(tab, text):
    tab.identity.description.setText(text)
    tab.identity.description.editingFinished.emit()     # the static models hear a field when it is left


EDITORS = {
    "tab_schema": (_edit_identity, lambda here, tab: here.details_dir / f"{tab.current_id}.json"),
    "tab_statics": (_edit_identity, lambda here, tab: here.statics_dir / f"{tab.current_id}.json"),
    "tab_connections": (_edit_identity, lambda here, tab: here.connectors_dir / f"{tab.current_id}.json"),
    "tab_mc_tension": (_edit_identity, lambda here, tab: here.checks_dir / f"{tab.current_id}.json"),
    "tab_polar": (lambda tab, text: tab.label_edit.setText(text), lambda here, tab: here.connections_dir / f"{tab.current_id}.json"),
    "tab_positions": (lambda tab, text: tab.description_edit.setPlainText(text), lambda here, tab: here.sources_dir / "positions.json"),
    "tab_journal": (lambda tab, text: tab.label_edit.setText(text), lambda here, tab: tab.file()),
}


def test_an_edit_is_saved_when_the_tab_is_left_without_a_box():
    window, here = _window()
    with project.using(here):
        for key, (edit, file_of) in EDITORS.items():
            tab = _show(window, key)
            if key == "tab_journal" and tab.current is None:
                with _boxes():
                    tab.new()        # the example's convention d'utilisation has no revision: a new one, its date and label typed, is saved as well
                tab.date_edit.setText("2026-10-07")
                tab.initials_edit.setText("FL")   # the office's short form, which a revision needs
            else:
                assert getattr(tab, "current_id", getattr(tab, "current", None)) is not None, f"{key}: the example has an object to edit"
            text = f"autosave {key}"
            with _boxes() as shown:
                edit(tab, text)
                assert tab.dirty, f"{key}: an edit makes the tab dirty"
                new = getattr(tab, "current", 0) is None
                _leave(window)
                if new:
                    # a draft never saved waits while the engineer only looks elsewhere (review A02), and is saved when it is replaced
                    assert tab.dirty and text not in (file_of(here, tab).read_text(encoding="utf-8") if file_of(here, tab).is_file() else ""), key
                    tab = _show(window, key)
                    assert tab.confirm_leave()
            assert not shown, (key, shown)
            assert not tab.dirty, f"{key}: still dirty after the tab was left -- {window.status.text()}"
            assert text in file_of(here, tab).read_text(encoding="utf-8"), f"{key}: the edit is not in {file_of(here, tab).name}"


def test_what_is_refused_is_not_written_and_the_reason_is_in_the_status_line():
    window, here = _window()
    with project.using(here):
        tab = _show(window, "tab_schema")
        path = here.details_dir / f"{tab.current_id}.json"
        before = path.read_bytes()
        with _boxes() as shown:
            tab.identity.id.setText("")             # an ID is required: the save refuses it
            assert tab.dirty
            _leave(window)
        assert not shown, shown
        assert tab.dirty and path.read_bytes() == before, "a draft refused is never written in silence"
        said = tab.t("autosave_refused", name=tab.current_id, reason="")      # «VU-Skizze» n'est pas enregistré : <the reason>
        assert window.status.text().startswith(said) and len(window.status.text()) > len(said) + 3, window.status.text()
        tab.revert()


def test_a_rename_is_never_made_without_the_engineer():
    window, here = _window()
    with project.using(here):
        tab = _show(window, "tab_schema")
        old = tab.current_id
        with _boxes() as shown:
            tab.identity.id.setText(old + "x")
            _leave(window)
        assert not shown, shown
        assert tab.dirty and (here.details_dir / f"{old}.json").is_file() and not (here.details_dir / f"{old}x.json").exists(), "an ID half typed would rename the schema"
        assert tab.t("autosave_rename") in window.status.text(), window.status.text()
        tab.revert()


def test_a_new_position_never_touched_is_not_written():
    window, here = _window()
    with project.using(here):
        tab = _show(window, "tab_positions")
        before = (here.sources_dir / "positions.json").read_bytes()
        with _boxes() as shown:
            tab.new_position()
            assert tab.current_id is None and tab.untouched_draft()
            _leave(window)
            tab = _show(window, "tab_positions")
            tab.load_first() if hasattr(tab, "load_first") else None
        assert (here.sources_dir / "positions.json").read_bytes() == before, "a position nobody asked for was written"
        assert "warning" not in shown and "critical" not in shown, shown
        tab.dirty = False


def test_nothing_is_written_in_a_project_opened_read_only():
    window, here = _window()
    with project.using(here):
        tab = _show(window, "tab_connections")
        path = here.connectors_dir / f"{tab.current_id}.json"
        before = path.read_bytes()
        window.read_only = True
        try:
            with _boxes() as shown:
                _edit_identity(tab, "read only")
                _leave(window)
            assert not shown, f"saving without a question opens no box, not even the read-only one: {shown}"
            assert path.read_bytes() == before and tab.dirty
        finally:
            window.read_only = False
            tab.revert()


def test_a_save_put_off_while_an_export_runs_is_made_when_it_ends():
    window, here = _window()
    with project.using(here):
        tab = _show(window, "tab_polar")
        path = here.connections_dir / f"{tab.current_id}.json"
        window.process = object()
        try:
            with _boxes() as shown:
                tab.label_edit.setText("after the export")
                _leave(window)
            assert not shown and tab.dirty and "after the export" not in path.read_text(encoding="utf-8")
            assert window.autosave_pending
        finally:
            window.process = None
        window.flush_autosave()
        assert not tab.dirty and "after the export" in path.read_text(encoding="utf-8")


def test_the_window_left_for_another_application_saves_what_can_be():
    from PySide6.QtCore import Qt
    window, here = _window()
    with project.using(here):
        tab = _show(window, "tab_mc_tension")
        path = here.checks_dir / f"{tab.current_id}.json"
        with _boxes() as shown:
            _edit_identity(tab, "focus left")
            window.on_application_state(Qt.ApplicationState.ApplicationInactive)
        assert not shown and not tab.dirty and "focus left" in path.read_text(encoding="utf-8")
        # a script half typed would run at the next export: the Python tab waits for the tab or the script to be left
        import python_tab
        assert python_tab.PythonTab.SAVE_ON_FOCUS is False


def test_a_plan_a_view_and_another_object_save_without_a_box():
    """The plans (since v0.114, through the same module since v0.117), another view of a tab, and another object chosen in its list."""
    window, here = _window()
    with project.using(here):
        plan = _show(window, "tab_plan")
        path = here.plans_dir / f"{plan.current_id}.json"
        with _boxes() as shown:
            plan.label_edit.setText("plan left")
            plan.label_edit.editingFinished.emit()
            assert plan.dirty
            _leave(window)
        assert not shown and not plan.dirty and "plan left" in path.read_text(encoding="utf-8"), window.status.text()
        statics = _show(window, "tab_statics")
        path = here.statics_dir / f"{statics.current_id}.json"
        with _boxes() as shown:
            _edit_identity(statics, "view left")
            window.on_view_chosen("display")
        assert not shown and not statics.dirty and "view left" in path.read_text(encoding="utf-8"), "another view saves as another tab does"
        window.on_view_chosen("draw")
        first, second = statics.current_id, next(i for i in statics.saved_ids if i != statics.current_id)
        with _boxes() as shown:
            _edit_identity(statics, "object left")
            statics.on_list_change(second)
        assert not shown and statics.current_id == second and "object left" in (here.statics_dir / f"{first}.json").read_text(encoding="utf-8")


def test_the_focus_left_never_saves_an_id_being_typed_and_closing_asks_for_what_cannot_be_saved():
    from PySide6.QtCore import Qt
    window, here = _window()
    with project.using(here):
        tab = _show(window, "tab_mc_tension")
        path = here.checks_dir / f"{tab.current_id}.json"
        before = path.read_bytes()
        with _boxes() as shown:
            _edit_identity(tab, "id has the cursor")
            tab.identity.id.hasFocus = lambda: True        # the cursor in the ID field as Woodcore is left
            window.on_application_state(Qt.ApplicationState.ApplicationInactive)
        del tab.identity.id.hasFocus
        assert not shown and tab.dirty and path.read_bytes() == before, "an ID being typed is never saved on the focus alone"
        tab.identity.id.setText("")                      # refused: no ID
        with _boxes() as shown:
            assert tab.confirm_leave() is True             # what closing asks of every tab; the stub answers «Discard»
        assert shown == ["question"], f"what cannot be saved is asked about once: {shown}"
        assert not tab.dirty and path.read_bytes() == before
        tab.load(tab.current_id)


def test_the_fire_plan_the_compression_an_annex_and_a_script_save_without_a_box():
    """REQ-001 for the editors the first test leaves out: the fire protection plan, the compression check, an annex's source, and a script -- which, saved when the tab is left, waits for that and not for the focus (SAVE_ON_FOCUS)."""
    window, here = _window()
    with project.using(here):
        fire = _show(window, "tab_fire")
        path = here.fire_dir / f"{fire.current_id}.json"
        with _boxes() as shown:
            fire.label_edit.setText("fire left")
            fire.label_edit.editingFinished.emit()
            assert fire.dirty
            _leave(window)
        assert not shown and not fire.dirty and "fire left" in path.read_text(encoding="utf-8"), window.status.text()

        check = _show(window, "tab_mc_compression")
        path = here.checks_dir / f"{check.current_id}.json"
        with _boxes() as shown:
            _edit_identity(check, "compression left")
            _leave(window)
        assert not shown and not check.dirty and "compression left" in path.read_text(encoding="utf-8"), window.status.text()

        annexes = _show(window, "tab_annexes")
        sid = sorted(annexes.sources)[0]
        annexes.load("source", sid)
        path = here.sources_dir / "annexes" / "sources" / f"{sid}.json"
        with _boxes() as shown:
            annexes.source_identity.description.setText("annex left")
            assert annexes.dirty
            _leave(window)
        assert not shown and not annexes.dirty and "annex left" in path.read_text(encoding="utf-8"), window.status.text()

        from PySide6.QtCore import Qt
        scripts = _show(window, "tab_python")
        assert scripts.current is not None, "the example has a script"
        path = scripts.path_of(scripts.current)
        text = scripts.editor.toPlainText()
        with _boxes() as shown:
            scripts.editor.setPlainText(text + "\n# script left\n")
            assert scripts.dirty
            window.on_application_state(Qt.ApplicationState.ApplicationInactive)
            assert scripts.dirty and "# script left" not in path.read_text(encoding="utf-8"), "a script half typed is not saved when the window is left"
            _leave(window)
        assert not shown and not scripts.dirty and "# script left" in path.read_text(encoding="utf-8"), window.status.text()
        scripts.editor.setPlainText(text)
        _leave(window)


def test_another_document_saves_the_journal_of_the_one_left():
    """REQ-001, the document changed (the window's `on_mode_changed`): the journal being written is saved into the journal of the document it was written for, before the other document is shown."""
    window, here = _window()
    with project.using(here):
        journal = _show(window, "tab_journal")
        mode = window.current_document()
        other = next(m for m in here.modes if m != mode)
        file = journal.file()
        with _boxes() as shown:
            journal.new()
            journal.date_edit.setText("2026-10-08")
            journal.initials_edit.setText("FL")
            journal.label_edit.setText("document left")
            assert journal.dirty
            window.on_mode_changed(other)
        try:
            assert not shown, shown
            assert window.mode == other and "document left" in file.read_text(encoding="utf-8"), "the revision went with the document it was not written for"
        finally:
            window.on_mode_changed(mode)

