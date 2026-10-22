"""The export sheets of a project (v0.114): a plan sheet A0 to A6 on which the position plans drawn in Woodcore are set at a chosen scale, beside a legend, a schematic section, texts of the engineer's own and a title block -- STE Compact 02's plan de positions.

**A sheet is a .typ file**, `<Typst root>/Plans/<id>.typ`, compiled to `Plans/<id>.pdf` beside it with the project's own engine (`#import "/commands.typ": *`): the project's folder for a project in three documents, the report's folder for a report alone (`Project.typst_root`). **The .typ is the source of truth.** Every thing on it is one object of lib/sheet.typ, written between two tags in the canonical form calc/typst_objects.py reads and writes back -- the page (`sheet-page`, the show rule `#show: sheet.with(...)`), a text, a plan (`sheet-viewport`), a fire-protection plan (`sheet-fire-viewport`, v0.115), a section, the legend (and the fire plans' own, `sheet-fire-legend`), the title block -- so what the engineer edits in VS Code is read back here, and what Woodcore writes changes the object it edits and nothing else of the file.

**A sheet is of one kind** (v0.116): a sheet of position plans or a sheet of fire-protection plans, never both -- the engineer: «le plan de position ne doit absolument pas être mélangé avec le plan d'incendie». The page says which (`#show: sheet.with(..., kind: "fire")`); a sheet written before v0.116 says nothing, and its kind is read off the objects it holds -- any fire-protection object makes it a fire sheet (`sheet_kind`). An object of the other kind is refused (`wrong_kind`), and the sheets are listed per kind (`list_sheets(kind=)`).

**A PDF bundle** (v0.116, «Création d'un PDF»): a name and an ordered list of sheets of one kind, kept in `Plans/bundles.json` (`woodcore-sheet-bundles` 1.0, written whole and atomically, checked as it is read). Exporting a bundle compiles each of its sheets into its own PDF, as `compile` does, and then writes `Plans/<name>.pdf`, their pages one after the other in the bundle's order -- merged with pypdf rather than written as one Typst document including the sheets, because each sheet is a document of its own whose states (`sheet-plans.final()`, `sheet-scales.final()`: the legend's symbols, the title block's scales) must stay its own: one document would give every sheet the legend and the scales of all of them.

**The list of the positions** (v0.116): the object `sheet-position-list` (`add_position_list`), and a sheet of its own, A4 portrait, holding the list alone (`new_position_list_sheet`).

Every function takes the project (`project.Project`) and a sheet's id; a refusal is a SheetError with a code (CODES), an English sentence and its values, which the window turns into its own words. An object's own refusals are typst_objects' ObjectError and ModelError, passed through.

Qt-free.
"""

import json
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

import proc
import documents
import project as project_module
import typst_objects as to
from i18n import strings

# The sheets' folder in a project laid out before the folders of issue #64: `Plans/` at the top of the Typst root, the sheets of both kinds together. Laid out by folders, a sheet lies in the exports of its kind's plan tab -- `Plans/Position-plan/Exports/`, `Plans/Fire-plan/Exports/` (spec 2026-10-15 D-06, D-17) -- and its id is still one for the whole project (`folder`, `path`).
FOLDER = project_module.PLANS_FOLDER
# The plan tab each kind of sheet belongs to (project.DRAWING_FOLDERS).
KIND_TABS = {"position": "plan", "fire": "fire"}
# A sheet's id is its file's name: letters, digits and `_ . + -`, as a connector's (the id is the file name).
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$")
FORMATS = to.SHEET_FORMATS
LANGUAGES = ("de", "fr", "en")
# The id of the page object of every sheet Woodcore writes.
PAGE_ID = "page"
# A sheet's import of the engine is the project's own, from the Typst root (calc/documents.py `root_import_line`): `/000-Typst-Config/commands.typ` in a project laid out by folders (issue #64), `/commands.typ` before.

CODES = ("bad_id", "exists", "no_sheet", "no_page", "bad_format", "bad_object", "no_typst", "typst_failed", "write_failed",
         # v0.116: a sheet's kind, and the PDF bundles
         "bad_kind", "wrong_kind", "bad_bundles", "bad_bundle_name", "bundle_exists", "no_bundle", "missing_sheet")

# What a sheet shows (v0.116): its position plans or its fire-protection plans, never both (typst_objects.SHEET_KINDS, lib/sheet.typ's `sheet(kind:)`).
KINDS = to.SHEET_KINDS
# The objects that belong to one kind of sheet; a text and the title block belong to both.
KIND_OBJECTS = {
    "position": ("sheet-viewport", "sheet-section", "sheet-legend", "sheet-position-list", "sheet-quantities"),
    "fire": ("sheet-fire-viewport", "sheet-fire-legend"),
}

# The PDF bundles of a project's sheets: Plans/bundles.json.
BUNDLES_FILE = "bundles.json"
BUNDLES_FORMAT = "woodcore-sheet-bundles"
# 1.1 (v0.117, the engineer: «on doit pouvoir modifier le nom, la description, l'étage, l'id du document. Par défaut, les valeurs sont reprises automatiquement lors de l'import dessus du premier plan»): a bundle may state its `id` -- what names its PDF, short and stable, where 1.0 named it by its `name`, now a free label --, its `description` and its `storey`. Each optional: absent, it is the first plan's on the bundle's first sheet (`bundle_fields`), read and never copied, so a plan renamed is followed. A 1.0 file is read as it is and written 1.1 at its next change.
BUNDLES_VERSION = "1.1"
BUNDLES_VERSIONS = ("1.0", BUNDLES_VERSION)
BUNDLE_FIELDS = ("id", "description", "storey")
# What a bundle's name may not hold: it names a PDF beside the sheets, so what Windows refuses in a file name -- and a sheet's own name is refused too, its PDF being Plans/<id>.pdf already.
_BAD_NAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}

