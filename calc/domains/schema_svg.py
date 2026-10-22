"""The figure of a detail schema, as SVG text: the pieces, the fastener markers, the construction aids that are shown, and the dimensions (docs/domain/detail-schemas.md §3.3decies).

One drawing serves both places it is seen: Woodcore's window shows it live while a schema is edited, and export writes it to data/schemas/<id>-<lang>.svg (Details/Exports/Figures/ in a project laid out by folders, issue #64), which show-schema sets in the report. It is built as plain text here, with no Qt, so export_all.py draws it too, without a window.

**A schema is a detail at its real size, in millimetres -- not a scale-free sketch normalised to 1000 figure units the way a static model's is.** Its coordinates are used as they stand, scaled to PAPER_MM only when the SVG's own width/height are set, exactly as connector_svg.section() already does; that is what will let a *Connecteurs* or *Moments polaires* calculation place its own force arrows over a copy of this drawing with no conversion (module docstring of schema.py).

Kept to what both renderers read alike, like every other figure here: SVG Tiny 1.2, no <marker>, no CSS, no arc command (an arc is a sampled polyline), `font-family="Arial"` bare.

**A text is set over a white rectangle, its own box, and never drawn twice with a wide white stroke** (v0.99): the stroke method left a «cloud» round every letter -- the finding statics_svg.py already records, made here for the same reason, on every text the schema writes (a piece's label, a marker's id, a point's name, a dimension's value). The rectangle is the label's own box, the one a click and a leader read (`hw`, `hh`), turned with its text, and it is **translucent** (`LABEL_GROUND_OPACITY`): a schema's label sits *on* the piece it names, so an opaque ground would take a bite out of that piece's fill.

**A shown construction line is cut at the boxes of the labels it crosses** (v0.99, `cut_at_labels`). The aids are drawn over everything, the labels included -- v0.77's rule, which stands -- so a line ran straight through a piece's number and no ground behind the text could mend it: it is the line that gives way, which is what a drawing office does. The line still runs to the edges of the frame; only what falls inside a label's box is left out.

**The three factors** every figure here is set with -- `line` on the strokes, `point` on the symbols placed on a point, `text` on the texts -- are `figure_style`'s, shared with the plans and the static models, and a **single entry may state a factor of its own** over the drawing's (v0.99): `Sizes`, `sizes_of`, `entry_sizes`. Everything an entry draws is drawn with that entry's own sizes, so the window's canvas and the exported figure honour them alike, being the one SVG.

Ported from connection_svg.py (the members' bands, their fill and stroke, a piece's label set inside its own band) and from statics_svg.py (a label the engineer may drag clear of its symbol and a thin leader back to it when they have, and a dimension's witness lines, arrowheads and arc) rather than imported from either: both are bound to their own module's shapes, one to a connection's node-relative members and the other to a figure normalised away from real units, neither of which this module works in. schema.py's own docstring says the same of the geometry this one draws.
"""

import math
from xml.sax.saxutils import escape

from domains import svg_draw  # the one writer of an SVG number and text (D6)
from domains import dimension  # one unit vector and one label box (ARCH-004)
from domains import figure_style
from domains import figure_text  # a text placed with the Text tool (issue #43)
from domains import schema as model
from i18n import strings

# The pieces' fill, in the same rotation connection_svg.py uses, so a detail drawn in both tabs reads the same way.
ELEMENT_FILLS = svg_draw.colours("wood")
ELEMENT_OPACITY = 0.75
ELEMENT_STROKE = svg_draw.colour("brown")
CONNECTOR_FILL = svg_draw.colour("ink")
CONNECTOR_LABEL = svg_draw.colour("ink")
TEXT_COLOR = svg_draw.colour("ink")
MUTED = svg_draw.colour("muted")
AID_COLOUR = svg_draw.colour("aid")
AID_SHOWN_COLOUR = svg_draw.colour("ink-soft")
# A named point (an aid of kind `point`) is a green cross, drawn in front of everything, the construction lines included, so it is always seen (v0.77, the engineer's rule).
POINT_COLOUR = svg_draw.colour("green")
DIMENSION = svg_draw.colour("ink")
LABEL_COLOUR = svg_draw.colour("ink")
# The white a text placed with the Text tool is drawn over first, as a share of its size -- statics_svg.TEXT_HALO's.
TEXT_HALO = 0.3
HIGHLIGHT = svg_draw.colour("orange")

FONT = svg_draw.FONT

HIGHLIGHT_MARK = "<!-- highlight -->"
# Where the report puts the halo of a **connector marker or a named point**: over the pieces, the dimensions and their labels, and under the markers and the aids themselves, so the ring shows round what it marks. At HIGHLIGHT_MARK, under the pieces, a point's halo was hidden beneath the pieces' fill -- «un point doit être affiché au-dessus de tout». HIGHLIGHT_MARK stays where it was, for a piece's own halo and a dimension's, which a piece's fill is drawn over on purpose. Emitted by `body`, outside AIDS_OPEN/AIDS_CLOSE, so `aids: false` leaves it in place.
HIGHLIGHT_POINTS_MARK = "<!-- highlight-points -->"
AIDS_OPEN = "<!-- aids -->"
AIDS_CLOSE = "<!-- /aids -->"

# The drawing's size on paper, at most, whichever side is longer -- connector_svg.py's own PAPER_MM.
PAPER_MM = 160.0

DIM_WITNESS_SHARE = 0.25
DIM_WITNESS_MIN_FONT = 0.4

LABEL_TEXT = 1.0
LINE_SPACING = 1.25

# What a text is set over: its own box, filled white and **translucent**. A schema's label sits ON the piece it names -- the middle of the longest stretch no other piece covers (v0.75) -- so an opaque ground would take a bite out of that piece's fill and out of the dimension lines the value stands on. At 0.85 the piece is still read through the box and the text still reads over the piece; set it to 1.0 for an opaque white, which is the one number to change.
GROUND = svg_draw.colour("ground")
LABEL_GROUND = GROUND
LABEL_GROUND_OPACITY = 0.85

# The three quantities a schema is drawn with, as shares of the drawing's own extent: the font (the unit the rest is expressed in), the stroke, and the radius a fastener marker is drawn at where it states no diameter -- with a floor under the radius so a marker is never thinner than the lines around it.
FONT_DIVISOR = 40.0
STROKE_DIVISOR = 480.0
RADIUS_DIVISOR = 130.0
RADIUS_STROKE_FLOOR = 3.5

# A connector marker that states its diameter is drawn at it -- a Ø 8 dowel is a dot 8 mm across on a detail at its real size -- but never smaller than this share of the drawing's own marker radius, below which a nail would be a speck (v0.75).
MARKER_FLOOR_SHARE = 0.5

# The text of the figure: Arial's advances, the subscripts, the typed `*`, the measure and the setting -- calc/domains/svg_text.py, the one text engine of every figure since issue #43 (D-19). Until then this module carried a table it called a copy of statics_svg's and was not («m» 0.7222 em here, 0.833 there), and placed a subscript its own way: the engineer chose one engine, the labels of a schema moving slightly with it.
from domains.svg_text import (  # noqa: E402  -- every name this module had is still importable from it
    ARIAL_DEFAULT, ARIAL_WIDTHS, SUB_DROP, SUB_SCALE, SUBSCRIPT, TIMES, TYPED_TIMES, text_runs, text_width,
)
from domains import svg_text  # noqa: E402


