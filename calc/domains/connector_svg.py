"""A connector's two drawings, as SVG text: the fastener pattern, and the section through the joint (docs/domain/connectors.md §3.3nonies).

**The pattern** is the drawing of «Moments polaires»: the members meeting at the node, their sections, and the fasteners numbered in their order. It is not redrawn here -- `connection_svg.layout()` and `render()` are called with the connector's own geometry, which is field for field a connection source's, so there is one drawing of a fastener group in this project and not two.

**The section** is new, and it is the figure the engineer's own workbook puts at the top of each sheet: the pieces the fastener passes through, side by side along its axis, with the shear planes between them. Four configurations, one drawing:

    Holz-Holz einschnittig       [ t_1 ][ t_2 ]                 one shear plane
    Holz-Holz zweischnittig      [ t_1 ][ t_2 ][ t_1 ]          two
    Stahl-Holz, Bleche aussen    [ ▪ ][ t_2 ][ ▪ ]              two, at the plates
    Stahl-Holz, Schlitzbleche    [ t_1 ][ ▪ ][ t_2 ][ ▪ ][ t_1 ]  A at the outer plates, B inside

The widths are proportional to the real thicknesses as soon as they are known, and the dimensions are written with their values; while a thickness is still open the pieces are drawn equal and the dimension keeps its letter -- t_1, t_2, A, B, d -- which is what lets Woodcore show the figure before anything has been typed.

Kept to what QtSvg (SVG Tiny 1.2) and resvg read alike, like every other drawing here: no marker, no CSS, no arc command, a text's halo is the text drawn twice, a subscript is a second `<text>` set smaller and lower, and `font-family` names one bare family. Text is measured against `statics_svg.ARIAL_WIDTHS`, so the frame fits the words it actually carries.
"""

import math

from domains import svg_draw  # the one writer of an SVG number and text (D6)
from domains import svg_text  # the one plain text writer (ARCH-004)
from domains import schema_svg, statics_svg
from i18n import strings

# The ink and the fills, the schema's own so that every drawing of one joint in this project -- the detail, the
# pattern and the section -- looks like one set. ⚠️ Read off `schema_svg` and not off `connection_svg`, which
# carries the same values: `connection_svg` imports `connection`, which imports `schema`, which imports this
# module's own caller -- taking the constants from there closed a cycle that broke on two of five import orders.
TIMBER_FILL = schema_svg.ELEMENT_FILLS[0]
TIMBER_FILL_ALT = schema_svg.ELEMENT_FILLS[1]
TIMBER_STROKE = schema_svg.ELEMENT_STROKE
STEEL_FILL = svg_draw.colour("aid")
STEEL_STROKE = svg_draw.colour("ink-soft")
FASTENER_FILL = schema_svg.CONNECTOR_FILL
TEXT_COLOR = schema_svg.TEXT_COLOR
MUTED = schema_svg.MUTED

FONT = svg_draw.FONT
GROUND = svg_draw.colour("ground")

# The drawing's own units: the joint is normalised to this width, so a 60 mm joint and a 600 mm one come out the same figure (statics_svg's rule).
WIDTH = 1000.0
PIECE_HEIGHT = 330.0
# How far a timber piece is moved off the fastener's axis, so that two pieces meeting at a shear plane
# read as two. Bounded well under half PIECE_HEIGHT: the rod is drawn in the band every piece still
# covers, which is what keeps it inside the wood at every section.
PIECE_STEP = 46.0
# The rod's drawn thickness where nothing is to scale yet -- no thickness typed, so no mm per unit.
DOWEL_HEIGHT = 34.0
# ... and the floor under it once it IS to scale, so a Ø 6 mm in a 240 mm joint is still a rod and not a
# hairline. Where the floor bites, the figure says so rather than lying quietly about the scale.
DOWEL_MIN = 16.0
# ... and the ceiling over it, as a share of a piece's drawn height. Only the width is to scale, so a
# diameter taken at the width's scale has to be held to something the frame can carry.
DOWEL_MAX_SHARE = 0.22
MARGIN_X = 90.0
MARGIN_TOP = 96.0
DIM_GAP = 26.0
DIM_HEIGHT = 74.0
TEXT_SIZE = 34.0
SMALL_SIZE = 26.0
SUB_SIZE = 22.0
SUB_DROP = 8.0
STROKE = 3.0
THIN = 2.0

# The width the figure is written at, as connection_svg writes its own: Typst scales it to the
# width the call asks for, and a figure with no size at all comes out blank.
PAPER_MM = 160.0

