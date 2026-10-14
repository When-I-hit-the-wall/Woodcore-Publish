"""A free steel profile: rectangles drawn or typed in the «Profilés» tab, and the section values computed from them (issue #50, spec 2026-10-12-section-acier REQ-003, D-03, D-10, D-11, D-12, D-16; docs/domain/steel.md).

**Source.** `Woodcore-Datei/profiles/<id>.json` (`Project.profiles_dir`), one file per profile, schema `profile-source` 1.0 (schemas/profile-source.schema.json): its `id` (the file name), optional `name`, `label` and `group`, the `unit` (mm, the one unit of every length), an optional `template` -- the model it was loaded from, `{kind, params}` or `{c5: "HEA 200"}`, kept as provenance and never read back as a value -- and its `parts`, each a rectangle `{name, y, z, b, h, role}`: (y, z) its lower left corner, y to the right and z upwards, b its width along y and h its height along z. A position names it by the section type `USR` and the profile's id as its dimension (calc/domains/section.py); a profile a position cites can be neither renamed nor deleted (D-16, `cited_by`).

**The method** is the one of the course's `Querschnittsrechner.py` (F. Graber, BFH StahlBetonBau1 HS26), written again here rather than copied: the area and the centroid as sums over the parts, I_y and I_z with Steiner's term, W_el about each axis at its farther fibre, the plastic neutral axes as the lines that halve the area -- found exactly, the area below a line being linear between the parts' edges -- and W_pl as the first moment of the two halves about them. Nothing here is a norm's value: a rectangle's mechanics. Root radii are not drawn (D-10): a profile loaded from SZS C5 has a little less area and inertia than the book's row, and says so.

**The walls** (D-11). Each rectangle carries a role -- `internal` (a plate held on both long edges: a web, a tube's wall), `outstand` (held on one: half a flange), or `none` (a junction, or a part not checked) -- which a template sets and the engineer may change. `walls(parts)` gives each wall's c (its long side) and t (its short side): what Tabelle 5 of SIA 263 classifies (domains/steel_section.py).
"""

import json
import math
import re
from pathlib import Path

import project
import validation

SOURCE_SCHEMA = "profile-source"
SOURCE_SCHEMA_VERSION = "1.0"
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$")
UNIT = "mm"

# The role of a rectangle in the section class (D-11). Held equal to schemas/profile-source.schema.json by tests/test_steel_free_profile.py.
ROLES = ("internal", "outstand", "none")

# The models a free profile starts from, each with the numbers it is drawn from (mm), in the order a form asks them.
TEMPLATES = {
    "I": ("h", "b", "t_w", "t_f"),
    "U": ("h", "b", "t_w", "t_f"),
    "T": ("h", "b", "t_w", "t_f"),
    "L": ("a", "b", "t"),
    "RHS": ("h", "b", "t"),
    "plate": ("b", "t"),
}

# Which model an SZS C5 family is drawn as. RND and ROR are round, which rectangles do not draw (D-10).
C5_TEMPLATES = {
    "IPE": "I", "IPEA": "I", "IPN": "I", "HEA": "I", "HEB": "I", "HEM": "I", "HD": "I", "HL": "I",
    "UPE": "U", "UPN": "U", "T": "T", "IPET": "T", "HEAT": "T", "HEBT": "T", "L": "L", "RRK": "RHS", "RRW": "RHS", "VKT": "plate",
}


def _fail(where, message):
    raise validation.ValidationError("%s: %s" % (where, message))


def _number(value):
    return not isinstance(value, bool) and isinstance(value, (int, float))


# --- the models -----------------------------------------------------------------

def _part(name, y, z, b, h, role):
    return {"name": name, "y": y, "z": z, "b": b, "h": h, "role": role}


