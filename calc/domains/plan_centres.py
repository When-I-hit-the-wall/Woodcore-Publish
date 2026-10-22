"""The stiffness centre S and the mass centre M of a storey, from what a position plan draws (issue #54, docs/domain/position-plans.md §3.3sexies; spec docs/requirements/completed/2026-10-13-plan-positions-centre-rigidite-centre-masse.md).

The engineer, 12.10.2026: «calculer et dessiner le centre de rigidité S et le centre de masse M sur le plan de positions». S is where a horizontal force moves the floor without turning it; M is where the earthquake acts; a bracing laid out symmetrically keeps the two close. Both are **derived from the drawing and stored nowhere** -- a plan's file holds what they are computed from, as it holds a dimension's points and never its value: each bracing wall's construction mode (`construction`), the power a CLT wall's length is raised to (`clt_power`), the building's outline (`outlines`) and whether the three are printed (`print_centres`).

**The method is a document and no norm** (docs/architecture/principles.md rule 7): «Centre de rigidité d'un étage — calcul mécanique général» (12.10.2026), reproduced whole in the spec's Annexe A, its sections 5 and 9 -- the barycentre of the stiffnesses, in the general form that takes walls at any angle. No SIA norm gives it: SIA 261 uses the stiffness centre as known and SIA 265 does not name it. Its assumptions are the document's (section 2): a floor rigid in its plane, walls linear elastic that carry forces in their own plane only, one storey at a time. What it leaves out is said in section 12 -- a flexible floor, several storeys, cores whose wings work together.

**A wall's stiffness is its length to a power, and only the ratios count** (the engineer, issue #54; the document's section 4): 1 for timber frame, 1.5 or 2 for CLT as the engineer chooses on the plan, 3 for concrete. S is therefore computed in the sheet's own units, on a plan without a scale as on one with -- and only where every wall taken is built the same way, the power being no measure between two constructions.

Qt-free, and no file: Woodcore's window, the drawing (plan_svg.py) and the export (plan.py) all ask `state()`, so the three cannot come to place S differently.
"""

import math

import engine
from domains.plan_geometry import _point_segment, bbox, centroid, ring_area

# What every result of this module says it came from (rule 5), and the method it followed (rule 7): a document, cited whole with its sections, and no norm.
SOURCE = "python:domains/plan_centres.py"
REFERENCE = "Centre de rigidité d'un étage — calcul mécanique général (12.10.2026), sections 5 et 9"

# The elements that brace: a bracing wall (H) and a wall that bears and braces (W). A bearing wall (V) and a concrete wall drawn as an area (B «wand») do not count (the engineer, issue #54).
WALL_TYPES = ("H", "W")

# How a wall is built, and the powers its length may be raised to for its stiffness -- said here once; the schema's enums are held equal to it by tests/test_constants.py. One power: the mode fixes it. Two: the engineer chooses, on the plan (`clt_power`).
POWERS = {"timber_frame": (1.0,), "clt": (1.5, 2.0), "concrete": (3.0,)}
MODES = tuple(POWERS)

# Two directions closer than this are one direction: what tells a straight wall drawn through an intermediate point from a wall that turns a corner, and a storey braced one way only from one braced both ways. Half a degree is far above what rounding a point to a hundredth of a sheet unit turns a wall by, and far below any corner an engineer draws.
ALIGNED_DEG = 0.5

# Lines of action that all pass within this share of the walls' extent of one point pass through it: the storey then has no torsional stiffness. Relative, never an absolute length -- the sheet's units are points, pixels or hundredths of a millimetre.
CONCURRENT = 1e-4

# An outline whose area is under this share of its bounding box's diagonal squared encloses nothing: three points on a line.
FLAT = 1e-9


def applies(source):
    """Whether a plan has a stiffness centre at all: a floor plan and a load-path plan do, an elevation section does not -- it shows storeys, not a storey's walls in plan. A section is the one plan whose role is `section` (plan.check_source holds `plan_type` to it)."""
    return source.get("role", "plan") != "section"


def uses_centres(source):
    """Whether a plan carries anything of this module -- a wall's construction mode, an outline, the CLT power or the printing switch --, which is what makes its file a 1.8 one (plan.version_of)."""
    if source.get("outlines") or "clt_power" in source or "print_centres" in source:
        return True
    return any("construction" in element for element in source.get("elements") or [])


