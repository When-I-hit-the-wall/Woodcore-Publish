"""Static models (statische Systeme), drawn in Woodcore and exported as a figure for the report (docs/domain/static-models.md §3.3octies).

A static model is the sketch an engineer draws before a calculation: the members, where they are held, where they are hinged, and what acts on them. This module owns its source file, `statics/<id>.json`, which Woodcore writes and nothing else does -- the arrangement the connections and the position plans already have, for the same reasons (docs/decisions.md §13).

**It draws a system; it does not solve one.** There are no reactions here, no N/V/M, no stability check and no cable-slack check. What the module computes is geometry, and the one piece of arithmetic it does is a load's magnitude times its influence width.

The frame is the connection module's, and for the same reason (section 3.3quinquies): metres, **x to the right and z down**, angles in degrees from +x turning towards +z -- clockwise as the figure is read, so a load at 90 degrees points down. The drawing needs no flip: what the engineer types is what the figure draws.

There is no Qt in this file, so Woodcore's canvas and a test script call the same functions -- which is what lets the AutoCAD-style tracking below be verified without a window.
"""

import copy
import json
import math
import re
from pathlib import Path

import engine
import validation
from domains._common import check_number as _number, fail as _fail  # one copy of the domains' helpers (spec 2026-10-19-base-saine-nettoyage, G4)
from domains import dimension  # a dimension's geometry, shared with the schemas and the plans (issue #9)
from domains import figure_style
from domains import figure_text  # a text placed with the Text tool, the four engines' one (issue #43, ARCH-003)
from domains import links  # a magnitude naming a variable reads it the way every linked field does (spec 2026-10-11-variables-liees-champs-et-textes, ARCH-001)
from i18n import strings
from domains.statics_geometry import (  # split out of this module (issue #30): every name it had is still importable from it
    ALONG_PATTERN,
    ANGLE_DIGITS,
    DIGITS,
    DIMENSION_UNITS,
    LABEL_MODES,
    PARALLEL_TOLERANCE,
    SAME_POINT,
    SNAP_KINDS,
    TRACK_ANGLES,
    TRACK_TOLERANCE_DEG,
    _axis,
    _cross,
    _member_ray,
    _midpoint,
    _point_segment,
    _segments,
    along,
    angle_rays,
    bbox,
    constrain,
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
    entry_of,
    extension_lines,
    figure_number,
    fmt_number,
    grid_snap,
    hit_label,
    hit_load,
    hit_member,
    hit_point,
    index_of,
    line_load_span,
    load_at,
    load_direction,
    member_angle,
    member_direction,
    member_length,
    member_points,
    nearest_ray,
    normalize_angle,
    parse_along,
    point_at,
    snap,
    snap_targets,
    track,
    tracking_rays,
    typed_point,
)
from domains._common import source_paths  # one copy (G4)
from domains import svg_draw

# Of a source file (statics/<id>.json) and of the export (data/statics.json).
SOURCE_SCHEMA_VERSION = "1.1"
# 1.2 is 1.1 with `links` on a point, a member, a release, a load or the model, and `last` on a magnitude naming a variable (spec 2026-10-11-variables-liees-champs-et-textes, D-17), and `texts`, the Text tool's (issue #43): written only by a source that carries one, so a model that follows no variable is saved and exported as before
LINKED_SCHEMA_VERSION = "1.2"
# A 1.0 source carries no dimensions and is read exactly as it is -- the rule a plan's label_offset set in v0.42.
SOURCE_SCHEMA_VERSIONS = ("1.0", SOURCE_SCHEMA_VERSION, LINKED_SCHEMA_VERSION)
EXPORT_SCHEMA_VERSION = "1.1"
# 1.2 is 1.1 with a model's `links`, where its linked fields came from (REQ-012), and its `texts`, what each printed: written only where one follows a variable or carries a text
LINKED_EXPORT_VERSION = "1.2"
# 1.3 is 1.2 with its figures named from the Typst root (`/Statics/Exports/Figures/M01-fr.svg`): written by a project laid out by folders, where they lie in the tab's Exports/Figures/ (issue #64, D-10)
ROOTED_EXPORT_VERSION = "1.3"

# A model's id is the file name of its source and the string the report addresses it by -- the rule the plans and the connections follow, for the same reason.
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$")

# The id of a point, a member, a support, a release or a load. Kept narrower than a model's, since it is typed into a table cell and read back in a list of choices.
ENTITY_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")

# The eight collections a model holds, in the order they are checked, listed and drawn. `texts`, the Text tool's (issue #43), is figure_text's: a model that has one is a 1.2 source.
ENTITIES = ("points", "members", "supports", "releases", "point_loads", "line_loads", "dimensions", figure_text.COLLECTION)

# What a new entry of each collection is called: P1, B1, A1 (Auflager), G1 (Gelenk), F1, q1, D1.
ENTITY_PREFIX = {
    "points": "P",
    "members": "B",
    "supports": "A",
    "releases": "G",
    "point_loads": "F",
    "line_loads": "q",
    "dimensions": "D",
    figure_text.COLLECTION: figure_text.PREFIX,
}

# A member is a bar (takes anything), a cable (a positive normal force only) or a spring (a translational spring along its own axis). Each is drawn its own way, and a cable and a spring may say how stiff they are.
MEMBER_KINDS = ("bar", "cable", "spring")

# The unit a member's own stiffness is given in -- a spring's, along its axis.
MEMBER_STIFFNESS_UNIT = "kN/m"

# Einspannung, Festlager, Loslager.
SUPPORT_TYPES = ("fixed", "pinned", "roller")

# A Festlager and a Loslager are hinges, and their pin is drawn as the circle a moment release is drawn as. Where that pin sits is the engineer's to say, because the model cannot tell: `shared` -- the default -- is the pin the bar itself turns about, drawn on the node; `through` is a bar running over the support, its pin set back along the support's own axis until the circle just touches the bar, with the support hanging under it. An Einspannung has no pin, so it takes neither.
SUPPORT_HINGES = ("shared", "through")
HINGED_SUPPORTS = ("pinned", "roller")

# A release is a degree of freedom set free at one end of a member: free in moment (a hinge), in shear or in normal force. A `stiffness` on a moment release makes it a rotational spring. A translational spring is not a release at all -- it is a member of its own kind (MEMBER_KINDS), which is where the engineer looks for it.
RELEASE_DOFS = ("moment", "shear", "normal")
RELEASE_ENDS = ("start", "end")

# The unit a rotational spring's stiffness is given in. Only a moment release may be a spring.
SPRING_UNITS = {"moment": "kNm/rad"}

# Which way a load acts: straight down, straight along +x, at an angle from +x, or at an angle from a member's axis -- the reference line of the engineer's request. A point load in `member` mode names the member it is measured from; a line load is measured from the member it runs on.
LOAD_DIRECTIONS = ("vertical", "horizontal", "angle", "member")

