"""A table RFEM exported as CSV, read into columns and rows.

This is the universal half of the RFEM import: **RFEM's own table export needs no API key**, so it is the one route every user has (`calc/rfem_import/` — docs/open-questions.md §14). A script driving the gRPC API can produce the same data faster and at full precision, but only for a user Dlubal has issued a key to; this module is what does not depend on that.

It reads *structure* and nothing else: no notion of a member, a force or a load case, so it can be pointed at any table RFEM writes and tested against all 580 files of one export. What a column *means* is `results.py`'s and the model readers' business.

**The format, established on RFEM 6.15's own output** rather than assumed -- 580 CSV files exported from the engineer's model:

- **UTF-8 with a BOM**, so the file is opened `utf-8-sig`; a BOM left in place turns the first header cell into something no alias matches.
- **Semicolon-separated**, with **CRLF** line endings. The delimiter is sniffed all the same, since a machine set to another list separator writes commas, and a table of numbers with decimal commas would then be unreadable.
- **Two header rows.** The first carries group names that *span* columns -- «Forces [kN]» over N, V_y and V_z -- an empty cell continuing the group to its left; the second carries the column's own name. A column's name is the second row's cell where it has one, and the first row's where it has not («Barre n°», whose second cell is empty).
- **Units live in the headers, in brackets**: «Forces [kN]», «x [m]». Read from the name first, then from the group. ⚠️ A unit is whatever the model's «Unités et décimales» says, so it is *read* and never assumed: the same table is kN in one project and N in another.
- **The headers are localised.** This project's RFEM is French («Barre n°», «Nœud», «Commentaire»), another office's is German. What saves the reader is that the columns that matter most are *symbols* -- N, V_y, V_z, M_T, M_y, M_z are the same in every language -- so only the identifying columns need aliases, and `column()` matches on an accent- and case-insensitive form of the name, the group-and-name, or the slug.
- **A column may have no header at all and still carry data.** In the member internal forces table the fifth column is headed by nothing and holds the criterion of an «Extrêmes» row (`N`, `V_y`, …). Such a column is kept and named `col<index>`; dropping empty-header columns would have thrown it away.
- **Rows of two kinds are interleaved.** A row whose first cell is not a number is RFEM's own summary row -- «Extrêmes» -- repeating a governing value. They are returned as they come, `Row.is_labelled` telling them apart, because filtering them is a decision about results and not about CSV.

⚠️ **What this module is not for, and why it does not try to refuse it.** RFEM's `*_résumé.csv` is not a table of objects but a list of statements («Somme des charges en Z; 247.95; kN») with section titles among its rows, and `read_table` reads it without complaint -- it is delimited text like any other. A rule was tried and dropped: «a table whose first column is empty in every row is not a table of objects» refuses all 57 `résumé` files of one export, and also refuses `timber_design_non_valide-désactivé.csv`, which is a perfectly real table (object type, object numbers, error code, description) that merely opens with a blank column. One false refusal in 580 is worse than none, because it drops a table silently.

So the guard is not here but at the point of use: a caller says which columns it needs (`require`), and gets a refusal naming what the file actually holds. `read_table` refuses only what is structurally impossible -- a file with no row, or one whose very first row already carries numbers and so has no header.

⚠️ **The composite last column is not where a comment should be read.** The result tables end in a column headed «Section (matériau) | Commentaire sur la barre» whose cells hold four or more parts joined by « | » -- type, section, material, length, and the comment after them. Which part is the comment cannot be told apart reliably, and it does not have to be: the **model's** member table carries a clean `comment` column, and that is where `metadata_parser` is pointed.
"""

import csv
import re
import unicodedata

# The delimiters worth sniffing, most likely first. RFEM writes `;` on this machine; a list separator set to comma or tab is what another Windows locale gives.
DELIMITERS = (";", "\t", ",")

# At most this many leading rows are taken for headers. RFEM writes two for an object or result table; the cap is what keeps a file of the wrong kind from being read as a table with a very tall head (the `résumé` files above).
MAX_HEADER_ROWS = 2

# A unit written in brackets at the end of a header: «Forces [kN]», «x [m]», «V [m^3]».
_UNIT = re.compile(r"\[([^\]]+)\]\s*$")

# What RFEM writes in the brackets of a quantity that has none -- «[--]», seen nine times over one export. Read as no unit, so that a dimensionless column does not come back carrying a dash where a caller expects a unit or None.
_NO_UNIT = {"--", "-", "–", "—", ""}

