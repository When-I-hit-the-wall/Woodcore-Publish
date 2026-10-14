"""The geometry of a connection detail -- an element's outline, sides, width and caption, the aids and fasteners placed on it, the dimensions, what a click hits, what the pointer snaps and tracks to -- split out of calc/domains/schema.py (issue #30), moved verbatim: what the «Schémas» canvas asks while it draws. schema.py imports every name back. Qt-free.
"""

import math
from domains import connector, figure_style, section as position_section
from domains import dimension  # a dimension's geometry, shared with the static models and the plans (issue #9)


# A linear element's visible width: its height (the default -- "on voit leur hauteur") or its breadth.
ELEMENT_VIEWS = ("h", "b")


# An element's section, b and h in mm (v0.75). Each side FOLLOWS the element's position -- read afresh at every export off the position's `section`, «100/200» giving b = 100 and h = 200 -- unless the element states it, which is an override that stays written over through the next import (the connectors' own reference pattern, section 3.3nonies). ⚠️ The position's dimension is read once, by domains/section.py, into that `section` (v0.94, docs/domain/positions.md §7): a round section gives its diameter for both sides, a plate or a CLT panel its thickness, and a steel profile nothing -- the element then simply has no section until one is stated on it.
ELEMENT_SIDES = ("b", "h")


# A linear element's band thickness in mm while the side its view shows is still unknown -- no position, a position whose dimension is not b/h, and nothing stated. Purely a drawing default, and the export says so in a warning: a fresh element is still visible before its section is known.
ELEMENT_DEFAULT_WIDTH = 100.0


# An aid names a point (exported by default, so a dimension or a connector may address it) or a construction line (not exported unless `shown`). The five line kinds all resolve to one point-plus-angle shape when they are drawn -- which of the five it was only changes how the tool computed that angle and which icon it drew with, so a schema does not have to keep a 'perpendicular' aid living relative to a reference that might later move.
AID_POINT_KINDS = ("centre", "point")


AID_ANGLE_KINDS = ("vertical", "horizontal", "point-angle", "perpendicular", "parallel")


AID_TWO_POINT_KINDS = ("two-points",)


DIMENSION_UNITS = {"horizontal": "mm", "vertical": "mm", "parallel": "mm", "angle": "°"}


# What a dimension writes beside itself -- statics.py's own four (its LABEL_MODES, a load's), restated rather than imported as the kinds above are: nothing, its name (its `label`), what it measured, or both. tests/test_schema.py holds the two equal.
LABEL_MODES = ("none", "name", "value", "name+value")


# Two members whose axes are this near to parallel have no crossing to turn an angle about -- statics.py's own tolerance.
PARALLEL_TOLERANCE = 1e-6


# Two points closer than this, in mm, are one point typed twice -- a tenth of a millimetre.
SAME_POINT = 0.1


# The directions the cursor locks to, in degrees from +x -- statics.py's eight, unchanged.
TRACK_ANGLES = (0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0)


TRACK_TOLERANCE_DEG = 4.0


# The snap targets, in the order one is preferred over another at equal distance.
SNAP_KINDS = ("point", "midpoint", "crossing", "on-line", "grid")


# At most this many decimals wherever this module writes a number as text, trailing zeros dropped -- connection_svg.py's and connector_svg.py's own precision for a millimetre figure (their _f()), so the schema, the connector and the polar-moment drawings agree on how a number looks.
DIGITS = 2


# An angle is written to a tenth of a degree, as show-polar-moment writes its force-grain angles.
ANGLE_DIGITS = 1


def fmt_number(value, digits=DIGITS):
    """A number as the figure writes it: at most `digits` decimals, trailing zeros dropped (4.9788 -> 4.98, 3.50 -> 3.5, 20 -> 20) -- statics.py's fmt_number, in mm's own precision."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return str(value)
    text = f"{value:.{digits}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def figure_number(value, digits=DIGITS):
    """A number as the figure *prints* it -- statics.py's figure_number: `fmt_number` with the real minus U+2212 for its sign, never a hyphen. For text set on the figure only; a cell Woodcore reads back keeps `fmt_number`."""
    text = fmt_number(value, digits)
    return "−" + text[1:] if text.startswith("-") else text


def normalize_angle(degrees):
    """An angle in degrees, brought into (-180, 180]."""
    a = math.fmod(degrees, 360.0)
    if a <= -180:
        a += 360
    elif a > 180:
        a -= 360
    return a


def index_of(source, collection, eid):
    for i, entry in enumerate(source.get(collection, [])):
        if entry.get("id") == eid:
            return i
    return None


def entry_of(source, collection, eid):
    i = index_of(source, collection, eid)
    return source[collection][i] if i is not None else None


def element_kind(element):
    return element.get("kind")


def segments_of(element):
    """The consecutive pairs of an element's points -- a linear element's polyline, or an area element's polygon closed back onto its first point. plan.py's segments_of, ported: that one reads element_kind(element) off plan.TYPES, which a schema element has none of."""
    points = [tuple(p) for p in element.get("points", [])]
    if len(points) < 2:
        return []
    pairs = [(points[i - 1], points[i]) for i in range(1, len(points))]
    if element_kind(element) == "area":
        pairs.append((points[-1], points[0]))
    return pairs


