"""Stabdübel (dowel) connections: the design value of the shear resistance, SIA 265:2021 6.2.1.

One module per kind of connector, chosen on the connector's `type`; this is the first. What it computes is equation (88):

    R_d,Verb = k_alpha · k_red · n_tot · (p · k_beta) · sqrt(M_u,k · f_h,1,k · d) · eta_w · eta_t

with k_alpha from 6.2.1.1, M_u,k from equation (87), f_h,k from Tabelle 22, k_red from equation (86) and k_beta from **Anhang A, Tabellen 45 and 46** -- the more accurate bilinear form, which 6.2.1.1 offers as an alternative to the simplified Tabelle 23 and which the engineer chose for every configuration. R_d = R_d,Verb / n_tot.

**Where the numbers come from: `calc/norms/`, and nowhere here** (v0.77). Every value of SIA 265 this module calculates with is read through `norms/sia265.py` from the JSON files beside it -- a strength class's rho_k and species, eta_w, eta_t, k_alpha, the minimum spacings of Tabelle 24, the K_ser coefficients of Tabelle 25, **and the coefficients inside the formulas**: the 0.082, 0.01, -0.3, 0.015 and 1.35/0.90 of Tabelle 22, the 0.3 and 2.6 of equation (87), the -0.1, 10 and 0.25 of equation (86), the corners of Tabellen 45 and 46 and the two conditions above equations (130) and (131). Until v0.76 those stayed beside their formula as named constants; the engineer's rule is that a norm value is written once and only in `calc/norms/`, so what stays here is the *shape* of each formula, and the printed formula strings are composed from the same numbers the arithmetic uses (docs/architecture/layout.md §11).

**Two things the engineer's own workbook does differently**, both settled in favour of the norm:

- `Verbindung.xlsm`, sheet «Stabdübel (Holz-Holz)», cells O34/P34 compute the *einschnittig* second member's t_2,i with sqrt(beta_f/(1+beta_f)) -- member 1's bracket. Tabelle 45 equation (125) uses sqrt(1/(1+beta_f)). The two agree exactly when beta_f = 1, which is every case that workbook has been used on, and part company as soon as the two members differ in strength class, in grain angle or in predrilling.
- Tabelle 46 equations (130) and (131) hold only *wenn t_2 >= 2 · t_1* resp. *wenn t_1 >= 0,35 · t_2*. The workbook enforces them only through the data validation of 'Stabdübel (Stahl-Holz)'!C20 (0.35 <= t_1/t_2 <= 0.5), which a typed-over value bypasses. Here they are checked and reported -- as a warning, not a stop, since the number is still the norm's own formula and it is the engineer who decides.

**What is a warning and what is a stop.** A defect in the data stops the export (section 3.6). Two things about a *connection* only warn, and both for the v0.33 reason: stopping would stop the positions' own export with it, and leave Woodcore nothing to repair the connector against. Those are a member whose position no longer resolves, and a dowel pattern that breaks the minimum spacings of Tabelle 24 -- which SIA 265 6.2.1.1 makes equation (88) conditional on, so it is said loudly and printed in the report, but the engineer is the one who fixes the layout.
"""

import math

import engine
import validation
from domains._common import fail as _fail  # one copy of the domains' helpers (spec 2026-10-19-base-saine-nettoyage, G4)
from norms import sia263, sia265
import number_text

# What a connector of this kind is called, in the `type` field of its source and of Positionen.xlsx's own list.
TYPE = "Stabdübel"

# No coefficient of SIA 265 is written in this module: k_alpha, k_red's, M_u,k's, Tabelle 22's and the corners of Tabellen 45 and 46 are all read from calc/norms/ at the moment they are used (norms/sia265.py).

# The four configurations SIA 265 gives a k_beta for. `Holz-Holz mehrschnittig` and a single one-sided steel plate are deliberately absent: Tabellen 45 and 46 do not cover them, and 6.1.1.11 sends a configuration the norm does not treat to testing rather than to an equation applied outside its domain.
ASSEMBLIES = {
    "Holz-Holz einschnittig": {
        "family": "timber-timber",
        "shear_planes": 1,
        "members": 2,
        "equations": "SIA 265 Tabelle 45, Gleichungen (124) und (125)",
    },
    "Holz-Holz zweischnittig": {
        "family": "timber-timber",
        "shear_planes": 2,
        "members": 2,
        "equations": "SIA 265 Tabelle 45, Gleichungen (120) und (121)",
    },
    "Stahl-Holz, Bleche aussen": {
        "family": "steel-timber",
        "shear_planes": 2,
        "members": 1,
        "equations": "SIA 265 Tabelle 46, Gleichung (128)",
    },
    "Stahl-Holz, Schlitzbleche": {
        "family": "steel-timber",
        "shear_planes": None,  # 2 per plate
        # One timber member is entered, its whole thickness: the slots are what divide it into a side and a middle piece, which steel_geometry() computes.
        "members": 1,
        "equations": "SIA 265 Tabelle 46, Gleichungen (129) bis (131)",
    },
}


# Configurations an engineer may well want and SIA 265 gives no k_beta for: Tabelle 45 covers ein- and zweischnittig only, Tabelle 46 zwei- and mehrschnittig only. They are named here so that asking for one is answered with the reason rather than with "unknown assembly" -- 6.1.1.11 sends a configuration the norm does not treat to testing, not to an equation applied outside its range.
UNCOVERED_ASSEMBLIES = {
    "Holz-Holz mehrschnittig": "SIA 265 Tabelle 45 gibt k_beta nur für ein- und zweischnittige Holz-Holz-Verbindungen an.",
    "Stahl-Holz, Blech aussen, einschnittig": "SIA 265 Tabelle 46 gibt k_beta nur für zwei- und mehrschnittige Stahl-Holz-Verbindungen an.",
    "Holz-Beton": "SIA 265 Kapitel 6 behandelt Holz-Beton-Verbindungen nicht.",
}

# Two dowels closer than this (mm) are one point typed twice -- connection.py's own tolerance.
SAME_POINT = 1e-6


# --- the pieces of equation (88) ---------------------------------------------

def embedment_strength(rho_k, d, alpha, species, predrilled):
    """f_h,alpha,k in N/mm2, SIA 265 Tabelle 22 (6.1.4.3).

    Three rows: softwood predrilled, softwood not predrilled (where the two directions are equal, so the angle does not enter), hardwood predrilled. `alpha` is the angle between the force and the grain in degrees, and the norm interpolates the two directions linearly across it.

    Hardwood not predrilled has no row at all, so it is refused rather than read off the softwood one.
    """
    table = sia265.embedment()
    divisors = table["f_90_divisor"]
    if species not in divisors:
        _fail("f_h,k", "species %r -- SIA 265 Tabelle 22 gives %s"
              % (species, " and ".join(sorted(divisors))))
    if not 0 <= alpha <= 90:
        _fail("f_h,k", "alpha = %s deg -- the angle between force and grain is folded into 0 to 90" % alpha)
    if not predrilled and species not in table["undrilled_species"]:
        _fail("f_h,k", "%s must be predrilled -- SIA 265 Tabelle 22 gives no value for it without predrilling" % species)
    if not predrilled:
        value = table["factor"] * d ** table["undrilled_exponent"] * rho_k
        return {"f_h_0_k": value, "f_h_90_k": value, "f_h_alpha_k": value}
    f_0 = table["factor"] * (1 - table["predrilled_slope"] * d) * rho_k
    f_90 = f_0 / (divisors[species] + table["f_90_diameter_term"] * d)
    f_alpha = f_90 + (f_0 - f_90) * (90 - alpha) / 90.0
    return {"f_h_0_k": f_0, "f_h_90_k": f_90, "f_h_alpha_k": f_alpha}


def yield_moment(f_u_k, d):
    """M_u,k in Nmm, SIA 265 equation (87)."""
    clause = sia265.yield_moment()
    return clause["factor"] * f_u_k * d ** clause["exponent"]


def reduction(n, a_1, d, alpha):
    """k_red, SIA 265 equation (86), for one timber member.

    `n` is the number of dowels in a row along the grain. With one dowel in a row there is nothing to reduce, and a_1 has no meaning, so the answer is 1 -- which equation (86) does not state and the workbook guards on its steel sheet only.
    """
    if n < 1:
        _fail("k_red", "n = %r -- a row holds at least one dowel" % n)
    clause = sia265.reduction()
    if n == 1:
        return float(clause["single_fastener"])
    if a_1 is None or a_1 <= 0:
        _fail("k_red", "a_1 = %r with n = %d -- the spacing along the grain is needed as soon as two dowels follow one another"
              % (a_1, n))
    if not 0 <= alpha <= 90:
        _fail("k_red", "alpha = %s deg -- the angle between force and grain is folded into 0 to 90" % alpha)
    value = (n ** clause["n_exponent"]
             * (a_1 / (clause["spacing_reference"] * d)) ** clause["spacing_exponent"]
             * (90 - alpha) / 90.0
             + alpha / 90.0)
    return min(float(clause["maximum"]), value)


def _bilinear(t, t_1, k_1, t_2, k_2):
    """k_beta at thickness `t`, given the two corners of Figur 45: 0 at t = 0, k_1 at t_1, k_2 at t_2, flat beyond.

    Anhang A, A.1.2: «Für kleinere Holzdicken und Zwischenwerte sind die Hilfswerte linear zu interpolieren».
    """
    if t >= t_2:
        return k_2
    if t_1 > 0 and t >= t_1:
        return k_1 + (t - t_1) / (t_2 - t_1) * (k_2 - k_1)
    if t_1 > 0:
        return t / t_1 * k_1
    return t / t_2 * k_2


def _timber_corners(assembly, beta_f, f_u_k, f_h_1_k, f_h_2_k, d):
    """The four corners of Tabelle 45, per member: (t_i,1, k_beta_i,1, t_i,2, k_beta_i,2).

    bracket_1 = sqrt(beta_f/(1+beta_f)) + 1 belongs to member 1 and bracket_2 = sqrt(1/(1+beta_f)) + 1 to member 2. The two are equal only at beta_f = 1, which is why swapping them is invisible on a symmetric joint -- and why the workbook's O34/P34 have never been caught by use.
    """
    table = sia265.table_45()
    side, middle = table["seitenholz"], table["mittelholz"]
    k_max = math.sqrt(table["k_max_numerator"] * beta_f / (1 + beta_f))
    bracket_1 = math.sqrt(beta_f / (1 + beta_f)) + 1
    bracket_2 = math.sqrt(1 / (1 + beta_f)) + 1
    base_1 = math.sqrt(f_u_k / f_h_1_k) * d ** table["t_exponent"]
    base_2 = math.sqrt(f_u_k / f_h_2_k) * d ** table["t_exponent"]

    def seitenholz(bracket, base):
        return (side["t_1_factor"] * bracket * base, side["k_1_share"] * k_max,
                side["t_2_factor"] * bracket * base, k_max)

    # Seitenholz t_1 -- the same in both configurations, equations (120) and (124)
    member_1 = seitenholz(bracket_1, base_1)

    if assembly == "Holz-Holz zweischnittig":
        # Mittelholz t_2, equation (121): the lower corner is the origin
        member_2 = (0.0, 0.0, middle["t_2_factor"] * (1 / math.sqrt(1 + beta_f)) * base_2, k_max)
    else:
        # Seitenholz t_2, equation (125)
        member_2 = seitenholz(bracket_2, base_2)
    return member_1, member_2, k_max


