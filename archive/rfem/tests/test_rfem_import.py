"""The second half of the RFEM import: what the metadata *means* (`validation.py`), what the import writes (`json_export.py`), and what a structure becomes (`import_controller.py`).

One file for the three because they are one chain and the facts worth holding are about the chain: a comment is read, its meaning is checked against the model and the project, the structure is translated into a static model, and the whole is written down. The reading itself is `tests/test_model_tables.py`'s and `tests/test_structure_detection.py`'s.

👉 **Run on the engineer's own export before any of it was asserted here**, and it found something on its first run: member 24 realises position T001, RFEM gives its section as **500/200 mm** and `Positionen.xlsx` gives **100/200 mm**. That is the check that catches an error of substance rather than of naming, and it caught one.

⚠️ **Two collisions the real data found, both of which would have overwritten data in silence:**

- **A load's number is per load case**, so an id made of the number alone collides: his model has a load 4 on member 26 in two cases, and `statics.check_source` refused the pair by name. The id carries the case.
- **Two exports of one building make one static model id.** He named an `.xlsx` and a re-export of it, and each made «VU-gunstig»; `statics.prepare` keys its models by id, so the second overwrote the first. Refused now, across exports and not only inside one.
"""

import contextlib
import json
import shutil

import conftest
from fixtures import rfem_model

import engine
import project
from domains import statics
from rfem_import import import_controller as controller
from rfem_import import json_export
from rfem_import import validation as rv
from rfem_import.metadata_parser import parse_metadata
from rfem_import.model_tables import read_model
from rfem_import.structure_detection import Item, detect


def _folder(name):
    return conftest.tmpdir("rfem_import_" + name)


def _read(name, lang="fr"):
    model = read_model(rfem_model.workbook(_folder(name) / "modele.xlsx", lang=lang))
    return model, detect(model.items(), combinations=model.combination_cases())


def _codes(notes):
    return sorted({note.code for note in notes})


# --- what the metadata means ----------------------------------------------------------------------


def test_a_position_may_be_on_a_member_or_a_surface_and_nowhere_else():
    """The engineer's rule: «une position ne peut être attribué qu'à un élément barre ou panneau. Une charge ou un appui ne peux pas recevoir de position»."""
    items = [
        Item("member", 1, nodes=[1, 2], meta=parse_metadata('@position "T001"', where="Member 1")),
        Item("surface", 2, nodes=[1, 2, 3], meta=parse_metadata('@position "D001"', where="Surface 2")),
        Item("support", 3, nodes=[1], meta=parse_metadata('@position "A001"', where="Support 3")),
        Item("member_load", 4, on=[("member", 1)], meta=parse_metadata('@position "Q001"', where="Load 4")),
    ]
    found = rv.position_places(items)
    assert _codes(found) == ["rfem_position_place"]
    # The object is named by `Item.where`, which is how every message of the import names it -- one object, one name, wherever it is reported.
    named = sorted(note.args["where"] for note in found)
    assert named == ["Member load 4", "Support 3"], f"got {named} -- a member and a surface may carry one"


def test_a_position_the_workbook_does_not_hold_says_what_to_add():
    model, _ = _read("unknown_position")
    assert rv.positions_resolve(model, ["T001"]) == [], "the fixture's member 24 names T001"
    found = rv.positions_resolve(model, ["S001"])
    assert _codes(found) == ["rfem_position_unknown"] and "T001" in found[0], found


def test_a_project_that_has_never_been_exported_is_told_nothing():
    """A project whose positions are not exported yet must not be told that every one of them is unknown."""
    model, _ = _read("no_positions")
    assert rv.positions_resolve(model, []) == []


def test_a_position_on_two_structures_is_reported():
    """Two elements of one position are ordinary inside one structure -- the position plan has allowed it since v0.44 -- and rarely meant across two."""
    items = [
        Item("member", 1, nodes=[1, 2], meta=parse_metadata('@model "A"\n@position "T001"', where="Member 1")),
        Item("member", 2, nodes=[3, 4], meta=parse_metadata('@model "B"\n@position "T001"', where="Member 2")),
    ]
    found = rv.positions_across_structures(detect(items))
    assert _codes(found) == ["rfem_position_shared"]
    assert "T001" in found[0] and "«A»" in found[0] and "«B»" in found[0], found[0]


