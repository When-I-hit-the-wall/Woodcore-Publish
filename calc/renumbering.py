"""Deleting a position and numbering the ones after it again, everywhere at once (issue #9, spec docs/requirements/completed/2026-10-08-plan-positions-cotes-numerotation-sections.md, REQ-004, REQ-005, REQ-016, ARCH-001).

The engineer, 08.10.2026: «Quand une position est supprimée, renuméroter en cascade toutes celles qui la suivent : supprimer S110 fait de S111 un S110, de S130 un S129, etc. La renumérotation est reportée partout : remplacement dans tous les documents Typst du projet.» And, asked what becomes of what cites the position deleted: «Refuser tant qu'elle est citée. Il est cependant possible de choisir "Copier les valeurs" afin que, partout où la position est appelée, un message orange apparaît et indique que les calculs portent sur les valeurs d'une ancienne position.»

Two steps, so that the window can show what is about to happen before anything happens:

* `preview(here, deleted, keep_values)` reads and writes nothing but what it returns: the table {old id: new id}, what still cites a position deleted, and every occurrence of an id in a file it would rewrite, each of which the engineer may untick;
* `apply(here, preview, unchecked)` writes it, **all or nothing** (`sharing.commit`: a file changed since the preview stops everything), after copying the bytes of every file it touches into the project's archives with a note of intent -- a renumbering is no step of «Annuler», and that copy is how it is undone (`restore`).

What carries a position's id, and so what is rewritten: positions.json (written by its own store, `positions_store.encode`), the plans' element labels -- never a load's, whose `L101` only looks like a position --, the checks' `position`, the schemas' elements' `position` (rewritten **textually**: the JSON tokens of those ids change and not one other byte), and every `.typ` the engineer writes -- the three documents' and the sheets of `Plans/` --, never the engine's copy, the export, the archives, a form (`Template/`) or the journal, which is history. An id is replaced whole, by one pass of one expression over each file: S11 is not S110, `#D101` is a colour, `S101.png` a file, `S110-old` an archived position, and S111 → S110 cannot be caught again by S110 → S109.

Qt-free: the window calls it and shows it, and the Positions tab's renaming of a position is the same table of one entry (`rename_preview`).
"""

import datetime
import json
import re
from dataclasses import dataclass, field
from json.decoder import scanstring
from pathlib import Path

import engine
import positions_store
import project
import sharing
import validation
from domains import plan as plan_model

# An id the cascade renumbers: one letter, the storey's numbering character, digits -- S110, TU01, T0100 (positions_store.propose_id). Any other id is left as it is.
NUMBERED = re.compile(r"^([^\W\d_])([^\W_])(\d+)$")

ARCHIVE_FILE = "positions-archive.json"
ARCHIVE_FORMAT = "woodcore-positions-archive"
ARCHIVE_VERSION = "1.0"
OLD_SUFFIX = "-old"

BACKUP_PREFIX = "renumerotation"
INTENT_FILE = "intent.json"

# What the occurrences of an id may sit against: no letter, digit or _ either side, no # before (a colour, «#D101»), no «.ext» after (a file, «S101.png») and no «-old» after (an archived position is no position).
BEFORE = r"(?<![\w#])"
AFTER = r"(?![\w]|\.\w|-old)"


class RenumberError(validation.ValidationError):
    """A renumbering refused, said by name: `code` and the `values` it is about."""

    def __init__(self, message, code, **values):
        super().__init__(message)
        self.code = code
        self.values = values


@dataclass
class Occurrence:
    """One id in one file: where (`path`, `start`, `end` in the decoded text, its `line` number and the line itself), what it is (`old`) and what it becomes (`new`), and the kind of file (`typ` or `json`). `key` names it for unticking."""
    path: Path
    start: int
    end: int
    line: int
    text: str
    old: str
    new: str
    kind: str

    @property
    def key(self):
        return (str(self.path), self.start)