# A uniform line load, or one that varies linearly along the member. Triangular is `linear` with one end zero and trapezoidal is `linear` with two ends, so the drawing, the check and the record each keep one code path where Woodcore offers three buttons.
LINE_LOAD_SHAPES = ("uniform", "linear")


# The colours a load may be drawn in -- its arrows, its band and its cap -- by the name the source stores, each the ink the figure draws it with. Red is the one every load was drawn in until the engineer could choose, and a load stating no `color` is still drawn in it, so a model saved before the choice existed draws exactly as it did. Five inks dark enough to read on white paper, and apart enough to tell two load cases from each other on one figure. Held here, beside the names the source check allows, so that the names and the inks cannot drift apart; statics_svg reads the inks from here.
LOAD_COLOURS = {
    "red": svg_draw.colour("red"),
    "green": svg_draw.colour("green"),
    "orange": svg_draw.colour("orange"),
    "blue": svg_draw.colour("blue"),
    "violet": svg_draw.colour("violet"),
}
DEFAULT_LOAD_COLOUR = "red"

# What a dimension measures. The three linear ones run between two anchors -- a point of the model, or a place of its own -- and differ only in the direction their dimension line takes: `horizontal` gives the distance along x, `vertical` the distance along z, `parallel` the true distance between them. `angle` is the odd one and says so in its ends: it names two members and measures the angle between their axes, in degrees.
DIMENSION_KINDS = dimension.KINDS
DIMENSION_LINEAR = dimension.LINEAR


# The grid steps in metres the editor snaps to, coarsest first, each with the interval its heavier lines are drawn at. "auto" takes the finest step still far enough apart on screen.
GRID_STEPS = ((5.0, 10.0), (1.0, 5.0), (0.5, 5.0), (0.1, 1.0))
GRID_SNAPS = tuple(step for step, _heavy in GRID_STEPS)

# What the style sliders may do to the symbols: from a quarter to three times their size. Read from `figure_style` since v0.99 rather than restated here -- the plans, the static models and the detail schemas share one range and one set of names, so a slider means the same thing in every tab. The two names stay, `statics_tab` and the tests reading them by these.
STYLE_KEYS = figure_style.KEYS
STYLE_RANGE = figure_style.RANGE

# The word `figure_style.ENTRY_KEYS` files this module's collections under, so that `figure_style.allowed(STYLE_KIND, collection)` says which of the three one entry of that collection may state over the drawing's.
STYLE_KIND = "statics"


# A load's magnitude may name a var of data/calculations.json instead of stating a number: the figure then follows the workbook by itself, and the source records where the number came from (docs/architecture/principles.md §2 rules 1 and 5). A referenced magnitude may also carry a `factor` and an `offset` -- 0.8 x SL, SL + 10 -- and a `description` for the figure's notes. A load may carry **no** magnitude at all: a value is only ever shown and scaled by, never calculated with, so a system may be drawn before its actions are known.
MAGNITUDE_LITERAL_KEYS = {"value", "unit"}
MAGNITUDE_REFERENCE_KEYS = {"domain", "instance", "var"}
MAGNITUDE_REFERENCE_EXTRAS = {"factor", "offset", "description", "last", "origin"}

# An influence width multiplies a load per square metre into one per metre, or one per metre into a force: the actions are calculated in kN/m2 and the systems carry kN/m. Anything else has no width to be multiplied by.
PER_AREA_SUFFIXES = ("/m²", "/m2", "/m^2")
PER_LENGTH_SUFFIX = "/m"

# The unit an influence width itself is given in. It is a width, so it is metres, and saying so is what lets the export refuse a stray "cm".
WIDTH_UNIT = "m"

# What b_e is called on the figure when the engineer names it nothing else.
DEFAULT_WIDTH_LABEL = "b_e"

# The fields of a model a variable of the export may fill besides a load's magnitude (REQ-009, D-05), by collection -- "model" for the model's own -- with the unit each is written in: the geometry and the springs. A load's magnitude names its variable in its own reference form (`domain`, `instance`, `var`), which it had before any other field could follow one.
LINKABLE = {
    "model": {"width": WIDTH_UNIT},
    "points": {"x": "m", "z": "m"},
    "members": {"stiffness": MEMBER_STIFFNESS_UNIT},
    "releases": {"stiffness": SPRING_UNITS["moment"]},
    "point_loads": {"width": WIDTH_UNIT},
    "line_loads": {"width": WIDTH_UNIT},
}


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


def _clean(value):
    """A number as it is saved: six decimals at most, -0 as 0, a whole float as an int."""
    value = round(float(value), 6) + 0.0
    return int(value) if value.is_integer() else value


def load_colour(load):
    """The name of the colour a load is drawn in: the one it states, else red, the colour every load was drawn in before the engineer could choose."""
    colour = load.get("color")
    return colour if colour in LOAD_COLOURS else DEFAULT_LOAD_COLOUR


def magnitude_kind(magnitude):
    """`literal` for a magnitude stating a number, `reference` for one naming a var of the export, `none` for a load that states none at all, None for anything else."""
    if magnitude is None:
        return "none"
    if not isinstance(magnitude, dict):
        return None
    keys = set(magnitude)
    if keys == MAGNITUDE_LITERAL_KEYS:
        return "literal"
    if MAGNITUDE_REFERENCE_KEYS <= keys <= MAGNITUDE_REFERENCE_KEYS | MAGNITUDE_REFERENCE_EXTRAS:
        return "reference"
    return None


def width_unit(unit):
    """The unit a load takes once multiplied by an influence width in metres: kN/m2 -> kN/m, kN/m -> kN. None where the unit is neither, which is what makes a width on a moment refusable."""
    if not isinstance(unit, str):
        return None
    text = unit.strip()
    for suffix in PER_AREA_SUFFIXES:
        if text.endswith(suffix):
            return (text[: -len(suffix)] + PER_LENGTH_SUFFIX).strip()
    if text.endswith(PER_LENGTH_SUFFIX):
        return text[: -len(PER_LENGTH_SUFFIX)].strip()
    return None


# --- The source file ------------------------------------------------------------


def _check_style(source, where):
    """The drawing's own three factors -- all three of which every drawing is set with, so none of them is refused here."""
    figure_style.check(source.get("style"), lambda message: _fail(where, message))


def _check_entry_style(entry, where, what, collection):
    """One entry's own factors: a **factor multiplying the drawing's** and never a size, and only the ones that entry is drawn with (`figure_style.ENTRY_KEYS`).

    A factor an entry does not draw is refused naming the ones it may state: a bar draws no symbol on a node, so a `point` on one would be a field nobody could see the effect of -- the argument that took `plates.thickness` out of a connector's source in v0.70. The message names the entry as every other refusal of this module does, `_fail` being handed to `figure_style.check` rather than the check knowing where the entry came from.
    """
    figure_style.check(entry.get("style"), lambda message: _fail(where, message),
                       figure_style.allowed(STYLE_KIND, collection), f"{what}'s style")


def _check_label_offset(entry, where, what):
    if "label_offset" in entry:
        _point(entry["label_offset"], where, f"{what}'s label_offset")


