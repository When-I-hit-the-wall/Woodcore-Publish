"""Content brought from another document of the project, and objects moved inside one (the three document modes, the rework of 01.10.2026: «Importer depuis un autre document du projet» and the drag and drop of the «Structure du document» tab).

**Importing.** The engineer chooses a document -- the convention d'utilisation (cu), the base de projet (bp) or the report (rs) -- and gets a tree of its sections and, under each, the parametric objects its file holds (`importable`); he ticks what he wants and `import_items` brings it into the document he works in:

- **whole sections** arrive **at the bottom of the tree**: a leaf at the end of the top level of a CU's or a BP's structure.json, an `#include` line after the report's last one;
- **objects imported alone** arrive in a section of their own, **«Importé»** (`imported` -- Importiert, Imported -- the id is English and stable, the heading is in the document's language), created at the bottom when the document has none and written to where it already is when it has: each object is appended at the end of its file, a blank line between two. Drag and drop then places them (`move_object`, `move_section`).
- **A section and some of its objects both ticked: the section wins** -- the objects are not imported a second time, and `Result.skipped` says so.

**Linked, or a copy of one's own.** What is imported stays **linked** unless the engineer ticks «copie indépendante» (`linked=False`):

- A whole section is shared (sharing.share): its file is copied, its body wrapped in shared tags in the source and in the copy, the same file name in both documents -- so the engineer's later edit in one document turns the other orange (calc/sync.py), and `shared_with` is written on both sides. Where the section carries a name the target already has, the import is refused (`id_exists`): a shared section keeps its id.
- An object alone is **wrapped in shared tags in both files** -- the source file and the copy -- `// woodcore:shared <id>` … `// woodcore:/shared <id>` around the object's own two tags, and the shared id is **derived from the object's id and unique in the whole project** (`<object id>`, then `-2`, `-3`, …). An object that is alone in a shared block already is shared under that block's id and the block is copied as it stands. An object that stands inside a **larger** shared block (the whole body of a shared section, say) is **already linked through that block**: a linked import of it alone is refused (`inside_shared`, naming the block) -- import the section, or tick «copie indépendante». **The object's id is the same in every copy of its block** (the synchronisation compares the objects of a block by id), so where the destination file holds that id already -- two sections of a template each have a `title` and a `p1` -- the object takes a fresh one (`title-2`) **in the source and in the copy**; an object that is a shared block alone already cannot be renamed, and is refused (`id_exists`). The block between the tags is identical in both files from the start: a path in it that would no longer reach its file from the other folder is written root-absolute in the copy **and in the source** (the sharing module's own rule, typst_paths.rewrite).
- **An independent copy** carries no shared tag at all: a section's file is copied with its shared tags taken out and a fresh id (`live-loads-2` where the target has `live-loads`, a report's next numbered file name), and an object is appended to «Importé» without the shared tags it might have stood in, under an object id free in the file -- its own where free, else `-2`, `-3` ….

**Moving.** `move_object` moves one tagged object -- with its tags, **and with its shared tags where the object alone is a shared block** -- inside its file or into another file of the same document, above or below an object, or to the end of the file. An object that stands inside a **larger** shared block cannot leave it (`leaves_shared_block`: that block is what the other documents' copies hold; it may be reordered inside, which is an edit of the shared block like any other in Woodcore, and `Result.shared_changed` names it), and a shared block alone cannot be put inside another (`nested_shared`). Everything else in both files stays byte for byte. `move_section` is calc/structure.py's `move_node`, the one operation that moves a section anywhere in the tree.

**Every operation is all or nothing.** Everything is read and checked before anything is written; the writes are made beside each file and moved into place (tried again on the PermissionError the sync client of NextCloud gives on a file it has just seen written), and what the operations of the structure and the sharing modules write -- structure.json, the entry files, the section files -- is **taken back by a snapshot** if any later step fails: a refusal or a failure leaves the project as it was. Line endings are kept: what is written into a file takes its own, a CRLF file stays CRLF.

**calc/sync.py is told what it needs to know.** A linked import makes copies that start in step with their source (`_record_copies`: what sharing.share does for a section, for an object); a move that reorders the objects of a shared block, or puts one into it, is an edit of that block, made in this document alone -- `sync.record_local_edit` is called with the block as it stood, so that the block shows as local here and incoming in the other documents and not as a conflict. A record that cannot be written does not undo the import or the move: the shared ids are in `Result.unrecorded`, and the copies are in place.

Qt-free. Every refusal is a `DocImportError` -- a `structure.StructureError`, so whatever catches the catalogue's and the sharing's catches these -- with a `code` (CODES), the `values` it is about and an English sentence; the window writes its own sentence for the code. The refusals of the operations this module calls (`structure.CODES`, `sharing.CODES`) pass through as they are.
"""

import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

import documents
import sharing
import structure
import typst_paths

SECTIONS_DIR = structure.SECTIONS_DIR

# The section objects imported alone go into: an English, stable id, and its heading in the document's own language.
IMPORTED_ID = "imported"
IMPORTED_TITLES = {"fr": "Importé", "de": "Importiert", "en": "Imported"}

# What an item of the tree is.
KIND_GROUP = "group"
KIND_SECTION = "section"
KIND_OBJECT = "object"
KINDS = (KIND_GROUP, KIND_SECTION, KIND_OBJECT)

# Why an operation refuses, one code each, so that a window can say it in its own words (DocImportError.code; `values` names what the refusal is about).
CODES = (
    "bad_mode",               # a document that is none of cu, bp, rs (`mode`)
    "no_such_document",       # the project has no such document: a report laid out alone has no cu and no bp (`mode`)
    "same_document",          # importing from the document one works in (`mode`)
    "no_items",               # nothing to import
    "bad_item",               # an item that is none of a section, a group or an object (`item`)
    "no_such_node",           # no section or group of that id (`id`)
    "not_a_section",          # a node that is not a section file, for an object's section (`id`)
    "no_such_object",         # no object of that id in the file (`id`, `file`)
    "file_missing",           # a section's file is not there or cannot be read (`file`)
    "tags_unreadable",        # a file whose tags Woodcore cannot read, which it does not rewrite (`file`, `problems`)
    "inside_shared",          # a linked import of an object that stands inside a larger shared block (`id`, `shared_id`)
    "already_shared",         # the target document holds a copy of that shared block already (`mode`, `shared_id`, `file`)
    "id_exists",              # the destination file holds an object of that id and the one to import is a shared block alone, whose id cannot change (`id`, `file`)
    "imported_not_a_section", # `imported` is a group in the target: the objects have no file to go into (`id`)
    "bad_place",              # a move above and below at once (`before`, `after`)
    "leaves_shared_block",    # an object of a larger shared block moved out of it (`id`, `shared_id`)
    "nested_shared",          # a shared block alone moved into another shared block (`id`, `shared_id`)
    "changed_meanwhile",      # a file changed between being read and being written: nothing was written, try again (`file`)
    "write_failed",           # the disk refused: what had been written has been put back (`error`)
)


