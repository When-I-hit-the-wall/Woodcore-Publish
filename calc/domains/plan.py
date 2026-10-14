"""Position plans (Positionspläne): the structure's STE symbols drawn over an architect's plan, from the definition Woodcore saves (docs/domain/position-plans.md §3.3sexies).

A plan is not read from a workbook. It is drawn in Woodcore's «Plan de positions» tab and saved as one source file per plan, `plans/<id>.json` beside calc/. That file plays the part a load's sheet plays: Woodcore is the only thing that writes it, and this module the only thing that reads it. A plan is normally one floor, whose character is the second one of its positions' numbers (T001: Träger, floor 0, number 01); a project of several small buildings, like this one, gives each building a plan of its own on the same floor.

A plan is drawn over a background -- one page of a PDF, an image or an SVG in the project folder -- in that background's own units, which this module calls the sheet: points for a PDF, pixels for an image, viewBox units for an SVG, measured from the top left corner with y pointing down. The export copies the background under data/plans/, a PDF reduced to the one page drawn on, since Typst reads nothing outside the report's own folder; plan_svg.py writes the symbols as an SVG over the same frame, so that lib/calc-engine.typ's show-plan sets one exactly over the other.

What a plan says about a position is where it is, and nothing else: an element's label is a position id of Positionen.xlsx, which stays the one source of positions (docs/domain/positions.md §7). A label that is not there is a warning at export, never an error -- a position renamed or removed in Excel since it was drawn; Woodcore draws only the sheet's positions and refuses to save another (v0.45) -- and nothing here writes to the workbook.

The geometry below -- hit-testing, snapping, the Shift constraint, labels proposed for a new element -- has no Qt in it, so Woodcore's canvas and a test script call the same functions.
"""

import copy
import functools
import hashlib
import io
import json
import math
import re
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

import engine
import validation
from domains import dimension  # a dimension's geometry, the static models' and the schemas' own (issue #9)
from domains import figure_style
from domains import figure_text  # a text placed with the Text tool, the four engines' one (issue #43, ARCH-003)
from domains import lines  # a construction aid's geometry: a line through two points, parallel at a distance (issue #18)
from domains.plan_geometry import (  # split out of this module (issue #30): every name it had is still importable from it
    LENGTH_TYPES,
    MIN_POINTS,
    PT_PER_M,
    SNAP_KINDS,
    SnapIndex,
    TYPES,
    _axis_name,
    _axis_ordinal,
    _clean,
    _inside,
    _letters,
    _line_cross,
    _point_segment,
    auto_label,
    axis_across,
    axis_direction,
    axis_distance,
    axis_normal,
    axis_orientation,
    axis_scheme,
    axis_segment,
    axis_sort_key,
    bbox,
    centroid,
    constrain,
    default_span,
    default_subtype,
    distance_m,
    element_kind,
    element_length_m,
    hit_axis,
    hit_element,
    hit_label,
    insert_axis,
    is_load,
    labelled,
    legend_key,
    line_in_polygon,
    metres_text,
    nearest_point,
    nearest_vertex,
    new_axis_scheme,
    next_load_label,
    parallel_axis,
    polyline_length,
    quantities,
    ring_area,
    segments_of,
    shows_length,
    units_per_m,
)
from domains.plan_background import (  # split out of this module (issue #30): every name it had is still importable from it
    BACKGROUND_FORMATS,
    STOREYS,
    _LENGTH_RE,
    _STOREY_ATTIC,
    _STOREY_BASEMENTS,
    _STOREY_GROUND,
    _UNIT_PX,
    _fail,
    _file_state,
    _hash_file,
    _jpeg_size,
    _pdf_page_size,
    _pdf_reader,
    _png_size,
    _read_pdf,
    _storey_key,
    _svg_size,
    background_format,
    background_path,
    file_hash,
    pdf_page_count,
    preload,
    relative_background,
    sheet_of,
    storey_floor,
    storey_index,
)

# Of a source file (plans/<id>.json) and of the export (data/plans.json). Export 1.1: the legend is a list of lines, each with its swatch, which show-plan lays out -- 1.0 pointed at one SVG of the whole legend. Source 1.1 and export 1.2: an element's number may be moved by hand (label_offset), and the export says where every number is drawn (label_at). A 1.0 source is read as it is, every number in its own place.
# ⚠️ Neither moved for v0.99's `style` on an element or an axis: a field whose absence has a meaning -- «follows the plan's own three» -- is additive, so no file needs migrating and a plan drawn before it is read, and drawn, exactly as it was (the v0.69 rule for `group`, docs/decisions.md §13).
# Source 1.2 and export 1.3 (v0.114): a plan names the document it is drawn on (`background.document`, calc/domains/plan_documents.py), its storey in free text beside the one character of its positions' numbers (`storey`, `floor`), whether it is a floor plan or a section (`role`), the section a floor plan refers to (`section_plan`), and on a section its storey lines and boxes. Every one of them optional and additive: a 1.0 or 1.1 source is read as it is, a floor plan with no storey.
# Source 1.3 (v0.116): a plan states its type (`plan_type`: a floor plan, an elevation section, a load-path plan), a load-path plan carries STE's six load symbols (types PL and LL), a section its load transfer levels (`load_levels`), and a storey box or a load level the numbering character its designation «x1xx» is made of (`floor`). Every one of them optional and additive: a 1.2 source is read as it is, its type derived from its role. The export stays 1.3, its new keys being additive and written only where a plan uses them.
# Source 1.4 (v0.117, the engineer's «pouvoir tourner les poteaux» and «activer ou désactiver cet affichage pour un unique élément»): a column (S) or a point Auflager (M) may carry its `angle`, which 1.3 refused on anything but a load symbol -- hence the version, so an older Woodcore says the file is newer rather than refusing a column --, and an element whose length is written may say so for itself (`show_length`, true or false, absent: as the plan's `show_lengths`). A 1.3 source is read as it is. The export stays 1.3: its legend lines gain a `quantity` where the plan has a scale, additive and written only where there is one.
# Source 1.5 (issue #9, the engineer's «outils de cotation pour pouvoir coter les plans»): a plan carries its dimensions (`dimensions`), aligned, horizontal or vertical, a chain of them on one line, or an angle -- hence the version, so an older Woodcore says the file is newer rather than drawing the plan without them. A 1.4 source is read as it is; the export stays 1.3, its `dimensions` additive and written only where a plan has some.
SOURCE_SCHEMA_VERSION = "1.6"   # 1.6 (issue #18): the construction aids, `aids` -- a file of 1.5 has none, and is read as it is
# 1.7 is 1.6 with `texts`, the Text tool's (issue #43, spec 2026-10-11-variables-liees-champs-et-textes): written only by a plan that holds one (`version_of`), so a plan without a text is saved and exported as before
TEXT_SCHEMA_VERSION = "1.7"
SOURCE_SCHEMA_VERSIONS = ("1.0", "1.1", "1.2", "1.3", "1.4", "1.5", SOURCE_SCHEMA_VERSION, TEXT_SCHEMA_VERSION)
EXPORT_SCHEMA_VERSION = "1.3"
# 1.4 is 1.3 with a plan's `texts`, what each printed: written only where one holds a text
TEXT_EXPORT_VERSION = "1.4"


def version_of(source):
    """The schema_version Woodcore writes a plan at: 1.7 where it holds a text, 1.6 where it does not -- what every writer of a plan's file asks, so that a plan without a text is written as before."""
    return TEXT_SCHEMA_VERSION if source.get("texts") else SOURCE_SCHEMA_VERSION

# What a plan is: a floor plan, whose positions it locates, or a section, which shows the storeys a floor plan refers to.
ROLES = ("plan", "section")
# What kind of plan it is (v0.116, the engineer's «Type de plan»): a floor plan («coupe en plan»), an elevation section («coupe en élévation», role "section"), or a load-path plan («plan de descente de charges», STE Compact 02 pp. 14-15) -- a floor plan whose tools also draw the six load symbols. Absent from a source, it is derived from its role, so no file needs migrating.
PLAN_TYPES = ("floor", "section", "loadpath")


# A plan id is the file name of its source and the string the report addresses it by -- the rule connections follow, for the same reason.
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$")


# A plan without a background is drawn on an empty sheet the size of an A3 page in landscape, in points.
BLANK_SHEET = {"width": 1190.55, "height": 841.89}


# What the style sliders may do to the symbols: from a quarter to three times their size. Read from figure_style rather than written here, since v0.99 an element and an axis may state a factor of their own over the plan's and the two levels must mean the same three things; the two names stay, plan_tab.py naming them.
STYLE_KEYS = figure_style.KEYS
STYLE_RANGE = figure_style.RANGE

# How much of the background shows through the white veil under the symbols, by default: the plan stays readable, the symbols dominate.
DEFAULT_OPACITY = 0.45

