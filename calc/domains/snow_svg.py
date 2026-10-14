"""The sketch of a snow load's disposition, as SVG text (issue #36, UI-004): the roof's section and, under it, the loads of model 1 and model 2 of SIA 261 Figur 3, each block as high as its coefficient -- the third column of the figure, the curved roof, with its two triangles mu_3/2 and mu_3.

No word is written: a block carries its coefficient (μ11, μ12/2, μ2m, μ3), a row its model's number, so one SVG serves the three languages. The roof is drawn to its slopes, not to a scale. Kept to what QtSvg and resvg read alike: lines, polygons, text. No Qt here.
"""

import math

from domains import dead_load_svg, schema_svg

FONT = dead_load_svg.FONT
TEXT = 15.0
SMALL = 13.0
INK = schema_svg.TEXT_COLOR
MUTED = schema_svg.MUTED
ROOF_FILL = schema_svg.ELEMENT_FILLS[0]
SNOW_FILL = "#cfe3f3"
SNOW_STROKE = "#5a86a8"
WIDTH = 420.0          # the roof's span, drawn
LEFT = 70.0
ROW = 92.0             # the height of one row of loads
MU_UNIT = 30.0         # drawn height of mu = 1


def _f(value):
    text = ("%.1f" % value).rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


def _poly(out, points, fill, stroke, width=1.2):
    out.append('<polygon points="%s" fill="%s" stroke="%s" stroke-width="%s"/>' % (" ".join("%s,%s" % (_f(x), _f(y)) for x, y in points), fill, stroke, _f(width)))


def _text(out, x, y, content, size=SMALL, anchor="middle", colour=INK):
    out.append('<text x="%s" y="%s" font-family="%s" font-size="%s" fill="%s" text-anchor="%s">%s</text>' % (_f(x), _f(y), FONT, _f(size), colour, anchor, content))


def _line(out, x1, y1, x2, y2, colour=MUTED, width=1.0):
    out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"/>' % (_f(x1), _f(y1), _f(x2), _f(y2), colour, _f(width)))


def _mu(name):
    """μ11, μ12, μ2m, μ3 -- the subscript set as plain digits, which both renderers draw."""
    return "μ" + name.split("_", 1)[1] if "_" in name else name


def _block(out, x0, x1, base, mu, label):
    """A uniform load of coefficient `mu` from x0 to x1, its top `mu` high above `base`."""
    h = max(mu * MU_UNIT, 1.5)
    _poly(out, [(x0, base), (x0, base - h), (x1, base - h), (x1, base)], SNOW_FILL, SNOW_STROKE)
    _text(out, (x0 + x1) / 2, base - h - 4, label)


def _triangle(out, x0, x1, base, mu, label):
    h = max(mu * MU_UNIT, 1.5)
    _poly(out, [(x0, base), ((x0 + x1) / 2, base - h), (x1, base)], SNOW_FILL, SNOW_STROKE)
    _text(out, (x0 + x1) / 2, base - h - 4, label)


def _roof(out, src, top, alpha_0):
    """The roof's section between LEFT and LEFT + WIDTH, its eaves at `top + 60`: (where its loaded part starts, where it ends) -- a curved roof is loaded between the points of slope alpha_0."""
    eaves = top + 60.0
    x0, x1 = LEFT, LEFT + WIDTH
    roof = src["roof"]
    if roof == "flat":
        _poly(out, [(x0, eaves), (x0, eaves - 8), (x1, eaves - 8), (x1, eaves)], ROOF_FILL, INK)
    elif roof == "mono":
        rise = min(math.tan(math.radians(src["alpha_1"])) * WIDTH, 56.0)
        _poly(out, [(x0, eaves), (x0, eaves - 4), (x1, eaves - 4 - rise), (x1, eaves)], ROOF_FILL, INK)
    elif roof == "duo":
        r1 = math.tan(math.radians(src["alpha_1"])) * WIDTH / 2
        r2 = math.tan(math.radians(src["alpha_2"])) * WIDTH / 2
        ridge = min(max(r1, r2), 56.0)
        _poly(out, [(x0, eaves), (x0 + WIDTH / 2, eaves - ridge), (x1, eaves)], ROOF_FILL, INK)
    elif roof == "shed":
        half = WIDTH / 2
        for start in (x0, x0 + half):
            _poly(out, [(start, eaves), (start + half * 0.75, eaves - 44), (start + half, eaves)], ROOF_FILL, INK)
    else:
        radius = WIDTH / 2
        steps = 24
        points = [(x0 + radius - radius * math.cos(math.pi * k / steps), eaves - 56.0 * math.sin(math.pi * k / steps)) for k in range(steps + 1)]
        _poly(out, points, ROOF_FILL, INK)
        # the loaded part: where the tangent is under alpha_0 (an ellipse's x at that slope, close enough for a sketch)
        reach = radius * math.sin(math.radians(alpha_0))
        return x0 + radius - reach, x0 + radius + reach
    return x0, x1


