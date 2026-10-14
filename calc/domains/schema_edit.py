"""What the «Schémas» tab does to the elements of a connection detail -- move, turn, mirror, duplicate, split one in two, merge two into one -- split out of calc/domains/schema.py (issue #30), moved verbatim. schema.py imports every name back. Qt-free.
"""

import copy
import math
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


# The five collections a schema holds, in the order they are checked, listed and drawn. `texts`, the Text tool's (issue #43), is figure_text's: a schema that has one is a 1.2 source.
ENTITIES = ("elements", "connectors", "aids", "dimensions", "texts")


# What a new entry of each collection is called: E1, C1, A1, D1, T1.
ENTITY_PREFIX = {"elements": "E", "connectors": "C", "aids": "A", "dimensions": "D", "texts": "T"}


def find_entry(source, eid):
    """The (collection, entry) an id names, whatever collection it is in -- ids are unique across a schema."""
    for collection in ENTITIES:
        entry = entry_of(source, collection, eid)
        if entry is not None:
            return collection, entry
    return None, None


def all_ids(source):
    """Every id the schema carries, in collection order."""
    return [entry["id"] for collection in ENTITIES for entry in source.get(collection, [])]


def next_id(source, collection):
    """The first free `<prefix><n>` of that collection -- E3, C7, A2 -- ignoring case, as the file system and the id check do."""
    taken = {eid.lower() for eid in all_ids(source)}
    prefix = ENTITY_PREFIX[collection]
    n = 1
    while f"{prefix}{n}".lower() in taken:
        n += 1
    return f"{prefix}{n}"


def used_by(source, collection, eid):
    """Everything that names this entry, as (collection, id) pairs -- what Woodcore lists before it deletes a node."""
    out = []
    if collection == "aids":
        for dim in source.get("dimensions", []):
            for end in ("from", "to"):
                anchor = dim.get(end) or {}
                if anchor.get("point") == eid or anchor.get("aid") == eid:
                    out.append(("dimensions", dim["id"]))
    elif collection == "elements":
        for dim in source.get("dimensions", []):
            for end in ("from", "to"):
                if (dim.get(end) or {}).get("element") == eid:
                    out.append(("dimensions", dim["id"]))
    return out


def remove(source, collection, eid):
    """Deletes an entry and everything hanging off it, and says what went."""
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


def round_place(value, digits=DIGITS):
    """A coordinate as it is saved: to a hundredth of a millimetre, far below what a click can place. `schema_canvas._round`'s own rule, restated here so that a value a modification computes is rounded exactly as one a click puts down -- a rotation of 90 degrees four times must give back the coordinates it started from, and it does so only if both sides round alike."""
    value = round(float(value), digits) + 0.0
    return int(value) if float(value).is_integer() else value


def _place_point(p, place):
    x, z = place(float(p[0]), float(p[1]))
    return [round_place(x), round_place(z)]


def translation(dx, dz):
    """Moving by a vector. Returns the (place, bearing, flips) triple every modification is applied through."""
    return (lambda x, z: (x + dx, z + dz), lambda a: a, False)


def rotation(centre, degrees):
    """Turning about a point, degrees from +x towards +z -- the frame's own sense (clockwise as the drawing is read, section 3.3decies)."""
    cx, cz = float(centre[0]), float(centre[1])
    rad = math.radians(degrees)
    cos, sin = math.cos(rad), math.sin(rad)

    def place(x, z):
        dx, dz = x - cx, z - cz
        return (cx + dx * cos - dz * sin, cz + dx * sin + dz * cos)

    return (place, lambda a: normalize_angle(a + degrees), False)


