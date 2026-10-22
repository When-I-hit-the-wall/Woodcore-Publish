"""Detail schemas (Schémas), drawn in Woodcore and exported as a figure for the report (docs/domain/detail-schemas.md §3.3decies).

A schema is the one drawing of a connection detail: the pieces (a beam, a plate, seen edge-on or face-on), the fastener markers, the construction lines and points that helped draw it, and its dimensions. It replaces the two forms of geometry *Connecteurs* and *Moments polaires* used to carry separately -- one drawing, named by both. This module owns its source file, `details/<id>.json`, which Woodcore writes and nothing else does -- the arrangement the connections, the plans and the static models already have, for the same reasons (docs/decisions.md §13).

⚠️ **The source folder is `details/`, not `schemas/`.** The plan this module was built from (je-souhaite-commencer-generic-valley.md) names the folder after the module, "schemas/<id>.json" -- and `000-Python/schemas/` was already the home of every `*.schema.json` contract (docs/architecture/layout.md §11), `schema.py`'s own two included. Reading sources from there would have `source_paths()` glob up `connectors.schema.json`, `statics-source.schema.json` and the rest as if they were schemas to draw -- caught immediately (`schema_version is None`, the first `*.schema.json` file alphabetically has none) but only once something was actually exported into it. `details/` is the plan's own word for what this draws ("un schéma est un détail à l'échelle réelle"), so nothing else had to be renamed: the module, its functions, `show-schema`, `data/schemas.json` and the `schemas/*.schema.json` contracts that describe both keep their names.

The frame is the connections' (section 3.3quinquies): **millimetres**, x to the right, z down, angles in degrees from +x turning towards +z, clockwise as the figure is read. Unlike a static model, whose drawing is a scale-free sketch normalised to 1000 figure units, a schema is a **detail at its real size**: its coordinates ARE millimetres, scaled to `PAPER_MM` only when it is rendered, as connector_svg.section() already does. That is what lets a connector or a moment-polaire calculation place its own force arrows over this drawing with no conversion at all.

There is no Qt in this file, so Woodcore's canvas and a test script call the same functions.

**Where this module's design departs from a literal reading of the plan, and why (flagged here since the plan itself asks that an assumption be stated where one had to be made, section "Hypothèse à confirmer").** The plan lists four collections -- elements, connectors, aids, dimensions -- and no fifth, flat `points` collection; a named point is therefore an aid of kind `centre` or `point` (the project's convention, docs/decisions.md, of stating a design choice applies here as it does everywhere else in this project). Two functions that are genuinely generic are reused unchanged: `plan.constrain` (pure tuple arithmetic) and `plan.nearest_vertex` (reads only an entry's own `points` list). The plan also names `plan.SnapIndex`, `plan.hit_element`, `plan.hit_label`, `plan.nearest_point`, and `statics.dimension_*`/`tracking_rays`/`nearest_ray`/`extension_lines`/`typed_point`/`track` as reusable: those are bound to their own modules' data shapes (plan.py's STE-typed elements with a `TYPES` z-order; statics.py's flat `points` collection and its `members` that reference two of them by id) which a schema's elements -- each carrying its own point list, `linear` or `area` -- do not share. They are therefore **ported** here rather than imported: the same algorithm, the same names wherever the vocabulary still fits, adapted to a schema's own shapes. `schema_svg.py` carries the same relationship to `connection_svg.py` and `statics_svg.py` for the same reason.
"""

import copy
import json
import math
import re
from pathlib import Path

