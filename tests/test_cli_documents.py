"""`woodcore-cli export` for the three documents of a project (calc/cli.py, calc/stamps.py, the engineer's request of 30.09.2026), and the two commands beside it that learnt about them, `new --folders` and `migrate`.

What is held, and why each is worth a test rather than care:

⚠️ **Every compile goes through `documents.compile_args`**, `--root` among it. A new project is laid out in three documents, its sections importing `/commands.typ` from the project's own folder, and `woodcore-cli export` compiled it with no `--root` until work package 1.6 -- Typst then took the entry's folder for its root and the first `#import` failed, so the very first export of every new project failed at the compile. The first test below is that export.

⚠️ **A document whose Typst did not change since its PDF is neither compiled nor archived**, and this is held after a *full* export and not only after `--skip-data`: the export writes data/ again at every run, and it is the digest of a file and not its time that says it is unchanged (calc/stamps.py). A CU edit then compiles the CU alone -- a section of it, and its own journal, which the report must not read.

⚠️ **A report alone exports as it did**: one PDF where its layout puts it, one `<timestamp>.zip`, and the same «unchanged» on a second run. And a document it has not got is refused naming the migration rather than compiled against nothing.

Every project here is a copy in this process's own temp folder: a new one made by `project_template.create`, and a copy of the example project for the report alone. The command is run in this process (`cli.main`) inside `project.using(...)`, which puts back the session's project whatever `main` named -- a subprocess would cost an interpreter's start per run for nothing the in-process run does not already prove.
"""

import contextlib
import io
import json
import shutil
import time
from pathlib import Path

import conftest

import cli
import documents
import journal
import proc
import project
import project_template
import stamps


def _need_typst():
    if not conftest.have_typst():
        raise conftest.Skip("no Typst on this machine")


def _cli(here, *args):
    """`woodcore-cli <args> --project <here>` run in this process: (exit code, what it printed on stdout and stderr together). The session's current project is put back afterwards, `main` naming its own."""
    out = io.StringIO()
    with project.using(project.current()), contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = cli.main([*args, "--project", str(here.file)])
    return code, out.getvalue()


def _new(name, **kw):
    """A new project in three documents, as «Nouveau projet» makes one."""
    return project_template.create(conftest.tmpdir(name) / "Halle", "Halle", **kw)


def _mtimes(here):
    return {mode: here.document_pdf(mode).stat().st_mtime_ns if here.document_pdf(mode).is_file() else None
            for mode in here.modes}


def _zips(here, mode):
    return sorted(p.name for p in here.archives_dir.glob(f"*-{mode}*.zip"))


def _section(here, mode):
    """A section of document `mode`: the template's purpose.typ where it has one, else its first."""
    folder = here.document_dir(mode) / "Sections"
    named = folder / "purpose.typ"
    return named if named.is_file() else sorted(folder.glob("*.typ"))[0]


def _later():
    """A moment, so that a file written next has another modification time than the PDF compiled last -- which the stamps do not need, and which proves they do not: a time alone must change nothing."""
    time.sleep(0.05)


# --- three documents ---------------------------------------------------------------------------------

