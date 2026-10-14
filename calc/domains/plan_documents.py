"""The documents a position plan is drawn on: an architect's PDF, an image, an SVG or a CAD drawing, imported once into the project and then cut into plans (v0.114, docs/domain/position-plans.md §3.3sexies).

**A document is a source of its own**, `Woodcore-Datei/plans/documents/<docid>.json`, a subfolder of the plans' own folder -- which `plan.source_paths` globs at its top only, so a document is never read as a plan:

    {"schema_version": "1.0", "id": "D01", "name": "", "file": "01_Pläne/03_Pavillon.pdf", "kind": "pdf",
     "sha256": "…", "pages": [{"page": 1, "rotation": 0}], "layers_off": ["100 Bemassung Ausführung"]}

`kind` is `pdf`, `image` (PNG, JPEG), `svg` or `cad` (DXF, DWG). `pages` lists every page with the rotation the engineer gave it, in degrees clockwise, on top of a PDF's own /Rotate; a CAD drawing's pages are its layouts -- page 1 the model space, then the paper-space layouts in their tab order, each `layout` naming its own. `layers_off` names the layers switched off -- a PDF's optional-content groups or a drawing's layers -- one list for the whole document, initialised from the file's own default state when it is imported. Nothing is copied: the file stays where the engineer keeps it, inside the project, and a plan names the document (`background.document`) with its page.

**What the window shows** is `render_source`: for a PDF a copy of the whole document with the switched-off groups stated as its default (`/OCProperties /D /OFF`, which QtPdf's PDFium honours) and each page turned by the engineer's rotation (`/Rotate`), the pages keeping their numbers; for a CAD drawing an SVG of the layout without its switched-off layers (calc/domains/cad.py); an image or an SVG as it is, or wrapped in an SVG that turns it. Each is cached outside the project (`%LOCALAPPDATA%\\Woodcore\\layers`), keyed by the file's SHA-256, the rotations and the layers switched off.

**What the report sets** is `flatten_page`: one page as a PDF of its own, turned, with the content of every switched-off group **taken out** of the page -- Typst's PDF export draws every optional-content group whatever its state (it says so: «PDF contains optional content groups»), so stripping is the one way the report hides a layer. A marked-content section `/OC /name BDC … EMC` of a group that is off paints nothing, and neither does a form or an image XObject whose own `/OC` is off; the stripping follows PDF 2.0 8.11.3.2 exactly -- hidden content **paints nothing and changes the graphics state as it would have**: a path is still built and still clips, a colour is still set, a `cm` still moves what follows, and a text-showing operator still advances the text position, set in the invisible rendering mode rather than removed. An optional-content membership dictionary is evaluated by its `/P` (AnyOn by default) or its visibility expression `/VE`. The page's `/OCProperties` and its XObjects' `/OC` are dropped once nothing they govern is left.

Imports pypdf and ezdxf when a document needs them, like plan.py. Every refusal is a `DocumentError`, carrying a code the window translates and an English sentence.
"""

import base64
import hashlib
import io
import json
import os
import re
import threading
from collections import namedtuple
from pathlib import Path

import validation
from domains import cad
from domains import plan as model

SCHEMA_VERSION = "1.1"
SCHEMA_VERSIONS = ("1.0", SCHEMA_VERSION)
# Which tab a document belongs to (v0.116, schema 1.1, the engineer: «je ne dois pas avoir accès dans le volet de gauche à des documents qui ont été déposés dans le plan de protection incendie, si je me trouve dans le plan de position et vice versa»): the tab that imported it. A document written before says nothing and is the position plans' -- unless every plan drawn on it is a fire plan with a frame of its own (plan_pages.document_owner).
OWNERS = ("plan", "fire")
# What the flattened pages cached are made by: raised where flatten_page would make another page of the same document, so a page cached by an older Woodcore is never taken for one of this one.
FLATTEN_VERSION = 1

# A document's kind, by file suffix.
KINDS = ("pdf", "image", "svg", "cad")
SUFFIX_KINDS = {".pdf": "pdf", ".png": "image", ".jpg": "image", ".jpeg": "image", ".svg": "svg", ".dxf": "cad", ".dwg": "cad"}
# The rotations a page may be given, in degrees clockwise.
ROTATIONS = (0, 90, 180, 270)
# A document's id: D01, D02, …; any id of the plans' own shape is read.
ID_PATTERN = model.ID_PATTERN
ID_PREFIX = "D"

# The folder of the caches, below %LOCALAPPDATA%\Woodcore; a test points CACHE_ROOT somewhere of its own.
CACHE_NAME = "layers"
CAD_CACHE_NAME = "cad"
CACHE_ROOT = None

# Where a document lives: the project's folder, and the plans' own folder whose subfolder `documents` holds the sources. A Project is one (its `root` and `plans_dir`); plan.prepare, which is handed the two folders, builds one.
Place = namedtuple("Place", "root plans_dir")


class DocumentError(validation.ValidationError):
    """A document that cannot be imported, read or drawn: `code` names the window's sentence (`doc_outside`, `doc_kind`, `doc_missing`, `doc_unreadable`, `doc_page`, `doc_rotation`, `doc_id`, `doc_taken`, and calc/domains/cad.py's own), `values` fill its holes, and the exception's text is the English sentence."""

    def __init__(self, code, message, **values):
        super().__init__(message)
        self.code = code
        self.values = values


def _fail(code, message, **values):
    raise DocumentError(code, message, **values)


def _place(here):
    if here is None:
        import project
        here = project.current()
    return Place(Path(here.root), Path(here.plans_dir))


