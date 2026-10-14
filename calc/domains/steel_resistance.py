"""The resistance of a steel section after SIA 263:2013 5.1 and 5.2 -- tension, compression, bending, shear and their interactions -- and its class after Tabelle 5 (issue #51, spec 2026-10-12-section-acier REQ-005, REQ-006; docs/domain/steel.md).

Each check is a function of a resolved record (domains/steel_check.py `resolve`) and returns the rows of its page (domains/steel_calc.py) with its verdict: `{"calc", "eta", "relation", "ratio", "class", "classification", "notes"}`, or `{"reason"}` where the norm offers this program no way through -- class 4 (EER, 4.5.3, not built), a shear beyond half the resistance of a section 5.1.5 gives no reduction for. The arithmetic is in N and mm. Forces are signed, tension positive (the timber checks' rule); Tabelle 5 reads compression positive, which `classify` is given.

| kind | equations |
|---|---|
| class | Tabelle 5a, 5b under the design forces (domains/steel_section.py `classify`) |
| tension | (38) the gross section, (39) the net section where A_net is given |
| compression | (38), class 1 to 3 -- the section alone; buckling is «Flambement» (lot 2) |
| bending | (40) or (52) about each axis; with N or about both axes (44), or (45) to (48) for a doubly symmetric I and a rolled RHS of class 1 or 2, (54) in class 3 |
| shear | (41), A_v (41a) or SZS C5's for an I, A_w in class 3 (5.2.4); (42) for an I or a U; with M_y, (43) or (53) beyond 0.5 V_Rd |

Every value of the norm -- f_y, f_u, tau_y (Tabelle 1, by the profile's thickest plate), E (3.2.2.3), gamma_M1, gamma_M2 (4.1.3), Tabelle 5 -- is read through calc/norms/sia263.py; the numbers written here are the equations' own (0,9 of (39), 0,5 of 5.1.5.1, the coefficients of (45) to (48)).
"""

import math

from domains import steel_section
from domains.steel_calc import Calc
from norms import sia263

# The kinds of lot 1 (spec D-08); lot 2 adds buckling, lateral-torsional and interaction, lot 3 the connections.
KINDS = ("class", "tension", "compression", "bending", "shear")


def _material(c, rec):
    """f_y, f_u, tau_y of the grade at the profile's thickest plate, E, gamma_M1 -- given to the page with their tables."""
    steel = sia263.steel(rec["grade"], rec["section"]["t_max"])
    band = "t ≤ 40 mm" if sia263.band_for(rec["section"]["t_max"]) == "thin" else "40 mm < t ≤ 100 mm"
    where = "%s, %s" % (rec["grade"], band)
    c.given("f_y", steel["f_y"], "N/mm²", "f_y", "Streckgrenze", level=2, norm="SIA 263", norm_ref="Tabelle 1",
            source="norm:SIA 263:2013, Tabelle 1", group="material", description=where)
    gm1 = sia263.gamma_M1()
    c.given("gamma_M1", gm1["value"], "", "gamma_(M 1)", "Widerstandsbeiwert", level=3, norm="SIA 263", norm_ref=gm1["norm_ref"],
            source="norm:SIA 263:2013, 4.1.3", group="material")
    return steel


def _section_values(c, rec, keys):
    sec = rec["section"]
    names = {"A": ("A", "Querschnittsfläche", "mm²"), "A_net": ("A_(n e t)", "Nettoquerschnittsfläche", "mm²"),
             "W_pl_y": ("W_(p l,y)", "plastisches Widerstandsmoment", "mm³"), "W_pl_z": ("W_(p l,z)", "plastisches Widerstandsmoment", "mm³"),
             "W_el_y": ("W_(e l,y)", "elastisches Widerstandsmoment", "mm³"), "W_el_z": ("W_(e l,z)", "elastisches Widerstandsmoment", "mm³"),
             "A_v_z": ("A_v", "wirksame Schubfläche", "mm²"), "A_v_y": ("A_(v,y)", "wirksame Schubfläche", "mm²"),
             "A_w": ("A_w", "Stegfläche", "mm²")}
    for key in keys:
        symbol, label, unit = names[key]
        value = rec.get("A_net") if key == "A_net" else sec.get(key)
        source = rec["section_source"] if key != "A_net" else c.source
        c.given(key, value, unit, symbol, label, level=2, norm=sec["norm_ref"].split(",")[0] if sec["source"] == "c5" else "",
                norm_ref=sec["norm_ref"].split(", ", 1)[1] if sec["source"] == "c5" else "", source=source, group="section",
                description=sec["designation"])


