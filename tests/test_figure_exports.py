"""The export's figures in the tabs' folders, their one copy (issue #64, spec 2026-10-15-structure-projet-dossiers lot 2: REQ-007, REQ-008, REQ-009, ARCH-003).

A project laid out by folders has the figures the export draws -- plans, fire plans, static models, schemas, connections, connectors, a dead load's build-up -- in its tab's `Exports/Figures/`, and the annexes' excerpts in `Appendix/Exports/`; data/ keeps the JSON alone, which names each figure from the Typst root. One writer puts them there (calc/engine.py `write_managed`, `Figures`) and removes only what the last export listed -- the folder is one the engineer sees, and a file of his in it is his --, and one function of the engine reads them back (lib/calc-engine.typ `figure-path`), the names under data/ of every export before still read. The documents a plan is drawn on are copied into `Imported Plans/` and the annexes' PDFs into `Appendix/` (the documents' own tests: test_plan_documents, test_annex).
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import conftest
from conftest import CALC, ROOT

import engine
import project
import stamps
import validation


def _example(name):
    """A copy of the committed example, laid out by folders, with what a compile or a sync writes left out."""
    top = conftest.SAMPLE.parent.resolve()

    def ignore(directory, names):
        here = Path(directory).resolve()
        if here == top:
            return {n for n in names if n.startswith(".woodcore-") or n.endswith(".lock")}
        if here.parent == top and here.name == project.WOODCORE_FOLDER:
            return {n for n in names if n in ("lib", "calc", "VERSION", "stamps", "archives", "out", ".preview", "docs")}
        return set()
    dest = conftest.tmpdir(name) / "Exemple"
    shutil.copytree(top, dest, ignore=ignore)
    return project.Project.load(dest / conftest.SAMPLE.name)


def _export(here):
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    env.pop(project.ENV, None)
    run = subprocess.run([sys.executable, str(CALC / "export_all.py"), "--project", str(here.file)],
                         capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(ROOT), env=env)
    assert run.returncode == 0, run.stdout + run.stderr
    return run.stdout


def _tree(here):
    """{path from the project: bytes} of data/ and of every folder the export writes figures into."""
    out = {}
    for folder in [here.data_dir] + [here.exports_dir(kind) for kind in project.FIGURE_KINDS]:
        for path in sorted(folder.rglob("*")) if folder.is_dir() else ():
            if path.is_file():
                out[path.relative_to(here.root).as_posix()] = path.read_bytes()
    return out


# --- the one writer ------------------------------------------------------------------------

def test_the_managed_writer_removes_only_what_the_last_export_listed():
    base = conftest.tmpdir("fx_managed") / "Figures"
    base.mkdir(parents=True)
    (base / "mine.svg").write_text("<svg>the engineer's</svg>", encoding="utf-8")
    (base / "old.svg").write_text("<svg>an export's</svg>", encoding="utf-8")
    written = engine.write_managed(base, {"P01.svg": "<svg>\r\none</svg>\r\n", "P01-plan.pdf": b"%PDF-1.7\r\n"}, previous=["old.svg", "gone.svg"])
    assert sorted(written) == ["P01-plan.pdf", "P01.svg"]
    assert (base / "mine.svg").is_file(), "a file the last export did not list is the engineer's, and stays"
    assert not (base / "old.svg").exists(), "a figure the last export wrote and this one does not is removed"
    assert (base / "P01.svg").read_bytes() == b"<svg>\none</svg>\n", "text is written LF, whatever the platform"
    assert (base / "P01-plan.pdf").read_bytes() == b"%PDF-1.7\r\n", "bytes are written as they are"
    assert engine.write_managed(base, {"P01.svg": "<svg>\none</svg>\n"}, previous=["P01.svg", "P01-plan.pdf"]) == [], "an unchanged file is not written again"
    assert not (base / "P01-plan.pdf").exists() and not list(base.glob("*.part"))
    for bad in ({"../outside.svg": "x"}, {}):
        try:
            engine.write_managed(base, bad, previous=["../../outside.svg"] if not bad else [])
        except ValueError:
            continue
        raise AssertionError(f"a path leaving the folder was accepted: {bad or 'previous'}")


def test_a_figure_is_named_from_the_typst_root_laid_out_by_folders_and_under_data_before():
    here = conftest.PROJECT
    assert here.has_folders
    place = engine.Figures(here.data_dir, "plan", here)
    name = place.name("P01.svg")
    assert name == "/Plans/Position-plan/Exports/Figures/P01.svg", name
    assert place.path(name) == here.typst_root / "Plans" / "Position-plan" / "Exports" / "Figures" / "P01.svg"
    assert place.path("plans/P01.svg") == here.data_dir / "plans" / "P01.svg", "a name an older export wrote is found where it was"
    assert place.listed({"a": [name, "/Statics/Exports/Figures/M-de.svg", "plans/P02.svg", "P01.json"]}) == ["P01.svg"], "only this kind's figures in its own folder"
    before = engine.Figures(here.data_dir, "plan")
    assert before.name("P01.svg") == "plans/P01.svg" and before.folder == here.data_dir / "plans"
    assert engine.figures(here.data_dir, "connector").here is not None, "the project is found from its data/"
    assert engine.figures(conftest.tmpdir("fx_nobody") / "data", "connector").here is None
    for kind, file in (("plan", "P01.svg"), ("statics", "M-de.svg"), ("connection", "V-fr.svg")):
        old, new = validation.figure_names(kind, file)
        assert new == engine.Figures(here.data_dir, kind, here).name(file) and old == engine.Figures(here.data_dir, kind).name(file)
    assert engine.Figures(here.data_dir, "annex", here).name("E01.pdf") == "/Appendix/Exports/E01.pdf"


def test_every_folder_of_figures_is_made_with_the_project():
    folders = {path.relative_to(conftest.PROJECT.typst_root).as_posix() for path in conftest.PROJECT.structure_folders()}
    for kind in project.FIGURE_KINDS:
        assert project.figures_folder(kind) in folders, kind
    # the wind's figure of its table of Annexe C, cut out of the norm, beside its case's file (spec 2026-10-23-onglet-vent-briques, REQ-017)
    assert "wind-load" in project.LOAD_FIGURE_KINDS and project.figures_folder("wind-load").endswith("Variable-loads/Wind/Exports/Figures"), project.figures_folder("wind-load")


# --- the export ------------------------------------------------------------------------------

def test_the_export_writes_its_figures_into_the_tabs_exports_and_keeps_the_engineer_s_file():
    """REQ-008 and D-17: no figure under data/, each in its tab's Exports/Figures/, named so in the JSON; a file the engineer put there survives two exports; a figure of a model that is gone goes; two exports are byte for byte the same."""
    here = _example("fx_export")
    mine = here.figures_dir("plan") / "Notiz des Ingenieurs.svg"
    mine.parent.mkdir(parents=True, exist_ok=True)
    mine.write_text("<svg/>", encoding="utf-8")
    _export(here)
    left = [p.relative_to(here.data_dir).as_posix() for p in here.data_dir.rglob("*") if p.is_file() and p.suffix.lower() in engine.FIGURE_SUFFIXES]
    assert not left, f"figures left under data/: {left}"
    plans = json.loads((here.data_dir / "plans.json").read_text(encoding="utf-8"))
    assert plans["schema_version"] == "1.6"
    for pid, record in plans["plans"].items():
        assert record["overlay"] == f"/Plans/Position-plan/Exports/Figures/{pid}.svg"
        assert (here.typst_root / record["overlay"][1:]).is_file()
        if "background" in record:
            assert (here.typst_root / record["background"]["file"][1:]).is_file()
    for kind, export in (("statics", "statics.json"), ("details", "schemas.json"), ("connection", "connections.json"), ("connector", "connectors.json"), ("fire", "fire.json"), ("annex", "annexes.json")):
        data = json.loads((here.data_dir / export).read_text(encoding="utf-8"))
        named = engine.Figures(here.data_dir, kind, here).listed(data)
        assert named, f"{export} names no figure in {project.figures_folder(kind)}"
        assert all((here.figures_dir(kind) / rel).is_file() for rel in named), export
    assert mine.is_file(), "the engineer's own file in Exports/Figures/ was removed by the export"
    first = _tree(here)
    _export(here)
    second = _tree(here)
    assert first == second, sorted(k for k in set(first) | set(second) if first.get(k) != second.get(k))[:5]
    # a static model gone takes its figures with it, and nothing else
    gone = sorted(here.statics_dir.glob("*.json"))[0]
    gone.unlink()
    _export(here)
    assert not list(here.figures_dir("statics").glob(f"{gone.stem}-*.svg")) and mine.is_file()


