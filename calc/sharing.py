"""Sharing a section between the three documents -- the convention d'utilisation (CU), the base de projet (BP) and the rapport de statique (RS) -- and keeping what they share the same (the engineer's decisions of 30.09.2026, phase 5).

**The unit of sharing is the whole file.** Sharing a section copies its `.typ` into the other documents' `Sections/` folders, each copy a file of its own that its document includes like any other. What stays **synchronised** is only what lies between two tags, a line comment each, alone on its line:

    // woodcore:shared <shared-id>
    …any Typst, parametric objects included…
    // woodcore:/shared <shared-id>

**Outside the tags each copy is free** -- a document may keep only the table and drop the heading and the words around it. **Between the tags each copy may be edited freely too**, in VS Code or in Woodcore, and an edit only ever writes the copy of the document it was made in. **Keeping the copies in step is calc/sync.py's** (the rework of 01.10.2026): each document sees what another changed as incoming, what both changed as a conflict, and takes the other version between the tags when the engineer says so -- one document at a time. ⚠️ That replaces the rule of phase 5, «when the block is edited in Woodcore, an alert lists the copies that differ and Woodcore writes its version into every copy»: `plan_sync` and `apply_sync`, which did that, are gone from this module. A copy is found by its tags and by nothing else: the tags are the truth, and `shared_with` in a structure.json is what they say, written down for the tree (`reconcile` writes it again from them).

What this module does, and each of its refusals is a `SharingError` -- a `structure.StructureError`, so whatever catches the catalogue's refusals catches these -- with a `code` (CODES), the `values` it is about and an English sentence; the window writes its own sentence for the code:

- `copies(here, shared_id)` -- every copy of a shared block in the project, in every document's `Sections/`; `index(here)` every copy of every block at once, which calc/sync.py reads.
- `share(here, mode, node_id, targets)` -- a section's file copied into other documents, the copies recorded as in step (calc/sync.py's records of both sides).
- `stop_sharing(here, mode, node_id)` -- this copy's tags taken off, and its record of the block with them.
- `reconcile(here)` -- every structure.json's `shared_with` recomputed from the tags.

**A section is shared as the file it lies in.** The engine works per file -- a file is what a document includes, and a shared block is a stretch of one file -- so a node given by the tree that is a heading inside a file (`live-loads#2`, a sub-section) stands for **its whole file**, as the «Structure document» tab selects everything in the same file. A group has no file and is not shared (`not_a_file`); a heading the report's entry file carries itself is no section (`not_a_section`).

**Where a copy lies, and what it is called** -- in a CU or a BP, `Sections/<id>.typ`, the id the section has in the document it comes from: **the same file name is the same stable id**, which is why a shared section keeps its id (structure.rename_section refuses one). It is added to the target's structure.json at the end of the group of the same id -- else of the same title -- as the one the section stands under where it comes from, and at the end of the document where the target has none (or where that group lies too deep to hold it); the entry's generated block is written again.

**In the report** a copy is `Sections/<id>.typ` too -- **the id as the file's stem, without the three-digit number the report's own sections carry** -- and a line `#include "Sections/<id>.typ"` after the report's last `#include` line, by the rule of structure.add_section (templates.sync_includes). Three reasons for no number: the tree gives a report's section the file's stem for its id, so the copy is known by **one id in the three documents** -- what stop_sharing and the tree's link badge address it by; the number of a report's file stopped saying its place the day sections could be moved (structure.move_node renames nothing); and a number would be a second name for one section, kept in step by nobody. The other way round, a report's file shared into a CU or a BP takes an id there made from its stem with the number taken off (`004-einwirkungen` gives `einwirkungen`), or the one `section_id` names; its shared tags carry that id, and the report's file keeps its own name.

**What the copy is**: the file, byte for byte, but for three things. Its shared tags where it had none: the whole body after its `#import "…commands.typ": *` line is wrapped in `// woodcore:shared <file-id>`, from its first line that is not blank to its last, **in the source too**. Its import line, written as `documents.import_line` has it for the project -- the one spelling valid from every document's folder. And a path that would no longer reach its file from the other document's folder, which is written root-absolute (typst_paths.rewrite): outside the block in the copy alone, inside the block **in every copy, the source included**, the root-absolute spelling being the one that names the same file from every document -- so that the copies start identical between their tags.

Every operation reads everything and checks everything before it writes anything, writes every file beside itself and moves it into place (tried again on the PermissionError NextCloud's client gives on a file it has just seen written), and **puts back what it had written if a later write fails**. Qt-free.
"""

import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

import documents
import structure
import typst_paths
import validation

SECTIONS_DIR = structure.SECTIONS_DIR
# The documents a section may be shared between, in the order they are said: structure.py's.
SHARE_MODES = structure.SHARE_MODES

