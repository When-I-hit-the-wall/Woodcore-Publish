"""The wind's buildings in 3D, built from SIA 261 Annexe C's figures as numbers (spec 2026-10-23-onglet-vent-briques, REQ-010, ARCH-011, UI-008 to UI-017, D-23).

`calc/norms/sia261-2020-annexc-wind-geometry.json` holds the 37 buildings -- each its family, the table's own proportions h : b : d and the place of every surface the table names --; this module builds a `model3d.Scene` of one, one builder a family: prisms (31-45, 58-60b: flat, pitched, mono-pitched, an off-centre ridge, sheds, a hipped roof), open buildings (46-49), the stand (50), the platform canopies (51-56), the eaves (57a-d) and the curved forms (63, 64). x runs along d from wall A, y along b from wall C, z up; the wind at φ = 0° blows onto A along +x, at 90° onto C along +y.

What the scene holds: the faces, each keyed by its surface (`A`, `m`, `5°`…) and labelled on itself, the strips m, n, o laid on their face and cut at a ridge; Q₁ to Q₃ in their direction; the direction φ, an arrow that turns about the building and points at it, an arc from φ = 0°; b, d, h on the edges, h_e at the eaves of a pitched roof and the slope α -- and, for the results, the global forces with their value scaled to the largest (`forces`) and the load planes of the surfaces held off their face by arrows, red a pressure, blue a suction (`loads`). The drawing follows the table's proportions, never what is typed (UI-008). No Qt.
"""

import math

from domains import model3d as m3
from norms import _loader

GEOMETRY = "sia261-2020-annexc-wind-geometry"
_cache = {}


def data():
    if "data" not in _cache:
        from pathlib import Path
        path = Path(__file__).resolve().parents[1] / "norms" / (GEOMETRY + ".json")
        _cache["data"] = _loader.load(path)
    return _cache["data"]


def building(number):
    """The geometry of the building of Tableau `number`, None where the file holds none."""
    return data()["buildings"].get(number)


# --- the families -----------------------------------------------------------------------------------------------------

class _Model:
    """What a builder gives: its faces, the heights the dimensions and forces read, and where the roof is at x."""

    def __init__(self, h, b, d):
        self.h, self.b, self.d = h, b, d
        self.faces = []          # (Polygon, label point or None)
        self.za = self.zb = self.he = h
        self.roof = lambda x, y=None: h
        self.kinks = []
        self.slope = 0
        self.ridged = False
        self.walls = True

    def face(self, key, points, normal=None, layer=0, hatch=False, role=None, opacity=1.0, label=True, owner=None):
        normal = normal or m3.normal_of(points)
        role = role or ("strip" if layer == 1 else "face")
        poly = m3.Polygon([tuple(p) for p in points], role=role, key=key, normal=tuple(normal), layer=layer, hatch=hatch, opacity=opacity,
                          width=0.7 if layer == 1 else 1.0, owner=owner)
        self.faces.append((poly, label))
        return poly


