"""The values of SIA 265:2021 this project calculates with, out of the JSON files beside this module in `calc/norms/` (docs/architecture/layout.md §11).

`calc/norms/` is **the one source of every value taken from a norm** for a calculation made in Python: the numbers live in the JSON, once, and the code that needs them reads them through here -- a table's cells, a scalar the norm states under its own symbol, **and the coefficients inside a formula** (the 0.082 of Tabelle 22, the 0.3 and 2.6 of equation (87), the 0.44/1.26/2.52 of Tabellen 45 and 46), which until v0.77 stayed beside their formula in `domains/dowel.py`. The engineer's rule: no norm value twice, and none outside `calc/norms/` (a calculation made in Excel keeps its own). Every number was transcribed by hand from `SIA265-2021-DE.pdf`, at a page that can be turned to, and each file's `_source` says which (section 2 rule 13).

**One file per table or clause, named `<norm>-<year>-<table or clause>-<designation>.json`**, so a value is found by the norm's own number:

    sia265-2021-2.2.6-eta-t.json                   2.2.6, eta_t
    sia265-2021-5.3.6.2.2-fachwerk.json            5.3.6.2.2, the truss reduction
    sia265-2021-6.1.4.2-k-red.json                 6.1.4.2, equation (86) and Tabelle 21's n = 1
    sia265-2021-6.1.4.4-fliessmoment.json          6.1.4.4, equation (87)
    sia265-2021-6.2.1.1-k-alpha.json               6.2.1.1, k_alpha and the diameters of equation (88)
    sia265-2021-6.2.1.3-schlupf.json               6.2.1.3, the slip
    sia265-2021-tab01-gamma-m.json                 Tabelle 1, gamma_M/eta_M (2.2.5)
    sia265-2021-tab03-feuchteklassen.json          Tabelle 3, the moisture classes (3.2.1.2)
    sia265-2021-tab04-eta-w.json                   Tabelle 4, eta_w (3.2.1.3)
    sia265-2021-tab08-vollholz.json                Tabelle 8, Vollholz: C16, C24, C30, D30 (3.3.2.1)
    sia265-2021-tab09-brettschichtholz.json        Tabelle 9, Brettschichtholz: GL20h .. GL32h (3.4.2.2)
    sia265-2021-tab22-lochleibungsfestigkeit.json  Tabelle 22, f_h,k (6.1.4.3)
    sia265-2021-tab24-abstaende.json               Tabelle 24, the dowels' minimum spacings (6.2.1.2)
    sia265-2021-tab25-kser.json                    Tabelle 25, K_ser (6.2.1.4)
    sia265-2021-tab45-kbeta-holz-holz.json         Anhang A, Tabelle 45 (A.1.1)
    sia265-2021-tab46-kbeta-stahl-holz.json        Anhang A, Tabelle 46 (A.1.2)

and what the member checks of chapter 4.2 read, which `lib/timber.typ` computes in Typst:

    sia265-2021-3.4.2.3-k-h.json                                 3.4.2.3, k_h of glulam, equation (5)
    sia265-2021-4.2.6-abscheren.json                             4.2.6, equations (26)/(27) and the 150 mm
    sia265-2021-4.2.7-schub-querdruck.json                       4.2.7.1, k_t,90 of equation (28)
    sia265-2021-4.2.8-knicken.json                               4.2.8, beta_c and equations (30)/(31)
    sia265-2021-4.2.9-kippen.json                                4.2.9, equations (39) to (44)
    sia265-2021-4.5-brandfall.json                               4.5.2, the fire situation: Tabelle 13, d_red, 4.5.2.4, (51) (issue #46)
    sia265-2021-tab47-druckfestigkeit-e005-vollholz.json         Anhang B, Tabelle 47: f_c,0,k and E_0,05, Vollholz
    sia265-2021-tab48-druckfestigkeit-e005-brettschichtholz.json Anhang B, Tabelle 48: the same, Brettschichtholz

and the minimum distances and timber thicknesses of each kind of fastener, which `lib/distance.typ` prints computed with a diameter (v0.87) -- Tabelle 24 above, and

    sia265-2021-tab27-holzdicken-naegel.json                 Tabelle 27, nails without predrilling (6.4.2.1.2)
    sia265-2021-tab28-abstaende-naegel.json                  Tabelle 28 (6.4.2.1.3)
    sia265-2021-tab32-holzdicken-naegel-vorgebohrt.json      Tabelle 32, nails with predrilling (6.4.3.1.2)
    sia265-2021-tab33-abstaende-naegel-vorgebohrt.json       Tabelle 33 (6.4.3.1.3)
    sia265-2021-tab36-holzdicken-schrauben.json              Tabelle 36, screws without predrilling (6.5.2.3.2)
    sia265-2021-tab37-holzdicken-schrauben-vorgebohrt.json   Tabelle 37, screws with predrilling (6.5.2.3.2)
    sia265-2021-tab38-abstaende-schrauben.json               Tabelle 38 (6.5.2.3.3)
    sia265-2021-tab39-abstaende-schrauben-vorgebohrt.json    Tabelle 39 (6.5.2.3.3)
    sia265-2021-tab40-abstaende-schrauben-axial.json         Tabelle 40, screws loaded along their axis (6.5.3.3)
    sia265-2021-tab41-abstaende-ringduebel.json              Tabelle 41, split rings (6.8.3.4)
    sia265-2021-6.4.1.1-nageldurchmesser.json                6.4.1.1, the diameters the nail clauses hold for
    sia265-2021-6.5.2.3.1-schraubendurchmesser.json          6.5.2.2 / 6.5.2.3.1, the diameters Tabellen 34 to 37 hold for

The files are hand-written -- the one place in the pipeline where a number is transcribed rather than read -- so each is checked here before anything is built from it: a grade listed twice, a property that is not a number, a moisture class Tabelle 4 gives no eta_w for, a footnote referenced but never written. A norm table that contradicts itself must stop the export naming the file, exactly as a defective workbook cell does (section 3.6).

Two tables of SIA 265 that this project will want are deliberately not here yet, because their editions are not in the reference library: the grades SN EN 14080 gives for GL40h and above, and the CLT classes of SIA 265/1.
"""

from pathlib import Path

import validation
from norms import _loader  # how every reader of calc/norms/ opens its files (G3)

HERE = Path(__file__).resolve().parent

ETA_T = "sia265-2021-2.2.6-eta-t"
TRUSS = "sia265-2021-5.3.6.2.2-fachwerk"
K_RED = "sia265-2021-6.1.4.2-k-red"
YIELD_MOMENT = "sia265-2021-6.1.4.4-fliessmoment"
K_ALPHA = "sia265-2021-6.2.1.1-k-alpha"
SLIP = "sia265-2021-6.2.1.3-schlupf"
TAB01 = "sia265-2021-tab01-gamma-m"
TAB03 = "sia265-2021-tab03-feuchteklassen"
TAB04 = "sia265-2021-tab04-eta-w"
TAB08 = "sia265-2021-tab08-vollholz"
TAB09 = "sia265-2021-tab09-brettschichtholz"
TAB22 = "sia265-2021-tab22-lochleibungsfestigkeit"
TAB24 = "sia265-2021-tab24-abstaende"
TAB25 = "sia265-2021-tab25-kser"
TAB45 = "sia265-2021-tab45-kbeta-holz-holz"
TAB46 = "sia265-2021-tab46-kbeta-stahl-holz"
TAB27 = "sia265-2021-tab27-holzdicken-naegel"
TAB28 = "sia265-2021-tab28-abstaende-naegel"
TAB32 = "sia265-2021-tab32-holzdicken-naegel-vorgebohrt"
TAB33 = "sia265-2021-tab33-abstaende-naegel-vorgebohrt"
TAB36 = "sia265-2021-tab36-holzdicken-schrauben"
TAB37 = "sia265-2021-tab37-holzdicken-schrauben-vorgebohrt"
TAB38 = "sia265-2021-tab38-abstaende-schrauben"
TAB39 = "sia265-2021-tab39-abstaende-schrauben-vorgebohrt"
TAB40 = "sia265-2021-tab40-abstaende-schrauben-axial"
TAB41 = "sia265-2021-tab41-abstaende-ringduebel"
NAIL_DIAMETERS = "sia265-2021-6.4.1.1-nageldurchmesser"
SCREW_DIAMETERS = "sia265-2021-6.5.2.3.1-schraubendurchmesser"
K_H = "sia265-2021-3.4.2.3-k-h"
SHEAR_OFF = "sia265-2021-4.2.6-abscheren"
SHEAR_TRANSVERSE = "sia265-2021-4.2.7-schub-querdruck"
BUCKLING = "sia265-2021-4.2.8-knicken"
LATERAL_BUCKLING = "sia265-2021-4.2.9-kippen"
TAB47 = "sia265-2021-tab47-druckfestigkeit-e005-vollholz"
TAB48 = "sia265-2021-tab48-druckfestigkeit-e005-brettschichtholz"
FIRE = "sia265-2021-4.5-brandfall"
# the design values set for a class the tables do not list (3.3.2.2 solid timber, 3.4.2.2 glulam): what a member of the engineer's own reads (issue #110)
OTHER_SOLID = "sia265-2021-3.3.2.2-andere-festigkeitsklassen"
OTHER_GLULAM = "sia265-2021-3.4.2.2-andere-festigkeitsklassen"

