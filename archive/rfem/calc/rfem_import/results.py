"""The Schnittgrössen an RFEM export carries: N, V_y, V_z, M_T, M_y, M_z along each member, per loading.

Reads the CSV tables `csv_tables.py` hands it and gives back, per loading, the stations along each member with their internal forces in **kN and kNm** whatever unit the model was set to. It needs no API key, since RFEM's own table export does not (`calc/rfem_import/` — docs/open-questions.md §14).

**A member-forces table is recognised by its content, not by its name.** The filenames are localised -- «CO1_analyse_statique_barres_efforts_internes.csv» here, something else in a German office -- so a table is one of these when it carries all six force columns. Those six are *symbols* and identical in every language, which is what makes the recognition possible at all; 173 of the engineer's 580 exported files answer to it.

**Three kinds of row are interleaved, and telling them apart is the whole difficulty.** Established on those 580 files:

- a **distribution** row: the member's number, the station `x`, and the six forces. This is the data.
- an **extremes** row: the same shape, but with a *criterion* — `N`, `V_y`, … — naming which quantity is extreme there. RFEM opens that section with a row labelled «Extrêmes» in the member column and then goes on writing the member's number, so the label does **not** mark the section: the criterion does. Every extreme repeats a value the distribution already carries, so nothing is lost by leaving them out — and `governing()` recomputes the same answer from the distribution, where it can be traced.
- a **trailer**: «Total», «max/min», whose first cell is a word. 4047 «Total» and 171 «max/min» rows over one export.

⚠️ **The criterion column is found by its content and never by its index.** It carries no header, and in the 24 column shapes of one export it sits at index 4 in 57 tables and at index 5 in 57 others; 59 tables have none at all. Worse, index 4 is the *markers* column («R», «L | M») in some shapes, so reading a fixed index would have taken markers for criteria. It is therefore the column whose non-empty values are all force symbols — 1 or 0 candidates per table, never two, over all 173.

⚠️ **Units are read from the headers and converted, never assumed.** «Unités et décimales» is a property of the model, so the same table is kN in one project and N in another; a unit the module does not know stops that table by name rather than being silently taken for kN.

⚠️ **What is deliberately not read here**: the member's comment. The result tables end in a composite column («Section (matériau) | Commentaire sur la barre») whose parts cannot be told apart, and the model's own member table carries a clean `comment` column instead (`csv_tables.py`, `metadata_parser.py`).
"""

import os
import re

import engine
from rfem_import.csv_tables import RfemCsvError, fold, number, read_table

# The six internal forces, by the symbols RFEM writes in every language -- and ⚠️ **in the two spellings its two export formats give them**: the CSV writes «V_y», «M_T», the XLSX writes «Vy», «MT». Measured on the engineer's own exports, and it is the only difference between the two for these tables. The first spelling of each is the key everything downstream uses, so nothing above here knows which format it was handed.
FORCE_ALIASES = {
    "N": ("N",),
    "V_y": ("V_y", "Vy"),
    "V_z": ("V_z", "Vz"),
    "M_T": ("M_T", "MT", "Mt"),
    "M_y": ("M_y", "My"),
    "M_z": ("M_z", "Mz"),
}
FORCES = tuple(FORCE_ALIASES)

# Which of them is a force and which a moment, for the unit conversion.
MOMENTS = frozenset({"M_T", "M_y", "M_z"})

# A loading's own id, as RFEM writes it first in a result sheet's name: CC1, CO48, SP2, and the German
# and English spellings of the same three (LF/LK/EK, CC/CO/SP, LC/LCO/DS). Letters then digits, which is
# what every language's abbreviation has in common -- so the pattern is the abbreviation's *shape*.
_LOADING_ID = re.compile(r"^[A-Z]{2,3}\d{1,3}$")

# What RFEM heads a member-forces table with, folded: «Efforts internes», «Schnittgrössen», «Internal
# Forces». Any of them in a sheet's name, beside a loading id, marks the sheet without reading it.
# ⚠️ **Stems, not whole words: Excel truncates a sheet name to 31 characters** and RFEM's own names run past it
# -- «CO10 | Barres | Efforts interne» has lost the «s» of «internes», and 39 of one export's 57 result sheets
# are cut that way. Matching the whole word found 18 of 57 (measured), which is the kind of silent shortfall
# `csv_tables.Workbook` already resolves sheet names by prefix for.
_FORCE_WORDS = ("efforts_interne", "schnittgross", "schnittgroess", "internal_force")