def _profile(model, roof):
    """The roof of a prism across d: model.roof(x), its kinks, the walls' heights at A and B."""
    h, d = model.h, model.d
    kind = roof["kind"]
    if kind == "flat":
        return
    if kind == "duo":
        t = math.tan(math.radians(roof["slope"]))
        he = max(h * 0.35, h - t * d / 2)
        model.roof = lambda x, y=None: he + (h - he) * (1 - abs(x - d / 2) / (d / 2))
        model.kinks, model.za, model.zb, model.he, model.slope, model.ridged = [d / 2], he, he, he, roof["slope"], True
    elif kind == "mono":
        t = math.tan(math.radians(roof["slope"]))
        zb = max(h * 0.3, h - t * d)
        model.roof = lambda x, y=None: h - (h - zb) * x / d
        model.zb, model.slope = zb, roof["slope"]
    elif kind == "ridge":
        left, right = (math.tan(math.radians(s)) for s in roof["slopes"])
        xr = roof["ridge"] * d
        za, zb = max(0.3 * h, h - left * xr), max(0.3 * h, h - right * (d - xr))
        model.roof = lambda x, y=None: (za + (h - za) * x / xr) if x <= xr else (h - (h - zb) * (x - xr) / (d - xr))
        model.kinks, model.za, model.zb, model.slope, model.ridged = [xr], za, zb, roof["slopes"][0], True
    elif kind == "sheds":
        up, down = (math.tan(math.radians(s)) for s in roof["slopes"])
        w = d / roof["count"]
        wu = w * down / (up + down)
        valley = max(0.3 * h, h - up * wu)
        points = []
        for i in range(roof["count"]):
            points += [(i * w, valley), (i * w + wu, h)]
        points.append((d, valley))

        def z(x, y=None):
            for (x0, z0), (x1, z1) in zip(points, points[1:]):
                if x <= x1 + 1e-12:
                    return z0 + (z1 - z0) * (x - x0) / ((x1 - x0) or 1)
            return points[-1][1]
        model.roof = z
        model.kinks = [p[0] for p in points[1:-1]]
        model.za = model.zb = valley
        model.slope = roof["slopes"][0]


def _split(x0, x1, kinks):
    cuts = [x0] + [k for k in kinks if x0 + 1e-9 < k < x1 - 1e-9] + [x1]
    return list(zip(cuts, cuts[1:]))


def _wall(model, wall, u0, u1, v0, v1):
    """The polygon of a part of a wall: A and B along y, C and D along x; v up to the wall's top, which follows the roof on C and D."""
    h, b, d = model.h, model.b, model.d
    if wall in ("A", "B"):
        x = 0.0 if wall == "A" else d
        top = model.za if wall == "A" else model.zb
        return [(x, u0 * b, v0 * top), (x, u1 * b, v0 * top), (x, u1 * b, v1 * top), (x, u0 * b, v1 * top)], ((-1, 0, 0) if wall == "A" else (1, 0, 0))
    y = 0.0 if wall == "C" else b
    xa, xb = u0 * d, u1 * d
    xs = [xa] + [k for k in model.kinks if xa + 1e-9 < k < xb - 1e-9] + [xb]
    bottom = [(x, y, v0 * model.roof(x)) for x in (xa, xb)]
    top = [(x, y, v1 * model.roof(x)) for x in reversed(xs)]
    points = bottom + top
    return points, ((0, -1, 0) if wall == "C" else (0, 1, 0))


def _roof_parts(model, x0, x1, y0, y1):
    """A part of the roof as polygons, one a slope: cut at every kink of the profile."""
    b, d = model.b, model.d
    out = []
    for a, c in _split(x0 * d, x1 * d, model.kinks):
        out.append([(a, y0 * b, model.roof(a)), (c, y0 * b, model.roof(c)), (c, y1 * b, model.roof(c)), (a, y1 * b, model.roof(a))])
    return out


def _prism(geo, model):
    roof = geo["roof"]
    _profile(model, roof)
    b, d, h = model.b, model.d, model.h
    hip = roof["kind"] == "hip"
    if hip:
        ix = roof["inset"] * d
        iy = min(ix, 0.45 * b)
        eave = max(0.3 * h, h - math.tan(math.radians(roof["slope"])) * ix)
        model.za = model.zb = model.he = eave
        model.roof = lambda x, y=None: eave
        model.slope = roof["slope"]
        corners = {"A": [(0, 0, eave), (0, b, eave), (ix, b - iy, h), (ix, iy, h)], "B": [(d, 0, eave), (d - ix, iy, h), (d - ix, b - iy, h), (d, b, eave)],
                   "C": [(0, 0, eave), (ix, iy, h), (d - ix, iy, h), (d, 0, eave)], "D": [(0, b, eave), (d, b, eave), (d - ix, b - iy, h), (ix, b - iy, h)]}
    opened = set(geo.get("open", ()))
    for surface, place, x0, x1, y0, y1 in geo["zones"]:
        if place in ("A", "B", "C", "D"):
            points, normal = _wall(model, place, x0, x1, y0, y1)
            model.face(surface, points, normal, opacity=0.25 if place in opened else 1.0)
        elif place.startswith("wallstrip:"):
            points, normal = _wall(model, place.split(":")[1], x0, x1, y0, y1)
            shift = tuple(0.002 * c * max(b, d) for c in normal)
            model.face(surface, [tuple(p[k] + shift[k] for k in range(3)) for p in points], normal, layer=1, hatch=True, owner=normal)
        elif place.startswith("hip:"):
            model.face(surface, corners[place.split(":")[1]], role="roof")
        elif place in ("roof", "strip"):
            if hip:
                parts = [[(ix + a * (d - 2 * ix), iy + c * (b - 2 * iy), h) for a, c in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]]
            else:
                parts = _roof_parts(model, x0, x1, y0, y1)
            for points in parts:
                normal = m3.normal_of(points)
                if place == "roof":
                    model.face(surface, points, normal, role="roof")
                else:
                    lifted = [(p[0] + normal[0] * 0.002 * h, p[1] + normal[1] * 0.002 * h, p[2] + normal[2] * 0.002 * h) for p in points]
                    model.face(surface, lifted, normal, layer=1, hatch=True, owner=normal)


