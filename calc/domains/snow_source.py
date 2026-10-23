"""Snow loads entered in Woodcore (issue #36): one roof per source, its characteristic snow loads computed here from SIA 261:2020 chapter 5 -- the values out of `norms/sia261_snow.py`. Since v0.120 the one calculation of the snow: an `SL-*` sheet of the Belastungsannahmen workbook is read for its inputs alone and computed here too (domains/snow.py, spec 2026-10-21-restes-issue-69, REQ-001, ARCH-002; docs/domain/loads.md §3.3bis).

**A source** is `Woodcore-Datei/loads/snow/<id>.json` (schemas/snow-source.schema.json, 1.0): the altitude `h_0` and the correction of Anhang D (`correction`, m), the exposure (`exposure`: normal, exposed, sheltered -- 5.2.4) and C_T (`c_t`, 5.2.5), the roof (`roof`) and what it reads -- `length` and `width` (m) of a flat roof, `alpha_1` of a mono-pitch or a curved roof, `alpha_1` and `alpha_2` of a duo-pitch or a shed roof --, and whether the snow can slide off (`sliding`: possible, hindered).

**What is computed**, equation (9) q_k = mu · C_e · C_T · s_k with s_k of (10) at h_ref = h_0 + Δh, for the load models of Figur 3:
  * `flat` -- mu_1 = 0.8, or Figur 4 where the length and the width both exceed 20 m (5.3.5);
  * `mono` -- half a duo-pitch roof (5.3.2): mu_1(alpha) in model 1, and its half in model 2;
  * `duo` -- mu_11 = mu_1(alpha_1), mu_12 = mu_1(alpha_2): model 1 both, model 2 one side halved, then the other;
  * `shed` -- mu_11, mu_12 on the outer slopes and mu_2m = mu_2((alpha_1 + alpha_2)/2) in the valley (model 2);
  * `curved` -- the third column of Figur 3 (D-01): 0.8 uniform in model 1, and in model 2 two triangles, mu_3/2 and mu_3, mu_3 = mu_3(alpha) of Figur 2, over the part of the roof whose slope is under alpha_0 = 60°.
Where the sliding is hindered (5.3.4), mu_1 is 0.8 -- on every side and before any half is taken, which the workbook's N37/N38 forget (D-02). A roof steeper than 60° with the snow free to slide carries none (5.3.3), which Figur 2 already says. Above 2000 m these provisions do not apply (5.1.4): a source whose site h_0 is higher is computed, `messages` says so to the tab in orange and the export in a note, the report saying nothing (spec 2026-10-14-neige-vent-affichage-altitude; spec 2026-10-22-onglet-neige-type, D-19) -- its h_0, not h_0 + Δh. **What the tab says** -- every field it cannot read, and what is only said -- is `messages`, each with its field and severity (contracts.Message); the tab's form is `declaration()` (calc/tools/calc_tab.py draws it). **Said, not computed** (D-04 of spec 2026-10-12-audit-issues-47-48-49): the extra load at a height step of Figur 5 (5.3.6), where the source's `height_step` says the roof has one (schema 1.2), and the cornice of an overhanging roof above 800 m (5.3.7), each a var of its own whose description the report prints. No Qt here.
"""

import json
import re
from pathlib import Path

import project
import validation
from domains._common import fail as _fail, is_number as _number, plain as _fmt  # one copy of the domains' helpers (spec 2026-10-19-base-saine-nettoyage, G4)
from domains import links  # a field that follows a variable of the export (spec 2026-10-11-variables-liees-champs-et-textes)
from domains import snow_svg
from norms import sia261_snow

