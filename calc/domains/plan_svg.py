"""The drawing of a position plan, as SVG text: the STE symbols (STE Compact 02, «Plandarstellung im Holzbau») of every element with its position number, the axes with their bubbles and the lengths of the walls, over a white veil that lets the architect's plan show through; and the swatches of the symbols a plan uses, which show-plan sets in its legend beside what each stands for (docs/domain/position-plans.md §3.3sexies). The scale bar is the report's: show-plan draws it under the plan, where it hides nothing.

One drawing serves both places it is seen. Woodcore's window shows it over the background while a plan is edited, and export writes it to data/plans/<id>.svg (Plans/Position-plan/Exports/Figures/<id>.svg in a project laid out by folders, issue #64), which lib/calc-engine.typ's show-plan sets over the same background in the report -- so the plan the engineer drew is the plan the checker reads. That is why it is built as plain text here, with no Qt: export_all.py draws it too, without a window. The symbols follow the reference editor in 000-positionsPlan, whose code is not reused: its colours and proportions are the STE convention, and are what is taken from it.

It is kept to what both renderers read alike. QtSvg implements SVG Tiny 1.2, which has no <pattern>, no clipPath, no <marker>, no CSS and no paint-order: a concrete wall's hatching is made of segments cut to its outline here, a text's white halo is the text drawn twice, and an arrowhead is a polygon. Coordinates are the plan's sheet units (plan.py), y down.

Two markers are left in the report's drawing, as in a connection's figure: HIGHLIGHT_MARK, under the symbols, where show-plan inserts the halo of the positions it highlights, and AXES_OPEN/AXES_CLOSE around the axes, which `axes: false` removes. A section's storey lines stand between STOREYS_OPEN/STOREYS_CLOSE (v0.114), written only on a plan that has one.

Since v0.99 the three sliders are two levels: the plan's own (`Sizes`, `sizes_of`) and, over them, the factors one element or one axis states for itself (`entry_sizes`, `calc/domains/figure_style.py`). Every function that draws one entry is handed that entry's sizes; `number_frame` alone reads the factors off the element it is given, since it is asked from the window and from the export with the plan's.
"""

import math
from xml.sax.saxutils import escape

from domains import svg_draw  # the one writer of an SVG number and text (D6)
from domains import dimension  # one unit vector and one label box (ARCH-004)
from domains import figure_style
from domains import figure_text  # a text placed with the Text tool, the four engines' one (issue #43)
from domains import plan as model
from domains import plan_centres  # where the stiffness centre and the mass centre are: computed there, drawn here (issue #54)
from domains.dimension import _local  # plane geometry written once (D4)

# The STE colours.
ORANGE = svg_draw.colour("orange")
VIOLET = svg_draw.colour("violet")
BLUE = svg_draw.colour("blue")
GREEN = svg_draw.colour("green")
BROWN = svg_draw.colour("brown")
LIGHT_BLUE = svg_draw.colour("light-blue")
YELLOW = svg_draw.colour("yellow")
GREY = svg_draw.colour("aid")
INK = svg_draw.colour("ink")
GROUND = svg_draw.colour("ground")
MUTED = svg_draw.colour("muted")
CONCRETE = svg_draw.colour("concrete")
CONCRETE_DECK = svg_draw.colour("concrete-deck")
COLOURS = {"V": ORANGE, "H": VIOLET, "W": ORANGE, "T": BLUE, "S": BLUE, "A": VIOLET, "D": BROWN,
           "M": GREEN, "L": LIGHT_BLUE, "Ö": YELLOW, "B": GREY, "PL": ORANGE, "LL": ORANGE}
# A W carries both an orange and a violet symbol, so its number is set in black.
LABEL_COLOURS = {"W": INK}
# The load-path plan's symbols (v0.116, STE Compact 02 pp. 14-15) take their colour from their subtype, not their type: a vertical load orange, a horizontal one violet, one acting both ways violet with orange in it -- its number then in black, as a W's.
LOAD_COLOURS = {"vert": ORANGE, "horiz": VIOLET, "vh": VIOLET}
LOAD_LABEL_COLOURS = {"vert": ORANGE, "horiz": VIOLET, "vh": INK}
# A section's load transfer level (STE p. 14, «Niveau de reprise des charges»): a red dash-dot line, a red arrow coming down onto each end, and its words beside it.
LOAD_LEVEL_COLOUR = svg_draw.colour("red")
# The types whose number sits in a stadium rather than a rectangle, as in the STE legend.
STADIUM = {"T", "A", "D"}
AXIS_COLOUR = svg_draw.colour("axis")
FLAG_COLOUR = svg_draw.colour("red")
# One family, not a list: QtSvg takes the whole font-family string as a single name, so a list matched nothing and Woodcore set the numbers in a fallback face (statics_svg.FONT; periodic audit 260916, AUD-6-24).
FONT = svg_draw.FONT

HIGHLIGHT_MARK = "<!-- highlight -->"
AXES_OPEN = "<!-- axes -->"
AXES_CLOSE = "<!-- /axes -->"
# A section's storey lines, between markers of their own, which show-plan may strip as it strips the axes. Written only on a plan that has a storey line, so every other plan is drawn byte for byte as before.
STOREYS_OPEN = "<!-- storeys -->"
STOREYS_CLOSE = "<!-- /storeys -->"
STOREY_COLOUR = AXIS_COLOUR
# A section's storey boxes, each its STE designation (x1xx) in a box at its middle, and its load transfer levels (v0.116): each between markers of their own, written only where the section has one.
BOXES_OPEN = "<!-- storey-boxes -->"
BOXES_CLOSE = "<!-- /storey-boxes -->"
LEVELS_OPEN = "<!-- load-levels -->"
LEVELS_CLOSE = "<!-- /load-levels -->"
# A plan's dimensions (issue #9), between markers `show-plan(dimensions: false)` takes out -- written only where the plan has a dimension it draws, so a plan without is drawn byte for byte as before. In the axes' ink.
DIMENSIONS_OPEN = "<!-- dimensions -->"
DIMENSIONS_CLOSE = "<!-- /dimensions -->"
DIMENSION_COLOUR = AXIS_COLOUR
# The lengths written beside the elements (issue #9), between markers `show-plan(lengths: false)` takes out -- written only where a length is drawn.
LENGTHS_OPEN = "<!-- lengths -->"
LENGTHS_CLOSE = "<!-- /lengths -->"
# The stiffness centre S, the mass centre M and the building's outline (issue #54, domains/plan_centres.py), between markers `show-plan(centres: false)` takes out -- two pairs of them, the outline under the symbols and the two centres over the numbers --, written only where there is one of the three to draw and only where `render` is asked for them: Woodcore's window always is, the export where the plan says so (`print_centres`). S is drawn in the bracing walls' violet, being theirs; M and the outline in the axes' ink.
CENTRES_OPEN = "<!-- centres -->"
CENTRES_CLOSE = "<!-- /centres -->"
STIFFNESS_COLOUR = VIOLET
MASS_COLOUR = AXIS_COLOUR
OUTLINE_COLOUR = AXIS_COLOUR
# Their three legend lines, by key -- the lines `centres: false` takes out of a legend (`legend_items` marks them).
CENTRE_KEYS = ("Steifigkeitszentrum", "Massenzentrum", "Umriss")

# The symbols' unit, in sheet units, is the longer side of the frame the report shows divided by this: at the report's full text width a position number then comes out about 6 pt high, whatever the frame, and the style sliders scale it from there.
UNIT_DIVISOR = 850.0

