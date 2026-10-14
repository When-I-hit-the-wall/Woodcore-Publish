"""The view of one imported document in the position plan tab (v0.114, calc/tools/document_view.py, docs/domain/position-plans.md §3.3sexies, docs/ui/window.md §10quater): every page of a PDF or every layout of a CAD drawing in one view that scrolls, zoomed with Ctrl + the wheel, each page ticked into the plans, turned, cropped and calibrated, its layers switched with the preview following at once.

Built off-screen on documents written in the test: tests/fixtures/layered_pdf.py's PDF of three optional-content groups, three pages alike, and a DXF written with ezdxf -- so nothing here needs an architect's plan. The renders are QtPdf's and QtSvg's own, so what is held of a layer switched is what is **seen**: the colour of the square the layer draws. plan_documents' caches are pointed into the test's own folder and put back afterwards.

What the view says is held exactly where it matters: a crop and a calibration come back in the page's own sheet units, and the point clicked is mapped back to the same point of the sheet whatever the zoom.
"""

import functools
import os
import re
import sys
import time

import conftest
from conftest import ROOT, Skip
from fixtures import layered_pdf as fx

TOOLS = ROOT / "calc" / "tools"


def _qt():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
        import PySide6.QtPdf  # noqa: F401
    except ImportError as exc:
        raise Skip(f"PySide6 or its QtPdf is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _wait(app, condition, timeout=60, what="the view"):
    from PySide6.QtCore import QEventLoop
    end = time.monotonic() + timeout
    while not condition():
        if time.monotonic() > end:
            raise AssertionError(f"{what}: nothing after {timeout} s")
        app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 50)
        time.sleep(0.01)


def _own_caches(test):
    """Points plan_documents' caches into the test's own folder for the test, and puts the module's own back afterwards -- a test must never write the engineer's %LOCALAPPDATA%, and must not leave the next one writing into a folder it removed."""
    @functools.wraps(test)
    def run():
        from domains import plan_documents
        kept = plan_documents.CACHE_ROOT
        try:
            test()
        finally:
            plan_documents.CACHE_ROOT = kept
    return run


def _project(name):
    from domains import plan_documents
    root = conftest.tmpdir(f"dview_{name}")
    (root / "01_Pläne").mkdir()
    (root / "Woodcore-Datei" / "plans").mkdir(parents=True)
    plan_documents.CACHE_ROOT = root / "_cache"
    return plan_documents.Place(root, root / "Woodcore-Datei" / "plans")


def _pdf_doc(place, pages=3):
    from domains import plan_documents
    path = fx.write(place.root / "01_Pläne" / "Plan.pdf", pages=pages)
    return plan_documents.import_file(place, path)


def _view(app, place, doc, width=900, height=640):
    import document_view
    view = document_view.DocumentView(lang="fr")
    view.resize(width, height)
    view.show()
    app.processEvents()
    view.set_document(place, doc)
    _idle(app, view)
    return view


def _idle(app, view):
    _wait(app, lambda: not view.is_busy() and bool(view.area.pages), what="the document's pages")


def _record(signal):
    seen = []
    signal.connect(lambda *args: seen.append(args))
    return seen


def _sheet_colour(view, page, x, y):
    """The colour the coarse render of `page` shows at the sheet point (x, y): what the window shows there."""
    shown = view.area.base[page]
    info = view.area.info(page)
    px = round(x * shown.image.width() / info.width)
    py = round(y * shown.image.height() / info.height)
    c = shown.image.pixelColor(px, py)
    a = c.alphaF()   # QtPdf leaves the paper transparent: seen over the white page the view paints
    return tuple(round(v * a + 255 * (1 - a)) for v in (c.red(), c.green(), c.blue()))


def _near(colour, target, tolerance=40):
    return all(abs(a - b) <= tolerance for a, b in zip(colour, target))


def _pdf_point(name):
    """A square's point of tests/fixtures/layered_pdf.py, in the page's sheet units (y down)."""
    (x, y), colour = fx.COLOURS[name]
    return x, fx.HEIGHT - y, colour


