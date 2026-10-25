"""Wind loads entered in Woodcore (issue #37): one building per source, its wind computed here from SIA 261:2020 chapter 6 and Annexe C -- every coefficient out of `norms/sia261_wind.py`. The one calculation of the wind and, since issue #109, its one way in: the `WL-*` sheets of the Belastungsannahmen workbooks are read no more (decision D-33; docs/domain/loads.md §3.3quater).

**A source** is `Woodcore-Datei/loads/wind/<id>.json` (schemas/wind-source.schema.json, 1.0; 1.1 with links; 1.2 with the openings' case): q_p0 at the site (Annexe E, kN/m²), the terrain category of Tableau 4, the building's b, d and h (m) and the height z the dynamic pressure is taken at (null: h, 6.2.2.3), the table of Annexe C whose coefficients the building takes -- any building's of Tableaux 31 to 60b, 63 and 64 (D-06) -- and c_d (1.0 unless SIA 261/1 gives another, 6.3.5).

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
from domains._common import fail_first as _fail_first, fail as _fail, is_number as _number, plain as _fmt  # one copy of the domains' helpers (spec 2026-10-19-base-saine-nettoyage, G4)
from domains import links  # a field that follows a variable of the export (spec 2026-10-11-variables-liees-champs-et-textes)
from domains import wind_forces  # the arithmetic and where each number came from (spec 2026-10-23-onglet-vent-briques)
from norms import sia261_wind

DOMAIN = "wind-load"
# What the registry writes of the domain (registry.DOMAIN_MODULES, docs/domain/calculation-domains.md §3.3): read off this module since the sheets' reader went (issue #109, ARCH-001)
LABEL = "Windlast"
ENGINE = "python"
ACTION = "variable"  # SIA 260: a variable action (Q), as opposed to a permanent one (G)
SOURCE_SCHEMA = "wind-source"
SOURCE_SCHEMA_VERSION = "1.0"
# 1.1 is 1.0 with `links` (spec 2026-10-11-variables-liees-champs-et-textes, D-17): written only by a source that carries one, so a load following no variable is saved and exported as before
LINKED_SCHEMA_VERSION = "1.1"
# 1.2 is 1.1 with `openings`, the openings' case the local pressures take (spec 2026-10-23-onglet-vent-briques, CON-002): what a new source is written at; 1.0 and 1.1 are read, their openings uniformly distributed with a warning (D-24)
OPENINGS_SCHEMA_VERSION = "1.2"
SOURCE_SCHEMA_VERSIONS = (SOURCE_SCHEMA_VERSION, LINKED_SCHEMA_VERSION, OPENINGS_SCHEMA_VERSION)
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
    return {"schema_version": OPENINGS_SCHEMA_VERSION, "id": cid, "name": "", "label": "", "group": "",
            "q_p0": 1.1, "terrain": "III", "b": 20.0, "d": 12.0, "h": 8.0, "z": None, "table": "33", "c_d": 1.0, "openings": "rep"}


def stamp_version(src):
    """The schema_version a source is saved at: 1.2 where it holds its openings' case, else 1.1 where a field follows a variable, 1.0 where none does -- what Woodcore's window calls before it writes one."""
    src["schema_version"] = OPENINGS_SCHEMA_VERSION if "openings" in src else LINKED_SCHEMA_VERSION if links.is_linked(src, LINKABLE) else SOURCE_SCHEMA_VERSION
    return src


def check_source(src, where="loads/wind"):
    if not isinstance(src, dict):
        _fail(where, "a wind load is a JSON object")
    if src.get("schema_version") not in SOURCE_SCHEMA_VERSIONS:
        _fail(where, "schema_version is %r -- this reads %s" % (src.get("schema_version"), ", ".join(SOURCE_SCHEMA_VERSIONS)))
    if links.is_linked(src, LINKABLE) and src.get("schema_version") not in (LINKED_SCHEMA_VERSION, OPENINGS_SCHEMA_VERSION):
        _fail(where, "follows a variable at schema_version %r -- a load with links is %r or %r" % (src.get("schema_version"), LINKED_SCHEMA_VERSION, OPENINGS_SCHEMA_VERSION))
    if "openings" in src and src.get("schema_version") != OPENINGS_SCHEMA_VERSION:
        _fail(where, "holds its openings at schema_version %r -- a load with openings is %r" % (src.get("schema_version"), OPENINGS_SCHEMA_VERSION))
    links.check_all(src, LINKABLE, lambda message: _fail(where, message), "the wind load", links.LOADS)
    try:
        validation.validate_structure(src, SOURCE_SCHEMA)
    except validation.ValidationError as exc:
        _fail(where, str(exc))
    if not ID_PATTERN.match(src.get("id") or ""):
        _fail(where, "id %r -- letters, digits and _ . + - only, starting with a letter or digit" % src.get("id"))
    check_fields(src, lambda _field, message: _fail(where, message))


def _problems(src):
    """Every field the calculation cannot read, checked against SIA 261, in the form's order: [(field, code, params, sentence)] -- the one place the wind's rules «red» are written (spec 2026-10-23-onglet-vent-briques, REQ-009, ARCH-RISK-015): `check_fields` refuses on the first, `messages` says them all. A source's id is the tab's identity's to say."""
    out = []

    def bad(field, code, sentence, **params):
        out.append((field, code, params, sentence))
    if not _number(src.get("q_p0")) or src["q_p0"] <= 0:
        bad("q_p0", "q_p0", "q_p0 is %r -- the reference dynamic pressure of Annexe E, kN/m², above 0" % (src.get("q_p0"),), ref="6.2.1.3")
    try:
        sia261_wind.terrain(src.get("terrain"))
    except validation.ValidationError as exc:
        bad("terrain", "terrain", str(exc))
    for key in ("b", "d", "h"):
        if not _number(src.get(key)) or src[key] <= 0:
            bad(key, "dimension", "%s is %r -- a dimension of the building in m, above 0" % (key, src.get(key)), key=key)
    scope = sia261_wind.clause()["scope"]
    if _number(src.get("h")) and src["h"] > scope["max_height"]:
        bad("h", "too_high", "h is %g m -- SIA 261 %s: the provisions apply to buildings up to %g m" % (src["h"], scope["norm_ref"], scope["max_height"]), h=src["h"], limit=scope["max_height"], ref=scope["norm_ref"])
    if src.get("z") is not None and (not _number(src["z"]) or src["z"] <= 0):
        bad("z", "z", "z is %r -- the height above ground the dynamic pressure is taken at, m, or null for h" % (src.get("z"),))
    if src.get("table") not in sia261_wind.NUMBERS:
        bad("table", "table", "table is %r -- the buildings of SIA 261 Annexe C are Tableaux %s" % (src.get("table"), ", ".join(sia261_wind.NUMBERS)))
    if not _number(src.get("c_d")) or src["c_d"] <= 0:
        bad("c_d", "c_d", "c_d is %r -- the dynamic factor, above 0 (1.0, SIA 261 6.3.5)" % (src.get("c_d"),), ref="6.3.5")
    return out


