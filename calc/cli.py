"""woodcore-cli: the report built from a terminal, without the window (docs/conventions/build-and-release.md §12, v0.82).

    python calc/cli.py export      [--project F] [--document cu|bp|rs|all] [--force] [--level N | --uniform N] [--lang de|fr|en] [--all-levels] [--skip-data | --data-only] [--update-engine]
    python calc/cli.py check       [--project F]
    python calc/cli.py run-script  <script.py> --report <file> [--project P]
    python calc/cli.py sync-engine [--project F] [--update]
    python calc/cli.py sync        status|share|import|move [--document cu|bp|rs] ...   the sections the documents share (calc/cli_sync.py, v0.117)
    python calc/cli.py new         <folder> --name N [--template T] [--style S] [--language de|fr|en] [--folders CU BP RS] [--report-folder F] [--number ...] [--client ...] [--address ...] [--company ...] [--author ...] [--checker ...]
    python calc/cli.py migrate     [--project F] [--language de|fr|en] [--names CU BP RS] [--dry-run] [--skip-data] [--update-engine] [--lock-owner PID]
    python calc/cli.py migrate     --rollback <archives>/migration-<timestamp>

`woodcore-cli.bat` beside the program runs the same, and so does `woodcore-cli.exe` beside an installed Woodcore (v0.83). It takes the place of `build.ps1` and the `Makefile`, which named the paths of the one project the code used to sit in: every command here names a project -- `--project <file>.woodcore`, else `WOODCORE_PROJECT`'s, else the one beside the code's checkout (calc/project.py).

**export** does what *Exporter PDF* does in Woodcore's window, in the same order and for the same reason: the export first, then `typst compile`, and the compilation only if the export passed -- Typst is never compiled against unvalidated data (section 12); then the archive. `--level` forces the base level for this run, `--uniform` every call's level, `--lang` the engine's language -- the three `--input` flags spelt once, here (`input_args`), and read by the window too. With none of them no `--input` is passed, and the report comes out as written. `--all-levels` also writes the three uniform variants into the project's generated folder, `out/report-1|2|3.pdf`. `--update-engine` replaces a copy of the engine another version wrote or someone edited by hand (project.sync_engine). `--data-only` stops after the export, which is what *Import données* runs in Woodcore's window (v0.83) -- the one route from the window to the export, from the sources and from the installed program alike.

A project laid out in three documents compiles **each of them into its own PDF**, beside its entry file, and archives each apart (the engineer's request of 30.09.2026): `--document cu|bp|rs` names one, `all` -- the default -- every one the project has, which for a project laid out as one report is the report alone. **A document whose Typst did not change since its PDF is neither compiled nor archived** (calc/stamps.py): the command says so and why, and `--force` compiles it all the same. Every compile goes through `documents.compile_args`, the one spelling of the command line, `--root` on the Typst root among it -- the project's own folder in three documents, which a compile without it could not find its `/commands.typ` from. `--all-levels`' variants are the report's, and are not stamped.

**migrate** moves a project laid out as one report into three documents, or undoes a migration (calc/project_migrate.py's own command, its arguments handed on as they were typed).

**check** runs the whole export and writes nothing: every workbook read, every source checked, every record validated.

**sync-engine** copies the program's engine into the project, as an export does.

**new** makes an empty folder a new project (calc/project_template.py, v0.83): the report and its sections, the folders Woodcore's window saves into, an empty list of positions (Woodcore-Datei/positions.json, which Woodcore's Positions tab fills, v0.114), and the `.woodcore` file. Since 06.10.2026 a project is made from a **form** and three **content templates**: `--form` names the look of the three documents (`neutral`, `compact`, `bfh`, or `<place>:<id>`: calc/forms.py's `Template/`, title.typ and a config.typ that keeps the language) -- the settings' default one (forms.default_ref), else neutral, where none is given --, and `--content-cu`, `--content-bp` and `--content-rs` name the content template of each document (`builtin:cu/standard`, `user:rs/<folder>` …: calc/doc_templates.py), the builtin standard ones where none is given. `--style` is the older name of `--form`. `--template` is **legacy**: it names a project template of the engineer's or the office's saved before forms (`Standard`, a name or a folder, or `<place>:<folder>`), whose own report, config.typ and title page then make the project -- a form only where `--form` asks for one --, else the settings' default project template, else Standard; the languages and the company, author and checker are the template's, else the settings' defaults, each person written over by its flag. The project is laid out in three documents, their folders named in its language unless `--folders` names the three (in the order CU BP RS) or `--report-folder` the report's alone; the project keeps its language whichever form is chosen, and an unknown form is refused naming the valid ones before anything is made. It names no existing project, so it is the one command that takes none.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "tools"))

import project  # noqa: E402
import proc  # noqa: E402  -- a child process starts without a console window flashing open
import validation  # noqa: E402
import engine  # noqa: E402

LEVELS = (1, 2, 3)
LANGUAGES = ("de", "fr", "en")


def input_args(kind=None, n=None, lang=None):
    """The `--input` flags Typst is given: `kind` "level" (the base, per-call overrides still apply) or "uniform" (every call at `n`), and the engine's language. None of them where the document's own base level and language govern, which is what makes the report come out «as written» (docs/typst/report-engine.md §4, docs/typst/language.md §4bis). The one spelling: the PDF menu of Woodcore's window builds its flags through it too."""
    args = []
    if kind is not None:
        args += ["--input", f"{kind}={int(n)}"]
    if lang is not None:
        args += ["--input", f"lang={lang}"]
    return args


