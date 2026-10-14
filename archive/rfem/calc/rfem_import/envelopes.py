"""The extreme a design situation reaches, and **the combination that produced it** — read, never enveloped here.

RFEM's table export carries, beside the 48 combinations, the four *result combinations* this model's design situations are — `SP1` ELU fondamental, `SP2` ELS rare, `SP3` ELS fréquent, `SP4` ELS quasi-permanent — and each of their tables is already the envelope, with one column more than a combination's: **«Chargement correspondant»**, naming the combination that reached the value on that row (`CO20`, `CO3`, …).

So the engineer's «l'effort maximal, et la combinaison de charge qui a calculé cet effort maximal» is a **reading**. Nothing here compares 48 combinations: RFEM did it, and doing it again would be a second opinion on a number the solver already settled (§3.3duodecies — Woodcore shows what RFEM computed). It is also 4 tables instead of 48: the forces of every combination cost 11.9 s on the engineer's own export.

**One reader for three tables, because RFEM gives them one shape.** Member internal forces, member deformations and nodal support reactions are all written the same way: a row per object, per abscissa, per **criterion** — and the criterion *names the column the row is extreme in*. So nothing here holds a list of what a force table or a deformation table contains; it reads the criterion and takes the value of the column of that name.

⚠️ **A sheet holds more than one block, and they are not the same width.** Measured on the engineer's own export: `SP1 | Barres | Efforts internes` writes 1812 rows with a leading *section* column, then a «Total» and a «max/min» trailer, and then **770 more rows without it** — every cell one to the left. Every `CO` sheet does the same, 84 rows one way and 578 the other. A reader that trusts the header's column indices reads the second block with every value in the wrong field, in silence. So the criterion is found **in the row** (`results.criterion_at`) and the whole row is read at the offset that puts it where the header says it should be. A table with one block gives an offset of zero throughout, which is every CSV RFEM writes.

⚠️ **A deformation table carries two kinds of row and only one of them is an envelope.** RFEM writes `max` and `min` rows, which are the **column-wise** extremes — each column's own largest and smallest, from different combinations — and therefore name no loading at all; then a row per quantity (`|u|`, `ux`, …) which is one combination's, and names it. Only the second kind is read: a row that cannot say which combination produced it is a row a report cannot cite.

⚠️ **The extreme of a member is the extreme over its stations**, taken across every row of that criterion rather than from the order the rows come in. RFEM writes the pair max-then-min, and reading it by position would be right today and silent the day it is not.

⚠️ **The concomitant values are kept.** The row carrying the largest M_y also carries the N and the V *that act at the same moment under the same combination*, which is what a verification needs — a bending-and-normal-force check reads the normal force concomitant to the moment, not the largest of each. What is not kept is any attempt to combine them.

⚠️ **Units are read from the headers and converted**, never assumed, and the family is read from the unit itself rather than from the quantity's name — which is what lets one reader take kN, kNm, mm and mrad out of three tables that share no column.
"""

import os
import re

import engine
from rfem_import.csv_tables import RfemCsvError, fold, read_table, read_workbook
from rfem_import.results import criterion_at

# The column that makes a table an envelope: it names the loading each row's extreme came from. Its absence is
# what tells a result combination's table from an ordinary combination's, in any language.
LOADING_ALIASES = (
    "Chargement correspondant", "Zugehörige Belastung", "Zugehoerige Belastung",
    "Corresponding loading", "Corresponding Loading", "Zugehörige Einwirkung",
)

# What identifies the object a row is about.
MEMBER_ALIASES = ("Barre n°", "Stab Nr.", "Member No.", "Stab-Nr.", "barre_no", "member_no", "stab_nr")
NODE_ALIASES = ("Nœud n°", "Knoten Nr.", "Node No.", "noeud_no", "node_no", "knoten_nr")
LOCATION_ALIASES = ("x", "Stelle x", "Location x", "Position x")

# The criteria that name no column: RFEM's own column-wise envelope, which names no loading and is skipped.
COLUMNLESS = frozenset({"max", "min", "maximum", "minimum"})

