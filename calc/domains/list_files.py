"""The lists Woodcore writes **once** in raw Typst, each cell kept in step by `#sync`: the revision journal of a document, the list of the positions, the quantities of the position plans (spec docs/requirements/completed/2026-10-21-commandes-typst-refonte.md, REQ-017, UI-003, Q-008).

The engineer, Q-008 (21.10.2026): their rows are the data -- a revision, a position, a material and its section --, so a file Woodcore rewrote at every change would make every new row a change of structure. They are written once (`write`), a `#table` with one row a line, each cell `[#sync("<domain>/<instance>/<variable>")[the value]]` (calc/typst_sync.py): the export compares every cell with its data and warns of one that differs (ARCH-010), the engineer edits, removes or reorders the rows as he likes, and a row his file does not hold yet is proposed by «Ajouter» (`missing`, `add`), which writes it before the table's end. Nothing here rewrites a row.

The values a cell is compared with are this module's (`records`), the export's data read as the cells print them: a date as the report prints it, a measure missing as «—». Qt-free.
"""

import json
import re

import engine
import project
import validation
import typst_sync

KINDS = ("journal", "position-list", "quantities")
# the documents a journal is written for, each its own data/journal*.json (journal.EXPORT_FILES)
DOCUMENTS = ("rs", "cu", "bp")
# the columns of each list, by the variable a cell reads and the engine's word its heading is (calc/i18n/strings.json)
COLUMNS = {
    "journal": (("index", "journal.index"), ("date", "journal.date"), ("name", "journal.name"), ("initials", "journal.initials"),
                ("label", "journal.label"), ("summary", "journal.summary"), ("description", "journal.description")),
    "position-list": tuple((key, "position_list." + key) for key in ("id", "type", "material", "strength_class", "section_type", "dimension", "units", "moisture_class", "description")),
    "quantities": (("material", "quantities.material"), ("section", "quantities.section"), ("pieces", "quantities.pieces"), ("length_m", "quantities.length"), ("volume_m3", "quantities.volume")),
}
# a measure the plans do not give, as the quantities' table prints it
NONE = "—"


class ListError(ValueError):
    """A list that cannot be written or added to as asked: a file already there, a table whose end Woodcore no longer finds."""


def sync_domain(kind, document="rs"):
    """The domain of a list's `#sync` ids: `journal` for the report's journal, `journal-cu`, `journal-bp` for the two other documents', `position`, `quantities`."""
    if kind == "journal":
        return "journal" if document == "rs" else "journal-" + document
    return {"position-list": "position", "quantities": "quantities"}[kind]


def _json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _date(iso):
    parts = str(iso).split("-")
    return ".".join(reversed(parts)) if len(parts) == 3 else str(iso)


def _number(value, digits):
    if value is None:
        return NONE
    return round(float(value), digits)


def records(here, kind, document="rs"):
    """{instance: {variable: value}} of a list as the export holds it, in the order the list prints it: a revision by its number (newest first), a position by its id, a material and section by `material · section` -- its total by `material · Σ`."""
    import journal
    out = {}
    if kind == "journal":
        data = _json(here.data_dir / journal.EXPORT_FILES[document]) or {}
        for entry in data.get("entries", []):
            out[str(entry["index"])] = {"index": entry["index"], "date": _date(entry.get("date", "")), "name": entry.get("name", ""), "initials": entry.get("initials", ""),
                                        "label": entry.get("label", ""), "summary": entry.get("summary", ""), "description": entry.get("description", "")}
    elif kind == "position-list":
        index = _json(here.data_dir / "positions-index.json") or {}
        for pid in index.get("positions", []):
            r = _json(here.data_dir / "positions" / f"{pid}.json") or {}
            out[pid] = {"id": pid, **{key: r.get(key, "") for key, _word in COLUMNS[kind][1:]}}
    elif kind == "quantities":
        summary = (_json(here.data_dir / "quantities.json") or {}).get("all", {"groups": [], "totals": []})
        for total in summary.get("totals", []):
            for g in summary.get("groups", []):
                if g["material"] == total["material"]:
                    out[f"{g['material']} · {g['section']}"] = {"material": g["material"] or NONE, "section": g["section"] or NONE, "pieces": g["pieces"],
                                                               "length_m": _number(g.get("length_m"), 2), "volume_m3": _number(g.get("volume_m3"), 3)}
            out[f"{total['material']} · Σ"] = {"material": "Σ", "section": "", "pieces": total["pieces"],
                                               "length_m": _number(total.get("length_m"), 2), "volume_m3": _number(total.get("volume_m3"), 3)}
    else:
        raise ListError(f"no list {kind!r} -- {', '.join(KINDS)}")
    return out


def sync_records(here):
    """{domain: {instance: {variable: {value, unit}}}} of every list, what `typst_sync.check` compares a cell of one with."""
    out = {}
    for kind in KINDS:
        for document in (DOCUMENTS if kind == "journal" else ("rs",)):
            rows = records(here, kind, document)
            out[sync_domain(kind, document)] = {i: {v: {"value": value, "unit": ""} for v, value in row.items()} for i, row in rows.items()}
    return out


def path(here, kind, document="rs"):
    """Where a list is written: a journal beside its document's entry file (`journal.typ`), the list of the positions and the quantities beside positions.json, `Positions/position-list.typ` and `Positions/quantities.typ` in a project laid out by folders."""
    if kind == "journal":
        return here.document_dir(document) / "journal.typ"
    return here.positions_dir / f"{kind}.typ"


