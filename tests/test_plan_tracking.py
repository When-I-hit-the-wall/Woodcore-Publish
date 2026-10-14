"""The tracking of the plan canvases (v0.116, calc/domains/plan_tracking.py, calc/tools/plan_canvas.py, calc/tools/fire_canvas.py; docs/domain/position-plans.md §3.3sexies, docs/ui/window.md §10quater): as in the static models' tab, resting the pointer on a point of the plan acquires it, the cursor then locks to the eight polar rays through the acquired points and to where they cross, Tab takes a distance along the ray, and a section's storey lines and boxes offer their ends and corners as snap points.

The arithmetic is checked first, on plain tuples in the sheet's frame -- x to the right, y DOWN, so the ray at 90 degrees points down the page --, and then the canvases, off-screen, with a source dictionary of their own: nothing here needs a window or the example project.
"""

import math
import os
import sys

import conftest
from conftest import ROOT
from domains import fire, plan
from domains import plan_tracking as tracking

TOOLS = ROOT / "calc" / "tools"


def _qt():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _index(source=None, **kwargs):
    source = source or plan.new_source("P01")
    return tracking.PlanSnapIndex(source, plan.crop_of(source), **kwargs)


def _near(a, b, eps=1e-6):
    return math.dist(a, b) <= eps


# --- the rays -----------------------------------------------------------------------------------


def test_the_eight_rays_run_from_the_anchor_and_ninety_degrees_points_down_the_page():
    rays = tracking.polar_rays((100, 100))
    assert [r["angle"] for r in rays] == [0, 45, 90, 135, 180, 225, 270, 315]
    by_angle = {r["angle"]: r["unit"] for r in rays}
    assert _near(by_angle[0], (1, 0)) and _near(by_angle[90], (0, 1)) and _near(by_angle[270], (0, -1))
    assert _near(by_angle[45], (math.sqrt(0.5), math.sqrt(0.5))), "y grows down the page: 45 degrees is down and to the right"
    assert all(r["anchor"] == (100.0, 100.0) for r in rays)


def test_the_pointer_locks_to_the_ray_it_is_near_in_the_right_sense_at_the_right_angle():
    anchor, tol = (100, 100), 5
    for point, angle in (((300, 103), 0), ((103, 300), 90), ((297, 303), 45), ((-100, 297), 135), ((-98, 100), 180), ((100, -97), 270), ((-100, -101), 225), ((300, -98), 315)):
        locked = tracking.locked_rays([anchor], point, tol)
        assert locked and locked[0][1]["angle"] == angle, (point, angle, locked)
    # a pointer far from every ray, and one on the anchor itself, lock nothing
    assert tracking.locked_rays([anchor], (300, 150), tol) == []
    assert tracking.locked_rays([anchor], (101, 100), tol) == []
    # the half-line: behind the anchor is the opposite ray
    assert [r["angle"] for _d, r in tracking.locked_rays([anchor], (50, 101), tol)] == [180]


def test_a_locked_pointer_is_projected_onto_its_ray_exactly():
    result = tracking.track(_index(), [(100, 100)], (300, 103), 5)
    assert result["kind"] == "track" and _near(result["point"], (300, 100)) and [r["angle"] for r in result["rays"]] == [0]
    result = tracking.track(_index(), [(100, 100)], (297, 303), 5)
    assert result["kind"] == "track" and _near(result["point"], (300, 300), 1e-6), "the 45 degree ray, down and to the right"
    free = tracking.track(_index(), [(100, 100)], (300, 150), 5)
    assert free["kind"] is None and free["rays"] == [] and free["point"] == (300, 150)


def test_where_two_rays_of_two_acquired_points_cross_the_cursor_takes_the_crossing():
    result = tracking.track(_index(), [(100, 100), (300, 300)], (302, 102), 5)
    assert result["kind"] == "track-crossing" and _near(result["point"], (300, 100)) and len(result["rays"]) == 2
    assert {r["angle"] for r in result["rays"]} == {0, 270}, "the 0 ray of the first, the 270 (up the page) of the second"
    # two diagonals: (0,0) at 45 degrees and (200,0) at 135 degrees meet at (100,100)
    result = tracking.track(_index(), [(0, 0), (200, 0)], (101, 99), 5)
    assert result["kind"] == "track-crossing" and _near(result["point"], (100, 100), 1e-6)
    # the crossing lies on the half-lines or it is none: (100,100)'s 180 ray and (300,300)'s 90 ray meet at (300,100)?? no -- behind both
    assert tracking.track(_index(), [(100, 100), (300, 300)], (100, 300 - 1000), 5)["kind"] != "track-crossing"
    # three acquired points: the crossing of the nearest pair of rays wins
    result = tracking.track(_index(), [(0, 400), (100, 100), (300, 300)], (302, 102), 5)
    assert result["kind"] == "track-crossing" and _near(result["point"], (300, 100))


