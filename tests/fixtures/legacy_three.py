"""The example project as it was laid out from 0.111 to 0.118 -- three documents, what they share at the top of the project -- rebuilt from the committed example, which is laid out by folders since it was migrated (issue #64, spec 2026-10-15-structure-projet-dossiers).

The migration's own tests (tests/test_migrate_folders.py) need a project in that shape to migrate, and so does tests/fixtures/legacy_example.py, which goes one step further back, to the report alone. Rather than a second copy of the example, committed beside the first and ageing apart from it, the shape is rebuilt from the new one by undoing calc/project_migrate_folders.py by hand, backwards:

- what the migration made taken away: Positions/Positions.xlsx, and the folders of the layout left empty;
- every rename reversed: the documents' folders back to `1_…`, `2_…`, `3_…` in the project's language, 000-Woodcore/ back to `_woodcore/` and its sources to `Woodcore-Datei/`, Domains/ to `Formules/` with the unfolded checks and their base, the positions and the scripts back into the sources, what configures the documents back to the top;
- every path the migration rewrote written back (calc/typst_paths.py, root-absolute as the example writes them), commands.typ's import of the engine relative again as the example writes it;
- the figures the export writes into each tab's Exports/Figures/ and Appendix/Exports/ moved back under the export's data/, and every JSON of data/ naming them as data/ named them (`plans/P01.svg`); each annex's PDF moved back beside its record as `<id>.pdf`, the record at 1.0 again (lot 2, D-10, D-11);
- the project file stating the layout of three documents, schema_version 1.0;
- and the export's two indexes that name a file -- data/checks.json's `file` of an unfolded check, data/formulas.json's -- written again for that layout, as an export of it writes them.

⚠️ It rebuilds the example as it was committed before this migration, which was checked once, file for file, against the commit before it -- the export's two indexes aside, written since by the engine that reads `file` (checks 1.4). It is not a promise for any project, only for this one, which is what the tests need. The engine, the stamps, the archives and a document's PDF are not copied: the old shape is the one a fresh clone has.
"""

import json
import os
import shutil
from pathlib import Path

import documents
import engine
import project
import typst_paths

_ENGINE = {"lib", "calc", project.ENGINE_STAMP, "stamps", "archives"}


def _ignore(top, document_dirs):
    def ignore(directory, names):
        here = Path(directory)
        if here == top:
            return {n for n in names if n.endswith(".lock") or n.startswith(".woodcore-")}
        if here.name == project.WOODCORE_FOLDER and here.parent == top:
            return {n for n in names if n in _ENGINE}
        if here in document_dirs:
            return {n for n in names if n.endswith(".pdf")}   # a document's PDF, which a compile wrote
        return set()
    return ignore


def _move(source, target, moves):
    if source.exists():
        import project_migrate
        target.parent.mkdir(parents=True, exist_ok=True)
        project_migrate._rename(source, target)   # tried again where OneDrive or an antivirus holds a folder just copied
        moves[target] = source   # typst_paths reads {where it was: where it is now} -- here the other way round, the copy's new place to its old
        return True
    return False


