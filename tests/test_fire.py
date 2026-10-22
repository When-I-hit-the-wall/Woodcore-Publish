"""Fire-protection plans: the source, the frame it follows or carries, and what is drawn on it by hand (calc/domains/fire.py, calc/domains/fire_svg.py).

What is held here: a source that follows a position plan AND states a frame of its own is refused, and so is one that does neither; a plan that follows a position plan takes that plan's frame afresh at every reading, and a position plan that is gone is a Note and an empty sheet, never an error; an id is unique across every collection and a number is never given twice; a surface is of one of the sheet's three kinds or a draft; a door opens the way its two points and its side say, and flipping its hinge keeps the side of the wall it opens to; the emergency exit's arrow and the sliding door keep the proportions of the sheet's pictograms; an escape route writes its length and a width what it measures; the legend lists what is drawn and nothing else, in the sheet's order and in the language asked for; the drawing is kept to what QtSvg and Typst read alike; a factor multiplies and reaches what it names; an entry is as opaque as it says; a text moved by hand follows its entry; a plan that follows a position plan may state its own crop and nothing else of the frame; and the export carries the figure in every language with what the plan measures.

Since v0.115 (the engineer's decisions of 06.10.2026) the source is schema 2.0: a plan with a frame of its own may be drawn on a page of an imported document, shared with the position plans; a 1.0 source -- Gian's, kept in the example project as the migration fixture -- is read as 2.0 and nothing is written; turning a page turns the fire plans on it (`rotate_source`) with the position plans (calc/domains/plan_pages.py); and a position plan archived while fire plans follow it detaches them (`detach`).

Nothing is delimited by the program any more (the engineer's decision of 2026-10-05): the last test holds that the detection is gone rather than asleep.

The sheet is drawn at PER_M sheet units to the metre. Everything measured is written in metres and turned into sheet units by `m`.
"""

TIER = "fast"  # tests/run_tests.py --fast

import copy
import json
import math
import re
import xml.etree.ElementTree as ElementTree
from pathlib import Path

import conftest
from conftest import ROOT

import validation
from domains import figure_style, fire, fire_svg, plan
from domains import plan_documents as documents
from domains import plan_pages
from i18n import strings
from norms import vkf
import project

PLANS = project.Project.load(ROOT / "tests" / "projet-exemple" / "Exemple.woodcore").plans_dir   # 000-Woodcore/sources/ since the layout by folders (issue #64)
FIRE = project.Project.load(ROOT / "tests" / "projet-exemple" / "Exemple.woodcore").fire_dir

PER_M = 50


def m(metres):
    """Metres as sheet units."""
    return int(round(metres * PER_M))


W, H = m(20), m(12)
SQUARE = [[0, 0], [100, 0], [100, 100], [0, 100]]


def _source(**more):
    source = {
        "schema_version": "2.0", "id": "EG", "label": "", "zones": [],
        "sheet": {"width": W, "height": H},
        "scale": {"mode": "calibration", "points": [[0, 0], [m(10), 0]], "length_m": 10},
    }
    source.update(more)
    return source


def _frame(source):
    return fire.frame_of(source, {})[0]


def _invalid(source, word):
    try:
        fire.check_source(source, "t")
    except validation.ValidationError as exc:
        assert word in str(exc), f"refused, but without {word!r}: {exc}"
        return
    raise AssertionError(f"accepted -- expected a refusal naming {word!r}")


def _door(kind="swing", points=((0, 0), (40, 0)), side=1, **more):
    return {"id": "T1", "kind": kind, "points": [list(p) for p in points], "side": side, **more}


def _everything():
    """A plan that draws one of each thing, and a draft surface beside them."""
    return _source(
        zones=[{"id": "Z1", "kind": "horizontal", "points": [[100, 100], [600, 100], [600, 160], [100, 160]]},
               {"id": "Z2", "kind": "vertical", "label": "Treppenhaus", "points": [[20, 100], [100, 100], [100, 300], [20, 300]]},
               {"id": "Z3", "kind": "clear", "points": [[300, 100], [400, 100], [400, 160], [300, 160]]},
               {"id": "Z4", "points": [[700, 300], [800, 300], [800, 400], [700, 400]]}],
        walls=[{"id": "W1", "class": "EI 30", "points": [[100, 95], [600, 95]]},
               {"id": "W2", "class": "EI 60-RF1", "points": [[20, 100], [20, 300], [100, 300]]}],
        doors=[_door("swing", ((100, 100), (100, 150)), 1, id="T1", **{"class": "EI 30"}),
               _door("slide", ((450, 95), (500, 95)), -1, id="T2", **{"class": "E 30"}),
               _door("swing", ((200, 160), (240, 160)), 1, id="T3")],
        routes=[{"id": "F1", "points": [[580, 130], [120, 130]]}],
        exits=[{"id": "N1", "points": [[60, 280], [60, 340]]}],
        widths=[{"id": "B1", "points": [[250, 100], [250, 160]]}],
        legend={"x": 650, "y": 20},
    )


# --- the source ---------------------------------------------------------------------

def test_a_plan_follows_a_position_plan_or_carries_its_own_frame_never_both():
    fire.check_source(fire.new_source("EG", plan_id="Pavillon"), "t")
    fire.check_source(fire.new_source("EG"), "t")
    both = fire.new_source("EG", plan_id="Pavillon")
    both["sheet"] = {"width": 100, "height": 100}
    _invalid(both, "never both")
    neither = fire.new_source("EG")
    del neither["sheet"]
    _invalid(neither, "names no position plan")


def test_a_frame_of_its_own_is_checked_as_a_position_plans_is():
    source = _source(crop={"x": -50, "y": 0, "w": 10, "h": 10})
    _invalid(source, "crop leaves the sheet")


def test_a_surface_is_an_outline_of_one_of_the_sheets_three_kinds_or_a_draft():
    square = [[0, 0], [10, 0], [10, 10], [0, 10]]
    for kind in ("vertical", "horizontal", "clear"):
        fire.check_source(_source(zones=[{"id": "Z1", "kind": kind, "points": square}]), "t")
    # a surface drawn before the kinds existed states none, and is read
    fire.check_source(_source(zones=[{"id": "Z1", "points": square, "holes": [[[2, 2], [4, 2], [4, 4]]]}]), "t")
    _invalid(_source(zones=[{"id": "Z1", "kind": "sprinkler", "points": square}]), "kind 'sprinkler'")
    _invalid(_source(zones=[{"id": "Z1", "points": square[:2]}]), "at least three")
    _invalid(_source(zones=[{"id": "Z1", "points": square}, {"id": "Z1", "points": square}]), "used twice")
    _invalid(_source(zones=[{"id": "1Z", "points": square}]), "a letter")
    _invalid(_source(zones=[{"id": "Z1", "points": [[0, 0], [5, 0], [10, 0]]}]), "encloses no surface")
    _invalid(_source(zones=[{"id": "Z1", "points": [[0, 0], [0, 0], [10, 0], [10, 10]]}]), "same point")
    assert fire.SURFACES == ("vertical", "horizontal", "clear") and all(vkf.escape(kind) for kind in fire.SURFACES)


def test_a_wall_has_a_resistance_of_the_sheet_and_an_escape_route_two_points():
    square = [[0, 0], [10, 0], [10, 10], [0, 10]]
    good = _source(zones=[{"id": "Z1", "points": square}],
                   walls=[{"id": "W1", "class": "EI 30", "points": [[0, 0], [10, 0], [10, 10]]}],
                   routes=[{"id": "F1", "points": [[1, 1], [9, 1]], "text": "35 m"}])
    fire.check_source(good, "t")
    _invalid(_source(walls=[{"id": "W1", "class": "EI 45", "points": [[0, 0], [10, 0]]}]), "class 'EI 45'")
    _invalid(_source(walls=[{"id": "W1", "class": "EI 30", "points": [[0, 0]]}]), "at least two")
    _invalid(_source(walls=[{"id": "W1", "class": "EI 30", "points": [[0, 0], [0, 0]]}]), "same point")
    _invalid(_source(routes=[{"id": "F1", "points": [[0, 0]]}]), "at least two")
    # an id is unique in the whole plan, not in its collection
    _invalid(_source(zones=[{"id": "Z1", "points": square}], walls=[{"id": "Z1", "class": "EI 30", "points": [[0, 0], [10, 0]]}]), "used twice")
    _invalid(_source(walls=[{"id": "W1", "class": "EI 30", "points": [[0, 0], [10, 0]]}], routes=[{"id": "W1", "points": [[0, 0], [10, 0]]}]), "used twice")


def test_a_door_has_a_kind_two_points_a_side_and_a_resistance_the_sheet_gives_a_door_or_none():
    assert vkf.door_classes() == ["EI 30", "E 30"]
    for kind in ("swing", "slide"):
        fire.check_source(_source(doors=[_door(kind)]), "t")   # without a fire resistance
        for cls in vkf.door_classes():
            fire.check_source(_source(doors=[_door(kind, **{"class": cls})]), "t")
    _invalid(_source(doors=[_door("revolving")]), "kind 'revolving'")
    # a wall may be EI 60; the sheet gives no door of that class
    _invalid(_source(doors=[_door(**{"class": "EI 60"})]), "class 'EI 60'")
    for side in (0, 2, True, 0.5):
        _invalid(_source(doors=[_door(side=side)]), "side")
    _invalid(_source(doors=[_door(points=((0, 0), (40, 0), (40, 40)))]), "exactly 2")
    _invalid(_source(doors=[_door(points=((0, 0), (0, 0)))]), "same point")
    _invalid(_source(walls=[{"id": "T1", "class": "EI 30", "points": [[0, 0], [10, 0]]}], doors=[_door()]), "used twice")


def test_an_exit_and_a_width_have_exactly_two_points_and_a_legend_a_place():
    fire.check_source(_everything(), "t")
    _invalid(_source(exits=[{"id": "N1", "points": [[0, 0], [10, 0], [20, 0]]}]), "exactly 2")
    _invalid(_source(exits=[{"id": "N1", "points": [[5, 5], [5, 5]]}]), "same point")
    _invalid(_source(widths=[{"id": "B1", "points": [[0, 0]]}]), "exactly 2")
    _invalid(_source(exits=[{"id": "N1", "points": [[0, 0], [10, 0]]}], widths=[{"id": "N1", "points": [[0, 0], [10, 0]]}]), "used twice")
    _invalid(_source(legend={"x": 10}), "legend")
    _invalid(_source(legend={"x": "left", "y": 0}), "legend")


def test_a_source_file_is_named_after_its_id():
    folder = conftest.tmpdir("fire_source")
    path = folder / "EG.json"
    path.write_text(json.dumps(_source()), encoding="utf-8")
    assert fire.read_source(path)["id"] == "EG"
    other = folder / "OG.json"
    other.write_text(json.dumps(_source()), encoding="utf-8")
    try:
        fire.read_source(other)
    except validation.ValidationError as exc:
        assert "must agree" in str(exc)
    else:
        raise AssertionError("a file named after another id was read")


