"""A steel member's section: its values, whether SZS C5's or a free profile's, and its class after SIA 263:2013 Tabelle 5a/5b (issues #50, #51; spec 2026-10-12-section-acier REQ-001, REQ-003, REQ-005, D-11, ARCH-RISK-206; docs/domain/steel.md).

**One record for both sources.** `of_c5(code, dims)` and `of_free(resolved)` give the same dictionary -- `shape` (I, U, T, L, RHS, CHS, bar or free), the designation, A, the shear areas, I, W_el, W_pl, i and K about both axes, the plates' sizes and the walls Tabelle 5 classifies -- so no check branches on where its section came from (ARCH-RISK-102). The values are the table's (calc/norms/szs_c5.py) or the rectangles' (domains/profile.py); nothing here is a norm's value except Tabelle 5's limits, read through calc/norms/sia263.py.

**The walls** are what Tabelle 5 calls «Scheiben»: an internal wall held on both long edges (Tabelle 5a: a web, a tube's wall), an outstand held on one (5b: half a flange, a T's stem, an angle's leg). Their c is the figure's: between the root radii of a rolled I or U (C5's h_1 for the web), (b − t_w − 2r)/2 for half a flange, h − 3t and b − 3t for a hollow section (1.5 t at each corner); for an angle the leg less its thickness. A free profile's are its rectangles' (D-11). Each wall also says which way it lies -- `vertical` walls are bent in their plane by M_y, `horizontal` ones by M_z -- and where it lies about the centroid.

**The class** (`classify`) is the worst of the walls' under the member's design forces, compression positive:

* a wall nowhere compressed is not classified;
* an internal wall bent in its plane and not compressed over its whole height takes the rows «Druck mit Biegung» / «Zug mit Biegung»: for classes 1 and 2 alpha, the compressed part of the plastic stress block, alpha = (1 + N_Ed γ_M1 / (c t f_y)) / 2 -- the web carrying the normal force alone, the reference templates' assumption and the safe one --, alpha = 0.5 being «reine Biegung»; for class 3 psi, the ratio of its elastic edge stresses;
* every other wall -- one compressed over its whole width, and every outstand -- takes the row «Druck» (9 ε, 10 ε, 14 ε for an outstand): the safe side, a gradient along an outstand being left out;
* a round tube takes D/t ≤ 50 ε², 70 ε², 90 ε²; a solid bar is class 1.

Class 4 (EER, 4.5.3) is not built: a check on such a section is not calculable and says so.
"""

import math

from norms import sia263, szs_c5

SHAPES = ("I", "U", "T", "L", "RHS", "CHS", "bar", "free")
SHAPE_OF = {
    "IPE": "I", "IPEA": "I", "IPN": "I", "HEA": "I", "HEB": "I", "HEM": "I", "HD": "I", "HL": "I",
    "UPE": "U", "UPN": "U", "T": "T", "IPET": "T", "HEAT": "T", "HEBT": "T", "L": "L",
    "RRK": "RHS", "RRW": "RHS", "ROR": "CHS", "RND": "bar", "VKT": "bar",
}
# The shapes Tabelle 5's sentences and SIA 263 5.1.5, 5.1.6 name: a doubly symmetric I and a rolled rectangular hollow section (RRW; RRK is cold formed, which 5.1.5.3 and 5.1.6.3 do not name).
DOUBLY_SYMMETRIC_I = ("IPE", "IPEA", "IPN", "HEA", "HEB", "HEM", "HD", "HL")
ROLLED_RHS = ("RRW",)


def _wall(name, role, c, t, p1, p2):
    """A wall: its c and t, and the two ends of its long side as (y, z) about the centroid -- what the stresses are read at. `lies` says which moment bends it in its plane: a vertical wall (its ends one above the other) M_y, a horizontal one M_z."""
    lies = "vertical" if abs(p1[0] - p2[0]) < abs(p1[1] - p2[1]) else "horizontal"
    return {"name": name, "role": role, "c": c, "t": t, "lies": lies, "p1": p1, "p2": p2}


