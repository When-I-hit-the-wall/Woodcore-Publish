"""Detail schemas: the source's own checks, the drawing's determinism, and the seam to data/schemas.json (docs/domain/detail-schemas.md §3.3decies).

Three things earn most of the tests here, because each is a decision that could plausibly have gone the other way, exactly as test_connectors.py's own header says of its module:

- **A named point is an aid of kind 'centre' or 'point', not a fifth collection.** A dimension's `{"point": id}` anchor and a connector marker's own `x`/`z` both rest on that choice; the module docstring states it and this file holds it.
- **The source folder is `details/`, not `schemas/`.** `000-Python/schemas/` already holds every `*.schema.json` contract; a schema's own sources living there too would be glob-matched as contracts by `source_paths()`. Caught once, by hand, while writing the first real example (`details/Beispiel.json`) -- `test_a_new_source_passes_its_own_checks` below writes into a scratch `details` directory for the same reason.
- **The tool bar's three ways to draw a rectangle are one function, not three.** Two diagonal clicks are their own shape; three clicks and "one click + Tab" both reduce to an edge and a signed width off it, so they must produce the same points to the digit or the engineer would see the rectangle jump when switching tools.
- **A label the engineer has not moved carries no leader.** `frame["moved"]` is what tells the two apart, and it is what a checker reads on the page: a leader on every label would be as unreadable as a missing one when a label has actually left its symbol.
"""

import json
import re

import conftest
from conftest import ROOT, Skip, tmpdir
from domains import schema, schema_svg
import validation

# the project the tests work on: the example project, copied for this run (conftest.PROJECT, v0.81)
SOURCES = conftest.PROJECT.details_dir
DATA = conftest.PROJECT.data_dir


