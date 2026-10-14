"""The polar moment and the distribution of N, V and M over a fastener group.

This is the one calculation in the project with a published answer to check against: the HB2 method sheet's worked example (`ExternalFiles/104-MomentPolaire/Fiche_methode_assemblage_effort_tranchant_1.pdf`, docs/domain/connections.md §3.3quinquies). A 3 x 5 dowel group, N = 7.5 kN, V = 25 kN, M = 6.6 kNm, and the sheet gives 7 210 N at 39.7° to the Nebenträger.

Everything else here is an invariant rather than a reference value: the forces must be statically equivalent to the actions they were distributed from, whatever the geometry. That is the check a wrong sign would fail and a wrong magnitude would not, and it needs no published answer.
"""

import math

import conftest
from domains import connection

# The HB2 sheet's group: three columns at x = -70, 0, +70, five rows at z = 0, ±60, ±120.
HB2_POINTS = [(x, z) for x in (-70, 0, 70) for z in (-120, -60, 0, 60, 120)]
HB2 = {"N": 7.5, "V": 25.0, "M": 6.6}


def _geometry(points, center=None):
    centre = center or connection.centroid(points)
    ipx, ipz = connection.polar_moments(points, centre)
    return {"n": len(points), "I_p": ipx + ipz, "center": centre, "points": points}


def test_polar_moment_of_the_hb2_group():
    """I_p,x = 49 000, I_p,z = 108 000, I_p = 157 000 mm²."""
    ipx, ipz = connection.polar_moments(HB2_POINTS, connection.centroid(HB2_POINTS))
    assert abs(ipx - 49_000) < 1e-6, f"I_p,x = {ipx}, the sheet gives 49 000 mm²"
    assert abs(ipz - 108_000) < 1e-6, f"I_p,z = {ipz}, the sheet gives 108 000 mm²"
    assert abs(ipx + ipz - 157_000) < 1e-6


def test_the_hb2_corner_dowel_carries_the_sheets_force():
    """F = 7.21 kN, at 39.7° to the Nebenträger (the reference member, whose grain is x)."""
    g = _geometry(HB2_POINTS)
    rows, governing = connection.fastener_forces(g, {"N": 0.0, "V": 90.0}, HB2["N"], HB2["V"], HB2["M"])
    top = rows[governing[0]]
    assert abs(abs(top["fx"]) - 5.545) < 5e-4, f"F_x = {top['fx']:.4f}, the sheet gives 5.545 kN"
    assert abs(abs(top["fz"]) - 4.609) < 5e-4, f"F_z = {top['fz']:.4f}, the sheet gives 4.609 kN"
    assert abs(top["f"] - 7.21) < 5e-3, f"F = {top['f']:.4f}, the sheet gives 7.21 kN"
    beta = connection.grain_angle(connection.force_line(top["fx"], top["fz"]), 0.0)
    assert abs(beta - 39.7) < 0.05, f"β = {beta:.2f}°, the sheet gives 39.7°"


def test_the_forces_are_statically_equivalent_to_the_actions():
    """ΣF = N + V and ΣM about the rotation centre = M, on an irregular group with forces at arbitrary angles.

    The invariant a sign error breaks and a plausible-looking wrong number does not. M is positive anticlockwise on the figure, turning z towards x, so its moment sums as Δz·F_x − Δx·F_z (docs/domain/connections.md §3.3quinquies).

    Held about the **centroid**, which is where the elastic method assumes the group turns: there ΣΔx = ΣΔz = 0, so the moment terms cancel across the group and what is left is exactly N + V. About a centre the engineer fixes elsewhere they do not cancel -- see the test below, which is not a defect but is worth knowing.
    """
    points = [(0, 0), (55, -12), (-30, 44), (120, 90), (-75, -60)]
    g = _geometry(points)
    directions = {"N": 23.0, "V": 131.0}
    n_total, v_total, m_total = 14.0, -9.5, 4.25
    rows, _ = connection.fastener_forces(g, directions, n_total, v_total, m_total)

    nx = n_total * math.cos(math.radians(directions["N"]))
    nz = n_total * math.sin(math.radians(directions["N"]))
    vx = v_total * math.cos(math.radians(directions["V"]))
    vz = v_total * math.sin(math.radians(directions["V"]))

    assert abs(sum(r["fx"] for r in rows) - (nx + vx)) < 1e-9, "ΣF_x is not N_x + V_x"
    assert abs(sum(r["fz"] for r in rows) - (nz + vz)) < 1e-9, "ΣF_z is not N_z + V_z"
    moment = sum(r["dz"] * r["fx"] - r["dx"] * r["fz"] for r in rows) / 1000.0
    assert abs(moment - m_total) < 1e-9, f"Σ moments = {moment:.9f} kNm, M = {m_total} kNm"