# Why a sharing refuses, one code each, so that a window can say it in its own words (SharingError.code; `values` names what the refusal is about).
CODES = (
    "bad_mode",               # a document that is none of cu, bp, rs (`mode`)
    "no_such_document",       # the project has no such document: a report laid out alone has no cu and no bp (`mode`)
    "no_targets",             # sharing into no document at all
    "same_document",          # a section shared into the document it lies in (`mode`)
    "no_such_node",           # no section or heading of that id (`id`)
    "not_a_file",             # a group: it has no file, and sharing copies a file (`id`)
    "not_a_section",          # a heading the report's entry file carries itself, not a section file (`id`)
    "file_missing",           # the section's file is not there or cannot be read (`file`)
    "tags_unreadable",        # a file whose tags Woodcore cannot read, which it does not rewrite (`file`, `problems`)
    "bad_id",                 # an id that is not an id: English, lower case, hyphen-separated (`id`)
    "id_exists",              # the target has a section of that id already (`mode`, `id`)
    "file_exists",            # a file lies where the copy would go: nothing is ever overwritten (`mode`, `file`)
    "already_shared",         # the target holds a copy of this section already (`mode`, `file`, `shared_ids`)
    "structure_unreadable",   # a structure.json that cannot be read (`mode`, `error`)
    "entry_unreadable",       # an entry file whose tags cannot be read or that has no structure block (`mode`, `file`)
    "not_shared",             # stopping the sharing of a file that carries no shared tag (`file`)
    "no_copies",              # a shared id no file of the project carries (`shared_id`)
    "bad_block",              # a new block that holds shared or structure tags or pairs no tags (`problems`, `file`) -- what calc/sync.py's write_local refuses
    "changed_meanwhile",      # a file changed between being read and being written: nothing was written, read again (`file`)
    "write_failed",           # the disk refused: what had been written has been put back (`error`)
)


class SharingError(structure.StructureError):
    """A sharing that is refused, said by name: a `code` of CODES, the `values` the refusal is about and an English sentence. A structure.StructureError -- and so a ValidationError -- so whatever catches the catalogue's refusals catches these too."""


def _refuse(code, message, **values):
    raise SharingError(message, code, **values)


# --- reading and writing -------------------------------------------------------------------

def _replace(source, target):
    """`os.replace`, tried again a few times on the PermissionError the sync client of NextCloud gives while it holds a file it has just seen written."""
    for attempt in range(6):
        try:
            return os.replace(source, target)
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(0.1 * (attempt + 1))


def _put(path, data):
    """`data` (bytes) written beside `path` and moved into place: a failed write leaves the old file, and nothing beside it."""
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    try:
        temporary.write_bytes(data)
        _replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except OSError:
            pass


def put(path, data):
    """`data` (bytes) written beside `path` and moved into place -- `_put`, by the name other modules call it (calc/renumbering.py putting a project back from its copy)."""
    return _put(path, data)


def commit(writes):
    """Every write of `writes` -- (path, new bytes, old bytes, or None for a file made new) -- done, or none of them: `_commit`, by the name the other modules call it (calc/renumbering.py, issue #9), rather than a sixth writer of the same few lines. Refuses with a SharingError: `changed_meanwhile`, `file_exists`, `write_failed`. Returns the paths written."""
    return _commit(writes)


def _commit(writes):
    """Every write of `writes` -- (path, new bytes, old bytes, or None for a file made new) -- done, or none of them.

    First every file is checked to hold what was read (`changed_meanwhile` where it does not, and a file to be made new must not be there, `file_exists`), so that nothing is written over an edit made meanwhile. Then the writes are done in order; one that fails puts back, in the opposite order, what was written -- a file made new is taken away again -- and is said as a `write_failed`. Returns the paths written.
    """
    for path, _new, old in writes:
        path = Path(path)
        if old is None:
            if path.exists():
                _refuse("file_exists", f"{path.name}: is there already -- a copy never overwrites a file", file=str(path))
            continue
        try:
            now = path.read_bytes()
        except OSError:
            now = None
        if now != old:
            _refuse("changed_meanwhile", f"{path.name}: changed since it was read -- nothing was written; read it again", file=str(path))
    done = []
    try:
        for path, new, old in writes:
            path = Path(path)
            if old is None:
                path.parent.mkdir(parents=True, exist_ok=True)
            _put(path, new)
            done.append((path, old))
    except Exception as exc:
        for path, old in reversed(done):
            try:
                if old is None:
                    path.unlink()
                else:
                    _put(path, old)
            except Exception:  # broad: an undo that fails must not hide the error being raised, which follows
                pass
        if isinstance(exc, OSError):
            where = Path(exc.filename).name if getattr(exc, "filename", None) else "a file"
            _refuse("write_failed", f"{where}: could not be written ({exc.strerror or exc}) -- what had been written was put back", error=str(exc))
        raise
    return tuple(path for path, _new, _old in writes)


def _read(path):
    """A Typst file's text with its line endings kept (typst_paths.read_text), or None where it cannot be read."""
    try:
        return typst_paths.read_text(path)
    except (OSError, UnicodeDecodeError):
        return None


def _key(path):
    """A path as a key: absolute and in the case Windows compares names in."""
    return os.path.normcase(os.path.abspath(str(path)))


# --- lines, blocks and tags ------------------------------------------------------------------

_LINE = re.compile(r"[^\r\n]*(?:\r\n|\r|\n)|[^\r\n]+")
# The line a section imports the engine with: `#import "/commands.typ": *`, or `"../commands.typ"` in a report laid out alone.
_IMPORT = re.compile(r'^[ \t]*#import[ \t]+"[^"]*commands\.typ"[ \t]*:[ \t]*\*[ \t]*$')
# A shared tag written in a file, read or not: what finds a copy in a file whose tags cannot be paired.
_SHARED_LINE = re.compile(r"^[ \t]*// woodcore:/?shared[ \t]+(\S+)[ \t\r]*$", re.M)