# --- the frame ----------------------------------------------------------------------

def test_a_plan_that_follows_a_position_plan_takes_its_frame_afresh():
    frames = fire.plan_frames(PLANS)
    assert "Pavillon" in frames
    source = fire.new_source("EG", plan_id="Pavillon")
    frame, problem = fire.frame_of(source, frames)
    assert problem is None
    assert frame["sheet"] == frames["Pavillon"]["sheet"] and frame["background"] == frames["Pavillon"]["background"]
    assert set(frame) <= set(fire.FRAME_KEYS)
    # the position plan's crop changes: the fire-protection plan's does, with nothing written into it
    moved = copy.deepcopy(frames)
    moved["Pavillon"]["crop"] = {"x": 1, "y": 2, "w": 3, "h": 4}
    assert fire.frame_of(source, moved)[0]["crop"] == {"x": 1, "y": 2, "w": 3, "h": 4}
    assert plan.crop_of(fire.frame_of(source, moved)[0])["w"] == 3.0


def test_a_position_plan_that_is_gone_is_a_note_and_an_empty_sheet():
    frame, problem = fire.frame_of(fire.new_source("EG", plan_id="Nirgends"), {})
    assert problem is not None and problem.code == "fire_plan_gone" and problem.args["plan"] == "Nirgends"
    assert frame == {"sheet": dict(plan.BLANK_SHEET)}
    notes = fire.warnings(fire.new_source("EG", plan_id="Nirgends"), {})
    assert [note.code for note in notes] == ["fire_plan_gone"]


def test_a_plan_with_a_frame_of_its_own_answers_with_it():
    source = _source()
    frame, problem = fire.frame_of(source, {"EG": {"sheet": {"width": 1, "height": 1}}})
    assert problem is None and frame["sheet"] == {"width": W, "height": H}
    assert abs(fire.per_m(frame) - PER_M) < 1e-9
    assert abs(fire.drawing_unit(frame) - W / 850) < 1e-9


def test_what_should_be_looked_at_is_said_and_stops_nothing():
    unscaled = _source()
    del unscaled["scale"]
    assert [note.code for note in fire.warnings(unscaled, {})] == ["fire_no_scale"]
    outside = _source(zones=[{"id": "Z1", "points": [[W + 100, 0], [W + 200, 0], [W + 200, 50]]}])
    notes = fire.warnings(outside, {})
    assert [note.code for note in notes] == ["fire_zone_outside"] and notes[0].args["zone"] == "Z1"
    assert fire.warnings(_source(), {}) == []


# --- ids and what lies under a click -------------------------------------------------

def test_a_number_is_never_given_twice_and_each_collection_has_its_letter():
    source = _source(zones=[{"id": "Z1", "points": SQUARE}, {"id": "Z7", "points": SQUARE}, {"id": "Flur", "points": SQUARE}],
                     walls=[{"id": "W4", "class": "EI 30", "points": [[0, 50], [100, 50]]}])
    assert fire.next_id(source, "zones") == "Z8" and fire.next_id(source, "zones", taken=["Z8", "Z9"]) == "Z10"
    assert fire.next_id(source, "walls") == "W5" and fire.next_id(source, "walls", taken=["W5"]) == "W6"
    assert [fire.next_id(_source(), collection) for collection in ("zones", "walls", "doors", "routes", "exits", "widths")] == ["Z1", "W1", "T1", "F1", "N1", "B1"]
    assert set(fire.PREFIXES) == set(fire.ENTRY_COLLECTIONS) and len(set(fire.PREFIXES.values())) == len(fire.ENTRY_COLLECTIONS), "two collections share a letter"   # the texts' X since issue #43
    assert fire.entry_of(source, "W4") == ("walls", 0) and fire.entry_of(source, "Flur") == ("zones", 2) and fire.entry_of(source, "Z9") is None


def test_a_click_takes_what_is_drawn_on_top():
    source = _source(zones=[{"id": "Z1", "kind": "horizontal", "points": [[0, 0], [400, 0], [400, 200], [0, 200]]}],
                     walls=[{"id": "W1", "class": "EI 30", "points": [[0, 100], [400, 100]]}],
                     doors=[_door("swing", ((100, 100), (140, 100)), 1, id="T1")],
                     routes=[{"id": "F1", "points": [[10, 100], [390, 100]]}],
                     exits=[{"id": "N1", "points": [[300, 100], [360, 100]]}],
                     widths=[{"id": "B1", "points": [[330, 80], [330, 120]]}])
    # at (330, 100) everything lies one on another: the width, the exit, the route, the wall, the surface
    assert fire.hit(source, (330, 100), 2) == "B1"
    assert fire.hit(source, (310, 100), 2) == "N1"
    assert fire.hit(source, (200, 100), 2) == "F1"
    assert fire.hit(source, (110, 110), 2) == "T1", "a door is taken anywhere inside its quarter disc"
    assert fire.hit(source, (200, 104), 1) == "Z1" and fire.hit(source, (200, 104), 1, band=10) == "W1", "a wall is taken anywhere on its band"
    assert fire.hit(source, (50, 30), 2) == "Z1"
    assert fire.hit(source, (500, 500), 2) is None
    # a collection the plan does not carry is no error
    assert fire.hit(_source(), (10, 10), 2) is None


def test_a_click_takes_the_smallest_surface_under_it_and_an_island_is_not_the_surface():
    hall = {"id": "Z1", "points": [[0, 0], [100, 0], [100, 100], [0, 100]], "holes": [[[40, 40], [60, 40], [60, 60], [40, 60]]]}
    core = {"id": "Z2", "points": [[40, 40], [60, 40], [60, 60], [40, 60]]}
    source = _source(zones=[hall, core])
    assert fire.hit_zone(source, (10, 10)) == 0
    assert fire.hit_zone(source, (50, 50)) == 1
    assert fire.hit_zone(_source(zones=[hall]), (50, 50)) is None
    assert fire.hit_zone(source, (W - 10, H - 10)) is None
    assert abs(fire.zone_area(hall) - (10000 - 400)) < 1e-9
    assert abs(fire.area_m2(core, 10) - 4.0) < 1e-9 and fire.area_m2(core, None) is None


def test_a_surfaces_name_is_written_inside_it():
    ell = {"id": "Z1", "points": [[0, 0], [100, 0], [100, 20], [20, 20], [20, 100], [0, 100]]}
    assert fire.inside(fire.label_point(ell), ell)
    ring = {"id": "Z2", "points": [[0, 0], [100, 0], [100, 100], [0, 100]], "holes": [[[20, 20], [80, 20], [80, 80], [20, 80]]]}
    assert fire.inside(fire.label_point(ring), ring)


# --- the escape routes' three marks ----------------------------------------------------

def test_an_escape_route_writes_its_length_or_what_the_engineer_typed():
    route = {"id": "F1", "points": [[0, 0], [m(30), 0], [m(30), m(4.6)]]}
    assert abs(fire.route_length_m(route, PER_M) - 34.6) < 1e-9
    assert fire.route_text(route, PER_M) == "34.6 m"
    assert fire.route_text({"id": "F2", "points": [[0, 0], [m(35), 0]]}, PER_M) == "35 m"
    assert fire.route_text(dict(route, text="max. 35 m"), PER_M) == "max. 35 m"
    assert fire.route_length_m(route, None) is None and fire.route_text(route, None) == ""


def test_a_width_writes_what_it_measures_to_the_centimetre_as_the_sheet_does():
    width = {"id": "B1", "points": [[0, 0], [0, m(1.2)]]}
    assert abs(fire.width_m(width, PER_M) - 1.2) < 1e-9
    assert fire.width_text(width, PER_M) == "1.20 m", "the sheet writes «1.20 m», not «1.2 m»"
    assert fire.width_text({"id": "B2", "points": [[0, 0], [m(0.9), 0]]}, PER_M) == "0.90 m"
    assert fire.width_text(dict(width, text="min. 1.20 m"), PER_M) == "min. 1.20 m"
    assert fire.width_m(width, None) is None and fire.width_text(width, None) == ""


def test_the_exit_is_the_sheets_arrow_between_its_two_points():
    shape = fire.exit_shape([[100, 200], [200, 200]])
    assert len(shape) == 7 and shape[3] == (200, 200), "the tip is the second point"
    proportions = vkf.shape("exit")
    xs, ys = [x for x, _y in shape], [y for _x, y in shape]
    assert abs(min(xs) - 100) < 1e-9 and abs(max(xs) - 200) < 1e-9, "the arrow is as long as its two points are apart"
    assert abs((max(ys) - min(ys)) - proportions["head_width"] * 100) < 1e-9
    assert abs((shape[0][1] - shape[6][1]) - proportions["shaft_width"] * 100) < 1e-9
    assert abs(shape[1][0] - (100 + proportions["shaft_length"] * 100)) < 1e-9
    # symmetric about its axis, whatever way it points
    assert all(abs((shape[i][1] - 200) + (shape[6 - i][1] - 200)) < 1e-9 for i in range(3))
    turned = fire.exit_shape([[100, 200], [100, 300]])
    assert abs(fire.ring_area(turned) - fire.ring_area(shape)) < 1e-6 and turned[3] == (100, 300)
    # the pictogram itself: «Sortie de secours.jpeg» is 825 wide, its shaft 500 long and 200 wide, its head 590 wide
    assert abs(proportions["shaft_length"] - 500 / 825) < 1e-3 and abs(proportions["shaft_width"] - 200 / 825) < 1e-3 and abs(proportions["head_width"] - 590 / 825) < 1e-3


# --- the doors ---------------------------------------------------------------------------

def test_a_swing_door_is_a_quarter_disc_on_its_hinge_swept_to_its_side():
    door = _door("swing", ((100, 100), (140, 100)), 1)
    shape = fire.door_shape(door)
    assert shape[0] == (100, 100), "the first corner is the hinge"
    assert all(abs(a - b) < 1e-9 for a, b in zip(shape[1], (140, 100))), "then the end of the closed leaf, on the other jamb"
    assert all(abs(math.dist(p, (100, 100)) - 40) < 1e-9 for p in shape[1:]), "every point of the arc is a leaf's length from the hinge"
    opened = fire.door_open_end(door)
    assert all(abs(a - b) < 1e-9 for a, b in zip(shape[-1], opened)) and all(abs(a - b) < 1e-9 for a, b in zip(opened, (100, 140))), "side 1 is the side turned a quarter towards +y"
    assert abs(fire.ring_area(shape) - math.pi * 40 * 40 / 4) < 0.01 * math.pi * 400, "a quarter of the disc, to the arc's straight pieces"
    other = fire.door_shape(dict(door, side=-1))
    assert all(abs(a - b) < 1e-9 for a, b in zip(other[-1], (100, 60))), "side -1 opens to the other side of the wall"
    assert abs(fire.door_width_m(door, PER_M) - 0.8) < 1e-9 and fire.door_width_m(door, None) is None


