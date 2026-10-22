"""The report's revision journal, written in Woodcore and printed by Typst (docs/domain/journal.md §3.3terdecies).

One entry per revision of the report: its number, the day, who made it and the office's short form, then what it is -- a label, a short description and a long one. The engineer asked for it in those words, and for the three levels to govern those three texts alone: level 1 the label, level 2 the label and the short description, level 3 everything an entry carries.

This module owns its source file, `Woodcore-Datei/journal.json`, which Woodcore's «Journal» tab writes and nothing else does -- the arrangement the static models, the detail schemas and the position plans already have, for the same reasons (docs/decisions.md §13). Two things are different, and both because a journal is one list rather than a set of named objects:

**One file, not one per entry.** A journal is read as a whole, in order, and nothing addresses one revision by an id -- no `show-*` call names one, no other source refers to one. So there is no folder of files, no `group` and no id to keep in step with a file name, and the whole of §3.3octies' `source_paths`/`read_source` machinery has nothing to do here.

**Written by hand, one entry per revision** (the engineer's decision 6.2). Nothing appends an entry when a drawing is saved: an afternoon in the schemas tab would leave twenty of them, and «what I changed in the report» is not «which files I touched».

**Nothing is computed.** The export is the source's entries sorted, and that is all: there is deliberately no `{vars, steps, checks}` record, so nothing addresses a journal with `show-calc` and nobody can mistake it for a traced calculation (the rule a static model and a detail schema already follow, sections 3.3octies, 3.3decies).

There is no Qt in this file, so the tab and a test script call the same functions.
"""

import datetime
import json
import re
from pathlib import Path

import engine
import validation
from domains._common import fail as _fail  # one copy of the domains' helpers (spec 2026-10-19-base-saine-nettoyage, G4)

# Of the source file (Woodcore-Datei/journal.json) and of the export (data/journal.json).
SOURCE_SCHEMA_VERSION = "1.0"
EXPORT_SCHEMA_VERSION = "1.0"


# What the export writes, beside data/calculations.json and the rest.
EXPORT_FILE = "journal.json"

# What the export writes for each document of a project laid out in three documents, one journal per document since each prints its own «Historique des versions» (the engineer's decision of 30.09.2026): the report's is EXPORT_FILE, as it has been since v0.99, and the convention d'utilisation's and the base de projet's lie beside it. The same names as the sources' (calc/project.py, JOURNAL_FILES), and the ones lib/calc-engine.typ's `journal-files` reads -- which Typst cannot ask the existence of, so a document's compile stops on a missing one, and seeding a project writes all three (export_all.seed).
EXPORT_FILES = {"rs": EXPORT_FILE, "cu": "journal-cu.json", "bp": "journal-bp.json"}

# What an entry holds, in the order the form and the list show it. The first five are required and the two descriptions are not, which the contract states once (schemas/journal-source.schema.json) and nothing here restates.
FIELDS = ("index", "date", "name", "initials", "label", "summary", "description")

# A date is typed, so its shape is checked here rather than trusted: ISO and a real day.
DATE_PATTERN = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")

# How long an office's short form may be. Not a rule of the trade -- it is a guard against a full name typed into the wrong field, which would then be printed in a column three characters wide.
INITIALS_MAX = 12


def blank():
    """An empty journal, as a project that has never been revised carries one -- and what `read` gives where there is no file at all."""
    return {"schema_version": SOURCE_SCHEMA_VERSION, "entries": []}


def parse_date(text):
    """`text` as a date, or None where it is not one: ISO, and a real day -- «2026-02-30» is not."""
    found = DATE_PATTERN.match(str(text or "").strip())
    if found is None:
        return None
    try:
        return datetime.date(int(found.group(1)), int(found.group(2)), int(found.group(3)))
    except ValueError:
        return None