def compile_report(here, flags, target, mode="rs", deps=None):
    """`typst compile` of document `mode` of project `here` -- the report by default -- into `target`, by the one spelling of a compile's command line (documents.compile_args): `--root` on the Typst root, the project's own folder in three documents and the report's folder for a report alone, and `--deps` into `deps` where it names the file Typst writes what it read into. Returns Typst's message, or None where it worked."""
    import documents
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    # started in the Typst root, as the window starts it: the deps file's relative paths are from there (calc/stamps.py _read_deps)
    result = proc.run([project.typst_executable(), *documents.compile_args(here, mode, flags, target=target, deps=deps)],
                            capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=here.typst_root)
    if result.returncode != 0:
        return (result.stderr or result.stdout).strip() or f"typst exited {result.returncode}"
    return None


# What `--document` takes: one of the three documents, or all of the project's -- the three for a project laid out in three documents, the report for one laid out as a report alone, whose only document it is.
ALL_DOCUMENTS = "all"


def requested_documents(here, which=None):
    """The documents `--document` names, in the project's order (project.MODES): every one of the project's for `all` or None, else the one named -- a ProjectError where the project has no such document, a report alone having none but the report (Project.document_typ says so, naming the migration)."""
    if which in (None, ALL_DOCUMENTS):
        return tuple(here.modes)
    here.document_typ(which)
    return (which,)


def document_label(mode):
    """How the command line names a document: its code and its English name, `cu (Service criteria agreement)` -- in English, like every message of the pipeline (the window writes its own)."""
    import documents
    return f"{mode} ({documents.MODE_NAMES['en'][mode]})"


def compile_document(here, mode, flags, force=False, route="woodcore-cli", log=print, warn=None):
    """One document of an export, as `woodcore-cli export` builds each: asked first whether its Typst changed since its PDF (calc/stamps.py, the engineer's rule «export a document only if its Typst changed since its PDF»), then compiled with `--deps`, stamped and archived -- and neither compiled nor archived where nothing changed and `force` does not ask for it all the same. Returns (status, message): "unchanged", "compiled" or "failed", the message being what was printed, or Typst's own for a failure.

    The window's *Exporter PDF* runs the same steps with a QProcess of its own (docs/ui/window.md §10quater): `stamps.changed(here, mode, flags)`, then `documents.compile_args(here, mode, flags, deps=stamps.deps_file(here, mode))`, then on success `stamps.record(here, mode, flags, deps, here.document_pdf(mode))` and `archive_export.run("gui", detail, mode=mode)`.
    """
    import stamps
    warn = warn or (lambda text: print(text, file=sys.stderr))
    changed, why = stamps.changed(here, mode, flags)
    pdf = here.document_pdf(mode)
    if not changed and not force:
        message = (f"woodcore-cli: {document_label(mode)} is unchanged since its PDF ({here.rel(pdf)}) -- "
                   f"nothing compiled, nothing archived; --force compiles it all the same")
        log(message)
        return "unchanged", message
    deps = stamps.deps_file(here, mode)
    error = compile_report(here, flags, pdf, mode=mode, deps=deps)
    if error:
        warn(f"woodcore-cli: {document_label(mode)} does not compile:\n{error}")
        return "failed", error
    reason = "--force" if not changed else str(why)
    message = f"woodcore-cli: wrote {here.rel(pdf)} ({reason})"
    log(message)
    try:
        stamps.record(here, mode, flags, deps, pdf)
    except OSError as exc:   # a document not stamped is one compiled again next time: slow, never wrong
        warn(f"woodcore-cli: {document_label(mode)} was compiled and not stamped ({exc}) -- it will be compiled again")
    import archive_export
    try:
        archive_export.run(route, " ".join(flags), mode=mode)
    except Exception as exc:  # broad: a convenience, never a failed build -- said as a warning
        warn(f"archive_export: skipped ({exc})")
    return "compiled", message


