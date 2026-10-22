"""A position plan's dimensions (calc/domains/plan.py, plan_svg.py, dimension.py; issue #9, spec docs/requirements/completed/2026-10-08-plan-positions-cotes-numerotation-sections.md, REQ-010, ARCH-003, ARCH-004, D-006, D-016).

The engineer, 08.10.2026: «Ajouter des outils de cotation pour pouvoir coter les plans» -- aligned, horizontal or vertical, a chain of them, an angle (rayon et diamètre abandonnés: a plan has no circle).

What is held: each kind measures what it says, in metres from the plan's scale or in degrees, computed from its points and never typed; the drawing writes it between markers it writes only where there is one, so a plan without any is drawn byte for byte as before (tests/test_plan_style.py's hashes); the export carries the values, additive; a plan with no scale draws no length and says why, an angle needing none; a malformed dimension stops the export naming the file and the dimension; the static models and the schemas measure with the same core.
"""

TIER = "fast"  # tests/run_tests.py --fast

import copy

import validation
from domains import dimension
from domains import plan as model
from domains import plan_svg
from domains import schema, statics


def _plan(*dims):
    """A plan calibrated at 100 sheet units a metre, carrying `dims`."""
    source = model.new_source("P90", floor="1")
    source["scale"] = {"mode": "calibration", "points": [[0, 0], [100, 0]], "length_m": 1.0}
    source["dimensions"] = list(dims)
    model.check_source(source, "P90.json")
    return source


def _values(source):
    return [[round(part["value"], 6) for part in model.dimension_parts(source, dim)] for dim in source["dimensions"]]


def test_each_kind_measures_what_it_says_in_metres_or_degrees():
    a, b = [0, 0], [300, 400]
    source = _plan({"kind": "parallel", "points": [a, b], "offset": 20},
                   {"kind": "horizontal", "points": [a, b], "offset": -30},
                   {"kind": "vertical", "points": [a, b]},
                   {"kind": "chain", "axis": "horizontal", "points": [[0, 0], [100, 50], [300, 0]], "offset": 40},
                   {"kind": "angle", "points": [[0, 0], [100, 0], [0, 100]]})
    assert _values(source) == [[5.0], [3.0], [4.0], [1.0, 2.0], [90.0]]
    # a chain's segments share one line: every witness line is parallel, every end carried onto the same y
    chain = model.dimension_parts(source, source["dimensions"][3])
    ys = {round(y, 9) for part in chain for _x, y in part["line"]}
    assert len(ys) == 1, ys
    # the line follows the ends: `offset` from their middle
    (p, q), = [part["line"] for part in model.dimension_parts(source, source["dimensions"][0])]
    middle = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
    assert abs(((middle[0] - 150) ** 2 + (middle[1] - 200) ** 2) ** 0.5 - 20) < 1e-9
    assert model.dimension_value_text(chain[0]) == "1.00 m" and model.dimension_value_text({"value": 37.5, "unit": "°"}) == "37.5°"


def test_the_drawing_writes_them_between_markers_written_only_where_there_are_some():
    source = _plan({"kind": "parallel", "points": [[100, 100], [600, 100]], "offset": 30})
    svg = plan_svg.render(source)
    assert svg.count(plan_svg.DIMENSIONS_OPEN) == 1 and svg.count(plan_svg.DIMENSIONS_CLOSE) == 1
    inside = svg.split(plan_svg.DIMENSIONS_OPEN)[1].split(plan_svg.DIMENSIONS_CLOSE)[0]
    assert "5.00 m" in inside and plan_svg.DIMENSION_COLOUR in inside
    bare = copy.deepcopy(source)
    bare.pop("dimensions")
    assert plan_svg.DIMENSIONS_OPEN not in plan_svg.render(bare), "a plan without dimensions writes no marker"
    # its own sizes: a text factor makes the value larger, and nothing else on the plan
    own = copy.deepcopy(source)
    own["dimensions"][0]["style"] = {"text": 2.0}
    model.check_source(own, "P90.json")
    assert plan_svg.render(own) != svg


