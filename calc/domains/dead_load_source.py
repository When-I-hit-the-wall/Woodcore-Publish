"""Permanent loads entered in Woodcore (issue #35, redesigned by issue #111): a build-up of layers, one source file each, weighed with the materials of `materials` and summed by `dead_load.instance_from_layers` -- the same arithmetic as an `EL+AL-*` sheet, which stays read beside it (docs/domain/loads.md §3.3ter, decision D-04).

**A source** is `Woodcore-Datei/loads/dead/<id>.json` (schemas/dead-load-source.schema.json, 2.0): its id, name, label and group, its layers top to bottom, and the retained value (`chosen`, kN/m², null for the tenth above the sum, `dead_load_layers.retained`). **A layer** (spec 2026-10-24-poids-propre-repense, REQ-001) names
  * `kind` -- `gk` (Eigenlast, poids propre) or `ak` (Auflast, surcharge): the engineer's choice for each one;
  * `pose` -- `continuous`, `spaced`, `surface` or `typed` (dead_load_layers.POSES), and `material`, a material's id (materials_catalogue, the engineer's `u-…`), none for `typed`, whose words are its `label`;
  * `thickness`, and for a spaced layer `width` and `spacing`, in mm;
  * `link` -- true where the layer shares its level with the one below (the rafters and the insulation between them, two lines at most, D-07); the line that is not spaced fills the gap the pieces leave (`fill`, the default), or the `width` it is given;
  * `role` -- what the layer is for, optional (dead_load_layers.ROLES);
  * `load` -- the load typed of a `typed` layer, or the load that replaces the calculation of any other (ARCH-006), a number or a link (`links.load`).

Sources written before issue #111 (1.0 to 1.2: `library`, `ebene`, `beside`) are read through `dead_load_migrate.upgrade`, in memory: nothing is rewritten on reading, the window writes 2.0 at the next save. A malformed source stops the export naming the file and the field; nothing here is the project's to lack. No Qt here.
"""

import json
import re
from pathlib import Path

import engine
import project
import validation
from domains._common import fail as _fail, is_number as _number  # one copy of the domains' helpers (spec 2026-10-19-base-saine-nettoyage, G4)
from domains import links  # a field that follows a variable of the export (spec 2026-10-11-variables-liees-champs-et-textes)
from domains import dead_load, dead_load_layers, dead_load_messages, dead_load_migrate, dead_load_svg, materials, materials_project
from domains.contracts import Layer

DOMAIN = dead_load.DOMAIN
SOURCE_SCHEMA = "dead-load-source"
# 2.0 (issue #111): a layer's pose, a material by its id, `link` to the line below in place of `beside`, `fill`, `role` -- a change 1.x cannot carry (D-05), read through dead_load_migrate
SOURCE_SCHEMA_VERSION = dead_load_migrate.VERSION
# What was written before: 1.0; 1.1 with `links` (D-17); 1.2 with a layer naming a material by its id (`library: "catalogue"`, issue #110)
OLD_SCHEMA_VERSIONS = ("1.0", "1.1", "1.2")
SOURCE_SCHEMA_VERSIONS = OLD_SCHEMA_VERSIONS + (SOURCE_SCHEMA_VERSION,)
# The fields a variable may fill (REQ-009, issue #42) -- the chosen value and each layer's thickness, width, spacing and load --, with the unit each is written in. A load follows only another load or a «Formule» domain, the loads being computed first (links.LOADS, D-11). The lists take none.
LINKABLE = {links.SELF: {"chosen": "kN/m²"}, "layers": {"thickness": "mm", "width": "mm", "spacing": "mm", "load": "kN/m²"}}
# The folder of the project's sources, under Woodcore-Datei (project.SOURCE_FOLDERS holds `loads`)
FOLDER = "loads/dead"
SOURCE = "python:domains/dead_load_source.py"
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$")
KINDS = dead_load.KINDS
# The libraries a 1.x layer named (dead_load_migrate reads them)
LIBRARIES = materials.LIBRARIES + ("direct",)

# What the table says under the layers (a glossary term: a French report says it in French)
NOTE = ("Last je Schicht = Wichte · Dicke · Breite / Abstand; eine Flächenlast ohne die Dicke. "
        "Gewichte in kg werden mit g = 10 m/s² in kN umgerechnet.")

def folder(here=None):
    return (here or project.current()).sources_dir / FOLDER


def source_paths(here=None):
    directory = folder(here)
    return sorted(directory.glob("*.json")) if directory.is_dir() else []


def new_source(cid):
    """A build-up with one layer of 27 mm softwood, the retained value left to the sum -- at 2.0."""
    return {"schema_version": SOURCE_SCHEMA_VERSION, "id": cid, "name": "", "label": "", "group": "",
            "layers": [new_layer()], "chosen": None}


