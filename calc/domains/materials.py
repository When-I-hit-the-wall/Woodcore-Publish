"""The materials a permanent load's layer is weighed with (issue #35, decision D-07): three libraries, each saying where its numbers come from.

* **`sia261`** -- SIA 261:2020 Anhang A, Tabelle 28 (kN/m³) and Tabelle 29 (kN/m²), read through `norms.sia261`, never copied here: the norm, and the one that wins where a material is both the norm's and the workbook's.
* **`belastungsannahmen`** -- the library of a load workbook of an engineering office, read out once into `calc/libraries/materials-library.json`: not a norm, so it lives beside `calc/norms/` and not in it, each entry carrying the workbook's own «Quellen». Keyed by (Ebene, material), as the workbook keys it: a name listed under two Ebenen with two weights is two entries, and the rule the workbook's reader kept until issue #109 -- the exact pair, never a guess -- holds.
* **`project`** -- the weights the engineer added by hand to `Woodcore-Datei/materials.json` 1.0 (schemas/materials.schema.json) until v0.125.

Since issue #110 (spec docs/requirements/active/2026-10-24-onglet-materiaux.md, D-07 replaced) a layer names **one id** under `library: "catalogue"` (dead-load-source 1.2): a material Woodcore ships (`materials_catalogue`: `sia265:…`, `sia265-1:…`, `sia261:…`, `ext:<row>`) or one of the engineer's own (`u-…`), read from the copy the project keeps of it (`materials.json` 2.0, `materials_project`) -- never from the engineer's library, so that the project computes alike on another computer. The three old libraries stay read forever, for the layers written before (CON-003).

A layer names its library and its material; `weight(layer)` gives (value, unit, label, source) and refuses, naming the field, what it cannot find. The load of a layer is computed in `dead_load_source`. No Qt here.
"""

import json
from pathlib import Path

import project
import validation
from norms import sia261

LIBRARY_FILE = Path(__file__).resolve().parent.parent / "libraries" / "materials-library.json"
PROJECT_SCHEMA = "materials"
PROJECT_SCHEMA_VERSION = "2.0"
PROJECT_SCHEMA_VERSIONS = ("1.0", "2.0")   # 1.0 read (the weights typed in the project until v0.125), 2.0 written: the copies of the engineer's materials (issue #110)

LIBRARIES = ("sia261", "belastungsannahmen", "project", "catalogue")
# The units a weight may carry: per volume (multiplied by the layer's thickness) or per surface (not)
VOLUME_UNITS = ("kg/m³", "kN/m³")
SURFACE_UNITS = ("kg/m²", "kN/m²")
UNITS = VOLUME_UNITS + SURFACE_UNITS
# kg -> kN as the Belastungsannahmen workbook converts it, g = 10 m/s² (dead_load.KG_TO_KN)
KG_TO_KN = 100.0

_workbook = None


def workbook_library():
    """The Woodcore materials library as its file states it: [{ebene, material, mass, unit, quelle, info, row}]."""
    global _workbook
    if _workbook is None:
        data = json.loads(LIBRARY_FILE.read_text(encoding="utf-8"))
        for entry in data["materials"]:
            if entry["unit"] not in UNITS or not isinstance(entry["mass"], (int, float)):
                raise validation.ValidationError("%s: row %s, %r -- a weight in %s" % (LIBRARY_FILE.name, entry.get("row"), entry.get("material"), ", ".join(UNITS)))
        _workbook = data
    return _workbook


def norm_entries():
    """SIA 261 Anhang A as the libraries list it: [{id, name, group, value, unit, table}] -- Tabelle 28's unit weights and Tabelle 29's surface loads, a line without a value left out."""
    out = []
    for table, column, unit in ((sia261.table_28(), "raumlast", "kN/m³"), (sia261.table_29(), "flaechenlast", "kN/m²")):
        for line in table["rows"]:
            value = line.get(column)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                out.append({"id": line["id"], "name": line["name"], "group": line.get("group"), "value": value, "unit": unit,
                            "table": table["number"]})
    return out