def test_a_section_rfem_and_the_workbook_disagree_about_is_reported():
    """⚠️ The check that caught a real one on his own project: RFEM 500/200 against Positionen.xlsx 100/200 for T001."""
    model, _ = _read("sections")
    assert rv.sections_agree(model, {"T001": (500.0, 200.0)}) == [], "the fixture's section 1 is 500/200"
    found = rv.sections_agree(model, {"T001": (100.0, 200.0)})
    assert _codes(found) == ["rfem_section_disagrees"]
    assert "500/200 mm" in found[0] and "100/200 mm" in found[0], found[0]
    assert rv.sections_agree(model, {"T001": (200.0, 500.0)}) == [], "a section stated the other way round is the same section"
    assert rv.sections_agree(model, {"T001": (500.05, 200.0)}) == [], "a tenth of a millimetre is not a disagreement"


def test_a_width_no_structure_could_have_is_reported():
    """`metadata_parser` reads «1500» as 1500 m because deciding it is a mistake needs a notion of plausibility, which is here and not there."""
    items = [Item("member_load", 1, on=[("member", 1)], meta=parse_metadata("@be 1500", where="Load 1")),
             Item("member_load", 2, on=[("member", 1)], meta=parse_metadata("@be 1.7m", where="Load 2"))]

    class Stub:
        def items(self):
            return items

    found = rv.widths_plausible(Stub())
    assert _codes(found) == ["rfem_width_implausible"] and "Member load 1" in found[0], found


def test_a_load_that_names_no_instance_is_reported():
    items = [Item("member_load", 1, on=[("member", 1)], meta=parse_metadata("@load snow-load/SL-Dach9", where="Load 1"))]

    class Stub:
        def items(self):
            return items

    assert rv.loads_resolve(Stub(), {"snow-load": ["SL-Dach9"]}) == []
    found = rv.loads_resolve(Stub(), {"snow-load": ["SL"]})
    assert _codes(found) == ["rfem_load_unknown"] and "SL-Dach9" in found[0], found


def test_a_structure_nobody_named_is_reported_once():
    """One note per structure, not one per member: twenty-one structures are a to-do list and sixty members would be noise."""
    model, structures = _read("unnamed")
    found = rv.structures_named(structures)
    assert len(found) == sum(1 for s in structures if not s.named)
    assert _codes(found) == ["rfem_structure_unnamed"] and "@model" in found[0]


def test_nothing_refuses():
    """The rule the plans, the static models and the connectors follow (docs/architecture/data-contracts.md §3.6): every finding is a note, so one mistyped position cannot stop the import of every other structure."""
    model, structures = _read("nothing_refuses")
    found = rv.problems(model, structures, known_positions=["S001"], sections_of={"T001": (1.0, 1.0)},
                        instances={"snow-load": ["SL"]})
    assert found and all(isinstance(note, engine.Note) for note in found)
    assert "rfem_position_unknown" in _codes(found) and "rfem_section_disagrees" in _codes(found)


def test_the_keys_in_use_and_the_references_are_gathered():
    """What an import prints to say the convention reached the model at all, and what validation resolves."""
    model, _ = _read("keys")
    counts = rv.keys_in_use(model)
    assert counts["model"] == 1 and counts["position"] == 1 and counts["be"] == 2, counts
    references = rv.references(model)
    assert list(references["position"]) == ["T001"] and references["position"]["T001"] == ["Member 24"]


# --- what a structure becomes ---------------------------------------------------------------------


def test_a_structure_becomes_a_static_model_the_pipeline_accepts():
    """The one thing that matters about the translation: `statics.check_source` is what says it is well formed, and it is the very check a drawn model goes through."""
    model, structures = _read("source")
    made = controller.models_of(model, structures)
    assert len(made) == 1, f"only the named structure becomes a model, got {[s['id'] for s in made]}"
    source = made[0]
    statics.check_source(source, "the imported model")          # raises where it is not
    assert source["id"] == "VU" and source["name"] == "Velo Unterstand"
    assert source["label"] == "günstige Einwirkung"
    assert source["schema_version"] == "1.1"


def test_only_a_structure_somebody_named_becomes_a_model():
    """A model's id is what a report addresses it by, and «member-1» is a placeholder. The unnamed ones are reported by validation, once each."""
    model, structures = _read("named_only")
    assert len(controller.models_of(model, structures)) == 1
    assert len(controller.models_of(model, structures, named_only=False)) == len(structures)


