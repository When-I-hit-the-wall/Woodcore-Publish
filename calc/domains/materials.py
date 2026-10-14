"""The materials a permanent load's layer is weighed with (issue #35, decision D-07): three libraries, each saying where its numbers come from.

* **`sia261`** -- SIA 261:2020 Anhang A, Tabelle 28 (kN/m³) and Tabelle 29 (kN/m²), read through `norms.sia261`, never copied here: the norm, and the one that wins where a material is both the norm's and the workbook's.
* **`belastungsannahmen`** -- the library of a load workbook of an engineering office, read out once into `calc/libraries/materials-library.json`: not a norm, so it lives beside `calc/norms/` and not in it, each entry carrying the workbook's own «Quellen». Keyed by (Ebene, material), as the workbook keys it: a name listed under two Ebenen with two weights is two entries, and `dead_load.MaterialLibrary`'s rule -- the exact pair, never a guess -- holds.
* **`project`** -- the weights the engineer adds by hand, `Woodcore-Datei/materials.json` (schemas/materials.schema.json): a material the two others lack, or the one a manufacturer states.

A layer names its library and its material; `weight(layer)` gives (value, unit, label, source) and refuses, naming the field, what it cannot find. The load of a layer is computed in `dead_load_source`. No Qt here.
"""

import json
from pathlib import Path

import project
import validation
from norms import sia261

LIBRARY_FILE = Path(__file__).resolve().parent.parent / "libraries" / "materials-library.json"
PROJECT_SCHEMA = "materials"
PROJECT_SCHEMA_VERSION = "1.0"

LIBRARIES = ("sia261", "belastungsannahmen", "project")
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
    """The engineer's library: its shape, and each entry an id, a name, a weight above 0 in one of UNITS -- a defect stops, naming the entry."""
    if not isinstance(data, dict) or data.get("schema_version") != PROJECT_SCHEMA_VERSION:
        raise validation.ValidationError("%s: schema_version is %r -- expected %r" % (where, (data or {}).get("schema_version") if isinstance(data, dict) else data, PROJECT_SCHEMA_VERSION))
    validation.validate_structure(data, PROJECT_SCHEMA)
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
    if library == "project":
        for entry in (projects or empty_project())["materials"]:
            if entry["id"] == material:
                return entry["value"], entry["unit"], entry.get("name") or entry["id"], "project:materials.json" + (", %s" % entry["source"] if entry.get("source") else "")
        raise validation.ValidationError("material %r is not in the project's library (Woodcore-Datei/materials.json)" % (material,))
    raise validation.ValidationError("library %r -- %s" % (library, ", ".join(LIBRARIES)))


def to_kn(value, unit):
    """A weight in kN per m³ or per m², from the unit it is given in."""
    return value / KG_TO_KN if unit.startswith("kg") else float(value)


def per_volume(unit):
    return unit in VOLUME_UNITS