def test_a_sliding_door_is_the_sheets_flat_arrow_along_the_wall():
    door = _door("slide", ((300, 100), (100, 100)), 1)
    shape = fire.door_shape(door)
    proportions = vkf.shape("slide")
    assert len(shape) == 5 and shape[0] == (100, 100) and shape[-1] == (300, 100), "from the tip, where it slides to, back to where it stands closed"
    length = 200
    # the line 300 -> 100 runs towards -x, so its side 1 is towards -y: the bar and the half head rise there
    assert abs(shape[1][1] - (100 - proportions["head_height"] * length)) < 1e-9 and abs(shape[1][0] - (100 + proportions["head_length"] * length)) < 1e-9
    assert abs(shape[2][1] - (100 - proportions["bar"] * length)) < 1e-9 and abs(shape[3][1] - shape[2][1]) < 1e-9 and abs(shape[3][0] - 300) < 1e-9
    below = fire.door_shape(dict(door, side=-1))
    assert below[1][1] > 100 and below[3][1] > 100
    # the pictogram itself: «Porte coulissante EI 30.jpeg» is 1771 long, its bar 118 thick, its half head 354 long and 296 high
    assert abs(proportions["bar"] - 118 / 1771) < 1e-3 and abs(proportions["head_length"] - 354 / 1771) < 1e-3 and abs(proportions["head_height"] - 296 / 1771) < 1e-3


def test_the_third_click_says_the_side_a_door_opens_to():
    a, b = (100, 100), (200, 100)
    assert fire.side_of(a, b, (150, 180)) == 1 and fire.side_of(a, b, (150, 20)) == -1
    assert fire.side_of(a, b, (150, 100)) == 1, "on the line itself: one of the two, never 0"
    assert fire.side_of(b, a, (150, 180)) == -1, "the line turned round counts its sides the other way"
    # the door then opens where the click was
    for click in ((150, 180), (150, 20)):
        door = _door("swing", (a, b), fire.side_of(a, b, click))
        assert fire.side_of(a, b, fire.door_open_end(door)) == fire.side_of(a, b, click)


def test_a_door_flipped_opens_the_other_way_and_twice_flipped_is_itself():
    door = _door("swing", ((100, 100), (140, 100)), 1, **{"class": "EI 30"})
    before = copy.deepcopy(door)
    a, b = door["points"]
    sided = fire.door_flipped(door, "side")
    assert sided["points"] == door["points"] and sided["side"] == -1
    assert all(abs(p - q) < 1e-9 for p, q in zip(fire.door_open_end(sided), (100, 60)))
    hinged = fire.door_flipped(door, "hinge")
    assert hinged["points"] == [[140, 100], [100, 100]], "the hinge is on the other jamb"
    # ...and it still opens to the same side of the wall: the open leaf now stands at the other jamb, on the side it stood on
    assert all(abs(p - q) < 1e-9 for p, q in zip(fire.door_open_end(hinged), (140, 140)))
    assert fire.side_of(a, b, fire.door_open_end(hinged)) == fire.side_of(a, b, fire.door_open_end(door))
    assert door == before, "door_flipped changed the door it was given"
    for what in ("hinge", "side"):
        twice = fire.door_flipped(fire.door_flipped(door, what), what)
        assert twice == door, what
        assert fire.door_flipped(door, what)["id"] == "T1" and fire.door_flipped(door, what)["class"] == "EI 30"
        fire.check_source(_source(doors=[fire.door_flipped(door, what)]), "t")
    try:
        fire.door_flipped(door, "upside down")
    except ValueError as exc:
        assert "hinge" in str(exc)
    else:
        raise AssertionError("an unknown way to flip a door was accepted")


# --- the legend ---------------------------------------------------------------------------

def test_the_legend_lists_what_is_drawn_in_the_sheets_order_and_nothing_else():
    assert fire.legend_rows(_source()) == []
    rows = fire.legend_rows(_everything())
    assert [(row["symbol"], row["kind"], row["class"]) for row in rows] == [
        ("wall", None, "EI 60-RF1"), ("wall", None, "EI 30"),          # the sheet's order, not the order they were drawn in
        ("surface", "vertical", None), ("surface", "horizontal", None), ("surface", "clear", None),
        ("exit", None, None), ("length", None, None), ("width", None, None),
        ("door", "swing", "EI 30"), ("door", "slide", "E 30"), ("door", "swing", None),
    ]
    by_symbol = {(row["symbol"], row["kind"], row["class"]): row for row in rows}
    assert by_symbol[("wall", None, "EI 30")]["label"] == "Feuerwiderstand EI 30" and by_symbol[("wall", None, "EI 30")]["rgb"] == [255, 191, 0]
    assert by_symbol[("surface", "clear", None)]["label"] == "freizuhaltende Fläche"
    assert by_symbol[("exit", None, None)]["label"] == "Notausgang" and by_symbol[("length", None, None)]["label"] == "Fluchtweglänge" and by_symbol[("width", None, None)]["label"] == "Fluchtwegbreite"
    assert by_symbol[("door", "slide", "E 30")]["label"] == "Schiebetüre / Schiebetor E 30" and by_symbol[("door", "slide", "E 30")]["rgb"] == [250, 186, 252]
    # a door without a fire resistance is no symbol of the sheet: the engine names it
    plain = by_symbol[("door", "swing", None)]
    assert plain["label"] is None and plain["rgb"] is None
    assert fire_svg.legend_text(plain, "fr") == strings.text("fire.door.swing", "fr") == "Porte sans résistance au feu"
    # a draft surface, which states no kind, is in no legend; and a wall drawn twice is listed once
    only = _source(zones=[{"id": "Z1", "points": SQUARE}],
                   walls=[{"id": "W1", "class": "E 30", "points": [[0, 0], [10, 0]]}, {"id": "W2", "class": "E 30", "points": [[0, 5], [10, 5]]}])
    assert [(row["symbol"], row["class"]) for row in fire.legend_rows(only)] == [("wall", "E 30")]


def test_every_word_of_the_legend_is_in_the_glossary_in_three_languages():
    labels = [row["label"] for row in vkf.resistances()] + [vkf.escape(key)["label"] for key in vkf.ESCAPE_KEYS]
    labels += [vkf.door(kind, cls)["label"] for kind in vkf.DOOR_KINDS for cls in vkf.door_classes()]
    known = strings.terms()
    for label in labels:
        if label == "RF1":
            continue   # the class's own name, the same in every language: no word to translate
        assert label in known, f"the glossary does not carry {label!r}"
        assert strings.term(label, "fr") != label and strings.term(label, "en") != label, f"{label!r} is not translated"
    for key in ("fire.legend", "fire.door.swing", "fire.door.slide"):
        assert all(strings.text(key, lang).strip() for lang in strings.LANGUAGES)
    assert strings.term("Türe / Tor EI 30", "fr") == "Porte / portail EI 30" and strings.term("Notausgang", "fr") == "Sortie de secours"


def test_the_legend_stands_where_it_is_put_and_is_as_large_as_what_it_lists():
    source = _everything()
    frame = _frame(source)
    assert fire_svg.legend_box(_source(), frame) is None, "a plan that states no legend shows none"
    x, y, width, height = fire_svg.legend_box(source, frame, "de")
    assert (x, y) == (650.0, 20.0)
    unit = fire.drawing_unit(frame)
    longest = max(fire_svg.text_width(fire_svg.legend_text(row, "de"), fire_svg.LEGEND_TEXT * unit) for row in fire.legend_rows(source))
    assert width >= longest + (fire_svg.LEGEND_SWATCH[0] + fire_svg.LEGEND_GAP + 2 * fire_svg.LEGEND_PAD) * unit - 1e-9, "the frame is narrower than its longest line"
    fewer = dict(source, doors=[], widths=[])
    assert fire_svg.legend_box(fewer, frame, "de")[3] < height, "fewer rows, and the box is no shorter"
    assert abs((height - fire_svg.legend_box(fewer, frame, "de")[3]) - 4 * fire_svg.LEGEND_ROW * unit) < 1e-6
    # nothing drawn: the title alone, in a box that still has a size to be grabbed by
    empty = fire_svg.legend_box(_source(legend={"x": 5, "y": 5}), frame, "fr")
    assert empty[2] > 0 and empty[3] > 0
    place = fire.legend_default(frame)
    crop = plan.crop_of(frame)
    assert crop["x"] < place["x"] < crop["x"] + crop["w"] / 4 and crop["y"] < place["y"] < crop["y"] + crop["h"] / 4
    fire.check_source(dict(_source(), legend=place), "t")


# --- the drawing ------------------------------------------------------------------------

def _texts(svg):
    return re.findall(r"<text[^>]*>([^<]*)</text>", svg)


def test_the_drawing_is_valid_and_kept_to_what_both_renderers_read():
    source = _everything()
    for editing in (False, True):
        svg = fire_svg.render(source, _frame(source), editing=editing, lang="fr")
        ElementTree.fromstring(svg)
        for banned in ("<pattern", "clip-path", "<clipPath", "<marker", "style=", "<tspan", "paint-order"):
            assert banned not in svg, f"{banned} is not SVG Tiny 1.2"
        # no arc command: a door's quarter circle is straight pieces
        for path in re.findall(r'<path d="([^"]*)"', svg):
            assert not re.search(r"[AaCcQqSsTt]", path), path


def test_a_surface_is_tinted_in_its_kinds_colour_and_a_draft_is_the_editors_alone():
    source = {k: v for k, v in _everything().items() if k != "legend"}   # the legend draws a small surface of each kind too
    frame = _frame(source)
    printed = fire_svg.render(source, frame)
    assert f'fill="{fire_svg.colour_of("horizontal")}" fill-opacity="{fire.OPACITY["zones"]}"' in printed
    assert f'fill="{fire_svg.colour_of("vertical")}" fill-opacity="{fire.OPACITY["zones"]}"' in printed
    assert fire_svg.colour_of("vertical") == "#009900" and fire_svg.colour_of("horizontal") == "#cafe96" and fire_svg.colour_of("clear") == "#9fff7f"
    # the surface to be kept clear is hatched, each line cut to its outline
    hatch = re.findall(rf'<line x1="([\d.]+)" y1="([\d.]+)" x2="([\d.]+)" y2="([\d.]+)" stroke="{fire_svg.colour_of("clear")}"', printed)
    assert len(hatch) >= 5, "a surface to be kept clear without its hatching"
    for x1, y1, x2, y2 in hatch:
        assert 300 - 0.01 <= float(x1) <= 400.01 and 300 - 0.01 <= float(x2) <= 400.01 and 99.99 <= float(y1) <= 160.01 and 99.99 <= float(y2) <= 160.01, "the hatching leaves its surface"
    assert fire_svg.ZONE_COLOUR not in printed, "a draft surface is printed"
    assert "Treppenhaus" in _texts(printed) and "Z4" not in _texts(printed) and "Z1" not in _texts(printed), "a surface writes its name, never its id"
    editing = fire_svg.render(source, frame, editing=True)
    assert fire_svg.ZONE_COLOUR in editing and "Z4" in _texts(editing), "the editor does not show the draft"


