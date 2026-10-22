"""Whether a document's Typst changed since its PDF was written -- the engineer's rule «export a document only if its Typst changed since its PDF» (30.09.2026), for the three documents of a project (calc/documents.py) and for a report alone.

Typst can say what a compile read: `typst compile --deps <file> --deps-format json` writes `{"inputs": [...], "outputs": [...]}`, the path -- absolute, or from the folder Typst was started in, the Typst root (`_read_deps`) -- of every file the document read -- its sections, config.typ and commands.typ, the engine's lib/ and the norm tables it reads, the export's data/ and the pictures -- and none that it did not. `record` turns that, after a successful compile, into a **stamp** in the export's folder (`_woodcore/stamps/<document>.json`): the PDF's SHA-256, the Typst version, the flags, and a digest of every input. `changed` compares today's files with the stamp; nothing is compiled to find out. A document whose stamp says nothing changed is neither compiled nor archived.

**A digest of the content and never a modification time.** A file saved again with the same bytes -- NextCloud setting a time, an editor saving without a change, the data export writing identical JSON (`data/project.json` carries no date, calc/project.py) -- changes nothing in the PDF, and compiling it again is the ten seconds the rule is there to save. A file of the project is hashed (`sha256:<hex>`); one outside it -- a Typst package, a font -- is named by its size and time (`stat:<size>:<mtime_ns>`), being Typst's and not the engineer's.

⚠️ **An input modified after the PDF was written is not vouched for.** `record` runs after the compile, so a file saved in between would be hashed in its new state and the stamp would call a PDF current that was made from the old one. The only part of that window a stamp can see is a modification later than the PDF itself, and such a file is recorded as unsettled (`UNSETTLED`): it never matches, and the next `changed` names it. A time in the future (`CLOCK_SLACK_NS`) is no evidence of anything -- a file another machine's clock dated, which NextCloud brings over -- and is not held against the file: it would otherwise be unsettled for ever, and its document compiled at every export. What is saved while Typst is still compiling is indistinguishable from what was there before, and is the one case this does not catch.

**Where Typst's list is missing or unreadable** -- a Typst too old to write one, a deps file another compile left behind -- the stamp falls back on an enumerated set: the document folder's .typ files, config.typ, commands.typ and references.bib at the Typst root, the export's lib/, calc/ and data/, and the pictures. It says so (`inputs_from`), and `changed` then also names a file that has appeared in that set since, which a list Typst wrote cannot need and this one does.

The preview of a document (the Structure tab's, compiled at every save, docs/domain/documents.md §3.3octodecies) keeps a stamp of its own, `<document>.preview.json`, so it never says anything of the deliverable. Qt-free, and it reads no project of its own: a function that needs one is handed it.
"""

import hashlib
import json
import os
import time
from pathlib import Path

import engine
import project

# The stamp's format: a stamp of another is read as none, so the document is compiled and a stamp of this one written.
STAMP_VERSION = 1
# Where a stamp's inputs came from: Typst's own list of what it read, or the set this module enumerates where there is none.
FROM_DEPS = "deps"
FROM_ENUMERATED = "enumerated"
# The digest of an input that changed after the PDF was written, or that could not be read when the stamp was taken: it equals no digest a file can have, so `changed` names the file.
UNSETTLED = "unsettled"
# How far ahead of the clock a file's modification time may be for `record` to take it for a real one: a time further on is another machine's clock and says nothing about when the file was saved.
CLOCK_SLACK_NS = 1_000_000_000
# The folders of the export a document reads, where Typst's list is not there to say so.
GENERATED_READS = ("lib", "calc", "data")
# A folder no enumeration looks into: out/ holds the uniform variants a build writes, .probe/ the .typ files the test suite compiles inside the Typst root, archives a copy of an export, and git's own.
SKIPPED_FOLDERS = ("out", ".probe", "archives", "__pycache__")
_CHUNK = 1 << 20


# --- where a document's stamp and its deps file are ---------------------------------------

def _name(mode, preview):
    return f"{mode}.preview" if preview else mode


def deps_file(here, mode, preview=False):
    """The file Typst writes what it read into when it compiles document `mode` of project `here` -- `<export>/stamps/<mode>.deps.json`, `<mode>.preview.deps.json` for a preview -- with its folder made. What `documents.compile_args` is given as `deps`, and `record` afterwards as `deps_file`.

    A document `here` does not have (`cu` of a report alone) is a ProjectError, as everywhere else.
    """
    here.document_typ(mode)
    here.stamps_dir.mkdir(parents=True, exist_ok=True)
    return here.stamps_dir / f"{_name(mode, preview)}.deps.json"


