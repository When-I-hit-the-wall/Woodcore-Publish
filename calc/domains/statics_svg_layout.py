"""Where everything of a static model's figure stands -- its scale, the sizes of its strokes and its texts, the frames of its labels, the cuts a release makes in a member -- before anything is drawn: split out of calc/domains/statics_svg.py (issue #30), moved verbatim. statics_svg.py imports every name back and draws what this lays out. Qt-free.
"""

import math
import re
from domains import figure_style
from domains import figure_text
from domains import statics as model
from domains import svg_draw
from domains import dimension  # one unit vector and one label box (ARCH-004)
from i18n import strings


UNRESOLVED = svg_draw.colour("aid")


# The figure's own span: whatever the model measures, its longer side is drawn this many units wide.
FIGURE_SPAN = 1000.0


# The symbols' unit is that span divided by this, so every literal below reads as a percentage of the drawing.
UNIT_DIVISOR = 100.0


# A model with no extent at all -- one point, or none -- still needs something to normalise by. In metres.
MIN_EXTENT = 0.5


# The longest arrow of each kind, and the shortest one a load may be drawn with -- the fraction of the longest below which a small load would vanish beside a large one. The figure says so in its notes.
ARROW_POINT = 18.0


ARROW_LINE = 11.0


MIN_FRACTION = 0.35


# What a load whose magnitude could not be read is drawn at: visible, and visibly not a number.
UNKNOWN_FRACTION = 0.6


RELEASE_SPLIT = 0.9


RELEASE_CLEAR = 0.8


# A normal release is the one whose members do NOT stand clear of it: what it says is that the two halves slide along each other, so its two lines are a sleeve and the halves have to be seen inside it. Each drawn end stops this far from the node -- half the visible break, about as wide as a bar is thick -- which leaves each half reaching three quarters of the way out along the sleeve. A sleeve around nothing says nothing (v0.56).
RELEASE_SLIDE = 0.6


# A hinge is one circle wherever it stands: a moment release on a member, the pin of a Festlager or a Loslager, and the centre of a rotational spring -- all three are the same thing, a member free to turn. One radius and one stroke for all of them, so that they cannot come to be drawn differently.
HINGE_RADIUS = 1.7


HINGE_WIDTH = 0.6


# A rotational spring is a moment release with a stiffness, so it is drawn as that hinge with a coil around it: the coil opens from the circle's own edge out to SPRING_OUTER over SPRING_TURNS, keeping the ~1.6 between coils it has always had, since closer than that they read as hatching rather than as a spring (v0.56).
#
# The turns are a quarter past a whole one, and that is the whole of what makes it read as a coil rather than as a ring. The spiral starts along the member's own axis, so a whole or a half turn ends it back on that axis, where the member's line -- drawn thicker than the coil -- swallows the free end: with nothing to say where it stops, two rings around a hinge are what is left. A quarter turn past leaves the end square to the member, in the open.
SPRING_OUTER = 4.0


# How wide a member is drawn, by its kind. A hinge set back from a bar it runs over is moved until the circle just touches the bar's edge, so the pen's own width has to be known here as well as in _member.
MEMBER_WIDTH = {"bar": 1.15, "cable": 0.55, "spring": 0.6}


# A label's text height, as a fraction of the drawing. At the width the report prints a figure at this is about a 10 pt line -- and a label of a dozen characters then takes a fifth of the drawing, which is as much as one may take.
LABEL_TEXT = 2.4


LINE_SPACING = 1.25


# Arial's average character, as a fraction of its size, and a space, which is half of one: enough to keep a label's box honest and its pieces in step without measuring a font this module cannot see.
# Arial's advances, the subscripts and the typed `*`: calc/domains/svg_text.py, the one text engine of every figure since issue #43 (D-19), moved there unchanged -- every name is still importable from here.
from domains.svg_text import (  # noqa: E402
    _ARIAL_GROUPS, ARIAL_DEFAULT, ARIAL_WIDTHS, SUB_SCALE, SUBSCRIPT, TIMES, TYPED_TIMES, text_runs, text_width,
    advance as _advance,
)
from domains.dimension import _local  # plane geometry written once (D4)


# The notes under the drawing are set smaller than a label, as the report sets a table's note smaller than its cells.
NOTE_TEXT = 2.0


NOTE_SPACING = 1.5






def _to_figure(p, k):
    """A point of the model -- metres, x right and z down -- in the figure's units. The two frames agree in direction; only the scale differs."""
    return (p[0] * k, p[1] * k)


_unit = dimension.unit   # (ARCH-004: one copy, D-15)


def _add(p, u, t):
    return (p[0] + u[0] * t, p[1] + u[1] * t)


def _perp(u):
    return (-u[1], u[0])


def figure_scale(extent):
    """How many figure units one metre of a model of this extent is drawn as."""
    return FIGURE_SPAN / max(extent[0], extent[1], MIN_EXTENT)


def base_unit():
    """The symbols' unit, before the style sliders. A constant: the figure is normalised, not the symbols."""
    return FIGURE_SPAN / UNIT_DIVISOR