# The words a new sheet starts with, in the project's language: its title and the heading of its remark (calc/i18n/strings.json's own, `sheet.position_plan` and `sheet.remark`, so that the window, the engine and a new sheet say one word).
_WORDS_KEYS = {"title": "sheet.position_plan", "remark": "sheet.remark", "fire_title": "sheet.fire_plan", "list_title": "position_list.title"}


class SheetError(ValueError):
    """A refusal of this module: a `code` (CODES), an English sentence, and the values it is about."""

    def __init__(self, code, message, **values):
        self.code = code
        self.values = values
        super().__init__(message)


# --- where the sheets are ----------------------------------------------------------------------

def folder(here, kind=None):
    """The folder of the project's sheets of `kind`: `Plans/` at the top of its Typst root in a project laid out before, whatever the kind; laid out by folders, the exports of the kind's plan tab -- `Plans/Position-plan/Exports/` for "position" (the kind where none is named), `Plans/Fire-plan/Exports/` for "fire"."""
    if not here.has_folders:
        return Path(here.typst_root) / FOLDER
    return here.drawing_dir(KIND_TABS[kind or "position"]) / project_module.EXPORTS_FOLDER


def folders(here):
    """Every folder the project's sheets lie in: one, `Plans/`, laid out before; one per kind laid out by folders."""
    if not here.has_folders:
        return [folder(here)]
    return [folder(here, kind) for kind in KINDS]


def bundles_folder(here):
    """Where the PDF bundles' file is kept: `Plans/` -- the sheets' folder before, the parent of the two plan tabs' laid out by folders, the bundles of both kinds in one file as they always were."""
    return Path(here.typst_root) / FOLDER


def path(here, sheet_id, kind=None):
    """The .typ of sheet `sheet_id`: where it lies -- in the folder of either kind laid out by folders, an id being one for the whole project --, else where a sheet of `kind` is written."""
    _check_id(sheet_id)
    if here.has_folders:
        for base in folders(here):
            if (base / f"{sheet_id}.typ").is_file():
                return base / f"{sheet_id}.typ"
    return folder(here, kind) / f"{sheet_id}.typ"


def pdf(here, sheet_id):
    """The PDF sheet `sheet_id` compiles to, beside its .typ."""
    return path(here, sheet_id).with_suffix(".pdf")


def _check_id(sheet_id):
    if not isinstance(sheet_id, str) or not ID_PATTERN.match(sheet_id):
        raise SheetError("bad_id", f"{sheet_id!r} is not a sheet's id -- letters, digits and _ . + -, starting with a letter or a digit", id=sheet_id)


def list_sheets(here, kind=None):
    """The ids of the project's sheets, in file-name order (case ignored, as Windows lists them) -- those of `kind` alone where it is given ("position", "fire"), each sheet's kind read by `sheet_kind`."""
    found = sorted((p.stem for base in folders(here) if base.is_dir() for p in base.glob("*.typ") if p.is_file() and ID_PATTERN.match(p.stem)), key=str.lower)
    if kind is None:
        return found
    _check_kind(kind)
    return [s for s in found if _kind_or_none(here, s) == kind]


def _check_kind(kind):
    if kind not in KINDS:
        raise SheetError("bad_kind", f"{kind!r} is not a kind of sheet -- expected one of {', '.join(KINDS)}", kind=kind)


def object_kind(object_type):
    """The kind of sheet an object belongs to ("position", "fire"), None for one that belongs to both -- a text, the title block, the page."""
    return next((k for k, types in KIND_OBJECTS.items() if object_type in types), None)


def declared_kind(text):
    """The kind a sheet's text says it is, or what its objects say -- its page's `kind:`, else (a sheet written before v0.116) "fire" where it holds a fire-protection object and "position" where it holds a position plan's object --, None for a sheet that says nothing yet: a title, a remark and a title block belong to both kinds."""
    found = to.objects(text)
    page = next((o for o in found if o.type == "sheet-page"), None)
    if page is not None and page.call is not None and page.call.args.get("kind") in KINDS:
        return page.call.args["kind"]
    held = {object_kind(o.type) for o in found} - {None}
    return "fire" if "fire" in held else "position" if held else None


def kind_of_text(text):
    """The kind of the sheet whose text is `text` (`declared_kind`), "position" for one that says nothing yet."""
    return declared_kind(text) or "position"


def sheet_kind(here, sheet_id):
    """The kind of sheet `sheet_id`: "position" or "fire" (`kind_of_text`)."""
    return kind_of_text(read(here, sheet_id))


def _kind_or_none(here, sheet_id):
    try:
        return sheet_kind(here, sheet_id)
    except (SheetError, OSError, UnicodeDecodeError):
        return None


def new_id(here):
    """The next free id, B01, B02, … -- a number left free by a sheet taken away is not given again while a higher one stands; a PDF bundle's name is not given either."""
    taken = {s.lower() for s in list_sheets(here)} | _bundle_names(here)
    numbers = [int(m.group(1)) for s in taken if (m := re.fullmatch(r"b(\d+)", s))]
    n = max(numbers, default=0) + 1
    while f"b{n:02d}" in taken:
        n += 1
    return f"B{n:02d}"


def read(here, sheet_id):
    """The text of sheet `sheet_id`, as written (line endings kept)."""
    p = path(here, sheet_id)
    if not p.is_file():
        raise SheetError("no_sheet", f"there is no sheet {sheet_id!r} -- the sheets are {', '.join(list_sheets(here)) or 'none'}", id=sheet_id)
    return p.read_bytes().decode("utf-8")


