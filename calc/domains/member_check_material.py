"""What a member check reads of its material -- a class of SIA 265, a member of the engineer's own, a wood-based panel of SIA 265/1 (spec docs/requirements/completed/2026-10-24-verifications-elements-v3.md, REQ-001 to REQ-007, REQ-016, ARCH-001, ARCH-002, ARCH-008; issue #112).

`member_check.py` keeps the arithmetic of SIA 265 chapter 4; this module says **which resistance it computes with**, written once and without Qt:

* **the source's fields** (`check_fields`): `material` -- an id of the library (`sia265:C24`, `sia265-1:osb3`, `u-<8 hex>`), absent to follow the position --, a panel's `loading` {mode: plaque | voile | tc, direction: par | perp}, its `kled` and `accidental`, and `display`, the options of «Affichage» (REQ-010);
* **what a check reads** (`needs`): by its kind, its angle, its variant, the sign of its normal force -- f_m,d, f_t,0,d, f_c,0,d, f_t,90,d, f_c,90,d (by its case), f_v,d, k_a, β_c, f_c,0,k, E_0,05, f_m,k (REQ-005); the same table gives the menu's line of each material (`offered`) and whether a panel's loading bubble has a value (`loading_value`);
* **the resistance frozen into the record** (`resistance`, ARCH-008): what `resolve` reads of the library or the project's copy once, so that `compute` stays a function of the record and the norms. A class of SIA 265 freezes nothing: `compute` reads it from `norms.sia265` as it always did, the same numbers to the bit (CON-002);
* **the factors** (`Strengths`, REQ-006): a member's f_d = η_w · η_t · the table's value (SIA 265 2.2.2 eq. 3; γ_M/η_M of Tabelle 1 already in Tabellen 8 and 9, 3.3.2.1); a panel's f_d = η_mod · f_k / γ_M (SIA 265/1 6.1.2.1 eq. 5), η_mod of Tableau 9 by moisture class and KLED, γ_M of Tableau 6 or 1,0 in an accidental situation (note 1) -- the b table's own value where those are moisture class 1, KLED medium and a normal situation (D-23). No k_h for a panel: SIA 265/1 has none.

A reason a check cannot be calculated is a code with its numbers (`Refusal`), which `member_check.resolve` writes in English into `reason` and the window says in its language (`member_check_tab_words`). Every value is read from `calc/norms/` or the material: none is written here (ARCH-002).
"""

import re
from dataclasses import dataclass, field

from domains import materials_contract as contract
from domains.timber_calc import NORM, line as _row
from norms import sia265, sia265_1
from number_text import exact as _fmt

# A panel's loading, as the source writes it, and the loading of SIA 265/1's grid it reads (Tableaux 11 to 23: plate, shear, axial)
MODES = ("plaque", "voile", "tc")
GRID = {"plaque": "plate", "voile": "shear", "tc": "axial"}
DIRECTIONS = contract.DIRECTIONS
KLED = sia265_1.KLED
DEFAULT_KLED = sia265_1.DESIGN_KLED
DEFAULT_CLASS = sia265_1.DESIGN_CLASS
PANEL_NORM = "SIA 265/1"

# The fields of a source this module checks, and those only a panel carries (REQ-001); `impact` (η_t) is a member's
FIELDS = ("material", "loading", "kled", "accidental", "display")
PANEL_FIELDS = ("loading", "kled", "accidental")

# The options of «Affichage» a check keeps in its source (REQ-010): the report's level (None: auto), the member's line printed from a level on or not at all, the verdict as a ratio or in percent, the description and the title printed
DISPLAY = {"level": (0, 1, 2, 3), "member_line": ("none", 1, 2, 3), "verdict": ("ratio", "percent"), "description": (True, False), "title": (True, False)}
DISPLAY_DEFAULT = {"level": None, "member_line": None, "verdict": "percent", "description": False, "title": True}

PANEL_ID = re.compile(r"^sia265-1:[a-z0-9_-]+$")
GRADE_PREFIX = "sia265:"

