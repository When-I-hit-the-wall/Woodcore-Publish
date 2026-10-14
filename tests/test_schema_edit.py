"""Modifying a detail schema: move, duplicate, turn, mirror, split and merge (docs/domain/detail-schemas.md §3.3decies; plan 4 of je-souhaite-commencer-generic-valley.md).

Two halves, and they are guarded differently on purpose.

**The geometry is pure Python on a plain dict** -- `schema.modify`, `duplicate`, `split_element`, `merge_elements` and the three transforms they are given -- so it is exercised here directly, with no window anywhere near it. That is `statics.py`'s own arrangement for its tracking, and it is what lets the awkward cases (a concave area, a cut landing exactly on a vertex, a mirror twice over) be written down as arithmetic rather than as clicks.

**The interaction is driven through `SchemaCanvas`**, off-screen: the four verbs go through `place()` like every tool the peer session wrote, so a modification the tab can perform is one the export accepts -- which is the guard that matters, the engineer otherwise meeting the refusal only at *Enregistrer*.

⚠️ What no test here reaches is the pointer: Ctrl+click is exercised through `select(..., add=True)` rather than through a `QMouseEvent`, and the rubber band does not exist. That is the engineer's own walk through the window, which the plan's verification section asks for in so many words.
"""

import copy
import math
import os
import sys

from conftest import ROOT, Skip
from domains import schema as model


# --- fixtures -----------------------------------------------------------------------

def _source():
    """A beam, a plate, a centre and a vertical construction line at x = 50 -- the smallest schema on which every verb has something to do."""
    source = model.new_source("D99")
    source["elements"] = [
        {"id": "E1", "kind": "linear", "position": "T001", "view": "h",
         "h": 40, "points": [[0, 0], [100, 0]]},
        {"id": "E2", "kind": "area", "position": "S001",
         "points": [[0, 0], [100, 0], [100, 100], [0, 100]]},
    ]
    source["connectors"] = [{"id": "C1", "kind": "Stabdübel", "x": 20, "z": 0}]
    source["aids"] = [
        {"id": "A1", "kind": "centre", "x": 0, "z": 0},
        {"id": "A2", "kind": "vertical", "x": 50, "z": 0, "angle": 90.0, "shown": False},
    ]
    return source


def _checked(source):
    """The source as it stands, checked the way the export checks it."""
    model.check_source(source, "D99.json")
    return source


def _canvas(source=None):
    path = str(ROOT / "calc" / "tools")
    if path not in sys.path:
        sys.path.insert(0, path)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    QApplication.instance() or QApplication([])
    from schema_canvas import SchemaCanvas
    canvas = SchemaCanvas()
    canvas.set_source(source if source is not None else _source())
    return canvas


def _points(source, eid):
    return [tuple(p) for p in model.entry_of(source, "elements", eid)["points"]]


# --- what the plan asks for, in its own four sentences --------------------------------

def test_an_element_split_in_two_keeps_its_position_number():
    """The rule the engineer set: «un élément tranché en 2 créé 2 éléments avec les mêmes numéros de position». The position plan already allows two identical elements to share a number (v0.44), which is what makes it legal downstream rather than merely convenient here."""
    source = _source()
    made = model.split_element(source, "E1", "A2")
    assert len(made) == 2, made
    assert made[0] == "E1", "the first piece keeps the element's own id, so a dimension anchored to it still resolves"
    for eid in made:
        piece = model.entry_of(source, "elements", eid)
        assert piece["position"] == "T001"
        assert piece["h"] == 40, "a cut changes where a piece ends, not what it is -- its section included (v0.75)"
        assert piece["view"] == "h"
    assert _points(source, made[0]) == [(0, 0), (50, 0)]
    assert _points(source, made[1]) == [(50, 0), (100, 0)]
    _checked(source)