def _write(target, text):
    """`text` written to `target` beside itself and moved into place -- tried again for a moment where the sync client holds the file."""
    target.parent.mkdir(parents=True, exist_ok=True)
    staged = target.with_name(target.name + ".new")
    staged.write_bytes(text.encode("utf-8"))
    for attempt in range(10):
        try:
            os.replace(staged, target)
            return
        except PermissionError:
            if attempt == 9:
                staged.unlink(missing_ok=True)
                raise SheetError("write_failed", f"{target.name} cannot be written -- another program holds it", file=str(target)) from None
            time.sleep(0.2)


def write(here, sheet_id, text):
    """Writes the whole text of sheet `sheet_id` -- what every edit below ends in."""
    _write(path(here, sheet_id), text)


# --- a new sheet ---------------------------------------------------------------------------------

def language(here):
    """The language the project's documents are written in -- config.typ's `doc-lang` at the Typst root --, German where it says none: the language a new sheet's words and its title block's labels are in."""
    config = Path(here.config_typ)
    try:
        found = re.search(r'#let\s+doc-lang\s*=\s*"([a-z]{2})"', config.read_text(encoding="utf-8"))
    except OSError:
        found = None
    lang = found.group(1) if found else "de"
    return lang if lang in LANGUAGES else "de"


def _word(key, lang):
    return strings.text(_WORDS_KEYS[key], lang)


def _mm(value):
    return to.Length(value, "mm")


def new_sheet(here, sheet_id=None, format="A3", landscape=True, title="", lang=None, kind="position"):
    """Writes a new sheet and gives back its path: the page in `format`, of `kind` ("position" or "fire", v0.116), a title top-left (`title`, else «Plan de positions» -- «Plan de protection incendie» for a fire sheet -- in the project's language), a remark bottom-left -- «Remarque :» in bold and a text still to be written -- and the title block bottom-right, every cell from the project. No plan yet: they are added with `add_viewport`.

    Refused: an id that is not one, one a sheet or a PDF bundle already has (case ignored), a format that is not A0 to A6, a kind that is not one.
    """
    sheet_id = new_id(here) if sheet_id is None else sheet_id
    _check_id(sheet_id)
    _check_kind(kind)
    sheet_of = kind   # the sheet's kind, which its folder follows laid out by folders: `kind` is the loop's name below
    if format not in FORMATS:
        raise SheetError("bad_format", f"{format!r} is not a format of a sheet -- expected one of {', '.join(FORMATS)}", format=format)
    if sheet_id.lower() in {s.lower() for s in list_sheets(here)} | _bundle_names(here):
        raise SheetError("exists", f"a sheet {sheet_id!r} exists already", id=sheet_id)
    lang = language(here) if lang is None else lang
    # the page states its four arguments, defaults or not: a sheet says what paper it is on, and what it shows
    page = to.SheetPageModel(to.Call("sheet-page", {"format": format, "landscape": bool(landscape), "margin": _mm(10), "kind": kind}))
    width, height = page.size()
    heading = title.strip() if isinstance(title, str) and title.strip() else _word("fire_title" if kind == "fire" else "title", lang)
    # the remark bottom-left, beside the title block where the frame leaves room for it (A3, A2 …), above it where it does not (A4 portrait)
    block_left = width - 10 - min(200, width - 20)
    if block_left - 25 >= 50:
        remark_y, remark_w = height - 40, min(150, block_left - 25)
    else:
        remark_y, remark_w = height - 10 - 43 - 25, width - 40
    calls = [
        ("sheet-page", PAGE_ID, page.to_call()),
        ("sheet-text", "title", to.Call("sheet-text", {"x": _mm(20), "y": _mm(17), "body": to.Content(_escape(heading)), "size": to.Length(18, "pt"), "weight": "bold"})),
        ("sheet-text", "remark", to.Call("sheet-text", {"x": _mm(20), "y": _mm(remark_y), "body": to.Content(f"*{_escape(_word('remark', lang))}{_colon(lang)}* \\ " + to.PLACEHOLDER), "width": _mm(remark_w)})),
        ("sheet-titleblock", "titleblock", to.Call("sheet-titleblock", {"plan-number": sheet_id})),
    ]
    lines = [f"// Export sheet {sheet_id}: written by Woodcore (calc/sheets.py), yours to edit here or in Woodcore -- each object stands between its two `// woodcore:` tags.",
             documents.root_import_line(here), "", ""]
    text = "\n".join(lines)
    for kind, oid, call in calls:
        text += f"{to.START} {kind} {oid}\n{to.body_of(call)}\n{to.END} {oid}\n"   # a placed object a raw #place (Q-015), the page its show rule
        if kind == "sheet-page":
            # the engine's words on this sheet -- the title block's labels, the legend's -- in the project's language; after the show rule, which is what sets the page
            text += f'#set-report-language("{lang}")\n'
        text += "\n"
    target = path(here, sheet_id, sheet_of)
    _write(target, text)
    return target


def _escape(words):
    """Plain words as markup: the characters markup reads specially, escaped."""
    return re.sub(r'([\\#$*_`<>@=\-+/\[\]~])', r"\\\1", words)


def _colon(lang):
    return " :" if lang == "fr" else ":"