def new_layer():
    """A layer of 27 mm softwood, its material named by its id (issue #110): what the window adds."""
    return {"kind": "gk", "pose": "continuous", "material": "sia261:holz_nadelhoelzer_allgemein", "label": "", "thickness": 27,
            "width": None, "spacing": None, "link": False, "fill": True, "role": None, "load": None}


def stamp_version(src):
    """The schema_version a source is saved at: 2.0, what Woodcore's window writes (issue #111) -- what it calls before it writes one."""
    src["schema_version"] = SOURCE_SCHEMA_VERSION
    return src


def upgraded(src, where="loads/dead", projects=None):
    """`src` as 2.0, in memory (dead_load_migrate.upgrade): itself where it is 2.0 already."""
    return dead_load_migrate.upgrade(src, where, projects)


def used_materials(src):
    """The engineer's own materials (`u-…`) the layers of `src` name -- what the project keeps a copy of; a source of any version."""
    from domains import materials_contract
    ids = (layer.get("material") if src.get("schema_version") == SOURCE_SCHEMA_VERSION else dead_load_migrate.material_id(layer)
           for layer in src.get("layers") or ())
    return [m for m in ids if materials_contract.USER_ID.match(str(m or ""))]


def check_source(src, where="loads/dead"):
    """What makes a source malformed, as a ValidationError naming `where` and the field. A 1.x source is checked as it was written, then read as 2.0 (dead_load_migrate) and checked again."""
    if not isinstance(src, dict):
        _fail(where, "a build-up is a JSON object")
    version = src.get("schema_version")
    if version not in SOURCE_SCHEMA_VERSIONS:
        _fail(where, "schema_version is %r -- this reads %s" % (version, ", ".join(SOURCE_SCHEMA_VERSIONS)))
    if version == "1.0" and links.is_linked(src, LINKABLE):
        _fail(where, "follows a variable at schema_version %r -- a load with links is %r or later" % (version, "1.1"))
    if version in ("1.0", "1.1") and any(isinstance(layer, dict) and layer.get("library") == "catalogue" for layer in src.get("layers") or ()):
        _fail(where, "names a material by its id (library «catalogue») at schema_version %r -- such a build-up is %r or later" % (version, "1.2"))
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
        _fail(where, "chosen is %r -- the permanent load designed with, kN/m², above 0, or null for the tenth above the sum" % (chosen,))
    if version != SOURCE_SCHEMA_VERSION:
        _check_old_layers(src, where)
        src = upgraded(src, where)
    _check_layers(src["layers"], where)


def _check_layers(layers, where):
    """The layers of a 2.0 source: each one's kind, pose, numbers and role; the links the rule of two allows (D-07)."""
    for i, layer in enumerate(layers):
        at = "%s: layers[%d]" % (where, i)
        if layer.get("kind") not in KINDS:
            _fail(at, "kind %r -- gk (Eigenlast) or ak (Auflast)" % (layer.get("kind"),))
        if layer.get("pose") not in dead_load_layers.POSES:
            _fail(at, "pose %r -- %s" % (layer.get("pose"), ", ".join(dead_load_layers.POSES)))
        for key in ("thickness", "width", "spacing"):
            value = layer.get(key)
            if value is not None and (not _number(value) or value <= 0):
                _fail(at, "%s is %r -- in mm, above 0, or null" % (key, value))
        if layer.get("spacing") is not None and layer["pose"] != "spaced":
            _fail(at, "spacing is %r on a layer of pose %r -- only a spaced layer has one" % (layer["spacing"], layer["pose"]))
        role = layer.get("role")
        if role is not None and role not in dead_load_layers.ROLES:
            _fail(at, "role %r -- %s, or null" % (role, ", ".join(dead_load_layers.ROLES)))
        load = layer.get("load")
        if load is not None and (not _number(load) or load <= 0):
            _fail(at, "load is %r -- a load in kN/m², above 0, or null" % (load,))
        if layer["pose"] == "typed":
            if layer.get("material") is not None:
                _fail(at, "material %r on a load typed -- its words are its label" % (layer["material"],))
        if layer.get("link") and i == len(layers) - 1:
            _fail(at, "link is true on the last layer -- it shares the level of the line below it, and there is none")
    for index, code in dead_load_layers.level_problems(layers):
        _fail("%s: layers[%d]" % (where, index), dead_load_messages.LEVEL_TEXT[code])