def _lines(text):
    """The lines of `text`, each with its own terminator -- structure.py's split, so a line index here is one there."""
    return _LINE.findall(text)


def _bare(line):
    return line.rstrip("\r\n")


def _ending(line):
    return line[len(_bare(line)):]


def _newline(text):
    """The line ending a file mostly uses: CRLF where it has one, else LF."""
    return "\r\n" if "\r\n" in text else "\n"


def _lf(text):
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _block(text):
    """A block's text as it is compared and written: LF, and ending in a line ending unless it is empty -- the closing tag stands on a line of its own."""
    text = _lf(text or "")
    if text and not text.endswith("\n"):
        text += "\n"
    return text


def _offsets(lines):
    out = [0]
    for line in lines:
        out.append(out[-1] + len(line))
    return out


def _shared_spans(text):
    """(blocks, problems, spans) of `text`: its tags paired (structure.pair_tags), and for every shared block (block, content start, content end, the line ending of its opening tag) -- the content being the characters between the two tag lines, `text[start:end]`."""
    blocks, problems = structure.pair_tags(text)
    lines = _lines(text)
    offsets = _offsets(lines)
    spans = []
    for block in blocks:
        if block.kind != "shared":
            continue
        newline = _ending(lines[block.start]) or _newline(text)
        spans.append((block, offsets[block.start + 1], offsets[block.end], newline))
    return blocks, problems, spans


def _tag(shared_id, closing=False):
    return f"// woodcore:{'/' if closing else ''}shared {shared_id}"


# --- the copies ------------------------------------------------------------------------------

@dataclass(frozen=True)
class Copy:
    """One copy of a shared block: the document it lies in (`mode`), its file, the text between its two tags as the file has it (`block_text`, the file's own line endings), where that text lies in the file's text (`start`, `end`: character offsets, `text[start:end] == block_text`) and the line ending its opening tag's line has, which a block written into it takes."""
    mode: str
    file: Path
    block_text: str
    start: int
    end: int
    newline: str = "\n"


@dataclass(frozen=True)
class _File:
    """A section file of the project as an operation finds it: its document, its path, its text (None where it cannot be read), the shared ids it carries and what is wrong with its tags."""
    mode: str
    path: Path
    text: str
    ids: frozenset
    problems: tuple = ()


def _section_files(here):
    """(mode, path) of every section file of every document of the project: `<document>/Sections/*.typ` -- not the archives beside them, which no document includes."""
    for mode in (m for m in SHARE_MODES if m in here.modes):
        folder = here.document_dir(mode) / SECTIONS_DIR
        if folder.is_dir():
            for path in sorted(folder.glob("*.typ")):
                if path.is_file():
                    yield mode, path


def _file(mode, path, text=None):
    """A `_File` for `path`, read where `text` is None."""
    if text is None:
        text = _read(path)
    if text is None:
        return _File(mode, Path(path), None, frozenset(), ("the file could not be read",))
    if "woodcore:" not in text:
        return _File(mode, Path(path), text, frozenset())
    blocks, problems = structure.pair_tags(text)
    if problems:
        return _File(mode, Path(path), text, frozenset(), tuple(str(p) for p in problems))
    return _File(mode, Path(path), text, frozenset(b.id for b in blocks if b.kind == "shared"))


def _index(here):
    """Every section file of the project, read: what the tags say is shared, and where."""
    return [_file(mode, path) for mode, path in _section_files(here)]


def _mentions(record, shared_id):
    """Whether a file carries a shared tag for `shared_id` -- read from its lines, for a file whose tags cannot be paired."""
    if record.text is None:
        return False
    return shared_id in _SHARED_LINE.findall(record.text)


@dataclass(frozen=True)
class Index:
    """Every shared block of a project at once: the section files read (`files`, each with its text, the shared ids it carries and what is wrong with its tags), {shared id: the copies, in the order of the documents and of the files' names} and {shared id: (mode, path, why) of every file that carries a tag for it but whose tags cannot be read} -- a copy Woodcore neither compares nor writes."""
    files: tuple
    copies: dict
    skipped: dict


def index(here, files=None):
    """The `Index` of project `here`: every section file of every document read once, every copy of every shared block found in them. `files` -- this module's records of the section files, as an operation will make them -- stands for reading them from the disk."""
    files = _index(here) if files is None else list(files)
    found, skipped = {}, {}
    for record in files:
        if record.problems:
            for shared_id in dict.fromkeys(_SHARED_LINE.findall(record.text or "")):
                skipped.setdefault(shared_id, []).append((record.mode, record.path, "; ".join(record.problems)))
            continue
        if not record.ids:
            continue
        _blocks, _problems, spans = _shared_spans(record.text)
        for block, start, end, newline in spans:
            found.setdefault(block.id, []).append(Copy(record.mode, record.path, record.text[start:end], start, end, newline))
    return Index(tuple(files), {k: tuple(v) for k, v in found.items()}, {k: tuple(v) for k, v in skipped.items()})