def test_merging_two_different_position_numbers_refuses_naming_both():
    """«Il est uniquement possible de fusionner des éléments avec les mêmes numéros de position (un message d'erreur s'affiche sinon)» -- and the message has to name them, or it says only that something is wrong."""
    source = _source()
    source["elements"][1]["kind"] = "linear"
    source["elements"][1]["h"] = 40
    source["elements"][1]["points"] = [[100, 0], [200, 0]]
    try:
        model.merge_elements(source, ["E1", "E2"])
    except model.Refused as exc:
        assert exc.code == "merge-positions"
        assert "T001" in str(exc) and "S001" in str(exc), str(exc)
        assert "T001" in exc.detail and "S001" in exc.detail, exc.detail
    else:
        raise AssertionError("two positions merged into one")
    assert len(source["elements"]) == 2, "a refusal changes nothing"


def test_a_quarter_turn_four_times_gives_back_the_coordinates_it_started_from():
    """Four times 90 degrees is the identity, and it has to be so **to the digit**: a rotation that rounds its own way would walk a schema off its grid over an afternoon's editing. What makes it exact is that `round_place` is the rounding a click already uses, applied by both."""
    source = _source()
    before = copy.deepcopy(source)
    for _ in range(4):
        model.modify(source, ["E1", "E2", "C1", "A1", "A2"], model.rotation((13, 7), 90))
    for collection in ("elements", "connectors", "aids"):
        assert source[collection] == before[collection], collection
    _checked(source)


def test_mirroring_twice_gives_back_the_coordinates_it_started_from():
    source = _source()
    before = copy.deepcopy(source)
    for _ in range(2):
        model.modify(source, ["E1", "E2", "C1", "A1", "A2"], model.reflection((10, 10), (60, 90)))
    for collection in ("elements", "connectors", "aids"):
        assert source[collection] == before[collection], collection
    _checked(source)


# --- the verbs, one at a time ---------------------------------------------------------

def test_a_move_carries_every_shape_of_entry_with_it():
    source = _source()
    model.modify(source, ["E1", "E2", "C1", "A1", "A2"], model.translation(10, -5))
    assert _points(source, "E1") == [(10, -5), (110, -5)]
    marker = model.entry_of(source, "connectors", "C1")
    assert (marker["x"], marker["z"]) == (30, -5)
    centre = model.entry_of(source, "aids", "A1")
    assert (centre["x"], centre["z"]) == (10, -5)
    line = model.entry_of(source, "aids", "A2")
    assert (line["x"], line["z"]) == (60, -5)
    assert line["angle"] == 90.0, "a translation moves a construction line and does not turn it"
    _checked(source)


def test_a_rotation_turns_a_construction_line_with_the_geometry():
    source = _source()
    model.modify(source, ["A2"], model.rotation((0, 0), 30))
    assert model.entry_of(source, "aids", "A2")["angle"] == 120.0


def test_a_mirror_folds_a_direction_about_the_axis_rather_than_turning_it():
    """A reflection reverses orientation, so a direction is folded (2·axis − angle) and not rotated. Mirroring a vertical line across a vertical axis leaves it vertical; rotating it by anything would not."""
    source = _source()
    model.modify(source, ["A2"], model.reflection((0, 0), (0, 100)))
    assert abs(abs(model.entry_of(source, "aids", "A2")["angle"]) - 90.0) < 1e-9


def test_a_duplicate_keeps_the_position_and_takes_a_new_id():
    source = _source()
    made = model.duplicate(source, ["E1", "C1"], model.translation(0, 200))
    assert len(made) == 2 and "E1" not in made and "C1" not in made
    copy_of = model.entry_of(source, "elements", made[0])
    assert copy_of["position"] == "T001", "two identical pieces share a number (v0.44)"
    assert copy_of["points"] == [[0, 200], [100, 200]]
    assert _points(source, "E1") == [(0, 0), (100, 0)], "the original stays where it was"
    _checked(source)


def test_a_duplicate_leaves_a_dimension_alone():
    """A dimension is anchored. A copy of one would either measure the original from the copy's place or name nothing at all, so the geometry is duplicated and re-dimensioned instead -- which is the honest order, and is said in `duplicate`'s own docstring."""
    source = _source()
    source["dimensions"] = [{"id": "D1", "kind": "horizontal",
                             "from": {"point": "A1"}, "to": {"x": 100, "z": 0}, "offset": -40}]
    made = model.duplicate(source, ["E1", "D1"], model.translation(0, 200))
    assert len(made) == 1, "the element was copied and the dimension was not"
    assert len(source["dimensions"]) == 1