@_own_caches
def test_the_pages_per_row_grow_as_the_view_zooms_out_and_each_page_is_rendered():
    app = _qt()
    place = _project("rows")
    view = _view(app, place, _pdf_doc(place))
    assert [i.page for i in view.area.pages] == [1, 2, 3]
    assert (view.area.info(1).width, view.area.info(1).height) == (300.0, 100.0)
    view.set_zoom(3.0)            # 900 px a page: one across
    assert view.pages_per_row() == 1
    view.set_zoom(0.8)            # 240 px a page: all three
    assert view.pages_per_row() == 3
    view.set_zoom(1.2)            # 360 px: two, then one
    assert view.pages_per_row() == 2 and view.area.rows == [[1, 2], [3]]
    _idle(app, view)
    for page in (1, 2, 3):
        assert page in view.area.base and not view.area.base[page].image.isNull()
    # what is rendered is the document's own choice of layers: «Dims» is off by the file's default, «Walls» on
    x, y, green = _pdf_point("green")
    assert _near(_sheet_colour(view, 1, x, y), green)
    x, y, _red = _pdf_point("red")
    assert _near(_sheet_colour(view, 1, x, y), (255, 255, 255))
    # the zoom stops where a page would be too small to carry its strip
    import document_view
    view.set_zoom(0.001)
    assert view.area.rects[1].width() >= document_view.MIN_PAGE_PX - 1e-9


@_own_caches
def test_ctrl_and_the_wheel_zoom_about_the_pointer_and_the_wheel_alone_scrolls():
    app = _qt()
    from PySide6.QtCore import QPoint, QPointF, Qt
    from PySide6.QtGui import QWheelEvent
    from PySide6.QtWidgets import QApplication
    place = _project("wheel")
    view = _view(app, place, _pdf_doc(place), height=500)
    view.set_zoom(2.5)
    assert view.pages_per_row() == 1 and view.area.verticalScrollBar().maximum() > 0
    viewport = view.area.viewport()

    def wheel(dy, modifiers, at):
        event = QWheelEvent(QPointF(at), QPointF(viewport.mapToGlobal(at)), QPoint(0, 0), QPoint(0, dy), Qt.MouseButton.NoButton, modifiers,
                            Qt.ScrollPhase.NoScrollPhase, False)
        QApplication.sendEvent(viewport, event)

    before = view.zoom()
    wheel(-120, Qt.KeyboardModifier.NoModifier, QPoint(300, 200))
    assert view.zoom() == before and view.area.verticalScrollBar().value() > 0
    at = view.viewport_point(1, 150, 50).toPoint()
    page, x, y = view.sheet_point(at)
    wheel(120, Qt.KeyboardModifier.ControlModifier, at)
    assert abs(view.zoom() / before - 1.2) < 1e-9
    page2, x2, y2 = view.sheet_point(at)
    assert page2 == page and abs(x2 - x) < 1 and abs(y2 - y) < 1     # the point under the pointer stays under it
    wheel(-240, Qt.KeyboardModifier.ControlModifier, at)
    assert abs(view.zoom() - before * 1.2 / 1.44) < 1e-9


@_own_caches
def test_a_page_is_ticked_into_the_plans_and_turned_by_its_own_buttons_or_the_bars():
    app = _qt()
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    place = _project("tick")
    view = _view(app, place, _pdf_doc(place))
    view.set_zoom(1.0)
    toggled, turned, selected = _record(view.pageToggled), _record(view.rotateRequested), _record(view.pageSelected)
    viewport = view.area.viewport()

    def click(rect):
        QTest.mouseClick(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, (rect.center() - view.area.scroll()).toPoint())

    box, _number, left, right = view.area.strip(2)
    click(box)
    assert toggled == [(2, True)] and view.used_pages() == [2]
    click(box)
    assert toggled[-1] == (2, False) and view.used_pages() == []
    view.set_used_pages([1, 3])
    assert view.used_pages() == [1, 3]
    click(right)
    click(left)
    assert turned == [(2, 90), (2, -90)]
    # the bar turns the pages selected, and only while some are
    assert not view.right_button.isEnabled()
    click(view.area.rects[3])
    assert selected[-1] == (3,) and view.selected_pages() == [3] and view.right_button.isEnabled()
    QTest.mouseClick(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier, (view.area.rects[1].center() - view.area.scroll()).toPoint())
    assert view.selected_pages() == [3, 1]
    view.left_button.click()
    assert turned[-2:] == [(3, -90), (1, -90)]
    assert view.document()["pages"][0]["rotation"] == 0     # the view writes nothing: the caller turns the page