def element_direction(element):
    """The unit vector from an element's first point towards its last -- a straight 2-point element's own axis, and a polyline's overall direction otherwise (its bends are not turned about for an angle dimension). None for one of no length."""
    points = element.get("points", [])
    if len(points) < 2:
        return None
    a, b = points[0], points[-1]
    length = math.dist(a, b)
    if length <= SAME_POINT:
        return None
    return ((b[0] - a[0]) / length, (b[1] - a[1]) / length)


def position_records(positions):
    """{id: record} from whatever a caller holds of the positions: the records themselves (export_all.py's, `connector.known_positions`'), a list of ids (which exist, and nothing of what they hold), or None (nothing exported yet, so none resolves)."""
    if positions is None:
        return {}
    if isinstance(positions, dict):
        return positions
    return {pid: {} for pid in positions}


def _stated(value):
    return value is not None and not isinstance(value, bool) and isinstance(value, (int, float)) and value > 0


def element_section(element, positions=None):
    """An element's section as the export and Woodcore's window read it: {b, h, b_from, h_from, position, resolved, position_b, position_h, material, strength_class, dimension, units, section_text, section_type}.

    A side the element states is `"stated"` and wins -- an override, and one that stays written over when Positionen.xlsx changes; a side it does not state is `"position"` where its position's dimension reads as b/h; else it is None -- a side being the position's section read by domains/section.py: a rectangle's b and h, a round section's d, a plate's or a CLT panel's t, and nothing for a steel profile. `position_b`/`position_h` are what the position holds whatever the element says, which is what Woodcore's orange line names beside a side written over.

    ⚠️ A draft still shaped as 1.0 -- an element carrying `width` and not yet through `upgrade_source` -- is read the way the upgrade would read it, so that nothing drawn before a save comes out a different size after it.
    """
    records = position_records(positions)
    pid = (element.get("position") or "").strip()
    record = records.get(pid) if pid else None
    # the section domains/section.py read at the export -- or, for a record exported before v0.94, the one its dimension reads as by the same reader
    held = position_section.sides(record) if record else None
    shape = position_section.of_record(record) if record else None
    out = {
        "position": pid,
        "resolved": record is not None,
        "position_b": held[0] if held else None,
        "position_h": held[1] if held else None,
        "material": ((record or {}).get("material") or "").strip(),
        # the strength class, which is what the label prints («T001 C24 100/200») -- `material` is what the piece is made of since the sheet gained a `resistance class` column
        "strength_class": connector.strength_class_of(record) if record else "",
        "dimension": str((record or {}).get("dimension") or "").strip(),
        "units": ((record or {}).get("units") or "").strip(),
        # what the summaries print of the position's section, «Ø 200 mm», «ROR 101.6×10» -- its dimension as typed where it has none
        "section_text": position_section.display(record) if record else "",
        "section_type": (shape or {}).get("type", ""),
    }
    legacy_side = element.get("view", "h") if "width" in element and element_kind(element) == "linear" else None
    for index, side in enumerate(ELEMENT_SIDES):
        stated = element.get(side)
        if not _stated(stated) and side == legacy_side and _stated(element.get("width")):
            stated = element["width"]
        if _stated(stated):
            out[side], out[f"{side}_from"] = float(stated), "stated"
        elif held:
            out[side], out[f"{side}_from"] = held[index], "position"
        else:
            out[side], out[f"{side}_from"] = None, None
    return out


def element_width(element, positions=None):
    """A linear element's band thickness in mm: the side of its section its view shows -- h for «h», b for «b» -- stated on it or followed from its position, and ELEMENT_DEFAULT_WIDTH only while that side is unknown. Meaningless for an area element, which has no band."""
    section = element_section(element, positions)
    side = element.get("view", "h") if element.get("view", "h") in ELEMENT_VIEWS else "h"
    value = section[side]
    return float(value) if value else ELEMENT_DEFAULT_WIDTH


def element_caption(element, positions=None):
    """What is written on an element: its own `label` where it states one, else **its position, the position's strength class and its section** -- «T001 C24 100/200», the engineer's own words for it (v0.75).

    The section is the element's own b/h, so a side written over shows as written. Where its position's section is not a rectangle -- a round section, a plate, a CLT panel, a steel profile -- and nothing is written over, it is that section's own text, «S003 GL24h Ø 200 mm», «S002 S355 ROR 101.6×10», b/h over a diameter or a thickness saying something the position does not; and where the position has no section at all, its `dimension` as the workbook has it (a panel's «180»). A position the export no longer lists is named alone; an element naming none is named by its id, with its section where it states one.
    """
    label = (element.get("label") or "").strip()
    if label:
        return label
    section = element_section(element, positions)
    parts = [section["position"] or element.get("id", "")]
    if section["resolved"] and section["strength_class"]:
        parts.append(section["strength_class"])
    followed = section["b_from"] != "stated" and section["h_from"] != "stated"
    if section["resolved"] and followed and section["section_type"] not in ("", "rec") and section["section_text"]:
        parts.append(section["section_text"])
    elif section["b"] is not None and section["h"] is not None:
        parts.append(f"{fmt_number(section['b'])}/{fmt_number(section['h'])}")
    elif section["resolved"] and section["section_text"]:
        parts.append(section["section_text"] if section["section_type"] else section["dimension"])
    return " ".join(part for part in parts if part)


