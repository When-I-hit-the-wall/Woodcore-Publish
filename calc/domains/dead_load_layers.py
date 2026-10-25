"""The layers of a build-up of permanent loads, computed (spec docs/requirements/completed/2026-10-24-poids-propre-repense.md, REQ-003 to REQ-006, ARCH-006; issue #111).

**A layer** (dead-load-source 2.0) has a `pose`:

* `continuous` -- a board, a screed, a full insulation: γ · t;
* `spaced` -- battens, rafters, joists, pieces `width` b wide every `spacing` e: γ · t · b / e;
* `surface` -- tiles, membranes, sheets weighed per m² (SIA 261 Tabelle 29): γ, the thickness for the drawing alone;
* `typed` -- services, partitions: no material, the load typed (`load`).

**A level.** A layer `link`ed to the one below shares its level: **two lines at most** (D-07, the engineer, 24.10.2026: «il ne peut y avoir que deux matériaux sur une même couche») -- one spaced, one that fills the gap the pieces leave on 1 m, w = 1000 · (1 − b/e) mm (`fill`, the default), or a width written (`fill` false; 1000 where none is). The thicker gives the level's height. **A load written** on a layer of any pose (`load`, or `links.load` to a variable) replaces its calculation in the sum -- the report prints it without a mark (ARCH-006).

**The retained value** (REQ-005): written, or else the tenth above or equal to the sum -- 0.909 → 1.0, 0.900 → 0.9 (`retained`).

The roles a layer may take are `ROLES`, written once. kg go to kN with g = 10 m/s². No Qt here.
"""

import math

from domains import materials

POSES = ("continuous", "spaced", "surface", "typed")
# What a layer is for, optional and apart from its material (T16, T54), in the order the pane lists them; their words are `ld_role_<id>`
ROLES = ("structure", "insulation", "roofing", "underlay", "counter_battens", "roof_battens", "battens", "boarding", "vapour_barrier", "waterproofing",
         "protection", "ballast", "screed", "impact_insulation", "floor_finish", "bracing_panel", "lining", "facade", "facade_membrane", "underlay_membrane")
# The battens the tiles of SIA 261 Tabelle 29 «inkl. Lattung» already carry: a layer of these roles under them counts them a second time (T34, Q-006)
BATTEN_ROLES = ("roof_battens", "counter_battens")
# The width a level is computed on, mm
STRIP = 1000.0
# A sum on a tenth stays on it: 0.900 retains 0.9, not 1.0 (T36), floats read back notwithstanding
_TENTH_TOLERANCE = 1e-9


def retained(total):
    """The tenth above or equal to `total`, kN/m² (REQ-005): 0.909 → 1.0, 0.900 → 0.9, 0.901 → 1.0."""
    return math.ceil(round(total * 10, 9) - _TENTH_TOLERANCE) / 10.0 if total > 0 else 0.0


def levels(layers):
    """The levels of a build-up, top to bottom: [[index] or [index, index+1]] -- a layer `link`ed to the one below shares its level. A link on the last layer, or a third layer on a level, is said by `level_problems` and read here as no link."""
    out, i = [], 0
    while i < len(layers):
        if layers[i].get("link") and i + 1 < len(layers) and not layers[i + 1].get("link"):
            out.append([i, i + 1])
            i += 2
        else:
            out.append([i])
            i += 1
    return out


def level_problems(layers):
    """[(index, code)] of the links the rule of two refuses: a third layer on a level (`level_three`), a level of two spaced or two filling layers (`level_two_spaced`, `level_two_fill`)."""
    out = []
    for i, layer in enumerate(layers):
        if layer.get("link") and i + 1 < len(layers) and layers[i + 1].get("link"):
            out.append((i + 1, "level_three"))
    for level in levels(layers):
        if len(level) == 2:
            a, b = (layers[j] for j in level)
            if a.get("pose") == "spaced" and b.get("pose") == "spaced":
                out.append((level[1], "level_two_spaced"))
            elif a.get("pose") != "spaced" and b.get("pose") != "spaced" and a.get("pose") != "typed" and b.get("pose") != "typed":
                out.append((level[1], "level_two_fill"))
    return out


def share(layer):
    """b/e of a spaced layer, 0 for another."""
    if layer.get("pose") == "spaced" and _num(layer.get("width")) and _num(layer.get("spacing")):
        return layer["width"] / layer["spacing"]
    return 0.0


