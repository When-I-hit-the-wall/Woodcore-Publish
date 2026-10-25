"""The copy a project keeps of the engineer's materials it names, and what Woodcore says when his library has changed since (spec docs/requirements/active/2026-10-24-onglet-materiaux.md, REQ-013, REQ-014, D-11; issue #110).

`Woodcore-Datei/materials.json` 2.0 holds, for every material of the engineer's own (`u-…`) a case of the project names, a whole copy -- names, values, weight, source -- and the PDF of its source copied beside it into `Woodcore-Datei/materials/`. The project computes from the copy alone (`materials.weight`), never from the engineer's library: it computes alike on another computer. A material Woodcore ships is not copied: it is read from the version of Woodcore that computes, as a class of SIA 265 always was.

**The copy is taken once**, when a case first names the material, and kept as it is. Woodcore compares it with the engineer's library field by field (`diff`) and says what changed: a value of the calculation (`calc`, orange) or a word (`words`, said only). The engineer takes the new version (`take`), keeps the copy (`keep` -- the fingerprint of the version refused is written into the copy, `kept_fingerprint`, so that the warning is not said again until the library changes once more), or, for a material his library lacks -- a project from another computer --, adds it to his library (`add_to_library`). Numbers are compared with a relative tolerance of 1e-9, never `==` on floats read back.

The writers here write into the project: the tab that calls them is guarded (tab_guard). No Qt here.
"""

import copy
import json
import shutil
from pathlib import Path

import engine
import project
import validation
from domains import materials, materials_contract as contract, materials_user

# The fields that change a calculation, and those that change only words (D-11).
CALC_FIELDS = ("type", "family", "values", "product", "isotropic", "columns", "thickness", "rho_k", "grid", "weight.value", "weight.unit")
WORD_FIELDS = ("names", "category", "comment", "source", "weight.ref")
PDF_FOLDER = "materials"
TOLERANCE = 1e-9


def _here(here):
    return here or project.current()


def read(here=None):
    """The project's materials.json, checked; 1.0 as it is, 2.0 the copies -- empty 2.0 where there is none."""
    return materials.read_project(_here(here))


def copies(here=None):
    """The copies of the engineer's materials the project keeps (2.0) -- none in a 1.0 file."""
    data = read(here)
    return data["materials"] if data["schema_version"] == "2.0" else []


def find(material_id, here=None):
    return next((m for m in copies(here) if m["id"] == material_id), None)


def for_calculation(here=None):
    """What a calculation of the project weighs its layers with (`materials.weight`'s `projects`): the project's file -- its copies, or its 1.0 entries --, and, for one of the engineer's materials a draft names before its case is first saved, the library's version (`materials_project.sync` takes its copy at the save, before the export: `dead_load_source.before_export`). A copy, where there is one, always wins over the library."""
    data = read(here)
    have = {m["id"] for m in data["materials"]}
    try:
        extra = [m for m in materials_user.materials() if m["id"] not in have]
    except validation.ValidationError:
        extra = []   # a library that cannot be read is the «Matériaux» tab's to say; the project computes from its copies
    return {"schema_version": data["schema_version"], "materials": data["materials"] + extra}


def used_ids(here=None):
    """The ids of the engineer's materials the project's cases name -- the build-ups of the permanent loads, and the member checks (issue #112, REQ-002: a check naming a member or a panel of one's own computes from the project's copy, as a layer does)."""
    from domains import dead_load_source, member_check
    out = []
    for path in dead_load_source.source_paths(_here(here)):
        try:
            src = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue   # a source that cannot be read is the export's to name
        out.extend(dead_load_source.used_materials(src))
    for src in member_check.list_sources(_here(here)):
        mid = src.get("material")
        if isinstance(mid, str) and contract.USER_ID.match(mid):
            out.append(mid)
    return list(dict.fromkeys(out))


def _get(m, path):
    node = m
    for part in path.split("."):
        node = node.get(part) if isinstance(node, dict) else None
    return node