# The unit families this reader converts, each to the unit it hands on. Chosen by the **unit** a header
# declares and not by the quantity's name, which is what lets one reader take a force table, a deformation
# table and a reaction table without holding a list of what each contains.
FAMILIES = (
    ("kN", {"n": 0.001, "kn": 1.0, "mn": 1000.0}),
    ("kNm", {"nm": 1e-3, "nmm": 1e-6, "knm": 1.0, "kncm": 0.01, "mnm": 1000.0}),
    ("mm", {"mm": 1.0, "cm": 10.0, "dm": 100.0, "m": 1000.0}),
    ("mrad", {"mrad": 1.0, "rad": 1000.0}),
)

# A design situation's own id, as RFEM writes it first in a sheet's name: «SP1 | Barres | Efforts internes».
# The letters are its localised abbreviation and are carried opaquely, like a loading's (`results.py`).
_SITUATION = re.compile(r"^([A-Za-z]{1,4})(\d+)\s*[_\-|]")

# How a member-deformation sheet says which axis system it is written in. A beam's deflection is read across
# its **own** axis, so the local table is the one taken where both are exported.
LOCAL_WORDS = ("local", "lokal", "loc")
GLOBAL_WORDS = ("global", "glob", "glo")


class Extreme:
    """One extreme of one quantity on one object: its value, where it is, and the loading that produced it."""

    __slots__ = ("object", "quantity", "kind", "value", "unit", "loading", "x", "concomitant")

    def __init__(self, object, quantity, kind, value, unit, loading, x, concomitant):
        self.object, self.quantity, self.kind = object, quantity, kind
        self.value, self.unit, self.loading = value, unit, loading
        self.x, self.concomitant = x, concomitant

    def __repr__(self):
        return (f"Extreme({self.object}, {self.quantity}.{self.kind}="
                f"{self.value} {self.unit}, {self.loading})")


class Envelope:
    """Every extreme one design situation's table holds, by object and quantity.

    `on` is `"member"` or `"node"`; `extremes` is `{(object, quantity): {"max": Extreme, "min": Extreme}}`.
    """

    __slots__ = ("path", "name", "situation", "on", "extremes", "quantities", "units", "read", "skipped", "problems")

    def __init__(self, path, name, situation, on, extremes, quantities, units, read, skipped, problems):
        self.path, self.name, self.situation, self.on = path, name, situation, on
        self.extremes, self.quantities, self.units = extremes, quantities, units
        self.read, self.skipped, self.problems = read, skipped, problems

    def of(self, object, quantity):
        """`{"max": Extreme, "min": Extreme}` for one object and quantity, or `{}`."""
        return self.extremes.get((object, quantity), {})

    def objects(self):
        """Every object this envelope carries an extreme for, in increasing number."""
        return sorted({object for object, _quantity in self.extremes})

    def __repr__(self):
        return (f"Envelope({self.situation!r}, on={self.on}, "
                f"{len(self.objects())} objects, {len(self.quantities)} quantities)")


def situation_of(name):
    """`("SP1", "SP", 1)` from «SP1 | Barres | …», or `(name, "", None)` from a name RFEM did not prefix."""
    stem = re.sub(r"\.csv$", "", os.path.basename(str(name)), flags=re.I)
    match = _SITUATION.match(stem)
    if match:
        return f"{match.group(1)}{match.group(2)}", match.group(1), int(match.group(2))
    return stem, "", None


def factor_of(unit):
    """`(canonical unit, factor)` for a unit a header declares, or `(unit, None)` where no family holds it."""
    if unit is None:
        return None, None
    key = fold(unit).replace("_", "")
    for canonical, family in FAMILIES:
        if key in family:
            return canonical, family[key]
    return unit, None


def is_envelope(table):
    """True where the table names, per row, the loading that row's extreme came from.

    That column is what a *result combination*'s table has and a combination's has not, so it is the one
    language-independent way to tell an envelope from a distribution.
    """
    return table is not None and table.column(*LOADING_ALIASES) is not None