def archive(here, sheet_id):
    """Takes sheet `sheet_id` out of the project, never deleting it: its .typ (and its PDF) moved into `Plans/archives/<yymmdd-hhmmss>-<id>.typ`. Gives back the archived .typ."""
    source = path(here, sheet_id)
    if not source.is_file():
        raise SheetError("no_sheet", f"there is no sheet {sheet_id!r}", id=sheet_id)
    stamp = datetime.now().strftime("%y%m%d-%H%M%S")
    target = source.parent / "archives" / f"{stamp}-{sheet_id}.typ"
    target.parent.mkdir(parents=True, exist_ok=True)
    os.replace(source, target)
    out = pdf(here, sheet_id)
    if out.is_file():
        os.replace(out, target.with_suffix(".pdf"))
    # a sheet taken out leaves the PDF bundles that held it -- where the file of bundles can be read: a broken one is the engineer's to repair, and stops no archive
    try:
        data = _read_bundles(here)
    except SheetError:
        data = []
    if any(sheet_id in b["sheets"] for b in data):
        for b in data:
            b["sheets"] = [s for s in b["sheets"] if s != sheet_id]
        _write_bundles(here, data)
    return target


# --- the objects of a sheet ----------------------------------------------------------------------

def objects(here, sheet_id):
    """Every object of the sheet, in the order the file writes them (typst_objects.Object)."""
    return to.objects(read(here, sheet_id))


def find(here, sheet_id, object_id):
    """The object `object_id` of the sheet, refused where there is none."""
    obj = to.find(read(here, sheet_id), object_id)
    if obj is None:
        raise SheetError("bad_object", f"sheet {sheet_id!r} holds no object {object_id!r}", id=sheet_id, object=object_id)
    return obj


def model(here, sheet_id, object_id):
    """The editor's model of one object (typst_objects' SheetTextModel, ViewportModel, …) -- a ModelError where it cannot be read."""
    return find(here, sheet_id, object_id).model()


def set_object(here, sheet_id, object_id, value, force=False, expected=None):
    """Writes object `object_id` from `value` -- a model or a Call -- between its tags and nowhere else (typst_objects.write_object: an object written by hand is refused unless `force`, one changed since `expected` was loaded is refused)."""
    call = value.to_call() if hasattr(value, "to_call") else value
    write(here, sheet_id, to.write_object(read(here, sheet_id), object_id, call, force=force, expected=expected))


def _edit(here, sheet_id, object_id, change, force=False):
    """Reads one object's model, applies `change(model)` and writes it back."""
    m = model(here, sheet_id, object_id)
    change(m)
    set_object(here, sheet_id, object_id, m, force=force)
    return m


def add_object(here, sheet_id, kind, call=None, object_id=None, base=None):
    """Adds an object of `kind` after the last object of the sheet -- the title block's tag standing last, before it -- and gives back its id: `object_id`, else one made free from `base` (the kind's name where none)."""
    if kind not in to.SHEET_TYPES or kind == "sheet-page":
        raise SheetError("bad_object", f"{kind!r} is not an object to add to a sheet -- expected one of {', '.join(k for k in to.SHEET_TYPES if k != 'sheet-page')}", kind=kind)
    text = read(here, sheet_id)
    # a sheet written before v0.116 that holds nothing of either kind yet takes the kind of the first plan put on it
    belongs, sheet = object_kind(kind), declared_kind(text)
    if belongs is not None and sheet is not None and belongs != sheet:
        raise SheetError("wrong_kind", f"a {kind} is no object of a {sheet} sheet -- position plans and fire-protection plans are never on one sheet", kind=kind, sheet=sheet, id=sheet_id)
    found = to.objects(text)
    if object_id is None:
        object_id = to.free_id(text, _base(base or kind.removeprefix("sheet-")))
    # a list on a sheet is the project's file of it, included (spec 2026-10-21-commandes-typst-refonte, Q-015): written once where the project has none yet
    import typst_sheet_place
    if kind in typst_sheet_place.LIST_FILES:
        from domains import list_files
        list_kind = "position-list" if kind == "sheet-position-list" else "quantities"
        if not list_files.path(here, list_kind).is_file():
            list_files.write(here, list_kind)
    blocks = [o for o in found if o.type != "sheet-titleblock"]
    after = blocks[-1].end if blocks else len(to._lines(text)) - 1
    new = to.insert_object(text, after, kind, object_id, call)
    # a blank line before the new object, as Woodcore writes a sheet: one object, one paragraph of the file
    start = to.find(new, object_id).start
    lines = to._lines(new)
    if start > 0 and lines[start - 1].strip():
        newline = to._newline_of(new)
        new = "".join(lines[:start]) + newline + "".join(lines[start:])
    write(here, sheet_id, new)
    return object_id


def _base(words):
    slug = to._slug(words) or "object"
    return slug if slug[0].isalpha() else "o-" + slug


def add_viewport(here, sheet_id, plan, x, y, scale=None, width=None, highlight=None):
    """Adds plan `plan` at (x, y) millimetres, at 1:`scale` or `width` millimetres wide; gives back the object's id (`viewport-<plan>`)."""
    m = to.ViewportModel(to.Call("sheet-viewport", {}))
    m.set_plan(plan)
    m.move_to(x, y)
    if scale is not None:
        m.set_scale(scale)
    if width is not None:
        m.set_width(width)
    if highlight is not None:
        m.set_highlight(highlight)
    return add_object(here, sheet_id, "sheet-viewport", m.to_call(), base=f"viewport-{plan}")


def add_fire_viewport(here, sheet_id, plan, x, y, scale=None, width=None, legend=True):
    """Adds fire-protection plan `plan` at (x, y) millimetres, at 1:`scale` or `width` millimetres wide, its legend drawn on it where `legend`; gives back the object's id (`fire-<plan>`)."""
    m = to.FireViewportModel(to.Call("sheet-fire-viewport", {}))
    m.set_plan(plan)
    m.move_to(x, y)
    if scale is not None:
        m.set_scale(scale)
    if width is not None:
        m.set_width(width)
    if not legend:
        m.set_legend(False)
    return add_object(here, sheet_id, "sheet-fire-viewport", m.to_call(), base=f"fire-{plan}")