def reflection(a, b):
    """Mirroring across the line through two points. Raises where the two are the same point -- two points in one place name no axis."""
    ax, az = float(a[0]), float(a[1])
    bx, bz = float(b[0]), float(b[1])
    length = math.dist((ax, az), (bx, bz))
    if length <= SAME_POINT:
        raise ValueError("a mirror axis needs two distinct points")
    ux, uz = (bx - ax) / length, (bz - az) / length
    axis = math.degrees(math.atan2(uz, ux))

    def place(x, z):
        dx, dz = x - ax, z - az
        along = dx * ux + dz * uz
        across = dx * uz - dz * ux          # the signed distance to the axis
        # the foot of the perpendicular, then the same distance on the axis's other side -- `+ across` put the point back where it was, so «Symétrie» moved nothing (periodic audit 260916)
        return (ax + along * ux - across * uz, az + along * uz + across * ux)

    # A reflection reverses orientation, so a signed offset changes side and a direction is
    # folded about the axis rather than turned by a constant.
    return (place, lambda d: normalize_angle(2.0 * axis - d), True)


def _modify_entry(collection, entry, place, bearing, flips):
    """Applies one modification to one entry, in place, by the shape that entry has."""
    if collection == "elements":
        entry["points"] = [_place_point(p, place) for p in entry.get("points", [])]
        return
    if collection in ("connectors", "texts"):   # a marker and a text (issue #43) are each one place, x and z
        x, z = place(float(entry["x"]), float(entry["z"]))
        entry["x"], entry["z"] = round_place(x), round_place(z)
        return
    if collection == "aids":
        kind = entry.get("kind")
        if kind in AID_TWO_POINT_KINDS:
            x1, z1 = place(float(entry["x1"]), float(entry["z1"]))
            x2, z2 = place(float(entry["x2"]), float(entry["z2"]))
            entry["x1"], entry["z1"] = round_place(x1), round_place(z1)
            entry["x2"], entry["z2"] = round_place(x2), round_place(z2)
            return
        x, z = place(float(entry["x"]), float(entry["z"]))
        entry["x"], entry["z"] = round_place(x), round_place(z)
        if kind in AID_ANGLE_KINDS:
            entry["angle"] = round_place(bearing(float(entry.get("angle", 0.0))), ANGLE_DIGITS)
        return
    if collection == "dimensions":
        # A dimension keeps its kind: a horizontal one turned about a point is still the x-distance
        # between its ends, which is what choosing that kind said. What moves is a *free* anchor,
        # a place of its own rather than a point it names; one naming an aid follows that aid.
        for end in ("from", "to"):
            anchor = entry.get(end) or {}
            if "x" in anchor and "z" in anchor:
                x, z = place(float(anchor["x"]), float(anchor["z"]))
                anchor["x"], anchor["z"] = round_place(x), round_place(z)
        if "bearing" in entry:
            entry["bearing"] = round_place(bearing(float(entry["bearing"])), ANGLE_DIGITS)
        if flips and "offset" in entry:
            entry["offset"] = round_place(-float(entry["offset"]))
        return


def modify(source, ids, transform):
    """Applies one modification to every entry named, in place. `transform` is a (place, bearing, flips) triple -- `translation`, `rotation` or `reflection`. Ids the schema does not carry are skipped rather than raised on: the canvas may hold a selection a reload has since emptied."""
    place, bearing, flips = transform
    for eid in ids:
        collection, entry = find_entry(source, eid)
        if entry is not None:
            _modify_entry(collection, entry, place, bearing, flips)


def duplicate(source, ids, transform):
    """Copies every entry named, applies the modification to the copies, and appends them. Returns the new ids, in the order the originals were given.

    A copy is a copy of the *drawing*, so it keeps its element's position number, its label, its view and its section (b, h) -- two identical pieces share a number, which is exactly what the position plan already allows (v0.44). What it cannot keep is its id, ids being unique across a schema.

    ⚠️ A **dimension** is deliberately not copied, even when one is in the selection: it is anchored, and a copy would either name the originals' own anchors -- measuring the original, in the copy's place -- or name nothing. Duplicating the geometry and re-dimensioning it is the honest order.
    """
    place, bearing, flips = transform
    made = []
    for eid in ids:
        collection, entry = find_entry(source, eid)
        if entry is None or collection == "dimensions":
            continue
        copy_of = copy.deepcopy(entry)
        copy_of["id"] = next_id(source, collection)
        _modify_entry(collection, copy_of, place, bearing, flips)
        source[collection].append(copy_of)
        made.append(copy_of["id"])
    return made