def copies(here, shared_id):
    """Every copy of the shared block `shared_id` in project `here`: one `Copy` per file of a document's `Sections/` -- the convention's, the base de projet's and the report's -- carrying `// woodcore:shared <shared_id>`, in the order of the documents and of the files' names. A file whose tags cannot be read is none (`index` names it among the skipped)."""
    return list(index(here).copies.get(shared_id, ()))


def _shared_with(mode, ids, files):
    """The documents other than `mode` holding a file that carries one of `ids` -- what `shared_with` says of a leaf whose file carries them, in SHARE_MODES' order."""
    if not ids:
        return []
    modes = {f.mode for f in files if f.mode != mode and f.ids & ids}
    return [m for m in SHARE_MODES if m in modes]


# --- where a section is --------------------------------------------------------------------------

@dataclass(frozen=True)
class _Source:
    mode: str
    path: Path       # the section's file
    rel: str         # its name in its document: Sections/<name>.typ
    stem: str        # its file's stem: a leaf's id (cu, bp), a report's file name (rs)
    node_id: str     # the node given


def _check_mode(here, mode, role="document"):
    if mode not in SHARE_MODES:
        _refuse("bad_mode", f"{role} {mode!r} -- expected one of {', '.join(SHARE_MODES)}", mode=mode)
    if mode not in here.modes:
        _refuse("no_such_document", f"this project has no {mode} document -- it is laid out as a report alone, and migration gives it the three", mode=mode)


def _structure_error(mode, exc):
    """A structure.py refusal said as a sharing's: its own code where it states one (entry_unreadable), structure_unreadable otherwise."""
    code = getattr(exc, "code", "") or "structure_unreadable"
    if code not in CODES:
        code = "structure_unreadable"
    raise SharingError(str(exc), code, mode=mode, error=str(exc), **{k: v for k, v in getattr(exc, "values", {}).items() if k not in ("mode", "error")}) from None


def _locate(here, mode, node_id):
    """The file node `node_id` of document `mode` stands in -- a heading stands for its whole file."""
    try:
        nodes = structure.tree(here, mode)
    except validation.ValidationError as exc:
        _structure_error(mode, exc)
    node = structure.find_node(nodes, node_id) if isinstance(node_id, str) else None
    if node is None:
        known = ", ".join(n.id for n in structure.flatten(nodes) if n.kind != "heading") or "none"
        _refuse("no_such_node", f"document {mode} has no section or heading {node_id!r} -- its sections are {known}", id=node_id)
    if node.kind == "group":
        _refuse("not_a_file", f"{node_id!r} is a group -- it has no file, and a section is shared as the file it lies in", id=node_id)
    rel = node.file or ""
    if not rel.startswith(SECTIONS_DIR + "/"):
        _refuse("not_a_section", f"{node_id!r} is a heading of the entry file itself, not a section file -- only a file of {SECTIONS_DIR}/ is shared", id=node_id)
    path = here.document_dir(mode) / rel
    return _Source(mode, path, rel, Path(rel).stem, node_id)


def id_from_stem(stem):
    """The id a report's file takes in a convention or a base de projet: its stem with the number the report's files begin with taken off, as `templates.slug` writes a title -- `004-einwirkungen` gives `einwirkungen`, `section-` before it where it would still start with a digit."""
    import templates   # here and not at the top: templates imports project, which this module is imported beside
    found = re.match(r"^\d+[-_ ]+(.+)$", stem)
    base = templates.slug(found.group(1) if found else stem)
    if not structure.ID_PATTERN.match(base):
        base = f"section-{base}"
    return base


def _check_id(section_id):
    if not isinstance(section_id, str) or not structure.ID_PATTERN.match(section_id):
        _refuse("bad_id", f"id {section_id!r} is not an id -- English, lower case, letters and digits parted by single hyphens, starting with a letter (live-loads)", id=section_id)
    return section_id


# --- the copy's text -----------------------------------------------------------------------------

def _wrap(text, shared_id):
    """`text` with its body -- everything after its `#import "…commands.typ": *` line, from its first line that is not blank to its last -- between `// woodcore:shared <shared_id>` and its closing tag, in the file's own line ending. A file with no import line among its first lines is wrapped from its start; one whose body is empty gets the two tags, empty, after its import line."""
    lines = _lines(text)
    newline = _newline(text)
    body = 0
    for index, line in enumerate(lines):
        bare = _bare(line).strip()
        if not bare:
            continue
        if _IMPORT.match(_bare(line)):
            body = index + 1
            break
        if bare.startswith("//"):
            continue
        break
    filled = [i for i in range(body, len(lines)) if _bare(lines[i]).strip()]
    lines = list(lines)
    if body and not _ending(lines[body - 1]):
        lines[body - 1] += newline
    if not filled:
        return "".join(lines[:body] + [_tag(shared_id) + newline, _tag(shared_id, True) + newline] + lines[body:])
    first, last = filled[0], filled[-1]
    if not _ending(lines[last]):
        lines[last] += newline
    return "".join(lines[:first] + [_tag(shared_id) + newline] + lines[first:last + 1] + [_tag(shared_id, True) + newline] + lines[last + 1:])


def _with_import(text, line):
    """`text` with its first `#import "…commands.typ": *` line written as `line`, the rest as it was."""
    lines = _lines(text)
    for index, found in enumerate(lines):
        if _IMPORT.match(_bare(found)):
            if _bare(found) != line:
                lines[index] = line + _ending(found)
            return "".join(lines)
    return text


