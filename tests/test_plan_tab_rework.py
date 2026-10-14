"""The position plan tab reworked (v0.114, calc/tools/plan_tab.py, docs/domain/position-plans.md §3.3sexies, docs/ui/window.md §10quater): documents imported and cut into plans on their pages with no dialog, a crop, a calibration and a turn drawn on a page written into that page's plan, a plan saved on leaving it, the storey proposing the numbering character, a tool with no position creating a blank one, the «Commande Typst» entry and the export sheets beside the plans.

The window is built once, off-screen, on a copy of the example project (conftest.project_copy), whose plans carry no document. The documents are tests/fixtures/layered_pdf.py's PDF of three pages, written into the copy. Every message box and dialog is stubbed -- a modal off-screen never comes back -- and every box shown is recorded, so a test can say that **none** was. plan_documents' caches are pointed into the test's own folder and put back afterwards; the window's export after a blank position, which would run the whole pipeline, is recorded rather than run.
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


def _window():
    if "window" not in _STATE:
        app = _qt()
        conftest.exported("plans.json")
        here = conftest.project_copy("plan_tab_rework")
        from domains import plan_documents
        _STATE["cache"] = plan_documents.CACHE_ROOT
        plan_documents.CACHE_ROOT = conftest.tmpdir("plan_tab_rework_cache")
        (here.root / "01_Pläne").mkdir(exist_ok=True)
        # the copy carries no backgrounds (conftest.project_copy), and a plan drawn on a file that is not there stops the plans' export: they are drawn on an empty sheet here
        for path in here.plans_dir.glob("*.json"):
            source = json.loads(path.read_text(encoding="utf-8"))
            source.pop("background", None)
            path.write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        with project.using(here), _boxes():
            import woodcore_gui
            window = woodcore_gui.MainWindow()
        exports = []
        window.reexport = lambda **kwargs: exports.append(kwargs)
        _STATE.update(app=app, window=window, here=here, exports=exports)
    return _STATE["window"], _STATE["here"]


def _tab():
    window, here = _window()
    import plan_tab
    tab = next(t for t in window.tabs if isinstance(t, plan_tab.PlanTab))
    tab.dirty = False
    return tab, here


def _settle(tab, timeout=60):
    """The document view idle: nothing being read or rendered -- so that a PDF is never held open by a render the test has gone past."""
    app = _STATE["app"]
    end = time.monotonic() + timeout
    while tab.doc_view.is_busy():
        if time.monotonic() > end:
            raise AssertionError("the document view is still busy")
        app.processEvents()
        time.sleep(0.01)


@contextlib.contextmanager
def _boxes(answer=None, file=None, length=None):
    """The message boxes and the dialogs stubbed: every box shown recorded; a question answered by `answer` (Yes where none is given); the file dialog answers `file`; the length asked for a calibration `length`."""
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


def _import(tab, here, name="Plan.pdf", pages=3):
    path = fx.write(here.root / "01_Pläne" / name, pages=pages)
    with _boxes(file=path) as shown:
        assert tab.import_document(), shown
    return tab.doc_id, shown


def _plan(here, pid):
    return json.loads((here.plans_dir / f"{pid}.json").read_text(encoding="utf-8"))


def _done(tab):
    tab.doc_view.set_document(None, None)
    _settle(tab)
    tab.show_plan_view()
    tab.dirty = False


def test_importing_a_pdf_lists_it_and_opens_every_page_with_no_dialog():
    """«Importer…» with no dialog of pages: the document listed «D01 – Plan.pdf», chosen, and shown in the middle -- its card on the right; no box at all."""
    tab, here = _tab()
    with project.using(here), _boxes():
        docid, shown = _import(tab, here)
        assert not shown, shown
        assert tab.view_kind == "document" and tab.center.currentWidget() is tab.doc_view
        assert tab.doc_list.currentItem().text() == f"{docid} – Plan.pdf"
        assert tab.doc_view.document()["id"] == docid and tab.doc_pages_text.text() == "3"
        _settle(tab)
        assert [i.page for i in tab.doc_view.area.pages] == [1, 2, 3]
        _done(tab)


def test_ticking_a_page_makes_a_plan_of_it_and_unticking_archives_it():
    """A page ticked: a plan, its background the document's page, its sheet the page's size, saved and exported; unticked with nothing drawn: archived without a word; with something drawn: asked first."""
    tab, here = _tab()
    with project.using(here), _boxes():
        docid, _shown = _import(tab, here, "Ticked.pdf")
        before = set(tab.taken_ids())
        with _boxes() as shown:
            tab.on_page_toggled(2, True)
        assert not shown, shown
        (pid,) = set(tab.taken_ids()) - before
        source = _plan(here, pid)
        assert source["background"]["document"] == docid and source["background"]["page"] == 2
        assert source["sheet"] == {"width": 300.0, "height": 100.0}
        assert tab.doc_view.used_pages() == [2]
        records = json.loads((here.data_dir / "plans.json").read_text(encoding="utf-8"))["plans"]
        assert pid in records, "the plan made is not exported"
        with _boxes() as shown:
            tab.on_page_toggled(2, False)
        assert not shown and pid not in tab.taken_ids(), "a plan with nothing drawn on it was not archived silently"
        assert tab.doc_view.used_pages() == []
        # drawn on: asked, and kept on «No»
        tab.on_page_toggled(3, True)
        (pid,) = set(tab.taken_ids()) - before
        source = _plan(here, pid)
        source["elements"] = [{"type": "S", "label": "S001", "points": [[50, 50]]}]
        tab.write_plan(source)
        from PySide6.QtWidgets import QMessageBox
        with _boxes(answer=QMessageBox.StandardButton.No) as shown:
            tab.on_page_toggled(3, False)
        assert [k for k, _t in shown] == ["question"] and pid in tab.taken_ids() and tab.doc_view.used_pages() == [3]
        with _boxes() as shown:
            tab.on_page_toggled(3, False)
        assert pid not in tab.taken_ids()
        _done(tab)


def test_a_crop_and_a_calibration_drawn_on_a_page_are_that_page_s_plan_s():
    tab, here = _tab()
    with project.using(here), _boxes():
        _import(tab, here, "Cropped.pdf", pages=1)
        before = set(tab.taken_ids())
        tab.on_page_toggled(1, True)
        (pid,) = set(tab.taken_ids()) - before
        with _boxes() as shown:
            tab.on_doc_crop(1, (10.0, 20.0, 150.0, 60.0))
        assert not shown, shown
        assert _plan(here, pid)["crop"] == {"x": 10.0, "y": 20.0, "w": 150.0, "h": 60.0}
        crops = tab.doc_view.area.crops[1]
        assert crops[0]["plan"] == pid and crops[0]["label"].startswith(pid)
        with _boxes(length=2.5):
            tab.on_doc_calibrated(1, [(0.0, 0.0), (100.0, 0.0)])
        assert _plan(here, pid)["scale"] == {"mode": "calibration", "points": [[0.0, 0.0], [100.0, 0.0]], "length_m": 2.5}
        _done(tab)


def test_turning_a_page_turns_the_document_and_what_is_drawn_on_it():
    """A page turned a quarter clockwise: the document's rotation, and the plan's elements and sheet turned with it (plan.rotate_source) -- a column at (10, 20) of a page 100 high lands at (80, 10)."""
    tab, here = _tab()
    with project.using(here), _boxes():
        docid, _shown = _import(tab, here, "Turned.pdf", pages=1)
        before = set(tab.taken_ids())
        tab.on_page_toggled(1, True)
        (pid,) = set(tab.taken_ids()) - before
        source = _plan(here, pid)
        source["elements"] = [{"type": "S", "label": "S001", "points": [[10, 20]]}]
        tab.write_plan(source)
        with _boxes() as shown:
            assert tab.rotate_page(docid, 1, 90)
        assert not shown, shown
        from domains import plan_documents
        assert plan_documents.rotation(plan_documents.read(here, docid), 1) == 90
        turned = _plan(here, pid)
        assert turned["elements"][0]["points"] == [[80, 10]], turned["elements"]
        assert turned["sheet"] == {"width": 100, "height": 300}
        _done(tab)


def test_a_layer_switched_writes_the_document():
    tab, here = _tab()
    with project.using(here), _boxes():
        docid, _shown = _import(tab, here, "Layers.pdf", pages=1)
        with _boxes() as shown:
            tab.on_layers_changed(["Walls"])
        assert not shown, shown
        from domains import plan_documents
        assert plan_documents.read(here, docid)["layers_off"] == ["Walls"]
        _done(tab)


def test_leaving_a_plan_saves_it_without_a_question():
    """Autosave (the engineer's request of 06.10.2026): a plan changed and another chosen -- the change written, no box shown, the dot gone."""
    tab, here = _tab()
    with project.using(here), _boxes():
        first, second = tab.taken_ids()[:2]
        tab.load(first)
        tab.show_plan_view()
        tab.label_edit.setText("Autosaved")
        tab.on_meta()
        assert tab.dirty
        with _boxes() as shown:
            tab.on_list_change(second)
        assert not shown, shown
        assert tab.current_id == second and not tab.dirty
        assert _plan(here, first)["label"] == "Autosaved"


def test_the_storey_proposes_the_numbering_character_until_one_is_typed():
    tab, here = _tab()
    with project.using(here), _boxes():
        import plan_tab
        from domains import plan
        tab.new()
        storeys = plan.STOREYS[tab.app.lang]
        tab.storey_combo.setEditText(storeys[3])     # the 1st floor
        assert tab.floor_edit.text() == "1" and tab.source["floor"] == "1" and tab.source["storey"] == storeys[3]
        tab.storey_combo.setEditText(storeys[0])     # a basement
        assert tab.floor_edit.text() == "U"
        tab.floor_edit.setText("7")
        tab.on_floor_typed("7")
        tab.storey_combo.setEditText(storeys[2])
        assert tab.floor_edit.text() == "7", "a character typed by the engineer was written over"
        # the left pane's line: id – name – storey
        tab.name_edit.setText("Hauptgebäude")
        tab.on_meta()
        assert tab.save()
        pid = tab.current_id
        rows = {entry: item.text(0) for item, entry in tab.list.rows()}
        assert rows[pid] == f"{pid} – Hauptgebäude – {storeys[2]}", rows[pid]
        assert plan_tab.plan_text("P09", {"label": "Grundriss"}) == "P09 – Grundriss"


def test_a_new_element_is_numbered_on_and_its_position_is_made_by_the_save():
    """Issue #9 (REQ-003, REQ-007, D-009): every element drawn takes the next number of its letter on the plan's storey -- A101, A102 --, nothing is written while it is drawn, so drawing, undoing and drawing again leaves no gap; «Enregistrer» makes the positions with the plan, each with the section of the last of its type; and the save then has the window export them."""
    tab, here = _tab()
    with project.using(here), _boxes():
        import positions_store
        rows = positions_store.read(here)
        rows.append({"position": "A001", "type": positions_store.type_for("A"), "section_type": "rec", "dimension": "60/120", "units": "mm"})
        positions_store.write(here, rows)
        tab.reread_positions()
        tab.new()
        tab.floor_edit.setText("1")
        tab.on_floor_typed("1")
        before = positions_store.path(here).read_bytes()
        tab.choose_tool("A")
        tab.canvas.add_element("A", [[10, 10], [200, 10]])
        tab.canvas.add_element("A", [[10, 50], [200, 50]])
        assert [e["label"] for e in tab.source["elements"]] == ["A101", "A102"]
        assert positions_store.path(here).read_bytes() == before, "nothing is written while drawing"
        tab.undo()
        tab.canvas.add_element("A", [[10, 90], [200, 90]])
        assert [e["label"] for e in tab.source["elements"]] == ["A101", "A102"], "undone and drawn again: no gap"
        assert tab.pending_positions()["A101"]["dimension"] == "60/120", "the section of the last A"
        exports = len(_STATE["exports"])
        assert tab.save()
        rows = {r["position"]: r for r in positions_store.read(here)}
        assert rows["A101"]["dimension"] == rows["A102"]["dimension"] == "60/120" and rows["A101"]["units"] == "mm"
        assert "_pending_positions" not in json.loads((here.plans_dir / f"{tab.current_id}.json").read_text(encoding="utf-8")), "the draft's own key never reaches the file"
        assert len(_STATE["exports"]) == exports + 1, "the positions made were not exported with the plan"


def test_an_element_taken_off_offers_its_position_s_deletion_and_numbers_the_next_again():
    """Issue #9 (REQ-004, D-002, D-009): the save after an element is deleted asks -- the plan's position no plan draws any more --, and on a yes A101 goes, A102 becomes A101 in positions.json and in the plan, with an empty history: what was written is no step of «Annuler»."""
    window, here = _window()
    import plan_tab
    import positions_store
    import renumber_dialog
    tab = next(t for t in window.tabs if isinstance(t, plan_tab.PlanTab))
    asked = []
    renumber_dialog.CONFIRM = lambda result: (asked.append(result) or True, [])
    try:
        with project.using(here), _boxes():
            tab.new()
            tab.floor_edit.setText("2")
            tab.on_floor_typed("2")
            tab.choose_tool("A")
            tab.canvas.add_element("A", [[10, 10], [200, 10]])
            tab.canvas.add_element("A", [[10, 50], [200, 50]])
            assert tab.save()
            pid = tab.current_id
            assert {"A201", "A202"} <= {r["position"] for r in positions_store.read(here)}
            tab.canvas.selection = ("element", 0)
            tab.edit(lambda: tab.source["elements"].pop(0))
            assert tab.save()
            assert asked and asked[-1].deleted == ["A201"] and asked[-1].mapping == {"A202": "A201"}
            ids = [r["position"] for r in positions_store.read(here)]
            assert "A201" in ids and "A202" not in ids
            assert [e["label"] for e in json.loads((here.plans_dir / f"{pid}.json").read_text(encoding="utf-8"))["elements"]] == ["A201"]
            assert [e["label"] for e in tab.source["elements"]] == ["A201"] and tab.undo_stack == [], "read again, with no history"
    finally:
        renumber_dialog.CONFIRM = None


def _pane(tab):
    """The selection card's rows as (label text, field) in their order -- what the right pane shows."""
    rows = []

    def walk(layout):
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.layout() is not None:
                walk(item.layout())
            elif item.widget() is not None:
                rows.append(item.widget())
    walk(tab.selection_layout)
    return rows


def _texts(tab):
    from PySide6.QtWidgets import QLabel
    return [w.text() for w in _pane(tab) if isinstance(w, QLabel)]


def test_a_drawing_tool_shows_its_elements_options_at_once_and_they_are_the_next_elements():
    """Issue #9 (REQ-015, D-014): «à l'activation d'un outil de dessin (par exemple S pour un poteau), afficher tout de suite dans le volet de droite les options de l'objet, comme si un objet déjà dessiné du même type était sélectionné. Vaut pour tous les outils de dessin.» What is set there is the next element's, and only what it may carry."""
    from PySide6.QtWidgets import QDoubleSpinBox
    tab, here = _tab()
    with project.using(here), _boxes():
        tab.new()
        tab.floor_edit.setText("3")
        tab.on_floor_typed("3")
        for tool in ("V", "H", "W", "T", "S", "A", "D", "Ö", "B", "M", "L"):
            tab.choose_tool(tool)
            assert tab.has_selection() and tab.t("plan_tool_defaults_note") in _texts(tab), tool
        tab.choose_tool("S")
        texts = _texts(tab)
        assert "S301" in texts and tab.t("plan_section_copy") in texts and tab.t("plan_element_angle") in texts, texts
        spin = next(w for w in _pane(tab) if isinstance(w, QDoubleSpinBox))
        spin.setValue(45)
        spin.editingFinished.emit()
        assert tab.canvas.tool_defaults["S"]["angle"] == 45
        tab.canvas.tool_defaults["S"]["section"] = {"section_type": "rec", "dimension": "140/140", "units": "mm"}
        tab.canvas.add_element("S", [[10, 10]])
        column = tab.source["elements"][-1]
        assert column["label"] == "S301" and column["angle"] == 45, column
        assert tab.pending_positions()["S301"]["dimension"] == "140/140", "the section the tool states"
        assert tab.has_selection() and tab.t("plan_tool_defaults_note") in _texts(tab), "the pane stays the tool's while it is chosen"
        tab.canvas.tool_defaults["M"] = {"angle": 30}
        tab.choose_tool("M")
        tab.canvas.add_element("M", [[10, 100], [200, 100]])
        assert "angle" not in tab.source["elements"][-1], "an Auflager drawn with two points is not turned"
        # with «Sélection» the pane is the element's again, its Section above its position (UI-002)
        tab.choose_tool("select")
        tab.canvas.selection = ("element", 0)
        tab.refresh_selection()
        texts = _texts(tab)
        assert texts.index(tab.t("plan_section_copy")) < texts.index(tab.t("plan_number")), texts
        assert tab.save()
        import positions_store
        rows = {r["position"]: r for r in positions_store.read(here)}
        assert (rows["S301"]["section_type"], rows["S301"]["dimension"]) == ("rec", "140/140")


def _copy_combo(tab):
    from PySide6.QtWidgets import QComboBox
    return next(w for w in _pane(tab) if isinstance(w, QComboBox) and w.count() and w.itemText(0) == tab.t("plan_section_copy_none"))


def test_numbers_follow_one_another_by_letter_and_storey_and_a_section_is_copied_without_a_link():
    """Issue #9 (REQ-003, REQ-006, UI-002, D-007, D-011): S101, S102, S103; T101; S201 on the storey above -- here on the 5th and 6th floors, which the example has no position of. The *Section* field offers the other positions and not the element's own; a section taken from one is a copy: the position copied from changed afterwards leaves it as it was, and «Annuler» before the save takes the copy back."""
    tab, here = _tab()
    with project.using(here), _boxes():
        import positions_store
        rows = positions_store.read(here)
        rows.append({"position": "T590", "type": positions_store.type_for("T"), "section_type": "rec", "dimension": "80/200", "units": "mm"})
        positions_store.write(here, rows)
        tab.reread_positions()
        tab.new()
        tab.floor_edit.setText("5")
        tab.on_floor_typed("5")
        tab.choose_tool("S")
        for x in (10, 60, 110):
            tab.canvas.add_element("S", [[x, 10]])
        tab.choose_tool("T")
        tab.canvas.add_element("T", [[10, 200], [300, 200]])
        assert [e["label"] for e in tab.source["elements"]] == ["S501", "S502", "S503", "T591"], "T590 is taken: the next T of the floor"
        # the Section of S502: the other positions offered, its own not
        tab.choose_tool("select")
        tab.canvas.selection = ("element", 1)
        tab.refresh_selection()
        combo = _copy_combo(tab)
        offered = [combo.itemData(i) for i in range(combo.count())]
        assert "T590" in offered and "S502" not in offered, offered
        before = dict(tab.pending_positions().get("S502", {}))
        combo.setCurrentIndex(combo.findData("T590"))
        combo.activated.emit(combo.currentIndex())
        assert tab.pending_positions()["S502"]["dimension"] == "80/200"
        # T590 changed afterwards: S502 keeps what was copied
        rows = positions_store.read(here)
        next(r for r in rows if r["position"] == "T590")["dimension"] = "100/240"
        positions_store.write(here, rows)
        tab.reread_positions()
        assert tab.pending_positions()["S502"]["dimension"] == "80/200", "a copy, never a link"
        tab.undo()
        assert tab.pending_positions().get("S502", {}).get("dimension") == before.get("dimension"), "«Annuler» before the save takes the copy back"
        tab.canvas.selection = ("element", 1)
        tab.refresh_selection()
        combo = _copy_combo(tab)
        combo.setCurrentIndex(combo.findData("T590"))
        combo.activated.emit(combo.currentIndex())
        assert tab.save()
        saved = {r["position"]: r for r in positions_store.read(here)}
        assert {"S501", "S502", "S503", "T591"} <= set(saved)
        assert saved["S502"]["dimension"] == "100/240" and saved["T590"]["dimension"] == "100/240", "copied again after T590 changed: its section of now"
        # the storey above starts again at 01
        tab.new()
        tab.floor_edit.setText("6")
        tab.on_floor_typed("6")
        tab.choose_tool("S")
        tab.canvas.add_element("S", [[10, 10]])
        assert tab.source["elements"][-1]["label"] == "S601"
        assert tab.save()


def test_a_column_turned_by_its_circle_is_one_step_of_annuler_and_its_field_follows():
    """Issue #9 (REQ-002): the circle dragged turns the column, the angle field of the pane shows the angle reached, and «Annuler» puts the column back as it was -- one step for the whole drag."""
    from test_plan_canvas_rework import _drag
    tab, here = _tab()
    import plan_canvas_tools as tools
    with project.using(here), _boxes():
        tab.new()
        tab.floor_edit.setText("7")
        tab.on_floor_typed("7")
        tab.choose_tool("S")
        tab.canvas.add_element("S", [[400, 300]])
        tab.choose_tool("select")
        tab.canvas.select(("element", 0))
        tab.refresh_selection()
        tab.canvas.show()
        tab.canvas.resize(900, 600)
        tab.canvas.centerOn(400, 300)
        steps = len(tab.undo_stack)
        column = tab.source["elements"][0]
        at = tools.rotation_point(tab.canvas, column)
        _drag(tab.canvas, at, (460, 300))
        column = tab.source["elements"][0]
        assert abs(column["angle"] - 90) < 3, column   # the pointer moves by whole pixels at this zoom
        assert len(tab.undo_stack) == steps + 1, "the whole drag is one step"
        assert abs(tab.angle_spin.value() - column["angle"]) < 0.05, (tab.angle_spin.value(), column["angle"])
        tab.undo()
        assert "angle" not in tab.source["elements"][0], "«Annuler» puts the column back"
        tab.dirty = False


def test_a_tool_s_defaults_survive_a_language_switch():
    """Issue #9 (REQ-015): what is set for a tool's next element is kept when the window is built again in another language, as its variants were."""
    window, here = _window()
    import plan_tab
    tab, _ = _tab()
    tab.canvas.tool_defaults["S"] = {"angle": 30.0, "section": {"section_type": "rec", "dimension": "140/140", "units": "mm"}}
    lang = window.lang
    try:
        with project.using(here), _boxes():
            window.lang = "de" if lang != "de" else "fr"
            _release(tab)
            window.rebuild()
            tab = next(t for t in window.tabs if isinstance(t, plan_tab.PlanTab))
            assert tab.canvas.tool_defaults.get("S") == {"angle": 30.0, "section": {"section_type": "rec", "dimension": "140/140", "units": "mm"}}, tab.canvas.tool_defaults
    finally:
        with project.using(here), _boxes():
            window.lang = lang
            _release(tab)
            window.rebuild()
        tab, _ = _tab()
        tab.canvas.tool_defaults.clear()


def test_the_command_entry_shows_the_builder():
    tab, here = _tab()
    with project.using(here), _boxes():
        tab.set_view("typst")   # the «Commande Typst» row of v0.114 is the «Typst» view since v0.117
        assert tab.view_kind == "command" and tab.view == "typst"
        assert tab.center.currentWidget() is tab.builder.preview and tab.right.currentWidget().isAncestorOf(tab.builder.options)
        assert tab.builder.command().startswith("#show-plan(")
        tab.builder.stop()
        tab.show_plan_view()
        assert tab.center.currentWidget() is tab.center.widget(0) and tab.view == "draw"


def test_a_sheet_made_from_the_left_pane_is_listed_and_opened_in_the_editor():
    tab, here = _tab()
    with project.using(here), _boxes():
        with _boxes() as shown:
            sid = tab.new_sheet()
        assert sid and not [k for k, _t in shown if k in ("warning", "critical")], shown
        assert (here.typst_root / "Plans" / f"{sid}.typ").is_file()
        assert tab.sheet_list.ids().count(sid) == 1
        assert tab.view_kind == "sheet"
        assert tab.center.currentWidget() is tab.sheet_editor.canvas and tab.right.currentWidget().isAncestorOf(tab.sheet_editor.options)
        tab.sheet_editor.stop()
        tab.show_plan_view()


def test_every_writer_the_plan_tab_reaches_is_guarded_wherever_it_is_defined():
    """woodcore_gui.WRITERS wraps methods by NAME on the classes its loop lists, reading each class's own vars(): since v0.115 most of the plan tab's writers -- «Supprimer», a drop into a folder, a document or a sheet archived -- are drawing_tab.DrawingTab's, and they would lose the read-only guard in silence were the base not in that loop. Every writer reachable on PlanTab, on every class of its MRO that defines it, must be the guarded wrapper, and refuse on a project held read-only; and «replace_source», the undo helper, must never be one."""
    _qt()
    import types
    import drawing_tab
    import plan_tab
    import woodcore_gui
    assert "replace_source" not in woodcore_gui.WRITERS
    reached = []
    for name in woodcore_gui.WRITERS:
        if not hasattr(plan_tab.PlanTab, name):
            continue
        reached.append(name)
        for cls in plan_tab.PlanTab.__mro__:
            if name in vars(cls):
                assert hasattr(vars(cls)[name], "__wrapped__"), f"{cls.__name__}.{name} is not guarded by woodcore_gui.WRITERS"
    assert {"save", "delete", "on_moved", "delete_document", "delete_sheet"} <= set(reached), reached
    # v0.116: the PDF bundles, the sheets moved between them, the list of the positions and the document view's frames (WP-K)
    assert {"new_bundle", "rename_bundle", "delete_bundle", "on_sheets_moved", "export_bundle", "create_position_list", "write_frame_crop", "on_frames_delete"} <= set(reached), reached
    assert {"delete", "on_moved", "delete_document", "delete_sheet"} <= set({k: v for c in reversed(woodcore_gui.own_classes(drawing_tab.DrawingTab)) for k, v in vars(c).items()}), "the writers moved into the base (or its mixins, issue #30) are not where this test looks"
    refused = []
    app = types.SimpleNamespace(read_only=True, refuse_read_only=lambda: refused.append(True))
    fake = types.SimpleNamespace(app=app)
    for name in reached:
        assert getattr(plan_tab.PlanTab, name)(fake) is False, name
    assert len(refused) == len(reached)


def _release(tab):
    """The document view and the canvas let go of every PDF they hold -- a frame drawn in the document view opens its plan (v0.116), whose page the canvas then renders from the file, and the run's folder is removed afterwards, which Windows refuses for a file held open (test_fire_tab's own end); a tab the window builds again is left holding them otherwise."""
    _done(tab)
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


def test_the_end_puts_the_caches_back():
    """Last of the file: the document view released and plan_documents' cache put back -- a test must never leave the next one writing into a folder it removed."""
    if "window" in _STATE:
        tab, _here = _tab()
        _release(tab)
        from domains import plan_documents
        plan_documents.CACHE_ROOT = _STATE["cache"]