@dataclass
class Preview:
    """What a renumbering would do, read and not written: `mapping` {old: new} of the positions numbered again (and of the archived names, where values are kept), `deleted` the ids taken out, `cited` {deleted id: [Occurrence]} what still names one, `drawn` {deleted id: [plan file]} the plans that still draw one, `occurrences` every replacement in the files, and `files` {path: bytes read}."""
    deleted: list
    mapping: dict
    keep_values: bool
    cited: dict = field(default_factory=dict)
    drawn: dict = field(default_factory=dict)
    occurrences: list = field(default_factory=list)
    files: dict = field(default_factory=dict)
    archived: dict = field(default_factory=dict)
    rows: list = field(default_factory=list)
    old_rows: list = field(default_factory=list)
    today: str = ""

    @property
    def refused(self):
        """Why it may not be applied as it stands, or "" -- a deleted position still drawn on a plan, or still cited where its values are not kept."""
        if any(self.drawn.values()):
            names = ", ".join(sorted(pid for pid, plans in self.drawn.items() if plans))
            return f"drawn on a plan still: {names} -- take the element off the plan first"
        if not self.keep_values and any(self.cited.values()):
            names = ", ".join(sorted(pid for pid, found in self.cited.items() if found))
            return f"still cited: {names} -- take the citations out, or keep the values («Copier les valeurs»)"
        return ""


# --- the table of new numbers ------------------------------------------------------------

def cascade(ids, deleted):
    """{old: new} for every id after a deleted one of the same letter and storey, moved down by as many deleted below it: S110 deleted makes S111 S110 and S130 S129. Each keeps its number's width (S1100 stays four digits wide until it cannot). Ids that are not numbered so are left out. Raises RenumberError where two ids would meet."""
    groups = {}
    for pid in ids:
        match = NUMBERED.match(pid)
        if match:
            groups.setdefault((match.group(1), match.group(2)), []).append((int(match.group(3)), match.group(3), pid))
    gone = {}
    for pid in deleted:
        match = NUMBERED.match(pid)
        if match:
            gone.setdefault((match.group(1), match.group(2)), []).append(int(match.group(3)))
    mapping = {}
    for key, numbers in gone.items():
        for number, digits, pid in groups.get(key, []):
            if pid in deleted:
                continue
            below = sum(1 for n in numbers if n < number)
            if below:
                mapping[pid] = key[0] + key[1] + str(number - below).zfill(len(digits))
    staying = set(ids) - set(deleted) - set(mapping)
    targets = list(mapping.values())
    if len(set(targets)) != len(targets) or staying & set(targets):
        clash = sorted((set(t for t in targets if targets.count(t) > 1)) | (staying & set(targets)))
        raise RenumberError(f"numbering again would give {', '.join(clash)} twice", "clash", ids=clash)
    return mapping


def archived_name(pid, taken):
    """The name a deleted position's values are kept under: «S110-old», then «S110-old2» … where the name is taken."""
    name, n = pid + OLD_SUFFIX, 1
    while name in taken:
        n += 1
        name = f"{pid}{OLD_SUFFIX}{n}"
    return name


# --- where ids are --------------------------------------------------------------------------

def typst_files(here):
    """Every .typ the engineer writes that may cite a position: the three documents' sections and the sheets of `Plans/` -- never the engine's copy and the export (`_woodcore/`), the archives, a form (`Template/`)."""
    import sheets
    roots = [here.document_dir(mode) for mode in here.modes]
    roots += sheets.folders(here)   # Plans/ before, the sheets of each kind in their plan tab's exports laid out by folders (issue #64)
    if here.has_folders:
        roots += [here.formulas_dir] + [here.domain_dir(kind) for kind in project.DOMAIN_FOLDERS]   # the domains' files may cite a position too (issue #64)
    never = [Path(here.generated_dir).resolve(), Path(here.archives_dir).resolve(), Path(here.template_dir).resolve()]
    found = []
    for root in roots:
        if not root.is_dir():
            continue
        for file in sorted(root.rglob("*.typ")):
            resolved = file.resolve()
            if any(resolved == n or n in resolved.parents for n in never):
                continue
            if here.has_folders and project.DOMAIN_ARCHIVES in file.relative_to(root).parts[:-1]:
                continue   # a domain's or a sheet's archives: history, as the project's are
            if resolved not in found:
                found.append(resolved)
    return found


