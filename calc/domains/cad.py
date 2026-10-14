"""A CAD drawing as the background of a position plan: a DXF read with ezdxf, a DWG converted to DXF first by the ODA File Converter where it is installed (v0.114, the engineer's answer: «DXF read with ezdxf; a DWG converted by the ODA File Converter if installed, else Woodcore says where to download it -- nothing proprietary ships»).

What Woodcore draws a plan over is a page; a CAD drawing's pages are its layouts -- page 1 the model space, then the paper-space layouts in their tab order -- each rendered to an SVG by ezdxf's own drawing add-on (`ezdxf.addons.drawing`, SVG backend), with the layers the engineer switched off left out. That SVG is what the window shows (QtSvg) and what the report sets (Typst), so the plan the engineer drew on is the plan the checker reads, as for a PDF.

**Its units.** An SVG of ezdxf's is drawn in a coordinate space of its own, an integer grid whose longer side is `output_coordinate_space`; this module asks for one unit per hundredth of a millimetre of the page, so a plan's sheet units are 0.01 mm (`UNITS_PER_MM`) whatever the layout -- a paper-space layout is what is drawn on it fitted onto its paper size, the model space onto a page no longer than `MODEL_PAGE_MM` (an A1's long side), and the real scale of either is a calibration, a drawing's own units being nobody's guarantee.

**What it is kept to.** ezdxf writes its colours as CSS classes in a `<style>`, which QtSvg and Typst both read (checked: `tests/test_cad.py` renders one with QSvgRenderer); text is written as filled paths, so no font is needed on the machine that compiles the report. The background is white and ACI 7 is drawn black (`BackgroundPolicy.WHITE`, `ColorPolicy.COLOR`), the plot of a drawing rather than its screen.

Imports ezdxf when a drawing is read and not before: a project without a CAD background never needs it. Every child process goes through calc/proc.py, without a console window (tests/test_no_console.py).
"""

import functools
import os
import re
import shutil
import tempfile
from pathlib import Path

import validation

# Where the ODA File Converter is downloaded from, named by the refusal that says it is missing.
ODA_URL = "https://www.opendesign.com/guestfiles/oda_file_converter"
# The DXF version a DWG is converted to: ezdxf reads every one, and 2018 keeps what a recent drawing carries.
ODA_VERSION = "ACAD2018"
ODA_TIMEOUT = 300

# A plan's sheet unit for a CAD background: a hundredth of a millimetre of the page (see the module's note).
UNITS_PER_MM = 100.0
# The model space is fitted onto a page no longer than this, in mm: a sheet whose numbers stay sane, the real scale being a calibration.
MODEL_PAGE_MM = 841.0

MODEL = "Model"


class CadError(validation.ValidationError):
    """A drawing that cannot be read or converted, said by a code the window translates (`oda_missing`, `oda_failed`, `ezdxf_missing`, `dxf_unreadable`, `no_layout`) and an English sentence for whoever has no window."""

    def __init__(self, code, message, **values):
        super().__init__(message)
        self.code = code
        self.values = values


def _ezdxf():
    try:
        import ezdxf
    except ImportError as exc:
        raise CadError("ezdxf_missing", "a plan is drawn on a CAD drawing, and reading one needs ezdxf: python -m pip install ezdxf") from exc
    return ezdxf


# --- the ODA File Converter ---------------------------------------------------------------

def _version_key(path):
    """ODAFileConverter 25.12.0 → (25, 12, 0): the newest installed is taken."""
    return tuple(int(n) for n in re.findall(r"\d+", path.parent.name)) or (0,)


