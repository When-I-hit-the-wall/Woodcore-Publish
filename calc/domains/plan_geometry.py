"""The geometry of a position plan -- lengths, areas and centroids, the axes and their names, what a click hits, the index the pointer snaps against -- split out of calc/domains/plan.py (issue #30), moved verbatim: what the plans' canvas asks while it draws and what the quantities measure. plan.py imports every name back. Qt-free.
"""

import math
import re
from domains.dimension import _inside, constrain  # plane geometry written once (D4)


# Points per metre on paper, for a PDF plotted at 1:n: 72 pt per inch, 25.4 mm per inch.
PT_PER_M = 72.0 / 25.4 * 1000.0


# The STE symbols (STE Compact 02, «Plandarstellung im Holzbau»), by the letter that is also the first character of a position's number. `geo` is the shape drawn: a polyline, a point or a polygon; `points`, where the type fixes it, how many points its element has -- a beam and a bracing member are single straight members, drawn from one end to the other, where a wall may turn a corner; `z` the drawing order, areas under lines and points on top; `labelled` whether it carries a position number (an opening and a concrete wall do not). `names` are those of Positionen.xlsx's data_type sheet, by subtype, used where a missing position is offered for pasting into the Positions Element sheet.
TYPES = {
    "V": {"geo": "line", "z": 3, "names": {None: "vertikal tragende Wand"}},
    "H": {"geo": "line", "z": 3, "names": {None: "aussteifende Wand"}},
    "W": {"geo": "line", "z": 3, "names": {None: "vertikal tragende und aussteifende Wand"}},
    "T": {"geo": "line", "points": 2, "z": 3, "names": {None: "Träger"}},
    "S": {"geo": "point", "z": 4, "names": {None: "Stütze"}},
    "A": {"geo": "line", "points": 2, "z": 3, "names": {None: "Aussteifung, Stabilisierung Einzelstab"}},
    "D": {"geo": "poly", "z": 2, "subtypes": ("scheibe", "normal"),
          "names": {"scheibe": "Scheibenbildung Decke/Dach", "normal": "Decke/Dach"}},
    "M": {"geo": "line", "z": 3, "subtypes": ("vert", "horiz", "vh"),
          "names": {"vert": "vertikal wirkendes Auflager", "horiz": "horizontal wirkendes Auflager",
                    "vh": "vertikal und horizontal wirkendes Auflager"}},
    "L": {"geo": "line", "z": 3, "subtypes": ("linie", "punkt"),
          "names": {"linie": "Abfangung Linienlast von oben", "punkt": "Abfangung Punktlast von oben"}},
    "Ö": {"geo": "poly", "z": 1, "labelled": False, "names": {None: "Ausschnitt/Öffnung"}},
    "B": {"geo": "poly", "z": 0, "labelled": False, "subtypes": ("wand", "decke"),
          "names": {"wand": "Betonwand", "decke": "Betondecke"}},
    # The load-path plan's six symbols (v0.116, STE Compact 02 pp. 14-15): a point load and a line load, each vertical (orange), horizontal (violet) or both. They are loads and not positions: their numbers (Pxxx, Lxxx: `prefix`, the floor's character, two digits) are the plan's own, proposed one after another (next_load_label), never a position of positions.json -- so they are in no list of positions, no check against the project, and only on a load-path plan.
    "PL": {"geo": "point", "z": 5, "load": True, "prefix": "P", "subtypes": ("vert", "horiz", "vh"),
           "names": {"vert": "Punktlast vertikal", "horiz": "Punktlast horizontal", "vh": "Punktlast vertikal und horizontal"}},
    "LL": {"geo": "line", "z": 3, "load": True, "prefix": "L", "subtypes": ("vert", "horiz", "vh"),
           "names": {"vert": "Linienlast vertikal", "horiz": "Linienlast horizontal", "vh": "Linienlast vertikal und horizontal"}},
}


def _clean(value):
    """A number as it is saved: six decimals at most, -0 as 0, a whole float as an int."""
    value = round(float(value), 6) + 0.0
    return int(value) if value.is_integer() else value


def labelled(type_):
    return TYPES[type_].get("labelled", True)