# What a thousands separator may be, none of which is a decimal point: an apostrophe (Swiss), a narrow or ordinary no-break space, a plain space. Stripped before a number is read, so that «1'234.56» and «1 234,56» are both numbers. No sample in the engineer's own export reaches four digits, so this is defensive rather than observed, and it is written down as such.
_GROUPING = ("'", "’", " ", " ", " ")

# Characters that must not simply be dropped, because dropping them makes two different headers fold alike. The degree sign is the one that bites: «n°» is French for «No.» and folding it to `n` collided with the axial force **N** in the member internal forces table, so `value("N")` read the node number. It folds to `o`, which also makes «n°» and the English «No.» one key.
_LIGATURES = {
    "œ": "oe", "Œ": "OE", "æ": "ae", "Æ": "AE", "ß": "ss",
    "°": "o", "º": "o",
}


# The metres in one of each length unit a header may declare. Here rather than in each reader because a table's own header is where a unit comes from, and three copies of this table is three places to get it wrong; `results.py` and `metadata_parser.py` still carry their own, and `tests/test_rfem_csv.py` holds all three equal.
LENGTH_UNITS = {"mm": 0.001, "cm": 0.01, "dm": 0.1, "m": 1.0}


class RfemCsvError(Exception):
    """A file that is not a table RFEM wrote, or one whose header cannot be delimited. Names the file, since an import points at a folder of hundreds."""


def fold(text):
    """A header reduced to what can be compared across languages and spellings: lower case, no accents, no ligature, every run of anything else one underscore.

    «Barre n°» and «barre n ¤» fold alike; «Nœud» folds to `noeud`. It is what lets `column()` be given a display name, a slug or a group-and-name and find the same column.
    """
    text = "" if text is None else str(text)
    # ⚠️ **A hyphen in a header is never a word boundary, so it is dropped rather than made a separator.** RFEM uses it two ways and neither parts two words: as a **hyphenation**, breaking one word across its cell or across the two header rows — «Last-\n kombin.» is «Lastkombin.» and «Last-» over «richtung» is «Lastrichtung» — and as a **joiner** inside one term, «Cross-Section», «Stablast-Parameter». Measured on `DE.xlsx` and `EN.xlsx`: read as a separator, the German combination identifier and the German load direction matched no alias, silently. The line break goes first, so a hyphenation across rows leaves no underscore behind.
    text = text.replace("-\r\n", "").replace("-\n", "").replace("-", "")
    for char, plain in _LIGATURES.items():
        text = text.replace(char, plain)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def number(text):
    """A cell read as a float, or None where it holds no number.

    Accepts a decimal point or a decimal comma, and strips the grouping characters above. Where a cell carries both a point and a comma the **last** of the two is the decimal separator, which is the only reading that makes «1.234,56» and «1,234.56» both right.
    """
    if text is None:
        return None
    raw = str(text).strip()
    if not raw:
        return None
    for char in _GROUPING:
        raw = raw.replace(char, "")
    if "," in raw and "." in raw:
        decimal = max(raw.rfind(","), raw.rfind("."))
        raw = re.sub(r"[.,]", "", raw[:decimal]) + "." + raw[decimal + 1:]
    else:
        raw = raw.replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


class Column:
    """One column of the table: where it sits, what it is called, which group it belongs to, and the unit its header declares."""

    __slots__ = ("index", "name", "group", "unit", "id")

    def __init__(self, index, name, group, unit, id):
        self.index, self.name, self.group, self.unit, self.id = index, name, group, unit, id

    @property
    def full(self):
        """«Forces [kN] N» -- the group and the name, as the two header rows read together.

        ⚠️ **A group ending in a hyphen is a word RFEM broke across the two header rows**, and the two halves are joined with no space between them: the German member-load table heads its direction column «Last-» on the first row and «richtung» on the second, which is «Lastrichtung» and not «Last- richtung». Measured on `DE.xlsx`; it is the same hyphenation `fold` undoes inside a single cell.
        """
        if not self.group:
            return self.name
        joiner = "" if self.group.endswith("-") else " "
        return f"{self.group}{joiner}{self.name}".strip()

    def __repr__(self):
        unit = f" [{self.unit}]" if self.unit else ""
        return f"Column({self.index}, {self.full!r}{unit})"


