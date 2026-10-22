"""Deleting a position and numbering the ones after it again, everywhere at once (calc/renumbering.py; issue #9, spec docs/requirements/completed/2026-10-08-plan-positions-cotes-numerotation-sections.md, REQ-004, REQ-005, REQ-016, ARCH-001).

The engineer, 08.10.2026: «supprimer S110 fait de S111 un S110, de S130 un S129 … La renumérotation est reportée partout : remplacement dans tous les documents Typst du projet» -- and a position still cited is refused, unless its values are kept («Copier les valeurs») under `S110-old`.

What is held: the table moves every later number of the same letter and storey down, in one pass that cannot catch its own output; a deleted position still cited is refused, one still drawn too; loads are no positions; an id is replaced whole and nothing else -- not S1100, not a colour, not a file, not an archived name --, and not one byte beside it moves, CRLF or LF; the JSON sources are rewritten token by token; every file or none is written, a file changed since the preview stops everything, and the copy in the archives puts the project back; the module imports no Qt and never reads the engine's copy.
"""

import json
import shutil
import sys

import conftest
from conftest import ROOT

import positions_store as store
import project
import sheets
import renumbering
import sharing

SAMPLE = ROOT / "tests" / "projet-exemple"


def _here(name, ids=("S101", "S102", "S110", "S111", "S130", "T101", "S201")):
    """A copy of the example project whose positions are `ids`, a check citing S111 and a section citing S130 and S1100."""
    root = conftest.tmpdir(name) / "Exemple"
    shutil.copytree(SAMPLE, root, ignore=shutil.ignore_patterns("lib", "VERSION", "stamps", "_Archiv"))
    here = project.Project.load(root / "Exemple.woodcore")
    store.write(here, [{"position": pid, "type": "Stütze" if pid[0] == "S" else "Träger", "section_type": "rec", "dimension": "100/200"} for pid in ids])
    for plan in here.plans_dir.glob("*.json"):
        plan.unlink()
    for check in here.checks_dir.glob("*.json"):
        check.unlink()
    for detail in here.details_dir.glob("*.json"):
        detail.unlink()
    return here


def _section(here, text, name="probe.typ", newline="\n"):
    file = here.document_dir("rs") / "Sections" / name
    file.write_bytes(text.replace("\n", newline).encode("utf-8"))
    return file


def _check(here, position, name="BI-99"):
    file = here.checks_dir / f"{name}.json"
    file.write_text(json.dumps({"schema_version": "1.0", "id": name, "position": position, "note": position}, indent=2) + "\n", encoding="utf-8")
    return file


def _ids(here):
    return [row["position"] for row in store.read(here)]


# --- the table ----------------------------------------------------------------------------

def test_the_cascade_moves_every_later_number_of_the_same_letter_and_storey_down():
    ids = ["S101", "S102", "S110", "S111", "S130", "T101", "T111", "S201", "S211", "S1100", "TU01", "X-1"]
    assert renumbering.cascade(ids, ["S110"]) == {"S111": "S110", "S130": "S129", "S1100": "S1099"}
    assert renumbering.cascade(ids, ["S110", "S102"]) == {"S111": "S109", "S130": "S128", "S1100": "S1098"}, "two deleted below: two down"
    two = renumbering.cascade(["S101", "S102", "S103", "S104"], ["S101", "S103"])
    assert two == {"S102": "S101", "S104": "S102"}, two
    assert renumbering.cascade(ids, ["T101"]) == {"T111": "T110"}, "the beams of the first floor only"
    assert renumbering.cascade(["S0100", "S0101"], ["S0100"]) == {"S0101": "S0100"}, "the number keeps its width"
    assert renumbering.cascade(ids, ["X-1"]) == {}, "an id that is not numbered so moves nothing"
    assert renumbering.archived_name("S110", {"S110-old"}) == "S110-old2"


def test_the_numbers_are_moved_in_one_pass_that_never_catches_its_own_output():
    here = _here("renumber_one_pass")
    _section(here, '#member("S110") #member("S111") #member("S130")\n')
    result = renumbering.preview(here, ["S110"], keep_values=True)
    renumbering.apply(here, result)
    text = (here.document_dir("rs") / "Sections" / "probe.typ").read_text(encoding="utf-8")
    assert text == '#member("S110-old") #member("S110") #member("S129")\n', text
    assert _ids(here) == ["S101", "S102", "S110", "S129", "T101", "S201"]


# --- what still names a deleted position ----------------------------------------------------------

