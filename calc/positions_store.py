"""The project's positions, in a file of Woodcore's own: `Woodcore-Datei/positions.json` (docs/domain/positions.md §7, v0.114).

Until v0.114 the positions were the rows of the engineer's `Positionen.xlsx`, sheet «Positions Element», which the export read and, from v0.94, Woodcore's «Positions» tab wrote through calc/positions_workbook.py. The engineer asked for Woodcore to be the one place a position is entered (06.10.2026): the workbook is no longer read. Its rows are imported **once**, at the first opening or the first export (`migrate`), into this file, and the workbook is then **moved** into the project's archives, never deleted; the Positions tab keeps an «Importer depuis Excel…» for an old workbook found later (`import_workbook`).

**The file.** `{"schema_version": "1.0", "format": "woodcore-positions", "positions": [ … ]}`, the list in the order the positions are listed and exported -- the order the sheet had -- each row a dictionary of `KEYS`. Only `position` and `type` are required; every other key may be absent, which reads as blank (`""`, and `None` for the moisture class). Written whole, LF, two spaces of indent, beside itself and moved into place (`os.replace`), so NextCloud never syncs half a file and a failed write leaves the old one as it was.

**Nothing but the id and the type stops anything.** A row is refused here only for what makes it no position at all: no id, an id that cannot name a file, an id another row holds (ignoring case, as Windows does -- the id is the name of `data/positions/<id>.json`), and no type. A moisture class that is not one of SIA 265 Tabelle 3's is refused too, the window offering nothing else; a section that does not read is **not** refused -- the export warns about it and writes the position with `section: null` (export_all.py).

Every refusal is a PositionsError -- a ValidationError, so the command line prints it as one -- whose `args[0]` is an English sentence and whose `code` and `detail` are what the window writes its own sentence from, `positions_workbook.WorkbookError`'s arrangement. Qt-free.
"""

import json
import os
import re
import time
from pathlib import Path

import engine
import project
import validation

FILE = "positions.json"
FORMAT = "woodcore-positions"
SCHEMA_VERSION = "1.0"

# The fields of a position, in the order a row is written -- what the export carries into data/positions/<id>.json beside the section it reads.
KEYS = ("position", "type", "material", "strength_class", "section_type", "dimension", "units", "moisture_class", "description")

# An id: letters, digits and _ . + -, starting with a letter or a digit -- the name of a file on every system, positions_workbook's own rule.
ID_PATTERN = re.compile(r"^[^\W_][\w.+-]*$")

# The workbook a project carried until v0.114, at the top of its folder, and the sheet its positions were on (`Positions` until v0.33).
WORKBOOK = "Positionen.xlsx"
SHEET = "Positions Element"
OLD_SHEET = "Positions"

# A column of that sheet, by its header, and the key of a row it fills. The moisture class under its older header too.
COLUMNS = {
    "position": "position", "type": "type", "material": "material", "resistance class": "strength_class",
    "section type": "section_type", "dimension": "dimension", "units": "units",
    "moisture class": "moisture_class", "Wood moisture class": "moisture_class", "description": "description",
}

# The materials the Positions tab offers before the project names any: what a timber office writes most -- the engineer's own lists were the workbook's `data_type` sheet, which no longer exists.
MATERIALS = ("Fichte", "Lärche", "Buche", "Eiche", "Brettschichtholz", "Brettsperrholz", "Stahl", "Beton")


class PositionsError(validation.ValidationError):
    """A change positions.json refuses: `args[0]` a sentence that stands on its own in English, for a caller with no window and for a test; `code` and `detail` what Woodcore's window turns into its own three languages."""

    def __init__(self, message, code, **detail):
        super().__init__(message)
        self.code = code
        self.detail = detail


# --- where -------------------------------------------------------------------------------

def path(here=None):
    """The project's positions.json: in its `sources` folder, beside what Woodcore draws (`Woodcore-Datei/positions.json`)."""
    return (here or project.current()).sources_dir / FILE


def workbook(here=None):
    """Where a project made before v0.114 kept its positions: `Positionen.xlsx` at the top of its folder."""
    return (here or project.current()).root / WORKBOOK


# --- a row -------------------------------------------------------------------------------