def project_file(here=None):
    return (here or project.current()).sources_dir / "materials.json"


def empty_project():
    return {"schema_version": PROJECT_SCHEMA_VERSION, "materials": []}


def check_project(data, where="materials.json"):
    """The project's materials: their shape, and -- 1.0 -- each entry an id, a name, a weight above 0 in one of UNITS; -- 2.0 -- each a copy of one of the engineer's materials, the shape of `materials_contract`. A defect stops, naming the entry."""
    if not isinstance(data, dict) or data.get("schema_version") not in PROJECT_SCHEMA_VERSIONS:
        raise validation.ValidationError("%s: schema_version is %r -- expected %s" % (where, (data or {}).get("schema_version") if isinstance(data, dict) else data, " or ".join(PROJECT_SCHEMA_VERSIONS)))
    validation.validate_structure(data, PROJECT_SCHEMA)
    if data["schema_version"] == "2.0":
        from domains import materials_contract
        from norms import sia265_1
        products = set(sia265_1.products())
        for m in data["materials"]:
            materials_contract.check_material(m, where + ": materials", products)
            if not materials_contract.USER_ID.match(m["id"]):
                raise validation.ValidationError("%s: materials[%s] -- a project keeps copies of the engineer's own materials only (u-<8 hex>)" % (where, m["id"]))
        materials_contract.check_ids_unique(data["materials"], where)
        return
    seen = set()
    for i, entry in enumerate(data["materials"]):
        at = "%s: materials[%d]" % (where, i)
        if not str(entry.get("id") or "").strip():
            raise validation.ValidationError("%s: no id" % at)
        if entry["id"] in seen:
            raise validation.ValidationError("%s: id %r is listed twice" % (at, entry["id"]))
        seen.add(entry["id"])
        if entry.get("unit") not in UNITS:
            raise validation.ValidationError("%s: unit %r -- %s" % (at, entry.get("unit"), ", ".join(UNITS)))
        mass = entry.get("value")
        if isinstance(mass, bool) or not isinstance(mass, (int, float)) or mass <= 0:
            raise validation.ValidationError("%s: value %r -- a weight above 0" % (at, mass))


def read_project(here=None):
    """The engineer's library, checked -- empty where the project has none."""
    path = project_file(here)
    if not path.exists():
        return empty_project()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise validation.ValidationError("materials.json: cannot be read as JSON -- %s" % exc)
    check_project(data)
    return data


def weight(layer, projects=None):
    """(value, unit, label, source) of the material a layer names -- `projects` the engineer's library (read_project()). Refuses, naming the field, a library or a material it does not find, and a weight of 0."""
    library = layer.get("library")
    material = layer.get("material")
    if library == "sia261":
        for entry in norm_entries():
            if entry["id"] == material:
                label = "%s, %s" % (entry["group"], entry["name"]) if entry.get("group") else entry["name"]
                return entry["value"], entry["unit"], label, "norm:SIA 261:2020, Anhang A, Tabelle %s" % entry["table"]
        raise validation.ValidationError("material %r is not a line of SIA 261 Anhang A, Tabelle 28 or 29" % (material,))
    if library == "belastungsannahmen":
        ebene = layer.get("ebene") or ""
        found = [e for e in workbook_library()["materials"] if e["material"] == material and e["ebene"] == ebene]
        if not found:
            names = [e for e in workbook_library()["materials"] if e["material"] == material]
            if len(names) == 1:
                found = names
            elif names:
                raise validation.ValidationError("material %r is listed under %s with different weights and not under Ebene %r -- name its Ebene"
                                                 % (material, ", ".join(sorted({e["ebene"] for e in names})), ebene))
        if not found:
            raise validation.ValidationError("material %r is not in Woodcore's materials library" % (material,))
        entry = found[0]
        if entry["mass"] <= 0:
            raise validation.ValidationError("material %r weighs %s %s in Woodcore's materials library -- state its weight in the project's library"
                                             % (material, entry["mass"], entry["unit"]))
        source = "library:Woodcore materials, %s" % (entry["quelle"] or "ohne Quellenangabe")
        return entry["mass"], entry["unit"], entry["material"], source
    if library == "catalogue":
        return _catalogue_weight(material, projects)
    if library == "project":
        for entry in (projects or empty_project())["materials"]:
            if entry["id"] == material and "value" in entry:
                return entry["value"], entry["unit"], entry.get("name") or entry["id"], "project:materials.json" + (", %s" % entry["source"] if entry.get("source") else "")
        raise validation.ValidationError("material %r is not in the project's library (Woodcore-Datei/materials.json)" % (material,))
    raise validation.ValidationError("library %r -- %s" % (library, ", ".join(LIBRARIES)))


