"""Reading a table RFEM exported as CSV (`calc/rfem_import/csv_tables.py`).

The reader was written against **580 real files** exported from the engineer's model and reads all 580 without one refusal, in 24 distinct column shapes. These tests hold the format facts that took that export to establish, on fixtures that reproduce it byte for byte (`tests/fixtures/rfem_csv.py`) rather than on his project data.

⚠️ **Two of them are regressions for defects the real files found**, and both were silent:

- `value("N")` returned the **node number** instead of the axial force. «Nœud n°» and «N» both folded to `n`, and the node column won by being first. A wrong force with no error anywhere is the worst thing this reader could do.
- The composite last column declared the unit **kNm**. RFEM's group row spans to the end of the line, so «Moments [kNm]» swept up the «Section (matériau) | Commentaire» column. Nothing in the header can tell that apart; the cells can, and now do.
"""

import conftest
from fixtures import rfem_csv, rfem_model
from rfem_import.csv_tables import RfemCsvError, fold, number, read_table, read_workbook

FORCES = ("N", "V_y", "V_z", "M_T", "M_y", "M_z")


def _folder(name):
    return conftest.tmpdir("rfem_csv_" + name)


# --- the format RFEM writes ------------------------------------------------------------------------


def test_the_shape_of_a_member_internal_forces_table():
    """Two header rows, twelve columns, the BOM and the CRLF absorbed, and the «Extrêmes» row not counted as data."""
    path = rfem_csv.member_internal_forces(_folder("shape") / "CO1_efforts.csv")
    table = read_table(path)
    assert table.delimiter == ";", f"RFEM writes semicolons, got {table.delimiter!r}"
    assert len(table.header) == 2, f"two header rows, got {len(table.header)}"
    assert len(table.columns) == 12, f"got {len(table.columns)}: {[c.full for c in table.columns]}"
    assert len(table.rows) == 4 and len(table.data_rows()) == 3, (
        f"{len(table.rows)} rows of which {len(table.data_rows())} numbered -- the «Extrêmes» row is not data"
    )
    assert table.columns[0].name.startswith("Barre"), "a BOM left in place would corrupt the first header cell"


def test_the_axial_force_is_not_the_node_number():
    """⚠️ The regression the real files found: «Nœud n°» and «N» both folded to `n`, so `value("N")` read the node number -- a wrong force, silently.

    The degree sign now folds to `o`, which also makes «n°» and the English «No.» one key.
    """
    path = rfem_csv.member_internal_forces(_folder("collision") / "CO1_efforts.csv")
    table = read_table(path)
    first = table.data_rows()[0]
    assert first.value("N") == -17.09, f"N came out as {first.value('N')} -- the node number is 1, the force is -17.09"
    assert table.unit("N") == "kN", f"got {table.unit('N')!r}"
    assert fold("n°") == "no" and fold("No.") == "no", "«n°» and «No.» must fold alike, and neither to «n»"
    assert fold("N") == "n"


def test_a_group_gives_its_unit_to_the_columns_it_spans():
    """«Forces [kN]» over N, V_y, V_z; «x [m]» carrying its own. The unit is read because it is the model's «Unités et décimales» setting, not a constant of RFEM."""
    table = read_table(rfem_csv.member_internal_forces(_folder("units") / "CO1_efforts.csv"))
    assert table.unit("x") == "m"
    for name in ("N", "V_y", "V_z"):
        assert table.unit(name) == "kN", f"{name} came out in {table.unit(name)!r}"
    for name in ("M_T", "M_y", "M_z"):
        assert table.unit(name) == "kNm", f"{name} came out in {table.unit(name)!r}"
    assert table.column("N").group == "Forces", f"the group keeps its name without its brackets, got {table.column('N').group!r}"