def _text(value):
    """A value as a row holds it: a text stripped, a whole number without its «.0», nothing as ""."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def moisture(value):
    """A moisture class as a row holds it: 1, 2 or 3 as a number -- typed as one or as text, «2», «2.0» --, None where it is blank, and anything else as it was given, for the caller to refuse or to warn about."""
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if re.fullmatch(r"\d+(?:\.0+)?", text):
            return int(float(text))
        return text
    return value


def normalise(row):
    """A row with every key of KEYS: its texts stripped -- a number typed into a text field a text, «180» --, the moisture class as `moisture` reads it, what it leaves out blank. Keys a row carries beyond KEYS are dropped."""
    row = row or {}
    out = {key: _text(row.get(key)) for key in KEYS if key != "moisture_class"}
    out["moisture_class"] = moisture(row.get("moisture_class"))
    return {key: out[key] for key in KEYS}


def compact(row):
    """A row as the file writes it: its id and type always, every other key only where it holds something -- a blank key absent, which reads as blank."""
    row = normalise(row)
    return {key: value for key, value in row.items() if key in ("position", "type") or value not in ("", None)}


def check_row(row, where="positions.json"):
    """What makes a row no position: no id, an id that cannot name a file, no type, a moisture class that is not one of SIA 265 Tabelle 3's. Raises a PositionsError; returns the row normalised."""
    row = normalise(row)
    pid = row["position"]
    if not pid:
        raise PositionsError(f"{where}: a position needs an id", "no-id")
    if not ID_PATTERN.match(pid):
        raise PositionsError(f"{where}: '{pid}' cannot be a position id -- letters, digits and _ . + -, starting with a letter or a digit",
                             "bad-id", position=pid)
    if not row["type"]:
        raise PositionsError(f"{where}: {pid} needs a type", "no-type", position=pid)
    allowed = validation.moisture_classes()
    mc = row["moisture_class"]
    if mc is not None and (isinstance(mc, bool) or mc not in allowed):
        raise PositionsError(f"{where}: {pid}'s moisture class is {mc!r} -- expected {', '.join(map(str, allowed))} or nothing",
                             "moisture", position=pid, value=str(mc))
    return row


def _unique(rows, pid, skip=None):
    """Refuses `pid` where another row than `skip` holds it, ignoring case."""
    for i, other in enumerate(rows):
        if i != skip and other["position"].lower() == pid.lower():
            raise PositionsError(f"there is a position '{other['position']}' already -- an id is its file's name, and Windows does not tell {other['position']} from {pid}"
                                 if other["position"] != pid else f"there is a position '{pid}' already",
                                 "duplicate-id", position=pid, existing=other["position"])


# --- the file ----------------------------------------------------------------------------

def read(here=None):
    """The project's positions, in their order, each row normalised: every key of KEYS present, a blank one "" (None for the moisture class). [] where the project has no positions.json yet. A file that cannot be read is a PositionsError naming it -- never read as no positions, which would sweep every position's record at the next export."""
    file = path(here)
    if not file.is_file():
        return []
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PositionsError(f"{file} cannot be read ({exc})", "unreadable", file=file.name, error=str(exc)) from None
    rows = data.get("positions") if isinstance(data, dict) else None
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise PositionsError(f"{file} is not a list of positions -- expected {{\"positions\": [ … ]}}", "unreadable",
                             file=file.name, error="no list of positions")
    return [normalise(row) for row in rows]


def write(here, rows):
    """Writes `rows` whole, in their order, each checked (`check_row`) and no id twice -- nothing is written where one is refused. Atomic: beside the file, then moved into place. Returns the rows normalised."""
    here = here or project.current()
    checked = []
    for row in rows:
        row = check_row(row)
        _unique(checked, row["position"])
        checked.append(row)
    file = path(here)
    file.parent.mkdir(parents=True, exist_ok=True)
    temporary = file.with_name(file.name + ".tmp")
    temporary.write_bytes(encode(checked))
    _replace(temporary, file)
    return checked


def encode(rows):
    """The bytes positions.json holds for `rows` -- the one form the file is ever written in, by `write` and by a renumbering that writes it with the other files it changes (calc/renumbering.py, issue #9)."""
    data = {"schema_version": SCHEMA_VERSION, "format": FORMAT, "positions": [compact(row) for row in rows]}
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _replace(source, target, attempts=10):
    """os.replace, tried again a moment later where Windows refuses it -- NextCloud's client holding the file it has just seen written."""
    for attempt in range(attempts):
        try:
            os.replace(source, target)
            return
        except PermissionError:
            if attempt == attempts - 1:
                raise
            time.sleep(0.2)