def is_load(type_):
    """Whether an element of this type is one of the load-path plan's load symbols (PL, LL) -- numbered by the plan, not a position."""
    return bool(TYPES.get(type_, {}).get("load"))


def next_load_label(source, type_):
    """The number a load symbol drawn on this plan is given: its letter (P a point load, L a line load), the plan's floor character and the next free two-digit number among the plan's own load symbols of that letter -- PU01, P001, L101 -- so that each one drawn gets the next. The engineer may write another over it (free text)."""
    prefix = TYPES[type_]["prefix"] + (source.get("floor") or "")
    used = []
    for element in source.get("elements", []):
        label = element.get("label", "")
        if is_load(element.get("type")) and TYPES[element["type"]]["prefix"] == TYPES[type_]["prefix"] and label.startswith(prefix):
            rest = label[len(prefix):]
            if rest.isdigit():
                used.append(int(rest))
    return f"{prefix}{(max(used) + 1 if used else 1):02d}"


def default_subtype(type_):
    subtypes = TYPES[type_].get("subtypes")
    return subtypes[0] if subtypes else None


def element_kind(element):
    """The shape an element is drawn as: `line`, `point` or `poly`. An Abfangung is a point load when its subtype says so, and an Auflager a point when it was placed with one click -- the other types' shape is their type's."""
    type_ = element["type"]
    geo = TYPES[type_]["geo"]
    if geo == "point":
        return "point"
    if type_ == "L" and element.get("subtype") == "punkt":
        return "point"
    if type_ == "M" and len(element.get("points", [])) == 1:
        return "point"
    return geo


MIN_POINTS = {"point": 1, "line": 2, "poly": 3}


def units_per_m(source):
    """Sheet units per metre of the building, or None for a plan without a scale: from 1:n for a PDF, whose points are paper; from the two points and the length of a calibration otherwise."""
    scale = source.get("scale")
    if not scale:
        return None
    if scale.get("mode") == "ratio" and scale.get("ratio"):
        return PT_PER_M / float(scale["ratio"])
    if scale.get("mode") == "calibration" and scale.get("length_m"):
        a, b = scale["points"]
        return math.dist(a, b) / float(scale["length_m"])
    return None


# What has a length written beside it, the plan's `show_lengths` on, or the element's own `show_length`: the walls, the beams and the slabs, a slab side by side (the engineer, 07.10.2026: «longueur de chaque mur, chaque T, longueur de chaque côté de dale»).
LENGTH_TYPES = ("V", "H", "W", "T", "D")


def shows_length(source, element):
    """Whether `element`'s length is written beside it: its own `show_length` where it has one, else the plan's `show_lengths` -- for a wall, a beam or a slab on a plan with a scale, never otherwise."""
    if element.get("type") not in LENGTH_TYPES or not units_per_m(source):
        return False
    if "show_length" in element:
        return bool(element["show_length"])
    return bool(source.get("show_lengths"))


def ring_area(ring):
    """The surface an outline encloses, in its own units squared (fire.py's zones and a slab's outline alike)."""
    total = 0.0
    for i in range(len(ring)):
        (x1, y1), (x2, y2) = ring[i - 1], ring[i]
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


def legend_key(element):
    """The legend line an element is listed under: its type, or its type and the subtype that changes its symbol (D:scheibe)."""
    type_, subtype = element["type"], element.get("subtype")
    if TYPES[type_].get("subtypes"):
        return f"{type_}:{subtype or default_subtype(type_)}"
    return type_


def quantities(source):
    """The plan's quantities by legend line (the engineer, 07.10.2026: «dans légende … sous le descriptif des symboles, les métrés totaux par type d'objet»): {key: {"value", "unit"}} -- a line drawn summed in metres, an area in square metres, a point counted. Empty without a scale: nothing is measured on a plan that has none. Rounded to the centimetre and the hundredth of a square metre, as the lengths beside the walls are written."""
    per_m = units_per_m(source)
    if not per_m:
        return {}
    totals = {}
    for element in source.get("elements", []):
        points = element.get("points") or []
        kind = element_kind(element)
        if len(points) < MIN_POINTS[kind]:
            continue
        key = legend_key(element)
        if kind == "line":
            value, unit = element_length_m(element, per_m), "m"
        elif kind == "poly":
            value, unit = ring_area(points) / (per_m * per_m), "m2"
        else:
            value, unit = 1, "pcs"
        entry = totals.setdefault(key, {"value": 0, "unit": unit})
        entry["value"] += value
    for entry in totals.values():
        entry["value"] = round(entry["value"], 2) if entry["unit"] != "pcs" else int(entry["value"])
    return totals


