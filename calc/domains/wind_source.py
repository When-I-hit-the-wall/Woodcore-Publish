"""Wind loads entered in Woodcore (issue #37): one building per source, its wind computed here from SIA 261:2020 chapter 6 and Annexe C -- every coefficient out of `norms/sia261_wind.py`. Since v0.120 the one calculation of the wind: a `WL-*` sheet of the Belastungsannahmen workbook is read for its inputs alone and computed here too (domains/wind.py, spec 2026-10-21-restes-issue-69, REQ-002, ARCH-002; docs/domain/loads.md §3.3quater).

**A source** is `Woodcore-Datei/loads/wind/<id>.json` (schemas/wind-source.schema.json, 1.0): q_p0 at the site (Annexe E, kN/m²), the terrain category of Tableau 4, the building's b, d and h (m) and the height z the dynamic pressure is taken at (null: h, 6.2.2.3), the table of Annexe C whose coefficients the building takes -- any building's of Tableaux 31 to 60b, 63 and 64 (D-06) -- and c_d (1.0 unless SIA 261/1 gives another, 6.3.5).

**What is computed** -- c_h of (12) at z, with its floors and category IV's switch (6.2.1.2), q_p = c_h · q_p0 (11); c_red of Figur 9 for the facade areas b·h (beta = b/h) and d·h (beta = d/h) -- each its own in the rows of a reference direction, the larger of the two in an oblique row (6.3.3, D-18 of spec 2026-10-12-audit-issues-47-48-49) --, 1.0 for the roof's and any other (6.3.2) -- **computed**, where the workbook reads it off a scroll bar; then
  * the **global forces** per unit of reference area, q_k = c_red · c_d · c_f · q_p (15), the largest and the smallest over the table's rows, for each force coefficient the table gives -- an area's factor (0.96·d·h) said in its header; a coefficient the norm marks «*» (computed directly, the platform canopies' Q1) is named and not computed;
  * the **local pressures**: on every surface the table names, c_pe · q_p (13) over the rows; and where the table gives internal coefficients, the net q_p · (c_pe − c_pi) -- for a closed building the workbook's envelope, uniformly distributed openings and a dominant opening in each wall; for an open one the surface's own c_pi.
A pair the norm writes ±x or a/b counts both its values. No Qt here.
"""

import json
import re
from pathlib import Path

import project
import validation
from domains._common import fail as _fail, is_number as _number, plain as _fmt  # one copy of the domains' helpers (spec 2026-10-19-base-saine-nettoyage, G4)
from domains import links  # a field that follows a variable of the export (spec 2026-10-11-variables-liees-champs-et-textes)
from norms import sia261_wind

# The domain's name, held here: domains/wind.py, the reader of the sheets, takes it from its calculation (ARCH-RISK-806, no import the other way)
DOMAIN = "wind-load"
SOURCE_SCHEMA = "wind-source"
SOURCE_SCHEMA_VERSION = "1.0"
# 1.1 is 1.0 with `links` (spec 2026-10-11-variables-liees-champs-et-textes, D-17): written only by a source that carries one, so a load following no variable is saved and exported as before
LINKED_SCHEMA_VERSION = "1.1"
SOURCE_SCHEMA_VERSIONS = (SOURCE_SCHEMA_VERSION, LINKED_SCHEMA_VERSION)
# The fields a variable may fill (REQ-009, issue #42) -- q_p0, the building's b, d, h, the height z and c_d --, with the unit each is written in. A load follows only another load or a «Formule» domain, the loads being computed first (links.LOADS, D-11). The lists take none.
LINKABLE = {links.SELF: {"q_p0": "kN/m²", "b": "m", "d": "m", "h": "m", "z": "m", "c_d": ""}}
FOLDER = "loads/wind"
SOURCE = "python:domains/wind_source.py"
NORM = "SIA 261"
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$")


def folder(here=None):
    return (here or project.current()).sources_dir / FOLDER


def source_paths(here=None):
    directory = folder(here)
    return sorted(directory.glob("*.json")) if directory.is_dir() else []


def new_source(cid):
    return {"schema_version": SOURCE_SCHEMA_VERSION, "id": cid, "name": "", "label": "", "group": "",
            "q_p0": 1.1, "terrain": "III", "b": 20.0, "d": 12.0, "h": 8.0, "z": None, "table": "33", "c_d": 1.0}


