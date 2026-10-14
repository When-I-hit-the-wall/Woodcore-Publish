"""The figure of a connection, as SVG text: **the detail schema it is drawn on**, and over it the fasteners numbered as the report's tables number them, the rotation centre, the x/z pair, and -- when the forces are known -- the forces on every fastener, at one scale but for N/n and V/n where a moment would make them too short to see (docs/domain/connections.md §3.3quinquies).

⚠️ Since v0.74 the pieces are **not drawn here**. `schema_svg.body()` draws them, from the schema's own source, and this module adds the layers that belong to a fastener group: the numbered dots, the members' axes, the centre, the pair of axes, the moment's arc, the legend and the arrows. That is what makes one joint one drawing (section 2, rule 1) -- and it is also what `connector_svg.pattern_of` now goes through, so the connector's pattern and the connection's figure are the same detail with different layers on it.

One drawing serves both places it is seen. Woodcore's window shows it live while a connection is edited, and export writes it to data/connections/<id>.svg, which show-polar-moment sets in the report -- so the figure the engineer placed the fasteners on is the figure the checker reads. That is why it is built as plain text here, with no Qt: export_all.py draws it too, without a window.

The forces are the one part not known here: N, V and M are given in the report. So the exported figure carries a marker, FORCES_MARK, where lib/calc-engine.typ inserts the arrows for the forces of its call, from the placement data meta() exports with the connection, and a second one, NOTE_MARK, in the legend's last line, where it says which of N/n and V/n had to be drawn longer than their scale; Woodcore inserts its preview's arrows and note at the same places, by force_arrows() and share_note() below. The two draw by the same rules -- a line, a polygon head, the resultant's label, the shares' minimum length -- and a change to one is a change to make to the other.

It is kept to what both renderers read alike. QtSvg implements SVG Tiny 1.2, which has no <marker> and no arc command, and reads no CSS: arrowheads are polygons, the moment's arc is a polyline, and every colour and stroke is a presentation attribute. Coordinates are the SVG's own, y down, in mm: a point of the connection (x, z) sits at x·e_x + z·e_z, e_x being the reference member's direction on the drawing and e_z that direction turned a quarter clockwise.
"""

import math
from xml.sax.saxutils import escape

from domains import connection, schema_svg
from i18n import strings

# The detail's own ink, so that the pieces the schema draws and the layers drawn over them are one figure.
MEMBER_FILLS = schema_svg.ELEMENT_FILLS
MEMBER_OPACITY = schema_svg.ELEMENT_OPACITY
MEMBER_STROKE = schema_svg.ELEMENT_STROKE
FASTENER_FILL = schema_svg.CONNECTOR_FILL
TEXT_COLOR = schema_svg.TEXT_COLOR
MUTED = schema_svg.MUTED
AXIS_COLOR = "#333333"
HIGHLIGHT = "#e67e22"
COLOR_N = "#1f5fbf"
COLOR_V = "#c0392b"
COLOR_M = "#2e8b57"
COLOR_F = "#f2c200"
COLOR_F_EDGE = "#6b5200"

# Where the arrows of the forces go: the report's (lib/calc-engine.typ) or Woodcore's preview (force_arrows).
FORCES_MARK = "<!-- forces -->"
# Where the legend says which of N/n and V/n are drawn longer than their scale (share_note), inside the text element of its last line.
NOTE_MARK = "<!-- note -->"

# How thick an arrow is drawn, in strokes. An action -- N/n, V/n, the force from M, and the moment's own arc -- is always the thinner, and the resultant they add up to the heavier, outlined besides: one pair of constants, tied to each other, so that the two cannot drift apart and the resultant cannot end up the thinner of the two.
ACTION_WIDTH = 1.6
RESULTANT_WIDTH = 1.5 * ACTION_WIDTH

# Every arrow is drawn at the one scale, so that the three a fastener carries add up to the resultant beside them, as they do in the calculation. N/n and V/n can then be too short to read -- an N/n of 0.06 kN beside an F of 10.7 kN is 1/170 of its length, lost under the fastener's dot -- but it is drawn all the same, at the length it has: leaving it out would break the same addition that stretching it broke, by the very length left out. A share shorter than this many arrowheads -- about the fastener's own dot, so hidden under it -- is named with its value in the legend instead (share_note).
SHARE_SHOWN = 0.9
# A fastener drawn at its own diameter (a connector's pattern, v0.75) is never smaller than this share of the drawing's own marker radius: a small nail on a 400 mm detail would otherwise be a speck. Where the floor bites the pattern says so under the drawing.
DOT_FLOOR_SHARE = 0.6
# The shares' heads, smaller than the resultants': an arrow held to its minimum length would otherwise be mostly head.
SHARE_HEAD = 0.7
# The longest note the legend has to make room for, in the language the figure is drawn in: the
# prefix is the glossary's, and what follows it the widest a pair of values can be.
NOTE_VALUES = "N/n = 00000.00 kN, V/n = 00000.00 kN"


