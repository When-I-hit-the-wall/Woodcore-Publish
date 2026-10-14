"""The extremes of a design situation, and the combination that produced each (`calc/rfem_import/envelopes.py`).

The engineer asked for «l'effort maximal, et la combinaison de charge qui a calculé cet effort maximal». RFEM
has already answered it: its *result combination* tables — `SP1` ELU fondamental, `SP2` ELS rare, `SP3` ELS
fréquent, `SP4` ELS quasi-permanent — carry one column a combination's table has not, «Chargement
correspondant», naming the combination each row's extreme came from. So this is read and never enveloped here.

⚠️ **The trap this module exists for, and it is in the file rather than in the code:** one sheet holds **two
blocks of different widths**. `SP1 | Barres | Efforts internes` writes 1812 rows with a leading section column,
then a «Total» and a «max/min» trailer, then 770 more rows **without it**, every cell one to the left. Every
`CO` sheet does the same, 84 rows one way and 578 the other. Read at the header's indices, the second block's
criterion lands in the abscissa's field and its forces in each other's — and nothing says so.

👉 **The oracle is the file itself.** RFEM writes its own «Total» and «max/min» rows at the foot of each block,
so the envelope this reader builds can be checked against the numbers RFEM printed beside them. On the
engineer's own export it agrees to the digit — max M_y = **23.77363**, min = **−18.062302** — which are the
two numbers his own RFEM screenshot shows.
"""

import conftest
from rfem_import import envelopes
from rfem_import.csv_tables import table_from_rows

# One block's header, as RFEM writes a member-forces envelope: a leading section column, then the member, the
# node, the abscissa, the unnamed criterion, six forces, and the loading each row's extreme came from.
HEAD = [
    ["Section\nn°", "Barre", "Nœud", "Position", None, "Forces [kN]", None, None, "Moments [kNm]", None, None, None],
    [None, "n°", "n°", "x [m]", None, "N", "Vy", "Vz", "MT", "My", "Mz", "Chargement correspondant"],
]


def _table(rows, name="SP1 | Barres | Efforts internes"):
    return table_from_rows([list(row) for row in HEAD + rows], "test.xlsx[" + name + "]", name)


def _wide(member, node, x, criterion, forces, loading):
    """A row of the first block: with its section cell."""
    return ["1", member, node, x, criterion] + list(forces) + [loading]


def _narrow(member, node, x, criterion, forces, loading):
    """The same row as the second block writes it: one cell fewer, everything shifted left."""
    return [member, node, x, criterion] + list(forces) + [loading, None]


def test_an_envelope_is_the_table_that_names_its_loading():
    """The one language-independent way to tell a result combination's table from a combination's."""
    rows = [_wide(1, 1, 0, "My", [0, 0, 0, 0, 12.0, 0], "CO3")]
    assert envelopes.is_envelope(_table(rows))
    without = [row[:-1] + [None] for row in rows]
    head = [HEAD[0], HEAD[1][:-1] + [None]]
    bare = table_from_rows([list(r) for r in head + without], "t.xlsx[CO1]", "CO1 | Barres | Efforts internes")
    assert not envelopes.is_envelope(bare)


def test_the_criterion_names_the_column_the_row_is_extreme_in():
    """Which is what lets one reader take a force table, a deformation table and a reaction table."""
    rows = [
        _wide(1, 1, 0.0, "My", [1.0, 0, 2.0, 0, 12.0, 0], "CO3"),
        _wide(1, 1, 0.0, "My", [1.0, 0, 2.0, 0, -4.0, 0], "CO7"),
        _wide(1, 1, 0.0, "N", [9.0, 0, 2.0, 0, 3.0, 0], "CO5"),
    ]
    env = envelopes.envelope_of(_table(rows))
    assert env.of(1, "My")["max"].value == 12.0
    assert env.of(1, "My")["max"].loading == "CO3"
    assert env.of(1, "My")["min"].value == -4.0
    assert env.of(1, "My")["min"].loading == "CO7"
    assert env.of(1, "N")["max"].value == 9.0, "an N row is an extreme of N and not of My"


