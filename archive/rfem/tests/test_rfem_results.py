"""The Schnittgrössen an RFEM export carries (`calc/rfem_import/results.py`).

Written against the engineer's own export -- 580 files, of which **173 are member-forces tables** across 59 loadings -- and every count here was measured on it before it was asserted on a fixture.

⚠️ **Two regressions, both of which put wrong data in with no error anywhere:**

- **A member's summary row was read as a station.** After each member's extremes RFEM writes a «Total» row and then a row carrying *the member's number and no x at all*. It has a numeric member number and an empty criterion, so only the missing station tells it apart -- and taken for a station it put a phantom point on all 62 members, at x = None, carrying that member's extreme value.
- **The criterion column cannot be read at a fixed index.** It is unnamed, and over the 24 column shapes of one export it sits at index 4 in 57 tables and at index 5 in 57 others, while index 4 is the *markers* column («R», «L | M») in some shapes. Read by index, markers would have been taken for criteria and two thirds of the rows misclassified.

**The test that catches both at once** is the accounting: `len(stations) + extremes + summaries + trailers` must equal every row the file held. It balanced on all 173 real tables, and it is what a fixture asserts here.
"""

import conftest
from fixtures import rfem_csv
from rfem_import import results
from rfem_import.results import FORCES, read_member_forces, read_results


def _folder(name):
    return conftest.tmpdir("rfem_results_" + name)


# --- recognising a table --------------------------------------------------------------------------


def test_a_member_forces_table_is_recognised_by_its_six_symbols():
    """The filenames are localised; N, V_y, V_z, M_T, M_y, M_z are not. 173 of the engineer's 580 files answer to this."""
    table = read_member_forces(rfem_csv.member_forces_block(_folder("recognise") / "CO1_efforts.csv"))
    assert table is not None
    assert read_member_forces(rfem_csv.nodes(_folder("recognise") / "noeuds.csv")) is None, (
        "a node table carries no forces and must not be read as one"
    )
    assert read_member_forces(rfem_csv.summary(_folder("recognise") / "CO1_résumé.csv")) is None


def test_the_loading_is_read_from_the_filename():
    """RFEM names the file after the loading. Its letters are RFEM's own localised abbreviation -- «CC» is «cas de charge» in this French installation -- so they are carried as a label and never interpreted."""
    assert results.loading_of("CO12_analyse_statique_barres_efforts_internes.csv") == ("CO12", "CO", 12)
    assert results.loading_of("CC1_x.csv") == ("CC1", "CC", 1)
    assert results.loading_of("SP3_x.csv") == ("SP3", "SP", 3)
    stem, kind, num = results.loading_of("timber_design_efforts_internes.csv")
    assert kind == "" and num is None and stem.startswith("timber"), f"got {(stem, kind, num)}"


# --- the accounting, which is what catches a misread row -------------------------------------------


def test_every_row_of_the_file_is_accounted_for():
    """⚠️ The test that found both regressions. A row this reader does not classify is a row it either loses or invents."""
    table = read_member_forces(rfem_csv.member_forces_block(_folder("accounting") / "CO1.csv"))
    assert len(table.stations) == 5, f"5 distribution rows, got {len(table.stations)}"
    assert table.extremes == 2, f"2 extreme rows, got {table.extremes}"
    assert table.summaries == 2, f"one summary per member, got {table.summaries}"
    assert table.trailers == 3, f"«Total» twice and «max/min» once, got {table.trailers}"
    assert table.rows_accounted == 12, f"the file holds 12 non-empty rows after its two headers, classified {table.rows_accounted}"


def test_a_member_summary_row_is_not_a_station():
    """⚠️ The first regression: the row carrying a member's number and no x is that member's own summary, and it put a phantom station at x = None on every member."""
    table = read_member_forces(rfem_csv.member_forces_block(_folder("summary_row") / "CO1.csv"))
    assert all(station.x is not None for station in table.stations), (
        f"{sum(1 for s in table.stations if s.x is None)} station(s) came out with no x -- those are member summaries"
    )
    assert table.summaries == 2
    assert len(table.by_member()[1]) == 3, f"member 1 has three stations, got {len(table.by_member()[1])}"


def test_an_extreme_row_is_not_a_station():
    """Every extreme repeats a value the distribution already carries, so leaving them out loses nothing -- and `governing()` recomputes the same answer where it can be traced."""
    table = read_member_forces(rfem_csv.member_forces_block(_folder("extremes") / "CO1.csv"))
    member_one = table.by_member()[1]
    assert [round(s.x, 3) for s in member_one] == [0.0, 1.475, 2.95], f"got {[s.x for s in member_one]}"
    assert table.extremes == 2