def _classify(c, rec, N, M_y, M_z):
    """The class under the design forces (compression positive for Tabelle 5), given to the page as a var with its governing wall."""
    sec = rec["section"]
    cls = steel_section.classify(sec, sia263.steel(rec["grade"], sec["t_max"])["f_y"], N=-N, M_y=M_y, M_z=M_z)
    gov = cls["governing"]
    description = None
    if gov:
        description = "%s: c/t = %.1f (Klasse 1: %.1f, 2: %.1f, 3: %.1f)" % (gov["name"], gov["ratio"], *gov["limits"])
    c.given("QK", cls["class"], "", "\"QK\"", "Querschnittsklasse", level=1, norm="SIA 263", norm_ref=cls["norm_ref"],
            source="python:domains/steel_section.py", group="section", description=description)
    return cls


def _not_class_4(cls):
    if cls["class"] == 4:
        gov = cls["governing"]
        return ("the section is class 4 (%s: c/t %.1f above %.1f, Tabelle 5) -- the method EER of 4.5.3, a reduced section, is not built: "
                "choose a stockier profile or a lower grade" % (gov["name"], gov["ratio"], gov["limits"][2]))
    return None


def check(rec):
    """The check of a resolved, calculable record -- see the module's table."""
    kind = rec["kind"]
    c = Calc("woodcore:steel/%s.json" % rec["id"])
    return {"class": _check_class, "tension": _tension, "compression": _compression, "bending": _bending, "shear": _shear}[kind](c, rec)


def _verdict(c, eta, ratio, clause, answer=None):
    """The verdict: `ratio`, the utilisation written with the vars' keys -- what `#show-check-steel` hands `verify` as `ratio <= 1`, printed in letters, numbers and value with ✔ or ✘ --, its value `eta` and the clause. The last step, eta's own, is taken out of the rows the page prints: the verdict prints it, once."""
    c.vars.pop("eta", None)
    c.steps[:] = [st for st in c.steps if st["result"] != "eta"]
    results = [answer] if answer else [st["result"] for st in c.steps if st.get("level") == 1 or st["result"].endswith("_Rd")][-1:]
    return {"calc": c.record(), "eta": eta, "relation": ratio + " <= 1", "ratio": ratio, "clause": clause, "results": results}


# --- class ---------------------------------------------------------------------------

def _check_class(c, rec):
    N, M_y, M_z = rec["N"], rec["M_y"], rec["M_z"]
    _material(c, rec)
    _forces(c, rec, ("N", "M_y", "M_z"))
    cls = _classify(c, rec, N, M_y, M_z)
    out = {"calc": c.record(), "eta": None, "relation": None, "ratio": None, "results": ["QK"], "classification": cls}
    out["tables"] = [_class_table(cls)]
    return out


def _class_table(cls):
    """Tabelle 5's walls, one row each: c, t, c/t, the three limits, the class."""
    rows = [[w["name"], round(w["c"], 1), round(w["t"], 1), round(w["ratio"], 2)] + [round(x, 2) for x in w["limits"]] + [w["class"]] for w in cls["walls"]]
    return {"title": "Querschnittsklasse", "level": 2, "place": "below", "norm": "SIA 263", "norm_ref": cls["norm_ref"],
            "note": "Massgebend ist die ungünstigste Scheibe (4.3.1.2).",
            "columns": [{"label": "Scheibe", "kind": "wide", "unit": ""}, {"label": "c", "kind": "number", "unit": "mm"},
                        {"label": "t", "kind": "number", "unit": "mm"}, {"label": "c/t", "kind": "number", "unit": ""},
                        {"label": "Klasse 1", "kind": "number", "unit": ""}, {"label": "Klasse 2", "kind": "number", "unit": ""},
                        {"label": "Klasse 3", "kind": "number", "unit": ""}, {"label": "Querschnittsklasse", "kind": "number", "unit": ""}],
            "rows": rows}


