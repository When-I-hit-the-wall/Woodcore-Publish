"""The documents of the plan tabs in v0.116 (WP-G; calc/tools/document_view.py, calc/tools/drawing_tab.py, calc/domains/plan_documents.py, calc/domains/plan_pages.py, docs/domain/position-plans.md §3.3sexies, docs/domain/fire-plans.md §3.3vicies, docs/ui/window.md §10quater): several frames on one page, each a plan of its own; the selection of frames in the document view and the plan's module of the frame chosen in the right pane, named and given a storey without the plan being opened; Suppr archiving; a layer switched shown at once -- written as an incremental update of the PDF, rendered again from the cache where it was seen before, exported in the background --; and the documents each tab's own.

The engineer's words (06.10.2026): «il doit être possible de cadrer, de mettre plusieurs cadrages sur une même feuille», «un outil sélection et sélectionner les cadres … dans le volet de droite, on doit immédiatement pouvoir … nommer ces cadres, donner un étage», «en activer un ou en désactiver un [calque] prend énormément de temps … quasi instantané», «je ne dois pas avoir accès dans le volet de gauche à des documents qui ont été déposés dans le plan de protection incendie, si je me trouve dans le plan de position et vice versa». His answers: the tick makes the first plan of a page, of the whole page; every further frame a new plan; unticking archives them all.

One window for the file, on a copy of the example project whose plans are drawn on no file and which holds no fire plan -- tests/test_fire_tab.py's arrangement --, the documents tests/fixtures/layered_pdf.py's PDF. Every box shown is recorded.
"""

import contextlib
import json
import os
import sys
import time

import conftest
from conftest import ROOT, Skip
from fixtures import layered_pdf as fx

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
def _boxes(answer=None, file=None, length=None):
    """Every box recorded; a question answered by `answer` (Yes where none is given); the file dialog answers `file`; the length asked for a calibration `length`."""
    from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox
    shown = []

    def box(kind):
        def show(_parent, _title, text, *args, **kwargs):
            shown.append((kind, text))
            if kind == "question":
                return answer if answer is not None else QMessageBox.StandardButton.Yes
            return QMessageBox.StandardButton.Ok
        return staticmethod(show)
    saved = {(QMessageBox, n): QMessageBox.__dict__[n] for n in ("question", "warning", "information", "critical")}
    saved[(QFileDialog, "getOpenFileName")] = QFileDialog.__dict__["getOpenFileName"]
    saved[(QInputDialog, "getDouble")] = QInputDialog.__dict__["getDouble"]
    for name in ("question", "warning", "information", "critical"):
        setattr(QMessageBox, name, box(name))
    QFileDialog.getOpenFileName = staticmethod(lambda *a, **k: (str(file) if file else "", ""))
    QInputDialog.getDouble = staticmethod(lambda *a, **k: (length, length is not None))
    try:
        yield shown
    finally:
        for (owner, name), original in saved.items():
            setattr(owner, name, original)


def _window():
    if "window" not in _STATE:
        app = _qt()
        here = conftest.project_copy("doc_frames_v0116")
        for path in here.fire_dir.glob("*.json"):
            path.unlink()
        from domains import plan_documents
        _STATE["cache"] = plan_documents.CACHE_ROOT
        plan_documents.CACHE_ROOT = conftest.tmpdir("doc_frames_v0116_cache")
        (here.root / "01_Pläne").mkdir(exist_ok=True)
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
    plan_tab = next(t for t in window.tabs if type(t).__name__ == "PlanTab")
    fire_tab = next(t for t in window.tabs if type(t).__name__ == "FireTab")
    for tab in (plan_tab, fire_tab):
        tab.dirty = False
    return plan_tab, fire_tab, here


def _settle(tab, timeout=60):
    app = _STATE["app"]
    end = time.monotonic() + timeout
    while tab.doc_view.is_busy():
        if time.monotonic() > end:
            raise AssertionError("the document view is still busy")
        app.processEvents()
        time.sleep(0.01)


