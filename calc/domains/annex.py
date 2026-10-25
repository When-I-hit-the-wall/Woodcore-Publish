"""Annexes: the documents a report draws on from outside -- a FEM program's print report first -- and the excerpts it shows of them (docs/domain/annexes.md §3.3undevicies, v0.115).

The engineer: «Cette partie va servir d'entrepôt pour des documents externes comme des ETA pour des moyens d'assemblage, des fiches technique de produit en bois type CLT ou pour des rapports d'impression sortie d'un programme de FEM. [...] le programme doit ensuite pouvoir utiliser le PDF source stocker dans ''Annexes'' pour montrer quelque chose dedans.»

Two kinds of source file, both written by Woodcore's «Annexes» tab and read here alone -- the arrangement every other editor tab has (docs/decisions.md §13):

**A source** is a PDF copied into the project, `Woodcore-Datei/annexes/sources/<id>.pdf`, beside its record `<id>.json`: its Nom · Description · ID (the window's rule, identity.py), and what of it the report's annexes carry -- the pages an excerpt is taken from (`used`, the default), every page (`all`), or nothing (`none`). Copied rather than referenced (the engineer's answer B3), so the project is whole on another machine and every archive of an export holds it; a new version of the print report is written **over** it (B4), and every excerpt then follows it.

**An excerpt** («Extrait», the engineer's word for what he first called an «aperçu») is a region of one page of a source: a diagram, a table. It is anchored on the **bookmark** the source carries for the title above it, and its frame is kept relative to that bookmark -- so when the print report comes out again with two more pages and every chapter renumbered, the excerpt finds its diagram all the same.

⚠️ **The anchor is a bookmark, not the title's text, and that was measured rather than assumed.** RFEM's own PDF export («Visionneuse du rapport», DynaPDF) draws every heading as vector paths: on a page of diagrams pypdf and QtPdf both read the numbers inside the diagrams and not one character of the titles above them. What it does write is an outline: one bookmark per heading of its navigator, 56 of them on the engineer's own report, each with its page and the height of the heading (`/FitBH`, `/Top`). A title is therefore found by its bookmark, its leading chapter number left out -- «5.16 CO1: Efforts internes M_y» was «6.4» in the previous version of the same report -- and, where one title is used several times («Charges de barre» under each load case), by the path of titles above it and then by its rank among those that remain (the engineer's answer C8: a title found several times is told apart by a mark of its own).

⚠️ **A PDF printed through «Microsoft Print to PDF» has neither text nor bookmarks** (the engineer's first report: 29 pages of JPEG tiles, 60 MB). Such a source still works, anchored on a page and a place; but nothing can follow it when it is replaced, so an excerpt anchored that way is refused by the report until the engineer has looked at it again in Woodcore and confirmed it (`confirmed`, the source's SHA-256 at that moment).

**Nothing is computed.** An excerpt is a picture of somebody else's calculation, so there is no {vars, steps, checks} record and nothing addresses one with show-calc: it is printed by `#show-extract`, and the pages it comes from by `#show-annexes`, at the end of the report, each linked to the other.

**The page is cropped here, never in Typst.** Typst 0.15.1 draws a page made of clipped image tiles wrongly as soon as it is placed away from the origin -- the content moves twice as far as its own clips (reproduced with Typst's own PNG export, so not a viewer's fault). So the export writes each excerpt as a one-page PDF whose MediaBox and CropBox ARE the frame (pypdf), which Typst then sets at the origin, exactly and in vector.

There is no Qt in this file, so the tab and a test script call the same functions.
"""

import copy
import hashlib
import io
import json
import math
import re
from pathlib import Path

import engine
import validation
from domains._common import fail as _fail  # one copy of the domains' helpers (spec 2026-10-19-base-saine-nettoyage, G4)

# Of a source record, of an excerpt and of the export (data/annexes.json).
SOURCE_SCHEMA_VERSION = "1.0"
# 1.1 is 1.0 with `file`, the name of its PDF in the project's Appendix/ -- the name it was added under, the engineer's (issue #64, D-11): written by a project laid out by folders, where the PDF lies there and no more beside its record; a 1.0 record is read as it is, its PDF `<id>.pdf` beside it
APPENDIX_SCHEMA_VERSION = "1.1"
SOURCE_SCHEMA_VERSIONS = (SOURCE_SCHEMA_VERSION, APPENDIX_SCHEMA_VERSION)
EXCERPT_SCHEMA_VERSION = "1.0"
EXPORT_SCHEMA_VERSION = "1.0"
# 1.1 is 1.0 with the excerpts' and the annexes' PDFs named from the Typst root (`/Appendix/Exports/E01.pdf`): written by a project laid out by folders, where they lie in Appendix/Exports/ (D-19)
ROOTED_EXPORT_VERSION = "1.1"

# The folder of the project's sources this module owns (project.SOURCE_FOLDERS), and its two sub-folders -- the two «dossiers» the engineer asked for inside «Annexes».
FOLDER = "annexes"
SOURCES = "sources"
EXCERPTS = "excerpts"

# What the export writes, beside data/calculations.json and the rest, and the folder of its PDFs.
EXPORT_FILE = "annexes.json"
EXPORT_FOLDER = "annexes"

# An id is a file name and the string the report quotes -- every other editor's rule.
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$")

# What a source's pages the annexes at the end of the report carry: the pages an excerpt is taken from, every page, or none (the engineer's answer E15). `used` by default, which keeps a 60 MB print report from travelling whole into every PDF and every archive.
MODES = ("used", "all", "none")
DEFAULT_MODE = "used"