class Row:
    """One row: its cells, and whether RFEM labelled it instead of numbering it.

    `is_labelled` is true for the «Extrêmes» rows RFEM interleaves with the distribution -- their first cell is a word where a data row's is an object number. It is stated rather than filtered here, the decision being about results and not about CSV.
    """

    __slots__ = ("cells", "table")

    def __init__(self, cells, table):
        self.cells, self.table = cells, table

    def __getitem__(self, key):
        return self.cells[key] if isinstance(key, int) else self.table.cell(self, key)

    def __len__(self):
        return len(self.cells)

    @property
    def label(self):
        return self.cells[0].strip() if self.cells else ""

    @property
    def is_labelled(self):
        return bool(self.label) and number(self.label) is None

    def get(self, *aliases, default=None):
        return self.table.cell(self, *aliases, default=default)

    def value(self, *aliases):
        """The cell as a float, or None -- what a force or a coordinate is read with.

        ⚠️ **Never call this with a `Column`'s own `name`.** A name is not unique in an RFEM table: the node table
        carries two columns named «X» -- «Coordonnées X», relative to the node's reference node, and «Coordonnées
        globales X» -- and a member-forces table carries two named «n°», the member's and the node's. `column()`
        registers the first of each (`setdefault`), so resolving a column by its full name and then asking for its
        *bare* name gives back the **other** column. That is what read every relative coordinate as a global one
        and drew seven of this model's sixty-two members somewhere they are not. `at()` is what to use once a
        column is in hand.
        """
        return number(self.table.cell(self, *aliases))

    def at(self, column):
        """The cell of **this** column as a float, or None -- the column itself and never its name (see `value`)."""
        if column is None or column.index >= len(self.cells):
            return None
        return number(self.cells[column.index])

    def __repr__(self):
        return f"Row({self.cells!r})"


class Table:
    """A table RFEM exported: its `columns`, its `rows`, and where it came from."""

    __slots__ = ("path", "name", "columns", "rows", "delimiter", "header", "_by_key")

    def __init__(self, path, name, columns, rows, delimiter, header):
        self.path, self.name, self.delimiter, self.header = path, name, delimiter, header
        self.columns = columns
        self.rows = [Row(cells, self) for cells in rows]
        # ⚠️ A column holding no number at all has no unit, whatever its header said. RFEM's group row spans to the end of the line, so the member internal forces table's last column -- the composite «Section (matériau) | Commentaire sur la barre» -- is swept into «Moments [kNm]» and came out declaring kNm. Nothing in the header can tell that apart; the cells can.
        for column in columns:
            if column.unit and not any(
                number(cells[column.index]) is not None
                for cells in rows if column.index < len(cells)
            ):
                column.unit = None
        self._by_key = {}
        for column in columns:
            for key in (column.id, fold(column.name), fold(column.full)):
                self._by_key.setdefault(key, column)

    def column(self, *aliases):
        """The first column any of `aliases` names, or None. An alias may be a slug, a display name or a group-and-name, in any language's spelling and any case."""
        for alias in aliases:
            found = self._by_key.get(fold(alias))
            if found is not None:
                return found
        return None

    def require(self, *aliases):
        """The column, or `RfemCsvError` naming what was looked for and what the file actually holds -- so an unrecognised language says which header to add rather than failing further down."""
        found = self.column(*aliases)
        if found is None:
            have = ", ".join(f"«{c.full}»" for c in self.columns) or "nothing"
            raise RfemCsvError(
                f"{self.path}: no column named {' or '.join(repr(a) for a in aliases)} -- this table holds {have}"
            )
        return found

    def cell(self, row, *aliases, default=None):
        column = self.column(*aliases)
        if column is None or column.index >= len(row.cells):
            return default
        return row.cells[column.index]

    def unit(self, *aliases):
        column = self.column(*aliases)
        return column.unit if column else None

    def data_rows(self):
        """The rows RFEM numbered -- every «Extrêmes» row left out."""
        return [row for row in self.rows if not row.is_labelled]

    def __len__(self):
        return len(self.rows)

    def __iter__(self):
        return iter(self.rows)

    def __repr__(self):
        return f"Table({self.name!r}, {len(self.columns)} columns, {len(self.rows)} rows)"


