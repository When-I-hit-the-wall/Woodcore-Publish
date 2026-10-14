"""The export sheets (v0.114): a plan sheet A0 to A6, `Plans/<id>.typ` at the top of the project's Typst root, on which the position plans are set at a scale beside a legend, a schematic section, texts and a title block -- lib/sheet.typ prints it, calc/sheets.py writes it, calc/typst_objects.py reads and writes each of its objects.

What is held:

* a new sheet **compiles to a PDF of its format** -- A3 landscape, A4 portrait --, its title, the project's name in its title block and the title block's labels in the project's language;
* a plan at **1:100 is drawn at exactly 1:100**, read off the PDF: the architect's page under it is scaled by 1000 mm / (100 · units_per_m) per sheet unit; one given a width is that wide; and the title block names the scale;
* a plan given a scale with no calibration is refused naming the plan, and one given both a scale and a width is refused;
* a section **highlights its storey** -- the red of STE Compact 02 is in the PDF where a storey is named and not where none is --, and a storey the section has no box for is refused naming the boxes it has;
* an edit through calc/sheets.py writes **the canonical form**, between the object's tags and nowhere else: a move, a scale that takes the width away, a resize;
* **a hand edit in the file is read back**, and one Woodcore does not write is refused unless forced;
* the page is the show rule `#show: sheet.with(...)` as an object of its own, read and written like any call;
* lib/sheet.typ and the logo travel with the engine, the PNG byte for byte.

⚠️ Every compiled check is skipped where `typst` is not on the path. Each works on a project of its own -- the example project copied, its engine synced, its plans' record changed where a check needs a calibration or a section -- so nothing the rest of the suite reads changes under it.
"""

import json
import os
import re
import shutil

import conftest
from conftest import ROOT, Skip
import project
import sheets
import typst_objects as to

SAMPLE = ROOT / "tests" / "projet-exemple"
RED = (227, 6, 19)


def _project(name, calibrate=True):
    """A copy of the example project, its engine synced -- Pavillon calibrated at 1:100 of its PDF and Fluchttreppe made a section with a box for «EG» and one for «1.OG» where `calibrate`."""
    root = conftest.tmpdir(name) / "Exemple"
    shutil.copytree(SAMPLE, root, ignore=shutil.ignore_patterns("lib", "VERSION", "stamps", "_Archiv"))
    here = project.Project.load(root / "Exemple.woodcore")
    project.sync_engine(here)
    if calibrate:
        record = here.data_dir / "plans.json"
        data = json.loads(record.read_text(encoding="utf-8"))
        data["plans"]["Pavillon"]["scale"] = {"mode": "ratio", "ratio": 100, "units_per_m": 72 / 0.0254 / 100}
        section = data["plans"]["Fluchttreppe"]
        crop = section["crop"]
        section["role"] = "section"
        section["storey_boxes"] = [
            {"storey": "EG", "x": crop["x"], "y": crop["y"] + crop["h"] / 2, "w": crop["w"], "h": crop["h"] / 4},
            {"storey": "1.OG", "x": crop["x"], "y": crop["y"] + crop["h"] / 4, "w": crop["w"], "h": crop["h"] / 4},
        ]
        record.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return here


def _need_typst():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")


def _compile(here, sheet_id):
    ok, message = sheets.compile(here, sheet_id)
    assert ok, message
    from pypdf import PdfReader
    return PdfReader(str(sheets.pdf(here, sheet_id)))


def _mul(a, b):
    return [a[0] * b[0] + a[1] * b[2], a[0] * b[1] + a[1] * b[3], a[2] * b[0] + a[3] * b[2], a[2] * b[1] + a[3] * b[3],
            a[4] * b[0] + a[5] * b[2] + b[4], a[4] * b[1] + a[5] * b[3] + b[5]]


def _forms(reader):
    """Every form XObject the page draws, as (width of its BBox, horizontal scale it is drawn at) -- the architect's pages under the plans, read off the content stream with the transformation it is drawn under."""
    from pypdf.generic import ContentStream
    page = reader.pages[0]
    xobjects = page["/Resources"].get("/XObject", {})
    ctm, stack, out = [1, 0, 0, 1, 0, 0], [], []
    for operands, op in ContentStream(page.get_contents(), reader).operations:
        if op == b"q":
            stack.append(ctm)
        elif op == b"Q":
            ctm = stack.pop()
        elif op == b"cm":
            ctm = _mul([float(x) for x in operands], ctm)
        elif op == b"Do":
            form = xobjects[operands[0]].get_object()
            if form.get("/Subtype") != "/Form":
                continue
            box = [float(x) for x in form.get("/BBox")]
            matrix = _mul([float(x) for x in form.get("/Matrix", [1, 0, 0, 1, 0, 0])], ctm)
            out.append((box[2] - box[0], matrix[0]))
    return out


