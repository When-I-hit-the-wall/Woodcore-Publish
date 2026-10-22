"""A position plan's storey, its role and its section, a page turned under what was drawn on it, and the opening's symbol (v0.114, plan-source 1.2 and plans 1.3, calc/domains/plan.py and plan_svg.py, docs/domain/position-plans.md §3.3sexies).

The engineer's answers of 06.10.2026: a plan's storey is a free designation of any length (`storey`) beside the one character of its positions' numbers (`floor`), which is proposed from it; a section plan carries storey lines -- drawn with the storey's designation in a bubble at both ends -- and storey boxes, which a sheet highlights; and a page turned in its document turns everything drawn on it, so the drawing stays on the architecture. Every field is additive: a 1.0 or 1.1 source is read as it is, and a plan without them is drawn byte for byte as before (tests/test_plan_style.py's frozen hashes).
"""

TIER = "fast"  # tests/run_tests.py --fast

import copy
import json
import math
import re

import conftest
import validation
from domains import plan
from domains import plan_svg


def _source(**extra):
    source = plan.new_source("P01")
    source["sheet"] = {"width": 1000.0, "height": 700.0}
    source["elements"] = [
        {"type": "T", "label": "T001", "points": [[100, 200], [500, 200]], "label_offset": [0, -40]},
        {"type": "S", "label": "S001", "points": [[600, 300]]},
        {"type": "D", "subtype": "normal", "label": "D001", "points": [[100, 400], [500, 400], [500, 600], [100, 600]], "span": 0},
    ]
    source["axes"] = [{"label": "A", "point": [100, 0], "angle": 90, "bubbles": "start"},
                      {"label": "1", "point": [0, 200], "angle": 0, "bubbles": "end"}]
    source["crop"] = {"x": 50, "y": 100, "w": 800, "h": 550}
    source["scale"] = {"mode": "calibration", "points": [[100, 650], [300, 650]], "length_m": 2.0}
    source.update(extra)
    return source


def _section(**extra):
    section = _source(role="section", storey_lines=[{"storey": "EG", "points": [[50, 500], [950, 500]]},
                                                     {"storey": "1.OG", "points": [[50, 300], [950, 300]]}],
                      storey_boxes=[{"storey": "EG", "x": 60, "y": 300, "w": 880, "h": 200}])
    section.update(extra)
    return section


def _refused(source, words):
    try:
        plan.check_source(source, "P01.json")
    except validation.ValidationError as exc:
        assert words in str(exc), (words, str(exc))
    else:
        assert False, f"accepted: {words}"


# --- the source -----------------------------------------------------------------------------

def test_a_1_2_source_carries_its_storey_role_and_section():
    source = _section(storey="EG")
    plan.check_source(source, "P01.json")
    assert plan.new_source("X")["schema_version"] == "1.6"  # v0.116: the plan type, the load symbols and the load levels; v0.117: a column turned, a length of its own; issue #9: the dimensions; issue #18: the construction aids
    plan.check_source({**source, "schema_version": "1.2"}, "P01.json")  # a 1.2 source is read as it is
    floor = _source(storey="Mezzanine mit Galerie", section_plan="S01")
    plan.check_source(floor, "P01.json")
    # a 1.1 source, with none of it, is read as it is
    old = {k: v for k, v in _source().items() if k not in ("storey", "role")}
    old["schema_version"] = "1.1"
    plan.check_source(old, "P01.json")


def test_what_a_source_may_not_say_is_refused_naming_it():
    _refused(_source(role="Schnitt"), "'Schnitt'")
    _refused(_source(storey_lines=[{"storey": "EG", "points": [[0, 0], [10, 0]]}]), "drawn on a section")
    _refused(_section(storey_lines=[{"storey": "EG", "points": [[5, 5], [5, 5]]}]), "same point")
    _refused(_section(storey_lines=[{"storey": " ", "points": [[0, 0], [10, 0]]}]), "names no storey")
    _refused(_section(storey_boxes=[{"storey": "EG", "x": 0, "y": 0, "w": 0, "h": 10}]), "greater than 0")
    _refused(_source(section_plan="S 01"), "section_plan")
    # a CAD drawing is drawn on through its document only
    dxf = _source(background={"file": "01_Pläne/Plan.dxf", "page": 2})
    _refused(dxf, "through its document")
    plan.check_source(_source(background={"file": "01_Pläne/Plan.dxf", "page": 2, "document": "D01"}), "P01.json")
    _refused(_source(background={"file": "01_Pläne/Plan.pdf", "page": 1, "document": "D 1"}), "background.document")