def sniff(sample):
    """The delimiter a sample of the file uses: the candidate that splits its first lines into the most, and equally many, fields. Falls back to `;`, which is what RFEM writes here."""
    lines = [line for line in sample.splitlines() if line.strip()][:6]
    best, score = DELIMITERS[0], 0
    for delimiter in DELIMITERS:
        counts = [line.count(delimiter) for line in lines]
        if not counts or min(counts) == 0:
            continue
        # A real delimiter gives every line the same number of fields; prefer the one that does, then the one that gives most.
        consistent = len(set(counts)) == 1
        value = min(counts) * (10 if consistent else 1)
        if value > score:
            best, score = delimiter, value
    return best


def _headers(rows):
    """How many leading rows are headers: the rows before the first one carrying a number, capped at `MAX_HEADER_ROWS` -- and never more rows than the file holds.

    ⚠️ That last cap is what an **empty table** needs. A model with no surfaces exports its surface table as a header row and nothing else, and without the cap this returned 2 for a file of one row: the header was read as two rows, of which one did not exist.
    """
    for index, cells in enumerate(rows[: MAX_HEADER_ROWS + 1]):
        if any(number(cell) is not None for cell in cells):
            return index
    return min(MAX_HEADER_ROWS, len(rows))


def _columns(header):
    """The columns the header rows describe: a group spanning until the next non-empty cell of the first row, a name from the last row that has one, and a unit out of either's brackets."""
    width = max((len(row) for row in header), default=0)
    groups, starts, group = [], [], ""
    first = header[0] if header else []
    for index in range(width):
        cell = first[index].strip() if index < len(first) else ""
        if cell:
            group = cell
        groups.append(group)
        starts.append(bool(cell))

    columns, used = [], {}
    for index in range(width):
        name = ""
        for row in reversed(header[1:]):
            if index < len(row) and row[index].strip():
                name = row[index].strip()
                break
        group = groups[index]
        # Where only the first row named this column, that name is the column's own and not a group -- but only where the group *started* here. A column the group merely spans has no name of its own, and calling it after the group would give «Position» to both the x column's neighbour and the unnamed criterion column beside it.
        if not name and starts[index]:
            name, group = group, ""
        elif group == name:
            group = ""

        unit = None
        for text, own in ((name, True), (group, False)):
            match = _UNIT.search(text or "")
            if match:
                unit = match.group(1).strip()
                if unit in _NO_UNIT:
                    unit = None
                if own:
                    name = _UNIT.sub("", name).strip()
                else:
                    group = _UNIT.sub("", group).strip()
                break

        key = fold(name) or f"col{index}"
        if key in used:
            used[key] += 1
            key = f"{fold(group)}_{key}" if group else f"{key}_{used[key]}"
        else:
            used[key] = 1
        columns.append(Column(index, name, group, unit, key))
    return columns


def read_table(path, name=None):
    """The table one RFEM-exported CSV holds.

    `name` names the table in messages; the file's stem is used where it is not given. Raises `RfemCsvError` on a file holding no row at all and on one whose very first row already carries numbers -- which is what a file that is not a table looks like from here.

    ⚠️ **A table of no rows is a table**, and is read: an object type the model has none of exports its header and nothing else -- this project's surface table, the model carrying no surface. Refusing it made «the model has no surfaces» and «this export is broken» one exception, which a caller cannot tell apart, and it stopped the structure detection of every model built out of members alone.
    """
    path = str(path)
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(8192)
        handle.seek(0)
        delimiter = sniff(sample)
        rows = [row for row in csv.reader(handle, delimiter=delimiter)]

    stem = name or re.sub(r"\.csv$", "", path.replace("\\", "/").rsplit("/", 1)[-1])
    return table_from_rows(rows, path, stem, delimiter)


def table_from_rows(rows, path, name, delimiter=None):
    """A `Table` out of rows of cells, whatever they were read from -- a CSV's lines or a worksheet's cells.

    It is the whole of `read_table` but the reading, which is what lets one table abstraction serve both formats RFEM's table export writes (`read_workbook`): every rule about header rows, spanning groups, units in brackets and unnamed columns is stated once. A cell that is not a string -- a number a worksheet stored as a number -- is written out as one, since every rule here reads text.
    """
    rows = [[("" if cell is None else str(cell)) for cell in row] for row in rows]
    rows = [row for row in rows if any(cell.strip() for cell in row)]
    if not rows:
        raise RfemCsvError(f"{path}: the file holds no row at all")

    count = _headers(rows)
    if count == 0:
        raise RfemCsvError(
            f"{path}: the first row already holds numbers, so this file has no header -- read_table wants a table RFEM exported, not a list of statements such as a «résumé» file"
        )
    header, body = rows[:count], rows[count:]
    columns = _columns(header)
    if not columns:
        raise RfemCsvError(f"{path}: no column could be read from its header")

    return Table(path, name, columns, body, delimiter, header)


