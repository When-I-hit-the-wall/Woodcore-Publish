"""The export sheets' list of the two tabs of plans (v0.116, WP-I2): each tab lists and makes the sheets of its own kind, the PDF bundles are folders of the list whose sheets are dragged in and ordered, a bundle is exported as one PDF in the list's order, renamed and deleted, and the position plans' tab makes the list of the positions.

The window is built once, off-screen, on a copy of the example project of its own; every message box is stubbed -- a modal off-screen never comes back. A drop is driven through `SheetList.drop_on`, which is what `dropEvent` calls with the row under the pointer; the pointer's own drag is the one thing no test reaches.
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
def _boxes(answer=None, names=()):
    """The message boxes stubbed, every box shown recorded; a question answered Yes (or `answer`), a name asked for given from `names`."""
    from PySide6.QtWidgets import QInputDialog, QMessageBox
    shown = []
    queue = list(names)

    def box(kind):
        def show(_parent, _title, text, *args, **kwargs):
            shown.append((kind, text))
            if kind == "question":
                return answer if answer is not None else QMessageBox.StandardButton.Yes
            return QMessageBox.StandardButton.Ok
        return staticmethod(show)
    saved = {(QMessageBox, n): QMessageBox.__dict__[n] for n in ("question", "warning", "information", "critical")}
    saved[(QInputDialog, "getText")] = QInputDialog.__dict__["getText"]
    for n in ("question", "warning", "information", "critical"):
        setattr(QMessageBox, n, box(n))
    QInputDialog.getText = staticmethod(lambda *a, **k: (queue.pop(0), True) if queue else ("", False))
    try:
        # what was a box is a notice since v0.117: an information keeps its name, an error or a warning reads «warning» as its box did
        with conftest.notices_said(lambda notice: shown.append(("information" if notice.severity == "info" else "warning", notice.text))):
            yield shown
    finally:
        for (cls, name), value in saved.items():
            setattr(cls, name, value)


def _window():
    if "window" not in _STATE:
        app = _qt()
        conftest.exported("plans.json")
        here = conftest.project_copy("sheet_bundles_tab")
        import shutil
        for name in ("commands.typ", "config.typ", "title.typ"):     # what a sheet imports: the copy carries the report's folders and not these
            if not (here.typst_root / name).is_file():
                shutil.copy2(ROOT / "tests" / "projet-exemple" / name, here.typst_root / name)
        project.sync_engine(here)
        for path in here.plans_dir.glob("*.json"):
            source = json.loads(path.read_text(encoding="utf-8"))
            source.pop("background", None)
            path.write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        with project.using(here), _boxes():
            import woodcore_gui
            window = woodcore_gui.MainWindow()
        window.reexport = lambda **kwargs: None
        _STATE.update(app=app, window=window, here=here)
    return _STATE["window"], _STATE["here"]


def _tabs():
    window, here = _window()
    import fire_tab
    import plan_tab
    plan = next(t for t in window.tabs if isinstance(t, plan_tab.PlanTab))
    fire = next(t for t in window.tabs if isinstance(t, fire_tab.FireTab))
    plan.dirty = fire.dirty = False
    return plan, fire, here


def _clean(here):
    """Every sheet and bundle of the copy gone, so that a test starts from nothing."""
    import shutil
    folder = here.typst_root / "Plans"
    if folder.is_dir():
        shutil.rmtree(folder)


def _row(tree, sid):
    return tree._item_for(sid)


def _select(tree, *sids):
    from PySide6.QtCore import QItemSelectionModel
    tree.clearSelection()
    tree.setCurrentItem(_row(tree, sids[-1]), 0, QItemSelectionModel.SelectionFlag.NoUpdate)
    for sid in sids:
        _row(tree, sid).setSelected(True)


def _folder(tree, name):
    import grouped_list
    return next(i for i in tree._items(("folder",)) if i.data(0, grouped_list.GROUP_ROLE) == name)


def test_each_tab_lists_and_makes_the_sheets_of_its_own_kind():
    import sheets
    plan, fire, here = _tabs()
    with project.using(here), _boxes():
        _clean(here)
        sheets.new_sheet(here, "P1", kind="position")
        sheets.new_sheet(here, "F1", kind="fire")
        plan.reload_sheets()
        fire.reload_sheets()
        assert plan.sheet_list.ids() == ["P1"] and fire.sheet_list.ids() == ["F1"]
        made = plan.new_sheet()
        plan.sheet_editor.stop()
        assert sheets.sheet_kind(here, made) == "position"
        made_fire = fire.new_sheet()
        fire.sheet_editor.stop()
        assert sheets.sheet_kind(here, made_fire) == "fire"
        assert made in plan.sheet_list.ids() and made not in fire.sheet_list.ids()
        assert made_fire in fire.sheet_list.ids() and made_fire not in plan.sheet_list.ids()
        assert plan.sheet_editor.kind == "position" and fire.sheet_editor.kind == "fire"
        plan.show_plan_view()
        fire.show_plan_view()
        # the buttons: a fire tab makes no list of positions
        assert "list" in plan.bundle_buttons and "list" not in fire.bundle_buttons


def test_a_bundle_is_a_folder_two_sheets_are_dragged_in_at_once_and_reordered():
    import sheets
    plan, _fire, here = _tabs()
    with project.using(here), _boxes(names=["Satz"]):
        _clean(here)
        for sid in ("A", "B", "C"):
            sheets.new_sheet(here, sid, title=f"Blatt {sid}")
        plan.reload_sheets()
        tree = plan.sheet_list
        assert tree.bundle_names() == [] and tree.root_sheets() == ["A", "B", "C"]
        tree._new_folder()                      # the button/menu: asks a name, makes the bundle
        assert [b["name"] for b in sheets.list_bundles(here)] == ["Satz"] and tree.bundle_names() == ["Satz"]
        # two sheets dragged onto the bundle in one drop
        _select(tree, "A", "C")
        tree.drop_on(_folder(tree, "Satz"))
        assert sheets.bundle(here, "Satz")["sheets"] == ["A", "C"]
        assert tree.bundle_sheets("Satz") == ["A", "C"] and tree.root_sheets() == ["B"], "the sheets stand beneath the bundle, B stays at the root"
        # B dropped above C: the pages' order follows
        _select(tree, "B")
        tree.drop_on(_row(tree, "C"), below=False)
        assert sheets.bundle(here, "Satz")["sheets"] == ["A", "B", "C"]
        # C dragged above A within the bundle
        _select(tree, "C")
        tree.drop_on(_row(tree, "A"), below=False)
        assert sheets.bundle(here, "Satz")["sheets"] == ["C", "A", "B"]
        # below the last sheet
        _select(tree, "C")
        tree.drop_on(_row(tree, "B"), below=True)
        assert sheets.bundle(here, "Satz")["sheets"] == ["A", "B", "C"]
        # out of the bundle, onto the root
        _select(tree, "B")
        tree.drop_on(None)
        assert sheets.bundle(here, "Satz")["sheets"] == ["A", "C"] and "B" in tree.root_sheets()
        assert sorted(plan.sheet_list.ids()) == ["A", "B", "C"], "no sheet is lost by leaving a bundle"


def test_a_bundle_is_exported_as_one_pdf_in_the_lists_order_renamed_and_deleted():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    import sheets
    from pypdf import PdfReader
    plan, _fire, here = _tabs()
    with project.using(here), _boxes(names=["Alle"]) as shown:
        _clean(here)
        for sid in ("A", "B"):
            sheets.new_sheet(here, sid, title=f"Titel {sid}")
        plan.reload_sheets()
        plan.sheet_list._new_folder()
        _select(plan.sheet_list, "B", "A")
        plan.sheet_list.drop_on(_folder(plan.sheet_list, "Alle"))
        assert sheets.bundle(here, "Alle")["sheets"] == ["A", "B"]
        # exporting needs a bundle chosen
        plan.sheet_list.setCurrentItem(None)
        assert plan.export_bundle() is False
        plan.sheet_list.setCurrentItem(_folder(plan.sheet_list, "Alle"))
        assert plan.export_bundle() is True, shown
        pdf = sheets.bundle_pdf(here, "Alle")
        assert pdf.is_file() and len(PdfReader(str(pdf)).pages) == 2
        pages = [p.extract_text() for p in PdfReader(str(pdf)).pages]
        assert "Titel A" in pages[0] and "Titel B" in pages[1], "the pages follow the list's order"
        assert sheets.pdf(here, "A").is_file() and sheets.pdf(here, "B").is_file(), "each sheet keeps its own PDF"
        # reordered, exported again
        _select(plan.sheet_list, "B")
        plan.sheet_list.drop_on(_row(plan.sheet_list, "A"), below=False)
        plan.sheet_list.setCurrentItem(_folder(plan.sheet_list, "Alle"))
        assert plan.export_bundle()
        pages = [p.extract_text() for p in PdfReader(str(pdf)).pages]
        assert "Titel B" in pages[0] and "Titel A" in pages[1]
        # renamed: the PDF follows
        assert plan.rename_bundle("Alle", "Gesamt")
        assert sheets.bundle_pdf(here, "Gesamt").is_file() and not pdf.is_file()
        assert plan.sheet_list.bundle_names() == ["Gesamt"]
        # a name that cannot name a PDF is refused in words
        shown.clear()
        assert plan.rename_bundle("Gesamt", "a/b") is False and shown and shown[-1][0] == "warning"
        # deleted: the sheets stay, the PDF goes to the archives
        assert plan.delete_bundle("Gesamt")
        assert plan.sheet_list.bundle_names() == [] and sorted(plan.sheet_list.ids()) == ["A", "B"]
        assert not sheets.bundle_pdf(here, "Gesamt").is_file() and list((here.typst_root / "Plans" / "archives").glob("*Gesamt.pdf"))


def test_a_deleted_sheet_leaves_its_bundle_and_a_fire_bundle_gathers_fire_sheets_alone():
    import sheets
    plan, fire, here = _tabs()
    with project.using(here), _boxes(names=["Nur"]):
        _clean(here)
        sheets.new_sheet(here, "P1")
        sheets.new_sheet(here, "F1", kind="fire")
        sheets.create_bundle(here, "Pos", kind="position", sheets=["P1"])
        plan.reload_sheets()
        fire.reload_sheets()
        assert plan.sheet_list.bundle_names() == ["Pos"] and fire.sheet_list.bundle_names() == [], "a bundle is of one kind"
        fire.sheet_list._new_folder()
        assert [b["kind"] for b in sheets.list_bundles(here) if b["name"] == "Nur"] == ["fire"]
        _select(fire.sheet_list, "F1")
        fire.sheet_list.drop_on(_folder(fire.sheet_list, "Nur"))
        assert sheets.bundle(here, "Nur")["sheets"] == ["F1"]
        plan.sheet_list.select("P1")
        assert plan.delete_sheet()
        assert sheets.bundle(here, "Pos")["sheets"] == [] and "P1" not in plan.sheet_list.ids()


def test_the_list_of_the_positions_is_made_for_the_sheet_the_bundle_or_every_position():
    import sheets
    plan, fire, here = _tabs()
    with project.using(here), _boxes():
        _clean(here)
        sheets.new_sheet(here, "P1", title="Plan")
        sheets.add_viewport(here, "P1", "Geratehaus", 20, 35, width=120)
        sheets.create_bundle(here, "Pos", sheets=["P1"])
        plan.reload_sheets()
        plan.sheet_list.select("P1")
        made = plan.create_position_list()
        plan.sheet_editor.stop()
        assert made and sheets.page(here, made).size() == (210, 297), "an A4 portrait sheet"
        assert sheets.model(here, made, "positions").get("plans") == ["Geratehaus"], "the plans of the sheet chosen"
        assert made in plan.sheet_list.ids() and plan.view_kind == "sheet"
        plan.show_plan_view()
        # a bundle chosen: the plans of its sheets
        plan.sheet_list.setCurrentItem(_folder(plan.sheet_list, "Pos"))
        again = plan.create_position_list()
        plan.sheet_editor.stop()
        assert sheets.model(here, again, "positions").get("plans") == ["Geratehaus"]
        plan.show_plan_view()
        # nothing chosen: every position
        plan.sheet_list.setCurrentItem(None)
        every = plan.create_position_list()
        plan.sheet_editor.stop()
        assert sheets.model(here, every, "positions").get("scope") == "all"
        plan.show_plan_view()
        # the fire tab lists no positions
        assert "list" not in fire.bundle_buttons


def test_a_project_held_read_only_writes_no_bundle_no_sheet_and_no_frame():
    """v0.116 (WP-K): what the plan tabs write since v0.116 is refused in a project another window holds -- a PDF bundle made, renamed, deleted or exported, sheets dragged into one, the list of the positions made, a frame of the document view resized or deleted (woodcore_gui.WRITERS) -- and so is every write of the sheet editor and its PDF (SheetEditor.refused_read_only), each said once and nothing on disk changed."""
    import sheets
    plan, _fire, here = _tabs()
    window = _STATE["window"]
    with project.using(here), _boxes() as shown:
        _clean(here)
        sheets.new_sheet(here, "P1", title="Plan")
        sheets.create_bundle(here, "Pos", kind="position")
        plan.reload_sheets()
        pid, source, _group = next(iter(plan.list_sources()))
        plan_file = plan.sources_dir() / f"{pid}.json"
        before_plan = plan_file.read_bytes()
        before_sheet = sheets.read(here, "P1")
        before_bundles = sheets.list_bundles(here)
        window.read_only = True
        try:
            shown.clear()
            assert plan.new_bundle("Neu") is False
            assert plan.rename_bundle("Pos", "Anders") is False
            assert plan.delete_bundle("Pos") is False
            assert plan.on_sheets_moved([("P1", "")], "Pos", None) is False
            plan.sheet_list.setCurrentItem(_folder(plan.sheet_list, "Pos"))
            assert plan.export_bundle() is False
            assert plan.create_position_list() is False
            assert plan.write_frame_crop(pid, {"x": 1, "y": 1, "w": 10, "h": 10}) is False
            assert plan.on_frames_delete([pid]) is False
            refused = [text for kind, text in shown if kind == "information"]
            assert len(refused) == 8 and not [k for k, _t in shown if k == "question"], shown
            # the sheet editor: no object added, no PDF compiled
            editor = plan.sheet_editor
            saved = (editor.here, editor.sheet_id, editor.compiler.request)
            editor.here, editor.sheet_id = here, "P1"
            editor.compiler.request = lambda *args, **kwargs: None
            try:
                assert editor.add_text() is None
                assert editor.move("title", 30, 30) is False
                assert editor.export_pdf() == (False, "")
            finally:
                editor.here, editor.sheet_id, editor.compiler.request = saved
        finally:
            window.read_only = False
        assert sheets.list_bundles(here) == before_bundles and not sheets.bundle_pdf(here, "Pos").is_file()
        assert sheets.read(here, "P1") == before_sheet and not sheets.pdf(here, "P1").is_file()
        assert sorted(plan.sheet_list.ids()) == ["P1"], "no list of the positions made"
        assert plan_file.read_bytes() == before_plan, "the frame neither cropped nor archived"


def test_the_bundles_words_are_said_in_the_three_languages():
    _qt()
    import sheet_editor
    for lang in ("fr", "de", "en"):
        words = sheet_editor.bundle_words(lang)
        assert set(words) == set(sheet_editor.BUNDLE_KEYS) and all(words.values()), lang
        assert "{name}" in words["se_bundle_delete_ask"] and "{name}" in words["se_bundle_created"]
        assert "ß" not in "".join(words.values())


def test_zz_the_end_lets_go_of_the_window():
    """Last of the file (run in name order): the editors stopped and the window closed, so that the run's folder can be removed -- Windows refuses a folder a watcher holds."""
    if "window" not in _STATE:
        return
    plan, fire, _here = _tabs()
    for tab in (plan, fire):
        tab.sheet_editor.stop()
        tab.sheet_editor.wait()      # a compile still running holds the folder
        tab.show_plan_view()
    app, window = _STATE["app"], _STATE["window"]
    conftest.dispose(window)   # closed and destroyed at once
    app.processEvents()


