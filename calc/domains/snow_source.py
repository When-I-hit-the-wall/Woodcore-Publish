"""Snow loads entered in Woodcore (issue #36): one roof per source, its characteristic snow loads computed here from SIA 261:2020 chapter 5 -- the values out of `norms/sia261_snow.py`, never from the Belastungsannahmen workbook, whose `SL-*` sheets stay read beside it (domains/snow.py, docs/domain/loads.md §3.3bis, decision D-04).

**A source** is `Woodcore-Datei/loads/snow/<id>.json` (schemas/snow-source.schema.json, 1.0): the altitude `h_0` and the correction of Anhang D (`correction`, m), the exposure (`exposure`: normal, exposed, sheltered -- 5.2.4) and C_T (`c_t`, 5.2.5), the roof (`roof`) and what it reads -- `length` and `width` (m) of a flat roof, `alpha_1` of a mono-pitch or a curved roof, `alpha_1` and `alpha_2` of a duo-pitch or a shed roof --, and whether the snow can slide off (`sliding`: possible, hindered).

**What is computed**, equation (9) q_k = mu · C_e · C_T · s_k with s_k of (10) at h_ref = h_0 + Δh, for the load models of Figur 3:
  * `flat` -- mu_1 = 0.8, or Figur 4 where the length and the width both exceed 20 m (5.3.5);
  * `mono` -- half a duo-pitch roof (5.3.2): mu_1(alpha) in model 1, and its half in model 2;
  * `duo` -- mu_11 = mu_1(alpha_1), mu_12 = mu_1(alpha_2): model 1 both, model 2 one side halved, then the other;
  * `shed` -- mu_11, mu_12 on the outer slopes and mu_2m = mu_2((alpha_1 + alpha_2)/2) in the valley (model 2);
  * `curved` -- the third column of Figur 3 (D-01): 0.8 uniform in model 1, and in model 2 two triangles, mu_3/2 and mu_3, mu_3 = mu_3(alpha) of Figur 2, over the part of the roof whose slope is under alpha_0 = 60°.
Where the sliding is hindered (5.3.4), mu_1 is 0.8 -- on every side and before any half is taken, which the workbook's N37/N38 forget (D-02). A roof steeper than 60° with the snow free to slide carries none (5.3.3), which Figur 2 already says. Above 2000 m these provisions do not apply (5.1.4): a source whose site h_0 is higher is computed all the same and `warnings` tells the tab, the report saying nothing (spec 2026-10-14-neige-vent-affichage-altitude) -- its h_0, not h_0 + Δh. **Said, not computed** (D-04 of spec 2026-10-12-audit-issues-47-48-49): the extra load at a height step of Figur 5 (5.3.6), where the source's `height_step` says the roof has one (schema 1.2), and the cornice of an overhanging roof above 800 m (5.3.7), each a var of its own whose description the report prints. No Qt here.
"""

import json
import re
from pathlib import Path

import project
import validation
from domains import links  # a field that follows a variable of the export (spec 2026-10-11-variables-liees-champs-et-textes)
from domains import snow, snow_svg
from norms import sia261_snow

DOMAIN = snow.DOMAIN
SOURCE_SCHEMA = "snow-source"
SOURCE_SCHEMA_VERSION = "1.0"
# 1.1 is 1.0 with `links` (spec 2026-10-11-variables-liees-champs-et-textes, D-17): written only by a source that carries one, so a load following no variable is saved and exported as before
LINKED_SCHEMA_VERSION = "1.1"
# 1.2 is 1.1 with `height_step` (spec 2026-10-12-audit-issues-47-48-49, D-19), written only where the roof has a height step: a superset of 1.1, so a stepped roof may follow a variable too. The versions are floors -- links need 1.1 at least, a height step 1.2 --, and a source without either is saved at 1.0 as before
STEP_SCHEMA_VERSION = "1.2"
SOURCE_SCHEMA_VERSIONS = (SOURCE_SCHEMA_VERSION, LINKED_SCHEMA_VERSION, STEP_SCHEMA_VERSION)
# The fields a variable may fill (REQ-009, issue #42) -- the altitude, c_t, the roof's length, width and slopes --, with the unit each is written in. A load follows only another load or a «Formule» domain, the loads being computed first (links.LOADS, D-11). The lists take none.
LINKABLE = {links.SELF: {"h_0": "m", "c_t": "", "length": "m", "width": "m", "alpha_1": "°", "alpha_2": "°"}}
FOLDER = "loads/snow"
SOURCE = "python:domains/snow_source.py"
NORM = "SIA 261"
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$")
ROOFS = ("flat", "mono", "duo", "shed", "curved")
SLIDING = ("possible", "hindered")
# The words the report prints for a roof and for the sliding: glossary terms, so a French report says them in French
ROOF_WORDS = {"flat": "Flachdach", "mono": "Pultdach", "duo": "Satteldach", "shed": "Sheddach", "curved": "Tonnendach"}
SLIDING_WORDS = {"possible": "möglich", "hindered": "behindert oder erschwert"}
# What each roof reads beyond the common fields
ROOF_FIELDS = {"flat": ("length", "width"), "mono": ("alpha_1",), "duo": ("alpha_1", "alpha_2"), "shed": ("alpha_1", "alpha_2"), "curved": ("alpha_1",)}