# A piece whose thickness is not known yet is drawn this wide, so an untyped joint still has a figure.
PLACEHOLDER = 1.0
# A steel plate is drawn at least this wide, whatever its thickness, or it would be a line.
PLATE_MIN = 26.0


_f = svg_draw.number_at(2)   # a coordinate at 2 decimals (svg_draw.py, D6)


def _rect(out, x, y, w, h, fill, stroke, width=STROKE):
    out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="%s" stroke="%s" stroke-width="%s"/>'
               % (_f(x), _f(y), _f(w), _f(h), fill, stroke, _f(width)))


def _line(out, x1, y1, x2, y2, colour=TEXT_COLOR, width=THIN, dash=None):
    extra = ' stroke-dasharray="%s"' % dash if dash else ""
    out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"%s/>'
               % (_f(x1), _f(y1), _f(x2), _f(y2), colour, _f(width), extra))


_escape = svg_draw.escape   # (svg_draw.py, D6)


def _text(out, x, y, content, size=TEXT_SIZE, colour=TEXT_COLOR, anchor="middle", bold=False):
    svg_text.plain(out, x, y, content, size, colour, _f, anchor, ' font-weight="bold"' if bold else "")


def _labelled(out, x, y, base, sub, size=TEXT_SIZE, colour=TEXT_COLOR, bold=False):
    """A symbol with a subscript, centred on x: a second <text> set smaller and lower, because SVG Tiny has neither baseline-shift nor a <tspan> dy both renderers honour (statics_svg's rule).

    The whole is centred, so the two halves are measured and placed from the left.
    """
    base_w = statics_svg.text_width(base, size)
    sub_w = statics_svg.text_width(sub, SUB_SIZE) if sub else 0.0
    left = x - (base_w + sub_w) / 2.0
    _text(out, left, y, base, size=size, colour=colour, anchor="start", bold=bold)
    if sub:
        _text(out, left + base_w, y + SUB_DROP, sub, size=SUB_SIZE, colour=colour, anchor="start", bold=bold)
    return base_w + sub_w


def _dimension(out, x1, x2, y, base, sub, value, unit="mm"):
    """A dimension under a piece: two witness lines, the line between them with a tick at each end, and the label over it. The label is the value when there is one, and the letter while there is not."""
    _line(out, x1, y - DIM_GAP, x1, y + 12, MUTED, THIN)
    _line(out, x2, y - DIM_GAP, x2, y + 12, MUTED, THIN)
    _line(out, x1, y, x2, y, MUTED, THIN)
    for x, direction in ((x1, 1), (x2, -1)):
        _line(out, x, y, x + direction * 10, y - 6, MUTED, THIN)
        _line(out, x, y, x + direction * 10, y + 6, MUTED, THIN)
    middle = (x1 + x2) / 2.0
    if value is None:
        _labelled(out, middle, y - 12, base, sub, size=TEXT_SIZE, colour=TEXT_COLOR)
    else:
        _text(out, middle, y - 12, "%s %s" % (_f(value), unit), size=SMALL_SIZE, colour=TEXT_COLOR)


def pieces(assembly, thicknesses, plates):
    """What the section is made of, left to right: (kind, thickness or None, label base, label subscript).

    `thicknesses` is {"t_1": mm or None, "t_2": mm or None} and `plates` the member's plate block, or None.
    """
    t_1 = thicknesses.get("t_1")
    t_2 = thicknesses.get("t_2")
    if assembly == "Holz-Holz einschnittig":
        return [("timber", t_1, "t", "1"), ("timber", t_2, "t", "2")]
    if assembly == "Holz-Holz zweischnittig":
        return [("timber", t_1, "t", "1"), ("timber", t_2, "t", "2"), ("timber", t_1, "t", "1")]
    # The plate is drawn as wide as the **slot** it sits in -- `Schlitzbreite`, the classeur's `t` -- which is
    # the timber taken out for it and the one thickness the source carries. Its own plate thickness left the
    # source in schema 1.1: nothing read it, the plate's Lochleibung check not being built (section 14).
    plate_t = (plates or {}).get("slot", {}).get("value") if plates else None
    if assembly == "Stahl-Holz, Bleche aussen":
        return [("steel", plate_t, "", ""), ("timber", t_2, "t", "2"), ("steel", plate_t, "", "")]
    count = int((plates or {}).get("count", 1) or 1)
    out = [("timber", t_1, "t", "1")]
    for index in range(count):
        out.append(("steel", plate_t, "", ""))
        if index < count - 1:
            out.append(("timber", t_2, "t", "2"))
    out.append(("timber", t_1, "t", "1"))
    return out


