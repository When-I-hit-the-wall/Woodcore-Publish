"""The structures an RFEM model holds (`calc/rfem_import/structure_detection.py`).

Run on the engineer's own model before any of it was asserted here -- its 62 members over 91 nodes, read through the member → line → nodes chain -- and what that run found is the headline of this file: **his model is 22 separate structures**, most of them one to six members. That is not a defect of the detection and not a surprise to be smoothed over: a timber engineer models one static system per element in one RFEM file, and RFEM connects by node, so twenty-two little systems is what the model *is*. It is also exactly why `@model` exists — the engineer names them, and the ones that belong together are merged by name.

Two facts about that run are asserted here on fixtures, because they are what a reader of the numbers would get wrong:

- **An RFEM support or load is one object applied to a set.** His nodal support 2 holds 23 nodes and his member load 1 acts on members 2, 8 and 9. So an object may reach several structures and is listed in each — 10 of his did — and the accounting counts items by identity rather than summing over the structures.
- **The accounting balances**: `items_accounted` equals every item the detection was given. On his model: 194 given, 194 accounted, 12 of them orphans (7 nodes no element touches, 3 support definitions assigned to nothing, 2 loads acting on nothing).

⚠️ And one regression, for a defect the real model found in **`csv_tables.py`** rather than here: his model carries no surface, so RFEM exports its surface table as a header row and nothing else, and `read_table` refused it — «no data». That made «the model has no surfaces» and «this export is broken» one exception a caller cannot tell apart, and it stopped the detection of every model built out of members alone. `tests/test_rfem_csv.py` holds the fix; this file holds what it was blocking.
"""

from rfem_import.metadata_parser import parse_metadata
from rfem_import.structure_detection import Item, detect


def member(number, nodes, comment=None):
    return Item("member", number, nodes=nodes, meta=parse_metadata(comment, where=f"Member {number}"))


def node(number, comment=None):
    return Item("node", number, nodes=[number], meta=parse_metadata(comment, where=f"Node {number}"))


def load(number, on, comment=None, case=None):
    return Item("member_load", number, on=on, case=case,
                meta=parse_metadata(comment, where=f"Member load {number}"))


# A frame of three members on four nodes, and a beam of two on three, sharing nothing -- the shape of the engineer's own model.
def two_systems():
    return [
        member(1, [1, 2]), member(2, [2, 3]), member(3, [3, 4]),
        member(10, [10, 11]), member(11, [11, 12]),
    ]


# --- the components -------------------------------------------------------------------------------


def test_a_structure_is_a_connected_component_of_the_node_graph():
    """Two groups sharing no node are two structures. RFEM connects by node, so this is its own notion of connection and not a choice made here."""
    found = detect(two_systems())
    assert len(found) == 2, f"got {len(found)}: {found.names}"
    first, second = found.structures
    assert first.numbers("member") == [1, 2, 3] and first.nodes == [1, 2, 3, 4]
    assert second.numbers("member") == [10, 11] and second.nodes == [10, 11, 12]


def test_members_that_touch_and_share_no_node_stay_two_structures():
    """⚠️ The commonest way a model surprises its author -- a hinge modelled as two coincident nodes -- and geometry is deliberately not consulted: a tolerance that merged two structures the engineer meant apart would be worse than a list he can read."""
    items = [member(1, [1, 2]), member(2, [3, 4])]      # nodes 2 and 3 may well be the same point
    assert len(detect(items)) == 2, "coordinates must not join what RFEM did not join"


def test_the_structures_are_ordered_by_their_lowest_member():
    found = detect(list(reversed(two_systems())))
    assert [structure.numbers("member")[0] for structure in found] == [1, 10]


def test_a_surface_joins_its_whole_boundary():
    """Chained to its first node rather than paired node by node, which is what keeps a surface of thirty nodes thirty unions."""
    items = [Item("surface", 1, nodes=[1, 2, 3, 4]), member(1, [4, 5])]
    found = detect(items)
    assert len(found) == 1 and found.structures[0].nodes == [1, 2, 3, 4, 5]
    assert len(found.structures[0].surfaces) == 1


# --- what the engineer's comments name -------------------------------------------------------------