def test_a_position_still_cited_is_refused_naming_where_and_kept_values_rename_the_citations():
    here = _here("renumber_cited")
    check = _check(here, "S110")
    section = _section(here, 'Siehe #member("S110").\n')
    result = renumbering.preview(here, ["S110"])
    cited = {(o.path.name, o.line) for o in result.cited["S110"]}
    assert cited == {(check.name, 4), (section.name, 1)}, cited
    assert "S110" in result.refused and "Copier les valeurs" in result.refused
    try:
        renumbering.apply(here, result)
    except renumbering.RenumberError as exc:
        assert exc.code == "refused"
    else:
        raise AssertionError("a position still cited was deleted")
    assert "S110" in _ids(here), "nothing written"
    kept = renumbering.preview(here, ["S110"], keep_values=True)
    assert not kept.refused
    renumbering.apply(here, kept)
    assert json.loads(check.read_text(encoding="utf-8"))["position"] == "S110-old"
    assert json.loads(check.read_text(encoding="utf-8"))["note"] == "S110", "only the position field is a citation"
    assert section.read_text(encoding="utf-8") == 'Siehe #member("S110-old").\n'
    archive = renumbering.read_archive(here)
    assert [(a["position"], a["was"], a["dimension"]) for a in archive] == [("S110-old", "S110", "100/200")]
    # deleted again (the new S110, once S111): its values go under S110-old2
    _check(here, "S110", "BI-98")
    again = renumbering.preview(here, ["S110"], keep_values=True)
    assert again.archived == {"S110": "S110-old2"}
    renumbering.apply(here, again)
    assert [a["position"] for a in renumbering.read_archive(here)] == ["S110-old", "S110-old2"]


def test_a_position_still_drawn_on_a_plan_is_refused_even_with_its_values_kept():
    here = _here("renumber_drawn")
    from domains import plan as model
    source = model.new_source("P01", floor="1")
    source["elements"] = [{"type": "S", "label": "S110", "points": [[10, 10]]}, {"type": "S", "label": "S111", "points": [[20, 10]]}]
    (here.plans_dir / "P01.json").write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    result = renumbering.preview(here, ["S110"], keep_values=True)
    assert result.drawn["S110"] and "drawn on a plan" in result.refused
    result = renumbering.preview(here, ["S102"])
    renumbering.apply(here, result)
    labels = [e["label"] for e in json.loads((here.plans_dir / "P01.json").read_text(encoding="utf-8"))["elements"]]
    assert labels == ["S109", "S110"], labels


def test_loads_are_no_positions_and_are_never_renumbered():
    here = _here("renumber_loads", ids=("L101", "L102", "L103", "S101"))
    from domains import plan as model
    source = model.new_source("P02", floor="1")
    source["plan_type"] = "loadpath"
    source["elements"] = [{"type": "LL", "subtype": "vert", "label": "L103", "points": [[0, 0], [100, 0]]},
                          {"type": "L", "subtype": "linie", "label": "L103", "points": [[0, 50], [100, 50]]}]
    file = here.plans_dir / "P02.json"
    file.write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    renumbering.apply(here, renumbering.preview(here, ["L101"]))
    labels = [(e["type"], e["label"]) for e in json.loads(file.read_text(encoding="utf-8"))["elements"]]
    assert labels == [("LL", "L103"), ("L", "L102")], labels


# --- the files ------------------------------------------------------------------------------

def test_an_id_is_replaced_whole_and_not_one_byte_beside_it_moves():
    here = _here("renumber_bytes", ids=("S101", "S110", "S111", "S1110", "D101", "D102"))
    body = ('// S111 in a comment\n#member("S111")\n#show-plan("P", highlight: ("S111", "S1110"))\n'
            '#rect(fill: rgb("#D102"))\n#image("Images/S111.png")\nS111. S111, (S111) S111-old\n')
    crlf = _section(here, body, "crlf.typ", "\r\n")
    lf = _section(here, body, "lf.typ")
    result = renumbering.preview(here, ["S110", "D101"])
    renumbering.apply(here, result)
    expected = ('// S110 in a comment\n#member("S110")\n#show-plan("P", highlight: ("S110", "S1109"))\n'
                '#rect(fill: rgb("#D102"))\n#image("Images/S111.png")\nS110. S110, (S110) S111-old\n')
    assert lf.read_bytes() == expected.encode("utf-8"), lf.read_text(encoding="utf-8")
    assert crlf.read_bytes() == expected.replace("\n", "\r\n").encode("utf-8")