# The legend's lines, in the order it lists them, by the key of the symbol each shows (a type, or a type and the subtype that changes its symbol): STE's wording, each line saying on its own what STE's legend says under a heading (Wände, Auflager Massivbau, Abfangungen), since show-plan flows the lines into as many columns as the width takes.
LEGEND = (
    ("T", "Träger / Wechsel / Unterzug / Überzug"),
    ("S", "Stütze"),
    ("A", "Aussteifung, Stabilisierung Einzelstab"),
    ("D:normal", "Decke / Dach, Pfeil = Spannrichtung"),
    ("D:scheibe", "Scheibenbildung Decke / Dach"),
    ("Ö", "Ausschnitt / Öffnung"),
    ("V", "Wand, vertikal tragend"),
    ("H", "Wand, aussteifend"),
    ("W", "Wand, vertikal tragend und aussteifend"),
    ("B:wand", "Betonwand"),
    ("B:decke", "Betondecke"),
    ("M:vert", "Auflager Massivbau, vertikal"),
    ("M:horiz", "Auflager Massivbau, horizontal"),
    ("M:vh", "Auflager Massivbau, vertikal und horizontal"),
    ("L:linie", "Abfangung Linienlast von oben"),
    ("L:punkt", "Abfangung Punktlast von oben"),
    ("PL:vert", "Punktlast vertikal"),
    ("PL:horiz", "Punktlast horizontal"),
    ("PL:vh", "Punktlast vertikal und horizontal"),
    ("LL:vert", "Linienlast vertikal"),
    ("LL:horiz", "Linienlast horizontal"),
    ("LL:vh", "Linienlast vertikal und horizontal"),
    ("Lastniveau", "Lastübergabeniveau"),
    ("Achse", "Achse"),
    ("Steifigkeitszentrum", "Steifigkeitszentrum"),
    ("Massenzentrum", "Massenzentrum"),
    ("Umriss", "Gebäudeumriss"),
)
# A legend swatch, in mm, and the symbols' unit in it: fine lines, the symbols' own proportions -- the plan's sliders size the plan's symbols for the plan, and a legend drawn with them came out coarse.
LEGEND_SWATCH = (10.0, 3.6)
LEGEND_UNIT = 0.12


_f = svg_draw.number_at(3)   # a coordinate at 3 decimals (svg_draw.py, D6)


def _pts(points):
    return " ".join(f"{_f(x)},{_f(y)}" for x, y in points)


_unit = dimension.unit   # (ARCH-004: one copy, D-15)


def base_unit(crop):
    """The symbols' unit for a frame {x, y, w, h}, before the style sliders."""
    return max(crop["w"], crop["h"]) / UNIT_DIVISOR


class Sizes:
    """A symbol's sizes, from the unit and the three sliders: `line` for strokes, dashes and arrowheads, `point` for the squares and dots placed on a point, `text` for the numbers, their boxes, the lengths and the axes' bubbles."""

    def __init__(self, unit, style):
        self.u = unit
        self.lf = float(style.get("line", 1.0))
        self.pf = float(style.get("point", 1.0))
        self.tf = float(style.get("text", 1.0))
        # The plan's own sizes, whatever these are: `scaled` carries it over, so an entry's factors can be asked for from the plan's sizes or from another entry's and are never applied twice (`entry_sizes`).
        self.drawing = self

    def scaled(self, factors):
        """This, with `factors` multiplied into the three -- what an entry that states a factor of its own is drawn with (figure_style). It multiplies this one's three and remembers the *plan's*, which is what lets `entry_sizes` answer from either."""
        sz = Sizes(self.u, {"line": self.lf * factors["line"], "point": self.pf * factors["point"],
                            "text": self.tf * factors["text"]})
        sz.drawing = self.drawing
        return sz

    def line(self, x):
        return x * self.u * self.lf

    def point(self, x):
        return x * self.u * self.pf

    def text(self, x):
        return x * self.u * self.tf


def sizes_of(source):
    """The sizes a plan's symbols are drawn at: the unit of the frame the report shows, and the plan's three sliders."""
    return Sizes(base_unit(model.crop_of(source)), source.get("style", {}))


def entry_sizes(sz, entry):
    """The sizes one element or one axis is drawn at: the plan's, times the factors that entry states over them -- and the plan's own, unchanged and the very same object, where it states none (v0.99, docs/domain/position-plans.md §3.3sexies).

    ⚠️ It is **idempotent**, and that is not tidiness: it starts from `sz.drawing`, the plan's own sizes, so asking twice for the same entry gives the same answer rather than the factor squared. Every function here that draws one entry is handed that entry's sizes, while `number_frame` is handed the plan's by Woodcore's canvas and by the export -- so one of the two would have been scaling a scaled number, and a number's box quietly 1.69 times its size is exactly the kind of thing no page says out loud.

    ⚠️ It applies the three the entry states, whatever they are, rather than only those `figure_style.ENTRY_KEYS` allows it: this module draws a draft as it stands (`render` is called on every movement of the mouse), and a factor that names nothing the entry draws scales nothing. `plan.check_source` is what refuses it, once, at the save and at the export.
    """
    own = figure_style.stated(entry or {})
    if not own:
        return sz.drawing
    return sz.drawing.scaled(figure_style.entry_factors(entry))


# --- The symbols ----------------------------------------------------------------------

def colour_of(element):
    """The colour an element's symbol is drawn in: its type's, or for a load symbol its subtype's (LOAD_COLOURS)."""
    if model.is_load(element["type"]):
        return LOAD_COLOURS.get(element.get("subtype") or "vert", ORANGE)
    return COLOURS[element["type"]]


def label_colour_of(element):
    """The colour an element's number and its box are drawn in."""
    if model.is_load(element["type"]):
        return LOAD_LABEL_COLOURS.get(element.get("subtype") or "vert", ORANGE)
    return LABEL_COLOURS.get(element["type"], COLOURS[element["type"]])


def _polyline(out, points, colour, width, dash=None, cap=None, join="round", opacity=None):
    extra = ""
    if dash:
        extra += f' stroke-dasharray="{dash}"'
    if cap:
        extra += f' stroke-linecap="{cap}"'
    if opacity is not None:
        extra += f' stroke-opacity="{_f(opacity)}"'
    out.append(f'<polyline points="{_pts(points)}" fill="none" stroke="{colour}" stroke-width="{_f(width)}" stroke-linejoin="{join}"{extra}/>')


def _dotted(out, points, colour, sz, width=4.6):
    """A row of dots -- a vertically bearing wall: a dash of next to nothing with round ends, one dot per gap."""
    _polyline(out, points, colour, sz.line(width), dash=f"{_f(sz.line(0.02))} {_f(sz.line(7.5))}", cap="round")


def _double(out, points, colour, sz, outer=7.0, core=3.8):
    """Two thin parallel lines -- a bracing wall: a thick coloured line with a white one down its middle."""
    _polyline(out, points, colour, sz.line(outer))
    _polyline(out, points, GROUND, sz.line(core))


def _arrowhead(out, tip, towards, colour, sz):
    d = _unit(towards, tip)
    length, width = sz.line(13), sz.line(9)
    bx, by = tip[0] - d[0] * length, tip[1] - d[1] * length
    px, py = -d[1], d[0]
    out.append(f'<polygon points="{_pts([tip, (bx + px * width / 2, by + py * width / 2), (bx - px * width / 2, by - py * width / 2)])}" fill="{colour}"/>')


def _square(out, point, size, colour, fill=None, stroke=None, stroke_width=0.0, opacity=None, angle=0.0):
    x, y = point
    extra = f' fill-opacity="{_f(opacity)}"' if opacity is not None else ""
    if stroke:
        extra += f' stroke="{stroke}" stroke-width="{_f(stroke_width)}"'
    if angle:   # degrees, clockwise on the drawing, about the square's centre
        extra += f' transform="rotate({_f(angle)} {_f(x)} {_f(y)})"'
    out.append(f'<rect x="{_f(x - size / 2)}" y="{_f(y - size / 2)}" width="{_f(size)}" height="{_f(size)}" fill="{fill or colour}"{extra}/>')


def _segments(out, segments, colour, width):
    for p, q in segments:
        out.append(f'<line x1="{_f(p[0])}" y1="{_f(p[1])}" x2="{_f(q[0])}" y2="{_f(q[1])}" stroke="{colour}" stroke-width="{_f(width)}"/>')


def _cut_at_box(p, q, cx, cy, hw, hh):
    """The parts of segment pq outside the box centred on (cx, cy) with half-sides hw and hh (Liang-Barsky) -- a slab's diagonals broken behind its number."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    t0, t1 = 0.0, 1.0
    for den, num in ((-dx, p[0] - (cx - hw)), (dx, (cx + hw) - p[0]), (-dy, p[1] - (cy - hh)), (dy, (cy + hh) - p[1])):
        if abs(den) < 1e-12:
            if num < 0:
                return [(p, q)]
            continue
        t = num / den
        if den < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
    if t1 <= t0:
        return [(p, q)]
    out = []
    if t0 > 1e-4:
        out.append((p, (p[0] + dx * t0, p[1] + dy * t0)))
    if t1 < 1 - 1e-4:
        out.append(((p[0] + dx * t1, p[1] + dy * t1), q))
    return out


def _label_box(label, sz):
    """The half-sides of a number's box: as wide as its characters, as high as a line of them."""
    return (len(label) * sz.text(7.1) + sz.text(10)) / 2, sz.text(16.5) / 2