def test_the_composite_last_column_declares_no_unit():
    """⚠️ The second regression: RFEM's group row spans to the end of the line, so «Moments [kNm]» reached the section-and-comment column. A column with no number in it has no unit, whatever its header said."""
    table = read_table(rfem_csv.member_internal_forces(_folder("composite") / "CO1_efforts.csv"))
    last = table.columns[-1]
    assert last.unit is None, f"the composite column came out in {last.unit!r}"
    assert "Commentaire" in last.name or "Commentaire" in last.full


def test_a_column_with_no_header_is_kept():
    """The fifth column is headed by nothing and holds the criterion of an «Extrêmes» row. Dropping empty-header columns would have thrown that away."""
    table = read_table(rfem_csv.member_internal_forces(_folder("unnamed") / "CO1_efforts.csv"))
    assert table.columns[4].id == "col4", f"got {table.columns[4].id!r}"
    extreme = [row for row in table.rows if row.is_labelled][0]
    assert extreme.cells[4] == "N", "the unnamed column carries which quantity the extreme is of"


def test_an_extreme_row_is_told_apart_by_its_first_cell():
    """A row RFEM labelled instead of numbering. Reported rather than filtered, the decision being about results and not about CSV."""
    table = read_table(rfem_csv.member_internal_forces(_folder("extreme") / "CO1_efforts.csv"))
    labelled = [row for row in table.rows if row.is_labelled]
    assert len(labelled) == 1 and labelled[0].label == "Extrêmes", f"got {[r.label for r in labelled]}"
    assert all(not row.is_labelled for row in table.data_rows())


# --- the languages --------------------------------------------------------------------------------


def test_the_force_columns_read_the_same_in_three_languages():
    """What makes this reader possible: N, V_y, V_z, M_T, M_y, M_z are symbols, identical in French, German and English. Only the identifying columns are translated, and those take aliases."""
    for lang in ("fr", "de", "en"):
        table = read_table(rfem_csv.member_internal_forces(_folder("lang_" + lang) / "CO1.csv", lang=lang))
        first = table.data_rows()[0]
        assert first.value("N") == -17.09, f"{lang}: N came out as {first.value('N')}"
        assert table.unit("M_y") == "kNm", f"{lang}: M_y in {table.unit('M_y')!r}"
        assert all(table.column(name) is not None for name in FORCES), f"{lang}: missing one of {FORCES}"
        member = table.column("Barre n°", "Stab Nr.", "Member No.")
        assert member is not None and member.index == 0, f"{lang}: the member column was not found by its aliases"


def test_a_header_no_alias_names_is_refused_by_name():
    """An unrecognised language must say which header to add, not fail further down with a wrong number."""
    table = read_table(rfem_csv.member_internal_forces(_folder("require") / "CO1.csv", lang="de"))
    try:
        table.require("Barre n°")
    except RfemCsvError as error:
        assert "Stab Nr" in str(error), f"the message must show what the file holds: {error}"
    else:
        raise AssertionError("require() must refuse a header no alias names")


# --- a model table --------------------------------------------------------------------------------


def test_a_model_table_has_one_header_row_and_a_clean_comment():
    """The node and member tables are where metadata is read: a single header row and a `comment` column of its own, unlike the composite column of a result table."""
    path = rfem_csv.nodes(_folder("nodes") / "noeuds.csv", comment='@model "VU-gunstig"')
    table = read_table(path)
    assert len(table.header) == 1, f"got {len(table.header)} header rows"
    assert table.unit("X") == "m"
    row = table.data_rows()[0]
    assert row.get("Commentaire") == '@model "VU-gunstig"'
    assert row.value("Z") == -2.95


# --- numbers --------------------------------------------------------------------------------------


def test_a_unit_written_as_a_dash_is_no_unit():
    """RFEM writes «[--]» for a dimensionless quantity -- nine columns of one export did."""
    table = read_table(rfem_csv.dimensionless(_folder("dimensionless") / "ratios.csv"))
    assert table.columns[1].unit is None, f"got {table.columns[1].unit!r}"
    assert table.data_rows()[0].value("Rapport") == 0.783