@_own_caches
def test_a_crop_drawn_on_a_page_comes_back_in_its_sheet_units_exactly():
    app = _qt()
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtTest import QTest
    place = _project("crop")
    view = _view(app, place, _pdf_doc(place))
    drawn = _record(view.cropDrawn)
    viewport = view.area.viewport()
    view.set_tool("crop")
    assert view.crop_button.isChecked() and view.current_tool() == "crop"
    # at one pixel a point, a page starting on a whole pixel: the sheet point and the pixel are one
    view.set_zoom(1.0)
    a, b = view.viewport_point(2, 20, 10), view.viewport_point(2, 120, 70)
    assert a == QPointF(a.toPoint()) and b == QPointF(b.toPoint())
    QTest.mousePress(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, a.toPoint())
    QTest.mouseMove(viewport, b.toPoint())
    QTest.mouseRelease(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, b.toPoint())
    assert drawn == [(2, (20.0, 10.0, 100.0, 60.0))]
    # at any zoom, what comes back is the sheet under the pixels pressed and released
    view.set_zoom(1.7)
    a, b = view.viewport_point(1, 33.3, 12.1).toPoint(), view.viewport_point(1, 250.7, 88.9).toPoint()
    QTest.mousePress(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, a)
    QTest.mouseMove(viewport, b)
    QTest.mouseRelease(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, b)
    page, x0, y0 = view.sheet_point(a)
    _page, x1, y1 = view.sheet_point(b)
    got = drawn[-1]
    assert got[0] == page == 1
    assert all(abs(g - e) < 1e-3 for g, e in zip(got[1], (x0, y0, x1 - x0, y1 - y0)))
    assert abs(got[1][0] - 33.3) < 1 and abs(got[1][2] - (250.7 - 33.3)) < 1.5
    # dragged past the page's edge, the crop stops at the edge
    a = view.viewport_point(3, 200, 50).toPoint()
    out = (view.area.rects[3].bottomRight() - view.area.scroll() + QPointF(40, 40)).toPoint()
    QTest.mousePress(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, a)
    QTest.mouseMove(viewport, out)
    QTest.mouseRelease(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, out)
    page, (x, y, w, h) = drawn[-1]
    assert page == 3 and abs(x + w - 300) < 1e-6 and abs(y + h - 100) < 1e-6
    # Escape leaves the tool, and its button, for the selection (v0.116)
    QTest.keyClick(view.area, Qt.Key.Key_Escape)
    assert view.current_tool() == "select" and not view.crop_button.isChecked() and view.select_button.isChecked()


@_own_caches
def test_calibration_takes_two_clicks_on_one_page_and_escape_cancels_the_first():
    app = _qt()
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    place = _project("calibrate")
    view = _view(app, place, _pdf_doc(place))
    view.set_zoom(1.0)
    done = _record(view.calibrated)
    viewport = view.area.viewport()
    view.set_tool("calibrate")
    assert view.calibrate_button.isChecked() and not view.crop_button.isChecked()
    click = lambda page, x, y: QTest.mouseClick(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, view.viewport_point(page, x, y).toPoint())
    click(1, 10, 20)
    QTest.keyClick(view.area, Qt.Key.Key_Escape)
    assert view.area.calib is None and view.current_tool() == "calibrate"
    click(1, 10, 20)
    click(2, 50, 50)          # another page: the first point is taken there again
    click(2, 250, 50)
    assert done == [(2, [(50.0, 50.0), (250.0, 50.0)])]