# The domain's name, held here: domains/snow.py, the reader of the sheets, takes it from its calculation (ARCH-RISK-806, no import the other way)
DOMAIN = "snow-load"
SOURCE_SCHEMA = "snow-source"
SOURCE_SCHEMA_VERSION = "1.0"
# 1.1 is 1.0 with `links` (spec 2026-10-11-variables-liees-champs-et-textes, D-17): written only by a source that carries one, so a load following no variable is saved and exported as before
LINKED_SCHEMA_VERSION = "1.1"
# 1.2 is 1.1 with `height_step` (spec 2026-10-12-audit-issues-47-48-49, D-19), written only where the roof has a height step: a superset of 1.1, so a stepped roof may follow a variable too. The versions are floors -- links need 1.1 at least, a height step 1.2 --, and a source without either is saved at 1.0 as before
STEP_SCHEMA_VERSION = "1.2"
# 1.3 is 1.2 with a free C_e (spec 2026-10-22-onglet-neige-type, REQ-021): `exposure: "custom"` and its number `c_e`, written only where the engineer types one -- the three buttons of 5.2.4 keep a source at its version
CUSTOM_SCHEMA_VERSION = "1.3"
SOURCE_SCHEMA_VERSIONS = (SOURCE_SCHEMA_VERSION, LINKED_SCHEMA_VERSION, STEP_SCHEMA_VERSION, CUSTOM_SCHEMA_VERSION)
CUSTOM = "custom"   # the exposure of a free C_e
# The fields a variable may fill (REQ-009, issue #42) -- the altitude, c_t, the roof's length, width and slopes --, with the unit each is written in. A load follows only another load or a «Formule» domain, the loads being computed first (links.LOADS, D-11). The lists take none.
LINKABLE = {links.SELF: {"h_0": "m", "c_t": "", "length": "m", "width": "m", "alpha_1": "°", "alpha_2": "°", "c_e": ""}}   # c_e: a free C_e (REQ-021), a number like the others (issue #42)
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


def folder(here=None):
    return (here or project.current()).sources_dir / FOLDER


def source_paths(here=None):
    directory = folder(here)
    return sorted(directory.glob("*.json")) if directory.is_dir() else []


def new_source(cid):
    return {"schema_version": SOURCE_SCHEMA_VERSION, "id": cid, "name": "", "label": "", "group": "",
            "h_0": 500, "correction": 0, "exposure": "normal", "c_t": 1.0, "roof": "duo",
            "length": None, "width": None, "alpha_1": 30, "alpha_2": 30, "sliding": "possible"}


def _version(text):
    """A schema_version as a tuple, so that versions are compared as numbers (1.10 after 1.9)."""
    return tuple(int(part) for part in str(text).split("."))


def stamp_version(src):
    """The schema_version a source is saved at: the highest floor one of its fields asks -- 1.3 a free C_e, 1.2 a height step, 1.1 a field following a variable, 1.0 none -- what Woodcore's window calls before it writes one. A height step that is false and the number of a C_e that is not free are not written at all (D-19, REQ-021), so a source without either stays byte for byte what it was."""
    if not src.get("height_step"):
        src.pop("height_step", None)
    if src.get("exposure") != CUSTOM:
        src.pop("c_e", None)
    if src.get("exposure") == CUSTOM:
        src["schema_version"] = CUSTOM_SCHEMA_VERSION
    elif src.get("height_step"):
        src["schema_version"] = STEP_SCHEMA_VERSION
    else:
        src["schema_version"] = LINKED_SCHEMA_VERSION if links.is_linked(src, LINKABLE) else SOURCE_SCHEMA_VERSION
    return src


def check_source(src, where="loads/snow"):
    """A source of `loads/snow/` checked: its versions, links and structure, its id, then its fields (`check_fields`)."""
    if not isinstance(src, dict):
        _fail(where, "a snow load is a JSON object")
    if src.get("schema_version") not in SOURCE_SCHEMA_VERSIONS:
        _fail(where, "schema_version is %r -- this reads %s" % (src.get("schema_version"), ", ".join(SOURCE_SCHEMA_VERSIONS)))
    version = _version(src["schema_version"])
    if links.is_linked(src, LINKABLE) and version < _version(LINKED_SCHEMA_VERSION):
        _fail(where, "follows a variable at schema_version %r -- a load with links is %r or later" % (src.get("schema_version"), LINKED_SCHEMA_VERSION))
    if "height_step" in src and version < _version(STEP_SCHEMA_VERSION):
        _fail(where, "height_step at schema_version %r -- a roof with a height step is %r or later" % (src.get("schema_version"), STEP_SCHEMA_VERSION))
    if (src.get("exposure") == CUSTOM or "c_e" in src) and version < _version(CUSTOM_SCHEMA_VERSION):
        _fail(where, "a free C_e at schema_version %r -- it is %r or later" % (src.get("schema_version"), CUSTOM_SCHEMA_VERSION))
    links.check_all(src, LINKABLE, lambda message: _fail(where, message), "the snow load", links.LOADS)
    try:
        validation.validate_structure(src, SOURCE_SCHEMA)
    except validation.ValidationError as exc:
        _fail(where, str(exc))
    if not ID_PATTERN.match(src.get("id") or ""):
        _fail(where, "id %r -- letters, digits and _ . + - only, starting with a letter or digit" % src.get("id"))
    check_fields(src, lambda _field, message: _fail(where, message))