def test_walls_doors_and_the_escape_routes_marks_are_drawn_in_the_sheets_colours():
    source = {k: v for k, v in _everything().items() if k != "legend"}
    frame = _frame(source)
    svg = fire_svg.render(source, frame)
    band = fire.band_width(frame)
    assert abs(band - 0.25 * PER_M) < 1e-9
    assert f'stroke="{fire_svg.wall_colour("EI 30")}" stroke-width="{fire_svg._f(band)}"' in svg and fire_svg.wall_colour("EI 30") == "#ffbf00"
    # a door with a resistance is filled with it; one without is an outline and no fill
    assert fire_svg.door_colour(source["doors"][0]) == "#ffbf00" and fire_svg.door_colour(source["doors"][1]) == "#fabafc" and fire_svg.door_colour(source["doors"][2]) is None
    polygons = re.findall(r'<polygon points="[^"]*" fill="([^"]*)"', svg)
    assert polygons.count("#ffbf00") == 1 and polygons.count("#fabafc") == 1
    plain = [line for line in svg.splitlines() if line.startswith("<polyline") and f'stroke="{fire_svg.INK}"' in line]
    assert len(plain) == 1 and 'fill="none"' in plain[0], "a door without a fire resistance is not drawn as an outline"
    # the exit: the thick green arrow; the length: the thin one with what it measures; the width: its figure
    assert f'<polygon points="{fire_svg._pts(fire.exit_shape(source["exits"][0]["points"]))}" fill="#009900"' in svg
    assert "9.2 m" in _texts(svg), "the escape route's length"
    assert "1.20 m" in _texts(svg), "the width, to the centimetre"
    assert "stroke-dasharray" not in svg, "the line a width is measured along is the editor's"
    assert "stroke-dasharray" in fire_svg.render(source, frame, editing=True)
    # without a scale nothing is measured, and nothing is written
    unscaled = {k: v for k, v in source.items() if k != "scale"}
    assert _texts(fire_svg.render(unscaled, _frame(unscaled))) == ["Treppenhaus"]


def test_a_text_is_never_upside_down_and_reads_from_the_bottom_up_along_a_vertical():
    frame = _frame(_source())
    unit = fire.drawing_unit(frame)
    down = fire_svg.width_label({"points": [[100, 100], [100, 160]]}, frame, unit)
    up = fire_svg.width_label({"points": [[100, 160], [100, 100]]}, frame, unit)
    assert down[3] == up[3] == -90, "across a horizontal passage the width reads from the bottom up, whichever way it was clicked"
    assert (down[1], down[2]) == (100, 130), "at the middle of what it measures"
    for end in ((300, 100), (300, 300), (100, 300), (-100, 300), (-100, 100), (-100, -100), (100, -100), (300, -100)):
        label = fire_svg.route_label({"points": [[100, 100], list(end)]}, frame, unit)
        assert -90 <= label[3] < 90, (end, label[3])
    assert fire_svg.width_label({"points": [[0, 0], [0, 60]]}, _frame({"sheet": {"width": W, "height": H}}), unit) is None, "no scale and no text: nothing to write"


def test_the_legend_is_written_in_the_language_it_is_asked_for():
    source = _everything()
    frame = _frame(source)
    german, french, english = (_texts(fire_svg.render(source, frame, lang=lang)) for lang in ("de", "fr", "en"))
    assert "Legende" in german and "Feuerwiderstand EI 30" in german and "Notausgang" in german and "Türe / Tor EI 30" in german
    assert "Légende" in french and "Résistance au feu EI 30" in french and "Sortie de secours" in french and "Voie d'évacuation horizontale" in french and "Porte sans résistance au feu" in french
    assert "Legend" in english and "Emergency exit" in english
    assert "Feuerwiderstand EI 30" not in french, "the French legend still speaks German"
    assert _texts(fire_svg.render(source, frame)) == german, "German is the language of a drawing that is asked for none"
    # the legend's own two placeholders are the sheet's
    assert fire_svg.LEGEND_LENGTH in german and fire_svg.LEGEND_WIDTH in german
    without = {k: v for k, v in source.items() if k != "legend"}
    assert "Legende" not in _texts(fire_svg.render(without, frame))
    # the legend is drawn over everything: its frame comes after every mark of the plan
    svg = fire_svg.render(source, frame)
    assert svg.rindex(f'fill="{fire_svg.GROUND}" stroke="{fire_svg.INK}"') > svg.index(fire_svg._pts(fire.exit_shape(source["exits"][0]["points"])))


# --- how large, how opaque, and where a text stands ---------------------------------------

def _strokes(svg, colour):
    """The widths of the strokes drawn in `colour`."""
    return [float(w) for w in re.findall(rf'stroke="{colour}" stroke-width="([0-9.]+)"', svg)]


def test_the_plans_factors_are_the_position_plans_and_a_plan_has_no_point_to_scale():
    assert fire.STYLE_KEYS == ("line", "text") and fire.STYLE_RANGE == figure_style.RANGE
    fire.check_source(_source(style={"line": 2, "text": 0.5}), "t")
    fire.check_source(_source(style={}), "t")
    _invalid(_source(style={"point": 1.5}), "style.point means nothing here")
    _invalid(_source(style={"line": 4}), "from 0.25 to 3")
    _invalid(_source(style={"thick": 2}), "is not a factor")
    assert fire.drawing_factors(_source()) == {"line": 1.0, "point": 1.0, "text": 1.0}
    # a plan that states no factor, and one that states 1 for both, are drawn alike to the byte: the arithmetic adds nothing of its own
    source = _everything()
    frame = _frame(source)
    assert fire_svg.render(source, frame, editing=True) == fire_svg.render(dict(source, style={"line": 1, "text": 1}), frame, editing=True)


def test_an_entry_states_only_the_factors_it_is_drawn_with():
    """figure_style's table, the fire-protection plans' rows: a wall is a band and writes nothing, a width is a figure and draws no line, an emergency exit is sized by its two points and states nothing at all."""
    assert figure_style.allowed("fire", "zones") == ("line", "text") and figure_style.allowed("fire", "routes") == ("line", "text")
    assert figure_style.allowed("fire", "walls") == ("line",) and figure_style.allowed("fire", "doors") == ("line",)
    assert figure_style.allowed("fire", "widths") == ("text",) and figure_style.allowed("fire", "exits") == ()
    wall = {"id": "W1", "class": "EI 30", "points": [[0, 0], [10, 0]]}
    fire.check_source(_source(walls=[dict(wall, style={"line": 2})]), "t")
    _invalid(_source(walls=[dict(wall, style={"text": 2})]), "drawn with line")
    _invalid(_source(widths=[{"id": "B1", "points": [[0, 0], [10, 0]], "style": {"line": 2}}]), "drawn with text")
    _invalid(_source(exits=[{"id": "N1", "points": [[0, 0], [10, 0]], "style": {"line": 2}}]), "states no factor of its own")
    _invalid(_source(walls=[dict(wall, style={"line": 0.1})]), "from 0.25 to 3")


def test_a_factor_multiplies_and_reaches_what_it_names_and_nothing_else():
    source = {k: v for k, v in _everything().items() if k != "legend"}
    frame = _frame(source)
    band = fire.band_width(frame)
    ei30, ei60 = fire_svg.wall_colour("EI 30"), fire_svg.wall_colour("EI 60-RF1")
    plain = fire_svg.render(source, frame)
    assert _strokes(plain, ei30) == [band] and _strokes(plain, ei60) == [band]
    # the plan's own factor reaches every wall; a wall's own multiplies it, for that wall alone
    doubled = fire_svg.render(dict(source, style={"line": 2}), frame)
    assert _strokes(doubled, ei30) == [2 * band] and _strokes(doubled, ei60) == [2 * band]
    own = copy.deepcopy(source)
    own["style"] = {"line": 2}
    own["walls"][0]["style"] = {"line": 1.5}
    drawn = fire_svg.render(own, frame)
    assert _strokes(drawn, ei30) == [3 * band] and _strokes(drawn, ei60) == [2 * band]
    assert fire.factors(own, own["walls"][0])["line"] == 3.0 and fire.factors(own, own["walls"][1])["line"] == 2.0
    # a click still takes a wall anywhere on the band it is now drawn with
    wide = _source(walls=[{"id": "W1", "class": "EI 30", "points": [[0, 100], [400, 100]], "style": {"line": 3}}])
    assert fire.hit(wide, (200, 100 + 0.4 * 3 * 10), 1, band=10) == "W1" and fire.hit(wide, (200, 100 + 0.6 * 3 * 10), 1, band=10) is None
    # the text factor reaches the texts and leaves the strokes alone
    sizes = lambda svg: sorted({float(s) for s in re.findall(r'font-size="([0-9.]+)"', svg)})
    larger = fire_svg.render(dict(source, style={"text": 2}), frame)
    assert sizes(larger) == [round(2 * s, 3) for s in sizes(plain)] and _strokes(larger, ei30) == [band]


def test_an_entry_is_drawn_as_opaque_as_it_says():
    assert fire.OPACITY["zones"] == 0.65 and all(fire.OPACITY[c] == 1.0 for c in ("walls", "doors", "routes", "exits"))
    assert fire.opacity_of("zones", {"kind": "horizontal"}) == 0.65 and fire.opacity_of("zones", {"kind": "clear"}) == 1.0, "a surface to be kept clear is hatched, not tinted"
    assert fire.opacity_of("walls", {}) == 1.0 and fire.opacity_of("walls", {"opacity": 0.4}) == 0.4
    wall = {"id": "W1", "class": "EI 30", "points": [[0, 0], [100, 0]]}
    source = _source(walls=[dict(wall, opacity=0.4)], zones=[{"id": "Z1", "kind": "vertical", "points": SQUARE, "opacity": 0.3}],
                     exits=[{"id": "N1", "points": [[0, 50], [60, 50]], "opacity": 0.5}])
    fire.check_source(source, "t")
    svg = fire_svg.render(source, _frame(source))
    assert 'stroke-opacity="0.4"' in svg and 'fill-opacity="0.3"' in svg and 'fill-opacity="0.5"' in svg
    # a drawing nobody made translucent is written as it always was
    assert "stroke-opacity" not in fire_svg.render(_source(walls=[wall]), _frame(_source()))
    _invalid(_source(walls=[dict(wall, opacity=0)]), "from 0.1 to 1")
    _invalid(_source(walls=[dict(wall, opacity=1.2)]), "from 0.1 to 1")
    _invalid(_source(widths=[{"id": "B1", "points": [[0, 0], [10, 0]], "opacity": 0.5}]), "it is a text")
    assert "widths" not in fire.OPACITY


