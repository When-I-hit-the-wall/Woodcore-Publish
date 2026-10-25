"""Buckling and lateral torsional buckling of a member check, SIA 265 4.2.8 and 4.2.9 -- `member_check.compute`'s arithmetic for the two kinds of stability, moved out of calc/domains/member_check.py unchanged when the material of the library made it longer than the ceiling (issue #112; tests/test_module_size.py). Its numbers are held, with every other kind's, by tests/test_member_check.py and the 13 checks of the example project (tests/test_member_check_material.py). No Qt here.
"""

import math

from domains.timber_calc import line as _row
from norms import sia265
from number_text import exact as _fmt

def _slenderness_rows(record, axis, lever, sigma_c, f_c, beta_c, f_c_0_k, e_0_05, bend=None):
    """Buckling about one axis, 4.2.8 -- timber-kc's arithmetic: l_k = beta · l, lambda = l_k / i, lambda_rel = lambda/pi · sqrt(f_c,0,k / E_0,05) (34), and k_c = 1 up to lambda_rel,limit (Figur 10), else (30) with k of (31). `lever` is i about the axis; `bend` the bending term (37) adds, (formula, value) or None. Gives (rows, eta about the axis)."""
    clause = sia265.buckling()
    l_k = record["beta_" + axis] * record["l_" + axis]
    lam = l_k / lever
    lam_rel = lam / math.pi * math.sqrt(f_c_0_k / e_0_05)
    rows = [_row("l_k_" + axis, "l_(k,%s)" % axis, l_k, "mm", "beta_%s dot l_%s" % (axis, axis)),
            _row("lambda_" + axis, "lambda_" + axis, lam, "", "l_(k,%s) / i_%s" % (axis, axis)),
            _row("lambda_rel_" + axis, "lambda_(rel,%s)" % axis, lam_rel, "", "lambda_%s / pi dot sqrt(f_(c,0,k) / E_(0,05))" % axis)]
    if lam_rel <= clause["lambda_rel_limit"]:
        k_c = 1.0
        rows.append(_row("k_c_" + axis, "k_(c,%s)" % axis, k_c, "", label="λ_rel ⩽ %s" % _fmt(clause["lambda_rel_limit"])))
    else:
        k = clause["k_factor"] * (1 + beta_c * (lam_rel - clause["lambda_rel_offset"]) + lam_rel ** 2)
        k_c = 1 / (k + math.sqrt(k ** 2 - lam_rel ** 2))
        rows += [_row("k_" + axis, "k_" + axis, k, "", "%s dot (1 + beta_c dot (lambda_(rel,%s) - %s) + lambda_(rel,%s)^2)" % (_fmt(clause["k_factor"]), axis, _fmt(clause["lambda_rel_offset"]), axis)),
                 _row("k_c_" + axis, "k_(c,%s)" % axis, k_c, "", "1 / (k_%s + sqrt(k_%s^2 - lambda_(rel,%s)^2))" % (axis, axis, axis))]
    eta = sigma_c / (k_c * f_c) + (bend[1] if bend else 0)
    formula = "sigma_(c,0,d) / (k_(c,%s) dot f_(c,0,d))" % axis + (" + " + bend[0] if bend else "")
    rows.append(_row("eta_" + axis, "eta_(c,%s)" % axis, eta, "", formula))
    return rows, eta


def _stiffness(record):
    """What the relative slendernesses read of the member, as `#member` stores it: f_c,0,k and E_0,05 of Anhang B (Tabellen 47, 48), E_0,05 times eta_w for the stiffness (Tabelle 4) -- the factor the Stützen workbook computes and leaves out (issue #38) -- and the radii of gyration i_y, i_z (d/4 both for a round section). Gives (rows, f_c_0_k, E_0_05, i_y, i_z)."""
    characteristic = sia265.characteristic(record["grade"])
    eta_w_e = sia265.eta_w(record["moisture_class"], "stiffness")
    e_0_05 = eta_w_e * characteristic["E_0_05"]
    section = record["section"]
    if section["type"] == "cir":
        i_y = i_z = section["d"] / 4
        radius_rows = [_row("i_y", "i_y", i_y, "mm", "d / 4")]
    else:
        i_y, i_z = section["h"] / math.sqrt(12), section["b"] / math.sqrt(12)
        radius_rows = [_row("i_y", "i_y", i_y, "mm", "sqrt(I_y / A)"), _row("i_z", "i_z", i_z, "mm", "sqrt(I_z / A)")]
    rows = radius_rows + [_row("eta_w_E", "eta_(w,E)", eta_w_e, "", label="Feuchteklasse %d" % record["moisture_class"]),
                          _row("f_c_0_k", "f_(c,0,k)", characteristic["f_c_0_k"], "N/mm²"),
                          _row("E_0_05", "E_(0,05)", e_0_05, "N/mm²", "eta_(w,E) dot %s" % _fmt(characteristic["E_0_05"]))]
    return rows, characteristic["f_c_0_k"], e_0_05, i_y, i_z