# The files the member checks of chapter 4.2 read (lib/timber.typ reads the same ones by relative path), and 4.5's for a check in the fire situation (issue #46).
MEMBER_FILES = (K_H, SHEAR_OFF, SHEAR_TRANSVERSE, BUCKLING, LATERAL_BUCKLING, TAB47, TAB48, FIRE)

# The choices of wood Tabelle 13 reads a charring rate for (issue #46): `softwood` is what a grade SIA 265 lists as Nadelholz stands for, and is never asked; the three others are asked of the engineer -- a Laubholz grade (D30) is beech or oak, and solid timber cladding is a row of its own. Written once: the schema enumerates them and lib/timber.typ's `fire:` takes them, both held equal to this tuple by tests/test_fire_resistance.py.
FIRE_WOODS = ("softwood", "beech", "oak", "cladding")

# The four faces of a rectangular section the fire may reach (issue #46): two reduce the width b, two the height h.
FIRE_SIDES = ("bottom", "top", "left", "right")
FIRE_WIDTH_SIDES = ("left", "right")
FIRE_HEIGHT_SIDES = ("bottom", "top")

# The tables of minimum distances and timber thicknesses `lib/distance.typ` prints (v0.87), in the norm's order, and the clauses a table's fastener may name as the diameters it holds for. lib/distance.typ names the same files; tests/test_distance.py holds the two lists equal, and calc/project.py's ENGINE_FILES carries them into every project.
DISTANCE_TABLES = (TAB24, TAB27, TAB28, TAB32, TAB33, TAB36, TAB37, TAB38, TAB39, TAB40, TAB41)
DIAMETER_SCOPES = (K_ALPHA, NAIL_DIAMETERS, SCREW_DIAMETERS)

# Every file this module reads, and the key its table or clause sits under. The reader checks that all of them name the same edition: two files disagreeing about which SIA 265 they were read from would be two norms pretending to be one.
FILES = {
    ETA_T: "eta_t",
    TRUSS: "clause",
    K_RED: "clause",
    YIELD_MOMENT: "clause",
    K_ALPHA: "clause",
    SLIP: "slip",
    OTHER_SOLID: "clause",
    OTHER_GLULAM: "clause",
    TAB01: "table_1",
    TAB03: "table_3",
    TAB04: "table_4",
    TAB08: "table_8",
    TAB09: "table_9",
    TAB22: "table_22",
    TAB24: "table_24",
    TAB25: "table_25",
    TAB45: "table_45",
    TAB46: "table_46",
    TAB27: "table_27",
    TAB28: "table_28",
    TAB32: "table_32",
    TAB33: "table_33",
    TAB36: "table_36",
    TAB37: "table_37",
    TAB38: "table_38",
    TAB39: "table_39",
    TAB40: "table_40",
    TAB41: "table_41",
    NAIL_DIAMETERS: "clause",
    SCREW_DIAMETERS: "clause",
    K_H: "clause",
    SHEAR_OFF: "clause",
    SHEAR_TRANSVERSE: "clause",
    BUCKLING: "clause",
    LATERAL_BUCKLING: "clause",
    TAB47: "table_47",
    TAB48: "table_48",
    FIRE: "clause",
}

# The scalars the norm states under a symbol of their own, by the name the calculation asks for them.
CLAUSES = {"k_alpha": K_ALPHA, "truss_reduction": TRUSS}

# The two families of Tabelle 8 / Tabelle 9 -- which file a grade is read from, not a value of either. The species a grade may carry are Tabelle 22's rows (`species_names()`), and the moisture classes Tabelle 3's (`moisture_class_ids()`): read, never restated.
FAMILIES = ("Vollholz", "Brettschichtholz")

# The two columns of Tabelle 4.
ETA_W_KINDS = ("resistance", "stiffness")

# Every numeric property a grade row must carry, as the two tables head them.
GRADE_NUMBERS = (
    "f_m_k", "E_m_mean", "rho_k",
    "f_m_d", "f_t_0_d", "f_c_0_d", "f_t_90_d", "f_v_d",
    "E_0_mean", "E_90_mean", "G_mean",
)

# The three rows of Tabelle 24 and the two directions each gives.
SPACING_ROWS = ("fastener", "loaded_edge", "unloaded_edge")
DIRECTIONS = ("parallel", "perpendicular")

# The two families of Tabelle 25.
KSER_FAMILIES = ("timber-timber", "steel-timber")

_cache = {}


_fail = _loader.fail   # calc/norms/<name>.json: <what> (G3)


def _read(name):
    """One file, read once and checked once."""
    if name in _cache:
        return _cache[name]
    path = HERE / (name + ".json")
    data = _loader.load(path)
    _loader.edition(name, data)
    key = FILES[name]
    if not isinstance(data.get(key), dict):
        _fail(name, "no '%s' block" % key)
    # Cached before it is checked: a check may read another file (Tabelle 4 asks Tabelle 3 for its classes), and a file that fails is taken back out.
    _cache[name] = data
    try:
        _CHECKS[name](name, data[key], data)
    except Exception:  # broad: a table that failed its check is taken out of the cache, then the refusal raised again
        _cache.pop(name, None)
        raise
    return data


