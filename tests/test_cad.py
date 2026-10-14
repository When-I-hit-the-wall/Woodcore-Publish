"""A CAD drawing as a plan's background: read with ezdxf, a DWG converted by the ODA File Converter (v0.114, calc/domains/cad.py, docs/domain/position-plans.md §3.3sexies).

Every drawing here is built by ezdxf in the test, so the file runs on a clone with no drawing of the engineer's: two layers in the model space -- walls (W) and dimensions (B) --, a paper-space layout with a viewport, and an empty layout. A DWG cannot be written without the converter, so its path is held with the converter mocked; the one real run needs an ODA File Converter on the machine and is skipped where there is none.
"""

import os
import re
from pathlib import Path

import conftest
from domains import cad


def _drawing(name="drawing"):
    """A DXF of two layers -- `W` lines and a text, `B` a line and a circle -- a third, `OFF`, switched off in the file and one `FROZEN` frozen, a paper-space layout `Plan 1` with a viewport, and an empty layout `Leer`. Returns its path."""
    import ezdxf
    folder = conftest.tmpdir(f"cad_{name}")
    doc = ezdxf.new(units=4)
    doc.layers.add("W")
    doc.layers.add("B")
    doc.layers.add("OFF").off()
    doc.layers.add("FROZEN").freeze()
    msp = doc.modelspace()
    msp.add_line((0, 0), (10000, 0), dxfattribs={"layer": "W"})
    msp.add_line((10000, 0), (10000, 6000), dxfattribs={"layer": "W"})
    msp.add_text("Wand", height=300, dxfattribs={"layer": "W"}).set_placement((1000, 1000))
    msp.add_line((0, 6000), (10000, 6000), dxfattribs={"layer": "B"})
    msp.add_circle((5000, 3000), 800, dxfattribs={"layer": "B"})
    msp.add_line((0, 3000), (2000, 3000), dxfattribs={"layer": "OFF"})
    msp.add_line((0, 4000), (2000, 4000), dxfattribs={"layer": "FROZEN"})
    sheet = doc.layouts.new("Plan 1")
    sheet.page_setup(size=(420, 297), margins=(10, 10, 10, 10), units="mm")
    sheet.add_line((20, 20), (400, 20), dxfattribs={"layer": "B"})
    sheet.add_viewport(center=(210, 148), size=(380, 250), view_center_point=(5000, 3000), view_height=7000)
    doc.layouts.new("Leer")
    path = folder / "drawing.dxf"
    doc.saveas(path)
    return path


def _paths(svg):
    return len(re.findall(r"<path\b", svg))


def test_the_pages_are_the_model_then_the_layouts_in_tab_order():
    path = _drawing("pages")
    names = cad.layouts(path)
    assert names[0] == "Model", names
    assert names.index("Plan 1") < names.index("Leer"), names


def test_the_layers_say_what_the_file_shows():
    path = _drawing("layers")
    states = {layer["name"]: layer for layer in cad.layers(path)}
    assert states["W"]["on"] and not states["W"]["frozen"]
    assert not states["OFF"]["on"]
    assert states["FROZEN"]["frozen"]
    assert set(cad.default_off(path)) == {"OFF", "FROZEN"}


def test_a_layer_switched_off_takes_its_geometry_away_and_leaves_the_frame():
    """The engineer's «turn the dimensions off»: a layer off draws nothing -- and the frame does not move, or every plan drawn on the drawing would slide off the architecture. ⚠️ That second half is what a first version got wrong: ezdxf fits the page to what it drew, so switching `W` off shrank it (cad.render_svg's note)."""
    path = _drawing("off")
    full, w, h = cad.render_svg(path, "Model")
    without_b, w2, h2 = cad.render_svg(path, "Model", ["b"])  # a layer's name compares without regard to case
    without_w, w3, h3 = cad.render_svg(path, "Model", ["W"])
    assert (w, h) == (w2, h2) == (w3, h3), "the frame moved when a layer was switched off"
    assert _paths(without_b) < _paths(full) and _paths(without_w) < _paths(full)
    assert _paths(without_b) != _paths(without_w)
    # a layer the file switched off is shown when the document does not name it: what is shown is the document's choice
    everything, *_ = cad.render_svg(path, "Model", [])
    off_and_frozen, *_ = cad.render_svg(path, "Model", ["OFF", "FROZEN"])
    assert _paths(everything) > _paths(off_and_frozen)


def test_the_sheet_is_in_hundredths_of_a_millimetre():
    path = _drawing("units")
    text, width, height = cad.render_svg(path, "Model")
    mm = re.search(r'width="([0-9.]+)mm" height="([0-9.]+)mm"', text)
    assert mm, text[:200]
    assert abs(width - cad.UNITS_PER_MM * float(mm.group(1))) <= 1 and abs(height - cad.UNITS_PER_MM * float(mm.group(2))) <= 1
    assert max(float(mm.group(1)), float(mm.group(2))) <= cad.MODEL_PAGE_MM + 1e-6, "the model space is fitted onto a page no longer than an A1"
    paper, pw, ph = cad.render_svg(path, "Plan 1")
    assert 'width="420mm"' in paper and 'height="297mm"' in paper, paper[:200]
    assert (pw, ph) == (42000.0, 29700.0)