# How an excerpt is anchored: on a bookmark of its source, or on a page and a place for a source that has none.
ANCHORS = ("bookmark", "page")

# A leading chapter number, which a print report renumbers as soon as a chapter is added: «5.16 », «3.1.1 », «A » -- and nothing else, so «CO1: Efforts» keeps its CO1.
CHAPTER = re.compile(r"^\s*(?:\d+(?:\.\d+)*\.?|[A-Z](?:\.\d+)*\.?)\s+(?=\S)")

# How far a frame may run past its page before it is refused, in points: a hair, so that a frame drawn to the page's very edge is not refused for rounding.
EDGE = 0.5

# The smallest frame, in points, either way: a frame smaller than this is a click, not a drag.
MIN_FRAME = 5.0


def _note(code, text, **args):
    return engine.Note(code, text, **args)


# --- the files ---------------------------------------------------------------------------

def folder(here):
    """The project's annexes folder: `Woodcore-Datei/annexes` (project.Project.annexes_dir)."""
    return Path(here.annexes_dir)


def sources_dir(here):
    return folder(here) / SOURCES


def excerpts_dir(here):
    return folder(here) / EXCERPTS


def appendix_dir(here):
    """The project's Appendix/, where the annexes' PDFs lie under their own names in a project laid out by folders (issue #64, D-11); None in one laid out before."""
    import project
    return here.typst_root / project.APPENDIX_FOLDER if getattr(here, "has_folders", False) else None


def pdf_path(here, sid, source=None):
    """The PDF of source `sid`: `Appendix/<file>` where its record names one (`source`, else read from its file) in a project laid out by folders, `<id>.pdf` beside its record otherwise -- where a record written before 1.1 still finds it."""
    folder = appendix_dir(here)
    if folder is not None:
        if source is None:
            record = sources_dir(here) / f"{sid}.json"
            try:
                source = json.loads(record.read_text(encoding="utf-8")) if record.is_file() else {}
            except (OSError, ValueError):
                source = {}
        name = source.get("file") if isinstance(source, dict) else None
        if name:
            return folder / name
    return sources_dir(here) / f"{sid}.pdf"


def appendix_name(here, sid, original, sources=None):
    """The name a source's new PDF is given in Appendix/: the file's own (`original`), unless another source's PDF has it or a file of that name lies there already -- the engineer's, which is never written over --, then `<sid>.pdf`."""
    sources = list_sources(here) if sources is None else sources
    taken = {str(s.get("file", "")).casefold() for other, s in sources.items() if other != sid}
    name = Path(original).name
    if name.casefold() in taken or (appendix_dir(here) / name).exists() or not name.lower().endswith(".pdf"):
        name = f"{sid}.pdf"
    return name


def copy_pdf(here, source, path):
    """`source` given the PDF at `path`: copied where its record says its PDF lies -- a source new in a project laid out by folders gets its name in Appendix/ first (`appendix_name`), a source replaced keeps its own --, written whole and moved into place, its SHA-256 and the name it came from brought up to date. Returns the source, changed; its record is not written (`write_source`)."""
    source = dict(source)
    folder = appendix_dir(here)
    if folder is not None and not source.get("file"):
        source["file"] = appendix_name(here, source["id"], Path(path).name)
    target = pdf_path(here, source["id"], source)
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".part")
    partial.write_bytes(Path(path).read_bytes())
    partial.replace(target)
    source.update(sha256=file_hash(target), original=Path(path).name)
    return source


def adoptable(here):
    """The source records `adopt` may rewrite, whose paths a migration backs up before it moves them."""
    return _paths(sources_dir(here))


def adopt(here):
    """In a project laid out by folders, every source whose PDF still lies beside its record as `<id>.pdf` -- one added before the layout by folders -- given a copy in Appendix/ under the name it was added under (`original`, `appendix_name`), and its record written at 1.1 to name it (issue #64, D-11): what the migration does, and every export after it. The copy beside the record is left where it is, read by nothing any more; copying twice copies nothing. A source whose PDF is missing is left as it is: the export says it. Returns [(the record rewritten, the copy made or None)]."""
    folder = appendix_dir(here)
    if folder is None:
        return []
    sources = list_sources(here)
    done = []
    for sid, source in sources.items():
        legacy = sources_dir(here) / f"{sid}.pdf"
        if source.get("file") or not legacy.is_file():
            continue
        payload = legacy.read_bytes()
        name = source.get("original") or legacy.name
        same = folder / Path(name).name
        if same.is_file() and same.read_bytes() == payload and same.name.casefold() not in {str(s.get("file", "")).casefold() for s in sources.values()}:
            target, made = same, None
        else:
            target = folder / appendix_name(here, sid, name, sources)
            if target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            partial = target.with_name(target.name + ".part")
            partial.write_bytes(payload)
            partial.replace(target)
            made = target
        source = dict(source, file=target.name)
        sources[sid] = source
        write_source(here, source)
        done.append((sources_dir(here) / f"{sid}.json", made))
    return done


def refresh_sources(here):
    """(the ids of the sources read again, the notes): in a project laid out by folders, every source whose PDF in Appendix/ was written over since the window last wrote its record -- by a file of the same name, from outside Woodcore (D-11) -- has its SHA-256 brought up to date, and is said; the export looks for every excerpt in it again as it always does. Nothing in a project laid out before, nor for a PDF that is missing, which the export says."""
    if appendix_dir(here) is None:
        return [], []
    changed, notes = [], []
    for sid, source in list_sources(here).items():
        path = pdf_path(here, sid, source)
        if not path.is_file():
            continue
        digest = file_hash(path)
        if digest != source.get("sha256"):
            write_source(here, dict(source, sha256=digest))
            changed.append(sid)
            notes.append(_note("annex_pdf_replaced", f"annex source {sid}: its PDF {path.name} has changed since it was added -- every excerpt is looked for in it again", source=sid, file=path.name))
    return changed, notes