def _steel_corners(assembly, f_u_k, f_h_k, d):
    """The corners of Tabelle 46, per shear plane. Equation (128) for a timber between two outer plates, (129)/(130) for a side timber against a slotted plate, (131) for a timber between two slotted plates."""
    table = sia265.table_46()
    base = math.sqrt(f_u_k / f_h_k) * d ** table["t_exponent"]

    def corner(key):
        spec = table[key]
        k_2 = spec["k_2"] if "k_2" in spec else math.sqrt(spec["k_2_root"])
        return (spec["t_1_factor"] * base, float(spec["k_1"]), spec["t_2_factor"] * base, float(k_2))

    if assembly == "Stahl-Holz, Bleche aussen":
        # equation (128), Mittelholz: the lower corner is the origin and k_beta tops out at sqrt(2)
        return {"outer": corner("mittelholz_bleche_aussen")}
    # equations (129)/(130) Scherfuge A, and (131) Scherfuge B
    return {
        "A": corner("seitenholz_scherfuge_a"),
        "B": corner("mittelholz_scherfuge_b"),
    }


def steel_geometry(b, slot, plates, ratio):
    """The side and middle timber thicknesses of a slotted-plate joint, from the whole member thickness.

    With one plate the timber is simply halved by the slot. With several, the member is `plates` slots plus (plates-1) middle pieces plus two side pieces, and `ratio` = t_1/t_2 says how the timber is shared between them -- which is the workbook's own arrangement (cells C18/C19 of «Stabdübel (Stahl-Holz)»).
    """
    if plates < 1:
        _fail("steel geometry", "%r plates -- a slotted-plate joint has at least one" % plates)
    if slot <= 0:
        _fail("steel geometry", "slot width %r mm -- expected a positive number" % slot)
    if b <= plates * slot:
        _fail("steel geometry", "the member is %s mm thick and %d slot(s) of %s mm take all of it -- no timber is left"
              % (b, plates, slot))
    if plates == 1:
        return {"t_1": (b - slot) / 2.0, "t_2": 0.0}
    if not 0 < ratio:
        _fail("steel geometry", "t_1/t_2 = %r -- expected a positive ratio" % ratio)
    t_2 = (b - plates * slot) / ((plates - 1) + 2 * ratio)
    return {"t_1": ratio * t_2, "t_2": t_2}


def shear_planes(assembly, plates=1):
    """p, the number of shear planes per dowel. Two per slotted plate; two for a timber between outer plates; one or two for a timber-timber joint."""
    spec = ASSEMBLIES[assembly]
    if spec["shear_planes"] is not None:
        return spec["shear_planes"]
    return 2 * plates


# --- the resistance ----------------------------------------------------------

def _timber_resistance(inputs, warnings):
    """Holz-Holz, one or two shear planes."""
    d, f_u_k = inputs["d"], inputs["f_u_k"]
    members = inputs["members"]
    strengths = [embedment_strength(m["rho_k"], d, m["alpha"], m["species"], m["predrilled"]) for m in members]
    f_h_1_k = strengths[0]["f_h_alpha_k"]
    f_h_2_k = strengths[1]["f_h_alpha_k"]
    beta_f = f_h_2_k / f_h_1_k

    corner_1, corner_2, k_max = _timber_corners(inputs["assembly"], beta_f, f_u_k, f_h_1_k, f_h_2_k, d)
    k_beta_1 = _bilinear(members[0]["t"], *corner_1)
    k_beta_2 = _bilinear(members[1]["t"], *corner_2)
    k_beta = min(k_beta_1, k_beta_2)

    return {
        "strengths": strengths,
        "f_h_1_k": f_h_1_k,
        "f_h_2_k": f_h_2_k,
        "f_h_ref_k": f_h_1_k,  # equation (88): the Seitenholz 1 value goes into the root
        "beta_f": beta_f,
        "k_beta_max": k_max,
        # `shape` says which row of Tabelle 45 the corner was read off, so the report can write that row's
        # own formula rather than a table of the numbers it produced (the engineer, v0.84). It is the
        # table's row and not a description of it: the printed formula is composed from the same JSON
        # factors the arithmetic used (docs/architecture/layout.md §11).
        "corners": [
            {"member": 1, "t": members[0]["t"], "t_1": corner_1[0], "k_1": corner_1[1],
             "t_2": corner_1[2], "k_2": corner_1[3], "k_beta": k_beta_1, "shape": "seitenholz_1"},
            {"member": 2, "t": members[1]["t"], "t_1": corner_2[0], "k_1": corner_2[1],
             "t_2": corner_2[2], "k_2": corner_2[3], "k_beta": k_beta_2,
             "shape": "mittelholz" if inputs["assembly"] == "Holz-Holz zweischnittig" else "seitenholz_2"},
        ],
        "k_beta": k_beta,
        "p": shear_planes(inputs["assembly"]),
        "p_k_beta": shear_planes(inputs["assembly"]) * k_beta,
    }


def _steel_resistance(inputs, warnings):
    """Stahl-Holz: outer plates, or one or more slotted plates."""
    d, f_u_k = inputs["d"], inputs["f_u_k"]
    member = inputs["members"][0]
    strength = embedment_strength(member["rho_k"], d, member["alpha"], member["species"], member["predrilled"])
    f_h_k = strength["f_h_alpha_k"]
    steel = inputs["steel"]
    plates = steel.get("plates", 1)
    corners = _steel_corners(inputs["assembly"], f_u_k, f_h_k, d)

    if inputs["assembly"] == "Stahl-Holz, Bleche aussen":
        corner = corners["outer"]
        k_beta = _bilinear(member["t"], *corner)
        p = shear_planes(inputs["assembly"])
        rows = [{"plane": "Scherfuge", "t": member["t"], "count": p, "shape": "mittelholz_bleche_aussen",
                 "t_1": corner[0], "k_1": corner[1], "t_2": corner[2], "k_2": corner[3], "k_beta": k_beta}]
        p_k_beta = p * k_beta
        geometry = {"t_1": member["t"], "t_2": 0.0}
    else:
        geometry = steel_geometry(member["t"], steel["slot"], plates, steel.get("ratio", 0.5))
        t_1, t_2 = geometry["t_1"], geometry["t_2"]
        corner_a, corner_b = corners["A"], corners["B"]
        k_beta_1 = _bilinear(t_1, *corner_a)
        k_beta_2 = _bilinear(t_2, *corner_b) if plates > 1 else 0.0
        p = shear_planes(inputs["assembly"], plates)
        count_b = p - 2
        p_k_beta = 2 * k_beta_1 + count_b * k_beta_2
        rows = [{"plane": "A", "t": t_1, "count": 2, "shape": "seitenholz_scherfuge_a",
                 "t_1": corner_a[0], "k_1": corner_a[1], "t_2": corner_a[2], "k_2": corner_a[3], "k_beta": k_beta_1}]
        if count_b:
            rows.append({"plane": "B", "t": t_2, "count": count_b, "shape": "mittelholz_scherfuge_b",
                         "t_1": corner_b[0], "k_1": corner_b[1], "t_2": corner_b[2], "k_2": corner_b[3],
                         "k_beta": k_beta_2})
            # Tabelle 46, the conditions printed above equations (130) and (131)
            conditions = sia265.table_46()["conditions"]
            over_t1 = conditions["equation_130_t2_over_t1"]
            over_t2 = conditions["equation_131_t1_over_t2"]
            if t_2 < over_t1 * t_1 - 1e-9:
                warnings.append(
                    "Tabelle 46, Gleichung (130) gilt nur wenn t_2 >= %s · t_1; hier ist t_2 = %.1f mm und %s · t_1 = %.1f mm."
                    % (_fmt(over_t1), t_2, _fmt(over_t1), over_t1 * t_1))
            if t_1 < over_t2 * t_2 - 1e-9:
                warnings.append(
                    "Tabelle 46, Gleichung (131) gilt nur wenn t_1 >= %s · t_2; hier ist t_1 = %.1f mm und %s · t_2 = %.1f mm."
                    % (_fmt(over_t2), t_1, _fmt(over_t2), over_t2 * t_2))
        k_beta = min(r["k_beta"] for r in rows)

    return {
        "strengths": [strength],
        "f_h_1_k": f_h_k,
        "f_h_2_k": None,
        "f_h_ref_k": f_h_k,
        "beta_f": None,
        "k_beta_max": max(r["k_2"] for r in rows),
        "geometry": geometry,
        "planes": rows,
        "k_beta": k_beta,
        "p": p,
        "p_k_beta": p_k_beta,
    }