def _span_arrow(out, cx, cy, angle, length, sz, colour, head=None):
    """A slab's span: a line in the direction it spans, with half an arrowhead at each end, the two on opposite sides (STE)."""
    a = math.radians(angle)
    dx, dy = math.cos(a), math.sin(a)
    px, py = -dy, dx
    h, side = (sz.line(13) if head is None else head), 0.58
    x1, y1, x2, y2 = cx - dx * length / 2, cy - dy * length / 2, cx + dx * length / 2, cy + dy * length / 2
    width = sz.line(2.4)
    _polyline(out, [(x1, y1), (x2, y2)], colour, width, cap="round")
    _polyline(out, [(x2, y2), (x2 - dx * h + px * h * side, y2 - dy * h + py * h * side)], colour, width, cap="round")
    _polyline(out, [(x1, y1), (x1 + dx * h - px * h * side, y1 + dy * h - py * h * side)], colour, width, cap="round")


def _slab(out, element, points, sz, label, compact=False):
    """A slab: its outline, its diagonals -- both where it forms a diaphragm, one where it does not -- broken behind its number, and the arrow of its span. `compact` fits the arrow inside the outline, for a legend line or a tool's icon."""
    colour = BROWN
    out.append(f'<polygon points="{_pts(points)}" fill="none" stroke="{colour}" stroke-width="{_f(sz.line(2))}" stroke-linejoin="round"/>')
    cx, cy = model.centroid(points)
    x0, y0, x1, y1 = model.bbox(points)
    w, h = x1 - x0, y1 - y0
    scheibe = element.get("subtype", "scheibe") != "normal"
    diagonal = element.get("diagonal", 0) % 2
    if len(points) == 4:
        # a quadrilateral: corner to corner
        pairs = [(points[0], points[2]), (points[1], points[3])]
        segments = pairs if scheibe else [pairs[1] if diagonal else pairs[0]]
    else:
        # any other outline: both diagonals through the centroid, cut to the outline, so they reach its edges however it is shaped
        length = math.hypot(w, h) or 1.0
        d1, d2 = (w / length, h / length), (w / length, -h / length)
        if scheibe:
            segments = model.line_in_polygon((cx, cy), d1, points) + model.line_in_polygon((cx, cy), d2, points)
        else:
            segments = model.line_in_polygon((cx, cy), d2 if diagonal else d1, points)
    frame = number_frame(element, sz) if label else None
    if frame is not None:
        # broken behind the number wherever it is, its own place or where it was moved to
        pad = sz.text(3)
        segments = [part for p, q in segments for part in _cut_at_box(p, q, *frame["at"], frame["hw"] + pad, frame["hh"] + pad)]
    _segments(out, segments, colour, sz.line(1.6))
    span = element.get("span")
    span = model.default_span(points) if span is None else float(span)
    if compact:
        _span_arrow(out, cx, cy, span, 0.5 * (w if abs(math.cos(math.radians(span))) > 0.5 else h), sz, colour, head=0.3 * min(w, h))
        return
    arrow = max(sz.line(50), min(0.5 * min(w, h), 0.85 * max(w, h)))
    a = math.radians(span)
    nx, ny = math.sin(a), -math.cos(a)
    if ny > 0:
        nx, ny = -nx, -ny
    _span_arrow(out, cx + nx * sz.text(24), cy + ny * sz.text(24), span, arrow, sz, colour)


def opening_wedge(points, sz):
    """The black wedge of an opening's symbol, as the four points of a polygon -- or None for an outline of fewer than three corners. For the corner C lying furthest up and right (the largest x − y, y pointing down), its neighbours A (before it) and B (after it), and a thickness t = min(14 text units, 0.18 × the shorter of CA and CB): the points A, C, B, P with P = C + t·(uA + uB), uA and uB the unit vectors from C towards A and B -- two triangles meeting in the corner, a wedge growing from nothing at A to t at C along one edge and shrinking back to nothing at B along the other (v0.114, the engineer's drawing after STE Compact 02)."""
    if len(points) < 3:
        return None
    n = len(points)
    v = max(range(n), key=lambda i: points[i][0] - points[i][1])
    corner, a, b = points[v], points[(v - 1) % n], points[(v + 1) % n]
    t = min(sz.text(14), 0.18 * min(math.dist(corner, a), math.dist(corner, b)))
    ua, ub = _unit(corner, a), _unit(corner, b)
    inner = (corner[0] + t * (ua[0] + ub[0]), corner[1] + t * (ua[1] + ub[1]))
    return [tuple(a), tuple(corner), tuple(b), inner]


def _opening(out, points, sz):
    """An opening: a yellow rectangle with a thin black outline, and a black wedge of two triangles meeting in its top right corner (STE; opening_wedge)."""
    out.append(f'<polygon points="{_pts(points)}" fill="{YELLOW}" fill-opacity="0.92" stroke="{INK}" stroke-width="{_f(sz.line(0.8))}"/>')
    wedge = opening_wedge(points, sz)
    if wedge is not None:
        out.append(f'<polygon points="{_pts(wedge)}" fill="{INK}"/>')


def _concrete(out, element, points, sz):
    if element.get("subtype") == "decke":
        out.append(f'<polygon points="{_pts(points)}" fill="{CONCRETE_DECK}" fill-opacity="0.85" stroke="{GREY}" stroke-width="{_f(sz.line(1))}"/>')
        return
    out.append(f'<polygon points="{_pts(points)}" fill="{CONCRETE}" fill-opacity="0.7" stroke="{MUTED}" stroke-width="{_f(sz.line(1))}"/>')
    # crossed hatching at 45°, cut to the outline
    x0, y0, x1, y1 = model.bbox(points)
    spacing = sz.line(9)
    reach = (x1 - x0) + (y1 - y0)
    segments = []
    for direction in ((1 / math.sqrt(2), -1 / math.sqrt(2)), (1 / math.sqrt(2), 1 / math.sqrt(2))):
        normal = (-direction[1], direction[0])
        count = int(reach / spacing) + 2
        centre = ((x0 + x1) / 2, (y0 + y1) / 2)
        for k in range(-count, count + 1):
            through = (centre[0] + normal[0] * k * spacing, centre[1] + normal[1] * k * spacing)
            segments += model.line_in_polygon(through, direction, points)
    _segments(out, segments, MUTED, sz.line(0.9))


def _end_ticks(out, points, colour, sz):
    """A short stroke across each end of a line load, as STE draws a vertical line load's ends."""
    ticks = []
    for end, inner in ((points[0], points[1]), (points[-1], points[-2])):
        u = _unit(inner, end)
        h = sz.line(7)
        ticks.append(((end[0] - u[1] * h, end[1] + u[0] * h), (end[0] + u[1] * h, end[1] - u[0] * h)))
    _segments(out, ticks, colour, sz.line(2.2))


def _double_arrow(out, p, angle, colour, sz):
    """A horizontal point load's double arrow through its point, along its direction (`angle`, in degrees from the sheet's right, clockwise)."""
    a = math.radians(angle)
    u = (math.cos(a), math.sin(a))
    half = sz.point(18)
    a1, a2 = (p[0] - u[0] * half, p[1] - u[1] * half), (p[0] + u[0] * half, p[1] + u[1] * half)
    _polyline(out, [a1, a2], colour, sz.line(2.4))
    _arrowhead(out, a1, a2, colour, sz)
    _arrowhead(out, a2, a1, colour, sz)


def _load_symbol(out, element, points, sz):
    """One of the load-path plan's six symbols (STE Compact 02 pp. 14-15): a point load -- an orange square (vertical), a violet double arrow with a dot (horizontal), the square on the double arrow (both) -- or a line load -- an orange dotted line with a stroke across each end (vertical), a violet double line (horizontal), the double line with the orange dots in it and the strokes (both)."""
    subtype = element.get("subtype") or "vert"
    if element["type"] == "LL":
        if subtype == "horiz":
            _double(out, points, VIOLET, sz)
            return
        if subtype == "vh":
            _double(out, points, VIOLET, sz, 11, 7)
        _dotted(out, points, ORANGE, sz)
        _end_ticks(out, points, ORANGE, sz)
        return
    p = points[0]
    if subtype in ("horiz", "vh"):
        _double_arrow(out, p, float(element.get("angle", 0) or 0), VIOLET, sz)
    if subtype == "horiz":
        out.append(f'<circle cx="{_f(p[0])}" cy="{_f(p[1])}" r="{_f(sz.point(3))}" fill="{VIOLET}"/>')
    else:
        _square(out, p, sz.point(10), ORANGE)