def test_the_frame_is_carried_across_without_a_flip():
    """⚠️ Measured, not assumed: RFEM's global Z points **down** in this model and a Woodcore static model is drawn z down, so a coordinate is carried as it is. A structure whose supports came out above its loads is the sign to look at."""
    model, structures = _read("frame")
    source = controller.models_of(model, structures)[0]
    by_id = {point["id"]: point for point in source["points"]}
    assert by_id["P36"]["x"] == 3.5 and by_id["P36"]["z"] == -2.95, by_id["P36"]
    assert model.node(36).z == -2.95, "the same number the export held"


def test_a_member_becomes_a_bar_and_an_unknown_type_is_reported():
    """A cable read as a bar is a system that carries compression it cannot, and RFEM's type is a localised word -- so a type this import does not know is carried as a bar **and named**."""
    model, structures = _read("member_kind")
    problems = []
    source = controller.models_of(model, structures, problems=problems)[0]
    assert [member["kind"] for member in source["members"]] == ["bar"]
    assert "rfem_import_member_type" not in _codes(problems), "«Poutre» is a beam"
    for member in model.members:
        member.type = "Seil"
    problems = []
    controller.models_of(model, structures, problems=problems)
    assert "rfem_import_member_type" in _codes(problems)


def test_a_member_carries_its_position_as_its_label():
    model, structures = _read("label")
    source = controller.models_of(model, structures)[0]
    assert [member.get("label") for member in source["members"]] == ["T001"]


def test_a_support_over_several_nodes_becomes_several_supports():
    """⚠️ An RFEM support is one definition applied to a set — his support 2 holds 23 nodes — and a Woodcore support holds one point."""
    items = [Item("member", 1, nodes=[1, 2], meta=parse_metadata('@model "A"', where="Member 1"))]
    model, structures = _read("supports")
    # the fixture's support 1 holds nodes 1, 50 and 51; the structure of member 30 holds 50 and 51
    structure = [s for s in structures if 30 in s.numbers("member")][0]
    structure.name = "Bench"                                    # named, so it is translated
    source = controller.source_of(structure, model)
    held = sorted(support["point"] for support in source["supports"])
    assert held == ["P50", "P51"], f"got {held} -- node 1 is in another structure"
    assert all(support["type"] == "fixed" for support in source["supports"])
    assert len({support["id"] for support in source["supports"]}) == 2, "one id each"


def test_a_hinge_becomes_a_release_and_a_spring_keeps_its_stiffness():
    """The hinge definition says which freedom it sets free, and `inf` there means *not* released — the reading inverted from a support's."""
    model, structures = _read("releases")
    source = controller.models_of(model, structures)[0]
    assert len(source["releases"]) == 1, source["releases"]
    release = source["releases"][0]
    assert release["member"] == "B24" and release["end"] == "end" and release["dof"] == "moment"
    assert release["stiffness"] == {"value": 21.672001, "unit": "kNm/rad"}, release["stiffness"]


def test_a_load_becomes_one_load_per_member_with_its_width():
    """And `@be` becomes the load's own influence width, which is what that key was for."""
    model, structures = _read("loads")
    source = controller.models_of(model, structures)[0]
    assert len(source["line_loads"]) == 1, source["line_loads"]
    load = source["line_loads"][0]
    assert load["member"] == "B24" and load["shape"] == "uniform" and load["direction"] == "vertical"
    assert load["magnitude"] == {"value": 2.5, "unit": "kN/m"}
    assert load["width"]["value"] == 2.0 and load["width"]["shown"] is True
    assert "avant-toit" in load["width"]["description"]


def test_a_load_s_id_carries_its_load_case():
    """⚠️ The collision the real export found: a load's number is per case, and his model has a load 4 on member 26 in two of them."""
    model, structures = _read("load_ids")
    source = controller.models_of(model, structures)[0]
    assert all(load["id"].startswith("qCC1_") for load in source["line_loads"]), [l["id"] for l in source["line_loads"]]


def test_a_direction_this_import_does_not_read_is_reported():
    model, structures = _read("direction")
    for load in model.loads:
        load.direction = "along the grain"
    problems = []
    source = controller.models_of(model, structures, problems=problems)[0]
    assert "rfem_import_direction" in _codes(problems)
    assert source["line_loads"][0]["direction"] == "vertical", "drawn as vertical, and said so"


