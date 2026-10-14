"""The values of SIA 263:2013 this project calculates with, out of the JSON files beside this module in `calc/norms/` (docs/architecture/layout.md §11).

The steel counterpart of `sia265.py`, and built on exactly its pattern: `calc/norms/` is the one source of every value taken from a norm for a calculation made in Python, one file per table named `<norm>-<year>-<table>-<designation>.json`, every number transcribed by hand from `ExternalFiles/000-Normes/SIA263-2013-DE.pdf` at a page that can be turned to, each file's `_source` naming it, and the whole checked here before anything is built from it (section 2 rule 13, section 3.6).

    sia263-2013-tab01-baustaehle.json   Tabelle 1, the structural steels: S235, S275, S355, S460 (3.2.2.3)
    sia263-2013-tab02-schrauben.json    Tabelle 2, the bolt classes: 4.6 .. 10.9 (3.4.2)

**Both tables are graphics in the PDF and do not extract as text.** They were read off a render of pages 18 and 19. That is worth saying because it is the one case where «read from the norm» means read with the eyes rather than with `extract_text()`, and where a second reader checking the transcription has to do the same.

**What this is for, today.** Woodcore's «Connecteurs» tab offers the grade of the **plate** of a Stahl-Holz joint, which is Tabelle 1's (a Holz-Holz joint has no plate, and the row is not shown). `fastener_grades()` joins Tabelle 1 and Tabelle 2 for a fastener -- a Bolzen or a Passbolzen being a Schraube -- and is kept for the kinds of fastener still to come.

**A Stabdübel's steel is asked for since 12.10.2026** (spec 2026-10-12-audit-issues-47-48-49, D-06, D-20): SN EN 14592:2022 Tabelle G.9 gives a dowel's bar only a minimum yield stress, so the f_u,k SIA 265 6.1.4.4 reads is this table's f_u of the grade (`norms/sn_en_14592.f_u_k`), S355 by default -- the 510 N/mm² the project credited until then to SN EN 14592+A1:2012.

⚠️ **Tabelle 3 is deliberately not transcribed.** Its «Stifte» are the pins of fastenings and supports, by its own Anwendungsbereich column, not the Stabdübel of a timber connection.

⚠️ **The Lochleibungswiderstand of the plate is not here either** (SIA 263 6.1.4, p. 66). It is the one piece of the connectors' agreed scope still unbuilt (section 14); when it is written it adds a file beside this module rather than a number to a domain module.
"""

import json
from pathlib import Path

import validation

HERE = Path(__file__).resolve().parent

# Every file this module reads, and the key its table sits under. The reader checks that both name the same edition: two files disagreeing about which SIA 263 they were read from would be two norms pretending to be one.
FILES = {
    "sia263-2013-tab01-baustaehle": "table_1",
    "sia263-2013-tab02-schrauben": "table_2",
    "sia263-2013-tab16-lochleibung": "table_16",
    # the steel members of Woodcore's «Acier» tabs (spec 2026-10-12-section-acier): 3.2.2.3's E and G, 4.1.3's gamma_M1, Tabelle 5's slenderness limits
    "sia263-2013-3.2.2-kennwerte": "properties",
    "sia263-2013-4.1.3-widerstandsbeiwerte": "factors",
    "sia263-2013-tab05-schlankheit": "table_5",
}

# The two thickness bands of Tabelle 1, in the order the table sets them.
BANDS = ("thin", "thick")

# Every value a Tabelle 1 band must carry, as the table heads them.
BAND_NUMBERS = ("f_y", "tau_y", "f_u")

# Every value a Tabelle 2 class must carry.
BOLT_NUMBERS = ("f_yb", "f_ub", "eps_u")

# Which table an entry of `fastener_grades()` came from, so a citation names the right one.
STEEL_TABLE, BOLT_TABLE = "Tabelle 1", "Tabelle 2"

_cache = {}


def _fail(message):
    raise validation.ValidationError("calc/norms/sia263: %s" % message)


