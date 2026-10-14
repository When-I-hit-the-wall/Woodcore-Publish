"""The shape of a moment diagram between two exported stations (`calc/rfem_import/diagram_curve.py`).

The engineer, on the figures of the RFEM tab: «pour l'affichage des efforts internes dans les schémas, tu fais
simplement une interpolation linéaire entre le max et le min, mais cela est faux. Les efforts peuvent également
être courbes.» He is right in effect: the line was drawn through the stations RFEM exported, and RFEM exports
**two to four per member** — his own 4.23 m beam comes out of CO1 as x = 0, 2.115, 2.115, 4.23, so a uniformly
loaded beam was drawn as a triangle.

⚠️ **The oracle here is arithmetic and not a fixture.** Under a uniform load q the moment is
`M(x) = M0 + V0·x − q·x²/2` exactly, and the export gives M0, V0 and q (as the slope of V). So each test states
the parabola in closed form and asserts the reconstruction lands on it — which is a stronger check than any
recorded curve, because it fails if the interpolation is right only at the points it was fitted to.

👉 Measured on the engineer's own export before any of this was written: integrating V_z over member 2 of CO1
from 0 to 2.115 m gives **−8.527614**, and RFEM exports **−8.527615**.
"""

import math

from rfem_import import diagram_curve


def _uniform(length, m0, v0, q, at):
    """The moment of a member under a uniform load, in closed form -- the oracle every test here compares with."""
    return [(x, m0 + v0 * x - q * x * x / 2.0) for x in at]


def _stations(length, m0, v0, q, xs):
    """What RFEM would export at `xs`: the moment, and the shear that is its slope."""
    return [(x, m0 + v0 * x - q * x * x / 2.0, v0 - q * x) for x in xs]


def test_a_uniformly_loaded_beam_is_reconstructed_to_the_digit():
    """The case the engineer met: three stations, and the parabola between them.

    His beam, near enough: 4.23 m, q = 3.375 kN/m, and the export's own numbers at the ends and the middle.
    """
    length, q = 4.23, 3.375
    v0 = q * length / 2.0
    points = _stations(length, 0.0, v0, q, [0.0, length / 2.0, length])
    sign = diagram_curve.slope_sign({1: points})
    assert sign == 1, "the shear is the slope of the moment, and the export says so with sign +1"
    drawn = diagram_curve.refine(points, sign, steps=8)
    for x, value in drawn:
        assert abs(value - (v0 * x - q * x * x / 2.0)) < 1e-9, (
            f"at x = {x:.3f} the reconstruction gives {value:.6f} where the parabola is "
            f"{v0 * x - q * x * x / 2.0:.6f}"
        )


def test_the_chord_is_what_it_replaces():
    """What the figure drew before, and how far from the diagram it was -- so the gain is stated, not assumed."""
    length, q = 4.23, 3.375
    v0 = q * length / 2.0
    points = _stations(length, 0.0, v0, q, [0.0, length / 2.0, length])
    quarter = length / 4.0
    chord = (0.0 + (v0 * (length / 2.0) - q * (length / 2.0) ** 2 / 2.0)) / 2.0   # halfway along the first half
    true = v0 * quarter - q * quarter * quarter / 2.0
    drawn = dict(diagram_curve.refine(points, 1, steps=4))
    assert abs(drawn[quarter] - true) < 1e-9
    assert abs(chord - true) > 1.0, "the chord is more than 1 kNm from the diagram at the quarter point"


def test_a_linearly_varying_load_is_exact_too():
    """M is then a cubic, and a cubic is what value and slope at two points determine -- so it is exact, not near.

    `M(x) = −k·x³/6` with `V(x) = −k·x²/2`: a triangular load rising from nothing.
    """
    k = 2.0
    xs = [0.0, 1.5, 3.0]
    points = [(x, -k * x ** 3 / 6.0, -k * x * x / 2.0) for x in xs]
    drawn = diagram_curve.refine(points, 1, steps=6)
    for x, value in drawn:
        assert abs(value - (-k * x ** 3 / 6.0)) < 1e-9