def _colours(reader):
    """Every colour a stream of the PDF sets, as 0-255 triples."""
    found = set()
    size = int(reader.trailer["/Size"])
    for number in range(1, size):
        try:
            obj = reader.get_object(number)
            data = obj.get_data() if hasattr(obj, "get_data") else None
        except Exception:
            continue
        if not data:
            continue
        for m in re.finditer(rb"([\d.]+) ([\d.]+) ([\d.]+) (?:rg|RG|scn|SCN|sc|SC)\b", data):
            found.add(tuple(round(float(x) * 255) for x in m.groups()))
    return found


# --- where a sheet lives, and its name ------------------------------------------------------------------

def test_a_sheet_lives_in_plans_at_the_typst_root_and_is_numbered_b01_b02():
    here = _project("sheets_where", calibrate=False)
    assert sheets.folder(here) == here.typst_root / "Plans"
    assert sheets.list_sheets(here) == [] and sheets.new_id(here) == "B01"
    first = sheets.new_sheet(here)
    assert first == here.typst_root / "Plans" / "B01.typ" and first.is_file()
    assert sheets.new_id(here) == "B02"
    sheets.new_sheet(here, "Dach")
    assert sheets.list_sheets(here) == ["B01", "Dach"]
    for bad, code in (("B01", "exists"), ("b01", "exists"), ("x/y", "bad_id"), ("", "bad_id")):
        try:
            sheets.new_sheet(here, bad)
        except sheets.SheetError as exc:
            assert exc.code == code, (bad, exc.code)
        else:
            raise AssertionError(f"{bad!r} was taken")
    try:
        sheets.new_sheet(here, "B09", format="B4")
    except sheets.SheetError as exc:
        assert exc.code == "bad_format"
    else:
        raise AssertionError("a format B4 was taken")
    archived = sheets.archive(here, "Dach")
    assert archived.parent == sheets.folder(here) / "archives" and archived.is_file()
    assert sheets.list_sheets(here) == ["B01"]


def test_a_new_sheet_is_canonical_and_says_its_paper():
    """Every object Woodcore writes is in the form it reads back, and the page states its format, its orientation and its margin -- defaults or not (written first through the model, the page came out `#show: sheet.with()`, saying nothing of its paper)."""
    here = _project("sheets_canonical", calibrate=False)
    text = sheets.read(here, sheets.new_sheet(here, format="A4", landscape=False).stem)
    found, problems = to.scan(text)
    assert not problems, problems
    assert [o.type for o in found] == ["sheet-page", "sheet-text", "sheet-text", "sheet-titleblock"]
    assert all(o.state == "canonical" for o in found), [(o.id, o.state, o.diff()) for o in found]
    assert '#show: sheet.with(\n  format: "A4",\n  landscape: false,\n  margin: 10mm,\n  kind: "position",\n)' in text
    assert text.startswith("// Export sheet") and '#import "/commands.typ": *' in text
    page = sheets.page(here, "B01")
    assert page.size() == (210, 297)
    # the remark stands above the title block on a sheet too narrow to put it beside
    remark = sheets.model(here, "B01", "remark")
    assert remark.position() == (20.0, 297 - 10 - 43 - 25)


# --- the PDF -------------------------------------------------------------------------------------------

def test_a_new_sheet_compiles_to_its_format_with_its_title_and_the_projects_name():
    _need_typst()
    here = _project("sheets_compile", calibrate=False)
    sheets.new_sheet(here, title="Positionsplan Erdgeschoss")
    reader = _compile(here, "B01")
    box = reader.pages[0].mediabox
    assert len(reader.pages) == 1
    assert abs(float(box.width) - 420 / 25.4 * 72) < 0.5 and abs(float(box.height) - 297 / 25.4 * 72) < 0.5, box
    text = reader.pages[0].extract_text()
    for words in ("Positionsplan Erdgeschoss", "Exemple", "Bemerkung", "Bauherrschaft", "Plan-Nr.", "B01", "420 × 297 mm", "Max Muster", "25.09.2026"):
        assert words in text, (words, text)
    sheets.set_page(here, "B01", format="A4", landscape=False)
    box = _compile(here, "B01").pages[0].mediabox
    assert abs(float(box.width) - 210 / 25.4 * 72) < 0.5 and abs(float(box.height) - 297 / 25.4 * 72) < 0.5, box


