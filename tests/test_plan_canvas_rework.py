"""The position plan's drawing surface as v0.114 reworked it (calc/tools/plan_canvas.py, docs/domain/position-plans.md §3.3sexies, docs/ui/window.md §10quater): a plan shown as its crop alone, the whole page under a veil only on request or while the crop is drawn; a section's storey lines and boxes, drawn, selected, moved and deleted; and a background read from an imported document (calc/domains/plan_documents.py) -- the document's own layers switched off and its page turned, which the canvas renders and lays the scene out on again.

Every check builds a PlanCanvas of its own, off-screen, with a source dictionary of its own: nothing here needs a window or the example project.
"""

TIER = "fast"  # tests/run_tests.py --fast

import os
import sys

import conftest
from conftest import ROOT
from domains import plan
from domains import plan_svg
from domains import plan_documents as documents
from fixtures import layered_pdf as fx

TOOLS = ROOT / "calc" / "tools"


def _qt():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _canvas(source, root, here=None):
    _qt()
    import plan_canvas
    canvas = plan_canvas.PlanCanvas()
    canvas.resize(900, 600)
    canvas.show()
    canvas.set_source(source, root, here=here)
    return canvas


def _source(**extra):
    source = plan.new_source("P01")
    source["sheet"] = {"width": 1000, "height": 500}
    source.update(extra)
    return source


def _png(root, width=200, height=100):
    from PySide6.QtGui import QColor, QImage
    image = QImage(width, height, QImage.Format.Format_RGB32)
    image.fill(QColor("#3070c0"))
    path = root / "plan.png"
    image.save(str(path))
    return path


def _click(canvas, point, shift=False):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtCore import QPointF
    at = canvas.mapFromScene(QPointF(*point))
    QTest.mouseMove(canvas.viewport(), at)
    QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ShiftModifier if shift else Qt.KeyboardModifier.NoModifier, at)


def _drag(canvas, start, end):
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtTest import QTest
    a, b = canvas.mapFromScene(QPointF(*start)), canvas.mapFromScene(QPointF(*end))
    QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, a)
    # QTest.mouseMove sends no buttons held: the move is sent as Qt sends one while the button is down
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtCore import QEvent
    for t in (0.5, 1.0):
        p = QPointF(a.x() + (b.x() - a.x()) * t, a.y() + (b.y() - a.y()) * t)
        event = QMouseEvent(QEvent.Type.MouseMove, p, canvas.viewport().mapToGlobal(p), Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        canvas.mouseMoveEvent(event)
    QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, b)


def test_a_plan_shows_its_crop_alone_and_the_whole_page_only_on_request():
    """The engineer, 06.10.2026: «on ne verra plus que le cadrage et pas les éléments autour». The drawing is clipped to the crop, no veil is drawn, and the view is no larger than the crop and its margin; set_show_outside(True) gives back the page under its veil, and the crop tool shows the whole page while it is used."""
    from PySide6.QtWidgets import QGraphicsItem
    root = conftest.tmpdir("canvas_crop")
    png = _png(root)
    source = _source(crop={"x": 100, "y": 100, "w": 300, "h": 200}, background={"file": png.name, "page": 1})
    canvas = _canvas(source, root)
    clips = QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape
    crop = canvas.crop_rect()
    assert canvas.clipped()
    assert not any(item.isVisible() for item in canvas.dims), "no veil where only the crop is shown"
    assert canvas.clip.flags() & clips and canvas.clip.rect() == crop
    margin = 0.04 * 300 + 1e-6
    assert crop.adjusted(-margin, -margin, margin, margin).contains(canvas.sceneRect()), canvas.sceneRect()
    assert canvas.background is not None and canvas.background.parentItem() is canvas.clip, "the background is clipped with the rest"
    assert canvas.overlay.parentItem() is canvas.clip and canvas.sheet_item.parentItem() is canvas.clip
    assert canvas.shown_rect() == crop

    canvas.set_show_outside(True)
    assert not canvas.clipped() and not (canvas.clip.flags() & clips)
    assert all(item.isVisible() for item in canvas.dims), "the whole page under its veil"
    assert canvas.sceneRect().contains(canvas.sheet_rect())
    canvas.set_show_outside(False)
    assert canvas.clipped() and canvas.clip.flags() & clips

    canvas.set_tool("crop")
    assert not canvas.clipped(), "a crop is drawn on the page around it"
    assert canvas.sceneRect().contains(canvas.sheet_rect())
    _drag(canvas, (50, 50), (500, 400))
    want = {"x": 50, "y": 50, "w": 450, "h": 350}
    assert all(abs(source["crop"][k] - v) < 3 for k, v in want.items()), source["crop"]  # within the pixel a click lands on
    canvas.set_tool("select")
    assert canvas.clipped() and canvas.clip.rect() == canvas.crop_rect(), "leaving the crop tool shows the crop just drawn"
    canvas.close()