def _import(tab, here, name, pages=2):
    path = fx.write(here.root / "01_Pläne" / name, pages=pages)
    with _boxes(file=path) as shown:
        assert tab.import_document(), shown
    _settle(tab)
    return tab.doc_id


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _release(tab):
    """The canvas lets go of the PDF it renders the plan open from -- a frame chosen opens its plan, whose page the canvas reads from the file, and the run's folder is removed afterwards, which Windows refuses for a file held open. Every test ends so, the runner taking the tests in the order of their names."""
    app, canvas = _STATE["app"], tab.canvas
    end = time.monotonic() + 30
    while canvas.busy() and time.monotonic() < end:
        app.processEvents()
        time.sleep(0.01)
    if canvas.pages is not None:
        canvas.pages.drop()
        canvas.retired.append(canvas.pages)
        canvas.pages = None
    canvas.collect()


def _done(*tabs):
    for tab in tabs:
        tab.finish_layer_export()
        tab.doc_view.set_document(None, None)
        _settle(tab)
        tab.show_plan_view()
        tab.dirty = False
        _release(tab)


def _click(tab, page, x, y, modifiers=None, double=False):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    view = tab.doc_view
    view.set_zoom(1.0)
    where = view.viewport_point(page, x, y).toPoint()
    send = QTest.mouseDClick if double else QTest.mouseClick
    send(view.area.viewport(), Qt.MouseButton.LeftButton, modifiers or Qt.KeyboardModifier.NoModifier, where)
    _STATE["app"].processEvents()


def test_two_frames_on_one_page_are_two_plans_and_unticking_archives_both():
    """The tick makes the first plan of the page, of the whole page -- framed by the page in the view --; the first frame drawn crops it; the next one is a NEW plan of that frame, on the same page of the same document, chosen at once. Unticking the page archives both, never deletes."""
    plan_tab, _fire, here = _tabs()
    with project.using(here), _boxes() as shown:
        docid = _import(plan_tab, here, "Frames.pdf")
        before = set(plan_tab.taken_ids())
        plan_tab.on_page_toggled(1, True)
        (first,) = set(plan_tab.taken_ids()) - before
        whole = plan_tab.doc_view.area.crops[1]
        assert [(c["plan"], c["rect"], c["whole"]) for c in whole] == [(first, (0.0, 0.0, 300.0, 100.0), True)], whole
        plan_tab.on_doc_crop(1, (10.0, 10.0, 100.0, 60.0))
        assert set(plan_tab.taken_ids()) - before == {first}, "the first frame is the whole page's plan's"
        assert _json(here.plans_dir / f"{first}.json")["crop"] == {"x": 10.0, "y": 10.0, "w": 100.0, "h": 60.0}
        plan_tab.on_doc_crop(1, (150.0, 20.0, 120.0, 70.0))
        (second,) = set(plan_tab.taken_ids()) - before - {first}
        source = _json(here.plans_dir / f"{second}.json")
        assert source["background"]["document"] == docid and source["background"]["page"] == 1
        assert source["crop"] == {"x": 150.0, "y": 20.0, "w": 120.0, "h": 70.0} and source["sheet"] == {"width": 300.0, "height": 100.0}
        crops = {c["plan"]: c for c in plan_tab.doc_view.area.crops[1]}
        assert set(crops) == {first, second} and crops[second]["label"].startswith(second) and not crops[second]["whole"]
        assert plan_tab.doc_view.used_pages() == [1]
        assert plan_tab.doc_view.selected_frames() == [second] and plan_tab.current_id == second, "the frame drawn is chosen, its plan the one open"
        assert second in _json(here.data_dir / "plans.json")["plans"]
        # a third frame on page 2, which nothing is drawn on yet: a plan of that frame, the page ticked
        plan_tab.on_doc_crop(2, (5.0, 5.0, 50.0, 50.0))
        assert plan_tab.doc_view.used_pages() == [1, 2]
        # unticked: both plans of page 1 archived at once, no question where nothing is drawn on them
        plan_tab.on_page_toggled(1, False)
        assert not ({first, second} & set(plan_tab.taken_ids()))
        for pid in (first, second):
            assert list((here.plans_dir / "archives").glob(f"*-{pid}.json")), f"{pid} was not archived"
        assert plan_tab.doc_view.used_pages() == [2]
        assert not [k for k, _t in shown if k in ("warning", "critical")], shown
        _done(plan_tab)