def check_fields(src, fail):
    """The fields the calculation reads, each checked against SIA 261: `fail(field, message)` stops on the first one wrong (`_problems`), naming the field, the caller naming the source's file."""
    _fail_first(_problems(src), fail)


# How far the building's proportions h : b : d may stand from its table's before the tab says so -- Woodcore's own threshold, not the norm's (issue #100, T45): 1.5 times, either way, of h/d or b/d
RATIO_SPREAD = 1.5
# The messages the export says too (engine.Note), the others being the tab's alone: a facade Figur 9 does not draw (spec 2026-10-21-restes-issue-69, D-08), the norm's figure not cut, its edition not shipped (spec 2026-10-23-onglet-vent-briques, REQ-017)
EXPORT_CODES = ("c_red_outside", "no_library")
# The file of the wind's excerpts of SIA 261 -- where its figures of Annexe C are cut from (spec 2026-10-23-onglet-vent-briques, ARCH-012)
EXCERPTS = "sia261-2020-wind-excerpts"
# The editions a figure of the norm is cut out of, one file each; English reads German
FIGURE_EDITIONS = ("fr", "de")
RATIO = re.compile(r"^\s*([\d,.]+)\s*:\s*([\d,.]+)\s*:\s*([\d,.]+)\s*$")


def messages(src):
    """What the wind's tab says of a source (spec 2026-10-23-onglet-vent-briques, REQ-009): every field it cannot read, an `error` that blocks the calculation (`_problems`), else what is only said, `info`, the calculation made -- [contracts.Message], each on its field. The tab words each code (`<prefix>msg_<code>`) and compares nothing itself.

    `z_min` -- z below 6.2.1.2's floor, raised to it; `iv_as_iii` -- category IV above 30 m, read on category III's profile (6.2.1.2); `c_d_default` -- c_d = 1.0 for a building above 6.3.5's 15 m, which then holds only for the buildings it names; `c_red_outside` -- a facade's (h, beta) Figur 9 does not draw, c_red read at the nearest curve's end (D-08); `ratio` -- proportions more than `RATIO_SPREAD` times from the table's; `direct` -- a force coefficient the norm marks «*», computed directly and not here; `no_area` -- a reference area with a dimension the building is not given by (h1, d1, hs), its force per m² only; `openings_default` -- a source of 1.0 or 1.1, which holds no openings' case, read with uniformly distributed openings until one is chosen (D-24)."""
    from domains.contracts import Message
    out = [Message(code, field, "error", params) for field, code, params, _sentence in _problems(src)]
    if out:
        return out
    clause = sia261_wind.clause()
    table = sia261_wind.table(src["table"])
    z = src["z"] if src.get("z") is not None else src["h"]
    _c_h, z_used, profile = sia261_wind.c_h(z, src["terrain"])
    z_field = "z" if src.get("z") is not None else "h"
    ref_h = clause["c_h"]["norm_ref"]
    if z < z_used:
        out.append(Message("z_min", z_field, "info", {"z": z, "z_min": z_used, "ref": ref_h}))
    if profile != src["terrain"]:
        out.append(Message("iv_as_iii", "terrain", "info", {"above": clause["c_h"]["iv_as_iii_above"], "ref": ref_h}))
    c_d = clause["c_d"]
    if src["h"] > c_d["building_height"] and src["c_d"] == c_d["default"]:
        out.append(Message("c_d_default", "c_d", "info", {"h": src["h"], "limit": c_d["building_height"], "ref": c_d["norm_ref"]}))
    for code, params in _c_red_outside(src):
        out.append(Message(code, "h", "info", params))
    m = RATIO.match(table.get("ratio") or "")
    if m:
        h_, b_, d_ = (float(x.replace(",", ".")) for x in m.groups())
        mine, norm = (src["h"] / src["d"], src["b"] / src["d"]), (h_ / d_, b_ / d_)
        if any(max(x / y, y / x) > RATIO_SPREAD for x, y in zip(mine, norm)):
            out.append(Message("ratio", "b", "info", {"entered": "%s : %s : 1" % (_fmt(round(mine[0], 2)), _fmt(round(mine[1], 2))), "table": table["number"], "ratio": table["ratio"]}))
    forces = [c for c in table["columns"] if c["group"] in ("cf", "cf_snow")]
    if any(row["values"][i] == "direct" for i, c in enumerate(table["columns"]) if c in forces for row in table["rows"]):
        out.append(Message("direct", "table", "info", {"table": table["number"]}))
    if any(sia261_wind.area(c, src["b"], src["d"], src["h"]) is None for c in forces):
        out.append(Message("no_area", "table", "info", {"table": table["number"], "areas": ", ".join(sorted({area_label(c) for c in forces if sia261_wind.area(c, 1, 1, 1) is None}))}))
    if "openings" not in src and wind_forces.chosen_opening(table, wind_forces.DEFAULT_OPENING):
        out.append(Message("openings_default", "openings", "info", {"opening": wind_forces.DEFAULT_OPENING}))
    missing = [lang for lang in FIGURE_EDITIONS if _edition_pdf(table["number"], lang) is None]
    if missing:
        out.append(Message("no_library", "table", "info", {"table": table["number"], "files": ", ".join(_excerpt(table["number"], lang).file for lang in missing)}))
    return out