def add_section(here, sheet_id, plan, storey, x, y, scale=None, width=None):
    """Adds the section plan `plan` with storey `storey` highlighted at (x, y) millimetres; gives back the object's id."""
    m = to.SectionModel(to.Call("sheet-section", {}))
    m.set_plan(plan)
    m.set_storey(storey)
    m.move_to(x, y)
    if scale is not None:
        m.set_scale(scale)
    if width is not None:
        m.set_width(width)
    return add_object(here, sheet_id, "sheet-section", m.to_call(), base="section")


def add_text(here, sheet_id, x, y, body, size=None, weight=None, width=None):
    """Adds a text at (x, y) millimetres -- `body` is markup, the engineer's words; gives back the object's id."""
    m = to.SheetTextModel(to.Call("sheet-text", {}))
    m.move_to(x, y)
    m.set_body(body)
    if size is not None:
        m.set_size(size)
    if weight is not None:
        m.set_weight(weight)
    if width is not None:
        m.set_width(width)
    return add_object(here, sheet_id, "sheet-text", m.to_call(), base="text")


def add_legend(here, sheet_id, x, y, width=120, plans=to.AUTO):
    """Adds the legend of the sheet's plans at (x, y) millimetres; gives back the object's id."""
    m = to.LegendModel(to.Call("sheet-legend", {}))
    m.move_to(x, y)
    m.set_width(width)
    m.set_plans(plans)
    return add_object(here, sheet_id, "sheet-legend", m.to_call(), base="legend")


def add_fire_legend(here, sheet_id, x, y, width=120, plans=to.AUTO):
    """Adds the legend of the sheet's fire-protection plans at (x, y) millimetres, a block of its own; gives back the object's id."""
    m = to.FireLegendModel(to.Call("sheet-fire-legend", {}))
    m.move_to(x, y)
    m.set_width(width)
    m.set_plans(plans)
    return add_object(here, sheet_id, "sheet-fire-legend", m.to_call(), base="fire-legend")


def add_position_list(here, sheet_id, x, y, width=180):
    """Adds the list of the positions at (x, y) millimetres, `width` wide (v0.116): the project's list, written once (calc/domains/list_files.py) -- its plans, its scope and its storey have no raw form since the spec 2026-10-21-commandes-typst-refonte (Q-015); gives back the object's id."""
    m = to.PositionListModel(to.Call("sheet-position-list", {}))
    m.move_to(x, y)
    m.set_width(width)
    return add_object(here, sheet_id, "sheet-position-list", m.to_call(), base="positions")


def add_quantities(here, sheet_id, x, y, width=150):
    """Adds the quantities at (x, y) millimetres, `width` wide (issue #9): the project's, written once (calc/domains/list_files.py) -- of every position plan, their plans and scope having no raw form (Q-015); gives back the object's id."""
    m = to.QuantitiesModel(to.Call("sheet-quantities", {}))
    m.move_to(x, y)
    m.set_width(width)
    return add_object(here, sheet_id, "sheet-quantities", m.to_call(), base="quantities")


def plans_of_sheet(here, sheet_id):
    """The position plans sheet `sheet_id` shows, by their ids, in the order its viewports are written -- what a position list of that sheet lists by default."""
    out = []
    for obj in objects(here, sheet_id):
        if obj.type == "sheet-viewport" and obj.call is not None:
            plan = obj.call.args.get("plan")
            if isinstance(plan, str) and plan not in out:
                out.append(plan)
    return out


def new_position_list_sheet(here, sheet_id=None, lang=None):
    """Writes a new A4 portrait position sheet holding the list of the positions alone -- «Liste des positions» its title -- and gives back its path (v0.116, the button «Créer une liste des positions»): the project's list, every position (Q-015)."""
    sheet_id = new_id(here) if sheet_id is None else sheet_id
    lang = language(here) if lang is None else lang
    target = new_sheet(here, sheet_id, format="A4", landscape=False, title=_word("list_title", lang), lang=lang, kind="position")
    text = read(here, sheet_id)
    # the list alone: the remark and the title block a new sheet carries are taken off
    for oid in ("remark", "titleblock"):
        if to.find(text, oid) is not None:
            text = to.remove_object(text, oid)
    write(here, sheet_id, text)
    add_position_list(here, sheet_id, 20, 32, width=170)
    return target

def remove(here, sheet_id, object_id):
    """Takes object `object_id` out of the sheet -- its two tags and what is between them."""
    find(here, sheet_id, object_id)
    write(here, sheet_id, to.remove_object(read(here, sheet_id), object_id))


def move(here, sheet_id, object_id, x, y):
    """Moves an object's top-left corner to (x, y) millimetres from the sheet's top-left corner."""
    return _edit(here, sheet_id, object_id, lambda m: m.move_to(x, y))


def set_scale(here, sheet_id, object_id, n):
    """Prints a plan or a section at 1:n -- the width it had goes (a drawing has one size)."""
    return _edit(here, sheet_id, object_id, lambda m: m.set_scale(n))


def set_width(here, sheet_id, object_id, width):
    """Prints a plan or a section `width` millimetres wide -- the scale it had goes."""
    return _edit(here, sheet_id, object_id, lambda m: m.set_width(width))