def render(src, mus, alpha_0):
    """The SVG of the roof of `src` and its two load models, `mus` the coefficients the source computes ({mu_1, mu_11, mu_12, mu_2m, mu_3})."""
    out = []
    top = 10.0
    loaded = _roof(out, src, top, alpha_0)
    a, b = loaded
    middle = (a + b) / 2
    rows = top + 60 + 30
    roof = src["roof"]
    models = []
    if roof == "flat":
        models = [[("block", a, b, mus["mu_1"], "μ1")], [("block", a, b, mus["mu_1"], "μ1")]]
    elif roof == "mono":
        models = [[("block", a, b, mus["mu_1"], "μ1")], [("block", a, b, mus["mu_1"] / 2, "μ1/2")]]
    elif roof == "duo":
        models = [[("block", a, middle, mus["mu_11"], "μ11"), ("block", middle, b, mus["mu_12"], "μ12")],
                  [("block", a, middle, mus["mu_11"] / 2, "μ11/2"), ("block", middle, b, mus["mu_12"], "μ12")],
                  [("block", a, middle, mus["mu_11"], "μ11"), ("block", middle, b, mus["mu_12"] / 2, "μ12/2")]]
    elif roof == "shed":
        half = (b - a) / 2
        models = [[("block", a, a + half * 0.75, mus["mu_11"], "μ11"), ("block", a + half * 0.75, a + half, mus["mu_12"], "μ12"),
                   ("block", a + half, a + half * 1.75, mus["mu_11"], "μ11"), ("block", a + half * 1.75, b, mus["mu_12"], "μ12")],
                  [("block", a, a + half * 0.4, mus["mu_11"], "μ11"), ("triangle", a + half * 0.4, a + half * 1.6, mus["mu_2m"], "μ2m"),
                   ("block", a + half * 1.6, b, mus["mu_12"], "μ12")]]
    else:
        models = [[("block", a, b, 0.8, "0.8")],
                  [("triangle", a, middle, mus["mu_3"] / 2, "μ3/2"), ("triangle", middle, b, mus["mu_3"], "μ3")],
                  [("triangle", a, middle, mus["mu_3"], "μ3"), ("triangle", middle, b, mus["mu_3"] / 2, "μ3/2")]]
    numbers = ["1"] + ["2"] * (len(models) - 1)
    peak = max([item[3] for model in models for item in model] + [0.8])
    row_h = max(ROW, peak * MU_UNIT + 34)
    for k, (model, number) in enumerate(zip(models, numbers)):
        base = rows + (k + 1) * row_h
        _line(out, LEFT - 6, base, LEFT + WIDTH + 6, base, INK, 1.2)
        _text(out, LEFT - 26, base - 8, "(%s)" % number, TEXT)
        for kind, x0, x1, mu, label in model:
            (_block if kind == "block" else _triangle)(out, x0, x1, base, mu, label)
    height = rows + len(models) * row_h + 14
    width = LEFT + WIDTH + 30
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s" width="%s" height="%s">' % (_f(width), _f(height), _f(width), _f(height))
            + "".join(out) + "</svg>\n")