@_own_caches
def test_the_crops_are_drawn_on_their_pages_a_click_in_one_chooses_it_and_a_double_click_opens_its_plan():
    app = _qt()
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    place = _project("crops")
    view = _view(app, place, _pdf_doc(place))
    view.set_zoom(1.0)
    _idle(app, view)
    before = view.area.viewport().grab().toImage()
    view.set_crops({1: [{"plan": "P01", "rect": (60, 10, 150, 80), "label": "P01 – Haus – EG"}],
                    2: [{"plan": "P02", "rect": (0, 0, 300, 100), "label": "P02"}, {"plan": "P03", "rect": (200, 20, 50, 50), "label": "P03"}]})
    app.processEvents()
    after = view.area.viewport().grab().toImage()
    ratio = after.width() / view.area.viewport().width()
    edge = view.viewport_point(1, 100, 10)
    changed = [before.pixelColor(round((edge.x() + dx) * ratio), round(edge.y() * ratio)) != after.pixelColor(round((edge.x() + dx) * ratio), round(edge.y() * ratio)) for dx in range(0, 20)]
    assert any(changed), "the crop's dashed edge is drawn"
    activated, selected, chosen = _record(view.planActivated), _record(view.pageSelected), _record(view.frameSelected)
    viewport = view.area.viewport()
    QTest.mouseClick(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, view.viewport_point(1, 100, 50).toPoint())
    assert chosen == [(["P01"],)] and selected[-1] == (1,) and activated == [], "a click chooses the frame, and opens nothing"
    QTest.mouseClick(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, view.viewport_point(1, 20, 50).toPoint())
    assert chosen[-1] == ([],) and selected[-1] == (1,)          # outside the crop: the page alone, the frame let go
    QTest.mouseDClick(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, view.viewport_point(1, 100, 50).toPoint())
    assert activated == [("P01",)], "a double click opens the plan"
    QTest.mouseClick(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, view.viewport_point(2, 220, 40).toPoint())
    assert chosen[-1] == (["P03"],)                               # of two crops, the smaller one holding the point
    QTest.mouseClick(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier, view.viewport_point(2, 100, 40).toPoint())
    assert chosen[-1] == (["P03", "P02"],) and view.selected_frames() == ["P03", "P02"], "Ctrl adds a frame"


@_own_caches
def test_a_layer_switched_is_said_at_once_and_the_page_rendered_again_without_it():
    app = _qt()
    place = _project("layers")
    doc = _pdf_doc(place)
    view = _view(app, place, doc)
    view.set_zoom(1.0)
    _idle(app, view)
    assert view.layers_button.isEnabled()
    view.show_layers(True)
    assert view.panel.isVisible()
    assert [(l["name"], l["on"]) for l in view.panel.layers()] == [("Dims", False), ("Walls", True), ("Furniture", True)]
    changed = _record(view.layersChanged)
    first_source = view.area.sources[0][0]
    x, y, green = _pdf_point("green")
    assert _near(_sheet_colour(view, 1, x, y), green)
    item = next(view.panel.list.item(i) for i in range(view.panel.list.count()) if view.panel.list.item(i).text() == "Walls")
    from PySide6.QtCore import Qt
    item.setCheckState(Qt.CheckState.Unchecked)
    assert changed == [(["Dims", "Walls"],)] and view.document()["layers_off"] == ["Dims", "Walls"]
    assert view.is_busy() and view.busy_label.isVisibleTo(view)
    assert 1 in view.area.base                                     # the old render stays while the new one comes
    _idle(app, view)
    assert view.area.sources[0][0] != first_source and not view.busy_label.isVisibleTo(view)
    assert _near(_sheet_colour(view, 1, x, y), (255, 255, 255))     # the walls are gone from the page
    # the caller saves and hands the same document back: nothing to render again
    view.set_document(place, view.document())
    assert view.loading is None
    # «Tout» and «Aucun» act on the layers the filter shows
    view.panel.filter.setText("furn")
    view.panel.set_all(False)
    assert changed[-1] == (["Dims", "Walls", "Furniture"],)
    view.panel.filter.setText("")
    view.panel.set_all(True)
    assert changed[-1] == ([],)
    _idle(app, view)
    assert _near(_sheet_colour(view, 1, x, y), green)


@_own_caches
def test_a_page_turned_is_laid_out_turned_once_the_caller_hands_the_document_back():
    app = _qt()
    from domains import plan_documents
    place = _project("turn")
    doc = _pdf_doc(place)
    view = _view(app, place, doc)
    plan_documents.set_rotation(doc, 2, 90)
    view.set_document(place, doc)
    _idle(app, view)
    assert (view.area.info(2).width, view.area.info(2).height) == (100.0, 300.0)
    rect = view.area.rects[2]
    assert abs(rect.width() / rect.height() - 1 / 3) < 1e-9
    assert view.area.base[2].image.height() > view.area.base[2].image.width()


