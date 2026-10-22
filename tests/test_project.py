"""Where the program is, and where the project it works on is (calc/project.py, v0.81, docs/architecture/layout.md §11).

Until v0.80 every module derived both from its own `__file__`: the project's workbooks two levels above the code, its export and its sources beside it. That tied one copy of the code to one project, which is what the split into an installed program (Woodcore) and project folders undoes. A project is now named by its `.woodcore` file, and a module asks `project.current()` for a path at the moment it needs one.

The checks here hold the file's rules, the resolution order of `current()`, and -- the one that matters -- that no module of calc/ has gone back to deriving a project path from its own location.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import conftest
from conftest import CALC, ROOT

import documents
import project
import validation

# an absolute folder of the machine running the tests: "C:/" on Windows, "/" elsewhere, where "C:/" is a relative name
ELSEWHERE = Path(os.path.abspath(os.sep)).as_posix().rstrip("/") + "/"


def _write(folder, data):
    path = folder / "P.woodcore"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _refused(path, words):
    try:
        project.Project.load(path)
    except validation.ValidationError as exc:
        assert words in str(exc), exc
        return
    raise AssertionError(f"{path.name} was read, and should have been refused for {words!r}")


def test_a_project_left_to_its_defaults_is_laid_out_as_a_new_one():
    folder = conftest.tmpdir("project_defaults")
    here = project.write(folder / "Neu.woodcore", "Neu")
    assert here.name == "Neu"
    assert here.report_typ == (folder / "Statischer Bericht (typst)" / "Statischer Rapport.typ").resolve()
    assert here.typst_root == (folder / "Statischer Bericht (typst)").resolve()
    # beside its .typ, in the report's own folder, since v0.87 -- the engineer: «le pdf doit être créé au root et pas un dossier au-dessus»
    assert here.report_pdf == (folder / "Statischer Bericht (typst)" / "Statischer Rapport.pdf").resolve()
    assert here.report_pdf == here.report_typ.with_suffix(".pdf") and here.report_pdf.parent == here.typst_root
    assert here.connectors_dir == (folder / "Woodcore-Datei" / "connectors").resolve()
    assert here.details_dir == (folder / "Woodcore-Datei" / "details").resolve()
    assert here.data_dir == (folder / "Statischer Bericht (typst)" / "_woodcore" / "data").resolve()
    assert here.archives_dir == (folder / "_Archiv").resolve()
    assert here.positions_book == folder.resolve() / "Positionen.xlsx"
    # and the file says only what it has to: a layout left to its defaults is not written out
    assert "layout" not in json.loads((folder / "Neu.woodcore").read_text(encoding="utf-8"))
    assert project.Project.load(folder / "Neu.woodcore").layout == project.DEFAULT_LAYOUT


def test_a_project_that_states_where_its_pdf_goes_keeps_it():
    """The default moved in v0.87, from the top of the project folder into the report's folder; a project whose .woodcore names its `layout.pdf` -- one written before, or a folder converted where it stands -- is written where it says, whatever the default is."""
    folder = conftest.tmpdir("project_pdf_stated")
    here = project.write(folder / "Alt.woodcore", "Alt", {"pdf": "Statischer Rapport.pdf"})
    assert here.report_pdf == (folder / "Statischer Rapport.pdf").resolve()
    assert here.report_typ == (folder / "Statischer Bericht (typst)" / "Statischer Rapport.typ").resolve(), "the keys it does not state keep the default"
    assert project.Project.load(folder / "Alt.woodcore").report_pdf == here.report_pdf


def test_the_project_beside_the_checkout_is_laid_out_as_a_new_one():
    """The project beside the code since the move of v0.82 -- Musterprojekt/, next to Woodcore/ -- is laid out as a new project is. Laid out as one report, it states no layout: its .woodcore says its name and its people and nothing else. Migrated into three documents (the three document modes), it states its layout in full, as a new project does since. Until v0.82 it named the folders as they stood before, the code sitting inside it.

    Both shapes are held, the engineer's project being migrated on his word and not by this suite: the one it has when the suite runs is the one checked."""
    if project.checkout_project() is None:
        raise conftest.Skip("no project beside this checkout")
    here = project.Project.load(project.checkout_project())
    if here.has_modes:
        # a key retired in 0.117 (project.RETIRED_KEYS) may still be stated by a project migrated before: read, ignored and said
        stated = set(here.data["layout"]) - {key for section, key in project.RETIRED_KEYS if section == "layout"}
        assert stated == set(project.LAYOUT_KEYS), sorted(set(project.LAYOUT_KEYS) ^ stated)
        assert here.typst_root == here.root and here.modes == project.MODES
        for mode in project.MODES:
            assert here.document_typ(mode).is_file(), mode
    else:
        assert here.layout == project.DEFAULT_LAYOUT
    assert here.root.parent == ROOT.parent, "the project beside the checkout is a folder next to the code's, not around it"
    import positions_store
    assert here.report_typ.is_file() and (positions_store.path(here).is_file() or here.positions_book.is_file()), "its positions: Woodcore's own since v0.114, or the workbook a migration will take them from"