class Sizes:
    """What one thing of a schema is drawn with: its font, its stroke and its marker radius, each scaled by the factors that apply to it (`figure_style`).

    Unlike the plans' and the static models' own `Sizes`, which hold one unit and three factors, a schema's three quantities are three different shares of the drawing's extent -- 1/40 of it for the font, 1/480 for the stroke, 1/130 for a marker -- so they are computed here and the factors applied to them. What the three factors reach:

    - **`text`** the font, and so every box a text is set in and every standoff measured from one;
    - **`line`** the stroke, and `on_line`, which is a length belonging to a line's own symbol: a dimension's head, how far a witness runs past its line, a leader's own width;
    - **`point`** the marker radius, and `on_point`, a symbol placed on a point: a centre's cross, a named point's.

    ⚠️ The radius keeps the floor it has always had, `RADIUS_STROKE_FLOOR` times the **scaled** stroke: what the floor is for is that a marker is never lost among the lines around it, and a drawing whose strokes were set three times as heavy would lose it again if the floor were taken on the unscaled stroke.

    `on_line`, `on_point` and `on_text` are all in the drawing's own unit -- the font before the `text` factor -- so a quantity written `0.45 * font` before v0.99 is `on_point(0.45)` or `on_line(0.45)` now and comes out at the very same number while every factor is 1: which is what makes a drawing that states no factor byte for byte the drawing it was.
    """

    def __init__(self, size, factors=None):
        self.size = float(size)
        given = factors or {}
        self.factors = {key: float(given.get(key, figure_style.DEFAULT)) for key in figure_style.KEYS}
        self.unit = self.size / FONT_DIVISOR
        self.font = self.unit * self.factors["text"]
        self.stroke = (self.size / STROKE_DIVISOR) * self.factors["line"]
        self.radius = max((self.size / RADIUS_DIVISOR) * self.factors["point"],
                          RADIUS_STROKE_FLOOR * self.stroke)

    def on_line(self, x):
        return x * self.unit * self.factors["line"]

    def on_point(self, x):
        return x * self.unit * self.factors["point"]

    def on_text(self, x):
        return x * self.unit * self.factors["text"]

    def scaled(self, factors):
        """This, with `factors` multiplied into the three -- what an entry that states a factor of its own is drawn with. `self` itself where it states none, so nothing is rebuilt for the usual case."""
        if not factors:
            return self
        return Sizes(self.size, {key: self.factors[key] * factors.get(key, figure_style.DEFAULT)
                                 for key in figure_style.KEYS})


def sizes_of(source, size):
    """The sizes a schema of this extent is drawn at, with the drawing's own three factors."""
    return Sizes(size, figure_style.drawing_factors(source))


def entry_sizes(sz, entry):
    """`sz` scaled by the factors `entry` states over the drawing's own -- `sz` itself where it states none."""
    return sz.scaled(figure_style.stated(entry))


_f = svg_draw.number_at(2)   # a coordinate at 2 decimals (svg_draw.py, D6)


def _pt(point):
    return f"{_f(point[0])},{_f(point[1])}"


def _add(p, u, t=1.0):
    return (p[0] + t * u[0], p[1] + t * u[1])


_unit = dimension.unit   # (ARCH-004: one copy, D-15)


def _perp(u):
    return (-u[1], u[0])


def _text(out, point, content, size, colour, anchor="middle", bold=False, rotate=None, halo=None, raw=False):
    """A (possibly subscripted) text -- svg_text.draw, the one text engine of every figure (D-19). `halo` is (colour, width), drawn first so the text reads over what is behind it; `raw` sets it as it is written, no subscript cut."""
    svg_text.draw(out, point, content, size, colour, anchor, bold, rotate,
                  halo[1] if halo else None, halo[0] if halo else LABEL_GROUND, raw)


def _line(out, a, b, colour, width, dash=None, cap="round"):
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    out.append(
        f'<line x1="{_f(a[0])}" y1="{_f(a[1])}" x2="{_f(b[0])}" y2="{_f(b[1])}" stroke="{colour}" '
        f'stroke-width="{_f(width)}" stroke-linecap="{cap}"{dash_attr}/>'
    )


def _polyline(out, points, colour, width):
    out.append(f'<polyline points="{" ".join(_pt(p) for p in points)}" fill="none" stroke="{colour}" stroke-width="{_f(width)}"/>')


def _polygon(out, points, fill, opacity=1.0, stroke=None, width=0.0):
    stroke_attr = f' stroke="{stroke}" stroke-width="{_f(width)}"' if stroke else ""
    out.append(f'<polygon points="{" ".join(_pt(p) for p in points)}" fill="{fill}" fill-opacity="{_f(opacity)}"{stroke_attr}/>')


def _circle(out, centre, r, fill, stroke=None, width=0.0):
    stroke_attr = f' stroke="{stroke}" stroke-width="{_f(width)}"' if stroke else ""
    out.append(f'<circle cx="{_f(centre[0])}" cy="{_f(centre[1])}" r="{_f(r)}" fill="{fill}"{stroke_attr}/>')


# --- Labels (statics_svg.py's own mechanics, ported: a label the engineer dragged clear of its symbol, and a thin leader back to it) ---


def _label_box(lines, font):
    width = max((text_width(line, font) for line in lines), default=0.0)
    height = len(lines) * LINE_SPACING * font
    return (max(width, font) / 2.0 + 0.4 * font, max(height, font) / 2.0 + 0.3 * font)


def label_offset(entry):
    offset = entry.get("label_offset")
    return (0.0, 0.0) if not offset else (float(offset[0]), float(offset[1]))


def _frame(lines, home, font, angle=0.0):
    """A label's box at its own place, `hw`/`hh` its half-sides -- statics_svg.py's own shape (its own `_frame`), so a schema's labels are dragged and hit-tested exactly as a static model's are. The caller moves `at` off `home` by the entry's own label_offset once this returns."""
    hw, hh = _label_box(lines, font)
    return {"at": home, "home": home, "moved": False, "angle": angle, "hw": hw, "hh": hh, "lines": list(lines)}


def _local(frame, point):
    a = math.radians(frame["angle"])
    dx, dy = point[0] - frame["at"][0], point[1] - frame["at"][1]
    return (dx * math.cos(a) + dy * math.sin(a), -dx * math.sin(a) + dy * math.cos(a))


def on_label(frame, point, margin=0.0):
    x, y = _local(frame, point)
    return abs(x) <= frame["hw"] + margin and abs(y) <= frame["hh"] + margin


def _draw_label(out, frame, sz, scale=1.0, colour=LABEL_COLOUR):
    """A label's lines, over a white rectangle: **its own box** (`hw`, `hh`), turned with its text, at `LABEL_GROUND_OPACITY`.

    Until v0.99 the ground was each line drawn a second time with a wide white stroke, which puts a cloud round every letter rather than a ground under the word -- the very finding statics_svg.py records for its own labels (v0.77), made here again by the engineer on a schema. The box is drawn as a polygon of the corners `label_corners` already computes, not as a `<rect>` with a `transform`: a polygon needs no transform to be read, which is one thing fewer for either renderer to agree about.

    `scale` is the share of the drawing's font this label is set at -- 1 for a piece, 0.72 for a marker or a point, 0.85 for a dimension's value -- so the label's own font and the widths its leader is drawn at both follow the entry's own factors.
    """
    font = scale * sz.font
    lines = frame["lines"]
    if any(line.strip() for line in lines):
        _polygon(out, label_corners(frame), LABEL_GROUND, LABEL_GROUND_OPACITY)
    top = -((len(lines) - 1) / 2.0) * LINE_SPACING * font
    a = frame["angle"] or None
    for i, line in enumerate(lines):
        dy = top + i * LINE_SPACING * font
        if a:
            rad = math.radians(frame["angle"])
            at = (frame["at"][0] - dy * math.sin(rad), frame["at"][1] + dy * math.cos(rad))
        else:
            at = (frame["at"][0], frame["at"][1] + dy)
        _text(out, at, line, font, colour, bold=(i == 0), rotate=a)


