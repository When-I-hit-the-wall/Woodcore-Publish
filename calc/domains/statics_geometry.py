"""The geometry of a static model -- where a member's points, a load and a dimension stand, what a click hits, what the pointer snaps and tracks to -- split out of calc/domains/statics.py (issue #30), moved verbatim: what the «Modèles statiques» canvas asks while it draws. statics.py imports every name back, so `statics.snap` and the rest are still read where they always were. Qt-free.
"""

import math
import re
import number_text  # the one trimming of a number (ARCH-004)
from domains import dimension  # a dimension's geometry, shared with the schemas and the plans (issue #9)
from domains.dimension import _cross, _point_segment, constrain, grid_snap, index_of  # plane geometry written once (D4)
from domains.dimension import normalize_angle  # plane geometry written once (D4)


# What a load writes beside itself: nothing, the name it was given, its value and unit, or both. A dimension takes the same four, its name being its `label` (`dimension_show`).
LABEL_MODES = ("none", "name", "value", "name+value")


# What a dimension prints: metres for a length, degrees for an angle.
DIMENSION_UNITS = {"horizontal": "m", "vertical": "m", "parallel": "m", "angle": "°"}


# Two members whose axes are this near to parallel have no crossing to turn an angle about.
PARALLEL_TOLERANCE = 1e-6


# Two points closer than this, in metres, are one point typed twice -- a tenth of a millimetre.
SAME_POINT = 1e-4


# The directions the cursor locks to, in degrees from +x. The eight of AutoCAD's polar tracking; a member's own axis and its normal are added to them at a node.
TRACK_ANGLES = (0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0)


# How far off a ray the pointer may be and still lock to it.
TRACK_TOLERANCE_DEG = 4.0


# The snap targets, in the order one is preferred over another at equal distance.
SNAP_KINDS = ("point", "midpoint", "crossing", "on-member", "grid")


# How far along its reference member a point load is drawn, given as a length in metres or as a fraction of that member's own length -- `0.5l` is its middle. It moves where the load is drawn and nothing else: the load still acts at its point.
ALONG_PATTERN = re.compile(r"^\s*([-+]?[0-9]*[.,]?[0-9]+)\s*([lL]?)\s*$")


# At most this many decimals wherever this module writes a number as text, trailing zeros dropped. The same rule as lib/calc-engine.typ's fmt-decimals and woodcore_gui.fmt_value; the three must agree, since the figure, the report and the window show the same number.
DIGITS = 3


# An angle is written to a tenth of a degree, as show-polar-moment writes its force-grain angles: three decimals on an angle read as a precision the drawing it was measured off does not have.
ANGLE_DIGITS = 1


def fmt_number(value, digits=DIGITS):
    """A number as the figure writes it: at most `digits` decimals, trailing zeros dropped (4.9788 -> 4.979, 3.50 -> 3.5, 20 -> 20)."""
    return number_text.plain(value, digits)


def figure_number(value, digits=DIGITS):
    """A number as a figure *prints* it: `fmt_number`, its sign the real minus U+2212 and never a hyphen, which is the width of a letter's stroke and reads as a dash beside a number. For text set on a figure only -- a coordinate, a cell Woodcore reads back and anything else a program parses keeps `fmt_number`'s hyphen."""
    text = fmt_number(value, digits)
    return "−" + text[1:] if text.startswith("-") else text


def parse_along(text, length=None):
    """How far along its reference member a point load is drawn: `2.5` is metres, `0.5l` half the member. None for anything else; 0 for nothing given."""
    if text in (None, ""):
        return 0.0
    if isinstance(text, (int, float)) and not isinstance(text, bool):
        return float(text)
    m = ALONG_PATTERN.match(str(text))
    if m is None:
        return None
    value = float(m.group(1).replace(",", "."))
    if not m.group(2):
        return value
    return value if length is None else value * length


def entry_of(source, collection, eid):
    i = index_of(source, collection, eid)
    return source[collection][i] if i is not None else None


