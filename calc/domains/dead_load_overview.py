"""Every build-up of permanent loads of a project at a glance (spec docs/requirements/completed/2026-10-24-poids-propre-repense.md, REQ-011, UI-004, P06; issue #111): what the tab shows when no build-up is open, «⊞ Vue d'ensemble».

`overview(here)` gives, a build-up a line in the order of the files: its id and name, its number of layers, g_k, a_k, their sum, the retained value and whether it was written in place of the tenth above the sum, its state -- complete, or the number of red messages to correct (Q-007 A) -- and those red messages; the layers' model (contracts.Layer) for its small section where they can be weighed. A file that cannot be read or is malformed is a line too, its state the reason. Pure: nothing is written. No Qt here.
"""

import json

import validation
from domains import dead_load_layers, dead_load_messages, dead_load_source, materials_project


def _blank(path):
    return {"id": path.stem, "name": "", "layers": 0, "gk": None, "ak": None, "total": None, "retained": None, "replaced": False,
            "state": "complete", "to_fix": 0, "problems": [], "model": [], "malformed": None}


def _line(path, src, projects):
    where = "%s/%s" % (dead_load_source.FOLDER, path.name)
    line = _blank(path)
    if isinstance(src, dict):
        line.update(id=src.get("id") or path.stem, name=src.get("name") or "", layers=len(src.get("layers") or ()))
    try:
        dead_load_source.check_source(src, where)
        rows, problems = dead_load_messages.evaluate(src, projects, where)
    except validation.ValidationError as exc:
        line.update(state="malformed", to_fix=1, malformed=str(exc))
        return line
    line["problems"] = dead_load_messages.red(problems)
    if problems:
        line.update(state="to_fix", to_fix=len(problems))
        return line
    gk = sum(r["load"] for r in rows if r["kind"] == "gk")
    ak = sum(r["load"] for r in rows if r["kind"] == "ak")
    chosen = src.get("chosen")
    line.update(gk=gk, ak=ak, total=gk + ak, retained=chosen if chosen is not None else dead_load_layers.retained(gk + ak),
                replaced=chosen is not None, model=dead_load_source.layers_of(rows))
    return line


def overview(here=None):
    """[line] of every build-up of the project `here` -- see the module's docstring."""
    try:
        projects = materials_project.for_calculation(here)
    except validation.ValidationError:
        projects = None   # a project's materials.json that cannot be read: each build-up naming a copy says it
    out = []
    for path in dead_load_source.source_paths(here):
        try:
            src = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            out.append(dict(_blank(path), state="malformed", to_fix=1, malformed="%s/%s: cannot be read as JSON -- %s" % (dead_load_source.FOLDER, path.name, exc)))
            continue
        out.append(_line(path, src, projects))
    return out
