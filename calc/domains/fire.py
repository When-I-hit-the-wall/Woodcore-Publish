"""Fire-protection plans (Brandschutzpläne, plans de protection incendie): the concept of a floor, drawn by hand over an architect's plan, from the definition Woodcore saves.

A fire-protection plan is drawn in Woodcore's «Protection incendie» tab and saved as one source file per plan, `fire/<id>.json` in the project's sources. Woodcore is the only thing that writes it, and this module the only thing that reads it -- the position plans' arrangement, for the same reasons (domains/plan.py).

It is drawn over a FRAME: a background -- a file of the project or, since 2.0, a page of an imported document, shared with the position plans --, a sheet, a crop and a scale. A plan that names a position plan (`plan`) FOLLOWS that plan's frame, read afresh at every reading, so changing the background, the crop or the scale in «Plan de positions» changes them here -- one source for one thing. A plan that names none carries a frame of its own, in the very four fields a position plan states, checked by the very function that checks them there (plan.check_frame, background.document included). Never both: a background, a sheet or a scale stated twice is one that disagrees with itself.

The one field a plan that follows a position plan may state for itself is its CROP -- what the report shows: a position plan often carries three floors on one sheet, and a fire-protection plan is one floor. Absent, the position plan's crop is taken, as before; present, it is this plan's own and stays so (the engineer's decision of 2026-10-05: «on doit pouvoir importer celui du plan de position mais également en créer un»). It is the pattern of a value that follows another source and may be written over (a schema element's b and h, v0.75).

What is drawn is what the top of the AEAI's sample legend lists, and nothing else -- the engineer's choice (2026-10-05) among the sheets' hundred pictograms:

- the SURFACES (`zones`): closed outlines drawn by hand, each of one of the three kinds the sheet gives a surface of an escape route -- a vertical escape route, a horizontal one, a surface to be kept clear;
- the WALLS with their fire resistance: a line and one of the sheet's classes (norms/vkf.py), drawn as that class's coloured band;
- the DOORS: a swing door, the sheet's quarter disc, or a sliding one, its flat arrow -- with the fire resistance the sheet gives a door (EI 30, E 30) or with none, which is no symbol of the sheet -- and the way each opens: where its hinge is and to which side of the wall;
- the ESCAPE ROUTES' three marks: the length (`routes`, a thin green arrow with its length along it), the emergency exit (`exits`, the thick green arrow) and the width (`widths`, a green figure across the passage);
- and a LEGEND, a box placed on the plan that lists what is drawn.

How large it is drawn is the position plan's own logic (domains/figure_style.py): the plan's `style` scales every stroke (`line`) and every text (`text`), and an entry may state a factor of its own MULTIPLYING the plan's, for the factors it is drawn with. Beside them an entry may state how opaque it is drawn (`opacity`), a text may be moved clear of what it hides (`label_offset`, from its own place, so that it follows its entry), and the legend has a size of its own (`legend.scale`).

Nothing is delimited by the program: until 2026-10-05 it read the plan's picture and proposed the rooms as zones, which the engineer had removed -- a proposal that needs correcting on every plan costs more than the outlines it saves. Nothing is computed for a check either: an area, a length and a width are the drawing's own, measured with the frame's scale.

The EXPORT (`prepare`, `write`, `export`) is the position plans' arrangement: data/fire.json, one record per plan, and under data/fire/ the drawing once per language -- the legend carries words -- and the background of a plan that has one of its own; a plan that follows a position plan is set over that plan's exported background, which is then in data/ once.

A page of a document may carry both kinds of plan, and turning it turns both (`rotate_source`, beside plan.rotate_source; calc/domains/plan_pages.py does the writing). Archiving a position plan that fire plans follow DETACHES them first (`detach`): the frame they followed is copied into them.

No Qt in it, so the window's canvas and a test script call the same functions.
"""

import copy
import json
import math
import re
from pathlib import Path

import engine
import validation
from domains._common import fail as _fail  # one copy of the domains' helpers (spec 2026-10-19-base-saine-nettoyage, G4)
from domains import figure_style, plan
from domains import figure_text  # a text placed with the Text tool (issue #43): its last values, refreshed as a plan is saved
from i18n import strings
from norms import vkf
from domains._common import source_paths  # one copy (G4)

# 2.0 (v0.115, the engineer's decision of 06.10.2026): the frame of a plan that carries one of its own may be drawn on a page of an imported document (`background.document`, plan-source 1.2's own field), whose rotation and layers are then the document's. A 1.0 source -- Gian's, whose background is a file only -- is read as it is and upgraded on reading (`upgrade`): nothing is written until the plan is saved.
SOURCE_SCHEMA_VERSION = "2.0"
# 2.1 is 2.0 with `texts`, the Text tool's (issue #43, spec 2026-10-11-variables-liees-champs-et-textes): written only by a plan that holds one (`version_of`), so a plan without a text is saved and exported as before
TEXT_SCHEMA_VERSION = "2.1"
SOURCE_SCHEMA_VERSIONS = ("1.0", SOURCE_SCHEMA_VERSION, TEXT_SCHEMA_VERSION)
# 2.0 adds `legend_lines`, the legend as lines the report sets in its own typeface (as a position plan's), and lets a background be a page of a document.
EXPORT_SCHEMA_VERSION = "2.0"
# 2.1 is 2.0 with a plan's `texts`, what each printed: written only where one holds a text
TEXT_EXPORT_VERSION = "2.1"
# 2.2 is 2.1 with its figures and backgrounds named from the Typst root (`/Plans/Fire-plan/Exports/Figures/F01-fr.svg`): written by a project laid out by folders, where they lie in the tab's Exports/Figures/ (issue #64, D-10)
ROOTED_EXPORT_VERSION = "2.2"


def version_of(source):
    """The schema_version Woodcore writes a fire-protection plan at: 2.1 where it holds a text, 2.0 where it does not."""
    return TEXT_SCHEMA_VERSION if source.get("texts") else SOURCE_SCHEMA_VERSION
EXPORT_FILE = "fire.json"

# The word this source is called by in figure_style.ENTRY_KEYS, the table of which entry may state which factor.
STYLE_KIND = "fire"
# The factors the plan itself states: there is no symbol placed on a point here, so `point` would be a slider nobody could see the effect of.
STYLE_KEYS = ("line", "text")
STYLE_RANGE = figure_style.RANGE

# A plan's own pattern: the id is the file name and the string the report will address the plan by.
ID_PATTERN = plan.ID_PATTERN

# An entry's id, unique in its plan across every collection: what is selected, and what the report will highlight, is named by its id alone.
ENTRY_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")