def stamp_version(src):
    """The schema_version a source is saved at: 1.1 where a field follows a variable, 1.0 where none does -- what Woodcore's window calls before it writes one."""
    src["schema_version"] = LINKED_SCHEMA_VERSION if links.is_linked(src, LINKABLE) else SOURCE_SCHEMA_VERSION
    return src


def check_source(src, where="loads/wind"):
    if not isinstance(src, dict):
        _fail(where, "a wind load is a JSON object")
    if src.get("schema_version") not in SOURCE_SCHEMA_VERSIONS:
        _fail(where, "schema_version is %r -- this reads %s" % (src.get("schema_version"), ", ".join(SOURCE_SCHEMA_VERSIONS)))
    if links.is_linked(src, LINKABLE) and src.get("schema_version") != LINKED_SCHEMA_VERSION:
        _fail(where, "follows a variable at schema_version %r -- a load with links is %r" % (src.get("schema_version"), LINKED_SCHEMA_VERSION))
    links.check_all(src, LINKABLE, lambda message: _fail(where, message), "the wind load", links.LOADS)
    try:
        validation.validate_structure(src, SOURCE_SCHEMA)
    except validation.ValidationError as exc:
        _fail(where, str(exc))
    if not ID_PATTERN.match(src.get("id") or ""):
        _fail(where, "id %r -- letters, digits and _ . + - only, starting with a letter or digit" % src.get("id"))
    check_fields(src, lambda _field, message: _fail(where, message))


def check_fields(src, fail):
    """The fields the calculation reads, each checked against SIA 261: `fail(field, message)` stops, naming the field -- a source names its file, a sheet of the workbook the cell the field is read from (domains/wind.py, ARCH-RISK-807)."""
    if not _number(src.get("q_p0")) or src["q_p0"] <= 0:
        fail("q_p0", "q_p0 is %r -- the reference dynamic pressure of Annexe E, kN/m², above 0" % (src.get("q_p0"),))
    try:
        sia261_wind.terrain(src.get("terrain"))
    except validation.ValidationError as exc:
        fail("terrain", str(exc))
    for key in ("b", "d", "h"):
        if not _number(src.get(key)) or src[key] <= 0:
            fail(key, "%s is %r -- a dimension of the building in m, above 0" % (key, src.get(key)))
    if src["h"] > 200:
        fail("h", "h is %g m -- SIA 261 6.1.2: the provisions apply to buildings up to 200 m" % src["h"])
    if src.get("z") is not None and (not _number(src["z"]) or src["z"] <= 0):
        fail("z", "z is %r -- the height above ground the dynamic pressure is taken at, m, or null for h" % (src.get("z"),))
    if src.get("table") not in sia261_wind.NUMBERS:
        fail("table", "table is %r -- the buildings of SIA 261 Annexe C are Tableaux %s" % (src.get("table"), ", ".join(sia261_wind.NUMBERS)))
    if not _number(src.get("c_d")) or src["c_d"] <= 0:
        fail("c_d", "c_d is %r -- the dynamic factor, above 0 (1.0, SIA 261 6.3.5)" % (src.get("c_d"),))


def warnings(src):
    """What is said about a valid source and the report never prints, [(code, params)]: `c_red_outside`, a facade's (h, beta) that Figur 9 does not draw -- c_red is then read at the nearest curve's end (sia261_wind.c_red, spec 2026-10-21-restes-issue-69, D-08)."""
    out = []
    for area, side in (("b·h", "b"), ("d·h", "d")):
        beta = src[side] / src["h"]
        if not sia261_wind.in_range(src["h"], beta):
            out.append(("c_red_outside", {"area": area, "h": src["h"], "beta": round(beta, 3), "ref": sia261_wind.clause()["c_red"]["norm_ref"]}))
    return out


def notes_of(src, where):
    """`warnings(src)` as the export's warnings (engine.Note), `where` the file or the sheet they are of."""
    import engine
    return [engine.Note("wind_" + code, "%s: the reference area %s has h = %g m and beta = %g, which SIA 261 %s does not draw -- c_red is read at the end of the nearest curve" % (where, p["area"], p["h"], p["beta"], p["ref"]),
                        where=where, **p) for code, p in warnings(src)]