def test_an_edge_dragged_resizes_its_frame_and_a_whole_page_s_corner_gives_it_one():
    """An edge or a corner of a frame dragged with «Sélection» or «Cadrer»: that frame resized (frameEdited), no new plan made -- a plan of the whole page given a crop so."""
    plan_tab, _fire, here = _tabs()
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    with project.using(here), _boxes():
        _import(plan_tab, here, "Edges.pdf", pages=1)
        before = set(plan_tab.taken_ids())
        plan_tab.on_page_toggled(1, True)
        (pid,) = set(plan_tab.taken_ids()) - before
        view = plan_tab.doc_view
        view.set_zoom(1.0)
        edited = []
        view.frameEdited.connect(lambda *args: edited.append(args))
        viewport = view.area.viewport()
        # the page's own bottom-right corner, dragged up and left: the whole-page plan's frame
        a = view.viewport_point(1, 299.0, 99.0).toPoint()
        b = view.viewport_point(1, 200.0, 70.0).toPoint()
        QTest.mousePress(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, a)
        QTest.mouseMove(viewport, b)
        QTest.mouseRelease(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, b)
        _STATE["app"].processEvents()
        assert edited and edited[-1][:2] == (1, pid), edited
        crop = _json(here.plans_dir / f"{pid}.json")["crop"]
        assert crop["x"] == 0.0 and crop["y"] == 0.0 and abs(crop["w"] - 201.0) < 2.5 and abs(crop["h"] - 71.0) < 2.5, crop
        assert set(plan_tab.taken_ids()) - before == {pid}, "a frame resized made no plan"
        # its left edge, with «Cadrer»: resized, still no new plan
        view.set_tool("crop")
        a = view.viewport_point(1, 0.5, 30.0).toPoint()
        b = view.viewport_point(1, 40.0, 30.0).toPoint()
        QTest.mousePress(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, a)
        QTest.mouseMove(viewport, b)
        QTest.mouseRelease(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, b)
        _STATE["app"].processEvents()
        crop = _json(here.plans_dir / f"{pid}.json")["crop"]
        assert abs(crop["x"] - 40.0) < 2.5 and set(plan_tab.taken_ids()) - before == {pid}, crop
        view.set_tool("select")
        _done(plan_tab)