def test_model_names_the_structure_and_label_and_descr_name_the_static_model():
    """The engineer's own mapping, and the three keys name two different things: `@model` is the structure, `@label` and `@descr` the static model it becomes (`metadata_parser.KEYS`)."""
    items = [member(1, [1, 2], '@model "VU-gunstig"\n@label "Velo Unterstand"\n@descr "reduzierte Einwirkungsbreite"'),
             member(2, [2, 3])]
    structure = detect(items).structures[0]
    assert structure.name == "VU-gunstig" and structure.named
    assert structure.statics_name == "Velo Unterstand"
    assert structure.statics_descr == "reduzierte Einwirkungsbreite"
    assert structure.key == "VU-gunstig"


def test_a_name_written_on_a_node_names_the_structure_that_node_belongs_to():
    """Which is where the engineer wrote it: node 36 of his own model carries the three keys."""
    items = [member(1, [1, 36]), member(2, [36, 3]), node(36, '@model "Pavillon"')]
    found = detect(items)
    assert len(found) == 1 and found.structures[0].name == "Pavillon"


def test_two_components_carrying_one_name_are_one_structure():
    """⚠️ The one direction the engineer may override the geometry in, and the safe one: saying «these two groups are the Velo-Unterstand» adds what the model does not hold."""
    items = two_systems()
    items[0] = member(1, [1, 2], '@model "Velo"')
    items[3] = member(10, [10, 11], '@model "Velo"')
    found = detect(items)
    assert len(found) == 1, f"got {len(found)}: {found.names}"
    assert found.structures[0].numbers("member") == [1, 2, 3, 10, 11]
    assert found.structures[0].nodes == [1, 2, 3, 4, 10, 11, 12]


def test_two_names_in_one_component_are_refused_by_name_and_the_commonest_wins():
    """Nothing can part what RFEM has joined, so the contradiction is reported with what to do about it -- and the value most objects carry is used meanwhile."""
    items = [member(1, [1, 2], '@model "A"'), member(2, [2, 3], '@model "B"'), member(3, [3, 4], '@model "B"')]
    found = detect(items)
    assert len(found) == 1 and found.structures[0].name == "B", f"got {found.names}"
    conflict = [note for note in found.problems if note.code == "rfem_structure_conflict"]
    assert len(conflict) == 1, f"got {[n.code for n in found.problems]}"
    assert "«A»" in conflict[0] and "«B»" in conflict[0] and "part them in RFEM" in conflict[0]


def test_a_group_nobody_named_says_where_to_write_the_name():
    """Its key is its lowest element, stable while that element exists, so a second import does not rename everything."""
    found = detect(two_systems())
    assert [structure.key for structure in found] == ["member-1", "member-10"]
    assert all(structure.name is None and not structure.named for structure in found)
    unnamed = [note for note in found.problems if note.code == "rfem_structure_unnamed"]
    assert len(unnamed) == 2 and "@model" in unnamed[0], f"got {[str(n) for n in unnamed]}"


def test_a_position_is_listed_with_the_element_that_carries_it():
    """What the window lists and what validation resolves against Positionen.xlsx. Member 24 of the engineer's model carries `@position "T001"` and `@be 1.7m`."""
    items = [member(24, [1, 2], '@position "T001"\n@be 1.7m'), member(25, [2, 3], '@position "T001"')]
    structure = detect(items).structures[0]
    assert list(structure.positions) == ["T001"]
    assert [item.number for item in structure.positions["T001"]] == [24, 25]
    assert structure.members[0].meta["be"] == 1.7, "a width is read in metres by the parser"


# --- an object applied to a set --------------------------------------------------------------------


def test_a_support_over_several_structures_is_listed_in_each():
    """⚠️ Measured on the engineer's model: his nodal support 2 holds **23 nodes**, his member load 1 acts on members 2, 8 and 9. An RFEM support is a definition applied to a set, not one physical support, so placing it in the first structure it touched would have hidden it from the others."""
    items = two_systems() + [Item("support", 2, nodes=[1, 10])]
    found = detect(items)
    assert len(found) == 2
    assert all(len(structure.supports) == 1 for structure in found), "the support belongs to both"
    assert len(found.shared) == 1 and found.shared[0].where == "Support 2"
    assert found.items_accounted == len(items), (
        f"{found.items_accounted} accounted of {len(items)} given -- an item in two structures is counted once"
    )


