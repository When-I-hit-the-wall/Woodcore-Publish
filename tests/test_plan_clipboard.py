"""Copying from one plan and pasting on another (issue #61, calc/domains/plan_clip.py, calc/tools/plan_clipboard.py, docs/ui/tab-plans.md §10quater, docs/domain/position-plans.md §3.3sexies, docs/domain/fire-plans.md).

What is held: a paste puts the base point on the point clicked, scales the geometry about it where both plans have a scale (D-003), gives every element the next number of its prefix on the target's storey -- two occurrences of one position sharing their new one --, replaces the target's outline with a pasted one (D-002), and leaves out what the target cannot hold, every result passing `plan.check_source`; a fire-protection plan's paste gives each entry an id of its own. In the window: Ctrl+click adds and removes, Ctrl+A takes everything but the outline, Move/Delete act on the whole selection in one step, Ctrl+C asks for a base point and Ctrl+V puts the clip down in one step of «Annuler», a clip of the other kind of plan or of another project is refused, and Ctrl+C in a field is the field's.

⚠️ The window tests are skipped where PySide6 is not installed; the domain's are not.
"""

TIER = "fast"  # tests/run_tests.py --fast

import copy

import conftest
from domains import fire
from domains import plan
from domains import plan_clip


def _floor(pid="P1", floor="1", per_m=100.0):
    source = plan.new_source(pid, floor=floor)
    source["sheet"] = {"width": 2000, "height": 1000}
    if per_m:
        source["scale"] = {"mode": "calibration", "points": [[0, 0], [per_m, 0]], "length_m": 1.0}
    source["elements"] = [{"type": "S", "label": f"S{floor}01", "points": [[100, 100]]},
                          {"type": "S", "label": f"S{floor}02", "points": [[300, 100]]},
                          {"type": "H", "label": f"H{floor}01", "points": [[100, 200], [200, 200]]}]
    source["axes"] = [{"label": "A", "point": [100, 0], "angle": 90, "bubbles": "both"}]
    return source


def _check(source):
    """The plan as a save writes it -- at the version what it holds asks for (plan.version_of) -- passes the checks a file is read with."""
    written = copy.deepcopy(source)
    written["schema_version"] = plan.version_of(written)
    plan.check_source(written, "test")


def _numbers(type_taken):
    """A `propose` as the tab's: the next of the letter on the plan's storey over what the plan draws."""
    import positions_store

    def propose(source):
        return lambda type_: positions_store.propose_id(list(type_taken) + plan.plan_labels(source), type_, source.get("floor") or "0")
    return propose


def test_a_paste_puts_the_base_on_the_point_and_renumbers_on_the_target_storey():
    a, b = _floor("P1", "1"), _floor("P2", "2")
    b["elements"] = [{"type": "S", "label": "S201", "points": [[50, 50]]}]
    clip = plan_clip.clip_plan(a, [("element", 0), ("element", 1)], (100, 50), plan.units_per_m(a), {"S101": {"type": "Stütze", "section_type": "rect", "dimension": "200x200", "units": "mm"}})
    result = plan_clip.paste_plan(b, clip, (300, 80), plan.units_per_m(b), plan.crop_of(b), _numbers([])(b))
    assert [e["label"] for e in b["elements"]] == ["S201", "S202", "S203"]
    assert b["elements"][1]["points"] == [[300, 130]] and b["elements"][2]["points"] == [[500, 130]], "moved by (200, 30)"
    assert result["relabelled"] == {"S101": "S202", "S102": "S203"}
    assert result["added"] == [("element", 1), ("element", 2)]
    assert plan_clip.new_positions(clip, result["relabelled"]) == {"S202": {"type": "Stütze", "section_type": "rect", "dimension": "200x200", "units": "mm"}}
    assert [e["label"] for e in a["elements"]] == ["S101", "S102", "H101"], "the plan copied from is untouched"
    _check(b)


def test_two_occurrences_of_one_position_share_their_new_number():
    a, b = _floor("P1", "1"), _floor("P2", "2")
    a["elements"][1]["label"] = "S101"
    b["elements"] = []
    clip = plan_clip.clip_plan(a, [("element", 0), ("element", 1)], (0, 0), None)
    plan_clip.paste_plan(b, clip, (0, 0), None, plan.crop_of(b), _numbers([])(b))
    assert [e["label"] for e in b["elements"]] == ["S201", "S201"]