def test_the_criterion_column_is_found_by_content_not_by_index():
    """⚠️ The second regression. With a markers column it sits at index 4; without one it moves to 3. Read by index, «R» and «L | M» would have been taken for criteria."""
    with_markers = read_member_forces(rfem_csv.member_forces_block(_folder("crit_4") / "CO1.csv"))
    assert with_markers.extremes == 2

    from rfem_import.csv_tables import read_table
    from rfem_import.results import criterion_column
    table = read_table(rfem_csv.member_forces_block(_folder("crit_4b") / "CO1.csv"))
    column = criterion_column(table)
    assert column is not None and column.index == 4, f"got {column}"

    moved = read_table(rfem_csv.member_forces_no_markers(_folder("crit_3") / "b.csv"))
    column = criterion_column(moved)
    assert column is not None and column.index == 3, f"without a markers column the criterion moves, got {column}"
    assert read_member_forces(rfem_csv.member_forces_no_markers(_folder("crit_3b") / "b.csv")).extremes == 1


def test_a_table_with_no_extremes_has_no_criterion_column():
    """59 of the engineer's 173 tables have none -- `criterion_column` must then return None rather than settle on some other column."""
    from rfem_import.csv_tables import read_table
    from rfem_import.results import criterion_column
    table = read_table(rfem_csv.member_internal_forces(_folder("no_crit") / "CO1.csv"))
    # the fixture's only criterion cell is on its «Extrêmes» row
    assert criterion_column(table) is not None
    plain = read_table(rfem_csv.member_forces_units(_folder("no_crit2") / "u.csv"))
    assert criterion_column(plain) is None, "a table with no criterion cell at all has no criterion column"


# --- units ----------------------------------------------------------------------------------------


def test_the_forces_come_back_in_kilonewtons_whatever_the_model_was_set_to():
    """«Unités et décimales» is a property of the model, so a table in N and Nm must be converted, not assumed.

    ⚠️ **This test asserted 0.00475 kNm for 4750 Nm until v0.99**, which is a thousand too small -- and it
    passed, because `MOMENT_UNITS` carried the same error: «nm» was 1e-6 where a newton-metre is a thousandth
    of a kilonewton-metre, and «nmm» 1e-9 where a newton-millimetre is a millionth. The constant and the test
    agreed with each other and with nothing else. Nothing showed it, since the engineer's own model states kNm
    and the only factor ever used was 1.0; a model set to Nm would have had every moment read a thousand times
    too small, on the page and in the report.
    """
    table = read_member_forces(rfem_csv.member_forces_units(_folder("units") / "CO1.csv"))
    assert not table.problems, f"got {[str(p) for p in table.problems]}"
    first, second = table.stations
    assert round(first["N"], 3) == -17.09, f"-17090 N should read -17.09 kN, got {first['N']}"
    assert round(second["M_y"], 6) == 4.75, f"4750 Nm should read 4.75 kNm, got {second['M_y']}"
    assert round(second.x, 3) == 2.95, f"2950 mm should read 2.95 m, got {second.x}"
    assert table.units["N"] == "N" and table.units["x"] == "mm", "the unit the file declared is recorded"


def test_kn_and_knm_pass_through_unchanged():
    table = read_member_forces(rfem_csv.member_forces_block(_folder("kn") / "CO1.csv"))
    assert table.stations[0]["N"] == -17.09
    assert results.FORCE_UNIT == "kN" and results.MOMENT_UNIT == "kNm"


def test_a_unit_the_reader_does_not_know_is_reported_and_the_force_left_out():
    """A force taken for kN when it is something else is a wrong number on a page. It is left out and named instead."""
    table = read_member_forces(rfem_csv.member_forces_units(_folder("badunit") / "CO1.csv", force="Zork"))
    codes = [p.code for p in table.problems]
    assert "rfem_results_unit" in codes, f"got {codes}"
    assert "Zork" in " ".join(str(p) for p in table.problems)
    assert all("N" not in station.forces for station in table.stations), (
        "a force whose unit could not be read must not reach a station"
    )
    assert any("M_y" in station.forces for station in table.stations), "the moments are still readable"