def test_a_frame_chosen_shows_its_plan_s_module_on_the_right_written_as_it_is_left():
    """«Sélection»: a click in a frame chooses it -- the smallest holding the point --, its plan made the plan open without the centre leaving the document, and the plan's own «Plan» module shown in the document's right pane: the name and the storey typed there are written into the plan as a field is left, and its frame's label follows. A click outside every frame lets it go, the module back in the plan's column; a double click opens the plan."""
    plan_tab, _fire, here = _tabs()
    with project.using(here), _boxes() as shown:
        _import(plan_tab, here, "Chosen.pdf", pages=1)
        before = set(plan_tab.taken_ids())
        plan_tab.on_page_toggled(1, True)
        plan_tab.on_doc_crop(1, (10.0, 10.0, 100.0, 60.0))
        plan_tab.on_doc_crop(1, (150.0, 20.0, 120.0, 70.0))
        first, second = sorted(set(plan_tab.taken_ids()) - before)
        _click(plan_tab, 1, 50.0, 40.0)
        assert plan_tab.doc_view.selected_frames() == [first] and plan_tab.current_id == first
        assert plan_tab.view_kind == "document" and plan_tab.center.currentWidget() is plan_tab.doc_view
        assert plan_tab.frame_module_shown() and plan_tab.frame_box.isAncestorOf(plan_tab.plan_group)
        assert plan_tab.plan_group.isVisibleTo(plan_tab.frame_box) and not plan_tab.doc_card.isVisibleTo(plan_tab.right)
        plan_tab.name_edit.setText("Ost")
        plan_tab.on_meta()
        plan_tab.storey_combo.setEditText("1.OG")
        assert plan_tab.dirty
        plan_tab.name_edit.editingFinished.emit()
        _STATE["app"].processEvents()
        source = _json(here.plans_dir / f"{first}.json")
        assert source.get("name") == "Ost" and source.get("storey") == "1.OG", source
        assert not plan_tab.dirty
        label = next(c["label"] for c in plan_tab.doc_view.area.crops[1] if c["plan"] == first)
        assert "Ost" in label and "1.OG" in label, label
        assert plan_tab.doc_view.selected_frames() == [first], "the frame stays chosen once its plan is written"
        # the other frame: the first plan left, the second shown
        _click(plan_tab, 1, 200.0, 50.0)
        assert plan_tab.current_id == second and plan_tab.doc_view.selected_frames() == [second]
        # outside both frames: let go, the module back in the plan's column, the document's card again
        _click(plan_tab, 1, 130.0, 95.0)
        assert plan_tab.doc_view.selected_frames() == [] and not plan_tab.frame_module_shown()
        assert plan_tab.properties_layout.indexOf(plan_tab.plan_group) >= 0 and plan_tab.doc_card.isVisibleTo(plan_tab.right)
        # chosen again, then the plan view shown: the module goes home with it
        _click(plan_tab, 1, 200.0, 50.0)
        assert plan_tab.frame_module_shown()
        plan_tab.show_plan_view()
        assert not plan_tab.frame_module_shown() and plan_tab.properties_layout.indexOf(plan_tab.plan_group) >= 0
        assert [c for c, _w in plan_tab.modules if c is plan_tab.plan_group]
        # a double click opens the plan
        plan_tab.open_document(plan_tab.doc_id)
        _settle(plan_tab)
        _click(plan_tab, 1, 50.0, 40.0, double=True)
        assert plan_tab.view_kind == "plan" and plan_tab.current_id == first
        assert not [k for k, _t in shown if k in ("warning", "critical")], shown
        _done(plan_tab)


def test_suppr_archives_the_plans_of_the_frames_chosen_asking_where_something_is_drawn():
    plan_tab, _fire, here = _tabs()
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QMessageBox
    with project.using(here), _boxes():
        _import(plan_tab, here, "Deleted.pdf", pages=1)
        before = set(plan_tab.taken_ids())
        plan_tab.on_page_toggled(1, True)
        plan_tab.on_doc_crop(1, (10.0, 10.0, 100.0, 60.0))
        plan_tab.on_doc_crop(1, (150.0, 20.0, 120.0, 70.0))
        first, second = sorted(set(plan_tab.taken_ids()) - before)
        source = _json(here.plans_dir / f"{first}.json")
        source["elements"] = [{"type": "S", "label": "S001", "points": [[50, 40]]}]
        plan_tab.write_plan(source)
        _click(plan_tab, 1, 200.0, 50.0)
        with _boxes() as shown:
            QTest.keyClick(plan_tab.doc_view.area, Qt.Key.Key_Delete)
            _STATE["app"].processEvents()
        assert not shown and second not in plan_tab.taken_ids(), "a plan with nothing drawn is archived without a word"
        assert list((here.plans_dir / "archives").glob(f"*-{second}.json"))
        _click(plan_tab, 1, 50.0, 40.0)
        with _boxes(answer=QMessageBox.StandardButton.No) as shown:
            QTest.keyClick(plan_tab.doc_view.area, Qt.Key.Key_Delete)
        assert [k for k, _t in shown] == ["question"] and first in plan_tab.taken_ids(), "something drawn: asked, and kept on No"
        with _boxes() as shown:
            plan_tab.on_frames_delete([first])
        assert first not in plan_tab.taken_ids() and plan_tab.doc_view.used_pages() == []
        _done(plan_tab)