def element_middle(element):
    """The middle of an element's length -- ((x, z), the unit direction of the segment it falls on) -- where its label is set. ⚠️ Not `points[len(points) // 2]`, which is what v0.72 to v0.74 used: on a two-point element that is its END, so every beam's number sat at its far end."""
    points = [(float(p[0]), float(p[1])) for p in element.get("points", [])]
    if not points:
        return (0.0, 0.0), None
    if len(points) == 1:
        return points[0], None
    lengths = [math.dist(points[i - 1], points[i]) for i in range(1, len(points))]
    half = sum(lengths) / 2.0
    for i, length in enumerate(lengths):
        if half <= length or i == len(lengths) - 1:
            a, b = points[i], points[i + 1]
            t = 0.0 if length <= 1e-12 else min(half / length, 1.0)
            direction = None if length <= SAME_POINT else ((b[0] - a[0]) / length, (b[1] - a[1]) / length)
            return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])), direction
        half -= length
    return points[-1], None


def element_bbox(element):
    points = element.get("points", [])
    if not points:
        return None
    xs = [p[0] for p in points]
    zs = [p[1] for p in points]
    return (min(xs), min(zs), max(xs), max(zs))


def bbox(source):
    """The schema's own extent, (x0, z0, x1, z1) -- every element's points and every connector marker. None for a schema with nothing drawn yet. What *Ajuster* fits and what the drawing's symbol size is derived from; the drawing's own frame is larger, and is schema_svg's to compute."""
    xs, zs = [], []
    for element in source.get("elements", []):
        for p in element.get("points", []):
            xs.append(float(p[0]))
            zs.append(float(p[1]))
    for marker in source.get("connectors", []):
        xs.append(float(marker["x"]))
        zs.append(float(marker["z"]))
    if not xs:
        return None
    return (min(xs), min(zs), max(xs), max(zs))


def aid_point(aid):
    """A point-shaped aid's own place, or None for a line-shaped one."""
    if aid.get("kind") in AID_POINT_KINDS:
        return (float(aid["x"]), float(aid["z"]))
    return None


def aid_line(aid):
    """A line-shaped aid as (point, unit direction), or None for a point-shaped one. The five angle kinds share one shape once drawn (module docstring); 'two-points' is turned into the same shape here."""
    kind = aid.get("kind")
    if kind in AID_ANGLE_KINDS:
        a = math.radians(float(aid.get("angle", 0.0)))
        return (float(aid["x"]), float(aid["z"])), (math.cos(a), math.sin(a))
    if kind in AID_TWO_POINT_KINDS:
        p, q = (float(aid["x1"]), float(aid["z1"])), (float(aid["x2"]), float(aid["z2"]))
        length = math.dist(p, q)
        if length <= SAME_POINT:
            return None
        return p, ((q[0] - p[0]) / length, (q[1] - p[1]) / length)
    return None


def named_point(source, pid):
    """An aid point's coordinates by id -- what a dimension's {"point": id} anchor, and a connector marker placed on it, resolve against. None where the schema has no such aid, or the aid is not point-shaped."""
    aid = entry_of(source, "aids", pid)
    return None if aid is None else aid_point(aid)


def fastener_places(detail):
    """{id: (x, z)} of everything in a schema a calculation may take as a fastener: its **connector markers, then the construction points ticked «connecteur»** (aids of kind `point` carrying `connector: true`), in the schema's own order. The one list every module reads -- *Connecteurs* and *Moments polaires* alike (v0.77, the engineer: «des points doivent toujours pouvoir être repris par d'autres modules»).

    A point left unticked is a point to draw by, and is not offered. A centre is not offered either: it is what a rotation centre is chosen from. What kind of fastener sits on a place does not enter here: a polar moment has no use for it, and a connector's calculation reads its own `type`, never a marker's kind. Ids are unique across a schema's collections, so a marker and a point never share one.
    """
    places = {}
    for marker in (detail or {}).get("connectors", []):
        places[marker.get("id")] = (marker["x"], marker["z"])
    for aid in (detail or {}).get("aids", []):
        if aid.get("kind") == "point" and aid.get("connector"):
            places[aid.get("id")] = (aid["x"], aid["z"])
    return places


def default_fasteners(detail):
    """What a new calculation on `detail` ticks: every connector marker, or -- on a schema that carries none -- every point ticked «connecteur». Never both: a marker drawn on a point would be counted twice."""
    markers = [m["id"] for m in (detail or {}).get("connectors", [])]
    points = [a["id"] for a in (detail or {}).get("aids", []) if a.get("kind") == "point" and a.get("connector")]
    return markers or points


def _anchor_ref(anchor):
    """(id, kind) of an angle dimension's end -- 'element' or 'aid', whichever it names -- or (None, None)."""
    anchor = anchor or {}
    for key in ("element", "aid"):
        if anchor.get(key):
            return anchor[key], key
    return None, None