def test_the_export_carries_what_they_measure_and_a_plan_without_a_scale_draws_no_length():
    source = _plan({"kind": "horizontal", "points": [[0, 0], [250, 80]]}, {"kind": "angle", "points": [[0, 0], [100, 0], [100, 100]], "offset": 40})
    record = model.build_record(source, (1000.0, 700.0))
    assert record["dimensions"] == [{"kind": "horizontal", "points": [[0, 0], [250, 80]], "values": [2.5], "unit": "m"},
                                    {"kind": "angle", "points": [[0, 0], [100, 0], [100, 100]], "values": [45], "unit": "°"}], record["dimensions"]
    plans_schema = validation.load_schema("plans")["properties"]["plans"]
    item = next(iter(plans_schema["patternProperties"].values()))["properties"]["dimensions"]
    validation._validate_node(record["dimensions"], item, "plans.P90.dimensions")   # the field as schemas/plans.schema.json states it
    assert "dimensions" not in model.build_record(_plan(), (1000.0, 700.0)), "written only where a plan has some"
    # no scale: no length is measured -- not drawn, not exported, and said; an angle needs none
    unscaled = copy.deepcopy(source)
    unscaled.pop("scale")
    assert model.dimension_parts(unscaled, unscaled["dimensions"][0]) == []
    assert [d["kind"] for d in model.build_record(unscaled, (1000.0, 700.0))["dimensions"]] == ["angle"]
    notes = model.warnings(unscaled, [])
    assert any(n.code == "plan_dimensions_no_scale" for n in notes), [n.code for n in notes]
    assert not any(n.code == "plan_dimensions_no_scale" for n in model.warnings(source, []))


def test_a_malformed_dimension_stops_naming_the_file_and_the_dimension():
    for dim, said in (({"kind": "radius", "points": [[0, 0], [1, 1]]}, "'radius'"),
                      ({"kind": "parallel", "points": [[0, 0]]}, "needs 2 points"),
                      ({"kind": "chain", "points": [[0, 0], [9, 9]]}, "needs 3 or more"),
                      ({"kind": "parallel", "points": [[0, 0], [0, 0]]}, "the same point"),
                      ({"kind": "chain", "axis": "oblique", "points": [[0, 0], [1, 0], [2, 0]]}, "'oblique'"),
                      ({"kind": "parallel", "points": [[0, 0], [9, 0]], "offset": "far"}, "offset"),
                      ({"kind": "parallel", "points": [[0, 0], [9, 0]], "style": {"point": 2}}, "style")):
        source = model.new_source("P91")
        source["dimensions"] = [dim]
        try:
            model.check_source(source, "P91.json")
        except validation.ValidationError as exc:
            assert "P91.json" in str(exc) and ("dimension 1" in str(exc) or "dimensions[0]" in str(exc)) and said in str(exc), (dim, str(exc))
        else:
            raise AssertionError(f"accepted: {dim}")
    # a 1.4 source is read as it is
    old = model.new_source("P92")
    old["schema_version"] = "1.4"
    model.check_source(old, "P92.json")


def test_the_static_models_the_schemas_and_the_plans_measure_with_one_core():
    """ARCH-004: one geometry. The two older figures' kinds are the core's, and the core gives what each of them computed before it."""
    assert statics.DIMENSION_KINDS == schema.DIMENSION_KINDS == dimension.KINDS
    assert set(model.DIMENSION_KINDS) == set(dimension.LINEAR) | {"chain", "angle"}
    a, b = (0.0, 0.0), (3.0, 4.0)
    assert dimension.linear_value("parallel", a, b) == 5.0 and dimension.linear_value("horizontal", a, b) == 3.0
    (p, q) = dimension.line("parallel", a, b, 0.0, 1e-9)
    assert max(abs(p[0]), abs(p[1]), abs(q[0] - 3.0), abs(q[1] - 4.0)) < 1e-12
    assert dimension.direction("parallel", a, a, 1e-9) is None and dimension.crossing((0, 0), (1, 0), (0, 1), (1, 0), 1e-6) is None
    sweep, start = dimension.arc((1.0, 0.0), (0.0, 1.0), False)
    assert (round(sweep, 9), round(start, 9)) == (90.0, 0.0) and dimension.arc((1.0, 0.0), (0.0, 1.0), True)[0] == -270.0
    assert dimension.text("name+value", "l", "5 m") == "l = 5 m" and dimension.text("name", "", "5 m") == ""
