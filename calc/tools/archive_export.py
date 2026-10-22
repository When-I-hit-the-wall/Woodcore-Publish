"""Archives every successful PDF export into the project's archives folder, as one zip (docs/conventions/build-and-release.md §12).

    python calc/tools/archive_export.py --route woodcore-cli [--detail "--input level=2"] [--project <file>.woodcore] [--mode cu|bp|rs]

Called right after a successful `typst compile` by every route that builds the deliverable -- the command line (`woodcore-cli export`) and the window's *Exporter PDF* -- the one place this is spelled out. Two things land in the project's archives folder (`_Archiv/` by default) per call: a flat copy of the PDF, `<timestamp>-Statischer Rapport.pdf`, to look at, and `<timestamp>.zip`, holding everything needed to reopen Woodcore on the exact state that produced that PDF: the project's `.woodcore` file, its report folder -- the report, its sections and pictures, the export and the engine copied beside it -- and the sources drawn in the window, with `archive-info.json` naming the route, the flags and what produced the export (data/project.json).

**One zip, since v0.82.** Until then the snapshot was a folder of hundreds of files, which NextCloud synced one by one and which reached Windows' 260-character limit on paths a few folders deep -- where Explorer cannot delete a file and Excel refuses to open one. A zip is one file, its members' names carry no path of the machine, and it is a third the size.

The workbooks are not in it: they are the engineer's, they live beside the report and not in it, and data/project.json records the SHA-256 of every one the export read -- so a checker can tell whether the workbook in hand is the one, which is what traceability asks of them. Left out as well, wherever they occur: the archives folder itself, the PDF itself (written in the report's folder since v0.87, and already copied beside the zip), and the debris a build or a test leaves (`__pycache__/`, `.render-cache/`, `.preview/`, `.probe/`, a Tinymist PDF in Sections/). For a project still laid out as until v0.81, whose report folder holds the program, the program's frozen examples, build output and test debris are left out too.

Archiving is a convenience, never part of the validated pipeline (section 3.6): `run()` raises on failure, but `main()` catches everything and always exits 0, so a full disk or a slow sync never turns a successful export into a failed build. The window calls `run()` directly, so it can put the one message that matters on its own status line rather than losing it to a console it does not have.

**A project laid out in three documents archives each document apart** (the engineer's request of 30.09.2026): `run(route, detail, mode=...)` archives the one document just compiled, as `<timestamp>-<mode>.zip` beside `<timestamp>-<mode>-<its PDF>` -- a report alone keeps `<timestamp>.zip`, holding what it always held but the stamps its export's folder now carries. What such a zip holds is chosen by name and never by walking the Typst root, which is the whole project folder there and would sweep the other two documents, the workbooks, the architect's plans and the archives themselves into it (`members_of_document`): the `.woodcore`, that document's own folder, what the three share at the top -- config.typ, commands.typ, references.bib, title.typ, the form's `Template/`, the export's folder less its out/ and its stamps/, and Images/ --, the sources drawn in the window and the three journals.
"""

import argparse
import json
import sys
import zipfile
from datetime import datetime
from pathlib import Path

# calc/ on the path: this module is also run on its own, by the command line.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import project  # noqa: E402  -- every path below is the current project's (calc/project.py, v0.81)

# Which route is calling, as the manifest names it: the command line, or the window's *Exporter PDF* (`gui`). The window's route was `katalog` until v0.96, and a caller of an older checkout that still says so is accepted and recorded as `gui`.
ROUTES = ("woodcore-cli", "gui")
LEGACY_ROUTES = {"katalog": "gui"}

# Skipped wherever they occur, at any depth: debris, never project state.
EXCLUDED_NAMES = {"__pycache__", ".render-cache", ".preview", ".probe"}

# Skipped only at these exact locations, relative to the report's folder: what a report folder laid out as until v0.81 held of the program -- a name-only rule would be wrong here, "out" and "examples" being ordinary words a project could otherwise have a reason to use elsewhere. The archives' own folder is skipped wherever the project puts it (`_excluded`).
EXCLUDED_PATHS = {
    Path("000-ExternalFiles"),
    Path("000-Python/examples"),
    Path("000-Python/out"),
    Path("000-Python/tests/.tmp"),
}


