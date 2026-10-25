"""A 3D model drawn in a tab of calculation, written once and without Qt (spec 2026-10-23-onglet-vent-briques, ARCH-007, UI-008 to UI-017; its first user the wind's building, calc/domains/wind_geometry.py).

**A scene** is a list of primitives in metres -- `Polygon` (a face: its points, its outward normal, a colour role, a key it is hovered and lit by), `Line`, `Arrow` and `Text` --, and the sphere that holds everything it may draw (`Scene.bounds`): the centre, the radius in plan, the half height. The consumer builds it -- the faces of a building, its forces, a direction, its dimensions -- and names nothing of its domain here: no word, no surface, no wind. The colours are roles, resolved by `palette()` from `calc/tools/theme.json`'s `model-*` tokens in either scheme.

**A view** (`View`: yaw, pitch, zoom, the size of the drawing) projects it (`projector`): orthographic, turned about the centre, **one scale whatever the rotation** -- computed once on the sphere that holds the scene, so that turning never makes it jump (UI-009) --, the zoom about the centre, bounded so that the building is between a quarter of the drawing's width and five times it. `render(scene, view)` gives what is seen, in the order it is drawn:

* a face turned away from the eye or seen edge on is not drawn, nor what it carries (`owner`: its letter, a strip laid on it, a load on it) (UI-010);
* the faces sorted by depth, the strips over their face (`layer`), then the load planes, lines, arrows and texts;
* a line, an arrow or a dimension seen end on (shorter on the screen than `min_length`) is not drawn;
* an arrow's label beyond its end farthest from the model, never on it (UI-017); a text that would cover another moved aside with a leader (`movable`);
* what `lit` names drawn again over everything, a face lit through the model (UI-013).

`to_svg(items, view)` writes the drawing as SVG (the tests read it; nothing hidden is in it), `pick(items, x, y)` the key of the face under a point. The Qt widget is thin: calc/tools/calc_blocks.py draws the same items with a QPainter.
"""

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

THEME = Path(__file__).resolve().parents[1] / "tools" / "theme.json"
# The colour roles a scene names, each a token `model-<role>` of theme.json
ROLES = ("face", "roof", "strip", "ground", "ink", "muted", "pressure", "suction", "direction", "lit", "halo")
SEEN = 1e-3            # a face is seen where its normal turns to the eye by more than this (UI-010: edge on, not drawn)
MIN_LENGTH = 8.0       # a line, an arrow or a dimension shorter than this on the screen is seen end on, and not drawn (px)
ZOOM_MIN_SHARE, ZOOM_MAX_SHARE = 0.25, 5.0   # the model's width from a quarter of the drawing's to five times it (UI-009)


@dataclass
class Polygon:
    points: list
    role: str = "face"
    key: str = ""
    normal: tuple = None   # outward, unit; None: computed, turned up
    layer: int = 0         # 0 a face, 1 a strip laid on a face, 2 a load plane
    owner: tuple = None    # the normal of the face it lies on: hidden with it
    hatch: bool = False
    opacity: float = 1.0
    width: float = 1.0
    outline: str = "ink"


@dataclass
class Line:
    a: tuple
    b: tuple
    role: str = "ink"
    width: float = 1.0
    dash: bool = False
    owner: tuple = None
    min_length: float = MIN_LENGTH
    key: str = ""


@dataclass
class Arrow:
    tail: tuple
    head: tuple
    role: str = "ink"
    width: float = 2.2
    head_size: float = 10.0
    label: str = ""
    owner: tuple = None    # a normal: dashed and pale where it turns away (a force on a face seen from behind)
    hide_owner: tuple = None   # a normal: not drawn at all where it turns away (a load's arrow)
    key: str = ""
    min_length: float = MIN_LENGTH


@dataclass
class Text:
    at: tuple
    text: str
    role: str = "ink"
    size: float = 12.0
    owner: tuple = None
    italic: bool = True
    bold: bool = False
    movable: bool = False
    key: str = ""


@dataclass
class Scene:
    primitives: list = field(default_factory=list)
    centre: tuple = (0.0, 0.0, 0.0)
    radius: float = 1.0        # in plan, about the centre: everything the scene may draw, at any yaw
    half_height: float = 1.0   # above and below the centre
    width: float = 1.0         # the model's own width in plan, what the zoom is bounded by

    def add(self, *items):
        self.primitives.extend(items)
        return self