def test_a_dimension_moved_with_the_geometry_keeps_its_kind_and_moves_its_free_end():
    source = _source()
    source["dimensions"] = [{"id": "D1", "kind": "horizontal",
                             "from": {"point": "A1"}, "to": {"x": 100, "z": 0}, "offset": -40}]
    model.modify(source, ["E1", "A1", "D1"], model.translation(10, -5))
    dim = model.entry_of(source, "dimensions", "D1")
    assert dim["kind"] == "horizontal", "choosing a kind said what is measured; a move does not unsay it"
    assert dim["from"] == {"point": "A1"}, "an anchored end follows its aid rather than being moved twice"
    assert (dim["to"]["x"], dim["to"]["z"]) == (110, -5), "a free end is a place of its own and moves"
    _checked(source)


def test_a_mirror_puts_a_dimension_line_on_the_other_side():
    source = _source()
    source["dimensions"] = [{"id": "D1", "kind": "horizontal",
                             "from": {"x": 0, "z": 0}, "to": {"x": 100, "z": 0}, "offset": -40}]
    model.modify(source, ["D1"], model.reflection((0, 0), (100, 0)))
    assert model.entry_of(source, "dimensions", "D1")["offset"] == 40


# --- trancher --------------------------------------------------------------------------

def test_an_area_cut_by_a_line_gives_two_areas_that_add_back_up():
    source = _source()
    made = model.split_element(source, "E2", "A2")
    assert len(made) == 2
    halves = [_points(source, eid) for eid in made]
    for half in halves:
        assert len(half) == 4
    assert sum(_area(h) for h in halves) == 10000, "the two halves are the whole square"
    _checked(source)


def _area(points):
    """A polygon's area, by the shoelace formula -- what says two halves add back up to the whole."""
    total = 0.0
    for i, (x, z) in enumerate(points):
        nx, nz = points[(i + 1) % len(points)]
        total += x * nz - nx * z
    return abs(total) / 2.0


def test_a_line_that_misses_the_element_refuses_and_changes_nothing():
    source = _source()
    source["aids"].append({"id": "A3", "kind": "vertical", "x": 400, "z": 0, "angle": 90.0, "shown": False})
    try:
        model.split_element(source, "E1", "A3")
    except model.Refused as exc:
        assert exc.code == "split-missed"
    else:
        raise AssertionError("a line 300 mm away cut the element")
    assert _points(source, "E1") == [(0, 0), (100, 0)]


def test_a_named_point_is_refused_as_a_cutting_line():
    """A centre is an aid too, and it is the obvious thing to select by mistake. The refusal names why rather than reporting that the cut missed."""
    source = _source()
    try:
        model.split_element(source, "E1", "A1")
    except model.Refused as exc:
        assert exc.code == "split-aid-point"
    else:
        raise AssertionError("a point cut an element")


def test_a_line_crossing_an_area_four_times_is_refused_by_the_count():
    """A U cut across both of its uprights: the line enters, leaves, enters and leaves again. Two pieces is not the answer, and three without saying so is worse, so it refuses **naming the count** -- the engineer then moves the line or cuts twice.

    ⚠️ An **L** is the shape that first comes to mind here and it does not work: whichever way a straight line is laid across an L it enters once and leaves once, so the L splits perfectly well. It took drawing both to see it, which is why the U is written down here with its coordinates."""
    source = _source()
    source["elements"][1]["points"] = [[0, 0], [100, 0], [100, 100], [70, 100],
                                       [70, 40], [30, 40], [30, 100], [0, 100]]
    source["aids"].append({"id": "A3", "kind": "horizontal", "x": 0, "z": 70, "angle": 0.0, "shown": False})
    try:
        model.split_element(source, "E2", "A3")
    except model.Refused as exc:
        assert exc.code == "split-crossings", exc.code
        assert exc.detail == "4", exc.detail
    else:
        raise AssertionError("a U was cut into two by one line across both uprights")