def _on_own_piece(frame, kind, points, width):
    """Whether a label's centre lies on the piece it names: within the band of a linear element -- or within the label's own half-height of its axis, where the band is thinner than the text -- or inside an area element's outline."""
    at = frame["at"]
    if kind == "linear":
        if len(points) < 2:
            return False
        reach = max((width or 0.0) / 2.0, frame["hh"])
        return min(model._point_segment(at, a, b)[0] for a, b in zip(points, points[1:])) <= reach
    return len(points) >= 3 and model._inside(at, points)


def _leader(out, frame, sz, scale=1.0, colour=LABEL_COLOUR, dot=True):
    """A thin line from what a label names back to the label dragged clear of it. It starts at the frame's `anchor` -- a marker's centre, a dimension line's middle, a point's place -- or, for a piece, at the label's own place on the piece. `dot` is false where the anchor is already a mark of its own (a marker, a point).

    `scale` is the label's share of the drawing's font, as in `_draw_label`: the gap it leaves is a text's and the width it is drawn at is a line's, so the two follow the entry's `text` and `line` factors respectively.
    """
    if not frame.get("leader", frame["moved"]):
        return
    home, at = frame.get("anchor", frame["home"]), frame["at"]
    if math.dist(home, at) < 1e-6:
        return
    u = _unit(home, at)
    start = _add(home, u, min(0.35 * scale * sz.font, 0.4 * math.dist(home, at)))
    end = _add(at, u, -min(frame["hw"], 0.4 * math.dist(home, at)))
    if math.dist(start, end) > 1e-6:
        _line(out, start, end, colour, sz.on_line(0.12 * scale), cap="butt")
        if dot:
            _circle(out, home, sz.on_line(0.14 * scale), colour)


def _left_home(frame):
    """Whether a label dragged by its `label_offset` has left its own place -- by more than the height of its box, plan_svg's rule (a number nudged beside its symbol needs no line to say whose it is)."""
    return frame["moved"] and math.dist(frame["at"], frame["home"]) > 2.0 * frame["hh"]


def label_frames(source, drawing=None):
    """(key, frame) for every label a schema draws -- an element's, a connector marker's, an aid's, a dimension's -- what hit_label reads, and what a moved label is dragged as (schema.py's v0.42-style rule). `drawing` is layout()'s result where the caller already keeps one, Woodcore's canvas doing exactly that on every movement of the mouse."""
    drawing = drawing if drawing is not None else layout(source)
    return [((collection, eid), frame) for collection, eid, frame in drawing["label_frames"]]


# --- Layout ------------------------------------------------------------------------


def _element_polygons(element, width):
    """The rectangles of a linear element's band, one per segment -- a simpler shape than a true mitred offset polygon, and the one this module draws: a schema's pieces are close to straight, and a small gap at a bend costs nothing a checker reads as an error."""
    polys = []
    half = width / 2.0
    for a, b in model.segments_of(element):
        u = _unit(a, b)
        n = _perp(u)
        polys.append([_add(a, n, half), _add(b, n, half), _add(b, n, -half), _add(a, n, -half)])
    return polys


LABEL_SAMPLES = 96


def _free_middle(element, others):
    """Where a linear element's label goes: ((x, z), the unit direction there) -- the middle of the longest stretch of its axis that no other piece covers, or the middle of its whole length where every stretch is covered (v0.75).

    Sampled along the length rather than solved exactly: a schema's pieces are a handful of bands, and a label needs a place to sit, not a boundary to the hundredth of a millimetre. Of two stretches as long as each other, the one nearer the element's own middle is taken, then the later one -- a beam through a column carries its label on its far half, where v0.74 put it.
    """
    points = [(float(p[0]), float(p[1])) for p in element.get("points", [])]
    if len(points) < 2 or not others:
        return model.element_middle(element)
    lengths = [math.dist(points[i - 1], points[i]) for i in range(1, len(points))]
    total = sum(lengths)
    if total <= model.SAME_POINT:
        return model.element_middle(element)

    def at(s):
        for i, length in enumerate(lengths):
            if s <= length or i == len(lengths) - 1:
                a, b = points[i], points[i + 1]
                t = 0.0 if length <= 1e-12 else min(max(s / length, 0.0), 1.0)
                u = None if length <= model.SAME_POINT else ((b[0] - a[0]) / length, (b[1] - a[1]) / length)
                return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])), u
            s -= length
        return points[-1], None

    samples = [total * (k + 0.5) / LABEL_SAMPLES for k in range(LABEL_SAMPLES)]
    free = [not any(model._inside(at(s)[0], poly) for poly in others if len(poly) >= 3) for s in samples]
    runs, start = [], None
    for k, ok in enumerate(free + [False]):
        if ok and start is None:
            start = k
        elif not ok and start is not None:
            runs.append((start, k - 1))
            start = None
    if not runs:
        return model.element_middle(element)
    middle = (LABEL_SAMPLES - 1) / 2.0
    first, last = max(runs, key=lambda r: (r[1] - r[0], -abs((r[0] + r[1]) / 2.0 - middle), r[0]))
    if first == 0 and last == LABEL_SAMPLES - 1:
        return model.element_middle(element)
    return at((samples[first] + samples[last]) / 2.0)


def _connector_label_text(marker):
    return marker["id"]