def journal_files(here):
    """{document: its journal's file from the Typst root} of every document whose journal is written -- what `domain-file("journal", document)` reads in data/domain-files.json, so that a journal section includes it with no path written by hand, its own folder named differently in each language (ARCH-008)."""
    out = {}
    for mode in (project.MODES if here.has_modes else ("rs",)):
        target = path(here, "journal", mode)
        if target.is_file():
            out[mode] = here.from_root(target)
    return out


def list_journals(here):
    """data/domain-files.json naming each document's journal where it lies now (`journal_files`): what seeding a project and moving its documents (a migration) write, an export writing the whole file again. True where it changed."""
    from domains import unfold
    listing = here.data_dir / unfold.FILES_FILE
    files = engine.previous_json(listing) or unfold.empty_files()
    journals = journal_files(here)
    if files["files"].get("journal", {}) == journals:
        return False
    if journals:
        files["files"]["journal"] = journals
    else:
        files["files"].pop("journal", None)
    validation.validate_structure(files, unfold.FILES_SCHEMA)
    engine.write_json(listing, files)
    return True


def label(kind, document="rs"):
    """The label the table is closed by: what «Ajouter» finds its end by."""
    return "<" + (sync_domain(kind, document) if kind == "journal" else kind) + ">"


def _cell(text):
    return re.sub(r"([\\#*_`$<>@\[\]~])", r"\\\1", str(text))


def row_line(kind, instance, row, document="rs", lang="de"):
    """One row of a list, on one line: each cell `[#sync(id)[value]]`, a word in the document's language where the glossary carries it (`typst_sync.stale` reads it as the export's), a total bold."""
    from i18n import strings
    cells = []
    for variable, _word in COLUMNS[kind]:
        value = row[variable]
        shown = strings.translate(value, lang) if isinstance(value, str) and variable in ("type", "material") else typst_sync.written(value) if not isinstance(value, str) else value
        # in markup, a cell `[…]`, where Typst runs the `#sync` and Woodcore's lexer finds it (calc/typst_sync.py)
        cell = "#sync(" + json.dumps(typst_sync.make_id(sync_domain(kind, document), instance, variable), ensure_ascii=False) + ")[" + _cell(shown) + "]"
        cells.append("[*" + cell + "*]" if kind == "quantities" and row.get("material") == "Σ" else "[" + cell + "]")
    return "  " + ", ".join(cells) + ","


def text(here, kind, document="rs", lang="de"):
    """The whole file of a list, as Woodcore writes it once: the engine imported from the root, the table with its caption, its header in the document's language, one row a line, closed by its label."""
    import documents
    from i18n import strings
    title = {"journal": None, "position-list": "position_list.title", "quantities": "quantities.title"}[kind]
    header = ", ".join("[*" + _cell(strings.text(word, lang)) + "*]" for _variable, word in COLUMNS[kind])
    lines = [documents.root_import_line(here), "",
             "#figure(kind: table" + (", caption: [" + _cell(strings.text(title, lang)) + "]" if title else "") + ",",
             f"table(columns: {len(COLUMNS[kind])},",
             f"  table.header({header}),"]
    lines += [row_line(kind, i, row, document, lang) for i, row in records(here, kind, document).items()]
    lines += [")) " + label(kind, document), ""]
    return "\n".join(lines)


def write(here, kind, document="rs", lang=None):
    """Writes a list's file where it has none, and returns its path; a file already there is the engineer's and is never written over (ListError)."""
    import positions_store
    target = path(here, kind, document)
    if target.exists():
        raise ListError(f"{here.rel(target)} is there already -- it is yours; «Ajouter» writes the rows it does not hold")
    with project.using(here):
        body = text(here, kind, document, lang or positions_store.project_language(here))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8", newline="\n")
    return target


def held_instances(file_text, kind, document="rs"):
    """The instances a list's file holds a `#sync` of, in their order."""
    domain = sync_domain(kind, document)
    seen = []
    for s in typst_sync.syncs(file_text):
        parts = typst_sync.split_id(s.id)
        if parts and parts[0] == domain and parts[1] not in seen:
            seen.append(parts[1])
    return seen


def missing(here, kind, document="rs"):
    """The instances of the export the list's file holds no row of -- what «Ajouter» proposes; every one where the file is not there."""
    target = path(here, kind, document)
    rows = records(here, kind, document)
    if not target.is_file():
        return list(rows)
    held = set(held_instances(target.read_text(encoding="utf-8"), kind, document))
    return [i for i in rows if i not in held]


def add(here, kind, document="rs", instances=None, lang=None):
    """«Ajouter»: the rows of `instances` (every missing one where None) written before the table's end -- the line its label closes --, nothing else of the file touched, its line endings kept. Returns the instances added. A file whose end Woodcore no longer finds is refused, naming the label to put back."""
    import positions_store
    target = path(here, kind, document)
    if not target.is_file():
        raise ListError(f"{here.rel(target)} is not there -- write it first")
    raw = target.read_bytes().decode("utf-8")
    newline = "\r\n" if "\r\n" in raw else "\n"
    todo = [i for i in (instances if instances is not None else missing(here, kind, document)) if i in missing(here, kind, document)]
    if not todo:
        return []
    end = re.search(r"^[ \t]*\)\)?[ \t]*" + re.escape(label(kind, document)) + r"[ \t]*$", raw, re.MULTILINE)
    if end is None:
        raise ListError(f"{here.rel(target)}: the table's end, `)) {label(kind, document)}`, is not there -- put the label back after the table for «Ajouter» to find it")
    rows = records(here, kind, document)
    lang = lang or positions_store.project_language(here)
    with project.using(here):
        lines = "".join(row_line(kind, i, rows[i], document, lang) + newline for i in todo)
    target.write_bytes((raw[:end.start()] + lines + raw[end.start():]).encode("utf-8"))
    return todo
