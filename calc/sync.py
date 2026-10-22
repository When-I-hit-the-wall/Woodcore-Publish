"""Keeping what the three documents share in step -- one document at a time, and only as the engineer decides (the rework of 01.10.2026, which replaces the «overwrite every copy after an alert» rule of phase 5).

**Only shared content syncs**: the text between two shared tags (`// woodcore:shared <id>` … `// woodcore:/shared <id>`, calc/sharing.py), of which each document of the project that shares it holds a copy in a section file. Outside the tags every copy is free and is never read here. An edit may come from anywhere -- VS Code writing the file, or Woodcore's own right pane -- and **it only ever writes the copy of the document it was made in**: the others learn of it, they are not changed by it. Each document then says, for each shared block and for each parametric object inside it (calc/typst_objects.py: a heading, a paragraph, a table …, compared by id), where it stands:

- `in_sync` -- nothing has changed since this document last synchronised with the others (or they all hold the same now);
- `local` -- only this copy changed: the others will see it as incoming;
- `incoming` (orange) -- another document's copy changed since this document last synchronised with it, and this copy did not;
- `conflict` (red) -- both this copy and another changed since, and they differ;
- `ignored` -- the engineer chose «Ignorer» for the block or the object in this document: never imported, until «Réactiver»;
- `problem` -- this document's copy cannot be compared: its file's tags cannot be read, or two files of the document carry the block.

«Importer les modifications» (`import_changes`) takes, for what is incoming, the other document's version and writes it **between the tags only**, in this document's copy alone; a conflict asks which version to keep (`choices`). `ignore` and `reactivate` set and take off «Ignorer», per document, permanently.

**What is remembered, and where.** Each document keeps its own record, `sync.json`, beside its entry file (and for the convention and the base de projet beside their structure.json): the documents' folders are what an archive of a document holds (calc/tools/archive_export.py's members_of_document) and what a migration moves, so the record travels with the copies it describes, and a document template -- its entry, its structure and its listed sections -- never carries it. It is Woodcore's own file, written whole (LF, two-space indent, keys in a fixed order: the same bytes on every machine NextCloud syncs), beside itself and moved into place, never edited by hand. For every shared block the document holds it records hashes of the block **as this document last synchronised it** -- the block's own text (everything between the tags but its objects, the text "following the block") and each object, by id -- and where the relation with one other document stands apart from that (`with`): for each part, the hash of **this** copy (`own`) and of **that** copy (`seen`) when the two last synchronised. A plain base per block would not do, which is why there are two: «keep mine» in a conflict means this document has *seen* the other version and kept its own, which one hash cannot say, and a copy made by `share` inherits the source's standing with a third document while being in step with the source itself. The ignore flags (the block, and objects one by one) are in the same record.

**A hash** is the first 16 hexadecimal digits of the SHA-256 of the part's text with its line endings made LF -- so a file saved CRLF by one editor and LF by another holds the same version; `-` says the object was not in that copy; `null` says the base is not known (a block whose copies have never been seen equal).

**How a state is worked out** -- for a part of a block, in document D, against every other document O holding a copy: the two copies hold the same → in step; else `mine` = D's copy is not what D held when it last synchronised with O (`own`), `theirs` = O's copy is not what D then saw of it (`seen`); both → conflict, `theirs` alone → incoming, `mine` alone → local, neither → in step, D having seen O's version and kept its own. D's state for the part is the worst over the others (`STATES` in order of severity), the block's the worst over its parts, a file's the worst over its blocks.

**Settling.** Two copies found holding the same part are in step for it, whatever they held before: every read (`status`) and every write records that, for every pair of documents, in both documents' records -- so two copies edited the same way in VS Code, or made equal by an import, never come out as a conflict later. It is also what initialises a project seen for the first time: copies that are equal start in step, and copies that differ -- with no record to say who changed -- are in conflict, for the engineer to settle.

**Writes** -- an import, an ignore, a recorded edit -- read everything, check everything, and then write every file they change at once, each beside itself and moved into place, tried again on the PermissionError NextCloud's client gives, a file found changed since it was read refusing the whole (`changed_meanwhile`) and a write that fails putting back every file written before it (`write_failed`): calc/sharing.py's `_commit`. Every refusal is a `SyncError` -- a `sharing.SharingError`, and so a `structure.StructureError` -- with a `code` (CODES), the `values` it is about and an English sentence; the window writes its own sentence for the code.

**The window** colours a file and an object by the `state` `status` gives it (orange for `incoming`, red for `conflict`, grey for `ignored`), offers «Importer les modifications» on what is incoming or in conflict -- `import_changes(here, mode, items, choices)`, asking first for every conflict which version to keep (`ObjectStatus.versions` / `BlockStatus.versions` hold each document's text, for a diff) -- and «Ignorer» / «Réactiver» on a selection. After it has written a shared block itself it calls `record_local_edit(here, mode, shared_id, before=<the block as loaded>)`, or writes through `write_local`, so that a project never synchronised before shows the edit as local here and incoming elsewhere rather than as a conflict.

**A module that makes or unmakes copies** keeps the records itself, in its own commit: `share_writes(here, source_mode, shared_ids, files, targets)` gives the writes that start each new copy in step with the block it was made from -- calc/sharing.py's `share` and calc/doc_import.py's linked import call it (the latter by the name it had first, `_share_writes`, kept as an alias) -- and `stop_writes(here, removed)` those that drop the record of a copy whose tags were taken off (`stop_sharing`).

Qt-free; standard library and the project's own modules only.
"""

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import sharing
import structure
import typst_objects
import typst_sync
import validation

FILE = "sync.json"
FORMAT = "woodcore-sync"
SCHEMA_VERSION = "1.0"

# The documents that share, in the order they are said: structure.py's.
SHARE_MODES = structure.SHARE_MODES

# The states of a block, an object or a file, in order of severity: what a file or a block shows is the worst of what it holds.
STATES = ("in_sync", "ignored", "local", "incoming", "conflict", "problem")
_RANK = {state: rank for rank, state in enumerate(STATES)}

# What a conflict -- or an incoming change -- may be answered with in `choices`: this document's version, the newest other version, or a document's name (cu, bp, rs) for that document's version.
MINE, THEIRS = "mine", "theirs"

# Why an operation refuses, one code each (SyncError.code; `values` names what the refusal is about).
CODES = (
    "bad_mode",           # a document that is none of cu, bp, rs (`mode`)
    "no_such_document",   # the project has no such document: a report laid out alone (`mode`)
    "bad_item",           # an item that is not «<shared id>» or «<shared id>/<object id>» (`item`)
    "no_such_item",       # no shared block or object of that id in this document (`item`)
    "ignored",            # an item asked for by name that this document ignores: reactivate it first (`item`)
    "needs_choice",       # a conflict imported without a choice of version (`items`)
    "bad_choice",         # a choice that is none of mine, theirs or a document holding a copy (`item`, `choice`)
    "unreadable_copy",    # this document's copy cannot be compared: its tags cannot be read, or two files carry it (`item`, `files`)
    "state_unreadable",   # this document's sync.json cannot be read, so it is not rewritten (`file`, `error`)
    "bad_block",          # a block that would leave a file's tags unreadable, or that holds shared or structure tags (`file`, `problems`)
    "changed_meanwhile",  # a file changed between being read and being written: nothing was written, read again (`file`)
    "write_failed",       # the disk refused: what had been written has been put back (`error`)
)

# What `status` reports beside the states, one code each (Problem.code).
PROBLEMS = (
    "unreadable_copy",    # a file carrying a shared block whose tags cannot be read: that copy is left out (`mode`, `file`, `shared_id`)
    "duplicate_copy",     # a document holding one shared block in two files (`mode`, `files`, `shared_id`)
    "state_unreadable",   # a sync.json that cannot be read: read as empty, and never written (`mode`, `file`, `error`)
    "settle_failed",      # copies found equal could not be recorded as such: the disk refused (`error`)
)

ABSENT = "-"      # an object a copy does not hold
UNKNOWN = None    # a base no record states
TEXT = ""         # the part that is the block's own text -- an object id is never empty