@dataclass
class View:
    yaw: float = -131.0
    pitch: float = 28.0
    zoom: float = 1.0
    width: int = 460
    height: int = 360
    pad: float = 18.0


def palette(scheme="light"):
    """{role: colour} of theme.json's `model-*` tokens in `scheme` -- read without Qt."""
    tokens = json.loads(THEME.read_text(encoding="utf-8"))[scheme]
    return {role: tokens["model-" + role] for role in ROLES}


def normal_of(points):
    """The unit normal of a flat polygon, turned up (z ≥ 0)."""
    a = points[0]
    for i in range(1, len(points) - 1):
        u = [points[i][k] - a[k] for k in range(3)]
        v = [points[i + 1][k] - a[k] for k in range(3)]
        n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        length = math.sqrt(sum(x * x for x in n))
        if length > 1e-12:
            n = tuple(x / length for x in n)
            return tuple(-x for x in n) if n[2] < 0 else n
    return (0.0, 0.0, 1.0)


def eye(view):
    """The direction the model is seen from: (sin yaw · cos pitch, cos yaw · cos pitch, sin pitch) -- yaw −90° looks along +x (a face whose normal is −x seen square), 180° along +y, pitch 90° from above."""
    y, p = math.radians(view.yaw), math.radians(view.pitch)
    return (math.sin(y) * math.cos(p), math.cos(y) * math.cos(p), math.sin(p))


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


class Projection:
    """Points of the scene on the drawing: `self(p)` -> (x, y, depth), depth growing towards the eye. `scale` px per metre at zoom 1, the same at every rotation; `zoom` the view's, bounded to [zoom_min, zoom_max]."""

    def __init__(self, scene, view):
        self.view = view
        self.c = scene.centre
        cy, sy = math.cos(math.radians(view.yaw)), math.sin(math.radians(view.yaw))
        cp, sp = math.cos(math.radians(view.pitch)), math.sin(math.radians(view.pitch))
        self._rot = (cy, sy, cp, sp)
        r, z = max(scene.radius, 1e-9), max(scene.half_height, 1e-9)
        self.scale = min((view.width / 2 - view.pad) / r, (view.height / 2 - view.pad) / math.sqrt(r * r + z * z))
        span = max(scene.width, 1e-9) * self.scale
        self.zoom_min = ZOOM_MIN_SHARE * view.width / span
        self.zoom_max = ZOOM_MAX_SHARE * view.width / span
        self.zoom = max(self.zoom_min, min(self.zoom_max, view.zoom or 1.0))
        self.k = self.scale * self.zoom

    def __call__(self, p):
        cy, sy, cp, sp = self._rot
        x, y, z = p[0] - self.c[0], p[1] - self.c[1], p[2] - self.c[2]
        X, Y = x * cy - y * sy, x * sy + y * cy
        return (self.view.width / 2 + X * self.k, self.view.height / 2 - (z * cp - Y * sp) * self.k, Y * cp + z * sp)


def projector(scene, view):
    return Projection(scene, view)


def _seen(normal, e):
    return normal is None or _dot(normal, e) > SEEN


def _length(p, q):
    return math.hypot(q[0] - p[0], q[1] - p[1])


def _area(points):
    return abs(sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(points, points[1:] + points[:1]))) / 2


def _arrow_parts(p, q, head_size):
    """The shaft's end and the head's three points of an arrow from p to q on the screen."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    length = math.hypot(dx, dy) or 1.0
    ux, uy = dx / length, dy / length
    hd = min(head_size, length * 0.6)
    hx, hy = q[0] - ux * hd, q[1] - uy * hd
    hw = hd / 2
    return (hx, hy), [(q[0], q[1]), (hx - uy * hw, hy + ux * hw), (hx + uy * hw, hy - ux * hw)]


def _beyond(near, far):
    """Where an arrow's label stands: past `far`, the end farthest from the model, and its anchor -- never on the arrow (UI-017)."""
    dx, dy = far[0] - near[0], far[1] - near[1]
    length = math.hypot(dx, dy) or 1.0
    vx, vy = dx / length, dy / length
    x, y = far[0] + vx * 8, far[1] + vy * 8
    anchor = "start" if vx > 0.35 else "end" if vx < -0.35 else "middle"
    y += (-4 if vy < 0 else 13) if anchor == "middle" else 4 + (6 if vy > 0.35 else -4 if vy < -0.35 else 0)
    return (x, y), anchor