# Where an axis carries its bubble: at the top of a vertical axis or the left of a horizontal one ("start"), the other end, both, or none.
BUBBLES = ("both", "start", "end", "none")

# Two points closer than this, in sheet units, are one point typed twice.
SAME_POINT = 1e-6


# The order the tools and the legend list the types in -- the STE position types; the load symbols, which are no positions, are LOAD_TYPES.
TYPE_ORDER = ("V", "H", "W", "T", "S", "A", "D", "Ö", "B", "M", "L")
LOAD_TYPES = ("PL", "LL")


def _number(value, where, what, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        _fail(where, f"{what} must be a number, got {value!r}")
    if positive and value <= 0:
        _fail(where, f"{what} must be greater than 0, got {value!r}")
    return value


def normalize_angle(degrees):
    """An angle in degrees, brought into (-180, 180]."""
    a = math.fmod(degrees, 360.0)
    if a <= -180:
        a += 360
    elif a > 180:
        a -= 360
    return a


def plan_type(source):
    """The plan's type (PLAN_TYPES): the one it states, else derived from its role -- a section, or a floor plan -- so a plan saved before v0.116 is read as what it was."""
    stated = source.get("plan_type")
    if stated in PLAN_TYPES:
        return stated
    return "section" if source.get("role", "plan") == "section" else "floor"


def storey_designation(entry, siblings=()):
    """The STE designation of a storey on a section: «x» + the storey's numbering character + «xx» -- x1xx, x0xx, xUxx (STE Compact 02 p. 12) -- for a storey box or a load transfer level. The character is the one the entry states (`floor`), else the one its storey proposes (storey_floor), the attic above the highest digit among `siblings` (the section's other boxes); where neither gives one, the storey's own designation."""
    floor = str(entry.get("floor") or "").strip()
    if not floor:
        others = [str(s.get("floor") or "") or storey_floor(s.get("storey", "")) for s in siblings if s is not entry]
        floor = storey_floor(entry.get("storey", ""), [f for f in others if f])
    return f"x{floor}xx" if floor else str(entry.get("storey", ""))


def point_count(type_):
    """How many points an element of this type has, where its type fixes it -- two for a beam and a bracing member, Woodcore's tool ending the line on its second click --, or None where it may have any number."""
    return TYPES[type_].get("points")


def type_name(type_, subtype=None):
    """What Positionen.xlsx's data_type sheet calls an element of this type and subtype."""
    names = TYPES[type_]["names"]
    return names.get(subtype, next(iter(names.values())))


# --- The sheet ------------------------------------------------------------------


# A CAD drawing is drawn on through its document only (calc/domains/plan_documents.py), which renders a layout to an SVG.
CAD_SUFFIXES = (".dxf", ".dwg")


# --- The source file ------------------------------------------------------------

# --- The superposition: another plan shown over this one (v0.116) ------------------
# The engineer: «superposer au plan un autre plan déjà existant avec ou sans les éléments que l'on a dessinés par dessus». A drawing aid of the window and never printed: the optional `superposition` of a source says which plan of the same tab is shown over it -- {plan, elements, opacity, colour, tint_elements, offset} -- and nothing exports it (record() reads none of it). The other plan's point q (its own sheet units) is shown at p = s·q + offset in this plan's sheet units, s = this plan's units per metre over the other's where both have a scale, else 1: a translation only, both plans being calibrated.

# The colours the superposed plan may be shown in: as it is, in grey, or in one of five colours -- its background always, its elements too where `tint_elements` says so.
SUPERPOSITION_COLOURS = ("normal", "grey", "green", "blue", "yellow", "red", "pink")
SUPERPOSITION_INKS = {"grey": "#8a8a8a", "green": "#2e9d4a", "blue": "#1f6fd1", "yellow": "#d9a400", "red": "#d32f2f", "pink": "#e754a6"}
SUPERPOSITION_OPACITY = (0.05, 1.0)
SUPERPOSITION_DEFAULT = {"elements": True, "opacity": 0.5, "colour": "red", "tint_elements": False}


def superposition_of(source):
    """The superposition a source states, with its defaults filled in -- or None where it states none, or names no plan."""
    spec = source.get("superposition") if isinstance(source, dict) else None
    if not isinstance(spec, dict) or not str(spec.get("plan") or "").strip():
        return None
    out = dict(SUPERPOSITION_DEFAULT)
    out.update(spec)
    return out


def check_superposition(source, where):
    """The superposition's rules (a schema states its shape): a plan of a valid id other than this one, an opacity within SUPERPOSITION_OPACITY, a colour of SUPERPOSITION_COLOURS, an offset of two numbers. A plan that does not exist is no error -- it may have been archived since --: the window says so and shows nothing."""
    spec = source.get("superposition")
    if spec is None:
        return
    if not isinstance(spec, dict):
        _fail(where, "superposition is not an object")
    other = spec.get("plan")
    if not isinstance(other, str) or not ID_PATTERN.match(other):
        _fail(where, f"superposition.plan is {other!r} -- the id of another plan of the same tab")
    if other == source.get("id"):
        _fail(where, f"superposition.plan is {other!r} -- the plan itself; name another plan")
    if "opacity" in spec:
        _number(spec["opacity"], where, "superposition.opacity")
        lo, hi = SUPERPOSITION_OPACITY
        if not lo <= float(spec["opacity"]) <= hi:
            _fail(where, f"superposition.opacity is {spec['opacity']!r} -- expected {lo} to {hi}")
    if "colour" in spec and spec["colour"] not in SUPERPOSITION_COLOURS:
        _fail(where, f"superposition.colour is {spec['colour']!r} -- expected one of {', '.join(SUPERPOSITION_COLOURS)}")
    for key in ("elements", "tint_elements"):
        if key in spec and not isinstance(spec[key], bool):
            _fail(where, f"superposition.{key} is {spec[key]!r} -- expected true or false")
    if "offset" in spec:
        offset = spec["offset"]
        if not isinstance(offset, list) or len(offset) != 2:
            _fail(where, f"superposition.offset is {offset!r} -- expected [dx, dy]")
        for i, value in enumerate(offset):
            _number(value, where, f"superposition.offset[{i}]")


def superposition_scale(frame, other_frame):
    """(s, scaled): this plan's sheet units per sheet unit of the other -- the ratio of their units per metre where both have a scale (`scaled` True), else 1."""
    mine, theirs = units_per_m(frame), units_per_m(other_frame)
    if mine and theirs:
        return mine / theirs, True
    return 1.0, False


def superposition_default_offset(frame, other_frame):
    """The offset a superposition starts from: the other plan's crop's top left corner on this plan's -- what is right for two pages of one plan set laid out alike, and what «Aligner» then corrects."""
    s, _scaled = superposition_scale(frame, other_frame)
    mine, theirs = crop_of(frame), crop_of(other_frame)
    return [_clean(mine["x"] - s * theirs["x"]), _clean(mine["y"] - s * theirs["y"])]


def superposition_transform(spec, frame, other_frame):
    """(s, dx, dy): the other plan's point q is shown at (s·qx + dx, s·qy + dy) on this plan -- `spec`'s offset, else the default (superposition_default_offset)."""
    s, _scaled = superposition_scale(frame, other_frame)
    offset = spec.get("offset") if spec else None
    if not (isinstance(offset, list) and len(offset) == 2):
        offset = superposition_default_offset(frame, other_frame)
    return s, float(offset[0]), float(offset[1])


def check_frame(source, where):
    """The frame a drawing is made over -- its sheet, its background (on a file or on a page of an imported document), its crop and its scale -- checked as a position plan's is. A function of its own since a fire-protection plan that carries a frame of its own states it in the very same four fields, and two copies of these rules would be two places for them to drift apart."""
    sheet = source["sheet"]
    _number(sheet["width"], where, "sheet.width", positive=True)
    _number(sheet["height"], where, "sheet.height", positive=True)

    background = source.get("background")
    if background is not None:
        document = background.get("document")
        if document is not None and not ID_PATTERN.match(document):
            _fail(where, f"background.document {document!r} -- the id of a document of plans/documents/")
        fmt = background_format(background["file"])
        cad = document is not None and Path(background["file"]).suffix.lower() in CAD_SUFFIXES
        if fmt is None and not cad:
            _fail(where, f"background {background['file']!r} -- a plan is drawn on a PDF, a PNG, a JPEG or an SVG, or on a DXF or a DWG through its document")
        page = background["page"]
        if isinstance(page, bool) or not isinstance(page, int) or page < 1:
            _fail(where, f"background.page is {page!r} -- a page number, from 1")
        if fmt != "pdf" and not cad and page != 1:
            _fail(where, f"background.page is {page} -- only a PDF and a CAD drawing have pages")
        opacity = _number(background.get("opacity", DEFAULT_OPACITY), where, "background.opacity")
        if not 0 <= opacity <= 1:
            _fail(where, f"background.opacity is {opacity} -- from 0 (hidden) to 1 (as it is)")

    crop = source.get("crop")
    if crop is not None:
        for key in ("x", "y"):
            _number(crop[key], where, f"crop.{key}")
        for key in ("w", "h"):
            _number(crop[key], where, f"crop.{key}", positive=True)
        tolerance = 1e-6 * max(sheet["width"], sheet["height"])
        if (crop["x"] < -tolerance or crop["y"] < -tolerance
                or crop["x"] + crop["w"] > sheet["width"] + tolerance
                or crop["y"] + crop["h"] > sheet["height"] + tolerance):
            _fail(where, "the crop leaves the sheet -- draw it again inside the plan")

    scale = source.get("scale")
    if scale is not None:
        mode = scale.get("mode")
        if mode == "ratio":
            _number(scale.get("ratio"), where, "scale.ratio", positive=True)
            if background is None or background_format(background["file"]) != "pdf":
                _fail(where, "a scale 1:n needs a PDF background, the one kind whose sheet is in real units -- calibrate an image instead")
        elif mode == "calibration":
            points = scale.get("points")
            if not isinstance(points, list) or len(points) != 2:
                _fail(where, "a calibration needs its two points")
            for i, p in enumerate(points, start=1):
                _point(p, where, f"scale.points[{i}]")
            if math.dist(points[0], points[1]) <= SAME_POINT:
                _fail(where, "the calibration's two points are the same point")
            _number(scale.get("length_m"), where, "scale.length_m", positive=True)
        else:
            _fail(where, f"scale.mode is {mode!r} -- expected 'ratio' or 'calibration'")


def check_source(source, where):
    """Everything a source file must satisfy before it is exported -- its structure against schemas/plan-source.schema.json, then the rules a schema cannot state. Every failure is a blocking error naming the file and the field (docs/architecture/data-contracts.md §3.6). What does not stop the report -- a label Positionen.xlsx does not have, say -- is warnings()'s."""
    if isinstance(source, dict) and source.get("schema_version") not in (None, *SOURCE_SCHEMA_VERSIONS):
        _fail(where, f"schema_version is {source.get('schema_version')!r} -- expected {' or '.join(map(repr, SOURCE_SCHEMA_VERSIONS))}")
    try:
        validation.validate_structure(source, "plan-source")
    except validation.ValidationError as exc:
        _fail(where, str(exc))

    if not ID_PATTERN.match(source["id"]):
        _fail(where, f"id {source['id']!r} -- use letters, digits and _ . + - only, starting with a letter or a digit")
    if not isinstance(source["floor"], str) or len(source["floor"]) > 1:
        _fail(where, f"floor is {source['floor']!r} -- one character, the second of the positions' numbers (U, 0, 1, …), or empty")

    check_frame(source, where)
    check_superposition(source, where)

    role = source.get("role", "plan")
    if role not in ROLES:
        _fail(where, f"role is {role!r} -- expected one of {', '.join(ROLES)}")
    stated = source.get("plan_type")
    if stated is not None and stated not in PLAN_TYPES:
        _fail(where, f"plan_type is {stated!r} -- expected one of {', '.join(PLAN_TYPES)}")
    if stated is not None and (stated == "section") != (role == "section"):
        _fail(where, f"plan_type {stated!r} and role {role!r} disagree -- a section is the one plan whose role is section")
    kind_of_plan = plan_type(source)
    for i, level in enumerate(source.get("load_levels") or [], start=1):
        at = f"load level {i}"
        if role != "section":
            _fail(where, "load transfer levels are drawn on a section -- set its type to section, or take them out")
        if not str(level.get("storey", "")).strip():
            _fail(where, f"{at} names no storey")
        points = level.get("points")
        if not isinstance(points, list) or len(points) != 2:
            _fail(where, f"{at} needs its two points")
        for j, p in enumerate(points, start=1):
            _point(p, where, f"{at}: point {j}")
        if math.dist(points[0], points[1]) <= SAME_POINT:
            _fail(where, f"{at}: its two points are the same point")
        if "label_offset" in level:
            _point(level["label_offset"], where, f"{at}: label_offset")
        if "style" in level:
            _fail(where, f"{at} follows the plan's own sizes and states none of its own, got a style")
    for i, entry in enumerate((source.get("storey_boxes") or []) + (source.get("load_levels") or []), start=1):
        floor = entry.get("floor")
        if floor is not None and (not isinstance(floor, str) or len(floor) > 1):
            _fail(where, f"floor {floor!r} of a storey box or a load level -- one character (U, 0, 1, …), or empty")
    section_plan = source.get("section_plan")
    if section_plan is not None and not ID_PATTERN.match(section_plan):
        _fail(where, f"section_plan {section_plan!r} -- the id of a section plan")
    if role != "section" and (source.get("storey_lines") or source.get("storey_boxes")):
        _fail(where, "storey lines and storey boxes are drawn on a section -- set its role to section, or take them out")
    for i, line in enumerate(source.get("storey_lines") or [], start=1):
        at = f"storey line {i}"
        if not str(line.get("storey", "")).strip():
            _fail(where, f"{at} names no storey")
        points = line.get("points")
        if not isinstance(points, list) or len(points) != 2:
            _fail(where, f"{at} needs its two points")
        for j, p in enumerate(points, start=1):
            _point(p, where, f"{at}: point {j}")
        if math.dist(points[0], points[1]) <= SAME_POINT:
            _fail(where, f"{at}: its two points are the same point")
    for i, box in enumerate(source.get("storey_boxes") or [], start=1):
        at = f"storey box {i}"
        if not str(box.get("storey", "")).strip():
            _fail(where, f"{at} names no storey")
        for key in ("x", "y"):
            _number(box.get(key), where, f"{at}: {key}")
        for key in ("w", "h"):
            _number(box.get(key), where, f"{at}: {key}", positive=True)

    # The plan's own three. A key `style` does not know is refused here where it was silently ignored until v0.99: with a factor of its own on every entry, a misspelt `lines` is a factor the engineer set and nothing draws.
    figure_style.check(source["style"], lambda message: _fail(where, message))

    for i, axis in enumerate(source["axes"], start=1):
        at = f"axis {i}"
        if not axis["label"].strip():
            _fail(where, f"{at} has no label")
        _point(axis["point"], where, f"{at}: point")
        _number(axis["angle"], where, f"{at}: angle")
        if axis.get("bubbles", "both") not in BUBBLES:
            _fail(where, f"{at}: bubbles is {axis['bubbles']!r} -- expected one of {', '.join(BUBBLES)}")
        # an axis is a dash-dot line and the bubble its name is set in: `point` on one would be a field with nothing to show for it (figure_style.ENTRY_KEYS)
        figure_style.check(axis.get("style"), lambda message: _fail(where, message),
                           may=figure_style.allowed("plan", "axes"), what=f"{at}: style")

    for i, element in enumerate(source["elements"], start=1):
        at = f"element {i}"
        type_ = element["type"]
        if type_ not in TYPES:
            _fail(where, f"{at}: type {type_!r} -- expected one of {', '.join(TYPE_ORDER + LOAD_TYPES)}")
        if is_load(type_):
            if kind_of_plan != "loadpath":
                _fail(where, f"{at} ({type_}) is a load symbol, drawn on a load-path plan -- set the plan's type to load-path plan, or take it out")
            if "angle" in element:
                _number(element["angle"], where, f"{at}: angle")
        elif "angle" in element:
            if not is_rotatable(element):
                _fail(where, f"{at} ({type_}) has no direction of its own, got an angle -- a column (S) or a point Auflager (M) may be turned")
            _number(element["angle"], where, f"{at}: angle")
        if "show_length" in element:
            if not isinstance(element["show_length"], bool):
                _fail(where, f"{at}: show_length must be true or false, got {element['show_length']!r}")
            if type_ not in LENGTH_TYPES:
                _fail(where, f"{at} ({type_}) has no length written beside it -- show_length is for {', '.join(LENGTH_TYPES)}")
        subtypes = TYPES[type_].get("subtypes")
        subtype = element.get("subtype")
        if subtypes and subtype not in subtypes:
            _fail(where, f"{at} ({type_}): subtype {subtype!r} -- expected one of {', '.join(subtypes)}")
        if not subtypes and subtype is not None:
            _fail(where, f"{at} ({type_}) has no subtypes, got {subtype!r}")
        if not labelled(type_) and element.get("label", ""):
            _fail(where, f"{at} ({type_}) carries no position number, got {element['label']!r}")
        if "label_offset" in element:
            if not labelled(type_):
                _fail(where, f"{at} ({type_}) carries no position number to move, got a label_offset")
            _point(element["label_offset"], where, f"{at}: label_offset")
        points = element["points"]
        for j, p in enumerate(points, start=1):
            _point(p, where, f"{at}: point {j}")
        kind = element_kind(element)
        if len(points) < MIN_POINTS[kind] or (kind == "point" and len(points) != 1):
            shape = {"point": "a point", "line": "a line", "poly": "an area"}[kind]
            _fail(where, f"{at} ({type_}) is drawn as {shape} and has {len(points)} point(s)")
        count = point_count(type_)
        if count is not None and len(points) != count:
            _fail(where, f"{at} ({type_}) is a single straight member, drawn from one end to the other, and has {len(points)} points -- draw it again with its {count} ends")
        if kind != "point":
            for j in range(1, len(points)):
                if math.dist(points[j - 1], points[j]) <= SAME_POINT:
                    _fail(where, f"{at} ({type_}): points {j} and {j + 1} are the same point")
        if "span" in element:
            _number(element["span"], where, f"{at}: span")
        if element.get("diagonal", 0) not in (0, 1):
            _fail(where, f"{at}: diagonal is {element['diagonal']!r} -- 0 or 1")
        # all three: one of the eleven STE symbols is a line, or a symbol on a point, and every one of them carries its position number
        figure_style.check(element.get("style"), lambda message: _fail(where, message),
                           may=figure_style.allowed("plan", "elements"), what=f"{at} ({type_}): style")
    check_dimensions(source, where)
    check_aids(source, where)
    check_texts(source, where, "plan", TEXT_SCHEMA_VERSION)


# --- Texts (issue #43) ---------------------------------------------------------------------
# A text placed with the Text tool: `{points: [[x, y]], text, vars?, style?}`, its one point its centre on the sheet; what it prints is figure_text's, the four engines' one (ARCH-003). Shared with the fire-protection plans, which hold theirs the same way (with an id, as every entry of theirs): a list of one point rather than a `point`, since every entry of a fire plan is moved, copied and turned by its `points`, and a plan's elements, lines and dimensions are too.

def check_texts(source, where, kind, version):
    """A drawing's texts as a source must state them: a point of two numbers, figure_text's token text and variables (D-13), and only the `text` factor of a style (figure_style). Only at `version` or later -- a file of an earlier version has none. Each failure names the file and the text."""
    texts = source.get("texts", [])
    if not isinstance(texts, list):
        _fail(where, "texts is not a list")
    if texts and source.get("schema_version") is not None and source.get("schema_version") != version:
        _fail(where, f"holds a text at schema_version {source.get('schema_version')!r} -- a drawing with texts is {version!r}")
    for i, text in enumerate(texts, start=1):
        at = f"text {i}"
        if not isinstance(text, dict):
            _fail(where, f"{at} is not an object")
        points = text.get("points")
        if not isinstance(points, list) or len(points) != 1:
            _fail(where, f"{at}: points must be one point, [[x, y]], got {points!r}")
        _point(points[0], where, f"{at}: point")
        figure_text.check(text, lambda message: _fail(where, message), at)
        figure_style.check(text.get("style"), lambda message: _fail(where, message),
                           may=figure_style.allowed(kind, "texts"), what=f"{at}: style")


def text_records(source, values, where, notes):
    """The texts of a drawing as its record carries them: [{text, lines, links?}] -- what each printed and where its variables came from (REQ-012). Their warnings are added to `notes`."""
    out = []
    for i, text in enumerate(source.get("texts") or [], start=1):
        printed, provenance, found = figure_text.resolve(text, values or {}, f"{where}, text {i}")
        notes += found
        record = {"text": text.get("text", ""), "lines": printed, "point": [_clean(v) for v in text["points"][0]]}
        if "id" in text:
            record["id"] = text["id"]
        if provenance:
            record["links"] = provenance
        out.append(record)
    return out


# --- Construction aids (issue #18) ------------------------------------------------------------
# A line without ends the plan is laid out with, drawn in Woodcore alone and never in the report nor on a sheet: horizontal, vertical, through two points, or parallel to another line at a distance (D-008). Stored resolved, `{kind, point, angle}` -- an axis without bubbles --, so it is drawn, snapped to and turned as an axis is; `kind` only says how it was made. A fire-protection plan has none (D-015).
AID_KINDS = ("horizontal", "vertical", "two-points", "parallel")


def new_aid(kind, point, angle):
    """An aid of `kind` through `point` at `angle` (degrees, clockwise from the right), as a source stores it."""
    if kind not in AID_KINDS:
        raise ValueError(f"aid kind {kind!r} -- expected one of {', '.join(AID_KINDS)}")
    return {"kind": kind, "point": [_clean(point[0]), _clean(point[1])], "angle": _clean(lines.normal_angle(angle))}


def check_aids(source, where):
    """A plan's construction aids as a source must state them: a kind of AID_KINDS, a point of two numbers, an angle. Each failure names the file and the aid."""
    aids = source.get("aids", [])
    if not isinstance(aids, list):
        _fail(where, "aids is not a list")
    for i, aid in enumerate(aids, start=1):
        at = f"aid {i}"
        if not isinstance(aid, dict):
            _fail(where, f"{at} is not an object")
        if aid.get("kind") not in AID_KINDS:
            _fail(where, f"{at}: kind is {aid.get('kind')!r} -- expected one of {', '.join(AID_KINDS)}")
        point = aid.get("point")
        if not (isinstance(point, list) and len(point) == 2 and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in point)):
            _fail(where, f"{at}: point must be two numbers")
        _number(aid.get("angle"), where, f"{at}: angle")


