"""A project in three documents moved into the layout by folders (issue #64, spec 2026-10-15-structure-projet-dossiers REQ-012, UI-002).

From 0.111 to 0.118 a project in three documents kept what the three share at its top -- config.typ, commands.typ, title.typ, references.bib, the form's Template/, the export in `_woodcore/`, the sources in `Woodcore-Datei/`, the archives in `_Archiv/`, the engineer's domains and the unfolded checks in `Formules/`, the sheets in `Plans/` -- and named its documents' folders `1_…`, `2_…`, `3_…` in its language. Laid out by folders (schema 1.1), what configures the documents lies in `000-Typst-Config/`, what is Woodcore's in `000-Woodcore/` -- the export and the engine, the sources and the archives inside it --, the documents in `100-…`, `200-…`, `300-…`, the engineer's domains in `Domains/`, a member check unfolded in its kind's folder under `Timber-checks/`, the scripts in `Scripts/`, the positions in `Positions/`, the sheets in the exports of their kind's plan tab (calc/project.py). This module moves the one into the other: the second step of a migration, after calc/project_migrate.py has brought a report alone into three documents, and the only one for a project made from 0.111 to 0.118.

**It is calc/project_migrate.py's way, applied once more.** Nothing is deleted and nothing is copied: things are renamed (`project_migrate._rename`, tried again where OneDrive or an antivirus holds a file for a moment), in an order where every folder a rename needs is there; `_Archiv/` last, since the migration's own folder is kept beside the archives once it is done. Every `.typ` the engineer writes is rewritten by calc/typst_paths.py where a path it names would stop reaching its target -- `#import "/commands.typ": *` becomes `#import "/000-Typst-Config/commands.typ": *` -- and nothing else of it moves. The `.woodcore` states its new layout and schema_version 1.1, in Woodcore's own form or textually (`project_migrate.woodcore_text`). Then what the layout by folders adds is made: the stub of every domain of a specialised tab (calc/domains/domain_file.py), the folders it has from the start, the workbook of the positions, and a copy of every document a plan is drawn on in its tab's Imported Plans/ and of every annex's PDF in Appendix/ (plan_documents.adopt, annex.adopt: the originals untouched, the records rewritten to name the copies, both backed up first).

**It is proved against a reference taken first**: the export run, the three documents compiled as they are written and read as text; after the last write the project is read again, laid out by folders, its engine intact, the export run again, and each document compiled from its new place must print the same pages, outline and variables (`project_migrate.compare_pdf`).

**A failure anywhere undoes everything**, and a migration that went through is undone on request (`rollback`): `before.zip` holds every file the migration rewrites and the export as it was, `moves.json` every step as it is done, and the migration's folder lies at the top of the project while it runs -- inside no folder it moves -- and in the archives once it is done or undone. Qt-free: the command line (`woodcore-cli migrate`), the window's dialog (migrate_dialog.py) and the tests all go through it.
"""

import json
import os
import shutil
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import documents
import engine
import project
import project_lock
import project_migrate as pm
import typst_paths
import validation

KIND = "folders"
# The migration's own folder while it runs: at the top of the project, inside nothing it moves -- `_Archiv/` is moved into 000-Woodcore/ -- and moved into the archives when it is done or undone.
RUNNING_PREFIX = ".woodcore-" + pm.WORKSPACE_PREFIX
WORKSPACE_PREFIX = pm.WORKSPACE_PREFIX + KIND + "-"
REFERENCE_DIR = pm.REFERENCE_DIR
# The export's folders a rollback puts back as they were: what the reference's export and the proof's write into.
EXPORT_PARTS = ("data", "docs", project.STAMPS_FOLDER)
# What a build or a test leaves in a project, never read as the engineer's: no .typ in it is rewritten.
DEBRIS = pm.DEBRIS | {".git", ".vscode"}


@dataclass
class Plan:
    """What moving `here` into the layout by folders would do, read and never written: the renames in their order, the `.typ` rewritten, the new layout and `.woodcore` text, Tinymist's settings -- and, where it cannot be done, `refusals`."""
    here: project.Project
    after: project.Project = None
    layout: dict = field(default_factory=dict)
    moves: list = field(default_factory=list)
    rewrites: list = field(default_factory=list)
    woodcore_text: str = None
    woodcore_route: str = ""
    vscode: pm.VsCode = None
    refusals: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    language: str = ""

    @property
    def moved(self):
        return {m.source: m.target for m in self.moves}

    @property
    def pairs(self):
        return [(m.source, m.target) for m in self.moves]


def _note(code, text, **args):
    return engine.Note(code, text, **args)