def test_a_polyline_cut_twice_gives_three_pieces():
    """`split_element` produces the polyline that section 3.3decies says only a split can produce, so cutting one again has to work -- the general case, not a second special one."""
    source = _source()
    source["elements"][0]["points"] = [[0, 0], [100, 0], [100, 100]]
    source["aids"].append({"id": "A3", "kind": "horizontal", "x": 0, "z": 50, "angle": 0.0, "shown": False})
    made = model.split_element(source, "E1", "A2")
    assert len(made) == 2
    again = model.split_element(source, made[1], "A3")
    assert len(again) == 2
    assert {model.entry_of(source, "elements", eid)["position"] for eid in made + again} == {"T001"}
    _checked(source)


# --- fusionner ---------------------------------------------------------------------------

def test_splitting_then_merging_gives_back_the_shape_it_started_from():
    """The property that makes the two verbs a pair rather than two features. ⚠️ It needs the collinear point the cut left behind to be taken out again, which `_drop_collinear` is for -- without it a merge gives the right shape carrying two vertices nobody drew."""
    for eid in ("E1", "E2"):
        source = _source()
        before = _points(source, eid)
        made = model.split_element(source, eid, "A2")
        kept = model.merge_elements(source, made)
        after = _points(source, kept)
        assert len(after) == len(before), (eid, after)
        assert _same_ring(after, before), (eid, after, before)
        assert len(source["elements"]) == 2, "the piece that went is gone"
        _checked(source)


def _same_ring(a, b):
    """Two closed shapes are the same whatever vertex they are written from, and whichever way round."""
    if len(a) != len(b):
        return False
    if a == b:
        return True
    for turn in (list(b), list(reversed(b))):
        for i in range(len(turn)):
            if a == turn[i:] + turn[:i]:
                return True
    return False


def test_elements_that_do_not_touch_refuse_to_merge():
    source = _source()
    source["elements"][1] = {"id": "E2", "kind": "linear", "position": "T001",
                             "view": "h", "h": 40, "points": [[300, 0], [400, 0]]}
    try:
        model.merge_elements(source, ["E1", "E2"])
    except model.Refused as exc:
        assert exc.code == "merge-apart"
    else:
        raise AssertionError("two elements 200 mm apart were joined")


def test_a_linear_element_and_an_area_do_not_merge():
    source = _source()
    source["elements"][1]["position"] = "T001"
    try:
        model.merge_elements(source, ["E1", "E2"])
    except model.Refused as exc:
        assert exc.code == "merge-kinds"
    else:
        raise AssertionError("a line and an area became one piece")


def test_merging_one_element_is_refused():
    source = _source()
    try:
        model.merge_elements(source, ["E1"])
    except model.Refused as exc:
        assert exc.code == "merge-too-few"
    else:
        raise AssertionError("one element merged with itself")


# --- the canvas: the multiple selection, and the verbs through place() -------------------

def test_ctrl_adds_to_the_selection_and_clicking_it_again_takes_it_out():
    canvas = _canvas()
    canvas.select(("elements", "E1"))
    canvas.select(("connectors", "C1"), add=True)
    assert canvas.selection_ids() == [("connectors", "C1"), ("elements", "E1")], \
        "the one just clicked takes the focus and the other joins the rest"
    canvas.select(("connectors", "C1"), add=True)
    assert canvas.selection_ids() == [("elements", "E1")]
    canvas.select(("elements", "E1"), add=True)
    assert canvas.selection_ids() == []
    assert canvas.selection is None


def test_a_plain_click_replaces_the_whole_selection():
    canvas = _canvas()
    canvas.select(("elements", "E1"))
    canvas.select(("elements", "E2"), add=True)
    canvas.select(("connectors", "C1"))
    assert canvas.selection_ids() == [("connectors", "C1")]


def test_deleting_a_multiple_selection_is_one_step_of_undo():
    """⚠️ The point of the bracket. Six entries deleted in six `begin_change()` pairs would be six presses of «Annuler» to get back, which is not what the engineer did."""
    canvas = _canvas()
    steps = []
    canvas.about_to_change.connect(lambda: steps.append(1))
    canvas.select(("elements", "E1"))
    canvas.select(("connectors", "C1"), add=True)
    canvas.delete_selection()
    assert steps == [1], steps
    assert model.entry_of(canvas.source, "elements", "E1") is None
    assert model.entry_of(canvas.source, "connectors", "C1") is None
    assert canvas.selection_ids() == []