def test_the_documents_are_each_tab_s_own():
    """A document imported in a tab is that tab's (`owner`) and listed there alone; a document written before v0.116 is the position plans', unless only fire plans with a frame of their own are drawn on it."""
    plan_tab, fire_tab, here = _tabs()
    from domains import plan_documents, plan_pages
    with project.using(here), _boxes():
        mine = _import(plan_tab, here, "Positions.pdf", pages=1)
        assert plan_documents.read(here, mine)["owner"] == "plan" and plan_documents.read(here, mine)["schema_version"] == "1.1"
        theirs = _import(fire_tab, here, "Brandschutz.pdf", pages=1)
        assert plan_documents.read(here, theirs)["owner"] == "fire"
        plan_tab.reload_documents()
        fire_tab.reload_documents()
        listed = lambda tab: {tab.doc_list.item(i).data(0x0100) for i in range(tab.doc_list.count())}
        assert mine in listed(plan_tab) and theirs not in listed(plan_tab)
        assert theirs in listed(fire_tab) and mine not in listed(fire_tab)
        # a fire plan on the fire tab's document, ticked there: a frame of its own
        fire_tab.open_document(theirs)
        _settle(fire_tab)
        before = set(fire_tab.taken_ids())
        fire_tab.on_page_toggled(1, True)
        (fid,) = set(fire_tab.taken_ids()) - before
        assert "plan" not in _json(here.fire_dir / f"{fid}.json")
        # a document written before 1.1: owned by what is drawn on it
        legacy = dict(plan_documents.read(here, theirs))
        legacy.pop("owner")
        legacy["schema_version"] = "1.0"
        plan_documents.write(here, legacy)
        assert plan_documents.read(here, theirs)["schema_version"] == "1.0"
        usage = plan_pages.document_usage(here)
        assert usage[theirs]["fire_own"] == 1 and usage[theirs]["position"] == 0
        assert plan_pages.document_owner(plan_documents.read(here, theirs), usage) == "fire"
        fire_tab.reload_documents()
        plan_tab.reload_documents()
        assert theirs in listed(fire_tab) and theirs not in listed(plan_tab)
        assert plan_pages.document_owner({"id": "D99"}, usage) == "plan", "a document nothing is drawn on is the position plans'"
        assert plan_pages.document_owner({"id": theirs}, {theirs: {"position": 1, "fire_own": 1, "fire_follow": 0}}) == "plan"
        # an owner that is no tab is refused
        try:
            plan_documents.write(here, dict(legacy, owner="statics"))
        except Exception as exc:
            assert "owner" in str(exc)
        else:
            assert False, "an owner that is no tab was written"
        fire_tab.on_page_toggled(1, False)
        _done(plan_tab, fire_tab)


def test_a_fire_tab_s_frames_follow_its_page_then_have_frames_of_their_own():
    """In the fire tab: the first frame drawn on a page carrying one position plan and no fire plan follows that plan, its frame a crop of its own; every further frame a fire plan of a frame of its own on the page (the engineer's answer 9)."""
    plan_tab, fire_tab, here = _tabs()
    with project.using(here), _boxes():
        docid = _import(plan_tab, here, "Shared.pdf", pages=1)
        before = set(plan_tab.taken_ids())
        plan_tab.on_page_toggled(1, True)
        (pid,) = set(plan_tab.taken_ids()) - before
        fire_tab.open_document(docid)
        _settle(fire_tab)
        before = set(fire_tab.taken_ids())
        fire_tab.on_doc_crop(1, (10.0, 10.0, 100.0, 60.0))
        (first,) = set(fire_tab.taken_ids()) - before
        source = _json(here.fire_dir / f"{first}.json")
        assert source["plan"] == pid and source["crop"] == {"x": 10.0, "y": 10.0, "w": 100.0, "h": 60.0}
        fire_tab.on_doc_crop(1, (150.0, 20.0, 120.0, 70.0))
        (second,) = set(fire_tab.taken_ids()) - before - {first}
        source = _json(here.fire_dir / f"{second}.json")
        assert "plan" not in source and source["background"]["document"] == docid and source["crop"]["x"] == 150.0
        crops = {c["plan"] for c in fire_tab.doc_view.area.crops[1] if not c.get("other")}
        assert crops == {first, second}
        fire_tab.on_page_toggled(1, False)
        plan_tab.open_document(docid)
        plan_tab.on_page_toggled(1, False)
        _done(plan_tab, fire_tab)