def read_source(path):
    path = Path(path)
    where = "%s/%s" % (FOLDER, path.name)
    try:
        src = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _fail(where, "cannot be read as JSON -- %s" % exc)
    check_source(src, where)
    if src["id"] != path.stem:
        _fail(where, "id %r is not its file name %r -- the id is the file name" % (src["id"], path.stem))
    return src


def _values(value):
    """A cell as the values it stands for: a pair both, a number itself, an empty or a direct cell none."""
    if value is None or value == "direct":
        return []
    return list(value) if isinstance(value, list) else [value]


def area_label(column):
    factor = column.get("area_factor")
    return ("%s·%s" % (_fmt(factor), column["area"])) if factor else column["area"]


def c_red_of(column, cred, label=None):
    """Which reduction factor a force coefficient's reference area takes in the row `label`: b·h and d·h the facades' (6.3.3) -- each its own where the row's wind direction is less than 15° off a reference direction, the larger of the two in every other row (sia261_wind.oblique, D-18) --, any other -- the roof's, a canopy's -- 1.0 (6.3.2). Returns (factor, the var that holds it)."""
    if column["area"] not in ("b·h", "d·h"):
        return 1.0, None
    if label is not None and sia261_wind.oblique(label):
        return max(cred["bh"], cred["dh"]), "cred_max"
    return (cred["bh"], "cred_bh") if column["area"] == "b·h" else (cred["dh"], "cred_dh")


def global_forces(table, qp, cred, c_d):
    """[(column, name, max, min)] -- q_k = c_red · c_d · c_f · q_p over the table's rows, per force coefficient, c_red taken row by row (`c_red_of`); a column the norm computes directly («*») has max and min None."""
    out = []
    for i, column in enumerate(table["columns"]):
        if column["group"] not in ("cf", "cf_snow"):
            continue
        name = "%s%d" % ("cfs" if column["group"] == "cf_snow" else "cf", column["index"])
        if any(row["values"][i] == "direct" for row in table["rows"]):
            out.append((column, name, None, None))
            continue
        values = [c_red_of(column, cred, row["label"])[0] * c_d * v * qp for row in table["rows"] for v in _values(row["values"][i])]
        out.append((column, name, max(values) if values else None, min(values) if values else None))
    return out


def takes_max(table):
    """Whether a row of the table takes the larger c_red (6.3.3): a facade's force coefficient given in an oblique row."""
    return any(c_red_of(column, {"bh": 0, "dh": 0}, row["label"])[1] == "cred_max" and _values(row["values"][i])
               for i, column in enumerate(table["columns"]) if column["group"] in ("cf", "cf_snow") for row in table["rows"])


def local_pressures(table, qp):
    """[(surface label, {case: (max, min)})] -- on every surface the table names: c_pe · q_p (13) over its rows, and the net q_p · (c_pe − c_pi): with the openings of a closed building (rép., A-D), or the surface's own c_pi of an open one."""
    cols = table["columns"]
    index = {c["key"]: i for i, c in enumerate(cols)}
    openings = [c for c in cols if c["group"] == "cpi_opening"]
    own_cpi = {c["surface"]: index[c["key"]] for c in cols if c["group"] == "cpi"}
    out = []
    for column in cols:
        if column["group"] not in ("cpe", "cpe_local"):
            continue
        i = index[column["key"]]
        cases = {}
        external = [qp * v for row in table["rows"] for v in _values(row["values"][i])]
        if not external:
            continue
        cases["c_pe"] = (max(external), min(external))
        for opening in openings:
            j = index[opening["key"]]
            net = [qp * (e - p) for row in table["rows"] for e in _values(row["values"][i]) for p in _values(row["values"][j])]
            if net:
                cases[opening["opening"]] = (max(net), min(net))
        surface = column["surface"]
        if surface in own_cpi:
            j = own_cpi[surface]
            net = [qp * (e - p) for row in table["rows"] for e in _values(row["values"][i]) for p in _values(row["values"][j])]
            if net:
                cases["netto"] = (max(net), min(net))
        label = surface.replace("_", "") + (" (lokal)" if column["group"] == "cpe_local" else "")
        out.append((label, cases))
    return out