import engine
import validation
from domains._common import check_number as _number, fail as _fail  # one copy of the domains' helpers (spec 2026-10-19-base-saine-nettoyage, G4)
from domains import connector, figure_style, section as position_section
from domains import dimension  # a dimension's geometry, shared with the static models and the plans (issue #9)
from domains import figure_text  # a text placed with the Text tool, the four engines' one (issue #43, ARCH-003)
from domains.plan import constrain, nearest_vertex  # generic geometry, unchanged by a schema's shapes
from i18n import strings
from domains.schema_geometry import (  # split out of this module (issue #30): every name it had is still importable from it
    AID_ANGLE_KINDS,
    AID_POINT_KINDS,
    AID_TWO_POINT_KINDS,
    ANGLE_DIGITS,
    DIGITS,
    DIMENSION_UNITS,
    ELEMENT_DEFAULT_WIDTH,
    ELEMENT_SIDES,
    ELEMENT_VIEWS,
    LABEL_MODES,
    PARALLEL_TOLERANCE,
    SAME_POINT,
    SNAP_KINDS,
    TRACK_ANGLES,
    TRACK_TOLERANCE_DEG,
    _all_segments,
    _anchor_ref,
    _cross,
    _direction_of,
    _inside,
    _member_ray,
    _midpoint,
    _point_segment,
    _stated,
    _tidy,
    _unit_towards,
    aid_line,
    aid_point,
    along,
    angle_rays,
    area_fixed,
    band_outlines,
    bbox,
    default_fasteners,
    dimension_anchor,
    dimension_angle,
    dimension_corner,
    dimension_direction,
    dimension_ends,
    dimension_line,
    dimension_show,
    dimension_text,
    dimension_value,
    dimension_value_text,
    element_bbox,
    element_caption,
    element_direction,
    element_kind,
    element_middle,
    element_section,
    element_width,
    entry_of,
    extension_lines,
    fastener_places,
    figure_number,
    fmt_number,
    grid_snap,
    hit_aid_line,
    hit_aid_point,
    hit_connector,
    hit_element,
    hit_label,
    index_of,
    named_point,
    nearest_ray,
    normalize_angle,
    perpendicular_offset,
    position_records,
    rectangle_from_edge,
    rectangle_two_corners,
    rectangle_with_fixed_side,
    rectangle_with_fixed_width,
    reference_direction,
    segments_of,
    snap,
    snap_geometry,
    snap_targets,
    track,
    tracking_rays,
    typed_point,
)
from domains.schema_edit import (  # split out of this module (issue #30): every name it had is still importable from it
    ENTITIES,
    ENTITY_PREFIX,
    Refused,
    _chain,
    _cut_points,
    _drop_collinear,
    _drop_repeats,
    _line_of_aid,
    _modify_entry,
    _place_point,
    _polygon_pieces,
    _polyline_pieces,
    _shared_edge,
    _splice,
    all_ids,
    duplicate,
    find_entry,
    merge_elements,
    modify,
    next_id,
    reflection,
    remove,
    rotation,
    round_place,
    split_element,
    translation,
    used_by,
)
from domains._common import source_paths  # one copy (G4)

# Of a source file (details/<id>.json) and of the export (data/schemas.json). 1.1 (v0.75): an element states its section as `b` and `h`, each following its position unless written over, and `width` is gone; a 1.0 source is read as it stands, its `width` becoming the side its view shows (`upgrade_source`). A schema may also carry a `crop`.
SOURCE_SCHEMA_VERSION = "1.1"
# 1.2 is 1.1 with `texts`, the Text tool's (issue #43, spec 2026-10-11-variables-liees-champs-et-textes): written only by a schema that holds one, so a schema without a text is saved and exported as before
TEXT_SCHEMA_VERSION = "1.2"
SOURCE_SCHEMA_VERSIONS = ("1.0", SOURCE_SCHEMA_VERSION, TEXT_SCHEMA_VERSION)
EXPORT_SCHEMA_VERSION = "1.1"
# 1.2 is 1.1 with a schema's `texts`, what each printed: written only where one holds a text
TEXT_EXPORT_VERSION = "1.2"
# 1.3 is 1.2 with its figures named from the Typst root (`/Details/Exports/Figures/D01-fr.svg`): written by a project laid out by folders, where they lie in the tab's Exports/Figures/ (issue #64, D-10)
ROOTED_EXPORT_VERSION = "1.3"
# 1.4 (v0.120, spec 2026-10-19-base-saine-nettoyage, D7) is 1.3 with each schema's `size`, the extent schema_svg.layout sizes its symbols by, which the report's halo reads rather than working it out again from the geometry. Written by every export since -- with texts or without, laid out by folders or not, which the record itself says (`texts`, a figure named from the root).
SIZE_EXPORT_VERSION = "1.4"

# A schema's id is the file name of its source and the string the report addresses it by -- the connections', the plans' and the static models' own rule.
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$")

# The id of an element, a connector marker, an aid or a dimension. Kept narrower than a schema's own, since it is typed into a table cell and read back in a list of choices -- statics.py's ENTITY_ID, unchanged.
ENTITY_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


# The three factors the drawing is set with -- the strokes, the symbols placed on a point, the texts -- and the range a slider moves them over (v0.99). `figure_style`'s own, so that a slider means in this tab exactly what it means in the plans' and the static models' (docs/ui/window.md §10quater); the names are kept here because the tab reads them from its own model, as the other two do.
STYLE_KEYS = figure_style.KEYS
STYLE_RANGE = figure_style.RANGE


# A piece is drawn edge-on (a polyline of at least two points, its width one of the section's two dimensions) or face-on (a polygon of at least three).
ELEMENT_KINDS = ("linear", "area")
ELEMENT_MIN_POINTS = {"linear": 2, "area": 3}


# The fastener kinds a marker may carry -- connector.TYPES, so a marker drawn here already says roughly what it will be calculated as, and the *Connecteurs* tab offers exactly the same tool bar (docs/domain/connectors.md §3.3nonies). One source of truth: this module never restates the list.
CONNECTOR_KINDS = tuple(connector.TYPES)