def hit_aid(source, point, tolerance, window):
    """The index of the construction aid passing within `tolerance` of `point`, the nearest first, or None -- `hit_axis` on the aids."""
    return hit_axis({"axes": source.get("aids", [])}, point, tolerance, window)


# --- An object moved or copied (issue #18) ----------------------------------------------------
# What a selection of the plan may be, and the list of the source it is an index into -- the canvas's SELECTION_LISTS, said once here.
ENTRY_LISTS = {"element": "elements", "axis": "axes", "storey-line": "storey_lines", "storey-box": "storey_boxes",
               "load-level": "load_levels", "dimension": "dimensions", "aid": "aids", "text": "texts"}


def shifted(points, dx, dy):
    """`points` moved by (dx, dy), to a hundredth of a sheet unit -- what a drag, «Déplacer» and «Copier» all write."""
    return [[_clean(round(float(x) + dx, 2)), _clean(round(float(y) + dy, 2))] for x, y in points]


def translate_entry(source, kind, index, dx, dy):
    """The entry `index` of the selection kind `kind` moved by (dx, dy), in place: an element's, a storey line's, a load level's or a dimension's points, an axis's or an aid's point, a storey box's corner. What is measured from the entry itself -- a number moved clear (`label_offset`), a dimension's `offset`, a slab's span -- moves with it unchanged."""
    entry = source[ENTRY_LISTS[kind]][index]
    if kind in ("axis", "aid"):
        entry["point"] = shifted([entry["point"]], dx, dy)[0]
    elif kind == "storey-box":
        entry["x"], entry["y"] = (_clean(round(float(entry["x"]) + dx, 2)), _clean(round(float(entry["y"]) + dy, 2)))
    else:
        entry["points"] = shifted(entry["points"], dx, dy)
    return entry