def _check_magnitude(magnitude, where, what, optional=False):
    kind = magnitude_kind(magnitude)
    if kind == "none" and not optional:
        _fail(where, f"{what} must be given")
    if kind is None:
        _fail(
            where,
            f"{what} must be either a value and its unit ({{\"value\", \"unit\"}}) or a variable of the export "
            f"({{\"domain\", \"instance\", \"var\"}}, with an optional factor, offset and description), "
            f"got {sorted(magnitude) if isinstance(magnitude, dict) else magnitude!r}",
        )
    if kind == "literal":
        _number(magnitude["value"], where, f"{what}'s value")
        _string(magnitude["unit"], where, f"{what}'s unit")
    elif kind == "reference":
        for key in ("domain", "instance", "var"):
            _string(magnitude[key], where, f"{what}'s {key}")
        if "factor" in magnitude:
            _number(magnitude["factor"], where, f"{what}'s factor")
        if "offset" in magnitude:
            _number(magnitude["offset"], where, f"{what}'s offset")
        if "description" in magnitude:
            _string(magnitude["description"], where, f"{what}'s description", blank=True)
        if "origin" in magnitude and magnitude["origin"] != links.FORMULAS:
            _fail(where, f"{what}'s origin is {magnitude['origin']!r} -- {links.FORMULAS!r} for a domain of the «Formule» tab, or absent for the export")
        if "last" in magnitude:
            last = magnitude["last"]
            if not isinstance(last, dict) or set(last) != MAGNITUDE_LITERAL_KEYS:
                _fail(where, f"{what}'s last must be the value it last had and its unit ({{\"value\", \"unit\"}}), got {last!r}")
            _number(last["value"], where, f"{what}'s last value")
            _string(last["unit"], where, f"{what}'s last unit", blank=True)
    return kind


def _check_width(load, where, what):
    """An influence width, where the thing carries one: b_e in metres, with the name and the description the figure prints. A model carries one for the whole of it and a load may carry one of its own, which overrides it; both are checked here."""
    width = load.get("width")
    if width is None:
        return
    if not isinstance(width, dict):
        _fail(where, f"{what}'s width must be an object, got {width!r}")
    _number(width.get("value"), where, f"{what}'s width", positive=True)
    unit = width.get("unit", WIDTH_UNIT)
    if unit != WIDTH_UNIT:
        _fail(where, f"{what}'s width is in {unit!r} -- an influence width is given in {WIDTH_UNIT}")
    _string(width.get("label", DEFAULT_WIDTH_LABEL), where, f"{what}'s width label")
    _string(width.get("description", ""), where, f"{what}'s width description", blank=True)
    if not isinstance(width.get("show", True), bool):
        _fail(where, f"{what}'s width show must be true or false, got {width.get('show')!r}")
    # A width only makes sense on a magnitude it can divide a metre out of. A literal says its unit here; a reference says it at the export, where it is warned about rather than refused, since the var may simply be gone (docs/domain/static-models.md §3.3octies). A model's own width is checked against nothing here: which loads it applies to is only known once they are read.
    magnitude = load.get("magnitude")
    if magnitude_kind(magnitude) == "literal" and width_unit(magnitude["unit"]) is None:
        _fail(
            where,
            f"{what} is in {magnitude['unit']!r}, which an influence width cannot multiply -- "
            f"a width multiplies a load per metre or per square metre",
        )


def _check_direction(load, where, what, member_ids, reference_needed):
    direction = _one_of(load.get("direction"), LOAD_DIRECTIONS, where, f"{what}'s direction")
    if direction in ("angle", "member"):
        if "angle" not in load:
            _fail(where, f"{what} acts at an angle but gives none")
        _number(load["angle"], where, f"{what}'s angle")
    elif "angle" in load:
        _fail(where, f"{what} is {direction} and carries an angle -- an angle belongs to 'angle' and 'member' only")
    if direction == "member" and reference_needed:
        reference = load.get("reference") or ""
        if not reference.strip():
            _fail(where, f"{what} acts at an angle from a member but names none -- give it the member its angle is measured from")
        if reference not in member_ids:
            _fail(where, f"{what} is measured from member {reference!r}, which the model does not have")
    elif not reference_needed and "reference" in load and load["reference"]:
        # a line load is measured from the member it runs on; a point load's reference member is checked where it is read, being what it is drawn along as well
        _fail(where, f"{what} names a reference member but runs on one already")
    return direction


