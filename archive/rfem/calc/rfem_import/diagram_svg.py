"""The figure the RFEM tab shows: one structure's static system, and over it the diagram of one internal force for one loading.

The engineer's own request, and its shape: «fais les figures dans le volet de droite … une figure avec un sélecteur», «afficher le schéma statique avec la courbe des moments, des réactions d'appui, des efforts tranchants, des forces normales», and «M positif vers le bas. Valeurs aux extremums (positifs et négatifs) et aux nœuds».

**It draws and computes nothing.** The system comes from `model_tables`, the grouping from `structure_detection`, the stations from `results`; this module places them and writes SVG. That is the rule every other figure module here follows (`statics_svg`, `schema_svg`, `connection_svg`), and it is what lets the same drawing be shown in the window and set in the report.

⚠️ **M positive is drawn towards +z, which is downwards, which is the tension side.** The frame is RFEM's own here — x right, z down (`import_controller`) — so rotating a member's axis by a quarter turn from x towards z gives the normal a positive value is offset along: a beam along +x has the normal (0, 1), and a sagging moment is drawn under it. Nothing is flipped anywhere, and a member drawn at an angle follows its own axis.

⚠️ **The polyline keeps two stations at one x.** A shear force jumps where a point load sits, and RFEM writes both values at the same abscissa — member 2 of CO1 carries V_z = −7.551 and +7.551 at x = 2.115. Sorting by x alone would keep both, in the order the table gives them, which is the order that draws the jump; collapsing them would draw a diagram that is continuous where the structure's is not.

⚠️ **Kept to SVG Tiny 1.2**, like every drawing of this project: no CSS, no `<marker>`, no arc command, no `pattern` — Woodcore renders it through QtSvg, which implements no more, and Typst reads the same file. A hatch is a run of line segments and a label's halo is a rectangle under it (`statics_svg`'s own rule).

⚠️ **One bare font family**, `Arial`: QtSvg takes the whole `font-family` string as a single name, so a list matches nothing and falls back to a face whose advances are not Arial's (`statics_svg`, v0.79, periodic audit B20). `tests/test_constants.py` holds every figure module to one family.
"""

import math

from rfem_import import diagram_curve

# The drawing's own units: the longer side of the frame, as `statics_svg` normalises its own sketch, so that
# a 2 m detail and a 25 m frame come out as the same figure to the printed digit.
EXTENT = 1000.0
MARGIN = 0.10          # of the extent, around everything drawn
DIAGRAM = 0.22         # the height the largest value of a diagram is drawn at, of the extent

FONT = "Arial"
LABEL_PT = 20.0
MEMBER_WIDTH = 4.0
CURVE_WIDTH = 2.5
SUPPORT = 26.0         # the size a support symbol is drawn at

INK = "#1a1a1a"
MUTED = "#8a8a8a"
# One colour per quantity, and one family per kind: a normal force green, a shear blue, a moment red --
# the reading RFEM's own diagrams train an engineer in.
COLOURS = {
    "N": "#2e7d32",
    "V_y": "#1565c0", "V_z": "#1565c0",
    "M_T": "#b8860b", "M_y": "#c62828", "M_z": "#c62828",
}
FILL_OPACITY = "0.18"

# What each quantity is called on the figure, and its unit.
UNITS = {"N": "kN", "V_y": "kN", "V_z": "kN", "M_T": "kNm", "M_y": "kNm", "M_z": "kNm"}


def _round(value, digits=3):
    """A number as SVG source: no exponent, no trailing zeros, and a hyphen for its sign -- an SVG parser reads no typographic minus."""
    text = f"{value:.{digits}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _label(value):
    """A value as the figure writes it: at most two decimals, and a real minus sign, which is text and not source."""
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    if text in ("", "-", "-0"):
        text = "0"
    return text.replace("-", "−")


class Geometry:
    """Where one structure's members and supports are, in metres, and how that maps onto the figure."""

    __slots__ = ("members", "supports", "x0", "z0", "x1", "z1", "scale", "dx", "dz", "used")

    def __init__(self, members, supports, box):
        self.members, self.supports = members, supports
        self.x0, self.z0, self.x1, self.z1 = box
        width = max(self.x1 - self.x0, 1e-6)
        height = max(self.z1 - self.z0, 1e-6)
        self.scale = EXTENT / max(width, height)
        # ⚠️ **The frame takes the structure's own proportions**, and the drawing is not centred in a square:
        # a portal frame is three times as wide as it is tall, and squaring its frame put two thirds of the
        # figure's height in white -- which in the window is two thirds of the room the engineer gave it.
        self.dx = self.dz = 0.0
        self.used = (width * self.scale, height * self.scale)

    def at(self, x, z):
        """A point in metres, as a point of the figure."""
        return ((x - self.x0) * self.scale + self.dx, (z - self.z0) * self.scale + self.dz)