class Refused(ValueError):
    """A modification the geometry does not allow.

    It carries **both** halves on purpose: `args[0]` is a sentence that stands on its own in English, for a caller with no window and for a test that asserts what went wrong; `code` and `detail` are what Woodcore turns into its own three languages, since a refusal an engineer reads in the status line is chrome and follows the window (section 4bis). Neither is derived from the other -- parsing the sentence back into a code is exactly the fragility the code exists to avoid.
    """

    def __init__(self, code, message, detail=""):
        super().__init__(message)
        self.code = code
        self.detail = detail


def _line_of_aid(source, aid_id):
    """The (point, unit direction) of a construction line, or a refusal naming what was found instead."""
    aid = entry_of(source, "aids", aid_id)
    if aid is None:
        raise Refused("split-no-aid", f"the schema has no aid {aid_id!r}", aid_id)
    line = aid_line(aid)
    if line is None:
        raise Refused("split-aid-point", f"aid {aid_id} is a named point, not a construction line -- a cut needs a line to cut along", aid_id)
    return line


def _cut_points(points, closed, a, u):
    """Where the line (a, u) crosses a polyline (or a closed polygon), as (segment index, parameter, point), in order along it. A crossing at a vertex is taken once, on the segment it opens."""
    out = []
    n = len(points)
    last = n if closed else n - 1
    for i in range(last):
        p, q = points[i], points[(i + 1) % n]
        v = (q[0] - p[0], q[1] - p[1])
        hit = _cross(a, u, p, v)
        if hit is None:
            continue
        _point, _t, s = hit
        if -1e-9 <= s < 1 - 1e-9:
            out.append((i, s, (p[0] + s * v[0], p[1] + s * v[1])))
    return out


def _polyline_pieces(points, a, u):
    """A polyline cut by a line, as a list of polylines. One piece where the line misses it."""
    cuts = _cut_points(points, False, a, u)
    if not cuts:
        return [list(points)]
    pieces, current = [], [list(points[0])]
    by_segment = {}
    for i, s, q in cuts:
        by_segment.setdefault(i, []).append((s, q))
    for i in range(len(points) - 1):
        for _s, q in sorted(by_segment.get(i, [])):
            if math.dist(current[-1], q) > SAME_POINT:
                current.append([round_place(q[0]), round_place(q[1])])
            if len(current) >= 2:
                pieces.append(current)
                current = [list(current[-1])]
            else:
                current = [[round_place(q[0]), round_place(q[1])]]
        nxt = points[i + 1]
        if math.dist(current[-1], nxt) > SAME_POINT:
            current.append(list(nxt))
    if len(current) >= 2:
        pieces.append(current)
    return [p for p in pieces if len(p) >= 2]


def _polygon_pieces(points, a, u):
    """A polygon cut by a line into two, where the line crosses its outline exactly twice -- it enters once and leaves once, which is true of every convex piece and of a concave one the line does not re-enter. Raises otherwise, naming the count, rather than returning a shape nobody asked for."""
    cuts = _cut_points(points, True, a, u)
    if len(cuts) < 2:
        return [list(points)]
    if len(cuts) > 2:
        raise Refused("split-crossings", f"the line crosses this area {len(cuts)} times -- «trancher» cuts an area a line enters once and leaves once", str(len(cuts)))
    (i1, _s1, q1), (i2, _s2, q2) = cuts
    q1 = [round_place(q1[0]), round_place(q1[1])]
    q2 = [round_place(q2[0]), round_place(q2[1])]
    n = len(points)
    first = [q1] + [list(points[(i1 + 1 + k) % n]) for k in range((i2 - i1) % n)] + [q2]
    second = [q2] + [list(points[(i2 + 1 + k) % n]) for k in range((i1 - i2) % n)] + [q1]
    out = []
    for piece in (first, second):
        piece = _drop_repeats(piece)
        if len(piece) >= 3:
            out.append(piece)
    return out