def _excerpt(number, lang):
    from norms import excerpts
    return excerpts.excerpt(EXCERPTS, "fig" + number, lang)


def _edition_pdf(number, lang):
    """The shipped PDF the figure of Tableau `number` is cut out of in `lang`, None where it is not there (REQ-004)."""
    return _excerpt(number, lang).pdf()


_CUT = {}


def figure_pdf(number, lang):
    """The figure of Tableau `number` alone, cut out of its edition's page by its box (annex.crop: a one-page PDF whose page is the frame, vector, without Qt) -- once per edition, kept; None where the edition is not shipped (REQ-017, D-28)."""
    key = (number, lang)
    if key not in _CUT:
        path = _edition_pdf(number, lang)
        if path is None:
            return None
        from pypdf import PdfReader
        from domains import annex
        e = _excerpt(number, lang)
        x0, y0, x1, y1 = e.box
        _CUT[key] = annex.crop(PdfReader(str(path)), e.page, [x0, y0, x1 - x0, y1 - y0])
    return _CUT[key]


def _c_red_outside(src):
    """A facade's (h, beta) that Figur 9 does not draw -- c_red is then read at the nearest curve's end (sia261_wind.c_red, spec 2026-10-21-restes-issue-69, D-08)."""
    out = []
    for area, side in (("b·h", "b"), ("d·h", "d")):
        beta = src[side] / src["h"]
        if not sia261_wind.in_range(src["h"], beta):
            out.append(("c_red_outside", {"area": area, "h": src["h"], "beta": round(beta, 3), "ref": sia261_wind.clause()["c_red"]["norm_ref"]}))
    return out


