"""The wind's arithmetic, worked out once and kept with where each number came from (spec 2026-10-23-onglet-vent-briques, REQ-001 to REQ-008, ARCH-004): `analysis(src)` is what `wind_source.build_instance` writes, and what the wind's tab shows and lights up on a hover -- never `calculations.json`. Every coefficient out of `norms/sia261_wind.py`. No Qt here.

**What is computed** -- c_h of (12) at z (h unless the source says another), with its floors and category IV's switch (6.2.1.2), q_p = c_h · q_p0 (11); c_red of Figur 9 for the facade areas b·h and d·h, each its own in a row less than 15° off a reference direction, the larger of the two in every other (6.3.3), 1.0 for any other area (6.3.2); then

* the **global forces**, per force coefficient of the table and per row φ: q_k = c_red · c_d · c_f · q_p (kN/m²) and Q_k = q_k · A_ref (15) in kN, A_ref from the norm file's closed table (`sia261_wind.area`; None where the header names a dimension the building is not given by, its force per m² only); their largest and smallest with the φ and the c_f that gave them; a column the norm marks «*» (computed directly) is named and not computed;
* the **local pressures**, per surface the table names and per row φ: q_k = q_p · (c_d · c_pe − c_pi) of (13), (14), (17), (18), without c_red (6.3.1) -- c_pi the chosen openings' column (the source's `openings`, «rep» where a source of 1.0 or 1.1 holds none, D-24), else the surface's own (open buildings), else 0 (canopies); a pair the norm writes ±x or a/b counts both its values; the largest and the smallest with their φ, c_pe and c_pi and which value of a pair each is; m, n and o (`group` «loc») apart from the walls and the roofs (Figur 22).

**Keys** -- every number carries the cells of the table it was read off, `cell(column key, row)` and, for a pair, `cell(column key, row, side)`: opaque words the tab's hover brick matches and never reads (ARCH-004).
"""

import re

from norms import sia261_wind

DEFAULT_OPENING = "rep"
WALL = re.compile(r"^[ABCD]\d*$")


def values(value):
    """A cell as the values it stands for, [(value, side)]: a pair both (side 0 and 1), a number itself (side None), an empty or a direct cell none."""
    if value is None or value == "direct":
        return []
    return list(zip(value, (0, 1))) if isinstance(value, list) else [(value, None)]


def cell(key, row, side=None):
    """The opaque key of a cell of the table: its column's key and its row's index, and which value of a pair."""
    return "cell:%s:%d" % (key, row) + ("" if side is None else ":%d" % side)


def surface_group(column):
    """Where a surface is shown: «loc» the localised m, n, o (Figur 22, never added to the large surfaces), «pt» a point of a curved roof (Tableaux 63, 64), «wall» A to D and their parts, «roof» every other."""
    if column["group"] == "cpe_local":
        return "loc"
    surface = column["surface"]
    if surface.endswith("°"):
        return "pt"
    return "wall" if WALL.match(surface) else "roof"


def c_red_of(column, cred, label):
    """The reduction factor a force coefficient's area takes in the row `label` (6.3.2, 6.3.3), and which: «bh», «dh», «max» or None (1.0)."""
    if column["area"] not in ("b·h", "d·h"):
        return 1.0, None
    if sia261_wind.oblique(label):
        return cred["max"], "max"
    which = "bh" if column["area"] == "b·h" else "dh"
    return cred[which], which


def _extreme(entries, larger):
    """The first entry with the largest (`larger`) or the smallest q -- the row order of the norm's table decides a tie, as the prototype's does."""
    best = None
    for entry in entries:
        if best is None or (entry["q"] > best["q"] if larger else entry["q"] < best["q"]):
            best = entry
    return best


def chosen_opening(table, opening):
    """The openings' c_pi column `opening` names, else the table's first, else None (a table with no openings' column)."""
    openings = [c for c in table["columns"] if c["group"] == "cpi_opening"]
    return next((c for c in openings if c["opening"] == opening), openings[0] if openings else None)


def global_forces(table, qp, cred, c_d, dims):
    out = []
    for i, column in enumerate(table["columns"]):
        if column["group"] not in ("cf", "cf_snow"):
            continue
        name = "%s%d" % ("cfs" if column["group"] == "cf_snow" else "cf", column["index"])
        area = sia261_wind.area(column, *dims)
        force = {"name": name, "key": column["key"], "column": column, "area": area, "direct": any(row["values"][i] == "direct" for row in table["rows"]),
                 "facade": column["area"] in ("b·h", "d·h"), "rows": [], "max": None, "min": None}
        if not force["direct"]:
            entries = []
            for r, row in enumerate(table["rows"]):
                factor, which = c_red_of(column, cred, row["label"])
                qs = []
                for value, side in values(row["values"][i]):
                    q = factor * c_d * value * qp
                    entry = {"q": q, "Q": None if area is None else q * area, "phi": row["label"], "row": r, "c_f": value, "c_red": factor, "c_red_of": which,
                             "keys": [cell(column["key"], r, side)]}
                    qs.append(entry)
                    entries.append(entry)
                force["rows"].append({"phi": row["label"], "row": r, "c_red": factor, "c_red_of": which, "values": qs})
            force["max"], force["min"] = _extreme(entries, True), _extreme(entries, False)
        out.append(force)
    return out


