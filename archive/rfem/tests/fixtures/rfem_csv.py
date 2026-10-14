"""Minimal CSV files in the shape RFEM 6.15 exports, written for the tests.

The reader was built against **580 real files** exported from the engineer's own model, and these fixtures reproduce their format to the byte: the BOM, the semicolons, the CRLF, the two header rows with their spanning group names, the units in brackets, the unnamed criterion column, the interleaved «Extrêmes» rows and the composite last column. Every oddity here was observed, not invented -- the docstring of `calc/rfem_import/csv_tables.py` says where each came from.

A test writes its own file rather than pointing at the engineer's export, for the reason `tests/fixtures/workbook.py` already gives: his files are project data, they are not in the repository, and a defect has to be *put into* a file to check that the reader reports it -- which nothing here may do to his model.
"""

# RFEM writes UTF-8 with a BOM, semicolons and CRLF. Written out rather than left to `csv`, so that a test reads exactly the bytes RFEM produces.
BOM = "﻿"
SEP = ";"
EOL = "\r\n"


def _write(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = BOM + EOL.join(lines) + EOL
    path.write_bytes(text.encode("utf-8"))
    return path


# The member internal forces table, in the three languages RFEM's UI offers this project. The force and moment columns are *symbols* and identical in all three -- which is what makes the reader's job possible; only the identifying columns are translated.
HEADERS = {
    "fr": (
        ["Barre n°", "Nœud", "Position", "", "", "Forces [kN]", "", "", "Moments [kNm]", "", "", ""],
        ["", "n°", "x [m]", "Marqueurs", "", "N", "V_y", "V_z", "M_T", "M_y", "M_z",
         "Section (matériau) | Commentaire sur la barre"],
    ),
    "de": (
        ["Stab Nr.", "Knoten", "Stelle", "", "", "Kräfte [kN]", "", "", "Momente [kNm]", "", "", ""],
        ["", "Nr.", "x [m]", "Markierungen", "", "N", "V_y", "V_z", "M_T", "M_y", "M_z",
         "Querschnitt (Material) | Kommentar am Stab"],
    ),
    "en": (
        ["Member No.", "Node", "Location", "", "", "Forces [kN]", "", "", "Moments [kNm]", "", "", ""],
        ["", "No.", "x [m]", "Markers", "", "N", "V_y", "V_z", "M_T", "M_y", "M_z",
         "Section (Material) | Comment on Member"],
    ),
}

SPECIFICATION = "Poutre | 1 - R_M1 500/200 | 6 - C24 | L : 2.950 m"


def member_internal_forces(path, lang="fr", extreme_label="Extrêmes", comment=None):
    """The member internal forces of one combination: three numbered rows of member 1 and one «Extrêmes» row.

    `comment` appends a member comment to the composite last column, as RFEM does -- which is exactly why that column is not where a comment should be read.
    """
    top, names = HEADERS[lang]
    spec = SPECIFICATION + (f" | {comment}" if comment else "")
    rows = [
        ["1", "1", "0.0000000000000000", "L | C | M", "", "-17.09", "0.00", "0.00", "0.00", "0.00", "0.00", spec],
        ["1", "", "0.4214285714285714", "R", "", "-16.81", "0.00", "0.00", "0.00", "0.00", "0.00", spec],
        ["1", "2", "2.9500000000000002", "L | M", "", "-15.10", "0.00", "0.00", "0.00", "0.00", "0.00", spec],
        [extreme_label, "2", "2.9500000000000002", "L | M", "N", "-15.10", "0.00", "0.00", "0.00", "0.00", "0.00", spec],
    ]
    return _write(path, [SEP.join(top), SEP.join(names)] + [SEP.join(row) for row in rows])


def nodes(path, comment=""):
    """A model table with one header row only and a clean `comment` column -- the shape a node or member table takes, and where metadata is actually read."""
    return _write(path, [
        SEP.join(["Nœud n°", "X [m]", "Z [m]", "Commentaire"]),
        SEP.join(["36", "3.500", "-2.950", comment.replace("\n", "\\n")]),
        SEP.join(["40", "7.000", "-2.950", ""]),
    ])


def dimensionless(path):
    """A table whose unit RFEM writes «[--]» -- nine columns of one export did."""
    return _write(path, [
        SEP.join(["Barre n°", "Rapport [--]"]),
        SEP.join(["24", "0.783"]),
    ])


def grouped_numbers(path):
    """A table whose numbers carry a thousands separator and a decimal comma. Defensive: no sample of the engineer's own export reaches four digits, so the reader accepts both spellings rather than assuming his."""
    return _write(path, [
        SEP.join(["Barre n°", "N [kN]", "M [kNm]"]),
        SEP.join(["24", "1'234.56", "1 234,56"]),
        SEP.join(["25", "-2'000.00", "-2.5"]),
    ])


def comma_separated(path):
    """The same table as a machine with a comma list separator writes it: `,` between fields and `.` inside numbers."""
    return _write(path, [
        ",".join(["Barre n°", "N [kN]"]),
        ",".join(["24", "-17.09"]),
        ",".join(["25", "-16.81"]),
    ])


def summary(path):
    """RFEM's `*_résumé.csv`: statements and section titles, not a table of objects. `read_table` must refuse it rather than return rows that are half headings."""
    return _write(path, [
        SEP.join(["", "", "", "", ""]),
        SEP.join(["", "Description", "Valeur", "Unité", "Notes"]),
        SEP.join(["", "Somme des charges et somme des forces d'appui", "", "", ""]),
        SEP.join(["", "Somme des charges en Z", "247.95", "kN", ""]),
    ])


def empty(path):
    return _write(path, [])


def headers_only(path):
    """A table of no rows: the header and nothing under it.

    What RFEM exports for an object type the model has none of -- this project's surface table, the model being built of members alone. It is a table, and reading it is what lets «the model has no surfaces» be told from «this export is broken».
    """
    return _write(path, [
        SEP.join(["Surface n°", "Lignes de contour", "Épaisseur", "Commentaire"]),
    ])


# --- the full per-member structure, as RFEM really writes it ---------------------------------------

# Established on the engineer's export: after each member's distribution RFEM writes an «Extrêmes»
# section, then a «Total» row, then a row carrying **the member's number and no x** -- the member's own
# summary -- then a blank line before the next member. The file ends on a «max/min» row.
def member_forces_block(path, lang="fr", extreme_label="Extrêmes", total_label="Total", minmax_label="max/min"):
    """Two members with their distribution, extremes, «Total», per-member summary and a trailing «max/min».

    Counts: 5 stations, 2 extreme rows, 2 member summaries, 3 trailers -- so a test can assert that
    every row of the file was classified.
    """
    top, names = HEADERS[lang]
    spec = SPECIFICATION
    rows = [
        ["1", "1", "0.000", "L | C | M", "", "-17.09", "0.00", "0.00", "0.00", "0.00", "0.00", spec],
        ["1", "", "1.475", "R", "", "-16.10", "0.00", "0.00", "0.00", "0.00", "0.00", spec],
        ["1", "2", "2.950", "L | M", "", "-15.10", "0.00", "0.00", "0.00", "0.00", "0.00", spec],
        [extreme_label, "2", "2.950", "L | M", "N", "-15.10", "0.00", "0.00", "0.00", "0.00", "0.00", spec],
        ["1", "1", "0.000", "L | C | M", "V_y", "-17.09", "0.00", "0.00", "0.00", "0.00", "0.00", spec],
        [total_label, "", "", "", "", "-15.10", "0.00", "0.00", "0.00", "0.00", "0.00", spec],
        ["1", "", "", "", "", "-17.09", "0.00", "0.00", "0.00", "0.00", "0.00", spec],
        ["", "", "", "", "", "", "", "", "", "", "", ""],
        ["2", "14", "0.000", "L | M", "", "0.00", "0.00", "-0.41", "0.00", "0.00", "0.00", spec],
        ["2", "", "1.500", "R", "", "-1.20", "0.00", "2.30", "0.00", "4.75", "0.00", spec],
        [total_label, "", "", "", "", "0.00", "0.00", "2.30", "0.00", "4.75", "0.00", spec],
        ["2", "", "", "", "", "-1.20", "0.00", "-0.41", "0.00", "0.00", "0.00", spec],
        [minmax_label, "", "", "", "", "-19.37", "0.00", "0.00", "0.00", "0.00", "0.00", spec],
    ]
    return _write(path, [SEP.join(top), SEP.join(names)] + [SEP.join(row) for row in rows])


def member_forces_no_markers(path):
    """The same table without a markers column, so the criterion column moves from index 4 to index 3.

    RFEM's 24 column shapes put it at 4 in 57 tables and at 5 in 57 others; this is what proves the
    reader finds it by content and not by a fixed index.
    """
    top = ["Barre n°", "Nœud", "Position", "", "Forces [kN]", "", "", "Moments [kNm]", "", ""]
    names = ["", "n°", "x [m]", "", "N", "V_y", "V_z", "M_T", "M_y", "M_z"]
    rows = [
        ["1", "1", "0.000", "", "-17.09", "0.00", "0.00", "0.00", "0.00", "0.00"],
        ["1", "2", "2.950", "", "-15.10", "0.00", "0.00", "0.00", "0.00", "0.00"],
        ["1", "1", "0.000", "N", "-17.09", "0.00", "0.00", "0.00", "0.00", "0.00"],
    ]
    return _write(path, [SEP.join(top), SEP.join(names)] + [SEP.join(r) for r in rows])


def member_forces_units(path, force="N", moment="Nm", length="mm"):
    """The same two stations with the units a differently configured model writes.

    «Unités et décimales» is a property of the model, so the reader must convert rather than assume kN.
    """
    top = ["Barre n°", "Position", f"Forces [{force}]", "", "", f"Moments [{moment}]", "", ""]
    names = ["", f"x [{length}]", "N", "V_y", "V_z", "M_T", "M_y", "M_z"]
    rows = [
        ["1", "0", "-17090", "0", "0", "0", "0", "0"],
        ["1", "2950", "-15100", "0", "0", "0", "4750", "0"],
    ]
    return _write(path, [SEP.join(top), SEP.join(names)] + [SEP.join(r) for r in rows])