def _raised(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except validation.ValidationError as exc:
        return str(exc)
    raise AssertionError("%s should have raised a ValidationError" % getattr(fn, "__name__", fn))


def _source(**overrides):
    """A small, valid detail: two linear pieces crossing at a right angle, two dowel markers, a centre and a horizontal dimension."""
    source = schema.new_source("T_99")
    source["elements"] = [
        {"id": "E1", "kind": "linear", "points": [[0, 0], [300, 0]], "position": "T001", "h": 140},
        {"id": "E2", "kind": "linear", "points": [[150, -150], [150, 150]], "h": 80},
    ]
    source["connectors"] = [
        {"id": "C1", "kind": "Stabdübel", "x": 100, "z": 0},
        {"id": "C2", "kind": "Stabdübel", "x": 200, "z": 0},
    ]
    source["aids"] = [{"id": "A1", "kind": "centre", "x": 150, "z": 0}]
    source["dimensions"] = [
        {"id": "D1", "kind": "horizontal", "from": {"x": 0, "z": 0}, "to": {"x": 300, "z": 0}, "offset": -80},
    ]
    source.update(overrides)
    return source


POSITIONS = ["T001", "S001"]


# --- the source folder is details/, not schemas/ ---------------------------------
# Caught once, by hand (module docstring): `000-Python/schemas/` already holds every
# *.schema.json contract, and source_paths() globs *.json without asking what kind
# of file it found. This is what a wrong SOURCES constant looked like before it was
# fixed -- held here so the mistake cannot quietly come back.

def test_the_schemas_folder_holds_no_schema_sources():
    """Every file the real schemas/ folder holds is a *.schema.json contract, never a detail's own source -- reading one as a source must fail loudly rather than silently succeed."""
    contracts = sorted((ROOT / "schemas").glob("*.json"))
    assert contracts, "schemas/ should hold at least the *.schema.json contracts"
    for path in contracts:
        assert _raised(schema.read_source, path), f"{path.name} parsed as a schema source"


def test_the_source_folder_is_not_the_schemas_folder():
    assert SOURCES != ROOT / "schemas"
    assert SOURCES.name == "details"


def test_the_record_names_the_source_it_was_exported_from():
    """The record's `source` is a path from 000-Python/ to the file it was built from. It said `schemas/<id>.json` -- the contracts' folder, the very confusion the move to `details/` removed (periodic audit 260916, AUD-7-311)."""
    record = schema.build_record(_source())
    assert record["source"] == f"{SOURCES.name}/T_99.json", record["source"]


# --- the source -----------------------------------------------------------------

def test_a_new_source_passes_its_own_checks():
    """«Nouveau» must produce something the checks accept, or the tab opens on an error."""
    schema.check_source(schema.new_source("T_01"), "T_01.json")


def test_the_worked_example_passes_its_own_checks():
    schema.check_source(_source(), "T_99.json")


def test_an_id_that_is_not_the_file_name_is_refused():
    path = tmpdir("details") / "T_77.json"
    source = _source(id="T_78")
    path.write_text(json.dumps(source, ensure_ascii=False), encoding="utf-8")
    assert "must agree" in _raised(schema.read_source, path)


def test_a_linear_element_needs_at_least_two_points():
    source = _source()
    source["elements"][0]["points"] = [[0, 0]]
    assert "at least 2 points" in _raised(schema.check_source, source, "T_99.json")


def test_an_area_element_needs_at_least_three_points():
    source = _source()
    source["elements"].append({"id": "E3", "kind": "area", "points": [[0, 0], [10, 0]]})
    assert "at least 3 points" in _raised(schema.check_source, source, "T_99.json")


def test_an_id_is_unique_across_every_collection_at_once():
    """`highlight` names an id and must not have to ask which collection it meant."""
    source = _source()
    source["connectors"][0]["id"] = "E1"
    assert "E1" in _raised(schema.check_source, source, "T_99.json")


def test_a_connector_marker_s_kind_is_one_of_connector_types():
    source = _source()
    source["connectors"][0]["kind"] = "Vampire"
    assert "Vampire" in _raised(schema.check_source, source, "T_99.json")


def test_an_area_element_carries_no_view():
    source = _source()
    source["elements"].append({"id": "E3", "kind": "area", "points": [[0, 0], [10, 0], [10, 10]], "view": "h"})
    assert "only a linear element" in _raised(schema.check_source, source, "T_99.json")


def test_a_two_points_aid_needs_two_distinct_points():
    source = _source()
    source["aids"].append({"id": "A2", "kind": "two-points", "x1": 5, "z1": 5, "x2": 5, "z2": 5})
    assert "same point twice" in _raised(schema.check_source, source, "T_99.json")


def test_an_angle_dimension_of_an_element_with_itself_is_refused():
    source = _source()
    source["dimensions"].append({"id": "D2", "kind": "angle", "from": {"element": "E1"}, "to": {"element": "E1"}})
    assert "with itself" in _raised(schema.check_source, source, "T_99.json")


def test_an_angle_dimension_needs_a_corner_to_turn_about():
    """Two parallel elements never cross."""
    source = _source()
    source["elements"].append({"id": "E3", "kind": "linear", "points": [[0, 50], [300, 50]]})
    source["dimensions"].append({"id": "D2", "kind": "angle", "from": {"element": "E1"}, "to": {"element": "E3"}})
    assert "corner" in _raised(schema.check_source, source, "T_99.json")


def test_an_angle_dimension_between_two_crossing_elements_measures_ninety_degrees():
    source = _source()
    source["dimensions"].append({"id": "D2", "kind": "angle", "from": {"element": "E1"}, "to": {"element": "E2"}, "offset": 40})
    schema.check_source(source, "T_99.json")
    value, unit = schema.dimension_value(source, source["dimensions"][1])
    assert unit == "°"
    assert abs(value - 90.0) < 1e-6


def test_an_angle_may_be_measured_against_a_construction_line():
    """An angle's end names a **direction**: a linear element's axis, or a line-shaped aid. Found by reading rather than by use -- the first version looked a line aid up among the point-shaped ones, refused it as one "the schema does not have", and would have sent the engineer looking for a line that was there all along."""
    source = _source()
    source["aids"].append({"id": "A2", "kind": "point-angle", "x": 150, "z": 0, "angle": 45, "shown": True})
    source["dimensions"].append(
        {"id": "D2", "kind": "angle", "from": {"element": "E1"}, "to": {"aid": "A2"}, "offset": 60}
    )
    schema.check_source(source, "T_99.json")
    value, unit = schema.dimension_value(source, source["dimensions"][1])
    assert abs(value - 45.0) < 1e-6 and unit == "°"


def test_an_angle_against_a_point_aid_is_refused_for_the_right_reason():
    """A point has no direction, and the message must say so rather than claim the aid is missing."""
    source = _source()
    source["dimensions"].append(
        {"id": "D2", "kind": "angle", "from": {"element": "E1"}, "to": {"aid": "A1"}, "offset": 60}
    )
    message = _raised(schema.check_source, source, "T_99.json")
    assert "no direction" in message


def test_a_dimension_s_point_anchor_follows_its_aid():
    """{"point": id} tracks the aid; {"x", "z"} stays where it was put -- statics.py's own rule (section 3.3octies), which schema.py's dimension_anchor carries over unchanged."""
    source = _source()
    source["dimensions"].append({"id": "D2", "kind": "horizontal", "from": {"point": "A1"}, "to": {"x": 300, "z": 0}})
    schema.check_source(source, "T_99.json")
    before = schema.dimension_ends(source, source["dimensions"][1])
    source["aids"][0]["x"] = 50.0
    after = schema.dimension_ends(source, source["dimensions"][1])
    assert before[0] != after[0]
    assert after[0] == (50.0, 0.0)


# --- drawing an area element (the three tool-bar modes) -------------------------

def test_the_three_ways_to_draw_a_rectangle_agree_to_the_digit():
    """Two diagonal clicks; an edge and a third click's own perpendicular width; an edge and a typed width -- the second and third are one function (rectangle_from_edge), and all three must land on the same box."""
    diagonal = schema.rectangle_two_corners((0.0, 0.0), (100.0, 50.0))
    three_clicks = schema.rectangle_from_edge((0.0, 0.0), (100.0, 0.0), 50.0)
    typed = schema.rectangle_from_edge(
        (0.0, 0.0), schema.typed_point((0.0, 0.0), {"unit": (1.0, 0.0)}, "100"), 50.0
    )
    assert diagonal == three_clicks == typed


def test_a_rectangle_drawn_the_other_way_round_gives_the_reflected_width():
    """A third click (or a typed width) on the other side of the edge is a negative width, and the box is drawn on that side instead -- the sign is the tool's own answer to "which side", not an error."""
    left = schema.rectangle_from_edge((0.0, 0.0), (100.0, 0.0), 50.0)
    right = schema.rectangle_from_edge((0.0, 0.0), (100.0, 0.0), -50.0)
    assert left[2][1] == 50.0
    assert right[2][1] == -50.0


# --- the drawing: labels, aids and determinism -----------------------------------

def test_an_unmoved_label_carries_no_leader():
    source = _source()
    drawing = schema_svg.layout(source)
    frame = next(f for c, i, f in drawing["label_frames"] if (c, i) == ("connectors", "C1"))
    assert frame["moved"] is False


def test_a_label_dragged_clear_of_its_symbol_carries_a_leader():
    source = _source()
    source["connectors"][0]["label_offset"] = [40.0, -40.0]
    drawing = schema_svg.layout(source)
    frame = next(f for c, i, f in drawing["label_frames"] if (c, i) == ("connectors", "C1"))
    assert frame["moved"] is True
    assert frame["at"] != frame["home"]


def test_a_piece_s_label_dragged_back_onto_the_piece_loses_its_leader():
    """The engineer, v0.77: a label moved off its piece grows a leader, and brought back onto the piece's axis the leader must go again. Until then `moved` alone decided -- any stored offset, however small, kept the leader -- so a label dropped back on its own band still carried a line to a dot a few millimetres away."""
    def leader_of(offset):
        source = _source()
        source["elements"][0]["label_offset"] = offset
        drawing = schema_svg.layout(source)
        frame = next(f for c, i, f in drawing["label_frames"] if (c, i) == ("elements", "E1"))
        out = []
        schema_svg._leader(out, frame, drawing["sz"])
        assert bool(out) == frame["leader"], "the flag is what the drawing reads"
        return frame
    along = leader_of([40.0, 0.0])
    assert along["moved"] and not along["leader"], "moved along its own axis: no leader"
    inside = leader_of([0.0, 50.0])
    assert inside["moved"] and not inside["leader"], "still inside its 140 mm band: on the piece"
    off = leader_of([0.0, 160.0])
    assert off["moved"] and off["leader"], "clear of its band: the leader says whose it is"
    area = _source()
    area["elements"].append({"id": "E3", "kind": "area", "points": [[400, 0], [600, 0], [600, 200], [400, 200]], "label_offset": [30.0, 30.0]})
    frame = next(f for c, i, f in schema_svg.layout(area)["label_frames"] if (c, i) == ("elements", "E3"))
    assert frame["moved"] and not frame["leader"], "an area's label moved within its outline"


def test_a_line_shaped_aid_is_absent_from_the_export_by_default_and_a_point_is_present():
    source = _source()
    source["aids"].append({"id": "A2", "kind": "vertical", "x": 50, "z": 0, "angle": 90})
    schema.check_source(source, "T_99.json")
    record = schema.build_record(source, POSITIONS)
    ids = {a["id"] for a in record["aids"]}
    assert "A1" in ids    # a point/centre is shown unless told otherwise
    assert "A2" not in ids  # a line is hidden unless `shown` says so


def test_a_line_shaped_aid_marked_shown_reaches_the_export():
    source = _source()
    source["aids"].append({"id": "A2", "kind": "vertical", "x": 50, "z": 0, "angle": 90, "shown": True})
    record = schema.build_record(source, POSITIONS)
    ids = {a["id"] for a in record["aids"]}
    assert "A2" in ids


def test_the_drawing_is_identical_when_nothing_moved():
    source = _source()
    first = schema_svg.render(schema_svg.layout(source))
    second = schema_svg.render(schema_svg.layout(source))
    assert first == second


def test_an_element_s_position_that_positionen_no_longer_has_is_unresolved_and_not_a_stop():
    """The v0.33 pattern applied to a fourth editor (docs/decisions.md §13): a reference that no longer resolves warns and does not stop the export."""
    source = _source()
    source["elements"][0]["position"] = "D999"
    schema.check_source(source, "T_99.json")  # does not raise
    record = schema.build_record(source, POSITIONS)
    assert record["unresolved"] == ["E1: position 'D999' is not a position of the project"]
    notes = schema.warnings(source, POSITIONS)
    assert any("D999" in n and n.startswith("schema") for n in notes)


def test_an_element_s_position_that_positionen_has_is_not_unresolved():
    record = schema.build_record(_source(), POSITIONS)
    assert record["unresolved"] == []


# --- export -----------------------------------------------------------------------

def test_prepare_validates_against_the_schemas():
    data, files, notes = schema.prepare(_write(_source()), POSITIONS)
    validation.validate_structure(data, "schemas")
    validation.validate_schemas_business(data)
    assert notes == []
    assert set(files) == {"schemas/T_99-de.svg", "schemas/T_99-fr.svg", "schemas/T_99-en.svg"}


def test_export_writes_and_sweeps_stale_figures():
    source_dir = _write(_source())
    data_dir = tmpdir("data")
    schema.export(source_dir, data_dir, POSITIONS)
    assert (data_dir / "schemas.json").is_file()
    before = sorted(p.name for p in (data_dir / "schemas").iterdir())
    assert before == ["T_99-de.svg", "T_99-en.svg", "T_99-fr.svg"]
    (source_dir / "T_99.json").unlink()
    schema.export(source_dir, data_dir, POSITIONS)
    after = list((data_dir / "schemas").iterdir())
    assert after == []


def _write(source):
    d = tmpdir("details")
    (d / f"{source['id']}.json").write_text(json.dumps(source, ensure_ascii=False), encoding="utf-8")
    return d


# --- construction lines and snapping ---------------------------------------------------

def test_a_construction_line_runs_to_the_edges_of_the_frame():
    """It used to stop a share of the detail's size either side of its own point -- a few centimetres on a large detail, and short of the frame on one side when its point lay off-centre."""
    source = _source()
    source["aids"].append({"id": "A2", "kind": "vertical", "x": 290, "z": -140, "angle": 90, "shown": True})
    source["aids"].append({"id": "A3", "kind": "horizontal", "x": 0, "z": 40, "angle": 0, "shown": True})
    drawing = schema_svg.layout(source)
    x0, z0, x1, z1 = drawing["bbox"]
    lines = {a["id"]: a["line"] for a in drawing["aids"] if a["line"] is not None}
    (ax, az), (bx, bz) = lines["A2"]
    assert abs(ax - 290) < 1e-9 and abs(bx - 290) < 1e-9
    assert {round(az, 6), round(bz, 6)} == {round(z0, 6), round(z1, 6)}
    (ax, az), (bx, bz) = lines["A3"]
    assert {round(ax, 6), round(bx, 6)} == {round(x0, 6), round(x1, 6)}


def test_a_line_that_misses_the_frame_is_not_drawn():
    assert schema_svg.clip_line((0.0, 500.0), (1.0, 0.0), (0.0, 0.0, 100.0, 100.0)) is None
    ends = schema_svg.clip_line((50.0, 50.0), (0.6, 0.8), (0.0, 0.0, 100.0, 100.0))
    assert ends is not None and all(-1e-9 <= c <= 100 + 1e-9 for p in ends for c in p)


def test_construction_aids_are_drawn_over_the_pieces_the_lines_last():
    source = _source()
    source["aids"].append({"id": "A2", "kind": "vertical", "x": 50, "z": 0, "angle": 90, "shown": True})
    svg = schema_svg.render(schema_svg.layout(source))
    opening = svg.index(schema_svg.AIDS_OPEN)
    assert svg.rindex("<polygon") < opening, "every piece is drawn before the aids"
    assert svg.rindex("<circle", 0, opening) < opening, "and every marker"
    aids = svg[opening:svg.index(schema_svg.AIDS_CLOSE)]
    assert aids.index("<circle") < aids.index("stroke-dasharray"), "the centre, then the lines over it"


def test_a_point_is_a_green_cross_drawn_over_the_lines():
    """v0.77, the engineer: «les points doivent être des croix vertes, affichées devant tout, même les lignes d'aides, afin d'être toujours visibles». A centre keeps its grey cross and circle, under the lines."""
    source = _source()
    source["aids"].append({"id": "A2", "kind": "vertical", "x": 50, "z": 0, "angle": 90, "shown": True})
    source["aids"].append({"id": "A3", "kind": "point", "x": 60, "z": 40, "shown": True})
    svg = schema_svg.render(schema_svg.layout(source))
    aids = svg[svg.index(schema_svg.AIDS_OPEN):svg.index(schema_svg.AIDS_CLOSE)]
    green = aids.index(schema_svg.POINT_COLOUR)
    assert green > aids.rindex("stroke-dasharray"), "the point is drawn after every construction line"
    assert aids.count(schema_svg.POINT_COLOUR) == 2, "one stroke each way: a cross"
    assert schema_svg.POINT_COLOUR not in aids[:aids.index("<circle") + 200], "the centre is not green"
    # the canvas draws the points itself, after its own lines, so the SVG it renders carries none
    assert schema_svg.POINT_COLOUR not in schema_svg.render(schema_svg.layout(source), aid_lines=False, aid_points=False)
    assert schema_svg.POINT_COLOUR in schema_svg.swatch("point"), "the tool shows what it puts down"


def test_the_canvas_svg_leaves_the_lines_to_the_canvas():
    source = _source()
    source["aids"].append({"id": "A2", "kind": "vertical", "x": 50, "z": 0, "angle": 90, "shown": False})
    drawing = schema_svg.layout(source, editing=True)
    assert "stroke-dasharray" in schema_svg.render(drawing)
    assert "stroke-dasharray" not in schema_svg.render(drawing, aid_lines=False)


def test_where_two_pieces_cross_is_a_snap_point():
    """«Un point d'intersection entre deux éléments doit être un point d'accroche»: the corners of the square where a beam's band crosses a column's, not only the crossing of their axes."""
    source = _source()
    # E1: along x at z = 0, h = 140 -> edges at z = +-70; E2: along z at x = 150, h = 80 -> edges at x = 110 and 190
    for target in ((110.0, -70.0), (190.0, 70.0), (150.0, 0.0), (110.0, 70.0)):
        near = (target[0] + 1.5, target[1] - 1.5)
        point, kind = schema.snap(source, near, 4.0)
        assert kind in ("crossing", "point") and abs(point[0] - target[0]) < 1e-6 and abs(point[1] - target[1]) < 1e-6, (target, point, kind)


def test_a_construction_line_crossing_a_piece_or_another_line_is_a_snap_point():
    source = _source()
    source["aids"].append({"id": "A2", "kind": "vertical", "x": 40, "z": 0, "angle": 90})
    source["aids"].append({"id": "A3", "kind": "horizontal", "x": 0, "z": 200, "angle": 0})
    point, kind = schema.snap(source, (41.0, 201.0), 4.0)
    assert kind == "crossing" and point == (40.0, 200.0)
    point, kind = schema.snap(source, (41.0, -69.0), 4.0)
    assert kind == "crossing" and abs(point[1] + 70.0) < 1e-9
    point, kind = schema.snap(source, (40.5, 120.0), 4.0)
    assert kind == "on-line" and point == (40.0, 120.0), "a point slides along a construction line"


def test_show_schema_prints_the_aids_the_engineer_left_shown():
    """`show-schema(id)` stripped every aid by default, `aids: false`, so the points ticked «visible» in the «Schémas» tab -- A12 to A15 of VU-Skizze -- never reached the report unless the call said `aids: true` (periodic audit 260916, AUD-7-219). The export already leaves out what is not ticked, a construction line by default; what it keeps is printed."""
    import base64
    import re
    import subprocess
    import conftest
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    records = json.loads((DATA / "schemas.json").read_text(encoding="utf-8"))["schemas"]
    shown = [sid for sid, m in records.items() if m.get("aids")]
    if not shown:
        raise Skip("no exported schema carries a shown aid")
    d = conftest.probe_dir("show_schema_aids")
    probe = d / "probe.typ"

    def embedded(call):
        probe.write_text('#import "/commands.typ": *\n' + call + "\n", encoding="utf-8")
        out = d / "probe.svg"
        run = subprocess.run(["typst", "compile", "--root", str(conftest.TYPST_ROOT), "--format", "svg", str(probe), str(out)],
                             capture_output=True, text=True, encoding="utf-8")
        assert run.returncode == 0, run.stderr
        text = out.read_text(encoding="utf-8")
        return "".join(base64.b64decode(b).decode("utf-8", "replace") for b in re.findall(r"data:image/svg\+xml;base64,([A-Za-z0-9+/=]+)", text))

    sid = shown[0]
    assert schema_svg.POINT_COLOUR in embedded(f'#show-schema("{sid}")'), f"show-schema(\"{sid}\") left out the aids its source shows"
    assert schema_svg.POINT_COLOUR not in embedded(f'#show-schema("{sid}", aids: false)'), "aids: false no longer leaves the aids out"


def test_a_marker_s_a_dimension_s_and_an_aid_s_label_dragged_clear_carry_a_leader_and_an_aid_s_label_is_drawn():
    """Section 3.3decies: a piece's, a marker's, an aid's and a dimension's label may each be dragged clear, and a thin leader runs back once it has left its place. Only a piece's did: a marker's and a dimension's label moved away had no leader, and an aid's `label` was accepted by the check and drawn nowhere (periodic audit 260916, AUD-7-310)."""
    source = _source()
    source["connectors"][0]["label_offset"] = [60.0, -90.0]
    source["dimensions"][0]["label_offset"] = [0.0, -120.0]
    source["aids"].append({"id": "A2", "kind": "point", "x": 250, "z": 60, "label": "Punkt A", "label_offset": [80.0, 80.0]})
    drawing = schema_svg.layout(source)
    frames = {(c, i): f for c, i, f in drawing["label_frames"]}
    assert ("aids", "A2") in frames, "an aid's label has no frame, so it can be neither drawn nor dragged"
    for key in (("connectors", "C1"), ("dimensions", "D1"), ("aids", "A2")):
        out = []
        schema_svg._leader(out, frames[key], drawing["sz"])
        assert out, f"{key} was dragged clear and carries no leader"
    svg = schema_svg.render(drawing)
    assert "Punkt A" in svg, "the aid's label is not drawn"
    # unmoved, no leader
    still = schema_svg.layout(_source())
    for key in (("connectors", "C1"), ("dimensions", "D1")):
        frame = next(f for c, i, f in still["label_frames"] if (c, i) == key)
        out = []
        schema_svg._leader(out, frame, still["sz"])
        assert not out, f"{key} has not moved and carries a leader"


# --- a marker's and a point's halo over the pieces; what a dimension writes ------------------------------


def test_a_marker_s_and_a_point_s_halo_go_over_the_pieces_and_under_the_marker():
    """«La mise en évidence d'un point dans show-schema est invisible, cachée sous les pièces. Un point doit être affiché au-dessus de tout.» The report put every halo at HIGHLIGHT_MARK, before the pieces, which are filled at three quarters opacity: a halo round a pin inside a beam could not be seen. HIGHLIGHT_POINTS_MARK stands after the pieces, their labels and the dimensions, and before the markers and the aids -- so the ring shows round what it marks, and the marker and the green cross are still drawn over it. It is outside the aids' span, which `aids: false` strips."""
    source = _source()
    source["aids"].append({"id": "A3", "kind": "point", "x": 60, "z": 40, "shown": True})
    svg = schema_svg.render(schema_svg.layout(source))
    mark = svg.index(schema_svg.HIGHLIGHT_POINTS_MARK)
    assert svg.count(schema_svg.HIGHLIGHT_POINTS_MARK) == 1
    # a piece's halo and a dimension's stay where they were, under the pieces
    assert svg.index(schema_svg.HIGHLIGHT_MARK) < svg.index("<polygon") < mark
    assert _pieces(svg) and max(_pieces(svg)) < mark, "a piece is drawn over the halo"
    assert svg.rindex("stroke-linecap=\"butt\"", 0, mark) > svg.index(schema_svg.HIGHLIGHT_MARK), "the dimension's lines are drawn before it"
    assert mark < svg.index(f'fill="{schema_svg.CONNECTOR_FILL}"'), "the markers are drawn over the halo"
    assert mark < svg.index(schema_svg.AIDS_OPEN) < svg.index(schema_svg.POINT_COLOUR), "and the aids, the green cross last"
    stripped = svg[:svg.index(schema_svg.AIDS_OPEN)] + svg[svg.index(schema_svg.AIDS_CLOSE):]
    assert schema_svg.HIGHLIGHT_POINTS_MARK in stripped, "`aids: false` takes the mark with it"
    # the window's own ring round a selected marker is drawn in the same place: over the pieces, under the marker
    ringed = schema_svg.render(schema_svg.layout(source), highlight=("connectors", "C1"))
    ring = ringed.index(f'stroke="{schema_svg.HIGHLIGHT}"')
    assert max(_pieces(ringed)) < ring < ringed.index(f'fill="{schema_svg.CONNECTOR_FILL}"')


def _pieces(svg):
    """Where every piece's own polygon stands in `svg`.

    ⚠️ Named by the pieces' own fill opacity and not by «the last `<polygon`»: since v0.99 a label is set over its own box, which is a polygon too (`LABEL_GROUND_OPACITY`), and a marker's box is drawn with the marker -- after the halo, which is exactly where it belongs. The proxy said «piece» and meant «polygon», and the halo it was written for is unchanged.
    """
    opacity = f'fill-opacity="{schema_svg.ELEMENT_OPACITY}"'
    return [m.start() for m in re.finditer(re.escape("<polygon") + r"[^>]*" + re.escape(opacity), svg)]


def test_a_schema_dimension_writes_what_its_show_asks_for():
    """A static model's own four (statics.dimension_show), restated in schema.py and held equal here."""
    from domains import statics
    assert schema.LABEL_MODES == statics.LABEL_MODES
    cases = [
        ({"show": "value", "label": "a"}, "300 mm"),
        ({"show": "name", "label": "a"}, "a"),
        ({"show": "name+value", "label": "a"}, "a = 300 mm"),
        ({"show": "none", "label": "a"}, ""),
        ({"show": "name"}, ""),
        ({"label": "a"}, "a"),
        ({}, "300 mm"),
    ]
    for fields, want in cases:
        source = _source()
        source["dimensions"][0].update(fields)
        schema.check_source(source, "T_99.json")
        drawing = schema_svg.layout(source)
        assert drawing["dimensions"][0]["text"] == want, (fields, drawing["dimensions"][0]["text"])
        record = schema.build_record(source)["dimensions"][0]
        assert record["text"] == want and record["show"] == schema.dimension_show(source["dimensions"][0]), (fields, record)
        framed = [key for key, _frame in schema_svg.label_frames(source, drawing) if key[0] == "dimensions"]
        assert bool(framed) == bool(want), f"{fields}: a dimension that writes nothing still has a label to hit"
        if want:
            assert f">{want}<" in schema_svg.render(drawing), f"{fields}: {want!r} is not written on the figure"
    bad = _source()
    bad["dimensions"][0]["show"] = "both"
    assert "both" in _raised(schema.check_source, bad, "T_99.json")


# --- an area element with a side fixed by a position (v0.117) -----------------------------------------------

def test_a_position_fixes_one_side_of_an_area_and_the_other_is_drawn():
    """v0.117, the engineer: «je dois pouvoir choisir si je dessine la largeur ou la hauteur de la position. Ensuite, je dessine l'élément qui possède donc une largeur fixe». The values are `section.sides`' -- the one reader of a dimension --, nothing here recomputes them."""
    rec = {"section_type": "rec", "dimension": "100/200", "units": "mm"}     # no `section` record: the same deduction the export applies
    assert schema.area_fixed(rec, "b") == {"draw": "b", "fixed": "h", "length": 200.0}, "the width is drawn, the height is the position's"
    assert schema.area_fixed(rec, "h") == {"draw": "h", "fixed": "b", "length": 100.0}, "the height is drawn, the width is the position's"
    assert schema.area_fixed(rec) == schema.area_fixed(rec, "b")
    cm = {"section": {"type": "rec", "kind": "timber", "text": "10/20 cm", "b": 100, "h": 200}}
    assert schema.area_fixed(cm, "h")["length"] == 100.0, "in mm, whatever the sheet's unit"
    # a section with one dimension fixes that one, and the rest is drawn whichever way `draw` says
    plate = {"section": {"type": "pla", "kind": "timber", "text": "22 mm", "t": 22}}
    assert schema.area_fixed(plate, "h") == schema.area_fixed(plate, "b") == {"draw": "", "fixed": "t", "length": 22.0}
    assert schema.area_fixed({"section": {"type": "cir", "kind": "timber", "text": "Ø 160 mm", "d": 160}}) == {"draw": "", "fixed": "d", "length": 160.0}
    assert schema.area_fixed({"section": {"type": "clt", "kind": "timber", "text": "20/30/20 mm (70 mm)", "layers": [20, 30, 20], "t": 70}})["length"] == 70.0
    # a steel profile carries none this module knows, a position with no section none either
    assert schema.area_fixed({"section": {"type": "IPE", "kind": "steel", "text": "IPE 200", "dims": [200]}}) is None
    assert schema.area_fixed({"dimension": "nach Plan"}) is None and schema.area_fixed({}) is None and schema.area_fixed(None) is None


def test_a_drag_with_a_fixed_side_gives_the_rectangle_that_follows_the_cursor():
    assert schema.rectangle_with_fixed_side((0, 0), (300, 40), 200, "b") == [(0, 0), (300, 0), (300, 200), (0, 200)], "the width is the drag's, the height 200"
    assert schema.rectangle_with_fixed_side((0, 0), (30, 140), 100, "h") == [(0, 0), (100, 0), (100, 140), (0, 140)], "the height is the drag's, the width 100"
    # it follows the cursor: left and down give a rectangle left and down
    assert schema.rectangle_with_fixed_side((0, 0), (-300, -40), 200, "b") == schema.rectangle_two_corners((0, 0), (-300, -200))
    assert schema.rectangle_with_fixed_side((0, 0), (300, -40), 200, "b") == schema.rectangle_two_corners((0, 0), (300, -200))
    # one dimension: the longer extent of the drag is the length of the piece, the thickness lies across it
    assert schema.rectangle_with_fixed_side((0, 0), (300, 40), 22, "") == [(0, 0), (300, 0), (300, 22), (0, 22)]
    assert schema.rectangle_with_fixed_side((0, 0), (40, 300), 22, "") == [(0, 0), (22, 0), (22, 300), (0, 300)]
    # by an edge: the third click only says on which side of it the rectangle lies
    assert schema.rectangle_with_fixed_width((0, 0), (300, 0), (100, 50), 22) == [(0, 0), (300, 0), (300, 22), (0, 22)]
    assert schema.rectangle_with_fixed_width((0, 0), (300, 0), (100, 5000), 22) == [(0, 0), (300, 0), (300, 22), (0, 22)], "its distance is ignored"
    assert schema.rectangle_with_fixed_width((0, 0), (300, 0), (100, -50), 22) == [(0, 0), (300, 0), (300, -22), (0, -22)]