def test_a_move_through_the_canvas_takes_two_clicks_and_one_undo_step():
    canvas = _canvas()
    steps = []
    canvas.about_to_change.connect(lambda: steps.append(1))
    canvas.select(("elements", "E1"))
    canvas.select(("connectors", "C1"), add=True)
    canvas.set_tool("move")
    canvas.place((0.0, 0.0))
    canvas.place((0.0, 200.0))
    assert steps == [1], steps
    assert _points(canvas.source, "E1") == [(0, 200), (100, 200)]
    assert model.entry_of(canvas.source, "connectors", "C1")["z"] == 200
    _checked(canvas.source)


def test_a_duplicate_through_the_canvas_selects_the_copies():
    """So that a second duplicate copies the copy, which is what laying out a row of identical pieces is."""
    canvas = _canvas()
    canvas.select(("elements", "E1"))
    canvas.set_tool("duplicate")
    canvas.place((0.0, 0.0))
    canvas.place((0.0, 200.0))
    made = canvas.selection_ids()
    assert made and made[0][1] != "E1", made
    canvas.place((0.0, 200.0))
    canvas.place((0.0, 400.0))
    assert len(canvas.source["elements"]) == 4
    zs = sorted(e["points"][0][1] for e in canvas.source["elements"] if e["kind"] == "linear")
    assert zs == [0, 200, 400], zs
    _checked(canvas.source)


def test_a_turn_through_the_canvas_reads_the_second_click_as_a_direction():
    canvas = _canvas()
    canvas.select(("elements", "E1"))
    canvas.set_tool("rotate")
    canvas.place((0.0, 0.0))
    canvas.place((0.0, 50.0))      # due +z, which is 90 degrees from +x
    assert _points(canvas.source, "E1") == [(0, 0), (0, 100)]
    _checked(canvas.source)


def test_a_modification_with_nothing_selected_says_so(capture=None):
    """A tool that silently does nothing is the failure mode this project treats as the worst kind (v0.47's own rule for a plan tool that draws nothing)."""
    canvas = _canvas()
    said = []
    canvas.refused.connect(said.append)
    canvas.set_tool("move")
    canvas.place((0.0, 0.0))
    canvas.place((0.0, 200.0))
    assert said and said[0].startswith("modify-nothing"), said
    assert _points(canvas.source, "E1") == [(0, 0), (100, 0)]


def test_the_split_button_needs_one_line_in_the_selection():
    canvas = _canvas()
    said = []
    canvas.refused.connect(said.append)
    canvas.select(("elements", "E1"))
    canvas.split_selection()
    assert said and said[-1].startswith("split-no-line"), said
    assert len(canvas.source["elements"]) == 2, "a refusal cuts nothing"
    canvas.select(("aids", "A2"), add=True)
    canvas.split_selection()
    assert len(canvas.source["elements"]) == 3
    assert canvas.selection_ids() == [("elements", "E1"), ("elements", "E3")], canvas.selection_ids()


def test_a_refused_split_leaves_no_undo_step_behind():
    """⚠️ `begin_change()` is what pushes a step of «Annuler». A refusal after it would leave an undo that undoes nothing, and a cut that misses is the common case here, not the rare one -- hence the probe on a copy."""
    canvas = _canvas()
    steps = []
    canvas.about_to_change.connect(lambda: steps.append(1))
    canvas.source["aids"].append({"id": "A3", "kind": "vertical", "x": 400, "z": 0,
                                  "angle": 90.0, "shown": False})
    canvas.select(("elements", "E1"))
    canvas.select(("aids", "A3"), add=True)
    canvas.split_selection()
    assert steps == [], steps


