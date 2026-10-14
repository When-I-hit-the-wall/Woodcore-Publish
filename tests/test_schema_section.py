"""An element's section and its label (v0.75, docs/domain/detail-schemas.md §3.3decies, docs/domain/positions.md §7): «T001 C24 100/200», and a schema that knows b and h.

The engineer set three rules, and the file is written on them rather than on the arithmetic. **b and h follow the element's position**, read afresh at every export off the position's `dimension` text; **a side typed on the element stays written over** when Positionen.xlsx changes, until «Reprendre» takes it back; and **the band is the side the view shows**. The label is the fourth: the position, its strength class and the section.

⚠️ Since v0.94 a position's dimension is read once, by domains/section.py, into the `section` of its record (tests/test_section.py), and an element's b and h are that section's -- a rectangle's own two, a round section's d, a plate's t, and nothing for a steel profile. A record exported before carries no `section` and is read by the same reader's deduction, which is what the records below are: `schema.parse_section`, the lenient reader v0.75 wrote here, is gone. What the tests hold is that a dimension that gives no b/h stays a warning, never a stop, a «180» panel being a piece with no b/h rather than a defect.

What it also holds, because each was got wrong on the way: the label of a beam through a column sits on the beam's own visible part and not under the node (v0.72 to v0.74 put it on a two-point element's far END, and the first v0.75 draft on its middle, under the rotation centre); a construction line the report leaves out is drawn in the editor (it was invisible there since v0.72); and a 1.0 source reads as 1.1 without its drawing moving.
"""

import copy
import math

import conftest
from conftest import ROOT, Skip
from domains import schema
from domains import schema_svg
from domains import section

POSITIONS = {
    "T001": {"material": "C24", "dimension": "100/200", "units": "mm", "type": "Träger", "moisture_class": 2},
    "S001": {"material": "C24", "dimension": "100/200", "units": "mm", "type": "Stütze", "moisture_class": 2},
    "D001": {"material": "C24", "dimension": "180", "units": "mm", "type": "Decke", "moisture_class": 1},
    "B001": {"material": "", "dimension": "10/20", "units": "cm", "type": "Brett", "moisture_class": None},
}


def _element(**fields):
    base = {"id": "E1", "kind": "linear", "points": [[-230, 0], [230, 0]], "view": "h", "position": "T001"}
    base.update(fields)
    return {k: v for k, v in base.items() if v is not None}


def _source(elements=None, **extra):
    source = schema.new_source("T_99")
    source["elements"] = elements if elements is not None else [
        _element(),
        _element(id="E2", points=[[0, -100], [0, 230]], position="S001"),
    ]
    source.update(extra)
    return source


# --- reading the dimension ---------------------------------------------------------

def test_a_dimension_is_read_in_every_shape_it_is_written_in():
    """A record exported before v0.94 -- no `section` -- read by domains/section.py's deduction: every shape «b/h» was written in before the column existed."""
    for text, units, want in (("100/200", "mm", (100, 200)), ("100 / 200", "mm", (100, 200)),
                              ("100x200", "mm", (100, 200)), ("100X200", "", (100, 200)),
                              ("100×200", "mm", (100, 200)), ("100,5/200", "mm", (100.5, 200)),
                              ("10/20", "cm", (100, 200)), ("0.1/0.2", "m", (100, 200)),
                              (" 101.6/10 ", "MM", (101.6, 10))):
        got = section.sides({"dimension": text, "units": units})
        assert got is not None and all(math.isclose(a, b) for a, b in zip(got, want)), (text, units, got)


def test_what_is_not_b_over_h_gives_no_section_and_no_error():
    for text, units in (("180", "mm"), ("100/200/300", "mm"), ("abc", "mm"), ("", "mm"), ("100/", "mm"),
                        ("/200", "mm"), ("0/200", "mm"), ("100/0", "mm"), ("100/200", "in"), (None, None),
                        ("-100/200", "mm")):
        assert section.sides({"dimension": text, "units": units}) is None, (text, units)