def _fail(where, message):
    raise validation.ValidationError("%s: %s" % (where, message))


def _number(value):
    return not isinstance(value, bool) and isinstance(value, (int, float))


def folder(here=None):
    return (here or project.current()).sources_dir / FOLDER


def source_paths(here=None):
    directory = folder(here)
    return sorted(directory.glob("*.json")) if directory.is_dir() else []


def new_source(cid):
    return {"schema_version": SOURCE_SCHEMA_VERSION, "id": cid, "name": "", "label": "", "group": "",
            "h_0": 500, "correction": 0, "exposure": "normal", "c_t": 1.0, "roof": "duo",
            "length": None, "width": None, "alpha_1": 30, "alpha_2": 30, "sliding": "possible"}


def stamp_version(src):
    """The schema_version a source is saved at: 1.2 where the roof has a height step, 1.1 where a field follows a variable, 1.0 where neither -- what Woodcore's window calls before it writes one. A height step that is false is not written at all (D-19), so a source without one stays byte for byte what it was."""
    if not src.get("height_step"):
        src.pop("height_step", None)
    if src.get("height_step"):
        src["schema_version"] = STEP_SCHEMA_VERSION
    else:
        src["schema_version"] = LINKED_SCHEMA_VERSION if links.is_linked(src, LINKABLE) else SOURCE_SCHEMA_VERSION
    return src


def check_source(src, where="loads/snow"):
    if not isinstance(src, dict):
        _fail(where, "a snow load is a JSON object")
    if src.get("schema_version") not in SOURCE_SCHEMA_VERSIONS:
        _fail(where, "schema_version is %r -- this reads %s" % (src.get("schema_version"), ", ".join(SOURCE_SCHEMA_VERSIONS)))
    if links.is_linked(src, LINKABLE) and src.get("schema_version") not in (LINKED_SCHEMA_VERSION, STEP_SCHEMA_VERSION):
        _fail(where, "follows a variable at schema_version %r -- a load with links is %r or %r" % (src.get("schema_version"), LINKED_SCHEMA_VERSION, STEP_SCHEMA_VERSION))
    if "height_step" in src and src.get("schema_version") != STEP_SCHEMA_VERSION:
        _fail(where, "height_step at schema_version %r -- a roof with a height step is %r" % (src.get("schema_version"), STEP_SCHEMA_VERSION))
    links.check_all(src, LINKABLE, lambda message: _fail(where, message), "the snow load", links.LOADS)
    try:
        validation.validate_structure(src, SOURCE_SCHEMA)
    except validation.ValidationError as exc:
        _fail(where, str(exc))
    if not ID_PATTERN.match(src.get("id") or ""):
        _fail(where, "id %r -- letters, digits and _ . + - only, starting with a letter or digit" % src.get("id"))
    c = sia261_snow.clause()
    if not _number(src.get("h_0")) or src["h_0"] < 0:
        _fail(where, "h_0 is %r -- the altitude above sea level, m" % (src.get("h_0"),))
    if src.get("correction") not in c["corrections"]["values"]:
        _fail(where, "correction is %r -- SIA 261 Anhang D gives %s m" % (src.get("correction"), ", ".join("%+g" % v for v in c["corrections"]["values"])))
    # a site above 5.1.4's limit is no defect of the file: it is computed, and `warnings` says so to the tab (spec 2026-10-14-neige-vent-affichage-altitude, REQ-003)
    sia261_snow.exposure(src.get("exposure"))
    if not _number(src.get("c_t")) or not 0 < src["c_t"] <= c["c_t"]["default"]:
        _fail(where, "c_t is %r -- C_T, above 0 and at most %s (5.2.5)" % (src.get("c_t"), c["c_t"]["default"]))
    if src.get("roof") not in ROOFS:
        _fail(where, "roof is %r -- %s" % (src.get("roof"), ", ".join(ROOFS)))
    if "height_step" in src and not isinstance(src["height_step"], bool):
        _fail(where, "height_step is %r -- true or false" % (src["height_step"],))
    if src.get("sliding") not in SLIDING:
        _fail(where, "sliding is %r -- %s" % (src.get("sliding"), ", ".join(SLIDING)))
    for key in ROOF_FIELDS[src["roof"]]:
        value = src.get(key)
        if key.startswith("alpha"):
            if not _number(value) or not 0 <= value <= 90:
                _fail(where, "%s is %r -- a slope in degrees, 0 to 90" % (key, value))
        elif not _number(value) or value <= 0:
            _fail(where, "%s is %r -- a plan dimension in m, above 0" % (key, value))