def _edit_literals(text, edits):
    for start, end, value in sorted(edits, reverse=True):
        text = text[:start] + typst_paths._escape(value) + text[end:]
    return text


def _root_absolute_in_blocks(text, source, targets, root):
    """`text` -- the source's, its shared tags in place -- with every path literal inside a shared block that would no longer reach its file from one of `targets` written root-absolute, the one spelling that names the same file from every document (typst_paths.rewrite); and the changes made."""
    _blocks, _problems, spans = _shared_spans(text)
    edits, changes = {}, []
    for target in targets:
        _text, found, _unresolved = typst_paths.rewrite(text, source, target, root, root, {})
        for change in found:
            start = change.literal.start
            if start in edits or not any(a <= start < b for _blk, a, b, _nl in spans):
                continue
            edits[start] = (start, change.literal.end, change.new)
            changes.append(change)
    return _edit_literals(text, edits.values()), changes


# --- the structures --------------------------------------------------------------------------------

@dataclass
class _Structure:
    path: Path
    source: dict
    raw: bytes
    before: str


def _load_structure(here, mode):
    path = here.structure_file(mode)
    try:
        raw = path.read_bytes()
        source = structure.read(path)
    except (OSError, validation.ValidationError) as exc:
        raise SharingError(f"{path.name} of {mode}: could not be read -- {exc}", "structure_unreadable", mode=mode, error=str(exc)) from None
    return _Structure(path, source, raw, structure.dumps(source))


def _restructure(here, files, touched, loaded):
    """`shared_with` of every leaf whose file is in `touched` (keys) written from the tags of `files` -- the section files as they will be. `loaded` holds the structures read so far ({mode: _Structure}), read here where more are needed. Returns the modes whose structure changes."""
    by_key = {_key(f.path): f for f in files}
    for mode in (m for m in structure.MODES if m in here.modes):
        folder = here.document_dir(mode)
        if not any(f.mode == mode and _key(f.path) in touched for f in files):
            continue
        if mode not in loaded:
            loaded[mode] = _load_structure(here, mode)
        for leaf, _depth in structure.leaves(loaded[mode].source):
            key = _key(folder / leaf["file"])
            if key not in touched:
                continue
            record = by_key.get(key)
            if record is None or record.problems:
                continue
            after = _shared_with(mode, record.ids, files)
            if after:
                leaf["shared_with"] = after
            else:
                leaf.pop("shared_with", None)
    return [mode for mode, held in loaded.items() if structure.dumps(held.source) != held.before]


def _structure_writes(loaded, modes):
    writes = []
    for mode in modes:
        held = loaded[mode]
        try:
            structure.check_source(held.source, held.path.name)
        except validation.ValidationError as exc:
            raise SharingError(str(exc), "structure_unreadable", mode=mode, error=str(exc)) from None
        writes.append((held.path, structure.dumps(held.source).encode("utf-8"), held.raw))
    return writes


def _group_for(target_source, parent):
    """The children list of `target_source` a copy goes at the end of: the group of the same id as `parent` (the group the section stands under where it comes from), else of the same title in one of the three languages, where it lies high enough to hold a section -- else the document's top level."""
    if parent is not None:
        candidates = [(node, depth) for node, depth, _p in structure.walk(target_source) if "children" in node]
        found = next(((n, d) for n, d in candidates if n["id"] == parent["id"]), None)
        if found is None:
            titles = {(lang, structure.title_of(parent, lang).strip().casefold()) for lang in structure.LANGUAGES}
            found = next(((n, d) for n, d in candidates
                          if any((lang, structure.title_of(n, lang).strip().casefold()) in titles for lang in structure.LANGUAGES)), None)
        if found is not None and found[1] + 1 <= structure.MAX_DEPTH:
            return found[0]["children"]
    return target_source["sections"]


# --- sharing --------------------------------------------------------------------------------------

@dataclass
class ShareResult:
    """What `share` did: the shared ids the copies carry, the source file, whether its tags were added (`wrapped`) and whether it was rewritten at all, the copies made as (mode, path), the structure.json and entry files rewritten, the path literals rewritten as (file, typst_paths.Change) -- in the source, those inside its shared blocks -- and those left as they were as (file, typst_paths.Unresolved)."""
    shared_ids: tuple
    source: Path
    wrapped: bool
    source_changed: bool
    copies: tuple
    structures: tuple
    entries: tuple
    rewritten: tuple = ()
    unresolved: tuple = ()

    @property
    def modes(self):
        return tuple(mode for mode, _path in self.copies)


def _targets(here, mode, targets):
    if isinstance(targets, str):
        targets = [targets]
    targets = list(dict.fromkeys(targets or ()))
    if not targets:
        _refuse("no_targets", "a section is shared into at least one other document", mode=mode)
    for target in targets:
        _check_mode(here, target, "target document")
        if target == mode:
            _refuse("same_document", f"the section lies in {mode} already -- it is shared into another document", mode=target)
    return [m for m in SHARE_MODES if m in targets]


