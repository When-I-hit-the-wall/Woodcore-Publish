"""The drawing of a static model, as SVG text: the members, where they are held, where they are hinged, and what acts on them, with the figure's frame computed from what it actually draws (docs/domain/static-models.md §3.3octies).

One drawing serves both places it is seen. Woodcore's window shows it while a model is edited, and the export writes it to data/statics/<id>.svg, which lib/calc-engine.typ's show-static-model sets in the report -- so the system the engineer drew is the system the checker reads. That is why it is built as plain text here, with no Qt: export_all.py draws it too, without a window.

It is kept to what both renderers read alike. QtSvg implements SVG Tiny 1.2, which has no <marker>, no clipPath, no <pattern>, no CSS, no paint-order and no arc command: an arrowhead is a polygon, a member interrupted by a hinge is drawn as the stretches that clear it, a moment spring's spiral is a polyline, a subscript is a second <text> set smaller and lower, and a label's white halo is a rectangle, its own box turned with its text (v0.77). A `transform="rotate(...)"` is read by both and is what draws a support upright once and turns it.

**The frame is computed, not given.** A plan's frame is its crop, which the engineer drew; a static model's has to take in a load arrow that reaches well past the last node. So `layout()` places everything and notes the box of each thing, `meta()` hands the placed geometry to the report's record, and `render()` writes the text -- the arrangement connection_svg.py has, for the same reason.

**Every size is two factors deep** (v0.99): the drawing's own three -- the strokes, the symbols placed on a node, the texts -- and, over them, whatever factor one entry states of its own (`entry_sizes`, `calc/domains/figure_style.py`). `layout()` works the pair out once per entry and hands it down as that entry's `sz`, so the symbol, its own box in the frame, its label and the halo the report may put under it all come out at one size. An entry that states nothing is handed the drawing's own `sz`, the very object -- which is what keeps a source written before the factors existed drawing byte for byte as it did.

Coordinates are the model's own -- x to the right, z down, as statics.py states them -- scaled so that the model's longer side is FIGURE_SPAN units. Every size below is then a constant of this module rather than a fraction of a project's spans, which is what makes a 2 m model and a 20 m one come out identical, and what keeps a font size in the range a renderer reads: QtSvg silently drops a `<text>` of 0.26 user units while still painting its halo, which is what a figure drawn in metres would ask it for.
"""

import math
import re
from xml.sax.saxutils import escape

from domains import figure_style
from domains import figure_text  # a text placed with the Text tool (issue #43)
from domains import svg_text  # the one text engine of every figure (D-19)
from domains import statics as model
from i18n import strings
from domains.statics_svg_layout import (  # split out of this module (issue #30): every name it had is still importable from it
    ARIAL_DEFAULT,
    ARIAL_WIDTHS,
    ARROW_LINE,
    ARROW_POINT,
    FIGURE_SPAN,
    HINGE_RADIUS,
    HINGE_WIDTH,
    LABEL_TEXT,
    LINE_SPACING,
    MEMBER_WIDTH,
    MIN_EXTENT,
    MIN_FRACTION,
    NOTE_SPACING,
    NOTE_TEXT,
    RELEASE_CLEAR,
    RELEASE_SLIDE,
    RELEASE_SPLIT,
    SPRING_OUTER,
    SUBSCRIPT,
    SUB_SCALE,
    Sizes,
    TIMES,
    TYPED_TIMES,
    UNIT_DIVISOR,
    UNKNOWN_FRACTION,
    UNRESOLVED,
    _ARIAL_GROUPS,
    _add,
    _advance,
    _arc_at,
    _arc_points,
    _box,
    _frame,
    _label_box,
    _label_height,
    _local,
    _member_gaps,
    _perp,
    _readable,
    _release_cuts,
    _release_extent,
    _runs,
    _scale_of,
    _support_frame,
    _to_figure,
    _union,
    _unit,
    base_unit,
    entry_factor,
    entry_sizes,
    figure_scale,
    hit_label,
    hit_load,
    label_corners,
    label_frames,
    label_offset,
    layout,
    on_label,
    scale_of,
    sizes_of,
    text_runs,
    text_width,
)

# The colours. A bar is the drawing's own black; a cable and a spring are set apart, being members that carry along their axis only; the supports and the hinges are the structure's, the loads the action's.
BAR = "#1f1f1f"
CABLE = "#1f6fb2"
SPRING = "#1f6fb2"
SUPPORT = "#1f1f1f"
RELEASE = "#1f1f1f"
# a dimension measures the drawing and is not part of it, so it is written in the drawing's own ink and set apart by its thinner line rather than by a colour of its own
DIMENSION = "#1f1f1f"
# A load's ink is its own (statics.LOAD_COLOURS): the colour it states, red where it states none -- the colour every load was drawn in before the engineer could choose, so a model saved before then draws exactly as it did. Its arrows, its band and its cap take it; its label stays in the drawing's own ink, being text set on a white box and read the same whatever colour the arrows are.
NODE = "#1f1f1f"
LABEL = "#1f1f1f"
NOTE_COLOUR = "#6b6b6b"
HIGHLIGHT_COLOUR = "#ffd34d"
# One family, not a list: QtSvg takes the whole font-family string as a single name, so "Arial, Helvetica, sans-serif" matches nothing and it falls back to a face whose advances are not Arial's -- which put every subscript, placed where ARIAL_WIDTHS says the run before it ends, beside its letter instead of under it. resvg reads a bare family too, and a machine without Arial substitutes Liberation Sans, which has the same advances.
FONT = "Arial"