def copy_entry(source, kind, index, dx, dy, window):
    """A copy of the entry `index` of `kind`, moved by (dx, dy) and added to the source: (its index, the axes renamed). A copied element keeps its position number -- a second occurrence of the same position, as a copy in the schemas keeps it (D-004) --; a copied axis is named by where it lands among the others (`insert_axis`), the others renamed after it."""
    entries = source.setdefault(ENTRY_LISTS[kind], [])
    copy_ = copy.deepcopy(entries[index])
    entries.append(copy_)
    translate_entry(source, kind, len(entries) - 1, dx, dy)
    if kind == "axis":
        entries.pop()
        copy_["label"] = ""
        renames = insert_axis(source["axes"], copy_, window)
        return next(i for i, axis in enumerate(source["axes"]) if axis is copy_), renames
    return len(entries) - 1, {}


# --- Dimensions (issue #9) ------------------------------------------------------------------
# What a plan's dimension may be: the three linear kinds of the static models and the schemas (domains/dimension.py), a chain of them on one line, and an angle. A dimension's points are points of the sheet -- not references to an element, which a plan has no lasting name for -- so a dimension does not follow an element that is moved.
DIMENSION_KINDS = dimension.LINEAR + ("chain", "angle")
DIMENSION_POINTS = {"horizontal": (2, 2), "vertical": (2, 2), "parallel": (2, 2), "chain": (3, None), "angle": (3, 3)}