def quantities_of(table, skip):
    """The columns a criterion may name: every column with a unit this reader converts, bar the identifying ones."""
    out = {}
    for column in table.columns:
        if column.index in skip or not column.name:
            continue
        canonical, factor = factor_of(column.unit)
        if factor is not None:
            out[column.name] = (column, canonical, factor)
    return out


def _at(row, column, offset):
    """The number in `column`, read at the offset this row's own block is written at."""
    index = column.index + offset
    if index < 0 or index >= len(row.cells):
        return None
    from rfem_import.csv_tables import number
    return number(row.cells[index])


def _text(row, column, offset):
    index = column.index + offset
    return row.cells[index].strip() if 0 <= index < len(row.cells) else ""


def envelope_of(table, path=None, situation=None):
    """The extremes one already-read envelope table holds, or None where it is not one."""
    if not is_envelope(table):
        return None
    path = table.path if path is None else path
    problems = []

    loading_column = table.column(*LOADING_ALIASES)
    member_column = table.column(*MEMBER_ALIASES)
    node_column = table.column(*NODE_ALIASES)
    location = table.column(*LOCATION_ALIASES)
    # ⚠️ A member table carries a node column too -- the node at each station -- so the member decides.
    on = "member" if member_column is not None else "node"
    object_column = member_column if on == "member" else node_column
    if object_column is None:
        problems.append(engine.Note(
            "rfem_envelope_no_object",
            f"{os.path.basename(str(path))}: this envelope names neither a member nor a node -- it is not read",
            where=os.path.basename(str(path)),
        ))
        return None

    skip = {c.index for c in (loading_column, member_column, node_column, location) if c is not None}
    quantities = quantities_of(table, skip)
    if not quantities:
        problems.append(engine.Note(
            "rfem_envelope_no_quantity",
            f"{os.path.basename(str(path))}: no column of this envelope carries a unit this reader converts",
            where=os.path.basename(str(path)),
        ))
        return None
    by_key = {fold(name): value for name, value in quantities.items()}
    # ⚠️ The criterion column carries no header of its own; it is the one immediately before the first
    # quantity, which is where RFEM has put it in every table of one export. It is a **reference** and not a
    # place to read: each row says where its own block put it (`criterion_at`).
    reference = min(column.index for column, _unit, _factor in quantities.values()) - 1

    extremes, read, skipped = {}, 0, 0
    for row in table.rows:
        found = criterion_at(row, by_key)
        if found is None:
            skipped += 1
            continue
        offset = found - reference
        key = fold(row.cells[found].strip())
        column, unit, factor = by_key[key]
        value = _at(row, column, offset)
        object = _at(row, object_column, offset)
        loading = _text(row, loading_column, offset)
        if value is None or object is None or not loading:
            # A row that cannot say which object it is about, or which combination produced it, is a row a
            # report cannot cite -- RFEM's own column-wise «max»/«min» rows among them.
            skipped += 1
            continue
        value *= factor
        concomitant = {}
        for other, (other_column, other_unit, other_factor) in quantities.items():
            got = _at(row, other_column, offset)
            if got is not None:
                concomitant[other] = (got * other_factor, other_unit)
        x = _at(row, location, offset) if location is not None else None
        read += 1
        slot = extremes.setdefault((int(object), column.name), {})
        for kind, better in (("max", lambda a, b: a > b), ("min", lambda a, b: a < b)):
            held = slot.get(kind)
            if held is None or better(value, held.value):
                slot[kind] = Extreme(int(object), column.name, kind, value, unit, loading, x, concomitant)

    name = getattr(table, "name", "") or os.path.basename(str(path))
    if situation is None:
        situation = situation_of(name)[0]
    units = {name: unit for name, (_column, unit, _factor) in quantities.items()}
    return Envelope(str(path), name, situation, on, extremes,
                    sorted(quantities), units, read, skipped, problems)


