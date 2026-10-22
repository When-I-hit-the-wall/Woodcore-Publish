"""A dimension's geometry, once for every figure that carries dimensions: the static models (domains/statics.py), the detail schemas (domains/schema.py) and the position plans (domains/plan.py) -- issue #9, spec docs/requirements/completed/2026-10-08-plan-positions-cotes-numerotation-sections.md, ARCH-004, Q-010 (the engineer: «noyau commun»).

Until issue #9 the static models and the schemas each carried their own copy of these few lines, word for word, and the plan would have been the third. Here they work on points **already resolved** -- each figure says itself where a dimension's ends are (a node, an aid, a point of the sheet) and in what unit -- so what a dimension measures and where its line runs is computed the one way: a horizontal or vertical dimension the projection of its two ends, a parallel one their distance, its line `offset` from their middle so it follows them when one moves; an angle the arc between two rays about where two directions cross. No unit, no anchor, no drawing: those stay each figure's own.

Qt-free, as every module of calc/domains/.
"""

import math

# The kinds a dimension may be, the linear three and the angle -- the static models' and the schemas' since v0.66; a plan's chain is a row of linear dimensions of one of the three (plan.DIMENSION_KINDS).
KINDS = ("horizontal", "vertical", "parallel", "angle")
LINEAR = ("horizontal", "vertical", "parallel")


def normalize_angle(degrees):
    """An angle in degrees, brought into (-180, 180]."""
    a = math.fmod(degrees, 360.0)
    if a <= -180:
        a += 360
    elif a > 180:
        a -= 360
    return a


def midpoint(a, b):
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def direction(kind, a, b, same_point):
    """The direction a linear dimension's line runs in, and the direction its offset is measured along -- the one at right angles to it, pointing the way a positive offset goes: (1, 0) and (0, 1) for the two axis-aligned kinds whatever the two ends do, the ends' own direction for a parallel one. None for a parallel dimension whose ends are closer than `same_point`."""
    if kind == "horizontal":
        return (1.0, 0.0), (0.0, 1.0)
    if kind == "vertical":
        return (0.0, 1.0), (1.0, 0.0)
    length = math.dist(a, b)
    if length <= same_point:
        return None
    u = ((b[0] - a[0]) / length, (b[1] - a[1]) / length)
    return u, (-u[1], u[0])


def onto(kind, a, b, points, offset, same_point):
    """`points` carried onto the line of the dimension from `a` to `b` -- `offset` from the middle of a and b along the offset direction --, so every witness line is parallel: the two ends of one dimension, or every point of a chain of them. None where `direction` is."""
    frame = direction(kind, a, b, same_point)
    if frame is None:
        return None
    _u, n = frame
    offset = float(offset)
    base = midpoint(a, b)

    def one(p):
        d = (p[0] - base[0]) * n[0] + (p[1] - base[1]) * n[1]
        return (p[0] + n[0] * (offset - d), p[1] + n[1] * (offset - d))
    return [one(p) for p in points]


def line(kind, a, b, offset, same_point):
    """Where a linear dimension's line is drawn: the two ends carried onto it, `offset` from their middle along the offset direction, so the two witness lines are parallel and the line follows the ends. None where `direction` is."""
    found = onto(kind, a, b, (a, b), offset, same_point)
    return None if found is None else (found[0], found[1])


def linear_value(kind, a, b):
    """What a linear dimension measures, in its ends' unit: the horizontal or the vertical projection, or the distance."""
    if kind == "horizontal":
        return abs(b[0] - a[0])
    if kind == "vertical":
        return abs(b[1] - a[1])
    return math.dist(a, b)


def crossing(a, u, b, v, parallel):
    """Where the line through `a` along `u` crosses the one through `b` along `v`, with the two directions: (centre, u, v); None where they are parallel within `parallel`, leaving no corner to turn about."""
    denominator = u[0] * v[1] - u[1] * v[0]
    if abs(denominator) < parallel:
        return None
    t = ((b[0] - a[0]) * v[1] - (b[1] - a[1]) * v[0]) / denominator
    return ((a[0] + u[0] * t, a[1] + u[1] * t), u, v)