def analyse(inputs):
    """Every number of SIA 265 6.2.1 for one dowel connection, and the warnings it earned.

    `inputs` is the resolved form of a connector's `dowel` block: `assembly`, `d`, `f_u_k`, `n_tot`, `impact`, `truss`, a `members` list carrying each timber's resolved `rho_k`, `species`, `moisture_class`, `alpha`, `t`, `predrilled`, `n` and `a_1`, and for a steel joint a `steel` block. Nothing here reads a file: the caller resolves the positions first, so the same function serves the export and Woodcore's live preview.
    """
    warnings = []
    assembly = inputs.get("assembly")
    if assembly in UNCOVERED_ASSEMBLIES:
        _fail("dowel", "%r: %s Der Tragwiderstand ist nach 6.1.1.11 versuchsmässig zu bestimmen."
              % (assembly, UNCOVERED_ASSEMBLIES[assembly]))
    if assembly not in ASSEMBLIES:
        _fail("dowel", "assembly %r -- SIA 265 Tabellen 45 and 46 give %s"
              % (assembly, ", ".join(sorted(ASSEMBLIES))))
    d = inputs["d"]
    diameters = sia265.resistance_diameters()
    if not diameters["min"] <= d <= diameters["max"]:
        warnings.append(
            "SIA 265 6.2.1.1 gibt Gleichung (88) für Stabdübel mit d = %g bis %g mm an; hier ist d = %g mm."
            % (diameters["min"], diameters["max"], d))
    spec = ASSEMBLIES[assembly]
    members = inputs["members"]
    if len(members) < spec["members"]:
        _fail("dowel", "assembly %r needs %d timber member(s), %d given"
              % (assembly, spec["members"], len(members)))

    if spec["family"] == "timber-timber":
        result = _timber_resistance(inputs, warnings)
    else:
        result = _steel_resistance(inputs, warnings)

    # k_red per timber member, the smallest retained (6.1.4.2)
    reductions = []
    for index, member in enumerate(members[:spec["members"]], start=1):
        rows = member["n"] or 1
        reductions.append({
            "member": index,
            "n": member["n"],
            # n_quer, the classeur's own ROUNDUP(n_tot / n) ('Stabdübel (Holz-Holz)'!C31, '(Stahl-Holz)'!C29).
            # Nothing in equation (88) reads it -- it is the count across the grain that the rows imply, and
            # the engineer checks the drawing against it -- so it is carried and never multiplied by.
            "n_quer": int(math.ceil(inputs["n_tot"] / float(rows))),
            "a_1": member.get("a_1"),
            "alpha": member["alpha"],
            "k_red": reduction(member["n"], member.get("a_1"), d, member["alpha"]),
        })
    k_red = min(r["k_red"] for r in reductions)

    m_u_k = yield_moment(inputs["f_u_k"], d)
    n_tot = inputs["n_tot"]
    if n_tot < 1:
        _fail("dowel", "n_tot = %r -- a connection has at least one dowel" % n_tot)

    timber = members[:spec["members"]]
    moisture = _moisture_class(timber)
    classes = {m["moisture_class"] for m in timber}
    if len(classes) > 1:
        warnings.append(
            "Die Bauteile sind verschiedenen Feuchteklassen zugeordnet (%s); massgebend ist die ungünstigste, "
            "Klasse %d mit eta_w = %s (SIA 265 Tabelle 4)."
            % (", ".join(str(c) for c in sorted(classes)), moisture, sia265.eta_w(moisture)))
    eta_w = sia265.eta_w(moisture)
    eta_t = sia265.eta_t(bool(inputs.get("impact")))

    # Equation (88), in N, then kN. k_alpha is the norm's own named constant (6.2.1.1).
    #
    # ⚠️ **One fastener first, then the connection** (the engineer, v0.84): equation (88) states
    # R_d,Verb with n_tot inside it, and what an engineer reads off the page is the resistance of one
    # dowel. So the product is taken without n_tot -- which is R_d exactly -- and R_d,Verb is n_tot
    # times it. The two numbers are the norm's own to the last digit either way; what changes is which
    # of them the report derives from the other, and so which of them carries the working.
    k_alpha = sia265.constant("k_alpha")
    r_d = (k_alpha * k_red * result["p_k_beta"]
           * math.sqrt(m_u_k * result["f_h_ref_k"] * d) / 1000.0
           * eta_w * eta_t)
    r_d_verb = n_tot * r_d

    out = dict(result)
    out.update({
        "assembly": assembly,
        "d": d,
        "f_u_k": inputs["f_u_k"],
        "dowel_steel": inputs.get("dowel_steel", ""),
        "M_u_k": m_u_k,
        "k_alpha": k_alpha,
        "reductions": reductions,
        "k_red": k_red,
        "n_tot": n_tot,
        "moisture_class": moisture,
        "eta_w": eta_w,
        "eta_t": eta_t,
        "R_d_Verb": r_d_verb,
        "R_d": r_d,
        "warnings": warnings,
    })
    # 5.3.6.2.2 is narrower than the word «truss»: it is the connections of the Ausfachungsstäbe under the simplified calculation of 5.3.6.1.2. So it is carried as a second answer beside R_d,Verb -- the workbook's own C44/C45 arrangement -- and never folded into R_d, where a reader could not see it. Since v0.84 it is a second answer *twice*: the connection's and one fastener's, because the report gives both numbers and a truss node reduces both (the engineer's request).
    if inputs.get("truss"):
        factor = sia265.constant("truss_reduction")
        out["truss_factor"] = factor
        out["R_d_truss"] = r_d * factor
        out["R_d_Verb_truss"] = r_d_verb * factor
    out["K_ser"] = _stiffness(inputs, result, spec, members)
    return out


def preview(inputs):
    """p, and where the timber resolves k_beta, p · k_beta and M_u,k -- the pieces of equation (88) that depend on the assembly, the timber, d and f_u,k and on no dowel of the pattern. What Woodcore shows while a connector is not calculated yet; never exported (connector.preview).

    p is Tabelle 45/46's own count of shear planes: 1 for Holz-Holz einschnittig, 2 for zweischnittig and for outer plates, 2 per slotted plate.
    """
    assembly = inputs.get("assembly")
    if assembly not in ASSEMBLIES:
        return {}
    plates = (inputs.get("steel") or {}).get("plates", 1)
    out = {"p": shear_planes(assembly, plates)}
    spec = ASSEMBLIES[assembly]
    members = inputs.get("members") or []
    if len(members) < spec["members"] or any(not m.get("rho_k") or not m.get("t") for m in members[:spec["members"]]):
        return out
    try:
        result = _timber_resistance(inputs, []) if spec["family"] == "timber-timber" else _steel_resistance(inputs, [])
    except (validation.ValidationError, KeyError, TypeError, ValueError, ZeroDivisionError):
        return out
    out.update({"k_beta": result["k_beta"], "p": result["p"], "p_k_beta": result["p_k_beta"]})
    if inputs.get("f_u_k") and inputs.get("d"):
        out["M_u_k"] = yield_moment(inputs["f_u_k"], inputs["d"])
    return out


def _moisture_class(members):
    """The connection's moisture class: the worst of the members it joins, which is the *highest* number -- class 3 is the wettest and carries the smallest eta_w.

    Every member must carry one. Resolving a member against a position is where a blank class becomes a warning and a fallback (docs/domain/positions.md §7 -- an element that is not timber leaves the column empty); by the time it reaches here it is a number, or the calculation has no eta_w to apply and says so.
    """
    classes = [m.get("moisture_class") for m in members]
    if any(c is None for c in classes):
        _fail("dowel", "a member carries no moisture class -- SIA 265 Tabelle 4 needs one to give eta_w")
    return max(classes)


def _stiffness(inputs, result, spec, members):
    """K_ser per dowel and shear plane, and for the connection (SIA 265 Tabelle 25), with the slip of 6.2.1.3.

    Tabelle 25 is stated for Feuchteklasse 1; another class multiplies it by the *stiffness* column of Tabelle 4, which is not the column a resistance uses.

    ⚠️ **eta_w is applied to each member's K_ser, not to the connection's** (the engineer, v0.84: «il faut toujours multiplier le résultat avec eta_w»). The product is the same either way -- K_ser,Verb = n_tot · p · K_ser -- and this is where the report can *say* it: the formula Tabelle 25 states is printed with eta_w on its own line, and K_ser,Verb is then a count times a stiffness. The per-member values are unchanged in Feuchteklasse 1, which is the class the two workbook cases carry.

    The two tabulated coefficients travel with the answer (`c_0`, `c_90`), because the printed formula is composed from the very numbers the arithmetic used (docs/architecture/layout.md §11) and Tabelle 25 interpolates between them over alpha.
    """
    family = spec["family"]
    coefficients = sia265.kser_coefficients(family)
    exponents = sia265.table_25()["exponents"]
    eta_w_stiffness = sia265.eta_w(_moisture_class(members[:spec["members"]]), "stiffness")
    per_member = []
    for index, member in enumerate(members[:spec["members"]], start=1):
        value = sia265.kser(family, member["rho_k"], inputs["d"], member["alpha"]) * eta_w_stiffness
        per_member.append({"member": index, "K_ser": value, "alpha": member["alpha"]})
    governing = min(entry["K_ser"] for entry in per_member)
    return {
        "family": family,
        "per_member": per_member,
        "K_ser": governing,
        "eta_w": eta_w_stiffness,
        "c_0": coefficients["parallel"],
        "c_90": coefficients["perpendicular"],
        "exponents": exponents,
        "K_ser_Verb": governing * inputs["n_tot"] * result["p"],
        "slip": sia265.slip()["value"],
    }


# --- the dowel pattern against Tabelle 24 ------------------------------------

def pattern_spacings(fasteners, d, alpha):
    """The spacings a dowel pattern actually has, in mm, measured in the grain direction and across it.

    The coordinates are the detail schema's (docs/domain/detail-schemas.md §3.3decies): x to the right, z down. ⚠️ The grain is taken to run along x, which holds where the reference member is drawn along x -- every detail this project has -- and not on a detail drawn at an angle, whose spacings would have to be measured along the member's own axis. `alpha` is the angle between the force and that grain, so the *grain* direction is x whatever the force does -- Tabelle 24 measures against the grain, not against the force.

    Returns the smallest spacing found between two dowels in each direction, and the rows the pattern falls into, so the report can print what was measured beside what the norm asks for.
    """
    points = [(f["x"], f["z"]) for f in fasteners]
    if len(points) < 2:
        return {"parallel": None, "perpendicular": None, "pairs": 0}
    smallest_parallel = None
    smallest_perpendicular = None
    for i, (x1, z1) in enumerate(points):
        for x2, z2 in points[i + 1:]:
            dx, dz = abs(x2 - x1), abs(z2 - z1)
            # two dowels share a row across the grain when their x agree: their distance is then perpendicular
            if dx <= SAME_POINT:
                smallest_perpendicular = dz if smallest_perpendicular is None else min(smallest_perpendicular, dz)
            elif dz <= SAME_POINT:
                smallest_parallel = dx if smallest_parallel is None else min(smallest_parallel, dx)
            else:
                smallest_parallel = dx if smallest_parallel is None else min(smallest_parallel, dx)
                smallest_perpendicular = dz if smallest_perpendicular is None else min(smallest_perpendicular, dz)
    return {
        "parallel": smallest_parallel,
        "perpendicular": smallest_perpendicular,
        "pairs": len(points) * (len(points) - 1) // 2,
    }


def pattern_rows(fasteners, grain_angle=0.0, tolerance=1.0):
    """How many fasteners follow one another along a member's grain, and how far apart -- (n, a_1).

    The coordinates are the detail schema's, x to the right; `grain_angle` is the member's own grain from that x, so a member at 90 degrees has its rows counted across the drawing instead of along it. Fasteners whose distance across the grain agrees to `tolerance` mm are one row; n is the longest row and a_1 the smallest gap inside it.

    This is a *suggestion*, not the calculation's own answer. Which fasteners count as «hintereinander angeordnet» in the sense of SIA 265 6.1.4.2 is a judgement -- a staggered group is the obvious case where the drawing does not settle it -- so the source stores n and a_1 as entered, and this is what Woodcore offers and the migration filled in.
    """
    if len(fasteners) < 2:
        return (len(fasteners), None)
    radians = math.radians(grain_angle)
    along = math.cos(radians), math.sin(radians)
    rows = {}
    for f in fasteners:
        # distance along the grain, and across it -- the row a fastener belongs to
        u = f["x"] * along[0] + f["z"] * along[1]
        v = -f["x"] * along[1] + f["z"] * along[0]
        key = round(v / tolerance)
        rows.setdefault(key, []).append(u)
    longest = max(rows.values(), key=len)
    if len(longest) < 2:
        return (1, None)
    ordered = sorted(longest)
    gap = min(b - a for a, b in zip(ordered, ordered[1:]))
    return (len(longest), gap if gap > 0 else None)