def test_a_path_that_leaves_the_project_is_refused():
    folder = conftest.tmpdir("project_outside")
    base = {"schema_version": "1.0", "format": "woodcore-project", "name": "P"}
    _refused(_write(folder, {**base, "layout": {"sources": "../elsewhere"}}), "leaves the project's folder")
    _refused(_write(folder, {**base, "layout": {"archives": ELSEWHERE + "Archiv"}}), "leaves the project's folder")
    # the export must lie where the report can read it: inside the report's folder
    _refused(_write(folder, {**base, "layout": {"generated": "Export"}}), "must lie inside the report's folder")


def test_a_file_that_is_not_a_project_is_refused_by_name():
    folder = conftest.tmpdir("project_refused")
    _refused(_write(folder, {"schema_version": "1.0", "format": "something-else", "name": "P"}), "woodcore-project")
    _refused(_write(folder, {"schema_version": "0.9", "format": "woodcore-project", "name": "P"}), "expected one of '1.0', '1.1'")
    _refused(_write(folder, {"schema_version": "1.0", "format": "woodcore-project"}), "missing required field 'name'")
    (folder / "Broken.woodcore").write_text("{ not json", encoding="utf-8")
    _refused(folder / "Broken.woodcore", "cannot be read as a project file")
    _refused(folder / "Missing.woodcore", "no such project file")


def test_the_argument_is_taken_out_of_the_command_line():
    assert project.take_argument(["--project", "a.woodcore", "-v"]) == ("a.woodcore", ["-v"])
    assert project.take_argument(["--project=b.woodcore"]) == ("b.woodcore", [])
    assert project.take_argument(["-v"]) == (None, ["-v"])
    try:
        project.take_argument(["--project"])
    except project.ProjectError:
        pass
    else:
        raise AssertionError("--project with no file after it was taken for nothing")


def test_using_puts_the_project_back():
    before = project.current()
    folder = conftest.tmpdir("project_using")
    other = project.write(folder / "Other.woodcore", "Other")
    with project.using(other):
        assert project.current() is other
    assert project.current() is before


def test_a_process_names_its_project_or_finds_the_one_beside_the_checkout():
    """`WOODCORE_PROJECT` names one; without it the one .woodcore at the top of the checkout is taken, which is what keeps `python calc/export_all.py` working with no argument."""
    folder = conftest.tmpdir("project_env")
    project.write(folder / "Env.woodcore", "Env")
    probe = "import project; print(project.current().name)"
    env = dict(os.environ, WOODCORE_PROJECT=str(folder / "Env.woodcore"))
    named = subprocess.run([sys.executable, "-c", probe], cwd=CALC, env=env, capture_output=True, text=True)
    assert named.stdout.strip() == "Env", named.stderr
    env.pop("WOODCORE_PROJECT")
    if project.checkout_project() is None:
        return   # nothing beside this checkout: a process naming no project is refused, which test_project's first checks hold
    beside = subprocess.run([sys.executable, "-c", probe], cwd=CALC, env=env, capture_output=True, text=True)
    assert beside.stdout.strip() == project.checkout_project().stem, beside.stderr