def rays_by_bearing(u, v, bearing):
    """The ray of each direction on the side `bearing` (degrees, the direction of the click that placed the dimension, from the corner) points to: the two rays that bound the sector the click fell in."""
    a = math.radians(float(bearing))
    d = (math.cos(a), math.sin(a))
    first = u if d[0] * u[0] + d[1] * u[1] >= 0 else (-u[0], -u[1])
    second = v if d[0] * v[0] + d[1] * v[1] >= 0 else (-v[0], -v[1])
    return first, second


def arc(first, second, reflex):
    """An angle dimension's arc between two rays: (sweep, start) in degrees, the short way round -- at most 180 -- or its reflex where `reflex`."""
    start = math.degrees(math.atan2(first[1], first[0]))
    sweep = normalize_angle(math.degrees(math.atan2(second[1], second[0])) - start)
    if reflex:
        sweep = sweep - 360.0 if sweep > 0 else sweep + 360.0
    return sweep, start


def show(dim, modes):
    """What a dimension writes beside itself, one of `modes` -- nothing, its name, what it measured, or both: the `show` it states, else, for one saved before it could say so, `name` where it carries a label and `value` where it does not."""
    mode = dim.get("show")
    if mode in modes:
        return mode
    return "name" if (dim.get("label") or "").strip() else "value"


def text(mode, label, value_text):
    """What a dimension writes on the figure by its `mode`: nothing, its name, what it measured, or `name = value` -- a name asked for and not given writes nothing, and `name+value` without one writes the value alone (a load's own rule)."""
    if mode == "none":
        return ""
    label = (label or "").strip()
    if mode == "name":
        return label
    if mode == "value" or not label:
        return value_text
    return f"{label} = {value_text}"


# --- plane geometry the drawing engines share (spec 2026-10-19-base-saine-nettoyage, D4): written once here, imported back by the modules that each had a copy

def _cross(a, u, b, v):
    """Where the line through `a` along `u` meets the one through `b` along `v`, with the two parameters, or None for parallels."""
    det = u[0] * v[1] - u[1] * v[0]
    if abs(det) < 1e-12:
        return None
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = (dx * v[1] - dy * v[0]) / det
    s = (dx * u[1] - dy * u[0]) / det
    return ((a[0] + t * u[0], a[1] + t * u[1]), t, s)


def _inside(p, polygon):
    """Even-odd point-in-polygon."""
    inside = False
    n = len(polygon)
    for i in range(n):
        (x1, y1), (x2, y2) = polygon[i], polygon[(i + 1) % n]
        if (y1 > p[1]) != (y2 > p[1]) and p[0] < (x2 - x1) * (p[1] - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def _local(frame, point):
    """`point` in the frame of a number's box: from its centre, x along its text, y across it."""
    a = math.radians(frame["angle"])
    dx, dy = point[0] - frame["at"][0], point[1] - frame["at"][1]
    return (dx * math.cos(a) + dy * math.sin(a), -dx * math.sin(a) + dy * math.cos(a))


def _point_segment(p, a, b):
    """The distance from `p` to the segment a-b, and the nearest point on it."""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    length2 = dx * dx + dy * dy
    if length2 <= 0:
        return math.dist(p, a), tuple(a)
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / length2))
    q = (ax + t * dx, ay + t * dy)
    return math.dist(p, q), q


def constrain(anchor, point):
    """`point` brought onto the nearest of the eight directions from `anchor` -- horizontal, vertical or at 45° -- as Shift does while drawing."""
    dx, dy = point[0] - anchor[0], point[1] - anchor[1]
    if abs(dx) < 1e-12 and abs(dy) < 1e-12:
        return tuple(anchor)
    a = round(math.atan2(dy, dx) / (math.pi / 4)) * (math.pi / 4)
    ux, uy = math.cos(a), math.sin(a)
    t = dx * ux + dy * uy
    return (anchor[0] + t * ux, anchor[1] + t * uy)


def grid_snap(p, step):
    """`p` pulled onto the nearest crossing of a grid of that step, in mm."""
    if not step or step <= 0:
        return tuple(p)
    return (round(p[0] / step) * step, round(p[1] / step) * step)


def index_of(source, collection, eid):
    for i, entry in enumerate(source.get(collection, [])):
        if entry.get("id") == eid:
            return i
    return None