# Where the report puts what only the call knows: a halo under the parts it highlights, and the loads, which `loads: false` removes so a bare system can be shown first. The loads' arrows and their labels are two separate stretches, and one regex takes both.
HIGHLIGHT_MARK = "<!-- highlight -->"
LOADS_OPEN = "<!-- loads -->"
LOADS_CLOSE = "<!-- /loads -->"
# the dimensions have a region of their own, between the structure and the loads: a system may be shown with its dimensions and without its actions, or the other way round
DIMS_OPEN = "<!-- dims -->"
DIMS_CLOSE = "<!-- /dims -->"


# The figure's intrinsic size, in millimetres along its longer side. The report gives it a width of its own; this is what it falls back to.
PAPER_MM = 150.0


# How far a release that is not a moment reaches along the member it sits on: half the length of a normal release's two parallel lines, and the offset of a shear release's two bars either side of the node. The member ends meeting at that node are cut back by that reach plus RELEASE_CLEAR of air, so the gap is the symbol's own size and no wider. They are stated here, once, because the symbol and the gap it needs cannot be allowed to drift apart.
RELEASE_HALF = 2.4
# How far each of that sleeve's two lines lies off the member's axis. Wide enough that the white between the sleeve and the bar can be seen at the size the report prints a figure: without it the three run together into one thick band, and the bar is no longer visibly *between* the lines.
RELEASE_SLEEVE = 1.35


SPRING_TURNS = 1.25

# How much of the way from the dimension line to what it measures a witness line actually covers: a quarter of it, leaving the three quarters nearest the model empty (v0.57). A line that runs the whole way is read as part of the structure; a quarter of it says which point is meant and nothing more. DIM_WITNESS_MIN, in point units, keeps a line on a dimension drawn close to the model, where a quarter would be nothing at all.
DIM_WITNESS_SHARE = 0.25
DIM_WITNESS_MIN = 1.0


# The notes under the drawing come out of the glossary, in the language the figure is drawn in (docs/typst/language.md
# §4bis). They are the only words of this figure that are the engine's: a label, a value and a
# description are all the engineer's, and stay as he wrote them.


SUB_DROP = svg_text.SUB_DROP   # svg_text's, named here as it always was


def _f(value):
    """A coordinate as short SVG text: three decimals at most, trailing zeros dropped."""
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def _pts(points):
    return " ".join(f"{_f(x)},{_f(y)}" for x, y in points)


def _to_model(p, k):
    """The way back, for a pointer over Woodcore's canvas."""
    return (p[0] / k, p[1] / k)


def _own(placed, sz):
    """The sizes a placed thing is drawn at: the ones `layout` worked out for its entry, else the drawing's -- so a dict built by hand still draws."""
    return placed.get("sz") or sz


def _grown(placed, sz, nominal, key):
    """A halo's width: `nominal` in the drawing's own `point` unit, carried by the factor the part it marks states for `key`. A member's bar is widened by its `line`, and a ring at the drawing's width would then be thinner than the bar it is there to mark."""
    return sz.point(nominal) * (placed.get("style") or {}).get(key, figure_style.DEFAULT)


# --- Primitives -----------------------------------------------------------------


def _line(out, a, b, colour, width, dash=None, cap="round"):
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    out.append(
        f'<line x1="{_f(a[0])}" y1="{_f(a[1])}" x2="{_f(b[0])}" y2="{_f(b[1])}" '
        f'stroke="{colour}" stroke-width="{_f(width)}" stroke-linecap="{cap}"{extra}/>'
    )


def _polyline(out, points, colour, width, dash=None, cap="round", fill="none"):
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    out.append(
        f'<polyline points="{_pts(points)}" fill="{fill}" stroke="{colour}" stroke-width="{_f(width)}" '
        f'stroke-linejoin="round" stroke-linecap="{cap}"{extra}/>'
    )


def _polygon(out, points, fill, stroke=None, width=0.0):
    extra = f' stroke="{stroke}" stroke-width="{_f(width)}" stroke-linejoin="round"' if stroke else ""
    out.append(f'<polygon points="{_pts(points)}" fill="{fill}"{extra}/>')


def _circle(out, centre, r, fill, stroke=None, width=0.0):
    extra = f' stroke="{stroke}" stroke-width="{_f(width)}"' if stroke else ""
    out.append(f'<circle cx="{_f(centre[0])}" cy="{_f(centre[1])}" r="{_f(r)}" fill="{fill}"{extra}/>')


def _arrow(out, tail, tip, colour, sz, scale=1.0):
    """A force arrow: a stem and a polygon head, the head never more than half the arrow long, so a short arrow is still an arrow."""
    length = math.dist(tail, tip)
    if length < 1e-12:
        return
    u = _unit(tail, tip)
    head = min(sz.line(3.2) * scale, 0.5 * length)
    half = sz.line(1.15) * scale
    base = _add(tip, u, -head)
    p = _perp(u)
    _line(out, tail, base, colour, sz.line(0.75) * scale, cap="butt")
    _polygon(out, [tip, _add(base, p, half), _add(base, p, -half)], colour)


