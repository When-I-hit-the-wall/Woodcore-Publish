"""The documents a position plan is drawn on (v0.114, calc/domains/plan_documents.py, docs/domain/position-plans.md §3.3sexies): imported once, their pages turned and their layers switched off by the engineer, rendered for the window, flattened for the report.

The PDF is `tests/fixtures/layered_pdf.py`'s, written in the test: three optional-content groups, marked-content sections, a form XObject with an /OC of its own, a form holding a section, a membership dictionary, and a hidden section that only moves the coordinates. Each check renders a page with QtPdf -- PDFium, the window's own renderer -- and reads the colour of each square, so what is held is what is **seen**, and the report's flattened page is held equal, pixel for pixel, to the window's rendering of the same choice of layers.

⚠️ What the flattening rests on, found while it was written and held by `test_a_hidden_section_still_moves_what_follows`: PDF 2.0 8.11.3.2 hides a section's **painting** and keeps its **change of the graphics state** -- a `cm`, a colour, a clip. Taking a hidden section out whole, the obvious reading, would have moved everything drawn after a hidden `cm`, and PDFium (the window) does not.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import re
import subprocess
from pathlib import Path

import conftest
import engine
import validation
from domains import plan
from domains import plan_documents as documents
from fixtures import layered_pdf as fx


def _project(name):
    """A project folder of the test's own -- its root and plans folder, which is what plan_documents asks of a Project -- and the caches pointed into it, never at the engineer's %LOCALAPPDATA%."""
    root = conftest.tmpdir(f"pdoc_{name}")
    (root / "01_Pläne").mkdir()
    (root / "Woodcore-Datei" / "plans").mkdir(parents=True)
    documents.CACHE_ROOT = root / "_cache"
    return documents.Place(root, root / "Woodcore-Datei" / "plans")


def _pdf(place, name="Plan.pdf", **kwargs):
    return fx.write(place.root / "01_Pläne" / name, **kwargs)


def test_a_pdf_is_imported_with_its_pages_and_the_layers_it_hides():
    place = _project("import")
    path = _pdf(place, pages=2)
    doc = documents.import_file(place, path, name="Grundrisse")
    assert doc["id"] == "D01" and doc["kind"] == "pdf" and doc["file"] == "01_Pläne/Plan.pdf"
    assert doc["pages"] == [{"page": 1, "rotation": 0}, {"page": 2, "rotation": 0}]
    assert doc["layers_off"] == ["Dims"], "the file's own default state is what a document starts with"
    assert doc["sha256"] == plan.file_hash(path)
    assert documents.read(place, "D01") == doc
    assert [d["id"] for d in documents.list_documents(place)] == ["D01"]
    assert documents.new_id(place) == "D02"
    # a document is a source of its own, in a subfolder the plans' glob does not reach
    assert plan.source_paths(place.plans_dir) == []
    text = (documents.source_dir(place) / "D01.json").read_bytes()
    assert b"\r\n" not in text and text.endswith(b"\n")


def test_a_file_outside_the_project_or_of_another_kind_is_refused_by_its_code():
    place = _project("refused")
    outside = fx.write(conftest.tmpdir("pdoc_outside") / "elsewhere.pdf")
    for path, code in ((outside, "doc_outside"), (place.root / "01_Pläne" / "Notes.txt", "doc_kind")):
        try:
            documents.import_file(place, path)
        except documents.DocumentError as exc:
            assert exc.code == code, (exc.code, code)
        else:
            assert False, f"{path.name} was imported"
    try:
        documents.read(place, "D07")
    except documents.DocumentError as exc:
        assert exc.code == "doc_missing"
    else:
        assert False, "a document that is not there was read"


def test_the_layers_follow_the_documents_choice_and_not_the_files():
    place = _project("layers")
    doc = documents.import_file(place, _pdf(place))
    assert documents.layers(place, doc) == [{"name": "Dims", "on": False}, {"name": "Walls", "on": True}, {"name": "Furniture", "on": True}]
    documents.set_layer(doc, "Dims", True)
    documents.set_layer(doc, "Walls", False)
    assert doc["layers_off"] == ["Walls"]
    assert [layer["on"] for layer in documents.layers(place, doc)] == [True, False, True]


def test_a_page_turns_by_quarter_turns_and_its_size_turns_with_it():
    place = _project("rotation")
    doc = documents.import_file(place, _pdf(place))
    assert documents.page_size(place, doc, 1) == (300.0, 100.0)
    documents.set_rotation(doc, 1, -90)
    assert documents.rotation(doc, 1) == 270
    assert documents.page_size(place, doc, 1) == (100.0, 300.0)
    for degrees, page in ((45, 1), (90, 2)):
        try:
            documents.set_rotation(doc, page, degrees)
        except documents.DocumentError as exc:
            assert exc.code in ("doc_rotation", "doc_page")
        else:
            assert False, f"rotation {degrees} of page {page} was taken"
    documents.write(place, doc)
    assert documents.read(place, doc["id"])["pages"][0]["rotation"] == 270


def test_the_flattened_page_takes_out_exactly_the_layers_switched_off():
    """The report's page against what the engineer switched off: Dims (the file's default), then Walls and Furniture as well -- a form whose own /OC is off goes, a section inside a form goes and what is beside it stays, and a membership dictionary AllOn(Walls, Furniture) follows its groups."""
    place = _project("flatten")
    doc = documents.import_file(place, _pdf(place))
    flat = place.root / "flat.pdf"
    flat.write_bytes(documents.flatten_page(place, doc, 1))
    image, size = fx.render(flat)
    assert size == (300.0, 100.0)
    seen = {name: fx.shows(image, name) for name in fx.COLOURS}
    assert seen == {"grey": True, "red": False, "green": True, "blue": True, "magenta": False, "black": True, "cyan": True, "orange": True}, seen
    for name in ("Walls", "Furniture"):
        documents.set_layer(doc, name, False)
    flat.write_bytes(documents.flatten_page(place, doc, 1))
    image, _ = fx.render(flat)
    seen = {name: fx.shows(image, name) for name in fx.COLOURS}
    assert seen == {"grey": True, "red": False, "green": False, "blue": False, "magenta": False, "black": True, "cyan": False, "orange": True}, seen
    # nothing optional left for Typst to draw whatever its state
    from pypdf import PdfReader
    reader = PdfReader(flat)
    assert "/OCProperties" not in reader.trailer["/Root"]
    assert len(reader.pages) == 1


def test_the_report_sees_what_the_window_sees():
    """The window renders the document with the off groups stated as its default (render_source, which PDFium honours); the report sets the flattened page. The two are the same image, pixel for pixel -- for every subset of the three groups."""
    place = _project("same")
    doc = documents.import_file(place, _pdf(place))
    import itertools
    for count in range(4):
        for off in itertools.combinations(fx.GROUPS, count):
            doc["layers_off"] = list(off)
            window, _ = fx.render(documents.render_source(place, doc))
            flat = place.root / "flat.pdf"
            flat.write_bytes(documents.flatten_page(place, doc, 1))
            report, _ = fx.render(flat)
            assert window == report, f"the window and the report differ with {off} switched off"


def test_a_hidden_section_still_moves_what_follows():
    """PDF 2.0 8.11.3.2: hidden content paints nothing and changes the graphics state as it would have. The fixture's last «Dims» section only moves the coordinates up 30 pt, and the orange square after it is drawn at y 50 -- with «Dims» shown and with it hidden alike. Taking the section out whole would have dropped the square to y 20."""
    place = _project("state")
    doc = documents.import_file(place, _pdf(place))
    for off in ([], ["Dims"]):
        doc["layers_off"] = off
        flat = place.root / "flat.pdf"
        flat.write_bytes(documents.flatten_page(place, doc, 1))
        image, _ = fx.render(flat)
        assert fx.shows(image, "orange"), off
        assert fx.colour_at(image, (145, 25)) == (255, 255, 255), f"the orange square fell back to y 20 with {off} off"