def test_a_point_of_the_plan_beats_every_ray_and_a_ray_crossing_a_wall_takes_the_crossing():
    source = plan.new_source("P01")
    source["elements"] = [{"type": "V", "label": "V001", "points": [[200, 0], [200, 400]]}]
    index = _index(source)
    # the wall's end is a point: the pointer within reach of it lands on it, ray or no ray
    result = tracking.track(index, [(100, 400)], (203, 397), 5)
    assert result["kind"] == "vertex" and result["point"] == (200.0, 400.0) and result["rays"] == []
    # the ray from (100,100) at 0 degrees meets the wall at (200,100): near it the cursor lands exactly there
    result = tracking.track(index, [(100, 100)], (203, 101), 5)
    assert result["kind"] == "track-line" and _near(result["point"], (200, 100), 1e-6) and [r["angle"] for r in result["rays"]] == [0]
    # on a wall that no ray crosses there, the wall holds the pointer
    result = tracking.track(index, [(100, 100)], (201, 250), 5)
    assert result["kind"] == "on-line" and _near(result["point"], (200, 250)) and result["rays"] == []
    # and a point of the plan on the ray, a little further than the pointer, is taken
    source["elements"].append({"type": "S", "label": "S001", "points": [[300, 100]]})
    result = tracking.track(_index(source), [(100, 102)], (292, 101), 5)
    assert result["kind"] == "vertex" and result["point"] == (300.0, 100.0)


def test_a_distance_typed_goes_along_the_ray_in_metres_where_the_plan_has_a_scale():
    ray = tracking.polar_rays((100, 100))[0]
    assert _near(tracking.typed_point(ray, "50", None), (150, 100))
    assert _near(tracking.typed_point(ray, "2,5", 40), (200, 100)), "a comma is a decimal point, and metres are scaled to sheet units"
    down = tracking.polar_rays((100, 100))[2]
    assert _near(tracking.typed_point(down, "1", 100), (100, 200)), "90 degrees is down the page"
    assert _near(tracking.typed_point(down, "-1", 100), (100, 0))
    assert tracking.typed_point(ray, "abc") is None and tracking.typed_point(ray, "") is None and tracking.typed_point(ray, "inf") is None
    assert tracking.distance_text(ray, (200, 100), 40) == "2.5" and tracking.distance_text(ray, (150, 100)) == "50"


def test_acquired_points_are_kept_newest_first_up_to_three_and_none_twice():
    kept = []
    for p in ((1, 1), (2, 2), (3, 3)):
        kept = tracking.acquire(kept, p)
    assert kept == [(3.0, 3.0), (2.0, 2.0), (1.0, 1.0)]
    kept = tracking.acquire(kept, (4, 4))
    assert kept == [(4.0, 4.0), (3.0, 3.0), (2.0, 2.0)], "the oldest goes"
    kept = tracking.acquire(kept, (2, 2))
    assert kept == [(2.0, 2.0), (4.0, 4.0), (3.0, 3.0)], "a point acquired again moves to the front"


# --- a section's storeys --------------------------------------------------------------------------