def warnings(src):
    """What the export says of a valid source and the report never prints, [(code, params)]: the `messages` of `EXPORT_CODES` -- a facade Figur 9 does not draw."""
    return [(m.code, m.params) for m in messages(src) if m.code in EXPORT_CODES]


def notes_of(src, where):
    """`warnings(src)` as the export's warnings (engine.Note), `where` the file they are of."""
    import engine
    said = {"c_red_outside": lambda p: "%s: the reference area %s has h = %g m and beta = %g, which SIA 261 %s does not draw -- c_red is read at the end of the nearest curve" % (where, p["area"], p["h"], p["beta"], p["ref"]),
            "no_library": lambda p: "%s: Tableau %s's figure of SIA 261 is not cut -- %s is not in norm-library/; the file is written without it" % (where, p["table"], p["files"])}
    return [engine.Note("wind_" + code, said[code](p), where=where, **p) for code, p in warnings(src)]


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


def area_label(column):
    factor = column.get("area_factor")
    return ("%s·%s" % (_fmt(factor), column["area"])) if factor else column["area"]


# A local pressures' table is cut into blocks of at most this many surfaces, balanced (spec 2026-10-23-onglet-vent-briques, REQ-014, REQ-020): a table wide and low rather than high
BLOCK_SURFACES = 12
# The words of an openings' case over the local pressures (the glossary's German, the file's language by calc/i18n/strings.json)
OPENING_WORDS = {"rep": "Öffnungen gleichmässig verteilt", "A": "Dominante Öffnung in der Wand A", "B": "Dominante Öffnung in der Wand B",
                 "C": "Dominante Öffnung in der Wand C", "D": "Dominante Öffnung in der Wand D"}
OWN_CPI_WORDS = "Innendruckbeiwert jeder Fläche"