class Sizes:
    """A symbol's sizes, from the unit and the three sliders: `line` for strokes, arrowheads and arrows, `point` for the symbols placed on a node, `text` for the labels and their boxes. plan_svg's, unchanged."""

    def __init__(self, unit, style):
        self.u = unit
        self.lf = float(style.get("line", 1.0))
        self.pf = float(style.get("point", 1.0))
        self.tf = float(style.get("text", 1.0))

    def line(self, x):
        return x * self.u * self.lf

    def point(self, x):
        return x * self.u * self.pf

    def text(self, x):
        return x * self.u * self.tf

    def scaled(self, factors):
        """This, with `factors` multiplied into the three -- what one entry that states a factor of its own is drawn with (`figure_style`).

        A new object rather than a mutation: the drawing's own `sz` is read by everything else on the figure, and an entry's factors must reach that entry alone.
        """
        if not factors:
            return self
        return Sizes(self.u, {
            "line": self.lf * float(factors.get("line", figure_style.DEFAULT)),
            "point": self.pf * float(factors.get("point", figure_style.DEFAULT)),
            "text": self.tf * float(factors.get("text", figure_style.DEFAULT)),
        })


def sizes_of(source):
    """The sizes a model's symbols are drawn at, in figure units."""
    return Sizes(base_unit(), source.get("style", {}))


def entry_sizes(sz, entry):
    """The sizes one entry is drawn at: `sz` scaled by the factors that entry states over the drawing's, or **`sz` itself** where it states none (v0.99).

    Returning the very same object is what keeps a source that overrides nothing drawing byte for byte as it did before the factors existed: every length then comes out of the same three floats it always did, and `tests/test_statics.py` holds the figure against a frozen hash.
    """
    own = figure_style.stated(entry or {})
    return sz.scaled(own) if own else sz


def entry_factor(entry, key):
    """The factor one entry states over the drawing's for `key`, 1 where it states none -- what multiplies a length the drawing has already scaled, which is how a load's arrow follows its own `line` (`_scale_of` gives that length in the drawing's units)."""
    return figure_style.stated(entry or {}).get(key, figure_style.DEFAULT)


def scale_of(source):
    """The figure units one metre of this model is drawn as."""
    box = model.bbox(source)
    extent = (0.0, 0.0) if box is None else (box[2] - box[0], box[3] - box[1])
    return figure_scale(extent)


def _box(points, margin=0.0):
    """The bounding box of some points, widened by `margin`: (x0, z0, x1, z1)."""
    xs = [p[0] for p in points]
    zs = [p[1] for p in points]
    return (min(xs) - margin, min(zs) - margin, max(xs) + margin, max(zs) + margin)


def _union(boxes):
    boxes = [b for b in boxes if b is not None]
    if not boxes:
        return None
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def _label_box(lines, sz):
    """The half-width and half-height of a label of these lines."""
    size = sz.text(LABEL_TEXT)
    width = max((text_width(line, size) for line in lines), default=0.0)
    height = len(lines) * LINE_SPACING * size
    return (max(width, size) / 2.0 + sz.text(0.4), max(height, size) / 2.0 + sz.text(0.3))


def label_offset(entry, k=1.0):
    """How far the engineer moved a label from its own place, in figure units -- (0, 0) for one left where it is drawn by itself. Saved in metres, in the model's own frame, which the figure's agrees with."""
    offset = entry.get("label_offset")
    if not offset:
        return (0.0, 0.0)
    return (float(offset[0]) * k, float(offset[1]) * k)


def _frame(lines, home, sz, angle=0.0, along=(1.0, 0.0), offset=(0.0, 0.0)):
    """Where a label is drawn: `at`, the centre of its box, whose half-sides are `hw` along the text and `hh` across it; `angle`, the angle it is read at; `home`, its own place, which `at` is moved from; `moved`, whether it was; `sz`, the sizes it is set at -- its own entry's, so that `_label` sets the same text height the box was measured at. The shape plan_svg's number_frame returns, so Woodcore drags a label here exactly as it drags a position number there."""
    hw, hh = _label_box(lines, sz)
    return {
        "at": (home[0] + offset[0], home[1] + offset[1]),
        "home": home,
        "moved": bool(offset[0] or offset[1]),
        "angle": angle,
        "along": along,
        "hw": hw,
        "hh": hh,
        "lines": list(lines),
        "sz": sz,
    }


def on_label(frame, point, margin=0.0):
    """Whether `point` lies on a label's box, or within `margin` of it."""
    x, y = _local(frame, point)
    return abs(x) <= frame["hw"] + margin and abs(y) <= frame["hh"] + margin


label_corners = dimension.box_corners   # (ARCH-004: one copy)


def _readable(angle):
    """A label turned with its member is never read upside down."""
    a = model.normalize_angle(angle)
    return a + 180 if a > 90 or a <= -90 else a


def _release_extent(release, sz):
    """How far a release's symbol reaches from the node it stands on, in figure units -- what the frame has to take in, what a halo has to cover, and how far its own label has to stand off. A rotational spring's coil reaches further than anything else drawn at a node, so the three cannot be a constant (v0.56)."""
    if release["dof"] == "moment" and release["spring"]:
        return sz.point(SPRING_OUTER) + sz.line(0.5)
    return sz.point(4.0)


