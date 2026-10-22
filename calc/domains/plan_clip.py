"""What is copied from a plan with Ctrl+C and put down on another with Ctrl+V (issue #61, docs/ui/tab-plans.md §10quater): the clip and its pasting, for the position plan and the fire-protection plan alike.

The engineer, 14.10.2026: «copier ce qui est dessiné sur un plan (par exemple le sous-sol), passer à un autre plan (par exemple le rez-de-chaussée) et y coller tous les objets sélectionnés». A clip holds deep copies of the entries selected, the base point clicked after Ctrl+C, the scale of the plan they came from and the project it belongs to; pasting puts the base point on the point clicked, scales the geometry about it where both plans have a scale (D-003), gives each element the next number of its prefix on the target plan's storey (REQ-006), replaces the target's building outline with a pasted one (D-002), and leaves out what the target plan cannot hold -- the very predicates `plan.check_source` refuses (REQ-009).

No Qt here (ARCH-001): the canvases call these functions and the tabs hold the one clip of the process (tools/plan_clipboard.py). The positions' numbering is the tab's, given as `propose`, so that this module does not reach the positions store.
"""

import copy
import dataclasses
import math

from domains import fire
from domains import plan
from domains import plan_centres

POSITION, FIRE = "position", "fire"   # the plan tabs' own KIND (drawing_tab.DrawingTab): a clip is pasted where its kind is the tab's
KINDS = (POSITION, FIRE)

# The plan's entries that exist on an elevation section alone (plan.check_source: storey lines and boxes, load transfer levels).
SECTION_ONLY = ("storey-line", "storey-box", "load-level")


@dataclasses.dataclass
class Clip:
    """What Ctrl+C took: `kind` POSITION or FIRE, `entries` [(kind or collection, entry)] as deep copies in the order selected, the `base` point, the `per_m` of the plan copied from (None without a scale), `sections` {position number: its row's type and section} for the elements copied, and the project's `root`."""
    kind: str
    entries: list
    base: tuple
    per_m: float = None
    sections: dict = dataclasses.field(default_factory=dict)
    root: str = None

    def __len__(self):
        return len(self.entries)


def clip_plan(source, selection, base, per_m, sections=None, root=None):
    """A clip of the position plan's entries `selection` [(kind, index)], taken at `base`. `sections` {number: {type, section_type, dimension, units}} is what the new positions a paste makes take (REQ-006), read when the copy is made: the source plan's pending positions are gone once it is saved."""
    entries = []
    for kind, index in selection:
        items = source.get(plan.ENTRY_LISTS[kind]) or []
        if 0 <= index < len(items):
            entries.append((kind, copy.deepcopy(items[index])))
    return Clip(POSITION, entries, (float(base[0]), float(base[1])), per_m, dict(sections or {}), root)


def clip_fire(source, ids, base, per_m, root=None):
    """A clip of the fire-protection plan's entries `ids`, taken at `base`."""
    entries = []
    for eid in ids:
        found = fire.entry_of(source, eid)
        if found is not None:
            entries.append((found[0], copy.deepcopy(source[found[0]][found[1]])))
    return Clip(FIRE, entries, (float(base[0]), float(base[1])), per_m, {}, root)


def ratio(clip, per_m):
    """The factor the clip's geometry is scaled by on a plan of `per_m` sheet units per metre: the target's over the source's where both have a scale (D-003), else 1."""
    if clip.per_m and per_m:
        return float(per_m) / float(clip.per_m)
    return 1.0


def _mapper(base, point, factor):
    def at(p):
        x = point[0] + (float(p[0]) - base[0]) * factor
        y = point[1] + (float(p[1]) - base[1]) * factor
        return [plan._clean(round(x, 2)), plan._clean(round(y, 2))]
    return at


def placed(clip, point, per_m):
    """The clip's entries as a paste at `point` would put them, base on point: deep copies, every geometric field mapped (REQ-010) -- the points of every entry, an axis's or an aid's point, a storey box's corner and size, a dimension's offset, a surface's islands. What is not geometry stays: a number moved clear (`label_offset`), an angle, a diagonal, a slab's span, a style, the size of a symbol or a text. The preview and the paste both draw on this one function."""
    factor = ratio(clip, per_m)
    at = _mapper(clip.base, point, factor)
    out = []
    for kind, original in clip.entries:
        entry = copy.deepcopy(original)
        if "points" in entry:
            entry["points"] = [at(p) for p in entry["points"]]
        if "point" in entry:
            entry["point"] = at(entry["point"])
        if entry.get("holes"):
            entry["holes"] = [[at(p) for p in hole] for hole in entry["holes"]]
        if kind == "storey-box":
            entry["x"], entry["y"] = at((entry["x"], entry["y"]))
            entry["w"] = plan._clean(round(float(entry["w"]) * factor, 2))
            entry["h"] = plan._clean(round(float(entry["h"]) * factor, 2))
        if kind == "dimension" and "offset" in entry:
            entry["offset"] = plan._clean(round(float(entry["offset"]) * factor, 2))
        out.append((kind, entry))
    return out


