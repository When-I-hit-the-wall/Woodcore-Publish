"""The JSON an RFEM import writes: the one intermediate format between RFEM and Woodcore.

The engineer asked for a structured JSON as the **principal intermediate format**, with the native RFEM data, the metadata he wrote, the structures detected and the results kept apart from one another. That separation is the whole of this file's design, and it is what makes each part answerable for itself: a number in `model` came out of RFEM's own table, a name in `metadata` came out of a comment he typed, a grouping in `structures` was worked out here, and `results` is what the solver produced. Nothing in one is derived from another at read time — the derivation happened once, on the way in, and this file is its record.

**Why an intermediate file at all**, when `model_tables` and `structure_detection` could hand their objects straight to the importer: because an import is a step the engineer takes and then reads. The JSON is what he can open, diff in Git beside the rest of `data/` (§1bis), and hand to a checker years later; it is also what lets the two producers — the GUI table export every user has, and the API script only a key holder has — meet at one contract. ⚠️ Two producers, one consumer, and this is the one file both must write.

**It is written into the export and never into the sources.** `data/rfem/<model>.json`, beside `data/statics.json` and the rest: it is generated, regenerated at every import, and hand-editing it would be hand-editing `data/` (§2). The engineer's own exports stay where he put them; nothing here copies or moves them.

**Versioned like every other contract** (§3.0): `schema_version` at the top, `schemas/rfem-import.schema.json` beside the others, checked before anything is written. What may be left out is stated there and not guessed at here: a model with no surface carries an empty list, and an import made without reading the results carries no `results` key at all rather than an empty one that would read as «no forces».

⚠️ **Every number is in the units this project computes in**: a length in **metres**, a section's b and h in **millimetres**, a force in **kN** and a moment in **kNm** — converted on the way in by the readers, from whatever «Unités et décimales» the model was set to. A reader of this file needs no unit table.
"""

import engine
from rfem_import import validation as rfem_validation

SCHEMA_VERSION = "1.0"

# Where an import writes, under the export's own folder. One file per RFEM model, named after it, so several models live side by side as the window lists them.
FOLDER = "rfem"


def _meta(item_or_record):
    """A `Metadata` as the file keeps it: its values, the prose it carried, and nothing else. The problems are not kept -- they are the import's to report and would be stale the moment the comment is corrected."""
    meta = item_or_record.meta
    kept = {"values": dict(meta.values)}
    if meta.text:
        kept["text"] = meta.text
    return kept


def _node(node):
    return {"no": node.no, "x": node.x, "z": node.z, **_meta(node)}


def _member(model, member):
    section = model.section_of(member)
    return {
        "no": member.no,
        "line": member.line,
        "nodes": list(member.nodes),
        "type": member.type,
        "length": member.length,
        "section": None if section is None else section.no,
        "hinge_start": member.hinge_start,
        "hinge_end": member.hinge_end,
        **_meta(member),
    }


def _surface(surface):
    return {
        "no": surface.no,
        "lines": list(surface.lines),
        "nodes": list(surface.nodes),
        "thickness": surface.thickness,
        **_meta(surface),
    }


def _section(section):
    return {
        "no": section.no, "name": section.name, "material": section.material,
        "b": section.b, "h": section.h, "members": list(section.members),
    }


def _restraint(restraint):
    return {
        "no": restraint.no, "role": restraint.role, "kind": restraint.kind,
        "nodes": list(restraint.nodes), "x": _finite(restraint.x), "z": _finite(restraint.z),
        "phi": _finite(restraint.phi), **_meta(restraint),
    }


def _finite(value):
    """`inf` as the string «inf»: JSON has no infinity, and `json.dumps` writes `Infinity`, which is not JSON and which a strict reader refuses."""
    if value is None:
        return None
    return "inf" if value == float("inf") else ("-inf" if value == float("-inf") else value)


def _load(load):
    return {
        "no": load.no, "kind": load.kind, "case": load.case,
        "members": list(load.members), "nodes": list(load.nodes),
        "type": load.type, "distribution": load.distribution, "direction": load.direction,
        "magnitude": load.magnitude, "unit": load.unit,
        **_meta(load),
    }


def _case(case):
    return {"id": case.id, "name": case.name, "category": case.category,
            "action": case.action, "duration": case.duration, **_meta(case)}


def _combination(combination):
    return {
        "id": combination.id, "name": combination.name, "situation": combination.situation,
        "terms": [{"factor": factor, "case": case} for factor, case in combination.terms],
        **_meta(combination),
    }


