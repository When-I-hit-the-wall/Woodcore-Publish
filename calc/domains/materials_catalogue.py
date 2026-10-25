"""The materials Woodcore ships, read only, each read at its source (spec docs/requirements/active/2026-10-24-onglet-materiaux.md, REQ-003, REQ-005, ARCH-004, ARCH-008; issue #110).

* **SIA 265:2021 Tabellen 8 and 9** -- the strength classes, `sia265:<class>` (`norms.sia265.grades()`): members whose design values are the tables'.
* **SIA 265/1:2018 Tableaux 11 to 23** -- the wood-based panels, `sia265-1:<panel>` (`norms.sia265_1.panels()`): characteristic and design values both the norm's.
* **SIA 261:2020 Tabellen 28 to 30** -- the weights, `sia261:<row>`, every row with a value (`norms.sia261`).
* **The workbook's library** -- `calc/libraries/materials-library.json`, «Externe», `ext:<row>`: shown merged by name and weight, as the dead-load prototype did, under the first row's id; every row stays an id of its own (`ALIASES`), so that a layer naming a row the view merged is still weighed (D02).

Their names in French and English and their category are `calc/libraries/materials-catalogue.json`'s, which holds no number; the weight of a material of resistance is the line that file names for it (ARCH-008). The shape is `materials_contract`'s; a shipped material carries `origin` (`sia265`, `sia265-1`, `sia261`, `ext`), the file it is read from (`stored`) and, where its source is a norm, the excerpt the tab shows (`excerpt`: [norm file, id]). No Qt here.
"""

import json
from pathlib import Path

import validation
from domains import materials_contract as contract
from norms import sia261, sia265, sia265_1

CATALOGUE_FILE = Path(__file__).resolve().parent.parent / "libraries" / "materials-catalogue.json"
WORKBOOK_FILE = Path(__file__).resolve().parent.parent / "libraries" / "materials-library.json"
ORIGINS = ("sia265", "sia265-1", "sia261", "ext")
# kg -> kN as the workbook converts it, g = 10 m/s² (the one conversion of Woodcore's weights)
KG_TO_KN = 100.0

_cache = {}


def _catalogue():
    if "catalogue" not in _cache:
        _cache["catalogue"] = json.loads(CATALOGUE_FILE.read_text(encoding="utf-8"))
    return _cache["catalogue"]


def _workbook():
    if "workbook" not in _cache:
        _cache["workbook"] = json.loads(WORKBOOK_FILE.read_text(encoding="utf-8"))["materials"]
    return _cache["workbook"]


def _sia261_rows():
    """{row id: (row, table number, unit, value)} -- every row of Tabellen 28 to 30 with a value; Tabelle 29's «per 10 mm» row read as the volume it is."""
    per_10 = set(_catalogue()["sia261_per_10_mm"])
    out = {}
    for table, column, unit in ((sia261.table_28(), "raumlast", "kN/m³"), (sia261.table_29(), "flaechenlast", "kN/m²"), (sia261.table_30(), "raumlast", "kN/m³")):
        for row in table["rows"]:
            value = row.get(column)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            if row["id"] in per_10:
                value, unit_here = round(value / 0.010, 6), "kN/m³"
            else:
                unit_here = unit
            out[row["id"]] = (row, table["number"], unit_here, value)
    return out


def _german(row):
    group = row.get("group")
    return "%s, %s" % (group, row["name"]) if group and group not in ("Bodenbeläge", "Mörtelüberzüge") else row["name"]


