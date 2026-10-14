"""How an imported static model is presented (`calc/domains/statics_view.py`).

The engineer: «Le user peut modifier l'affichage (quel effort ou déformation afficher), afficher la valeur, un nom ou les deux, modifier la taille des éléments (comme pour tous les autres éléments de l'onglet Modèles statiques).» — and, asked whether an imported model should become a drawn one or stay generated, he chose **B**: it stays generated, and a small presentation file beside it keeps his choices, merged at each import. So the geometry is RFEM's and the presentation is his.

⚠️ **The trap this file exists for**: `statics.source_paths` globs `*.json` at the top of `Woodcore-Datei/statics/`, so a view sitting beside the models would be read as a model and refused for having no points — which is exactly why the detail schemas live in `details/` and not in `schemas/` (§3.3decies). A view is therefore in a **subfolder**, and one test here holds that.
"""

import json

import conftest
import validation
from domains import statics, statics_view


def _folder(name):
    folder = conftest.tmpdir("statics_view_" + name)
    (folder / statics_view.FOLDER).mkdir(parents=True, exist_ok=True)
    return folder


def _view(**diagram):
    view = statics_view.default()
    if diagram:
        view["diagram"] = dict({"quantity": "M_y", "loading": "CO3"}, **diagram)
    return view


def test_a_view_lives_in_a_subfolder_the_models_glob_does_not_reach():
    """The `details/` trap (§3.3decies), met again and avoided the same way.

    `statics.source_paths` reads every `*.json` at the top of the folder; a view beside the models would be
    read as one and refused for having no `points`, which is a refusal nobody could act on.
    """
    folder = _folder("subfolder")
    statics_view.write(folder, "VU-Probe", _view())
    assert statics_view.path_of(folder, "VU-Probe").is_file()
    assert statics_view.path_of(folder, "VU-Probe").parent.name == statics_view.FOLDER
    assert statics.source_paths(folder) == [], "a view must not be read as a model"


def test_a_view_is_read_back_as_it_was_written():
    folder = _folder("roundtrip")
    written = _view(show="name+value")
    written["style"] = {"line": 1.5, "text": 0.8}
    statics_view.write(folder, "VU-Probe", written)
    assert statics_view.read(folder, "VU-Probe") == written
    assert statics_view.read(folder, "Nirgends") is None, "a model with no view has none, and that is not an error"


def test_what_a_view_may_not_say_is_refused_by_name():
    """A view sets the presentation and nothing else: no point, no member, no load -- those are RFEM's."""
    folder = _folder("refusals")
    for view, expected in (
        (_view(quantity="M_q"), "diagram.quantity"),
        (_view(loading="  "), "diagram.loading"),
        (_view(show="toujours"), "diagram.show"),
        ({"schema_version": "1.0", "style": {"epaisseur": 2}}, "epaisseur"),
        ({"schema_version": "0.9"}, "schema_version"),
    ):
        try:
            statics_view.check(view, "probe")
        except validation.ValidationError as exc:
            assert expected in str(exc), f"{expected} is not named in {exc}"
        else:
            raise AssertionError(f"{view} was not refused")


def test_a_view_that_cannot_be_read_is_a_note_and_never_a_refusal():
    """A page of settings with a typo must not stop the report: the model is drawn as the import makes it."""
    folder = _folder("broken")
    (folder / statics_view.FOLDER / "VU-Probe.json").write_text("{ not json", encoding="utf-8")
    views, problems = statics_view.read_all(folder)
    assert views == {}
    assert len(problems) == 1 and "VU-Probe" in str(problems[0])


def test_a_view_of_a_model_that_is_gone_is_kept_and_reported():
    """An export renamed, a structure renamed in RFEM, a workbook not synced yet -- none of them is a reason to
    throw a page of settings away."""
    folder = _folder("orphan")
    statics_view.write(folder, "VU-Parti", _view())
    views, _ = statics_view.read_all(folder)
    problems = statics_view.missing(views, {"VU-Reste": {}})
    assert len(problems) == 1 and "VU-Parti" in str(problems[0])
    assert statics_view.path_of(folder, "VU-Parti").is_file(), "it is kept"