class DocImportError(structure.StructureError):
    """A refusal of this module, said by name: a `code` of CODES, the `values` it is about and an English sentence. A structure.StructureError -- and so a ValidationError."""


def _refuse(code, message, **values):
    raise DocImportError(message, code, **values)


# --- lines, texts and files ------------------------------------------------------------------------------

_LINE = re.compile(r"[^\r\n]*(?:\r\n|\r|\n)|[^\r\n]+")
# The line a section imports the engine with, and a shared tag line, read or not paired.
_IMPORT = re.compile(r'^[ \t]*#import[ \t]+"[^"]*commands\.typ"[ \t]*:[ \t]*\*[ \t]*$')
_SHARED_TAG = re.compile(r"^[ \t]*// woodcore:/?shared[ \t]+(\S+)[ \t\r]*$")
_ENDING = re.compile(r"\r\n|\r|\n")


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


def _normalise(text, newline):
    """`text` with every line ending made `newline`, and ending in one."""
    text = _ENDING.sub(newline, text)
    if text and not text.endswith(newline):
        text += newline
    return text


def _blank(line):
    return not line.strip()


def _key(path):
    """A path as a key: absolute and in the case Windows compares names in."""
    return os.path.normcase(os.path.abspath(str(path)))


def _read(path):
    """A Typst file's text with its line endings kept, or None where it cannot be read."""
    try:
        return typst_paths.read_text(path)
    except (OSError, UnicodeDecodeError):
        return None


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


def _commit(writes):
    """Every write of `writes` -- (path, new bytes, old bytes) -- done, or none of them.

    First every file is checked to hold what was read (`changed_meanwhile` where it does not: nothing is written over an edit made meanwhile). Then the writes are done in order; one that fails puts back, in the opposite order, what was written, and is said as a `write_failed`. Returns the paths written.
    """
    for path, _new, old in writes:
        try:
            now = Path(path).read_bytes()
        except OSError:
            now = None
        if now != old:
            _refuse("changed_meanwhile", f"{Path(path).name}: changed since it was read -- nothing was written; read it again", file=str(path))
    done = []
    try:
        for path, new, old in writes:
            _put(path, new)
            done.append((path, old))
    except Exception as exc:
        for path, old in reversed(done):
            try:
                _put(path, old)
            except Exception:  # broad: an undo that fails must not hide the error being raised, which follows
                pass
        if isinstance(exc, OSError):
            where = Path(exc.filename).name if getattr(exc, "filename", None) else "a file"
            _refuse("write_failed", f"{where}: could not be written ({exc.strerror or exc}) -- what had been written was put back", error=str(exc))
        raise
    return tuple(Path(path) for path, _new, _old in writes)


def _disk(exc):
    """A failure of the disk -- an OSError from anywhere in an operation -- said as a `write_failed`, once what was written has been put back; any other exception is left to be raised as it is."""
    if isinstance(exc, OSError):
        where = Path(exc.filename).name if getattr(exc, "filename", None) else "a file"
        _refuse("write_failed", f"{where}: could not be written ({exc.strerror or exc}) -- what had been written was put back", error=str(exc))


# --- a file as an operation reads it ------------------------------------------------------------------

@dataclass(frozen=True)
class _Unit:
    """What moves with an object: the lines `start` to `end` (0-based, the tag lines included) -- its own two tags, or the shared tags around it where it is alone in a shared block (`shared` then names that block). `inside` is the id of the **larger** shared block the object stands in, where it does; `block` the object's own block."""
    start: int
    end: int
    shared: str
    inside: str
    block: structure.Block


class _Doc:
    """A section file read: its text, its lines, its tags paired."""

    def __init__(self, path, text):
        self.path = Path(path)
        self.text = text
        self.lines = _lines(text)
        self.newline = _newline(text)
        self.blocks, self.problems = structure.pair_tags(text) if "woodcore:" in text else ([], [])

    def with_lines(self, lines):
        return _Doc(self.path, "".join(lines))

    def objects(self):
        return [b for b in self.blocks if b.kind == "object"]

    def object(self, object_id):
        return next((b for b in self.blocks if b.kind == "object" and b.id == object_id), None)

    def shared_ids(self):
        return {b.id for b in self.blocks if b.kind == "shared"}

    def larger(self, block):
        """The shared block `block` stands inside, or None."""
        return next((s for s in self.blocks if s.kind == "shared" and s.start < block.start and block.end < s.end), None)

    def alone(self, shared, block):
        """Whether the shared block holds nothing but the object `block` -- white space aside."""
        for index in range(shared.start + 1, shared.end):
            if block.start <= index <= block.end:
                continue
            if self.lines[index].strip():
                return False
        return True

    def unit(self, object_id):
        block = self.object(object_id)
        if block is None:
            return None
        around = self.larger(block)
        if around is not None and self.alone(around, block):
            return _Unit(around.start, around.end, around.id, None, block)
        if around is not None:
            return _Unit(block.start, block.end, None, around.id, block)
        return _Unit(block.start, block.end, None, None, block)

    def block_text(self, start, end):
        return "".join(self.lines[start:end + 1])

    def shared_text(self, shared_id):
        """What lies between the two tags of the shared block `shared_id`, as written -- the block calc/sync.py compares."""
        block = next((b for b in self.blocks if b.kind == "shared" and b.id == shared_id), None)
        return "".join(self.lines[block.start + 1:block.end]) if block is not None else ""


def _check_doc(doc, where):
    if doc.problems:
        _refuse("tags_unreadable", f"{where}: Woodcore cannot read the tags of this file, so it does not rewrite it -- " + "; ".join(str(p) for p in doc.problems),
                file=str(doc.path), problems=[str(p) for p in doc.problems])