def resize(here, sheet_id, object_id, factor):
    """Enlarges a plan or a section by `factor`: its scale 1:n becomes 1:(n / factor), rounded to a whole n, or its width is multiplied. Gives back the model written."""
    m = model(here, sheet_id, object_id)
    if not isinstance(m, to._Drawing):
        raise SheetError("bad_object", f"{object_id!r} is a {m.type}, which has no scale", object=object_id)
    n = m.get("scale")
    if isinstance(n, (int, float)) and not isinstance(n, bool):
        m.set_scale(max(1, round(n / factor)))
    else:
        w = to.mm_of(m.get("width"))
        if w is None:
            raise SheetError("bad_object", f"{object_id!r} has neither a scale nor a width Woodcore can read", object=object_id)
        m.set_width(round(w * factor, 1))
    set_object(here, sheet_id, object_id, m)
    return m


def page(here, sheet_id):
    """The sheet's page model (typst_objects.SheetPageModel): its format, its orientation, its margin, and `size()` in millimetres."""
    obj = next((o for o in objects(here, sheet_id) if o.type == "sheet-page"), None)
    if obj is None:
        raise SheetError("no_page", f"sheet {sheet_id!r} has no `sheet-page` object -- its first object is `#show: sheet.with(...)` between two tags", id=sheet_id)
    return obj.model()


def set_page(here, sheet_id, format=None, landscape=None, margin=None):
    """Changes the sheet's format, orientation or margin -- what is not given stays."""
    m = page(here, sheet_id)
    if format is not None:
        m.set_format(format)
    if landscape is not None:
        m.set_landscape(landscape)
    if margin is not None:
        m.set_margin(margin)
    obj = next(o for o in objects(here, sheet_id) if o.type == "sheet-page")
    set_object(here, sheet_id, obj.id, m)
    return m


# --- the PDF bundles (v0.116) --------------------------------------------------------------------

def bundles_path(here):
    """Plans/bundles.json: the PDF bundles of the project's sheets (`bundles_folder`)."""
    return bundles_folder(here) / BUNDLES_FILE


def _check_bundle(entry, where):
    if not isinstance(entry, dict) or not {"name", "kind", "sheets"} <= set(entry) or set(entry) - {"name", "kind", "sheets", *BUNDLE_FIELDS}:
        raise SheetError("bad_bundles", f"{where}: a bundle is {{name, kind, sheets}} and may state {', '.join(BUNDLE_FIELDS)} -- got {entry!r}", file=BUNDLES_FILE)
    for key in BUNDLE_FIELDS:
        if key in entry and (not isinstance(entry[key], str) or not entry[key].strip()):
            raise SheetError("bad_bundles", f"{where}: a bundle's {key} is a non-empty string where it is stated", file=BUNDLES_FILE)
    if not isinstance(entry["name"], str) or not entry["name"].strip():
        raise SheetError("bad_bundles", f"{where}: a bundle's name is a non-empty string", file=BUNDLES_FILE)
    if entry["kind"] not in KINDS:
        raise SheetError("bad_bundles", f"{where}: a bundle's kind is one of {', '.join(KINDS)} -- got {entry['kind']!r}", file=BUNDLES_FILE)
    if not isinstance(entry["sheets"], list) or not all(isinstance(s, str) and ID_PATTERN.match(s) for s in entry["sheets"]):
        raise SheetError("bad_bundles", f"{where}: a bundle's sheets are a list of sheet ids", file=BUNDLES_FILE)
    if len(set(entry["sheets"])) != len(entry["sheets"]):
        raise SheetError("bad_bundles", f"{where}: a bundle lists a sheet twice", file=BUNDLES_FILE)


def _read_bundles(here):
    """Every bundle as Plans/bundles.json holds it, checked: [] where there is no file; `bad_bundles` where it is not a file of bundles -- refused rather than overwritten, a file written by hand being the engineer's."""
    target = bundles_path(here)
    if not target.is_file():
        return []
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SheetError("bad_bundles", f"{BUNDLES_FILE} cannot be read -- {exc}", file=BUNDLES_FILE) from None
    if not isinstance(data, dict) or data.get("format") != BUNDLES_FORMAT or data.get("schema_version") not in BUNDLES_VERSIONS or not isinstance(data.get("bundles"), list):
        raise SheetError("bad_bundles", f"{BUNDLES_FILE} is no {BUNDLES_FORMAT} file of version {' or '.join(BUNDLES_VERSIONS)}", file=BUNDLES_FILE)
    names = set()
    for i, entry in enumerate(data["bundles"]):
        _check_bundle(entry, f"bundle {i + 1}")
        if entry["name"].lower() in names:
            raise SheetError("bad_bundles", f"two bundles are named {entry['name']!r}", file=BUNDLES_FILE)
        names.add(entry["name"].lower())
    return data["bundles"]