def _problems(src):
    """Every field the calculation cannot read, checked against SIA 261, in the form's order: [(field, code, params, sentence)] -- the one place the rules «red» are written (spec 2026-10-22-onglet-neige-type, REQ-008, ARCH-RISK-W02, D04). `check_fields` refuses on the first, `messages` says them all."""
    c = sia261_snow.clause()
    out = []

    def bad(field, code, sentence, **params):
        out.append((field, code, params, sentence))
    if not _number(src.get("h_0")) or src["h_0"] < 0:
        bad("h_0", "h_0", "h_0 is %r -- the altitude above sea level, m" % (src.get("h_0"),))
    if src.get("correction") not in c["corrections"]["values"]:
        bad("correction", "correction", "correction is %r -- SIA 261 Anhang D gives %s m" % (src.get("correction"), ", ".join("%+g" % v for v in c["corrections"]["values"])),
            values=", ".join("%+g" % v for v in c["corrections"]["values"]))
    # a site above 5.1.4's limit is no defect of the file: it is computed, and `messages` says so to the tab (spec 2026-10-14-neige-vent-affichage-altitude, REQ-003)
    if src.get("exposure") == CUSTOM:
        if not _number(src.get("c_e")) or src["c_e"] <= 0:
            bad("c_e", "c_e", "c_e is %r -- a free C_e is a number above 0 (5.2.4)" % (src.get("c_e"),), ref=c["exposure"]["norm_ref"])
    else:
        try:
            sia261_snow.exposure(src.get("exposure"))
        except validation.ValidationError as exc:
            bad("exposure", "exposure", str(exc))
        if "c_e" in src:
            bad("c_e", "c_e_unused", "c_e is %r with the exposure %r -- a C_e of its own is written with the exposure %r" % (src["c_e"], src.get("exposure"), CUSTOM))
    if not _number(src.get("c_t")) or not 0 < src["c_t"] <= c["c_t"]["default"]:
        bad("c_t", "c_t", "c_t is %r -- C_T, above 0 and at most %s (5.2.5)" % (src.get("c_t"), c["c_t"]["default"]), most=c["c_t"]["default"], ref=c["c_t"]["norm_ref"])
    if src.get("roof") not in ROOFS:
        bad("roof", "roof", "roof is %r -- %s" % (src.get("roof"), ", ".join(ROOFS)))
    if "height_step" in src and not isinstance(src["height_step"], bool):
        bad("height_step", "height_step_type", "height_step is %r -- true or false" % (src["height_step"],))
    if src.get("sliding") not in SLIDING:
        bad("sliding", "sliding", "sliding is %r -- %s" % (src.get("sliding"), ", ".join(SLIDING)))
    for key in ROOF_FIELDS.get(src.get("roof"), ()):
        value = src.get(key)
        if key.startswith("alpha"):
            if not _number(value) or not 0 <= value <= 90:
                bad(key, "alpha", "%s is %r -- a slope in degrees, 0 to 90" % (key, value), symbol=_alpha_symbol(src, key))
        elif not _number(value) or value <= 0:
            bad(key, "dimension", "%s is %r -- a plan dimension in m, above 0" % (key, value))
    return out