# The collections an id may be in, in the order a click looks through them -- what is drawn on top first -- and the letter a new entry of each is named with: Z a surface (Zone), W a wall (Wand), T a door (Türe), F an escape route's length (Fluchtweglänge), N an emergency exit (Notausgang), B an escape route's width (Fluchtwegbreite).
COLLECTIONS = ("widths", "exits", "routes", "doors", "walls", "zones")
PREFIXES = {"zones": "Z", "walls": "W", "doors": "T", "routes": "F", "exits": "N", "widths": "B", "texts": "X"}

# Every collection an id may be in: the six of the concept and, over them, the texts placed with the Text tool (issue #43), X1, X2 -- the letter T being a door's. Kept apart from COLLECTIONS, which the tab lists and the canvas snaps to: a text is in no list of the concept and no corner of it is a point to draw from. Each is `{id, points: [[x, y]], text, vars?, style?}`, the position plan's own shape (plan.check_texts), so it is moved, copied and turned by its points as every entry here is.
ENTRY_COLLECTIONS = ("texts",) + COLLECTIONS

# What a surface may be: the three the sheet draws as a filled or hatched surface, by their keys in norms/vkf.py. A surface that states none is a draft -- one drawn before the kinds existed --, shown in the editor and never printed.
SURFACES = ("vertical", "horizontal", "clear")

# The two ways a door opens (norms/vkf.py's own two): a leaf turning on a hinge, a leaf sliding along the wall.
DOOR_KINDS = vkf.DOOR_KINDS
# How many straight pieces the quarter circle of a swing door is drawn with: SVG Tiny has no arc command.
ARC_STEPS = 16

# How opaque an entry is drawn where it states nothing: a surface is tinted, so that the plan under it -- a stair's treads, a corridor's doors -- stays readable, and everything else is drawn full. The collections named here are the ones that may state an `opacity`: an escape route's width is a text and has none.
OPACITY = {"zones": 0.65, "walls": 1.0, "doors": 1.0, "routes": 1.0, "exits": 1.0}
OPACITY_RANGE = (0.1, 1.0)

# The collections whose entries write a text that may be moved by hand (`label_offset`): a surface its name, an escape route its length, a width its figure.
TEXT_COLLECTIONS = ("zones", "routes", "widths")

# How far the legend's size may be set, the factors' own range.
LEGEND_SCALE_RANGE = figure_style.RANGE

# The band a wall's fire resistance is drawn as: this wide in metres where the plan has a scale -- about a wall's own thickness, the band lying over the wall as the VKF's sample plans draw it -- and WALL_BAND_UNITS of the drawing's unit where it has none.
WALL_BAND_M = 0.25
WALL_BAND_UNITS = 5.0

# Where a legend just switched on stands: this many of the drawing's units in from the top left corner of the crop.
LEGEND_MARGIN_UNITS = 12.0

# The four fields of a frame, a position plan's own. Present on a fire-protection plan that follows no position plan, and on none that does.
FRAME_KEYS = ("background", "sheet", "crop", "scale")

# A coordinate as it is saved: to a hundredth of a sheet unit, as a position plan's.
DECIMALS = 2

SAME_POINT = plan.SAME_POINT


def _ring(ring, where, what):
    """An outline: at least three points, no two consecutive ones the same, enclosing a surface."""
    if not isinstance(ring, list) or len(ring) < 3:
        _fail(where, f"{what} has {len(ring) if isinstance(ring, list) else 0} point(s) -- an outline has at least three")
    for j, p in enumerate(ring, start=1):
        plan._point(p, where, f"{what}: point {j}")
    for j in range(len(ring)):
        if math.dist(ring[j - 1], ring[j]) <= SAME_POINT:
            _fail(where, f"{what}: points {j or len(ring)} and {j + 1} are the same point")
    if ring_area(ring) <= SAME_POINT:
        _fail(where, f"{what} encloses no surface")


def _line(points, where, what, exactly=None):
    """A line drawn from point to point: at least two points -- `exactly` that many where given --, no two consecutive ones the same."""
    count = len(points) if isinstance(points, list) else 0
    if exactly is not None and count != exactly:
        _fail(where, f"{what} has {count} point(s) -- it has exactly {exactly}")
    if count < 2:
        _fail(where, f"{what} has {count} point(s) -- a line has at least two")
    for j, p in enumerate(points, start=1):
        plan._point(p, where, f"{what}: point {j}")
    for j in range(1, len(points)):
        if math.dist(points[j - 1], points[j]) <= SAME_POINT:
            _fail(where, f"{what}: points {j} and {j + 1} are the same point")


def _own(entry, collection, where, at):
    """What an entry may state of how it is drawn: the factors it is drawn with (figure_style's table), how opaque it is, and where its text was moved to."""
    figure_style.check(entry.get("style"), lambda message: _fail(where, f"{at}: {message}"), may=figure_style.allowed(STYLE_KIND, collection))
    if "opacity" in entry:
        if collection not in OPACITY:
            _fail(where, f"{at}: opacity means nothing here -- it is a text")
        value = plan._number(entry["opacity"], where, f"{at}: opacity")
        if not OPACITY_RANGE[0] <= value <= OPACITY_RANGE[1]:
            _fail(where, f"{at}: opacity is {entry['opacity']} -- from {OPACITY_RANGE[0]} to {OPACITY_RANGE[1]}")
    if "label_offset" in entry:
        if collection not in TEXT_COLLECTIONS:
            _fail(where, f"{at}: label_offset means nothing here -- it writes no text")
        plan._point(entry["label_offset"], where, f"{at}: label_offset")


def _entry_id(eid, seen, where, at):
    """An id is unique in the whole plan, not in its collection: the report's highlight will name an id and must not have to ask which collection it meant."""
    if not ENTRY_ID.match(eid):
        _fail(where, f"{at}: id {eid!r} -- a letter, then letters, digits and _")
    if eid in seen:
        _fail(where, f"{at}: the id {eid} is used twice")
    seen.add(eid)


# --- The source file ------------------------------------------------------------