def test_a_plan_at_1_100_is_drawn_at_1_100_and_the_title_block_names_the_scale():
    """The architect's page under the plan is drawn at s = 1000 mm / (n · units_per_m) per sheet unit -- 1 pt per pt at 1:100 of a PDF drawn at 1:100 --, so the plan's crop is crop.w · s wide; a plan given a width is that wide, crop.w · s = width."""
    _need_typst()
    here = _project("sheets_scale")
    sheets.new_sheet(here)
    sheets.add_viewport(here, "B01", "Pavillon", 20, 35, scale=100)
    sheets.add_viewport(here, "B01", "Velo-Unterstand", 230, 35, width=150)
    reader = _compile(here, "B01")
    plans = json.loads((here.data_dir / "plans.json").read_text(encoding="utf-8"))["plans"]
    pt = 72 / 25.4
    expected = {
        round(plans["Pavillon"]["sheet"]["width"], 1): 1000 / (100 * plans["Pavillon"]["scale"]["units_per_m"]) * pt,
        round(plans["Velo-Unterstand"]["sheet"]["width"], 1): 150 * pt / plans["Velo-Unterstand"]["crop"]["w"],
    }
    seen = {}
    for width, scale in _forms(reader):
        seen.setdefault(round(width, 1), scale)
    for width, scale in expected.items():
        assert width in seen, (width, seen)
        assert abs(seen[width] - scale) < 1e-3, (width, seen[width], scale)
    # the printed width of the Pavillon at 1:100: its crop in metres, a hundredth of it
    assert abs(plans["Pavillon"]["crop"]["w"] * seen[round(plans["Pavillon"]["sheet"]["width"], 1)] / pt - plans["Pavillon"]["crop"]["w"] / plans["Pavillon"]["scale"]["units_per_m"] * 10) < 0.01
    text = reader.pages[0].extract_text()
    assert "1:100" in text and "Massstab" in text, text


def test_a_plan_on_a_sheet_carries_its_scale_bar_when_asked():
    """Issue #9: ticking «Barre d'échelle» on a sheet's plan stopped the sheet compiling -- `plan-scale-bar` measured its labels outside any `context`, which `show-plan`'s `layout` gave it and `sheet-viewport` did not. The bar now carries its own context: the sheet compiles and prints the bar's metres under the plan."""
    _need_typst()
    here = _project("sheets_scale_bar")
    sheets.new_sheet(here)
    oid = sheets.add_viewport(here, "B01", "Pavillon", 20, 35, scale=100)
    assert not re.search(r"^0\b.*\bm$", _compile(here, "B01").pages[0].extract_text(), re.M), "no bar unasked"
    model = sheets.model(here, "B01", oid)
    model.set_scale_bar(True)
    sheets.set_object(here, "B01", oid, model)
    text = _compile(here, "B01").pages[0].extract_text()
    assert re.search(r"^0\b.*\bm$", text, re.M), text


def test_a_plan_on_a_sheet_shows_its_dimensions_and_lengths_unless_told_not_to():
    """Issue #9 (REQ-011, REQ-012): `dimensions: false` and `lengths: false` take out what the drawing writes between their markers -- the view «Export» says it per sheet, as `axes:`."""
    _need_typst()
    here = _project("sheets_dimensions")
    overlay = here.data_dir / json.loads((here.data_dir / "plans.json").read_text(encoding="utf-8"))["plans"]["Pavillon"]["overlay"]
    svg = overlay.read_text(encoding="utf-8")
    marks = ('<!-- dimensions --><text x="20" y="40" font-size="30">DIMTEXT</text><!-- /dimensions -->'
             '<!-- lengths --><text x="20" y="90" font-size="30">LENTEXT</text><!-- /lengths -->')
    overlay.write_text(svg.replace("</svg>", marks + "</svg>"), encoding="utf-8")
    sheets.new_sheet(here)
    oid = sheets.add_viewport(here, "B01", "Pavillon", 20, 35, scale=100)
    text = _compile(here, "B01").pages[0].extract_text()
    assert "DIMTEXT" in text and "LENTEXT" in text, text
    model = sheets.model(here, "B01", oid)
    model.set_dimensions(False)
    model.set_lengths(False)
    sheets.set_object(here, "B01", oid, model)
    assert "dimensions: false" in sheets.read(here, "B01") and "lengths: false" in sheets.read(here, "B01")
    text = _compile(here, "B01").pages[0].extract_text()
    assert "DIMTEXT" not in text and "LENTEXT" not in text, text