def text_box(x, y, text, size, anchor):
    """The box a text takes on the screen: (left, top, width, height), its width estimated from its characters."""
    w = 0.58 * size * len(text)
    left = x - w / 2 if anchor == "middle" else x - w if anchor == "end" else x
    return (left, y - size * 0.8, w, size)


def _overlap(a, b):
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def render(scene, view, lit=()):
    """What is seen of `scene` in `view`, in drawing order: dicts {"kind": "polygon"|"line"|"arrow"|"text", ...} on the screen. `lit`, keys to draw again over everything (a face hovered, seen through the model)."""
    pr = projector(scene, view)
    e = eye(view)
    lit = set(lit or ())
    polys, rest, texts = [], [], []
    for prim in scene.primitives:
        if isinstance(prim, Polygon):
            normal = prim.normal or normal_of(prim.points)
            if not _seen(normal, e) or (prim.owner is not None and not _seen(prim.owner, e)):
                continue
            q = [pr(p) for p in prim.points]
            polys.append((prim.layer, sum(p[2] for p in q) / len(q), {"kind": "polygon", "points": [(p[0], p[1]) for p in q], "role": prim.role, "key": prim.key,
                                                                    "hatch": prim.hatch, "opacity": prim.opacity, "width": prim.width, "outline": prim.outline}))
        elif isinstance(prim, Line):
            if prim.owner is not None and not _seen(prim.owner, e):
                continue
            p, q = pr(prim.a), pr(prim.b)
            if _length(p, q) < prim.min_length:
                continue
            rest.append({"kind": "line", "a": p[:2], "b": q[:2], "role": prim.role, "width": prim.width, "dash": prim.dash, "key": prim.key})
        elif isinstance(prim, Arrow):
            if prim.hide_owner is not None and not _seen(prim.hide_owner, e):
                continue
            p, q = pr(prim.tail), pr(prim.head)
            if _length(p, q) < prim.min_length:
                continue
            behind = prim.owner is not None and not _seen(prim.owner, e)
            shaft, head = _arrow_parts(p, q, prim.head_size)
            rest.append({"kind": "arrow", "a": p[:2], "b": shaft, "head": head, "role": prim.role, "width": prim.width, "dash": behind, "opacity": 0.6 if behind else 1.0, "key": prim.key})
            if prim.label:
                near, far = (q, p) if _dot(_sub(prim.tail, scene.centre), _sub(prim.tail, scene.centre)) >= _dot(_sub(prim.head, scene.centre), _sub(prim.head, scene.centre)) else (p, q)
                at, anchor = _beyond(near, far)
                texts.append({"kind": "text", "x": at[0], "y": at[1], "text": prim.label, "role": prim.role, "size": 13, "anchor": anchor, "italic": True, "bold": True,
                              "movable": False, "key": prim.key, "arrow": (p[:2], q[:2])})
        elif isinstance(prim, Text):
            if prim.owner is not None and not _seen(prim.owner, e):
                continue
            p = pr(prim.at)
            texts.append({"kind": "text", "x": p[0], "y": p[1], "text": prim.text, "role": prim.role, "size": prim.size, "anchor": "middle", "italic": prim.italic,
                          "bold": prim.bold, "movable": prim.movable, "key": prim.key})
    polys.sort(key=lambda t: (t[0], t[1]))
    out = [t[2] for t in polys] + rest + _placed(texts)
    for poly in [t[2] for t in polys]:
        if poly["key"] and poly["key"] in lit:
            out.append(dict(poly, role="lit", opacity=0.55, hatch=False, lit=True))
    # a face hovered that is hidden: drawn whole, over everything, all the same (UI-013)
    seen_keys = {t[2]["key"] for t in polys}
    for prim in scene.primitives:
        if isinstance(prim, Polygon) and prim.key in lit and prim.key not in seen_keys and prim.layer < 2:
            q = [pr(p) for p in prim.points]
            out.append({"kind": "polygon", "points": [(p[0], p[1]) for p in q], "role": "lit", "key": prim.key, "hatch": False, "opacity": 0.55, "width": 1.0, "outline": "lit", "lit": True})
    return out


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _placed(texts):
    """The texts, those that may move set aside where they would cover one already placed, with a leader to where they belong (UI-016)."""
    placed, out = [], []
    for t in sorted(texts, key=lambda t: t["movable"]):
        box = text_box(t["x"], t["y"], t["text"], t["size"], t["anchor"])
        if t["movable"]:
            step = t["size"]
            tries = [(0, 0)] + [d for i in range(1, 8) for d in ((0, i * step), (0, -i * step), (i * step * 1.6, 0), (-i * step * 1.6, 0), (i * step, i * step), (-i * step, -i * step))]
            for dx, dy in tries:
                moved = (box[0] + dx, box[1] + dy, box[2], box[3])
                if not any(_overlap(moved, o) for o in placed):
                    break
            else:
                dx, dy = 0, 0
            if dx or dy:
                out.append({"kind": "line", "a": (t["x"], t["y"] - t["size"] * 0.3), "b": (t["x"] + dx, t["y"] + dy - t["size"] * 0.3), "role": t["role"], "width": 0.7, "dash": True, "key": ""})
                t = dict(t, x=t["x"] + dx, y=t["y"] + dy)
                box = (box[0] + dx, box[1] + dy, box[2], box[3])
        placed.append(box)
        out.append(t)
    return out


