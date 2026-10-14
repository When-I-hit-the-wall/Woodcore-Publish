"""Member checks (vérifications d'élément): one source file each, written by Woodcore, resolved here, calculated in Typst (docs/domain/connectors.md §3.3nonies, docs/domain/member-checks.md §3.3undecies).

A member check is the saved form of what `#member` and a `#verify-*` command write in the report by hand: which member, with which section, strength class and moisture class, under which action. It is a file of its own, `Woodcore-Datei/checks/<id>.json`, written by Woodcore and read by this module alone -- the arrangement of `connectors/`, for the same reasons (docs/decisions.md §13). **Nothing is computed here**: the check is computed in the report by `#show-check-member` (lib/timber.typ), which reads the record this module exports and calls `#member` and the `#verify-*` of its kind with the values written out -- `#verify-tension`; for a compression `#verify-compression(stability: false)` along the grain and `#verify-compression-perp` at an angle; for a bending `#verify-bending(stability: false)` without a normal force and `#verify-bending-normal(stability: false)` with one. What this module does is store, check and resolve -- the connector's reference pattern applied to a member.

**A value follows its position unless it is stated.** `grade`, `section` and `moisture_class` are `null` (follow the position the check names, read afresh at every export, so *Import données* is all it takes) or a value (written over, and staying so). The record says where each came from, `*_from`: "position", "stated", or None where neither gives one.

**What warns and what stops.** A malformed source stops the export, naming the file and the field (docs/architecture/data-contracts.md §3.6): an id that is not its file name, a kind that is not one of `KINDS`, a kind not implemented yet, an angle outside 0..90, a stated strength class SIA 265 does not give, a stated section with a side of 0. Anything the *project* lacks -- a position that is gone, a position with no section, no strength class, no moisture class, a force that is not a tension -- is never a stop (the v0.33 rule): the check is exported `calculable: false` with its reason, and `#show-check-member` refuses it with that reason.

**A compression** (SIA 265 4.2.2) takes one angle, like a tension. At 0 it is the section alone, sigma_c,0,d = N/A <= f_c,0,d (4.2.2.1) -- buckling is a check of its own, «Flambage». Above 0 it is a contact: (11) at 90°, (12) with f_c,alpha,d of (13) between, over the area `l` x `w`, `w` following the section's width b unless stated, and f_c,90,d read from Tabelle 8 or 9 for one of its three `case`s, the bracketed value where `larger` says the larger indentations provably do not matter. The force is the one field `N`, its magnitude positive: the normal force over the whole section along the grain, the force on the contact area at an angle.

**A bending** (SIA 265 4.2.3 and 4.2.4, the module «Flexion») is the section alone: lateral torsional buckling and buckling are checks of their own, «Déversement» and «Flambage». It reads the moments `M_y` and `M_z` (a {value, unit} block each, absent or 0 being no moment, their sign immaterial) and `N` **signed**, tension positive -- the one kind whose N is: 0 is (14) along the grain or (17) to (20) at an angle; a tension is (21), a compression (22). At an angle it reads M_y alone, and with a normal force (21) or (22) are applied with the strengths at that angle -- f_t,alpha,d of (9) or f_c,alpha,d of (13) and k_mt,alpha or k_mc,alpha of (19), (20) -- on the side where N adds, the other side by (17) or (18) alone: the engineer's reading of 08.10.2026, the norm writing neither equation at an angle (docs/decisions.md §13).

**Buckling, lateral torsional buckling and shear** (issue #38, 11.10.2026) are checks of their own. `buckling` (4.2.8) is a compression along the grain with its stability, `#verify-compression(stability: true)`, read with the system lengths `l_y`, `l_z` and the coefficients `beta_y`, `beta_z` (l_k = beta · l, a length of 0 held). `lateral-torsional` (4.2.9) is a bending along the grain with its stability: the moments, the distance `a` between the lateral supports or a `sigma_m_crit` of a finer calculation, and N signed -- 0 `#verify-bending`, a tension (21) with (38), a compression (22) with (37), which also reads the buckling lengths (the engineer, 11.10.2026, D-09). `shear` (4.2.5) reads the shear forces `V_z`, `V_y` and `pith`, and no N: `#verify-shear`, torsion staying a kind of its own.

Only `tension` (SIA 265 4.2.1), `compression` (4.2.2), `bending` (4.2.3, 4.2.4), `shear` (4.2.5), `buckling` (4.2.8) and `lateral-torsional` (4.2.9) are implemented; the other kinds are listed so that a source naming one is refused as «not implemented yet» rather than as unknown.
"""

import json
import math
import re
from pathlib import Path

import engine
import project
import shown_variables
import validation
from domains import links
from norms import sia265, vkf

DOMAIN = "member-check"
SOURCE_SCHEMA = "member-check-source"
EXPORT_SCHEMA = "checks"
SOURCE_SCHEMA_VERSION = "1.0"
# 1.1 is 1.0 with `links` (spec 2026-10-11-variables-liees-champs-et-textes, D-17): written only by a source that carries one, so a check that follows no variable is saved and exported byte for byte as before
LINKED_SCHEMA_VERSION = "1.1"
# 1.2 is 1.1 with `fire`, the design situation fire of SIA 265 4.5.2 (issue #46, spec 2026-10-12-resistance-au-feu ARCH-RISK-005): written only by a check in the fire situation, `links` or not -- every other check is saved and exported byte for byte as before
FIRE_SCHEMA_VERSION = "1.2"
SOURCE_SCHEMA_VERSIONS = (SOURCE_SCHEMA_VERSION, LINKED_SCHEMA_VERSION, FIRE_SCHEMA_VERSION)
EXPORT_SCHEMA_VERSION = "1.0"
LINKED_EXPORT_VERSION = "1.1"
FIRE_EXPORT_VERSION = "1.2"

# The kinds a check in the fire situation may be (D-09: bending with its shear as two checks, buckling, compression and tension of the section -- no lateral torsional buckling), all along the grain
FIRE_KINDS = ("tension", "compression", "bending", "shear", "buckling")
# The keys of `fire` in a source, and the default of a new one: the three faces of a beam under a slab (SIA 265 Figur 13a), the duration following VKF 15-15
FIRE_KEYS = ("duration", "sides", "wood", "top_level")
FIRE_DEFAULT = {"duration": None, "sides": {"bottom": True, "top": False, "left": True, "right": True}, "wood": None, "top_level": False}
# The keys #member publishes in the fire situation alone (lib/shown-variables.json `member`), which the window offers for such a check only
FIRE_MEMBER_KEYS = ("t_fi", "beta_n", "d_char_n", "d_red", "d_ef", "b", "h", "k_fi")
# The project's building, which VKF 15-15 reads a duration off (project.building_file)
BUILDING_SCHEMA = "fire-building"
BUILDING_SCHEMA_VERSION = "1.0"

# The file data/checks.json is written to, which lib/timber.typ reads (`show-check-member`, `check-member-ids`).
EXPORT_FILE = "checks.json"

# The folder of the project's sources this domain reads (project.SOURCE_FOLDERS, Project.checks_dir).
SOURCES = "checks"

# Every kind of member check the window may offer, in the order it lists them, and the ones calculated so far.
KINDS = ("tension", "compression", "bending", "shear", "torsion", "buckling", "lateral-torsional", "deformation", "vibration")
IMPLEMENTED = ("tension", "compression", "bending", "shear", "buckling", "lateral-torsional")
# The kinds read along the grain alone: their alpha is 0
ALONG_GRAIN = ("shear", "buckling", "lateral-torsional")

# Which f_c,90,d of SIA 265 Tabelle 8 or 9 a compression at an angle reads (4.2.2.2): «generell», with at least 100 mm of timber beyond the load on both sides, or at an end support -- and the table's own words for each, which the record carries.
CASES = ("generell", "mit_vorholz", "endauflagerung")
CASE_WORDS = {"generell": "generell", "mit_vorholz": "mit Vorholz", "endauflagerung": "Endauflagerung"}
# The bracketed value of Tabelle 8 note 4 (Tabelle 9 note 3): the larger indentations provably without influence on the load-bearing member.
LARGER_WORDS = "grössere Eindrückungen"

# A check's id is its file name and the string the report addresses it by -- connector.ID_PATTERN's rule.
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$")

# The sections a member check computes with: a rectangle and a circle, which is what `#member` computes (docs/domain/member-checks.md §3.3undecies).
SECTION_TYPES = ("rec", "cir")

# The units a design force and a design moment may be written in; the report's unit algebra converts any of them.
FORCE_UNITS = ("kN", "N", "MN")
MOMENT_UNITS = ("kNm", "Nm", "MNm")
# The moments of a bending, in the order the window and the call give them.
MOMENTS = ("M_y", "M_z")
# The shear forces of a shear check: in the plane of h (z) and of b (y)
SHEAR_FORCES = ("V_z", "V_y")
# The system lengths and buckling length coefficients of a buckling check (and of a lateral torsional buckling with a compression): l_k = beta · l, about y and about z
LENGTHS = ("l_y", "l_z")
BETAS = ("beta_y", "beta_z")
# The largest shear stress of a section at its centroid is V/A times this -- mechanics, not the norm: SIA 265 (23) states tau_d <= f_v,d and no factor (SIA265-2021-DE p. 33). lib/timber.typ (`timber-shear-stress`) writes the same two, and tests/test_member_check.py holds them equal.
SHEAR_FACTORS = {"rec": 1.5, "cir": 4 / 3}

# The fields a variable of the export may fill (REQ-009), by their key in the source, with the unit each is written in -- None where the field's own {value, unit} block says it. The strength class, the moisture class, the case and every other choice from a list take none (T6, §8).
LINKABLE = {
    "N": None, "V_z": None, "V_y": None, "M_y": None, "M_z": None,
    "alpha": "°",
    "section.b": "mm", "section.h": "mm", "section.d": "mm",
    "l": "mm", "w": "mm", "l_y": "mm", "l_z": "mm", "a": "mm",
    "beta_y": "", "beta_z": "",
    "sigma_m_crit": "N/mm²",
}


def _fail(where, message):
    raise validation.ValidationError("%s: %s" % (where, message))


def _number(value):
    return not isinstance(value, bool) and isinstance(value, (int, float))


def _fmt(value):
    """A number as a section's text and a Typst call write it: at most six decimals, trailing zeros dropped -- 100, 101.6."""
    text = f"{float(value):.6f}".rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


def _typst_str(text):
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _typst_dict(levels):
    """`shown:` as Typst writes it: `(A: 2, W_y: 1)`, `(:)` where nothing is chosen -- every key a registry key, a bare identifier."""
    return "(" + ", ".join("%s: %d" % (key, n) for key, n in levels.items()) + ")" if levels else "(:)"


# --- the source ---------------------------------------------------------------

def _dir(here=None):
    return (here or project.current()).checks_dir


def source_paths(here=None):
    """Every member-check source of the project, in file-name order."""
    directory = _dir(here)
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*.json"))


