"""The drawing tabs' editing tools (issue #18, calc/tools/plan_canvas_edit.py, calc/domains/plan.py, calc/domains/lines.py, docs/ui/window.md §10quater, docs/domain/position-plans.md §3.3sexies): «Déplacer» and «Copier» an object of the plan, the construction aids, and «Dupliquer» and «Supprimer» under «Objet sélectionné».

What is held: a translation moves every kind of object the same way, the domain's (`translate_entry`, which the drags use too); a copy keeps its position number and a copied axis is named among the others; «Copier» puts down a copy at every click until Escape, each one step of «Annuler»; an aid is stored resolved (`{kind, point, angle}`), saved in source 1.6 -- a 1.5 file read as it is --, snapped to as an axis is, turned with its page, and never drawn by the report; the fire-protection plan has the moves and the copies and no aid (D-015).

⚠️ The canvas tests are skipped where PySide6 is not installed; the domain's are not.
"""

import copy
import json
import math
import os
import sys
import tempfile
from pathlib import Path

import conftest
from conftest import ROOT
from domains import lines
from domains import plan
from domains import plan_svg

TOOLS = ROOT / "calc" / "tools"


def _source():
    source = plan.new_source("P01")
    source["sheet"] = {"width": 1000, "height": 500}
    source["role"] = "section"   # storey lines and storey boxes are a section's alone (plan.check_source)
    source["scale"] = {"mode": "calibration", "points": [[0, 0], [100, 0]], "length_m": 1.0}
    source["elements"] = [{"type": "T", "label": "T101", "points": [[100, 100], [500, 100]]},
                          {"type": "D", "subtype": "normal", "label": "D101", "points": [[100, 200], [300, 200], [300, 400], [100, 400]]}]
    source["axes"] = [{"label": "A", "point": [100, 0], "angle": 90, "bubbles": "both"}, {"label": "B", "point": [500, 0], "angle": 90, "bubbles": "both"}]
    source["storey_lines"] = [{"storey": "1", "points": [[0, 450], [900, 450]]}]
    source["storey_boxes"] = [{"storey": "1", "x": 10, "y": 10, "w": 50, "h": 40}]
    source["dimensions"] = [{"kind": "horizontal", "points": [[100, 100], [500, 100]], "offset": -20}]
    source["aids"] = [plan.new_aid("horizontal", (0, 300), 0)]
    return source


# --- the domain ----------------------------------------------------------------------------

def test_every_kind_of_object_moves_by_the_same_translation():
    source = _source()
    expected = {"element": lambda e: e["points"], "axis": lambda e: [e["point"]], "storey-line": lambda e: e["points"],
                "storey-box": lambda e: [[e["x"], e["y"]]], "dimension": lambda e: e["points"], "aid": lambda e: [e["point"]]}
    for kind, points_of in expected.items():
        entry = source[plan.ENTRY_LISTS[kind]][0]
        before = copy.deepcopy(points_of(entry))
        plan.translate_entry(source, kind, 0, 12.5, -7.25)
        after = points_of(source[plan.ENTRY_LISTS[kind]][0])
        assert after == [[round(x + 12.5, 2), round(y - 7.25, 2)] for x, y in before], (kind, before, after)
    assert source["dimensions"][0]["offset"] == -20, "what is measured from the object itself moves with it unchanged"


def test_a_copy_keeps_its_position_and_a_copied_axis_is_named_among_the_others():
    source = _source()
    index, renames = plan.copy_entry(source, "element", 0, 0, 50, plan.crop_of(source))
    assert index == 2 and source["elements"][2]["label"] == "T101" and source["elements"][2]["points"] == [[100, 150], [500, 150]]
    assert source["elements"][0]["points"] == [[100, 100], [500, 100]], "the original stays"
    index, renames = plan.copy_entry(source, "axis", 0, 200, 0, plan.crop_of(source))
    assert source["axes"][index]["point"] == [300, 0] and len(source["axes"]) == 3
    assert sorted(a["label"] for a in source["axes"]) == ["A", "B", "C"], "named where it lies, between A and the old B"