def test_a_layer_switched_is_written_at_once_and_exported_in_the_background():
    """The document written as the layer is switched, the plans exported LAYER_EXPORT_MS after the last switch in a thread -- and finished before any other export or the tab being left (finish_layer_export), so data/ is never written twice at once."""
    plan_tab, _fire, here = _tabs()
    import drawing_tab
    from domains import plan_documents
    with project.using(here), _boxes() as shown:
        docid = _import(plan_tab, here, "Layered.pdf", pages=1)
        before = set(plan_tab.taken_ids())
        plan_tab.on_page_toggled(1, True)
        (pid,) = set(plan_tab.taken_ids()) - before
        plan_tab.on_layers_changed(["Walls"])
        assert plan_documents.read(here, docid)["layers_off"] == ["Walls"]
        assert plan_tab.layer_timer.isActive(), "the export waits for the switches to stop"
        record = _json(here.data_dir / "plans.json")["plans"][pid]["background"]
        assert record["layers_off"] != ["Walls"], "nothing is exported at the switch itself"
        plan_tab.start_layer_export()
        plan_tab.layer_timer.stop()
        drawing_tab._Background.thread.join(60)
        _STATE["app"].processEvents()
        record = _json(here.data_dir / "plans.json")["plans"][pid]["background"]
        assert record["layers_off"] == ["Walls"], record
        # pending when something else exports: run first, in the window's thread
        plan_tab.on_layers_changed(["Walls", "Furniture"])
        plan_tab.finish_layer_export()
        assert not plan_tab.layer_timer.isActive()
        assert _json(here.data_dir / "plans.json")["plans"][pid]["background"]["layers_off"] == ["Furniture", "Walls"]
        assert not shown, shown
        plan_tab.on_page_toggled(1, False)
        _done(plan_tab)


def test_zz_the_end_closes_the_window_and_puts_the_caches_back():
    """Last of the file -- the runner takes the tests by name: the window closed, which finishes a layer's export still under way (confirm_leave), and plan_documents' cache put back."""
    if "window" in _STATE:
        plan_tab, fire_tab, _here = _tabs()
        _done(plan_tab, fire_tab)
        app = _STATE["app"]
        _STATE["window"].close()
        app.processEvents()
        from domains import plan_documents
        plan_documents.CACHE_ROOT = _STATE["cache"]


# --- what needs no window: the incremental update, and a configuration seen before served from the cache ---------------------------------------------------

def _place(name):
    from domains import plan_documents
    root = conftest.tmpdir(f"docframes_{name}")
    (root / "01_Pläne").mkdir()
    (root / "Woodcore-Datei" / "plans").mkdir(parents=True)
    plan_documents.CACHE_ROOT = root / "_cache"
    return plan_documents.Place(root, root / "Woodcore-Datei" / "plans")