def check_source(source, where):
    """Everything a source file must satisfy -- its structure against schemas/fire-source.schema.json, then the rules a schema cannot state. Every failure is a blocking error naming the file and the field. What does not stop anything -- a position plan that is gone, a surface outside the frame -- is `warnings`'."""
    if isinstance(source, dict) and source.get("schema_version") not in (None,) + SOURCE_SCHEMA_VERSIONS:
        _fail(where, f"schema_version is {source.get('schema_version')!r} -- expected one of {', '.join(SOURCE_SCHEMA_VERSIONS)}")
    try:
        validation.validate_structure(source, "fire-source")
    except validation.ValidationError as exc:
        _fail(where, str(exc))

    if not ID_PATTERN.match(source["id"]):
        _fail(where, f"id {source['id']!r} -- use letters, digits and _ . + - only, starting with a letter or a digit")

    own = [key for key in FRAME_KEYS if key in source and key != "crop"]
    if "plan" in source:
        if not source["plan"].strip():
            _fail(where, "plan is empty -- name the position plan this plan follows, or give it a frame of its own")
        if own:
            _fail(where, f"it follows the position plan {source['plan']!r} and states its own {', '.join(own)} as well -- a fire-protection plan follows a position plan or carries a frame of its own, never both")
        if "crop" in source:
            # the one field it may state for itself; whether it lies on the sheet is the position plan's to say, and so a warning (`warnings`)
            for key in ("x", "y"):
                plan._number(source["crop"][key], where, f"crop.{key}")
            for key in ("w", "h"):
                plan._number(source["crop"][key], where, f"crop.{key}", positive=True)
    else:
        if "sheet" not in source:
            _fail(where, "it names no position plan (plan) and has no sheet of its own -- one of the two says what it is drawn over")
        plan.check_frame(source, where)

    figure_style.check(source.get("style"), lambda message: _fail(where, message), may=STYLE_KEYS)
    plan.check_superposition(source, where)   # another fire plan shown over this one, a drawing aid of the window (v0.116)

    seen = set()
    for i, zone in enumerate(source["zones"], start=1):
        at = f"surface {i} ({zone['id']})"
        _entry_id(zone["id"], seen, where, at)
        if "kind" in zone and zone["kind"] not in SURFACES:
            _fail(where, f"{at}: kind {zone['kind']!r} -- expected one of {', '.join(SURFACES)}")
        _ring(zone["points"], where, f"{at}: outline")
        for j, hole in enumerate(zone.get("holes", []), start=1):
            _ring(hole, where, f"{at}: island {j}")
        _own(zone, "zones", where, at)

    classes = vkf.resistance_keys()
    for i, wall in enumerate(source.get("walls", []), start=1):
        at = f"wall {i} ({wall['id']})"
        _entry_id(wall["id"], seen, where, at)
        if wall["class"] not in classes:
            _fail(where, f"{at}: class {wall['class']!r} -- expected one of {', '.join(classes)}")
        _line(wall["points"], where, at)
        _own(wall, "walls", where, at)

    classes = vkf.door_classes()
    for i, door in enumerate(source.get("doors", []), start=1):
        at = f"door {i} ({door['id']})"
        _entry_id(door["id"], seen, where, at)
        if door["kind"] not in DOOR_KINDS:
            _fail(where, f"{at}: kind {door['kind']!r} -- expected one of {', '.join(DOOR_KINDS)}")
        if "class" in door and door["class"] not in classes:
            _fail(where, f"{at}: class {door['class']!r} -- expected one of {', '.join(classes)}, or none for a door without a fire resistance")
        if isinstance(door["side"], bool) or door["side"] not in (1, -1):
            _fail(where, f"{at}: side is {door['side']!r} -- 1 or -1, the side of its line it opens to")
        _line(door["points"], where, at, exactly=2)
        _own(door, "doors", where, at)

    for i, route in enumerate(source.get("routes", []), start=1):
        at = f"escape route {i} ({route['id']})"
        _entry_id(route["id"], seen, where, at)
        _line(route["points"], where, at)
        _own(route, "routes", where, at)
    for i, entry in enumerate(source.get("exits", []), start=1):
        at = f"emergency exit {i} ({entry['id']})"
        _entry_id(entry["id"], seen, where, at)
        _line(entry["points"], where, at, exactly=2)
        _own(entry, "exits", where, at)
    for i, entry in enumerate(source.get("widths", []), start=1):
        at = f"escape route width {i} ({entry['id']})"
        _entry_id(entry["id"], seen, where, at)
        _line(entry["points"], where, at, exactly=2)
        _own(entry, "widths", where, at)

    plan.check_texts(source, where, STYLE_KIND, TEXT_SCHEMA_VERSION)   # the Text tool's (issue #43), the position plan's own rule
    for i, text in enumerate(source.get("texts", []), start=1):
        _entry_id(text.get("id", ""), seen, where, f"text {i}")

    if "legend" in source:
        for key in ("x", "y"):
            plan._number(source["legend"][key], where, f"legend.{key}")
        if "scale" in source["legend"]:
            scale = plan._number(source["legend"]["scale"], where, "legend.scale")
            if not LEGEND_SCALE_RANGE[0] <= scale <= LEGEND_SCALE_RANGE[1]:
                _fail(where, f"legend.scale is {source['legend']['scale']} -- from {LEGEND_SCALE_RANGE[0]} to {LEGEND_SCALE_RANGE[1]}")


def upgrade(source):
    """A copy of `source` as the current schema reads it: `schema_version` 2.0. A 1.0 source needs nothing else -- its background, a file only, is a valid 2.0 one, and a canvas falls back on `background.file` for a plan that names no document -- so the upgrade is the version and a deep copy, and nothing is written: the plan is written as 2.0 when it is saved, and not before. Anything that is no source is returned as it is for check_source to refuse."""
    if not isinstance(source, dict):
        return source
    upgraded = copy.deepcopy(source)
    if upgraded.get("schema_version") in SOURCE_SCHEMA_VERSIONS:
        upgraded["schema_version"] = version_of(upgraded)
    return upgraded


def read_source(path):
    """One plan's source file, upgraded to the current schema and checked -- nothing is written. Its id must be its file name: the file is how Woodcore finds a plan, the id how the report will."""
    path = Path(path)
    try:
        source = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _fail(path.name, f"not readable as JSON -- {exc}")
    source = upgrade(source)
    check_source(source, path.name)
    if source["id"] != path.stem:
        _fail(path.name, f"id is {source['id']!r} but the file is named {path.name} -- they must agree")
    return source


def new_source(fid, plan_id=None):
    """A plan with nothing drawn yet: following the position plan `plan_id`, or on an empty sheet of its own."""
    source = {"schema_version": SOURCE_SCHEMA_VERSION, "id": fid, "label": "", "zones": []}
    if plan_id:
        source["plan"] = plan_id
    else:
        source["sheet"] = dict(plan.BLANK_SHEET)
    return source


# --- The frame --------------------------------------------------------------------

def plan_frames(plans_dir):
    """The frame of every position plan, by its id: its four frame fields, with its name and label for a list to show. Read leniently -- a position plan that would not pass its own checks still says what it is drawn over, and a file that is no JSON at all is passed over: what a fire-protection plan needs of it is where it lies, not whether it is finished."""
    frames = {}
    for path in plan.source_paths(plans_dir):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict) or not isinstance(data.get("sheet"), dict):
            continue
        frame = {key: data[key] for key in FRAME_KEYS if key in data}
        frame["name"] = data.get("name", "")
        frame["label"] = data.get("label", "")
        frames[path.stem] = frame
    return frames


def follows(source):
    """The id of the position plan `source` follows, or None for a plan with a frame of its own."""
    return source.get("plan") or None


