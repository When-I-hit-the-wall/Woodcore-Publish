"""What a fire-protection plan is drawn with, out of `calc/norms/vkf-2016-symbole-brandschutzplan.json`: the VKF / AEAI sheets of symbols for fire-protection plans, dated 16.12.2016 (docs/architecture/layout.md §11).

Four things, and no more than the drawing uses: the fire RESISTANCES a wall may be drawn with, each with the colour the sheet gives it -- colour is the only code a plan carries for them --, the colours of the ESCAPE routes, the DOORS that carry a fire resistance (a swing door and a sliding one, EI 30 and E 30: the four the sheet gives), and the proportions of the two pictograms the drawing sets as SHAPES, the emergency exit's arrow and the sliding door's. A label is the sheet's own German and the key the glossary translates (calc/i18n/strings.json).

⚠️ The sheets carry no document number, so nothing here cites one, and they are not in the repository: the engineer keeps them beside it. The file's `_source` says which page each value was read off and how it was checked.
"""

import json
from pathlib import Path

import validation

NAME = "vkf-2016-symbole-brandschutzplan"
PATH = Path(__file__).resolve().parent / (NAME + ".json")

# The entries of the escape routes the drawing may ask for.
ESCAPE_KEYS = ("length", "exit", "width", "vertical", "horizontal", "clear")

# The two ways a door opens, and what each pictogram's shape is stated by: every value a share of the pictogram's own length.
DOOR_KINDS = ("swing", "slide")
SHAPES = {"exit": ("shaft_length", "shaft_width", "head_width"), "slide": ("head_length", "head_height", "bar")}

_cache = {}


def _fail(what):
    raise validation.ValidationError("calc/norms/%s.json: %s" % (NAME, what))


def _rgb(value, what):
    if not isinstance(value, list) or len(value) != 3 or any(isinstance(c, bool) or not isinstance(c, int) or not 0 <= c <= 255 for c in value):
        _fail("%s: rgb is %r -- expected three whole numbers from 0 to 255" % (what, value))