def check_source(source, where):
    """Everything a model's source must satisfy, checked in one place -- the schema first, then every rule a schema cannot state. Raises on the first breach, naming the collection, the entry and the field."""
    version = source.get("schema_version")
    if version not in SOURCE_SCHEMA_VERSIONS:
        _fail(where, f"schema_version is {version!r} -- this reads {', '.join(SOURCE_SCHEMA_VERSIONS)}")
    try:
        validation.validate_structure(source, "statics-source")
    except validation.ValidationError as exc:
        _fail(where, str(exc))

    if not ID_PATTERN.match(source["id"]):
        _fail(where, f"id {source['id']!r} -- use letters, digits and _ . + - only, starting with a letter or a digit")
    _check_style(source, where)
    # one influence width for the whole model, which a load may override with one of its own
    _check_width(source, where, "the model")
    grid = source.get("grid", {})
    if isinstance(grid, dict) and "snap" in grid and grid["snap"] != "auto" and grid["snap"] not in GRID_SNAPS:
        _fail(where, f"grid.snap is {grid['snap']!r} -- 'auto' or one of {', '.join(map(str, GRID_SNAPS))}")

    # One id for one thing, across the whole model: the report's `highlight` names an id and must not have to ask which collection it meant.
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

    # the fields that follow a variable of the export (D-17): only where the model is at 1.2, and only the fields LINKABLE names
    if is_linked(source) and version != LINKED_SCHEMA_VERSION:
        _fail(where, f"follows a variable at schema_version {version!r} -- a model with links, a last value or a «Formule» variable is {LINKED_SCHEMA_VERSION!r}")
    links.check_all(source, {links.SELF: LINKABLE["model"], **{c: LINKABLE.get(c, {}) for c in ENTITIES}}, lambda message: _fail(where, message), "the model")

    point_ids = {p["id"] for p in source["points"]}
    member_ids = {m["id"] for m in source["members"]}

    for point in source["points"]:
        what = f"point {point['id']}"
        _number(point.get("x"), where, f"{what}'s x")
        _number(point.get("z"), where, f"{what}'s z")
        _string(point.get("label", ""), where, f"{what}'s label", blank=True)
        _check_label_offset(point, where, what)
        _check_entry_style(point, where, what, "points")

    for member in source["members"]:
        what = f"member {member['id']}"
        kind = _one_of(member.get("kind"), MEMBER_KINDS, where, f"{what}'s kind")
        stiffness = member.get("stiffness")
        if stiffness is not None:
            if kind != "spring":
                _fail(where, f"{what} is a {kind} and carries a stiffness -- only a spring has one")
            if not isinstance(stiffness, dict):
                _fail(where, f"{what}'s stiffness must be an object, got {stiffness!r}")
            _number(stiffness.get("value"), where, f"{what}'s stiffness", positive=True)
            unit = _string(stiffness.get("unit", ""), where, f"{what}'s stiffness unit")
            if unit != MEMBER_STIFFNESS_UNIT:
                _fail(where, f"{what} is a spring in {unit!r} -- expected {MEMBER_STIFFNESS_UNIT}")
        for end in ("p1", "p2"):
            if member.get(end) not in point_ids:
                _fail(where, f"{what}'s {end} is {member.get(end)!r}, which the model has no point of")
        if member["p1"] == member["p2"]:
            _fail(where, f"{what} runs from {member['p1']} to itself")
        a = point_at(source, member["p1"])
        b = point_at(source, member["p2"])
        if math.dist(a, b) <= SAME_POINT:
            _fail(where, f"{what} is {math.dist(a, b):g} m long -- its two points are one point")
        _string(member.get("label", ""), where, f"{what}'s label", blank=True)
        _check_label_offset(member, where, what)
        _check_entry_style(member, where, what, "members")

    held = {}
    for support in source["supports"]:
        what = f"support {support['id']}"
        if support.get("point") not in point_ids:
            _fail(where, f"{what} is at {support.get('point')!r}, which the model has no point of")
        if support["point"] in held:
            _fail(where, f"{what} and {held[support['point']]} are both at point {support['point']}")
        held[support["point"]] = what
        _one_of(support.get("type"), SUPPORT_TYPES, where, f"{what}'s type")
        if "hinge" in support:
            # an Einspannung has no pin to place, so a hinge on one is a mistake said out loud rather than a field quietly ignored
            if support.get("type") not in HINGED_SUPPORTS:
                _fail(where, f"{what} is a {support.get('type')!r} support and has no hinge to place -- "
                             f"only a {' or a '.join(HINGED_SUPPORTS)} takes one")
            _one_of(support["hinge"], SUPPORT_HINGES, where, f"{what}'s hinge")
        if "angle" in support:
            _number(support["angle"], where, f"{what}'s angle")
        _string(support.get("label", ""), where, f"{what}'s label", blank=True)
        _check_label_offset(support, where, what)
        _check_entry_style(support, where, what, "supports")

    freed = {}
    for release in source["releases"]:
        what = f"release {release['id']}"
        if release.get("member") not in member_ids:
            _fail(where, f"{what} is on member {release.get('member')!r}, which the model does not have")
        _one_of(release.get("end"), RELEASE_ENDS, where, f"{what}'s end")
        dof = _one_of(release.get("dof"), RELEASE_DOFS, where, f"{what}'s dof")
        key = (release["member"], release["end"], dof)
        if key in freed:
            _fail(where, f"{what} and {freed[key]} both free the {dof} at the {release['end']} of {release['member']}")
        freed[key] = what
        stiffness = release.get("stiffness")
        if stiffness is not None:
            if dof not in SPRING_UNITS:
                _fail(where, f"{what} frees the {dof} and carries a stiffness -- a spring along a member is a member of kind 'spring', not a release")
            if not isinstance(stiffness, dict):
                _fail(where, f"{what}'s stiffness must be an object, got {stiffness!r}")
            _number(stiffness.get("value"), where, f"{what}'s stiffness", positive=True)
            unit = _string(stiffness.get("unit", ""), where, f"{what}'s stiffness unit")
            if unit != SPRING_UNITS[dof]:
                _fail(where, f"{what} is a {dof} spring in {unit!r} -- expected {SPRING_UNITS[dof]}")
        _string(release.get("label", ""), where, f"{what}'s label", blank=True)
        _check_label_offset(release, where, what)
        _check_entry_style(release, where, what, "releases")

    for load in source["point_loads"]:
        what = f"point load {load['id']}"
        if load.get("point") not in point_ids:
            _fail(where, f"{what} is at {load.get('point')!r}, which the model has no point of")
        reference = load.get("reference") or ""
        if reference and reference not in member_ids:
            _fail(where, f"{what} refers to member {reference!r}, which the model does not have")
        if load.get("along") not in (None, ""):
            if parse_along(load["along"]) is None:
                _fail(where, f"{what}'s along is {load['along']!r} -- a length in metres, or a fraction of the member such as 0.5l")
            if not reference:
                _fail(where, f"{what} is drawn along a member but names none -- give it a reference member")
        _check_direction(load, where, what, member_ids, reference_needed=True)
        _check_magnitude(load.get("magnitude"), where, f"{what}'s magnitude", optional=True)
        _check_width(load, where, what)
        _string(load.get("label", ""), where, f"{what}'s label", blank=True)
        _one_of(load.get("show", "name+value"), LABEL_MODES, where, f"{what}'s show")
        _one_of(load.get("color", DEFAULT_LOAD_COLOUR), tuple(LOAD_COLOURS), where, f"{what}'s color")
        _check_label_offset(load, where, what)
        _check_entry_style(load, where, what, "point_loads")

    for load in source["line_loads"]:
        what = f"line load {load['id']}"
        if load.get("member") not in member_ids:
            _fail(where, f"{what} is on member {load.get('member')!r}, which the model does not have")
        start = _number(load.get("from", 0.0), where, f"{what}'s from")
        end = _number(load.get("to", 1.0), where, f"{what}'s to")
        if not 0.0 <= start < end <= 1.0:
            _fail(where, f"{what} runs from {start} to {end} -- 0 <= from < to <= 1 along the member")
        shape = _one_of(load.get("shape"), LINE_LOAD_SHAPES, where, f"{what}'s shape")
        _check_magnitude(load.get("magnitude"), where, f"{what}'s magnitude", optional=True)
        if shape == "linear":
            _check_magnitude(load.get("magnitude_end"), where, f"{what}'s magnitude_end", optional=True)
        elif load.get("magnitude_end") is not None:
            _fail(where, f"{what} is uniform and carries a second value -- a second value belongs to a linear load")
        _check_direction(load, where, what, member_ids, reference_needed=False)
        _check_width(load, where, what)
        _string(load.get("label", ""), where, f"{what}'s label", blank=True)
        _one_of(load.get("show", "name+value"), LABEL_MODES, where, f"{what}'s show")
        _one_of(load.get("color", DEFAULT_LOAD_COLOUR), tuple(LOAD_COLOURS), where, f"{what}'s color")
        _check_label_offset(load, where, what)
        _check_entry_style(load, where, what, "line_loads")

    for dim in source.get("dimensions", []):
        what = f"dimension {dim['id']}"
        kind = _one_of(dim.get("kind"), DIMENSION_KINDS, where, f"{what}'s kind")
        _check_anchor(dim.get("from"), where, f"{what}'s first end", kind, point_ids, member_ids)
        _check_anchor(dim.get("to"), where, f"{what}'s second end", kind, point_ids, member_ids)
        _number(dim.get("offset", 0.0), where, f"{what}'s offset")
        if "bearing" in dim:
            _number(dim["bearing"], where, f"{what}'s bearing")
            if kind != "angle":
                _fail(where, f"{what} is a {kind!r} and carries a bearing -- only an angle names the sector it is measured in")
        if kind == "angle":
            if (dim["from"] or {}).get("member") == (dim["to"] or {}).get("member"):
                _fail(where, f"{what} is the angle of member {(dim['from'] or {}).get('member')!r} with itself")
            if dimension_corner(source, dim) is None:
                _fail(where, f"{what} is between two members that do not cross -- an angle needs a corner to turn about")
        else:
            ends = dimension_ends(source, dim)
            if ends is not None and math.dist(ends[0], ends[1]) <= SAME_POINT:
                _fail(where, f"{what} begins and ends in the same place -- there is nothing to measure")
        _string(dim.get("label", ""), where, f"{what}'s label", blank=True)
        if "show" in dim:
            _one_of(dim["show"], LABEL_MODES, where, f"{what}'s show")
        _check_label_offset(dim, where, what)
        _check_entry_style(dim, where, what, "dimensions")

    # a text placed with the Text tool (issue #43): a place in the model's frame, and figure_text's token text and variables (D-13)
    for text in source.get(figure_text.COLLECTION, []):
        what = f"text {text['id']}"
        _number(text.get("x"), where, f"{what}'s x")
        _number(text.get("z"), where, f"{what}'s z")
        figure_text.check(text, lambda message: _fail(where, message), what)
        _check_label_offset(text, where, what)
        _check_entry_style(text, where, what, figure_text.COLLECTION)