def file_hash(path):
    """The SHA-256 of a file: what tells one version of a print report from the next."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reader(path):
    """The PDF at `path`, read by pypdf from its bytes -- so nothing holds the file open, and the tab may write a new version over it."""
    from pypdf import PdfReader
    try:
        return PdfReader(io.BytesIO(Path(path).read_bytes()))
    except Exception as exc:   # pypdf raises a dozen kinds for a file that is not a PDF
        raise validation.ValidationError(f"{Path(path).name}: could not be read as a PDF -- {exc}") from None


# --- the sources ---------------------------------------------------------------------------

def new_source(sid, name="", label="", original=""):
    return {
        "schema_version": SOURCE_SCHEMA_VERSION,
        "id": sid,
        "name": name,
        "label": label,
        "mode": DEFAULT_MODE,
        "original": original,
        "sha256": "",
    }


def check_source(source, where):
    """A source's record, checked: everything the schema walker cannot say. Raises a ValidationError naming the field."""
    if not isinstance(source, dict):
        _fail(where, "is not a JSON object")
    validation.validate_structure(source, "annex-source")
    if "file" in source and (not source["file"] or Path(source["file"]).name != source["file"]):
        _fail(where, f"file is {source['file']!r} -- the name of a PDF in Appendix/, without a folder")
    if not ID_PATTERN.match(source["id"]):
        _fail(where, f"id {source['id']!r} -- letters, digits and _ . + -, starting with a letter or a digit")
    if source["mode"] not in MODES:
        _fail(where, f"mode is {source['mode']!r} -- expected one of {', '.join(MODES)}")
    return source


def check_excerpt(excerpt, where):
    """An excerpt, checked: its anchor, its frame and the source it names. Raises a ValidationError naming the field."""
    if not isinstance(excerpt, dict):
        _fail(where, "is not a JSON object")
    validation.validate_structure(excerpt, "annex-excerpt")
    if not ID_PATTERN.match(excerpt["id"]):
        _fail(where, f"id {excerpt['id']!r} -- letters, digits and _ . + -, starting with a letter or a digit")
    if not ID_PATTERN.match(excerpt["source"]):
        _fail(where, f"source {excerpt['source']!r} is not a source's id")
    anchor = excerpt["anchor"]
    if anchor["kind"] not in ANCHORS:
        _fail(where, f"anchor kind is {anchor['kind']!r} -- expected one of {', '.join(ANCHORS)}")
    if anchor["kind"] == "bookmark":
        path = anchor.get("path")
        if not isinstance(path, list) or not path or not all(isinstance(t, str) and t.strip() for t in path):
            _fail(where, "a bookmark anchor names its path: the titles from the outermost to the bookmark itself")
        occurrence = anchor.get("occurrence", 1)
        if isinstance(occurrence, bool) or not isinstance(occurrence, int) or occurrence < 1:
            _fail(where, f"anchor occurrence is {occurrence!r} -- a whole number of 1 or more")
    else:
        page = anchor.get("page")
        if isinstance(page, bool) or not isinstance(page, int) or page < 1:
            _fail(where, f"a page anchor names its page, a whole number of 1 or more -- got {page!r}")
    frame = excerpt["frame"]
    for key in ("x", "y", "w", "h"):
        value = frame[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            _fail(where, f"frame.{key} is {value!r} -- a number of points")
    if frame["w"] < MIN_FRAME or frame["h"] < MIN_FRAME:
        _fail(where, f"the frame is {frame['w']:g} × {frame['h']:g} pt -- at least {MIN_FRAME:g} pt either way")
    return excerpt


def _read_json(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _fail(Path(path).name, f"could not be read -- {exc}")
    return data


def read_source(path):
    path = Path(path)
    source = check_source(_read_json(path), path.name)
    if source["id"] != path.stem:
        _fail(path.name, f"id is {source['id']!r} but the file is named {path.name} -- they must agree")
    return source


def read_excerpt(path):
    path = Path(path)
    excerpt = check_excerpt(_read_json(path), path.name)
    if excerpt["id"] != path.stem:
        _fail(path.name, f"id is {excerpt['id']!r} but the file is named {path.name} -- they must agree")
    return excerpt


def _paths(directory):
    directory = Path(directory)
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*.json"), key=lambda p: p.name.lower())


def list_sources(here):
    """{id: source}, in file-name order -- the order the annexes are lettered in."""
    return {path.stem: read_source(path) for path in _paths(sources_dir(here))}


def list_excerpts(here):
    """{id: excerpt}, in file-name order."""
    return {path.stem: read_excerpt(path) for path in _paths(excerpts_dir(here))}


def write_source(here, source):
    """The source's record, written: at 1.1 where it names its PDF in Appendix/ (`file`), at the version it was read as otherwise."""
    if "file" in source:
        source = dict(source, schema_version=APPENDIX_SCHEMA_VERSION)
    check_source(source, f"{source.get('id')}.json")
    engine.write_json(sources_dir(here) / f"{source['id']}.json", source)


def write_excerpt(here, excerpt):
    check_excerpt(excerpt, f"{excerpt.get('id')}.json")
    engine.write_json(excerpts_dir(here) / f"{excerpt['id']}.json", excerpt)


# --- the outline ---------------------------------------------------------------------------

def title_key(title):
    """A bookmark's title as it is compared: its leading chapter number left out, its spaces collapsed, its case folded -- «5.16 CO1: Efforts internes M_y , En direction -Y» and «6.4 co1: efforts internes M_y, En direction -Y» are one title."""
    text = CHAPTER.sub("", str(title or ""), count=1)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,;:])", r"\1", text)
    return text.casefold()