def test_a_scale_needs_a_calibration_and_one_size_only():
    _need_typst()
    here = _project("sheets_refusals")
    sheets.new_sheet(here)
    oid = sheets.add_viewport(here, "B01", "Geratehaus", 20, 35, scale=100)
    ok, message = sheets.compile(here, "B01")
    assert not ok and "Geratehaus" in conftest.panic_message(message) and "calibrate" in message, message
    sheets.set_width(here, "B01", oid, 120)
    assert sheets.compile(here, "B01")[0]
    text = sheets.read(here, "B01").replace("  width: 120mm,\n", "  scale: 50,\n  width: 120mm,\n")
    sheets.write(here, "B01", text)
    ok, message = sheets.compile(here, "B01")
    assert not ok and "not both" in conftest.panic_message(message), message


def test_a_section_highlights_its_storey_and_refuses_one_it_has_no_box_for():
    _need_typst()
    here = _project("sheets_section")
    sheets.new_sheet(here)
    oid = sheets.add_section(here, "B01", "Fluchttreppe", None, 300, 30, width=80)
    assert RED not in _colours(_compile(here, "B01")), "a section with no storey named is drawn in red"
    model = sheets.model(here, "B01", oid)
    model.set_storey("EG")
    sheets.set_object(here, "B01", oid, model)
    reader = _compile(here, "B01")
    assert RED in _colours(reader)
    assert "Schematischer Schnitt" in reader.pages[0].extract_text()
    model.set_storey("DG")
    sheets.set_object(here, "B01", oid, model)
    ok, message = sheets.compile(here, "B01")
    panic = conftest.panic_message(message)
    assert not ok and "DG" in panic and "EG, 1.OG" in panic, message


def test_the_legend_lists_the_symbols_of_the_sheets_plans_once():
    _need_typst()
    here = _project("sheets_legend")
    sheets.new_sheet(here)
    sheets.add_viewport(here, "B01", "Pavillon", 20, 35, scale=100)
    sheets.add_viewport(here, "B01", "Geratehaus", 230, 35, width=120)
    sheets.add_legend(here, "B01", 230, 150, width=150)
    text = _compile(here, "B01").pages[0].extract_text()
    assert text.count("Stütze") == 1 and "Legende" in text, text


# --- editing the file ----------------------------------------------------------------------------------

def test_an_edit_writes_the_canonical_form_between_the_tags_and_nowhere_else():
    here = _project("sheets_edit", calibrate=False)
    sheets.new_sheet(here)
    oid = sheets.add_viewport(here, "B01", "Pavillon", 20, 35, width=100)
    assert oid == "viewport-pavillon"
    before = sheets.read(here, "B01")
    sheets.move(here, "B01", oid, 42.5, 50)
    after = sheets.read(here, "B01")
    obj = to.find(after, oid)
    assert obj.state == "canonical" and obj.model().position() == (42.5, 50.0)
    begin, finish = to.find(before, oid).body_span
    assert after[:begin] == before[:begin] and after[obj.body_span[1]:] == before[finish:]
    # a scale takes the width away, a width the scale: a drawing has one size
    sheets.set_scale(here, "B01", oid, 200)
    m = sheets.model(here, "B01", oid)
    assert m.get("scale") == 200 and m.get("width") is None
    sheets.resize(here, "B01", oid, 2)
    assert sheets.model(here, "B01", oid).get("scale") == 100
    sheets.set_width(here, "B01", oid, 90)
    m = sheets.model(here, "B01", oid)
    assert m.get("scale") is None and to.mm_of(m.get("width")) == 90
    sheets.resize(here, "B01", oid, 1.5)
    assert to.mm_of(sheets.model(here, "B01", oid).get("width")) == 135
    for found in sheets.objects(here, "B01"):
        assert found.state == "canonical", (found.id, found.diff())
    text_id = sheets.add_text(here, "B01", 20, 25, "Wände EG, Decke über EG (Mst. 1:100)", size=12)
    assert sheets.model(here, "B01", text_id).get("body") == to.Content("Wände EG, Decke über EG (Mst. 1:100)")
    sheets.remove(here, "B01", text_id)
    assert to.find(sheets.read(here, "B01"), text_id) is None