def test_an_aid_is_made_horizontal_vertical_through_two_points_or_parallel_at_a_distance():
    assert plan.new_aid("vertical", (5, 5), 90)["angle"] == 90
    point, angle = lines.through((0, 0), (10, 10))
    assert plan.new_aid("two-points", point, angle)["angle"] == 45
    assert lines.through((0, 0), (10, -10))[1] == -45 and lines.normal_angle(135) == -45
    origin, angle = lines.parallel_at((0, 0), 0, 30, (5, 100))
    assert angle == 0 and abs(origin[1] - 30) < 1e-9, "on the side of the click, y down"
    origin, _angle = lines.parallel_at((0, 0), 0, 30, (5, -100))
    assert abs(origin[1] + 30) < 1e-9
    try:
        plan.new_aid("oblique", (0, 0), 10)
    except ValueError:
        pass
    else:
        raise AssertionError("an unknown kind of aid is refused")


def test_a_source_with_aids_is_1_6_and_a_1_5_file_is_read_as_it_is():
    source = _source()
    assert plan.SOURCE_SCHEMA_VERSION == "1.6"
    plan.check_source(source, "P01.json")
    old = copy.deepcopy(source)
    old["schema_version"] = "1.5"
    del old["aids"]
    plan.check_source(old, "P01.json")
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "P01.json"
        path.write_text(json.dumps(old), encoding="utf-8")
        assert plan.read_source(path)["id"] == "P01"
    broken = copy.deepcopy(source)
    broken["aids"] = [{"kind": "horizontal", "point": [0], "angle": 0}]
    try:
        plan.check_source(broken, "P01.json")
    except Exception as exc:
        assert "aid 1" in str(exc)
    else:
        raise AssertionError("an aid of one coordinate is refused")


def test_the_report_never_draws_an_aid():
    source = _source()
    without = copy.deepcopy(source)
    without["aids"] = []
    window = {"x": 0, "y": 0, "w": 1000, "h": 500}
    assert plan_svg.render(source, window) == plan_svg.render(without, window), "an aid is the editor's alone"


def test_an_aid_snaps_as_an_axis_does_and_turns_with_its_page():
    source = _source()
    index = plan.SnapIndex(source, plan.crop_of(source), axes=True, elements=False)
    point, kind = index.snap((50, 302), 5)
    assert kind in ("on-axis", "axis-crossing") and abs(point[1] - 300) < 1e-6, (point, kind)
    hidden = plan.SnapIndex(source, plan.crop_of(source), axes=False, elements=False)
    assert hidden.snap((50, 302), 5)[1] is None, "behind «Accrocher aux axes», as the axes"
    turned = plan.rotate_source(source, 1, (1000, 500))
    assert turned["aids"][0]["kind"] == "vertical" and turned["aids"][0]["angle"] == 90
    assert turned["dimensions"][0]["kind"] == "vertical" and turned["dimensions"][0]["points"][0] == plan.turn_point([100, 100], 500), "the dimensions turn with the page too"