def check_source(src, where="checks"):
    """Everything that makes a source malformed, as a ValidationError naming `where` and the field. Nothing about the project -- a position gone, a section missing -- is checked here: that is `resolve`'s, and never a stop."""
    if not isinstance(src, dict):
        _fail(where, "a member check is a JSON object")
    version = src.get("schema_version")
    if version not in SOURCE_SCHEMA_VERSIONS:
        _fail(where, "schema_version is %r -- this reads %s" % (version, ", ".join(SOURCE_SCHEMA_VERSIONS)))
    if links.LINKS in src and version == SOURCE_SCHEMA_VERSION:
        _fail(where, "carries links at schema_version %r -- a source following a variable is %r" % (version, LINKED_SCHEMA_VERSION))
    links.check_links(src, LINKABLE, lambda message: _fail(where, message), "the check")
    for key in links.links_of(src):
        if key.startswith("section.") and not isinstance(src.get("section"), dict):
            _fail(where, "%s follows a variable and the check states no section -- it follows its position's; state the section, or take the link off" % key)
    # the kind before the structure: an unknown kind and one not implemented yet each say so in words of their own
    kind = src.get("kind")
    if kind not in KINDS:
        _fail(where, "kind %r -- the kinds of member check are %s" % (kind, ", ".join(KINDS)))
    if kind not in IMPLEMENTED:
        _fail(where, "kind %r is not implemented yet -- only %s is" % (kind, ", ".join(IMPLEMENTED)))
    # the fire before the structure: its refusals name the file (issue #46)
    _check_fire(src, where)
    validation.validate_structure(src, SOURCE_SCHEMA)
    cid = src.get("id", "")
    if not ID_PATTERN.match(cid or ""):
        _fail(where, "id %r -- letters, digits and _ . + - only, starting with a letter or digit" % cid)
    position = src.get("position")
    if position is not None and not str(position).strip():
        _fail(where, "position is an empty string -- name a position, or null for a member that is none")
    grade = src.get("grade")
    if grade is not None:
        known = sia265.grades()
        if grade not in known:
            _fail(where, "grade %r is not a strength class of SIA 265 Tabelle 8 or 9 (%s) -- or null to follow the position"
                  % (grade, ", ".join(known)))
    section = src.get("section")
    if section is not None:
        stype = section.get("type")
        if stype not in SECTION_TYPES:
            _fail(where, "section type %r -- a member check computes %s" % (stype, " or ".join(SECTION_TYPES)))
        sides = ("d",) if stype == "cir" else ("b", "h")
        for side in sides:
            value = section.get(side)
            if not _number(value) or value <= 0:
                _fail(where, "section.%s is %r -- a side in mm, above 0" % (side, value))
        for side in ("b", "h", "d"):
            if side not in sides and side in section:
                _fail(where, "section.%s is not a side of a %s section" % (side, stype))
    moisture = src.get("moisture_class")
    if moisture is not None and moisture not in validation.moisture_classes():
        _fail(where, "moisture_class %r -- expected %s, or null to follow the position"
              % (moisture, ", ".join(str(c) for c in validation.moisture_classes())))
    alpha = src.get("alpha", 0)
    if not _number(alpha) or not 0 <= alpha <= 90:
        _fail(where, "alpha is %r -- the angle between the force and the grain, in degrees, 0 to 90" % (alpha,))
    if kind in ALONG_GRAIN and alpha != 0:
        _fail(where, "alpha is %r -- a %s check is along the grain, alpha 0" % (alpha, kind))
    force = src.get("N")
    if kind == "shear" and force is None:
        pass     # a shear check reads its shear forces, and no N
    elif not isinstance(force, dict) or not _number(force.get("value")):
        _fail(where, "N is %r -- a {value, unit} block, the design force: a tension's positive, a compression's and a buckling's magnitude positive, a bending's and a lateral torsional buckling's normal force signed (tension positive)" % (force,))
    elif force.get("unit") not in FORCE_UNITS:
        _fail(where, "N.unit is %r -- %s" % (force.get("unit"), ", ".join(FORCE_UNITS)))
    # a shear check's forces: absent or null is none; one that is there is a {value, unit} block
    for key in SHEAR_FORCES:
        shear = src.get(key)
        if shear is None:
            continue
        if not isinstance(shear, dict) or not _number(shear.get("value")):
            _fail(where, "%s is %r -- a {value, unit} block, the design shear force, or null for none" % (key, shear))
        if shear.get("unit") not in FORCE_UNITS:
            _fail(where, "%s.unit is %r -- %s" % (key, shear.get("unit"), ", ".join(FORCE_UNITS)))
    if src.get("pith") is not None and not isinstance(src.get("pith"), bool):
        _fail(where, "pith is %r -- true or false" % (src.get("pith"),))
    # buckling lengths: a system length in mm, 0 or above (0 held against buckling), and its coefficient, 0 or above
    for key in LENGTHS + BETAS:
        value = src.get(key)
        if value is not None and (not _number(value) or value < 0):
            _fail(where, "%s is %r -- %s, 0 or above, or null" % (key, value, "a system length in mm" if key in LENGTHS else "a buckling length coefficient"))
    # lateral torsional buckling: the distance between the lateral supports, or the critical stress of a finer calculation -- one, not both
    for key, what in (("a", "the distance between the lateral supports, in mm"), ("sigma_m_crit", "the critical bending stress, in N/mm²")):
        value = src.get(key)
        if value is not None and (not _number(value) or value <= 0):
            _fail(where, "%s is %r -- %s, above 0, or null" % (key, value, what))
    if src.get("a") is not None and src.get("sigma_m_crit") is not None:
        _fail(where, "a and sigma_m_crit are both given -- (41) computes sigma_m,crit from a; give one or the other")
    # a bending's moments: absent or null is no moment; one that is there is a {value, unit} block
    for key in MOMENTS:
        moment = src.get(key)
        if moment is None:
            continue
        if not isinstance(moment, dict) or not _number(moment.get("value")):
            _fail(where, "%s is %r -- a {value, unit} block, the design moment, or null for none" % (key, moment))
        if moment.get("unit") not in MOMENT_UNITS:
            _fail(where, "%s.unit is %r -- %s" % (key, moment.get("unit"), ", ".join(MOMENT_UNITS)))
    # a compression at an angle: the case of Tabelle 8 or 9, the bracketed value, the contact area
    case = src.get("case")
    if case is not None and case not in CASES:
        _fail(where, "case is %r -- %s, or null for generell" % (case, ", ".join(CASES)))
    larger = src.get("larger")
    if larger is not None and not isinstance(larger, bool):
        _fail(where, "larger is %r -- true or false" % (larger,))
    if larger and (case or "generell") == "generell":
        _fail(where, "larger is true with case generell -- SIA 265 Tabelle 8 and 9 give a bracketed f_c,90,d for mit_vorholz and endauflagerung only")
    for key in ("l", "w"):
        value = src.get(key)
        if value is not None and (not _number(value) or value <= 0):
            _fail(where, "%s is %r -- a contact %s in mm, above 0, or null" % (key, value, "length" if key == "l" else "width"))
    if kind == "compression" and alpha > 0 and src.get("l") is None:
        _fail(where, "l is null -- a compression at an angle to the grain needs the contact length along the grain, in mm")


def _check_fire(src, where):
    """`fire` (issue #46): at 1.2 only, on a kind of FIRE_KINDS along the grain, its keys FIRE_KEYS, a duration in whole minutes above 0 or null, the four faces each true or false, a wood of Tabelle 13 or null. A duration beyond what d_red is stated for is no malformation but a check that cannot be calculated (`resolve`)."""
    fire = src.get("fire")
    if fire is None:
        if "fire" in src:
            _fail(where, "fire is null -- a check at normal temperature carries no fire key")
        return
    if src.get("schema_version") != FIRE_SCHEMA_VERSION:
        _fail(where, "carries fire at schema_version %r -- a check in the fire situation is %r" % (src.get("schema_version"), FIRE_SCHEMA_VERSION))
    kind = src.get("kind")
    if kind not in FIRE_KINDS:
        _fail(where, "fire on a %s check -- the fire situation is checked for %s" % (kind, ", ".join(FIRE_KINDS)))
    if src.get("alpha", 0) != 0:
        _fail(where, "fire with alpha %r -- a check in the fire situation is along the grain" % (src.get("alpha"),))
    if not isinstance(fire, dict):
        _fail(where, "fire is %r -- an object {duration, sides, wood, top_level}" % (fire,))
    unknown = sorted(set(fire) - set(FIRE_KEYS))
    if unknown:
        _fail(where, "fire.%s is no key of fire -- %s" % (unknown[0], ", ".join(FIRE_KEYS)))
    duration = fire.get("duration")
    if duration is not None and (isinstance(duration, bool) or not isinstance(duration, int) or duration <= 0):
        _fail(where, "fire.duration is %r -- whole minutes above 0, or null to follow VKF 15-15" % (duration,))
    sides = fire.get("sides")
    if not isinstance(sides, dict) or set(sides) != set(sia265.FIRE_SIDES) or any(not isinstance(v, bool) for v in sides.values()):
        _fail(where, "fire.sides is %r -- %s, each true or false" % (sides, ", ".join(sia265.FIRE_SIDES)))
    wood = fire.get("wood")
    if wood is not None and wood not in sia265.FIRE_WOODS[1:]:
        _fail(where, "fire.wood is %r -- %s, or null for a softwood grade" % (wood, ", ".join(sia265.FIRE_WOODS[1:])))
    if not isinstance(fire.get("top_level", False), bool):
        _fail(where, "fire.top_level is %r -- true or false" % (fire.get("top_level"),))


def read_source(path):
    """One source, read and checked; its id must be its file name."""
    path = Path(path)
    where = "checks/%s" % path.name
    try:
        src = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _fail(where, "cannot be read as JSON -- %s" % exc)
    check_source(src, where)
    if src["id"] != path.stem:
        _fail(where, "id %r is not its file name %r -- the id is the file name" % (src["id"], path.stem))
    return src


def stamp_version(src):
    """The schema_version a source is saved at, the lowest that holds what it carries: 1.2 with `fire` (links or not), 1.1 with a link, 1.0 with neither -- what Woodcore's window calls before it writes one."""
    if not links.links_of(src):
        src.pop(links.LINKS, None)
    if src.get("fire") is not None:
        src["schema_version"] = FIRE_SCHEMA_VERSION
    else:
        src.pop("fire", None)
        src["schema_version"] = LINKED_SCHEMA_VERSION if links.links_of(src) else SOURCE_SCHEMA_VERSION
    return src


def list_sources(here=None):
    """Every source of the project as a dict, sorted by file name, **unchecked** -- what Woodcore lists, so that one malformed file does not empty the list; a file that is not a JSON object is left out. `read_source` is what checks one."""
    out = []
    for path in source_paths(here):
        try:
            src = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(src, dict):
            out.append(src)
    return out


def new_source(cid, kind="tension", fire=False):
    """A new source with Woodcore's defaults: no position, every value to be stated or to follow one, a force of 10 kN along the grain -- for a compression the fields of a contact, `case` generell, `larger` false, `l` and `w` null (w following the section's width); for a bending a moment M_y of 10 kNm, no M_z and no normal force; for a buckling system lengths of 3 m, beta 1; for a lateral torsional buckling a bending with a = 3 m; for a shear V_z = 10 kN and no N. `fire` makes it a check in the fire situation (issue #46): FIRE_DEFAULT, at 1.2."""
    if fire:
        src = new_source(cid, kind)
        src["fire"] = json.loads(json.dumps(FIRE_DEFAULT))
        return stamp_version(src)
    src = {
        "schema_version": SOURCE_SCHEMA_VERSION,
        "id": cid,
        "name": "",
        "label": "",
        "group": "",
        "kind": kind,
        "position": None,
        "grade": None,
        "section": None,
        "moisture_class": None,
        "impact": False,
        "alpha": 0,
        "N": {"value": 10, "unit": "kN"},
    }
    if kind == "compression":
        src.update(case="generell", larger=False, l=None, w=None)
    if kind == "bending":
        src.update(N={"value": 0, "unit": "kN"}, M_y={"value": 10, "unit": "kNm"}, M_z=None)
    if kind == "buckling":
        src.update(l_y=3000, l_z=3000, beta_y=1, beta_z=1)
    if kind == "lateral-torsional":
        src.update(N={"value": 0, "unit": "kN"}, M_y={"value": 10, "unit": "kNm"}, M_z=None, a=3000, sigma_m_crit=None,
                   l_y=None, l_z=None, beta_y=1, beta_z=1)
    if kind == "shear":
        del src["N"]
        src.update(V_z={"value": 10, "unit": "kN"}, V_y=None, pith=False)
    return src


# --- what the project gives it -------------------------------------------------

def _section_record(section):
    """A section as the record carries it: {type, b, h} or {type, d}, with the text a summary prints."""
    if section["type"] == "cir":
        return {"type": "cir", "d": section["d"], "text": "Ø %s mm" % _fmt(section["d"])}
    return {"type": "rec", "b": section["b"], "h": section["h"], "text": "%s/%s mm" % (_fmt(section["b"]), _fmt(section["h"]))}


