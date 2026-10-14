"""The model an RFEM table export holds (`calc/rfem_import/model_tables.py`).

Written against an authentic export — `Musterprojekt/01_29509-Model.xlsx`, RFEM 6.15's own *Fichier → Exporter → Tableaux* — and every count here was measured on it before it was asserted on a fixture. What it reads of his model, with **no problem reported**: 62 members over 91 nodes, 9 sections, 4 materials, 5 nodal supports, 2 member hinges, 5 load cases, 48 combinations, 162 loads; and through `Model.items()` into `structure_detection`, the same 22 structures the API route finds, in one second.

⚠️ **Three traps of the format, each of which loses data in silence, and each held here:**

- **A number RFEM lists is not always an object.** A deleted object leaves an empty row carrying its number: 97 node rows for 91 nodes (3, 4, 6, 10, 16, 56 gone), 64 member rows for 62 members (11, 12 gone). Counted in `skipped`, not reported one by one.
- **A list of object numbers carries ranges.** «2-4» on a load, «1,2,5,8-10,13,14,17-19» on a section. Read without expanding them, a load on three members acts on none.
- **A load case's identifier is «CC1», not a number** — and `Table.data_rows()`, which drops a row whose first cell is not a number, is a *results* notion («Extrêmes»). It dropped every row of the load case and the combination tables, so the model came back with **no loading at all**: no case, no combination, no load, and no problem reported either. This module reads `table.rows` and checks each identifier itself.

⚠️ **And one reading that is exactly inverted between two tables**: on a support «inf» means held, on a hinge it means *not released* — RFEM's hinge columns are «Libération/ressort de…». Read as a support, this model's hinge 1 (Cφ,y = 0, a moment release) and hinge 2 (Cφ,y = 21.672 kNm/rad, a rotational spring) both came out «pinned». A `Restraint` therefore carries the role it was read under.

👉 **The German and the English are the aliases and not an export.** This office's RFEM is French, so only the French is read off a real file; the other two are `SHEETS` and `COLUMNS`' own claims, and a test in them tests the aliases. An export in those languages is what would settle them (docs/open-questions.md §14).
"""

import math

import conftest
from fixtures import rfem_model
from rfem_import.csv_tables import RfemCsvError
from rfem_import.model_tables import numbers, read_model
from rfem_import.structure_detection import detect


def _folder(name):
    return conftest.tmpdir("rfem_model_" + name)


def _model(name, lang="fr"):
    return read_model(rfem_model.workbook(_folder(name) / "modele.xlsx", lang=lang))


# --- what one export holds ------------------------------------------------------------------------


def test_the_model_reads_whole_and_reports_nothing():
    """A clean export produces no problem at all -- the state the engineer's own is in."""
    model = _model("whole")
    assert [node.no for node in model.nodes] == [1, 2, 4, 36, 40, 50, 51], f"got {[n.no for n in model.nodes]}"
    assert [member.no for member in model.members] == [1, 2, 24, 30]
    assert len(model.sections) == 2 and len(model.supports) == 5 and len(model.hinges) == 2
    assert len(model.cases) == 2 and len(model.combinations) == 2 and len(model.loads) == 4
    assert model.problems == [], f"got {[str(p) for p in model.problems]}"


def test_a_number_rfem_lists_for_an_object_that_is_gone_is_counted_not_read():
    """⚠️ Node 3 and member 11 of the fixture are empty rows carrying a number, as 6 nodes and 2 members of the engineer's model are. Read as objects they would be a node at no coordinates and a member on no line."""
    model = _model("deleted")
    assert model.skipped == {"node": 1, "member": 1}, f"got {model.skipped}"
    assert model.node(3) is None and all(member.no != 11 for member in model.members)
    assert not [note for note in model.problems if note.code == "rfem_model_no_number"], (
        "an empty numbered row is counted, not reported -- six of them would be six warnings about nothing"
    )