def test_a_text_moved_by_hand_follows_its_entry_and_is_grabbed_where_it_is_drawn():
    assert fire.TEXT_COLLECTIONS == ("zones", "routes", "widths")
    source = _source(routes=[{"id": "F1", "points": [[100, 300], [500, 300]]}], widths=[{"id": "B1", "points": [[300, 100], [300, 160]]}],
                     zones=[{"id": "Z1", "kind": "vertical", "label": "Treppe", "points": [[600, 100], [700, 100], [700, 200], [600, 200]]}])
    frame = _frame(source)
    home = {item["id"]: item for item in fire_svg.text_frames(source, frame)}
    assert set(home) == {"F1", "B1", "Z1"} and all(item["at"] == item["home"] for item in home.values())
    assert home["F1"]["text"] == "8 m" and home["B1"]["text"] == "1.20 m" and home["Z1"]["text"] == "Treppe"
    moved = copy.deepcopy(source)
    moved["routes"][0]["label_offset"] = [0, 60]
    fire.check_source(moved, "t")
    item = {i["id"]: i for i in fire_svg.text_frames(moved, frame)}["F1"]
    assert item["home"] == home["F1"]["home"] and item["at"] == (item["home"][0], item["home"][1] + 60)
    # from its own place, so the text follows its entry: the route moved, and the text with it
    for point in moved["routes"][0]["points"]:
        point[0] += 40
    later = {i["id"]: i for i in fire_svg.text_frames(moved, frame)}["F1"]
    assert later["at"] == (item["at"][0] + 40, item["at"][1])
    # a click lands on the text where it is drawn, and no longer where it was
    assert fire_svg.hit_text(moved, frame, later["at"])["id"] == "F1" and fire_svg.hit_text(moved, frame, later["home"]) is None
    assert fire_svg.hit_text(source, frame, home["B1"]["at"])["id"] == "B1", "a text turned with its line is still grabbed in its box"
    assert fire_svg.hit_text(source, frame, (10, 10)) is None
    # moved clear of its own height, it is tied back to its place by a leader in its own colour; in its place there is none
    leader = rf'<line x1="[0-9.]+" y1="[0-9.]+" x2="[0-9.]+" y2="[0-9.]+" stroke="{fire_svg.route_colour()}" stroke-width'
    assert len(re.findall(leader, fire_svg.render(moved, frame))) == 1 and not re.findall(leader, fire_svg.render(source, frame))
    _invalid(_source(walls=[{"id": "W1", "class": "EI 30", "points": [[0, 0], [10, 0]], "label_offset": [1, 1]}]), "it writes no text")
    _invalid(_source(routes=[{"id": "F1", "points": [[0, 0], [10, 0]], "label_offset": [1]}]), "label_offset")
    # a draft's id is a text of the editor alone
    draft = _source(zones=[{"id": "Z9", "points": SQUARE}])
    assert [i["id"] for i in fire_svg.text_frames(draft, frame, editing=True)] == ["Z9"] and fire_svg.text_frames(draft, frame) == []


def test_the_legend_has_a_size_of_its_own_and_may_be_left_out_of_the_figure():
    source = _everything()
    frame = _frame(source)
    x, y, width, height = fire_svg.legend_box(source, frame, "de")
    larger = copy.deepcopy(source)
    larger["legend"]["scale"] = 2
    fire.check_source(larger, "t")
    assert fire.legend_scale(source) == 1.0 and fire.legend_scale(larger) == 2.0
    box = fire_svg.legend_box(larger, frame, "de")
    assert box[:2] == (x, y) and abs(box[2] - 2 * width) < 1e-6 and abs(box[3] - 2 * height) < 1e-6, "the legend does not grow from its own corner"
    # the plan's own factors leave it alone: a legend reads the same whatever the plan's strokes and texts were set to
    assert fire_svg.legend_box(dict(source, style={"line": 3, "text": 3}), frame, "de") == (x, y, width, height)
    for scale in (0.1, 4):
        bad = copy.deepcopy(source)
        bad["legend"]["scale"] = scale
        _invalid(bad, "legend.scale")
    # between its two markers, so that the report can leave it out without the figure being drawn twice
    svg = fire_svg.render(source, frame)
    assert svg.count(fire_svg.LEGEND_OPEN) == 1 and svg.count(fire_svg.LEGEND_CLOSE) == 1 and svg.index(fire_svg.LEGEND_OPEN) < svg.index("Legende") < svg.index(fire_svg.LEGEND_CLOSE)
    without = re.sub(r"(?s)<!-- legend -->.*?<!-- /legend -->", "", svg)
    ElementTree.fromstring(without)
    assert "Legende" not in _texts(without) and "9.2 m" in _texts(without)
    assert fire_svg.LEGEND_OPEN not in fire_svg.render({k: v for k, v in source.items() if k != "legend"}, frame)


# --- a crop of its own on a plan that follows a position plan -----------------------------

def test_a_plan_that_follows_may_state_its_own_crop_and_nothing_else_of_the_frame():
    frames = fire.plan_frames(PLANS)
    source = fire.new_source("EG", plan_id="Pavillon")
    assert not fire.own_crop(source) and fire.frame_of(source, frames)[0]["crop"] == frames["Pavillon"]["crop"]
    source["crop"] = {"x": 300, "y": 400, "w": 200, "h": 150}
    fire.check_source(source, "t")
    frame, problem = fire.frame_of(source, frames)
    assert problem is None and fire.own_crop(source) and frame["crop"] == {"x": 300, "y": 400, "w": 200, "h": 150}
    assert frame["background"] == frames["Pavillon"]["background"] and frame["sheet"] == frames["Pavillon"]["sheet"], "the background and the sheet stay the position plan's"
    assert frames["Pavillon"]["crop"] != frame["crop"], "frame_of wrote the plan's own crop into the position plan's frame"
    assert fire.warnings(source, frames) and all(note.code != "fire_crop_outside" for note in fire.warnings(source, frames))
    # taken back, the position plan's is taken again
    del source["crop"]
    assert fire.frame_of(source, frames)[0]["crop"] == frames["Pavillon"]["crop"]
    # a background, a sheet or a scale of its own is still refused, and a crop that is no frame too
    for key, value in (("sheet", {"width": 10, "height": 10}), ("scale", {"mode": "ratio", "ratio": 100})):
        _invalid(dict(fire.new_source("EG", plan_id="Pavillon"), **{key: value}), "never both")
    _invalid(dict(fire.new_source("EG", plan_id="Pavillon"), crop={"x": 0, "y": 0, "w": 0, "h": 10}), "crop.w")
    # whether it lies on the sheet is the position plan's to say: a warning, never a refusal
    outside = dict(fire.new_source("EG", plan_id="Pavillon"), crop={"x": 1100, "y": 1100, "w": 500, "h": 500})
    fire.check_source(outside, "t")
    assert "fire_crop_outside" in [note.code for note in fire.warnings(outside, frames)]
    assert fire.own_crop(_source()), "a plan with a frame of its own always states its crop itself"


# --- the export ---------------------------------------------------------------------------

def _export_project(name, sources):
    """A project's folders for the export, in this run's temp folder: the fire-protection plans given, and the example project's position plans."""
    root = conftest.tmpdir(name)
    for source in sources:
        (root / "fire").mkdir(exist_ok=True)
        (root / "fire" / f"{source['id']}.json").write_text(json.dumps(source), encoding="utf-8")
    (root / "data").mkdir(exist_ok=True)
    return root


def test_a_plan_is_exported_with_its_figure_in_every_language_and_what_it_measures():
    own = _everything()
    root = _export_project("fire_export", [own])
    data, files, notes = fire.prepare(root / "fire", PLANS, root, root / "data", plans={})
    assert notes == [] and list(data["plans"]) == ["EG"] and data["schema_version"] == fire.EXPORT_SCHEMA_VERSION
    record = data["plans"]["EG"]
    assert record["figures"] == {lang: f"fire/EG-{lang}.svg" for lang in strings.LANGUAGES} and set(files) == set(record["figures"].values())
    assert "Legende" in _texts(files["fire/EG-de.svg"]) and "Légende" in _texts(files["fire/EG-fr.svg"]) and "Legend" in _texts(files["fire/EG-en.svg"])
    assert fire_svg.ZONE_COLOUR not in files["fire/EG-de.svg"], "the report's figure shows what only the editor does"
    assert record["legend"] is True and "background" not in record and "plan" not in record
    assert record["scale"] == {"mode": "calibration", "units_per_m": PER_M} and record["crop"] == {"x": 0, "y": 0, "w": W, "h": H}
    # the draft surface, which states no kind, is not exported; the three of a kind are, each with its area
    assert [zone["id"] for zone in record["zones"]] == ["Z1", "Z2", "Z3"] and record["zones"][0]["area_m2"] == 12.0 and record["zones"][1]["label"] == "Treppenhaus"
    assert record["walls"][0] == {"id": "W1", "class": "EI 30", "length_m": 10.0}
    assert record["doors"][0] == {"id": "T1", "kind": "swing", "class": "EI 30", "width_m": 1.0} and "class" not in record["doors"][2]
    assert record["routes"] == [{"id": "F1", "text": "9.2 m", "length_m": 9.2}] and record["widths"] == [{"id": "B1", "text": "1.20 m", "width_m": 1.2}] and record["exits"] == [{"id": "N1"}]
    validation.validate_structure(data, "fire")
    validation.validate_fire_business(data)
    # written, and written again unchanged; a plan that is gone takes its files with it
    fire.write(data, files, root / "data")
    assert sorted(p.name for p in (root / "data" / "fire").iterdir()) == ["EG-de.svg", "EG-en.svg", "EG-fr.svg"]
    assert json.loads((root / "data" / "fire.json").read_text(encoding="utf-8")) == data
    assert fire.export(root / "fire", PLANS, root, root / "data") == []
    (root / "fire" / "EG.json").unlink()
    fire.export(root / "fire", PLANS, root, root / "data")
    assert list((root / "data" / "fire").iterdir()) == [] and json.loads((root / "data" / "fire.json").read_text(encoding="utf-8")) == fire.empty()


def test_a_plan_without_a_scale_measures_nothing_and_what_an_entry_states_is_recorded():
    source = {k: v for k, v in _everything().items() if k != "scale"}
    source["walls"][0].update(style={"line": 1.5}, opacity=0.5)
    source["style"] = {"text": 2}
    root = _export_project("fire_export_unscaled", [source])
    data, _files, notes = fire.prepare(root / "fire", PLANS, root, root / "data", plans={})
    assert [note.code for note in notes] == ["fire_no_scale"]
    record = data["plans"]["EG"]
    assert "scale" not in record and record["style"] == {"line": 1.0, "text": 2.0}
    for collection in ("zones", "walls", "doors", "routes", "widths"):
        assert not any(key in entry for entry in record[collection] for key in validation.FIRE_MEASURES), f"{collection} states a measure on a plan without a scale"
    assert record["walls"][0] == {"id": "W1", "class": "EI 30", "style": {"line": 1.5}, "opacity": 0.5} and "style" not in record["walls"][1]
    assert record["routes"][0]["text"] == "" and record["widths"][0]["text"] == ""