def check_source(source, where):
    """The source as Woodcore writes it, checked -- everything the schema walker cannot say (docs/architecture/data-contracts.md §3.6). Raises a ValidationError naming the entry and the field."""
    if not isinstance(source, dict):
        _fail(where, "is not a JSON object")
    validation.validate_structure(source, "journal-source")
    seen = {}
    for position, entry in enumerate(source["entries"], 1):
        # Named by its own index where it has one, so a defect is found in the tab's list and not by counting rows.
        who = f"{where}, entry {entry.get('index', position)!r}"
        # every required field is there and of its declared type: the schema walker above said so, naming the entry by its position, so nothing restates it here
        index = entry["index"]
        if isinstance(index, bool) or not isinstance(index, int) or index < 1:
            _fail(who, f"index is {index!r} -- a whole number of 1 or more, as a revision block numbers one")
        if index in seen:
            # Two entries of one number would print «Rev. 3» twice and a reader could not say which the report is at.
            _fail(who, f"index {index} is the index of the entry {seen[index]!r} already -- a revision's number is its own")
        seen[index] = entry.get("label", "")
        if parse_date(entry["date"]) is None:
            _fail(who, f"date is {entry['date']!r} -- write a day as 2026-09-27 (ISO)")
        for field in ("name", "initials", "label"):
            if not isinstance(entry[field], str) or not entry[field].strip():
                _fail(who, f"{field} must not be empty")
        if len(entry["initials"].strip()) > INITIALS_MAX:
            _fail(who, f"initials are {entry['initials']!r} -- at most {INITIALS_MAX} characters, an office's short form and not its name")
        for field in ("summary", "description"):
            if field in entry and not isinstance(entry[field], str):
                _fail(who, f"{field} is {entry[field]!r} -- text, or left out")
    return source


def read(path):
    """The journal of a project, checked -- `blank()` where there is no file, which is a project that has never been revised (never an error: a project without a journal exports without one)."""
    path = Path(path)
    if not path.is_file():
        return blank()
    try:
        source = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _fail(path.name, f"could not be read -- {exc}")
    return check_source(source, path.name)


def write_source(path, source):
    """The journal written back, checked first -- the one writer of Woodcore-Datei/journal.json."""
    check_source(source, Path(path).name)
    engine.write_json(path, source)
    return Path(path)


def next_index(source):
    """The number Woodcore proposes for a new entry: the largest plus one -- so a **gap is never refilled**, which is `positions_workbook.propose_id`'s own rule for a position's id and a revision block's on paper. Rev. 2 deleted out of 1, 2, 3 leaves 2 unused and the next revision is 4; the newest deleted gives its number back, which is right for one typed by mistake and taken out at once."""
    numbers = [e["index"] for e in source.get("entries", ()) if isinstance(e.get("index"), int) and not isinstance(e.get("index"), bool)]
    return max(numbers, default=0) + 1


def entries(source):
    """The entries **newest first**, which is the order the report prints them in (the engineer's decision 6.7).

    Ordered by the **index** and never by the date: the date is typed, so it may be wrong or two entries may share one, and a journal that reordered itself around a typo would print a revision under the wrong one. The index is unique by construction (`check_source`) and is what a revision block is read by anyway. Equal is impossible; a stable fall-back on the position in the file is kept all the same, so the order never depends on the sort's own accidents.
    """
    listed = list(source.get("entries", ()))
    return sorted(listed, key=lambda e: (-e["index"], listed.index(e)))


def record(entry):
    """One entry as the export carries it: every field present, the two descriptions "" where the source leaves them out, so the display layer never has to ask what it was given."""
    return {
        "index": entry["index"],
        "date": str(entry["date"]).strip(),
        "name": str(entry["name"]).strip(),
        "initials": str(entry["initials"]).strip(),
        "label": str(entry["label"]).strip(),
        "summary": str(entry.get("summary", "")).strip(),
        "description": str(entry.get("description", "")).strip(),
    }


def latest(data):
    """The newest revision of an export, or None where the journal is empty -- what the PDF's keywords name (`project.record`'s `revision`, v0.99). The export is sorted, so it is simply its first entry."""
    listed = data.get("entries", ())
    return listed[0] if listed else None


def prepare(path):
    """The journal read, checked and built: (data, warnings). Nothing is written here, so an export that fails leaves data/ as it was."""
    source = read(path)
    data = {"schema_version": EXPORT_SCHEMA_VERSION, "entries": [record(e) for e in entries(source)]}
    validation.validate_structure(data, "journal")
    validation.validate_journal_business(data)
    return data, []


def write(data, data_dir, mode="rs"):
    """The only writer: data/journal.json -- or, for document `mode` of a project laid out in three documents, the journal of that document (EXPORT_FILES: data/journal-cu.json, data/journal-bp.json)."""
    engine.write_json(Path(data_dir) / EXPORT_FILES[mode], data)


def export(path, data_dir, mode="rs"):
    """prepare + write, and the warnings -- what Woodcore runs when an entry is saved, so the report sees it without the load workbooks being read again. `mode` is the document whose journal `path` is (`Project.journal_file_for`), the report's by default."""
    data, notes = prepare(path)
    write(data, data_dir, mode)
    return notes