def _plates(c, rec, keys):
    """The plates' sizes a formula reads, given to the page at level 3 from the section's table or rectangles."""
    sec = rec["section"]
    labels = {"b": "Breite", "h": "Höhe", "t_f": "Flanschdicke", "t_w": "Stegdicke", "t": "Wanddicke"}
    for key in keys:
        if key not in c.vars and sec.get(key) is not None:
            c.given(key, sec[key], "mm", key, labels[key], level=3, norm=sec["norm_ref"].split(",")[0] if sec["source"] == "c5" else "",
                    norm_ref=sec["norm_ref"].split(", ", 1)[1] if sec["source"] == "c5" else "", source=rec["section_source"], group="section")


def _num(x):
    """A number as a formula writes it: at most four decimals, trailing zeros dropped."""
    return ("%.4f" % x).rstrip("0").rstrip(".")


def _forces(c, rec, keys):
    labels = {"N": ("N_(E d)", "Normalkraft", "kN"), "M_y": ("M_(y,E d)", "Biegemoment", "kNm"), "M_z": ("M_(z,E d)", "Biegemoment", "kNm"),
              "V_z": ("V_(z,E d)", "Querkraft", "kN"), "V_y": ("V_(y,E d)", "Querkraft", "kN")}
    for key in keys:
        if key in ("M_y", "M_z", "V_z", "V_y") and not rec[key]:
            continue
        symbol, label, unit = labels[key]
        c.given(key + "_Ed", rec[key], unit, symbol, label, level=1, group="input")


# --- tension and compression -------------------------------------------------------------

def _tension(c, rec):
    steel = _material(c, rec)
    _section_values(c, rec, ("A",) + (("A_net",) if rec.get("A_net") else ()))
    _forces(c, rec, ("N",))
    N = rec["N"]
    A = rec["section"]["A"]
    g1 = sia263.gamma_M1()["value"]
    n1 = c.step("N_Rd_gross", steel["f_y"] * A / g1, "kN", "N_(R d,1)", "Normalkraftwiderstand im Bruttoquerschnitt", "f_y dot A / gamma_(M 1)",
                ("f_y", "A", "gamma_M1"), "5.1.2 (38)")
    n_rd = n1
    if rec.get("A_net"):
        g2 = sia263.gamma_M2()
        c.given("f_u", steel["f_u"], "N/mm²", "f_u", "Zugfestigkeit", level=2, norm="SIA 263", norm_ref="Tabelle 1", source="norm:SIA 263:2013, Tabelle 1", group="material")
        c.given("gamma_M2", g2["value"], "", "gamma_(M 2)", "Widerstandsbeiwert", level=3, norm="SIA 263", norm_ref=g2["norm_ref"], source="norm:SIA 263:2013, 4.1.3", group="material")
        n2 = c.step("N_Rd_net", 0.9 * steel["f_u"] * rec["A_net"] / g2["value"], "kN", "N_(R d,2)", "Normalkraftwiderstand im Nettoquerschnitt",
                    "0.9 dot f_u dot A_(n e t) / gamma_(M 2)", ("f_u", "A_net", "gamma_M2"), "5.1.2 (39)")
        n_rd = min(n1, n2)
        c.step("N_Rd", n_rd, "kN", "N_(R d)", "Normalkraftwiderstand", "min(N_(R d,1), N_(R d,2))", ("N_Rd_gross", "N_Rd_net"), "5.1.2", level=1, bold=True)
    else:
        c.values["N_Rd"] = n1
        c.vars["N_Rd"] = dict(c.vars["N_Rd_gross"], symbol="N_(R d)")
        c.vars.pop("N_Rd_gross")
        c.steps[-1].update(result="N_Rd", formula="N_(R d) = f_y dot A / gamma_(M 1)", level=1)
    eta = N / n_rd
    c.step("eta", eta, "", "eta", "Ausnutzung", "N_(E d) / N_(R d)", ("N_Ed", "N_Rd"), "5.1.2", level=1, bold=True)
    return _verdict(c, eta, "N_Ed / N_Rd", "5.1.2")