def layout(source, lang=strings.SOURCE_LANGUAGE, positions=None, editing=False, use_crop=True, values=None):
    """Where everything goes, for render() and for meta() -- a draft is laid out as far as it goes: a schema with nothing drawn yet still returns a (small) frame.

    `positions` are the position records ({id: record}) an element's section and label are resolved against (v0.75): a linear element's band is the side of its section its view shows, and its label reads «T001 C24 100/200». Without them an element keeps what it states and is named by its position number alone.

    `values` are the export's, which a text's variables print (issue #43, figure_text); without them a text prints its variables' last values.

    `editing` is Woodcore's canvas and nothing else. It keeps the construction aids the report leaves out, drawn light, so a line drawn to help place something is SEEN while it helps (until v0.75 an aid line with `shown` false was invisible in the very tab it was drawn in, but for its selection outline); and it ignores the `crop`, the canvas showing the whole detail and marking the crop over it. The export never passes it.
    """
    elements = source.get("elements", [])
    connectors = source.get("connectors", [])
    all_aids = source.get("aids", [])
    dimensions = source.get("dimensions", [])

    xs, zs = [], []
    for element in elements:
        for p in element.get("points", []):
            xs.append(float(p[0]))
            zs.append(float(p[1]))
    for marker in connectors:
        xs += [float(marker["x"])]
        zs += [float(marker["z"])]
    for aid in all_aids:
        at = model.aid_point(aid)
        if at is not None and (editing or aid.get("shown", True)):
            xs.append(at[0])
            zs.append(at[1])
    if not xs:
        xs, zs = [0.0, 100.0], [0.0, 100.0]
    size = max(max(xs) - min(xs), max(zs) - min(zs), 1.0)
    # the drawing's own three, and the entries' own over them (figure_style): `font`, `stroke` and `radius` stay what they were, the drawing-wide values a connection's and a connector's own layers are drawn with (connection_svg reads them off the record)
    sz = sizes_of(source, size)
    font, stroke, radius = sz.font, sz.stroke, sz.radius

    label_frames = []

    # Elements: their bands (linear) or their outline (area), and their labels, placed on the middle of what is seen of them.
    shapes = {}
    for element in elements:
        if model.element_kind(element) == "linear":
            shapes[element["id"]] = _element_polygons(element, model.element_width(element, positions))
        else:
            shapes[element["id"]] = [[tuple(p) for p in element.get("points", [])]]
    element_draw = []
    for element in elements:
        esz = entry_sizes(sz, element)
        kind = model.element_kind(element)
        points = [tuple(p) for p in element.get("points", [])]
        section = model.element_section(element, positions)
        if kind == "linear":
            width = model.element_width(element, positions)
            polys = shapes[element["id"]]
            # on the middle of the longest stretch no other piece covers (v0.75): the middle of the whole length is where two pieces of a joint cross, under the node, the other piece's label and a connection's rotation centre -- and points[len // 2], what v0.72 to v0.74 used, is a two-point element's far END
            others = [poly for eid, polys_of in shapes.items() if eid != element["id"] for poly in polys_of]
            home, along = _free_middle(element, others)
            direction = along or model.element_direction(element) or (1.0, 0.0)
            angle = math.degrees(math.atan2(direction[1], direction[0]))
            rotate = angle if -90 <= angle <= 90 else angle - 180
        else:
            polys = [points]
            width = None
            xs_e = [p[0] for p in points]
            zs_e = [p[1] for p in points]
            home = ((min(xs_e) + max(xs_e)) / 2.0, (min(zs_e) + max(zs_e)) / 2.0)
            rotate = 0.0
        text = model.element_caption(element, positions)
        dx, dz = label_offset(element)
        frame = _frame([text], home, esz.font, angle=rotate if kind == "linear" else 0.0)
        frame["at"] = (home[0] + dx, home[1] + dz)
        frame["moved"] = bool(dx or dz)
        # A label dragged back onto its own piece needs nothing to say whose it is: the leader is drawn only while the label lies off the piece (v0.77, the engineer's request) -- plan_svg's own rule, a number moved along its beam getting none. `moved` keeps saying whether an offset is stored at all.
        frame["leader"] = frame["moved"] and not _on_own_piece(frame, kind, points, width)
        label_frames.append(("elements", element["id"], frame))
        element_draw.append({"id": element["id"], "kind": kind, "polys": polys, "points": points, "frame": frame,
                             "section": section, "width": width, "sz": esz,
                             "style": figure_style.record(element)})

    # Connector markers: a filled dot, its id beside it.
    connector_draw = []
    for i, marker in enumerate(connectors):
        msz = entry_sizes(sz, marker)
        at = (float(marker["x"]), float(marker["z"]))
        dx, dz = label_offset(marker)
        stated = (marker.get("diameter") or {}).get("value")
        reach = max(float(stated) / 2.0, MARKER_FLOOR_SHARE * msz.radius) if stated else msz.radius
        home = _add(at, (1.3 * reach, -1.3 * reach))
        frame = _frame([_connector_label_text(marker)], home, 0.72 * msz.font)
        frame["at"] = (home[0] + dx, home[1] + dz)
        frame["moved"] = bool(dx or dz)
        # a marker's label dragged clear grows a leader back to the marker, as a piece's does (periodic audit 260916, AUD-7-310)
        frame["anchor"] = at
        frame["leader"] = _left_home(frame)
        label_frames.append(("connectors", marker["id"], frame))
        diameter = (marker.get("diameter") or {}).get("value")
        # a marker stating its diameter is drawn at it, at a detail's real size, with a floor for legibility (v0.75). Its `point` factor moves the floor and the radius of a marker that states no diameter; a diameter stated is a length in millimetres and is never scaled -- a Ø 8 dowel is 8 mm across whatever the sliders say.
        r = max(float(diameter) / 2.0, MARKER_FLOOR_SHARE * msz.radius) if diameter else msz.radius
        connector_draw.append({"id": marker["id"], "kind": marker["kind"], "at": at, "diameter": diameter, "r": r,
                               "frame": frame, "sz": msz, "style": figure_style.record(marker)})

    # Aids: a point/centre is exported unless it says otherwise; a line only where `shown` is true, and drawn heavier when it is -- the module's own rule (schema.py docstring). The editor keeps the rest, drawn light (`editing`).
    aid_draw = []
    for aid in all_aids:
        asz = entry_sizes(sz, aid)
        kind = aid.get("kind")
        shown = aid.get("shown", kind in model.AID_POINT_KINDS)
        if not shown and not editing:
            continue
        at = model.aid_point(aid)
        if at is not None:
            entry = {"id": aid["id"], "kind": kind, "shown": bool(shown), "at": at, "line": None, "frame": None,
                     "sz": asz, "style": figure_style.record(aid)}
            text = str(aid.get("label", "") or "").strip()
            if text:
                # an aid's label was accepted by the check and drawn nowhere (periodic audit 260916, AUD-7-310): it sits beside its point, and may be dragged clear like any other
                home = _add(at, (0.9 * asz.font, -0.9 * asz.font))
                frame = _frame([text], home, 0.72 * asz.font)
                dx, dz = label_offset(aid)
                frame["at"] = (home[0] + dx, home[1] + dz)
                frame["moved"] = bool(dx or dz)
                frame["anchor"] = at
                frame["leader"] = _left_home(frame)
                label_frames.append(("aids", aid["id"], frame))
                entry["frame"] = frame
            aid_draw.append(entry)
            continue
        line = model.aid_line(aid)
        if line is None:
            continue
        # the ends are the frame's edges, worked out once the frame is known (below): a construction line is infinite, and the figure shows all of it that falls inside
        aid_draw.append({"id": aid["id"], "kind": kind, "shown": bool(shown), "at": None, "line": None, "axis": line,
                         "sz": asz, "style": figure_style.record(aid)})

    # Dimensions: statics_svg.py's own arithmetic (_dimension/_angle_dimension), ported onto schema.py's dimension_* helpers.
    dim_draw = []
    for dim in dimensions:
        dsz = entry_sizes(sz, dim)
        kind = dim.get("kind")
        text = model.dimension_text(source, dim)
        value, unit = model.dimension_value(source, dim)
        entry = {"id": dim["id"], "kind": kind, "text": text, "value": value, "unit": unit,
                 "show": model.dimension_show(dim), "sz": dsz, "style": figure_style.record(dim)}
        if kind == "angle":
            rays = model.angle_rays(source, dim)
            angle = model.dimension_angle(source, dim)
            if rays is not None and angle is not None:
                centre, _first, _second = rays
                _c2, sweep, start = angle
                radius = float(dim.get("offset", 0.0)) or 0.25 * size
                steps = max(2, min(48, int(abs(sweep) / 4) + 2))
                arc = [_add(centre, (math.cos(math.radians(start + sweep * k / steps)), math.sin(math.radians(start + sweep * k / steps))), radius) for k in range(steps + 1)]
                entry["centre"] = centre
                entry["radius"] = radius
                entry["arc"] = arc
                label_at = _add(centre, (math.cos(math.radians(start + sweep / 2.0)), math.sin(math.radians(start + sweep / 2.0))), radius + 0.9 * dsz.font)
                anchor = _add(centre, (math.cos(math.radians(start + sweep / 2.0)), math.sin(math.radians(start + sweep / 2.0))), radius)
            else:
                entry["arc"] = []
                entry["centre"] = None
                label_at = (0.0, 0.0)
                anchor = label_at
        else:
            ends = model.dimension_ends(source, dim)
            drawn = model.dimension_line(source, dim)
            if ends is not None and drawn is not None:
                entry["ends"] = ends
                entry["line"] = drawn
                mid = ((drawn[0][0] + drawn[1][0]) / 2.0, (drawn[0][1] + drawn[1][1]) / 2.0)
                frame_dir = model.dimension_direction(source, dim)
                n = frame_dir[1] if frame_dir else (0.0, -1.0)
                label_at = _add(mid, n, 0.9 * dsz.font)
                anchor = mid
            else:
                entry["ends"] = None
                entry["line"] = None
                label_at = (0.0, 0.0)
                anchor = label_at
        dx, dz = label_offset(dim)
        frame = _frame([text], label_at, 0.85 * dsz.font)
        frame["at"] = (label_at[0] + dx, label_at[1] + dz)
        frame["moved"] = bool(dx or dz)
        # a dimension's value dragged clear grows a leader back to its line (periodic audit 260916, AUD-7-310)
        frame["anchor"] = anchor
        frame["leader"] = _left_home(frame)
        # One whose `show` writes nothing -- `none`, or a name it was not given -- is drawn with no label: no box to hit, to drag or to size the frame by. The frame is kept all the same, for where the record says the dimension is written (`meta`).
        entry["labelled"] = bool(text)
        if text:
            label_frames.append(("dimensions", dim["id"], frame))
        entry["frame"] = frame
        dim_draw.append(entry)

    # The texts placed with the Text tool (issue #43): their lines as they print now, centred on their own place -- a frame like any label's, so Woodcore hits it and drags it as it does a label
    text_draw = []
    for text in source.get(figure_text.COLLECTION, []):
        tsz = entry_sizes(sz, text)
        at = (float(text["x"]), float(text["z"]))
        frame = _frame(figure_text.lines(text, values or {}) or [""], at, tsz.font)
        label_frames.append((figure_text.COLLECTION, text["id"], frame))
        text_draw.append({"id": text["id"], "at": at, "frame": frame, "sz": tsz, "style": figure_style.record(text)})

    # The frame: every band, every marker (with its label margin), every shown aid, every dimension's witness and label, every text.
    for t in text_draw:
        for p in label_corners(t["frame"]):
            xs.append(p[0])
            zs.append(p[1])
    for e in element_draw:
        for poly in e["polys"]:
            for p in poly:
                xs.append(p[0])
                zs.append(p[1])
        corners_of_label = label_corners(e["frame"])
        for p in corners_of_label:
            xs.append(p[0])
            zs.append(p[1])
    for c in connector_draw:
        xs += [c["at"][0] - c["r"], c["at"][0] + c["r"]]
        zs += [c["at"][1] - c["r"], c["at"][1] + c["r"]]
        for p in label_corners(c["frame"]):
            xs.append(p[0])
            zs.append(p[1])
    for a in aid_draw:
        if a.get("frame") is not None and a["shown"]:
            for p in label_corners(a["frame"]):
                xs.append(p[0])
                zs.append(p[1])
    for d in dim_draw:
        for p in label_corners(d["frame"]) if d["labelled"] else ():
            xs.append(p[0])
            zs.append(p[1])
        if d.get("ends"):
            for p in d["ends"]:
                xs.append(p[0])
                zs.append(p[1])
        if d.get("arc"):
            for p in d["arc"]:
                xs.append(p[0])
                zs.append(p[1])

    margin = 1.2 * font
    bbox = (min(xs) - margin, min(zs) - margin, max(xs) + margin, max(zs) + margin)
    crop = source.get("crop")
    # `use_crop=False` for a figure drawn ON the schema -- a connection's, a connector's pattern -- which keeps its own frame for its fasteners, arrows and legend (section 3.3decies; periodic audit 260916)
    if isinstance(crop, dict) and use_crop and not editing:
        # «Cadrage» (v0.75): what the report shows is the crop the engineer drew, and nothing the frame would have added round it
        try:
            x0, z0, w, h = (float(crop[k]) for k in ("x", "z", "w", "h"))
            if w > 0 and h > 0:
                bbox = (x0, z0, x0 + w, z0 + h)
        except (KeyError, TypeError, ValueError):
            pass

    # A construction line runs to the edges of the frame, whichever way it crosses it -- it used to be drawn a share of the detail's size either side of its own point, so a line placed off-centre stopped short inside the figure. One that misses the frame altogether is not drawn.
    for a in aid_draw:
        if a.get("axis") is not None:
            a["line"] = clip_line(a["axis"][0], a["axis"][1], bbox)
    aid_draw = [a for a in aid_draw if a["at"] is not None or a["line"] is not None]

    return {
        "source": source,
        "lang": lang,
        "size": size,
        "sz": sz,
        "style": figure_style.drawing_factors(source),
        "font": font,
        "stroke": stroke,
        "radius": radius,
        "elements": element_draw,
        "connectors": connector_draw,
        "aids": aid_draw,
        "dimensions": dim_draw,
        "texts": text_draw,
        "bbox": bbox,
        "label_frames": label_frames,
        "editing": editing,
    }