def test_the_ends_of_a_storey_line_and_the_four_corners_of_a_storey_box_are_snap_points():
    source = plan.new_source("P01")
    source["storey_lines"] = [{"storey": "EG", "points": [[100, 200], [600, 200]]}]
    source["storey_boxes"] = [{"storey": "1.OG", "x": 100, "y": 300, "w": 500, "h": 100}]
    index = _index(source)
    for corner in ((100, 200), (600, 200), (100, 300), (600, 300), (600, 400), (100, 400)):
        point, kind = index.snap((corner[0] + 3, corner[1] - 2), 6)
        assert kind == "vertex" and point == (float(corner[0]), float(corner[1])), corner
    # the middles of their edges, too, and where the edge of a box crosses the line of another
    assert index.snap((352, 301), 6) == ((350.0, 300.0), "midpoint")
    assert index.snap((350, 252), 6)[1] != "vertex"
    # what is being dragged does not snap to itself
    without = _index(source, exclude_storey=("storey-line", 0))
    assert without.snap((103, 198), 6)[1] != "vertex"
    without = _index(source, exclude_storey=("storey-box", 0))
    assert without.snap((103, 298), 6)[1] != "vertex" and without.snap((103, 198), 6)[1] == "vertex"
    # storeys follow the `elements` button, as walls do
    assert _index(source, elements=False).snap((103, 198), 6)[1] is None
    # a storey line crossing the edge of a box is a crossing
    source["storey_lines"].append({"storey": "UG", "points": [[350, 250], [350, 450]]})
    index = _index(source)
    assert index.snap((351, 301), 6) == ((350.0, 300.0), "crossing") or index.snap((351, 301), 6)[1] in ("crossing", "midpoint")


def test_tracking_applies_to_storey_corners_too():
    source = plan.new_source("P01")
    source["storey_boxes"] = [{"storey": "EG", "x": 100, "y": 100, "w": 400, "h": 300}]
    index = _index(source)
    # a corner of the box is an anchor: the ray along its top edge continues past the corner
    result = tracking.track(index, [(500, 100)], (700, 103), 5)
    assert result["kind"] == "track" and _near(result["point"], (700, 100)) and result["rays"][0]["angle"] == 0
    # a point level with the box's bottom, straight down from the right corner, crosses the ray of the bottom-left: the corners align a second box
    result = tracking.track(index, [(500, 100), (100, 400)], (502, 402), 5)
    assert result["kind"] == "track-crossing" or result["kind"] == "vertex", result
    assert _near(result["point"], (500, 400), 1e-6)


# --- the canvas, off-screen -------------------------------------------------------------------------


def _canvas(source, name, fire_canvas=False):
    _qt()
    root = conftest.tmpdir(name)
    if fire_canvas:
        import fire_canvas as module
        canvas = module.FireCanvas()
    else:
        import plan_canvas as module
        canvas = module.PlanCanvas()
    canvas.resize(900, 600)
    canvas.show()
    canvas.set_source(source, root)
    return canvas


def _source(**extra):
    source = plan.new_source("P01")
    source["sheet"] = {"width": 1000, "height": 500}
    source.update(extra)
    return source


def _move(canvas, point, shift=False):
    """The pointer at `point` (scene coordinates), no button down, as Qt sends it."""
    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    pos = QPointF(canvas.mapFromScene(QPointF(*point)))
    modifiers = Qt.KeyboardModifier.ShiftModifier if shift else Qt.KeyboardModifier.NoModifier
    canvas.mouseMoveEvent(QMouseEvent(QEvent.Type.MouseMove, pos, canvas.viewport().mapToGlobal(pos), Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, modifiers))


def _click(canvas, point, shift=False):
    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    pos = QPointF(canvas.mapFromScene(QPointF(*point)))
    modifiers = Qt.KeyboardModifier.ShiftModifier if shift else Qt.KeyboardModifier.NoModifier
    _move(canvas, point, shift)
    canvas.mousePressEvent(QMouseEvent(QEvent.Type.MouseButtonPress, pos, canvas.viewport().mapToGlobal(pos), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, modifiers))
    canvas.mouseReleaseEvent(QMouseEvent(QEvent.Type.MouseButtonRelease, pos, canvas.viewport().mapToGlobal(pos), Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton, modifiers))


def _is(point, expected, eps=1.5):
    """The cursor is where it should be, give or take a pixel: it was mapped through the view, which rounds to whole pixels -- a coordinate a tracking ray fixes is exact all the same, and the checks say so."""
    return point is not None and math.dist(point, expected) <= eps


def _key(canvas, key):
    from PySide6.QtTest import QTest
    QTest.keyClick(canvas, key)