def stamp_file(here, mode, preview=False):
    """Where document `mode`'s stamp is: `<export>/stamps/<mode>.json`, `<mode>.preview.json` for a preview. Not made, nor its folder."""
    here.document_typ(mode)
    return here.stamps_dir / f"{_name(mode, preview)}.json"


def read(here, mode, preview=False):
    """Document `mode`'s stamp as it was written, or None -- where there is none, where it cannot be read, where it is another format's or where a field is not what `record` writes. A caller that gets None compiles."""
    try:
        data = json.loads(stamp_file(here, mode, preview).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or data.get("stamp_version") != STAMP_VERSION:
        return None
    for key in ("document", "entry", "pdf", "pdf_sha256", "typst"):
        if not isinstance(data.get(key), str):
            return None
    if not isinstance(data.get("flags"), list) or not isinstance(data.get("inputs"), dict):
        return None
    if data.get("inputs_from") not in (FROM_DEPS, FROM_ENUMERATED):
        return None
    if not all(isinstance(digest, str) for digest in data["inputs"].values()):
        return None
    return data


# --- paths and digests -----------------------------------------------------------------

def _plain(path):
    """A path as Windows' own tools write it: Typst canonicalises, and its deps file holds `\\\\?\\C:\\...` (and `\\\\?\\UNC\\server\\share\\...` for a network drive), which Python accepts and which nothing else compares equal to a plain path."""
    text = str(path)
    if text.startswith("\\\\?\\UNC\\"):
        return "\\\\" + text[8:]
    if text.startswith("\\\\?\\"):
        return text[4:]
    return text


def _same(path):
    """A path as two spellings of one file agree on it: real, and compared as the platform compares names."""
    return os.path.normcase(os.path.realpath(_plain(path)))


def _key(here, path):
    """(the key a stamp keeps `path` under, whether it is in the project): its path from the project's folder with forward slashes for a file of the project, its absolute path with forward slashes for one outside it -- a stamp read on another machine, or after the project moved, names the same files."""
    path = Path(os.path.realpath(_plain(path)))
    try:
        return path.relative_to(here.root.resolve()).as_posix(), True
    except ValueError:
        return path.as_posix(), False


def _locate(here, key):
    """The file a key names: absolute where the key is, else from the project's folder."""
    path = Path(key)
    return path if path.is_absolute() else here.root / key


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _digest(path, inside, info=None):
    """`sha256:<hex>` of a file of the project, `stat:<size>:<mtime_ns>` of one outside it, None where it cannot be read."""
    try:
        if not inside:
            info = info or os.stat(path)
            return f"stat:{info.st_size}:{info.st_mtime_ns}"
        return "sha256:" + _sha256(path)
    except OSError:
        return None


def _write_json(path, data):
    """`data` written whole beside `path` and moved into place, so a file NextCloud syncs is never seen half-written; in UTF-8, with `\\n` whatever the platform, so an unchanged stamp is unchanged to the byte. A file the synchronisation holds for a moment is waited for."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with open(temporary, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    for attempt in range(5):
        try:
            os.replace(temporary, path)
            return
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.1)


# --- what a compile read ---------------------------------------------------------------

def _read_deps(deps, target, base):
    """The absolute paths Typst's deps file lists as read, or None where the file is not one this compile wrote: missing, unreadable, not the shape Typst writes, or naming other outputs than `target` -- a file another compile left behind is not an answer for this one.

    Typst writes a path relative to the folder it was started in wherever it can -- on Linux and macOS always, on Windows only where the `\\\\?\\` spelling lets it not; every compile starts it in the Typst root (`base`, which `documents.compile_args` gives as `--root`), and a relative path is read from there."""
    if deps is None:
        return None
    try:
        data = json.loads(Path(deps).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("inputs"), list):
        return None
    if not all(isinstance(item, str) for item in data["inputs"]):
        return None
    outputs = data.get("outputs")
    if isinstance(outputs, list) and outputs:
        wanted = _same(target)
        if not any(isinstance(item, str) and _same(Path(base) / _plain(item)) == wanted for item in outputs):
            return None
    return [Path(base) / _plain(item) for item in data["inputs"]]


def _walk(folder, skipped=()):
    """Every file under `folder`, in name order, leaving the folders no enumeration looks into (SKIPPED_FOLDERS, git's own, and `skipped`)."""
    skipped = {_same(path) for path in skipped}
    found = []
    for base, dirs, files in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if d not in SKIPPED_FOLDERS and not d.startswith(".git")
                         and _same(Path(base) / d) not in skipped)
        found += [Path(base) / name for name in sorted(files)]
    return found


def enumerated(here, mode):
    """The files document `mode` of project `here` is taken to read where Typst's own list is not there: the .typ files of its folder, config.typ, commands.typ, references.bib and title.typ (in 000-Typst-Config/ laid out by folders), the form's `Template/`, the .typ of every domain, everything under the export's lib/, calc/ and data/ -- never its sources nor its archives, which 000-Woodcore/ holds too --, laid out by folders every file of each tab's Exports/ (the figures) and of Appendix/Exports/, and the pictures. More than the document reads, never less -- which is the side to err on, a stamp saying «changed» costing a compile and one saying «unchanged» a stale PDF."""
    found = {}

    def add(path):
        found.setdefault(_same(path), Path(path))

    generated = here.generated_dir
    for path in _walk(here.document_dir(mode), skipped=(generated,)):
        if path.suffix.lower() == ".typ":
            add(path)
    for path in (here.config_typ, here.commands_typ, here.references_bib, here.title_typ):   # in 000-Typst-Config/ laid out by folders, at the Typst root before
        if path.is_file():
            add(path)
    form = here.template_dir   # the form the documents are set in: template.typ, its assets
    if form.is_dir():
        for path in _walk(form):
            add(path)
    # the domains a document may include: the engineer's own, and laid out by folders one folder per kind of domain (issue #64) -- their archives left out by SKIPPED_FOLDERS
    for folder in [here.formulas_dir] + [here.domain_dir(kind) for kind in project.DOMAIN_FOLDERS if here.has_folders]:
        if folder.is_dir():
            for path in _walk(folder):
                if path.suffix.lower() == ".typ":
                    add(path)
    for folder in GENERATED_READS:
        if (generated / folder).is_dir():
            for path in _walk(generated / folder):
                add(path)
    # laid out by folders, the figures the export writes lie in each tab's Exports/ -- Exports/Figures/, the sheets beside them, the annexes' excerpts in Appendix/Exports/ -- and not in data/ (issue #64, D-10): every file of them
    for folder in [here.exports_dir(kind) for kind in project.FIGURE_KINDS] if here.has_folders else ():
        if folder.is_dir():
            for path in _walk(folder):
                add(path)
    if here.images_dir.is_dir():
        for path in _walk(here.images_dir):
            add(path)
    return sorted(found.values(), key=lambda path: str(path).lower())


def _left_out(here, mode, deps, target):
    """What a stamp never lists as an input: the stamp itself, the deps file, the PDF it is of and the document's own PDF -- they are written by the compile, not read by it."""
    stamp = {_same(stamp_file(here, mode, preview)) for preview in (False, True)}
    files = {_same(target), _same(here.document_pdf(mode))}
    if deps is not None:
        files.add(_same(deps))
    return stamp | files


def record(here, mode, flags, deps_file, target, preview=False):
    """Writes document `mode`'s stamp after a compile of it that worked, and gives back what it wrote (the JSON object of `stamps/<mode>.json`, `<mode>.preview.json` for a preview).

    `flags` are the `--input` flags the compile was given (cli.input_args); `deps_file` the file it was told to write what it read into (`deps_file(here, mode)`, which `documents.compile_args` was given), or None; `target` the PDF it wrote, which is the document's own unless a preview or a level in out/ is meant. The stamp holds `stamp_version` (1), `document`, `entry` and `pdf` (as paths from the project's folder), `pdf_sha256`, `typst` (the version, as `project.typst_version` asks it), `flags`, `inputs_from` (`deps` or `enumerated`, see the module's docstring) and `inputs` -- every file the compile read, in key order, each a digest (`_digest`).

    The stamp, the deps file and the PDF are not among the inputs. An input newer than the PDF is recorded `unsettled` (the module's docstring says why). A FileNotFoundError says the PDF is not there, which a compile that worked does not leave; an OSError from writing is the caller's to swallow -- a document not stamped is one compiled again, which is slow and never wrong.
    """
    target = Path(target)
    entry = here.document_typ(mode)
    target_info = os.stat(target)
    pdf_sha = _sha256(target)
    now = time.time_ns()
    paths = _read_deps(deps_file, target, here.typst_root)
    source = FROM_DEPS
    if paths is None:
        paths, source = enumerated(here, mode), FROM_ENUMERATED
    left_out = _left_out(here, mode, deps_file, target)
    inputs = {}
    for path in paths:
        if _same(path) in left_out:
            continue
        key, inside = _key(here, path)
        if key in inputs:
            continue
        try:
            info = os.stat(path)
        except OSError:
            inputs[key] = UNSETTLED
            continue
        digest = _digest(path, inside, info)
        if digest is None or (inside and target_info.st_mtime_ns < info.st_mtime_ns <= now + CLOCK_SLACK_NS):
            digest = UNSETTLED
        inputs[key] = digest
    stamp = {
        "stamp_version": STAMP_VERSION,
        "document": mode,
        "entry": _key(here, entry)[0],
        "pdf": _key(here, target)[0],
        "pdf_sha256": pdf_sha,
        "typst": project.typst_version(),
        "flags": [str(flag) for flag in flags],
        "inputs_from": source,
        "inputs": dict(sorted(inputs.items())),
    }
    _write_json(stamp_file(here, mode, preview), stamp)
    return stamp


# --- whether the document changed --------------------------------------------------------

def _note(code, text, **args):
    return engine.Note(code, text, **args)


def changed(here, mode, flags, ignore_flags=False, preview=False):
    """Whether document `mode` of project `here` has to be compiled again, as (changed, why) -- `why` an `engine.Note`: the English sentence the command line prints, a `code` and the values beside it (`args`) for the window to write in its own language.

    It has to be, and `why` says which, where: there is no stamp (`stamp_no_record`) or the stamp is another format's; Typst is not the version that compiled it (`stamp_typst`); the flags differ (`stamp_flags`) -- unless `ignore_flags`, which is what asking whether a PDF is *current* and not whether it is the PDF these flags would give (calc/variables.py) means --; the document's entry file or its PDF is not where the stamp has it (`stamp_entry`, `stamp_pdf_place`), the layout having moved; the PDF is gone (`stamp_pdf_missing`) or is not the file the compile wrote (`stamp_pdf_changed`); or an input is gone (`stamp_input_missing`) or has another digest (`stamp_input_changed`) -- the first such file in key order, named in `args["file"]`. After a stamp of enumerated inputs, a file that has appeared in that set (`stamp_input_added`). Otherwise it does not, and `why` is `stamp_unchanged`.

    Nothing is compiled, and a modification time alone changes nothing: a file saved again with the same bytes is unchanged, which is the point. The cost is one `typst --version` and the hashing of the PDF and of every input of the project -- a moment, not a compile.
    """
    stamp = read(here, mode, preview)
    if stamp is None:
        return True, _note("stamp_no_record", f"there is no record of a compile of the {mode} document", document=mode)
    typst = project.typst_version()
    if stamp["typst"] != typst:
        return True, _note("stamp_typst", f"Typst is {typst or 'not installed'}, the {mode} document was compiled with {stamp['typst'] or 'an unknown version'}",
                           document=mode, now=typst, then=stamp["typst"])
    if not ignore_flags and stamp["flags"] != [str(flag) for flag in flags]:
        return True, _note("stamp_flags", f"the {mode} document was compiled with other flags ({' '.join(stamp['flags']) or 'none'}) than now ({' '.join(map(str, flags)) or 'none'})",
                           document=mode, now=[str(flag) for flag in flags], then=stamp["flags"])
    entry = _key(here, here.document_typ(mode))[0]
    if stamp["entry"] != entry:
        return True, _note("stamp_entry", f"the {mode} document's entry file is {entry}, it was compiled from {stamp['entry']}",
                           document=mode, now=entry, then=stamp["entry"])
    if not preview:
        pdf = _key(here, here.document_pdf(mode))[0]
        if stamp["pdf"] != pdf:
            return True, _note("stamp_pdf_place", f"the {mode} document's PDF is {pdf}, it was compiled to {stamp['pdf']}",
                               document=mode, now=pdf, then=stamp["pdf"])
    pdf_path = _locate(here, stamp["pdf"])
    if not pdf_path.is_file():
        return True, _note("stamp_pdf_missing", f"{stamp['pdf']} is missing", document=mode, file=stamp["pdf"])
    try:
        if _sha256(pdf_path) != stamp["pdf_sha256"]:
            return True, _note("stamp_pdf_changed", f"{stamp['pdf']} is not the PDF the last compile wrote", document=mode, file=stamp["pdf"])
    except OSError:
        return True, _note("stamp_pdf_changed", f"{stamp['pdf']} cannot be read", document=mode, file=stamp["pdf"])
    for key, recorded in stamp["inputs"].items():
        path = _locate(here, key)
        inside = not Path(key).is_absolute()
        if not path.is_file():
            return True, _note("stamp_input_missing", f"{key} is missing", document=mode, file=key)
        if _digest(path, inside) != recorded:
            return True, _note("stamp_input_changed", f"{key} changed", document=mode, file=key)
    if stamp["inputs_from"] == FROM_ENUMERATED:
        left_out = {_same(pdf_path), _same(here.document_pdf(mode))}
        now = {}
        for path in enumerated(here, mode):
            if _same(path) not in left_out:
                now.setdefault(_key(here, path)[0], path)
        for key in sorted(set(now) - set(stamp["inputs"])):
            return True, _note("stamp_input_added", f"{key} is new", document=mode, file=key)
    return False, _note("stamp_unchanged", f"the {mode} document is unchanged since its PDF", document=mode)
