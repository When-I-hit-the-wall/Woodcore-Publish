"""Permanent loads entered in Woodcore (issue #35): a build-up of layers, one source file each, weighed with the libraries of `materials` and summed by `dead_load.instance_from_layers` -- the same arithmetic as an `EL+AL-*` sheet, which stays read beside it (docs/domain/loads.md §3.3ter, decision D-04).

**A source** is `Woodcore-Datei/loads/dead/<id>.json` (schemas/dead-load-source.schema.json, 1.0): its id, name, label and group, its layers top to bottom, and the chosen value (`chosen`, kN/m², null for the sum). **A layer** names
  * `kind` -- `gk` (Eigenlast, poids propre) or `ak` (Auflast, surcharge): the engineer's choice for each one (T4);
  * `library` and `material` -- a line of SIA 261 Anhang A (`sia261`, its id), of Woodcore's materials library (`belastungsannahmen`, its name, with its `ebene`), or of the project's (`project`, its id) -- or `direct`, a load typed in kN/m² (`load`), as the workbook takes «Installationen und Innenwände»;
  * `thickness` in mm -- what a weight per volume is multiplied by, and what the drawing stacks;
  * `width` and `spacing` in mm -- battens, rafters, joists: the layer weighs width/spacing of a full one; both null for a continuous layer;
  * `beside` -- true where the layer shares the band of the one above it (the insulation between the rafters): drawn in the gaps, summed like any other.

The load of a layer is weight · thickness · width/spacing (a weight per surface without the thickness); kg go to kN with g = 10 m/s², the workbook's own conversion (materials.KG_TO_KN). A malformed source stops the export naming the file and the field; nothing here is the project's to lack. No Qt here.
"""

import json
import re
from pathlib import Path

import project
import validation
from domains import links  # a field that follows a variable of the export (spec 2026-10-11-variables-liees-champs-et-textes)
from domains import dead_load, dead_load_svg, materials

DOMAIN = dead_load.DOMAIN
SOURCE_SCHEMA = "dead-load-source"
SOURCE_SCHEMA_VERSION = "1.0"
# 1.1 is 1.0 with `links` (spec 2026-10-11-variables-liees-champs-et-textes, D-17): written only by a source that carries one, so a load following no variable is saved and exported as before
LINKED_SCHEMA_VERSION = "1.1"
SOURCE_SCHEMA_VERSIONS = (SOURCE_SCHEMA_VERSION, LINKED_SCHEMA_VERSION)
# The fields a variable may fill (REQ-009, issue #42) -- the chosen value and each layer's thickness, width, spacing and load --, with the unit each is written in. A load follows only another load or a «Formule» domain, the loads being computed first (links.LOADS, D-11). The lists take none.
LINKABLE = {links.SELF: {"chosen": "kN/m²"}, "layers": {"thickness": "mm", "width": "mm", "spacing": "mm", "load": "kN/m²"}}
# The folder of the project's sources, under Woodcore-Datei (project.SOURCE_FOLDERS holds `loads`)
FOLDER = "loads/dead"
SOURCE = "python:domains/dead_load_source.py"
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$")
KINDS = dead_load.KINDS
LIBRARIES = materials.LIBRARIES + ("direct",)

# What the table says under the layers (a glossary term: a French report says it in French)
NOTE = ("Last je Schicht = Wichte · Dicke · Breite / Abstand; eine Flächenlast ohne die Dicke. "
        "Gewichte in kg werden mit g = 10 m/s² in kN umgerechnet.")


def _fail(where, message):
    raise validation.ValidationError("%s: %s" % (where, message))


def _number(value):
    return not isinstance(value, bool) and isinstance(value, (int, float))


def folder(here=None):
    return (here or project.current()).sources_dir / FOLDER


def source_paths(here=None):
    directory = folder(here)
    return sorted(directory.glob("*.json")) if directory.is_dir() else []