def _load(stem):
    if stem not in _cache:
        path = HERE / ("%s.json" % stem)
        if not path.is_file():
            _fail("%s.json is missing" % stem)
        try:
            _cache[stem] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            _fail("%s.json is not valid JSON: %s" % (stem, exc))
    return _cache[stem]


def _number(value, where):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail("%s is %r -- expected a number" % (where, value))
    if value <= 0:
        _fail("%s is %s -- expected a positive strength" % (where, value))
    return float(value)


# --- the edition ---------------------------------------------------------------

def edition():
    """The edition every value here was read from -- what a var's `source` names (section 2 rule 5)."""
    return _load("sia263-2013-tab01-baustaehle")["edition"]


# --- Tabelle 1: the structural steels ------------------------------------------

def _table_1():
    return _load("sia263-2013-tab01-baustaehle")["table_1"]


def grades():
    """The Baustahl grades, in the order Tabelle 1 lists them."""
    return tuple(entry["name"] for entry in _table_1()["grades"])


def grade(name):
    """One grade's two thickness bands. An unknown one is refused by name, listing what the table has."""
    for entry in _table_1()["grades"]:
        if entry["name"] == name:
            return entry
    _fail("no steel grade %r in Tabelle 1 -- it gives %s" % (name, ", ".join(grades())))


def band_for(thickness=None):
    """Which band of Tabelle 1 a thickness falls in. `None` -- a thickness not stated -- takes the thin band, which is the common plate and the safe default for a value that is only displayed."""
    if thickness is None:
        return "thin"
    limit = _table_1()["bands"][0]["max_thickness"]
    return "thin" if thickness <= limit else "thick"


def steel(name, thickness=None):
    """{f_y, tau_y, f_u} of one grade at one thickness, in N/mm²."""
    return dict(grade(name)[band_for(thickness)])


def f_u(name, thickness=None):
    """The tensile strength of a structural steel, in N/mm²."""
    return steel(name, thickness)["f_u"]


def bands():
    """The two bands, each with its label and its upper thickness -- what a tooltip says."""
    return tuple(dict(b) for b in _table_1()["bands"])


# --- Tabelle 2: the bolt classes -----------------------------------------------

def _table_2():
    return _load("sia263-2013-tab02-schrauben")["table_2"]


def bolt_classes():
    """The Festigkeitsklassen, in the order Tabelle 2 lists them."""
    return tuple(entry["name"] for entry in _table_2()["classes"])


def bolt(name):
    """One bolt class: f_yb, f_ub, eps_u, and whether SIA 263 calls it usual in Switzerland."""
    for entry in _table_2()["classes"]:
        if entry["name"] == name:
            return entry
    _fail("no bolt class %r in Tabelle 2 -- it gives %s" % (name, ", ".join(bolt_classes())))


def bolt_footnote():
    """What the table says about the classes it marks: too little elongation at rupture to be usual here."""
    return _table_2()["footnote"]


# --- the one list the interface offers -----------------------------------------

def fastener_grades():
    """Every grade a fastener may be made of, as ({name, f_u, table, norm_ref, note}), Tabelle 1 then Tabelle 2.

    Joined here rather than in the window, because which table a value came from has to travel with it: a
    plain round Stabdübel is a structural steel and a Bolzen is a Schraube, and a report citing the wrong
    table would be citing a number the norm does not give for that fastener.
    """
    out = []
    for name in grades():
        out.append({"name": name, "f_u": f_u(name), "table": STEEL_TABLE,
                    "norm_ref": _table_1()["norm_ref"], "note": ""})
    footnote = bolt_footnote()
    for name in bolt_classes():
        entry = bolt(name)
        out.append({"name": name, "f_u": float(entry["f_ub"]), "table": BOLT_TABLE,
                    "norm_ref": _table_2()["norm_ref"],
                    "note": "" if entry.get("common", True) else footnote})
    return tuple(out)


def plate_grades():
    """The grades a steel plate may be, which is Tabelle 1 and nothing else."""
    return grades()


# --- Tabelle 16 and 6.2.5: the bearing of a plate on a dowel --------------------