def of_c5(code, dims):
    """The section of an SZS C5 designation, or None where the tables do not carry it."""
    p = szs_c5.profile(code, dims)
    if p is None:
        return None
    shape = SHAPE_OF[code]
    rec = {"source": "c5", "code": code, "shape": shape, "designation": p["designation"], "norm_ref": "SZS C5:2018, " + p["norm_ref"],
           "anomalies": p["anomalies"], "doubly_symmetric_i": code in DOUBLY_SYMMETRIC_I, "rolled_rhs": code in ROLLED_RHS}
    for key in ("A", "A_v", "A_w", "I_y", "I_z", "W_el_y", "W_el_z", "W_pl_y", "W_pl_z", "i_y", "i_z", "K", "h", "b", "t_w", "t_f", "t", "D", "h_1", "m"):
        rec[key] = p.get(key)
    h, b = p["h"], p["b"]
    walls = []
    if shape in ("I", "U", "T"):
        tw, tf = p.get("t_w"), p.get("t_f")
        if code == "T":
            tw = tf = p["t"]
        # the root radius: IPN's is its web's thickness and UPN's its flange's (the heads of pp. 33 and 37), a T's is r_1
        r = p.get("r") or (tw if code == "IPN" else tf if code == "UPN" else p.get("r_1") or 0)
        rec["t_w"], rec["t_f"], rec["r"] = tw, tf, r
        if shape == "I":
            c_web = p.get("h_1") or h - 2 * tf - 2 * r
            walls.append(_wall("Steg", "internal", c_web, tw, (0, -c_web / 2), (0, c_web / 2)))
            c = (b - tw - 2 * r) / 2
            for side, z in (("oben", h / 2 - tf / 2), ("unten", -(h / 2 - tf / 2))):
                walls.append(_wall("Flansch %s links" % side, "outstand", c, tf, (-b / 2, z), (-(tw / 2 + r), z)))
                walls.append(_wall("Flansch %s rechts" % side, "outstand", c, tf, (tw / 2 + r, z), (b / 2, z)))
        elif shape == "U":
            e = p.get("e") or b / 2   # the centroid's distance from the web's back (p. 35, p. 37)
            c_web = p.get("h_1") or h - 2 * tf - 2 * r
            walls.append(_wall("Steg", "internal", c_web, tw, (-e + tw / 2, -c_web / 2), (-e + tw / 2, c_web / 2)))
            c = b - tw - r
            for side, z in (("oben", h / 2 - tf / 2), ("unten", -(h / 2 - tf / 2))):
                walls.append(_wall("Flansch %s" % side, "outstand", c, tf, (-e + tw + r, z), (b - e, z)))
        else:
            e = p.get("e_y") or h / 2   # the centroid's distance from the flange's outer face (p. 48, p. 49)
            c_stem = h - tf - r
            walls.append(_wall("Steg", "outstand", c_stem, tw, (0, e - tf - r), (0, -(h - e))))
            c = (b - tw - 2 * r) / 2
            z = e - tf / 2
            walls.append(_wall("Flansch links", "outstand", c, tf, (-b / 2, z), (-(tw / 2 + r), z)))
            walls.append(_wall("Flansch rechts", "outstand", c, tf, (tw / 2 + r, z), (b / 2, z)))
    elif shape == "L":
        t, a = p["t"], p["a"]
        ey, ez = p.get("e_y") or a / 2, p.get("e_z") or p["b"] / 2
        walls.append(_wall("Schenkel a", "outstand", a - t, t, (-ez + t / 2, -ey + t), (-ez + t / 2, a - ey)))
        walls.append(_wall("Schenkel b", "outstand", p["b"] - t, t, (-ez + t, -ey + t / 2), (p["b"] - ez, -ey + t / 2)))
        rec["t"] = t
    elif shape == "RHS":
        t = p["t"]
        cw, cf = h - 3 * t, b - 3 * t
        for side, y in (("links", -(b / 2 - t / 2)), ("rechts", b / 2 - t / 2)):
            walls.append(_wall("Steg %s" % side, "internal", cw, t, (y, -cw / 2), (y, cw / 2)))
        for side, z in (("oben", h / 2 - t / 2), ("unten", -(h / 2 - t / 2))):
            walls.append(_wall("Flansch %s" % side, "internal", cf, t, (-cf / 2, z), (cf / 2, z)))
        # 5.1.4: the area available in the shear's direction -- the two webs (mechanics; SZS C5 prints no A_v for a tube)
        rec["A_v"] = rec["A_v_z"] = 2 * (h - 2 * t) * t
        rec["A_v_y"] = 2 * (b - 2 * t) * t
    elif shape == "CHS":
        # a round tube's shear area, 2 A / pi -- mechanics (SZS C5 prints none)
        rec["A_v"] = rec["A_v_z"] = rec["A_v_y"] = 2 * p["A"] / math.pi
    else:
        # a solid bar's: 3/4 A (round) and 2/3 A (square), the shear stress at the centroid being 4/3 and 3/2 of V/A -- mechanics
        rec["A_v"] = rec["A_v_z"] = rec["A_v_y"] = p["A"] * (0.75 if code == "RND" else 2 / 3)
    if shape in ("I", "U") and rec.get("A_v"):
        rec["A_v_z"] = rec["A_v"]
        # V_y is carried by the flanges -- mechanics; SZS C5's A_v is for a shear along the web
        rec["A_v_y"] = 2 * b * rec["t_f"] if shape == "I" else 2 * (b - rec["t_w"]) * rec["t_f"]
    if shape in ("T", "L"):
        thick = rec.get("t_f") or rec.get("t")
        rec["A_v_z"] = (rec["h"] - thick) * (rec.get("t_w") or rec.get("t"))
        rec["A_v_y"] = rec["b"] * thick
        rec["A_v"] = rec["A_v_z"]
    rec["walls"] = walls
    rec["t_max"] = max(x for x in (rec.get("t_w"), rec.get("t_f"), rec.get("t"), h if shape == "bar" else None) if x)
    return rec