def check_dimensions(source, where):
    """A plan's dimensions as a source must state them: a kind of DIMENSION_KINDS, its points -- two for a linear one, three or more for a chain, the corner and one point on each side for an angle --, no two following ones the same, a chain's `axis` one of the linear kinds, a number for `offset`, and the factors of a style a dimension may state (`line`, `text`). Each failure names the file and the dimension."""
    for i, dim in enumerate(source.get("dimensions") or [], start=1):
        at = f"dimension {i}"
        if not isinstance(dim, dict):
            _fail(where, f"{at} must be an object, got {dim!r}")
        kind = dim.get("kind")
        if kind not in DIMENSION_KINDS:
            _fail(where, f"{at}: kind {kind!r} -- expected one of {', '.join(DIMENSION_KINDS)}")
        points = dim.get("points")
        low, high = DIMENSION_POINTS[kind]
        if not isinstance(points, list) or len(points) < low or (high is not None and len(points) > high):
            count = f"{low}" if low == high else f"{low} or more"
            _fail(where, f"{at} ({kind}) needs {count} points, got {points!r}")
        for j, p in enumerate(points, start=1):
            _point(p, where, f"{at}: point {j}")
        for j in range(1, len(points)):
            if math.dist(points[j - 1], points[j]) <= SAME_POINT:
                _fail(where, f"{at}: points {j} and {j + 1} are the same point")
        if kind == "chain" and dim.get("axis", "parallel") not in dimension.LINEAR:
            _fail(where, f"{at}: axis {dim.get('axis')!r} -- expected one of {', '.join(dimension.LINEAR)}")
        if "offset" in dim:
            _number(dim["offset"], where, f"{at}: offset")
        figure_style.check(dim.get("style"), lambda message: _fail(where, message),
                           may=figure_style.allowed("plan", "dimensions"), what=f"{at}: style")


def dimension_parts(source, dim):
    """What a dimension draws and says, in sheet units, its values in metres or degrees: for a linear one or a chain, a list of segments {ends, line, value, unit} along one line; for an angle, one part {centre, radius, start, sweep, value, unit}. [] where a length cannot be measured -- a plan without a scale (`units_per_m`), whose dimensions are then a warning (D-016) -- or the points do not make one."""
    kind, points = dim["kind"], [tuple(map(float, p)) for p in dim["points"]]
    offset = float(dim.get("offset", 0.0))
    if kind == "angle":
        centre, a, b = points
        ra, rb = math.dist(centre, a), math.dist(centre, b)
        if ra <= SAME_POINT or rb <= SAME_POINT:
            return []
        first = ((a[0] - centre[0]) / ra, (a[1] - centre[1]) / ra)
        second = ((b[0] - centre[0]) / rb, (b[1] - centre[1]) / rb)
        sweep, start = dimension.arc(first, second, offset < 0)
        radius = abs(offset) or 0.6 * min(ra, rb)
        return [{"centre": centre, "radius": radius, "start": start, "sweep": sweep, "value": abs(sweep), "unit": "°"}]
    per_m = units_per_m(source)
    if not per_m:
        return []
    axis = dim.get("axis", "parallel") if kind == "chain" else kind
    carried = dimension.onto(axis, points[0], points[-1], points, offset, SAME_POINT)
    if carried is None:
        return []
    return [{"ends": (points[j], points[j + 1]), "line": (carried[j], carried[j + 1]),
             "value": dimension.linear_value(axis, points[j], points[j + 1]) / per_m, "unit": "m"}
            for j in range(len(points) - 1)]


def dimension_value_text(part):
    """What a dimension writes beside its line: «4.25 m» to the centimetre, as a wall's length; «37.5°» to the tenth of a degree."""
    if part["unit"] == "°":
        return f"{part['value']:.1f}°"
    return metres_text(part["value"])


def _point(p, where, what):
    if not isinstance(p, list) or len(p) != 2:
        _fail(where, f"{what} must be [x, y], got {p!r}")
    _number(p[0], where, f"{what} x")
    _number(p[1], where, f"{what} y")


def read_source(path):
    """One plan's source file, checked. Its id must be its file name: the file is how Woodcore finds a plan, the id how the report does."""
    path = Path(path)
    try:
        source = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _fail(path.name, f"not readable as JSON -- {exc}")
    check_source(source, path.name)
    if source["id"] != path.stem:
        _fail(path.name, f"id is {source['id']!r} but the file is named {path.name} -- they must agree")
    return source


def position_plan_sources(plans_dir):
    """Every position plan's source the quantities measure: the plans of `plans_dir` in their order, a section left out (a section is no plan of positions). The one place that says which plans are measured -- the export's data/quantities.json and the Positions tab's lengths and quantities alike (issue #14). Raises validation.ValidationError on a file it cannot read, as `read_source`."""
    return [source for source in (read_source(path) for path in source_paths(plans_dir)) if plan_type(source) != "section"]


def new_source(pid, floor="0"):
    """A plan with nothing on it yet, on an empty sheet."""
    return {
        "schema_version": SOURCE_SCHEMA_VERSION,
        "id": pid,
        "label": "",
        "floor": floor,
        "storey": "",
        "role": "plan",
        "sheet": dict(BLANK_SHEET),
        "show_lengths": False,
        "style": {key: 1.0 for key in STYLE_KEYS},
        "axes": [],
        "elements": [],
    }


def source_paths(source_dir):
    """Every plan source, in file-name order -- the order they are listed in, exported in, and shown in the report."""
    source_dir = Path(source_dir)
    if not source_dir.is_dir():
        return []
    return sorted(source_dir.glob("*.json"), key=lambda p: p.name.lower())


# --- Geometry -------------------------------------------------------------------
# Tolerant of a draft: Woodcore calls these on every movement of the mouse.

def crop_of(source):
    """The frame the report shows, {x, y, w, h}: the crop drawn, or the whole sheet."""
    crop = source.get("crop")
    if crop:
        return {key: float(crop[key]) for key in ("x", "y", "w", "h")}
    sheet = source.get("sheet") or BLANK_SHEET
    return {"x": 0.0, "y": 0.0, "w": float(sheet["width"]), "h": float(sheet["height"])}


# What may be turned: a column and a point Auflager, drawn as a square (v0.117, the engineer: «un carré comme aujourd'hui, qu'il est possible de tourner (e.g. 30°)»).
ROTATABLE = ("S", "M")

# The step a turn takes with Shift held, on the circle a turnable element shows when it is selected (issue #9, «tourner les poteaux avec le cercle qui apparaît à la sélection»).
ANGLE_STEP = 15


def is_rotatable(element):
    """Whether an element may be turned by an `angle` of its own: a column, and an Auflager placed on a point (v0.117) -- the one rule the check of a source, the window's angle field and the circle a selected element turns by all read."""
    return element.get("type") in ROTATABLE and element_kind(element) == "point"


def snap_angle(degrees, step=ANGLE_STEP):
    """`degrees` to the nearest multiple of `step`, in (-180, 180]."""
    return normalize_angle(round(float(degrees) / step) * step)


def set_element_angle(element, degrees):
    """Turns `element` to `degrees`, brought into (-180, 180] and kept to the hundredth; 0 takes the angle off, so a plan never turned reads as one that never had the field. Returns whether the element changed."""
    value = round(normalize_angle(float(degrees)), 2)
    if value == 0:
        value = 0.0
    if value == float(element.get("angle", 0) or 0):
        return False
    if value:
        element["angle"] = value
    else:
        element.pop("angle", None)
    return True


# What a drawing tool remembers for the next element it draws (issue #9: «à l'activation d'un outil de dessin, afficher tout de suite les options de l'objet» -- set there, they are the next element's).
TOOL_DEFAULT_KEYS = ("subtype", "angle", "show_length", "span", "diagonal", "style")


def apply_defaults(element, defaults):
    """Gives a new `element` -- its type and points set -- what its tool's `defaults` hold that such an element may carry, and nothing else: a subtype its type has, an angle where it is turnable (an Auflager drawn with two points takes none), a length shown or hidden where it has one, a slab's span and diagonal, the style factors an element may state. A source written so is one `check_source` accepts. Returns the element."""
    defaults = defaults or {}
    type_ = element["type"]
    subtypes = TYPES[type_].get("subtypes")
    if subtypes and defaults.get("subtype") in subtypes:
        element["subtype"] = defaults["subtype"]
    if "angle" in defaults and (is_rotatable(element) or (is_load(type_) and element_kind(element) == "point")):
        set_element_angle(element, defaults["angle"])
    if isinstance(defaults.get("show_length"), bool) and type_ in LENGTH_TYPES:
        element["show_length"] = defaults["show_length"]
    if type_ == "D":
        span = defaults.get("span")
        if isinstance(span, (int, float)) and not isinstance(span, bool) and math.isfinite(span):
            element["span"] = _clean(span)
        if defaults.get("diagonal") in (0, 1):
            element["diagonal"] = defaults["diagonal"]
    style = defaults.get("style") or {}
    may = figure_style.allowed("plan", "elements")
    own = {key: value for key, value in style.items() if key in may and isinstance(value, (int, float)) and not isinstance(value, bool)}
    if own:
        element["style"] = own
    return element


# --- Hit-testing and snapping -------------------------------------------------------


# --- Labels ------------------------------------------------------------------------

