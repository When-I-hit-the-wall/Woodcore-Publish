"""A fire-protection plan's drawing, as SVG text: what Woodcore's canvas shows over the architect's plan, and what the report prints (domains/fire.py).

Kept to what QtSvg (SVG Tiny 1.2) and Typst read alike, as every drawing of this project is: no pattern, no clip path, no marker, no arc command, no CSS, no group opacity -- a surface is one path, its islands cut out of it by the even-odd rule; the hatching of a surface to be kept clear is segments cut to its outline; a door's quarter circle is a run of straight pieces; an arrowhead is a polygon; an entry's opacity is written on each of its own shapes, which do not overlap; and a text stands on a box of its own rather than being drawn twice with a white stroke (domains/schema_svg.py's rule, v0.99).

What it draws is the concept, in the colours the VKF / AEAI sheet gives each thing (norms/vkf.py): the SURFACES of the escape routes, under everything, tinted rather than filled so that the architect's lines still show through them; the WALLS, each the band of its fire resistance; the DOORS, the sheet's quarter disc or its flat arrow in the colour of the door's resistance -- in black outline for a door without one; the escape routes' LENGTHS, EXITS and WIDTHS; and over them all the LEGEND, a box listing what the plan draws (fire.legend_rows) in the language it is asked for. For the editor alone (`editing`): a surface that states no kind, in a grey no entry of the legend uses, and the line an escape route's width is measured along.

How large: every size is a multiple of the drawing's unit (plan_svg.base_unit), times the plan's own factor and the entry's own -- `line` for strokes, `text` for texts (fire.factors, domains/figure_style.py). How opaque: fire.opacity_of. Where a text stands: its own place, moved by the entry's `label_offset` (`text_frames`, which the drawing and the canvas's hit-test both read, so a click lands on the text where it is drawn); a text moved clear of its own height is tied back to its place by a thin leader, as a position number is (plan_svg, v0.42).

The legend is written between two markers, `LEGEND_OPEN` and `LEGEND_CLOSE`, so that the report may leave it out (show-fire-plan's `legend: false`) without the figure being drawn twice.
"""

import math

from domains import svg_draw  # the one writer of an SVG number and text (D6)
from domains import fire, plan, plan_svg, statics_svg
from i18n import strings
from norms import vkf

FONT = svg_draw.FONT

LEGEND_OPEN = "<!-- legend -->"
LEGEND_CLOSE = "<!-- /legend -->"

# A surface nobody has given a kind: a grey no entry of the fire-protection legend uses. The editor's own, never printed.
ZONE_COLOUR = svg_draw.colour("ink-soft")
ZONE_FILL_OPACITY = 0.14
# The ground a text stands on (schema_svg.LABEL_GROUND_OPACITY's value, for its reason: the text sits ON what it names).
LABEL_GROUND_OPACITY = 0.85
INK = svg_draw.colour("ink")
GROUND = svg_draw.colour("ground")

# Sizes in the drawing's unit (plan_svg.base_unit: the frame's longer side / 850), a position plan's own scale of things.
ZONE_STROKE = 1.1
SURFACE_STROKE = 0.8
HATCH_SPACING = 5.0
HATCH_STROKE = 0.9
LABEL_SIZE = 9.0
# A door: the hairline round a filled one, as the sheet's pictograms have, and the line of one without a fire resistance.
DOOR_STROKE = 0.5
DOOR_PLAIN_STROKE = 1.0
# An emergency exit's hairline, the pictogram's own.
EXIT_STROKE = 0.4
# An escape route's length: the line's width, the arrowhead's length and half-width, the size of the length written along it.
ROUTE_STROKE = 1.3
ROUTE_HEAD = 9.0
ROUTE_HEAD_HALF = 3.2
ROUTE_TEXT = 8.5
# An escape route's width: the size of its figure, and the line it is measured along, which only the editor shows.
WIDTH_TEXT = 8.5
WIDTH_GUIDE = 0.7
# The leader that ties a text moved by hand back to its own place.
LEADER_STROKE = 0.5
# The legend: its title, its texts, what lies between its frame and its contents, a row's height, a symbol's box and the gap to its text.
LEGEND_TITLE = 11.0
LEGEND_TEXT = 8.5
LEGEND_PAD = 6.0
LEGEND_ROW = 14.0
LEGEND_SWATCH = (24.0, 9.0)
LEGEND_GAP = 6.0
LEGEND_STROKE = 0.6
# What the legend writes for the two symbols that carry a figure: the sheet's own placeholders.
LEGEND_LENGTH = "... m"
LEGEND_WIDTH = "1.20 m"


