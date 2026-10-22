"""The drawing of a build-up of permanent loads, as SVG text (issue #35, UI-002, UI-003): the layers stacked top to bottom, the way Ubakus draws a wall or a roof, with the height of each band dimensioned at the left, each layer named at the right, and, for battens, rafters or joists set at a spacing, the width of one and the spacing dimensioned above their band.

**A band** is one layer, or a layer and those that come `beside` it (the insulation between the rafters): the band is as high as its thickest layer; a continuous layer fills it, and the members of a spaced one are drawn over it at their spacing. A layer with no thickness (a load typed, a weight per surface stated without one) is named and not drawn. The heights are to scale, except that a band is never drawn thinner than `MIN_BAND`, so a membrane of 1 mm stays visible -- its dimension still says 1. Two bays of the widest spacing are drawn, or `PLAIN_WIDTH` mm where nothing is spaced.

Kept to what QtSvg (SVG Tiny 1.2) and resvg read alike, like every drawing here: no marker, no CSS, no pattern; one SVG for every language, its words being the materials' own names -- the data's, as the table beside it prints them. The fills are the detail schemas' own (`schema_svg`), so a build-up and a detail of one project look like one set. No Qt here.
"""

from domains import svg_draw  # the one writer of an SVG number and text (D6)
from domains import svg_text  # the one plain text writer (ARCH-004)
from domains import schema_svg, statics_svg

FONT = svg_draw.FONT
FILLS = schema_svg.ELEMENT_FILLS + svg_draw.colours("layers")
INSULATION_FILL = svg_draw.colour("insulation")
GROUND = svg_draw.colour("ground")
STROKE_COLOUR = schema_svg.ELEMENT_STROKE
TEXT_COLOUR = schema_svg.TEXT_COLOR
MUTED = schema_svg.MUTED

DRAW_WIDTH = 520.0          # the strip, in the drawing's units
PLAIN_WIDTH = 600.0         # mm drawn where no layer is spaced
MIN_BAND = 7.0              # the thinnest band drawn
SCALE_MAX = 1.6             # drawing units per mm at most: a thin build-up is not blown up
LEFT = 160.0                # room for the chain of heights and the whole height
RIGHT = 330.0               # room for the names
TOP = 20.0
TEXT = 15.0
SMALL = 13.0
STROKE = 1.2
THIN = 0.8
INSULATION_WORDS = ("dämm", "isol", "wolle", "faser", "steinwolle", "glaswolle", "insul")


_f = svg_draw.number_at(1)   # a coordinate at 1 decimals (svg_draw.py, D6)


_esc = svg_draw.escape   # (svg_draw.py, D6)


def _rect(out, x, y, w, h, fill, stroke=STROKE_COLOUR, width=STROKE):
    out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="%s" stroke="%s" stroke-width="%s"/>' % (_f(x), _f(y), _f(w), _f(h), fill, stroke, _f(width)))


def _line(out, x1, y1, x2, y2, colour=MUTED, width=THIN):
    out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s" stroke-linecap="round"/>' % (_f(x1), _f(y1), _f(x2), _f(y2), colour, _f(width)))


def _text(out, x, y, content, size=TEXT, anchor="middle", colour=TEXT_COLOUR, rotate=False):
    svg_text.plain(out, x, y, content, size, colour, _f, anchor, ' transform="rotate(-90 %s %s)"' % (_f(x), _f(y)) if rotate else "")


def _tick(out, x, y, vertical):
    if vertical:
        _line(out, x - 4, y + 4, x + 4, y - 4, TEXT_COLOUR, THIN)
    else:
        _line(out, x - 4, y + 4, x + 4, y - 4, TEXT_COLOUR, THIN)


def _insulation(layer):
    words = ("%s %s" % (layer.get("label") or "", layer.get("ebene") or "")).lower()
    return any(w in words for w in INSULATION_WORDS)


def bands(layers):
    """The layers grouped into bands, top to bottom: [[layer, ...], ...] -- a layer `beside` the one above it joins its band; a layer with no thickness is in none."""
    out = []
    for layer in layers:
        if not layer.get("thickness"):
            continue
        if layer.get("beside") and out:
            out[-1].append(layer)
        else:
            out.append([layer])
    return out


