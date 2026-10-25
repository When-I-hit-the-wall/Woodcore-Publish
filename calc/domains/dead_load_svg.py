"""The section of a build-up of permanent loads, as SVG text (issue #35, UI-002, UI-003; redrawn by issue #111, spec docs/requirements/completed/2026-10-24-poids-propre-repense.md, REQ-009, UI-003, P09): one strip of 1 m, the heights at the same scale as the width -- a build-up three times as wide as it is high is drawn so --, the way Ubakus draws a wall or a roof.

**A level** is one layer, or a spaced layer and the one that fills between its pieces (`link`, two at most, D-07): the pieces at their true spacing, centred in their bays, cut at the strip's edges; the line that fills drawn between them from the bottom, the air above it left empty; a level as high as its thicker layer. A layer weighed per m² without a thickness (tiles, a membrane) is a line; a load typed is not drawn. Nothing is drawn thinner than it is: no minimum band any more.

**The words.** Each band's height in the chain at the left where it fits, the whole height beside it, «1000» under the strip, the width of one piece and its spacing under it where they fit. The names in a column at the right, one per layer, each joined to its layer by a line fanned out from it, cut by «…» where the column is too narrow (the whole name its `<title>`); under `LEGEND_BELOW` units of width, the legend mode: a number beside each layer and the names listed under the drawing.

`render(layers, width, legend)` draws it at the width the caller gives (None: the export's, `EXPORT_WIDTH`, its bytes stable) and `hit_boxes(layers, width, legend)` gives the box of each layer drawn, for a click -- both from one layout (`_layout`). Kept to what QtSvg (SVG Tiny 1.2) and resvg read alike, like every drawing here: no marker, no CSS, no pattern, no clip path; one SVG for every language, its words being the materials' own names. The fills are the detail schemas' own (`schema_svg`). No Qt here.
"""

from domains import svg_draw  # the one writer of an SVG number and text (D6)
from domains import svg_text  # the one plain text writer (ARCH-004)
from domains import dead_load_layers, schema_svg

FONT = svg_draw.FONT
FILLS = schema_svg.ELEMENT_FILLS + svg_draw.colours("layers")
INSULATION_FILL = svg_draw.colour("insulation")
GROUND = svg_draw.colour("ground")
STROKE_COLOUR = schema_svg.ELEMENT_STROKE
TEXT_COLOUR = schema_svg.TEXT_COLOR
MUTED = schema_svg.MUTED

STRIP = dead_load_layers.STRIP   # mm drawn: one metre
EXPORT_WIDTH = 760.0             # the drawing's width where the caller gives none -- the export's, the report's
LEGEND_BELOW = 560.0             # under this width, the names listed under the drawing
LEFT = 96.0                      # the chain of heights and the whole height
LEFT_LEGEND = 80.0
NAMES = 230.0                    # the column of names
NAMES_GAP = 34.0                 # from the strip to the names, where the fanned lines run
NUMBER_GAP = 22.0                # the legend's numbers beside the strip
TOP = 16.0
TEXT = 13.0
SMALL = 11.0
LINE = TEXT + 5.0                # one name to the next
STROKE = 1.0
THIN = 0.7
INSULATION_WORDS = ("dämm", "isol", "wolle", "faser", "steinwolle", "glaswolle", "insul")
INSULATION_ROLES = ("insulation", "impact_insulation")


_f = svg_draw.number_at(1)   # a coordinate at 1 decimals (svg_draw.py, D6)


def _rect(out, x, y, w, h, fill, stroke=STROKE_COLOUR, width=STROKE):
    out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="%s" stroke="%s" stroke-width="%s"/>' % (_f(x), _f(y), _f(w), _f(h), fill, stroke, _f(width)))


def _line(out, x1, y1, x2, y2, colour=MUTED, width=THIN):
    out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s" stroke-linecap="round"/>' % (_f(x1), _f(y1), _f(x2), _f(y2), colour, _f(width)))


def _text(out, x, y, content, size=TEXT, anchor="middle", colour=TEXT_COLOUR):
    svg_text.plain(out, x, y, content, size, colour, _f, anchor)


def _tick(out, x, y):
    _line(out, x - 3, y + 3, x + 3, y - 3, TEXT_COLOUR, THIN)


def _insulation(layer):
    if layer.role in INSULATION_ROLES:
        return True
    words = ("%s %s" % (layer.label or "", layer.ebene or "")).lower()
    return any(w in words for w in INSULATION_WORDS)