def _symbol(out, element, sz, label="", compact=False):
    """One element's symbol, without its number. `sz` is **that element's own** sizes (`entry_sizes`), which it passes on to `_slab`, `_opening` and `_concrete`. `compact` is a legend line's or a tool's: a slab's span arrow kept inside its outline, and there the sizes are the swatch's rather than any plan's."""
    type_, points = element["type"], [tuple(p) for p in element["points"]]
    kind = model.element_kind(element)
    if model.is_load(type_):
        _load_symbol(out, element, points, sz)
        return
    colour = COLOURS[type_]
    if kind == "line":
        if type_ == "V":
            _dotted(out, points, colour, sz)
        elif type_ == "W":
            _double(out, points, VIOLET, sz, 11, 7)
            _dotted(out, points, ORANGE, sz)
        elif type_ == "H":
            _double(out, points, colour, sz)
        elif type_ in ("T", "A"):
            _polyline(out, points, colour, sz.line(2.4))
            if type_ == "T":
                _arrowhead(out, points[0], points[1], colour, sz)
                _arrowhead(out, points[-1], points[-2], colour, sz)
            else:
                for p in (points[0], points[-1]):
                    out.append(f'<circle cx="{_f(p[0])}" cy="{_f(p[1])}" r="{_f(sz.point(4))}" fill="{colour}"/>')
        elif type_ == "M":
            subtype = element.get("subtype", "vert")
            if subtype == "vh":
                _double(out, points, colour, sz, 10, 5.8)
                _dotted(out, points, colour, sz, 4)
            elif subtype == "horiz":
                _double(out, points, colour, sz)
            else:
                _dotted(out, points, colour, sz, 4.2)
        elif type_ == "L":
            _polyline(out, points, colour, sz.line(5.5), dash=f"{_f(sz.line(10))} {_f(sz.line(8))}", join="miter")
    elif kind == "poly":
        if type_ == "D":
            _slab(out, element, points, sz, label, compact)
        elif type_ == "Ö":
            _opening(out, points, sz)
        elif type_ == "B":
            _concrete(out, element, points, sz)
    else:
        p = points[0]
        if type_ in ("S", "M"):
            _square(out, p, sz.point(12), colour, angle=element.get("angle") or 0.0)   # turned about its centre (source 1.4)
        elif type_ == "L":
            s = sz.point(14)
            _square(out, p, s, colour, fill=GROUND, stroke=colour, stroke_width=sz.line(2), opacity=0.7)
            _segments(out, [((p[0] - s / 2, p[1]), (p[0] + s / 2, p[1])), ((p[0], p[1] - s / 2), (p[0], p[1] + s / 2))], colour, sz.line(1.5))


def _midpoint(points):
    """The middle of a polyline, and the angle its text is read at there -- never upside down."""
    half = model.polyline_length(points) / 2
    acc = 0.0
    for i in range(1, len(points)):
        d = math.dist(points[i - 1], points[i])
        if acc + d >= half or i == len(points) - 1:
            t = (half - acc) / d if d else 0.0
            x = points[i - 1][0] + (points[i][0] - points[i - 1][0]) * t
            y = points[i - 1][1] + (points[i][1] - points[i - 1][1]) * t
            angle = math.degrees(math.atan2(points[i][1] - points[i - 1][1], points[i][0] - points[i - 1][0]))
            if angle > 90:
                angle -= 180
            if angle <= -90:
                angle += 180
            return (x, y), angle, _unit(points[i - 1], points[i])
        acc += d
    return tuple(points[0]), 0.0, (1.0, 0.0)


def _text(out, point, content, size, colour, anchor="middle", bold=False, rotate=None, halo=None):
    """A text, centred on `point` vertically as well -- SVG Tiny has no dominant-baseline, so it is lowered by a third of its size. `halo` draws it first in white, `halo` wide, so it reads over the plan."""
    weight = ' font-weight="bold"' if bold else ""
    x, y = point
    transform = f' transform="translate({_f(x)},{_f(y)}) rotate({_f(rotate)})"' if rotate else ""
    tx, ty = (0.0, 0.35 * size) if rotate else (x, y + 0.35 * size)
    body = escape(content)
    common = f'x="{_f(tx)}" y="{_f(ty)}" font-family="{FONT}" font-size="{_f(size)}" text-anchor="{anchor}"{weight}{transform}'
    if halo:
        out.append(f'<text {common} fill="{GROUND}" stroke="{GROUND}" stroke-width="{_f(halo)}" stroke-linejoin="round">{body}</text>')
    out.append(f'<text {common} fill="{colour}">{body}</text>')


# --- The position numbers ----------------------------------------------------------------

def label_offset(element):
    """How far the engineer moved an element's number from its own place, (dx, dy) in sheet units -- (0, 0) for one left where it is drawn by itself."""
    offset = element.get("label_offset")
    if not offset:
        return (0.0, 0.0)
    return (float(offset[0]), float(offset[1]))


def number_frame(element, sz):
    """Where an element's position number is drawn, or None for an element without one: `at`, the centre of its box, whose half-sides are `hw` along the text and `hh` across it; `angle`, the angle the text is read at; `home`, its own place -- along a line at its middle, at the centre of an area, above a point --, which `at` is moved from by the element's label_offset; `moved`, whether it was; `along`, the line's direction at its middle, which an Auflager's square beside its number follows. What _number draws, Woodcore's window grabs and the export frames a detail round, from this one computation.

    ⚠️ **It applies the element's own factors itself** (`entry_sizes`, v0.99), so `sz` may be the plan's sizes or the element's and the answer is the same. That is what keeps the three places this is asked from in step without a line of their own: Woodcore's canvas hit-tests a click on a number with `sizes_of(self.source)` (plan_canvas.py), `plan.warnings` and `plan.build_record`'s `label_at` ask with the plan's too, and `_number`, `_leader` and `_slab` ask with the element's while they draw it.
    """
    label = element.get("label", "")
    points = [tuple(p) for p in element.get("points") or []]
    if not label or len(points) < model.MIN_POINTS[model.element_kind(element)]:
        return None
    sz = entry_sizes(sz, element)
    kind = model.element_kind(element)
    hw, hh = _label_box(label, sz)
    if kind == "line":
        home, angle, along = _midpoint(points)
    elif kind == "poly":
        home, angle, along = model.centroid(points), 0.0, (1.0, 0.0)
    elif model.is_load(element["type"]):
        # a point load's number stands above and to the right of it, a dotted line back to it (STE p. 14; _load_leader)
        home, angle, along = (points[0][0] + hw + sz.point(8), points[0][1] - sz.point(12) - hh), 0.0, (1.0, 0.0)
    else:
        home, angle, along = (points[0][0], points[0][1] - sz.point(14) - hh), 0.0, (1.0, 0.0)
    dx, dy = label_offset(element)
    return {"at": (home[0] + dx, home[1] + dy), "home": home, "moved": bool(dx or dy),
            "angle": angle, "along": along, "hw": hw, "hh": hh}


def number_frames(source):
    """Every position number a plan draws, in the order it draws them, the last one on top: [(index of the element, its frame)]. Each at the element's own size, `number_frame` reading its factors off the element it is given."""
    sz = sizes_of(source)
    order = sorted(enumerate(source.get("elements", [])), key=lambda item: (model.TYPES[item[1]["type"]]["z"], item[0]))
    frames = []
    for index, element in order:
        frame = number_frame(element, sz)
        if frame is not None:
            frames.append((index, frame))
    return frames


def on_number(frame, point, margin=0.0):
    """Whether `point` lies on a number's box, or within `margin` of it."""
    x, y = _local(frame, point)
    return abs(x) <= frame["hw"] + margin and abs(y) <= frame["hh"] + margin


number_corners = dimension.box_corners   # (ARCH-004: one copy)


def _leader(out, element, sz):
    """A thin line from a number the engineer moved clear of its symbol to the nearest point of the symbol, ending on a dot there, so the number still says which element it names. Drawn only once the number has left its symbol -- further from it than its box is high, or than a column's number sits above the column by itself: a number moved along its beam, or just beside it, needs none."""
    frame = number_frame(element, sz)
    if frame is None or not frame["moved"]:
        return
    kind = model.element_kind(element)
    target, distance = model.nearest_point(element, frame["at"])
    if distance == 0:
        return  # on its line, or inside its area
    x, y = _local(frame, target)
    hw, hh = frame["hw"], frame["hh"]
    gap = math.hypot(max(abs(x) - hw, 0.0), max(abs(y) - hh, 0.0))
    if gap <= max(2 * hh, sz.point(14) if kind == "point" else 0.0):
        return
    # the line leaves the box where the way to the target crosses its edge
    s = min(hw / abs(x) if abs(x) > 1e-12 else math.inf, hh / abs(y) if abs(y) > 1e-12 else math.inf)
    a = math.radians(frame["angle"])
    u, v = x * s, y * s
    start = (frame["at"][0] + u * math.cos(a) - v * math.sin(a), frame["at"][1] + u * math.sin(a) + v * math.cos(a))
    colour = label_colour_of(element)
    _segments(out, [(start, target)], colour, sz.line(1))
    if kind != "point":
        # a column is its own mark; a line or an area gets a dot where the leader meets it
        out.append(f'<circle cx="{_f(target[0])}" cy="{_f(target[1])}" r="{_f(sz.line(2))}" fill="{colour}"/>')