_f = svg_draw.number_at(3)   # the plan's own precision (svg_draw.py, D6)


def _pts(points):
    return " ".join(f"{_f(x)},{_f(y)}" for x, y in points)


_escape = svg_draw.escape   # (svg_draw.py, D6)


def _op(name, value):
    """An opacity as an attribute, left out where the shape is drawn full: a drawing nobody made translucent is written as it always was."""
    return "" if value >= 1.0 else f' {name}="{_f(value)}"'


def text_width(text, size):
    """How wide `text` is set at `size`, by Arial's own advances (statics_svg.ARIAL_WIDTHS): what a text's box and the legend's frame are sized by."""
    return size * sum(statics_svg.ARIAL_WIDTHS.get(ch, statics_svg.ARIAL_DEFAULT) for ch in text)


def colour_of(key):
    """The colour of one entry of the escape routes (norms/vkf.py): "length", "exit", "width", "vertical", "horizontal", "clear"."""
    return vkf.colour(vkf.escape(key)["rgb"])


def route_colour():
    return colour_of("length")


def wall_colour(cls):
    return vkf.colour(vkf.resistance(cls)["rgb"])


def door_colour(door):
    """The colour a door is filled with -- its fire resistance's -- or None for a door without one, which is drawn in outline."""
    cls = door.get("class")
    return None if cls is None else vkf.colour(vkf.door(door.get("kind", "swing"), cls)["rgb"])


def _units(source, entry, unit):
    """(the unit an entry's strokes are sized in, the unit its texts are): the drawing's unit times the plan's factors and the entry's own."""
    factors = fire.factors(source, entry)
    return unit * factors["line"], unit * factors["text"]


# --- The surfaces ------------------------------------------------------------------

def _ring_path(ring):
    return "M" + " L".join(f"{_f(x)} {_f(y)}" for x, y in ring) + " Z"


def zone_path(zone):
    """A surface as path data: its outline, then each island, for the even-odd rule to cut out."""
    return " ".join(_ring_path(ring) for ring in [zone["points"]] + list(zone.get("holes", [])))


def zone_caption(zone):
    """What is written on a surface: its name where it has one; and on one that states no kind -- a draft, which the editor alone shows -- its id before it, so that it can be found in the list."""
    label = (zone.get("label") or "").strip()
    if zone.get("kind") in fire.SURFACES:
        return label
    return f"{zone['id']} {label}" if label else zone["id"]


def label_box(zone, unit):
    """Where a surface's caption stands in its own place: (cx, cy, half width, half height) in sheet units, `unit` the unit its text is sized in."""
    size = LABEL_SIZE * unit
    cx, cy = fire.label_point(zone)
    return cx, cy, text_width(zone_caption(zone), size) / 2.0 + 0.35 * size, 0.68 * size