def _check_anchor(anchor, where, what, kind, point_ids, member_ids):
    """One end of a dimension: a member for an angle, and for the three linear kinds a point of the model or a place of its own."""
    if not isinstance(anchor, dict):
        _fail(where, f"{what} is {anchor!r} -- a point, a member or a place of its own")
    if kind == "angle":
        mid = anchor.get("member")
        if mid not in member_ids:
            _fail(where, f"{what} is member {mid!r}, which the model does not have")
        return
    if anchor.get("member"):
        _fail(where, f"{what} names member {anchor['member']!r} -- only an angle is measured between members")
    if "point" in anchor:
        if anchor["point"] not in point_ids:
            _fail(where, f"{what} is at {anchor['point']!r}, which the model has no point of")
        return
    if "x" not in anchor or "z" not in anchor:
        _fail(where, f"{what} names no point and gives no place of its own -- it needs one or the other")
    _number(anchor.get("x"), where, f"{what}'s x")
    _number(anchor.get("z"), where, f"{what}'s z")


def drop_release_stiffness(source, where):
    """Takes the stiffness off a release that frees a shear or a normal force, and returns the sentences saying so.

    A translational spring is a member of kind `spring`, not a release (docs/decisions.md §13, v0.51), and the decision was that such a release «keeps its degree of freedom and loses the stiffness». `check_source` refused it instead, so one file of that form stopped every model's export (periodic audit 260916, AUD-7-424). Read here, before the check, both by the export and by Woodcore's tab -- turning it into a member would change the structure, which is the engineer's to do.
    """
    notes = []
    if not isinstance(source, dict) or not isinstance(source.get("releases"), list):
        return notes
    for release in source["releases"]:
        if not isinstance(release, dict) or release.get("stiffness") is None:
            continue
        if release.get("dof") in RELEASE_DOFS and release.get("dof") not in SPRING_UNITS:
            del release["stiffness"]
            notes.append(engine.Note("statics_release_stiffness_" + release["dof"],
                                     f"{where}: release {release.get('id')} frees the {release['dof']} and carried a stiffness, which is dropped -- "
                                     f"a spring along a member is a member of kind 'spring'",
                                     model=source.get("id") or "?", release=release.get("id")))
    return notes


def read_source(path, notes=None):
    """One model's source, checked. Its id must be its file name: the id is what the report addresses, and a file whose name says another thing would be addressed by neither. What is dropped on the way (`drop_release_stiffness`) is said in `notes`, where a list is given."""
    path = Path(path)
    try:
        source = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _fail(path.name, f"could not be read -- {exc}")
    if not isinstance(source, dict):
        _fail(path.name, "is not a JSON object")
    dropped = drop_release_stiffness(source, f"model {source.get('id', path.stem)}")
    if notes is not None:
        notes.extend(dropped)
    check_source(source, path.name)
    if source["id"] != path.stem:
        _fail(path.name, f"id is {source['id']!r} but the file is named {path.name} -- they must agree")
    return source


def new_source(sid):
    """An empty model, as Woodcore's *Nouveau* starts one."""
    return {
        "schema_version": SOURCE_SCHEMA_VERSION,
        "id": sid,
        "label": "",
        "style": {key: 1.0 for key in STYLE_KEYS},
        "grid": {"snap": "auto"},
        # no `texts`: a model is 1.1 until a text is placed in it, and a list a 1.1 model never had would be one more key in every new file
        **{collection: [] for collection in ENTITIES if collection != figure_text.COLLECTION},
    }


def snapshot(source):
    """A copy for the undo history."""
    return copy.deepcopy(source)


# --- The register ---------------------------------------------------------------


def find_entry(source, eid):
    """The (collection, entry) an id names, whatever collection it is in -- ids are unique across a model."""
    for collection in ENTITIES:
        entry = entry_of(source, collection, eid)
        if entry is not None:
            return collection, entry
    return None, None


def all_ids(source):
    """Every id the model carries, in collection order."""
    return [entry["id"] for collection in ENTITIES for entry in source.get(collection, [])]


def next_id(source, collection):
    """The first free `<prefix><n>` of that collection -- P3, B7, q2 -- ignoring case, as the file system and the id check do."""
    taken = {eid.lower() for eid in all_ids(source)}
    prefix = ENTITY_PREFIX[collection]
    n = 1
    while f"{prefix}{n}".lower() in taken:
        n += 1
    return f"{prefix}{n}"


def used_by(source, collection, eid):
    """Everything that names this entry, as (collection, id) pairs -- what Woodcore lists before it deletes a node."""
    out = []
    if collection == "points":
        for member in source["members"]:
            if eid in (member.get("p1"), member.get("p2")):
                out.append(("members", member["id"]))
        for support in source["supports"]:
            if support.get("point") == eid:
                out.append(("supports", support["id"]))
        for load in source["point_loads"]:
            if load.get("point") == eid:
                out.append(("point_loads", load["id"]))
        for dim in source.get("dimensions", []):
            if any((dim.get(end) or {}).get("point") == eid for end in ("from", "to")):
                out.append(("dimensions", dim["id"]))
    elif collection == "members":
        for release in source["releases"]:
            if release.get("member") == eid:
                out.append(("releases", release["id"]))
        for load in source["line_loads"]:
            if load.get("member") == eid:
                out.append(("line_loads", load["id"]))
        for load in source["point_loads"]:
            if load.get("reference") == eid:
                out.append(("point_loads", load["id"]))
        for dim in source.get("dimensions", []):
            if any((dim.get(end) or {}).get("member") == eid for end in ("from", "to")):
                out.append(("dimensions", dim["id"]))
    return out