def _usersettings():
    """usersettings.py, from calc/tools/ -- imported as calc/templates.py imports it."""
    try:
        import usersettings
    except ImportError:
        from tools import usersettings
    return usersettings


def cache_dir(name=CACHE_NAME):
    """A folder of this module's caches: `layers` for what is rendered, `cad` for a DWG converted to DXF. Outside the project, which NextCloud syncs; deleting it costs a render."""
    folder = Path(CACHE_ROOT) / name if CACHE_ROOT is not None else _usersettings().cache_dir(name)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _write_atomic(path, payload):
    """`payload` written beside `path` and moved into place. The part's name is this writer's own (v0.116): the window's document view and its canvas may make the same cached copy at once, each in its own thread -- and where the other has put it in place first, and holds it open already (QtPdf loads the canvas's page from its path), this one's copy, the same bytes, is simply let go."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f"{path.name}.{os.getpid()}-{threading.get_ident()}.part")
    partial.write_bytes(payload if isinstance(payload, bytes) else payload.encode("utf-8"))
    try:
        os.replace(partial, path)
    except PermissionError:
        if not path.is_file():
            raise
        partial.unlink(missing_ok=True)
    return path


# --- the source ---------------------------------------------------------------------------

def source_dir(here=None):
    """The folder of the document sources: `documents/` inside the plans' own folder."""
    return _place(here).plans_dir / "documents"


def kind_of(path):
    """The kind of document a file is, by its suffix, or None for one Woodcore does not read."""
    return SUFFIX_KINDS.get(Path(path).suffix.lower())


def check(doc, where):
    """Everything a document source must satisfy: its structure against schemas/plan-document.schema.json, then what a schema cannot say -- a page listed once each from 1, a rotation of a quarter turn, a CAD page naming its layout."""
    if isinstance(doc, dict) and doc.get("schema_version") not in SCHEMA_VERSIONS:
        raise validation.ValidationError(f"{where}: schema_version is {doc.get('schema_version')!r} -- expected {' or '.join(map(repr, SCHEMA_VERSIONS))}")
    try:
        validation.validate_structure(doc, "plan-document")
    except validation.ValidationError as exc:
        raise validation.ValidationError(f"{where}: {exc}") from None
    if not ID_PATTERN.match(doc["id"]):
        raise validation.ValidationError(f"{where}: id {doc['id']!r} -- use letters, digits and _ . + - only")
    if doc["kind"] not in KINDS:
        raise validation.ValidationError(f"{where}: kind is {doc['kind']!r} -- expected one of {', '.join(KINDS)}")
    if "owner" in doc and doc["owner"] not in OWNERS:
        raise validation.ValidationError(f"{where}: owner is {doc['owner']!r} -- expected one of {', '.join(OWNERS)}")
    if kind_of(doc["file"]) != doc["kind"]:
        raise validation.ValidationError(f"{where}: {doc['file']!r} is not a file of kind {doc['kind']!r}")
    for i, page in enumerate(doc["pages"], start=1):
        if page["page"] != i:
            raise validation.ValidationError(f"{where}: pages[{i}] is page {page['page']!r} -- the pages are listed once each, from 1")
        if page.get("rotation", 0) not in ROTATIONS:
            raise validation.ValidationError(f"{where}: page {i}: rotation is {page.get('rotation')!r} -- 0, 90, 180 or 270 degrees clockwise")
        if doc["kind"] == "cad" and not page.get("layout"):
            raise validation.ValidationError(f"{where}: page {i} of a CAD drawing names no layout")
    if not doc["pages"]:
        raise validation.ValidationError(f"{where}: a document has at least one page")


def list_documents(here=None):
    """Every document of the project, checked, in id order."""
    folder = source_dir(here)
    if not folder.is_dir():
        return []
    docs = []
    for path in sorted(folder.glob("*.json"), key=lambda p: p.name.lower()):
        docs.append(_read_path(path))
    return docs


def _read_path(path):
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise validation.ValidationError(f"{Path(path).name}: not readable as JSON -- {exc}") from None
    check(doc, Path(path).name)
    if doc["id"] != Path(path).stem:
        raise validation.ValidationError(f"{Path(path).name}: id is {doc['id']!r} but the file is named {Path(path).name} -- they must agree")
    return doc


def read(here, docid):
    """The document `docid`, checked; a document that is not there is `doc_missing`."""
    path = source_dir(here) / f"{docid}.json"
    if not path.is_file():
        _fail("doc_missing", f"document {docid} does not exist -- import its file again", id=docid)
    return _read_path(path)


def write(here, doc):
    """Writes the document's source, whole, LF, two-space indent, beside itself and moved into place. Returns its path. A document that names its owner is written as 1.1, the version that has the field; one that names none keeps the version it was read as."""
    if "owner" in doc and doc.get("schema_version") != SCHEMA_VERSION:
        doc = dict(doc, schema_version=SCHEMA_VERSION)
    check(doc, f"documents/{doc.get('id')}.json")
    text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    return _write_atomic(source_dir(here) / f"{doc['id']}.json", text)


def new_id(here=None):
    """The next free id, D01, D02, … -- after the highest taken, a gap never refilled (the rule of a position's id)."""
    folder = source_dir(here)
    highest = 0
    if folder.is_dir():
        for path in folder.glob("*.json"):
            m = re.fullmatch(rf"{ID_PREFIX}(\d+)", path.stem, re.IGNORECASE)
            if m:
                highest = max(highest, int(m.group(1)))
    return f"{ID_PREFIX}{highest + 1:02d}"