def local_pressures(table, qp, c_d, opening):
    """The surfaces of the table, each with its rows φ and their q_k, and its extremes -- c_pi from the chosen openings' column, the surface's own, or 0."""
    cols = table["columns"]
    index = {c["key"]: i for i, c in enumerate(cols)}
    own = {c["surface"]: index[c["key"]] for c in cols if c["group"] == "cpi"}
    chosen = chosen_opening(table, opening)
    out = []
    for i, column in enumerate(cols):
        if column["group"] not in ("cpe", "cpe_local"):
            continue
        j = index[chosen["key"]] if chosen else own.get(column["surface"])
        cpi_key = None if j is None else cols[j]["key"]
        rows, entries, cpes = [], [], []
        for r, row in enumerate(table["rows"]):
            externals = values(row["values"][i])
            internals = (values(row["values"][j]) if j is not None else []) or [(0, None)]
            qs = []
            for e, e_side in externals:
                cpes.append(e)
                for p, p_side in internals:
                    keys = [cell(column["key"], r, e_side)] + ([cell(cpi_key, r, p_side)] if j is not None and row["values"][j] is not None else [])
                    entry = {"q": qp * (c_d * e - p), "phi": row["label"], "row": r, "c_pe": e, "c_pi": p, "c_pi_key": cpi_key, "keys": keys}
                    qs.append(entry)
                    entries.append(entry)
            rows.append({"phi": row["label"], "row": r, "values": qs})
        if not entries:
            continue
        out.append({"surface": column["surface"], "key": column["key"], "group": surface_group(column), "c_pi_key": cpi_key, "own_c_pi": not chosen and j is not None,
                    "rows": rows, "max": _extreme(entries, True), "min": _extreme(entries, False), "c_pe_max": max(cpes), "c_pe_min": min(cpes)})
    return out, chosen


def analysis(src):
    """The wind of a valid source (`wind_source.check_fields`), every number with where it came from -- see the module's docstring."""
    table = sia261_wind.table(src["table"])
    b, d, h, c_d = src["b"], src["d"], src["h"], src["c_d"]
    z = src["z"] if src.get("z") is not None else h
    c_h, z_used, profile = sia261_wind.c_h(z, src["terrain"])
    qp = c_h * src["q_p0"]
    cred = {"bh": sia261_wind.c_red(h, b / h), "dh": sia261_wind.c_red(h, d / h)}
    cred["max"] = max(cred["bh"], cred["dh"])
    forces = global_forces(table, qp, cred, c_d, (b, d, h))
    local, chosen = local_pressures(table, qp, c_d, src.get("openings") or DEFAULT_OPENING)
    peak = table.get("cpe_peak")
    return {"table": table, "q_p0": src["q_p0"], "z": z, "z_used": z_used, "c_h": c_h, "profile": profile, "terrain": src["terrain"], "q_p": qp,
            "cred": cred, "c_d": c_d, "forces": forces, "local": local,
            "opening": chosen["opening"] if chosen else None, "opening_key": chosen["key"] if chosen else None,
            "openings": [c["opening"] for c in table["columns"] if c["group"] == "cpi_opening"],
            "cpe_peak": peak, "q_peak": None if peak is None else peak * qp}


# --- what the results in 3D show (spec 2026-10-23-onglet-vent-briques, UI-014 to UI-016): the prototype's loadsAt and forcesAt

MAX = "max"   # every direction of the table, its extreme


def _pick(values, sign):
    return (max(values) if sign == "+" else min(values)) if values else None


def loads_at(result, direction=MAX, sign="+"):
    """{surface: q_k} at the row `direction` of the table, or the extreme over every row (MAX): the largest pressure ("+") or the largest suction ("-") -- a surface whose extreme is of the other sign left out."""
    out = {}
    for s in result["local"]:
        values = [v["q"] for r in s["rows"] if direction == MAX or r["phi"] == direction for v in r["values"]]
        value = _pick(values, sign)
        if value is None or (value <= 0 if sign == "+" else value >= 0):
            continue
        out[s["surface"]] = value
    return out


def forces_at(result, direction=MAX, sign="+"):
    """{"f1": Q_k in kN, ...} at the row `direction`, or the extreme over every row (MAX): the largest ("+") or the smallest ("-") -- a force with no reference area, or computed directly, left out."""
    out = {}
    for f in result["forces"]:
        if f["direct"] or f["area"] is None or not f["name"].startswith("cf"):
            continue
        values = [v["Q"] for r in f["rows"] if direction == MAX or r["phi"] == direction for v in r["values"]]
        value = _pick(values, sign)
        if value is not None:
            out["f" + f["name"][2:]] = value
    return out