def frame_of(source, frames):
    """(frame, problem): what `source` is drawn over -- a dictionary carrying the frame fields there are, shaped as a position plan's source so that plan.crop_of and plan.units_per_m read it -- and a Note where the position plan it follows is gone, the frame then being an empty sheet. `frames` is plan_frames()'s."""
    pid = follows(source)
    if pid is None:
        return {key: source[key] for key in FRAME_KEYS if key in source}, None
    if pid in frames:
        frame = {key: frames[pid][key] for key in FRAME_KEYS if key in frames[pid]}
        if "crop" in source:
            frame["crop"] = dict(source["crop"])   # its own, over the position plan's
        return frame, None
    fid = source.get("id") or "?"
    return {"sheet": dict(plan.BLANK_SHEET)}, engine.Note("fire_plan_gone", f"fire-protection plan {fid}: the position plan {pid} it follows is gone -- choose another in Woodcore, or give the plan a background of its own", fire=fid, plan=pid)


def own_crop(source):
    """Whether `source` states the crop the report shows itself: always, for a plan with a frame of its own; for one that follows a position plan, only once the engineer has drawn one here -- until then it takes the position plan's."""
    return follows(source) is None or "crop" in source


def per_m(frame):
    """Sheet units per metre of the building, or None for a frame without a scale."""
    return plan.units_per_m(frame)


def drawing_unit(frame):
    """The drawing's unit in sheet units -- the crop's longer side over 850, a position plan's own scale of things (plan_svg.base_unit) -- which every size that is not a length of the building is a multiple of."""
    crop = plan.crop_of(frame)
    return max(crop["w"], crop["h"]) / 850.0


def detach(source, frame):
    """A copy of `source` that follows no position plan any more, the frame it followed copied into it: what archiving a position plan that fire plans follow does to each of them, so that none is left over a frame that is gone. `frame` is frame_of()'s -- the position plan's background, sheet, crop and scale, the plan's own crop over the position plan's where it states one -- and the plan then carries those four fields itself, as a plan with a frame of its own does. A source that follows nothing is returned as a copy."""
    detached = upgrade(source)
    detached.pop("plan", None)
    if follows(source) is None:
        return detached
    for key in FRAME_KEYS:
        if key in frame:
            detached[key] = copy.deepcopy(frame[key])
        else:
            detached.pop(key, None)
    detached["sheet"] = copy.deepcopy(frame.get("sheet") or plan.BLANK_SHEET)
    return detached


# --- Turning it with its page --------------------------------------------------------------

def _turn_points(points, height):
    return [plan.turn_point(p, height) for p in points]


def _turn_vector(vector):
    dx, dy = vector
    return [plan._clean(-float(dy)), plan._clean(float(dx))]


def _turn_quarter(source, width, height, frame=None, lang=strings.SOURCE_LANGUAGE):
    """`source` turned a quarter clockwise, in place, with the page it is drawn on: a point (x, y) of the old sheet goes to (height - y, x), a vector (dx, dy) to (-dy, dx) -- plan._turn_quarter's rule, for the fire plan's own entries. A door's `side` stays: it is counted from the line of the door, which turns with its points. The frame's own fields -- crop, calibration, sheet -- turn only where the plan carries them (a plan that follows a position plan has only its own crop, the rest being the position plan's, which turns with the page by itself)."""
    for collection in ENTRY_COLLECTIONS:
        for entry in source.get(collection, []):
            entry["points"] = _turn_points(entry.get("points", []), height)
            if collection == "zones" and entry.get("holes"):
                entry["holes"] = [_turn_points(hole, height) for hole in entry["holes"]]
            if entry.get("label_offset"):
                entry["label_offset"] = _turn_vector(entry["label_offset"])
    legend = source.get("legend")
    if legend:
        box = None
        if frame is not None:
            from domains import fire_svg  # the drawing module knows how large the legend is

            box = fire_svg.legend_box(source, frame, lang)
        if box is not None:
            # the box itself does not turn, its text staying horizontal: its CENTRE does, so that it stays where it was on the architecture
            x, y, w, h = box
            cx, cy = plan.turn_point([x + w / 2.0, y + h / 2.0], height)
            legend["x"], legend["y"] = plan._clean(cx - w / 2.0), plan._clean(cy - h / 2.0)
        else:
            legend["x"], legend["y"] = plan.turn_point([legend["x"], legend["y"]], height)
    if source.get("crop"):
        source["crop"] = plan.turn_rect(source["crop"], height)
    if follows(source) is None:
        scale = source.get("scale")
        if scale and scale.get("mode") == "calibration" and isinstance(scale.get("points"), list):
            scale["points"] = _turn_points(scale["points"], height)
    return source


def rotate_source(source, quarter_turns, old_sheet, frame=None):
    """A copy of `source` with everything drawn on it turned with its page, `quarter_turns` quarters clockwise (negative: anticlockwise) from a sheet of `old_sheet` (width, height) -- plan.rotate_source's rule for the fire plan's entries: every point of every collection, a surface's islands included, a text moved by hand (`label_offset`, a vector), the legend, and, on a plan with a frame of its own, the crop, a calibration's two points and the sheet. A plan that follows a position plan turns its drawing and its own crop; its sheet is the position plan's, which turns on its own.

    `old_sheet` is the sheet the plan is drawn on (the position plan's, for a plan that follows one); `frame`, frame_of()'s, lets the legend turn about its centre -- its size is the drawing's -- and not about its corner; without it the legend's corner is turned as a point."""
    turned = upgrade(source)
    turns = int(quarter_turns) % 4
    width, height = float(old_sheet[0]), float(old_sheet[1])
    if not turns:
        return turned
    for _ in range(turns):
        turned = _turn_quarter(turned, width, height, frame)
        if frame is not None and frame.get("crop") is not None:
            frame = {**frame, "crop": plan.turn_rect(frame["crop"], height)}
        if frame is not None:
            frame = {**frame, "sheet": {"width": height, "height": width}}
        width, height = height, width
    if follows(turned) is None:
        turned["sheet"] = {"width": plan._clean(width), "height": plan._clean(height)}
    return turned


# --- How large and how opaque --------------------------------------------------------------

def drawing_factors(source):
    """The plan's own factors, 1 where it states none: `line` for every stroke, `text` for every text. (`point` is carried at 1 so that figure_style's arithmetic reads it; the plan cannot state it.)"""
    return figure_style.drawing_factors(source)


def factors(source, entry):
    """The factors one entry is drawn with: the plan's own times the entry's own."""
    return figure_style.product(drawing_factors(source), entry)


def opacity_of(collection, entry):
    """How opaque `entry` is drawn: what it states, else its collection's own (OPACITY) -- 1 for a collection that states none."""
    value = entry.get("opacity")
    if value is not None:
        return float(value)
    if collection == "zones" and entry.get("kind") == "clear":
        return 1.0   # hatched, not tinted: its thin pale lines are drawn full
    return OPACITY.get(collection, 1.0)