def geometry(model, structure):
    """The members and supports of `structure`, with the box they occupy -- what `render` places everything against."""
    coords = {node.no: (node.x, node.z) for node in model.nodes}
    wanted = set(structure.numbers("member"))
    members, xs, zs = [], [], []
    for member in model.members:
        if member.no not in wanted:
            continue
        ends = [coords[n] for n in member.nodes if n in coords]
        if len(ends) < 2:
            continue
        (ax, az), (bx, bz) = ends[0], ends[-1]
        length = math.hypot(bx - ax, bz - az)
        if length <= 0:
            continue
        section = model.section_of(member)
        members.append({
            "no": member.no, "a": (ax, az), "b": (bx, bz), "length": length,
            "u": ((bx - ax) / length, (bz - az) / length),
            "section": section.name if section is not None else "",
        })
        xs.extend((ax, bx)); zs.extend((az, bz))
    nodes = set(structure.nodes)
    supports = []
    for support in model.supports:
        for node in support.nodes:
            if node in nodes and node in coords:
                supports.append({"no": support.no, "node": node, "at": coords[node],
                                 "kind": getattr(support, "kind", "") or ""})
    if not xs:
        return None
    return Geometry(members, supports, (min(xs), min(zs), max(xs), max(zs)))


def curves(geo, table, key):
    """Per member of the geometry, the stations of `key` along it: `{member: [(x, value, slope), …]}`, in the table's own order.

    ⚠️ Kept in the table's order rather than sorted, so that two stations at one abscissa draw the jump they are (see the module's header).

    ⚠️ **The third number is the quantity that is this one's slope** where the table carries one -- V_z for M_y,
    V_y for M_z (`diagram_curve.SLOPE_OF`) -- and `None` otherwise. It is what lets the line between two stations
    be drawn as the curve it is rather than as the chord RFEM's four rows per member would otherwise give.
    """
    if table is None:
        return {}
    slope_key = diagram_curve.SLOPE_OF.get(key)
    found = {}
    wanted = {member["no"] for member in geo.members}
    for station in table.stations:
        if station.member not in wanted:
            continue
        value = station.forces.get(key)
        if value is None or station.x is None:
            continue
        slope = None if slope_key is None else station.forces.get(slope_key)
        found.setdefault(station.member, []).append(
            (float(station.x), float(value), None if slope is None else float(slope)))
    return found


def _extremes(points):
    """Which of a member's stations carry a number: its two ends, and where the value is largest and smallest.

    The engineer's own list — «valeurs aux extremums (positifs et négatifs) et aux nœuds». Four labels a member
    at most, and the two ends are the nodes: RFEM writes a station at each of them and names the node there.
    Marking every turn instead put some forty numbers on a six-member frame, which is a figure nobody reads.
    """
    if not points:
        return []
    highest = max(range(len(points)), key=lambda i: points[i][1])
    lowest = min(range(len(points)), key=lambda i: points[i][1])
    return sorted({0, len(points) - 1, highest, lowest})