def test_the_chain_is_member_to_line_to_nodes():
    """The one path from a member to its geometry, and the reason the line table is read at all."""
    model = _model("chain")
    member = [m for m in model.members if m.no == 24][0]
    assert member.line == 25 and member.nodes == (36, 40), f"got line={member.line} nodes={member.nodes}"
    assert model.node(36).x == 3.5 and model.node(36).z == -2.95


def test_a_member_whose_line_the_model_lost_is_named():
    model = _model("no_line")
    rows = rfem_model.sheets("fr")
    assert any(row[1] == "25" for row in rows["Barres"]), "the fixture's member 24 is drawn on line 25"


# --- the ranges -----------------------------------------------------------------------------------


def test_a_list_of_object_numbers_expands_its_ranges():
    """⚠️ «2-4» is three members and «1,2,5,8-10,13,14,17-19» is eleven. Both are real cells of his export."""
    assert numbers("1,2") == [1, 2]
    assert numbers("2-4") == [2, 3, 4]
    assert numbers("1,2,5,8-10,13,14,17-19") == [1, 2, 5, 8, 9, 10, 13, 14, 17, 18, 19]
    assert numbers("--") == [] and numbers("") == [] and numbers(None) == []
    assert numbers("7,7,8") == [7, 8], "a number listed twice is one object"
    assert numbers("4-2") == [4, 2], "a range the wrong way round is its two ends, not a run"
    assert numbers("1-999999") == [1, 999999], "a range wider than the limit is its two ends"


def test_a_range_on_a_load_reaches_its_members():
    model = _model("range")
    load = [load for load in model.loads if load.case.endswith("2")][0]
    assert load.members == [1, 2], f"«1-2» came out as {load.members}"


# --- the units -------------------------------------------------------------------------------------


def test_a_coordinate_is_metres_and_a_section_is_millimetres():
    """Each read with the unit its own header declares -- a static model is drawn in metres and a detail schema in millimetres (docs/domain/static-models.md §3.3octies, docs/domain/detail-schemas.md §3.3decies)."""
    model = _model("units")
    assert model.node(2).z == -2.95
    section = model.sections[0]
    assert (section.b, section.h) == (500.0, 200.0), f"got {(section.b, section.h)}"
    assert section.name == "R_M1 500/200" and section.members == [1, 2, 24]


def test_a_member_finds_its_section_through_either_table():
    """The member table names one, and a section's own member list names the members -- both read, since an export may fill either."""
    model = _model("section_of")
    member = [m for m in model.members if m.no == 24][0]
    assert model.section_of(member).no == 1
    assert model.section_of([m for m in model.members if m.no == 30][0]).no == 2


# --- a support and a hinge, which read «inf» the opposite way round --------------------------------


def test_a_support_is_read_as_held_and_a_hinge_as_released():
    """⚠️ The inversion: «inf» holds a support and withholds a release on a hinge. Read as a support, the fixture's two hinges would both be «pinned»."""
    model = _model("restraints")
    # 4 and 5 are the named structure's own pin and roller, which is the span its exported moments describe.
    assert [(s.no, s.kind) for s in model.supports] == [
        (1, "fixed"), (2, "roller"), (3, "pinned"), (4, "pinned"), (5, "roller")], (
        f"got {[(s.no, s.kind) for s in model.supports]}"
    )
    assert [(h.no, h.kind) for h in model.hinges] == [(1, "moment"), (2, "rotational-spring")], (
        f"got {[(h.no, h.kind) for h in model.hinges]}"
    )
    assert model.hinges[1].phi == 21.672001, "a rotational spring keeps its stiffness"


def test_a_support_holds_a_set_of_nodes_and_one_may_hold_none():
    """His nodal support 2 holds 23 nodes at once and three of his five are assigned to nothing."""
    model = _model("support_nodes")
    assert model.supports[0].nodes == [1, 50, 51]
    assert model.supports[1].nodes == [], "a definition assigned to nothing is read and belongs to no structure"


# --- the loadings ----------------------------------------------------------------------------------


