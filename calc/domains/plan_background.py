"""A plan's background -- its format, its storey, the size of its page in a PDF, a PNG, a JPEG or an SVG, its file's state and hash, its path from the project -- split out of calc/domains/plan.py (issue #30), moved verbatim. plan.py imports every name back. Qt-free.
"""

import functools
import hashlib
import re
import struct
import xml.etree.ElementTree as ET
from pathlib import Path
import validation
from domains._common import fail as _fail  # one copy of the domains' helpers (spec 2026-10-19-base-saine-nettoyage, G4)


# The storeys a plan's «Étage» offers, by language, the same index the same storey; free text is accepted as well (the engineer's answer of 06.10.2026: «storey» a free designation of any length, «floor» the one character of the positions' numbers, proposed from it -- storey_floor).
STOREYS = {
    "de": ["2.UG", "1.UG", "EG", "1.OG", "2.OG", "3.OG", "4.OG", "5.OG", "DG"],
    "fr": ["2e SS", "1er SS", "Rez", "1er", "2e", "3e", "4e", "5e", "Combles"],
    "en": ["B2", "B1", "GF", "1F", "2F", "3F", "4F", "5F", "Attic"],
}


# Where the list's storeys stand: the two basements, the ground floor, the five upper floors, the attic.
_STOREY_BASEMENTS = (0, 1)


_STOREY_GROUND = 2


_STOREY_ATTIC = 8


# The backgrounds a plan may be drawn on, by file suffix.
BACKGROUND_FORMATS = {".pdf": "pdf", ".png": "png", ".jpg": "jpg", ".jpeg": "jpg", ".svg": "svg"}


def background_format(path):
    return BACKGROUND_FORMATS.get(Path(path).suffix.lower())


def _storey_key(text):
    return re.sub(r"\s+", "", str(text or "")).casefold()


def storey_index(storey):
    """Where a storey stands in STOREYS -- the same index in every language -- or None for a designation of the engineer's own."""
    key = _storey_key(storey)
    if not key:
        return None
    for names in STOREYS.values():
        for index, name in enumerate(names):
            if _storey_key(name) == key:
                return index
    return None


def storey_floor(storey, other_floors=()):
    """The character a position's number takes for a storey (STE: U a basement, 0 the ground floor, 1 the first floor, …): proposed from the list, and the engineer's to change. The attic is one above the highest digit among `other_floors` -- the floors of the project's other plans --, else 1. A designation of the engineer's own proposes nothing, "", and so does an attic above the ninth floor, which one character cannot number."""
    index = storey_index(storey)
    if index is None:
        return ""
    if index in _STOREY_BASEMENTS:
        return "U"
    if index == _STOREY_GROUND:
        return "0"
    if index < _STOREY_ATTIC:
        return str(index - _STOREY_GROUND)
    digits = [int(f) for f in other_floors if isinstance(f, str) and len(f) == 1 and f.isdigit()]
    n = max(digits) + 1 if digits else 1
    return str(n) if n <= 9 else ""


def _file_state(path):
    """A file, its size and the time it was last written: what a reading of it is kept under, so that a file changed since is read again."""
    path = Path(path).resolve()
    stat = path.stat()
    return str(path), stat.st_size, stat.st_mtime_ns


def preload():
    """Imports pypdf ahead of the first PDF read -- called by Woodcore in a thread of its own: the import takes most of a second, which the first page turned would otherwise wait for."""
    try:
        __import__("pypdf")
    except ImportError:
        pass  # said when a PDF is read (_read_pdf)


def _pdf_reader(path):
    """The PDF at `path`, read by pypdf -- once while it is unchanged: the plans of a plan set are drawn on the same file, which the export and Woodcore's window would otherwise read again for each of them. pypdf reads the whole file into memory, so nothing holds it open."""
    return _read_pdf(*_file_state(path))