def export(args):
    import export_all
    here = project.current()
    try:
        documents_asked = requested_documents(here, args.document)
    except project.ProjectError as exc:
        print(f"woodcore-cli: {exc}", file=sys.stderr)
        return 1
    if not args.skip_data:
        try:
            export_all.run(update_engine=args.update_engine)
        except (validation.ValidationError, engine.EngineError) as exc:
            print(f"export failed: {exc}", file=sys.stderr)
            return 1
    if args.data_only:
        return 0
    kind, n = ("uniform", args.uniform) if args.uniform else (("level", args.level) if args.level else (None, None))
    flags = input_args(kind, n, args.lang)
    outcome = {mode: compile_document(here, mode, flags, force=args.force)[0] for mode in documents_asked}
    failed = [mode for mode, status in outcome.items() if status == "failed"]
    # The three uniform variants are the report's alone, and a record of none of them is kept (calc/stamps.py): they are compiled whenever they are asked for, the report's own PDF being stamped and theirs not.
    if args.all_levels and "rs" in outcome and "rs" not in failed:
        for level in LEVELS:
            target = here.generated_dir / "out" / f"report-{level}.pdf"
            error = compile_report(here, input_args("uniform", level, args.lang), target)
            if error:
                print(f"woodcore-cli: report-{level}.pdf does not compile:\n{error}", file=sys.stderr)
                return 1
            print(f"woodcore-cli: wrote {here.rel(target)}")
    elif args.all_levels and "rs" not in outcome:
        print("woodcore-cli: --all-levels writes the report's variants, and the report was not asked for -- none written", file=sys.stderr)
    return 1 if failed else 0


def check(_args):
    import export_all
    import cli_sync
    try:
        export_all.run(dry=True)
    except (validation.ValidationError, engine.EngineError) as exc:
        print(f"check failed: {exc}", file=sys.stderr)
        return 1
    # the records of what the three documents share (v0.117, issue #33): one that does not read stops the check naming its file and field, a document out of step is a warning -- read, never settled
    if cli_sync.check(project.current()):
        return 1
    print(f"woodcore-cli: {project.current().name} exports without a defect -- nothing written")
    return 0


def sync_engine(args):
    try:
        written = project.sync_engine(project.current(), update=args.update)
    except project.ProjectError as exc:
        print(f"sync-engine: {exc}", file=sys.stderr)
        return 1
    here = project.current()
    print(f"woodcore-cli: engine {'written: ' + ', '.join(written) if written else 'already current'} in {here.rel(here.generated_dir)}/")
    return 0