def test_resting_on_a_point_acquires_it_after_the_dwell_and_escape_lets_go_of_it():
    from PySide6.QtCore import Qt
    source = _source(elements=[{"type": "S", "label": "S001", "points": [[200, 150]]}, {"type": "S", "label": "S002", "points": [[600, 300]]}])
    canvas = _canvas(source, "tracking_acquire")
    canvas.propose_label = lambda t: "T001"
    canvas.set_tool("T")
    _move(canvas, (202, 151))
    assert canvas._hover == (200.0, 150.0) and canvas.acquire_timer.isActive() and canvas.acquired == [], "resting starts the dwell and acquires nothing yet"
    # the pointer leaving the point stops the dwell
    _move(canvas, (400, 250))
    assert canvas._hover is None and not canvas.acquire_timer.isActive()
    # the dwell over (the timer's own slot, called: no waiting on a clock): the point is acquired
    _move(canvas, (202, 151))
    canvas.acquire()
    assert canvas.acquired == [(200.0, 150.0)] and canvas._hover is None
    # resting on an acquired point again acquires nothing twice; a second point goes first
    _move(canvas, (201, 150))
    assert canvas._hover is None
    _move(canvas, (601, 301))
    canvas.acquire()
    assert canvas.acquired == [(600.0, 300.0), (200.0, 150.0)]
    # the timer is wired to acquire(), with the dwell that was chosen
    import plan_canvas
    assert canvas.acquire_timer.interval() == plan_canvas.ACQUIRE_MS and 250 <= plan_canvas.ACQUIRE_MS <= 500
    # Escape lets go of what was acquired, then leaves the tool
    done = []
    canvas.tool_done.connect(lambda: done.append(1))
    _key(canvas, Qt.Key.Key_Escape)
    assert canvas.acquired == [] and not done
    _key(canvas, Qt.Key.Key_Escape)
    assert done == [1]
    canvas.close()


def test_the_cursor_follows_the_ray_of_an_acquired_point_and_where_two_cross_and_shift_still_keeps_h_v_45():
    source = _source(elements=[{"type": "S", "label": "S001", "points": [[200, 150]]}, {"type": "S", "label": "S002", "points": [[600, 300]]}])
    canvas = _canvas(source, "tracking_cursor")
    canvas.propose_label = lambda t: "T001"
    canvas.set_tool("T")
    canvas.acquired = [(200.0, 150.0)]
    _move(canvas, (400, 153))
    assert _is(canvas.cursor, (400, 150)) and canvas.cursor[1] == 150.0 and canvas.locked and canvas.locked[0]["angle"] == 0
    assert not canvas.track_item.path().isEmpty(), "the dotted line is drawn across the view"
    _move(canvas, (400, 220))
    assert canvas.locked == [] and abs(canvas.cursor[1] - 220) < 1.5
    canvas.acquired = [(600.0, 300.0), (200.0, 150.0)]
    _move(canvas, (601, 152))
    assert len(canvas.locked) == 2 and canvas.cursor[0] == 600.0 and canvas.cursor[1] == 150.0, "the crossing of the two rays"
    # a click lands on what the cursor shows
    _click(canvas, (601, 152))
    assert canvas.drawing == [(600.0, 150.0)]
    # Shift is what it was: the eight directions from the last point, and no tracking
    _move(canvas, (700, 190), shift=True)
    assert canvas.locked == []
    ax, ay = canvas.drawing[-1]
    cx, cy = canvas.cursor
    angle = math.degrees(math.atan2(cy - ay, cx - ax)) % 45
    assert min(angle, 45 - angle) < 1e-6, "Shift: on one of the eight directions"
    canvas.close()