def shear_plane_labels(assembly, count):
    """The letter over each shear plane: A at a plate against a side timber, B at one against a middle timber (SIA 265 Tabelle 46). A timber-timber joint's planes carry no letter -- the norm gives them none."""
    if not assembly.startswith("Stahl-Holz"):
        return None
    if assembly == "Stahl-Holz, Bleche aussen":
        return ["A", "A"]
    labels = []
    for index in range(count):
        labels.append("A" if index in (0, count - 1) else "B")
        labels.append("A" if index in (0, count - 1) else "B")
    return labels


def piece_offsets(parts):
    """How far each piece is moved up or down, so the eye reads several pieces and not one bar.

    The classeur's own figures draw the side pieces at one level and the middle piece at another, and that step is the whole of what makes an *einschnittig* joint legible next to a *zweischnittig* one. Here the timber pieces alternate about the axis, and a steel plate stays centred -- a plate is the thing the timbers are threaded onto, not one of them.

    ⚠️ **The first timber piece is the LOWER one** (v0.77), as SIA 265's Figur 45 and the classeur draw it: einschnittig, the left piece sits below the right one; zweischnittig, both outer pieces sit below the middle one. Until v0.76 it was the other way round. y grows downwards, so lower is a positive offset.

    ⚠️ The step is bounded so that **every** piece still covers the fastener: the rod is drawn in the band they all share, `PIECE_HEIGHT - 2 * STEP` tall, which is what keeps it inside the wood at every section.
    """
    offsets, sign = [], 1
    for kind, _t, _b, _s in parts:
        if kind == "steel":
            offsets.append(0.0)
            continue
        offsets.append(sign * PIECE_STEP)
        sign = -sign
    return offsets


def highlighted_pieces(assembly, parts, member):
    """Which pieces of the section belong to timber member `member` (1-based), as indices into `parts`.

    The engineer, v0.84: hovering «Pièce 1» or «Pièce 2» in Woodcore must light that piece on the
    section too. Which piece that is, is the assembly's own answer and not a rule about left and right:
    a Seitenholz of a *zweischnittig* joint is **two** pieces, the outer ones, and the Mittelholz is the
    middle one; einschnittig they are simply the left and the right. A Stahl-Holz joint enters ONE timber
    member, so every timber piece is that member's -- the slots are what divide it (docs/domain/connectors.md §3.3nonies).
    """
    if not member:
        return set()
    one_member = assembly.startswith("Stahl-Holz")
    out = set()
    for index, (kind, _t, _base, sub) in enumerate(parts):
        if kind != "timber":
            continue
        if one_member:
            if member == 1:
                out.add(index)
        elif sub == str(member):
            out.add(index)
    return out


def section(assembly, thicknesses, plates=None, diameter=None, title=None, note=None, highlight=None):
    """The section through the joint, as SVG text.

    ⚠️ It writes no word of its own: where the diameter could not be drawn to scale, `note` -- {"enlarged": text, "reduced": text}, in the reader's language -- is written under it, and without it nothing is. The export draws it bare and says in the record's `section_scaled` what was resized, so that the report writes the note in its own language (periodic audit 260916, AUD-3-8: «Ø vergrössert, nicht massstäblich» was German in every report); `section_state` gives that word."""
    return _section(assembly, thicknesses, plates, diameter, title, note, highlight)[0]


def section_state(assembly, thicknesses, plates=None, diameter=None):
    """"enlarged" or "reduced" where the section had to draw the diameter at a bound, else None."""
    return _section(assembly, thicknesses, plates, diameter)[1]