def test_a_section_the_export_read_gives_the_sides_and_the_label():
    """v0.94: a round section gives its diameter for both sides and a plate its thickness, and the label prints what is not a rectangle as the summaries print it; a steel profile gives no b/h, the element states its own, and until it does the export says so -- a warning, never a stop."""
    records = {
        "S003": {"strength_class": "GL24h", "dimension": "200", "units": "mm", "section": section.parse("cir", "200", "mm")},
        "D004": {"strength_class": "C24", "dimension": "27", "units": "mm", "section": section.parse("pla", "27", "mm")},
        "S002": {"strength_class": "S355", "dimension": "101.6x10", "units": "mm", "section": section.parse("ROR", "101.6x10", "mm")},
    }
    rounded = schema.element_section(_element(position="S003"), records)
    assert (rounded["b"], rounded["h"], rounded["b_from"]) == (200, 200, "position")
    assert schema.element_caption(_element(position="S003"), records) == "S003 GL24h Ø 200 mm"
    assert schema.element_width(_element(position="D004", view="b"), records) == 27
    assert schema.element_caption(_element(position="S002"), records) == "S002 S355 ROR 101.6×10"
    assert schema.element_width(_element(position="S002"), records) == schema.ELEMENT_DEFAULT_WIDTH
    assert schema.element_caption(_element(position="S002", b=101.6, h=101.6), records) == "S002 S355 101.6/101.6", "sides written over are what is drawn"
    notes = schema.warnings(_source([_element(position="S002")]), records)
    assert any("ROR 101.6×10" in n and "S002" in n for n in notes), notes


# --- following, writing over, taking back ------------------------------------------

def test_a_side_follows_its_position():
    section = schema.element_section(_element(), POSITIONS)
    assert (section["b"], section["h"]) == (100, 200)
    assert (section["b_from"], section["h_from"]) == ("position", "position")


def test_a_side_written_over_stays_written_over_when_the_workbook_changes():
    """The engineer's own rule: «une valeur reprise puis écrasée reste écrasée» -- the next «Importer Excel» must not undo it, while the side nobody typed follows the new dimension."""
    element = _element(h=240)
    changed = copy.deepcopy(POSITIONS)
    changed["T001"]["dimension"] = "120/260"
    section = schema.element_section(element, changed)
    assert (section["b"], section["b_from"]) == (120, "position")
    assert (section["h"], section["h_from"]) == (240, "stated")
    assert section["position_h"] == 260, "the orange line names what the position now holds"


def test_emptying_a_side_follows_the_position_again():
    element = _element(h=240)
    element.pop("h")
    assert schema.element_section(element, POSITIONS)["h_from"] == "position"


def test_a_position_the_export_lost_or_none_or_no_export_at_all():
    lost = schema.element_section(_element(position="GONE"), POSITIONS)
    assert not lost["resolved"] and lost["b"] is None and lost["h"] is None
    none = schema.element_section(_element(position=None, b=20, h=150), POSITIONS)
    assert none["position"] == "" and (none["b"], none["h"]) == (20, 150)
    unexported = schema.element_section(_element(), None)
    assert not unexported["resolved"] and unexported["h"] is None


# --- the label --------------------------------------------------------------------

def test_the_label_reads_position_class_and_section():
    assert schema.element_caption(_element(), POSITIONS) == "T001 C24 100/200"


def test_the_label_follows_what_is_written_over():
    assert schema.element_caption(_element(h=240), POSITIONS) == "T001 C24 100/240"


def test_the_label_in_every_other_case():
    assert schema.element_caption(_element(position="B001"), POSITIONS) == "B001 100/200", "no class: nothing printed for it, cm read as mm"
    assert schema.element_caption(_element(position="D001"), POSITIONS) == "D001 C24 180", "a dimension that is not b/h is printed as the workbook has it"
    assert schema.element_caption(_element(position="GONE"), POSITIONS) == "GONE"
    assert schema.element_caption(_element(id="E3", position=None), POSITIONS) == "E3"
    assert schema.element_caption(_element(id="E3", position=None, b=20, h=150), POSITIONS) == "E3 20/150"
    assert schema.element_caption(_element(label="Pfette"), POSITIONS) == "Pfette", "a label typed on the piece wins"
    assert schema.element_caption(_element(h=240.55), POSITIONS) == "T001 C24 100/240.55"


# --- the band -----------------------------------------------------------------------

def test_the_band_is_the_side_the_view_shows():
    assert schema.element_width(_element(view="h"), POSITIONS) == 200
    assert schema.element_width(_element(view="b"), POSITIONS) == 100
    assert schema.element_width(_element(view="b", b=60), POSITIONS) == 60


def test_a_band_whose_side_is_unknown_is_drawn_at_the_default_and_said():
    source = _source([_element(position="D001"), _element(id="E2", position=None, points=[[0, -100], [0, 230]])])
    assert schema.element_width(source["elements"][0], POSITIONS) == schema.ELEMENT_DEFAULT_WIDTH
    notes = schema.warnings(source, POSITIONS)
    assert any("E1" in n and "180" in n for n in notes), notes
    assert any("E2" in n and "names no position" in n for n in notes), notes
    schema.check_source(source, "T_99.json")   # a warning, never a stop