def test_a_fixed_rotation_centre_does_not_balance_the_applied_forces():
    """A rotation centre fixed away from the centroid leaves the fastener forces out of balance with N and V, by M/I_p · ΣΔ.

    Not a defect: it is what the elastic method *is*. Sharing N and V equally and adding M in proportion to the distance assumes the group turns about its centroid; fixing the centre elsewhere states a different assumption, which the engineer makes deliberately (docs/domain/connections.md §3.3quinquies, `center.mode = "manual"`).

    It is here because it is a trap worth having written down: the sum of the printed forces will not come to the applied load, and a checker who adds them up needs to know that is expected rather than an arithmetic error. Nor is the moment about the fixed centre simply M -- the equally shared N and V act through an offset and add a moment of their own.
    """
    points = [(0, 0), (55, -12), (-30, 44), (120, 90), (-75, -60)]
    g = _geometry(points, center=(20.0, 5.0))
    rows, _ = connection.fastener_forces(g, {"N": 23.0, "V": 131.0}, 14.0, -9.5, 4.25)

    nx = 14.0 * math.cos(math.radians(23.0)) + (-9.5) * math.cos(math.radians(131.0))
    drift = sum(r["fx"] for r in rows) - nx
    expected = 4.25 * 1000.0 * sum(r["dz"] for r in rows) / g["I_p"]
    assert abs(drift - expected) < 1e-9, (
        f"the imbalance is {drift:.6f} kN, M/I_p · ΣΔz gives {expected:.6f} -- the "
        f"distribution is no longer the elastic one"
    )
    assert abs(drift) > 1e-3, "this group was chosen so that the imbalance is visible"

    # The moment about the fixed centre, written out in full: M, plus what the equally shared N and V contribute through the offset of the centre from the centroid. Σ(Δz·F_x − Δx·F_z) = M + (N_x+V_x)/n·ΣΔz − (N_z+V_z)/n·ΣΔx.
    nz = 14.0 * math.sin(math.radians(23.0)) + (-9.5) * math.sin(math.radians(131.0))
    n = g["n"]
    want = 4.25 + (nx / n * sum(r["dz"] for r in rows) - nz / n * sum(r["dx"] for r in rows)) / 1000.0
    moment = sum(r["dz"] * r["fx"] - r["dx"] * r["fz"] for r in rows) / 1000.0
    assert abs(moment - want) < 1e-9, (
        f"Σ moments about the fixed centre = {moment:.9f} kNm, the distribution gives {want:.9f}"
    )
    assert abs(moment - 4.25) > 1e-3, (
        "this group was chosen so that the moment about the fixed centre is visibly not M"
    )


def test_a_moment_puts_a_force_at_right_angles_to_the_lever_arm():
    """M·r_i/I_p, perpendicular to Δ -- bauforumstahl's V_b,i, which v0.50's green arrow draws."""
    points = [(-60, -40), (60, -40), (-60, 40), (60, 40)]
    g = _geometry(points)
    rows, _ = connection.fastener_forces(g, {"N": 0.0, "V": 90.0}, 0.0, 0.0, 5.0)
    for r in rows:
        size = math.hypot(r["fx"], r["fz"])
        want = 5.0 * 1000.0 * math.hypot(r["dx"], r["dz"]) / g["I_p"]
        assert abs(size - want) < 1e-9, f"fastener {r['nr']}: |F| = {size}, M·r/I_p = {want}"
        # perpendicular: the dot product of the force and the lever arm is zero
        assert abs(r["dx"] * r["fx"] + r["dz"] * r["fz"]) < 1e-9, (
            f"fastener {r['nr']}: the force from the moment is not at right angles to its lever arm"
        )


def test_a_symmetric_group_shares_n_and_v_equally():
    points = [(-50, -50), (50, -50), (-50, 50), (50, 50)]
    g = _geometry(points)
    rows, governing = connection.fastener_forces(g, {"N": 0.0, "V": 90.0}, 8.0, 4.0, 0.0)
    assert len(governing) == 4, "without a moment every fastener of a symmetric group carries the same force"
    for r in rows:
        assert abs(r["fx"] - 2.0) < 1e-12 and abs(r["fz"] - 1.0) < 1e-12


def test_a_moment_without_a_lever_arm_is_refused():
    """One fastener, or all of them at the rotation centre: nothing to take a moment on."""
    g = _geometry([(0, 0)])
    try:
        connection.fastener_forces(g, {"N": 0.0, "V": 90.0}, 5.0, 5.0, 1.0)
    except ValueError as exc:
        assert "lever arm" in str(exc), exc
    else:
        assert False, "a moment on a group with I_p = 0 was accepted"


def test_ties_at_the_largest_force_are_all_named():
    """Several fasteners carrying the same largest force are all reported, so the report can name them as a range."""
    points = [(-60, -60), (60, -60), (-60, 60), (60, 60)]
    g = _geometry(points)
    _, governing = connection.fastener_forces(g, {"N": 0.0, "V": 90.0}, 0.0, 0.0, 10.0)
    assert len(governing) == 4, f"a square group under a pure moment ties everywhere, got {governing}"
    assert connection.number_ranges([i + 1 for i in governing]) == "1–4"


def test_the_exported_connections_still_hold_their_own_numbers():
    """Every connection in data/: the n and I_p it carries are the ones its own fasteners give.

    Guards the record against the geometry drifting from the vars printed beside it -- validation checks the count, this checks the arithmetic.
    """
    data = conftest.exported("connections.json")["connections"]
    if not data:
        raise conftest.Skip("no connection exported yet")
    for cid, record in data.items():
        points = [(f["x"], f["z"]) for f in record["fasteners"]]
        centre = (record["vars"]["x_c"]["value"], record["vars"]["z_c"]["value"])
        ipx, ipz = connection.polar_moments(points, centre)
        assert abs(ipx + ipz - record["vars"]["I_p"]["value"]) < 1e-6, (
            f"{cid}: I_p in the record is {record['vars']['I_p']['value']}, its own "
            f"fasteners give {ipx + ipz}"
        )
        assert record["vars"]["n"]["value"] == len(points), cid