def _compute_buckling(record, row, area, area_row, factors, design):
    """`compute` for a buckling, SIA 265 4.2.8 -- verify-compression's with `stability: true`: the section, sigma_c,0,d <= f_c,0,d (10), then about each axis (29) with k_c of (30), (31) and lambda_rel of (34); eta the largest of the three."""
    from domains.member_check import _TO_KN, _family, _result
    force = record["N"]["value"] * _TO_KN[record["N"]["unit"]]
    sigma = force * 1000 / area
    f_c, f_row = design("f_c_0_d", "f_(c,0,d)", row["f_c_0_d"])
    stiffness_rows, f_c_0_k, e_0_05, i_y, i_z = _stiffness(record)
    beta_c = sia265.buckling()["beta_c"][_family(record["grade"])]
    eta_s = sigma / f_c
    rows = [area_row] + stiffness_rows + [_row("N_c_d", "N_(c,d)", force, "kN")] + factors + [
        f_row, _row("sigma_c_0_d", "sigma_(c,0,d)", sigma, "N/mm²", "N_(c,d) / A"),
        _row("eta_s", "eta_s", eta_s, "", "sigma_(c,0,d) / f_(c,0,d)"), _row("beta_c", "beta_c", beta_c, "")]
    etas = [eta_s]
    for axis, lever in (("y", i_y), ("z", i_z)):
        axis_rows, eta_axis = _slenderness_rows(record, axis, lever, sigma, f_c, beta_c, f_c_0_k, e_0_05)
        rows += axis_rows
        etas.append(eta_axis)
    eta = max(etas)
    governing = ("sigma_c_0_d <= f_c_0_d", "sigma_c_0_d <= k_c_y dot f_c_0_d", "sigma_c_0_d <= k_c_z dot f_c_0_d")[etas.index(eta)]
    rows.append(_row("eta", "eta", eta, "", "max(eta_s, eta_(c,y), eta_(c,z))"))
    return _result("buckling", "(10), (29)", "4.2.8", rows, eta, governing)