def test_an_occurrence_unticked_is_left_as_it_is():
    here = _here("renumber_untick", ids=("S101", "S301", "S355"))     # S355: the letter S, storey 3, number 55 -- and a steel grade
    file = _section(here, '#member("S355")\nStahl S355\n')
    result = renumbering.preview(here, ["S301"])
    steel = [o for o in result.occurrences if o.path == file.resolve() and o.line == 2]
    assert len(steel) == 1 and steel[0].text == "Stahl S355" and steel[0].new == "S354", "the steel grade is listed, with its line"
    # the example's own page on structural steel names S355 too: listed, every line of it, for the engineer to untick
    grades = [o for o in result.occurrences if o.path.name == "structural-steel.typ"]
    assert grades and all("S355" in o.text for o in grades)
    renumbering.apply(here, result, unchecked=[steel[0].key] + [o.key for o in grades])
    assert file.read_text(encoding="utf-8") == '#member("S354")\nStahl S355\n'
    steel_page = here.document_dir("bp") / "Sections" / "structural-steel.typ"
    assert steel_page.read_bytes() == (SAMPLE / steel_page.relative_to(here.root)).read_bytes(), "nothing unticked is written"


def test_the_json_sources_are_rewritten_token_by_token():
    here = _here("renumber_json")
    file = _check(here, "S111")
    raw = file.read_text(encoding="utf-8").replace('"note": "S111"', '"note": "S111"  ')   # a spacing json.dumps would not keep
    file.write_text(raw, encoding="utf-8")
    renumbering.apply(here, renumbering.preview(here, ["S110"]))
    assert file.read_text(encoding="utf-8") == raw.replace('"position": "S111"', '"position": "S110"')


def test_a_schema_s_elements_and_a_plan_drawn_before_with_a_shared_number_follow_the_cascade():
    """REQ-004, CON-006: a schema element's `position` is renumbered and nothing else of it -- not a note naming the same id --, and on a plan drawn before issue #9, where two elements share a number, both elements move together."""
    here = _here("renumber_details")
    from domains import plan as model
    detail = here.details_dir / "D-99.json"
    raw = json.dumps({"schema_version": "1.0", "id": "D-99", "elements": [{"position": "S111", "note": "S111"}, {"position": "S130"}, {"position": "T101"}]}, indent=2) + "\n"
    detail.write_text(raw, encoding="utf-8")
    source = model.new_source("P01", floor="1")
    source["elements"] = [{"type": "S", "label": "S111", "points": [[10, 10]]}, {"type": "S", "label": "S111", "points": [[40, 10]]}]
    plan_file = here.plans_dir / "P01.json"
    plan_file.write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    renumbering.apply(here, renumbering.preview(here, ["S110"]))
    assert detail.read_text(encoding="utf-8") == raw.replace('"position": "S111"', '"position": "S110"').replace('"position": "S130"', '"position": "S129"')
    labels = [e["label"] for e in json.loads(plan_file.read_text(encoding="utf-8"))["elements"]]
    assert labels == ["S110", "S110"], labels


def test_every_file_or_none_is_written_and_a_change_meanwhile_stops_everything():
    here = _here("renumber_atomic")
    first, second = _section(here, '#member("S111")\n', "a.typ"), _section(here, '#member("S130")\n', "b.typ")
    before = {p: p.read_bytes() for p in (first, second, store.path(here))}
    result = renumbering.preview(here, ["S110"])
    real, calls = sharing._put, []

    def failing(path, data):
        calls.append(path)
        if len(calls) == 2:
            raise OSError(28, "No space left on device", str(path))
        return real(path, data)
    sharing._put = failing
    try:
        renumbering.apply(here, result)
    except sharing.SharingError as exc:
        assert exc.code == "write_failed"
    else:
        raise AssertionError("a failed write was not reported")
    finally:
        sharing._put = real
    assert {p: p.read_bytes() for p in before} == before, "what had been written was put back"
    result = renumbering.preview(here, ["S110"])
    first.write_text('#member("S111") // edited meanwhile\n', encoding="utf-8")
    try:
        renumbering.apply(here, result)
    except sharing.SharingError as exc:
        assert exc.code == "changed_meanwhile"
    else:
        raise AssertionError("a file edited since the preview was written over")
    assert "S110" in _ids(here)


def test_the_copy_in_the_archives_puts_the_project_back():
    here = _here("renumber_restore")
    file = _section(here, '#member("S111")\n')
    _check(here, "S110")
    before = {p: p.read_bytes() for p in (file, store.path(here))}
    folder = renumbering.apply(here, renumbering.preview(here, ["S110"], keep_values=True))
    assert renumbering.unfinished(here) == [], "a renumbering done says so"
    archive = here.sources_dir / renumbering.ARCHIVE_FILE
    assert archive.is_file()
    renumbering.restore(here, folder)
    assert {p: p.read_bytes() for p in before} == before and not archive.exists(), "the file it made new is taken away"
    renumbering._intent(folder, done=False)
    assert renumbering.unfinished(here) == [folder]