def _structure(structure):
    """One structure as the file keeps it: what it is, what it is made of, and what the engineer called it.

    ⚠️ It keeps **numbers and not objects**: a structure names its members, and `model` is where a member is. A structure carrying a copy of its members would be the same fact in two places, and the two would part the first time one was edited (§2 rule 1).
    """
    return {
        "key": structure.key,
        "name": structure.name,
        "statics_name": structure.statics_name,
        "statics_descr": structure.statics_descr,
        "members": structure.numbers("member"),
        "surfaces": structure.numbers("surface"),
        "nodes": list(structure.nodes),
        "supports": structure.numbers("support"),
        "loads": [{"kind": load.kind, "no": load.number, "case": load.case} for load in structure.loads],
        "cases": list(structure.cases),
        "combinations": list(structure.combinations),
        "positions": {name: [item.where for item in carriers]
                      for name, carriers in sorted(structure.positions.items())},
    }


def build(model, structures, source=None, results=None, problems=()):
    """The record one RFEM model becomes: `{schema_version, source, model, metadata, structures, results?}`.

    `source` says where it came from — the export's path, and what produced it. `results` is a `rfem_import.results.Results` or None; **absent where it is None**, so that «this import read no results» and «this model has no forces» are not one thing. `problems` are the notes the import gathered, kept so that a reader of the file knows what the import already knew.
    """
    record = {
        "schema_version": SCHEMA_VERSION,
        "source": dict(source or {}),
        "model": {
            "nodes": [_node(node) for node in model.nodes],
            "lines": {str(no): list(nodes) for no, nodes in sorted(model.lines.items())},
            "members": [_member(model, member) for member in model.members],
            "surfaces": [_surface(surface) for surface in model.surfaces],
            "sections": [_section(section) for section in model.sections],
            "materials": [{"no": m.no, "name": m.name} for m in model.materials],
            "supports": [_restraint(support) for support in model.supports],
            "hinges": [_restraint(hinge) for hinge in model.hinges],
            "cases": [_case(case) for case in model.cases],
            "combinations": [_combination(combination) for combination in model.combinations],
            "loads": [_load(load) for load in model.loads],
            "skipped": dict(model.skipped),
        },
        "metadata": {
            "keys": rfem_validation.keys_in_use(model),
            "references": rfem_validation.references(model),
        },
        "structures": [_structure(structure) for structure in structures],
        "problems": [str(note) for note in problems],
    }
    if results is not None:
        record["results"] = _results(results)
    return record


def _results(results):
    """The Schnittgrössen as the file keeps them: per loading, per member, the stations in kN and kNm.

    ⚠️ **The distribution and nothing else.** RFEM's own «Extrêmes» rows repeat a value the distribution already carries, and `ForceTable.governing` recomputes the same answer from it — so keeping them would be keeping a number twice and letting the two disagree. What is kept beside the stations is the **count** of what was left out, which is what says the file was understood rather than partly skipped (`results.py`).
    """
    kept = {}
    for loading in results.loadings:
        table = results.base(loading)
        if table is None:
            continue
        members = {}
        for member, stations in sorted(table.by_member().items()):
            members[str(member)] = [
                {"x": station.x, **{key: station.forces[key] for key in sorted(station.forces)}}
                for station in stations
            ]
        kept[loading] = {
            "kind": table.kind,
            "number": table.number,
            "members": members,
            "left_out": {"extremes": table.extremes, "summaries": table.summaries, "trailers": table.trailers},
        }
    return {"units": {"force": "kN", "moment": "kNm", "length": "m"}, "loadings": kept}


def write(record, data_dir, name):
    """Writes one import's record into `data/rfem/<name>.json`, checked first. Returns the path.

    Checked before it is written, like every other artifact of `data/` (§3.6): an import that produced something the contract does not describe writes nothing rather than a file the report would read.
    """
    from pathlib import Path

    import validation as pipeline_validation

    pipeline_validation.validate_structure(record, "rfem-import")
    folder = Path(data_dir) / FOLDER
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}.json"
    engine.write_json(path, record)
    return path


def sweep(data_dir, names):
    """Removes the records of imports the project no longer names -- a model the engineer took off the list in the RFEM tab. Returns what it removed."""
    from pathlib import Path

    folder = Path(data_dir) / FOLDER
    if not folder.is_dir():
        return []
    wanted = {f"{name}.json" for name in names}
    gone = []
    for stale in sorted(folder.iterdir()):
        if stale.is_file() and stale.name.endswith(".json") and stale.name not in wanted:
            stale.unlink()
            gone.append(stale.name)
    return gone