def new(args):
    import project_template
    import templates
    import usersettings
    settings = usersettings.read()
    try:
        template = templates.find(args.template, settings) if args.template else templates.default_template(settings)
        document, report = templates.languages_for(template, settings)
        # One language sets both the document's and the engine's (the engineer's answer C9, v0.100), and the report's folder is offered in it.
        if args.language:
            document = report = args.language
        details = {key: value for key, value in templates.people_for(template, settings).items() if value}
        details.update({key: getattr(args, key) for key in project.DETAILS if getattr(args, key)})
        # The three folders are what `--folders` names, the report's what `--report-folder` names, and what neither names is what the template offers for the language (templates.folders_offered, which project_template.create asks itself).
        here = project_template.create(args.folder, args.name or Path(args.folder).name, template=template,
                                       document_language=document, report_language=report,
                                       report_folder=args.report_folder or None, folders=args.folders or None,
                                       form=args.form or None, style=args.style or None,
                                       document_templates={mode: ref for mode, ref in (("cu", args.content_cu), ("bp", args.content_bp), ("rs", args.content_rs)) if ref} or None,
                                       **details)
    except project.ProjectError as exc:
        print(f"woodcore-cli: {exc}", file=sys.stderr)
        return 1
    print(f"woodcore-cli: created {here.file}")
    print("  next: copy the office's Belastungsannahmen workbook into the folder, enter the positions in Woodcore's Positions tab, "
          "then woodcore-cli export --project \"%s\"" % here.file)
    return 0


def migrate(argv):
    """`woodcore-cli migrate ...`: a project laid out as one report moved into three documents, or a migration undone (`--rollback`) -- calc/project_migrate.py's own command, handed the arguments as they were typed, so that it reads them itself and the two cannot come to spell them two ways. It names its project as every other command does (`--project`, else WOODCORE_PROJECT's, else the one beside the checkout)."""
    try:
        import project_migrate
    except ImportError as exc:
        print(f"woodcore-cli: the migration is not available in this Woodcore ({exc})", file=sys.stderr)
        return 1
    return project_migrate.command(argv)


def convert(args):
    """`woodcore-cli convert <folder>`: writes a `.woodcore` into a folder laid out before Woodcore (v0.82) -- `000-TypstRapport/` with `000-Python/` beside it, or an archive of one -- naming its parts where they stand and moving nothing (project_template.convert). The start page offered it as «Convertir un ancien dossier» from v0.83 until the engineer took the button away (v0.113), every project he has being laid out the new way: the function stays reachable here for the old folder that turns up all the same."""
    import project_template
    try:
        here = project_template.convert(args.folder, name=args.name)
    except (project.ProjectError, OSError) as exc:
        print(f"woodcore-cli: {exc}", file=sys.stderr)
        return 1
    print(f"woodcore-cli: wrote {here.file}; nothing was moved -- the first export asks before replacing the engine the folder carries")
    return 0


def run_script(args):
    """`woodcore-cli run-script <source> --report <file>`: runs one script of the project **in this process** and writes what it did.

    It is the child `calc/domains/script.py` spawns, and it is a command of its own rather than a private entry point because that is what lets an installed Woodcore -- which has no `python.exe` -- relaunch itself to run a script (project.cli_command). Run by hand it is also the way to see a script fail with its traceback on the terminal.
    """
    from domains import script_runner
    return script_runner.main([args.source, "--report", args.report, *(["--results-only"] if args.results_only else [])])