def warnings(src):
    """What the engineer is told about a valid source and the report never prints, [(code, params)] -- the tab words each code (`ld_warn_<code>`), so it compares nothing itself (spec 2026-10-14-neige-vent-affichage-altitude, REQ-004, D-04). `above_limit`: the site is above 5.1.4's limit, where the provisions of chapter 5 do not apply -- its altitude h_0, not the reference height h_0 + Δh of Anhang D (D-02 of spec 2026-10-12-audit-issues-47-48-49)."""
    limit = sia261_snow.clause()["max_altitude"]
    if _number(src.get("h_0")) and src["h_0"] > limit["value"]:
        return [("above_limit", {"h_0": src["h_0"], "limit": limit["value"], "ref": limit["norm_ref"]})]
    return []


def sketch(src):
    """The sketch of the disposition (snow_svg) the tab shows beside its results -- never in the export, the report printing no drawing of the snow (spec 2026-10-14-neige-vent-affichage-altitude, D-02, D-03)."""
    return snow_svg.render(src, {k: v[0] for k, v in coefficients(src).items()}, sia261_snow.clause()["curved"]["alpha_0"])


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


def _fmt(value):
    text = ("%.6f" % value).rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


def coefficients(src):
    """The roof's shape coefficients, {name: (value, why)} in the order the report prints them -- the arithmetic of Figur 2, 3 and 4 and of 5.3.2 to 5.3.5, apart from the loads so that a test reads it."""
    c = sia261_snow.clause()
    hindered = src["sliding"] == "hindered"

    def mu_1(alpha):
        value = sia261_snow.curve(c["mu_1"]["points"], alpha)
        return c["hindered"]["mu_1"] if hindered else value

    roof = src["roof"]
    if roof == "flat":
        value, why = mu_1(0), "Figur 2"
        side_min, side_max = min(src["length"], src["width"]), max(src["length"], src["width"])
        if side_min > c["large_flat"]["min_side"]:
            value, why = max(value, sia261_snow.curve(c["large_flat"]["points"], side_max)), "Figur 4"
        return {"mu_1": (value, why)}
    if roof == "mono":
        return {"mu_1": (mu_1(src["alpha_1"]), "Figur 2")}
    if roof in ("duo", "shed"):
        out = {"mu_11": (mu_1(src["alpha_1"]), "Figur 2"), "mu_12": (mu_1(src["alpha_2"]), "Figur 2")}
        if roof == "shed":
            out["mu_2m"] = (sia261_snow.curve(c["mu_2"]["points"], (src["alpha_1"] + src["alpha_2"]) / 2), "Figur 2")
        return out
    return {"mu_3": (sia261_snow.curve(c["mu_3"]["points"], src["alpha_1"]), "Figur 2")}