def test_tab_takes_a_distance_along_the_locked_ray_and_enter_puts_the_point_down():
    from PySide6.QtCore import Qt
    source = _source()
    canvas = _canvas(source, "tracking_typed")
    canvas.set_tool("axis-o")   # two clicks: a point of the axis, then its direction
    canvas.acquired = [(100.0, 100.0)]
    _move(canvas, (300, 102))
    assert len(canvas.locked) == 1 and _is(canvas.cursor, (300, 100)) and canvas.cursor[1] == 100.0
    _key(canvas, Qt.Key.Key_Tab)
    assert canvas.typing and abs(float(canvas.distance.text()) - 200) < 1.5, "the field starts with the distance so far"
    canvas.distance.setText("50")
    canvas.on_typed("50")
    assert canvas.cursor == (150.0, 100.0), "the cursor follows the number as it is typed"
    canvas.commit_typed()
    assert not canvas.typing and canvas.drawing == [(150.0, 100.0)], "the first point of the axis is at the typed distance"
    # while a distance is typed the pointer's movements are let go
    canvas.acquired = [(150.0, 100.0)]
    _move(canvas, (600, 103))
    _key(canvas, Qt.Key.Key_Tab)
    assert canvas.typing
    before = canvas.cursor
    _move(canvas, (50, 400))
    assert canvas.cursor == before
    _key(canvas, Qt.Key.Key_Escape)
    assert not canvas.typing and canvas.acquired, "Escape ends the typing and nothing else"
    # in metres where the plan has a scale
    source["scale"] = {"mode": "ratio", "ratio": 100}
    per_m = plan.units_per_m(source)
    _move(canvas, (600, 103))
    _key(canvas, Qt.Key.Key_Tab)
    canvas.distance.setText("1")
    canvas.on_typed("1")
    assert abs(canvas.cursor[0] - (150.0 + per_m)) < 1e-6
    canvas.hide_distance()
    canvas.close()


def test_a_storey_line_snaps_to_the_corner_of_a_storey_box_and_to_the_end_of_another_line():
    source = _source(role="section", storey_boxes=[{"storey": "EG", "x": 200, "y": 150, "w": 300, "h": 100}], storey_lines=[{"storey": "UG", "points": [[200, 300], [500, 300]]}])
    canvas = _canvas(source, "tracking_storey")
    canvas.set_storey_choice("1.OG")
    canvas.set_tool("storey-line")
    _click(canvas, (203, 148))
    assert canvas.drawing == [(200.0, 150.0)], "the first end lands on the box's corner"
    _click(canvas, (497, 152))
    line = source["storey_lines"][-1]
    assert line["points"] == [[200, 150], [500, 150]], line
    # one above another: the next line starts exactly at the end of the first
    canvas.set_tool("storey-line")
    canvas.set_storey_choice("2.OG")
    _click(canvas, (498, 301))
    assert canvas.drawing == [(500.0, 300.0)]
    canvas.drawing = []
    # a box's corners are placed on the corners of another
    canvas.set_tool("storey-box")
    _click(canvas, (503, 253))
    _click(canvas, (698, 398))
    box = source["storey_boxes"][-1]
    assert (box["x"], box["y"]) == (500, 250), box
    # dragging a corner of the selected box does not stick to the corner it holds
    canvas.set_tool("select")
    canvas.select(("storey-box", len(source["storey_boxes"]) - 1))
    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QMouseEvent

    def event(kind, scene, buttons, button=Qt.MouseButton.LeftButton):
        pos = QPointF(canvas.mapFromScene(QPointF(*scene)))
        return QMouseEvent(kind, pos, canvas.viewport().mapToGlobal(pos), button, buttons, Qt.KeyboardModifier.NoModifier)

    canvas.mousePressEvent(event(QEvent.Type.MouseButtonPress, (700, 400), Qt.MouseButton.LeftButton))
    assert canvas.drag and canvas.drag["kind"] == "storey-box-corner"
    canvas.mouseMoveEvent(event(QEvent.Type.MouseMove, (740, 430), Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton))
    canvas.mouseReleaseEvent(event(QEvent.Type.MouseButtonRelease, (740, 430), Qt.MouseButton.NoButton))
    box = source["storey_boxes"][-1]
    assert abs(box["w"] + box["x"] - 740) < 2 and abs(box["h"] + box["y"] - 430) < 2, "free to move away from its own corner"
    plan.check_source(source, "P01.json")
    canvas.close()


def test_the_snapping_buttons_still_decide_and_tracking_stays_out_of_the_way_when_both_are_off():
    source = _source(elements=[{"type": "S", "label": "S001", "points": [[200, 150]]}])
    canvas = _canvas(source, "tracking_buttons")
    canvas.propose_label = lambda t: "T001"
    canvas.set_tool("T")
    canvas.snap_axes = canvas.snap_elements = False
    canvas.acquired = [(200.0, 150.0)]
    _move(canvas, (400, 153))
    assert _is(canvas.cursor, (400, 153)) and abs(canvas.cursor[1] - 153) < 1.5 and canvas.cursor[1] != 150.0 and canvas.locked == [], "snapping off: the pointer is where it is"
    canvas.snap_elements = True
    canvas._snap_index = None
    _move(canvas, (202, 152))
    assert canvas.cursor == (200.0, 150.0)
    canvas.close()