def weight_of(material_id, projects=None):
    """`weight` of a material named by its id alone, as a layer of dead-load-source 2.0 names it (issue #111): a shipped one or the engineer's (`catalogue`), or `project:<id>`, a 1.0 project's own weight not yet poured into the library (dead_load_migrate)."""
    text = str(material_id or "")
    if text.startswith("project:"):
        return weight({"library": "project", "material": text[len("project:"):]}, projects)
    return weight({"library": "catalogue", "material": material_id}, projects)


def knows(material_id, projects=None):
    """Whether a material named by its id is one Woodcore ships or the project keeps -- with a weight or without: what tells «unknown» from «no weight» (dead_load_messages)."""
    from domains import materials_catalogue
    text = str(material_id or "")
    kept = (projects or empty_project())["materials"]
    if text.startswith("project:"):
        return any(m.get("id") == text[len("project:"):] for m in kept)
    return materials_catalogue.find(material_id) is not None or any(m.get("id") == material_id and "type" in m for m in kept)


def includes_battens(material_id, projects=None):
    """Whether the material weighs with its battens, as SIA 261 Tabelle 29's tiles «inkl. Lattung» do (issue #111, P11) -- a shipped material's flag, never one of the engineer's own."""
    from domains import materials_catalogue
    found = materials_catalogue.find(material_id) if not str(material_id or "").startswith("project:") else None
    return bool(found and found.get("includes_battens"))


def _catalogue_weight(material, projects):
    """A layer of `library: "catalogue"`: a shipped material by its id, or the project's copy of one of the engineer's (`u-…`) -- refused, naming it, where neither has it or it has no weight."""
    from domains import materials_catalogue, materials_contract
    if materials_contract.USER_ID.match(str(material or "")):
        found = next((m for m in (projects or empty_project())["materials"] if m.get("id") == material and "type" in m), None)
        if found is None:
            raise validation.ValidationError("material %r is one of the engineer's own, and the project keeps no copy of it (Woodcore-Datei/materials.json) -- save the case once where the engineer's library holds it" % (material,))
        where = "project:materials.json"
    else:
        found = materials_catalogue.find(material)
        if found is None:
            raise validation.ValidationError("material %r is not a material Woodcore ships" % (material,))
        where = "library" if found.get("origin") == "ext" else "norm"
    weight = found.get("weight")
    if not weight:
        raise validation.ValidationError("material %r (%s) has no weight -- give it one in the «Matériaux» tab" % (material, materials_contract.name(found, "de")))
    source = (found.get("source") or {}).get("ref") or (found.get("source") or {}).get("url") or ""
    return weight["value"], weight["unit"], materials_contract.name(found, "de"), "%s:%s" % (where, weight.get("ref") or source)


def to_kn(value, unit):
    """A weight in kN per m³ or per m², from the unit it is given in."""
    return value / KG_TO_KN if unit.startswith("kg") else float(value)


def per_volume(unit):
    return unit in VOLUME_UNITS