def test_a_load_case_carries_its_id_and_the_action_it_is():
    """⚠️ «CC1» is an identifier and not a number. Its category is RFEM's own localised word, mapped to SIA 260's action (docs/domain/calculation-domains.md §3.3)."""
    model = _model("cases")
    assert [(case.id, case.name, case.action) for case in model.cases] == [
        ("CC1", "EG + AL", "permanent"), ("CC2", "Schnee", "variable")
    ], f"got {[(c.id, c.name, c.action) for c in model.cases]}"


def test_a_combination_carries_its_factored_cases():
    """Read by the word for «Factor» and the column beside each, because the *group* over those pairs is the localised «CC.1», «CC.2»."""
    model = _model("combinations")
    first, second = model.combinations
    assert first.id == "CO1" and first.terms == [(1.35, "CC1")], f"got {first.terms}"
    assert second.terms == [(1.35, "CC1"), (1.5, "CC2")], f"got {second.terms}"
    assert second.situation == "SP1 - ELU"
    assert model.combination_cases() == {"CO1": ["CC1"], "CO2": ["CC1", "CC2"]}


def test_the_loads_are_found_per_case_by_the_case_s_own_id():
    """⚠️ The sheet is «CC1 - Charges de barre» here and «LF1 - Stablasten» in German, so it is never looked for by a name this module spells: the case's id is the prefix. It is also the only place the load → case link exists -- the gRPC object listing carries none."""
    model = _model("loads")
    by_case = {}
    for load in model.loads:
        by_case.setdefault(load.case, []).append(load)
    assert sorted(by_case) == ["CC1", "CC2"], f"got {sorted(by_case)}"
    assert {load.kind for load in by_case["CC1"]} == {"member_load", "nodal_load"}
    member_load = [load for load in by_case["CC1"] if load.kind == "member_load"][0]
    assert member_load.members == [1, 2, 24] and member_load.magnitude == 2.5 and member_load.unit == "kN/m"
    nodal = [load for load in by_case["CC1"] if load.kind == "nodal_load"][0]
    assert nodal.nodes == [40] and nodal.magnitude == 11.19 and nodal.unit == "kN"


# --- the metadata ----------------------------------------------------------------------------------


def test_the_comment_column_is_where_the_metadata_is_read():
    """Each object's own clean `comment`, never the composite column of a result table (`csv_tables`). The three comments here are the three the engineer wrote into his model, which travelled through RFEM and the export whole."""
    model = _model("metadata")
    assert model.node(36).meta["model"] == "VU"
    assert model.node(36).meta["label"] == "Velo Unterstand"
    assert model.node(36).meta["descr"] == "günstige Einwirkung"
    member = [m for m in model.members if m.no == 24][0]
    assert member.position == "T001" and member.meta["be"] == 1.7, "a width is read in metres by the parser"
    load = [load for load in model.loads if load.meta.get("be")][0]
    assert load.width == 2.0 and "avant-toit" in load.meta["note"]


# --- the two formats of one dialog -----------------------------------------------------------------


def test_a_workbook_and_a_folder_of_csvs_give_the_same_model():
    """*Fichier → Exporter → Tableaux* writes either, and nothing above `csv_tables` can tell which it was handed."""
    book = read_model(rfem_model.workbook(_folder("both_xlsx") / "modele.xlsx"))
    folder = read_model(rfem_model.csv_folder(_folder("both_csv") / "tables"))

    def shape(model):
        return (
            [(n.no, n.x, n.z) for n in model.nodes],
            [(m.no, m.line, m.nodes, m.section) for m in model.members],
            [(s.no, s.b, s.h, s.members) for s in model.sections],
            [(s.no, s.kind, s.nodes) for s in model.supports],
            [(h.no, h.kind) for h in model.hinges],
            [(c.id, c.action) for c in model.cases],
            [(c.id, c.terms) for c in model.combinations],
            sorted((l.case, l.kind, l.no, tuple(l.members), tuple(l.nodes), l.magnitude) for l in model.loads),
            model.skipped,
        )

    assert shape(book) == shape(folder), "the two formats must read to one model"
    assert book.node(36).meta["model"] == folder.node(36).meta["model"] == "VU", (
        "a multi-line comment survives a quoted CSV field as it survives a worksheet cell"
    )


