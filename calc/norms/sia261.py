"""The values of SIA 261:2020 this project reads, out of the JSON files beside this module in `calc/norms/` (docs/architecture/layout.md §11).

`calc/norms/` is the one source of every value taken from a norm for a calculation made in Python: the numbers live in the JSON, once, and the code that needs them reads them through here. A value read from a norm is neither entered in Excel nor calculated -- which is why the domains built on it declare `ENGINE = "norm"` and cite the edition named here (section 3.3). Every number was transcribed by hand from `SIA261-2020-DE.pdf`, and each file's `_source` says at which page (section 2 rule 13).

One file per table, named `<norm>-<year>-<table>-<designation>.json`:

    sia261-2020-tab08-nutzlasten.json                  Tabelle 8, the Nutzlasten per category of Nutzfläche (8.2.1) -- read by domains/live_load.py (section 3.3septies)
    sia261-2020-tab28-raumlasten-baustoffe.json        Anhang A, Tabelle 28, Mittlere Raumlasten von Baustoffen [kN/m³]
    sia261-2020-tab29-flaechenlasten-bedachungen.json  Anhang A, Tabelle 29, Mittlere Flächenlasten von Bedachungen und Verkleidungen [kN/m²]
    sia261-2020-tab30-raumlasten-lagergueter.json      Anhang A, Tabelle 30, Raumlasten und Schüttwinkel von Erdauflasten, Gleisschotter und Lagergütern [kN/m³, °]

Tabellen 28 to 30 were read off a render of pp. 77-78, the PDF's text layer interleaving the two columns of each table. ⚠️ **They are mean unit weights per kind of material, not densities per strength class**, and nothing calculates with them yet: the characteristic density ρ_k a connection is calculated with is SIA 265's, the 5 % fractile per grade (`sia265.rho_k`).

The files are hand-written -- the one place in the pipeline where a number is transcribed rather than read -- so each is checked here before anything is built from it: an id twice, a value that is neither a number nor absent, a footnote referenced but not written, a Schüttwinkel range running backwards. A norm table that contradicts itself must stop the export naming the line, exactly as a defective workbook cell does.
"""

from pathlib import Path

import validation
from norms import _loader  # how every reader of calc/norms/ opens its files (G3)

HERE = Path(__file__).resolve().parent

TAB08 = "sia261-2020-tab08-nutzlasten"
TAB28 = "sia261-2020-tab28-raumlasten-baustoffe"
TAB29 = "sia261-2020-tab29-flaechenlasten-bedachungen"
TAB30 = "sia261-2020-tab30-raumlasten-lagergueter"

EDITION = "SIA 261:2020"

# What Tabelle 8 must carry per category row. `q_k`/`Q_k` may be null -- the norm gives no value for category E (SIA 261 8.2.2) -- but the keys are required, so a forgotten value cannot pass as one the norm does not give.
CATEGORY_KEYS = ("id", "nutzflaeche", "beispiel", "q_k", "Q_k", "notes_q", "notes_Q", "notes_category")

# The key each Anhang A file's table sits under, and the value columns each of its rows carries.
ANNEX_TABLES = {
    TAB28: ("table_28", ("raumlast",)),
    TAB29: ("table_29", ("flaechenlast",)),
    TAB30: ("table_30", ("raumlast", "schuettwinkel")),
}

# The one line of Tabelle 28 that carries no value, the norm leaving it to be determined case by case.
UNVALUED = {"leichtbeton_im_einzelfall_zu_bestimmen"}

_cache = {}


_fail = _loader.fail   # calc/norms/<name>.json: <what> (G3)


def _read(name, check):
    """One file, read once and checked once."""
    if name in _cache:
        return _cache[name]
    path = HERE / (name + ".json")
    data = _loader.load(path)
    _loader.edition(name, data, EDITION)
    check(name, data)
    _cache[name] = data
    return data


# --- Tabelle 8, the Nutzlasten --------------------------------------------------