def _same(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= TOLERANCE * max(abs(a), abs(b), 1.0)
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(_same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    return a == b


def _leaves(node, path=""):
    """{dotted path: value} of every leaf under `node` -- so that a change says which value, not which block."""
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            out.update(_leaves(v, "%s.%s" % (path, k) if path else k))
        return out or {path: {}}
    if isinstance(node, list) and any(isinstance(x, (dict, list)) for x in node):
        out = {}
        for i, v in enumerate(node):
            out.update(_leaves(v, "%s[%d]" % (path, i)))
        return out
    return {path: node}


def diff(copy_, original):
    """What differs between a project's copy and the library's material: [(field, level, before, after)] -- `calc` for a value of the calculation, `words` for a name, a comment, a source. The copy's own bookkeeping (`kept_fingerprint`) is not compared."""
    out = []
    for fields, level in ((CALC_FIELDS, "calc"), (WORD_FIELDS, "words")):
        for f in fields:
            a, b = _get(copy_, f), _get(original, f)
            if _same(a, b):
                continue
            la, lb = _leaves(a, f) if isinstance(a, (dict, list)) else {f: a}, _leaves(b, f) if isinstance(b, (dict, list)) else {f: b}
            for key in sorted(set(la) | set(lb)):
                if not _same(la.get(key), lb.get(key)):
                    out.append((key, level, la.get(key), lb.get(key)))
    return out


def fingerprint(material):
    """The SHA-256 of a material's calculation fields, written canonically -- what «Garder la copie» records of the version it refused."""
    return engine.digest(*[_get(material, f) for f in CALC_FIELDS])


def warnings(here=None, used=None):
    """What the cases that name the engineer's materials are told: [{id, name, kind, changes}] -- `changed` where the library's version differs from the copy in a value of the calculation and was not refused (`keep`), `words` where only words differ, `absent` where the library has no such material (another computer). `used` limits it to those ids."""
    out = []
    try:
        library = {m["id"]: m for m in materials_user.materials()}
    except validation.ValidationError:
        library = {}
    for c in copies(here):
        if used is not None and c["id"] not in used:
            continue
        original = library.get(c["id"])
        if original is None:
            out.append({"id": c["id"], "name": c["names"], "kind": "absent", "changes": []})
            continue
        changes = diff(c, original)
        if not changes:
            continue
        calc = [x for x in changes if x[1] == "calc"]
        if calc and c.get("kept_fingerprint") == fingerprint(original):
            calc = []
        if calc:
            out.append({"id": c["id"], "name": c["names"], "kind": "changed", "changes": calc})
        elif any(x[1] == "words" for x in changes):
            out.append({"id": c["id"], "name": c["names"], "kind": "words", "changes": [x for x in changes if x[1] == "words"]})
    return out


def _pdf_dir(here):
    return _here(here).sources_dir / PDF_FOLDER


def _copy_of(material, here):
    """A copy of the library's `material` for the project: its PDF copied into Woodcore-Datei/materials/, its source naming that copy."""
    m = copy.deepcopy(material)
    m.pop("kept_fingerprint", None)
    pdf = materials_user.source_path(material)
    if pdf is not None:
        target = _pdf_dir(here) / Path(pdf).name
        if pdf.is_file() and (not target.is_file() or target.read_bytes() != pdf.read_bytes()):
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(pdf, target)
        m["source"] = dict(m["source"], file="%s/%s" % (PDF_FOLDER, Path(pdf).name))
    return m


def pdf_path(material, here=None):
    """The PDF of a project's copy, in Woodcore-Datei/materials/, or None."""
    rel = (material.get("source") or {}).get("file")
    return _here(here).sources_dir / rel if rel else None


def _write(data, here):
    materials.check_project(data)
    engine.write_json(materials.project_file(_here(here)), data)


def sync(used, here=None):
    """The project's copies made to follow `used` -- the ids of the engineer's materials its cases name, at a save: a copy taken of each that has none, from the engineer's library (refused, naming it, where the library lacks it too); a copy no case names any more removed with its PDF. An existing copy is never changed here. Returns the ids copied."""
    here = _here(here)
    data = read(here)
    if data["schema_version"] == "1.0" and data["materials"]:
        # weights typed in the project until v0.125, not yet poured into the library (a project opened read only): never written over
        if not used:
            return []
        raise validation.ValidationError("the project's materials.json is still at 1.0, its materials typed in the project -- open the project writable once, which moves them into your library")
    kept = data["materials"] if data["schema_version"] == "2.0" else []
    have = {m["id"]: m for m in kept}
    library = None
    added = []
    for mid in dict.fromkeys(used):
        if mid in have:
            continue
        if library is None:
            library = {m["id"]: m for m in materials_user.materials()}
        if mid not in library:
            raise validation.ValidationError("material %r is neither in the project's copies nor in the engineer's library -- choose another material for the layer" % mid)
        have[mid] = _copy_of(library[mid], here)
        added.append(mid)
    keep = [have[mid] for mid in have if mid in set(used)]
    gone = [m for m in kept if m["id"] not in set(used)]
    if not added and not gone and data["schema_version"] == "2.0":
        return []
    _write({"schema_version": materials.PROJECT_SCHEMA_VERSION, "materials": keep}, here)
    named = {(m.get("source") or {}).get("file") for m in keep}
    for m in gone:
        pdf = (m.get("source") or {}).get("file")
        if pdf and pdf not in named:
            try:
                (here.sources_dir / pdf).unlink()
            except OSError:
                pass
    return added


def _replace(material_id, new, here):
    data = read(here)
    data["materials"] = [new if m["id"] == material_id else m for m in data["materials"]]
    _write(data, here)


def take(material_id, here=None):
    """«Reprendre la nouvelle version»: the copy replaced by the library's material."""
    here = _here(here)
    original = materials_user.find(material_id)
    if original is None or find(material_id, here) is None:
        raise validation.ValidationError("material %r: no copy in the project or no such material in the library" % material_id)
    _replace(material_id, _copy_of(original, here), here)


def keep(material_id, here=None):
    """«Garder la copie»: the copy kept, the library's version recorded as refused -- the warning is not said again until the library changes once more."""
    here = _here(here)
    original = materials_user.find(material_id)
    current = find(material_id, here)
    if original is None or current is None:
        raise validation.ValidationError("material %r: no copy in the project or no such material in the library" % material_id)
    _replace(material_id, dict(current, kept_fingerprint=fingerprint(original)), here)


def add_to_library(material_id, here=None):
    """«Ajouter à ma bibliothèque»: a copy the engineer's library lacks -- a project of another computer -- added to it under its own id, its PDF copied into the library's sources."""
    here = _here(here)
    current = find(material_id, here)
    if current is None:
        raise validation.ValidationError("material %r: no copy in the project" % material_id)
    m = copy.deepcopy(current)
    m.pop("kept_fingerprint", None)
    pdf = pdf_path(current, here)
    if pdf is not None and pdf.is_file():
        m["source"] = dict(m["source"], file=materials_user.import_pdf(pdf))
    materials_user.save(m)
    return m