def clip_line(p, u, box):
    """The two points where the infinite line through `p` along the unit `u` crosses the rectangle `box` = (x0, z0, x1, z1), or None where it misses it -- what a construction line is drawn between, in the export and in Woodcore's canvas alike (the canvas passes the part of the scene in view)."""
    x0, z0, x1, z1 = box
    low, high = -math.inf, math.inf
    for origin, direction, lo, hi in ((p[0], u[0], x0, x1), (p[1], u[1], z0, z1)):
        if abs(direction) < 1e-12:
            if origin < lo or origin > hi:
                return None
            continue
        t0, t1 = (lo - origin) / direction, (hi - origin) / direction
        low, high = max(low, min(t0, t1)), min(high, max(t0, t1))
    if not math.isfinite(low) or not math.isfinite(high) or high - low <= 1e-9:
        return None
    return (_add(p, u, low), _add(p, u, high))


def _box_interval(a, b, frame, margin=0.0):
    """The stretch of the segment a-b that lies inside `frame`'s box, as (t0, t1) in [0, 1], or None where it misses it.

    The box is turned with its text, so the segment is taken into the box's own frame (`_local`) and clipped there against a rectangle that is axis-aligned in those coordinates -- the slab method `clip_line` already uses, on a rectangle that has been turned rather than on a frame that has.
    """
    p, q = _local(frame, a), _local(frame, b)
    d = (q[0] - p[0], q[1] - p[1])
    lo, hi = 0.0, 1.0
    for origin, direction, half in ((p[0], d[0], frame["hw"] + margin), (p[1], d[1], frame["hh"] + margin)):
        if abs(direction) < 1e-12:
            if origin < -half or origin > half:
                return None
            continue
        t0, t1 = (-half - origin) / direction, (half - origin) / direction
        lo, hi = max(lo, min(t0, t1)), min(hi, max(t0, t1))
    return None if hi - lo <= 1e-9 else (lo, hi)


def cut_at_labels(a, b, frames, margin=0.0):
    """The stretches of the segment a-b left once the boxes of `frames` are taken out: [(p, q), ...], and [(a, b)] where it crosses none of them.

    A shown construction line is drawn **over everything, the labels included** -- v0.77's rule, which stands, a line being what the eye reads the detail against -- so a line ran straight through a piece's number and no ground behind the text could mend it. The line gives way instead: it stops at the box and starts again beyond it, which is what a drawing office does and what the engineer asked for. The line still runs to the edges of the frame; what is left out is only what falls inside a box.

    ⚠️ It is read by the export **and by Woodcore's canvas**, which draws the lines itself across the whole view (`schema_canvas.aid_line_segments`): the window and the report would otherwise show one detail two ways.

    A box already carries the padding `_label_box` puts round its text, so `margin` is 0 by default rather than a share of the font invented here.
    """
    cuts = sorted(filter(None, (_box_interval(a, b, frame, margin) for frame in frames)))
    if not cuts:
        return [(a, b)]
    out, cursor = [], 0.0
    for lo, hi in cuts:
        if lo - cursor > 1e-6:
            out.append((_at(a, b, cursor), _at(a, b, lo)))
        cursor = max(cursor, hi)
    if 1.0 - cursor > 1e-6:
        out.append((_at(a, b, cursor), b))
    return out