def _note_longest(lang):
    return strings.text("figure.too_small", lang) + NOTE_VALUES

# The moment's arc, on the drawing: from south-west to south-east, where 90 degrees is south and a falling angle turns anticlockwise, as a positive moment does.
MOMENT_SPAN = (135.0, 45.0)
# What it keeps clear of the force arrows, in fonts, and the fraction of the widest member it is capped at: a group whose arrows reach further than its members are wide would otherwise push the arc, and the frame drawn around it, far past them. At the cap the arc may cross an arrow again.
MOMENT_CLEAR = 0.8
MOMENT_MAX = 0.95

# The drawing's size on paper, at most, whichever side is longer.
PAPER_MM = 160.0


def _f(value):
    """A coordinate as short SVG text: two decimals at most, trailing zeros dropped."""
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def _over_white(colour, opacity):
    """A fill as it comes out on the white page, once its opacity is applied -- what a halo drawn behind a label on that band must be."""
    channels = (int(colour[i:i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{round(opacity * c + (1 - opacity) * 255):02x}" for c in channels)


def _pt(point):
    return f"{_f(point[0])},{_f(point[1])}"


def _unit(degrees):
    """A direction on the drawing, clockwise from the page's right, as an SVG vector (y down)."""
    a = math.radians(degrees)
    return (math.cos(a), math.sin(a))


def _add(p, q, k=1.0):
    return (p[0] + k * q[0], p[1] + k * q[1])


def _dot(p, q):
    return p[0] * q[0] + p[1] * q[1]


def _quarter(u):
    """A direction turned a quarter clockwise on the drawing: e_x to e_z."""
    return (-u[1], u[0])


def _placed(point, ex, ez):
    return (point[0] * ex[0] + point[1] * ez[0], point[0] * ex[1] + point[1] * ez[1])


def _moment_radius(points, center, arrow, font, w_max):
    """How far from the rotation centre the moment's arc runs, so that it clears the force arrows the report draws later. An arrow leaves its fastener in any direction and reaches `arrow`, its label a little further, so every fastener claims a disc of that radius; the arc is set beyond the farthest point those discs reach along the directions it spans (MOMENT_SPAN), with MOMENT_CLEAR of a font to spare. It is never shorter than 0.45 of the widest member, so that a small group still shows a readable arc, and never longer than MOMENT_MAX of it: a group whose arrows reach further than that would otherwise push the arc, and the whole frame, far past the members -- there the arc may cross an arrow again."""
    reach = arrow + 1.2 * font  # the arrow and the label at its tip
    needed = 0.45 * w_max
    if center is not None:
        start, stop = MOMENT_SPAN
        steps = 18
        for k in range(steps + 1):
            u = _unit(start + (stop - start) * k / steps)
            for p in points:
                q = (p[0] - center[0], p[1] - center[1])
                across = abs(q[0] * u[1] - q[1] * u[0])  # how far the fastener sits from this ray
                if across < reach:
                    # where the disc around it ends, along the ray
                    needed = max(needed, _dot(q, u) + math.sqrt(reach * reach - across * across) + MOMENT_CLEAR * font)
    return min(needed, MOMENT_MAX * w_max)


# --- The layout: everything the drawing and the report's arrows need ------------

EMPTY_SCHEMA = {"elements": [], "connectors": [], "aids": [], "dimensions": []}


def marker_points(detail, marker_ids):
    """The (x, z) of the fasteners `marker_ids` names -- the schema's connector markers and its points ticked «connecteur» (`connection.fastener_places`, v0.77) -- in the order it names them. One the schema no longer carries is skipped -- which is what lets a connection whose schema was edited still be opened and repaired, the export naming it in a warning (docs/decisions.md §13, the v0.33 rule)."""
    places = connection.fastener_places(detail)
    return [places[mid] for mid in marker_ids or [] if mid in places]


def missing_markers(detail, marker_ids):
    """The ids of `marker_ids` the schema carries neither as a marker nor as a point ticked «connecteur», in order."""
    places = connection.fastener_places(detail)
    return [mid for mid in (marker_ids or []) if mid not in places]


def _band_widths(detail, positions=None):
    """Every linear element's drawn width, in mm -- what the moment's arc and the arrows are sized against, as the members' own widths were. `positions` resolve a side that follows its position (v0.75), exactly as the schema's own drawing resolves it."""
    from domains import schema as schema_model
    return [schema_model.element_width(e, positions) for e in (detail or {}).get("elements", [])
            if schema_model.element_kind(e) == "linear"]


def layout(source, geometry=None, detail=None, positions=None):
    """Where everything goes, for render() and for meta(): the schema's own drawing, and on top of it what belongs to this connection -- the fasteners it carries, the rotation centre, the x/z pair and the room the force arrows need.

    ⚠️ Since v0.74 the pieces are **not laid out here**. `detail` is the schema source (section 3.3decies) and `schema_svg.layout()` places it; this function adds the connection's own layers and widens the frame around them. That is what makes the figure the engineer drew the figure the checker reads, with no second drawing of one joint to keep in step.

    A draft is laid out as far as it goes: a connection with no schema yet, or none of whose markers resolve, still returns a frame.

    `positions` are the position records the schema's elements resolve their section and label against (v0.75) -- the export's own, or `connector.known_positions` in Woodcore -- so this figure's pieces are the width and carry the label «T001 C24 100/200» the schema's own figure does.

    The schema is laid out in the **source** language on purpose. Nothing it draws is translated today, and `meta()` -- the placement data the report's arrows are computed from -- has to be one set of numbers for all three languages, since data/connections.json carries one `figure` block and not three.
    """
    from domains import connection as connection_model
    if geometry is None:
        geometry = connection_model.analyse(source, detail)
    base = schema_svg.layout(detail or EMPTY_SCHEMA, positions=positions, use_crop=False)
    points = [tuple(p) for p in geometry["points"]]
    center = tuple(geometry["center"]) if geometry["center"] is not None else None
    gravity = tuple(geometry["centroid"]) if geometry["centroid"] is not None else None

    # The schema's own ink: one detail, one set of sizes, so the fasteners the connection numbers are the size of the markers the schema drew.
    font, stroke = base["font"], base["stroke"]
    widths = _band_widths(detail, positions)
    w_max = max(widths) if widths else max(base["size"] / 6.0, 1.0)

    if len(points) >= 2:
        nearest = min(math.hypot(p[0] - q[0], p[1] - q[1]) for i, p in enumerate(points) for q in points[i + 1:])
        radius = max(min(base["size"] / 95, 0.3 * nearest), base["size"] / 400)
        arrow = min(max(0.9 * nearest, 0.12 * w_max), 0.35 * w_max)
    else:
        radius = base["radius"]
        arrow = 0.3 * w_max

    xs = [base["bbox"][0], base["bbox"][2]]
    ys = [base["bbox"][1], base["bbox"][3]]
    # The frame keeps room for the longest force arrow around every fastener and for its label, so the report's arrows, drawn later, never leave it.
    margin = arrow + 1.4 * font
    for p in points:
        xs += [p[0] - margin, p[0] + margin]
        ys += [p[1] - margin, p[1] + margin]

    moment_radius = _moment_radius(points, center, arrow, font, w_max)
    if center is not None:
        reach_m = moment_radius + 1.4 * font
        xs += [center[0] - reach_m, center[0] + reach_m]
        ys += [center[1] - reach_m, center[1] + reach_m]

    # The x/z pair, drawn at the start of the reference member's element, as a member's local axes are drawn in RFEM. x and z are the schema's own now, so the pair says which way the coordinates of the positions table run.
    ex, ez = (1.0, 0.0), (0.0, 1.0)
    triad = 2.4 * font
    triad_origin = _triad_origin(detail, geometry, base, font)
    if triad_origin is not None:
        for tip in (_add(triad_origin, ex, triad + font), _add(triad_origin, ez, triad + font)):
            xs.append(tip[0])
            ys.append(tip[1])

    return {
        "geometry": geometry,
        "source": source,
        "detail": detail,
        "base": base,
        "axes": geometry.get("axis", []),
        "points": points,
        "center": center,
        "centroid": gravity,
        "bbox": (min(xs), min(ys), max(xs), max(ys)),
        "size": base["size"],
        "font": font,
        "stroke": stroke,
        "radius": radius,
        "arrow": arrow,
        "head": 0.8 * font,
        "ex": ex,
        "ez": ez,
        "moment_radius": moment_radius,
        "triad_origin": triad_origin,
        "triad": triad,
        "member_lines": _member_lines(source, detail),
    }


def _triad_origin(detail, geometry, base, font):
    """Where the x/z pair is drawn: a little in from the start of the reference member's element. None where that element cannot be found, which is a draft naming nothing yet."""
    from domains import schema as schema_model
    element = _reference_element(detail, geometry)
    if element is None:
        x0, y0, _x1, _y1 = base["bbox"]
        return (x0 + 1.5 * font, y0 + 2.0 * font)
    points = [tuple(p) for p in element.get("points", [])]
    if not points:
        return None
    direction = schema_model.element_direction(element) or (1.0, 0.0)
    return _add(points[0], direction, 1.0 * font)


def _reference_element(detail, geometry):
    """The element of the member the report calls the Bezugselement, or None."""
    from domains import schema as schema_model
    ids = geometry.get("elements", [])
    r = geometry.get("reference", 0)
    if not ids or not 0 <= r < len(ids) or not ids[r]:
        return None
    return schema_model.entry_of(detail or {}, "elements", ids[r])


def _member_lines(source, detail):
    """Each member's axis, as the two ends of the line drawn dashed along it.

    A schema may draw more pieces than the joint has members -- a stiffener, a plate, a neighbouring beam -- so the connection marks the ones it calls its members. That is also the line the angles theta_(r,j) and the force-grain angles are measured along, which is worth showing on the figure the angles are read off.
    """
    from domains import schema as schema_model
    lines = []
    for member in source.get("members", []):
        element = schema_model.entry_of(detail or {}, "elements", member.get("element", ""))
        if element is None or schema_model.element_kind(element) != "linear":
            continue
        points = [tuple(p) for p in element.get("points", [])]
        if len(points) >= 2:
            lines.append((points[0], points[-1]))
    return lines


def meta(drawing):
    """What the report needs to draw the forces on the exported figure: the fasteners' positions in its coordinates, the directions of x and z there, the length of the longest arrow and the sizes of a head, a stroke and a label -- stored with the connection in data/connections.json.

    ⚠️ Its shape has not changed since v0.32, and deliberately: `lib/calc-engine.typ`'s `fastener-arrows` reads exactly these keys, and `tests/test_arrows.py` compares what it draws with what `force_arrows` below draws, element by element. The move to a schema changed where the coordinates come from and nothing about what they are -- x and z are now the schema's own, so `ex` and `ez` are the unit vectors rather than the reference member's direction on a turned page.
    """
    def r4(v):
        return round(v, 4) + 0.0

    return {
        "points": [[r4(x), r4(y)] for x, y in drawing["points"]],
        "ex": [r4(drawing["ex"][0]), r4(drawing["ex"][1])],
        "ez": [r4(drawing["ez"][0]), r4(drawing["ez"][1])],
        "arrow": r4(drawing["arrow"]),
        "head": r4(drawing["head"]),
        "stroke": r4(drawing["stroke"]),
        "font": r4(drawing["font"]),
    }


# --- Arrows ---------------------------------------------------------------------
# The same rules as lib/calc-engine.typ's fastener-arrows, which draws the report's.

def _arrow(p, q, color, width, head, edge=None):
    """A straight arrow from p to q: a line and a polygon head. `edge` outlines it -- the yellow resultant needs one on white."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    length = math.hypot(dx, dy)
    if length < 1e-9:
        return ""
    ux, uy = dx / length, dy / length
    h = min(head, 0.6 * length)
    base = (q[0] - h * ux, q[1] - h * uy)
    side = (-uy * 0.37 * h, ux * 0.37 * h)
    head_points = f"{_pt(q)} {_pt(_add(base, side))} {_pt(_add(base, side, -1))}"
    parts = []
    if edge:
        parts.append(f'<line x1="{_f(p[0])}" y1="{_f(p[1])}" x2="{_f(base[0])}" y2="{_f(base[1])}" stroke="{edge}" stroke-width="{_f(width * 1.7)}"/>')
    parts.append(f'<line x1="{_f(p[0])}" y1="{_f(p[1])}" x2="{_f(base[0])}" y2="{_f(base[1])}" stroke="{color}" stroke-width="{_f(width)}"/>')
    edge_attr = f' stroke="{edge}" stroke-width="{_f(width * 0.35)}"' if edge else ""
    parts.append(f'<polygon points="{head_points}" fill="{color}"{edge_attr}/>')
    return "".join(parts)


def _moment_parts(rows, n_share, v_share):
    """What the moment alone puts on each fastener: its force less the shares of N and V, which every fastener carries alike. That is M·r_i/I_p at right angles to the lever arm -- the V_b,i of bauforumstahl's Arbeitshilfe 2.9, Bild 3."""
    return [(r["fx"] - n_share[0] - v_share[0], r["fz"] - n_share[1] - v_share[1]) for r in rows]


def _shares(figure, rows, n_share, v_share):
    """The common scale k (drawing units per kN, the longest arrow `figure["arrow"]` long) and N/n and V/n as they are drawn: for each that is not zero, its vector (x, z) and size in kN, its colour, its length on the drawing -- k times its size, always, so that the arrows add up -- and whether that length can be made out at all beside the fastener's dot (SHARE_SHOWN)."""
    sizes = [math.hypot(*n_share), math.hypot(*v_share)]
    # every arrow the figure carries, so that one scale fits them all: a resultant can be shorter than the forces it adds up, where they oppose each other
    largest = max([r["f"] for r in rows] + sizes + [math.hypot(*m) for m in _moment_parts(rows, n_share, v_share)] + [0.0])
    if largest <= 0:
        return 0.0, []
    k = figure["arrow"] / largest
    shortest = SHARE_SHOWN * figure["head"]
    shares = []
    for name, vector, size, colour in (("N/n", n_share, sizes[0], COLOR_N), ("V/n", v_share, sizes[1], COLOR_V)):
        if size > 0:
            shares.append({"name": name, "vector": vector, "size": size, "colour": colour,
                           "length": k * size, "hidden": k * size < shortest})
    return k, shares


def force_arrows(figure, rows, n_share, v_share):
    """The arrows of the forces, as SVG elements for FORCES_MARK: on every fastener the resultant F_i (yellow, labelled F1, F2, …), its share of N (blue), its share of V (red) and the force the moment puts on it (green, M·r_i/I_p at right angles to the lever arm), at one scale -- the longest of them `figure["arrow"]` long, so an F of 20 kN is twice an N/n of 10 kN -- every one at its true length, so that the three actions on a fastener add up to its resultant; one too small to make out is drawn all the same and named in the legend with its value (_shares, share_note). The actions are drawn over the resultants, which would hide them. `figure` is meta()'s dictionary; `rows` connection.fastener_forces()'s; `n_share`, `v_share` the forces N/n and V/n as (x, z) in kN."""
    k, shares = _shares(figure, rows, n_share, v_share)
    if k <= 0:
        return ""
    ex, ez = figure["ex"], figure["ez"]
    stroke, head, font = figure["stroke"], figure["head"], figure["font"]

    def step(vector, scale):
        return (scale * (vector[0] * ex[0] + vector[1] * ez[0]), scale * (vector[0] * ex[1] + vector[1] * ez[1]))

    parts, labels = [], []
    for p, row in zip(figure["points"], rows):
        q = _add(p, step((row["fx"], row["fz"]), k))
        parts.append(_arrow(p, q, COLOR_F, RESULTANT_WIDTH * stroke, head, COLOR_F_EDGE))
        length = math.hypot(q[0] - p[0], q[1] - p[1])
        if length > 1e-9:
            ux, uy = (q[0] - p[0]) / length, (q[1] - p[1]) / length
            at = (q[0] + 0.6 * font * ux, q[1] + 0.6 * font * uy + 0.22 * font)
            labels.append(f'<text x="{_f(at[0])}" y="{_f(at[1])}" font-family="Arial" font-size="{_f(0.62 * font)}" font-weight="bold" fill="{COLOR_F_EDGE}" text-anchor="middle">F{row["nr"]}</text>')
    for p, moment in zip(figure["points"], _moment_parts(rows, n_share, v_share)):
        parts.append(_arrow(p, _add(p, step(moment, k)), COLOR_M, ACTION_WIDTH * stroke, SHARE_HEAD * head))
    for share in shares:
        d = step(share["vector"], k)
        for p in figure["points"]:
            parts.append(_arrow(p, _add(p, d), share["colour"], ACTION_WIDTH * stroke, SHARE_HEAD * head))
    return "".join(parts + labels)


def share_note(figure, rows, n_share, v_share, lang=strings.SOURCE_LANGUAGE):
    """The legend's last line, for NOTE_MARK: which of N/n and V/n come out too small to make out at the figure's scale, with their values -- "Zu klein zum Erkennen: N/n = 0.06 kN, V/n = 0.31 kN" -- or nothing when both can be read off the drawing."""
    _k, shares = _shares(figure, rows, n_share, v_share)
    hidden = [f"{s['name']} = {_f(s['size'])} kN" for s in shares if s["hidden"]]
    return strings.text("figure.too_small", lang) + ", ".join(hidden) if hidden else ""


# --- The drawing ------------------------------------------------------------------

def render(drawing, forces=None, highlight=None, show_moment=True, lang=strings.SOURCE_LANGUAGE,
           legend=True, show_center=True, mark=None):
    """The connection's figure as an SVG document: the schema's own drawing, and on it this connection's fasteners, rotation centre, x/z pair, moment arc, force arrows and legend.

    `forces` -- {"N": kN, "V": kN, "M": kNm}, Woodcore's trial values -- draws their arrows in place of FORCES_MARK and writes the legend's note in place of NOTE_MARK; without them both markers stay, for the report to fill. `highlight` is the 0-based index of a fastener to ring (the row selected in Woodcore); `mark` a (collection, id) pair of the schema to ring, which is what the *Connecteurs* tab lights while an element is chosen.

    `legend` and `show_center` are off only for the *connector's* own drawing of the same fastener group (connector_svg.pattern_of): a connector carries no N, V or M and turns about nothing, so a legend of force arrows and a rotation centre would answer a question that figure does not ask. Both default to what a connection has always drawn.
    """
    geometry = drawing["geometry"]
    directions = (drawing["source"].get("directions") or {"N": 0, "V": 90})
    return overlay(
        drawing["base"], drawing["points"], lang=lang, highlight=highlight, mark=mark,
        legend=legend, show_center=show_center, show_moment=show_moment,
        center=drawing["center"], centroid=drawing["centroid"],
        triad=(drawing["triad_origin"], drawing["triad"]) if drawing["triad_origin"] is not None else None,
        member_lines=drawing["member_lines"], bbox=drawing["bbox"],
        font=drawing["font"], stroke=drawing["stroke"], radius=drawing["radius"],
        moment_radius=drawing["moment_radius"],
        forces=forces, geometry=geometry, directions=directions, figure=meta(drawing),
    )


def overlay(base, points, lang=strings.SOURCE_LANGUAGE, highlight=None, mark=None, legend=True,
            show_center=True, show_moment=True, center=None, centroid=None, triad=None,
            member_lines=(), bbox=None, font=None, stroke=None, radius=None, moment_radius=0.0,
            forces=None, geometry=None, directions=None, figure=None, dot_diameter=None, note=None):
    """The schema `base` draws, with a fastener group's own layers over it, as one SVG document.

    It is the one routine both drawings go through -- a connection's figure (render, above) and a connector's pattern (connector_svg.pattern_of) -- so that the detail under them cannot come out two different ways. Everything optional is off by default: a caller that wants only the numbered fasteners on a schema passes the points and nothing else.

    `dot_diameter` (mm) draws the fasteners at their own size -- the connector's pattern knows its d, a detail being at its real size (v0.75) -- never below a floor of legibility; `note` is a line written under the drawing, which is where the pattern says the floor bit. A connection's own figure passes neither: its dot radius is part of the placement data the report's arrows are drawn with (`SHARE_SHOWN`), and must not move.
    """
    font = font if font is not None else base["font"]
    stroke = stroke if stroke is not None else base["stroke"]
    radius = radius if radius is not None else base["radius"]
    if dot_diameter:
        radius = max(float(dot_diameter) / 2.0, DOT_FLOOR_SHARE * base["radius"])
    directions = directions or {"N": 0, "V": 90}

    legend_rows = []
    if legend:
        legend_rows = [
            ("N", COLOR_N, "N/n", strings.text("figure.normal_force_per_fastener", lang), float(directions.get("N", 0))),
            ("V", COLOR_V, "V/n", strings.text("figure.shear_force_per_fastener", lang), float(directions.get("V", 0))),
        ]
        if show_moment:
            legend_rows.append(("FM", COLOR_M, "F_M", strings.text("figure.moment_force_per_fastener", lang), 0.0))
        legend_rows.append(("F", COLOR_F, "F", strings.text("figure.resultant_per_fastener", lang), 0.0))
        if show_moment:
            legend_rows.append(("M", COLOR_M, "M", strings.text("figure.moment_about_centre", lang), None))

    pad = 1.2 * font
    note_size = 0.7 * font
    legend_width = (max(5.0 * font + max(len(meaning) for *_, meaning, _d in legend_rows) * 0.5 * 0.8 * font,
                        len(_note_longest(lang)) * 0.5 * note_size) if legend_rows else 0.0)
    min_x, min_y, max_x, max_y = bbox if bbox is not None else base["bbox"]
    left = min_x - pad
    right = max(max_x + pad, left + 0.6 * font + legend_width)
    # the colours' lines, then the note's
    legend_height = (len(legend_rows) * 1.45 * font + 1.2 * font + 0.4 * font) if legend_rows else 0.0
    top = min_y - pad - legend_height
    bottom = max_y + pad + (1.3 * note_size if note else 0.0)
    view_w, view_h = right - left, bottom - top
    scale = PAPER_MM / max(view_w, view_h)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="{_f(left)} {_f(top)} {_f(view_w)} {_f(view_h)}" '
        f'width="{_f(view_w * scale)}mm" height="{_f(view_h * scale)}mm">',
        f'<rect x="{_f(left)}" y="{_f(top)}" width="{_f(view_w)}" height="{_f(view_h)}" fill="#ffffff"/>',
    ]

    def text(point, content, size_, color=TEXT_COLOR, anchor="start", bold=False, rotate=None, raw=False, halo=None):
        weight = ' font-weight="bold"' if bold else ""
        transform = f' transform="rotate({_f(rotate)} {_f(point[0])} {_f(point[1])})"' if rotate is not None else ""
        body = content if raw else escape(content)
        common = f'x="{_f(point[0])}" y="{_f(point[1])}" font-family="Arial" font-size="{_f(size_)}" text-anchor="{anchor}"{weight}{transform}'
        # SVG Tiny has no paint-order, so a halo is the text drawn once more underneath, stroked in the colour of its ground -- plan_svg.py does the same over the architect's plan.
        if halo is not None:
            out.append(f'<text {common} fill="{halo[0]}" stroke="{halo[0]}" stroke-width="{_f(halo[1])}" stroke-linejoin="round">{body}</text>')
        out.append(f'<text {common} fill="{color}">{body}</text>')

    def line(p, q, color, width, dash=None):
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        out.append(f'<line x1="{_f(p[0])}" y1="{_f(p[1])}" x2="{_f(q[0])}" y2="{_f(q[1])}" stroke="{color}" stroke-width="{_f(width)}"{dash_attr}/>')

    # The detail itself: the schema's own aids, pieces, labels and dimensions, drawn by the schema's own routine so that this figure and «Schémas» cannot disagree about one joint. Its markers are left out -- this figure numbers the fasteners IT carries, 1, 2, 3 ... in the order the report's tables number them.
    schema_svg.body(out, base, highlight=mark, markers=False)

    # The members' axes: which of the schema's pieces this calculation calls its members, and the line theta and the force-grain angles are measured along.
    dash = f"{_f(48 * stroke)},{_f(12 * stroke)},{_f(4 * stroke)},{_f(12 * stroke)}"
    for a, b in member_lines:
        reach = math.hypot(b[0] - a[0], b[1] - a[1])
        if reach < 1e-9:
            continue
        u = ((b[0] - a[0]) / reach, (b[1] - a[1]) / reach)
        line(_add(a, u, -0.04 * reach), _add(b, u, 0.04 * reach), MEMBER_STROKE, stroke, dash)

    # The moment's arc, over the detail and under the fasteners: the layout set it clear of the force arrows, and where its radius was capped it may still reach a label, which is then read over it.
    if center is not None and show_moment:
        (start, stop), steps = MOMENT_SPAN, 24
        arc = [_add(center, _unit(start + (stop - start) * k / steps), moment_radius) for k in range(steps + 1)]
        a = math.radians(stop)
        tangent = (math.sin(a), -math.cos(a))  # the direction of travel, the angle decreasing: anticlockwise on the drawing
        arc[-1] = _add(arc[-1], tangent, -0.7 * font)
        out.append(f'<polyline points="{" ".join(_pt(p) for p in arc)}" fill="none" stroke="{COLOR_M}" stroke-width="{_f(ACTION_WIDTH * stroke)}"/>')
        out.append(_arrow(arc[-1], _add(center, _unit(stop), moment_radius), COLOR_M, ACTION_WIDTH * stroke, 0.9 * font))
        text(_add(arc[0], (-0.5 * font, 0.35 * font)), "M", 1.0 * font, COLOR_M, "end", bold=True)

    # The x/z pair, at the start of the reference member's element.
    if triad is not None:
        o, t = triad
        for direction, name in (((1.0, 0.0), "x"), ((0.0, 1.0), "z")):
            out.append(_arrow(o, _add(o, direction, t), AXIS_COLOR, 1.4 * stroke, 0.7 * font))
            text(_add(_add(o, direction, t + 0.7 * font), (0, 0.3 * font)), name, 0.8 * font, AXIS_COLOR, "middle", bold=True)

    # The fasteners, numbered in the order the report's tables list them.
    for i, (x, y) in enumerate(points):
        if highlight == i:
            out.append(f'<circle cx="{_f(x)}" cy="{_f(y)}" r="{_f(2.0 * radius)}" fill="none" stroke="{HIGHLIGHT}" stroke-width="{_f(3 * stroke)}"/>')
        out.append(f'<circle cx="{_f(x)}" cy="{_f(y)}" r="{_f(radius)}" fill="{FASTENER_FILL}" stroke="#ffffff" stroke-width="{_f(0.6 * stroke)}"/>')
        text((x + 1.15 * radius, y - 1.15 * radius), str(i + 1), 0.62 * font, TEXT_COLOR)

    # The rotation centre, the centroid beside it when the engineer fixed a different point.
    if center is not None and show_center:
        if centroid is not None and math.hypot(center[0] - centroid[0], center[1] - centroid[1]) > 1e-6:
            g = 0.45 * font
            line((centroid[0] - g, centroid[1] - g), (centroid[0] + g, centroid[1] + g), MUTED, 1.5 * stroke)
            line((centroid[0] - g, centroid[1] + g), (centroid[0] + g, centroid[1] - g), MUTED, 1.5 * stroke)
        rc = max(1.7 * radius, 0.45 * font)
        out.append(f'<circle cx="{_f(center[0])}" cy="{_f(center[1])}" r="{_f(rc)}" fill="#ffffff" fill-opacity="0.8" stroke="#000000" stroke-width="{_f(1.6 * stroke)}"/>')
        line((center[0] - rc, center[1]), (center[0] + rc, center[1]), "#000000", 1.2 * stroke)
        line((center[0], center[1] - rc), (center[0], center[1] + rc), "#000000", 1.2 * stroke)

    # The forces: Woodcore's trial ones here, the report's inserted at the marker -- and with them the legend's note, at its own marker.
    forces_note = None
    if forces is not None and geometry is not None and geometry["n"] > 0:
        forces_note = ""
        try:
            rows, _governing = connection.fastener_forces(geometry, directions, forces["N"], forces["V"], forces["M"])
        except ValueError:
            rows = []
        if rows:
            n_count = geometry["n"]
            shares = []
            for key in ("N", "V"):
                a = math.radians(float(directions.get(key, 0)))
                shares.append((forces[key] / n_count * math.cos(a), forces[key] / n_count * math.sin(a)))
            out.append(force_arrows(figure, rows, shares[0], shares[1]))
            forces_note = share_note(figure, rows, shares[0], shares[1], lang)
    elif legend_rows:
        out.append(FORCES_MARK)

    # The legend: the colours, and N and V drawn in the directions they act in, so the figure says so even without forces.
    y_line = top + 1.25 * font
    x0 = left + 0.6 * font
    for key, color, symbol, meaning, direction in legend_rows:
        middle = (x0 + 1.1 * font, y_line - 0.3 * font)
        if key == "M":
            # the moment as it is drawn on the figure, a short arc turning anticlockwise, so that it is not read as one more straight force
            (start, stop), steps = MOMENT_SPAN, 8
            centre, r_leg = (middle[0], middle[1] - 0.55 * font), 0.95 * font
            arc = [_add(centre, _unit(start + (stop - start) * t / steps), r_leg) for t in range(steps + 1)]
            out.append(f'<polyline points="{" ".join(_pt(p) for p in arc)}" fill="none" stroke="{color}" stroke-width="{_f(ACTION_WIDTH * stroke)}"/>')
            out.append(_arrow(arc[-2], arc[-1], color, ACTION_WIDTH * stroke, 0.45 * font))
        else:
            d = _unit(direction)
            p, q = _add(middle, d, -0.8 * font), _add(middle, d, 0.8 * font)
            out.append(_arrow(p, q, color, (RESULTANT_WIDTH if key == "F" else ACTION_WIDTH) * stroke, 0.55 * font, COLOR_F_EDGE if key == "F" else None))
        text((x0 + 2.6 * font, y_line), symbol, 0.8 * font, COLOR_F_EDGE if key == "F" else color, bold=True)
        text((x0 + 5.0 * font, y_line), meaning, 0.8 * font, TEXT_COLOR)
        y_line += 1.45 * font
    # The note on the shares drawn longer than their scale: empty until the forces are known, the report filling it at its marker.
    if legend_rows:
        text((x0, y_line - 0.15 * font), NOTE_MARK if forces_note is None else escape(forces_note), note_size, TEXT_COLOR, raw=True)
    # A line under the drawing, where the pattern says a fastener is drawn larger than it is (v0.75).
    if note:
        text((left + 0.6 * font, bottom - 0.45 * note_size), note, note_size, TEXT_COLOR)

    out.append("</svg>")
    return "\n".join(out) + "\n"