def test_an_export_document_chosen_shows_all_its_pages_and_its_fields_taken_from_its_first_plan():
    """The engineer, 07.10.2026: «dans l'affichage "Export", on doit voir toutes les pages qui composent un document lorsqu'on navigue dans ses plans. On doit pouvoir modifier le nom, la description, l'étage, l'id du document. Par défaut, les valeurs sont reprises automatiquement lors de l'import dessus du premier plan.» (spec 2026-10-07-performance-erreurs-plans-legendes, REQ-016)"""
    import time
    import sheets
    window, here = _window()
    plan = next(t for t in window.tabs if type(t).__name__ == "PlanTab")
    with project.using(here), _boxes(names=["Gesamt"]):
        first = sheets.new_sheet(here).stem
        second = sheets.new_sheet(here).stem
        sheets.add_viewport(here, first, "Pavillon", 20, 20)
        sheets.create_bundle(here, "Gesamt", sheets=[first, second])
        plan.reload_sheets()
        assert plan.sheet_list.select_folder("Gesamt")
        plan.on_sheet_id("")
        assert plan.view_kind == "bundle" and plan.center.currentWidget() is plan.bundle_pages
        card = plan.bundle_card
        assert card.fields["id"].text() == "" and card.fields["id"].placeholderText() == "Pavillon", "the first plan's id, shown in grey"
        assert card.fields["name"].text() == "Gesamt"
        app = _STATE["app"]
        end = time.monotonic() + 120
        while plan.bundle_pages.page_count() != 2 and time.monotonic() < end:
            app.processEvents()
            time.sleep(0.02)
        assert plan.bundle_pages.page_count() == 2, "every page of the document, one after the other"
        card.fields["id"].setText("E01")
        card.fields["id"].editingFinished.emit()
        assert sheets.bundle(here, "Gesamt")["id"] == "E01" and sheets.bundle_pdf(here, "Gesamt").name == "E01.pdf"
        assert card.fields["id"].text() == "E01"
        card.fields["storey"].setText("1.OG")
        card.fields["storey"].editingFinished.emit()
        assert sheets.bundle(here, "Gesamt")["storey"] == "1.OG"