def _check_old_layers(src, where):
    """The layers of a 1.x source as it was written: what the reader before issue #111 refused, refused still."""
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
    """A source read and checked -- a 1.x file as it is, read as 2.0 by `layer_rows` (dead_load_migrate, in memory: never rewritten on reading)."""
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
    """The layers as `dead_load.instance_from_layers` reads them -- lengths in m, the weight in its unit, the load in kN/m² -- each also carrying what the drawing and the pane read (`thickness`, `width`, `spacing` in mm, `pose`, `link`, `fill_width`, `air`, `role`, `number`, `label`, the `formula` of its load, the load `computed` and whether a load written `replaced` it). A 1.x source is read as 2.0 first. A layer that cannot be weighed -- no material, one the libraries lack, a number its pose needs missing, a level the rule of two refuses -- stops, naming the layer: the first problem of `dead_load_messages.evaluate`, which the tab says in red."""
    rows, problems = dead_load_messages.evaluate(src, projects, where)
    for problem in problems:
        if problem.index is not None:
            raise validation.ValidationError(problem.text)
    return rows


def layers_of(rows):
    """The model of a build-up's layers (contracts.Layer) from `layer_rows`'s rows: what its drawing reads, and the one thing a service that draws layers will ask (spec 2026-10-23-onglets-types-et-services, ARCH-007, D-14; spec 2026-10-24-poids-propre-repense, ARCH-003)."""
    return [Layer(id=str(r["number"]), kind=r["kind"], thickness=r["thickness"], width=r["width"], spacing=r["spacing"], link=r["link"],
                  label=r["label"], ebene=r["ebene"], pose=r["pose"], fill_width=r["fill_width"], air=r["air"], role=r["role"], number=r["number"])
            for r in rows]


def layers(src, here=None):
    """The layers of the build-up `src` (contracts.Layer), its materials read from the libraries and the project's own; a material a library lacks stops, naming `layers[i]` as `layer_rows` does. No Qt."""
    return layers_of(layer_rows(src, materials_project.for_calculation(here), "%s/%s.json" % (FOLDER, src.get("id"))))


_drawn_last = [None, None]   # the last build-up drawn and its SVG: the export's drawing and the tab's are one, drawn once a keystroke


def _drawn(model):
    """The SVG of the layers `model` -- drawn again only where they changed since the last one, so that the tab's drawing (`figure_svg`) is the one `build_instance` just made."""
    key = tuple(model)
    if _drawn_last[0] != key:
        _drawn_last[:] = [key, dead_load_svg.render(model)]
    return _drawn_last[1]


def figure_svg(src, lang=None):
    """The drawing of the build-up the tab shows -- the one the export prints above its table, one code and no word of a language (`lang` unused)."""
    return _drawn(layers(src, project.current()))


def messages(src):
    """What the tab says of a build-up beside its calculation (contracts.Message): what its layers say -- red where one stops, orange where a value was replaced or a layer asks a look, information, green where every layer has its weight (dead_load_messages, REQ-007 of the spec 2026-10-24-poids-propre-repense) --, and, in orange, a material of the engineer's own whose library has changed since the project took its copy, or that this computer's library lacks (spec 2026-10-24-onglet-materiaux, REQ-014): the card «Matériaux de la bibliothèque» offers what to do."""
    from domains.contracts import Message
    here = project.current()
    try:
        projects = materials_project.for_calculation(here)
    except validation.ValidationError:
        return []   # a project's materials.json that cannot be read stops the calculation, said by its check
    try:
        out = dead_load_messages.messages(src, projects, "%s/%s.json" % (FOLDER, src.get("id")))
    except validation.ValidationError:
        out = []    # a level of before the rule of two refuses: its check says it
    used = used_materials(src)
    if not used:
        return out
    try:
        said = materials_project.warnings(here, set(used))
    except validation.ValidationError:
        return out
    for w in said:
        if w["kind"] == "words":
            continue
        name = w["name"].get("fr") or next(iter(w["name"].values()), w["id"])
        changes = "; ".join("%s %s → %s" % (field, _shown(before), _shown(after)) for field, _level, before, after in w["changes"])
        out.append(Message("material_" + w["kind"], None, "info", {"name": name, "changes": changes}))
    return out


def _shown(value):
    return "—" if value is None else ("%g" % value if isinstance(value, float) else str(value))


def before_export(here):
    """What a save does between writing the case and computing the export (SourceStore.save): the project's copies of the engineer's materials made to follow what its build-ups name -- a copy taken of a material newly named, one no build-up names any more removed (materials_project.sync, REQ-013)."""
    return materials_project.sync(materials_project.used_ids(here), here)


# --- what the tab's services ask (spec 2026-10-24-poids-propre-repense, UI-001 to UI-004): each the domain's one function, no Qt ---