def _direction_of(source, kind, eid):
    """A named direction's own point-on-it and unit vector, for a ref used by an angle dimension: an element's (its element_direction, anchored at its first point) or a line-shaped aid's (its aid_line)."""
    if kind == "element":
        element = entry_of(source, "elements", eid)
        if element is None:
            return None
        u = element_direction(element)
        points = element.get("points", [])
        return None if u is None or not points else (tuple(points[0]), u)
    if kind == "aid":
        aid = entry_of(source, "aids", eid)
        return None if aid is None else aid_line(aid)
    return None


def dimension_anchor(source, anchor):
    """Where one end of a dimension is, in mm. `{"point": "A1"}` follows that aid as it is moved; `{"x": .., "z": ..}` stays where it was put. None where it names an aid the schema no longer has."""
    if not isinstance(anchor, dict):
        return None
    if anchor.get("point"):
        return named_point(source, anchor["point"])
    if "x" in anchor and "z" in anchor:
        return (float(anchor["x"]), float(anchor["z"]))
    return None


def dimension_ends(source, dim):
    """A linear dimension's two ends, in mm, or None where either is unresolvable."""
    a = dimension_anchor(source, dim.get("from"))
    b = dimension_anchor(source, dim.get("to"))
    return None if a is None or b is None else (a, b)


def _midpoint(a, b):
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def dimension_direction(source, dim):
    """The direction a linear dimension's line runs in, and the direction its offset is measured along."""
    kind = dim.get("kind")
    if kind in ("horizontal", "vertical"):
        return dimension.direction(kind, None, None, SAME_POINT)
    ends = dimension_ends(source, dim)
    return None if ends is None else dimension.direction(kind, ends[0], ends[1], SAME_POINT)


def dimension_line(source, dim):
    """Where a linear dimension's line is drawn, in mm: the two ends projected onto it, `offset` from the middle of the two ends."""
    ends = dimension_ends(source, dim)
    if ends is None:
        return None
    return dimension.line(dim.get("kind"), ends[0], ends[1], dim.get("offset", 0.0), SAME_POINT)


def _member_ray(source, kind, eid, centre, u):
    """The ray of a direction that runs from `centre` towards the referenced thing's own body, as (dx, dz) -- statics.py's _member_ray, ported. An element has a body (its points) to point towards; a construction line does not, and is returned as it is."""
    if kind != "element":
        return u
    element = entry_of(source, "elements", eid)
    points = element.get("points", []) if element else []
    if not points:
        return u
    xs = [p[0] for p in points]
    zs = [p[1] for p in points]
    middle = ((min(xs) + max(xs)) / 2.0, (min(zs) + max(zs)) / 2.0)
    reach = (middle[0] - centre[0], middle[1] - centre[1])
    along = reach[0] * u[0] + reach[1] * u[1]
    return (-u[0], -u[1]) if along < 0 else u


def dimension_corner(source, dim):
    """Where an angle dimension's two directions cross, in mm, with each one's own direction. None where either is unresolvable or the two are parallel."""
    fid, fkind = _anchor_ref(dim.get("from"))
    tid, tkind = _anchor_ref(dim.get("to"))
    first = _direction_of(source, fkind, fid)
    second = _direction_of(source, tkind, tid)
    if first is None or second is None:
        return None
    (a, u), (b, v) = first, second
    return dimension.crossing(a, u, b, v, PARALLEL_TOLERANCE)


def angle_rays(source, dim):
    """The two rays an angle dimension's arc runs between, and the corner they turn about -- statics.py's angle_rays, ported (its own docstring on `bearing` applies unchanged: a stored direction is not a ray of the corner by itself)."""
    corner = dimension_corner(source, dim)
    if corner is None:
        return None
    centre, u, v = corner
    bearing = dim.get("bearing")
    fid, fkind = _anchor_ref(dim.get("from"))
    tid, tkind = _anchor_ref(dim.get("to"))
    if bearing is None:
        first = _member_ray(source, fkind, fid, centre, u)
        second = _member_ray(source, tkind, tid, centre, v)
        return centre, first, second
    first, second = dimension.rays_by_bearing(u, v, bearing)
    return centre, first, second


def dimension_angle(source, dim):
    """An angle dimension's arc: where it starts, how far it sweeps (signed, degrees) and about which point -- statics.py's dimension_angle, ported."""
    rays = angle_rays(source, dim)
    if rays is None:
        return None
    centre, first, second = rays
    sweep, start = dimension.arc(first, second, dim.get("bearing") is not None and float(dim.get("offset", 0.0)) < 0)
    return centre, sweep, start


def dimension_value(source, dim):
    """What a dimension measures, and its unit."""
    kind = dim.get("kind")
    unit = DIMENSION_UNITS.get(kind, "")
    if kind == "angle":
        if dimension_corner(source, dim) is None:
            return None, unit
        return abs(dimension_angle(source, dim)[1]), unit
    ends = dimension_ends(source, dim)
    if ends is None:
        return None, unit
    return dimension.linear_value(kind, ends[0], ends[1]), unit