# --- the dimensions and the tracking of the schemas and the static models (spec 2026-10-20-indices-et-niveaux, ARCH-004): written once here, each module keeping a wrapper that hands its own anchor reader and its own tolerance (mm in a schema, m in a static model)

def ends(anchor_of, source, dim):
    """A linear dimension's two ends, or None where either is unresolvable -- `anchor_of(source, ref)` the module's reader of a point a dimension names."""
    a = anchor_of(source, dim.get("from"))
    b = anchor_of(source, dim.get("to"))
    return None if a is None or b is None else (a, b)


def linear_direction(dim, both, same_point):
    """The direction a linear dimension's line runs in and the one its offset is measured along (`direction`): (1, 0) and (0, 1) for the two axis-aligned kinds whatever the ends do; None where a parallel one's ends (`both`) do not resolve."""
    kind = dim.get("kind")
    if kind in ("horizontal", "vertical"):
        return direction(kind, None, None, same_point)
    return None if both is None else direction(kind, both[0], both[1], same_point)


def linear_line(dim, both, same_point):
    """Where a linear dimension's line is drawn (`line`): its two ends (`both`) projected onto it, `offset` from their middle; None where they do not resolve."""
    return None if both is None else line(dim.get("kind"), both[0], both[1], dim.get("offset", 0.0), same_point)


def angle_arc(rays, dim):
    """An angle dimension's arc -- (centre, sweep, start) -- between the two rays the module chose (`rays`: centre, first, second), the reflex where a negative radius asks for it on a dimension carrying its `bearing` (`arc`); None where the rays do not resolve."""
    if rays is None:
        return None
    centre, first, second = rays
    sweep, start = arc(first, second, dim.get("bearing") is not None and float(dim.get("offset", 0.0)) < 0)
    return centre, sweep, start


def along(anchor, ray, distance):
    """The point `distance` from `anchor` along `ray`, in the figure's unit."""
    return (anchor[0] + distance * ray["unit"][0], anchor[1] + distance * ray["unit"][1])


def typed_point(anchor, ray, text):
    """Where a distance typed into Woodcore's field lands along `ray`, or None where it is not a number. A comma is read as a decimal point, the keyboard here having one."""
    try:
        distance = float(str(text).strip().replace(",", "."))
    except (TypeError, ValueError):
        return None
    if not math.isfinite(distance):
        return None
    return along(anchor, ray, distance)


def nearest_ray(rays, anchor, point, tolerance_deg, same_point):
    """The ray of smallest angular deviation from `anchor` towards `point`, within `tolerance_deg`, and `point` projected onto it -- or (None, point). A ray is measured in its own sense only, both senses being in the list, so a lock holds on either side."""
    dx, dy = point[0] - anchor[0], point[1] - anchor[1]
    if math.hypot(dx, dy) <= same_point:
        return None, tuple(point)
    angle = math.degrees(math.atan2(dy, dx))
    best, best_off = None, tolerance_deg
    for ray in rays:
        off = abs(normalize_angle(angle - ray["angle"]))
        if off <= best_off:
            best, best_off = ray, off
    if best is None:
        return None, tuple(point)
    along_ray = dx * best["unit"][0] + dy * best["unit"][1]
    return best, (anchor[0] + along_ray * best["unit"][0], anchor[1] + along_ray * best["unit"][1])


def box_corners(frame, margin=0.0):
    """The four corners of a label's box -- `frame`: its centre `at`, its half sizes `hw`, `hh`, its `angle` --, `margin` beyond its edges, turned with its text: what Woodcore outlines a selected label or position number with (the schemas, the static models, the plans; ARCH-004)."""
    a = math.radians(frame["angle"])
    c, s = math.cos(a), math.sin(a)
    (x, y), hw, hh = frame["at"], frame["hw"] + margin, frame["hh"] + margin
    return [(x + u * c - v * s, y + u * s + v * c) for u, v in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]


def unit(a, b):
    """The unit vector from `a` to `b`, (1, 0) where they are one point (ARCH-004, D-15)."""
    d = math.dist(a, b)
    return (1.0, 0.0) if d < 1e-12 else ((b[0] - a[0]) / d, (b[1] - a[1]) / d)
