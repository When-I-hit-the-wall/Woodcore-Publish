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
