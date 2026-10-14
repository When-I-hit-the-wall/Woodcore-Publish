# -*- coding: utf-8 -*-
"""The objects taken out of a document, kept where they stood so that they can be put back (the engineer's request of 06.10.2026: «quand on supprime un objet … il reste affiché dans l'arborescence, mais qu'on comprenne visuellement qu'il est supprimé … si on veut tout d'un coup remettre l'objet, il suffit de faire clic droit et de le réintégrer au document. Et il se réintégrera à la position où il se trouve»).

An object removed from a section file is, as since v0.112, **copied into the document's `Sections/archives/`** first (`<yymmdd-hhmmss>-<file>-<id>.typ`, its two tags and its body as written), and only then cut out of its file. What this module adds is the **register** beside those copies, `Sections/archives/removed.json`: one entry per object removed, saying which file it was in, its type, id and short label, its copy, and **where it stood** -- the id of the object just before it (`after`) and of the one just after it (`before`), or None at either end of the file. The «Structure du document» tab reads the register and shows each object at that place in the tree, greyed and struck through, with «Réintégrer dans le document» on the right button.

**Putting one back** (`restore`) inserts its copy, as written -- a hand-written body is put back as it was --, **right after the closing tag of the object that stood before it**: whatever text the engineer added since between that object and the next stays between the two, and the object takes its place directly after its neighbour, which is the engineer's own rule («aller rechercher la fin de la balise d'avant … intégrer ce nouvel objet directement après»). Where that object is gone too, it goes right before the opening tag of the one that stood after it; where both are gone, at the end of the file. Where another object of the file has taken its id meanwhile, it comes back under a free one (`typst_objects.free_id`), its two tags rewritten and nothing else. A blank line is put on either side where there is none, Typst parting two paragraphs by one. Its entry leaves the register; its copy stays in the archives, as everything put there does.

**Forgetting one** (`forget`) takes its entry out of the register -- the row leaves the tree -- and leaves its copy where it is.

The register is Woodcore's own file: written whole, beside itself and moved into place, never edited by hand; an entry it cannot read is passed over and kept, an entry whose file is gone is still listed (its section may come back). There is no Qt in this file.
"""

import datetime
import json
import os
from pathlib import Path

import structure
import typst_objects
import typst_paths

REGISTER = "removed.json"
FORMAT = "woodcore-removed"
SCHEMA_VERSION = "1.0"
KEYS = ("file", "object_id", "type", "title", "archive", "after", "before", "removed")


class RemovedError(ValueError):
    """A removal or a restoration refused: a `code` and an English sentence, the window writing its own for the code."""

    def __init__(self, code, message, **values):
        super().__init__(message)
        self.code = code
        self.values = values


def archives_dir(doc_dir):
    return Path(doc_dir) / structure.SECTIONS_DIR / structure.ARCHIVES_DIR


def register_path(doc_dir):
    return archives_dir(doc_dir) / REGISTER


def read(doc_dir):
    """The entries of the register, in the order the objects were removed -- [] where there is none or it cannot be read (a register that cannot be read hides no object from the document: it only shows fewer rows)."""
    path = register_path(doc_dir)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    entries = data.get("removed") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return []
    return [entry for entry in entries if isinstance(entry, dict) and isinstance(entry.get("file"), str) and isinstance(entry.get("object_id"), str)]


def entries_for(doc_dir, file):
    """The entries of section file `file` (relative to the document's folder, `/`-separated)."""
    return [entry for entry in read(doc_dir) if entry["file"] == file]


def _write(doc_dir, entries):
    path = register_path(doc_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"schema_version": SCHEMA_VERSION, "format": FORMAT, "removed": [{key: entry.get(key) for key in KEYS} for entry in entries]}
    staged = path.with_name(path.name + ".new")
    staged.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    os.replace(staged, path)


def neighbours(text, object_id):
    """(after, before): the ids of the objects just before and just after object `object_id` in a file's text, None at either end."""
    found = typst_objects.objects(text)
    ids = [o.id for o in found]
    if object_id not in ids:
        raise RemovedError("no_such_object", f"the file holds no object {object_id!r}", id=object_id)
    index = ids.index(object_id)
    return (ids[index - 1] if index > 0 else None), (ids[index + 1] if index + 1 < len(ids) else None)


