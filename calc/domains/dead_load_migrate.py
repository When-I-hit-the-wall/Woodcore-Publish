"""A build-up written before issue #111 read as dead-load-source 2.0, in memory (spec docs/requirements/completed/2026-10-24-poids-propre-repense.md, REQ-002, ARCH-007; answer 1 of 24.10.2026).

Nothing is rewritten when a source is read: the export of a project stays what its files say until the engineer saves the build-up again, which writes 2.0. `upgrade(src)` is pure and the one reader of the old shapes -- 1.0, 1.1 (with `links`), 1.2 (a material by its id):

* **`beside`** on layer i («beside the line above») becomes **`link`** on layer i − 1 («linked to the line below»): on a level of a spaced layer and another, the other keeps the full width it was summed with -- `fill` false, `width` 1000 --, so the sum does not change (answer 1); two layers beside each other neither of which is spaced are left on two levels (the same sum, drawn one above the other); two spaced layers beside each other, or three layers on one level, break the rule of two (D-07) and are refused naming the layer;
* **the library**: `catalogue` keeps its id; `sia261` becomes `sia261:<id>`; `belastungsannahmen` the workbook's row (`materials_catalogue.ext_id`, the exact pair first, as `materials.weight` always read it) -- a name no row carries left unnamed, which the build-up says in red, as the old reading refused it; `project` (a 1.0 project's own weight, not yet poured into the library) `project:<id>`; `direct` the pose `typed`, its words its `label`;
* **the pose** from the weight's unit and the layer's numbers: per surface `surface`, a width with a spacing `spaced`, else `continuous`;
* **the role** from the workbook's Ebene the layer named, which said what the layer is for (`EBENE_ROLES`): «Dämmung» insulation, «Dachlattung» roof battens… -- an Ebene that says no one role leaves none.

No Qt here.
"""

import copy

import validation
from domains import materials, materials_catalogue

VERSION = "2.0"
# The workbook's Ebenen (its column «Ebene», calc/libraries/materials-library.json) as the roles of dead_load_layers.ROLES -- «Beschichtung» says no one role
EBENE_ROLES = {"Dämmung": "insulation", "Trittschalldämmung": "impact_insulation", "Konstruktion": "structure", "Beplankung": "bracing_panel",
               "Bekleidung": "lining", "Fussboden": "floor_finish", "Unterlagsboden": "screed", "Lattung": "battens", "Gefällslattung": "battens",
               "Rostung": "battens", "Dachlattung": "roof_battens", "Konterlattung": "counter_battens", "Fassade": "facade", "Beschwerung": "ballast",
               "Dachhaut": "roofing", "Schutzbahn/Dachhaut": "protection", "Unterdach": "underlay", "Unterdachbahn": "underlay_membrane",
               "Abdeckbahn": "underlay_membrane", "Abdichtung": "waterproofing"}


def _unit_of(material_id, projects=None):
    """The unit a material is weighed in, or None where it cannot be found."""
    try:
        return materials.weight_of(material_id, projects)[1]
    except validation.ValidationError:
        return None


def material_id(layer):
    """The id a 1.x layer's material takes in 2.0 -- None for a load typed, or a workbook's name no row carries."""
    library, material, ebene = layer.get("library"), layer.get("material"), layer.get("ebene") or ""
    if library == "catalogue":
        return material
    if library == "sia261":
        return "sia261:" + str(material)
    if library == "belastungsannahmen":
        return materials_catalogue.ext_id(material, ebene)
    if library == "project":
        return "project:" + str(material)
    return None


def _upgrade_layer(layer, projects):
    out = {k: v for k, v in layer.items() if k not in ("library", "material", "ebene", "beside")}
    out["role"] = EBENE_ROLES.get(str(layer.get("ebene") or "").strip())
    if layer.get("library") == "direct":
        share = layer["width"] / layer["spacing"] if layer.get("width") and layer.get("spacing") else 1.0
        load = layer.get("load")
        out.update(pose="typed", material=None, label=layer.get("material") or "", width=None, spacing=None,
                   load=load * share if isinstance(load, (int, float)) and share != 1.0 else load)   # a typed load at a spacing was summed as its share: the same sum
        return out
    out["material"] = material_id(layer)
    out.setdefault("label", "")
    unit = _unit_of(out["material"], projects) if out["material"] else None
    if unit in materials.SURFACE_UNITS:
        out["pose"] = "surface"
    elif layer.get("width") is not None and layer.get("spacing") is not None:
        out["pose"] = "spaced"
    else:
        out["pose"] = "continuous"
        out["width"] = None
    if out["pose"] != "spaced":
        out["spacing"] = None
    out["load"] = None if out["pose"] != "typed" else out.get("load")
    return out


def upgrade(src, where="loads/dead", projects=None):
    """`src` as 2.0, a copy -- itself where it is 2.0 already. A level the rule of two refuses stops, naming the file and the layer."""
    if src.get("schema_version") == VERSION:
        return src
    old = src.get("layers") or []
    layers = [_upgrade_layer(layer, projects) for layer in old]
    for layer in layers:
        layer.update(link=False, fill=True)
    for i in range(1, len(old)):
        if not old[i].get("beside"):
            continue
        above, here = layers[i - 1], layers[i]
        if old[i - 1].get("beside"):
            raise validation.ValidationError("%s: layers[%d] -- a third layer beside the two above it: a level holds two layers at most, one spaced and one that fills (D-07)" % (where, i))
        if above["pose"] == "spaced" and here["pose"] == "spaced":
            raise validation.ValidationError("%s: layers[%d] -- two spaced layers beside each other: a level holds one spaced layer and one that fills (D-07)" % (where, i))
        if "spaced" not in (above["pose"], here["pose"]):
            continue    # two layers beside each other, neither spaced: two levels, the same sum
        above["link"] = True
        filler = here if here["pose"] != "spaced" else above
        filler.update(fill=False, width=1000)
    out = copy.deepcopy({k: v for k, v in src.items() if k != "layers"})
    out["schema_version"] = VERSION
    out["layers"] = layers
    return out