def woodcore_text(raw, layout, version):
    """The project file with `layout` stated and its `schema_version` `version` -- `(text, route)`, the layout written by `project_migrate.woodcore_text` (Woodcore's own form kept, a hand-written file edited textually) and the version's value replaced where it stands. Raises ValueError where the edit does not give the data meant."""
    text, route = pm.woodcore_text(raw, layout)
    bom = "﻿" if text.startswith("﻿") else ""
    body = text[len(bom):]
    members, _end = pm._members(body)
    found = next((m for m in members if m[0] == "schema_version"), None)
    if found is None:
        raise ValueError("the project file states no schema_version")
    _key, _ks, vs, ve = found
    body = body[:vs] + json.dumps(version) + body[ve:]
    expected = dict(json.loads(raw.lstrip("﻿").replace("\r\n", "\n")), layout=dict(layout), schema_version=version)
    if json.loads(body.replace("\r\n", "\n")) != expected:
        raise ValueError("the edit of the project file does not give the data meant")
    return bom + body, route


def _unfolded_kind(path):
    """The kind of check a file of Formules/ was unfolded from -- its `#var-domain(…, gen: (kind: …))`, or, written by the generator 2 that puts no `gen:` in the file (spec 2026-10-21-commandes-typst-refonte, REQ-012), the form the base beside it keeps (Formules/unfold.json) -- or None for a domain of the engineer's own."""
    from domains import formula_domain as fd, unfold
    try:
        domain = fd.read(path)
    except (OSError, UnicodeDecodeError):
        return None
    gen = getattr(domain, "gen", None)
    if isinstance(gen, dict):
        return gen.get("kind")
    try:
        entry = json.loads((path.parent / unfold.BASE_FILE).read_text(encoding="utf-8"))["domains"].get(path.stem) or {}
    except (OSError, ValueError, KeyError, AttributeError):
        return None
    return (entry.get("gen") or {}).get("kind")


def _typs(here, skip):
    """Every `.typ` the engineer writes in project `here`: under its folder, but not under `skip` (the export's folder, the archives) nor in a folder a build or a test leaves (DEBRIS)."""
    out = []
    root = here.root
    for path in sorted(root.rglob("*.typ")):
        if not path.is_file() or any(pm._is_under(path, s) for s in skip):
            continue
        if any(part in DEBRIS or part.startswith((".project-", ".settings-", RUNNING_PREFIX)) for part in path.relative_to(root).parts):
            continue
        out.append(path)
    return out