def dimension_show(dim):
    """What a dimension writes beside itself, one of LABEL_MODES -- statics.dimension_show's rule: the `show` it states, else, for one saved before it could say so, `name` where it carries a label (which then took the value's place) and `value` where it does not."""
    return dimension.show(dim, LABEL_MODES)


def dimension_value_text(source, dim):
    """What a dimension measured, with its unit, as the figure prints it; '?' where it no longer resolves."""
    value, unit = dimension_value(source, dim)
    if value is None:
        return "?"
    if unit == "°":
        return f"{figure_number(value, ANGLE_DIGITS)}{unit}"
    return f"{figure_number(value)} {unit}"


def dimension_text(source, dim):
    """What a dimension writes on the figure, by its `show`: nothing, its name, what it measured, or `name = value` -- a name asked for and not given writes nothing, and `name+value` without one writes the value alone (statics.dimension_text's own rule, a load's)."""
    mode = dimension_show(dim)
    return dimension.text(mode, dim.get("label"), dimension_value_text(source, dim) if mode not in ("none", "name") else "")


def rectangle_two_corners(p1, p2):
    """An axis-aligned rectangle's four points from two diagonal corners, clockwise from p1 -- the 'deux clics diagonaux' mode."""
    (x1, z1), (x2, z2) = p1, p2
    return [(x1, z1), (x2, z1), (x2, z2), (x1, z2)]


def perpendicular_offset(a, b, point):
    """The signed distance of `point` off the line a-b, at right angles to it -- what the tool bar's third click (or a typed value) becomes before rectangle_from_edge() draws the box. Positive on the side n = (-u_z, u_x) points to, u being the direction from a to b."""
    length = math.dist(a, b)
    if length <= SAME_POINT:
        return 0.0
    u = ((b[0] - a[0]) / length, (b[1] - a[1]) / length)
    n = (-u[1], u[0])
    return (point[0] - a[0]) * n[0] + (point[1] - a[1]) * n[1]


def reference_direction(source, point, exclude=None):
    """The direction of the element segment or shown aid line nearest `point` -- what the 'perpendicular' and 'parallel' aid tools take their angle from, the second click naming a reference by proximity rather than by id (there being nothing else at that click to name one by). None where nothing is near enough to call a reference."""
    best, best_d = None, None
    for _eid, a, b in _all_segments(source, exclude):
        d, _q = _point_segment(point, a, b)
        if best_d is None or d < best_d:
            best, best_d = _unit_towards(a, b), d
    for aid in source.get("aids", []):
        line = aid_line(aid)
        if line is None:
            continue
        p, u = line
        d, _q = _point_segment(point, (p[0] - u[0] * 1e5, p[1] - u[1] * 1e5), (p[0] + u[0] * 1e5, p[1] + u[1] * 1e5))
        if best_d is None or d < best_d:
            best, best_d = u, d
    return best


def _unit_towards(a, b):
    length = math.dist(a, b)
    return (1.0, 0.0) if length <= SAME_POINT else ((b[0] - a[0]) / length, (b[1] - a[1]) / length)


def rectangle_from_edge(p1, p2, width):
    """A rectangle's four points from one edge (`p1` to `p2`) and a signed width at right angles to it -- the 'trois clics' mode (the third click's own distance off the line p1-p2) and the '1 clic + Tab' mode (the same width typed instead of clicked), which are therefore one function and not two."""
    length = math.dist(p1, p2)
    if length <= SAME_POINT:
        return [tuple(p1), tuple(p2), tuple(p2), tuple(p1)]
    u = ((p2[0] - p1[0]) / length, (p2[1] - p1[1]) / length)
    n = (-u[1], u[0])
    far1 = (p1[0] + n[0] * width, p1[1] + n[1] * width)
    far2 = (p2[0] + n[0] * width, p2[1] + n[1] * width)
    return [tuple(p1), tuple(p2), far2, far1]


def area_fixed(record, draw="b"):
    """The side of an area element a position fixes -- the engineer's request of 08.10.2026: «je choisis si je dessine la largeur ou la hauteur de la position; ensuite je dessine l'élément qui possède donc une largeur fixe». `record` is a position record, `draw` which dimension is drawn for a rectangular section, "b" its width or "h" its height; the other is the position's own.

    Returns {"draw": what the drawing leaves free -- "b", "h" or "" --, "fixed": the dimension that is the position's -- "b", "h", "t" (a plate's or a CLT panel's thickness) or "d" (a round section's diameter) --, "length": its value in mm}, or None where the position has no dimension to fix: a steel profile, whose designation carries none this module knows, or no section at all. A section with one dimension fixes that one and leaves the rest of the drawing free, whichever way `draw` is: «Épaisseur fixe» (the longer side of the drag is the length, the shorter across it is the thickness).

    The values are `section.sides` -- the one reader of a position's dimension -- and nothing here recomputes them."""
    sides = position_section.sides(record)
    if sides is None:
        return None
    kind = (position_section.of_record(record) or {}).get("type")
    b, h = sides
    if kind == "rec":
        return {"draw": "h", "fixed": "b", "length": b} if draw == "h" else {"draw": "b", "fixed": "h", "length": h}
    return {"draw": "", "fixed": "d" if kind == "cir" else "t", "length": b}