# What a member column may be called. Tried before the fallback below, so that a table whose first column is not the member is still read correctly.
MEMBER_ALIASES = ("Barre n°", "Stab Nr.", "Member No.", "Stab-Nr.", "barre_no", "member_no", "stab_nr")

# What a station column may be called. `x` is what RFEM writes in all three languages of this project.
LOCATION_ALIASES = ("x", "Stelle x", "Location x", "Position x")

# To kN, and to kNm. A unit is folded first (dots and spaces dropped, case kept by folding to lower), so «kN.m» and «kNm» are one key and «N/mm2» never looks like a force.
FORCE_UNITS = {"n": 0.001, "kn": 1.0, "mn": 1000.0}
# ⚠️ 1 N·m is a **thousandth** of a kN·m and 1 N·mm a millionth. Both were a further thousand too small
# until v0.99, which no export of this project could show -- the engineer's model states kNm, so the only
# factor ever used was 1.0. A model set to Nm would have had every moment read a thousand times too small.
MOMENT_UNITS = {"nm": 1e-3, "nmm": 1e-6, "knm": 1.0, "kncm": 0.01, "mnm": 1000.0}
LENGTH_UNITS = {"mm": 0.001, "cm": 0.01, "m": 1.0}

# The unit the module hands on, whatever the model was set to.
FORCE_UNIT = "kN"
MOMENT_UNIT = "kNm"
LENGTH_UNIT = "m"

# «CO1_…» in a file's name, «CO1 | Barres | Efforts internes» in a workbook's sheet: RFEM names both after the loading, and what follows the number is an underscore, a hyphen, a space or a pipe depending on which it is. The letters are its own localised abbreviation (CC is «cas de charge» in this French installation, LF in a German one), so they are carried as an opaque label rather than interpreted.
_LOADING = re.compile(r"^([A-Za-z]{1,4})(\d+)\s*[_\-|]")


def _unit_key(unit):
    return fold(unit).replace("_", "")


def _factor(unit, table, key, path, problems):
    """The factor that takes `unit` to kN, kNm or m, or None with a `Note` naming the table and the unit."""
    wanted = MOMENT_UNITS if key in MOMENTS else FORCE_UNITS if key in FORCES else LENGTH_UNITS
    if unit is None:
        # A column with no unit in its header: the table declares none, so the value is taken as already canonical and said so.
        problems.append(engine.Note(
            "rfem_results_no_unit",
            f"{os.path.basename(path)}: «{key}» carries no unit in its header -- read as {FORCE_UNIT if key in FORCES else LENGTH_UNIT}",
            where=os.path.basename(path), key=key,
        ))
        return 1.0
    factor = wanted.get(_unit_key(unit))
    if factor is None:
        problems.append(engine.Note(
            "rfem_results_unit",
            f"{os.path.basename(path)}: «{key}» is given in «{unit}», which is not a unit this reader knows -- it knows {', '.join(sorted(wanted))}",
            where=os.path.basename(path), key=key, unit=unit,
        ))
    return factor


class Station:
    """One point along one member, with the six internal forces there.

    `x` is in metres from the member's start; the forces are in kN and the moments in kNm. `node` is the node number RFEM writes at a member's ends and leaves empty between them.
    """

    __slots__ = ("member", "x", "forces", "node", "markers")

    def __init__(self, member, x, forces, node=None, markers=""):
        self.member, self.x, self.forces, self.node, self.markers = member, x, forces, node, markers

    def __getitem__(self, key):
        return self.forces[key]

    def get(self, key, default=None):
        return self.forces.get(key, default)

    @property
    def n(self):
        return self.forces.get("N")

    def __repr__(self):
        return f"Station(member={self.member}, x={self.x}, N={self.forces.get('N')})"