def _stand(geo, model):
    """The stand (Tableau 50): a roof cantilevered from a back wall at x = d, its top and its underside, the back wall's upper part outside and in, a sloping stand under it."""
    b, d, h = model.b, model.d, model.h
    t = math.tan(math.radians(abs(geo["slope"])))
    thick = 0.03 * h
    top = lambda x: h - t * x
    low = h - geo["roof_depth"] * h
    model.roof = lambda x, y=None: top(x)
    model.za, model.zb = h, h
    model.walls = False
    for surface, x0, x1, y0, y1 in geo["top"]:
        model.face(surface, [(x0 * d, y0 * b, top(x0 * d)), (x1 * d, y0 * b, top(x1 * d)), (x1 * d, y1 * b, top(x1 * d)), (x0 * d, y1 * b, top(x0 * d))], role="roof")
    for surface, x0, x1, y0, y1 in geo["under"]:
        points = [(x0 * d, y0 * b, top(x0 * d) - thick), (x0 * d, y1 * b, top(x0 * d) - thick), (x1 * d, y1 * b, top(x1 * d) - thick), (x1 * d, y0 * b, top(x1 * d) - thick)]
        model.face(surface, points, tuple(-c for c in m3.normal_of(points)))
    for surface, y0, y1 in geo["back_out"]:
        model.face(surface, [(d, y0 * b, low), (d, y1 * b, low), (d, y1 * b, top(d)), (d, y0 * b, top(d))], (1, 0, 0))
    for surface, y0, y1 in geo["back_in"]:
        x = d - 0.01 * d
        model.face(surface, [(x, y0 * b, low), (x, y0 * b, top(d) - thick), (x, y1 * b, top(d) - thick), (x, y1 * b, low)], (-1, 0, 0))
    # m and o, which the figure draws and the table gives no coefficient of: hatched over their surfaces, as every letter of a figure is (D-37)
    for surface, x0, x1, y0, y1 in geo.get("top_strips", ()):
        lift = 0.004 * h
        model.face(surface, [(x0 * d, y0 * b, top(x0 * d) + lift), (x1 * d, y0 * b, top(x1 * d) + lift), (x1 * d, y1 * b, top(x1 * d) + lift), (x0 * d, y1 * b, top(x0 * d) + lift)],
                   layer=1, hatch=True, role="roof")
    for surface, y0, y1, depth in geo.get("back_strips", ()):
        x, z0 = d + 0.002 * d, top(d) - depth * (top(d) - low)
        model.face(surface, [(x, y0 * b, z0), (x, y1 * b, z0), (x, y1 * b, top(d)), (x, y0 * b, top(d))], (1, 0, 0), layer=1, hatch=True)
    # the stand itself, from the ground at the front to the back wall's foot: no surface of the table
    model.face("", [(0, 0, 0), (d, 0, low * 0.9), (d, b, low * 0.9), (0, b, 0)], label=False)
    model.face("", [(d, 0, 0), (d, b, 0), (d, b, low), (d, 0, low)], (1, 0, 0), label=False)