def test_a_dotted_moment_unit_is_the_same_as_an_undotted_one():
    """RFEM writes «kN.m/m» in some tables and «kNm» in others; the unit is folded before it is looked up."""
    table = read_member_forces(rfem_csv.member_forces_units(_folder("dotted") / "CO1.csv", moment="kN.m"))
    assert not [p for p in table.problems if p.code == "rfem_results_unit"], f"got {[str(p) for p in table.problems]}"
    assert table.stations[1]["M_y"] == 4750.0, "kN.m is kNm, so 4750 stays 4750"


# --- what a caller asks of a table ----------------------------------------------------------------


def test_the_stations_of_a_member_come_in_order_along_it():
    table = read_member_forces(rfem_csv.member_forces_block(_folder("order") / "CO1.csv"))
    for member, stations in table.by_member().items():
        xs = [s.x for s in stations]
        assert xs == sorted(xs), f"member {member} came out as {xs}"
    assert table.members == [1, 2]


def test_governing_is_computed_from_the_distribution():
    """Not read from RFEM's «Extrêmes» rows: a value the report prints must be traceable to a station the report also carries."""
    table = read_member_forces(rfem_csv.member_forces_block(_folder("governing") / "CO1.csv"))
    largest, smallest = table.governing("N", member=1)
    assert smallest["N"] == -17.09 and round(smallest.x, 3) == 0.0
    assert largest["N"] == -15.10 and round(largest.x, 3) == 2.95
    largest, smallest = table.governing("M_y")
    assert largest["M_y"] == 4.75 and largest.member == 2, f"got {largest}"
    assert table.governing("N", member=999) == (None, None), "a member the table has not gives no station"


def test_a_station_carries_its_node_and_its_markers():
    table = read_member_forces(rfem_csv.member_forces_block(_folder("station") / "CO1.csv"))
    first = table.by_member()[1][0]
    assert first.node == 1 and first.markers == "L | C | M"
    assert first.member == 1 and first.n == -17.09
    middle = table.by_member()[1][1]
    assert middle.node is None, "RFEM writes a node number only at a member's ends"


def test_every_force_is_present_on_a_station():
    table = read_member_forces(rfem_csv.member_forces_block(_folder("six") / "CO1.csv"))
    for station in table.stations:
        assert set(station.forces) == set(FORCES), f"got {sorted(station.forces)}"


# --- a whole folder -------------------------------------------------------------------------------


def test_a_folder_gives_its_loadings_and_counts_what_it_skipped():
    """An RFEM export holds hundreds of tables of other kinds -- deformations, support forces, design ratios. They are counted, not named one by one, or the count of what matters would be buried."""
    folder = _folder("folder")
    rfem_csv.member_forces_block(folder / "CO1_efforts.csv")
    rfem_csv.member_forces_block(folder / "CO2_efforts.csv")
    rfem_csv.nodes(folder / "CO1_noeuds.csv")
    rfem_csv.summary(folder / "CO1_résumé.csv")
    read = read_results(folder)
    assert read.loadings == ["CO1", "CO2"], f"got {read.loadings}"
    assert len(read.tables) == 2 and read.skipped == 2, f"{len(read.tables)} tables, {read.skipped} skipped"
    assert read.base("CO1") is not None and len(read.base("CO1")) == 5
    assert read.base("CO9") is None, "a loading the folder has not gives no table"


def test_the_fullest_table_of_a_loading_is_the_base_one():
    """A loading has several tables -- the distribution and variants grouped by section or member set. Which is the base one is decided by content (most stations), not by a localised filename."""
    folder = _folder("base")
    rfem_csv.member_forces_block(folder / "CO1_efforts.csv")            # 5 stations
    rfem_csv.member_forces_no_markers(folder / "CO1_efforts_par_section.csv")   # 2 stations
    read = read_results(folder)
    assert len(read.of("CO1")) == 2, "both tables belong to CO1"
    assert len(read.base("CO1")) == 5, f"the base table is the fullest, got {len(read.base('CO1'))}"


def test_three_languages_read_alike():
    """Only the identifying columns are translated; the six forces are symbols. A German export must give the same numbers."""
    tables = {}
    for lang in ("fr", "de", "en"):
        folder = _folder("lang_" + lang)
        tables[lang] = read_member_forces(rfem_csv.member_forces_block(folder / "CO1.csv", lang=lang))
    for lang, table in tables.items():
        assert len(table.stations) == 5, f"{lang}: {len(table.stations)} stations"
        assert table.summaries == 2 and table.extremes == 2, f"{lang}: {table.summaries}/{table.extremes}"
        assert table.stations[0]["N"] == -17.09, f"{lang}: N came out {table.stations[0]['N']}"
        assert table.members == [1, 2]
