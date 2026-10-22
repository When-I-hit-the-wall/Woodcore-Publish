"""The export sheet editor (v0.114, calc/tools/sheet_editor.py): a sheet `Plans/<id>.typ` shown as Typst compiles it, its objects framed over the page, dragged and resized there, and their options in cards beside it -- every change written between the object's tags through calc/sheets.py.

What is held:

* a sheet opens and **compiles into the cache, never into Plans/<id>.pdf**, which only the export writes;
* lib/sheet.typ's `<woodcore-sheet-box>` query gives **one box per object, in the file's order**, a plan's at the width it is printed at;
* **dragging a frame** writes the object's new x and y, and nothing outside that object's tags changes;
* **resizing a calibrated plan rounds its scale to a whole 1:n**; an uncalibrated one changes its width;
* the title block and the legend are put on and taken off;
* **an edit made elsewhere is read back**, and one the editor wrote is not taken for one;
* an object written by hand is rewritten only once `ask` says yes;
* the boxes are estimated where Typst cannot be asked, and the words are the same keys in three languages.

⚠️ Every check that compiles is skipped where `typst` is not on the path. Each works on the example project copied with its engine synced -- Pavillon calibrated at 1:100 of its page, Fluchttreppe made a section --, its previews compiled into a folder of the test's own.
"""

import json
import os
import shutil
import sys
import time

import conftest
from conftest import ROOT, Skip

TOOLS = ROOT / "calc" / "tools"
SAMPLE = ROOT / "tests" / "projet-exemple"


def _qt():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
        import PySide6.QtPdf  # noqa: F401
    except ImportError as exc:
        raise Skip(f"PySide6 or its QtPdf is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _need_typst():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")


def _project(name):
    """A copy of the example project with its engine, Pavillon calibrated at 1:100 of its PDF page and Fluchttreppe a section with a box for «EG» -- tests/test_sheets.py's own arrangement."""
    import project
    root = conftest.tmpdir(name) / "Exemple"
    shutil.copytree(SAMPLE, root, ignore=shutil.ignore_patterns("lib", "VERSION", "stamps", "_Archiv"))
    here = project.Project.load(root / "Exemple.woodcore")
    project.sync_engine(here)
    record = here.data_dir / "plans.json"
    data = json.loads(record.read_text(encoding="utf-8"))
    data["plans"]["Pavillon"]["scale"] = {"mode": "ratio", "ratio": 100, "units_per_m": 72 / 0.0254 / 100}
    section = data["plans"]["Fluchttreppe"]
    crop = section["crop"]
    section["role"] = "section"
    section["storey_boxes"] = [{"storey": "EG", "x": crop["x"], "y": crop["y"] + crop["h"] / 2, "w": crop["w"], "h": crop["h"] / 4}]
    record.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return here


def _editor(here, sheet_id="B01", ask=None):
    import sheet_editor
    editor = sheet_editor.SheetEditor(lang="fr", ask=ask or (lambda _q: True))
    editor.preview_folder = conftest.tmpdir("sheet-editor-previews")
    editor.set_project(here)
    editor.open(sheet_id)
    editor.wait()
    return editor


def _pump(app, seconds):
    from PySide6.QtCore import QEventLoop
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 20)
        time.sleep(0.01)


def _outside(text, object_id):
    """The lines of `text` outside object `object_id`'s two tags."""
    import typst_objects as to
    obj = to.find(text, object_id)
    lines = text.splitlines()
    return lines[:obj.start] + lines[obj.end + 1:]