AID_KINDS = AID_POINT_KINDS + AID_ANGLE_KINDS + AID_TWO_POINT_KINDS

# What a dimension measures -- statics.py's own four, taken as-is (docs/domain/static-models.md §3.3octies).
DIMENSION_KINDS = dimension.KINDS
DIMENSION_LINEAR = dimension.LINEAR


# The grid steps in millimetres the editor snaps to, coarsest first, each with the interval its heavier lines are drawn at. "auto" takes the finest step still far enough apart on screen -- statics.py's mechanism, in mm rather than m.
GRID_STEPS = ((1000.0, 5000.0), (100.0, 500.0), (10.0, 50.0), (1.0, 5.0))
GRID_SNAPS = tuple(step for step, _heavy in GRID_STEPS)


def _string(value, where, what, blank=False):
    if not isinstance(value, str):
        _fail(where, f"{what} must be text, got {value!r}")
    if not blank and not value.strip():
        _fail(where, f"{what} must not be empty")
    return value


def _one_of(value, allowed, where, what):
    if value not in allowed:
        _fail(where, f"{what} is {value!r} -- expected {', '.join(map(str, allowed))}")
    return value


def _point(p, where, what):
    if not isinstance(p, (list, tuple)) or len(p) != 2:
        _fail(where, f"{what} must be [x, z], got {p!r}")
    return (_number(p[0], where, f"{what}'s x"), _number(p[1], where, f"{what}'s z"))


# --- The source file --------------------------------------------------------------


def _check_style(style, where, what, may=None):
    """The three factors a schema, or one entry of it, is drawn with -- `figure_style`'s own check, raised through this module's own refusal so the message names the file and the entry like every other one here (v0.99).

    `may` is the factors the entry is drawn with, `None` for the drawing itself, which is drawn with all three.
    """
    figure_style.check(style, lambda message: _fail(where, message),
                       may=figure_style.KEYS if may is None else may, what=what)


def _check_label_offset(entry, where, what):
    if "label_offset" in entry:
        _point(entry["label_offset"], where, f"{what}'s label_offset")


def _check_element(element, where):
    what = f"element {element['id']}"
    kind = _one_of(element.get("kind"), ELEMENT_KINDS, where, f"{what}'s kind")
    points = element.get("points")
    if not isinstance(points, list) or len(points) < ELEMENT_MIN_POINTS[kind]:
        _fail(where, f"{what} ({kind}) needs at least {ELEMENT_MIN_POINTS[kind]} points, got {len(points) if isinstance(points, list) else points!r}")
    for i, p in enumerate(points, start=1):
        _point(p, where, f"{what}'s point {i}")
    if kind == "linear":
        if "view" in element:
            _one_of(element["view"], ELEMENT_VIEWS, where, f"{what}'s view")
    elif "view" in element:
        _fail(where, f"{what} is an area and carries a view -- only a linear element does")
    if "width" in element:
        _fail(where, f"{what} carries a width -- since schema 1.1 an element states its section as b and h, and its band is the side its view shows")
    for side in ELEMENT_SIDES:
        if element.get(side) is not None:
            _number(element[side], where, f"{what}'s {side}", positive=True)
    if "position" in element and element["position"] is not None:
        _string(element["position"], where, f"{what}'s position")
    _string(element.get("label", ""), where, f"{what}'s label", blank=True)
    _check_label_offset(element, where, what)


def _check_connector(marker, where):
    what = f"connector {marker['id']}"
    _one_of(marker.get("kind"), CONNECTOR_KINDS, where, f"{what}'s kind")
    _number(marker.get("x"), where, f"{what}'s x")
    _number(marker.get("z"), where, f"{what}'s z")
    diameter = marker.get("diameter")
    if diameter is not None:
        if not isinstance(diameter, dict):
            _fail(where, f"{what}'s diameter must be an object, got {diameter!r}")
        _number(diameter.get("value"), where, f"{what}'s diameter", positive=True)
        _string(diameter.get("unit", ""), where, f"{what}'s diameter unit")
    _check_label_offset(marker, where, what)


def _check_aid(aid, where):
    what = f"aid {aid['id']}"
    kind = _one_of(aid.get("kind"), AID_KINDS, where, f"{what}'s kind")
    if kind in AID_TWO_POINT_KINDS:
        for key in ("x1", "z1", "x2", "z2"):
            _number(aid.get(key), where, f"{what}'s {key}")
        if math.dist((aid["x1"], aid["z1"]), (aid["x2"], aid["z2"])) <= SAME_POINT:
            _fail(where, f"{what} has the same point twice -- an aid needs two distinct points")
        for key in ("angle",):
            if key in aid:
                _fail(where, f"{what} is 'two-points' and carries an angle -- only a line aid measured from one point does")
    else:
        _number(aid.get("x"), where, f"{what}'s x")
        _number(aid.get("z"), where, f"{what}'s z")
        if kind in AID_ANGLE_KINDS:
            _number(aid.get("angle"), where, f"{what}'s angle")
        elif "angle" in aid:
            _fail(where, f"{what} is a {kind!r} and carries an angle -- only a construction line does")
    if "shown" in aid and not isinstance(aid["shown"], bool):
        _fail(where, f"{what}'s shown must be true or false, got {aid['shown']!r}")
    _string(aid.get("label", ""), where, f"{what}'s label", blank=True)
    _check_label_offset(aid, where, what)