def bearing():
    """Equation (76) of Tabelle 16 with its conditions, the Bolzen's cap of 6.2.5 and gamma_M2 of 4.1.3: {number, norm_ref, equation, page, factor, limit, e2_min, p2_min, pin: {norm_ref, page, factor}, gamma_M2: {value, norm_ref, page}} (spec 2026-10-12-audit-issues-47-48-49, D-16)."""
    return _load("sia263-2013-tab16-lochleibung")["table_16"]


# --- the checks ----------------------------------------------------------------

def check_all():
    """Read and check every file. Called by the export before a value is taken out, so a defective transcription stops the export naming the line rather than printing a wrong resistance."""
    editions = set()
    for stem, key in FILES.items():
        data = _load(stem)
        if not isinstance(data.get("edition"), str) or not data["edition"]:
            _fail("%s.json names no edition" % stem)
        editions.add(data["edition"])
        if key not in data:
            _fail("%s.json carries no %r" % (stem, key))
        for field in ("number", "title", "norm", "norm_ref"):
            if not data[key].get(field):
                _fail("%s.json: the table carries no %r" % (stem, field))
    if len(editions) > 1:
        _fail("the files name %d different editions (%s) -- they must all be one norm"
              % (len(editions), ", ".join(sorted(editions))))

    table_1 = _table_1()
    if [b["id"] for b in table_1["bands"]] != list(BANDS):
        _fail("Tabelle 1's bands are %r -- expected %r" % ([b["id"] for b in table_1["bands"]], list(BANDS)))
    previous = 0
    for band in table_1["bands"]:
        limit = band.get("max_thickness")
        if not isinstance(limit, (int, float)) or limit <= previous:
            _fail("Tabelle 1, band %r: max_thickness %r does not rise" % (band["id"], limit))
        previous = limit

    seen = set()
    for entry in table_1["grades"]:
        name = entry.get("name")
        if not name:
            _fail("Tabelle 1 has a grade with no name")
        if name in seen:
            _fail("Tabelle 1 lists %r twice" % name)
        seen.add(name)
        for band in BANDS:
            if band not in entry:
                _fail("Tabelle 1, %s: no %r band" % (name, band))
            for field in BAND_NUMBERS:
                _number(entry[band].get(field), "Tabelle 1, %s, %s.%s" % (name, band, field))
        # The thick band is the thin one reduced: a transcription that got them the wrong way round
        # would read as a steel that grows stronger with thickness, which no steel does.
        for field in BAND_NUMBERS:
            if entry["thick"][field] > entry["thin"][field]:
                _fail("Tabelle 1, %s: %s is larger in the thick band (%s) than in the thin one (%s) -- the bands are swapped"
                      % (name, field, entry["thick"][field], entry["thin"][field]))
        if entry["thin"]["f_u"] <= entry["thin"]["f_y"]:
            _fail("Tabelle 1, %s: f_u (%s) is not above f_y (%s)" % (name, entry["thin"]["f_u"], entry["thin"]["f_y"]))

    table_2 = _table_2()
    if not table_2.get("footnote"):
        _fail("Tabelle 2 carries no footnote, which is what says a class is not usual here")
    seen = set()
    for entry in table_2["classes"]:
        name = entry.get("name")
        if not name:
            _fail("Tabelle 2 has a class with no name")
        if name in seen:
            _fail("Tabelle 2 lists %r twice" % name)
        seen.add(name)
        for field in BOLT_NUMBERS:
            _number(entry.get(field), "Tabelle 2, %s, %s" % (name, field))
        if not isinstance(entry.get("common"), bool):
            _fail("Tabelle 2, %s: `common` is %r -- expected true or false" % (name, entry.get("common")))
        # A class is named after its own two numbers: 8.8 is f_ub = 800 and f_yb = 0.8 * f_ub.
        head, tail = name.split(".")
        if abs(float(head) * 100 - float(entry["f_ub"])) > 1e-9:
            _fail("Tabelle 2, %s: f_ub is %s -- a class %s carries %s" % (name, entry["f_ub"], name, float(head) * 100))
        if abs(float(head) * float(tail) * 10 - float(entry["f_yb"])) > 1e-9:
            _fail("Tabelle 2, %s: f_yb is %s -- a class %s carries %s"
                  % (name, entry["f_yb"], name, float(head) * float(tail) * 10))
    t16 = bearing()
    for where, value in (("factor", t16.get("factor")), ("limit", t16.get("limit")), ("e2_min", t16.get("e2_min")), ("p2_min", t16.get("p2_min")),
                         ("pin.factor", (t16.get("pin") or {}).get("factor")), ("gamma_M2", (t16.get("gamma_M2") or {}).get("value"))):
        _number(value, "Tabelle 16, %s" % where)
    if not t16["factor"] < t16["limit"]:
        _fail("Tabelle 16: the factor of (76) %s is not below its limit %s" % (t16["factor"], t16["limit"]))
    _check_steel_members()
    return True