def test_the_fire_protection_canvas_tracks_the_same_way_over_the_points_it_carries():
    from PySide6.QtCore import Qt
    source = fire.new_source("F1")
    source["sheet"] = {"width": 1000, "height": 500}
    source["walls"] = [{"id": "W1", "class": "EI 30", "points": [[200, 150], [500, 150]]}]
    canvas = _canvas(source, "tracking_fire", fire_canvas=True)
    canvas.set_tool("wall")
    # the corner of a wall is a snap point, and resting on it acquires it
    _move(canvas, (203, 152))
    assert canvas.cursor == (200.0, 150.0) and canvas._hover == (200.0, 150.0)
    canvas.acquire()
    assert canvas.acquired == [(200.0, 150.0)]
    # the cursor follows the ray, down the page at 90 degrees
    _move(canvas, (202, 400))
    assert _is(canvas.cursor, (200, 400)) and canvas.cursor[0] == 200.0 and canvas.locked and canvas.locked[0]["angle"] == 90
    # Tab, a distance, Enter: the first point of a wall at 120 units under the corner
    _key(canvas, Qt.Key.Key_Tab)
    assert canvas.typing
    canvas.distance.setText("120")
    canvas.on_typed("120")
    canvas.commit_typed()
    assert canvas.drawing == [(200.0, 270.0)], canvas.drawing
    # the wall's other end is level with the first corner of the first wall's, found by the ray of the typed point and the acquired corner's
    _move(canvas, (503, 272))
    assert canvas.cursor[1] == 270.0, "level with the point just put down"
    _key(canvas, Qt.Key.Key_Escape)
    assert canvas.drawing == [] and canvas.acquired, "Escape gives the wall up first"
    _key(canvas, Qt.Key.Key_Escape)
    assert canvas.acquired == []
    # a right click lets go of what was acquired as well
    canvas.acquired = [(200.0, 150.0)]
    from PySide6.QtCore import QEvent, QPointF
    from PySide6.QtGui import QMouseEvent
    pos = QPointF(canvas.mapFromScene(QPointF(300, 300)))
    canvas.mousePressEvent(QMouseEvent(QEvent.Type.MouseButtonPress, pos, canvas.viewport().mapToGlobal(pos), Qt.MouseButton.RightButton, Qt.MouseButton.RightButton, Qt.KeyboardModifier.NoModifier))
    assert canvas.acquired == []
    canvas.close()


def test_a_point_dragged_in_the_fire_canvas_does_not_stick_to_itself_and_snaps_to_the_others():
    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    source = fire.new_source("F1")
    source["sheet"] = {"width": 1000, "height": 500}
    source["walls"] = [{"id": "W1", "class": "EI 30", "points": [[200, 150], [500, 150]]}, {"id": "W2", "class": "EI 30", "points": [[200, 300], [500, 300]]}]
    canvas = _canvas(source, "tracking_fire_drag", fire_canvas=True)
    canvas.set_tool("select")
    canvas.select_ids(["W1"])

    def event(kind, scene, buttons, button=Qt.MouseButton.LeftButton):
        pos = QPointF(canvas.mapFromScene(QPointF(*scene)))
        return QMouseEvent(kind, pos, canvas.viewport().mapToGlobal(pos), button, buttons, Qt.KeyboardModifier.NoModifier)

    canvas.mousePressEvent(event(QEvent.Type.MouseButtonPress, (500, 150), Qt.MouseButton.LeftButton))
    assert canvas.drag and canvas.drag["kind"] == "vertex"
    canvas.mouseMoveEvent(event(QEvent.Type.MouseMove, (503, 152), Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton))
    assert source["walls"][0]["points"][1] == [503, 152] or abs(source["walls"][0]["points"][1][0] - 503) < 4, "free to leave where it was"
    canvas.mouseMoveEvent(event(QEvent.Type.MouseMove, (498, 298), Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton))
    assert source["walls"][0]["points"][1] == [500, 300], "onto the end of the other wall"
    canvas.mouseReleaseEvent(event(QEvent.Type.MouseButtonRelease, (498, 298), Qt.MouseButton.NoButton))
    canvas.close()