# What a check reads of its material, by quantity: the key of a member's values (Tabellen 8 and 9, materials_contract.MEMBER_STRENGTHS), and for a panel the loading of the grid and the row -- f_m and f_v under the loading chosen (plate or shear), f_t and f_c always in the plane (axial), in the direction chosen. A quantity a panel has no row for (f_t,90, f_c,90, k_a, …) it does not give (D-19).
MEMBER_KEY = {"f_m": "m", "f_t_0": "t_0", "f_c_0": "c_0", "f_t_90": "t_90", "f_c_90": "c_90", "f_v": "v"}
PANEL_ROW = {"f_m": (None, "f_m"), "f_v": (None, "f_v"), "f_t_0": ("axial", "f_t"), "f_c_0": ("axial", "f_c")}
# The symbol each quantity is said by -- in a reason, in the menu's line
SYMBOLS = {"f_m": "f_m,d", "f_t_0": "f_t,0,d", "f_c_0": "f_c,0,d", "f_t_90": "f_t,90,d", "f_c_90": "f_c,90,d", "f_v": "f_v,d",
           "k_a": "k_a", "beta_c": "β_c", "f_c_0_k": "f_c,0,k", "E_0_05": "E_0,05", "f_m_k": "f_m,k"}
# The quantity each of the four tabs shows in the menu's line and its loading bubble (UI-005, UI-006)
TAB_QUANTITY = {"tension": "f_t_0", "compression": "f_c_0", "bending": "f_m", "shear": "f_v"}
# The loading bubbles a panel offers in each tab, as the engineer validated them for OSB/3 (T35, CON-005)
TAB_LOADINGS = {"bending": (("plaque", "par"), ("plaque", "perp"), ("voile", "par"), ("voile", "perp")),
                "tension": (("tc", "par"), ("tc", "perp")), "compression": (("tc", "par"), ("tc", "perp")),
                "shear": (("plaque", "par"), ("voile", "par"))}
# The tab a kind is listed in (REQ-011: the stability is the last accordion of compression and bending)
TAB_OF_KIND = {"tension": "tension", "compression": "compression", "buckling": "compression", "bending": "bending", "lateral-torsional": "bending", "shear": "shear"}


@dataclass(frozen=True)
class Refusal:
    """Why a check cannot be calculated with its material: `code` -- the window's words are `mc_why_<code>` -- and its numbers; `text` the English the record's `reason` carries."""
    code: str
    params: dict = field(default_factory=dict)
    text: str = ""


# --- the source --------------------------------------------------------------------------

def kind_of_id(material_id):
    """"grade" (a class of SIA 265), "panel" (a panel of SIA 265/1), "user" (the engineer's own) or None for an id of none of the three."""
    mid = str(material_id or "")
    if mid.startswith(GRADE_PREFIX):
        return "grade"
    if PANEL_ID.match(mid):
        return "panel"
    if contract.USER_ID.match(mid):
        return "user"
    return None


def grade_of(material_id):
    """The class of SIA 265 a `sia265:<class>` names, else None."""
    return material_id[len(GRADE_PREFIX):] if kind_of_id(material_id) == "grade" else None


def check_fields(src, fail):
    """The fields of a 1.3 source this module owns, each malformed one refused by `fail(message)` naming it (REQ-001): `material` an id of the library, never with `grade`; `loading`, `kled`, `accidental` a panel's only -- never with no material or a class of SIA 265 --, `impact` a member's only; `display` its known options. An empty field is absent: a null is refused, `material` absent following the position."""
    for key in FIELDS:
        if key in src and src[key] is None:
            fail("%s is null -- an empty field is left out of the file (absent %s)" % (key, "follows the position" if key == "material" else "is the default"))
    material = src.get("material")
    kind = None
    if material is not None:
        kind = kind_of_id(material)
        if kind is None:
            fail("material %r -- an id of the library: sia265:<class>, sia265-1:<panel>, u-<8 hex>, or absent to follow the position" % (material,))
        if src.get("grade") is not None:
            fail("grade %r and material %r are both given -- the material replaces the grade; give one" % (src["grade"], material))
        if kind == "grade" and grade_of(material) not in sia265.grades():
            fail("material %r is not a strength class of SIA 265 Tabelle 8 or 9 (%s)" % (material, ", ".join(sia265.grades())))
        if kind == "panel":
            from domains import materials_catalogue
            if materials_catalogue.find(material) is None:
                fail("material %r is not a panel of SIA 265/1 Tableaux 11 to 23" % (material,))
    for key in PANEL_FIELDS:
        if key in src and kind in (None, "grade"):
            fail("%s is given for %s -- only a panel (SIA 265/1) carries it" % (key, "a class of SIA 265" if kind == "grade" else "a check following its position"))
    if kind == "panel" and src.get("impact"):
        fail("impact is true for the panel %s -- η_t is a member's (SIA 265 2.2.6); a panel takes impacts in KLED «very short» (SIA 265/1 Tableau 8)" % material)
    loading = src.get("loading")
    if loading is not None:
        if not isinstance(loading, dict) or set(loading) != {"mode", "direction"} or loading.get("mode") not in MODES or loading.get("direction") not in DIRECTIONS:
            fail("loading is %r -- {mode: %s, direction: %s}" % (loading, " | ".join(MODES), " | ".join(DIRECTIONS)))
    if src.get("kled") is not None and src["kled"] not in KLED:
        fail("kled is %r -- %s (SIA 265/1 Tableau 7)" % (src["kled"], ", ".join(KLED)))
    if "accidental" in src and not isinstance(src["accidental"], bool):
        fail("accidental is %r -- true or false" % (src["accidental"],))
    display = src.get("display")
    if display is not None:
        if not isinstance(display, dict):
            fail("display is %r -- an object of %s" % (display, ", ".join(DISPLAY)))
        for key, value in display.items():
            if key not in DISPLAY:
                fail("display.%s is no option -- %s" % (key, ", ".join(DISPLAY)))
            if value not in DISPLAY[key] or isinstance(value, bool) != isinstance(DISPLAY[key][0], bool):
                fail("display.%s is %r -- %s" % (key, value, ", ".join(str(v) for v in DISPLAY[key])))