def _open(path, where):
    """The `_Doc` of the file at `path`, refused where it cannot be read or its tags cannot be paired."""
    text = _read(path)
    if text is None:
        _refuse("file_missing", f"{where}: is not there or cannot be read", file=str(path))
    doc = _Doc(path, text)
    _check_doc(doc, where)
    return doc


def _tag_line(shared_id, closing, newline):
    return f"// woodcore:{'/' if closing else ''}shared {shared_id}{newline}"


def _wrap(lines, start, end, shared_id, newline):
    """`lines` with the lines `start` to `end` between shared tags for `shared_id`, each on a line of its own."""
    out = list(lines[:start]) + [_tag_line(shared_id, False, newline)] + list(lines[start:end + 1])
    if not _ending(out[-1]):
        out[-1] += newline
    out.append(_tag_line(shared_id, True, newline))
    out += lines[end + 1:]
    return out


def _open_tag(line):
    """Whether `line` is the opening tag of a shared block, which an object lies tight against."""
    found = _SHARED_TAG.match(_bare(line))
    return bool(found) and "woodcore:shared" in line


def _close_tag(line):
    found = _SHARED_TAG.match(_bare(line))
    return bool(found) and "woodcore:/shared" in line


def _cut(lines, start, end):
    """`lines` without the lines `start` to `end` -- and with one blank line less where the cut leaves two together, or leaves a blank line at the start or the end of the file or against a shared tag."""
    lines = list(lines)
    count = len(lines)
    before = start > 0 and _blank(lines[start - 1])
    after = end + 1 < count and _blank(lines[end + 1])
    top = start == 0 or _open_tag(lines[start - 1])
    bottom = end + 1 >= count or _close_tag(lines[end + 1])
    del lines[start:end + 1]
    if before and after:
        del lines[start]
    elif before and bottom:
        del lines[start - 1]
    elif after and top:
        del lines[start]
    return lines


def _place(lines, index, block, newline):
    """`lines` with `block` (text ending in a line ending) inserted before line `index`, one blank line between it and a line of text on either side -- none against the tag of a shared block, which an object lies tight against."""
    lines = list(lines)
    previous = lines[index - 1] if index > 0 else None
    following = lines[index] if index < len(lines) else None
    out = []
    if previous is not None:
        if not _ending(previous):
            lines[index - 1] = previous + newline
        if not _blank(previous) and not _open_tag(previous):
            out.append(newline)
    out.append(block)
    if following is not None and not _blank(following) and not _close_tag(following):
        out.append(newline)
    lines[index:index] = out
    return lines


def _with_import(text, line):
    """`text` with its first `#import "…commands.typ": *` line written as `line`, the rest as it was."""
    lines = _lines(text)
    for index, found in enumerate(lines):
        if _IMPORT.match(_bare(found)):
            if _bare(found) != line:
                lines[index] = line + _ending(found)
            return "".join(lines)
    return text


def _without_shared_tags(text):
    """`text` without its shared tag lines -- what lay between them kept, as it is."""
    return "".join(line for line in _lines(text) if not _SHARED_TAG.match(_bare(line)))


def _rename_object(block_lines, old, new):
    """The lines of an object (its tags included) with its id `old` written `new` in both tags."""
    lines = list(block_lines)
    opening = re.compile(r"^([ \t]*// woodcore:object[ \t]+\S+[ \t]+)" + re.escape(old) + r"([ \t\r\n]*)$")
    closing = re.compile(r"^([ \t]*// woodcore:/object[ \t]+)" + re.escape(old) + r"([ \t\r\n]*)$")
    lines[0] = opening.sub(lambda m: m.group(1) + new + m.group(2), lines[0])
    lines[-1] = closing.sub(lambda m: m.group(1) + new + m.group(2), lines[-1])
    return lines


# --- a snapshot, to take back what the other modules wrote ------------------------------------------------

SYNC_FILE = "sync.json"


def _watched(here):
    """The files an operation of the structure, the sharing and the synchronisation modules may write: every document's entry file and structure.json, the record of its sharing (`sync.json`, calc/sync.py) where it has one, and the section files in its `Sections/` -- not the archives beside them."""
    out = []
    for mode in here.modes:
        out.append(Path(here.document_typ(mode)))
        if mode in structure.MODES:
            out.append(Path(here.structure_file(mode)))
        record = Path(here.document_dir(mode)) / SYNC_FILE
        if record.is_file():
            out.append(record)
        folder = Path(here.document_dir(mode)) / SECTIONS_DIR
        if folder.is_dir():
            out += sorted(p for p in folder.glob("*.typ") if p.is_file())
    return out


class _Snapshot:
    """The bytes of every watched file of the project, taken before an operation: `restore` puts every one back, takes away the files made since and the beside-files a write left."""

    def __init__(self, here):
        self.here = here
        self.files = {}
        for path in _watched(here):
            try:
                self.files[_key(path)] = (path, path.read_bytes())
            except OSError:
                pass

    def _now(self):
        return {_key(p): p for p in _watched(self.here)}

    def changed(self):
        """The paths that differ from what was taken, or are new, in the order they lie."""
        out = []
        for key, path in self._now().items():
            held = self.files.get(key)
            try:
                data = path.read_bytes()
            except OSError:
                continue
            if held is None or held[1] != data:
                out.append(path)
        return tuple(out)

    def restore(self):
        for key, (path, data) in self.files.items():
            try:
                if not path.exists() or path.read_bytes() != data:
                    _put(path, data)
            except OSError:
                pass
        for key, path in self._now().items():
            if key not in self.files:
                try:
                    path.unlink()
                except OSError:
                    pass
        for path, _data in self.files.values():
            for leftover in (path.with_name(path.name + ".tmp"), path.with_name(path.name + ".part")):
                try:
                    leftover.unlink()
                except OSError:
                    pass


# --- the items --------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Item:
    """One row of the tree the import dialog shows: a `group` (a chapter of a CU or a BP: ticking it ticks every section under it), a `section` (a file) or an `object` (a tagged object of a file).

    `mode` the document it is in; `id` its id -- a group's or a section's id in the document's tree (calc/structure.py's `tree`: the structure id of a CU's or a BP's, the file's stem of the report's), an object's id in its file; `title` what a row shows -- the plain words of the first heading of a section, the label of an object (its caption, its own words, else its first line); `section` the id of the section it is, or of the one an object lies in; `parent` the id of the group above; `file` the file, relative to the document's folder; `object_type` the call an object is (`doc-table`); `shared_id` the shared block an object stands in -- `alone` saying it is that block's only content, which a linked import can then share as it stands, where a larger block refuses it --; `shared_ids` and `shared_with` what a section's file carries and the documents it is shared with; `enabled`, `problems` as the tree says them; `children` the items under it -- sections and groups under a group, objects under a section."""
    kind: str
    mode: str
    id: str
    title: str = ""
    section: str = None
    parent: str = None
    file: str = None
    object_type: str = None
    shared_id: str = None
    alone: bool = False
    shared_ids: tuple = ()
    shared_with: tuple = ()
    enabled: bool = True
    problems: tuple = ()
    children: tuple = ()

    def ref(self):
        """What identifies the item -- `(kind, section id, id)` -- whether it is the dialog's own or one a caller writes."""
        return (self.kind, self.section if self.kind == KIND_OBJECT else self.id, self.id)