def fill_width(layers, index):
    """(width in mm over 1 m, whether it was computed) of a non-spaced layer: on a level with a spaced one and `fill` (the default), what the pieces leave, 1000 · (1 − b/e), never below 0; `fill` false, its width written, 1000 where none is; alone on its level, 1000."""
    layer = layers[index]
    level = next(lv for lv in levels(layers) if index in lv)
    partner = [layers[j] for j in level if j != index]
    if layer.get("pose") in ("spaced", "typed"):
        return None, False
    if partner and partner[0].get("pose") == "spaced" and layer.get("fill", True):
        return max(0.0, STRIP * (1.0 - share(partner[0]))), True
    if partner and not layer.get("fill", True):
        return (_num(layer.get("width")) or STRIP), False
    return STRIP, False


def air(layers, index):
    """mm of air above a filling layer thinner than the pieces beside it (T18), 0 where there is none."""
    level = next(lv for lv in levels(layers) if index in lv)
    if len(level) < 2 or layers[index].get("pose") == "spaced":
        return 0.0
    pieces = [layers[j] for j in level if j != index and layers[j].get("pose") == "spaced"]
    if not pieces:
        return 0.0
    return max(0.0, (_num(pieces[0].get("thickness")) or 0.0) - (_num(layers[index].get("thickness")) or 0.0))


def _num(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def pose_for(unit, layer):
    """The pose a material's unit asks (T40): a weight per surface makes the line «surface»; a weight per volume on a «surface» line makes it «continuous» again; otherwise the pose stays."""
    if unit in materials.SURFACE_UNITS:
        return "surface"
    if layer.get("pose") == "surface":
        return "continuous"
    return layer.get("pose") or "continuous"


def computed_load(layer, weight, unit, width_mm=None):
    """(load in kN/m², its numbers {gamma, t, b, e, w}) of a layer weighed `weight` `unit`, by its pose -- None where a number it needs is missing. `width_mm` is the filling width (`fill_width`)."""
    pose = layer.get("pose")
    if pose == "typed":
        load = _num(layer.get("load"))
        return (load, {}) if load is not None else (None, {})
    gamma = materials.to_kn(weight, unit)
    if pose == "surface" or not materials.per_volume(unit):
        return gamma, {"gamma": gamma}
    t = _num(layer.get("thickness"))
    if t is None:
        return None, {"gamma": gamma}
    if pose == "spaced":
        b, e = _num(layer.get("width")), _num(layer.get("spacing"))
        if b is None or e is None:
            return None, {"gamma": gamma, "t": t}
        return gamma * t / 1000.0 * b / e, {"gamma": gamma, "t": t, "b": b, "e": e}
    w = width_mm if width_mm is not None else STRIP
    return gamma * t / 1000.0 * w / STRIP, {"gamma": gamma, "t": t, "w": w}


def formula(numbers, load):
    """The layer's load written in numbers, as the pane shows it (T54): «5 kN/m³ × 0.2 m × 60/625 = 0.096 kN/m²»."""
    if not numbers or load is None:
        return ""
    n = lambda v: ("%.3f" % v).rstrip("0").rstrip(".") if isinstance(v, float) else str(v)
    if "t" not in numbers:
        return "%s kN/m²" % n(numbers["gamma"])
    parts = ["%s kN/m³" % n(numbers["gamma"]), "%s m" % n(numbers["t"] / 1000.0)]
    if "b" in numbers:
        parts.append("%s/%s" % (n(numbers["b"]), n(numbers["e"])))
    elif numbers.get("w") not in (None, STRIP):
        parts.append("%s/1000" % n(numbers["w"]))
    return "%s = %s kN/m²" % (" × ".join(parts), ("%.3f" % load))


def contributions(rows):
    """What each layer weighs in the sum (REQ-008, T11): {"gk", "ak", "all"} -- g_k alone, a_k alone, the two -- each [{number, label, load, share}] in the order of the layers, `share` the part of its list's total (0 where the total is 0), and their totals {"gk", "ak", "all"}. `rows` are dead_load_source.layer_rows'."""
    out, totals = {}, {}
    for key, kinds in (("gk", ("gk",)), ("ak", ("ak",)), ("all", ("gk", "ak"))):
        chosen = [r for r in rows if r["kind"] in kinds]
        total = sum(r["load"] for r in chosen)
        totals[key] = total
        out[key] = [{"number": r["number"], "label": r["label"], "load": r["load"], "share": r["load"] / total if total else 0.0} for r in chosen]
    return out, totals