def _check_anchor(anchor, where, what, kind, point_ids, direction_ids):
    """One end of a dimension: a direction for an angle -- a linear element or a line-shaped aid -- and for the three linear kinds an aid of kind 'centre'/'point', or a place of its own. statics.py's own rule (section 3.3octies), adapted to a schema's collections.

    `direction_ids` is keyed by what the anchor may name, `{"element": ..., "aid": ...}`, so that an angle naming a **point**-shaped aid is refused for the reason it is wrong -- a point has no direction -- rather than for one that is untrue of it.
    """
    if not isinstance(anchor, dict):
        _fail(where, f"{what} is {anchor!r} -- a point, an element, an aid, or a place of its own")
    if kind == "angle":
        given = [k for k in ("element", "aid") if anchor.get(k)]
        if len(given) != 1:
            _fail(where, f"{what} must name exactly one of an element or an aid, got {sorted(anchor)}")
        key = given[0]
        allowed = direction_ids[key]
        if anchor[key] not in allowed:
            what_it_is = "a linear element" if key == "element" else "a construction line"
            _fail(where, f"{what} is {key} {anchor[key]!r}, which the schema has no direction of -- "
                         f"an angle is measured between two directions, so each end names {what_it_is}"
                         + (f" ({', '.join(sorted(allowed))})" if allowed else ", and this schema has none"))
        return
    if anchor.get("element") or anchor.get("aid"):
        _fail(where, f"{what} names an element or an aid -- only an angle is measured between two directions")
    if "point" in anchor:
        if anchor["point"] not in point_ids:
            _fail(where, f"{what} is at {anchor['point']!r}, which the schema has no aid point of")
        return
    if "x" not in anchor or "z" not in anchor:
        _fail(where, f"{what} names no point and gives no place of its own -- it needs one or the other")
    _number(anchor.get("x"), where, f"{what}'s x")
    _number(anchor.get("z"), where, f"{what}'s z")


def upgrade_source(source):
    """A source as schema 1.1 describes it, converted in place and returned.

    A 1.0 element carried one number, `width`, the thickness its band was drawn at. It becomes the side the element's view shows -- `h` for a view «h», `b` for «b» -- stated on the element, so **the drawing does not move by a pixel**; the other side follows the position from now on. A side the element already states is left alone. Nothing else changed between the two versions, so nothing else is touched, and a file that is not 1.0 is returned as it is.
    """
    if not isinstance(source, dict) or source.get("schema_version") != "1.0":
        return source
    for element in source.get("elements", []) or []:
        if not isinstance(element, dict) or "width" not in element:
            continue
        width = element.pop("width")
        side = element.get("view", "h") if element.get("kind") == "linear" else None
        if side in ELEMENT_SIDES and element.get(side) is None:
            element[side] = width
    source["schema_version"] = SOURCE_SCHEMA_VERSION
    return source


