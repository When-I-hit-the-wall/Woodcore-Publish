"""Every button under the list of every editor tab, clicked -- against a copy of the project's sources, off-screen.

Two defects of the same kind reached the engineer in one evening (v0.77), each a handler that raised and so did nothing, silently, under pythonw: *Moments polaires*' «Enregistrer» still read the fastener table of v0.31, and *Modèles statiques*' `taken_ids()` unpacked `list_models()` as two values when it had returned three since v0.69 -- so «Nouveau», «Dupliquer» and «Enregistrer» of that tab had been broken for eight versions. Nothing clicked them. `woodcore_gui.install_error_box` showed such an exception (a critical notice since v0.117, `notices_ui.install_hooks`), and this file clicks them: load the first entry, Nouveau, Enregistrer, Dupliquer, Enregistrer, Annuler les modifications, Supprimer, and a new folder, in each of the five tabs. Planted back, the statics unpack fails it naming the tab and the button.

⚠️ The project the tabs work on is a copy made for the run (conftest.project_copy, v0.81), and the message boxes and file dialogs are stubbed -- a modal off-screen never comes back (tests/test_connectors.py). The copies are taken from the project as it stands, so this also says whether the engineer's own files can be opened, saved and duplicated.
"""

import os
import sys
import traceback

import conftest
from conftest import ROOT, Skip

import project  # the copy the tabs work on (calc/project.py)

# Every tab whose list has «Nouveau», «Enregistrer», «Dupliquer» and «Supprimer» under it -- the journal's own since v0.99.
# The annexes (v0.115) file their entries in two fixed folders and delete rather than archive, like the journal.
EDITORS = ("PlanTab", "FireTab", "StaticsTab", "SchemaTab", "ConnectorsTab", "PolarTab", "JournalTab", "AnnexTab", "TensionTab", "CompressionTab")
# The five that file their sources in folders and archive them on «Supprimer» (source_archive.py). The journal is one file of entries, in the journal's own order: it has no folder to make and nothing to archive, so the two checks that read a folder are skipped for it.
ARCHIVING = ("PlanTab", "FireTab", "StaticsTab", "SchemaTab", "ConnectorsTab", "PolarTab", "TensionTab", "CompressionTab")
CLICKS = ("load_first", "new", "save", "duplicate", "save", "revert", "delete", "load_first", "duplicate", "revert")

# The modules of the tabs.
MODULES = ("statics_tab", "plan_tab", "fire_tab", "schema_tab", "connectors_tab", "journal_tab", "annex_tab", "member_check_tab", "woodcore_gui")


def test_every_list_button_of_every_editor_tab_runs():
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        from PySide6.QtWidgets import QApplication, QFileDialog, QInputDialog, QMessageBox
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    real = project.current()
    modules, copy, restore = _copied_project("editor_buttons")

    stubs = {
        (QMessageBox, "warning"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok),
        (QMessageBox, "critical"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok),
        (QMessageBox, "information"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok),
        # a yes/no question says yes (a rename, a delete); a save/discard/cancel one discards
        (QMessageBox, "question"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes if len(a) < 4 else QMessageBox.StandardButton.Discard),
        (QFileDialog, "getOpenFileName"): staticmethod(lambda *a, **k: ("", "")),
        (QInputDialog, "getText"): staticmethod(lambda *a, **k: ("Dossier_77", True)),
    }
    originals = {key: key[0].__dict__[key[1]] for key in stubs}
    for (owner, attr), stub in stubs.items():
        setattr(owner, attr, stub)

    failures = []
    try:
        app = QApplication.instance() or QApplication([])
        window = modules["woodcore_gui"].MainWindow()
        for tab in window.tabs:
            name = type(tab).__name__
            if name not in EDITORS:
                continue
            window.tab_widget.setCurrentWidget(tab)
            for click in CLICKS + ("new_folder",):
                target = getattr(tab.list, "new_folder", None) if click == "new_folder" else getattr(tab, click, None)
                if target is None:
                    continue
                if click != "save":
                    tab.dirty = False
                try:
                    target()
                    app.processEvents()
                except Exception:  # noqa: BLE001 -- what the engineer met: a button whose handler raises
                    failures.append(f"{name}.{click}: {traceback.format_exc().splitlines()[-1]}")
            if name in ARCHIVING and "Dossier_77" not in tab.list.empty_folders():
                failures.append(f"{name}.new_folder: the folder made is not in the list")
            tab.dirty = False
        conftest.dispose(window)
    finally:
        for (owner, attr), original in originals.items():
            setattr(owner, attr, original)
        restore()
    assert not failures, "buttons that raise:\n  " + "\n  ".join(failures)
    # «Supprimer» archives (v0.77): what was deleted in the copy is in its archives/, without its id, and not where the export reads
    import json
    import source_archive
    archived = [p for folder in ("statics", "plans", "fire", "details", "connectors", "connections", "checks")
                for p in source_archive.folder(copy / folder).glob("*.json")]
    assert len(archived) >= 7, "«Supprimer» did not archive in every tab: %s" % [p.parent.parent.name for p in archived]
    assert all("id" not in json.loads(p.read_text(encoding="utf-8")) for p in archived), "an archived source kept its id"
    assert not [p for p in real.statics_dir.glob("S0*.json")], "a model was written into the project's own statics/"