def test_the_merge_button_reports_the_model_s_own_refusal_with_its_detail():
    """The reason reaches the tab as «code|detail», so the window can say it in French and still name the two numbers the model found."""
    canvas = _canvas()
    said = []
    canvas.refused.connect(said.append)
    canvas.source["elements"][1]["kind"] = "linear"
    canvas.source["elements"][1]["h"] = 40
    canvas.source["elements"][1]["points"] = [[100, 0], [200, 0]]
    canvas.select(("elements", "E1"))
    canvas.select(("elements", "E2"), add=True)
    canvas.merge_selection()
    assert said, "a merge that cannot happen must say why"
    code, _, detail = said[-1].partition("|")
    assert code == "merge-positions"
    assert "T001" in detail and "S001" in detail, detail
    assert len(canvas.source["elements"]) == 2


def test_every_refusal_the_canvas_raises_has_words_in_all_three_languages():
    """A code the tab has no string for shows the raw code in the status line, which is a defect the engineer would meet and nobody else would."""
    _canvas()                                   # puts calc/tools on the path
    import schema_tab
    from domains import schema as schema_model
    codes = set(schema_tab.REFUSALS)
    for code in ("modify-nothing", "modify-axis", "split-no-element", "split-no-line",
                 "split-many-lines", "split-missed", "split-crossings", "split-aid-point",
                 "merge-too-few", "merge-kinds", "merge-positions", "merge-apart",
                 "merge-no-edge"):
        assert code in codes, code
    for lang, texts in schema_tab.STRINGS.items():
        for code, key in schema_tab.REFUSALS.items():
            assert key in texts, f"{lang} has no {key} (for {code})"
    assert schema_model.Refused("x", "y").code == "x"


def test_the_lists_and_the_canvas_hold_the_same_selection():
    """They are kept in phase in the only way a tabbed layout allows: each list marks its own share, and the canvas holds the whole."""
    canvas = _canvas()          # builds the QApplication, off-screen
    del canvas
    import woodcore_gui
    window = woodcore_gui.MainWindow()
    window.show()
    tab = next(t for t in window.tabs if type(t).__name__ == "SchemaTab")
    tab.window_ref = window     # the window outlives this call, or the tab goes with it
    tab.open_source(_source(), "D99", False)
    tab.canvas.select(("elements", "E1"))
    tab.canvas.select(("elements", "E2"), add=True)
    tab.on_selection()
    linear = tab.table_widgets["linear"]
    area = tab.table_widgets["area"]
    assert {i.row() for i in linear.selectedIndexes()} == {0}
    assert {i.row() for i in area.selectedIndexes()} == {0}
    # And back the other way: picking a row hands the canvas that row.
    tab.canvas.select(None)
    tab.loading = False
    linear.selectRow(0)
    tab.on_table_selection("linear")
    assert tab.canvas.selection_ids() == [("elements", "E1")], tab.canvas.selection_ids()


def test_a_mirror_moves_a_point_to_the_other_side_of_its_axis():
    """`reflection()` returned the point itself (periodic audit 260916, AUD-5-1): «Symétrie» folded the construction lines' angles and flipped the dimensions' sides while leaving every point where it was -- and mirroring twice, the one check it had, cannot tell a mirror from the identity."""
    import math
    from domains import schema as model

    def same(p, q):
        return all(math.isclose(a, b, abs_tol=1e-9) for a, b in zip(p, q))

    place, _bearing, _flips = model.reflection((0, 600), (100, 600))
    assert same(place(0, 0), (0, 1200)), place(0, 0)
    place, _bearing, _flips = model.reflection((0, 0), (0, 100))
    assert same(place(30, 5), (-30, 5)), place(30, 5)
    place, _bearing, _flips = model.reflection((0, 0), (100, 100))
    assert same(place(10, 0), (0, 10)), place(10, 0)
    source = model.new_source("D99")
    source["elements"] = [{"id": "E1", "kind": "linear", "position": "T001", "view": "h", "h": 40, "points": [[0, 0], [100, 0]]}]
    model.modify(source, ["E1"], model.reflection((0, 50), (100, 50)))
    assert [list(map(float, p)) for p in source["elements"][0]["points"]] == [[0.0, 100.0], [100.0, 100.0]], source["elements"][0]["points"]