def surface_blocks(items, most=BLOCK_SURFACES):
    """`items` cut into ⌈n / most⌉ runs as equal as can be, in order -- 29 surfaces into 10, 10, 9, never 12, 12, 5."""
    count = -(-len(items) // most) or 1
    size, extra = divmod(len(items), count)
    out, at = [], 0
    for k in range(count):
        n = size + (1 if k < extra else 0)
        out.append(items[at:at + n])
        at += n
    return out


def build_instance(src, here=None):
    """One instance of `wind-load`: the site, the building, q_p, c_red and c_d as vars, the global forces as results printed by their table, the local pressures as a table after them. Each input's provenance is the source it was entered in, `entered:loads/wind/<id>.json`."""
    import engine
    clause = sia261_wind.clause()
    table = sia261_wind.table(src["table"])
    calc = engine.Calculation()
    where = "%s/%s.json" % (FOLDER, src["id"])
    def entered(_field):
        return "entered:%s" % where

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
    a = wind_forces.analysis(src)
    cred = a["cred"]
    var("cred_bh", cred["bh"], 'c_("red", "b/h")', "", "Reduktionsfaktor b", clause["c_red"]["norm_ref"], group_label="Reduktionsfaktor b",
        description="Reduktionsfaktor für die Bezugsfläche b·h, aus dem Verhältnis Länge (b) zu Höhe (h).")
    var("cred_dh", cred["dh"], 'c_("red", "d/h")', "", "Reduktionsfaktor d", clause["c_red"]["norm_ref"], group_label="Reduktionsfaktor d",
        description="Reduktionsfaktor für die Bezugsfläche d·h, aus dem Verhältnis Breite (d) zu Höhe (h).")
    if any(r["c_red_of"] == "max" and r["values"] for f in a["forces"] for r in f["rows"]):
        var("cred_max", cred["max"], 'c_("red", "max")', "", "Reduktionsfaktor schräge Windrichtung", clause["c_red"]["directions"]["norm_ref"], group_label="Reduktionsfaktor schräg",
            description="Für eine Windrichtung, die um 15° oder mehr von den Bezugsrichtungen abweicht, gilt der ungünstigere (grössere) der beiden Reduktionsfaktoren.")
    var("cd", src["c_d"], "c_d", "", "Dynamischer Faktor", clause["c_d"]["norm_ref"], source=entered("c_d"), group_label="dynamischer Faktor")
    qp = a["q_p"]
    var("qp", qp, "q_p", "kN/m²", "Staudruck", "6.2 (11)")
    calc.add_step(name="Staudruck", result="qp", uses=["ch", "qp0"], formula="q_p = c_h dot q_(p 0)", bold=True, norm=NORM, norm_ref="6.2 (11)")
    var("tabelle", table["number"], '"Tabelle"', "", "Tabelle der Druckbeiwerte", "Anhang C", source=entered("table"),
        description="SIA 261, Anhang C, Tabelle %s, h : b : d = %s." % (table["number"], table["ratio"]))
    # --- the global forces: q_k per m² under their names of always (the sections cite them, loads_names compares them), Q_k in kN beside them where the area is known (REQ-002, REQ-013)
    computed = [f for f in a["forces"] if not f["direct"]]
    results, per_m2 = [], []
    for f in computed:
        label = area_label(f["column"])
        for kind in ("max", "min"):
            key = "qk_%s_%s" % (kind, f["name"])
            var(key, f[kind]["q"], 'q_(k,"%s","%s")' % (kind, label), "kN/m²", "%s globale Windlast je m², Bezugsfläche %s" % ("Maximale" if kind == "max" else "Minimale", label), "6.2.3.2")
            per_m2.append(key)
    forces = []
    for f in computed:
        if f["area"] is None:
            continue
        label = area_label(f["column"])
        for kind in ("max", "min"):
            key = "Qk_%s_%s" % (kind, f["name"])
            var(key, f[kind]["Q"], 'Q_(k,"%s","%s")' % (kind, label), "kN", "%s globale Windkraft, Bezugsfläche %s" % ("Maximale" if kind == "max" else "Minimale", label), "6.2.3.2")
            forces.append(key)
    results = per_m2 + forces
    tables = []
    if computed:
        areas = ", ".join("%s = %s m²" % (area_label(f["column"]), _fmt(round(f["area"], 1))) for f in computed if f["area"] is not None)
        alone = ", ".join(area_label(f["column"]) for f in computed if f["area"] is None)
        note = "$Q_k = c_\"red\" dot c_d dot c_f dot q_p dot A_\"ref\"$ (SIA 261, 6.2.3.2); $A_\"ref\"$: %s." % (areas or "–")
        if alone:
            note += " Ohne Bezugsfläche aus den Gebäudeabmessungen, je m²: %s." % alone
        tables.append({
            "title": "Globale Windkräfte", "level": 1, "place": "below", "norm": NORM, "norm_ref": "6.2.3.2", "source": SOURCE, "note": note + " Negative Werte sind Sog.",
            "columns": [{"label": "Globale Windkraft", "kind": "wide", "unit": "kN"}, {"label": "", "kind": "math"}]
                       + [{"label": area_label(f["column"]), "kind": "value", "group": "Bezugsfläche", "decimals": 1 if f["area"] is not None else 3, **({} if f["area"] is not None else {"unit": "kN/m²"})}
                          for f in computed],
            "rows": [["%s globale Windkraft" % word, "Q_k ="] + ["%s_%s_%s" % ("Qk" if f["area"] is not None else "qk", kind, f["name"]) for f in computed]
                     for kind, word in (("max", "maximale"), ("min", "minimale"))],
        })
    # --- the local pressures of the openings' case chosen, transposed -- a column a surface, a row max and a row min --, in blocks of at most BLOCK_SURFACES (REQ-014)
    local = a["local"]
    if local:
        group = OPENING_WORDS.get(a["opening"]) if a["opening"] else (OWN_CPI_WORDS if any(s["own_c_pi"] for s in local) else "")
        runs = surface_blocks(local)
        for k, run in enumerate(runs):
            table_k = {
                "title": "", "level": 2, "place": "below", "norm": NORM, "norm_ref": "6.2.2.1", "source": SOURCE, "widths": "first-auto",
                "columns": [{"label_math": "q_k", "label": "q_k", "kind": "wide", "unit": "kN/m²", "strong": True}]
                           + [{"label": s["surface"].replace("_", ""), "kind": "number", "group": group, "decimals": 3} for s in run],
                "rows": [["max"] + [s["max"]["q"] for s in run], ["min"] + [s["min"]["q"] for s in run]],
            }
            if k == 0:
                table_k["title"] = "Lokale Windkräfte"   # a block after the first carries an empty title: the schema asks for one, the file prints none
            if k == len(runs) - 1:
                named = [s["surface"] for s in local if s["group"] == "loc"]
                localised = "; lokale Flächen (Figur 22): %s" % ", ".join(named) if named else ""
                table_k["note"] = ("Grösster (max) und kleinster (min) Wert von $q_k = q_p dot (c_d dot c_\"pe\" - c_\"pi\")$ je Fläche über die Windrichtungen der Tabelle %s%s. Negative Werte sind Sog." % (table["number"], localised))
            tables.append(table_k)
    out = {"results": results, "tables": tables, **calc.to_dict()}
    # the figure of the table of Annexe C, cut out of the norm at the export and printed from level 3 on (REQ-017, REQ-018, D-28, D-29): one file an edition, under Variable-loads/Wind/Exports/Figures/
    cut = {lang: figure_pdf(table["number"], lang) for lang in FIGURE_EDITIONS}
    if all(cut.values()):
        place = engine.Figures(here.data_dir if here is not None else None, DOMAIN, here)
        files = {lang: place.name("%s-fig-%s.pdf" % (src["id"], lang)) for lang in FIGURE_EDITIONS}
        out["figures"] = [{"file": files["de"], "files": files, "title": "Figur der Tabelle %s (SIA 261, Anhang C)" % table["number"], "level": 3, "from_level": 3}]
        out["_files"] = {files[lang]: cut[lang] for lang in FIGURE_EDITIONS}
    return out


# --- what the wind's tab is described by (spec 2026-10-23-onglet-vent-briques, V5): its declaration, its fields shown, its results, its blocks, its links, Figur 9 -- domains/wind_view.py
from domains.wind_view import blocks, chart, declaration, key_links, results, visible_fields  # noqa: E402,F401
