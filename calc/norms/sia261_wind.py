"""SIA 261:2020 chapter 6 and Annexe C, the wind on buildings: the values `domains/wind_source.py` computes with (issue #37, decision D-06), out of the JSON files beside this module (docs/architecture/layout.md §11).

* `sia261-2020-6.2-wind.json` -- Tableau 4 (z_g, alpha_r), equations (11) and (12), the curves of Figur 9 (c_red) read off the PDF's vector paths, c_d of 6.3.5;
* `sia261-2020-tabNN-wind[-x].json` -- one per table of Annexe C that gives the coefficients of a building: Tableaux 31 to 60b (closed buildings, sheds, open buildings, a grandstand, platform canopies, canopies, long and tall buildings), 63 (hemispheres) and 64 (semi-cylindrical roofs). The bridges (61, 62), the cylinders (65-68), the walls and panels (69), the covered walkway (70) and the sections, wires, lattices and flags (71-76) are no buildings and are left out (D-06).

Each table file is checked here before anything is built from it -- every row as many values as the table has columns, a column a known group, a coefficient a number, a pair (±x, a/b), null or «direct» --, as the review asked (ARCH-RISK-004); the transcription itself is held against the Belastungsannahmen workbook's tables 31-45, 59a, 59b by tests/test_wind_source.py.
"""

import math
import re
from pathlib import Path

import validation
from norms import _loader  # how every reader of calc/norms/ opens its files (G3)

HERE = Path(__file__).resolve().parent
CLAUSE = "sia261-2020-6.2-wind"
EDITION = "SIA 261:2020"
GROUPS = ("cpe", "cpe_local", "cpi_opening", "cpi", "cf", "cf_snow")
# The tables of Annexe C transcribed, in the norm's order: the buildings (D-06)
NUMBERS = tuple(str(n) for n in range(31, 57)) + ("57a", "57b", "57c", "57d", "58", "59a", "59b", "60a", "60b", "63", "64")
_cache = {}


def _name(number):
    digits, suffix = re.match(r"(\d+)([a-d]?)$", number).groups()
    return "sia261-2020-tab%s-wind%s" % (digits, "-" + suffix if suffix else "")


FILES = (CLAUSE,) + tuple(_name(n) for n in NUMBERS)


_fail = _loader.fail   # calc/norms/<name>.json: <what> (G3)


def _read(name):
    if name in _cache:
        return _cache[name]
    data = _loader.load((HERE / (name + ".json")))
    _loader.edition(name, data, EDITION)
    _cache[name] = data
    return data


def _check_value(name, where, value):
    if value is None or value == "direct":
        return
    values = value if isinstance(value, list) else [value]
    if isinstance(value, list) and len(value) != 2:
        _fail(name, "%s: a pair has two values -- %r" % (where, value))
    for v in values:
        if isinstance(v, bool) or not isinstance(v, (int, float)) or abs(v) > 3:
            _fail(name, "%s: %r is no coefficient" % (where, v))


def clause():
    """6.2 and 6.3: the terrain categories, c_h, c_red's curves, c_d."""
    data = _read(CLAUSE)
    c = data["clause"]
    if [t["id"] for t in c["terrain"]["categories"]] != ["II", "IIa", "III", "IV"]:
        _fail(CLAUSE, "Tableau 4 lists II, IIa, III, IV")
    betas = [curve["beta"] for curve in c["c_red"]["curves"]]
    if betas != sorted(betas):
        _fail(CLAUSE, "the curves of Figur 9 by rising beta")
    for curve in c["c_red"]["curves"]:
        hs = [p[0] for p in curve["points"]]
        if hs != sorted(hs) or not all(0.5 <= p[1] <= 1.0 for p in curve["points"]):
            _fail(CLAUSE, "Figur 9, beta %s: heights rising, c_red in 0.5..1.0" % curve["beta"])
    rule = c["c_red"].get("directions") or {}
    if rule.get("norm_ref") != "6.3.3" or not rule.get("reference") or not 0 < (rule.get("band") or 0) < 45:
        _fail(CLAUSE, "c_red.directions: the reference directions and the band of 6.3.3")
    return c


