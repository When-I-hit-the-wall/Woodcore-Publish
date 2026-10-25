"""A project's materials typed by hand before issue #110 poured into the engineer's library, once, when the project is opened (spec docs/requirements/active/2026-10-24-onglet-materiaux.md, REQ-015, Q-003 answer B, D-15).

Until v0.125 the «Poids propre» tab wrote its own weights into `Woodcore-Datei/materials.json` 1.0 -- an id, a name, a weight, a source --, and a layer named one by `library: "project"`. Now every material the engineer makes is his, in his library (`materials_user`), and the project keeps a copy of those its cases name (`materials_project`). So, at the opening:

1. **the library first**: each 1.0 entry becomes a material of the engineer's own (`other`, its weight in kN), or is the one already there of the same name and weight -- weights compared in kN, so that 500 kg/m³ is 5 kN/m³ --, never twice;
2. **then the project**, where it is writable: `materials.json` written at 2.0, the copies of those materials under their new ids, and every layer that named an old id rewritten to `library: "catalogue"` and the new id (dead-load-source 1.2) -- each file saved first into the project's archives, all written together or none (`commands_migrate.commit`, the one way a migration writes).

A project opened read only pours into the library and changes nothing of its own: its layers keep reading the 1.0 file. A second opening finds a 2.0 file and does nothing. What is poured is named, for the window to say. No Qt here.
"""

import json
from pathlib import Path

import engine
import validation
from domains import commands_migrate, dead_load_source, materials, materials_user

LABEL = "materials"


def _old(here):
    """The 1.0 entries of the project's materials.json, or [] -- a 2.0 file, none, or one that cannot be read (the export says why)."""
    path = materials.project_file(here)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        materials.check_project(data)
    except (OSError, ValueError, validation.ValidationError):
        return []
    return data["materials"] if data.get("schema_version") == "1.0" else []


def _same_weight(m, value, unit):
    w = m.get("weight") or {}
    return w.get("unit") == unit and abs(float(w.get("value") or 0) - value) <= 1e-9 * max(abs(value), 1.0)


def _as_material(entry, taken, project_name):
    value = round(materials.to_kn(entry["value"], entry["unit"]), 9)
    unit = "kN/m³" if materials.per_volume(entry["unit"]) else "kN/m²"
    source = {"kind": "book", "ref": entry["source"]} if str(entry.get("source") or "").strip() else {"kind": "none"}
    return {"id": materials_user.new_id(taken), "type": "other", "names": {"fr": entry.get("name") or entry["id"]}, "category": "direct",
            "comment": "← %s, materials.json" % project_name, "weight": {"value": value, "unit": unit, "ref": entry.get("source") or project_name}, "source": source}


def plan(here):
    """(the materials to add to the library, {old id: new id}) -- nothing for a project with no 1.0 entries."""
    old = _old(here)
    if not old:
        return [], {}
    library = materials_user.materials()
    taken = {m["id"] for m in library}
    add, ids = [], {}
    for entry in old:
        value = materials.to_kn(entry["value"], entry["unit"])
        unit = "kN/m³" if materials.per_volume(entry["unit"]) else "kN/m²"
        name = (entry.get("name") or entry["id"]).strip().casefold()
        found = next((m for m in library + add if m["type"] == "other" and _same_weight(m, value, unit)
                      and any(str(n).strip().casefold() == name for n in (m.get("names") or {}).values())), None)
        if found is None:
            found = _as_material(entry, taken, here.name)
            taken.add(found["id"])
            add.append(found)
        ids[entry["id"]] = found["id"]
    return add, ids


def _rewritten_sources(here, ids, projects=None):
    """The changes of every build-up whose layers name an old id of the project's library."""
    changes = []
    for path in dead_load_source.source_paths(here):
        before = path.read_text(encoding="utf-8")
        try:
            src = json.loads(before)
        except ValueError:
            continue   # a file that cannot be read is the export's to name
        old = [layer.get("material") if isinstance(layer, dict) and layer.get("library") == "project" else None for layer in src.get("layers") or ()]
        if not any(material in ids for material in old):
            continue
        try:
            src = dead_load_source.upgraded(src, "%s/%s" % (dead_load_source.FOLDER, path.name), projects)   # one reader of the old shapes (dead_load_migrate): the file is written at 2.0
        except validation.ValidationError:
            continue   # a level the rule of two refuses is the export's to name
        notes = []
        for i, (layer, material) in enumerate(zip(src["layers"], old)):
            if material in ids:
                notes.append("layers[%d]: project %s -> catalogue %s" % (i, material, ids[material]))
                layer["material"] = ids[material]
        if notes:
            dead_load_source.stamp_version(src)
            changes.append(commands_migrate.Change(path, before, engine.source_bytes(src).decode("utf-8"), notes))
    return changes


def migrate(here, read_only=False):
    """The migration done: the library first, then -- unless `read_only` -- the project. Returns the names of the materials poured into the library (for the window to say), [] on a second run."""
    add, ids = plan(here)
    if not ids:
        return []
    if add:
        materials_user.save_all(add)
    library = {m["id"]: m for m in materials_user.materials()}
    names = [library[new]["names"].get("fr") or new for new in dict.fromkeys(ids.values())]
    if read_only:
        return names
    copies = [library[new] for new in dict.fromkeys(ids.values())]
    path = materials.project_file(here)
    data = {"schema_version": materials.PROJECT_SCHEMA_VERSION, "materials": copies}
    materials.check_project(data)
    changes = [commands_migrate.Change(path, path.read_text(encoding="utf-8"), engine.source_bytes(data).decode("utf-8"),
                                       ["1.0 -> 2.0: %d material(s) moved into the engineer's library, kept here as copies" % len(ids)])]
    changes += _rewritten_sources(here, ids, materials.read_project(here))   # the 1.0 file, still on disk: what tells a weight per surface
    commands_migrate.commit(here, changes, LABEL)
    return names