def test_nothing_outside_the_crop_is_taken():
    """An element outside the crop is not shown, so a click there takes nothing -- until the whole page is shown."""
    root = conftest.tmpdir("canvas_outside")
    source = _source(crop={"x": 100, "y": 100, "w": 300, "h": 200}, elements=[{"type": "S", "label": "S001", "points": [[700, 300]]}])
    canvas = _canvas(source, root)
    canvas.set_tool("select")
    canvas.press_select((700, 300))
    assert canvas.selection is None
    canvas.set_show_outside(True)
    canvas.press_select((700, 300))
    assert canvas.selection == ("element", 0)
    canvas.close()


def test_a_storey_line_drawn_with_shift_is_level_and_lands_in_the_source():
    root = conftest.tmpdir("canvas_storey_line")
    source = _source(role="section")
    canvas = _canvas(source, root)
    drawn, changes, missing = [], [], []
    canvas.storeyLineDrawn.connect(drawn.append)
    canvas.storeyMissing.connect(missing.append)
    canvas.about_to_change.connect(lambda: changes.append("before"))
    canvas.changed.connect(lambda: changes.append("after"))
    canvas.set_tool("storey-line")
    _click(canvas, (100, 100))
    _click(canvas, (400, 180))
    assert missing and set(missing) == {"storey-line"} and not source.get("storey_lines"), "no storey chosen: nothing drawn, and said"
    canvas.drawing = []
    missing.clear()

    canvas.set_storey_choice("EG")
    _click(canvas, (100, 100))
    _click(canvas, (400, 180), shift=True)
    lines = source["storey_lines"]
    assert len(lines) == 1 and lines[0]["storey"] == "EG"
    (x0, y0), (x1, y1) = lines[0]["points"]
    assert y0 == y1, "Shift keeps a storey line level"
    assert abs(x0 - 100) < 2 and abs(y0 - 100) < 2 and abs(x1 - 400) < 2
    assert drawn == [lines[0]["points"]] and changes == ["before", "after"] and not missing
    assert canvas.selection == ("storey-line", 0)
    plan.check_source(source, "P01.json")
    canvas.close()


def test_a_storey_box_lands_in_the_source_and_is_drawn():
    root = conftest.tmpdir("canvas_storey_box")
    source = _source(role="section")
    canvas = _canvas(source, root)
    boxes = []
    canvas.storeyBoxDrawn.connect(boxes.append)
    canvas.set_storey_choice("1.OG")
    canvas.set_tool("storey-box")
    _click(canvas, (500, 300))
    _click(canvas, (200, 150))
    assert len(source["storey_boxes"]) == 1
    box = source["storey_boxes"][0]
    assert box["storey"] == "1.OG"
    assert abs(box["x"] - 200) < 2 and abs(box["y"] - 150) < 2 and abs(box["w"] - 300) < 3 and abs(box["h"] - 150) < 3
    assert boxes == [box] and box["floor"] == "1", "the box keeps its storey's numbering character (v0.116)"
    # v0.116: the canvas draws the box alone, no storey in its corner; its STE designation x1xx stands at its middle, in the overlay
    assert len(canvas.storey_items) == 1 and not any(hasattr(item, "text") for item in canvas.storey_items)
    svg = plan_svg.render(source)
    assert ">x1xx</text>" in svg.split(plan_svg.BOXES_OPEN)[1].split(plan_svg.BOXES_CLOSE)[0]
    plan.check_source(source, "P01.json")
    canvas.close()


def test_a_storey_line_is_selected_moved_and_deleted():
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    root = conftest.tmpdir("canvas_storey_select")
    source = _source(role="section", storey_lines=[{"storey": "EG", "points": [[100, 200], [600, 200]]}],
                     storey_boxes=[{"storey": "EG", "x": 100, "y": 220, "w": 500, "h": 100}])
    canvas = _canvas(source, root)
    canvas.set_tool("select")
    _click(canvas, (350, 200))
    assert canvas.selection == ("storey-line", 0) and canvas.selected_storey_line() is source["storey_lines"][0]
    assert len(canvas.handles) == 2, "a handle on each end"
    _drag(canvas, (600, 200), (650, 200))
    assert abs(source["storey_lines"][0]["points"][1][0] - 650) < 2, "an end dragged by its handle"
    _click(canvas, (350, 270))
    assert canvas.selection == ("storey-box", 0) and len(canvas.handles) == 4
    _click(canvas, (350, 200))
    QTest.keyClick(canvas, Qt.Key.Key_Delete)
    assert source["storey_lines"] == [] and canvas.selection is None
    assert len(source["storey_boxes"]) == 1, "only what was selected is deleted"
    canvas.close()