def legend_scale(source):
    """The legend's own size factor, 1 where it states none."""
    return float((source.get("legend") or {}).get("scale", 1.0))


# --- Geometry -----------------------------------------------------------------------
# Tolerant of a draft: Woodcore calls these on every movement of the mouse.

# The surface an outline encloses: plan.py's, one source for the zones here and a slab's quantity there (v0.117).
ring_area = plan.ring_area


def zone_area(zone):
    """A surface's area in sheet units squared: its outline's less its islands'."""
    return max(ring_area(zone["points"]) - sum(ring_area(hole) for hole in zone.get("holes", [])), 0.0)


def area_m2(zone, units_per_m):
    """A surface's area in square metres, or None without a scale."""
    if not units_per_m:
        return None
    return zone_area(zone) / (units_per_m * units_per_m)


def inside(point, zone):
    """Whether `point` lies in the surface: within its outline and in none of its islands."""
    if not plan._inside(point, zone["points"]):
        return False
    return not any(plan._inside(point, hole) for hole in zone.get("holes", []))


def hit_zone(source, point):
    """The index of the surface under `point`, the smallest where several lie one in another -- a surface to be kept clear drawn inside a corridor is what a click on it means --, or None."""
    hits = [i for i, zone in enumerate(source.get("zones", [])) if inside(point, zone)]
    if not hits:
        return None
    return min(hits, key=lambda i: zone_area(source["zones"][i]))


def next_id(source, collection, taken=()):
    """The id a new entry of `collection` takes -- its letter and one past the largest number there is, in any collection --, so a number is never given twice: a deleted entry's is not refilled, the positions' own rule (positions_workbook.propose_id)."""
    prefix = PREFIXES[collection]
    largest = 0
    ids = [entry["id"] for each in ENTRY_COLLECTIONS for entry in source.get(each, [])]
    for eid in ids + list(taken):
        match = re.fullmatch(rf"{prefix}(\d+)", eid)
        if match:
            largest = max(largest, int(match.group(1)))
    return f"{prefix}{largest + 1}"


def translate_entry(source, eid, dx, dy):
    """The entry `eid` moved by (dx, dy), in place -- its points, and a surface's islands with them; what is measured from the entry itself (a text moved clear, `label_offset`) moves with it unchanged. The position plan's `plan.translate_entry`, for a fire-protection plan's entries (issue #18, rule 16)."""
    collection, index = entry_of(source, eid)
    entry = source[collection][index]
    entry["points"] = plan.shifted(entry["points"], dx, dy)
    if entry.get("holes"):
        entry["holes"] = [plan.shifted(hole, dx, dy) for hole in entry["holes"]]
    return entry


def copy_entry(source, eid, dx, dy):
    """A copy of the entry `eid`, moved by (dx, dy), added to its collection with an id of its own (`next_id`): the copy's id."""
    collection, index = entry_of(source, eid)
    made = copy.deepcopy(source[collection][index])
    made["id"] = next_id(source, collection)
    source[collection].append(made)
    translate_entry(source, made["id"], dx, dy)
    return made["id"]


def entry_of(source, eid):
    """(collection, index) of the entry `eid`, or None."""
    for collection in ENTRY_COLLECTIONS:
        for i, entry in enumerate(source.get(collection, [])):
            if entry["id"] == eid:
                return collection, i
    return None


def rounded(points):
    """Points as they are saved: to a hundredth of a sheet unit."""
    return [[round(float(x), DECIMALS) + 0.0, round(float(y), DECIMALS) + 0.0] for x, y in points]


def line_length(points):
    return sum(math.dist(points[j - 1], points[j]) for j in range(1, len(points)))


def _axis(a, b):
    """(length, unit vector along a -> b, its normal): the frame a door's, an exit's and a width's shape is laid out in. The normal is the direction turned a quarter towards +y, which is down the sheet: the side `1` of a door."""
    length = math.dist(a, b)
    if length <= 0:
        return 0.0, (1.0, 0.0), (0.0, 1.0)
    ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
    return length, (ux, uy), (-uy, ux)


def side_of(a, b, point):
    """The side of the line a -> b that `point` lies on: 1 or -1, 1 on the line itself. What the third click of the door tool says: to which side the door opens."""
    _length, _u, (nx, ny) = _axis(a, b)
    return -1 if (point[0] - a[0]) * nx + (point[1] - a[1]) * ny < 0 else 1


def _near_polyline(point, points, closed=False):
    """How far `point` lies from the line through `points`."""
    count = len(points)
    pairs = [(points[j - 1], points[j]) for j in range(0 if closed else 1, count)]
    return min(plan._point_segment(point, a, b)[0] for a, b in pairs)


def hit_line(source, collection, point, tolerance):
    """The index of the entry of `collection` whose line passes within `tolerance` of `point`, the nearest, or None."""
    best = None
    for i, entry in enumerate(source.get(collection, [])):
        d = _near_polyline(point, entry["points"])
        if d <= tolerance and (best is None or d < best[0]):
            best = (d, i)
    return None if best is None else best[1]


def _hit_shape(source, collection, shape_of, point, tolerance):
    """The index of the entry of `collection` whose shape `point` lies in, or within `tolerance` of whose outline it lies -- the smallest where several do."""
    hits = []
    for i, entry in enumerate(source.get(collection, [])):
        shape = shape_of(entry)
        if plan._inside(point, shape) or _near_polyline(point, shape, closed=True) <= tolerance:
            hits.append((ring_area(shape), i))
    return min(hits)[1] if hits else None


def hit(source, point, tolerance, band=0.0):
    """The id of what lies under `point`, what is drawn on top first: an escape route's width within `tolerance` of the line it measures, an emergency exit's arrow, an escape route within `tolerance` of its line, a door's shape, a wall -- within `tolerance`, or anywhere on its band --, else the surface there; None for nothing. `band` is band_width(frame), the band of a wall drawn at 100 %; each wall's own factors are applied here."""
    i = hit_line(source, "widths", point, tolerance)
    if i is not None:
        return source["widths"][i]["id"]
    i = _hit_shape(source, "exits", lambda entry: exit_shape(entry["points"]), point, tolerance)
    if i is not None:
        return source["exits"][i]["id"]
    i = hit_line(source, "routes", point, tolerance)
    if i is not None:
        return source["routes"][i]["id"]
    i = _hit_shape(source, "doors", door_shape, point, tolerance)
    if i is not None:
        return source["doors"][i]["id"]
    best = None
    for i, wall in enumerate(source.get("walls", [])):
        # `band` is the band of a wall drawn at 100 %: each wall's own is that times its factors
        reach = max(tolerance, band * factors(source, wall)["line"] / 2.0)
        d = _near_polyline(point, wall["points"])
        if d <= reach and (best is None or d < best[0]):
            best = (d, i)
    if best is not None:
        return source["walls"][best[1]]["id"]
    i = hit_zone(source, point)
    return None if i is None else source["zones"][i]["id"]