# --- Text, with the subscripts an engineer writes -------------------------------


def _text(out, point, content, size, colour, anchor="middle", bold=False, rotate=None, halo=None):
    """A text, its subscripts set smaller and lower -- svg_text.draw, the one text engine of every figure (D-19). `halo` draws it first in white, `halo` wide, so it reads over whatever is behind it."""
    svg_text.draw(out, point, content, size, colour, anchor, bold, rotate, halo)


# --- Labels ---------------------------------------------------------------------


# --- Placing everything ---------------------------------------------------------


def support_angle(g):
    """The angle a ground direction stands for -- what Woodcore writes back while the pointer turns a support."""
    return model.normalize_angle(math.degrees(math.atan2(-g[0], g[1])))


# --- Hit-testing, for Woodcore -----------------------------------------------


# --- The symbols ----------------------------------------------------------------


def _hatch(out, centre, g, t, sz, half=None, colour=SUPPORT):
    """A ground line with its hatching -- the one helper all three supports stand on. `g` points into the ground, `t` along it."""
    half = half if half is not None else sz.point(4.6)
    a, b = _add(centre, t, -half), _add(centre, t, half)
    _line(out, a, b, colour, sz.line(0.7))
    n, reach, step = 7, sz.point(2.4), 2 * half / 7
    for i in range(n):
        foot = _add(a, t, step * (i + 0.5))
        # the stroke leans at 45 degrees into the ground, which is the convention wherever it is drawn
        _line(out, foot, _add(_add(foot, g, reach), t, -reach), colour, sz.line(0.45))


def _support(out, support, sz):
    """A support, drawn from its own origin: the node, or -- where the bar runs over it -- a circle's diameter down the support's axis, so that its apex meets the pin (`_hinge`)."""
    g, t = support["g"], support["t"]
    height, half = sz.point(6.0), sz.point(3.5)
    if support["type"] == "fixed":
        _hatch(out, support["at"], g, t, sz, half=sz.point(5.2))
        return
    apex = support["origin"]
    base_a, base_b = _add(_add(apex, g, height), t, -half), _add(_add(apex, g, height), t, half)
    _polygon(out, [apex, base_a, base_b], "#ffffff", SUPPORT, sz.line(0.7))
    if support["type"] == "pinned":
        _hatch(out, _add(apex, g, height), g, t, sz)
    else:
        r = sz.point(1.0)
        for side in (-1, 1):
            _circle(out, _add(_add(apex, g, height + r), t, side * half * 0.55), r, "#ffffff", SUPPORT, sz.line(0.55))
        _hatch(out, _add(apex, g, height + 2 * r), g, t, sz)
    # the pin last, over the triangle's apex and over whatever member runs past it: a Festlager and a Loslager are hinges, and this is the circle a moment release is drawn as
    if support["hinge_at"] is not None:
        _hinge(out, support["hinge_at"], sz)


def _hinge(out, at, sz):
    """A hinge: the white circle a moment release is drawn as, and the pin of a Festlager or a Loslager."""
    _circle(out, at, sz.point(HINGE_RADIUS), "#ffffff", RELEASE, sz.line(HINGE_WIDTH))


def _spring_inner(sz):
    """Where a rotational spring's coil starts: the outer edge of the hinge circle at its centre, so the coil comes out from behind it rather than from under it."""
    return sz.point(HINGE_RADIUS) + sz.line(HINGE_WIDTH) / 2


def _spiral(centre, u, sz, turns=SPRING_TURNS, samples=120):
    """A moment spring, as the polyline SVG Tiny leaves for an arc: an Archimedean spiral opening from the hinge at its centre. Fewer than two turns, and opening wide: coils any closer read as hatching rather than as a spring."""
    r0, r1 = _spring_inner(sz), sz.point(SPRING_OUTER)
    start = math.atan2(u[1], u[0])
    pts = []
    for i in range(samples + 1):
        s = i / samples
        a = start + turns * 2 * math.pi * s
        r = r0 + (r1 - r0) * s
        pts.append((centre[0] + r * math.cos(a), centre[1] + r * math.sin(a)))
    return pts


def _zigzag(a, b, across, sz, teeth=5, amplitude=1.5):
    """A spring, as a polyline between two points, its teeth `across` wide to the side."""
    pts = [a]
    for i in range(2 * teeth):
        t = (i + 0.5) / (2 * teeth)
        base = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        pts.append(_add(base, across, sz.point(amplitude) * (1 if i % 2 == 0 else -1)))
    pts.append(b)
    return pts


