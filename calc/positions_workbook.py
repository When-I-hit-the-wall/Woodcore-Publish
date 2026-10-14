"""Positionen.xlsx read, for the one thing it is still read for: its positions imported into Woodcore's own `positions.json` (calc/positions_store.py, docs/domain/positions.md §7, v0.114).

From v0.94 to v0.113 this module also wrote the workbook -- a row added, modified or deleted from Woodcore's «Positions» tab, the engineer's drop-down lists put back after openpyxl saved. Since v0.114 Woodcore keeps the positions itself, and the workbook of a project made before is read once (`positions_store.migrate`, at the first opening or the first export) and then moved into the project's archives; the tab's «Importer depuis Excel…» reads one found later. So nothing writes a workbook any more, and what is left is the reader: the rows of «Positions Element», its legend's lists and symbols.

Every refusal is a WorkbookError whose `args[0]` is an English sentence and whose `code` and `detail` are what a window writes its own sentence from.
"""

import os
import warnings
import zipfile
from collections import namedtuple
from pathlib import Path

# The sheet the positions were on -- `Positions` until v0.33, when the connectors got a sheet of their own -- and the legend sheet beside it.
ELEMENTS_SHEET = "Positions Element"
OLD_ELEMENTS_SHEET = "Positions"
LEGEND_SHEET = "data_type"

Table = namedtuple("Table", "headers rows")


class WorkbookError(Exception):
    """A workbook that cannot be read as Positionen.xlsx: `args[0]` a sentence that stands on its own in English; `code` and `detail` what Woodcore's window turns into its own three languages."""

    def __init__(self, message, code, **detail):
        super().__init__(message)
        self.code = code
        self.detail = detail


# --- reading ----------------------------------------------------------------------------

def _load(path, **options):
    """openpyxl warns about the list extension it is about to drop -- which is what this module puts back -- so it is silenced, as io_excel silences it."""
    from openpyxl import load_workbook
    from openpyxl.utils.exceptions import InvalidFileException
    name = Path(path).name if isinstance(path, (str, os.PathLike)) else getattr(path, "name", "workbook")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        try:
            return load_workbook(path, **options)
        except FileNotFoundError:
            raise WorkbookError(f"{path}: no such workbook", "missing", workbook=name) from None
        except (zipfile.BadZipFile, InvalidFileException, KeyError, ValueError) as exc:
            raise WorkbookError(f"{name} cannot be read as a workbook ({exc})", "unreadable", workbook=name) from None


def _text(value):
    return "" if value is None else str(value).strip()


def _elements(book, name):
    if ELEMENTS_SHEET in book.sheetnames:
        return book[ELEMENTS_SHEET]
    if OLD_ELEMENTS_SHEET in book.sheetnames:
        raise WorkbookError(f"{name}: the sheet '{OLD_ELEMENTS_SHEET}' is called '{ELEMENTS_SHEET}' now -- rename it in Excel",
                            "old-sheet", workbook=name)
    raise WorkbookError(f"{name}: no sheet '{ELEMENTS_SHEET}' -- found: {', '.join(book.sheetnames)}", "no-sheet", workbook=name)


def _headers(sheet):
    """{header: column number} of row 1, as typed, the first of two equal headers winning as it does for the export."""
    headers = {}
    for cell in next(sheet.iter_rows(min_row=1, max_row=1), ()):
        name = _text(cell.value)
        if name and name not in headers:
            headers[name] = cell.column
    return headers


def read(path):
    """The rows of Positions Element: Table(headers, rows), the headers in column order and each row a dict keyed by them, empty rows left out. Values as the cells hold them -- a moisture class a number, a text stripped."""
    path = Path(path)
    sheet = _elements(_load(path, data_only=True), path.name)
    headers = _headers(sheet)
    rows = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        record = {}
        for name, column in headers.items():
            value = row[column - 1] if column <= len(row) else None
            record[name] = value.strip() if isinstance(value, str) else value
        if any(_text(value) for value in record.values()):
            rows.append(record)
    return Table(tuple(headers), rows)


def choices(path):
    """The lists of the legend sheet, by header -- what the engineer's drop-downs offer: {"type": [...], "material": [...], "resistance class": [...], "section type": [...]}, each in the order the sheet lists it. Empty where the workbook has no legend sheet."""
    return choices_in(_load(path, data_only=True))


def choices_in(book):
    """`choices` of a workbook already open."""
    if LEGEND_SHEET not in book.sheetnames:
        return {}
    lists = {}
    for column in book[LEGEND_SHEET].iter_cols(values_only=True):
        header = _text(column[0]) if column else ""
        if header and header not in lists:
            lists[header] = [_text(value) for value in column[1:] if _text(value)]
    return lists


def symbols(path):
    """{type: symbol} from the legend's rows carrying both -- «Träger» T, «Stütze» S -- which is what an id is proposed from (`propose_id`)."""
    book = _load(path, data_only=True)
    if LEGEND_SHEET not in book.sheetnames:
        return {}
    sheet = book[LEGEND_SHEET]
    headers = {name.lower(): column for name, column in _headers(sheet).items()}
    if "symbol" not in headers or "type" not in headers:
        return {}
    found = {}
    for row in sheet.iter_rows(min_row=2):
        symbol, name = _text(row[headers["symbol"] - 1].value), _text(row[headers["type"] - 1].value)
        if symbol and name:
            found.setdefault(name, symbol)
    return found