def _sia261_materials():
    names = _catalogue()["sia261"]
    out = []
    for rid, (row, number, unit, value) in _sia261_rows().items():
        entry = names.get(rid)
        if entry is None:
            raise validation.ValidationError("%s: sia261.%s -- a row of SIA 261 Tabelle %s without its names" % (CATALOGUE_FILE.name, rid, number))
        ref = "SIA 261:2020, Tabelle %s" % number
        stored = "calc/norms/%s.json" % {"28": sia261.TAB28, "29": sia261.TAB29, "30": sia261.TAB30}[number]
        out.append({"id": "sia261:" + rid, "stored": stored, "type": "other", "origin": "sia261", "category": entry["category"],
                    "names": {"fr": entry["fr"], "de": _german(row), "en": entry["en"]}, "comment": "",
                    "weight": {"value": value, "unit": unit, "ref": ref + (" (0,20 kN/m² pro 10 mm)" if rid in _catalogue()["sia261_per_10_mm"] else "")},
                    "source": {"kind": "norm", "ref": ref}, "excerpt": ["sia261-2020-materials-excerpts", "tab%s" % number]})
        if row.get("includes_battens"):
            out[-1]["includes_battens"] = True   # Tabelle 29's tiles «inkl. Lattung» (issue #111, P11)
    return out


def _workbook_groups():
    """The workbook's rows merged by (material, mass, unit), in the file's order: [(rows)]."""
    groups = {}
    for e in _workbook():
        groups.setdefault((e["material"], e["mass"], e["unit"]), []).append(e)
    return list(groups.values())


def _ext_materials():
    names, roles = _catalogue()["workbook"], _catalogue()["workbook_roles"]
    groups = _workbook_groups()
    masses = {}
    for rows in groups:
        masses.setdefault(rows[0]["material"], set()).add(rows[0]["mass"])
    out = []
    for rows in groups:
        first = rows[0]
        entry = names.get(first["material"])
        if entry is None:
            raise validation.ValidationError("%s: workbook.%s -- a material of the workbook without its names" % (CATALOGUE_FILE.name, first["material"]))
        fr, de, en = entry["fr"], first["material"], entry["en"]
        if len(masses[first["material"]]) > 1:   # one name, two weights: the role tells them apart
            fr, de, en = "%s (%s)" % (fr, roles.get(first["ebene"], first["ebene"])), "%s (%s)" % (de, first["ebene"]), "%s (%s)" % (en, first["ebene"])
        quelle = ", ".join(sorted({e["quelle"] for e in rows if e.get("quelle")}))
        lines = ", ".join(str(e["row"]) for e in rows)
        ref = "Classeur Belastungsannahmen, %s %s%s" % ("ligne" if len(rows) == 1 else "lignes", lines, " · « %s »" % quelle if quelle else "")
        material = {"id": "ext:%d" % first["row"], "type": "other", "origin": "ext", "stored": "calc/libraries/" + WORKBOOK_FILE.name, "category": entry["category"],
                    "names": {"fr": fr, "de": de, "en": en}, "comment": first.get("info") or "", "rows": [e["row"] for e in rows],
                    "source": {"kind": "book", "ref": ref}}
        if first["mass"] > 0:
            material["weight"] = {"value": round(first["mass"] / KG_TO_KN, 6), "unit": "kN/m³" if first["unit"] == "kg/m³" else "kN/m²", "ref": ref}
        if first["material"] in _catalogue().get("includes_battens", {}):
            material["includes_battens"] = True   # the workbook's tile weighs as a line of Tabelle 29 «inkl. Lattung» (issue #111, P11)
        out.append(material)
    return out


def _weight_of(material_id, by_id):
    target = _catalogue()["weights"].get(material_id)
    if target is None:
        return None
    found = by_id.get(target)
    if found is None or not found.get("weight"):
        raise validation.ValidationError("%s: weights.%s names %r -- not a shipped material with a weight" % (CATALOGUE_FILE.name, material_id, target))
    weight = dict(found["weight"])
    weight["ref"] = "%s: %s" % (contract.name(found, "fr"), weight["ref"])
    return weight


def _family(grade):
    if grade["family"] == "Brettschichtholz":
        return "glulam"
    return "hardwood" if grade["species"] == "Laubholz" else "softwood"


