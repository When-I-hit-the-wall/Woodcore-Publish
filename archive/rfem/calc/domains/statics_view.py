"""How an **imported** static model is presented: the engineer's choices, kept beside a drawing he does not own.

The rule v0.98 settled, and it stands: the static models an RFEM import makes go into `data/statics.json` and **never** into `Woodcore-Datei/statics/`. They are regenerated at every import, because RFEM is the source — a model he did not draw has no business in the folder he draws in.

But he asked to be able to set how one is shown: «Le user peut modifier l'affichage (quel effort ou déformation afficher), afficher la valeur, un nom ou les deux, modifier la taille des éléments (comme pour tous les autres éléments de l'onglet Modèles statiques).» So the geometry follows RFEM and **the presentation is his**, which is his own answer B of three:

> (A) «Ajouter aux modèles statiques» materialises a real drawn model, editable, which no longer follows RFEM; (B) it stays generated and a small presentation file beside it keeps his choices, merged at each import; (C) the settings live in the `.woodcore`.

⚠️ **A view is not a model, and it must not be read as one.** `statics.source_paths` globs `*.json` at the top of the folder, so a `views/<id>.json` sitting beside the models would be read as a model and refused for having no `points` — the very trap `details/` was renamed to avoid (§3.3decies). It is therefore a **subfolder**, which that glob does not reach.

⚠️ **A view of a model that no longer exists is kept, not deleted.** An export renamed, a structure renamed in RFEM, a workbook not synced yet: each makes a view point at nothing for a while, and throwing away a page of settings because a file was briefly absent is the kind of loss this project treats as the worst kind. It is reported and left alone.

⚠️ **What a view may set is the presentation and nothing else.** No point, no member, no support, no load: those are RFEM's. What it holds is the three size factors every drawing carries (`figure_style`), and which internal force or deformation is drawn over the system, for which loading, with what written beside it.

⚠️ **A drawn model has no view file**, and is refused one by name: it carries its own `style` and its own everything, and a second place to set the same thing is the duplication §2 rule 1 forbids. The view exists only because an imported model's own file is not the engineer's to edit.
"""

import json
from pathlib import Path

import engine
import validation
from domains import figure_style


def _fail(where, message):
    """The refusal every source module of this project makes, so a view's message reads like a model's."""
    raise validation.ValidationError(f"{where}: {message}")

SCHEMA_VERSION = "1.0"
SCHEMA_VERSIONS = ("1.0",)

# The subfolder of `Woodcore-Datei/statics/` the views live in -- never beside the models, which are globbed.
FOLDER = "views"

# What may be drawn over the system: RFEM's own six internal forces, and the deformations it exports.
QUANTITIES = ("N", "V_y", "V_z", "M_T", "M_y", "M_z")

# What a diagram writes beside itself, on a load's own four (`statics.SHOW_MODES`): the engineer asked for
# «afficher la valeur, un nom ou les deux».
SHOW_MODES = ("none", "name", "value", "name+value")


def folder(statics_dir):
    return Path(statics_dir) / FOLDER


def path_of(statics_dir, model_id):
    return folder(statics_dir) / f"{model_id}.json"


def default():
    """A view that changes nothing: the drawing as the import makes it, and no diagram over it."""
    return {"schema_version": SCHEMA_VERSION, "diagram": None, "style": {}}


def check(view, where):
    """Everything a view must satisfy. Raises `engine.ExportError` naming the field, like every other source."""
    version = view.get("schema_version")
    if version not in SCHEMA_VERSIONS:
        _fail(where, f"schema_version is {version!r} -- this reads {', '.join(SCHEMA_VERSIONS)}")
    validation.validate_structure(view, "statics-view")
    # A view sets the **drawing's** own three factors, so none of them is refused here -- `statics._check_style`'s
    # own call, made the same way so the two refusals read alike.
    figure_style.check(view.get("style"), lambda message: _fail(where, message))
    diagram = view.get("diagram")
    if diagram in (None, {}):
        return
    quantity = diagram.get("quantity")
    if quantity not in QUANTITIES:
        _fail(where, f"diagram.quantity is {quantity!r} -- one of {', '.join(QUANTITIES)}")
    if not str(diagram.get("loading") or "").strip():
        _fail(where, "diagram.loading names no loading -- say which combination or load case to draw, «CO3»")
    show = diagram.get("show", "value")
    if show not in SHOW_MODES:
        _fail(where, f"diagram.show is {show!r} -- one of {', '.join(SHOW_MODES)}")


def read(statics_dir, model_id):
    """One model's view, or `None` where it has none. A malformed one raises, naming the file."""
    path = path_of(statics_dir, model_id)
    if not path.is_file():
        return None
    try:
        view = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _fail(f"{FOLDER}/{model_id}.json", str(exc))
    check(view, f"{FOLDER}/{model_id}.json")
    return view


def read_all(statics_dir):
    """`({model id: view}, problems)` for every view the folder holds.

    ⚠️ A view that cannot be read is a **problem and not a refusal**: it is a page of settings, and a report
    that will not build because one of them has a typo is a report held hostage by its own chrome. The model
    is then drawn as the import makes it, which is what it looked like before the view existed.
    """
    out, problems = {}, []
    here = folder(statics_dir)
    if not here.is_dir():
        return out, problems
    for path in sorted(here.glob("*.json"), key=lambda p: p.name.lower()):
        try:
            out[path.stem] = read(statics_dir, path.stem)
        except validation.ValidationError as exc:
            problems.append(engine.Note(
                "statics_view_unreadable",
                f"The view {FOLDER}/{path.name} could not be read -- {exc}; «{path.stem}» is drawn as the "
                f"import makes it",
                where=path.stem,
            ))
    return out, problems


def write(statics_dir, model_id, view):
    """Writes one model's view, making the subfolder where it is needed. Checked before it touches the disk."""
    check(view, f"{FOLDER}/{model_id}.json")
    here = folder(statics_dir)
    here.mkdir(parents=True, exist_ok=True)
    path = path_of(statics_dir, model_id)
    path.write_text(json.dumps(view, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return path


def apply_style(source, view):
    """The imported source with the view's own size factors over the import's, or the source untouched.

    ⚠️ The view's factors **replace** the drawing's three rather than multiplying them, which is the opposite
    of what one *entry* of a drawing does (`figure_style`): an entry states a factor *over* its drawing, and a
    view states the drawing's own. There is one drawing and one engineer, so a view is the drawing's setting.
    """
    if not view or not view.get("style"):
        return source
    out = dict(source)
    style = dict(out.get("style") or {})
    style.update(view["style"])
    out["style"] = style
    return out


def missing(views, models):
    """A note per view whose model is not there any more -- kept, never deleted."""
    problems = []
    for model_id in sorted(set(views) - set(models)):
        problems.append(engine.Note(
            "statics_view_orphan",
            f"The view {FOLDER}/{model_id}.json is set for a static model no import makes any more -- it is "
            f"kept; the structure may have been renamed in RFEM, or its export not read yet",
            where=model_id,
        ))
    return problems