def template(kind, **params):
    """The rectangles of a model, its lower left corner at (0, 0), its roles set (D-11): an I's web internal and each half flange an outstand, the web's width of flange a junction; a channel's web internal and its flanges outstands; a T's flange halves outstands and its stem an outstand; an angle's two legs outstands; a tube's four walls internal (its corners belong to the flanges, c = h − 2t of a web, b − 2t of a flange); a plate an outstand of none. ValueError for a model or a number that does not make one."""
    if kind not in TEMPLATES:
        raise ValueError("no model %r -- the models are %s" % (kind, ", ".join(TEMPLATES)))
    missing = [p for p in TEMPLATES[kind] if not _number(params.get(p)) or params[p] <= 0]
    if missing:
        raise ValueError("%s needs %s above 0" % (kind, ", ".join(missing)))
    p = {k: float(v) for k, v in params.items()}
    if kind == "I":
        h, b, tw, tf = p["h"], p["b"], p["t_w"], p["t_f"]
        if tw >= b or 2 * tf >= h:
            raise ValueError("I: t_w must be below b and 2 t_f below h")
        c = (b - tw) / 2
        return [
            _part("Flansch unten links", 0, 0, c, tf, "outstand"), _part("Flansch unten Mitte", c, 0, tw, tf, "none"), _part("Flansch unten rechts", c + tw, 0, c, tf, "outstand"),
            _part("Steg", c, tf, tw, h - 2 * tf, "internal"),
            _part("Flansch oben links", 0, h - tf, c, tf, "outstand"), _part("Flansch oben Mitte", c, h - tf, tw, tf, "none"), _part("Flansch oben rechts", c + tw, h - tf, c, tf, "outstand"),
        ]
    if kind == "U":
        h, b, tw, tf = p["h"], p["b"], p["t_w"], p["t_f"]
        if tw >= b or 2 * tf >= h:
            raise ValueError("U: t_w must be below b and 2 t_f below h")
        return [
            _part("Steg", 0, 0, tw, h, "internal"),
            _part("Flansch unten", tw, 0, b - tw, tf, "outstand"),
            _part("Flansch oben", tw, h - tf, b - tw, tf, "outstand"),
        ]
    if kind == "T":
        h, b, tw, tf = p["h"], p["b"], p["t_w"], p["t_f"]
        if tw >= b or tf >= h:
            raise ValueError("T: t_w must be below b and t_f below h")
        c = (b - tw) / 2
        return [
            _part("Steg", c, 0, tw, h - tf, "outstand"),
            _part("Flansch links", 0, h - tf, c, tf, "outstand"), _part("Flansch Mitte", c, h - tf, tw, tf, "none"), _part("Flansch rechts", c + tw, h - tf, c, tf, "outstand"),
        ]
    if kind == "L":
        a, b, t = p["a"], p["b"], p["t"]
        if t >= min(a, b):
            raise ValueError("L: t must be below a and b")
        return [_part("Schenkel a", 0, 0, t, a, "outstand"), _part("Schenkel b", t, 0, b - t, t, "outstand")]
    if kind == "RHS":
        h, b, t = p["h"], p["b"], p["t"]
        if 2 * t >= min(h, b):
            raise ValueError("RHS: 2 t must be below h and b")
        return [
            _part("Flansch unten", 0, 0, b, t, "internal"), _part("Flansch oben", 0, h - t, b, t, "internal"),
            _part("Steg links", 0, t, t, h - 2 * t, "internal"), _part("Steg rechts", b - t, t, t, h - 2 * t, "internal"),
        ]
    return [_part("Blech", 0, 0, p["b"], p["t"], "none")]


def from_c5(code, dims):
    """The model an SZS C5 profile is drawn as, `(kind, params)`, read off its table (calc/norms/szs_c5.py) -- root radii left out (D-10) -- or None for a round one (RND, ROR) or a designation the tables do not carry."""
    from norms import szs_c5
    kind = C5_TEMPLATES.get(code)
    row = szs_c5.profile(code, dims) if kind else None
    if row is None:
        return None
    if kind in ("I", "U", "T"):
        return kind, {"h": row["h"], "b": row["b"], "t_w": row["t_w"], "t_f": row["t_f"]}
    if kind == "L":
        return kind, {"a": row["a"], "b": row["b"], "t": row["t"]}
    if kind == "RHS":
        return kind, {"h": row["h"], "b": row["b"], "t": row["t"]}
    return kind, {"b": row["b"], "t": row["h"]}


# --- the section values ---------------------------------------------------------

def _bounds(parts):
    return (min(p["y"] for p in parts), max(p["y"] + p["b"] for p in parts),
            min(p["z"] for p in parts), max(p["z"] + p["h"] for p in parts))


def _area_below(parts, axis, at):
    """The area on the lower (z) or left (y) side of a line."""
    lo, size, other = ("z", "h", "b") if axis == "z" else ("y", "b", "h")
    return sum(p[other] * min(max(at - p[lo], 0.0), p[size]) for p in parts)


def _halving(parts, axis):
    """The line that halves the area, exactly: the area below a line is linear between the parts' edges, so the crossing is found in its interval and solved."""
    lo, size = ("z", "h") if axis == "z" else ("y", "b")
    target = sum(p["b"] * p["h"] for p in parts) / 2
    edges = sorted({p[lo] for p in parts} | {p[lo] + p[size] for p in parts})
    for a, b in zip(edges, edges[1:]):
        fa, fb = _area_below(parts, axis, a), _area_below(parts, axis, b)
        if fa <= target <= fb and fb > fa:
            return a + (target - fa) / (fb - fa) * (b - a)
    return edges[0]