def render(layers):
    """The SVG of a build-up. `layers` are dead_load_source.layer_rows(...)'s: each {thickness, width, spacing, beside, label, ebene} in mm."""
    groups = bands(layers)
    spacings = [l["spacing"] for l in layers if l.get("spacing")]
    strip_mm = 2 * max(spacings) if spacings else PLAIN_WIDTH
    total_mm = sum(max(l["thickness"] for l in band) for band in groups) or 1.0
    scale = min(DRAW_WIDTH / strip_mm, SCALE_MAX)
    width_units = strip_mm * scale
    heights = [max(max(l["thickness"] for l in band) * scale, MIN_BAND) for band in groups]
    total_h = sum(heights)
    out = []
    x0, y = LEFT, TOP
    # a fill per layer, in the order of the table: the same layer is the same colour wherever it is drawn
    fills = {}
    for i, layer in enumerate(layers):
        fills[id(layer)] = INSULATION_FILL if _insulation(layer) else FILLS[i % len(FILLS)]
    dimension_x = x0 - 46
    centres, members = [], []
    for band, h in zip(groups, heights):
        continuous = [l for l in band if not l.get("spacing")]
        spaced = [l for l in band if l.get("spacing")]
        for layer in continuous:
            _rect(out, x0, y, width_units, h, fills[id(layer)])
        if spaced and not continuous:
            _rect(out, x0, y, width_units, h, GROUND, MUTED, THIN)     # the gaps, empty
        for layer in spaced:
            member_h = max(layer["thickness"] * scale, MIN_BAND)
            w, sp = layer["width"] * scale, layer["spacing"] * scale
            x = x0 + sp / 2 - w / 2
            members.append((layer, x, w, sp, y + member_h))
            while x < x0 + width_units - 1e-6:
                left, right = max(x, x0), min(x + w, x0 + width_units)
                if right > left:
                    _rect(out, left, y, right - left, member_h, fills[id(layer)])
                x += sp
        # UI-003: the band's height, in the chain at the left
        _line(out, dimension_x, y, dimension_x, y + h, TEXT_COLOUR)
        _line(out, dimension_x - 6, y, x0 - 4, y, MUTED, THIN)
        _tick(out, dimension_x, y, True)
        centres.append((y + h / 2, " + ".join(l.get("label") or "" for l in band), max(l["thickness"] for l in band)))
        y += h
    _line(out, dimension_x - 6, y, x0 - 4, y, MUTED, THIN)
    _tick(out, dimension_x, y, True)
    # the heights' values and the names: set apart so that two thin bands never write over each other, each joined to its band
    gap = TEXT + 3
    placed = []
    for centre, _name, _t in centres:
        placed.append(max(centre, placed[-1] + gap) if placed else centre)
    overflow = placed[-1] - (TOP + total_h - TEXT / 2) if placed else 0
    if overflow > 0:
        placed = [max(p - overflow, TOP + TEXT / 2 + k * gap) for k, p in enumerate(placed)]
    for (centre, name, thickness), at in zip(centres, placed):
        _text(out, dimension_x - 8, at + SMALL / 3, _f(thickness), SMALL, anchor="end")
        _line(out, x0 + width_units, centre, x0 + width_units + 14, centre, MUTED, THIN)
        _line(out, x0 + width_units + 14, centre, x0 + width_units + 24, at, MUTED, THIN)
        _text(out, x0 + width_units + 28, at + TEXT / 3, name, TEXT, anchor="start")
    # UI-003: under the drawing, the width of one member and the spacing, one line per spaced layer
    below = TOP + total_h + 26
    for layer, first, w, sp, bottom in members:
        _line(out, first, bottom, first, below + 4, MUTED, THIN)
        _line(out, first + w, bottom, first + w, below + 4, MUTED, THIN)
        _line(out, first, below, first + w, below, TEXT_COLOUR)
        _tick(out, first, below, False)
        _tick(out, first + w, below, False)
        _text(out, first + w / 2, below + SMALL + 4, _f(layer["width"]), SMALL)
        if first + sp + w <= x0 + width_units + 1e-6:
            a, b = first + w / 2, first + sp + w / 2
            line_y = below + 34
            _line(out, a, bottom, a, line_y + 4, MUTED, THIN)
            _line(out, b, bottom, b, line_y + 4, MUTED, THIN)
            _line(out, a, line_y, b, line_y, TEXT_COLOUR)
            _tick(out, a, line_y, False)
            _tick(out, b, line_y, False)
            _text(out, (a + b) / 2, line_y + SMALL + 4, "e = %s" % _f(layer["spacing"]), SMALL)
        below += 70
    # the whole height
    total_x = dimension_x - 50
    _line(out, total_x, TOP, total_x, TOP + total_h, TEXT_COLOUR)
    _tick(out, total_x, TOP, True)
    _tick(out, total_x, TOP + total_h, True)
    _text(out, total_x - 6, TOP + total_h / 2 + TEXT / 3, _f(total_mm), TEXT, anchor="end")
    longest = max([statics_svg.text_width(name, TEXT) for _c, name, _t in centres] or [0.0])
    view_w = LEFT + width_units + max(RIGHT, longest + 44)
    view_h = max(below if members else TOP + total_h + 24, placed[-1] + TEXT if placed else 0) + 4
    head = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s" width="%s" height="%s">' % (_f(view_w), _f(view_h), _f(view_w), _f(view_h)))
    return head + "".join(out) + "</svg>\n"
