"""The engineer's own library of materials (calc/domains/materials_user.py, spec docs/requirements/active/2026-10-24-onglet-materiaux.md, REQ-001 to REQ-003, REQ-006, REQ-007, REQ-012, ARCH-010; issue #110).

What is held:

* **REQ-001** -- `usersettings.materials_dir()`: `WOODCORE_MATERIALS` first, a folder beside the settings when only `WOODCORE_SETTINGS` is set (a test run), `%APPDATA%\\Woodcore\\materials\\` otherwise; and this suite's library is never the engineer's;
* **REQ-002** -- a material written is checked first: an invalid one refused and the file left as it was; a file that cannot be read refused naming it and the field; a shipped material refused;
* **REQ-003** -- an id `u-<8 hex>`, kept by a rename;
* **REQ-006, REQ-007** -- duplicate, save, delete, the PDF removed with the last material naming it;
* **REQ-012** -- a PDF copied under a clean name, `-2` for another file of that name, the same file again for the same bytes;
* **ARCH-010** -- the two schemas of a material hold the same shape.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import conftest
import usersettings
import validation
from domains import materials_catalogue, materials_contract, materials_user


class _Library:
    """A library of its own for one test: `WOODCORE_MATERIALS` pointed at an empty folder, put back after."""

    def __enter__(self):
        self.was = os.environ.get(usersettings.MATERIALS_ENV)
        self.path = conftest.tmpdir("materials-library")
        os.environ[usersettings.MATERIALS_ENV] = str(self.path)
        return self.path

    def __exit__(self, *_):
        if self.was is None:
            os.environ.pop(usersettings.MATERIALS_ENV, None)
        else:
            os.environ[usersettings.MATERIALS_ENV] = self.was


def _other(name="Verre cellulaire", value=1.15):
    m = materials_user.blank("other")
    m["names"]["fr"] = name
    m["weight"] = {"value": value, "unit": "kN/m³", "ref": "fiche du fabricant"}
    return m


def test_the_folder_is_the_variables_then_beside_the_settings_then_appdata():
    saved = {k: os.environ.get(k) for k in (usersettings.MATERIALS_ENV, usersettings.ENV, "APPDATA")}
    try:
        os.environ[usersettings.MATERIALS_ENV] = r"C:\somewhere\mats"
        assert usersettings.materials_dir() == Path(r"C:\somewhere\mats")
        os.environ.pop(usersettings.MATERIALS_ENV)
        os.environ[usersettings.ENV] = r"C:\tests\.settings-1.json"
        assert usersettings.materials_dir() == Path(r"C:\tests\.settings-1-materials")
        os.environ.pop(usersettings.ENV)
        os.environ["APPDATA"] = r"C:\Users\x\AppData\Roaming"
        assert usersettings.materials_dir() == Path(r"C:\Users\x\AppData\Roaming") / "Woodcore" / "materials"
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_this_suites_library_is_never_the_engineers():
    """CON-004: under the suite, the library is beside the suite's settings file -- never under %APPDATA%."""
    folder = usersettings.materials_dir().resolve()
    assert conftest.ROOT.resolve() in folder.parents, folder


def test_an_invalid_material_is_refused_and_the_file_left_as_it_was():
    with _Library() as path:
        saved = materials_user.save(_other())
        before = (path / "materials.json").read_bytes()
        bad = dict(_other(), weight={"value": -3, "unit": "kN/m³"})
        for broken, said in ((bad, "weight.value"), (dict(_other(), category="cheese"), "category"), (dict(_other(), names={}), "names")):
            try:
                materials_user.save(broken)
            except validation.ValidationError as exc:
                assert said in str(exc), (said, exc)
            else:
                raise AssertionError("saved %r" % said)
        assert (path / "materials.json").read_bytes() == before
        assert materials_user.find(saved["id"])["names"]["fr"] == "Verre cellulaire"