def carries_library(src):
    """Whether a source carries a field of 1.3 -- what `stamp_version` writes 1.3 for, the lowest version that holds it."""
    return any(key in src for key in FIELDS)


def drop_empty(src):
    """The fields of 1.3 left out where empty (REQ-001: «Reprendre» leaves no 1.3 without a reason); a panel's fields where the material is none."""
    for key in FIELDS:
        if key in src and src[key] in (None, {}):
            del src[key]
    if kind_of_id(src.get("material")) != "panel":
        for key in PANEL_FIELDS:
            src.pop(key, None)
    if "display" in src:
        kept = {k: v for k, v in src["display"].items() if DISPLAY_DEFAULT.get(k, object()) != v}
        if kept:
            src["display"] = kept
        else:
            del src["display"]
    return src


def display_of(record_or_src):
    """The options of «Affichage» of a check, every one given -- its source's over the defaults."""
    return dict(DISPLAY_DEFAULT, **((record_or_src or {}).get("display") or {}))


# --- what a check reads --------------------------------------------------------------------

def needs(kind, alpha=0, variant=None, normal=0.0, case=None, larger=False, compressed=False):
    """The quantities a check reads of its material, in the order its rows read them (REQ-005): `normal` a bending's signed normal force (tension positive), `compressed` a lateral torsional buckling with a compression."""
    out = []
    if kind == "tension":
        out = ["f_t_0"] if alpha == 0 else ["f_t_90"] if alpha == 90 else ["f_t_0", "f_t_90"]
    elif kind == "compression":
        out = ["f_c_0"] if alpha == 0 else ["f_c_90"] if alpha == 90 else ["f_c_90", "f_c_0"]
    elif kind == "bending":
        out = ["f_m"] + (["f_t_0"] if normal > 0 else ["f_c_0"] if normal < 0 else [])
        if alpha > 0:
            out += ["f_t_90", "f_c_90"]
    elif kind == "shear":
        variant = variant or "shear"
        out = ["f_v"] + (["k_a"] if variant == "shear-off" else ["f_t_90", "f_c_90"] if variant == "shear-perp" else [])
    elif kind == "buckling":
        out = ["f_c_0", "f_c_0_k", "E_0_05", "beta_c"]
    elif kind == "lateral-torsional":
        out = ["f_m"] + (["f_t_0"] if normal > 0 else ["f_c_0"] if normal < 0 else []) + ["f_m_k", "E_0_05"] + (["f_c_0_k", "beta_c"] if compressed else [])
    return out


def needs_of(src):
    """`needs` for a source or a record."""
    force = src.get("N") or {}
    normal = force.get("value", 0) if isinstance(force, dict) else 0
    return needs(src.get("kind"), src.get("alpha", 0) or 0, src.get("variant"), normal if src.get("kind") in ("bending", "lateral-torsional") else 0,
                 src.get("case"), bool(src.get("larger")), src.get("kind") == "lateral-torsional" and normal < 0)


# --- a panel's column, by its thickness ----------------------------------------------------

