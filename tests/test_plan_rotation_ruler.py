"""A column turned by the circle its selection shows, and the ruler (calc/tools/plan_canvas_tools.py; issue #9, REQ-002, REQ-009, D-005, D-012).

The engineer, 08.10.2026: «Permettre de tourner les poteaux avec le cercle qui apparaît à la sélection, et non plus seulement par l'angle saisi en texte» -- «Ajouter un outil règle».

What is held: a selected column shows a circle, which stands at a distance on the screen whatever the zoom; dragging it turns the column -- clockwise on the drawing, 0° above it, Shift by steps of 15° --, in one step of «Annuler» and only where the angle changed, the angle field told as it goes; an Auflager drawn with two points shows none. The ruler shows the distance between two clicks, in metres on a plan with a scale and in the sheet's units on one without, and writes nothing -- no change, no history; Escape takes it away, on the position plan and on the fire-protection plan alike.
"""

TIER = "fast"  # tests/run_tests.py --fast

import copy
import math

from test_plan_canvas_rework import _canvas, _click, _drag, _qt, _source

from domains import plan
from domains import plan_svg


def _column(angle=None):
    source = _source()
    source["scale"] = {"mode": "calibration", "points": [[0, 0], [100, 0]], "length_m": 1.0}
    column = {"type": "S", "label": "S101", "points": [[500, 250]]}
    if angle is not None:
        column["angle"] = angle
    source["elements"] = [column, {"type": "M", "subtype": "vert", "label": "M101", "points": [[100, 100], [300, 100]]}]
    return source


def test_a_selected_column_shows_a_circle_and_dragging_it_turns_the_column_in_one_step():
    _qt()
    import plan_canvas_tools as tools
    source = _column()
    canvas = _canvas(source, None)
    changes, angles = [], []
    canvas.about_to_change.connect(lambda: changes.append(True))
    canvas.angle_dragged.connect(angles.append)
    canvas.select(("element", 0))
    at = tools.rotation_point(canvas, source["elements"][0])
    assert at is not None and at[0] == 500 and at[1] < 250, "above the column at 0°"
    # the circle stands at a distance on the screen, whatever the zoom
    before = canvas.mapFromScene(*at) - canvas.mapFromScene(500, 250)
    canvas.zoom_at(canvas.mapFromScene(500, 250).toPointF(), 2.0)
    after_at = tools.rotation_point(canvas, source["elements"][0])
    after = canvas.mapFromScene(*after_at) - canvas.mapFromScene(500, 250)
    ring = 18 * canvas.transform().m11() * plan_svg.base_unit(plan.crop_of(source))
    assert abs((abs(after.y()) - ring) - tools.ROTATE_PX) < 2, (before, after, ring)
    # a click on the circle alone changes nothing
    _click(canvas, after_at)
    assert not changes and "angle" not in source["elements"][0]
    # dragged to the right of the column: a quarter turn clockwise, one step of «Annuler», the field told
    centre = source["elements"][0]["points"][0]
    _drag(canvas, after_at, (centre[0] + 60, centre[1]))
    turned = source["elements"][0]["angle"]
    assert abs(turned - 90) < 1 and len(changes) == 1 and angles and angles[-1] == turned, (turned, changes, angles)   # the pointer moves by whole pixels
    plan.check_source(source, "P01.json")
    # the angle an element turned by the pointer gives: Shift by steps of 15°
    assert tools.angle_at((0, 0), (10, -10), False) == 45 and tools.angle_at((0, 0), (10, -9), True) == 45
    assert tools.angle_at((0, 0), (0, 10), False) == 180 and tools.angle_at((0, 0), (-10, 0), False) == -90
    # an Auflager drawn with two points has no circle
    canvas.select(("element", 1))
    assert tools.rotation_point(canvas, source["elements"][1]) is None


def test_the_ruler_shows_a_distance_and_writes_nothing():
    _qt()
    import plan_canvas_tools as tools
    source = _column()
    kept = copy.deepcopy(source)
    canvas = _canvas(source, None)
    changes = []
    canvas.about_to_change.connect(lambda: changes.append(True))
    canvas.set_tool(tools.RULER)
    canvas.snap_axes = canvas.snap_elements = False
    _click(canvas, (100, 400))
    _click(canvas, (400, 400))
    a, b = canvas.ruler
    assert canvas.ruler_shown == plan.metres_text(plan.distance_m(a, b, plan.units_per_m(source))), canvas.ruler_shown
    assert abs(math.dist(a, b) - 300) < 15 and canvas.ruler_shown.endswith(" m")
    assert source == kept and not changes, "the ruler writes nothing and is no step of «Annuler»"
    # without a scale: the sheet's units, named as such
    canvas.unit_word = lambda: "pt"
    del source["scale"]
    assert tools.ruler_text(canvas, (0, 0), (30, 40)) == "50.0 pt"
    # Escape takes the measure away and keeps the tool
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    QTest.keyClick(canvas, Qt.Key.Key_Escape)
    assert canvas.ruler == [] and canvas.ruler_items == [] and canvas.tool == tools.RULER


def test_the_fire_plan_has_the_ruler_too():
    _qt()
    import fire_canvas
    import fire_tab
    import plan_canvas_tools as tools
    assert "ruler" in fire_tab.TOOLS and fire_tab.NAMES["ruler"] == "plan_tool_ruler"
    canvas = fire_canvas.FireCanvas()
    canvas.resize(900, 600)
    canvas.show()
    source = {"schema_version": "1.0", "id": "F01", "zones": [], "walls": [], "doors": [], "routes": [], "exits": [], "widths": [], "texts": [], "plan": "P01"}   # following a position plan: its scale is the ruler's
    frame = _column()
    canvas.set_plan(source, frame, None)
    kept, kept_frame = copy.deepcopy(source), copy.deepcopy(frame)
    changes = []
    canvas.about_to_change.connect(lambda: changes.append(True))
    canvas.set_tool(tools.RULER)
    tools.ruler_click(canvas, (100, 100), False)
    tools.ruler_click(canvas, (100, 300), False)
    assert len(canvas.ruler) == 2 and canvas.ruler_shown == plan.metres_text(plan.distance_m((100, 100), (100, 300), plan.units_per_m(frame))), canvas.ruler_shown
    assert source == kept and frame == kept_frame and not changes, "the ruler writes nothing on the fire plan either and is no step of «Annuler»"
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    QTest.keyClick(canvas, Qt.Key.Key_Escape)
    assert canvas.ruler == [] and canvas.ruler_items == [] and canvas.tool == tools.RULER