def file_path(here, doc):
    """The document's file, from the path its source gives relative to the project folder; one outside it is `doc_outside`, one that is gone `doc_missing`."""
    place = _place(here)
    path = model.background_path(place.root, doc["file"])
    if path is None:
        _fail("doc_outside", f"{doc['file']} lies outside the project folder -- copy it into the folder first", file=doc["file"])
    if not path.is_file():
        _fail("doc_missing", f"{doc['file']} does not exist -- was it renamed or moved?", file=doc["file"], id=doc.get("id", ""))
    return path


def import_file(here, path, name="", docid=None, owner="plan"):
    """Imports the file at `path` -- which must lie inside the project, nothing is copied -- as a new document, written and returned: its kind, its SHA-256, every page at no rotation, the layers the file itself does not show, and the tab it belongs to (`owner`, OWNERS: the tab that imports it, v0.116). A DWG is converted to DXF for reading (`cad_source`), which needs the ODA File Converter."""
    if owner not in OWNERS:
        raise ValueError(f"owner {owner!r} -- expected one of {', '.join(OWNERS)}")
    place = _place(here)
    path = Path(path)
    kind = kind_of(path)
    if kind is None:
        _fail("doc_kind", f"{path.name} -- a plan is drawn on a PDF, a PNG, a JPEG, an SVG, a DXF or a DWG", file=path.name)
    relative = model.relative_background(place.root, path)
    if relative is None:
        _fail("doc_outside", f"{path.name} lies outside the project folder -- copy it into the folder first", file=path.name)
    if not path.is_file():
        _fail("doc_missing", f"{path.name} does not exist", file=path.name, id="")
    docid = docid or new_id(here)
    if (source_dir(here) / f"{docid}.json").exists():
        _fail("doc_taken", f"document {docid} exists already", id=docid)
    doc = {"schema_version": SCHEMA_VERSION, "id": docid, "name": name, "file": relative, "kind": kind,
           "sha256": model.file_hash(path), "pages": [], "layers_off": [], "owner": owner}
    doc["pages"], doc["layers_off"] = _pages_and_layers(here, doc)
    write(here, doc)
    return doc


def _pages_and_layers(here, doc):
    kind = doc["kind"]
    path = file_path(here, doc)
    if kind == "pdf":
        count = _count_pdf(path)
        return [{"page": i, "rotation": 0} for i in range(1, count + 1)], pdf_default_off(path)
    if kind == "cad":
        dxf = cad_source(here, doc)
        return ([{"page": i, "rotation": 0, "layout": name} for i, name in enumerate(cad.layouts(dxf), start=1)],
                cad.default_off(dxf))
    return [{"page": 1, "rotation": 0}], []


def refresh(here, doc):
    """(doc, notes): the document read against its file again -- a file replaced since it was imported keeps the rotations of the pages it still has and the layers switched off that it still names, gains a page at no rotation for each it gained, and its SHA-256 is brought up to date. Nothing is written; the notes say what changed."""
    path = file_path(here, doc)
    digest = model.file_hash(path)
    if digest == doc.get("sha256"):
        return doc, []
    old = {p["page"]: p for p in doc["pages"]}
    pages, defaults = _pages_and_layers(here, doc)
    names = {layer["name"] for layer in layers(here, {**doc, "layers_off": []})}
    fresh = dict(doc, sha256=digest, pages=[{**p, "rotation": old.get(p["page"], {}).get("rotation", 0)} for p in pages],
                 layers_off=[n for n in doc["layers_off"] if n in names])
    notes = [f"document {doc['id']}: {doc['file']} has changed since it was imported"]
    if len(pages) != len(doc["pages"]):
        notes.append(f"document {doc['id']}: {doc['file']} has {len(pages)} page(s) now, and not {len(doc['pages'])}")
    return fresh, notes


def page_entry(doc, page):
    """The entry of page `page` of the document; a page it does not have is `doc_page`."""
    if isinstance(page, bool) or not isinstance(page, int) or not 1 <= page <= len(doc["pages"]):
        _fail("doc_page", f"document {doc['id']} has {len(doc['pages'])} page(s), not a page {page!r}", id=doc["id"], page=page, count=len(doc["pages"]))
    return doc["pages"][page - 1]


def rotation(doc, page):
    """The rotation the engineer gave page `page`, in degrees clockwise."""
    return int(page_entry(doc, page).get("rotation", 0))


def set_rotation(doc, page, degrees):
    """Gives page `page` a rotation of `degrees` clockwise -- any multiple of 90, brought into 0-270 -- and returns the document, changed in place. What was drawn on that page is turned with it by the caller, `plan.rotate_source`."""
    if isinstance(degrees, bool) or not isinstance(degrees, (int, float)) or degrees % 90:
        _fail("doc_rotation", f"a page is turned by quarter turns, not by {degrees!r} degrees", degrees=degrees)
    page_entry(doc, page)["rotation"] = int(degrees) % 360
    return doc


def set_layer(doc, name, on):
    """Switches the layer `name` on or off in the document, and returns it changed in place; `layers_off` keeps the order the layers were switched off in."""
    off = [n for n in doc["layers_off"] if n != name]
    if not on:
        off.append(name)
    doc["layers_off"] = off
    return doc


def page_count(here, doc):
    """How many pages the document has: a PDF's pages, a drawing's layouts, 1 for an image or an SVG -- read from its source, which import_file and refresh keep in step with the file."""
    return len(doc["pages"])


# --- PDF ----------------------------------------------------------------------------------

def _reader(path):
    return model._pdf_reader(path)