def _timestamp():
    return datetime.now().strftime("%y%m%d-%Hh%M")


def _excluded(typst_root):
    """EXCLUDED_PATHS, and the project's archives folder where it lies inside the report's folder: never nest an archive inside itself -- and the PDF itself where it lies there, which it does by default since v0.87 (project.DEFAULT_LAYOUT): its copy already stands beside the zip, and a zip holds the state that produced the PDF, not the PDF a second time."""
    excluded = set(EXCLUDED_PATHS)
    here = project.current()
    # the stamps too (calc/stamps.py): what a compile read, written after it, which says nothing of the state an archive reopens -- its PDF is not in the zip, so a stamp restored with it would only say «compile again»
    for path in (here.archives_dir, here.report_pdf, here.stamps_dir):
        try:
            excluded.add(path.relative_to(typst_root))
        except ValueError:
            pass
    return excluded


def _kept(path, typst_root, excluded):
    """Whether `path`, a file under the report's folder, goes into the archive."""
    rel = path.relative_to(typst_root)
    if any(part in EXCLUDED_NAMES or part.startswith((".project-", ".settings-")) for part in rel.parts):
        return False  # debris, and the test suite's own copies of the example project in a legacy layout
    if any(rel == ex or ex in rel.parents for ex in excluded):
        return False
    if rel.parts[:1] == ("Sections",) and path.suffix.lower() == ".pdf":
        return False  # a Tinymist stray, kept out of Git for the same reason (.gitignore)
    return True


def members(here):
    """(file, name in the zip) for everything an archive of a report alone holds, the names relative to the project's folder: the report's whole folder, which is its Typst root, and the sources beside it."""
    typst_root = here.typst_root
    excluded = _excluded(typst_root)
    chosen = {here.file: here.file.name}
    for path in sorted(typst_root.rglob("*")):
        if path.is_file() and _kept(path, typst_root, excluded):
            chosen[path] = here.rel(path)
    if not project._is_within(here.sources_dir, typst_root):
        for folder in project.SOURCE_FOLDERS:
            for path in sorted((here.sources_dir / folder).rglob("*")):
                if path.is_file() and not any(part in EXCLUDED_NAMES for part in path.parts):
                    chosen[path] = here.rel(path)
        # The revision journal, one file at the top of the sources rather than a folder of them (calc/journal.py, v0.99): an archive holds everything Woodcore needs to reopen the project on exactly that state, and the journal is what the report's own page prints.
        if here.journal_file.is_file():
            chosen[here.journal_file] = here.rel(here.journal_file)
        # The project's positions, Woodcore's own since v0.114 (calc/positions_store.py): one file at the top of the sources too, and what every position of the report comes from.
        positions = here.sources_dir / POSITIONS_FILE
        if positions.is_file():
            chosen[positions] = here.rel(positions)
        # The order of the window's lists and the folders of the «Formules» tab (calc/list_order.py, issue #15): the engineer's own, beside the sources
        if here.lists_file.is_file():
            chosen[here.lists_file] = here.rel(here.lists_file)
    return sorted(chosen.items(), key=lambda item: item[1])


# The project's positions, a file at the top of the sources (calc/positions_store.py's FILE, v0.114) -- named here rather than imported, this module reading no positions.
POSITIONS_FILE = "positions.json"

# The export's own folders an archive of a document leaves out: out/, the uniform variants a build writes, and stamps/, what each compile read -- neither is the state an archive reopens.
GENERATED_LEFT_OUT = ("out", project.STAMPS_FOLDER)