# --- The escape routes' three marks ----------------------------------------------------

def route_length_m(route, units_per_m):
    """An escape route's length in metres, along its line, or None without a scale."""
    return line_length(route["points"]) / units_per_m if units_per_m else None


def route_text(route, units_per_m):
    """What is written along an escape route: its own `text` where the engineer typed one, else its length -- «35 m», to a tenth of a metre, a whole number written without its decimal -- and nothing without a scale."""
    text = (route.get("text") or "").strip()
    if text:
        return text
    length = route_length_m(route, units_per_m)
    if length is None:
        return ""
    return f"{round(length, 1):g} m"


def width_m(entry, units_per_m):
    """What an escape route's width measures, in metres -- the distance between its two points --, or None without a scale."""
    return line_length(entry["points"]) / units_per_m if units_per_m else None


def width_text(entry, units_per_m):
    """What an escape route's width writes: its own `text` where the engineer typed one, else what it measures to the centimetre -- «1.20 m», «0.90 m», as the sheet and its sample plans write one -- and nothing without a scale."""
    text = (entry.get("text") or "").strip()
    if text:
        return text
    width = width_m(entry, units_per_m)
    return "" if width is None else f"{width:.2f} m"


def exit_shape(points):
    """The emergency exit's arrow from `points[0]`, its tail, to `points[1]`, its tip: the sheet's pictogram in its own proportions (norms/vkf.py), seven corners. The two points give it its place, its direction and its size at once."""
    a, b = points
    length, (ux, uy), (nx, ny) = _axis(a, b)
    shape = vkf.shape("exit")
    neck = shape["shaft_length"] * length
    half, wide = shape["shaft_width"] * length / 2.0, shape["head_width"] * length / 2.0
    mx, my = a[0] + ux * neck, a[1] + uy * neck
    return [
        (a[0] + nx * half, a[1] + ny * half), (mx + nx * half, my + ny * half), (mx + nx * wide, my + ny * wide),
        (b[0], b[1]),
        (mx - nx * wide, my - ny * wide), (mx - nx * half, my - ny * half), (a[0] - nx * half, a[1] - ny * half),
    ]


# --- The doors ---------------------------------------------------------------------------

def door_width_m(door, units_per_m):
    """A door's width in metres -- its leaf's, the distance between its two points --, or None without a scale."""
    return line_length(door["points"]) / units_per_m if units_per_m else None


def door_open_end(door):
    """Where the free end of a swing door's leaf stands when it is open at a right angle: a leaf's length from the hinge, on the side the door opens to."""
    a, b = door["points"]
    length, _u, (nx, ny) = _axis(a, b)
    side = door.get("side", 1)
    return (a[0] + nx * length * side, a[1] + ny * length * side)


def door_shape(door):
    """A door's shape, as the corners of a closed outline.

    A SWING door is the sheet's quarter disc: its centre on the hinge (`points[0]`), its radius the leaf's -- the leaf closed reaches `points[1]`, the other jamb --, swept a quarter turn to the side the door opens to (`side`): the hinge, the closed leaf's end, the arc, the open leaf's end. A SLIDING door is the sheet's flat arrow along the wall: a bar from `points[0]` to `points[1]`, the way the leaf slides to open, with half an arrowhead at `points[1]` rising on `side`.
    """
    a, b = door["points"]
    length, (ux, uy), (nx, ny) = _axis(a, b)
    side = door.get("side", 1)
    nx, ny = nx * side, ny * side
    if door.get("kind") == "slide":
        shape = vkf.shape("slide")
        head, height, bar = shape["head_length"] * length, shape["head_height"] * length, shape["bar"] * length
        hx, hy = b[0] - ux * head, b[1] - uy * head
        return [(b[0], b[1]), (hx + nx * height, hy + ny * height), (hx + nx * bar, hy + ny * bar), (a[0] + nx * bar, a[1] + ny * bar), (a[0], a[1])]
    arc = []
    for step in range(ARC_STEPS + 1):
        t = math.pi / 2.0 * step / ARC_STEPS
        c, s = math.cos(t) * length, math.sin(t) * length
        arc.append((a[0] + ux * c + nx * s, a[1] + uy * c + ny * s))
    return [(a[0], a[1])] + arc


def door_flipped(door, what):
    """`door` opening the other way, as a new entry: `what` "hinge" puts the hinge on the other jamb -- a sliding door then slides the other way -- and keeps the side of the wall it opens to; "side" keeps the hinge and opens it to the other side of the wall."""
    if what not in ("hinge", "side"):
        raise ValueError(f"door_flipped: {what!r} -- 'hinge' or 'side'")
    flipped = dict(door)
    # the side is counted from the line hinge -> jamb, so the line turned round turns the count round with it: the same side of the wall is then the other number
    flipped["side"] = -door.get("side", 1)
    if what == "hinge":
        flipped["points"] = [list(door["points"][1]), list(door["points"][0])]
    return flipped


# --- What is drawn where ---------------------------------------------------------------

def band_width(frame):
    """How wide a wall's band is drawn at 100 %, in sheet units: WALL_BAND_M where the frame has a scale, a few of the drawing's units where it has none. The plan's and the wall's own `line` factors multiply it (`factors`)."""
    units = per_m(frame)
    if units:
        return WALL_BAND_M * units
    return WALL_BAND_UNITS * drawing_unit(frame)


def label_point(zone):
    """Where a surface's name is written: its outline's area centroid, or the middle of its bounding box where that falls outside the surface (an L, a ring)."""
    c = plan.centroid(zone["points"])
    if inside(c, zone):
        return c
    x0, y0, x1, y1 = plan.bbox(zone["points"])
    # the widest run of the surface along the horizontal through the middle of its box: an L and a U both have one
    y = (y0 + y1) / 2.0
    xs = sorted(_crossings(zone["points"], y) + [x for hole in zone.get("holes", []) for x in _crossings(hole, y)])
    best = None
    for a, b in zip(xs[::2], xs[1::2]):
        if best is None or b - a > best[1] - best[0]:
            best = (a, b)
    return ((best[0] + best[1]) / 2.0, y) if best else c


def _crossings(ring, y):
    """Where the horizontal at `y` crosses an outline."""
    out = []
    for i in range(len(ring)):
        (x1, y1), (x2, y2) = ring[i - 1], ring[i]
        if (y1 > y) != (y2 > y):
            out.append(x1 + (x2 - x1) * (y - y1) / (y2 - y1))
    return out


# --- The legend ---------------------------------------------------------------------------

def legend_default(frame):
    """Where a legend just switched on stands, {"x", "y"}: its top left corner a little in from the crop's."""
    crop = plan.crop_of(frame)
    margin = LEGEND_MARGIN_UNITS * drawing_unit(frame)
    return {"x": round(crop["x"] + margin, DECIMALS), "y": round(crop["y"] + margin, DECIMALS)}