def _compression(c, rec):
    steel = _material(c, rec)
    _section_values(c, rec, ("A",))
    _forces(c, rec, ("N",))
    cls = _classify(c, rec, rec["N"], 0, 0)
    reason = _not_class_4(cls)
    if reason:
        return {"reason": reason, "classification": cls}
    g1 = sia263.gamma_M1()["value"]
    clause = "5.1.2 (38)" if cls["class"] <= 2 else "5.2.2, 5.1.2 (38)"
    n_rd = c.step("N_Rd", steel["f_y"] * rec["section"]["A"] / g1, "kN", "N_(R d)", "Normalkraftwiderstand", "f_y dot A / gamma_(M 1)", ("f_y", "A", "gamma_M1"), clause, level=1, bold=True)
    eta = abs(rec["N"]) / n_rd
    c.step("eta", eta, "", "eta", "Ausnutzung", "abs(N_(E d)) / N_(R d)", ("N_Ed", "N_Rd"), clause, level=1, bold=True)
    out = _verdict(c, eta, "abs(N_Ed) / N_Rd", clause)
    out["classification"] = cls
    return out


# --- bending ----------------------------------------------------------------------------------

def _moment_resistances(c, rec, cls, steel, axes):
    """M_y,Rd and M_z,Rd: plastic (40) in class 1 and 2, elastic (52) in class 3 -- and elastic where SZS C5 prints no W_pl (■ of a thin ROR)."""
    sec = rec["section"]
    g1 = sia263.gamma_M1()["value"]
    out = {}
    for axis in axes:
        plastic = cls["class"] <= 2 and sec.get("W_pl_" + axis) is not None
        w = "W_pl_" + axis if plastic else "W_el_" + axis
        _section_values(c, rec, (w,))
        symbol = "W_(%s,%s)" % ("p l" if plastic else "e l", axis)
        out[axis] = c.step("M_%s_Rd" % axis, steel["f_y"] * sec[w] / g1, "kNm", "M_(%s,R d)" % axis, "Biegewiderstand",
                           "f_y dot %s / gamma_(M 1)" % symbol, ("f_y", w, "gamma_M1"), "5.1.3 (40)" if plastic else "5.2.3 (52)", level=2)
    return out


def _bending(c, rec):
    steel = _material(c, rec)
    N, M_y, M_z = rec["N"], abs(rec["M_y"]), abs(rec["M_z"])
    _forces(c, rec, ("N", "M_y", "M_z"))
    cls = _classify(c, rec, N, M_y, M_z)
    reason = _not_class_4(cls)
    if reason:
        return {"reason": reason, "classification": cls}
    sec = rec["section"]
    axes = [a for a, m in (("y", M_y), ("z", M_z)) if m]
    m_rd = _moment_resistances(c, rec, cls, steel, axes)
    g1 = sia263.gamma_M1()["value"]
    if not N and len(axes) == 1:
        a = axes[0]
        eta = c.step("eta", (M_y if a == "y" else M_z) / m_rd[a], "", "eta", "Ausnutzung", "M_(%s,E d) / M_(%s,R d)" % (a, a),
                     ("M_%s_Ed" % a, "M_%s_Rd" % a), "5.1.3" if cls["class"] <= 2 else "5.2.3", level=1, bold=True)
        out = _verdict(c, eta, "M_%s_Ed / M_%s_Rd" % (a, a), "5.1.3" if cls["class"] <= 2 else "5.2.3")
        out["classification"] = cls
        return out
    _section_values(c, rec, ("A",))
    n_rd = c.step("N_Rd", steel["f_y"] * sec["A"] / g1, "kN", "N_(R d)", "Normalkraftwiderstand", "f_y dot A / gamma_(M 1)", ("f_y", "A", "gamma_M1"), "5.1.2 (38)", level=2)
    n = abs(N) / n_rd
    reduced = cls["class"] <= 2 and (sec["doubly_symmetric_i"] or sec["rolled_rhs"]) and N and n <= 0.9
    if reduced:
        eta, ratio, clause = _reduced_interaction(c, rec, cls, n, axes, m_rd)
        out = _verdict(c, eta, ratio, clause)
    else:
        terms = ["abs(N_(E d)) / N_(R d)"] + ["M_(%s,E d) / M_(%s,R d)" % (a, a) for a in axes]
        uses = ["N_Ed", "N_Rd"] + ["M_%s_Ed" % a for a in axes] + ["M_%s_Rd" % a for a in axes]
        eta = n + sum((M_y if a == "y" else M_z) / m_rd[a] for a in axes)
        clause = "5.1.6.1 (44)" if cls["class"] <= 2 else "5.2.6 (54)"
        c.step("eta", eta, "", "eta", "Ausnutzung", " + ".join(terms), uses, clause, level=1, bold=True)
        ratio = " + ".join(["abs(N_Ed) / N_Rd"] + ["M_%s_Ed / M_%s_Rd" % (a, a) for a in axes])
        out = _verdict(c, eta, ratio, clause)
    out["classification"] = cls
    return out