def _files(folder, skipped=()):
    """Every file under `folder`, the debris of EXCLUDED_NAMES and the folders `skipped` left out -- nothing where the folder is not there."""
    if not folder.is_dir():
        return []
    skipped = [Path(path).resolve() for path in skipped]
    found = []
    for path in sorted(folder.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(folder)
        if any(part in EXCLUDED_NAMES or part.startswith((".project-", ".settings-")) for part in rel.parts):
            continue
        if any(project._is_within(path, other) for other in skipped):
            continue
        found.append(path)
    return found


def members_of_document(here, mode):
    """(file, name in the zip) for everything the archive of document `mode` of a project laid out in three documents holds, the names relative to the project's folder -- **chosen by name, never by walking the Typst root**, which is the whole project folder here and would take the other documents, the workbooks, the architect's plans and the archives themselves along.

    The `.woodcore`; the document's own folder -- its entry file, its structure.json, its Sections/ -- less its PDF, whose copy stands beside the zip, and a Tinymist stray in Sections/; what the three documents share at the top: config.typ, commands.typ, references.bib and title.typ, the form's `Template/`, the export's folder less out/ and stamps/ (GENERATED_LEFT_OUT), the pictures; laid out by folders, the domains' folders, the drawing tabs' (their imports and their exports) and Appendix/; the sources drawn in the window; and the three journals, each document printing its own. Not the other documents' folders, not the workbooks -- data/project.json records their hashes, as for a report alone --, not `.vscode/`.
    """
    generated = here.generated_dir
    folder = here.document_dir(mode)
    # what lies in the document's folder and is not the document: the archives and the export, where a layout put them there, and another document's folder nested in it
    left_out = [here.archives_dir, generated] + [
        here.document_dir(other) for other in here.modes
        if other != mode and here.document_dir(other) != folder and project._is_within(here.document_dir(other), folder)]
    chosen = {here.file: here.file.name}
    pdf = here.document_pdf(mode).resolve()
    for path in _files(folder, skipped=left_out):
        rel = path.relative_to(folder)
        if path.resolve() == pdf or (rel.parts[:1] == ("Sections",) and path.suffix.lower() == ".pdf"):
            continue
        chosen[path] = here.rel(path)
    for path in (here.config_typ, here.commands_typ, here.references_bib, here.title_typ):
        if path.is_file():
            chosen[path] = here.rel(path)
    for path in _files(here.template_dir, skipped=[here.archives_dir]):   # the form the documents are set in (calc/forms.py): template.typ, form.json, its assets
        chosen[path] = here.rel(path)
    # the export, less what lies inside it and is not the export: the sources and the archives of a project laid out by folders, which 000-Woodcore/ holds too -- taken in, every archive would carry every earlier one (spec 2026-10-15 ARCH-RISK-A01)
    for path in _files(generated, skipped=[generated / name for name in GENERATED_LEFT_OUT] + here.generated_excludes()):
        chosen[path] = here.rel(path)
    # the domains every document may print: the engineer's own (Domains/, Formules/ before 0.119, v0.117) and, laid out by folders, one folder per kind of domain (issue #64) -- a domain archived left out, as every archive is (issue #15)
    shared = [here.images_dir, here.formulas_dir] + [here.domain_dir(kind) for kind in project.DOMAIN_FOLDERS if here.has_folders]
    # laid out by folders, the drawing tabs' folders -- the documents imported to draw on (Imported Plans/) and what the export made of them (Exports/, the figures the documents print) -- and Appendix/, the annexes' PDFs and their excerpts (issue #64, D-09 to D-11, D-19): what the documents read lies there and no more in the export's data/
    if here.has_folders:
        shared += [here.drawing_dir(tab) for tab in project.DRAWING_FOLDERS] + [here.typst_root / project.APPENDIX_FOLDER]
    for folder in shared:
        for path in _files(folder, skipped=[here.archives_dir]):
            if project.DOMAIN_ARCHIVES in path.relative_to(folder).parts[:-1]:
                continue
            chosen[path] = here.rel(path)
    for sub in project.SOURCE_FOLDERS:
        for path in _files(here.sources_dir / sub):
            chosen[path] = here.rel(path)
    for other in here.modes:
        journal = here.journal_file_for(other)
        if journal.is_file():
            chosen[journal] = here.rel(journal)
    positions = here.positions_dir / POSITIONS_FILE   # the project's positions, which every document's #member reads through the export (v0.114) -- in Positions/ laid out by folders (D-24)
    if positions.is_file():
        chosen[positions] = here.rel(positions)
    if here.lists_file.is_file():   # the order of the window's lists and the «Formules» tab's folders (calc/list_order.py, issue #15)
        chosen[here.lists_file] = here.rel(here.lists_file)
    return sorted(chosen.items(), key=lambda item: item[1])


def _reserve(timestamp, pdf_name=None):
    """The zip and the flat PDF path for one archive, claimed without overwriting an earlier one. Two exports in the same clock minute share a timestamp; `-2`, `-3`, ... tell them apart instead of the second silently replacing the first -- opening the zip for exclusive creation is what makes the claim atomic. `timestamp` is the stem the zip is named after -- `<timestamp>-<mode>` for a document of a project in three documents -- and `pdf_name` the name of the PDF copied beside it, the report's by default."""
    here = project.current()
    here.archives_dir.mkdir(parents=True, exist_ok=True)
    pdf_name = pdf_name or here.report_pdf.name
    n = 1
    while True:
        name = timestamp if n == 1 else f"{timestamp}-{n}"
        archive = here.archives_dir / f"{name}.zip"
        pdf = here.archives_dir / f"{name}-{pdf_name}"
        n += 1
        if pdf.exists() or (here.archives_dir / name).exists():
            continue  # a PDF already there, or a folder archived before v0.82 under this very name
        try:
            handle = archive.open("xb")
        except FileExistsError:
            continue
        return name, archive, handle, pdf


def run(route, detail="", mode="rs"):
    """Archives the PDF that was just compiled, and the project state that produced it, into the project's archives folder. Raises on failure -- the caller decides how loud that is. Returns the zip written, or None where there is no PDF yet to archive: a quiet no-op, since that is not a failure of anything.

    `route` names which route is calling (ROUTES: "woodcore-cli" or "gui"; "katalog", the window's route until v0.96, is recorded as "gui"), and `detail` is the exact `--input ...` flags typst compile was given for this run -- forwarded as the caller already built it for the compile itself, never rebuilt here, so the manifest can never disagree with what was actually compiled. `mode` is the document compiled: the report's by default, the only one a report alone has, whose archive is `<timestamp>.zip` as it always was; in a project laid out in three documents each is archived apart, `<timestamp>-<mode>.zip`, with what `members_of_document` chooses and its manifest naming the document. A document the project does not have is a ProjectError.
    """
    route = LEGACY_ROUTES.get(route, route)
    here = project.current()
    source = here.document_pdf(mode)
    if not source.exists():
        return None
    stem, chosen = _timestamp(), None
    if here.has_modes:
        stem, chosen = f"{stem}-{mode}", members_of_document(here, mode)
    name, archive, handle, pdf = _reserve(stem, source.name)
    try:
        pdf.write_bytes(source.read_bytes())
        record = here.data_dir / "project.json"
        manifest = {
            "timestamp": name, "route": route, "detail": detail, "pdf": pdf.name,
            "project": json.loads(record.read_text(encoding="utf-8")) if record.is_file() else None,
        }
        if here.has_modes:
            manifest["document"] = mode
        with zipfile.ZipFile(handle, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for path, arcname in (members(here) if chosen is None else chosen):
                z.write(path, arcname)
            z.writestr("archive-info.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    finally:
        handle.close()
    print(f"archive_export: wrote {here.rel(pdf)} and {here.rel(archive)}")
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--route", required=True, help="which route is calling: woodcore-cli or gui (katalog, its name until v0.96, is read as gui)")
    parser.add_argument("--detail", default="", help="the --input flags typst compile was given for this run, forwarded verbatim")
    parser.add_argument("--project", default=None, help="the project's .woodcore file; the one project.current() finds when left out")
    parser.add_argument("--mode", default="rs", choices=project.MODES, help="the document just compiled: the report (rs) by default, the only one a report alone has")
    args = parser.parse_args()
    try:
        if args.project:
            project.use(args.project)
        run(args.route, args.detail, mode=args.mode)
    except Exception as exc:  # broad: best-effort -- a failed archive must never fail a build that already succeeded; said on stderr
        print(f"archive_export: skipped ({exc})", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