def _copied_project(name):
    """The five tabs' modules, the current project pointed at a copy of it, the copy's sources folder -- connectors/, plans/, ... -- and a function that puts the project back."""
    import importlib
    modules = {module: importlib.import_module(module) for module in MODULES}
    scope = project.using(conftest.project_copy(name))
    copied = scope.__enter__()
    return modules, copied.sources_dir, lambda: scope.__exit__(None, None, None)


def test_supprimer_on_an_unsaved_draft_archives_nothing():
    """«Supprimer» after «Nouveau» or «Dupliquer», before «Enregistrer», archived the SAVED entry still highlighted in the list -- Fluchttreppe in «Plan de positions», VU-SD-10 in «Connecteurs» -- and left the draft on the form (periodic audit 260916, AUD-5-3)."""
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    modules, copy, restore = _copied_project("unsaved_delete")
    stubs = {
        (QMessageBox, "question"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes if len(a) < 4 else QMessageBox.StandardButton.Discard),
        (QMessageBox, "warning"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok),
        (QFileDialog, "getOpenFileName"): staticmethod(lambda *a, **k: ("", "")),    # «Nouveau» plan: no background chosen
    }
    originals = {key: key[0].__dict__[key[1]] for key in stubs}
    for (owner, attr), stub in stubs.items():
        setattr(owner, attr, stub)
    wrong = []
    try:
        app = QApplication.instance() or QApplication([])
        window = modules["woodcore_gui"].MainWindow()
        for tab in window.tabs:
            if type(tab).__name__ not in ARCHIVING:
                continue
            folder = {"PlanTab": "plans", "FireTab": "fire", "StaticsTab": "statics", "SchemaTab": "details", "ConnectorsTab": "connectors", "PolarTab": "connections", "TensionTab": "checks", "CompressionTab": "checks"}[type(tab).__name__]
            for verb in ("new", "duplicate"):
                tab.dirty = False
                if hasattr(tab, "load_first"):
                    tab.load_first()
                else:
                    tab.reload_list()
                    if not tab.ids:
                        wrong.append(f"{type(tab).__name__} before {verb}: no saved entry left to open")
                        break
                    tab.load(tab.ids[0])
                    tab.reload_list(tab.ids[0])
                app.processEvents()
                before = sorted(p.name for p in (copy / folder).glob("*.json"))
                getattr(tab, verb)()
                app.processEvents()
                tab.delete()
                app.processEvents()
                after = sorted(p.name for p in (copy / folder).glob("*.json"))
                if after != before:
                    wrong.append(f"{type(tab).__name__} after {verb}: {sorted(set(before) - set(after))} archived")
                tab.dirty = False
        conftest.dispose(window)
    finally:
        for (owner, attr), original in originals.items():
            setattr(owner, attr, original)
        restore()
    assert not wrong, "«Supprimer» on an unsaved draft archived a saved entry:\n  " + "\n  ".join(wrong)


def test_a_refused_ajouter_leaves_no_undo_step_and_no_dot():
    """«Ajouter» under «Barres», «Charges ponctuelles», «Charges linéaires» or «Cotations» of a model with nothing to hang it on added nothing, and still pushed a step of «Annuler» and marked the model modified, with no word said (periodic audit 260916, AUD-5-4). A refusal leaves no step (docs/decisions.md §13, v0.73's rule)."""
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    QApplication.instance() or QApplication([])
    import woodcore_gui
    from domains import statics as model
    window = woodcore_gui.MainWindow()
    tab = next(t for t in window.tabs if type(t).__name__ == "StaticsTab")
    tab.open_source(model.new_source("S99"), None, False)
    try:
        for collection in ("members", "point_loads", "line_loads", "dimensions"):
            steps = len(tab.undo_stack)
            tab.add_row(collection)
            assert not tab.source.get(collection), collection
            assert len(tab.undo_stack) == steps, f"«Ajouter» {collection} refused and still took {len(tab.undo_stack) - steps} step(s)"
            assert not tab.dirty, f"«Ajouter» {collection} refused and marked the model modified"
    finally:
        tab.dirty = False
        conftest.dispose(window)