@_own_caches
def test_a_drawing_is_shown_layout_by_layout_in_its_own_sheet_units():
    app = _qt()
    try:
        import ezdxf
    except ImportError as exc:
        raise Skip(f"ezdxf is not installed ({exc})")
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    import document_view
    from domains import plan_documents
    place = _project("dxf")
    drawing = ezdxf.new(units=4)
    drawing.layers.add("Wand")
    drawing.layers.add("Mass").off()
    msp = drawing.modelspace()
    msp.add_line((0, 0), (8000, 0), dxfattribs={"layer": "Wand"})
    msp.add_line((8000, 0), (8000, 4000), dxfattribs={"layer": "Wand"})
    msp.add_line((0, 4000), (8000, 4000), dxfattribs={"layer": "Mass"})
    drawing.layouts.new("Grundriss")
    path = place.root / "01_Pläne" / "Plan.dxf"
    drawing.saveas(path)
    doc = plan_documents.import_file(place, path)
    view = _view(app, place, doc)
    count = plan_documents.page_count(place, doc)
    assert [i.page for i in view.area.pages] == list(range(1, count + 1))
    info = view.area.info(1)
    assert (info.width, info.height) == plan_documents.page_size(place, doc, 1) and info.unit == document_view.CAD_UNIT_PT
    _idle(app, view)
    assert 1 in view.area.base and not view.area.base[1].image.isNull()
    assert [l["name"] for l in view.panel.layers() if not l["on"]] == ["Mass"]
    # the view's points are the layout's viewBox units, both ways
    for fx_, fy_ in ((0.0, 0.0), (0.3, 0.45), (0.999, 0.999)):
        x, y = info.width * fx_, info.height * fy_
        page, sx, sy = view.sheet_point(view.viewport_point(1, x, y))
        assert page == 1 and abs(sx - x) < 1e-6 and abs(sy - y) < 1e-6
    drawn = _record(view.cropDrawn)
    view.set_tool("crop")
    a, b = view.viewport_point(1, info.width * 0.1, info.height * 0.2).toPoint(), view.viewport_point(1, info.width * 0.6, info.height * 0.7).toPoint()
    QTest.mousePress(view.area.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, a)
    QTest.mouseMove(view.area.viewport(), b)
    QTest.mouseRelease(view.area.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, b)
    _page, x0, y0 = view.sheet_point(a)
    _page, x1, y1 = view.sheet_point(b)
    page, rect = drawn[-1]
    assert page == 1 and all(abs(g - e) < 1e-3 for g, e in zip(rect, (x0, y0, x1 - x0, y1 - y0)))


@_own_caches
def test_an_image_is_painted_from_its_own_file():
    app = _qt()
    from PySide6.QtGui import QColor, QImage
    from domains import plan_documents
    place = _project("image")
    image = QImage(80, 40, QImage.Format.Format_RGB32)
    image.fill(QColor(0, 0, 255))
    path = place.root / "01_Pläne" / "Foto.png"
    image.save(str(path))
    doc = plan_documents.import_file(place, path)
    view = _view(app, place, doc)
    assert (view.area.info(1).width, view.area.info(1).height) == (80.0, 40.0)
    assert 1 in view.area.images and not view.layers_button.isEnabled()


def test_the_views_words_are_the_same_keys_in_three_languages():
    _qt()
    import document_view
    keys = set(document_view.STRINGS["fr"])
    assert all(key.startswith("dv_") for key in keys)
    for lang in ("de", "en"):
        assert set(document_view.STRINGS[lang]) == keys, lang
    for key, text in document_view.STRINGS["de"].items():
        assert "ß" not in text, key
    for key, text in document_view.STRINGS["fr"].items():
        assert not re.search(r"[^\s  ][;:](\s|$)", text), f"fr {key}: a space before : and ;"
    for lang in ("de", "en"):
        # tests/test_i18n.py's own rule: a sentence the same in two languages is a missed translation, a word is a cognate
        same = [k for k in keys if document_view.STRINGS[lang][k] == document_view.STRINGS["fr"][k]
                and " " in re.sub(r"\{[^}]*\}", "", document_view.STRINGS["fr"][k]).strip() and len(re.sub(r"\{[^}]*\}", "", document_view.STRINGS["fr"][k])) > 12]
        assert not same, f"{lang}: left in French: {same}"
    for lang, table in document_view.STRINGS.items():
        t = document_view.words(lang)
        assert t("dv_page", n=3).endswith("3") and "{" not in t("dv_layers_count", on=1, n=2)