def _section(assembly, thicknesses, plates=None, diameter=None, title=None, note=None, highlight=None):
    parts = pieces(assembly, thicknesses, plates)
    known = [t for _kind, t, _b, _s in parts if t]
    # Proportional as soon as the thicknesses are known; equal while they are not.
    if known:
        raw = []
        for kind, t, _b, _s in parts:
            value = t if t else (sum(known) / len(known)) * 0.2
            raw.append(max(value, 1.0))
    else:
        raw = [PLACEHOLDER] * len(parts)
    inner = WIDTH - 2 * MARGIN_X
    scale = inner / sum(raw)
    widths = []
    for (kind, _t, _b, _s), value in zip(parts, raw):
        w = value * scale
        widths.append(max(w, PLATE_MIN) if kind == "steel" else w)
    # keep the whole inside the frame after any minimum was applied
    total = sum(widths)
    if total > inner:
        widths = [w * inner / total for w in widths]
        scale *= inner / total

    offsets = piece_offsets(parts)
    out = []
    axis = MARGIN_TOP + PIECE_HEIGHT / 2.0 + PIECE_STEP
    x = MARGIN_X
    edges = [x]
    placed = []
    for (kind, _t, _b, _s), w, dy in zip(parts, widths, offsets):
        top = axis - PIECE_HEIGHT / 2.0 + dy
        if kind == "timber":
            fill = TIMBER_FILL if len(edges) % 2 else TIMBER_FILL_ALT
            _rect(out, x, top, w, PIECE_HEIGHT, fill, TIMBER_STROKE)
        else:
            _rect(out, x, top, w, PIECE_HEIGHT, STEEL_FILL, STEEL_STROKE)
        placed.append((x, top, w))
        x += w
        edges.append(x)

    # The piece(s) of one timber member, ringed in the schema's own highlight colour -- the same ink the
    # pattern beside this figure rings an element in, so the two drawings mark one thing one way.
    for index in sorted(highlighted_pieces(assembly, parts, highlight)):
        left, top, w = placed[index]
        _rect(out, left, top, w, PIECE_HEIGHT, "none", schema_svg.HIGHLIGHT, 2.2 * STROKE)

    # The fastener: **as thick as its own diameter**, at the same scale as the thicknesses, so that d can
    # be read against t_1 and t_2 on the page; and drawn from the first face to the last, never beyond --
    # a rod sticking out of the timber is a drawing that says the wrong thing about the joint.
    #
    # ⚠️ Only the TIMBER thicknesses may set that scale. A joint whose pieces are still untyped has its
    # widths from the plates alone, and a diameter drawn at that scale came out taller than the whole
    # figure -- the drawing was one black rectangle. Where they are unknown the rod keeps its nominal
    # height, which is what lets Woodcore show a figure before anything has been typed.
    # ⚠️ Only the drawing's WIDTH is to scale: the height of a piece is the member's depth, which the
    # section does not model. So a diameter drawn at the width's scale can come to a fifth of the frame --
    # a Ø 8 mm dowel through a 30 mm joint is 27 % of it, and the figure was one black bar. It is held to
    # a fraction of the piece, and the figure says when that bit.
    band = min(PIECE_HEIGHT * DOWEL_MAX_SHARE, PIECE_HEIGHT - 2 * PIECE_STEP - 16)
    known_timber = [t for kind, t, _b, _s in parts if kind == "timber" and t]
    thickness = diameter * scale if (diameter and known_timber) else DOWEL_HEIGHT
    enlarged = thickness < DOWEL_MIN
    shrunk = thickness > band
    thickness = min(max(thickness, DOWEL_MIN), band)
    _rect(out, edges[0], axis - thickness / 2.0, edges[-1] - edges[0], thickness,
          FASTENER_FILL, FASTENER_FILL, THIN)
    # The diameter is written at the head of the figure, not beside the rod: anchored at the left edge it
    # would be drawn outside the viewBox and clipped away, which is what the first rendering showed.
    if diameter:
        _text(out, MARGIN_X, 52, "Ø %s mm" % _f(diameter),
              size=TEXT_SIZE, colour=TEXT_COLOR, anchor="start")
    else:
        _text(out, MARGIN_X, 52, "Ø d", size=TEXT_SIZE, colour=TEXT_COLOR, anchor="start")

    # the shear planes: the inner edges, each with its letter where the norm gives one
    labels = shear_plane_labels(assembly, int((plates or {}).get("count", 1) or 1))
    inner_edges = edges[1:-1]
    span_top = axis - PIECE_HEIGHT / 2.0 - PIECE_STEP
    span_bottom = axis + PIECE_HEIGHT / 2.0 + PIECE_STEP
    for index, edge in enumerate(inner_edges):
        _line(out, edge, span_top - 34, edge, span_bottom + 8, MUTED, THIN, dash="10 8")
        if labels and index < len(labels):
            _text(out, edge, span_top - 44, labels[index], size=TEXT_SIZE, colour=TEXT_COLOR, bold=True)

    # A dimension under every piece, the plates included: their width is the Schlitzbreite, a number the
    # source carries, so it costs the figure no word and keeps one file for all three languages.
    dim_y = span_bottom + DIM_HEIGHT
    for (kind, t, base, sub), left, right in zip(parts, edges, edges[1:]):
        _dimension(out, left, right, dim_y, base or "t", sub, t)

    height = dim_y + 50
    head = []
    if title:
        _text(head, WIDTH / 2.0, 46, title, size=TEXT_SIZE, colour=TEXT_COLOR, bold=True)
    state = ("enlarged" if enlarged else "reduced") if diameter and (enlarged or shrunk) else None
    if state and note and note.get(state):
        # The project's own rule for a quantity the frame cannot take at its true size: it is drawn at the
        # bound and the figure SAYS so, rather than being drawn to scale and disappearing, or drawn at the
        # bound in silence (connection_svg's share note, statics_svg's «Vergrössert, nicht massstäblich»).
        _text(out, MARGIN_X, height - 8, note[state], size=SMALL_SIZE, colour=MUTED, anchor="start")
    body = "".join(head + out)
    # An explicit width and height in mm, as connection_svg and statics_svg give: Typst sizes an image
    # from them, and a root carrying only `width="100%"` comes out blank and takes the rest of the page.
    mm_w = PAPER_MM
    mm_h = PAPER_MM * height / WIDTH
    return ('<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 %s %s" '
            'width="%smm" height="%smm">'
            '<rect x="0" y="0" width="%s" height="%s" fill="%s"/>%s</svg>'
            % (_f(WIDTH), _f(height), _f(mm_w), _f(mm_h), _f(WIDTH), _f(height), GROUND, body)), state