def polyline_length(points, closed=False):
    total = sum(math.dist(points[i - 1], points[i]) for i in range(1, len(points)))
    if closed and len(points) > 2:
        total += math.dist(points[-1], points[0])
    return total


# The one measure of a length on a plan (issue #9): the drawing, the export, the quantities, the ruler and the dimensions all read these, so a wall cannot be 4.12 m beside it and 4.13 m in a total.
def distance_m(a, b, per_m):
    """The real distance between two sheet points, in metres, on a plan of `per_m` sheet units per metre (`units_per_m`)."""
    return math.dist(a, b) / per_m


def element_length_m(element, per_m):
    """An element's length in metres -- a line's along its points, an area's perimeter --, or None for a point, or where the plan has no scale (`per_m` None)."""
    kind = element_kind(element)
    if not per_m or kind == "point":
        return None
    return polyline_length(element["points"], closed=kind == "poly") / per_m


def metres_text(value):
    """A length as the plan writes it beside an element: «4.25 m», to the centimetre, the decimal a point in every language."""
    return f"{value:.2f} m"


def centroid(points):
    """A polygon's area centroid -- not the mean of its corners, which an L-shaped slab would pull off its middle; the mean for a degenerate one."""
    area = cx = cy = 0.0
    n = len(points)
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        cross = x1 * y2 - x2 * y1
        area += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    if abs(area) < 1e-12:
        return (sum(p[0] for p in points) / n, sum(p[1] for p in points) / n)
    return (cx / (3 * area), cy / (3 * area))