def _load_leader(out, element, sz):
    """The dotted line from a point load's number back to its point, always drawn (STE p. 14): from the edge of the number's box nearest the point."""
    frame = number_frame(element, sz)
    if frame is None:
        return
    p = tuple(element["points"][0])
    (cx, cy), hw, hh = frame["at"], frame["hw"], frame["hh"]
    q = (min(max(p[0], cx - hw), cx + hw), min(max(p[1], cy - hh), cy + hh))
    if math.dist(q, p) <= sz.point(6):
        return
    _polyline(out, [q, p], label_colour_of(element), sz.line(1.2), dash=f"{_f(sz.line(0.02))} {_f(sz.line(3))}", cap="round")


def _number(out, element, sz, flagged=False):
    """An element's position number, in its box, where number_frame puts it: its own place, or where the engineer moved it."""
    frame = number_frame(element, sz)
    if frame is None:
        return
    label, type_ = element["label"], element["type"]
    colour = COLOURS[type_]
    text_colour = label_colour_of(element)
    border = FLAG_COLOUR if flagged else text_colour
    at, angle, hw, hh = frame["at"], frame["angle"], frame["hw"], frame["hh"]
    rx = hh if type_ in STADIUM else sz.text(3)
    rotate = f' transform="translate({_f(at[0])},{_f(at[1])}) rotate({_f(angle)})"' if angle else ""
    ox, oy = (0.0, 0.0) if angle else at
    out.append(f'<rect x="{_f(ox - hw)}" y="{_f(oy - hh)}" width="{_f(2 * hw)}" height="{_f(2 * hh)}" rx="{_f(rx)}" ry="{_f(rx)}" fill="{GROUND}" stroke="{border}" stroke-width="{_f(sz.text(1.6))}"{rotate}/>')
    _text(out, at, label, sz.text(11.2), text_colour, bold=True, rotate=angle or None)
    if type_ == "M" and model.element_kind(element) == "line":
        # a green square beside the number, as in the legend
        off = hw + sz.text(10)
        direction = frame["along"]
        _square(out, (at[0] + direction[0] * off, at[1] + direction[1] * off), sz.point(9.5), colour)


def _length(out, element, sz, per_m):
    points = [tuple(p) for p in element["points"]]
    at, angle, _direction = _midpoint(points)
    length = model.element_length_m(element, per_m)
    a = math.radians(angle)
    offset = sz.text(20)
    # below the number, on the side the text reads from
    point = (at[0] - math.sin(a) * offset, at[1] + math.cos(a) * offset)
    _text(out, point, model.metres_text(length), sz.text(9.5), COLOURS[element["type"]], rotate=angle or None, halo=sz.text(3))


def _side_lengths(out, element, sz, per_m):
    """A slab's length written along each of its sides, outside it (the engineer: «longueur de chaque côté de dale»)."""
    points = [tuple(p) for p in element["points"]]
    centre = model.centroid(points)
    colour = COLOURS[element["type"]]
    for i in range(len(points)):
        p, q = points[i], points[(i + 1) % len(points)]
        length = model.distance_m(p, q, per_m)
        if length <= 0:
            continue
        mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
        angle = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
        normal = (-(q[1] - p[1]), q[0] - p[0])
        size = math.hypot(*normal) or 1.0
        normal = (normal[0] / size, normal[1] / size)
        if (mid[0] - centre[0]) * normal[0] + (mid[1] - centre[1]) * normal[1] < 0:
            normal = (-normal[0], -normal[1])   # outward
        if angle > 90:
            angle -= 180
        elif angle < -90:
            angle += 180
        offset = sz.text(12)
        _text(out, (mid[0] + normal[0] * offset, mid[1] + normal[1] * offset), model.metres_text(length), sz.text(9.5), colour, rotate=angle or None, halo=sz.text(3))


def _axes(out, source, crop, plan_sz):
    """Every axis, each at its own sizes: a dash-dot line, and the bubble its name is set in, whose radius is already a `text`."""
    for axis in source.get("axes", []):
        segment = model.axis_segment(axis, crop)
        if segment is None:
            continue
        sz = entry_sizes(plan_sz, axis)
        a, b = segment
        u = _unit(a, b)
        radius = sz.text(8.5)
        bubbles = axis.get("bubbles", "both")
        start = bubbles in ("both", "start")
        end = bubbles in ("both", "end")
        # the bubbles sit inside the frame, at its edge; the line runs from bubble to bubble
        margin = sz.text(3)
        ca = (a[0] + u[0] * (radius + margin), a[1] + u[1] * (radius + margin))
        cb = (b[0] - u[0] * (radius + margin), b[1] - u[1] * (radius + margin))
        la = (ca[0] + u[0] * radius, ca[1] + u[1] * radius) if start else a
        lb = (cb[0] - u[0] * radius, cb[1] - u[1] * radius) if end else b
        if math.dist(la, lb) > 1e-9 and ((lb[0] - la[0]) * u[0] + (lb[1] - la[1]) * u[1]) > 0:
            dash = f"{_f(sz.line(14))} {_f(sz.line(3))} {_f(sz.line(1.5))} {_f(sz.line(3))}"
            _polyline(out, [la, lb], AXIS_COLOUR, sz.line(0.8), dash=dash, join="miter")
        for show, centre in ((start, ca), (end, cb)):
            if show:
                out.append(f'<circle cx="{_f(centre[0])}" cy="{_f(centre[1])}" r="{_f(radius)}" fill="{GROUND}" stroke="{AXIS_COLOUR}" stroke-width="{_f(sz.line(1))}"/>')
                _text(out, centre, axis["label"], sz.text(10), AXIS_COLOUR, bold=True)


def storey_bubble(storey, sz):
    """The half-sides of a storey line's bubble: a stadium as wide as its designation, which may be long («Mezzanine»), and as high as an axis's bubble."""
    hh = sz.text(8.5)
    return max(hh, (len(storey) * sz.text(6.2) + sz.text(8)) / 2), hh


def _storeys(out, source, sz):
    """A section's storey lines: each a dash-dot line between its two points, with the storey's designation in a rounded bubble at **both** ends, inside them, the line running from bubble to bubble -- an axis's arrangement, and no label in the middle. The bubbles are read along the line, never upside down. A section's storey boxes are not drawn: show-plan draws the one a sheet highlights."""
    for line in source.get("storey_lines") or []:
        points = line.get("points") or []
        if len(points) != 2 or math.dist(points[0], points[1]) <= 1e-9:
            continue
        a, b = tuple(points[0]), tuple(points[1])
        u = _unit(a, b)
        storey = str(line.get("storey", ""))
        hw, hh = storey_bubble(storey, sz)
        angle = math.degrees(math.atan2(u[1], u[0]))
        if angle > 90:
            angle -= 180
        elif angle <= -90:
            angle += 180
        ca = (a[0] + u[0] * hw, a[1] + u[1] * hw)
        cb = (b[0] - u[0] * hw, b[1] - u[1] * hw)
        la = (ca[0] + u[0] * hw, ca[1] + u[1] * hw)
        lb = (cb[0] - u[0] * hw, cb[1] - u[1] * hw)
        if ((lb[0] - la[0]) * u[0] + (lb[1] - la[1]) * u[1]) > 0:
            dash = f"{_f(sz.line(14))} {_f(sz.line(3))} {_f(sz.line(1.5))} {_f(sz.line(3))}"
            _polyline(out, [la, lb], STOREY_COLOUR, sz.line(0.8), dash=dash, join="miter")
        for centre in (ca, cb):
            rotate = f' transform="translate({_f(centre[0])},{_f(centre[1])}) rotate({_f(angle)})"' if angle else ""
            ox, oy = (0.0, 0.0) if angle else centre
            out.append(f'<rect x="{_f(ox - hw)}" y="{_f(oy - hh)}" width="{_f(2 * hw)}" height="{_f(2 * hh)}" rx="{_f(hh)}" ry="{_f(hh)}" fill="{GROUND}" stroke="{STOREY_COLOUR}" stroke-width="{_f(sz.line(1))}"{rotate}/>')
            _text(out, centre, storey, sz.text(10), STOREY_COLOUR, bold=True, rotate=angle or None)