def _hatch(out, outline, colour, unit, opacity=1.0):
    """The hatching of a surface to be kept clear: lines at 45°, cut to the outline (plan.line_in_polygon), since SVG Tiny has no pattern to fill with."""
    points = [tuple(p) for p in outline]
    x0, y0, x1, y1 = plan.bbox(points)
    spacing = HATCH_SPACING * unit
    direction = (1 / math.sqrt(2), 1 / math.sqrt(2))
    normal = (-direction[1], direction[0])
    centre = ((x0 + x1) / 2.0, (y0 + y1) / 2.0)
    count = int(((x1 - x0) + (y1 - y0)) / spacing) + 2
    for k in range(-count, count + 1):
        through = (centre[0] + normal[0] * k * spacing, centre[1] + normal[1] * k * spacing)
        for p, q in plan.line_in_polygon(through, direction, points):
            out.append(f'<line x1="{_f(p[0])}" y1="{_f(p[1])}" x2="{_f(q[0])}" y2="{_f(q[1])}" stroke="{colour}" stroke-width="{_f(HATCH_STROKE * unit)}"{_op("stroke-opacity", opacity)}/>')


def _surface(out, zone, unit, opacity):
    """One surface of a kind, as the sheet draws that kind: a vertical or a horizontal escape route tinted in its colour, a surface to be kept clear outlined and hatched in its own. `unit` is the unit its strokes are sized in; `opacity` is its tint's, or its hatching's -- its outline stays full, so that a surface made faint is still bounded."""
    kind = zone["kind"]
    colour = colour_of(kind)
    if kind == "clear":
        out.append(f'<path d="{zone_path(zone)}" fill="none" stroke="{colour}" stroke-width="{_f(SURFACE_STROKE * unit)}" stroke-linejoin="round"/>')
        _hatch(out, zone["points"], colour, unit, opacity)
        return
    # a horizontal escape route's own colour is too pale to bound it on white paper: both kinds are edged in the vertical one's green
    out.append(f'<path d="{zone_path(zone)}" fill="{colour}" fill-opacity="{_f(opacity)}" fill-rule="evenodd" stroke="{colour_of("vertical")}" stroke-width="{_f(SURFACE_STROKE * unit)}" stroke-linejoin="round"/>')


def _zones(out, source, unit, editing):
    for zone in source.get("zones", []):
        lu, _tu = _units(source, zone, unit)
        if zone.get("kind") in fire.SURFACES:
            _surface(out, zone, lu, fire.opacity_of("zones", zone))
        elif editing:
            out.append(f'<path d="{zone_path(zone)}" fill="{ZONE_COLOUR}" fill-opacity="{_f(ZONE_FILL_OPACITY)}" fill-rule="evenodd" stroke="{ZONE_COLOUR}" stroke-width="{_f(ZONE_STROKE * lu)}" stroke-linejoin="round"/>')


# --- The walls and the doors ---------------------------------------------------------

def _walls(out, source, frame):
    """Each wall as the band of its fire resistance: a line as wide as a wall is thick -- times the plan's and its own `line` --, its ends square so that two stretches meeting at a corner fill it."""
    band = fire.band_width(frame)
    for wall in source.get("walls", []):
        width = band * fire.factors(source, wall)["line"]
        out.append(f'<polyline points="{_pts(wall["points"])}" fill="none" stroke="{wall_colour(wall["class"])}" stroke-width="{_f(width)}"{_op("stroke-opacity", fire.opacity_of("walls", wall))} stroke-linecap="square" stroke-linejoin="miter"/>')


def _door(out, door, unit, opacity=1.0):
    """One door: the sheet's shape filled with the colour of its fire resistance inside a hairline, or -- without one -- an architect's door in black outline: the leaf standing open and the arc it sweeps, or the flat arrow's outline. `unit` is the unit its strokes are sized in."""
    shape = fire.door_shape(door)
    colour = door_colour(door)
    if colour is not None:
        out.append(f'<polygon points="{_pts(shape)}" fill="{colour}"{_op("fill-opacity", opacity)} stroke="{INK}" stroke-width="{_f(DOOR_STROKE * unit)}"{_op("stroke-opacity", opacity)} stroke-linejoin="round"/>')
    elif door.get("kind") == "slide":
        out.append(f'<polygon points="{_pts(shape)}" fill="none" stroke="{INK}" stroke-width="{_f(DOOR_PLAIN_STROKE * unit)}"{_op("stroke-opacity", opacity)} stroke-linejoin="round"/>')
    else:
        # hinge -> the open leaf's end -> back along the arc to where the leaf closes: the opening itself stays undrawn
        line = [shape[0]] + list(reversed(shape[1:]))
        out.append(f'<polyline points="{_pts(line)}" fill="none" stroke="{INK}" stroke-width="{_f(DOOR_PLAIN_STROKE * unit)}"{_op("stroke-opacity", opacity)} stroke-linejoin="round"/>')