def new_source(cid):
    """A build-up with one layer of 27 mm three-ply board, the chosen value left to the sum."""
    return {"schema_version": SOURCE_SCHEMA_VERSION, "id": cid, "name": "", "label": "", "group": "",
            "layers": [new_layer()], "chosen": None}


def new_layer():
    return {"kind": "gk", "library": "sia261", "material": "holz_nadelhoelzer_allgemein", "ebene": "", "thickness": 27,
            "width": None, "spacing": None, "beside": False, "load": None}


def stamp_version(src):
    """The schema_version a source is saved at: 1.1 where a field follows a variable, 1.0 where none does -- what Woodcore's window calls before it writes one."""
    src["schema_version"] = LINKED_SCHEMA_VERSION if links.is_linked(src, LINKABLE) else SOURCE_SCHEMA_VERSION
    return src


def check_source(src, where="loads/dead"):
    """What makes a source malformed, as a ValidationError naming `where` and the field -- the layer's material included, a library being part of the program."""
    if not isinstance(src, dict):
        _fail(where, "a build-up is a JSON object")
    if src.get("schema_version") not in SOURCE_SCHEMA_VERSIONS:
        _fail(where, "schema_version is %r -- this reads %s" % (src.get("schema_version"), ", ".join(SOURCE_SCHEMA_VERSIONS)))
    if links.is_linked(src, LINKABLE) and src.get("schema_version") != LINKED_SCHEMA_VERSION:
        _fail(where, "follows a variable at schema_version %r -- a load with links is %r" % (src.get("schema_version"), LINKED_SCHEMA_VERSION))
    links.check_all(src, LINKABLE, lambda message: _fail(where, message), "the build-up", links.LOADS)
    try:
        validation.validate_structure(src, SOURCE_SCHEMA)
    except validation.ValidationError as exc:
        _fail(where, str(exc))      # the file named, as every refusal here names it
    if not ID_PATTERN.match(src.get("id") or ""):
        _fail(where, "id %r -- letters, digits and _ . + - only, starting with a letter or digit" % src.get("id"))
    if not src["layers"]:
        _fail(where, "layers is empty -- a build-up has one layer at least")
    chosen = src.get("chosen")
    if chosen is not None and (not _number(chosen) or chosen <= 0):
        _fail(where, "chosen is %r -- the permanent load designed with, kN/m², above 0, or null for the sum" % (chosen,))
    for i, layer in enumerate(src["layers"]):
        at = "%s: layers[%d]" % (where, i)
        if layer.get("kind") not in KINDS:
            _fail(at, "kind %r -- gk (Eigenlast) or ak (Auflast)" % (layer.get("kind"),))
        if layer.get("library") not in LIBRARIES:
            _fail(at, "library %r -- %s" % (layer.get("library"), ", ".join(LIBRARIES)))
        for key in ("thickness", "width", "spacing"):
            value = layer.get(key)
            if value is not None and (not _number(value) or value <= 0):
                _fail(at, "%s is %r -- in mm, above 0, or null" % (key, value))
        if (layer.get("width") is None) != (layer.get("spacing") is None):
            _fail(at, "width and spacing go together -- both for battens at a spacing, neither for a continuous layer")
        if layer.get("width") is not None and layer["width"] > layer["spacing"]:
            _fail(at, "width %s mm is above the spacing %s mm" % (layer["width"], layer["spacing"]))
        if i == 0 and layer.get("beside"):
            _fail(at, "beside is true on the first layer -- it shares the band of the layer above it, and there is none")
        if layer["library"] == "direct":
            if not _number(layer.get("load")) or layer["load"] <= 0:
                _fail(at, "load is %r -- a load typed in kN/m², above 0" % (layer.get("load"),))
            continue
        if not str(layer.get("material") or "").strip():
            _fail(at, "no material")


def read_source(path):
    path = Path(path)
    where = "%s/%s" % (FOLDER, path.name)
    try:
        src = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _fail(where, "cannot be read as JSON -- %s" % exc)
    check_source(src, where)
    if src["id"] != path.stem:
        _fail(where, "id %r is not its file name %r -- the id is the file name" % (src["id"], path.stem))
    return src