def flatten(items):
    """The items of `items` and of their subtrees, in document order (an item before its children)."""
    out = []
    for item in items:
        out.append(item)
        out += flatten(item.children)
    return out


_LABEL_ARGS = ("caption", "label", "title", "text", "body", "file", "plan")


def _display(value):
    """What a value of a call says as words: a string, or the markup of a content block -- None for anything else."""
    markup = getattr(value, "markup", None)
    if isinstance(markup, str):
        value = markup
    if isinstance(value, str):
        return " ".join(value.split())
    return None


def _shorten(text, length=60):
    text = " ".join(text.split())
    return text if len(text) <= length else text[:length - 1].rstrip() + "…"


def _label(doc, block):
    """The words a row of the tree shows for an object: the first of its caption, label, title, text, … that is words, else the first line of its body, else its type."""
    body = "".join(doc.lines[block.start + 1:block.end])
    found = None
    try:
        import typst_objects
        call = typst_objects.parse_call(body)
        for name in _LABEL_ARGS:
            found = _display(call.args.get(name))
            if found:
                break
    except (ImportError, ValueError):   # a body typst_objects cannot read (ParseError): its first line stands in
        found = None
    if not found:
        for line in body.splitlines():
            line = line.strip()
            if line and not line.startswith("//"):
                found = re.sub(r"^[=#\s]+", "", line)
                break
    return _shorten(found) if found else (block.type or block.id)


def _titles(doc):
    """{object id: its label} as calc/typst_objects.py words it for the tree (`object_title`: a heading's title, a paragraph's first words, a table's caption …) -- empty where that module cannot read the file, `_label` then standing in."""
    try:
        import typst_objects
        return {o.id: typst_objects.object_title(o) for o in typst_objects.scan(doc.text)[0]}
    except (ImportError, ValueError):   # a file typst_objects cannot read (ParseError): `_label` stands in
        return {}


def _check_mode(here, mode, role="document"):
    if mode not in structure.SHARE_MODES:
        _refuse("bad_mode", f"{role} {mode!r} -- expected one of {', '.join(structure.SHARE_MODES)}", mode=mode)
    if mode not in here.modes:
        _refuse("no_such_document", f"this project has no {mode} document -- it is laid out as a report alone, and migration gives it the three", mode=mode)


def _section_item(here, mode, node, parent):
    problems = list(node.problems)
    children = ()
    path = Path(here.document_dir(mode)) / node.file if node.file else None
    text = _read(path) if path is not None else None
    if text is not None:
        doc = _Doc(path, text)
        if doc.problems:
            problems += [f"{node.file}: {p}" for p in doc.problems]
        titled = _titles(doc)
        out = []
        for block in doc.objects():
            unit = doc.unit(block.id)
            out.append(Item(KIND_OBJECT, mode, block.id, titled.get(block.id) or _label(doc, block), node.id, node.id, node.file, block.type,
                            unit.shared or unit.inside, unit.shared is not None))
        children = tuple(out)
    return Item(KIND_SECTION, mode, node.id, structure.plain_title(node.title or "") or node.id, node.id, parent, node.file, None, None, False,
                tuple(node.shared_ids), tuple(node.shared_with), node.enabled, tuple(problems), children)


def importable(here, source_mode, language=None):
    """What can be imported from document `source_mode`: its sections -- a chapter's `group` items with the sections and groups under them, each section with the parametric objects its file holds under it -- as a list of top-level `Item`s in document order, for a tree with a check box on each row.

    A convention's or a base de projet's tree is its structure.json's, the report's its `#include` lines (no group). **Only tagged objects are objects**: a report's file the engineer has not tagged is a section without children. A heading of a file is no item: it is part of the section. Raises what `structure.tree` raises where the document cannot be read, and `bad_mode` / `no_such_document` for a document that is none.
    """
    _check_mode(here, source_mode)
    nodes = structure.tree(here, source_mode, language)

    def build(node, parent):
        if node.kind == "group":
            kids = tuple(item for item in (build(child, node.id) for child in node.children) if item is not None)
            return Item(KIND_GROUP, source_mode, node.id, structure.plain_title(node.title or "") or node.id, None, parent, None,
                        enabled=node.enabled, children=kids)
        if node.kind == "file":
            return _section_item(here, source_mode, node, parent)
        return None

    return [item for item in (build(node, None) for node in nodes) if item is not None]


# --- what is asked for -------------------------------------------------------------------------------------

def _coerce(item):
    """(kind, section or group id, id) of an item the dialog hands over: an `Item`, or the tuple `(kind, id)` / `("object", section id, object id)` a caller writes."""
    if isinstance(item, Item):
        if item.kind not in KINDS:
            _refuse("bad_item", f"{item!r} is none of a section, a group or an object", item=repr(item))
        return item.ref()
    if isinstance(item, (tuple, list)):
        if len(item) == 2 and item[0] in (KIND_GROUP, KIND_SECTION):
            return (item[0], item[1], item[1])
        if len(item) == 3 and item[0] == KIND_OBJECT:
            return (KIND_OBJECT, item[1], item[2])
        if len(item) == 3 and item[0] in (KIND_GROUP, KIND_SECTION):
            return (item[0], item[1], item[2])
    _refuse("bad_item", f"{item!r} is none of a section, a group or an object -- an Item of `importable`, or (\"section\", id), (\"group\", id), (\"object\", section id, object id)", item=repr(item))


@dataclass
class _Plan:
    sections: list      # file nodes, in document order
    objects: list       # (file node, object id), put in document order once the files are read
    skipped: list       # (kind, id, section, why)
    order: dict         # node id -> its place in the document


