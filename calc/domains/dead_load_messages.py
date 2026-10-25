"""What a build-up of permanent loads says of itself (spec docs/requirements/completed/2026-10-24-poids-propre-repense.md, REQ-007, P04; issue #111): its layers weighed once, by `evaluate`, which the export reads to stop (dead_load_source.layer_rows raises the first problem) and the tab reads to say (`messages`). One rule, written once.

**Red** (`error`, the export stops): a layer with no material, a load typed with no value, a material Woodcore does not know or that has no weight, a thickness, a width or a spacing its pose needs missing, pieces as wide as their spacing (b/e ≥ 1, nothing left to fill), a level the rule of two refuses (D-07), a retained value written below the sum.
**Orange** (`warning`): a load written in place of a layer's calculation (v in place of c), a retained value written in place of the tenth above the sum (v, auto c), a line that fills thicker than the pieces beside it, battens counted twice under tiles weighed «inkl. Lattung» (SIA 261 Tabelle 29, + d kN/m², Q-006: the roles `dead_load_layers.BATTEN_ROLES`) -- none changes the sum.
**Information** (`info`): the air above a line that fills thinner than its pieces; a material of the engineer's own that his library changed or lacks (issue #110, REQ-014).
**Green** (`ok`): every layer has its weight.

Each message names its layer (`field`: "layers[i]"), or the retained value ("chosen"), or the build-up (None). Its words are the tab's, `ld_msg_<code>`, filled with its params. No Qt here.
"""

from collections import namedtuple

import validation
from domains import dead_load, dead_load_layers, dead_load_migrate, materials
from domains.contracts import Message

# One thing that stops a layer from being weighed: its index (None for the build-up), its code, the values its words take, and the English the export stops with
Problem = namedtuple("Problem", "index code params text")

# What the export stops with where a level breaks the rule of two (D-07), read by dead_load_source.check_source too
LEVEL_TEXT = {"level_three": "a third layer on one level -- a level holds two layers at most, one spaced and one that fills (D-07)",
               "level_two_spaced": "two spaced layers on one level -- a level holds one spaced layer and one that fills (D-07)",
               "level_two_fill": "two layers on one level, neither spaced -- a level holds one spaced layer and one that fills (D-07)"}


def _weigh(material_id, projects):
    """(weight, None) -- weight being materials.weight_of's (value, unit, label, source) -- or (None, (code, text)) where it cannot be weighed."""
    try:
        return materials.weight_of(material_id, projects), None
    except validation.ValidationError as exc:
        return None, ("no_weight" if materials.knows(material_id, projects) else "unknown_material", str(exc))


def evaluate(src, projects=None, where="loads/dead"):
    """(rows, problems) of the build-up `src` (a 1.x source read as 2.0 first): a row a layer as `dead_load_source.layer_rows` gives it -- its `load` None where a problem stops it --, and the problems, the layers' first, then a retained value written below the sum."""
    src = dead_load_migrate.upgrade(src, where, projects)
    layers = src["layers"]
    rows, problems = [], []

    def stop(i, code, params, text):
        problems.append(Problem(i, code, params, "%s: layers[%d] -- %s" % (where, i, text) if i is not None else "%s: %s" % (where, text)))

    for i, layer in enumerate(layers):
        pose = layer["pose"]
        base = {"kind": layer["kind"], "ebene": "", "thickness": layer.get("thickness"),
                "width": layer.get("width") if pose == "spaced" else None, "spacing": layer.get("spacing") if pose == "spaced" else None,
                "pose": pose, "link": bool(layer.get("link")), "role": layer.get("role"), "number": i + 1, "fill_width": None, "air": 0.0,
                "material_id": layer.get("material"), "includes_battens": False}
        if pose == "typed" and layer.get("load") is None:
            rows.append({**base, "material": dead_load.DIRECT_LOAD, "label": layer.get("label") or dead_load.DIRECT_LOAD, "dicke": None, "breite": None,
                         "dist": None, "mass": None, "unit": "", "load": None, "source": "entered", "formula": "", "computed": None, "replaced": False})
            stop(i, "missing_load", {"layer": i + 1}, "a load typed with no value -- type it in kN/m²")
            continue
        if pose == "typed":
            rows.append({**base, "material": dead_load.DIRECT_LOAD, "label": layer.get("label") or dead_load.DIRECT_LOAD,
                         "dicke": None, "breite": None, "dist": None, "mass": None, "unit": "", "load": float(layer["load"]),
                         "source": "entered", "formula": "", "computed": None, "replaced": False})
            continue
        row = {**base, "material": layer.get("label") or "", "label": layer.get("label") or "", "dicke": None, "breite": None, "dist": None,
               "mass": None, "unit": "", "load": None, "source": "", "formula": "", "computed": None, "replaced": False}
        rows.append(row)
        if not layer.get("material"):
            stop(i, "no_material", {"layer": i + 1, "name": layer.get("label") or ""},
                 "no material" + (" -- %r is not a material Woodcore knows" % layer["label"] if layer.get("label") else ""))
            continue
        weight, failed = _weigh(layer["material"], projects)
        if failed:
            stop(i, failed[0], {"layer": i + 1, "name": layer["material"]}, failed[1])
            continue
        value, unit, label, source = weight
        row.update(material=label, label=layer.get("label") or label, mass=value, unit=unit, source=source,
                   includes_battens=materials.includes_battens(layer["material"], projects))
        if pose == "spaced" and dead_load_layers.share(layer) >= 1:
            stop(i, "share_full", {"layer": i + 1, "width": layer["width"], "spacing": layer["spacing"]},
                 "width %s mm is not below the spacing %s mm -- the pieces leave nothing to fill" % (layer["width"], layer["spacing"]))
            continue
        width_mm, _computed = dead_load_layers.fill_width(layers, i)
        load, numbers = dead_load_layers.computed_load(layer, value, unit, width_mm)
        if load is None:
            code = "missing_thickness" if "t" not in numbers else "missing_width_spacing"
            stop(i, code, {"layer": i + 1, "name": label},
                 "%s weighs %s %s, per volume -- it needs %s" % (label, value, unit, "its thickness" if code == "missing_thickness" else "its width and its spacing"))
            continue
        replaced = layer.get("load") is not None
        per_volume = "t" in numbers
        if pose == "spaced":
            row.update(breite=layer["width"] / 1000.0, dist=layer["spacing"] / 1000.0)
        elif per_volume and width_mm is not None and abs(width_mm - dead_load_layers.STRIP) > 1e-9:
            row.update(breite=width_mm / 1000.0, dist=dead_load_layers.STRIP / 1000.0)   # a line that fills: its width on 1 m
        row.update(fill_width=width_mm, air=dead_load_layers.air(layers, i), dicke=layer["thickness"] / 1000.0 if per_volume else None,
                   load=float(layer["load"]) if replaced else load, formula=dead_load_layers.formula(numbers, load), computed=load, replaced=replaced)
    for index, code in dead_load_layers.level_problems(layers):
        stop(index, code, {"layer": index + 1}, LEVEL_TEXT[code])
    if not problems:
        total = sum(r["load"] for r in rows)
        chosen = src.get("chosen")
        if chosen is not None and total > 0 and chosen < total * (1 - dead_load.CHOSEN_TOLERANCE):
            problems.append(Problem(None, "chosen_below", {"chosen": chosen, "total": round(total, 3)},
                                    "%s: chosen is %.3f kN/m², below the %.3f kN/m² its own layers add up to -- round up, never down" % (where, chosen, total)))
    return rows, problems