def build_instance(src, here=None, inputs=None):
    """One instance of `wind-load`: the site, the building, q_p, c_red and c_d as vars, the global forces as results printed by their table, the local pressures as a table after them. `inputs` says where each field of `src` was read, {field: source} -- a sheet's cells, `excel:<workbook>!<cell>` (domains/wind.py) --, a field it does not name being entered in Woodcore."""
    import engine
    clause = sia261_wind.clause()
    table = sia261_wind.table(src["table"])
    calc = engine.Calculation()
    where = "%s/%s.json" % (FOLDER, src["id"])
    inputs = inputs or {}

    def entered(field):
        return inputs.get(field, "entered:%s" % where)

    def var(name, value, symbol, unit, label, norm_ref, **more):
        calc.add_var(name=name, value=value, unit=unit, symbol=symbol, label=label,
                     source=more.pop("source", SOURCE), norm=NORM, norm_ref=norm_ref, **more)

    var("qp0", src["q_p0"], "q_(p 0)", "kN/m²", "Referenzwert des Staudrucks", "Anhang E", source=entered("q_p0"),
        description="Referenzwert des Staudrucks am Standort nach SIA 261.")
    var("b", src["b"], "b", "m", "Gebäudelänge", "6.3", source=entered("b"), group="geometrie", group_label="Gebäude Geometrie")
    var("d", src["d"], "d", "m", "Gebäudebreite", "6.3", source=entered("d"), group="geometrie")
    var("h", src["h"], "h", "m", "Gebäudehöhe", "6.3", source=entered("h"), group="geometrie")
    choices = [{"value": t["id"], "desc": "$z_g$ = %s m, $alpha_r$ = %s" % (_fmt(t["z_g"]), _fmt(t["alpha_r"]))} for t in clause["terrain"]["categories"]]
    var("gelaendekategorie", src["terrain"], '"Geländekategorie"', "", "Geländekategorie", clause["terrain"]["norm_ref"], source=entered("terrain"), choices=choices,
        description="Die Geländekategorie bestimmt die Gradientenhöhe und die Bodenrauigkeit des Windprofils.")
    z = src["z"] if src.get("z") is not None else src["h"]
    c_h, z_used, profile = sia261_wind.c_h(z, src["terrain"])
    t = sia261_wind.terrain(profile)
    var("zg", t["z_g"], "z_g", "m", "Gradientenhöhe", clause["terrain"]["norm_ref"], group_label="Gradientenhöhe")
    var("alpha_r", t["alpha_r"], "alpha_r", "", "Bodenrauigkeit", clause["terrain"]["norm_ref"], group_label="Bodenrauigkeit")
    var("z", z_used, "z", "m", "Höhe über Boden", clause["c_h"]["norm_ref"], group_label="Höhe über Boden",
        description="Höhe über Boden, für die der Staudruck bestimmt wird; die Norm setzt sie mindestens zu 5 m an (10 m in Geländekategorie IV).")
    ch = clause["c_h"]
    var("ch", c_h, "c_h", "", "Windprofilbeiwert", ch["norm_ref"], group_label="Windprofilbeiwert")
    calc.add_step(name="Windprofilbeiwert", result="ch", uses=["z", "zg", "alpha_r"],
                  formula="c_h = %s dot ((z / z_g)^alpha_r + %s)^2" % (_fmt(ch["factor"]), _fmt(ch["offset"])), norm=NORM, norm_ref="%s (%s)" % (ch["norm_ref"], ch["equation"]))
    cred = {"bh": sia261_wind.c_red(src["h"], src["b"] / src["h"]), "dh": sia261_wind.c_red(src["h"], src["d"] / src["h"])}
    var("cred_bh", cred["bh"], 'c_("red", "b/h")', "", "Reduktionsfaktor b", clause["c_red"]["norm_ref"], group_label="Reduktionsfaktor b",
        description="Reduktionsfaktor für die Bezugsfläche b·h, aus dem Verhältnis Länge (b) zu Höhe (h).")
    var("cred_dh", cred["dh"], 'c_("red", "d/h")', "", "Reduktionsfaktor d", clause["c_red"]["norm_ref"], group_label="Reduktionsfaktor d",
        description="Reduktionsfaktor für die Bezugsfläche d·h, aus dem Verhältnis Breite (d) zu Höhe (h).")
    if takes_max(table):
        var("cred_max", max(cred["bh"], cred["dh"]), 'c_("red", "max")', "", "Reduktionsfaktor schräge Windrichtung", clause["c_red"]["directions"]["norm_ref"], group_label="Reduktionsfaktor schräg",
            description="Für eine Windrichtung, die um 15° oder mehr von den Bezugsrichtungen abweicht, gilt der ungünstigere (grössere) der beiden Reduktionsfaktoren.")
    var("cd", src["c_d"], "c_d", "", "Dynamischer Faktor", clause["c_d"]["norm_ref"], source=entered("c_d"), group_label="dynamischer Faktor")
    qp = c_h * src["q_p0"]
    var("qp", qp, "q_p", "kN/m²", "Staudruck", "6.2 (11)")
    calc.add_step(name="Staudruck", result="qp", uses=["ch", "qp0"], formula="q_p = c_h dot q_(p 0)", bold=True, norm=NORM, norm_ref="6.2 (11)")
    var("tabelle", table["number"], '"Tabelle"', "", "Tabelle der Druckbeiwerte", "Anhang C", source=entered("table"),
        description="SIA 261, Anhang C, Tabelle %s, h : b : d = %s." % (table["number"], table["ratio"]))
    # --- the global forces: results, printed by their table
    results = []
    forces = global_forces(table, qp, cred, src["c_d"])
    computed = [(column, name, hi, lo) for column, name, hi, lo in forces if hi is not None]
    for column, name, hi, lo in computed:
        for kind, value in (("max", hi), ("min", lo)):
            key = "qk_%s_%s" % (kind, name)
            var(key, value, 'q_(k,"%s","%s")' % (kind, area_label(column)), "kN/m²",
                "%s globale Windkraft, Bezugsfläche %s" % ("Maximale" if kind == "max" else "Minimale", area_label(column)), "6.2.3.2")
            results.append(key)
    tables = []
    if computed:
        tables.append({
            "title": "Globale Windkräfte", "level": 1, "place": "below", "formula": 'q_k = c_"red" dot c_d dot c_f dot q_p', "norm": NORM, "norm_ref": "6.2.3.2",
            "source": SOURCE,
            "note": "SIA 261, Anhang C, Tabelle %s: $c_f$ ist der grösste bzw. kleinste globale Kraftbeiwert über die Windrichtungen; $c_\"red\"$ nach Figur 9 für b·h und d·h in den Windrichtungen 0°, 90° und 180°, der grössere der beiden in jeder anderen Windrichtung (6.3.3), 1.0 für jede andere Bezugsfläche (6.3.2). Negative Werte sind Sog." % table["number"],
            "columns": [{"label": "Globale Windkraft", "kind": "wide", "unit": "kN/m²"}, {"label": "", "kind": "math"}]
                       + [{"label": area_label(column), "kind": "value", "group": "Bezugsfläche"} for column, _n, _h, _l in computed],
            "rows": [["%s globale Windkraft" % word, "q_k ="] + ["qk_%s_%s" % (kind, name) for _c, name, _h, _l in computed]
                     for kind, word in (("max", "maximale"), ("min", "minimale"))],
        })
    # --- the local pressures
    local = local_pressures(table, qp)
    cases = []
    for _label, by_case in local:
        for case in by_case:
            if case not in cases:
                cases.append(case)
    words = {"c_pe": "aussen", "rep": "gleichmässig", "netto": "netto", "A": "Öffnung A", "B": "Öffnung B", "C": "Öffnung C", "D": "Öffnung D"}
    if local:
        tables.append({
            "title": "Lokale Windkräfte", "level": 2, "place": "below", "formula": 'q_k = q_p dot (c_"pe" - c_"pi")', "norm": NORM, "norm_ref": "6.2.2.1",
            "source": SOURCE,
            "note": "Grösster (max) und kleinster (min) Wert je Fläche über die Windrichtungen der Tabelle %s; aussen: $c_\"pe\" dot q_p$ allein; gleichmässig: gleichmässig verteilte Öffnungen; Öffnung A–D: dominante Öffnung in der Wand A, B, C bzw. D; netto: mit dem Innendruckbeiwert derselben Fläche. Negative Werte sind Sog." % table["number"],
            "columns": [{"label": "Lokale Windkraft", "kind": "wide", "unit": "kN/m²"}]
                       + [{"label": bound, "kind": "number", "group": words.get(case, case)} for case in cases for bound in ("max", "min")],
            "rows": [[label] + [v for case in cases for v in (by_case.get(case) or ("", ""))] for label, by_case in local],
        })
    return {"results": results, "tables": tables, **calc.to_dict()}