def build(dest, source=None):
    """The example laid out in three documents as 0.111 to 0.118 laid it out, in `dest` (made here; it must not exist yet), and its Project. `source` names the example's `.woodcore` -- tests/projet-exemple/Exemple.woodcore by default."""
    from domains import formula_domain, member_check, script, unfold
    source = Path(source) if source else Path(__file__).resolve().parent.parent / "projet-exemple" / "Exemple.woodcore"
    here = project.Project.load(source)
    if not here.has_folders:
        raise ValueError(f"{source} is not laid out by folders: there is nothing to undo")
    dest = Path(dest)
    shutil.copytree(here.root, dest, ignore=_ignore(here.root.resolve(), {here.document_dir(mode) for mode in project.MODES}))
    copy = project.Project.load(dest / source.name)
    top = copy.root
    lang = next(lang for lang in documents.LANGUAGES if documents.ENTRY_NAMES[lang]["cu"] == copy.document_typ("cu").name)

    # what the migration made (the domains' files, written out since the spec 2026-10-21-commandes-typst-refonte, are carried: lot 18)
    (copy.positions_dir / "Positions.xlsx").unlink(missing_ok=True)

    # lot 2: the figures back under data/, named from data/ again; the annexes' PDFs back beside their records
    from domains import annex
    renamed = {}
    for kind, sub in project.FIGURE_KINDS.items():
        folder = copy.figures_dir(kind)
        for path in sorted(folder.iterdir()) if folder.is_dir() else []:
            if path.is_file():
                _move(path, copy.data_dir / sub / path.name, {})
        renamed[f'"/{project.figures_folder(kind)}/'] = f'"{sub}/'
    for path in sorted(copy.data_dir.rglob("*.json")):
        text = before = path.read_text(encoding="utf-8")
        for new, old_name in renamed.items():
            text = text.replace(new, old_name)
        if text != before:
            path.write_bytes(text.encode("utf-8"))
    # the domains the export wrote out name their figures from the root (spec 2026-10-21-commandes-typst-refonte, REQ-017): named where the figures lie now, under data/ -- the renames below carry them on
    for kind, sub in project.FIGURE_KINDS.items():
        for folder in {copy.domain_dir(k) for k in project.DOMAIN_FOLDERS if k != "script"} | {copy.unfolded_dir(k) for k in project.CHECK_KIND_FOLDERS}:
            for path in sorted(folder.glob("*.typ")) if folder.is_dir() else []:
                text = before = path.read_text(encoding="utf-8")
                text = text.replace(f'"/{project.figures_folder(kind)}/', f'"{copy.from_root(copy.data_dir / sub)}/')
                if text != before:
                    path.write_bytes(text.encode("utf-8"))
    for sid, record in annex.list_sources(copy).items():
        if record.get("file"):
            _move(annex.pdf_path(copy, sid, record), annex.sources_dir(copy) / f"{sid}.pdf", {})
            record = {k: v for k, v in record.items() if k != "file"}
            record["schema_version"] = annex.SOURCE_SCHEMA_VERSION
            engine.write_json(annex.sources_dir(copy) / f"{sid}.json", record)

    # the renames, backwards: {old place: new place} as the forward migration saw them
    back = {}   # new -> old
    old = {mode: top / documents.LEGACY_MODE_FOLDERS[lang][mode] for mode in project.MODES}
    for mode in reversed(project.MODES):
        _move(copy.document_dir(mode), old[mode], back)
    # each document's journal, which its section includes by domain-file("journal", document): named in its folder's old name
    listing = copy.data_dir / "domain-files.json"
    if listing.is_file():
        files = json.loads(listing.read_text(encoding="utf-8"))
        if "journal" in files["files"]:
            files["files"]["journal"] = {mode: "/" + old[mode].name + "/journal.typ" for mode in files["files"]["journal"]}
            listing.write_text(json.dumps(files, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _move(copy.sources_dir, top / project.DEFAULT_LAYOUT["sources"], back)
    _move(copy.generated_dir, top / documents.LEGACY_GENERATED_FOLDER, back)
    sources = top / project.DEFAULT_LAYOUT["sources"]
    formulas = top / project.FORMULAS_FOLDER
    _move(copy.formulas_dir, formulas, back)
    _move(unfold.base_path(copy), formulas / unfold.BASE_FILE, back)
    for kind in project.CHECK_KIND_FOLDERS:
        folder = copy.unfolded_dir(kind)
        for path in sorted(folder.glob("*.typ")) if folder.is_dir() else []:
            _move(path, formulas / path.name, back)
    _move(copy.positions_dir / "positions.json", sources / "positions.json", back)
    scripts = copy.domain_dir("script")
    for path in sorted(scripts.iterdir()) if scripts.is_dir() else []:
        if path.suffix != ".typ":
            _move(path, sources / script.SOURCES / path.name, back)
    for part in (project.CONFIG_FILE, project.COMMANDS_FILE, project.TITLE_FILE, project.REFERENCES_FILE, project.TEMPLATE_FOLDER):
        _move(copy.config_dir / part, top / part, back)
    # the folders of the layout, left empty
    for folder in sorted(copy.structure_folders() + [copy.config_dir, copy.generated_dir], key=lambda p: len(p.parts), reverse=True):
        for path in [folder, *folder.parents]:
            if path == top or not path.is_dir() or any(path.iterdir()):
                break
            path.rmdir()

    # the paths written back, root-absolute as the example writes them; commands.typ's import of the engine relative again
    import project_migrate
    forward = list(back.items())                       # (the old place, the folders' place): where each file lay before this undoing
    undone = {new: old for old, new in back.items()}   # what typst_paths reads: {where it was: where it is now}
    for file in sorted(top.rglob("*.typ")):
        if (top / documents.LEGACY_GENERATED_FOLDER) in file.parents:
            continue
        typst_paths.rewrite_file(file, project_migrate._where(file, forward), top, top, undone)
    commands = top / project.COMMANDS_FILE
    text = typst_paths.read_text(commands)
    typst_paths.write_text(commands, text.replace(f'"/{project.WOODCORE_FOLDER}/lib/', f'"{documents.LEGACY_GENERATED_FOLDER}/lib/'))

    # the project file: three documents as 0.111 laid them out, schema 1.0, a retired key where the file states it
    raw = copy.file.read_bytes().decode("utf-8")
    newline = "\r\n" if "\r\n" in raw else "\n"
    data = json.loads(raw)
    stated = data["layout"]
    layout = documents.legacy_modes_layout(documents.LEGACY_MODE_FOLDERS[lang], {m: copy.document_typ(m).name for m in ("cu", "bp")}, rs_entry=copy.report_typ.name)
    ordered = {}
    for key in layout:
        ordered[key] = layout[key]
        if key == "images":
            ordered.update({k: stated[k] for s, k in project.RETIRED_KEYS if s == "layout" and k in stated})
    data["layout"], data["schema_version"] = ordered, "1.0"
    copy.file.write_bytes((json.dumps(data, ensure_ascii=False, indent=2) + "\n").replace("\n", newline).encode("utf-8"))
    legacy = project.Project.load(copy.file)
    assert legacy.has_modes and not legacy.has_folders, "the example did not come back laid out in three documents"

    # the export's indexes that name a file, as an export of this layout writes them
    checks_file = legacy.data_dir / "checks.json"
    if checks_file.is_file():
        checks = json.loads(checks_file.read_text(encoding="utf-8"))
        if member_check.mark_unfolded_files(checks, unfold.unfolded_files(legacy, checks)):
            engine.write_json(checks_file, checks)
    with project.using(legacy):
        formula_domain.export(legacy)
    return legacy
