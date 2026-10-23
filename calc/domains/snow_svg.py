"""The drawings of a snow load, as SVG text: the column of SIA 261 Figur 3 for the case's roof, the five roofs' tiles, and the data of Figur 2's chart (spec 2026-10-22-onglet-neige-type, REQ-016, UI-009, UI-010, ARCH-008; issue #36, UI-004 before it).

**One code for the tab and the report** (ARCH-008): `figure` draws the roof above its structure -- the «petit rectangle» that says the roof stands on walls --, its slopes α₁ and α₂ (α and α₀ = 60° for a curved roof), then the load models 1 and 2 as the norm draws them, each block as high as its coefficient and written «μ₁₁ = 0.80», and under them the row of the definitions with their values. It is drawn **in black and white, in the style of Figur 3** (T39): the figure palette's ink, ground and muted grey, nothing else (tests hold it).

**No words in the report's drawing** (D-31): the report is compiled in its language after the export wrote the SVG, so the figure the export writes carries symbols and values only -- «(1)», «(2)», «μ₁₁ = 0.80» -- and the words, «Modèle de charge 1 et 2», are the Typst caption's. The tab hands `words` (its language's, read from the glossary) and gets the same drawing with the models named in its left column. The geometry is the prototype's (`geometry()`, `fig3()`, `tileIcon()`, commit 5f2b2dc).

Kept to what QtSvg and resvg read alike: lines, polylines, polygons, rectangles, an arc path, and text set by svg_text (a subscript a <text> of its own). Deterministic: the same case gives the same bytes (the export stays reproducible). No Qt here.
"""

import math

from domains import svg_draw  # the one writer of an SVG number and text (D6)
from domains import svg_text

INK = svg_draw.colour("ink")
GROUND = svg_draw.colour("ground")
GREY = svg_draw.colour("muted")
TEXT = 10.5
_f = svg_draw.number_at(1)   # a coordinate at 1 decimal (svg_draw.py, D6)


def _two(value):
    return "%.2f" % (round(value * 100) / 100)


def _deg(value):
    return "%d" % round(value)


def _line(out, x1, y1, x2, y2, colour=INK, width=1.0, dash=""):
    out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"%s/>'
               % (_f(x1), _f(y1), _f(x2), _f(y2), colour, _f(width), ' stroke-dasharray="%s"' % dash if dash else ""))


def _polyline(out, points, colour=INK, width=1.0, dash=""):
    out.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="%s"%s/>'
               % (" ".join("%s,%s" % (_f(x), _f(y)) for x, y in points), colour, _f(width), ' stroke-dasharray="%s"' % dash if dash else ""))


def _polygon(out, points, fill=GROUND, colour=INK, width=1.0):
    out.append('<polygon points="%s" fill="%s" stroke="%s" stroke-width="%s"/>'
               % (" ".join("%s,%s" % (_f(x), _f(y)) for x, y in points), fill, colour, _f(width)))


def _rect(out, x, y, w, h):
    out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="%s" stroke="%s" stroke-width="1"/>' % (_f(x), _f(y), _f(max(w, 0)), _f(max(h, 0)), GROUND, INK))


def _text(out, x, y, content, size=TEXT, anchor="start"):
    """A label on its baseline at `y`, its subscripts written `μ_11` (svg_text.draw centres on the point: lowered here by a third of the size)."""
    svg_text.draw(out, (x, y - 0.35 * size), content, size, INK, anchor)


def _arc_angle(out, cx, cy, r, start, end, label, side, size=TEXT):
    """An angle from the horizontal to the roof's line, an arc with an arrow head at both ends, as the norm draws them."""
    a0, a1 = math.radians(start), math.radians(end)
    x0, y0, x1, y1 = cx + r * math.cos(a0), cy - r * math.sin(a0), cx + r * math.cos(a1), cy - r * math.sin(a1)
    sweep = 0 if end > start else 1
    out.append('<path d="M%s,%s A%s,%s 0 0 %d %s,%s" fill="none" stroke="%s" stroke-width="0.9"/>' % (_f(x0), _f(y0), _f(r), _f(r), sweep, _f(x1), _f(y1), INK))

    def head(x, y, ang):
        dx, dy, n = math.cos(ang), math.sin(ang), 4
        _polygon(out, [(x, y), (x - n * dx + 2 * dy, y - n * dy - 2 * dx), (x - n * dx - 2 * dy, y - n * dy + 2 * dx)], INK, INK, 0.6)
    t0 = a0 + (-math.pi / 2 if end > start else math.pi / 2)
    t1 = a1 + (math.pi / 2 if end > start else -math.pi / 2)
    head(x0, y0, -t0)
    head(x1, y1, -t1)
    if label:
        mid = (a0 + a1) / 2
        lx = cx + (r + 5) * math.cos(mid) + (4 if side == "r" else -4)
        ly = cy - (r + 3) * math.sin(mid) + 4
        _text(out, lx, ly, label, size, "start" if side == "r" else "end")