def _release(out, release, sz):
    """A release, drawn on the node it frees.

    The two lines say which way the halves may move against each other: **along** the member for a normal-force release, so they are drawn parallel to it and the member's two ends are seen sliding inside them; **across** it for a shear release, so they are drawn perpendicular and the two ends come up to them. A moment release is the circle everyone draws, and a moment spring is that same circle with a spiral around it -- a rotational spring frees the moment like any hinge, so a black centre there would read as a fixed end with a coil hung on it (v0.56).
    """
    at, u, n = release["at"], release["u"], release["n"]
    dof, spring = release["dof"], release["spring"]
    if dof == "moment":
        if spring:
            _polyline(out, _spiral(at, u, sz), RELEASE, sz.line(0.5))
        # the hinge last, over the coil and over the member's own line
        _hinge(out, at, sz)
        return
    if dof == "normal":
        # the halves slide along the member: two short lines parallel to it, one each side
        half = sz.point(RELEASE_HALF)
        for side in (-1, 1):
            offset = _add(at, n, side * sz.point(RELEASE_SLEEVE))
            _line(out, _add(offset, u, -half), _add(offset, u, half), RELEASE, sz.line(0.7))
    else:
        # the halves slide across the member: two short lines perpendicular to it, one each side of the node
        for side in (-1, 1):
            centre = _add(at, u, side * sz.point(RELEASE_SPLIT))
            _line(out, _add(centre, n, -sz.point(1.9)), _add(centre, n, sz.point(1.9)), RELEASE, sz.line(0.7))


def _member(out, member, sz):
    """A bar, a cable or a spring, over whatever stretches its releases leave it.

    ⚠️ **A spring's zigzag follows the DRAWING's `point`, not the member's** (v0.99): the teeth's amplitude and the straight lead into them are a symbol's size, and a member states no `point` factor of its own (`figure_style.ENTRY_KEYS` -- one on a bar would be a field nobody could see the effect of). A spring drawn with a heavier `line` therefore has a heavier stroke and the same amplitude, which is what a thicker pen on the same symbol looks like; a whole spring drawn larger is the drawing's `point` slider.
    """
    kind = member["kind"]
    if kind == "spring":
        # a spring is drawn as what it is, over whatever stretch its releases leave it
        for a, b in member["runs"]:
            length = math.dist(a, b)
            u = _unit(a, b)
            lead = min(sz.point(2.5), 0.25 * length)
            p, q = _add(a, u, lead), _add(b, u, -lead)
            _line(out, a, p, SPRING, sz.line(0.6))
            _polyline(out, _zigzag(p, q, _perp(u), sz, teeth=5, amplitude=1.8), SPRING, sz.line(0.6))
            _line(out, q, b, SPRING, sz.line(0.6))
        return
    colour = CABLE if kind == "cable" else BAR
    width = sz.line(0.55) if kind == "cable" else sz.line(1.15)
    for a, b in member["runs"]:
        _line(out, a, b, colour, width, cap="round")


def _load(out, load, sz):
    colour = load["colour"]
    if load["kind"] == "point":
        for tail, tip in load["arrows"]:
            _arrow(out, tail, tip, colour, sz)
        if "leader" in load:
            _line(out, load["leader"][0], load["leader"][1], colour, sz.line(0.35),
                  dash=f"{_f(sz.line(1.2))} {_f(sz.line(1.0))}")
            _circle(out, load["leader"][1], sz.line(0.6), colour)
        return
    _line(out, load["cap_a"], load["cap_b"], colour, sz.line(0.7))
    for tail, tip in load["arrows"]:
        _arrow(out, tail, tip, colour, sz, scale=0.8)


def _dim_head(out, tip, inward, sz, length=None):
    """A dimension's arrowhead: a slim filled triangle, its tip on the line's end and its base back along `inward`. Slimmer than a force arrow's, which is what tells the two apart at a glance."""
    full = sz.line(2.2)
    head = full if length is None else min(full, 0.4 * length)
    base = _add(tip, inward, head)
    half = sz.line(0.55) * (head / full if full > 1e-12 else 1.0)
    p = _perp(inward)
    _polygon(out, [tip, _add(base, p, half), _add(base, p, -half)], DIMENSION)


def _witness_gap(reach, sz):
    """How much of the way from what is measured to the dimension line is left empty, in figure units.

    The witness line is drawn from the dimension line and covers DIM_WITNESS_SHARE of the way towards what it measures; the rest, the part next to the model, is not drawn at all. A line running the whole way is read as part of the structure, and the engineer asked for a quarter of it exactly. The only floor is DIM_WITNESS_MIN, for a dimension drawn so close to the model that a quarter of the reach would be nothing -- and never more than the reach itself.
    """
    drawn = max(DIM_WITNESS_SHARE * reach, min(sz.point(DIM_WITNESS_MIN), reach))
    return max(reach - drawn, 0.0)


def _dimension(out, dim, sz):
    """A length, written the way a dimension is: a witness line part of the way out from each end of what is measured, the dimension line between them with a head at either end, and the value over it. The witness line starts clear of the model and runs a little past the dimension line, so a dimension neither touches nor reaches the node it measures."""
    (a, b), (p0, p1) = dim["ends"], dim["line"]
    width = sz.line(0.35)
    for end, foot in ((a, p0), (b, p1)):
        reach = math.dist(end, foot)
        if reach < 1e-9:
            continue
        d = _unit(end, foot)
        _line(out, _add(end, d, _witness_gap(reach, sz)), _add(foot, d, sz.line(1.2)), DIMENSION, width, cap="butt")
    length = math.dist(p0, p1)
    _line(out, p0, p1, DIMENSION, width, cap="butt")
    if length > 1e-9:
        u = _unit(p0, p1)
        _dim_head(out, p0, u, sz, length)
        _dim_head(out, p1, (-u[0], -u[1]), sz, length)