def _resolve(here, source_mode, items):
    nodes = structure.tree(here, source_mode)
    flat = structure.flatten(nodes)
    order = {node.id: index for index, node in enumerate(flat)}
    by_id = {node.id: node for node in flat}
    files = {node.file: node for node in flat if node.kind == "file"}

    def file_node(node_id):
        node = by_id.get(node_id)
        if node is None:
            known = ", ".join(n.id for n in flat if n.kind != "heading") or "none"
            _refuse("no_such_node", f"document {source_mode} has no section {node_id!r} -- its sections are {known}", id=node_id)
        if node.kind in ("heading", "object"):
            node = files.get(node.file, node)    # a heading or an object of a file stands for its file
        return node

    sections, objects, skipped = {}, {}, []
    for item in items:
        kind, section_id, object_id = _coerce(item)
        if kind in (KIND_GROUP, KIND_SECTION):
            node = file_node(section_id)
            if node.kind == "group":
                for below in structure.flatten(node.children):
                    if below.kind == "file":
                        sections[below.id] = below
            else:
                sections[node.id] = node
        else:
            node = file_node(section_id)
            if node.kind != "file":
                _refuse("not_a_section", f"{section_id!r} is not a section file -- an object is taken from the file of a section", id=section_id)
            objects.setdefault((node.id, object_id), node)
    wanted = sorted(sections.values(), key=lambda n: order[n.id])
    kept = []
    for (section_id, object_id), node in objects.items():
        if section_id in sections:
            skipped.append((KIND_OBJECT, object_id, section_id, "section_selected"))
        else:
            kept.append((node, object_id))
    return _Plan(wanted, kept, skipped, order)


def other_documents(here, mode):
    """The documents one can import into `mode` from: the other documents of the project, in their order -- what the dialog's «Importer depuis…» offers."""
    _check_mode(here, mode)
    return tuple(m for m in structure.SHARE_MODES if m in here.modes and m != mode)


def _check_modes(here, target_mode, source_mode):
    _check_mode(here, target_mode, "target document")
    _check_mode(here, source_mode, "source document")
    if target_mode == source_mode:
        _refuse("same_document", f"the content comes from {source_mode}, the document one works in -- it is imported from another document", mode=source_mode)


def _used_shared_ids(here):
    """Every shared id some section file of the project carries, tags read as lines -- a file whose tags cannot be paired counts too."""
    used = set()
    for path in _watched(here):
        if path.suffix != ".typ" or path.parent.name != SECTIONS_DIR:
            continue
        text = _read(path)
        if text and "woodcore:" in text:
            used.update(m.group(1) for line in _lines(text) if (m := _SHARED_TAG.match(_bare(line))))
    return used


def _free(base, used):
    candidate, number = base, 2
    while candidate in used:
        candidate, number = f"{base}-{number}", number + 1
    return candidate


# --- the «Importé» section -----------------------------------------------------------------------------------

def _imported_title(here, mode):
    return IMPORTED_TITLES[structure.document_language(here, mode)]


def _imported_section(here, mode):
    """(id, path, created) of the section objects imported alone go into: the one the document has -- wherever the engineer has moved it -- else a new one at the bottom of its tree."""
    folder = Path(here.document_dir(mode))
    if mode == "rs":
        for node in structure.flatten(structure.tree(here, "rs")):
            if node.kind == "file" and sharing.id_from_stem(node.id.split("#")[0]) == IMPORTED_ID:
                return node.id, folder / node.file, False
        stem = structure.suggest_id(here, "rs", IMPORTED_ID)
        structure.add_section(here, "rs", None, None, stem, _imported_title(here, "rs"))
        return stem, folder / structure.section_file(stem), True
    found = structure.find(structure.read(here.structure_file(mode)), IMPORTED_ID)
    if found is not None:
        node = found[0]
        if "children" in node:
            _refuse("imported_not_a_section", f"{IMPORTED_ID!r} is a group of {mode} -- the objects imported alone need a section of that id (or move the group away)", id=IMPORTED_ID)
        return IMPORTED_ID, folder / node["file"], False
    structure.add_section(here, mode, None, None, IMPORTED_ID, _imported_title(here, mode))
    return IMPORTED_ID, folder / structure.section_file(IMPORTED_ID), True


# --- importing -------------------------------------------------------------------------------------------------

@dataclass
class Result:
    """What an operation did.

    `op` -- `import` or `move_object`; `mode` the document written (the target of an import); `source` the document an import came from; `linked`. `sections` -- (source section id, id in the target) of each whole section imported; `objects` -- (section id, object id, object id in the copy -- the source's too where a linked copy had to be given a fresh one --, shared id or None) of each object imported alone; `imported` the id of the «Importé» section they went into and `created` whether it was made for them; `shared_ids` every shared id the operation put on a block or reused; `skipped` -- (kind, id, section id, why) of what was left out: an object of a section that is imported whole (`section_selected`); `written` the files written, the structure.json and entry files among them; `unresolved` -- (file, typst_paths.Unresolved) path literals that name nothing and were left as they were; `moved` -- (object id, file id it left, file id it went to) of a `move_object`, `shared_changed` the shared blocks whose content the move changed -- the objects of a block put in another order, or an object put into one -- which the other documents' copies will then differ from; `unrecorded` the shared ids whose synchronisation record (calc/sync.py) could not be written -- the copies are in place and the window may show such a block as in conflict until the engineer settles it."""
    op: str
    mode: str
    source: str = None
    linked: bool = True
    sections: tuple = ()
    objects: tuple = ()
    imported: str = None
    created: bool = False
    shared_ids: tuple = ()
    skipped: tuple = ()
    written: tuple = ()
    unresolved: tuple = ()
    moved: tuple = ()
    shared_changed: tuple = ()
    unrecorded: tuple = ()

    @property
    def changed(self):
        return bool(self.sections or self.objects or self.moved)

    def as_dict(self):
        """Plain values, paths as strings: what a log prints."""
        return {"op": self.op, "mode": self.mode, "source": self.source, "linked": self.linked, "sections": [list(s) for s in self.sections],
                "objects": [list(o) for o in self.objects], "imported": self.imported, "created": self.created, "shared_ids": list(self.shared_ids),
                "skipped": [list(s) for s in self.skipped], "written": [str(p) for p in self.written], "moved": [list(m) for m in self.moved],
                "shared_changed": list(self.shared_changed), "unrecorded": list(self.unrecorded)}