def test_pasting_on_the_plan_copied_from_renumbers_where_copier_keeps_the_number():
    a = _floor()
    clip = plan_clip.clip_plan(a, [("element", 0)], (100, 100), None)
    plan_clip.paste_plan(a, clip, (900, 900), None, plan.crop_of(a), _numbers([])(a))
    assert a["elements"][-1]["label"] == "S103" and a["elements"][-1]["points"] == [[900, 900]]


def test_the_geometry_is_scaled_about_the_base_between_two_scales():
    a, b = _floor("P1", "1", per_m=100.0), _floor("P2", "2", per_m=200.0)   # 1:100 and 1:50, as sheet units per metre
    b["elements"] = []
    clip = plan_clip.clip_plan(a, [("element", 2)], (100, 200), plan.units_per_m(a))
    plan_clip.paste_plan(b, clip, (400, 400), plan.units_per_m(b), plan.crop_of(b), _numbers([])(b))
    wall = b["elements"][0]["points"]
    assert wall[0] == [400, 400] and math_dist(wall) == 200, wall
    # without a scale on one side, nothing is scaled
    c = _floor("P3", "3", per_m=None)
    c["elements"] = []
    plan_clip.paste_plan(c, clip, (400, 400), plan.units_per_m(c), plan.crop_of(c), _numbers([])(c))
    assert math_dist(c["elements"][0]["points"]) == 100


def math_dist(points):
    import math
    return round(math.dist(points[0], points[1]), 6)


def test_placed_scales_every_geometric_field_and_keeps_the_rest():
    entries = [("storey-box", {"storey": "1", "x": 10, "y": 10, "w": 50, "h": 40}),
               ("dimension", {"kind": "horizontal", "points": [[0, 0], [10, 0]], "offset": -20}),
               ("element", {"type": "S", "label": "S101", "points": [[10, 10]], "label_offset": [5, 5], "angle": 30}),
               ("axis", {"label": "A", "point": [10, 0], "angle": 90})]
    clip = plan_clip.Clip(plan_clip.POSITION, entries, (0.0, 0.0), 100.0)
    out = dict(plan_clip.placed(clip, (0, 0), 200.0))
    assert (out["storey-box"]["x"], out["storey-box"]["w"], out["storey-box"]["h"]) == (20, 100, 80)
    assert out["dimension"]["offset"] == -40 and out["dimension"]["points"][1] == [20, 0]
    assert out["element"]["label_offset"] == [5, 5] and out["element"]["angle"] == 30 and out["element"]["points"] == [[20, 20]]
    assert out["axis"]["point"] == [20, 0]
    assert entries[0][1]["x"] == 10, "the clip itself is never changed"


def test_a_pasted_outline_replaces_the_target_s_and_is_never_left_twice():
    a, b = _floor("P1", "1"), _floor("P2", "2")
    a["outlines"] = [{"points": [[0, 0], [100, 0], [100, 100]]}]
    b["outlines"] = [{"points": [[0, 0], [50, 0], [50, 50]]}]
    clip = plan_clip.clip_plan(a, [("outline", 0)], (0, 0), None)
    result = plan_clip.paste_plan(b, clip, (10, 10), None, plan.crop_of(b), _numbers([])(b))
    assert result["outline_replaced"] and len(b["outlines"]) == 1 and b["outlines"][0]["points"][1] == [110, 10]
    _check(b)


def test_what_the_target_cannot_hold_is_left_out_and_counted():
    section = _floor("C1", "1")
    section["role"], section["plan_type"] = "section", "section"
    section["storey_lines"] = [{"storey": "1", "points": [[0, 450], [900, 450]]}]
    section["outlines"] = []
    clip = plan_clip.clip_plan(section, [("storey-line", 0), ("element", 0)], (0, 0), None)
    floor = _floor("P2", "2")
    floor["elements"] = []
    result = plan_clip.paste_plan(floor, clip, (0, 0), None, plan.crop_of(floor), _numbers([])(floor))
    assert result["left_out"] == {"section-only": 1} and len(floor["elements"]) == 1 and "storey_lines" not in floor
    _check(floor)
    # a load symbol off a load-path plan, an outline on a section, an axis already there
    loads = plan_clip.Clip(plan_clip.POSITION, [("element", {"type": "PL", "label": "P101", "points": [[5, 5]]}),
                                                ("outline", {"points": [[0, 0], [10, 0], [10, 10]]}),
                                                ("axis", {"label": "A", "point": [100, 50], "angle": 90, "bubbles": "both"})], (0.0, 0.0))
    target = _floor("C2", "2")
    target["role"], target["plan_type"] = "section", "section"
    result = plan_clip.paste_plan(target, loads, (0, 0), None, plan.crop_of(target), _numbers([])(target))
    assert result["left_out"] == {"load": 1, "outline-on-section": 1, "axis-there": 1} and result["added"] == []
    _check(target)