def _labelled_box(out, centre, text, sz, colour, size=10.0, fill=GROUND):
    """A text in a rectangle of its own, centred on `centre`: a storey box's designation."""
    hw, hh = (len(text) * sz.text(0.62 * size) + sz.text(8)) / 2, sz.text(0.85 * size)
    out.append(f'<rect x="{_f(centre[0] - hw)}" y="{_f(centre[1] - hh)}" width="{_f(2 * hw)}" height="{_f(2 * hh)}" fill="{fill}" stroke="{colour}" stroke-width="{_f(sz.line(1))}"/>')
    _text(out, centre, text, sz.text(size), colour, bold=True)


def _storey_boxes(out, source, sz):
    """A section's storey boxes, each its STE designation -- «x» + the storey's numbering character + «xx», x1xx -- in a box at its middle (STE Compact 02 p. 12; plan.storey_designation). The box itself is not drawn: a sheet highlights the one its floor plan shows (lib/sheet.typ's sheet-section)."""
    boxes = source.get("storey_boxes") or []
    for box in boxes:
        try:
            centre = (float(box["x"]) + float(box["w"]) / 2, float(box["y"]) + float(box["h"]) / 2)
        except (KeyError, TypeError, ValueError):
            continue
        _labelled_box(out, centre, model.storey_designation(box, boxes), sz, STOREY_COLOUR)


def load_level_text(level, siblings=(), lang="de"):
    """What a load transfer level writes beside itself: «Niveau de reprise des charges (x0xx)» in `lang`, the designation made of its storey's numbering character (plan.storey_designation)."""
    from i18n import strings  # the engine's words, which a figure has to be drawn to measure
    return f"{strings.text('plan.load_level', lang)} ({model.storey_designation(level, siblings)})"


def load_level_frame(level, sz, siblings=(), lang="de"):
    """Where a load transfer level's words are drawn, as number_frame says it of a position number: `at` the centre of their box, `hw`/`hh` its half-sides, `home` their own place -- above the line's left end, ending left of it --, which `at` is moved from by the level's label_offset; `moved`, whether it was; `text`, the words. None for a level without its two points."""
    points = [tuple(q) for q in level.get("points") or []]
    if len(points) != 2:
        return None
    text = load_level_text(level, siblings, lang)
    size = sz.text(9.5)
    hw, hh = len(text) * 0.27 * size + sz.text(3), 0.7 * size
    left = min(points, key=lambda q: q[0])
    home = (left[0] - sz.text(6) - hw, left[1] - sz.text(16))
    offset = level.get("label_offset") or (0, 0)
    dx, dy = float(offset[0]), float(offset[1])
    return {"at": (home[0] + dx, home[1] + dy), "home": home, "moved": bool(dx or dy), "angle": 0.0, "hw": hw, "hh": hh, "text": text}


def _load_levels(out, source, sz, lang):
    """A section's load transfer levels: each a red dash-dot line between its two points, a red arrow coming down onto each end, and its words beside it -- with a thin line back to the level once they were moved clear of it."""
    boxes = source.get("storey_boxes") or []
    for level in source.get("load_levels") or []:
        points = [tuple(q) for q in level.get("points") or []]
        if len(points) != 2 or math.dist(points[0], points[1]) <= 1e-9:
            continue
        dash = f"{_f(sz.line(14))} {_f(sz.line(3))} {_f(sz.line(1.5))} {_f(sz.line(3))}"
        _polyline(out, points, LOAD_LEVEL_COLOUR, sz.line(1.6), dash=dash, join="miter")
        length = sz.text(20)
        for p in points:
            top = (p[0], p[1] - length)
            _polyline(out, [top, p], LOAD_LEVEL_COLOUR, sz.line(1.4))
            _arrowhead(out, p, top, LOAD_LEVEL_COLOUR, sz)
        frame = load_level_frame(level, sz, boxes, lang)
        if frame is None:
            continue
        if frame["moved"]:
            _distance, target = model._point_segment(frame["at"], points[0], points[1])
            (cx, cy), hw, hh = frame["at"], frame["hw"], frame["hh"]
            x, y = target[0] - cx, target[1] - cy
            gap = math.hypot(max(abs(x) - hw, 0.0), max(abs(y) - hh, 0.0))
            if gap > 2 * hh:
                s = min(hw / abs(x) if abs(x) > 1e-12 else math.inf, hh / abs(y) if abs(y) > 1e-12 else math.inf)
                _segments(out, [((cx + x * s, cy + y * s), target)], LOAD_LEVEL_COLOUR, sz.line(1))
        _text(out, frame["at"], frame["text"], sz.text(9.5), LOAD_LEVEL_COLOUR, halo=sz.text(3))


def render(source, window=None, flagged=(), lang="de", values=None, centres=False):
    """The plan's symbols as an SVG document over `window` ({x, y, w, h} in sheet units): the frame the report shows (the export) or the whole sheet (Woodcore's window, which also passes `flagged`, labels to outline in red -- unknown to Positionen.xlsx, or drawn twice). Sizes are always those of the report's frame, so Woodcore shows the symbols at the size they will be printed at. `source` needs only its sheet, crop, style, scale, show_lengths, axes and elements; `background` decides whether the veil is drawn.

    `values` are the export's, which a text's variables print (issue #43, figure_text); without them a text prints its variables' last values.

    `centres` asks for the stiffness centre S, the mass centre M and the building's outline (issue #54): Woodcore's window always does, the export where the plan says so (`print_centres`), and nothing else -- another plan shown over the open one is drawn without its own. Without it, and on a plan that has none of the three, the drawing is byte for byte the one this module wrote before.

    `lang` is the language of the engine's words a section's load transfer levels write (v0.116) -- the one drawing that carries any: a plan without one is drawn alike in every language.

    Every element and every axis is drawn at **its own** sizes since v0.99 -- the plan's three times the factors that entry states over them -- and a plan on which nothing states one is drawn with the plan's own sizes, the same object throughout, so its SVG is byte for byte the one this module wrote before (`entry_sizes`).
    """
    crop = model.crop_of(source)
    window = window or crop
    sz = Sizes(base_unit(crop), source.get("style", {}))
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="{_f(window["x"])} {_f(window["y"])} {_f(window["w"])} {_f(window["h"])}" '
        f'width="{_f(window["w"])}" height="{_f(window["h"])}">',
    ]
    background = source.get("background")
    if background is not None:
        veil = 1.0 - float(background.get("opacity", model.DEFAULT_OPACITY))
        if veil > 0:
            out.append(f'<rect x="{_f(window["x"])}" y="{_f(window["y"])}" width="{_f(window["w"])}" height="{_f(window["h"])}" fill="{GROUND}" fill-opacity="{_f(veil)}"/>')
    out.append(HIGHLIGHT_MARK)
    out.append(AXES_OPEN)
    _axes(out, source, crop, sz)
    out.append(AXES_CLOSE)
    if source.get("storey_lines"):
        out.append(STOREYS_OPEN)
        _storeys(out, source, sz)
        out.append(STOREYS_CLOSE)
    if source.get("storey_boxes"):
        out.append(BOXES_OPEN)
        _storey_boxes(out, source, sz)
        out.append(BOXES_CLOSE)
    if source.get("load_levels"):
        out.append(LEVELS_OPEN)
        _load_levels(out, source, sz, lang)
        out.append(LEVELS_CLOSE)
    _dimensions(out, source, sz)
    found = plan_centres.state(source) if centres else None
    if found and found["outline"]:
        # the building's outline under every symbol, so that a wall drawn along it stays the wall
        out.append(CENTRES_OPEN)
        _outline(out, found["outline"], sz)
        out.append(CENTRES_CLOSE)

    elements = list(enumerate(source.get("elements", [])))
    elements.sort(key=lambda item: (model.TYPES[item[1]["type"]]["z"], item[0]))
    per_m = model.units_per_m(source)
    # every element at its own sizes: the plan's three times the factors it states over them, which is `sz` itself where it states none (entry_sizes)
    for index, element in elements:
        if not element.get("points") or len(element["points"]) < model.MIN_POINTS[model.element_kind(element)]:
            continue
        out.append(f'<g id="el-{index + 1}">')
        _symbol(out, element, entry_sizes(sz, element), element.get("label", ""))
        out.append("</g>")
    # the leaders of the numbers moved clear of their symbols, under every number, so that none crosses a box
    for index, element in elements:
        if element["type"] == "PL":
            _load_leader(out, element, entry_sizes(sz, element))  # a point load's number always has its dotted line (STE)
        elif element.get("label_offset"):
            _leader(out, element, entry_sizes(sz, element))
    # the numbers above every symbol, so no wall runs across another's box
    for index, element in elements:
        if not element.get("points") or len(element["points"]) < model.MIN_POINTS[model.element_kind(element)]:
            continue
        _number(out, element, entry_sizes(sz, element), flagged=element.get("label", "") in flagged)
    # the lengths beside the walls, the beams and the slabs, between markers `show-plan(lengths: false)` takes out (issue #9) -- written only where a length is drawn
    lengths = []
    for index, element in elements:
        if not element.get("points") or len(element["points"]) < model.MIN_POINTS[model.element_kind(element)]:
            continue
        if model.shows_length(source, element):   # the plan's `show_lengths`, or the element's own `show_length` (source 1.4)
            if model.element_kind(element) == "line":
                _length(lengths, element, entry_sizes(sz, element), per_m)
            elif model.element_kind(element) == "poly":
                _side_lengths(lengths, element, entry_sizes(sz, element), per_m)
    if lengths:
        out += [LENGTHS_OPEN, *lengths, LENGTHS_CLOSE]
    if found and (found["mass"] or found["stiffness"]):
        # the two centres over every symbol and number: M first, so that an S that falls on it -- the bracing laid out symmetrically -- rings it rather than hides it
        out.append(CENTRES_OPEN)
        if found["mass"]:
            _mass_mark(out, found["mass"]["point"], sz)
        if found["stiffness"]:
            _stiffness_mark(out, found["stiffness"]["point"], sz)
        out.append(CENTRES_CLOSE)
    draw_texts(out, source, sz, values)
    out.append("</svg>")
    return "\n".join(out) + "\n"