def _angle_dimension(out, dim, sz):
    """An angle, as the arc its two members turn through: the arc sampled as a polyline -- SVG Tiny has no arc command, connection_svg's rule -- a head at either end of it, and a thin tie from the corner out to each end, so an arc drawn beyond the members is still read against the corner it turns about."""
    arc, centre = dim["arc"], dim["centre"]
    if len(arc) < 2:
        return
    for end in (arc[0], arc[-1]):
        _line(out, centre, end, DIMENSION, sz.line(0.22), cap="butt")
    _polyline(out, arc, DIMENSION, sz.line(0.35))
    for tip, neighbour in ((arc[0], arc[1]), (arc[-1], arc[-2])):
        if math.dist(tip, neighbour) > 1e-9:
            _dim_head(out, tip, _unit(tip, neighbour), sz)


def _label(out, frame, sz, colour=None):
    """A label, its lines stacked over a white rectangle, over whatever it lies on. A load whose value could not be read is written in the grey its arrow is drawn in, so the figure says as much as the warning does.

    The halo is the label's own box -- the one a click and a leader read (`hw`, `hh`) -- turned with its text. Until v0.77 it was each line drawn a second time with a wide white stroke, which over Woodcore's grid or a member left a «bubble» around every letter; the engineer asked for a rectangle."""
    colour = colour or (UNRESOLVED if frame.get("unresolved") else LABEL)
    size = sz.text(LABEL_TEXT)
    lines = frame["lines"]
    angle = frame["angle"] or None
    if any(line.strip() for line in lines):
        (x, y), hw, hh = frame["at"], frame["hw"], frame["hh"]
        turn = f' transform="translate({_f(x)},{_f(y)}) rotate({_f(frame["angle"])})"' if angle else ""
        ox, oy = (0.0, 0.0) if angle else (x, y)
        out.append(f'<rect x="{_f(ox - hw)}" y="{_f(oy - hh)}" width="{_f(2 * hw)}" height="{_f(2 * hh)}" fill="#ffffff"{turn}/>')
    top = -((len(lines) - 1) / 2.0) * LINE_SPACING * size
    for i, line in enumerate(lines):
        dy = top + i * LINE_SPACING * size
        if angle:
            a = math.radians(frame["angle"])
            at = (frame["at"][0] - dy * math.sin(a), frame["at"][1] + dy * math.cos(a))
        else:
            at = (frame["at"][0], frame["at"][1] + dy)
        _text(out, at, line, size, colour, bold=(i == 0), rotate=angle)


def _leader(out, frame, sz, colour=LABEL):
    """A thin line from a label the engineer moved clear of what it names back to its own place, so it still says what it belongs to. plan_svg's rule: drawn only once the label has left its symbol."""
    if not frame["moved"]:
        return
    home, at = frame["home"], frame["at"]
    gap = math.dist(home, at)
    if gap <= 2 * frame["hh"]:
        return
    x, y = _local(frame, home)
    hw, hh = frame["hw"], frame["hh"]
    s = min(hw / abs(x) if abs(x) > 1e-12 else math.inf, hh / abs(y) if abs(y) > 1e-12 else math.inf)
    a = math.radians(frame["angle"])
    u, v = x * s, y * s
    start = (at[0] + u * math.cos(a) - v * math.sin(a), at[1] + u * math.sin(a) + v * math.cos(a))
    _line(out, start, home, colour, sz.line(0.3))
    _circle(out, home, sz.line(0.55), colour)


# --- The figure -----------------------------------------------------------------


def _recorded(record, placed):
    """`record`, carrying the factors its entry states over the drawing's where it states any (v0.99) -- so the export says what each part of the figure was drawn with, which is the convention every other placed value here follows. Nothing is added where it states none, which is what leaves a record written before the factors existed unchanged."""
    if placed.get("style"):
        record["style"] = placed["style"]
    return record