def _canopy(geo, model):
    """A platform canopy (Tableaux 51-56): a roof on columns -- a ridge for a positive slope, a valley for a negative one --, its top E G, its underside C D, its edges A B, the zone m on the top and under it; a train under the convoy's."""
    b, d, h = model.b, model.d, model.h
    t = math.tan(math.radians(abs(geo["slope"])))
    thick = geo["thickness"] * h
    if geo["slope"] > 0:
        eave = max(0.5 * h, h - t * d / 2)
        top = lambda x: eave + (h - eave) * (1 - abs(x - d / 2) / (d / 2))
    else:
        valley = max(0.5 * h, h - t * d / 2)
        top = lambda x: valley + (h - valley) * abs(x - d / 2) / (d / 2)
    model.roof = lambda x, y=None: top(x)
    model.kinks, model.za, model.zb, model.walls = [d / 2], top(0), top(d), False
    model.slope, model.ridged = geo["slope"], geo["slope"] > 0
    for surface, x0, x1 in geo["top"]:
        for a, c in _split(x0 * d, x1 * d, model.kinks):
            model.face(surface, [(a, 0, top(a)), (c, 0, top(c)), (c, b, top(c)), (a, b, top(a))], role="roof")
    for surface, x0, x1 in geo["under"]:
        for a, c in _split(x0 * d, x1 * d, model.kinks):
            points = [(a, 0, top(a) - thick), (a, b, top(a) - thick), (c, b, top(c) - thick), (c, 0, top(c) - thick)]
            model.face(surface, points, tuple(-k for k in m3.normal_of(points)))
    for surface, x in zip(geo["edges"], (0.0, d)):
        model.face(surface, [(x, 0, top(x) - thick), (x, b, top(x) - thick), (x, b, top(x)), (x, 0, top(x))], (-1, 0, 0) if x == 0 else (1, 0, 0))
    x0, x1, y0, y1 = geo["m"]
    for a, c in _split(x0 * d, x1 * d, model.kinks):
        points = [(a, y0 * b, top(a) + 0.004 * h), (c, y0 * b, top(c) + 0.004 * h), (c, y1 * b, top(c) + 0.004 * h), (a, y1 * b, top(a) + 0.004 * h)]
        model.face("m_e", points, layer=1, hatch=True, owner=m3.normal_of(points))
        under = [(a, y0 * b, top(a) - thick - 0.004 * h), (a, y1 * b, top(a) - thick - 0.004 * h), (c, y1 * b, top(c) - thick - 0.004 * h), (c, y0 * b, top(c) - thick - 0.004 * h)]
        normal = tuple(-k for k in m3.normal_of(under))
        model.face("m_i", under, normal, layer=1, hatch=True, owner=normal)
    for y in (0.15 * b, 0.5 * b, 0.85 * b):
        model.faces.append((m3.Line((d / 2, y, 0), (d / 2, y, top(d / 2) - thick), role="muted", width=2.0), False))
    if geo["convoy"]:
        zt = 0.45 * h
        for points, normal in (([(0.15 * d, 0, 0), (0.15 * d, b, 0), (0.15 * d, b, zt), (0.15 * d, 0, zt)], (-1, 0, 0)), ([(0.85 * d, 0, 0), (0.85 * d, 0, zt), (0.85 * d, b, zt), (0.85 * d, b, 0)], (1, 0, 0)),
                               ([(0.15 * d, 0, zt), (0.85 * d, 0, zt), (0.85 * d, b, zt), (0.15 * d, b, zt)], (0, 0, 1)), ([(0.15 * d, 0, 0), (0.85 * d, 0, 0), (0.85 * d, 0, zt), (0.15 * d, 0, zt)], (0, -1, 0))):
            model.face("", points, normal, label=False, role="ground")