def column_of(material, thickness):
    """The index of the column of a panel's table whose range of thickness (t_min, t_max] holds `thickness` -- `from_inclusive` taking its lower bound in, an open bound (None) holding everything that side --, 0 for a panel of one column, None outside every range (REQ-004, REQ-007)."""
    columns = material.get("columns") or []
    if not columns:
        return 0
    for i, c in enumerate(columns):
        low, high = c.get("t_min"), c.get("t_max")
        above = low is None or thickness > low or (c.get("from_inclusive") and thickness >= low)
        below = high is None or thickness <= high
        if above and below:
            return i
    return None


def range_text(column):
    """A column's range in words of numbers -- «10–18 mm», «≤ 13 mm», «> 5,5 mm» -- what the reason and the clause's line say."""
    low, high = column.get("t_min"), column.get("t_max")
    if low is None and high is None:
        return ""
    if low is None:
        return "≤ %s mm" % _fmt(high)
    if high is None:
        return "> %s mm" % _fmt(low)
    return "%s–%s mm" % (_fmt(low), _fmt(high))


def ranges_text(material):
    return ", ".join(range_text(c) for c in material.get("columns") or [])


# --- reading a material ----------------------------------------------------------------------

def short_name(material, lang="fr"):
    """The name the material's bubble shows: a class of SIA 265 by its id («C24»), any other by its name in `lang`."""
    if material.get("origin") == "sia265":
        return material["id"][len(GRADE_PREFIX):]
    return contract.name(material, lang)


def loading_words(loading):
    """A panel's loading as a short code the window says in its words: «plaque-par»."""
    return "%s-%s" % (loading["mode"], loading["direction"]) if loading else ""


def _panel_cell(material, quantity, loading, column):
    """(k, d) of a panel for `quantity` under `loading` in `column` -- None each where the grid has no value."""
    grid_loading, row = PANEL_ROW.get(quantity, (None, None))
    if row is None:
        return None, None
    grid_loading = grid_loading or GRID[loading["mode"]]   # f_m and f_v under the loading chosen (none in the plane, «tc»), f_t and f_c always in the plane
    direction = "all" if material.get("isotropic") else loading["direction"]
    from domains import materials_derive as derive
    return derive.cell(material, grid_loading, row + "_k", direction, column), derive.cell(material, grid_loading, row + "_d", direction, column)


def loading_value(material, quantity, loading, thickness=None):
    """The design value a panel's loading bubble shows -- the b table's, moisture class 1, KLED medium -- for `quantity`, at `thickness` (the first column where none is given), or None: a bubble without a value is greyed (UI-006)."""
    column = column_of(material, thickness) if thickness is not None else 0
    if column is None:
        return None
    k, d = _panel_cell(material, quantity, loading, column)
    if d is not None:
        return d
    from domains import materials_derive as derive
    if k is not None:
        factors = derive.panel_factors(material)
        return derive.round_tenth(factors[1] * k / factors[0]) if factors else None
    return None


def _member_values(material):
    """{key: (value, how, clause)} of a member of the engineer's own -- each design value typed, set by the norm or deduced (materials_derive.member_design), at η_w = η_t = 1 -- and the characteristic values a stability reads."""
    from domains import materials_derive as derive
    out = {}
    for quantity, strength in MEMBER_KEY.items():
        design = derive.member_design(material, strength)
        if design is not None:
            clause = design.params.get("clause") if design.how == "set" else "2.2.2" if design.how == "deduced" else ""
            out[quantity] = {"value": design.value, "how": design.how, "clause": clause}
    values = material.get("values") or {}
    for key in ("f_m_k", "f_c_0_k"):
        if isinstance(values.get(key), (int, float)) and not isinstance(values.get(key), bool):
            out[key] = {"value": values[key], "how": "typed", "clause": ""}
    return out


FAMILY_WORDS = {"softwood": "Vollholz", "hardwood": "Vollholz", "glulam": "Brettschichtholz"}


def _source_ref(material):
    source = material.get("source") or {}
    return source.get("ref") or source.get("url") or ""


