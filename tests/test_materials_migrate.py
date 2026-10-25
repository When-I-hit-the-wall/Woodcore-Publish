"""The copy a project keeps of the engineer's materials, what changes are said, and the materials of a project of before poured into his library (calc/domains/materials_project.py, materials_migrate.py, materials.py; spec docs/requirements/active/2026-10-24-onglet-materiaux.md, REQ-013 to REQ-015, ARCH-007, D-11, D-15; issue #110).

What is held:

* **ARCH-007** -- a layer of `library: "catalogue"` weighed by its id, a shipped material or the project's copy; a build-up naming one at 1.2 read, refused at 1.0, and at 2.0; the old libraries still read;
* **REQ-013** -- a copy taken at a save, with its PDF; a copy no case names removed; the project computes from the copy with the engineer's library gone;
* **REQ-014, D-11** -- a value changed in the library said, naming it; words said apart; «Garder» silences that version and not the next; «Reprendre» takes it; a material another computer lacks offered to the library;
* **REQ-015, D-15** -- a 1.0 file poured into the library at the opening, the project at 2.0, its layers rewritten to the new ids and the archives holding what was; the same load before and after; a second opening pours nothing; a project read only pours into the library and changes nothing of its own; weights compared in kN.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import conftest
import engine
import project
import usersettings
import validation
from domains import dead_load_source, materials, materials_migrate, materials_project, materials_user


class _Library:
    def __enter__(self):
        self.was = os.environ.get(usersettings.MATERIALS_ENV)
        os.environ[usersettings.MATERIALS_ENV] = str(conftest.tmpdir("migrate-library"))
        return self

    def __exit__(self, *_):
        if self.was is None:
            os.environ.pop(usersettings.MATERIALS_ENV, None)
        else:
            os.environ[usersettings.MATERIALS_ENV] = self.was


def _mine(name="Dreischichtplatte", value=5.2):
    m = materials_user.blank("other", "board")
    m["names"]["fr"] = name
    m["weight"] = {"value": value, "unit": "kN/m³", "ref": "Datenblatt"}
    m["source"] = {"kind": "url", "url": "https://example.org"}
    return m


def _build_up(here, cid, layers, version=None):
    """A build-up written: at 2.0, or at the 1.x `version` given, its layers as they were written then."""
    src = dead_load_source.new_source(cid)
    src["layers"] = layers
    if version:
        src["schema_version"] = version
    else:
        dead_load_source.stamp_version(src)
    dead_load_source.check_source(src)
    path = dead_load_source.folder(here) / ("%s.json" % cid)
    engine.write_json(path, src)
    return src


def _layer(material, thickness=27, **more):
    return dict(dead_load_source.new_layer(), material=material, thickness=thickness, **more)


def _old_layer(library, material, thickness=27):
    """A layer as dead-load-source 1.x wrote it (issue #111 reads it through dead_load_migrate)."""
    return {"kind": "gk", "library": library, "material": material, "ebene": "", "thickness": thickness, "width": None, "spacing": None, "beside": False, "load": None}


def test_a_layer_names_a_material_by_its_id():
    here = conftest.project_copy("mat-catalogue")
    with project.using(here), _Library():
        assert materials.weight({"library": "catalogue", "material": "sia261:holz_nadelhoelzer_allgemein"})[:2] == (5, "kN/m³")
        assert materials.weight({"library": "catalogue", "material": "sia265-1:osb3"})[0] == 6.8
        assert materials.weight({"library": "catalogue", "material": "ext:62"})[0] == 6.8
        for bad, said in (("sia261:nothing", "ships"), ("u-00000099", "no copy"), ("sia265-1:mdf-la", "no weight")):
            try:
                materials.weight({"library": "catalogue", "material": bad})
            except validation.ValidationError as exc:
                assert said in str(exc), (bad, exc)
            else:
                raise AssertionError(bad)
        src = _build_up(here, "DA-90", [_old_layer("catalogue", "sia261:holz_nadelhoelzer_allgemein"), _old_layer("sia261", "holz_nadelhoelzer_allgemein")], "1.2")
        rows = dead_load_source.layer_rows(src, materials.read_project(here))
        assert abs(rows[0]["load"] - rows[1]["load"]) < 1e-12        # the same line, by its id and by the old keys
        assert dead_load_source.layer_rows(_build_up(here, "DA-89", [_layer("sia261:holz_nadelhoelzer_allgemein")]))[0]["load"] == rows[0]["load"]   # and at 2.0
        src["schema_version"] = "1.0"
        try:
            dead_load_source.check_source(src)
        except validation.ValidationError as exc:
            assert "1.2" in str(exc)
        else:
            raise AssertionError("a catalogue layer at 1.0")


def test_a_copy_is_taken_at_a_save_and_the_project_computes_from_it_alone():
    here = conftest.project_copy("mat-copy")
    with project.using(here), _Library():
        pdf = conftest.tmpdir("mat-copy-pdf") / "Datenblatt.pdf"
        pdf.write_bytes(b"%PDF-1.4 datasheet")
        m = _mine()
        m["source"] = {"kind": "pdf", "file": materials_user.import_pdf(pdf)}
        materials_user.save(m)
        src = _build_up(here, "DA-91", [_layer(m["id"])])
        assert materials_project.sync(dead_load_source.used_materials(src), here) == [m["id"]]
        data = json.loads(materials.project_file(here).read_text(encoding="utf-8"))
        assert data["schema_version"] == "2.0" and [c["id"] for c in data["materials"]] == [m["id"]]
        assert (here.sources_dir / "materials" / "datenblatt.pdf").read_bytes() == b"%PDF-1.4 datasheet"
        before = dead_load_source.build_instance(src, here)["vars"]
        os.environ[usersettings.MATERIALS_ENV] = str(conftest.tmpdir("mat-copy-other-computer"))   # the library gone: another computer
        assert dead_load_source.build_instance(src, here)["vars"] == before
        assert materials_project.sync([], here) == []                                            # no case names it any more
        assert json.loads(materials.project_file(here).read_text(encoding="utf-8"))["materials"] == []
        assert not (here.sources_dir / "materials" / "datenblatt.pdf").exists()


def test_a_change_in_the_library_is_said_and_kept_or_taken():
    here = conftest.project_copy("mat-diff")
    with project.using(here), _Library():
        m = materials_user.save(_mine())
        materials_project.sync([m["id"]], here)
        assert materials_project.warnings(here) == []
        changed = dict(m, weight={"value": 5.6, "unit": "kN/m³", "ref": "Datenblatt"})
        materials_user.save(changed)
        said = materials_project.warnings(here)
        assert [(w["kind"], [c[:2] for c in w["changes"]]) for w in said] == [("changed", [("weight.value", "calc")])]
        assert said[0]["changes"][0][2:] == (5.2, 5.6)
        materials_project.keep(m["id"], here)
        assert materials_project.warnings(here) == []                                             # that version refused
        materials_user.save(dict(changed, weight={"value": 5.9, "unit": "kN/m³", "ref": "Datenblatt"}))
        assert [w["kind"] for w in materials_project.warnings(here)] == ["changed"]               # the next one said again
        materials_project.take(m["id"], here)
        assert materials_project.find(m["id"], here)["weight"]["value"] == 5.9 and materials_project.warnings(here) == []
        materials_user.save(dict(materials_user.find(m["id"]), comment="neu"))
        assert [w["kind"] for w in materials_project.warnings(here)] == ["words"]
        assert materials_project.diff({"values": {"f_m_k": 24.0}}, {"values": {"f_m_k": 24.0 + 1e-12}}) == []   # floats read back are not a change


def test_a_material_another_computer_lacks_is_offered_to_the_library():
    here = conftest.project_copy("mat-absent")
    with project.using(here), _Library():
        m = materials_user.save(_mine("Schaumglas", 1.15))
        materials_project.sync([m["id"]], here)
        os.environ[usersettings.MATERIALS_ENV] = str(conftest.tmpdir("mat-absent-other"))
        assert [w["kind"] for w in materials_project.warnings(here)] == ["absent"]
        materials_project.add_to_library(m["id"], here)
        assert materials_user.find(m["id"])["names"]["fr"] == "Schaumglas" and materials_project.warnings(here) == []


def _old_project(name):
    here = conftest.project_copy(name)
    engine.write_json(materials.project_file(here), {"schema_version": "1.0", "materials": [
        {"id": "M1", "name": "Fermacell 18", "value": 1150, "unit": "kg/m³", "source": "Datenblatt"},
        {"id": "M2", "name": "Installationen", "value": 0.5, "unit": "kN/m²"}]})
    src = _build_up(here, "DA-92", [_old_layer("project", "M1", 18), _old_layer("project", "M2", None), _old_layer("sia261", "holz_nadelhoelzer_allgemein")], "1.0")
    return here, src


def test_a_project_of_before_is_poured_into_the_library_once():
    here, src = _old_project("mat-migrate")
    with project.using(here), _Library():
        before = dead_load_source.build_instance(src, here)["vars"]
        names = materials_migrate.migrate(here)
        assert names == ["Fermacell 18", "Installationen"]
        library = {m["names"]["fr"]: m for m in materials_user.materials()}
        assert library["Fermacell 18"]["weight"] == {"value": 11.5, "unit": "kN/m³", "ref": "Datenblatt"}
        assert library["Installationen"]["category"] == "direct"
        data = json.loads(materials.project_file(here).read_text(encoding="utf-8"))
        assert data["schema_version"] == "2.0" and {c["id"] for c in data["materials"]} == {m["id"] for m in library.values()}
        after = dead_load_source.read_source(dead_load_source.folder(here) / "DA-92.json")
        assert after["schema_version"] == "2.0"                     # rewritten through dead_load_migrate (issue #111)
        assert [l["material"] for l in after["layers"][:2]] == [library["Fermacell 18"]["id"], library["Installationen"]["id"]]
        assert after["layers"][1]["pose"] == "surface" and after["layers"][2]["material"] == "sia261:holz_nadelhoelzer_allgemein"
        assert dead_load_source.build_instance(after, here)["vars"] == before
        archived = list(Path(here.archives_dir).glob("materials-*/**/materials.json"))
        assert archived and json.loads(archived[0].read_text(encoding="utf-8"))["schema_version"] == "1.0"
        assert materials_migrate.migrate(here) == [] and len(materials_user.materials()) == 2      # a second opening


def test_a_material_already_in_the_library_is_not_poured_twice():
    here, _src = _old_project("mat-migrate-twice")
    with project.using(here), _Library():
        same = _mine("Fermacell 18", 11.5)
        same["category"] = "gyps"
        materials_user.save(same)
        materials_migrate.migrate(here)
        assert len(materials_user.materials()) == 2                                               # 1150 kg/m³ is 11.5 kN/m³: the one already there
        assert materials_user.find(same["id"])["category"] == "gyps"


def test_a_project_read_only_pours_into_the_library_and_changes_nothing_of_its_own():
    here, src = _old_project("mat-migrate-ro")
    with project.using(here), _Library():
        before = materials.project_file(here).read_bytes()
        assert materials_migrate.migrate(here, read_only=True) == ["Fermacell 18", "Installationen"]
        assert len(materials_user.materials()) == 2
        assert materials.project_file(here).read_bytes() == before
        assert dead_load_source.read_source(dead_load_source.folder(here) / "DA-92.json")["layers"][0]["library"] == "project"
        try:
            materials_project.sync(["u-00000001"], here)
        except validation.ValidationError as exc:
            assert "1.0" in str(exc)
        else:
            raise AssertionError("wrote over a 1.0 file")