def _check_table_8(name, data):
    table = data.get("table_8")
    if not isinstance(table, dict):
        _fail(name, "no 'table_8'")
    for key in ("title", "norm", "norm_ref", "units", "categories", "notes"):
        if not table.get(key):
            _fail(name, "table_8 has no '%s'" % key)

    notes = table["notes"]
    for ref, text in notes.items():
        if not isinstance(text, str) or not text.strip():
            _fail(name, "footnote %s of table_8 is empty" % ref)

    for unit_key in ("q_k", "Q_k"):
        if not table["units"].get(unit_key):
            _fail(name, "table_8 gives no unit for %s" % unit_key)

    seen = set()
    for row in table["categories"]:
        for key in CATEGORY_KEYS:
            if key not in row:
                _fail(name, "a category row has no '%s': %s" % (key, row))
        cat = row["id"]
        if not isinstance(cat, str) or not cat.strip():
            _fail(name, "a category row has no id: %s" % row)
        if cat in seen:
            _fail(name, "category '%s' is listed twice -- one row per category" % cat)
        seen.add(cat)
        if not row["nutzflaeche"]:
            _fail(name, "category '%s' has no Art der Nutzfläche" % cat)
        for key in ("q_k", "Q_k"):
            value = row[key]
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                _fail(name, "category '%s': %s is %r -- expected a number, or null where the norm gives none" % (cat, key, value))
            if value <= 0:
                _fail(name, "category '%s': %s is %s -- a characteristic load is positive" % (cat, key, value))
        # Both values are given together or not at all: a category the norm leaves to the project (E) leaves both open, and half a row would be read as a value that is simply missing.
        if (row["q_k"] is None) != (row["Q_k"] is None):
            _fail(name, "category '%s': q_k and Q_k must both be given, or both be null (SIA 261 8.2.2)" % cat)
        for key in ("notes_q", "notes_Q", "notes_category"):
            if not isinstance(row[key], list):
                _fail(name, "category '%s': '%s' must be a list of footnote references" % (cat, key))
            for ref in row[key]:
                if ref not in notes:
                    _fail(name, "category '%s' refers to footnote %r, which table_8 does not carry (footnotes: %s)"
                          % (cat, ref, ", ".join(sorted(notes))))

    ref = table.get("project_specific_note")
    if ref is not None and ref not in notes:
        _fail(name, "project_specific_note refers to footnote %r, which table_8 does not carry" % ref)


def edition():
    """The edition every value read here belongs to, "SIA 261:2020" -- cited in the report and recorded in each var's `source` (docs/project/purpose.md §1bis). Every file must name it."""
    return _read(TAB08, _check_table_8)["edition"]


def table_8():
    """Tabelle 8 as the file states it: its title, its citation, the unit of each value, one row per category and the footnotes those rows refer to."""
    return _read(TAB08, _check_table_8)["table_8"]


def note_texts(refs):
    """The texts of the footnotes `refs` names, in the order given -- what a category's values carry as their description in the report."""
    notes = table_8()["notes"]
    return [notes[ref] for ref in refs]


# --- Anhang A, Tabellen 28 to 30 ------------------------------------------------

def _number(name, where, label, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        _fail(name, "%s: %s is %r -- expected a positive number" % (where, label, value))


def _check_annex(name, data):
    key, columns = ANNEX_TABLES[name]
    table = data.get(key)
    if not isinstance(table, dict):
        _fail(name, "no '%s' table" % key)
    for field in ("number", "title", "norm", "norm_ref", "units", "rows"):
        if field not in table:
            _fail(name, "the table carries no '%s'" % field)
    for column in columns:
        if column not in table["units"]:
            _fail(name, "no unit for '%s'" % column)
    seen = set()
    for index, line in enumerate(table["rows"], start=1):
        where = "row %d (%s)" % (index, line.get("id"))
        if not isinstance(line.get("id"), str) or not line["id"]:
            _fail(name, "%s: no id" % where)
        if line["id"] in seen:
            _fail(name, "%s: the id is listed twice" % where)
        seen.add(line["id"])
        if not isinstance(line.get("name"), str) or not line["name"]:
            _fail(name, "%s: no name" % where)
        for column in columns:
            value = line.get(column)
            if column == "schuettwinkel":
                if value is None:
                    continue
                if isinstance(value, list):
                    if len(value) != 2:
                        _fail(name, "%s: a Schüttwinkel range is two numbers, got %r" % (where, value))
                    for v in value:
                        _number(name, where, column, v)
                    if value[0] >= value[1]:
                        _fail(name, "%s: the Schüttwinkel range %r runs backwards" % (where, value))
                    continue
                _number(name, where, column, value)
            elif value is None and line["id"] in UNVALUED:
                continue
            else:
                _number(name, where, column, value)
        # issue #111 (P11): a roofing weighed with its battens says so, as its heading does -- and only there
        if "includes_battens" in line and line["includes_battens"] is not True:
            _fail(name, "%s: includes_battens is %r -- true, or absent" % (where, line["includes_battens"]))
        if bool(line.get("includes_battens")) != ("inkl. Lattung" in (line.get("group") or "")):
            _fail(name, "%s: includes_battens goes with a heading «… inkl. Lattung», and only with one" % where)


def table_28():
    """Anhang A, Tabelle 28, the mean unit weights of building materials."""
    return _read(TAB28, _check_annex)["table_28"]


def table_29():
    """Anhang A, Tabelle 29, the mean surface loads of roofings and claddings."""
    return _read(TAB29, _check_annex)["table_29"]


def table_30():
    """Anhang A, Tabelle 30, the unit weights and angles of repose of soils, ballast and stored goods."""
    return _read(TAB30, _check_annex)["table_30"]


def row(table, row_id):
    """The line `row_id` of a table (one of table_28/29/30's results); KeyError naming the ids there are where it has none."""
    for line in table["rows"]:
        if line["id"] == row_id:
            return line
    raise KeyError("Tabelle %s has no line %r -- it has %s" % (table["number"], row_id, ", ".join(l["id"] for l in table["rows"])))


def check_all():
    """Read and check every file, for a test or for an export that wants to fail early rather than at the first lookup."""
    table_8()
    table_28()
    table_29()
    table_30()
    return edition()