def test_a_turned_page_is_turned_for_the_window_and_for_the_report():
    place = _project("turned")
    doc = documents.import_file(place, _pdf(place, pages=2))
    documents.set_rotation(doc, 2, 90)
    view = documents.render_source(place, doc)
    from pypdf import PdfReader
    reader = PdfReader(view)
    assert [int(p.rotation) for p in reader.pages] == [0, 90], "every page keeps its number, and only the turned one turns"
    flat = place.root / "flat.pdf"
    flat.write_bytes(documents.flatten_page(place, doc, 2))
    _image, size = fx.render(flat)
    assert size == (100.0, 300.0)
    assert documents.page_size(place, doc, 2) == size


def test_nothing_is_rendered_twice_and_an_untouched_pdf_is_shown_as_it_is():
    place = _project("cache")
    path = _pdf(place, off=())
    doc = documents.import_file(place, path)
    assert documents.render_source(place, doc) == path, "a PDF neither turned nor switched differently is the file itself"
    documents.set_layer(doc, "Walls", False)
    first = documents.render_source(place, doc)
    assert first != path and first.is_file()
    stamp = first.stat().st_mtime_ns
    assert documents.render_source(place, doc) == first and first.stat().st_mtime_ns == stamp
    from pypdf import PdfReader
    default = PdfReader(first).trailer["/Root"]["/OCProperties"]["/D"]
    assert [g.get_object()["/Name"] for g in default["/OFF"]] == ["Walls"]