def test_a_hand_edit_in_the_file_is_read_back_and_not_overwritten_unasked():
    here = _project("sheets_hand", calibrate=False)
    sheets.new_sheet(here)
    oid = sheets.add_viewport(here, "B01", "Pavillon", 20, 35, width=100)
    text = sheets.read(here, "B01")
    # as VS Code saves it: another place, in the canonical form -- read back as it stands
    sheets.write(here, "B01", text.replace("  x: 20mm,\n  y: 35mm,\n  width: 100mm,", "  x: 2.5cm,\n  y: 35mm,\n  width: 100mm,").replace("\n", "\r\n"))
    m = sheets.model(here, "B01", oid)
    assert m.position() == (25.0, 35.0)
    assert sheets.find(here, "B01", oid).state == "canonical"
    # a comment is no part of Woodcore's form: the object is hand-edited, and written over only once that is said
    text = sheets.read(here, "B01").replace("  y: 35mm,\r\n", "  y: 35mm, // under the title\r\n")
    sheets.write(here, "B01", text)
    assert sheets.find(here, "B01", oid).state == "hand_edited"
    try:
        sheets.move(here, "B01", oid, 30, 40)
    except to.ObjectError as exc:
        assert exc.code == "hand_edited"
    else:
        raise AssertionError("a hand-edited object was overwritten unasked")
    sheets.set_object(here, "B01", oid, sheets.model(here, "B01", oid), force=True)
    written = sheets.read(here, "B01")
    assert sheets.find(here, "B01", oid).state == "canonical" and "\r\n" in written and "under the title" not in written


def test_the_page_is_a_show_rule_read_and_written_as_a_call():
    text = '#show: sheet.with(\n  format: "A2",\n  landscape: false,\n  margin: 8mm,\n)'
    call = to.parse_call(text)
    assert call.type == "sheet-page" and call.args["format"] == "A2" and to.serialize(call) == text
    assert to.serialize(to.Call("sheet-page", {})) == "#show: sheet.with()"
    found = to.objects(f"// woodcore:object sheet-page page\n{text}\n// woodcore:/object page\n")
    assert found[0].state == "canonical" and found[0].model().size() == (420, 594)
    # a show rule of another function is no sheet
    try:
        to.parse_call("#show: conf.with(x: 1)")
    except to.ParseError:
        pass
    else:
        raise AssertionError("#show: conf.with(...) was read as a call")


def test_every_sheet_object_reads_back_its_default_and_its_model():
    for kind in to.SHEET_TYPES:
        call = to.default_call(kind)
        text = to.serialize(call)
        assert to.serialize(to.parse_call(text)) == text, kind
        assert to.serialize(to.model_for(call).to_call()) == text, kind
    block = to.TitleBlockModel(to.Call("sheet-titleblock", {}))
    block.set_cell("architect", "Muster Architekten AG")
    block.set_cell("object", to.AUTO)
    block.move_to(to.AUTO, to.AUTO)
    assert to.serialize(block.to_call()) == '#sheet-titleblock(\n  architect: [Muster Architekten AG],\n)'
    for bad in (lambda: block.set_cell("architect", to.AUTO), lambda: block.set_cell("colour", "red")):
        try:
            bad()
        except to.ModelError:
            pass
        else:
            raise AssertionError("the title block took a cell it has not")


def test_the_formats_are_lib_sheets_own():
    text = (ROOT / "lib" / "sheet.typ").read_text(encoding="utf-8")
    block = re.search(r"#let sheet-formats = \((.*?)\n\)", text, re.S).group(1)
    found = {name: (int(a), int(b)) for name, a, b in re.findall(r"(A\d): \((\d+), (\d+)\)", block)}
    assert found == to.SHEET_SIZES and tuple(found) == to.SHEET_FORMATS


# --- the engine --------------------------------------------------------------------------------------