def geometry(out, roof, v, x0, x1, top, bot):
    """The roof's elevation over its walls between x0 and x1, its ridge under `top`, its walls down to `bot` -- true slopes, the building narrowed and centred where the roof would not fit. `v` holds the slopes (`a1`, `a2`) and the labels (`l1`, `l2`, `la`, `l0`, `dims`, `ar` the radius of an angle); returns where the loads are drawn ({x0, x1, xr, w, d, x60, cx})."""
    wall = bot
    min_wall = max(12.0, (bot - top) * 0.24)
    avail = bot - top - min_wall - 2

    def deg(a):
        return max(0.0, min(89.0, a))

    def fit(h_full, span):
        k = avail / h_full if h_full > avail else 1.0
        cx, w = (x0 + x1) / 2, span * k
        h = h_full * k
        wy = min(bot - min_wall, max(top + h + 2, top + (bot - top) * 0.42))
        return {"a": cx - w / 2, "b": cx + w / 2, "h": h, "wy": wy, "w": w}
    span = x1 - x0
    ar = v.get("ar")
    at = {}
    if roof == "flat":
        wy = top + (bot - top) * 0.42
        _line(out, x0, wy, x1, wy, INK, 1.4)
        _line(out, x0, wy, x0, wall, GREY)
        _line(out, x1, wy, x1, wall, GREY)
        _line(out, x0, wall, x1, wall, GREY)
        if v.get("dims"):
            _text(out, (x0 + x1) / 2, wy - 6, v["dims"], TEXT, "middle")
        at.update(x0=x0, x1=x1)
    elif roof == "mono":
        g = fit(math.tan(math.radians(deg(v["a1"]))) * span, span)
        _line(out, g["a"], g["wy"], g["b"], g["wy"] - g["h"], INK, 1.4)
        _line(out, g["a"], g["wy"], g["a"], wall, GREY)
        _line(out, g["b"], g["wy"] - g["h"], g["b"], wall, GREY)
        _line(out, g["a"], wall, g["b"], wall, GREY)
        _line(out, g["a"], g["wy"], g["a"] + (ar * 1.6 if ar else 34), g["wy"], INK, 0.8)
        _arc_angle(out, g["a"], g["wy"], ar or 22, 0, deg(v["a1"]), v.get("la"), "r")
        at.update(x0=g["a"], x1=g["b"])
    elif roof == "duo":
        t1, t2 = math.tan(math.radians(deg(v["a1"]))), math.tan(math.radians(deg(v["a2"])))
        f = t2 / (t1 + t2) if (t1 + t2) else 0.5
        g = fit(t1 * f * span, span)
        xr = g["a"] + g["w"] * f
        _polyline(out, [(g["a"], g["wy"]), (xr, g["wy"] - g["h"]), (g["b"], g["wy"])], INK, 1.4)
        _line(out, g["a"], g["wy"], g["a"], wall, GREY)
        _line(out, g["b"], g["wy"], g["b"], wall, GREY)
        _line(out, g["a"], wall, g["b"], wall, GREY)
        _line(out, g["a"], g["wy"], g["a"] + (ar * 1.6 if ar else 34), g["wy"], INK, 0.8)
        _arc_angle(out, g["a"], g["wy"], ar or 22, 0, deg(v["a1"]), v.get("l1"), "r")
        _line(out, g["b"] - (ar * 1.6 if ar else 34), g["wy"], g["b"], g["wy"], INK, 0.8)
        _arc_angle(out, g["b"], g["wy"], ar or 22, 180, 180 - deg(v["a2"]), v.get("l2"), "l")
        at.update(x0=g["a"], xr=xr, x1=g["b"])
    elif roof == "shed":
        # two sheds: the steep side α₁ rises from the valley, the long side α₂ falls to the next valley
        t1, t2 = math.tan(math.radians(deg(v["a1"]))), math.tan(math.radians(deg(v["a2"])))
        f = t2 / (t1 + t2) if (t1 + t2) else 0.5
        g = fit(t1 * f * span / 2, span)
        w = g["w"] / 2
        d = w * f
        points = []
        for i in range(2):
            vx = g["a"] + i * w
            points += [(vx, g["wy"]), (vx + d, g["wy"] - g["h"])]
        points.append((g["b"], g["wy"]))
        _line(out, g["a"] - 16, g["wy"] - g["h"] * 0.5, g["a"], g["wy"], INK, 0.9, "2 2")
        _line(out, g["b"], g["wy"], g["b"] + 14, g["wy"] - g["h"] * 0.6, INK, 0.9, "2 2")
        _polyline(out, points, INK, 1.4)
        for i in range(3):
            _line(out, g["a"] + i * w, g["wy"], g["a"] + i * w, wall, GREY)
        _line(out, g["a"] - 14, wall, g["b"] + 14, wall, GREY, 1, "2 2")
        _line(out, g["a"], wall, g["b"], wall, GREY)
        _line(out, g["a"], g["wy"], g["a"] + (ar * 1.6 if ar else 30), g["wy"], INK, 0.8)
        _arc_angle(out, g["a"], g["wy"], ar or 18, 0, deg(v["a1"]), v.get("l1"), "r")
        _line(out, g["b"] - (ar * 1.6 if ar else 30), g["wy"], g["b"], g["wy"], INK, 0.8)
        _arc_angle(out, g["b"], g["wy"], ar or 18, 180, 180 - deg(v["a2"]), v.get("l2"), "l")
        at.update(x0=g["a"], w=w, d=d, x1=g["b"])
    else:
        # the curved roof: a semicircle over the walls, the chords, α and α₀ = 60°
        r = min(span / 2, avail)
        cx = (x0 + x1) / 2
        xa, xb = cx - r, cx + r
        cy = min(bot - min_wall, top + r + 2)
        out.append('<path d="M%s,%s A%s,%s 0 0 1 %s,%s" fill="none" stroke="%s" stroke-width="1.4"/>' % (_f(xa), _f(cy), _f(r), _f(r), _f(xb), _f(cy), INK))
        alpha_0 = v.get("alpha_0", 60)
        x60 = cx - r * math.cos(math.radians(90 - alpha_0))   # where the slope is alpha_0
        y60 = cy - r * math.sin(math.radians(90 - alpha_0))
        _line(out, xa, cy, xb, cy, INK, 0.8)
        _line(out, xa, wall, xb, wall, GREY)
        _line(out, xa, cy, xa, wall, GREY)
        _line(out, xb, cy, xb, wall, GREY)
        _line(out, x60, y60, x60, wall, GREY, 0.8, "3 2")
        _line(out, 2 * cx - x60, y60, 2 * cx - x60, wall, GREY, 0.8, "3 2")
        _polyline(out, [(x60, y60), (cx, cy - r), (2 * cx - x60, y60)], INK, 0.8, "2 2")
        _line(out, xa, cy, cx, cy - r, INK, 0.6, "2 2")
        _arc_angle(out, x60, y60, ar or 16, 0, alpha_0, v.get("l0") or "α_0", "r")
        _line(out, x60, y60, x60 + 22, y60, INK, 0.6, "2 2")
        _arc_angle(out, xa, cy, ar or 22, 0, min(89.0, v["a1"]), v.get("la"), "r")
        at.update(x60=x60, cx=cx, x0=xa, x1=xb)
    return at