def _index(rows, pid):
    for i, row in enumerate(rows):
        if row["position"] == pid:
            return i
    raise PositionsError(f"there is no position '{pid}'", "unknown-position", position=pid)


def add(here, row):
    """Appends a position. Returns it normalised."""
    rows = read(here)
    row = check_row(row)
    _unique(rows, row["position"])
    write(here, rows + [row])
    return row


def update(here, old_id, row):
    """Writes `row` over position `old_id`, in its place. A new id renames it: returns (row, renamed_from), renamed_from being `old_id` where the id changed and None where it did not -- a plan, a connector or a report naming the old id will not find it any more."""
    rows = read(here)
    at = _index(rows, old_id)
    row = check_row(row)
    _unique(rows, row["position"], skip=at)
    rows[at] = row
    write(here, rows)
    return row, (old_id if row["position"] != old_id else None)


def delete(here, pid):
    """Takes position `pid` out. Returns the row it was."""
    rows = read(here)
    at = _index(rows, pid)
    gone = rows.pop(at)
    write(here, rows)
    return gone


# --- an id, a type ------------------------------------------------------------------------

def _ids(source):
    return [_text(item.get("position") if isinstance(item, dict) else item) for item in source]


def propose_id(rows, symbol, floor=None):
    """The next free id for a position of type `symbol` -- `<symbol><floor><number>`, T001 being a Träger of floor 0, number 01 (docs/domain/positions.md §7, the STE numbering plan.py draws). `rows` are the positions or their ids. `floor` left out is the floor of the last position of that symbol, else 0; "" numbers without a floor, on three digits. The number is one more than the highest of that symbol and floor, **never a gap**: a number deleted may still be named by a plan or a report, and taking it again would give it to another element without a word. Ids compared ignoring case. positions_workbook.propose_id's rule, unchanged."""
    symbol = _text(symbol)
    if not symbol:
        raise PositionsError("an id is proposed for a symbol -- T, S, D …", "no-symbol")
    ids = [pid for pid in _ids(rows) if pid]
    same = re.compile(re.escape(symbol) + r"(.)(\d+)$", re.IGNORECASE)
    if floor is None:
        floors = [match.group(1) for match in map(same.fullmatch, ids) if match and match.group(1)]
        floor = floors[-1] if floors else "0"
    floor = _text(floor)
    prefix = symbol + floor
    numbered = re.compile(re.escape(prefix) + r"(\d+)$", re.IGNORECASE)
    numbers = [match.group(1) for match in map(numbered.fullmatch, ids) if match]
    width = max([len(n) for n in numbers] + [2 if floor else 3])
    taken = {pid.lower() for pid in ids}
    number = max((int(n) for n in numbers), default=0) + 1
    while (prefix + str(number).zfill(width)).lower() in taken:
        number += 1
    return prefix + str(number).zfill(width)


SECTION_KEYS = ("section_type", "dimension", "units")


def section_of(row):
    """A position's section as a copy of its three cells -- `section_type`, `dimension`, `units` -- what the plan's *Section* field copies from one position to another, with no link back (issue #9); None where the row states none of them."""
    cells = {key: _text((row or {}).get(key)) for key in SECTION_KEYS}
    return cells if any(cells.values()) else None


def last_section_of_type(rows, type_):
    """The section of the last position of type `type_` that states one -- the section a new element of that type is proposed (issue #9: «par défaut, la section proposée est celle du dernier objet du même type dessiné») --, None where no position of the type states one. `rows` in their order, the positions of the project first and those drawn and not yet saved after them."""
    type_ = _text(type_)
    for row in reversed(list(rows)):
        if _text(row.get("type")) == type_:
            found = section_of(row)
            if found:
                return found
    return None


def types():
    """Every type an STE symbol names (plan.TYPES), in the tools' order -- «vertikal tragende Wand» … «Abfangung Punktlast von oben» --, in German, the data's language: what the Positions tab offers."""
    from domains import plan
    names = []
    for letter in plan.TYPE_ORDER:
        for name in plan.TYPES[letter]["names"].values():
            if name not in names:
                names.append(name)
    return names