def page_box(page):
    """(left, bottom, right, top) of the page as a viewer shows it: its CropBox, its MediaBox where it has none."""
    box = page.cropbox
    return float(box.left), float(box.bottom), float(box.right), float(box.top)


def outline(pdf):
    """Every bookmark of the PDF, in document order: {title, key, path, keys, page (1-based), top} -- `top` measured **down** from the top of the page in points, so it reads as the page is read; `path` the titles from the outermost to this one. An empty list where the PDF has no outline, or one pypdf cannot follow."""
    try:
        items = pdf.outline
    except Exception:  # broad: pypdf raises a family of its own for an outline it cannot follow -- no bookmarks, which the annex's own check says
        return []
    found = []

    def walk(nodes, ancestors):
        last = None
        for node in nodes:
            if isinstance(node, list):
                walk(node, ancestors + ([last] if last is not None else []))
                continue
            try:
                title = str(node.title)
                index = pdf.get_destination_page_number(node)
            except Exception:  # broad: pypdf's family again -- a bookmark that cannot be followed is left out, the others kept
                last = None
                continue
            if index is None or index < 0:
                last = None
                continue
            left, bottom, right, top_edge = page_box(pdf.pages[index])
            top = node.get("/Top") if hasattr(node, "get") else None
            try:
                top = float(top) if top is not None else None
            except (TypeError, ValueError):
                top = None
            down = 0.0 if top is None else max(0.0, min(top_edge - bottom, top_edge - top))
            entry = {
                "title": title,
                "key": title_key(title),
                "path": [a["title"] for a in ancestors] + [title],
                "keys": [a["key"] for a in ancestors] + [title_key(title)],
                "page": index + 1,
                "top": round(down, 3),
            }
            found.append(entry)
            last = entry

    walk(items, [])
    return found


def page_count(pdf):
    return len(pdf.pages)


def has_text(pdf, pages=3):
    """True where the first pages carry any text at all -- what tells a PDF exported by its program from one printed through «Microsoft Print to PDF»."""
    for page in list(pdf.pages)[:pages]:
        try:
            if (page.extract_text() or "").strip():
                return True
        except Exception:  # broad: pypdf's family again -- a page whose text cannot be read counts as none
            continue
    return False


def bookmark_at(marks, page, down, grace=1.0):
    """The bookmark a click on `page` at `down` points below the top of it names: the lowest bookmark of that page standing at or above the click -- a title is drawn just under the height its bookmark gives. None where no bookmark of that page stands above it."""
    above = [m for m in marks if m["page"] == page and m["top"] <= down + grace]
    return max(above, key=lambda m: m["top"]) if above else None


def anchor_for(marks, mark):
    """The anchor that finds `mark` again: its path, and its rank among the bookmarks that path alone does not tell apart (the engineer's answer C8)."""
    same = candidates(marks, mark["keys"])
    occurrence = next((i for i, m in enumerate(same, 1) if m is mark or (m["page"], m["top"], m["keys"]) == (mark["page"], mark["top"], mark["keys"])), 1)
    return {"kind": "bookmark", "path": list(mark["path"]), "occurrence": occurrence}


def candidates(marks, keys):
    """The bookmarks a path of title keys can mean, narrowed one level of parent at a time: a title first, then its parent, then its parent's parent -- as long as there is more than one and the next level still leaves some. A parent renamed in the new version therefore costs nothing where the title alone is unique."""
    keys = [k for k in keys if k]
    if not keys:
        return []
    found = [m for m in marks if m["key"] == keys[-1]]
    depth = 2
    while len(found) > 1 and depth <= len(keys):
        narrower = [m for m in found if m["keys"][-depth:] == keys[-depth:]]
        if not narrower:
            break
        found = narrower
        depth += 1
    return found


# --- three ways to make an excerpt (issue #16) ------------------------------------------------
# The engineer, 08.10.2026: «Extraire en dessinant un cadre», «en choisissant un nombre de pages : chaque page devient son propre extrait», «en choisissant un cadre trouvé dans la page : Woodcore détecte les cadres tracés dans le PDF (p. ex. une impression RFEM) et on en clique un». Each gives an excerpt of the one shape the schema knows -- an anchor and a frame on one page (CON-002) --, worked out here, without Qt, and written by the tab through `write_excerpt` like any other.

# The smallest rectangle of a page's drawing offered as a frame, in points either way: a print report's tables are cells of a few points, and a frame worth an excerpt is a diagram, a table, a block.
MIN_FOUND = 20.0

# How deep a page's drawings are followed into the forms they call: a print report nests two or three, and a form that calls itself is not followed for ever.
FOUND_DEPTH = 8

# A rectangle that covers this share of its page both ways is the page's own ground, never offered.
PAGE_SHARE = 0.98

# The operators that paint a path -- a rectangle found is one that is drawn, never a clip (`W n`) nor a path left unpainted.
_PAINT = {"S", "s", "f", "F", "f*", "B", "B*", "b", "b*"}
_CLOSE_AND_PAINT = {"s", "b", "b*"}


FRAME_GRACE = 12.0   # pt: how far under a frame's top the title it is drawn round may stand and still anchor it (issue #16) -- a click on a title keeps bookmark_at's single point


