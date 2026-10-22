"""The dimension tools of the position plan (calc/tools/plan_canvas_tools.py, dimension_icons.py; issue #9, REQ-010, UI-004).

What is held: a linear dimension is its two points then a click for its line, a chain its points, Enter, then its line, an angle its corner and a point on each side -- each written into the plan in one step of «Annuler», and selected; a dimension is taken by a click on its line, its line moved by dragging it, in one step, and deleted with the selection; Escape gives up the one being drawn; and a dimension tool shows the same symbol in the static models', the schemas' and the plans' bars.
"""

TIER = "fast"  # tests/run_tests.py --fast

from test_plan_canvas_rework import _canvas, _qt, _source

from domains import plan


def _plan():
    source = _source()
    source["scale"] = {"mode": "calibration", "points": [[0, 0], [100, 0]], "length_m": 1.0}
    return source


def _canvas_for(source):
    canvas = _canvas(source, None)
    changes = []
    canvas.about_to_change.connect(lambda: changes.append(True))
    canvas.snap_axes = canvas.snap_elements = False
    return canvas, changes


def test_each_dimension_tool_draws_its_kind_in_one_step():
    _qt()
    import plan_canvas_tools as tools
    source = _plan()
    canvas, changes = _canvas_for(source)
    canvas.set_tool("dimension-parallel")
    for p in ((100, 100), (400, 100), (250, 60)):
        tools.dimension_click(canvas, p, False)
    dim = source["dimensions"][0]
    assert (dim["kind"], dim["points"], abs(dim["offset"])) == ("parallel", [[100, 100], [400, 100]], 40.0), dim
    assert len(changes) == 1 and canvas.selection == ("dimension", 0)
    assert [p["value"] for p in plan.dimension_parts(source, source["dimensions"][0])] == [3.0]
    # a chain: its points, Enter, then where its line goes
    canvas.set_tool("dimension-chain")
    for p in ((100, 300), (200, 300), (450, 300)):
        tools.dimension_click(canvas, p, False)
    assert tools.finish_chain(canvas)
    tools.dimension_click(canvas, (300, 350), False)
    chain = source["dimensions"][1]
    assert chain["kind"] == "chain" and chain["axis"] == "horizontal" and len(chain["points"]) == 3 and len(changes) == 2
    assert [p["value"] for p in plan.dimension_parts(source, chain)] == [1.0, 2.5]
    # an angle: its corner and a point on each side
    canvas.set_tool("dimension-angle")
    for p in ((600, 400), (700, 400), (600, 300)):
        tools.dimension_click(canvas, p, False)
    assert source["dimensions"][2]["kind"] == "angle" and len(changes) == 3
    assert [p["value"] for p in plan.dimension_parts(source, source["dimensions"][2])] == [90.0]
    plan.check_source(source, "P01.json")
    # Escape gives up the one being drawn; nothing written
    canvas.set_tool("dimension-horizontal")
    tools.dimension_click(canvas, (50, 50), False)
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    QTest.keyClick(canvas, Qt.Key.Key_Escape)
    assert canvas.dim_points == [] and len(source["dimensions"]) == 3 and len(changes) == 3


def test_a_dimension_is_taken_by_its_line_moved_and_deleted():
    _qt()
    import plan_canvas_tools as tools
    source = _plan()
    source["dimensions"] = [{"kind": "horizontal", "points": [[100, 100], [400, 100]], "offset": 50}]
    canvas, changes = _canvas_for(source)
    canvas.set_tool("select")
    (p, q), = [part["line"] for part in plan.dimension_parts(source, source["dimensions"][0])]
    on_line = ((p[0] + q[0]) / 2, p[1])
    assert tools.hit_dimension(canvas, on_line, canvas.tolerance()) == 0
    canvas.press_select(on_line)
    assert canvas.selection == ("dimension", 0) and canvas.drag["kind"] == "dimension"
    tools.move_dimension(canvas, canvas.drag, (on_line[0], on_line[1] + 30))
    assert source["dimensions"][0]["offset"] == 80 and len(changes) == 1
    canvas.end_change()
    canvas.drag = None
    canvas.delete_selection()
    assert source["dimensions"] == [] and len(changes) == 2


def test_a_dimension_tool_shows_the_same_symbol_in_the_three_tabs():
    _qt()
    import dimension_icons
    import schema_tab
    import statics_tab

    def pixels(icon):
        image = icon.pixmap(24, 24).toImage()
        return bytes(image.constBits())[: image.sizeInBytes()]
    for tool in ("dimension-horizontal", "dimension-vertical", "dimension-parallel", "dimension-angle"):
        assert pixels(schema_tab.tool_icon(tool, 24)) == pixels(statics_tab.svg_icon(tool, 24)) == pixels(dimension_icons.icon(tool, 24)), tool
    assert not dimension_icons.icon("dimension-chain", 24).isNull()


def test_the_view_dessin_shows_the_dimensions_or_not_and_writes_nothing():
    """REQ-011: in «Dessin» the dimensions are the engineer's setting -- drawn or not, the plan unchanged --, shown all the same while a dimension tool is chosen."""
    _qt()
    import copy
    source = _plan()
    source["dimensions"] = [{"kind": "horizontal", "points": [[100, 100], [400, 100]], "offset": 50}]
    kept = copy.deepcopy(source)
    canvas, changes = _canvas_for(source)
    assert canvas.drawn_source()["dimensions"] == source["dimensions"]
    canvas.show_dimensions = False
    assert canvas.drawn_source()["dimensions"] == [] and source == kept and not changes, "hidden in the view, kept in the plan"
    canvas.set_tool("dimension-parallel")
    assert canvas.drawn_source()["dimensions"] == source["dimensions"], "shown while one is being drawn"