def project_language(here=None, fallback="de"):
    """The language the project's documents are written in -- the `doc-lang` of its config.typ, else the report's own language -- or `fallback` where the project states none (v0.116). What the Positions tab shows a position's type in; the report prints it in the language it is compiled in."""
    import templates
    here = here or project.current()
    try:
        document, report = templates.read_languages(here.report_typ, config=templates.config_for(here.report_typ))
    except (OSError, ValueError, AttributeError):
        return fallback
    for lang in (document, report):
        if lang in ("de", "fr", "en"):
            return lang
    return fallback


def type_label(type_, lang="de"):
    """A type as it is shown in `lang`: the glossary's word for an STE type (the stored key is German, as the data has always carried it), a type typed freely -- one the glossary does not carry -- as typed (v0.116)."""
    from i18n import strings
    type_ = _text(type_)
    return strings.term(type_, lang) if type_ else ""


def type_key(text, lang="de"):
    """The stored type of what the engineer sees or typed: an STE type's name in `lang` -- or in any language -- gives its German key; anything else is a free type and stays as typed (v0.116)."""
    text = _text(text)
    if not text:
        return ""
    folded = text.casefold()
    keys = types()
    for key in keys:
        if key.casefold() == folded:
            return key
    for other in (lang, "fr", "en"):
        for key in keys:
            if type_label(key, other).casefold() == folded:
                return key
    return text


def symbol_for(type_, rows=()):
    """The letter an id of this type starts with: the STE letter whose name it is, else the first letter of a position of that type, else ""."""
    type_ = _text(type_)
    if not type_:
        return ""
    from domains import plan
    for letter in plan.TYPE_ORDER:
        if type_ in plan.TYPES[letter]["names"].values():
            return letter
    for row in rows:
        pid = _text(row.get("position"))
        if _text(row.get("type")) == type_ and pid:
            return pid[0]
    return ""


def type_for(letter, rows=()):
    """The type a position of `letter` is: the STE name of that letter (its first, for a letter with subtypes), else the type of a position whose id starts with it, else ""."""
    from domains import plan
    letter = _text(letter)
    if letter in plan.TYPES:
        return next(iter(plan.TYPES[letter]["names"].values()))
    for row in rows:
        if _text(row.get("position")).startswith(letter) and _text(row.get("type")):
            return _text(row.get("type"))
    return ""


def create_blank(here, pid=None, type_="", floor=None):
    """A position holding its id and its type and nothing else -- what the plan tab writes where a tool has no position of its letter to give what it draws (v0.114). `pid` left out is proposed from the type's symbol and `floor` (`propose_id`). A position of that very id is given back as it is, so asking twice writes once. Returns the row."""
    here = here or project.current()
    rows = read(here)
    type_ = _text(type_)
    if not pid:
        symbol = symbol_for(type_, rows)
        pid = propose_id(rows, symbol, floor)
    for row in rows:
        if row["position"] == pid:
            return row
    return add(here, {"position": pid, "type": type_})


# --- the workbook of a project made before v0.114 ----------------------------------------

def from_sheet(sheet_rows, name=WORKBOOK):
    """The rows of a «Positions Element» sheet -- dictionaries keyed by its headers -- as positions: (rows, notes). A row with no id is left out, an id the sheet holds twice is taken once, a row with no type takes its STE letter's, a moisture class that is not 1, 2 or 3 is left blank; each said in a Note, nothing refused. A blank row is no row."""
    rows, notes, seen = [], [], set()
    for number, cells in enumerate(sheet_rows, start=2):
        row = {}
        for header, value in cells.items():
            key = COLUMNS.get(_text(header))
            # the first column of a key wins, unless it is blank and another holds something -- the moisture class under its two headers
            if key and (key not in row or (_text(row[key]) == "" and _text(value))):
                row[key] = value
        row = normalise(row)
        if not any(_text(v) for v in row.values()):
            continue
        pid = row["position"]
        if not pid or not ID_PATTERN.match(pid):
            notes.append(engine.Note("positions_import_no_id", f"{name}, row {number}: no position id that can name a file ({pid!r}) -- left out",
                                     row=number, position=pid))
            continue
        if pid.lower() in seen:
            notes.append(engine.Note("positions_import_twice", f"{name}: {pid} is there twice -- the first row is taken", position=pid))
            continue
        if not row["type"]:
            row["type"] = type_for(pid[0], rows)
            if not row["type"]:
                notes.append(engine.Note("positions_import_no_type", f"{name}: {pid} has no type and its letter names none -- left out", position=pid))
                continue
            notes.append(engine.Note("positions_import_type", f"{name}: {pid} has no type -- given «{row['type']}», its letter's", position=pid, type=row["type"]))
        mc = row["moisture_class"]
        if mc is not None and (isinstance(mc, bool) or mc not in validation.moisture_classes()):
            notes.append(engine.Note("positions_import_moisture", f"{name}: {pid}'s moisture class {mc!r} is not 1, 2 or 3 -- left blank", position=pid, value=str(mc)))
            row["moisture_class"] = None
        seen.add(pid.lower())
        rows.append(row)
    return rows, notes