# --- The texts -------------------------------------------------------------------------

def _turned(angle):
    """An angle a text is read at: never upside down, and a text along a vertical line read from the bottom up, as a drawing's is."""
    if angle >= 90:
        angle -= 180
    elif angle < -90:
        angle += 180
    return angle


def route_label(route, frame, unit):
    """Where an escape route's text stands in its own place and how it is turned: (text, cx, cy, angle in degrees, half width, half height), or None where it writes nothing. Along the route's longest stretch, beside the line rather than on it, and never upside down. `unit` is the unit its text is sized in."""
    text = fire.route_text(route, fire.per_m(frame))
    if not text:
        return None
    points = route["points"]
    j = max(range(1, len(points)), key=lambda k: math.dist(points[k - 1], points[k]))
    (x1, y1), (x2, y2) = points[j - 1], points[j]
    angle = _turned(math.degrees(math.atan2(y2 - y1, x2 - x1)))
    size = ROUTE_TEXT * unit
    # off the line by a little more than half the text's height, on the side that is «above» the text as it is read
    nx, ny = math.sin(math.radians(angle)), -math.cos(math.radians(angle))
    off = 0.95 * size
    return text, (x1 + x2) / 2 + nx * off, (y1 + y2) / 2 + ny * off, angle, text_width(text, size) / 2.0 + 0.3 * size, 0.62 * size


def width_label(entry, frame, unit):
    """Where an escape route's width is written in its own place and how it is turned: (text, cx, cy, angle, half width, half height), or None where it writes nothing. At the middle of the two points it is measured between, along the line through them -- across the passage, as the sample plans write it."""
    text = fire.width_text(entry, fire.per_m(frame))
    if not text:
        return None
    (x1, y1), (x2, y2) = entry["points"]
    size = WIDTH_TEXT * unit
    return text, (x1 + x2) / 2, (y1 + y2) / 2, _turned(math.degrees(math.atan2(y2 - y1, x2 - x1))), text_width(text, size) / 2.0 + 0.3 * size, 0.62 * size


def text_frames(source, frame, editing=False):
    """Every text the plan writes, where it is drawn: a list of {"id", "collection", "text", "at", "home", "angle", "hw", "hh", "size", "colour"} -- `home` the text's own place, `at` where it stands once its entry's `label_offset` has moved it, `hw` and `hh` its box's half sides, `angle` how the box is turned. In the order they are drawn: the escape routes' lengths, the widths, then the surfaces' names, which lie over everything.

    One function for the drawing and for the canvas, which asks it what lies under the pointer (`hit_text`): a text is then grabbed exactly where it is seen. A surface's caption is listed only where it is drawn -- a name the engineer typed, or, for the editor, the id of a draft.
    """
    unit = plan_svg.base_unit(plan.crop_of(frame))
    frames = []

    def add(collection, entry, label, size, colour):
        text, cx, cy, angle, hw, hh = label
        dx, dy = entry.get("label_offset") or (0.0, 0.0)
        frames.append({"id": entry["id"], "collection": collection, "text": text, "home": (cx, cy), "at": (cx + dx, cy + dy),
                       "angle": angle, "hw": hw, "hh": hh, "size": size, "colour": colour})

    for route in source.get("routes", []):
        _lu, tu = _units(source, route, unit)
        label = route_label(route, frame, tu)
        if label is not None:
            add("routes", route, label, ROUTE_TEXT * tu, route_colour())
    for entry in source.get("widths", []):
        _lu, tu = _units(source, entry, unit)
        label = width_label(entry, frame, tu)
        if label is not None:
            add("widths", entry, label, WIDTH_TEXT * tu, colour_of("width"))
    for zone in source.get("zones", []):
        typed = zone.get("kind") in fire.SURFACES
        caption = zone_caption(zone)
        if not caption or not (typed or editing):
            continue
        _lu, tu = _units(source, zone, unit)
        cx, cy, hw, hh = label_box(zone, tu)
        add("zones", zone, (caption, cx, cy, 0.0, hw, hh), LABEL_SIZE * tu, INK if typed else ZONE_COLOUR)
    return frames