class Workbook:
    """The tables one RFEM table export in XLSX holds, **read one sheet at a time**.

    ⚠️ **A sheet is read only when it is asked for, and that is the difference between four seconds and forty-five.** A full export of this project is **490 to 609 sheets and 14 MB**, nearly all of it results, where the model reader wants some twenty of them: the ten model tables and two per load case. Reading every sheet eagerly cost 43 s a workbook and 4 % of it was used. A sheet read once is kept, so asking twice costs nothing.

    ⚠️ **Excel truncates a sheet name to 31 characters**, and RFEM's table names are longer: «Ajustements des résultats de su», «CC1 - Charges d'ensembles de li». So a sheet is looked up by **prefix** as well as by its whole name, and a caller never has to know where the cut fell. It does not collide in practice, RFEM putting the loading's own id first — «CO1 | …» and «CO10 | …» differ inside 31 characters — and 294 of one export's names sit exactly at the limit with not one duplicate.

    It holds the workbook open for as long as it is used, so a caller closes it — `read_model` does, and `with read_workbook(path) as book:` works.
    """

    __slots__ = ("path", "names", "_book", "_tables", "_folded")

    def __init__(self, path, book, names):
        self.path, self._book, self.names = path, book, list(names)
        self._tables = {}
        self._folded = {}
        for name in self.names:
            self._folded.setdefault(fold(name), name)

    def _load(self, name):
        """That sheet as a `Table`, read now and kept. None where it is not a table at all -- an empty sheet, or a note."""
        if name not in self._tables:
            rows = [list(row) for row in self._book[name].iter_rows(values_only=True)]
            try:
                self._tables[name] = table_from_rows(rows, f"{self.path}[{name}]", name)
            except RfemCsvError:
                self._tables[name] = None
        return self._tables[name]

    def sheet(self, *aliases):
        """The name of the sheet any of `aliases` names, or None -- resolved without reading it."""
        for alias in aliases:
            found = self._folded.get(fold(alias))
            if found is not None:
                return found
        for alias in aliases:
            key = fold(alias)
            for folded, name in self._folded.items():
                if folded and key.startswith(folded):
                    return name
        return None

    def table(self, *aliases):
        """The table any of `aliases` names, read now, or None."""
        name = self.sheet(*aliases)
        return None if name is None else self._load(name)

    def require(self, *aliases):
        """The table, or `RfemCsvError` naming what was looked for -- so an export in an unrecognised language says which sheet to add rather than failing further down."""
        found = self.table(*aliases)
        if found is None:
            have = ", ".join(f"«{name}»" for name in self.names[:12]) or "nothing"
            raise RfemCsvError(
                f"{self.path}: no sheet named {' or '.join(repr(a) for a in aliases)} -- this workbook holds {have}…"
            )
        return found

    def close(self):
        self._book.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def __getitem__(self, name):
        return self.require(name)

    def __contains__(self, name):
        return self.sheet(name) is not None

    def __len__(self):
        return len(self.names)

    def __repr__(self):
        return f"Workbook({len(self.names)} sheets, {len(self._tables)} read)"


def read_workbook(path):
    """An RFEM table export in XLSX, as a `Workbook` whose sheets are read one at a time.

    The same abstraction the CSV route gives, from the format the engineer actually hands over: RFEM's *Fichier → Exporter → Tableaux* writes either one XLSX of every table or one CSV per table, and a reader above this cannot tell which it was given. A sheet with a header and no rows is a table of no rows, which is what an object type the model has none of looks like.

    ⚠️ **openpyxl is imported here and not at the top of the module**, so that the CSV route -- the one route every user has -- needs nothing beyond the standard library, exactly as `domains/plan.py` imports pypdf only for a plan that has a PDF background.
    """
    import openpyxl                                          # noqa: PLC0415 -- deliberately lazy, see above

    path = str(path)
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    if not book.sheetnames:
        book.close()
        raise RfemCsvError(f"{path}: this workbook holds no sheet at all")
    return Workbook(path, book, book.sheetnames)