def check_fields(src, fail):
    """The fields the calculation reads, each checked against SIA 261: `fail(field, message)` stops on the first one wrong (`_problems`), naming the field -- a source names its file, a sheet of the workbook the cell the field is read from (domains/snow.py, ARCH-RISK-807)."""
    for field, _code, _params, sentence in _problems(src):
        fail(field, sentence)
        return


def _alpha_symbol(src, key):
    """How the form names a slope: α alone on a roof of one slope, α₁ and α₂ on two."""
    return "α" if src.get("roof") in ("mono", "curved") else {"alpha_1": "α₁", "alpha_2": "α₂"}.get(key, key)


# The messages the export says too (engine.Note), the others being the tab's alone: a site above 5.1.4's limit (spec 2026-10-14-neige-vent-affichage-altitude, REQ-003)
EXPORT_CODES = ("above_limit",)


def messages(src):
    """What the tab says of a source (spec 2026-10-22-onglet-neige-type, REQ-008, REQ-008b): every field it cannot read, an `error` that blocks the calculation, then what is only said, `info`, the calculation made -- [contracts.Message]. The tab words each code (`sn_msg_<code>`) and compares nothing itself; every threshold and clause is the norm file's.

    `above_limit` -- the site h_0 above 5.1.4's limit, where chapter 5 does not apply (h_0, not h_0 + Δh: D-02 of spec 2026-10-12-audit-issues-47-48-49); else `cornice` -- above 5.3.7's altitude, a cornice for the overhangs; `ct_low` -- C_T under 1 (5.2.5); `steep` -- a slope of 60° or more with the snow free to slide, which carries none (5.3.3); `large_flat` -- a flat roof whose two sides exceed 20 m, Figur 4 applied (5.3.5); `height_step` -- a stepped roof, not computed (5.3.6)."""
    from domains.contracts import Message
    out = [Message(code, field, "error", params) for field, code, params, _sentence in _problems(src)]
    c = sia261_snow.clause()
    infos = []
    limit, cornice = c["max_altitude"], c["cornice"]
    if _number(src.get("h_0")) and src["h_0"] > limit["value"]:
        infos.append(Message("above_limit", "h_0", "info", {"h_0": src["h_0"], "limit": limit["value"], "ref": limit["norm_ref"]}))
    elif _number(src.get("h_0")) and src["h_0"] > cornice["min_altitude"]:
        infos.append(Message("cornice", "h_0", "info", {"h_0": src["h_0"], "limit": cornice["min_altitude"], "ref": cornice["norm_ref"]}))
    if _number(src.get("c_t")) and 0 < src["c_t"] < c["c_t"]["default"]:
        infos.append(Message("ct_low", "c_t", "info", {"c_t": src["c_t"], "ref": c["c_t"]["norm_ref"]}))
    steep = c["steep"]
    if src.get("sliding") == "possible" and src.get("roof") in ("mono", "duo", "shed"):
        for key in ROOF_FIELDS[src["roof"]]:
            if _number(src.get(key)) and steep["alpha"] <= src[key] <= 90:
                infos.append(Message("steep", key, "info", {"symbol": _alpha_symbol(src, key), "alpha": src[key], "limit": steep["alpha"], "ref": steep["norm_ref"]}))
    large = c["large_flat"]
    if src.get("roof") == "flat" and _number(src.get("length")) and _number(src.get("width")) and min(src["length"], src["width"]) > large["min_side"]:
        infos.append(Message("large_flat", "length", "info", {"L": src["length"], "B": src["width"], "limit": large["min_side"], "ref": large["norm_ref"]}))
    if src.get("height_step"):
        infos.append(Message("height_step", "height_step", "info", {"ref": c["height_step"]["norm_ref"]}))
    return out + infos


def warnings(src):
    """What the export says of a valid source and the report never prints, [(code, params)]: the `messages` of `EXPORT_CODES` -- a site above 5.1.4's limit (spec 2026-10-14-neige-vent-affichage-altitude, REQ-004, D-04)."""
    return [(m.code, m.params) for m in messages(src) if m.code in EXPORT_CODES]