def _at(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


label_corners = dimension.box_corners   # Woodcore outlines a selected label with it (ARCH-004: one copy)


def meta(drawing):
    """What data/schemas.json carries for one language: the frame, and every entry's placed geometry (docs/architecture/principles.md: a report record carries what show-schema needs and nothing it would have to recompute)."""
    x0, y0, x1, y1 = drawing["bbox"]

    def r4(v):
        return round(v, 4) + 0.0

    elements = []
    for e, source_element in zip(drawing["elements"], drawing["source"].get("elements", [])):
        entry = {
            "id": e["id"], "kind": e["kind"],
            "at": [[r4(p[0]), r4(p[1])] for p in e["points"]],
            "label": e["frame"]["lines"][0],
        }
        if source_element.get("position"):
            entry["position"] = source_element["position"]
        if e["kind"] == "linear" and "view" in source_element:
            entry["view"] = source_element["view"]
        # the section the drawing was made with, and where each side came from (v0.75): a connector calculation may read it
        section = e.get("section") or {}
        for side in model.ELEMENT_SIDES:
            value = section.get(side)
            entry[side] = None if value is None else r4(value)
            entry[f"{side}_from"] = section.get(f"{side}_from") or ""
        if e.get("width") is not None:
            entry["width"] = r4(e["width"])
        _own_style(entry, e)
        elements.append(entry)

    connectors = []
    for c in drawing["connectors"]:
        entry = {"id": c["id"], "kind": c["kind"], "at": [r4(c["at"][0]), r4(c["at"][1])]}
        if c["diameter"] is not None:
            entry["diameter"] = r4(c["diameter"])
        _own_style(entry, c)
        connectors.append(entry)

    aids = []
    for a in drawing["aids"]:
        entry = {"id": a["id"], "kind": a["kind"], "shown": True}
        if a["at"] is not None:
            entry["at"] = [r4(a["at"][0]), r4(a["at"][1])]
        if a["line"] is not None:
            entry["line"] = [[r4(p[0]), r4(p[1])] for p in a["line"]]
        _own_style(entry, a)
        aids.append(entry)

    dimensions = []
    for d in drawing["dimensions"]:
        entry = {"id": d["id"], "kind": d["kind"], "show": d["show"], "text": d["text"], "unit": d["unit"], "at": [r4(d["frame"]["at"][0]), r4(d["frame"]["at"][1])]}
        if d.get("value") is not None:
            entry["value"] = r4(d["value"])
        if d.get("line"):
            entry["line"] = [[r4(p[0]), r4(p[1])] for p in d["line"]]
        if d.get("centre") is not None:
            entry["centre"] = [r4(d["centre"][0]), r4(d["centre"][1])]
        if d.get("radius") is not None:
            entry["radius"] = r4(d["radius"])
        _own_style(entry, d)
        dimensions.append(entry)

    return {
        "view": {"x": r4(x0), "y": r4(y0), "w": r4(x1 - x0), "h": r4(y1 - y0)},
        "style": {key: r4(value) for key, value in drawing["style"].items()},
        "elements": elements,
        "connectors": connectors,
        "aids": aids,
        "dimensions": dimensions,
    }


def _own_style(entry, drawn):
    """The factors this entry stated over the drawing's, where it stated any (`figure_style.record`, which rounded them when the drawing was laid out): a record says what the figure was drawn with, which is the convention every other placed value here follows. An entry that stated none carries no key at all, so `data/schemas.json` does not move for a schema that uses none."""
    if drawn.get("style"):
        entry["style"] = dict(drawn["style"])


def hit_label(source, point, tolerance, frames=None):
    frames = frames if frames is not None else label_frames(source)
    hit = None
    for key, frame in frames:
        if on_label(frame, point, 0.5 * tolerance):
            hit = key
    return hit


# --- Render --------------------------------------------------------------------------


def render(drawing, highlight=None, background=True, aid_lines=True, aid_points=True):
    """The schema's figure as an SVG document. `highlight` is a (collection, id) pair to ring, inserted at HIGHLIGHT_MARK by lib/calc-engine.typ the way a connection's and a static model's own halo already are. `background` is off only for Woodcore's own canvas, which draws its grid underneath and must see it through the figure (statics_svg.render's own flag, for the same reason)."""
    x0, y0, x1, y1 = drawing["bbox"]
    view_w, view_h = x1 - x0, y1 - y0
    scale = PAPER_MM / max(view_w, view_h, 1e-6)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="{_f(x0)} {_f(y0)} {_f(view_w)} {_f(view_h)}" '
        f'width="{_f(view_w * scale)}mm" height="{_f(view_h * scale)}mm">',
    ]
    if background:
        out.append(f'<rect x="{_f(x0)}" y="{_f(y0)}" width="{_f(view_w)}" height="{_f(view_h)}" fill="{GROUND}"/>')
    out.append(HIGHLIGHT_MARK)
    body(out, drawing, highlight, aid_lines=aid_lines, aid_points=aid_points)
    out.append("</svg>")
    return "\n".join(out) + "\n"