def oda_converter(program_files=None):
    """The ODA File Converter installed on this machine -- `%ProgramFiles%\\ODA\\ODAFileConverter*\\ODAFileConverter.exe`, the newest of them -- or None. `program_files` is a list of folders to search, for a test; by default %ProgramFiles% and %ProgramFiles(x86)%."""
    roots = program_files if program_files is not None else [
        os.environ.get(name) for name in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)")]
    found = []
    for root in roots:
        if not root:
            continue
        found += [p for p in (Path(root) / "ODA").glob("ODAFileConverter*/ODAFileConverter.exe") if p.is_file()]
    return max(found, key=_version_key) if found else None


def convert_dwg(path, target, converter=None):
    """Converts the DWG at `path` into the DXF `target` with the ODA File Converter, through calc/proc.py (no console window). A converter that is not installed is `oda_missing`, naming where to download it; one that writes nothing is `oda_failed`. Returns `target`."""
    import proc

    path, target = Path(path), Path(target)
    converter = converter or oda_converter()
    if converter is None:
        raise CadError("oda_missing", f"{path.name} is a DWG, which Woodcore reads once the free ODA File Converter is installed -- download it from {ODA_URL}", file=path.name, url=ODA_URL)
    with tempfile.TemporaryDirectory(prefix="woodcore-oda-") as out:
        # input folder, output folder, version, type, recurse, audit, filter: the drawing's own folder filtered to its name, so nothing is copied
        command = [str(converter), str(path.parent), out, ODA_VERSION, "DXF", "0", "1", path.name]
        try:
            result = proc.run(command, capture_output=True, timeout=ODA_TIMEOUT)
        except Exception as exc:  # a converter that cannot be started (OSError), or that hangs (TimeoutExpired)
            raise CadError("oda_failed", f"the ODA File Converter could not convert {path.name} -- {exc}", file=path.name, reason=str(exc)) from exc
        written = Path(out) / (path.stem + ".dxf")
        if not written.is_file():
            reason = (getattr(result, "stderr", b"") or b"").decode("utf-8", "replace").strip()
            raise CadError("oda_failed", f"the ODA File Converter wrote no DXF for {path.name}" + (f" -- {reason}" if reason else ""), file=path.name, reason=reason)
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_name(target.name + ".part")
        shutil.copyfile(written, partial)
        os.replace(partial, target)
    return target


# --- reading a DXF ------------------------------------------------------------------------

def _state(path):
    path = Path(path).resolve()
    stat = path.stat()
    return str(path), stat.st_size, stat.st_mtime_ns


def _layer_states(doc):
    return [{"name": layer.dxf.name, "on": bool(layer.is_on()), "frozen": bool(layer.is_frozen())} for layer in doc.layers]


@functools.lru_cache(maxsize=4)
def _read(path, _size, _mtime_ns):
    ezdxf = _ezdxf()
    try:
        doc = ezdxf.readfile(path)
    except Exception as exc:  # ezdxf raises a family of its own for a damaged file
        raise CadError("dxf_unreadable", f"{Path(path).name} cannot be read as a DXF -- {exc}", file=Path(path).name, reason=str(exc)) from exc
    return doc, _layer_states(doc)


def read_dxf(path):
    """(the ezdxf document, its layers as the file states them): read once while the file is unchanged. The document's layer table is set afresh by every render, so the states of the file are kept apart, read before any render touched them."""
    path = Path(path)
    if not path.is_file():
        raise CadError("dxf_unreadable", f"{path.name} does not exist", file=path.name, reason="missing")
    return _read(*_state(path))


def layouts(path):
    """The drawing's pages: the model space first, then its paper-space layouts in their tab order."""
    doc, _ = read_dxf(path)
    names = list(doc.layouts.names_in_taborder())
    return [MODEL] + [name for name in names if name != MODEL]


def layers(path):
    """The drawing's layers as the file states them: [{"name", "on", "frozen"}], in the layer table's order. A layer is shown where it is on and not frozen."""
    _, states = read_dxf(path)
    return [dict(state) for state in states]


def default_off(path):
    """The names of the layers the file itself does not show -- off or frozen: what a document starts with, as the PDF's own default state is for a PDF."""
    return [state["name"] for state in layers(path) if not state["on"] or state["frozen"]]