# --- the steel members (spec 2026-10-12-section-acier) --------------------------
# What the checks of Woodcore's «Acier» tabs read besides Tabelle 1: 3.2.2.3's E and G, 4.1.3's gamma_M1 (gamma_M2 is Tabelle 16's file's, `bearing()`), and Tabelle 5a/5b's slenderness limits. Each value is a file's; nothing here writes one.

def _properties():
    return _load("sia263-2013-3.2.2-kennwerte")["properties"]


def material():
    """{E, G, nu, rho_a, norm_ref, page} of a structural steel, E and G in N/mm² (3.2.2.3)."""
    p = _properties()
    return {"E": float(p["E"]["value"]), "G": float(p["G"]["value"]), "nu": float(p["nu"]["value"]),
            "rho_a": float(p["rho_a"]["value"]), "norm_ref": p["norm_ref"], "page": p["page"]}


def gamma_M1():
    """{value, norm_ref, page}: the resistance factor of the strength and stability checks (4.1.3)."""
    f = _load("sia263-2013-4.1.3-widerstandsbeiwerte")["factors"]
    return {"value": float(f["gamma_M1"]["value"]), "norm_ref": f["norm_ref"], "page": f["page"]}


def gamma_M2():
    """{value, norm_ref, page}: the resistance factor of fasteners and the net section (4.1.3), as Tabelle 16's file carries it."""
    g = bearing()["gamma_M2"]
    return {"value": float(g["value"]), "norm_ref": g["norm_ref"], "page": g["page"]}


def table_5():
    """Tabelle 5a and 5b as their file states them (see its _note for the kinds of formula)."""
    return _load("sia263-2013-tab05-schlankheit")["table_5"]


def epsilon(f_y):
    """epsilon = sqrt(f_y,ref / f_y), Tabelle 5's reduction factor for the higher grades."""
    return (table_5()["epsilon"]["f_y_ref"] / float(f_y)) ** 0.5


def _check_steel_members():
    m = material()
    for key in ("E", "G", "rho_a"):
        _number(m[key], "3.2.2.3, %s" % key)
    if not 0 < m["nu"] < 0.5:
        _fail("3.2.2.3: nu is %s -- a Poisson ratio lies between 0 and 0.5" % m["nu"])
    if abs(m["G"] - m["E"] / (2 * (1 + m["nu"]))) > 0.005 * m["G"]:
        _fail("3.2.2.3: G = %s is not E/(2(1+nu)) = %.0f -- one of the three is mistyped" % (m["G"], m["E"] / (2 * (1 + m["nu"]))))
    _number(gamma_M1()["value"], "4.1.3, gamma_M1")
    t5 = table_5()
    for name, eps in t5["epsilon"]["check"].items():
        if abs(epsilon(steel(name)["f_y"]) - eps) > 0.0006:
            _fail("Tabelle 5: epsilon of %s is printed %s, sqrt(235/f_y) gives %.4f" % (name, eps, epsilon(steel(name)["f_y"])))
    for part in ("internal", "outstand"):
        for row in ("compression",) + (("bending",) if part == "internal" else ()):
            limits = t5[part][row]
            if len(limits) != 3 or not limits[0] < limits[1] < limits[2]:
                _fail("Tabelle 5 %s, %s: %r -- three limits rising from class 1 to class 3" % (part, row, limits))