def resistance(material, src, section, moisture, lang="fr"):
    """What `resolve` freezes into the record of a check whose material is not a class of SIA 265 (ARCH-008), and why it cannot be calculated: (resistance, Refusal or None, notes). `src` gives the kind, the angle, the force, the loading and the factors; `section` the resolved section; `moisture` the moisture class. Notes are (code, params) said in orange."""
    name = contract.name(material, "en")
    notes = []
    kind = src["kind"]
    wanted = needs_of(src)
    if material.get("type") == "member":
        values = _member_values(material)
        family = material.get("family")
        out = {"type": "member", "family": FAMILY_WORDS.get(family), "glulam": family == "glulam", "values": values,
               "norm": _source_ref(material) or contract.name(material, "de")}
        case = src.get("case") or "generell"
        missing = []
        for q in wanted:
            if q == "k_a" or q == "beta_c":
                if family not in FAMILY_WORDS:
                    missing.append(q)
            elif q == "E_0_05":
                missing.append(q)   # the library carries no E_0,05, and a modulus is never deduced (issue #110): no stability of a member of one's own
            elif q == "f_c_90" and kind == "compression" and (case != "generell" or src.get("larger")):
                missing.append(q)   # the engineer's member gives f_c,90,d «generell» alone
            elif q not in values:
                missing.append(q)
        if missing:
            return out, _lacks(material, None, kind, missing), notes
        return out, None, notes
    if material.get("type") != "panel":
        return None, Refusal("not_resistant", {"material": name}, "%s gives no resistance -- a weight only; choose a member or a panel" % name), notes
    # a panel: its loading, the thickness the smallest side of the section, its column, its factors
    loading = src.get("loading") or {"mode": "plaque", "direction": "par"}
    if section is None or section.get("type") != "rec":
        return None, Refusal("panel_round", {"material": name}, "%s is a panel -- it is checked on a rectangular section, b × h" % name), notes
    thickness = min(section["b"], section["h"])
    column = column_of(material, thickness)
    if column is None:
        ranges = ranges_text(material)
        return None, Refusal("thickness_out", {"material": name, "thickness": _fmt(thickness), "ranges": ranges},
                             "%s is %s mm thick, the smallest side of the section -- SIA 265/1 gives its values for %s" % (name, _fmt(thickness), ranges)), notes
    expected = {"plaque": "h", "voile": "b"}.get(loading["mode"])
    if expected and section["b"] != section["h"] and section[expected] != thickness:
        notes.append(("panel_side", {"material": name, "thickness": _fmt(thickness), "side": "b" if expected == "h" else "h", "expected": expected, "mode": loading["mode"]}))
    product = material.get("product")
    kled = src.get("kled") or DEFAULT_KLED
    accidental = bool(src.get("accidental"))
    default = moisture == DEFAULT_CLASS and kled == DEFAULT_KLED and not accidental
    if product in sia265_1.products():
        if moisture not in sia265_1.admitted_classes(product) or kled not in sia265_1.admitted_kled(product, moisture):
            classes = ", ".join(str(c) for c in sia265_1.admitted_classes(product))
            return None, Refusal("class_not_admitted", {"material": name, "moisture": moisture, "classes": classes, "kled": kled},
                                 "SIA 265/1 Tableau 9 does not admit %s in moisture class %s for KLED %s -- it admits class %s" % (name, moisture, kled, classes)), notes
        eta_mod = sia265_1.eta_mod(product, moisture, kled)
        gamma_m = sia265_1.design_gamma_m(product, accidental)
        eta_ref, gamma_ref = sia265_1.eta_mod(product), sia265_1.product_gamma_m(product)
    elif default:
        eta_mod = gamma_m = eta_ref = gamma_ref = None
    else:
        return None, Refusal("panel_no_product", {"material": name},
                             "%s names no product of SIA 265/1 Tableau 9 -- its design values hold for moisture class 1, KLED medium and a normal situation only" % name), notes
    columns = material.get("columns") or []
    values = {}
    for q in ("f_m", "f_v", "f_t_0", "f_c_0"):
        k, d = _panel_cell(material, q, loading, column)
        if k is None and d is None:
            continue
        if default and d is None and eta_ref is not None:
            from domains import materials_derive as derive
            d = derive.round_tenth(eta_ref * k / gamma_ref)   # a panel of one's own with f_k alone: its b value as the Materials tab deduces it
        if default and d is None:
            continue
        entry = {"k": k, "d": d}
        if not default and k is None:
            entry["k"] = d * gamma_ref / eta_ref   # a panel of one's own with a design value alone: its characteristic value as the b table's rule gives it back (D-23)
            entry["scaled"] = True
        values[q] = entry
    stored = material.get("stored") or ""
    table = None
    found = re.search(r"tab(\d+)", stored)
    if found:
        table = str(int(found.group(1)))
    out = {"type": "panel", "product": product, "mode": loading["mode"], "direction": loading["direction"], "thickness": thickness,
           "column": column, "range": range_text(columns[column]) if columns else "", "ranges": ranges_text(material),
           "moisture_class": moisture, "kled": kled, "accidental": accidental, "default": default,
           "eta_mod": eta_mod, "gamma_m": gamma_m, "table": table, "page": _page_of(material), "values": values,
           "norm": PANEL_NORM if material.get("origin") == "sia265-1" else (_source_ref(material) or contract.name(material, "de"))}
    missing = [q for q in wanted if q not in values]
    if missing:
        return out, _lacks(material, loading, kind, missing), notes
    return out, None, notes