def _drop_repeats(points, closed=True):
    """Consecutive points in the same place taken out once -- a cut lands on a vertex often enough that this is the common case, not the corner one -- and, for a **closed** shape only, a last point sitting on the first. ⚠️ A polyline is not closed and may legitimately end where it began, so `closed` is a parameter rather than a rule."""
    out = []
    for p in points:
        if not out or math.dist(out[-1], p) > SAME_POINT:
            out.append(list(p))
    if closed:
        while len(out) > 1 and math.dist(out[0], out[-1]) <= SAME_POINT:
            out.pop()
    return out


def _drop_collinear(points, closed):
    """Points lying on the straight line between their two neighbours, taken out -- which is exactly what a merge leaves behind where the cut used to be, so that splitting a piece and merging it again gives back the shape it started with rather than the same shape carrying two extra vertices. A polyline's two ends are kept, being ends and not bends."""
    n = len(points)
    if n < 3:
        return [list(p) for p in points]
    keep = []
    for i in range(n):
        if not closed and (i == 0 or i == n - 1):
            keep.append(list(points[i]))
            continue
        a, b, c = points[(i - 1) % n], points[i], points[(i + 1) % n]
        # b is a bend unless it sits on a-c: the triangle's area is its distance from that line.
        area = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
        length = math.dist(a, c)
        if length <= SAME_POINT or area / length > SAME_POINT:
            keep.append(list(b))
    return keep if len(keep) >= (3 if closed else 2) else [list(p) for p in points]


def split_element(source, eid, aid_id):
    """Cuts one element along a construction line and returns the ids of the pieces.

    **The pieces carry the same position number**, which is the whole point: an element cut in two is two elements of one position, which the position plan already allows for identical elements (v0.44). They carry the same label, view and section (b, h) too -- a cut changes where a piece ends, not what it is.

    The **first piece keeps the element's own id**, so a dimension anchored to it still resolves; the rest are given the next free ids. Raises where the line misses the element, where the aid is a point rather than a line, and where a line crosses an area more than twice.
    """
    element = entry_of(source, "elements", eid)
    if element is None:
        raise Refused("split-no-element", f"the schema has no element {eid!r}", eid)
    a, u = _line_of_aid(source, aid_id)
    points = [(float(p[0]), float(p[1])) for p in element.get("points", [])]
    kind = element_kind(element)
    pieces = _polyline_pieces(points, a, u) if kind == "linear" else _polygon_pieces(points, a, u)
    if len(pieces) < 2:
        raise Refused("split-missed", f"the construction line does not cross element {eid} -- «trancher» needs a line that cuts it", eid)
    pieces = [[[round_place(p[0]), round_place(p[1])] for p in piece] for piece in pieces]
    index = index_of(source, "elements", eid)
    made = []
    for n, piece in enumerate(pieces):
        if n == 0:
            element["points"] = piece
            made.append(element["id"])
            continue
        other = copy.deepcopy(element)
        other["points"] = piece
        other["id"] = next_id(source, "elements")
        other.pop("label_offset", None)     # the second half's number goes back to its own place
        source["elements"].insert(index + n, other)
        made.append(other["id"])
    return made