def render(model, structure, table=None, key="M_y", labels=True, caption=None):
    """The structure, and the diagram of `key` over it where `table` carries one, as one SVG document."""
    geo = geometry(model, structure)
    if geo is None:
        return _empty("—")

    stations = curves(geo, table, key)
    # The line is drawn through the curve the exported stations determine (`diagram_curve`); the numbers
    # written on it stay the stations' own, so nothing on the figure is a value this program worked out.
    data = diagram_curve.refined(stations, key)
    peak = max((abs(v) for points in data.values() for _x, v in points), default=0.0)
    vscale = (DIAGRAM * EXTENT / peak) if peak > 0 else 0.0
    colour = COLOURS.get(key, INK)

    out = []
    # Room for the structure, for the diagram either side of it, and for the labels and the caption on top.
    used_w, used_h = geo.used
    pad = MARGIN * EXTENT
    reach = (DIAGRAM * EXTENT + LABEL_PT * 2.0) if peak > 0 else SUPPORT * 2.0
    view = (-pad, -pad - reach, used_w + 2 * pad, used_h + 2 * pad + 2 * reach)
    out.append(
        '<svg xmlns="http://www.w3.org/2000/svg" version="1.2" baseProfile="tiny" '
        'viewBox="%s %s %s %s" width="100%%" height="100%%">' % tuple(_round(v, 1) for v in view))
    out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#ffffff"/>'
               % tuple(_round(v, 1) for v in view))

    # The system first, so the diagram is read over it.
    for member in geo.members:
        ax, az = geo.at(*member["a"])
        bx, bz = geo.at(*member["b"])
        out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s" '
                   'stroke-linecap="round"/>'
                   % (_round(ax, 1), _round(az, 1), _round(bx, 1), _round(bz, 1), INK, _round(MEMBER_WIDTH, 1)))
    for support in geo.supports:
        out.extend(_support(geo, support))

    # Then the diagram, member by member.
    texts = []
    for member in geo.members:
        points = data.get(member["no"])
        if not points or vscale <= 0:
            continue
        ux, uz = member["u"]
        nx, nz = -uz, ux          # a quarter turn from x towards z: a positive value goes towards +z, downwards
        ax, az = member["a"]

        def place(x, value):
            return geo.at(ax + ux * x + nx * value * vscale / geo.scale,
                          az + uz * x + nz * value * vscale / geo.scale)

        outline = [place(x, v) for x, v in points]
        start = geo.at(*member["a"])
        end = geo.at(ax + ux * member["length"], az + uz * member["length"])
        ring = [start] + outline + [end]
        out.append('<polygon points="%s" fill="%s" fill-opacity="%s" stroke="none"/>'
                   % (" ".join("%s,%s" % (_round(px, 1), _round(pz, 1)) for px, pz in ring), colour, FILL_OPACITY))
        out.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="%s"/>'
                   % (" ".join("%s,%s" % (_round(px, 1), _round(pz, 1)) for px, pz in outline),
                      colour, _round(CURVE_WIDTH, 1)))
        # The rungs that tie the diagram to its member, as a printed diagram draws them.
        for index, (x, value) in enumerate(points):
            if index % max(1, len(points) // 12) and index not in (0, len(points) - 1):
                continue
            foot = geo.at(ax + ux * x, az + uz * x)
            head = place(x, value)
            out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1" '
                       'stroke-opacity="0.45"/>'
                       % (_round(foot[0], 1), _round(foot[1], 1), _round(head[0], 1), _round(head[1], 1), colour))
        if labels:
            marks = [(x, value) for x, value, _slope in stations.get(member["no"], [])]
            for index in _extremes(marks):
                x, value = marks[index]
                if peak and abs(value) < 0.02 * peak and 0 < index < len(marks) - 1:
                    continue
                px, pz = place(x, value)
                texts.append((px, pz + (LABEL_PT * 0.35 if value >= 0 else -LABEL_PT * 0.5), _label(value), colour))

    written = []
    for px, pz, text, ink in texts:
        if any(abs(px - qx) < LABEL_PT * 1.6 and abs(pz - qz) < LABEL_PT * 0.9 and text == other
               for qx, qz, other in written):
            continue          # two members meeting at a node carry the same value there; it is written once
        written.append((px, pz, text))
        out.extend(_text(px, pz, text, ink))
    if caption:
        out.extend(_text(used_w / 2.0, -pad - reach + LABEL_PT * 1.4, caption, MUTED,
                         size=LABEL_PT * 1.15, anchor="middle", halo=False))
    out.append("</svg>")
    return "\n".join(out)


def _text(x, z, text, ink, size=LABEL_PT, anchor="middle", halo=True):
    """A label, with the white box under it that `statics_svg` puts under its own -- a halo drawn as a rectangle, Tiny having no paint-order."""
    escaped = (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    width = 0.62 * size * max(len(str(text)), 1)
    out = []
    if halo:
        left = x - width / 2.0 if anchor == "middle" else x
        out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#ffffff" fill-opacity="0.82"/>'
                   % (_round(left - 2, 1), _round(z - size * 0.78, 1), _round(width + 4, 1), _round(size * 1.05, 1)))
    out.append('<text x="%s" y="%s" font-family="%s" font-size="%s" fill="%s" text-anchor="%s">%s</text>'
               % (_round(x, 1), _round(z, 1), FONT, _round(size, 1), ink, anchor, escaped))
    return out


def _support(geo, support):
    """One support, as the symbol its kind gives it: a triangle for a pin, a triangle on rollers, hatching for a fixed one."""
    x, z = geo.at(*support["at"])
    s = SUPPORT
    kind = (support["kind"] or "").lower()
    out = []
    if "fix" in kind or "encastr" in kind or "einspann" in kind:
        out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="3"/>'
                   % (_round(x - s, 1), _round(z, 1), _round(x + s, 1), _round(z, 1), INK))
        for i in range(-3, 4):
            out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="2"/>'
                       % (_round(x + i * s / 3.0, 1), _round(z, 1),
                          _round(x + i * s / 3.0 - s / 3.0, 1), _round(z + s * 0.55, 1), INK))
        return out
    out.append('<polygon points="%s,%s %s,%s %s,%s" fill="none" stroke="%s" stroke-width="3"/>'
               % (_round(x, 1), _round(z, 1), _round(x - s * 0.55, 1), _round(z + s, 1),
                  _round(x + s * 0.55, 1), _round(z + s, 1), INK))
    out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="3"/>'
               % (_round(x - s * 0.8, 1), _round(z + s, 1), _round(x + s * 0.8, 1), _round(z + s, 1), INK))
    return out


def _empty(text):
    return ('<svg xmlns="http://www.w3.org/2000/svg" version="1.2" baseProfile="tiny" '
            'viewBox="0 0 100 40" width="100%%" height="100%%">'
            '<text x="50" y="24" font-family="%s" font-size="10" fill="%s" text-anchor="middle">%s</text>'
            '</svg>' % (FONT, MUTED, text))