def notes_of(src, where):
    """`warnings(src)` as the export's warnings (engine.Note), `where` the file or the sheet they are of: a site above 5.1.4's limit is computed, and said (spec 2026-10-21-restes-issue-69, ARCH-RISK-811)."""
    import engine
    return [engine.Note("snow_" + code, "%s: h_0 = %g m is above the %g m of SIA 261 %s -- its provisions do not apply there" % (where, p["h_0"], p["limit"], p["ref"]),
                        where=where, **p) for code, p in warnings(src)]


# The figure's caption, a glossary term (the report's language), and the words the tab's drawing names its models with (D-31: the export's drawing has none)
FIGURE_TITLE = {True: "Schneelastanordnung, Lastmodelle 1 und 2 (SIA 261, Figur 3)", False: "Schneelastanordnung (SIA 261, Figur 3)"}
FIGURE_WORDS = {"lm1": "Lastmodell 1", "lm2": "Lastmodell 2", "one": "Beim Flachdach nur ein Lastmodell"}


def figure_svg(src, lang=None):
    """The column of SIA 261 Figur 3 for the roof of `src` (snow_svg.figure): without `lang` the export's, symbols and values only (D-31); with it the tab's, its models named in that language from the glossary. One code for the two (ARCH-008)."""
    words = None
    if lang:
        from i18n import strings
        words = {key: strings.translate(term, lang) for key, term in FIGURE_WORDS.items()}
    return snow_svg.figure(src, {k: v[0] for k, v in coefficients(src).items()}, sia261_snow.clause()["curved"]["alpha_0"], words)


def sketch(src):
    """The tab's drawing of the disposition before the spec 2026-10-22-onglet-neige-type: the export's figure since (`figure_svg`), kept under this name for tests/test_figure_golden.py."""
    return figure_svg(src)


def tile_svg(roof):
    """The tile of a roof form in the form (T39, snow_svg.tile)."""
    return snow_svg.tile(roof)


def chart(src):
    """Figur 2 as an interactive chart (UI-010, snow_svg.chart): μ₁, μ₂, μ₃ as the norm file draws them, and the case's slopes marked on the curve the case reads -- μ₃ for a curved roof, μ₁ (0.8 where the sliding is hindered) otherwise."""
    c = sia261_snow.clause()
    series = [("μ_1", c["mu_1"]["points"]), ("μ_2", c["mu_2"]["points"]), ("μ_3", c["mu_3"]["points"])]
    roof = src.get("roof")
    slopes = {"duo": (("α_1", "alpha_1"), ("α_2", "alpha_2")), "shed": (("α_1", "alpha_1"), ("α_2", "alpha_2"))}.get(roof) or ((("α", "alpha_1"),) if roof in ("mono", "curved") else ())
    marks = []
    for label, key in slopes:
        alpha = src.get(key)
        if not _number(alpha) or not 0 <= alpha <= 70:
            continue
        if roof == "curved":
            marks.append((label, alpha, sia261_snow.curve(c["mu_3"]["points"], alpha), "μ_3"))
        else:
            mu = c["hindered"]["mu_1"] if src.get("sliding") == "hindered" else sia261_snow.curve(c["mu_1"]["points"], alpha)
            marks.append((label, alpha, mu, "μ_1"))
    return snow_svg.chart(series, marks)


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