def remove(source, collection, eid):
    """Deletes an entry and everything hanging off it, and says what went -- a node takes its members, its support and its loads with it, and those members take their own releases and line loads."""
    removed = []
    i = index_of(source, collection, eid)
    if i is None:
        return removed
    for child_collection, child_id in used_by(source, collection, eid):
        removed += remove(source, child_collection, child_id)
    i = index_of(source, collection, eid)
    if i is not None:
        removed.append((collection, source[collection].pop(i)))
    return removed


def rename(source, collection, old, new):
    """Renames an entry and every reference to it -- what an id cell edited in one of Woodcore's four lists does. Raises where the new id is taken or malformed, so a clash refuses rather than merges two things into one."""
    where = f"model {source.get('id', '?')}"
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
    if collection == "points":
        for member in source["members"]:
            for end in ("p1", "p2"):
                if member.get(end) == old:
                    member[end] = new
        for support in source["supports"]:
            if support.get("point") == old:
                support["point"] = new
        for load in source["point_loads"]:
            if load.get("point") == old:
                load["point"] = new
        for dim in source.get("dimensions", []):
            for end in ("from", "to"):
                if (dim.get(end) or {}).get("point") == old:
                    dim[end]["point"] = new
    elif collection == "members":
        for release in source["releases"]:
            if release.get("member") == old:
                release["member"] = new
        for load in source["line_loads"]:
            if load.get("member") == old:
                load["member"] = new
        for load in source["point_loads"]:
            if load.get("reference") == old:
                load["reference"] = new
        for dim in source.get("dimensions", []):
            for end in ("from", "to"):
                if (dim.get(end) or {}).get("member") == old:
                    dim[end]["member"] = new


# --- Geometry (metres, x right and z down) --------------------------------------
# Tolerant of a draft: Woodcore calls these on every movement of the mouse, on a model that is still being drawn.


# --- Hit-testing and snapping ---------------------------------------------------


# --- Tracking, the way AutoCAD tracks -------------------------------------------
# Hovering a point acquires it; the cursor then follows a ray from it -- one of the eight polar directions, or the axis or the normal of a member meeting there, or the line of a member extended -- and a distance typed along that ray places the point. All of it is arithmetic on plain tuples, so it is verified without a window.


# --- The values a load shows ----------------------------------------------------


def known_values(data_dir):
    """The same, read from data/ -- what Woodcore's window has, saving a model without the whole export being run again: every variable a link may name (`variable_sources.known_values`). Empty where nothing has been exported yet, so the window opens on a fresh checkout without complaining."""
    import variable_sources   # the reader of data/'s files: imported here, since it imports the domains that import this one
    return variable_sources.known_values(Path(data_dir))


def reference_text(magnitude):
    """A reference as one string, for the record's provenance and for a warning: `snow-load/SL-Dach1/q_k11`."""
    return f"{magnitude['domain']}/{magnitude['instance']}/{magnitude['var']}"


def resolve(magnitude, width=None, values=None, width_optional=False):
    """A magnitude's number and unit, the factor, the constant and the influence width applied.

    Returns {value, unit, base_value, base_unit, from, missing, given, factor, offset, description}. `given` is False for a load that states no magnitude at all, which is not an error: a value is only ever shown and scaled by, never calculated with, so a system may be drawn before its actions are known. `value` is None where a reference names a var the export does not have, or one whose value is text (a dropdown entry such as "Flachdach" is not a load) -- `missing` then says which, and the export turns it into a warning rather than a stop, for the reason a connection linked to no connector is warned about (docs/decisions.md §13).

    Two pieces of arithmetic happen here, and they are the module's only ones. A referenced var may be taken with a **factor** and a **constant** -- 0.8 x SL, SL + 10 -- which is how a design value is written down beside the characteristic one it comes from. And the **influence width**: an action calculated per square metre times the width it acts over is a load per metre, which is what a static system carries, one metre coming off the unit with it.
    """
    values = values or {}
    kind = magnitude_kind(magnitude)
    out = {"value": None, "unit": "", "base_value": None, "base_unit": "", "from": "", "missing": "",
           "given": kind in ("literal", "reference"), "factor": 1.0, "offset": 0.0, "description": "",
           "width_applied": False}
    if kind == "none":
        return out
    if kind == "literal":
        out["base_value"] = float(magnitude["value"])
        out["base_unit"] = magnitude["unit"]
    elif kind == "reference":
        out["from"] = reference_text(magnitude)
        out["factor"] = float(magnitude.get("factor", 1.0))
        out["offset"] = float(magnitude.get("offset", 0.0))
        out["description"] = (magnitude.get("description") or "").strip()
        # the one resolution of a link (links.resolve, ARCH-001), in the variable's own unit -- a magnitude states none of its own -- and the words this module has always said it in
        last = magnitude.get("last") or {}
        found = links.resolve(magnitude, values, None, last.get("value"))
        if found["stale"]:
            code = found["missing"].code
            if code == "link_not_a_number":
                value = found["missing"].args.get("value")
                out["missing"] = engine.Note("statics_not_a_number", f"{out['from']} is {value!r}, which is not a number", ref=out["from"], value=value)
            else:
                out["missing"] = engine.Note("statics_no_variable", f"no such variable: {out['from']}", ref=out["from"])
            # the value it last had, which Woodcore's window wrote beside the reference: kept and warned about rather than drawn as «?» (D-06); none where the source predates it
            if not last:
                return out
            out["base_value"], out["base_unit"] = float(last["value"]), last["unit"]
        else:
            out["base_value"] = found["value"]
            out["base_unit"] = found["unit"]
    else:
        out["missing"] = engine.Note("statics_no_magnitude", "the magnitude is neither a value nor a variable")
        return out

    out["value"], out["unit"] = out["base_value"], out["base_unit"]
    if width:
        unit = width_unit(out["base_unit"])
        if unit is None:
            # the model's width stands for the whole drawing, so it passes over a load it cannot apply to -- a force in kN among loads per square metre. A width the engineer put on a load itself was meant for it, and is refused instead.
            if width_optional:
                return out
            out["missing"] = engine.Note(
                "statics_width_unit",
                f"{out['base_unit'] or 'no unit'} cannot be multiplied by an influence width -- "
                f"a width multiplies a load per metre or per square metre",
                unit=out["base_unit"] or "–")
            out["value"] = None
            return out
        out["value"] = out["base_value"] * float(width["value"])
        out["unit"] = unit
        out["width_applied"] = True
    return out


def is_linked(source):
    """Whether a model follows a variable anywhere -- a field's `links`, or a magnitude's `last` -- or carries a text (issue #43): what makes it a 1.2 source."""
    if links.is_linked(source, link_spec()) or source.get(figure_text.COLLECTION):
        return True
    return any(isinstance(load.get(key), dict) and ("last" in load[key] or "origin" in load[key])
               for collection in ("point_loads", "line_loads") for load in source.get(collection, []) for key in ("magnitude", "magnitude_end"))