def list_sources(here=None):
    """Every source as a dict, by file name, unchecked -- what the window lists."""
    out = []
    for path in source_paths(here):
        try:
            src = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(src, dict):
            out.append(src)
    return out


def layer_rows(src, projects=None, where="loads/dead"):
    """The layers as `dead_load.instance_from_layers` reads them -- lengths in m, the weight in its unit, the load in kN/m² -- each also carrying what the drawing reads (`thickness`, `width`, `spacing` in mm, `beside`, `label`). A material a library lacks stops, naming the layer."""
    rows = []
    for i, layer in enumerate(src["layers"]):
        at = "%s: layers[%d]" % (where, i)
        base = {"kind": layer["kind"], "ebene": layer.get("ebene") or "", "thickness": layer.get("thickness"),
                "width": layer.get("width"), "spacing": layer.get("spacing"), "beside": bool(layer.get("beside"))}
        share = layer["width"] / layer["spacing"] if layer.get("spacing") else 1.0
        if layer["library"] == "direct":
            rows.append({**base, "material": dead_load.DIRECT_LOAD, "label": layer.get("material") or dead_load.DIRECT_LOAD,
                         "dicke": None, "breite": None, "dist": None, "mass": None, "unit": "", "load": float(layer["load"]) * share,
                         "source": "entered"})
            continue
        try:
            value, unit, label, source = materials.weight(layer, projects)
        except validation.ValidationError as exc:
            _fail(at, str(exc))
        if materials.per_volume(unit) and not layer.get("thickness"):
            _fail(at, "%s weighs %s %s, per volume -- it needs its thickness" % (label, value, unit))
        thickness = (layer.get("thickness") or 0) / 1000.0
        load = materials.to_kn(value, unit) * (thickness if materials.per_volume(unit) else 1.0) * share
        rows.append({**base, "material": label, "label": label,
                     "dicke": thickness if materials.per_volume(unit) else None,
                     "breite": layer["width"] / 1000.0 if layer.get("width") else None,
                     "dist": layer["spacing"] / 1000.0 if layer.get("spacing") else None,
                     "mass": value, "unit": unit, "load": load, "source": source})
    return rows


def build_instance(src, here=None):
    """One instance of `dead-load` from a source: the sums, the chosen value and the table, `dead_load.instance_from_layers`'s; refused, naming the field, where the chosen value is below the sum (the workbook's rule, dead_load._check_chosen)."""
    where = "%s/%s.json" % (FOLDER, src["id"])
    rows = layer_rows(src, materials.read_project(here), where)
    total = sum(r["load"] for r in rows)
    chosen = src.get("chosen")
    if chosen is not None and total > 0 and chosen < total * (1 - dead_load.CHOSEN_TOLERANCE):
        _fail(where, "chosen is %.3f kN/m², below the %.3f kN/m² its own layers add up to -- round up, never down" % (chosen, total))
    instance = dead_load.instance_from_layers(rows, chosen, "entered:%s, chosen" % where,
                                              "Auf der sicheren Seite gerundeter Bemessungswert der ständigen Lasten.", source=SOURCE, note=NOTE)
    for row, layer in zip(instance["tables"][0]["rows"], rows):
        if layer["dicke"] is None and layer["mass"] is not None:
            row[3] = ""      # a weight per surface: no thickness in the sum (the drawing still shows it)
        if layer["breite"] is None and layer["mass"] is not None:
            row[4] = row[5] = ""
    # UI-002, UI-003: the build-up drawn, printed by show-calc above its table and shown by the tab
    rel = "calculations/%s-%s.svg" % (DOMAIN, src["id"])
    instance["figures"] = [{"file": rel, "title": "Schichtaufbau", "level": 2}]
    instance["_files"] = {rel: dead_load_svg.render(rows)}
    return instance