def test_a_jump_at_one_abscissa_stays_a_jump():
    """RFEM writes two rows at one x where a point load sits, and the diagram is discontinuous there.

    Nothing may be interpolated across that pair: a curve drawn through it would draw a diagram that is
    continuous where the structure's is not (`diagram_svg`'s own rule, held here for the refinement too).
    """
    points = [(0.0, 0.0, 5.0), (2.0, 10.0, 5.0), (2.0, 10.0, -5.0), (4.0, 0.0, -5.0)]
    drawn = diagram_curve.refine(points, 1, steps=4)
    at_two = [value for x, value in drawn if abs(x - 2.0) < 1e-12]
    assert at_two == [10.0, 10.0], "both rows at x = 2 are kept, and nothing is drawn between them"
    assert drawn == sorted(drawn, key=lambda p: p[0]), "the table's own order is kept"


def test_the_sign_of_the_relation_is_measured_and_not_assumed():
    """Which shear is the slope of which moment, and with which sign, is the program's convention.

    So both are tried against what RFEM exported and the one that reproduces it wins -- a wrong sign doubles
    the error, so the two are never close.
    """
    length, q = 4.0, 2.0
    v0 = q * length / 2.0
    points = _stations(length, 0.0, v0, q, [0.0, length / 2.0, length])
    assert diagram_curve.slope_sign({1: points}) == 1
    flipped = [(x, value, -slope) for x, value, slope in points]
    assert diagram_curve.slope_sign({1: flipped}) == -1


def test_a_table_neither_sign_explains_is_left_alone():
    """The refusal that keeps this module honest: a diagram it cannot verify is one it does not touch.

    An export whose shear is not the slope of its moment -- another convention, another quantity, a table this
    reader has not met -- draws the polyline it drew before, and no curve anybody would have to vouch for.
    """
    points = [(0.0, 0.0, 1.0), (1.0, 10.0, 1.0), (2.0, -4.0, 1.0)]
    assert diagram_curve.slope_sign({1: points}) == 0
    drawn = diagram_curve.refine(points, 0)
    assert drawn == [(0.0, 0.0), (1.0, 10.0), (2.0, -4.0)], "the stations, and nothing between them"


def test_only_the_moments_are_reconstructed():
    """N, V and M_T keep their stations: a shear under a uniform load is already a straight line between them,
    and a torsional moment is tied to nothing else the table carries."""
    assert set(diagram_curve.SLOPE_OF) == {"M_y", "M_z"}
    curves = {1: [(0.0, 3.0, None), (2.0, 1.0, None)]}
    assert diagram_curve.refined(curves, "N") == {1: [(0.0, 3.0), (2.0, 1.0)]}
    assert diagram_curve.refined(curves, "V_z") == {1: [(0.0, 3.0), (2.0, 1.0)]}


def test_a_flat_diagram_needs_no_sign():
    """A plane frame carries no M_z and no V_y at all, so both signs explain it equally -- and nothing is drawn
    differently either way. The answer is «do not reconstruct», which is the honest one."""
    curves = {1: [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0)]}
    assert diagram_curve.slope_sign(curves) == 0


def test_the_ends_are_always_rfem_s_own_numbers():
    """Whatever is drawn between two stations, the stations themselves are untouched -- which is what makes the
    reconstruction a reading of the export rather than a second opinion about it."""
    points = _stations(3.0, -1.0, 4.0, 2.0, [0.0, 1.0, 3.0])
    drawn = diagram_curve.refine(points, 1, steps=5)
    for x, value, _slope in points:
        assert any(abs(x - dx) < 1e-12 and abs(value - dv) < 1e-12 for dx, dv in drawn), (
            f"the station at x = {x} is missing from the drawn line"
        )
