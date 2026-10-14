"""Connections (Anschlüsse): a fastener group's geometry and its polar moment of inertia, from the definition Woodcore saves (docs/domain/connections.md §3.3quinquies).

A connection is not read from a workbook. Its definition -- which detail schema it is drawn on, which of that schema's markers carry its fasteners, which of its elements are the members, the rotation centre, the directions of N and V -- is entered in Woodcore's «Moments polaires» tab and saved as one source file per connection, `connections/<id>.json` beside calc/. That file plays the part a load's sheet plays: Woodcore is the only thing that writes it, and this module the only thing that reads it.

⚠️ **Since v0.74 a connection carries no geometry of its own.** It names a schema (`details/<id>.json`, section 3.3decies) and reads the pieces and the coordinates off it, so that one physical joint is drawn once and not twice -- the duplication section 2 rule 1 forbids everywhere else, and which the member form and the x/z table here were. The frame is unchanged by the move and needed no conversion, a schema being written in the connections' own: millimetres, x to the right, z down, angles from x towards z. What the reference member used to fix -- the direction of x -- the schema fixes now, which is why `orientation` is gone and why a member's angle is kept twice over in the record: `axis`, its grain from the schema's x, which is what a force-grain angle is measured against, and `local`, its grain from the reference member's, which is what theta_(r,j) prints. Until v0.73 the two were the same number by construction; they part company as soon as a detail is drawn at an angle.

⚠️ **Since v0.76 a connection names no connector.** A polar moment distributes forces over points and has no use for what fastens them, so the link v0.33 made -- the id composed as `<connector>-<variant>`, the connector printed under the report's heading, a calculation of no listed connector refused -- is gone. A connection has a **name**, and its id is that name made safe as a file name (`id_from_name`), writable over. A 3.0 or 3.1 file is read as 4.0: its `connector` and `variant` are dropped, its name is the one it states or else its id, and its id is kept as it is.

What is calculated here is the geometry, and only the geometry: the rotation centre (the fasteners' centroid, a point the engineer fixed, or a centre drawn in the schema), the distances to it, and I_p,x = Σ Δx_i², I_p,z = Σ Δz_i², I_p = I_p,x + I_p,z -- in mm², the discrete counterpart of a polar moment of inertia, every fastener counting as one unit point. The connection enters data/connections.json as the ordinary {vars, steps, checks, tables, results} record (section 2, rule 2), so `show-calc("connection", id)` and `var-of("connection", id, "I_p")` read it like any other calculation.

The forces in the fasteners are *not* calculated here. N, V and M are written in the report, `show-polar-moment(id, N:, V:, M:)`, until load combinations export them, so lib/calc-engine.typ distributes them (section 13). `fastener_forces()` below is the same formula once more, for Woodcore's preview only -- nothing it returns is saved -- and the two are checked against each other.

Conventions, all stated in section 3.3quinquies. Coordinates in mm, **the schema's own**: the origin where the schema puts it, x to the right, z down. Angles -- of N, of V, of a member's grain -- are counted from x towards z, clockwise on the drawing. M is positive the other way, turning z towards x (M_y of a right-handed frame), which is anticlockwise on the drawing.
"""

import copy
import json
import math
import re
import unicodedata
from pathlib import Path

import engine
import validation
from domains import schema as schema_model  # a connection is drawn on one: its ids, its geometry and its accessors
from domains import links  # a field that follows a variable of the export (spec 2026-10-11-variables-liees-champs-et-textes)
from i18n import strings

DOMAIN = "connection"
LABEL = "Verbindungen"
ENGINE = "python"
SOURCE = "python:domains/connection.py"

# Of a source file (connections/<id>.json) and of the export (data/connections.json). 2.0: the x/z frame of a reference member, and any number of members. 2.1: the connector the calculation belongs to. 3.0: the geometry is a schema's, named here. 3.1 (v0.75): a `name` and a `variant`, the two halves the id was composed of. 4.0 (v0.76): no `connector` and no `variant` -- a name, and the id made from it; the export's record loses its `connector` with it.
SOURCE_SCHEMA_VERSION = "4.0"
# Read as 4.0 by upgrade_source, which only drops two fields and fills a name -- nothing to write, so nothing is written.
UPGRADED_SOURCE_VERSIONS = ("3.0", "3.1")
# 4.1 is 4.0 with `links` (spec 2026-10-11-variables-liees-champs-et-textes, D-17): written only by a source that carries one, so a calculation following no variable is saved and exported as before
LINKED_SCHEMA_VERSION = "4.1"
EXPORT_SCHEMA_VERSION = "4.1"
LINKED_EXPORT_VERSION = "4.2"

# The fields a variable of the export may fill (REQ-009, issue #42): a rotation centre placed by hand, the two directions, and the trial forces the «Calcul» view starts from -- data of the calculation since that issue (D-12), `trial` being optional and additive.
LINKABLE = {links.SELF: {"center.x": "mm", "center.z": "mm", "directions.N": "°", "directions.V": "°",
                         "trial.N": "kN", "trial.V": "kN", "trial.M": "kNm"}}
TRIAL_KEYS = ("N", "V", "M")
# The file data/connections.json is written to -- named once, for this module and the Variables tab's reader (calc/variable_sources.py).
EXPORT_FILE = "connections.json"