def _eave(geo, model):
    """An eave (Tableaux 57a-d): a building, no surface of the table, and a plate along its wall B at h1, its top I J n and its underside K L p along b."""
    b, d, h = model.b, model.d, model.h
    d1, z1, thick = geo["d1"] * d, geo["h1"] * h, 0.02 * h
    model.za = model.zb = h
    for points, normal in (([(0, 0, 0), (0, b, 0), (0, b, h), (0, 0, h)], (-1, 0, 0)), ([(d, 0, 0), (d, 0, h), (d, b, h), (d, b, 0)], (1, 0, 0)),
                           ([(0, 0, 0), (d, 0, 0), (d, 0, h), (0, 0, h)], (0, -1, 0)), ([(0, b, 0), (0, b, h), (d, b, h), (d, b, 0)], (0, 1, 0)),
                           ([(0, 0, h), (d, 0, h), (d, b, h), (0, b, h)], (0, 0, 1))):
        model.face("", points, normal, label=False)
    for surface, y0, y1 in geo["top"]:
        model.face(surface, [(d, y0 * b, z1), (d + d1, y0 * b, z1), (d + d1, y1 * b, z1), (d, y1 * b, z1)], (0, 0, 1), role="roof", hatch=surface in ("n", "p"))
    for surface, y0, y1 in geo["under"]:
        model.face(surface, [(d, y0 * b, z1 - thick), (d, y1 * b, z1 - thick), (d + d1, y1 * b, z1 - thick), (d + d1, y0 * b, z1 - thick)], (0, 0, -1), hatch=surface in ("n", "p"))
    model.d_extent = d + d1


def _curved(geo, model):
    """A dome (Tableau 63) or a vault (64): faceted, each point of measure a small mark keyed by its angle α from the windward ground on the meridian the wind blows along."""
    b, d, h = model.b, model.d, model.h
    r = d / 2
    cx, cy = d / 2, b / 2
    model.za = model.zb = 0.0
    model.walls = False
    n_a, n_b = 12, 16
    if geo["shape"] == "dome":
        model.roof = lambda x, y=None: math.sqrt(max(r * r - (x - cx) ** 2 - ((y if y is not None else cy) - cy) ** 2, 0.0))

        def at(alpha, beta):
            return (cx - r * math.cos(alpha) * math.cos(beta), cy - r * math.cos(alpha) * math.sin(beta), r * math.sin(alpha))
        for i in range(n_a):
            for j in range(n_b):
                a0, a1 = i * math.pi / 2 / n_a, (i + 1) * math.pi / 2 / n_a
                b0, b1 = j * 2 * math.pi / n_b, (j + 1) * 2 * math.pi / n_b
                points = [at(a0, b0), at(a0, b1), at(a1, b1), at(a1, b0)] if i < n_a - 1 else [at(a0, b0), at(a0, b1), at(a1, b0)]
                mid = at((a0 + a1) / 2, (b0 + b1) / 2)
                model.face("", points, _unit((mid[0] - cx, mid[1] - cy, mid[2])), label=False, role="roof")
        mark = lambda alpha: at(alpha, 0.0)
    else:
        model.roof = lambda x, y=None: math.sqrt(max(r * r - (x - cx) ** 2, 0.0))

        def arc(alpha, y):
            return (cx - r * math.cos(alpha), y, r * math.sin(alpha))
        steps = 18
        for i in range(steps):
            a0, a1 = i * math.pi / steps, (i + 1) * math.pi / steps
            mid = arc((a0 + a1) / 2, cy)
            model.face("", [arc(a0, 0), arc(a1, 0), arc(a1, b), arc(a0, b)], _unit((mid[0] - cx, 0, mid[2])), label=False, role="roof")
        for y, normal in ((0.0, (0, -1, 0)), (b, (0, 1, 0))):
            model.face("", [arc(i * math.pi / steps, y) for i in range(steps + 1)], normal, label=False)
        mark = lambda alpha: arc(alpha, cy)
    s = 0.035 * d
    for label in geo["points"]:
        alpha = math.radians(float(label.rstrip("°")))
        p = mark(alpha)
        normal = _unit((p[0] - cx, p[1] - cy if geo["shape"] == "dome" else 0.0, p[2]))
        # a small square tangent to the surface at the point, lifted off it
        tangent = (-math.sin(alpha) * (1 if normal[0] <= 0 else -1), 0.0, math.cos(alpha)) if abs(normal[1]) < 0.99 else (1.0, 0.0, 0.0)
        tangent = _unit(_cross(normal, (0, 1, 0))) if abs(normal[1]) < 0.99 else (1.0, 0.0, 0.0)
        side = (0.0, 1.0, 0.0)
        lift = tuple(p[k] + normal[k] * 0.01 * d for k in range(3))
        points = [tuple(lift[k] + (u * tangent[k] + v * side[k]) * s for k in range(3)) for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        model.face(label, points, normal, layer=1, role="strip", owner=normal)


def _unit(v):
    length = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / length for c in v)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