def test_a_new_axis_is_named_where_it_lands():
    a, b = _floor("P1", "1"), _floor("P2", "2")
    a["axes"].append({"label": "B", "point": [600, 0], "angle": 90, "bubbles": "both"})
    clip = plan_clip.clip_plan(a, [("axis", 0), ("axis", 1)], (0, 0), None)
    result = plan_clip.paste_plan(b, clip, (0, 0), None, plan.crop_of(b), _numbers([])(b))
    assert result["left_out"] == {"axis-there": 1} and sorted(axis["label"] for axis in b["axes"]) == ["A", "B"]
    _check(b)


def test_a_fire_plan_paste_gives_new_ids_in_collections_the_target_may_lack():
    a = {"zones": [{"id": "Z1", "kind": "clear", "points": [[0, 0], [10, 0], [10, 10]], "holes": [[[2, 2], [3, 2], [3, 3]]]}],
         "walls": [{"id": "W2", "points": [[0, 0], [10, 0]]}]}
    b = {"zones": [{"id": "Z1", "kind": "clear", "points": [[0, 0], [5, 0], [5, 5]]}]}
    clip = plan_clip.clip_fire(a, ["Z1", "W2"], (0, 0), 100.0)
    result = plan_clip.paste_fire(b, clip, (100, 100), 200.0)
    ids = [entry["id"] for entry in b["zones"] + b["walls"]]
    assert len(set(ids)) == len(ids) == 3 and set(result["added"]) <= set(ids)
    assert b["zones"][1]["points"][1] == [120, 100] and b["zones"][1]["holes"][0][0] == [104, 104]
    assert fire.entry_of(b, result["added"][1])[0] == "walls"


# --- the window --------------------------------------------------------------------------------

import sys
import tempfile
from pathlib import Path

from conftest import ROOT, Skip
import project

_STATE = {}


def _qt():
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        from PySide6.QtWidgets import QApplication
        import PySide6.QtPdf  # noqa: F401
    except ImportError as exc:
        raise Skip(f"PySide6 or its QtPdf is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _canvas(source):
    _qt()
    import plan_canvas
    canvas = plan_canvas.PlanCanvas()
    canvas.resize(900, 700)
    canvas.show()
    canvas.set_source(source, Path(tempfile.gettempdir()))
    history = []
    canvas.about_to_change.connect(lambda: history.append(copy.deepcopy(canvas.source)))
    return canvas, history


def _ctrl_click(canvas, point):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier, canvas.mapFromScene(*point))


def test_ctrl_click_adds_and_takes_out_and_a_plain_click_replaces():
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    canvas, _history = _canvas(_floor())
    canvas.fit()
    _ctrl_click(canvas, (100, 100))
    _ctrl_click(canvas, (300, 100))
    assert canvas.selected_entries() == [("element", 0), ("element", 1)] and canvas.selection == ("element", 1)
    assert canvas.selection_count() == 2
    path = canvas.select_item.path().boundingRect()
    assert path.left() <= 100 and path.right() >= 300, "both are drawn selected"
    _ctrl_click(canvas, (100, 100))
    assert canvas.selected_entries() == [("element", 1)]
    QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, canvas.mapFromScene(150, 200))
    assert canvas.selected_entries() == [("element", 2)], "a plain click selects the one object clicked"


def test_ctrl_a_takes_everything_but_the_outline():
    source = _floor()
    source["outlines"] = [{"points": [[0, 0], [900, 0], [900, 900]]}]
    canvas, _history = _canvas(source)
    canvas.select_all()
    chosen = canvas.selected_entries()
    assert len(chosen) == 4 and all(kind != "outline" for kind, _index in chosen), chosen


def test_move_and_delete_act_on_the_whole_selection_in_one_step():
    canvas, history = _canvas(_floor())
    canvas.set_selected([("element", 0), ("element", 1)])
    canvas.begin_change()
    canvas.translate_selection(10, 0)
    canvas.end_change()
    assert canvas.source["elements"][0]["points"] == [[110, 100]] and canvas.source["elements"][1]["points"] == [[310, 100]]
    canvas.delete_selection()
    assert [e["label"] for e in canvas.source["elements"]] == ["H101"] and len(history) == 2