def test_typst_sets_the_flattened_page_without_its_hidden_layers():
    """Typst's PDF export draws every optional-content group whatever its state (it warns: «PDF contains optional content groups»): the flattened page carries none, so Typst says nothing and draws what the window draws."""
    if not conftest.have_typst():
        raise conftest.Skip("Typst is not installed")
    place = _project("typst")
    doc = documents.import_file(place, _pdf(place))
    (place.root / "flat.pdf").write_bytes(documents.flatten_page(place, doc, 1))
    (place.root / "t.typ").write_text('#set page(width: 300pt, height: 100pt, margin: 0pt)\n#image("flat.pdf", width: 100%)\n', encoding="utf-8")
    result = subprocess.run(["typst", "compile", "--ppi", "144", str(place.root / "t.typ"), str(place.root / "t.png")], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "optional content" not in result.stderr, result.stderr
    from PySide6.QtGui import QImage
    image = QImage(str(place.root / "t.png"))
    seen = {name: fx.shows(image, name) for name in fx.COLOURS}
    assert seen == {"grey": True, "red": False, "green": True, "blue": True, "magenta": False, "black": True, "cyan": True, "orange": True}, seen


def _png(path, width=40, height=20):
    import os
    from PySide6.QtGui import QColor, QGuiApplication, QImage
    QGuiApplication.instance() or QGuiApplication([])
    image = QImage(width, height, QImage.Format_RGB32)
    image.fill(QColor("red"))
    image.save(str(path))
    return path


def test_an_image_turned_is_an_svg_that_turns_it():
    place = _project("image")
    doc = documents.import_file(place, _png(place.root / "01_Pläne" / "Skizze.png"))
    assert doc["kind"] == "image" and doc["layers_off"] == [] and documents.page_count(place, doc) == 1
    assert documents.render_source(place, doc) == place.root / "01_Pläne" / "Skizze.png"
    content, fmt = documents.background(place, doc, 1)
    assert fmt == "png" and content == (place.root / "01_Pläne" / "Skizze.png").read_bytes()
    documents.set_rotation(doc, 1, 90)
    assert documents.page_size(place, doc, 1) == (20.0, 40.0)
    content, fmt = documents.background(place, doc, 1)
    assert fmt == "svg" and 'viewBox="0 0 20 40"' in content
    from PySide6.QtCore import QByteArray
    from PySide6.QtSvg import QSvgRenderer
    renderer = QSvgRenderer(QByteArray(content.encode("utf-8")))
    assert renderer.isValid() and renderer.viewBoxF().width() == 20


def test_an_svg_is_turned_about_its_own_sheet():
    text = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="10 20 200 100" width="200" height="100"><rect x="10" y="20" width="10" height="10"/></svg>'
    for degrees, box in ((90, "0 0 100 200"), (180, "0 0 200 100"), (270, "0 0 100 200")):
        turned = documents.rotate_svg(text, degrees)
        assert f'viewBox="{box}"' in turned, turned
        assert "translate(-10 -20)" in turned, "a viewBox not starting at 0, 0 is moved there first"
    assert 'width="100" height="200"' in documents.rotate_svg(text, 90)
    assert documents.rotate_svg(text, 360) == text


def _dxf(place):
    import ezdxf
    doc = ezdxf.new(units=4)
    doc.layers.add("Wand")
    doc.layers.add("Mass").off()
    msp = doc.modelspace()
    msp.add_line((0, 0), (8000, 0), dxfattribs={"layer": "Wand"})
    msp.add_line((8000, 0), (8000, 4000), dxfattribs={"layer": "Wand"})
    msp.add_line((0, 4000), (8000, 4000), dxfattribs={"layer": "Mass"})
    doc.layouts.new("Grundriss")
    path = place.root / "01_Pläne" / "Plan.dxf"
    doc.saveas(path)
    return path


def test_a_dxf_is_a_document_whose_pages_are_its_layouts():
    place = _project("dxf")
    doc = documents.import_file(place, _dxf(place))
    assert doc["kind"] == "cad"
    assert [p["layout"] for p in doc["pages"]][0] == "Model" and "Grundriss" in [p["layout"] for p in doc["pages"]]
    assert doc["layers_off"] == ["Mass"]
    assert {layer["name"]: layer["on"] for layer in documents.layers(place, doc)}["Mass"] is False
    view = documents.render_source(place, doc, 1)
    assert view.suffix == ".svg" and view.read_text(encoding="utf-8").startswith("<svg")
    width, height = documents.page_size(place, doc, 1)
    content, fmt = documents.background(place, doc, 1)
    assert fmt == "svg" and f'viewBox="0 0 {width:g} {height:g}"' in content
    documents.set_rotation(doc, 1, 90)
    assert documents.page_size(place, doc, 1) == (height, width)
    assert f'viewBox="0 0 {height:g} {width:g}"' in documents.background(place, doc, 1)[0]


def test_a_dwg_is_read_through_the_dxf_the_converter_makes_of_it():
    """The converter mocked: a DWG is imported, converted once into the cache and read from there; without a converter the import says where to download one."""
    from domains import cad
    place = _project("dwg")
    dxf = _dxf(place)
    dwg = place.root / "01_Pläne" / "Plan.dwg"
    dwg.write_bytes(b"AC1032 not really a drawing")
    original = cad.convert_dwg
    try:
        cad.convert_dwg = lambda path, target, converter=None: (Path(target).parent.mkdir(parents=True, exist_ok=True), Path(target).write_bytes(dxf.read_bytes()), Path(target))[2]
        doc = documents.import_file(place, dwg)
        assert doc["kind"] == "cad" and doc["layers_off"] == ["Mass"]
        assert documents.cad_source(place, doc).parent == documents.cache_dir("cad")
        original_oda = cad.oda_converter
        cad.convert_dwg = original
        cad.oda_converter = lambda program_files=None: None
        try:
            (documents.cad_source(place, doc)).unlink()  # the cache cleared: converted again, and there is no converter
            documents.page_size(place, doc, 1)
        except cad.CadError as exc:
            assert exc.code == "oda_missing" and cad.ODA_URL in str(exc)
        else:
            assert False, "a DWG was read with no converter"
        finally:
            cad.oda_converter = original_oda
    finally:
        cad.convert_dwg = original


def test_a_document_source_is_checked():
    place = _project("check")
    doc = documents.import_file(place, _pdf(place))
    for broken in ({**doc, "kind": "image"}, {**doc, "pages": [{"page": 2, "rotation": 0}]},
                   {**doc, "pages": [{"page": 1, "rotation": 45}]}, {**doc, "schema_version": "2.0"}, {k: v for k, v in doc.items() if k != "sha256"}):
        try:
            documents.check(broken, "D01.json")
        except validation.ValidationError:
            pass
        else:
            assert False, f"{broken} passed"


def test_refresh_keeps_the_rotations_and_says_what_changed():
    place = _project("refresh")
    path = _pdf(place)
    doc = documents.import_file(place, path)
    documents.set_rotation(doc, 1, 180)
    same, notes = documents.refresh(place, doc)
    assert same is doc and notes == []
    fx.write(path, pages=3, off=("Walls",))
    fresh, notes = documents.refresh(place, doc)
    assert [p["rotation"] for p in fresh["pages"]] == [180, 0, 0] and fresh["sha256"] == plan.file_hash(path)
    assert fresh["layers_off"] == ["Dims"], "the document's own choice is kept where the file still names the layer"
    assert len(notes) == 2


# --- the export -----------------------------------------------------------------------------------

def _plan_on(place, doc, page=1, pid="P01", **extra):
    source = plan.new_source(pid)
    width, height = documents.page_size(place, doc, page)
    source["sheet"] = {"width": width, "height": height}
    source["background"] = {"file": doc["file"], "page": page, "document": doc["id"], "sha256": doc["sha256"]}
    source["elements"] = [{"type": "S", "label": "S001", "points": [[50, 50]]}]
    source.update(extra)
    plan.check_source(source, f"{pid}.json")
    (place.plans_dir / f"{pid}.json").write_text(json.dumps(source, ensure_ascii=False, indent=2), encoding="utf-8")
    return source


def test_the_export_sets_the_flattened_page_and_keeps_it_while_nothing_changed():
    place = _project("export")
    doc = documents.import_file(place, _pdf(place))
    documents.set_layer(doc, "Walls", False)
    documents.set_rotation(doc, 1, 90)
    documents.write(place, doc)
    _plan_on(place, doc)
    data_dir = place.root / "data"
    data, files, notes = plan.prepare(place.plans_dir, place.root, data_dir, ["S001"])
    record = data["plans"]["P01"]
    assert data["schema_version"] == "1.3" and record["storey"] == "" and record["role"] == "plan"
    background = record["background"]
    assert background["file"] == "plans/P01-plan.pdf" and background["format"] == "pdf"
    assert background["document"] == "D01" and background["rotation"] == 90 and background["layers_off"] == ["Dims", "Walls"]
    assert not any("hides some of its layers" in n for n in notes), notes
    page = files["plans/P01-plan.pdf"]
    from pypdf import PdfReader
    import io
    reader = PdfReader(io.BytesIO(page))
    assert "/OCProperties" not in reader.trailer["/Root"] and int(reader.pages[0].rotation) == 90
    plan.write(data, files, data_dir)
    again, files2, _ = plan.prepare(place.plans_dir, place.root, data_dir, ["S001"])
    assert files2["plans/P01-plan.pdf"] == page, "a background already written for the same file, page, rotation and layers is kept byte for byte"
    documents.set_layer(doc, "Walls", True)
    documents.write(place, doc)
    third, files3, _ = plan.prepare(place.plans_dir, place.root, data_dir, ["S001"])
    assert third["plans"]["P01"]["background"]["layers_off"] == ["Dims"] and files3["plans/P01-plan.pdf"] != page


def test_a_plan_on_a_drawing_sets_its_layout_as_an_svg():
    place = _project("export_cad")
    doc = documents.import_file(place, _dxf(place))
    _plan_on(place, doc)
    data, files, _notes = plan.prepare(place.plans_dir, place.root, place.root / "data", ["S001"])
    background = data["plans"]["P01"]["background"]
    assert background["format"] == "svg" and background["file"] == "plans/P01-plan.svg"
    assert files["plans/P01-plan.svg"].startswith("<svg")


def test_a_plan_whose_document_is_gone_is_drawn_on_its_file_and_says_so():
    place = _project("export_gone")
    doc = documents.import_file(place, _pdf(place))
    _plan_on(place, doc)
    (documents.source_dir(place) / "D01.json").unlink()
    data, files, notes = plan.prepare(place.plans_dir, place.root, place.root / "data", ["S001"])
    assert any(getattr(n, "code", "") == "plan_document_missing" for n in notes), notes
    background = data["plans"]["P01"]["background"]
    assert "document" not in background and background["origin"] == "01_Pläne/Plan.pdf"


# --- the frame and its helpers, shared with a second kind of plan -------------------------------------

def test_the_frame_is_checked_on_its_own_and_a_background_exports_under_the_stem_it_is_given():
    place = _project("frame")
    doc = documents.import_file(place, _pdf(place))
    source = _plan_on(place, doc)
    plan.check_frame(source, "P01.json")
    for broken in ({**source, "crop": {"x": 0, "y": 0, "w": 1e9, "h": 1}},
                   {**source, "scale": {"mode": "ratio", "ratio": -1}},
                   {**source, "background": {**source["background"], "document": "no way"}}):
        try:
            plan.check_frame(broken, "P01.json")
        except validation.ValidationError:
            pass
        else:
            assert False, f"{broken} passed"
    files, notes = {}, []
    got = plan.document_background(source["background"], place.root, place.plans_dir, engine.Figures(place.root / "data", "fire"), "fire/F01-plan", {}, "F01.json", "fire plan F01", files, notes)
    assert got is not None and got[0]["file"] == "fire/F01-plan.pdf" and "fire/F01-plan.pdf" in files and not notes
    plain = {"file": doc["file"], "page": 1}
    background, sheet, more = plan.file_background(plain, got[1], place.root, engine.Figures(place.root / "data", "fire"), "fire/F02-plan", {}, "F02.json", "fire plan F02", files)
    assert background["file"] == "fire/F02-plan.pdf" and background["origin"] == doc["file"] and "fire/F02-plan.pdf" in files
    assert plan.turn_point([10, 20], 100) == [80, 10] and plan.turn_rect({"x": 0, "y": 0, "w": 10, "h": 20}, 100)["x"] == 80


# --- Imported Plans/: the document copied at its import (issue #64, D-09, D-18) ------------------

def _folders_project(name):
    """A copy of the project the tests work on, laid out by folders, with the caches pointed into it."""
    here = conftest.project_copy(f"pdoc_{name}")
    assert here.has_folders
    documents.CACHE_ROOT = here.root / "_cache"
    (here.root / "01_Pläne").mkdir(exist_ok=True)
    return here


def test_laid_out_by_folders_a_document_is_copied_into_imported_plans_from_anywhere():
    """REQ-007: the file copied into its tab's Imported Plans/ under its name, the document naming the copy, the original untouched -- a file outside the project too; the fire plans' into their own."""
    here = _folders_project("copied")
    original = fx.write(conftest.tmpdir("pdoc_outside_folders") / "03_Pavillon.pdf", pages=2)
    before = original.read_bytes()
    doc = documents.import_file(here, original, name="Pavillon")
    copy = documents.imported_dir(here, "plan") / "03_Pavillon.pdf"
    assert doc["file"] == "Plans/Position-plan/Imported Plans/03_Pavillon.pdf" and copy.read_bytes() == before
    assert original.read_bytes() == before, "the original is never touched"
    assert documents.file_path(here, doc) == copy
    again = documents.import_file(here, original)
    assert again["file"] == doc["file"] and again["id"] != doc["id"], "the same file again: the copy taken as it is, nothing copied twice"
    fire_doc = documents.import_file(here, _pdf(here, "Brandschutz.pdf"), owner="fire")
    assert fire_doc["file"] == "Plans/Fire-plan/Imported Plans/Brandschutz.pdf"
    assert documents.imported_dir(_project("before"), "plan") is None, "a project laid out before copies nothing"


def test_a_document_of_the_same_name_and_other_content_is_replaced_only_on_confirmation_and_its_plans_follow():
    """D-18: `doc_replace` first; with `replace` the copy written over and the document that names it read again -- the same id, its new pages, its new SHA-256 -- rather than a new one."""
    here = _folders_project("replace")
    doc = documents.import_file(here, _pdf(here, "Plan.pdf", pages=1))
    newer = fx.write(conftest.tmpdir("pdoc_newer") / "Plan.pdf", pages=3)
    try:
        documents.import_file(here, newer)
    except documents.DocumentError as exc:
        assert exc.code == "doc_replace" and exc.values["file"] == "Plan.pdf"
    else:
        raise AssertionError("a document of the same name was written over without asking")
    assert len(documents.read(here, doc["id"])["pages"]) == 1, "refused, nothing changed"
    replaced = documents.import_file(here, newer, replace=True)
    assert replaced["id"] == doc["id"] and len(replaced["pages"]) == 3 and replaced["sha256"] == plan.file_hash(newer)
    assert documents.read(here, doc["id"]) == replaced and [d["id"] for d in documents.list_documents(here)] == [doc["id"]]


def test_a_document_written_over_in_imported_plans_is_read_again_by_refresh_all():
    """D-09: a file replaced from outside Woodcore by one of the same name -- its pages and its SHA-256 brought up to date, the rotation of a page it still has kept; nothing changed, nothing written."""
    here = _folders_project("refresh")
    doc = documents.import_file(here, _pdf(here, "Plan.pdf", pages=1))
    documents.write(here, documents.set_rotation(documents.read(here, doc["id"]), 1, 90))
    assert documents.refresh_all(here) == ([], [])
    fx.write(documents.file_path(here, doc), pages=2)
    changed, notes = documents.refresh_all(here)
    assert changed == [doc["id"]] and notes
    fresh = documents.read(here, doc["id"])
    assert len(fresh["pages"]) == 2 and fresh["pages"][0]["rotation"] == 90 and fresh["sha256"] == plan.file_hash(documents.file_path(here, doc))
    assert documents.refresh_all(_project("refresh_before")) == ([], []), "a project laid out before is read as it always was"


def test_a_document_imported_before_is_adopted_into_imported_plans_once():
    """Step 15: a document whose file lies where the engineer keeps it gets a copy in Imported Plans/ and names it; the original stays; adopting twice copies nothing; a file of that name with other bytes there gives the copy the document's id."""
    here = _folders_project("adopt")
    original = _pdf(here, "Grundriss.pdf")
    doc = {"schema_version": "1.0", "id": "D01", "name": "", "file": "01_Pläne/Grundriss.pdf", "kind": "pdf",
           "sha256": plan.file_hash(original), "pages": [{"page": 1, "rotation": 0}], "layers_off": []}
    documents.write(here, doc)
    folder = documents.imported_dir(here, "plan")
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "Grundriss.pdf").write_bytes(b"%PDF-1.7 the engineer's other plan")
    done = documents.adopt(here)
    assert [(p.name, m.name) for p, m in done] == [("D01.json", "Grundriss-D01.pdf")]
    assert documents.read(here, "D01")["file"] == "Plans/Position-plan/Imported Plans/Grundriss-D01.pdf"
    assert original.is_file() and (folder / "Grundriss.pdf").read_bytes() == b"%PDF-1.7 the engineer's other plan"
    assert documents.adopt(here) == []