def test_a_load_is_placed_where_the_members_it_acts_on_are():
    items = two_systems() + [load(1, [("member", 2), ("member", 3)], "@be 2m", case="CC1")]
    found = detect(items)
    assert len(found.structures[0].loads) == 1 and not found.structures[1].loads
    assert found.structures[0].loads[0].meta["be"] == 2.0
    assert found.structures[0].cases == ["CC1"] and found.structures[1].cases == []


def test_a_load_naming_a_member_the_model_does_not_carry_is_named():
    """A load acting on members 2, 8 and 9 of which 9 was deleted no longer says what it acts on, so it is reported whether or not the rest of it placed."""
    items = two_systems() + [load(4, [("member", 2), ("member", 99)])]
    found = detect(items)
    missing = [note for note in found.problems if note.code == "rfem_structure_unknown_host"]
    assert len(missing) == 1 and "member 99" in missing[0], f"got {[str(n) for n in found.problems]}"
    assert len(found.structures[0].loads) == 1, "what could be placed still is"


def test_the_combinations_acting_on_a_structure_are_the_ones_its_cases_are_in():
    """What the window lists beside a structure's elements. The combinations are the model's own -- «CO1 = 1.35 · CC1» -- and their labels are never interpreted."""
    items = two_systems() + [load(1, [("member", 2)], case="CC1"), load(2, [("member", 10)], case="CC2")]
    found = detect(items, combinations={"CO1": ["CC1"], "CO2": ["CC1", "CC2"], "CO3": ["CC3"]})
    first, second = found.structures
    assert first.combinations == ["CO1", "CO2"], f"got {first.combinations}"
    assert second.combinations == ["CO2"], f"got {second.combinations}"


# --- what belongs to nothing ----------------------------------------------------------------------


def test_a_node_no_element_touches_is_an_orphan_and_is_not_reported_unless_it_says_something():
    """A construction node is ordinary in an RFEM model -- his has 7 -- so naming each would be noise. One carrying metadata names nothing, and that is worth a word."""
    items = two_systems() + [node(50), node(51, '@model "nowhere"')]
    found = detect(items)
    assert len(found.orphans) == 2
    orphan = [note for note in found.problems if note.code == "rfem_structure_orphan"]
    assert len(orphan) == 1 and "Node 51" in orphan[0], f"got {[str(n) for n in found.problems]}"


def test_an_element_defined_by_fewer_than_two_nodes_connects_nothing_and_says_so():
    """A member whose line the model lost. It still becomes its own structure rather than vanishing."""
    found = detect([member(1, [1]), member(2, [])])
    lonely = [note for note in found.problems if note.code == "rfem_structure_no_nodes"]
    assert len(lonely) == 2, f"got {[n.code for n in found.problems]}"
    assert len(found) == 1 and found.orphans[0].number == 2, "the one with no node at all is placed nowhere"


def test_nothing_refuses():
    """The rule the plans, the static models and the connectors already follow: a detection that stopped on one unnamed group would stop the import of every other."""
    found = detect([member(1, [1, 2], '@model "A"'), member(2, [1, 3], '@model "B"'),
                    node(9, "@model"), load(1, [("member", 77)]), member(3, [])])
    assert isinstance(found.problems, list) and found.problems, "every one of those is a problem and none is an exception"
    assert found.items_accounted == 5


# --- the accounting, which is what catches a misplaced object --------------------------------------


def test_every_item_is_accounted_for():
    """`items_accounted` against the length of the input -- the invariant that balanced on all 194 items of the engineer's model."""
    items = two_systems() + [
        node(1), node(2), node(99),
        Item("support", 1, nodes=[1]), Item("support", 3, nodes=[]),
        load(1, [("member", 1)]), load(2, [("member", 404)]),
    ]
    found = detect(items)
    assert found.items_accounted == len(items), f"{found.items_accounted} of {len(items)}"
    assert len(found.orphans) == 3, f"got {[item.where for item in found.orphans]}"


def test_a_structure_is_found_from_one_of_its_members():
    """What tells a member's internal forces which static system they act in (`results.py`)."""
    found = detect(two_systems())
    assert found.by_member(2) is found.structures[0]
    assert found.holding("member", 11) is found.structures[1]
    assert found.by_member(77) is None
    assert found.of("member-10") is found.structures[1]
