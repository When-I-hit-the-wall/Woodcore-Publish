"""Tracking for the plan canvases -- the way the static models' tab tracks (docs/domain/static-models.md §3.3octies, docs/ui/window.md §10quater), brought to the position plan and the fire-protection plan (v0.116).

Resting the pointer on a snap point for a moment **acquires** it; the cursor then locks to a tracking ray through the point -- one of the eight polar directions, drawn across the view as a thin dotted line -- and, where two rays of two acquired points meet, to their crossing; where a ray meets an axis, a wall or a storey box, to that crossing. A distance typed with Tab then goes along the locked ray. All of it is arithmetic on plain tuples in the plan's own frame -- **sheet units, x to the right and y DOWN** -- so a ray at 90 degrees points down the page, and it is verified without a window; the canvases (plan_canvas.py, fire_canvas.py) only hold which state they are in.

The module also gives the plan's snapping index the points a section draws and a plan never offered: the two ends of a storey line and the four corners of a storey box are snap points like a wall's corners, so that storeys can be drawn one above another and boxes aligned. It is a module of its own, beside plan.py, so that the geometry the canvases share lies in one place and no plan source or schema moves: nothing here is saved.
"""

import math

from domains import plan

# The kinds of snap that are a point -- the ones a pointer may rest on to acquire it, and that beat every tracking ray: a click lands exactly on such a point or not at all.
HARD_KINDS = ("axis-crossing", "vertex", "crossing", "midpoint")
# What a pointer snapped onto a line (not a point of it) is.
LINE_KINDS = ("on-axis", "on-line")
# The eight polar directions, in degrees from +x towards +y -- the sheet's y runs down, so 90 is straight down the page.
POLAR_ANGLES = (0, 45, 90, 135, 180, 225, 270, 315)
# How many points are kept acquired at once, the newest first, as AutoCAD keeps them.
MAX_ACQUIRED = 3
# What the tracking adds to the snap kinds: a point on a ray, where two rays cross, where a ray crosses a line of the plan.
TRACK_KINDS = ("track", "track-crossing", "track-line")


# --- Storeys ---------------------------------------------------------------------------


def box_corners(box):
    """A storey box's four corners, clockwise from its top left (y down): (x, y), (x + w, y), (x + w, y + h), (x, y + h)."""
    x, y, w, h = (float(box[k]) for k in ("x", "y", "w", "h"))
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def storey_segments(source, exclude=None):
    """The storey lines and the edges of the storey boxes as (kind, index, a, b), kind `storey-line` or `storey-box`. `exclude` is the (kind, index) being dragged, which must not snap to itself."""
    out = []
    for i, line in enumerate(source.get("storey_lines") or []):
        if exclude == ("storey-line", i):
            continue
        points = line.get("points") or []
        if len(points) == 2:
            try:
                out.append(("storey-line", i, (float(points[0][0]), float(points[0][1])), (float(points[1][0]), float(points[1][1]))))
            except (TypeError, ValueError, IndexError):
                continue
    for i, box in enumerate(source.get("storey_boxes") or []):
        if exclude == ("storey-box", i):
            continue
        try:
            corners = box_corners(box)
        except (KeyError, TypeError, ValueError):
            continue
        for j in range(4):
            out.append(("storey-box", i, corners[j], corners[(j + 1) % 4]))
    return out