def table(number):
    """One table of Annexe C, checked: {number, title, page, ratio, roof, columns, rows, cpe_peak, cfr, notes}."""
    if number not in NUMBERS:
        raise validation.ValidationError("Tableau %r -- the buildings of SIA 261 Annexe C are %s" % (number, ", ".join(NUMBERS)))
    name = _name(number)
    t = _read(name)["table"]
    if t["number"] != number:
        _fail(name, "carries Tableau %r" % t["number"])
    for column in t["columns"]:
        if column["group"] not in GROUPS:
            _fail(name, "column %s: group %r" % (column.get("key"), column["group"]))
    keys = [c["key"] for c in t["columns"]]
    if len(set(keys)) != len(keys):
        _fail(name, "a column twice")
    for row in t["rows"]:
        if len(row["values"]) != len(keys):
            _fail(name, "row %s: %d values for %d columns" % (row["label"], len(row["values"]), len(keys)))
        for key, value in zip(keys, row["values"]):
            _check_value(name, "row %s, %s" % (row["label"], key), value)
    return t


def tables():
    return [table(n) for n in NUMBERS]


def terrain(category):
    for t in clause()["terrain"]["categories"]:
        if t["id"] == category:
            return t
    raise validation.ValidationError("terrain category %r -- SIA 261 Tableau 4 gives II, IIa, III, IV" % (category,))


def c_h(z, category):
    """Equation (12), with the floors and the switch of 6.2.1.2: (c_h, the z it is taken at, the category whose profile it reads)."""
    c = clause()["c_h"]
    profile = "III" if category == "IV" and z > c["iv_as_iii_above"] else category
    z_used = max(z, c["z_min_IV"] if category == "IV" else c["z_min"])
    t = terrain(profile)
    return c["factor"] * ((z_used / t["z_g"]) ** t["alpha_r"] + c["offset"]) ** 2, z_used, profile


def c_red(h, beta):
    """Figur 9: c_red of a reference area by the height h (m) and beta = b/h or d/h -- linear in h along each curve, linear in log(beta) between two curves; below the lowest height read the curve's first value, beyond a curve's end its last (said by the caller, `in_range`)."""
    curves = clause()["c_red"]["curves"]

    def along(curve):
        pts = curve["points"]
        if h <= pts[0][0]:
            return pts[0][1]
        for (h0, c0), (h1, c1) in zip(pts, pts[1:]):
            if h <= h1:
                return c0 + (c1 - c0) * (h - h0) / (h1 - h0)
        return pts[-1][1]

    if beta <= curves[0]["beta"]:
        return along(curves[0])
    if beta >= curves[-1]["beta"]:
        return along(curves[-1])
    for lower, upper in zip(curves, curves[1:]):
        if beta <= upper["beta"]:
            t = (math.log(beta) - math.log(lower["beta"])) / (math.log(upper["beta"]) - math.log(lower["beta"]))
            return along(lower) + (along(upper) - along(lower)) * t


DIRECTION = re.compile(r"^([−-]?\d+(?:\.\d+)?)°$")


def direction(label):
    """The wind direction a row of an Annexe C table stands for, in degrees, read off its label («0°», «22.5°», «−30°»), or None where the label names no direction alone -- Tableau 64's «mou, φ = 0°», «φ = 90°» (spec 2026-10-12-audit-issues-47-48-49, D-18)."""
    m = DIRECTION.match(label.strip())
    return float(m.group(1).replace("−", "-")) if m else None


def oblique(label):
    """Whether 6.3.3 gives a row the more unfavourable of the two c_red: its direction is not «less than 15°» off a reference direction. A row with no direction (`direction` None) is not oblique -- it keeps its area's own value, as the table's note says."""
    rule = clause()["c_red"]["directions"]
    angle = direction(label)
    if angle is None:
        return False
    off = min(abs((angle - ref + 180) % 360 - 180) for ref in rule["reference"])
    return not off < rule["band"]


def in_range(h, beta):
    """Whether Figur 9 draws (h, beta): a curve below and above, each reaching h."""
    curves = clause()["c_red"]["curves"]
    if not curves[0]["beta"] <= beta <= curves[-1]["beta"]:
        return False
    for lower, upper in zip(curves, curves[1:]):
        if lower["beta"] <= beta <= upper["beta"]:
            return h <= min(lower["points"][-1][0], upper["points"][-1][0]) and h >= lower["points"][0][0]
    return True


def check_all():
    clause()
    tables()