def same_axis(a, b, window):
    """Whether two axes are one line: the same direction (to a hundredth of a degree, either way round) and the one's point on the other's line, to a millionth of the frame -- the same grid pasted on the next storey."""
    turn = (float(a.get("angle", 0.0)) - float(b.get("angle", 0.0))) % 180.0
    if min(turn, 180.0 - turn) > 0.01:
        return False
    angle = math.radians(float(b.get("angle", 0.0)))
    dx, dy = float(a["point"][0]) - float(b["point"][0]), float(a["point"][1]) - float(b["point"][1])
    across = abs(dx * math.sin(angle) - dy * math.cos(angle))
    return across <= 1e-6 * max(window["w"], window["h"], 1.0) + 0.01


def refused(source, kind, entry, window):
    """Why the position plan `source` would not hold this pasted entry -- "section-only", "load", "outline-on-section", "axis-there" -- or None. The predicates are `plan.check_source`'s and `plan_centres.applies`'s, so a paste never makes a file Woodcore refuses."""
    if kind in SECTION_ONLY and source.get("role", "plan") != "section":
        return "section-only"
    if kind == "element" and plan.is_load(entry.get("type")) and plan.plan_type(source) != "loadpath":
        return "load"
    if kind == "outline" and not plan_centres.applies(source):
        return "outline-on-section"
    if kind == "axis" and any(same_axis(entry, other, window) for other in source.get("axes") or []):
        return "axis-there"
    return None


def paste_plan(source, clip, point, per_m, window, propose):
    """The clip put down on the position plan `source` at `point`, in place -- inside a change the caller opened, so that it is one step of «Annuler». `propose(type_)` is the number a new element of that type takes on this plan's storey (the tab's `propose_label`, which reads the plan as it now is, the elements pasted before included). Returns {added: [(kind, index)], relabelled: {old: new}, left_out: {reason: count}, axes_renamed: [(old, new)], outline_replaced: bool}.

    Two elements copied with one number -- two occurrences of one position -- share their new one too. A load symbol takes the plan's next load number. An element without a number keeps none. An axis is named by where it lands (`insert_axis`), unless it is already there."""
    added, relabelled, left_out, renames = [], {}, {}, []
    outline_replaced = False
    for kind, entry in placed(clip, point, per_m):
        reason = refused(source, kind, entry, window)
        if reason:
            left_out[reason] = left_out.get(reason, 0) + 1
            continue
        if kind == "outline":
            outline_replaced = outline_replaced or bool(source.get("outlines"))
            source["outlines"] = [entry]
            added = [item for item in added if item[0] != "outline"] + [("outline", 0)]
            continue
        if kind == "axis":
            entry["label"] = ""
            axes = source.setdefault("axes", [])
            renames = _compose(renames, plan.insert_axis(axes, entry, window))
            added.append(("axis", next(i for i, axis in enumerate(axes) if axis is entry)))
            continue
        if kind == "element":
            _relabel(source, entry, relabelled, propose)
        items = source.setdefault(plan.ENTRY_LISTS[kind], [])
        items.append(entry)
        added.append((kind, len(items) - 1))
    return {"added": added, "relabelled": relabelled, "left_out": left_out, "axes_renamed": renames, "outline_replaced": outline_replaced}


def _relabel(source, element, relabelled, propose):
    old = element.get("label")
    if not old:
        return
    type_ = element.get("type")
    if plan.is_load(type_):
        element["label"] = plan.next_load_label(source, type_)
        return
    if not plan.labelled(type_):
        return
    if old not in relabelled:
        relabelled[old] = propose(type_)
    element["label"] = relabelled[old]


def _compose(renames, more):
    """Two lists of renames as one: an axis renamed A→B then B→C is A→C."""
    out = list(renames)
    for old, new in more:
        for i, (first, last) in enumerate(out):
            if last == old:
                out[i] = (first, new)
                break
        else:
            out.append((old, new))
    return [(a, b) for a, b in out if a != b]


def paste_fire(source, clip, point, per_m):
    """The clip put down on the fire-protection plan `source` at `point`, in place: each entry with an id of its own (`fire.next_id`), in a collection the plan may not have yet. Returns {added: [ids], left_out: {}}."""
    added = []
    for collection, entry in placed(clip, point, per_m):
        entry["id"] = fire.next_id(source, collection)
        source.setdefault(collection, []).append(entry)
        added.append(entry["id"])
    return {"added": added, "left_out": {}}


def new_positions(clip, relabelled):
    """{new number: its row} for the positions a paste made: the copied position's type and section under its new number -- what the tab keeps among the plan's pending positions until it is saved."""
    return {new: dict(clip.sections[old]) for old, new in relabelled.items() if old in clip.sections}
