"""The names of the snow and wind values of a workbook's sheet before v0.120, and what each became (spec 2026-10-21-restes-issue-69, REQ-001, REQ-002, CON-002, D-06; docs/domain/loads.md §3.3bis, §3.3quater).

Until v0.120 an `SL-*` or `WL-*` sheet gave its instance the names of its own cells -- `q_k11` for a flat roof's one load, `lastmodell`, `qk_max_bh` for the global wind force on b·h. From v0.120 the sheet was computed by the code a load entered in Woodcore is computed by, and its instance took that code's names: `q_k1`, `dachform`, `qk_max_cf1`. The sheets are read no more since issue #109 (D-33); what stays is the one table of what changed, read by the migration that rewrites a project's sections, scripts and sources when it is opened (domains/loads_migrate.py) off its previous export. A rename depends on the instance -- its roof, its table of Annexe C --, so each table is a function of them.

**No equivalent** is a rename to None: a value the old reader printed and the new one does not -- «Grosse Höhensprünge: Nein», which states that nothing is added and so is no var any more; the six global forces of a table whose force coefficients are not one per reference area (Tableaux 50 to 56). The migration does not guess one: a section that still names it stops the export, naming the file, the line and the name (CON-002).

Qt-free; imports nothing of the domains but the wind tables of calc/norms/.
"""

from norms import sia261_wind

SNOW = "snow-load"
WIND = "wind-load"

# --- snow ------------------------------------------------------------------------------------

# The roof a load model of an old snow instance names, by its first word («GiebeldachLM2» -> duo): what its names depend on
ROOF_OF = {"Flachdach": "flat", "Giebeldach": "duo", "Sheddach": "shed"}


def roof_of(load_model):
    """The source's roof a load model of the workbook names, None where it names none (domains/snow.py until issue #109)."""
    return next((roof for word, roof in ROOF_OF.items() if str(load_model).startswith(word)), None)


def snow_renamed(roof, height_step):
    """{old name: new name, or None where there is none} of an SL-* sheet's instance, by its roof and whether F19 says «Ja»."""
    out = {"lastmodell": "dachform", "hoehenspruenge": "hoehensprung" if height_step else None}
    if roof == "flat":
        out.update({"mu_11": "mu_1", "q_k11": "q_k1"})
    return out


# --- wind ------------------------------------------------------------------------------------

# The areas the old reader named a global force by, and the area of Annexe C's force coefficient each is
WIND_AREAS = (("bh", "b·h"), ("dh", "d·h"), ("db", "d·b"))
WIND_KINDS = ("max", "min")


def wind_forces(table):
    """{old area key: the force coefficient's name} for a table of Annexe C, `bh` -> `cf1`: the one coefficient of the group `cf` whose reference area is that area (a factor of it, 0.96·d·h, being the same area). An area two coefficients share, or none gives, has no name (None)."""
    columns = [c for c in sia261_wind.table(str(table))["columns"] if c["group"] == "cf"]
    out = {}
    for key, area in WIND_AREAS:
        found = [c for c in columns if c["area"] == area]
        out[key] = "cf%d" % found[0]["index"] if len(found) == 1 else None
    return out


def wind_renamed(table):
    """{old name: new name, or None} of a WL-* sheet's instance by its table: the six global forces, `qk_max_bh` -> `qk_max_cf1`."""
    forces = wind_forces(table)
    return {"qk_%s_%s" % (kind, key): ("qk_%s_%s" % (kind, forces[key]) if forces[key] else None)
            for kind in WIND_KINDS for key, _area in WIND_AREAS}


def renamed(domain, instance):
    """{old: new or None} of one instance of the calculations an old export wrote, by its own values -- the roof its `lastmodell` named and its `hoehenspruenge`, the table its `tables` cite: what the migration reads off the previous data/calculations.json. {} for an instance entered in Woodcore, whose names did not change."""
    if instance.get("source_file"):
        return {}
    values = {name: var.get("value") for name, var in (instance.get("vars") or {}).items()}
    if domain == SNOW:
        roof = roof_of(values.get("lastmodell", "")) if "lastmodell" in values else None
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