def _reduced_interaction(c, rec, cls, n, axes, m_rd):
    """(45) to (48): the plastic moments reduced by the normal force, of a doubly symmetric I (5.1.6.2) and a rolled rectangular hollow section (5.1.6.3)."""
    sec = rec["section"]
    M = {"y": abs(rec["M_y"]), "z": abs(rec["M_z"])}
    c.step("n", n, "", "n", "bezogene Normalkraft", "abs(N_(E d)) / N_(R d)", ("N_Ed", "N_Rd"), "5.1.6.2", level=3)
    reduced = {}
    if sec["doubly_symmetric_i"]:
        _plates(c, rec, ("b", "t_f"))
        a = min((sec["A"] - 2 * sec["b"] * sec["t_f"]) / sec["A"], 0.5)
        c.step("a", a, "", "a", "Hilfswert", "min((A - 2 dot b dot t_f) / A, 0.5)", ("A", "b", "t_f"), "5.1.6.2", level=3)
        xi = 1 / (1 - 0.5 * a)
        c.step("xi", xi, "", "xi", "Hilfswert", "1 / (1 - 0.5 dot a)", ("a",), "5.1.6.2", level=3)
        if "y" in axes:
            reduced["y"] = c.step("M_y_N_Rd", min(m_rd["y"] * xi * (1 - n), m_rd["y"]), "kNm", "M_(y,N,R d)", "reduzierter Biegewiderstand",
                                  "min(M_(y,R d) dot xi dot (1 - n), M_(y,R d))", ("M_y_Rd", "xi", "n"), "5.1.6.2 (45)", level=2)
        if "z" in axes:
            value = m_rd["z"] * (1 - ((n - a) / (1 - a)) ** 2) if n > a else m_rd["z"]
            reduced["z"] = c.step("M_z_N_Rd", value, "kNm", "M_(z,N,R d)", "reduzierter Biegewiderstand",
                                  "M_(z,R d) dot (1 - ((n - a) / (1 - a))^2)" if n > a else "M_(z,R d)", ("M_z_Rd", "n", "a"),
                                  "5.1.6.2 (46)" if n > a else "5.1.6.2 (47)", level=2)
        # 5.1.6.4, an I: alpha = 2, beta = 5 n, at least 1.1
        alpha, beta = 2.0, max(5 * n, 1.1)
        given_alpha = True
    else:
        t = sec["t"]
        for axis in axes:
            # 5.1.6.3: a = (A − 2 h t)/A for the strong axis, (A − 2 b t)/A for the weak one
            a = min((sec["A"] - 2 * (sec["b"] if axis == "y" else sec["h"]) * t) / sec["A"], 0.5)
            _plates(c, rec, ("b", "h", "t"))
            c.step("a_%s" % axis, a, "", "a_%s" % axis, "Hilfswert", "min((A - 2 dot %s dot t) / A, 0.5)" % ("b" if axis == "y" else "h"), ("A", "b" if axis == "y" else "h", "t"), "5.1.6.3", level=3)
            xi = 1 / (1 - 0.5 * a)
            c.step("xi_%s" % axis, xi, "", "xi_%s" % axis, "Hilfswert", "1 / (1 - 0.5 dot a_%s)" % axis, ("a_%s" % axis,), "5.1.6.3", level=3)
            reduced[axis] = c.step("M_%s_N_Rd" % axis, min(m_rd[axis] * xi * (1 - n), m_rd[axis]), "kNm", "M_(%s,N,R d)" % axis, "reduzierter Biegewiderstand",
                                   "min(M_(%s,R d) dot xi_%s dot (1 - n), M_(%s,R d))" % (axis, axis, axis), ("M_%s_Rd" % axis, "xi_%s" % axis, "n"), "5.1.6.3 (45)", level=2)
        # 5.1.6.4, a rolled rectangular hollow section: alpha = beta = 1.66 / (1 − 1.33 n²), at most 6
        alpha = beta = min(1.66 / (1 - 1.33 * n ** 2), 6.0)
        given_alpha = False
    if len(axes) == 1:
        a = axes[0]
        return M[a] / reduced[a], "M_%s_Ed / M_%s_N_Rd" % (a, a), "5.1.6.2" if sec["doubly_symmetric_i"] else "5.1.6.3"
    if given_alpha:
        c.given("alpha_N", alpha, "", "alpha", "Exponent", level=3, norm="SIA 263", norm_ref="5.1.6.4", source="norm:SIA 263:2013, 5.1.6.4", group="norm")
        c.step("beta_N", beta, "", "beta", "Exponent", "max(5 dot n, 1.1)", ("n",), "5.1.6.4", level=3)
    else:
        c.step("alpha_N", alpha, "", "alpha", "Exponent", "min(1.66 / (1 - 1.33 dot n^2), 6)", ("n",), "5.1.6.4", level=3)
        c.given("beta_N", beta, "", "beta", "Exponent", level=3, norm="SIA 263", norm_ref="5.1.6.4", source="python:domains/steel_resistance.py", group="norm")
    eta = (M["y"] / reduced["y"]) ** alpha + (M["z"] / reduced["z"]) ** beta
    # verify's power is a number written out (lib/formula.typ: `atom ^ number`), alpha and beta being known here
    return eta, "(M_y_Ed / M_y_N_Rd)^%s + (M_z_Ed / M_z_N_Rd)^%s" % (_num(alpha), _num(beta)), "5.1.6.4 (48)"