def section_of(source, thicknesses=None, note=None, highlight=None):
    """The section of one connector source -- Woodcore's preview and the export's own figure.

    ⚠️ A **Stahl-Holz** joint enters ONE timber member, whose `t` is the whole piece: the slots are what
    divide it into a side and a middle piece, and t_1/t_2 are `dowel.steel_geometry`'s to compute. Reading
    the member's `t` as t_1 would draw a joint several times too wide and label it wrongly.
    """
    return section(*_section_args(source, thicknesses), note=note, highlight=highlight)


def section_state_of(source, thicknesses=None):
    """What `section_of` had to resize for this source: "enlarged", "reduced" or None -- the record's `section_scaled`."""
    return section_state(*_section_args(source, thicknesses))


def _section_args(source, thicknesses):
    from domains import dowel                      # here, not at import: dowel imports nothing of this
    assembly = source.get("assembly", "Holz-Holz zweischnittig")
    plates = next((m.get("plates") for m in source.get("members", []) if m.get("plates")), None)
    if thicknesses is None:
        timber = [m for m in source.get("members", []) if m.get("role") == "timber"]
        values = [(m.get("t") or {}).get("value") for m in timber]
        if assembly.startswith("Stahl-Holz") and plates and values and values[0]:
            try:
                geometry = dowel.steel_geometry(
                    values[0], (plates.get("slot") or {}).get("value") or 0.0,
                    int(plates.get("count", 1) or 1), plates.get("ratio", 0.5))
                thicknesses = {"t_1": geometry.get("t_1"), "t_2": geometry.get("t_2")}
            except Exception:  # broad: a figure must never be what stops a draft being shown
                thicknesses = {"t_1": None, "t_2": None}
        else:
            thicknesses = {"t_1": values[0] if values else None,
                           "t_2": values[1] if len(values) > 1 else None}
    diameter = (source.get("diameter") or {}).get("value")
    return assembly, thicknesses, plates, diameter


def pattern_of(source, detail, lang="de", highlight=None, positions=None):
    """The fastener pattern: **the schema's own drawing**, with this connector's fasteners numbered on it.

    Since v0.74 a connector carries no geometry -- it names a detail schema and the markers of it its fasteners sit on (docs/domain/connectors.md §3.3nonies) -- so there is nothing here to lay out. `detail` is that schema's source; `None` (a schema that was renamed, or a connector that names none yet) gives an empty figure rather than an exception, a drawing never being what stops a draft being shown.

    `highlight` is a (collection, id) pair the *Connecteurs* tab rings while a row is hovered or an element chosen -- the very argument `show-schema` takes, so the window and the report mark the same thing.

    Drawn once per language, as a connection's figure is; with no legend, only the note under it differs between languages (docs/typst/language.md §4bis).

    `positions` are the position records the schema's elements resolve their section and label against (v0.75). The fasteners are drawn at the connector's own d -- a detail is at its real size -- with a floor for legibility, and a line under the drawing says so where the floor bites, which is the project's rule for a quantity too small to be read.
    """
    from domains import connection_svg  # here, not at import: it reads connection, which reads schema, which reads this module's caller
    if not detail:
        return schema_svg.render(schema_svg.layout({"elements": [], "connectors": [], "aids": [], "dimensions": []}, lang=lang))
    drawing = schema_svg.layout(detail, lang=lang, positions=positions, use_crop=False)
    fasteners = source.get("fasteners", [])
    points = connection_svg.marker_points(detail, fasteners)
    diameter = (source.get("diameter") or {}).get("value")
    note = None
    if diameter and diameter / 2.0 < connection_svg.DOT_FLOOR_SHARE * drawing["radius"]:
        note = strings.text("figure.enlarged", lang) + "Ø %s mm" % _f(diameter)
    # ⚠️ `highlight` is a (collection, id) pair and `overlay` takes two different things: `highlight`, the 0-based index of a fastener it numbers, and `mark`, a piece of the schema. The pair used to be handed over as the index, which is never equal to one -- so neither a hovered marker row nor a chosen element was ever lit on this figure.
    index, mark = None, None
    if highlight and highlight[0] in ("connectors", "aids"):
        # a fastener -- a marker, or a point ticked «connecteur» (v0.77) -- is lit by the number it carries
        places = connection_svg.connection.fastener_places(detail)
        drawn = [mid for mid in fasteners if mid in places]
        index = drawn.index(highlight[1]) if highlight[1] in drawn else None
    elif highlight:
        mark = tuple(highlight)
    # No legend, no rotation centre and no moment: a connector carries no N, V or M and turns about nothing.
    return connection_svg.overlay(drawing, points, lang=lang, highlight=index, mark=mark,
                                  legend=False, show_center=False, show_moment=False,
                                  center=None, centroid=None, triad=None,
                                  dot_diameter=diameter, note=note)