def check_source(source, where):
    """Everything a schema's source must satisfy, checked in one place -- the schema first, then every rule a JSON schema cannot state. Raises on the first breach, naming the collection, the entry and the field. A 1.0 source is upgraded first (`upgrade_source`), which is why the caller's dictionary may come back changed."""
    version = source.get("schema_version")
    if version not in SOURCE_SCHEMA_VERSIONS:
        _fail(where, f"schema_version is {version!r} -- this reads {', '.join(SOURCE_SCHEMA_VERSIONS)}")
    upgrade_source(source)
    try:
        validation.validate_structure(source, "schema-source")
    except validation.ValidationError as exc:
        _fail(where, str(exc))

    if not ID_PATTERN.match(source["id"]):
        _fail(where, f"id {source['id']!r} -- use letters, digits and _ . + - only, starting with a letter or a digit")
    grid = source.get("grid", {})
    if isinstance(grid, dict) and "snap" in grid and grid["snap"] != "auto" and grid["snap"] not in GRID_SNAPS:
        _fail(where, f"grid.snap is {grid['snap']!r} -- 'auto' or one of {', '.join(map(str, GRID_SNAPS))}")
    crop = source.get("crop")
    if crop is not None:
        if not isinstance(crop, dict):
            _fail(where, f"crop is {crop!r} -- expected {{x, z, w, h}} in mm")
        for key in ("x", "z", "w", "h"):
            _number(crop.get(key), where, f"crop.{key}", positive=key in ("w", "h"))
    _check_style(source.get("style"), where, "style")

    # One id for one thing, across the whole schema: `highlight` names an id and must not have to ask which collection it meant.
    seen = {}
    for collection in ENTITIES:
        for i, entry in enumerate(source.get(collection, []), start=1):
            eid = entry.get("id")
            what = f"{collection} {i}"
            if not isinstance(eid, str) or not ENTITY_ID.match(eid):
                _fail(where, f"{what} has id {eid!r} -- a letter, then letters, digits and _")
            if eid.lower() in seen:
                _fail(where, f"{what} is called {eid!r}, which {seen[eid.lower()]} is called too")
            seen[eid.lower()] = what
            # the factors this entry states over the drawing's, and only the ones it is drawn with (figure_style)
            _check_style(entry.get("style"), where, f"{what} ({eid})'s style",
                         figure_style.allowed("schema", collection))

    for element in source["elements"]:
        _check_element(element, where)
    for marker in source["connectors"]:
        _check_connector(marker, where)
    for aid in source["aids"]:
        _check_aid(aid, where)

    aid_ids = {a["id"] for a in source["aids"] if a.get("kind") in AID_POINT_KINDS}
    element_ids = {e["id"] for e in source["elements"] if e.get("kind") == "linear"}
    line_aid_ids = {a["id"] for a in source["aids"] if a.get("kind") in AID_ANGLE_KINDS + AID_TWO_POINT_KINDS}
    for dim in source["dimensions"]:
        what = f"dimension {dim['id']}"
        kind = _one_of(dim.get("kind"), DIMENSION_KINDS, where, f"{what}'s kind")
        # what an angle's end may name: a linear element's axis, or a construction line. A point-shaped aid is in neither, having no direction.
        directions = {"element": element_ids, "aid": line_aid_ids}
        _check_anchor(dim.get("from"), where, f"{what}'s first end", kind, aid_ids, directions)
        _check_anchor(dim.get("to"), where, f"{what}'s second end", kind, aid_ids, directions)
        _number(dim.get("offset", 0.0), where, f"{what}'s offset")
        if "bearing" in dim:
            _number(dim["bearing"], where, f"{what}'s bearing")
            if kind != "angle":
                _fail(where, f"{what} is a {kind!r} and carries a bearing -- only an angle names the sector it is measured in")
        if kind == "angle":
            fa, fk = _anchor_ref(dim.get("from"))
            ta, tk = _anchor_ref(dim.get("to"))
            if (fa, fk) == (ta, tk):
                _fail(where, f"{what} is the angle of {fk} {fa!r} with itself")
            if dimension_corner(source, dim) is None:
                _fail(where, f"{what} is between two directions that do not cross -- an angle needs a corner to turn about")
        else:
            ends = dimension_ends(source, dim)
            if ends is not None and math.dist(ends[0], ends[1]) <= SAME_POINT:
                _fail(where, f"{what} begins and ends in the same place -- there is nothing to measure")
        _string(dim.get("label", ""), where, f"{what}'s label", blank=True)
        if "show" in dim:
            _one_of(dim["show"], LABEL_MODES, where, f"{what}'s show")
        _check_label_offset(dim, where, what)

    # a text placed with the Text tool (issue #43): a place in mm, and figure_text's token text and variables (D-13); only in a 1.2 schema
    if source.get(figure_text.COLLECTION) and source.get("schema_version") != TEXT_SCHEMA_VERSION:
        _fail(where, f"holds a text at schema_version {source.get('schema_version')!r} -- a schema with texts is {TEXT_SCHEMA_VERSION!r}")
    for text in source.get(figure_text.COLLECTION, []):
        what = f"text {text['id']}"
        _number(text.get("x"), where, f"{what}'s x")
        _number(text.get("z"), where, f"{what}'s z")
        figure_text.check(text, lambda message: _fail(where, message), what)


def stamp_version(source, values=None):
    """Before Woodcore's window writes a schema: its texts' last values refreshed where `values` are given (D-14), and the schema_version that says what it holds -- 1.2 with a text, 1.1 without, an emptied list of texts taken off."""
    if values is not None:
        figure_text.refresh_all(source, values)
    if figure_text.COLLECTION in source and not source[figure_text.COLLECTION]:
        del source[figure_text.COLLECTION]
    source["schema_version"] = TEXT_SCHEMA_VERSION if source.get(figure_text.COLLECTION) else SOURCE_SCHEMA_VERSION
    return source