def test_a_plan_that_follows_is_set_over_the_position_plans_own_exported_background():
    follower = dict(fire.new_source("OG", plan_id="Pavillon"), crop={"x": 300, "y": 400, "w": 200, "h": 150},
                    walls=[{"id": "W1", "class": "EI 30", "points": [[310, 410], [480, 410]]}])
    orphan = fire.new_source("UG", plan_id="Nirgends")
    root = _export_project("fire_export_follows", [follower, orphan])
    exported = {"Pavillon": {"sheet": {"width": 1190.55, "height": 1190.55}, "background": {"file": "plans/Pavillon-plan.pdf", "format": "pdf", "page": 1, "opacity": 0.45, "sha256": "x"}}}
    data, files, notes = fire.prepare(root / "fire", PLANS, root, root / "data", plans=exported)
    # the plan whose position plan is gone is not exported, and says so; nothing stops
    assert list(data["plans"]) == ["OG"] and "fire_plan_gone" in [getattr(note, "code", None) for note in notes]
    record = data["plans"]["OG"]
    assert record["plan"] == "Pavillon" and record["background"] == {"file": "plans/Pavillon-plan.pdf", "format": "pdf", "page": 1, "opacity": 0.45}
    assert record["crop"] == {"x": 300, "y": 400, "w": 200, "h": 150}, "its own crop, over the position plan's"
    assert not any(name.endswith(".pdf") for name in files), "the page is in data/ once, under the position plan's name"
    validation.validate_fire_business(data)
    # the position plan saved but not exported yet: drawn without its background, and said
    data, _files, notes = fire.prepare(root / "fire", PLANS, root, root / "data", plans={})
    assert "background" not in data["plans"]["OG"] and "fire_plan_unexported" in [getattr(note, "code", None) for note in notes]


def test_a_defective_export_is_refused_by_name():
    root = _export_project("fire_export_rules", [_everything()])
    good, _files, _notes = fire.prepare(root / "fire", PLANS, root, root / "data", plans={})

    def refused(change, word):
        data = copy.deepcopy(good)
        change(data["plans"]["EG"])
        try:
            validation.validate_fire_business(data)
        except validation.ValidationError as exc:
            assert word in str(exc), str(exc)
        else:
            raise AssertionError(f"accepted -- expected a refusal naming {word!r}")

    refused(lambda r: r["figures"].pop("fr"), "figures")
    refused(lambda r: r["figures"].update(de="fire/OG-de.svg"), "fire/EG-de.svg")
    refused(lambda r: r["crop"].update(w=0), "frame is empty")
    refused(lambda r: r.update(background={"file": "plans/Pavillon-plan.pdf", "format": "pdf", "page": 1, "opacity": 0.4}), "background")
    refused(lambda r: r["zones"][0].update(kind="sprinkler"), "kind 'sprinkler'")
    refused(lambda r: r["walls"][0].update(length_m=-1), "never negative")
    refused(lambda r: r["doors"][0].update(id="W1"), "used twice")
    refused(lambda r: r.pop("scale"), "without a scale")
    validation.validate_fire_business(good)


# --- what is gone -------------------------------------------------------------------------

def test_nothing_is_delimited_by_the_program_any_more():
    """The engineer's decision of 2026-10-05: no proposal of zones, no wand, no cut, no merge, no walls on an outline -- and so no picture of the plan read at all. Held so that the engine is deleted rather than left uncalled (docs/decisions.md §13, v0.59)."""
    for name in ("survey", "propose", "wand", "merge", "split", "contour_walls", "detection_of", "grid_of", "DETECTION", "Refused"):
        assert not hasattr(fire, name), f"fire.{name} is back"
    assert not (ROOT / "calc" / "domains" / "fire_zones.py").exists() and not (ROOT / "calc" / "tools" / "fire_render.py").exists()
    schema = json.loads((ROOT / "schemas" / "fire-source.schema.json").read_text(encoding="utf-8"))
    assert "detection" not in schema["properties"] and "barriers" not in schema["properties"]
    assert "numpy" not in (ROOT / "calc" / "domains" / "fire.py").read_text(encoding="utf-8")


# --- v0.115: the source is 2.0, read from 1.0 without writing a byte ---------------------------

def test_a_1_0_source_is_read_as_2_0_and_nothing_is_written():
    """Gian's two plans, in the example project exactly as they were written -- schema 1.0 -- are the migration fixture: one follows a position plan, one carries a frame of its own on a plain empty sheet."""
    assert fire.SOURCE_SCHEMA_VERSIONS == ("1.0", "2.0", "2.1") and fire.SOURCE_SCHEMA_VERSION == "2.0" and fire.EXPORT_SCHEMA_VERSION == "2.0"   # 2.1: a plan with texts (issue #43)
    for name, follows in (("Pavillon-EG", "Pavillon"), ("Treppenhaus", None)):
        path = FIRE / f"{name}.json"
        before, stamp = path.read_bytes(), path.stat().st_mtime_ns
        raw = json.loads(before.decode("utf-8"))
        assert raw["schema_version"] == "1.0"
        fire.check_source(raw, path.name)   # a 1.0 source is valid as it stands
        source = fire.read_source(path)
        assert source["schema_version"] == "2.0" and fire.follows(source) == follows
        assert {key: value for key, value in source.items() if key != "schema_version"} == {key: value for key, value in raw.items() if key != "schema_version"}, "the upgrade changes the version and nothing else"
        assert path.read_bytes() == before and path.stat().st_mtime_ns == stamp, "reading a 1.0 source wrote it"
    # the upgrade is a copy: the dictionary it was given is not touched
    raw = json.loads((FIRE / "Treppenhaus.json").read_text(encoding="utf-8"))
    upgraded = fire.upgrade(raw)
    upgraded["zones"].append({"id": "Z99"})
    assert raw["schema_version"] == "1.0" and all(zone["id"] != "Z99" for zone in raw["zones"])
    _invalid(dict(_source(), schema_version="3.0"), "expected one of 1.0, 2.0")
    assert fire.new_source("EG")["schema_version"] == "2.0"
    assert fire.upgrade("not a source") == "not a source"


def test_both_1_0_plans_of_the_example_project_export_and_validate():
    import shutil
    root = conftest.tmpdir("fire_example")
    shutil.copytree(FIRE, root / "fire")
    (root / "data").mkdir()
    exported = {"Pavillon": {"sheet": {"width": 1190.55, "height": 1190.55}, "background": {"file": "plans/Pavillon-plan.pdf", "format": "pdf", "page": 1, "opacity": 0.45}}}
    data, files, notes = fire.prepare(root / "fire", PLANS, root, root / "data", plans=exported)
    assert sorted(data["plans"]) == ["Pavillon-EG", "Treppenhaus"] and data["schema_version"] == "2.0"
    assert data["plans"]["Pavillon-EG"]["background"]["file"] == "plans/Pavillon-plan.pdf" and "background" not in data["plans"]["Treppenhaus"]
    assert all(record["legend_lines"] for record in data["plans"].values())
    assert len(files) == 6


# --- the frame on a page of a document ------------------------------------------------------------------

def _project(name):
    """A project of the test's own, as a real Project object -- the folders plan_pages asks of it -- with a PDF of two pages imported as a document and the caches pointed into it."""
    import project
    from fixtures import layered_pdf as fx
    root = conftest.tmpdir(f"fire_{name}")
    (root / "01_Pläne").mkdir()
    (root / "Woodcore.woodcore").write_text(json.dumps({"schema_version": "1.0", "format": "woodcore-project", "name": "T"}), encoding="utf-8")
    here = project.Project.load(root / "Woodcore.woodcore")
    for folder in (here.plans_dir, here.fire_dir, here.data_dir):
        folder.mkdir(parents=True, exist_ok=True)
    documents.CACHE_ROOT = root / "_cache"
    fx.write(root / "01_Pläne" / "Plan.pdf", pages=2)
    doc = documents.import_file(here, root / "01_Pläne" / "Plan.pdf", name="Grundrisse")
    return here, doc


def _write(folder, source):
    (folder / f"{source['id']}.json").write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _position_plan(here, doc, page=1, pid="P01"):
    source = plan.new_source(pid)
    width, height = documents.page_size(here, doc, page)
    source["sheet"] = {"width": width, "height": height}
    source["background"] = {"file": doc["file"], "page": page, "document": doc["id"], "sha256": doc["sha256"]}
    source["crop"] = {"x": 10, "y": 5, "w": 200, "h": 80}
    source["scale"] = {"mode": "calibration", "points": [[0, 0], [100, 0]], "length_m": 10}
    source["elements"] = [{"type": "S", "label": "S001", "points": [[50, 40]]}]
    plan.check_source(source, f"{pid}.json")
    _write(here.plans_dir, source)
    return source


def _fire_on_page(here, doc, page=1, fid="F01"):
    """A fire plan with a frame of its own on a page of the document, with one of each thing drawn on it."""
    width, height = documents.page_size(here, doc, page)
    source = fire.new_source(fid)
    source["sheet"] = {"width": width, "height": height}
    source["background"] = {"file": doc["file"], "page": page, "document": doc["id"], "sha256": doc["sha256"]}
    source["crop"] = {"x": 0, "y": 0, "w": 250, "h": 90}
    source["scale"] = {"mode": "calibration", "points": [[10, 10], [110, 10]], "length_m": 10}
    source.update({
        "zones": [{"id": "Z1", "kind": "horizontal", "label": "Flur", "label_offset": [4, 7], "points": [[20, 20], [120, 20], [120, 60], [20, 60]],
                   "holes": [[[40, 30], [60, 30], [60, 50]]]}],
        "walls": [{"id": "W1", "class": "EI 30", "points": [[20, 20], [120, 20]]}],
        "doors": [{"id": "T1", "kind": "swing", "side": 1, "points": [[30, 20], [50, 20]]}],
        "routes": [{"id": "F1", "points": [[110, 50], [30, 50]], "label_offset": [-3, 2]}],
        "exits": [{"id": "N1", "points": [[200, 40], [240, 40]]}],
        "widths": [{"id": "B1", "points": [[100, 20], [100, 60]]}],
        "legend": {"x": 150, "y": 10},
    })
    fire.check_source(source, f"{fid}.json")
    _write(here.fire_dir, source)
    return source