BUILDERS = {"prism": _prism, "open": _prism, "stand": _stand, "canopy": _canopy, "eave": _eave, "curved": _curved}


def model(number):
    """The faces of the building of Tableau `number` in its table's proportions."""
    geo = building(number)
    if geo is None:
        raise KeyError("Tableau %s has no geometry in calc/norms/%s.json" % (number, GEOMETRY))
    h, b, d = geo["hbd"]
    out = _Model(h, b, d)
    BUILDERS[geo["family"]](geo, out)
    return out


def surfaces(number):
    """The surfaces the building of Tableau `number` places -- every key of its faces."""
    return {poly.key for poly, _label in model(number).faces if isinstance(poly, m3.Polygon) and poly.key}


# --- the scene --------------------------------------------------------------------------------------------------------

def _centroid(points):
    return tuple(sum(p[k] for p in points) / len(points) for k in range(3))


def scene(number, phi=0.0, forces=None, loads=None, show_forces=True, show_phi=True, show_dims=True, words=None):
    """The scene of the building of Tableau `number`: its faces labelled, Q₁ to Q₃ -- `forces` {"f1": (value, text)}, None the bare arrows --, the direction `phi` (None or False none), b d h and α, and the load planes of `loads` {surface: q_k} at the scale of the largest. `words`: {"phi": "φ = {phi}°"} the consumer's words for what is written on the drawing."""
    words = words or {}
    mdl = model(number)
    h, b, d = mdl.h, mdl.b, mdl.d
    extent = getattr(mdl, "d_extent", d)
    rb = 0.5 * math.sqrt(extent * extent + b * b) * 1.06
    la = 0.24 * max(extent, b)
    cz = h / 2
    sc = m3.Scene(centre=(extent / 2, b / 2, cz), radius=max(rb + la, math.hypot(extent / 2, b / 2)), half_height=max(cz, 1.45 * h - cz), width=math.hypot(extent, b))
    # the ground, under everything
    sc.add(m3.Polygon([(-0.25 * extent, -0.25 * b, 0), (1.25 * extent, -0.25 * b, 0), (1.25 * extent, 1.25 * b, 0), (-0.25 * extent, 1.25 * b, 0)], role="ground", normal=(0, 0, 1), layer=-1, outline="ground"))
    labels = {}
    for item, label in mdl.faces:
        sc.add(item)
        if isinstance(item, m3.Polygon) and label and item.key:
            area = _area3(item.points)
            if item.key not in labels or labels[item.key][0] < area:
                labels[item.key] = (area, item)
    for key, (_area, poly) in labels.items():
        c = _centroid(poly.points)
        lift = tuple(c[k] + poly.normal[k] * 0.01 * max(h, d) for k in range(3))
        sc.add(m3.Text(lift, key, size=11 if poly.layer == 1 else 14, owner=poly.normal, bold=True, movable=poly.layer == 1, key=key))
    if loads:
        _loads(sc, mdl, loads)
    if show_forces:
        _forces(sc, mdl, forces)
    if show_phi is not False and phi is not None and phi is not False:
        _direction(sc, mdl, float(phi) % 360, rb, la, words.get("phi", "φ = {phi}°"))
    if show_dims:
        _dimensions(sc, mdl)
    return sc