def _field(index):
    return None if index is None else "layers[%d]" % index


def red(problems):
    """The problems of `evaluate` as the tab says them (contracts.Message, `error`): each with its layer, or the retained value."""
    return [Message(p.code, "chosen" if p.code == "chosen_below" else _field(p.index), "error", p.params) for p in problems]


def messages(src, projects=None, where="loads/dead"):
    """What the tab says of the build-up `src` (contracts.Message), red first, then orange, then information; green alone where no layer stops (REQ-007). The engineer's materials changed in his library are said by dead_load_source.messages, which adds them."""
    rows, problems = evaluate(src, projects, where)
    out = red(problems)
    if out:
        return out
    src = dead_load_migrate.upgrade(src, where, projects)
    total = sum(r["load"] for r in rows)
    for i, row in enumerate(rows):
        if row["replaced"]:
            out.append(Message("load_replaced", _field(i), "warning", {"layer": i + 1, "value": row["load"], "computed": round(row["computed"], 3)}))
    if src.get("chosen") is not None:
        out.append(Message("chosen_replaced", "chosen", "warning", {"value": src["chosen"], "auto": dead_load_layers.retained(total)}))
    for level in dead_load_layers.levels(src["layers"]):
        pieces = [j for j in level if rows[j]["pose"] == "spaced"]
        fills = [j for j in level if rows[j]["pose"] != "spaced"]
        if pieces and fills and (rows[fills[0]]["thickness"] or 0) > (rows[pieces[0]]["thickness"] or 0):
            out.append(Message("fill_thicker", _field(fills[0]), "warning",
                               {"layer": fills[0] + 1, "fill": rows[fills[0]]["thickness"], "pieces": rows[pieces[0]]["thickness"]}))
    out.extend(_battens_twice(rows))
    for i, row in enumerate(rows):
        if row["air"] > 0:
            out.append(Message("air", _field(i), "info", {"layer": i + 1, "air": row["air"]}))
    out.append(Message("all_weighed", None, "ok", {"total": round(total, 3)}))
    return out


def _battens_twice(rows):
    """The battens a build-up adds under tiles that already carry them (T34, T62, Q-006): one warning on the tiles, + the battens' load."""
    tiles = [i for i, r in enumerate(rows) if r["includes_battens"]]
    battens = [r for r in rows if r["role"] in dead_load_layers.BATTEN_ROLES]
    if not tiles or not battens:
        return []
    extra = sum(r["load"] for r in battens)
    return [Message("battens_twice", _field(tiles[0]), "warning", {"layer": tiles[0] + 1, "extra": round(extra, 3), "tiles": rows[tiles[0]]["label"]})]