def test_a_file_that_cannot_be_read_stops_naming_it_and_is_never_written_over():
    with _Library() as path:
        (path / "materials.json").write_text('{"schema_version": "1.0", "materials": [{"id": "u-00000001", "type": "rock"}]}', encoding="utf-8")
        for call in (materials_user.read, lambda: materials_user.save(_other())):
            try:
                call()
            except validation.ValidationError as exc:
                assert "materials.json" in str(exc)
            else:
                raise AssertionError("read a malformed library")
        assert "rock" in (path / "materials.json").read_text(encoding="utf-8")


def test_a_shipped_material_is_read_only():
    with _Library():
        try:
            materials_user.save(materials_catalogue.find("sia265:C24"))
        except validation.ValidationError as exc:
            assert "read only" in str(exc)
        else:
            raise AssertionError("saved a shipped material")


def test_an_id_is_drawn_once_and_kept_by_a_rename():
    with _Library():
        m = materials_user.save(_other())
        assert materials_contract.USER_ID.match(m["id"]), m["id"]
        m["names"]["fr"] = "Schaumglas"
        materials_user.save(m)
        assert [x["id"] for x in materials_user.materials()] == [m["id"]]
        assert materials_user.find(m["id"])["names"]["fr"] == "Schaumglas"


def test_duplicating_a_shipped_class_makes_a_material_of_ones_own():
    with _Library():
        c24 = materials_catalogue.find("sia265:C24")
        mine = materials_user.duplicate(c24, "SIA 265")
        assert mine["id"].startswith("u-") and mine["type"] == "member" and mine["values"] == c24["values"]
        assert mine["comment"].startswith("← SIA 265")
        assert mine["source"] == {"kind": "book", "ref": "SIA 265:2021, Tabelle 8"}
        mine.pop("origin")
        mine.pop("excerpt")
        materials_user.save(mine)
        assert materials_user.find(mine["id"])["values"]["f_m_d"] == 14.1


def test_a_pdf_is_copied_under_a_clean_name_and_removed_with_its_last_material():
    with _Library() as path:
        here = conftest.tmpdir("materials-pdfs")
        one = here / "Fiche technique (v2).pdf"
        one.write_bytes(b"%PDF-1.4 one")
        other = here / "sub"
        other.mkdir()
        two = other / "Fiche technique (v2).pdf"
        two.write_bytes(b"%PDF-1.4 two")
        assert materials_user.import_pdf(one) == "sources/fiche-technique-v2.pdf"
        assert materials_user.import_pdf(one) == "sources/fiche-technique-v2.pdf"     # the same bytes: the same copy
        assert materials_user.import_pdf(two) == "sources/fiche-technique-v2-2.pdf"   # another file of that name
        one.unlink()
        a = _other("A")
        a["source"] = {"kind": "pdf", "file": "sources/fiche-technique-v2.pdf"}
        b = _other("B")
        b["source"] = {"kind": "pdf", "file": "sources/fiche-technique-v2.pdf"}
        materials_user.save(a)
        materials_user.save(b)
        assert materials_user.source_path(a).read_bytes() == b"%PDF-1.4 one"   # the copy, the original gone
        materials_user.delete(a["id"])
        assert (path / "sources" / "fiche-technique-v2.pdf").is_file()          # still named by B
        materials_user.delete(b["id"])
        assert not (path / "sources" / "fiche-technique-v2.pdf").exists()
        try:
            materials_user.import_pdf(here / "sub")
        except validation.ValidationError:
            pass
        else:
            raise AssertionError("imported a folder")


def test_the_two_schemas_of_a_material_hold_one_shape():
    """ARCH-010: a project's copy (materials 2.0) and the engineer's library describe a material alike -- every property of the library's, the same in the copy's (its source also a text, for 1.0)."""
    schemas = conftest.ROOT / "schemas"
    user = json.loads((schemas / "user-materials.schema.json").read_text(encoding="utf-8"))["properties"]["materials"]["items"]["properties"]
    copy = json.loads((schemas / "materials.schema.json").read_text(encoding="utf-8"))["properties"]["materials"]["items"]["properties"]
    for key, sub in user.items():
        theirs = dict(copy[key])
        mine = dict(sub)
        if key == "source":
            theirs.pop("type"), mine.pop("type")
        if key in ("source", "id"):
            theirs.pop("description", None), mine.pop("description", None)
        assert theirs == mine, key