def test_two_structures_whose_names_slug_alike_are_refused():
    items = [
        # ⚠️ «Velo-Unterstand» would **not** collide: the slug keeps a hyphen. What collides is an accent, which it decomposes.
        Item("member", 1, nodes=[1, 2], meta=parse_metadata('@model "Vélo"', where="Member 1")),
        Item("member", 24, nodes=[36, 40], meta=parse_metadata('@model "Velo"', where="Member 24")),
    ]
    model, _ = _read("slug")
    structures = detect(items)
    problems = []
    made = controller.models_of(model, structures, problems=problems)
    assert len(made) == 1 and "rfem_import_id_taken" in _codes(problems), (len(made), _codes(problems))


# --- the whole import, and what it writes ----------------------------------------------------------


def test_an_export_the_project_no_longer_has_is_a_warning_and_not_a_stop():
    """An RFEM file NextCloud has not synced yet must not stop the positions' own export."""
    with _using("gone") as here:
        export = rfem_model.workbook(here.root / "A.xlsx")
        here = project.set_rfem_models(here, [export])
        export.unlink()
        sources, records, _domain, warnings = controller.prepare(here)
        assert sources == [] and records == {}
        assert "rfem_import_gone" in _codes(warnings), _codes(warnings)


def test_two_exports_of_one_building_are_refused_by_name():
    """⚠️ The second collision the real project found: he named an .xlsx and a re-export of it, each making «VU-gunstig», and `statics.prepare` keys its models by id."""
    with _using("two_exports") as here:
        first = rfem_model.workbook(here.root / "A.xlsx")
        second = rfem_model.workbook(here.root / "B.xlsx")
        here = project.set_rfem_models(here, [first, second])
        sources, records, _domain, warnings = controller.prepare(here)
        assert len(sources) == 1, [source["id"] for source in sources]
        assert len(records) == 2, "both are read and both keep their own record"
        assert "rfem_import_id_taken" in _codes(warnings), _codes(warnings)


def test_the_import_writes_its_json_and_it_answers_to_its_schema():
    """The one intermediate format between RFEM and Woodcore, checked against `schemas/rfem-import.schema.json` before it is written -- like every other artifact of data/ (docs/architecture/data-contracts.md §3.6)."""
    with _using("json") as here:
        here = project.set_rfem_models(here, [rfem_model.workbook(here.root / "A.xlsx")])
        _sources, records, _domain, _warnings = controller.prepare(here)
        assert list(records) == ["A"], list(records)
        written = controller.write(records, here.data_dir)
        assert written == [], "nothing to sweep on a first import"
        path = here.data_dir / json_export.FOLDER / "A.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        assert record["schema_version"] == json_export.SCHEMA_VERSION
        assert record["source"]["format"] == "xlsx" and record["source"]["producer"] == "gui"
        assert len(record["model"]["members"]) == 4 and len(record["structures"]) == 3
        assert record["metadata"]["keys"]["model"] == 1
        assert record["metadata"]["references"]["position"] == {"T001": ["Member 24"]}
        assert "results" not in record, "no results were read, which is not the same as no forces"
        assert record["model"]["supports"][0]["x"] == "inf", "JSON has no infinity"


def test_the_results_are_read_only_when_they_are_asked_for():
    """⚠️ Off by default, and that is a measurement: reading the result sheets of one of the engineer's workbooks takes **105 s** against 1.1 s for the model tables, and a static model needs no forces. `woodcore-cli import --results` is what asks."""
    with _using("results") as here:
        here = project.set_rfem_models(here, [rfem_model.workbook(here.root / "A.xlsx")])
        _s, records, _domain, _w = controller.prepare(here)
        assert "results" not in records["A"], "a normal import carries none"
        _s, records, _domain, _w = controller.prepare(here, read_results=True)
        assert "results" in records["A"], "asking for them reads them"

    # And an export whose result tables were not ticked in RFEM's own dialog says so, rather than writing an
    # empty «results» nobody could tell from a model with no forces in it.
    with _using("results_none") as here:
        here = project.set_rfem_models(here, [rfem_model.workbook(here.root / "B.xlsx", results=False)])
        _s, records, _domain, warnings = controller.prepare(here, read_results=True)
        assert "results" not in records["B"]
        assert "rfem_import_no_results" in _codes(warnings), _codes(warnings)
        assert "internal forces in RFEM's export dialog" in str(
            [note for note in warnings if note.code == "rfem_import_no_results"][0])