def test_a_rename_is_a_table_of_one_entry():
    here = _here("renumber_rename")
    file = _section(here, '#member("S111") #member("S1110")\n')
    renumbering.apply(here, renumbering.rename_preview(here, "S111", "S120"))
    assert file.read_text(encoding="utf-8") == '#member("S120") #member("S1110")\n'
    assert "S120" in _ids(here) and "S111" not in _ids(here)


def test_the_engine_s_copy_the_export_and_the_archives_are_never_read():
    here = _here("renumber_scope")
    engine = here.generated_dir / "lib" / "probe.typ"
    engine.parent.mkdir(parents=True, exist_ok=True)
    engine.write_text('#member("S111")\n', encoding="utf-8")
    kept = here.archives_dir / "old.typ"
    kept.parent.mkdir(parents=True, exist_ok=True)
    kept.write_text('#member("S111")\n', encoding="utf-8")
    sheet = sheets.folder(here) / "B09.typ"   # Plans/ before, the position plan's exports laid out by folders (issue #64)
    sheet.parent.mkdir(parents=True, exist_ok=True)
    sheet.write_text('#sheet-viewport(plan: "P", highlight: "S111")\n', encoding="utf-8")
    files = renumbering.typst_files(here)
    assert sheet.resolve() in files and engine.resolve() not in files and kept.resolve() not in files
    renumbering.apply(here, renumbering.preview(here, ["S110"]))
    assert engine.read_text(encoding="utf-8") == '#member("S111")\n' and 'highlight: "S110"' in sheet.read_text(encoding="utf-8")


def test_the_module_imports_no_qt():
    import subprocess
    code = "import sys; sys.path.insert(0, 'calc'); import renumbering; print(any(m.startswith('PySide') for m in sys.modules))"
    out = subprocess.run([sys.executable, "-c", code], cwd=str(ROOT), capture_output=True, text=True)
    assert out.returncode == 0 and out.stdout.strip() == "False", (out.stdout, out.stderr)


def test_an_old_position_is_exported_apart_and_the_report_prints_its_values_saying_so_in_orange():
    """REQ-016: «Copier les valeurs» -- the deleted position's values are exported under S110-old, a call that names it prints them and says, in the report's language, that they are the values of the former S110; no list of the project's positions shows it, and every export warns of it."""
    import subprocess
    import export_all
    import unicodedata
    if not conftest.have_typst():
        raise conftest.Skip("typst is not on the path")
    here = _here("renumber_report")
    rows = store.read(here)
    rows[2].update({"material": "Fichte", "strength_class": "C24", "moisture_class": 1})    # S110
    store.write(here, rows)
    _section(here, '#position("S110")\n')
    renumbering.apply(here, renumbering.preview(here, ["S110"], keep_values=True))
    project.sync_engine(here)
    with project.using(here):
        export_all.run()
    index = json.loads((here.data_dir / "positions-index.json").read_text(encoding="utf-8"))
    assert index["archived"] == ["S110-old"] and "S110-old" not in index["positions"] and "S110" in index["positions"]
    record = json.loads((here.data_dir / "positions" / "S110-old.json").read_text(encoding="utf-8"))
    assert record["archived"] == {"was": "S110", "deleted": record["archived"]["deleted"]} and record["strength_class"] == "C24"
    for lang, words in (("de", "Berechnung mit den Werten der früheren Position S110"), ("fr", "Calcul sur les valeurs de l’ancienne position S110"), ("en", "Calculated on the values of the former position S110")):
        probe = here.typst_root / f"probe-{lang}.typ"
        probe.write_text(f'#import "/000-Typst-Config/commands.typ": *\n#set-report-language("{lang}")\n#position("S110-old")\n\nLIST: #ids("position").join(",") END\n', encoding="utf-8")
        out = subprocess.run([project.typst_executable(), "compile", "--root", str(here.typst_root), str(probe), str(probe.with_suffix(".pdf"))],
                             capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert out.returncode == 0, out.stderr
        from pypdf import PdfReader
        text = unicodedata.normalize("NFKC", "\n".join(p.extract_text() for p in PdfReader(str(probe.with_suffix(".pdf"))).pages))
        flat = " ".join(text.split())
        assert unicodedata.normalize("NFKC", words) in flat and "C24" in flat, (lang, flat)
        listed = flat.split("LIST:", 1)[1].split("END", 1)[0]
        assert "S110" in listed and "S110-old" not in listed, ("the list of positions does not show it", listed)
