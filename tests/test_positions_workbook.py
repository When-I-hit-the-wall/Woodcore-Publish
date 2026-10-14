"""Positionen.xlsx read (calc/positions_workbook.py, docs/domain/positions.md §7), for the one thing it is still read for since v0.114: its positions imported into Woodcore's own positions.json (calc/positions_store.py, tests/test_positions_store.py).

From v0.94 to v0.113 the module also wrote the workbook, and this file held that its writes kept the engineer's drop-down lists; nothing writes a workbook any more, so what is left to hold is the reader: the rows read back as the cells hold them, the legend's lists and symbols, and a workbook that is not one refused by name.

The workbooks are built here -- the engineer's own is never copied into the repository.
"""

import conftest

import positions_workbook as workbook

HEADERS = ["position", "type", "material", "resistance class", "dimension", "units", "moisture class", "description"]
ROWS = [
    ["T001", "Träger", "Fichte", "C24", "100/200", "mm", 2, "UK"],
    ["S001", "Stütze", "Fichte", "C24", 180, "mm", 2, "UK"],
    [None, None, None, None, None, None, None, None],
    ["S002", "Träger", "Stahl", "S355", "101.6/10", "mm", 2, "Pavillon - Stahlstütze"],
]
LEGEND = [
    ["symbol", "type", "material", "resistance class", "units"],
    ["T", "Träger", "Fichte", "C24", "mm"],
    ["S", "Stütze", "Buche", "C30", "cm"],
    ["D", "Decke/Dach", "Stahl", "S355", "m"],
]


def _build(name, sheet_title="Positions Element", legend=True):
    from openpyxl import Workbook
    path = conftest.tmpdir(name) / "Positionen.xlsx"
    book = Workbook()
    sheet = book.active
    sheet.title = sheet_title
    sheet.append(HEADERS)
    for row in ROWS:
        sheet.append(row)
    if legend:
        extra = book.create_sheet("data_type")
        for row in LEGEND:
            extra.append(row)
    book.save(path)
    return path


def test_the_rows_read_back_as_the_cells_hold_them():
    path = _build("pw_read")
    table = workbook.read(path)
    assert table.headers == tuple(HEADERS), table.headers
    assert [row["position"] for row in table.rows] == ["T001", "S001", "S002"], "a blank row is no row"
    assert table.rows[0]["moisture class"] == 2 and isinstance(table.rows[0]["moisture class"], int)
    assert table.rows[1]["dimension"] == 180, "a number typed into Excel stays a number: positions_store makes it the text «180»"
    assert workbook.choices(path)["type"] == ["Träger", "Stütze", "Decke/Dach"]
    assert workbook.symbols(path) == {"Träger": "T", "Stütze": "S", "Decke/Dach": "D"}


def test_a_workbook_that_is_not_one_is_refused_by_name():
    for path, code in ((_build("pw_old", sheet_title="Positions"), "old-sheet"), (_build("pw_none", sheet_title="Tabelle1"), "no-sheet")):
        try:
            workbook.read(path)
        except workbook.WorkbookError as exc:
            assert exc.code == code and path.name in str(exc), (code, str(exc))
        else:
            raise AssertionError(f"{code}: read")
    broken = conftest.tmpdir("pw_broken") / "Positionen.xlsx"
    broken.write_bytes(b"not a workbook")
    for path, code in ((broken, "unreadable"), (broken.with_name("absent.xlsx"), "missing")):
        try:
            workbook.read(path)
        except workbook.WorkbookError as exc:
            assert exc.code == code, (code, exc.code)
        else:
            raise AssertionError(f"{code}: read")
    assert workbook.choices(_build("pw_no_legend", legend=False)) == {}


def test_nothing_writes_a_workbook_any_more():
    """v0.114: the writer is gone with the workbook as a source -- what is left must not look as if it could write one."""
    for name in ("add", "update", "delete", "ensure_section_column", "propose_id"):
        assert not hasattr(workbook, name), name