def check(source, fail):
    """What a source must satisfy to state this module's fields, each failure handed to `fail(message)` -- plan.check_source's, which names the file: a construction mode of MODES and on a bracing wall only, one outline at most, of three distinct points at least, with no sizes of its own and on no elevation section, a CLT power of the two, a switch that is true or false."""
    for i, element in enumerate(source.get("elements") or [], start=1):
        if "construction" not in element:
            continue
        at = f"element {i} ({element.get('type')})"
        if element.get("type") not in WALL_TYPES:
            fail(f"{at} carries no construction mode -- construction is for the bracing walls, {', '.join(WALL_TYPES)}")
        if element["construction"] not in MODES:
            fail(f"{at}: construction is {element['construction']!r} -- expected one of {', '.join(MODES)}")
    outlines = source.get("outlines", [])
    if not isinstance(outlines, list):
        fail("outlines is not a list")
    if len(outlines) > 1:
        fail(f"a plan has one building outline, got {len(outlines)}")
    if outlines and not applies(source):
        fail("a building outline is drawn on a floor plan -- set the plan's type to floor plan, or take it out")
    for i, outline in enumerate(outlines, start=1):
        at = f"outline {i}"
        if not isinstance(outline, dict):
            fail(f"{at} is not an object")
        points = outline.get("points")
        if not isinstance(points, list) or len(points) < 3:
            fail(f"{at} is an area and needs three points at least, got {points!r}")
        for j, p in enumerate(points, start=1):
            if not (isinstance(p, list) and len(p) == 2 and all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in p)):
                fail(f"{at}: point {j} must be two numbers, got {p!r}")
        for j in range(len(points)):
            if math.dist(points[j - 1], points[j]) <= 1e-6:
                fail(f"{at}: points {j or len(points)} and {j + 1} are the same point")
        if "style" in outline:
            fail(f"{at} follows the plan's own sizes and states none of its own, got a style")
    if "clt_power" in source and (isinstance(source["clt_power"], bool) or source["clt_power"] not in POWERS["clt"]):
        fail(f"clt_power is {source['clt_power']!r} -- expected {' or '.join(str(p) for p in POWERS['clt'])}")
    if "print_centres" in source and not isinstance(source["print_centres"], bool):
        fail(f"print_centres must be true or false, got {source['print_centres']!r}")


def hit_outline(source, point, tolerance):
    """The index of the outline whose **edge** passes within `tolerance` of `point`, or None. An outline is taken by its line and never by its inside: it runs round the whole building, so a click in the middle of it is a click on what stands there, or on nothing -- where a slab, an area too, is taken by its inside (plan_geometry.hit_element)."""
    for index, outline in enumerate(source.get("outlines") or []):
        points = outline.get("points") or []
        if len(points) >= 2 and any(_point_segment(point, points[j - 1], points[j])[0] <= tolerance for j in range(len(points))):
            return index
    return None


def power_of(source, mode):
    """The power a wall's length is raised to for its stiffness: its mode's own, or for CLT the one the plan states -- None while the engineer has not chosen it."""
    powers = POWERS[mode]
    if len(powers) == 1:
        return powers[0]
    stated = source.get("clt_power")
    return float(stated) if stated in powers and not isinstance(stated, bool) else None


def _direction(a, b):
    d = math.dist(a, b)
    return (b[0] - a[0]) / d, (b[1] - a[1]) / d


def _same_direction(u, v, sense=False):
    """Whether two unit vectors lie along one line, within ALIGNED_DEG -- and point the same way, where `sense` asks it."""
    aligned = abs(u[0] * v[1] - u[1] * v[0]) <= math.sin(math.radians(ALIGNED_DEG))
    return aligned and (not sense or u[0] * v[0] + u[1] * v[1] > 0)


def walls(source):
    """The bracing walls of a plan, one per **straight run** of an H or W element: [{element, label, construction, a, b, length, direction}] -- its element's index and number, its construction mode or None, its two ends in sheet units, its length and its unit direction. A wall carries forces in its own plane only (the document's section 2), so one that turns a corner is as many walls as it has runs; the segments of one element that follow each other along one line -- a point put down on the way -- are one wall of their whole length. Two elements stay two walls, end to end or not."""
    out = []
    for index, element in enumerate(source.get("elements") or []):
        if element.get("type") not in WALL_TYPES:
            continue
        points = [(float(x), float(y)) for x, y in element.get("points") or []]
        runs = []
        for a, b in zip(points, points[1:]):
            if math.dist(a, b) <= 1e-9:
                continue  # a draft's point clicked twice: check_source refuses it at the save
            if runs and _same_direction(_direction(*runs[-1]), _direction(a, b), sense=True):
                runs[-1] = (runs[-1][0], b)
            else:
                runs.append((a, b))
        for a, b in runs:
            out.append({"element": index, "label": element.get("label", ""), "construction": element.get("construction"),
                        "a": a, "b": b, "length": math.dist(a, b), "direction": _direction(a, b)})
    return out


