"""SIA 261:2020 chapter 5, the snow load: the values `domains/snow_source.py` computes with, out of `sia261-2020-5.2-schnee.json` beside this module (docs/architecture/layout.md §11, issue #36).

A file of its own reader, beside `sia261.py`, as the review asked (ARCH-RISK-004): the snow's coefficients are curves and choices, checked here before anything is built from them -- a polyline whose angles do not rise, a mu outside 0..2.4 (Figur 2's own axis), an exposure listed twice, a correction the map does not give.
"""

import json
from pathlib import Path

import validation

HERE = Path(__file__).resolve().parent
SNOW = "sia261-2020-5.2-schnee"
EDITION = "SIA 261:2020"
FILES = (SNOW,)

_cache = {}


def _fail(what):
    raise validation.ValidationError("calc/norms/%s.json: %s" % (SNOW, what))


def _check_points(where, points, top):
    if not isinstance(points, list) or len(points) < 2:
        _fail("%s: a polyline of two points at least" % where)
    xs = [p[0] for p in points]
    if xs != sorted(xs) or len(set(xs)) != len(xs):
        _fail("%s: the abscissae %r do not rise" % (where, xs))
    for x, y in points:
        if not (0 <= y <= top):
            _fail("%s: %s at %s -- outside 0..%s" % (where, y, x, top))


def clause():
    """The whole clause block, read once and checked once."""
    if SNOW in _cache:
        return _cache[SNOW]
    path = HERE / (SNOW + ".json")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _fail("cannot be read -- %s" % exc)
    if data.get("edition") != EDITION:
        _fail("edition is %r -- expected %r" % (data.get("edition"), EDITION))
    c = data["clause"]
    for key in ("mu_1", "mu_2", "mu_3"):
        _check_points(key, c[key]["points"], 2.4)
    _check_points("large_flat", c["large_flat"]["points"], 2.4)
    ids = [e["id"] for e in c["exposure"]["choices"]]
    if len(set(ids)) != len(ids) or not all(e["value"] > 0 for e in c["exposure"]["choices"]):
        _fail("exposure: an id twice or a C_e not above 0")
    if 0 not in c["corrections"]["values"]:
        _fail("corrections: the map gives ± 0 m")
    s = c["s_k"]
    if not (s["factor"] > 0 and s["divisor"] > 0 and s["min"] > 0):
        _fail("s_k: factor, divisor and min above 0")
    if c["height_step"]["norm_ref"] != "5.3.6" or c["cornice"]["norm_ref"] != "5.3.7" or not 0 < c["cornice"]["min_altitude"] < c["max_altitude"]["value"]:
        _fail("height_step and cornice: 5.3.6 and 5.3.7, the cornice's altitude below the chapter's limit")
    _cache[SNOW] = c
    return c


def curve(points, x):
    """The value of a polyline of Figur 2 or 4 at x: linear between two points, constant beyond the first and the last."""
    if x <= points[0][0]:
        return float(points[0][1])
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return float(points[-1][1])


def s_k(h_ref):
    """Equation (10): the characteristic snow load on level ground at the reference altitude, kN/m², and whether its floor holds."""
    c = clause()["s_k"]
    raw = (1 + (h_ref / c["divisor"]) ** c["exponent"]) * c["factor"]
    return max(raw, c["min"]), raw < c["min"]


def exposure(choice):
    for e in clause()["exposure"]["choices"]:
        if e["id"] == choice:
            return e
    raise validation.ValidationError("exposure %r -- %s" % (choice, ", ".join(e["id"] for e in clause()["exposure"]["choices"])))


def check_all():
    clause()