def share(here, mode, node_id, targets, section_id=None):
    """The section `node_id` of document `mode` shared into the documents `targets` (a mode, or a list of them). Returns a `ShareResult`.

    `node_id` is an id the tree gives (structure.tree): a section file, or a heading inside one, which stands for its whole file -- the engine works per file. **The file is copied** into each target's `Sections/`, **its body wrapped in shared tags where it carries none yet** (`// woodcore:shared <file-id>` … `// woodcore:/shared <file-id>`, from the first line after its import line that is not blank to its last), its import line written for the project (documents.import_line) and a path that would no longer reach its file written root-absolute (see the module's docstring). In a CU or a BP target the copy is `Sections/<id>.typ` and a leaf of structure.json, at the end of the group of the same id -- else the same title -- as the one it stands under at home, else at the end of the document, and the entry's block is written again; in the report it is `Sections/<id>.typ` and an `#include` line after the last one. `<id>` is the section's own id, or for a report's file the id made from its stem (`id_from_stem`) unless `section_id` names another -- which is refused for a section of a CU or a BP, whose id is its file's name. **`shared_with` is written on every side**: of the section itself, of each copy, and of every copy it already had. **And the synchronisation records of both sides** (calc/sync.py's `sync.json`): each copy starts in step with the section it was made from, and stands with a third document holding the block already as that section stands with it -- written in the same commit.

    Refused (SharingError, CODES) before anything is written: a document that is none (`bad_mode`) or that the project lacks (`no_such_document`), no target (`no_targets`), the section's own document (`same_document`), a node that is not there (`no_such_node`), a group (`not_a_file`), a heading of the report's entry file (`not_a_section`), a file that is not there (`file_missing`) or whose tags cannot be read (`tags_unreadable`), an id that is not one (`bad_id`), a target with a section of that id (`id_exists`) or a file of that name (`file_exists`), a target holding a copy already (`already_shared`), a structure.json or an entry that cannot be read (`structure_unreadable`, `entry_unreadable`). A write that fails puts back what was written (`write_failed`).
    """
    _check_mode(here, mode)
    targets = _targets(here, mode, targets)
    source = _locate(here, mode, node_id)
    text = _read(source.path)
    if text is None:
        _refuse("file_missing", f"{source.rel} of {mode}: is not there or cannot be read", file=str(source.path))
    blocks, problems = structure.pair_tags(text)
    if problems:
        _refuse("tags_unreadable", f"{source.rel} of {mode}: Woodcore cannot read the tags of this file, so it does not share it -- " + "; ".join(map(str, problems)),
                file=str(source.path), problems=[str(p) for p in problems])

    loaded = {}
    parent = None
    if mode == "rs":
        carried = list(dict.fromkeys(b.id for b in blocks if b.kind == "shared"))
        if section_id is not None:
            file_id = _check_id(section_id)
        else:
            file_id = _check_id(carried[0] if len(carried) == 1 else id_from_stem(source.stem))
    else:
        file_id = source.stem
        if section_id is not None and section_id != file_id:
            _refuse("bad_id", f"a section of {mode} keeps its id when it is shared ({file_id!r}) -- the same file name is the same section in every document", id=section_id)
        loaded[mode] = _load_structure(here, mode)
        found = structure.find(loaded[mode].source, file_id)
        parent = found[2] if found else None

    wrapped = not any(b.kind == "shared" for b in blocks)
    # the title stays the document's own, outside the block (06.10.2026): two documents place a section they share at different depths, and a heading written at its level could not be the same bytes in both
    new_source = structure.title_out_of_shared(_wrap(text, file_id)) if wrapped else text
    _blocks, problems, _spans = _shared_spans(new_source)
    if problems:
        _refuse("tags_unreadable", f"{source.rel} of {mode}: its body cannot be put between shared tags -- " + "; ".join(map(str, problems)),
                file=str(source.path), problems=[str(p) for p in problems])
    shared_ids = frozenset(b.id for b in _blocks if b.kind == "shared")

    files = _index(here)
    names = {}
    for target in targets:
        folder = here.document_dir(target) / SECTIONS_DIR
        destination = folder / f"{file_id}.typ"
        held = [f for f in files if f.mode == target and (f.ids & shared_ids or (f.problems and any(_mentions(f, i) for i in shared_ids)))]
        if held:
            _refuse("already_shared", f"{target} holds a copy of this section already ({held[0].path.name})", mode=target, file=str(held[0].path), shared_ids=sorted(shared_ids))
        if target == "rs":
            items = structure._rs_items(_entry(here, target))
            if file_id.lower() in {item["name"][:-4].lower() for item in items}:
                _refuse("id_exists", f"the report has a section {file_id!r} already", mode=target, id=file_id)
        else:
            if target not in loaded:
                loaded[target] = _load_structure(here, target)
            if structure.find(loaded[target].source, file_id) is not None:
                _refuse("id_exists", f"{target} has a section {file_id!r} already -- a shared section keeps its id in every document", mode=target, id=file_id)
        if destination.exists():
            _refuse("file_exists", f"{SECTIONS_DIR}/{destination.name} of {target}: is there already -- a copy never overwrites a file", mode=target, file=str(destination))
        names[target] = destination

    root = here.typst_root
    canonical, inside = _root_absolute_in_blocks(new_source, source.path, list(names.values()), root)
    rewritten = [(source.path, change) for change in inside]
    unresolved = []
    copies_text = {}
    import_line = documents.import_line(here)
    for target, destination in names.items():
        copy_text, changes, left = typst_paths.rewrite(canonical, source.path, destination, root, root, {})
        rewritten += [(destination, change) for change in changes]
        unresolved += [(destination, why) for why in left]
        copies_text[target] = _with_import(copy_text, import_line)

    # the structures and the entries, as they will be
    writes, entries = [], []
    for target, destination in names.items():
        entry = here.document_typ(target)
        entry_text = _entry(here, target)
        if target == "rs":
            items = structure._rs_items(entry_text)
            items.append({"id": file_id, "name": f"{file_id}.typ", "comment": "", "body": f'#include "{SECTIONS_DIR}/{file_id}.typ"'})
            new_entry = structure._rs_lay_out(entry_text, items)
        else:
            target_source = loaded[target].source
            _group_for(target_source, parent).append({"id": file_id, "file": structure.section_file(file_id), "enabled": True})
            # the copy's title at the level its place prints it at -- the depth in a document that writes its headings so, level 1 in one laid out with offsets
            placed = structure.find(target_source, file_id)
            level = placed[1] if placed is not None and structure.is_absolute(target_source) else 1
            copies_text[target] = structure.fit_text(copies_text[target], level)
            try:
                structure.check_source(target_source, loaded[target].path.name)
                new_entry = structure._entry_text(entry.name, entry_text, structure.block_lines(target_source, structure.document_language(here, target)))
            except validation.ValidationError as exc:
                _structure_error(target, exc)
        if new_entry is not None and new_entry != entry_text:
            writes.append((entry, new_entry.encode("utf-8"), entry_text.encode("utf-8")))
            entries.append(entry)
        writes.insert(0, (destination, copies_text[target].encode("utf-8"), None))

    after = [f for f in files if _key(f.path) != _key(source.path)] + [_file(mode, source.path, canonical)]
    after += [_file(target, destination, copies_text[target]) for target, destination in names.items()]
    touched = {_key(f.path) for f in files if f.ids & shared_ids} | {_key(f.path) for f in after if f.ids & shared_ids}
    changed = _restructure(here, after, touched, loaded)
    writes += _structure_writes(loaded, changed)
    source_changed = canonical != text
    if source_changed:
        writes.append((source.path, canonical.encode("utf-8"), text.encode("utf-8")))
    import sync   # here and not at the top: sync reads this module
    writes += sync.share_writes(here, mode, shared_ids, after, list(names))
    _commit(writes)
    return ShareResult(tuple(sorted(shared_ids)), source.path, wrapped, source_changed, tuple(names.items()),
                       tuple(loaded[m].path for m in changed), tuple(entries), tuple(rewritten), tuple(unresolved))