# pypdf's reader is one object per file, shared (plan._pdf_reader) and read through one stream: two threads resolving its objects at once -- the document view's loader, the window's canvas, the export of a layer switched in the background (v0.116) -- would read each other's bytes. Every use of it here takes this lock; it is held for moments, the one long read -- a page stripped for the report -- reading a reader of its own (_flatten).
_PDF_LOCK = threading.RLock()


def _locked(function):
    import functools

    @functools.wraps(function)
    def run(*args, **kwargs):
        with _PDF_LOCK:
            return function(*args, **kwargs)
    return run


@_locked
def _count_pdf(path):
    try:
        return len(_reader(path).pages)
    except validation.ValidationError:
        raise
    except Exception as exc:  # broad: pypdf raises a family of its own for a damaged file -- _fail stops naming the file
        _fail("doc_unreadable", f"{Path(path).name} cannot be read as a PDF -- {exc}", file=Path(path).name, reason=str(exc))


def _text(value):
    return str(value) if value is not None else ""


def _ocgs(reader):
    """The optional-content groups of a PDF, as (name, indirect reference or object), in the order /OCProperties /OCGs lists them."""
    root = reader.trailer["/Root"]
    properties = root.get("/OCProperties")
    if properties is None:
        return []
    groups = properties.get_object().get("/OCGs")
    groups = groups.get_object() if groups is not None else []
    return [(_text(g.get_object().get("/Name")), g) for g in groups]


def _array(value):
    """A PDF array, direct or indirect, as a list; nothing as an empty one."""
    if value is None:
        return []
    value = value.get_object()
    return list(value) if isinstance(value, list) else [value]


def _ref_id(obj):
    return getattr(obj, "idnum", None) or id(obj)


@_locked
def pdf_layers(path):
    """The PDF's optional-content groups: [{"name", "on"}] in /OCGs order, `on` the default state /OCProperties /D gives them (/BaseState, /ON, /OFF), each name once."""
    reader = _reader(path)
    groups = _ocgs(reader)
    if not groups:
        return []
    default = reader.trailer["/Root"]["/OCProperties"].get_object().get("/D")
    default = default.get_object() if default is not None else {}
    base_off = _text(default.get("/BaseState")) == "/OFF"
    on_ids = {_ref_id(g) for g in _array(default.get("/ON"))}
    off_ids = {_ref_id(g) for g in _array(default.get("/OFF"))}
    out, seen = [], set()
    for name, group in groups:
        if name in seen:
            continue
        seen.add(name)
        gid = _ref_id(group)
        shown = (gid in on_ids) if base_off else (gid not in off_ids)
        out.append({"name": name, "on": shown})
    return out


def pdf_default_off(path):
    """The names of the groups the PDF itself hides by default: what a document starts with."""
    return [layer["name"] for layer in pdf_layers(path) if not layer["on"]]


def layers(here, doc):
    """The document's layers, each with whether the document shows it: [{"name", "on"}] -- a PDF's optional-content groups, a drawing's layers, none for an image or an SVG. `on` is the document's choice (`layers_off`), not the file's."""
    off = set(doc.get("layers_off", []))
    if doc["kind"] == "pdf":
        names = [layer["name"] for layer in pdf_layers(file_path(here, doc))]
    elif doc["kind"] == "cad":
        names = [layer["name"] for layer in cad.layers(cad_source(here, doc))]
    else:
        names = []
    return [{"name": name, "on": name not in off} for name in names]


@_locked
def page_size(here, doc, page):
    """(width, height) of page `page` in its sheet units, as the window shows it -- **after** the engineer's rotation: points for a PDF (its crop box, turned by its own /Rotate then by the rotation), pixels for an image, viewBox units for an SVG, hundredths of a millimetre for a drawing's layout (calc/domains/cad.py)."""
    entry = page_entry(doc, page)
    path = file_path(here, doc)
    kind = doc["kind"]
    if kind == "pdf":
        width, height = model.sheet_of(path, "pdf", page, f"document {doc['id']}")
    elif kind == "cad":
        _text_svg, width, height = _cad_svg(here, doc, page, unrotated=True)
    else:
        fmt = model.background_format(path)
        width, height = model.sheet_of(path, fmt, 1, f"document {doc['id']}")
    if int(entry.get("rotation", 0)) % 180 == 90:
        width, height = height, width
    return float(width), float(height)


def _cache_key(doc, *parts):
    text = json.dumps([doc.get("sha256", ""), doc["kind"], *parts], ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]


def _off_set(doc):
    return sorted(set(doc.get("layers_off", [])))