def _area3(points):
    n = (0.0, 0.0, 0.0)
    for p, q in zip(points, points[1:] + points[:1]):
        n = (n[0] + p[1] * q[2] - p[2] * q[1], n[1] + p[2] * q[0] - p[0] * q[2], n[2] + p[0] * q[1] - p[1] * q[0])
    return 0.5 * math.sqrt(sum(c * c for c in n))


def _forces(sc, mdl, forces):
    """Q₁ onto A along +x, Q₂ onto C along +y, Q₃ down onto the roof: red a pressure, blue a suction turned away from the face, each as long as its share of the largest (UI-015); a nought force its label alone, grey."""
    h, b, d = mdl.h, mdl.b, mdl.d
    z1 = mdl.za * 0.55 if mdl.za > 0 else h * 0.4   # a curved form, nought at its foot: Q₁ at mid-height
    anchors = {"f1": ((-0.42 * d, b / 2, z1), (-0.02 * d, b / 2, z1), (-1, 0, 0), "Q₁"),
               "f2": ((d * 0.5, -0.42 * b, h * 0.45), (d * 0.5, -0.02 * b, h * 0.45), (0, -1, 0), "Q₂"),
               "f3": ((d * 0.62, b * 0.5, h * 1.42), (d * 0.62, b * 0.5, mdl.roof(d * 0.62) + 0.03 * h), (0, 0, 1), "Q₃")}
    largest = max((abs(v[0]) for v in (forces or {}).values() if v and v[0] is not None), default=0.0)
    for name, (tail, head, normal, symbol) in anchors.items():
        value = (forces or {}).get(name)
        if forces is not None and value is None:
            continue
        share = 1.0 if not value or not largest else 0.35 + 0.65 * abs(value[0]) / largest
        start = tuple(head[k] + (tail[k] - head[k]) * share for k in range(3))
        label = symbol if value is None else "%s = %s" % (symbol, value[1])
        if value is not None and abs(value[0]) < 1e-9:
            sc.add(m3.Text(start, label, role="muted", size=12, bold=True))
            continue
        role = "ink" if value is None else "pressure" if value[0] > 0 else "suction"
        a, c = (head, start) if value is not None and value[0] < 0 else (start, head)
        sc.add(m3.Arrow(a, c, role=role, label=label, owner=normal, key="force:" + name))


def _direction(sc, mdl, phi, rb, la, word):
    """φ on the ground: an arrow that turns about the building and points at it -- 0° onto A along +x, 90° onto C along +y --, the reference at 0° dashed and an arc from it (UI-012)."""
    c = (sc.centre[0], sc.centre[1], 0.0)

    def at(angle, r):
        return (c[0] - math.cos(math.radians(angle)) * r, c[1] - math.sin(math.radians(angle)) * r, 0.0)
    sc.add(m3.Line(at(0, rb), at(0, rb + la), role="direction", width=0.9, dash=True))
    if abs(phi) > 0.5:
        steps = 24
        for i in range(steps):
            sc.add(m3.Line(at(phi * i / steps, rb + 0.55 * la), at(phi * (i + 1) / steps, rb + 0.55 * la), role="direction", width=1.0, min_length=0.0))
    sc.add(m3.Arrow(at(phi, rb + la), at(phi, rb), role="direction", label=word.format(phi=int(round(phi))), key="phi"))