def test_the_storey_list_is_one_list_in_three_languages():
    lengths = {len(names) for names in plan.STOREYS.values()}
    assert lengths == {9} and set(plan.STOREYS) == {"de", "fr", "en"}
    for index in range(9):
        assert {plan.storey_index(names[index]) for names in plan.STOREYS.values()} == {index}


def test_the_floor_character_is_proposed_from_the_storey():
    """STE's numbering: U a basement, 0 the ground floor, n the n-th floor; the attic one above the highest floor the project's other plans have; a designation of the engineer's own proposes nothing."""
    cases = {"2.UG": "U", "1er SS": "U", "B1": "U", "EG": "0", "rez": "0", " GF ": "0", "1.OG": "1", "3e": "3", "5F": "5"}
    for storey, floor in cases.items():
        assert plan.storey_floor(storey) == floor, (storey, plan.storey_floor(storey))
    assert plan.storey_floor("DG", ["0", "1", "2", "U"]) == "3"
    assert plan.storey_floor("Combles") == "1"
    assert plan.storey_floor("Attic", ["9"]) == "", "one character cannot number a tenth floor"
    assert plan.storey_floor("Mezzanine") == "" and plan.storey_floor("") == ""


# --- a page turned --------------------------------------------------------------------------

def test_four_quarter_turns_give_back_the_source_and_a_turn_back_undoes_one():
    source = _section()
    sheet = (source["sheet"]["width"], source["sheet"]["height"])
    turned = plan.rotate_source(source, 1, sheet)
    assert turned["sheet"] == {"width": 700, "height": 1000}
    back = plan.rotate_source(turned, -1, (700, 1000))
    assert {k: back[k] for k in source if k != "sheet"} == {k: source[k] for k in source if k != "sheet"}
    around = source
    size = sheet
    for _ in range(4):
        around = plan.rotate_source(around, 1, size)
        size = (around["sheet"]["width"], around["sheet"]["height"])
    assert {k: around[k] for k in source if k != "sheet"} == {k: source[k] for k in source if k != "sheet"}
    assert plan.rotate_source(source, 0, sheet) == source and plan.rotate_source(source, 0, sheet) is not source


def test_a_quarter_turn_moves_everything_drawn_with_the_page():
    """A point (x, y) of a sheet h high goes to (h − y, x) when the page turns a quarter clockwise; every kind of thing drawn is checked once against that, and an axis's bubble stays at the end it was at."""
    source = _section()
    turned = plan.rotate_source(source, 1, (1000, 700))
    beam = turned["elements"][0]
    assert beam["points"] == [[500, 100], [500, 500]]
    assert beam["label_offset"] == [40, 0], "a number moved by hand is moved by the turned vector"
    assert turned["elements"][2]["span"] == 90
    vertical, horizontal = turned["axes"]
    assert vertical["point"] == [700, 100] and vertical["angle"] == 0
    assert vertical["bubbles"] == "end", "the top of a vertical axis is the right end once turned"
    assert horizontal["angle"] == 90 and horizontal["bubbles"] == "end", "the right end of a horizontal axis is its bottom once turned"
    assert turned["crop"] == {"x": 50, "y": 50, "w": 550, "h": 800}
    assert turned["scale"]["points"] == [[50, 100], [50, 300]] and plan.units_per_m(turned) == plan.units_per_m(source)
    assert turned["storey_lines"][0]["points"] == [[200, 50], [200, 950]]
    assert turned["storey_boxes"][0] == {"storey": "EG", "x": 200, "y": 60, "w": 200, "h": 880}
    assert turned["elements"][1]["points"] == [[400, 600]]
    plan.check_source(turned, "P01.json")


# --- the export record ------------------------------------------------------------------------