def _in_frame(point, frame, slack=0.0):
    """Whether `point` lies in a text's box, which is turned with its text."""
    dx, dy = point[0] - frame["at"][0], point[1] - frame["at"][1]
    a = math.radians(frame["angle"])
    along, across = dx * math.cos(a) + dy * math.sin(a), -dx * math.sin(a) + dy * math.cos(a)
    return abs(along) <= frame["hw"] + slack and abs(across) <= frame["hh"] + slack


def hit_text(source, frame, point, editing=True, slack=0.0):
    """The frame (text_frames') of the text under `point`, the one drawn last where two lie one on another, or None. What a press of the selection tool asks before anything else: a text is drawn over what it names, and dragging it moves the text and not its entry."""
    for item in reversed(text_frames(source, frame, editing)):
        if _in_frame(point, item, slack):
            return item
    return None


def _text(out, item, unit):
    """One text on its ground, turned as it is read; where it was moved clear of its own height, a thin leader ties it back to its own place."""
    (cx, cy), (hx, hy) = item["at"], item["home"]
    if math.dist((cx, cy), (hx, hy)) > 2.0 * item["hh"]:
        out.append(f'<line x1="{_f(hx)}" y1="{_f(hy)}" x2="{_f(cx)}" y2="{_f(cy)}" stroke="{item["colour"]}" stroke-width="{_f(LEADER_STROKE * unit)}"/>')
    hw, hh, size = item["hw"], item["hh"], item["size"]
    turn = f' transform="translate({_f(cx)},{_f(cy)}) rotate({_f(item["angle"])})"'
    out.append(f'<rect x="{_f(-hw)}" y="{_f(-hh)}" width="{_f(2 * hw)}" height="{_f(2 * hh)}" fill="{GROUND}" fill-opacity="{_f(LABEL_GROUND_OPACITY)}"{turn}/>')
    out.append(f'<text x="0" y="{_f(0.35 * size)}" font-family="{FONT}" font-size="{_f(size)}" fill="{item["colour"]}" text-anchor="middle"{turn}>{_escape(item["text"])}</text>')


# --- The escape routes' three marks ----------------------------------------------------

def _arrow(out, points, colour, unit, opacity=1.0):
    """A thin line ending on a filled head at its last point: the sheet's «Fluchtweglänge». The line stops at the head's base, so the two never lie one on the other and an opacity shows no seam."""
    (x1, y1), (x2, y2) = points[-2], points[-1]
    d = math.dist((x1, y1), (x2, y2)) or 1.0
    ux, uy = (x2 - x1) / d, (y2 - y1) / d
    head = min(ROUTE_HEAD * unit, 0.6 * d)
    bx, by = x2 - ux * head, y2 - uy * head
    half = ROUTE_HEAD_HALF * unit
    line = [tuple(p) for p in points[:-1]] + [(bx, by)]
    out.append(f'<polyline points="{_pts(line)}" fill="none" stroke="{colour}" stroke-width="{_f(ROUTE_STROKE * unit)}"{_op("stroke-opacity", opacity)} stroke-linejoin="round"/>')
    out.append(f'<polygon points="{_pts([(x2, y2), (bx - uy * half, by + ux * half), (bx + uy * half, by - ux * half)])}" fill="{colour}"{_op("fill-opacity", opacity)}/>')