_DIGEST = re.compile(r"^[0-9a-f]{16}$")
_LINE = re.compile(r"[^\r\n]*(?:\r\n|\r|\n)|[^\r\n]+")
# Where an object stands in a block's text when the text is compared without it: a line no Typst file holds.
_PLACEHOLDER = "\x00woodcore-object {}\n"
_ENTRY_KEYS = ("text", "objects", "with", "ignored", "ignored_objects")


class SyncError(sharing.SharingError):
    """A synchronisation refused, said by name: a `code` of CODES, the `values` it is about and an English sentence. A sharing.SharingError -- so a structure.StructureError and a ValidationError -- so whatever catches the catalogue's and the sharing's refusals catches these too."""


def _refuse(code, message, **values):
    raise SyncError(message, code, **values)


# --- text --------------------------------------------------------------------------------------

def _lines(text):
    return _LINE.findall(text)


def _bare(line):
    return line.rstrip("\r\n")


def _ending(line):
    return line[len(_bare(line)):]


def _lf(text):
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _block(text):
    """A block's text as it is compared: LF, and ending in a line ending unless empty -- sharing.py's."""
    text = _lf(text or "")
    if text and not text.endswith("\n"):
        text += "\n"
    return text


def digest(text):
    """The hash a part is recorded by: the first 16 hexadecimal digits of the SHA-256 of `text` with its line endings made LF."""
    return hashlib.sha256(_lf(text).encode("utf-8")).hexdigest()[:16]


def three_way(mine_now, theirs_now, own, seen):
    """Where one part stands between this copy and another, by the rule this module is built on: the same text in both is in step; else `mine` is this copy not being what it held when the two last synchronised (`own`), `theirs` the other not being what this one then saw of it (`seen`) -- both a conflict, `theirs` alone incoming, `mine` alone local, neither in step (this copy saw the other's version and kept its own). A base nobody states (UNKNOWN) differs from every text: a difference with no record is a conflict, never guessed. Pure; shared by an unfolded check's lines and its writing (calc/domains/unfold.py, spec 2026-10-15 REQ-007)."""
    if theirs_now == mine_now:
        return "in_sync"
    mine, theirs = mine_now != own, theirs_now != seen
    return "conflict" if (mine and theirs) else "incoming" if theirs else "local" if mine else "in_sync"


def _blank(line):
    return not _bare(line).strip()


# --- items -------------------------------------------------------------------------------------

def item_key(shared_id, object_id=None):
    """The name of an item: «<shared id>» for a block, «<shared id>/<object id>» for an object inside it -- ids never hold a slash."""
    return shared_id if not object_id else f"{shared_id}/{object_id}"


def split_key(item):
    """(shared id, object id or None) of an item given as «<shared id>», «<shared id>/<object id>» or a pair; `bad_item` where it is none."""
    if isinstance(item, (tuple, list)) and len(item) == 2:
        shared_id, object_id = item
    elif isinstance(item, str):
        shared_id, slash, object_id = item.partition("/")
        if slash and not object_id:
            object_id = ""
        elif not slash:
            object_id = None
    else:
        _refuse("bad_item", f"{item!r} is not an item -- a shared block is named «<id>», an object in it «<id>/<object id>»", item=repr(item))
    ok = isinstance(shared_id, str) and structure.ID_PATTERN.match(shared_id or "")
    if object_id is not None:
        ok = ok and isinstance(object_id, str) and structure.ID_PATTERN.match(object_id or "")
    if not ok:
        _refuse("bad_item", f"{item!r} is not an item -- a shared block is named «<id>», an object in it «<id>/<object id>», each id lower case, letters and digits parted by single hyphens", item=str(item))
    return shared_id, object_id


# --- a block taken apart --------------------------------------------------------------------------

@dataclass(frozen=True)
class _Parts:
    """A copy of a block as it is compared: its lines (their own endings kept), the hash of each part -- TEXT for the text around the objects, an object's id for that object, its two tag lines included -- the LF text of each, where each object lies (line indices of its two tags), its type, the objects' order, and the block's text read as a sequence of ("line", line) and ("object", id)."""
    lines: tuple
    values: dict
    texts: dict
    spans: dict
    types: dict
    order: tuple
    skeleton: tuple

    def value(self, part):
        return self.values.get(part, ABSENT)


def _top_objects(block_text):
    """The objects of `block_text` as typst_objects reads them, those standing inside another left out -- or None where two of them carry one id, which leaves nothing to compare by."""
    try:
        found = typst_objects.objects(block_text)
    except ValueError:            # a block typst_objects cannot read (ParseError): it is then compared whole
        return []
    found = sorted(found, key=lambda o: o.start)
    top, until = [], -1
    for obj in found:
        if obj.start <= until:
            continue
        top.append(obj)
        until = obj.end
    ids = [o.id for o in top]
    if len(ids) != len(set(ids)):
        return None
    return top


def _decompose(block_text, flat=False):
    """`_Parts` of a block's text, or None where its objects cannot be told apart (an id twice) and `flat` is not asked for -- `flat` compares the block whole, as text alone."""
    lines = tuple(_lines(block_text))
    found = [] if flat else _top_objects(block_text)
    if found is None:
        return None
    spans, types, texts, values, order = {}, {}, {}, {}, []
    starts = {}
    for obj in found:
        if not (0 <= obj.start <= obj.end < len(lines)):
            continue
        starts[obj.start] = obj
    skeleton, out = [], []
    index = 0
    while index < len(lines):
        obj = starts.get(index)
        if obj is None:
            skeleton.append(("line", lines[index]))
            out.append(_lf(lines[index]))
            index += 1
            continue
        span = _block("".join(lines[obj.start:obj.end + 1]))
        spans[obj.id] = (obj.start, obj.end)
        types[obj.id] = obj.type
        texts[obj.id] = span
        # the values Woodcore keeps in step (`#sync`, calc/typst_sync.py) are left out of what two copies are compared by: a number refreshed is no edit (spec 2026-10-21-commandes-typst-refonte, ARCH-009, ARCH-RISK-303); the text kept, and written, is the whole of it
        values[obj.id] = digest(typst_sync.blanked(span))
        order.append(obj.id)
        skeleton.append(("object", obj.id))
        out.append(_PLACEHOLDER.format(obj.id))
        index = obj.end + 1
    texts[TEXT] = "".join(out)
    values[TEXT] = digest(typst_sync.blanked(texts[TEXT]))
    return _Parts(lines, values, texts, spans, types, tuple(order), tuple(skeleton))


# --- the record ----------------------------------------------------------------------------------

@dataclass
class _Entry:
    """What a document records of one shared block: whether it states a base at all (`known`), the base -- {part: hash or UNKNOWN}, an object not listed being one the copy did not hold --, the relations with other documents standing apart from it ({mode: {part: (own, seen)}}) and the ignore flags."""
    known: bool = False
    base: dict = field(default_factory=dict)
    rel: dict = field(default_factory=dict)
    ignored: bool = False
    ignored_objects: set = field(default_factory=set)

    def base_of(self, part):
        if not self.known:
            return UNKNOWN
        if part == TEXT:
            return self.base.get(TEXT, UNKNOWN)
        return self.base.get(part, ABSENT)

    def pair(self, other, part):
        """(own, seen) of `part` in this document's relation with `other`: what this copy and that one held when the two last synchronised."""
        found = self.rel.get(other, {}).get(part)
        if found is not None:
            return found
        base = self.base_of(part)
        return (base, base)

    def make_known(self, parts):
        """A base stated for every part of `parts` -- UNKNOWN for each -- where the entry stated none: what a relation recorded on a block never seen equal needs."""
        if not self.known:
            self.known = True
            self.base = {part: UNKNOWN for part in parts}
            self.rel = {}


@dataclass
class _Doc:
    """One document's record as read: its file, its bytes (None where it is not there), its entries by shared id, and why it cannot be read (then it is read as empty and never written)."""
    mode: str
    path: Path
    raw: bytes
    entries: dict
    problem: str = None


def _check_value(value, where, absent=True):
    if value is None or (absent and value == ABSENT) or (isinstance(value, str) and _DIGEST.match(value)):
        return value
    raise ValueError(f"{where}: {value!r} is not a hash -- 16 hexadecimal digits, «-» for an object the copy did not hold, or null")