def meta(drawing):
    """The placed geometry the report's record carries: the frame, the size unit, and where everything was drawn -- enough for a halo and for a caption, and nothing more."""
    view = drawing["view"]
    return {
        "view": {key: round(view[key], 4) for key in ("x", "y", "w", "h")},
        "unit": round(drawing["unit"], 6),
        "points": [
            _recorded({"id": p["id"], "at": [round(p["at"][0], 4), round(p["at"][1], 4)], "label": p["label"]}, p)
            for p in drawing["points"]
        ],
        "members": [
            _recorded({
                "id": m["id"],
                "kind": m["kind"],
                "at": [[round(m["a"][0], 4), round(m["a"][1], 4)], [round(m["b"][0], 4), round(m["b"][1], 4)]],
                "label": m["label"],
                "length_m": round(m["length_m"], 4),
            }, m)
            for m in drawing["members"]
        ],
        "supports": [
            # `at` is where the symbol was drawn, which is the node except where a bar runs over the support and its pin is set back: what reads this is the report's halo, and a halo belongs on the symbol
            _recorded({"id": s["id"], "point": s["point"], "type": s["type"],
                       "at": [round(s["origin"][0], 4), round(s["origin"][1], 4)]}, s)
            for s in drawing["supports"]
        ],
        "releases": [
            _recorded({"id": r["id"], "member": r["member"], "end": r["end"], "dof": r["dof"],
                       "at": [round(r["at"][0], 4), round(r["at"][1], 4)]}, r)
            for r in drawing["releases"]
        ],
        "dimensions": [
            {
                key: value
                for key, value in (
                    ("id", d["id"]),
                    ("kind", d["kind"]),
                    ("show", d["show"]),
                    ("text", d["text"]),
                    ("value", None if d["value"] is None else round(d["value"], 6)),
                    ("unit", d["unit"]),
                    ("at", [round(d["at"][0], 4), round(d["at"][1], 4)]),
                    ("line", None if d["kind"] == "angle" else [
                        [round(d["line"][0][0], 4), round(d["line"][0][1], 4)],
                        [round(d["line"][1][0], 4), round(d["line"][1][1], 4)],
                    ]),
                    ("centre", None if d["kind"] != "angle" else
                     [round(d["centre"][0], 4), round(d["centre"][1], 4)]),
                    ("radius", None if d["kind"] != "angle" else round(d["radius"], 4)),
                    ("style", d["style"]),
                )
                if value is not None
            }
            for d in drawing["dimensions"]
        ],
        "loads": [
            {
                key: value
                for key, value in (
                    ("id", load["id"]),
                    ("kind", load["kind"]),
                    ("label", load["label"]),
                    ("show", load["show"]),
                    ("color", load["colour_name"]),
                    ("text", " / ".join(load["lines"])),
                    ("value", None if load["value"] is None else round(load["value"], 6)),
                    ("unit", load["unit"]),
                    ("base_value", None if load["base_value"] is None else round(load["base_value"], 6)),
                    ("base_unit", load["base_unit"]),
                    ("width", load.get("width")),
                    ("width_label", load.get("width_label")),
                    ("from", load["from"]),
                    ("factor", None if load["factor"] == 1.0 else round(load["factor"], 6)),
                    ("offset", None if load["offset"] == 0.0 else round(load["offset"], 6)),
                    ("description", load["description"] or None),
                    ("at", [round(load["at"][0], 4), round(load["at"][1], 4)]),
                    ("style", load["style"]),
                )
                if value is not None
            }
            for load in drawing["loads"]
        ],
    }


# The white a text placed with the Text tool is drawn over first, as a share of its size: wide enough to part it from a member it lies across, narrow enough not to hide one.
TEXT_HALO = 0.3

def render(drawing, highlight=None, background=True, nodes=False):
    """The figure, as SVG text. `highlight` is what Woodcore rings while it is being edited; the report inserts its own at HIGHLIGHT_MARK, which is why the mark is left in the file. `background: False` leaves the white ground out, so Woodcore's grid shows through the drawing.

    `nodes: True` marks every point the drawing has no symbol of its own at with a dot. Those dots say where one may click, so they belong to Woodcore and to nothing else: a point carrying neither a support nor a release is not an articulation, and in the report a dot there would claim it is one. What the report does draw at a node, it draws as the thing itself -- a hinge's white circle, a release's mark, a wall's hatching.
    """
    sz = drawing["sz"]
    view = drawing["view"]
    scale = PAPER_MM / FIGURE_SPAN
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
        f'viewBox="{_f(view["x"])} {_f(view["y"])} {_f(view["w"])} {_f(view["h"])}" '
        f'width="{_f(view["w"] * scale)}mm" height="{_f(view["h"] * scale)}mm">'
    ]
    if background:
        out.append(
            f'<rect x="{_f(view["x"])}" y="{_f(view["y"])}" width="{_f(view["w"])}" '
            f'height="{_f(view["h"])}" fill="#ffffff"/>'
        )
    out.append(HIGHLIGHT_MARK)
    if highlight:
        out.append(halo(drawing, highlight))

    # every symbol at its own entry's sizes (`_own`): the drawing's three times whatever factor that entry states over them
    for member in drawing["members"]:
        _member(out, member, _own(member, sz))
    for support in drawing["supports"]:
        _support(out, support, _own(support, sz))
    for release in drawing["releases"]:
        _release(out, release, _own(release, sz))

    out.append(DIMS_OPEN)
    for dim in drawing["dimensions"]:
        if dim["kind"] == "angle":
            _angle_dimension(out, dim, _own(dim, sz))
        else:
            _dimension(out, dim, _own(dim, sz))
    out.append(DIMS_CLOSE)

    out.append(LOADS_OPEN)
    for load in drawing["loads"]:
        _load(out, load, _own(load, sz))
    out.append(LOADS_CLOSE)

    if nodes:
        for point in drawing["points"]:
            if point["id"] not in drawing.get("hidden_nodes", ()):
                _circle(out, point["at"], sz.point(0.9), NODE)

    # The structure's labels first; the loads' after them, inside a second marked region, so that `loads: false` takes a load's name away with its arrow. They are the last thing drawn either way: a label reads over whatever it lies on, never under it.
    structure = [f for f in drawing["labels"] if f["collection"] not in ("point_loads", "line_loads", "dimensions", figure_text.COLLECTION)]
    texts = [f for f in drawing["labels"] if f["collection"] == figure_text.COLLECTION]
    dim_labels = [f for f in drawing["labels"] if f["collection"] == "dimensions"]
    load_labels = [f for f in drawing["labels"] if f["collection"] in ("point_loads", "line_loads")]
    for frame in structure:
        _leader(out, frame, _own(frame, sz))
    for frame in structure:
        _label(out, frame, _own(frame, sz))
    # the texts placed with the Text tool (issue #43), over the structure and under the dimensions and the loads: figure_text sets them, with no box and no bold line -- a note on the drawing, not the name of a part of it
    for frame in texts:
        size = _own(frame, sz).text(LABEL_TEXT)
        figure_text.draw(out, frame["at"], frame["lines"], size, LABEL, halo=TEXT_HALO * size)

    # a dimension's value goes with its own lines, inside the region they are cut at, and over them: the halo it carries is what breaks the dimension line behind it
    out.append(DIMS_OPEN)
    for frame in dim_labels:
        _leader(out, frame, _own(frame, sz), colour=DIMENSION)
    for frame in dim_labels:
        _label(out, frame, _own(frame, sz), colour=DIMENSION)
    out.append(DIMS_CLOSE)

    out.append(LOADS_OPEN)
    for frame in load_labels:
        _leader(out, frame, _own(frame, sz))
    for frame in load_labels:
        _label(out, frame, _own(frame, sz))
    if drawing["notes"]:
        # every note is about a load -- what was enlarged, what an influence width is, what could not be read -- so the notes go with them
        size = drawing["note_size"]
        x = view["x"] + sz.text(2.4)
        y = view["y"] + view["h"] - (len(drawing["notes"]) - 0.4) * NOTE_SPACING * size
        for i, note in enumerate(drawing["notes"]):
            _text(out, (x, y + i * NOTE_SPACING * size), note, size, NOTE_COLOUR, anchor="start")
    out.append(LOADS_CLOSE)

    out.append("</svg>")
    return "\n".join(out) + "\n"