def rows(src, here=None):
    """The layers of `src` as `layer_rows` gives them, weighed with the project's materials -- or, where a layer cannot be weighed, as far as `dead_load_messages.evaluate` gets (its `load` None): what the table of the layers shows beside each line, its computed load and its formula."""
    return dead_load_messages.evaluate(src, materials_project.for_calculation(here), "%s/%s.json" % (FOLDER, src.get("id")))[0]


def contributions(src, here=None):
    """(lists, totals) of what each layer weighs, g_k alone, a_k alone, the two (REQ-008, dead_load_layers.contributions); ({}, {}) where a layer cannot be weighed."""
    found, problems = dead_load_messages.evaluate(src, materials_project.for_calculation(here), "%s/%s.json" % (FOLDER, src.get("id")))
    return ({}, {}) if problems else dead_load_layers.contributions(found)


def section_svg(model, width=None, legend=None):
    """The section of the layers `model` (contracts.Layer) at `width` units (dead_load_svg.render): what the tab draws at the width it has, a template's card and the overview at theirs."""
    return dead_load_svg.render(model, width, legend)


def section_boxes(model, width=None, legend=None):
    """[(layer number, x, y, w, h)] of the section at `width` (dead_load_svg.hit_boxes): what a click on it opens."""
    return dead_load_svg.hit_boxes(model, width, legend)


def overview(here=None):
    """Every build-up of the project at a glance (dead_load_overview.overview, REQ-011)."""
    from domains import dead_load_overview
    return dead_load_overview.overview(here)


def templates():
    """(Woodcore's templates, the engineer's own, the files of his that cannot be read) -- dead_load_templates (REQ-010)."""
    from domains import dead_load_templates
    mine, problems = dead_load_templates.mine()
    return dead_load_templates.shipped(), mine, problems


def template_summary(template, here=None):
    from domains import dead_load_templates
    return dead_load_templates.summary(template, materials_project.for_calculation(here))


def from_template(template, cid, lang="fr"):
    from domains import dead_load_templates
    return dead_load_templates.to_source(template, cid, lang)


def save_template(src, words, lang):
    from domains import dead_load_templates
    return dead_load_templates.save_mine(src, words, lang)


def delete_template(tid):
    from domains import dead_load_templates
    dead_load_templates.delete_mine(tid)


def template_name(template, lang):
    from domains import dead_load_templates
    return dead_load_templates.name(template, lang)


def results(instance):
    """What «Résultats» lists: every value of the instance -- g_k, a_k, their sum and the chosen value --, the layers being its table."""
    return list(instance["vars"])


def build_instance(src, here=None):
    """One instance of `dead-load` from a source: the sums, the retained value and the table, `dead_load.instance_from_layers`'s. The retained value is always there (REQ-005): written, or the tenth above or equal to the sum (`dead_load_layers.retained`); refused, naming the field, where a value written is below the sum (the workbook's rule, dead_load._check_chosen)."""
    where = "%s/%s.json" % (FOLDER, src["id"])
    rows, problems = dead_load_messages.evaluate(src, materials_project.for_calculation(here), where)
    if problems:
        raise validation.ValidationError(problems[0].text)   # what the tab says in red, the layers' first, then a value written below the sum
    total = sum(r["load"] for r in rows)
    chosen = src.get("chosen")
    retained = chosen if chosen is not None else dead_load_layers.retained(total)
    instance = dead_load.instance_from_layers(rows, retained, "entered:%s, chosen" % where if chosen is not None else "%s, retained" % SOURCE,
                                              "Auf der sicheren Seite gerundeter Bemessungswert der ständigen Lasten.", source=SOURCE, note=NOTE)
    for row, layer in zip(instance["tables"][0]["rows"], rows):
        if layer["dicke"] is None and layer["mass"] is not None:
            row[3] = ""      # a weight per surface: no thickness in the sum (the drawing still shows it)
        if layer["breite"] is None and layer["mass"] is not None:
            row[4] = row[5] = ""
    # UI-002, UI-003: the build-up drawn, printed by show-calc above its table and shown by the tab
    # where the drawing lies and how the record names it: Permanent-loads/Exports/Figures/ in a project laid out by folders, data/calculations/ otherwise (engine.Figures, issue #64)
    place = engine.Figures(here.data_dir if here is not None else None, DOMAIN, here)
    rel = place.name("%s-%s.svg" % (DOMAIN, src["id"]))
    # REQ-013 (Q-002 A, P05): the retained value at every level, g_k, a_k, their sum and the section from level 2, the table of the layers at level 3
    instance["figures"] = [{"file": rel, "title": "Schichtaufbau", "level": 2, "from_level": 2}]
    instance["tables"][0]["from_level"] = 3
    instance["_files"] = {rel: _drawn(layers_of(rows))}
    return instance