def _routes(out, source, unit):
    """Each escape route's length as the sheet draws it: a thin green arrow. Its length is one of the plan's texts (`text_frames`)."""
    colour = route_colour()
    for route in source.get("routes", []):
        lu, _tu = _units(source, route, unit)
        _arrow(out, route["points"], colour, lu, fire.opacity_of("routes", route))


def _exits(out, source, unit):
    """Each emergency exit: the sheet's thick green arrow, whose size is its two points'."""
    colour = colour_of("exit")
    hairline = EXIT_STROKE * unit * fire.drawing_factors(source)["line"]
    for entry in source.get("exits", []):
        opacity = fire.opacity_of("exits", entry)
        out.append(f'<polygon points="{_pts(fire.exit_shape(entry["points"]))}" fill="{colour}"{_op("fill-opacity", opacity)} stroke="{INK}" stroke-width="{_f(hairline)}"{_op("stroke-opacity", opacity)} stroke-linejoin="miter"/>')


def _width_guides(out, source, unit):
    """The line each escape route's width is measured along, which the editor alone shows: it is how a width that writes nothing -- no scale, no text -- is still found."""
    colour = colour_of("width")
    for entry in source.get("widths", []):
        (x1, y1), (x2, y2) = entry["points"]
        out.append(f'<line x1="{_f(x1)}" y1="{_f(y1)}" x2="{_f(x2)}" y2="{_f(y2)}" stroke="{colour}" stroke-width="{_f(WIDTH_GUIDE * unit)}" stroke-dasharray="{_f(3 * unit)} {_f(2 * unit)}"/>')


# --- The legend ---------------------------------------------------------------------------

def legend_text(row, lang):
    """What a row of the legend says, in `lang`: the sheet's own words through the glossary, or -- a door without a fire resistance, which no sheet names -- the engine's."""
    if row["label"] is None:
        return strings.text(f"fire.door.{row['kind']}", lang)
    return strings.term(row["label"], lang)


def _legend_unit(source, frame):
    """The unit the legend is sized in: the drawing's, times the legend's own size -- and nothing else, so that a legend reads the same whatever the plan's strokes and texts were set to."""
    return plan_svg.base_unit(plan.crop_of(frame)) * fire.legend_scale(source)


def legend_box(source, frame, lang=strings.SOURCE_LANGUAGE):
    """Where the legend stands, (x, y, width, height) in sheet units, or None for a plan that shows none. As wide as its longest line, as tall as its rows: what the canvas grabs to move it, and what the drawing frames."""
    place = source.get("legend")
    if not place:
        return None
    unit = _legend_unit(source, frame)
    rows = fire.legend_rows(source)
    title = text_width(strings.text("fire.legend", lang), LEGEND_TITLE * unit)
    texts = max([text_width(legend_text(row, lang), LEGEND_TEXT * unit) for row in rows], default=0.0)
    inner = max(title, (LEGEND_SWATCH[0] + LEGEND_GAP) * unit + texts if rows else 0.0)
    height = (2 * LEGEND_PAD + 1.3 * LEGEND_TITLE + LEGEND_ROW * len(rows)) * unit
    return float(place["x"]), float(place["y"]), inner + 2 * LEGEND_PAD * unit, height


