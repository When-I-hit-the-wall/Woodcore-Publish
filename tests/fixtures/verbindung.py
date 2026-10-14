"""The cells of the engineer's `Verbindung.xlsm` the tests compare with, frozen once into verbindung.json (v0.81).

`tests/test_dowel.py` reproduces the project's connector off the «Stabdübel (Holz-Holz)» sheet cell by cell, and `tests/test_norms.py` compares SIA 265 Tabellen 8 and 9 with the workbook's own transcription on its «Daten» sheet. Both read the workbook until v0.81, which a clone of the code does not have -- the workbook is the project's, and the project left the repository -- so both were skipped wherever the code was not beside it. The values are frozen here instead, and read by both tests everywhere; `read()` is what froze them, and what a test on the engineer's own machine uses to say the workbook still holds them.
"""

import json
import shutil
import tempfile
import warnings
from pathlib import Path

FROZEN = Path(__file__).with_name("verbindung.json")

# «Stabdübel (Holz-Holz)»: the case and the results the Python calculation is held to.
#
# ⚠️ **Every input the test's own case restates is frozen**, and that is the rule this list is kept by rather than «the cells somebody thought mattered». It was not, until 20.09.2026: the force-grain angles C19/D19 were outside the set, the engineer entered 50.2° and 39.8° where the sheet had carried 0°, and nothing said so -- `test_the_workbook_still_holds_the_frozen_cells` passed, because every cell it watched was unchanged, while `test_the_workbook_s_holz_holz_sheet_is_the_project_s_connector_cell_by_cell` went red on a result. A frozen set that watches the answers and not all of the question reports the wrong test.
HOLZ_HOLZ_SHEET = "Stabdübel (Holz-Holz)"
HOLZ_HOLZ_INPUTS = ("C12", "C13", "C14", "C15", "C19", "D19", "C20", "D20", "C21", "D21", "C22", "D22",
                    "C23", "D23", "C24", "D24", "C29", "C30", "D30", "C31", "D31", "C32", "D32", "C36", "C39")
# k_red is one per member (C33, D33) and the calculation reads the smaller; the rest are the connection's.
HOLZ_HOLZ_RESULTS = ("C25", "D25", "C33", "D33", "C37", "C40", "C43", "C44", "C62")
HOLZ_HOLZ_CELLS = HOLZ_HOLZ_INPUTS + HOLZ_HOLZ_RESULTS

# «Daten»: one row per strength class, from row 3 to row 21, the grade's name in column A.
DATEN_SHEET = "Daten"
DATEN_ROWS = range(3, 22)
DATEN_COLUMNS = {
    "f_m_d": "B", "f_t_0_d": "C", "f_c_0_d": "D", "generell": "E",
    "mit_vorholz": "F", "endauflagerung": "G", "bracket": "H",
    "f_v_d": "I", "E_0_mean": "J", "rho_k": "K",
}


def read(book):
    """The cells above, read from the workbook at `book` -- through a copy, the engineer may have it open."""
    import openpyxl
    copy = Path(tempfile.mkdtemp()) / Path(book).name
    shutil.copy2(book, copy)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        workbook = openpyxl.load_workbook(copy, data_only=True, read_only=True)
        holz = workbook[HOLZ_HOLZ_SHEET]
        daten = workbook[DATEN_SHEET]
        holz_holz = {ref: holz[ref].value for ref in HOLZ_HOLZ_CELLS}
        grades = {}
        for row in DATEN_ROWS:
            name = daten["A%d" % row].value
            if name is None:
                continue
            grades[str(name)] = {key: daten["%s%d" % (column, row)].value for key, column in DATEN_COLUMNS.items()}
        workbook.close()
    shutil.rmtree(copy.parent, ignore_errors=True)
    return {"holz_holz": holz_holz, "daten": grades}


def frozen():
    """What verbindung.json holds: the cells as the workbook gave them the day they were frozen."""
    data = json.loads(FROZEN.read_text(encoding="utf-8"))
    return {"holz_holz": data["holz_holz"], "daten": data["daten"]}


def freeze(book, when):
    """Writes verbindung.json from the workbook at `book`. Deliberate, like build_examples.py --freeze: nothing calls it but a hand."""
    data = {"source": f"Verbindung.xlsm, read {when}", **read(book)}
    FROZEN.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return data