def plan_labels(source):
    """The position numbers a plan shows, each once -- identical elements share theirs -- in the order they were first drawn."""
    return list(dict.fromkeys(e["label"] for e in source.get("elements", []) if e.get("label") and not is_load(e.get("type"))))


def unknown_labels(source, position_ids):
    """The position numbers a plan shows that Positionen.xlsx does not have, each once, in the order drawn: what Woodcore refuses to save -- only the sheet's positions are drawn -- and what the export warns about, a position renamed or removed in Excel since it was drawn."""
    known = set(position_ids)
    return [label for label in plan_labels(source) if label not in known]


def missing_rows(source, position_ids):
    """The lines to paste into Positionen.xlsx's Positions Element sheet for the labels this plan shows and the sheet does not have: the id and its type, tab-separated, one per line -- the sheet stays the one source of positions, and the engineer the one who writes to it."""
    known = set(position_ids)
    rows, seen = [], set()
    for element in source.get("elements", []):
        label = element.get("label", "")
        if label and label not in known and label not in seen and not is_load(element.get("type")):
            seen.add(label)
            rows.append(f"{label}\t{type_name(element['type'], element.get('subtype'))}")
    return "\n".join(rows)


def warnings(source, position_ids, where=None):
    """What does not stop the report but should be looked at, as sentences: a label Positionen.xlsx does not have, a label that does not begin with its type's letter, a labelled element without a number, an element outside the frame the report shows, a number moved by hand out of that frame. A number drawn on several elements is not one of them: identical elements share their position, on one plan or on several -- Woodcore's tools draw the same number every time -- and what is said of it is said once."""
    from domains import plan_svg  # where a number is drawn is the drawing module's to say

    pid = source.get("id") or "?"
    where = where or f"plan {pid}"
    known = set(position_ids)
    out = []
    crop = crop_of(source)
    sz = plan_svg.sizes_of(source)
    for i, element in enumerate(source.get("elements", []), start=1):
        type_, label = element["type"], element.get("label", "")
        if not labelled(type_):
            continue
        if not label:
            out.append(engine.Note("plan_no_number", f"{where}: element {i} ({type_}) has no position number", plan=pid, i=i, type=type_))
            continue
        if label not in known and not is_load(type_):
            out.append(engine.Note("plan_unknown", f"{where}: {label} is not a position of the project -- add it in Woodcore's Positions tab", plan=pid, label=label))
        if not is_load(type_) and not label.startswith(type_):
            out.append(engine.Note("plan_wrong_type", f"{where}: {label} is drawn as a {type_} ({type_name(type_, element.get('subtype'))})", plan=pid, label=label, type=type_, name=type_name(type_, element.get("subtype"))))
        x0, y0, x1, y1 = bbox(element["points"])
        if x1 < crop["x"] or y1 < crop["y"] or x0 > crop["x"] + crop["w"] or y0 > crop["y"] + crop["h"]:
            out.append(engine.Note("plan_outside", f"{where}: {label} lies outside the plan's frame and will not be seen in the report", plan=pid, label=label))
            continue
        frame = plan_svg.number_frame(element, sz)
        if frame is not None and frame["moved"]:
            x0, y0, x1, y1 = bbox(plan_svg.number_corners(frame))
            if x0 < crop["x"] or y0 < crop["y"] or x1 > crop["x"] + crop["w"] or y1 > crop["y"] + crop["h"]:
                out.append(engine.Note("plan_number_outside", f"{where}: {label}'s number was moved out of the plan's frame, which will cut it off in the report", plan=pid, label=label))
    linear = [dim for dim in source.get("dimensions") or [] if dim.get("kind") != "angle"]
    if linear and not units_per_m(source):
        # a length cannot be measured without a scale: the dimensions are drawn nowhere, and said (issue #9, D-016)
        out.append(engine.Note("plan_dimensions_no_scale", f"{where}: {len(linear)} dimension(s) measure lengths and the plan has no scale -- calibrate it, or they are not drawn", plan=pid, count=len(linear)))
    return list(dict.fromkeys(out))


# --- The report record ---------------------------------------------------------------

def build_record(source, sheet, background=None):
    """One plan as it enters data/plans.json: the frame the report shows, the files under data/ it is drawn with, its scale, the size unit of its symbols, its legend's lines, and its elements and axes with what show-plan needs to highlight one or frame a detail around it -- a numbered element's points, and where its number is drawn.

    An element or an axis that states a factor of its own over the plan's three carries it here too (`figure_style.record`), and one that states none carries nothing: the record then says with what the figure beside it was drawn, which is the convention every other placed value of this export follows. `label_at` needs no such thought -- `plan_svg.number_frame` reads the element's own factors itself -- and a wall's `length_m` and an axis's `segment` are geometry, which no factor touches.
    """
    from domains import plan_svg  # the drawing module draws what this module describes

    pid = source["id"]
    crop = crop_of({**source, "sheet": {"width": sheet[0], "height": sheet[1]}})
    sz = plan_svg.Sizes(plan_svg.base_unit(crop), source["style"])
    per_m = units_per_m(source)
    scale = None
    if per_m:
        scale = {"mode": source["scale"]["mode"], "units_per_m": _clean(per_m)}
        if source["scale"]["mode"] == "ratio":
            scale["ratio"] = source["scale"]["ratio"]
    elements = []
    for element in source["elements"]:
        kind = element_kind(element)
        record = {
            "type": element["type"],
            "label": element.get("label", ""),
            "kind": kind,
            "points": [[_clean(x), _clean(y)] for x, y in element["points"]],
        }
        if element.get("subtype") is not None:
            record["subtype"] = element["subtype"]
        if "angle" in element:
            record["angle"] = _clean(element["angle"])  # a load symbol's horizontal direction (v0.116)
        own = figure_style.record(element)
        if own is not None:
            record["style"] = own
        if per_m and kind != "point":
            record["length_m"] = _clean(element_length_m(element, per_m))
        frame = plan_svg.number_frame(element, sz)
        if frame is not None:
            # the centre of its number, in its own place or where it was moved to: a detail frames it with the element
            record["label_at"] = [_clean(frame["at"][0]), _clean(frame["at"][1])]
        elements.append(record)
    axes = []
    for axis in source["axes"]:
        segment = axis_segment(axis, crop)
        entry = {
            "label": axis["label"],
            "point": [_clean(v) for v in axis["point"]],
            "angle": axis["angle"],
            "bubbles": axis.get("bubbles", "both"),
            "segment": [[_clean(v) for v in p] for p in segment] if segment else [],
        }
        own = figure_style.record(axis)
        if own is not None:
            entry["style"] = own
        axes.append(entry)
    record = {
        "label": source.get("label", ""),
        "floor": source.get("floor", ""),
        "source": f"plans/{pid}.json",
        "sheet": {"width": _clean(sheet[0]), "height": _clean(sheet[1])},
        "crop": {key: _clean(value) for key, value in crop.items()},
        "overlay": f"plans/{pid}.svg",
        "legend": plan_svg.legend_items(source),
        "unit": _clean(plan_svg.base_unit(crop)),
        "style": {key: float(source["style"].get(key, 1.0)) for key in STYLE_KEYS},
        "elements": elements,
        "axes": axes,
        "labels": plan_labels(source),
    }
    if background is not None:
        record["background"] = background
    if scale is not None:
        record["scale"] = scale
    # 1.3: the storey, the role, the section a floor plan refers to, and a section's storey lines and boxes in sheet units -- show-plan draws the box of the storey a sheet highlights, the overlay the lines
    record["storey"] = source.get("storey", "")
    # v0.116: the plan's name, which an export sheet heads the plan with -- «Nom — description, étage (éch. 1:n)» (lib/sheet.typ's sheet-plan-title)
    record["name"] = source.get("name", "")
    record["role"] = source.get("role", "plan")
    if source.get("section_plan"):
        record["section_plan"] = source["section_plan"]
    if record["role"] == "section":
        record["storey_lines"] = [{"storey": line["storey"], "points": [[_clean(x), _clean(y)] for x, y in line["points"]]}
                                  for line in source.get("storey_lines") or []]
        boxes = source.get("storey_boxes") or []
        record["storey_boxes"] = [{"storey": box["storey"], **{key: _clean(box[key]) for key in ("x", "y", "w", "h")},
                                   **({"floor": box["floor"]} if box.get("floor") else {})}
                                  for box in boxes]
        # v0.116: a section's load transfer levels, and each box's STE designation (x1xx) -- written only where the section has a level or a box, so a section drawn before is exported as it was
        if source.get("load_levels"):
            record["load_levels"] = [{"storey": level["storey"], "designation": storey_designation(level, boxes),
                                      "points": [[_clean(x), _clean(y)] for x, y in level["points"]],
                                      **({"floor": level["floor"]} if level.get("floor") else {})}
                                     for level in source["load_levels"]]
    # v0.116: the plan's type, where it states one -- a plan that states none is a floor plan or a section by its role, and is exported as it was
    if source.get("plan_type"):
        record["plan_type"] = source["plan_type"]
    # issue #9: the dimensions, each with what it measures -- computed here, never typed -- and written only where the plan has some it can measure, so a plan without is exported as it was
    measured = []
    for dim in source.get("dimensions") or []:
        parts = dimension_parts(source, dim)
        if parts:
            measured.append({"kind": dim["kind"], "points": [[_clean(x), _clean(y)] for x, y in dim["points"]],
                             "values": [_clean(part["value"]) for part in parts], "unit": parts[0]["unit"]})
    if measured:
        record["dimensions"] = measured
    return record