def test_copy_with_an_outline_selected_copies_the_rest():
    source = _floor()
    source["outlines"] = [{"points": [[0, 0], [900, 0], [900, 900]]}]
    canvas, _history = _canvas(source)
    canvas.set_selected([("element", 0), ("outline", 0)])
    canvas.begin_change()
    made = canvas.copy_selection(0, 50)
    canvas.end_change()
    assert made == [("element", 3)] and len(canvas.source["outlines"]) == 1
    assert canvas.selected_entries() == [("element", 0), ("outline", 0)], "the originals stay selected (D-014)"


def _window():
    if "window" not in _STATE:
        app = _qt()
        here = conftest.project_copy("plan_clipboard")
        with project.using(here):
            import woodcore_gui
            window = woodcore_gui.MainWindow()
        _STATE.update(app=app, window=window, here=here)
    return _STATE["window"], _STATE["here"]


def _tab(kind):
    window, here = _window()
    tab = next(t for t in window.tabs if type(t).__name__ == kind)
    tab.dirty = False
    return tab, here


def _open(tab, source):
    tab.open_source(source, None, False)
    tab.show_plan_view()
    tab.choose_tool("select")
    tab.canvas.select(None)
    tab.dirty = False


def test_ctrl_c_and_ctrl_v_carry_the_selection_to_another_plan_renumbered_in_one_step():
    tab, here = _tab("PlanTab")
    import plan_canvas_edit
    import plan_clipboard
    plan_clipboard.clear()
    with project.using(here):
        a, b = _floor("PA", "1"), _floor("PB", "2")
        b["elements"] = [{"type": "S", "label": "S201", "points": [[50, 50]]}]
        _open(tab, a)
        tab.canvas.set_selected([("element", 0), ("element", 1)])
        tab.clip_copy()
        assert tab.canvas.tool == plan_canvas_edit.CLIP_BASE and tab.hint.text() == tab.t("plan_hint_clip_base")
        tab.on_clip_point(plan_canvas_edit.CLIP_BASE, 100.0, 50.0)
        clip = plan_clipboard.current()
        assert len(clip) == 2 and clip.base == (100.0, 50.0) and tab.canvas.tool == "select"
        assert tab.source["elements"] == a["elements"], "Ctrl+C changes nothing"
        _open(tab, b)
        tab.clip_paste()
        assert tab.canvas.tool == plan_canvas_edit.PASTE
        tab.canvas.cursor = (300.0, 80.0)
        assert not tab.canvas.clip_outline((300.0, 80.0)).isEmpty(), "the clip follows the pointer"
        tab.on_clip_point(plan_canvas_edit.PASTE, 300.0, 80.0)
        labels = [e["label"] for e in tab.source["elements"]]
        assert labels == ["S201", "S202", "S203"], labels
        assert tab.source["elements"][1]["points"] == [[300, 130]]
        assert set(tab.pending_positions()) >= {"S202", "S203"}
        assert tab.canvas.selected_entries() == [("element", 1), ("element", 2)]
        assert tab.object_heading.text() == tab.w("plan_objects", n=2)
        tab.undo()
        assert [e["label"] for e in tab.source["elements"]] == ["S201"], "one step of «Annuler» takes the paste back"
        tab.dirty = False


def test_a_paste_of_the_other_kind_of_plan_or_another_project_is_refused():
    tab, here = _tab("FireTab")
    import plan_clipboard
    with project.using(here):
        plan_clipboard.put(plan_clip.Clip(plan_clip.POSITION, [("element", {"type": "S", "label": "S101", "points": [[1, 1]]})], (0.0, 0.0), root=str(here.root)))
        tab.clip_paste()
        assert tab.canvas.tool == "select" and tab.hint.text() == tab.t("plan_paste_from_position")
        plan_clipboard.put(plan_clip.Clip(plan_clip.FIRE, [("walls", {"id": "W1", "points": [[0, 0], [1, 0]]})], (0.0, 0.0), root="elsewhere"))
        tab.clip_paste()
        assert tab.hint.text() == tab.t("plan_paste_other_project")
    plan_clipboard.clear()