def _positive(name, where, label, value, allow_zero=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(name, "%s: %s is %r -- expected a number" % (where, label, value))
    if value < 0 or (value == 0 and not allow_zero):
        _fail(name, "%s: %s is %s -- expected a positive number" % (where, label, value))


def _number(name, where, label, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(name, "%s: %s is %r -- expected a number" % (where, label, value))


def _range(name, where, span):
    if not isinstance(span, dict):
        _fail(name, "%s: no diameter_range -- {min, max, unit}" % where)
    _positive(name, where, "diameter_range.min", span.get("min"))
    _positive(name, where, "diameter_range.max", span.get("max"))
    if span["min"] >= span["max"]:
        _fail(name, "%s: diameter_range runs from %s to %s -- backwards" % (where, span["min"], span["max"]))


def _check_gamma_m(name, table, _data):
    seen = set()
    for entry in table.get("entries") or ():
        for key in ("id", "label", "value"):
            if key not in entry:
                _fail(name, "an entry has no '%s': %r" % (key, entry))
        if entry["id"] in seen:
            _fail(name, "entry '%s' is listed twice -- one row per kind" % entry["id"])
        seen.add(entry["id"])
        _positive(name, "entry '%s'" % entry["id"], "value", entry["value"])
        if entry["value"] < 1:
            _fail(name, "entry '%s': gamma_M/eta_M is %s -- a resistance is divided by it, so it is not below 1"
                  % (entry["id"], entry["value"]))
    if not seen:
        _fail(name, "carries no entry")


def _check_classes(name, table, _data):
    classes = table.get("classes") or ()
    seen = [c.get("id") for c in classes]
    if not seen or any(isinstance(x, bool) or not isinstance(x, int) for x in seen) or len(set(seen)) != len(seen):
        _fail(name, "the moisture classes are %r -- expected whole numbers, once each" % (seen,))
    for entry in classes:
        for key in ("moisture", "label"):
            if not entry.get(key):
                _fail(name, "Feuchteklasse %s has no '%s'" % (entry["id"], key))


def _check_eta_w(name, table, _data):
    classes = table.get("classes") or ()
    seen = [c.get("id") for c in classes]
    expected = moisture_class_ids()
    if len(seen) != len(expected) or sorted(x for x in seen if isinstance(x, int)) != sorted(expected):
        _fail(name, "gives eta_w for the classes %r -- Tabelle 3 (%s.json) has %s, and each needs one row"
              % (seen, TAB03, ", ".join(str(c) for c in expected)))
    for entry in classes:
        where = "Feuchteklasse %s" % entry["id"]
        for kind in ETA_W_KINDS:
            if kind not in entry:
                _fail(name, "%s has no '%s'" % (where, kind))
            _positive(name, where, kind, entry[kind])
            if entry[kind] > 1:
                _fail(name, "%s: %s is %s -- eta_w converts from class 1 downwards, so it is at most 1"
                      % (where, kind, entry[kind]))
        if entry["id"] == 1 and (entry["resistance"] != 1 or entry["stiffness"] != 1):
            _fail(name, "Feuchteklasse 1 must carry eta_w = 1.0 for both properties (SIA 265 3.2.1.3)")


def _check_eta_t(name, eta_t, _data):
    for key in ("normal", "impact"):
        if key not in eta_t:
            _fail(name, "eta_t has no '%s'" % key)
        _positive(name, "eta_t", key, eta_t[key])
    if eta_t["impact"] < eta_t["normal"]:
        _fail(name, "eta_t: impact (%s) is below normal (%s) -- a stossartige Einwirkung raises the resistance"
              % (eta_t["impact"], eta_t["normal"]))


def _check_grades(name, table, _data):
    notes = table.get("notes") or {}
    units = table.get("units") or {}
    grades = table.get("grades") or ()
    if not grades:
        _fail(name, "carries no grade")
    species_known = species_names()
    seen = set()
    for grade in grades:
        gid = grade.get("id")
        if not isinstance(gid, str) or not gid.strip():
            _fail(name, "a grade row has no id: %r" % grade)
        if gid in seen:
            _fail(name, "grade '%s' is listed twice -- one row per strength class" % gid)
        seen.add(gid)
        where = "grade '%s'" % gid
        if grade.get("family") not in FAMILIES:
            _fail(name, "%s: family is %r -- expected one of %s" % (where, grade.get("family"), ", ".join(FAMILIES)))
        if grade.get("species") not in species_known:
            _fail(name, "%s: species is %r -- Tabelle 22 (%s.json) has a row for %s"
                  % (where, grade.get("species"), TAB22, ", ".join(species_known)))
        for key in GRADE_NUMBERS:
            if key not in grade:
                _fail(name, "%s has no '%s'" % (where, key))
            _positive(name, where, key, grade[key])
            if key not in units:
                _fail(name, "%s: '%s' has no unit in the table's units block" % (where, key))
        compression = grade.get("f_c_90_d")
        if not isinstance(compression, dict):
            _fail(name, "%s: f_c_90_d must be a block of generell / mit_vorholz / endauflagerung" % where)
        _positive(name, where, "f_c_90_d.generell", compression.get("generell"))
        for row in ("mit_vorholz", "endauflagerung"):
            entry = compression.get(row)
            if not isinstance(entry, dict):
                _fail(name, "%s: f_c_90_d.%s must carry a value and its bracket" % (where, row))
            _positive(name, where, "f_c_90_d.%s.value" % row, entry.get("value"))
            bracket = entry.get("groessere_eindrueckungen", "missing")
            if bracket == "missing":
                _fail(name, "%s: f_c_90_d.%s has no 'groessere_eindrueckungen' -- write null where the norm gives no bracketed value"
                      % (where, row))
            if bracket is not None:
                _positive(name, where, "f_c_90_d.%s bracket" % row, bracket)
                if bracket < entry["value"]:
                    _fail(name, "%s: f_c_90_d.%s bracket (%s) is below the value (%s) -- footnote 4's value is the higher one"
                          % (where, row, bracket, entry["value"]))
        for field, refs in (grade.get("notes") or {}).items():
            if not isinstance(refs, list):
                _fail(name, "%s: notes['%s'] must be a list of footnote references" % (where, field))
            for ref in refs:
                if ref not in notes:
                    _fail(name, "%s refers to footnote %r, which this table does not carry (footnotes: %s)"
                          % (where, ref, ", ".join(sorted(notes))))


def _check_spacings(name, table, _data):
    rows = {row.get("id"): row for row in table.get("rows") or ()}
    if tuple(rows) != SPACING_ROWS:
        _fail(name, "the rows are %r -- expected exactly %s, in that order"
              % (tuple(rows), ", ".join(SPACING_ROWS)))
    for rid, row in rows.items():
        for direction in DIRECTIONS:
            entry = row.get(direction)
            if not isinstance(entry, dict):
                _fail(name, "row '%s' has no '%s' block" % (rid, direction))
            _positive(name, "row '%s' %s" % (rid, direction), "factor", entry.get("factor"))
            floor = entry.get("min", "missing")
            if floor == "missing":
                _fail(name, "row '%s' %s has no 'min' -- write null where the norm gives no absolute floor" % (rid, direction))
            if floor is not None:
                _positive(name, "row '%s' %s" % (rid, direction), "min", floor)


def _check_kser(name, table, _data):
    families = {f.get("id"): f for f in table.get("families") or ()}
    if tuple(families) != KSER_FAMILIES:
        _fail(name, "the families are %r -- expected exactly %s" % (tuple(families), ", ".join(KSER_FAMILIES)))
    for fid, family in families.items():
        for direction in DIRECTIONS:
            _positive(name, "family '%s'" % fid, direction, family.get(direction))
    exponents = table.get("exponents") or {}
    for key in ("rho_k", "d"):
        if key not in exponents:
            _fail(name, "no exponent for '%s' -- K_ser = c * rho_k^a * d^b" % key)
        _positive(name, "exponents", key, exponents[key])


def _check_slip(name, slip_block, _data):
    _positive(name, "slip", "value", slip_block.get("value"))
    if not slip_block.get("unit"):
        _fail(name, "slip has no unit")


def _check_scalar(name, entry, _data):
    """A scalar stated under its own symbol: k_alpha, the truss reduction."""
    for field in ("value", "unit", "label", "norm", "norm_ref"):
        if field not in entry:
            _fail(name, "the clause has no '%s'" % field)
    _positive(name, "the clause", "value", entry["value"])
    if not entry["norm_ref"]:
        _fail(name, "the clause has no norm_ref -- a scalar taken from prose names the clause it came from")


def _check_set_values(name, entry, _data):
    """3.3.2.2 / 3.4.2.2: per family, the two design values the norm sets rather than deduces -- f_v,d and f_t,90,d, above 0."""
    if not entry.get("norm_ref"):
        _fail(name, "the clause has no norm_ref")
    families = entry.get("families")
    if not isinstance(families, dict) or not families:
        _fail(name, "the clause has no families")
    for family, values in families.items():
        for key in SET_DESIGN_VALUES:
            _positive(name, "families.%s" % family, key, values.get(key))


def _check_k_alpha(name, entry, data):
    _check_scalar(name, entry, data)
    _range(name, "k_alpha", entry.get("diameter_range"))


def _check_k_red(name, entry, _data):
    for key in ("spacing_reference", "spacing_exponent", "maximum", "single_fastener"):
        _positive(name, "k_red", key, entry.get(key))
    _number(name, "k_red", "n_exponent", entry.get("n_exponent"))
    if entry["n_exponent"] >= 0:
        _fail(name, "k_red: n_exponent is %s -- more fasteners in a row reduce, so it is negative" % entry["n_exponent"])


def _check_yield_moment(name, entry, _data):
    for key in ("factor", "exponent"):
        _positive(name, "M_u,k", key, entry.get(key))
    if not entry.get("unit"):
        _fail(name, "M_u,k has no unit")
    _range(name, "M_u,k", entry.get("diameter_range"))


def _check_embedment(name, table, _data):
    for key in ("factor", "predrilled_slope", "f_90_diameter_term"):
        _positive(name, "Tabelle 22", key, table.get(key))
    _number(name, "Tabelle 22", "undrilled_exponent", table.get("undrilled_exponent"))
    divisors = table.get("f_90_divisor")
    if not isinstance(divisors, dict) or not divisors:
        _fail(name, "Tabelle 22: no f_90_divisor -- one per species")
    for species_name, value in divisors.items():
        _positive(name, "Tabelle 22 f_90_divisor", species_name, value)
    for species_name in table.get("undrilled_species") or ():
        if species_name not in divisors:
            _fail(name, "Tabelle 22: undrilled_species names %r, which has no row" % species_name)
    _range(name, "Tabelle 22", table.get("diameter_range"))


def _check_kbeta_timber(name, table, _data):
    for key in ("t_exponent", "k_max_numerator"):
        _positive(name, "Tabelle 45", key, table.get(key))
    side = table.get("seitenholz") or {}
    for key in ("t_1_factor", "k_1_share", "t_2_factor"):
        _positive(name, "Tabelle 45 seitenholz", key, side.get(key))
    if side["t_1_factor"] >= side["t_2_factor"]:
        _fail(name, "Tabelle 45 seitenholz: t_1_factor %s is not below t_2_factor %s -- the lower corner comes first"
              % (side["t_1_factor"], side["t_2_factor"]))
    if side["k_1_share"] > 1:
        _fail(name, "Tabelle 45 seitenholz: k_1_share %s -- the lower corner's k_beta is a share of k_max" % side["k_1_share"])
    _positive(name, "Tabelle 45 mittelholz", "t_2_factor", (table.get("mittelholz") or {}).get("t_2_factor"))


def _check_kbeta_steel(name, table, _data):
    _positive(name, "Tabelle 46", "t_exponent", table.get("t_exponent"))
    for key in ("mittelholz_bleche_aussen", "seitenholz_scherfuge_a", "mittelholz_scherfuge_b"):
        corner = table.get(key)
        where = "Tabelle 46 %s" % key
        if not isinstance(corner, dict):
            _fail(name, "no '%s' corner" % key)
        for field in ("t_1_factor", "k_1"):
            _positive(name, where, field, corner.get(field), allow_zero=True)
        _positive(name, where, "t_2_factor", corner.get("t_2_factor"))
        if "k_2" in corner:
            _positive(name, where, "k_2", corner["k_2"])
        else:
            _positive(name, where, "k_2_root", corner.get("k_2_root"))
    conditions = table.get("conditions") or {}
    for key in ("equation_130_t2_over_t1", "equation_131_t1_over_t2"):
        _positive(name, "Tabelle 46 conditions", key, conditions.get(key))


# --- the tables of minimum distances and timber thicknesses (v0.87) ---------------

# The fasteners a table of distances is stated for, by the English key `#distance` takes (lib/distance.typ): the kinds of connector.TYPES that SIA 265 gives such a table for. A staple (6.6, SIA 265/1) and a glued-in rod have none, so no table may name them.
DISTANCE_FASTENERS = ("dowel", "bolt", "nail", "screw", "ring")

# What a cell of such a table holds -- one of three, and nothing else: a multiple of d (a number, or the norm's fraction [4, 3]), one multiple per diameter range (Tabellen 28 and 38 split a column at d = 4 mm), or Tabelle 41's multiple that depends on the angle between force and grain.
CELL_KINDS = ("factor", "cases", "alpha")


def _fraction(name, where, label, value):
    """A multiple as the norm writes it: a number, or [numerator, denominator] for 4/3. Returns its value."""
    if isinstance(value, list):
        if len(value) != 2:
            _fail(name, "%s: %s is %r -- a fraction is [numerator, denominator]" % (where, label, value))
        _positive(name, where, label + " numerator", value[0])
        _positive(name, where, label + " denominator", value[1])
        return value[0] / value[1]
    _positive(name, where, label, value)
    return value


def _notes(name, where, entry, footnotes, used):
    for ref in entry.get("notes") or ():
        if ref not in footnotes:
            _fail(name, "%s refers to footnote %r, which this table does not carry (footnotes: %s)"
                  % (where, ref, ", ".join(sorted(footnotes)) or "none"))
        used.add(ref)


def _check_distance_cell(name, where, cell, footnotes, used):
    if not isinstance(cell, dict):
        _fail(name, "%s: no cell -- {factor}, {cases} or {alpha}" % where)
    kinds = [k for k in CELL_KINDS if k in cell]
    if len(kinds) != 1:
        _fail(name, "%s carries %s -- a cell holds exactly one of %s" % (where, kinds or "none of them", ", ".join(CELL_KINDS)))
    if "factor" in cell:
        _fraction(name, where, "factor", cell["factor"])
    elif "cases" in cell:
        cases = cell["cases"]
        if not isinstance(cases, list) or len(cases) != 2:
            _fail(name, "%s: cases must be two, one up to a diameter and one above it" % where)
        low, high = cases
        _positive(name, where, "cases[0].d_max", low.get("d_max"))
        _positive(name, where, "cases[1].d_above", high.get("d_above"))
        if low["d_max"] != high.get("d_above"):
            _fail(name, "%s: the cases split at d = %s and d = %s -- one diameter, or some d falls in neither or in both"
                  % (where, low["d_max"], high["d_above"]))
        for case in cases:
            _fraction(name, where, "a case's factor", case.get("factor"))
    else:
        alpha = cell["alpha"]
        if not isinstance(alpha, dict):
            _fail(name, "%s: alpha must be {coefficient, base, divisor}" % where)
        coefficient = _fraction(name, where, "alpha.coefficient", alpha.get("coefficient"))
        base = _fraction(name, where, "alpha.base", alpha.get("base"))
        _positive(name, where, "alpha.divisor", alpha.get("divisor"))
        if coefficient * (base - 90.0 / alpha["divisor"]) <= 0:
            _fail(name, "%s: the spacing comes to nothing or less at alpha = 90° -- base and divisor are the wrong way round" % where)
    if cell.get("min") is not None:
        _positive(name, where, "min", cell["min"])
    _notes(name, where, cell, footnotes, used)


def _check_distances(name, table, _data):
    """A table of minimum distances or timber thicknesses, as lib/distance.typ prints it: what it is stated for, its head and columns as the page heads them, and one cell per row and column."""
    where = "Tabelle %s" % table.get("number")
    if FILES[name] != "table_%s" % table.get("number"):
        _fail(name, "carries table number %r under '%s'" % (table.get("number"), FILES[name]))
    for key in ("title", "norm", "norm_ref"):
        if not isinstance(table.get(key), str) or not table[key].strip():
            _fail(name, "%s has no '%s'" % (where, key))
    page = table.get("page")
    if isinstance(page, bool) or not isinstance(page, int) or page <= 0:
        _fail(name, "%s: page is %r -- the page of the German edition it was read off" % (where, page))
    if table.get("unit") != "mm":
        _fail(name, "%s: unit is %r -- a distance computed with d in mm is in mm" % (where, table.get("unit")))
    footnotes = table.get("footnotes")
    if not isinstance(footnotes, dict):
        _fail(name, "%s: no footnotes block -- write {} where the table has none" % where)
    used = set()
    fasteners = table.get("fasteners") or ()
    if not fasteners:
        _fail(name, "%s names no fastener it is stated for" % where)
    for entry in fasteners:
        if entry.get("fastener") not in DISTANCE_FASTENERS:
            _fail(name, "%s: fastener %r -- the kinds a distance table is stated for are %s"
                  % (where, entry.get("fastener"), ", ".join(DISTANCE_FASTENERS)))
        if not entry.get("clause"):
            _fail(name, "%s: fastener '%s' names no clause -- the norm says somewhere that the table is its" % (where, entry["fastener"]))
        if not isinstance(entry.get("auto"), bool):
            _fail(name, "%s: fastener '%s' has no 'auto' -- true where #distance shows it by itself" % (where, entry["fastener"]))
        if "scope" in entry and entry["scope"] not in DIAMETER_SCOPES:
            _fail(name, "%s: fastener '%s' names the scope %r -- the clauses stating a diameter range are %s"
                  % (where, entry["fastener"], entry["scope"], ", ".join(DIAMETER_SCOPES)))
    head = table.get("head")
    if not isinstance(head, dict) or not head.get("label"):
        _fail(name, "%s: no head -- the label over the first column" % where)
    _notes(name, where + " head", head, footnotes, used)
    columns = table.get("columns")
    if not isinstance(columns, list) or not columns:
        _fail(name, "%s: columns must be a list of {id, label}" % where)
    ids = [c.get("id") for c in columns]
    if len(set(ids)) != len(ids) or not all(ids):
        _fail(name, "%s: the column ids are %r -- each once" % (where, ids))
    for column in columns:
        if not isinstance(column.get("label"), str) or (len(columns) > 1 and not column["label"]):
            _fail(name, "%s: column '%s' has no label -- only a single column may go unnamed" % (where, column["id"]))
        _notes(name, "%s column '%s'" % (where, column["id"]), column, footnotes, used)
    rows = table.get("rows") or ()
    if not rows:
        _fail(name, "%s carries no row" % where)
    seen = set()
    for row in rows:
        rid = row.get("id")
        if not rid or rid in seen:
            _fail(name, "%s: row id %r is missing or listed twice" % (where, rid))
        seen.add(rid)
        if not row.get("label"):
            _fail(name, "%s: row '%s' has no label" % (where, rid))
        for cid in ids:
            _check_distance_cell(name, "%s row '%s' %s" % (where, rid, cid), row.get(cid), footnotes, used)
    orphans = sorted(set(footnotes) - used)
    if orphans:
        _fail(name, "%s carries footnote(s) %s that nothing refers to -- a mark was left off a cell" % (where, ", ".join(orphans)))


def _check_dowel_distances(name, table, data):
    """Tabelle 24 is read twice: by domains/dowel.py, whose three rows it must keep, and by lib/distance.typ like every other table of distances."""
    _check_spacings(name, table, data)
    _check_distances(name, table, data)


def _check_diameter_scope(name, entry, _data):
    """A clause stating the diameters a fastener's tables hold for."""
    for field in ("label", "norm", "norm_ref"):
        if not entry.get(field):
            _fail(name, "the clause has no '%s'" % field)
    _range(name, "the clause", entry.get("diameter_range"))


# --- the member checks of chapter 4.2 ------------------------------------------

# Anhang B's two tables, and the table of design values each one's grades must match row for row.
CHARACTERISTIC_OF = {TAB47: TAB08, TAB48: TAB09}
CHARACTERISTIC_NUMBERS = ("f_c_0_k", "E_0_05")


def _clause_head(name, entry):
    for field in ("norm", "norm_ref", "label"):
        if not isinstance(entry.get(field), str) or not entry[field].strip():
            _fail(name, "the clause has no '%s'" % field)


def _by_family(name, where, block):
    """A value per family of Tabelle 8 / Tabelle 9, and exactly those two."""
    if not isinstance(block, dict) or set(block) != set(FAMILIES):
        _fail(name, "%s is %r -- expected one value for each of %s" % (where, block, ", ".join(FAMILIES)))
    for family in FAMILIES:
        _positive(name, where, family, block[family])


def _check_characteristic(name, table, _data):
    """Anhang B, Tabelle 47 or 48: f_c,0,k and E_0,05 for exactly the grades of the matching Tabelle 8 or 9, E_0,05 below that grade's E_0,mean."""
    where = "Tabelle %s" % table.get("number")
    if FILES[name] != "table_%s" % table.get("number"):
        _fail(name, "carries table number %r under '%s'" % (table.get("number"), FILES[name]))
    units = table.get("units") or {}
    notes = table.get("notes") or {}
    for key in CHARACTERISTIC_NUMBERS:
        if key not in units:
            _fail(name, "%s: '%s' has no unit in the units block" % (where, key))
    source = CHARACTERISTIC_OF[name]
    design = {g["id"]: g for g in _read(source)[FILES[source]]["grades"]}
    family = table.get("family")
    seen = []
    for grade in table.get("grades") or ():
        gid = grade.get("id")
        if gid in seen:
            _fail(name, "%s: grade '%s' is listed twice -- one row per strength class" % (where, gid))
        seen.append(gid)
        row = "%s grade '%s'" % (where, gid)
        if gid not in design:
            _fail(name, "%s: %s.json gives no such strength class -- Anhang B tabulates the grades of Tabelle 8 and 9 (%s)"
                  % (row, source, ", ".join(design)))
        if grade.get("family") != family or family != design[gid]["family"]:
            _fail(name, "%s: family is %r -- the table is %r and %s.json says %r"
                  % (row, grade.get("family"), family, source, design[gid]["family"]))
        for key in CHARACTERISTIC_NUMBERS:
            _positive(name, row, key, grade.get(key))
        if grade["E_0_05"] >= design[gid]["E_0_mean"]:
            _fail(name, "%s: E_0_05 = %s is not below E_0,mean = %s -- a 5 percent fractile lies under the mean"
                  % (row, grade["E_0_05"], design[gid]["E_0_mean"]))
        for refs in (grade.get("notes") or {}).values():
            for ref in refs:
                if ref not in notes:
                    _fail(name, "%s refers to footnote %r, which this table does not carry" % (row, ref))
    missing = [g for g in design if g not in seen]
    if missing:
        _fail(name, "%s gives no row for %s -- every grade of %s.json needs its f_c,0,k and E_0,05"
              % (where, ", ".join(missing), source))


def _check_k_h(name, entry, _data):
    _clause_head(name, entry)
    for key in ("reference_height", "exponent", "maximum"):
        _positive(name, "k_h", key, entry.get(key))
    if entry["maximum"] <= 1:
        _fail(name, "k_h: maximum is %s -- k_h may only raise f_m,d, so its cap is above 1" % entry["maximum"])
    if not entry.get("families"):
        _fail(name, "k_h names no family it holds for")
    for family in entry["families"]:
        if family not in FAMILIES:
            _fail(name, "k_h: family %r -- expected one of %s" % (family, ", ".join(FAMILIES)))


def _check_shear_off(name, entry, _data):
    _clause_head(name, entry)
    _by_family(name, "factor", entry.get("factor"))
    for family in FAMILIES:
        if entry["factor"][family] > 1:
            _fail(name, "factor %s = %s -- Abscheren reduces f_v,d, so the factor is at most 1" % (family, entry["factor"][family]))
    _positive(name, "the clause", "min_shear_length", entry.get("min_shear_length"))


def _check_shear_transverse(name, entry, _data):
    _clause_head(name, entry)
    k = entry.get("k_t_90")
    if not isinstance(k, dict) or set(k) != {"querzug", "querdruck"}:
        _fail(name, "k_t_90 is %r -- expected querzug and querdruck" % (k,))
    for key in k:
        _positive(name, "k_t_90", key, k[key])
    if k["querdruck"] <= k["querzug"]:
        _fail(name, "k_t_90: querdruck (%s) is not above querzug (%s) -- transverse compression is the more favourable case"
              % (k["querdruck"], k["querzug"]))


def _check_buckling(name, entry, _data):
    _clause_head(name, entry)
    _by_family(name, "beta_c", entry.get("beta_c"))
    if entry["beta_c"]["Brettschichtholz"] >= entry["beta_c"]["Vollholz"]:
        _fail(name, "beta_c: Brettschichtholz (%s) is not below Vollholz (%s) -- glulam is the straighter product"
              % (entry["beta_c"]["Brettschichtholz"], entry["beta_c"]["Vollholz"]))
    for key in ("k_factor", "lambda_rel_offset", "lambda_rel_limit"):
        _positive(name, "the clause", key, entry.get(key))
    limits = entry.get("slenderness_limits") or {}
    for key in ("secondary", "primary"):
        _positive(name, "slenderness_limits", key, (limits.get(key) or {}).get("value"))
    if limits["primary"]["value"] >= limits["secondary"]["value"]:
        _fail(name, "slenderness_limits: primary (%s) is not below secondary (%s)" % (limits["primary"]["value"], limits["secondary"]["value"]))
    _by_family(name, "simplified_divisors", entry.get("simplified_divisors"))


def _check_lateral_buckling(name, entry, _data):
    _clause_head(name, entry)
    k = entry.get("k_m")
    if not isinstance(k, dict):
        _fail(name, "no k_m block -- the three branches of equation (39)")
    for key in ("lower_bound", "upper_bound", "intercept", "slope"):
        _positive(name, "k_m", key, k.get(key))
    if k["lower_bound"] >= k["upper_bound"]:
        _fail(name, "k_m: lower_bound %s is not below upper_bound %s" % (k["lower_bound"], k["upper_bound"]))
    # The straight middle branch meets 1 at the lower bound and 1/lambda^2 at the upper one, to the two decimals the norm prints.
    low = k["intercept"] - k["slope"] * k["lower_bound"]
    high = k["intercept"] - k["slope"] * k["upper_bound"]
    if abs(low - 1) > 0.01 or abs(high - 1 / k["upper_bound"] ** 2) > 0.01:
        _fail(name, "k_m: the middle branch runs from %.3f to %.3f -- it must join 1 at %s and 1/lambda^2 = %.3f at %s"
              % (low, high, k["lower_bound"], 1 / k["upper_bound"] ** 2, k["upper_bound"]))
    _positive(name, "the clause", "sigma_m_crit_factor", entry.get("sigma_m_crit_factor"))
    _positive(name, "the clause", "lambda_rel_m_factor", entry.get("lambda_rel_m_factor"))
    if abs(entry["lambda_rel_m_factor"] - entry["sigma_m_crit_factor"] ** -0.5) > 0.01:
        _fail(name, "lambda_rel_m_factor %s is not 1/sqrt(sigma_m_crit_factor %s) -- equation (42) is (41) put into (40)"
              % (entry["lambda_rel_m_factor"], entry["sigma_m_crit_factor"]))
    _by_family(name, "simplified_factors", entry.get("simplified_factors"))


def _check_fire(name, entry, _data):
    """Clause 4.5.2: Tabelle 13's rows, each read for some woods and families, every (wood, family) pair the engine may ask for found exactly once; d_red with the duration it holds up to; 4.5.2.4's widths rising with the duration; (51)'s factor above 1."""
    _clause_head(name, entry)
    charring = entry.get("charring")
    if not isinstance(charring, dict) or not isinstance(charring.get("rows"), list) or not charring["rows"]:
        _fail(name, "no charring rows -- Tabelle 13")
    seen = {}
    for row in charring["rows"]:
        rid = row.get("id") if isinstance(row, dict) else None
        if not isinstance(rid, str) or not rid:
            _fail(name, "a row of Tabelle 13 without an id: %r" % (row,))
        _positive(name, rid, "beta_n", row.get("beta_n"))
        for wood in row.get("woods") or []:
            if wood not in FIRE_WOODS:
                _fail(name, "%s: wood %r -- expected one of %s" % (rid, wood, ", ".join(FIRE_WOODS)))
            for family in row.get("families") or []:
                if family not in FAMILIES:
                    _fail(name, "%s: family %r -- expected one of %s" % (rid, family, ", ".join(FAMILIES)))
                if (wood, family) in seen:
                    _fail(name, "%s and %s both give a charring rate for %s %s" % (seen[(wood, family)], rid, wood, family))
                seen[(wood, family)] = rid
    missing = [(w, f) for w in FIRE_WOODS for f in FAMILIES if (w, f) not in seen]
    if missing:
        _fail(name, "Tabelle 13 gives no row for %s" % ", ".join("%s %s" % pair for pair in missing))
    d_red = entry.get("d_red") or {}
    _positive(name, "d_red", "value", d_red.get("value"))
    _positive(name, "d_red", "max_duration", d_red.get("max_duration"))
    rows = (entry.get("min_width") or {}).get("rows")
    if not isinstance(rows, list) or not rows:
        _fail(name, "no min_width rows -- 4.5.2.4")
    for before, after in zip(rows, rows[1:]):
        if not (after["duration"] > before["duration"] and after["b"] > before["b"]):
            _fail(name, "min_width: the rows must rise with the duration")
    for row in rows:
        _positive(name, "min_width", "duration", row.get("duration"))
        _positive(name, "min_width", "b", row.get("b"))
    factor = (entry.get("resistance_factor") or {}).get("value")
    _positive(name, "resistance_factor", "value", factor)
    if factor <= 1:
        _fail(name, "resistance_factor is %s -- (51) raises the design resistance" % factor)


_CHECKS = {
    ETA_T: _check_eta_t,
    TRUSS: _check_scalar,
    K_RED: _check_k_red,
    YIELD_MOMENT: _check_yield_moment,
    K_ALPHA: _check_k_alpha,
    SLIP: _check_slip,
    OTHER_SOLID: _check_set_values,
    OTHER_GLULAM: _check_set_values,
    TAB01: _check_gamma_m,
    TAB03: _check_classes,
    TAB04: _check_eta_w,
    TAB08: _check_grades,
    TAB09: _check_grades,
    TAB22: _check_embedment,
    TAB24: _check_dowel_distances,
    TAB25: _check_kser,
    TAB45: _check_kbeta_timber,
    TAB46: _check_kbeta_steel,
    TAB27: _check_distances,
    TAB28: _check_distances,
    TAB32: _check_distances,
    TAB33: _check_distances,
    TAB36: _check_distances,
    TAB37: _check_distances,
    TAB38: _check_distances,
    TAB39: _check_distances,
    TAB40: _check_distances,
    TAB41: _check_distances,
    NAIL_DIAMETERS: _check_diameter_scope,
    SCREW_DIAMETERS: _check_diameter_scope,
    K_H: _check_k_h,
    SHEAR_OFF: _check_shear_off,
    SHEAR_TRANSVERSE: _check_shear_transverse,
    BUCKLING: _check_buckling,
    LATERAL_BUCKLING: _check_lateral_buckling,
    TAB47: _check_characteristic,
    TAB48: _check_characteristic,
    FIRE: _check_fire,
}


# --- what the rest of the pipeline reads ------------------------------------

def edition():
    """The edition every value read here belongs to, "SIA 265:2021" -- cited in the report and recorded in each var's `source` (docs/project/purpose.md §1bis). Every file must name the same one."""
    editions = {name: _read(name)["edition"] for name in FILES}
    distinct = set(editions.values())
    if len(distinct) > 1:
        listed = ", ".join("%s: %s" % (n, e) for n, e in sorted(editions.items()))
        raise validation.ValidationError(
            "calc/norms/sia265-*: the files name more than one edition (%s) -- they are read from one PDF and must say so" % listed)
    return distinct.pop()


def grades():
    """Every strength class, Tabelle 8's then Tabelle 9's, keyed by id. A class listed in both tables stops the export: the two are read as one catalogue and an id means one thing."""
    out = {}
    for name in (TAB08, TAB09):
        data = _read(name)
        for grade in data[FILES[name]]["grades"]:
            if grade["id"] in out:
                raise validation.ValidationError(
                    "calc/norms/sia265-*: grade '%s' is given by two tables -- Tabelle 8 and Tabelle 9 are read as one catalogue"
                    % grade["id"])
            out[grade["id"]] = grade
    return out


def grade(name):
    """One strength class, by the name Excel and Woodcore spell it ("C24", "GL24h"). An unknown name fails listing the ones the norm gives -- and says which norms are missing, since GL40h and the CLT classes are deliberately absent."""
    known = grades()
    if name in known:
        return known[name]
    raise validation.ValidationError(
        "calc/norms/sia265-*: no strength class %r -- SIA 265 gives %s. GL40h and above belong to SN EN 14080 and the CLT classes to SIA 265/1; neither edition is in the reference library yet."
        % (name, ", ".join(known)))


def grade_table(name):
    """The number of the table a strength class is read from -- "8" (Vollholz) or "9" (Brettschichtholz) --, what a design value of the class cites (`#member` prints «Tabelle 8», «Tabelle 9»)."""
    grade(name)
    return "9" if name in {g["id"] for g in table_9()["grades"]} else "8"


def rho_k(name):
    """The characteristic density of one strength class, in kg/m3 -- the 5 % fractile, what SIA 265 Tabelle 22 computes a Lochleibungsfestigkeit from."""
    return grade(name)["rho_k"]


def species(name):
    """"Nadelholz" or "Laubholz" for one strength class -- which branch of Tabelle 22 its Lochleibungsfestigkeit is read from. It is the norm's own column, so it is never asked of the engineer."""
    return grade(name)["species"]


def table_8():
    """Tabelle 8 as the file states it: its title, its citation, the unit and label of each property, one row per strength class, and the footnotes those rows refer to."""
    return _read(TAB08)["table_8"]


def table_9():
    """Tabelle 9, as table_8() gives Tabelle 8."""
    return _read(TAB09)["table_9"]


def eta_w(moisture_class, kind="resistance"):
    """The moisture factor of SIA 265 Tabelle 4: `kind` is "resistance" (the Tragwiderstand column, what a resistance is multiplied by) or "stiffness" (the Steifigkeit column, what K_ser is). Class 1 gives 1.0 in both."""
    if kind not in ETA_W_KINDS:
        raise validation.ValidationError(
            "calc/norms/sia265-*: eta_w kind %r -- use %s" % (kind, " or ".join(repr(k) for k in ETA_W_KINDS)))
    table = _read(TAB04)["table_4"]
    for entry in table["classes"]:
        if entry["id"] == moisture_class:
            return entry[kind]
    raise validation.ValidationError(
        "calc/norms/sia265-*: no Feuchteklasse %r -- SIA 265 Tabelle 3 gives %s"
        % (moisture_class, ", ".join(str(c) for c in moisture_class_ids())))


def moisture_classes():
    """The classes of Tabelle 3 with their moisture range and what they describe -- what the report prints beside eta_w."""
    return _read(TAB03)["table_3"]["classes"]


def moisture_class_ids():
    """The ids of Tabelle 3's classes, (1, 2, 3) -- what a position's Feuchteklasse is checked against and what Woodcore offers. Read, never restated: validation.py asks here."""
    return tuple(entry["id"] for entry in moisture_classes())


def species_names():
    """The species Tabelle 22 has a row for, ("Nadelholz", "Laubholz") -- the only species a grade may carry, since a Lochleibungsfestigkeit is read off that row."""
    return tuple(embedment()["f_90_divisor"])


def eta_t(impact=False):
    """The factor of clause 2.2.6: 1.0 in general, and 1.4 for stossartige Einwirkungen -- an earthquake, an impact, a dynamic road load. `impact` is the engineer's own statement about the connection, so it is a flag and not a lookup."""
    block = _read(ETA_T)["eta_t"]
    return block["impact"] if impact else block["normal"]


def eta_t_block():
    """The eta_t block entire, for the label and the clause the report cites beside the factor."""
    return _read(ETA_T)["eta_t"]


# The design values 3.3.2.2 and 3.4.2.2 set for a class neither table lists; every other strength of such a class is deduced (2.2.2).
SET_DESIGN_VALUES = ("f_v_d", "f_t_90_d")
# A member's family (calc/domains/materials_contract.FAMILIES) -> its clause and its ratio γ_M/η_M of Tabelle 1.
FAMILY_CLAUSE = {"softwood": OTHER_SOLID, "hardwood": OTHER_SOLID, "glulam": OTHER_GLULAM}
FAMILY_GAMMA = {"softwood": "solid", "hardwood": "solid", "glulam": "glulam"}


def set_design_value(family, key):
    """(value, clause, page) of a design value 3.3.2.2 or 3.4.2.2 sets for `family` ("softwood", "hardwood", "glulam") -- `key` "f_v_d" or "f_t_90_d" --, or None for a key the norm deduces."""
    if key not in SET_DESIGN_VALUES:
        return None
    if family not in FAMILY_CLAUSE:
        raise validation.ValidationError("calc/norms/sia265-*: no family %r -- %s" % (family, ", ".join(FAMILY_CLAUSE)))
    clause = _read(FAMILY_CLAUSE[family])["clause"]
    return clause["families"][family][key], clause["norm_ref"], clause["page"]


def family_gamma_m(family):
    """γ_M/η_M of Tabelle 1 for a member's family."""
    return gamma_m(FAMILY_GAMMA[family])


def gamma_m(kind):
    """One ratio gamma_M/eta_M of Tabelle 1, by its id: "solid", "glulam", "connection" or "connection_ductile"."""
    table = _read(TAB01)["table_1"]
    for entry in table["entries"]:
        if entry["id"] == kind:
            return entry["value"]
    raise validation.ValidationError(
        "calc/norms/sia265-*: no gamma_M/eta_M for %r -- SIA 265 Tabelle 1 gives %s"
        % (kind, ", ".join(e["id"] for e in table["entries"])))


def table_24():
    """Tabelle 24 as the file states it -- the rows, their labels and the two directions, for the table the report prints."""
    return _read(TAB24)["table_24"]


def dowel_spacings(d):
    """The minimum spacings of Tabelle 24 in mm, for a dowel of diameter `d`: {row id: {"parallel": mm, "perpendicular": mm}}. The loaded end's absolute floor of 80 mm is applied here, where the norm prints it in the cell."""
    _positive(TAB24, "dowel_spacings", "d", d)
    out = {}
    for row in table_24()["rows"]:
        entry = {}
        for direction in DIRECTIONS:
            spec = row[direction]
            value = spec["factor"] * d
            if spec["min"] is not None:
                value = max(value, spec["min"])
            entry[direction] = value
        out[row["id"]] = entry
    return out


def table_25():
    """Tabelle 25 as the file states it -- the two families, their coefficients and the exponents of the formula."""
    return _read(TAB25)["table_25"]


def kser_coefficients(family):
    """The two coefficients of Tabelle 25 for one family, "timber-timber" or "steel-timber": {"parallel": c0, "perpendicular": c90}, to be used as K_ser = c * rho_k^0.5 * d^1.7."""
    table = table_25()
    for entry in table["families"]:
        if entry["id"] == family:
            return {d: entry[d] for d in DIRECTIONS}
    raise validation.ValidationError(
        "calc/norms/sia265-*: no K_ser family %r -- SIA 265 Tabelle 25 gives %s"
        % (family, ", ".join(e["id"] for e in table["families"])))


def kser(family, rho_k_value, d, alpha):
    """K_ser per dowel and shear plane in N/mm, for Feuchteklasse 1 and short-term loading (SIA 265 6.2.1.4). `alpha` is the angle between the force and the grain in degrees; the norm interpolates linearly between the parallel and the perpendicular value, so 0 gives K_ser,0 and 90 gives K_ser,90."""
    coefficients = kser_coefficients(family)
    exponents = table_25()["exponents"]
    if not 0 <= alpha <= 90:
        raise validation.ValidationError(
            "calc/norms/sia265-*: K_ser at alpha = %s deg -- the angle between force and grain is folded into 0 to 90" % alpha)
    base = rho_k_value ** exponents["rho_k"] * d ** exponents["d"]
    parallel = coefficients["parallel"] * base
    perpendicular = coefficients["perpendicular"] * base
    return parallel - (parallel - perpendicular) * alpha / 90.0


def slip():
    """The slip of a dowel connection in mm, clause 6.2.1.3, with the clause and the wording the report prints beside it."""
    return _read(SLIP)["slip"]


def clause(name):
    """One scalar the norm states under its own symbol, with its value, its unit, its label and its clause: "k_alpha" (6.2.1.1) or "truss_reduction" (5.3.6.2.2)."""
    if name in CLAUSES:
        return _read(CLAUSES[name])["clause"]
    raise validation.ValidationError(
        "calc/norms/sia265-*: no clause %r -- the scalars stated under their own symbol are %s" % (name, ", ".join(sorted(CLAUSES))))


def constant(name):
    """The bare value of `clause(name)`, for the arithmetic."""
    return clause(name)["value"]


def reduction():
    """Equation (86) and Tabelle 21's n = 1, clause 6.1.4.2: {n_exponent, spacing_reference, spacing_exponent, maximum, single_fastener, norm_ref, equation}."""
    return _read(K_RED)["clause"]


def yield_moment():
    """Equation (87), clause 6.1.4.4: {factor, exponent, unit, diameter_range, norm_ref, equation}."""
    return _read(YIELD_MOMENT)["clause"]


def resistance_diameters():
    """The diameters equation (88) is stated for, clause 6.2.1.1: {min, max, unit}."""
    return clause("k_alpha")["diameter_range"]


def embedment():
    """Tabelle 22's coefficients: {factor, predrilled_slope, undrilled_exponent, f_90_diameter_term, f_90_divisor, undrilled_species, diameter_range}."""
    return _read(TAB22)["table_22"]


def table_45():
    """Anhang A, Tabelle 45's coefficients -- the corners k_beta is interpolated between, Holz-Holz."""
    return _read(TAB45)["table_45"]


def table_46():
    """Anhang A, Tabelle 46's coefficients -- the corners k_beta is interpolated between, Stahl-Holz -- and the two conditions printed above equations (130) and (131)."""
    return _read(TAB46)["table_46"]


def distance_table(number):
    """One table of minimum distances or timber thicknesses by its number, "28" or 28 -- as the file states it: its title, its page, the fasteners it is stated for, its head, its columns, its rows and its footnotes. What lib/distance.typ prints, read here for the tests and for anything in Python that wants the same numbers."""
    for name in DISTANCE_TABLES:
        if FILES[name] == "table_%s" % number:
            return _read(name)[FILES[name]]
    raise validation.ValidationError(
        "calc/norms/sia265-*: no table of distances %r -- SIA 265 gives %s"
        % (number, ", ".join(FILES[n][len("table_"):] for n in DISTANCE_TABLES)))


def diameter_scope(name):
    """The diameters a fastener's tables hold for, {min, max, unit}, out of the clause `name` states them in (one of DIAMETER_SCOPES)."""
    if name not in DIAMETER_SCOPES:
        raise validation.ValidationError(
            "calc/norms/sia265-*: %r states no diameter range -- the clauses that do are %s" % (name, ", ".join(DIAMETER_SCOPES)))
    return _read(name)["clause"]["diameter_range"]


def _multiple(value):
    return value[0] / value[1] if isinstance(value, list) else value


def distance(cell, d, alpha=0):
    """One cell of a table of distances, in mm, for a fastener of diameter `d` mm: its multiple of d -- the case d falls in, or Tabelle 41's at the angle `alpha` in degrees between force and grain -- and the absolute floor where the cell carries one. The arithmetic lib/distance.typ does, written once more so a test can hold the two equal."""
    _positive("distance", "distance", "d", d)
    if "cases" in cell:
        low, high = cell["cases"]
        factor = _multiple(low["factor"] if d <= low["d_max"] else high["factor"])
    elif "alpha" in cell:
        spec = cell["alpha"]
        if not 0 <= alpha <= 90:
            raise validation.ValidationError(
                "calc/norms/sia265-*: alpha = %s deg -- the angle between force and grain is folded into 0 to 90" % alpha)
        factor = _multiple(spec["coefficient"]) * (_multiple(spec["base"]) - alpha / spec["divisor"])
    else:
        factor = _multiple(cell["factor"])
    value = factor * d
    if cell.get("min") is not None:
        value = max(value, cell["min"])
    return value


def table_47():
    """Anhang B, Tabelle 47 as the file states it: f_c,0,k and E_0,05 of the grades of Tabelle 8."""
    return _read(TAB47)["table_47"]


def table_48():
    """Anhang B, Tabelle 48, as table_47() gives Tabelle 47: the grades of Tabelle 9."""
    return _read(TAB48)["table_48"]


def characteristic(name):
    """One strength class's row of Anhang B, {id, family, f_c_0_k, E_0_05, ...}, in N/mm² -- what the relative slenderness of 4.2.8.4 and 4.2.9.3 reads. An unknown name fails as grade() does."""
    grade(name)
    for table in (table_47(), table_48()):
        for row in table["grades"]:
            if row["id"] == name:
                return row
    raise validation.ValidationError("calc/norms/sia265-*: Anhang B gives no row for %r" % name)


def k_h():
    """Clause 3.4.2.3, equation (5): {reference_height, exponent, maximum, unit, families, not_with, ...}. A permission for glulam's f_m,d; solid timber has none."""
    return _read(K_H)["clause"]


def shear_off():
    """Clause 4.2.6: {factor: {Vollholz, Brettschichtholz}, min_shear_length, unit, ...}."""
    return _read(SHEAR_OFF)["clause"]


def shear_transverse():
    """Clause 4.2.7.1, equation (28): {k_t_90: {querzug, querdruck}, exclusive_with, ...}."""
    return _read(SHEAR_TRANSVERSE)["clause"]


def buckling():
    """Clause 4.2.8: {beta_c: {Vollholz, Brettschichtholz}, k_factor, lambda_rel_offset, lambda_rel_limit, slenderness_limits, simplified_divisors, ...}."""
    return _read(BUCKLING)["clause"]


def lateral_buckling():
    """Clause 4.2.9: {k_m: {lower_bound, upper_bound, intercept, slope}, sigma_m_crit_factor, lambda_rel_m_factor, simplified_factors, ...}."""
    return _read(LATERAL_BUCKLING)["clause"]


def fire():
    """Clause 4.5.2, the fire situation: {charring: {rows, table, ...}, d_red: {value, max_duration}, min_width: {rows}, resistance_factor: {value, not_with}, simplified_action, equations, ...}."""
    return _read(FIRE)["clause"]


def family(name):
    """"Vollholz" or "Brettschichtholz": which of Tabelle 8 / Tabelle 9 a strength class is read from."""
    return characteristic(name)["family"]


def charring_rate(name, wood=None):
    """Tabelle 13's row for a strength class and a choice of wood: {id, label, beta_n, ...}. `wood` None follows the grade -- a Nadelholz grade is softwood; a Laubholz grade must say beech or oak, and None then fails, which the member check turns into a reason it cannot be calculated."""
    if wood is not None and wood not in FIRE_WOODS:
        raise validation.ValidationError("calc/norms/%s: wood %r -- expected one of %s" % (FIRE, wood, ", ".join(FIRE_WOODS)))
    if wood is None:
        if species(name) != "Nadelholz":
            raise validation.ValidationError(
                "calc/norms/%s: %s is %s -- Tabelle 13 reads beech and oak at different rates, so the wood must be named" % (FIRE, name, species(name)))
        wood = "softwood"
    fam = family(name)
    for row in fire()["charring"]["rows"]:
        if wood in row["woods"] and fam in row["families"]:
            return row
    raise validation.ValidationError("calc/norms/%s: no row of Tabelle 13 for %s %s" % (FIRE, wood, fam))


def check_all():
    """Read and check every file, for a test or for an export that wants to fail early rather than at the first lookup."""
    for name in FILES:
        _read(name)
    return edition()