def of_free(resolved):
    """The section of a free profile as domains/profile.py `resolve` gives it."""
    props = resolved["properties"]
    parts = resolved["source"]["parts"]
    rec = {"source": "user", "code": "USR", "shape": "free", "designation": "USR %s" % resolved["id"], "norm_ref": "",
           "anomalies": {}, "doubly_symmetric_i": False, "rolled_rhs": False}
    for key in ("A", "I_y", "I_z", "W_el_y", "W_el_z", "W_pl_y", "W_pl_z", "i_y", "i_z", "K", "h", "b", "t_max"):
        rec[key] = props[key]
    walls = []
    for p in parts:
        if p["role"] == "none":
            continue
        yc, zc = p["y"] + p["b"] / 2 - props["y_s"], p["z"] + p["h"] / 2 - props["z_s"]
        if p["h"] >= p["b"]:
            ends = ((yc, p["z"] - props["z_s"]), (yc, p["z"] + p["h"] - props["z_s"]))
        else:
            ends = ((p["y"] - props["y_s"], zc), (p["y"] + p["b"] - props["y_s"], zc))
        walls.append(_wall(p["name"], p["role"], max(p["b"], p["h"]), min(p["b"], p["h"]), *ends))
    rec["walls"] = walls
    # 5.1.4: the area available in the shear's direction -- the rectangles standing in it (mechanics)
    rec["A_v_z"] = sum(p["b"] * p["h"] for p in parts if p["h"] > p["b"]) or props["A"]
    rec["A_v_y"] = sum(p["b"] * p["h"] for p in parts if p["b"] >= p["h"]) or props["A"]
    rec["A_v"] = rec["A_v_z"]
    return rec


# --- the class --------------------------------------------------------------------------------

def _limits(kind, cls_index, eps, alpha=None, psi=None, k=None):
    """One limit of Tabelle 5 (max c/t) by the file's kind of formula."""
    t5 = sia263.table_5()
    if kind == "internal_compression":
        return t5["internal"]["compression"][cls_index] * eps
    if kind == "internal_bending":
        return t5["internal"]["bending"][cls_index] * eps
    if kind == "outstand_compression":
        return t5["outstand"]["compression"][cls_index] * eps
    if kind == "internal_compression_bending":
        rows = t5["internal"]["compression_bending"]["class_%d" % (cls_index + 1)]
        if cls_index < 2:
            row = rows[0] if alpha >= 0.5 else rows[1]
            if row["kind"] == "alpha_internal":
                return row["coefficient"] * eps / (row["divisor"][0] * alpha - row["divisor"][1])
            return row["coefficient"] * eps / alpha
        row = rows[0] if psi > -1 else rows[1]
        if row["kind"] == "psi_internal":
            return row["coefficient"] * eps / (row["divisor"][0] + row["divisor"][1] * psi)
        return row["coefficient"] * eps * (1 - psi) * math.sqrt(-psi)
    raise ValueError(kind)