def plan(here, *, strict=False):
    """What moving `here` (a Project or the path of its `.woodcore`) into the layout by folders would do, and what stands in its way -- read and never written. The refusals: a project laid out as one report (calc/project_migrate.py moves it into three documents first), one laid out by folders already, a place a rename would put something where something is, a path that cannot be made to follow its target, a project file whose layout cannot be written. `strict` refuses a path naming nothing inside the export's folder too, which `run` plans again with once the engine and the export are written."""
    here = here if isinstance(here, project.Project) else project.Project.load(here)
    p = Plan(here=here)
    refuse = p.refusals.append
    name = here.file.name
    if not here.has_modes:
        refuse(_note("not_three_documents", f"{name} is laid out as one report: it is moved into three documents first (woodcore-cli migrate does both)", project=name))
        return p
    if here.has_folders:
        refuse(_note("already_folders", f"{name} is laid out by folders already: there is nothing to migrate", project=name))
        return p
    root = here.root
    entries = {mode: here.document_typ(mode).name for mode in ("cu", "bp")}
    layout = documents.modes_layout(documents.MODE_FOLDERS, entries, rs_entry=here.report_typ.name)
    # a key Woodcore no longer reads is the engineer's to take out, never the migration's (project.RETIRED_KEYS): kept as it is stated
    stated = here.data.get("layout") or {}
    layout.update({key: stated[key] for section, key in project.RETIRED_KEYS if section == "layout" and key in stated})
    p.layout = layout
    p.after = after = project.Project(here.file, {**here.data, "schema_version": project.SCHEMA_VERSION, "layout": layout})
    moves = p.moves

    def move(source, target, what):
        if source.exists() and pm._key(source) != pm._key(target):
            moves.append(pm.Move(source, target, what))

    # 1. What configures the documents, into 000-Typst-Config/.
    for part in (project.CONFIG_FILE, project.COMMANDS_FILE, project.TITLE_FILE, project.REFERENCES_FILE, project.TEMPLATE_FOLDER):
        move(here.config_dir / part, after.config_dir / part, part)
    # 2. Out of the sources before they move: the scripts into Scripts/, the positions into Positions/.
    from domains import script
    scripts = here.sources_dir / script.SOURCES
    if scripts.is_dir():
        for path in sorted(scripts.iterdir()):
            move(path, after.domain_dir("script") / path.name, f"the script {path.name}")
    move(here.sources_dir / "positions.json", after.positions_dir / "positions.json", "the positions")
    # 3. Out of Formules/ before it moves: each unfolded check into its kind's folder, and the base of the unfolded checks.
    from domains import unfold
    formulas = here.formulas_dir
    if formulas.is_dir():
        for path in sorted(formulas.glob("*.typ")):
            kind = _unfolded_kind(path)
            if kind in project.CHECK_KIND_FOLDERS:
                move(path, after.unfolded_dir(kind) / path.name, f"the unfolded check {path.stem}")
        move(formulas / unfold.BASE_FILE, unfold.base_path(after), "the base of the unfolded checks")
        move(formulas, after.formulas_dir, "the engineer's domains (Formules/ -> Domains/)")
    # 4. The sheets, into the exports of their kind's plan tab, their PDF beside them; the bundles' PDFs beside the sheets of their kind.
    import sheets
    for sheet_id in sheets.list_sheets(here):
        try:
            kind = sheets.sheet_kind(here, sheet_id)
        except sheets.SheetError:
            kind = "position"
        target = sheets.folder(after, kind)
        move(sheets.folder(here) / f"{sheet_id}.typ", target / f"{sheet_id}.typ", f"the sheet {sheet_id}")
        move(sheets.folder(here) / f"{sheet_id}.pdf", target / f"{sheet_id}.pdf", f"the PDF of the sheet {sheet_id}")
    try:
        bundles = sheets._read_bundles(here)
    except sheets.SheetError:
        bundles = []
    for entry in bundles:
        try:
            move(sheets.bundle_pdf(here, entry), sheets.bundle_pdf(after, entry), f"the PDF of the bundle {entry['name']}")
        except (sheets.SheetError, KeyError):
            pass
    # 5. The export and the engine into 000-Woodcore/, then the sources inside it.
    move(here.generated_dir, after.generated_dir, "the export and the engine")
    move(here.sources_dir, after.sources_dir, "the sources (Woodcore-Datei/)")
    # 6. The documents' folders.
    for mode in project.MODES:
        move(here.document_dir(mode), after.document_dir(mode), f"the {documents.MODE_NAMES['en'][mode].lower()}'s folder")
    # 7. The archives last: into 000-Woodcore/.
    move(here.archives_dir, after.archives_dir, "the archives (_Archiv/)")

    seen = set()
    for m in moves:
        key = pm._key(m.target)
        if key in seen:
            refuse(_note("collision", f"two things would be moved to {pm._rel(root, m.target)}", path=pm._rel(root, m.target)))
        seen.add(key)
        if m.target.exists():
            refuse(_note("collision", f"{pm._rel(root, m.target)} is there already: {m.what} cannot be moved there -- rename or move it first", path=pm._rel(root, m.target)))

    # The paths every .typ names, rewritten where they would stop reaching their targets -- read now, written after the renames.
    for file in _typs(here, [here.generated_dir, here.archives_dir]):
        file_new = pm._where(file, p.pairs)
        text = typst_paths.read_text(file)
        new_text, changes, unresolved = typst_paths.rewrite(text, file, file_new, root, root, p.moved)
        for item in unresolved:
            literal = item.literal
            target = root / literal.value.lstrip("/") if (literal.root_relative or literal.value.startswith("/")) else file.parent / literal.value
            if "names nothing" in item.reason and (not strict or not pm._is_under(target, here.generated_dir)):
                p.notes.append(f"{here.rel(file)}: {literal.value!r} names nothing, before the migration as after it -- left as it is")
                continue
            refuse(_note("unrewritable", f"{here.rel(file)}: {item.reason}", file=here.rel(file), literal=literal.value, reason=item.reason))
        if new_text != text:
            p.rewrites.append(pm.Rewrite(file, file_new, pm._sha(text.encode("utf-8")), new_text, changes))

    # The project file, schema 1.1.
    raw = here.file.read_bytes().decode("utf-8")
    try:
        text, route = woodcore_text(raw, layout, project.SCHEMA_VERSION)
        new_data = json.loads(text.lstrip("﻿"))
        validation.validate_structure(new_data, "woodcore-project")
        project.Project(here.file, new_data)
    except (ValueError, KeyError, IndexError, validation.ValidationError) as exc:
        refuse(_note("woodcore_unrewritable", f"{name}: its layout cannot be written ({exc})", project=name, reason=str(exc)))
    else:
        p.woodcore_text, p.woodcore_route = text, route

    # Tinymist's settings: its output following the report's folder where it named it -- the root is the project's folder still.
    settings = root / ".vscode" / "settings.json"
    if settings.is_file():
        found = pm.vscode_text(typst_paths.read_text(settings), pm._rel(root, here.document_dir("rs")), pm._rel(root, after.document_dir("rs")))
        if found is not None:
            p.vscode = pm.VsCode(settings, found[0], found[1], False, False)
    return p