def point_at(source, pid):
    """A point's coordinates, or None where the model has no such point."""
    point = entry_of(source, "points", pid)
    return None if point is None else (float(point["x"]), float(point["z"]))


def member_points(source, mid):
    """A member's two ends, or None where either is missing."""
    member = entry_of(source, "members", mid)
    if member is None:
        return None
    a = point_at(source, member.get("p1"))
    b = point_at(source, member.get("p2"))
    return None if a is None or b is None else (a, b)


def member_length(source, mid):
    ends = member_points(source, mid)
    return 0.0 if ends is None else math.dist(ends[0], ends[1])


def member_direction(source, mid):
    """The unit vector from p1 towards p2, or None for a member of no length -- which check_source refuses, but a draft may hold for a moment."""
    ends = member_points(source, mid)
    if ends is None:
        return None
    (ax, ay), (bx, by) = ends
    length = math.hypot(bx - ax, by - ay)
    if length <= SAME_POINT:
        return None
    return ((bx - ax) / length, (by - ay) / length)


def member_angle(source, mid):
    """The angle of a member's axis in degrees from +x towards +z, or None."""
    u = member_direction(source, mid)
    return None if u is None else math.degrees(math.atan2(u[1], u[0]))


def load_at(source, load):
    """Where a point load is **drawn**: its point, moved along its reference member by `along`. It still acts at its point -- the offset is a drawing convenience, which is why a load at midspan needs no node there: `0.5l` puts it at the middle of the member it refers to."""
    p = point_at(source, load.get("point"))
    if p is None:
        return None
    reference = load.get("reference")
    if not reference or load.get("along") in (None, ""):
        return p
    u = member_direction(source, reference)
    distance = parse_along(load.get("along"), member_length(source, reference))
    if u is None or distance is None:
        return p
    return (p[0] + u[0] * distance, p[1] + u[1] * distance)


def load_direction(source, load, member_id=None):
    """The unit vector a load acts along, resolving the four modes: straight down, along +x, at an angle from +x, or at an angle from a member's axis. None where the member it is measured from has no direction. Down is +z, so a vertical load and a load at 90 degrees point the same way."""
    direction = load.get("direction")
    if direction == "vertical":
        return (0.0, 1.0)
    if direction == "horizontal":
        return (1.0, 0.0)
    angle = math.radians(float(load.get("angle", 0.0)))
    if direction == "angle":
        return (math.cos(angle), math.sin(angle))
    reference = load.get("reference") or member_id
    base = member_angle(source, reference)
    if base is None:
        return None
    total = math.radians(base) + angle
    return (math.cos(total), math.sin(total))


def line_load_span(source, load):
    """The stretch of its member a line load covers, as its two end points."""
    ends = member_points(source, load.get("member"))
    if ends is None:
        return None
    (ax, ay), (bx, by) = ends
    s, t = float(load.get("from", 0.0)), float(load.get("to", 1.0))
    return ((ax + (bx - ax) * s, ay + (by - ay) * s), (ax + (bx - ax) * t, ay + (by - ay) * t))


def bbox(source):
    """The model's own extent, (x0, z0, x1, z1) -- every point and every load's point of application. None for a model with nothing in it. What *Ajuster* fits and what the drawing's symbol size is derived from; the drawing's own frame is larger, and is statics_svg's to compute."""
    xs, zs = [], []
    for point in source.get("points", []):
        xs.append(float(point["x"]))
        zs.append(float(point["z"]))
    for load in source.get("point_loads", []):
        p = load_at(source, load)
        if p is not None:
            xs.append(p[0])
            zs.append(p[1])
    if not xs:
        return None
    return (min(xs), min(zs), max(xs), max(zs))


def dimension_anchor(source, anchor):
    """Where one end of a dimension is, in metres. `{"point": "P1"}` follows that point as it is moved -- the reason an anchor is stored rather than a pair of coordinates -- and `{"x": .., "z": ..}` stays where it was put. None where it names a point the model no longer has."""
    if not isinstance(anchor, dict):
        return None
    if anchor.get("point"):
        return point_at(source, anchor["point"])
    if "x" in anchor and "z" in anchor:
        return (float(anchor["x"]), float(anchor["z"]))
    return None