class ForceTable:
    """One member-forces table of one loading: its stations, and what it left out.

    `extremes`, `summaries` and `trailers` are counted rather than kept, so that nothing is dropped in silence: `len(stations) + extremes + summaries + trailers` is every row the table held, and an import can say «447 stations read, 694 extreme rows, 62 member summaries and 65 trailers left out» -- a line from which a reader knows the file was understood rather than partly skipped.
    """

    __slots__ = ("path", "name", "loading", "kind", "number", "stations", "extremes", "summaries", "trailers", "units", "problems")

    def __init__(self, path, name, loading, kind, num, stations, extremes, summaries, trailers, units, problems):
        self.path, self.name = path, name
        self.loading, self.kind, self.number = loading, kind, num
        self.stations, self.extremes, self.summaries, self.trailers = stations, extremes, summaries, trailers
        self.units, self.problems = units, problems

    @property
    def rows_accounted(self):
        """Every row the table held, as this reader classified it -- what a test compares with the file's own row count."""
        return len(self.stations) + self.extremes + self.summaries + self.trailers

    def by_member(self):
        """The stations of each member, in order along it: `{member: [Station, …]}`."""
        members = {}
        for station in self.stations:
            members.setdefault(station.member, []).append(station)
        for stations in members.values():
            stations.sort(key=lambda s: (s.x if s.x is not None else 0.0))
        return members

    @property
    def members(self):
        return sorted(self.by_member())

    def governing(self, key, member=None):
        """The stations where `key` is largest and smallest -- `(maximum, minimum)`, each a `Station` or None.

        Computed from the distribution rather than read from RFEM's own «Extrêmes» rows, so that the value on the page can be traced to a station the report also carries.
        """
        stations = [s for s in self.stations if s.forces.get(key) is not None
                    and (member is None or s.member == member)]
        if not stations:
            return None, None
        return (max(stations, key=lambda s: s.forces[key]),
                min(stations, key=lambda s: s.forces[key]))

    def __len__(self):
        return len(self.stations)

    def __repr__(self):
        return f"ForceTable({self.loading!r}, {len(self.stations)} stations, {len(self.by_member())} members)"


def is_member_forces(table):
    """True where the table carries all six internal forces -- the one language-independent way to recognise one."""
    return all(table.column(*FORCE_ALIASES[key]) is not None for key in FORCES)


# Every spelling of the six criteria, folded -- what a row naming one of them is recognised by.
CRITERIA = frozenset(fold(spelling) for key in FORCES for spelling in FORCE_ALIASES[key])


def criterion_at(row, criteria):
    """The index of the cell naming which quantity this row is extreme in, or None.

    ⚠️ **Found in the row and not at a column's index**, because one sheet holds more than one block and
    they are not the same width. Measured on the engineer's own export: «SP1 | Barres | Efforts internes»
    writes 1812 rows with a leading *section* column, then a «Total» and a «max/min» trailer, then **770 more
    rows without it** -- every cell one to the left; and every «CO» sheet does the same, 84 rows one way and
    578 the other. Read at the header's index, the second block's criterion falls where the abscissa should
    be and its forces fall in each other's fields, in silence: before this, 84 extremes rows per combination
    were read as stations and drawn on the diagram.

    `criteria` is a set -- or a dict -- of **folded** names; matching is on the whole cell, so a comment that
    merely contains «N» is not one.
    """
    for index, cell in enumerate(row.cells):
        text = cell.strip()
        if text and fold(text) in criteria:
            return index
    return None


def criterion_column(table):
    """The unnamed column naming which quantity an «Extrêmes» row is extreme in, or None.

    Found by content: the column whose non-empty values are all force symbols. Never by index -- it sits at 4 or at 5 depending on the table's shape, and index 4 is the *markers* column in some of them.
    """
    symbols = {fold(spelling) for key in FORCES for spelling in FORCE_ALIASES[key]}
    for column in table.columns:
        values = set()
        for row in table.rows:
            if column.index < len(row.cells):
                cell = row.cells[column.index].strip()
                if cell:
                    values.add(fold(cell))
        if values and values <= symbols:
            return column
    return None


def loading_of(path):
    """`("CO1", "CO", 1)` from «CO1_analyse_statique_….csv», or `(stem, "", None)` from a file RFEM did not prefix."""
    stem = re.sub(r"\.csv$", "", os.path.basename(str(path)), flags=re.I)
    match = _LOADING.match(stem)
    if match:
        return f"{match.group(1)}{match.group(2)}", match.group(1), int(match.group(2))
    return stem, "", None


