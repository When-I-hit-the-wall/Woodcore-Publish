"""The names of the snow and wind values of a workbook's sheet: what changed in v0.120, and where the sheet shows each (spec 2026-10-21-restes-issue-69, REQ-001, REQ-002, CON-002, D-06, D-07; docs/domain/loads.md §3.3bis, §3.3quater).

Until v0.120 an `SL-*` or `WL-*` sheet gave its instance the names of its own cells -- `q_k11` for a flat roof's one load, `lastmodell`, `qk_max_bh` for the global wind force on b·h. Since the sheet is computed by the code a load entered in Woodcore is computed by, its instance takes that code's names: `q_k1`, `dachform`, `qk_max_cf1`. The one table of what changed is here, read twice -- by the migration that rewrites a project's sections, scripts and sources when it is opened (domains/loads_migrate.py), and by the readers of the sheets, which compare what the sheet computed with Woodcore's value under its new name (snow.py, wind.py). A rename depends on the instance -- its roof, its table of Annexe C --, so each table is a function of them.

**No equivalent** is a rename to None: a value the old reader printed and the new one does not -- «Grosse Höhensprünge: Nein», which states that nothing is added and so is no var any more; the six global forces of a table whose force coefficients are not one per reference area (Tableaux 50 to 56). The migration does not guess one: a section that still names it stops the export, naming the file, the line and the name (CON-002).

Qt-free; imports nothing of the domains but the wind tables of calc/norms/.
"""

from norms import sia261_wind

SNOW = "snow-load"
WIND = "wind-load"

# --- snow ------------------------------------------------------------------------------------

# The values an SL-* sheet computes, by the roof its load model names, and the cell it shows each in: what is compared with Woodcore's (D-07). N37/N38, the duo-pitch roof's load model 2, are the halves Woodcore computes as q_k11h and q_k12h.
_SNOW_COMMON = [("h_ref", "H12"), ("s_k", "H17")]
SNOW_COMPARED = {
    "flat": _SNOW_COMMON + [("mu_1", "H26"), ("q_k1", "I37")],
    "duo": _SNOW_COMMON + [("mu_11", "H26"), ("mu_12", "H27"), ("q_k11", "I37"), ("q_k12", "I38"), ("q_k11h", "N37"), ("q_k12h", "N38")],
    "shed": _SNOW_COMMON + [("mu_11", "H26"), ("mu_12", "H27"), ("mu_2m", "K35"), ("q_k11", "I37"), ("q_k12", "I38"), ("q_k2m", "I39")],
}


def snow_renamed(roof, height_step):
    """{old name: new name, or None where there is none} of an SL-* sheet's instance, by its roof and whether F19 says «Ja»."""
    out = {"lastmodell": "dachform", "hoehenspruenge": "hoehensprung" if height_step else None}
    if roof == "flat":
        out.update({"mu_11": "mu_1", "q_k11": "q_k1"})
    return out


# --- wind ------------------------------------------------------------------------------------

# The areas the old reader named a global force by, the column it read each from, and the area of Annexe C's force coefficient it is
WIND_AREAS = (("bh", "J", "b·h"), ("dh", "K", "d·h"), ("db", "L", "d·b"))
WIND_ROWS = (("max", 69), ("min", 70))
_WIND_COMMON = [("zg", "J12"), ("alpha_r", "J13"), ("z", "J14"), ("ch", "J15"), ("qp", "J17"), ("cred_bh", "J19"), ("cred_dh", "J20")]


def wind_forces(table):
    """{old area key: the force coefficient's name} for a table of Annexe C, `bh` -> `cf1`: the one coefficient of the group `cf` whose reference area is that area (a factor of it, 0.96·d·h, being the same area). An area two coefficients share, or none gives, has no name (None)."""
    columns = [c for c in sia261_wind.table(str(table))["columns"] if c["group"] == "cf"]
    out = {}
    for key, _column, area in WIND_AREAS:
        found = [c for c in columns if c["area"] == area]
        out[key] = "cf%d" % found[0]["index"] if len(found) == 1 else None
    return out


def wind_renamed(table):
    """{old name: new name, or None} of a WL-* sheet's instance by its table: the six global forces, `qk_max_bh` -> `qk_max_cf1`."""
    forces = wind_forces(table)
    return {"qk_%s_%s" % (kind, key): ("qk_%s_%s" % (kind, forces[key]) if forces[key] else None)
            for kind, _row in WIND_ROWS for key, _column, _area in WIND_AREAS}


def wind_compared(table):
    """[(var name, cell)] of a WL-* sheet with the table `table`: the profile, q_p, c_red and the six global forces, under their new names."""
    forces = wind_forces(table)
    out = list(_WIND_COMMON)
    for kind, row in WIND_ROWS:
        for key, column, _area in WIND_AREAS:
            if forces[key]:
                out.append(("qk_%s_%s" % (kind, forces[key]), "%s%d" % (column, row)))
    return out


def renamed(domain, instance):
    """{old: new or None} of one instance of the calculations an old export wrote, by its own values -- the roof its `lastmodell` named and its `hoehenspruenge`, the table its `tables` cite: what the migration reads off the previous data/calculations.json. {} for an instance entered in Woodcore, whose names did not change."""
    if instance.get("source_file"):
        return {}
    values = {name: var.get("value") for name, var in (instance.get("vars") or {}).items()}
    if domain == SNOW:
        from domains import snow
        roof = snow.roof_of(values.get("lastmodell", "")) if "lastmodell" in values else None
        if roof is None:
            return {}   # already in the new names
        return snow_renamed(roof, values.get("hoehenspruenge") == "Ja")
    if domain == WIND:
        if not any(name.startswith(("qk_max_", "qk_min_")) and name[-2:] in ("bh", "dh", "db") for name in values):
            return {}
        table = wind_table_of(instance)
        if table is None:
            return {key: None for key in wind_renamed("31")}
        return wind_renamed(table)
    return {}


def wind_table_of(instance):
    """The table of Annexe C an old wind instance was read with: its local forces table's note names it («Druckbeiwerte 59b»), None where it does not or names no table Woodcore holds."""
    import re
    for table in instance.get("tables") or ():
        match = re.search(r"\(Druckbeiwerte ([0-9]+[a-d]?)\)", str(table.get("note", "")))
        if match and match.group(1) in sia261_wind.NUMBERS:
            return match.group(1)
    return None