def describe(p, refusals=None):
    """The plan as lines of English, for a dry run and for the window's dialog."""
    here = p.here
    out = [f"Migration of {here.name} ({here.file.name}) into the layout by folders:"]
    if p.moves:
        out.append("  moves -- renamed, nothing copied, nothing deleted:")
        out += [f"    {here.rel(m.source)} -> {pm._rel(here.root, m.target)}   ({m.what})" for m in p.moves]
    if p.rewrites:
        count = sum(len(r.changes) for r in p.rewrites)
        out.append(f"  rewrites -- {count} path literal(s) in {len(p.rewrites)} file(s)")
    if p.layout:
        out.append(f"  {here.file.name} ({p.woodcore_route or 'not writable'}) -- schema_version {project.SCHEMA_VERSION}, the layout stated in full:")
        out += [f"    {key}: {value}" for key, value in p.layout.items()]
    if p.vscode:
        out.append(f"  .vscode/settings.json: tinymist.outputPath {p.vscode.output_path[0]!r} -> {p.vscode.output_path[1]!r}")
    out.append("  then: a stub per domain of a specialised tab, the folders of the layout, Positions/Positions.xlsx")
    out += [f"  note: {n}" for n in p.notes]
    refusals = p.refusals if refusals is None else refusals
    if refusals:
        out.append("  REFUSED:")
        out += [f"    [{r.code}] {r}" for r in refusals]
    else:
        out.append("  nothing stands in the way")
    return out


def check(p, *, update_engine=False, lock_owner=None):
    """The refusals of plan `p` and what depends on the moment -- the lock, the engine, Typst, pypdf -- as calc/project_migrate.py's `check` says them."""
    refusals = list(p.refusals)
    here = p.here
    me = project_lock.whoami()
    if lock_owner is not None:
        me["pid"] = int(lock_owner)
    other = project_lock.holder(here, me)
    if other is not None:
        refusals.append(_note("locked", f"{here.file.name} is open in {other.get('user', '?')}'s window on {other.get('host', '?')} since {other.get('since', '?')} -- close it there first",
                              user=other.get("user", "?"), host=other.get("host", "?"), since=other.get("since", "?")))
    if here.has_modes:
        state, detail = project.engine_state(here)
        if state == "newer" or (state in project.ASKED and not update_engine):
            refusals.append(_note("engine_" + ("newer" if state == "newer" else "asked"), project.engine_message(state, detail).replace("export with --update-engine", "migrate with --update-engine"), state=state, detail=detail))
    executable = project.typst_executable()
    if not (Path(executable).is_file() or shutil.which(executable)):
        refusals.append(_note("no_typst", "no Typst to compile the documents with: the migration compares them before and after, and cannot without it"))
    import importlib.util
    if importlib.util.find_spec("pypdf") is None:
        refusals.append(_note("no_pypdf", "pypdf is not installed: the migration reads the documents' pages to compare them, and cannot without it"))
    return refusals


# --- running it -----------------------------------------------------------------------------------

def _running_workspace(here):
    stamp = datetime.now().strftime("%y%m%d-%Hh%M")
    n = 1
    while True:
        name = f"{WORKSPACE_PREFIX}{stamp}" if n == 1 else f"{WORKSPACE_PREFIX}{stamp}-{n}"
        ws = here.root / (RUNNING_PREFIX + name[len(pm.WORKSPACE_PREFIX):])
        try:
            ws.mkdir()
            return ws, name
        except FileExistsError:
            n += 1


def _adopted_records(here):
    """The records the migration's last step may rewrite to name the copies it makes (plan_documents.adopt, annex.adopt), where they lie before anything moves: backed up with the rest."""
    from domains import annex, plan_documents
    return plan_documents.adoptable(here) + annex.adoptable(here)