def _first_moment(parts, axis, at):
    """Sum of |area · distance| of each part's two sides of the line: the plastic modulus about it."""
    lo, size, other = ("z", "h", "b") if axis == "z" else ("y", "b", "h")
    total = 0.0
    for p in parts:
        below = min(max(at - p[lo], 0.0), p[size])   # the part's extent below the line, from its lower edge
        above = p[size] - below
        if below > 0:
            total += p[other] * below * (at - (p[lo] + below / 2))
        if above > 0:
            total += p[other] * above * ((p[lo] + below + above / 2) - at)
    return total


def properties(parts):
    """The section values of rectangles, in mm units: {A, y_s, z_s, I_y, I_z, W_el_y, W_el_z, W_el_y_top, W_el_y_bottom, W_el_z_right, W_el_z_left, i_y, i_z, y_pl, z_pl, W_pl_y, W_pl_z, K, h, b, t_max}.

    y is the major axis's direction only by convention: I_y is about the horizontal axis through the centroid (bending in the z direction, a beam's strong axis when it stands upright). W_el about an axis is the smaller of its two fibres'. K is the torsion constant of an open thin-walled section, the sum of c·t³/3 of its rectangles -- an approximation for the stocky part and wrong for a closed tube (`K_open: True` says which). t_max, the thickest plate, is what Tabelle 1 of SIA 263 reads its band by."""
    if not parts:
        raise ValueError("a profile needs at least one rectangle")
    A = sum(p["b"] * p["h"] for p in parts)
    if A <= 0:
        raise ValueError("a profile's area is 0")
    y_s = sum(p["b"] * p["h"] * (p["y"] + p["b"] / 2) for p in parts) / A
    z_s = sum(p["b"] * p["h"] * (p["z"] + p["h"] / 2) for p in parts) / A
    I_y = sum(p["b"] * p["h"] ** 3 / 12 + p["b"] * p["h"] * (p["z"] + p["h"] / 2 - z_s) ** 2 for p in parts)
    I_z = sum(p["h"] * p["b"] ** 3 / 12 + p["b"] * p["h"] * (p["y"] + p["b"] / 2 - y_s) ** 2 for p in parts)
    y0, y1, z0, z1 = _bounds(parts)
    top, bottom, right, left = z1 - z_s, z_s - z0, y1 - y_s, y_s - y0
    z_pl, y_pl = _halving(parts, "z"), _halving(parts, "y")
    K = sum(max(p["b"], p["h"]) * min(p["b"], p["h"]) ** 3 / 3 for p in parts)
    return {
        "A": A, "y_s": y_s, "z_s": z_s, "I_y": I_y, "I_z": I_z,
        "W_el_y_top": I_y / top, "W_el_y_bottom": I_y / bottom, "W_el_z_right": I_z / right, "W_el_z_left": I_z / left,
        "W_el_y": I_y / max(top, bottom), "W_el_z": I_z / max(right, left),
        "i_y": math.sqrt(I_y / A), "i_z": math.sqrt(I_z / A),
        "y_pl": y_pl, "z_pl": z_pl, "W_pl_y": _first_moment(parts, "z", z_pl), "W_pl_z": _first_moment(parts, "y", y_pl),
        "K": K, "K_open": True, "h": z1 - z0, "b": y1 - y0, "t_max": max(min(p["b"], p["h"]) for p in parts),
    }


def walls(parts):
    """The walls Tabelle 5 classifies: [{name, role, c, t}] of every rectangle whose role is not `none`, c its long side and t its short side."""
    return [{"name": p["name"], "role": p["role"], "c": max(p["b"], p["h"]), "t": min(p["b"], p["h"])}
            for p in parts if p["role"] != "none"]


# --- the source -------------------------------------------------------------------

def _dir(here=None):
    return (here or project.current()).profiles_dir


def source_paths(here=None):
    """Every free profile of the project, in file-name order."""
    directory = _dir(here)
    return sorted(directory.glob("*.json")) if directory.is_dir() else []