def dimension_ends(source, dim):
    """A linear dimension's two ends, in metres, or None where either is unresolvable."""
    return dimension.ends(dimension_anchor, source, dim)


def _axis(source, mid):
    """A member's axis as a point on it and its unit direction -- what an angle is turned about."""
    ends = member_points(source, mid)
    u = member_direction(source, mid)
    return None if ends is None or u is None else (ends[0], u)


def dimension_corner(source, dim):
    """Where an angle dimension's two members cross, in metres, with each member's direction. None where either member is unresolvable or the two are parallel, which leaves no corner to turn about."""
    first = _axis(source, (dim.get("from") or {}).get("member"))
    second = _axis(source, (dim.get("to") or {}).get("member"))
    if first is None or second is None:
        return None
    (a, u), (b, v) = first, second
    return dimension.crossing(a, u, b, v, PARALLEL_TOLERANCE)


_midpoint = dimension.midpoint   # written once (ARCH-004)


def dimension_direction(source, dim):
    """The direction a linear dimension's line runs in, and the direction its offset is measured along -- the one at right angles to it, pointing the way a positive offset goes. (1, 0) and (0, 1) for the two axis-aligned kinds, whatever the two ends do."""
    return dimension.linear_direction(dim, dimension_ends(source, dim), SAME_POINT)


def dimension_line(source, dim):
    """Where a linear dimension's line is drawn, in metres: the two ends projected onto it. The offset is measured from the **middle** of the two ends, so the line follows them when a point is moved."""
    return dimension.linear_line(dim, dimension_ends(source, dim), SAME_POINT)


def dimension_value(source, dim):
    """What a dimension measures, and its unit: a length in metres for the three linear kinds, an angle in degrees for the fourth. None where the geometry does not resolve."""
    kind = dim.get("kind")
    unit = DIMENSION_UNITS.get(kind, "")
    if kind == "angle":
        corner = dimension_corner(source, dim)
        if corner is None:
            return None, unit
        return abs(dimension_angle(source, dim)[1]), unit
    ends = dimension_ends(source, dim)
    if ends is None:
        return None, unit
    return dimension.linear_value(kind, ends[0], ends[1]), unit


def _member_ray(source, mid, centre, u):
    """The ray of a member's axis that runs from `centre` towards the member's own body, as (dx, dz). Where the corner falls at the member's middle -- two members crossing rather than meeting -- there is no body to point at and `u` is returned as it is."""
    ends = member_points(source, mid)
    if ends is None:
        return u
    middle = _midpoint(ends[0], ends[1])
    reach = (middle[0] - centre[0], middle[1] - centre[1])
    along = reach[0] * u[0] + reach[1] * u[1]
    return (-u[0], -u[1]) if along < 0 else u


def angle_rays(source, dim):
    """The two rays an angle dimension's arc runs between, one along each member's axis, and the corner they turn about: (centre, first, second).

    **A member's stored direction is not a ray of the corner.** `member_direction` runs p1 -> p2, which at an L or a T points away from the corner as often as towards it, so an arc built from the two stored directions lands in whichever of the four sectors those happen to bound -- and the sign of the radius then only chooses between that sector and its reflex. Two of the four sectors could not be drawn at all, which is what the engineer met: a beam and the post under it, wanting the 90 degrees below and to the left and getting only 270.

    So the sector is chosen here, from the four the two axes cut the plane into. `bearing` -- the direction of the third click from the corner, in degrees -- names it: the ray of each axis lying on the click's own side bounds the sector the click fell in, which is the one the engineer pointed at. A dimension written before `bearing` existed falls back to each member's body, which is the corner's own geometry and is right wherever the two meet end to end.
    """
    corner = dimension_corner(source, dim)
    if corner is None:
        return None
    centre, u, v = corner
    bearing = dim.get("bearing")
    if bearing is None:
        first = _member_ray(source, (dim.get("from") or {}).get("member"), centre, u)
        second = _member_ray(source, (dim.get("to") or {}).get("member"), centre, v)
        return centre, first, second
    first, second = dimension.rays_by_bearing(u, v, bearing)
    return centre, first, second


