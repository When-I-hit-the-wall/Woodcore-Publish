"""The example project as it was laid out before the three documents -- one report whose folder is the Typst root -- rebuilt from the committed example, which is laid out in three since it was migrated (the three document modes, work package 1.8).

The migration's own tests (tests/test_migrate.py) and the path rewriter's (tests/test_typst_paths.py) need a project in the old shape to migrate, and the committed example is not one any more. Rather than a second copy of it, committed beside the first and ageing apart from it, the old shape is rebuilt from the new by undoing the migration by hand, in the order the migration did it and backwards:

- the two documents the migration made, the Tinymist settings it wrote where the project had none and the two journals it seeded, taken away;
- the report's folder given back its old name, and what went up to the top of the project -- the export, the pictures, config.typ, commands.typ, references.bib -- put back into it;
- every root-absolute path the migration wrote into the report (`"/commands.typ"`, `"/Images/…"`) made relative again from where its file lies, which is the form the example was written in (`"../commands.typ"`, `"commands.typ"` from the entry), a `project:` path, which the engine reads from the root either way, left as it is;
- and the project file's `layout` taken out, which leaves the file in Woodcore's own form, as the example's was.

⚠️ It rebuilds the example **exactly** as it was committed before its migration, and that was checked once, file for file against the commit before it (modulo line endings, which git gives each machine its own): 97 files, the same bytes. It is not a promise that holds for any project -- a report written with root-absolute paths before the three documents would come back relative -- only for this one, which is what the tests need.

⚠️ The engine the migrated example carries (gitignored, `_woodcore/lib/` and the rest) is not copied, and neither are its archives, its stamps or a document's PDF a compile left: the old shape is the one a fresh clone has.
"""

import json
import os
import shutil
from pathlib import Path

import documents
import project
import project_migrate
import typst_paths

# The report's folder as every project was laid out before the three documents: project.DEFAULT_LAYOUT's, which the example stated by stating no layout at all.
REPORT = Path(project.DEFAULT_LAYOUT["report"]).parent.name
# What the migration took up to the top of the project, in the order it moved them (calc/project_migrate.py plan()).
TAKEN_UP = (documents.LEGACY_GENERATED_FOLDER, project.IMAGES_FOLDER, project.CONFIG_FILE, project.COMMANDS_FILE, project.REFERENCES_FILE)
# What a copy of the migrated example leaves out: the engine a sync wrote, the stamps a compile wrote, the archives.
_ENGINE = {"lib", "calc", project.ENGINE_STAMP, "stamps"}


def _ignore(top):
    def ignore(directory, names):
        here = Path(directory)
        if here == top:
            return {n for n in names if n in ("_Archiv",) or n.endswith(".lock")}
        if here.name == documents.LEGACY_GENERATED_FOLDER and here.parent == top:
            return {n for n in names if n in _ENGINE}
        return set()
    return ignore


def _relative_again(file, root):
    """The root-absolute paths of `file` -- what the migration wrote -- relative again from the file's own folder, every other byte kept."""
    text = typst_paths.read_text(file)
    edits = []
    for literal in typst_paths.literals(text):
        if literal.partial or literal.root_relative or not literal.value.startswith("/"):
            continue
        target = root / literal.value.lstrip("/")
        relative = os.path.relpath(target, file.parent).replace(os.sep, "/")
        edits.append((literal.start, literal.end, typst_paths._escape(relative)))
    for start, end, new in sorted(edits, reverse=True):
        text = text[:start] + new + text[end:]
    if edits:
        typst_paths.write_text(file, text)
    return len(edits)


def build(dest, source=None):
    """The example laid out as one report, in `dest` (made here; it must not exist yet), and its Project. `source` names the example's `.woodcore` -- tests/projet-exemple/Exemple.woodcore by default."""
    source = Path(source) if source else Path(__file__).resolve().parent.parent / "projet-exemple" / "Exemple.woodcore"
    here = project.Project.load(source)
    if not here.has_modes:
        raise ValueError(f"{source} is laid out as one report already: there is nothing to undo")
    dest = Path(dest)
    if here.has_folders:
        # laid out by folders since issue #64: first back to the three documents of 0.111 (tests/fixtures/legacy_three.py), then on as below
        from fixtures import legacy_three
        copy = legacy_three.build(dest, source)
    else:
        shutil.copytree(here.root, dest, ignore=_ignore(here.root.resolve()))
        copy = project.Project.load(dest / source.name)
    top = copy.root
    rs = copy.document_dir("rs")

    # what the migration made
    for mode in ("cu", "bp"):
        shutil.rmtree(copy.document_dir(mode))
        (copy.data_dir / documents.JOURNAL_FILES[mode]).unlink(missing_ok=True)
    # and the title page the two documents set, which the migration writes where the report carries none -- the report's entry keeps its own
    (top / project.TITLE_FILE).unlink(missing_ok=True)
    shutil.rmtree(top / ".vscode", ignore_errors=True)
    for mode in project.MODES:
        copy.document_pdf(mode).unlink(missing_ok=True)

    # the report's folder under its old name, and what went up put back into it
    old = top / REPORT
    project_migrate._rename(rs, old)
    for name in TAKEN_UP:
        if (top / name).exists():
            project_migrate._rename(top / name, old / name)
    # the domains the export wrote out, which the report includes by domain-file(kind, id) (spec 2026-10-21-commandes-typst-refonte, ARCH-008): beside it under the report's root, and data/domain-files.json naming them from there -- the journal the report's own, the two documents' gone with them
    for name in sorted({folder.split("/")[0] for folder in project.DOMAIN_FOLDERS.values()}):
        if (top / name).is_dir():
            project_migrate._rename(top / name, old / name)
    listing = old / documents.LEGACY_GENERATED_FOLDER / "data" / "domain-files.json"
    if listing.is_file():
        files = json.loads(listing.read_text(encoding="utf-8"))
        journals = files["files"].pop("journal", {})
        if "rs" in journals:
            files["files"]["journal"] = {"rs": "/" + journals["rs"].split("/", 2)[2]}
        listing.write_text(json.dumps(files, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # its paths relative again
    generated = old / documents.LEGACY_GENERATED_FOLDER
    for file in sorted(old.rglob("*.typ")):
        if generated in file.parents:
            continue
        _relative_again(file, old)

    # the project file without its layout, in Woodcore's own form and its own line endings
    raw = copy.file.read_bytes().decode("utf-8")
    newline = "\r\n" if "\r\n" in raw else "\n"
    data = json.loads(raw)
    data.pop("layout", None)
    copy.file.write_bytes((json.dumps(data, ensure_ascii=False, indent=2) + "\n").replace("\n", newline).encode("utf-8"))
    legacy = project.Project.load(copy.file)
    assert not legacy.has_modes and legacy.report_typ.is_file(), "the example did not come back as one report"
    return legacy