@functools.lru_cache(maxsize=4)
def _read_pdf(path, _size, _mtime_ns):
    """pypdf is needed only by a plan drawn on a PDF, so it is imported here rather than by every export."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise validation.ValidationError(
            "a plan is drawn on a PDF, and reading one needs pypdf: python -m pip install pypdf"
        ) from exc
    return PdfReader(path)


def _pdf_page_size(page):
    """The page as a viewer shows it: its crop box (its media box when it has none), turned by its /Rotate."""
    box = page.cropbox
    width, height = float(box.width), float(box.height)
    if int(page.rotation or 0) % 180 == 90:
        width, height = height, width
    return width, height


def _png_size(data):
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", data[16:24])


def _jpeg_size(data):
    """The size in the first start-of-frame marker of a JPEG -- any SOF but the DHT, JPG and DAC markers that share their range."""
    if data[:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        length = struct.unpack(">H", data[i + 2:i + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            height, width = struct.unpack(">HH", data[i + 5:i + 9])
            return width, height
        i += 2 + length
    return None


_LENGTH_RE = re.compile(r"^\s*([0-9.]+)\s*(px|pt|mm|cm|in)?\s*$")


_UNIT_PX = {None: 1.0, "px": 1.0, "pt": 96 / 72, "mm": 96 / 25.4, "cm": 96 / 2.54, "in": 96.0}


def _svg_size(data):
    """An SVG's sheet: its viewBox, whose units its drawing is in; without one, its width and height. Also whether the width and height it is set at keep the viewBox's proportions -- an SVG whose do not would be letterboxed by Typst and stretched by nobody else."""
    root = ET.fromstring(data)
    box = root.get("viewBox")
    width, height = root.get("width"), root.get("height")

    def length(text):
        m = _LENGTH_RE.match(text or "")
        return float(m.group(1)) * _UNIT_PX[m.group(2)] if m else None

    w, h = length(width), length(height)
    if box:
        parts = [float(v) for v in re.split(r"[\s,]+", box.strip())]
        if len(parts) == 4 and parts[2] > 0 and parts[3] > 0:
            proportional = not (w and h) or abs(w / h - parts[2] / parts[3]) <= 0.005 * parts[2] / parts[3]
            return (parts[2], parts[3]), proportional, (parts[0], parts[1])
    if w and h:
        return (w, h), True, (0.0, 0.0)
    return None, True, (0.0, 0.0)


def sheet_of(path, fmt, page=1, where="background"):
    """(width, height) of a background's sheet, in its own units. A background that cannot be read, or a page it does not have, is a blocking error naming the file."""
    path = Path(path)
    if not path.is_file():
        _fail(where, f"{path.name} does not exist -- was it renamed or moved? Choose the background again in Woodcore")
    if fmt == "pdf":
        try:
            reader = _pdf_reader(path)
            count = len(reader.pages)
        except validation.ValidationError:
            raise
        except Exception as exc:  # broad: pypdf raises a family of its own for a damaged file -- _fail stops naming the file
            _fail(where, f"{path.name} cannot be read as a PDF -- {exc}")
        if not 1 <= page <= count:
            _fail(where, f"{path.name} has {count} page(s), not a page {page}")
        return _pdf_page_size(reader.pages[page - 1])
    data = path.read_bytes()
    if fmt == "png":
        size = _png_size(data)
    elif fmt == "jpg":
        size = _jpeg_size(data)
    else:
        try:
            size, _proportional, _origin = _svg_size(data)
        except ET.ParseError as exc:
            _fail(where, f"{path.name} cannot be read as an SVG -- {exc}")
    if not size or size[0] <= 0 or size[1] <= 0:
        _fail(where, f"{path.name}: its size cannot be read")
    return float(size[0]), float(size[1])


def file_hash(path):
    """The SHA-256 of a file, computed once while it is unchanged -- the plans of a plan set share it."""
    return _hash_file(*_file_state(path))


@functools.lru_cache(maxsize=16)
def _hash_file(path, _size, _mtime_ns):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def background_path(project_root, relative):
    """The background's file, from the path the source gives relative to the project folder -- which it may not leave, so that the project stays whole on another machine syncing it."""
    root = Path(project_root).resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None
    return path


def relative_background(project_root, path):
    """The path a source stores for a background file: relative to the project folder, with forward slashes; None for a file outside it."""
    root = Path(project_root).resolve()
    try:
        return Path(path).resolve().relative_to(root).as_posix()
    except ValueError:
        return None