def _import_section_linked(here, target_mode, source_mode, node):
    done = sharing.share(here, source_mode, node.id, [target_mode])
    new_path = dict(done.copies)[target_mode]
    new_id = Path(new_path).stem
    if target_mode in structure.MODES:
        # share puts the copy at the end of the group of the same id; an import puts it at the bottom of the tree
        structure.move_node(here, target_mode, new_id, None, None)
    return new_id, tuple(done.shared_ids), tuple((str(p), c) for p, c in done.unresolved)


def _free_section_id(here, target_mode, base):
    """An id for a copy of a section in `target_mode`: `base` where it is free, else `base-2`, `base-3`, … -- the report's, its next numbered file name."""
    if target_mode == "rs":
        return structure.suggest_id(here, "rs", base)
    source = structure.read(here.structure_file(target_mode))
    folder = Path(here.document_dir(target_mode))
    candidate, number = base, 2
    while structure.find(source, candidate) is not None or (folder / structure.section_file(candidate)).exists():
        candidate, number = f"{base}-{number}", number + 1
    return candidate


def _import_section_copy(here, target_mode, source_mode, node):
    folder = Path(here.document_dir(source_mode))
    path = folder / node.file
    doc = _open(path, f"{node.file} of {source_mode}")
    base = node.id if source_mode in structure.MODES else sharing.id_from_stem(node.id.split("#")[0])
    new_id = _free_section_id(here, target_mode, base)
    title = " ".join(structure.plain_title(node.title or "").split()) or new_id
    structure.add_section(here, target_mode, None, None, new_id, title)
    destination = Path(here.document_dir(target_mode)) / structure.section_file(new_id)
    text = _without_shared_tags(doc.text)
    text, _changes, unresolved = typst_paths.rewrite(text, path, destination, here.typst_root, here.typst_root, {})
    text = _with_import(text, documents.import_line(here))
    text = structure.fit_text(text, 1)      # at the bottom of the tree: a chapter's level (06.10.2026)
    _put(destination, text.encode("utf-8"))
    return new_id, tuple((str(destination), u) for u in unresolved)


def _preflight_objects(here, target_mode, source_mode, plan, linked):
    """The source files of the objects, read, with every refusal that does not depend on the destination raised before anything is written: {key: _Doc}."""
    docs = {}
    folder = Path(here.document_dir(source_mode))
    for node, object_id in plan.objects:
        key = _key(folder / node.file)
        if key not in docs:
            docs[key] = _open(folder / node.file, f"{node.file} of {source_mode}")
        doc = docs[key]
        unit = doc.unit(object_id)
        if unit is None:
            known = ", ".join(b.id for b in doc.objects()) or "none"
            _refuse("no_such_object", f"{node.file} of {source_mode}: holds no object {object_id!r} -- its objects are {known}", id=object_id, file=str(doc.path))
        if linked and unit.inside:
            _refuse("inside_shared", f"{object_id!r} of {node.file} stands inside the larger shared block {unit.inside!r}, which already links it -- import the section, or tick «copie indépendante»",
                    id=object_id, shared_id=unit.inside)
        if linked and unit.shared:
            held = [c for c in sharing.copies(here, unit.shared) if c.mode == target_mode]
            if held:
                _refuse("already_shared", f"{target_mode} holds a copy of the shared block {unit.shared!r} already ({held[0].file.name})", mode=target_mode, shared_id=unit.shared, file=str(held[0].file))
    # in document order: the sections as the tree has them, the objects as their file writes them
    place = {(node.id, oid): [b.id for b in docs[_key(folder / node.file)].objects()].index(oid) for node, oid in plan.objects}
    plan.objects.sort(key=lambda pair: (plan.order[pair[0].id], place[(pair[0].id, pair[1])]))
    return docs


def _record_copies(here, source_mode, shared_ids, target_mode):
    """The synchronisation records (calc/sync.py) of the copies just made: each new copy in step with the block it was made from, and standing with a third document as the source stands with it -- what sharing.share writes beside its own files, by the module that owns the format. Returns the shared ids whose record could not be written (a record that cannot be read is left alone), () where all were; nothing at all where calc/sync.py is not there."""
    if not shared_ids:
        return ()
    try:
        import sync
        make = sync._share_writes
    except (ImportError, AttributeError):
        return ()
    index = getattr(sharing, "index", None)
    files = index(here).files if index is not None else sharing._index(here)
    try:
        writes = make(here, source_mode, list(shared_ids), files, [target_mode])
        if writes:
            _commit(writes)
    except sharing.SharingError:
        return tuple(shared_ids)
    return ()