# --- shear ------------------------------------------------------------------------------------

def _shear(c, rec):
    steel = _material(c, rec)
    sec = rec["section"]
    V_z, V_y, M_y = abs(rec["V_z"]), abs(rec["V_y"]), abs(rec["M_y"])
    _forces(c, rec, ("V_z", "V_y", "M_y"))
    cls = _classify(c, rec, 0.0, M_y, 0.0)
    reason = _not_class_4(cls)
    if reason:
        return {"reason": reason, "classification": cls}
    E = sia263.material()["E"]
    notes = []
    if sec["shape"] in ("I", "U"):
        # 5.1.4.2, (42): the web's slenderness, held against the simplified criterion for an I and a U
        limit = math.sqrt(4 * E / steel["f_y"])
        ratio = (sec["h"] - sec["t_f"]) / sec["t_w"]
        if ratio > limit:
            return {"reason": "(h − t_f)/t_w = %.1f is above sqrt(4 E / f_y) = %.1f (SIA 263 5.1.4.2, (42)): shear buckling after 4.5.4 is not built" % (ratio, limit),
                    "classification": cls}
        c.given("E", E, "N/mm²", "E", "Elastizitätsmodul", level=3, norm="SIA 263", norm_ref="3.2.2.3", source="norm:SIA 263:2013, 3.2.2.3", group="material")
        c.step("web_slenderness", ratio, "", "(h - t_f) / t_w", "Stegschlankheit", "%s / %s" % (_num(sec["h"] - sec["t_f"]), _num(sec["t_w"])), (), "5.1.4.2 (42)", level=3)
        c.step("web_limit", limit, "", "sqrt(4 E / f_y)", "Grenzschlankheit", "sqrt(4 dot E / f_y)", ("E", "f_y"), "5.1.4.2 (42)", level=3)
    else:
        notes.append("Schubbeulen nach 4.5.4 nicht nachgewiesen (5.1.4.2).")
    c.given("tau_y", steel["tau_y"], "N/mm²", "tau_y", "Fliessschubspannung", level=2, norm="SIA 263", norm_ref="Tabelle 1",
            source="norm:SIA 263:2013, Tabelle 1", group="material")
    g1 = sia263.gamma_M1()["value"]
    etas, uses, terms = [], [], []
    v_rd = {}
    for axis, V in (("z", V_z), ("y", V_y)):
        if not V:
            continue
        area = "A_v_%s" % axis
        if axis == "z" and cls["class"] == 3 and sec["shape"] in ("I", "U") and sec.get("A_w"):
            area = "A_w"   # 5.2.4: A_v replaced by A_w in class 3
        _section_values(c, rec, (area,))
        symbol = {"A_v_z": "A_v", "A_v_y": "A_(v,y)", "A_w": "A_w"}[area]
        clause = "5.1.4 (41)" if area != "A_w" else "5.2.4, 5.1.4 (41)"
        v_rd[axis] = c.step("V_%s_Rd" % axis, steel["tau_y"] * sec[area] / g1, "kN", "V_(%s,R d)" % axis, "Querkraftwiderstand",
                            "tau_y dot %s / gamma_(M 1)" % symbol, ("tau_y", area, "gamma_M1"), clause, level=2)
        etas.append(V / v_rd[axis])
        terms.append("V_(%s,E d) / V_(%s,R d)" % (axis, axis))
        uses += ["V_%s_Ed" % axis, "V_%s_Rd" % axis]
    eta_v = c.step("eta_V", max(etas), "", "eta_V", "Ausnutzung Querkraft", "max(%s)" % ", ".join(terms) if len(terms) > 1 else terms[0],
                   uses, "5.1.4", level=2)
    eta = eta_v
    if M_y:
        m_rd = _moment_resistances(c, rec, cls, steel, ("y",))["y"]
        if V_z > 0.5 * v_rd.get("z", float("inf")):
            if not (sec["doubly_symmetric_i"] or sec["rolled_rhs"]):
                return {"reason": "V_z,Ed is above 0.5 V_z,Rd (SIA 263 5.1.5.1): the bending resistance must be reduced, and 5.1.5 gives a reduction for a doubly symmetric I and a rolled rectangular hollow section only",
                        "classification": cls}
            if sec["doubly_symmetric_i"]:
                b, t1, t2, h = sec["b"], sec["t_f"], sec["t_w"], sec["h"]
                hw = h - 2 * t1
            else:
                b, t1, t2, h = sec["b"], sec["t"], 2 * sec["t"], sec["h"]
                hw = h - 3 * sec["t"]
            k = 4 if cls["class"] <= 2 else 6
            for key, value, label in (("b", b, "Breite"), ("h", h, "Höhe"), ("t_1", t1, "Flanschdicke"), ("t_2", t2, "Stegdicke"), ("h_w", hw, "Steghöhe")):
                c.given(key, value, "mm", key, label, level=3, norm=sec["norm_ref"].split(",")[0] if sec["source"] == "c5" else "",
                        norm_ref="5.1.5.2" if key in ("t_1", "t_2", "h_w") else "", source=rec["section_source"], group="section")
            m_v = (b * t1 * steel["f_y"] * (h - t1) / g1 + hw ** 2 * t2 * steel["f_y"] / (k * g1) * (1 - (V_z / v_rd["z"]) ** 2))
            m_v = min(m_v, m_rd)
            c.step("M_V_Rd", m_v, "kNm", "M_(V,R d)", "reduzierter Biegewiderstand",
                   "b dot t_1 dot f_y dot (h - t_1) / gamma_(M 1) + h_w^2 dot t_2 dot f_y / (%d dot gamma_(M 1)) dot (1 - (V_(z,E d) / V_(z,R d))^2)" % k,
                   ("b", "t_1", "f_y", "h", "gamma_M1", "h_w", "t_2", "V_z_Ed", "V_z_Rd"), "5.1.5.2 (43)" if k == 4 else "5.2.5.2 (53)", level=2)
            eta_m = c.step("eta_M", M_y / m_v, "", "eta_M", "Ausnutzung Biegung", "M_(y,E d) / M_(V,R d)", ("M_y_Ed", "M_V_Rd"), "5.1.5", level=2)
        else:
            eta_m = c.step("eta_M", M_y / m_rd, "", "eta_M", "Ausnutzung Biegung", "M_(y,E d) / M_(y,R d)", ("M_y_Ed", "M_y_Rd"), "5.1.5.1", level=2)
        eta = max(eta_v, eta_m)
    out = _verdict(c, eta, "max(eta_V, eta_M)" if M_y else "eta_V", "5.1.4, 5.1.5" if M_y else "5.1.4")
    out["classification"] = cls
    out["notes"] = notes
    return out