# --- Figur 45: the line k_beta is read off (v0.77) -----------------------------
# SIA 265 Anhang A, Figur 45: k_beta against the timber's thickness -- 0 at t = 0, k_i,1 at t_i,1, k_i,2 at t_i,2, flat beyond, and for a Mittelholz a straight line from the origin to the upper corner (the dashed «bois médian»). One figure per thickness, t_1 and t_2, with every corner and the thickness the calculation reads written on it as «symbol = value unit» -- the engineer: «t_1,1 = 30 mm». No word is on it, so one file serves the three languages, as the section does; the report names what each is under it.

CURVE_WIDTH = 1000.0
CURVE_HEIGHT = 700.0
CURVE_TEXT = 34.0
CURVE_PAPER_MM = 80.0
# The thickness the calculation reads and the k_beta it reads there, in an accent of their own: they are the one point of the line the calculation uses.
CURVE_ACCENT = svg_draw.colour("blue")


def _number(value, decimals):
    text = "%.*f" % (decimals, value)
    return text.rstrip("0").rstrip(".") if "." in text else text


def _spread(wanted, gap, low, high):
    """Positions for labels wanted at `wanted` (ascending), moved apart so that no two are closer than `gap`, and kept within [low, high] where there is room."""
    out = []
    for w in wanted:
        out.append(max(w, out[-1] + gap) if out else max(w, low))
    overflow = out[-1] - high if out else 0.0
    if overflow > 0:
        out[-1] -= overflow
        for index in range(len(out) - 2, -1, -1):
            out[index] = min(out[index], out[index + 1] - gap)
    return out