def halo(drawing, ids):
    """The halo under the parts an id names -- what show-static-model inserts at HIGHLIGHT_MARK, drawn here too so Woodcore rings a selection the same way.

    Each halo grows with the part it marks (v0.99): a ring thinner than the symbol under it marks nothing. A halo's own nominal width is in the drawing's `point` unit wherever it was, and what carries it is the factor that widened what it marks -- `line` for a stroke, an arrow or a dimension line (`_grown`), `point` for a symbol on a node, which a support and a release may state themselves. A point takes the drawing's, drawing nothing of its own to mark.
    """
    wanted = {ids} if isinstance(ids, str) else set(ids)
    sz = drawing["sz"]
    out = []
    for member in drawing["members"]:
        if member["id"] in wanted:
            _line(out, member["a"], member["b"], HIGHLIGHT_COLOUR, _grown(member, sz, 3.2, "line"), cap="round")
    for point in drawing["points"]:
        if point["id"] in wanted:
            _circle(out, point["at"], sz.point(2.6), HIGHLIGHT_COLOUR)
    for support in drawing["supports"]:
        if support["id"] in wanted:
            # from where the symbol is actually drawn, so the halo follows a pin set back from a bar running over it
            own = _own(support, sz)
            _circle(out, _add(support["origin"], support["g"], own.point(3.0)), own.point(5.5), HIGHLIGHT_COLOUR)
    for release in drawing["releases"]:
        if release["id"] in wanted:
            _circle(out, release["at"], _release_extent(release, _own(release, sz)), HIGHLIGHT_COLOUR)
    for dim in drawing["dimensions"]:
        if dim["id"] in wanted:
            width = _grown(dim, sz, 1.6, "line")
            if dim["kind"] == "angle":
                _polyline(out, dim["arc"], HIGHLIGHT_COLOUR, width)
            else:
                _line(out, dim["line"][0], dim["line"][1], HIGHLIGHT_COLOUR, width)
    for load in drawing["loads"]:
        if load["id"] in wanted:
            for a, b in load["arrows"]:
                _line(out, a, b, HIGHLIGHT_COLOUR, _grown(load, sz, 1.8, "line"), cap="round")
    return "\n".join(out)


# --- Tool icons, for Woodcore ------------------------------------------------

# One tiny model per tool, drawn by the real code, so a button cannot come to show something the figure does not. The keys are the canvas's tool names, plus the release variants the tab's combo stands for.
SWATCHES = {
    "point": ("points", None),
    "bar": ("members", "bar"),
    "cable": ("members", "cable"),
    "spring": ("members", "spring"),
    "support-fixed": ("supports", "fixed"),
    "support-pinned": ("supports", "pinned"),
    "support-roller": ("supports", "roller"),
    "release": ("releases", "moment"),
    "release-moment": ("releases", "moment"),
    "release-shear": ("releases", "shear"),
    "release-normal": ("releases", "normal"),
    "release-spring-moment": ("releases", "spring-moment"),
    "point-load": ("point_loads", None),
    "line-load": ("line_loads", "uniform"),
    "line-load-linear": ("line_loads", "linear"),
    "dimension-horizontal": ("dimensions", "horizontal"),
    "dimension-vertical": ("dimensions", "vertical"),
    "dimension-parallel": ("dimensions", "parallel"),
    "dimension-angle": ("dimensions", "angle"),
}