def test_the_two_export_formats_spell_the_forces_differently():
    """⚠️ The CSV writes «V_y», «M_T»; the workbook writes «Vy», «MT». Measured on the engineer's own exports, and the only difference between the two for these tables -- read as one spelling, a whole workbook of results is not a results table at all."""
    from rfem_import.results import FORCE_ALIASES, FORCES

    assert FORCES == ("N", "V_y", "V_z", "M_T", "M_y", "M_z"), FORCES
    assert "Vy" in FORCE_ALIASES["V_y"] and "V_y" in FORCE_ALIASES["V_y"]
    assert "MT" in FORCE_ALIASES["M_T"] and "M_T" in FORCE_ALIASES["M_T"]
    assert all(key == spellings[0] for key, spellings in FORCE_ALIASES.items()), (
        "the first spelling of each is the key everything downstream uses"
    )


def test_a_loading_is_read_from_a_sheet_name_as_well_as_from_a_file_name():
    """«CO1_analyse_….csv» and «CO1 | Barres | Efforts internes» both name the loading; what follows the number is an underscore, a hyphen, a space or a pipe."""
    from rfem_import.results import loading_of

    assert loading_of("CO1 | Barres | Efforts internes") == ("CO1", "CO", 1)
    assert loading_of("LF12 | Stäbe | Schnittgrößen") == ("LF12", "LF", 12)
    assert loading_of("CO1_analyse_statique.csv") == ("CO1", "CO", 1)


def test_a_record_the_project_no_longer_names_is_swept():
    with _using("sweep") as here:
        here = project.set_rfem_models(here, [rfem_model.workbook(here.root / "A.xlsx")])
        _s, records, _domain, _w = controller.prepare(here)
        controller.write(records, here.data_dir)
        assert controller.write({}, here.data_dir) == ["A.json"], "the record of an export no longer named"
        assert not (here.data_dir / json_export.FOLDER / "A.json").exists()


def test_an_imported_model_joins_the_drawn_ones_and_an_id_both_claim_is_refused():
    """`statics.prepare(generated=…)` is where the two meet, and the id is where they can collide -- a `show-static-model` call would otherwise print whichever was read last."""
    with _using("prepare") as here:
        here = project.set_rfem_models(here, [rfem_model.workbook(here.root / "A.xlsx")])
        sources, _records, _domain, _warnings = controller.prepare(here)
        data, files, notes = statics.prepare(here.statics_dir, {}, sources)
        assert "VU" in data["models"], sorted(data["models"])
        assert f"statics/VU-fr.svg" in files
        drawn = sorted(name for name in data["models"] if name != "VU")
        assert drawn, "the project's own drawn models are still there"

        clash = dict(sources[0])
        clash["id"] = drawn[0]
        try:
            statics.prepare(here.statics_dir, {}, [clash])
        except Exception as error:
            assert drawn[0] in str(error) and "drawn in Woodcore" in str(error), error
        else:
            raise AssertionError("an id a drawn model claims must be refused")


# --- the helpers this file needs --------------------------------------------------------------------


@contextlib.contextmanager
def _using(name):
    """A copy of the example project, current for the length of the block.

    ⚠️ A context manager, because `conftest.project_copy` copies **the project that is current**: a test that left its own copy named would be copied by the next one, and every one after it would carry the RFEM exports of the tests before it (`tests/test_rfem_tab.py` found that the hard way).
    """
    copy = conftest.project_copy(f"rfem_import_{name}")
    # ⚠️ The example project **names an RFEM export of its own** since v0.100 --
    # `RFEM-Export/Beispiel-Modell.xlsx`, which is what makes the six `rfem-*` commands' examples compile
    # and their pages render (docs/typst/command-docs.md §10sexies). A test states its own models, so the copy starts with
    # none and with none of that import's records to sweep; `set_rfem_models` returns the project as it now
    # stands and does not make it current, so it is the **returned** one that is used.
    copy = project.set_rfem_models(copy, [])
    shutil.rmtree(copy.generated_dir / "data" / "rfem", ignore_errors=True)
    with project.using(copy):
        yield project.current()