def test_the_domain_reads_without_qt():
    import subprocess
    code = "import sys; sys.path.insert(0, sys.argv[1]); from domains import lines, plan, fire; import sys as s; assert 'PySide6' not in s.modules"
    done = subprocess.run([sys.executable, "-c", code, str(ROOT / "calc")], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr


def test_a_fire_entry_is_moved_and_copied_with_an_id_of_its_own():
    from domains import fire
    source = {"zones": [{"id": "Z1", "points": [[0, 0], [10, 0], [10, 10]], "holes": [[[2, 2], [3, 2], [3, 3]]]}], "walls": [{"id": "W1", "points": [[0, 0], [5, 0]]}]}
    fire.translate_entry(source, "Z1", 1, 2)
    assert source["zones"][0]["points"][0] == [1, 2] and source["zones"][0]["holes"][0][0] == [3, 4]
    made = fire.copy_entry(source, "W1", 0, 10)
    assert made == "W2" and source["walls"][1]["points"] == [[0, 10], [5, 10]]


# --- the canvas ----------------------------------------------------------------------------

def _qt():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _canvas(source):
    _qt()
    import plan_canvas
    canvas = plan_canvas.PlanCanvas()
    canvas.resize(900, 600)
    canvas.show()
    canvas.set_source(source, Path(tempfile.gettempdir()))
    history = []
    canvas.about_to_change.connect(lambda: history.append(copy.deepcopy(canvas.source)))
    return canvas, history


def _at(canvas, point):
    """A click exactly at `point`, past the snapping: the tests say where, not what is near."""
    import plan_canvas_edit
    canvas._forced = tuple(point)
    try:
        plan_canvas_edit.click(canvas, point, False)
    finally:
        canvas._forced = None


def test_move_takes_the_selection_by_its_base_point_in_one_step():
    canvas, history = _canvas(_source())
    canvas.select(("element", 0))
    canvas.set_tool("move")
    _at(canvas, (100, 100))
    assert canvas.drawing == [(100, 100)]
    _at(canvas, (130, 140))
    assert canvas.source["elements"][0]["points"] == [[130, 140], [530, 140]] and len(history) == 1
    assert canvas.drawing == [], "the tool is given back"


def test_copy_puts_down_a_copy_at_every_click_until_escape():
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    canvas, history = _canvas(_source())
    canvas.select(("element", 0))
    canvas.set_tool("copy")
    _at(canvas, (100, 100))
    _at(canvas, (100, 150))
    _at(canvas, (100, 200))
    labels = [e["label"] for e in canvas.source["elements"]]
    assert labels.count("T101") == 3 and len(history) == 2, (labels, len(history))
    assert canvas.selection == ("element", 0), "the original stays selected: the next copy is made of it"
    QTest.keyClick(canvas, Qt.Key.Key_Escape)
    assert canvas.drawing == []


def test_nothing_selected_is_refused_and_said():
    canvas, _history = _canvas(_source())
    said = []
    canvas.edit_refused.connect(said.append)
    canvas.set_tool("move")
    _at(canvas, (100, 100))
    assert said == ["move"] and canvas.drawing == []


def test_an_aid_is_drawn_selected_and_deleted_and_the_element_dragged_moves_by_the_domain():
    canvas, history = _canvas(_source())
    canvas.set_tool("aid-v")
    _at(canvas, (700, 50))
    assert canvas.source["aids"][-1] == {"kind": "vertical", "point": [700, 50], "angle": 90} and canvas.selection == ("aid", 1)
    canvas.set_tool("aid-2p")
    _at(canvas, (0, 0))
    _at(canvas, (100, 100))
    assert canvas.source["aids"][-1]["kind"] == "two-points" and canvas.source["aids"][-1]["angle"] == 45
    canvas.ask_distance = lambda: 50.0
    canvas.set_tool("aid-par")
    _at(canvas, (300, 100))   # on T101's line
    _at(canvas, (300, 400))   # below it
    made = canvas.source["aids"][-1]
    assert made["kind"] == "parallel" and abs(made["point"][1] - 150) < 1e-6 and made["angle"] == 0, made
    assert not canvas.aid_item.boundingRect().isEmpty(), "the aids are drawn by the canvas"
    canvas.set_tool("select")
    canvas.select(("aid", 0))
    count = len(canvas.source["aids"])
    canvas.delete_selection()
    assert len(canvas.source["aids"]) == count - 1


def test_duplicate_puts_a_copy_beside_the_selection_and_selects_it():
    canvas, history = _canvas(_source())
    canvas.select(("element", 0))
    assert canvas.duplicate_selection()
    copy_ = canvas.source["elements"][-1]
    assert canvas.selection == ("element", len(canvas.source["elements"]) - 1) and copy_["label"] == "T101" and copy_["points"] != canvas.source["elements"][0]["points"]
    assert len(history) == 1
    canvas.select(None)
    assert not canvas.duplicate_selection()


def test_both_plan_tabs_have_the_tools_and_the_object_buttons():
    """REQ-010, UI-010, ARCH-004: «Déplacer» and «Copier» in both plan tabs, the aids in the position plan's alone (D-015); «Objet sélectionné» at the foot of the left pane, closed with nothing selected; its words in three languages."""
    _qt()
    import plan_tab
    import woodcore_gui
    window = woodcore_gui.MainWindow()
    try:
        for kind in ("PlanTab", "FireTab"):
            tab = next(t for t in window.tabs if type(t).__name__ == kind)
            assert {"move", "copy"} <= set(tab.tool_buttons), kind
            assert ("aid-h" in tab.tool_buttons) == (kind == "PlanTab"), kind
            assert tab.left_pane.isAncestorOf(tab.object_box) and not tab.object_duplicate_button.isEnabled() and not tab.object_delete_button.isEnabled(), kind
            tab.dirty = False
        for key in ("plan_tool_move", "plan_tool_copy", "plan_tool_aid_par", "plan_hint_copy", "plan_object", "plan_object_duplicate", "plan_object_delete", "plan_edit_nothing"):
            assert all(key in plan_tab.STRINGS[lang] for lang in ("fr", "de", "en")), key
    finally:
        window.close()