def _page_of(material):
    found = re.search(r"p\. (\d+)", (material.get("source") or {}).get("ref") or "")
    return int(found.group(1)) if found else None


def _lacks(material, loading, kind, missing):
    """The refusal of T39: the material (and the loading of a panel) gives not every resistance of the check -- naming what it lacks."""
    name = contract.name(material, "en")
    said = ", ".join(SYMBOLS[q] for q in missing)
    params = {"material": name, "loading": loading_words(loading), "kind": kind, "missing": said}
    return Refusal("material_lacks", params, "%s%s gives not every resistance of this check (%s): %s missing -- choose a member or another loading, or complete it in the Materials tab"
                   % (name, " under %s" % loading_words(loading) if loading else "", kind, said))


def grade_refusal(grade, kind):
    """What a class of SIA 265 cannot do that a check asks: nothing today -- every class gives Tabellen 8, 9 and Anhang B. Kept so that a reason of the material is one code for every material."""
    return None


def fire_refusal(material):
    """REQ-016: SIA 265 4.5 is applied in this lot to the classes of SIA 265 alone -- a panel or a member of one's own in the fire situation is not calculable."""
    name = contract.name(material, "en")
    return Refusal("fire_material", {"material": name}, "%s -- the fire situation (SIA 265 4.5.2) is checked here for a class of SIA 265 Tabelle 8 or 9 only" % name)


def unknown_refusal(material_id):
    return Refusal("unknown_material", {"material": material_id},
                   "material %s is neither shipped by Woodcore, nor in the project's copies, nor in your library -- choose another material" % material_id)


# --- the factors and the design values, as compute writes them -----------------------------------------------