def _swatch(out, row, x, y, unit):
    """The symbol of one row of the legend, in the box whose top left corner is (x, y): the very thing the plan draws, small, at the size and the opacity of an entry that states none of its own."""
    w, h = LEGEND_SWATCH[0] * unit, LEGEND_SWATCH[1] * unit
    cy = y + h / 2.0
    symbol = row["symbol"]
    if symbol == "wall":
        out.append(f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}" fill="{vkf.colour(row["rgb"])}"/>')
    elif symbol == "surface":
        zone = {"kind": row["kind"], "points": [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]}
        _surface(out, zone, unit, fire.opacity_of("zones", zone))
    elif symbol == "exit":
        length = h / vkf.shape("exit")["head_width"]
        left = x + (w - length) / 2.0
        out.append(f'<polygon points="{_pts(fire.exit_shape([[left, cy], [left + length, cy]]))}" fill="{vkf.colour(row["rgb"])}" stroke="{INK}" stroke-width="{_f(EXIT_STROKE * unit)}"/>')
    elif symbol == "length":
        colour = vkf.colour(row["rgb"])
        base = y + 0.82 * h
        _arrow(out, [[x + w, base], [x, base]], colour, unit * 0.75)
        size = 0.8 * LEGEND_TEXT * unit
        out.append(f'<text x="{_f(x + 0.6 * w)}" y="{_f(base - 0.25 * h)}" font-family="{FONT}" font-size="{_f(size)}" fill="{colour}" text-anchor="middle">{_escape(LEGEND_LENGTH)}</text>')
    elif symbol == "width":
        size = LEGEND_TEXT * unit
        out.append(f'<text x="{_f(x + w / 2.0)}" y="{_f(cy + 0.35 * size)}" font-family="{FONT}" font-size="{_f(size)}" fill="{vkf.colour(row["rgb"])}" text-anchor="middle">{_escape(LEGEND_WIDTH)}</text>')
    elif symbol == "door":
        door = {"kind": row["kind"], "side": 1}
        if row["class"] is not None:
            door["class"] = row["class"]
        if row["kind"] == "slide":
            # the sheet's own way round: the arrowhead at the left, rising
            door["points"] = [[x + w, y + h], [x, y + h]]
        else:
            # a leaf as long as the box is high, hinged at the left and opening upwards
            left = x + (w - h) / 2.0
            door["points"] = [[left, y + h], [left + h, y + h]]
            door["side"] = -1
        _door(out, door, unit)


# The swatch of a legend line the report sets in its own typeface: the legend's own symbol box (LEGEND_SWATCH, in the drawing's unit) shrunk to about 10 x 4 mm, the size a position plan's swatches have (plan_svg.LEGEND_SWATCH), so that the two kinds of plan's legends read alike.
SWATCH_MM = 10.0


def legend_key(row):
    """A line of the legend by what it is: wall:<class>, surface:<kind>, exit, length, width, door:<kind>:<class>, door:<kind> for a door without a fire resistance."""
    symbol = row["symbol"]
    if symbol == "wall":
        return f"wall:{row['class']}"
    if symbol == "surface":
        return f"surface:{row['kind']}"
    if symbol == "door":
        return f"door:{row['kind']}:{row['class']}" if row["class"] is not None else f"door:{row['kind']}"
    return symbol


def legend_swatch(row):
    """The symbol of one legend line as an SVG document SWATCH_MM wide: the very thing the plan draws, small, for show-fire-plan and an export sheet's legend to set beside its text in the report's typeface."""
    unit = SWATCH_MM / LEGEND_SWATCH[0]
    height = LEGEND_SWATCH[1] * unit
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 {_f(SWATCH_MM)} {_f(height)}" width="{_f(SWATCH_MM)}mm" height="{_f(height)}mm">']
    _swatch(out, row, 0.0, 0.0, unit)
    out.append("</svg>")
    return "".join(out)


def legend_lines(source):
    """The legend as the report sets it, in the order the figure writes it (fire.legend_rows): [{key, text, swatch}] -- `text` the line's words in the sheet's German (or the engine's, for a door without a fire resistance), with `term` the glossary term they stand for or `engine` the glossary key of the engine's own word, which the report translates -- and the swatch an SVG. Empty for a plan that draws nothing the legend lists."""
    lines = []
    for row in fire.legend_rows(source):
        line = {"key": legend_key(row), "text": legend_text(row, strings.SOURCE_LANGUAGE)}
        if row["label"] is None:
            line["engine"] = f"fire.door.{row['kind']}"
        else:
            line["term"] = row["label"]
        line["swatch"] = legend_swatch(row)
        lines.append(line)
    return lines