def _entry(here, mode):
    entry = here.document_typ(mode)
    text = _read(entry)
    if text is None:
        _refuse("entry_unreadable", f"{entry.name} of {mode}: could not be read", mode=mode, file=str(entry))
    return text


# --- a block written by hand into a copy ---------------------------------------------------------

# ⚠️ Superseded (the engineer's rework of 01.10.2026): `plan_sync` and `apply_sync`, which wrote a block edited in Woodcore into **every** copy after an alert listing the copies that differed, are gone. A block is written into the copy of the document it is edited in and nowhere else, and the other documents see it as incoming (calc/sync.py: `status`, `import_changes`, `write_local`). What stays here is the check a block written into a copy must pass.

def _check_block(new_block):
    """Refuses (`bad_block`) a block that is not text, that holds a shared or a structure tag -- a shared block holds objects and nothing else that is tagged -- or whose object tags do not pair: what calc/sync.py's write_local writes between a copy's two tags."""
    if not isinstance(new_block, str):
        _refuse("bad_block", "a block is text", problems=["not text"])
    blocks, problems = structure.pair_tags(new_block)
    problems = [str(p) for p in problems] + [f"line {b.start + 1}: {b.kind} tags cannot stand inside a shared block" for b in blocks if b.kind != "object"]
    if problems:
        _refuse("bad_block", "the block cannot be written into the copy -- " + "; ".join(problems), problems=problems)


# --- stopping the sharing ------------------------------------------------------------------------

@dataclass
class StopResult:
    """What `stop_sharing` did: the file whose tags were taken off, the shared ids it carried, `also_unshared` -- (mode, path, shared id) of each copy left alone with one of those blocks, whose tags were taken off too since it shares with nobody now -- and the structure.json files rewritten, and `skipped`, (mode, path, why) of copies whose tags cannot be read and that were not touched."""
    file: Path
    shared_ids: tuple
    also_unshared: tuple
    structures: tuple
    skipped: tuple = ()


def _untag(text, shared_ids):
    """`text` with the tag lines of its shared blocks `shared_ids` taken out -- what was between them left as it was."""
    blocks, _problems = structure.pair_tags(text)
    drop = set()
    for block in blocks:
        if block.kind == "shared" and block.id in shared_ids:
            drop.update((block.start, block.end))
    return "".join(line for index, line in enumerate(_lines(text)) if index not in drop)


