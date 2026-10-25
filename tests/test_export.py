"""What the export guarantees about the files it writes.

Three things, each of which was untrue or unchecked before v0.59:

* every artifact carries the schema version the code that reads it expects, and an older one is refused rather than read as a current one -- the walker ignored `const` and `enum` until v0.59, so the version field was required to be present and never compared to anything;
* a position deleted from Excel takes its record with it, instead of leaving a `data/positions/<id>.json` that `show-position` -- `#member` since v0.94 -- goes on printing (found in v0.59: `D001`);
* the export is reproducible -- the same inputs give the same bytes, which is what makes a `git diff` on `data/` a diff of values rather than of noise.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import os
import re
import shutil
import subprocess
import sys

import conftest
from conftest import ROOT, Skip
import validation

# Every file the export writes, with the schema it is validated against.
ARTIFACTS = (
    ("calculations.json", "calculations"),
    ("positions-index.json", "positions-index"),
    ("connectors.json", "connectors"),
    ("connections.json", "connections"),
    ("plans.json", "plans"),
    ("statics.json", "statics"),
)


def test_every_artifact_still_validates():
    """The files in data/ pass the schema and the business rules they were written under.

    Cheap, and it is the check that says whether the export on disk is the one this code produces -- a record left over from an older version fails here rather than in Typst.
    """
    for name, schema in ARTIFACTS:
        data = conftest.exported(name)
        validation.validate_structure(data, schema)
        checker = getattr(validation, f"validate_{schema.replace('-', '_')}_business", None)
        if checker is not None:
            checker(data)


def test_position_records_still_validate():
    index = conftest.exported("positions-index.json")
    for pid in index["positions"]:
        record = conftest.exported(f"positions/{pid}.json")
        validation.validate_structure(record, "position")
        validation.validate_positions_business(record)


def test_every_schema_pins_its_version():
    """A schema that does not fix `schema_version` cannot catch a record written at another one.

    Until v0.59 none of them did, and Typst reads the field nowhere at all -- so the versioning of section 3.0 was a field that was written and never compared.
    """
    for name, schema in ARTIFACTS + (("positions/", "position"),):
        spec = json.loads((ROOT / "schemas" / f"{schema}.schema.json").read_text(encoding="utf-8"))
        node = spec["properties"]["schema_version"]
        assert "const" in node or "enum" in node, (
            f"schemas/{schema}.schema.json does not pin schema_version -- a record "
            f"written at an older version would pass as a current one"
        )


def test_a_record_at_the_wrong_version_is_refused():
    """The walker enforces `const`, rather than declaring it and walking past."""
    data = dict(conftest.exported("positions-index.json"))
    data["schema_version"] = "0.9"
    try:
        validation.validate_structure(data, "positions-index")
    except validation.ValidationError as exc:
        assert "0.9" in str(exc), exc
    else:
        assert False, "a positions-index at version 0.9 was accepted as a 1.0"


def test_the_index_and_the_position_files_agree():
    """Every id the index names has a file, and every file is named by the index.

    The second half is the one v0.59 added the sweep for: `data/positions/D001.json` outlived its row in Excel, and `show-position("D001")` went on printing an element the project does not carry.
    """
    index = set(conftest.exported("positions-index.json")["positions"])
    folder = conftest.PROJECT.data_dir / "positions"
    if not folder.is_dir():
        raise Skip("data/positions/ is not there -- run the export first")
    on_disk = {p.stem for p in folder.glob("*.json")}
    assert index <= on_disk, f"the index names positions with no record: {sorted(index - on_disk)}"
    assert on_disk <= index, (
        f"data/positions/ holds records of positions Positions Element no longer has: "
        f"{sorted(on_disk - index)} -- the export should have swept them "
        f"(export_all._sweep_positions)"
    )


def test_the_sweep_removes_a_record_whose_row_is_gone():
    """The sweep itself, driven directly: a file whose id is not in the index goes."""
    import export_all
    folder = conftest.PROJECT.data_dir / "positions"
    if not folder.is_dir():
        raise Skip("data/positions/ is not there -- run the export first")
    index = conftest.exported("positions-index.json")["positions"]
    ghost = folder / "ZZZ999-test-ghost.json"
    ghost.write_text('{"schema_version": "1.2", "position": "ZZZ999"}', encoding="utf-8")
    try:
        export_all._sweep_positions(index)
        assert not ghost.exists(), (
            "a record of a position the index does not name survived the sweep"
        )
    finally:
        if ghost.exists():
            ghost.unlink()
    # and the real ones are still there
    for pid in index:
        assert (folder / f"{pid}.json").exists(), f"the sweep removed {pid}, which the index names"


def _example_copy(name):
    """A whole copy of the project the tests work on -- its sources, its sections, its export and its engine --, for a test that runs the export on it in a subprocess."""
    import project
    d = conftest.tmpdir(name)
    shutil.copytree(conftest.PROJECT.root, d / "P", ignore=shutil.ignore_patterns(".probe", "*.lock", ".woodcore-*"))
    return project.Project.load(d / "P" / conftest.PROJECT.file.name)


def _export(here, *more):
    return subprocess.run(
        [sys.executable, str(ROOT / "calc" / "export_all.py"), "--project", str(here.file), *more],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(ROOT),
        env={k: v for k, v in dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8").items() if k != "WOODCORE_PROJECT"},   # the child prints «Übung», «Stütze»: in the console's code page otherwise, which a UTF-8 reader fails on
    )


def test_the_export_is_reproducible():
    """Run twice, data/ comes out byte for byte the same -- on a copy of the example project, whose loads are cases entered in Woodcore since issue #109 (the engineer's own workbook was needed until then, and the test skipped without it).

    It is what makes a `git diff` on data/ readable: a value that changed shows as a value that changed, not inside a wall of reordered keys and redrawn figures. The first export is run over a data/calculations.json of an earlier Woodcore (1.8): it is not stopped by it, and writes 1.9 (REQ-007, C-1).
    """
    here = _example_copy("export")
    data = here.data_dir
    calculations = data / "calculations.json"
    old = json.loads(calculations.read_text(encoding="utf-8"))
    old["schema_version"] = "1.8"
    calculations.write_text(json.dumps(old), encoding="utf-8")
    out = _export(here)
    assert out.returncode == 0, out.stderr or out.stdout
    assert json.loads(calculations.read_text(encoding="utf-8"))["schema_version"] == "1.9", "the export over an old file writes the current one"
    d = conftest.tmpdir("export_before")
    before = d / "before"
    shutil.copytree(data, before)
    # The reference workbook too: openpyxl stamps the time of every save into docProps/core.xml, so it was rewritten by every export and every run of this very test left the committed file modified (periodic audit 260916, AUD-1-3).
    reference = here.docs_dir / "typst-reference.xlsx"
    reference_before = reference.read_bytes() if reference.exists() else None
    out = _export(here)
    assert out.returncode == 0, out.stderr or out.stdout
    differences = []
    for p in sorted(data.rglob("*")):
        if p.is_dir():
            continue
        twin = before / p.relative_to(data)
        if not twin.exists():
            differences.append(f"  {p.relative_to(data)} was not there before")
        elif twin.read_bytes() != p.read_bytes():
            differences.append(f"  {p.relative_to(data)} differs")
    for p in sorted(before.rglob("*")):
        if p.is_file() and not (data / p.relative_to(before)).exists():
            differences.append(f"  {p.relative_to(before)} disappeared")
    assert not differences, "a second export changed data/:\n" + "\n".join(differences)
    if reference_before is not None:
        assert reference.read_bytes() == reference_before, "a second export rewrote docs/typst-reference.xlsx although data/ did not change"


def test_an_export_of_an_earlier_woodcore_stops_the_compile_and_check_says_what_to_do():
    """Issue #109, REQ-007, C-1: a data/calculations.json at 1.8 -- the load workbooks' cases -- stops the report's compile, saying «Import données» (lib/calc-engine-core.typ, `load-calculations`, the version the export writes); `woodcore-cli check`, which writes nothing, says it too and is not stopped by it."""
    import registry
    engine_text = (ROOT / "lib" / "calc-engine-core.typ").read_text(encoding="utf-8")
    assert '#let calculations-version = "%s"' % registry.SCHEMA_VERSION in engine_text, "the engine reads the version the export writes"
    here = _example_copy("old_export")
    calculations = here.data_dir / "calculations.json"
    old = json.loads(calculations.read_text(encoding="utf-8"))
    old["schema_version"] = "1.8"
    calculations.write_text(json.dumps(old), encoding="utf-8")
    note = registry.old_export_note(here.data_dir)
    assert note is not None and note.code == "calculations_old_export" and note.args == {"version": "1.8", "current": registry.SCHEMA_VERSION}
    check = subprocess.run([sys.executable, str(ROOT / "calc" / "cli.py"), "check", "--project", str(here.file)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(ROOT),
                           env={k: v for k, v in dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8").items() if k != "WOODCORE_PROJECT"})
    assert check.returncode == 0 and "earlier version of Woodcore" in check.stderr and "Import données" in check.stderr, check.stdout + check.stderr
    assert json.loads(calculations.read_text(encoding="utf-8"))["schema_version"] == "1.8", "check writes nothing"
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    probe = here.typst_root / "probe-old.typ"
    probe.write_text('#import "/000-Typst-Config/commands.typ": *\n#var("q_k1", domain: ("snow-load", "SL"))\n', encoding="utf-8")
    run = subprocess.run(["typst", "compile", "--root", str(here.typst_root), str(probe), str(probe.with_suffix(".pdf"))],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    message = conftest.panic_message(run.stderr) or run.stderr
    assert run.returncode != 0 and "earlier version of Woodcore" in message and "Import données" in message and '"1.8"' in message, message


def test_every_case_a_section_of_the_example_cites_is_exported():
    """Issue #109, REQ-004: each `domain-file(kind, id)` of a load that the example's sections and the report's 004-einwirkungen.typ include names a case of data/calculations.json -- the three ids corrected (WL-Fluchttreppe+Geraete, EL+AL-Dach_mit_Wasser, EL+AL-Dach_ohne_Wasser) among them -- and each case is a source of Woodcore-Datei/loads/."""
    here = conftest.PROJECT
    calculations = json.loads((here.data_dir / "calculations.json").read_text(encoding="utf-8"))["domains"]
    cited = set()
    for path in here.root.rglob("*.typ"):
        if any(part.startswith((".", "000-Woodcore")) for part in path.relative_to(here.root).parts):
            continue
        cited |= set(re.findall(r'domain-file\("((?:dead|snow|wind)-load)", "([^"]+)"\)', path.read_text(encoding="utf-8")))
    assert {("dead-load", "EL+AL-Dach_mit_Wasser"), ("dead-load", "EL+AL-Dach_ohne_Wasser"), ("wind-load", "WL-Fluchttreppe+Geraete"), ("snow-load", "SL")} <= cited, cited
    missing = sorted(c for c in cited if c[1] not in calculations[c[0]]["instances"])
    assert not missing, missing
    for kind in ("dead-load", "snow-load", "wind-load"):
        for case, instance in calculations[kind]["instances"].items():
            assert instance.get("source_file", "").startswith("loads/") and (here.sources_dir / instance["source_file"]).is_file(), (kind, case)


# --- the strength class, its own field ------------------------------------------------

def _row(**fields):
    row = {"position": "T001", "type": "Träger", "material": "Fichte", "strength_class": "C24", "section_type": "rec",
           "dimension": "100/200", "units": "mm", "moisture_class": 2, "description": ""}
    row.update(fields)
    return row


def test_the_strength_class_is_read_from_its_own_field_and_the_material_stays_the_material():
    """The engineer split `material` in two: what the element is made of (Fichte) and its strength class (C24), the one a connector and a schema's label read."""
    import export_all
    (position,), _notes = export_all._positions([_row()])
    assert position["material"] == "Fichte" and position["strength_class"] == "C24"
    validation.validate_structure(position, "position")


def test_the_moisture_class_is_read_under_the_workbooks_new_header_and_its_old_one_and_a_bad_one_is_a_warning():
    """A workbook imported (positions_store.from_sheet) reads the moisture class under `moisture class` and under `Wood moisture class`; a moisture class that is not 1, 2 or 3 is exported blank with a warning since v0.114 -- it stopped the export until then."""
    import export_all
    import positions_store
    sheet = {"position": "T001", "type": "Träger", "moisture class": 2}
    old = {"position": "T001", "type": "Träger", "Wood moisture class": 2}
    for row in (sheet, old):
        ((position,), _notes) = export_all._positions(positions_store.from_sheet([row])[0])
        assert position["moisture_class"] == 2
    (position,), notes = export_all._positions([_row(moisture_class="$")])
    assert position["moisture_class"] is None and [n.code for n in notes] == ["position_moisture"] and "T001" in notes[0]


def test_a_record_exported_before_the_split_still_gives_its_strength_class():
    from domains import connector, schema
    assert connector.strength_class_of({"material": "GL24h"}) == "GL24h", "an older record's material WAS its strength class"
    assert connector.strength_class_of({"material": "Fichte", "strength_class": "C24"}) == "C24"
    assert connector.strength_class_of({"material": "Fichte", "strength_class": ""}) == "", "a blank strength class is never read off the material"
    element = {"id": "E1", "kind": "linear", "points": [[0, 0], [100, 0]], "position": "T001"}
    positions = {"T001": {"material": "Fichte", "strength_class": "C24", "dimension": "100/200", "units": "mm"}}
    assert schema.element_caption(element, positions) == "T001 C24 100/200"


# --- the dimension, facultative ----------------------------------------------------------

def _dimensionless_rows():
    """Positions as the Positions tab keeps them: a timber beam, a support with no dimension and no unit, and a load from above with a unit and no dimension; and a column whose record names no dimension and no unit at all."""
    rows = [{"position": "T001", "type": "Träger", "material": "Fichte", "strength_class": "C24", "section_type": "rec", "dimension": "100/200", "units": "mm", "moisture_class": 1},
            {"position": "M001", "type": "Auflager"},
            {"position": "L001", "type": "Last von oben", "units": "mm", "description": "aus dem Dach"}]
    bare = [{"position": "S001", "type": "Stütze", "material": "Fichte", "strength_class": "GL24h", "moisture_class": 1}]
    return rows, bare


def test_a_position_needs_no_dimension():
    """The engineer, v0.87: «dans le excel Positions, les dimensions d'une position ne sont pas obligatoires». A blank `dimension` cell, and a sheet with no `dimension` or `units` column at all, export as "" -- as `material` has since v0.16 -- and pass the schema and the business rules, which refused an empty dimension until then."""
    import export_all
    book, bare = _dimensionless_rows()
    positions = {p["position"]: p for p in export_all._positions(book)[0]}
    assert (positions["T001"]["dimension"], positions["T001"]["units"]) == ("100/200", "mm")
    assert (positions["M001"]["dimension"], positions["M001"]["units"]) == ("", ""), positions["M001"]
    assert (positions["L001"]["dimension"], positions["L001"]["units"]) == ("", "mm"), "the unit is carried through as typed; it is the summaries that leave it out"
    (column_less,), _notes = export_all._positions(bare)
    assert (column_less["dimension"], column_less["units"]) == ("", ""), column_less
    for record in (*positions.values(), column_less):
        validation.validate_structure(record, "position")
        validation.validate_positions_business(record)
    index = {"schema_version": "1.0", "positions": [*positions, column_less["position"]]}
    validation.validate_structure(index, "positions-index")


def test_a_position_without_a_dimension_is_summarised_without_a_dangling_separator():
    """What the window prints of a position -- «T001 — Träger C24 100/200 mm» in its combos, «T001 C24 100/200» on a schema's element -- leaves out a blank dimension with its unit, and never prints a unit alone nor a trailing separator."""
    import export_all
    from domains import connector, schema
    book, bare = _dimensionless_rows()
    records = {p["position"]: p for p in export_all._positions(book)[0]}
    records.update({p["position"]: p for p in export_all._positions(bare)[0]})
    assert connector.position_dimension(records["T001"]) == "100/200 mm"
    assert connector.position_dimension(records["M001"]) == ""
    assert connector.position_dimension(records["L001"]) == "", "a unit left beside a blank dimension is not printed on its own"
    assert connector.position_dimension({"dimension": "180", "units": ""}) == "180"
    assert connector.position_dimension({}) == "" and connector.position_dimension(None) == ""
    # the two combos, as the tabs build them (schema_tab.fill_positions, plan_tab's number combo)
    assert " ".join(part for part in ("Auflager", "", "", connector.position_dimension(records["M001"])) if part) == "Auflager"
    assert ", ".join(part for part in ("Last von oben", "", connector.position_dimension(records["L001"])) if part) == "Last von oben"
    # a schema element's label, and the warning for a band that cannot be sized
    element = {"id": "E1", "kind": "linear", "points": [[0, 0], [100, 0]], "view": "h", "position": "S001"}
    assert schema.element_caption(element, records) == "S001 GL24h"
    assert schema.element_caption({**element, "position": "M001"}, records) == "M001"
    from domains import section
    assert section.sides({"dimension": "", "units": "mm"}) is None and section.sides(None) is None
    ((eid, reason),) = schema._section_reasons({"elements": [element]}, records)
    assert eid == "E1" and "''" not in str(reason) and "—" in str(reason), str(reason)
    # no module of the window puts a position's dimension and its unit together itself -- the form both tabs had, which printed «mm» alone for a blank dimension: connector.position_dimension is the one place that decides the unit goes with its dimension
    for path in sorted((ROOT / "calc" / "tools").glob("*.py")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            assert not (re.search(r"""get\(\s*['"]dimension['"]""", line) and re.search(r"""get\(\s*['"]units['"]""", line)), (
                f"{path.name}:{number} prints a position's dimension and unit itself -- print them through connector.position_dimension")