def test_a_thousands_separator_and_a_decimal_comma_are_read():
    """Defensive rather than observed, and written down as such: no sample of the engineer's export reaches four digits, so the reader must not depend on his machine's spelling."""
    table = read_table(rfem_csv.grouped_numbers(_folder("grouped") / "grands.csv"))
    first, second = table.data_rows()
    assert first.value("N") == 1234.56, f"«1'234.56» came out as {first.value('N')}"
    assert first.value("M") == 1234.56, f"«1 234,56» came out as {first.value('M')}"
    assert second.value("N") == -2000.0 and second.value("M") == -2.5


def test_number_reads_both_orders_of_separator():
    assert number("1.234,56") == 1234.56, "the last separator is the decimal one"
    assert number("1,234.56") == 1234.56
    assert number("-17.09") == -17.09
    assert number("0") == 0.0
    for nothing in ("", "   ", None, "L | C | M", "Extrêmes", "--"):
        assert number(nothing) is None, f"{nothing!r} is not a number"


def test_a_comma_separated_file_is_sniffed():
    """A machine whose list separator is a comma writes commas. The delimiter is sniffed rather than assumed, or such a file would come back as one column."""
    table = read_table(rfem_csv.comma_separated(_folder("comma") / "virgules.csv"))
    assert table.delimiter == ",", f"got {table.delimiter!r}"
    assert len(table.columns) == 2 and table.data_rows()[0].value("N") == -17.09


# --- what is refused ------------------------------------------------------------------------------


def test_a_summary_file_is_read_and_the_caller_is_what_refuses_it():
    """⚠️ RFEM's `*_résumé.csv` is a list of statements, not a table of objects -- and `read_table` reads it anyway, deliberately.

    A rule was tried and dropped: «a table whose first column is empty in every row is not a table of objects» refuses all 57 `résumé` files of the engineer's export, and also refuses `timber_design_non_valide-désactivé.csv`, a real table that merely opens with a blank column. One false refusal in 580 is worse than none, because it drops a table in silence.

    So the guard lives at the point of use: a caller names the columns it needs and gets a refusal naming what the file holds. That is what this test pins.
    """
    path = rfem_csv.summary(_folder("summary") / "CO1_résumé.csv")
    table = read_table(path)          # read, not refused
    assert table.column("N") is None, "a résumé carries no force column"
    try:
        table.require("Barre n°", "Stab Nr.", "Member No.")
    except RfemCsvError as error:
        assert "Description" in str(error) or "Valeur" in str(error), (
            f"the refusal must show what the file actually holds: {error}"
        )
    else:
        raise AssertionError("require() must refuse a résumé asked for a member column")


def test_a_table_of_no_rows_is_a_table():
    """⚠️ The regression the engineer's own model found: it carries **no surface**, so RFEM exports its surface table as a header row and nothing else -- and that was refused, «2 header row(s) and no data».

    Two things were wrong at once. `_headers` counted two header rows in a file of one, no row carrying a number for it to stop at. And an empty body was refused, which made «the model has no surfaces» and «this export is broken» one exception a caller cannot tell apart -- it stopped the structure detection of every model built out of members alone.
    """
    table = read_table(rfem_csv.headers_only(_folder("no_rows") / "surfaces.csv"))
    assert len(table.header) == 1, f"one header row in a file of one, got {len(table.header)}"
    assert len(table.columns) == 4, f"got {[c.name for c in table.columns]}"
    assert table.rows == [] and table.data_rows() == []
    assert table.column("Surface n°") is not None, "its columns are readable, which is what says the table is empty and not broken"