def refresh_links(source, values):
    """Every linked field and every magnitude naming a variable given, in `source` itself, the value the variable gives now -- its last value (D-14) --, a field whose variable cannot be read left as it is. What Woodcore's window does as it opens a model and as it saves one, so the drawing on screen is the one the report will print; never the export, which writes no source."""
    links.refresh_all(source, link_spec(), values)
    figure_text.refresh_all(source, values)
    for collection in ("point_loads", "line_loads"):
        for load in source.get(collection, []):
            for key in ("magnitude", "magnitude_end"):
                magnitude = load.get(key)
                if magnitude_kind(magnitude) != "reference":
                    continue
                found = resolve(magnitude, None, values)
                if not found["missing"]:
                    magnitude["last"] = {"value": _clean(found["base_value"]), "unit": found["base_unit"]}
    return source


def stamp_version(source, values=None):
    """Before Woodcore's window writes a model: its linked values refreshed where `values` are given (`refresh_links`), and the schema_version that says so, 1.2 where the model follows a variable and 1.1 where it does not."""
    if values is not None:
        refresh_links(source, values)
    if figure_text.COLLECTION in source and not source[figure_text.COLLECTION]:
        del source[figure_text.COLLECTION]   # the last text deleted: the model is 1.1 again, as it was before one was placed
    source["schema_version"] = LINKED_SCHEMA_VERSION if is_linked(source) else SOURCE_SCHEMA_VERSION
    return source


def link_spec():
    """LINKABLE as `links` reads a source of several collections: the model's own fields under links.SELF."""
    return {links.SELF if collection == "model" else collection: fields for collection, fields in LINKABLE.items()}


def follow_links(source, values):
    """The model with every field that follows a variable (`links`) set to what the variable gives now: (model, provenance, warnings) -- `links.follow`. The source itself is never changed; a field whose variable cannot be read keeps the number the source holds, its last value, with a warning (D-06). A load's magnitude is not among these: it names its variable in its own reference form, `resolve`'s."""
    return links.follow(source, link_spec(), values or {}, f"model {source.get('id') or '?'}")


def width_of(source, load):
    """The influence width a load is multiplied by, and whether it is the model's: its own where it carries one, else the model's, which stands for the whole drawing. A load's own is the exception and overrides it."""
    own = load.get("width")
    if own:
        return own, False
    return source.get("width"), True


def load_lines(load, resolved, end=None):
    """What the figure writes beside a load: the first line from its `show` mode, the second the influence width where the load carries one of its own and it is to be shown. A load that states no value shows its name alone; one whose value could not be read is written as `?`, so the figure says so rather than saying nothing. A load that tapers is written from one end to the other -- `0 … 12 kN/m` -- since neither end on its own is the load that is drawn."""
    mode = load.get("show", "name+value")
    name = (load.get("label") or "").strip()
    if not resolved["given"]:
        return [name] if name and mode != "none" else []
    number = "?" if resolved["value"] is None else figure_number(resolved["value"])
    if end is not None and end["given"]:
        far = "?" if end["value"] is None else figure_number(end["value"])
        if far != number:
            # an en dash with spaces, the way a range is set, and not a hyphen, which would read as a minus
            number = f"{number} \u2026 {far}"
    value = f"{number} {resolved['unit']}".strip()
    if mode == "none":
        first = ""
    elif mode == "name":
        first = name
    elif mode == "value":
        first = value
    else:
        first = f"{name} = {value}" if name else value
    lines = [first] if first else []
    # the model's own width stands under the drawing, once, rather than beside every load it applies to
    own = load.get("width")
    if own and own.get("show", True) and mode != "none":
        label = (own.get("label") or DEFAULT_WIDTH_LABEL).strip()
        lines.append(f"{label} = {figure_number(own['value'])} {WIDTH_UNIT}")
    return lines


def width_note(width):
    """The sentence the figure puts under the drawing for an influence width that carries a description: `b_e = 3.6 m — Einflussbreite Dach, Achse 2-3`. A long description would crowd the arrow, so it is said once, underneath -- and a model's own width is only ever said there."""
    if not width or not width.get("show", True):
        return ""
    description = (width.get("description") or "").strip()
    if not description:
        return ""
    label = (width.get("label") or DEFAULT_WIDTH_LABEL).strip()
    # an en dash, not the two hyphens this project's prose uses: this line is printed on a figure, not read in a source file
    return f"{label} = {figure_number(width['value'])} {WIDTH_UNIT} — {description}"


def value_note(load, resolved, width=None):
    """The line the figure puts under the drawing for a load whose value is not simply itself: where it was read from, the factor and the constant it was taken with, the width it was multiplied by, and whatever the engineer wrote about it.

    It is what makes a number on a figure traceable: `q_d = 0.8 · q_k11 + 2 = 3.106 kN/m² [snow-load/SL-Dach1] × b_e = 2.5 m — Schnee, Feld 2`. The expression is given in letters and then, as everywhere else in this report, in the number it came to (§10bis); without that number the line reads as though the variable's name were the value. A value typed in the window and taken as it stands needs no such line and gets none.
    """
    if not resolved["given"] or resolved["base_value"] is None:
        return ""
    if not resolved["from"] and not resolved["width_applied"] and not resolved["description"]:
        # a number typed in the window and taken as it stands says everything beside its own arrow
        return ""
    if resolved["from"]:
        var = resolved["from"].rsplit("/", 1)[-1]
        expression = var if resolved["factor"] == 1.0 else f"{figure_number(resolved['factor'])} · {var}"
        if resolved["offset"]:
            sign = "+" if resolved["offset"] > 0 else "−"
            expression += f" {sign} {figure_number(abs(resolved['offset']))}"
        expression += f" = {figure_number(resolved['base_value'])}"
        if resolved["base_unit"]:
            expression += f" {resolved['base_unit']}"
        pieces = [f"{expression} [{resolved['from'].rsplit('/', 1)[0]}]"]
    else:
        pieces = [f"{figure_number(resolved['base_value'])} {resolved['base_unit']}".strip()]
    if width and resolved["width_applied"]:
        label = (width.get("label") or DEFAULT_WIDTH_LABEL).strip()
        pieces.append(f"× {label} = {figure_number(width['value'])} {WIDTH_UNIT}")
    name = (load.get("label") or load["id"]).strip()
    line = f"{name} = " + " ".join(pieces)
    if resolved["description"]:
        line += f" — {resolved['description']}"
    return line


def resolved_loads(source, values):
    """Every load of the model, resolved once: [(collection, load, resolved, resolved at the far end)]. Built here rather than in the drawing, so the record and the figure print the same numbers."""
    out = []
    for collection in ("point_loads", "line_loads"):
        for load in source.get(collection, []):
            width, from_model = width_of(source, load)
            resolved = resolve(load.get("magnitude"), width, values, from_model)
            end = None
            if load.get("magnitude_end") is not None:
                end = resolve(load["magnitude_end"], width, values, from_model)
            out.append((collection, load, resolved, end))
    return out