def frame_excerpt(marks, page, rect, sha):
    """The anchor and the frame of an excerpt drawn as `rect` -- [x, down, w, h] in points from the top-left corner of `page` -- with nothing chosen before it (issue #16, «chaque cadre dessiné crée un extrait»): anchored on the lowest bookmark of the page standing above the frame's top -- or under it by `FRAME_GRACE` at most, the title the frame is drawn round --, the frame measured from it (a negative `y` where the frame starts above its title); on the page itself where no bookmark stands above, then confirmed on this version of the source (`sha`), which an excerpt anchored on a page must be. {anchor, frame, confirmed?}."""
    x, down, w, h = (float(v) for v in rect)
    # a frame is drawn from a little above the title it holds: a bookmark standing under its top by up to FRAME_GRACE is still the frame's, never the one before it
    mark = bookmark_at(marks or [], page, down, grace=min(FRAME_GRACE, h)) if marks else None
    if mark is not None:
        return {"anchor": anchor_for(marks, mark), "frame": {"x": round(x, 2), "y": round(down - mark["top"], 2), "w": round(w, 2), "h": round(h, 2)}}
    return {"anchor": {"kind": "page", "page": int(page)}, "frame": {"x": round(x, 2), "y": round(down, 2), "w": round(w, 2), "h": round(h, 2)}, "confirmed": sha}


def page_excerpt(pdf, page, sha):
    """The anchor and the frame of an excerpt that is page `page` whole (issue #16, «chaque page devient son propre extrait»): anchored on the page, framed by its crop box, confirmed on this version of the source. {anchor, frame, confirmed}."""
    left, bottom, right, top = page_box(pdf.pages[page - 1])
    return {"anchor": {"kind": "page", "page": int(page)}, "frame": {"x": 0.0, "y": 0.0, "w": round(right - left - 0.01, 2), "h": round(top - bottom - 0.01, 2)}, "confirmed": sha}


def excerpt_name(marks, excerpt, page_word):
    """The name an excerpt made in one gesture is given: its title without its chapter number where it is anchored on a bookmark -- «Charges de barre» --, «<page_word> <n>» where it is anchored on a page."""
    anchor = excerpt["anchor"]
    if anchor["kind"] == "bookmark":
        title = CHAPTER.sub("", anchor["path"][-1]).strip()
        if title:
            return title
    return f"{page_word} {excerpt_page(marks, excerpt)}"


def excerpt_page(marks, excerpt):
    """The page an excerpt made here lies on: its anchor's page, or its bookmark's."""
    anchor = excerpt["anchor"]
    if anchor["kind"] == "page":
        return anchor["page"]
    same = candidates(marks, [title_key(t) for t in anchor["path"]])
    occurrence = anchor.get("occurrence", 1)
    return same[occurrence - 1]["page"] if 0 < occurrence <= len(same) else 1


def free_id(stem, taken, fallback="Annexe"):
    """An id made of `stem` -- letters, digits and _ . + - (ID_PATTERN) -- that none of `taken` is, case aside: `stem`, else `stem-2`, `stem-3`… A batch passes the ids it has already given, so two excerpts of one gesture never share one."""
    base = re.sub(r"[^A-Za-z0-9_.+-]+", "-", str(stem or "")).strip("-._+") or fallback
    if not ID_PATTERN.match(base):
        base = fallback + "-" + base
    lowered = {str(t).lower() for t in taken}
    found, n = base, 2
    while found.lower() in lowered:
        found, n = f"{base}-{n}", n + 1
    return found


def _times(a, b):
    """The matrix `a` then `b`, PDF's [a b c d e f] order."""
    return (a[0] * b[0] + a[1] * b[2], a[0] * b[1] + a[1] * b[3],
            a[2] * b[0] + a[3] * b[2], a[2] * b[1] + a[3] * b[3],
            a[4] * b[0] + a[5] * b[2] + b[4], a[4] * b[1] + a[5] * b[3] + b[5])


def _apply(m, x, y):
    return (m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5])


def _box_of(points):
    """The rectangle a closed path of four corners is, axis-aligned, as (x0, y0, x1, y1) -- None for any other shape: a slanted quadrilateral, a triangle, a curve."""
    pts = list(points)
    if len(pts) == 5 and abs(pts[0][0] - pts[-1][0]) < 0.01 and abs(pts[0][1] - pts[-1][1]) < 0.01:
        pts = pts[:4]
    if len(pts) != 4:
        return None
    xs = sorted({round(p[0], 2) for p in pts})
    ys = sorted({round(p[1], 2) for p in pts})
    if len(xs) != 2 or len(ys) != 2:
        return None
    corners = {(round(p[0], 2), round(p[1], 2)) for p in pts}
    if corners != {(xs[0], ys[0]), (xs[1], ys[0]), (xs[1], ys[1]), (xs[0], ys[1])}:
        return None
    return xs[0], ys[0], xs[1], ys[1]