def dimension_angle(source, dim):
    """An angle dimension's arc: where it starts, how far it sweeps (signed, degrees) and about which point.

    The arc runs between the two rays `angle_rays` chooses, the short way round, so what is drawn is the sector the third click fell in -- at most 180 degrees, and any of the four. A **negative** radius draws that sector's reflex instead, for the rare figure that wants the 270 rather than the 90; a click never writes one, since a click always falls inside a sector.

    On a dimension written **before** `bearing` existed the sign is ignored. There it did not mean a reflex: it was the only way the engineer had of asking for the other side, the two sectors he wanted being unreachable -- so reapplying it would hold the very angle this repairs at 270 degrees. The radius is its magnitude either way.
    """
    return dimension.angle_arc(angle_rays(source, dim), dim)


def dimension_show(dim):
    """What a dimension writes beside itself, one of LABEL_MODES -- a load's own four: nothing, its name (its `label`), what it measured, or both.

    A dimension saved before it could say so reads as it was drawn then: `name` where it carries a label, which then took the measurement's place on the figure, and `value` where it does not.
    """
    return dimension.show(dim, LABEL_MODES)


def dimension_value_text(source, dim):
    """What a dimension measured, with its unit, as the figure prints it -- '?' where the geometry no longer resolves, as an unreadable load value is written. Woodcore's \u00abvaleur\u00bb column shows this whatever the figure writes."""
    value, unit = dimension_value(source, dim)
    if value is None:
        return "?"
    # an angle to a tenth of a degree, as show-polar-moment writes its force-grain angles: three decimals on an angle read as a precision nothing here has. A degree sign sits against its number, a unit of length after a space -- and no narrow space, which is not in ARIAL_WIDTHS and would mis-size the frame.
    if unit == "\u00b0":
        return f"{figure_number(value, ANGLE_DIGITS)}{unit}"
    return f"{figure_number(value)} {unit}"


def dimension_text(source, dim):
    """What a dimension writes on the figure, by its `show` (`dimension_show`): nothing, its name, what it measured, or `name = value`. A name asked for and not given writes nothing, and `name+value` without a name writes the value alone -- a load's own rule (`load_lines`), so the two say the same thing about the same choice."""
    mode = dimension_show(dim)
    return dimension.text(mode, dim.get("label"), dimension_value_text(source, dim) if mode not in ("none", "name") else "")


def hit_point(source, p, tolerance):
    """The id of the point under `p`, the nearest one within the tolerance, or None."""
    best, best_d = None, tolerance
    for point in source.get("points", []):
        d = math.dist(p, (float(point["x"]), float(point["z"])))
        if d <= best_d:
            best, best_d = point["id"], d
    return best


def hit_member(source, p, tolerance):
    """The id of the member under `p`, or None."""
    best, best_d = None, tolerance
    for member in source.get("members", []):
        ends = member_points(source, member["id"])
        if ends is None:
            continue
        d, _q = _point_segment(p, ends[0], ends[1])
        if d <= best_d:
            best, best_d = member["id"], d
    return best


def hit_load(source, p, tolerance, sizes=None):
    """The (collection, id) of the load whose arrow lies under `p`, or (None, None). The arrows' geometry is the drawing's, so it is asked of it."""
    from domains import statics_svg  # where an arrow is drawn is the drawing module's to say

    return statics_svg.hit_load(source, p, tolerance, sizes)


def hit_label(source, p, tolerance, frames=None):
    """The (collection, id) whose label box lies under `p`, or (None, None) -- a label is drawn over every symbol, so a click on it takes the label."""
    from domains import statics_svg

    return statics_svg.hit_label(source, p, tolerance, frames)