def record(doc_dir, file, obj, archive, after, before, when=None):
    """An entry added to the register for object `obj` (a typst_objects.Object), just removed from `file` and copied to `archive` (a path): where it stood is `after` and `before`. Returns the entry."""
    archive = Path(archive)
    try:
        archive_rel = archive.relative_to(Path(doc_dir)).as_posix()
    except ValueError:
        archive_rel = archive.as_posix()
    entry = {"file": file, "object_id": obj.id, "type": obj.type, "title": typst_objects.object_title(obj), "archive": archive_rel,
             "after": after, "before": before, "removed": (when or datetime.datetime.now()).isoformat(timespec="seconds")}
    entries = read(doc_dir)
    entries.append(entry)
    _write(doc_dir, entries)
    return entry


def _same(a, b):
    return a.get("file") == b.get("file") and a.get("object_id") == b.get("object_id") and a.get("archive") == b.get("archive")


def forget(doc_dir, entry):
    """`entry` taken out of the register -- its row leaves the tree -- its copy left in the archives. True where it was there."""
    entries = read(doc_dir)
    kept = [e for e in entries if not _same(e, entry)]
    if len(kept) == len(entries):
        return False
    _write(doc_dir, kept)
    return True


def _retag(block, old_id, new_id):
    """The block's two tag lines given `new_id` in place of `old_id`, nothing else of it changed."""
    lines = block.splitlines(keepends=True)
    for index in (0, len(lines) - 1):
        line = lines[index]
        body = line.rstrip("\r\n")
        ending = line[len(body):]
        if body.rstrip().endswith(" " + old_id):
            stripped = body.rstrip()
            lines[index] = stripped[: -len(old_id)] + new_id + ending
    return "".join(lines)


def insert_place(text, entry):
    """The 0-based line the object of `entry` goes back to in `text`: right after the closing tag of the object that stood before it, else right before the opening tag of the one that stood after it, else the end of the file."""
    found = {o.id: o for o in typst_objects.objects(text)}
    lines = typst_objects._lines(text)
    after = found.get(entry.get("after")) if entry.get("after") else None
    if after is not None:
        return after.end + 1
    before = found.get(entry.get("before")) if entry.get("before") else None
    if before is not None:
        return before.start
    return len(lines)


def restore(doc_dir, entry):
    """The object of `entry` put back into its file (see the module's docstring) and its entry taken out of the register. Returns (path, new text, the object's id in the file, the text as it was): the caller writes nothing more, the file being written here -- it gives the texts to calc/sync.py where the object came back into a shared block. Refused (RemovedError) where the file or the copy is gone, or the file's tags cannot be read."""
    doc_dir = Path(doc_dir)
    path = doc_dir / entry["file"]
    copy = doc_dir / entry["archive"]
    if not path.is_file():
        raise RemovedError("file_gone", f"{entry['file']} is not there any more -- put its section back first", file=entry["file"])
    if not copy.is_file():
        raise RemovedError("copy_gone", f"the copy {entry['archive']} is not there any more", archive=entry["archive"])
    text = typst_paths.read_text(path)
    try:
        typst_objects._readable(text)
    except typst_objects.ObjectError as exc:
        raise RemovedError("tags", str(exc)) from None
    block = typst_paths.read_text(copy)
    object_id = entry["object_id"]
    if typst_objects.find(text, object_id) is not None or any(b.kind == "object" and b.id == object_id for b in structure.pair_tags(text)[0]):
        new_id = typst_objects.free_id(text, object_id)
        block = _retag(block, object_id, new_id)
        object_id = new_id
    newline = typst_objects._newline_of(text)
    block = block.replace("\r\n", "\n").rstrip("\n").replace("\n", newline) + newline
    lines = typst_objects._lines(text)
    at = insert_place(text, entry)
    head = lines[:at]
    if head and not typst_objects._ending(head[-1]):
        head[-1] += newline
    tail = lines[at:]
    pieces = list(head)
    if head and head[-1].strip():
        pieces.append(newline)          # a blank line between the object and the one it follows
    pieces.append(block)
    if tail and tail[0].strip():
        pieces.append(newline)          # and between it and what follows it
    new_text = "".join(pieces + tail)
    typst_paths.write_text(path, new_text)
    forget(doc_dir, entry)
    return path, new_text, object_id, text