def _release_cuts(source, sz):
    """How far each member end is drawn back from its node, as {(member id, end): cut} in figure units.

    A release is drawn **on** the node it frees, so what it opens in the structure belongs to that node and not to the one member end the release happens to be recorded against. Where the node joins **exactly two** member ends -- a beam an articulation splits -- both are drawn back by the same amount, and the symbol sits in the middle of what they leave: which of the two halves carries the freedom is bookkeeping, while what the symbol says is that the two may move against each other. Drawing back only the released end, as this did until v0.55, put the whole break on one side of the node and the symbol across the other member's line. Where more than two ends meet, "the two halves" means nothing: the freedom is one member's, so only that end is drawn back.

    **How far** is the symbol's own affair, and the two symbols want opposite things (v0.56):

    - a **shear** release's halves slide across each other, so its two bars stand one each side of the node and the members come up to them and stop -- clear of the symbol, by its reach plus RELEASE_CLEAR of air;
    - a **normal** release's halves slide *along* each other, so its two lines are a sleeve and the members have to be seen **inside** it: each end stops RELEASE_SLIDE from the node, which is well within the sleeve, and what is left between them is a break about as wide as a bar is thick.

    The break is measured from the drawn ends, not the nominal ones: a member is drawn with a round cap, which reaches half its own stroke further, so half that stroke is added here. That is what keeps the break the same width whatever the `line` and `point` sliders are set to -- the calculation a support's pin already makes for the same reason.

    ⚠️ **The cut keeps the DRAWING's own factors, and not the member's or the release's** (v0.99). It is the price of the cut belonging to the node: both ends meeting there are drawn back by the same amount, which is this function's own rule, and a cut taken from each member's own `line` factor would open a break wider on one side of one node than on the other -- the very thing v0.55 repaired. A member or a release drawn heavier than its drawing therefore stands in a break sized for the drawing; what a heavier release does widen is its own symbol, and its extent (`_release_extent`) follows it.
    """
    point_of, ends_at, kind_of = {}, {}, {}
    for member in source.get("members", []):
        kind_of[member["id"]] = member.get("kind", "bar")
        for end, key in (("start", "p1"), ("end", "p2")):
            point = member.get(key)
            if point is None:
                continue
            point_of[(member["id"], end)] = point
            ends_at.setdefault(point, []).append((member["id"], end))
    cuts = {}
    for release in source.get("releases", []):
        dof = release.get("dof")
        if dof == "moment":
            continue
        held = (release.get("member"), release.get("end"))
        point = point_of.get(held)
        if point is None:
            continue
        joined = ends_at[point] if len(ends_at[point]) == 2 else [held]
        for key in joined:
            if dof == "normal":
                pen = sz.line(MEMBER_WIDTH.get(kind_of.get(key[0], "bar"), MEMBER_WIDTH["bar"]))
                cut = sz.point(RELEASE_SLIDE) + pen / 2
            else:
                cut = sz.point(RELEASE_SPLIT + RELEASE_CLEAR)
            cuts[key] = max(cuts.get(key, 0.0), cut)
    return cuts


def _member_gaps(source, mid, sz, k, cuts=None):
    """Where a member is interrupted by a release on one of its ends, as (start, end) distances from its p1, in figure units. SVG Tiny cannot clip, so the member is drawn as the stretches that clear the gap (connection_svg's rule)."""
    length = model.member_length(source, mid) * k
    cuts = _release_cuts(source, sz) if cuts is None else cuts
    gaps = []
    for end in ("start", "end"):
        cut = cuts.get((mid, end))
        if cut is None or cut <= 1e-9:
            continue
        gaps.append((0.0, cut) if end == "start" else (length - cut, length))
    # a gap that would swallow its member says less than the whole member does
    if sum(b - a for a, b in gaps) >= 0.8 * length:
        return []
    return sorted(gaps)


def _runs(a, b, gaps):
    """The stretches of the segment a-b left once the gaps are taken out, as pairs of points.

    A stretch of no length is dropped rather than drawn: a member is drawn with a round cap, and SVG renders a zero-length line with one as a dot -- which would put back, at the node, the very mark the gap was opened to clear. A gap reaching a member's far end leaves exactly such a stretch, the gap being measured from the model's own length and the run from the drawn points, which agree to all but their last bits.
    """
    length = math.dist(a, b)
    if length < 1e-12:
        return []
    u = _unit(a, b)
    runs, cursor = [], 0.0
    for start, end in gaps:
        if start - cursor > 1e-6:
            runs.append((_add(a, u, cursor), _add(a, u, start)))
        cursor = max(cursor, end)
    if length - cursor > 1e-6:
        runs.append((_add(a, u, cursor), b))
    return runs