def _svg(width, height, body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s" width="%s" height="%s">' % (_f(width), _f(height), _f(width), _f(height))
            + "".join(body) + "</svg>\n")


def figure(src, mus, alpha_0, words=None):
    """The column of SIA 261 Figur 3 for the roof of `src`: its elevation, model 1, model 2 (none for a flat roof), the row of the definitions -- `mus` the coefficients the source computes ({mu_1, mu_11, mu_12, mu_2m, mu_3}, from snow_source.coefficients), `alpha_0` Figur 3's 60°. `words` names the models in the left column ({"lm1", "lm2", "one"}: the tab's); without it the column says «(1)» and «(2)» and the figure carries no word (the report's, D-31)."""
    roof = src["roof"]
    lab = 108 if words else 40
    w0 = 400 if words else 332
    x0, x1 = lab + 18, w0 - 16
    has_m2 = roof != "flat"
    m2_rows = 2 if roof in ("duo", "curved") else 1
    g_h, m1_h = 150, 70
    m2_h = 76 * m2_rows if has_m2 else (30 if words else 0)
    f_h = 26
    height = g_h + m1_h + m2_h + f_h
    out = ['<rect x="0" y="0" width="%s" height="%s" fill="%s"/>' % (_f(w0), _f(height), GROUND)]
    # the table of the figure
    _line(out, lab, 0, w0 - 0.5, 0, INK, 0.8)
    _line(out, lab, 0, lab, height, INK, 0.8)
    _line(out, w0 - 0.5, 0, w0 - 0.5, height, INK, 0.8)
    for y in (g_h, g_h + m1_h, g_h + m1_h + m2_h, height - 0.5):
        _line(out, 0, y, w0, y, INK, 0.8)
    _line(out, 0.5, g_h, 0.5, height, INK, 0.8)
    if words:
        _text(out, 8, g_h + m1_h / 2 + 4, words.get("lm1", ""), 10)
        if has_m2:
            _text(out, 8, g_h + m1_h + m2_h / 2 + 4, words.get("lm2", ""), 10)
    else:
        _text(out, lab / 2, g_h + m1_h / 2 + 4, "(1)", 10, "middle")
        if has_m2:
            _text(out, lab / 2, g_h + m1_h + m2_h / 2 + 4, "(2)", 10, "middle")
    a1 = float(src.get("alpha_1") or 0)
    a2 = float(src.get("alpha_2") or 0)
    dims = ""
    if roof == "flat":
        dims = "L = %s m · B = %s m" % (svg_draw.number(float(src.get("length") or 0), 2), svg_draw.number(float(src.get("width") or 0), 2))
    v = {"a1": a1, "a2": a2, "alpha_0": alpha_0, "l0": "α_0 = %s°" % _deg(alpha_0), "l1": "α_1 = %s°" % _deg(a1), "l2": "α_2 = %s°" % _deg(a2),
         "la": "α = %s°" % _deg(a1), "dims": dims}
    at = geometry(out, roof, v, x0, x1, 12, g_h - 10)

    def mu(name):
        return mus.get(name, 0.8)
    top_mu = max([0.8] + list(mus.values()))

    def scale(h):
        return (h - 26) / max(top_mu, 0.8)

    def base(y):
        _line(out, x0 - 8, y, x1 + 8, y, GREY, 2)

    def label(x, y, content, anchor="start"):
        _text(out, x, y - 3, content, TEXT, anchor)
    # model 1
    b1, u1 = g_h + m1_h - 12, scale(m1_h)
    bx0, bx1 = at["x0"], at["x1"]
    if roof == "curved":
        bx0, bx1 = at["x60"], 2 * at["cx"] - at["x60"]
    base(b1)
    if roof in ("flat", "mono"):
        m = mu("mu_1")
        _rect(out, bx0, b1 - m * u1, bx1 - bx0, m * u1)
        label(bx1 - 2, b1 - m * u1, "μ_1 = " + _two(m), "end")
    elif roof == "duo":
        xr, m11, m12 = at["xr"], mu("mu_11"), mu("mu_12")
        _rect(out, bx0, b1 - m11 * u1, xr - bx0, m11 * u1)
        _rect(out, xr, b1 - m12 * u1, bx1 - xr, m12 * u1)
        label(bx0 + 2, b1 - m11 * u1, "μ_11 = " + _two(m11))
        label(bx1 - 2, b1 - m12 * u1, "μ_12 = " + _two(m12), "end")
    elif roof == "shed":
        w, d, m11, m12 = at["w"], at["d"], mu("mu_11"), mu("mu_12")
        for i in range(2):
            vx = bx0 + i * w
            _rect(out, vx, b1 - m11 * u1, d, m11 * u1)
            _rect(out, vx + d, b1 - m12 * u1, w - d, m12 * u1)
        label(bx0, b1 - max(m11, m12) * u1 - 11, "μ_11 = " + _two(m11))
        label(bx0 + w - 2, b1 - m12 * u1, "μ_12 = " + _two(m12), "end")
    else:
        _rect(out, bx0, b1 - 0.8 * u1, bx1 - bx0, 0.8 * u1)
        label(bx1 - 2, b1 - 0.8 * u1, _two(0.8), "end")
    # model 2
    y2 = g_h + m1_h
    if not has_m2:
        if words and words.get("one"):
            _text(out, (x0 + x1) / 2, y2 + 19, words["one"], TEXT, "middle")
    elif roof == "mono":
        b, u, m = y2 + m2_h - 12, scale(m2_h), mu("mu_1")
        base(b)
        _rect(out, bx0, b - m / 2 * u, bx1 - bx0, m / 2 * u)
        label(bx1 - 2, b - m / 2 * u, "μ_1/2 = " + _two(m / 2), "end")
    elif roof == "duo":
        xr, m11, m12 = at["xr"], mu("mu_11"), mu("mu_12")
        for j, (left, right, ls, rs) in enumerate(((m11 / 2, m12, "μ_11/2", "μ_12"), (m11, m12 / 2, "μ_11", "μ_12/2"))):
            b, u = y2 + 76 * (j + 1) - 12, scale(76)
            base(b)
            _rect(out, bx0, b - left * u, xr - bx0, left * u)
            _rect(out, xr, b - right * u, bx1 - xr, right * u)
            label(bx0 + 2, b - left * u, ls + " = " + _two(left))
            label(bx1 - 2, b - right * u, rs + " = " + _two(right), "end")
    elif roof == "shed":
        w, d, m11, m12, m2m = at["w"], at["d"], mu("mu_11"), mu("mu_12"), mu("mu_2m")
        b, u = y2 + m2_h - 12, scale(m2_h)
        vx1 = bx0 + w
        base(b)
        _rect(out, bx0, b - m11 * u, d, m11 * u)
        _polygon(out, [(bx0 + d, b), (vx1, b - m2m * u), (vx1, b)])
        _polygon(out, [(vx1, b), (vx1, b - m2m * u), (vx1 + d, b - m12 * u), (vx1 + d, b)])
        _rect(out, vx1 + d, b - m12 * u, w - d, m12 * u)
        label(bx0, b - m11 * u, "μ_11 = " + _two(m11))
        label(vx1 + 3, b - m2m * u, "μ_(2m) = " + _two(m2m))
        label(bx1 - 2, b - m12 * u, "μ_12 = " + _two(m12), "end")
    else:
        m3, cx, xa, xb = mu("mu_3"), at["cx"], bx0, bx1
        for j, (left, right, ls, rs) in enumerate(((m3 / 2, m3, "μ_3/2", "μ_3"), (m3, m3 / 2, "μ_3", "μ_3/2"))):
            b, u = y2 + 76 * (j + 1) - 12, scale(76)
            la, rb = (xa + cx) / 2, (cx + xb) / 2
            base(b)
            _polygon(out, [(xa, b), (la, b - left * u), (cx, b)])
            _line(out, la, b, la, b - left * u)
            _polygon(out, [(cx, b), (rb, b - right * u), (xb, b)])
            _line(out, rb, b, rb, b - right * u)
            label(la + 3, b - left * u, ls + " = " + _two(left))
            label(rb + 3, b - right * u, rs + " = " + _two(right))
    # the row of the definitions, with their values -- one space between their parts: SVG folds two into one, which svg_text would measure as two
    if roof == "flat":
        foot = "μ_1 = " + _two(mu("mu_1"))
    elif roof == "mono":
        foot = "μ_1 = μ_1(α) = " + _two(mu("mu_1"))
    elif roof == "duo":
        foot = "μ_11 = μ_1(α_1) = %s · μ_12 = μ_1(α_2) = %s" % (_two(mu("mu_11")), _two(mu("mu_12")))
    elif roof == "shed":
        foot = "μ_(2m) = μ_2((α_1 + α_2)/2) = " + _two(mu("mu_2m"))
    else:
        foot = "μ_3 = μ_3(α) = %s · α_0 = %s°" % (_two(mu("mu_3")), _deg(alpha_0))
    _text(out, (lab + w0) / 2, height - 9, foot, TEXT, "middle")
    return _svg(w0, height, out)