def body(out, drawing, highlight=None, markers=True, aid_lines=True, aid_points=True):
    """Everything the figure draws, appended to `out` -- the aids, the pieces, the dimensions and the connector markers -- so that one routine draws the schema wherever it is shown.

    It is split out of `render` for `connection_svg`, whose figure is this drawing plus its own layers (the numbered fasteners, the rotation centre, the x/z pair, the moment's arc, the force arrows): the alternative was a second drawing of one detail, which is the very duplication the schemas module exists to remove (docs/architecture/principles.md §2, rule 1).

    `markers` is false for that caller. A connection numbers the fasteners **it** carries 1, 2, 3 ... in the order its own tables number them, which is neither the schema's marker order nor necessarily all of its markers -- a schema may carry two calculations' worth -- so it draws its own.

    ⚠️ **Every entry is drawn with its own sizes** (`entry["sz"]`, v0.99), so a factor one entry states over the drawing's reaches the window's canvas and the exported figure alike -- they are the one SVG. The drawing's own three are still used for what belongs to the drawing rather than to an entry: an arc's default radius, the frame's margin.
    """
    sz = drawing.get("sz") or Sizes(drawing["size"], drawing.get("style"))
    radius = drawing["radius"]
    # what a shown construction line is cut at: the box of every label this figure actually writes, which is not every label the drawing laid out -- a connection's figure draws no marker labels (`markers`), and a dimension whose `show` writes nothing has no box at all
    cut_frames = _drawn_frames(drawing, markers)

    # The pieces: their bands or outline, then their labels.
    for i, e in enumerate(drawing["elements"]):
        fill = ELEMENT_FILLS[i % len(ELEMENT_FILLS)]
        for poly in e["polys"]:
            _polygon(out, poly, fill, ELEMENT_OPACITY, ELEMENT_STROKE, 1.3 * e["sz"].stroke)
    for e in drawing["elements"]:
        _draw_label(out, e["frame"], e["sz"], colour=ELEMENT_STROKE)
        _leader(out, e["frame"], e["sz"], colour=ELEMENT_STROKE)

    # The dimensions: a length's witness lines and heads, or an angle's arc -- and what their `show` writes, where it writes anything.
    for d in drawing["dimensions"]:
        if d["kind"] == "angle":
            _draw_angle_dimension(out, d, d["sz"])
        elif d.get("line"):
            _draw_linear_dimension(out, d, d["sz"])
        if d.get("labelled", True):
            _leader(out, d["frame"], d["sz"], 0.85, DIMENSION, dot=False)
            _draw_label(out, d["frame"], d["sz"], 0.85, DIMENSION)

    # The texts placed with the Text tool (issue #43), over the pieces and the dimensions: figure_text sets them, with no ground and no bold line -- a note on the drawing, not the name of a part of it
    for t in drawing.get("texts", ()):
        font = t["sz"].font
        figure_text.draw(out, t["frame"]["at"], t["frame"]["lines"], font, LABEL_COLOUR, halo=TEXT_HALO * font)

    # A marker's or a named point's halo goes here, over everything above and under the markers and the aids below (HIGHLIGHT_POINTS_MARK): at HIGHLIGHT_MARK a point's halo lay under the pieces' fill and could not be seen.
    out.append(HIGHLIGHT_POINTS_MARK)

    # The connector markers, on top, numbered by their own id.
    if markers:
        for c in drawing["connectors"]:
            csz = c["sz"]
            r = c.get("r", radius)
            _leader(out, c["frame"], csz, 0.72, CONNECTOR_LABEL, dot=False)
            if highlight == ("connectors", c["id"]):
                _circle(out, c["at"], 2.0 * r, "none", HIGHLIGHT, 0.6 * csz.stroke)
            _circle(out, c["at"], r, CONNECTOR_FILL, LABEL_GROUND, 0.5 * csz.stroke)
            _draw_label(out, c["frame"], csz, 0.72, CONNECTOR_LABEL)

    if highlight and highlight[0] == "elements":
        for e in drawing["elements"]:
            if e["id"] == highlight[1]:
                for poly in e["polys"]:
                    _polygon(out, poly, "none", 1.0, HIGHLIGHT, 2.2 * e["sz"].stroke)

    # The construction aids, **over everything else**, in three layers: the centres, then the construction lines over them, then the named points **over the lines** as green crosses -- a construction line is what the eye reads the detail against, and a point is what it must always find (v0.77). Between AIDS_OPEN/AIDS_CLOSE, so show-schema's `aids: false` still strips the whole span, for a figure that wants the detail alone.
    out.append(AIDS_OPEN)
    for a in drawing["aids"]:
        if a["at"] is None or a["kind"] == "point":
            continue
        # an aid the report leaves out reaches here only in the editor, and is drawn light there: seen while it helps, and never mistaken for one the report will print
        asz = a["sz"]
        shown = a.get("shown", True)
        colour = AID_SHOWN_COLOUR if shown else AID_COLOUR
        weight = 1.0 if shown else 0.6
        r = asz.on_point(0.35)
        _line(out, (a["at"][0] - r, a["at"][1]), (a["at"][0] + r, a["at"][1]), colour, 0.6 * weight * asz.stroke, cap="butt")
        _line(out, (a["at"][0], a["at"][1] - r), (a["at"][0], a["at"][1] + r), colour, 0.6 * weight * asz.stroke, cap="butt")
        _circle(out, a["at"], 0.6 * r, "none", colour, 0.6 * weight * asz.stroke)
    if aid_lines:
        # `aid_lines` is false for Woodcore's own canvas alone, which draws the lines itself across the whole view (schema_canvas.drawForeground)
        for a in drawing["aids"]:
            if a["at"] is None and a["line"] is not None:
                asz = a["sz"]
                shown = a.get("shown", True)
                colour = AID_SHOWN_COLOUR if shown else AID_COLOUR
                dash = f"{_f(6 * asz.stroke)},{_f(4 * asz.stroke)}"
                width = 0.9 * (1.0 if shown else 0.6) * asz.stroke
                # cut at the boxes of the labels it crosses (v0.99): the line is drawn over everything, so it is the line that gives way to the text and not the other way round
                for p, q in cut_at_labels(a["line"][0], a["line"][1], cut_frames):
                    _line(out, p, q, colour, width, dash=dash, cap="butt")
    if aid_points:
        # `aid_points` is false for the canvas too, which draws the points after its own lines (schema_canvas.drawForeground)
        for a in drawing["aids"]:
            if a["at"] is not None and a["kind"] == "point":
                _point_cross(out, a["at"], a["sz"], a.get("shown", True))
    # an aid's label, over its point: drawn whatever `aid_points` says, the canvas drawing only the crosses itself
    for a in drawing["aids"]:
        if a.get("frame") is not None:
            colour = AID_SHOWN_COLOUR if a.get("shown", True) else AID_COLOUR
            _leader(out, a["frame"], a["sz"], 0.72, colour, dot=False)
            _draw_label(out, a["frame"], a["sz"], 0.72, colour)
    out.append(AIDS_CLOSE)


def _drawn_frames(drawing, markers=True):
    """The boxes of the labels this figure actually writes -- what a construction line is cut at.

    Not `drawing["label_frames"]`, which is every label the layout placed: a connection's figure draws none of the schema's marker labels (`markers`), and cutting a line at a box where nothing is written would open a gap in the line for no reason a reader could see.
    """
    frames = [e["frame"] for e in drawing["elements"]]
    frames += [d["frame"] for d in drawing["dimensions"] if d.get("labelled", True)]
    if markers:
        frames += [c["frame"] for c in drawing["connectors"]]
    frames += [a["frame"] for a in drawing["aids"] if a.get("frame") is not None]
    frames += [t["frame"] for t in drawing.get("texts", ())]
    return frames


def _point_cross(out, at, sz, shown=True):
    """A named point: a green cross, one stroke each way -- heavier where the report prints it, lighter where only the editor shows it. A symbol placed on a point, so its reach follows `point` and its ink follows `line`."""
    r = sz.on_point(0.45)
    width = (1.0 if shown else 0.65) * sz.stroke
    _line(out, (at[0] - r, at[1]), (at[0] + r, at[1]), POINT_COLOUR, width, cap="butt")
    _line(out, (at[0], at[1] - r), (at[0], at[1] + r), POINT_COLOUR, width, cap="butt")


def _draw_linear_dimension(out, d, sz):
    """A length: a witness line part of the way out from each end, the dimension line between them with a head at either end -- **cut where its own value stands over it** (v0.99).

    The cut is the drawing office's answer to a value that has to be read against the line it belongs to, and it is the one the engineer asked for over making the value's ground opaque: a line broken under its own number is read as one line, where a white box laid over it reads as a patch. The value floats clear of the line by default (`0.9 * font` off it), so nothing is cut until the engineer drags it onto the line -- which is exactly when it would otherwise be unreadable.
    """
    (a, b), (p0, p1) = d["ends"], d["line"]
    width = 0.35 * sz.stroke
    for end, foot in ((a, p0), (b, p1)):
        reach = math.dist(end, foot)
        if reach < 1e-9:
            continue
        u = _unit(end, foot)
        drawn = max(DIM_WITNESS_SHARE * reach, min(sz.on_line(DIM_WITNESS_MIN_FONT), reach))
        gap = max(reach - drawn, 0.0)
        _line(out, _add(end, u, gap), _add(foot, u, sz.on_line(1.2)), DIMENSION, width, cap="butt")
    own = [d["frame"]] if d.get("labelled", True) else []
    for p, q in cut_at_labels(p0, p1, own):
        _line(out, p, q, DIMENSION, width, cap="butt")
    length = math.dist(p0, p1)
    if length > 1e-9:
        u = _unit(p0, p1)
        _dim_head(out, p0, u, sz, length)
        _dim_head(out, p1, (-u[0], -u[1]), sz, length)


def _dim_head(out, tip, inward, sz, length=None):
    full = sz.on_line(2.2)
    head = full if length is None else min(full, 0.4 * length)
    base = _add(tip, inward, head)
    half = sz.on_line(0.55) * (head / full if full > 1e-12 else 1.0)
    p = _perp(inward)
    _polygon(out, [tip, _add(base, p, half), _add(base, p, -half)], DIMENSION)


def _draw_angle_dimension(out, d, sz):
    arc, centre = d.get("arc") or [], d.get("centre")
    if len(arc) < 2 or centre is None:
        return
    for end in (arc[0], arc[-1]):
        _line(out, centre, end, DIMENSION, 0.22 * sz.stroke, cap="butt")
    _polyline(out, arc, DIMENSION, 0.35 * sz.stroke)
    for tip, neighbour in ((arc[0], arc[1]), (arc[-1], arc[-2])):
        if math.dist(tip, neighbour) > 1e-9:
            _dim_head(out, tip, _unit(tip, neighbour), sz)


# --- The tool bar's swatches -------------------------------------------------------