def bbox(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def default_span(points):
    """A slab spans its short side unless the engineer says otherwise: an arrow at 90° (down the page) across a wide slab, at 0° across a tall one."""
    x0, y0, x1, y1 = bbox(points)
    return 90 if x1 - x0 >= y1 - y0 else 0


def line_in_polygon(point, direction, polygon):
    """The pieces of the line through `point` along `direction` that lie inside `polygon`, as segments -- the crossings sorted along the line and paired, even-odd, so a concave outline gets several pieces. Used for a slab's diagonals and a concrete wall's hatching, which SVG Tiny cannot clip."""
    ts = []
    n = len(polygon)
    for i in range(n):
        a, b = polygon[i], polygon[(i + 1) % n]
        ex, ey = b[0] - a[0], b[1] - a[1]
        den = direction[0] * ey - direction[1] * ex
        if abs(den) < 1e-12:
            continue
        ax, ay = a[0] - point[0], a[1] - point[1]
        s = (ax * direction[1] - ay * direction[0]) / den
        if s < 0 or s >= 1:
            continue
        ts.append((ax * ey - ay * ex) / den)
    ts.sort()
    segments = []
    for i in range(0, len(ts) - 1, 2):
        p = (point[0] + direction[0] * ts[i], point[1] + direction[1] * ts[i])
        q = (point[0] + direction[0] * ts[i + 1], point[1] + direction[1] * ts[i + 1])
        if math.dist(p, q) > 1e-9:
            segments.append((p, q))
    return segments


def axis_direction(axis):
    a = math.radians(float(axis["angle"]))
    return (math.cos(a), math.sin(a))


def axis_normal(axis):
    """The side an axis is offset to by a positive distance: right for a vertical axis, down for a horizontal one, and for an oblique one the side to the right."""
    dx, dy = axis_direction(axis)
    nx, ny = dy, -dx
    if nx < -1e-9 or (abs(nx) <= 1e-9 and ny < 0):
        nx, ny = -nx, -ny
    return (nx, ny)


def axis_segment(axis, window):
    """Where an axis crosses `window` ({x, y, w, h}): (start, end), start being the top of a vertical axis and the left of a horizontal one; None where it misses the window. An axis is a line without ends: the frame shown decides where it is drawn."""
    px, py = axis["point"]
    dx, dy = axis_direction(axis)
    # start at the top (a vertical axis) or at the left: its direction turned that way
    if dx < -1e-9 or (abs(dx) <= 1e-9 and dy < 0):
        dx, dy = -dx, -dy
    if abs(dx) <= 1e-9:
        dx, dy = 0.0, 1.0
    t0, t1 = -math.inf, math.inf
    for d, p, lo, hi in ((dx, px, window["x"], window["x"] + window["w"]), (dy, py, window["y"], window["y"] + window["h"])):
        if abs(d) < 1e-12:
            if p < lo or p > hi:
                return None
            continue
        a, b = (lo - p) / d, (hi - p) / d
        t0, t1 = max(t0, min(a, b)), min(t1, max(a, b))
    if t1 - t0 <= 1e-9:
        return None
    return (px + dx * t0, py + dy * t0), (px + dx * t1, py + dy * t1)


def axis_distance(a, b, per_m):
    """The distance from axis a to a parallel axis b, in metres, positive when b lies on a's positive side (axis_normal); None when they are not parallel or there is no scale."""
    if not per_m or abs(math.sin(math.radians(float(a["angle"]) - float(b["angle"])))) > 1e-6:
        return None
    nx, ny = axis_normal(a)
    return ((b["point"][0] - a["point"][0]) * nx + (b["point"][1] - a["point"][1]) * ny) / per_m


def parallel_axis(axis, distance_m, per_m, label):
    """A new axis parallel to `axis`, `distance_m` metres to its positive side."""
    nx, ny = axis_normal(axis)
    d = distance_m * per_m
    return {"label": label, "point": [_clean(axis["point"][0] + nx * d), _clean(axis["point"][1] + ny * d)],
            "angle": axis["angle"], "bubbles": axis.get("bubbles", "both")}


def _letters(n):
    """1 -> A, 26 -> Z, 27 -> AA."""
    text = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        text = chr(65 + r) + text
    return text


def axis_scheme(label):
    """How an axis is named: `letters` (A, B, …, Z, AA), `numbers` (1, 2, …), or None for any other name (C', 2a, X3) -- which the numbering of new axes leaves alone."""
    if re.fullmatch(r"[A-Z]+", label or ""):
        return "letters"
    if re.fullmatch(r"[1-9][0-9]*", label or ""):
        return "numbers"
    return None


def _axis_ordinal(label, scheme):
    """A → 1, AA → 27; "12" → 12."""
    if scheme == "numbers":
        return int(label)
    n = 0
    for ch in label:
        n = n * 26 + ord(ch) - 64
    return n


def _axis_name(n, scheme):
    return str(n) if scheme == "numbers" else _letters(n)


def new_axis_scheme(axis):
    """The names a new axis takes: letters for one running up the plan, numbers for one running across it, and for an oblique one those of the nearer of the two."""
    a = math.fmod(abs(float(axis["angle"])), 180.0)
    return "letters" if abs(a - 90) < 45 else "numbers"


def axis_across(axis, scheme, window):
    """Where an axis lies among the others of its scheme: an axis named by a letter runs up the plan, and is placed by the x at which it crosses the middle of `window`; one named by a number runs across it, and is placed by the y at which it crosses its middle. An oblique axis is so placed by where it passes through the plan, not by the point it was clicked at."""
    cx, cy = window["x"] + window["w"] / 2, window["y"] + window["h"] / 2
    px, py = axis["point"]
    dx, dy = axis_direction(axis)
    if scheme == "letters":
        return px + (cy - py) / dy * dx if abs(dy) > 1e-9 else px
    return py + (cx - px) / dx * dy if abs(dx) > 1e-9 else py


def insert_axis(axes, axis, window):
    """Adds a new `axis` to `axes`, at the end of the list, and names it by where it lies among the axes named like it: drawn between A and B it becomes B, and B, and those after it, move up by one -- only as far as the next gap, so a name left out on purpose (A, C) stays left out, and an axis drawn in that gap simply takes it. Letters run left to right and numbers bottom to top, as on a plan, unless the axes already there run the other way. Returns the axes renamed, as [(old, new), …]. An order the axes already break (C left of A and B) is left alone: the new axis then takes the first free name, and nothing is renamed."""
    scheme = new_axis_scheme(axis)
    family = [a for a in axes if axis_scheme(a["label"]) == scheme]
    position = {id(a): axis_across(a, scheme, window) for a in family}
    here = axis_across(axis, scheme, window)

    # the way the names run: from the axes already there, or as a plan runs them -- y points down, so numbers rising up the plan fall with y
    placed = sorted(family, key=lambda a: position[id(a)])
    ordinal = {id(a): _axis_ordinal(a["label"], scheme) for a in family}
    rising = sum(ordinal[id(b)] > ordinal[id(a)] for a, b in zip(placed, placed[1:]))
    falling = sum(ordinal[id(b)] < ordinal[id(a)] for a, b in zip(placed, placed[1:]))
    sign = (1 if rising > falling else -1) if rising != falling else (1 if scheme == "letters" else -1)

    # the family in the order its names should run, the new axis after any it coincides with
    order = sorted(family, key=lambda a: sign * position[id(a)])
    tolerance = 1e-6 * max(window["w"], window["h"], 1.0)
    before = [a for a in order if sign * position[id(a)] <= sign * here + tolerance]
    after = [a for a in order if sign * position[id(a)] > sign * here + tolerance]
    taken = set(ordinal.values())
    n, moved = 1, {}
    if all(ordinal[id(b)] > ordinal[id(a)] for a, b in zip(order, order[1:])):
        if before:
            n = ordinal[id(before[-1])] + 1
        elif after:
            n = ordinal[id(after[0])] - 1
            if n < 1 or n in taken:
                n = ordinal[id(after[0])]
        # the axes after it move up as far as they must, and no further
        last = n
        for a in after:
            if ordinal[id(a)] > last:
                break
            last += 1
            moved[id(a)] = last
    else:
        while n in taken:
            n += 1

    renames = []
    for a in order:
        if id(a) in moved:
            new = _axis_name(moved[id(a)], scheme)
            renames.append((a["label"], new))
            a["label"] = new
    axis["label"] = _axis_name(n, scheme)
    axes.append(axis)
    return renames


def axis_sort_key(axis):
    """The order axes are listed in: letters, then numbers, each in its own order, then any other name."""
    scheme = axis_scheme(axis["label"])
    if scheme is None:
        return (2, 0, axis["label"])
    return (0 if scheme == "letters" else 1, _axis_ordinal(axis["label"], scheme), "")


def auto_label(type_, floor, elements=(), position_ids=()):
    """The number a type's tool draws before any element of that type has been renumbered -- after that, Woodcore's tool draws the number last given (plan_tab.py), identical elements sharing one position. Only a position of Positionen.xlsx (`position_ids`) is ever drawn: the last number of that type and of the plan's floor on this plan that the sheet has (`elements`, in the order they were drawn), so the tool goes on where the plan stops; else the sheet's first position of that type and floor; else its first of that type on another floor; else "", and Woodcore draws nothing -- the sheet has no position of this type to give. Never the next free number: the same number is drawn every time."""
    if not labelled(type_):
        return ""
    known = set(position_ids)
    if is_load(type_):
        return next_load_label({"floor": floor, "elements": list(elements)}, type_)
    prefix = type_ + (floor or "")
    for element in reversed(list(elements)):
        label = element.get("label", "")
        if element.get("type") == type_ and label.startswith(prefix) and label in known:
            return label
    for start in (prefix, type_):
        for pid in position_ids:
            if pid.startswith(start):
                return pid
    return ""


def _point_segment(p, a, b):
    """The distance from p to the segment ab, and the nearest point on it."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    length2 = dx * dx + dy * dy
    t = 0.0 if length2 < 1e-18 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / length2))
    q = (a[0] + t * dx, a[1] + t * dy)
    return math.dist(p, q), q


def segments_of(element):
    points = element["points"]
    kind = element_kind(element)
    if kind == "point":
        return []
    pairs = [(points[i - 1], points[i]) for i in range(1, len(points))]
    if kind == "poly":
        pairs.append((points[-1], points[0]))
    return pairs


def nearest_point(element, point):
    """(the point of an element nearest to `point`, its distance): the element's point itself, the nearest point of its line, or of an area's outline -- `point` itself, at 0, when it lies inside the area."""
    points = [tuple(p) for p in element["points"]]
    if element_kind(element) == "poly" and len(points) >= 3 and _inside(point, points):
        return tuple(point), 0.0
    candidates = [_point_segment(point, a, b) for a, b in segments_of(element)]
    if not candidates:
        return points[0], math.dist(point, points[0])
    distance, nearest = min(candidates)
    return nearest, distance


def hit_label(source, point, tolerance, frames=None):
    """The index of the element whose position number lies under `point` -- the one drawn last, on top, where two overlap -- or None. The numbers are drawn over every symbol, so Woodcore asks this before hit_element: a click on a number takes the number, to move it (label_offset). `frames` are plan_svg.number_frames(source), when the caller keeps them."""
    from domains import plan_svg  # where a number is drawn is the drawing module's to say

    hit = None
    for index, frame in frames if frames is not None else plan_svg.number_frames(source):
        if plan_svg.on_number(frame, point, 0.5 * tolerance):
            hit = index
    return hit


def hit_element(source, point, tolerance):
    """The index of the element under `point` -- the one drawn on top: points before lines, lines before areas, an area hit anywhere inside it -- or None."""
    best = None
    for i, element in enumerate(source.get("elements", [])):
        points = element.get("points") or []
        if not points:
            continue
        kind = element_kind(element)
        z = TYPES[element["type"]]["z"]
        if kind == "point":
            d = math.dist(point, points[0])
            hit = d <= 1.5 * tolerance
        else:
            d = min((_point_segment(point, a, b)[0] for a, b in segments_of(element)), default=math.inf)
            hit = d <= tolerance or (kind == "poly" and _inside(point, points))
            if hit and kind == "poly" and d > tolerance:
                d = tolerance  # anywhere inside an area counts, behind its own outline
        if hit:
            rank = (-(10 if kind == "point" else z), d)
            if best is None or rank < best[0]:
                best = (rank, i)
    return best[1] if best else None


def hit_axis(source, point, tolerance, window):
    """The index of the axis passing within `tolerance` of `point`, the nearest first, or None."""
    best = None
    for i, axis in enumerate(source.get("axes", [])):
        segment = axis_segment(axis, window)
        if segment is None:
            continue
        d = _point_segment(point, *segment)[0]
        if d <= tolerance and (best is None or d < best[0]):
            best = (d, i)
    return best[1] if best else None


def nearest_vertex(element, point, tolerance):
    best = None
    for j, p in enumerate(element.get("points", [])):
        d = math.dist(point, p)
        if d <= tolerance and (best is None or d < best[0]):
            best = (d, j)
    return best[1] if best else None


def _line_cross(p, d, q, e):
    """Where the line through p along d meets the line through q along e: (point, t along the first, s along the second), or None for parallel lines."""
    den = d[0] * e[1] - d[1] * e[0]
    if abs(den) < 1e-12:
        return None
    wx, wy = q[0] - p[0], q[1] - p[1]
    t = (wx * e[1] - wy * e[0]) / den
    s = (wx * d[1] - wy * d[0]) / den
    return (p[0] + t * d[0], p[1] + t * d[1]), t, s


# What a snapped point is, in the order a candidate is preferred when several are within reach.
SNAP_KINDS = ("axis-crossing", "vertex", "crossing", "midpoint", "on-axis", "on-line")


class SnapIndex:
    """Everything a point being drawn may snap to, gathered once per state of the plan rather than on every movement of the mouse: the axes' crossings, the elements' corners and middles, where an axis or a wall crosses another, and the axes and segments themselves. `axes` and `elements` are the two snapping buttons; `exclude` is the element being edited, which must not snap to itself."""

    def __init__(self, source, window, axes=True, elements=True, exclude=None):
        self.points = []  # (priority, kind, point)
        self.lines = []   # (kind, point, direction, t0, t1): an axis runs across the window, a segment from t0 = 0 to t1 = 1
        axis_lines = []
        if axes:
            for axis in list(source.get("axes", [])) + list(source.get("aids") or []):   # a construction aid snaps as an axis does (issue #18), behind the same button
                segment = axis_segment(axis, window)
                if segment is None:
                    continue
                a, b = segment
                d = (b[0] - a[0], b[1] - a[1])
                axis_lines.append((a, d))
                self.lines.append(("on-axis", a, d, 0.0, 1.0))
        segment_lines = []
        if elements:
            for i, element in enumerate(source.get("elements", [])):
                if i == exclude or not element.get("points"):
                    continue
                for p in element["points"]:
                    self.points.append((1, "vertex", tuple(p)))
                for a, b in segments_of(element):
                    d = (b[0] - a[0], b[1] - a[1])
                    segment_lines.append((tuple(a), d))
                    self.lines.append(("on-line", tuple(a), d, 0.0, 1.0))
                    self.points.append((3, "midpoint", ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)))
        for i, (p, d) in enumerate(axis_lines):
            for q, e in axis_lines[i + 1:]:
                cross = _line_cross(p, d, q, e)
                if cross and 0 <= cross[1] <= 1 and 0 <= cross[2] <= 1:
                    self.points.append((0, "axis-crossing", cross[0]))
        # a wall crossing an axis, or another wall
        for i, (p, d) in enumerate(segment_lines):
            for q, e in axis_lines + segment_lines[i + 1:]:
                cross = _line_cross(p, d, q, e)
                if cross and -1e-9 <= cross[1] <= 1 + 1e-9 and -1e-9 <= cross[2] <= 1 + 1e-9:
                    self.points.append((2, "crossing", cross[0]))

    def snap(self, point, tolerance, anchor=None, constrained=False):
        """(point, kind): `point` moved onto the best target within `tolerance` -- the kinds of SNAP_KINDS in that order of preference, the nearest among equals -- or left where it is with kind None. With `constrained` (Shift) and an `anchor`, the point first goes onto its direction of 0°, 45° or 90° from the anchor, and only a target on that ray is taken: a corner or a crossing lying on it, or where the ray meets an axis or a segment."""
        if constrained and anchor is not None:
            ray_point = constrain(anchor, point)
            d = (ray_point[0] - anchor[0], ray_point[1] - anchor[1])
            length = math.hypot(*d)
            if length < 1e-12:
                return ray_point, None
            u = (d[0] / length, d[1] / length)
            best = None
            for priority, kind, c in self.points:
                t = (c[0] - anchor[0]) * u[0] + (c[1] - anchor[1]) * u[1]
                on_ray = (anchor[0] + t * u[0], anchor[1] + t * u[1])
                if math.dist(c, on_ray) <= 1e-6 * max(1.0, tolerance) + 1e-9 and math.dist(on_ray, ray_point) <= tolerance:
                    rank = (priority, math.dist(on_ray, ray_point))
                    if best is None or rank < best[0]:
                        best = (rank, on_ray, kind)
            for kind, p, e, t0, t1 in self.lines:
                cross = _line_cross(anchor, u, p, e)
                if cross is None or not t0 - 1e-9 <= cross[2] <= t1 + 1e-9:
                    continue
                if math.dist(cross[0], ray_point) <= tolerance:
                    rank = (2 if kind == "on-axis" else 2.5, math.dist(cross[0], ray_point))
                    if best is None or rank < best[0]:
                        best = (rank, cross[0], "crossing")
            return (best[1], best[2]) if best else (ray_point, None)

        best = None
        for priority, kind, c in self.points:
            dist = math.dist(point, c)
            if dist <= tolerance:
                rank = (priority, dist)
                if best is None or rank < best[0]:
                    best = (rank, c, kind)
        if best:
            return best[1], best[2]
        for kind, p, e, t0, t1 in self.lines:
            dist, q = _point_segment(point, p, (p[0] + e[0], p[1] + e[1]))
            if dist <= tolerance:
                rank = (SNAP_KINDS.index(kind), dist)
                if best is None or rank < best[0]:
                    best = (rank, q, kind)
        return (best[1], best[2]) if best else (tuple(point), None)