def render_source(here, doc, page=None):
    """The file the window renders the document's page `page` from (a Path):

    * a **PDF** -- the whole document, its pages keeping their numbers, with the groups the document switched off stated as the default state (`/OCProperties /D`: /BaseState /ON, the off groups in /OFF, any /AS taken out so no usage overrides it) and each page turned by its rotation; the file itself where neither changes anything. `page` is not needed for a PDF.
    * a **CAD drawing** -- an SVG of the layout of page `page` without its switched-off layers, turned by its rotation;
    * an **image** or an **SVG** -- the file itself, or, turned, an SVG that turns it.

    Cached outside the project, keyed by the file's SHA-256, the rotations and the layers switched off: a second call with the same document is a path.

    ⚠️ **A layer switched costs an append, not a rewrite** (v0.116, the engineer: «en activer un ou en désactiver un prend énormément de temps»). Rewriting the whole PDF with pypdf took 1 to 1.6 s on an architect's plan set of 18 pages and 74 groups (8 MB) at every switch; the state of the groups is one small dictionary, so it is written as an **incremental update** appended to the file -- the default configuration's object written again, a cross-reference section of its own pointing back to the file's (`_with_state_update`), a few kilobytes and a few milliseconds. The pages turned are a copy of their own, made once per set of rotations (`_turned`), the layers' update appended to it. A file pypdf cannot update so -- an encrypted one, a damaged one -- is rewritten whole, as before."""
    kind = doc["kind"]
    path = file_path(here, doc)
    if kind == "pdf":
        rotations = [int(p.get("rotation", 0)) for p in doc["pages"]]
        off = _off_set(doc)
        if not any(rotations) and off == sorted(set(pdf_default_off(path))) and _default_is_plain(path):
            return path
        target = cache_dir() / f"{_cache_key(doc, 'view', rotations, off)}.pdf"
        if not target.is_file():
            base = _turned(doc, path, rotations) if any(rotations) else path
            try:
                content = _with_state_update(base, off)
            except Exception:  # broad: pypdf's own family for a file it cannot read so, and anything this writer cannot follow: the whole file rewritten instead
                content = None
            if content is None:
                content = _pdf_with_state(path, rotations, off)
            _write_atomic(target, content)
        return target
    page = page or 1
    turn = rotation(doc, page)
    if kind == "cad":
        target = cache_dir() / f"{_cache_key(doc, 'cad', page, turn, _off_set(doc))}.svg"
        if not target.is_file():
            text, _w, _h = _cad_svg(here, doc, page)
            _write_atomic(target, text)
        return target
    if not turn:
        return path
    target = cache_dir() / f"{_cache_key(doc, 'turn', turn)}.svg"
    if not target.is_file():
        _write_atomic(target, _turned_svg(path, kind, turn))
    return target


@_locked
def _default_is_plain(path):
    """Whether the PDF's default configuration is plain enough to be left as it is: no /AS, which could switch a group by its usage."""
    groups = _ocgs(_reader(path))
    if not groups:
        return True
    default = _reader(path).trailer["/Root"]["/OCProperties"].get_object().get("/D")
    return default is None or "/AS" not in default.get_object()


def _turned(doc, path, rotations):
    """The whole PDF with each page turned by its rotation and its groups left as the file states them -- the copy a layers' update is appended to, made once per set of rotations and cached beside the views."""
    target = cache_dir() / f"{_cache_key(doc, 'turned', rotations)}.pdf"
    if not target.is_file():
        _write_atomic(target, _pdf_with_state(path, rotations, None))
    return target


def _serialized(obj):
    stream = io.BytesIO()
    obj.write_to_stream(stream)
    return stream.getvalue()


@_locked
def _with_state_update(base, off, section=None):
    """The bytes of the PDF `base` with the groups named in `off` stated off by default -- its default configuration (/OCProperties /D: /BaseState /ON, the off groups in /OFF, the others in /ON, any /AS taken out) written again as an **incremental update** appended to the file (PDF 2.0 7.5.6): the one object that holds the configuration -- /D where it is an object of its own, else /OCProperties, else the catalogue --, then a cross-reference section of the same kind as the file's last (a table, or a cross-reference stream) whose /Prev points back to it. Every other byte of the file is the file's. `base`'s own bytes where it has no groups; raises where it cannot be updated so -- an encrypted file --, the caller then rewriting the whole file."""
    from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject, NameObject, NumberObject

    data = Path(base).read_bytes()
    reader = _reader(base)
    if reader.is_encrypted:
        raise ValueError("an encrypted PDF is rewritten whole")
    trailer = reader.trailer
    root_ref = trailer.raw_get("/Root")
    if not isinstance(root_ref, IndirectObject):
        raise ValueError("a catalogue that is no object of its own")
    root = root_ref.get_object()
    if "/OCProperties" not in root:
        return data
    props_ref = root.raw_get("/OCProperties")
    props = props_ref.get_object()
    groups = props.get("/OCGs")
    groups = list(groups.get_object()) if groups is not None else []
    if not groups or not all(isinstance(g, IndirectObject) for g in groups):
        raise ValueError("an optional-content group that is no object of its own")
    off = set(off)
    d_ref = props.raw_get("/D") if "/D" in props else None
    default = DictionaryObject(d_ref.get_object()) if d_ref is not None else DictionaryObject()
    default[NameObject("/BaseState")] = NameObject("/ON")
    default[NameObject("/OFF")] = ArrayObject([g for g in groups if _text(g.get_object().get("/Name")) in off])
    default[NameObject("/ON")] = ArrayObject([g for g in groups if _text(g.get_object().get("/Name")) not in off])
    if "/AS" in default:
        del default[NameObject("/AS")]
    if isinstance(d_ref, IndirectObject):
        number, generation, body = d_ref.idnum, d_ref.generation, default
    else:
        fresh = DictionaryObject(props)
        fresh[NameObject("/D")] = default
        if isinstance(props_ref, IndirectObject):
            number, generation, body = props_ref.idnum, props_ref.generation, fresh
        else:
            catalogue = DictionaryObject(root)
            catalogue[NameObject("/OCProperties")] = fresh
            number, generation, body = root_ref.idnum, root_ref.generation, catalogue
    found = data.rfind(b"startxref")
    if found < 0:
        raise ValueError("no startxref")
    previous = int(data[found + len(b"startxref"):].split()[0])
    size = int(trailer["/Size"])
    out = bytearray(data)
    if not out.endswith(b"\n"):
        out += b"\n"
    offset = len(out)
    out += f"{number} {generation} obj\n".encode("ascii") + _serialized(body) + b"\nendobj\n"
    xref = len(out)
    kept = {key: trailer.raw_get(key) for key in ("/Root", "/Info", "/ID") if key in trailer}
    # `section` forces the kind of the update's cross-reference section -- what a test does to reach the kind its own fixture does not end on
    if (section or ("table" if data[previous:previous + 32].lstrip().startswith(b"xref") else "stream")) == "table":
        tail = DictionaryObject({NameObject("/Size"): NumberObject(max(size, number + 1)), NameObject("/Prev"): NumberObject(previous)})
        tail.update({NameObject(k): v for k, v in kept.items()})
        out += b"xref\n" + f"{number} 1\n{offset:010d} {generation:05d} n\r\n".encode("ascii") + b"trailer\n" + _serialized(tail)
        out += f"\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
    else:
        stream_number = max(size, number + 1)
        if generation > 0xFFFF or xref > 0xFFFFFFFF:
            raise ValueError("an offset or a generation too large for a 4-byte cross-reference stream")
        rows = bytes([1]) + offset.to_bytes(4, "big") + generation.to_bytes(2, "big") + bytes([1]) + xref.to_bytes(4, "big") + (0).to_bytes(2, "big")
        tail = DictionaryObject({NameObject("/Type"): NameObject("/XRef"), NameObject("/Size"): NumberObject(stream_number + 1),
                                 NameObject("/W"): ArrayObject([NumberObject(1), NumberObject(4), NumberObject(2)]),
                                 NameObject("/Index"): ArrayObject([NumberObject(number), NumberObject(1), NumberObject(stream_number), NumberObject(1)]),
                                 NameObject("/Prev"): NumberObject(previous), NameObject("/Length"): NumberObject(len(rows))})
        tail.update({NameObject(k): v for k, v in kept.items()})
        out += f"{stream_number} 0 obj\n".encode("ascii") + _serialized(tail) + b"\nstream\n" + rows + b"\nendstream\nendobj\n"
        out += f"startxref\n{xref}\n%%EOF\n".encode("ascii")
    return bytes(out)


