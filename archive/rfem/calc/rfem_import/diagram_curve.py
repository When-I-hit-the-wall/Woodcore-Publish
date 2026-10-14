"""The shape of a moment diagram *between* two stations RFEM exported.

An RFEM table lists a member's internal forces at its **characteristic points** and nowhere else: the two ends, the nodes, wherever a load is discontinuous, and the extremes. The engineer's own beam, 4.23 m under a uniform load, comes out of CO1 with four rows — x = 0, 2.115, 2.115, 4.23 — so a polyline through them draws a **triangle** where the diagram is a parabola. The curve RFEM shows on screen is drawn from ten divisions it keeps in the model and does not write into the table.

**What this module does, and it is the one place in the RFEM import that does arithmetic:** it reads the shape back out of the numbers already exported, using the relation every internal-force diagram obeys — **the shear is the slope of the moment**. With M and V known at both ends of a segment, the moment between them is fixed: value and slope at two points are four conditions, and a cubic has four coefficients, so the Hermite interpolant *is* the diagram. Under a uniform load, where V is linear and M quadratic, it is exact; under a linearly varying load, where M is cubic, it is exact too.

⚠️ **This is not a recalculation of the structure and must never become one.** Nothing here reads a load, a stiffness or a support: it integrates values RFEM itself wrote down, between two of its own stations, and every endpoint of the reconstruction is RFEM's own number to the digit. The rule of §3.3duodecies stands — Woodcore computes nothing, it shows what RFEM computed — and this is the thinnest possible reading of «shows»: the same data, at the abscissae between the ones printed.

⚠️ **The sign of the relation is measured, never assumed.** Which shear is the slope of which moment, and with which sign, is a convention — RFEM's own, and it differs between programs and between a local and a global axis system. So `slope_sign` tries both signs over every segment of every member of one table and keeps the one whose integral reproduces the exported moments; where neither does, the reconstruction is **refused** and the polyline is drawn through the stations exactly as before. A diagram this module cannot verify is a diagram it does not touch.

👉 Verified on the engineer's own export, CO1, member 2: integrating V_z from x = 0 to 2.115 gives **−8.527614** where RFEM exports **−8.527615**.

⚠️ **Only the moments are reconstructed.** N, V and M_T are drawn through their stations as they always were: a shear under a uniform load is already linear, so the polyline is already exact, and a torsional moment has no such relation to anything else in the table.

⚠️ **The values written on the figure stay RFEM's.** The refinement adds points to the *drawn* line and to nothing else, so a number printed beside a diagram is one RFEM exported and never one computed here. The true peak of a parabola falls between two stations and is therefore not labelled — it is read from the envelope tables instead (`results.py`), where RFEM states it with the combination that produced it.
"""

# Which exported quantity is the slope of which moment, along the member's own axis.
# M_T is deliberately absent: torsion is tied to nothing else the table carries.
SLOPE_OF = {"M_y": "V_z", "M_z": "V_y"}

# How many pieces one segment is drawn in. Twelve is what makes a parabola read as a parabola at the size a
# report prints a figure; the cost is a polyline of a few dozen points, which an SVG does not notice.
STEPS = 12

# Two stations closer together than this are the same abscissa -- the jump a point load writes, which RFEM
# exports as two rows at one x and which must stay a jump (`diagram_svg`).
SAME_X = 1e-9

# How far the integral of the slope may fall from the exported change in the moment, relative to the largest
# change the table holds, before the reconstruction is refused. A **wrong sign** doubles the error, so the two
# answers are never close; what this tolerance really allows for is a load whose shear is not linear, where the
# trapezoid under-reads a little. Measured: the engineer's own export answers at 1e-9.
TOLERANCE = 0.25


def hermite(t, p0, p1, m0, m1, h):
    """The cubic through `p0` and `p1` whose slopes there are `m0` and `m1`, at `t` in [0, 1] over a span `h`.

    Value and slope at two points are four conditions and a cubic has four coefficients, so this is the only
    cubic that fits -- and therefore *is* the moment diagram wherever that diagram is a polynomial of degree
    three or less, which a uniform or linearly varying load makes it.
    """
    t2 = t * t
    t3 = t2 * t
    return ((2 * t3 - 3 * t2 + 1) * p0
            + (t3 - 2 * t2 + t) * h * m0
            + (-2 * t3 + 3 * t2) * p1
            + (t3 - t2) * h * m1)


def _segments(points):
    """The consecutive pairs of `points` that span a real distance -- every jump at one abscissa left out."""
    for (x0, p0, m0), (x1, p1, m1) in zip(points, points[1:]):
        if x1 - x0 > SAME_X and m0 is not None and m1 is not None:
            yield (x0, p0, m0), (x1, p1, m1)


def slope_sign(curves):
    """Whether the slope quantity is `+1`, `−1` or `0` times the moment's derivative, over a whole table.

    `curves` is `{member: [(x, value, slope), …]}`. Decided **once per table** rather than per member, because a
    convention is a property of the program that wrote the file and not of one beam; and returned as `0` --
    *do not reconstruct* -- where neither sign reproduces what RFEM exported, so that an unrecognised export
    draws exactly the polyline it drew before rather than a curve nobody can vouch for.
    """
    errors = {1: 0.0, -1: 0.0}
    scale = 0.0
    for points in curves.values():
        for (x0, p0, m0), (x1, p1, m1) in _segments(points):
            span = x1 - x0
            change = p1 - p0
            scale = max(scale, abs(change))
            for sign in (1, -1):
                integral = sign * (m0 + m1) / 2.0 * span
                errors[sign] += abs(integral - change)
    if scale <= 0.0:
        # Nothing varies -- a diagram that is flat everywhere, which every sign draws alike.
        return 0
    best = min(errors, key=lambda sign: errors[sign])
    return best if errors[best] <= TOLERANCE * scale else 0


def refine(points, sign, steps=STEPS):
    """`[(x, value), …]` drawn through the stations of one member, curved between them where `sign` allows it.

    `points` is `[(x, value, slope), …]` in the table's own order, and the order is kept: two stations at one
    abscissa are the jump a point load writes and are passed straight through.
    """
    if not points:
        return []
    out = [(points[0][0], points[0][1])]
    for (x0, p0, m0), (x1, p1, m1) in zip(points, points[1:]):
        span = x1 - x0
        if sign and span > SAME_X and m0 is not None and m1 is not None:
            for step in range(1, steps):
                t = step / float(steps)
                out.append((x0 + t * span, hermite(t, p0, p1, sign * m0, sign * m1, span)))
        out.append((x1, p1))
    return out


def refined(curves, key, steps=STEPS):
    """Every member's drawn diagram of `key`, curved between the exported stations where it can be verified.

    `curves` is `{member: [(x, value, slope), …]}` and the answer is `{member: [(x, value), …]}` -- the shape
    `diagram_svg` draws. A quantity with no slope in the table (`N`, `V_y`, `V_z`, `M_T`) keeps its stations:
    a shear under a uniform load is already a straight line between them.
    """
    if key not in SLOPE_OF:
        return {member: [(x, value) for x, value, _slope in points] for member, points in curves.items()}
    sign = slope_sign(curves)
    return {member: refine(points, sign, steps) for member, points in curves.items()}