def stop_sharing(here, mode, node_id):
    """The section `node_id` of document `mode` shared no more: **this copy's shared tags are taken off**, what lay between them kept, and `shared_with` written again on every side. Returns a `StopResult`.

    `node_id` is the tree's id of the section's file, or of a heading in it (which stands for the file). The other copies of each block stay shared among themselves **where two or more of them remain**; where only one does, it shares with nobody any more, and its tags are taken off too -- said in `also_unshared`. Each copy whose tags are taken off has its synchronisation record of the block dropped with them (calc/sync.py's `sync.json`, its ignore flags included), in the same commit. Refused: what `share` refuses of a node (`bad_mode`, `no_such_document`, `no_such_node`, `not_a_file`, `not_a_section`, `file_missing`, `tags_unreadable`) and a file that carries no shared tag (`not_shared`); a write that fails puts back what was written (`write_failed`).
    """
    _check_mode(here, mode)
    source = _locate(here, mode, node_id)
    text = _read(source.path)
    if text is None:
        _refuse("file_missing", f"{source.rel} of {mode}: is not there or cannot be read", file=str(source.path))
    record = _file(mode, source.path, text)
    if record.problems:
        _refuse("tags_unreadable", f"{source.rel} of {mode}: Woodcore cannot read the tags of this file, so it does not rewrite it -- " + "; ".join(record.problems),
                file=str(source.path), problems=list(record.problems))
    ids = record.ids
    if not ids:
        _refuse("not_shared", f"{source.rel} of {mode}: carries no shared block -- it is shared with no other document", file=str(source.path))

    files = _index(here)
    overrides = {_key(source.path): (mode, source.path, text, _untag(text, ids))}
    also, skipped = [], []
    for shared_id in sorted(ids):
        rest = [f for f in files if _key(f.path) != _key(source.path) and shared_id in f.ids]
        skipped += [(f.mode, f.path, "; ".join(f.problems)) for f in files if f.problems and _mentions(f, shared_id)]
        if len(rest) == 1:
            other = rest[0]
            key = _key(other.path)
            current = overrides[key][3] if key in overrides else other.text
            overrides[key] = (other.mode, other.path, other.text, _untag(current, {shared_id}))
            also.append((other.mode, other.path, shared_id))

    after = [f for f in files if _key(f.path) not in overrides]
    after += [_file(m, p, new) for m, p, _old, new in overrides.values()]
    touched = {_key(f.path) for f in files if f.ids & ids} | set(overrides)
    loaded = {}
    changed = _restructure(here, after, touched, loaded)
    writes = [(p, new.encode("utf-8"), old.encode("utf-8")) for _m, p, old, new in overrides.values() if new != old]
    writes += _structure_writes(loaded, changed)
    import sync   # here and not at the top: sync reads this module
    writes += sync.stop_writes(here, [(mode, i) for i in ids] + [(m, i) for m, _p, i in also])
    _commit(writes)
    return StopResult(source.path, tuple(sorted(ids)), tuple(also), tuple(loaded[m].path for m in changed), tuple(dict.fromkeys(skipped)))


# --- reconciling --------------------------------------------------------------------------------

@dataclass(frozen=True)
class Difference:
    """A leaf whose `shared_with` said otherwise than the tags: its document, its id, what structure.json said and what the tags say."""
    mode: str
    id: str
    before: tuple
    after: tuple


@dataclass
class ReconcileResult:
    """What `reconcile` found: every `Difference`, the structure.json files written, and what it could not settle, said by name -- a structure.json that cannot be read, a leaf whose file is missing or whose tags cannot be read (its `shared_with` left as it was)."""
    changes: tuple
    written: tuple
    problems: tuple

    @property
    def changed(self):
        return bool(self.changes)


def reconcile(here, write=True):
    """`shared_with` of every leaf of every structure.json of project `here` written again from the tags actually present -- **the tags are the truth**: a leaf's file that carries shared ids is shared with every other document holding a file that carries one of them, and a file that carries none is shared with nobody. Returns a `ReconcileResult` naming each difference; `write=False` says them and writes nothing. A leaf whose file is missing, or whose tags cannot be read, keeps what it said, and the result says why; so does a structure.json that cannot be read. The report has no structure.json and nothing is written for it, its tree reading the tags itself.
    """
    files = _index(here)
    by_key = {_key(f.path): f for f in files}
    changes, written, problems = [], [], []
    for mode in (m for m in structure.MODES if m in here.modes):
        try:
            held = _load_structure(here, mode)
        except SharingError as exc:
            problems.append(str(exc))
            continue
        folder = here.document_dir(mode)
        for leaf, _depth in structure.leaves(held.source):
            record = by_key.get(_key(folder / leaf["file"]))
            before = list(leaf.get("shared_with", ()))
            if record is None:
                problems.append(f"{mode}, section {leaf['id']!r}: {leaf['file']} is not there -- what structure.json says of its sharing is left as it was")
                continue
            if record.problems:
                problems.append(f"{mode}, section {leaf['id']!r}: the tags of {leaf['file']} cannot be read -- " + "; ".join(record.problems))
                continue
            after = _shared_with(mode, record.ids, files)
            if after != before:
                changes.append(Difference(mode, leaf["id"], tuple(before), tuple(after)))
                if after:
                    leaf["shared_with"] = after
                else:
                    leaf.pop("shared_with", None)
        if write and structure.dumps(held.source) != held.before:
            _commit(_structure_writes({mode: held}, [mode]))
            written.append(held.path)
    return ReconcileResult(tuple(changes), tuple(written), tuple(problems))