def legend_rows(source):
    """What the plan's legend lists: one row per symbol the plan actually draws, in the order of the AEAI's own sample legend -- the fire resistances of its walls in the sheet's order, the kinds of its surfaces, the emergency exit, the escape route's length and its width --, then its doors.

    A row is {"symbol", "kind", "class", "label", "rgb"}: `symbol` says what is drawn beside the text ("wall", "surface", "exit", "length", "width", "door"); `kind` the surface's or the door's; `class` the fire resistance, None for a door without one; `label` the sheet's German, which the glossary translates -- None for a door without a fire resistance, which is no symbol of the sheet: its words are the engine's own (calc/i18n/strings.json, `fire.door.<kind>`).
    """
    rows = []
    used = {wall.get("class") for wall in source.get("walls", [])}
    for row in vkf.resistances():
        if row["key"] in used:
            rows.append({"symbol": "wall", "kind": None, "class": row["key"], "label": row["label"], "rgb": row["rgb"]})
    kinds = {zone.get("kind") for zone in source.get("zones", [])}
    for kind in SURFACES:
        if kind in kinds:
            entry = vkf.escape(kind)
            rows.append({"symbol": "surface", "kind": kind, "class": None, "label": entry["label"], "rgb": entry["rgb"]})
    for symbol, collection in (("exit", "exits"), ("length", "routes"), ("width", "widths")):
        if source.get(collection):
            entry = vkf.escape(symbol)
            rows.append({"symbol": symbol, "kind": None, "class": None, "label": entry["label"], "rgb": entry["rgb"]})
    doors = {(door.get("kind"), door.get("class")) for door in source.get("doors", [])}
    for kind in DOOR_KINDS:
        for cls in vkf.door_classes():
            if (kind, cls) in doors:
                entry = vkf.door(kind, cls)
                rows.append({"symbol": "door", "kind": kind, "class": cls, "label": entry["label"], "rgb": entry["rgb"]})
    for kind in DOOR_KINDS:
        if (kind, None) in doors:
            rows.append({"symbol": "door", "kind": kind, "class": None, "label": None, "rgb": None})
    return rows


# --- Export ------------------------------------------------------------------------------

def empty():
    """The export of a project that has no fire-protection plan: what a new project is seeded with, so that `fire-plan-ids()` gives an empty array rather than stopping the compile on a missing file."""
    return {"schema_version": EXPORT_SCHEMA_VERSION, "plans": {}}


def _read_export(path, key):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8")).get(key, {})
    except (OSError, ValueError, AttributeError):
        return {}


def _metres(value):
    return None if value is None else round(value, 3) + 0.0


def build_record(source, frame, background=None):
    """One plan as it enters data/fire.json: the frame the report shows, the files under data/ it is drawn with -- its figure once per language, the legend carrying words --, its scale, and what it draws with what each measures. `frame` is frame_of()'s with the sheet as the background's file now gives it.

    A surface that states no kind is a draft and is not in the record: the report does not print it. A measure is absent where the plan has no scale -- never 0, which would read as a measure.
    """
    from domains import fire_svg  # the drawing module draws what this module describes

    fid = source["id"]
    crop = plan.crop_of(frame)
    units = per_m(frame)

    def entry(base, collection, item, **measures):
        record = dict(base)
        record.update({key: value for key, value in measures.items() if value is not None})
        own = figure_style.record(item)
        if own is not None:
            record["style"] = own
        if "opacity" in item:
            record["opacity"] = float(item["opacity"])
        return record

    zones = [entry({"id": zone["id"], "kind": zone["kind"], "label": zone.get("label", "")}, "zones", zone, area_m2=_metres(area_m2(zone, units)))
             for zone in source.get("zones", []) if zone.get("kind") in SURFACES]
    walls = [entry({"id": wall["id"], "class": wall["class"]}, "walls", wall, length_m=_metres(line_length(wall["points"]) / units if units else None))
             for wall in source.get("walls", [])]
    doors = [entry({"id": door["id"], "kind": door["kind"], **({"class": door["class"]} if "class" in door else {})}, "doors", door, width_m=_metres(door_width_m(door, units)))
             for door in source.get("doors", [])]
    routes = [entry({"id": route["id"], "text": route_text(route, units)}, "routes", route, length_m=_metres(route_length_m(route, units)))
              for route in source.get("routes", [])]
    exits = [entry({"id": item["id"]}, "exits", item) for item in source.get("exits", [])]
    widths = [entry({"id": item["id"], "text": width_text(item, units)}, "widths", item, width_m=_metres(width_m(item, units)))
              for item in source.get("widths", [])]
    record = {
        "name": source.get("name", ""),
        "label": source.get("label", ""),
        "source": f"fire/{fid}.json",
        "sheet": {"width": plan._clean(frame["sheet"]["width"]), "height": plan._clean(frame["sheet"]["height"])},
        "crop": {key: plan._clean(value) for key, value in crop.items()},
        "unit": plan._clean(drawing_unit(frame)),
        "style": {key: drawing_factors(source)[key] for key in STYLE_KEYS},
        "figures": {lang: f"fire/{fid}-{lang}.svg" for lang in strings.LANGUAGES},
        "legend": "legend" in source,
        "legend_lines": fire_svg.legend_lines(source),
        "zones": zones, "walls": walls, "doors": doors, "routes": routes, "exits": exits, "widths": widths,
    }
    if follows(source) is not None:
        record["plan"] = follows(source)
    if background is not None:
        record["background"] = background
    if units:
        record["scale"] = {"mode": frame["scale"]["mode"], "units_per_m": plan._clean(units)}
        if frame["scale"]["mode"] == "ratio":
            record["scale"]["ratio"] = frame["scale"]["ratio"]
    return record


def _followed_background(shown):
    """The background of a position plan's export record, as a plan that follows it sets it: where the file is, what it is and how visible, and -- for a plan drawn on a page of a document -- which document and how it was turned and what it hides."""
    background = {key: shown["background"][key] for key in ("file", "format", "page")}
    background["opacity"] = float(shown["background"].get("opacity", plan.DEFAULT_OPACITY))
    for key in ("document", "rotation", "layers_off"):
        if key in shown["background"]:
            background[key] = shown["background"][key]
    return background