def stiffness_centre(parts):
    """The stiffness centre of walls given as (x, y, c, s, k) -- a point of each wall's line of action, its unit direction and its stiffness along it --, by the document's section 9: K_xx, K_yy, K_xy, K_xθ and K_yθ summed over the walls with each one's lever arm r = x·s − y·c, then x_S = (K_xx·K_yθ − K_xy·K_xθ) / D and y_S = (K_xy·K_yθ − K_yy·K_xθ) / D, D = K_xx·K_yy − K_xy². None where D is not positive: every wall along one line.

    The sums are taken about the walls' own middle and not about the sheet's corner: S does not depend on the origin, and the lever arms then stay of the size of the building whatever page it is drawn on. The formulas hold as they are with y pointing down, the sheet's frame: mirroring y mirrors S and nothing else (tests/test_plan_centres.py).
    """
    parts = list(parts)
    if not parts:
        return None
    x0 = sum(p[0] for p in parts) / len(parts)
    y0 = sum(p[1] for p in parts) / len(parts)
    kxx = kyy = kxy = kxt = kyt = 0.0
    for x, y, c, s, k in parts:
        r = (x - x0) * s - (y - y0) * c
        kxx += k * c * c
        kyy += k * s * s
        kxy += k * s * c
        kxt += k * c * r
        kyt += k * s * r
    det = kxx * kyy - kxy * kxy
    if det <= 0:
        return None
    return x0 + (kxx * kyt - kxy * kxt) / det, y0 + (kxy * kyt - kyy * kxt) / det


def _stiffness(source, pid):
    """(S's record or None, why there is none, what to say of it) -- `state`'s half for the walls."""
    found = walls(source)
    if not found:
        return None, engine.Note("plan_centres_no_walls", f"plan {pid}: no bracing wall (H, W) is drawn -- no stiffness centre", plan=pid), []
    bare = list(dict.fromkeys(wall["label"] or "?" for wall in found if wall["construction"] not in MODES))
    if bare:
        return None, engine.Note("plan_centres_no_mode", f"plan {pid}: {len(bare)} bracing wall(s) carry no construction mode ({', '.join(bare)}) -- the stiffness centre is not calculated",
                                 plan=pid, count=len(bare), labels=", ".join(bare)), []
    counts = {mode: sum(1 for wall in found if wall["construction"] == mode) for mode in MODES}
    used = [mode for mode in MODES if counts[mode]]
    if len(used) > 1:
        return None, engine.Note("plan_centres_mixed", f"plan {pid}: the bracing walls are not all built the same way (timber frame: {counts['timber_frame']}, CLT: {counts['clt']}, concrete: {counts['concrete']}) -- the stiffness centre is calculated for one construction mode only",
                                 plan=pid, **counts), []
    mode = used[0]
    power = power_of(source, mode)
    if power is None:
        return None, engine.Note("plan_centres_no_power", f"plan {pid}: the bracing walls are CLT and the power their length is raised to (1.5 or 2) is not chosen -- the stiffness centre is not calculated", plan=pid), []
    first = found[0]["direction"]
    if all(_same_direction(first, wall["direction"]) for wall in found):
        return None, engine.Note("plan_centres_one_direction", f"plan {pid}: every bracing wall runs in the same direction -- the stiffness centre needs walls in two directions at least", plan=pid), []
    parts = [((wall["a"][0] + wall["b"][0]) / 2, (wall["a"][1] + wall["b"][1]) / 2, *wall["direction"], wall["length"] ** power) for wall in found]
    point = stiffness_centre(parts)
    if point is None:
        return None, engine.Note("plan_centres_one_direction", f"plan {pid}: every bracing wall runs in the same direction -- the stiffness centre needs walls in two directions at least", plan=pid), []
    remarks = []
    x0, y0, x1, y1 = bbox([end for wall in found for end in (wall["a"], wall["b"])])
    extent = math.hypot(x1 - x0, y1 - y0)
    if all(abs((x - point[0]) * s - (y - point[1]) * c) <= CONCURRENT * extent for x, y, c, s, _k in parts):
        remarks.append(engine.Note("plan_centres_no_torsion", f"plan {pid}: the lines of action of every bracing wall pass through one point -- the storey has no torsional stiffness", plan=pid))
    return {"point": point, "construction": mode, "power": power, "walls": len(found)}, None, remarks