def build_instance(src, here=None, inputs=None):
    """One instance of `snow-load`: h_ref, s_k, C_e, C_T, the roof and its coefficients, and the loads of the two models of Figur 3. No drawing: `sketch` is the tab's (D-03). `inputs` says where each field of `src` was read, {field: source} -- a sheet's cells, `excel:<workbook>!<cell>` (domains/snow.py) --, a field it does not name being entered in Woodcore."""
    import engine
    c = sia261_snow.clause()
    calc = engine.Calculation()
    where = "%s/%s.json" % (FOLDER, src["id"])

    def var(name, value, symbol, unit, label, norm_ref, **more):
        calc.add_var(name=name, value=value, unit=unit, symbol=symbol, label=label,
                     source=more.pop("source", SOURCE), norm=NORM, norm_ref=norm_ref, **more)

    inputs = inputs or {}

    def entered(field):
        return inputs.get(field, "entered:%s" % where)
    # --- the site
    var("h_0", src["h_0"], "h_0", "m", "Höhe ü. NN", "5.2.6", source=entered("h_0"), description="Höhe des Standorts über Meer.")
    # the corrections Anhang D allows, each its height (the workbook's dropdown until v0.120): the choice the report sets beside Δh
    corrections = [{"value": v, "desc": "± 0 m" if v == 0 else "%+g m" % v} for v in c["corrections"]["values"]]
    var("korrektur", src["correction"], "Delta h", "m", "Korrektur Wert", "Anhang D", source=entered("correction"),
        description="Höhenzuschlag auf die Höhe ü. NN nach SIA 261, Anhang D.", choices=corrections)
    h_ref = src["h_0"] + src["correction"]
    var("h_ref", h_ref, 'h_"ref"', "m", "Bezugshöhe", "5.2.6")
    calc.add_step(name="Bezugshöhe", result="h_ref", uses=["h_0", "korrektur"], formula='h_"ref" = h_0 + Delta h', norm=NORM, norm_ref="Anhang D")
    # --- the coefficients
    if src["exposure"] == CUSTOM:
        # a C_e of the engineer's own (REQ-021): its number, without the norm's three choices beside it
        exposure = {"value": src["c_e"]}
        var("ce", src["c_e"], "C_e", "", "Expositionsbeiwert", c["exposure"]["norm_ref"], source=entered("c_e"), group="beiwerte")
    else:
        exposure = sia261_snow.exposure(src["exposure"])
        choices = [{"value": e["value"], "desc": e["label"]} for e in c["exposure"]["choices"]]
        var("ce", exposure["value"], "C_e", "", "Expositionsbeiwert", c["exposure"]["norm_ref"], source=entered("exposure"), choices=choices, group="beiwerte")
    var("ct", src["c_t"], "C_T", "", "Thermischer Beiwert", c["c_t"]["norm_ref"], source=entered("c_t"), group="beiwerte")
    # --- the roof
    var("dachform", ROOF_WORDS[src["roof"]], '"Dachform"', "", "Dachform / Lastmodell", "Figur 3", source=entered("roof"))
    if src["roof"] == "flat":
        var("L", src["length"], "L", "m", "Gebäudelänge", "5.3.5", source=entered("length"), group="geometrie", group_label="Gebäude Geometrie")
        var("B", src["width"], "B", "m", "Gebäudebreite", "5.3.5", source=entered("width"), group="geometrie")
    else:
        var("alpha_1", src["alpha_1"], "alpha_1" if src["roof"] in ("duo", "shed") else "alpha", "°", "Dachneigung 1", "Figur 3", source=entered("alpha_1"), group="dachneigung")
        if src["roof"] in ("duo", "shed"):
            var("alpha_2", src["alpha_2"], "alpha_2", "°", "Dachneigung 2", "Figur 3", source=entered("alpha_2"), group="dachneigung")
    var("abgleiten", SLIDING_WORDS[src["sliding"]], '"Abgleiten des Schnees"', "", "Abgleiten des Schnees", c["hindered"]["norm_ref"], source=entered("sliding"),
        description="Ist das Abgleiten behindert oder erschwert, wird der Dachformbeiwert μ₁ mit 0.8 angesetzt (SIA 261, Ziffer 5.3.4).")
    # 5.3.6 and 5.3.7 are not computed: the report says where they apply (D-04) -- a stepped roof as its source states, a cornice for works above 800 m
    if src.get("height_step"):
        step = c["height_step"]
        var("hoehensprung", "Zusatzlast nach Figur 5", '"Höhensprung"', "", "Höhensprung", step["norm_ref"], source=entered("height_step"),
            description="Bei abgestuften Dächern oder bei einem Dach, das an ein höheres Bauwerk angrenzt, ist auf der unteren Dachfläche eine dreieckförmige Zusatzlast nach Figur 5 anzusetzen (Verdoppelung von μ₁ auf der Seite des Höhensprungs, Einflusslänge l_s = 2 h). Sie ist hier nicht berechnet.")
    # the cornice of 5.3.7 left the report (spec 2026-10-22-onglet-neige-type, REQ-018, D-13): the tab says it in orange above 800 m (`messages`), the file no longer prints it
    mus = coefficients(src)
    labels = {"mu_1": ("mu_1", "Dachformbeiwert"), "mu_11": ("mu_11", "Dachformbeiwert"), "mu_12": ("mu_12", "Dachformbeiwert 2"),
              "mu_2m": ("mu_(2m)", "Dachformbeiwert der Schneeanhäufung"), "mu_3": ("mu_3", "Dachformbeiwert")}
    for name, (value, why) in mus.items():
        var(name, value, labels[name][0], "", labels[name][1], why, group="dachformbeiwerte")
    # --- the ground
    s_k, floored = sia261_snow.s_k(h_ref)
    sc = c["s_k"]
    var("s_k", s_k, "s_k", "kN/m²", "Charakteristischer Wert der Schneelast auf horizontalem Gelände", sc["norm_ref"])
    # equation (10) as `#eq` computes it again (spec 2026-10-22-onglet-neige-type, REQ-017, ARCH-RISK-F06): its floor a max(), every unit written, so that the line is an `#eq` at every altitude -- above the floor and on it
    calc.add_step(name="Charakteristischer Wert auf horizontalem Gelände", result="s_k", uses=["h_ref"],
                  formula='s_k = max((1 + (h_"ref" / (%s "m"))^%s) dot %s "kN/m²", %s "kN/m²")' % (_fmt(sc["divisor"]), _fmt(sc["exponent"]), _fmt(sc["factor"]), _fmt(sc["min"])),
                  norm=NORM, norm_ref=sc["norm_ref"])
    # --- the loads of the two models
    base = exposure["value"] * src["c_t"] * s_k
    results = []

    def load(name, mu, symbol, mu_symbol, label, uses, half=False):
        value = mu * base / (2 if half else 1)
        var(name, value, symbol, "kN/m²", label, "5.2.2")
        formula = "%s = %s%s dot C_e dot C_T dot s_k" % (symbol, mu_symbol, " / 2" if half else "")
        calc.add_step(name=label, result=name, uses=uses + ["ce", "ct", "s_k"], formula=formula, norm=NORM, norm_ref="5.2.2")
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
    out = {"results": results, **calc.to_dict()}
    # the column of Figur 3 for the case's roof, printed at the head of its file (spec 2026-10-22-onglet-neige-type, REQ-016, D-32): written by the export under Variable-loads/Snow/Exports/Figures/, the same drawing as the tab's (ARCH-008)
    place = engine.Figures(here.data_dir if here is not None else None, DOMAIN, here)
    rel = place.name("%s-fig3.svg" % src["id"])
    out["figures"] = [{"file": rel, "title": FIGURE_TITLE[src["roof"] != "flat"], "level": 1}]
    out["_files"] = {rel: figure_svg(src)}
    return out