# --- Export ----------------------------------------------------------------------------

def _extract_pdf_page(path, page):
    """The one page drawn on, as a PDF of its own: a plan set of 25 sheets is 8 MB, the page a small part of it. Its crop box and /Rotate go with it, so Typst shows it as Woodcore's window did."""
    from pypdf import PdfWriter

    reader = _pdf_reader(path)
    writer = PdfWriter()
    writer.add_page(reader.pages[page - 1])
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def _hidden_layers(path):
    """How many of a PDF's layers are hidden by default. Typst draws every layer, so a hidden one would appear in the report."""
    try:
        root = _pdf_reader(path).trailer["/Root"]
        properties = root.get("/OCProperties")
        if properties is None:
            return 0
        default = properties.get_object().get("/D")
        return len(default.get_object().get("/OFF", [])) if default is not None else 0
    except Exception:  # broad: pypdf raises a family of its own -- a layer table that cannot be read hides nothing we can tell of
        return 0


def _previous(data_dir):
    path = Path(data_dir) / "plans.json"
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("plans", {})
    except (OSError, ValueError, AttributeError):
        return {}


def prepare(source_dir, project_root, data_dir, position_ids, values=None):
    """(data, files, warnings): data/plans.json as it will be written, every file under data/plans/ it refers to (path relative to data/ -> bytes or text), and the warnings to print -- built and validated from every source file, nothing written yet, so export_all.py can check the plans along with everything else before it writes anything. A background already extracted from the same file and page is kept as it is: pypdf would write the same page with a new document id, and Git would see a change that is none."""
    from domains import plan_svg

    data_dir = Path(data_dir)
    previous = _previous(data_dir)
    plans, files, notes = {}, {}, []
    sources = [read_source(path) for path in source_paths(source_dir)]
    sections = {source["id"] for source in sources if source.get("role", "plan") == "section"}
    for source in sources:
        pid = source["id"]
        where = f"plans/{pid}.json"
        sheet = (float(source["sheet"]["width"]), float(source["sheet"]["height"]))
        background = None
        spec = source.get("background")
        document = document_background(spec, project_root, source_dir, data_dir, f"plans/{pid}-plan", previous.get(pid, {}).get("background", {}), where, f"plan {pid}", files, notes, plan=pid) if spec and spec.get("document") else None
        if document is not None:
            background, actual = document
            if abs(actual[0] - sheet[0]) > 0.5 or abs(actual[1] - sheet[1]) > 0.5:
                notes.append(engine.Note("plan_sheet_moved", f"plan {pid}: page {spec['page']} of document {spec['document']} is now {actual[0]:.0f} × {actual[1]:.0f} and not {sheet[0]:.0f} × {sheet[1]:.0f} as when it was drawn on -- open the plan in Woodcore and check its symbols", plan=pid, document=spec["document"], page=spec["page"]))
                sheet = actual
            spec = None  # drawn
        if source.get("section_plan") and source["section_plan"] not in sections:
            notes.append(engine.Note("plan_section_missing", f"plan {pid}: its section {source['section_plan']} is not a section plan of this project", plan=pid, section=source["section_plan"]))
        if spec is not None:
            background, sheet, more = file_background(spec, sheet, project_root, data_dir, f"plans/{pid}-plan", previous.get(pid, {}).get("background", {}), where, f"plan {pid}", files)
            notes += more
        drawn = {**source, "sheet": {"width": sheet[0], "height": sheet[1]}}
        notes += warnings(drawn, position_ids)
        record = build_record(drawn, sheet, background)
        record["unknown"] = sorted({label for label in record["labels"] if label not in set(position_ids)})
        texts = text_records(drawn, values, f"plan {pid}", notes)
        if texts:
            record["texts"] = texts
        plans[pid] = record
        crop = record["crop"]
        files[record["overlay"]] = plan_svg.render(drawn, crop, values=values)
        if drawn.get("load_levels"):
            # a load transfer level writes «Niveau de reprise des charges (x0xx)» on the plan, the engine's words: such a section is drawn once per language, as a fire-protection plan is, and show-plan sets the report's (lib/calc-engine.typ's plan-figure reads `figures`). Its `overlay` stays, the German one, for whatever reads it.
            from i18n import strings
            record["figures"] = {}
            for lang in strings.LANGUAGES:
                name = f"plans/{pid}-{lang}.svg"
                record["figures"][lang] = name
                files[name] = plan_svg.render(drawn, crop, lang=lang, values=values)
    data = {"schema_version": TEXT_EXPORT_VERSION if any("texts" in r for r in plans.values()) else EXPORT_SCHEMA_VERSION, "plans": plans}
    validation.validate_structure(data, "plans")
    validation.validate_plans_business(data)
    return data, files, notes


def document_background(spec, project_root, plans_dir, data_dir, stem, old, where, what, files, notes, plan=None):
    """(the record's background, the page's sheet) for a drawing made on a page of a document of plans/documents/ -- the page flattened to a PDF of its own with the document's switched-off layers taken out, or a drawing's layout as an SVG (calc/domains/plan_documents.py) -- or None where the document is gone, said in a warning and the drawing then drawn on its file as it was saved (`background.file`). `spec` is the source's `background`, `plans_dir` the folder the documents live under (plans/documents/), `stem` the file's name under data/ without its extension (`plans/<id>-plan`), `old` the background the last export recorded for this drawing, `what` how the notes name it (`plan P01`), `where` how a refusal names its file. The file written is put in `files` (its path under data/ -> bytes) and the notes in `notes`. A background already written for the same file, page, rotation and layers is kept as it is, as for any plan: pypdf would write the same page with a new document id, and Git would see a change that is none. A function of its own since a fire-protection plan drawn on a page exports its background the same way."""
    from domains import plan_documents

    place = plan_documents.Place(project_root, plans_dir)
    try:
        doc = plan_documents.read(place, spec["document"])
        path = plan_documents.file_path(place, doc)
    except validation.ValidationError as exc:
        notes.append(engine.Note("plan_document_missing", f"{what}: its document {spec['document']} cannot be read ({exc}) -- the plan is drawn on {spec['file']} as it was saved", plan=plan, document=spec["document"], reason=str(exc)))
        return None
    page = spec["page"]
    try:
        actual = plan_documents.page_size(place, doc, page)
    except plan_documents.DocumentError as exc:
        _fail(where, str(exc))
    digest = file_hash(path)
    key = plan_documents.export_key(doc, page)
    fmt = "pdf" if doc["kind"] == "pdf" else ("svg" if doc["kind"] in ("cad", "svg") or key["rotation"] else background_format(path))
    name = f"{stem}.{fmt}"
    kept = Path(data_dir) / name
    if (old.get("file") == name and old.get("sha256") == digest and old.get("origin_page") == page
            and old.get("document") == doc["id"] and old.get("rotation") == key["rotation"]
            and old.get("layers_off") == key["layers_off"] and kept.is_file()):
        files[name] = kept.read_bytes()
    else:
        content, fmt_made = plan_documents.background(place, doc, page)
        if fmt_made != fmt:  # an image turned is an SVG; the name follows what was made
            fmt, name = fmt_made, f"{stem}.{fmt_made}"
        files[name] = content
    if spec.get("sha256") and spec["sha256"] != digest:
        notes.append(engine.Note("plan_background_changed", f"{what}: {doc['file']} has changed since the plan was saved -- check that the symbols still sit on it, then save the plan again", plan=plan, file=doc["file"]))
    background = {
        "file": name,
        "format": fmt,
        "page": 1,  # one page, the one drawn on
        "origin": doc["file"],
        "origin_page": page,
        "sha256": digest,
        "opacity": float(spec.get("opacity", DEFAULT_OPACITY)),
        "document": doc["id"],
        "rotation": key["rotation"],
        "layers_off": key["layers_off"],
    }
    return background, actual


_document_background = document_background  # the name the function had until it was shared


