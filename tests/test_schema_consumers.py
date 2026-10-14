"""A connector and a polar-moment calculation drawn on one schema (docs/domain/connectors.md §3.3nonies, docs/domain/connections.md §3.3quinquies, docs/domain/detail-schemas.md §3.3decies; plan 5 of je-souhaite-commencer-generic-valley.md).

What this file holds is the *seam*, and nothing either side of it already holds: that the two calculations read one drawing rather than two forms, that moving a piece in the schema moves it in both, that what the schema no longer carries warns rather than stops, and that the frame the move introduced -- a member's grain from the schema's x, beside its grain from the reference member's -- is the two different numbers it is supposed to be.

⚠️ The one thing it deliberately does NOT re-check is the arithmetic. `test_connection.py` holds the polar moment against the HB2 method sheet and `test_dowel.py` holds the resistance against `Verbindung.xlsm`, cell by cell; the move changed where the coordinates come from and not what is done with them, and a second copy of those numbers here would be a second place to update when a norm value moves.
"""

import copy
import json

import conftest
from conftest import ROOT, tmpdir
from domains import connection, connector, schema
import validation


def _raised(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except validation.ValidationError as exc:
        return str(exc)
    return ""


def _detail(**overrides):
    """A beam and a column crossing at the origin, with four markers and a centre."""
    detail = {
        "schema_version": schema.SOURCE_SCHEMA_VERSION,
        "id": "D_SEAM",
        "label": "Seam",
        "elements": [
            {"id": "E1", "kind": "linear", "points": [[-230, 0], [230, 0]], "view": "h",
             "h": 200, "position": "T001"},
            {"id": "E2", "kind": "linear", "points": [[0, -100], [0, 230]], "view": "h",
             "h": 200, "position": "S001"},
        ],
        "connectors": [
            {"id": "C1", "kind": "Stabdübel", "x": -60, "z": -60},
            {"id": "C2", "kind": "Stabdübel", "x": 60, "z": -60},
            {"id": "C3", "kind": "Stabdübel", "x": -60, "z": 60},
            {"id": "C4", "kind": "Stabdübel", "x": 60, "z": 60},
        ],
        "aids": [{"id": "A1", "kind": "centre", "x": 30, "z": 0}],
        "dimensions": [],
    }
    detail.update(overrides)
    return detail


def _connection(**overrides):
    source = {
        "schema_version": connection.SOURCE_SCHEMA_VERSION,
        "id": "SD_01-V1",
        "name": "SD_01-V1",
        "label": "",
        "norm": connection.DEFAULT_NORM,
        "norm_ref": "",
        "schema": "D_SEAM",
        "reference": 1,
        "members": [{"name": "", "element": "E1"}, {"name": "", "element": "E2"}],
        "fasteners": ["C1", "C2", "C3", "C4"],
        "center": {"mode": "centroid"},
        "directions": {"N": 0, "V": 90},
    }
    source.update(overrides)
    return source


def _connector(**overrides):
    source = connector.new_source("SD_01", schema="D_SEAM")
    source["assembly"] = "Holz-Holz zweischnittig"
    source["diameter"] = {"value": 14, "unit": "mm"}
    source["fasteners"] = ["C1", "C2", "C3", "C4"]
    source["n_tot"] = {"value": 4, "override": False}
    source["moisture_class"] = 1
    for index, member in enumerate(source["members"]):
        member["element"] = "E%d" % (index + 1)
        member["material"] = None                  # follow the element's position
        member["t"] = {"value": 70 if index == 0 else 100, "unit": "mm"}
        member["n"] = 2
        member["a_1"] = {"value": 120, "unit": "mm"}
        member["alpha"] = 0
    source.update(overrides)
    return source


POSITIONS = {
    "T001": {"material": "C24", "moisture_class": 1},
    "S001": {"material": "GL24h", "moisture_class": 1},
}


# --- one drawing, two calculations ------------------------------------------------

def test_both_calculations_read_the_same_coordinates():
    """The whole point of the move: the connector's pattern and the connection's fastener group are one set
    of numbers, because both are the schema's markers rather than two tables typed twice."""
    detail = _detail()
    geometry = connection.analyse(_connection(), detail)
    drawn = connector.marker_points(_connector(), detail)
    assert [tuple(p) for p in geometry["points"]] == list(drawn)
    assert list(drawn) == [(-60, -60), (60, -60), (-60, 60), (60, 60)]


def test_moving_a_marker_moves_it_in_both():
    """A marker dragged in the «Schémas» tab reaches every calculation drawn on that schema, with nothing
    else to do -- which is what makes one drawing worth the move (section 2, rule 1)."""
    moved = _detail()
    moved["connectors"][0]["x"] = -90
    geometry = connection.analyse(_connection(), moved)
    assert geometry["points"][0] == (-90, -60)
    assert connector.marker_points(_connector(), moved)[0] == (-90, -60)
    # and the polar moment follows, since I_p is built from those very points
    assert geometry["I_px"] != connection.analyse(_connection(), _detail())["I_px"]


def test_a_member_reaches_its_position_through_its_element():
    """The element is the one place a position is named since schema 2.0: the strength class and the moisture
    class are read from the row that element names, and `material` says only whether the class is overridden."""
    record, warnings = connector.build_record(_connector(), POSITIONS, _detail())
    assert warnings == [], warnings
    assert [m["position"] for m in record["members"]] == ["T001", "S001"]
    assert record["members"][0]["grade"] == "C24" and record["members"][1]["grade"] == "GL24h"

    source = _connector()
    source["members"][0]["material"] = {"grade": "GL32h"}       # T001 says C24
    record, _warnings = connector.build_record(source, POSITIONS, _detail())
    assert record["members"][0]["grade"] == "GL32h"
    assert record["members"][0]["position_grade"] == "C24", (
        "the line under the field must still say what the position holds, or «Reprendre» means nothing")


# --- the two angles a member now carries ------------------------------------------

def test_local_and_axis_are_the_same_number_on_a_detail_drawn_along_x():
    """Which is every detail this project has: the reference member's element runs along the schema's x, so
    theta_(r,j) and the angle a force-grain angle is measured against agree, as they did until v0.73."""
    geometry = connection.analyse(_connection(), _detail())
    assert geometry["local"] == geometry["axis"] == [0.0, 90.0]


def test_a_detail_drawn_at_an_angle_parts_them():
    """⚠️ The one real consequence of the frame being the schema's rather than the reference member's.

    Turn the whole detail by 30°: every member's grain from the reference member's is unchanged -- the two
    pieces still meet at 90° -- while its grain from the schema's x moves by 30°, which is what a force's
    components are measured against. A record carrying one number for both would be wrong for one of them.
    """
    turned = _detail()
    turned["elements"][0]["points"] = [[-199.19, -115.0], [199.19, 115.0]]     # 30°
    turned["elements"][1]["points"] = [[50.0, -86.6], [-115.0, 199.19]]       # 120°
    geometry = connection.analyse(_connection(), turned)
    assert [round(a) for a in geometry["local"]] == [0, 90], "the pieces still meet at a right angle"
    assert [round(a) for a in geometry["axis"]] == [30, 120], "and both have turned with the detail"


def test_the_reference_members_local_angle_is_always_zero():
    """theta_(r,r) is not printed, and validation refuses a record whose reference says otherwise -- which is
    what would happen if the record had been built against another reference than it names."""
    for reference in (1, 2):
        geometry = connection.analyse(_connection(reference=reference), _detail())
        assert geometry["local"][reference - 1] == 0.0


# --- what the schema no longer carries: a warning, never a stop -------------------

def test_a_marker_the_schema_lost_warns_and_is_left_out():
    """The v0.33 rule, applied to the seam: the report refuses such a calculation, and the window must still
    be able to open it and tick another marker."""
    short = _detail()
    short["connectors"] = short["connectors"][:3]
    source = _connection()
    connection.check_source(source, "SD_01-V1.json")          # the FILE is well formed; the drawing changed
    geometry = connection.analyse(source, short)
    assert geometry["n"] == 3
    assert geometry["missing"]["markers"] == ["C4"]
    warnings = connection.schema_warnings(source, short, {"D_SEAM": short}, "connections/SD_01-V1.json")
    assert any("C4" in w for w in warnings), warnings


def test_a_schema_that_is_gone_warns_and_names_what_there_is():
    source = _connection(schema="D_GONE")
    connection.check_source(source, "SD_01-V1.json")
    warnings = connection.schema_warnings(source, None, {"D_SEAM": _detail()}, "connections/SD_01-V1.json")
    assert any("D_GONE" in w and "D_SEAM" in w for w in warnings), warnings


def test_a_connector_on_a_schema_that_is_gone_is_described_and_not_calculated():
    record, warnings = connector.build_record(_connector(), POSITIONS, None)
    assert record["calculated"] is False
    assert record["reason"]
    # and the descriptive half is still whole, so the window has something to relink
    for key in ("position", "type", "assembly", "diameter", "elements", "description"):
        assert key in record


# --- the rotation centre a schema may draw ----------------------------------------

def test_a_centre_drawn_in_the_schema_is_turned_about():
    source = _connection(center={"mode": "aid", "aid": "A1"})
    geometry = connection.analyse(source, _detail())
    assert geometry["center"] == (30, 0), "the aid's own place, not the centroid's (0, 0)"
    assert geometry["missing"]["centre"] is None


def test_a_centre_the_schema_lost_falls_back_to_the_centroid_and_says_so():
    """Rather than putting the whole calculation out of reach over one renamed point."""
    source = _connection(center={"mode": "aid", "aid": "A9"})
    geometry = connection.analyse(source, _detail())
    assert geometry["center"] == (0.0, 0.0)
    assert geometry["missing"]["centre"] == "A9"
    # ... and the record says what was calculated: until the audit of 260916 it kept mode "aid" and level 3 printed «Drehpunkt (festgelegt)» over the centroid it had used (AUD-7-302)
    record = connection.build_record(source, _detail())
    assert record["center"]["mode"] == "centroid", record["center"]
    assert record["vars"]["x_c"]["group_label"].startswith("Drehpunkt (Schwerpunkt"), record["vars"]["x_c"]["group_label"]


# --- the sources refuse what they should ------------------------------------------

def test_a_source_that_still_carries_its_own_drawing_is_sent_to_the_migration():
    """A 2.1 connection and a 1.1 connector each hold a member form and a coordinate table. Converting one
    means WRITING a second file -- the schema that drawing becomes -- which a reader must not do quietly."""
    old = _connection(schema_version="2.1")
    assert "migrate_to_schemas" in _raised(connection.check_source, old, "SD_01-V1.json")
    old = _connector(schema_version="1.1")
    assert "migrate_to_schemas" in _raised(connector.check_source, old, "SD_01.json")


def test_a_marker_named_twice_is_refused_on_both_sides():
    assert "twice" in _raised(connection.check_source, _connection(fasteners=["C1", "C1"]), "x.json")
    source = _connector(fasteners=["C1", "C1"])
    source["n_tot"] = {"value": 2, "override": False}
    assert "twice" in _raised(connector.check_source, source, "x.json")


# --- the project as it stands ------------------------------------------------------

def test_every_source_of_this_project_names_a_schema_that_exists():
    """After the migration, nothing in connectors/ or connections/ is left pointing at a drawing that is not
    there -- which is the one thing `migrate_to_schemas.py` could have got wrong and nothing else would say."""
    details = schema.read_sources(conftest.PROJECT.details_dir)
    for reader, folder in ((connector, "connectors"), (connection, "connections")):
        for path in reader.source_paths(ROOT / folder):
            source = reader.read_source(path)
            assert source["schema"] in details, (
                "%s names schema %r, which details/ does not hold (%s)"
                % (path.name, source["schema"], ", ".join(sorted(details))))


def test_the_project_exports_and_both_sides_agree_on_the_geometry():
    """The connector's own pattern and the polar moment of the calculation drawn on it must place the
    fasteners in the same places, since both read one schema."""
    details = schema.read_sources(conftest.PROJECT.details_dir)
    data = conftest.PROJECT.data_dir
    connectors, _images, _warnings = connector.prepare(
        conftest.PROJECT.connectors_dir, connector.known_positions(data), details)
    connections, _figures, _link = connection.prepare(conftest.PROJECT.connections_dir, details)
    # A polar moment names no connector since v0.76: what the two share is the schema.
    for cid, record in connections["connections"].items():
        for linked in connectors["connectors"].values():
            if linked.get("schema") != record.get("schema"):
                continue
            theirs = [(f["x"], f["z"]) for f in linked["fasteners"]]
            ours = [(f["x"], f["z"]) for f in record["fasteners"]]
            assert set(ours) <= set(theirs) or set(theirs) <= set(ours), (
                "%s and connector %s are drawn on schema %s and place their fasteners differently"
                % (cid, linked["position"], record["schema"]))


# --- a polar moment takes construction points too -----------------------------------------

def _points_only():
    """The same joint with its four fasteners drawn as construction POINTS and no connector marker -- what the engineer drew on VU-Skizze."""
    points = [{"id": "A%d" % (i + 2), "kind": "point", "x": x, "z": z, "connector": True}
              for i, (x, z) in enumerate(((-60, -60), (60, -60), (-60, 60), (60, 60)))]
    return _detail(connectors=[], aids=[{"id": "A1", "kind": "centre", "x": 30, "z": 0}] + points)


def test_a_polar_moment_takes_construction_points_as_fasteners():
    """«The module Moments polaires reads connector markers AND points»: a polar moment distributes forces over points, whatever sits on them."""
    on_points = connection.analyse(_connection(fasteners=["A2", "A3", "A4", "A5"]), _points_only())
    on_markers = connection.analyse(_connection(), _detail())
    assert on_points["n"] == 4 and on_points["missing"]["markers"] == []
    assert on_points["I_p"] == on_markers["I_p"] and on_points["points"] == on_markers["points"]
    connection.check_source(_connection(fasteners=["A2", "A3", "A4", "A5"]), "SD_01-V1.json")


def test_a_centre_is_not_a_fastener_and_markers_and_points_mix():
    detail = _detail(aids=[{"id": "A1", "kind": "centre", "x": 30, "z": 0}, {"id": "A2", "kind": "point", "x": 0, "z": 120, "connector": True},
                           {"id": "A3", "kind": "point", "x": 0, "z": -120}])
    geometry = connection.analyse(_connection(fasteners=["C1", "A2", "A1"]), detail)
    assert geometry["n"] == 2 and geometry["missing"]["markers"] == ["A1"]
    assert list(connection.fastener_places(detail)) == ["C1", "C2", "C3", "C4", "A2"], "markers first, then points ticked «connecteur»; never a centre, never an unticked point (v0.77)"


def test_a_connector_takes_the_points_ticked_connecteur_too():
    """v0.77, the engineer: «des points doivent toujours pouvoir être repris par d'autres modules (pas uniquement Moments polaires)» -- A12 to A15 of VU-Skizze were ticked «connecteur» and could not be chosen in «Disposition des broches». A point ticked is a dowel to a connector as it is a fastener to a polar moment: the calculation reads the connector's own `type`, never a marker's kind. Until then this test held the opposite, `test_a_connector_still_takes_markers_only`."""
    on_points = _connector(fasteners=["A2", "A3", "A4", "A5"])
    assert connector.marker_points(on_points, _points_only()) == connector.marker_points(_connector(), _detail())
    assert connector.missing_markers(on_points, _points_only()) == []
    by_points, warnings = connector.build_record(on_points, POSITIONS, _points_only())
    by_markers, _warnings = connector.build_record(_connector(), POSITIONS, _detail())
    assert by_points["calculated"] and not [w for w in warnings if "no longer carries" in w], warnings
    assert [(f["id"], f["x"], f["z"]) for f in by_points["fasteners"]] == [("A2", -60, -60), ("A3", 60, -60), ("A4", -60, 60), ("A5", 60, 60)]
    assert abs(by_points["vars"]["R_d"]["value"] - by_markers["vars"]["R_d"]["value"]) < 1e-9
    # a point left unticked is a point to draw by, for a connector as for a polar moment
    unticked = _points_only()
    for aid in unticked["aids"]:
        aid.pop("connector", None)
    assert connector.marker_points(on_points, unticked) == []
    assert connector.missing_markers(on_points, unticked) == ["A2", "A3", "A4", "A5"]
    # a new calculation ticks the markers, or the points where the schema has no marker -- never both
    assert schema.default_fasteners(_detail()) == ["C1", "C2", "C3", "C4"]
    assert schema.default_fasteners(_points_only()) == ["A2", "A3", "A4", "A5"]


def test_the_schemas_crop_frames_its_own_figure_and_not_the_calculations_drawn_on_it():
    """The crop is what the report shows of the schema itself; a connection's figure and a connector's pattern keep their frame, which their fasteners, arrows and legend need (docs/domain/detail-schemas.md §3.3decies). Until the audit of 260916 both took the crop, and a tight one cut the connector's fasteners off its pattern (AUD-7-309)."""
    import re
    from domains import connection_svg, connector_svg

    def view(svg):
        return re.search(r'viewBox="([^"]+)"', svg).group(1)

    plain, cropped = _detail(), _detail(crop={"x": -30, "z": -30, "w": 60, "h": 60})
    source = _connection()
    assert view(connection_svg.render(connection_svg.layout(source, detail=cropped))) == view(connection_svg.render(connection_svg.layout(source, detail=plain)))
    assert view(connector_svg.pattern_of(_connector(), cropped)) == view(connector_svg.pattern_of(_connector(), plain))


# --- a schema or a marker lost: warned, and never a stop (periodic audit 260916) ----

def _prepared(kind, source, schemas):
    folder = tmpdir("lost_" + kind)
    (folder / ("%s.json" % source["id"])).write_text(json.dumps(source), encoding="utf-8")
    if kind == "connection":
        data, _figures, warnings = connection.prepare(folder, schemas, None)
        return data["connections"][source["id"]], warnings
    data, _images, warnings = connector.prepare(folder, POSITIONS, schemas)
    return data["connectors"][source["id"]], warnings


def test_a_schema_or_a_marker_lost_never_stops_the_export_and_the_calculation_says_why():
    """Section 13, the v0.33 rule: what the schema no longer carries warns and never stops. In a sandbox, deleting the schema VU-Skizze stopped the export on «connections.VU-MP-1: has no fastener», and deleting its point A12 on «connectors.VU-SD-10: n_tot is 4 and the drawing has 3» (periodic audit 260916, AUD-8-1, AUD-8-2). And a connection that lost one marker of four was printed on the three left, with no refusal (AUD-7-301). Each is now exported `calculated: false` with its reason, which the report prints instead of a number."""
    short = _detail()
    short["connectors"] = short["connectors"][:3]
    for kind, source in (("connection", _connection()), ("connector", _connector())):
        for label, schemas, named in (("schema gone", {}, "D_SEAM"), ("marker lost", {"D_SEAM": short}, "C4")):
            try:
                record, warnings = _prepared(kind, copy.deepcopy(source), schemas)
            except validation.ValidationError as exc:
                raise AssertionError(f"{kind}, {label}: the export stopped -- {exc}")
            assert record["calculated"] is False, f"{kind}, {label}: calculated"
            assert named in record["reason"], f"{kind}, {label}: the reason does not name {named}: {record['reason']!r}"
            assert any(named in w for w in warnings), f"{kind}, {label}: no warning names {named}: {warnings}"
    # and an intact schema still calculates both
    for kind, source in (("connection", _connection()), ("connector", _connector())):
        record, _warnings = _prepared(kind, source, {"D_SEAM": _detail()})
        assert record["calculated"] is True, f"{kind}: an intact detail no longer calculates -- {record.get('reason')}"


def test_the_report_refuses_a_polar_moment_the_schema_no_longer_carries():
    """`show-polar-moment`, `show-calc` and `var-of` on a connection exported `calculated: false` stop the compile with its reason, as `show-connector-resistance` does for a connector -- where until the audit of 260916 they printed n = 3 and an I_p of three fasteners (AUD-7-301)."""
    import shutil
    import subprocess
    import conftest
    if not conftest.have_typst():
        from conftest import Skip
        raise Skip("typst is not on the path")
    short = _detail()
    short["connectors"] = short["connectors"][:3]
    root = tmpdir("lost_report")
    python = root / "000-Python"
    shutil.copytree(ROOT / "lib", python / "lib")
    (python / "calc" / "i18n").mkdir(parents=True)
    shutil.copy2(ROOT / "calc" / "i18n" / "strings.json", python / "calc" / "i18n" / "strings.json")
    (root / "commands.typ").write_text('#import "/000-Python/lib/calc-engine.typ": *\n#import "/000-Python/lib/formula.typ": *\n', encoding="utf-8")  # a tree of its own, laid out as until v0.80
    sources = root / "sources"
    sources.mkdir()
    (sources / "SD_01-V1.json").write_text(json.dumps(_connection()), encoding="utf-8")
    connection.export(sources, python / "data", schemas={"D_SEAM": short})
    # what show-calc's lookup reads before it reaches a connection: no domain and no position here
    (python / "data" / "calculations.json").write_text(json.dumps({"schema_version": "1.4", "domains": {}}), encoding="utf-8")
    (python / "data" / "positions-index.json").write_text(json.dumps({"schema_version": "1.0", "positions": []}), encoding="utf-8")
    for call in ('#show-polar-moment("SD_01-V1", V: 10)', '#show-calc("connection", "SD_01-V1")', '#var-of("connection", "SD_01-V1", "I_p")'):
        (root / "probe.typ").write_text('#import "/commands.typ": *\n' + call + "\n", encoding="utf-8")
        run = subprocess.run(["typst", "compile", "--root", str(root), str(root / "probe.typ"), str(root / "probe.pdf")],
                             capture_output=True, text=True, encoding="utf-8")
        assert run.returncode != 0, f"{call} printed a polar moment on the fasteners its schema still carries"
        assert "C4" in run.stderr, f"{call}: the refusal does not say why -- {run.stderr[-400:]}"