# --- the snow tab's declaration (spec 2026-10-22-onglet-neige-type, ARCH-002; calc/domains/contracts.py) ---------------
#
# The form the calculation tab draws for the snow, described here and drawn by calc/tools/calc_tab.py, which holds no word of the snow: its sections, in the prototype's order -- the building first (T37) --, its fields, their choices read off the norm file and this module's words, and the excerpts each ⓘ shows (the prototype's FIELD_NORM, T28 to T31). The tab's words are `sn_s_<section>`, `sn_f_<key>`, `sn_msg_<code>` (calc/tools/snow_tab_words.py).

PREFIX = "sn_"
NORM_FILE = sia261_snow.SNOW
# The values the tab shows as results, never an input (REQ-009): every var of the instance but these
INPUTS = ("h_0", "korrektur", "ce", "ct", "dachform", "L", "B", "alpha_1", "alpha_2", "abgleiten", "hoehensprung")
# The excerpts of each roof's tile (T28): a duo-pitch, a shed and a curved roof the whole of Figur 3, a mono-pitch roof 5.3.2 and Figur 3, a flat roof 5.3.5 and Figur 4
ROOF_EXCERPTS = {"flat": ("5.3.5", "fig4"), "mono": ("5.3.2", "fig3"), "duo": ("fig3",), "shed": ("fig3",), "curved": ("fig3",)}
# The order the buttons of C_e are shown in (T38): sheltered 1.2, normal 1.0, exposed 0.8
EXPOSURE_ORDER = ("sheltered", "normal", "exposed")