def test_ctrl_c_in_a_field_is_the_field_s():
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QLineEdit
    tab, here = _tab("PlanTab")
    import plan_clipboard
    plan_clipboard.clear()
    with project.using(here):
        window, _here = _window()
        window.tab_widget.setCurrentIndex(window.tabs.index(tab))   # a shortcut of the canvas reaches it once its tab is the one shown
        window.show()
        window.activateWindow()
        _open(tab, _floor("PC", "1"))
        tab.canvas.select_all()
        field = QLineEdit(tab.canvas)   # a field over the plan -- as the typed distance is (PlanCanvas.distance): a child of the canvas, which its shortcut must not reach
        field.show()
        field.setFocus()
        _STATE["app"].processEvents()   # the focus where it was asked, before a key is sent
        QTest.keyClick(field, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
        assert tab.canvas.tool == "select" and plan_clipboard.current() is None
        tab.canvas.setFocus()
        _STATE["app"].processEvents()
        QTest.keyClick(tab.canvas, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
        assert tab.canvas.tool == "clip-base", "on the plan, Ctrl+C asks for the base point"
        tab.choose_tool("select")
        field.deleteLater()
        tab.dirty = False


def test_the_words_exist_in_three_languages():
    _qt()
    import plan_tab
    keys = ("plan_hint_clip_base", "plan_hint_paste", "plan_clip_nothing", "plan_clip_done", "plan_paste_empty", "plan_paste_from_position", "plan_paste_from_fire",
            "plan_paste_other_project", "plan_paste_done", "plan_paste_left_out", "plan_paste_outline_replaced", "plan_paste_scaled", "plan_objects")
    for key in keys:
        assert all(key in plan_tab.STRINGS[lang] for lang in ("fr", "de", "en")), key


def test_the_selection_is_drawn_in_the_selections_orange():
    _qt()
    import theme
    canvas, _history = _canvas(_floor())
    canvas.set_selected([("element", 0), ("element", 1)])
    assert canvas.select_item.pen().color().rgb() == theme.qcolor("plan-select").rgb()


def test_a_selection_of_one_object_after_a_new_one_and_no_index_left_behind_by_an_undo():
    tab, here = _tab("PlanTab")
    with project.using(here):
        _open(tab, _floor("PD", "1"))
        tab.canvas.select_all()
        tab.canvas.add_element("S", [[700, 700]])
        assert len(tab.canvas.selected_entries()) == 1, "a new object leaves one object selected"
        tab.canvas.select_all()
        tab.canvas.delete_selection()
        tab.undo()
        entries = tab.canvas.selected_entries()
        lists = {kind: len(tab.source.get(model_list) or []) for kind, model_list in plan.ENTRY_LISTS.items()}
        assert all(index < lists[kind] for kind, index in entries)
        tab.dirty = False


def test_move_duplicate_and_their_undo_act_on_the_whole_selection():
    tab, here = _tab("PlanTab")
    with project.using(here):
        _open(tab, _floor("PE", "1"))
        tab.canvas.set_selected([("element", 0), ("element", 1)])
        tab.canvas.begin_change()
        tab.canvas.translate_selection(10, 0)
        tab.canvas.end_change()
        tab.undo()
        assert tab.source["elements"][0]["points"] == [[100, 100]] and tab.source["elements"][1]["points"] == [[300, 100]], "Ctrl+Z puts both back"
        tab.canvas.set_selected([("element", 0), ("element", 1)])
        assert tab.canvas.duplicate_selection()
        assert len(tab.source["elements"]) == 5 and tab.canvas.selected_entries() == [("element", 3), ("element", 4)]
        tab.undo()
        assert len(tab.source["elements"]) == 3, "one step"
        tab.dirty = False


def _copy(tab, entries, base):
    import plan_canvas_edit
    tab.canvas.set_selected(entries)
    tab.clip_copy()
    tab.on_clip_point(plan_canvas_edit.CLIP_BASE, *base)


def _paste(tab, point):
    import plan_canvas_edit
    tab.clip_paste()
    assert tab.canvas.tool == plan_canvas_edit.PASTE, tab.hint.text()
    tab.on_clip_point(plan_canvas_edit.PASTE, *point)


def test_a_pasted_outline_replaces_the_plans_and_undo_gives_the_old_one_back():
    tab, here = _tab("PlanTab")
    with project.using(here):
        a, b = _floor("PF", "1"), _floor("PG", "2")
        a["outlines"] = [{"points": [[0, 0], [100, 0], [100, 100]]}]
        b["outlines"] = [{"points": [[0, 0], [50, 0], [50, 50]]}]
        _open(tab, a)
        _copy(tab, [("outline", 0), ("element", 0)], (0.0, 0.0))
        _open(tab, b)
        _paste(tab, (10.0, 10.0))
        assert len(tab.source["outlines"]) == 1 and tab.source["outlines"][0]["points"][1] == [110, 10]
        assert tab.t("plan_paste_outline_replaced") in tab.hint.text()
        tab.undo()
        assert tab.source["outlines"] == [{"points": [[0, 0], [50, 0], [50, 50]]}], "the same step: Ctrl+Z gives the old outline back"
        tab.dirty = False


def test_the_clip_survives_a_change_of_plan_escape_gives_up_and_a_paste_is_repeated():
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    import plan_canvas_edit
    import plan_clipboard
    tab, here = _tab("PlanTab")
    with project.using(here):
        a, b, c = _floor("PH", "1"), _floor("PI", "2"), _floor("PJ", "3")
        for source in (b, c):
            source["elements"] = []
        plan_clipboard.clear()
        _open(tab, a)
        tab.canvas.set_selected([("element", 0)])
        tab.clip_copy()
        QTest.keyClick(tab.canvas, Qt.Key.Key_Escape)
        assert tab.canvas.tool == "select" and plan_clipboard.current() is None, "Escape gives the copy up"
        _copy(tab, [("element", 0)], (7.0, 7.0))
        clip = plan_clipboard.current()
        _open(tab, b)
        _open(tab, a)
        assert plan_clipboard.current() is clip, "the clip is kept across the plans opened"
        _open(tab, b)
        tab.clip_paste()
        QTest.keyClick(tab.canvas, Qt.Key.Key_Escape)
        assert tab.canvas.tool == "select" and tab.source["elements"] == [], "Escape gives the paste up"
        _paste(tab, (20.0, 20.0))
        _open(tab, c)
        _paste(tab, (20.0, 20.0))
        assert [e["label"] for e in tab.source["elements"]] == ["S301"], "the clip pasted again, on the next storey"
        tab.dirty = False


def test_the_number_field_shows_the_object_in_focus():
    from PySide6.QtWidgets import QComboBox
    tab, here = _tab("PlanTab")
    with project.using(here):
        _open(tab, _floor("PK", "1"))
        from PySide6.QtCore import QCoreApplication, QEvent
        tab.canvas.set_selected([("element", 0), ("element", 1)])
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete.value)   # the card of the previous selection really gone
        shown = [w.currentData() for w in tab.findChildren(QComboBox)]
        assert "S102" in shown and "S101" not in shown, "the number field is the focus's, the last added"
        tab.dirty = False


def test_no_button_for_the_clip_and_the_selection_tool_says_the_shortcuts():
    import plan_canvas_edit
    for kind, key in (("PlanTab", "plan_hint_select"), ("FireTab", "fp_hint_select")):
        tab, _here = _tab(kind)
        assert not set(plan_canvas_edit.CLIP_TOOLS) & set(tab.tool_buttons), kind
        tip = tab.tool_buttons["select"].toolTip()
        assert tip == tab.t(key) and ("Ctrl+A" in tip or "Strg+A" in tip), (kind, tip)


def test_the_fire_tab_selects_copies_and_pastes_between_its_plans_and_refuses_the_other_kind():
    import plan_canvas_edit
    import plan_clipboard
    plan_clipboard.clear()
    tab, here = _tab("FireTab")
    with project.using(here):
        a = fire.new_source("FA")
        a.setdefault("walls", []).append({"id": "W1", "class": "EI 30", "points": [[0, 0], [100, 0]]})
        b = fire.new_source("FB")
        tab.open_source(a, None, False)
        tab.choose_tool("select")
        tab.clip_select_all()
        assert tab.canvas.selected == ["W1"]
        tab.clip_copy()
        assert tab.canvas.tool == plan_canvas_edit.CLIP_BASE
        tab.on_clip_point(plan_canvas_edit.CLIP_BASE, 0.0, 0.0)
        assert plan_clipboard.current().kind == plan_clip.FIRE
        tab.open_source(b, None, False)
        tab.clip_paste()
        tab.on_clip_point(plan_canvas_edit.PASTE, 50.0, 50.0)
        assert [w["points"] for w in tab.source["walls"]] == [[[50, 50], [150, 50]]] and tab.canvas.selected == [tab.source["walls"][0]["id"]]
        tab.undo()
        assert not tab.source.get("walls"), "one step of «Annuler»"
        tab.dirty = False
    plan_tab_, here = _tab("PlanTab")
    with project.using(here):
        plan_tab_.clip_paste()
        assert plan_tab_.hint.text() == plan_tab_.t("plan_paste_from_fire") and plan_tab_.canvas.tool == "select"
        plan_tab_.dirty = False
    plan_clipboard.clear()