def read_member_forces(path, name=None):
    """The member internal forces one exported CSV holds, or None where it is not such a table.

    Returns a `ForceTable`. A unit the reader does not know is a problem on the table and that force is left out of every station, rather than being taken for kN.
    """
    try:
        table = read_table(path, name=name)
    except RfemCsvError:
        return None
    return forces_of(table, path)


def forces_of(table, path=None, loading=None):
    """The member internal forces one already-read `Table` holds, or None where it is not such a table.

    What `read_member_forces` does once the file is read, and the way a **workbook** sheet is read: RFEM's table export writes its results into the same XLSX as the model, one sheet per loading («CO1 | Barres | Efforts internes»), and nothing above `csv_tables` can tell a sheet from a file. `loading` names the loading where the caller knows it -- a sheet's name says it and a file's name says it differently -- and is read off `path` where it does not.

    ⚠️ **A sheet of that kind is grouped by cross-section**, and opens each group with a row naming the section: its member cell holds a name and not a number, so it falls where an «Extrêmes» label falls and is counted as a trailer. Nothing had to be added for it, which is what the row-by-row accounting is for.
    """
    if not is_member_forces(table):
        return None

    path = table.path if path is None else path
    problems = []
    member_column = table.column(*MEMBER_ALIASES) or table.columns[0]
    location = table.column(*LOCATION_ALIASES)
    criterion = criterion_column(table)
    node = table.column("Nœud n°", "Knoten Nr.", "Node No.", "no")
    markers = table.column("Marqueurs", "Markierungen", "Markers")

    factors, units, force_columns = {}, {}, {}
    for key in FORCES:
        column = table.column(*FORCE_ALIASES[key])
        force_columns[key] = column
        factor = _factor(column.unit, table, key, str(path), problems)
        factors[key] = factor
        units[key] = column.unit
    length_factor = 1.0
    if location is not None:
        length_factor = _factor(location.unit, table, "x", str(path), problems) or 1.0
        units["x"] = location.unit

    stations, extremes, trailers, summaries = [], 0, 0, 0
    for row in table.rows:
        # ⚠️ The criterion is tested **before** the label, and the order is the whole point: RFEM opens an extremes section with a row labelled «Extrêmes» *and* carrying a criterion, then goes on writing the member's number on the rows that follow. Testing the label first counted that opening row among the «Total» trailers, so `extremes` said one where the section held two -- the accounting still balanced, which is exactly why it had to be named rather than left to balance.
        if criterion_at(row, CRITERIA) is not None:
            extremes += 1
            continue
        if row.is_labelled:
            trailers += 1
            continue
        member = number(row.cells[member_column.index]) if member_column.index < len(row.cells) else None
        if member is None:
            trailers += 1
            continue
        # ⚠️ A station has a station. After each member's extremes RFEM writes a «Total» row and then a row carrying **the member's number and no x at all** -- the member's own summary, one per member, 62 of them in this model. It has a numeric member number and an empty criterion, so nothing but the missing `x` tells it from a distribution row; taken for one, it put a phantom station on every member.
        if location is not None and row.at(location) is None:
            summaries += 1
            continue
        forces = {}
        for key in FORCES:
            value = row.at(force_columns[key])
            if value is not None and factors[key] is not None:
                forces[key] = value * factors[key]
        x = row.at(location) if location is not None else None
        stations.append(Station(
            member=int(member),
            x=None if x is None else x * length_factor,
            forces=forces,
            node=None if row.at(node) is None else int(row.at(node)),
            markers=(row.cells[markers.index].strip() if markers is not None and markers.index < len(row.cells) else ""),
        ))

    loading, kind, num = loading_of(loading if loading is not None else path)
    return ForceTable(str(path), table.name, loading, kind, num, stations, extremes, summaries, trailers, units, problems)


def read_workbook_results(path):
    """Every member-forces sheet of an RFEM table export in XLSX, as a `Results`.

    The other half of `read_results`, which reads a folder of CSVs: the same dialog writes the results into the same workbook as the model, one sheet per loading, so a project that hands over one file hands over everything. A sheet that is not a member-forces table is counted in `skipped` and not named -- an export of this project holds 490 sheets and 58 of them are these.

    ⚠️ **Read one sheet at a time**, so a workbook of 14 MB costs the 58 sheets and not the 490 (`csv_tables.Workbook`).
    """
    from rfem_import.csv_tables import read_workbook

    book = read_workbook(path)
    tables, problems, skipped = [], [], 0
    try:
        for name in book.names:
            table = book.table(name)
            if table is None:
                skipped += 1
                continue
            found = forces_of(table, path=f"{path}[{name}]", loading=name)
            if found is None:
                skipped += 1
                continue
            tables.append(found)
            problems.extend(found.problems)
    finally:
        book.close()
    return Results(str(path), tables, problems, skipped)