def _mouse(widget, kind, point, buttons):
    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtWidgets import QApplication
    types = {"press": QEvent.Type.MouseButtonPress, "move": QEvent.Type.MouseMove, "release": QEvent.Type.MouseButtonRelease}
    button = Qt.MouseButton.NoButton if kind == "move" else Qt.MouseButton.LeftButton
    pos = QPointF(*point)
    event = QMouseEvent(types[kind], pos, widget.mapToGlobal(pos), button, buttons, Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(widget, event)


def _drag(canvas, start, end):
    from PySide6.QtCore import Qt
    surface = canvas.surface
    _mouse(surface, "press", start, Qt.MouseButton.LeftButton)
    middle = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
    _mouse(surface, "move", middle, Qt.MouseButton.LeftButton)
    _mouse(surface, "move", end, Qt.MouseButton.LeftButton)
    _mouse(surface, "release", end, Qt.MouseButton.NoButton)


# --- opening and compiling ------------------------------------------------------------------------

def test_a_new_sheet_opens_and_compiles_into_the_cache_not_into_plans():
    app = _qt()
    _need_typst()
    import sheets
    here = _project("sheet-editor-open")
    sheets.new_sheet(here)
    editor = _editor(here)
    assert editor.last_result and editor.last_result["ok"], editor.last_result
    assert editor.canvas.has_page()
    w, h = editor.canvas.page_mm
    assert abs(w - 420) < 0.5 and abs(h - 297) < 0.5, editor.canvas.page_mm
    assert not sheets.pdf(here, "B01").exists(), "the preview wrote the deliverable"
    assert [b.id for b in editor.canvas.boxes] == ["title", "remark", "titleblock"]
    assert not any(b.estimated for b in editor.canvas.boxes)
    assert editor.canvas.wait_rendered() is not None, "the page is rendered, off the window's thread since v0.117"
    editor.options.load()
    app.processEvents()


def test_the_box_query_gives_one_box_per_object_in_the_files_order():
    _qt()
    _need_typst()
    import sheets
    import sheet_editor
    here = _project("sheet-editor-boxes")
    sheets.new_sheet(here)
    sheets.add_viewport(here, "B01", "Geratehaus", 20, 30, width=150)
    sheets.add_legend(here, "B01", 250, 30)
    sheets.add_section(here, "B01", "Fluchttreppe", "EG", 330, 120, width=50)
    result = sheet_editor.render(here, "B01", conftest.tmpdir("sheet-editor-render") / "B01.pdf")
    assert result["ok"], result["message"]
    kinds = [b["kind"] for b in result["boxes"]]
    assert kinds == ["sheet-text", "sheet-text", "sheet-viewport", "sheet-legend", "sheet-section", "sheet-titleblock"], kinds
    boxes = sheet_editor.match_boxes(result["text"], result["boxes"])
    assert [b.id for b in boxes] == ["title", "remark", "viewport-geratehaus", "legend", "section", "titleblock"]
    viewport = boxes[2]
    assert (viewport.x, viewport.y) == (20.0, 30.0) and abs(viewport.dw - 150) < 1e-6 and abs(viewport.w - 150) < 1e-6 and viewport.h > 10, viewport
    assert abs(boxes[-1].w - 200) < 1e-6 and abs(boxes[-1].x - (420 - 10 - 200)) < 1e-6


def test_a_call_written_outside_the_tags_does_not_shift_the_boxes():
    """A hand-written `#sheet-text` outside any tag emits a box too: the boxes are matched by kind and place, so it is passed over."""
    _qt()
    import sheet_editor
    text = "\n".join([
        '#import "/000-Typst-Config/commands.typ": *',
        "// woodcore:object sheet-text a", "#sheet-text(", "  x: 10mm,", "  y: 20mm,", ")", "// woodcore:/object a",
        "// woodcore:object sheet-text b", "#sheet-text(", "  x: 50mm,", "  y: 60mm,", ")", "// woodcore:/object b", ""])
    raw = [{"kind": "sheet-text", "x": 1, "y": 2, "w": 3, "h": 4}, {"kind": "sheet-text", "x": 10, "y": 20, "w": 5, "h": 5},
           {"kind": "sheet-text", "x": 50, "y": 60, "w": 7, "h": 7}]
    boxes = sheet_editor.match_boxes(text, raw)
    assert [(b.id, b.x, b.w) for b in boxes] == [("a", 10.0, 5.0), ("b", 50.0, 7.0)]


# --- dragging and resizing --------------------------------------------------------------------------

def test_dragging_a_frame_writes_its_x_and_y_and_nothing_outside_its_tags():
    app = _qt()
    _need_typst()
    import sheets
    import typst_objects as to
    here = _project("sheet-editor-drag")
    sheets.new_sheet(here)
    sheets.add_viewport(here, "B01", "Geratehaus", 20, 30, width=150)
    editor = _editor(here)
    canvas = editor.canvas
    canvas.resize(1200, 900)
    canvas.show()
    _pump(app, 0.2)
    before = sheets.read(here, "B01")
    box = canvas.box("viewport-geratehaus")
    start = canvas.surface.to_px(box.x + box.w / 2, box.y + box.h / 2)
    end = (start[0] + 25 * canvas.ppm, start[1] + 10 * canvas.ppm)
    _drag(canvas, start, end)
    _pump(app, 0.1)
    after = sheets.read(here, "B01")
    model = to.find(after, "viewport-geratehaus").model()
    x, y = model.position()
    assert abs(x - 45) <= 0.5 and abs(y - 40) <= 0.5, (x, y)
    assert x * 2 == round(x * 2) and y * 2 == round(y * 2), "a frame lands on the half millimetre"
    assert _outside(before, "viewport-geratehaus") == _outside(after, "viewport-geratehaus")
    assert to.find(after, "viewport-geratehaus").state == "canonical"
    assert editor.selected == "viewport-geratehaus"
    editor.wait()
    assert abs(canvas.box("viewport-geratehaus").x - x) < 0.01
    canvas.close()


def test_resizing_a_calibrated_plan_rounds_its_scale_and_an_uncalibrated_one_changes_its_width():
    app = _qt()
    _need_typst()
    import sheets
    import typst_objects as to
    here = _project("sheet-editor-resize")
    sheets.new_sheet(here)
    sheets.add_viewport(here, "B01", "Pavillon", 20, 30, scale=100)
    sheets.add_viewport(here, "B01", "Geratehaus", 200, 30, width=100)
    editor = _editor(here)
    canvas = editor.canvas
    canvas.resize(1200, 900)
    canvas.show()
    _pump(app, 0.2)
    box = canvas.box("viewport-pavillon")
    assert box.n == 100 and box.dw > 0
    editor.select("viewport-pavillon")
    rect = canvas.surface.rect_of(box)
    handle = (rect.right(), rect.bottom())
    _drag(canvas, handle, (handle[0] + 0.37 * rect.width(), handle[1]))
    _pump(app, 0.1)
    n = to.find(sheets.read(here, "B01"), "viewport-pavillon").model().get("scale")
    assert isinstance(n, int) and n == round(100 / 1.37), n
    assert to.find(sheets.read(here, "B01"), "viewport-pavillon").model().get("width") is None, "a drawing has one size"
    assert editor.resize_object("viewport-geratehaus", 1.5)
    width = to.mm_of(to.find(sheets.read(here, "B01"), "viewport-geratehaus").model().get("width"))
    assert abs(width - 150) < 0.2, width
    editor.wait()
    assert editor.last_result["ok"], editor.last_result["message"]
    canvas.close()


# --- the options -------------------------------------------------------------------------------------

def test_the_title_block_and_the_legend_are_put_on_and_taken_off():
    app = _qt()
    _need_typst()
    import sheets
    here = _project("sheet-editor-toggles")
    sheets.new_sheet(here)
    editor = _editor(here)
    kinds = lambda: [o.type for o, _m in editor.objects()]
    editor.options.titleblock_check.setChecked(False)
    assert "sheet-titleblock" not in kinds()
    editor.options.titleblock_check.setChecked(True)
    assert kinds().count("sheet-titleblock") == 1
    block = next(m for o, m in editor.objects() if o.type == "sheet-titleblock")
    assert block.get("plan-number") == "B01"
    editor.options.legend_check.setChecked(True)
    assert kinds().count("sheet-legend") == 1
    editor.options.legend_check.setChecked(False)
    assert "sheet-legend" not in kinds()
    editor.set_cell("phase", "51 Projet d'exécution")
    editor.set_cell("client", "")
    block = next(m for o, m in editor.objects() if o.type == "sheet-titleblock")
    assert block.get("phase").markup == "51 Projet d'exécution"
    import typst_objects as to
    assert block.get("client") is to.AUTO
    editor.wait()
    assert editor.last_result["ok"], editor.last_result["message"]
    _pump(app, 0.05)


def test_the_scale_list_stays_open_when_it_takes_the_focus():
    """The engineer, 07.10.2026: «lorsque je sélectionne un plan et clique pour modifier l'échelle, le menu déroulant s'ouvre et se ferme instantanément». The list opening takes the focus from the combo's own field, whose `editingFinished` wrote the scale again unchanged, and the right pane made again under the open list closed it (spec 2026-10-07-performance-erreurs-plans-legendes, REQ-017). An edit that changes nothing now writes and rebuilds nothing; a scale chosen is still written."""
    app = _qt()
    _need_typst()
    import sheets
    import typst_objects as to
    here = _project("sheet-editor-scale-list")
    sheets.new_sheet(here)
    editor = _editor(here)
    new = editor.add_viewport("Pavillon")
    editor.select(new)
    _pump(app, 0.1)
    scale = editor.options.object_widgets["scale"]
    before = sheets.path(here, "B01").stat().st_mtime_ns
    scale.showPopup()
    scale.lineEdit().editingFinished.emit()   # what the focus taken by the list sends
    _pump(app, 0.5)
    assert editor.options.object_widgets["scale"] is scale, "the right pane was made again under the open list"
    assert scale.view().isVisible(), "the list closed by itself"
    assert sheets.path(here, "B01").stat().st_mtime_ns == before, "an unchanged scale was written again"
    scale.hidePopup()
    scale.setCurrentText("1:50")
    scale.lineEdit().editingFinished.emit()
    assert to.find(sheets.read(here, "B01"), new).model().get("scale") == 50
    editor.wait()
    _pump(app, 0.05)


def test_the_options_of_a_text_and_of_a_plan_write_their_object():
    app = _qt()
    _need_typst()
    import sheets
    import typst_objects as to
    here = _project("sheet-editor-options")
    sheets.new_sheet(here)
    editor = _editor(here)
    new = editor.add_viewport("Pavillon")
    assert new == "viewport-pavillon" and editor.selected == "", "an object added is not chosen: its options show once it is clicked (v0.116)"
    model = to.find(sheets.read(here, "B01"), new).model()
    assert model.get("scale") == 100, "a calibrated plan is put on at 1:100"
    editor.set_scale(new, 50)
    editor.set_highlight(new, "T001")
    assert to.find(sheets.read(here, "B01"), new).model().get("scale") == 50
    text = editor.add_text()
    editor.set_body(text, "Hallo *Welt*")
    editor.set_bold(text, True)
    model = to.find(sheets.read(here, "B01"), text).model()
    assert model.get("body").markup == "Hallo *Welt*" and model.get("weight") == "bold"
    _pump(app, 0.05)
    editor.select(text)
    _pump(app, 0.05)
    assert editor.options.object_widgets["body"].toPlainText() == "Hallo *Welt*"
    editor.set_page(format="A4", landscape=False)
    page = editor.page_model()
    assert page.size() == (210, 297) and editor.canvas.page_mm == (210.0, 297.0)
    assert editor.remove_selected()
    assert text not in [o.id for o, _m in editor.objects()]
    editor.wait()


def test_an_object_written_by_hand_is_rewritten_only_once_asked():
    _qt()
    _need_typst()
    import sheets
    here = _project("sheet-editor-hand")
    sheets.new_sheet(here)
    text = sheets.read(here, "B01")
    # a comment of the engineer's in the object's #place (spec 2026-10-21-commandes-typst-refonte, Q-015): no part of Woodcore's form
    assert "#place(top + left, dx: 20mm, dy: 17mm," in text, text
    hand = text.replace("#place(top + left, dx: 20mm, dy: 17mm,", "#place(top + left, dx: 20mm, dy: 17mm,  // by hand")
    sheets.write(here, "B01", hand)
    asked = []
    editor = _editor(here, ask=lambda q: asked.append(q) or False)
    assert not editor.move("title", 30, 30)
    assert asked and "title" in asked[0] and sheets.read(here, "B01") == hand
    editor.ask = lambda q: True
    assert editor.move("title", 30, 30)
    assert "dx: 30mm, dy: 30mm" in sheets.read(here, "B01")


# --- the file watched ----------------------------------------------------------------------------------

def test_an_edit_made_elsewhere_is_read_back_and_the_editors_own_is_not():
    app = _qt()
    _need_typst()
    import sheets
    here = _project("sheet-editor-watch")
    sheets.new_sheet(here)
    editor = _editor(here)
    editor.start()
    seen = []
    editor.changed.connect(seen.append)
    assert editor.move("title", 25, 18)
    _pump(app, 0.6)
    assert not editor.reload_external(), "the editor's own write was taken for an edit made elsewhere"
    seen.clear()
    path = sheets.path(here, "B01")
    path.write_bytes(path.read_bytes().replace(b"x: 25mm", b"x: 60mm"))
    end = time.monotonic() + 10
    while not seen and time.monotonic() < end:
        _pump(app, 0.1)
    assert seen == ["B01"], "the watcher did not read the file back"
    editor.wait()
    assert abs(editor.canvas.box("title").x - 60) < 0.01
    editor.stop()
    assert not editor.watcher.files() and not editor.watcher.directories()


def test_export_writes_plans_pdf_beside_the_typ():
    _qt()
    _need_typst()
    import sheets
    here = _project("sheet-editor-export")
    sheets.new_sheet(here)
    editor = _editor(here)
    ok, message = editor.export_pdf()
    assert ok, message
    pdf = sheets.pdf(here, "B01")
    assert pdf.is_file() and pdf.read_bytes().startswith(b"%PDF")
    editor.exportRequested.emit()
    assert "B01.pdf" in editor.canvas.banner.text()


def test_a_sheet_that_does_not_compile_says_so_and_keeps_its_page():
    app = _qt()
    _need_typst()
    import sheets
    here = _project("sheet-editor-broken")
    sheets.new_sheet(here)
    editor = _editor(here)
    generation = editor.canvas.generation
    path = sheets.path(here, "B01")
    path.write_text(path.read_text(encoding="utf-8") + "\n#sheet-text(x: \"nowhere\")\n", encoding="utf-8")
    assert editor.reload_external()
    editor.wait()
    assert not editor.last_result["ok"]
    assert editor.canvas.banner.isVisibleTo(editor.canvas) and "sheet-text" in editor.canvas.banner.text()
    assert editor.canvas.has_page() and editor.canvas.generation == generation
    _pump(app, 0.05)


def test_a_fire_plan_and_its_legend_are_put_on_the_sheet_framed_resized_and_edited_like_any_plan():
    """The fire-protection plan on a sheet (v0.115): `+ Plan incendie` puts the first fire plan of the export on at 1:100 where it is calibrated, its box is read back with the width and the scale it is printed at, a corner dragged rounds its scale as a position plan's does -- from the fire plan's own calibration --, the card of the object offers the legend and the scale bar and no axes, and the fire legend is put on and taken off beside the position plans' own."""
    app = _qt()
    _need_typst()
    import sheets
    import sheet_editor
    import typst_objects as to
    here = _project("sheet-editor-fire")
    sheets.new_sheet(here, kind="fire")
    editor = _editor(here)
    kinds = lambda: [o.type for o, _m in editor.objects()]
    new = editor.add_fire_viewport("Treppenhaus")
    assert new == "fire-treppenhaus" and editor.selected == ""
    editor.select(new)
    model = to.find(sheets.read(here, "B01"), new).model()
    assert model.get("plan") == "Treppenhaus" and model.get("scale") == 100, "a calibrated fire plan is put on at 1:100"
    editor.wait()
    assert editor.last_result["ok"], editor.last_result["message"]
    box = editor.canvas.box(new)
    assert box.kind == "sheet-fire-viewport" and box.resizable and box.n == 100 and abs(box.dw - 320) < 1e-6, box
    # the card of the object: the plan among the fire plans, the legend and the scale bar, and no axes
    _pump(app, 0.05)
    widgets = editor.options.object_widgets
    assert {"plan", "scale", "width", "legend", "scale_bar"} <= set(widgets) and "axes" not in widgets and "highlight" not in widgets
    plans = [widgets["plan"].itemData(i) for i in range(widgets["plan"].count())]
    assert plans == [None, "Pavillon-EG", "Treppenhaus"], plans
    widgets["legend"].setChecked(False)
    assert to.find(sheets.read(here, "B01"), new).model().get("legend") is False
    # resized: the fire plan's own calibration gives the scale
    assert editor.resize_object(new, 2)
    assert to.find(sheets.read(here, "B01"), new).model().get("scale") == 50
    assert editor.set_scale(new, 200) is not False
    assert to.find(sheets.read(here, "B01"), new).model().get("scale") == 200
    # the legend of the fire plans, a block of its own, put on and taken off
    editor.options.fire_legend_check.setChecked(True)
    assert kinds().count("sheet-fire-legend") == 1 and kinds().count("sheet-legend") == 0
    editor.wait()
    assert editor.last_result["ok"], editor.last_result["message"]
    assert [b["kind"] for b in editor.last_result["boxes"]].count("sheet-fire-legend") == 1
    assert editor.canvas.box("fire-legend") is not None
    editor.options.fire_legend_check.setChecked(False)
    assert "sheet-fire-legend" not in kinds()
    # a plan that follows an uncalibrated one is put on at a width, and the editor says it has no scale
    other = editor.add_fire_viewport("Pavillon-EG")
    model = to.find(sheets.read(here, "B01"), other).model()
    assert model.get("scale") is None and to.mm_of(model.get("width")) == 150.0
    _pump(app, 0.05)


def test_the_boxes_of_the_fire_objects_are_estimated_too_and_their_words_are_in_three_languages():
    _qt()
    import sheets
    import sheet_editor
    here = _project("sheet-editor-fire-estimate")
    sheets.new_sheet(here, kind="fire")
    sheets.add_fire_viewport(here, "B01", "Treppenhaus", 20, 30, scale=100)
    sheets.add_fire_legend(here, "B01", 250, 30, width=90)
    boxes = {b.id: b for b in sheet_editor.estimate_boxes(here, sheets.read(here, "B01"))}
    viewport, legend = boxes["fire-treppenhaus"], boxes["fire-legend"]
    assert viewport.resizable and abs(viewport.dw - 320) < 1e-6 and abs(viewport.n - 100) < 1e-6 and viewport.estimated
    assert (legend.x, legend.w) == (250.0, 90.0) and legend.resizable   # its width by its handle since v0.117 (REQ-018)
    assert sheet_editor.read_fire_plans(here)["Treppenhaus"]["scale"]["units_per_m"] == 20
    for lang in ("fr", "de", "en"):
        for key in ("se_kind_fire-viewport", "se_kind_fire-legend", "se_add_fire_view", "se_legend_show"):
            assert key in sheet_editor.STRINGS[lang], (lang, key)


# --- Qt-free parts -----------------------------------------------------------------------------------

def test_the_boxes_are_estimated_where_typst_cannot_be_asked():
    _qt()
    import sheets
    import sheet_editor
    here = _project("sheet-editor-estimate")
    sheets.new_sheet(here)
    sheets.add_viewport(here, "B01", "Pavillon", 20, 30, scale=100)
    assert sheet_editor.parse_boxes("not json") is None and sheet_editor.parse_boxes('[{"kind": 1}]') is None
    boxes = sheet_editor.estimate_boxes(here, sheets.read(here, "B01"))
    assert [b.id for b in boxes] == ["title", "remark", "viewport-pavillon", "titleblock"]
    viewport = boxes[2]
    plan = sheet_editor.read_plans(here)["Pavillon"]
    assert abs(viewport.dw - plan["crop"]["w"] / plan["scale"]["units_per_m"] * 10) < 1e-6
    assert abs(sheet_editor.scale_for(plan, viewport.dw) - 100) < 1e-6
    assert sheet_editor.parse_scale("1:200") == 200 and sheet_editor.parse_scale(" 50 ") == 50 and sheet_editor.parse_scale("1:0") is None


def test_the_words_are_the_same_keys_in_three_languages():
    _qt()
    import sheet_editor
    keys = set(sheet_editor.STRINGS["fr"])
    for lang in ("de", "en"):
        assert set(sheet_editor.STRINGS[lang]) == keys, lang
    assert all(k.startswith("se_") for k in keys)
    assert not any("ß" in v for v in sheet_editor.STRINGS["de"].values())
    import re
    for value in sheet_editor.STRINGS["fr"].values():
        assert not re.search(r"[^\s\d]:(\s|$)", value.replace("#show:", "")), f"French puts a space before a colon: {value!r}"
    for code, key in sheet_editor.WHY.items():
        assert key in keys, code


def test_the_canvas_fits_the_sheet_and_zooms_under_ctrl_and_the_wheel():
    app = _qt()
    import sheet_editor
    from PySide6.QtCore import QPoint, QPointF, Qt
    from PySide6.QtGui import QWheelEvent
    from PySide6.QtWidgets import QApplication
    canvas = sheet_editor.SheetCanvas(lang="de")
    canvas.resize(800, 600)
    canvas.show()
    _pump(app, 0.1)
    fitted = canvas.ppm
    assert canvas.fitting and canvas.surface.width() <= canvas.scroll.viewport().width() + 1
    point = QPointF(200, 150)
    wheel = QWheelEvent(point, canvas.surface.mapToGlobal(point), QPoint(), QPoint(0, 120), Qt.MouseButton.NoButton,
                        Qt.KeyboardModifier.ControlModifier, Qt.ScrollPhase.NoScrollPhase, False)
    QApplication.sendEvent(canvas.surface, wheel)
    assert abs(canvas.ppm - fitted * sheet_editor.ZOOM_STEP) < 1e-9 and not canvas.fitting
    canvas.zoom_out()
    canvas.fit()
    assert abs(canvas.ppm - fitted) < 1e-9
    canvas.close()


# --- the right pane follows what is chosen (v0.116) --------------------------------------------------

def _shown(card):
    return not card.isHidden()


def test_nothing_chosen_shows_the_sheet_and_its_options_and_an_object_chosen_its_own_module_alone():
    """The engineer, 06.10.2026: nothing chosen on the sheet, the modules «Feuille» and «Options» -- the title block and the legend as two switches, then what may be added, one under another --; an object clicked, its own module and nothing else: «Titre» for the sheet's title, «Vue en plan» for a plan, the title block's cells for the title block. An object added shows no options until it is chosen, and the combo that chose an object by its kind is gone."""
    app = _qt()
    _need_typst()
    import sheets
    here = _project("sheet-editor-pane")
    sheets.new_sheet(here)
    editor = _editor(here)
    o = editor.options
    assert not hasattr(o, "object_combo"), "objects are chosen on the sheet, not in a list of kinds"
    assert _shown(o.page_card) and _shown(o.options_card) and not _shown(o.object_card)
    assert o.options_card.title() == "Options" and o.titleblock_check.text() == "Afficher le cartouche" and o.legend_check.text() == "Afficher la légende"
    shown = [key for key, button in o.add_buttons.items() if not button.isHidden()]
    assert shown == ["se_add_plan_view", "se_add_section_view", "se_add_text_object", "se_add_position_list", "se_add_quantities"], shown   # the quantities since issue #9
    # the plan to add is chosen in a list of the position plans, sections left out
    asked = []
    editor.choose = lambda question, items: (asked.append((question, items)), "Pavillon")[1]
    new = editor.add_viewport_chosen()
    assert new == "viewport-pavillon" and editor.selected == "" and not _shown(o.object_card)
    question, items = asked[-1]
    assert question == "Quelle vue en plan ajouter ?" and [value for _label, value in items] == ["Geratehaus", "Pavillon", "Velo-Unterstand"], items
    editor.choose = lambda question, items: (asked.append((question, items)), None)[1]
    assert editor.add_section_chosen() is None and [value for _l, value in asked[-1][1]] == ["Fluchttreppe"], "nothing chosen, nothing added"
    # the title: the module «Titre» alone
    editor.select("title")
    _pump(app, 0.05)
    assert not _shown(o.page_card) and not _shown(o.options_card) and _shown(o.object_card)
    assert o.object_card.title() == "Titre" and "body" in o.object_widgets
    # a plan: «Vue en plan», the position highlighted chosen among those the plan shows
    editor.select(new)
    _pump(app, 0.05)
    assert o.object_card.title() == "Vue en plan"
    highlight = o.object_widgets["highlight"]
    assert [highlight.itemData(i) for i in range(highlight.count())] == [None, "S001", "T001", "S002"]
    highlight.setCurrentIndex(2)
    highlight.activated.emit(2)
    assert sheets.model(here, "B01", new).get("highlight") == "T001"
    title = o.object_widgets["title"]
    assert title.isChecked()
    title.setChecked(False)
    assert sheets.model(here, "B01", new).get("title") is None
    # the title block: its cells alone
    editor.select("titleblock")
    _pump(app, 0.05)
    assert o.object_card.title() == "Cartouche" and set(o.cell_widgets) >= {"object", "client", "phase"} and "remove" not in o.object_widgets
    editor.select("")
    _pump(app, 0.05)
    assert _shown(o.page_card) and not _shown(o.object_card)
    editor.wait()
    assert editor.last_result["ok"], editor.last_result["message"]


def test_the_position_list_is_added_from_the_options_and_its_module_says_which_positions():
    app = _qt()
    _need_typst()
    import sheets
    here = _project("sheet-editor-list")
    sheets.new_sheet(here)
    editor = _editor(here)
    new = editor.add_position_list()
    assert new == "positions" and editor.selected == ""
    editor.wait()
    assert editor.last_result["ok"], editor.last_result["message"]
    box = editor.canvas.box(new)
    assert box is not None and box.kind == "sheet-position-list" and box.resizable   # its width by its handle since v0.117 (REQ-018)
    editor.select(new)
    _pump(app, 0.05)
    o = editor.options
    assert o.object_card.title() == "Liste des positions"
    # the list is the project's file, included (spec 2026-10-21-commandes-typst-refonte, Q-015): no scope to choose on the sheet, its file written once where it was missing
    assert "scope" not in o.object_widgets and "storey" not in o.object_widgets
    from domains import list_files
    assert list_files.path(here, "position-list").is_file()
    assert '#include "/Positions/position-list.typ"' in sheets.read(here, "B01")
    estimated = {b.id: b for b in __import__("sheet_editor").estimate_boxes(here, sheets.read(here, "B01"))}
    assert estimated[new].h > 20 and estimated[new].estimated
    editor.wait()


def test_a_fire_sheet_offers_the_fire_objects_alone_and_its_legend_switch_is_the_fire_plans():
    app = _qt()
    _need_typst()
    import sheets
    here = _project("sheet-editor-fire-kind")
    sheets.new_sheet(here, kind="fire")
    editor = _editor(here)
    o = editor.options
    shown = [key for key, button in o.add_buttons.items() if not button.isHidden()]
    assert shown == ["se_add_fire_view", "se_add_text_object"], shown
    editor.choose = lambda question, items: items[-1][1]
    assert editor.add_fire_viewport_chosen() == "fire-treppenhaus"
    o.legend_check.setChecked(True)
    assert [ob.type for ob, _m in editor.objects()].count("sheet-fire-legend") == 1
    assert not any(ob.type == "sheet-legend" for ob, _m in editor.objects())
    # a position plan's object is refused on it, said in the banner
    assert editor.add_viewport("Pavillon") is None
    assert "plans de position et plans de protection incendie" in editor.canvas.banner.text()
    editor.wait()
    _pump(app, 0.05)


def test_the_bundles_words_are_the_editors_in_three_languages():
    _qt()
    import sheet_editor
    for lang in ("fr", "de", "en"):
        found = sheet_editor.bundle_words(lang)
        assert set(found) == set(sheet_editor.BUNDLE_KEYS) and all(found.values())
    assert sheet_editor.bundle_words("fr")["se_bundle"] == "Création d'un PDF"


def test_a_zoom_never_renders_the_page_on_the_window_s_thread_and_a_deep_one_renders_the_part_in_view():
    """The engineer, 07.10.2026: «l'affichage des pdf + svg (affichage Dessin ou Export) est également pas très fluide». Until v0.117 each zoom rendered the whole page in the paint -- an A3 at the deepest zoom, 10 500 x 7 400 pixels, on the window's thread. Now a paint renders nothing: the image before is drawn stretched, a render is asked of QtPdf's own thread once the zoom stands still, and past RENDER_MAX_PX only the part in view is rendered (spec 2026-10-07-performance-erreurs-plans-legendes, REQ-015)."""
    app = _qt()
    _need_typst()
    import sheets
    import sheet_editor
    here = _project("sheet-editor-async")
    sheets.new_sheet(here)
    editor = _editor(here)
    canvas = editor.canvas
    canvas.resize(900, 700)
    canvas.show()
    first = canvas.wait_rendered()
    assert first is not None
    calls = []
    original = canvas.document.render
    canvas.document.render = lambda *a, **k: calls.append(a) or original(*a, **k)
    for _ in range(12):
        canvas.zoom_in()
        canvas.surface.repaint()   # a paint at once, as the wheel does: it must not render
    assert not calls, "a paint rendered the page on the window's thread"
    assert canvas.page_image() is first, "the image before is shown, stretched, until the new one is back"
    deep = canvas.wait_rendered()
    w, h = canvas.page_mm
    full = w * canvas.ppm * canvas.devicePixelRatioF() * h * canvas.ppm * canvas.devicePixelRatioF()
    assert full > sheet_editor.RENDER_MAX_PX, "the zoom is not deep enough for the test to say anything"
    assert deep is not first and deep.width() * deep.height() <= full / 2, "the part in view, not the whole page"
    assert canvas.page_render()[1].width() < 1, "the render covers part of the page"
    canvas.close()


def test_a_list_of_the_positions_and_a_legend_are_widened_by_their_handle():
    """The engineer, 07.10.2026: «dans l'affichage "Export", il faut pouvoir redimensionner les liste de positions à l'aide de la souris» (REQ-018): its handle sets its width, its height following its lines; until v0.117 only a plan or a section had one."""
    app = _qt()
    _need_typst()
    import sheets
    import sheet_editor
    import typst_objects as to
    here = _project("sheet-editor-list-handle")
    sheets.new_sheet(here)
    editor = _editor(here)
    editor.add_viewport("Pavillon")
    editor.wait()
    listed = editor.add_position_list()
    editor.wait()
    _pump(app, 0.1)
    box = editor.canvas.box(listed)
    assert box is not None and box.resizable, "the list has its handle"
    before = to.mm_of(to.find(sheets.read(here, "B01"), listed).model().get("width")) or box.w
    assert editor.resize_object(listed, 1.5)
    after = to.mm_of(to.find(sheets.read(here, "B01"), listed).model().get("width"))
    assert abs(after - round(before * 1.5, 1)) < 0.11, (before, after)
    assert "sheet-legend" in sheet_editor.RESIZABLE_KINDS and "sheet-fire-legend" in sheet_editor.RESIZABLE_KINDS
    editor.wait()
    _pump(app, 0.05)