def _grade_materials(by_id):
    template = _catalogue()["grades"]
    out = []
    for gid, grade in sia265.grades().items():
        table = sia265.grade_table(gid)
        values = {k: grade[k] for k in contract.MEMBER_KEYS if isinstance(grade.get(k), (int, float))}
        values["f_c_90_d"] = grade["f_c_90_d"]["generell"]   # the general value; «mit Vorholz» and the end support stay the member check's
        family = _family(grade)
        ref = "SIA 265:2021, Tabelle %s" % table
        m = {"id": "sia265:" + gid, "type": "member", "origin": "sia265", "stored": "calc/norms/%s.json" % (sia265.TAB09 if table == "9" else sia265.TAB08), "category": "wood", "family": family, "values": values,
             "names": {lang: words.replace("{id}", gid) for lang, words in template[grade["family"]].items()}, "comment": "",
             "source": {"kind": "norm", "ref": ref}, "excerpt": ["sia265-2021-materials-excerpts", "tab0%s" % table]}
        weight = _weight_of(family, by_id)
        if weight:
            m["weight"] = weight
        out.append(m)
    return out


def _panel_materials(by_id):
    names = _catalogue()["panels"]
    out = []
    for panel in sia265_1.panels():
        pid = "sia265-1:" + panel["id"]
        entry = names.get(panel["id"])
        if entry is None:
            raise validation.ValidationError("%s: panels.%s -- a panel of SIA 265/1 without its names" % (CATALOGUE_FILE.name, panel["id"]))
        ref = "SIA 265/1:2018, Tableaux %sa et %sb, p. %d" % (panel["table"], panel["table"], panel["page"])
        m = {"id": pid, "type": "panel", "origin": "sia265-1", "stored": "calc/norms/%s.json" % panel["file"], "category": "board", "names": dict(entry), "comment": "",
             "product": panel["product"], "isotropic": panel["isotropic"], "columns": panel["columns"], "thickness": None,
             "rho_k": panel["rho_k"], "grid": panel["grid"], "unavailable": panel.get("unavailable", []),
             "source": {"kind": "norm", "ref": ref}, "excerpt": ["sia265-1-2018-materials-excerpts", "tab%s" % panel["table"]]}
        if panel.get("rho_k_is_minimum"):
            m["rho_k_is_minimum"] = True
        weight = _weight_of(pid, by_id)
        if weight:
            m["weight"] = weight
        out.append(m)
    return out


def catalogue():
    """Every material Woodcore ships, in the order the list shows within a category: the classes, the panels, SIA 261, the workbook."""
    if "materials" not in _cache:
        weights = _sia261_materials() + _ext_materials()
        by_id = {m["id"]: m for m in weights}
        _cache["materials"] = _grade_materials(by_id) + _panel_materials(by_id) + weights
    return _cache["materials"]


def by_id():
    """{id: material}, every row of the workbook among them (`ALIASES`)."""
    if "by_id" not in _cache:
        out = {m["id"]: m for m in catalogue()}
        for m in catalogue():
            for row in m.get("rows", ()):
                out.setdefault("ext:%d" % row, m)
        _cache["by_id"] = out
    return _cache["by_id"]


def find(material_id):
    return by_id().get(material_id)


def ids():
    """Every shipped id -- the materials listed and the workbook's rows they merge."""
    return sorted(by_id())


def ext_id(material, ebene=""):
    """The id of the workbook's row a layer of the old shape names -- (material, Ebene), the exact pair first, else the one row of that name, as `materials.weight` has always read it."""
    rows = [e for e in _workbook() if e["material"] == material]
    exact = [e for e in rows if e["ebene"] == (ebene or "")]
    found = exact or (rows if len({(e["mass"], e["unit"]) for e in rows}) == 1 else [])
    return "ext:%d" % found[0]["row"] if found else None


def is_shipped(material_id):
    return str(material_id).split(":", 1)[0] in ORIGINS and ":" in str(material_id)