def read_source(path):
    """One schema's source, checked -- and upgraded, a 1.0 file being read as 1.1 (`upgrade_source`). Its id must be its file name: the id is what the report addresses, and a file whose name says another thing would be addressed by neither."""
    path = Path(path)
    try:
        source = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _fail(path.name, f"could not be read -- {exc}")
    if not isinstance(source, dict):
        _fail(path.name, "is not a JSON object")
    check_source(source, path.name)
    if source["id"] != path.stem:
        _fail(path.name, f"id is {source['id']!r} but the file is named {path.name} -- they must agree")
    return source


def new_source(sid):
    """An empty schema, as Woodcore's *Nouveau* starts one -- at the version this module writes."""
    return {
        "schema_version": SOURCE_SCHEMA_VERSION,
        "id": sid,
        "label": "",
        "grid": {"snap": "auto"},
        # the three sliders at rest, written out as the plans' and the static models' own new sources write them: a schema that carries no `style` at all -- every one written before v0.99 -- is read exactly the same way, all three being 1
        "style": {key: 1.0 for key in STYLE_KEYS},
        # no `texts`: a schema is 1.1 until a text is placed in it
        **{collection: [] for collection in ENTITIES if collection != figure_text.COLLECTION},
    }


def readable_sources(source_dir):
    """({id: source}, [(path, error)]): every schema of the folder that reads, and each one that does not with the ValidationError that says why (v0.117, issue #28) -- what a tab offers while another tab may be editing a schema. The export reads the folder with `read_sources`, which stops on the first that does not read; a tab goes on with the others and says which it left out (notices_ui.tell_unreadable_schemas), where it once left it out without a word."""
    sources, problems = {}, []
    for path in source_paths(source_dir):
        try:
            source = read_source(path)
        except validation.ValidationError as exc:
            problems.append((path, exc))
            continue
        sources[source["id"]] = source
    return sources, problems


def read_sources(source_dir):
    """{id: source} of every schema in the folder, checked -- what the two modules that consume a schema are handed (docs/domain/connectors.md §3.3nonies, docs/domain/connections.md §3.3quinquies).

    One read, shared: `export_all.py` reads the folder once and gives the same dictionary to the connectors and to the connections, so a schema is parsed and checked once per export however many calculations are drawn on it, and all of them see exactly the same geometry.
    """
    return {source["id"]: source for source in (read_source(path) for path in source_paths(source_dir))}


def snapshot(source):
    """A copy for the undo history."""
    return copy.deepcopy(source)


# --- The register -------------------------------------------------------------------


def rename(source, collection, old, new):
    """Renames an entry and every reference to it. Raises where the new id is taken or malformed, so a clash refuses rather than merges two things into one."""
    where = f"schema {source.get('id', '?')}"
    if not ENTITY_ID.match(new or ""):
        _fail(where, f"id {new!r} -- a letter, then letters, digits and _")
    if old == new:
        return
    if any(eid.lower() == new.lower() for eid in all_ids(source)):
        _fail(where, f"id {new!r} is taken")
    entry = entry_of(source, collection, old)
    if entry is None:
        _fail(where, f"{collection} has no {old!r}")
    entry["id"] = new
    if collection == "aids":
        for dim in source.get("dimensions", []):
            for end in ("from", "to"):
                anchor = dim.get(end) or {}
                if anchor.get("point") == old:
                    anchor["point"] = new
                if anchor.get("aid") == old:
                    anchor["aid"] = new
    elif collection == "elements":
        for dim in source.get("dimensions", []):
            for end in ("from", "to"):
                anchor = dim.get(end) or {}
                if anchor.get("element") == old:
                    anchor["element"] = new


# --- Geometry (mm, x right and z down) -----------------------------------------------
# Tolerant of a draft: Woodcore calls these on every movement of the mouse, on a schema that is still being drawn.


# --- Dimensions -----------------------------------------------------------------
# statics.py's dimension_* functions, ported to a schema's own anchors (an aid point or a place of its own for the three linear kinds; an element or a line-shaped aid for an angle).


# --- Drawing an area element -------------------------------------------------------
# The tool bar offers three ways to draw a rectangle (plan 3 of je-souhaite-commencer-generic-valley.md's "Surfacique" tool): two diagonal clicks, three clicks (an edge, then a perpendicular width), or one click and a typed length and width. The first is its own shape -- an axis-aligned box -- and the other two are one function apart: a third click and a typed width both end up as the same signed distance off the edge p1-p2, so schema_canvas.py calls rectangle_from_edge() for both and only rectangle_two_corners() is a shape of its own.


# --- An area element with one side fixed by a position (v0.117) ---------------------


# --- Hit-testing and snapping -----------------------------------------------------


# --- Tracking, the way AutoCAD tracks ---------------------------------------------
# statics.py's tracking_rays/nearest_ray/along/typed_point/track, ported: an anchor locks onto the eight polar directions, plus the axis and the normal of every element segment that meets it.