# --- the version --------------------------------------------------------------------

def test_a_1_0_source_reads_as_1_1_and_its_drawing_does_not_move():
    old = _source([_element(width=140), _element(id="E2", points=[[0, -100], [0, 230]], position="S001", view="b", width=80)])
    old["schema_version"] = "1.0"
    before = schema_svg.render(schema_svg.layout(copy.deepcopy(old), positions=POSITIONS))
    schema.check_source(old, "T_99.json")
    assert old["schema_version"] == schema.SOURCE_SCHEMA_VERSION
    assert "width" not in old["elements"][0] and old["elements"][0]["h"] == 140
    assert old["elements"][1]["b"] == 80 and "h" not in old["elements"][1]
    after = schema_svg.render(schema_svg.layout(old, positions=POSITIONS))
    assert before == after, "reading a 1.0 file moved its drawing"


def test_a_1_1_source_still_carrying_width_is_refused_naming_it():
    source = _source([_element(width=140)])
    try:
        schema.check_source(source, "T_99.json")
    except Exception as exc:  # noqa: BLE001
        assert "width" in str(exc) and "b and h" in str(exc), str(exc)
    else:
        raise AssertionError("a 1.1 element carrying width was accepted")


def test_a_side_must_be_a_positive_number():
    for bad in (0, -5, "200", True):
        source = _source([_element(h=bad)])
        try:
            schema.check_source(source, "T_99.json")
        except Exception:  # noqa: BLE001
            continue
        raise AssertionError(f"h = {bad!r} was accepted")


# --- the modifications keep the section --------------------------------------------

def test_every_modification_keeps_the_section():
    source = _source([_element(h=240, view="b"), _element(id="E2", points=[[0, -100], [0, 230]], position="S001")])
    source["aids"].append({"id": "A1", "kind": "vertical", "x": 100, "z": 0, "angle": 90, "shown": False})
    made = schema.duplicate(source, ["E1"], schema.translation(0, 500))
    copy_of = schema.entry_of(source, "elements", made[0])
    assert (copy_of.get("h"), copy_of.get("view"), copy_of.get("position")) == (240, "b", "T001")
    pieces = schema.split_element(source, "E1", "A1")
    for eid in pieces:
        piece = schema.entry_of(source, "elements", eid)
        assert (piece.get("h"), piece.get("view")) == (240, "b"), piece
    kept = schema.merge_elements(source, pieces)
    assert schema.entry_of(source, "elements", kept).get("h") == 240
    schema.modify(source, ["E1"], schema.rotation((0, 0), 90))
    schema.modify(source, ["E1"], schema.reflection((0, 0), (0, 100)))
    assert schema.entry_of(source, "elements", "E1").get("h") == 240
    schema.check_source(source, "T_99.json")


# --- where the label sits ------------------------------------------------------------

def _home(source, eid):
    drawing = schema_svg.layout(source, positions=POSITIONS)
    return next(frame["home"] for (collection, key), frame in schema_svg.label_frames(source, drawing)
                if (collection, key) == ("elements", eid))


def test_a_lone_piece_carries_its_label_on_its_middle_not_its_end():
    home = _home(_source([_element()]), "E1")
    assert math.dist(home, (0, 0)) < 1.0, home


def test_a_polyline_carries_its_label_on_the_middle_of_its_length():
    source = _source([_element(points=[[0, 0], [100, 0], [100, 300]])])
    home = _home(source, "E1")
    assert math.dist(home, (100, 100)) < 3.0, home


def test_a_beam_through_a_column_carries_its_label_clear_of_the_node():
    """The planted defect: at the middle of the beam, the label sat on the column, under the other label and a connection's rotation centre."""
    source = _source()
    home = _home(source, "E1")
    assert abs(home[0]) > 100, f"the beam's label is at x = {home[0]}, inside the column's band"
    column = _home(source, "E2")
    assert column[1] > 100, f"the column's label is at z = {column[1]}, inside the beam's band"


# --- the exported figures ----------------------------------------------------------------