def _segments(source, exclude=None):
    """Every member as (id, a, b), skipping the one being dragged."""
    out = []
    for member in source.get("members", []):
        if member["id"] == exclude:
            continue
        ends = member_points(source, member["id"])
        if ends is not None:
            out.append((member["id"], ends[0], ends[1]))
    return out


def snap_targets(source, exclude=None):
    """The hard targets a point may be put down on, as (priority, kind, point) -- nodes first, then the middles of members, then where two members cross. `on-member` and the grid are handled in snap(), being a projection rather than a point."""
    out = []
    for point in source.get("points", []):
        out.append((0, "point", (float(point["x"]), float(point["z"]))))
    segments = _segments(source, exclude)
    for _mid, a, b in segments:
        out.append((1, "midpoint", ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)))
    for i, (_mi, a, b) in enumerate(segments):
        u = (b[0] - a[0], b[1] - a[1])
        for _mj, c, d in segments[i + 1:]:
            v = (d[0] - c[0], d[1] - c[1])
            hit = _cross(a, u, c, v)
            if hit is not None and -1e-9 <= hit[1] <= 1 + 1e-9 and -1e-9 <= hit[2] <= 1 + 1e-9:
                out.append((2, "crossing", hit[0]))
    return out


def snap(source, p, tolerance, step=None, exclude=None):
    """The point a click at `p` puts down, and what it snapped to. A node beats the middle of a member, which beats a crossing, which beats a point on a member; the grid catches whatever is left, so a click always lands on a round number where a grid is on."""
    best, best_kind, best_rank = tuple(p), None, None
    for priority, kind, q in snap_targets(source, exclude):
        d = math.dist(p, q)
        if d <= tolerance:
            rank = (priority, d)
            if best_rank is None or rank < best_rank:
                best, best_kind, best_rank = tuple(q), kind, rank
    if best_kind is None:
        for _mid, a, b in _segments(source, exclude):
            d, q = _point_segment(p, a, b)
            if d <= tolerance:
                rank = (SNAP_KINDS.index("on-member"), d)
                if best_rank is None or rank < best_rank:
                    best, best_kind, best_rank = q, "on-member", rank
    if best_kind is None and step:
        q = grid_snap(p, step)
        return q, "grid"
    return best, best_kind


def tracking_rays(source, anchor, tolerance=SAME_POINT):
    """The rays the cursor may lock to from `anchor`: the eight polar directions, plus the axis and the normal of every member that meets the anchor. Each is {kind, angle, unit, via}; two rays of the same direction are folded into one, the more specific kind winning, so a member lying at exactly 45 degrees gives one ray named by its member."""
    rays = {}
    # Where two rays fall on one direction, the more specific name for it wins: a member's own axis first, then a member's normal, then the bare polar direction. On a frame whose members are square to each other every polar direction is also an axis or a normal, and the readout should say which member it is following.
    rank = {"axis": 0, "normal": 1, "ortho": 2}

    def add(kind, angle, via=None):
        angle = normalize_angle(angle)
        key = round(angle, 6)
        if key in rays and rank[rays[key]["kind"]] <= rank[kind]:
            return
        radians = math.radians(angle)
        rays[key] = {"kind": kind, "angle": angle, "unit": (math.cos(radians), math.sin(radians)), "via": via}

    for angle in TRACK_ANGLES:
        add("ortho", angle)
    for member in source.get("members", []):
        ends = member_points(source, member["id"])
        if ends is None:
            continue
        for end, other in ((ends[0], ends[1]), (ends[1], ends[0])):
            if math.dist(anchor, end) <= tolerance:
                base = math.degrees(math.atan2(other[1] - end[1], other[0] - end[0]))
                add("axis", base, member["id"])
                add("axis", base + 180, member["id"])
                add("normal", base + 90, member["id"])
                add("normal", base - 90, member["id"])
    return sorted(rays.values(), key=lambda r: r["angle"])