def _check_pair(data, where):
    if not isinstance(data, dict) or set(data) != {"own", "seen"}:
        raise ValueError(f"{where}: a relation is {{\"own\": …, \"seen\": …}}")
    return (_check_value(data["own"], where + ".own"), _check_value(data["seen"], where + ".seen"))


def _check_id(value, where):
    if not isinstance(value, str) or not structure.ID_PATTERN.match(value):
        raise ValueError(f"{where}: {value!r} is not an id")
    return value


def _entry_from(data, mode, where):
    if not isinstance(data, dict):
        raise ValueError(f"{where}: is not an object")
    extra = sorted(set(data) - set(_ENTRY_KEYS))
    if extra:
        raise ValueError(f"{where}: carries {', '.join(map(repr, extra))} -- an entry holds {', '.join(_ENTRY_KEYS)}")
    entry = _Entry()
    if "text" in data:
        entry.known = True
        entry.base[TEXT] = _check_value(data["text"], where + ".text", absent=False)
        objects = data.get("objects", {})
        if not isinstance(objects, dict):
            raise ValueError(f"{where}.objects: is not an object")
        for object_id, value in objects.items():
            _check_id(object_id, f"{where}.objects")
            value = _check_value(value, f"{where}.objects.{object_id}")
            if value != ABSENT:
                entry.base[object_id] = value
        relations = data.get("with", {})
        if not isinstance(relations, dict):
            raise ValueError(f"{where}.with: is not an object")
        for other, parts in relations.items():
            if other not in SHARE_MODES or other == mode:
                raise ValueError(f"{where}.with: {other!r} is not another document -- expected one of {', '.join(m for m in SHARE_MODES if m != mode)}")
            if not isinstance(parts, dict) or set(parts) - {"text", "objects"}:
                raise ValueError(f"{where}.with.{other}: holds «text» and «objects» and nothing else")
            held = {}
            if "text" in parts:
                held[TEXT] = _check_pair(parts["text"], f"{where}.with.{other}.text")
            objects = parts.get("objects", {})
            if not isinstance(objects, dict):
                raise ValueError(f"{where}.with.{other}.objects: is not an object")
            for object_id, pair in objects.items():
                _check_id(object_id, f"{where}.with.{other}.objects")
                held[object_id] = _check_pair(pair, f"{where}.with.{other}.objects.{object_id}")
            entry.rel[other] = held
    elif "objects" in data or "with" in data:
        raise ValueError(f"{where}: «objects» and «with» stand beside a «text», the base they belong to")
    if "ignored" in data:
        if not isinstance(data["ignored"], bool):
            raise ValueError(f"{where}.ignored: is true or false")
        entry.ignored = data["ignored"]
    if "ignored_objects" in data:
        ignored = data["ignored_objects"]
        if not isinstance(ignored, list) or len(set(ignored)) != len(ignored):
            raise ValueError(f"{where}.ignored_objects: is a list of object ids, each once")
        entry.ignored_objects = {_check_id(i, f"{where}.ignored_objects") for i in ignored}
    return entry