def json_stores(here):
    """(file, rule) for every JSON source that carries a position's id, `rule(document, path)` saying whether the string at `path` is one: a plan's element label (not a load's), a check's position, a schema element's position."""
    def plan_label(doc, path):
        if len(path) != 3 or path[0] != "elements" or path[2] != "label":
            return False
        elements = doc.get("elements") or []
        return isinstance(path[1], int) and path[1] < len(elements) and not plan_model.is_load(elements[path[1]].get("type", ""))

    def check_position(_doc, path):
        return path == ("position",)

    def schema_position(_doc, path):
        return len(path) == 3 and path[0] == "elements" and path[2] == "position"

    stores = []
    for folder, rule in ((here.plans_dir, plan_label), (here.checks_dir, check_position), (here.details_dir, schema_position)):
        folder = Path(folder)
        if folder.is_dir():
            stores.extend((file, rule) for file in sorted(folder.glob("*.json")))
    return stores


def _json_strings(text):
    """Every string value of a JSON text with its path and its span: [(path, start, end, value)], the span that of the token, its quotes included. Keys are not values."""
    out = []
    ws = re.compile(r"[ \t\r\n]*")
    literal = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?|true|false|null")

    def skip(i):
        return ws.match(text, i).end()

    def value(i, path):
        i = skip(i)
        c = text[i]
        if c == "{":
            i = skip(i + 1)
            if text[i] == "}":
                return i + 1
            while True:
                key, i = scanstring(text, skip(i) + 1)
                i = skip(i)
                assert text[i] == ":", f"':' expected at {i}"
                i = value(i + 1, path + (key,))
                i = skip(i)
                if text[i] == ",":
                    i += 1
                    continue
                assert text[i] == "}", f"'}}' expected at {i}"
                return i + 1
        if c == "[":
            i = skip(i + 1)
            if text[i] == "]":
                return i + 1
            n = 0
            while True:
                i = value(i, path + (n,))
                n += 1
                i = skip(i)
                if text[i] == ",":
                    i += 1
                    continue
                assert text[i] == "]", f"']' expected at {i}"
                return i + 1
        if c == '"':
            string, end = scanstring(text, i + 1)
            out.append((path, i, end, string))
            return end
        match = literal.match(text, i)
        assert match, f"a value expected at {i}"
        return match.end()

    value(0, ())
    return out


def _line(text, start):
    first = text.rfind("\n", 0, start) + 1
    last = text.find("\n", start)
    return text.count("\n", 0, start) + 1, text[first:last if last >= 0 else len(text)].rstrip("\r")


def _decode(raw, path):
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RenumberError(f"{path}: is not UTF-8 text ({exc}) -- nothing was written", "unreadable", file=str(path)) from None


# --- the preview ----------------------------------------------------------------------------

def preview(here, deleted, keep_values=False, today=None):
    """What deleting `deleted` would do -- nothing read is written. `keep_values` keeps each deleted position's values under `<id>-old` and rewrites what cites it to that name («Copier les valeurs»). Raises RenumberError for an id the project does not have."""
    here = here or project.current()
    rows = positions_store.read(here)
    ids = [row["position"] for row in rows]
    deleted = list(dict.fromkeys(deleted))
    for pid in deleted:
        if pid not in ids:
            raise RenumberError(f"there is no position '{pid}'", "unknown-position", position=pid)
    mapping = cascade(ids, deleted)
    archived = {}
    if keep_values:
        taken = set(ids) | {row["position"] for row in read_archive(here)}
        for pid in deleted:
            archived[pid] = archived_name(pid, taken)
            taken.add(archived[pid])
    return _scan(here, rows, deleted, mapping, archived, keep_values, today)