def bands(layers):
    """The layers (contracts.Layer) top to bottom as the section draws them: [("level", [layer] or [layer, layer]) | ("line", [layer])] -- a layer `link`ed to the one below shares its level; a layer with no thickness weighed per m² is a line; a load typed is in none."""
    out, i = [], 0
    while i < len(layers):
        layer = layers[i]
        if layer.pose == "typed":
            i += 1
            continue
        if not layer.thickness:
            out.append(("line", [layer]))
            i += 1
            continue
        if layer.link and i + 1 < len(layers) and layers[i + 1].thickness and layers[i + 1].pose != "typed":
            out.append(("level", [layer, layers[i + 1]]))
            i += 2
            continue
        out.append(("level", [layer]))
        i += 1
    return out


def _fits(text, room, size=SMALL):
    return svg_text.text_width(text, size) + 4 <= room


def _cut(text, room, size=TEXT):
    """`text` cut by «…» to `room` units, whole where it fits."""
    if svg_text.text_width(text, size) <= room:
        return text
    while text and svg_text.text_width(text + "…", size) > room:
        text = text[:-1]
    return text.rstrip() + "…"


def _layout(layers, width=None, legend=None):
    """Where everything goes: the strip, each layer's boxes (pieces, filling, line), each band's height, the names' places. One layout for `render` and `hit_boxes`."""
    width = float(width or EXPORT_WIDTH)
    legend = width < LEGEND_BELOW if legend is None else legend
    left = LEFT_LEGEND if legend else LEFT
    right = NUMBER_GAP + 8 if legend else NAMES_GAP + NAMES
    strip = max(width - left - right, 120.0)
    k = strip / STRIP                       # units per mm, the same both ways
    x0, y = left, TOP
    fills = {layer.number: INSULATION_FILL if _insulation(layer) else FILLS[(layer.number - 1) % len(FILLS)] for layer in layers}
    drawn, chain = [], []
    for kind, group in bands(layers):
        if kind == "line":
            drawn.append({"layer": group[0], "boxes": [(x0, y, strip, 0.0)], "line": True, "anchor": y})
            continue
        h = max(l.thickness for l in group) * k
        pieces = [l for l in group if l.pose == "spaced" and l.width and l.spacing]
        others = [l for l in group if l not in pieces]
        if pieces:
            p = pieces[0]
            ph, bw, sp = p.thickness * k, p.width * k, p.spacing * k
            boxes, x = [], x0 + sp / 2 - bw / 2
            while x < x0 + strip:
                left_x, right_x = max(x, x0), min(x + bw, x0 + strip)
                if right_x > left_x:
                    boxes.append((left_x, y + h - ph, right_x - left_x, ph))
                x += sp
            edges = [x0] + [e for b in boxes for e in (b[0], b[0] + b[2])] + [x0 + strip]
            gaps = [(edges[j], edges[j + 1]) for j in range(0, len(edges), 2) if edges[j + 1] - edges[j] > 1e-6]
            drawn.append({"layer": p, "boxes": boxes, "line": False, "anchor": y + h - ph / 2, "pieces": (bw, sp, y + h)})
            for other in others:
                fh = other.thickness * k
                drawn.append({"layer": other, "boxes": [(a, y + h - fh, b - a, fh) for a, b in gaps], "line": False, "anchor": y + h - fh / 2})
        else:
            for other in others:
                drawn.append({"layer": other, "boxes": [(x0, y, strip, h)], "line": False, "anchor": y + h / 2})
        chain.append((y, h, max(l.thickness for l in group)))
        y += h
    total_mm = sum(t for _y, _h, t in chain)
    return {"width": width, "legend": legend, "x0": x0, "strip": strip, "k": k, "top": TOP, "bottom": y, "drawn": drawn,
            "chain": chain, "total_mm": total_mm, "fills": fills}


def hit_boxes(layers, width=None, legend=None):
    """[(layer number, x, y, w, h)] of every box of every layer drawn, in the drawing's units -- what a click on the section opens (UI-003). A line is given a few units of height to be clicked."""
    out = []
    for d in _layout(layers, width, legend)["drawn"]:
        for (x, y, w, h) in d["boxes"]:
            out.append((d["layer"].number, x, y - 3 if d["line"] else y, w, 6 if d["line"] else h))
    return out