class Results:
    """Every member-forces table of one exported folder, by loading.

    A loading may have several -- RFEM writes the distribution and variants grouped by section or by member set -- so they are kept as a list and `base(loading)` is what picks the fullest, rather than guessing from a localised filename.
    """

    __slots__ = ("folder", "tables", "problems", "skipped")

    def __init__(self, folder, tables, problems, skipped):
        self.folder, self.tables, self.problems, self.skipped = folder, tables, problems, skipped

    @property
    def loadings(self):
        return sorted({table.loading for table in self.tables})

    def of(self, loading):
        return [table for table in self.tables if table.loading == loading]

    def base(self, loading):
        """The fullest member-forces table of that loading: the one with most stations. None where the loading has none."""
        tables = self.of(loading)
        return max(tables, key=len) if tables else None

    def __len__(self):
        return len(self.tables)

    def __repr__(self):
        return f"Results({len(self.tables)} tables, {len(self.loadings)} loadings)"


def read_results(folder):
    """Every member-forces table in `folder`, read.

    Files that are not member-forces tables are counted in `skipped` and not reported one by one: an RFEM export holds hundreds of tables of other kinds -- deformations, support forces, design ratios -- and naming each would bury what matters.
    """
    folder = str(folder)
    tables, problems, skipped = [], [], 0
    for entry in sorted(os.listdir(folder)):
        if not entry.lower().endswith(".csv"):
            continue
        table = read_member_forces(os.path.join(folder, entry))
        if table is None:
            skipped += 1
            continue
        tables.append(table)
        problems.extend(table.problems)
    return Results(folder, tables, problems, skipped)


# -- one loading at a time ---------------------------------------------------------------
#
# ⚠️ **Reading every loading of a workbook costs 105 s and reading one costs 2.9 s** (measured on the
# engineer's own 490-sheet, 13 MB export). The window shows one diagram at a time, so it asks for one
# loading -- which is what makes the RFEM tab's figure answer in the time a tab switch may take
# (docs/domain/rfem.md §3.3duodecies, the engineer's own «à la demande, par structure»).

def loadings_in(path):
    """The loadings a workbook carries member forces for, in the order RFEM wrote them: `["CC1", …, "CO48"]`.

    Resolved from the **sheet names alone**, so it costs no reading at all: a sheet is a member-forces
    sheet of loading L when its name starts with L and carries the words RFEM heads that table with.
    The loading's id is the part before the first separator, which RFEM writes first in every language
    («CO1 | Barres | Efforts internes», «CO1 | Stäbe | Schnittgrössen»).
    """
    from rfem_import.csv_tables import read_workbook

    book = read_workbook(path)
    try:
        found = []
        for name in book.names:
            head = re.split(r"\s*[|\-]\s*", name, maxsplit=1)
            if len(head) < 2 or not _LOADING_ID.match(head[0].strip()):
                continue
            if fold(head[1]) and any(word in fold(name) for word in _FORCE_WORDS):
                loading = head[0].strip()
                if loading not in found:
                    found.append(loading)
        return found
    finally:
        book.close()


def read_loading(path, loading):
    """The member forces of one loading of an XLSX export, as a `ForceTable`, or None where it has none.

    The one sheet is read and the other 489 are not (`csv_tables.Workbook`), which is the difference
    between 2.9 s and 105 s.
    """
    from rfem_import.csv_tables import read_workbook

    book = read_workbook(path)
    try:
        for name in book.names:
            head = re.split(r"\s*[|\-]\s*", name, maxsplit=1)
            if len(head) < 2 or head[0].strip() != loading:
                continue
            if not any(word in fold(name) for word in _FORCE_WORDS):
                continue
            table = book.table(name)
            if table is None:
                continue
            found = forces_of(table, path=f"{path}[{name}]", loading=loading)
            if found is not None:
                return found
        return None
    finally:
        book.close()
