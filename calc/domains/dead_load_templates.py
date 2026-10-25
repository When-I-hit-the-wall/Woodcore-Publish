"""Templates of build-ups of permanent loads (spec docs/requirements/completed/2026-10-24-poids-propre-repense.md, REQ-010, UI-004, P07, D-08; issue #111): what «Nouveau…» offers before «Composition vide».

* **Woodcore's** -- `calc/libraries/dead-load-templates.json`: eight build-ups of Lignum's *Holzbau mit System*, each with its names in three languages, the page it is read off (`reference`), what it supposes that the book does not give (`assumptions`) and the book's weight of the whole where it gives one (`book_weight`), shown beside the sum as a check. Read only.
* **The engineer's own**, «Mes modèles» -- a JSON file each in `usersettings.dead_load_templates_dir()` (`%APPDATA%\\Woodcore\\dead-load-templates\\`), outside every project and every installation: a build-up of a project kept as a template by «Enregistrer comme modèle» (`save_mine`), removed by `delete_mine`.

A template's shape is schemas/dead-load-template.schema.json; its layers are a build-up's, dead-load-source 2.0, checked by the one rule that checks a build-up (dead_load_source.check_source). `to_source` copies one into a new build-up of the project -- «Créer depuis ce modèle»: nothing of the template is linked to the copy. `summary` gives what a card shows. A file of the engineer's that cannot be read is left out and named (`problems`), never written over. No Qt here.
"""

import copy
import json
import re
import secrets
from pathlib import Path

import engine
import usersettings
import validation
from domains import dead_load_layers, dead_load_messages, dead_load_source, materials

SCHEMA = "dead-load-template"
VERSION = "1.0"
SHIPPED_FILE = Path(__file__).resolve().parents[1] / "libraries" / "dead-load-templates.json"
MINE_ID = re.compile(r"^t-[0-9a-f]{8}$")
KINDS = ("roof", "flat", "wall", "floor", "other")


def check(template, where):
    """Raises naming `where` and the field where `template` is not one: its schema, then its layers as a build-up's."""
    validation.validate_structure(template, SCHEMA, where)
    if not template["layers"]:
        raise validation.ValidationError("%s: layers is empty -- a template has one layer at least" % where)
    dead_load_source.check_source(_as_source(template), where)


def _as_source(template, cid="T"):
    return {"schema_version": dead_load_source.SOURCE_SCHEMA_VERSION, "id": cid, "name": "", "label": "", "group": "",
            "layers": template["layers"], "chosen": template.get("chosen")}


_shipped = []


def shipped():
    """Woodcore's templates, checked once: a defect of the shipped file stops, naming the template and the field."""
    if not _shipped:
        data = json.loads(SHIPPED_FILE.read_text(encoding="utf-8"))
        out = []
        for i, template in enumerate(data["templates"]):
            template = dict(template, schema_version=data["schema_version"])
            check(template, "%s: templates[%d] (%s)" % (SHIPPED_FILE.name, i, template.get("id")))
            out.append(template)
        _shipped[:] = out
    return list(_shipped)


def folder():
    return usersettings.dead_load_templates_dir()


def mine():
    """(templates, problems) of the engineer's own, by name: the files that cannot be read named in `problems`, never written over."""
    out, problems = [], []
    directory = folder()
    for path in sorted(directory.glob("t-*.json")) if directory.is_dir() else ():
        try:
            template = json.loads(path.read_text(encoding="utf-8"))
            check(template, path.name)
            if template["id"] != path.stem:
                raise validation.ValidationError("%s: id %r is not its file name" % (path.name, template["id"]))
        except validation.ValidationError as exc:
            problems.append(str(exc))
            continue
        except (OSError, ValueError) as exc:
            problems.append("%s: cannot be read as JSON -- %s" % (path.name, exc))
            continue
        out.append(template)
    return sorted(out, key=lambda t: name(t, "fr").casefold()), problems


def name(template, lang):
    """The template's name in `lang`, else in another language it has."""
    names = template.get("names") or {}
    return names.get(lang) or next((n for n in names.values() if n), template["id"])


def save_mine(src, words, lang):
    """Keeps the build-up `src` as one of the engineer's templates named `words` (in the language `lang` he wrote them in) -- «Enregistrer comme modèle»: its layers and its retained value copied, a 1.x build-up read as 2.0. Returns the template written."""
    taken = {t["id"] for t in mine()[0]}
    tid = "t-" + secrets.token_hex(4)
    while tid in taken:
        tid = "t-" + secrets.token_hex(4)
    template = {"schema_version": VERSION, "id": tid, "kind": "other", "names": {lang: words.strip() or src.get("name") or src["id"]},
                "reference": None, "assumptions": {}, "book_weight": None,
                "layers": copy.deepcopy(dead_load_source.upgraded(src)["layers"]), "chosen": src.get("chosen")}
    check(template, "%s.json" % tid)
    engine.write_json(folder() / ("%s.json" % tid), template)
    return template


def delete_mine(tid):
    if not MINE_ID.match(str(tid or "")):
        raise validation.ValidationError("template %r is not one of the engineer's own -- Woodcore's are read only" % (tid,))
    (folder() / ("%s.json" % tid)).unlink(missing_ok=True)


def to_source(template, cid, lang="fr"):
    """A new build-up of the project from `template` -- «Créer depuis ce modèle»: its layers copied, its name the template's in `lang`, its reference in the description; dead-load-source 2.0."""
    src = dead_load_source.new_source(cid)
    src["name"] = name(template, lang)
    reference = template.get("reference")
    src["label"] = ("%s, %s, S. %s" % (reference["book"], reference["where"], reference["page"])) if reference else ""
    src["layers"] = copy.deepcopy(template["layers"])
    src["chosen"] = template.get("chosen")
    return src


def summary(template, projects=None):
    """What a card shows (T58): the number of layers, the sum in kN/m² and kg/m² (None where a layer cannot be weighed), the red messages, the layers' model for its small section, the book's weight."""
    rows, problems = dead_load_messages.evaluate(_as_source(template, template["id"]), projects, template["id"])
    total = None if problems else sum(r["load"] for r in rows)
    return {"layers": len(template["layers"]), "total": total, "total_kg": None if total is None else total * materials.KG_TO_KN,
            "retained": None if total is None else (template.get("chosen") or dead_load_layers.retained(total)),
            "problems": dead_load_messages.red(problems), "model": [] if problems else dead_load_source.layers_of(rows),
            "book_weight": template.get("book_weight")}