def read_envelope(path, name=None):
    """The envelope one exported CSV holds, or None where it is not one."""
    try:
        table = read_table(path, name=name)
    except RfemCsvError:
        return None
    return envelope_of(table, path=path)


def kind_of(table, name):
    """Which of the three envelopes a table is: `"forces"`, `"deformations"`, `"deformations-global"` or `"reactions"`.

    Decided by what the table identifies its rows with and by the units of its **quantity** columns -- never by
    the sheet's own words, which are localised. The one thing no column can say is which axis system a member
    deformation is written in, and that is the one thing read off the name.
    """
    member = table.column(*MEMBER_ALIASES)
    if member is None:
        return "reactions"
    skip = {c.index for c in (table.column(*LOADING_ALIASES), member,
                              table.column(*NODE_ALIASES), table.column(*LOCATION_ALIASES)) if c is not None}
    units = {unit for _name, (_column, unit, _factor) in quantities_of(table, skip).items()}
    if units & {"mm", "mrad"}:
        folded = fold(name)
        if any(word in folded for word in GLOBAL_WORDS) and not any(word in folded for word in LOCAL_WORDS):
            return "deformations-global"
        return "deformations"
    return "forces"


def read_workbook_envelopes(path, situations=None):
    """The envelopes of each design situation in an RFEM table export in XLSX: `({situation: {kind: Envelope}}, problems)`.

    ⚠️ **`situations` is what keeps this cheap.** An export of this project is 490 sheets of which 466 are
    results, and nothing in a sheet's *name* says whether its loading is a result combination -- only reading
    it does. So the caller, which has read the model and therefore knows which design situations its
    combinations name, says which to read: four situations are a dozen sheets and a second, where every sheet
    is 466 and a minute. With `None` every sheet is tried, which is what a caller with no model can do.

    A member-deformation table exported in both axis systems is taken in the **local** one: a beam's deflection
    is measured across its own axis, and the global table answers a different question.
    """
    wanted = None if situations is None else {str(s).strip().upper() for s in situations}
    book = read_workbook(path)
    found, problems = {}, []
    try:
        for name in book.names:
            situation, letters, num = situation_of(name)
            if not letters or num is None:
                continue
            if wanted is not None and situation.upper() not in wanted:
                continue
            table = book.table(name)
            if table is None or not is_envelope(table):
                continue
            kind = kind_of(table, name)
            if kind == "deformations-global":
                continue
            envelope = envelope_of(table, path=f"{path}!{name}", situation=situation)
            if envelope is None:
                continue
            problems.extend(envelope.problems)
            found.setdefault(situation, {})[kind] = envelope
    finally:
        book.close()
    return found, problems


def read_folder_envelopes(folder, situations=None):
    """The same, from a folder of CSVs: `({situation: {kind: Envelope}}, problems)`.

    RFEM writes either one workbook or one file per table, and a reader above this cannot tell which it was
    given (`csv_tables`). A file that is not an envelope is passed over without a word -- most of a folder of
    580 is not.
    """
    import pathlib

    wanted = None if situations is None else {str(s).strip().upper() for s in situations}
    found, problems = {}, []
    for file in sorted(pathlib.Path(folder).glob("*.csv")):
        situation, letters, num = situation_of(file.name)
        if not letters or num is None:
            continue
        if wanted is not None and situation.upper() not in wanted:
            continue
        try:
            table = read_table(file)
        except (RfemCsvError, OSError, UnicodeDecodeError):
            continue
        if not is_envelope(table):
            continue
        kind = kind_of(table, file.name)
        if kind == "deformations-global":
            continue
        envelope = envelope_of(table, path=file, situation=situation)
        if envelope is None:
            continue
        problems.extend(envelope.problems)
        found.setdefault(situation, {})[kind] = envelope
    return found, problems


def read_export_envelopes(path, situations=None):
    """The envelopes of an RFEM table export, whichever form it was handed over in."""
    import pathlib

    path = pathlib.Path(path)
    if path.is_dir():
        return read_folder_envelopes(path, situations)
    return read_workbook_envelopes(path, situations)