def test_a_second_block_of_another_width_is_read_at_its_own_offset():
    """The defect this module was written around: RFEM drops the section column partway down the sheet.

    Read at the header's indices, the narrow row's criterion «My» falls where the abscissa is read and its
    12.0 kNm falls in MT's field -- so the member would come out with no My at all and a torsion it has not.
    """
    rows = [
        _wide(1, 1, 0.0, "My", [0, 0, 0, 0, 5.0, 0], "CO1"),
        ["Total", None, None, None, None, 0, 0, 0, 0, 5.0, 0, None],
        _narrow(2, 4, 1.5, "My", [0, 0, 0, 0, 12.0, 0], "CO3"),
        _narrow(2, 4, 1.5, "My", [0, 0, 0, 0, -7.0, 0], "CO9"),
    ]
    env = envelopes.envelope_of(_table(rows))
    assert env.of(1, "My")["max"].value == 5.0, "the wide block still reads"
    assert env.of(2, "My")["max"].value == 12.0, "the narrow block is read at its own offset"
    assert env.of(2, "My")["min"].value == -7.0
    assert env.of(2, "My")["max"].loading == "CO3"
    assert env.of(2, "My")["max"].x == 1.5, "and its abscissa is the abscissa, not the criterion"


def test_a_column_wise_max_row_names_no_loading_and_is_left_out():
    """RFEM's deformation tables write `max` and `min` rows whose columns come from different combinations.

    They name no loading, so no report can cite them -- and a row nobody can cite is a row this reader does
    not keep. The per-quantity rows beside them are the ones read.
    """
    rows = [
        _wide(1, 1, 0.0, "max", [0, 0, 0, 0, 99.0, 0], None),
        _wide(1, 1, 0.0, "min", [0, 0, 0, 0, -99.0, 0], None),
        _wide(1, 1, 0.0, "My", [0, 0, 0, 0, 12.0, 0], "CO3"),
    ]
    env = envelopes.envelope_of(_table(rows))
    assert env.of(1, "My")["max"].value == 12.0, "99.0 came from a row naming no combination"
    assert env.read == 1 and env.skipped >= 2


def test_the_extreme_of_a_member_is_the_extreme_over_its_stations():
    """Taken across the rows rather than from the order they come in -- RFEM writes max then min, and reading
    that by position would be right today and silent the day it is not."""
    rows = [
        _wide(1, 1, 0.0, "My", [0, 0, 0, 0, 3.0, 0], "CO1"),
        _wide(1, 2, 2.0, "My", [0, 0, 0, 0, 17.0, 0], "CO4"),
        _wide(1, 3, 4.0, "My", [0, 0, 0, 0, 8.0, 0], "CO2"),
    ]
    env = envelopes.envelope_of(_table(rows))
    assert env.of(1, "My")["max"].value == 17.0
    assert env.of(1, "My")["max"].x == 2.0, "and it says where along the member it is"
    assert env.of(1, "My")["max"].loading == "CO4"


def test_the_concomitant_values_are_kept():
    """A bending-and-normal-force check reads the normal force acting **with** the moment, not the largest N."""
    rows = [_wide(1, 1, 0.0, "My", [-12.5, 0, 2.0, 0, 30.0, 0], "CO3")]
    env = envelopes.envelope_of(_table(rows))
    extreme = env.of(1, "My")["max"]
    assert extreme.concomitant["N"] == (-12.5, "kN")
    assert extreme.concomitant["Vz"] == (2.0, "kN")


def test_units_are_read_from_the_header_and_converted():
    """A model set to N and Nm exports N and Nm, and the reader hands on kN and kNm whatever it was set to."""
    head = [list(HEAD[0]), list(HEAD[1])]
    head[0][5], head[0][8] = "Forces [N]", "Moments [Nm]"
    rows = [_wide(1, 1, 0.0, "My", [2000.0, 0, 0, 0, 5000.0, 0], "CO1")]
    table = table_from_rows([list(r) for r in head + rows], "t.xlsx[SP1]", "SP1 | Barres | Efforts internes")
    env = envelopes.envelope_of(table)
    assert env.of(1, "My")["max"].value == 5.0, "5000 Nm is 5 kNm"
    assert env.of(1, "My")["max"].unit == "kNm"
    assert env.of(1, "My")["max"].concomitant["N"] == (2.0, "kN"), "2000 N is 2 kN"