class Strengths:
    """What `member_check._compute_section` reads of a record's material: `row` -- the values its arithmetic reads, in the shape of a row of SIA 265 Tabelle 8 or 9 --, `factor_rows` (η_w, η_t; or η_mod, γ_M), `design(key, symbol, value, label)` giving a design value and its line, `bending(axis, k_h)` a f_m,y,d / f_m,z,d, `family` and `glulam`. A class of SIA 265 reads exactly as compute always did: the table's value times η_w · η_t, the same floating-point products in the same order (CON-002)."""

    def __init__(self, record, k_fi=1.0):
        self.record = record
        self.k_fi = k_fi
        self.fire = k_fi != 1.0
        res = record.get("resistance")
        self.res = res
        self.kind = "grade" if res is None else res["type"]
        if self.kind == "grade":
            self._grade()
        elif self.kind == "member":
            self._member()
        else:
            self._panel()

    # a class of SIA 265: compute's arithmetic, as it was
    def _grade(self):
        record = self.record
        self.row = sia265.grade(record["grade"])
        self.eta_w = sia265.eta_w(record["moisture_class"], "resistance")
        self.eta_t = sia265.eta_t(bool(record.get("impact")))
        self.factor_rows = [_row("eta_w", "eta_w", self.eta_w, "", label="Feuchteklasse %d" % record["moisture_class"], clause="Tabelle 4"),
                            _row("eta_t", "eta_t", self.eta_t, "", clause="2.2.6")]
        self.factor = self.k_fi * self.eta_w * self.eta_t
        self.tab_ref = "Tabelle %s" % sia265.grade_table(record["grade"])
        self.family = "Brettschichtholz" if record["grade"] in {g["id"] for g in sia265.table_9()["grades"]} else "Vollholz"
        self.glulam = self.family == "Brettschichtholz"

    def _bar_design(self, key, symbol, table_value, label=None, clause=None, norm=NORM, table_word="Tab"):
        value = self.k_fi * self.eta_w * self.eta_t * table_value
        # the table's own value, a var of the unfolded file (`table`): Tabelle 8/9 gives design values, which eta_w and eta_t then multiply (SIA 265 2.2.2, 3.3.2.1)
        clause = self.tab_ref if clause is None else clause
        table = _row(key + "_tab", symbol[:-1] + ",\"%s\")" % table_word if symbol.endswith(")") else symbol + "_\"%s\"" % table_word, table_value, "N/mm²", clause=clause, norm=norm)
        return value, _row(key, symbol, value, "N/mm²", "%seta_w dot eta_t dot %s" % ("k_(fi) dot " if self.fire else "", _fmt(table_value)), label,
                           keys="%seta_w dot eta_t dot %s" % ("k_fi dot " if self.fire else "", table.key), clause=clause, table=table, norm=norm)

    # a member of the engineer's own: its design values at η_w = η_t = 1, then the same factors as a class
    def _member(self):
        record, res = self.record, self.res
        self.eta_w = sia265.eta_w(record["moisture_class"], "resistance")
        self.eta_t = sia265.eta_t(bool(record.get("impact")))
        self.factor_rows = [_row("eta_w", "eta_w", self.eta_w, "", label="Feuchteklasse %d" % record["moisture_class"], clause="Tabelle 4"),
                            _row("eta_t", "eta_t", self.eta_t, "", clause="2.2.6")]
        self.factor = self.k_fi * self.eta_w * self.eta_t
        values = res["values"]
        self.row = {"f_%s_d" % MEMBER_KEY[q]: v["value"] for q, v in values.items() if q in MEMBER_KEY}
        if "f_c_90" in values:
            self.row["f_c_90_d"] = {"generell": values["f_c_90"]["value"]}
        if "f_m_k" in values:
            self.row["f_m_k"] = values["f_m_k"]["value"]
        self.family = res.get("family")
        self.glulam = bool(res.get("glulam"))
        self.tab_ref = ""

    def _member_design(self, key, symbol, table_value, label=None):
        quantity = next((q for q, s in MEMBER_KEY.items() if key == "f_%s_d" % s), None)
        how = (self.res["values"].get(quantity) or {}) if quantity else {}
        words = {"typed": "eingegeben", "set": "von der Norm festgelegt", "deduced": "abgeleitet"}.get(how.get("how"), "")
        clause = how.get("clause") or ""
        norm = NORM if clause else self.res["norm"]
        return self._bar_design(key, symbol, table_value, label or words or None, clause=clause, norm=norm, table_word="Mat")

    # a panel: η_mod and γ_M of SIA 265/1
    def _panel(self):
        res = self.res
        self.default = bool(res.get("default"))
        self.eta_mod, self.gamma_m = res.get("eta_mod"), res.get("gamma_m")
        self.factor_rows = []
        if self.eta_mod is not None:
            kled_word = {"permanent": "ständig", "long": "lang", "medium": "mittel", "short": "kurz", "very_short": "sehr kurz"}[res["kled"]]
            self.factor_rows = [_row("eta_mod", "eta_(mod)", self.eta_mod, "", label="Feuchteklasse %d, KLED %s" % (res["moisture_class"], kled_word), clause="Tableau 9", norm=PANEL_NORM),
                                _row("gamma_M", "gamma_M", self.gamma_m, "", label="aussergewöhnlich" if res.get("accidental") else None, clause="Tableau 6", norm=PANEL_NORM)]
        self.factor = 1.0
        self.row = {}
        for q, entry in res["values"].items():
            self.row["f_%s_d" % MEMBER_KEY[q]] = entry["d"] if self.default else entry["k"]
        self.family = None
        self.glulam = False
        table = res.get("table")
        self.tab_ref = ("Tableau %sb" % table) if table else ""

    def _panel_design(self, key, symbol, value, label=None):
        res = self.res
        label = label or res.get("range") or None
        if self.default:
            return value, _row(key, symbol, value, "N/mm²", label=label, clause=self.tab_ref, norm=res["norm"])
        f = self.eta_mod * value / self.gamma_m
        return f, _row(key, symbol, f, "N/mm²", "eta_(mod) dot %s / gamma_M" % _fmt(value), label, clause="6.1.2.1 (5)", norm=PANEL_NORM)

    def design(self, key, symbol, table_value, label=None):
        """(design value, its line) of `key` from `table_value` -- compute's `design`."""
        if self.kind == "grade":
            return self._bar_design(key, symbol, table_value, label)
        if self.kind == "member":
            return self._member_design(key, symbol, table_value, label)
        return self._panel_design(key, symbol, table_value, label)

    def bending(self, axis, k_h):
        """(f_m,<axis>,d, its formula) -- `_bending_values`' arithmetic: a class's or a member's k_h · η_w · η_t · f_m,d; a panel's f_m,d of the b table, or η_mod · f_m,k / γ_M."""
        f_m_d = self.row["f_m_d"]
        if self.kind == "panel":
            if self.default:
                return f_m_d, None
            return self.eta_mod * f_m_d / self.gamma_m, "eta_(mod) dot %s / gamma_M" % _fmt(f_m_d)
        value = k_h * self.factor * f_m_d
        formula = "%s%seta_w dot eta_t dot %s" % ("k_(fi) dot " if self.fire else "", "k_(h,%s) dot " % axis if k_h != 1 else "", _fmt(f_m_d))
        return value, formula

    def bending_clause(self):
        """The clause and norm a f_m,<axis>,d line cites -- a panel's table (b) or 6.1.2.1; nothing for a class, as before."""
        if self.kind != "panel":
            return None, NORM, None
        return (self.tab_ref if self.default else "6.1.2.1 (5)"), (self.res["norm"] if self.default else PANEL_NORM), self.res.get("range") or None