def _compute_lateral(record, row, area, area_row, factors, design, strengths):
    """`compute` for a lateral torsional buckling, SIA 265 4.2.9 -- verify-bending's or verify-bending-normal's with `stability: true`, along the grain: the section by (14), (21) or (22); sigma_m,crit of (41) from a, or as given, lambda_rel,m (40) and k_m (39); then without a normal force or with a tension (38), sigma_m,y,d <= k_m · f_m,y,d, and with a compression (37) about each axis, k_c of 4.2.8 beside k_m. eta the largest."""
    from domains.member_check import _TO_KN, _bending_values, _family, _result, strong_axis
    values = _bending_values(record, row, strengths)
    moments, f_m = values["moments"], values["f_m"]
    normal = record["N"]["value"] * _TO_KN[record["N"]["unit"]]       # kN, tension positive
    section = record["section"]
    rows = ([area_row] if normal else []) + values["modulus_rows"] + values["moment_rows"]
    terms, shown_terms = [], []
    if normal > 0:
        f_n, f_n_row = design("f_t_0_d", "f_(t,0,d)", row["f_t_0_d"])
        sigma_n = normal * 1000 / area
        rows.append(_row("N_t_d", "N_(t,d)", normal, "kN"))
        n_rows = [f_n_row, _row("sigma_t_0_d", "sigma_(t,0,d)", sigma_n, "N/mm²", "N_(t,d) / A")]
        terms.append(sigma_n / f_n)
        shown_terms.append("sigma_(t,0,d) / f_(t,0,d)")
    elif normal < 0:
        f_n, f_n_row = design("f_c_0_d", "f_(c,0,d)", row["f_c_0_d"])
        sigma_n = -normal * 1000 / area
        rows.append(_row("N_c_d", "N_(c,d)", -normal, "kN"))
        n_rows = [f_n_row, _row("sigma_c_0_d", "sigma_(c,0,d)", sigma_n, "N/mm²", "N_(c,d) / A")]
        terms.append((sigma_n / f_n) ** 2)
        shown_terms.append("(sigma_(c,0,d) / f_(c,0,d))^2")
    else:
        n_rows = []
    rows += factors + values["k_rows"]
    sigma_m = {}
    stress_rows = []
    for axis, key in (("y", "M_y"), ("z", "M_z")):
        if moments[key]:
            rows.append(values["f_m_rows"][axis])
            sigma_m[axis] = moments[key] * 1e6 / (values["w_y"] if axis == "y" else values["w_z"])
            stress_rows.append(_row("sigma_m_%s_d" % axis, "sigma_(m,%s,d)" % axis, sigma_m[axis], "N/mm²", "M_(%s,d) / W_%s" % (axis, axis)))
            terms.append(sigma_m[axis] / f_m[axis])
            shown_terms.append("sigma_(m,%s,d) / f_(m,%s,d)" % (axis, axis))
    rows += n_rows + stress_rows
    eta_s = sum(terms)
    rows.append(_row("eta_s", "eta_s", eta_s, "", " + ".join(shown_terms)))
    # 4.2.9: sigma_m,crit, lambda_rel,m, k_m -- E_0,05 times eta_w for the stiffness, as #member stores it
    stiffness_rows, f_c_0_k, e_0_05, i_y, i_z = _stiffness(record)
    lateral = sia265.lateral_buckling()
    rows += stiffness_rows
    # the axis that tips (timber-tips' twin, D-09): y, z where the section is wider than high, none for a round section or where only the weak axis is bent (D-10, D-17) -- k_m = 1 then, and (38) has nothing to add
    axis = strong_axis(section)
    tips = axis is not None and axis in sigma_m
    if not tips:
        k_m = 1.0
        if normal < 0:
            # (37) reads it, as verify-bending-normal stores it; (38) has nothing to divide and prints none
            rows.append(_row("k_m", "k_m", k_m, "", label="Kreisquerschnitt" if axis is None else "Biegung nur um die schwache Achse"))
    else:
        if record.get("sigma_m_crit") is not None:
            crit = record["sigma_m_crit"]
            rows.append(_row("sigma_m_crit", "sigma_(m,crit)", crit, "N/mm²", label="vorgegeben"))
        else:
            # (41) for a b × h rectangle bent about its strong axis: the side along the moment's axis squared over the other -- b²/h about y, h²/b about z
            narrow, deep, shown = (section["b"], section["h"], "b^2 / (a dot h)") if axis == "y" else (section["h"], section["b"], "h^2 / (a dot b)")
            crit = lateral["sigma_m_crit_factor"] * e_0_05 * narrow ** 2 / (record["a"] * deep)
            rows += [_row("a", "a", record["a"], "mm"),
                     _row("sigma_m_crit", "sigma_(m,crit)", crit, "N/mm²", "%s dot E_(0,05) dot %s" % (_fmt(lateral["sigma_m_crit_factor"]), shown))]
        f_m_k = row["f_m_k"]
        lam_m = math.sqrt(f_m_k / crit)
        km = lateral["k_m"]
        if lam_m <= km["lower_bound"]:
            k_m, k_m_formula = 1.0, None
        elif lam_m <= km["upper_bound"]:
            k_m, k_m_formula = km["intercept"] - km["slope"] * lam_m, "%s - %s dot lambda_(rel,m)" % (_fmt(km["intercept"]), _fmt(km["slope"]))
        else:
            k_m, k_m_formula = 1 / lam_m ** 2, "1 / lambda_(rel,m)^2"
        rows += [_row("f_m_k", "f_(m,k)", f_m_k, "N/mm²"), _row("lambda_rel_m", "lambda_(rel,m)", lam_m, "", "sqrt(f_(m,k) / sigma_(m,crit))"),
                 _row("k_m", "k_m", k_m, "", k_m_formula)]
    if normal >= 0:
        if not tips:
            rows.append(_row("eta", "eta", eta_s, "", "eta_s"))
            return _result("lateral-torsional", "(38)", "4.2.9", rows, eta_s, "eta_s <= 1")
        # (38): the bending about the strong axis against k_m · f_m,d about it
        eta_m = sigma_m[axis] / (k_m * f_m[axis])
        rows.append(_row("eta_m", "eta_m", eta_m, "", "sigma_(m,%s,d) / (k_m dot f_(m,%s,d))" % (axis, axis)))
        eta = max(eta_s, eta_m)
        relation = "sigma_m_%s_d <= k_m dot f_m_%s_d" % (axis, axis) if eta_m >= eta_s else "eta_s <= 1"
        rows.append(_row("eta", "eta", eta, "", "max(eta_s, eta_m)"))
        return _result("lateral-torsional", "(38)", "4.2.9", rows, eta, relation)
    # (37) about each axis, with a compression: k_c beside k_m on y, the bending about z on z
    f_c = f_n
    beta_c = sia265.buckling()["beta_c"][_family(record["grade"])]
    rows.append(_row("beta_c", "beta_c", beta_c, ""))
    etas = [eta_s]
    strong = axis
    for axis, lever in (("y", i_y), ("z", i_z)):
        bend = None
        if axis in sigma_m:
            # k_m on the strong axis's bending (D-09), whose own k_m is 1 where nothing tips
            bend = ("sigma_(m,%s,d) / (k_m dot f_(m,%s,d))" % (axis, axis), sigma_m[axis] / (k_m * f_m[axis])) if axis == (strong or "y") else ("sigma_(m,%s,d) / f_(m,%s,d)" % (axis, axis), sigma_m[axis] / f_m[axis])
        axis_rows, eta_axis = _slenderness_rows(record, axis, lever, sigma_n, f_c, beta_c, f_c_0_k, e_0_05, bend)
        rows += axis_rows
        etas.append(eta_axis)
    eta = max(etas)
    rows.append(_row("eta", "eta", eta, "", "max(eta_s, eta_(c,y), eta_(c,z))"))
    return _result("lateral-torsional", "(22), (37)", "4.2.8.5", rows, eta, ("eta_s <= 1", "eta_y <= 1", "eta_z <= 1")[etas.index(eta)])