def test_the_background_is_the_documents_render_and_follows_its_page_turned():
    """A plan drawn on an imported document is rendered from plan_documents.render_source -- here the file hides «Dims» by default and the document shows it, so the window renders a copy, and the red square of «Dims» is seen; turning the page renders the turned copy and lays the scene out on the turned sheet."""
    from PySide6.QtCore import QCoreApplication
    from PySide6.QtTest import QTest
    root = conftest.tmpdir("canvas_document")
    (root / "01_Pläne").mkdir()
    (root / "Woodcore-Datei" / "plans").mkdir(parents=True)
    kept = documents.CACHE_ROOT
    documents.CACHE_ROOT = root / "_cache"
    try:
        place = documents.Place(root, root / "Woodcore-Datei" / "plans")
        path = fx.write(root / "01_Pläne" / "Plan.pdf")
        doc = documents.import_file(place, path)
        documents.set_layer(doc, "Dims", True)
        documents.write(place, doc)
        width, height = documents.page_size(place, doc, 1)
        source = plan.new_source("P01")
        source["sheet"] = {"width": width, "height": height}
        source["background"] = {"file": doc["file"], "page": 1, "document": doc["id"]}
        canvas = _canvas(source, root, here=place)
        assert canvas.background_problem is None
        rendered = documents.render_source(place, doc)
        assert rendered != path
        assert canvas.pdf_file[0] == str(rendered.resolve()), "the window renders the document's copy, not the file"
        for _ in range(100):
            if canvas.background is not None:
                break
            QTest.qWait(50)
        assert canvas.background is not None, "the page was rendered"
        image = canvas.background.pixmap().toImage()
        scale = image.width() / width
        (px, py), red = fx.COLOURS["red"]
        colour = image.pixelColor(round(px * scale), round((height - py) * scale))
        assert (colour.red(), colour.green(), colour.blue()) == red, "the layer the document switched on is drawn"

        old = (width, height)
        documents.set_rotation(doc, 1, 90)
        documents.write(place, doc)
        canvas.source = plan.rotate_source(source, 1, old)
        canvas.reload_background()
        assert (canvas.sheet_rect().width(), canvas.sheet_rect().height()) == (height, width)
        assert canvas.pdf_file[0] == str(documents.render_source(place, doc).resolve()) != str(rendered.resolve())
        assert canvas.crop_rect() == canvas.sheet_rect() and canvas.sceneRect().contains(canvas.sheet_rect())
        canvas.close()
        QCoreApplication.processEvents()
    finally:
        documents.CACHE_ROOT = kept


def test_a_document_that_cannot_be_read_falls_back_on_the_file_and_says_why():
    root = conftest.tmpdir("canvas_document_gone")
    png = _png(root)
    source = _source(background={"file": png.name, "page": 1, "document": "D09"})
    canvas = _canvas(source, root, here=documents.Place(root, root / "Woodcore-Datei" / "plans"))
    assert canvas.background_problem is not None
    assert canvas.background is not None, "drawn on its file all the same"
    canvas.close()


def test_the_frame_is_read_through_frame_source_which_a_subclass_may_override():
    """A drawing that follows another's frame (a fire plan following a position plan) overrides `frame_source`: the canvas reads the sheet, the crop and the background from what it answers, and the elements it draws from its own source."""
    root = conftest.tmpdir("canvas_frame")
    png = _png(root)
    own = _source(sheet={"width": 100, "height": 100})
    followed = _source(crop={"x": 100, "y": 100, "w": 300, "h": 200}, background={"file": png.name, "page": 1})
    canvas = _canvas(own, root)
    assert canvas.frame_source() is canvas.source and canvas.background is None
    _qt()
    import plan_canvas

    class Following(plan_canvas.PlanCanvas):
        def frame_source(self):
            return followed

    canvas = Following()
    canvas.resize(900, 600)
    canvas.show()
    canvas.set_source(own, root)
    assert canvas.source is own and canvas.frame_source() is followed
    assert canvas.sheet_rect().width() == 1000 and canvas.sheet_rect().height() == 500, "the sheet is the followed frame's"
    crop = canvas.crop_rect()
    assert (crop.x(), crop.y(), crop.width(), crop.height()) == (100, 100, 300, 200)
    assert canvas.background is not None and canvas.background_file() is not None, "the background is the followed frame's"