def import_workbook(here=None, file=None):
    """The positions of a workbook laid out as Positionen.xlsx was -- `file`, else the project's own -- as (rows, notes), read with calc/positions_workbook.py and mapped by `from_sheet`. Writes nothing: the Positions tab merges them, `migrate` writes them. A workbook that cannot be read, or has no «Positions Element» sheet, is a PositionsError naming it."""
    import positions_workbook
    file = Path(file) if file else workbook(here)
    try:
        table = positions_workbook.read(file)
    except positions_workbook.WorkbookError as exc:
        raise PositionsError(str(exc), exc.code if exc.code != "missing" else "missing-workbook", workbook=file.name, error=str(exc)) from None
    return from_sheet(table.rows, file.name)


def merge(rows, imported, replace=False):
    """`imported` taken into `rows`: `replace`, every position the workbook holds written over the one of the same id (ignoring case) and the new ones appended; else only the positions `rows` does not have, appended. Returns (rows, added, replaced) -- the ids added and written over."""
    rows = [normalise(row) for row in rows]
    at = {row["position"].lower(): i for i, row in enumerate(rows)}
    added, replaced = [], []
    for row in imported:
        row = normalise(row)
        key = row["position"].lower()
        if key in at:
            if replace and rows[at[key]] != row:
                rows[at[key]] = row
                replaced.append(row["position"])
            continue
        at[key] = len(rows)
        rows.append(row)
        added.append(row["position"])
    return rows, added, replaced


def migrate(here=None):
    """A project made before v0.114 given its positions.json: where it has none and still carries Positionen.xlsx at the top of its folder, the workbook's positions are written into positions.json and the workbook is **moved** into the project's archives as `<yymmdd-hhmm>-Positionen.xlsx` -- never deleted. Idempotent: a project that has its positions.json, or no workbook, is left as it is and None returned. Returns the Note saying what was done, the import's own notes in its `notes`.

    A workbook that cannot be read raises its PositionsError and writes nothing, so the next opening tries again -- never read as a project with no positions. A workbook Excel holds open is read and its positions written all the same; moving it is then put off, said in the Note, and the next migration finds positions.json there and leaves it.
    """
    here = here or project.current()
    book = workbook(here)
    if path(here).exists() or not book.is_file():
        return None
    rows, notes = import_workbook(here, book)
    write(here, rows)
    archive = here.archives_dir
    stamp = time.strftime("%y%m%d-%H%M")
    target = archive / f"{stamp}-{book.name}"
    n = 2
    while target.exists():
        target = archive / f"{stamp}-{n}-{book.name}"
        n += 1
    try:
        archive.mkdir(parents=True, exist_ok=True)
        _replace(book, target, attempts=3)
    except OSError as exc:
        note = engine.Note("positions_migrated_kept", f"{len(rows)} position(s) of {book.name} imported into {here.rel(path(here))}; "
                           f"the workbook could not be moved into {here.rel(archive)} ({exc}) -- close it in Excel and move it there: it is no longer read",
                           count=len(rows), workbook=book.name, file=here.rel(path(here)), archive=here.rel(archive))
    else:
        note = engine.Note("positions_migrated", f"{len(rows)} position(s) of {book.name} imported into {here.rel(path(here))}; "
                           f"the workbook is no longer read and was moved to {here.rel(target)}",
                           count=len(rows), workbook=book.name, file=here.rel(path(here)), archive=here.rel(target))
    note.notes = notes
    return note