@_locked
def _pdf_with_state(path, rotations, off):
    """The whole PDF with the groups named in `off` stated off by default -- left as the file states them where `off` is None -- and each page turned by its rotation."""
    from pypdf import PdfWriter
    from pypdf.generic import ArrayObject, NameObject

    writer = PdfWriter(clone_from=_reader(path))
    for page, turn in zip(writer.pages, rotations):
        if turn:
            page.rotate(turn)
    properties = writer._root_object.get("/OCProperties")
    if properties is not None and off is not None:
        properties = properties.get_object()
        groups = properties.get("/OCGs")
        groups = groups.get_object() if groups is not None else []
        off = set(off)
        default = properties.get("/D")
        default = default.get_object() if default is not None else None
        if default is None:
            from pypdf.generic import DictionaryObject
            default = DictionaryObject()
            properties[NameObject("/D")] = default
        default[NameObject("/BaseState")] = NameObject("/ON")
        default[NameObject("/OFF")] = ArrayObject([g for g in groups if _text(g.get_object().get("/Name")) in off])
        default[NameObject("/ON")] = ArrayObject([g for g in groups if _text(g.get_object().get("/Name")) not in off])
        for key in ("/AS",):
            if key in default:
                del default[key]
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


# --- stripping a hidden group from a page -------------------------------------------------------

# What paints, and what paints nothing but changes the state as painting would (PDF 2.0 8.11.3.2).
_PAINT_PATH = {b"S", b"s", b"f", b"F", b"f*", b"B", b"B*", b"b", b"b*"}
_SHOW_TEXT = {b"Tj", b"TJ", b"'", b'"'}


def _visible(entry, off, depth=0):
    """Whether an optional-content group or membership dictionary is visible with the groups named in `off` switched off. A membership dictionary is read by its visibility expression /VE where it has one, else by its /P policy over its /OCGs (AnyOn by default). Anything that cannot be read is visible: nothing is hidden on a guess."""
    if entry is None or depth > 16:
        return True
    entry = entry.get_object()
    kind = _text(entry.get("/Type"))
    if kind == "/OCG" or (kind == "" and "/Name" in entry and "/OCGs" not in entry):
        return _text(entry.get("/Name")) not in off
    if kind != "/OCMD":
        return True
    expression = entry.get("/VE")
    if expression is not None:
        return _expression(expression, off, depth + 1)
    groups = entry.get("/OCGs")
    if groups is None:
        return True
    groups = groups.get_object()
    members = list(groups) if isinstance(groups, list) else [groups]
    states = [_visible(g, off, depth + 1) for g in members]
    if not states:
        return True
    policy = _text(entry.get("/P")) or "/AnyOn"
    return {"/AllOn": all(states), "/AnyOn": any(states), "/AnyOff": not all(states), "/AllOff": not any(states)}.get(policy, any(states))


def _expression(expression, off, depth):
    expression = expression.get_object()
    if not isinstance(expression, list):
        return _visible(expression, off, depth)
    if not expression:
        return True
    op = _text(expression[0])
    operands = [_expression(e, off, depth + 1) for e in expression[1:]]
    if op == "/And":
        return all(operands)
    if op == "/Or":
        return any(operands)
    if op == "/Not":
        return not operands[0] if operands else True
    return True