# --- the three languages ---------------------------------------------------------------------------


def test_the_same_model_reads_in_three_languages():
    """Every word here is read off a real export -- `FR.xlsx`, `DE.xlsx`, `EN.xlsx`, the same model exported three times (26.09.2026). Against those three the reader gives **the same model to the digit**; only what RFEM itself translates differs, the load case's own abbreviation among it (`CC`, `LF`, `LC`), which is why the fixture parameterises it."""
    for lang in ("fr", "de", "en"):
        model = _model("lang_" + lang, lang=lang)
        assert [m.no for m in model.members] == [1, 2, 24, 30], f"{lang}: got {[m.no for m in model.members]}"
        assert model.node(36) is not None and model.node(36).x == 3.5, f"{lang}: node 36 not read"
        assert model.sections[0].b == 500.0, f"{lang}: b came out {model.sections[0].b}"
        assert len(model.cases) == 2 and len(model.loads) == 4, f"{lang}: {len(model.cases)} cases, {len(model.loads)} loads"
        assert model.cases[0].action == "permanent", f"{lang}: the action of the first case is {model.cases[0].action}"
        assert model.combinations[1].terms == [(1.35, model.cases[0].id), (1.5, model.cases[1].id)], f"{lang}"
        assert model.problems == [], f"{lang}: {[str(p) for p in model.problems]}"


# --- into the structures ---------------------------------------------------------------------------


def test_the_model_feeds_the_structure_detection():
    """`Model.items()` and `combination_cases()` are the whole seam. On the engineer's own export this gives 22 structures over 320 items in one second; here it gives the two the fixture draws, one of them named by the comment on **node 36** rather than on a member."""
    model = _model("detect")
    found = detect(model.items(), combinations=model.combination_cases())
    # Three systems: members 1 and 2 share node 2, member 24 stands on its own line and member 30 on another.
    assert len(found) == 3, f"got {len(found)}: {found.names}"
    named = found.of("VU")
    assert named is not None and named.numbers("member") == [24], f"got {named and named.numbers('member')}"
    assert named.statics_name == "Velo Unterstand" and named.statics_descr == "günstige Einwirkung"
    assert list(named.positions) == ["T001"]
    # Member 24 is acted on by CC1's member load 1 («1,2,24») and by nothing of CC2, so one case reaches it -- and both combinations, each being built on CC1.
    assert named.cases == ["CC1"], f"got {named.cases}"
    assert named.combinations == ["CO1", "CO2"], f"got {named.combinations}"
    assert found.by_member(30).key == "member-30", "the other system is unnamed and keyed by its lowest member"
    assert found.items_accounted == len(model.items())


# --- what is missing -------------------------------------------------------------------------------


def test_an_identifier_is_found_by_position_where_its_header_matches_no_alias():
    """⚠️ The regression `DE.xlsx` and `EN.xlsx` found, and the reason the identifier falls back to the **first column**.

    RFEM abbreviates exactly that header, differently per language and not as the table is called: «Quersch. Nr.» in a sheet called «Querschnitte», «Last-\\nkombin.» in «Lastkombinationen», «Load Combs.» in «Load Combinations», «Comb.\\ncharges» in French. Chasing those by alias lost the **German sections** and the **German and English combinations** outright — 9 sections and 48 combinations came back as none, each with a warning about a row «carrying no number» rather than about an alias.

    Held here on a header no alias could ever name, so the fallback is tested and not merely relied on.
    """
    folder = rfem_model.csv_folder(_folder("abbreviated") / "tables")
    path = folder / "Sections.csv"
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    lines[0] = lines[0].replace("Section n°", "Qs. Nr. abrégé")          # a word no alias of COLUMNS names
    path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8-sig")

    model = read_model(folder)
    assert [section.no for section in model.sections] == [1, 2], f"got {[s.no for s in model.sections]}"
    assert model.sections[0].b == 500.0, "and the rest of its columns still read"
    assert not [note for note in model.problems if note.code == "rfem_model_no_number"], (
        f"the identifier is the first column; nothing should be reported: {[str(p) for p in model.problems]}"
    )