def check_source(source, mode, where=FILE):
    """A document's record, checked: {shared id: _Entry}. Raises ValueError naming the entry and the field.

    **The contract is schemas/sync.schema.json** (v0.117, issue #33), checked first -- the types, the version, the format, the documents --, then what the schema walker cannot express is checked here: a hash's shape, an id's, the keys an entry, a relation and a pair may hold, `with` naming another document. The schema's description lists those rules, so the two are read as one contract; tests/test_sync.py holds the schema's constants equal to this module's."""
    try:
        validation.validate_structure(source, "sync", where)
    except validation.ValidationError as exc:
        raise ValueError(str(exc)) from None
    if not isinstance(source, dict):
        raise ValueError(f"{where}: is not a JSON object")
    keys = ("schema_version", "format", "document", "blocks")
    if set(source) != set(keys):
        raise ValueError(f"{where}: holds {', '.join(keys)} and nothing else")
    if source["format"] != FORMAT or source["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"{where}: is not a {FORMAT} {SCHEMA_VERSION} file")
    if source["document"] != mode:
        raise ValueError(f"{where}: is the record of document {source['document']!r}, not of {mode!r}")
    if not isinstance(source["blocks"], dict):
        raise ValueError(f"{where}.blocks: is not an object")
    return {_check_id(sid, f"{where}.blocks"): _entry_from(data, mode, f"{where}.blocks.{sid}") for sid, data in source["blocks"].items()}


def dumps(mode, entries):
    """The text of a document's record as it is written: keys in a fixed order, objects and ids sorted, two-space indent, LF, one trailing newline -- the same entries give the same bytes."""
    blocks = {}
    for sid in sorted(entries):
        entry = entries[sid]
        out = {}
        if entry.known:
            out["text"] = entry.base.get(TEXT, UNKNOWN)
            objects = {o: v for o, v in sorted(entry.base.items()) if o != TEXT and v != ABSENT}
            if objects:
                out["objects"] = objects
            relations = {}
            for other in SHARE_MODES:
                held = entry.rel.get(other)
                if not held:
                    continue
                part_out = {}
                if TEXT in held and held[TEXT] != (entry.base_of(TEXT),) * 2:
                    part_out["text"] = {"own": held[TEXT][0], "seen": held[TEXT][1]}
                objects = {o: {"own": p[0], "seen": p[1]} for o, p in sorted(held.items()) if o != TEXT and p != (entry.base_of(o),) * 2}
                if objects:
                    part_out["objects"] = objects
                if part_out:
                    relations[other] = part_out
            if relations:
                out["with"] = relations
        if entry.ignored:
            out["ignored"] = True
        if entry.ignored_objects:
            out["ignored_objects"] = sorted(entry.ignored_objects)
        if out:
            blocks[sid] = out
    record = {"schema_version": SCHEMA_VERSION, "format": FORMAT, "document": mode, "blocks": blocks}
    return json.dumps(record, ensure_ascii=False, indent=2) + "\n"


def state_file(here, mode):
    """Where document `mode` keeps its record: `sync.json` beside its entry file."""
    return here.document_dir(mode) / FILE


def _read_doc(here, mode):
    path = state_file(here, mode)
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return _Doc(mode, path, None, {})
    except OSError as exc:
        return _Doc(mode, path, None, {}, f"{path.name} of {mode}: could not be read -- {exc}")
    try:
        entries = check_source(json.loads(raw.decode("utf-8-sig")), mode, path.name)
    except (ValueError, UnicodeDecodeError) as exc:
        return _Doc(mode, path, raw, {}, f"{path.name} of {mode}: could not be read -- {exc}")
    return _Doc(mode, path, raw, entries)


def _modes(here):
    return [m for m in SHARE_MODES if m in here.created_modes]


def _check_mode(here, mode):
    if mode not in SHARE_MODES:
        _refuse("bad_mode", f"document {mode!r} -- expected one of {', '.join(SHARE_MODES)}", mode=mode)
    if mode not in here.modes:
        _refuse("no_such_document", f"this project has no {mode} document -- it is laid out as a report alone, and migration gives it the three", mode=mode)


# --- the world: every copy and every record ---------------------------------------------------------

@dataclass(frozen=True)
class _Holder:
    """One document's copy of a block that can be compared: its document, the sharing.Copy (file, block text, where it lies), its parts and its file's time of change."""
    mode: str
    copy: sharing.Copy
    parts: _Parts
    mtime: int

    def value(self, part):
        return self.parts.value(part)


@dataclass(frozen=True)
class Problem:
    """Something `status` could not settle, said by a code of PROBLEMS, an English sentence and the values it is about."""
    code: str
    message: str
    values: dict = field(default_factory=dict)

    def __str__(self):
        return self.message


class _World:
    """Every copy of every shared block of a project and every document's record, as an operation finds them -- or as it will make them (`files`, sharing's records of the section files)."""

    def __init__(self, here, docs, files=None):
        self.here = here
        self.docs = docs
        self.index = sharing.index(here, files)
        self.texts = {sharing._key(f.path): f.text for f in self.index.files}
        self.holders = {}      # shared id -> {mode: _Holder}
        self.bad = {}          # (shared id, mode) -> (code, files)
        self.mentioned = {}    # shared id -> modes holding a copy or a file that names it
        self.flat = {}         # shared id -> True where its copies are compared whole (an object id twice in one of them)
        self.problems = []
        for mode in docs:
            doc = docs[mode]
            if doc.problem:
                self.problems.append(Problem("state_unreadable", doc.problem, {"mode": mode, "file": str(doc.path), "error": doc.problem}))
        cache = {}
        for sid, found in self.index.copies.items():
            by_mode = {}
            for copy in found:
                by_mode.setdefault(copy.mode, []).append(copy)
            unreadable = {}
            for mode, path, why in self.index.skipped.get(sid, ()):
                unreadable.setdefault(mode, []).append(path)
                self.problems.append(Problem("unreadable_copy", f"{Path(path).name} of {mode}: carries the shared block {sid!r} and its tags cannot be read -- {why}", {"mode": mode, "file": str(path), "shared_id": sid}))
            self.mentioned[sid] = set(by_mode) | set(unreadable)
            usable = {}
            for mode, copies_ in by_mode.items():
                if len(copies_) > 1:
                    files = [str(c.file) for c in copies_]
                    self.bad[(sid, mode)] = ("duplicate_copy", files)
                    self.problems.append(Problem("duplicate_copy", f"{mode} holds the shared block {sid!r} in {len(copies_)} files ({', '.join(Path(f).name for f in files)}) -- one copy per document", {"mode": mode, "files": files, "shared_id": sid}))
                elif mode in unreadable:
                    self.bad[(sid, mode)] = ("unreadable_copy", [str(copies_[0].file)] + [str(p) for p in unreadable[mode]])
                else:
                    usable[mode] = copies_[0]
            for mode, paths in unreadable.items():
                if (sid, mode) not in self.bad:
                    self.bad[(sid, mode)] = ("unreadable_copy", [str(p) for p in paths])
            parts = {}
            flat = False
            for mode, copy in usable.items():
                text = _block(copy.block_text)
                if text not in cache:
                    cache[text] = _decompose(copy.block_text)
                parts[mode] = cache[text]
                if parts[mode] is None:
                    flat = True
            if flat:
                parts = {mode: _decompose(copy.block_text, flat=True) for mode, copy in usable.items()}
            self.flat[sid] = flat
            self.holders[sid] = {mode: _Holder(mode, copy, parts[mode], _mtime(copy.file)) for mode, copy in usable.items()}
        for sid, skipped in self.index.skipped.items():
            if sid in self.index.copies:
                continue
            self.mentioned[sid] = {m for m, _p, _w in skipped}
            for mode, path, why in skipped:
                self.bad.setdefault((sid, mode), ("unreadable_copy", []))[1].append(str(path))
                self.problems.append(Problem("unreadable_copy", f"{Path(path).name} of {mode}: carries the shared block {sid!r} and its tags cannot be read -- {why}", {"mode": mode, "file": str(path), "shared_id": sid}))

    @classmethod
    def read(cls, here, files=None):
        return cls(here, {mode: _read_doc(here, mode) for mode in _modes(here)}, files)

    # --- parts and relations ---------------------------------------------------------------------

    def parts_of(self, sid, first=None):
        """The parts of block `sid` in some copy: TEXT, then the object ids -- `first`'s copy's order first, then the others' in document order."""
        holders = self.holders.get(sid, {})
        order = [TEXT]
        ranked = ([first] if first in holders else []) + [m for m in SHARE_MODES if m in holders and m != first]
        for mode in ranked:
            order += [o for o in holders[mode].parts.order if o not in order]
        return order

    def entry(self, mode, sid):
        return self.docs[mode].entries.get(sid) or _Entry()

    def set_pair(self, mode, sid, other, part, pair):
        """`pair` recorded as `mode`'s relation with `other` for one part of block `sid` -- nothing where `mode`'s record cannot be read."""
        doc = self.docs.get(mode)
        if doc is None or doc.problem:
            return
        entry = doc.entries.get(sid)
        if entry is None:
            entry = doc.entries[sid] = _Entry()
        if not entry.known:
            entry.make_known(self.parts_of(sid))
        entry.rel.setdefault(other, {})[part] = pair

    def settle(self, sids=None):
        """Every pair of documents whose copies hold the same part recorded as in step for it, in both records."""
        for sid in (self.holders if sids is None else sids):
            holders = self.holders.get(sid, {})
            modes = [m for m in SHARE_MODES if m in holders]
            # the parts of the copies, and those the records still name -- an object every copy has lost is in step at «not there»
            parts = self.parts_of(sid)
            for mode in modes:
                entry = self.entry(mode, sid)
                named = set(entry.base) | {p for held in entry.rel.values() for p in held}
                parts += sorted(p for p in named if p not in parts)
            for i, a in enumerate(modes):
                for b in modes[i + 1:]:
                    for part in parts:
                        value = holders[a].value(part)
                        if value != holders[b].value(part):
                            continue
                        for one, other in ((a, b), (b, a)):
                            if self.entry(one, sid).pair(other, part) != (value, value):
                                self.set_pair(one, sid, other, part, (value, value))

    def _compact(self, mode, sid, entry):
        """An entry in its smallest form: the relations of documents that no longer name the block dropped, a part's base taken from its relations where every other document stands at one same version, and every relation that says no more than the base dropped."""
        if not entry.known:
            return
        others = sorted(self.mentioned.get(sid, set()) - {mode})
        entry.rel = {o: held for o, held in entry.rel.items() if o in others}
        parts = set(entry.base) | {p for held in entry.rel.values() for p in held} | set(self.parts_of(sid))
        for part in parts:
            pairs = [entry.pair(o, part) for o in others]
            if pairs and all(p == pairs[0] for p in pairs) and pairs[0][0] == pairs[0][1]:
                value = pairs[0][0]
                if part == TEXT or value != ABSENT:
                    entry.base[part] = value
                else:
                    entry.base.pop(part, None)
                for o in others:
                    entry.rel.get(o, {}).pop(part, None)
            base = entry.base_of(part)
            for o in others:
                held = entry.rel.get(o, {})
                if held.get(part) == (base, base):
                    held.pop(part)
        entry.rel = {o: held for o, held in entry.rel.items() if held}
        for part in [p for p, v in entry.base.items() if p != TEXT and v == ABSENT]:
            entry.base.pop(part)

    def state_writes(self, modes=None):
        """(path, new bytes, old bytes or None) of every record that changes -- compacted first; a record that cannot be read is never written, and none is made for a document holding nothing."""
        writes = []
        for mode, doc in self.docs.items():
            if doc.problem or (modes is not None and mode not in modes):
                continue
            for sid, entry in doc.entries.items():
                if sid in self.mentioned and mode in self.mentioned[sid]:
                    self._compact(mode, sid, entry)
            if doc.raw is None and not doc.entries:
                continue
            data = dumps(mode, doc.entries).encode("utf-8")
            if data != doc.raw:
                writes.append((doc.path, data, doc.raw))
        return writes

    # --- states ----------------------------------------------------------------------------------

    def part_state(self, mode, sid, part):
        """(state, pairwise states {other: state}) of one part of block `sid` in document `mode`, the ignore flags left aside."""
        holders = self.holders[sid]
        me = holders[mode]
        entry = self.entry(mode, sid)
        mine_now = me.value(part)
        pairwise = {}
        for other in SHARE_MODES:
            if other == mode or other not in holders:
                continue
            theirs_now = holders[other].value(part)
            own, seen = entry.pair(other, part)
            pairwise[other] = three_way(mine_now, theirs_now, own, seen)
        state = max(pairwise.values(), key=_RANK.get, default="in_sync")
        return state, pairwise

    def candidates(self, mode, sid, part, pairwise):
        """The documents whose version of the part is on offer -- incoming or in conflict -- newest first: grouped by what they hold, the group whose file was changed last first, and in a group the file changed last first (the order of SHARE_MODES where the times are equal)."""
        holders = self.holders[sid]
        offered = [m for m, s in pairwise.items() if s in ("incoming", "conflict")]
        groups = {}
        for m in offered:
            groups.setdefault(holders[m].value(part), []).append(m)
        def newest(ms):
            return max(holders[m].mtime for m in ms)
        ordered = []
        for value in sorted(groups, key=lambda v: (-newest(groups[v]), min(SHARE_MODES.index(m) for m in groups[v]))):
            ordered += sorted(groups[value], key=lambda m: (-holders[m].mtime, SHARE_MODES.index(m)))
        return tuple(ordered), len(groups) > 1


def _mtime(path):
    try:
        return os.stat(path).st_mtime_ns
    except OSError:
        return 0


# --- what status gives ---------------------------------------------------------------------------

def _worst(states):
    return max(states, key=_RANK.get, default="in_sync")


@dataclass(frozen=True)
class ObjectStatus:
    """Where one object of a shared block stands in a document: its block, its id and type; `state` -- what the window shows, `ignored` where the object or its block is ignored -- and `underlying`, the state the ignore hides (what «Réactiver» would show); `others` the documents that make it so (offering a version for incoming and conflict, differing from this copy for local); `sources` the documents offering a version, newest first, `newest` the first of them, `ambiguous` where they offer different versions; `present` whether this copy holds the object; `versions` {mode: its LF text, or None where that copy lacks it} for this document and every other holding the block."""
    shared_id: str
    id: str
    type: str
    state: str
    underlying: str
    others: tuple = ()
    sources: tuple = ()
    newest: str = None
    ambiguous: bool = False
    present: bool = True
    versions: dict = field(default_factory=dict, compare=False, repr=False)

    @property
    def key(self):
        return item_key(self.shared_id, self.id)

    @property
    def ignored(self):
        return self.state == "ignored"


@dataclass(frozen=True)
class BlockStatus:
    """Where one shared block stands in a document: its id, this document's copy (`file`, `rel` its path from the document's folder); `state`, the worst of what the window shows for its text and its objects (`ignored` where the block is ignored), `underlying` the same without the ignore flags; `text_state` and `text_underlying` for the block's own text -- everything between the tags but the objects, which follows the block; `others`, `sources`, `newest`, `ambiguous` for that text, as an ObjectStatus has them; `ignored` whether the block is; `modes` every document holding a copy; `objects` an ObjectStatus each, in this copy's order and then the others'; `versions` {mode: LF block text}; `problem` why the copy cannot be compared (`state` problem)."""
    shared_id: str
    file: Path
    rel: str
    state: str
    underlying: str
    text_state: str = "in_sync"
    text_underlying: str = "in_sync"
    others: tuple = ()
    sources: tuple = ()
    newest: str = None
    ambiguous: bool = False
    ignored: bool = False
    modes: tuple = ()
    objects: tuple = ()
    versions: dict = field(default_factory=dict, compare=False, repr=False)
    problem: str = None

    @property
    def key(self):
        return self.shared_id

    def object(self, object_id):
        return next((o for o in self.objects if o.id == object_id), None)

    @property
    def involved(self):
        """Every other document named by the block's text or one of its objects, in SHARE_MODES' order."""
        found = set(self.others)
        for obj in self.objects:
            found |= set(obj.others)
        return tuple(m for m in SHARE_MODES if m in found)


@dataclass(frozen=True)
class FileStatus:
    """A section file of the document holding shared blocks: its path, `rel` from the document's folder (what structure.Node.file says), the worst state of its blocks as shown (`state`) and without the ignore flags (`underlying`), and the shared ids it holds."""
    path: Path
    rel: str
    state: str
    underlying: str
    blocks: tuple


@dataclass(frozen=True)
class Status:
    """Where everything a document shares stands: `blocks` (BlockStatus, in the order of the files and of the blocks in them), `files` (FileStatus) and the `problems` met."""
    mode: str
    blocks: tuple
    files: tuple
    problems: tuple = ()

    def block(self, shared_id):
        return next((b for b in self.blocks if b.shared_id == shared_id), None)

    def item(self, item):
        """The BlockStatus or ObjectStatus of an item («<shared id>» or «<shared id>/<object id>»), or None."""
        sid, oid = split_key(item)
        block = self.block(sid)
        if block is None or oid is None:
            return block
        return block.object(oid)

    def state_of(self, item):
        found = self.item(item)
        return found.state if found is not None else None

    def file(self, path):
        """The FileStatus of a file -- a path, or its path from the document's folder (`Sections/live-loads.typ`) -- or None where it holds nothing shared."""
        if isinstance(path, Path) or (isinstance(path, str) and os.path.isabs(path)):
            key = sharing._key(path)
            return next((f for f in self.files if sharing._key(f.path) == key), None)
        rel = str(path).replace("\\", "/")
        return next((f for f in self.files if f.rel == rel), None)

    def keys(self, state, underlying=False):
        """Every item -- blocks and objects -- in `state` (as shown, or `underlying`), blocks before their objects."""
        found = []
        for block in self.blocks:
            if (block.underlying if underlying else block.state) == state:
                found.append(block.key)
            found += [o.key for o in block.objects if (o.underlying if underlying else o.state) == state]
        return tuple(found)

    @property
    def incoming(self):
        return self.keys("incoming")

    @property
    def conflicts(self):
        return self.keys("conflict")

    @property
    def ignored(self):
        return self.keys("ignored")

    def counts(self):
        """{state: number of blocks in it}, every state named."""
        counts = {state: 0 for state in STATES}
        for block in self.blocks:
            counts[block.state] += 1
        return counts


def _rel(here, mode, path):
    try:
        return Path(path).resolve().relative_to(here.document_dir(mode).resolve()).as_posix()
    except ValueError:
        return Path(path).name


def _status_of(world, mode):
    here = world.here
    blocks = []
    for sid in sorted(world.mentioned, key=lambda s: s):
        if mode not in world.mentioned[sid]:
            continue
        holders = world.holders.get(sid, {})
        modes = tuple(m for m in SHARE_MODES if m in world.mentioned[sid])
        if (sid, mode) in world.bad or mode not in holders:
            code, files = world.bad.get((sid, mode), ("unreadable_copy", []))
            path = Path(files[0]) if files else here.document_dir(mode)
            why = "the file's tags cannot be read" if code == "unreadable_copy" else "two files of the document carry it"
            blocks.append(BlockStatus(sid, path, _rel(here, mode, path), "problem", "problem", "problem", "problem", modes=modes, problem=why))
            continue
        me = holders[mode]
        entry = world.entry(mode, sid)
        others_holding = [m for m in SHARE_MODES if m in holders and m != mode]
        versions = {m: _block(holders[m].copy.block_text) for m in SHARE_MODES if m in holders}
        text_under, text_pairwise = world.part_state(mode, sid, TEXT)
        text_sources, text_ambiguous = world.candidates(mode, sid, TEXT, text_pairwise)
        objects = []
        for oid in world.parts_of(sid, first=mode)[1:]:
            under, pairwise = world.part_state(mode, sid, oid)
            sources, ambiguous = world.candidates(mode, sid, oid, pairwise)
            shown = "ignored" if (entry.ignored or oid in entry.ignored_objects) else under
            kind = me.parts.types.get(oid) or next((holders[m].parts.types[oid] for m in others_holding if oid in holders[m].parts.types), "")
            others = sources if under in ("incoming", "conflict") else tuple(m for m, s in pairwise.items() if s == "local")
            objects.append(ObjectStatus(sid, oid, kind, shown, under, others, sources, sources[0] if sources else None, ambiguous,
                                        oid in me.parts.texts, {m: holders[m].parts.texts.get(oid) for m in SHARE_MODES if m in holders}))
        text_shown = "ignored" if entry.ignored else text_under
        state = "ignored" if entry.ignored else _worst([text_shown] + [o.state for o in objects])
        underlying = _worst([text_under] + [o.underlying for o in objects])
        others = text_sources if text_under in ("incoming", "conflict") else tuple(m for m, s in text_pairwise.items() if s == "local")
        blocks.append(BlockStatus(sid, me.copy.file, _rel(here, mode, me.copy.file), state, underlying, text_shown, text_under, others,
                                  text_sources, text_sources[0] if text_sources else None, text_ambiguous, entry.ignored, modes,
                                  tuple(objects), versions))
    blocks.sort(key=lambda b: (b.rel, world.holders.get(b.shared_id, {}).get(mode).copy.start if mode in world.holders.get(b.shared_id, {}) else 0))
    files = {}
    for block in blocks:
        files.setdefault(sharing._key(block.file), []).append(block)
    file_status = tuple(FileStatus(found[0].file, found[0].rel, _worst(b.state for b in found), _worst(b.underlying for b in found), tuple(b.shared_id for b in found))
                        for found in files.values())
    return Status(mode, tuple(blocks), file_status, tuple(world.problems))


def status(here, mode, settle=True):
    """Where every shared block of document `mode` -- and every object inside it -- stands: a `Status`.

    It reads every section file of the project and every document's record; `settle` (the default) records, in every record that can be read, that copies found holding the same part are in step -- what initialises a project seen for the first time, and what keeps two copies made equal outside Woodcore from showing a conflict later. A record that cannot be written is said in the problems (`settle_failed`) and changes nothing else. Refused: a document that is none (`bad_mode`) or that the project lacks (`no_such_document`).
    """
    _check_mode(here, mode)
    world = _World.read(here)
    if settle:
        world.settle()
        writes = world.state_writes()
        if writes:
            try:
                sharing._commit(writes)
            except (sharing.SharingError, OSError) as exc:
                world.problems.append(Problem("settle_failed", f"copies found equal could not be recorded as such -- {exc}", {"error": str(exc)}))
    return _status_of(world, mode)


# --- writing -------------------------------------------------------------------------------------

def _commit(writes):
    """sharing's `_commit`, its refusals said as SyncErrors with the same code -- a record made new that another window made meanwhile is a change made meanwhile."""
    try:
        return sharing._commit(writes)
    except SyncError:
        raise
    except sharing.SharingError as exc:
        code = exc.code if exc.code in CODES else "changed_meanwhile" if exc.code == "file_exists" else "write_failed"
        raise SyncError(str(exc), code, **exc.values) from None


def _own_doc(world, mode):
    doc = world.docs[mode]
    if doc.problem:
        _refuse("state_unreadable", f"{doc.problem} -- Woodcore does not rewrite it; repair or remove it", file=str(doc.path), error=doc.problem)
    return doc


def _holder(world, mode, sid, item=None):
    """This document's copy of block `sid`, refused by name where there is none or it cannot be compared."""
    item = item or sid
    if (sid, mode) in world.bad:
        code, files = world.bad[(sid, mode)]
        _refuse("unreadable_copy", f"{mode}'s copy of the shared block {sid!r} cannot be compared -- " + ("its file's tags cannot be read" if code == "unreadable_copy" else "two files of the document carry it"), item=item, files=files)
    holder = world.holders.get(sid, {}).get(mode)
    if holder is None:
        _refuse("no_such_item", f"document {mode} holds no shared block {sid!r}", item=item)
    return holder


def _check_tags_of(path, text):
    problems = structure.check_tags(text)
    if problems:
        _refuse("bad_block", f"{Path(path).name}: the block would leave the file's tags unreadable -- " + "; ".join(problems), file=str(path), problems=problems)


def _new_file_texts(world, edits):
    """{file key: (path, old text, new text)} of every file whose blocks `edits` ({(shared id, mode): new block text, in the copy's own line endings}) replace -- each block between its two tags, the rest of the file as it was."""
    by_file = {}
    for (sid, mode), new_block in edits.items():
        copy = world.holders[sid][mode].copy
        by_file.setdefault(sharing._key(copy.file), []).append((copy, new_block))
    out = {}
    for key, found in by_file.items():
        path = found[0][0].file
        old = world.texts[key]
        new = old
        for copy, new_block in sorted(found, key=lambda pair: -pair[0].start):
            new = new[:copy.start] + new_block + new[copy.end:]
        if new != old:
            _check_tags_of(path, new)
            out[key] = (path, old, new)
    return out


def _files_after(world, new_texts):
    """sharing's records of every section file as it will be once `new_texts` are written."""
    return [sharing._file(f.mode, f.path, new_texts[sharing._key(f.path)][2]) if sharing._key(f.path) in new_texts else f for f in world.index.files]


def _object_text(part, decided, me):
    """The LF text object `part` has in the result, or None where the result holds none: the decided source's, else this copy's."""
    if part in decided and decided[part] is not None:
        return decided[part].parts.texts.get(part)
    return me.parts.texts.get(part)


def _rebuilt(me, decided, source):
    """The block rebuilt on `source`'s text -- its lines and the places of its objects -- each object as decided or as this copy has it; an object the result keeps and `source`'s text has no place for goes at the end of the block, a blank line before it. LF."""
    out, placed = [], set()
    for kind, value in source.parts.skeleton:
        if kind == "line":
            out.append(_lf(value))
            continue
        text = _object_text(value, decided, me)
        if text is not None:
            out.append(text)
            placed.add(value)
    wanted = [o for o in me.parts.order if _object_text(o, decided, me) is not None]
    wanted += [o for o, src in decided.items() if o != TEXT and src is not None and src.parts.texts.get(o) is not None]
    for oid in dict.fromkeys(wanted):
        if oid in placed:
            continue
        if out and out[-1].strip():
            out.append("\n")
        out.append(_object_text(oid, decided, me))
        placed.add(oid)
    return "".join(out)


def _blank_run(source, oid, before=True):
    """How many blank lines stand right before (or after) object `oid` in `source`'s text -- what separates it there."""
    skeleton = list(source.parts.skeleton)
    at = next(i for i, (kind, value) in enumerate(skeleton) if kind == "object" and value == oid)
    run, step = 0, (-1 if before else 1)
    i = at + step
    while 0 <= i < len(skeleton) and skeleton[i][0] == "line" and _blank(skeleton[i][1]):
        run += 1
        i += step
    return run


def _spliced(me, decided, newline):
    """This copy's block with each decided object written in its place -- its two tag lines and what lies between -- every other line kept byte for byte: an object the source does not hold any more is taken out, one this copy does not hold yet is put after the object it follows in the source (else before the one it precedes, else at the end of the block), separated as it is there."""
    lines = list(me.parts.lines)
    edits, inserts = {}, {}
    for part, source in decided.items():
        if part == TEXT or source is None:
            continue
        new = source.parts.texts.get(part)
        if part in me.parts.spans:
            start, end = me.parts.spans[part]
            nl = _ending(lines[start]) or newline
            if new is not None:
                edits[start] = (end + 1, new.replace("\n", nl))
                continue
            # taken out with the blank lines that part it from what precedes it, where blank lines follow it too -- the separation an inserted object is given
            first = start
            if end + 1 >= len(lines) or _blank(lines[end + 1]):
                while first > 0 and _blank(lines[first - 1]) and first - 1 not in edits:
                    first -= 1
            edits[first] = (end + 1, "")
            continue
        if new is None:
            continue
        order = list(source.parts.order)
        at = order.index(part)
        previous = next((o for o in reversed(order[:at]) if o in me.parts.spans), None)
        following = next((o for o in order[at + 1:] if o in me.parts.spans), None)
        body = new.replace("\n", newline)
        if previous is not None:
            where = me.parts.spans[previous][1] + 1
            chunk = newline * _blank_run(source, part, before=True) + body
        elif following is not None:
            where = me.parts.spans[following][0]
            chunk = body + newline * _blank_run(source, part, before=False)
        else:
            where = len(lines)
            chunk = (newline if lines and not _blank(lines[-1]) else "") + body
        inserts.setdefault(where, []).append(chunk)
    out, index = [], 0
    while True:
        out += inserts.get(index, [])
        if index >= len(lines):
            break
        if index in edits:
            end, replacement = edits[index]
            out.append(replacement)
            index = end
            continue
        out.append(lines[index])
        index += 1
    return "".join(out)


@dataclass(frozen=True)
class ImportResult:
    """What `import_changes` did: `imported` {item: the document whose version was taken}, `kept` the items this document kept its own version of, `unchanged` the items asked for that had nothing to import, the section `files` written and the records (`states`) written, and `conflicts` -- the items in conflict an import of everything (`items=None`) left as they were for want of a choice."""
    imported: dict
    kept: tuple
    unchanged: tuple
    files: tuple
    states: tuple
    conflicts: tuple = ()

    @property
    def written(self):
        return self.files + self.states


def _choice_for(choices, sid, part):
    if part != TEXT and item_key(sid, part) in choices:
        return choices[item_key(sid, part)]
    return choices.get(sid)


def import_changes(here, mode, items=None, choices=None):
    """What other documents changed, taken into document `mode`'s copies -- **between the tags only**, the rest of every file as it was, line endings kept. Returns an `ImportResult`.

    `items` -- None for everything incoming that is not ignored (and every conflict `choices` settles; a conflict without a choice is then left as it is and named in the result's `conflicts`), else a list of «<shared id>» (the block: its text and every object of it on offer) and «<shared id>/<object id>» (that object alone: only its two tag lines and what lies between are rewritten, or it is taken out where the other version no longer holds it, or put after the object it follows there where this copy does not hold it yet). An item in conflict is imported only with a choice, and one asked for by name without it refuses (`needs_choice`): `choices` {item: "mine" | "theirs" | <mode>} -- a block's choice standing for its text and for every object of it without a choice of its own; "theirs" is the newest version on offer (`ObjectStatus.newest`), a mode that document's version, "mine" keeps this one, which then counts as decided (in step, until either side changes again). An incoming item takes the newest version unless a choice says otherwise.

    All or nothing (sharing's `_commit`): the section files and the records are written together, beside themselves and moved into place; a file changed since it was read refuses the whole (`changed_meanwhile`), a write that fails puts back what was written (`write_failed`). Refused before anything is written: a document that is none or that the project lacks (`bad_mode`, `no_such_document`), an item that is not one (`bad_item`) or that the document does not hold (`no_such_item`), an ignored item asked for by name (`ignored`), a copy that cannot be compared (`unreadable_copy`), a conflict with no choice -- every one named (`needs_choice`) --, a choice that is none (`bad_choice`), this document's record unreadable (`state_unreadable`), and a result that would leave a file's tags unreadable (`bad_block`).
    """
    _check_mode(here, mode)
    choices = {item_key(*split_key(item)): choice for item, choice in dict(choices or {}).items()}
    world = _World.read(here)
    _own_doc(world, mode)
    held = [sid for sid in sorted(world.holders) if mode in world.holders[sid]]

    # what is asked for
    wanted = {}          # shared id -> parts asked for (None: every part on offer)
    explicit = set()     # items asked for by name
    if items is None:
        for sid in held:
            if (sid, mode) not in world.bad:
                wanted[sid] = None
    else:
        if isinstance(items, str):
            items = [items]
        for item in items:
            sid, oid = split_key(item)
            _holder(world, mode, sid, item_key(sid, oid))
            entry = world.entry(mode, sid)
            if entry.ignored or (oid is not None and oid in entry.ignored_objects):
                _refuse("ignored", f"{mode} ignores {item_key(sid, oid)!r} -- reactivate it to import it", item=item_key(sid, oid))
            if oid is not None and oid not in world.parts_of(sid):
                _refuse("no_such_item", f"no copy of the shared block {sid!r} holds an object {oid!r}", item=item_key(sid, oid))
            explicit.add(item_key(sid, oid))
            if oid is None:
                wanted[sid] = None
            elif wanted.get(sid, ()) is not None:
                wanted.setdefault(sid, set()).add(oid)

    for item, choice in choices.items():
        sid, oid = split_key(item)
        if sid not in world.holders or mode not in world.holders[sid]:
            _refuse("no_such_item", f"document {mode} holds no shared block {sid!r}", item=item_key(sid, oid))
        if choice in (MINE, THEIRS):
            continue
        if choice not in SHARE_MODES or choice == mode or choice not in world.holders[sid]:
            others = [m for m in SHARE_MODES if m in world.holders[sid] and m != mode]
            _refuse("bad_choice", f"{choice!r} for {item_key(sid, oid)!r} -- expected «mine», «theirs» or a document holding a copy ({', '.join(others) or 'none'})", item=item_key(sid, oid), choice=choice)

    # the decisions, part by part
    plan = {}            # shared id -> {part: (source _Holder or None for mine, candidates)}
    needing, left, unchanged, imported, kept = [], [], [], {}, []
    for sid, parts in wanted.items():
        holders = world.holders[sid]
        entry = world.entry(mode, sid)
        decided = {}
        for part in world.parts_of(sid, first=mode):
            if parts is not None and part not in parts:
                continue
            if entry.ignored or (part != TEXT and part in entry.ignored_objects):
                continue
            state, pairwise = world.part_state(mode, sid, part)
            if state not in ("incoming", "conflict"):
                if part != TEXT and item_key(sid, part) in explicit:
                    unchanged.append(item_key(sid, part))
                continue
            offered, _ambiguous = world.candidates(mode, sid, part, pairwise)
            choice = _choice_for(choices, sid, part)
            if choice is None:
                if state == "conflict":
                    (left if items is None else needing).append(item_key(sid, part or None))
                    continue
                choice = THEIRS
            if choice == MINE:
                decided[part] = (None, offered)
            else:
                source = holders[offered[0]] if choice == THEIRS else holders[choice]
                decided[part] = (source, offered)
        if parts is None and not decided and sid in explicit:
            unchanged.append(sid)
        if decided:
            plan[sid] = decided
    if needing:
        _refuse("needs_choice", "a conflict is imported with a choice of version -- " + ", ".join(needing) + ": «mine», «theirs» or a document's name", items=needing)

    # the new blocks
    edits = {}
    for sid, decided in plan.items():
        me = world.holders[sid][mode]
        sources = {part: src for part, (src, _offered) in decided.items()}
        text_source = sources.get(TEXT)
        if text_source is not None and text_source.value(TEXT) != me.value(TEXT):
            new_block = _rebuilt(me, sources, text_source).replace("\n", me.copy.newline)
        else:
            new_block = _spliced(me, sources, me.copy.newline)
        if new_block != me.copy.block_text:
            edits[(sid, mode)] = new_block
        for part, (src, _offered) in decided.items():
            key = item_key(sid, part or None)
            if src is None:
                kept.append(key)
            else:
                imported[key] = src.mode
    new_texts = _new_file_texts(world, edits)
    # where an object came in or went out alone, the block's text changed with it -- not by this document's hand: towards every document it had not changed it for it still has not, and that document has not seen it change
    rebased = {}
    for sid, decided in plan.items():
        if TEXT in decided:
            continue
        old_text = world.holders[sid][mode].value(TEXT)
        entry = world.entry(mode, sid)
        rebased[sid] = (old_text, {other: (entry.pair(other, TEXT), world.entry(other, sid).pair(mode, TEXT))
                                   for other in world.holders[sid] if other != mode and entry.pair(other, TEXT)[0] == old_text})
    after = _World(here, world.docs, _files_after(world, new_texts))
    for sid, (old_text, pairs) in rebased.items():
        if sid not in after.holders or mode not in after.holders[sid]:
            continue
        new_text = after.holders[sid][mode].value(TEXT)
        if new_text == old_text:
            continue
        for other, ((_own, seen), (their_own, their_seen)) in pairs.items():
            after.set_pair(mode, sid, other, TEXT, (new_text, seen))
            if their_seen == old_text:
                after.set_pair(other, sid, mode, TEXT, (their_own, new_text))

    # what this document has now seen, and decided
    for sid, decided in plan.items():
        if sid not in after.holders or mode not in after.holders[sid]:
            continue
        mine_now = after.holders[sid][mode]
        for part, (_src, offered) in decided.items():
            value = mine_now.value(part)
            for other in offered:
                theirs = after.holders[sid][other].value(part)
                if theirs != value:
                    after.set_pair(mode, sid, other, part, (value, theirs))
    after.settle()
    file_writes = [(path, new.encode("utf-8"), old.encode("utf-8")) for path, old, new in new_texts.values()]
    state_writes = after.state_writes()
    _commit(file_writes + state_writes)
    return ImportResult(imported, tuple(kept), tuple(dict.fromkeys(unchanged)), tuple(p for p, _n, _o in file_writes), tuple(p for p, _n, _o in state_writes), tuple(left))


# --- ignoring ------------------------------------------------------------------------------------

@dataclass(frozen=True)
class IgnoreResult:
    """What `ignore` or `reactivate` did: the items whose flag changed, and the records written."""
    changed: tuple
    states: tuple


def _flag(here, mode, items, on):
    _check_mode(here, mode)
    world = _World.read(here)
    doc = _own_doc(world, mode)
    if isinstance(items, str):
        items = [items]
    changed = []
    for item in items or ():
        sid, oid = split_key(item)
        if mode not in world.mentioned.get(sid, set()):
            _refuse("no_such_item", f"document {mode} holds no shared block {sid!r}", item=item_key(sid, oid))
        if oid is not None and oid not in world.parts_of(sid) and oid not in world.entry(mode, sid).ignored_objects:
            _refuse("no_such_item", f"no copy of the shared block {sid!r} holds an object {oid!r}", item=item_key(sid, oid))
        entry = doc.entries.get(sid)
        if entry is None:
            entry = doc.entries[sid] = _Entry()
        if oid is None:
            if entry.ignored != on:
                entry.ignored = on
                changed.append(item_key(sid))
        elif (oid in entry.ignored_objects) != on:
            (entry.ignored_objects.add if on else entry.ignored_objects.discard)(oid)
            changed.append(item_key(sid, oid))
    world.settle()
    writes = world.state_writes()
    _commit(writes)
    return IgnoreResult(tuple(changed), tuple(p for p, _n, _o in writes))


def ignore(here, mode, items):
    """«Ignorer»: the items -- «<shared id>» for a block, «<shared id>/<object id>» for one object -- never imported into document `mode` again and shown `ignored`, **permanently**, until `reactivate`. Nothing else changes: what the others change keeps being seen, and shows as incoming again once reactivated. Returns an IgnoreResult. Refused: `bad_mode`, `no_such_document`, `bad_item`, `no_such_item`, `state_unreadable`; a failed write puts back what was written (`write_failed`)."""
    return _flag(here, mode, items, True)


def reactivate(here, mode, items):
    """«Réactiver»: the items no longer ignored in document `mode` -- they show their state again, incoming where the others changed meanwhile. An item that is not ignored is left alone. Returns an IgnoreResult; refused as `ignore` is."""
    return _flag(here, mode, items, False)


# --- Woodcore's own edits --------------------------------------------------------------------------

@dataclass(frozen=True)
class LocalResult:
    """What `record_local_edit` or `write_local` did: the section file written (None for record_local_edit) and the records written."""
    file: Path
    states: tuple


def _settle_before(world, mode, sid, before):
    """Every other document whose copy holds what `before` held, part by part, recorded as in step with this one at `before`, in both records -- as if this copy still held it."""
    holders = world.holders.get(sid, {})
    if mode not in holders:
        return
    parts = _decompose(before, flat=world.flat.get(sid, False))
    if parts is None:            # an object id twice in what was loaded: nothing to compare it by
        return
    others = [m for m in SHARE_MODES if m in holders and m != mode]
    for part in set(world.parts_of(sid)) | set(parts.values):
        value = parts.value(part)
        for other in others:
            if holders[other].value(part) == value:
                world.set_pair(mode, sid, other, part, (value, value))
                world.set_pair(other, sid, mode, part, (value, value))


def record_local_edit(here, mode, shared_id, before=None):
    """Woodcore has just written document `mode`'s copy of block `shared_id` itself (its right pane): the records are kept so that the edit shows as **local** in this document and **incoming** in the others -- the same as an edit made in VS Code, nothing else being written. `before` is the block as it stood before the edit (the editor's loaded text): wherever another copy held what `before` held, the two are recorded as having been in step at `before` -- so that a project never synchronised before, or two copies made equal outside Woodcore and not looked at since, does not show the edit as a conflict. Returns a LocalResult. Refused: `bad_mode`, `no_such_document`, `bad_item`, `no_such_item`, `unreadable_copy`, `state_unreadable`."""
    _check_mode(here, mode)
    sid, _oid = split_key(shared_id)
    world = _World.read(here)
    _own_doc(world, mode)
    _holder(world, mode, sid)
    if before is not None:
        _settle_before(world, mode, sid, _block(before))
    world.settle([sid])
    writes = world.state_writes()
    _commit(writes)
    return LocalResult(None, tuple(p for p, _n, _o in writes))


def write_local(here, mode, shared_id, new_block, loaded_block):
    """`new_block` written between the tags of document `mode`'s copy of block `shared_id` -- **that copy alone**: the others become incoming. Only the characters between the two tag lines change, in the line ending the copy's opening tag has; `loaded_block` is the block as Woodcore's editor loaded it, and a copy that holds something else by now refuses (`changed_meanwhile`), as does a file changed between being read and written. The edit is recorded as `record_local_edit` records one. Returns a LocalResult. Refused besides: `bad_block` -- a block holding shared or structure tags, unpaired object tags, or that would leave the file's tags unreadable."""
    _check_mode(here, mode)
    sid, _oid = split_key(shared_id)
    try:
        sharing._check_block(new_block)
    except sharing.SharingError as exc:
        raise SyncError(str(exc), "bad_block", **exc.values) from None
    world = _World.read(here)
    _own_doc(world, mode)
    me = _holder(world, mode, sid)
    if _block(me.copy.block_text) != _block(loaded_block):
        _refuse("changed_meanwhile", f"{me.copy.file.name}: its block {sid!r} changed since it was loaded -- nothing was written; load it again", file=str(me.copy.file))
    block = _block(new_block).replace("\n", me.copy.newline)
    new_texts = _new_file_texts(world, {(sid, mode): block}) if block != me.copy.block_text else {}
    after = _World(here, world.docs, _files_after(world, new_texts))
    _settle_before(after, mode, sid, _block(loaded_block))
    after.settle([sid])
    file_writes = [(path, new.encode("utf-8"), old.encode("utf-8")) for path, old, new in new_texts.values()]
    state_writes = after.state_writes()
    _commit(file_writes + state_writes)
    return LocalResult(me.copy.file if file_writes else None, tuple(p for p, _n, _o in state_writes))


# --- what a module that makes or unmakes copies calls -------------------------------------------------------

def share_writes(here, source_mode, shared_ids, files, targets):
    """The records as `share` leaves them -- and as any operation that makes a copy of a shared block leaves them (calc/doc_import.py's linked import of an object) --, as (path, new bytes, old bytes) writes for its own commit: each new copy in step with the source and standing with every third document as the source stands with it -- the copy is the source's block -- every third document standing with the copy as it stands with the source, and every pair of copies holding the same recorded as in step. `files` are sharing's records of the section files as they will be. A record that cannot be read is left alone."""
    world = _World(here, {mode: _read_doc(here, mode) for mode in _modes(here)}, files)
    for sid in shared_ids:
        holders = world.holders.get(sid, {})
        if source_mode not in holders:
            continue
        source_entry = world.entry(source_mode, sid)
        parts = world.parts_of(sid)
        thirds = [m for m in SHARE_MODES if m in holders and m != source_mode and m not in targets]
        for target in targets:
            if target not in holders or world.docs[target].problem:
                continue
            entry = _Entry(known=True, base={p: holders[target].value(p) for p in parts if holders[target].value(p) != ABSENT})
            for third in thirds:
                for part in parts:
                    entry.rel.setdefault(third, {})[part] = source_entry.pair(third, part)
            world.docs[target].entries[sid] = entry
        for third in thirds:
            third_entry = world.entry(third, sid)
            for target in targets:
                if target in holders:
                    for part in parts:
                        world.set_pair(third, sid, target, part, third_entry.pair(source_mode, part))
    world.settle(list(shared_ids))
    return world.state_writes()


def stop_writes(here, removed):
    """The records as `stop_sharing` leaves them: the entry of each (mode, shared id) of `removed` -- a copy whose tags were taken off -- dropped, its ignore flags with it."""
    writes = []
    for mode in _modes(here):
        sids = {sid for m, sid in removed if m == mode}
        if not sids:
            continue
        doc = _read_doc(here, mode)
        if doc.problem or doc.raw is None or not sids & set(doc.entries):
            continue
        for sid in sids:
            doc.entries.pop(sid, None)
        writes.append((doc.path, dumps(mode, doc.entries).encode("utf-8"), doc.raw))
    return writes


# The names these two had while they were private, which calc/doc_import.py calls: kept, the same functions.
_share_writes = share_writes