def rename_preview(here, old, new):
    """Renaming one position, `old` → `new`, as a renumbering of one entry: every citation of it rewritten in the same files, by the same rule."""
    here = here or project.current()
    rows = positions_store.read(here)
    ids = [row["position"] for row in rows]
    if old not in ids:
        raise RenumberError(f"there is no position '{old}'", "unknown-position", position=old)
    if new in ids:
        raise RenumberError(f"there is a position '{new}' already", "duplicate-id", position=new)
    return _scan(here, rows, [], {old: new}, {}, False, None)


def _scan(here, rows, deleted, mapping, archived, keep_values, today):
    result = Preview(deleted=deleted, mapping=dict(mapping), keep_values=keep_values, archived=dict(archived))
    replace = {**mapping, **archived}
    result.cited = {pid: [] for pid in deleted}
    result.drawn = {pid: [] for pid in deleted}
    names = sorted(set(replace) | set(deleted), key=len, reverse=True)
    pattern = re.compile(BEFORE + "(?:" + "|".join(re.escape(name) for name in names) + ")" + AFTER) if names else None
    for file, rule in json_stores(here):
        raw = file.read_bytes()
        text = _decode(raw, file)
        try:
            doc = json.loads(text)
            strings = _json_strings(text)
        except (ValueError, AssertionError, IndexError) as exc:
            raise RenumberError(f"{file}: cannot be read as JSON ({exc}) -- nothing was written", "unreadable", file=str(file)) from None
        is_plan = Path(file).parent == Path(here.plans_dir)
        for path, start, end, value in strings:
            if not rule(doc, path):
                continue
            line, shown = _line(text, start)
            if value in deleted:
                if is_plan:
                    if file not in result.drawn[value]:
                        result.drawn[value].append(file)
                    continue
                occurrence = Occurrence(Path(file), start, end, line, shown, value, archived.get(value, ""), "json")
                result.cited[value].append(occurrence)
                if value in archived:
                    result.occurrences.append(occurrence)
                    result.files[Path(file)] = raw
            elif value in replace:
                result.occurrences.append(Occurrence(Path(file), start, end, line, shown, value, replace[value], "json"))
                result.files[Path(file)] = raw
    for file in typst_files(here) if pattern else []:
        raw = file.read_bytes()
        text = _decode(raw, file)
        for match in pattern.finditer(text):
            old = match.group(0)
            line, shown = _line(text, match.start())
            if old in deleted:
                occurrence = Occurrence(Path(file), match.start(), match.end(), line, shown, old, archived.get(old, ""), "typ")
                result.cited[old].append(occurrence)
                if old in archived:
                    result.occurrences.append(occurrence)
                    result.files[Path(file)] = raw
            else:
                result.occurrences.append(Occurrence(Path(file), match.start(), match.end(), line, shown, old, replace[old], "typ"))
                result.files[Path(file)] = raw
    new_rows = []
    for row in rows:
        if row["position"] in deleted:
            continue
        new_rows.append({**row, "position": mapping.get(row["position"], row["position"])})
    result.rows = new_rows
    result.today = today or datetime.date.today().isoformat()
    result.old_rows = rows
    return result


# --- writing it -----------------------------------------------------------------------------

def _rewritten(raw, occurrences, kind):
    text = raw.decode("utf-8")
    out, at = [], 0
    for occurrence in sorted(occurrences, key=lambda o: o.start):
        out.append(text[at:occurrence.start])
        out.append(f'"{occurrence.new}"' if kind == "json" else occurrence.new)
        at = occurrence.end
    out.append(text[at:])
    return "".join(out).encode("utf-8")


def read_archive(here):
    """The positions deleted with their values kept, [] where there are none. A file that cannot be read stops, naming it."""
    file = Path(here.sources_dir) / ARCHIVE_FILE
    if not file.is_file():
        return []
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
        validation.validate_structure(data, "positions-archive")
    except (OSError, ValueError) as exc:
        raise RenumberError(f"{file}: cannot be read ({exc})", "unreadable", file=str(file)) from None
    return data["positions"]