def check_spacings(fasteners, d, alpha):
    """The dowel pattern against SIA 265 Tabelle 24, as rows the report prints and warnings the export carries.

    Only the dowel-to-dowel distances are measured: an edge distance depends on where the group sits in the member, which the drawing does not know. Those two rows are printed with their required value and nothing beside it.
    """
    required = sia265.dowel_spacings(d)
    actual = pattern_spacings(fasteners, d, alpha)
    rows, warnings = [], []
    for row_id, label in (("fastener", "von Stabdübel zu Stabdübel"),
                          ("loaded_edge", "vom beanspruchten Rand"),
                          ("unloaded_edge", "vom unbeanspruchten Rand")):
        entry = {"id": row_id, "label": label,
                 "parallel": required[row_id]["parallel"],
                 "perpendicular": required[row_id]["perpendicular"]}
        if row_id == "fastener":
            entry["actual_parallel"] = actual["parallel"]
            entry["actual_perpendicular"] = actual["perpendicular"]
            for direction, german in (("parallel", "in Faserrichtung"), ("perpendicular", "rechtwinklig zur Faser")):
                have = actual[direction]
                want = required[row_id][direction]
                entry["ok_" + direction] = None if have is None else have >= want - 1e-9
                if have is not None and have < want - 1e-9:
                    warnings.append(
                        "Mindestabstand %s unterschritten: %.1f mm vorhanden, %.0f mm verlangt (SIA 265 Tabelle 24). "
                        "Gleichung (88) gilt nur bei Einhaltung der Mindestabstände (6.2.1.1)."
                        % (german, have, want))
        rows.append(entry)
    return {"rows": rows, "actual": actual, "warnings": warnings}


def plate_bearing(plate):
    """The bearing of the steel plates on one dowel, SIA 263:2013 Tabelle 16 equation (76) capped by 6.2.5 -- a Stabdübel in a plate is a Bolzen (spec 2026-10-12-audit-issues-47-48-49, D-16) --, every coefficient read from calc/norms/sia263-2013-tab16-lochleibung.json.

    `plate` is {d, t, e1, e2, d0, p1, p2, count, grade} in mm: the dowel's diameter, the plate's thickness, its end distance in the force's direction (the smallest), its edge distance across it, the hole's diameter, the dowels' spacings along and across the force read off the drawing (None where the pattern has no second dowel that way), the number of plates a dowel bears on, and the plate's grade of SIA 263 Tabelle 1. Per plate F_b,Rd = min(0.85 · e1/d0 · f_u · d · t, 2.4 · f_u · d · t, 1.5 · f_y · d · t) / gamma_M2, with p1 − d0/2 for e1 where p1 < e1 + d0/2; per dowel, count times that. A result beside R_d, never folded into it: the engineer verifies it against the force on one dowel (D-13). e2 < 1.0 d0 or p2 < 2.0 d0 is outside (76)'s premise and warns."""
    t16 = sia263.bearing()
    gamma = t16["gamma_M2"]["value"]
    for key in ("d", "t", "e1", "e2", "d0"):
        if not plate.get(key) or plate[key] <= 0:
            _fail("plate", "%s = %r mm -- the plate's bearing reads it" % (key, plate.get(key)))
    if plate["d0"] < plate["d"]:
        _fail("plate", "d0 = %s mm is smaller than the dowel's d = %s mm" % (plate["d0"], plate["d"]))
    steel = sia263.steel(plate["grade"], plate["t"])
    d, t, d0 = plate["d"], plate["t"], plate["d0"]
    e1 = plate["e1"]
    p1 = plate.get("p1")
    tight = p1 is not None and p1 < e1 + d0 / 2
    e1_eff = p1 - d0 / 2 if tight else e1
    f_76 = t16["factor"] * e1_eff / d0 * steel["f_u"] * d * t / gamma
    f_max = t16["limit"] * steel["f_u"] * d * t / gamma
    f_pin = t16["pin"]["factor"] * steel["f_y"] * d * t / gamma
    per_plate = min(f_76, f_max, f_pin)
    warnings = []
    if plate["e2"] < t16["e2_min"] * d0:
        warnings.append("Lochleibung der Bleche: $e_2$ = %s mm ist kleiner als %s · $d_0$ = %s mm, ausserhalb der Voraussetzung von SIA 263 Tabelle 16, Gleichung (76)."
                        % (_math(plate["e2"]), _math(t16["e2_min"]), _math(t16["e2_min"] * d0)))
    if plate.get("p2") is not None and plate["p2"] < t16["p2_min"] * d0:
        warnings.append("Lochleibung der Bleche: $p_2$ = %s mm ist kleiner als %s · $d_0$ = %s mm, ausserhalb der Voraussetzung von SIA 263 Tabelle 16, Gleichung (76)."
                        % (_math(plate["p2"]), _math(t16["p2_min"]), _math(t16["p2_min"] * d0)))
    return {"grade": plate["grade"], "f_u": steel["f_u"], "f_y": steel["f_y"], "gamma_M2": gamma, "d": d, "t": t, "e1": e1, "e2": plate["e2"],
            "d0": d0, "p1": p1, "p2": plate.get("p2"), "tight": tight, "e1_eff": e1_eff, "count": plate["count"],
            "F_76": f_76 / 1000, "F_max": f_max / 1000, "F_pin": f_pin / 1000, "F_plate": per_plate / 1000,
            "F_b_Rd": plate["count"] * per_plate / 1000, "warnings": warnings}


def connection_length(fasteners, d, rows_parallel, rows_perpendicular):
    """The minimum length a connection needs in each direction: the two end distances plus the dowel spacings between them (the workbook's own «min. Länge der Verbindung»)."""
    required = sia265.dowel_spacings(d)
    out = {}
    for direction, count in (("parallel", rows_parallel), ("perpendicular", rows_perpendicular)):
        if not count or count < 1:
            out[direction] = None
            continue
        out[direction] = (required["loaded_edge"][direction]
                          + required["fastener"][direction] * (count - 1)
                          + required["unloaded_edge"][direction])
    return out


# --- the report record -------------------------------------------------------
# What show-calc("connector", id) walks, and what show-connector-resistance lays out at its three
# levels. The order the vars are added in *is* the level-3 layout (docs/typst/api-conventions.md §10bis), so it is
# the order an engineer checks the calculation in: the inputs, then f_h,k per member, then the
# quantities equation (88) is built from, then the answer.

NORM = "SIA 265"
SOURCE = "python:domains/dowel.py"

# Where a value the engineer typed in Woodcore comes from. A diameter is not computed by this
# module and saying `python:` of it would be false (docs/architecture/principles.md §2 rule 5). `katalog:` until v0.96,
# which an export written before carries; nothing reads the prefix back.
def _entered(cid):
    return "woodcore:connectors/%s.json" % cid


def _norm_source(table):
    return "norm:%s, %s" % (sia265.edition(), table)


def _column(label, kind, unit="", label_math=None):
    entry = {"label": label, "kind": kind, "unit": unit}
    if label_math:
        entry["label_math"] = label_math
    return entry

def _math(value):
    """A coefficient as Typst math source writes it: 0.3, -0.1 in parentheses, since a bare minus after a caret would bind to nothing."""
    text = _fmt(value)
    return "(%s)" % text if text.startswith("-") else text


def _multiple(factor, floor):
    """A distance as Tabelle 24 states it, in multiples of d -- «7 d», and the loaded end's «7 d (min. 80 mm)» -- as prose carrying its math between dollars, which render-table and Woodcore both set."""
    text = "$%s d$" % _fmt(factor)
    return text if floor is None else "%s (min. %s mm)" % (text, _fmt(floor))


def _spacing_table(d, lengths):
    """SIA 265 Tabelle 24, laid out as `Verbindung.xlsm` lays it out ('Stabdübel (Holz-Holz)'!A47:E53): one row per distance, its value in mm and its multiple of d **in the grain direction** and **across it**, and the minimum length of the connection under them.

    Until v0.77 it was one row per distance *and* direction, with what the drawing «had» beside what the norm asks and a check mark -- the smallest gap between two markers along the schema's x and z, which holds only where the member is drawn along x. The engineer asked for the classeur's table and could not tell how the comparison was made, so it left the table; the export still warns when a gap between two dowels is below Tabelle 24 (check_spacings).

    ⚠️ **The head of the first column names the diameter the multiples are of** (the engineer, v0.84): every cell of this table is a multiple of d, and the table said nowhere which d. It is written as a one-column `group`, so it is set on the group line where the two directions are named -- the cell that was empty.

    Equation (88) holds only where these distances are kept (6.2.1.1), so the table is on the page at every level -- which is why its level is 1.
    """
    required = sia265.dowel_spacings(d)
    group_par, group_perp = "in Faserrichtung", "senkrecht zur Faserrichtung"
    rows = []
    for spec in sia265.table_24()["rows"]:
        row = [spec["label"]]
        for direction in ("parallel", "perpendicular"):
            row += [required[spec["id"]][direction], _multiple(spec[direction]["factor"], spec[direction]["min"])]
        rows.append(row)
    # an empty numeric cell is written as "" and never as null: render-table formats a number column with fmt-decimals, which refuses none (the project's own convention for a blank)
    totals = []
    if lengths.get("parallel") or lengths.get("perpendicular"):
        totals = [["min. Länge der Verbindung", lengths.get("parallel") or "", "", lengths.get("perpendicular") or "", ""]]
    return {
        "title": "Minimale Abstände",
        "level": 1,
        "place": "below",
        "norm": NORM,
        "norm_ref": "6.2.1.2",
        "note": ("Tabelle 24. Gleichung (88) gilt nur bei Einhaltung dieser Abstände (6.2.1.1). "
                 "Die Mindestlänge folgt aus der Anzahl Verbindungsmittel in und quer zur Faserrichtung."),
        "columns": [
            dict(_column("Abstand", "wide"), group="$d$ = %s mm" % _fmt(d)),
            dict(_column("", "number", "mm"), group=group_par),
            dict(_column("", "text"), group=group_par),
            dict(_column("", "number", "mm"), group=group_perp),
            dict(_column("", "text"), group=group_perp),
        ],
        "rows": rows,
        "totals": totals,
    }