def check_source(src, where="profiles"):
    """Everything that makes a profile source malformed, as a ValidationError naming `where` and the field: the schema, an id that is no id or an SZS C5 designation's code, a unit other than mm, no part, a part whose b or h is not above 0, whose y or z is no number, whose role is none of ROLES, and two parts with one name."""
    if not isinstance(src, dict):
        _fail(where, "is not a JSON object")
    if src.get("schema") != SOURCE_SCHEMA or src.get("schema_version") != SOURCE_SCHEMA_VERSION:
        _fail(where, "schema %r %r -- expected %r %r" % (src.get("schema"), src.get("schema_version"), SOURCE_SCHEMA, SOURCE_SCHEMA_VERSION))
    pid = src.get("id")
    if not isinstance(pid, str) or not ID_PATTERN.match(pid):
        _fail(where, "id %r -- letters, digits and _ . + - only" % (pid,))
    if not is_free_id(pid):
        _fail(where, "id %r reads as an SZS C5 designation -- a free profile's id must not, a position's dimension being one or the other" % pid)
    if src.get("unit", UNIT) != UNIT:
        _fail(where, "unit %r -- a profile is drawn in mm" % (src.get("unit"),))
    parts = src.get("parts")
    if not isinstance(parts, list) or not parts:
        _fail(where, "parts: a profile needs at least one rectangle")
    names = set()
    for n, part in enumerate(parts):
        here = "%s: parts[%d]" % (where, n)
        if not isinstance(part, dict):
            _fail(here, "is not an object")
        for key in ("y", "z"):
            if not _number(part.get(key)):
                _fail(here, "%s is %r -- expected a number (mm)" % (key, part.get(key)))
        for key in ("b", "h"):
            if not _number(part.get(key)) or part[key] <= 0:
                _fail(here, "%s is %r -- expected a number above 0 (mm)" % (key, part.get(key)))
        if part.get("role") not in ROLES:
            _fail(here, "role %r -- one of %s" % (part.get("role"), ", ".join(ROLES)))
        name = part.get("name")
        if not isinstance(name, str) or not name.strip():
            _fail(here, "has no name")
        if name in names:
            _fail(here, "name %r is used twice" % name)
        names.add(name)
    tpl = src.get("template")
    if tpl is not None and not isinstance(tpl, dict):
        _fail(where, "template is %r -- expected the model it came from, or none" % (tpl,))
    return src


def is_free_id(pid):
    """Whether an id may name a free profile: not a designation of SZS C5 («HEA 200», «IPE200»), which a position's dimension would read as a catalogue profile."""
    from norms import szs_c5
    head = re.match(r"^([A-Za-z]+)", str(pid or ""))
    return not (head and head.group(1).upper() in szs_c5.codes() and re.match(r"^[A-Za-z]+\s*\d", str(pid)))


def read_source(path):
    """One source, read and checked; its id must be its file name."""
    path = Path(path)
    where = "profiles/%s" % path.name
    try:
        src = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _fail(where, "cannot be read as JSON -- %s" % exc)
    check_source(src, where)
    if src["id"] != path.stem:
        _fail(where, "id %r is not its file name %r -- the id is the file name" % (src["id"], path.stem))
    return src


def list_sources(here=None):
    """Every source as a dict, sorted by file name, unchecked -- what the tab lists, so one malformed file does not empty the list."""
    out = []
    for path in source_paths(here):
        try:
            src = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(src, dict):
            src.setdefault("id", path.stem)
            out.append(src)
    return out


def new_source(pid, kind="I", **params):
    """A new profile drawn from a model -- by default an I 200 × 100, web 6, flanges 10."""
    params = params or {"h": 200, "b": 100, "t_w": 6, "t_f": 10} if kind == "I" else params
    return {"schema": SOURCE_SCHEMA, "schema_version": SOURCE_SCHEMA_VERSION, "id": pid, "unit": UNIT,
            "template": {"kind": kind, "params": dict(params)}, "parts": template(kind, **params)}


def cited_by(pid, positions):
    """The ids of the positions whose section is this free profile (type USR, dimension the id, ignoring case) -- what refuses a rename or a delete (D-16). `positions` is the export's list of position records."""
    out = []
    for record in positions or ():
        section = (record or {}).get("section") or {}
        if section.get("type") == "USR" and str(section.get("id", "")).lower() == str(pid).lower():
            out.append(record.get("id"))
    return out


def resolve(pid, here=None):
    """The free profile `pid` of the project, read and checked, with its values: {"id", "source", "properties", "walls"} -- None where no such file exists (the caller warns: a missing input never stops). A malformed file stops, naming it."""
    # by the files' own names, ignoring case as a position's id does: on Windows «pr-01.json» opens PR-01.json, whose id is PR-01
    for path in source_paths(here):
        if path.stem.lower() == str(pid).lower():
            break
    else:
        return None
    src = read_source(path)
    return {"id": src["id"], "source": src, "properties": properties(src["parts"]), "walls": walls(src["parts"])}