def releases_at(source, pid):
    """The releases sitting on a node: [(member id, end, release)]. A release belongs to an end of a member, and a node is where those ends meet -- which is what lets a point's own list show and set one."""
    out = []
    for member in source.get("members", []):
        for end, key in (("start", "p1"), ("end", "p2")):
            if member.get(key) != pid:
                continue
            release = next((r for r in source.get("releases", [])
                            if r.get("member") == member["id"] and r.get("end") == end), None)
            out.append((member["id"], end, release))
    return out


# --- Warnings -------------------------------------------------------------------


def warnings(source, values=None, where=None):
    """What is worth saying about a model without refusing it, as sentences. A reference that no longer resolves is the important one: the workbook may have been reorganized since, and the report must still build."""
    sid = source.get("id") or "?"
    where = where or f"model {sid}"
    out = []
    for _collection, load, resolved, end in resolved_loads(source, values or {}):
        for part, name, code in ((resolved, "value", "statics_unread"), (end, "value at the far end", "statics_unread_end")):
            if part is not None and part["given"] and part["missing"]:
                out.append(engine.Note(code, f"{where}: the {name} of load {load['id']} could not be read -- {part['missing']}",
                                       model=sid, load=load["id"], detail=part["missing"]))
    if not source.get("supports"):
        out.append(engine.Note("statics_no_support", f"{where}: nothing holds it -- it has no support", model=sid))
    used = set()
    for member in source.get("members", []):
        used.update((member.get("p1"), member.get("p2")))
    for support in source.get("supports", []):
        used.add(support.get("point"))
    for load in source.get("point_loads", []):
        used.add(load.get("point"))
    for dim in source.get("dimensions", []):
        for end in ("from", "to"):
            used.add((dim.get(end) or {}).get("point"))
    for point in source.get("points", []):
        if point["id"] not in used:
            out.append(engine.Note("statics_idle_point", f"{where}: point {point['id']} carries nothing and holds nothing", model=sid, point=point["id"]))
    return list(dict.fromkeys(out))


# --- The report record ----------------------------------------------------------


def build_record(source, values=None, drawings=None):
    """One model's entry of data/statics.json. The report sets the figure in a caption and may put a halo under one of its parts, so the record carries the frame, the size unit, what was drawn and where -- and, for every load, the number shown with where it came from, which is what makes a figure's value traceable to a cell of the workbook."""
    from domains import statics_svg  # the frame is the drawing's to compute: a load's arrow reaches well past the last node

    values = values or {}
    sid = source["id"]
    if drawings is None:
        drawings = {lang: statics_svg.layout(source, values, lang) for lang in strings.LANGUAGES}
    record = statics_svg.meta(drawings[strings.SOURCE_LANGUAGE])
    record["label"] = source.get("label", "")
    record["source"] = f"statics/{sid}.json"
    # One figure per language, each with its own frame and its own notes (docs/typst/language.md §4bis): the notes
    # are drawn inside the drawing and the frame is sized to hold them, so a longer sentence in one
    # language widens that language's figure and no other. Everything else in this record -- the scale, the
    # size unit, every placed point -- is geometry, and identical in all three.
    record["figures"] = {
        lang: {
            "file": f"statics/{sid}-{lang}.svg",
            "view": statics_svg.meta(drawings[lang])["view"],
            "notes": drawings[lang].get("notes", []),
        }
        for lang in strings.LANGUAGES
    }
    record.pop("view")
    record["style"] = {key: float(source.get("style", {}).get(key, 1.0)) for key in STYLE_KEYS}
    record["labels"] = all_ids(source)
    record["unresolved"] = [
        f"{load['id']}: {part['missing']}"
        for _collection, load, resolved, end in resolved_loads(source, values)
        for part in (resolved, end)
        if part is not None and part["missing"]
    ]
    return record


def text_records(source, values, where, notes):
    """The texts of a model as its record carries them: [{id, text, lines, links?}] -- what each printed and, where it printed a variable, where that came from (REQ-012). Their warnings are added to `notes`."""
    out = []
    for text in source.get(figure_text.COLLECTION, []):
        printed, provenance, found = figure_text.resolve(text, values, f"{where}, text {text['id']}")
        notes += found
        record = {"id": text["id"], "text": text.get("text", ""), "lines": printed}
        if provenance:
            record["links"] = provenance
        out.append(record)
    return out


# --- Export ---------------------------------------------------------------------


def prepare(source_dir, values=None, place=None):
    """Every static model, checked and built: (data, files, warnings). `files` is keyed by the figure's name in the JSON, which `place` (an engine.Figures) gives: from the Typst root in a project laid out by folders, under data/ otherwise. Nothing is written here, so an export that fails leaves data/ as it was. Until 0.117 it also took the models an RFEM import generated, held in memory; the import was retired then (archive/rfem/), and every model is one drawn in Woodcore."""
    from domains import statics_svg

    values = values or {}
    place = place or engine.Figures(None, "statics")
    models, files, notes = {}, {}, []
    sources = [read_source(path, notes) for path in source_paths(source_dir)]
    for source in sources:
        source, provenance, followed = follow_links(source, values)
        notes += followed
        drawings = {lang: statics_svg.layout(source, values, lang) for lang in strings.LANGUAGES}
        notes += warnings(source, values)
        models[source["id"]] = build_record(source, values, drawings)
        if provenance:
            models[source["id"]]["links"] = provenance
        texts = text_records(source, values, f"model {source['id']}", notes)
        if texts:
            models[source["id"]]["texts"] = texts
        for lang, drawing in drawings.items():
            name = place.name(f"{source['id']}-{lang}.svg")
            models[source["id"]]["figures"][lang]["file"] = name
            files[name] = statics_svg.render(drawing)
    linked = any("links" in record or "texts" in record for record in models.values())
    version = LINKED_EXPORT_VERSION if linked else EXPORT_SCHEMA_VERSION
    data = {"schema_version": ROOTED_EXPORT_VERSION if place.here is not None else version, "models": models}
    validation.validate_structure(data, "statics")
    validation.validate_statics_business(data)
    return data, files, notes


def write(data, files, data_dir):
    """The only writer: data/statics.json and the models' figures -- into the tab's Exports/Figures/ in a project laid out by folders, data/statics/ otherwise (engine.Figures) --, those of models that no longer exist removed: only what the last export wrote, never a file of the engineer's. A file whose content has not changed is left alone, so Git sees a change only where there is one."""
    data_dir = Path(data_dir)
    engine.figures(data_dir, "statics").write(files, engine.previous_json(data_dir / "statics.json"))
    engine.write_json(data_dir / "statics.json", data)


def export(source_dir, data_dir, values=None):
    """prepare + write, and the warnings -- what Woodcore's window runs when a model is saved, so the report sees it without the whole export being run again."""
    data, files, notes = prepare(source_dir, values, place=engine.figures(data_dir, "statics"))
    write(data, files, data_dir)
    return notes