def parser():
    ap = argparse.ArgumentParser(prog="woodcore-cli", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)
    e = sub.add_parser("export", help="the export, then the PDF, then the archive")
    levels = e.add_mutually_exclusive_group()
    levels.add_argument("--level", type=int, choices=LEVELS, help="the base level for this run; per-call levels still apply")
    levels.add_argument("--uniform", type=int, choices=LEVELS, help="every call at this level, per-call levels ignored")
    e.add_argument("--lang", choices=LANGUAGES, help="the language the engine prints in")
    e.add_argument("--all-levels", action="store_true", help="also out/report-1|2|3.pdf, each one level throughout")
    data = e.add_mutually_exclusive_group()
    data.add_argument("--skip-data", action="store_true", help="compile against the export already there")
    data.add_argument("--data-only", action="store_true", help="the export alone: no PDF, no archive -- what «Import données» runs in Woodcore's window")
    e.add_argument("--update-engine", action="store_true", help="replace a copy of the engine another version wrote, or one edited by hand")
    e.add_argument("--document", choices=(*project.MODES, ALL_DOCUMENTS), default=ALL_DOCUMENTS,
                   help="the document to compile: cu, bp, rs, or all of the project's (the default) -- the report alone for a project laid out as one report")
    e.add_argument("--force", action="store_true", help="compile and archive a document even where its Typst did not change since its PDF")
    sub.add_parser("check", help="the whole export, writing nothing")
    # its own arguments, read by calc/project_migrate.py (main() hands them on before this parser sees them): listed here so that `woodcore-cli --help` names it
    sub.add_parser("migrate", help="move a project laid out as one report into three documents -- `woodcore-cli migrate --help` for its arguments", add_help=False)
    r = sub.add_parser("run-script", help="run one script of the project in this process -- what Woodcore's Python tab and the export spawn")
    r.add_argument("source", help="the script: Woodcore-Datei/scripts/<id>.py")
    r.add_argument("--report", required=True, help="the JSON file the run's results, variables and reason are written to")
    r.add_argument("--results-only", action="store_true", help="leave the variables out: what the export asks for, having no use for a local")
    import cli_sync
    cli_sync.add_parser(sub)
    s = sub.add_parser("sync-engine", help="copy the program's engine into the project")
    s.add_argument("--update", action="store_true", help="replace a copy another version wrote, or one edited by hand")
    for p in (e, sub.choices["check"], s, r):
        p.add_argument("--project", help="the project's .woodcore file; else WOODCORE_PROJECT's, else the one beside the checkout")
    n = sub.add_parser("new", help="make an empty folder a new project")
    n.add_argument("folder", help="the project's folder: empty, or not there yet")
    n.add_argument("--name", help="the project's name; the folder's name if left out")
    n.add_argument("--form", help="the look of the three documents -- calc/forms.py's Template/, title.typ and config.typ --: neutral, compact, bfh, or <place>:<id>; the settings' default form, else neutral, if left out")
    n.add_argument("--style", help="the older name of --form")
    n.add_argument("--content-cu", metavar="REF", help="the content template of the convention d'utilisation: builtin:cu/standard, user:cu/<folder>, office:cu/<folder>; builtin:cu/standard if left out")
    n.add_argument("--content-bp", metavar="REF", help="the content template of the base de projet: builtin:bp/standard, user:bp/<folder>, office:bp/<folder>; builtin:bp/standard if left out")
    n.add_argument("--content-rs", metavar="REF", help="the content template of the report: builtin:rs/standard, user:rs/<folder>, office:rs/<folder>; builtin:rs/standard if left out")
    n.add_argument("--template", help="LEGACY: a project template saved before forms -- Standard, a template's name or folder, or <place>:<folder>; its own report, config.typ and title page make the project; the settings' default one, else Standard, if left out")
    n.add_argument("--language", choices=("de", "fr", "en"), help="the language the report is written in -- the document's and the engine's both (v0.100); the template's, else the settings' default, if left out")
    n.add_argument("--folders", nargs=3, metavar=("CU", "BP", "RS"),
                   help="the three documents' folders, in the order CU BP RS; the language's own -- 1_Nutzungsvereinbarung 2_Projektbasis \"3_Statischer Bericht\" in German -- if left out")
    n.add_argument("--report-folder", default="", help="the name of the report's folder alone, the third of --folders; the language's own -- 3_Statischer Bericht, 3_Rapport de statique, 3_Statical report -- if left out")
    for key in project.DETAILS:
        n.add_argument("--" + key, default="", help=f"the project's {key}, for the title page")
    c = sub.add_parser("convert", help="write a .woodcore into a folder laid out before Woodcore (v0.82), moving nothing")
    c.add_argument("folder", help="the old folder: 000-TypstRapport/ and 000-Python/, or an archive of one")
    c.add_argument("--name", help="the project's name; the folder's name if left out")
    return ap


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["migrate"]:
        return migrate(argv[1:])
    args = parser().parse_args(argv)
    if args.command == "new":
        return new(args)
    if args.command == "convert":
        return convert(args)
    try:
        if args.project:
            project.use(args.project)
        project.current()
    except project.ProjectError as exc:
        print(f"woodcore-cli: {exc}", file=sys.stderr)
        return 1
    if args.command == "sync":
        import cli_sync
        return cli_sync.run(args)
    return {"export": export, "check": check,
            "sync-engine": sync_engine, "run-script": run_script}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