def _chain(pieces):
    """Joins polylines end to end into one. Returns None where they do not all touch."""
    chain = list(pieces[0])
    rest = [list(p) for p in pieces[1:]]
    while rest:
        for i, piece in enumerate(rest):
            if math.dist(chain[-1], piece[0]) <= SAME_POINT:
                chain += piece[1:]
            elif math.dist(chain[-1], piece[-1]) <= SAME_POINT:
                chain += list(reversed(piece))[1:]
            elif math.dist(chain[0], piece[-1]) <= SAME_POINT:
                chain = piece[:-1] + chain
            elif math.dist(chain[0], piece[0]) <= SAME_POINT:
                chain = list(reversed(piece))[:-1] + chain
            else:
                continue
            rest.pop(i)
            break
        else:
            return None
    return chain


def _shared_edge(a, b):
    """The (i, j) of an edge polygon `a` and polygon `b` hold in common, walked opposite ways -- the cut a split left behind. None where they share none."""
    for i in range(len(a)):
        p, q = a[i], a[(i + 1) % len(a)]
        for j in range(len(b)):
            r, s = b[j], b[(j + 1) % len(b)]
            if math.dist(p, s) <= SAME_POINT and math.dist(q, r) <= SAME_POINT:
                return i, j
    return None


def _splice(a, b):
    """Two polygons sharing one edge, joined into one. None where they share none."""
    found = _shared_edge(a, b)
    if found is None:
        return None
    i, j = found
    n, m = len(a), len(b)
    out = [list(a[(i + 1 + k) % n]) for k in range(n)]          # a, opened at the shared edge
    out += [list(b[(j + 1 + k) % m]) for k in range(1, m - 1)]  # b, its own shared edge left out
    out = _drop_repeats(out)
    return out if len(out) >= 3 else None


def merge_elements(source, ids):
    """Merges elements of one position into one, and returns the id kept -- the inverse of `split_element`.

    ⚠️ **Only elements of the same position number merge.** Two pieces of one beam are one beam; two different positions are two things, and joining them would put one number on what the workbook calls two. A mismatch raises **naming both numbers**, which is the message the engineer reads.

    The first element named keeps its id and takes the merged shape; the others go. A linear element's pieces are chained end to end; an area's are spliced on the edge they share. Raises where the pieces do not touch.
    """
    entries = []
    for eid in ids:
        collection, entry = find_entry(source, eid)
        if entry is None:
            raise Refused("merge-missing", f"the schema has no {eid!r}", eid)
        if collection != "elements":
            raise Refused("merge-not-element", f"{eid} is a {collection[:-1]}, not an element -- «fusionner» joins elements", eid)
        entries.append(entry)
    if len(entries) < 2:
        raise Refused("merge-too-few", "«fusionner» joins two elements or more -- select them with Ctrl")
    kinds = {e.get("kind") for e in entries}
    if len(kinds) > 1:
        raise Refused("merge-kinds", "a linear element and an area do not merge -- they are not the same kind of piece")
    positions = []
    for entry in entries:
        position = (entry.get("position") or "").strip()
        if position not in positions:
            positions.append(position)
    if len(positions) > 1:
        named = ", ".join(p or "(no position)" for p in positions)
        raise Refused("merge-positions", f"only elements of the same position merge -- these carry {named}", named)
    pieces = [[(float(p[0]), float(p[1])) for p in e.get("points", [])] for e in entries]
    if kinds == {"linear"}:
        joined = _chain(pieces)
        if joined is None:
            raise Refused("merge-apart", "these elements do not touch end to end -- «fusionner» joins pieces that meet")
    else:
        joined = pieces[0]
        for piece in pieces[1:]:
            spliced = _splice(joined, piece)
            if spliced is None:
                raise Refused("merge-no-edge", "these areas share no edge -- «fusionner» joins pieces a cut left behind")
            joined = spliced
    kept = entries[0]
    closed = kinds == {"area"}
    tidy = _drop_collinear(_drop_repeats(joined, closed), closed)
    kept["points"] = [[round_place(p[0]), round_place(p[1])] for p in tidy]
    kept.pop("label_offset", None)          # the number goes back to its own place on the new shape
    for entry in entries[1:]:
        remove(source, "elements", entry["id"])
    return kept["id"]
