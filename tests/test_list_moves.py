"""Rows dropped into a folder, the same rule in every editor tab (spec 2026-10-21-restes-issue-69, UI-001, ARCH-001; calc/tools/source_editor.py).

The engineer, 21.10.2026: «Statique et Plan demandent d'enregistrer avant de déplacer, et affichent l'erreur d'écriture». Until v0.120 the four canvases each filed rows their own way, the static models and the plans moving a source without saving the draft first and letting a file the disk refused raise out of the window. Held here, on a copy of the example project, in «Schémas», «Statique», «Plan de positions», «Plan feu», «Moment polaire» and a member check (the base itself):

* **a file the disk refuses** (OneDrive holding it): the window does not raise, what was written before is exported and kept, what follows is not written, and the status bar says which file failed, last;
* **the draft is saved before the move** where it can be -- the question only where it cannot, «Annuler» moving nothing --, and takes the folder in memory too -- its next save does not put it back where it was;
* **a draft never saved, dropped into a folder,** stays there -- its row while it is a draft, its file once saved.
"""

import json

import conftest
from conftest import Skip  # noqa: F401  (a Qt-less machine skips through _qt)

import project
from test_autosave import _boxes, _edit_identity, _qt

_STATE = {}

TABS = ("tab_schema", "tab_statics", "tab_plan", "tab_fire", "tab_polar", "tab_mc_tension")


def _edit_label(tab, text):
    tab.label_edit.setText(text)
    tab.label_edit.editingFinished.emit()


EDITS = {"tab_schema": _edit_identity, "tab_statics": _edit_identity, "tab_mc_tension": _edit_identity, "tab_plan": _edit_label, "tab_fire": _edit_label, "tab_polar": _edit_label}


def _window():
    if "window" not in _STATE:
        app = _qt()
        here = conftest.project_copy("list_moves")
        with project.using(here), _boxes():
            import woodcore_gui
            window = woodcore_gui.MainWindow()
            window.reexport = lambda **_k: None
        _STATE.update(app=app, window=window, here=here)
    return _STATE["window"], _STATE["here"]


def _tab(window, key):
    import woodcore_gui
    index = [k for k, _f in woodcore_gui.TABS].index(key)
    window.tab_widget.setCurrentIndex(index)
    return window.tabs[index]


def _group(tab, cid):
    return json.loads((tab.sources_dir() / f"{cid}.json").read_text(encoding="utf-8")).get("group")


def _two_saved(tab):
    """Two saved sources of the tab, a second made by «Dupliquer» where the example holds one."""
    if len(tab.ids) < 2:
        with _boxes():
            tab.duplicate()
            assert tab.save() is not False
    assert len(tab.ids) >= 2, (tab.KEY, tab.ids)
    return tab.ids[0], tab.ids[1]


def test_a_file_the_disk_refuses_stops_the_move_and_is_said_last():
    import engine
    window, here = _window()
    with project.using(here):
        for key in TABS:
            tab = _tab(window, key)
            first, second = _two_saved(tab)
            with _boxes():
                tab.load(first)
                tab.reload_list(first)
            exported = []
            tab.export_listed = lambda text: exported.append(text)
            real_write = engine.write_json

            def refusing(path, data, real_write=real_write, second=second):
                if path.stem == second:
                    raise OSError("locked by the cloud")
                return real_write(path, data)
            engine.write_json = refusing
            try:
                with _boxes() as shown:
                    tab.on_moved([first, second], "Dossier A")
            finally:
                engine.write_json = real_write
                del tab.export_listed
            assert not shown, (key, shown)
            assert _group(tab, first) == "Dossier A" and _group(tab, second) != "Dossier A", key
            assert exported == [tab.word("moved", count=1, group="Dossier A")], (key, exported)
            assert window.status.text() == window.t("list_write_failed", id=second, error="locked by the cloud"), (key, window.status.text())
            assert tab.draft_group() == "Dossier A", f"{key}: the source open takes the folder in memory too"


def test_the_draft_is_saved_before_the_move_and_keeps_its_folder():
    window, here = _window()
    with project.using(here):
        for key in TABS:
            tab = _tab(window, key)
            first, _second = _two_saved(tab)
            with _boxes():
                tab.load(first)
                tab.reload_list(first)
            text = f"moved {key}"
            with _boxes() as shown:
                EDITS[key](tab, text)
                assert tab.dirty, key
                tab.on_moved([first], "Dossier B")
            assert not shown and not tab.dirty, (key, shown)
            written = (tab.sources_dir() / f"{first}.json").read_text(encoding="utf-8")
            assert text in written and json.loads(written).get("group") == "Dossier B", key
            # saved again, the source stays in its new folder: the draft took it in memory
            with _boxes():
                EDITS[key](tab, text + " again")
                tab.confirm_leave()
            assert _group(tab, first) == "Dossier B", f"{key}: the next save put the source back where it was"


def test_a_draft_never_saved_dropped_into_a_folder_stays_there():
    window, here = _window()
    from source_editor import NEW_ROW   # calc/tools on the path once the window is built
    with project.using(here):
        for key in TABS:
            tab = _tab(window, key)
            with _boxes():
                tab.new()
            assert tab.current_id is None, key
            tab.dirty = False   # a draft nothing has been typed into: confirm_leave lets it be, and it stays a draft
            with _boxes() as shown:
                tab.on_moved([NEW_ROW], "Dossier C")
            assert not shown and tab.draft_group() == "Dossier C", key
            assert tab.current_id is None and NEW_ROW in tab.list.ids(), key
            # saved, the draft is filed where it was dropped
            with _boxes():
                assert tab.save() is not False, key
            assert tab.current_id and _group(tab, tab.current_id) == "Dossier C", key
            with _boxes():
                tab.open_first()


def test_a_move_the_engineer_cancels_moves_nothing():
    """UI-001: where the draft cannot be saved, the question is asked -- and «Annuler» (confirm_leave False) leaves every file where it was."""
    window, here = _window()
    with project.using(here):
        for key in TABS:
            tab = _tab(window, key)
            first, second = _two_saved(tab)
            with _boxes():
                tab.load(first)
                tab.reload_list(first)
            before = {cid: (tab.sources_dir() / f"{cid}.json").read_bytes() for cid in (first, second)}
            tab.confirm_leave = lambda: False
            try:
                with _boxes() as shown:
                    tab.on_moved([first, second], "Dossier D")
            finally:
                del tab.confirm_leave
            assert not shown, key
            assert {cid: (tab.sources_dir() / f"{cid}.json").read_bytes() for cid in (first, second)} == before, f"{key}: a move cancelled wrote a file"