def _mass(source, pid):
    """(the outline's points or None, M's record or None, why there is none) -- `state`'s half for the outline."""
    outlines = source.get("outlines") or []
    points = [(float(x), float(y)) for x, y in (outlines[0].get("points") or [])] if outlines else []
    if len(points) < 3:
        return None, None, engine.Note("plan_centres_no_outline", f"plan {pid}: no building outline is drawn -- no mass centre", plan=pid)
    x0, y0, x1, y1 = bbox(points)
    if ring_area(points) <= FLAT * ((x1 - x0) ** 2 + (y1 - y0) ** 2):
        # asked before `centroid`, which gives the mean of the corners for an area of nothing
        return points, None, engine.Note("plan_centres_flat_outline", f"plan {pid}: the building outline encloses no area -- no mass centre", plan=pid)
    return points, {"point": centroid(points)}, None


def state(source):
    """S, M and the outline of a plan as it stands, and for each of the two centres why it is not there: {applies, outline, mass, mass_note, stiffness, stiffness_note, remarks}.

    `stiffness` is {point, construction, power, walls} -- S in sheet units, the one mode of the walls taken, the power their length was raised to and how many they are -- or None with `stiffness_note`, an `engine.Note` the window writes in its own language; `remarks` are what is to be said of an S that is there (no torsional stiffness). `mass` is {point}, the outline's area centroid, or None with `mass_note`. On a plan that has no stiffness centre at all (`applies`), everything is None and nothing is said.
    """
    pid = source.get("id") or "?"
    if not applies(source):
        return {"applies": False, "outline": None, "mass": None, "mass_note": None, "stiffness": None, "stiffness_note": None, "remarks": []}
    stiffness, stiffness_note, remarks = _stiffness(source, pid)
    outline, mass, mass_note = _mass(source, pid)
    return {"applies": True, "outline": outline, "mass": mass, "mass_note": mass_note,
            "stiffness": stiffness, "stiffness_note": stiffness_note, "remarks": remarks}


def drawn(found):
    """Whether a `state` has anything to draw: S, M or the outline."""
    return bool(found["stiffness"] or found["mass"] or found["outline"])


def mode_note(mode):
    """A construction mode as a word the window writes in its own language (`warn_plan_construction_<mode>`), the English one for the export."""
    return engine.Note(f"plan_construction_{mode}", {"timber_frame": "timber frame", "clt": "CLT", "concrete": "concrete"}[mode])


def warnings(source, sections=None):
    """What this module has to say of a plan that does not stop the report: where the plan asks for S, M and the outline to be printed (`print_centres`), each of the two centres that cannot be -- with its reason -- and what is to be said of S; and, whatever it prints, every bracing wall whose position has a CLT section (`sections`: position id -> section type) and which is drawn in another mode -- the plan's mode and the position's section are two statements of one wall, and this is where they are held together (the engineer, 13.10.2026). A wall without a mode is not one of them: the stiffness centre's own reason names it."""
    if not applies(source):
        return []
    pid = source.get("id") or "?"
    out = []
    if source.get("print_centres"):
        found = state(source)
        out += [note for note in (found["stiffness_note"], found["mass_note"]) if note is not None]
        out += found["remarks"]
    for element in source.get("elements") or []:
        mode, label = element.get("construction"), element.get("label", "")
        if element.get("type") in WALL_TYPES and mode in MODES and mode != "clt" and (sections or {}).get(label) == "clt":
            out.append(engine.Note("plan_centres_section", f"plan {pid}: {label}'s position has a CLT section and the wall is drawn as {mode_note(mode)} -- set one of the two",
                                   plan=pid, label=label, mode=mode_note(mode)))
    return list(dict.fromkeys(out))


def record(source, clean=float):
    """What data/plans.json says of a plan's centres where the plan prints them: {source, reference, unit, outline?, mass?, stiffness?} -- each of the three where it is drawn, in sheet units as the rest of the plan's record, with what S was computed from and the method cited. None where the plan prints none or has none to print. `clean` rounds a number as the record writes it (plan_geometry._clean)."""
    if not source.get("print_centres"):
        return None
    found = state(source)
    if not drawn(found):
        return None
    out = {"source": SOURCE, "reference": REFERENCE, "unit": "sheet"}
    if found["outline"]:
        out["outline"] = [[clean(x), clean(y)] for x, y in found["outline"]]
    if found["mass"]:
        out["mass"] = {"point": [clean(v) for v in found["mass"]["point"]]}
    if found["stiffness"]:
        s = found["stiffness"]
        out["stiffness"] = {"point": [clean(v) for v in s["point"]], "construction": s["construction"], "power": clean(s["power"]), "walls": s["walls"]}
    return out