def test_lib_sheet_and_its_logo_travel_with_the_engine_byte_for_byte():
    """sync_engine copies bytes: the PNG of the title block arrives as it is in lib/assets/, which is what a project's sheet prints from."""
    assert "lib/sheet.typ" in project.ENGINE_FILES and "lib/assets/logo-bfh.png" in project.ENGINE_FILES
    here = _project("sheets_engine", calibrate=False)
    copied = here.generated_dir / "lib" / "assets" / "logo-bfh.png"
    assert copied.read_bytes() == (ROOT / "lib" / "assets" / "logo-bfh.png").read_bytes()
    assert project.engine_state(here)[0] == "current"
    import sys
    sys.path.insert(0, str(ROOT / "calc" / "tools"))
    import build_reference as ref
    assert "sheet.typ" in ref.LIB_FILES
    names = dict(ref.CATEGORIES)["sheets"]
    assert set(names) == {"sheet", "sheet-text", "sheet-viewport", "sheet-fire-viewport", "sheet-section", "sheet-legend", "sheet-fire-legend", "sheet-titleblock", "sheet-position-list", "sheet-quantities"}
    formula = (ROOT / "lib" / "formula.typ").read_text(encoding="utf-8")
    assert re.search(r'#import "sheet\.typ": sheet, sheet-fire-legend, sheet-fire-viewport, sheet-legend, sheet-position-list, sheet-quantities, sheet-section, sheet-text, sheet-titleblock, sheet-viewport', formula)   # relative on purpose: lib/formula.typ's own import of its sibling, read and never written


def test_the_title_block_and_the_legend_speak_the_reports_language():
    from i18n import strings
    for key in ("object", "element", "client", "architect", "phase", "project_number", "plan_number", "index", "revision_date",
                "revision_author", "modification", "drawn_by", "scale", "date", "size", "legend", "section", "scale_short", "position_plan", "remark"):
        for lang in ("de", "fr", "en"):
            assert strings.text("sheet." + key, lang).strip(), (key, lang)
    assert "ß" not in "".join(strings.text("sheet." + k, "de") for k in ("client", "drawn_by", "size"))


# --- a sheet's kind (v0.116) -------------------------------------------------------------------------

def test_a_sheet_is_of_one_kind_said_by_its_page_or_read_off_its_objects():
    """Position plans and fire-protection plans are never on one sheet (the engineer, 06.10.2026): a new sheet's page says its kind, one written before v0.116 has it read off its objects -- any fire object makes it a fire sheet, the first plan put on a sheet that holds none deciding --, an object of the other kind is refused, and the sheets are listed per kind."""
    here = _project("sheets_kind", calibrate=False)
    sheets.new_sheet(here, "P1")
    sheets.new_sheet(here, "F1", kind="fire")
    assert sheets.sheet_kind(here, "P1") == "position" and sheets.sheet_kind(here, "F1") == "fire"
    assert "Brandschutzplan" in sheets.read(here, "F1"), "a fire sheet's own title, in the project's language"
    for sid, kind, other in (("P1", "sheet-viewport", "sheet-fire-viewport"), ("F1", "sheet-fire-viewport", "sheet-viewport")):
        try:
            sheets.add_object(here, sid, other, to.default_call(other))
        except sheets.SheetError as exc:
            assert exc.code == "wrong_kind", exc
        else:
            raise AssertionError(f"{other} was put on a {sheets.sheet_kind(here, sid)} sheet")
        sheets.add_object(here, sid, kind, to.default_call(kind))
    # a sheet written before v0.116: no kind on its page, its objects say it
    for sid, kind in (("Old", "sheet-fire-viewport"), ("Older", "sheet-viewport"), ("Blank", None)):
        sheets.new_sheet(here, sid)
        text = sheets.read(here, sid).replace('  kind: "position",\n', "")
        sheets.write(here, sid, text)
        assert sheets.declared_kind(text) is None
        if kind:
            sheets.add_object(here, sid, kind, to.default_call(kind))      # the first plan decides
    assert sheets.sheet_kind(here, "Old") == "fire" and sheets.sheet_kind(here, "Older") == "position" and sheets.sheet_kind(here, "Blank") == "position"
    assert sheets.list_sheets(here, kind="fire") == ["F1", "Old"]
    assert sheets.list_sheets(here, kind="position") == ["Blank", "Older", "P1"]
    try:
        sheets.list_sheets(here, kind="both")
    except sheets.SheetError as exc:
        assert exc.code == "bad_kind"
    else:
        raise AssertionError("a kind that is not one was taken")