# --- Modification (v0.73) ------------------------------------------------------------
# Move, duplicate, rotate, mirror, split and merge, as pure functions of a source: the canvas
# holds which entries are selected and the tab brackets one call in one undo step, and nothing
# here knows about either. That is statics.py's own arrangement for its tracking (`track`,
# `typed_point`), and it is what lets tests/test_schema_edit.py drive every verb without a window.
#
# A modification acts on the ids it is given and on nothing else. What *follows* rather than being
# acted on is the thing an anchor already buys: a dimension anchored to an aid point moves when
# that aid moves, whether or not the dimension is in the selection (section 3.3decies).


# -- Trancher ------------------------------------------------------------------------


# -- Fusionner -----------------------------------------------------------------------


# --- Warnings ----------------------------------------------------------------------


def _unresolved_reasons(source, positions=None):
    """(element id, reason) for every element whose `position` no longer resolves -- the one fact both warnings() (printed at export) and record["unresolved"] (statics.py's own shape, no 'schema X:' prefix) state, each in its own sentence. `positions` is the position records, or their ids (`position_records`)."""
    known = set(position_records(positions))
    out = []
    for element in source.get("elements", []):
        position = element.get("position")
        if position and position not in known:
            out.append((element["id"], engine.Note("schema_unresolved", f"position {position!r} is not a position of the project", position=position)))
    return out


def unresolved_positions(source, positions=None):
    """Elements whose `position` no longer resolves, as ['<element>: <why>'] -- what record["unresolved"] carries."""
    return [f"{eid}: {reason}" for eid, reason in _unresolved_reasons(source, positions)]


def _section_reasons(source, positions=None):
    """(element id, reason) for every LINEAR element whose band cannot be sized -- the side its view shows is neither stated nor readable off its position -- so it is drawn at ELEMENT_DEFAULT_WIDTH. A position that no longer resolves is said once, by `_unresolved_reasons`, and not again here."""
    records = position_records(positions)
    out = []
    for element in source.get("elements", []):
        if element_kind(element) != "linear":
            continue
        view = element.get("view", "h")
        section = element_section(element, records)
        if section[view] is not None:
            continue
        pid = section["position"]
        if pid and not section["resolved"]:
            continue
        if pid:
            # a steel profile's designation or a dimension that is descriptive text: named as the summaries print it, «ROR 101.6×10», «180 mm»
            reason = engine.Note("schema_section_unread",
                                 f"the dimension {section['section_text'] or '—'!r} of position {pid} does not read as b/h -- "
                                 f"state {view} on the element; it is drawn {fmt_number(ELEMENT_DEFAULT_WIDTH)} mm wide until then",
                                 dimension=section["section_text"] or "—", position=pid, view=view, width=fmt_number(ELEMENT_DEFAULT_WIDTH))
        else:
            reason = engine.Note("schema_section_none",
                                 f"names no position and states no {view} -- choose its position or state its section; "
                                 f"it is drawn {fmt_number(ELEMENT_DEFAULT_WIDTH)} mm wide until then",
                                 view=view, width=fmt_number(ELEMENT_DEFAULT_WIDTH))
        out.append((element["id"], reason))
    return out


def _crop_reasons(source):
    """(entry id, reason) for every element and connector marker lying wholly outside the schema's crop -- the report would not show it. None without a crop."""
    crop = source.get("crop")
    if not isinstance(crop, dict):
        return []
    x0, z0 = float(crop["x"]), float(crop["z"])
    x1, z1 = x0 + float(crop["w"]), z0 + float(crop["h"])
    out = []
    for element in source.get("elements", []):
        box = element_bbox(element)
        if box is not None and (box[2] < x0 or box[0] > x1 or box[3] < z0 or box[1] > z1):
            out.append((element["id"], engine.Note("schema_crop_element", "lies wholly outside the crop -- the report will not show it")))
    for marker in source.get("connectors", []):
        x, z = float(marker["x"]), float(marker["z"])
        if not (x0 <= x <= x1 and z0 <= z <= z1):
            out.append((marker["id"], engine.Note("schema_crop_marker", "lies outside the crop -- the report will not show it")))
    return out


def warnings(source, positions=None, where=None):
    """What is worth saying about a schema without refusing it, printed at export and under Woodcore's drawing -- the v0.33 pattern applied to a fourth editor (docs/decisions.md §13): an element whose `position` no longer resolves, a linear element whose section cannot be known (v0.75), and anything the crop leaves out."""
    sid = source.get("id") or "?"
    where = where or f"schema {sid}"
    # each reason is a Note of its own; the warning carries its code and values, and the schema and entry it is about
    out = [engine.Note(r.code, f"{where}: element {eid} refers to {r}", schema=sid, entry=eid, **r.args) for eid, r in _unresolved_reasons(source, positions)]
    out += [engine.Note(r.code, f"{where}: element {eid} {r}", schema=sid, entry=eid, **r.args) for eid, r in _section_reasons(source, positions)]
    out += [engine.Note(r.code, f"{where}: {eid} {r}", schema=sid, entry=eid, **r.args) for eid, r in _crop_reasons(source)]
    return out