class PlanSnapIndex(plan.SnapIndex):
    """plan.SnapIndex with what a section adds and what a drawing that is not a position plan carries: a storey line's two ends and a storey box's four corners are `vertex` points, their middles are `midpoint`s, their edges are lines a point may be put on, and where they cross a wall, an axis or each other is a `crossing`. `exclude_storey` is the (kind, index) of the storey line or box being dragged; `extra_points` are further `vertex` points -- the fire-protection plan's, whose entries are no elements. Storeys follow the `elements` button: they are drawn things, like walls."""

    def __init__(self, source, window, axes=True, elements=True, exclude=None, exclude_storey=None, extra_points=()):
        super().__init__(source, window, axes=axes, elements=elements, exclude=exclude)
        for p in extra_points:
            self.points.append((1, "vertex", (float(p[0]), float(p[1]))))
        if not elements:
            return
        before = list(self.lines)
        segments = storey_segments(source, exclude_storey)
        seen = set()
        for kind, i, a, b in segments:
            for end in (a, b):
                if (kind, i, end) not in seen:
                    seen.add((kind, i, end))
                    self.points.append((1, "vertex", end))
            d = (b[0] - a[0], b[1] - a[1])
            self.lines.append(("on-line", a, d, 0.0, 1.0))
            self.points.append((3, "midpoint", ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)))
            for _kind, p, e, t0, t1 in before:
                cross = plan._line_cross(a, d, p, e)
                if cross and -1e-9 <= cross[1] <= 1 + 1e-9 and t0 - 1e-9 <= cross[2] <= t1 + 1e-9:
                    self.points.append((2, "crossing", cross[0]))
        for n, (k1, i1, a, b) in enumerate(segments):
            d = (b[0] - a[0], b[1] - a[1])
            for k2, i2, c, f in segments[n + 1:]:
                if (k1, i1) == (k2, i2):
                    continue
                cross = plan._line_cross(a, d, c, (f[0] - c[0], f[1] - c[1]))
                if cross and 1e-9 < cross[1] < 1 - 1e-9 and 1e-9 < cross[2] < 1 - 1e-9:
                    self.points.append((2, "crossing", cross[0]))


# --- Rays ------------------------------------------------------------------------------


def polar_rays(anchor):
    """The eight rays from `anchor`, as {anchor, angle, unit}: the angle in degrees from +x towards +y (down the page), the unit vector its direction."""
    out = []
    for angle in POLAR_ANGLES:
        radians = math.radians(angle)
        out.append({"anchor": (float(anchor[0]), float(anchor[1])), "angle": float(angle), "unit": (math.cos(radians), math.sin(radians))})
    return out


def _clean(value):
    """A coordinate without the dust of a cosine -- 6.1e-17 is 0, 200.00000000000003 is 200 -- to a billionth of a sheet unit, far below what a click can place."""
    return round(value, 9) + 0.0


def _foot(ray, point):
    """(along, perpendicular distance) of `point` from the ray's line."""
    dx, dy = point[0] - ray["anchor"][0], point[1] - ray["anchor"][1]
    u = ray["unit"]
    return dx * u[0] + dy * u[1], abs(dx * u[1] - dy * u[0])


def locked_rays(anchors, point, tolerance):
    """The rays through `anchors` the pointer is within `tolerance` of, as (distance, ray), the nearest first. A ray is the half-line from its anchor, so a pointer behind the anchor is on the opposite ray, not this one, and a pointer on the anchor itself locks nothing."""
    out = []
    for anchor in anchors:
        if math.dist(anchor, point) <= tolerance * 0.5:
            continue
        for ray in polar_rays(anchor):
            along, perp = _foot(ray, point)
            if along > tolerance * 0.5 and perp <= tolerance:
                out.append((perp, ray))
    return sorted(out, key=lambda item: item[0])


def project(ray, point):
    """`point` projected onto the ray's line."""
    along, _perp = _foot(ray, point)
    return (ray["anchor"][0] + along * ray["unit"][0], ray["anchor"][1] + along * ray["unit"][1])


def along(ray, distance):
    """The point `distance` sheet units from the ray's anchor along it."""
    return (ray["anchor"][0] + distance * ray["unit"][0], ray["anchor"][1] + distance * ray["unit"][1])


def typed_point(ray, text, per_m=None):
    """Where a distance typed into the field lands on `ray`, or None where it is not a number. The distance is in metres where the plan has a scale (`per_m`, sheet units per metre), else in sheet units. A comma is read as a decimal point."""
    try:
        distance = float(str(text).strip().replace(",", "."))
    except (TypeError, ValueError):
        return None
    if not math.isfinite(distance):
        return None
    return along(ray, distance * (per_m or 1.0))