def _f(x):
    return "%.1f" % x


def to_svg(items, view, colours=None):
    """The drawing as SVG -- what the tests read, nothing hidden in it."""
    colours = colours or palette()
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">' % (view.width, view.height, view.width, view.height),
           '<defs><pattern id="m3h" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="5" height="5" fill="%s"/><line x1="0" y1="0" x2="0" y2="5" stroke="%s" stroke-width="0.9"/></pattern></defs>'
           % (colours["strip"], colours["ink"])]
    for it in items:
        key = (' data-key="%s"' % it["key"]) if it.get("key") else ""
        if it["kind"] == "polygon":
            d = "M" + "L".join("%s,%s" % (_f(x), _f(y)) for x, y in it["points"]) + "Z"
            fill = "url(#m3h)" if it["hatch"] else colours[it["role"]]
            out.append('<path%s d="%s" fill="%s" fill-opacity="%g" stroke="%s" stroke-width="%g"/>' % (key, d, fill, it["opacity"], colours[it["outline"]], it["width"]))
        elif it["kind"] == "line":
            dash = ' stroke-dasharray="4 3"' if it["dash"] else ""
            out.append('<line%s x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%g"%s/>' % (key, _f(it["a"][0]), _f(it["a"][1]), _f(it["b"][0]), _f(it["b"][1]), colours[it["role"]], it["width"], dash))
        elif it["kind"] == "arrow":
            dash = ' stroke-dasharray="5 3"' if it["dash"] else ""
            col = colours[it["role"]]
            out.append('<g%s opacity="%g"><line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%g"%s/><polygon points="%s" fill="%s"/></g>'
                       % (key, it["opacity"], _f(it["a"][0]), _f(it["a"][1]), _f(it["b"][0]), _f(it["b"][1]), col, it["width"], dash,
                          " ".join("%s,%s" % (_f(x), _f(y)) for x, y in it["head"]), col))
        elif it["kind"] == "text":
            style = (' font-style="italic"' if it["italic"] else "") + (' font-weight="bold"' if it["bold"] else "")
            text = it["text"].replace("&", "&amp;").replace("<", "&lt;")
            out.append('<text%s x="%s" y="%s" font-size="%g" font-family="Arial, Helvetica, sans-serif" fill="%s" text-anchor="%s"%s paint-order="stroke" stroke="%s" stroke-width="3">%s</text>'
                       % (key, _f(it["x"]), _f(it["y"]), it["size"], colours[it["role"]], it["anchor"], style, colours["halo"], text))
    out.append("</svg>")
    return "\n".join(out) + "\n"


def _inside(point, polygon):
    x, y = point
    inside = False
    for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / ((y2 - y1) or 1e-12):
            inside = not inside
    return inside


def pick(items, x, y):
    """The key of the face drawn on top under (x, y) -- a strip over its face --, None where there is none."""
    for it in reversed(items):
        if it["kind"] == "polygon" and it.get("key") and not it.get("lit") and _inside((x, y), it["points"]):
            return it["key"]
    return None


def texts(items):
    """The words a drawing shows, in order -- what a test reads."""
    return [it["text"] for it in items if it["kind"] == "text"]