# --- The stiffness centre, the mass centre and the outline (issue #54) -------------------------

# The two marks, in the plan's point unit, and their letters in its text unit: M a disc of this radius, S a ring wide enough to hold it with a cross reaching past the ring.
MASS_RADIUS = 7.0
STIFFNESS_RADIUS = 10.5
STIFFNESS_REACH = 1.45
CENTRE_LETTER = 12.0


def _outline(out, points, sz):
    """The building's outline: a thin broken line through its corners and back to the first -- broken, where an axis is dash-dot and a wall a full stroke."""
    ring = [*points, points[0]]
    _polyline(out, ring, OUTLINE_COLOUR, sz.line(1.2), dash=f"{_f(sz.line(10))} {_f(sz.line(6))}", join="miter")


def _mass_mark(out, point, sz, letter=True):
    """The mass centre: the centre-of-gravity mark, a disc quartered with two opposite quarters full, and its letter M below and to its left -- the side S's letter is not on, so the two read where the two centres fall on one point."""
    x, y = point
    r = sz.point(MASS_RADIUS)
    out.append(f'<circle cx="{_f(x)}" cy="{_f(y)}" r="{_f(r)}" fill="{GROUND}" stroke="{GROUND}" stroke-width="{_f(sz.line(3.4))}"/>')
    for start in (0.0, 180.0):
        # a quarter as a fan of short chords: SVG Tiny has no arc both renderers read alike (_angle_dimension)
        fan = [(x + r * math.cos(math.radians(start + 15 * k)), y + r * math.sin(math.radians(start + 15 * k))) for k in range(7)]
        out.append(f'<polygon points="{_pts([(x, y), *fan])}" fill="{MASS_COLOUR}"/>')
    out.append(f'<circle cx="{_f(x)}" cy="{_f(y)}" r="{_f(r)}" fill="none" stroke="{MASS_COLOUR}" stroke-width="{_f(sz.line(1.3))}"/>')
    if letter:
        size = sz.text(CENTRE_LETTER)
        _text(out, (x - r - 0.55 * size, y + r + 0.45 * size), "M", size, MASS_COLOUR, bold=True, halo=0.3 * size)


def _stiffness_mark(out, point, sz, letter=True):
    """The stiffness centre: a ring crossed by a cross that reaches past it, in the bracing walls' colour, and its letter S above and to its right. The ring is not filled: an M inside it shows."""
    x, y = point
    r = sz.point(STIFFNESS_RADIUS)
    reach = STIFFNESS_REACH * r
    cross = (((x - reach, y), (x + reach, y)), ((x, y - reach), (x, y + reach)))
    for colour, width in ((GROUND, sz.line(3.6)), (STIFFNESS_COLOUR, sz.line(1.5))):
        out.append(f'<circle cx="{_f(x)}" cy="{_f(y)}" r="{_f(r)}" fill="none" stroke="{colour}" stroke-width="{_f(width)}"/>')
        _segments(out, cross, colour, width)
    if letter:
        size = sz.text(CENTRE_LETTER)
        _text(out, (x + r + 0.55 * size, y - r - 0.45 * size), "S", size, STIFFNESS_COLOUR, bold=True, halo=0.3 * size)


def centre_keys(source):
    """The legend lines of what a plan prints of its centres (`print_centres`), each only where it is drawn: S, M, the outline -- none on a plan that prints none, which is then exported as it was."""
    if not source.get("print_centres"):
        return ()
    found = plan_centres.state(source)
    there = {"Steifigkeitszentrum": found["stiffness"], "Massenzentrum": found["mass"], "Umriss": found["outline"]}
    return tuple(key for key in CENTRE_KEYS if there[key])


# --- The texts (issue #43) -------------------------------------------------------------------

# A text's size, in the plan's text unit: a position number's (`_number`), so a note reads as the plan's own lettering.
TEXT_SIZE = 11.2
TEXT_COLOUR = INK


def text_frames(source, values=None, sz=None):
    """Every text of a drawing as it is drawn: [(index, centre, half-width, half-height, lines, size)] in sheet units -- what `_texts` draws and what Woodcore hits a text by. A plan's and a fire-protection plan's alike, both holding `texts` as `{points: [[x, y]], text, vars?, style?}`."""
    sz = sz or Sizes(base_unit(model.crop_of(source)), source.get("style", {}))
    out = []
    for i, text in enumerate(source.get("texts") or []):
        size = entry_sizes(sz, text).text(TEXT_SIZE)
        printed = figure_text.lines(text, values or {}) or [""]
        hw, hh = figure_text.box(printed, size)
        x, y = text["points"][0]
        out.append((i, (float(x), float(y)), hw, hh, printed, size))
    return out


def hit_text(source, point, tolerance=0.0, values=None):
    """The index of the text whose box lies under `point`, the last drawn first, or None."""
    for i, (x, y), hw, hh, _lines, _size in reversed(text_frames(source, values)):
        if abs(point[0] - x) <= hw + tolerance and abs(point[1] - y) <= hh + tolerance:
            return i
    return None


def draw_texts(out, source, sz, values):
    """The texts placed with the Text tool, over everything else: figure_text sets them, with a white halo so they read over the plan. Written only where the drawing has one, so a plan without is drawn as before. A fire-protection plan's are drawn by this too (fire_svg.render)."""
    for _i, at, _hw, _hh, printed, size in text_frames(source, values, sz):
        figure_text.draw(out, at, printed, size, TEXT_COLOUR, halo=0.3 * size)


# --- The dimensions (issue #9) ------------------------------------------------------------

def _dimensions(out, source, sz):
    """Every dimension the plan draws, between DIMENSIONS_OPEN and DIMENSIONS_CLOSE -- the markers written only where there is one to draw (plan.dimension_parts gives none for a length on a plan with no scale)."""
    drawn = [(dim, model.dimension_parts(source, dim)) for dim in source.get("dimensions") or []]
    drawn = [(dim, parts) for dim, parts in drawn if parts]
    if not drawn:
        return
    out.append(DIMENSIONS_OPEN)
    for dim, parts in drawn:
        dsz = entry_sizes(sz, dim)
        for part in parts:
            if "radius" in part:
                _angle_dimension(out, part, dsz)
            else:
                _linear_dimension(out, part, dsz)
    out.append(DIMENSIONS_CLOSE)


def _tick(out, at, u, sz):
    """The architect's tick at the end of a dimension line: a short stroke at 45° across it."""
    size = sz.point(4.0)
    d = ((u[0] - u[1]) / math.sqrt(2.0), (u[1] + u[0]) / math.sqrt(2.0))
    _polyline(out, [(at[0] - d[0] * size, at[1] - d[1] * size), (at[0] + d[0] * size, at[1] + d[1] * size)], DIMENSION_COLOUR, sz.line(1.1), cap="butt")