def test_a_typed_value_survives_a_trip_to_variables_and_back():
    """In a load's panel, «Valeur» -> «Variables» -> «Valeur» put 1.0 kN where 0.55 kN had been typed, and an «Enregistrer» then printed a load nobody entered (periodic audit 260916, AUD-5-9). The variable was already remembered the other way round; the typed value is now too."""
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    QApplication.instance() or QApplication([])
    import json
    import woodcore_gui
    window = woodcore_gui.MainWindow()
    tab = next(t for t in window.tabs if type(t).__name__ == "StaticsTab")
    source = {
        "schema_version": "1.1", "id": "S98", "label": "",
        "points": [{"id": "P1", "x": 0, "z": 0}, {"id": "P2", "x": 2, "z": 0}],
        "members": [{"id": "B1", "kind": "bar", "p1": "P1", "p2": "P2"}],
        "supports": [], "releases": [], "line_loads": [], "dimensions": [],
        "point_loads": [{"id": "F1", "point": "P2", "reference": "B1", "along": 0, "direction": "vertical",
                         "magnitude": {"value": 0.55, "unit": "kN"}, "label": "F", "show": "name+value"}],
    }
    tab.open_source(json.loads(json.dumps(source)), None, False)
    try:
        entry = tab.source["point_loads"][0]
        # «Variables» opens the «Variables» tab in its choosing mode since issue #42 (UI-005): the variable is chosen there
        import variables_tab
        listing = next(t for t in window.tabs if isinstance(t, variables_tab.VariablesTab))
        window.tab_widget.setCurrentWidget(tab)
        tab.set_magnitude_kind(entry, False)
        assert window.tab_widget.currentWidget() is listing and entry["magnitude"] == {"value": 0.55, "unit": "kN"}
        key = next(k for k, d in listing.domains.items() if k[0] == variables_tab.EXPORT and d.address == ("live-load", "A1"))
        listing.select_key((*key, "Q_k"))
        listing.pick_chosen()
        entry = tab.source["point_loads"][0]
        assert "domain" in entry["magnitude"], entry["magnitude"]
        tab.set_magnitude_kind(entry, True)
        entry = tab.source["point_loads"][0]
        assert entry["magnitude"] == {"value": 0.55, "unit": "kN"}, "the typed value was lost: %s" % entry["magnitude"]
    finally:
        tab.dirty = False
        conftest.dispose(window)
def test_nouveau_and_dupliquer_list_the_draft_in_connecteurs_as_in_the_other_tabs():
    """In «Connecteurs», «Nouveau» and «Dupliquer» added no row to the list and left the previous connector highlighted, where the four other editors list the draft and select it (periodic audit 260916, AUD-5-8) -- which is what made «Supprimer» on a draft archive the saved entry."""
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    modules, _copy, restore = _copied_project("connectors_draft_row")
    original = QMessageBox.__dict__["question"]
    QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Discard)
    try:
        app = QApplication.instance() or QApplication([])
        window = modules["woodcore_gui"].MainWindow()
        tab = next(t for t in window.tabs if type(t).__name__ == "ConnectorsTab")
        tab.reload_list()
        if not tab.ids:
            raise Skip("the project has no connector to duplicate")
        tab.load(tab.ids[0])
        tab.reload_list(tab.ids[0])
        for verb in ("new", "duplicate"):
            saved = list(tab.ids)
            tab.dirty = False
            getattr(tab, verb)()
            app.processEvents()
            rows = tab.list.ids()
            drafts = [r for r in rows if r not in saved]
            assert len(drafts) == 1, f"«{verb}»: the list holds {rows}, no draft row beside the saved {saved}"
            assert tab.list.selected_ids() == drafts, f"«{verb}»: {tab.list.selected_ids()} selected, not the draft"
            tab.dirty = False
            tab.load(saved[0])
            tab.reload_list(saved[0])
            assert tab.list.ids() == saved, "the draft row stayed after a saved connector was opened"
        conftest.dispose(window)
    finally:
        QMessageBox.question = original
        restore()