def test_a_plan_on_a_page_of_a_document_is_exported_under_its_own_stem():
    here, doc = _project("document")
    documents.set_layer(doc, "Walls", False)
    documents.write(here, doc)
    source = _fire_on_page(here, doc)
    assert source["background"]["document"] == doc["id"]
    data, files, notes = fire.prepare(here.fire_dir, here.plans_dir, here.root, here.data_dir, plans={})
    assert [n for n in notes if "layers" in str(n)] == [], "a plan drawn on its document hides its layers: nothing to warn about"
    background = data["plans"]["F01"]["background"]
    assert background["file"] == "fire/F01-plan.pdf" and background["document"] == doc["id"] and background["layers_off"] == ["Dims", "Walls"] and background["rotation"] == 0
    assert background["origin"] == doc["file"] and background["origin_page"] == 1 and "fire/F01-plan.pdf" in files
    from pypdf import PdfReader
    import io
    assert "/OCProperties" not in PdfReader(io.BytesIO(files["fire/F01-plan.pdf"])).trailer["/Root"], "the layers switched off are taken out of the report's page"
    validation.validate_structure(data, "fire")
    validation.validate_fire_business(data)
    # kept byte for byte while nothing changed, rewritten when the layers do
    fire.write(data, files, here.data_dir)
    again, files2, _ = fire.prepare(here.fire_dir, here.plans_dir, here.root, here.data_dir, plans={})
    assert files2["fire/F01-plan.pdf"] == files["fire/F01-plan.pdf"]
    documents.set_layer(doc, "Walls", True)
    documents.write(here, doc)
    third, files3, _ = fire.prepare(here.fire_dir, here.plans_dir, here.root, here.data_dir, plans={})
    assert third["plans"]["F01"]["background"]["layers_off"] == ["Dims"] and files3["fire/F01-plan.pdf"] != files["fire/F01-plan.pdf"]
    # the page turned in the document, the plan not yet: the sheet the page now has is said, and drawn
    documents.set_rotation(doc, 1, 90)
    documents.write(here, doc)
    turned, _f, notes = fire.prepare(here.fire_dir, here.plans_dir, here.root, here.data_dir, plans={})
    assert "fire_sheet_moved" in [getattr(n, "code", None) for n in notes] and turned["plans"]["F01"]["background"]["rotation"] == 90
    assert turned["plans"]["F01"]["sheet"] == {"width": 100.0, "height": 300.0}


def test_a_plan_whose_document_is_gone_is_drawn_on_its_file_and_says_so():
    here, doc = _project("document_gone")
    _fire_on_page(here, doc)
    (documents.source_dir(here) / f"{doc['id']}.json").unlink()
    data, _files, notes = fire.prepare(here.fire_dir, here.plans_dir, here.root, here.data_dir, plans={})
    assert any(getattr(n, "code", "") == "plan_document_missing" for n in notes), notes
    background = data["plans"]["F01"]["background"]
    assert "document" not in background and background["origin"] == doc["file"] and background["file"] == "fire/F01-plan.pdf"


def test_the_frame_of_a_document_is_checked_with_the_position_plans_rules():
    here, doc = _project("document_rules")
    source = _fire_on_page(here, doc)
    _invalid(dict(source, background=dict(source["background"], document="no way")), "background.document")
    _invalid(dict(source, background={"file": "01_Pläne/Plan.txt", "page": 1}), "a plan is drawn on")
    _invalid(dict(source, crop={"x": 0, "y": 0, "w": 1e9, "h": 1}), "crop leaves the sheet")
    follower = dict(fire.new_source("F02", plan_id="P01"), background=source["background"])
    _invalid(follower, "never both")
    fire.check_source(dict(source, background={"file": doc["file"], "page": 1}), "t")   # a plain file, as in 1.0


# --- turning it with its page ---------------------------------------------------------------------------

def _rounded(source):
    return json.loads(json.dumps(source, sort_keys=True), parse_float=lambda text: round(float(text), 6))


def test_a_quarter_turn_turns_everything_drawn_with_the_page():
    source = _everything()
    source["zones"][0]["holes"] = [[[110, 110], [130, 110], [130, 130]]]
    source["zones"][0]["label_offset"] = [3, 5]
    source["routes"][0]["label_offset"] = [-4, 2]
    source["crop"] = {"x": 10, "y": 20, "w": 300, "h": 200}
    turned = fire.rotate_source(source, 1, (W, H))
    height = H
    point = lambda p: [round(height - p[1], 2), round(p[0], 2)]
    assert turned["sheet"] == {"width": H, "height": W} and turned["schema_version"] == "2.0"
    for collection in fire.COLLECTIONS:
        for before, after in zip(source[collection], turned[collection]):
            assert after["points"] == [point(p) for p in before["points"]], collection
    assert turned["zones"][0]["holes"] == [[point(p) for p in source["zones"][0]["holes"][0]]], "an island turns with its surface"
    assert turned["zones"][0]["label_offset"] == [-5, 3] and turned["routes"][0]["label_offset"] == [-2, -4], "a text moved by hand turns as a vector"
    assert turned["crop"] == {"x": round(height - 20 - 200, 2), "y": 10.0, "w": 200.0, "h": 300.0}
    assert turned["scale"]["points"] == [point(p) for p in source["scale"]["points"]] and turned["scale"]["length_m"] == 10
    assert [d["side"] for d in turned["doors"]] == [d["side"] for d in source["doors"]], "a door's side is counted from its own line, which turns"
    # a turned door opens where the turned page says: its open leaf is the old open leaf turned
    for before, after in zip(source["doors"], turned["doors"]):
        want = point(fire.door_open_end(before))
        got = fire.door_open_end(after)
        assert abs(got[0] - want[0]) < 0.02 and abs(got[1] - want[1]) < 0.02, (before["id"], got, want)
    fire.check_source(turned, "t")
    assert source["sheet"] == {"width": W, "height": H}, "rotate_source changed the source it was given"
    # nothing to turn, a negative turn and a turn past a full circle
    assert fire.rotate_source(source, 0, (W, H)) == fire.upgrade(source) and fire.rotate_source(source, 4, (W, H)) == fire.upgrade(source)
    assert _rounded(fire.rotate_source(source, -1, (W, H))) == _rounded(fire.rotate_source(source, 3, (W, H)))


def test_four_quarter_turns_are_the_identity_to_the_hundredth():
    source = _everything()
    source["zones"][0]["holes"] = [[[110, 110], [130, 110], [130, 130]]]
    source["zones"][1]["label_offset"] = [3, 5]
    source["crop"] = {"x": 10, "y": 20, "w": 300, "h": 200}
    frame = _frame(source)
    for use_frame in (None, frame):
        turned, sheet, f = fire.upgrade(source), (W, H), use_frame
        for _ in range(4):
            turned = fire.rotate_source(turned, 1, sheet, frame=f)
            sheet = (sheet[1], sheet[0])
            f = _frame(turned) if f is not None else None
        assert _rounded(turned) == _rounded(fire.upgrade(source)), "four quarters leave the plan where it was" + (" (legend about its centre)" if use_frame else "")


def test_the_legend_turns_about_its_centre_and_not_about_its_corner():
    source = _everything()
    frame = _frame(source)
    x, y, w, h = fire_svg.legend_box(source, frame, "de")
    centre = plan.turn_point([x + w / 2, y + h / 2], H)
    turned = fire.rotate_source(source, 1, (W, H), frame=frame)
    tx, ty, tw, th = fire_svg.legend_box(turned, _frame(turned), "de")
    assert abs((tx + tw / 2) - centre[0]) < 0.02 and abs((ty + th / 2) - centre[1]) < 0.02 and abs(tw - w) < 1e-6
    plain = fire.rotate_source(source, 1, (W, H))
    assert plain["legend"] == {"x": plan.turn_point([650, 20], H)[0], "y": plan.turn_point([650, 20], H)[1]}, "without a frame, its corner is turned as a point"


def test_a_plan_that_follows_turns_its_drawing_and_its_own_crop_and_keeps_the_rest_of_the_frame_the_position_plans():
    source = dict(fire.new_source("OG", plan_id="Pavillon"), crop={"x": 300, "y": 400, "w": 200, "h": 150},
                  walls=[{"id": "W1", "class": "EI 30", "points": [[310, 410], [480, 410]]}], zones=[{"id": "Z1", "kind": "clear", "points": [[310, 410], [400, 410], [400, 480]]}])
    turned = fire.rotate_source(source, 1, (1190.55, 1190.55))
    assert "sheet" not in turned and "scale" not in turned and "background" not in turned and turned["plan"] == "Pavillon"
    assert turned["walls"][0]["points"] == [[round(1190.55 - 410, 2), 310.0], [round(1190.55 - 410, 2), 480.0]]
    assert turned["crop"] == {"x": round(1190.55 - 400 - 150, 2), "y": 300.0, "w": 150.0, "h": 200.0}
    fire.check_source(turned, "t")
    plain = fire.new_source("OG", plan_id="Pavillon")
    assert "crop" not in fire.rotate_source(plain, 1, (1190.55, 1190.55)), "a plan that states no crop of its own still states none"


# --- detaching a plan from the position plan it follows ---------------------------------------------------

def test_a_plan_detached_carries_the_frame_it_followed():
    frames = fire.plan_frames(PLANS)
    follower = dict(fire.new_source("EG", plan_id="Pavillon"), walls=[{"id": "W1", "class": "EI 30", "points": [[310, 410], [480, 410]]}], style={"line": 2})
    frame, problem = fire.frame_of(follower, frames)
    assert problem is None
    detached = fire.detach(follower, frame)
    assert "plan" not in detached and fire.follows(detached) is None and detached["schema_version"] == "2.0"
    for key in ("background", "sheet", "crop", "scale"):
        assert detached.get(key) == frames["Pavillon"].get(key), key
    assert detached["walls"] == follower["walls"] and detached["style"] == {"line": 2}, "what is drawn stays"
    fire.check_source(detached, "t")
    # it is drawn over the very same frame, with no position plan to read it from
    assert fire.frame_of(detached, {})[0] == frame
    # its own crop, where it states one, wins over the position plan's
    mine = dict(follower, crop={"x": 300, "y": 400, "w": 200, "h": 150})
    assert fire.detach(mine, fire.frame_of(mine, frames)[0])["crop"] == {"x": 300, "y": 400, "w": 200, "h": 150}
    assert fire.detach(mine, fire.frame_of(mine, frames)[0])["background"] == frames["Pavillon"]["background"]
    # the source it was given is untouched, and a plan that follows nothing is a plain copy
    assert follower["plan"] == "Pavillon" and "sheet" not in follower
    own = _everything()
    again = fire.detach(own, _frame(own))
    assert again == fire.upgrade(own) and again is not own


# --- the legend as the report sets it ---------------------------------------------------------------------