def _support_frame(angle):
    """A support's own directions in the figure: `g` towards the ground, `t` along it. At 0 degrees the ground lies below (+z); the angle turns the whole symbol from x towards z, as every other angle here does."""
    r = math.radians(angle)
    g = (-math.sin(r), math.cos(r))
    return g, (-g[1], g[0])


def _scale_of(loads, longest, not_given=()):
    """How long each load of one kind is drawn: in proportion to its magnitude, but never under MIN_FRACTION of the longest, so a small load beside a large one stays visible. A load that **states** no value is drawn at the full length -- a value is only ever shown and scaled by, so its absence says nothing about how big the load is -- while one whose value could not be *read* is drawn short and grey. Returns (lengths by id, the ids held up to the minimum)."""
    magnitudes = {lid: abs(v) for lid, v in loads.items() if v is not None}
    top = max(magnitudes.values(), default=0.0)
    fractions, raised = {}, []
    for lid in loads:
        value = loads[lid]
        if lid in not_given:
            fractions[lid] = 1.0
        elif value is None:
            fractions[lid] = UNKNOWN_FRACTION
        elif top <= 0:
            fractions[lid] = MIN_FRACTION
        else:
            share = abs(value) / top
            if share < MIN_FRACTION:
                fractions[lid] = MIN_FRACTION
                raised.append(lid)
            else:
                fractions[lid] = share
    return {lid: f * longest for lid, f in fractions.items()}, raised