def test_a_workbook_reads_a_sheet_only_when_it_is_asked_for():
    """⚠️ **The difference between one second and forty-five.** A full export of this project is **490 to 609 sheets and 14 MB**, nearly all of it results, and the model reader wants nineteen of them — measured: opening the book 1.48 s, reading those nineteen 0.07 s, and they are **36 kB of a 13.3 MB file**. Reading every sheet eagerly cost 43 s a workbook to use 4 % of it."""
    folder = _folder("lazy")
    book = rfem_model.workbook(folder / "modele.xlsx")
    workbook = read_workbook(book)
    try:
        assert len(workbook) > 5 and repr(workbook).endswith("0 read)"), f"got {workbook!r}"
        assert workbook.sheet("Barres") == "Barres", "a sheet is resolved by name without being read"
        assert repr(workbook).endswith("0 read)"), f"resolving a name must read nothing: {workbook!r}"
        table = workbook.table("Barres")
        assert table is not None and repr(workbook).endswith("1 read)"), f"got {workbook!r}"
        assert workbook.table("Barres") is table, "a sheet read once is kept"
    finally:
        workbook.close()


def test_an_empty_file_is_refused_by_name():
    path = rfem_csv.empty(_folder("empty") / "vide.csv")
    try:
        read_table(path)
    except RfemCsvError as error:
        assert "vide.csv" in str(error), f"the refusal must name the file, an import pointing at hundreds: {error}"
    else:
        raise AssertionError("an empty file must be refused")


# --- the shape of what comes back -----------------------------------------------------------------


def test_a_row_reads_by_name_by_alias_and_by_index():
    table = read_table(rfem_csv.member_internal_forces(_folder("access") / "CO1.csv"))
    row = table.data_rows()[0]
    assert row["N"] == "-17.09" and row[5] == "-17.09"
    assert row.get("pas une colonne") is None
    assert row.get("pas une colonne", default="?") == "?"
    assert row.value("N") == -17.09


def test_a_hyphen_in_a_header_is_never_a_word_boundary():
    """⚠️ The regression `DE.xlsx` and `EN.xlsx` found: RFEM uses a hyphen two ways in a header and neither parts two words.

    As a **hyphenation**, breaking one word across its own cell or across the two header rows — «Last-\\nkombin.» is «Lastkombin.», and «Last-» over «richtung» is «Lastrichtung». And as a **joiner** inside one term — «Cross-Section», «Stablast-Parameter». Read as a separator, the German combination identifier and the German load direction matched no alias, **silently**: 48 combinations came back as none.
    """
    assert fold("Last-\nkombin.") == fold("Lastkombin.") == "lastkombin"
    assert fold("Last-richtung") == fold("Lastrichtung") == "lastrichtung"
    assert fold("Cross-Section Name") == fold("Cross-Section Name") == "crosssection_name"
    assert fold("Barre n°") == "barre_no", "what was already right must stay right"
    assert fold("Quersch.\nNr.") == "quersch_nr"


def test_a_group_broken_at_a_hyphen_joins_its_name_with_no_space():
    """The other half of the same fact: RFEM breaks a long header **across its two header rows**, «Last-» on the group row and «richtung» on the name row, which is one word (`DE.xlsx`, member loads)."""
    path = _folder("hyphen") / "charges.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        (rfem_csv.BOM
         + rfem_csv.SEP.join(["Nr.", "", "Last-", ""]) + rfem_csv.EOL
         + rfem_csv.SEP.join(["", "Zugewiesen an Stäbe Nr.", "richtung", "p [kN/m]"]) + rfem_csv.EOL
         + rfem_csv.SEP.join(["1", "2-4", "ZL", "1.1"]) + rfem_csv.EOL).encode("utf-8")
    )
    table = read_table(path)
    direction = table.column("Lastrichtung")
    assert direction is not None, f"got {[c.full for c in table.columns]}"
    assert direction.index == 2 and direction.full == "Last-richtung"
    assert table.column("Forces N") is None, "a group that does not end in a hyphen still joins with a space"


def test_fold_compares_headers_across_spellings():
    assert fold("Barre n°") == fold("barre  N° ") == "barre_no"
    assert fold("Nœud") == "noeud", "a ligature must fold to its letters"
    assert fold("Kräfte") == "krafte"
    assert fold(None) == "" and fold("") == ""