# The sliders a tool icon is drawn with, by what it shows: heavier than a figure's, so the symbol still reads at the height of a toolbar button -- and heavier again for a release, whose whole symbol is a mark on a node and would otherwise be a speck beside its member.
SWATCH_STYLE = {"line": 1.7, "point": 1.5, "text": 1.0}
SWATCH_RELEASE_STYLE = {"line": 2.2, "point": 3.4, "text": 1.0}
# A load's and a dimension's symbol carries no name under it since the bar was made compact, so it is drawn heavier still: at 1.7 a line load's arrows were a pink haze at the size of a button, and it has to be read on its own now.
SWATCH_BARE_STYLE = {"line": 3.0, "point": 2.0, "text": 1.0}


def _swatch_source(tool):
    """A one-entity model showing what a tool draws."""
    collection, variant = SWATCHES[tool]
    s = model.new_source("swatch")
    s["style"] = dict(SWATCH_RELEASE_STYLE if collection == "releases"
                      else SWATCH_BARE_STYLE if collection in ("point_loads", "line_loads", "dimensions")
                      else SWATCH_STYLE)
    s["points"] = [{"id": "P1", "x": 0.0, "z": 0.0}, {"id": "P2", "x": 4.0, "z": 0.0}]
    if collection == "points":
        s["points"] = [{"id": "P1", "x": 2.0, "z": 0.0}]
        return s
    s["members"] = [{"id": "B1", "kind": variant if collection == "members" else "bar", "p1": "P1", "p2": "P2"}]
    if collection == "supports":
        s["points"] = [{"id": "P1", "x": 2.0, "z": 0.0}]
        s["members"] = []
        s["supports"] = [{"id": "A1", "point": "P1", "type": variant}]
    elif collection == "releases":
        dof = "moment" if variant == "spring-moment" else variant
        release = {"id": "G1", "member": "B1", "end": "start", "dof": dof}
        if variant == "spring-moment":
            release["stiffness"] = {"value": 1.0, "unit": model.SPRING_UNITS[dof]}
        s["releases"] = [release]
    elif collection == "dimensions":
        # whole numbers on purpose: the value is printed and the frame is sized around it, so a 4.472 would shrink the very symbol the button is there to show
        if variant == "vertical":
            s["points"] = [{"id": "P1", "x": 0.0, "z": 0.0}, {"id": "P2", "x": 0.0, "z": 3.0}]
        elif variant == "parallel":
            s["points"] = [{"id": "P1", "x": 0.0, "z": 0.0}, {"id": "P2", "x": 4.0, "z": 3.0}]
        s["members"] = [{"id": "B1", "kind": "bar", "p1": "P1", "p2": "P2"}]
        dim = {"id": "D1", "kind": variant, "from": {"point": "P1"}, "to": {"point": "P2"}, "offset": 1.2}
        if variant == "angle":
            s["points"].append({"id": "P3", "x": 0.0, "z": 4.0})
            s["members"].append({"id": "B2", "kind": "bar", "p1": "P1", "p2": "P3"})
            dim = {"id": "D1", "kind": "angle", "from": {"member": "B1"}, "to": {"member": "B2"}, "offset": 1.5}
        s["dimensions"] = [dim]
    elif collection == "point_loads":
        s["members"] = []
        s["points"] = [{"id": "P1", "x": 2.0, "z": 0.0}]
        s["point_loads"] = [{
            "id": "F1", "point": "P1", "direction": "vertical", "show": "none",
            "magnitude": {"value": 1.0, "unit": "kN"},
        }]
    elif collection == "line_loads":
        load = {
            "id": "q1", "member": "B1", "shape": variant, "direction": "vertical", "show": "none",
            "magnitude": {"value": 1.0, "unit": "kN/m"},
        }
        if variant == "linear":
            load["magnitude"] = {"value": 0.0, "unit": "kN/m"}
            load["magnitude_end"] = {"value": 1.0, "unit": "kN/m"}
        s["line_loads"] = [load]
    return s


def swatch(tool):
    """A tool's icon, as a standalone SVG document with no ground under it, carrying its own viewBox so that whoever renders it can keep its proportions -- a stretched symbol is a symbol one cannot read.

    A release's icon is cropped to the node it sits on: its whole symbol is a mark on that node, and shown beside a whole member it would be a speck. The member still runs out of the frame, which is what says the mark sits on one.
    """
    drawing = layout(_swatch_source(tool))
    view = drawing["view"]
    if drawing["releases"]:
        at = drawing["releases"][0]["at"]
        half = drawing["sz"].point(6.0)
        view = {"x": at[0] - half, "y": at[1] - half, "w": 2 * half, "h": 2 * half}
    # with its nodes, Woodcore's own: these are Woodcore's buttons, and the Point tool has nothing but a node to show
    body = render(drawing, background=False, nodes=True).split("\n")[1:-2]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
        f'viewBox="{_f(view["x"])} {_f(view["y"])} {_f(view["w"])} {_f(view["h"])}" '
        f'width="{_f(view["w"])}" height="{_f(view["h"])}">' + "".join(body) + "</svg>"
    )