def test_an_empty_layout_is_a_blank_page_of_its_paper():
    path = _drawing("empty")
    text, width, height = cad.render_svg(path, "Leer")
    assert "<path" not in text and width > 0 and height > 0


def test_an_unknown_layout_is_refused_by_its_code():
    path = _drawing("unknown")
    try:
        cad.render_svg(path, "Keines")
    except cad.CadError as exc:
        assert exc.code == "no_layout" and exc.values["layout"] == "Keines"
    else:
        assert False, "a layout the drawing has not was drawn"


def test_qtsvg_and_typst_read_the_drawing():
    """ezdxf writes its colours as CSS classes in a <style>; QtSvg (SVG Tiny, the window) and Typst (the report) both read them -- held by rendering, not by trust."""
    path = _drawing("qt")
    text, width, height = cad.render_svg(path, "Model")
    from PySide6.QtCore import QByteArray
    from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    QGuiApplication.instance() or QGuiApplication([])
    renderer = QSvgRenderer(QByteArray(text.encode("utf-8")))
    assert renderer.isValid()
    image = QImage(400, 400, QImage.Format_ARGB32)
    image.fill(QColor("white"))
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    dark = sum(1 for y in range(0, 400, 2) for x in range(0, 400, 2) if QColor(image.pixel(x, y)).lightness() < 128)
    assert dark > 20, "QtSvg drew nothing of the drawing"
    if not conftest.have_typst():
        return
    import subprocess
    folder = path.parent
    (folder / "d.svg").write_text(text, encoding="utf-8")
    (folder / "d.typ").write_text('#set page(width: 200mm, height: 200mm, margin: 0pt)\n#image("d.svg", width: 100%)\n', encoding="utf-8")
    result = subprocess.run(["typst", "compile", str(folder / "d.typ"), str(folder / "d.png"), "--ppi", "20"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_the_newest_oda_converter_is_found():
    root = conftest.tmpdir("cad_oda")
    for version in ("ODAFileConverter 25.4.0", "ODAFileConverter 26.10.0", "ODAFileConverter 26.2.0"):
        folder = root / "ODA" / version
        folder.mkdir(parents=True)
        (folder / "ODAFileConverter.exe").write_bytes(b"")
    found = cad.oda_converter([str(root)])
    assert found.parent.name == "ODAFileConverter 26.10.0", found
    assert cad.oda_converter([str(conftest.tmpdir("cad_oda_none"))]) is None


def test_a_dwg_without_the_converter_says_where_to_download_it():
    dwg = conftest.tmpdir("cad_dwg_missing") / "Plan.dwg"
    dwg.write_bytes(b"AC1032")
    original = cad.oda_converter
    cad.oda_converter = lambda program_files=None: None
    try:
        cad.convert_dwg(dwg, dwg.with_suffix(".dxf"))
    except cad.CadError as exc:
        assert exc.code == "oda_missing" and exc.values["url"] == cad.ODA_URL and cad.ODA_URL in str(exc)
    else:
        assert False, "a DWG was converted with no converter"
    finally:
        cad.oda_converter = original


def test_a_dwg_is_converted_through_proc_without_a_console():
    """The converter is a console program run from a window: it goes through calc/proc.py (tests/test_no_console.py), with the input folder, the output folder, the version, DXF, no recursion, an audit and the drawing's own name as its filter."""
    import proc
    folder = conftest.tmpdir("cad_dwg_convert")
    dwg = folder / "Plan.dwg"
    dwg.write_bytes(b"AC1032")
    source = _drawing("convert_source")
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        Path(command[2], "Plan.dxf").write_bytes(source.read_bytes())

        class Done:
            returncode = 0
            stderr = b""
        return Done()

    original = proc.run
    proc.run = fake_run
    try:
        target = cad.convert_dwg(dwg, folder / "cache" / "x.dxf", converter=Path("C:/ODA/ODAFileConverter.exe"))
    finally:
        proc.run = original
    assert target.is_file() and target.read_bytes() == source.read_bytes()
    (command,) = calls
    assert command[1] == str(folder) and command[3:] == [cad.ODA_VERSION, "DXF", "0", "1", "Plan.dwg"], command
    # a converter that writes nothing is said, not taken for a drawing
    proc.run = lambda command, **kwargs: type("Done", (), {"returncode": 1, "stderr": b"bad file"})()
    try:
        cad.convert_dwg(dwg, folder / "cache" / "y.dxf", converter=Path("C:/ODA/ODAFileConverter.exe"))
    except cad.CadError as exc:
        assert exc.code == "oda_failed" and "bad file" in str(exc)
    else:
        assert False, "a conversion that wrote nothing passed"
    finally:
        proc.run = original