def test_an_export_written_before_names_its_figures_under_data_and_is_read_as_it_was():
    """ARCH-003: the engine resolves a figure in one function, and a name under data/ -- every export before 0.119 -- is read there."""
    engine_text = conftest.engine_source()
    assert '#let figure-path(file) = if file.starts-with("/") { file } else { "../data/" + file }' in engine_text
    reads = []
    for path in sorted((ROOT / "lib").glob("*.typ")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if '"../data/" +' in line and "#let figure-path" not in line and not re.search(r'json\("\.\./data/" \+', line):
                reads.append(f"{path.name}:{number}: {line.strip()}")
    assert not reads, "a figure read from data/ outside figure-path:\n" + "\n".join(reads)
    if not conftest.have_typst():
        raise conftest.Skip("no typst here")
    # a name from the root is read as it stands from any file; a name under data/ is read beside the engine, where every image() of one is called -- what a project migrated with --skip-data compiles with (test_migrate_folders)
    probe = conftest.probe_dir("fx_figure_path")
    rooted = conftest.PROJECT.figures_dir("plan") / "fx-probe.svg"
    rooted.parent.mkdir(parents=True, exist_ok=True)
    rooted.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>', encoding="utf-8")
    try:
        engine_import = conftest.import_path(conftest.PROJECT.generated_dir / "lib" / "calc-engine.typ")
        (probe / "p.typ").write_text(f'#import "{engine_import}": figure-path\n#image(figure-path("{conftest.PROJECT.from_root(rooted)}"))\n#assert.eq(figure-path("plans/P01.svg"), "../data/plans/P01.svg")\n', encoding="utf-8")
        run = subprocess.run([str(project.typst_executable()), "compile", "--root", str(conftest.TYPST_ROOT), str(probe / "p.typ"), str(probe / "p.pdf")],
                             capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert run.returncode == 0, run.stderr
    finally:
        rooted.unlink(missing_ok=True)


def test_the_stamps_and_the_archive_take_in_the_tabs_exports_and_the_appendix():
    here = conftest.PROJECT
    figure = here.figures_dir("statics") / "fx-stamp.svg"
    figure.parent.mkdir(parents=True, exist_ok=True)
    figure.write_text("<svg/>", encoding="utf-8")
    try:
        assert figure in stamps.enumerated(here, "rs"), "a figure of Exports/Figures/ is an input of the documents"
        sys.path.insert(0, str(CALC / "tools"))
        import archive_export
        members = {rel for _path, rel in archive_export.members_of_document(here, "rs")}
        assert here.rel(figure) in members, "the archive of a document carries the figures it printed"
        appendix = [rel for rel in members if rel.startswith(project.APPENDIX_FOLDER + "/")]
        assert appendix, "the annexes' PDFs and their excerpts are archived with the documents"
    finally:
        figure.unlink(missing_ok=True)