_declaration = {}


def declaration():
    """The snow tab's form (contracts.Declaration), built once from the norm file and this module's words."""
    if "d" in _declaration:
        return _declaration["d"]
    from domains.contracts import Choice, Declaration, Field
    c = sia261_snow.clause()
    linkable = LINKABLE[links.SELF]
    by_id = {e["id"]: e for e in c["exposure"]["choices"]}
    fields = (
        Field("length", "number", "m", excerpts=("5.3.5", "fig4"), minimum=0.0, maximum=1000.0, decimals=1, step=1.0, linkable="length" in linkable),
        Field("width", "number", "m", excerpts=("5.3.5", "fig4"), minimum=0.0, maximum=1000.0, decimals=1, step=1.0, linkable="width" in linkable),
        Field("h_0", "number", "m", excerpts=("5.2.6", "5.1.4"), minimum=0.0, maximum=5000.0, decimals=0, step=10.0, linkable="h_0" in linkable),
        Field("correction", "buttons", "m", choices=tuple(Choice(v, value=v) for v in c["corrections"]["values"]), excerpts=("annexD",)),
        Field("exposure", "buttons", "", choices=tuple(Choice(i, PREFIX + "c_exposure_" + i, by_id[i]["value"]) for i in EXPOSURE_ORDER),
              excerpts=(c["exposure"]["norm_ref"],), minimum=0.01, maximum=5.0, decimals=2, step=0.05, free_id=CUSTOM, free_key="c_e"),
        Field("c_t", "number", "", excerpts=(c["c_t"]["norm_ref"],), minimum=0.0, maximum=c["c_t"]["default"], decimals=2, step=0.05, linkable="c_t" in linkable),
        Field("roof", "tiles", "", choices=tuple(Choice(r, ROOF_WORDS[r], excerpts=ROOF_EXCERPTS[r]) for r in ROOFS), excerpts=("fig3",)),
        Field("alpha_1", "number", "°", excerpts=("5.2.3", "fig2"), minimum=0.0, maximum=90.0, decimals=1, step=1.0, linkable="alpha_1" in linkable),
        Field("alpha_2", "number", "°", excerpts=("5.2.3", "fig2"), minimum=0.0, maximum=90.0, decimals=1, step=1.0, linkable="alpha_2" in linkable),
        Field("sliding", "buttons", "", choices=tuple(Choice(k, PREFIX + "c_sliding_" + k) for k in SLIDING), excerpts=(c["hindered"]["norm_ref"], c["steep"]["norm_ref"])),
        Field("height_step", "checkbox", "", excerpts=(c["height_step"]["norm_ref"], "fig5")),
    )
    sections = (("building", ("length", "width")), ("site", ("h_0", "correction", "exposure", "c_t")),
                ("roof", ("roof", "alpha_1", "alpha_2", "sliding", "height_step")))
    _declaration["d"] = Declaration(PREFIX, NORM_FILE, sections, fields)
    return _declaration["d"]


def visible_fields(src):
    """The fields the form shows for `src`: every one, but the slopes a roof does not have (ROOF_FIELDS) -- the building's length and width are always entered (T37)."""
    slopes = {"alpha_1", "alpha_2"} - set(ROOF_FIELDS.get(src.get("roof"), ()))
    return [f.key for f in declaration().fields if f.key not in slopes]


def results(instance):
    """The values the tab's «Résultats» shows (REQ-009): what is computed -- h_ref, s_k, the μ, the q_k --, never an input."""
    computed = [name for name in instance["vars"] if name not in INPUTS]
    rank = {"h_ref": 0, "s_k": 1}
    return sorted(computed, key=lambda name: rank.get(name, 2 if name.startswith("mu") else 3))   # the order of the prototype: h_ref, s_k, the μ, the q_k