def test_a_plan_on_a_sheet_is_headed_by_its_name_description_storey_and_scale():
    """The line above a plan, as STE heads each plan of a plan de positions: «Nom — description, étage (éch. 1:n)» -- the plan's name, description and storey from Woodcore, its printed scale --; `title: none` leaves it out, and a plan with neither name nor description is named by its id."""
    _need_typst()
    here = _project("sheets_title")
    record = here.data_dir / "plans.json"
    data = json.loads(record.read_text(encoding="utf-8"))
    data["plans"]["Pavillon"].update(name="École", label="Rez", storey="EG")
    data["plans"]["Velo-Unterstand"].update(name="", label="")
    record.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    sheets.new_sheet(here)
    sheets.add_viewport(here, "B01", "Pavillon", 20, 35, scale=100)
    sheets.add_viewport(here, "B01", "Velo-Unterstand", 230, 35, width=150)
    text = _compile(here, "B01").pages[0].extract_text()
    assert "École — Rez, EG (Mst. 1:100)" in text, text
    assert re.search(r"^Velo-Unterstand\s*$", text, re.M), "named by its id, and no scale where the plan has none"
    m = sheets.model(here, "B01", "viewport-pavillon")
    m.set_title(None)
    sheets.set_object(here, "B01", "viewport-pavillon", m)
    assert "title: none" in sheets.read(here, "B01")
    text = _compile(here, "B01").pages[0].extract_text()
    assert "École" not in text, text


# --- the PDF bundles (v0.116) ------------------------------------------------------------------------

def test_a_bundle_keeps_its_sheets_in_order_and_refuses_what_it_cannot_hold():
    here = _project("sheets_bundles", calibrate=False)
    for sid in ("B01", "B02", "B03"):
        sheets.new_sheet(here, sid)
    sheets.new_sheet(here, "F01", kind="fire")
    made = sheets.create_bundle(here, "Plans Rez", sheets=["B02", "B01"])
    assert made == {"name": "Plans Rez", "kind": "position", "sheets": ["B02", "B01"]}
    data = json.loads(sheets.bundles_path(here).read_text(encoding="utf-8"))
    assert data["format"] == "woodcore-sheet-bundles" and data["schema_version"] == "1.1"   # 1.1 since v0.117: id, description, storey
    assert sheets.add_to_bundle(here, "plans rez", "B03", index=0)["sheets"] == ["B03", "B02", "B01"], "case ignored, inserted where asked"
    assert sheets.set_bundle_sheets(here, "Plans Rez", ["B01", "B02", "B03"])["sheets"] == ["B01", "B02", "B03"]
    assert sheets.remove_from_bundle(here, "Plans Rez", ["B02"])["sheets"] == ["B01", "B03"]
    assert sheets.list_sheets(here) == ["B01", "B02", "B03", "F01"], "a bundle's file is no sheet"
    for action, code in ((lambda: sheets.add_to_bundle(here, "Plans Rez", "F01"), "wrong_kind"),
                         (lambda: sheets.create_bundle(here, "B01"), "bundle_exists"),
                         (lambda: sheets.create_bundle(here, "plans rez"), "bundle_exists"),
                         (lambda: sheets.create_bundle(here, "a/b"), "bad_bundle_name"),
                         (lambda: sheets.create_bundle(here, "Feuilles. "), "bad_bundle_name"),
                         (lambda: sheets.add_to_bundle(here, "Plans Rez", "B99"), "no_sheet"),
                         (lambda: sheets.bundle(here, "Nowhere"), "no_bundle"),
                         (lambda: sheets.new_sheet(here, "Plans Rez"), "bad_id")):
        try:
            action()
        except sheets.SheetError as exc:
            assert exc.code == code, (code, exc.code, exc)
        else:
            raise AssertionError(f"not refused: {code}")
    sheets.create_bundle(here, "Feu", kind="fire", sheets=["F01"])
    assert [b["name"] for b in sheets.list_bundles(here, kind="fire")] == ["Feu"]
    assert sheets.rename_bundle(here, "Feu", "Brandschutz")["name"] == "Brandschutz"
    sheets.delete_bundle(here, "Brandschutz")
    assert [b["name"] for b in sheets.list_bundles(here)] == ["Plans Rez"]
    # a sheet archived leaves the bundles that held it
    sheets.archive(here, "B03")
    assert sheets.bundle(here, "Plans Rez")["sheets"] == ["B01"]
    # a file of bundles written wrong is refused, never overwritten, and stops no sheet from being made
    sheets.bundles_path(here).write_text('{"format": "something else"}', encoding="utf-8")
    try:
        sheets.list_bundles(here)
    except sheets.SheetError as exc:
        assert exc.code == "bad_bundles"
    else:
        raise AssertionError("a broken file of bundles was read")
    assert sheets.new_sheet(here).stem == "B03", "the number B03 left free by the archive is given again"