def find_rects(pdf, page, min_size=MIN_FOUND):
    """The rectangles drawn on page `page` of `pdf` (pypdf's reader) -- a print report's frames round its diagrams and tables --, as [x, down, w, h] in points from the page's top-left corner, the measure of a frame, the smallest first; none smaller than `min_size` either way, nor the page's own ground (PAGE_SHARE).

    Read from the page's content as it is painted (issue #16, D-007: pypdf, no new dependency): a rectangle is a `re`, or a path of four straight sides closing on itself (`m l l l h`), **painted** -- stroked or filled, never a clip (`W n`) --, carried through the transformations `cm` sets and the forms `Do` calls, each with its own `/Matrix` and resources, at most FOUND_DEPTH deep and never twice into the same form. A page printed as a picture (a PDF printer's tiles) has none, which is no error."""
    from pypdf.generic import ContentStream
    the_page = pdf.pages[page - 1]
    left, bottom, right, top = page_box(the_page)
    page_w, page_h = right - left, top - bottom
    found = []

    def walk(content, resources, ctm, depth, inside):
        try:
            operations = ContentStream(content, pdf).operations
        except Exception:  # broad: a stream pypdf cannot read offers nothing, and stops nothing -- pypdf raises what it likes on a broken stream
            return
        saved, subpaths, current = [], [], None
        for operands, operator in operations:
            op = operator.decode("latin-1") if isinstance(operator, bytes) else str(operator)
            try:
                if op == "q":
                    saved.append(ctm)
                elif op == "Q":
                    ctm = saved.pop() if saved else ctm
                elif op == "cm" and len(operands) == 6:
                    ctm = _times(tuple(float(v) for v in operands), ctm)
                elif op == "re" and len(operands) == 4:
                    x, y, w, h = (float(v) for v in operands)
                    subpaths.append(([_apply(ctm, x, y), _apply(ctm, x + w, y), _apply(ctm, x + w, y + h), _apply(ctm, x, y + h)], True))
                    current = None
                elif op == "m" and len(operands) == 2:
                    current = [_apply(ctm, float(operands[0]), float(operands[1]))]
                    subpaths.append((current, False))
                elif op == "l" and len(operands) == 2 and current is not None:
                    current.append(_apply(ctm, float(operands[0]), float(operands[1])))
                elif op in ("c", "v", "y"):
                    if subpaths:
                        subpaths[-1] = (subpaths[-1][0], None)   # a curve: not a rectangle, whatever closes it
                    current = None
                elif op == "h":
                    if subpaths and subpaths[-1][1] is not None:
                        subpaths[-1] = (subpaths[-1][0], True)
                    current = None
                elif op in _PAINT:
                    for points, closed in subpaths:
                        if closed is None:
                            continue
                        if closed or op in _CLOSE_AND_PAINT or (len(points) == 5 and points[0] == points[-1]):
                            box = _box_of(points)
                            if box is not None:
                                found.append(box)
                    subpaths, current = [], None
                elif op == "n":
                    subpaths, current = [], None   # a clip's path, ended unpainted
                elif op == "Do" and operands and depth < FOUND_DEPTH and resources is not None:
                    xobjects = resources.get("/XObject")
                    xobjects = xobjects.get_object() if xobjects is not None else None
                    form = xobjects.get(operands[0]) if xobjects is not None else None
                    if form is None:
                        continue
                    ref = getattr(form, "idnum", None)
                    form = form.get_object()
                    if form.get("/Subtype") != "/Form" or (ref is not None and ref in inside):
                        continue
                    matrix = tuple(float(v) for v in form.get("/Matrix", [1, 0, 0, 1, 0, 0]))
                    own = form.get("/Resources")
                    walk(form, own.get_object() if own is not None else resources, _times(matrix, ctm), depth + 1, inside | ({ref} if ref is not None else set()))
            except (TypeError, ValueError, KeyError, AttributeError):
                continue   # an operator with operands it should not have: skipped, the rest of the page read

    resources = the_page.get("/Resources")
    content = the_page.get_contents()
    if content is None:
        return []
    walk(content, resources.get_object() if resources is not None else None, (1.0, 0.0, 0.0, 1.0, 0.0, 0.0), 0, frozenset())
    out, seen = [], set()
    for x0, y0, x1, y1 in found:
        rect = [round(x0 - left, 2), round(top - y1, 2), round(x1 - x0, 2), round(y1 - y0, 2)]
        if rect[2] < min_size or rect[3] < min_size:
            continue
        if rect[2] >= PAGE_SHARE * page_w and rect[3] >= PAGE_SHARE * page_h:
            continue
        key = tuple(round(v, 1) for v in rect)
        if key in seen:
            continue
        seen.add(key)
        out.append(rect)
    return sorted(out, key=lambda r: (r[2] * r[3], r[1], r[0]))


def find_rects_in(data, page, min_size=MIN_FOUND):
    """`find_rects` on a PDF given by its bytes, read by a reader of its own -- what the window asks off its own thread, pypdf's readers not being shared between threads."""
    from pypdf import PdfReader
    return find_rects(PdfReader(io.BytesIO(data)), page, min_size)


def rects_at(rects, x, down):
    """The rectangles of `rects` (find_rects) that hold the point (x, down), the smallest first -- the one under the pointer, then the ones round it, which Alt and the wheel climb to (D-013)."""
    return [r for r in rects if r[0] <= x <= r[0] + r[2] and r[1] <= down <= r[1] + r[3]]


# --- where an excerpt lies ------------------------------------------------------------------