def _table_of(grade):
    """The table of SIA 265 a strength class is read from: 8 (Vollholz) or 9 (Brettschichtholz)."""
    return sia265.table_8() if grade in {g["id"] for g in sia265.table_8()["grades"]} else sia265.table_9()


def _contact(src, grade, section):
    """What a compression at an angle to the grain reads beyond the member, as the record carries it: the case of Tabelle 8 or 9 and its words, the bracketed value or not, the table's f_c,90,d (before eta_w and eta_t, which the report applies -- read, not computed), the contact length and its width -- the section's b unless stated --, and why it cannot be calculated where it cannot. All null for a tension and for a compression along the grain, which read none of it. `grade` is None where the check already cannot be calculated."""
    out = {"case": None, "larger": None, "l": None, "w": None, "w_from": None, "case_label": None, "f_c_90_table": None, "reason": ""}
    if src["kind"] != "compression" or src.get("alpha", 0) == 0:
        return out
    case = src.get("case") or "generell"
    larger = bool(src.get("larger", False))
    out.update(case=case, larger=larger, l=src.get("l"),
               case_label=CASE_WORDS[case] + (" (%s)" % LARGER_WORDS if larger else ""))
    if src.get("w") is not None:
        out.update(w=src["w"], w_from="stated")
    elif section is not None and section["type"] == "rec":
        out.update(w=section["b"], w_from="section")
    elif section is not None:
        out["reason"] = "a round section gives no contact width to follow -- state the width w of the contact area"
    if grade is not None and grade in sia265.grades():
        cell = sia265.grade(grade)["f_c_90_d"][case]
        value = (cell.get("groessere_eindrueckungen") if larger else cell.get("value")) if isinstance(cell, dict) else (None if larger else cell)
        if value is None and not out["reason"]:
            out["reason"] = ("SIA 265 Tabelle %s gives %s no bracketed f_c,90,d for %s -- the larger indentations cannot be taken"
                             % (_table_of(grade).get("number", ""), grade, CASE_WORDS[case]))
        out["f_c_90_table"] = value
    return out


def read_building(here=None):
    """The project's building (project.building_file), checked: None where the file is absent -- a gap of the project, which a check following VKF 15-15 then says --, a ValidationError naming the field where it is malformed (a file Woodcore wrote)."""
    path = (here or project.current()).building_file
    if not path.is_file():
        return None
    where = "Woodcore-Datei/%s" % path.name
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _fail(where, "cannot be read as JSON -- %s" % exc)
    validation.validate_structure(data, BUILDING_SCHEMA, where)
    vkf.check_building(data, where)
    return data