def rectangle_with_fixed_side(a, b, length, draw=""):
    """The rectangle a drag from corner `a` to corner `b` gives where one of its sides is `length` -- a position's dimension (`area_fixed`). `draw` "b": the width is dragged -- the horizontal extent of the drag -- and the height is `length`; "h": the height is dragged and the width is `length`; "": the longer extent of the drag is the length of the piece and the fixed side lies across it. The fixed side grows the way the drag goes -- up where it goes up, down where it goes down, a drag with none going the way z grows -- so that the rectangle follows the cursor."""
    dx, dz = b[0] - a[0], b[1] - a[1]
    sx = -1.0 if dx < 0 else 1.0
    sz = -1.0 if dz < 0 else 1.0
    if draw == "b":
        width, height = abs(dx), length
    elif draw == "h":
        width, height = length, abs(dz)
    elif abs(dx) >= abs(dz):
        width, height = abs(dx), length
    else:
        width, height = length, abs(dz)
    return rectangle_two_corners(a, (a[0] + sx * width, a[1] + sz * height))


def rectangle_with_fixed_width(p1, p2, third, length):
    """The rectangle of an edge `p1` to `p2` and a fixed width `length` at right angles to it, on the side of the line the click `third` is on -- the click only says which side, its own distance being ignored (the edge modes of the tool, with a position that fixes the width)."""
    side = perpendicular_offset(p1, p2, third)
    return rectangle_from_edge(p1, p2, length if side >= 0 else -length)


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