def k_beta_curve(curve):
    """Figur 45 for one thickness, as SVG text. `curve` is one entry of the k_beta table's `curves` (dowel._k_beta_table): its `index` i, the thickness `t`, the corners `t_1`, `k_1`, `t_2`, `k_2`, and the `k_beta` read at `t`. A lower corner at the origin is a Mittelholz's, drawn dashed."""
    i = int(curve["index"])
    t, t_1, k_1, t_2, k_2, k_beta = (float(curve[key]) for key in ("t", "t_1", "k_1", "t_2", "k_2", "k_beta"))
    middle = t_1 <= 0
    size = CURVE_TEXT

    def mm(value):
        return "%s mm" % _number(value, 1)

    # «symbol = value unit» for every corner, then for the thickness read and its k_beta
    x_labels = [] if middle else [(t_1, "t_(%d,1) = %s" % (i, mm(t_1)), MUTED)]
    x_labels.append((t_2, "t_(%d,2) = %s" % (i, mm(t_2)), MUTED))
    x_labels.append((t, "t_%d = %s" % (i, mm(t)), CURVE_ACCENT))
    y_labels = [] if middle else [(k_1, "k_(β%d,1) = %s" % (i, _number(k_1, 3)), MUTED)]
    if abs(k_beta - k_2) <= 1e-9:
        # read on the flat part: one label says both
        y_labels.append((k_2, "k_(β%d) = k_(β%d,2) = %s" % (i, i, _number(k_2, 3)), CURVE_ACCENT))
    else:
        y_labels.append((k_2, "k_(β%d,2) = %s" % (i, _number(k_2, 3)), MUTED))
        y_labels.append((k_beta, "k_(β%d) = %s" % (i, _number(k_beta, 3)), CURVE_ACCENT))

    left = 60.0 + max(statics_svg.text_width(label, size) for _v, label, _c in y_labels)
    right = CURVE_WIDTH - 110.0
    top = 110.0
    x_max = max(t_2 * 1.25, t * 1.12)
    y_max = max(k_2, k_beta) * 1.2

    def px(value):
        return left + value / x_max * (right - left)

    # the x labels go into rows under the axis, each taking the first row where it clears the label before it -- the first row starting with the origin's «0», which ends just left of the axis
    row_ends, placed = [left - 6.0], []
    for value, label, colour in sorted(x_labels, key=lambda entry: entry[0]):
        x = px(value)
        width = statics_svg.text_width(label, size)
        centre = min(max(x, left + width / 2.0 - 40.0), CURVE_WIDTH - 12.0 - width / 2.0)
        row = 0
        while row < len(row_ends) and row_ends[row] > centre - width / 2.0 - 26.0:
            row += 1
        if row == len(row_ends):
            row_ends.append(0.0)
        row_ends[row] = centre + width / 2.0
        placed.append((x, centre, row, label, colour))
    row_height = 1.3 * size
    bottom = CURVE_HEIGHT - 40.0 - len(row_ends) * row_height

    def py(value):
        return bottom - value / y_max * (bottom - top)

    out = []
    # the axes, their arrowheads and their symbols
    _line(out, left, bottom, right + 40, bottom, TEXT_COLOR, STROKE)
    _line(out, left, bottom, left, top - 40, TEXT_COLOR, STROKE)
    out.append('<polygon points="%s,%s %s,%s %s,%s" fill="%s"/>' % (
        _f(right + 62), _f(bottom), _f(right + 36), _f(bottom - 11), _f(right + 36), _f(bottom + 11), TEXT_COLOR))
    out.append('<polygon points="%s,%s %s,%s %s,%s" fill="%s"/>' % (
        _f(left), _f(top - 62), _f(left - 11), _f(top - 36), _f(left + 11), _f(top - 36), TEXT_COLOR))
    svg_text.draw(out, (right + 64, bottom - 36), "t_%d" % i, size, TEXT_COLOR, anchor="end")
    svg_text.draw(out, (left + 22, top - 56), "k_(β%d)" % i, size, TEXT_COLOR, anchor="start")

    # the guides from the axes to the corners, dotted
    corners = [(t_2, k_2)] if middle else [(t_1, k_1), (t_2, k_2)]
    for cx, cz in corners:
        _line(out, px(cx), bottom, px(cx), py(cz), MUTED, THIN, dash="4 8")
        _line(out, left, py(cz), px(cx), py(cz), MUTED, THIN, dash="4 8")

    # the line: a Seitenholz's two slopes, a Mittelholz's one dashed from the origin -- then flat to the end of the axis
    if middle:
        _line(out, px(0), py(0), px(t_2), py(k_2), TEXT_COLOR, 2 * STROKE, dash="24 14")
    else:
        out.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round"/>' % (
            " ".join("%s,%s" % (_f(px(a)), _f(py(b))) for a, b in ((0.0, 0.0), (t_1, k_1), (t_2, k_2))),
            TEXT_COLOR, _f(2 * STROKE)))
    _line(out, px(t_2), py(k_2), px(x_max), py(k_2), TEXT_COLOR, 2 * STROKE)
    for cx, cz in corners:
        out.append('<circle cx="%s" cy="%s" r="7" fill="%s"/>' % (_f(px(cx)), _f(py(cz)), TEXT_COLOR))

    # the thickness the calculation reads, and the k_beta it reads there
    _line(out, px(t), bottom, px(t), py(k_beta), CURVE_ACCENT, THIN, dash="12 8")
    _line(out, left, py(k_beta), px(t), py(k_beta), CURVE_ACCENT, THIN, dash="12 8")
    out.append('<circle cx="%s" cy="%s" r="11" fill="%s" stroke="%s" stroke-width="3"/>' % (
        _f(px(t)), _f(py(k_beta)), CURVE_ACCENT, GROUND))

    # the x labels in their rows, a leader back to the tick where a label had to drop a row or move aside -- every tick and leader first, every text after them, so that no leader crosses a label
    texts = []
    for x, centre, row, label, colour in placed:
        baseline = bottom + 0.95 * size + row * row_height
        _line(out, x, bottom, x, bottom + 12, colour, THIN)
        if row or abs(centre - x) > 2:
            _line(out, x, bottom + 12, centre, baseline - 0.55 * size, colour, THIN)
        texts.append(((centre, baseline), label, colour, "middle"))

    # the y labels, right-aligned left of the axis, moved apart where two values are close, with a leader back to the tick
    wanted = sorted(y_labels, key=lambda entry: -entry[0])
    spots = _spread([py(v) for v, _label, _colour in wanted], 1.2 * size, top - 30.0, bottom - 0.9 * size)
    for (value, label, colour), y in zip(wanted, spots):
        _line(out, left - 12, py(value), left, py(value), colour, THIN)
        if abs(y - py(value)) > 2:
            _line(out, left - 12, py(value), left - 26, y, colour, THIN)
        texts.append(((left - 30, y), label, colour, "end"))
    texts.append(((left - 14, bottom + 0.95 * size), "0", MUTED, "end"))
    for point, label, colour, anchor in texts:
        svg_text.draw(out, point, label, size, colour, anchor=anchor, halo=6)

    return ('<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 %s %s" width="%smm" height="%smm">'
            '<rect x="0" y="0" width="%s" height="%s" fill="%s"/>%s</svg>'
            % (_f(CURVE_WIDTH), _f(CURVE_HEIGHT), _f(CURVE_PAPER_MM), _f(CURVE_PAPER_MM * CURVE_HEIGHT / CURVE_WIDTH),
               _f(CURVE_WIDTH), _f(CURVE_HEIGHT), GROUND, "".join(out)))