def _dimensions(sc, mdl):
    """b, d and h on the edges the eye sees -- each owned by the wall it runs along, so that the far ones are not drawn --, h_e at the eaves of a ridged roof with the ridge's h, and α on a gable (UI-008)."""
    h, b, d = mdl.h, mdl.b, mdl.d
    for y, normal, off in ((0.0, (0, -1, 0), -0.14 * b), (b, (0, 1, 0), 0.14 * b)):
        _dim(sc, (0, y, 0), (d, y, 0), (0, off, 0), "d", normal)
    for x, normal, off in ((0.0, (-1, 0, 0), -0.14 * d), (d, (1, 0, 0), 0.14 * d)):
        _dim(sc, (x, 0, 0), (x, b, 0), (off, 0, 0), "b", normal)
        top = mdl.he if mdl.ridged else (mdl.za if x == 0 else mdl.zb)
        if top > 0:
            _dim(sc, (x, 0, 0), (x, 0, top), (off * 0.6, -0.08 * b, 0), "hₑ" if mdl.ridged else "h", normal)
    if mdl.ridged:
        for y, normal in ((0.0, (0, -1, 0)), (b, (0, 1, 0))):
            sc.add(m3.Text((d / 2, y, h * 1.08), "h", size=12, owner=normal, bold=True))
    if mdl.slope:
        for y, normal in ((0.0, (0, -1, 0)), (b, (0, 1, 0))):
            sc.add(m3.Text((d * 0.1, y, mdl.roof(d * 0.1) + 0.1 * h), "α = %d°" % mdl.slope, size=11, owner=normal))


def _dim(sc, a, c, off, label, owner):
    pa = tuple(a[k] + off[k] for k in range(3))
    pc = tuple(c[k] + off[k] for k in range(3))
    sc.add(m3.Line(a, pa, role="muted", width=0.6, dash=True, owner=owner, min_length=0.0),
           m3.Line(c, pc, role="muted", width=0.6, dash=True, owner=owner, min_length=0.0),
           m3.Line(pa, pc, role="ink", width=0.8, owner=owner, min_length=10.0),
           m3.Text(tuple((pa[k] + pc[k]) / 2 for k in range(3)), label, size=13, owner=owner, bold=True))


def _loads(sc, mdl, loads):
    """Each surface's q_k as a load plane held off its face by arrows (as RFEM draws them): red a pressure, the arrows onto the face, blue a suction, away from it, its value in kN/m² beside it in its colour, all at the scale of the largest (UI-016, UI-017). A strip's load beside its face's."""
    h, b, d = mdl.h, mdl.b, mdl.d
    largest = max((abs(v) for v in loads.values() if v is not None), default=0.0) or 1.0
    reach = 0.3 * max(d, b / 2, h)
    done = set()
    for poly, _label in mdl.faces:
        if not isinstance(poly, m3.Polygon) or not poly.key or poly.key not in loads or loads[poly.key] is None:
            continue
        if (poly.key, poly.layer) in done and poly.layer == 0:
            continue
        value = loads[poly.key]
        normal = poly.normal
        length = reach * (0.3 + 0.7 * abs(value) / largest)
        c = _centroid(poly.points)
        k = 0.75 if poly.layer == 1 else 0.86
        ring = [tuple(c[i] + (p[i] - c[i]) * k for i in range(3)) for p in poly.points]
        off = lambda p: tuple(p[i] + normal[i] * length for i in range(3))
        role = "pressure" if value > 0 else "suction"
        sc.add(m3.Polygon([off(p) for p in ring], role=role, key="", normal=normal, layer=2, opacity=0.1, owner=normal, outline=role, width=1.0))
        points = []
        for p, q in zip(ring, ring[1:] + ring[:1]):
            points.append(p)
            if poly.layer == 0:
                points.append(tuple((p[i] + q[i]) / 2 for i in range(3)))
        for p in points:
            tail, head = (off(p), p) if value > 0 else (p, off(p))
            sc.add(m3.Arrow(tail, head, role=role, width=1.3, head_size=7, hide_owner=normal, min_length=4.0))
        sc.add(m3.Text(off(c), ("%.2f" % value).replace("-", "−") + " kN/m²", role=role, size=11, owner=normal, italic=False, bold=True, movable=True))
        done.add((poly.key, poly.layer))


# --- the views a consumer offers ------------------------------------------------------------------------------------

# Face A and Face C exactly square to their face, iso, from above (UI-009): (yaw, pitch)
VIEWS = {"A": (-90.0, 0.0), "C": (180.0, 0.0), "iso": (-131.0, 28.0), "top": (-90.0, 90.0)}