def test_the_export_reads_the_project_it_is_given():
    """Pointed at a copy whose positions cannot be read, the export reads the copy's positions.json and stops naming it -- not the one beside the code. (A copy with no workbook stopped on its Positionen.xlsx until v0.114; a project with no position is no error since.)"""
    import positions_store
    copied = conftest.project_copy("project_export", data=False)
    positions_store.path(copied).write_text("{ not json", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(project.EXPORT_SCRIPT), "--project", str(copied.file)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8"),
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert result.stderr.startswith("export failed: ") and positions_store.FILE in result.stderr, result.stderr
    assert str(copied.root) in result.stderr, result.stderr
    assert not copied.data_dir.exists(), "a failed export wrote into the copy's data/"


# Module-level names the modules of calc/ used for a project path until v0.80. One of them assigned at the top of a module is a path fixed at import from the code's own location -- the tie v0.81 undid.
RETIRED = ("PROJECT_ROOT", "DATA_DIR", "DATA_FILE", "INPUT_XLSX", "CONNECTIONS_DIR", "CONNECTORS_DIR", "PLANS_DIR",
           "STATICS_DIR", "DETAILS_DIR", "SCHEMAS_DIR", "MAIN_TYP", "REPORT_PDF", "TYPST_ROOT", "ARCHIVE_DIR",
           "POSITIONS_BOOK", "PREVIEW_DIR", "PREVIEW_TYP", "IMPORT_PREFIX")
ASSIGNED = re.compile(r"^(%s)\s*=" % "|".join(RETIRED), re.M)
# a one-off conversion that ran once in v0.74 and is kept for the record: it names folders of the layout it converted
EXEMPT = set()


def fixed_paths(text):
    """The retired names `text` assigns at the top level."""
    return ASSIGNED.findall(text)


def test_no_module_fixes_a_project_path_at_import():
    offenders = []
    for path in sorted(CALC.rglob("*.py")):
        if path.name in EXEMPT:
            continue
        found = fixed_paths(path.read_text(encoding="utf-8"))
        offenders += [f"{path.relative_to(CALC).as_posix()}: {name}" for name in found]
    assert not offenders, "a project path fixed at import, where project.current() should be asked:\n  " + "\n  ".join(offenders)


def test_the_guard_catches_a_planted_one():
    assert fixed_paths('ROOT = Path(__file__).parent\nDATA_DIR = ROOT / "data"\n') == ["DATA_DIR"]
    assert fixed_paths('    DATA_DIR = here.data_dir\n') == []  # inside a function it is a local, asked for at the call


# --- the engine copied into a project, and what produced an export (v0.82) ------------

def _stamp(here, version, **files):
    """Rewrites the copy's VERSION as another version, or another build, would have written it: `files` a {name: content} of the copy to put in place, recorded as written."""
    import hashlib
    stamp_file = here.generated_dir / project.ENGINE_STAMP
    stamp = json.loads(stamp_file.read_text(encoding="utf-8"))
    for name, content in files.items():
        path = here.generated_dir / name
        os.chmod(path, 0o666)
        path.write_text(content, encoding="utf-8")
        stamp["files"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
    stamp["version"] = version
    stamp_file.write_text(json.dumps(stamp), encoding="utf-8")


def test_the_engine_copy_is_replaced_only_when_it_may_be():
    """Absent or another build of this version: replaced. Another version's, or edited by hand: only when told to. A newer program's: never (calc/project.py sync_engine)."""
    folder = conftest.tmpdir("engine_states")
    here = project.write(folder / "E.woodcore", "E")
    assert project.engine_state(here)[0] == "absent"
    assert "lib/calc-engine.typ" in project.sync_engine(here)
    assert project.engine_state(here)[0] == "current"
    copy = here.generated_dir / "lib" / "formula.typ"
    assert not copy.stat().st_mode & 0o222, "the engine copied into a project is left read-only"  # the mode, not os.access, which says yes to root

    _stamp(here, project.VERSION, **{"lib/formula.typ": "// another build\n"})
    assert project.engine_state(here)[0] == "stale"
    assert project.sync_engine(here) == ["lib/formula.typ", project.ENGINE_STAMP]

    _stamp(here, "0.70.0", **{"lib/formula.typ": "// an older version\n"})
    assert project.engine_state(here) == ("older", "0.70.0")
    try:
        project.sync_engine(here)
    except project.EngineDecision as exc:
        assert exc.state == "older" and "--update-engine" in str(exc), exc
    else:
        raise AssertionError("an engine another version wrote was replaced without being asked")
    project.sync_engine(here, update=True)
    assert project.engine_state(here)[0] == "current"

    os.chmod(copy, 0o666)
    copy.write_text(copy.read_text(encoding="utf-8") + "// edited by hand\n", encoding="utf-8")
    assert project.engine_state(here) == ("edited", "lib/formula.typ")
    assert "-// edited by hand" in project.engine_diff(here)
    try:
        project.sync_engine(here)
    except project.EngineDecision as exc:
        assert exc.state == "edited", exc
    else:
        raise AssertionError("an engine edited by hand was overwritten without being asked")
    project.sync_engine(here, update=True)
    assert "edited by hand" not in copy.read_text(encoding="utf-8")

    _stamp(here, "9.0.0")
    assert project.engine_state(here) == ("newer", "9.0.0")
    for update in (False, True):
        try:
            project.sync_engine(here, update=update)
        except project.EngineDecision as exc:
            assert exc.state == "newer", exc
        else:
            raise AssertionError("a newer program's engine was replaced by an older one")


def test_the_command_line_refuses_to_overwrite_an_edited_engine():
    folder = conftest.tmpdir("engine_cli")
    here = project.write(folder / "E.woodcore", "E")
    project.sync_engine(here)
    copy = here.generated_dir / "lib" / "i18n.typ"
    os.chmod(copy, 0o666)
    copy.write_text("// mine\n", encoding="utf-8")
    run = subprocess.run([sys.executable, str(CALC / "cli.py"), "sync-engine", "--project", str(here.file)],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert run.returncode == 1 and "edited by hand" in run.stderr, run.stdout + run.stderr
    run = subprocess.run([sys.executable, str(CALC / "cli.py"), "sync-engine", "--update", "--project", str(here.file)],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert run.returncode == 0 and "lib/i18n.typ" in run.stdout, run.stdout + run.stderr


def test_the_record_of_an_export_names_what_produced_it_and_carries_no_date():
    folder = conftest.tmpdir("record")
    here = project.write(folder / "R.woodcore", "Halle", company="Musterbüro", author="Max Muster")
    here.positions_book.write_bytes(b"not really a workbook")
    first, second = project.record(here), project.record(here)
    assert first == second, "two records of the same inputs differ"
    validation.validate_structure(first, "project")
    assert (first["name"], first["company"], first["author"], first["number"]) == ("Halle", "Musterbüro", "Max Muster", "")
    assert first["woodcore"]["version"] == project.VERSION
    assert list(first["workbooks"]) == ["Positionen.xlsx"] and len(first["workbooks"]["Positionen.xlsx"]) == 64


def test_the_project_beside_the_checkout_is_found_in_a_neighbouring_folder():
    """`Musterprojekt/Musterprojekt.woodcore` beside `Woodcore/` (v0.82), and nothing where two would be a choice nobody made."""
    root = conftest.tmpdir("beside")
    (root / "Woodcore" / "calc").mkdir(parents=True)
    saved = project.APP_ROOT
    project.APP_ROOT = root / "Woodcore"
    try:
        assert project.checkout_project() is None
        (root / "Musterprojekt").mkdir()
        (root / "Musterprojekt" / "Musterprojekt.woodcore").write_text("{}", encoding="utf-8")
        assert project.checkout_project() == root / "Musterprojekt" / "Musterprojekt.woodcore"
        (root / "Other").mkdir()
        (root / "Other" / "Other.woodcore").write_text("{}", encoding="utf-8")
        assert project.checkout_project() is None
    finally:
        project.APP_ROOT = saved


def test_a_retired_key_is_read_ignored_said_and_kept():
    """A key of a feature Woodcore no longer has (project.RETIRED_KEYS: the RFEM import's `gui.rfem_models` and `layout.rfem_export`, retired in 0.117) is valid, read without effect, and said -- one note each, naming the key -- at every export; and Woodcore never takes it out of the file when it writes the `gui` key it shares: the file is the engineer's, and the key goes when he removes it."""
    folder = conftest.tmpdir("retired-keys")
    layout = dict(documents.layout_for("de"), rfem_export="RFEM-Export")
    here = project.Project.load(_write(folder, {"schema_version": "1.1", "format": "woodcore-project", "name": "P",
                                                "gui": {"rfem_models": ["RFEM-Export/gone.xlsx"]}, "layout": layout}))
    assert here.has_modes, "a project stating a retired key with the six of the three documents is laid out in three documents"
    notes = here.retired_keys()
    assert sorted(note.args["key"] for note in notes) == ["gui.rfem_models", "layout.rfem_export"], notes
    assert all(note.code == "retired_key" and "0.117" in note and "is ignored" in note for note in notes), notes
    here = project.set_empty_folders(here, "tab_polar", ["Leer"])
    stored = json.loads(here.file.read_text(encoding="utf-8"))
    assert stored[project.GUI_KEY] == {"rfem_models": ["RFEM-Export/gone.xlsx"], "empty_folders": {"tab_polar": ["Leer"]}}, stored
    assert stored["layout"]["rfem_export"] == "RFEM-Export"
    # a project that states none says nothing
    plain = project.Project.load(_write(conftest.tmpdir("retired-none"), {"schema_version": "1.0", "format": "woodcore-project", "name": "Q"}))
    assert plain.retired_keys() == []


# --- a project laid out in three documents (the engineer's request of 30.09.2026) ------------

def test_the_default_layout_is_what_it_has_always_been():
    """DEFAULT_LAYOUT is load-bearing: the engineer's own Musterprojekt and tests/projet-exemple state no layout and read every one of their paths from it, so a project in three documents is told apart by what its file states (`layout.typst_root`) and never by a default that moved. Pinned as a literal, its order included, rather than read back from the constant it guards."""
    assert list(project.DEFAULT_LAYOUT.items()) == [
        ("report", "Statischer Bericht (typst)/Statischer Rapport.typ"),
        ("pdf", "Statischer Bericht (typst)/Statischer Rapport.pdf"),
        ("sources", "Woodcore-Datei"),
        ("generated", "Statischer Bericht (typst)/_woodcore"),
        ("archives", "_Archiv"),
    ]
    assert project.LAYOUT_KEYS == tuple(project.DEFAULT_LAYOUT) + project.MODE_KEYS + project.FOLDER_KEYS
    assert not set(project.MODE_KEYS) & set(project.DEFAULT_LAYOUT), "a key of the three documents has a default, so every project would read as one in three documents"
    assert set(project.LAYOUT_ORDER) == set(project.LAYOUT_KEYS) and len(project.LAYOUT_ORDER) == len(project.LAYOUT_KEYS)


def test_a_report_alone_is_one_document_whose_paths_are_what_they_were():
    """A project whose file states no `typst_root` -- every project written before the three documents -- has the report and nothing else, and every path it had: the Typst root the report's folder, the config.typ, the pictures and the export inside it."""
    folder = conftest.tmpdir("modes_report_alone")
    here = project.write(folder / "Alt.woodcore", "Alt")
    report = (folder / "Statischer Bericht (typst)").resolve()
    assert not here.has_modes and here.modes == ("rs",)
    assert here.typst_root == report == here.report_typ.parent
    assert (here.document_typ("rs"), here.document_pdf("rs"), here.document_dir("rs")) == (here.report_typ, here.report_pdf, report)
    assert here.journal_file_for("rs") == here.journal_file == here.sources_dir / "journal.json"
    assert here.structure_file("rs") is None, "the report keeps its order in its #include lines"
    assert (here.config_typ, here.commands_typ, here.references_bib) == (report / "config.typ", report / "commands.typ", report / "references.bib")
    assert here.images_dir == report / "Images"
    assert here.stamps_dir == here.generated_dir / "stamps"
    for ask in (here.document_typ, here.document_pdf, here.document_dir, here.journal_file_for, here.structure_file):
        for mode in ("cu", "bp"):
            try:
                ask(mode)
            except project.ProjectError as exc:
                assert "laid out as one report" in str(exc) and "migrate" in str(exc), exc
            else:
                raise AssertionError(f"{ask.__name__}({mode!r}) answered for a project laid out as one report")
    try:
        here.document_typ("nv")
    except project.ProjectError as exc:
        assert "cu, bp, rs" in str(exc), exc
    else:
        raise AssertionError("a document that is none of the three was answered for")


def test_a_project_in_three_documents_says_where_each_lies():
    """Its own folder is the Typst root and holds what the three share; each document lies in a folder of its own, its PDF beside its entry file, its journal in the sources -- and the report keeps `report` and `pdf`, so `report_typ` still means the report."""
    folder = conftest.tmpdir("modes_where")
    layout = dict(documents.layout_for("de"), generated="_woodcore", sources="Woodcore-Datei", archives="_Archiv")
    layout.pop("config")
    layout.update({key: value.replace("100-Service criteria agreement", "1_Nutzungsvereinbarung").replace("200-Basis of design", "2_Projektbasis").replace("300-Statical report", "3_Statischer Bericht")
                   for key, value in layout.items() if key in project.ENTRY_KEYS.values() or key in project.PDF_KEYS.values()})
    here = project.write(folder / "Halle.woodcore", "Halle", layout)
    root = folder.resolve()
    assert here.has_modes and here.modes == ("cu", "bp", "rs") and not here.has_folders, "laid out as every project in three documents was before 0.119"
    assert here.typst_root == root
    for mode, folder_name, entry in (("cu", "1_Nutzungsvereinbarung", "Nutzungsvereinbarung"),
                                     ("bp", "2_Projektbasis", "Projektbasis"),
                                     ("rs", "3_Statischer Bericht", "Statischer Rapport")):
        assert here.document_dir(mode) == root / folder_name
        assert here.document_typ(mode) == root / folder_name / f"{entry}.typ"
        assert here.document_pdf(mode) == root / folder_name / f"{entry}.pdf"
    assert (here.report_typ, here.report_pdf) == (here.document_typ("rs"), here.document_pdf("rs"))
    assert here.structure_file("cu") == root / "1_Nutzungsvereinbarung" / "structure.json"
    assert here.structure_file("bp") == root / "2_Projektbasis" / "structure.json"
    assert here.structure_file("rs") is None
    assert [here.journal_file_for(mode).name for mode in here.modes] == ["journal-cu.json", "journal-bp.json", "journal.json"]
    assert here.journal_file_for("rs") == here.journal_file
    assert (here.config_typ, here.commands_typ, here.references_bib) == (root / "config.typ", root / "commands.typ", root / "references.bib")
    assert here.images_dir == root / "Images"
    assert here.generated_dir == root / "_woodcore" and here.data_dir == root / "_woodcore" / "data"
    assert here.stamps_dir == root / "_woodcore" / "stamps"
    assert (here.sources_dir, here.archives_dir) == (root / "Woodcore-Datei", root / "_Archiv")
    again = project.Project.load(here.file)
    assert again.layout == here.layout and again.has_modes


def test_a_project_in_three_documents_states_its_layout_in_full():
    """The engineer's rule: a new or migrated project states its layout, DEFAULT_LAYOUT being the projects' that state none. So a layout in three documents is written with every key, `sources` and `archives` included where they are the default -- which `templates.stated_layout` would have dropped -- in LAYOUT_ORDER, by `write` and by `update` alike; a layout of a report alone is still written as it is given."""
    folder = conftest.tmpdir("modes_full")
    layout = dict(documents.layout_for("fr"), sources=project.DEFAULT_LAYOUT["sources"], archives=project.DEFAULT_LAYOUT["archives"])
    stated = {key: value for key, value in layout.items() if project.DEFAULT_LAYOUT.get(key) != value}
    assert "sources" not in stated and "archives" not in stated
    here = project.write(folder / "F.woodcore", "F", stated)
    written = json.loads(here.file.read_text(encoding="utf-8"))["layout"]
    assert list(written) == list(project.LAYOUT_ORDER) and written == layout, written
    project.update(here.file, layout=stated)
    rewritten = json.loads(here.file.read_text(encoding="utf-8"))["layout"]
    assert list(rewritten) == list(project.LAYOUT_ORDER) and rewritten == layout, rewritten
    alone = project.write(folder / "A.woodcore", "A", {"pdf": "Statischer Rapport.pdf"})
    assert json.loads(alone.file.read_text(encoding="utf-8"))["layout"] == {"pdf": "Statischer Rapport.pdf"}


def test_a_layout_in_three_documents_states_all_six_keys_or_none():
    """None of the six has a default, so a file stating some and not the others is neither of the two layouts: refused, naming what it lacks, rather than read as whichever half happens to fit."""
    folder = conftest.tmpdir("modes_partial")
    base = {"schema_version": "1.1", "format": "woodcore-project", "name": "P"}
    full = documents.layout_for("de")
    for key in project.MODE_KEYS:
        _refused(_write(folder, {**base, "layout": {k: v for k, v in full.items() if k != key}}), f"and not layout.{key}")
    _refused(_write(folder, {**base, "layout": {"images": "Images"}}), "not layout.typst_root, layout.report_cu")


def test_three_documents_compile_from_the_project_s_own_folder_each_from_a_folder_of_its_own():
    folder = conftest.tmpdir("modes_rules")
    base = {"schema_version": "1.1", "format": "woodcore-project", "name": "P"}
    full = documents.layout_for("de")
    _refused(_write(folder, {**base, "layout": {**full, "typst_root": "3_Statischer Bericht"}}), 'must be "."')
    _refused(_write(folder, {**base, "layout": {**full, "typst_root": ".."}}), "leaves the project's folder")
    assert project.Project.load(_write(folder, {**base, "layout": {**full, "typst_root": "./"}})).typst_root == folder.resolve()
    _refused(_write(folder, {**base, "layout": {**full, "report_cu": "Nutzungsvereinbarung.typ"}}), "lies at the top of the project")
    _refused(_write(folder, {**base, "layout": {**full, "report_bp": "100-Service criteria agreement/Projektbasis.typ"}}), "are in one folder")
    if os.name == "nt":  # one folder, as Windows compares names; on Linux two
        _refused(_write(folder, {**base, "layout": {**full, "report_bp": "100-SERVICE CRITERIA AGREEMENT/Projektbasis.typ"}}), "are in one folder")
    _refused(_write(folder, {**base, "layout": {**full, "images": "../Bilder"}}), "leaves the project's folder")
    _refused(_write(folder, {**base, "layout": {**full, "pdf_cu": ELSEWHERE + "Ablage/NV.pdf"}}), "leaves the project's folder")
    # the export at the top of the project, where a report alone refuses it: the rule of the report's folder is a report alone's
    assert project.Project.load(_write(folder, {**base, "layout": full})).generated_dir == folder.resolve() / "000-Woodcore"


def test_the_schema_documents_every_layout_key():
    """Every key calc/project.py reads is described where a reader of the .woodcore looks for it, and none of the six is required -- a file written before the three documents must go on validating. A key retired in 0.117 (project.RETIRED_KEYS) stays described, as retired, so that a file written before goes on validating too."""
    schema = validation.load_schema("woodcore-project")
    layout = schema["properties"]["layout"]
    described = set(project.LAYOUT_KEYS) | {key for section, key in project.RETIRED_KEYS if section == "layout"}
    assert set(layout["properties"]) == described, sorted(set(layout["properties"]) ^ described)
    assert "required" not in layout
    assert all(entry.get("type") == "string" and entry.get("description") for entry in layout["properties"].values())


def test_a_project_laid_out_by_folders_says_where_each_part_lies():
    """Issue #64 (spec 2026-10-15-structure-projet-dossiers): what configures the documents in 000-Typst-Config/, what is Woodcore's in 000-Woodcore/ -- the export, the engine, the sources and the archives --, the three documents in 100-, 200-, 300-, the engineer's domains in Domains/, the positions in Positions/, one folder per kind of domain, the same names in every language."""
    folder = conftest.tmpdir("folders_where")
    here = project.write(folder / "Halle.woodcore", "Halle", documents.layout_for("fr"))
    root = folder.resolve()
    assert here.has_modes and here.has_folders
    assert json.loads(here.file.read_text(encoding="utf-8"))["schema_version"] == "1.1"
    config = root / "000-Typst-Config"
    assert here.config_dir == config
    assert (here.config_typ, here.commands_typ, here.title_typ, here.references_bib, here.template_dir) == (
        config / "config.typ", config / "commands.typ", config / "title.typ", config / "references.bib", config / "Template")
    assert here.from_root(here.commands_typ) == "/000-Typst-Config/commands.typ"
    woodcore = root / "000-Woodcore"
    assert (here.generated_dir, here.data_dir, here.stamps_dir) == (woodcore, woodcore / "data", woodcore / "stamps")
    assert (here.sources_dir, here.archives_dir) == (woodcore / "sources", woodcore / "archives")
    assert here.generated_excludes() == [woodcore / "sources", woodcore / "archives"]
    assert [here.document_dir(mode).name for mode in project.MODES] == ["100-Service criteria agreement", "200-Basis of design", "300-Statical report"]
    assert here.formulas_dir == root / "Domains" and here.positions_dir == root / "Positions"
    assert here.domain_dir("snow-load") == root / "Variable-loads" / "Snow"
    assert here.domain_dir("dead-load") == root / "Permanent-loads"
    assert here.domain_dir("check", "tension") == here.unfolded_dir("tension") == root / "Timber-checks" / "Tension"
    assert here.domain_dir("steel", "splice") == root / "Steel-checks" / "Splice"
    assert here.drawing_dir("plan") == root / "Plans" / "Position-plan"
    try:
        here.domain_dir("check", "flying")
    except project.ProjectError as exc:
        assert "unknown check kind" in str(exc), exc
    else:
        raise AssertionError("a kind of check that is none was given a folder")
    # every folder made, a second call makes none
    made = here.ensure_folders()
    assert made and all(path.is_dir() for path in here.structure_folders())
    assert (root / "Plans" / "Position-plan" / "Imported Plans").is_dir() and (root / "Plans" / "Fire-plan" / "Exports" / "Figures").is_dir()
    assert (root / "Appendix" / "Exports").is_dir() and (root / "Scripts").is_dir()
    assert not (root / "Variable-loads" / "Earthquake").exists(), "a folder for a tab that does not exist yet (D-23)"
    assert here.ensure_folders() == []


def test_a_project_laid_out_before_has_none_of_the_new_folders():
    """Read and compiled as it always was until it is migrated: its configuration at the top of the Typst root, `Formules/`, positions.json in its sources, and no folder of a kind of domain."""
    folder = conftest.tmpdir("folders_before")
    alone = project.write(folder / "A.woodcore", "A")
    assert not alone.has_folders and alone.config_dir == alone.typst_root and alone.formulas_dir == alone.typst_root / "Formules"
    assert alone.domain_dir("snow-load") is None and alone.drawing_dir("plan") is None
    assert alone.unfolded_dir("tension") == alone.formulas_dir and alone.positions_dir == alone.sources_dir
    assert alone.structure_folders() == [] and alone.generated_excludes() == []
    assert json.loads(alone.file.read_text(encoding="utf-8"))["schema_version"] == "1.0", "a project laid out before is not made unreadable to an older Woodcore"


def test_the_configuration_folder_is_stated_with_schema_1_1_and_three_documents():
    """`layout.config` and schema_version 1.1 go together (D-20): a 1.1 file without it, or a 1.0 file with it, is neither layout; and the folder is one folder at the top of the project, apart from the documents'."""
    folder = conftest.tmpdir("folders_rules")
    full = documents.layout_for("de")
    v11 = {"schema_version": "1.1", "format": "woodcore-project", "name": "P"}
    v10 = {**v11, "schema_version": "1.0"}
    plain = {key: value for key, value in full.items() if key != "config"}
    _refused(_write(folder, {**v11, "layout": plain}), "states schema_version 1.1 and no layout.config")
    _refused(_write(folder, {**v10, "layout": full}), "states schema_version 1.0 and layout.config")
    _refused(_write(folder, {**v11, "layout": {"config": "000-Typst-Config"}}), "without layout.typst_root")
    _refused(_write(folder, {**v11, "layout": {**full, "config": "."}}), "one folder at the top of the project")
    _refused(_write(folder, {**v11, "layout": {**full, "config": "Docs/Config"}}), "one folder at the top of the project")
    _refused(_write(folder, {**v11, "layout": {**full, "config": "100-Service criteria agreement"}}), "are one folder")
    assert project.Project.load(_write(folder, {**v10, "layout": plain})).has_folders is False
    assert project.Project.load(_write(folder, {**v11, "layout": full})).has_folders is True


def test_the_folders_of_the_kinds_of_check_are_the_kinds_of_check():
    """One folder per kind of member check and of steel check (D-21): the two tables of calc/project.py name exactly the kinds domains/member_check.py and domains/steel_check.py know, so a check of a kind added later is not left without a folder."""
    from domains import member_check, steel_check
    assert set(project.CHECK_KIND_FOLDERS) == set(member_check.KINDS)
    assert set(project.STEEL_KIND_FOLDERS) == set(steel_check.KINDS)
    for table in (project.CHECK_KIND_FOLDERS, project.STEEL_KIND_FOLDERS):
        assert len(set(name.casefold() for name in table.values())) == len(table), "two kinds in one folder"


# --- the content templates a project's documents were made from, and the title page reported at once (issues #87, #88) ---

def test_the_content_templates_are_an_additive_key_and_an_older_file_reads_as_unknown():
    import project_template
    root = conftest.tmpdir("content_templates_key")
    here = project_template.create_skeleton(root / "P", "Probe", "de")
    version = here.data["schema_version"]
    assert here.content_template("cu") == "" and "content_templates" not in here.data, "an old file -- or a skeleton -- states none"
    here = project.set_content_template(here, "cu", "user:cu/kurz")
    here = project.set_content_template(here, "rs", "builtin:rs/standard")
    again = project.Project.load(here.file)
    assert again.content_template("cu") == "user:cu/kurz" and again.content_template("rs") == "builtin:rs/standard" and again.content_template("bp") == ""
    assert again.data["schema_version"] == version, "the key moved the schema's version"
    try:
        project.set_content_template(here, "xx", "a")
    except project.ProjectError:
        pass
    else:
        raise AssertionError("an unknown document accepted")


def test_the_title_page_is_reported_into_the_export_alone_and_the_last_export_keeps_its_date():
    import json
    import export_all
    import project_template
    root = conftest.tmpdir("refresh_project_info")
    here = project_template.create_skeleton(root / "P", "Probe", "fr", client="Avant")
    info = here.data_dir / "project.json"
    kept = json.loads(info.read_text(encoding="utf-8"))
    kept["woodcore"] = {"version": "0.1.0", "revision": "abc"}   # what an older export wrote: kept, nothing being exported now
    kept["workbooks"] = {"Belastungsannahmen.xlsm": "0" * 64}
    info.write_text(json.dumps(kept), encoding="utf-8")
    when, _engine = project.last_export(here)
    here = project.update(here.file, client="Après", number="P-42")
    assert export_all.refresh_project_info(here) is True
    now = json.loads(info.read_text(encoding="utf-8"))
    assert now["client"] == "Après" and now["number"] == "P-42" and now["name"] == "Probe"
    assert now["woodcore"] == {"version": "0.1.0", "revision": "abc"} and now["workbooks"] == kept["workbooks"]
    assert export_all.refresh_project_info(here) is False, "rewritten with nothing changed"
    assert project.last_export(here)[0] == when, "the title page's report moved the date of the last export"
    info.write_text("{ not json", encoding="utf-8")
    assert export_all.refresh_project_info(here) is True and json.loads(info.read_text(encoding="utf-8"))["client"] == "Après"


def test_the_documents_made_are_the_ones_whose_entry_is_there():
    here = conftest.project_copy("created_modes")
    made = tuple(mode for mode in here.modes if here.document_typ(mode).is_file())
    assert here.created_modes == made
    assert all(here.is_created(mode) == (mode in made) for mode in project.MODES)