class _Stripper:
    """Takes the content of the switched-off groups out of one page, and out of the form XObjects it draws."""

    def __init__(self, writer, off):
        self.writer = writer
        self.off = set(off)
        self.forms = {}

    def properties(self, resources, name):
        props = (resources or {}).get("/Properties")
        props = props.get_object() if props is not None else {}
        return props.get(name)

    def marked(self, operands, resources):
        """Whether a `BDC` opens a section that is hidden: /OC with a name in the resources' /Properties, or an inline dictionary."""
        if len(operands) < 2 or _text(operands[0]) != "/OC":
            return False
        target = operands[1]
        if _text(target).startswith("/"):
            target = self.properties(resources, target)
        return target is not None and not _visible(target, self.off)

    def strip(self, operations, resources):
        """The operations with the hidden content painting nothing, as PDF 2.0 says it does not: a painting operator becomes `n` (the path still clips, if W came before it), a text-showing operator is set in the invisible rendering mode and then the mode put back (the text position still advances), an XObject, a shading and an inline image are dropped. Everything else -- q, Q, cm, the colours, a clip -- is kept."""
        from pypdf.generic import FloatObject, NameObject, NumberObject

        out = []
        hidden = []  # one flag per marked-content section open: whether it, or one around it, is hidden
        mode, stack = 0, []
        xobjects = (resources or {}).get("/XObject")
        xobjects = xobjects.get_object() if xobjects is not None else {}
        for operands, operator in operations:
            now = bool(hidden and hidden[-1])
            if operator == b"BDC":
                hidden.append(now or self.marked(operands, resources))
                out.append((operands, operator))
                continue
            if operator == b"BMC":
                hidden.append(now)
                out.append((operands, operator))
                continue
            if operator == b"EMC":
                if hidden:
                    hidden.pop()
                out.append((operands, operator))
                continue
            if operator == b"q":
                stack.append(mode)
            elif operator == b"Q":
                mode = stack.pop() if stack else 0
            elif operator == b"Tr" and operands:
                mode = int(operands[0])
            if operator == b"Do" and operands:
                xobject = xobjects.get(operands[0])
                xobject = xobject.get_object() if xobject is not None else None
                if now or (xobject is not None and not _visible(xobject.get("/OC"), self.off)):
                    continue
                if xobject is not None and _text(xobject.get("/Subtype")) == "/Form":
                    self.form(xobjects, operands[0], resources)
                out.append((operands, operator))
                continue
            if not now:
                out.append((operands, operator))
                continue
            if operator in _PAINT_PATH:
                out.append(([], b"n"))
            elif operator in _SHOW_TEXT:
                invisible = 7 if mode >= 4 else 3
                out.append(([NumberObject(invisible)], b"Tr"))
                out.append((operands, operator))
                out.append(([NumberObject(mode)], b"Tr"))
            elif operator in (b"sh", b"INLINE IMAGE", b"BI"):
                continue
            else:
                out.append((operands, operator))
        return out

    def form(self, xobjects, name, page_resources):
        """A form XObject drawn on the page, its own content stripped -- once per form, replaced in the resources by a new stream."""
        from pypdf.generic import ContentStream, DecodedStreamObject, NameObject

        original = xobjects[name]
        key = _ref_id(original)
        if key in self.forms:
            xobjects[NameObject(name)] = self.forms[key]
            return
        form = original.get_object()
        resources = form.get("/Resources")
        resources = resources.get_object() if resources is not None else page_resources
        content = ContentStream(form, self.writer)
        operations = self.strip(content.operations, resources)
        fresh = DecodedStreamObject()
        for k, v in form.items():
            if k not in ("/Filter", "/DecodeParms", "/Length", "/OC"):
                fresh[NameObject(k)] = v
        new_content = ContentStream(None, self.writer)
        new_content.operations = operations
        fresh.set_data(new_content.get_data())
        reference = self.writer._add_object(fresh.flate_encode())
        self.forms[key] = reference
        self.forms[_ref_id(reference)] = reference  # drawn again: already stripped
        xobjects[NameObject(name)] = reference


def flatten_page(here, doc, page):
    """Page `page` of a PDF document as a PDF of its own, for the report: turned by the engineer's rotation (on top of its own /Rotate), the content of every group the document switched off taken out of the page and of the form XObjects it draws (see the module's note), an XObject whose own /OC is off dropped, and nothing optional left -- no /OCProperties, no /OC on what remains. Bytes; Typst sets them as the plan's background."""
    if doc["kind"] != "pdf":
        _fail("doc_kind", f"document {doc['id']} is not a PDF", file=doc["file"])
    entry = page_entry(doc, page)
    path = file_path(here, doc)
    turn, off = int(entry.get("rotation", 0)), _off_set(doc)
    # kept beside the views (v0.116): a dense page takes seconds to strip, and switching a layer back is a page the export has made before
    # keyed by the file as it is now, and not by the hash the document was imported with: a plan set replaced under the same name is a page to strip again
    target = cache_dir() / f"{_cache_key(dict(doc, sha256=model.file_hash(path)), 'flat', FLATTEN_VERSION, page, turn, off)}.pdf"
    if target.is_file():
        return target.read_bytes()
    content = _flatten(path, page, turn, off)
    _write_atomic(target, content)
    return content


def _flatten(path, page, turn, off):
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import ContentStream, NameObject

    reader = PdfReader(Path(path))   # a reader of its own: stripping a page reads its whole content, which must not hold the shared reader's lock (_PDF_LOCK) for seconds
    writer = PdfWriter()
    target = writer.add_page(reader.pages[page - 1])
    if off:
        resources = target.get("/Resources")
        resources = resources.get_object() if resources is not None else {}
        content = target.get_contents()
        if content is not None:
            stripper = _Stripper(writer, off)
            operations = stripper.strip(content.operations, resources)
            fresh = ContentStream(None, writer)
            fresh.operations = operations
            target.replace_contents(fresh)
            target.compress_content_streams()
    # nothing optional left: Typst would warn of optional content it draws whatever its state
    xobjects = (target.get("/Resources") or {}).get("/XObject")
    if xobjects is not None:
        for name, reference in list(xobjects.get_object().items()):
            obj = reference.get_object()
            if "/OC" in obj:
                del obj[NameObject("/OC")]
    if "/OCProperties" in writer._root_object:
        del writer._root_object[NameObject("/OCProperties")]
    if turn:
        target.rotate(turn)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