def _read():
    if "data" in _cache:
        return _cache["data"]
    try:
        with PATH.open(encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        _fail("not found at %s -- the symbols of a fire-protection plan live in calc/norms/" % PATH)
    except json.JSONDecodeError as exc:
        _fail("is not valid JSON: %s" % exc)
    if not data.get("edition"):
        _fail("no 'edition'")
    rows = data.get("resistances")
    if not isinstance(rows, list) or not rows:
        _fail("no 'resistances'")
    seen = set()
    for row in rows:
        key = row.get("key") if isinstance(row, dict) else None
        if not isinstance(key, str) or not key.strip():
            _fail("a resistance without a key: %r" % (row,))
        if key in seen:
            _fail("the resistance %s is listed twice" % key)
        seen.add(key)
        if not isinstance(row.get("label"), str) or not row["label"].strip():
            _fail("%s: no label" % key)
        _rgb(row.get("rgb"), key)
    escape = data.get("escape")
    if not isinstance(escape, dict) or set(escape) != set(ESCAPE_KEYS):
        _fail("'escape' must carry exactly %s" % ", ".join(ESCAPE_KEYS))
    for key, row in escape.items():
        if not isinstance(row, dict) or not isinstance(row.get("label"), str) or not row["label"].strip():
            _fail("escape.%s: no label" % key)
        _rgb(row.get("rgb"), "escape." + key)
    doors = data.get("doors")
    if not isinstance(doors, dict) or set(doors) != set(DOOR_KINDS):
        _fail("'doors' must carry exactly %s" % ", ".join(DOOR_KINDS))
    for kind, rows in doors.items():
        if not isinstance(rows, list) or not rows:
            _fail("doors.%s: no door" % kind)
        classes = set()
        for row in rows:
            cls = row.get("class") if isinstance(row, dict) else None
            if cls not in seen:
                _fail("doors.%s: class %r is no fire resistance of this file" % (kind, cls))
            if cls in classes:
                _fail("doors.%s: the class %s is listed twice" % (kind, cls))
            classes.add(cls)
            if not isinstance(row.get("label"), str) or not row["label"].strip():
                _fail("doors.%s %s: no label" % (kind, cls))
            _rgb(row.get("rgb"), "doors.%s %s" % (kind, cls))
    if [row["class"] for row in doors["swing"]] != [row["class"] for row in doors["slide"]]:
        _fail("doors: a swing door and a sliding door must come in the same classes, in the same order")
    shapes = data.get("shapes")
    if not isinstance(shapes, dict) or set(shapes) != set(SHAPES):
        _fail("'shapes' must carry exactly %s" % ", ".join(SHAPES))
    for key, names in SHAPES.items():
        if not isinstance(shapes[key], dict) or set(shapes[key]) != set(names):
            _fail("shapes.%s must carry exactly %s" % (key, ", ".join(names)))
        for name in names:
            value = shapes[key][name]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 < value < 1:
                _fail("shapes.%s.%s is %r -- a share of the pictogram's length, between 0 and 1" % (key, name, value))
    _cache["data"] = data
    return data


def edition():
    return _read()["edition"]


def resistances():
    """The fire resistances a wall may be drawn with, in the sheet's order: each {"key", "label", "rgb"}."""
    return [dict(row) for row in _read()["resistances"]]


def resistance_keys():
    return [row["key"] for row in _read()["resistances"]]


def resistance(key):
    """One resistance by its key, e.g. "EI 30". Unknown: a ValidationError listing the keys there are."""
    for row in _read()["resistances"]:
        if row["key"] == key:
            return dict(row)
    raise validation.ValidationError("fire resistance %r -- expected one of %s" % (key, ", ".join(resistance_keys())))


def escape(key):
    """One entry of the escape routes: "length", "exit", "width", "vertical", "horizontal" or "clear"."""
    if key not in ESCAPE_KEYS:
        raise validation.ValidationError("escape entry %r -- expected one of %s" % (key, ", ".join(ESCAPE_KEYS)))
    return dict(_read()["escape"][key])


def door_classes():
    """The fire resistances a door may carry, in the sheet's order: "EI 30", "E 30"."""
    return [row["class"] for row in _read()["doors"]["swing"]]


def door(kind, cls):
    """One door of the sheet: `kind` "swing" or "slide", `cls` one of door_classes(). {"class", "label", "rgb"}."""
    if kind not in DOOR_KINDS:
        raise validation.ValidationError("door kind %r -- expected one of %s" % (kind, ", ".join(DOOR_KINDS)))
    for row in _read()["doors"][kind]:
        if row["class"] == cls:
            return dict(row)
    raise validation.ValidationError("door class %r -- expected one of %s" % (cls, ", ".join(door_classes())))


def shape(key):
    """The proportions of a pictogram drawn as a shape -- "exit", the emergency exit's arrow, or "slide", the sliding door --, each a share of the pictogram's length."""
    if key not in SHAPES:
        raise validation.ValidationError("shape %r -- expected one of %s" % (key, ", ".join(SHAPES)))
    return dict(_read()["shapes"][key])


def colour(rgb):
    """An RGB triple as the "#rrggbb" a drawing writes."""
    return "#%02x%02x%02x" % tuple(rgb)


# --- The fire resistance a load-bearing structure is required to have: VKF / AEAI 15-15, 3.7.1, tables 1 to 3 (issue #46) ---
#
# `calc/norms/vkf-2015-15-15-tab01-03-tragwerk.json`, the column «Système porteur» of the three tables and the four notes that change it, as data: the rules of the notes are never written here as `if`s on a use or a table, only applied as the file states them.

REQUIREMENT_NAME = "vkf-2015-15-15-tab01-03-tragwerk"
REQUIREMENT_PATH = Path(__file__).resolve().parent / (REQUIREMENT_NAME + ".json")

# The keys of a building's data (Woodcore-Datei/building.json, schemas/fire-building.schema.json), the lists of the file each is one of, and the conditions a note may be stated for.
BUILDING_KEYS = ("height", "use", "concept", "storeys")
BUILDING_LISTS = {"height": "heights", "use": "uses", "concept": "concepts", "storeys": "storeys"}
NOTE_CONDITIONS = ("single_storey", "top_level", "two_small")
NOTE_EFFECTS = ("none", "minus_30")


def _rfail(what):
    raise validation.ValidationError("calc/norms/%s.json: %s" % (REQUIREMENT_NAME, what))


def _read_requirement():
    if "requirement" in _cache:
        return _cache["requirement"]
    try:
        with REQUIREMENT_PATH.open(encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        _rfail("not found at %s" % REQUIREMENT_PATH)
    except json.JSONDecodeError as exc:
        _rfail("is not valid JSON: %s" % exc)
    if not data.get("edition"):
        _rfail("no 'edition'")
    req = data.get("requirement")
    if not isinstance(req, dict):
        _rfail("no 'requirement' block")
    ids = {}
    for key in BUILDING_LISTS.values():
        rows = req.get(key)
        if not isinstance(rows, list) or not rows or any(not isinstance(r, dict) or not r.get("id") or not r.get("label") for r in rows):
            _rfail("'%s' must list rows with an id and a label" % key)
        ids[key] = [r["id"] for r in rows]
        if len(set(ids[key])) != len(ids[key]):
            _rfail("'%s' lists an id twice" % key)
    tables = req.get("tables")
    notes = req.get("notes")
    if not isinstance(tables, dict) or not isinstance(notes, dict):
        _rfail("no 'tables' or no 'notes'")
    for height in req["heights"]:
        table = height.get("table")
        if table not in tables:
            _rfail("height %s names table %r, which the file does not carry" % (height["id"], table))
        seen = set()
        for row in tables[table]:
            for use in row.get("uses") or []:
                if use in (req.get("exemptions") or {}):
                    _rfail("table %s: the use %s is exempted by 3.2.3 and in a table" % (table, use))
                if use not in ids["uses"]:
                    _rfail("table %s: use %r is not listed in 'uses'" % (table, use))
                if use in seen:
                    _rfail("table %s: the use %s is in two rows" % (table, use))
                seen.add(use)
            for concept in ids["concepts"]:
                cell = row.get(concept)
                if not isinstance(cell, dict) or isinstance(cell.get("R"), bool) or not isinstance(cell.get("R"), int) or cell["R"] < 0:
                    _rfail("table %s, %s: %s has no R in whole minutes" % (table, "/".join(row.get("uses") or []), concept))
                for note in cell.get("notes") or []:
                    if note not in notes:
                        _rfail("table %s refers to note [%s], which the file does not carry" % (table, note))
    for use, exemption in (req.get("exemptions") or {}).items():
        if use not in ids["uses"] or not exemption.get("norm_ref"):
            _rfail("exemption %r: a use of 'uses' with its norm_ref" % use)
    for key, note in notes.items():
        if note.get("effect") not in NOTE_EFFECTS:
            _rfail("note [%s]: effect %r -- expected one of %s" % (key, note.get("effect"), ", ".join(NOTE_EFFECTS)))
        if not note.get("when") or any(w not in NOTE_CONDITIONS for w in note["when"]):
            _rfail("note [%s]: when %r -- expected among %s" % (key, note.get("when"), ", ".join(NOTE_CONDITIONS)))
        if any(t not in tables for t in note.get("tables") or []):
            _rfail("note [%s] names a table the file does not carry" % key)
        if note["effect"] == "minus_30" and (isinstance(note.get("by"), bool) or not isinstance(note.get("by"), int) or note["by"] <= 0):
            _rfail("note [%s]: a reduction states by how many minutes, 'by'" % key)
    _cache["requirement"] = data
    return data


def requirement():
    """The block of 15-15 3.7.1 as the file states it: heights, uses, concepts, storeys, tables, notes, and the citation."""
    return _read_requirement()["requirement"]


def requirement_edition():
    return _read_requirement()["edition"]


def building_ids(key):
    """The ids one field of a building's data may take, in the file's order: `key` one of BUILDING_KEYS."""
    return [row["id"] for row in requirement()[BUILDING_LISTS[key]]]


def check_building(building, where="building.json"):
    """A building's data against the lists of the file: each of BUILDING_KEYS present and one of the file's ids. A defect stops the export naming the field (the file is Woodcore's own)."""
    if not isinstance(building, dict):
        raise validation.ValidationError("%s: expected an object" % where)
    for key in BUILDING_KEYS:
        known = building_ids(key)
        if building.get(key) not in known:
            raise validation.ValidationError("%s: %s is %r -- expected one of %s" % (where, key, building.get(key), ", ".join(known)))


def required_resistance(building, top_level=False):
    """The fire resistance 15-15 requires of a load-bearing structure, for a building's data (check_building's shape) and a member on the top storey or not.

    Returns {minutes, table, page, row, base, notes, reason, norm, norm_ref}: `minutes` 0 is «pas d'exigence»; None with a `reason` where the table gives no row for the use (table 3 lists neither agriculture nor isolated lodging); `base` the table's value before the notes; `row` its place in the table, from 1; `notes` the notes applied, in the file's order. A note's condition is the building's (`single_storey`, `two_small`) or the member's (`top_level`); a note «column_wide» holds for every row of its tables, another only where the cell or the use names it."""
    check_building(building)
    req = requirement()
    height = next(h for h in req["heights"] if h["id"] == building["height"])
    table = height["table"]
    row = next((r for r in req["tables"][table] if building["use"] in r["uses"]), None)
    out = {"minutes": None, "table": table, "page": height["page"], "row": None, "base": None, "notes": [], "reason": None,
           "norm": req["norm"], "norm_ref": req["norm_ref"], "exemption": None}
    exemption = (req.get("exemptions") or {}).get(building["use"])
    if exemption is not None:
        # 3.2.3 al. 2 c, d: a single-family house, a building of reduced size -- no requirement, whatever the table
        out.update(minutes=0, base=0, exemption=exemption["norm_ref"], norm_ref=exemption["norm_ref"], page=exemption["page"])
        return out
    if row is None:
        out["reason"] = "VKF 15-15 table %s gives no row for the use %s" % (table, building["use"])
        return out
    cell = row[building["concept"]]
    out["row"] = req["tables"][table].index(row) + 1
    out["base"] = minutes = cell["R"]
    marked = set(cell.get("notes") or []) | set((row.get("use_notes") or {}).get(building["use"]) or [])
    holds = {"single_storey": building["storeys"] == "single", "two_small": building["storeys"] == "two_small", "top_level": bool(top_level)}
    for key, note in req["notes"].items():
        if table not in note["tables"] or not (note.get("column_wide") or key in marked):
            continue
        if not any(holds[w] for w in note["when"]) or minutes == 0:
            continue
        minutes = 0 if note["effect"] == "none" else max(0, minutes - note["by"])
        out["notes"].append(key)
    out["minutes"] = minutes
    return out