def test_a_bundle_is_exported_as_one_pdf_its_sheets_pages_in_its_order_each_sheet_keeping_its_own():
    _need_typst()
    from pypdf import PdfReader
    here = _project("sheets_bundle_export", calibrate=False)
    sheets.new_sheet(here, "B01", title="Erste Seite")
    sheets.new_sheet(here, "B02", format="A4", landscape=False, title="Zweite Seite")
    sheets.create_bundle(here, "Dossier", sheets=["B02", "B01"])
    ok, message = sheets.export_bundle(here, "Dossier")
    assert ok, message
    assert sheets.pdf(here, "B01").is_file() and sheets.pdf(here, "B02").is_file(), "each sheet keeps its own PDF"
    merged = PdfReader(str(sheets.bundle_pdf(here, "Dossier")))
    assert sheets.bundle_pdf(here, "Dossier") == here.typst_root / "Plans" / "Dossier.pdf"
    assert len(merged.pages) == 2
    assert "Zweite Seite" in merged.pages[0].extract_text() and "Erste Seite" in merged.pages[1].extract_text()
    assert abs(float(merged.pages[0].mediabox.width) - 210 / 25.4 * 72) < 0.5, "the A4 portrait sheet first, as the bundle orders them"
    # a bundle naming a sheet there is not is refused by name
    sheets.archive(here, "B01")
    data = json.loads(sheets.bundles_path(here).read_text(encoding="utf-8"))
    data["bundles"][0]["sheets"].append("B01")
    sheets.bundles_path(here).write_text(json.dumps(data), encoding="utf-8")
    try:
        sheets.export_bundle(here, "Dossier")
    except sheets.SheetError as exc:
        assert exc.code == "missing_sheet" and "B01" in str(exc)
    else:
        raise AssertionError("a bundle naming a sheet that is gone was exported")


def test_a_bundle_states_its_id_description_and_storey_or_takes_them_from_its_first_plan():
    """Bundles 1.1 (v0.117, spec 2026-10-07-performance-erreurs-plans-legendes, REQ-016, D9): the engineer, 07.10.2026: «on doit pouvoir modifier le nom, la description, l'étage, l'id du document. Par défaut, les valeurs sont reprises automatiquement lors de l'import dessus du premier plan.» An id distinct from the name names the PDF; a field not stated is the first plan's, read and never copied; a 1.0 file is read as it is."""
    import json
    import sheets
    here = _project("sheets-bundle-fields")
    sid = sheets.new_sheet(here).stem
    sheets.create_bundle(here, "Dossier", sheets=[sid])
    entry = sheets.bundle(here, "Dossier")
    empty = sheets.bundle_fields(here, entry)
    assert empty["id"] == "Dossier" and all(empty["derived"].values()), "no plan on the sheet: the name names the PDF, as in 1.0"
    sheets.add_viewport(here, sid, "Pavillon", 20, 20)   # the first plan put on it
    fields = sheets.bundle_fields(here, sheets.bundle(here, "Dossier"))
    plan = json.loads((here.plans_dir / "Pavillon.json").read_text(encoding="utf-8"))
    assert fields["id"] == "Pavillon" and fields["derived"]["id"], "the first plan's id, read and not copied"
    assert fields["storey"] == (plan.get("storey") or "") and fields["description"] == (plan.get("label") or "")
    assert "id" not in sheets.bundle(here, "Dossier"), "nothing written by reading"
    sheets.set_bundle_field(here, "Dossier", "id", "E01")
    sheets.set_bundle_field(here, "Dossier", "description", "Plans de l'étage")
    record = sheets.bundle(here, "Dossier")
    assert record["id"] == "E01" and sheets.bundle_pdf(here, "Dossier").name == "E01.pdf"
    fields = sheets.bundle_fields(here, record)
    assert fields["description"] == "Plans de l'étage" and not fields["derived"]["description"]
    sheets.set_bundle_field(here, "Dossier", "description", "")
    assert "description" not in sheets.bundle(here, "Dossier"), "emptied: the plan's again"
    for bad in (sid, "a/b"):
        try:
            sheets.set_bundle_field(here, "Dossier", "id", bad)
        except sheets.SheetError as exc:
            assert exc.code in ("bundle_exists", "bad_bundle_name")
        else:
            raise AssertionError(f"{bad!r} was taken as an id")
    # a 1.0 file is read as it is
    path = sheets.bundles_path(here)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["schema_version"] = "1.0"
    data["bundles"] = [{k: v for k, v in b.items() if k in ("name", "kind", "sheets")} for b in data["bundles"]]
    path.write_text(json.dumps(data), encoding="utf-8")
    assert sheets.list_bundles(here)[0]["name"] == "Dossier"
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == "1.0", "read, never written"