def test_a_table_that_is_absent_is_named_and_the_rest_is_read():
    """Nothing refuses: an export missing one sheet still gives the model around it -- the rule the plans, the static models and the connectors follow (docs/architecture/data-contracts.md §3.6)."""
    folder = rfem_model.csv_folder(_folder("missing") / "tables")
    (folder / "Cas de charge.csv").unlink()
    model = read_model(folder)
    assert [m.no for m in model.members] == [1, 2, 24, 30], "the geometry is read"
    assert model.cases == [] and model.loads == [], "and nothing is invented for what is gone"
    missing = [note for note in model.problems if note.code == "rfem_model_no_table"]
    assert len(missing) == 1 and "cases" in missing[0], f"got {[str(p) for p in model.problems]}"


def test_a_source_that_is_not_an_export_at_all_is_refused_by_name():
    folder = _folder("not_an_export")
    (folder / "notes.txt").write_text("nothing here", encoding="utf-8")
    try:
        read_model(folder / "notes.txt")
    except RfemCsvError as error:
        assert "notes.txt" in str(error), f"the refusal must name the file: {error}"
    except Exception as error:                                      # openpyxl's own refusal of a file that is no workbook
        assert "notes" in str(error) or "zip" in str(error).lower(), f"unexpected: {error!r}"
    else:
        raise AssertionError("a file that is not an export must be refused")


def test_a_node_defined_relative_to_another_is_read_at_its_global_place():
    """⚠️ **RFEM's node table carries two pairs of X/Z columns** -- the node's own coordinates, which for a node
    given relative to another are measured from *that* node, and the global ones. Both pairs are named X and Z,
    so resolving the global column and then asking the table for its bare name gives the relative one back
    (`csv_tables.Row.value` says why, and `Row.at` is the answer).

    Found on the engineer's own export (v0.99): node 81 came out at (0.5, 0) where it stands at (20.787, -3),
    so a 0.5 m canopy panel was drawn as a 20 m slanted bar; node 97 came out at (4.23, 0) where it stands at
    (20.97, 6.05), which laid the Pavillon's bench across the bike shelter -- and, its misread axis passing
    through the shelter's own node 8, welded it into that structure by `structure_detection`.
    """
    node = _model("relative").node(4)
    assert (node.x, node.z) == (4.25, -2.95), (
        "node 4 is given relative to node 2 and stands at (4.25, -2.95); "
        "reading its relative pair gives (4.25, 0)"
    )


def test_every_member_is_drawn_at_the_length_rfem_states():
    """The invariant that names a misread coordinate wherever it happens: a member drawn between two nodes is
    as long as RFEM says it is.

    It is the cheapest check there is on the geometry as a whole -- it needs no reference drawing and no eye --
    and on the engineer's own model it went from **7 members of 62 in contradiction to none**.
    """
    model = _model("lengths")
    coords = {node.no: (node.x, node.z) for node in model.nodes}
    checked = 0
    for member in model.members:
        nodes = list(member.nodes)
        if len(nodes) < 2 or member.length is None:
            continue
        a, b = coords.get(nodes[0]), coords.get(nodes[1])
        if a is None or b is None or None in a or None in b:
            continue
        drawn = math.dist(a, b)
        checked += 1
        assert abs(drawn - member.length) < 0.002, (
            f"member {member.no} is drawn {drawn:.3f} m long where RFEM states {member.length} m"
        )
    assert checked >= 3, "the fixture must hold members to check"

