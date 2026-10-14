"""What lands in the project's archives folder on every successful export, and what stays out (docs/conventions/build-and-release.md §12). One zip per export since v0.82, where it was a folder of hundreds of files.

Every check here builds its own small 000-TypstRapport/-shaped tree under tests/.tmp/ rather than touching the project's real 000-Archives/, with a .woodcore file of its own, and makes that the current project (calc/project.py), put back in a `finally`: every path the module uses is the current project's (docs/architecture/layout.md §11), so naming the project is the whole of the setup a test needs. Until v0.81 it reassigned the module's four path constants instead.
"""

import sys

import conftest
from conftest import ROOT

path = str(ROOT / "calc" / "tools")
if path not in sys.path:
    sys.path.insert(0, path)
import zipfile  # noqa: E402

import archive_export  # noqa: E402
import project  # noqa: E402


def _touch(path, content="x"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _sandbox(name):
    """A fresh {project_root, typst_root} pair under this process's own temp folder, typst_root empty and ready to be filled in by the caller."""
    project_root = conftest.tmpdir(name)
    typst_root = project_root / "000-TypstRapport"
    typst_root.mkdir()
    return project_root, typst_root


def _patched(project_root, typst_root):
    """The sandbox made the current project, laid out as this project was until v0.81 -- returns the scope, for the caller to close in a `finally`."""
    layout = {"report": f"{typst_root.name}/Statischer Rapport.typ", "pdf": "Statischer Rapport.pdf",
              "sources": f"{typst_root.name}/000-Python", "generated": f"{typst_root.name}/000-Python",
              "archives": f"{typst_root.name}/000-Archives"}
    scope = project.using(project.write(project_root / "Sandbox.woodcore", "Sandbox", layout))
    scope.__enter__()
    return scope


def _restore(scope):
    scope.__exit__(None, None, None)


def test_exclusions_keep_the_snapshot_to_what_a_rebuild_needs():
    """000-ExternalFiles/, 000-Archives/ itself, examples/, out/ and tests/.tmp/ never reach the snapshot; calc/, data/ and a generated .xlsx do -- proving the filter excludes by location, never by extension (docs/conventions/build-and-release.md §12)."""
    project_root, typst_root = _sandbox("archive_exclusions")
    original = _patched(project_root, typst_root)
    try:
        excluded = [
            typst_root / "000-ExternalFiles" / "norm.pdf",
            typst_root / "000-Python" / "examples" / "x.typ",
            typst_root / "000-Python" / "out" / "report-1.pdf",
            typst_root / "000-Python" / "tests" / ".tmp" / "leftover.txt",
            typst_root / "000-Python" / "calc" / "__pycache__" / "x.pyc",
            typst_root / "Sections" / "stray.pdf",
        ]
        survives = [
            typst_root / "000-Python" / "calc" / "x.py",
            typst_root / "000-Python" / "data" / "calculations.json",
            typst_root / "000-Python" / "docs" / "typst-reference.xlsx",  # generated, not an Excel *input* -- must not be swept out by an extension filter
            typst_root / "Sections" / "003-baustoffe.typ",
            typst_root / "commands.typ",
        ]
        for target in excluded + survives:
            _touch(target)
        project.current().report_pdf.write_bytes(b"%PDF-1.4 fake\n")

        archive = archive_export.run("test", "")

        assert archive is not None and archive.suffix == ".zip", "run() found the fake PDF but archived nothing in a zip"
        names = set(zipfile.ZipFile(archive).namelist())
        for target in excluded:
            rel = target.relative_to(project_root).as_posix()
            assert rel not in names, f"{rel} was excluded from the tree but reached the archive"
        for target in survives:
            rel = target.relative_to(project_root).as_posix()
            assert rel in names, f"{rel} should have been archived and was not"
        assert "archive-info.json" in names, "no manifest was written"
        assert "Sandbox.woodcore" in names, "the project file is not in the archive"
    finally:
        _restore(original)


def test_two_exports_in_the_same_minute_do_not_overwrite_each_other():
    """A collision is told apart with -2, never silently overwritten -- two exports genuinely can share a clock minute (a quick correction, a level/language trial), and this project generally asks rather than replaces without saying so (docs/decisions.md §13)."""
    project_root, typst_root = _sandbox("archive_collision")
    original = _patched(project_root, typst_root)
    original_timestamp = archive_export._timestamp
    archive_export._timestamp = lambda: "999999-99h99"
    try:
        _touch(typst_root / "commands.typ")
        project.current().report_pdf.write_bytes(b"first\n")
        first = archive_export.run("test", "")
        first_bytes = first.read_bytes()

        project.current().report_pdf.write_bytes(b"second\n")
        second = archive_export.run("test", "")

        assert first.name == "999999-99h99.zip", first.name
        assert second.name == "999999-99h99-2.zip", f"the second export did not get a distinct name: {second.name}"
        assert first.read_bytes() == first_bytes, "the first archive was touched by the second export"
        assert (project.current().archives_dir / "999999-99h99-Statischer Rapport.pdf").read_bytes() == b"first\n"
        assert (project.current().archives_dir / "999999-99h99-2-Statischer Rapport.pdf").read_bytes() == b"second\n"
    finally:
        archive_export._timestamp = original_timestamp
        _restore(original)


def test_an_archive_of_the_new_layout_holds_the_project_and_its_record():
    """The layout of v0.82: the report folder, the sources drawn in the window beside it, the engine copied into the report folder, the project file -- and not the workbooks, whose hashes data/project.json keeps, nor the archives folder itself. The manifest carries that record."""
    import json
    project_root = conftest.tmpdir("archive_layout")
    here = project.write(project_root / "Neu.woodcore", "Neu")
    with project.using(here):
        for target in (here.typst_root / "Statischer Rapport.typ", here.typst_root / "Sections" / "001.typ",
                       here.data_dir / "calculations.json", here.generated_dir / "lib" / "calc-engine.typ",
                       here.connectors_dir / "SD-1.json", here.details_dir / "D.json",
                       # the revision journal, one file at the top of the sources rather than a folder of them (v0.99): an archive holds what the report's own page prints
                       here.journal_file,
                       # the project's positions, Woodcore's own since v0.114 (calc/positions_store.py) -- and a Positionen.xlsx left beside them, which is no source any more
                       here.sources_dir / "positions.json",
                       here.positions_book, here.root / "Belastungsannahmen.xlsm",
                       here.archives_dir / "older.zip", here.typst_root / ".probe" / "p.typ"):
            _touch(target)
        (here.data_dir / "project.json").write_text(json.dumps({"name": "Neu"}), encoding="utf-8")
        here.report_pdf.write_bytes(b"%PDF-1.4 fake\n")
        archive = archive_export.run("test", "--input level=2")
        names = set(zipfile.ZipFile(archive).namelist())
        for kept in ("Neu.woodcore", "Statischer Bericht (typst)/Statischer Rapport.typ", "Statischer Bericht (typst)/Sections/001.typ",
                     "Statischer Bericht (typst)/_woodcore/data/calculations.json", "Statischer Bericht (typst)/_woodcore/lib/calc-engine.typ",
                     "Woodcore-Datei/connectors/SD-1.json", "Woodcore-Datei/details/D.json",
                     "Woodcore-Datei/journal.json", "Woodcore-Datei/positions.json", "archive-info.json"):
            assert kept in names, f"{kept} is not in the archive"
        # the PDF lies in the report's folder since v0.87 and is copied beside the zip, not into it a second time
        assert here.report_pdf.parent == here.typst_root, here.report_pdf
        assert (here.archives_dir / f"{archive.stem}-{here.report_pdf.name}").read_bytes() == b"%PDF-1.4 fake\n", "the flat copy of the PDF is not beside the zip"
        for left in ("Positionen.xlsx", "Belastungsannahmen.xlsm", "_Archiv/older.zip", "Statischer Bericht (typst)/.probe/p.typ",
                     "Statischer Bericht (typst)/Statischer Rapport.pdf"):
            assert left not in names, f"{left} reached the archive"
        manifest = json.loads(zipfile.ZipFile(archive).read("archive-info.json"))
        assert manifest["detail"] == "--input level=2" and manifest["project"] == {"name": "Neu"}, manifest


def test_a_fresh_checkout_with_no_pdf_yet_is_a_quiet_no_op():
    """Nothing has been compiled yet: run() must not raise, and must not create 000-Archives/ for nothing to put in it."""
    project_root, typst_root = _sandbox("archive_no_pdf")
    original = _patched(project_root, typst_root)
    try:
        assert not project.current().report_pdf.exists()
        result = archive_export.run("test", "")
        assert result is None, f"run() archived something with no PDF to archive: {result}"
        assert not project.current().archives_dir.exists(), "000-Archives/ was created for an export that never happened"
    finally:
        _restore(original)


def test_the_window_s_route_is_gui_and_its_old_name_is_read_as_it():
    """The manifest names the route that compiled: `woodcore-cli`, or `gui` for the window's *Exporter PDF* -- `katalog` until v0.96, which a caller of an older checkout may still pass and which is recorded as `gui`, so that one route is not named two ways across a project's archives."""
    import json
    assert archive_export.ROUTES == ("woodcore-cli", "gui") and archive_export.LEGACY_ROUTES == {"katalog": "gui"}
    assert 'archive_export.run("gui",' in conftest.module_source(ROOT / "calc" / "tools" / "woodcore_gui.py"), "the window archives under another route"
    project_root = conftest.tmpdir("archive_route")
    here = project.write(project_root / "Weg.woodcore", "Weg")
    with project.using(here):
        here.report_pdf.parent.mkdir(parents=True, exist_ok=True)
        here.report_pdf.write_bytes(b"%PDF-1.4 fake\n")
        for route, recorded in (("gui", "gui"), ("katalog", "gui"), ("woodcore-cli", "woodcore-cli")):
            archive = archive_export.run(route, "")
            manifest = json.loads(zipfile.ZipFile(archive).read("archive-info.json"))
            assert manifest["route"] == recorded, (route, manifest["route"])


# --- a project laid out in three documents (the engineer's request of 30.09.2026) ---------------------------

def _three(name):
    """A project in three documents, its layout calc/documents.py's for German, every part it archives or leaves out touched once -- and the other documents' folders, the workbooks, the architect's plans and `.vscode/` beside them, which a walk of the Typst root (the project's own folder here) would sweep in."""
    import documents
    here = project.write(conftest.tmpdir(name) / "Drei.woodcore", "Drei", layout=documents.layout_for("de"))
    for mode in here.modes:
        _touch(here.document_typ(mode))
        _touch(here.document_dir(mode) / "Sections" / f"{mode}-section.typ")
        _touch(here.document_dir(mode) / "Sections" / "stray.pdf")
    for mode in ("cu", "bp"):
        _touch(here.structure_file(mode), "{}")
    for target in (here.config_typ, here.commands_typ, here.references_bib, here.title_typ,
                   here.data_dir / "calculations.json", here.generated_dir / "lib" / "calc-engine.typ",
                   here.generated_dir / "VERSION", here.docs_dir / "typst-reference.xlsx",
                   here.generated_dir / "out" / "report-1.pdf", here.stamps_dir / "cu.json", here.stamps_dir / "cu.deps.json",
                   here.typst_root / "Template" / "template.typ", here.typst_root / "Template" / "form.json", here.typst_root / "Template" / "logo.png",
                   here.images_dir / "plan.png", here.root / "RFEM-Export" / "Modell.xlsx",
                   here.connectors_dir / "SD-1.json", here.details_dir / "D.json",
                   *(here.journal_file_for(mode) for mode in here.modes),
                   here.sources_dir / "positions.json",
                   here.positions_book, here.root / "Belastungsannahmen.xlsm", here.root / "01_Pläne" / "Grundriss.pdf",
                   here.root / ".vscode" / "settings.json", here.archives_dir / "older.zip",
                   here.generated_dir / "calc" / "__pycache__" / "x.pyc"):
        _touch(target)
    (here.data_dir / "project.json").write_text('{"name": "Drei"}', encoding="utf-8")
    return here


def test_an_archive_of_one_document_holds_that_document_and_what_the_three_share():
    """`<timestamp>-cu.zip` beside `<timestamp>-cu-Nutzungsvereinbarung.pdf`: the `.woodcore`, the document's own folder, config.typ, commands.typ, references.bib, title.typ and the form's `Template/`, the export less out/ and stamps/, the pictures, the sources and the three journals -- and **not** the other documents, an RFEM-Export/ folder an older project still carries (the RFEM import was retired in 0.117), the workbooks, the architect's plans, `.vscode/` or the archives: in three documents the Typst root is the project's own folder, and archiving it whole would take all of that along."""
    import json
    here = _three("archive_three")
    with project.using(here):
        pdf = here.document_pdf("cu")
        pdf.write_bytes(b"%PDF-1.4 cu\n")
        archive = archive_export.run("woodcore-cli", "--input level=2", mode="cu")
        assert archive is not None and archive.name.endswith("-cu.zip"), archive
        stem = archive.stem
        assert (here.archives_dir / f"{stem}-{pdf.name}").read_bytes() == b"%PDF-1.4 cu\n", "the flat copy of the CU's PDF is not beside its zip"
        names = set(zipfile.ZipFile(archive).namelist())
        rel = here.rel
        kept = [here.file.name, rel(here.document_typ("cu")), rel(here.document_dir("cu") / "Sections" / "cu-section.typ"),
                rel(here.structure_file("cu")), "config.typ", "commands.typ", "references.bib", "title.typ",
                "Template/template.typ", "Template/form.json", "Template/logo.png",
                "_woodcore/data/calculations.json", "_woodcore/lib/calc-engine.typ", "_woodcore/VERSION", "_woodcore/docs/typst-reference.xlsx",
                "Images/plan.png", "Woodcore-Datei/connectors/SD-1.json", "Woodcore-Datei/details/D.json",
                *(rel(here.journal_file_for(mode)) for mode in here.modes), "Woodcore-Datei/positions.json", "archive-info.json"]
        for name in kept:
            assert name in names, f"{name} is not in the CU's archive"
        left = [rel(pdf), rel(here.document_dir("cu") / "Sections" / "stray.pdf"),
                rel(here.document_typ("bp")), rel(here.document_typ("rs")), rel(here.document_dir("rs") / "Sections" / "rs-section.typ"),
                "_woodcore/out/report-1.pdf", "_woodcore/stamps/cu.json", "_woodcore/stamps/cu.deps.json", "_woodcore/calc/__pycache__/x.pyc",
                "Positionen.xlsx", "Belastungsannahmen.xlsm", "01_Pläne/Grundriss.pdf", ".vscode/settings.json", "_Archiv/older.zip", "RFEM-Export/Modell.xlsx"]
        for name in left:
            assert name not in names, f"{name} reached the CU's archive"
        manifest = json.loads(zipfile.ZipFile(archive).read("archive-info.json"))
        assert manifest["document"] == "cu" and manifest["detail"] == "--input level=2" and manifest["project"] == {"name": "Drei"}, manifest


def test_each_document_is_archived_apart_and_two_in_one_minute_do_not_overwrite_each_other():
    here = _three("archive_three_collision")
    saved = archive_export._timestamp
    archive_export._timestamp = lambda: "999999-99h99"
    try:
        with project.using(here):
            for mode in here.modes:
                here.document_pdf(mode).write_bytes(f"%PDF {mode}\n".encode())
            made = [archive_export.run("gui", "", mode=mode).name for mode in ("cu", "bp", "rs", "cu")]
            assert made == ["999999-99h99-cu.zip", "999999-99h99-bp.zip", "999999-99h99-rs.zip", "999999-99h99-cu-2.zip"], made
            assert (here.archives_dir / "999999-99h99-rs-Statischer Rapport.pdf").read_bytes() == b"%PDF rs\n"
            assert (here.archives_dir / f"999999-99h99-cu-2-{here.document_pdf('cu').name}").is_file()
            rs = set(zipfile.ZipFile(here.archives_dir / "999999-99h99-rs.zip").namelist())
            assert here.rel(here.document_typ("rs")) in rs and here.rel(here.document_typ("cu")) not in rs, sorted(rs)
    finally:
        archive_export._timestamp = saved


def test_a_document_not_compiled_yet_is_a_quiet_no_op_and_one_the_project_has_not_is_refused():
    here = _three("archive_three_no_pdf")
    with project.using(here):
        assert archive_export.run("woodcore-cli", "", mode="bp") is None
        assert [p.name for p in here.archives_dir.glob("*.zip")] == ["older.zip"], "an archive was written for a document never compiled"
    alone = project.write(conftest.tmpdir("archive_alone_cu") / "Allein.woodcore", "Allein")
    with project.using(alone):
        try:
            archive_export.run("woodcore-cli", "", mode="cu")
        except project.ProjectError as exc:
            assert "migrate" in str(exc), exc
        else:
            raise AssertionError("a report alone archived a convention d'utilisation it has not got")


def test_a_report_alone_keeps_its_stamps_out_of_its_archive():
    """The stamps (calc/stamps.py) lie in the export's folder, which a report alone keeps inside its own folder -- the one its archive takes whole. What a compile read says nothing of the state an archive reopens, whose PDF is not in the zip."""
    project_root = conftest.tmpdir("archive_alone_stamps")
    here = project.write(project_root / "Neu.woodcore", "Neu")
    with project.using(here):
        _touch(here.typst_root / "Statischer Rapport.typ")
        _touch(here.stamps_dir / "rs.json")
        _touch(here.data_dir / "calculations.json")
        here.report_pdf.write_bytes(b"%PDF-1.4 fake\n")
        archive = archive_export.run("woodcore-cli", "")
        assert "-rs" not in archive.name, archive.name
        names = set(zipfile.ZipFile(archive).namelist())
        assert here.rel(here.data_dir / "calculations.json") in names
        assert here.rel(here.stamps_dir / "rs.json") not in names, "a stamp reached the report's archive"