def write_building(building, here=None):
    """Writes the project's building, checked first; stamps its schema_version. What the «Résistance au feu» tab saves (issue #46)."""
    path = (here or project.current()).building_file
    data = {"schema_version": BUILDING_SCHEMA_VERSION}
    data.update({key: building[key] for key in vkf.BUILDING_KEYS})
    validation.validate_structure(data, BUILDING_SCHEMA, "Woodcore-Datei/%s" % path.name)
    vkf.check_building(data, "Woodcore-Datei/%s" % path.name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return data


def fire_duration(fire, building):
    """The duration a check in the fire situation is computed for, and where it came from: (minutes, "stated", None) where `fire.duration` is written; else (minutes, "vkf", requirement) from VKF 15-15 for `building` and the check's `top_level` -- minutes None where there is no building or the table has no row, 0 where it requires nothing."""
    requirement = vkf.required_resistance(building, fire.get("top_level", False)) if building else None
    if fire.get("duration") is not None:
        return fire["duration"], "stated", requirement
    if requirement is None:
        return None, None, None
    return requirement["minutes"], "vkf", requirement


def _fire_block(src, grade, section, building):
    """The `fire` of a record, and why the check cannot be calculated if it cannot: the duration and its provenance, the faces, the row of Tabelle 13, d_ef and the residual b and h -- the arithmetic `#member(fire:)` does, written here for the window and the summary and held equal to it by a test. `grade` and `section` None where the check already cannot be calculated."""
    fire = src["fire"]
    clause = sia265.fire()
    sides = [side for side in sia265.FIRE_SIDES if fire["sides"].get(side)]
    minutes, origin, requirement = fire_duration(fire, building)
    out = {"duration": minutes if minutes else None, "duration_from": origin if minutes else None, "requirement": requirement, "sides": sides,
           "wood": None, "top_level": bool(fire.get("top_level", False)), "beta_n": None, "d_ef": None, "b": None, "h": None}
    if minutes is None:
        return out, (requirement["reason"] + " -- state the fire resistance of this check" if requirement and requirement["reason"]
                     else "no fire resistance -- state one, or give the project's building in the «Résistance au feu» tab (VKF 15-15)")
    if minutes == 0:
        return out, ("VKF 15-15 table %s requires no fire resistance of this load-bearing structure%s -- state a duration to check it anyway"
                     % (requirement["table"], " (note [%s])" % ", ".join(requirement["notes"]) if requirement["notes"]
                        else " (%s)" % requirement["exemption"] if requirement.get("exemption") else ""))
    if minutes > clause["d_red"]["max_duration"]:
        return out, ("%d minutes -- SIA 265 %s states d_red for a fire resistance up to %d minutes only"
                     % (minutes, clause["d_red"]["norm_ref"], clause["d_red"]["max_duration"]))
    if not sides:
        return out, "no face exposed to the fire -- tick the faces the fire reaches"
    if grade is None or section is None:
        return out, ""
    if section["type"] != "rec":
        return out, "a round section -- the residual section of SIA 265 4.5.2.2 (Figur 13) is computed for a rectangle"
    try:
        row = sia265.charring_rate(grade, fire.get("wood"))
    except validation.ValidationError:
        return out, "%s is %s -- SIA 265 Tabelle 13 reads beech and oak at different rates: choose the wood" % (grade, sia265.species(grade))
    out["wood"] = fire.get("wood") or "softwood"
    d_ef = row["beta_n"] * minutes + clause["d_red"]["value"]
    out.update(beta_n=row["beta_n"], d_ef=d_ef)
    if len(sides) >= 2:
        need = next((r for r in clause["min_width"]["rows"] if minutes <= r["duration"]), None)
        least = min(section["b"], section["h"])
        if need is not None and least < need["b"]:
            return out, ("%s mm is under the minimum width of %d mm SIA 265 %s sets for R%d with the fire on several faces"
                         % (_fmt(least), need["b"], clause["min_width"]["norm_ref"], need["duration"]))
    b = section["b"] - sum(1 for s in sides if s in sia265.FIRE_WIDTH_SIDES) * d_ef
    h = section["h"] - sum(1 for s in sides if s in sia265.FIRE_HEIGHT_SIDES) * d_ef
    if b <= 0 or h <= 0:
        return out, "the fire leaves no section -- d_ef = %s mm on %d faces of %s" % (_fmt(d_ef), len(sides), section["text"])
    out.update(b=b, h=h)
    return out, ""


def resolve(src, positions, values=None, building=None):
    """The record of one checked source against `positions` ({id: position record}, as export_all builds them, or connector.known_positions reads them back): the source's fields with `grade`, `section` and `moisture_class` resolved, where each came from, whether the check can be calculated and why not, and the warnings it earned (engine.Note). Nothing is computed and nothing stops.

    A field that follows a variable (`links`) takes the value `values` give it now (`links.index`'s shape); one whose variable cannot be read keeps the number the source holds, its last value, with a warning (D-06). The record then carries `links`, where each linked value came from (REQ-012)."""
    cid = src["id"]
    where = "checks/%s.json" % cid
    warnings = []
    provenance = {}
    if values is not None:
        src, provenance, notes = links.apply_links(src, values, LINKABLE, where)
        warnings.extend(notes)
    pid = src.get("position")
    record = None
    if pid is not None:
        record = (positions or {}).get(pid)
        if record is None:
            warnings.append(engine.Note("check_position_missing", "%s: position %s is not a position of the project -- the values it would give are not there" % (where, pid),
                                        check=cid, position=pid))

    def follow(stated, from_position):
        if stated is not None:
            return stated, "stated"
        if record is not None:
            value = from_position(record)
            if value is not None and value != "":
                return value, "position"
        return None, None

    def position_grade(rec):
        if "strength_class" in rec:
            return (rec.get("strength_class") or "").strip()
        return (rec.get("material") or "").strip()

    grade, grade_from = follow(src.get("grade"), position_grade)

    reason = ""
    section, section_from = None, None
    if src.get("section") is not None:
        section, section_from = _section_record(src["section"]), "stated"
    elif record is not None:
        held = record.get("section")
        if held and held.get("type") in SECTION_TYPES:
            section, section_from = _section_record(held), "position"
        elif held:
            reason = reason or ("position %s's section %s is %s -- a member check computes a rectangular or a round section; state the section here"
                                % (pid, held.get("text", ""), "steel" if held.get("kind") == "steel" else "neither"))
    moisture, moisture_from = follow(src.get("moisture_class"), lambda rec: rec.get("moisture_class"))

    if not reason and section is None:
        reason = ("position %s gives no section -- state it here, or give the position a section type in the Positions tab" % pid
                  if record is not None else "no section -- state one, or name a position that has one")
    if not reason and not grade:
        reason = ("position %s gives no strength class -- state it here" % pid if record is not None
                  else "no strength class -- state one, or name a position that has one")
    if not reason and grade not in sia265.grades():
        reason = "strength class %r of position %s is not one of SIA 265 Tabelle 8 or 9 -- state one here" % (grade, pid)
    if not reason and moisture is None:
        reason = ("position %s states no moisture class -- state it here, or in the Positions tab" % pid if record is not None
                  else "no moisture class -- state one, or name a position that has one")
    kind = src["kind"]
    alpha = src.get("alpha", 0)
    if not reason and kind in ("tension", "compression", "buckling") and src["N"]["value"] <= 0:
        force_text_ = "%s %s" % (_fmt(src["N"]["value"]), src["N"]["unit"])
        reason = ("N is %s -- a tension is positive, and a compression is no tension check" % force_text_ if kind == "tension"
                  else "N is %s -- a %s check takes the force's magnitude, positive" % (force_text_, kind))
    lengths = {key: src.get(key) for key in LENGTHS}
    betas = {key: (src.get(key) if src.get(key) is not None else 1) for key in BETAS}
    shears = {key: (src.get(key) if src.get(key) and src[key]["value"] != 0 else None) for key in SHEAR_FORCES}
    compressed = kind == "lateral-torsional" and src["N"]["value"] < 0
    if not reason and (kind == "buckling" or compressed) and any(lengths[key] is None for key in LENGTHS):
        reason = ("no system length about %s -- buckling reads l_y and l_z (0 holds the member against buckling about that axis)" % " and ".join(key[-1] for key in LENGTHS if lengths[key] is None)
                  + (", which (37) reads with a compression" if compressed else ""))
    if not reason and kind == "lateral-torsional":
        # the moment that tips is the one about the strong axis -- y, or z where the section is wider than high (D-09); a round section does not tip and reads either moment with k_m = 1 (D-10, D-15); a rectangle wider than high bent about y alone has nothing to tip and is checked with k_m = 1 too (D-17)
        given = {key: bool(src.get(key) and src[key]["value"] != 0) for key in MOMENTS}
        axis = strong_axis(section) if section is not None else "y"
        if axis is None or (axis == "z" and not given["M_z"]):
            if not any(given.values()):
                reason = "no moment -- a lateral torsional buckling reads M_y, M_z or both"
        elif not given["M_" + axis]:
            reason = "no M_%s -- lateral torsional buckling is the bending about the strong axis, %s; without M_%s check a bending" % (axis, axis, axis)
        elif src.get("a") is None and src.get("sigma_m_crit") is None:
            reason = "neither a nor sigma_m_crit -- lateral torsional buckling needs the distance between the lateral supports, or the critical stress of a finer calculation"
    if not reason and kind == "shear" and shears["V_z"] is None and shears["V_y"] is None:
        reason = "no shear force -- a shear check needs V_z, V_y or both"
    moments = {key: (src.get(key) if src.get(key) and src[key]["value"] != 0 else None) for key in MOMENTS}
    if not reason and kind == "bending":
        # a bending's N is signed: any value is one; what it cannot do without is a moment, and at an angle M_z, which (17) to (20) do not read
        if moments["M_y"] is None and moments["M_z"] is None:
            reason = "no moment -- a bending check needs M_y, M_z or both"
        elif alpha > 0 and moments["M_z"] is not None:
            reason = ("M_z is %s %s at an angle of %s° to the grain -- (17) to (20) read M_y alone; check M_z with an angle of 0"
                      % (_fmt(moments["M_z"]["value"]), moments["M_z"]["unit"], _fmt(alpha)))
    contact = _contact(src, grade if not reason else None, section)
    if not reason and contact["reason"]:
        reason = contact["reason"]
    if not reason and kind == "tension" and alpha == 0:
        # Tabelle 8 note 2 (C16): «Für Zugglieder nicht zulässig» -- the very refusal verify-tension makes, said here so that the record is not exported as calculable and then refused by the report
        row = sia265.grade(grade)
        notes = (row.get("notes") or {}).get("f_t_0_d") or []
        table = _table_of(grade)
        for note in notes:
            text = table.get("notes", {}).get(str(note), "")
            if "Zugglieder" in text:
                reason = "%s -- SIA 265 Tabelle %s: %s" % (grade, table.get("number", ""), text)
                break
    fire = None
    if src.get("fire") is not None:
        # the design situation fire (issue #46): the duration, the faces, the residual section -- and what makes it not calculable
        fire, fire_reason = _fire_block(src, grade if not reason else None, section if not reason else None, building)
        if not reason and fire_reason:
            reason = fire_reason
    if reason:
        warnings.append(engine.Note("check_not_calculable", "%s: cannot be checked -- %s" % (where, reason), check=cid, reason=reason))

    out = {
        "id": cid,
        "name": src.get("name", "") or "",
        "label": src.get("label", "") or "",
        "group": src.get("group", "") or "",
        "kind": src["kind"],
        "position": pid,
        "position_found": record is not None,
        "grade": grade or None,
        "grade_from": grade_from if grade else None,
        "section": section,
        "section_from": section_from,
        "moisture_class": moisture,
        "moisture_from": moisture_from,
        "impact": bool(src.get("impact", False)),
        "alpha": alpha,
        "N": {"value": src["N"]["value"], "unit": src["N"]["unit"]} if src.get("N") is not None else None,
        "case": contact["case"],
        "larger": contact["larger"],
        "l": contact["l"],
        "w": contact["w"],
        "w_from": contact["w_from"],
        "case_label": contact["case_label"],
        "f_c_90_table": contact["f_c_90_table"],
        "calculable": not reason,
        "reason": reason,
        "warnings": warnings,
    }
    if kind in ("bending", "lateral-torsional"):
        # the moments of a bending, a moment of 0 being none -- only for its kind, so that a tension's and a compression's record stay as they were, byte for byte
        for key in MOMENTS:
            out[key] = {"value": moments[key]["value"], "unit": moments[key]["unit"]} if moments[key] else None
    if kind == "lateral-torsional":
        out.update(a=src.get("a"), sigma_m_crit=src.get("sigma_m_crit"))
    if kind in ("buckling", "lateral-torsional"):
        out.update({key: lengths[key] for key in LENGTHS}, **betas)
    if kind == "shear":
        for key in SHEAR_FORCES:
            out[key] = {"value": shears[key]["value"], "unit": shears[key]["unit"]} if shears[key] else None
        out["pith"] = bool(src.get("pith", False))
        if out["pith"] and grade and _family(grade) == "Brettschichtholz":
            # Tabelle 8 note 6 halves f_v,d of solid timber cut from the pith; Tabelle 9 has no such note -- the field stays as the source says, and is not applied (D-02 of spec 2026-10-12-audit-issues-47-48-49)
            warnings.append(engine.Note("check_pith_glulam", "%s: pith is true on %s, a glulam -- SIA 265 Tabelle 8 note 6 halves f_v,d of solid timber only, and Tabelle 9 has no such note: f_v,d is not halved" % (where, grade), check=cid, grade=grade))
    if fire is not None:
        out["fire"] = fire
    if provenance:
        out["links"] = provenance
    return out


# --- the Typst it comes to -----------------------------------------------------

def force_text(force):
    """The design force as `#show-check-member` hands it to `#verify-tension`: «25 kN»."""
    return "%s %s" % (_fmt(force["value"]), force["unit"])


def moment_text(moment):
    """A design moment as `#show-check-member` hands it to `#verify-bending`: its magnitude, «12.5 kNm» -- the sign of a moment says nothing a section check reads."""
    return "%s %s" % (_fmt(abs(moment["value"])), moment["unit"])


def fire_typst(fire):
    """A resolved `fire` as #member's `fire:` takes it: `(duration: 60, sides: ("bottom", "left", "right"), wood: "oak")` -- the four booleans of the source become the faces' names here and nowhere else (ARCH-RISK-009); a softwood's wood is none, which #member reads off the grade again."""
    sides = ", ".join(_typst_str(s) for s in fire["sides"]) + ("," if len(fire["sides"]) == 1 else "")
    wood = "none" if fire.get("wood") in (None, "softwood") else _typst_str(fire["wood"])
    return "(duration: %d, sides: (%s), wood: %s)" % (fire["duration"], sides, wood)


def draft_typst(record, level=None, member_level=1, description=False, title=None, unit=None, shown=None):
    """The Typst `#show-check-member` prints for `record` -- `#member(...)` then the check of its kind, `#verify-tension(...)`, `#verify-compression(..., stability: false)` along the grain or `#verify-compression-perp(...)` at an angle, every value written out -- for Woodcore to compile as the preview of a draft not exported yet. It compiles after `#import "/commands.typ": *` in a project. `level`, `title`, `unit` are verify-tension's: None leaves them to their default (auto), `title=False` is `none`; `member_level` is the member line's level, None for no line (level 0). At `level=-1` (issue #20) `shown` -- {key: level} -- is split as `#show-check-member` splits it, the check's keys to the check and the rest to the member, whose own level gives way (spec D-11). A record that cannot be calculated comes to the panic `#show-check-member` gives it."""
    cid = record["id"]
    if not record.get("calculable"):
        return "#panic(%s)\n" % _typst_str("show-check-member: %s cannot be checked -- %s" % (cid, record.get("reason", "")))
    if record.get("kind") not in IMPLEMENTED:
        return "#panic(%s)\n" % _typst_str("show-check-member: the %s check is not implemented yet" % record.get("kind"))
    section = record["section"]
    sides = ["d: %s" % _fmt(section["d"])] if section["type"] == "cir" else ["b: %s" % _fmt(section["b"]), "h: %s" % _fmt(section["h"])]
    position = record.get("position") if record.get("position_found") else None
    member = ["%s" % _typst_str(cid)] + sides + [
        "grade: %s" % _typst_str(record["grade"]),
        "moisture-class: %d" % record["moisture_class"],
        "position: %s" % (_typst_str(position) if position else "none"),
        "impact: %s" % ("true" if record.get("impact") else "false"),
    ] + (["fire: %s" % fire_typst(record["fire"])] if record.get("fire") else []) + [
        "description: %s" % ("true" if description else "false"),
        "level: %s" % (-1 if level == -1 else 0 if member_level is None else member_level),
    ]
    command = shown_variables.check_command(record)
    member_shown, check_shown = shown_variables.split_check_member(shown or {}, command)
    if level == -1:
        member.append("shown: %s" % _typst_dict(member_shown))
    alpha = record.get("alpha", 0)
    lengths = ["l-y: %s" % _fmt(record["l_y"]), "l-z: %s" % _fmt(record["l_z"]),
               "beta-y: %s" % _fmt(record["beta_y"]), "beta-z: %s" % _fmt(record["beta_z"])] if record.get("l_y") is not None else []
    if record["kind"] == "tension":
        check = [_typst_str(cid), "N: %s" % _typst_str(force_text(record["N"])), "alpha: %s" % _fmt(alpha)]
    elif record["kind"] == "shear":
        # 4.2.5: the shear forces, each in its plane, and a member cut from the pith
        check = [_typst_str(cid)] + ["%s: %s" % ("V" if key == "V_z" else "V-y", _typst_str(force_text(record[key]))) for key in SHEAR_FORCES if record.get(key)]
        check.append("pith: %s" % ("true" if record.get("pith") else "false"))
    elif record["kind"] == "buckling":
        # 4.2.8: a compression along the grain with its stability, the buckling lengths beta · l about each axis
        check = [_typst_str(cid), "N: %s" % _typst_str("-" + force_text(record["N"]))] + lengths
    elif record["kind"] == "lateral-torsional":
        # 4.2.9: a bending with its stability -- without a normal force (14) and (38), with a tension (21) and (38), with a compression (22) and (37), which reads the buckling lengths
        check = [_typst_str(cid)]
        if command == "verify-bending-normal":
            check.append("N: %s" % _typst_str(force_text(record["N"])))
        check += ["%s: %s" % (key.replace("_", "-"), _typst_str(moment_text(record[key]))) for key in MOMENTS if record.get(key)]
        if record.get("a") is not None:
            check.append("a: %s" % _fmt(record["a"]))
        elif record.get("sigma_m_crit") is not None:
            check.append("sigma-m-crit: %s" % _fmt(record["sigma_m_crit"]))
        if command == "verify-bending-normal" and record["N"]["value"] < 0:
            check += lengths
    elif record["kind"] == "bending":
        # the section alone: without a normal force (14) or (17) to (20), with one (21) or (22) -- N signed, tension positive
        check = [_typst_str(cid)]
        if command == "verify-bending-normal":
            check.append("N: %s" % _typst_str(force_text(record["N"])))
        check += ["%s: %s" % (key.replace("_", "-"), _typst_str(moment_text(record[key]))) for key in MOMENTS if record.get(key)]
        check += ["alpha: %s" % _fmt(alpha), "stability: false"]
    elif alpha == 0:
        check = [_typst_str(cid), "N: %s" % _typst_str("-" + force_text(record["N"])), "stability: false"]
    else:
        check = [_typst_str(cid), "F: %s" % _typst_str(force_text(record["N"])), "l: %s" % _fmt(record["l"]), "w: %s" % _fmt(record["w"]),
                 "alpha: %s" % _fmt(alpha), "case: %s" % _typst_str(record["case"]), "larger: %s" % ("true" if record.get("larger") else "false")]
    if level is not None:
        check.append("level: %s" % level)
    if level == -1:
        check.append("shown: %s" % _typst_dict(check_shown))
    if title is False:
        check.append("title: none")
    elif title is not None:
        check.append("title: %s" % _typst_str(title))
    if unit is not None:
        check.append("unit: %s" % _typst_str(unit))
    return "#member(%s)\n#%s(%s)\n" % (", ".join(member), command, ", ".join(check))


# --- the instant calculation -----------------------------------------------------

# A force in kN, from the unit a source writes it in.
_TO_KN = {"N": 1e-3, "kN": 1.0, "MN": 1e3}


def _row(key, symbol, value, unit, formula=None, label=None):
    row = {"key": key, "symbol": symbol, "value": value, "unit": unit}
    if formula:
        row["formula"] = formula
    if label:
        row["label"] = label
    return row


def compute(record):
    """`_compute`, and the ratio its verdict prints: `ratio`, the math source of the action over the resistance that governs -- the utilisation's own formula, or, where η is the larger of two sides (bending at an angle, across the grain), the formula of the side that gives it (issue #12: the window prints `σ/f = 0.41 ⩽ 1`, as the report does, and never η). Additive: every other key as `_compute` gives it."""
    result = _compute(record)
    if result:
        result["ratio"] = governing_ratio(result["rows"])
    return result


# The member's keys a round section does not print: one value about either axis, said once, and no Saint-Venant coefficient (lib/timber.typ, `member`)
_NOT_ROUND = ("W_z", "I_z", "i_z", "k_tor", "f_m_z_d", "k_h_z")


def shown_keys(record):
    """The keys the window offers for `record` at the level of detail -1 (issue #20, spec D-15): the member's that its section prints, then those of the check of its kind that this check computes (`_compute`'s rows, in lib/shown-variables.json's order) -- a subset of what `#show-check-member` accepts (shown_variables.check_member_keys), the engineer never offered a box for a line the page would not print. Empty for a check that cannot be calculated."""
    if not record.get("calculable") or record.get("kind") not in IMPLEMENTED:
        return []
    command = shown_variables.check_command(record)
    rows = {row["key"] for row in (_compute(record) or {}).get("rows", ())}
    own = shown_variables.keys(command)
    round_ = record.get("section", {}).get("type") == "cir"
    fire = bool(record.get("fire"))
    member = [key for key in shown_variables.keys("member") if key not in own and not (round_ and key in _NOT_ROUND)
              and (fire or key not in FIRE_MEMBER_KEYS) and not (fire and key in ("k_h_y", "k_h_z"))]
    return member + [key for key in own if key in rows]


def shown_choices(record):
    """`shown_keys(record)` as the window's switches take them, [(key, words, math)]: a verdict -- the key of its utilisation, `eta`, `eta_s`, `eta_y`… (issue #58) -- by the symbol its row has in the results («η_c,y»), every other key by its own name (shown_variables.key_math)."""
    rows = {row["key"]: row for row in (_compute(record) or {}).get("rows", ())}
    return [(key, None, rows[key]["symbol"] if key.startswith("eta") and key in rows else None) for key in shown_keys(record)]


def governing_ratio(rows):
    """The formula of the ratio a check's verdict prints, from its rows: the `eta` row's, unless that row is the larger of the two sides' utilisations (`max(…)`), then the formula of the side's row that is larger -- the first of the two on a tie, as `_compute` chooses its relation."""
    by_key = {row["key"]: row for row in rows}
    eta = by_key.get("eta") or {}
    formula = eta.get("formula") or ""
    if not formula.startswith("max("):
        return _indices(formula)
    # the parts a max() is taken over: the two sides of a section at an angle, or the section and its stability (issue #38)
    sides = [row for row in rows if row["key"] in ("eta_m_t", "eta_m_c", "eta_s", "eta_y", "eta_z", "eta_m")]
    best = max(sides, key=lambda row: row["value"]) if sides else None
    return _indices(best.get("formula", "") if best else formula)


def _indices(formula):
    """A formula in the registry's keys written with its indices grouped, as the rows' own formulas are: `sigma_t_0_d / f_t_0_d` -> `sigma_(t,0,d) / f_(t,0,d)`, which the window sets as one subscript and not three (richtext.math_html)."""
    return re.sub(r"\b([A-Za-z]+)((?:_[A-Za-z0-9]+){2,})\b", lambda m: "%s_(%s)" % (m.group(1), ",".join(m.group(2).split("_")[1:])), formula)


def _compute(record):
    """The check of `record` computed at once, in Python, for Woodcore to show while a draft is typed -- with no Typst compile in the way (the engineer, 07.10.2026). **The report does not read it**: `#show-check-member` computes the same check in Typst, and `tests/test_member_check.py` holds the two equal. Every value of SIA 265 is read through `norms.sia265` (Tabelle 8 or 9, Tabelle 4's eta_w, 2.2.6's eta_t), never written here, and the arithmetic is lib/timber.typ's: a design value is the table's times eta_w times eta_t, A is b·h or π·d²/4, A_c is l·w, and f_alpha is (9) or (13).

    Gives None where the record cannot be calculated or its kind is not implemented; otherwise
    {"kind", "equation", "clause", "rows": [{"key", "symbol", "value", "unit", "formula"?, "label"?}, …], "eta", "ok", "relation"},
    the rows in the order the report prints them and named by the registry's keys (`symbol` the Typst math source the page sets), `eta` the utilisation, `ok` whether it holds (eta <= 1, a tie absorbed at 1e-9), `relation` the norm's inequality in those keys."""
    if not record or not record.get("calculable") or record.get("kind") not in IMPLEMENTED:
        return None
    fire = record.get("fire")
    if not fire:
        return _compute_section(record)
    # the design situation fire (SIA 265 4.5.2, issue #46): #member(fire:)'s rows, then the check on the ideal residual section with (51)'s factor on the design values along the grain -- f_c,0,k and E_0,05 as they are, no k_h
    clause = sia265.fire()
    k_fi = clause["resistance_factor"]["value"]
    section = record["section"]
    sides = fire["sides"]
    n_b = sum(1 for s in sides if s in sia265.FIRE_WIDTH_SIDES)
    n_h = sum(1 for s in sides if s in sia265.FIRE_HEIGHT_SIDES)

    def reduced(base, n):
        return base if n == 0 else "%s - d_(ef)" % base if n == 1 else "%s - %d dot d_(ef)" % (base, n)

    d_char = fire["beta_n"] * fire["duration"]
    rows = [_row("t_fi", "t", fire["duration"], "min", label="R%d" % fire["duration"]),
            _row("beta_n", "beta_n", fire["beta_n"], "mm/min"),
            _row("d_char_n", "d_(char,n)", d_char, "mm", "beta_n dot t"),
            _row("d_red", "d_(red)", clause["d_red"]["value"], "mm"),
            _row("d_ef", "d_(ef)", fire["d_ef"], "mm", "d_(char,n) + d_(red)"),
            _row("b", "b_(fi)", fire["b"], "mm", reduced("b_0", n_b)),
            _row("h", "h_(fi)", fire["h"], "mm", reduced("h_0", n_h)),
            _row("k_fi", "k_(fi)", k_fi, "")]
    result = _compute_section(dict(record, section={"type": "rec", "b": fire["b"], "h": fire["h"], "text": section.get("text", "")}), k_fi)
    result["rows"] = rows + result["rows"]
    return result


def _compute_section(record, k_fi=1.0):
    """`_compute` of a record at normal temperature -- or, with `k_fi` and the residual section put in `record`, in the fire situation: every design value along the grain times k_fi, its formula saying so."""
    fire = k_fi != 1.0
    kind = record["kind"]
    alpha = record.get("alpha", 0)
    row = sia265.grade(record["grade"])
    eta_w = sia265.eta_w(record["moisture_class"], "resistance")
    eta_t = sia265.eta_t(bool(record.get("impact")))
    section = record["section"]
    if section["type"] == "cir":
        area = math.pi * section["d"] ** 2 / 4
        area_row = _row("A", "A", area, "mm²", "pi dot d^2 / 4")
    else:
        area = section["b"] * section["h"]
        area_row = _row("A", "A", area, "mm²", "b dot h")
    factors = [_row("eta_w", "eta_w", eta_w, "", label="Feuchteklasse %d" % record["moisture_class"]),
               _row("eta_t", "eta_t", eta_t, "")]

    def design(key, symbol, table_value, label=None):
        value = k_fi * eta_w * eta_t * table_value
        return value, _row(key, symbol, value, "N/mm²", "%seta_w dot eta_t dot %s" % ("k_(fi) dot " if fire else "", _fmt(table_value)), label)

    def at_angle(f0, f90):
        a = math.radians(alpha)
        return f90 * f0 / (f0 * math.sin(a) ** 2 + f90 * math.cos(a) ** 2)

    if kind == "bending":
        return _compute_bending(record, row, area, area_row, factors, design, at_angle, k_fi * eta_w * eta_t)
    if kind == "shear":
        return _compute_shear(record, area, area_row, factors, design, row)
    if kind == "buckling":
        return _compute_buckling(record, row, area, area_row, factors, design)
    if kind == "lateral-torsional":
        return _compute_lateral(record, row, area, area_row, factors, design, k_fi * eta_w * eta_t)
    force = record["N"]["value"] * _TO_KN[record["N"]["unit"]]       # kN
    if kind == "tension":
        force_row = _row("N_t_d", "N_(t,d)", force, "kN")
        sigma = force * 1000 / area                                    # N/mm²
        if alpha == 0:
            f, f_row = design("f_t_0_d", "f_(t,0,d)", row["f_t_0_d"])
            rows = [area_row, force_row] + factors + [f_row, _row("sigma_t_0_d", "sigma_(t,0,d)", sigma, "N/mm²", "N_(t,d) / A")]
            out = {"equation": "(6)", "clause": "4.2.1.1", "relation": "sigma_t_0_d <= f_t_0_d"}
        elif alpha == 90:
            f, f_row = design("f_t_90_d", "f_(t,90,d)", row["f_t_90_d"])
            rows = [area_row, force_row] + factors + [f_row, _row("sigma_t_90_d", "sigma_(t,90,d)", sigma, "N/mm²", "N_(t,d) / A")]
            out = {"equation": "(7)", "clause": "4.2.1.2", "relation": "sigma_t_90_d <= f_t_90_d"}
        else:
            f0, f0_row = design("f_t_0_d", "f_(t,0,d)", row["f_t_0_d"])
            f90, f90_row = design("f_t_90_d", "f_(t,90,d)", row["f_t_90_d"])
            f = at_angle(f0, f90)
            rows = [area_row, force_row, _row("alpha", "alpha", alpha, "°")] + factors + [
                f0_row, f90_row,
                _row("f_t_alpha_d", "f_(t,alpha,d)", f, "N/mm²", "f_(t,90,d) dot f_(t,0,d) / (f_(t,0,d) dot sin(alpha)^2 + f_(t,90,d) dot cos(alpha)^2)"),
                _row("sigma_t_alpha_d", "sigma_(t,alpha,d)", sigma, "N/mm²", "N_(t,d) / A")]
            out = {"equation": "(8)/(9)", "clause": "4.2.1.3", "relation": "sigma_t_alpha_d <= f_t_alpha_d"}
    elif alpha == 0:
        # along the grain, the section alone: (10) with k_c = 1, buckling being a check of its own
        sigma = force * 1000 / area
        f, f_row = design("f_c_0_d", "f_(c,0,d)", row["f_c_0_d"])
        rows = [area_row, _row("N_c_d", "N_(c,d)", force, "kN")] + factors + [f_row, _row("sigma_c_0_d", "sigma_(c,0,d)", sigma, "N/mm²", "N_(c,d) / A")]
        out = {"equation": "(10)", "clause": "4.2.2.1", "relation": "sigma_c_0_d <= f_c_0_d"}
    else:
        # a contact: the force on l·w, f_c,90,d read for the record's case
        contact_area = record["l"] * record["w"]
        sigma = force * 1000 / contact_area
        rows = [_row("l_c", "l", record["l"], "mm"), _row("w_c", "w", record["w"], "mm"),
                _row("A_c", "A_c", contact_area, "mm²", "l dot w"), _row("F_c_d", "F_(c,90,d)", force, "kN")]
        if alpha != 90:
            rows.append(_row("alpha", "alpha", alpha, "°"))
        rows += factors
        f90, f90_row = design("f_c_90_d", "f_(c,90,d)", record["f_c_90_table"], record.get("case_label"))
        if alpha == 90:
            f = f90
            rows += [f90_row, _row("sigma_c_90_d", "sigma_(c,90,d)", sigma, "N/mm²", "F_(c,90,d) / A_c")]
            out = {"equation": "(11)", "clause": "4.2.2.2", "relation": "sigma_c_90_d <= f_c_90_d"}
        else:
            f0, f0_row = design("f_c_0_d", "f_(c,0,d)", row["f_c_0_d"])
            f = at_angle(f0, f90)
            rows += [f90_row, f0_row,
                     _row("f_c_alpha_d", "f_(c,alpha,d)", f, "N/mm²", "f_(c,90,d) dot f_(c,0,d) / (f_(c,0,d) dot sin(alpha)^2 + f_(c,90,d) dot cos(alpha)^2)"),
                     _row("sigma_c_alpha_d", "sigma_(c,alpha,d)", sigma, "N/mm²", "F_(c,90,d) / A_c")]
            out = {"equation": "(12)/(13)", "clause": "4.2.2.3", "relation": "sigma_c_alpha_d <= f_c_alpha_d"}
    eta = sigma / f
    stress = rows[-1]["symbol"]
    ratio = "%s / %s" % (stress, ("f" + stress[len("sigma"):]))
    if shown_variables.check_command(record) == "verify-compression":
        # verify-compression prints the section's verdict as eta_s and stores eta = eta_s (lib/timber.typ): the row the window offers at -1 (issue #58)
        rows.append(_row("eta_s", "eta_s", eta, "", ratio))
    rows.append(_row("eta", "eta", eta, "", ratio))
    return {"kind": kind, "equation": out["equation"], "clause": out["clause"], "rows": rows,
            "eta": eta, "ok": eta <= 1 + 1e-9, "relation": out["relation"]}


# A moment in kNm, from the unit a source writes it in.
_TO_KNM = {"Nm": 1e-3, "kNm": 1.0, "MNm": 1e3}


def _bending_values(record, row, factor):
    """What a bending check reads of its member, as `#member` computes it: the moments in kNm (a moment absent or 0 is None), W_y and W_z (π·d³/32 for both about a round section), k_h of glulam under 600 mm (3.4.2.3, `sia265.k_h`) and f_m,y,d, f_m,z,d -- with the rows each prints. `factor` is eta_w·eta_t. Shared by the section's check (`_compute_bending`) and lateral torsional buckling (`_compute_lateral`), so the arithmetic is written once."""
    section = record["section"]
    moments = {key: abs(record[key]["value"]) * _TO_KNM[record[key]["unit"]] if record.get(key) else None for key in MOMENTS}   # kNm
    # the section's moduli and k_h, as #member computes them
    if section["type"] == "cir":
        w_y = w_z = math.pi * section["d"] ** 3 / 32
        modulus_rows = [_row("W_y", "W_y", w_y, "mm³", "pi dot d^3 / 32")]
        sides = (("k_h_y", "k_h", "d", section["d"]),)
    else:
        b, h = section["b"], section["h"]
        w_y, w_z = b * h ** 2 / 6, h * b ** 2 / 6
        modulus_rows = [_row("W_y", "W_y", w_y, "mm³", "b dot h^2 / 6")] + ([_row("W_z", "W_z", w_z, "mm³", "h dot b^2 / 6")] if moments["M_z"] else [])
        sides = (("k_h_y", "k_(h,y)", "h", h), ("k_h_z", "k_(h,z)", "b", b))
    glulam = record["grade"] in {g["id"] for g in sia265.table_9()["grades"]}
    clause = sia265.k_h()
    # in the fire situation k_h is not applied (SIA 265 4.5.2.5) and the factor carries (51)'s k_fi
    fire = bool(record.get("fire"))
    k_h, k_rows = {}, []
    for key, symbol, side, value in sides:
        if glulam and not fire and value < clause["reference_height"]:
            k_h[key] = min((clause["reference_height"] / value) ** clause["exponent"], clause["maximum"])
            # shown where its axis is bent: k_h,z says nothing to a check without M_z -- a round section's one k_h serves both
            if len(sides) == 1 or moments["M_" + key[-1]]:
                k_rows.append(_row(key, symbol, k_h[key], "", "min((%s mm / %s)^%s, %s)" % (_fmt(clause["reference_height"]), side, _fmt(clause["exponent"]), _fmt(clause["maximum"]))))
        else:
            k_h[key] = 1.0
    k_h.setdefault("k_h_z", k_h["k_h_y"])
    f_m = {axis: k_h["k_h_" + axis] * factor * row["f_m_d"] for axis in ("y", "z")}
    f_m_rows = {axis: _row("f_m_%s_d" % axis, "f_(m,%s,d)" % axis, f_m[axis], "N/mm²", "%s%seta_w dot eta_t dot %s" % ("k_(fi) dot " if fire else "", "k_(h,%s) dot " % axis if k_h["k_h_" + axis] != 1 else "", _fmt(row["f_m_d"])))
                for axis in ("y", "z")}
    moment_rows = [_row("%s_d" % key, "M_(%s,d)" % key[-1], moments[key], "kNm") for key in MOMENTS if moments[key]]
    return {"moments": moments, "w_y": w_y, "w_z": w_z, "k_h": k_h, "k_rows": k_rows, "f_m": f_m, "f_m_rows": f_m_rows,
            "modulus_rows": modulus_rows, "moment_rows": moment_rows}


def _compute_bending(record, row, area, area_row, factors, design, at_angle, factor):
    """`compute` for a bending, the section alone -- `#member`'s section values and design values, then verify-bending's or verify-bending-normal's arithmetic (lib/timber.typ): W_y = b·h²/6 and W_z = h·b²/6, or π·d³/32 for both; f_m by k_h for glulam under 600 mm (3.4.2.3, `sia265.k_h`); then (14), (15)/(16), (17) to (20), (21) or (22), and at an angle with a normal force (21) or (22) with (9) or (13), (19), (20) on the side where N adds and (17) or (18) on the other -- the engineer's reading (08.10.2026). `factor` is eta_w·eta_t. The rows are named by the registry's keys; the utilisation of each side is `eta_m_t` and `eta_m_c`, as the report stores it."""
    alpha = record.get("alpha", 0)
    normal = record["N"]["value"] * _TO_KN[record["N"]["unit"]]       # kN, tension positive
    values = _bending_values(record, row, factor)
    moments, w_y, w_z, k_rows, f_m, f_m_rows = values["moments"], values["w_y"], values["w_z"], values["k_rows"], values["f_m"], values["f_m_rows"]
    modulus_rows, moment_rows = values["modulus_rows"], values["moment_rows"]
    f90_c_table = row["f_c_90_d"]["generell"]
    f90_c_table = f90_c_table.get("value") if isinstance(f90_c_table, dict) else f90_c_table   # #member reads «generell», a number in both tables
    tension = normal > 0

    if alpha == 0:
        rows = modulus_rows + moment_rows
        terms, relation_terms, shown_terms = [], [], []
        if normal != 0:
            rows = [area_row] + rows
            if tension:
                rows.append(_row("N_t_d", "N_(t,d)", normal, "kN"))
                f_n, f_n_row = design("f_t_0_d", "f_(t,0,d)", row["f_t_0_d"])
                sigma_n = normal * 1000 / area
                sigma_row = _row("sigma_t_0_d", "sigma_(t,0,d)", sigma_n, "N/mm²", "N_(t,d) / A")
                terms.append(sigma_n / f_n)
                relation_terms.append("sigma_t_0_d / f_t_0_d")
                shown_terms.append("sigma_(t,0,d) / f_(t,0,d)")
            else:
                rows.append(_row("N_c_d", "N_(c,d)", -normal, "kN"))
                f_n, f_n_row = design("f_c_0_d", "f_(c,0,d)", row["f_c_0_d"])
                sigma_n = -normal * 1000 / area
                sigma_row = _row("sigma_c_0_d", "sigma_(c,0,d)", sigma_n, "N/mm²", "N_(c,d) / A")
                terms.append((sigma_n / f_n) ** 2)
                relation_terms.append("(sigma_c_0_d / f_c_0_d)^2")
                shown_terms.append("(sigma_(c,0,d) / f_(c,0,d))^2")
        rows += factors + k_rows
        stress_rows = []
        for axis, key in (("y", "M_y"), ("z", "M_z")):
            if moments[key]:
                rows.append(f_m_rows[axis])
                sigma_m = moments[key] * 1e6 / (w_y if axis == "y" else w_z)
                stress_rows.append(_row("sigma_m_%s_d" % axis, "sigma_(m,%s,d)" % axis, sigma_m, "N/mm²", "M_(%s,d) / W_%s" % (axis, axis)))
                terms.append(sigma_m / f_m[axis])
                relation_terms.append("sigma_m_%s_d / f_m_%s_d" % (axis, axis))
                shown_terms.append("sigma_(m,%s,d) / f_(m,%s,d)" % (axis, axis))
        if normal != 0:
            rows += [f_n_row, sigma_row]
        rows += stress_rows
        eta = sum(terms)
        out = ({"equation": "(14)", "clause": "4.2.3.1"} if normal == 0 else
               {"equation": "(21)", "clause": "4.2.4.1"} if tension else {"equation": "(22)", "clause": "4.2.4.2"})
        relation = " + ".join(relation_terms) + " <= 1"
        # verify-bending and verify-bending-normal print the section's verdict as eta_s and store eta = eta_s (lib/timber.typ): the row the window offers at -1 (issue #58)
        rows.append(_row("eta_s", "eta_s", eta, "", " + ".join(shown_terms)))
        rows.append(_row("eta", "eta", eta, "", " + ".join(shown_terms)))
        return {"kind": "bending", "equation": out["equation"], "clause": out["clause"], "rows": rows, "eta": eta, "ok": eta <= 1 + 1e-9, "relation": relation}

    # at an angle: M_y alone, M_y / W_y on both sides of the section
    m_y = moments["M_y"]
    f_t90, f_t90_row = design("f_t_90_d", "f_(t,90,d)", row["f_t_90_d"])
    f_c90, f_c90_row = design("f_c_90_d", "f_(c,90,d)", f90_c_table, "generell")
    sigma_m = m_y * 1e6 / w_y
    rows = modulus_rows + moment_rows
    if normal == 0 and alpha == 90:
        # (15), (16): the stress against f_t,90,d on the tension side and f_c,90,d on the compression side
        rows += factors + [f_t90_row, f_c90_row, _row("sigma_m_90_d", "sigma_(m,90,d)", sigma_m, "N/mm²", "M_(y,d) / W_y")]
        eta_t, eta_c = sigma_m / f_t90, sigma_m / f_c90
        rows += [_row("eta_m_t", "eta_(m,t)", eta_t, "", "sigma_(m,90,d) / f_(t,90,d)", "Biegezugseite"),
                 _row("eta_m_c", "eta_(m,c)", eta_c, "", "sigma_(m,90,d) / f_(c,90,d)", "Biegedruckseite")]
        eta = max(eta_t, eta_c)
        relation = "sigma_m_90_d <= f_t_90_d" if eta_t >= eta_c else "sigma_m_90_d <= f_c_90_d"
        rows.append(_row("eta", "eta", eta, "", "max(eta_(m,t), eta_(m,c))"))
        return {"kind": "bending", "equation": "(15)/(16)", "clause": "4.2.3.2", "rows": rows, "eta": eta, "ok": eta <= 1 + 1e-9, "relation": relation}

    a = math.radians(alpha)
    k_mc = f_c90 / (f_m["y"] * math.sin(a) ** 2 + f_c90 * math.cos(a) ** 2)
    k_mt = f_t90 / (f_m["y"] * math.sin(a) ** 2 + f_t90 * math.cos(a) ** 2)
    k_rows_alpha = [_row("k_mc_alpha", "k_(mc,alpha)", k_mc, "", "f_(c,90,d) / (f_(m,y,d) dot sin(alpha)^2 + f_(c,90,d) dot cos(alpha)^2)"),
                    _row("k_mt_alpha", "k_(mt,alpha)", k_mt, "", "f_(t,90,d) / (f_(m,y,d) dot sin(alpha)^2 + f_(t,90,d) dot cos(alpha)^2)")]
    sigma_m_row = _row("sigma_m_alpha_d", "sigma_(m,alpha,d)", sigma_m, "N/mm²", "M_(y,d) / W_y")
    bend_t, bend_c = sigma_m / (k_mt * f_m["y"]), sigma_m / (k_mc * f_m["y"])
    rows.append(_row("alpha", "alpha", alpha, "°"))
    if normal == 0:
        # (17) to (20)
        rows += factors + k_rows + [f_m_rows["y"], f_t90_row, f_c90_row] + k_rows_alpha + [sigma_m_row]
        eta_t, eta_c = bend_t, bend_c
        rows += [_row("eta_m_t", "eta_(m,t)", eta_t, "", "sigma_(m,alpha,d) / (k_(mt,alpha) dot f_(m,y,d))", "Biegezugseite"),
                 _row("eta_m_c", "eta_(m,c)", eta_c, "", "sigma_(m,alpha,d) / (k_(mc,alpha) dot f_(m,y,d))", "Biegedruckseite")]
        out = {"equation": "(17)–(20)", "clause": "4.2.3.3",
               "relation": "sigma_m_alpha_d <= k_mt_alpha dot f_m_y_d" if eta_t >= eta_c else "sigma_m_alpha_d <= k_mc_alpha dot f_m_y_d"}
    else:
        # (21) or (22) at the angle, the side where N adds; the other side by (17) or (18) alone
        rows = [area_row] + rows
        if tension:
            f0, f0_row = design("f_t_0_d", "f_(t,0,d)", row["f_t_0_d"])
            f_n = at_angle(f0, f_t90)
            sigma_n = normal * 1000 / area
            rows += [_row("N_t_d", "N_(t,d)", normal, "kN")] + factors + k_rows + [f_m_rows["y"], f0_row, f_t90_row, f_c90_row,
                     _row("f_t_alpha_d", "f_(t,alpha,d)", f_n, "N/mm²", "f_(t,90,d) dot f_(t,0,d) / (f_(t,0,d) dot sin(alpha)^2 + f_(t,90,d) dot cos(alpha)^2)"),
                     _row("sigma_t_alpha_d", "sigma_(t,alpha,d)", sigma_n, "N/mm²", "N_(t,d) / A")] + k_rows_alpha + [sigma_m_row]
            eta_t, eta_c = sigma_n / f_n + bend_t, bend_c
            rows += [_row("eta_m_t", "eta_(m,t)", eta_t, "", "sigma_(t,alpha,d) / f_(t,alpha,d) + sigma_(m,alpha,d) / (k_(mt,alpha) dot f_(m,y,d))", "Biegezugseite"),
                     _row("eta_m_c", "eta_(m,c)", eta_c, "", "sigma_(m,alpha,d) / (k_(mc,alpha) dot f_(m,y,d))", "Biegedruckseite")]
            out = {"equation": "(21), (9), (19), (20)", "clause": "4.2.4.1",
                   "relation": "sigma_t_alpha_d / f_t_alpha_d + sigma_m_alpha_d / (k_mt_alpha dot f_m_y_d) <= 1" if eta_t >= eta_c else "sigma_m_alpha_d <= k_mc_alpha dot f_m_y_d"}
        else:
            f0, f0_row = design("f_c_0_d", "f_(c,0,d)", row["f_c_0_d"])
            f_n = at_angle(f0, f_c90)
            sigma_n = -normal * 1000 / area
            rows += [_row("N_c_d", "N_(c,d)", -normal, "kN")] + factors + k_rows + [f_m_rows["y"], f0_row, f_t90_row, f_c90_row,
                     _row("f_c_alpha_d", "f_(c,alpha,d)", f_n, "N/mm²", "f_(c,90,d) dot f_(c,0,d) / (f_(c,0,d) dot sin(alpha)^2 + f_(c,90,d) dot cos(alpha)^2)"),
                     _row("sigma_c_alpha_d", "sigma_(c,alpha,d)", sigma_n, "N/mm²", "N_(c,d) / A")] + k_rows_alpha + [sigma_m_row]
            eta_t, eta_c = bend_t, (sigma_n / f_n) ** 2 + bend_c
            rows += [_row("eta_m_c", "eta_(m,c)", eta_c, "", "(sigma_(c,alpha,d) / f_(c,alpha,d))^2 + sigma_(m,alpha,d) / (k_(mc,alpha) dot f_(m,y,d))", "Biegedruckseite"),
                     _row("eta_m_t", "eta_(m,t)", eta_t, "", "sigma_(m,alpha,d) / (k_(mt,alpha) dot f_(m,y,d))", "Biegezugseite")]
            out = {"equation": "(22), (13), (19), (20)", "clause": "4.2.4.2",
                   "relation": "(sigma_c_alpha_d / f_c_alpha_d)^2 + sigma_m_alpha_d / (k_mc_alpha dot f_m_y_d) <= 1" if eta_c >= eta_t else "sigma_m_alpha_d <= k_mt_alpha dot f_m_y_d"}
    eta = max(eta_t, eta_c)
    rows.append(_row("eta", "eta", eta, "", "max(eta_(m,t), eta_(m,c))"))
    return {"kind": "bending", "equation": out["equation"], "clause": out["clause"], "rows": rows, "eta": eta, "ok": eta <= 1 + 1e-9, "relation": out["relation"]}


def _result(kind, equation, clause, rows, eta, relation):
    return {"kind": kind, "equation": equation, "clause": clause, "rows": rows, "eta": eta, "ok": eta <= 1 + 1e-9, "relation": relation}


def _compute_shear(record, area, area_row, factors, design, row):
    """`compute` for a shear, SIA 265 4.2.5.1 -- verify-shear's arithmetic: tau = factor · V / A at the centroid (1.5 for a rectangle, 4/3 for a circle: SHEAR_FACTORS, mechanics), the two planes added as vectors, against f_v,d -- halved for a member cut from the pith (Tabelle 8 note 6). Equation (23)."""
    factor = SHEAR_FACTORS[record["section"]["type"]]
    rows, taus = [area_row], []
    for key, plane in (("V_z", "z"), ("V_y", "y")):
        if record.get(key):
            force = abs(record[key]["value"]) * _TO_KN[record[key]["unit"]]
            tau = factor * force * 1000 / area
            rows += [_row("%s_d" % key, "V_(%s,d)" % plane, force, "kN"),
                     _row("tau_%s_d" % plane, "tau_(%s,d)" % plane, tau, "N/mm²", "%s dot V_(%s,d) / A" % ("4/3" if factor != 1.5 else "1.5", plane))]
            taus.append(("tau_(%s,d)" % plane, tau))
    tau_d = math.hypot(*(t for _s, t in taus)) if len(taus) == 2 else taus[0][1]
    if len(taus) == 2:
        rows.append(_row("tau_d", "tau_d", tau_d, "N/mm²", "sqrt(tau_(z,d)^2 + tau_(y,d)^2)"))
    rows += factors
    f_v, f_v_row = design("f_v_d", "f_(v,d)", row["f_v_d"])
    rows.append(f_v_row)
    shown_tau = "tau_d" if len(taus) == 2 else taus[0][0]
    pith = bool(record.get("pith")) and _family(record["grade"]) != "Brettschichtholz"   # Tabelle 8 note 6, solid timber only (D-02)
    if pith:
        f_v = f_v / 2
        rows.append(_row("f_v_d_p", "f_(v,d)", f_v, "N/mm²", "f_(v,d) / 2", "Markstück"))
        relation = "tau_d <= f_v_d_p"
    else:
        relation = "tau_d <= f_v_d"
    eta = tau_d / f_v
    rows.append(_row("eta", "eta", eta, "", "%s / %s" % (shown_tau, "(f_(v,d) / 2)" if pith else "f_(v,d)")))
    return _result("shear", "(23)", "4.2.5.1", rows, eta, relation)


def _slenderness_rows(record, axis, lever, sigma_c, f_c, beta_c, f_c_0_k, e_0_05, bend=None):
    """Buckling about one axis, 4.2.8 -- timber-kc's arithmetic: l_k = beta · l, lambda = l_k / i, lambda_rel = lambda/pi · sqrt(f_c,0,k / E_0,05) (34), and k_c = 1 up to lambda_rel,limit (Figur 10), else (30) with k of (31). `lever` is i about the axis; `bend` the bending term (37) adds, (formula, value) or None. Gives (rows, eta about the axis)."""
    clause = sia265.buckling()
    l_k = record["beta_" + axis] * record["l_" + axis]
    lam = l_k / lever
    lam_rel = lam / math.pi * math.sqrt(f_c_0_k / e_0_05)
    rows = [_row("l_k_" + axis, "l_(k,%s)" % axis, l_k, "mm", "beta_%s dot l_%s" % (axis, axis)),
            _row("lambda_" + axis, "lambda_" + axis, lam, "", "l_(k,%s) / i_%s" % (axis, axis)),
            _row("lambda_rel_" + axis, "lambda_(rel,%s)" % axis, lam_rel, "", "lambda_%s / pi dot sqrt(f_(c,0,k) / E_(0,05))" % axis)]
    if lam_rel <= clause["lambda_rel_limit"]:
        k_c = 1.0
        rows.append(_row("k_c_" + axis, "k_(c,%s)" % axis, k_c, "", label="λ_rel ⩽ %s" % _fmt(clause["lambda_rel_limit"])))
    else:
        k = clause["k_factor"] * (1 + beta_c * (lam_rel - clause["lambda_rel_offset"]) + lam_rel ** 2)
        k_c = 1 / (k + math.sqrt(k ** 2 - lam_rel ** 2))
        rows += [_row("k_" + axis, "k_" + axis, k, "", "%s dot (1 + beta_c dot (lambda_(rel,%s) - %s) + lambda_(rel,%s)^2)" % (_fmt(clause["k_factor"]), axis, _fmt(clause["lambda_rel_offset"]), axis)),
                 _row("k_c_" + axis, "k_(c,%s)" % axis, k_c, "", "1 / (k_%s + sqrt(k_%s^2 - lambda_(rel,%s)^2))" % (axis, axis, axis))]
    eta = sigma_c / (k_c * f_c) + (bend[1] if bend else 0)
    formula = "sigma_(c,0,d) / (k_(c,%s) dot f_(c,0,d))" % axis + (" + " + bend[0] if bend else "")
    rows.append(_row("eta_" + axis, "eta_(c,%s)" % axis, eta, "", formula))
    return rows, eta


def _stiffness(record):
    """What the relative slendernesses read of the member, as `#member` stores it: f_c,0,k and E_0,05 of Anhang B (Tabellen 47, 48), E_0,05 times eta_w for the stiffness (Tabelle 4) -- the factor the Stützen workbook computes and leaves out (issue #38) -- and the radii of gyration i_y, i_z (d/4 both for a round section). Gives (rows, f_c_0_k, E_0_05, i_y, i_z)."""
    characteristic = sia265.characteristic(record["grade"])
    eta_w_e = sia265.eta_w(record["moisture_class"], "stiffness")
    e_0_05 = eta_w_e * characteristic["E_0_05"]
    section = record["section"]
    if section["type"] == "cir":
        i_y = i_z = section["d"] / 4
        radius_rows = [_row("i_y", "i_y", i_y, "mm", "d / 4")]
    else:
        i_y, i_z = section["h"] / math.sqrt(12), section["b"] / math.sqrt(12)
        radius_rows = [_row("i_y", "i_y", i_y, "mm", "sqrt(I_y / A)"), _row("i_z", "i_z", i_z, "mm", "sqrt(I_z / A)")]
    rows = radius_rows + [_row("eta_w_E", "eta_(w,E)", eta_w_e, "", label="Feuchteklasse %d" % record["moisture_class"]),
                          _row("f_c_0_k", "f_(c,0,k)", characteristic["f_c_0_k"], "N/mm²"),
                          _row("E_0_05", "E_(0,05)", e_0_05, "N/mm²", "eta_(w,E) dot %s" % _fmt(characteristic["E_0_05"]))]
    return rows, characteristic["f_c_0_k"], e_0_05, i_y, i_z


def strong_axis(section):
    """The axis lateral torsional buckling tips about, as `timber-tips` in lib/timber.typ reads it (D-09): "y" for a rectangle as high as wide or higher -- the norm's own case --, "z" for one wider than high, None for a round section, which does not tip (D-10)."""
    if section is None or section.get("type") == "cir":
        return None
    return "z" if section["b"] > section["h"] else "y"


def _family(grade):
    return "Brettschichtholz" if grade in {g["id"] for g in sia265.table_9()["grades"]} else "Vollholz"


def _compute_buckling(record, row, area, area_row, factors, design):
    """`compute` for a buckling, SIA 265 4.2.8 -- verify-compression's with `stability: true`: the section, sigma_c,0,d <= f_c,0,d (10), then about each axis (29) with k_c of (30), (31) and lambda_rel of (34); eta the largest of the three."""
    force = record["N"]["value"] * _TO_KN[record["N"]["unit"]]
    sigma = force * 1000 / area
    f_c, f_row = design("f_c_0_d", "f_(c,0,d)", row["f_c_0_d"])
    stiffness_rows, f_c_0_k, e_0_05, i_y, i_z = _stiffness(record)
    beta_c = sia265.buckling()["beta_c"][_family(record["grade"])]
    eta_s = sigma / f_c
    rows = [area_row] + stiffness_rows + [_row("N_c_d", "N_(c,d)", force, "kN")] + factors + [
        f_row, _row("sigma_c_0_d", "sigma_(c,0,d)", sigma, "N/mm²", "N_(c,d) / A"),
        _row("eta_s", "eta_s", eta_s, "", "sigma_(c,0,d) / f_(c,0,d)"), _row("beta_c", "beta_c", beta_c, "")]
    etas = [eta_s]
    for axis, lever in (("y", i_y), ("z", i_z)):
        axis_rows, eta_axis = _slenderness_rows(record, axis, lever, sigma, f_c, beta_c, f_c_0_k, e_0_05)
        rows += axis_rows
        etas.append(eta_axis)
    eta = max(etas)
    governing = ("sigma_c_0_d <= f_c_0_d", "sigma_c_0_d <= k_c_y dot f_c_0_d", "sigma_c_0_d <= k_c_z dot f_c_0_d")[etas.index(eta)]
    rows.append(_row("eta", "eta", eta, "", "max(eta_s, eta_(c,y), eta_(c,z))"))
    return _result("buckling", "(10), (29)", "4.2.8", rows, eta, governing)


def _compute_lateral(record, row, area, area_row, factors, design, factor):
    """`compute` for a lateral torsional buckling, SIA 265 4.2.9 -- verify-bending's or verify-bending-normal's with `stability: true`, along the grain: the section by (14), (21) or (22); sigma_m,crit of (41) from a, or as given, lambda_rel,m (40) and k_m (39); then without a normal force or with a tension (38), sigma_m,y,d <= k_m · f_m,y,d, and with a compression (37) about each axis, k_c of 4.2.8 beside k_m. eta the largest."""
    values = _bending_values(record, row, factor)
    moments, f_m = values["moments"], values["f_m"]
    normal = record["N"]["value"] * _TO_KN[record["N"]["unit"]]       # kN, tension positive
    section = record["section"]
    rows = ([area_row] if normal else []) + values["modulus_rows"] + values["moment_rows"]
    terms, shown_terms = [], []
    if normal > 0:
        f_n, f_n_row = design("f_t_0_d", "f_(t,0,d)", row["f_t_0_d"])
        sigma_n = normal * 1000 / area
        rows.append(_row("N_t_d", "N_(t,d)", normal, "kN"))
        n_rows = [f_n_row, _row("sigma_t_0_d", "sigma_(t,0,d)", sigma_n, "N/mm²", "N_(t,d) / A")]
        terms.append(sigma_n / f_n)
        shown_terms.append("sigma_(t,0,d) / f_(t,0,d)")
    elif normal < 0:
        f_n, f_n_row = design("f_c_0_d", "f_(c,0,d)", row["f_c_0_d"])
        sigma_n = -normal * 1000 / area
        rows.append(_row("N_c_d", "N_(c,d)", -normal, "kN"))
        n_rows = [f_n_row, _row("sigma_c_0_d", "sigma_(c,0,d)", sigma_n, "N/mm²", "N_(c,d) / A")]
        terms.append((sigma_n / f_n) ** 2)
        shown_terms.append("(sigma_(c,0,d) / f_(c,0,d))^2")
    else:
        n_rows = []
    rows += factors + values["k_rows"]
    sigma_m = {}
    stress_rows = []
    for axis, key in (("y", "M_y"), ("z", "M_z")):
        if moments[key]:
            rows.append(values["f_m_rows"][axis])
            sigma_m[axis] = moments[key] * 1e6 / (values["w_y"] if axis == "y" else values["w_z"])
            stress_rows.append(_row("sigma_m_%s_d" % axis, "sigma_(m,%s,d)" % axis, sigma_m[axis], "N/mm²", "M_(%s,d) / W_%s" % (axis, axis)))
            terms.append(sigma_m[axis] / f_m[axis])
            shown_terms.append("sigma_(m,%s,d) / f_(m,%s,d)" % (axis, axis))
    rows += n_rows + stress_rows
    eta_s = sum(terms)
    rows.append(_row("eta_s", "eta_s", eta_s, "", " + ".join(shown_terms)))
    # 4.2.9: sigma_m,crit, lambda_rel,m, k_m -- E_0,05 times eta_w for the stiffness, as #member stores it
    stiffness_rows, f_c_0_k, e_0_05, i_y, i_z = _stiffness(record)
    lateral = sia265.lateral_buckling()
    rows += stiffness_rows
    # the axis that tips (timber-tips' twin, D-09): y, z where the section is wider than high, none for a round section or where only the weak axis is bent (D-10, D-17) -- k_m = 1 then, and (38) has nothing to add
    axis = strong_axis(section)
    tips = axis is not None and axis in sigma_m
    if not tips:
        k_m = 1.0
        if normal < 0:
            # (37) reads it, as verify-bending-normal stores it; (38) has nothing to divide and prints none
            rows.append(_row("k_m", "k_m", k_m, "", label="Kreisquerschnitt" if axis is None else "Biegung nur um die schwache Achse"))
    else:
        if record.get("sigma_m_crit") is not None:
            crit = record["sigma_m_crit"]
            rows.append(_row("sigma_m_crit", "sigma_(m,crit)", crit, "N/mm²", label="vorgegeben"))
        else:
            # (41) for a b × h rectangle bent about its strong axis: the side along the moment's axis squared over the other -- b²/h about y, h²/b about z
            narrow, deep, shown = (section["b"], section["h"], "b^2 / (a dot h)") if axis == "y" else (section["h"], section["b"], "h^2 / (a dot b)")
            crit = lateral["sigma_m_crit_factor"] * e_0_05 * narrow ** 2 / (record["a"] * deep)
            rows += [_row("a", "a", record["a"], "mm"),
                     _row("sigma_m_crit", "sigma_(m,crit)", crit, "N/mm²", "%s dot E_(0,05) dot %s" % (_fmt(lateral["sigma_m_crit_factor"]), shown))]
        f_m_k = row["f_m_k"]
        lam_m = math.sqrt(f_m_k / crit)
        km = lateral["k_m"]
        if lam_m <= km["lower_bound"]:
            k_m, k_m_formula = 1.0, None
        elif lam_m <= km["upper_bound"]:
            k_m, k_m_formula = km["intercept"] - km["slope"] * lam_m, "%s - %s dot lambda_(rel,m)" % (_fmt(km["intercept"]), _fmt(km["slope"]))
        else:
            k_m, k_m_formula = 1 / lam_m ** 2, "1 / lambda_(rel,m)^2"
        rows += [_row("f_m_k", "f_(m,k)", f_m_k, "N/mm²"), _row("lambda_rel_m", "lambda_(rel,m)", lam_m, "", "sqrt(f_(m,k) / sigma_(m,crit))"),
                 _row("k_m", "k_m", k_m, "", k_m_formula)]
    if normal >= 0:
        if not tips:
            rows.append(_row("eta", "eta", eta_s, "", "eta_s"))
            return _result("lateral-torsional", "(38)", "4.2.9", rows, eta_s, "eta_s <= 1")
        # (38): the bending about the strong axis against k_m · f_m,d about it
        eta_m = sigma_m[axis] / (k_m * f_m[axis])
        rows.append(_row("eta_m", "eta_m", eta_m, "", "sigma_(m,%s,d) / (k_m dot f_(m,%s,d))" % (axis, axis)))
        eta = max(eta_s, eta_m)
        relation = "sigma_m_%s_d <= k_m dot f_m_%s_d" % (axis, axis) if eta_m >= eta_s else "eta_s <= 1"
        rows.append(_row("eta", "eta", eta, "", "max(eta_s, eta_m)"))
        return _result("lateral-torsional", "(38)", "4.2.9", rows, eta, relation)
    # (37) about each axis, with a compression: k_c beside k_m on y, the bending about z on z
    f_c = f_n
    beta_c = sia265.buckling()["beta_c"][_family(record["grade"])]
    rows.append(_row("beta_c", "beta_c", beta_c, ""))
    etas = [eta_s]
    strong = axis
    for axis, lever in (("y", i_y), ("z", i_z)):
        bend = None
        if axis in sigma_m:
            # k_m on the strong axis's bending (D-09), whose own k_m is 1 where nothing tips
            bend = ("sigma_(m,%s,d) / (k_m dot f_(m,%s,d))" % (axis, axis), sigma_m[axis] / (k_m * f_m[axis])) if axis == (strong or "y") else ("sigma_(m,%s,d) / f_(m,%s,d)" % (axis, axis), sigma_m[axis] / f_m[axis])
        axis_rows, eta_axis = _slenderness_rows(record, axis, lever, sigma_n, f_c, beta_c, f_c_0_k, e_0_05, bend)
        rows += axis_rows
        etas.append(eta_axis)
    eta = max(etas)
    rows.append(_row("eta", "eta", eta, "", "max(eta_s, eta_(c,y), eta_(c,z))"))
    return _result("lateral-torsional", "(22), (37)", "4.2.8.5", rows, eta, ("eta_s <= 1", "eta_y <= 1", "eta_z <= 1")[etas.index(eta)])


# --- the export ----------------------------------------------------------------

def empty():
    """The export of a project with no member check -- what export_all.seed writes so that a report compiles from the start."""
    return {"schema_version": EXPORT_SCHEMA_VERSION, "checks": {}}


def prepare(here, positions, values=None):
    """Every member check of `here`, read, checked and resolved against `positions` -- and its linked fields against `values` (`links.index`), a check in the fire situation against the project's building (`read_building`) --, as data/checks.json holds it. Nothing is written. A malformed source stops; anything the project lacks is in the record, `calculable: false` and its reason (the warnings are on each record: `warnings_of`)."""
    checks, seen = {}, {}
    building = read_building(here)
    for path in source_paths(here):
        src = read_source(path)
        lower = src["id"].lower()
        if lower in seen:
            _fail("checks/%s" % path.name, "id %r is also %s's -- ids differ by more than their case" % (src["id"], seen[lower]))
        seen[lower] = path.name
        record = resolve(src, positions, values, building)
        record["warnings"] = [str(note) for note in record["warnings"]]
        checks[src["id"]] = record
    linked = any("links" in record for record in checks.values())
    burning = any("fire" in record for record in checks.values())
    version = FIRE_EXPORT_VERSION if burning else LINKED_EXPORT_VERSION if linked else EXPORT_SCHEMA_VERSION
    data = {"schema_version": version, "checks": checks}
    validation.validate_structure(data, EXPORT_SCHEMA)
    validation.validate_checks_business(data)
    return data


def warnings_of(data):
    """Every warning the records of `data` carry, in the order of the checks -- what export_all prints."""
    return [w for record in data["checks"].values() for w in record.get("warnings", [])]


def write(data, data_dir):
    """data/checks.json."""
    engine.write_json(Path(data_dir) / EXPORT_FILE, data)


def export(here=None):
    """prepare() then write(), against the positions the last export wrote -- what Woodcore runs when a check is saved, so that one check is exported without the workbooks being read again (connector.export's arrangement)."""
    from domains import connector   # known_positions: the one reader of the exported positions Woodcore's tabs share
    here = here or project.current()
    import variable_sources   # the reader of data/'s variables, which imports the domains: imported here, as connector is
    data = prepare(here, connector.known_positions(here.data_dir), variable_sources.known_values(here.data_dir))
    write(data, here.data_dir)
    return data