# --- the menu of the library, for a tab (UI-005) ---------------------------------------------------

GROUPS = ("solid", "glulam", "panel", "user", "other")


def group_of(material):
    """The group of the menu a material is listed in: solid timber (SIA 265 Tabelle 8), glulam (Tabelle 9), panels (SIA 265/1), the engineer's own, the materials without resistance (a weight only, greyed)."""
    if material.get("type") == "other":
        return "other"
    if not material.get("origin"):
        return "user"
    if material.get("type") == "panel":
        return "panel"
    return "glulam" if material.get("family") == "glulam" else "solid"


def offered(tab, materials, query="", lang="fr"):
    """The menu of the library in the tab `tab` (tension, compression, bending, shear): [(group, [entry])] in `GROUPS`' order, each entry {id, name, short, group, values, source, selectable, lacks} -- `values` the resistance the tab reads, [(loading, value)] for a panel by its loading bubbles (T35) or [(None, value)] for a member; `lacks` where the material gives none of it. `materials` is what the library lists (materials_library.entries), `query` filters by the words of `materials_search.search`."""
    from domains import materials_derive as derive, materials_search
    quantity = TAB_QUANTITY[tab]
    found = materials_search.search(materials, query) if query else list(materials)
    out = {g: [] for g in GROUPS}
    for m in found:
        group = group_of(m)
        entry = {"id": m["id"], "name": contract.name(m, lang), "short": short_name(m, lang), "group": group, "values": [], "selectable": group != "other",
                 "source": m.get("origin") or "user", "lacks": False}
        if m.get("type") == "member":
            if m.get("origin") == "sia265":
                grade = sia265.grade(grade_of(m["id"]))
                value = grade["f_%s_d" % MEMBER_KEY[quantity]]
                value = value.get("generell") if isinstance(value, dict) else value
            else:
                design = derive.member_design(m, MEMBER_KEY[quantity])
                value = design.value if design else None
            entry["values"] = [(None, value)]
            entry["lacks"] = value is None
        elif m.get("type") == "panel":
            entry["values"] = [((mode, direction), loading_value(m, quantity, {"mode": mode, "direction": direction})) for mode, direction in TAB_LOADINGS[tab]]
            entry["lacks"] = all(v is None for _l, v in entry["values"])
        out[group].append(entry)
    return [(g, out[g]) for g in GROUPS if out[g]]


def usable_in_checks(material):
    """REQ-012: whether a material is offered with a value in the member checks -- a member of one's own complete in what every tab reads (f_m, f_t,0, f_c,0, f_v), a panel giving one tab's resistance at least."""
    from domains import materials_derive as derive
    if material.get("type") == "member":
        return all(derive.member_design(material, MEMBER_KEY[q]) is not None for q in TAB_QUANTITY.values())
    if material.get("type") == "panel":
        return any(loading_value(material, TAB_QUANTITY[tab], {"mode": mode, "direction": direction}) is not None
                   for tab, loadings in TAB_LOADINGS.items() for mode, direction in loadings)
    return False