# --- CAD ----------------------------------------------------------------------------------------

def cad_source(here, doc):
    """The DXF a CAD document is read from: its file, or for a DWG the DXF the ODA File Converter made of it, cached outside the project by the DWG's SHA-256 and made again where it is missing."""
    path = file_path(here, doc)
    if path.suffix.lower() != ".dwg":
        return path
    target = cache_dir(CAD_CACHE_NAME) / f"{model.file_hash(path)}.dxf"
    if not target.is_file():
        cad.convert_dwg(path, target)
    return target


def _cad_svg(here, doc, page, unrotated=False):
    entry = page_entry(doc, page)
    text, width, height = cad.render_svg(cad_source(here, doc), entry["layout"], doc.get("layers_off", []))
    turn = 0 if unrotated else int(entry.get("rotation", 0))
    if turn:
        text = rotate_svg(text, turn, (width, height))
        if turn % 180:
            width, height = height, width
    return text, width, height


# --- turning an SVG or an image ---------------------------------------------------------------------

_ROOT = re.compile(r"<svg\b[^>]*>", re.S)


def _set_attribute(tag, name, value):
    pattern = re.compile(rf'(\s){re.escape(name)}\s*=\s*("[^"]*"|\'[^\']*\')')
    if pattern.search(tag):
        return pattern.sub(lambda m: f'{m.group(1)}{name}="{value}"', tag, count=1)
    return tag[:-1].rstrip("/") + f' {name}="{value}">' if not tag.endswith("/>") else tag[:-2] + f' {name}="{value}"/>'


def _transform(degrees, width, height):
    """The SVG matrix that turns a sheet of `width` × `height`, y down, by `degrees` clockwise onto a sheet starting at 0, 0."""
    return {90: f"matrix(0 1 -1 0 {height:g} 0)", 180: f"matrix(-1 0 0 -1 {width:g} {height:g})",
            270: f"matrix(0 -1 1 0 0 {width:g})"}[degrees % 360]


def rotate_svg(text, degrees, size=None):
    """An SVG document turned by `degrees` clockwise (a quarter turn or more): its root's viewBox, width and height made the turned sheet's and everything it draws wrapped in a group that turns it. `size` is its sheet (the viewBox's width and height), read from the document where not given; a viewBox not starting at 0, 0 is moved there first."""
    degrees = int(degrees) % 360
    if not degrees:
        return text
    m = _ROOT.search(text)
    if m is None:
        raise ValueError("not an SVG document")
    (width, height), _proportional, (x0, y0) = model._svg_size(text.encode("utf-8"))
    if size is not None:
        width, height = size
    tag = m.group(0)
    new_w, new_h = (height, width) if degrees % 180 else (width, height)
    tag = _set_attribute(tag, "viewBox", f"0 0 {new_w:g} {new_h:g}")
    w_attr = re.search(r'\swidth\s*=\s*"([^"]*)"', tag)
    h_attr = re.search(r'\sheight\s*=\s*"([^"]*)"', tag)
    if degrees % 180 and w_attr and h_attr:
        tag = _set_attribute(_set_attribute(tag, "width", h_attr.group(1)), "height", w_attr.group(1))
    close = text.rindex("</svg>")
    shift = f" translate({-x0:g} {-y0:g})" if (x0 or y0) else ""
    body = text[m.end():close]
    return (text[:m.start()] + tag + f'<g transform="{_transform(degrees, width, height)}{shift}">' + body + "</g>" + text[close:])


def _turned_svg(path, kind, degrees):
    """An image or an SVG file turned by `degrees`: an SVG, the image set in it as a data URI."""
    data = Path(path).read_bytes()
    if kind == "svg":
        return rotate_svg(data.decode("utf-8"), degrees)
    fmt = model.background_format(path)
    width, height = model.sheet_of(path, fmt, 1)
    mime = "image/png" if fmt == "png" else "image/jpeg"
    inner = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" '
             f'viewBox="0 0 {width:g} {height:g}" width="{width:g}" height="{height:g}">'
             f'<image x="0" y="0" width="{width:g}" height="{height:g}" xlink:href="data:{mime};base64,{base64.b64encode(data).decode("ascii")}"/></svg>')
    return rotate_svg(inner, degrees, (width, height))


# --- what the export sets -------------------------------------------------------------------------

def background(here, doc, page):
    """(content, format): what the report sets as the background of a plan drawn on page `page` -- bytes of a one-page PDF (`flatten_page`) for a PDF, the SVG text of the layout for a drawing, and for an image or an SVG the file as it is, or an SVG that turns it."""
    kind = doc["kind"]
    if kind == "pdf":
        return flatten_page(here, doc, page), "pdf"
    if kind == "cad":
        text, _w, _h = _cad_svg(here, doc, page)
        return text, "svg"
    path = file_path(here, doc)
    turn = rotation(doc, page)
    if turn:
        return _turned_svg(path, kind, turn), "svg"
    return path.read_bytes(), model.background_format(path)


def export_key(doc, page):
    """What the exported background of page `page` depends on beyond the file's SHA-256: its rotation and the layers switched off -- the export keeps a background it already wrote while these and the hash are unchanged."""
    return {"rotation": rotation(doc, page), "layers_off": _off_set(doc)}