def distance_text(ray, point, per_m=None):
    """The distance from the ray's anchor to `point` as the field shows it: in metres with a scale, else in sheet units, to two decimals and without trailing zeros."""
    d = math.dist(ray["anchor"], point) / (per_m or 1.0)
    text = f"{d:.2f}".rstrip("0").rstrip(".")
    return text or "0"


def track(index, anchors, point, tolerance):
    """Where the pointer is, tracking from `anchors` -- the one call a canvas makes on every movement of the mouse. `index` is a plan.SnapIndex (or PlanSnapIndex), `anchors` the points to track from, the newest first (the last point of what is being drawn, then the acquired ones).

    Returns {point, kind, rays}: `kind` one of plan.SNAP_KINDS or TRACK_KINDS or None, `rays` the rays the pointer is locked to -- none, one, or the two whose crossing it is on. What is preferred, in this order: a **point** of the plan within reach, which beats every ray -- a click lands exactly on a corner or not at all; **where two rays of two anchors cross**; where a ray crosses a **line** of the plan (an axis, a wall, a storey edge) or passes through a point of the plan; the **ray** itself; and last what snapping a point onto a line gives. A pointer on a wall that no ray crosses there stays on the wall."""
    p, kind = index.snap(point, tolerance)
    if kind in HARD_KINDS:
        return {"point": p, "kind": kind, "rays": []}
    locked = locked_rays(anchors, point, tolerance)
    if not locked:
        return {"point": p, "kind": kind, "rays": []}

    # where two rays of two anchors cross
    for n, (_pa, a) in enumerate(locked):
        for _pb, b in locked[n + 1:]:
            if a["anchor"] == b["anchor"]:
                continue
            cross = plan._line_cross(a["anchor"], a["unit"], b["anchor"], b["unit"])
            if cross is None or cross[1] <= 0 or cross[2] <= 0:
                continue
            if math.dist(cross[0], point) <= tolerance * 2:
                return {"point": (_clean(cross[0][0]), _clean(cross[0][1])), "kind": "track-crossing", "rays": [a, b]}

    ray = locked[0][1]
    projected = project(ray, point)
    # a point of the plan on the ray, or the ray crossing a line of the plan, close to where the pointer is
    best = None
    for priority, point_kind, c in index.points:
        _t, perp = _foot(ray, c)
        if perp <= tolerance * 0.5 and math.dist(c, projected) <= tolerance * 3:
            rank = (priority, math.dist(c, projected))
            if best is None or rank < best[0]:
                best = (rank, c, point_kind)
    if best is not None:
        return {"point": tuple(best[1]), "kind": best[2], "rays": [ray]}
    for _line_kind, q, e, t0, t1 in index.lines:
        cross = plan._line_cross(ray["anchor"], ray["unit"], q, e)
        if cross is None or cross[1] <= 0 or not t0 - 1e-9 <= cross[2] <= t1 + 1e-9:
            continue
        if math.dist(cross[0], projected) <= tolerance * 3:
            return {"point": (_clean(cross[0][0]), _clean(cross[0][1])), "kind": "track-line", "rays": [ray]}
    if kind in LINE_KINDS:
        return {"point": p, "kind": kind, "rays": []}   # on a wall no ray crosses here: the wall holds the pointer
    return {"point": (_clean(projected[0]), _clean(projected[1])), "kind": "track", "rays": [ray]}


def acquire(acquired, point, limit=MAX_ACQUIRED):
    """`acquired` with `point` put first, the oldest dropped past `limit`; a point already acquired just moves to the front."""
    point = (float(point[0]), float(point[1]))
    kept = [q for q in acquired if math.dist(q, point) > 1e-6]
    return ([point] + kept)[:limit]