def _linear_dimension(out, part, sz):
    """One length: a witness line from each end to the dimension line, the line with a tick at each end, and the value above it, turned with it so it reads from below or from the right."""
    (a, b), (p, q) = part["ends"], part["line"]
    width = sz.line(0.6)
    for end, foot in ((a, p), (b, q)):
        reach = math.dist(end, foot)
        if reach > 1e-9:
            d = ((foot[0] - end[0]) / reach, (foot[1] - end[1]) / reach)
            gap = min(sz.point(2.0), 0.5 * reach)
            _polyline(out, [(end[0] + d[0] * gap, end[1] + d[1] * gap), (foot[0] + d[0] * sz.point(2.0), foot[1] + d[1] * sz.point(2.0))], DIMENSION_COLOUR, width, cap="butt")
    length = math.dist(p, q)
    if length <= 1e-9:
        return
    _polyline(out, [p, q], DIMENSION_COLOUR, width, cap="butt")
    u = ((q[0] - p[0]) / length, (q[1] - p[1]) / length)
    _tick(out, p, u, sz)
    _tick(out, q, u, sz)
    angle = math.degrees(math.atan2(u[1], u[0]))
    if angle > 90:
        angle -= 180
    elif angle <= -90:
        angle += 180
    a_rad = math.radians(angle)
    lift = sz.text(6.5)
    mid = ((p[0] + q[0]) / 2 + math.sin(a_rad) * lift, (p[1] + q[1]) / 2 - math.cos(a_rad) * lift)
    _text(out, mid, model.dimension_value_text(part), sz.text(9.5), DIMENSION_COLOUR, rotate=angle or None, halo=sz.text(3))


def _angle_dimension(out, part, sz):
    """One angle: the arc between its two sides, sampled as a polyline -- SVG Tiny has no arc --, a tick at each end and the value outside its middle."""
    (cx, cy), r = part["centre"], part["radius"]
    start, sweep = math.radians(part["start"]), math.radians(part["sweep"])
    steps = max(8, int(abs(part["sweep"]) / 6))
    arc = [(cx + r * math.cos(start + sweep * k / steps), cy + r * math.sin(start + sweep * k / steps)) for k in range(steps + 1)]
    _polyline(out, arc, DIMENSION_COLOUR, sz.line(0.6))
    for tip, before in ((arc[0], arc[1]), (arc[-1], arc[-2])):
        length = math.dist(tip, before)
        if length > 1e-9:
            _tick(out, tip, ((tip[0] - before[0]) / length, (tip[1] - before[1]) / length), sz)
    middle = start + sweep / 2
    reach = r + sz.text(9)
    _text(out, (cx + reach * math.cos(middle), cy + reach * math.sin(middle)), model.dimension_value_text(part), sz.text(9.5), DIMENSION_COLOUR, halo=sz.text(3))


# --- The legend and the tools' icons -------------------------------------------------

def legend_keys(source):
    """The legend lines a plan needs: the symbols it uses, and «Achse» when it has axes."""
    keys = {model.legend_key(element) for element in source.get("elements", [])}
    if source.get("axes"):
        keys.add("Achse")
    if source.get("load_levels"):
        keys.add("Lastniveau")
    keys.update(centre_keys(source))   # the stiffness centre, the mass centre and the outline, where the plan prints them (issue #54)
    return keys


def _sample(key, width, height):
    """An element of the symbol a legend line or a tool shows, laid out in a width × height box."""
    type_, _, subtype = key.partition(":")
    mid = height / 2
    if type_ in ("S", "PL") or (type_ == "L" and subtype == "punkt"):
        return {"type": type_, "subtype": subtype or None, "points": [[width / 2, mid]]}
    if type_ in ("D", "Ö", "B"):
        inset = 0.12 * height
        return {"type": type_, "subtype": subtype or model.default_subtype(type_),
                "points": [[inset, inset], [width - inset, inset], [width - inset, height - inset], [inset, height - inset]],
                "span": 0}
    if type_ == "A":
        return {"type": type_, "points": [[0.12 * width, 0.8 * height], [0.88 * width, 0.2 * height]]}
    return {"type": type_, "subtype": subtype or model.default_subtype(type_), "points": [[0.06 * width, mid], [0.94 * width, mid]]}


def _swatch_body(out, key, width, height, sz, bubble=None):
    """A symbol laid out in a width × height box; an axis's bubble `bubble` in radius, by default as large as the symbols' texts."""
    if key == "Lastniveau":
        dash = f"{_f(sz.line(14))} {_f(sz.line(3))} {_f(sz.line(1.5))} {_f(sz.line(3))}"
        y = 0.7 * height
        ends = [(0.12 * width, y), (0.88 * width, y)]
        _polyline(out, ends, LOAD_LEVEL_COLOUR, sz.line(1.6), dash=dash, join="miter")
        for p in ends:
            top = (p[0], 0.12 * height)
            _polyline(out, [top, p], LOAD_LEVEL_COLOUR, sz.line(1.4))
            _arrowhead(out, p, top, LOAD_LEVEL_COLOUR, sz)
        return
    if key == "Achse":
        dash = f"{_f(sz.line(14))} {_f(sz.line(3))} {_f(sz.line(1.5))} {_f(sz.line(3))}"
        radius = bubble or min(height * 0.42, sz.text(8.5))
        _polyline(out, [(0.05 * width, height / 2), (width - 2.2 * radius, height / 2)], AXIS_COLOUR, sz.line(0.8), dash=dash, join="miter")
        centre = (width - 1.1 * radius, height / 2)
        out.append(f'<circle cx="{_f(centre[0])}" cy="{_f(centre[1])}" r="{_f(radius)}" fill="{GROUND}" stroke="{AXIS_COLOUR}" stroke-width="{_f(sz.line(1))}"/>')
        _text(out, centre, "A", radius * 1.15, AXIS_COLOUR, bold=True)
        return
    if key == "Umriss":
        inset = 0.2 * height
        _outline(out, [(0.08 * width, inset), (0.92 * width, inset), (0.92 * width, height - inset), (0.08 * width, height - inset)], sz)
        return
    if key in ("Steifigkeitszentrum", "Massenzentrum"):
        # the mark as the plan draws it, its letter beside it rather than at its corner: a swatch is a line high
        mark, letter, colour = (_stiffness_mark, "S", STIFFNESS_COLOUR) if key == "Steifigkeitszentrum" else (_mass_mark, "M", MASS_COLOUR)
        mark(out, (0.34 * width, height / 2), sz, letter=False)
        _text(out, (0.72 * width, height / 2), letter, sz.text(CENTRE_LETTER), colour, bold=True)
        return
    element = _sample(key, width, height)
    _symbol(out, element, sz, compact=True)


def legend_swatch(key):
    """The swatch of one legend line, as an SVG document LEGEND_SWATCH mm in size: the symbol of `key` in fine lines, for show-plan to set beside its text."""
    width, height = LEGEND_SWATCH
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 {_f(width)} {_f(height)}" width="{_f(width)}mm" height="{_f(height)}mm">']
    _swatch_body(out, key, width, height, Sizes(LEGEND_UNIT, {}), bubble=0.36 * height)
    out.append("</svg>")
    return "".join(out)


def legend_items(source):
    """The legend of the symbols a plan uses, in LEGEND's order: each line's key, its text and its swatch -- and, on a plan with a scale, its `quantity` (plan.quantities: metres, square metres or a count), which show-plan lists under the symbols. show-plan lays them out, the texts in the report's own typeface."""
    keys = legend_keys(source)
    measured = model.quantities(source)
    items = []
    for key, text in LEGEND:
        if key in keys:
            item = {"key": key, "text": text, "swatch": legend_swatch(key)}
            if key in CENTRE_KEYS:
                item["centres"] = True   # what `centres: false` takes out of a legend with the symbols it takes out of the drawing (lib/calc-engine.typ's plan-legend)
            if key in measured:
                item["quantity"] = measured[key]
            items.append(item)
    return items


def swatch(type_, subtype=None, width=26, height=18):
    """A tool's icon, drawn like its legend line: the symbol of `type_` (and `subtype`) in a width × height box, for Woodcore's tool bar."""
    key = type_ if type_ in ("Achse", "Lastniveau", *CENTRE_KEYS) else (f"{type_}:{subtype}" if subtype else type_)
    if type_ == "D" and not subtype:
        key = "D:scheibe"
    sz = Sizes(0.55 * height / 18, {"line": 1.0, "point": 1.0, "text": 1.0})
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 {width} {height}" width="{width}" height="{height}">']
    _swatch_body(out, key, width, height, sz)
    out.append("</svg>")
    return "\n".join(out) + "\n"