def _archive_bytes(entries):
    data = {"schema_version": ARCHIVE_VERSION, "format": ARCHIVE_FORMAT, "positions": entries}
    validation.validate_structure(data, "positions-archive")
    return engine.source_bytes(data)


def apply(here, result, unchecked=()):
    """Writes the renumbering `result` (a Preview) -- every file or none -- after keeping a copy of each file it changes in the archives. `unchecked` are the keys of occurrences the engineer unticked, left as they are. Refuses a preview that is `refused`, and one a file has changed under since (`changed_meanwhile`). Returns the folder the copy was kept in."""
    here = here or project.current()
    if result.refused:
        raise RenumberError(result.refused, "refused")
    skip = set(unchecked)
    writes = []
    by_file = {}
    for occurrence in result.occurrences:
        if occurrence.key not in skip:
            by_file.setdefault(occurrence.path, []).append(occurrence)
    for path, occurrences in by_file.items():
        raw = result.files[path]
        writes.append((path, _rewritten(raw, occurrences, occurrences[0].kind), raw))
    store = positions_store.path(here)
    old_store = store.read_bytes() if store.is_file() else None
    if result.archived:
        archive = Path(here.sources_dir) / ARCHIVE_FILE
        before = archive.read_bytes() if archive.is_file() else None
        entries = list(read_archive(here))
        for row in result.old_rows:
            if row["position"] in result.archived:
                kept = {key: value for key, value in positions_store.compact(row).items() if key != "position"}
                entries.append({"position": result.archived[row["position"]], "was": row["position"], "deleted": result.today, **kept})
        writes.append((archive, _archive_bytes(entries), before))
    # positions.json last: until it is written, the old ids are still the project's
    writes.append((store, positions_store.encode([positions_store.check_row(row) for row in result.rows]), old_store))
    backup = _backup(here, writes)
    sharing.commit(writes)
    _intent(backup, done=True)
    positions_store.write_workbook(here)   # the workbook beside positions.json, never read, follows it (issue #64, D-24)
    return backup


def _backup(here, writes):
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    folder = Path(here.archives_dir) / f"{stamp}-{BACKUP_PREFIX}"
    n = 1
    while folder.exists():
        n += 1
        folder = Path(here.archives_dir) / f"{stamp}-{BACKUP_PREFIX}-{n}"
    folder.mkdir(parents=True)
    files, created = [], []
    for path, _new, old in writes:
        rel = Path(path).resolve().relative_to(Path(here.root).resolve()).as_posix()
        if old is None:
            created.append(rel)
            continue
        target = folder / "files" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(old)
        files.append(rel)
    _intent(folder, files=files, created=created, done=False)
    return folder


def _intent(folder, files=None, created=None, done=False):
    note = Path(folder) / INTENT_FILE
    data = json.loads(note.read_text(encoding="utf-8")) if note.is_file() else {}
    if files is not None:
        data["files"] = files
    if created is not None:
        data["created"] = created
    data["done"] = done
    engine.write_json(note, data)


def unfinished(here):
    """The copies of renumberings that were begun and not finished -- Woodcore stopped in the middle --, for the window to offer to put back."""
    folder = Path((here or project.current()).archives_dir)
    if not folder.is_dir():
        return []
    found = []
    for candidate in sorted(folder.glob(f"*-{BACKUP_PREFIX}*")):
        note = candidate / INTENT_FILE
        try:
            if note.is_file() and not json.loads(note.read_text(encoding="utf-8")).get("done"):
                found.append(candidate)
        except ValueError:
            found.append(candidate)
    return found


def restore(here, folder):
    """Puts back every file a renumbering changed, from its copy in the archives, and takes away the files it made new: the project as it was before."""
    here = here or project.current()
    data = json.loads((Path(folder) / INTENT_FILE).read_text(encoding="utf-8"))
    root = Path(here.root)
    for rel in data.get("files", []):
        sharing.put(root / rel, (Path(folder) / "files" / rel).read_bytes())
    for rel in data.get("created", []):
        target = root / rel
        if target.is_file():
            target.unlink()
    _intent(folder, done=True)