# What calc/tools/migrate_to_schemas.py converts, and this module deliberately does not: a source at one of these carries its own drawing, and turning that drawing into a schema means writing a second file, which a reader has no business doing silently.
LEGACY_SOURCE_VERSIONS = ("1.0", "2.0", "2.1")

# What a new connection cites until the engineer says otherwise: a document rather than a norm clause, so it has no clause and is printed without one.
DEFAULT_NORM = "bauforumstahl, Arbeitshilfe: Tragwerksplanung im Stahlbau – Gelenkige Anschlüsse"

# A connection id is the file name of its source and the string the report addresses it by, so it is kept to characters that are safe in both.
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$")

# The rotation centre: the fasteners' centroid, which is what the elastic method assumes for fasteners of equal stiffness; a point the engineer fixes when the connection does not turn about its centroid; or a centre drawn in the schema, which is what the schema's own «Centre» tool is for (v0.74).
CENTER_MODES = ("centroid", "manual", "aid")

# How many members may meet at the node: two for a beam on a beam, up to six for a truss node.
MIN_MEMBERS, MAX_MEMBERS = 2, 6

# Two fasteners closer than this (mm) are taken as one point typed twice.
SAME_POINT = 1e-6

# Fasteners whose resultants differ by less than this, relatively, carry the same force: rounding noise, not a governing difference.
TIE_TOLERANCE = 1e-9


def _fail(where, message):
    raise validation.ValidationError(f"{where}: {message}")


