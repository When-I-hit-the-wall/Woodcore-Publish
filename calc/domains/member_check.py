"""Member checks (vérifications d'élément): one source file each, written by Woodcore, resolved here, calculated in Typst (docs/domain/connectors.md §3.3nonies, docs/domain/member-checks.md §3.3undecies).

A member check is the saved form of what `#member` and a `#verify-*` command write in the report by hand: which member, with which section, strength class and moisture class, under which action. It is a file of its own, `Woodcore-Datei/checks/<id>.json`, written by Woodcore and read by this module alone -- the arrangement of `connectors/`, for the same reasons (docs/decisions.md §13). **The check is computed twice, on purpose** (the engineer, 19.10.2026: «c'est tout à fait normal de calculer en python, puis en typst»): here by `compute()`, quickly, for the window -- the rows and the verdict shown as the engineer types -- and in the report by `#show-check-member` (lib/timber.typ), the one the report prints. tests/test_member_check.py holds the two equal, every kind of IMPLEMENTED, every row within 1e-6 and the clause it cites (`_held_equal`). The report's is computed by `#show-check-member`, which reads the record this module exports and calls `#member` and the `#verify-*` of its kind with the values written out -- `#verify-tension`; for a compression `#verify-compression(stability: false)` along the grain and `#verify-compression-perp` at an angle; for a bending `#verify-bending(stability: false)` without a normal force and `#verify-bending-normal(stability: false)` with one. What this module does is store, check and resolve -- the connector's reference pattern applied to a member -- and compute the window's copy.

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
import validation
from domains._common import fail as _fail, is_number as _number  # one copy of the domains' helpers (spec 2026-10-19-base-saine-nettoyage, G4)
from domains._common import RESULT_KEY  # noqa: F401  -- η, the key of the check's result, which the «Variables» tab reads here (spec 2026-10-24-onglet-variables-groupes, ARCH-012)
from domains import line_keys, links      # line_keys: what tells a row's formula computes its value (_with_keys)
from domains import member_check_material as material_  # what a check reads of its material: the library's, a panel's, the factors (issue #112, ARCH-001)
from domains.member_check_stability import _compute_buckling, _compute_lateral  # 4.2.8 and 4.2.9, moved out with no change (tests/test_module_size.py)
from norms import sia265, vkf
from number_text import exact as _fmt  # a number as a section's text and a Typst call write it: six decimals, trailing zeros dropped (calc/number_text.py, UI-003)
# the lines of `compute`, built by the engine (spec 2026-10-21-restes-issue-69, REQ-003): `_row` is timber_calc.line, NORM the norm a line cites where it states none of its own
from domains.timber_calc import NORM, SOURCE, TimberCalculation, line as _row

DOMAIN = "member-check"
SOURCE_SCHEMA = "member-check-source"
EXPORT_SCHEMA = "checks"
SOURCE_SCHEMA_VERSION = "1.0"
# 1.1 is 1.0 with `links` (spec 2026-10-11-variables-liees-champs-et-textes, D-17): written only by a source that carries one, so a check that follows no variable is saved and exported byte for byte as before
LINKED_SCHEMA_VERSION = "1.1"
# 1.2 is 1.1 with `fire`, the design situation fire of SIA 265 4.5.2 (issue #46, spec 2026-10-12-resistance-au-feu ARCH-RISK-005): written only by a check in the fire situation, `links` or not -- every other check is saved and exported byte for byte as before
FIRE_SCHEMA_VERSION = "1.2"
# 1.3 is 1.2 with the material of the library (issue #112, spec 2026-10-24-verifications-elements-v3, REQ-001): `material`, a panel's `loading`, `kled` and `accidental`, and `display`, the options of «Affichage» -- written only by a source that carries one of them (member_check_material.FIELDS), `links` and `fire` or not; every other check is saved and exported byte for byte as before
LIBRARY_SCHEMA_VERSION = "1.3"
SOURCE_SCHEMA_VERSIONS = (SOURCE_SCHEMA_VERSION, LINKED_SCHEMA_VERSION, FIRE_SCHEMA_VERSION, LIBRARY_SCHEMA_VERSION)
EXPORT_SCHEMA_VERSION = "1.0"
LINKED_EXPORT_VERSION = "1.1"
FIRE_EXPORT_VERSION = "1.2"
# 1.3 is 1.2 with `vars` and `gen` on a check printed unfolded (spec 2026-10-15, ARCH-007): what `#var(key, value, domain: ("check", id))` checks a literal against, and the form `#var-domain(id, gen:)` is compared with
UNFOLDED_EXPORT_VERSION = "1.3"
# 1.4 is 1.3 with `file` on a check printed unfolded (issue #64, D-16): the file of its domain from the Typst root, `/Timber-checks/Tension/<id>.typ`, or none where the file is still a stub -- what #show-check-member includes, where 1.3's engine included `/Formules/<id>.typ` of its own accord. Written once the checks are unfolded (`mark_unfolded_files`).
UNFOLDED_FILE_EXPORT_VERSION = "1.4"
# 1.5 is 1.4 with `fire.required` on a check whose duration VKF 15-15 requires (spec 2026-10-20-indices-et-niveaux, REQ-001, Q-004): the norm and the table the duration is cited by, `{"norm": "VKF 15-15", "norm_ref": "Tabelle 2"}` -- composed here once, copied by #show-check-member into #member's `fire: (required:)`
REQUIRED_EXPORT_VERSION = "1.5"
# 1.6 is 1.5 without `gen` (spec 2026-10-21-commandes-typst-refonte, ARCH-011): the form a check is written out from is the regeneration base's alone (calc/domains/unfold.py), the export no longer carries it -- every check printed unfolded is written at 1.6, with its `vars` and its `file`
UNFOLDED_BASE_EXPORT_VERSION = "1.6"
# 1.7 is 1.6 with the material of the library on a record whose source names one (issue #112, REQ-015): `material` {id, names, type, origin, short, from}, a panel's `loading`, `kled`, `accidental`, the `resistance` resolve froze (ARCH-008), the `reason_code` of a refusal of the material, and `display` -- what the «Synthèse» tab will read (OSB/3 en plaque ∥). `grade` and `grade_from` stay written for the readers of before
LIBRARY_EXPORT_VERSION = "1.7"
# The keys a record of 1.7 may carry beyond 1.6's
LIBRARY_RECORD_KEYS = ("material", "loading", "kled", "accidental", "resistance", "reason_code", "reason_params", "display", "notes")

# The kinds a check in the fire situation may be (D-09: bending with its shear as two checks, buckling, compression and tension of the section -- no lateral torsional buckling), all along the grain
FIRE_KINDS = ("tension", "compression", "bending", "shear", "buckling")
# The keys of `fire` in a source, and the default of a new one: the three faces of a beam under a slab (SIA 265 Figur 13a), the duration following VKF 15-15
FIRE_KEYS = ("duration", "sides", "wood", "top_level")
FIRE_DEFAULT = {"duration": None, "sides": {"bottom": True, "top": False, "left": True, "right": True}, "wood": None, "top_level": False}
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
# What a shear check checks (spec 2026-10-21-commandes-typst-refonte, REQ-021, Q-010: «ajouter ces cisaillements dans l'onglet cisaillement, le user choisit dans un menu déroulant»): the shear of 4.2.5.1, the shear-off of 4.2.6 -- a force `F` on a length `l` and a width `w` --, the shear with a stress perpendicular to the grain of 4.2.7.1 -- V_z and `sigma_90`, transverse tension positive. Until then the two last were `#verify-shear-off` and `#verify-shear-perp`, computed in Typst alone.
SHEAR_VARIANTS = ("shear", "shear-off", "shear-perp")
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
    # the material of the library (issue #112, REQ-001): its fields at 1.3 only, each checked naming it
    if material_.carries_library(src) and version != LIBRARY_SCHEMA_VERSION:
        _fail(where, "carries %s at schema_version %r -- a source naming a material of the library is %r"
              % (", ".join(k for k in material_.FIELDS if k in src), version, LIBRARY_SCHEMA_VERSION))
    material_.check_fields(src, lambda message: _fail(where, message))
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
    variant = src.get("variant")
    if variant is not None and (kind != "shear" or variant not in SHEAR_VARIANTS):
        _fail(where, "variant is %r -- a shear check's: %s, or null for shear" % (variant, ", ".join(SHEAR_VARIANTS)))
    off = src.get("F")
    if off is not None and (not isinstance(off, dict) or not _number(off.get("value")) or off.get("unit") not in FORCE_UNITS):
        _fail(where, "F is %r -- a {value, unit} block, the design force sheared off (SIA 265 4.2.6), or null" % (off,))
    if src.get("sigma_90") is not None and not _number(src.get("sigma_90")):
        _fail(where, "sigma_90 is %r -- the design stress perpendicular to the grain in N/mm², transverse tension positive (4.2.7.1), or null" % (src.get("sigma_90"),))
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
    if src.get("schema_version") not in (FIRE_SCHEMA_VERSION, LIBRARY_SCHEMA_VERSION):
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


def write_source(here, src):
    """Writes one check's source, `checks/<id>.json`, as the «Traction» tab writes it (two spaces, the keys in their order, a last line ending) -- checked first (`check_source`: a malformed source stops, naming the field), written beside itself and moved into place. The one writer of a source outside the tab's draft (spec 2026-10-15, ARCH-RISK-206): «Importer» in the «Formules» tab writes a value changed in an unfolded check back here (REQ-009)."""
    import sharing
    check_source(src)
    path = here.checks_dir / ("%s.json" % src["id"])
    old = path.read_bytes() if path.is_file() else None
    sharing._commit([(path, engine.source_bytes(src), old)])
    return path


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
    """The schema_version a source is saved at, the lowest that holds what it carries: 1.3 with a field of the library -- `material`, a panel's `loading`, `kled`, `accidental`, `display` (issue #112), each left out where empty --, 1.2 with `fire` (links or not), 1.1 with a link, 1.0 with none -- what Woodcore's window calls before it writes one."""
    if not links.links_of(src):
        src.pop(links.LINKS, None)
    material_.drop_empty(src)
    if src.get("fire") is None:
        src.pop("fire", None)
    if material_.carries_library(src):
        src["schema_version"] = LIBRARY_SCHEMA_VERSION
    elif src.get("fire") is not None:
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


def f_c_90_table(grade, case, larger=False):
    """The f_c,90,d of SIA 265 Tabelle 8 or 9 for a class of the norm, a case of 4.2.2.2 and the bracketed value or not (note 4 / note 3) -- None where the table gives none (D30's bracketed values): what a compression at an angle reads, and what the five cards of the tab show (issue #112, UI-008)."""
    cell = sia265.grade(grade)["f_c_90_d"][case]
    return (cell.get("groessere_eindrueckungen") if larger else cell.get("value")) if isinstance(cell, dict) else (None if larger else cell)


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
    if src.get("l") is None and not out["reason"]:
        out["reason"] = "a compression at an angle to the grain needs the contact length l along the grain -- state it, in mm"
    if grade is not None and grade in sia265.grades():
        value = f_c_90_table(grade, case, larger)
        if value is None and not out["reason"]:
            out["reason"] = ("SIA 265 Tabelle %s gives %s no bracketed f_c,90,d for %s -- the larger indentations cannot be taken"
                             % (_table_of(grade).get("number", ""), grade, CASE_WORDS[case]))
        out["f_c_90_table"] = value
    return out


def read_building(here=None):
    """The project's building (project.building_file), checked: None where the file is absent -- a gap of the project, which a check following VKF 15-15 then says --, a ValidationError naming the field where it is malformed (a file Woodcore wrote)."""
    here = here or project.current()
    path = here.building_file
    if not path.is_file():
        return None
    where = here.rel(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _fail(where, "cannot be read as JSON -- %s" % exc)
    validation.validate_structure(data, BUILDING_SCHEMA, where)
    vkf.check_building(data, where)
    return data


def write_building(building, here=None):
    """Writes the project's building, checked first; stamps its schema_version. What the «Résistance au feu» tab saves (issue #46)."""
    here = here or project.current()
    path = here.building_file
    data = {"schema_version": BUILDING_SCHEMA_VERSION}
    data.update({key: building[key] for key in vkf.BUILDING_KEYS})
    validation.validate_structure(data, BUILDING_SCHEMA, here.rel(path))
    vkf.check_building(data, here.rel(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    engine.write_json(path, data)
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
    # the citation of a duration VKF 15-15 requires (REQ-001): its norm and the table it is read off, which the row t_fi then cites in the window and in the report; a duration the engineer states keeps SIA 265 4.5.2
    required = {"norm": requirement["norm"], "norm_ref": "Tabelle " + requirement["table"]} if minutes and origin == "vkf" else None
    out = {"duration": minutes if minutes else None, "duration_from": origin if minutes else None, "requirement": requirement, "required": required, "sides": sides,
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


def find_material(material_id, library=None):
    """The material an id of the library names (issue #112, REQ-002): one Woodcore ships (materials_catalogue), else the project's copy or the engineer's library -- `library` {id: material} where the caller read it (prepare), else read here, of the current project. None where none has it."""
    from domains import materials_catalogue
    found = materials_catalogue.find(material_id)
    if found is not None or material_.kind_of_id(material_id) != "user":
        return found
    if library is None:
        try:
            library = library_of(project.current())
        except project.ProjectError:
            library = {}
    return library.get(material_id)


def library_of(here):
    """{id: material} of the engineer's materials a project computes with -- its copies, then the library's for a draft not yet saved (materials_project.for_calculation) --, {} where they cannot be read."""
    from domains import materials_project
    try:
        return {m["id"]: m for m in materials_project.for_calculation(here)["materials"]}
    except (validation.ValidationError, OSError):
        return {}


def resolve(src, positions, values=None, building=None, library=None):
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

    # the material (issue #112, REQ-013): one of the library written over the position -- a class of SIA 265 by its grade, any other by its resistance --, else the position's class
    material_id = src.get("material")
    material_kind = material_.kind_of_id(material_id)
    material = None
    if material_kind == "grade":
        grade, grade_from = material_.grade_of(material_id), "stated"
    elif material_kind is not None:
        grade, grade_from = None, None
        material = find_material(material_id, library)
    else:
        grade, grade_from = follow(src.get("grade"), position_grade)
    refusal = None
    material_notes = []

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
    if not reason and material_kind in ("panel", "user") and material is None:
        refusal = material_.unknown_refusal(material_id)
        reason = refusal.text
    if not reason and not grade and material is None:
        reason = ("position %s gives no strength class -- state it here" % pid if record is not None
                  else "no strength class -- state one, or name a position that has one")
    if not reason and material is None and grade not in sia265.grades():
        reason = "strength class %r of position %s is not one of SIA 265 Tabelle 8 or 9 -- state one here" % (grade, pid)
    if not reason and moisture is None:
        reason = ("position %s states no moisture class -- state it here, or in the Positions tab" % pid if record is not None
                  else "no moisture class -- state one, or name a position that has one")
    resistance = None
    if not reason and material is not None:
        # what the check reads of a material that is no class of SIA 265, frozen into the record (ARCH-008) -- and why it cannot, naming the material, the loading, what it lacks (REQ-005, REQ-007)
        resistance, refusal, material_notes = material_.resistance(material, src, section, moisture)
        if refusal is not None:
            reason = refusal.text
        if not reason and src.get("fire") is not None:
            refusal = material_.fire_refusal(material)
            reason = refusal.text
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
    variant = src.get("variant") or "shear"
    if not reason and kind == "shear" and variant == "shear" and shears["V_z"] is None and shears["V_y"] is None:
        reason = "no shear force -- a shear check needs V_z, V_y or both"
    if not reason and kind == "shear" and variant == "shear-off":
        clause = sia265.shear_off()
        if not src.get("F") or src["F"]["value"] == 0:
            reason = "no F -- a shear-off (SIA 265 4.2.6) reads the force sheared off"
        elif not src.get("l"):
            reason = "no l -- a shear-off reads the sheared length along the grain, in mm"
        elif src["l"] < clause["min_shear_length"]:
            reason = "l is %s mm -- SIA 265 4.2.6 reads a sheared length of %s mm at least" % (_fmt(src["l"]), _fmt(clause["min_shear_length"]))
    if not reason and kind == "shear" and variant == "shear-perp":
        if shears["V_z"] is None:
            reason = "no V_z -- a shear with a stress perpendicular to the grain (SIA 265 4.2.7.1) reads V_z"
        elif src.get("sigma_90") is None:
            reason = "no sigma_90 -- a shear with a stress perpendicular to the grain reads that stress, transverse tension positive"
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
    if resistance is not None and resistance["type"] == "member" and contact["case"] is not None and "f_c_90" in resistance["values"]:
        contact["f_c_90_table"] = resistance["values"]["f_c_90"]["value"]   # the engineer's member: f_c,90,d «generell», the one it gives (REQ-005)
    if not reason and kind == "tension" and alpha == 0 and grade:
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
        fire, fire_reason = _fire_block(src, grade if not reason and grade else None, section if not reason and grade else None, building)
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
        # the variant written where it is not the shear of 4.2.5.1, so that a project without one exports as before (REQ-021, additive)
        variant = src.get("variant") or "shear"
        if variant != "shear":
            out["variant"] = variant
        if variant == "shear-off":
            out.update(F=dict(src["F"]) if src.get("F") else None, l=src.get("l"), w=src.get("w"))
        if variant == "shear-perp":
            out["sigma_90"] = src.get("sigma_90")
        if out["pith"] and grade and _family(grade) == "Brettschichtholz":
            # Tabelle 8 note 6 halves f_v,d of solid timber cut from the pith; Tabelle 9 has no such note -- the field stays as the source says, and is not applied (D-02 of spec 2026-10-12-audit-issues-47-48-49)
            warnings.append(engine.Note("check_pith_glulam", "%s: pith is true on %s, a glulam -- SIA 265 Tabelle 8 note 6 halves f_v,d of solid timber only, and Tabelle 9 has no such note: f_v,d is not halved" % (where, grade), check=cid, grade=grade))
    if fire is not None:
        out["fire"] = fire
    if provenance:
        out["links"] = provenance
    # the material of the library (issue #112, REQ-015): only where the source names one, so that every other record is exported as before
    if material_id is not None:
        shown = material if material is not None else find_material(material_id, library)
        out["material"] = {"id": material_id, "type": (shown or {}).get("type") or ("member" if material_kind == "grade" else None),
                           "origin": (shown or {}).get("origin") or ("user" if material_kind == "user" else None),
                           "names": dict((shown or {}).get("names") or {}), "from": "stated"}
        if material_kind == "panel" or (shown or {}).get("type") == "panel":
            out["loading"] = dict(src.get("loading") or {"mode": "plaque", "direction": "par"})
            out["kled"] = src.get("kled") or material_.DEFAULT_KLED
            out["accidental"] = bool(src.get("accidental"))
        if resistance is not None:
            out["resistance"] = resistance
        held = position_grade(record) if record is not None else ""
        if held and held != grade:
            # REQ-013: the position says another class -- said in orange («Classe de résistance est écrasée (GL24h) alors que T001 dit C24»)
            material_notes = [("material_overrides", {"material": material_id, "position": pid, "held": held})] + list(material_notes)
    if refusal is not None:
        out["reason_code"] = refusal.code
        out["reason_params"] = dict(refusal.params)
    if material_notes:
        out["notes"] = [{"code": code, "params": params} for code, params in material_notes]
    if src.get("display"):
        out["display"] = dict(src["display"])
    return out


# --- the Typst it comes to -----------------------------------------------------

# --- the instant calculation -----------------------------------------------------

# A force in kN, from the unit a source writes it in.
_TO_KN = {"N": 1e-3, "kN": 1.0, "MN": 1e3}


def compute(record):
    """`_compute`, and the ratio its verdict prints: `ratio`, the math source of the action over the resistance that governs -- the utilisation's own formula, or, where η is the larger of two sides (bending at an angle, across the grain), the formula of the side that gives it (issue #12: the window prints `σ/f = 0.41 ⩽ 1`, as the report does, and never η). Additive: every other key as `_compute` gives it."""
    result = _compute(record)
    if result:
        result["ratio"] = governing_ratio(result["rows"])
        # the row that gives η where η is the largest of several -- a side, an axis -- which the window frames with a dashed line (issue #112, REQ-014); the rows stay in the order of the calculation, η last
        result["governing"] = governing_rows(result["rows"])
    return result


def governing_rows(rows):
    """[key] of the row that governs a maximum -- the side or the axis whose utilisation η is (`max(…)`), the first on a tie, as `governing_ratio` reads it --, [] where η is no maximum (REQ-014)."""
    eta = next((row for row in rows if row["key"] == "eta"), None)
    if eta is None or not (eta.get("formula") or "").startswith("max("):
        return []
    sides = [row for row in rows if row["key"] in GOVERNING_KEYS]
    if not sides:
        return []
    return [max(sides, key=lambda row: row["value"])["key"]]


# The utilisations of the parts a check's η is the largest of: the two sides of a section at an angle, the section and its stability about each axis (issue #38)
GOVERNING_KEYS = ("eta_m_t", "eta_m_c", "eta_s", "eta_y", "eta_z", "eta_m")


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
    """`_lines(record)` with its lines written by the engine (`_calculation`) and given back as rows -- the shape the window, `unfold`, `published_vars` and the parity with the report read (REQ-003) --, each row whose formula reads in the registry's keys given them (`_with_keys`). None where `_lines` gives none."""
    result, calculation = _calculation(record)
    if result is None:
        return None
    return dict(result, rows=_with_keys(calculation.rows(), record))


def section_sides(record):
    """[(key, symbol, value)] of the section's sides an unfolded check declares first: b and h, or d -- in the fire situation the initial section's, `b_0`, `h_0` (`d_0`), the rows of the residual section then being b and h, as #member(fire:) names them (spec 2026-10-21-commandes-typst-refonte, REQ-017)."""
    section = record["section"]
    sides = ("d",) if section["type"] == "cir" else ("b", "h")
    suffix = "_0" if record.get("fire") else ""
    return [(side + suffix, side + suffix, section[side]) for side in sides]


def _with_keys(rows, record):
    """`rows`, each that carries no `keys` but a formula given the formula in the registry's keys -- **only where that formula, computed as `#eq` computes it (calc/units.py), gives the row's own value** to 1e-9 (spec 2026-10-21-commandes-typst-refonte, REQ-017, ARCH-003): a row whose formula cannot be read that way -- a branch, a value of a table written as a number, a residual section in the fire situation -- keeps none, and an unfolded check writes its value as a literal checked by `domain:` (`published_vars`). The values a formula may name are those the unfolded file declares before it: the section's sides, then the rows above it and the values of their tables."""
    known, values = {}, {}
    for key, symbol, value in section_sides(record):
        known[symbol], values[key] = key, (value, "mm")
    out = []
    for row in rows:
        row = dict(row)
        table = row.get("table")
        if table:
            known[table["symbol"]] = table["key"]
            values[table["key"]] = (table["value"], table["unit"])
        if not row.get("keys") and row.get("formula") and row["key"] != "eta":
            keys = line_keys.keys_of(row["formula"], known)
            if line_keys.computes(keys, values, row["key"], row["value"], row.get("unit")):
                row["keys"] = keys
        if row["key"] == "eta" and not row.get("keys") and row.get("formula"):
            keys = line_keys.keys_of(row["formula"], known)
            if line_keys.computes(keys, values, row["key"], row["value"], row.get("unit")):
                row["keys"] = keys
        known[row["symbol"]] = row["key"]
        values[row["key"]] = (row["value"], row.get("unit") or "")
        out.append(row)
    return out


def _calculation(record):
    """The result of `_lines(record)` and the TimberCalculation its lines are written into, once, in the order the report prints them -- (None, None) where the record cannot be calculated."""
    result = _lines(record)
    if result is None:
        return None, None
    return result, TimberCalculation().take(result["rows"])


def _lines(record):
    """The check of `record` computed at once, in Python, for Woodcore to show while a draft is typed -- with no Typst compile in the way (the engineer, 07.10.2026). **The report does not read it**: `#show-check-member` computes the same check in Typst, and `tests/test_member_check.py` holds the two equal. Every value of SIA 265 is read through `norms.sia265` (Tabelle 8 or 9, Tabelle 4's eta_w, 2.2.6's eta_t), never written here, and the arithmetic is lib/timber.typ's: a design value is the table's times eta_w times eta_t, A is b·h or π·d²/4, A_c is l·w, and f_alpha is (9) or (13).

    Gives None where the record cannot be calculated or its kind is not implemented; otherwise
    {"kind", "equation", "clause", "rows": [Line, …], "eta", "ok", "relation"},
    the rows -- timber_calc Lines -- in the order the report prints them and named by the registry's keys (`symbol` the Typst math source the page sets), `eta` the utilisation, `ok` whether it holds (eta <= 1, a tie absorbed at 1e-9), `relation` the norm's inequality in those keys."""
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
    # each row cites the clause #member(fire:) cites for it (lib/timber.typ), so the window and the report say the same (C2, v0.120)
    residual = clause["d_red"]["norm_ref"]
    required = fire.get("required")
    rows = [_row("t_fi", "t", fire["duration"], "min", label="R%d" % fire["duration"], clause=required["norm_ref"] if required else clause["norm_ref"],
                 norm=required["norm"] if required else NORM),
            _row("beta_n", "beta_n", fire["beta_n"], "mm/min", clause="Tabelle " + clause["charring"]["table"]),
            _row("d_char_n", "d_(char,n)", d_char, "mm", "beta_n dot t", clause=residual),
            _row("d_red", "d_(red)", clause["d_red"]["value"], "mm", clause=residual),
            _row("d_ef", "d_(ef)", fire["d_ef"], "mm", "d_(char,n) + d_(red)", clause=residual),
            _row("b", "b_(fi)", fire["b"], "mm", reduced("b_0", n_b), clause=residual),
            _row("h", "h_(fi)", fire["h"], "mm", reduced("h_0", n_h), clause=residual),
            _row("k_fi", "k_(fi)", k_fi, "", clause=clause["resistance_factor"]["norm_ref"])]
    result = _compute_section(dict(record, section={"type": "rec", "b": fire["b"], "h": fire["h"], "text": section.get("text", "")}), k_fi)
    result["rows"] = rows + result["rows"]
    return result


def _compute_section(record, k_fi=1.0):
    """`_compute` of a record at normal temperature -- or, with `k_fi` and the residual section put in `record`, in the fire situation: every design value along the grain times k_fi, its formula saying so."""
    fire = k_fi != 1.0
    kind = record["kind"]
    alpha = record.get("alpha", 0)
    # what the check reads of its material (issue #112, ARCH-RISK-005): a class of SIA 265 its table's values times eta_w and eta_t, as always; a member of one's own its design values times the same; a panel η_mod and γ_M of SIA 265/1
    strengths = material_.Strengths(record, k_fi)
    row = strengths.row
    section = record["section"]
    if section["type"] == "cir":
        area = math.pi * section["d"] ** 2 / 4
        area_row = _row("A", "A", area, "mm²", "pi dot d^2 / 4", keys="pi dot d^2 / 4")
    else:
        area = section["b"] * section["h"]
        area_row = _row("A", "A", area, "mm²", "b dot h", keys="b dot h")
    factors = strengths.factor_rows
    design = strengths.design

    def at_angle(f0, f90):
        a = math.radians(alpha)
        return f90 * f0 / (f0 * math.sin(a) ** 2 + f90 * math.cos(a) ** 2)

    if kind == "bending":
        return _compute_bending(record, row, area, area_row, factors, design, at_angle, strengths)
    if kind == "shear":
        return _compute_shear(record, area, area_row, factors, design, row, strengths)
    if kind == "buckling":
        return _compute_buckling(record, row, area, area_row, factors, design)
    if kind == "lateral-torsional":
        return _compute_lateral(record, row, area, area_row, factors, design, strengths)
    force = record["N"]["value"] * _TO_KN[record["N"]["unit"]]       # kN
    if kind == "tension":
        force_row = _row("N_t_d", "N_(t,d)", force, "kN")
        sigma = force * 1000 / area                                    # N/mm²
        if alpha == 0:
            f, f_row = design("f_t_0_d", "f_(t,0,d)", row["f_t_0_d"])
            rows = [area_row, force_row] + factors + [f_row, _row("sigma_t_0_d", "sigma_(t,0,d)", sigma, "N/mm²", "N_(t,d) / A", keys="N_t_d / A", clause="4.2.1.1")]
            out = {"equation": "(6)", "clause": "4.2.1.1", "relation": "sigma_t_0_d <= f_t_0_d"}
        elif alpha == 90:
            f, f_row = design("f_t_90_d", "f_(t,90,d)", row["f_t_90_d"])
            rows = [area_row, force_row] + factors + [f_row, _row("sigma_t_90_d", "sigma_(t,90,d)", sigma, "N/mm²", "N_(t,d) / A", keys="N_t_d / A", clause="4.2.1.2")]
            out = {"equation": "(7)", "clause": "4.2.1.2", "relation": "sigma_t_90_d <= f_t_90_d"}
        else:
            f0, f0_row = design("f_t_0_d", "f_(t,0,d)", row["f_t_0_d"])
            f90, f90_row = design("f_t_90_d", "f_(t,90,d)", row["f_t_90_d"])
            f = at_angle(f0, f90)
            rows = [area_row, force_row, _row("alpha", "alpha", alpha, "°")] + factors + [
                f0_row, f90_row,
                _row("f_t_alpha_d", "f_(t,alpha,d)", f, "N/mm²", "f_(t,90,d) dot f_(t,0,d) / (f_(t,0,d) dot sin(alpha)^2 + f_(t,90,d) dot cos(alpha)^2)",
                     keys="f_t_90_d dot f_t_0_d / (f_t_0_d dot sin(alpha)^2 + f_t_90_d dot cos(alpha)^2)", clause="4.2.1.3 (9)"),
                _row("sigma_t_alpha_d", "sigma_(t,alpha,d)", sigma, "N/mm²", "N_(t,d) / A", keys="N_t_d / A", clause="4.2.1.3")]
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
    stress = rows[-1].symbol
    ratio = "%s / %s" % (stress, ("f" + stress[len("sigma"):]))
    rows.append(_row("eta", "eta", eta, "", ratio, keys=out["relation"].replace(" <= ", " / ")))
    return {"kind": kind, "equation": out["equation"], "clause": out["clause"], "rows": rows,
            "eta": eta, "ok": eta <= 1 + 1e-9, "relation": out["relation"]}


# A moment in kNm, from the unit a source writes it in.
_TO_KNM = {"Nm": 1e-3, "kNm": 1.0, "MNm": 1e3}


def _bending_values(record, row, strengths):
    """What a bending check reads of its member, as `#member` computes it: the moments in kNm (a moment absent or 0 is None), W_y and W_z (π·d³/32 for both about a round section), k_h of glulam under 600 mm (3.4.2.3, `sia265.k_h`) and f_m,y,d, f_m,z,d -- with the rows each prints. `strengths` (member_check_material.Strengths) gives f_m,d: a class's or a member's k_h · η_w · η_t · f_m,d, a panel's by SIA 265/1, no k_h (issue #112). Shared by the section's check (`_compute_bending`) and lateral torsional buckling (`_compute_lateral`), so the arithmetic is written once."""
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
    glulam = strengths.glulam
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
    bent = {axis: strengths.bending(axis, k_h["k_h_" + axis]) for axis in ("y", "z")}
    f_m = {axis: bent[axis][0] for axis in ("y", "z")}
    clause_m, norm_m, label_m = strengths.bending_clause()
    f_m_rows = {axis: _row("f_m_%s_d" % axis, "f_(m,%s,d)" % axis, f_m[axis], "N/mm²", bent[axis][1], label_m, clause=clause_m, norm=norm_m)
                for axis in ("y", "z")}
    moment_rows = [_row("%s_d" % key, "M_(%s,d)" % key[-1], moments[key], "kNm") for key in MOMENTS if moments[key]]
    return {"moments": moments, "w_y": w_y, "w_z": w_z, "k_h": k_h, "k_rows": k_rows, "f_m": f_m, "f_m_rows": f_m_rows,
            "modulus_rows": modulus_rows, "moment_rows": moment_rows}


def _compute_bending(record, row, area, area_row, factors, design, at_angle, strengths):
    """`compute` for a bending, the section alone -- `#member`'s section values and design values, then verify-bending's or verify-bending-normal's arithmetic (lib/timber.typ): W_y = b·h²/6 and W_z = h·b²/6, or π·d³/32 for both; f_m by k_h for glulam under 600 mm (3.4.2.3, `sia265.k_h`); then (14), (15)/(16), (17) to (20), (21) or (22), and at an angle with a normal force (21) or (22) with (9) or (13), (19), (20) on the side where N adds and (17) or (18) on the other -- the engineer's reading (08.10.2026). `factor` is eta_w·eta_t. The rows are named by the registry's keys; the utilisation of each side is `eta_m_t` and `eta_m_c`, as the report stores it."""
    alpha = record.get("alpha", 0)
    normal = record["N"]["value"] * _TO_KN[record["N"]["unit"]]       # kN, tension positive
    values = _bending_values(record, row, strengths)
    moments, w_y, w_z, k_rows, f_m, f_m_rows = values["moments"], values["w_y"], values["w_z"], values["k_rows"], values["f_m"], values["f_m_rows"]
    modulus_rows, moment_rows = values["modulus_rows"], values["moment_rows"]
    f90_c_table = (row.get("f_c_90_d") or {}).get("generell")
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


def _compute_shear(record, area, area_row, factors, design, row, strengths):
    """`compute` for a shear check, by its variant (REQ-021): the shear of 4.2.5.1 (`_compute_shear_v`), the shear-off of 4.2.6, the shear with a stress perpendicular to the grain of 4.2.7.1."""
    variant = record.get("variant") or "shear"
    if variant == "shear-off":
        return _compute_shear_off(record, factors, design, row, strengths.family)
    if variant == "shear-perp":
        return _compute_shear_perp(record, area, area_row, factors, design, row)
    return _compute_shear_v(record, area, area_row, factors, design, row, strengths.family)


def _compute_shear_off(record, factors, design, row, family):
    """`compute` for a shear-off, SIA 265 4.2.6 -- verify-shear-off's arithmetic, now Python's (REQ-021): tau_a = F / (l · w), w the member's width where none is given, against k_a · f_v,d, k_a 0.6 for solid timber (26) and 0.8 for glulam (27), the sheared length at least the clause's."""
    clause = sia265.shear_off()
    force = abs(record["F"]["value"]) * _TO_KN[record["F"]["unit"]]        # kN
    length = record["l"]
    width = record.get("w") or record["section"].get("b") or record["section"].get("d")
    tau = force * 1000 / (length * width)
    k_a = clause["factor"][family]
    rows = [_row("F_a_d", "F_(a,d)", force, "kN"), _row("l_a", "l_a", length, "mm"),
            _row("w_a", "w_a", width, "mm", label=None if record.get("w") else "b"),
            _row("tau_a_d", "tau_(a,d)", tau, "N/mm²", "F_(a,d) / (l_a dot w_a)", clause=clause["norm_ref"])]
    rows += factors
    f_v, f_v_row = design("f_v_d", "f_(v,d)", row["f_v_d"])
    rows += [f_v_row, _row("k_a", "k_a", k_a, "", label=family, clause="%s (%s)" % (clause["norm_ref"], clause["equation"][family]))]
    eta = tau / (k_a * f_v)
    rows.append(_row("eta", "eta", eta, "", "tau_(a,d) / (k_a dot f_(v,d))"))
    return _result("shear", "(%s)" % clause["equation"][family], clause["norm_ref"], rows, eta, "tau_a_d <= k_a dot f_v_d")


def _compute_shear_perp(record, area, area_row, factors, design, row):
    """`compute` for a shear with a stress perpendicular to the grain, SIA 265 4.2.7.1 -- verify-shear-perp's arithmetic, now Python's (REQ-021): tau_d = 1.5 · V_z / A (4/3 for a circle), sigma_90,d between -f_c,90,d and f_t,90,d, k_t,90 by its sign, and equation (28)."""
    clause = sia265.shear_transverse()
    factor = SHEAR_FACTORS[record["section"]["type"]]
    force = abs(record["V_z"]["value"]) * _TO_KN[record["V_z"]["unit"]]
    tau = factor * force * 1000 / area
    sigma = record["sigma_90"]
    k = clause["k_t_90"]["querzug" if sigma >= 0 else "querdruck"]
    rows = [area_row, _row("V_z_d", "V_(z,d)", force, "kN"),
            _row("tau_d", "tau_d", tau, "N/mm²", "%s dot V_(z,d) / A" % ("4/3" if factor != 1.5 else "1.5")),
            _row("sigma_90_d", "sigma_(90,d)", sigma, "N/mm²"),
            _row("k_t_90", "k_(t,90)", k, "", label="Querzug" if sigma >= 0 else "Querdruck", clause=clause["norm_ref"])]
    rows += factors
    f_c90_table = row["f_c_90_d"]["generell"]
    f_c90_table = f_c90_table.get("value") if isinstance(f_c90_table, dict) else f_c90_table
    f_c90, f_c90_row = design("f_c_90_d", "f_(c,90,d)", f_c90_table)
    f_t90, f_t90_row = design("f_t_90_d", "f_(t,90,d)", row["f_t_90_d"])
    f_v, f_v_row = design("f_v_d", "f_(v,d)", row["f_v_d"])
    rows += [f_c90_row, f_t90_row, f_v_row]
    resisted = f_c90 / (f_c90 + k * f_t90)
    eta = ((f_c90 + sigma) / (f_c90 + k * f_t90)) ** 2 + (tau / f_v) ** 2 * (1 - resisted ** 2)
    formula = "((f_(c,90,d) + sigma_(90,d)) / (f_(c,90,d) + k_(t,90) dot f_(t,90,d)))^2 + (tau_d / f_(v,d))^2 dot (1 - (f_(c,90,d) / (f_(c,90,d) + k_(t,90) dot f_(t,90,d)))^2)"
    rows.append(_row("eta", "eta", eta, "", formula, clause=clause["norm_ref"]))
    # (28) in the registry's keys, the relation an unfolded check verifies before its utilisation is written
    relation = "((f_c_90_d + sigma_90_d) / (f_c_90_d + k_t_90 dot f_t_90_d))^2 + (tau_d / f_v_d)^2 dot (1 - (f_c_90_d / (f_c_90_d + k_t_90 dot f_t_90_d))^2) <= 1"
    out = _result("shear", "(28)", clause["norm_ref"], rows, eta, relation)
    if not -f_c90 <= sigma <= f_t90:
        # sigma_90,d outside -f_c,90,d … f_t,90,d (issue #112, REQ-008): said in orange, the check computed all the same
        out["notes"] = [{"code": "sigma_90_outside", "field": "sigma_90", "level": "warn",
                         "params": {"sigma": _fmt(round(sigma, 3)), "f_c_90_d": _fmt(round(f_c90, 3)), "f_t_90_d": _fmt(round(f_t90, 3))}}]
    return out


def _compute_shear_v(record, area, area_row, factors, design, row, family):
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
    pith = bool(record.get("pith")) and family == "Vollholz"   # Tabelle 8 note 6, solid timber only (D-02)
    if pith:
        f_v = f_v / 2
        rows.append(_row("f_v_d_p", "f_(v,d)", f_v, "N/mm²", "f_(v,d) / 2", "Markstück"))
        relation = "tau_d <= f_v_d_p"
    else:
        relation = "tau_d <= f_v_d"
    eta = tau_d / f_v
    rows.append(_row("eta", "eta", eta, "", "%s / %s" % (shown_tau, "(f_(v,d) / 2)" if pith else "f_(v,d)")))
    return _result("shear", "(23)", "4.2.5.1", rows, eta, relation)


def strong_axis(section):
    """The axis lateral torsional buckling tips about, as `timber-tips` in lib/timber.typ reads it (D-09): "y" for a rectangle as high as wide or higher -- the norm's own case --, "z" for one wider than high, None for a round section, which does not tip (D-10)."""
    if section is None or section.get("type") == "cir":
        return None
    return "z" if section["b"] > section["h"] else "y"


def _family(grade):
    return "Brettschichtholz" if grade in {g["id"] for g in sia265.table_9()["grades"]} else "Vollholz"


# --- the export ----------------------------------------------------------------

def empty():
    """The export of a project with no member check -- what export_all.seed writes so that a report compiles from the start."""
    return {"schema_version": EXPORT_SCHEMA_VERSION, "checks": {}}


def prepare(here, positions, values=None):
    """Every member check of `here`, read, checked and resolved against `positions` -- and its linked fields against `values` (`links.index`), a check in the fire situation against the project's building (`read_building`) --, as data/checks.json holds it. Nothing is written. A malformed source stops; anything the project lacks is in the record, `calculable: false` and its reason (the warnings are on each record: `warnings_of`)."""
    checks, seen = {}, {}
    building = read_building(here)
    library = None   # the engineer's materials the checks name, read once where one names a u-… (issue #112, REQ-002)
    for path in source_paths(here):
        src = read_source(path)
        lower = src["id"].lower()
        if lower in seen:
            _fail("checks/%s" % path.name, "id %r is also %s's -- ids differ by more than their case" % (src["id"], seen[lower]))
        seen[lower] = path.name
        if library is None and material_.kind_of_id(src.get("material")) == "user":
            library = library_of(here)
        record = resolve(src, positions, values, building, library)
        record["warnings"] = [str(note) for note in record["warnings"]]
        checks[src["id"]] = record
        if is_unfolded(record):
            record["vars"] = published_vars(record)
    linked = any("links" in record for record in checks.values())
    burning = any("fire" in record for record in checks.values())
    unfolded_any = any(is_unfolded(record) for record in checks.values())
    required_any = any((record.get("fire") or {}).get("required") for record in checks.values())
    library_any = any(key in record for record in checks.values() for key in LIBRARY_RECORD_KEYS)
    version = (LIBRARY_EXPORT_VERSION if library_any else UNFOLDED_BASE_EXPORT_VERSION if unfolded_any else REQUIRED_EXPORT_VERSION if required_any else FIRE_EXPORT_VERSION if burning
               else LINKED_EXPORT_VERSION if linked else EXPORT_SCHEMA_VERSION)
    data = {"schema_version": version, "checks": checks}
    validation.validate_structure(data, EXPORT_SCHEMA)
    validation.validate_checks_business(data)
    return data


def mark_unfolded_files(data, files):
    """Each check of `data` printed unfolded given its `file` -- the file of its domain from the Typst root where `files` names one (domains/unfold.py `unfolded_files`), none where the engineer wrote another -- and the export's version made the one that carries it (1.6). Returns whether anything was marked."""
    marked = False
    for rid, record in data["checks"].items():
        if is_unfolded(record):
            record["file"] = files.get(rid)
            marked = True
    if marked:
        if data["schema_version"] != LIBRARY_EXPORT_VERSION:
            data["schema_version"] = UNFOLDED_BASE_EXPORT_VERSION   # 1.7 holds 1.6's file already
        validation.validate_structure(data, EXPORT_SCHEMA)
    return marked


def is_unfolded(record):
    """Whether `record` is printed unfolded, as a domain of the «Formules» tab (spec 2026-10-15, D-11): a calculable check of a kind unfolded so far, not in the fire situation (D-15)."""
    from domains import unfold
    return bool(record.get("calculable")) and record.get("kind") in unfold.UNFOLDED_KINDS


def form_of(record):
    """The form an unfolded check is written from -- its kind, the equation of SIA 265 its verdict follows and the writer's version --, exactly as `#var-domain(..., gen:)` writes it (REQ-003). None where `record` is not unfolded."""
    from domains import unfold
    if not is_unfolded(record):
        return None
    return {"kind": record["kind"], "form": compute(record)["equation"], "version": unfold.GENERATOR_VERSION}


def published_vars(record):
    """The values an unfolded check's literals are checked against (`domain: ("check", id)`, ARCH-007): the section's sides, every row of `compute` that is an input -- one with no `keys`: the force, the angle, eta_w, eta_t -- and every value of SIA 265's tables a design value is computed from, each a var of the export (value, unit, symbol, and the norm and clause it is read from). Nothing is computed here that `compute` does not."""
    if not is_unfolded(record):
        return {}
    source = SOURCE
    out = {}

    result = compute(record)

    def put(key, symbol, value, unit, clause=None, label=None, norm=NORM):
        # a value entered -- a side, a force, an angle -- cites the clause of the check it serves (Q-011, v0.120): every value names its norm
        out[key] = {"value": value, "unit": unit, "symbol": symbol, "label": label, "description": None,
                    "norm": norm, "norm_ref": clause or result["clause"], "source": source}

    for key, symbol, value in section_sides(record):
        put(key, symbol, value, "mm")
    for row in result["rows"]:
        # a row the unfolded file computes is an #eq of its own; every other is written as a literal checked here -- an input, or a value whose formula the file cannot compute (`_with_keys`), η among them where it is the largest of several
        if not row.get("keys"):
            put(row["key"], row["symbol"], row["value"], row["unit"], row.get("clause"), row.get("label"), row.get("norm", NORM))
        table = row.get("table")
        if table:
            put(table["key"], table["symbol"], table["value"], table["unit"], table["clause"])
    return out


def utilisations(data):
    """{check id: {"eta", "ok", "clause"}} of every check of `data` (data/checks.json) that can be calculated, computed as its tab computes it (`compute`): what the command palette shows beside a check and gathers among the warnings where it is above 1 (issue #83). A check that cannot be calculated, or whose computation gives nothing, is left out."""
    out = {}
    for ident, record in (data.get("checks") or {}).items():
        if not record.get("calculable"):
            continue
        result = compute(record)
        if result and isinstance(result.get("eta"), (int, float)):
            out[ident] = {"eta": float(result["eta"]), "ok": bool(result.get("ok")), "clause": str(result.get("clause") or "")}
    return out


def warnings_of(data):
    """Every warning the records of `data` carry, in the order of the checks -- what export_all prints."""
    return [w for record in data["checks"].values() for w in record.get("warnings", [])]


def write(data, data_dir):
    """data/checks.json."""
    engine.write_json(Path(data_dir) / EXPORT_FILE, data)


def export(here=None, moved=()):
    """prepare() then write(), against the positions the last export wrote -- what Woodcore runs when a check is saved, so that one check is exported without the workbooks being read again (connector.export's arrangement). `moved`: the checks whose kind the save changed and whose file it moved (issue #112, REQ-011) -- written again in their new form after the export, the engineer's changed lines kept (`unfold.regenerate`)."""
    from domains import connector   # known_positions: the one reader of the exported positions Woodcore's tabs share
    here = here or project.current()
    import variable_sources   # the reader of data/'s variables, which imports the domains: imported here, as connector is
    sync_materials(here)
    data = prepare(here, connector.known_positions(here.data_dir), variable_sources.known_values(here.data_dir))
    write(data, here.data_dir)
    # a check printed unfolded gets its domain when it is first saved (spec 2026-10-15, REQ-002), and the index of the domains lists it
    from domains import formula_domain, unfold
    if unfold.unfold_checks(here, data):
        formula_domain.export(here)
    from domains import unfold_display
    for rid in moved:
        try:
            unfold.regenerate(here, rid)
            unfold_display.apply_check_display(here, rid, data["checks"][rid], retitle=True)
        except (unfold.UnfoldError, KeyError):
            pass   # a conflict, or a check no longer unfolded: the «Formules» tab asks it line by line
    return data


def save_kind_change(here, rid, old_kind, new_kind):
    """What a save does before the export when the stability was ticked or unticked (REQ-011, ARCH-009): the file moved to the folder of the new kind (`unfold.move_domain`). Returns the ids to write again in the new form (`export(moved=)`)."""
    from domains import unfold
    return (rid,) if unfold.move_domain(here, rid, old_kind, new_kind) is not None else ()


def after_unfold(here, rid, record):
    """What `unfold.unfold_domains` writes onto a check's file after its lines: the options of «Affichage» its source keeps (issue #112, REQ-010, ARCH-010) -- `unfold_display.apply_check_display`."""
    from domains import unfold_display
    return unfold_display.apply_check_display(here, rid, record)


def change_kind(src, stability):
    """The source with its stability ticked or not (issue #112, REQ-011, Q-001 A): a compression becomes a buckling and a bending a lateral torsional buckling -- along the grain, alpha 0, the system lengths and coefficients of `new_source` added where it has none --, and back. The id, the position, the material, the section and the forces stay. The kind is what a check is listed, exported and filed by; the save moves its file (`unfold.move_domain`)."""
    out = dict(src)
    kind = out["kind"]
    target = {("compression", True): "buckling", ("bending", True): "lateral-torsional",
              ("buckling", False): "compression", ("lateral-torsional", False): "bending"}.get((kind, bool(stability)))
    if target is None:
        return out
    out["kind"] = target
    if stability:
        out["alpha"] = 0
        defaults = new_source(out["id"], target)
        for key in LENGTHS + BETAS + ("a", "sigma_m_crit"):
            if key in defaults and out.get(key) is None:
                out[key] = defaults[key]
        if out.get("sigma_m_crit") is not None:
            out["a"] = None
    else:
        for key in ("l_y", "l_z", "beta_y", "beta_z", "a", "sigma_m_crit"):
            out.pop(key, None)
        if target == "compression":
            out.setdefault("case", "generell")
            out.setdefault("larger", False)
            out.setdefault("l", None)
            out.setdefault("w", None)
    return out


def sync_materials(here):
    """The project's copies of the engineer's materials made to follow what its cases name -- the checks among them (issue #112, REQ-002, D-21): a copy taken of a member or a panel of one's own a check newly names, at the save, before the export (materials_project.sync, as the permanent loads do). A material neither copied nor in the library is left to the check, which then says it cannot be calculated; a project whose materials.json is still at 1.0 is left as it is."""
    from domains import materials_project
    try:
        used = materials_project.used_ids(here)
        if used or materials_project.copies(here):
            materials_project.sync(used, here)
    except (validation.ValidationError, OSError):
        pass


def references(record):
    """What an exported check names of the project's other objects, [(kind, id, field)] -- its position (domains/dependency_graph.py, spec 2026-10-21-graphe-dependances, ARCH-RISK-1103). The variables its fields follow are read off its source (`links.references`)."""
    return [("position", record["position"], "position")] if record.get("position") else []