def _legend(out, source, frame, lang):
    """The legend: a white box inside a thin frame, its title, then one row per symbol the plan draws -- the symbol, and what it means."""
    box = legend_box(source, frame, lang)
    if box is None:
        return
    x, y, width, height = box
    unit = _legend_unit(source, frame)
    pad = LEGEND_PAD * unit
    out.append(LEGEND_OPEN)
    out.append(f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(width)}" height="{_f(height)}" fill="{GROUND}" stroke="{INK}" stroke-width="{_f(LEGEND_STROKE * unit)}"/>')
    size = LEGEND_TITLE * unit
    out.append(f'<text x="{_f(x + pad)}" y="{_f(y + pad + 0.85 * size)}" font-family="{FONT}" font-size="{_f(size)}" fill="{INK}">{_escape(strings.text("fire.legend", lang))}</text>')
    size = LEGEND_TEXT * unit
    top = y + pad + 1.3 * LEGEND_TITLE * unit
    for i, row in enumerate(fire.legend_rows(source)):
        row_y = top + i * LEGEND_ROW * unit + (LEGEND_ROW - LEGEND_SWATCH[1]) * unit / 2.0
        _swatch(out, row, x + pad, row_y, unit)
        out.append(f'<text x="{_f(x + pad + (LEGEND_SWATCH[0] + LEGEND_GAP) * unit)}" y="{_f(row_y + LEGEND_SWATCH[1] * unit / 2.0 + 0.35 * size)}" font-family="{FONT}" font-size="{_f(size)}" fill="{INK}">{_escape(legend_text(row, lang))}</text>')
    out.append(LEGEND_CLOSE)


# --- The whole drawing --------------------------------------------------------------------

def render(source, frame, window=None, editing=False, lang=strings.SOURCE_LANGUAGE, values=None):
    """The plan as an SVG document over `window` ({x, y, w, h} in sheet units; the frame's crop by default): a veil over the background, as a position plan's, then the concept -- the surfaces, the walls, the doors, the escape routes' marks, the texts and the legend, in that order, each over what it may lie on. `frame` is fire.frame_of()'s; `lang` is the language the legend is written in; `editing` adds what only the editor shows; `values` are the export's, which a text placed with the Text tool prints (issue #43)."""
    crop = plan.crop_of(frame)
    window = window or crop
    unit = plan_svg.base_unit(crop)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="{_f(window["x"])} {_f(window["y"])} {_f(window["w"])} {_f(window["h"])}" '
        f'width="{_f(window["w"])}" height="{_f(window["h"])}">',
    ]
    background = frame.get("background")
    if background is not None:
        veil = 1.0 - float(background.get("opacity", plan.DEFAULT_OPACITY))
        if veil > 0:
            out.append(f'<rect x="{_f(window["x"])}" y="{_f(window["y"])}" width="{_f(window["w"])}" height="{_f(window["h"])}" fill="{GROUND}" fill-opacity="{_f(veil)}"/>')
    _zones(out, source, unit, editing)
    _walls(out, source, frame)
    for door in source.get("doors", []):
        lu, _tu = _units(source, door, unit)
        _door(out, door, lu, fire.opacity_of("doors", door))
    _routes(out, source, unit)
    _exits(out, source, unit)
    if editing:
        _width_guides(out, source, unit)
    for item in text_frames(source, frame, editing):
        _text(out, item, unit)
    # the texts placed with the Text tool (issue #43): the position plan's own drawing of them, at its own sizes, under the legend
    plan_svg.draw_texts(out, source, plan_svg.Sizes(unit, source.get("style", {})), values)
    _legend(out, source, frame, lang)
    out.append("</svg>")
    return "\n".join(out)