def tile(roof):
    """The tile of a roof form in the form (T39): its elevation alone, small, its slopes named α₁ and α₂ (α and α₀ for a curved roof) -- no number, the tile choosing the form and not the case."""
    v = {"a1": 30.0, "a2": 30.0, "l1": "α_1", "l2": "α_2", "la": "α", "l0": "α_0", "dims": "", "ar": 10}
    if roof == "shed":
        v.update(a1=55.0, a2=20.0)
    out = ['<rect width="98" height="64" fill="%s"/>' % GROUND]
    geometry(out, roof, v, 14, 84, 4, 58)
    return _svg(98, 64, out)


def chart(points, marks, x_max=70.0, y_max=2.4):
    """Figur 2 as the data of an interactive chart (UI-010): its series -- each `(name, [(alpha, mu)…])`, the polylines the calculation reads, carried constant to `x_max` -- and the case's marks, `(label, alpha, mu, series)`. The window draws it and reads a value off it at the pointer (calc/tools/calc_tab.py); it knows neither α nor μ."""
    series = []
    for name, line in points:
        line = [tuple(p) for p in line]
        if line[-1][0] < x_max:
            line.append((x_max, line[-1][1]))
        series.append({"name": name, "points": line})
    return {"x": {"min": 0.0, "max": x_max, "label": "α", "unit": "°", "step": 10.0}, "y": {"min": 0.0, "max": y_max, "label": "μ", "unit": "", "step": 0.4},
            "series": series, "marks": [{"label": label, "x": x, "y": y, "series": s} for label, x, y, s in marks]}