def build_instance(src, here=None):
    """One instance of `snow-load`: h_ref, s_k, C_e, C_T, the roof and its coefficients, and the loads of the two models of Figur 3. No drawing: `sketch` is the tab's (D-03)."""
    import engine
    c = sia261_snow.clause()
    calc = engine.Calculation()
    where = "%s/%s.json" % (FOLDER, src["id"])

    def var(name, value, symbol, unit, label, level, norm_ref, **more):
        calc.add_var(name=name, value=value, unit=unit, symbol=symbol, label=label, level=level,
                     source=more.pop("source", SOURCE), norm=NORM, norm_ref=norm_ref, **more)

    entered = "entered:%s" % where
    # --- the site
    var("h_0", src["h_0"], "h_0", "m", "Höhe ü. NN", 3, "5.2.6", source=entered, description="Höhe des Standorts über Meer.")
    var("korrektur", src["correction"], "Delta h", "m", "Korrektur Wert", 3, "Anhang D", source=entered,
        description="Höhenzuschlag auf die Höhe ü. NN nach SIA 261, Anhang D.")
    h_ref = src["h_0"] + src["correction"]
    var("h_ref", h_ref, 'h_"ref"', "m", "Bezugshöhe", 2, "5.2.6")
    calc.add_step(name="Bezugshöhe", level=3, result="h_ref", uses=["h_0", "korrektur"], formula='h_"ref" = h_0 + Delta h', norm=NORM, norm_ref="Anhang D")
    # --- the coefficients
    exposure = sia261_snow.exposure(src["exposure"])
    choices = [{"value": e["value"], "desc": e["label"]} for e in c["exposure"]["choices"]]
    var("ce", exposure["value"], "C_e", "", "Expositionsbeiwert", 3, c["exposure"]["norm_ref"], source=entered, choices=choices, group="beiwerte")
    var("ct", src["c_t"], "C_T", "", "Thermischer Beiwert", 3, c["c_t"]["norm_ref"], source=entered, group="beiwerte")
    # --- the roof
    var("dachform", ROOF_WORDS[src["roof"]], '"Dachform"', "", "Dachform / Lastmodell", 3, "Figur 3", source=entered)
    if src["roof"] == "flat":
        var("L", src["length"], "L", "m", "Gebäudelänge", 3, "5.3.5", source=entered, group="geometrie", group_label="Gebäude Geometrie")
        var("B", src["width"], "B", "m", "Gebäudebreite", 3, "5.3.5", source=entered, group="geometrie")
    else:
        var("alpha_1", src["alpha_1"], "alpha_1" if src["roof"] in ("duo", "shed") else "alpha", "°", "Dachneigung 1", 3, "Figur 3", source=entered, group="dachneigung")
        if src["roof"] in ("duo", "shed"):
            var("alpha_2", src["alpha_2"], "alpha_2", "°", "Dachneigung 2", 3, "Figur 3", source=entered, group="dachneigung")
    var("abgleiten", SLIDING_WORDS[src["sliding"]], '"Abgleiten des Schnees"', "", "Abgleiten des Schnees", 3, c["hindered"]["norm_ref"], source=entered,
        description="Ist das Abgleiten behindert oder erschwert, wird der Dachformbeiwert mu_1 mit 0.8 angesetzt (SIA 261, Ziffer 5.3.4).")
    # 5.3.6 and 5.3.7 are not computed: the report says where they apply (D-04) -- a stepped roof as its source states, a cornice for works above 800 m
    if src.get("height_step"):
        step = c["height_step"]
        var("hoehensprung", "Zusatzlast nach Figur 5", '"Höhensprung"', "", "Höhensprung", 1, step["norm_ref"], source=entered,
            description="Bei abgestuften Dächern oder bei einem Dach, das an ein höheres Bauwerk angrenzt, ist auf der unteren Dachfläche eine dreieckförmige Zusatzlast nach Figur 5 anzusetzen (Verdoppelung von mu_1 auf der Seite des Höhensprungs, Einflusslänge l_s = 2 h). Sie ist hier nicht berechnet.")
    cornice = c["cornice"]
    if src["h_0"] > cornice["min_altitude"]:
        var("schneeueberhang", "zu berücksichtigen", '"Schneeüberhang"', "", "Schneeüberhang", 1, cornice["norm_ref"],
            description="Für Bauwerke in dieser Höhenlage ist bei auskragenden Dachteilen ein Schneeüberhang als Linienlast am Dachrand zu berücksichtigen: Höhe und Breite gleich der halben Schneehöhe auf dem Dach (SIA 261, 5.3.7). Er ist hier nicht berechnet.")
    mus = coefficients(src)
    labels = {"mu_1": ("mu_1", "Dachformbeiwert"), "mu_11": ("mu_11", "Dachformbeiwert"), "mu_12": ("mu_12", "Dachformbeiwert 2"),
              "mu_2m": ("mu_(2m)", "Dachformbeiwert der Schneeanhäufung"), "mu_3": ("mu_3", "Dachformbeiwert")}
    for name, (value, why) in mus.items():
        var(name, value, labels[name][0], "", labels[name][1], 3, why, group="dachformbeiwerte")
    # --- the ground
    s_k, floored = sia261_snow.s_k(h_ref)
    sc = c["s_k"]
    var("s_k", s_k, "s_k", "kN/m²", "Charakteristischer Wert der Schneelast auf horizontalem Gelände", 2, sc["norm_ref"])
    calc.add_step(name="Charakteristischer Wert auf horizontalem Gelände", level=3, result="s_k", uses=["h_ref"],
                  formula='s_k = (1 + (h_"ref" / %s)^%s) dot %s >= %s thin "kN/m"^2' % (_fmt(sc["divisor"]), _fmt(sc["exponent"]), _fmt(sc["factor"]), _fmt(sc["min"])),
                  norm=NORM, norm_ref=sc["norm_ref"])
    # --- the loads of the two models
    base = exposure["value"] * src["c_t"] * s_k
    results = []

    def load(name, mu, symbol, mu_symbol, label, uses, half=False):
        value = mu * base / (2 if half else 1)
        var(name, value, symbol, "kN/m²", label, 1, "5.2.2")
        formula = "%s = %s%s dot C_e dot C_T dot s_k" % (symbol, mu_symbol, " / 2" if half else "")
        calc.add_step(name=label, level=1, result=name, uses=uses + ["ce", "ct", "s_k"], formula=formula, norm=NORM, norm_ref="5.2.2")
        results.append(name)

    lm1, lm2 = "Charakteristische Schneelast", "Charakteristische Schneelast, Lastmodell 2"
    roof = src["roof"]
    if roof == "flat":
        load("q_k1", mus["mu_1"][0], "q_k", "mu_1", lm1, ["mu_1"])
    elif roof == "mono":
        load("q_k1", mus["mu_1"][0], "q_(k,1)", "mu_1", lm1, ["mu_1"])
        load("q_k1h", mus["mu_1"][0], "q_(k,1,2)", "mu_1", lm2, ["mu_1"], half=True)
    elif roof in ("duo", "shed"):
        load("q_k11", mus["mu_11"][0], "q_(k,11)", "mu_11", lm1, ["mu_11"])
        load("q_k12", mus["mu_12"][0], "q_(k,12)", "mu_12", lm1, ["mu_12"])
        if roof == "duo":
            load("q_k11h", mus["mu_11"][0], "q_(k,11,2)", "mu_11", lm2, ["mu_11"], half=True)
            load("q_k12h", mus["mu_12"][0], "q_(k,12,2)", "mu_12", lm2, ["mu_12"], half=True)
        else:
            load("q_k2m", mus["mu_2m"][0], "q_(k,2m)", "mu_(2m)", "Charakteristische Schneelast der Schneeanhäufung", ["mu_2m"])
    else:
        load("q_k1", c["curved"]["model_1"], "q_(k,1)", _fmt(c["curved"]["model_1"]), lm1, [])
        load("q_k3", mus["mu_3"][0], "q_(k,3)", "mu_3", lm2, ["mu_3"])
        load("q_k3h", mus["mu_3"][0], "q_(k,3,2)", "mu_3", lm2, ["mu_3"], half=True)
    # no `figures` and no `_files`: the report prints no drawing of the snow, and the tab asks `sketch` for its own (D-02, D-03)
    return {"results": results, **calc.to_dict()}