def test_the_legend_is_exported_as_lines_the_report_sets_in_its_own_typeface():
    source = _everything()
    lines = fire_svg.legend_lines(source)
    assert [line["key"] for line in lines] == ["wall:EI 60-RF1", "wall:EI 30", "surface:vertical", "surface:horizontal", "surface:clear",
                                               "exit", "length", "width", "door:swing:EI 30", "door:slide:E 30", "door:swing"]
    assert len(lines) == len(fire.legend_rows(source)) and fire_svg.legend_lines(_source()) == []
    for line in lines:
        assert line["swatch"].startswith("<svg") and line["swatch"].endswith("</svg>")
        ElementTree.fromstring(line["swatch"])
        assert 'width="10mm"' in line["swatch"]
        for banned in ("<pattern", "clip-path", "<marker", "style="):
            assert banned not in line["swatch"]
        assert ("term" in line) != ("engine" in line), "a line is a word of the sheet or one of the engine's"
    by_key = {line["key"]: line for line in lines}
    assert by_key["wall:EI 30"]["text"] == "Feuerwiderstand EI 30" and by_key["wall:EI 30"]["term"] == "Feuerwiderstand EI 30"
    assert by_key["door:swing"]["engine"] == "fire.door.swing" and by_key["door:swing"]["text"] == strings.text("fire.door.swing", "de")
    assert strings.term(by_key["exit"]["term"], "fr") == "Sortie de secours"
    # the swatch is the very thing the plan draws: a wall's is its colour, a door's its resistance's
    assert vkf.colour(vkf.resistance("EI 30")["rgb"]) in by_key["wall:EI 30"]["swatch"] and "#fabafc" in by_key["door:slide:E 30"]["swatch"]
    # and it is in the export, per plan
    root = _export_project("fire_legend", [source])
    data, _files, _notes = fire.prepare(root / "fire", PLANS, root, root / "data", plans={})
    assert data["plans"]["EG"]["legend_lines"] == lines
    refused = copy.deepcopy(data)
    refused["plans"]["EG"]["legend_lines"].append(dict(lines[0]))
    try:
        validation.validate_fire_business(refused)
    except validation.ValidationError as exc:
        assert "twice" in str(exc)
    else:
        raise AssertionError("a legend line listed twice was accepted")
    refused["plans"]["EG"]["legend_lines"] = [dict(lines[0], swatch="plain")]
    try:
        validation.validate_fire_business(refused)
    except validation.ValidationError as exc:
        assert "no SVG" in str(exc)
    else:
        raise AssertionError("a swatch that is no SVG was accepted")


# --- what both kinds of plan on a page share ----------------------------------------------------------------

def _two_kinds(name):
    """A document of two pages; on page 1 a position plan, a fire plan of its own and a fire plan that follows the position plan; on page 2 a position plan and a fire plan of their own."""
    here, doc = _project(name)
    _position_plan(here, doc, 1, "P01")
    _position_plan(here, doc, 2, "P02")
    _fire_on_page(here, doc, 1, "F01")
    _fire_on_page(here, doc, 2, "F03")
    follower = dict(fire.new_source("F02", plan_id="P01"), walls=[{"id": "W1", "class": "EI 30", "points": [[20, 20], [120, 20]]}],
                    zones=[{"id": "Z1", "kind": "vertical", "points": [[20, 20], [60, 20], [60, 60]]}], crop={"x": 15, "y": 10, "w": 150, "h": 60}, legend={"x": 30, "y": 12})
    _write(here.fire_dir, follower)
    return here, doc


def test_the_drawings_on_a_page_are_of_both_kinds_and_the_fire_plans_that_follow_count():
    here, doc = _two_kinds("pages")
    both = plan_pages.drawings_on(here, doc["id"])
    assert [pid for pid, _s in both["position"]] == ["P01", "P02"] and [fid for fid, _s, _f in both["fire"]] == ["F01", "F02", "F03"]
    one = plan_pages.drawings_on(here, doc["id"], 1)
    assert [pid for pid, _s in one["position"]] == ["P01"] and [fid for fid, _s, _f in one["fire"]] == ["F01", "F02"], "a plan that follows is on the page of the position plan it follows"
    two = plan_pages.drawings_on(here, doc["id"], 2)
    assert [pid for pid, _s in two["position"]] == ["P02"] and [fid for fid, _s, _f in two["fire"]] == ["F03"]
    assert plan_pages.drawings_on(here, "D99") == {"position": [], "fire": []}
    # what it hands out is what a tab draws over: the frame of each fire plan, the position plan's for the one that follows
    frames = {fid: frame for fid, _s, frame in one["fire"]}
    assert frames["F02"]["sheet"] == frames["F01"]["sheet"] and frames["F02"]["crop"] == {"x": 15, "y": 10, "w": 150, "h": 60}
    assert plan_pages.position_plans_on(here, doc["id"], 2)[0][0] == "P02" and [f for f, _s, _fr in plan_pages.fire_plans_on(here, doc["id"], 1)] == ["F01", "F02"]
    # a fire plan whose position plan is gone, and a source that is no JSON, are passed over
    (here.plans_dir / "P01.json").unlink()
    (here.fire_dir / "Kaputt.json").write_text("{not json", encoding="utf-8")
    assert [fid for fid, _s, _f in plan_pages.drawings_on(here, doc["id"], 1)["fire"]] == ["F01"]


def test_turning_a_page_turns_the_position_plans_and_the_fire_plans_on_it_and_no_others():
    here, doc = _two_kinds("rotate")
    read = lambda folder, name: json.loads((folder / f"{name}.json").read_text(encoding="utf-8"))
    before = {("p", n): read(here.plans_dir, n) for n in ("P01", "P02")} | {("f", n): read(here.fire_dir, n) for n in ("F01", "F02", "F03")}
    assert before[("f", "F01")]["schema_version"] == "2.0"
    done = plan_pages.rotate_page(here, doc["id"], 1, 90)
    assert done == {"position": ["P01"], "fire": ["F01", "F02"]}
    assert documents.rotation(documents.read(here, doc["id"]), 1) == 90 and documents.rotation(documents.read(here, doc["id"]), 2) == 0
    width, height = before[("p", "P01")]["sheet"]["width"], before[("p", "P01")]["sheet"]["height"]
    p01 = read(here.plans_dir, "P01")
    assert p01["sheet"] == {"width": height, "height": width} and p01["elements"][0]["points"] == [[round(height - 40, 2), 50.0]]
    f01 = read(here.fire_dir, "F01")
    assert f01["sheet"] == {"width": height, "height": width} and f01["zones"][0]["points"][0] == [round(height - 20, 2), 20.0] and f01["zones"][0]["label_offset"] == [-7, 4]
    f02 = read(here.fire_dir, "F02")
    assert "sheet" not in f02 and f02["plan"] == "P01" and f02["walls"][0]["points"][0] == [round(height - 20, 2), 20.0]
    assert f02["crop"] == {"x": round(height - 10 - 60, 2), "y": 15.0, "w": 60.0, "h": 150.0}
    # page 2 and what is drawn on it is untouched, byte for byte
    for kind, folder, name in (("p", here.plans_dir, "P02"), ("f", here.fire_dir, "F03")):
        assert read(folder, name) == before[(kind, name)], name
    # the frame of a followed plan is still the position plan's, turned
    assert fire.frame_of(f02, fire.plan_frames(here.plans_dir))[0]["sheet"] == p01["sheet"]
    for plan_source, fire_source in ((p01, f01), (p01, f02)):
        plan.check_source(plan_source, "p")
        fire.check_source(fire_source, "f")
    # four quarters in all: everything is where it was, the document included
    for _ in range(3):
        plan_pages.rotate_page(here, doc["id"], 1, 90)
    assert documents.rotation(documents.read(here, doc["id"]), 1) == 0
    for (kind, name), source in before.items():
        folder = here.plans_dir if kind == "p" else here.fire_dir
        after = read(folder, name)
        want = dict(source, schema_version=plan.SOURCE_SCHEMA_VERSION) if kind == "p" else source
        assert _rounded(after) == _rounded(want), name
    # and a quarter back
    plan_pages.rotate_page(here, doc["id"], 1, -90)
    assert documents.rotation(documents.read(here, doc["id"]), 1) == 270 and read(here.fire_dir, "F01")["sheet"] == {"width": height, "height": width}


def test_a_refused_turn_writes_nothing():
    here, doc = _two_kinds("rotate_refused")
    before = {path.name: path.read_bytes() for folder in (here.plans_dir, here.fire_dir) for path in folder.glob("*.json")}
    docs = {path.name: path.read_bytes() for path in documents.source_dir(here).glob("*.json")}
    for bad_doc, bad_page in (("D99", 1), (doc["id"], 7)):
        try:
            plan_pages.rotate_page(here, bad_doc, bad_page, 90)
        except validation.ValidationError:
            pass
        else:
            raise AssertionError("a page that is not there was turned")
    try:
        plan_pages.rotate_page(here, doc["id"], 1, 45)
    except validation.ValidationError as exc:
        assert "quarter turns" in str(exc)
    else:
        raise AssertionError("a page was turned by 45 degrees")
    assert before == {path.name: path.read_bytes() for folder in (here.plans_dir, here.fire_dir) for path in folder.glob("*.json")}
    assert docs == {path.name: path.read_bytes() for path in documents.source_dir(here).glob("*.json")}


def test_the_export_of_both_kinds_runs_on_its_own_and_a_followed_plan_is_set_over_the_position_plans_page():
    here, doc = _two_kinds("export_both")
    notes = plan_pages.export_drawings(here)
    plans = json.loads((here.data_dir / "plans.json").read_text(encoding="utf-8"))["plans"]
    exported = json.loads((here.data_dir / "fire.json").read_text(encoding="utf-8"))["plans"]
    assert sorted(plans) == ["P01", "P02"] and sorted(exported) == ["F01", "F02", "F03"], notes
    assert exported["F02"]["plan"] == "P01" and exported["F02"]["background"]["file"] == "plans/P01-plan.pdf" and exported["F02"]["background"]["document"] == doc["id"]
    assert exported["F01"]["background"]["file"] == "fire/F01-plan.pdf" and (here.data_dir / "fire" / "F01-plan.pdf").is_file()
    assert (here.data_dir / "fire" / "F02-de.svg").is_file() and exported["F02"]["legend_lines"]
    # turned, exported again: the figures follow the page
    plan_pages.rotate_page(here, doc["id"], 1, 90)
    plan_pages.export_drawings(here)
    turned = json.loads((here.data_dir / "fire.json").read_text(encoding="utf-8"))["plans"]
    assert turned["F01"]["background"]["rotation"] == 90 and turned["F02"]["background"]["rotation"] == 90
    assert turned["F01"]["sheet"] == {"width": exported["F01"]["sheet"]["height"], "height": exported["F01"]["sheet"]["width"]}
    ElementTree.fromstring((here.data_dir / "fire" / "F01-de.svg").read_text(encoding="utf-8"))
