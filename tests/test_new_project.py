"""A new project, and an old folder made into one (calc/project_template.py, v0.83, docs/architecture/layout.md §11, docs/conventions/build-and-release.md §12).

`woodcore-cli new` and the start page's «Nouveau projet» copy `templates/projet/` into an empty folder; «Convertir un ancien dossier» writes a `.woodcore` into a folder laid out before Woodcore and moves nothing. These hold that a new project is laid out in three documents (the engineer's request of 30.09.2026) -- the convention d'utilisation, the base de projet and the report, each in a folder of its own named in the project's language, and what the three share at the top -- that the report it holds prints what a report alone printed, that each of the three compiles before any export and once there is one, that its workbook carries the headers the export reads, that seeding its export fills only what is missing -- the three journals among it --, that the two documents beside the report are made from the engineer's own document templates with their sharing settled (work package 6.2), and that a converted folder is read where it stands, its old engine replaced only once the engineer agrees.
"""

import contextlib
import json
import os
import re
import shutil
import subprocess
import sys
import types

import conftest
from conftest import CALC

import doc_templates
import documents
import project
import project_template
import structure
import templates


def _typst(here, mode="rs"):
    """Document `mode` of `here` compiled into its own PDF, by the one spelling of a compile's command line (documents.compile_args) -- with `--root` on the project's own folder for three documents. Not through `woodcore-cli export`, whose compile is the build routes' to bring to three documents (work package 1.6)."""
    return subprocess.run([project.typst_executable(), *documents.compile_args(here, mode)],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def _pages(pdf):
    """The text of every page of `pdf`, its runs of white collapsed: what a reader reads, and what two compiles of one report are compared by."""
    from pypdf import PdfReader
    return [" ".join((page.extract_text() or "").split()) for page in PdfReader(str(pdf)).pages]


def _tops(folder):
    return sorted(p.name for p in folder.iterdir())


def _in_config(data):
    """`data` -- a file's bytes or text -- with what a template, a form or a content template names at the root (`/config.typ`, `/commands.typ`, `/title.typ`, `/Template/…`) named where a project laid out by folders keeps it, in 000-Typst-Config/ (issue #64): what the creation rewrites, and nothing else."""
    pairs = [(f'"/{name}', f'"/{project.CONFIG_FOLDER}/{name}') for name in ("config.typ", "commands.typ", "title.typ", "Template/")]
    for old, new in pairs:
        data = data.replace(old.encode(), new.encode()) if isinstance(data, bytes) else data.replace(old, new)
    return data


# --- the layout ------------------------------------------------------------------------------------

def test_a_new_project_is_laid_out_in_three_documents():
    """Laid out by folders (issue #64, spec 2026-10-15-structure-projet-dossiers): what configures the three documents in 000-Typst-Config/ -- config.typ, commands.typ, references.bib, title.typ, the form's Template/ --, what is Woodcore's in 000-Woodcore/ -- the export, the engine, the sources, the archives --, the three documents in 100-, 200-, 300-, and one folder per kind of domain, every one there from the start (REQ-011) -- no RFEM-Export/ since the RFEM import was retired in 0.117; and the layout stated in full in the project's own file, schema 1.1, which reads nothing from DEFAULT_LAYOUT (the engineer's rule)."""
    folder = conftest.tmpdir("new_project") / "Halle Nord"
    here = project_template.create(folder, "Halle Nord", company="Musterbüro", number="  ")
    assert here.file == (folder / "Halle Nord.woodcore").resolve()
    assert here.has_modes and here.modes == project.MODES and here.has_folders
    assert here.layout == documents.layout_for("de"), here.layout
    data = json.loads(here.file.read_text(encoding="utf-8"))
    assert list(data["layout"]) == list(project.LAYOUT_ORDER), "the layout is not stated in full"
    assert data["schema_version"] == "1.1"
    assert data["company"] == "Musterbüro" and "number" not in data, data
    names = documents.MODE_FOLDERS
    assert _tops(folder) == sorted([".vscode", names["cu"], names["bp"], names["rs"], "Halle Nord.woodcore", "Images", "000-Typst-Config", "000-Woodcore",
                                    "Domains", "Positions", "Permanent-loads", "Variable-loads", "Plans", "Statics", "Details", "Connectors", "Connections",
                                    "Timber-checks", "Steel-checks", "Scripts", "Appendix"]), _tops(folder)
    assert sorted(p.name for p in (folder / "000-Typst-Config").iterdir()) == ["Template", "commands.typ", "config.typ", "references.bib", "title.typ"]
    assert {"sources", "archives", "data", "lib", "calc", "VERSION"} <= {p.name for p in (folder / "000-Woodcore").iterdir()}
    assert all(path.is_dir() for path in here.structure_folders()), "every folder of the layout is there from the start"
    assert not (folder / "Statischer Bericht (typst)").exists(), "the skeleton's own folder is renamed, not copied beside the three"
    assert not list((folder / "Images").iterdir()), "Images/ starts empty"
    report = folder / names["rs"]
    assert not any((report / name).exists() for name in ("config.typ", "commands.typ", "references.bib", "title.typ", "Images", "_woodcore", "Template")), \
        "what the three share is still in the report's folder"
    for mode in project.MODES:
        assert here.document_typ(mode).is_file(), mode
        assert here.document_typ(mode).name == documents.ENTRY_NAMES["de"][mode], here.document_typ(mode)
        assert here.document_pdf(mode) == here.document_typ(mode).with_suffix(".pdf"), "each PDF beside its own entry file, where Tinymist writes it"
    for mode in ("cu", "bp"):
        assert here.structure_file(mode).is_file(), mode
    assert here.report_typ == (report / "Statischer Rapport.typ").resolve(), "the report's entry file keeps its name"
    assert here.typst_root == here.root and here.generated_dir == (folder / "000-Woodcore").resolve()
    for part in ("config_typ", "commands_typ", "references_bib", "title_typ"):
        assert getattr(here, part).is_file(), part
    assert (here.template_dir / "template.typ").is_file() and (here.template_dir / "form.json").is_file(), "the form is Template/ in 000-Typst-Config/"
    import positions_store
    assert not here.positions_book.exists(), "no Positionen.xlsx is made since v0.114: the positions are Woodcore's own"
    assert positions_store.read(here) == [] and positions_store.path(here).is_file(), "an empty list of positions, Woodcore's own file"
    for sub in project.SOURCE_FOLDERS:
        assert (here.sources_dir / sub).is_dir(), sub
    assert here.archives_dir.is_dir() and here.images_dir.is_dir()
    settings = (here.root / ".vscode" / "settings.json").read_text(encoding="utf-8")
    # One PDF per document, whichever route writes it (v0.87): woodcore-cli and «Exporter PDF» write the layout's, beside each .typ, and Tinymist writes $dir/$name, beside the .typ, as long as the project's settings do not move it -- "$dir/../$name" until then, one level above.
    assert not re.search(r'^\s*"tinymist\.outputPath"\s*:', settings, re.M), "the template still moves Tinymist's PDF away from the .typ"
    assert project.engine_state(here)[0] == "current", "the engine is beside the export-to-be from the start"


def test_each_language_names_the_three_folders_its_own_way():
    """The folders are the same in every language -- «100-Service criteria agreement», «200-Basis of design», «300-Statical report» (issue #64, D-07, D-14) --, and the entry files of the two documents beside the report and the languages every file states follow the one language chosen -- the report keeping its own entry file's name in all three."""
    base = conftest.tmpdir("new_languages")
    for lang in documents.LANGUAGES:
        here = project_template.create(base / lang, "Halle", document_language=lang, report_language=lang)
        names = documents.MODE_FOLDERS
        assert {p.name for p in here.root.iterdir() if p.is_dir()} >= set(names.values()), (lang, _tops(here.root))
        for mode in project.MODES:
            assert here.document_typ(mode) == (here.root / names[mode] / documents.ENTRY_NAMES[lang][mode]).resolve(), (lang, mode)
            assert templates.read_languages(here.document_typ(mode)) == (lang, lang), (lang, mode)
        # the document's name is title.typ's, in the language the document is written in (v0.113): the entry asks for the convention's page
        assert '#title-page(document: "cu")' in here.document_typ("cu").read_text(encoding="utf-8"), "the convention d'utilisation does not set its title page"
        assert (here.root / "000-Typst-Config" / "title.typ").is_file(), "no title.typ in 000-Typst-Config/"
        assert here.layout == documents.layout_for(lang), (lang, here.layout)


def test_the_report_s_paths_are_read_from_the_project_s_own_folder():
    """A project template saved before forms is a report alone on disk, and is the one whose own report a new project still takes (Standard's is the rs content template, whose imports are root-absolute already); laid out in three documents, every path its files write that would no longer reach what it names is rewritten root-absolute (calc/typst_paths.py) -- the entry's two imports, each section's -- and every other byte is kept: `#include "Sections/…"`, `project: "references.bib"`, commands.typ's own import of the engine, which lies beside it still."""
    standard = _legacy_template("new_paths_template")
    here = project_template.create(conftest.tmpdir("new_paths") / "Pfade", "Pfade", template=standard)
    entry = here.report_typ.read_text(encoding="utf-8")
    config, commands, title = (f'/{project.CONFIG_FOLDER}/{name}' for name in ("config.typ", "commands.typ", "title.typ"))
    assert f'#import "{config}": conf' in entry and f'#import "{commands}": *' in entry, entry[:400]
    was = standard.report.read_text(encoding="utf-8")
    config_import, commands_import = '#import "config.typ": conf', '#import "commands.typ": *'   # the template's own imports, relative on purpose: what the creation rewrites
    title_import = '#import "title.typ": title-page'   # title.typ goes up with config.typ (v0.113); the template's own literal, relative on purpose
    assert entry == was.replace(config_import, f'#import "{config}": conf').replace(commands_import, f'#import "{commands}": *').replace(title_import, f'#import "{title}": title-page'), \
        "the report's entry file changed beyond its two imports"
    for section in templates.sections(here.report_typ.parent):
        text = section.read_text(encoding="utf-8")
        assert text.startswith(f'#import "{commands}": *'), section.name
        original = (standard.sections_dir / section.name).read_text(encoding="utf-8")
        assert text == original.replace('#import "../commands.typ": *', f'#import "{commands}": *', 1).replace('project: "references.bib"', f'project: "{project.CONFIG_FOLDER}/references.bib"'), section.name   # the template's own import, relative on purpose
    # commands.typ moved into 000-Typst-Config/: its import of the engine, `_woodcore/lib/…` beside it, is written from the root
    assert here.commands_typ.read_text(encoding="utf-8") == (standard.report_dir / "commands.typ").read_text(encoding="utf-8").replace('"_woodcore/lib/', '"/000-Woodcore/lib/')
    assert here.config_typ.read_bytes() == standard.config.read_bytes(), "config.typ is rewritten where its language was already the one asked for"
    assert here.references_bib.read_bytes() == (standard.report_dir / "references.bib").read_bytes()
    assert f'project: "{project.CONFIG_FOLDER}/references.bib"' in (here.report_typ.parent / "Sections" / "007-literatur.typ").read_text(encoding="utf-8")
    import typst_paths
    for path in here.root.rglob("*.typ"):
        if here.generated_dir not in path.parents:
            for literal in typst_paths.literals(typst_paths.read_text(path)):
                if literal.kind == "import":
                    assert literal.value in (commands, config, title) or path == here.commands_typ, (path, literal.value)


def test_a_new_project_goes_into_an_empty_folder_only():
    folder = conftest.tmpdir("new_not_empty")
    (folder / "something.txt").write_text("x", encoding="utf-8")
    try:
        project_template.create(folder, "X")
    except project.ProjectError as exc:
        assert "not empty" in str(exc), exc
    else:
        raise AssertionError("a new project was written into a folder holding something")
    try:
        project_template.create(conftest.tmpdir("new_no_name"), "  ")
    except project.ProjectError as exc:
        assert "name" in str(exc)
    else:
        raise AssertionError("a project with no name was made")


def test_a_new_project_s_positions_are_woodcore_s_own_and_a_blank_one_exports():
    """v0.114: no Positionen.xlsx -- the project's positions are an empty positions.json the Positions tab fills (calc/positions_store.py), and a position holding its id and its type alone, the one the plan tab writes, comes out as a position."""
    import export_all
    import positions_store
    folder = conftest.tmpdir("new_positions") / "Neu"
    here = project_template.create(folder, "Neu")
    positions_store.create_blank(here, None, "Träger")
    (position,), notes = export_all._positions(positions_store.read(here))
    assert (position["position"], position["type"], position["section"], position["moisture_class"]) == ("T001", "Träger", None, None) and not notes


# --- compiled -----------------------------------------------------------------------------------

def test_the_three_documents_compile_before_any_export():
    """v0.86.1: a new project had no data/ at all, and Tinymist stopped on «file not found … data/project.json» until the office's load workbook was copied in and exported -- which the engineer met on the first project «Nouveau projet» made. The project starts with the export of a project holding nothing (export_all.seed), its title page from the project file -- and, in three documents, the journals of the convention d'utilisation and of the base de projet, which their entry files read at every compile and Typst cannot ask the existence of. Each of the three compiles, in each language."""
    if not conftest.have_typst():
        raise conftest.Skip("no typst here")
    import export_all
    base = conftest.tmpdir("new_compiles_bare")
    for lang in documents.LANGUAGES:
        here = project_template.create(base / lang / "Übung 1", "Übung 1", document_language=lang, report_language=lang, author="Max Muster")
        info = json.loads((here.data_dir / "project.json").read_text(encoding="utf-8"))
        assert info["name"] == "Übung 1" and info["author"] == "Max Muster", info
        calculations = json.loads((here.data_dir / "calculations.json").read_text(encoding="utf-8"))
        assert not calculations["domains"]["snow-load"]["instances"], "no case of a workbook's domain before there is a workbook"
        assert calculations["domains"]["live-load"]["instances"], "SIA 261 Tabelle 8 needs no workbook, and every export carries it"
        assert export_all.seed(here) == [], "a project seeded once is not seeded again"
        for mode in here.modes:
            run = _typst(here, mode)
            assert run.returncode == 0, (lang, mode, run.stdout + run.stderr)
            assert here.document_pdf(mode).is_file(), (lang, mode)


def test_the_three_documents_compile_once_there_is_an_export():
    if not conftest.have_typst():
        raise conftest.Skip("no typst here")
    folder = conftest.tmpdir("new_compiles") / "Neu"
    here = project_template.create(folder, "Neu")
    shutil.copytree(conftest.PROJECT.data_dir, here.data_dir, dirs_exist_ok=True)
    # and the figures that export names, in the tabs' Exports/ and Appendix/, laid out by folders (issue #64, D-10)
    for kind in project.FIGURE_KINDS:
        if conftest.PROJECT.exports_dir(kind).is_dir():
            shutil.copytree(conftest.PROJECT.exports_dir(kind), here.exports_dir(kind), dirs_exist_ok=True)
    # and the domains that export wrote out, each in its file, which the report's sections include by domain-file(kind, id) (spec 2026-10-21-commandes-typst-refonte, REQ-017): their folders copied, data/domain-files.json listed again for this project -- its journals lie in its own documents' folders
    from domains import unfold
    for folder_name in sorted(set(path.split("/")[0] for path in project.DOMAIN_FOLDERS.values())):
        if (conftest.PROJECT.root / folder_name).is_dir():
            shutil.copytree(conftest.PROJECT.root / folder_name, here.root / folder_name, dirs_exist_ok=True)
    data = {name: json.loads((here.data_dir / name).read_text(encoding="utf-8")) for name in ("checks.json", "steel.json", "calculations.json", "connectors.json", "connections.json", "scripts.json")}
    files = unfold.domain_files(here, data["checks.json"], data["steel.json"], data["calculations.json"], data["connectors.json"], data["connections.json"], data["scripts.json"])
    (here.data_dir / unfold.FILES_FILE).write_text(json.dumps(files, ensure_ascii=False), encoding="utf-8")
    for mode in here.modes:
        run = _typst(here, mode)
        assert run.returncode == 0, (mode, run.stdout + run.stderr)
        assert here.document_pdf(mode).is_file(), mode


def _legacy_template(name):
    """A project template of the engineer's own as it was saved before forms -- Standard's skeleton as a folder of its own, report, config.typ and title page included: the template a new project is still made from, those files its own, where Standard makes a project from the neutral form and the rs content template."""
    folder = conftest.tmpdir(name) / "Vorlage"
    shutil.copytree(templates.standard().folder, folder)
    template = templates.read(folder, "user")
    assert not template.error and template.ref != templates.STANDARD, template.error
    return template


def _report_alone(folder, name, **details):
    """A new project as one was made until the three documents: Standard's skeleton copied as it stands, its .woodcore stating no layout, the engine beside the export and the export seeded -- built here by hand, since `create` lays every new project out in three, so that the text the report printed then can be held against the one it prints now."""
    import export_all
    standard = templates.standard()
    shutil.copytree(standard.folder, folder, ignore=shutil.ignore_patterns(templates.FILE))
    (folder / standard.layout["report"]).parent.joinpath(templates.IMAGES).mkdir(exist_ok=True)
    here = project.write(folder / f"{name}.woodcore", name, **details)
    assert not here.has_modes and here.layout == project.DEFAULT_LAYOUT
    project.sync_engine(here)
    export_all.seed(here)
    return here


def test_the_report_prints_what_a_report_alone_printed():
    """Nothing of the report is renamed by its becoming the third document (the engineer's decision), and nothing it prints moves: compiled from the project's own folder, every page of the report of a project made from a template saved before forms reads, word for word, what a new project's report read when it was a report alone."""
    if not conftest.have_typst():
        raise conftest.Skip("no typst here")
    base = conftest.tmpdir("new_same_text")
    alone = _report_alone(base / "Allein", "Halle Nord", company="Musterbüro", author="Max Muster")
    three = project_template.create(base / "Drei", "Halle Nord", template=_legacy_template("new_same_text_template"), company="Musterbüro", author="Max Muster")
    for here in (alone, three):
        run = _typst(here, "rs")
        assert run.returncode == 0, run.stdout + run.stderr
    before, after = _pages(alone.report_pdf), _pages(three.report_pdf)
    assert len(before) == len(after), (len(before), len(after))
    for number, (was, now) in enumerate(zip(before, after), 1):
        assert was == now, f"page {number} of the report reads otherwise:\n{was}\n---\n{now}"
    assert "Halle Nord" in after[0] and "Statischer Bericht" in after[0]


# --- the export it starts with ----------------------------------------------------------------------

def test_the_journals_of_the_three_documents_are_seeded_and_seeding_twice_writes_nothing():
    """Each document prints its own «Historique des versions» from its own journal, and Typst cannot ask whether a file is there: a new project in three documents is seeded all three, empty -- named as the sources are (project.JOURNAL_FILES) and as lib/calc-engine.typ's `journal-files` reads them."""
    import export_all
    import journal
    here = project_template.create(conftest.tmpdir("new_journals") / "Journal", "Journal")
    for mode in project.MODES:
        data = json.loads((here.data_dir / journal.EXPORT_FILES[mode]).read_text(encoding="utf-8"))
        assert data == {"schema_version": journal.EXPORT_SCHEMA_VERSION, "entries": []}, (mode, data)
    assert journal.EXPORT_FILES["rs"] == journal.EXPORT_FILE
    assert journal.EXPORT_FILES == project.JOURNAL_FILES, "the export's journals are not named as the sources'"
    engine = conftest.engine_source()
    table = re.search(r"#let journal-files = \((.*?)\)\n", engine).group(1)
    assert dict(re.findall(r'(\w+): "([^"]+)"', table)) == journal.EXPORT_FILES, table
    before = {p.name: p.read_bytes() for p in here.data_dir.iterdir()}
    assert export_all.seed(here) == [] and export_all.seed(here) == []
    assert {p.name: p.read_bytes() for p in here.data_dir.iterdir()} == before, "seeding a seeded project wrote something"


def test_a_report_alone_is_seeded_as_it_always_was():
    """A project laid out as a report alone has neither the convention d'utilisation nor the base de projet, and its export is seeded exactly the files it was seeded before the three documents -- no journal of a document it has not got."""
    import export_all
    here = _report_alone(conftest.tmpdir("new_seed_alone") / "Allein", "Allein")
    assert sorted(p.name for p in here.data_dir.iterdir()) == sorted([
        "project.json", "calculations.json", "positions-index.json", "connectors.json", "connections.json", "plans.json",
        "statics.json", "schemas.json", "journal.json", "scripts.json", "annexes.json", "fire.json",
        # the member checks (domains/member_check.py), seeded empty like every other export a report reads
        "checks.json",
        # where the domains Woodcore writes stand, and their files (spec 2026-10-21-commandes-typst-refonte, ARCH-007, ARCH-008), which #domain and domain-file read
        "domain-state.json", "domain-files.json",
        # the index of the «Formules» tab's domains (v0.117), which the «Variables» tab reads (issue #15)
        "formulas.json",
        # the quantities of the position plans (issue #9), which show-plan-quantities and sheet-quantities read
        "quantities.json",
        # the steel checks (domains/steel_check.py, issue #51), seeded empty like the member checks
        "steel.json",
        # the graph of dependencies (issue #71), which the «Dépendances» tab reads before a first export
        "dependencies.json"]), sorted(p.name for p in here.data_dir.iterdir())
    assert export_all.seed(here) == []
    (here.data_dir / "journal.json").unlink()
    assert export_all.seed(here) == ["journal.json"], "the report's journal is seeded as it always was"


def test_a_project_that_never_had_a_load_workbook_exports_without_one():
    """v0.89.1, the engineer's rule: no load workbook is a warning while no export has read one -- a new project exports its positions, plans and connectors before the office's workbook is copied in -- and still stops the export where the last one read a workbook that is gone, naming it: renamed out of the pattern, moved into a subfolder or not yet synced, it would otherwise look exactly like a project without loads, and the export would write the report's loads away. Until v0.89.1 it stopped whatever the project. Since v0.117 the export of a project that never had one says so in one line on stdout and warns no more: the engineer saw the warning on every export of a new project, in the window's box of warnings."""
    import contextlib
    import io
    import export_all
    import validation
    folder = conftest.tmpdir("new_no_loads") / "Ohne Lasten"
    here = project_template.create(folder, "Ohne Lasten")
    record = here.data_dir / "project.json"
    assert list(json.loads(record.read_text(encoding="utf-8"))["workbooks"]) == [], "a seeded project has read no workbook at all"
    with project.using(here):
        # never had one: the export goes on, one line of information on stdout and no warning on stderr (v0.117, the engineer: «cette erreur ne doit plus être affichée»)
        err, out = io.StringIO(), io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
            export_all.run(dry=True)
        assert "no load workbook" not in err.getvalue(), err.getvalue()
        assert "no load workbook" in out.getvalue() and "loads: none" in out.getvalue(), out.getvalue()
        # the last export read one, and it is gone: the export stops, naming it and the record that says so
        info = json.loads(record.read_text(encoding="utf-8"))
        info["workbooks"]["02_Belastungsannahmen.xlsm"] = "0" * 64
        record.write_text(json.dumps(info), encoding="utf-8")
        try:
            export_all.run(dry=True)
        except validation.ValidationError as exc:
            assert "02_Belastungsannahmen.xlsm" in str(exc) and "project.json" in str(exc), exc
        else:
            raise AssertionError("a load workbook the last export read is gone, and the export went on without it")
        # the way out the message names: the record deleted, the project is one without loads
        record.unlink()
        with contextlib.redirect_stderr(io.StringIO()):
            export_all.run(dry=True)


def test_seeding_fills_what_is_missing_and_touches_nothing_else():
    """The project the engineer met it on had saved a plan: data/plans.json was there, written by the window, and nothing else. Seeding writes the files it lacked -- a document's journal among them -- and leaves that one as it was, byte for byte, so the window may seed every project it opens."""
    import export_all
    folder = conftest.tmpdir("new_seed_partial") / "Teil"
    here = project_template.create(folder, "Teil")
    gone = ["project.json", "calculations.json", "positions-index.json", "connectors.json", "statics.json", "journal-cu.json"]
    for name in gone:
        (here.data_dir / name).unlink()
    plans = here.data_dir / "plans.json"
    plans.write_text('{"schema_version": "1.2", "plans": {"P01": "the window\'s own"}}\n', encoding="utf-8")
    before = plans.read_bytes()
    written = export_all.seed(here)
    assert sorted(written) == sorted(gone), written
    assert plans.read_bytes() == before, "a file an export or the window wrote is never touched"


# --- the three folders, named at creation --------------------------------------------------------------

def test_the_three_folders_are_named_at_creation():
    """The question v0.100 asked of the report's folder, asked of the three (the engineer's answer: offered in the creation dialog, editable there): `folders` names any of them, by mode or as three names in order, and `report_folder` the report's alone, as «Nouveau projet» and `woodcore-cli new --report-folder` still pass it. What is not named is what calc/documents.py offers for the language."""
    base = conftest.tmpdir("new_folders")
    here = project_template.create(base / "Eins", "Eins", folders={"cu": "NV", "bp": "PB"}, report_folder="Statik")
    assert [here.document_dir(mode).name for mode in project.MODES] == ["NV", "PB", "Statik"]
    assert here.document_typ("cu").name == "Nutzungsvereinbarung.typ" and here.report_typ.name == "Statischer Rapport.typ", "a folder is renamed, never an entry file"
    here = project_template.create(base / "Zwei", "Zwei", folders=("A", "B", "C"), document_language="en")
    assert [here.document_dir(mode).name for mode in project.MODES] == ["A", "B", "C"]
    here = project_template.create(base / "Drei", "Drei", folders={"bp": ""}, document_language="fr")
    assert [here.document_dir(mode).name for mode in project.MODES] == list(documents.MODE_FOLDERS.values()), "an empty name is no name, and the fixed one is offered"
    stated = json.loads(here.file.read_text(encoding="utf-8"))["layout"]
    assert stated == here.layout and list(stated) == list(project.LAYOUT_ORDER)


def test_a_refused_folder_leaves_nothing_behind():
    """The defect this was written for (v0.100): the name was checked *after* the skeleton had been copied, so a refused one left a half-copied project behind and the next attempt then failed on «is not empty» instead of on the name. Every name is checked before anything is created -- one that is not a folder's, two documents on one folder (as Windows compares names), a folder that would meet one of the files the three share, the report's folder named twice -- and a creation that fails later takes away what it wrote, the engine's read-only copy included."""
    folder = conftest.tmpdir("refused_folder") / "Halle"
    refused = [{"report_folder": bad} for bad in ("a/b", "..", "CON", "x?y")]
    refused += [{"folders": {"cu": "Gleich", "bp": "gleich"}}, {"folders": {"cu": "Images"}}, {"folders": {"bp": "config.typ"}},
                {"folders": {"rs": "000-Woodcore"}}, {"folders": {"cu": "000-Typst-Config"}}, {"folders": {"rs": "Statik"}, "report_folder": "Bericht"}, {"folders": ("A", "B")},
                {"folders": {"xx": "X"}}]
    for kwargs in refused:
        try:
            project_template.create(folder, "Halle", **kwargs)
        except project.ProjectError:
            pass
        else:
            raise AssertionError(f"{kwargs!r} was accepted")
        assert not folder.exists(), f"{kwargs!r} left a folder behind"
    import export_all
    real = export_all.seed

    def failing(here):
        raise project.ProjectError("planted: the seed failed")
    export_all.seed = failing
    try:
        project_template.create(folder, "Halle")
    except project.ProjectError as exc:
        assert "planted" in str(exc), exc
    else:
        raise AssertionError("a creation whose seed failed went through")
    finally:
        export_all.seed = real
    assert not folder.exists(), f"a failed creation left {sorted(p.name for p in folder.rglob('*'))} behind"
    here = project_template.create(folder, "Halle", report_folder="Statique")
    assert (folder / "Statique").is_dir() and here.report_typ.parent.name == "Statique", "and a sound name still works afterwards"


def test_the_folders_offered_are_the_language_own_words():
    """«300-Statical report» in every language since the project laid out by folders (issue #64, D-07, D-14) -- the report's folder a number and the document's English name, where 0.111 to 0.118 offered «3_Rapport de statique» in French and «3_Statischer Bericht» in German."""
    standard = templates.standard()
    for lang in documents.LANGUAGES + ("it",):
        assert templates.report_folder_offered(standard, lang) == documents.MODE_FOLDERS["rs"], lang
        assert templates.folders_offered(standard, lang) == documents.MODE_FOLDERS, lang
    assert templates.REPORT_FOLDERS == {lang: documents.MODE_FOLDERS["rs"] for lang in documents.LANGUAGES}


# --- the command line --------------------------------------------------------------------------------

def test_the_command_line_makes_a_new_project_and_names_none_to_do_it():
    folder = conftest.tmpdir("new_cli") / "Brücke"
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    env.pop(project.ENV, None)
    run = subprocess.run([sys.executable, str(CALC / "cli.py"), "new", str(folder), "--author", "Max Muster"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    assert run.returncode == 0, run.stdout + run.stderr
    here = project.Project.load(folder / "Brücke.woodcore")
    assert here.name == "Brücke" and here.detail("author") == "Max Muster"
    assert here.layout == documents.layout_for("de"), "woodcore-cli new lays a project out by folders, its documents in three"


def test_the_command_line_names_the_report_folder_and_the_language():
    """`woodcore-cli new --language fr` writes both languages -- the document's in config.typ and the engine's in every entry file, one choice setting both (his answer C9) -- the three folders keeping their fixed names (issue #64); `--report-folder` names the report's."""
    base = conftest.tmpdir("new_cli_lang")
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    env.pop(project.ENV, None)
    run = subprocess.run([sys.executable, str(CALC / "cli.py"), "new", str(base / "Pont"), "--language", "fr"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    assert run.returncode == 0, run.stdout + run.stderr
    here = project.Project.load(base / "Pont" / "Pont.woodcore")
    assert [here.document_dir(mode).name for mode in project.MODES] == list(documents.MODE_FOLDERS.values()), here.layout
    for mode in project.MODES:
        assert templates.read_languages(here.document_typ(mode)) == ("fr", "fr"), mode
    run = subprocess.run([sys.executable, str(CALC / "cli.py"), "new", str(base / "Steg"), "--language", "en", "--report-folder", "Statics"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    assert run.returncode == 0, run.stdout + run.stderr
    here = project.Project.load(base / "Steg" / "Steg.woodcore")
    assert [here.document_dir(mode).name for mode in project.MODES] == ["100-Service criteria agreement", "200-Basis of design", "Statics"]


# --- a report alone, which a project that states no layout still is --------------------------------------

def test_a_project_that_states_no_layout_reads_the_default_one():
    """The guard that stops `project.DEFAULT_LAYOUT` being renamed (v0.100).

    Both real projects -- the engineer's Musterprojekt and tests/projet-exemple -- stated **no** `layout` at all until they were migrated into three documents (tests/projet-exemple in work package 1.8, Musterprojekt on the engineer's word), and every project a clone of an older Woodcore made still states none, so the constant is what finds their report folder: `Project.__init__` does `{**DEFAULT_LAYOUT, **data.get("layout", {})}`. Renaming it to give new projects a differently named folder would have made the report of both unfindable at once, which is why C was built the other way round -- the constant stays as the layout of a project created before v0.100, and a new project states its own (in full since the three documents).
    """
    folder = conftest.tmpdir("no_layout") / "Alt"
    folder.mkdir(parents=True)
    (folder / "Alt.woodcore").write_text(
        json.dumps({"schema_version": "1.0", "format": "woodcore-project", "name": "Alt"}), encoding="utf-8")
    here = project.Project.load(folder / "Alt.woodcore")
    assert here.layout == project.DEFAULT_LAYOUT and not here.has_modes
    assert here.report_typ.parent.name == "Statischer Bericht (typst)", here.report_typ
    if "layout" in conftest.PROJECT.data:
        assert "typst_root" in conftest.PROJECT.data["layout"], "the example project states a layout of a report alone -- this check no longer guards what it means to"


def _old_folder(root, base):
    """A folder laid out as a project was until v0.80: the report and its code, the code's engine without a VERSION."""
    report = root / base
    (report / "000-Python" / "lib").mkdir(parents=True)
    (report / "000-Python" / "connectors").mkdir()
    (report / "Statischer Rapport.typ").write_text("= Statischer Bericht\n", encoding="utf-8")
    (report / "000-Python" / "lib" / "calc-engine.typ").write_text("// the old engine\n", encoding="utf-8")
    return report


def test_an_old_folder_is_converted_where_it_stands():
    root = conftest.tmpdir("convert") / "Altprojekt"
    report = _old_folder(root, "000-TypstRapport")
    before = sorted(p.relative_to(root).as_posix() for p in root.rglob("*"))
    here = project_template.convert(root)
    after = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p != here.file)
    assert before == after, "converting moved or wrote something besides the project file"
    assert here.name == "Altprojekt"
    assert here.report_typ == (report / "Statischer Rapport.typ").resolve()
    assert here.connectors_dir == (report / "000-Python" / "connectors").resolve()
    assert here.data_dir == (report / "000-Python" / "data").resolve()
    assert here.report_pdf == (root / "Statischer Rapport.pdf").resolve()
    assert project.engine_state(here) == ("unknown", "lib/calc-engine.typ")
    try:
        project.sync_engine(here)
    except project.EngineDecision as exc:
        assert exc.state == "unknown" and "--update-engine" in str(exc), exc
    else:
        raise AssertionError("the engine an old folder carried was replaced without being asked")
    assert (report / "000-Python" / "lib" / "calc-engine.typ").read_text(encoding="utf-8") == "// the old engine\n"
    project.sync_engine(here, update=True)
    assert project.engine_state(here)[0] == "current"
    try:
        project_template.convert(root)
    except project.ProjectError as exc:
        assert "already a project" in str(exc), exc
    else:
        raise AssertionError("a folder that is a project already was converted again")


def test_an_archive_of_an_old_folder_converts_too_and_anything_else_is_refused():
    archive = conftest.tmpdir("convert_archive") / "260915-10h00"
    _old_folder(archive, "")
    here = project_template.convert(archive, name="Archiv 15.09.")
    assert here.report_typ == (archive / "Statischer Rapport.typ").resolve() and here.name == "Archiv 15.09."
    other = conftest.tmpdir("convert_other")
    try:
        project_template.convert(other)
    except project.ProjectError as exc:
        assert "not a folder laid out before Woodcore" in str(exc), exc
    else:
        raise AssertionError("a folder with nothing of the old layout was converted")


def test_the_project_file_is_rewritten_keeping_what_it_does_not_name():
    """«Propriétés du projet» and the empty folders rewrite the file through project.update: a key given "" goes, every key not named stays -- the layout of a converted folder above all."""
    folder = conftest.tmpdir("update")
    here = project.write(folder / "U.woodcore", "U", layout={"archives": "Archiv"}, author="A", checker="C")
    here = project.set_empty_folders(here, "tab_plan", ["Leer"])
    updated = project.update(here.file, name="U2", checker="", number="7", woodcore_version="0.83")
    data = json.loads(here.file.read_text(encoding="utf-8"))
    assert data["name"] == "U2" and data["number"] == "7" and "checker" not in data and data["author"] == "A"
    assert data["layout"] == {"archives": "Archiv"} and data[project.GUI_KEY]["empty_folders"] == {"tab_plan": ["Leer"]}
    assert data[project.PIN_KEY] == "0.83"
    assert updated.empty_folders("tab_plan") == ["Leer"] and updated.layout["archives"] == "Archiv"
    updated = project.set_empty_folders(updated, "tab_plan", [])
    assert project.GUI_KEY not in json.loads(here.file.read_text(encoding="utf-8")), "no folder left, and the file still keeps the window's part"
    assert not list(folder.glob("*.tmp")), "the rewrite left its temporary file behind"


def test_a_project_file_written_before_v0_96_keeps_its_folders_and_is_migrated_by_the_first_change():
    """The window's part of a project file was `katalog` until v0.96 and is `gui` since: a file written before is read as it stands, and the first time the window writes its empty folders it writes `gui`, carries into it what `katalog` held, and takes `katalog` out -- every other key kept (project.set_empty_folders)."""
    folder = conftest.tmpdir("gui_key")
    here = project.write(folder / "Alt.woodcore", "Alt", layout={"archives": "Archiv"}, author="A")
    here = project.update(here.file, **{project.KATALOG_KEY: {"empty_folders": {"tab_plan": ["Alt"], "tab_polar": ["Leer"]}}})
    assert project.KATALOG_KEY == "katalog" and project.GUI_KEY == "gui"
    assert here.empty_folders("tab_plan") == ["Alt"] and here.empty_folders("tab_polar") == ["Leer"], "a project file of before v0.96 lost its folders"
    assert project.set_empty_folders(here, "tab_plan", ["Alt"]) is here, "folders unchanged, and the file was rewritten all the same"
    assert project.KATALOG_KEY in json.loads(here.file.read_text(encoding="utf-8")), "a file is migrated only when its folders change"
    here = project.set_empty_folders(here, "tab_plan", ["Alt", "Neu"])
    data = json.loads(here.file.read_text(encoding="utf-8"))
    assert project.KATALOG_KEY not in data, "the old key stayed beside the new one"
    assert data[project.GUI_KEY] == {"empty_folders": {"tab_plan": ["Alt", "Neu"], "tab_polar": ["Leer"]}}, data
    assert data["layout"] == {"archives": "Archiv"} and data["author"] == "A" and data["name"] == "Alt"
    assert project.Project.load(here.file).empty_folders("tab_polar") == ["Leer"]
    # a file carrying both, written by hand or by two versions in turn, is read by its new key
    both = project.update(here.file, **{project.KATALOG_KEY: {"empty_folders": {"tab_plan": ["Alt_nur"]}}})
    assert both.empty_folders("tab_plan") == ["Alt", "Neu"], "the old key was read over the new one"


# --- the look of a project: its form (work package 3.5, then calc/forms.py) ---------------------------------------------------------

def _text(path):
    """A file's text exactly as it lies, its line endings included: config.typ is CRLF in this checkout, and what a form swap must keep is bytes."""
    return path.read_bytes().decode("utf-8")


def _styled(folder, name="Halle", **kwargs):
    """A new project made with `kwargs` -- a style among them -- and the text of its one config.typ, which the three documents share."""
    here = project_template.create(folder, name, **kwargs)
    return here, _text(here.config_typ)


def test_no_form_neutral_and_an_empty_name_all_make_the_neutral_form():
    """No form, `neutral`, a Form object of it, the older `style=` name and an empty name all give the same project: the neutral form in `Template/` and a config.typ that holds the language and nothing of the look -- the default look is neutral, and asking for it changes nothing."""
    import forms
    base = conftest.tmpdir("form_neutral")
    results = {}
    for label, kwargs in (("none", {}), ("form", {"form": "neutral"}), ("object", {"form": forms.default()}), ("builtin", {"form": "builtin:neutral"}),
                          ("style", {"style": "neutral"}), ("empty", {"form": "", "style": ""})):
        here = project_template.create(base / label, "Halle", **kwargs)
        assert forms.current(here).ref == "builtin:neutral", label
        assert here.config_typ.read_text(encoding="utf-8") == _in_config(forms.config_text("de", "CH")), label
        assert not list(here.root.rglob("config.typ.new")), label
        results[label] = (here.title_typ.read_bytes(), (here.template_dir / "template.typ").read_bytes())
    assert len(set(results.values())) == 1, "the neutral form was made differently by two ways of asking for it"
    assert results["none"][0] == _in_config(forms.default().title_typ.read_bytes()) and results["none"][1] == forms.default().template_typ.read_bytes()


def test_the_compact_form_is_the_neutral_ones_page_set_smaller_and_the_projects_language_is_kept():
    """«Compact» is the neutral form's page and text set smaller, nothing else moved -- and the project's own language, which lives in config.typ beside the call of the form, is the one it carries: a French project made «compact» is still French. What differs from neutral is `Template/` and nothing at the top of the project but that."""
    import forms
    base = conftest.tmpdir("form_compact")
    neutral = project_template.create(base / "neutral", "Halle", document_language="fr", report_language="fr")
    here = project_template.create(base / "compact", "Halle", document_language="fr", report_language="fr", form="compact")
    assert forms.current(here).ref == "builtin:compact"
    compact = (here.template_dir / "template.typ").read_text(encoding="utf-8")
    plain = (neutral.template_dir / "template.typ").read_text(encoding="utf-8")
    assert compact != plain and "size: 10pt" in compact and "size: 11pt" not in compact, compact[:900]
    assert here.config_typ.read_bytes() == neutral.config_typ.read_bytes(), "the two forms hold their look in Template/, config.typ is the same file"
    assert templates.read_languages(here.report_typ) == ("fr", "fr"), "the project lost its language to the form"
    assert '#let doc-lang = "fr"' in _text(here.config_typ) and '#let doc-region = "CH"' in _text(here.config_typ)
    assert not list(here.root.rglob("config.typ.new"))
    german = project_template.create(base / "german", "Halle", form="compact")   # a project created German keeps German, too
    assert '#let doc-lang = "de"' in _text(german.config_typ)


def test_two_different_forms_are_refused_and_the_older_name_is_an_alias():
    """`style` is the older name of `form`: the same form named by both is fine, two different ones are refused before anything is written -- and a creation leaves no folder behind."""
    import forms
    base = conftest.tmpdir("form_alias")
    here = project_template.create(base / "same", "Halle", form="compact", style="builtin:compact")
    assert forms.current(here).ref == "builtin:compact"
    folder = base / "two"
    try:
        project_template.create(folder, "Halle", form="compact", style="bfh")
    except project.ProjectError as exc:
        assert "builtin:compact" in str(exc) and "builtin:bfh" in str(exc), exc
    else:
        raise AssertionError("two different forms were accepted")
    assert not folder.exists()


def test_a_projects_form_is_switched_mid_project_and_its_language_and_adjustments_survive_both_ways():
    """`replace_config` -- the older name of switching a form, `forms.apply` -- on a project that already exists: compact, then neutral again. The config.typ is the engineer's now, language and adjustments, and is kept by each switch; the old `Template/` goes into `_Archiv/<stamp>-forme/`, never deleted. A config.typ that is gone is written afresh in the project's language."""
    import forms
    here = project_template.create(conftest.tmpdir("style_switch") / "Wechsel", "Wechsel", document_language="en", report_language="en")
    mine = _text(here.config_typ).replace('#let doc-region = "CH"', '#let doc-region = "GB"').replace("  doc\n}", "  set text(size: 9pt)\n  doc\n}")
    here.config_typ.write_bytes(mine.encode("utf-8"))
    assert templates.replace_config(here, "compact") == here.config_typ
    assert forms.current(here).ref == "builtin:compact" and _text(here.config_typ) == mine, "config.typ is the engineer's and is kept"
    assert "size: 10pt" in (here.template_dir / "template.typ").read_text(encoding="utf-8")
    archive = next(here.archives_dir.glob("*-forme*"))
    assert "size: 11pt" in (archive / "Template" / "template.typ").read_text(encoding="utf-8"), "the old form is kept"
    templates.replace_config(here, "neutral")
    assert forms.current(here).ref == "builtin:neutral" and _text(here.config_typ) == mine
    assert len(list(here.archives_dir.glob("*-forme*"))) == 2
    here.config_typ.unlink()   # a project whose config.typ is gone has it written again, in its language
    templates.replace_config(here, "compact")
    assert '#let doc-lang = "en"' in _text(here.config_typ) and forms.is_form_config(here.config_typ)
    assert not list(here.root.rglob("config.typ.new"))


def test_an_unknown_form_is_refused_naming_the_valid_ones_and_a_creation_leaves_nothing_behind():
    """Before anything is written: `replace_config` names the forms there are and leaves the project as it was, and `create` refuses in the same words without making the folder -- the form being checked with the template, before the first file."""
    base = conftest.tmpdir("style_unknown")
    for key in ("style", "form"):
        folder = base / f"Nie-{key}"
        try:
            project_template.create(folder, "Nie", **{key: "barock"})
        except project.ProjectError as exc:
            assert "no form 'barock'" in str(exc) and "builtin:neutral" in str(exc) and "builtin:compact" in str(exc) and "builtin:bfh" in str(exc), exc
        else:
            raise AssertionError("a project was made in a form that does not exist")
        assert not folder.exists(), "a refused form left a folder behind"
    here = project_template.create(base / "Da", "Da")
    before = _tree_bytes(here)
    try:
        templates.replace_config(here, "barock")
    except templates.TemplateError as exc:
        assert "no form 'barock'" in str(exc) and "builtin:compact" in str(exc), exc
    else:
        raise AssertionError("an unknown form was applied")
    assert _tree_bytes(here) == before


def _tree_bytes(here):
    """Every file of the project but its export and archives, as {path: bytes}: what a refused switch must leave as it is."""
    return {path: path.read_bytes() for path in sorted(here.root.rglob("*")) if path.is_file() and here.generated_dir not in path.parents}


def test_the_three_documents_compile_with_every_builtin_form_in_the_three_languages():
    """A form is `Template/template.typ` and the entry files import `conf` from config.typ, which calls it: each of the three documents of a project made with each builtin form compiles before any export, in the three languages -- the report being the rs content template's, the two others their own -- and the title page is the form's, carrying the project's name."""
    if not conftest.have_typst():
        raise conftest.Skip("no typst here")
    import forms
    base = conftest.tmpdir("form_compiles")
    ids = [form.id for form in forms.list_forms() if form.place == "builtin"]
    assert {"neutral", "compact", "bfh"} <= set(ids), ids
    for form in ids:
        for lang in ("de", "fr", "en"):
            here = project_template.create(base / form / lang / "Halle", "Halle Nord", document_language=lang, report_language=lang, form=form, author="L. Exempel")
            assert forms.current(here).id == form and templates.read_languages(here.report_typ) == (lang, lang)
            for mode in here.modes:
                run = _typst(here, mode)
                assert run.returncode == 0, (form, lang, mode, run.stdout + run.stderr)
                assert here.document_pdf(mode).is_file(), (form, lang, mode)
            assert "Halle Nord" in _pages(here.report_pdf)[0], (form, lang)
    neutral = project.Project.load(base / "neutral" / "de" / "Halle" / "Halle Nord.woodcore")
    bfh = project.Project.load(base / "bfh" / "de" / "Halle" / "Halle Nord.woodcore")
    assert _pages(neutral.report_pdf)[0] != _pages(bfh.report_pdf)[0], "two forms give one title page"


def test_the_report_of_a_new_project_is_the_rs_content_template_in_each_language():
    """The report's entry and sections are `templates/documents/rs/standard/<language>/` as they stand (instantiate), named as the project names its entry, and nothing of the skeleton's own report -- its old sections numbered otherwise -- is left beside them. A project template saved before forms keeps its own report unless `document_templates` names the report's content, and is given no form it did not ask for."""
    import forms
    base = conftest.tmpdir("new_rs_content")
    for lang in ("fr", "de", "en"):
        here = project_template.create(base / lang, "Halle", document_language=lang, report_language=lang)
        content = doc_templates.find("builtin:rs/standard").language_dir(lang)
        assert here.report_typ.read_bytes() == _in_config((content / "Statischer Rapport.typ").read_bytes()), lang
        sections = sorted(p.name for p in (here.report_typ.parent / "Sections").iterdir())
        assert sections == sorted(p.name for p in (content / "Sections").iterdir()), (lang, sections)
    legacy = _legacy_template("new_rs_explicit")
    own = project_template.create(base / "own", "Halle", template=legacy)
    assert own.report_typ.read_bytes() == _in_config(legacy.report.read_bytes().replace(b'#import "config.typ"', b'#import "/config.typ"').replace(b'#import "commands.typ"', b'#import "/commands.typ"').replace(b'#import "title.typ"', b'#import "/title.typ"')), "a template saved before forms makes its own report"   # relative on purpose: the legacy template's own imports, which the creation rewrites
    assert forms.current(own) is None, "a project template saved before forms is not given a form it did not ask for"
    custom = project_template.create(base / "mine", "Halle", document_templates={"rs": "builtin:rs/standard"}, template=legacy)
    assert custom.report_typ.read_bytes() == _in_config((doc_templates.find("builtin:rs/standard").language_dir("de") / "Statischer Rapport.typ").read_bytes()), "a template that names the report's content gets it"
    assert forms.current(custom) is None


def test_a_template_saved_with_its_form_makes_a_project_with_that_form():
    """«Enregistrer ce projet comme modèle» carries `Template/` and title.typ (templates.save_project), and a project made from that template has them: a documents-shaped template with a form of its own is a project in that form, `form.json` and all -- no form is applied over it unless one is asked for, and one asked for replaces it without archiving a thing."""
    import forms
    base = conftest.tmpdir("form_saved")
    source = project_template.create(base / "Quelle", "Quelle", form="bfh")
    saved_env = os.environ.get("WOODCORE_TEMPLATES")
    os.environ["WOODCORE_TEMPLATES"] = str(base / "user")   # the engineer's templates, redirected for the length of the check
    try:
        saved = templates.save_project(source, "Mit Form", "user", {"templates": {}})
    finally:
        if saved_env is None:
            os.environ.pop("WOODCORE_TEMPLATES", None)
        else:
            os.environ["WOODCORE_TEMPLATES"] = saved_env
    assert (saved.folder / project.CONFIG_FOLDER / "Template" / "template.typ").is_file() and (saved.folder / project.CONFIG_FOLDER / "title.typ").is_file()
    here = project_template.create(base / "Ziel", "Ziel", template=saved)
    assert forms.current(here).ref == "builtin:bfh" and (here.template_dir / "logo-bfh.png").is_file()
    assert here.title_typ.read_bytes() == source.title_typ.read_bytes()
    other = project_template.create(base / "Anders", "Anders", template=saved, form="compact")
    assert forms.current(other).ref == "builtin:compact" and not list(other.archives_dir.glob("*-forme*")), "a new project has no old form to keep"


# --- the two documents beside the report: made from the engineer's own templates (work package 6.2) ----------------------------
#
# `create` hands each document its sibling documents (so a section a template shares with a document the project does not have is not shared) and settles the sharing once both are there, whichever templates they came from. What is held here: a new project made from a document template saved from a project -- its sections switched off still switched off, its text still there -- compiling; a convention d'utilisation of the engineer's combined with a base de projet that lacks a section it shares keeping no flag that says it is shared with nothing; a template handed over as the object it is, an office's whose folder no settings file names, needing no settings file; and a template in another language refused before anything is made.

MARK = "MODELEMARQUEUR"


@contextlib.contextmanager
def _own_documents(name):
    """The engineer's own document templates redirected into a clean folder of this process (`WOODCORE_TEMPLATES`) for the length of a check -- the suite's settings file names no office folder, so nothing else is read. Yields a namespace of `base` and `user` (the `documents/` folder of the engineer's place)."""
    base = conftest.tmpdir(name)
    saved = os.environ.get("WOODCORE_TEMPLATES")
    os.environ["WOODCORE_TEMPLATES"] = str(base / "user")
    try:
        yield types.SimpleNamespace(base=base, user=base / "user" / "documents")
    finally:
        if saved is None:
            os.environ.pop("WOODCORE_TEMPLATES", None)
        else:
            os.environ["WOODCORE_TEMPLATES"] = saved


def _leaves(here, mode):
    return [node for node, _depth in structure.leaves(structure.read(here.structure_file(mode)))]


def _document_template(root, mode, folder, names, languages, marker=MARK):
    """A document template `root/documents/<mode>/<folder>` made from the builtin one -- the languages it has only, the names given, `marker` written into the first section of each language -- read as the engineer's own (place `user`). Faster than saving one from a project, and what a list or a creation sees is the same."""
    builtin = doc_templates.find(f"builtin:{mode}/standard")
    target = root / "documents" / mode / folder
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(builtin.folder, target)
    for lang in doc_templates.LANGUAGES:
        if lang not in languages:
            shutil.rmtree(target / lang)
    meta = {"schema_version": "1.0", "format": doc_templates.FORMAT, "mode": mode,
            "name": {lang: names[lang] for lang in doc_templates.LANGUAGES if lang in languages},
            "description": {lang: f"{names[lang]} — description" for lang in doc_templates.LANGUAGES if lang in languages},
            "languages": [lang for lang in doc_templates.LANGUAGES if lang in languages]}
    (target / doc_templates.FILE).write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if marker:
        for lang in languages:
            first = structure.leaves(structure.read(target / lang / structure.FILE))[0][0]
            with open(target / lang / first["file"], "a", encoding="utf-8", newline="") as handle:
                handle.write(f"\n{marker}\n")
    template = doc_templates.read(target, mode, "user")
    assert not template.error, template.error
    return template


def test_a_new_project_made_from_a_saved_user_template_carries_its_disabled_sections_and_its_text_and_compiles():
    """The engineer's convention d'utilisation, saved from a project -- its second section switched off, its first section carrying his text -- and chosen when a new project is made: the project's convention has the second section still switched off (the entry says so, its heading is not in the PDF), the text in its file and in its PDF, and the base de projet is the builtin one. The template is handed over as the object, as the dialog hands it."""
    with _own_documents("np_user_cu") as ctx:
        source = project_template.create(ctx.base / "source" / "Quelle", "Quelle", document_language="fr", report_language="fr")
        first, second = _leaves(source, "cu")[:2]
        with open(source.document_dir("cu") / first["file"], "a", encoding="utf-8", newline="") as handle:
            handle.write(f"\n{MARK}\n")
        structure.set_enabled(source, "cu", second["id"], False)
        saved = doc_templates.save_from_document(source, "cu", "Convention courte", settings={})
        made = project_template.create(ctx.base / "new" / "Neuf", "Neuf", document_language="fr", report_language="fr", document_templates={"cu": saved})
        held = structure.read(made.structure_file("cu"))
        assert structure.find(held, second["id"])[0]["enabled"] is False, "a section switched off in the template came across switched on"
        assert f"// disabled: {second['id']} (" in made.document_typ("cu").read_text(encoding="utf-8"), "the entry does not say it"
        assert MARK in (made.document_dir("cu") / first["file"]).read_text(encoding="utf-8"), "the text the engineer wrote did not come across"
        builtin_bp = doc_templates.find("builtin:bp/standard").language_dir("fr")
        assert (made.document_dir("bp") / "Sections" / "live-loads.typ").read_bytes() == _in_config((builtin_bp / "Sections" / "live-loads.typ").read_bytes()), \
            "the other document is not the builtin one"
        assert not doc_templates.settle_sharing(made).changes, "a project made from a template shared as its source shared is settled"
        if not conftest.have_typst():
            raise conftest.Skip("no typst here")
        run = _typst(made, "cu")
        assert run.returncode == 0, run.stdout + run.stderr
        assert any(MARK in page for page in _pages(made.document_pdf("cu"))), "the pre-filled text is not in the PDF"
        titles = [structure.normalize_title(b.title) for b in structure.bookmarks_from_pdf(made.document_pdf("cu"))]
        disabled = structure.normalize_title(structure.scan_headings((made.document_dir("cu") / second["file"]).read_text(encoding="utf-8"))[0].title)
        assert disabled not in titles, "a section switched off in the template is printed"
        for mode in ("bp", "rs"):
            run = _typst(made, mode)
            assert run.returncode == 0, (mode, run.stdout + run.stderr)


def test_a_flag_that_says_a_section_is_shared_with_nothing_is_settled_when_the_project_is_made():
    """A convention d'utilisation of the engineer's that shares its live loads -- with the base de projet, and with the report -- combined with a base de projet that lacks that section: the project is made with every `shared_with` written again from the tags the files carry. The live loads' flag goes (no copy anywhere), the flags of what both documents share stay, and settling again changes nothing. The raw copy of the same template, made with the siblings the project has, still carries the flag: it is `create`'s settling that took it away."""
    with _own_documents("np_sharing") as ctx:
        source = project_template.create(ctx.base / "source" / "Quelle", "Quelle", document_language="fr", report_language="fr")
        structure.remove_section(source, "bp", "live-loads")
        path = source.structure_file("cu")
        held = structure.read(path)
        structure.find(held, "live-loads")[0]["shared_with"] = ["bp", "rs"]
        structure.write(path, held)
        cu = doc_templates.save_from_document(source, "cu", "Convention partagée", settings={})
        bp = doc_templates.save_from_document(source, "bp", "Base sans charges utiles", settings={})
        raw = doc_templates.instantiate("cu", "fr", ctx.base / "raw" / "1", template=cu, siblings=("bp", "rs"))
        assert structure.find(structure.read(raw.parent / "structure.json"), "live-loads")[0]["shared_with"] == ["bp", "rs"], \
            "the template does not carry the flag the check is about"
        made = project_template.create(ctx.base / "new" / "Neuf", "Neuf", document_language="fr", report_language="fr", document_templates={"cu": cu, "bp": bp})
        assert structure.find(structure.read(made.structure_file("bp")), "live-loads") is None, "the base de projet is the one that lacks the section"
        cu_live = structure.find(structure.read(made.structure_file("cu")), "live-loads")[0]
        assert "shared_with" not in cu_live, f"the flag stayed though no document holds a copy: {cu_live}"
        cu_flags = {node["id"]: node["shared_with"] for node in _leaves(made, "cu") if node.get("shared_with")}
        bp_flags = {node["id"]: node["shared_with"] for node in _leaves(made, "bp") if node.get("shared_with")}
        assert cu_flags and set(cu_flags) == set(bp_flags), (sorted(cu_flags), sorted(bp_flags))
        assert all(flag == ["bp"] for flag in cu_flags.values()) and all(flag == ["cu"] for flag in bp_flags.values()), "what both hold stays shared with the other, and with it alone"
        result = doc_templates.settle_sharing(made)
        assert not result.changes and not result.problems, (result.changes, result.problems)


def test_a_document_template_handed_over_as_an_object_needs_no_settings_file():
    """A template that lies in a folder no settings file names -- an office's, read as the office's -- made into a document when it is handed to `create` as the object. Handed over by its reference it would be found nowhere, which is why the dialog hands the objects."""
    with _own_documents("np_object") as ctx:
        office = conftest.tmpdir("np_object_office")
        template = _document_template(office, "bp", "kurz", {"fr": "Base courte", "de": "Kurze Basis"}, ("fr", "de"))
        template = doc_templates.read(template.folder, "bp", "office")
        try:
            doc_templates.find("office:bp/kurz")
        except doc_templates.DocTemplateError as exc:
            assert exc.code == "no_such_template", exc
        else:
            raise AssertionError("the office's folder is named by a settings file this check does not have")
        made = project_template.create(ctx.base / "Neuf", "Neuf", document_language="de", report_language="de", document_templates={"bp": template})
        assert MARK in (made.document_dir("bp") / _leaves(made, "bp")[0]["file"]).read_text(encoding="utf-8")
        assert made.document_typ("bp").name == documents.ENTRY_NAMES["de"]["bp"], "the entry file is named what the project calls it"


def test_a_document_template_that_does_not_exist_in_the_projects_language_is_refused_before_anything_is_made():
    with _own_documents("np_language") as ctx:
        template = _document_template(ctx.base / "user", "cu", "nur-fr", {"fr": "Convention en français"}, ("fr",))
        folder = ctx.base / "new" / "Neu"
        try:
            project_template.create(folder, "Neu", document_language="de", report_language="de", document_templates={"cu": template})
        except project.ProjectError as exc:
            assert "fr" in str(exc) and "de" in str(exc), exc
        else:
            raise AssertionError("a convention written in French was made into a German project")
        assert not folder.exists() or not any(folder.iterdir()), "a refused creation left files behind"


# --- a project made in two steps: the skeleton, then each document (issue #90) ---------------------------------

def _two_steps(name, language="fr", **details):
    root = conftest.tmpdir(name)
    return project_template.create_skeleton(root / "Projet", "Probe", language, **details)


def test_a_skeleton_has_its_language_its_layout_and_no_document():
    """«Nouveau projet» asks the name, the folder and the language (the engineer, 22.10.2026) and makes no document: the three folders and the language are stated, every document waits for its content template."""
    here = _two_steps("skeleton_bare", "fr", author="F. L.")
    assert here.has_folders and here.modes == project.MODES and here.created_modes == ()
    assert not any(here.is_created(mode) for mode in project.MODES)
    assert templates.project_language(here, fallback="") == "fr" and templates.read_languages(here.report_typ, config=here.config_typ)[0] == "fr"
    assert here.detail("author") == "F. L." and here.content_template("rs") == ""
    assert json.loads((here.data_dir / "project.json").read_text(encoding="utf-8"))["author"] == "F. L."
    for mode in project.MODES:   # no stray file in a document's folder: the document is made into an empty one
        folder = here.document_dir(mode)
        assert not folder.exists() or not any(folder.rglob("*")), (mode, sorted(folder.rglob("*")))
    assert project.Project.load(here.file).created_modes == ()


def test_each_document_made_later_is_the_one_a_whole_creation_makes():
    """`create` is the skeleton and its three documents: made one by one, in any order, they come to the very bytes a creation in one step writes -- the sharing of the convention d'utilisation and the base de projet settled once both are there."""
    import cli
    root = conftest.tmpdir("skeleton_whole")
    whole = project_template.create(root / "Whole", "Probe", document_language="fr", report_language="fr")
    here = project_template.create_skeleton(root / "Steps", "Probe", "fr")
    for mode in ("rs", "bp", "cu"):
        here = project_template.create_document(here, mode)
        assert here.is_created(mode) and here.content_template(mode) == f"builtin:{mode}/standard", mode
    assert whole.data["content_templates"] == here.data["content_templates"] == {m: f"builtin:{m}/standard" for m in project.MODES}

    def files(p):
        engine = p.generated_dir
        return {f.relative_to(p.root).as_posix(): f.read_bytes() for f in p.root.rglob("*")
                if f.is_file() and f.suffix in (".typ", ".json", ".bib") and not project._is_within(f, engine)}

    a, b = files(whole), files(here)
    assert sorted(a) == sorted(b), (sorted(set(a) - set(b)), sorted(set(b) - set(a)))
    differ = [name for name in a if a[name] != b[name] and not name.endswith(".woodcore")]
    assert not differ, differ
    assert cli.requested_documents(here) == project.MODES


def test_a_document_is_made_once_and_from_a_template_that_exists():
    here = project_template.create_document(_two_steps("skeleton_once"), "rs")
    before = here.file.read_bytes()
    try:
        project_template.create_document(here, "rs")
    except project.ProjectError:
        pass
    else:
        raise AssertionError("a document made twice")
    assert here.file.read_bytes() == before
    try:
        project_template.create_document(here, "cu", "builtin:cu/no-such-template")
    except project.ProjectError:
        pass
    else:
        raise AssertionError("an unknown content template accepted")
    folder = here.document_dir("cu")
    assert not here.is_created("cu") and (not folder.exists() or not any(folder.rglob("*"))), "a refused document left files behind"


def test_the_command_line_exports_only_the_documents_made():
    """`woodcore-cli export` on a project whose report alone is made: «all» is the report, and a document not made yet is refused by name rather than compiled against nothing."""
    import cli
    here = project_template.create_document(_two_steps("skeleton_cli"), "rs")
    assert cli.requested_documents(here) == ("rs",) and cli.requested_documents(here, "all") == ("rs",)
    try:
        cli.requested_documents(here, "cu")
    except project.ProjectError as exc:
        assert "not made yet" in str(exc), exc
    else:
        raise AssertionError("a document not made yet was asked for")


def test_a_report_made_alone_compiles():
    if not conftest.have_typst():
        raise conftest.Skip("typst is not installed here")
    here = project_template.create_document(_two_steps("skeleton_compiles"), "rs")
    done = _typst(here, "rs")
    assert done.returncode == 0, done.stderr[-2000:]