def extension_lines(source, exclude=None):
    """Every member's line, extended beyond its ends, as (point, unit, member id) -- "le prolongement d'une ligne existante"."""
    out = []
    for mid, a, b in _segments(source, exclude):
        length = math.dist(a, b)
        if length > SAME_POINT:
            out.append((a, ((b[0] - a[0]) / length, (b[1] - a[1]) / length), mid))
    return out


def nearest_ray(rays, anchor, point, tolerance_deg=TRACK_TOLERANCE_DEG):
    """The ray of smallest angular deviation from `anchor` towards `point`, within the tolerance, and `point` projected onto it -- or (None, point). A ray is measured in its own sense only, and both senses are in the list, so a lock holds on either side."""
    return dimension.nearest_ray(rays, anchor, point, tolerance_deg, SAME_POINT)


def along(anchor, ray, distance):
    """The point `distance` metres from `anchor` along `ray`."""
    return dimension.along(anchor, ray, distance)


def typed_point(anchor, ray, text):
    """Where a distance typed into Woodcore's field lands, or None where it is not a number. A comma is read as a decimal point, the keyboard here having one."""
    return dimension.typed_point(anchor, ray, text)


def track(source, anchor, point, tolerance, step=None, tolerance_deg=TRACK_TOLERANCE_DEG, exclude=None):
    """Where the cursor is, tracking from `anchor` -- the one call Woodcore's canvas makes on every movement of the mouse.

    Returns {point, ray, kind, distance, angle}. With a ray locked, what lies on that ray is preferred in this order: a hard snap target on it, then where it crosses the line of an existing member extended, then the nearest multiple of the grid along it, then the bare projection. With no ray it degrades to snap(), so the same call serves a pointer that is tracking and one that is not.
    """
    if anchor is None:
        p, kind = snap(source, point, tolerance, step, exclude)
        return {"point": p, "ray": None, "kind": kind, "distance": None, "angle": None}

    rays = tracking_rays(source, anchor)
    ray, projected = nearest_ray(rays, anchor, point, tolerance_deg)
    if ray is None:
        p, kind = snap(source, point, tolerance, step, exclude)
        return {"point": p, "ray": None, "kind": kind, "distance": math.dist(anchor, p), "angle": None}

    best, kind = projected, "ray"
    for priority, target_kind, q in snap_targets(source, exclude):
        _d, on_ray = _point_segment(q, anchor, along(anchor, ray, max(math.dist(anchor, q), 1e-9)))
        if math.dist(q, on_ray) <= tolerance and math.dist(q, projected) <= tolerance * 4:
            best, kind = tuple(q), target_kind
            break
    if kind == "ray":
        for a, u, mid in extension_lines(source, exclude):
            if mid == ray.get("via"):
                continue
            hit = _cross(anchor, ray["unit"], a, u)
            if hit is not None and math.dist(hit[0], projected) <= tolerance * 4:
                best, kind = hit[0], "ray-crossing"
                break
    if kind == "ray" and step:
        distance = (projected[0] - anchor[0]) * ray["unit"][0] + (projected[1] - anchor[1]) * ray["unit"][1]
        rounded = round(distance / step) * step
        if abs(rounded - distance) <= tolerance:
            best, kind = along(anchor, ray, rounded), "grid"
    return {
        "point": best,
        "ray": ray,
        "kind": kind,
        "distance": math.dist(anchor, best),
        "angle": ray["angle"],
    }


def angle_reach(centre, point):
    """Where a third click at `point` puts an angle dimension whose corner is `centre`: (its radius, its `bearing` in degrees -- the direction of the click from the corner, which names the sector the engineer pointed at, `angle_rays`), or None where the click is on the corner. Computed here, in the domain, and not in the canvas that asks for it (spec 2026-10-19-base-saine-nettoyage, D8: the window does not invent geometry)."""
    reach = (point[0] - centre[0], point[1] - centre[1])
    radius = math.hypot(reach[0], reach[1])
    if radius <= SAME_POINT:
        return None
    return radius, math.degrees(math.atan2(reach[1], reach[0]))