def test_export_compiles_each_document_once_and_then_only_what_changed():
    _need_typst()
    here = _new("cli_docs")
    assert here.has_modes

    # 1. the first export: three PDFs, each beside its own entry file, each stamped and archived apart
    code, said = _cli(here, "export", "--document", "all")
    assert code == 0, said
    for mode in here.modes:
        pdf = here.document_pdf(mode)
        assert pdf.is_file() and pdf.parent == here.document_dir(mode), f"{mode}: no PDF beside its entry file\n{said}"
        assert stamps.read(here, mode) is not None, f"{mode}: compiled and not stamped"
        assert _zips(here, mode), f"{mode}: compiled and not archived\n{said}"
        assert f"wrote {here.rel(pdf)}" in said, said
    first = _mtimes(here)
    archived = {mode: _zips(here, mode) for mode in here.modes}

    # 2. again, the full export included: nothing changed, so nothing is compiled and nothing archived
    _later()
    code, said = _cli(here, "export")
    assert code == 0, said
    assert said.count("is unchanged since its PDF") == 3, said
    assert _mtimes(here) == first, "an unchanged document was compiled again"
    assert {mode: _zips(here, mode) for mode in here.modes} == archived, "an unchanged document was archived again"

    # 3. a section of the convention d'utilisation edited: the CU alone
    _later()
    section = _section(here, "cu")
    section.write_text(section.read_text(encoding="utf-8") + "\nEin Satz mehr.\n", encoding="utf-8")
    code, said = _cli(here, "export", "--skip-data")
    assert code == 0, said
    now = _mtimes(here)
    assert now["cu"] != first["cu"], f"the CU was edited and not compiled\n{said}"
    assert (now["bp"], now["rs"]) == (first["bp"], first["rs"]), f"a document nobody touched was compiled\n{said}"
    assert len(_zips(here, "cu")) == len(archived["cu"]) + 1 and _zips(here, "rs") == archived["rs"]
    assert f"{here.rel(section)} changed" in said, said

    # 4. the CU's own journal: exported beside the report's, and read by the CU alone
    _later()
    journal.write_source(here.journal_file_for("cu"), {"schema_version": journal.SOURCE_SCHEMA_VERSION, "entries": [
        {"index": 1, "date": "2026-09-30", "name": "Max Muster", "initials": "MM", "label": "Erstausgabe"}]})
    before = _mtimes(here)
    code, said = _cli(here, "export")
    assert code == 0, said
    exported = json.loads((here.data_dir / journal.EXPORT_FILES["cu"]).read_text(encoding="utf-8"))
    assert [e["label"] for e in exported["entries"]] == ["Erstausgabe"], exported
    assert json.loads((here.data_dir / journal.EXPORT_FILE).read_text(encoding="utf-8"))["entries"] == [], "the CU's entry reached the report's journal"
    assert json.loads((here.data_dir / journal.EXPORT_FILES["bp"]).read_text(encoding="utf-8"))["entries"] == []
    now = _mtimes(here)
    assert now["cu"] != before["cu"], f"the CU's journal changed and the CU was not compiled\n{said}"
    assert (now["bp"], now["rs"]) == (before["bp"], before["rs"]), f"another document's journal compiled the report or the BP\n{said}"

    # 5. --force: every document, changed or not
    _later()
    before = _mtimes(here)
    code, said = _cli(here, "export", "--skip-data", "--force")
    assert code == 0, said
    now = _mtimes(here)
    assert all(now[mode] != before[mode] for mode in here.modes), f"--force left a document as it was\n{said}"
    assert said.count("(--force)") == 3, said

    # 6. one document named: the others are not even asked about
    code, said = _cli(here, "export", "--skip-data", "--document", "bp")
    assert code == 0 and "bp (Basis of design) is unchanged" in said and "cu (" not in said and "rs (" not in said, said

    # 7. --all-levels: the report's variants, written whenever they are asked for and stamped never
    record = stamps.stamp_file(here, "rs").read_bytes()
    code, said = _cli(here, "export", "--skip-data", "--all-levels")
    assert code == 0, said
    for level in cli.LEVELS:
        assert (here.generated_dir / "out" / f"report-{level}.pdf").is_file(), f"report-{level}.pdf\n{said}"
    assert stamps.stamp_file(here, "rs").read_bytes() == record, "a variant of the report was stamped as the report"
    assert said.count("is unchanged since its PDF") == 3, said


def test_a_document_that_does_not_compile_fails_the_export_and_leaves_the_others_compiled():
    _need_typst()
    here = _new("cli_docs_broken")
    entry = here.document_typ("bp")
    entry.write_text(entry.read_text(encoding="utf-8") + '\n#panic("deliberate, from tests/test_cli_documents.py")\n', encoding="utf-8")
    code, said = _cli(here, "export", "--skip-data")
    assert code == 1, said
    assert "bp (Basis of design) does not compile" in said and "deliberate" in said, said
    assert here.document_pdf("cu").is_file() and here.document_pdf("rs").is_file(), "one document failing stopped the others"
    assert not here.document_pdf("bp").is_file() and stamps.read(here, "bp") is None, "a document that failed was stamped"
    assert not _zips(here, "bp"), "a document that failed was archived"


def test_every_compile_names_the_typst_root():
    """The defect this package was written for: a compile of a document of three with no `--root` cannot find `/commands.typ`. What `compile_report` starts is `documents.compile_args`' line, the root stated, the entry and the target last."""
    here = _new("cli_docs_root")
    started = []
    saved = proc.subprocess.run   # the one place a child process is started (calc/proc.py), which calls the module's `run`
    proc.subprocess.run = lambda args, **kwargs: started.append(args) or __import__("types").SimpleNamespace(returncode=0, stdout="", stderr="")
    try:
        for mode in here.modes:
            deps = stamps.deps_file(here, mode)
            assert cli.compile_report(here, ["--input", "level=2"], here.document_pdf(mode), mode=mode, deps=deps) is None
    finally:
        proc.subprocess.run = saved
    for mode, args in zip(here.modes, started):
        assert args[1:] == documents.compile_args(here, mode, ["--input", "level=2"], deps=stamps.deps_file(here, mode)), args
        assert args[args.index("--root") + 1] == str(here.root), args
        assert args[-2:] == [str(here.document_typ(mode)), str(here.document_pdf(mode))], args