def test_the_views_factors_are_the_drawings_own():
    """⚠️ A view **replaces** the drawing's three factors, where one *entry* of a drawing states a factor
    multiplying them (`figure_style`). There is one drawing and one engineer, so a view is the drawing's own
    setting -- and a factor it leaves out keeps the import's."""
    source = {"id": "VU-Probe", "style": {"line": 1.0, "point": 1.0, "text": 1.0}}
    applied = statics_view.apply_style(source, _view())
    assert applied is source, "a view with no style changes nothing at all"
    applied = statics_view.apply_style(source, {"style": {"line": 1.4}})
    assert applied["style"] == {"line": 1.4, "point": 1.0, "text": 1.0}
    assert source["style"]["line"] == 1.0, "and the source it was given is not modified"


def test_the_diagram_is_rendered_by_the_import_and_taken_out_of_the_record():
    """The whole chain, on the engineer's own export: the view asks for a diagram, the import draws it -- the
    one place that can read RFEM's own distribution -- and `statics.prepare` writes the SVG into `data/statics/`
    while the record keeps only what it is.

    ⚠️ The SVG text must never reach `data/statics.json`: Typst reads that file on every compile.
    """
    project = conftest.real_project()
    export = conftest.real_rfem_export(project, "260929-01_29509-Model.xlsx")
    if not export.exists():
        raise conftest.Skip(f"the engineer's own RFEM export is not here ({export.name})")
    from rfem_import import import_controller, model_tables, structure_detection

    model = model_tables.read_model(export)
    structures = structure_detection.detect(model.items(), combinations=model.combination_cases())
    problems = []
    made = import_controller.models_of(model, structures, problems=problems)
    wanted = next(source["id"] for source in made)
    views = {wanted: _view(loading="CO1")}
    made = import_controller._presented(made, views, model, export, export.name, problems)
    source = next(s for s in made if s["id"] == wanted)
    assert "diagram" in source, f"no diagram was drawn for {wanted}: {[str(p) for p in problems][:3]}"
    assert sorted(source["diagram"]["files"]) == ["de", "en", "fr"], "one figure per language"
    assert source["diagram"]["files"]["de"].startswith("<svg"), "and each one is an SVG"

    data, files, _notes = statics.prepare(_folder("chain"), {}, made)
    record = data["models"][wanted]
    assert record["diagram"]["quantity"] == "M_y" and record["diagram"]["loading"] == "CO1"
    assert "files" not in record["diagram"], "the SVG text stays out of data/statics.json"
    for lang, name in record["diagram"]["figures"].items():
        assert name in files, f"the {lang} figure was not written"
        assert files[name].startswith("<svg")


def test_a_loading_the_export_has_not_got_is_a_note_and_the_system_is_drawn_bare():
    """A combination deleted in RFEM, or a table not ticked at the export, must not stop the positions' export."""
    project = conftest.real_project()
    export = conftest.real_rfem_export(project, "260929-01_29509-Model.xlsx")
    if not export.exists():
        raise conftest.Skip("the engineer's own RFEM export is not here")
    from rfem_import import import_controller, model_tables, structure_detection

    model = model_tables.read_model(export)
    structures = structure_detection.detect(model.items(), combinations=model.combination_cases())
    problems = []
    made = import_controller.models_of(model, structures, problems=problems)
    wanted = next(source["id"] for source in made)
    made = import_controller._presented(made, {wanted: _view(loading="CO999")}, model, export, export.name, problems)
    source = next(s for s in made if s["id"] == wanted)
    assert "diagram" not in source, "nothing is drawn"
    assert any("CO999" in str(note) for note in problems), "and the loading is named"