def layout(source, values=None, lang=strings.SOURCE_LANGUAGE):
    """Everything the figure draws, placed, and the frame that takes it all in.

    Returns a dict the three readers share: `render` writes it out, `meta` hands the placed geometry to the report's record, and Woodcore hit-tests against it. Coordinates are the figure's own -- the model's frame, x right and z down, scaled so its longer side is FIGURE_SPAN.

    Every placed thing carries the sizes it is drawn at, `sz` -- the drawing's own three times whatever factor its entry states over them (`entry_sizes`) -- and, where it states any, the `style` the export records. So a symbol drawn larger than its neighbours is larger in the figure, in its own box, in its label and in the halo the report may put under it, all from one place (v0.99).
    """
    values = values or {}
    sz = sizes_of(source)
    k = scale_of(source)
    boxes = []

    points = []
    at_of = {}
    for point in source.get("points", []):
        at = _to_figure((float(point["x"]), float(point["z"])), k)
        at_of[point["id"]] = at
        # a node is never drawn in the report (v0.56), so a point draws its label and nothing else: its own factor is `text`, which its label's frame carries, and the margin below is the dot Woodcore marks a clickable node with
        points.append({"id": point["id"], "at": at, "label": point.get("label", ""),
                       "style": figure_style.record(point)})
        boxes.append(_box([at], sz.point(1.6)))

    members = []
    cuts = _release_cuts(source, sz)
    for member in source.get("members", []):
        a, b = at_of.get(member.get("p1")), at_of.get(member.get("p2"))
        if a is None or b is None or math.dist(a, b) < 1e-12:
            continue
        u = _unit(a, b)
        own = entry_sizes(sz, member)
        members.append({
            "id": member["id"],
            "kind": member.get("kind", "bar"),
            "a": a,
            "b": b,
            "u": u,
            "n": _perp(u),
            "length_m": model.member_length(source, member["id"]),
            "runs": _runs(a, b, _member_gaps(source, member["id"], sz, k, cuts)),
            "label": member.get("label", ""),
            "stiffness": member.get("stiffness"),
            "sz": own,
            "style": figure_style.record(member),
        })
        boxes.append(_box([a, b], own.line(1.2)))
    member_by_id = {m["id"]: m for m in members}

    supports = []
    for support in source.get("supports", []):
        at = at_of.get(support.get("point"))
        if at is None:
            continue
        own = entry_sizes(sz, support)
        g, t = _support_frame(float(support.get("angle", 0.0)))
        reach = own.point(9.0)
        kind = support.get("type", "pinned")
        # A Festlager and a Loslager are hinges, so each carries the circle a moment release carries, and where that circle sits is the source's to say (statics.SUPPORT_HINGES). `shared` puts it on the node, the bar turning about the support's own pin. `through` is a bar running over the support: the circle is set back along the support's own axis -- usually straight down from a horizontal bar -- until it just touches the bar's edge, and the whole support hangs from it, apex against the circle. An Einspannung has no pin, and its hatched wall is the mark at its node.
        hinge = support.get("hinge", "shared") if kind in model.HINGED_SUPPORTS else None
        drop = 0.0
        if hinge == "through":
            # the widest pen actually drawn at this node, each member at its own `line` factor: the circle is set back until it just touches the bar's edge, and the bar's edge is where that bar's own stroke puts it
            widest = max((m["sz"].line(MEMBER_WIDTH.get(m["kind"], MEMBER_WIDTH["bar"]))
                          for m in members
                          if math.dist(m["a"], at) < 1e-9 or math.dist(m["b"], at) < 1e-9),
                         default=sz.line(MEMBER_WIDTH["bar"]))
            drop = widest / 2 + own.point(HINGE_RADIUS) + own.line(HINGE_WIDTH) / 2
        hinge_at = _add(at, g, drop) if hinge else None
        # the symbol proper starts at the node, or, where the bar runs over it, one circle further along the support's axis, so that its apex meets the circle
        origin = _add(hinge_at, g, own.point(HINGE_RADIUS) + own.line(HINGE_WIDTH) / 2) if drop else at
        supports.append({
            "id": support["id"],
            "point": support["point"],
            "type": kind,
            "angle": float(support.get("angle", 0.0)),
            "at": at,
            "hinge": hinge,
            "hinge_at": hinge_at,
            "origin": origin,
            "g": g,
            "t": t,
            "label": support.get("label", ""),
            "sz": own,
            "style": figure_style.record(support),
        })
        boxes.append(_box([_add(_add(origin, g, reach), t, reach), _add(_add(at, g, -1.0), t, -reach)]))

    releases = []
    for release in source.get("releases", []):
        member = member_by_id.get(release.get("member"))
        if member is None:
            continue
        # a release sits exactly on the node it frees, whatever it frees
        centre = member["a"] if release["end"] == "start" else member["b"]
        u = member["u"] if release["end"] == "start" else (-member["u"][0], -member["u"][1])
        own = entry_sizes(sz, release)
        releases.append({
            "id": release["id"],
            "member": member["id"],
            "end": release["end"],
            "dof": release.get("dof"),
            "spring": release.get("stiffness") is not None,
            "stiffness": release.get("stiffness"),
            "at": centre,
            "u": u,
            "n": _perp(u),
            "label": release.get("label", ""),
            "sz": own,
            "style": figure_style.record(release),
        })
        boxes.append(_box([centre], _release_extent(releases[-1], own)))

    # The dimensions, placed but not yet drawn: a length runs between two ends carried onto its own line, an angle sweeps an arc about the corner its two members make. Both are worked out in metres by statics.py and brought here, so that what the list says and what the figure shows cannot drift.
    dimensions = []
    for dim in source.get("dimensions", []):
        text = model.dimension_text(source, dim)
        value, unit = model.dimension_value(source, dim)
        own = entry_sizes(sz, dim)
        if dim.get("kind") == "angle":
            turn = model.dimension_angle(source, dim)
            if turn is None:
                continue
            centre, sweep, start = turn
            # the radius is the model's own geometry -- the offset the third click wrote, in metres -- and no size, so no factor reaches it
            radius = abs(float(dim.get("offset", 0.0))) * k
            at = _to_figure(centre, k)
            arc = _arc_points(at, start, sweep, radius)
            middle = _arc_at(at, start + sweep / 2.0, radius)
            dimensions.append({
                "id": dim["id"], "kind": "angle", "centre": at, "at": middle, "arc": arc,
                "start": start, "sweep": sweep, "radius": radius,
                "value": value, "unit": unit, "text": text, "show": model.dimension_show(dim),
                "sz": own, "style": figure_style.record(dim),
            })
            boxes.append(_box(arc, own.line(1.0)))
            continue
        ends = model.dimension_ends(source, dim)
        line = model.dimension_line(source, dim)
        if ends is None or line is None:
            continue
        a, b = (_to_figure(q, k) for q in ends)
        p0, p1 = (_to_figure(q, k) for q in line)
        middle = ((p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0)
        # which way the text sits above its own line, and which way the witness lines run out past it
        u = _unit(p0, p1) if math.dist(p0, p1) > 1e-12 else (1.0, 0.0)
        # the value is written on the side the line was carried to, which is where the model is not: taken from the two middles rather than from the sign of the offset, since which way `n` points is the kind's business and not the drawing's
        mid_ends = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
        away = _unit(mid_ends, middle) if math.dist(mid_ends, middle) > 1e-9 else _perp(u)
        dimensions.append({
            "id": dim["id"], "kind": dim.get("kind"), "ends": (a, b), "line": (p0, p1),
            "at": middle, "u": u, "n": _perp(u), "away": away,
            "value": value, "unit": unit, "text": text, "show": model.dimension_show(dim),
            "sz": own, "style": figure_style.record(dim),
        })
        boxes.append(_box([a, b, p0, p1], own.line(1.2)))

    # Two scales, one per kind: a kN and a kN/m cannot share one. Within a kind, equal magnitudes give equal arrows.
    point_values, line_values, resolved_by, not_given = {}, {}, {}, set()
    for collection, load, res, end in model.resolved_loads(source, values):
        resolved_by[load["id"]] = (collection, load, res, end)
        if not res["given"]:
            not_given.add(load["id"])
        peak = None
        if res["value"] is not None:
            peak = abs(res["value"])
            if end is not None and end["value"] is not None:
                peak = max(peak, abs(end["value"]))
        (point_values if collection == "point_loads" else line_values)[load["id"]] = peak
    point_lengths, point_raised = _scale_of(point_values, sz.line(ARROW_POINT), not_given)
    line_lengths, line_raised = _scale_of(line_values, sz.line(ARROW_LINE), not_given)
    # Line loads on one member and pointing one way are stacked rather than drawn over each other: each band sits on the one before it, and the running height is kept here.
    stacked = {}

    loads, notes, raised_notes = [], [], []
    for lid, (collection, load, res, end) in resolved_by.items():
        lines = model.load_lines(load, res, end)
        colour_name = model.load_colour(load)
        colour = model.LOAD_COLOURS[colour_name]
        if res["given"] and res["value"] is None:
            colour = UNRESOLVED
        own = entry_sizes(sz, load)
        entry = {
            "id": lid,
            "sz": own,
            "style": figure_style.record(load),
            "kind": "point" if collection == "point_loads" else "line",
            "collection": collection,
            "label": load.get("label", ""),
            "show": load.get("show", "name+value"),
            "lines": lines,
            "colour": colour,
            "colour_name": colour_name,
            "value": res["value"],
            "unit": res["unit"],
            "base_value": res["base_value"],
            "base_unit": res["base_unit"],
            "from": res["from"],
            "missing": res["missing"],
            "given": res["given"],
            "factor": res["factor"],
            "offset": res["offset"],
            "description": res["description"],
            "arrows": [],
        }
        width = load.get("width")
        if width:
            entry["width"] = float(width["value"])
            entry["width_label"] = (width.get("label") or model.DEFAULT_WIDTH_LABEL).strip()
        if res["given"] and res["missing"]:
            notes.append(strings.text("figure.value_not_found", lang) + lid)

        if collection == "point_loads":
            anchor = model.load_at(source, load)
            direction = model.load_direction(source, load)
            if anchor is None or direction is None:
                continue
            tip = _to_figure(anchor, k)
            d = direction
            # the length the two scales gave this load, times whatever `line` it states of its own: deliberately, so that two loads of equal magnitude no longer draw equal arrows where the engineer asked for one of them to stand out (v0.99). A figure whose arrows are proportional to their magnitudes is the default and stays it -- this is the exception said out loud, and the notes still name what was held up to the minimum.
            length = point_lengths.get(lid, sz.line(ARROW_POINT)) * entry_factor(load, "line")
            tail = _add(tip, d, -length)
            entry.update({"at": tip, "anchor": tip, "d": d, "arrows": [(tail, tip)], "tail": tail})
            boxes.append(_box([tail, tip], own.line(1.5)))
            if lid in point_raised:
                raised_notes.append(f"{load.get('label') or lid} = {model.figure_number(res['value'])} {res['unit']}".strip())
        else:
            member = member_by_id.get(load.get("member"))
            span = model.line_load_span(source, load)
            direction = model.load_direction(source, load, load.get("member"))
            if member is None or span is None or direction is None:
                continue
            a, b = _to_figure(span[0], k), _to_figure(span[1], k)
            d = direction
            top = line_lengths.get(lid, sz.line(ARROW_LINE)) * entry_factor(load, "line")
            if res["value"] is None or (end is not None and end["value"] is None):
                ha = hb = top
            else:
                peak = max(abs(res["value"]), abs(end["value"]) if end is not None else 0.0) or 1.0
                ha = top * abs(res["value"]) / peak
                hb = top * (abs(end["value"]) / peak if end is not None else abs(res["value"]) / peak)
            # another load already on this member, pointing the same way, holds this one off it
            key = (member["id"], round(d[0], 6), round(d[1], 6))
            base = stacked.get(key, 0.0)
            foot_a, foot_b = _add(a, d, -base), _add(b, d, -base)
            cap_a, cap_b = _add(foot_a, d, -ha), _add(foot_b, d, -hb)
            # the label goes inside the band; where the band is too shallow to hold it, it steps out past the cap, and the next load on this member starts beyond it
            label_height = _label_height(lines, own)
            band = (ha + hb) / 2.0
            outside = label_height > band
            reach = max(ha, hb) + (label_height + own.line(0.8) if outside else 0.0)
            stacked[key] = base + reach + own.line(1.6)
            count = max(2, min(14, int(round(math.dist(a, b) / max(own.line(4.5), 1e-9))) + 1))
            arrows = []
            for i in range(count):
                t = i / (count - 1)
                foot = (foot_a[0] + (foot_b[0] - foot_a[0]) * t, foot_a[1] + (foot_b[1] - foot_a[1]) * t)
                head = (cap_a[0] + (cap_b[0] - cap_a[0]) * t, cap_a[1] + (cap_b[1] - cap_a[1]) * t)
                if math.dist(foot, head) > own.line(0.6):
                    arrows.append((head, foot))
            # the label sits inside the band, between its cap and its foot -- above it, it would be read as the next load's
            middle = (
                (cap_a[0] + cap_b[0] + foot_a[0] + foot_b[0]) / 4.0,
                (cap_a[1] + cap_b[1] + foot_a[1] + foot_b[1]) / 4.0,
            )
            if outside:
                middle = _add(middle, d, -(band + label_height) / 2.0 - own.line(0.8))
            entry.update({
                "at": middle, "a": foot_a, "b": foot_b, "cap_a": cap_a, "cap_b": cap_b, "d": d,
                "member_id": member["id"], "base": base,
                "arrows": arrows, "shape": load.get("shape", "uniform"),
                "end_value": None if end is None else end["value"],
                "end_missing": "" if end is None else end["missing"],
            })
            if end is not None and end["given"] and end["missing"]:
                notes.append(strings.text("figure.value_not_found", lang) + lid)
            boxes.append(_box([a, b, foot_a, foot_b, cap_a, cap_b], own.line(1.0)))
            if lid in line_raised:
                raised_notes.append(f"{load.get('label') or lid} = {model.figure_number(res['value'])} {res['unit']}".strip())
        loads.append(entry)

    # The labels come last: every one of them is placed against something already placed.
    labels = []

    def place(collection, owner, lines, anchor, away, gap, angle=0.0, along=(1.0, 0.0), entry=None):
        """A label, set clear of what it names: `away` from `anchor` by its own half-height and `gap`, so a long label and a short one keep the same distance from the drawing.

        The label is set at its **entry's** own sizes (`entry_sizes`), which the frame carries: a text factor stated on one member enlarges that member's label, its white box, its leader and the room the frame leaves for it, and nothing else on the figure. The `gap` is the caller's, who knows which symbol the label has to clear and at what size that symbol is drawn.
        """
        if not lines:
            return
        own = entry_sizes(sz, entry or {})
        _hw, hh = _label_box(lines, own)
        home = _add(anchor, away, hh + gap)
        frame = _frame(lines, home, own, angle, along, label_offset(entry or {}, k))
        frame.update({"collection": collection, "owner": owner})
        labels.append(frame)
        boxes.append(_box(label_corners(frame)))

    # A member's label goes on the side its line loads are not on: they take the other one, and a label under a row of arrows cannot be read.
    load_side = {}
    for load in loads:
        if load["kind"] == "line":
            load_side.setdefault(load.get("member_id"), load["d"])

    source_by = {c: {e["id"]: e for e in source.get(c, [])} for c in model.ENTITIES}
    for point in points:
        if point["label"]:
            place("points", point["id"], [point["label"]], point["at"], (0.0, -1.0), sz.point(1.6),
                  entry=source_by["points"][point["id"]])
    for member in members:
        lines = [member["label"]] if member["label"] else []
        if member["kind"] == "spring" and member["stiffness"] and not lines:
            lines = [f"k = {model.figure_number(member['stiffness']['value'])} {member['stiffness']['unit']}"]
        if lines:
            mid = ((member["a"][0] + member["b"][0]) / 2.0, (member["a"][1] + member["b"][1]) / 2.0)
            angle = _readable(math.degrees(math.atan2(member["u"][1], member["u"][0])))
            d = load_side.get(member["id"])
            n = member["n"]
            if d is not None and (d[0] * n[0] + d[1] * n[1]) < 0:
                n = (-n[0], -n[1])
            place("members", member["id"], lines, mid, n, member["sz"].line(1.6), angle, member["u"],
                  source_by["members"][member["id"]])
    for support in supports:
        if support["label"]:
            place("supports", support["id"], [support["label"]], support["origin"], support["g"],
                  support["sz"].point(9.5), entry=source_by["supports"][support["id"]])
    for release in releases:
        lines = [release["label"]] if release["label"] else []
        if release["spring"] and not lines:
            stiffness = release["stiffness"]
            lines = [f"k = {model.figure_number(stiffness['value'])} {stiffness['unit']}"]
        if lines:
            # clear of the symbol itself, at the size that symbol is drawn: a rotational spring's "k = ..." set at a constant would fall across its coils
            own = release["sz"]
            place("releases", release["id"], lines, release["at"], release["n"],
                  max(own.point(2.2), _release_extent(release, own) - own.point(0.4)),
                  entry=source_by["releases"][release["id"]])
    for dim in dimensions:
        entry = source_by["dimensions"].get(dim["id"], {})
        # a dimension whose `show` writes nothing -- `none`, or a name it was not given -- is drawn with no label at all, and so with no box to hit or to size the frame by
        lines = [dim["text"]] if dim["text"] else []
        if dim["kind"] == "angle":
            away = _unit(dim["centre"], dim["at"]) if math.dist(dim["centre"], dim["at"]) > 1e-9 else (0.0, -1.0)
            place("dimensions", dim["id"], lines, dim["at"], away, dim["sz"].line(0.6), entry=entry)
        else:
            # turned with its own line and read from the same side as a member's label, so a vertical dimension reads upwards
            angle = _readable(math.degrees(math.atan2(dim["u"][1], dim["u"][0])))
            place("dimensions", dim["id"], lines, dim["at"], dim["away"], dim["sz"].line(0.6),
                  angle, dim["u"], entry)
    for load in loads:
        if not load["lines"]:
            continue
        entry = source_by[load["collection"]][load["id"]]
        if load["kind"] == "point":
            place(load["collection"], load["id"], load["lines"], load["tail"],
                  (-load["d"][0], -load["d"][1]), load["sz"].line(0.8), entry=entry)
        else:
            place(load["collection"], load["id"], load["lines"], load["at"], (0.0, 0.0), 0.0, entry=entry)
        labels[-1]["unresolved"] = load["given"] and load["value"] is None
    # a text placed with the Text tool (issue #43): its lines as they print now, figure_text's, centred on its own place -- a frame like any label's, so Woodcore hits it, drags it and rings it as it does a label
    for text in source.get(figure_text.COLLECTION, []):
        at = _to_figure((float(text["x"]), float(text["z"])), k)
        place(figure_text.COLLECTION, text["id"], figure_text.lines(text, values) or [""], at, (0.0, 0.0), 0.0, entry=text)

    # what the figure has to say about its numbers, under the drawing: the model's own influence width, then every load whose value was read from somewhere or taken with a factor
    note = model.width_note(source.get("width"))
    if note:
        notes.append(note)
    for collection, load, res, _end in model.resolved_loads(source, values):
        own = load.get("width")
        if own:
            note = model.width_note(own)
            if note:
                notes.append(note)
        note = model.value_note(load, res, model.width_of(source, load)[0])
        if note:
            notes.append(note)
    if raised_notes:
        notes.insert(0, strings.text("figure.enlarged", lang) + ", ".join(sorted(set(raised_notes))))
    notes = list(dict.fromkeys(notes))

    frame_box = _union(boxes) or (-1.0, -1.0, 1.0, 1.0)
    pad = sz.text(2.4)
    x0, y0, x1, y1 = frame_box[0] - pad, frame_box[1] - pad, frame_box[2] + pad, frame_box[3] + pad
    note_size = sz.text(NOTE_TEXT)
    if notes:
        # the notes take a band under the drawing, and the frame widens for the longest of them rather than letting it run off the page
        y1 += len(notes) * NOTE_SPACING * note_size + pad
        widest = max(text_width(note, note_size) for note in notes)
        x1 = max(x1, x0 + widest + 2 * pad)
    view = {"x": x0, "y": y0, "w": max(x1 - x0, 1e-6), "h": max(y1 - y0, 1e-6)}

    # A node the drawing already has a symbol for is not also given a dot: a release stands on its node, a fixed support's hatched wall is the mark at its own, and a hinge shared with the bar is the pin drawn there. A dot under any of them would only thicken the symbol, and under the wall it would sit half inside it.
    held = set()
    for release in releases:
        for point in points:
            if math.dist(point["at"], release["at"]) < 1e-9:
                held.add(point["id"])
    for support in supports:
        if support["type"] == "fixed" or support["hinge"] == "shared":
            held.add(support["point"])

    return {
        "sz": sz,
        "k": k,
        "unit": sz.u,
        "hidden_nodes": held,
        "style": {key: float(source.get("style", {}).get(key, 1.0)) for key in model.STYLE_KEYS},
        "points": points,
        "members": members,
        "supports": supports,
        "releases": releases,
        "dimensions": dimensions,
        "loads": loads,
        "labels": labels,
        "notes": notes,
        "note_size": note_size,
        "view": view,
    }


def label_frames(source, values=None, drawing=None):
    """Every label the figure draws, in the order it draws them, the last on top: [(collection, id, frame)]. In the figure's units."""
    drawing = drawing or layout(source, values)
    return [(f["collection"], f["owner"], f) for f in drawing["labels"]]


def hit_label(source, point, tolerance, frames=None, k=None):
    """The (collection, id) whose label box lies under `point` -- in the model's frame, metres. The one drawn last wins, labels being drawn over everything."""
    frames = frames if frames is not None else label_frames(source)
    k = scale_of(source) if k is None else k
    p = _to_figure(point, k)
    for collection, owner, frame in reversed(frames):
        if on_label(frame, p, tolerance * k * 0.5):
            return collection, owner
    return None, None


def hit_load(source, point, tolerance, drawing=None):
    """The (collection, id) of the load whose arrows lie under `point` -- in the model's frame, metres."""
    drawing = drawing or layout(source)
    p = _to_figure(point, drawing["k"])
    best, best_d = (None, None), tolerance * drawing["k"]
    for load in drawing["loads"]:
        for a, b in load["arrows"]:
            d, _q = model._point_segment(p, a, b)
            if d <= best_d:
                best, best_d = (load["collection"], load["id"]), d
    return best


def _arc_at(centre, degrees, radius):
    """One point of an arc, at `degrees` on the drawing."""
    a = math.radians(degrees)
    return (centre[0] + radius * math.cos(a), centre[1] + radius * math.sin(a))


def _arc_points(centre, start, sweep, radius, step=6.0):
    """An arc as the polyline SVG Tiny leaves for it -- connection_svg's moment arc, at a step fine enough that a quarter turn reads round. At least four segments, so even a short arc is a curve."""
    steps = max(4, int(abs(sweep) / step) + 1)
    return [_arc_at(centre, start + sweep * i / steps, radius) for i in range(steps + 1)]


def _label_height(lines, sz):
    """How tall a label is set: its lines, at the spacing `_label` stacks them with. What decides whether a line load's band can hold it."""
    if not lines:
        return 0.0
    size = sz.text(LABEL_TEXT)
    return (len(lines) - 1) * LINE_SPACING * size + size