def file_background(spec, sheet, project_root, data_dir, stem, old, where, what, files):
    """(the record's background, the sheet as the file now gives it, the notes to print) for a drawing made directly on a file of the project -- a PDF reduced to the page drawn on, a PNG, a JPEG or an SVG copied. `spec` is the source's `background`, `sheet` its sheet as (width, height), `stem` the file's name under data/ without its extension, `old` the background the last export recorded for this drawing; the file written is put in `files`. A background already extracted from the same file and page is kept as it is -- pypdf would write the same page with a new document id, and Git would see a change that is none. A function of its own since a fire-protection plan with a frame of its own exports its background by the very same steps."""
    notes = []
    path = background_path(project_root, spec["file"])
    if path is None:
        _fail(where, f"background {spec['file']!r} lies outside the project folder -- copy it into the folder first")
    fmt = background_format(path)
    actual = sheet_of(path, fmt, spec["page"], where)
    if abs(actual[0] - sheet[0]) > 0.5 or abs(actual[1] - sheet[1]) > 0.5:
        notes.append(f"{what}: {spec['file']} page {spec['page']} is now {actual[0]:.0f} × {actual[1]:.0f} and not {sheet[0]:.0f} × {sheet[1]:.0f} as when it was drawn on -- open the plan in Woodcore and check its symbols")
        sheet = actual
    digest = file_hash(path)
    if spec.get("sha256") and spec["sha256"] != digest:
        notes.append(f"{what}: {spec['file']} has changed since the plan was saved -- check that the symbols still sit on it, then save the plan again")
    name = f"{stem}.{fmt}"
    kept = Path(data_dir) / name
    if (old.get("file") == name and old.get("sha256") == digest and old.get("origin_page") == spec["page"]
            and old.get("origin") == spec["file"] and kept.is_file()):
        files[name] = kept.read_bytes()
    elif fmt == "pdf":
        files[name] = _extract_pdf_page(path, spec["page"])
        if _hidden_layers(path):
            notes.append(f"{what}: {spec['file']} hides some of its layers by default -- the report draws every layer of a file drawn on directly; draw the plan on its document (plans/documents/) and the report hides them")
    else:
        files[name] = path.read_bytes()
    if fmt == "svg":
        _size, proportional, _origin = _svg_size(path.read_bytes())
        if not proportional:
            notes.append(f"{what}: {spec['file']} is set at a size that does not keep its viewBox's proportions -- the report may shift it against the symbols")
    background = {
        "file": name,
        "format": fmt,
        "page": 1,  # a PDF is reduced to the page drawn on
        "origin": spec["file"],
        "origin_page": spec["page"],
        "sha256": digest,
        "opacity": float(spec.get("opacity", DEFAULT_OPACITY)),
    }
    return background, sheet, notes


def write(data, files, data_dir):
    """Writes data/plans.json and data/plans/, and removes the files of a plan that no longer exists -- that folder is generated, like the rest of data/. A file whose content has not changed is left alone."""
    data_dir = Path(data_dir)
    engine.write_json(data_dir / "plans.json", data)
    folder = data_dir / "plans"
    folder.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        target = data_dir / name
        payload = content.encode("utf-8") if isinstance(content, str) else content
        if target.is_file() and target.read_bytes() == payload:
            continue
        target.write_bytes(payload)
    wanted = {Path(name).name for name in files}
    for stale in folder.iterdir():
        if stale.is_file() and stale.name not in wanted:
            stale.unlink()


def export(source_dir, project_root, data_dir, position_ids, values=None):
    """The plans' part of the export, on its own: what Woodcore's window runs when a plan is saved, so the report sees it without the load workbooks being read again. export_all.py runs the same two steps. `values` are the export's, which a text's variables print (issue #43). Returns the warnings."""
    data, files, notes = prepare(source_dir, project_root, data_dir, position_ids, values)
    write(data, files, data_dir)
    return notes


def known_positions(data_dir):
    """The position ids of the last export (data/positions-index.json), for a plan exported on its own; none where there is no export yet."""
    try:
        return json.loads((Path(data_dir) / "positions-index.json").read_text(encoding="utf-8"))["positions"]
    except (OSError, ValueError, KeyError):
        return []


def turn_point(p, height):
    """A point of a sheet `height` high, y down, where it lands when the page is turned a quarter clockwise."""
    return [_clean(height - float(p[1])), _clean(float(p[0]))]


def turn_rect(rect, height):
    """A rectangle {x, y, w, h} turned a quarter clockwise with a sheet `height` high."""
    return {**rect, "x": _clean(height - float(rect["y"]) - float(rect["h"])), "y": _clean(float(rect["x"])),
            "w": _clean(float(rect["h"])), "h": _clean(float(rect["w"]))}


_turn_point, _turn_rect = turn_point, turn_rect  # the names the two had until a fire plan turned with the same helpers


def _turn_quarter(source, width, height):
    """The source turned a quarter clockwise, with the page it is drawn on: a point (x, y) of the old sheet goes to (height - y, x), a vector (dx, dy) to (-dy, dx), an angle gains 90°."""
    old_window = {"x": 0.0, "y": 0.0, "w": width, "h": height}
    new_window = {"x": 0.0, "y": 0.0, "w": height, "h": width}
    for element in source.get("elements", []):
        element["points"] = [turn_point(p, height) for p in element.get("points", [])]
        if element.get("label_offset"):
            dx, dy = element["label_offset"]
            element["label_offset"] = [_clean(-float(dy)), _clean(float(dx))]
        if element.get("span") is not None:
            element["span"] = _clean(normalize_angle(float(element["span"]) + 90))
        if element.get("angle") is not None:
            element["angle"] = _clean(normalize_angle(float(element["angle"]) + 90))
    for axis in source.get("axes", []):
        before = axis_segment(axis, old_window)
        axis["point"] = turn_point(axis["point"], height)
        axis["angle"] = _clean(math.fmod(float(axis["angle"]) + 90, 180.0) % 180.0)
        bubbles = axis.get("bubbles", "both")
        if before is not None and bubbles in ("start", "end"):
            # a bubble stays at the end of the axis it was drawn at: the old start is the new start or the new end
            after = axis_segment(axis, new_window)
            if after is not None:
                start = turn_point(before[0], height)
                if math.dist(start, after[0]) > math.dist(start, after[1]):
                    axis["bubbles"] = "end" if bubbles == "start" else "start"
    if source.get("crop"):
        source["crop"] = turn_rect(source["crop"], height)
    scale = source.get("scale")
    if scale and scale.get("mode") == "calibration" and isinstance(scale.get("points"), list):
        scale["points"] = [turn_point(p, height) for p in scale["points"]]
    for line in source.get("storey_lines") or []:
        line["points"] = [turn_point(p, height) for p in line.get("points", [])]
    if source.get("storey_boxes"):
        source["storey_boxes"] = [turn_rect(box, height) for box in source["storey_boxes"]]
    for level in source.get("load_levels") or []:
        level["points"] = [turn_point(p, height) for p in level.get("points", [])]
        if level.get("label_offset"):
            dx, dy = level["label_offset"]
            level["label_offset"] = [_clean(-float(dy)), _clean(float(dx))]
    # a plan's dimensions turn with it (issue #9 left them where they were; issue #18's review found it) -- their offset is measured from their own line, and turns with it -- and so do its construction aids, as an axis
    for dim in source.get("dimensions") or []:
        dim["points"] = [turn_point(p, height) for p in dim.get("points", [])]
        if dim.get("axis") in ("horizontal", "vertical"):
            dim["axis"] = "vertical" if dim["axis"] == "horizontal" else "horizontal"
        if dim.get("kind") in ("horizontal", "vertical"):
            dim["kind"] = "vertical" if dim["kind"] == "horizontal" else "horizontal"
    for text in source.get("texts") or []:
        text["points"] = [turn_point(p, height) for p in text.get("points", [])]   # a text stays where it was written, and reads upright on the turned page
    for aid in source.get("aids") or []:
        aid["point"] = turn_point(aid["point"], height)
        aid["angle"] = _clean(lines.normal_angle(float(aid["angle"]) + 90))
        if aid.get("kind") in ("horizontal", "vertical"):
            aid["kind"] = "vertical" if aid["kind"] == "horizontal" else "horizontal"
    return source


def rotate_source(source, quarter_turns, old_sheet):
    """A copy of `source` with everything drawn on it turned with its page, `quarter_turns` quarters clockwise (negative: anticlockwise) from a sheet of `old_sheet` (width, height) -- the elements, their numbers moved by hand, a slab's span, the axes (point and angle, a bubble kept at the end it was at), the crop, a calibration's two points, a section's storey lines and boxes -- so that what was drawn stays on the architecture when the engineer turns a page of its document (plan_documents.set_rotation). The sheet becomes the turned one."""
    turned = copy.deepcopy(source)
    turns = int(quarter_turns) % 4
    width, height = float(old_sheet[0]), float(old_sheet[1])
    if not turns:
        return turned
    for _ in range(turns):
        turned = _turn_quarter(turned, width, height)
        width, height = height, width
    turned["sheet"] = {"width": _clean(width), "height": _clean(height)}
    return turned


def snapshot(source):
    """A deep copy of a source, for an undo history."""
    return copy.deepcopy(source)