# A layout with nothing on it is a blank page, an A3 in landscape where the layout states no paper of its own.
EMPTY_PAGE_MM = (420.0, 297.0)


def blank_svg(width_mm, height_mm):
    """(svg_text, width, height): an empty white page of `width_mm` × `height_mm`, in sheet units -- a layout with nothing drawn on it, which ezdxf refuses to place."""
    w, h = round(UNITS_PER_MM * width_mm), round(UNITS_PER_MM * height_mm)
    text = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_mm:g}mm" height="{height_mm:g}mm" viewBox="0 0 {w} {h}">'
            f'<rect fill="#ffffff" x="0" y="0" width="{w}" height="{h}"/></svg>')
    return text, float(w), float(h)


def _draw(doc, target, off):
    """A recording of `target` drawn with the layers named in `off` (casefolded) switched off and every other one on and thawed."""
    from ezdxf.addons.drawing import Frontend, RenderContext, config, svg

    for layer in doc.layers:
        layer.thaw()
        if layer.dxf.name.casefold() in off:
            layer.off()
        else:
            layer.on()
    backend = svg.SVGBackend()
    context = RenderContext(doc)
    context.set_current_layout(target)
    configuration = config.Configuration(background_policy=config.BackgroundPolicy.WHITE, color_policy=config.ColorPolicy.COLOR)
    Frontend(context, backend, config=configuration).draw_layout(target)
    return backend


def render_svg(path, layout=MODEL, off_layers=()):
    """(svg_text, width, height): one layout of the drawing at `path` as an SVG whose viewBox is `0 0 width height` in sheet units (UNITS_PER_MM per mm of the page) and whose width and height are the page's in mm, the layers named in `off_layers` left out -- every other layer shown, the ones the file switched off included, since what is shown is the document's choice. Layer names compare without regard to case, as in a DXF.

    ⚠️ **The frame does not move when a layer is switched off**: ezdxf fits a page to what it drew, so a layer taken away would shrink the page and shift every plan drawn on it off the architecture. The frame is therefore the extent of the layout with **every** layer on, and the drawing without the off layers is placed in it.
    """
    from ezdxf.addons.drawing import layout as dlayout

    doc, _ = read_dxf(path)
    if layout not in layouts(path):
        raise CadError("no_layout", f"{Path(path).name} has no layout {layout!r}", file=Path(path).name, layout=layout)
    target = doc.modelspace() if layout == MODEL else doc.layouts.get(layout)
    if layout == MODEL:
        page = dlayout.Page(0, 0, dlayout.Units.mm, max_width=MODEL_PAGE_MM, max_height=MODEL_PAGE_MM)
    else:
        page = dlayout.Page.from_dxf_layout(target)
    full = _draw(doc, target, set())
    box = full.player().bbox()
    if not box.has_data or box.size.x <= 0 or box.size.y <= 0:
        # nothing drawn, or a single line with no extent across it: ezdxf cannot place it on a page
        return blank_svg(page.width_in_mm or EMPTY_PAGE_MM[0], page.height_in_mm or EMPTY_PAGE_MM[1])
    off = {name.casefold() for name in off_layers}
    backend = _draw(doc, target, off) if off else full
    final = dlayout.Layout(box).get_final_page(page, dlayout.Settings())
    side_mm = max(final.width_in_mm, final.height_in_mm)
    settings = dlayout.Settings(output_coordinate_space=round(UNITS_PER_MM * side_mm))
    text = backend.get_string(page, settings=settings, render_box=box, xml_declaration=False)
    found = re.search(r'viewBox="0 0 ([0-9.]+) ([0-9.]+)"', text)
    if not found:  # ezdxf's empty page
        return blank_svg(final.width_in_mm, final.height_in_mm)
    return text, float(found.group(1)), float(found.group(2))