SWATCH_STYLE = {"line": 1.6, "point": 1.4}


def swatch(kind):
    """A small SVG icon for one of the schema tab's tools -- the pattern the static models' and the connectors' bars already use (statics_svg.swatch, connector_svg.SWATCHES): the tool bar shows **what it draws** rather than a generic glyph.

    ⚠️ Every kind gets its own, and that is the whole point: the eight aid tools and the four dimension tools differ only in the direction or the measure they produce, so one shared dashed line for all twelve would leave the bar saying nothing at all. `_dash` is the construction lines' own stroke, `_dim` a dimension's slim head.
    """
    dash = "5,3"
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">']

    def guide(a, b):
        _line(out, a, b, AID_SHOWN_COLOUR, 1.8, dash=dash, cap="butt")

    def dim(a, b):
        """A dimension line with a slim head at either end, which is how the figure draws one."""
        _line(out, a, b, DIMENSION, 1.6, cap="butt")
        u = _unit(a, b)
        n = _perp(u)
        for tip, inward in ((a, u), (b, (-u[0], -u[1]))):
            base = _add(tip, inward, 5.0)
            _polygon(out, [tip, _add(base, n, 1.8), _add(base, n, -1.8)], DIMENSION)

    if kind == "text":
        return figure_text.icon_svg(DIMENSION)   # the Text tool's T, the four engines' one (issue #43), in the ink the bar recolours

    if kind in model.CONNECTOR_KINDS:
        # A fastener's own symbol is connector_svg's, not a second drawing of it: the Connecteurs tab's
        # bar and this one must show the same thing for the same kind. A kind it has no symbol for --
        # one added to connector.TYPES and not yet drawn -- falls back to the marker the figure puts on
        # the drawing, which says at least that it is a fastener.
        from domains import connector_svg
        if kind in connector_svg.SWATCHES:
            return connector_svg.swatch(kind)
        _circle(out, (16, 16), 5, CONNECTOR_FILL)
    elif kind == "linear":
        _line(out, (6, 24), (26, 8), ELEMENT_STROKE, 4, cap="round")
    elif kind == "area":
        _polygon(out, [(6, 24), (26, 24), (18, 8)], ELEMENT_FILLS[0], ELEMENT_OPACITY, ELEMENT_STROKE, 1.5)
    elif kind == "point":
        # the green cross the drawing puts down (v0.77)
        _line(out, (16, 7), (16, 25), POINT_COLOUR, 2.6, cap="butt")
        _line(out, (7, 16), (25, 16), POINT_COLOUR, 2.6, cap="butt")
    elif kind in AID_POINT_SWATCHES:
        _circle(out, (16, 16), 2.4, AID_SHOWN_COLOUR)
        if kind == "centre":
            _circle(out, (16, 16), 6.5, "none", AID_SHOWN_COLOUR, 1.4)
            _line(out, (16, 7), (16, 25), AID_SHOWN_COLOUR, 1.0, cap="butt")
            _line(out, (7, 16), (25, 16), AID_SHOWN_COLOUR, 1.0, cap="butt")
    elif kind == "vertical":
        guide((16, 3), (16, 29))
    elif kind == "horizontal":
        guide((3, 16), (29, 16))
    elif kind == "point-angle":
        guide((6, 26), (28, 10))
        _circle(out, (6, 26), 2.4, AID_SHOWN_COLOUR)
    elif kind == "perpendicular":
        _line(out, (4, 24), (28, 24), ELEMENT_STROKE, 2.4, cap="butt")
        guide((16, 24), (16, 4))
    elif kind == "parallel":
        _line(out, (4, 22), (28, 22), ELEMENT_STROKE, 2.4, cap="butt")
        guide((4, 11), (28, 11))
    elif kind == "two-points":
        guide((5, 25), (27, 7))
        _circle(out, (5, 25), 2.4, AID_SHOWN_COLOUR)
        _circle(out, (27, 7), 2.4, AID_SHOWN_COLOUR)
    elif kind == "horizontal-dim":
        dim((4, 16), (28, 16))
    elif kind == "vertical-dim":
        dim((16, 4), (16, 28))
    elif kind == "parallel-dim":
        dim((5, 26), (27, 8))
    elif kind in MODIFY_SWATCHES:
        # The six verbs are not entity kinds, so they are keyed by their own names -- which is also
        # what keeps them clear of the three an aid line and a dimension already share (horizontal,
        # vertical, parallel). Each shows the piece it acts on and what the verb does to it.
        bar, ghost = ELEMENT_STROKE, AID_SHOWN_COLOUR

        def arrow(a, b, colour=None):
            colour = colour or bar
            _line(out, a, b, colour, 1.8, cap="butt")
            u = _unit(a, b)
            n = _perp(u)
            base = _add(b, u, -5.5)
            _polygon(out, [b, _add(base, n, 2.6), _add(base, n, -2.6)], colour)

        if kind == "move":
            _line(out, (4, 22), (18, 22), bar, 3.4, cap="round")
            arrow((10, 17), (26, 8))
        elif kind == "duplicate":
            _line(out, (4, 24), (20, 24), ghost, 3.0, dash=dash, cap="round")
            _line(out, (11, 12), (27, 12), bar, 3.4, cap="round")
        elif kind == "rotate":
            _polyline(out, [(16 + 10 * math.cos(math.radians(a)), 16 + 10 * math.sin(math.radians(a)))
                            for a in range(200, 361, 10)], bar, 2.2)
            arrow((24, 12), (28, 18))
            _circle(out, (16, 16), 1.8, bar)
        elif kind == "mirror":
            _line(out, (16, 3), (16, 29), ghost, 1.6, dash=dash, cap="butt")
            _polygon(out, [(13, 9), (13, 23), (5, 16)], ELEMENT_FILLS[0], ELEMENT_OPACITY, bar, 1.4)
            _polygon(out, [(19, 9), (19, 23), (27, 16)], "none", 1, ghost, 1.4)
        elif kind == "split":
            _line(out, (4, 21), (13, 21), bar, 3.4, cap="butt")
            _line(out, (19, 21), (28, 21), bar, 3.4, cap="butt")
            _line(out, (16, 5), (16, 29), ghost, 1.8, dash=dash, cap="butt")
        elif kind == "merge":
            _line(out, (3, 16), (13, 16), bar, 3.4, cap="butt")
            _line(out, (19, 16), (29, 16), bar, 3.4, cap="butt")
            arrow((10, 26), (15, 21), ghost)
            arrow((22, 26), (17, 21), ghost)
    elif kind == "angle-dim":
        _line(out, (5, 26), (29, 26), DIMENSION, 1.6, cap="butt")
        _line(out, (5, 26), (25, 8), DIMENSION, 1.6, cap="butt")
        _polyline(out, [_add((5, 26), (math.cos(math.radians(-a)), -math.sin(math.radians(-a))), 13.0)
                        for a in (0, 6, 12, 18, 24, 30, 36, 42)], DIMENSION, 1.2)
    else:
        guide((4, 16), (28, 16))
    out.append("</svg>")
    return "\n".join(out)


# The two aid kinds drawn as a point rather than as a line.
AID_POINT_SWATCHES = ("centre", "point")

# What the four dimension tools ask swatch() for: their own `kind` is the dimension's, which would
# otherwise collide with the aid lines named the same way ("horizontal", "vertical", "parallel").
DIMENSION_SWATCHES = {"horizontal": "horizontal-dim", "vertical": "vertical-dim",
                      "parallel": "parallel-dim", "angle": "angle-dim"}

# The six verbs of the Modification group (v0.73). Keyed by the verb rather than by a kind, since a
# verb draws nothing: what its icon shows is a piece and what happens to it.
MODIFY_SWATCHES = ("move", "duplicate", "rotate", "mirror", "split", "merge")