def test_a_node_table_is_read_on_its_nodes():
    """A support-reaction envelope identifies its rows with a node and carries no member at all."""
    head = [
        ["Nœud\nn°", None, "Forces d'appui [kN]", None, None, "Moments d'appui [kNm]", None, None, None],
        [None, None, "Px", "Py", "Pz", "Mx", "My", "Mz", "Chargement correspondant"],
    ]
    rows = [["1", "Pz", 0.0, 0.0, 27.0, 0.0, 0.0, 0.0, "CO3"]]
    table = table_from_rows([list(r) for r in head + rows], "t.xlsx[SP1]", "SP1 | Nœuds | Forces d'appui")
    env = envelopes.envelope_of(table)
    assert env.on == "node"
    assert env.of(1, "Pz")["max"].value == 27.0
    assert env.of(1, "Pz")["max"].loading == "CO3"


def test_the_kind_of_a_table_is_read_from_its_content():
    """Forces, deformations and reactions are told apart by what identifies their rows and by their units --
    never by the sheet's own words, which are localised. The one word that is read is the axis system of a
    member deformation, which no column can say."""
    forces = _table([_wide(1, 1, 0.0, "My", [0, 0, 0, 0, 1.0, 0], "CO1")])
    assert envelopes.kind_of(forces, "SP1 | Barres | Efforts internes") == "forces"
    head = [
        ["Barre\nn°", "Nœud", "Position", None, "Déplacements [mm]", None, None, None],
        [None, "n°", "x [m]", None, "ux", "uy", "uz", "Chargement correspondant"],
    ]
    rows = [["1", 1, 0.0, "uz", 0.0, 0.0, 9.1, "CO36"]]
    local = table_from_rows([list(r) for r in head + rows], "t", "SP2 | Barres | Déformations loc")
    glob = table_from_rows([list(r) for r in head + rows], "t", "SP2 | Barres | Déformations glo")
    assert envelopes.kind_of(local, "SP2 | Barres | Déformations loc") == "deformations"
    assert envelopes.kind_of(glob, "SP2 | Barres | Déformations glo") == "deformations-global"


def test_a_design_situation_is_read_off_the_sheet_s_own_name():
    assert envelopes.situation_of("SP1 | Barres | Efforts internes")[0] == "SP1"
    assert envelopes.situation_of("SP12_analyse_statique.csv") == ("SP12", "SP", 12)
    assert envelopes.situation_of("Materiaux")[1] == ""


def test_the_engineers_own_export_reproduces_rfem_s_own_totals():
    """The end-to-end check, and the oracle is the file: RFEM writes «Total» and «max/min» rows at the foot of
    each block, and they are the two numbers his own screenshot of SP1 shows.

    max M_y = 23.77363 kNm, min = −18.062302 kNm, min N = −30.0975 kN, and V_z at ±22.48097.
    """
    project = conftest.real_project()
    export = conftest.real_rfem_export(project, "260929-01_29509-Model.xlsx")
    if not export.exists():
        raise conftest.Skip(f"the engineer's own RFEM export is not here ({export.name})")
    found, problems = envelopes.read_workbook_envelopes(export, situations=["SP1"])
    forces = found["SP1"]["forces"]
    assert not problems, f"the export read with problems: {[str(p) for p in problems]}"
    for quantity, (highest, lowest) in {
        "N": (0.95536, -30.0975),
        "Vz": (22.48097, -22.48097),
        "My": (23.77363, -18.062302),
    }.items():
        got_max = max(slot["max"].value for (_o, q), slot in forces.extremes.items() if q == quantity)
        got_min = min(slot["min"].value for (_o, q), slot in forces.extremes.items() if q == quantity)
        assert abs(got_max - highest) < 1e-4, f"{quantity} max: {got_max} against RFEM's own {highest}"
        assert abs(got_min - lowest) < 1e-4, f"{quantity} min: {got_min} against RFEM's own {lowest}"
    assert forces.of(2, "My")["min"].loading.startswith("CO"), "and each names the combination it came from"