def _backup(zip_path, root, files, folders):
    """before.zip: `files`, and every file under `folders`, named from `root`."""
    with zipfile.ZipFile(zip_path, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for file in files:
            if file.is_file():
                z.write(file, pm._rel(root, file))
        for folder in folders:
            if folder.is_dir():
                for path in sorted(folder.rglob("*")):
                    if path.is_file():
                        z.write(path, pm._rel(root, path))


def _references(here, folder, log, dates):
    """Each document compiled as it is written into `folder`, read (project_migrate.read_pdf): {mode: what it printed}. Raises MigrationError where one does not compile."""
    out = {}
    for mode in here.modes:
        target = folder / f"{mode}.pdf"
        dates.add(date.today().strftime("%d.%m.%Y"))
        error = pm._compile(documents.compile_args(here, mode, target=target), here)
        dates.add(date.today().strftime("%d.%m.%Y"))
        if error:
            raise pm.MigrationError("failed", f"the {documents.MODE_NAMES['en'][mode].lower()} does not compile as it is written -- the migration compares against it, so it needs one that does:\n{error}")
        out[mode] = pm.read_pdf(target)
        pm._say(log, f"the {documents.MODE_NAMES['en'][mode].lower()} compiled, for the reference")
    return out


def run(here, *, skip_data=False, update_engine=False, dry_run=False, lock_owner=None, log=print, archive=True):
    """Moves `here` (a Project or its `.woodcore`) into the layout by folders, proves it, and gives back what became of it -- result.json's content -- or, with `dry_run`, the Plan and nothing written. The arguments are calc/project_migrate.py `run`'s. Raises project_migrate.MigrationError: `refused` before anything is written, `failed` once everything was undone, `rollback_incomplete` where undoing it did not go through."""
    here = here if isinstance(here, project.Project) else project.Project.load(here)
    p = plan(here)
    refusals = check(p, update_engine=update_engine, lock_owner=lock_owner)
    if dry_run:
        p.refusals = refusals
        for line in describe(p, refusals):
            if log is not None:
                log(line)
        return p
    if refusals:
        raise pm.MigrationError("refused", f"{here.file.name} cannot be moved into the layout by folders: " + "; ".join(refusals), refusals=refusals)
    me = project_lock.whoami()
    if lock_owner is not None:
        me["pid"] = int(lock_owner)
    acquired = project_lock.read(here) is None
    if acquired:
        project_lock.acquire(here, me=me)
    try:
        return _run(here, p, skip_data=skip_data, update_engine=update_engine, log=log, archive=archive)
    finally:
        if acquired:
            project_lock.release(here, me=me)


def _run(here, p, *, skip_data, update_engine, log, archive):
    root = here.root
    ws, ws_name = _running_workspace(here)
    pm._say(log, f"{here.name}: the migration's folder is {pm._rel(root, ws)} while it runs")
    settings = root / ".vscode" / "settings.json"
    export_folders = [here.generated_dir / part for part in EXPORT_PARTS]
    record = {
        "format": pm.FORMAT, "kind": KIND, "log_version": pm.LOG_VERSION, "state": "backup",
        "project": here.file.name, "archives_before": here.layout["archives"], "archives_after": p.layout["archives"],
        "workspace": ws_name, "started": datetime.now().isoformat(timespec="seconds"),
        "generated_before": pm._rel(root, here.generated_dir), "generated_after": p.layout["generated"],
        "layout_before": here.data.get("layout"), "layout_after": p.layout,
        "moves": [], "rewritten": [], "woodcore": None, "vscode": None, "created": [], "made_folders": [], "skip_data": skip_data,
    }
    book = pm._Log(ws, record)
    dates = set()
    try:
        # 1. The backup -- every file the migration rewrites, the project file, Tinymist's settings and the export as it is -- before anything is written.
        pm._say(log, f"backing up what the migration may rewrite into {pm.BACKUP_FILE}")
        # every .typ the engineer writes, and not only those the first plan rewrites: the plan made again once the engine is written may rewrite more (commands.typ's import of an engine that was not there yet)
        _backup(ws / pm.BACKUP_FILE, root, [here.file, settings] + _typs(here, [here.generated_dir, here.archives_dir]) + _adopted_records(here), export_folders)
        record["woodcore"] = {"sha256_before": pm._sha_file(here.file), "route": p.woodcore_route}
        if p.vscode:
            record["vscode"] = {"sha256_before": pm._sha_file(settings)}
        book.state("reference")

        # 2. The reference: the export as the project stands, and the three documents as they are written.
        ref = ws / REFERENCE_DIR
        ref.mkdir()
        with project.using(here):
            if skip_data:
                project.sync_engine(here, update=update_engine)
            else:
                import export_all
                pm._say(log, "the export, as the project stands")
                export_all.run(update_engine=update_engine)
        references = _references(here, ref, log, dates)

        # The plan made again, strictly, now that the engine and the export are written.
        again = plan(here, strict=True)
        if again.refusals:
            raise pm.MigrationError("failed", "once the reference is taken the migration is refused: " + "; ".join(again.refusals), refusals=again.refusals)
        if [(m.source, m.target) for m in again.moves] != [(m.source, m.target) for m in p.moves]:
            raise pm.MigrationError("failed", "the project changed while the reference was taken: the moves are not the ones planned")
        p = again
        record["moves"] = [{"from": pm._rel(root, m.source), "to": pm._rel(root, m.target), "what": m.what, "state": "planned"} for m in p.moves]
        for rewrite in p.rewrites:
            record["rewritten"].append({"file": pm._rel(root, rewrite.file_new), "from": pm._rel(root, rewrite.file_old),
                                        "sha256_before": rewrite.sha_before, "state": "planned"})
        book.state("moving")

        # 3. The renames, in their order, each folder a rename needs made first -- and said, for a rollback to take away.
        for entry, move in zip(record["moves"], p.moves):
            if not move.source.exists() or move.target.exists():
                raise pm.MigrationError("failed", f"{move.what} is not where the plan found it, or {pm._rel(root, move.target)} is taken")
            made, parent = [], move.target.parent
            while not parent.exists():
                made.append(parent)
                parent = parent.parent
            for folder in reversed(made):
                folder.mkdir()
                record["made_folders"].append(pm._rel(root, folder))
            entry["state"] = "moving"
            book.save()
            pm._rename(move.source, move.target)
            entry["state"] = "done"
            book.save()
            pm._say(log, f"moved {entry['from']} -> {entry['to']}")

        # 4. The rewrites: every .typ's paths, the project file, Tinymist's settings.
        book.state("rewriting")
        for entry, rewrite in zip(record["rewritten"], p.rewrites):
            current = typst_paths.read_text(rewrite.file_new)
            if pm._sha(current.encode("utf-8")) != rewrite.sha_before:
                raise pm.MigrationError("failed", f"{entry['file']} changed while it was being migrated")
            entry["state"] = "writing"
            book.save()
            pm._write_bytes(rewrite.file_new, rewrite.text.encode("utf-8"))
            entry["sha256_after"] = pm._sha_file(rewrite.file_new)
            entry["state"] = "done"
            book.save()
        pm._say(log, f"{len(p.rewrites)} file(s) rewritten")
        if pm._sha_file(here.file) != record["woodcore"]["sha256_before"]:
            raise pm.MigrationError("failed", f"{here.file.name} changed while it was being migrated")
        record["woodcore"]["state"] = "writing"
        book.save()
        pm._write_bytes(here.file, p.woodcore_text.encode("utf-8"))
        record["woodcore"]["sha256_after"] = pm._sha_file(here.file)
        record["woodcore"]["state"] = "done"
        book.save()
        if p.vscode:
            if pm._sha_file(settings) != record["vscode"]["sha256_before"]:
                raise pm.MigrationError("failed", ".vscode/settings.json changed while the project was being migrated")
            pm._write_bytes(settings, p.vscode.text.encode("utf-8"))
            record["vscode"]["sha256_after"] = pm._sha_file(settings)
            record["vscode"]["state"] = "done"
            book.save()

        # 5. What the layout by folders adds: its folders, the stubs of the domains, the workbook of the positions.
        book.state("creating")
        migrated = project.Project.load(here.file)
        for folder in migrated.structure_folders():
            made, parent = [], folder
            while not parent.exists():
                made.append(parent)
                parent = parent.parent
            for path in reversed(made):
                path.mkdir()
                record["made_folders"].append(pm._rel(root, path))
        book.save()
        from domains import domain_file
        domain_file.sync(migrated)   # the domains' own files are written out at the next export (calc/domains/unfold.py)
        book.save()
        import positions_store
        workbook = positions_store.write_workbook(migrated)
        if workbook is not None:
            record["created"].append(pm._rel(root, workbook))
        # the documents the plans are drawn on copied into Imported Plans/, the annexes' PDFs into Appendix/, their records rewritten to name the copies (D-09, D-11) -- each copy said as made, each record as rewritten, its bytes before in before.zip under the path it had
        from domains import annex, plan_documents
        for written, made in plan_documents.adopt(migrated) + annex.adopt(migrated):
            if made is not None:
                record["created"].append(pm._rel(root, made))
            before = here.sources_dir / Path(written).resolve().relative_to(migrated.sources_dir)
            record["rewritten"].append({"file": pm._rel(root, written), "from": pm._rel(root, before), "sha256_after": pm._sha_file(written), "state": "done"})
        # the figures the proof's export writes into the tabs' Exports/ (D-10): set aside by a rollback, as the export in data/ is put back
        record["figure_folders"] = [pm._rel(root, migrated.figures_dir(kind)) for kind in project.FIGURE_KINDS]
        # each document's journal named in data/domain-files.json where its folder lies now (spec 2026-10-21-commandes-typst-refonte, Q-008): put back with data/ by a rollback
        from domains import list_files
        list_files.list_journals(migrated)
        book.save()
        book.state("verifying")

        # 6. The proof.
        diffs = _verify(migrated, references, ref, dates, skip_data, log)
        if diffs:
            raise pm.MigrationError("failed", f"the migrated project is not the project it was: {diffs[0]}", diffs=diffs)

        # 7. Done: the migration's folder into the archives, where a rollback is asked for.
        book.state("done")
        outcome = {"ok": True, "kind": KIND, "project": here.file.name, "workspace": pm._rel(root, migrated.archives_dir / ws_name),
                   "layout": p.layout, "moves": record["moves"], "rewritten": len(p.rewrites), "created": record["created"], "skip_data": skip_data}
        pm._result(ws, outcome)
        final = migrated.archives_dir / ws_name
        pm._rename(ws, final)
        if archive:
            pm._archive(migrated, log)
        pm._say(log, "the project is laid out by folders, and its documents print what they printed")
        return outcome
    except BaseException as exc:
        reason = str(exc) or exc.__class__.__name__
        diffs = getattr(exc, "diffs", [])
        pm._say(log, f"FAILED -- {reason.splitlines()[0]}; undoing everything")
        try:
            problems = _undo(ws, book.record, log)
        except BaseException as undo_exc:   # broad: the undo's own failure is said, never hidden behind the first
            problems = [f"the rollback stopped: {undo_exc}"]
        pm._result(ws, {"ok": False, "kind": KIND, "project": here.file.name, "reason": reason, "diffs": diffs,
                        "rolled_back": not problems, "rollback_problems": problems})
        kept = here.archives_dir / ws_name
        if not problems:
            try:
                here.archives_dir.mkdir(parents=True, exist_ok=True)
                pm._rename(ws, kept)
                ws = kept
            except OSError:
                pass
        if problems:
            raise pm.MigrationError("rollback_incomplete", f"the migration failed ({reason.splitlines()[0]}) and undoing it did not go through: "
                                    + "; ".join(problems) + f" -- {pm.BACKUP_FILE} in {pm._rel(root, ws)} holds what the migration rewrote", diffs=diffs, workspace=ws) from exc
        if isinstance(exc, KeyboardInterrupt):
            raise
        raise pm.MigrationError("failed", f"the migration failed and was undone: {reason}", diffs=diffs, workspace=ws) from exc


def _verify(migrated, references, ref, dates, skip_data, log):
    """The proof: the project read again laid out by folders, its engine intact, the export run again, and each document compiled from its new place printing what it printed -- the differences found, [] where there is none."""
    if not migrated.has_folders or migrated.modes != project.MODES:
        return [f"{migrated.file.name} does not read as a project laid out by folders"]
    state, detail = project.engine_state(migrated)
    if state not in ("current", "stale"):
        return [f"the engine moved with the export and is not intact: {state} {detail}".strip()]
    if not skip_data:
        import export_all
        pm._say(log, "the export again, from the layout by folders")
        with project.using(migrated):
            export_all.run()
    diffs = []
    for mode in migrated.modes:
        target = ref / f"{mode}-after.pdf"
        dates.add(date.today().strftime("%d.%m.%Y"))
        error = pm._compile(documents.compile_args(migrated, mode), migrated)
        dates.add(date.today().strftime("%d.%m.%Y"))
        if error:
            diffs.append(f"the {documents.MODE_NAMES['en'][mode].lower()} does not compile from its new folder:\n{error}")
            continue
        shutil.copyfile(migrated.document_pdf(mode), target)
        found = pm.compare_pdf(references[mode], pm.read_pdf(target), sorted(dates))
        diffs += [f"the {documents.MODE_NAMES['en'][mode].lower()}: {d}" for d in found]
        pm._say(log, f"the {documents.MODE_NAMES['en'][mode].lower()} compiled from its new folder" + ("" if not found else ", and prints otherwise"))
    return diffs


# --- undoing it -----------------------------------------------------------------------------------

def _undo(ws, record, log, check_after=False):
    """Everything the migration did, undone from its log: what it made set aside into the workspace's rolled-back/ (never deleted), every rewritten file given its bytes back from before.zip, the renames reversed, the folders it made taken away where empty, and the export put back as it was. `check_after` refuses, before anything is touched, a file the engineer changed since the migration (a rollback asked for). Returns the problems, [] where it all went through."""
    root = Path(ws).resolve().parent
    problems = []
    backup = Path(ws) / pm.BACKUP_FILE
    held = {}
    if backup.is_file():
        with zipfile.ZipFile(backup) as z:
            held = {name: z.read(name) for name in z.namelist() if not name.endswith("/")}
    if check_after:
        for entry in record["rewritten"]:
            if entry.get("state") == "done" and pm._sha_file(root / entry["file"]) != entry.get("sha256_after"):
                raise pm.MigrationError("rollback_refused", f"{entry['file']} changed since the migration -- it is not undone over what was written since")
    # what the migration made: set aside -- and every figure the proof's export wrote into the tabs' Exports/ (issue #64, D-10)
    for rel in reversed(record.get("created", [])):
        path = root / rel
        if path.exists():
            pm._set_aside(ws, root, path)
    for rel in record.get("figure_folders", []):
        folder = root / rel
        for path in sorted(folder.rglob("*")) if folder.is_dir() else ():
            if path.is_file():
                pm._set_aside(ws, root, path, "export")
    # the rewritten files, their bytes back where they lie now
    for entry in record["rewritten"]:
        if entry.get("state") in ("writing", "done") and entry["from"] in held:
            pm._write_bytes(root / entry["file"], held[entry["from"]])
    _remove_made(root, record)   # the folders made empty by setting aside what was made in them -- 000-Woodcore/archives before 000-Woodcore is renamed back
    # the renames, reversed
    for entry in reversed(record["moves"]):
        if entry.get("state") not in ("moving", "done"):
            continue
        source, target = root / entry["from"], root / entry["to"]
        if target.exists() and not source.exists():
            source.parent.mkdir(parents=True, exist_ok=True)
            pm._rename(target, source)
        elif not source.exists():
            problems.append(f"{entry['to']} is not where the migration put it, and {entry['from']} is not there either")
    _remove_made(root, record)   # and those the renames back left empty
    # archives the migration made rather than moved -- a project that had none -- and that hold something now, an archive written since: where the archives were, not inside the export's folder
    generated_after, archives_after = record["generated_after"], record["archives_after"]
    if archives_after.startswith(generated_after + "/"):
        stray = root / record["generated_before"] / archives_after[len(generated_after) + 1:]
        before = root / record["archives_before"]
        if stray.is_dir() and not before.exists():
            before.parent.mkdir(parents=True, exist_ok=True)
            pm._rename(stray, before)
    # the project file and Tinymist's settings, then the export as it was
    for rel in (record["project"], ".vscode/settings.json"):
        if rel in held and (root / rel).is_file() and (root / rel).read_bytes() != held[rel]:
            pm._write_bytes(root / rel, held[rel])
    generated = root / record["generated_before"]
    for part in EXPORT_PARTS:
        folder = generated / part
        prefix = pm._rel(root, folder) + "/"
        if folder.is_dir():
            for path in sorted(folder.rglob("*")):
                if path.is_file() and pm._rel(root, path) not in held:
                    pm._set_aside(ws, root, path, "export")
        for name, data in held.items():
            if name.startswith(prefix):
                target = root / name
                if not target.is_file() or target.read_bytes() != data:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    pm._write_bytes(target, data)
    pm._say(log, "undone" if not problems else "undone, with problems: " + "; ".join(problems))
    return problems


def _remove_made(root, record):
    """The folders the migration made, deepest first, taken away where nothing is left in them."""
    for rel in sorted(set(record.get("made_folders", [])), key=lambda r: r.count("/"), reverse=True):
        path = root / rel
        try:
            if path.is_dir() and not any(path.iterdir()):
                path.rmdir()
        except OSError:
            pass


def rollback(workspace, *, log=print, lock_owner=None):
    """Undoes a migration into the layout by folders that went through, from its folder in the archives (`000-Woodcore/archives/migration-folders-…`): the folder is taken to the top of the project first -- the archives are moved back to where they were with everything else --, refused where something was changed since, and kept in the archives where they are back. Raises MigrationError `rollback_refused` or `rollback_incomplete`."""
    workspace = Path(workspace).resolve()
    record = json.loads((workspace / pm.LOG_FILE).read_text(encoding="utf-8"))
    if record.get("kind") != KIND or record.get("state") != "done":
        raise pm.MigrationError("rollback_refused", f"{workspace.name} is no migration into the layout by folders that went through")
    root = workspace
    for _part in Path(record["archives_after"]).parts:
        root = root.parent
    root = root.parent
    here = project.Project.load(root / record["project"])
    me = project_lock.whoami()
    if lock_owner is not None:
        me["pid"] = int(lock_owner)
    other = project_lock.holder(here, me)
    if other is not None:
        raise pm.MigrationError("rollback_refused", f"{here.file.name} is open in {other.get('user', '?')}'s window -- close it there first")
    running = root / (RUNNING_PREFIX + record["workspace"][len(pm.WORKSPACE_PREFIX):])
    pm._rename(workspace, running)
    try:
        problems = _undo(running, record, log, check_after=True)
    except pm.MigrationError:
        pm._rename(running, workspace)
        raise
    record["state"] = "rolled_back"
    pm._write_json(running / pm.LOG_FILE, record)
    kept = root / record["archives_before"] / record["workspace"]
    kept.parent.mkdir(parents=True, exist_ok=True)
    pm._rename(running, kept)
    if problems:
        raise pm.MigrationError("rollback_incomplete", "the rollback did not go through: " + "; ".join(problems), workspace=kept)
    return kept