def render(layers, width=None, legend=None):
    """The SVG of a build-up at `width` units (None: the export's). `layers` are its model (contracts.Layer, dead_load_source.layers); `legend` None takes the legend mode under `LEGEND_BELOW`."""
    g = _layout(layers, width, legend)
    x0, strip, top, bottom = g["x0"], g["strip"], g["top"], g["bottom"]
    out = []
    for d in g["drawn"]:
        layer = d["layer"]
        for (x, y, w, h) in d["boxes"]:
            if d["line"]:
                _line(out, x, y, x + w, y, STROKE_COLOUR, 2.2)
            else:
                _rect(out, x, y, w, h, g["fills"][layer.number])
    # the frame of each band, so that the air above a line that fills reads as air
    for (y, h, _t) in g["chain"]:
        _rect(out, x0, y, strip, h, "none", MUTED, THIN)
    # UI-003: each band's height in the chain at the left where it fits, the whole height beside it
    chain_x = x0 - 30
    for (y, h, t) in g["chain"]:
        _line(out, chain_x, y, chain_x, y + h, TEXT_COLOUR, THIN)
        _tick(out, chain_x, y)
        if h >= SMALL:
            _text(out, chain_x - 5, y + h / 2 + SMALL / 3, _f(t), SMALL, anchor="end")
    if g["chain"]:
        _tick(out, chain_x, bottom)
        total_x = x0 - (62 if not g["legend"] else 52)
        _line(out, total_x, top, total_x, bottom, TEXT_COLOUR, THIN)
        _tick(out, total_x, top)
        _tick(out, total_x, bottom)
        _text(out, total_x - 4, (top + bottom) / 2 + TEXT / 3, _f(g["total_mm"]), TEXT, anchor="end")
    # under the strip: its metre, then the width and the spacing of each spaced layer where they fit
    below = bottom + 16
    _line(out, x0, below, x0 + strip, below, TEXT_COLOUR, THIN)
    _tick(out, x0, below)
    _tick(out, x0 + strip, below)
    _text(out, x0 + strip / 2, below + SMALL + 3, _f(STRIP), SMALL)
    below += SMALL + 10
    for d in g["drawn"]:
        if not d.get("pieces") or not d["boxes"]:
            continue
        bw, sp, _foot = d["pieces"]
        foot = bottom + 3          # the extension lines start under the strip: they never cross the layers below the pieces
        first = next((b for b in d["boxes"] if abs(b[2] - bw) < 1e-6), None)
        if first is None:
            continue
        a = first[0]
        line_y = below + 8
        if _fits(_f(d["layer"].width), bw + 30):
            _line(out, a, foot, a, line_y + 3)
            _line(out, a + bw, foot, a + bw, line_y + 3)
            _line(out, a, line_y, a + bw, line_y, TEXT_COLOUR, THIN)
            _text(out, a + bw / 2, line_y + SMALL + 3, _f(d["layer"].width), SMALL)
        if a + bw / 2 + sp <= x0 + strip and _fits("e = %s" % _f(d["layer"].spacing), sp):
            e_y = line_y + SMALL + 12
            _line(out, a + bw / 2, foot, a + bw / 2, e_y + 3)
            _line(out, a + bw / 2 + sp, foot, a + bw / 2 + sp, e_y + 3)
            _line(out, a + bw / 2, e_y, a + bw / 2 + sp, e_y, TEXT_COLOUR, THIN)
            _text(out, a + bw / 2 + sp / 2, e_y + SMALL + 3, "e = %s" % _f(d["layer"].spacing), SMALL)
            below = e_y + SMALL + 6
        else:
            below = line_y + SMALL + 6
    # the names: a column at the right joined by fanned lines, or the legend's numbers and list
    named = [d for d in g["drawn"]]
    if not g["legend"]:
        column = x0 + strip + NAMES_GAP
        height = len(named) * LINE
        start = max(top + TEXT / 2, (top + bottom) / 2 - height / 2 + LINE / 2)
        for n, d in enumerate(named):
            at = start + n * LINE
            _line(out, x0 + strip, d["anchor"], x0 + strip + 8, d["anchor"])
            _line(out, x0 + strip + 8, d["anchor"], column - 4, at - TEXT / 3)
            words = d["layer"].label or ""
            shown = _cut(words, NAMES - 4)
            out.append("<g><title>%s</title>" % svg_draw.escape(words))
            _text(out, column, at, shown, TEXT, anchor="start")
            out.append("</g>")
        view_h = max(below, start + len(named) * LINE) + 4
    else:
        for d in named:
            _line(out, x0 + strip, d["anchor"], x0 + strip + 6, d["anchor"])
            _text(out, x0 + strip + 9, d["anchor"] + SMALL / 3, str(d["layer"].number), SMALL, anchor="start")
        list_y = below + LINE
        for d in named:
            words = "%d  %s" % (d["layer"].number, d["layer"].label or "")
            out.append("<g><title>%s</title>" % svg_draw.escape(words))
            _text(out, LEFT_LEGEND - 60, list_y, _cut(words, g["width"] - (LEFT_LEGEND - 60) - 4), TEXT, anchor="start")
            out.append("</g>")
            list_y += LINE
        view_h = list_y + 4
    view_w = g["width"]
    head = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s" width="%s" height="%s">' % (_f(view_w), _f(view_h), _f(view_w), _f(view_h)))
    return head + "".join(out) + "</svg>\n"