def _inside(p, polygon):
    """Even-odd point-in-polygon -- plan.py's _inside, unchanged."""
    inside = False
    n = len(polygon)
    for i in range(n):
        (x1, y1), (x2, y2) = polygon[i], polygon[(i + 1) % n]
        if (y1 > p[1]) != (y2 > p[1]) and p[0] < (x2 - x1) * (p[1] - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def hit_element(source, p, tolerance):
    """The id of the element under `p` -- a line within tolerance of its polyline, an area anywhere inside it (or within tolerance of its outline) -- the one drawn last, on top, where two overlap. None otherwise."""
    best = None
    for i, element in enumerate(source.get("elements", [])):
        segments = segments_of(element)
        if not segments:
            continue
        d = min((_point_segment(p, a, b)[0] for a, b in segments), default=math.inf)
        hit = d <= tolerance
        if not hit and element_kind(element) == "area":
            hit = _inside(p, [tuple(q) for q in element["points"]])
        if hit:
            if best is None or i >= best[0]:
                best = (i, element["id"])
    return best[1] if best else None


def hit_connector(source, p, tolerance):
    """The id of the connector marker under `p`, the nearest one within tolerance, or None."""
    best, best_d = None, tolerance
    for marker in source.get("connectors", []):
        d = math.dist(p, (float(marker["x"]), float(marker["z"])))
        if d <= best_d:
            best, best_d = marker["id"], d
    return best


def hit_aid_point(source, p, tolerance):
    """The id of the point-shaped aid under `p`, the nearest one within tolerance, or None."""
    best, best_d = None, tolerance
    for aid in source.get("aids", []):
        at = aid_point(aid)
        if at is None:
            continue
        d = math.dist(p, at)
        if d <= best_d:
            best, best_d = aid["id"], d
    return best


def hit_aid_line(source, p, tolerance):
    """The id of the construction line under `p` -- the nearest one within tolerance of its infinite line -- or None.

    ⚠️ Until v0.75 nothing hit-tested a line at all, so the one thing «Trancher» needs selected with the elements could be picked in the «Aides» list and nowhere on the drawing. The canvas asks this LAST, after the markers, the points and the elements: a line runs across the whole detail, and taking a click meant for a piece it passes through would be the wrong way round.
    """
    best, best_d = None, tolerance
    for aid in source.get("aids", []):
        line = aid_line(aid)
        if line is None:
            continue
        (ax, az), (ux, uz) = line
        d = abs((p[0] - ax) * uz - (p[1] - az) * ux)
        if d <= best_d:
            best, best_d = aid["id"], d
    return best


def hit_label(source, p, tolerance, frames=None):
    """The (collection, id) whose label box lies under `p`, or None -- a label is drawn over every symbol, so Woodcore asks this before hit_element/hit_connector. `frames` are schema_svg.label_frames(source), when the caller keeps them -- plan.py's v0.42 rule, ported (plan.hit_label is bound to plan_svg's own numbering, not reusable as-is)."""
    from domains import schema_svg

    return schema_svg.hit_label(source, p, tolerance, frames)


def grid_snap(p, step):
    """`p` pulled onto the nearest crossing of a grid of that step, in mm."""
    if not step or step <= 0:
        return tuple(p)
    return (round(p[0] / step) * step, round(p[1] / step) * step)


def _all_segments(source, exclude=None):
    """Every element's segments as (element id, a, b), skipping the one being dragged."""
    out = []
    for element in source.get("elements", []):
        if element["id"] == exclude:
            continue
        for a, b in segments_of(element):
            out.append((element["id"], a, b))
    return out


def _cross(a, u, b, v):
    """Where the line through `a` along `u` meets the one through `b` along `v`, with the two parameters, or None for parallels."""
    det = u[0] * v[1] - u[1] * v[0]
    if abs(det) < 1e-12:
        return None
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = (dx * v[1] - dy * v[0]) / det
    s = (dx * u[1] - dy * u[0]) / det
    return ((a[0] + t * u[0], a[1] + t * u[1]), t, s)


def band_outlines(source, positions=None, exclude=None):
    """(element id, polygon) for what is SEEN of every element -- a linear element's band, one rectangle per segment at the thickness its view shows (the very rectangles `schema_svg` draws), an area element's own outline."""
    out = []
    for element in source.get("elements", []):
        if element["id"] == exclude:
            continue
        if element_kind(element) == "area":
            points = [(float(q[0]), float(q[1])) for q in element.get("points", [])]
            if len(points) >= 3:
                out.append((element["id"], points))
            continue
        half = element_width(element, positions) / 2.0
        for a, b in segments_of(element):
            length = math.dist(a, b)
            if length <= SAME_POINT:
                continue
            nx, nz = -(b[1] - a[1]) / length * half, (b[0] - a[0]) / length * half
            out.append((element["id"], [(a[0] + nx, a[1] + nz), (b[0] + nx, b[1] + nz), (b[0] - nx, b[1] - nz), (a[0] - nx, a[1] - nz)]))
    return out


def _tidy(point):
    """A crossing as it is kept: to a millionth of a millimetre, so that a line at 90 degrees crossing another lands on 40 and not on 40.000000000000014 (cos 90° is not quite 0 in floating point)."""
    return (round(point[0], 6) + 0.0, round(point[1], 6) + 0.0)


def snap_geometry(source, positions=None, exclude=None):
    """Everything a click may be pulled onto, worked out once per state of the schema -- Woodcore's canvas keeps it beside its drawing and hands it back on every movement of the mouse, rather than solving every crossing again.

    {"targets": [(priority, kind, point)], "segments": [(element id, a, b)], "lines": [(point, unit)]}:
    - targets: aid points, connector markers, the elements' own vertices and the corners of their bands (priority 0, "point"); the middles of element segments (1, "midpoint"); and **where two things cross** (2, "crossing") -- an element's axis or the edge of its band against another's, and a construction line against an element or against another construction line;
    - segments: what a point may slide along ("on-line"), axes and band edges alike;
    - lines: the construction lines, which a point may slide along too, and which are infinite.
    """
    targets = []
    for aid in source.get("aids", []):
        at = aid_point(aid)
        if at is not None:
            targets.append((0, "point", at))
    for marker in source.get("connectors", []):
        targets.append((0, "point", (float(marker["x"]), float(marker["z"]))))
    axes = _all_segments(source, exclude)
    for element in source.get("elements", []):
        if element["id"] != exclude:
            targets += [(0, "point", (float(q[0]), float(q[1]))) for q in element.get("points", [])]
    for _eid, a, b in axes:
        targets.append((1, "midpoint", ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)))
    # A band's edges join the axes; an area's outline already IS its axis segments, so it adds nothing here.
    linear = {e["id"] for e in source.get("elements", []) if element_kind(e) == "linear"}
    edges = []
    for eid, polygon in band_outlines(source, positions, exclude):
        if eid in linear:
            targets += [(0, "point", q) for q in polygon]
            edges += [(eid, polygon[i - 1], polygon[i]) for i in range(len(polygon))]
    segments = axes + edges
    for i, (ei, a, b) in enumerate(segments):
        u = (b[0] - a[0], b[1] - a[1])
        for ej, c, d in segments[i + 1:]:
            if ei == ej:
                continue    # a band's own corners are already points, and its edges cross its axis nowhere
            hit = _cross(a, u, c, (d[0] - c[0], d[1] - c[1]))
            if hit is not None and -1e-9 <= hit[1] <= 1 + 1e-9 and -1e-9 <= hit[2] <= 1 + 1e-9:
                targets.append((2, "crossing", _tidy(hit[0])))
    lines = [line for line in (aid_line(aid) for aid in source.get("aids", [])) if line is not None]
    for i, (p, u) in enumerate(lines):
        for q, v in lines[i + 1:]:
            hit = _cross(p, u, q, v)
            if hit is not None:
                targets.append((2, "crossing", _tidy(hit[0])))
        for _eid, a, b in segments:
            hit = _cross(p, u, a, (b[0] - a[0], b[1] - a[1]))
            if hit is not None and -1e-9 <= hit[2] <= 1 + 1e-9:
                targets.append((2, "crossing", _tidy(hit[0])))
    return {"targets": targets, "segments": segments, "lines": lines}


def snap_targets(source, exclude=None, positions=None):
    """The hard targets a point may be put down on, as (priority, kind, point) -- `snap_geometry`'s own, for a caller that wants only those."""
    return snap_geometry(source, positions, exclude)["targets"]