def resolve(excerpt, pdf, sha, marks=None):
    """Where the excerpt lies in this version of its source: {ok, page, down, rect, title, note}.

    `down` is the anchor's height below the top of the page, `rect` the frame as [x, y, w, h] below and right of the page's top-left corner, in points -- the page's own measure, what the annex page draws its frame at. `note` is None where it resolves, otherwise the engine.Note saying why not, which is also what the report refuses the excerpt with (the engineer's answer C9: an excerpt that cannot be found stops the report rather than printing another diagram).
    """
    where = f"excerpt {excerpt['id']}"
    anchor = excerpt["anchor"]
    pages = page_count(pdf)
    title = ""
    if anchor["kind"] == "bookmark":
        marks = outline(pdf) if marks is None else marks
        wanted = " › ".join(anchor["path"])
        if not marks:
            return _unresolved(_note("annex_no_bookmarks", f"{where}: its source {excerpt['source']} carries no bookmark -- the excerpt is anchored on «{wanted}»; export the report from its own program rather than through a PDF printer, or anchor the excerpt on its page", excerpt=excerpt["id"], source=excerpt["source"], title=wanted))
        same = candidates(marks, [title_key(t) for t in anchor["path"]])
        occurrence = anchor.get("occurrence", 1)
        if not same:
            return _unresolved(_note("annex_not_found", f"{where}: its source {excerpt['source']} no longer has the title «{wanted}» -- open the excerpt in Woodcore's Annexes tab and pick its title again", excerpt=excerpt["id"], source=excerpt["source"], title=wanted))
        if occurrence > len(same):
            return _unresolved(_note("annex_occurrence", f"{where}: «{wanted}» occurs {len(same)} time(s) in its source {excerpt['source']}, and the excerpt is its occurrence {occurrence} -- pick its title again", excerpt=excerpt["id"], source=excerpt["source"], title=wanted, count=len(same), occurrence=occurrence))
        mark = same[occurrence - 1]
        page, down, title = mark["page"], mark["top"], mark["title"]
    else:
        page, down = anchor["page"], 0.0
        if page > pages:
            return _unresolved(_note("annex_page_gone", f"{where}: its source {excerpt['source']} has {pages} page(s) and the excerpt is on page {page}", excerpt=excerpt["id"], source=excerpt["source"], page=page, pages=pages))
        if excerpt.get("confirmed", "") != sha:
            return _unresolved(_note("annex_unconfirmed", f"{where}: its source {excerpt['source']} was replaced since the excerpt was placed on its page, and a source without bookmarks cannot be followed -- look at the excerpt again in Woodcore's Annexes tab and confirm it", excerpt=excerpt["id"], source=excerpt["source"]), page=page)
    pdf_page = pdf.pages[page - 1]
    if int(pdf_page.rotation or 0) % 360:
        return _unresolved(_note("annex_rotated", f"{where}: page {page} of its source {excerpt['source']} is turned by /Rotate {pdf_page.rotation} -- an excerpt of a turned page is not supported yet", excerpt=excerpt["id"], source=excerpt["source"], page=page), page=page)
    left, bottom, right, top_edge = page_box(pdf_page)
    width, height = right - left, top_edge - bottom
    frame = excerpt["frame"]
    rect = [frame["x"], down + frame["y"], frame["w"], frame["h"]]
    if rect[0] < -EDGE or rect[1] < -EDGE or rect[0] + rect[2] > width + EDGE or rect[1] + rect[3] > height + EDGE:
        return _unresolved(_note("annex_outside", f"{where}: its frame runs past page {page} of its source {excerpt['source']} -- the title moved too far down the page; draw the frame again in Woodcore's Annexes tab", excerpt=excerpt["id"], source=excerpt["source"], page=page), page=page)
    rect = [round(max(0.0, rect[0]), 3), round(max(0.0, rect[1]), 3),
            round(min(rect[2], width - max(0.0, rect[0])), 3), round(min(rect[3], height - max(0.0, rect[1])), 3)]
    return {"ok": True, "page": page, "down": round(down, 3), "rect": rect, "size": [round(width, 3), round(height, 3)], "title": title, "note": None}


def _unresolved(note, page=None):
    return {"ok": False, "page": page, "down": None, "rect": None, "size": None, "title": "", "note": note}


# The version a PDF the export writes declares. RFEM's «Visionneuse du rapport» writes PDF 2.0, and Typst refuses to set a PDF of a higher version than the one it exports (1.7 by default: «the version of the PDF is too high»). Raising the report's own target would have to be done in every build route at once -- woodcore-cli, Woodcore's «Exporter PDF» and Tinymist's own settings -- so the pages the export writes declare 1.7 instead: they are pages copied as they stand, and the one engineer's report they were measured on (29 pages, DynaPDF 4.0) draws identically either way.
PDF_HEADER = b"%PDF-1.7"


def _writer():
    from pypdf import PdfWriter
    return PdfWriter()


def _bytes(writer):
    """What `writer` holds, declaring PDF_HEADER -- set here, just before writing, since pypdf raises the header to the source's own as each page is added."""
    writer.pdf_header = PDF_HEADER
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def crop(pdf, page, rect):
    """The bytes of a one-page PDF whose page IS the frame: its MediaBox and its CropBox moved onto `rect` ([x, y, w, h] below and right of the page's top-left corner), so Typst sets it at the origin -- see the module's docstring for why the crop is not left to Typst."""
    from pypdf.generic import RectangleObject
    writer = _writer()
    added = writer.add_page(pdf.pages[page - 1])
    left, bottom, right, top_edge = page_box(added)
    x, y, w, h = rect
    box = RectangleObject([left + x, top_edge - y - h, left + x + w, top_edge - y])
    added.mediabox = box
    added.cropbox = box
    return _bytes(writer)


def pages_of(pdf, numbers):
    """The bytes of a PDF holding those pages of `pdf`, in that order -- a source's annex."""
    writer = _writer()
    for number in numbers:
        writer.add_page(pdf.pages[number - 1])
    return _bytes(writer)


# --- the export -----------------------------------------------------------------------------

_digest = engine.digest   # the one fingerprint (the same bytes as this module's own until v0.120: a list and a tuple are one JSON array)