def _import_objects(here, target_mode, source_mode, plan, linked, docs):
    """The objects of `plan` appended to the end of the «Importé» section of `target_mode`. Returns (section id, created, [(section, object id, new id, shared id)], shared ids, unresolved, shared ids whose synchronisation record could not be written)."""
    section_id, destination, created = _imported_section(here, target_mode)
    dest = _open(destination, f"{destination.name} of {target_mode}")
    dest_old = dest.text.encode("utf-8")
    originals = {key: doc.text.encode("utf-8") for key, doc in docs.items()}
    folder = Path(here.document_dir(source_mode))
    used = _used_shared_ids(here)
    taken, shared_ids, unresolved = [], [], []
    for node, object_id in plan.objects:
        key = _key(folder / node.file)
        src = docs[key]
        unit = src.unit(object_id)
        shared_id = None
        if linked:
            new_id = object_id
            if dest.object(object_id) is not None:
                if unit.shared:
                    _refuse("id_exists", f"the section {section_id!r} of {target_mode} holds an object {object_id!r} already, and the one to import is a shared block alone, whose id is the same in every copy -- import it as an independent copy", id=object_id, file=str(dest.path))
                # the id of an object is the same in every copy of its block, so the object takes a fresh one -- in the source as well as in the copy
                new_id = _free(object_id, {b.id for b in dest.objects()} | {b.id for b in src.objects()})
                lines = list(src.lines)
                lines[unit.block.start:unit.block.end + 1] = _rename_object(lines[unit.block.start:unit.block.end + 1], object_id, new_id)
                src = src.with_lines(lines)
                unit = src.unit(new_id)
            if unit.shared:
                shared_id = unit.shared
            else:
                shared_id = _free(new_id, used)
                used.add(shared_id)
                src = src.with_lines(_wrap(src.lines, unit.start, unit.end, shared_id, src.newline))
                unit = src.unit(new_id)
            text = src.block_text(unit.start, unit.end)
            text, _changes, left = typst_paths.rewrite(text, src.path, dest.path, here.typst_root, here.typst_root, {})
            if text != src.block_text(unit.start, unit.end):
                # the block between the tags is the same in every copy: the rewritten spelling goes into the source too
                lines = list(src.lines[:unit.start]) + _lines(text) + list(src.lines[unit.end + 1:])
                src = src.with_lines(lines)
            block = _normalise(text, dest.newline)
        else:
            block_lines = src.lines[unit.block.start:unit.block.end + 1]
            text = "".join(block_lines)
            text, _changes, left = typst_paths.rewrite(text, src.path, dest.path, here.typst_root, here.typst_root, {})
            new_id = object_id
            if dest.object(object_id) is not None:
                taken_ids = {b.id for b in dest.objects()}
                new_id = _free(object_id, taken_ids)
                text = "".join(_rename_object(_lines(text), object_id, new_id))
            block = _normalise(text, dest.newline)
        unresolved += [(str(src.path), u) for u in left]
        docs[key] = src
        dest = dest.with_lines(_place(dest.lines, len(dest.lines), block, dest.newline))
        if dest.problems:
            _refuse("tags_unreadable", f"{destination.name} of {target_mode}: the object {object_id!r} would leave the tags of the file unreadable -- " + "; ".join(str(p) for p in dest.problems),
                    file=str(dest.path), problems=[str(p) for p in dest.problems])
        taken.append((node.id, object_id, new_id, shared_id))
        if shared_id and shared_id not in shared_ids:
            shared_ids.append(shared_id)
    writes = [(dest.path, dest.text.encode("utf-8"), dest_old)]
    for key, doc in docs.items():
        if doc.text.encode("utf-8") != originals[key]:
            writes.append((doc.path, doc.text.encode("utf-8"), originals[key]))
    _commit(writes)
    unrecorded = _record_copies(here, source_mode, shared_ids, target_mode) if linked else ()
    return section_id, created, taken, tuple(shared_ids), tuple(unresolved), unrecorded


def import_items(here, target_mode, source_mode, items, linked=True):
    """The `items` ticked in document `source_mode` brought into document `target_mode` of project `here`. Returns a `Result`.

    `items` are what the dialog's tree gives (`importable`'s `Item`s, a group standing for every section under it), or `("section", id)`, `("group", id)`, `("object", section id, object id)`. **Whole sections** go to the bottom of the target's tree, **objects ticked alone** to the end of its section `imported` («Importé», created at the bottom where it is not there); a section and some of its own objects ticked together: the section wins (`Result.skipped`). **`linked=True`** shares them -- a section as sharing.share does it, an object wrapped in shared tags in its source file and in the copy under a shared id made from its own; **`linked=False`** copies them for good: no shared tag, an id the target does not have.

    Refused (DocImportError, CODES), with nothing written: a document that is none (`bad_mode`, `no_such_document`) or the same as the target (`same_document`), nothing ticked (`no_items`), an item that is none (`bad_item`), a section that is not there (`no_such_node`, `not_a_section`), an object that is not (`no_such_object`), a file that cannot be read (`file_missing`) or whose tags cannot (`tags_unreadable`), a linked object that stands inside a larger shared block (`inside_shared`) or whose block the target holds (`already_shared`), a linked object that is a shared block alone whose id the destination file has (`id_exists`), a group named `imported` where the objects would go (`imported_not_a_section`); and what sharing.share and structure.add_section refuse of a section -- `id_exists`, `already_shared`, `file_exists`, … (their codes). **All or nothing**: whatever fails after the first write takes back everything written.
    """
    _check_modes(here, target_mode, source_mode)
    items = list(items or ())
    if not items:
        _refuse("no_items", "nothing is ticked -- tick the sections and the objects to import")
    plan = _resolve(here, source_mode, items)
    if not plan.sections and not plan.objects:
        _refuse("no_items", "nothing is left to import -- the ticked objects all lie in sections that are imported whole" if plan.skipped else "nothing is ticked -- tick the sections and the objects to import")
    docs = _preflight_objects(here, target_mode, source_mode, plan, linked) if plan.objects else {}
    for node in plan.sections:
        _open(Path(here.document_dir(source_mode)) / node.file, f"{node.file} of {source_mode}")
    snapshot = _Snapshot(here)
    sections, shared_ids, unresolved, objects, unrecorded = [], [], [], (), ()
    imported, created = None, False
    try:
        for node in plan.sections:
            if linked:
                new_id, shared, left = _import_section_linked(here, target_mode, source_mode, node)
                shared_ids += [s for s in shared if s not in shared_ids]
            else:
                new_id, left = _import_section_copy(here, target_mode, source_mode, node)
            sections.append((node.id, new_id))
            unresolved += list(left)
        if plan.objects:
            imported, created, objects, more, left, unrecorded = _import_objects(here, target_mode, source_mode, plan, linked, docs)
            shared_ids += [s for s in more if s not in shared_ids]
            unresolved += list(left)
        if linked:
            sharing.reconcile(here)
    except BaseException as exc:
        snapshot.restore()
        _disk(exc)
        raise
    return Result("import", target_mode, source_mode, linked, tuple(sections), tuple(objects), imported, created, tuple(shared_ids),
                  tuple(plan.skipped), snapshot.changed(), tuple(unresolved), unrecorded=tuple(unrecorded))


# --- moving ------------------------------------------------------------------------------------------------------

def move_section(here, mode, node_id, new_parent_id, position, language=None):
    """Section or group `node_id` of document `mode` moved under `new_parent_id` (None for the top) at `position` -- calc/structure.py's `move_node`, the one operation that moves a section anywhere in the tree; what drag and drop of a section calls. Returns its `Edit`."""
    return structure.move_node(here, mode, node_id, new_parent_id, position, language)


def _file_of(here, mode, node_id):
    """The path of the section file node `node_id` of document `mode` stands in -- a heading stands for its file."""
    nodes = structure.tree(here, mode)
    node = structure.find_node(nodes, node_id) if isinstance(node_id, str) else None
    if node is None:
        known = ", ".join(n.id for n in structure.flatten(nodes) if n.kind != "heading") or "none"
        _refuse("no_such_node", f"document {mode} has no section {node_id!r} -- its sections are {known}", id=node_id)
    if node.kind == "group" or not node.file:
        _refuse("not_a_section", f"{node_id!r} is a group -- an object lies in the file of a section", id=node_id)
    return Path(here.document_dir(mode)) / node.file, node.file