def snap(source, p, tolerance, step=None, exclude=None, geometry=None, positions=None):
    """The point a click at `p` puts down, and what it snapped to -- statics.py's snap(), ported: an aid point, a connector marker or a corner beats the middle of a segment, which beats a crossing, which beats a point on a segment or a construction line; the grid catches whatever is left. `geometry` is `snap_geometry`'s result where the caller keeps one."""
    geometry = geometry if geometry is not None else snap_geometry(source, positions, exclude)
    best, best_kind, best_rank = tuple(p), None, None
    for priority, kind, q in geometry["targets"]:
        d = math.dist(p, q)
        if d <= tolerance:
            rank = (priority, d)
            if best_rank is None or rank < best_rank:
                best, best_kind, best_rank = tuple(q), kind, rank
    if best_kind is None:
        for _eid, a, b in geometry["segments"]:
            d, q = _point_segment(p, a, b)
            if d <= tolerance:
                rank = (SNAP_KINDS.index("on-line"), d)
                if best_rank is None or rank < best_rank:
                    best, best_kind, best_rank = q, "on-line", rank
        for (ax, az), (ux, uz) in geometry["lines"]:
            t = (p[0] - ax) * ux + (p[1] - az) * uz
            q = _tidy((ax + t * ux, az + t * uz))
            d = math.dist(p, q)
            if d <= tolerance:
                rank = (SNAP_KINDS.index("on-line"), d)
                if best_rank is None or rank < best_rank:
                    best, best_kind, best_rank = q, "on-line", rank
    if best_kind is None and step:
        q = grid_snap(p, step)
        return q, "grid"
    return best, best_kind


def tracking_rays(source, anchor, tolerance=SAME_POINT):
    """The rays the cursor may lock to from `anchor`: the eight polar directions, plus the axis and the normal of every element segment that meets the anchor."""
    rays = {}
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
    for eid, a, b in _all_segments(source):
        for end, other in ((a, b), (b, a)):
            if math.dist(anchor, end) <= tolerance:
                base = math.degrees(math.atan2(other[1] - end[1], other[0] - end[0]))
                add("axis", base, eid)
                add("axis", base + 180, eid)
                add("normal", base + 90, eid)
                add("normal", base - 90, eid)
    return sorted(rays.values(), key=lambda r: r["angle"])


def nearest_ray(rays, anchor, point, tolerance_deg=TRACK_TOLERANCE_DEG):
    """The ray of smallest angular deviation from `anchor` towards `point`, within the tolerance, and `point` projected onto it -- or (None, point)."""
    dx, dy = point[0] - anchor[0], point[1] - anchor[1]
    length = math.hypot(dx, dy)
    if length <= SAME_POINT:
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


def along(anchor, ray, distance):
    """The point `distance` mm from `anchor` along `ray`."""
    return (anchor[0] + distance * ray["unit"][0], anchor[1] + distance * ray["unit"][1])


def typed_point(anchor, ray, text):
    """Where a distance typed into Woodcore's field lands, or None where it is not a number. A comma is read as a decimal point."""
    try:
        distance = float(str(text).strip().replace(",", "."))
    except (TypeError, ValueError):
        return None
    if not math.isfinite(distance):
        return None
    return along(anchor, ray, distance)


def extension_lines(source, exclude=None):
    """Every element segment's line, extended beyond its ends, as (point, unit, element id)."""
    out = []
    for eid, a, b in _all_segments(source, exclude):
        length = math.dist(a, b)
        if length > SAME_POINT:
            out.append((a, ((b[0] - a[0]) / length, (b[1] - a[1]) / length), eid))
    return out


def track(source, anchor, point, tolerance, step=None, tolerance_deg=TRACK_TOLERANCE_DEG, exclude=None, geometry=None, positions=None):
    """Where the cursor is, tracking from `anchor` -- the one call Woodcore's canvas makes on every movement of the mouse. statics.py's track(), ported. `geometry` is `snap_geometry`'s result where the caller keeps one."""
    geometry = geometry if geometry is not None else snap_geometry(source, positions, exclude)
    if anchor is None:
        p, kind = snap(source, point, tolerance, step, exclude, geometry)
        return {"point": p, "ray": None, "kind": kind, "distance": None, "angle": None}

    rays = tracking_rays(source, anchor)
    ray, projected = nearest_ray(rays, anchor, point, tolerance_deg)
    if ray is None:
        p, kind = snap(source, point, tolerance, step, exclude, geometry)
        return {"point": p, "ray": None, "kind": kind, "distance": math.dist(anchor, p), "angle": None}

    best, kind = projected, "ray"
    for priority, target_kind, q in geometry["targets"]:
        _d, on_ray = _point_segment(q, anchor, along(anchor, ray, max(math.dist(anchor, q), 1e-9)))
        if math.dist(q, on_ray) <= tolerance and math.dist(q, projected) <= tolerance * 4:
            best, kind = tuple(q), target_kind
            break
    if kind == "ray":
        for a, u, eid in extension_lines(source, exclude):
            if eid == ray.get("via"):
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
    return {"point": best, "ray": ray, "kind": kind, "distance": math.dist(anchor, best), "angle": ray["angle"]}