# --- The report record ---------------------------------------------------------------


def build_record(source, positions=None, drawings=None):
    """One schema's entry of data/schemas.json. `positions` are the position records the export has just built, which is where every element's section and label are resolved from."""
    from domains import schema_svg

    sid = source["id"]
    if drawings is None:
        drawings = {lang: schema_svg.layout(source, lang, positions=positions) for lang in strings.LANGUAGES}
    meta = schema_svg.meta(drawings[strings.SOURCE_LANGUAGE])
    record = {
        "label": source.get("label", ""),
        "source": f"details/{sid}.json",
        # what the figure was drawn with: the drawing's own three factors, as the plans' and the static models' records already carry theirs, and each entry's own beside its placed geometry where it states any (schema_svg.meta)
        "style": meta["style"],
        "figures": {
            lang: {"file": f"schemas/{sid}-{lang}.svg", "view": schema_svg.meta(drawings[lang])["view"]}
            for lang in strings.LANGUAGES
        },
        "elements": meta["elements"],
        "connectors": meta["connectors"],
        "aids": meta["aids"],
        "dimensions": meta["dimensions"],
        "labels": all_ids(source),
        "unresolved": unresolved_positions(source, positions),
        # the extent its symbols are sized by (font = size/40, a marker's radius size/130): the report's halo reads it (D7)
        "size": drawings[strings.SOURCE_LANGUAGE]["size"],
    }
    return record


def text_records(source, values, where, notes):
    """The texts of a schema as its record carries them: [{id, text, lines, links?}] -- what each printed and where its variables came from (REQ-012). Their warnings are added to `notes`."""
    out = []
    for text in source.get(figure_text.COLLECTION, []):
        printed, provenance, found = figure_text.resolve(text, values, f"{where}, text {text['id']}")
        notes += found
        record = {"id": text["id"], "text": text.get("text", ""), "lines": printed}
        if provenance:
            record["links"] = provenance
        out.append(record)
    return out


# --- Export --------------------------------------------------------------------------


def prepare(source_dir, positions=None, values=None, place=None):
    """Every schema, checked and built: (data, files, warnings), `files` keyed by the figure's name in the JSON that `place` (an engine.Figures) gives. Nothing is written here, so an export that fails leaves data/ as it was. `positions` are the position records ({id: record}) every element's section and label are resolved against -- afresh at every export, so «Import données» is all it takes for a section changed in the workbook to reach the drawing; a list of ids is accepted and resolves no section."""
    from domains import schema_svg

    values = values or {}
    place = place or engine.Figures(None, "details")
    schemas, files, notes = {}, {}, []
    for path in source_paths(source_dir):
        source = read_source(path)
        drawings = {lang: schema_svg.layout(source, lang, positions=positions, values=values) for lang in strings.LANGUAGES}
        notes += warnings(source, positions, where=f"schema {source['id']}")
        schemas[source["id"]] = build_record(source, positions, drawings)
        texts = text_records(source, values, f"schema {source['id']}", notes)
        if texts:
            schemas[source["id"]]["texts"] = texts
        for lang, drawing in drawings.items():
            name = place.name(f"{source['id']}-{lang}.svg")
            schemas[source["id"]]["figures"][lang]["file"] = name
            files[name] = schema_svg.render(drawing)
    data = {"schema_version": SIZE_EXPORT_VERSION, "schemas": schemas}
    validation.validate_structure(data, "schemas")
    validation.validate_schemas_business(data)
    return data, files, notes


def write(data, files, data_dir):
    """The only writer: data/schemas.json and the schemas' figures -- into the tab's Exports/Figures/ in a project laid out by folders, data/schemas/ otherwise (engine.Figures) --, those of schemas that no longer exist removed: only what the last export wrote, never a file of the engineer's."""
    data_dir = Path(data_dir)
    engine.figures(data_dir, "details").write(files, engine.previous_json(data_dir / "schemas.json"))
    engine.write_json(data_dir / "schemas.json", data)


def export(source_dir, data_dir, positions=None, values=None):
    """prepare + write, and the warnings -- what Woodcore's window runs when a schema is saved. `values` are the export's, which a text's variables print (issue #43)."""
    data, files, notes = prepare(source_dir, positions, values, place=engine.figures(data_dir, "details"))
    write(data, files, data_dir)
    return notes


def references(record):
    """What an exported schema names, [(kind, id, field)]: the position of each element (domains/dependency_graph.py, spec 2026-10-21-graphe-dependances, ARCH-RISK-1103)."""
    return [("position", element["position"], "elements[%s].position" % element.get("id", i))
            for i, element in enumerate(record.get("elements") or ()) if element.get("position")]