def test_the_exported_figures_carry_the_label():
    """Every exported element that follows its position for b and h carries «position class b/h» on the schema's figure, and on the connection's and the connector's figures drawn on that schema.

    ⚠️ It named `SD_01`, a schema the engineer had deleted (periodic audit 260916, B27), and so raised a `KeyError` rather than checking anything: it reads every exported schema now."""
    schemas = conftest.exported("schemas.json")["schemas"]
    followed = [(sid, e) for sid, s in schemas.items() for e in s["elements"] if e.get("b_from") == "position" and e.get("h_from") == "position"]
    if not followed:
        raise Skip("no exported schema element follows its position for both b and h")
    connections = conftest.exported("connections.json")["connections"]
    connectors = conftest.exported("connectors.json")["connectors"]
    for sid, element in followed:
        assert element["b"] and element["h"] and element["width"] in (element["b"], element["h"]), element
        names = ["schemas/%s-de.svg" % sid]
        names += [c["figure"]["files"]["de"] for c in connections.values() if c.get("schema") == sid]
        names += [c["figures"]["pattern"]["de"] for c in connectors.values() if c.get("schema") == sid and c.get("figures")]
        for name in names:
            text = (conftest.PROJECT.data_dir / name).read_text(encoding="utf-8")
            assert element["label"] in text, f"{name} does not carry the label {element['label']!r}"


# --- the crop, the aids, the markers ------------------------------------------------------

def test_the_crop_is_the_exported_frame_and_the_editor_ignores_it():
    source = _source(crop={"x": -300, "z": -150, "w": 600, "h": 400})
    schema.check_source(source, "T_99.json")
    exported = schema_svg.meta(schema_svg.layout(source, positions=POSITIONS))["view"]
    assert (exported["x"], exported["y"], exported["w"], exported["h"]) == (-300, -150, 600, 400)
    editing = schema_svg.layout(source, positions=POSITIONS, editing=True)["bbox"]
    assert editing != (-300, -150, 300, 250), "the canvas must show the whole detail, the crop marked over it"


def test_a_crop_with_no_area_is_refused_and_what_it_leaves_out_is_said():
    for bad in ({"x": 0, "z": 0, "w": 0, "h": 10}, {"x": 0, "z": 0, "w": 10}, "all"):
        source = _source(crop=bad)
        try:
            schema.check_source(source, "T_99.json")
        except Exception:  # noqa: BLE001
            continue
        raise AssertionError(f"crop {bad!r} was accepted")
    source = _source(crop={"x": 1000, "z": 1000, "w": 10, "h": 10})
    source["connectors"].append({"id": "C1", "kind": "Stabdübel", "x": 0, "z": 0})
    notes = schema.warnings(source, POSITIONS)
    assert any("E1" in n and "crop" in n for n in notes) and any("C1" in n and "crop" in n for n in notes), notes


def test_a_construction_line_is_drawn_in_the_editor_and_left_out_of_the_report():
    source = _source()
    source["aids"].append({"id": "A1", "kind": "horizontal", "x": 0, "z": 60, "angle": 0, "shown": False})
    exported = schema_svg.layout(source, positions=POSITIONS)
    editing = schema_svg.layout(source, positions=POSITIONS, editing=True)
    assert not [a for a in exported["aids"] if a["id"] == "A1"]
    drawn = [a for a in editing["aids"] if a["id"] == "A1"]
    assert drawn and drawn[0]["shown"] is False
    assert schema_svg.AID_COLOUR in schema_svg.render(editing), "a hidden line is drawn light, in its own colour"
    assert schema_svg.AID_COLOUR not in schema_svg.render(exported)


def test_a_line_is_hit_near_it_and_only_near_it():
    source = _source()
    source["aids"].append({"id": "A1", "kind": "point-angle", "x": 0, "z": 0, "angle": 45, "shown": False})
    assert schema.hit_aid_line(source, (100, 100), 2) == "A1"
    assert schema.hit_aid_line(source, (-300, -302), 3) == "A1", "a line runs past the two points it was drawn through"
    assert schema.hit_aid_line(source, (100, 120), 2) is None


def test_a_marker_stating_its_diameter_is_drawn_at_it_with_a_floor():
    source = _source()
    source["connectors"] += [{"id": "C1", "kind": "Stabdübel", "x": -60, "z": -60, "diameter": {"value": 12, "unit": "mm"}},
                             {"id": "C2", "kind": "Nagel", "x": 60, "z": -60, "diameter": {"value": 0.5, "unit": "mm"}},
                             {"id": "C3", "kind": "Stabdübel", "x": 60, "z": 60}]
    drawing = schema_svg.layout(source, positions=POSITIONS)
    r = {c["id"]: c["r"] for c in drawing["connectors"]}
    assert r["C1"] == 6.0
    assert r["C2"] == schema_svg.MARKER_FLOOR_SHARE * drawing["radius"], "a nail too thin to see is held to the floor"
    assert r["C3"] == drawing["radius"]