def _k_beta_figures(result):
    """SIA 265 Figur 45, one line per thickness -- the plate the curves are set on, and nothing else.

    Until v0.84 this was a table of the corners k_beta is interpolated between, with the curves hanging off it. The engineer asked for the formulas of Tabellen 45/46 in the report instead of a table of the numbers they produce, so the corners are `record`'s own steps now and what is left here is the *figures*: a `tables` entry carrying a title, a note and its `curves`, and no grid at all. `connector.figures` draws each curve and replaces `curves` by `figures`; `render-table` sets a plate with no columns as its title, its figures and its note (docs/domain/calculation-domains.md §3.3, docs/domain/connectors.md §3.3nonies).
    """
    curves = []

    def curve(index, label, entry):
        # The lower corner at the origin is the Mittelholz's dashed line (equations (121), (128), (131)); a lower corner of its own is a Seitenholz's.
        curves.append({"index": index, "label": label, "role": "Mittelholz" if entry["t_1"] <= 0 else "Seitenholz",
                       "t": entry["t"], "t_1": entry["t_1"], "k_1": entry["k_1"],
                       "t_2": entry["t_2"], "k_2": entry["k_2"], "k_beta": entry["k_beta"]})

    if "corners" in result:
        for corner in result["corners"]:
            curve(corner["member"], "Bauteil %d" % corner["member"], corner)
        note = ("Zwischenwerte werden linear interpoliert (Figur 45). Massgebend ist der kleinere Wert; "
                "$beta_f = f_(h,2,k) \\/ f_(h,1,k)$.")
        ref = "A.1.1"
    else:
        for plane in result["planes"]:
            # outer plates carry one unlettered plane, whose `plane` is the word itself
            curve(1 if plane["plane"] == "A" else 2,
                  "Scherfuge %s" % plane["plane"] if plane["plane"] in ("A", "B") else "Scherfuge", plane)
        note = ("Zwischenwerte werden linear interpoliert (Figur 45). Die vorhandene Anzahl Scherfugen wird "
                "mit dem zugehörigen Hilfswert berücksichtigt: $p dot k_beta = p_A dot k_(beta,1) + "
                "p_B dot k_(beta,2)$ (6.2.1.1).")
        ref = "A.1.2"
    return {
        "title": "Hilfswert $k_beta$",
        "level": 3,
        "place": "below",
        "norm": NORM,
        "norm_ref": ref,
        "note": note,
        "curves": curves,
        "columns": [],
        "rows": [],
    }


# --- the k_beta corners as Tabellen 45 and 46 write them ----------------------
# The engineer, v0.84: «au lieu de faire un tableau qui n'affiche que les résultats, reprends les
# formules ... et écris-les dans le rapport». So each corner is a step carrying the table's own formula,
# composed from the very JSON factors the arithmetic used -- never a second transcription of the norm
# (docs/architecture/layout.md §11). Which row of the table a corner was read off travels on it as `shape`.

def _timber_bracket(shape):
    """The bracket of Tabelle 45: member 1's, member 2's as a Seitenholz, or the Mittelholz's own factor."""
    if shape == "seitenholz_1":
        return "(sqrt(beta_f \\/ (1 + beta_f)) + 1)"
    if shape == "seitenholz_2":
        return "(sqrt(1 \\/ (1 + beta_f)) + 1)"
    return "1 \\/ sqrt(1 + beta_f)"


def _interpolation(k_sym, entry, names):
    """The branch of Figur 45 this thickness actually falls in, as its own formula and its operands.

    A.1.2: «Für kleinere Holzdicken und Zwischenwerte sind die Hilfswerte linear zu interpolieren». Which of the three branches applied is *printed* rather than described -- the rule `show-calc` already follows for the snow load's own conditional formula (docs/domain/loads.md §3.3bis).
    """
    t, t_1, t_2 = entry["t"], entry["t_1"], entry["t_2"]
    t_sym, t_1_sym, t_2_sym = names["t_sym"], names["t_1_sym"], names["t_2_sym"]
    k_1_sym, k_2_sym = names["k_1_sym"], names["k_2_sym"]
    if t >= t_2:
        return "%s = %s" % (k_sym, k_2_sym), [names["k_2"]]
    if t_1 > 0 and t >= t_1:
        return ("%s = %s + (%s - %s) \\/ (%s - %s) dot (%s - %s)"
                % (k_sym, k_1_sym, t_sym, t_1_sym, t_2_sym, t_1_sym, k_2_sym, k_1_sym),
                [names["k_1"], names["t"], names["t_1"], names["t_2"], names["k_2"]])
    if t_1 > 0:
        return "%s = %s \\/ %s dot %s" % (k_sym, t_sym, t_1_sym, k_1_sym), [names["t"], names["t_1"], names["k_1"]]
    return "%s = %s \\/ %s dot %s" % (k_sym, t_sym, t_2_sym, k_2_sym), [names["t"], names["t_2"], names["k_2"]]