def test_the_record_carries_the_storey_the_role_and_a_sections_lines_and_boxes():
    section = _section(storey="Schnitt A-A")
    record = plan.build_record(section, (1000, 700))
    assert record["storey"] == "Schnitt A-A" and record["role"] == "section"
    assert record["storey_lines"] == [{"storey": "EG", "points": [[50, 500], [950, 500]]}, {"storey": "1.OG", "points": [[50, 300], [950, 300]]}]
    assert record["storey_boxes"] == [{"storey": "EG", "x": 60, "y": 300, "w": 880, "h": 200}]
    floor = plan.build_record(_source(storey="EG", section_plan="S01"), (1000, 700))
    assert floor["role"] == "plan" and floor["section_plan"] == "S01" and "storey_lines" not in floor
    data = {"schema_version": plan.EXPORT_SCHEMA_VERSION, "plans": {"P01": {**record, "unknown": []}, "P02": {**floor, "overlay": "plans/P02.svg", "unknown": []}}}
    validation.validate_structure(data, "plans")
    validation.validate_plans_business(data)


def test_a_floor_plan_naming_no_section_of_the_project_is_said():
    root = conftest.tmpdir("plan_section_missing")
    plans = root / "plans"
    plans.mkdir()
    floor = _source(section_plan="S01")
    (plans / "P01.json").write_text(json.dumps(floor), encoding="utf-8")
    _data, _files, notes = plan.prepare(plans, root, root / "data", ["T001", "S001", "D001"])
    assert any(getattr(n, "code", "") == "plan_section_missing" for n in notes), notes
    section = _section(id="S01")
    (plans / "S01.json").write_text(json.dumps(section), encoding="utf-8")
    data, _files, notes = plan.prepare(plans, root, root / "data", ["T001", "S001", "D001"])
    assert not any(getattr(n, "code", "") == "plan_section_missing" for n in notes), notes
    assert data["plans"]["S01"]["role"] == "section" and data["plans"]["P01"]["section_plan"] == "S01"


# --- the drawing ---------------------------------------------------------------------------------

def test_a_storey_line_has_its_bubble_at_both_ends_and_the_boxes_are_not_drawn():
    svg = plan_svg.render(_section())
    assert svg.count(plan_svg.STOREYS_OPEN) == 1 and svg.count(plan_svg.STOREYS_CLOSE) == 1
    inside = svg.split(plan_svg.STOREYS_OPEN)[1].split(plan_svg.STOREYS_CLOSE)[0]
    assert len(re.findall(r">EG</text>", inside)) == 2 and len(re.findall(r">1\.OG</text>", inside)) == 2
    assert len(re.findall(r"<rect\b", inside)) == 4, "a bubble at each end of each line, and no box"
    assert "stroke-dasharray" in inside
    # the storeys stand between their own markers, which a sheet may strip as it strips the axes
    assert svg.index(plan_svg.AXES_CLOSE) < svg.index(plan_svg.STOREYS_OPEN)


def test_a_plan_without_storey_lines_carries_no_marker_of_them():
    svg = plan_svg.render(_source(storey="EG"))
    assert plan_svg.STOREYS_OPEN not in svg and plan_svg.STOREYS_CLOSE not in svg
    assert plan_svg.render(_source(storey="EG")) == plan_svg.render({k: v for k, v in _source().items() if k not in ("storey", "role")})


def test_the_opening_is_a_rectangle_and_a_wedge_in_its_top_right_corner():
    """The engineer's symbol after STE Compact 02: for the corner C furthest up and right, its neighbours A and B and t = min(14 text units, 0.18 · the shorter of CA, CB), the black polygon A, C, B, P with P = C + t·(uA + uB)."""
    sz = plan_svg.Sizes(1.0, {})
    points = [[100, 100], [400, 100], [400, 300], [100, 300]]
    wedge = plan_svg.opening_wedge(points, sz)
    t = min(14.0, 0.18 * 200)
    assert wedge[:3] == [(100, 100), (400, 100), (400, 300)]
    assert all(math.isclose(a, b) for a, b in zip(wedge[3], (400 - t, 100 + t)))
    # a thin opening: the wedge stays inside it
    thin = plan_svg.opening_wedge([[0, 0], [400, 0], [400, 20], [0, 20]], sz)
    assert math.isclose(thin[3][1], 0.18 * 20)
    out = []
    plan_svg._opening(out, points, sz)
    assert len(out) == 2 and f'fill="{plan_svg.INK}"' in out[1] and f'stroke="{plan_svg.INK}"' in out[0]
    swatch = plan_svg.legend_swatch("Ö")
    assert swatch.count("<polygon") == 2 and f'fill="{plan_svg.INK}"' in swatch, "the legend follows the symbol"