def test_the_view_is_retranslated_in_place():
    app = _qt()
    import document_view
    view = document_view.DocumentView(lang="fr")
    assert view.crop_button.accessibleName() == "Cadrer"
    view.retranslate(document_view.words("de"))
    assert view.crop_button.accessibleName() == "Zuschneiden" and view.panel.all_button.text() == "Alle"
    view.set_tool("crop")
    assert view.hint_label.text() == document_view.STRINGS["de"]["dv_hint_crop"]
    app.processEvents()


@_own_caches
def test_a_page_seen_close_is_rendered_again_at_the_screens_resolution_and_the_file_is_never_held_open():
    """A PDF QtPdf loads from its path stays open on Windows for as long as the view shows it -- and that is the architect's own file where nothing is switched off or turned (plan_documents.render_source hands the file itself back): the next version could not be copied over it. The view loads it from memory."""
    app = _qt()
    import os as _os
    import document_view
    place = _project("sharp")
    doc = _pdf_doc(place)
    view = _view(app, place, doc)
    view.set_zoom(6.0)                       # 1800 × 600 px a page: sharper than the coarse render
    _idle(app, view)
    page = view.area.visible_pages()[0]
    shown = view.area.sharp[page]
    ratio = view.area.viewport().devicePixelRatioF()
    assert abs(shown.scale - 6.0 * ratio) < 0.01 and shown.norm == document_view.QRectF(0, 0, 1, 1)
    view.set_zoom(document_view.MAX_ZOOM)    # too many pixels for the whole page: the part in view alone
    _idle(app, view)
    page = view.area.visible_pages()[0]
    shown = view.area.sharp[page]
    assert shown.norm.width() < 1 and abs(shown.scale - document_view.MAX_ZOOM * ratio) < 0.01
    # the file shown can be replaced under the view
    original = place.root / "01_Pläne" / "Plan.pdf"
    assert view.area.sources[0][0] == original
    copy = place.root / "01_Pläne" / "Neu.pdf"
    copy.write_bytes(original.read_bytes())
    _os.replace(copy, original)


def test_a_crop_of_the_other_kind_is_drawn_muted_and_never_hit_and_the_other_pages_are_marked():
    app = _qt()
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    place = _project("other_crops")
    view = _view(app, place, _pdf_doc(place))
    view.set_zoom(1.0)
    _idle(app, view)
    own = {"plan": "P01", "rect": (60, 10, 150, 80), "label": "P01"}
    other = {"plan": "F01", "rect": (0, 0, 300, 100), "label": "F01 – Haus", "other": True, "kind": "Incendie"}
    view.set_crops({1: [own, other]})
    area = view.area
    assert [plan for plan, _r, _l in area.crop_rects(1)] == ["P01"], "a crop of the other kind is not among those of its own"
    assert [label for _r, label in area.other_crop_rects(1)] == ["Incendie F01 – Haus"]
    activated = _record(view.planActivated)
    viewport = area.viewport()
    QTest.mouseDClick(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, view.viewport_point(1, 20, 50).toPoint())
    assert activated == [], "the other kind's crop is never hit"
    assert area.hit(view.viewport_point(1, 20, 50) + area.scroll()) == ("page", 1)
    QTest.mouseDClick(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, view.viewport_point(1, 100, 50).toPoint())
    assert activated == [("P01",)], "inside both, the plan of its own kind"
    # the hollow marker beside the tick: set, kept sorted, painted -- and nothing changes where it is not used
    assert view.other_pages() == []
    before = area.viewport().grab().toImage()
    view.set_other_pages([2, 1])
    app.processEvents()
    after = area.viewport().grab().toImage()
    assert view.other_pages() == [1, 2] and before != after
    view.set_other_pages([])
    view.set_crops({})
    app.processEvents()
    assert view.other_pages() == [] and area.other_crop_rects(1) == []