def record(cid, result, timber, spacings=None, lengths=None):
    """One dowel connection as the {results, tables, vars, steps, checks} record every calculation has.

    `result` is analyse()'s output and `timber` the resolved timber members it was given, so nothing is
    computed twice and the record cannot disagree with the numbers Woodcore previewed. `spacings` is
    check_spacings()' output and `lengths` connection_length()'s, when the fastener pattern is known --
    the table of Tabelle 24 is printed then, the fasteners' own positions no longer (v0.77: «Lage der
    Verbindungsmittel» left the report at the engineer's request, the pattern figure showing them).

    **The order the vars are added in *is* the level-3 layout** (docs/typst/api-conventions.md §10bis), so it is the
    order an engineer checks the calculation in. Since v0.84 that order is the engineer's own, and three
    things follow from it. Every short formula is `inline`: its letters, its numbers and its answer on
    one row. The three tables that held nothing but results -- Tabelle 22's embedment strengths,
    Tabellen 45/46's corners, Tabelle 25's stiffnesses -- are gone, and each of those tables' formulas is
    written out as a step instead. And a **run of single values is one row**: the inputs, the two
    members' material, and the factors of equation (88), each a `group` printed semicolon-separated.

    ⚠️ The formulas written out are those of Tabellen **45 and 46**, not of Tabelle 23. Tabelle 23 is the
    *simplified* k_beta the norm offers as an alternative in 6.2.1.1, and this module has computed the
    more accurate Anhang A form since v0.68 at the engineer's own choice -- so printing Tabelle 23 would
    put formulas on the page that do not produce the numbers beside them, which is the one thing this
    display layer exists to prevent.

    `checks` is empty and stays empty: there is no design force here. The report states F_d and the
    verification itself, with #verify reading var-of("connector", id, "R_d") -- which is the engineer's
    own decision (docs/domain/connectors.md §3.3nonies).
    """
    calc = engine.Calculation()
    entered = _entered(cid)
    steel = "planes" in result
    outer_plates = result["assembly"] == "Stahl-Holz, Bleche aussen"

    def add(name, value, unit, symbol, label, src=SOURCE, ref="6.2.1.1",
            description=None, group=None, group_label=None, keep=None, heading=None):
        calc.add_var(name, value=value, unit=unit, symbol=symbol, label=label,
                     source=src, norm=NORM, norm_ref=ref, description=description,
                     group=group, group_label=group_label, keep=keep, heading=heading)

    def add_step(name, produces, uses, formula, ref="6.2.1.1", description=None,
                 inline=True, bold=None):
        calc.add_step(name=name, result=produces, uses=list(uses),
                      norm=NORM, norm_ref=ref, formula=formula,
                      description=description, inline=inline, bold=bold)

    # --- what the engineer entered, on one row
    # «Anzahl Verbinder» is the classeur's own wording ('Stabdübel (Holz-Holz)'!A29) and is deliberately
    # not «Anzahl Verbindungsmittel», which connection.py uses for the fasteners of a polar moment: two
    # labels for two counts, so a glossary keyed by the German cannot conflate them.
    add("d", result["d"], "mm", "d", "Durchmesser", entered, group="input", keep=True)
    add("n_tot", result["n_tot"], "", 'n_"tot"', "Anzahl Verbinder", entered, group="input", keep=True)
    # f_u,k is the engineer's, or the f_u of the dowel's steel grade in SIA 263 Tabelle 1 (SN EN 14592 Tabelle G.9 giving none) -- said then, as the grade and the table it was read in (D-20)
    grade = result.get("dowel_steel") or ""
    if grade:
        calc.add_var("f_u_k", value=result["f_u_k"], unit="N/mm²", symbol="f_(u,k)", label="char. Zugfestigkeit des Stabdübels",
                     source="norm:%s, Tabelle 1" % sia263.edition(), norm="SIA 263", norm_ref="Tabelle 1", description="Stahl %s" % grade, group="input", keep=True)
    else:
        add("f_u_k", result["f_u_k"], "N/mm²", "f_(u,k)",
            "char. Zugfestigkeit des Stabdübels", entered, "6.1.4.4", group="input", keep=True)

    # --- per timber member: what it is made of, on one row, under the heading the book gives that block
    # «Charakteristische Lochleibungsfestigkeiten für C24:», Bemessungsbeispiele zur SIA 265 p. 291.
    # Where the members do not share one class there is no «für C24» to write, and the block is named
    # without it -- the same sentence, with its hole and the words around it taken out (section 4bis).
    grades = [member.get("grade", "") for member in timber]
    one_grade = grades[0] if grades and grades[0] and all(g == grades[0] for g in grades) else ""
    embedment_heading = ("Charakteristische Lochleibungsfestigkeiten für %s" % one_grade if one_grade
                         else "Charakteristische Lochleibungsfestigkeiten")

    # What each piece is called wherever the layout names one: «Bauteil 1 – Seitenholz», the very form
    # the Figur 45 plates are captioned with. The corners already know which is which -- a Mittelholz's
    # lower corner sits at the origin -- and where the role says nothing that the number does not (a
    # einschnittig joint, whose two pieces are both Seitenhölzer) the number stands on its own.
    roles = {c["member"]: ("Mittelholz" if c["shape"] == "mittelholz" else "Seitenholz")
             for c in result.get("corners", [])}
    named = len(set(roles.values())) == len(roles) == len(timber)

    def member_label(index):
        return "Bauteil %d — %s" % (index, roles[index]) if named else "Bauteil %d" % index

    for index, member in enumerate(timber, start=1):
        # Where this member's strength class -- and so its density -- came from, said as a footnote on
        # the value itself. It was the note under the Lochleibungsfestigkeit table until v0.84, and it
        # belongs here: it is one sentence about one var, translated on its own (periodic audit 260916,
        # AUD-3-7 -- one string with every piece's provenance in a hole came out half German).
        provenance = member.get("provenance")
        add("rho_k_%d" % index, member["rho_k"], "kg/m³", "rho_(k,%d)" % index,
            "Rohdichte", _norm_source(member.get("table", "Tabelle 8")),
            member.get("norm_ref", "3.3.2.1"),
            description=("Bauteil %d: %s." % (index, provenance)) if provenance else None,
            group="material", group_label=member_label(index), keep=True,
            heading=embedment_heading if index == 1 else None)
        # alpha keeps no row of its own: it is an operand of f_h,alpha,k and of k_red, and both
        # substituted formulas show it where it acts (docs/typst/api-conventions.md §10bis).
        add("alpha_%d" % index, member["alpha"], "°", "alpha_%d" % index,
            "Winkel zwischen der Kraft- und Faserrichtung der Holzteile", entered, "6.1.4.2",
            group="material")

    # --- the Lochleibungsfestigkeit, Tabelle 22 written out (the engineer, v0.84)
    t22 = sia265.embedment()
    for index, (member, strength) in enumerate(zip(timber, result["strengths"]), start=1):
        tag = "Bauteil %d" % index
        if member["predrilled"]:
            add("f_h_0_%d" % index, strength["f_h_0_k"], "N/mm²", "f_(h,0,%d)" % index,
                "Lochleibungsfestigkeit parallel zur Faser", SOURCE, "6.1.4.3")
            add_step(
                name="Lochleibungsfestigkeit parallel zur Faser %s" % tag,
                produces="f_h_0_%d" % index, uses=["d", "rho_k_%d" % index], ref="6.1.4.3",
                formula="f_(h,0,%d) = %s dot (1 - %s dot d) dot rho_(k,%d)"
                        % (index, _math(t22["factor"]), _math(t22["predrilled_slope"]), index))
            add("f_h_90_%d" % index, strength["f_h_90_k"], "N/mm²", "f_(h,90,%d)" % index,
                "Lochleibungsfestigkeit rechtwinklig zur Faser", SOURCE, "6.1.4.3")
            add_step(
                name="Lochleibungsfestigkeit rechtwinklig zur Faser %s" % tag,
                produces="f_h_90_%d" % index, uses=["f_h_0_%d" % index, "d"], ref="6.1.4.3",
                formula="f_(h,90,%d) = f_(h,0,%d) \\/ (%s + %s dot d)"
                        % (index, index, _math(t22["f_90_divisor"][member["species"]]),
                           _math(t22["f_90_diameter_term"])))
            add("f_h_%d" % index, strength["f_h_alpha_k"], "N/mm²", "f_(h,%d,k)" % index,
                "Lochleibungsfestigkeit", SOURCE, "6.1.4.3")
            add_step(
                name="Lochleibungsfestigkeit %s" % tag, produces="f_h_%d" % index,
                uses=["f_h_90_%d" % index, "f_h_0_%d" % index, "alpha_%d" % index], ref="6.1.4.3",
                formula="f_(h,%d,k) = f_(h,90,%d) + (f_(h,0,%d) - f_(h,90,%d)) dot (90 - alpha_%d) \\/ 90"
                        % (index, index, index, index, index),
                description="Tabelle 22, zwischen den beiden Faserrichtungen linear interpoliert.")
        else:
            # Tabelle 22's undrilled row gives one value for both directions, so the angle does not enter
            # and there is nothing to interpolate: one line rather than three.
            add("f_h_%d" % index, strength["f_h_alpha_k"], "N/mm²", "f_(h,%d,k)" % index,
                "Lochleibungsfestigkeit", SOURCE, "6.1.4.3")
            add_step(
                name="Lochleibungsfestigkeit %s" % tag, produces="f_h_%d" % index,
                uses=["d", "rho_k_%d" % index], ref="6.1.4.3",
                formula="f_(h,%d,k) = %s dot d^%s dot rho_(k,%d)"
                        % (index, _math(t22["factor"]), _math(t22["undrilled_exponent"]), index),
                description="Tabelle 22, nicht vorgebohrt: die Werte parallel und rechtwinklig zur Faser "
                            "sind gleich, der Winkel geht nicht ein.")

    # --- the ratio of the embedment strengths, a block of its own in the book
    if not steel:
        t45 = sia265.table_45()
        side, middle = t45["seitenholz"], t45["mittelholz"]
        exponent = _math(t45["t_exponent"])
        add("beta_f", result["beta_f"], "", "beta_f",
            "Verhältnis der Lochleibungsfestigkeiten", SOURCE, "A.1.1",
            heading="Verhältnis der Lochleibungsfestigkeiten")
        add_step(name="Verhältnis der Lochleibungsfestigkeiten", produces="beta_f",
                 uses=["f_h_2", "f_h_1"], ref="A.1.1", formula="beta_f = f_(h,2,k) \\/ f_(h,1,k)")

    # --- what each piece is thick, on one row under the book's own «Holzdicken:»
    # It stood with the material until v0.84, where the two read as one undifferentiated row; the book
    # gives the thicknesses a block of their own, between the ratio and the thicknesses required.
    if steel:
        # ⚠️ A Stahl-Holz joint enters ONE member, whose thickness is the whole piece: the slots are
        # what divide it into a side and a middle timber, which steel_geometry computes (t_1, t_2).
        geometry = result["geometry"]
        if not outer_plates:
            add("b", timber[0]["t"], "mm", "b", "Bauteildicke", entered, "A.1.2",
                group="thickness", keep=True, heading="Holzdicken")
        add("t_1", geometry["t_1"], "mm", "t_1",
            "Holzdicke" if outer_plates else "Holzdicke Seitenholz",
            entered if outer_plates else SOURCE, "A.1.2",
            group="thickness", group_label=None if outer_plates else "Seitenholz", keep=True,
            heading="Holzdicken" if outer_plates else None)
        if geometry.get("t_2"):
            add("t_2", geometry["t_2"], "mm", "t_2", "Holzdicke Mittelholz", SOURCE, "A.1.2",
                group="thickness", group_label="Mittelholz", keep=True)
    else:
        for index, member in enumerate(timber, start=1):
            add("t_%d" % index, member["t"], "mm", "t_%d" % index, "Holzdicke", entered, "A.1.2",
                group="thickness", group_label=member_label(index), keep=True,
                heading="Holzdicken" if index == 1 else None)

    # --- k_beta: the corners of Tabelle 45 resp. 46, each as the table's own formula, under the
    # heading the book gives that block («Erforderliche Holzdicken t_i,erf und Hilfswert k_beta»).
    # ⚠️ The formulas written out are Anhang A's and not Tabelle 23's -- see this function's docstring.
    if not steel:
        add("k_beta_max", result["k_beta_max"], "", 'k_(beta,"max")',
            "Grösstwert des Hilfswerts", SOURCE, "A.1.1",
            heading="Erforderliche Holzdicken und Hilfswert $k_beta$")
        add_step(name="Grösstwert des Hilfswerts", produces="k_beta_max", uses=["beta_f"],
                 ref="A.1.1",
                 formula='k_(beta,"max") = sqrt(%s dot beta_f \\/ (1 + beta_f))'
                         % _math(t45["k_max_numerator"]))

        for corner in result["corners"]:
            i = corner["member"]
            tag = "Bauteil %d" % i
            bracket = _timber_bracket(corner["shape"])
            base = "sqrt(f_(u,k) \\/ f_(h,%d,k)) dot d^%s" % (i, exponent)
            operands = ["beta_f", "f_u_k", "f_h_%d" % i, "d"]
            names = {"t": "t_%d" % i, "t_1": "t_c_%d_1" % i, "t_2": "t_c_%d_2" % i,
                     "k_1": "k_beta_%d_1" % i, "k_2": "k_beta_%d_2" % i,
                     "t_sym": "t_%d" % i, "t_1_sym": "t_(%d,1)" % i, "t_2_sym": "t_(%d,2)" % i,
                     "k_1_sym": "k_(beta,%d,1)" % i, "k_2_sym": "k_(beta,%d,2)" % i}
            if corner["shape"] != "mittelholz":
                # The piece this run is about, on a line of its own, as the book sets it («Seitenhölzer»,
                # «Mittelholz»): the symbols carry the member's number, and this is what adds the word.
                add("t_c_%d_1" % i, corner["t_1"], "mm", names["t_1_sym"],
                    "Holzdicke für den unteren Eckwert", SOURCE, "A.1.1",
                    heading=member_label(i))
                add_step(name="Holzdicke %s, unterer Eckwert" % tag, produces="t_c_%d_1" % i,
                         uses=operands, ref="A.1.1",
                         formula="%s = %s dot %s dot %s"
                                 % (names["t_1_sym"], _math(side["t_1_factor"]), bracket, base))
                add("k_beta_%d_1" % i, corner["k_1"], "", names["k_1_sym"],
                    "Hilfswert zum unteren Eckwert", SOURCE, "A.1.1")
                add_step(name="Hilfswert %s, unterer Eckwert" % tag,
                         produces="k_beta_%d_1" % i, uses=["k_beta_max"], ref="A.1.1",
                         formula='%s = %s dot k_(beta,"max")'
                                 % (names["k_1_sym"], _math(side["k_1_share"])))
            factor = middle["t_2_factor"] if corner["shape"] == "mittelholz" else side["t_2_factor"]
            add("t_c_%d_2" % i, corner["t_2"], "mm", names["t_2_sym"],
                "Holzdicke für den oberen Eckwert", SOURCE, "A.1.1",
                heading=member_label(i) if corner["shape"] == "mittelholz" else None)
            add_step(name="Holzdicke %s, oberer Eckwert" % tag, produces="t_c_%d_2" % i,
                     uses=operands, ref="A.1.1",
                     formula="%s = %s dot %s dot %s" % (names["t_2_sym"], _math(factor), bracket, base))
            add("k_beta_%d_2" % i, corner["k_2"], "", names["k_2_sym"],
                "Hilfswert zum oberen Eckwert", SOURCE, "A.1.1")
            add_step(name="Hilfswert %s, oberer Eckwert" % tag, produces="k_beta_%d_2" % i,
                     uses=["k_beta_max"], ref="A.1.1",
                     formula='%s = k_(beta,"max")' % names["k_2_sym"])
            add("k_beta_%d" % i, corner["k_beta"], "", "k_(beta,%d)" % i,
                "Hilfswert zur Scherfuge", SOURCE, "A.1.1")
            formula, uses = _interpolation("k_(beta,%d)" % i, corner, names)
            add_step(name="Hilfswert %s" % tag, produces="k_beta_%d" % i, uses=uses,
                     ref="A.1.1", formula=formula,
                     description="Zwischenwerte werden linear interpoliert (Figur 45)." if i == 1 else None)
    else:
        t46 = sia265.table_46()
        exponent = _math(t46["t_exponent"])
        base = "sqrt(f_(u,k) \\/ f_(h,1,k)) dot d^%s" % exponent
        operands = ["f_u_k", "f_h_1", "d"]
        for order, plane in enumerate(result["planes"], start=1):
            spec = t46[plane["shape"]]
            lettered = plane["plane"] in ("A", "B")
            letter = plane["plane"] if lettered else "1"
            tag = "Scherfuge %s" % plane["plane"] if lettered else "Scherfuge"
            thickness = "t_2" if plane["plane"] == "B" else "t_1"
            names = {"t": thickness, "t_1": "t_c_%d_1" % order, "t_2": "t_c_%d_2" % order,
                     "k_1": "k_beta_%d_1" % order, "k_2": "k_beta_%d_2" % order,
                     "t_sym": thickness, "t_1_sym": "t_(%s,1)" % letter, "t_2_sym": "t_(%s,2)" % letter,
                     "k_1_sym": "k_(beta,%s,1)" % letter, "k_2_sym": "k_(beta,%s,2)" % letter}
            # No sub-heading per shear plane, unlike the timber members': the letter a steel joint's
            # planes are told apart by is in every symbol of the run (t_(A,1), k_(beta,A,1)), where a
            # member's own word -- Seitenholz, Mittelholz -- is in none of its.
            block_heading = "Erforderliche Holzdicken und Hilfswert $k_beta$" if order == 1 else None
            if spec["t_1_factor"]:
                add("t_c_%d_1" % order, plane["t_1"], "mm", names["t_1_sym"],
                    "Holzdicke für den unteren Eckwert", SOURCE, "A.1.2",
                    heading=block_heading)
                block_heading = None
                add_step(name="Holzdicke %s, unterer Eckwert" % tag,
                         produces="t_c_%d_1" % order, uses=operands, ref="A.1.2",
                         formula="%s = %s dot %s" % (names["t_1_sym"], _math(spec["t_1_factor"]), base))
                # The lower corner's own k_beta is the table's own number, not a formula: it is stated
                # beside the upper one rather than on a line of its own.
                add("k_beta_%d_1" % order, plane["k_1"], "", names["k_1_sym"],
                    "Hilfswert zum unteren Eckwert", _norm_source("Tabelle 46"), "A.1.2",
                    group="corners_%d" % order, group_label=tag, keep=True)
            add("t_c_%d_2" % order, plane["t_2"], "mm", names["t_2_sym"],
                "Holzdicke für den oberen Eckwert", SOURCE, "A.1.2",
                heading=block_heading)
            add_step(name="Holzdicke %s, oberer Eckwert" % tag, produces="t_c_%d_2" % order,
                     uses=operands, ref="A.1.2",
                     formula="%s = %s dot %s" % (names["t_2_sym"], _math(spec["t_2_factor"]), base))
            add("k_beta_%d_2" % order, plane["k_2"], "", names["k_2_sym"],
                "Hilfswert zum oberen Eckwert", _norm_source("Tabelle 46"), "A.1.2",
                group="corners_%d" % order,
                group_label=None if spec["t_1_factor"] else tag, keep=True)
            if "k_2_root" in spec:
                # equation (128)'s «sqrt 2», written as the root the norm prints
                add_step(name="Hilfswert %s, oberer Eckwert" % tag,
                         produces="k_beta_%d_2" % order, uses=[], ref="A.1.2",
                         formula="%s = sqrt(%s)" % (names["k_2_sym"], _math(spec["k_2_root"])))
            add("k_beta_%d" % order, plane["k_beta"], "", "k_(beta,%s)" % letter,
                "Hilfswert zur Scherfuge", SOURCE, "A.1.2")
            formula, uses = _interpolation("k_(beta,%s)" % letter, plane, names)
            add_step(name="Hilfswert %s" % tag, produces="k_beta_%d" % order, uses=uses,
                     ref="A.1.2", formula=formula,
                     description="Zwischenwerte werden linear interpoliert (Figur 45)." if order == 1 else None)

    # --- k_red per member, the smallest retained
    red = sia265.reduction()
    for entry in result["reductions"]:
        index = entry["member"]
        # n and a_1 keep no row: both are operands of k_red's own formula, which shows them where they
        # act. The heading therefore hangs on k_red itself -- a var that prints nothing announces
        # nothing, which is the rule and the trap (calc/engine.py, `heading`).
        add("n_%d" % index, entry["n"], "", "n_%d" % index,
            "Anzahl der in Faserrichtung des Holzes hintereinander angeordneten Verbindungsmittel",
            entered, "6.1.4.2")
        if entry["a_1"]:
            add("a_1_%d" % index, entry["a_1"], "mm", "a_(1,%d)" % index,
                "Abstand der Verbindungsmittel untereinander in Faserrichtung", entered, "6.1.4.2")
        add("k_red_%d" % index, entry["k_red"], "", "k_(\"red\",%d)" % index,
            "Reduktionsbeiwert", SOURCE, "6.1.4.2",
            heading="Reduktionsbeiwert" if index == 1 else None)
        if entry["n"] > 1:
            add_step(
                name="Reduktionsbeiwert %s" % ("Bauteil %d" % index),
                produces="k_red_%d" % index,
                uses=["n_%d" % index, "a_1_%d" % index, "d", "alpha_%d" % index], ref="6.1.4.2",
                formula="k_(\"red\",%d) = n_%d^%s dot (a_(1,%d) \\/ (%s dot d))^%s dot (90 - alpha_%d) \\/ 90 + alpha_%d \\/ 90"
                        % (index, index, _math(red["n_exponent"]), index, _math(red["spacing_reference"]),
                           _math(red["spacing_exponent"]), index, index),
                # said once, on the first member's step: the same note against every member reads as
                # several different notes, which is the rule show-live-load states for its own footnotes.
                # %.1f and not _fmt: the German sentence is a glossary key, and it reads «1.0» (docs/typst/language.md §4bis)
                description=("Gleichung (86), jedoch $k_\"red\" <= %.1f$. Bei einem einzelnen "
                             "Verbindungsmittel in Faserrichtung ist $k_\"red\" = %.1f$ (Tabelle 21)."
                             % (red["maximum"], red["single_fastener"]))
                if index == 1 else None)

    # --- the yield moment, which only equation (88) reads: it stands where the book puts it, with the
    # resistance and not before k_beta, none of whose formulas uses it.
    add("M_u_k", result["M_u_k"], "Nmm", "M_(u,k)", "char. Fliessmoment des Stabdübels",
        SOURCE, "6.1.4.4", heading="Fliessmoment")
    moment = sia265.yield_moment()
    add_step(name="Fliessmoment", produces="M_u_k", uses=["f_u_k", "d"], ref="6.1.4.4",
             formula="M_(u,k) = %s dot f_(u,k) dot d^%s"
                     % (_math(moment["factor"]), _math(moment["exponent"])))

    # --- the factors of equation (88), on one row (the engineer, v0.84): each carries `keep`, because
    # every one of them is an operand of some step and would otherwise be absorbed into its formula.
    add("k_beta", result["k_beta"], "", "k_beta", "Hilfswert zur Scherfuge", SOURCE, "A.1.1",
        description="Massgebend ist der kleinste Hilfswert der beteiligten Holzteile "
                    "(Tabellen 45 und 46, zwischen den Eckwerten linear interpoliert).",
        group="factors", keep=True, heading="Bemessungswert des Tragwiderstands")
    add("p", result["p"], "", "p", "Anzahl Scherfugen", SOURCE, group="factors", keep=True)
    add("p_k_beta", result["p_k_beta"], "", "(p dot k_beta)",
        "Scherfugen mit ihren Hilfswerten", SOURCE,
        description="Bei mehrschnittigen Stahl-Holz-Verbindungen wird die vorhandene Anzahl Scherfugen "
                    "mit dem zugehörigen Hilfswert berücksichtigt: $p dot k_beta = p_A dot k_(beta,1) + p_B dot k_(beta,2)$."
        if steel else None,
        group="factors", keep=True)
    add("k_red", result["k_red"], "", 'k_"red"', "Massgebender Reduktionsbeiwert", SOURCE, "6.1.4.2",
        description="Bei unterschiedlichen Winkeln ist $k_\"red\"$ für alle Holzteile einzeln zu bestimmen und "
                    "der kleinste Wert einzusetzen.",
        group="factors", keep=True)
    for entry in result["reductions"]:
        index = entry["member"]
        # n_quer enters no equation -- it is the count across the grain the rows imply, which the
        # engineer checks the drawing against -- so it is stated beside the factors and never multiplied by.
        add("n_quer_%d" % index, entry["n_quer"], "", 'n_("quer",%d)' % index,
            "Anzahl Verbindungsmittel quer zur Faserrichtung", SOURCE, "6.1.4.2",
            description="$n_\"quer\" = n_\"tot\" \\/ n$, aufgerundet." if index == 1 else None,
            group="factors", keep=True)
    add("k_alpha", result["k_alpha"], "", "k_alpha", "Beiwert der Tragwiderstandsgleichung",
        _norm_source("Ziffer 6.2.1.1"), "6.2.1.1", group="factors", keep=True)
    add("eta_w", result["eta_w"], "", "eta_w", "Umrechnungsfaktor Holzfeuchte",
        _norm_source("Tabelle 4"), "3.2.1.3",
        description="Feuchteklasse %d." % result["moisture_class"], group="factors", keep=True)
    add("eta_t", result["eta_t"], "", "eta_t", "Umrechnungsfaktor Einwirkungsdauer",
        _norm_source("Ziffer 2.2.6"), "2.2.6",
        description="Stossartige Einwirkung (Erdbeben, Anprall)." if result["eta_t"] != 1 else None,
        group="factors", keep=True)

    # --- the answer: ONE fastener first, then the connection (the engineer, v0.84)
    add("R_d", result["R_d"], "kN", "R_d", "Tragwiderstand pro Verbindungsmittel", SOURCE, "6.2.1.1")
    add_step(
        name="Tragwiderstand pro Verbindungsmittel", produces="R_d",
        uses=["k_alpha", "k_red", "p_k_beta", "M_u_k", "f_h_1", "d", "eta_w", "eta_t"], ref="6.2.1.1",
        formula="R_d = k_alpha dot k_\"red\" dot (p dot k_beta) dot "
                "sqrt(M_(u,k) dot f_(h,1,k) dot d) dot eta_w dot eta_t",
        # the one formula of this record that is NOT set inline: it is the long one, and joining its
        # numbers onto its letters would run it over two lines anyway (docs/typst/api-conventions.md §10bis).
        inline=False,
        description="Gleichung (88), ohne $n_\"tot\"$. Die Wurzel ergibt N; der Wert ist in kN angegeben. "
                    "Bei Holz-Holz-Verbindungen ist die Lochleibungsfestigkeit des Seitenholzes 1 einzusetzen.")
    add("R_d_Verb", result["R_d_Verb"], "kN", 'R_(d,"Verb")', "Tragwiderstand der Verbindung",
        SOURCE, "6.2.1.1")
    add_step(name="Tragwiderstand der Verbindung", produces="R_d_Verb",
             uses=["n_tot", "R_d"], ref="6.2.1.1",
             formula="R_(d,\"Verb\") = n_\"tot\" dot R_d")

    results = ["R_d", "R_d_Verb"]
    if "R_d_truss" in result:
        # 5.3.6.2.2 reduces both answers, and the report now gives both, so both are printed (the
        # engineer, v0.84). Never folded into R_d, where a reader could not see it.
        factor = _math(result["truss_factor"])
        add("R_d_Fachwerk", result["R_d_truss"], "kN", 'R_(d,"Fachwerk")',
            "Tragwiderstand pro Verbindungsmittel bei vereinfachter Fachwerkberechnung",
            SOURCE, "5.3.6.2.2",
            description=sia265.clause("truss_reduction")["condition"])
        add_step(name="Tragwiderstand pro Verbindungsmittel im Fachwerk",
                 produces="R_d_Fachwerk", uses=["R_d"], ref="5.3.6.2.2",
                 formula="R_(d,\"Fachwerk\") = %s dot R_d" % factor)
        add("R_d_Verb_Fachwerk", result["R_d_Verb_truss"], "kN", 'R_(d,"Verb,Fachwerk")',
            "Tragwiderstand bei vereinfachter Fachwerkberechnung", SOURCE, "5.3.6.2.2")
        add_step(name="Tragwiderstand im Fachwerk", produces="R_d_Verb_Fachwerk",
                 uses=["n_tot", "R_d_Fachwerk"], ref="5.3.6.2.2",
                 formula="R_(d,\"Verb,Fachwerk\") = n_\"tot\" dot R_(d,\"Fachwerk\")")
        results += ["R_d_Fachwerk", "R_d_Verb_Fachwerk"]

    # --- the plates' bearing, SIA 263 Tabelle 16 (76) and 6.2.5 (D-13, D-16): a result of its own beside R_d
    plate = result.get("plate")
    if plate:
        t16 = sia263.bearing()
        norm263 = "norm:%s, Tabelle 16" % sia263.edition()
        table1 = "norm:%s, Tabelle 1" % sia263.edition()

        def add263(name, value, unit, symbol, label, ref, src=norm263, **more):
            calc.add_var(name, value=value, unit=unit, symbol=symbol, label=label, source=src, norm="SIA 263", norm_ref=ref, **more)

        def step263(name, produces, uses, formula, ref, **more):
            calc.add_step(name=name, result=produces, uses=list(uses), norm="SIA 263", norm_ref=ref, formula=formula, inline=True, **more)

        add263("t_pl", plate["t"], "mm", 't_"pl"', "Blechdicke", "Tabelle 16", src=entered, group="blech", group_label="Stahlblech", keep=True)
        add263("e_1", plate["e1"], "mm", "e_1", "Randabstand in Kraftrichtung", "Tabelle 16", src=entered, group="blech", keep=True)
        add263("e_2", plate["e2"], "mm", "e_2", "Randabstand quer zur Kraftrichtung", "Tabelle 16", src=entered, group="blech", keep=True)
        add263("d_0", plate["d0"], "mm", "d_0", "Lochdurchmesser", "Tabelle 16", src=entered, group="blech", keep=True)
        if plate["p1"] is not None:
            add263("p_1", plate["p1"], "mm", "p_1", "Abstand in Kraftrichtung", "Tabelle 16", src=SOURCE, group="blech_abstaende", group_label="Abstände der Stabdübel")
        if plate["p2"] is not None:
            add263("p_2", plate["p2"], "mm", "p_2", "Abstand quer zur Kraftrichtung", "Tabelle 16", src=SOURCE, group="blech_abstaende")
        add263("f_u_pl", plate["f_u"], "N/mm²", 'f_(u,"pl")', "Zugfestigkeit des Blechs", "Tabelle 1", src=table1,
               description="Stahl %s" % plate["grade"], group="blech_stahl", group_label="Stahl des Blechs")
        add263("f_y_pl", plate["f_y"], "N/mm²", 'f_(y,"pl")', "Streckgrenze des Blechs", "Tabelle 1", src=table1, group="blech_stahl")
        add263("gamma_M2", plate["gamma_M2"], "", "gamma_(M 2)", "Widerstandsbeiwert", t16["gamma_M2"]["norm_ref"], group="blech_stahl")
        if plate["tight"]:
            add263("e_1_eff", plate["e1_eff"], "mm", 'e_(1,"eff")', "Massgebender Randabstand", "Tabelle 16")
            step263("Massgebender Randabstand", "e_1_eff", ["p_1", "d_0"], 'e_(1,"eff") = p_1 - d_0 / 2', "Tabelle 16")
        e1_name = "e_1_eff" if plate["tight"] else "e_1"
        e1_symbol = 'e_(1,"eff")' if plate["tight"] else "e_1"
        add263("F_b_76", plate["F_76"], "kN", 'F_(b,"Rd",76)', "Lochleibungswiderstand nach Gleichung (76)", "Tabelle 16 (76)")
        step263("Lochleibungswiderstand nach Gleichung (76)", "F_b_76", [e1_name, "d_0", "f_u_pl", "d", "t_pl", "gamma_M2"],
                'F_(b,"Rd",76) = %s dot %s / d_0 dot f_(u,"pl") dot d dot t_"pl" / gamma_(M 2)' % (_math(t16["factor"]), e1_symbol), "Tabelle 16 (76)")
        add263("F_b_max", plate["F_max"], "kN", 'F_(b,"Rd,max")', "Obergrenze nach Gleichung (76)", "Tabelle 16 (76)")
        step263("Obergrenze nach Gleichung (76)", "F_b_max", ["f_u_pl", "d", "t_pl", "gamma_M2"],
                'F_(b,"Rd,max") = %s dot f_(u,"pl") dot d dot t_"pl" / gamma_(M 2)' % _math(t16["limit"]), "Tabelle 16 (76)")
        add263("F_b_pin", plate["F_pin"], "kN", 'F_(b,"Rd,Bolzen")', "Begrenzung für Bolzenverbindungen", t16["pin"]["norm_ref"])
        step263("Begrenzung für Bolzenverbindungen", "F_b_pin", ["f_y_pl", "d", "t_pl", "gamma_M2"],
                'F_(b,"Rd,Bolzen") = %s dot f_(y,"pl") dot d dot t_"pl" / gamma_(M 2)' % _math(t16["pin"]["factor"]), t16["pin"]["norm_ref"])
        add263("n_pl", plate["count"], "", 'n_"pl"', "Anzahl Bleche je Stabdübel", "Tabelle 16", src=entered)
        add263("F_b_Rd", plate["F_b_Rd"], "kN", 'F_(b,"Rd")', "Lochleibungswiderstand der Bleche pro Stabdübel", "Tabelle 16 (76)",
               description="Mit der Kraft auf einen Stabdübel nachzuweisen; nicht in R_d enthalten.")
        step263("Lochleibungswiderstand der Bleche pro Stabdübel", "F_b_Rd", ["n_pl", "F_b_76", "F_b_max", "F_b_pin"],
                'F_(b,"Rd") = n_"pl" dot min(F_(b,"Rd",76), F_(b,"Rd,max"), F_(b,"Rd,Bolzen"))', "Tabelle 16 (76)", bold=True)
        results.append("F_b_Rd")

    # --- the stiffness, Tabelle 25 written out (the engineer, v0.84)
    ser = result["K_ser"]
    c_0, c_90 = _math(ser["c_0"]), _math(ser["c_90"])
    rho_exponent, d_exponent = _math(ser["exponents"]["rho_k"]), _math(ser["exponents"]["d"])
    # eta_w,Steif keeps no row -- it is an operand of K_ser's own formula, which shows it -- so the
    # block's heading hangs on the first K_ser that prints (calc/engine.py, `heading`).
    add("eta_w_ser", ser["eta_w"], "", 'eta_(w,"Steif")',
        "Umrechnungsfaktor Holzfeuchte für die Steifigkeit", _norm_source("Tabelle 4"), "3.2.1.3")

    def kser_formula(symbol, index):
        return ("%s = (%s - (%s - %s) dot alpha_%d \\/ 90) dot rho_(k,%d)^%s dot d^%s dot eta_(w,\"Steif\")"
                % (symbol, c_0, c_0, c_90, index, index, rho_exponent, d_exponent))

    kser_note = ("Tabelle 25, pro Verbindungsmittel und Scherfuge. Die Werte gelten für Feuchteklasse 1 "
                 "und kurzfristige Beanspruchung; andere Feuchteklassen mit $eta_w$ der Steifigkeit "
                 "(Tabelle 4). Für beliebige Winkel zwischen Kraft- und Faserrichtung darf linear "
                 "interpoliert werden.")
    per_member = ser["per_member"]
    if len(per_member) > 1:
        for entry in per_member:
            i = entry["member"]
            add("K_ser_%d" % i, entry["K_ser"], "N/mm", 'K_("ser",%d)' % i,
                "Verschiebungsmodul", SOURCE, "6.2.1.4",
                heading="Verschiebungsmodul" if i == per_member[0]["member"] else None)
            add_step(name="Verschiebungsmodul Bauteil %d" % i, produces="K_ser_%d" % i,
                     uses=["alpha_%d" % i, "rho_k_%d" % i, "d", "eta_w_ser"], ref="6.2.1.4",
                     formula=kser_formula('K_("ser",%d)' % i, i),
                     description=kser_note if i == 1 else None)
        add("K_ser", ser["K_ser"], "N/mm", 'K_"ser"', "Massgebender Verschiebungsmodul",
            SOURCE, "6.2.1.4")
        add_step(name="Massgebender Verschiebungsmodul", produces="K_ser",
                 uses=["K_ser_%d" % e["member"] for e in per_member], ref="6.2.1.4",
                 formula='K_"ser" = min(%s)'
                         % ", ".join('K_("ser",%d)' % e["member"] for e in per_member))
    else:
        add("K_ser", ser["K_ser"], "N/mm", 'K_"ser"', "Verschiebungsmodul", SOURCE, "6.2.1.4",
            heading="Verschiebungsmodul")
        add_step(name="Verschiebungsmodul", produces="K_ser",
                 uses=["alpha_1", "rho_k_1", "d", "eta_w_ser"], ref="6.2.1.4",
                 formula=kser_formula('K_"ser"', 1), description=kser_note)
    # Level 1: the engineer reads the connection's stiffness beside its resistance, at every level
    # (show-connector-resistance prints it under R_d,Verb).
    add("K_ser_Verb", ser["K_ser_Verb"], "N/mm", 'K_("ser","Verb")',
        "Verschiebungsmodul der Verbindung", SOURCE, "6.2.1.4",
        description="Der Schlupf beträgt rund %s mm (6.2.1.3)." % _fmt(ser["slip"]))
    add_step(name="Verschiebungsmodul der Verbindung", produces="K_ser_Verb",
             uses=["n_tot", "p", "K_ser"], ref="6.2.1.4",
             formula='K_("ser","Verb") = n_"tot" dot p dot K_"ser"')

    # The tables, in the order they are declared; each carries the level and the side it belongs on,
    # so the display layer decides nothing (docs/domain/calculation-domains.md §3.3). Two of the four are gone in v0.84,
    # their numbers written out as formulas above; what is left of the k_beta table is its figures.
    tables = [_k_beta_figures(result)]
    if spacings is not None:
        tables.append(_spacing_table(result["d"], lengths or {}))

    return {"results": results, "tables": tables, **calc.to_dict()}


def _fmt(value):
    """A number as the dowel's formulas and tables write it: three decimals at most (calc/number_text.py's `trimmed`, UI-003)."""
    return number_text.trimmed(value, 3)