def prepare(here, previous=None):
    """Every source and excerpt, checked, resolved and built: (data, files, warnings). Nothing is written here, so an export that fails leaves data/ as it was.

    `previous` is the export already on disk ({} where there is none): a PDF whose inputs -- the source's SHA-256, the page, the frame -- have not changed is kept as it is rather than written again, pypdf being free to write the same page with other bytes (plan.py's own rule for a plan's background).
    """
    previous = previous or {}
    data_dir = Path(here.data_dir)
    place = engine.Figures(data_dir, "annex", here)   # Appendix/Exports/ in a project laid out by folders, data/annexes/ otherwise (D-19)
    sources, excerpts = list_sources(here), list_excerpts(here)
    notes, files = [], {}
    records = {"sources": {}, "excerpts": {}}
    opened = {}
    for sid, source in sources.items():
        path = pdf_path(here, sid, source)
        if not path.is_file():
            notes.append(_note("annex_pdf_missing", f"annex source {sid}: its PDF {path.name} is missing from {path.parent.name}/ -- add it again in Woodcore's Annexes tab", source=sid))
            opened[sid] = None
            continue
        pdf = reader(path)
        opened[sid] = (pdf, file_hash(path), outline(pdf))
    for eid, excerpt in excerpts.items():
        sid = excerpt["source"]
        record = {
            "name": excerpt.get("name", ""), "label": excerpt.get("label", ""), "source": sid,
            "resolved": False, "reason": "", "page": None, "title": "", "file": "", "size": None, "rect": None,
        }
        if sid not in sources:
            note = _note("annex_source_gone", f"excerpt {eid}: its source {sid} is not in the project any more", excerpt=eid, source=sid)
        elif opened[sid] is None:
            note = _note("annex_source_unreadable", f"excerpt {eid}: its source {sid} has no PDF", excerpt=eid, source=sid)
        else:
            pdf, sha, marks = opened[sid]
            where = resolve(excerpt, pdf, sha, marks)
            note = where["note"]
            record["page"] = where["page"]
            if note is None:
                name = place.name(f"{eid}.pdf")
                inputs = _digest(sha, where["page"], where["rect"])
                kept = previous.get("excerpts", {}).get(eid, {})
                if kept.get("inputs") == inputs and kept.get("file") == name and place.path(name).is_file():
                    files[name] = place.path(name).read_bytes()
                else:
                    files[name] = crop(pdf, where["page"], where["rect"])
                record.update(resolved=True, title=where["title"], file=name, rect=where["rect"],
                              size=[where["rect"][2], where["rect"][3]], page_size=where["size"], inputs=inputs)
        if note is not None:
            notes.append(note)
            record["reason"] = str(note)
        records["excerpts"][eid] = record
    for sid, source in sources.items():
        record = {"name": source.get("name", ""), "label": source.get("label", ""), "mode": source["mode"],
                  "pages": 0, "bookmarks": 0, "annex": None, "excerpts": sorted(e for e, x in excerpts.items() if x["source"] == sid)}
        if opened.get(sid) is not None:
            pdf, sha, marks = opened[sid]
            record["pages"], record["bookmarks"], record["sha256"] = page_count(pdf), len(marks), sha
            if source["mode"] == "all":
                numbers = list(range(1, page_count(pdf) + 1))
            elif source["mode"] == "used":
                numbers = sorted({x["page"] for x in records["excerpts"].values() if x["source"] == sid and x["resolved"]})
            else:
                numbers = []
            if numbers:
                name = place.name(f"{sid}-annex.pdf")
                inputs = _digest(sha, numbers)
                kept = previous.get("sources", {}).get(sid, {}).get("annex") or {}
                if kept.get("inputs") == inputs and kept.get("file") == name and place.path(name).is_file():
                    files[name] = place.path(name).read_bytes()
                else:
                    files[name] = pages_of(pdf, numbers)
                sizes = []
                for number in numbers:
                    left, bottom, right, top_edge = page_box(pdf.pages[number - 1])
                    sizes.append([round(right - left, 3), round(top_edge - bottom, 3)])
                record["annex"] = {"file": name, "pages": numbers, "sizes": sizes, "inputs": inputs}
        records["sources"][sid] = record
    data = {"schema_version": ROOTED_EXPORT_VERSION if place.here is not None else EXPORT_SCHEMA_VERSION, **records}
    validation.validate_structure(data, "annexes")
    validation.validate_annexes_business(data)
    return data, files, notes


def write(data, files, data_dir):
    """The only writer: data/annexes.json and the PDFs of the excerpts and the annexes -- Appendix/Exports/ in a project laid out by folders, data/annexes/ otherwise (engine.Figures) --, those it no longer needs removed: only what the last export wrote, never a file of the engineer's. A PDF whose bytes have not changed is left alone."""
    data_dir = Path(data_dir)
    engine.figures(data_dir, "annex").write(files, previous_export(data_dir))
    engine.write_json(data_dir / EXPORT_FILE, data)


def previous_export(data_dir):
    """The export already on disk, or {} -- what `prepare` keeps unchanged PDFs by."""
    try:
        return json.loads((Path(data_dir) / EXPORT_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def export(here):
    """prepare + write, and the warnings -- what Woodcore runs when a source or an excerpt is saved, so the report sees it without the whole export being run again."""
    data, files, notes = prepare(here, previous_export(here.data_dir))
    write(data, files, here.data_dir)
    return notes


def empty():
    """The export of a project that holds no annex: what a new project's report reads (export_all.seed)."""
    return {"schema_version": EXPORT_SCHEMA_VERSION, "sources": {}, "excerpts": {}}


def snapshot(value):
    return copy.deepcopy(value)