def _write_bundles(here, bundles):
    for i, entry in enumerate(bundles):
        _check_bundle(entry, f"bundle {i + 1}")
    data = {"format": BUNDLES_FORMAT, "schema_version": BUNDLES_VERSION,
            "bundles": [{"name": b["name"], "kind": b["kind"], "sheets": list(b["sheets"]), **{k: b[k] for k in BUNDLE_FIELDS if b.get(k)}} for b in bundles]}
    _write(bundles_path(here), json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def list_bundles(here, kind=None):
    """The PDF bundles, in the order the file keeps them -- those of `kind` alone where it is given: each {name, kind, sheets}, a copy."""
    found = _read_bundles(here)
    if kind is not None:
        _check_kind(kind)
        found = [b for b in found if b["kind"] == kind]
    return [{"name": b["name"], "kind": b["kind"], "sheets": list(b["sheets"]), **{k: b[k] for k in BUNDLE_FIELDS if b.get(k)}} for b in found]


def bundle(here, name):
    """The bundle `name` (case ignored), refused where there is none."""
    found = next((b for b in list_bundles(here) if b["name"].lower() == str(name).lower()), None)
    if found is None:
        raise SheetError("no_bundle", f"there is no PDF bundle {name!r}", name=name)
    return found


def _check_bundle_name(here, name, other_than=None):
    if not isinstance(name, str) or not name.strip() or name != name.strip() or name.endswith(".") or _BAD_NAME.search(name) or name.lower() in _RESERVED:
        raise SheetError("bad_bundle_name", f"{name!r} cannot name a PDF -- no < > : \" / \\ | ? *, and no space or dot at its end", name=name)
    lowered = name.lower()
    if other_than is not None and lowered == other_than.lower():
        return
    if lowered in {b["name"].lower() for b in list_bundles(here)}:
        raise SheetError("bundle_exists", f"a PDF bundle {name!r} exists already", name=name)
    if lowered in {s.lower() for s in list_sheets(here)}:
        raise SheetError("bundle_exists", f"{name!r} is a sheet's name -- its PDF is Plans/{name}.pdf already", name=name)


def _bundle_names(here):
    """The bundles' names, lowered -- none where Plans/bundles.json cannot be read, a broken file of bundles stopping no sheet from being made."""
    try:
        return {b["name"].lower() for b in _read_bundles(here)}
    except SheetError:
        return set()


def _first_plan(here, entry):
    """The source of the first plan on the bundle's first sheet that shows one, or None."""
    for sid in entry["sheets"]:
        try:
            plans = plans_of_sheet(here, sid)
        except (SheetError, OSError):
            continue
        for pid in plans:
            try:
                source = json.loads((here.plans_dir / f"{pid}.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if isinstance(source, dict):
                return source
    return None


def bundle_fields(here, entry):
    """What a bundle says of itself, each field its own where it states it, else the first plan's on its first sheet: {id, name, description, storey, derived: {field: True where it is the plan's}}. The id falls back on the name where no plan gives one (a 1.0 bundle with no plan names its PDF as it always did)."""
    plan = _first_plan(here, entry) or {}
    derived = {"id": plan.get("id") or entry["name"], "description": plan.get("label") or "", "storey": plan.get("storey") or ""}
    out = {"name": entry["name"], "derived": {}}
    for key in BUNDLE_FIELDS:
        own = entry.get(key)
        out[key] = own if own else derived[key]
        out["derived"][key] = not own
    if out["derived"]["id"] and not _free_id(here, out["id"], entry["name"]):
        out["id"] = entry["name"]   # the plan's id names a sheet or another bundle's PDF already: the name names it, as in 1.0
    return out


def _free_id(here, value, own_name):
    """Whether `value` may name bundle `own_name`'s PDF: no sheet's id (Plans/<id>.pdf is its PDF) and no other bundle's PDF."""
    lowered = str(value).lower()
    if lowered in {s.lower() for s in list_sheets(here)}:
        return False
    for other in _read_bundles(here):
        if other["name"].lower() == own_name.lower():
            continue
        if lowered in (other["name"].lower(), str(other.get("id", "")).lower()):
            return False
    return True


def set_bundle_field(here, name, key, value):
    """A bundle's `id`, `description` or `storey` written -- empty, taken out, the first plan's then shown again. A new id renames the PDF written already; one that names a sheet or another bundle's PDF, or that no file may be named, is refused."""
    if key not in BUNDLE_FIELDS:
        raise SheetError("bad_bundles", f"a bundle states {', '.join(BUNDLE_FIELDS)}, not {key!r}", file=BUNDLES_FILE)
    value = str(value or "").strip()
    old = bundle(here, name)
    before = bundle_pdf(here, old)
    if key == "id" and value:
        if _BAD_NAME.search(value) or value.endswith(".") or value.lower() in _RESERVED:
            raise SheetError("bad_bundle_name", f"{value!r} cannot name a PDF -- no < > : \" / \\ | ? *, and no dot at its end", name=value)
        if not _free_id(here, value, old["name"]):
            raise SheetError("bundle_exists", f"{value!r} names a sheet or another bundle's PDF already", name=value)

    def change(_data, entry):
        if value:
            entry[key] = value
        else:
            entry.pop(key, None)
    record = _edit_bundle(here, name, change)
    after = bundle_pdf(here, record)
    if before.is_file() and before != after:
        os.replace(before, after)
    return record


def bundle_pdf(here, name):
    """The PDF a bundle is written to, beside the sheets' own: Plans/<id>.pdf, its id its own or the first plan's (bundle_fields) -- `name` a bundle's name or its record."""
    entry = name if isinstance(name, dict) else next((b for b in _read_bundles(here) if b["name"].lower() == str(name).lower()), None)
    if entry is None:
        return folder(here) / f"{name}.pdf"
    return folder(here, entry.get("kind")) / f"{bundle_fields(here, entry)['id']}.pdf"   # beside the sheets of its kind


def _checked_sheets(here, entry, sheet_ids):
    """`sheet_ids` as a bundle's sheets: each a sheet there is, of the bundle's kind, listed once."""
    out = []
    for sid in sheet_ids:
        read(here, sid)      # no_sheet where there is none
        found = sheet_kind(here, sid)
        if found != entry["kind"]:
            raise SheetError("wrong_kind", f"sheet {sid!r} is a {found} sheet and the bundle {entry['name']!r} gathers {entry['kind']} sheets", id=sid, name=entry["name"])
        if sid not in out:
            out.append(sid)
    return out


def create_bundle(here, name, kind="position", sheets=()):
    """A new PDF bundle `name` of `kind`, holding `sheets` in that order; gives back its record."""
    _check_kind(kind)
    _check_bundle_name(here, name)
    data = _read_bundles(here)
    entry = {"name": name, "kind": kind, "sheets": []}
    entry["sheets"] = _checked_sheets(here, entry, list(sheets))
    data.append(entry)
    _write_bundles(here, data)
    return dict(entry)


def _edit_bundle(here, name, change):
    data = _read_bundles(here)
    entry = next((b for b in data if b["name"].lower() == str(name).lower()), None)
    if entry is None:
        raise SheetError("no_bundle", f"there is no PDF bundle {name!r}", name=name)
    change(data, entry)
    _write_bundles(here, data)
    return dict(entry)


def rename_bundle(here, name, new_name):
    """Renames a PDF bundle -- its PDF with it, where one was written."""
    old = bundle(here, name)
    _check_bundle_name(here, new_name, other_than=old["name"])
    before = bundle_pdf(here, old)

    def change(_data, entry):
        entry["name"] = new_name
    record = _edit_bundle(here, name, change)
    after = bundle_pdf(here, record)
    if before.is_file() and before != after:
        os.replace(before, after)
    return record


def delete_bundle(here, name):
    """Takes a PDF bundle away -- never its sheets; its PDF, where one was written, moved into Plans/archives."""
    old = bundle(here, name)
    out = bundle_pdf(here, old)
    _edit_bundle(here, name, lambda data, entry: data.remove(entry))
    if out.is_file():
        target = out.parent / "archives" / f"{datetime.now().strftime('%y%m%d-%H%M%S')}-{old['name']}.pdf"
        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(out, target)


def set_bundle_sheets(here, name, sheet_ids):
    """The bundle's sheets, in this order -- what a drag in the list writes."""
    return _edit_bundle(here, name, lambda _data, entry: entry.__setitem__("sheets", _checked_sheets(here, entry, list(sheet_ids))))


def add_to_bundle(here, name, sheet_ids, index=None):
    """Adds sheets to a bundle, at `index` (the end where None); a sheet it holds already is moved there."""
    sheet_ids = [sheet_ids] if isinstance(sheet_ids, str) else list(sheet_ids)

    def change(_data, entry):
        kept = [s for s in entry["sheets"] if s not in sheet_ids]
        at = len(kept) if index is None else max(0, min(index, len(kept)))
        entry["sheets"] = _checked_sheets(here, entry, kept[:at] + sheet_ids + kept[at:])
    return _edit_bundle(here, name, change)


def remove_from_bundle(here, name, sheet_ids):
    """Takes sheets out of a bundle -- never out of the project."""
    sheet_ids = [sheet_ids] if isinstance(sheet_ids, str) else list(sheet_ids)
    return _edit_bundle(here, name, lambda _data, entry: entry.__setitem__("sheets", [s for s in entry["sheets"] if s not in sheet_ids]))


def plans_of_bundle(here, name):
    """The position plans the sheets of a bundle show, in order, each once -- what a position list made for the bundle lists."""
    out = []
    for sid in bundle(here, name)["sheets"]:
        for plan in plans_of_sheet(here, sid):
            if plan not in out:
                out.append(plan)
    return out


def export_bundle(here, name, timeout=300):
    """Compiles every sheet of bundle `name` into its own PDF, as `compile` does, and writes Plans/<name>.pdf: their pages one after the other in the bundle's order (pypdf). Gives back (ok, message): Typst's words, prefixed with the sheet's id, where one does not compile -- nothing merged then. A bundle naming a sheet there is not is refused (`missing_sheet`)."""
    entry = bundle(here, name)
    if not entry["sheets"]:
        return False, f"the PDF bundle {entry['name']!r} holds no sheet"
    missing = [s for s in entry["sheets"] if not path(here, s).is_file()]
    if missing:
        raise SheetError("missing_sheet", f"the PDF bundle {entry['name']!r} names sheets there are not: {', '.join(missing)}", name=entry["name"], sheets=", ".join(missing))
    for sid in entry["sheets"]:
        ok, message = compile(here, sid, timeout=timeout)
        if not ok:
            return False, f"{sid}: {message}"
    target = bundle_pdf(here, entry)
    staged = target.with_name(target.name + ".new")
    try:
        from pypdf import PdfWriter
        writer = PdfWriter()
        for sid in entry["sheets"]:
            writer.append(str(pdf(here, sid)))
        with open(staged, "wb") as handle:
            writer.write(handle)
        writer.close()
        for attempt in range(10):
            try:
                os.replace(staged, target)
                break
            except PermissionError:
                if attempt == 9:
                    raise
                time.sleep(0.2)
    except Exception as exc:        # broad: a PDF that cannot be read or written (pypdf's family): a sentence, not a crash
        staged.unlink(missing_ok=True)
        return False, f"the PDF bundle {entry['name']!r} cannot be written -- {exc}"
    return True, ""


# --- the PDF -------------------------------------------------------------------------------------

def compile_args(here, sheet_id, target=None):
    """`typst compile`'s arguments for sheet `sheet_id`, the executable left out: the Typst root stated, the sheet's .typ and its PDF last -- calc/documents.py's own arrangement."""
    return ["compile", "--root", str(Path(here.typst_root)), str(path(here, sheet_id)), str(pdf(here, sheet_id) if target is None else target)]


def compile(here, sheet_id, target=None, timeout=300):
    """Compiles sheet `sheet_id` to its PDF (or `target`) with the project's engine. Gives back (ok, message): (True, "") where it compiled, (False, Typst's own words) where it did not -- a sheet half written does not compile, and that is a sentence to show, not an exception."""
    read(here, sheet_id)
    try:
        result = proc.run([project_module.typst_executable(), *compile_args(here, sheet_id, target)],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except OSError as exc:
        return False, f"Typst cannot be started -- {exc}"
    except subprocess.SubprocessError as exc:     # a timeout
        return False, str(exc)
    if result.returncode != 0:
        return False, (result.stderr or result.stdout or "").strip() or f"typst exited with {result.returncode}"
    return True, ""