# --- a report alone ------------------------------------------------------------------------------------

def _legacy_copy(name):
    """The example project laid out as one report -- as it was committed before it was itself migrated into three documents, rebuilt by tests/fixtures/legacy_example.py -- its engine synced, with no archive and no stamp of its own yet."""
    from fixtures import legacy_example
    here = legacy_example.build(conftest.tmpdir(name) / "project", conftest.SAMPLE)
    project.sync_engine(here)
    return here


def test_a_report_alone_exports_as_it_did():
    """One PDF where its layout puts it, one `<timestamp>.zip` beside `<timestamp>-<its PDF>`, the compile's root the report's folder -- the folder Typst takes when it is given none -- and a second export that compiles nothing. The example carries no workbook, so it is compiled against the export it has (`--skip-data`), as packaging/build.py compiles it."""
    _need_typst()
    here = _legacy_copy("cli_docs_legacy")
    assert here.modes == ("rs",) and cli.requested_documents(here) == ("rs",)
    assert documents.compile_args(here, "rs")[2] == str(here.report_typ.parent), "a report alone compiles from its own folder"
    code, said = _cli(here, "export", "--skip-data")
    assert code == 0, said
    assert here.report_pdf.is_file(), said
    zips = sorted(p.name for p in here.archives_dir.glob("*.zip"))
    assert len(zips) == 1 and "-rs" not in zips[0], f"a report alone's archive is <timestamp>.zip as it always was: {zips}"
    assert (here.archives_dir / f"{Path(zips[0]).stem}-{here.report_pdf.name}").is_file(), "the flat copy of the PDF is not beside the zip"
    assert stamps.read(here, "rs") is not None
    written = here.report_pdf.stat().st_mtime_ns
    code, said = _cli(here, "export", "--skip-data")
    assert code == 0 and "rs (Statical report) is unchanged since its PDF" in said, said
    assert here.report_pdf.stat().st_mtime_ns == written and len(list(here.archives_dir.glob("*.zip"))) == 1


def test_a_document_a_report_alone_has_not_is_refused_naming_the_migration():
    here = _legacy_copy("cli_docs_legacy_cu")
    code, said = _cli(here, "export", "--skip-data", "--document", "cu")
    assert code == 1 and "migrate" in said, said
    assert "wrote" not in said, said


# --- new --folders, and migrate -----------------------------------------------------------------------

def test_new_takes_the_three_folders():
    base = conftest.tmpdir("cli_docs_new")
    out = io.StringIO()
    with project.using(project.current()), contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = cli.main(["new", str(base / "Eins"), "--folders", "A_Nutzung", "B_Basis", "C_Statik"])
        refused = cli.main(["new", str(base / "Zwei"), "--folders", "A", "B", "C", "--report-folder", "D"])
    assert code == 0, out.getvalue()
    here = project.Project.load(base / "Eins" / "Eins.woodcore")
    assert [here.document_dir(mode).name for mode in project.MODES] == ["A_Nutzung", "B_Basis", "C_Statik"], here.layout
    assert refused == 1, out.getvalue()
    assert not (base / "Zwei").exists() or not any((base / "Zwei").iterdir()), "a refused creation left something behind"
    new_parser = cli.parser()._subparsers._group_actions[0].choices["new"]
    helps = {action.dest: action.help or "" for action in new_parser._actions}
    assert "folders" in helps and "CU BP RS" in helps["folders"], helps
    assert "3_Statischer Bericht" in helps["report_folder"], helps["report_folder"]
    assert "Static report" not in helps["report_folder"], "the --report-folder help still names v0.100's English folder"


def test_migrate_is_the_migration_s_own_command():
    """`woodcore-cli migrate ...` hands its arguments on as they were typed: calc/project_migrate.py reads them itself, so the two cannot spell them two ways."""
    import project_migrate
    handed = []
    saved = project_migrate.command
    project_migrate.command = lambda argv=None: handed.append(argv) or 0
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            assert cli.main(["migrate", "--dry-run", "--project", "X.woodcore", "--names", "A", "B", "C"]) == 0
    finally:
        project_migrate.command = saved
    assert handed == [["--dry-run", "--project", "X.woodcore", "--names", "A", "B", "C"]], handed
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        assert cli.main(["migrate", "--help"]) == 0
    assert "--rollback" in out.getvalue() and "--names" in out.getvalue(), out.getvalue()