def test_a_layer_switched_is_an_incremental_update_of_the_pdf_both_kinds_of_cross_reference_alike():
    """render_source appends the default configuration to the file rather than rewriting it (v0.116): the file's own bytes first, a few hundred bytes after them; and PDFium renders the update -- of a cross-reference table, and of a cross-reference stream -- pixel for pixel as it renders the whole file rewritten (_pdf_with_state)."""
    from domains import plan_documents as documents
    kept = documents.CACHE_ROOT
    try:
        place = _place("incremental")
        path = fx.write(place.root / "01_Pläne" / "Plan.pdf")
        doc = documents.import_file(place, path)
        original = path.read_bytes()
        for off in (["Walls"], ["Dims", "Furniture"], []):
            doc["layers_off"] = list(off)
            view = documents.render_source(place, doc)
            data = view.read_bytes()
            assert data.startswith(original) and len(data) - len(original) < 4096, (off, len(data) - len(original))
            full = place.root / "full.pdf"
            full.write_bytes(documents._pdf_with_state(path, [0], off))
            assert fx.render(view)[0] == fx.render(full)[0], off
        # a cross-reference stream: the update of an update written as a stream, then updated again by the file's own kind
        stream = place.root / "stream.pdf"
        stream.write_bytes(documents._with_state_update(path, ["Dims"], section="stream"))
        again = place.root / "again.pdf"
        again.write_bytes(documents._with_state_update(stream, ["Walls"]))
        tail = again.read_bytes()[len(stream.read_bytes()):]
        assert b"/XRef" in tail and b"trailer" not in tail,"the second update is a stream, as the file's last section is"
        full = place.root / "full.pdf"
        full.write_bytes(documents._pdf_with_state(path, [0], ["Walls"]))
        assert fx.render(again)[0] == fx.render(full)[0]
        from pypdf import PdfReader
        default = PdfReader(again).trailer["/Root"]["/OCProperties"]["/D"]
        assert [g.get_object()["/Name"] for g in default["/OFF"]] == ["Walls"]
        # turned pages: the turned copy made once, the layers appended to it
        documents.set_rotation(doc, 1, 90)
        doc["layers_off"] = ["Walls"]
        view = documents.render_source(place, doc)
        assert [int(p.rotation) for p in PdfReader(view).pages] == [90]
        assert view.read_bytes().startswith(documents._turned(doc, path, [90]).read_bytes()), "the layers appended to the turned copy"
        # the flattened page is kept: asked again, the same bytes, from the cache
        doc["pages"][0]["rotation"] = 0
        first = documents.flatten_page(place, doc, 1)
        cached = [p for p in documents.cache_dir().glob("*.pdf")]
        assert documents.flatten_page(place, doc, 1) == first and len(list(documents.cache_dir().glob("*.pdf"))) == len(cached)
    finally:
        documents.CACHE_ROOT = kept


def test_a_layer_configuration_seen_before_is_shown_again_from_the_cache_without_a_render():
    """Switching a layer off, on and off again: the third view is the first one's -- the same copy, its pages taken from the renders kept, not one render asked of PDFium (PageArea.sent)."""
    app = _qt()
    import document_view
    from domains import plan_documents as documents
    kept = documents.CACHE_ROOT
    try:
        place = _place("seen")
        doc = documents.import_file(place, fx.write(place.root / "01_Pläne" / "Plan.pdf", pages=3))
        view = document_view.DocumentView(lang="fr")
        view.resize(900, 640)
        view.show()
        app.processEvents()
        view.set_document(place, doc)

        def idle():
            end = time.monotonic() + 60
            while view.is_busy() or not view.area.pages:
                if time.monotonic() > end:
                    raise AssertionError("the view is still busy")
                app.processEvents()
                time.sleep(0.01)

        idle()
        view.set_zoom(1.0)
        idle()
        from PySide6.QtCore import Qt

        def switch(on):
            item = next(view.panel.list.item(i) for i in range(view.panel.list.count()) if view.panel.list.item(i).text() == "Walls")
            item.setCheckState(Qt.CheckState.Checked if on else Qt.CheckState.Unchecked)
            idle()

        switch(False)
        off_source = view.area.sources[0][0]
        switch(True)
        sent = view.area.sent
        switch(False)
        assert view.area.sources[0][0] == off_source, "the same configuration is the same copy"
        assert view.area.sent == sent, f"{view.area.sent - sent} render(s) asked for a configuration seen before"
        (px, py), _green = fx.COLOURS["green"]
        shown = view.area.base[1]
        colour = shown.image.pixelColor(round(px * shown.image.width() / fx.WIDTH), round((fx.HEIGHT - py) * shown.image.height() / fx.HEIGHT))
        a = colour.alphaF()
        seen = tuple(round(v * a + 255 * (1 - a)) for v in (colour.red(), colour.green(), colour.blue()))
        assert seen == (255, 255, 255) or abs(seen[0] - 255) < 40, f"the walls are gone from the page: {seen}"
        view.set_document(None, None)
        view.close()
        app.processEvents()
    finally:
        documents.CACHE_ROOT = kept