def _number(value, where, what, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        _fail(where, f"{what} must be a number, got {value!r}")
    if positive and value <= 0:
        _fail(where, f"{what} must be greater than 0, got {value!r}")
    return value


def _index(value, count, where, what):
    """A member's number, 1-based, as the form and the file give it."""
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= count:
        _fail(where, f"{what} is {value!r} -- expected a member number from 1 to {count}")
    return value


def _clean(value):
    """A converted number as it is saved: -0 is 0, a whole float an int."""
    value = round(float(value), 6) + 0.0
    return int(value) if value.is_integer() else value


def normalize_angle(degrees):
    """An angle in degrees, brought into (-180, 180]."""
    a = math.fmod(degrees, 360.0)
    if a <= -180:
        a += 360
    elif a > 180:
        a -= 360
    return a


# --- The source file ------------------------------------------------------------

def id_from_name(name):
    """The id a calculation's name gives it (v0.76): `Nord Anschluss` -> `Nord_Anschluss`, `Élément 2` -> `Element_2`.

    An id is the file's name and the string the report addresses the calculation by, so it is kept to what `ID_PATTERN` allows -- letters, digits and `_ . + -`, opening on a letter or a digit. It is the connectors' own rule (`connectors_tab.slug_id`) with no variant after it, and it gives the same answer for the same name whoever typed it: an accent is **decomposed** (NFKD) rather than dropped, a space becomes `_`, and a letter that cannot be decomposed -- a ß, a Cyrillic name -- is dropped, the ID field staying writable for exactly those cases.
    """
    out = []
    for char in unicodedata.normalize("NFKD", (name or "").strip()):
        if unicodedata.combining(char):
            continue                           # the accent NFKD split off
        if (char.isalnum() and char.isascii()) or char in "_.+-":
            out.append(char)
        elif char.isspace():
            out.append("_")
    made = "".join(out).strip("_")
    while made and not (made[0].isalnum() and made[0].isascii()):
        made = made[1:]
    return made


def new_source(cid, schema=""):
    """A blank connection, as Woodcore opens one: named after its id, two members naming nothing yet, no fastener, turning about its centroid."""
    return {
        "schema_version": SOURCE_SCHEMA_VERSION,
        "id": cid,
        "group": "",
        "name": cid,
        "label": "",
        "norm": DEFAULT_NORM,
        "norm_ref": "",
        "schema": schema,
        "reference": 1,
        "members": [{"name": "", "element": ""} for _ in range(MIN_MEMBERS)],
        "fasteners": [],
        "center": {"mode": "centroid"},
        "directions": {"N": 0, "V": 90},
    }


def upgrade_source(source):
    """A source as schema 4.0 describes it.

    A 3.0 or 3.1 file is converted here, as it is read, because nothing has to be written for it: its `connector` and its `variant` are dropped (v0.76, a polar moment names no connector), its `name` is the one it states or else its **id**, and its id is kept as it is. So `SD_01-8mm`, saved as a calculation of SD_01, is still `SD_01-8mm`, named `SD_01-8mm`; a 3.1 file named `SD_01` with the variant `8mm` keeps `SD_01-8mm` as its id, which Woodcore then reads as written over.

    ⚠️ A 1.0, 2.0 or 2.1 file carries **its own drawing**: the members with their sections and angles, and a table of fastener coordinates. Turning one into a 3.0 file means writing a second file, the schema that drawing becomes, and a reader must not do that quietly -- it would put a `details/<id>.json` on disk that nobody asked for, and do it again differently the next time the same file was read. `calc/tools/migrate_to_schemas.py` is the one thing that converts them, once and deliberately, and `check_source` refuses anything it has not been through, naming it.
    """
    if not isinstance(source, dict) or source.get("schema_version") not in UPGRADED_SOURCE_VERSIONS:
        return source
    stated = source.get("name")
    name = stated.strip() if isinstance(stated, str) and stated.strip() else source.get("id", "")
    upgraded = {}
    for key, value in source.items():
        if key in ("connector", "variant", "name"):
            continue
        upgraded[key] = SOURCE_SCHEMA_VERSION if key == "schema_version" else value
        if key == "id":
            upgraded["name"] = name
    upgraded.setdefault("name", name)
    return upgraded


def check_source(source, where):
    """Everything a source file must satisfy before it is calculated with -- its structure against schemas/connection-source.schema.json, then the rules a schema cannot state. Every failure is a blocking error naming the file and the field (docs/architecture/data-contracts.md §3.6).

    ⚠️ What it does **not** check is whether the schema, its markers and its elements exist: that is the export's question, as it is for a connector. A connection drawn on a schema that has been renamed must stay openable in Woodcore so it can be pointed at another one, so those are warnings (`prepare`) and the report refuses to print what they name (`lib/calc-engine.typ`).
    """
    version = source.get("schema_version") if isinstance(source, dict) else None
    if version in LEGACY_SOURCE_VERSIONS:
        _fail(where, f"schema_version is {version!r} -- it carries its own drawing; run `python calc/tools/migrate_to_schemas.py --write` once, which writes that drawing out as a schema under details/ and leaves this file naming it")
    if version in UPGRADED_SOURCE_VERSIONS:
        _fail(where, f"schema_version is {version!r} -- read it through connection.upgrade_source(), which makes it {SOURCE_SCHEMA_VERSION}")
    if version not in (None, SOURCE_SCHEMA_VERSION, LINKED_SCHEMA_VERSION):
        _fail(where, f"schema_version is {version!r} -- expected {SOURCE_SCHEMA_VERSION!r} or {LINKED_SCHEMA_VERSION!r}")
    if isinstance(source, dict) and links.is_linked(source, LINKABLE) and version != LINKED_SCHEMA_VERSION:
        _fail(where, f"follows a variable at schema_version {version!r} -- a calculation with links is {LINKED_SCHEMA_VERSION!r}")
    try:
        validation.validate_structure(source, "connection-source")
    except validation.ValidationError as exc:
        _fail(where, str(exc))

    if not ID_PATTERN.match(source["id"]):
        _fail(where, f"id {source['id']!r} -- use letters, digits and _ . + - only, starting with a letter or a digit")
    # ⚠️ Since 4.0 (v0.76) a connection names no connector, and has no variant: a field left over would be read by nothing and believed by whoever opens the file.
    for key in ("connector", "variant"):
        if key in source:
            _fail(where, f"carries a {key!r} -- a polar-moment calculation names no connector and no variant since schema 4.0; its id is made from its name")
    # The name is free text -- the id is what must be safe, and the id may be written over.
    if not isinstance(source["name"], str):
        _fail(where, f"name must be text, got {source['name']!r}")
    # Every calculation cites what it follows (engine.py). A document is cited whole, so the clause may be left empty; the reference itself may not.
    if not source["norm"].strip():
        _fail(where, "norm is empty -- a connection cites the reference its calculation follows")
    if source["schema"] and not ID_PATTERN.match(source["schema"]):
        _fail(where, f"schema {source['schema']!r} is not a schema id")

    members = source["members"]
    if not MIN_MEMBERS <= len(members) <= MAX_MEMBERS:
        _fail(where, f"has {len(members)} members -- a connection joins {MIN_MEMBERS} to {MAX_MEMBERS}")
    for i, member in enumerate(members, start=1):
        if not isinstance(member.get("name"), str):
            _fail(where, f"member {i}: name must be text")
        element = member.get("element")
        if not isinstance(element, str):
            _fail(where, f"member {i}: element must be the id of a schema element")
        if element and not schema_model.ENTITY_ID.match(element):
            _fail(where, f"member {i}: element {element!r} is not an element id")
    _index(source["reference"], len(members), where, "reference")

    seen = []
    for i, marker in enumerate(source["fasteners"], start=1):
        if not isinstance(marker, str) or not marker:
            _fail(where, f"fastener {i} is {marker!r} -- expected the id of a connector marker or a construction point of the schema")
        if not schema_model.ENTITY_ID.match(marker):
            _fail(where, f"fastener {i}: {marker!r} is not a marker id")
        if marker in seen:
            _fail(where, f"fastener {i}: marker {marker} is named twice")
        seen.append(marker)

    center = source["center"]
    if center["mode"] not in CENTER_MODES:
        _fail(where, f"center.mode is {center['mode']!r} -- expected one of {', '.join(CENTER_MODES)}")
    if center["mode"] == "manual":
        for key in ("x", "z"):
            if key not in center:
                _fail(where, f"a manual rotation centre needs its {key}")
            _number(center[key], where, f"center.{key}")
    if center["mode"] == "aid":
        aid = center.get("aid")
        if not isinstance(aid, str) or not aid or not schema_model.ENTITY_ID.match(aid):
            _fail(where, f"center.aid is {aid!r} -- expected the id of a point-shaped aid of the schema")
    for key in ("N", "V"):
        _number(source["directions"][key], where, f"directions.{key}")
    # the trial forces of the «Calcul» view (D-12): absent, or a number each, kN and kNm
    trial = source.get("trial")
    if trial is not None:
        if not isinstance(trial, dict) or set(trial) - set(TRIAL_KEYS):
            _fail(where, f"trial is {trial!r} -- the trial forces {{N, V, M}}, in kN and kNm")
        for key, value in trial.items():
            _number(value, where, f"trial.{key}")
    links.check_all(source, LINKABLE, lambda message: _fail(where, message), "the calculation", links.JOINTS)


def read_source(path):
    """One connection's source file, checked. Its id must be its file name: the file is how Woodcore finds a connection, the id how the report does, and the two must not disagree."""
    path = Path(path)
    try:
        source = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _fail(path.name, f"not readable as JSON -- {exc}")
    source = upgrade_source(source)
    check_source(source, path.name)
    if source["id"] != path.stem:
        _fail(path.name, f"id is {source['id']!r} but the file is named {path.name} -- they must agree")
    return source


# --- Geometry -----------------------------------------------------------------
# Tolerant of a draft: Woodcore calls these on every keystroke, with a form that may not be complete yet,
# and with a schema whose markers and elements it may be in the middle of renaming.

def fastener_places(detail):
    """{id: (x, z)} of everything in a schema a polar moment may take as a fastener: its connector markers, then the construction points ticked «connecteur» -- `schema.fastener_places`, the one list every module reads (v0.77). A polar moment distributes forces over points and has no use for what kind of fastener sits on one (section 3.3decies)."""
    return schema_model.fastener_places(detail)


def fastener_points(source, detail):
    """The connection's fasteners as (x, z), read off the schema's markers and construction points in the order the source names them. One the schema no longer carries is skipped -- `missing_markers` is what names it."""
    places = fastener_places(detail)
    return [places[fid] for fid in source.get("fasteners", []) or [] if fid in places]


def missing_markers(source, detail):
    """The fastener ids the source names and the schema carries neither as a marker nor as a point."""
    places = fastener_places(detail)
    return [fid for fid in source.get("fasteners", []) or [] if fid not in places]


def member_elements(source):
    """The element id each member names, in member order; "" for one that names none yet."""
    return [m.get("element", "") or "" for m in source.get("members", [])]


def missing_elements(source, detail):
    """The element ids the members name and the schema does not carry, in order and without repeats. An empty name is not one of them: a member that names nothing yet is a draft, not a broken reference."""
    known = {e.get("id") for e in (detail or {}).get("elements", [])}
    missing = []
    for eid in member_elements(source):
        if eid and eid not in known and eid not in missing:
            missing.append(eid)
    return missing


def centroid(points):
    if not points:
        return None
    n = len(points)
    return (sum(x for x, _ in points) / n, sum(z for _, z in points) / n)


def polar_moments(points, center):
    """(I_p,x, I_p,z) in mm²: Σ Δx_i² and Σ Δz_i², the distances measured from `center` -- the convention of the engineer's own Verbindungen workbook, where I_p,x sums the x distances."""
    xc, zc = center
    return (sum((x - xc) ** 2 for x, _ in points), sum((z - zc) ** 2 for _, z in points))


def _member_index(value, count, default):
    return value - 1 if isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= count else default


def reference_index(source):
    return _member_index(source.get("reference", 1), len(source.get("members", [])), 0)


def axis_angles(source, detail):
    """Each member's grain direction **from the schema's x**, in degrees (x→z); 0 where its element cannot be found or has no length.

    This is what a force-grain angle is measured against, the force's own components being in the schema's frame. Until v0.73 it was the same number as `local_angles` below, the reference member's grain being x by construction; a schema draws the detail as it was drawn, so the two part company as soon as a piece is not horizontal.
    """
    angles = []
    for eid in member_elements(source):
        element = schema_model.entry_of(detail or {}, "elements", eid) if eid else None
        direction = schema_model.element_direction(element) if element else None
        angles.append(0.0 if direction is None else normalize_angle(math.degrees(math.atan2(direction[1], direction[0]))))
    return angles


def local_angles(source, detail):
    """Each member's grain from the **reference member's**, in degrees within (-180, 180] -- theta_(r,j), which is what the report prints as the angle between two members."""
    angles = axis_angles(source, detail)
    if not angles:
        return []
    r = reference_index(source)
    base = angles[r] if r < len(angles) else 0.0
    return [normalize_angle(a - base) for a in angles]


def rotation_centre(source, detail, points):
    """(the centre actually used, what is wrong with it or None): the fasteners' centroid, a point the engineer fixed, or a centre drawn in the schema. A named aid the schema does not carry, or one that is not point-shaped, falls back to the centroid and says so, rather than putting the connection's whole calculation out of reach over one renamed point."""
    gravity = centroid(points)
    mode = (source.get("center") or {}).get("mode", "centroid")
    if mode == "manual":
        centre = source["center"]
        return (centre.get("x", 0), centre.get("z", 0)), None
    if mode == "aid":
        aid = (source.get("center") or {}).get("aid", "")
        at = schema_model.named_point(detail or {}, aid) if aid else None
        if at is None:
            return gravity, aid
        return at, None
    return gravity, None


def analyse(source, detail=None):
    """The connection's geometry as numbers, for the report record, the figure and Woodcore's preview alike: {points, n, centroid, center, I_px, I_pz, I_p, r_max, axis, local, elements, reference, missing}.

    `detail` is the schema source the connection is drawn on (docs/domain/detail-schemas.md §3.3decies); None -- a schema renamed, or a draft naming none yet -- gives an empty group rather than an exception, since Woodcore lays a draft out on every keystroke.

    `center` is the rotation centre actually used, `axis` the members' grain from the schema's x, `local` their grain from the reference member's, `elements` the element each member names, `reference` the reference member's 0-based index, and `missing` what the schema does not carry: `{"markers": [...], "elements": [...], "centre": id or None}`.
    """
    points = fastener_points(source, detail)
    center, lost_centre = rotation_centre(source, detail, points)
    gravity = centroid(points)
    if center is None or not points:
        ipx = ipz = r_max = 0.0
    else:
        ipx, ipz = polar_moments(points, center)
        r_max = max(math.hypot(x - center[0], z - center[1]) for x, z in points)
    return {
        "points": points,
        "n": len(points),
        "centroid": gravity,
        "center": center,
        "I_px": ipx,
        "I_pz": ipz,
        "I_p": ipx + ipz,
        "r_max": r_max,
        "axis": axis_angles(source, detail),
        "local": local_angles(source, detail),
        "elements": member_elements(source),
        "reference": reference_index(source),
        "missing": {
            "markers": missing_markers(source, detail),
            "elements": missing_elements(source, detail),
            "centre": lost_centre,
        },
    }


def fastener_forces(geometry, directions, N, V, M):
    """The force in every fastener, for Woodcore's preview -- the same distribution lib/calc-engine.typ's show-polar-moment prints, and checked against it (docs/domain/connections.md §3.3quinquies): N and V shared equally, M in proportion to the distance to the rotation centre and at right angles to it.

    N, V in kN along the angles `directions` gives them (degrees from x towards z), M in kNm about the rotation centre, positive turning z towards x. Returns ([{nr, dx, dz, fx, fz, f}, ...], governing), `governing` being the 0-based indices of every fastener carrying the largest resultant, smallest first -- the calculation is shown for the first. A moment on a group with no lever arm at all (I_p = 0) cannot be taken and raises ValueError.
    """
    n, ip = geometry["n"], geometry["I_p"]
    if n == 0:
        return [], []
    if M != 0 and ip <= 0:
        raise ValueError("I_p = 0: the fasteners have no lever arm about the rotation centre, so the connection cannot take a moment")
    a_n, a_v = math.radians(directions["N"]), math.radians(directions["V"])
    nx, nz = N * math.cos(a_n), N * math.sin(a_n)
    vx, vz = V * math.cos(a_v), V * math.sin(a_v)
    m = M * 1000.0  # kNm -> kN·mm, so that M·r/I_p comes out in kN
    xc, zc = geometry["center"]
    rows = []
    for i, (x, z) in enumerate(geometry["points"], start=1):
        dx, dz = x - xc, z - zc
        fx = (nx + vx) / n + (m * dz / ip if ip > 0 else 0.0)
        fz = (nz + vz) / n - (m * dx / ip if ip > 0 else 0.0)
        rows.append({"nr": i, "dx": dx, "dz": dz, "fx": fx, "fz": fz, "f": math.hypot(fx, fz)})
    f_max = max(r["f"] for r in rows)
    tolerance = TIE_TOLERANCE * max(1.0, f_max)
    governing = [i for i, r in enumerate(rows) if r["f"] >= f_max - tolerance]
    return rows, governing


def force_line(fx, fz):
    """The direction a force acts in, in degrees from x towards z within (-180, 180]; None for no force at all."""
    if fx == 0 and fz == 0:
        return None
    return math.degrees(math.atan2(fz, fx))


def grain_angle(line_deg, member_deg):
    """The angle between a force's line and a member's grain (Kraft-Faser-Winkel), folded into 0-90° -- a line and a grain have no sense. For the reference member (at 0°) it is arctan(|F_z| / |F_x|)."""
    if line_deg is None:
        return None
    b = math.fmod(abs(line_deg - member_deg), 180.0)
    return 180.0 - b if b > 90 else b


def number_ranges(numbers):
    """Fastener numbers as the report writes them: runs of consecutive numbers as "1–4", the rest one by one -- "1, 3, 13, 15"."""
    numbers = sorted(numbers)
    parts, i = [], 0
    while i < len(numbers):
        j = i
        while j + 1 < len(numbers) and numbers[j + 1] == numbers[j] + 1:
            j += 1
        parts.append(str(numbers[i]) if j == i else f"{numbers[i]}–{numbers[j]}")
        i = j + 1
    return ", ".join(parts)


# --- The report record ----------------------------------------------------------

def _table(geometry):
    """The fasteners' positions, for the checking report, with the sums I_p is made of (docs/domain/loads.md §3.3ter's pattern): its totals row names I_p,x and I_p,z, so they are printed there and not on rows of their own, and no Σ formula restates in letters what the rows list."""
    # No centre where no fastener is ticked or the schema is gone -- build_record's own fallback, so such a calculation is exported with its warning rather than stopping every connection's export (v0.77; it raised a TypeError here).
    xc, zc = geometry["center"] if geometry["center"] is not None else (0.0, 0.0)

    def column(label, kind, unit=""):
        return {"label": label, "kind": kind, "unit": unit}

    rows = []
    for i, (x, z) in enumerate(geometry["points"], start=1):
        dx, dz = x - xc, z - zc
        rows.append([i, x, z, dx, dz, dx * dx, dz * dz])
    return {
        "title": "Lage der Verbindungsmittel",
        "source": SOURCE,
        # The schema's frame since v0.74, and no longer the reference member's grain from the node (v0.76 corrected the note).
        "note": "x, z: Koordinaten im Rahmen des Schemas, x nach rechts, z nach unten; Δx, Δz: Abstände zum Drehpunkt.",
        "columns": [
            column("Nr.", "number"),
            column("x", "number", "mm"),
            column("z", "number", "mm"),
            column("Δx", "number", "mm"),
            column("Δz", "number", "mm"),
            column("Δx²", "value", "mm²"),
            column("Δz²", "value", "mm²"),
        ],
        "rows": rows,
        "totals": [["Σ", "", "", "", "", "I_px", "I_pz"]],
    }


def _member_record(member, index, geometry, detail):
    """One member as the report reads it. Its *section* is gone from the record with the member form: the pieces are the schema's, so `show-polar-moment` names a member and does not restate its b/h.

    Two angles, and they are not the same thing: `local` is the grain from the reference member's, which is what theta_(r,j) prints, and `axis` the grain from the schema's x, which is what a force-grain angle is measured against. Until v0.73 the two were one number by construction, the reference member's grain BEING x; a detail drawn at an angle parts them.
    """
    eid = member.get("element", "")
    element = schema_model.entry_of(detail or {}, "elements", eid) if eid else None
    return {
        "name": member.get("name", ""),
        "element": eid,
        "position": (element or {}).get("position", "") if element else "",
        "local": _clean(geometry["local"][index]),
        "axis": _clean(geometry["axis"][index]),
    }


def member_label(member, index, detail=None):
    """What the report calls a member: its name, else the position its element names, else its number.

    `detail` is the schema, for a **source** member, which carries only a name and an element id; an
    exported member record already carries its `position`, so it needs none.
    """
    position = member.get("position") or (schema_model.entry_of(detail or {}, "elements", member.get("element", "")) or {}).get("position", "")
    return member.get("name", "").strip() or (position or "").strip() or f"Element {index + 1}"


def build_record(source, detail=None, figure=None, positions=None):
    """One connection as it enters data/connections.json: the schema it is drawn on, its members and fasteners as the report draws and distributes forces with them, the figure's placement data, and the {vars, steps, checks, tables, results} record of its polar moment. `source` must have passed check_source(); `detail` is the schema source; `figure` is connection_svg.meta() of its layout, computed here when not given.

    Which values the report prints at which level, and in which order, is show-polar-moment's layout; the vars' levels serve show-calc("connection", id), which prints the record on its own.
    """
    cid = source["id"]
    geometry = analyse(source, detail)
    xc, zc = geometry["center"] if geometry["center"] is not None else (0.0, 0.0)
    r = geometry["reference"]
    norm, norm_ref = source["norm"].strip(), source["norm_ref"].strip()
    # A centre the schema no longer carries was replaced by the centroid (analyse): the record and the label say so rather than «festgelegt» over a centroid (periodic audit 260916).
    mode = "centroid" if geometry["missing"]["centre"] else source["center"]["mode"]
    manual = mode in ("manual", "aid")
    if figure is None:
        from domains import connection_svg  # the figure module draws what this module computes
        figure = connection_svg.meta(connection_svg.layout(source, geometry, detail, positions))

    calc = engine.Calculation()

    def add(name, value, unit, symbol, label, level, **extra):
        calc.add_var(name=name, value=value, unit=unit, symbol=symbol, label=label, level=level, source=SOURCE, norm=norm, norm_ref=norm_ref, **extra)

    center_label = "Drehpunkt (festgelegt)" if manual else "Drehpunkt (Schwerpunkt der Verbindungsmittel)"
    add("x_c", xc, "mm", "x_c", "Drehpunkt, x", 3, group="center", group_label=center_label)
    add("z_c", zc, "mm", "z_c", "Drehpunkt, z", 3, group="center")
    for j, member in enumerate(source["members"]):
        if j != r:
            add(f"theta_{j + 1}", _clean(geometry["local"][j]), "°", f"theta_({r + 1},{j + 1})",
                f"Winkel von Element {r + 1} zu Element {j + 1}", 3, group="angles", group_label="Winkel zwischen den Elementen")
    add("alpha_N", source["directions"]["N"], "°", "alpha_N", "Richtung der Normalkraft", 3, group="directions", group_label="Kraftrichtungen")
    add("alpha_V", source["directions"]["V"], "°", "alpha_V", "Richtung der Querkraft", 3, group="directions")
    add("n", geometry["n"], "", "n", "Anzahl Verbindungsmittel", 2)

    # The two sums are the table's totals row; their steps carry no formula and record only that they are calculated, like the dead load's g_k and a_k.
    add("I_px", geometry["I_px"], "mm²", "I_(p,x)", "Polares Flächenträgheitsmoment, Anteil x", 3)
    calc.add_step(name="Polares Flächenträgheitsmoment, Anteil x", level=3, result="I_px", uses=[], norm=norm, norm_ref=norm_ref)
    add("I_pz", geometry["I_pz"], "mm²", "I_(p,z)", "Polares Flächenträgheitsmoment, Anteil z", 3)
    calc.add_step(name="Polares Flächenträgheitsmoment, Anteil z", level=3, result="I_pz", uses=[], norm=norm, norm_ref=norm_ref)
    add("I_p", geometry["I_p"], "mm²", "I_p", "Polares Flächenträgheitsmoment", 2)
    calc.add_step(
        name="Polares Flächenträgheitsmoment", level=3, result="I_p", uses=["I_px", "I_pz"],
        formula="I_p = I_(p,x) + I_(p,z)", norm=norm, norm_ref=norm_ref,
        description="Σ (Δx² + Δz²) über alle Verbindungsmittel, jedes als Einheitspunkt gezählt — daher in mm² und nicht in mm⁴.",
    )

    calculated, reason = calculation_state(source, detail, geometry)
    return {
        "label": source.get("label", ""),
        "schema": source["schema"],
        "source": f"connections/{cid}.json",
        # 4.1 (periodic audit 260916, AUD-7-301): whether the report may print this calculation, and why not. A connection whose schema lost a marker or an element was printed on what remained -- n = 3 where four fasteners were ticked -- and one whose schema was gone stopped every connection's export.
        "calculated": calculated,
        "reason": reason,
        "norm": norm,
        "norm_ref": norm_ref,
        "reference": source["reference"],
        "members": [_member_record(m, j, geometry, detail) for j, m in enumerate(source["members"])],
        "fasteners": [{"x": x, "z": z} for x, z in geometry["points"]],
        "center": {"mode": mode, "x": xc, "z": zc},
        "directions": {"N": source["directions"]["N"], "V": source["directions"]["V"]},
        # One figure per language: its legend is five sentences, and its frame is sized from the widest of
        # them (docs/typst/language.md §4bis). Everything else the report reads off this block -- the fasteners'
        # places, the arrow sizes, the directions of x and z -- is geometry, and the same in all three.
        "figure": {"files": {lang: f"connections/{cid}-{lang}.svg" for lang in strings.LANGUAGES}, **figure},
        "results": ["I_p"],
        "tables": [_table(geometry)],
        **calc.to_dict(),
    }


def calculation_state(source, detail, geometry=None):
    """(calculated, reason): whether the report may print this polar moment, and, where it may not, the sentence it prints instead -- in English, being a compile error's (docs/typst/language.md §4bis).

    What the schema no longer carries warns at the export and never stops it (section 13, the v0.33 rule), and the report refuses to print what it names: a schema gone, a fastener or an element lost, or nothing ticked. A centre lost is not among them -- the centroid replaces it and the record says so (`center.mode`), which is a calculation of what was drawn.
    """
    sid = source.get("schema", "")
    if not sid:
        return False, "it is drawn on no schema -- name one in Woodcore's polar moments tab"
    if detail is None:
        return False, f"its schema {sid} is not among the exported schemas (renamed or deleted) -- name one in Woodcore's polar moments tab"
    geometry = geometry if geometry is not None else analyse(source, detail)
    if geometry["missing"]["markers"]:
        return False, f"its schema {sid} no longer carries the fastener(s) {', '.join(geometry['missing']['markers'])} -- tick the fasteners again in Woodcore's polar moments tab"
    if geometry["missing"]["elements"]:
        return False, f"its schema {sid} no longer carries the element(s) {', '.join(geometry['missing']['elements'])} -- choose the members' elements again in Woodcore's polar moments tab"
    if not geometry["points"]:
        return False, "no fastener is ticked -- tick them in Woodcore's polar moments tab"
    return True, ""


# --- Export -----------------------------------------------------------------------

def source_paths(source_dir):
    """Every connection source, in file-name order -- the order they are listed in, and exported in."""
    source_dir = Path(source_dir)
    if not source_dir.is_dir():
        return []
    return sorted(source_dir.glob("*.json"), key=lambda p: p.name.lower())


def schema_warnings(source, detail, schemas, where):
    """What the schema a source names does not carry, as warnings -- never as a stop (docs/decisions.md §13, the v0.33 rule): the report refuses to print such a connection, and Woodcore must still be able to open it and point it at another schema.

    Four things can be missing, and each is said with what to do about it: the schema itself, a marker a fastener sits on, an element a member is, and the aid a fixed rotation centre names.
    """
    out = []
    sid = source.get("schema", "")
    listed = ", ".join(sorted(schemas)) or "none yet -- draw one in Woodcore's «Schémas» tab"
    names = ", ".join(sorted(schemas))
    if not sid:
        out.append(engine.Note("polar_no_schema" if names else "polar_no_schema_none",
                               f"{where} is drawn on no schema -- name one in Woodcore's polar moments tab (schemas: {listed}); the report cannot print it until then",
                               connection=where, schemas=names))
        return out
    if detail is None:
        out.append(engine.Note("polar_schema_gone" if names else "polar_schema_gone_none",
                               f"{where} is drawn on schema {sid}, which the export does not list -- name one of {listed}; the report cannot print it until then",
                               connection=where, schema=sid, schemas=names))
        return out
    missing = analyse(source, detail)["missing"]
    if missing["markers"]:
        out.append(engine.Note("polar_markers_lost", f"{where}: schema {sid} no longer carries the marker(s) or point(s) {', '.join(missing['markers'])} -- tick the fasteners again in the polar moments tab; they are left out of the calculation",
                               connection=where, schema=sid, ids=", ".join(missing["markers"])))
    if missing["elements"]:
        out.append(engine.Note("polar_elements_lost", f"{where}: schema {sid} no longer carries the element(s) {', '.join(missing['elements'])} -- choose the members' elements again; their angles are taken as 0°",
                               connection=where, schema=sid, ids=", ".join(missing["elements"])))
    if missing["centre"]:
        out.append(engine.Note("polar_centre_lost", f"{where}: schema {sid} no longer carries the centre {missing['centre']} -- the fasteners' centroid is used instead",
                               connection=where, schema=sid, centre=missing["centre"]))
    return out


def stamp_version(source):
    """The schema_version a source is saved at: 4.1 where a field follows a variable, 4.0 where none does -- what Woodcore's window calls before it writes one."""
    source["schema_version"] = LINKED_SCHEMA_VERSION if links.is_linked(source, LINKABLE) else SOURCE_SCHEMA_VERSION
    return source


def prepare(source_dir, schemas=None, positions=None, values=None):
    """(data, figures, warnings): data/connections.json as it will be written and each connection's SVG, built and validated from every source file, nothing written yet -- so export_all.py can check the connections along with everything else before it writes anything -- and a warning for everything the schema a calculation is drawn on no longer carries. `schemas` is {id: source} of the detail schemas, which is where the geometry comes from since v0.74. `positions` are the position records the schema's elements take their section and label from (v0.75), so the figure's pieces are the ones the schema's own figure draws. No source folder is a project without connections, not an error. Since v0.76 no connector is asked for: a connection names none."""
    from domains import connection_svg  # the figure module draws what this module computes

    schemas = schemas if schemas is not None else {}
    connections, figures, warnings = {}, {}, []
    for path in source_paths(source_dir):
        source = read_source(path)
        # a field that follows a variable takes the value it gives now -- a load's, a script's, a «Formule» domain's, never a joint's (ARCH-005); one that cannot be read its last value with a warning
        provenance = []
        if values is not None:
            source, provenance, followed = links.follow(source, LINKABLE, values, f"connections/{path.name}", links.JOINTS)
            warnings += followed
        detail = schemas.get(source["schema"])
        geometry = analyse(source, detail)
        drawing = connection_svg.layout(source, geometry, detail, positions)
        connections[source["id"]] = build_record(source, detail, connection_svg.meta(drawing), positions)
        if provenance:
            connections[source["id"]]["links"] = provenance
        figures[source["id"]] = {lang: connection_svg.render(drawing, lang=lang) for lang in strings.LANGUAGES}
        warnings += schema_warnings(source, detail, schemas, f"connections/{path.name}")
    linked = any("links" in record for record in connections.values())
    data = {"schema_version": LINKED_EXPORT_VERSION if linked else EXPORT_SCHEMA_VERSION, "connections": connections}
    validation.validate_structure(data, "connections")
    validation.validate_connections_business(data)
    return data, figures, warnings


def write(data, figures, data_dir):
    """Writes data/connections.json and data/connections/<id>.svg, and removes the figure of a connection that no longer exists -- that folder is generated, like the rest of data/."""
    data_dir = Path(data_dir)
    engine.write_json(data_dir / EXPORT_FILE, data)
    figure_dir = data_dir / "connections"
    figure_dir.mkdir(parents=True, exist_ok=True)
    wanted = set()
    for cid, per_language in figures.items():
        for lang, svg in per_language.items():
            name = f"{cid}-{lang}.svg"
            wanted.add(name)
            target = figure_dir / name
            payload = svg.encode("utf-8")
            # A figure whose content has not changed is left alone, so Git sees a change only where there is one.
            if target.is_file() and target.read_bytes() == payload:
                continue
            target.write_bytes(payload)
    for stale in figure_dir.glob("*.svg"):
        if stale.name not in wanted:
            stale.unlink()


def export(source_dir, data_dir, schema_dir=None, schemas=None, values=None):
    """The connections' part of the export, on its own: what Woodcore's window runs when a connection is saved, so the report sees it without the load workbooks being read again -- the schemas they are drawn on being read here from `schema_dir` unless `schemas` is handed over, and the positions their pieces are labelled with being the ones the last full export wrote. export_all.py runs the same two steps. Returns (data, warnings)."""
    if schemas is None:
        schemas = schema_model.read_sources(schema_dir if schema_dir is not None else Path(source_dir).parent / "details")
    from domains import connector   # the position records the last export wrote, read as the connectors read them
    if values is None:
        import variable_sources   # the reader of data/'s variables, which imports this module: imported here
        values = variable_sources.known_values(Path(data_dir))
    data, figures, warnings = prepare(source_dir, schemas, connector.known_positions(data_dir), values)
    write(data, figures, data_dir)
    return data, warnings