def _edge_stresses(sec, wall, N, M_y, M_z):
    """The elastic stresses at a wall's two ends, compression positive, for the signs of the moments that compress it most: (sigma_1, sigma_2), sigma_1 the larger. M_y bends about the horizontal axis (stress along z), M_z about the vertical one (along y)."""
    n = N / sec["A"]
    best = None
    for sy in (1, -1):
        for sz in (1, -1):
            stresses = sorted((n + (sy * abs(M_y) * z / sec["I_y"] if M_y else 0) + (sz * abs(M_z) * y / sec["I_z"] if M_z else 0)
                               for y, z in (wall["p1"], wall["p2"])), reverse=True)
            if best is None or stresses[0] > best[0]:
                best = stresses
    return best


def classify(sec, f_y, N=0.0, M_y=0.0, M_z=0.0):
    """The class of a section under N (compression positive, N/mm units: N in N, M in Nmm, f_y in N/mm²): {"class", "epsilon", "walls": [{name, role, c, t, ratio, row, limits (3), class, alpha?, psi?}], "governing", "norm_ref"}.

    A wall nowhere compressed is left out; class 4 is the class, which the checks refuse (EER not built)."""
    eps = sia263.epsilon(f_y)
    gamma = sia263.gamma_M1()["value"]
    out = []
    if sec["shape"] == "bar":
        return {"class": 1, "epsilon": eps, "walls": [], "governing": None, "norm_ref": "Tabelle 5"}
    if sec["shape"] == "CHS":
        if N <= 0 and not (M_y or M_z):
            return {"class": 1, "epsilon": eps, "walls": [], "governing": None, "norm_ref": "Tabelle 5a"}
        spec = sia263.table_5()["internal"]["round_tube"]
        ratio = sec["D"] / sec["t"]
        limits = [c * eps ** spec["epsilon_power"] for c in spec["D_over_t"]]
        cls = next((i + 1 for i, lim in enumerate(limits) if ratio <= lim), 4)
        wall = {"name": "Rohr", "role": "round", "c": sec["D"], "t": sec["t"], "ratio": ratio, "row": "round_tube", "limits": limits, "class": cls}
        return {"class": cls, "epsilon": eps, "walls": [wall], "governing": wall, "norm_ref": "Tabelle 5a"}
    for wall in sec["walls"]:
        s1, s2 = _edge_stresses(sec, wall, N, M_y, M_z)
        if s1 <= 1e-9:
            continue   # nowhere compressed
        ratio = wall["c"] / wall["t"]
        entry = {"name": wall["name"], "role": wall["role"], "c": wall["c"], "t": wall["t"], "ratio": ratio}
        if wall["role"] == "internal" and s2 < 0:
            alpha = min(max(0.5 * (1 + N * gamma / (wall["c"] * wall["t"] * f_y)), 1e-6), 1.0)
            psi = s2 / s1
            if N == 0:
                entry["row"] = "internal_bending"
                limits = [_limits("internal_bending", i, eps) for i in range(3)]
            else:
                entry["row"] = "internal_compression_bending"
                entry["alpha"], entry["psi"] = alpha, psi
                limits = ([_limits("internal_compression_bending", i, eps, alpha=alpha, psi=psi) for i in range(3)]
                          if alpha < 1 else [_limits("internal_compression", i, eps) for i in range(3)])
        elif wall["role"] == "internal":
            entry["row"] = "internal_compression"
            limits = [_limits("internal_compression", i, eps) for i in range(3)]
        else:
            entry["row"] = "outstand_compression"
            limits = [_limits("outstand_compression", i, eps) for i in range(3)]
        entry["limits"] = limits
        entry["class"] = next((i + 1 for i, lim in enumerate(limits) if ratio <= lim + 1e-12), 4)
        out.append(entry)
    if not out:
        return {"class": 1, "epsilon": eps, "walls": [], "governing": None, "norm_ref": "Tabelle 5"}
    governing = max(out, key=lambda w: (w["class"], w["ratio"] / w["limits"][min(w["class"], 3) - 1]))
    return {"class": max(w["class"] for w in out), "epsilon": eps, "walls": out, "governing": governing,
            "norm_ref": "Tabelle 5a, 5b" if any(w["role"] == "outstand" for w in out) else "Tabelle 5a"}