def prepare(source_dir, plans_dir, project_root, data_dir, plans=None, values=None, place=None):
    """(data, files, warnings): data/fire.json as it will be written, every figure it refers to (its name in the JSON -> bytes or text, `place` an engine.Figures: the tab's Exports/Figures/ in a project laid out by folders, data/fire/ otherwise), and the warnings to print -- built and validated from every source file, nothing written yet, so export_all.py can check the fire-protection plans along with everything else before it writes anything.

    A plan with a frame of its own is drawn on its file, or on a page of an imported document -- the page flattened with the layers the engineer switched off taken out, turned as he turned it (plan.document_background, the position plans' own step) -- and its background is written under data/fire/ (`fire/<id>-plan.<format>`). `plans_dir` is where the documents live under (plans/documents/).

    `plans` is the position plans' own export, `data/plans.json`'s `plans`, as export_all.py has just built it; read off the disk where it is not given, which is what a save in Woodcore's window does. A plan that FOLLOWS a position plan is set over that plan's exported background -- the page is then in data/ once, however many floors are drawn on it -- and one whose position plan is not exported yet is drawn without a background, and says so. A plan whose position plan is gone is not exported at all: nothing says what it would be drawn over.
    """
    from domains import fire_svg  # the drawing module draws what this module describes

    data_dir = Path(data_dir)
    place = place or engine.figures(data_dir, "fire")
    previous = _read_export(data_dir / EXPORT_FILE, "plans")
    exported = plans if plans is not None else _read_export(data_dir / "plans.json", "plans")
    frames = plan_frames(plans_dir)
    records, files, notes = {}, {}, []
    for path in source_paths(source_dir):
        source = read_source(path)
        fid = source["id"]
        where = f"fire/{fid}.json"
        frame, problem = frame_of(source, frames)
        if problem is not None:
            notes.append(problem)
            continue
        notes += warnings(source, frames)
        sheet = (float(frame["sheet"]["width"]), float(frame["sheet"]["height"]))
        background = None
        pid = follows(source)
        if pid is not None:
            shown = exported.get(pid)
            if shown is None:
                notes.append(engine.Note("fire_plan_unexported", f"fire-protection plan {fid}: the position plan {pid} it follows is not in the export yet -- save it in Woodcore, or run the import; until then the report draws the plan without its background", fire=fid, plan=pid))
            else:
                sheet = (float(shown["sheet"]["width"]), float(shown["sheet"]["height"]))
                if "background" in shown:
                    background = _followed_background(shown)
        elif frame.get("background") is not None:
            spec = frame["background"]
            old = previous.get(fid, {}).get("background", {})
            what = f"fire-protection plan {fid}"
            document = plan.document_background(spec, project_root, plans_dir, place, place.name(f"{fid}-plan"), old, where, what, files, notes, plan=fid) if spec.get("document") else None
            if document is not None:
                background, actual = document
                if abs(actual[0] - sheet[0]) > 0.5 or abs(actual[1] - sheet[1]) > 0.5:
                    notes.append(engine.Note("fire_sheet_moved", f"{what}: page {spec['page']} of document {spec['document']} is now {actual[0]:.0f} × {actual[1]:.0f} and not {sheet[0]:.0f} × {sheet[1]:.0f} as when it was drawn on -- open the plan in Woodcore and check its symbols", fire=fid, document=spec["document"], page=spec["page"]))
                    sheet = actual
            else:
                background, sheet, more = plan.file_background(spec, sheet, project_root, place, place.name(f"{fid}-plan"), old, where, what, files)
                notes += more
        drawn = {**frame, "sheet": {"width": sheet[0], "height": sheet[1]}}
        record = build_record(source, drawn, background)
        record["figures"] = {lang: place.name(f"{fid}-{lang}.svg") for lang in strings.LANGUAGES}
        texts = plan.text_records(source, values, f"fire-protection plan {fid}", notes)
        if texts:
            record["texts"] = texts
        for lang in strings.LANGUAGES:
            files[record["figures"][lang]] = fire_svg.render(source, drawn, editing=False, lang=lang, values=values)
        records[fid] = record
    version = TEXT_EXPORT_VERSION if any("texts" in r for r in records.values()) else EXPORT_SCHEMA_VERSION
    data = {"schema_version": ROOTED_EXPORT_VERSION if place.here is not None else version, "plans": records}
    validation.validate_structure(data, "fire")
    validation.validate_fire_business(data)
    return data, files, notes


def write(data, files, data_dir):
    """Writes data/fire.json and the plans' figures and backgrounds -- into the tab's Exports/Figures/ in a project laid out by folders, data/fire/ otherwise (engine.Figures) --, and removes those of a plan that no longer exists: only what the last export wrote, never a file of the engineer's. A file whose content has not changed is left alone."""
    data_dir = Path(data_dir)
    engine.figures(data_dir, "fire").write(files, engine.previous_json(data_dir / EXPORT_FILE))
    engine.write_json(data_dir / EXPORT_FILE, data)


def export(source_dir, plans_dir, project_root, data_dir, values=None):
    """The fire-protection plans' part of the export, on its own: what Woodcore's window runs when a plan is saved, so the report sees it without the whole export being run again. export_all.py runs the same two steps, handing over the position plans it has just built. `values` are the export's, which a text's variables print (issue #43). Returns the warnings."""
    data, files, notes = prepare(source_dir, plans_dir, project_root, data_dir, values=values)
    write(data, files, data_dir)
    return notes


# --- What does not stop anything ------------------------------------------------------

def warnings(source, frames, where=None):
    """What should be looked at, as Notes: the position plan the plan follows is gone, the frame has no scale, a crop of its own leaves the sheet of the position plan it follows, a surface lies outside the frame."""
    fid = source.get("id") or "?"
    where = where or f"fire-protection plan {fid}"
    out = []
    frame, problem = frame_of(source, frames)
    if problem is not None:
        out.append(problem)
        return out
    if not per_m(frame):
        out.append(engine.Note("fire_no_scale", f"{where}: the plan has no scale -- no area, length or width on it is measured", fire=fid))
    crop = plan.crop_of(frame)
    sheet = frame["sheet"]
    if follows(source) is not None and "crop" in source and (
            crop["x"] < -1e-6 or crop["y"] < -1e-6 or crop["x"] + crop["w"] > sheet["width"] + 1e-6 or crop["y"] + crop["h"] > sheet["height"] + 1e-6):
        out.append(engine.Note("fire_crop_outside", f"{where}: its own crop leaves the sheet of the position plan {follows(source)} it follows -- draw it again, or take the position plan's", fire=fid, plan=follows(source)))
    for zone in source.get("zones", []):
        x0, y0, x1, y1 = plan.bbox(zone["points"])
        if x1 < crop["x"] or y1 < crop["y"] or x0 > crop["x"] + crop["w"] or y0 > crop["y"] + crop["h"]:
            out.append(engine.Note("fire_zone_outside", f"{where}: surface {zone['id']} lies outside the plan's frame", fire=fid, zone=zone["id"]))
    return out


def references(record):
    """What an exported fire plan names, [(kind, id, field)]: the position plan it follows (domains/dependency_graph.py, spec 2026-10-21-graphe-dependances, ARCH-RISK-1103)."""
    return [("plan", record["plan"], "plan")] if record.get("plan") else []