def move_object(here, mode, file_id, object_id, target_file_id, before=None, after=None):
    """Object `object_id` of the section `file_id` of document `mode` moved into the section `target_file_id` of the same document -- the same one to reorder inside a file --: **above** the object `before`, **below** the object `after`, or after everything in the file where neither is given -- outside any shared block, a block whose last object is named in `after` being entered at its end. Returns a `Result` (`moved`); an object put where it stands, or onto itself, is a Result with `changed` False and nothing written.

    What moves is the object with its two tags -- **and with its shared tags where it is alone in a shared block**, the block being what other documents hold. Where `before` or `after` names an object that is alone in a shared block, the place is outside that block; named an object in a **larger** block, the place is inside it. An object that stands inside a larger shared block **cannot leave it** (`leaves_shared_block`), but may be put elsewhere in it -- the block is then edited, and `Result.shared_changed` names it --; a shared block alone cannot be put inside another (`nested_shared`). The objects of a larger block entered from outside go in the same way. Everything else of both files stays byte for byte, line endings included; a section's `shared_with` is written again where a shared block changed files.

    Refused (DocImportError, CODES), nothing written: a document that is none, a section that is not there, an object that is not (`no_such_object`, for the object and for `before` / `after`), a file whose tags cannot be read (`tags_unreadable`), both `before` and `after` (`bad_place`), the two refusals above, and an id the destination file already holds (`id_exists`) or a shared block it already carries (`already_shared`). All or nothing.
    """
    _check_mode(here, mode)
    if before is not None and after is not None:
        _refuse("bad_place", "an object is put above one object or below another, not both", before=before, after=after)
    source_path, source_rel = _file_of(here, mode, file_id)
    target_path, target_rel = _file_of(here, mode, target_file_id)
    same = _key(source_path) == _key(target_path)
    source = _open(source_path, f"{source_rel} of {mode}")
    target = source if same else _open(target_path, f"{target_rel} of {mode}")
    unit = source.unit(object_id)
    if unit is None:
        known = ", ".join(b.id for b in source.objects()) or "none"
        _refuse("no_such_object", f"{source_rel} of {mode}: holds no object {object_id!r} -- its objects are {known}", id=object_id, file=str(source.path))
    reference = before if before is not None else after
    if reference is not None:
        if reference == object_id:
            return Result("move_object", mode)
        ref_unit = target.unit(reference)
        if ref_unit is None:
            known = ", ".join(b.id for b in target.objects()) or "none"
            _refuse("no_such_object", f"{target_rel} of {mode}: holds no object {reference!r} -- its objects are {known}", id=reference, file=str(target.path))
        entered = ref_unit.inside
    else:
        ref_unit, entered = None, None
    if unit.inside and not (same and entered == unit.inside):
        _refuse("leaves_shared_block", f"{object_id!r} stands inside the shared block {unit.inside!r}, which the other documents' copies hold -- it can be moved inside that block, not out of it",
                id=object_id, shared_id=unit.inside)
    if unit.shared and entered:
        _refuse("nested_shared", f"{object_id!r} is a shared block of its own and cannot be put inside the shared block {entered!r}", id=object_id, shared_id=entered)
    if not same:
        if target.object(object_id) is not None:
            _refuse("id_exists", f"{target_rel} of {mode}: holds an object {object_id!r} already -- an id names one object in its file", id=object_id, file=str(target.path))
        if unit.shared and unit.shared in target.shared_ids():
            _refuse("already_shared", f"{target_rel} of {mode}: carries the shared block {unit.shared!r} already", mode=mode, shared_id=unit.shared, file=str(target.path))
    block = source.block_text(unit.start, unit.end)
    cut = source.with_lines(_cut(source.lines, unit.start, unit.end))
    base = cut if same else target
    if reference is None:
        index = len(base.lines)
    else:
        # what the reference is -- an object, or the shared block it is alone in -- was settled before the cut: once the object is out of a block of two, the one left is alone in it
        if ref_unit.shared:
            held = next(b for b in base.blocks if b.kind == "shared" and b.id == ref_unit.shared)
        else:
            held = base.object(reference)
        index = held.start if before is not None else held.end + 1
    moved = base.with_lines(_place(base.lines, index, _normalise(block, base.newline), base.newline))
    if moved.problems:
        _refuse("tags_unreadable", f"{target_rel} of {mode}: the move would leave the tags of the file unreadable -- " + "; ".join(str(p) for p in moved.problems),
                file=str(target.path), problems=[str(p) for p in moved.problems])
    writes = [(source.path, (moved if same else cut).text.encode("utf-8"), source.text.encode("utf-8"))]
    if not same:
        writes.append((target.path, moved.text.encode("utf-8"), target.text.encode("utf-8")))
    if all(old == new for _p, new, old in writes):
        return Result("move_object", mode)
    changed = tuple(dict.fromkeys(s for s in (unit.inside, entered) if s))
    # the shared blocks edited, as they stood before: what calc/sync.py is told so that the edit is local here and incoming elsewhere
    before_blocks = {}
    if unit.inside:
        before_blocks[unit.inside] = source.shared_text(unit.inside)
    if entered:
        before_blocks.setdefault(entered, target.shared_text(entered))
    snapshot = _Snapshot(here)
    unrecorded = ()
    try:
        _commit(writes)
        if unit.shared and not same:
            sharing.reconcile(here)
        unrecorded = _record_edits(here, mode, before_blocks)
    except BaseException as exc:
        snapshot.restore()
        _disk(exc)
        raise
    return Result("move_object", mode, shared_ids=(unit.shared,) if unit.shared else (), written=snapshot.changed(),
                  moved=((object_id, file_id, target_file_id),), shared_changed=changed, unrecorded=unrecorded)


def _record_edits(here, mode, before_blocks):
    """calc/sync.py told that document `mode` has just edited the shared blocks of `before_blocks` -- {shared id: the block as it stood before} -- so that each shows as a local edit here and as incoming in the other documents, and not as a conflict. Returns the shared ids whose record could not be written; nothing at all where calc/sync.py is not there."""
    if not before_blocks:
        return ()
    try:
        import sync
        record = sync.record_local_edit
    except (ImportError, AttributeError):
        return ()
    left = []
    for shared_id, before in before_blocks.items():
        try:
            record(here, mode, shared_id, before=before)
        except sharing.SharingError:
            left.append(shared_id)
    return tuple(left)