# --- the tool bar's swatches (docs/ui/window.md §10quater) ---------------------
# One small drawing per kind of fastener, for the buttons of Woodcore's type bar -- the arrangement
# statics_svg.SWATCHES has for the static models' tools. Each is drawn in its own proportions inside a
# 100 x 100 box, in the sentinel ink and fill the tab substitutes for the palette's, so that a symbol
# drawn in the figure's own black is still legible on Windows' dark theme.
SWATCH_INK = svg_draw.colour("ink")
SWATCH_FILL = svg_draw.colour("ground")

_S = 'stroke="%s" stroke-width="6" fill="none"' % SWATCH_INK
_SF = 'stroke="%s" stroke-width="5" fill="%s"' % (SWATCH_INK, SWATCH_FILL)

SWATCHES = {
    # a dowel through two pieces, seen in section: the shear plane, and the rod across it
    "Stabdübel": '<rect x="10" y="18" width="80" height="30" %s/><rect x="10" y="52" width="80" height="30" %s/>'
                 '<rect x="38" y="12" width="24" height="76" fill="%s"/>' % (_SF, _SF, SWATCH_INK),
    # a nail: a head and a tapering shank
    "Nagel": '<rect x="18" y="14" width="64" height="10" fill="%s"/>'
             '<polygon points="46,24 54,24 52,88 48,88" fill="%s"/>' % (SWATCH_INK, SWATCH_INK),
    # a screw: a head and a threaded shank
    "Vollgewindeschraube": '<rect x="22" y="12" width="56" height="12" fill="%s"/>'
                           '<rect x="44" y="24" width="12" height="64" fill="%s"/>'
                           '<path d="M32 34 L68 42 M32 48 L68 56 M32 62 L68 70" %s/>' % (SWATCH_INK, SWATCH_INK, _S),
    # a bolt: a hexagon head, a shank and a nut
    "Bolzen": '<polygon points="30,12 70,12 78,26 70,40 30,40 22,26" %s/>'
              '<rect x="44" y="40" width="12" height="36" fill="%s"/>'
              '<rect x="32" y="76" width="36" height="14" %s/>' % (_SF, SWATCH_INK, _SF),
    # a ring connector between two pieces
    "Dübel besonderer Bauart": '<line x1="8" y1="50" x2="92" y2="50" %s/>'
                               '<circle cx="50" cy="50" r="28" %s/><circle cx="50" cy="50" r="18" %s/>' % (_S, _SF, _SF),
    # the carpentry joints: a lapped joint, a Versatz, a dovetail
    "Blatt": '<polygon points="10,30 56,30 56,50 90,50 90,70 44,70 44,50 10,50" %s/>' % _SF,
    "Versatz": '<polygon points="10,70 90,70 90,50 46,50 62,22 34,22 18,50 10,50" %s/>' % _SF,
    "Schwalbenschwanz": '<polygon points="10,20 90,20 90,80 10,80" %s/>'
                        '<polygon points="34,20 66,20 74,50 26,50" fill="%s"/>' % (_SF, SWATCH_FILL),
}


def swatch(kind):
    """The small drawing of one kind of fastener, as an SVG document. KeyError for a kind with none."""
    body = SWATCHES[kind]
    return ('<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 100 100" '
            'width="100" height="100">%s</svg>' % body)
